r"""EXP-001 D1 S1 — §10.4 item 3 exactness audit of the DV-007 breaches.

Campaign plan §10.4 item 3 allows the correction to conclude that the PRINet
3.0 side is the defective one only on an EMA-style mathematical audit claim,
verified with Z3/SymPy where applicable. This script provides that evidence for
every breach attributed to DV-007 (PRINet 3.0 evaluating its Stuart-Landau and
mean-field derivatives in ``complex64`` inside a float64 model):

* **Exactness (mpmath, 50 significant digits).** For each case, PRINet 3.0's
  own discrete map — its equations, its Euler/RK4 update, its guards
  (amplitude ``max(·, 0)``, ``max(r, 1e-8)`` phase divisor, phase wrap modulo
  the float64 constant ``2.0 * math.pi``) and its metrics — is evaluated in
  arbitrary precision from the case's exact float64 initial state. The
  reference arrays (the stored corpus for H1; a live PRINet 3.0 run for H2a)
  and PRIN's arrays are each compared with that exact evaluation at the
  registered tolerances.
* **Symbolic lemmas (SymPy).** L1-L3 show that PRIN and PRINet 3.0 evaluate
  the same mathematical map, so any difference between them is arithmetic.
  L4 gives the sensitivity of the phase equation near zero amplitude.

Z3 is not used: the claims involve transcendental functions (``sin``, ``cos``,
``exp``, ``atan2``) outside Z3's decidable real-arithmetic fragment. The one
piecewise-linear statement (L4b) is closed-form, so it is checked symbolically.

Run from the repository root with the project venv and a post-fix build::

    python EVIDENCE/exp001-d1-s1/dv007_exactness_audit.py \
        --decomposition EVIDENCE/exp001-d1-s1/root-cause-decomposition-postfix.json \
        --out EVIDENCE/exp001-d1-s1/dv007-exactness-audit.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import mpmath as mp
import numpy as np
import sympy as sp

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))

from prin import _prin_core  # noqa: E402
from prin.parity.harness import compare_arrays  # noqa: E402
from prin.parity.loader import CorpusLoader  # noqa: E402
from prin.parity.schema import CaseArrays  # noqa: E402

from benchmarks.campaign.exp001_driver import (  # noqa: E402
    T_STAR,
    draw_fuzz_initial,
    draw_fuzz_spec,
    run_prin_trajectory,
    run_prinet_trajectory,
)

mp.mp.dps = 50
_TWO_PI = mp.mpf(2.0 * math.pi)  # PRINet 3.0 wraps modulo the float64 constant
_SAFE_AMP = mp.mpf(1e-8)
_TRAJ = (
    "phase_traj",
    "amplitude_traj",
    "frequency_traj",
    "order_parameter_traj",
    "mean_phase_coherence_traj",
)

Vec = list[Any]


# ---------------------------------------------------------------------------
# PRINet 3.0's discrete map in arbitrary precision
# ---------------------------------------------------------------------------


def _derivs(
    model: str, params: dict[str, Any], phase: Vec, amp: Vec, freq: Vec
) -> tuple[Vec, Vec, Vec]:
    """Derivatives of the three DV-007 paths (``oscillator_models.py``)."""
    n = len(phase)
    k = mp.mpf(params["coupling_strength"])
    if model == "stuart_landau":
        mu = mp.mpf(params["bifurcation_param"])
        z = [amp[i] * mp.expj(phase[i]) for i in range(n)]
        dphi: Vec = []
        dr: Vec = []
        for i in range(n):
            coupling = mp.fsum((k / n) * (z[j] - z[i]) for j in range(n) if j != i)
            dz = mp.mpc(mu, freq[i]) * z[i] - amp[i] ** 2 * z[i] + coupling
            w = dz * mp.expj(-phase[i])
            dr.append(w.real)
            dphi.append(w.imag / max(amp[i], _SAFE_AMP))
        return dphi, dr, [mp.mpf(0)] * n
    z_mean = mp.fsum(amp[j] * mp.expj(phase[j]) for j in range(n)) / n
    big_r, psi = abs(z_mean), mp.arg(z_mean)
    gamma = mp.mpf(params.get("freq_adaptation_rate", 0.0))
    sines = [mp.sin(psi - phase[i]) for i in range(n)]
    cosines = [mp.cos(psi - phase[i]) for i in range(n)]
    domega = [gamma * k * big_r * sines[i] / n for i in range(n)]
    if model == "kuramoto":
        decay = mp.mpf(params.get("decay_rate", 0.0))
        dphi = [freq[i] + k * big_r * sines[i] for i in range(n)]
        dr = [-decay * amp[i] + k * big_r * cosines[i] for i in range(n)]
        return dphi, dr, domega
    mu = mp.mpf(params["bifurcation_param"])
    dphi = [freq[i] + k * big_r * sines[i] / max(amp[i], _SAFE_AMP) for i in range(n)]
    dr = [mu * amp[i] - amp[i] ** 3 + k * big_r * cosines[i] for i in range(n)]
    return dphi, dr, domega


def _nonneg(x: Any) -> Any:
    return mp.mpf(0) if x < 0 else x


def _step(
    model: str,
    params: dict[str, Any],
    integrator: str,
    dt: Any,
    phase: Vec,
    amp: Vec,
    freq: Vec,
) -> tuple[Vec, Vec, Vec]:
    """One ``_step_euler`` / ``_step_rk4`` of PRINet 3.0."""
    n = len(phase)
    if integrator == "euler":
        dp, da, df = _derivs(model, params, phase, amp, freq)
        return (
            [(phase[i] + dt * dp[i]) % _TWO_PI for i in range(n)],
            [_nonneg(amp[i] + dt * da[i]) for i in range(n)],
            [freq[i] + dt * df[i] for i in range(n)],
        )

    def stage(k: tuple[Vec, Vec, Vec], scale: Any) -> tuple[Vec, Vec, Vec]:
        return (
            [phase[i] + scale * k[0][i] for i in range(n)],
            [_nonneg(amp[i] + scale * k[1][i]) for i in range(n)],
            [freq[i] + scale * k[2][i] for i in range(n)],
        )

    k1 = _derivs(model, params, phase, amp, freq)
    k2 = _derivs(model, params, *stage(k1, dt / 2))
    k3 = _derivs(model, params, *stage(k2, dt / 2))
    k4 = _derivs(model, params, *stage(k3, dt))

    def comb(base: Vec, c: int) -> Vec:
        return [
            base[i] + (dt / 6) * (k1[c][i] + 2 * k2[c][i] + 2 * k3[c][i] + k4[c][i])
            for i in range(n)
        ]

    return (
        [p % _TWO_PI for p in comb(phase, 0)],
        [_nonneg(a) for a in comb(amp, 1)],
        comb(freq, 2),
    )


def _order_parameter(phase: Vec) -> Any:
    return abs(mp.fsum(mp.expj(p) for p in phase) / len(phase))


def _mean_phase_coherence(phase: Vec) -> Any:
    n = len(phase)
    total = mp.fsum(
        mp.cos(phase[i] - phase[j]) for i in range(n) for j in range(i + 1, n)
    )
    return total / (n * (n - 1) / 2)


def exact_trajectory(
    model: str,
    params: dict[str, Any],
    integrator: str,
    dt: float,
    n_steps: int,
    phase0: np.ndarray,
    amp0: np.ndarray,
    freq0: np.ndarray,
) -> dict[str, np.ndarray]:
    """PRINet 3.0's trajectory from an exact float64 state, in mpmath."""
    phase = [mp.mpf(float(x)) for x in phase0]
    amp = [mp.mpf(float(x)) for x in amp0]
    freq = [mp.mpf(float(x)) for x in freq0]
    step_dt = mp.mpf(float(dt))
    states = [(phase, amp, freq)]
    for _ in range(n_steps):
        phase, amp, freq = _step(model, params, integrator, step_dt, phase, amp, freq)
        states.append((phase, amp, freq))

    def arr(rows: list[Vec]) -> np.ndarray:
        return np.array([[float(v) for v in row] for row in rows], dtype=np.float64)

    return {
        "phase_traj": arr([s[0] for s in states]),
        "amplitude_traj": arr([s[1] for s in states]),
        "frequency_traj": arr([s[2] for s in states]),
        "order_parameter_traj": np.array(
            [float(_order_parameter(s[0])) for s in states], dtype=np.float64
        ),
        "mean_phase_coherence_traj": np.array(
            [float(_mean_phase_coherence(s[0])) for s in states], dtype=np.float64
        ),
    }


