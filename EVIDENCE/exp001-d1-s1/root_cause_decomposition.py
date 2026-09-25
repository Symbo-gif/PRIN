r"""EXP-001 D1 S1 root-cause decomposition of the H1/H2a refutations.

Evidence generator for the EXP-001 D1 correction cycle (S1). It re-derives
every H1 and H2a breach recorded by the committed E3 artefacts and attributes
each one to a mechanism by controlled substitution. PRINet 3.0 is re-run with
exactly one behaviour changed at a time, and the effect on the registered
comparison is measured:

* ``native``          — the archived PRINet 3.0 reference, unmodified;
* ``f64``             — the three DV-007 ``complex64`` paths evaluated in
                        float64 (``parity.prinet_f64``), nothing else changed;
* ``f64_bounded``     — ``f64`` with PRIN's *pre-correction* integrator guard
                        (amplitude ``[1e-6, 10]``, every derivative ``±1e4``)
                        swapped into ``OscillatorModel._step_euler/_step_rk4``;
* ``f64_ulp``         — ``f64`` from initial phases nudged by one ulp
                        (``numpy.nextafter(phase, +inf)``).

A case is **DV-007-sensitive** when ``native`` vs ``f64`` breaches the
registered tolerance, **guard-sensitive** when ``f64`` vs ``f64_bounded``
breaches, and **ill-conditioned** when ``f64`` vs ``f64_ulp`` breaches. PRIN
(whatever build is importable) is compared with each reference.

Run from the repository root with the project venv::

    python EVIDENCE/exp001-d1-s1/root_cause_decomposition.py --label postfix \\
        --out EVIDENCE/exp001-d1-s1/root-cause-decomposition-postfix.json

The output records the ``prin`` extension actually imported, so a run against
a pre-fix build is distinguishable from a post-fix one.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
from collections import Counter
from collections.abc import Generator
from pathlib import Path
from typing import Any

import numpy as np
import torch

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))

import prin  # noqa: E402
from prin import _prin_core  # noqa: E402
from prin.parity.harness import compare_arrays  # noqa: E402
from prin.parity.loader import CorpusLoader  # noqa: E402
from prin.parity.schema import CaseArrays  # noqa: E402
from prinet.core.propagation import oscillator_models as om  # noqa: E402
from prinet.core.propagation.oscillator_state import (  # noqa: E402
    OscillatorState as PrinetState,
)
from prinet.core.propagation.oscillator_state import _wrap_phase  # noqa: E402

from benchmarks.campaign.exp001_driver import (  # noqa: E402
    T_STAR,
    draw_fuzz_initial,
    draw_fuzz_spec,
    run_prin_trajectory,
    run_prinet_trajectory,
)
from parity.prinet_f64 import f64_corrected_reference, on_dv007_path  # noqa: E402

_CORPUS_ARTEFACT = (
    _REPO
    / "benchmarks/results/EXP-001/RUN-20260923T134012Z-6b9d6b6-corpus-cpu"
    / "corpus_corpus-cpu.json"
)
_FUZZ_ARTEFACT = (
    _REPO
    / "benchmarks/results/EXP-001/RUN-20260923T134250Z-6b9d6b6-fuzz-cpu"
    / "fuzz_fuzz-cpu.json"
)
_INIT = ("phase_init", "amplitude_init", "frequency_init")
_TRAJ = (
    "phase_traj",
    "amplitude_traj",
    "frequency_traj",
    "order_parameter_traj",
    "mean_phase_coherence_traj",
)
_ALL = (*_INIT, "phase_final", "amplitude_final", "frequency_final", *_TRAJ)


# ---------------------------------------------------------------------------
# PRINet 3.0 with PRIN's pre-correction guard (analysis instrument only)
# ---------------------------------------------------------------------------


def _clamp_derivative(t: torch.Tensor) -> torch.Tensor:
    """PRIN ``clamp_derivative``: NaN -> 0, then clamp to +-1e4."""
    t = torch.where(torch.isnan(t), torch.zeros_like(t), t)
    return torch.clamp(t, -1e4, 1e4)


def _clamp_amplitude(t: torch.Tensor) -> torch.Tensor:
    """PRIN ``clamp_amplitude``: NaN -> 1e-6, then clamp to [1e-6, 10]."""
    t = torch.where(torch.isnan(t), torch.full_like(t, 1e-6), t)
    return torch.clamp(t, 1e-6, 10.0)


def _bounded_derivatives(model: Any, state: Any) -> tuple[torch.Tensor, ...]:
    return tuple(_clamp_derivative(d) for d in model.compute_derivatives(state))


def _bounded_euler(self: Any, state: Any, dt: float) -> Any:
    dphi, dr, domega = _bounded_derivatives(self, state)
    return PrinetState(
        phase=_wrap_phase(state.phase + dt * dphi),
        amplitude=_clamp_amplitude(state.amplitude + dt * dr),
        frequency=state.frequency + dt * domega,
    )


def _bounded_rk4(self: Any, state: Any, dt: float) -> Any:
    def stage(k: tuple[torch.Tensor, ...], scale: float) -> Any:
        return PrinetState(
            phase=state.phase + scale * k[0],
            amplitude=_clamp_amplitude(state.amplitude + scale * k[1]),
            frequency=state.frequency + scale * k[2],
        )

    k1 = _bounded_derivatives(self, state)
    k2 = _bounded_derivatives(self, stage(k1, 0.5 * dt))
    k3 = _bounded_derivatives(self, stage(k2, 0.5 * dt))
    k4 = _bounded_derivatives(self, stage(k3, dt))

    def combine(i: int) -> torch.Tensor:
        base = (state.phase, state.amplitude, state.frequency)[i]
        result: torch.Tensor = base + (dt / 6.0) * (
            k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]
        )
        return result

    return PrinetState(
        phase=_wrap_phase(combine(0)),
        amplitude=_clamp_amplitude(combine(1)),
        frequency=combine(2),
    )


@contextlib.contextmanager
def _pre_correction_guard() -> Generator[None, None, None]:
    """Swap PRIN's pre-correction guard into PRINet 3.0's Euler/RK4."""
    cls = om.OscillatorModel
    originals = {name: cls.__dict__[name] for name in ("_step_euler", "_step_rk4")}
    try:
        setattr(cls, "_step_euler", _bounded_euler)  # noqa: B010 - class patch
        setattr(cls, "_step_rk4", _bounded_rk4)  # noqa: B010 - class patch
        yield
    finally:
        for name, original in originals.items():
            setattr(cls, name, original)


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------


def _breaches(
    ref: CaseArrays, test: CaseArrays, model: str, horizon: int | None
) -> list[str]:
    """Arrays outside the registered tolerance (H2a window when ``horizon``)."""
    names = _ALL if horizon is None else (*_INIT, *_TRAJ)
    out = []
    for name in names:
        a, b = getattr(ref, name), getattr(test, name)
        if horizon is not None and name in _TRAJ:
            a, b = a[: horizon + 1], b[: horizon + 1]
        if not compare_arrays(a, b, name, model).within_tolerance:
            out.append(name)
    return out


def _max_abs(ref: CaseArrays, test: CaseArrays, horizon: int | None) -> float:
    names = _ALL if horizon is None else (*_INIT, *_TRAJ)
    worst = 0.0
    for name in names:
        a, b = getattr(ref, name), getattr(test, name)
        if horizon is not None and name in _TRAJ:
            a, b = a[: horizon + 1], b[: horizon + 1]
        worst = max(worst, float(np.max(np.abs(a - b))))
    return worst


def _references(
    spec: dict[str, Any],
    phase: np.ndarray,
    amplitude: np.ndarray,
    frequency: np.ndarray,
) -> dict[str, CaseArrays]:
    """Run PRIN and the four reference variants from one explicit state."""

    def run(runner: Any, ph: np.ndarray) -> CaseArrays:
        result: CaseArrays = runner(
            model=spec["model"],
            coupling=spec["coupling"],
            integrator=spec["integrator"],
            n_oscillators=spec["n_oscillators"],
            n_steps=spec["n_steps"],
            dt=spec["dt"],
            parameters=spec["parameters"],
            phase_init=ph,
            amplitude_init=amplitude,
            frequency_init=frequency,
        )
        return result

    out = {"prin": run(run_prin_trajectory, phase)}
    out["native"] = run(run_prinet_trajectory, phase)
    with f64_corrected_reference():
        out["f64"] = run(run_prinet_trajectory, phase)
        out["f64_ulp"] = run(run_prinet_trajectory, np.nextafter(phase, np.inf))
        with _pre_correction_guard():
            out["f64_bounded"] = run(run_prinet_trajectory, phase)
    return out


def _classify(
    refs: dict[str, CaseArrays], model: str, horizon: int | None
) -> dict[str, Any]:
    pairs = {
        "prin_vs_native": ("native", "prin"),
        "prin_vs_f64": ("f64", "prin"),
        "prin_vs_f64_bounded": ("f64_bounded", "prin"),
        "dv007_sensitive": ("native", "f64"),
        "guard_sensitive": ("f64", "f64_bounded"),
        "ill_conditioned": ("f64", "f64_ulp"),
    }
    record: dict[str, Any] = {}
    for key, (a, b) in pairs.items():
        record[key] = _breaches(refs[a], refs[b], model, horizon)
        record[f"{key}_max_abs"] = _max_abs(refs[a], refs[b], horizon)
    return record


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------


def _corpus() -> list[dict[str, Any]]:
    loader = CorpusLoader(_REPO / "parity" / "corpus")
    recorded = json.loads(_CORPUS_ARTEFACT.read_text(encoding="utf-8"))
    e3 = {c["case_id"]: c for c in recorded["cases"]}
    rows = []
    for record in loader.manifest.cases:
        loaded = loader.load(record.case_id)
        s, arrays = loaded.spec, loaded.arrays
        spec = {
            "model": s.model,
            "coupling": s.coupling,
            "integrator": s.integrator,
            "n_oscillators": s.n_oscillators,
            "n_steps": s.n_steps,
            "dt": s.dt,
            "parameters": dict(s.parameters),
        }
        refs = _references(
            spec, arrays.phase_init, arrays.amplitude_init, arrays.frequency_init
        )
        refs["corpus"] = arrays
        row = {
            "case_id": s.case_id,
            "model": s.model,
            "coupling": s.coupling,
            "integrator": s.integrator,
            "dv007_path": on_dv007_path(s.model, s.coupling),
            "e3_breach": not e3[s.case_id]["within_tolerance"],
            "e3_max_abs": _e3_max_abs(e3[s.case_id]),
            "prin_vs_corpus": _breaches(arrays, refs["prin"], s.model, None),
            "prin_vs_corpus_max_abs": _max_abs(arrays, refs["prin"], None),
            "native_regen_bit_identical_to_corpus": all(
                np.array_equal(getattr(arrays, n), getattr(refs["native"], n))
                for n in _ALL
            ),
        }
        row.update(_classify(refs, s.model, None))
        rows.append(row)
    return rows


def _fuzz() -> list[dict[str, Any]]:
    recorded = json.loads(_FUZZ_ARTEFACT.read_text(encoding="utf-8"))
    cfg = recorded["config"]
    stream = _prin_core.Seed(cfg["seed_counter"], cfg["seed_key"])
    rows = []
    for index, case in enumerate(recorded["cases"]):
        spec = draw_fuzz_spec(stream)
        phase, amplitude, frequency = draw_fuzz_initial(stream, spec["n_oscillators"])
        for field in ("model", "coupling", "integrator", "n_oscillators", "n_steps"):
            if spec[field] != case[field]:
                raise RuntimeError(f"stream drift at case {index}: {field}")
        horizon = min(T_STAR, spec["n_steps"])
        refs = _references(spec, phase, amplitude, frequency)
        row = {
            "case_index": index,
            "model": spec["model"],
            "coupling": spec["coupling"],
            "integrator": spec["integrator"],
            "n_oscillators": spec["n_oscillators"],
            "n_steps": spec["n_steps"],
            "dt": spec["dt"],
            "dv007_path": on_dv007_path(spec["model"], spec["coupling"]),
            "e3_breach": not case["within_tolerance"],
            "e3_max_abs": _e3_max_abs(case),
            "native_amplitude_range": [
                float(refs["native"].amplitude_traj[: horizon + 1].min()),
                float(refs["native"].amplitude_traj[: horizon + 1].max()),
            ],
        }
        row.update(_classify(refs, spec["model"], horizon))
        rows.append(row)
    return rows


def _e3_max_abs(case: dict[str, Any]) -> float:
    """Largest ``max_abs_diff`` the E3 artefact recorded for one case."""
    return max(float(c["max_abs_diff"]) for c in case["comparisons"])


def _mechanism(row: dict[str, Any]) -> str:
    flags = [
        name
        for name in ("dv007_sensitive", "guard_sensitive", "ill_conditioned")
        if row[name]
    ]
    return "+".join(flags) if flags else "unexplained"


def _summary(
    corpus: list[dict[str, Any]], fuzz: list[dict[str, Any]]
) -> dict[str, Any]:
    h1 = [r for r in corpus if r["e3_breach"]]
    h2a = [r for r in fuzz if r["e3_breach"]]
    ill = sorted(r["case_index"] for r in fuzz if r["ill_conditioned"])
    return {
        "corpus_cases": len(corpus),
        "h1_recorded_breaches": len(h1),
        "build_prin_vs_corpus_breach_set_equals_h1": {
            r["case_id"] for r in corpus if r["prin_vs_corpus"]
        }
        == {r["case_id"] for r in h1},
        "native_regen_bit_identical_to_corpus": sum(
            r["native_regen_bit_identical_to_corpus"] for r in corpus
        ),
        "h1_mechanisms": dict(Counter(_mechanism(r) for r in h1)),
        "corpus_prin_vs_f64_breaches": sum(bool(r["prin_vs_f64"]) for r in corpus),
        "corpus_prin_vs_f64_max_abs": max(r["prin_vs_f64_max_abs"] for r in corpus),
        "corpus_prin_vs_f64_bounded_breaches": sum(
            bool(r["prin_vs_f64_bounded"]) for r in corpus
        ),
        "fuzz_cases": len(fuzz),
        "h2a_recorded_breaches": len(h2a),
        "build_prin_vs_native_breach_set_equals_h2a": {
            r["case_index"] for r in fuzz if r["prin_vs_native"]
        }
        == {r["case_index"] for r in h2a},
        "build_prin_vs_native_breaches": sum(bool(r["prin_vs_native"]) for r in fuzz),
        "h2a_mechanisms": dict(Counter(_mechanism(r) for r in h2a)),
        "h2a_large_magnitude_mechanisms": dict(
            Counter(_mechanism(r) for r in h2a if r["e3_max_abs"] >= 1e-3)
        ),
        "ill_conditioned_cases": ill,
        "fuzz_prin_vs_f64_breaches_outside_ill_conditioned": sorted(
            r["case_index"]
            for r in fuzz
            if r["prin_vs_f64"] and not r["ill_conditioned"]
        ),
        "fuzz_prin_vs_f64_bounded_breaches_outside_ill_conditioned": sorted(
            r["case_index"]
            for r in fuzz
            if r["prin_vs_f64_bounded"] and not r["ill_conditioned"]
        ),
        "fuzz_prin_vs_f64_max_abs_outside_ill_conditioned": max(
            r["prin_vs_f64_max_abs"] for r in fuzz if not r["ill_conditioned"]
        ),
        "fuzz_prin_vs_f64_bounded_max_abs_outside_ill_conditioned": max(
            r["prin_vs_f64_bounded_max_abs"] for r in fuzz if not r["ill_conditioned"]
        ),
    }


def _git(*args: str) -> str:
    return subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["git", *args],  # noqa: S607 - git resolved from PATH like every tool here
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def main(argv: list[str] | None = None) -> int:
    """Run the decomposition and write the JSON evidence file."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--label", required=True, help="prefix or postfix")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    corpus = _corpus()
    fuzz = _fuzz()
    payload = {
        "label": args.label,
        "git_head": _git("rev-parse", "HEAD"),
        "prin_package": str(Path(prin.__file__).resolve().parent),
        "prin_extension": str(Path(_prin_core.__file__).resolve()),
        "torch": torch.__version__,
        "numpy": np.__version__,
        "platform": sys.platform,
        "summary": _summary(corpus, fuzz),
        "corpus": corpus,
        "fuzz": fuzz,
    }
    args.out.write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(payload["summary"], indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
