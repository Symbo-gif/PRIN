"""H2a registered-stream differential gate (EXP-001 D1 correction).

EXP-001 H2a drew 1,000 cases from the registered ``Seed(0, 1)`` stream,
integrated PRINet 3.0 and PRIN from one identical explicit initial condition,
and compared them pointwise within the shadowing horizon (steps
``0..min(20, n_steps)``) at the registered corpus tolerances. This module
replays that stream through the same sampler (``draw_fuzz_spec`` /
``draw_fuzz_initial``) and the same two execution paths
(``run_prinet_trajectory`` / ``run_prin_trajectory``) and repeats the
comparison for every case, so the refutation's whole population stays under
CI. Each replayed spec is checked against the committed E3 artefact, and the
whole replayed stream — every spec *including* its drawn ``parameters`` and
all three initial arrays — is fingerprinted by :func:`h2a_stream_digest`
against a committed constant (the E3 artefact stores only the six scalar
identity fields, so without the fingerprint a sampler change could keep
every identity assertion green while testing different physics; see the
independent review of this PR, finding S1).

A breach on a DV-007 ``complex64`` path passes only when PRIN matches the
reference re-evaluated in float64 (:mod:`parity.prinet_f64`) at the same
registered tolerance — the explained-divergence rule of
``test_parity_prin_corpus.py``, whose docstring states the evidence. Any other
breach fails.

Twenty-two cases are excluded from the pointwise comparison because the
reference itself is not pointwise-reproducible there: evaluated in float64,
PRINet 3.0's own map breaches the registered tolerance within the horizon
when its initial phases move by one unit in the last place. In 21 of the 22
the committed decomposition records a native amplitude range bottoming out
at exactly ``0.0`` (case 691 at ``5.6e-3``), the regime where the phase
equation divides by ``max(r, 1e-8)``. Pointwise parity is not a meaningful
criterion for such a case, for PRIN or for any other correct
reimplementation. :func:`test_reference_is_ill_conditioned` re-proves the
reference property for each of them on every run, and
:func:`test_prin_output_on_ill_conditioned_cases_stays_valid` asserts the
registered hazard envelope and the amplitude floor on PRIN's own output for
each of them, so the exclusion removes the pointwise criterion only — never
every PRIN assertion — and cannot silently outlive its evidence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray
from prin import _prin_core
from prin.parity.harness import ComparisonResult, compare_arrays
from prin.parity.schema import CaseArrays

pytest.importorskip("prinet")

from benchmarks.campaign.exp001_driver import (
    T_STAR,
    _case_arrays_hazard_violation,
    draw_fuzz_initial,
    draw_fuzz_spec,
    h2a_stream_digest,
    run_prin_trajectory,
    run_prinet_trajectory,
)
from parity.prinet_f64 import f64_corrected_reference, on_dv007_path

pytestmark = [pytest.mark.parity, pytest.mark.slow]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FUZZ_ARTEFACT = (
    _REPO_ROOT
    / "benchmarks"
    / "results"
    / "EXP-001"
    / "RUN-20260923T134250Z-6b9d6b6-fuzz-cpu"
    / "fuzz_fuzz-cpu.json"
)
#: The registered H2a stream (preregistration §5.12; campaign plan §6.1).
_SEED_COUNTER = 0
_SEED_KEY = 1
_N_CASES = 1000

#: SHA-256 of the full replayed stream — every spec including ``parameters``
#: and all three initial arrays, in case order (``h2a_stream_digest``). This
#: is the bind that the E3 artefact cannot provide (it stores only six scalar
#: identity fields per case); a change to ``draw_fuzz_spec`` /
#: ``draw_fuzz_initial`` (including a parameter-range change) fails loudly
#: against it. The registered stream is immutable under the campaign
#: preregistration, so this constant must not be updated to make a changed
#: sampler pass; a registered stream change requires a new artefact and an
#: amendment. Mirrored in ``EVIDENCE/exp001-d1-s1/root_cause_decomposition.py``.
_H2A_STREAM_DIGEST = "9804fc09e4a510ef0c34dfa5b58c6639a62baf15cf4f38f481ed1c8b854cff76"

#: Case indices where PRINet 3.0's float64 map is ill-conditioned within the
#: horizon (see the module docstring). Evidence:
#: ``EVIDENCE/exp001-d1-s1/root-cause-decomposition-{prefix,postfix}.json``
#: (``summary.ill_conditioned_cases``).
_ILL_CONDITIONED: frozenset[int] = frozenset(
    {
        50, 76, 90, 270, 310, 330, 334, 362, 385, 398, 399,
        415, 456, 522, 621, 623, 653, 691, 734, 841, 867, 878,
    }
)  # fmt: skip

#: The arrays H2a compares, as ``compare_fuzz_case`` does: the three initial
#: arrays whole, then the trajectory arrays through the horizon.
_INIT_ARRAYS = ("phase_init", "amplitude_init", "frequency_init")
_TRAJ_ARRAYS = (
    "phase_traj",
    "amplitude_traj",
    "frequency_traj",
    "order_parameter_traj",
    "mean_phase_coherence_traj",
)
_IDENTITY_FIELDS = ("model", "coupling", "integrator", "n_oscillators", "n_steps", "dt")

_StreamCase = tuple[
    dict[str, Any], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]
]

#: Cases compared pointwise: the full registered stream minus the 22 the
#: reference cannot pointwise-reproduce (see the module docstring).
_POINTWISE_CASES = [i for i in range(_N_CASES) if i not in _ILL_CONDITIONED]


@pytest.fixture(scope="module")
def stream_cases() -> list[_StreamCase]:
    """Replay the registered stream exactly as ``run_fuzz_batch`` consumes it.

    The full replayed stream — specs with ``parameters`` and all three
    initial arrays — is fingerprinted against the committed constant, so a
    sampler change fails here before any case is integrated.
    """
    stream = _prin_core.Seed(_SEED_COUNTER, _SEED_KEY)
    cases: list[_StreamCase] = []
    for _ in range(_N_CASES):
        spec = draw_fuzz_spec(stream)
        phase, amplitude, frequency = draw_fuzz_initial(stream, spec["n_oscillators"])
        cases.append((spec, phase, amplitude, frequency))
    digest = h2a_stream_digest(cases)
    assert digest == _H2A_STREAM_DIGEST, (
        "the replayed H2a stream does not match the committed fingerprint "
        f"{_H2A_STREAM_DIGEST}; a sampler or parameter-range change is "
        f"testing different physics (got {digest})"
    )
    return cases


@pytest.fixture(scope="module")
def recorded_identities() -> list[dict[str, Any]]:
    """Identity fields of every case in the committed E3 fuzz artefact."""
    artefact = json.loads(_FUZZ_ARTEFACT.read_text(encoding="utf-8"))
    assert artefact["config"]["seed_counter"] == _SEED_COUNTER
    assert artefact["config"]["seed_key"] == _SEED_KEY
    cases = artefact["cases"]
    assert [case["case_index"] for case in cases] == list(range(_N_CASES))
    return [{field: case[field] for field in _IDENTITY_FIELDS} for case in cases]


def _run(
    runner: Any,
    spec: dict[str, Any],
    phase: NDArray[np.float64],
    amplitude: NDArray[np.float64],
    frequency: NDArray[np.float64],
) -> CaseArrays:
    """Integrate one replayed case through ``runner`` from its explicit state."""
    result: CaseArrays = runner(
        model=spec["model"],
        coupling=spec["coupling"],
        integrator=spec["integrator"],
        n_oscillators=spec["n_oscillators"],
        n_steps=spec["n_steps"],
        dt=spec["dt"],
        parameters=spec["parameters"],
        phase_init=phase,
        amplitude_init=amplitude,
        frequency_init=frequency,
    )
    return result


def _h2a_breaches(
    reference: CaseArrays, produced: CaseArrays, model: str, n_steps: int
) -> list[ComparisonResult]:
    """Return every H2a comparison outside the registered tolerance."""
    horizon = min(T_STAR, n_steps)
    results = [
        compare_arrays(getattr(reference, name), getattr(produced, name), name, model)
        for name in _INIT_ARRAYS
    ] + [
        compare_arrays(
            getattr(reference, name)[: horizon + 1],
            getattr(produced, name)[: horizon + 1],
            name,
            model,
        )
        for name in _TRAJ_ARRAYS
    ]
    return [result for result in results if not result.within_tolerance]


def _describe(breaches: list[ComparisonResult]) -> str:
    return "; ".join(
        f"{r.array_name} max_abs_diff={r.max_abs_diff:.6e} "
        f"failed={r.failed_count}/{r.total_count}"
        for r in breaches
    )


@pytest.mark.parametrize("case_index", _POINTWISE_CASES)
def test_prin_matches_prinet_within_horizon(
    stream_cases: list[_StreamCase],
    recorded_identities: list[dict[str, Any]],
    case_index: int,
) -> None:
    """PRIN matches PRINet 3.0 within the horizon, or the breach is exactly DV-007."""
    spec, phase, amplitude, frequency = stream_cases[case_index]
    assert {f: spec[f] for f in _IDENTITY_FIELDS} == recorded_identities[case_index]
    label = f"case {case_index} ({spec['model']}/{spec['coupling']}/" + (
        f"{spec['integrator']})"
    )
    reference = _run(run_prinet_trajectory, spec, phase, amplitude, frequency)
    produced = _run(run_prin_trajectory, spec, phase, amplitude, frequency)
    breaches = _h2a_breaches(reference, produced, spec["model"], spec["n_steps"])
    if not breaches:
        return
    assert on_dv007_path(spec["model"], spec["coupling"]), (
        f"{label} diverges off the DV-007 paths: {_describe(breaches)}"
    )
    with f64_corrected_reference():
        corrected = _run(run_prinet_trajectory, spec, phase, amplitude, frequency)
    residual = _h2a_breaches(corrected, produced, spec["model"], spec["n_steps"])
    assert not residual, (
        f"{label} breach is not explained by DV-007: {_describe(residual)}"
    )


@pytest.mark.parametrize("case_index", sorted(_ILL_CONDITIONED))
def test_reference_is_ill_conditioned(
    stream_cases: list[_StreamCase], case_index: int
) -> None:
    """PRINet 3.0 in float64 cannot reproduce itself under a 1-ulp phase change."""
    spec, phase, amplitude, frequency = stream_cases[case_index]
    nudged = np.nextafter(phase, np.inf)
    with f64_corrected_reference():
        first = _run(run_prinet_trajectory, spec, phase, amplitude, frequency)
        second = _run(run_prinet_trajectory, spec, nudged, amplitude, frequency)
    assert _h2a_breaches(first, second, spec["model"], spec["n_steps"]), (
        f"case {case_index} is no longer ill-conditioned; it must rejoin the "
        "pointwise comparison"
    )


@pytest.mark.parametrize("case_index", sorted(_ILL_CONDITIONED))
def test_prin_output_on_ill_conditioned_cases_stays_valid(
    stream_cases: list[_StreamCase], case_index: int
) -> None:
    """PRIN's own output stays inside the registered hazard envelope here.

    These 22 cases are excluded from *pointwise* parity because the float64
    reference cannot reproduce itself on them — not from every PRIN
    assertion. The residuals between PRIN and the float64 reference are O(1)
    there (they sit in the reference's chaotic regime), so a residual ceiling
    is not meaningful; what must hold for any faithful implementation is the
    registered hazard envelope (finiteness, wrapped phase, metric ranges) and
    the amplitude floor this correction redefined. Three of the 22
    (330, 385, 841) are off the DV-007 paths entirely — their recorded E3
    breach is the guard mechanism this PR changed — so without this test the
    fuzz gate would place no constraint on PRIN for them at all.
    """
    spec, phase, amplitude, frequency = stream_cases[case_index]
    produced = _run(run_prin_trajectory, spec, phase, amplitude, frequency)
    violation = _case_arrays_hazard_violation(f"case {case_index}", produced)
    assert violation is None, violation
    assert np.all(produced.amplitude_traj >= 0.0), (
        f"case {case_index}: negative amplitude in PRIN output under the "
        "NonNegative guard"
    )


def test_every_registered_case_is_covered() -> None:
    """The parametrizations partition the registered stream exactly once."""
    pointwise = set(_POINTWISE_CASES)
    characterised = set(_ILL_CONDITIONED)
    assert pointwise.isdisjoint(characterised)
    assert pointwise | characterised == set(range(_N_CASES))
    assert len(_POINTWISE_CASES) + len(_ILL_CONDITIONED) == _N_CASES