# ---------------------------------------------------------------------------
# Per-case audit
# ---------------------------------------------------------------------------


def _compare(
    exact: dict[str, np.ndarray], other: CaseArrays, model: str, horizon: int
) -> dict[str, Any]:
    breaches: list[str] = []
    worst = 0.0
    for name in _TRAJ:
        a = exact[name][: horizon + 1]
        b = getattr(other, name)[: horizon + 1]
        worst = max(worst, float(np.max(np.abs(a - b))))
        if not compare_arrays(a, b, name, model).within_tolerance:
            breaches.append(name)
    return {"breaches": breaches, "max_abs": worst}


def _audit_case(
    label: str,
    spec: dict[str, Any],
    reference: CaseArrays,
    prin: CaseArrays,
    horizon: int,
) -> dict[str, Any]:
    exact = exact_trajectory(
        spec["model"],
        spec["parameters"],
        spec["integrator"],
        spec["dt"],
        horizon,
        prin.phase_init,
        prin.amplitude_init,
        prin.frequency_init,
    )
    ref = _compare(exact, reference, spec["model"], horizon)
    got = _compare(exact, prin, spec["model"], horizon)
    return {
        "case": label,
        "model": spec["model"],
        "coupling": spec["coupling"],
        "integrator": spec["integrator"],
        "horizon": horizon,
        "reference_vs_exact": ref,
        "prin_vs_exact": got,
        "reference_is_the_erroneous_side": bool(ref["breaches"])
        and not got["breaches"],
    }


def _run(runner: Any, spec: dict[str, Any], ph: Any, am: Any, fr: Any) -> CaseArrays:
    result: CaseArrays = runner(
        model=spec["model"],
        coupling=spec["coupling"],
        integrator=spec["integrator"],
        n_oscillators=spec["n_oscillators"],
        n_steps=spec["n_steps"],
        dt=spec["dt"],
        parameters=spec["parameters"],
        phase_init=ph,
        amplitude_init=am,
        frequency_init=fr,
    )
    return result


def audit_h1(decomposition: dict[str, Any]) -> list[dict[str, Any]]:
    """Every H1 breach against the stored corpus."""
    loader = CorpusLoader(_REPO / "parity" / "corpus")
    out = []
    for row in decomposition["corpus"]:
        if not row["e3_breach"]:
            continue
        loaded = loader.load(row["case_id"])
        s = loaded.spec
        spec = {
            "model": s.model,
            "coupling": s.coupling,
            "integrator": s.integrator,
            "n_oscillators": s.n_oscillators,
            "n_steps": s.n_steps,
            "dt": s.dt,
            "parameters": dict(s.parameters),
        }
        a = loaded.arrays
        prin = _run(
            run_prin_trajectory,
            spec,
            a.phase_init,
            a.amplitude_init,
            a.frequency_init,
        )
        out.append(_audit_case(s.case_id, spec, a, prin, s.n_steps))
    return out


def audit_h2a(decomposition: dict[str, Any]) -> list[dict[str, Any]]:
    """Every H2a breach whose only mechanism is DV-007, within the horizon."""
    wanted = {
        r["case_index"]
        for r in decomposition["fuzz"]
        if r["e3_breach"]
        and r["dv007_sensitive"]
        and not r["guard_sensitive"]
        and not r["ill_conditioned"]
    }
    stream = _prin_core.Seed(0, 1)
    out = []
    for index in range(max(wanted) + 1):
        spec = draw_fuzz_spec(stream)
        ph, am, fr = draw_fuzz_initial(stream, spec["n_oscillators"])
        if index not in wanted:
            continue
        reference = _run(run_prinet_trajectory, spec, ph, am, fr)
        prin = _run(run_prin_trajectory, spec, ph, am, fr)
        horizon = min(T_STAR, spec["n_steps"])
        out.append(_audit_case(f"fuzz[{index}]", spec, reference, prin, horizon))
    return out


# ---------------------------------------------------------------------------
# Symbolic lemmas
# ---------------------------------------------------------------------------


def lemmas() -> dict[str, bool]:
    """SymPy checks that PRIN and PRINet 3.0 evaluate one mathematical map."""
    # L1: differentiate z(t) = r(t)·exp(iφ(t)), then name r, φ, ṙ, φ̇ as real
    # symbols so SymPy can take real and imaginary parts.
    t = sp.symbols("t", real=True)
    r_t, phi_t = sp.Function("r")(t), sp.Function("phi")(t)
    r, phi, r_dot, phi_dot = sp.symbols("r phi r_dot phi_dot", real=True)
    z_dot = sp.diff(r_t * sp.exp(sp.I * phi_t), t).subs(
        {sp.Derivative(r_t, t): r_dot, sp.Derivative(phi_t, t): phi_dot}
    )
    z_dot = z_dot.subs({r_t: r, phi_t: phi})
    rotated = sp.expand_complex(sp.expand(z_dot * sp.exp(-sp.I * phi)))
    l1 = (
        sp.simplify(sp.re(rotated) - r_dot) == 0
        and sp.simplify(sp.im(rotated) - r * phi_dot) == 0
    )

    n = 5
    rs = sp.symbols(f"r0:{n}", positive=True)
    ps = sp.symbols(f"p0:{n}", real=True)
    k = sp.symbols("K", positive=True)
    z_mean = sum(rs[j] * sp.exp(sp.I * ps[j]) for j in range(n)) / n
    l2 = all(
        sp.simplify(
            sp.expand_complex(sp.im(z_mean * sp.exp(-sp.I * ps[i])))
            - sum(rs[j] * sp.sin(ps[j] - ps[i]) for j in range(n)) / n
        )
        == 0
        and sp.simplify(
            sp.expand_complex(sp.re(z_mean * sp.exp(-sp.I * ps[i])))
            - sum(rs[j] * sp.cos(ps[j] - ps[i]) for j in range(n)) / n
        )
        == 0
        for i in range(n)
    )

    zs = sp.symbols(f"z0:{n}")
    pairwise = [
        sum((k / n) * (zs[j] - zs[i]) for j in range(n) if j != i) for i in range(n)
    ]
    l3 = all(
        sp.simplify(pairwise[i] - k * (sum(zs) / n - zs[i])) == 0 for i in range(n)
    )

    x, y = sp.symbols("x y", real=True)
    grad = [sp.diff(sp.atan2(y, x), v) for v in (x, y)]
    norm = sp.sqrt(grad[0] ** 2 + grad[1] ** 2)
    l4a = sp.simplify(norm - 1 / sp.sqrt(x**2 + y**2)) == 0
    s, eps = sp.symbols("s epsilon", positive=True)
    l4b = sp.diff(s / eps, s) == 1 / eps
    return {
        "L1_polar_extraction_Re_Im_of_zdot_exp_minus_iphi": bool(l1),
        "L2_mean_field_equals_pairwise_sum_N5": bool(l2),
        "L3_stuart_landau_pairwise_coupling_equals_K_times_mean_minus_self_N5": bool(
            l3
        ),
        "L4a_phase_gradient_norm_is_1_over_r": bool(l4a),
        "L4b_phase_velocity_sensitivity_is_1_over_eps_at_floor": bool(l4b),
    }


def main(argv: list[str] | None = None) -> int:
    """Run the audit and write the JSON evidence file."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--decomposition", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    decomposition = json.loads(args.decomposition.read_text(encoding="utf-8"))
    h1 = audit_h1(decomposition)
    h2a = audit_h2a(decomposition)
    cases = h1 + h2a
    payload = {
        "mpmath_dps": mp.mp.dps,
        "phase_wrap_modulus": "float64 2.0*math.pi (PRINet 3.0 _TWO_PI)",
        "lemmas": lemmas(),
        "summary": {
            "h1_cases": len(h1),
            "h2a_dv007_only_cases": len(h2a),
            "reference_is_the_erroneous_side": sum(
                c["reference_is_the_erroneous_side"] for c in cases
            ),
            "prin_vs_exact_max_abs": max(c["prin_vs_exact"]["max_abs"] for c in cases),
            "prin_vs_exact_breaches": sum(
                bool(c["prin_vs_exact"]["breaches"]) for c in cases
            ),
            "reference_vs_exact_max_abs": max(
                c["reference_vs_exact"]["max_abs"] for c in cases
            ),
        },
        "h1": h1,
        "h2a": h2a,
    }
    args.out.write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"lemmas": payload["lemmas"], **payload["summary"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
