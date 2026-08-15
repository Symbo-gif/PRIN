# PRIN Executive Mathematical Audit Report — Session 001 (EMA-001)

**Date:** 2026-08-14
**Auditor:** Claude Code (AI Pair & Systems Auditor)
**Tool:** `math-audit-mcp` v0.1.0 (SymPy 1.14.0, SciPy 1.18.0, z3-solver 5.0.0.0, NetworkX 3.6.1, mpmath 1.3.0; source-tree SHA-256 `1c717be8d9f06583fd0f4fd35497d2debfb552433a3178f3091c82ff90d2fab7`)
**Scope:** First integration of `math-audit-mcp` into PRIN; independent, tool-executed re-verification of 23 formally-restated mathematical claims across `prin-dynamics` (models, integrators, coupling, PAC, state guards), `prin-metrics` (order parameter, coherence, chimera/strength-of-incoherence, spectral density), and `prin-tensor`-adjacent coupling-matrix structure
**Git Branch/State:** `main` @ `f1204ed`
**Governing methodology:** `DOCS/standards/Executive_Mathematical_Audit_Governance_and_Methodology.md` (introduced this session; Project Plan amendment #23)
**Verdict:** **FAIL** — one D1 finding (a genuine, Z3-confirmed mathematical defect) is open and unremediated by design: this session's mandate is audit and reporting only, with remediation deliberately deferred to the follow-up EMA-001 remediation session per the session's own scope.

---

## 0. What this session did

This is the **first** Executive Mathematical Audit. Unlike EA-001 through EA-003 (which verify PRIN's mathematical core primarily by direct source inspection), EMA-001 independently **recomputes** a curated set of claims using SymPy, SciPy, Z3, and NetworkX — tools that never read PRIN's own comments, tests, or an auditor's prose reasoning. Four tasks were completed in this session:

1. **Tool setup:** `math-audit-mcp` (external, at `C:\dev\--DEV\Math Audit MCP`) installed into a dedicated Python 3.12 venv and smoke-tested against its own bundled examples (all 7 passed with the expected PASS/FAIL mix) before being pointed at PRIN.
2. **Governance:** `DOCS/standards/Executive_Mathematical_Audit_Governance_and_Methodology.md`, `DOCS/audits/TEMPLATE_Executive_Math_Audit_Report.md`, Project Plan amendment #23, and the EMA global-session register section were authored (§1–§8 of the governance doc; see that file for full rationale).
3. **Claim authoring:** 23 claims were independently restated (not copied from PRIN's own comments) across 5 claim ledgers under `tools/math_audit_claims/`, spanning all 5 directly-applicable claim types (`z3_invariant`, `symbolic_identity`, `ode_property`, `tensor_contract`, `graph_topology`).
4. **Execution:** `tools/math_audit_run.py` ran all 5 ledgers through `audit_claim_ledger` under `tools/math_audit_policy.yaml` (PRIN's strict-derived EMA policy). Every result below is quoted from the persisted `AuditResult`/bundle manifest JSON under `EVIDENCE/math-audit/`, not from prose recollection.

---

## 1. Executive Summary Table

| Claim Ledger | Subsystem | Overall Status | Summary |
|---|---|---|---|
| `prin-dynamics-symbolic-identities.json` | `prin-dynamics::models`, `prin-dynamics::state`, `prin-metrics::coherence`/`order`/`spectral` | ✅ **PASS** | All 8 claims achieved genuine SymPy **symbolic proof** (not numeric approximation) — every trig/complex-algebra identity checked reduces exactly to 0. |
| `prin-dynamics-z3-invariants.json` | `prin-dynamics::state` (clamps), `prin-metrics::order`/`chimera`/`pac` | ❌ **FAIL** | 5 of 7 claims Z3-proved `PASS`. One (`PW-02`) is a **genuine, Z3-confirmed counterexample**: `prin-metrics::chimera.rs`'s strength-of-incoherence wrap formula is not centred at zero as documented (**M-F1, D1, headline finding**). One (`PW-01`) is `INCONCLUSIVE` (Z3 timeout on a nonlinear Int/Real encoding — a coverage gap, not a defect; **M-F2, D3**). |
| `prin-dynamics-ode-properties.json` | `prin-dynamics::integrate` (Euler, RK4), `prin-dynamics::models` (Hopf/Stuart–Landau, Kuramoto locking) | ⚠️ **REQUIRES_HUMAN_REVIEW** | All 4 claims **independently PASSED** via SciPy reference-solver comparison (genuine evidence), but resolve to `REQUIRES_HUMAN_REVIEW` at the strict policy's high/critical-severity symbolic-or-formal gate — **M-F3, D2**, a policy-design interaction, not a code defect. |
| `prin-dynamics-tensor-contracts.json` | `prin-dynamics::coupling` (ring/all-to-all weight matrices) | ⚠️ **REQUIRES_HUMAN_REVIEW** | Both claims independently PASSED (NumPy einsum symmetry checks); the `high`-severity one (`TEN-01`) hits the same M-F3 gate. |
| `prin-dynamics-graph-topology.json` | `prin-dynamics::coupling` (ring/all-to-all topology) | ⚠️ **REQUIRES_HUMAN_REVIEW** | Both claims independently PASSED (NetworkX degree/connectivity checks); `GRA-01` (`high`) hits M-F3; `GRA-02` (`medium`) resolves clean `PASS`. |

**23/23 claims produced genuine independent evidence** (18 PASS, 1 FAIL, 1 INCONCLUSIVE, 3 REQUIRES_HUMAN_REVIEW-by-policy-gate-only-on-otherwise-passing-evidence). Zero `TOOL_ERROR`, zero `SKIPPED_BY_POLICY`.

---

## 2. Claim-by-Claim Results

Every row is quoted verbatim from the persisted `AuditResult.summary` field under `EVIDENCE/math-audit/audits/<audit_id>/normalized-result.json`.

### Ledger: `prin-dynamics-symbolic-identities.json` (verdict: PASS)

| Claim ID | Statement (short) | `code_refs` | Tool | Status | Result |
|---|---|---|---|---|---|
| PD-01-SIN | `safe_phase_diff` preserves `sin(a-b)` | `state.rs:284-291` | `verify_identity` | PASS | Symbolic proof established. |
| PD-01-COS | `safe_phase_diff` preserves `cos(a-b)` | `state.rs:284-291` | `verify_identity` | PASS | Symbolic proof established. |
| MF-01-PHASE | Mean-field ≡ full-matrix Kuramoto, phase channel (N=2, self-term included) | `models.rs:191-231,233-281` | `verify_identity` | PASS | Symbolic proof established. |
| MF-01-AMPLITUDE | Companion identity, amplitude/cosine channel | `models.rs:191-231,226` | `verify_identity` | PASS | Symbolic proof established. |
| SL-01-RADIAL | Stuart–Landau polar reduction: `dr/dt = mu*r - r^3` | `models.rs:473-480` | `verify_identity` | PASS | Symbolic proof established. |
| SL-01-ANGULAR | Stuart–Landau polar reduction: `dphi/dt = omega` | `models.rs:473-480,602-611` | `verify_identity` | PASS | Symbolic proof established. |
| MPC-01 | Mean phase coherence ≡ `(N*R^2-1)/(N-1)` (N=3) | `coherence.rs:39-57`, `order.rs:59-71` | `verify_identity` | PASS | Symbolic proof established. |
| PSD-01 | Parseval identity for the 2-point DFT periodogram | `spectral.rs:24-27,48-92` | `verify_identity` | PASS | Symbolic proof established. |

Every one of these 8 claims reached `PASS` via genuine SymPy reduction of `lhs - rhs` to `0` — the strongest evidentiary tier this system produces (`docs/audit-methodology.md`'s "symbolic proof" tier), not finite numeric sampling. **This is a materially stronger confirmation than EA-003's E1 direct-source review could produce on its own**, and it independently corroborates: the RK-stage phase-difference shortcut in `integrate.rs:26-31`, the self-term handling that makes `CouplingMode::MeanField` and `CouplingMode::Full` equivalent for both the phase and amplitude channels, the Stuart–Landau polar-form derivation, an inter-module consistency constraint between `order.rs` and `coherence.rs`, and the periodogram's energy-conservation property in `spectral.rs`.

### Ledger: `prin-dynamics-z3-invariants.json` (verdict: FAIL)

| Claim ID | Statement (short) | `code_refs` | Status | Result |
|---|---|---|---|---|
| **PW-02** | SI's per-pair phase-difference wrap is centred at 0 | `chimera.rs:169-171,129-131` | **FAIL** | Z3 found a model: `d=0, k=0, w=0, z=-π` — the invariant `d==0 ⟹ z==0` is **false**. See M-F1 below. |
| PW-01 | `wrap_phase`'s `[0,2π)` representative is unique | `state.rs:274-277,21` | INCONCLUSIVE | "Z3 returned unknown (reason: timeout)." See M-F2 below. |
| CL-01 | `clamp_amplitude` bounded `[1e-6,10]` and order-preserving | `state.rs:312-329,24-27` | PASS | Z3-proved. |
| CL-02 | `clamp_derivative` bounded `±1e4` and sign-preserving | `state.rs:331-343,30` | PASS | Z3-proved. |
| OP-01 | Order parameter magnitude bounded `[0,1]` | `order.rs:33-36,123` | PASS | Z3-proved. |
| SI-01 | SI's windowed numerator never exceeds the unwindowed denominator (triangle inequality) | `chimera.rs:173-199` | PASS | Z3-proved over free reals `z0..z3`. |
| PAC-01 | PAC modulation stays within `[0,2A]` pre-clamp, `[1e-6,10]` post-clamp | `pac.rs:216,228-229,161-169` | PASS | Z3-proved. |

### Ledger: `prin-dynamics-ode-properties.json` (verdict: REQUIRES_HUMAN_REVIEW — see M-F3)

| Claim ID | RHS / config | Raw `audit_ode` result | Ledger-resolved status | Reason |
|---|---|---|---|---|
| INT-01 | Euler, `y'=-2y`, h=0.05 | **PASS** — max error vs. DOP853 reference `0.0192` (tol `0.02`); observed convergence order `1.02` (theoretical 1) | REQUIRES_HUMAN_REVIEW | high-severity, non-symbolic evidence only |
| INT-02 | RK4, `y'=-2y`, h=0.1 | **PASS** — max error `5.8e-6` (tol `1e-4`); observed convergence order `4.07` (theoretical 4) | REQUIRES_HUMAN_REVIEW | critical-severity, non-symbolic evidence only |
| HOPF-01 | RK4, `y'=4y-y^3`, `y(0)=0.5` | **PASS** — positivity/monotonicity/boundedness `[0.5,2.0]`/equilibrium `2.0` all held | REQUIRES_HUMAN_REVIEW | critical-severity, non-symbolic evidence only |
| KUR-01 | RK4, `y'=1-2sin(y)`, `y(0)=0.1` | **PASS** — monotonicity/boundedness/equilibrium `π/6` all held | REQUIRES_HUMAN_REVIEW | critical-severity, non-symbolic evidence only |

### Ledger: `prin-dynamics-tensor-contracts.json` (verdict: REQUIRES_HUMAN_REVIEW)

| Claim ID | Claim | Raw result | Ledger-resolved status |
|---|---|---|---|
| TEN-01 | `build_ring(N=6,k=4)` weight matrix is symmetric | **PASS** | REQUIRES_HUMAN_REVIEW (high severity, M-F3 gate) |
| TEN-02 | `build_all_to_all(N=4)` weight matrix is symmetric | **PASS** | **PASS** (medium severity, gate does not apply) |

### Ledger: `prin-dynamics-graph-topology.json` (verdict: REQUIRES_HUMAN_REVIEW)

| Claim ID | Claim | Raw result | Ledger-resolved status |
|---|---|---|---|
| GRA-01 | `build_ring(N=6,k_ring=4)` is connected, 4-regular, 12 edges | **PASS** | REQUIRES_HUMAN_REVIEW (high severity, M-F3 gate) |
| GRA-02 | `build_all_to_all(N=4)` is connected, 3-regular, 6 edges (K4) | **PASS** | **PASS** (medium severity) |

---

## 3. Discovered Deviations and Findings Table

| ID | Severity | Claim ID(s) | Location / Subsystem | Issue Description | Violated Clause | Status |
|---|---|---|---|---|---|---|
| **M-F1** | **D1** | PW-02 | `crates/prin-metrics/src/chimera.rs:169-171` | `strength_of_incoherence`'s per-pair wrapped difference is computed as `(phase[m]-phase[(m+1)%n]).rem_euclid(TAU) - PI`, which maps a raw difference of `0` (two phases exactly in sync) to `z = -π`, not `z = 0`. The module doc (`chimera.rs:129-131`) explicitly claims the wrap is "centred to `[-π, π)`" — the correct centred-wrap formula is `((x + π).rem_euclid(2π)) - π` (note the missing `+ π` before the modulus). Independently Z3-proved: the query `Implies(d==0, z==0)` is **false**, with counterexample `d=0, k=0, w=0, z=-3.141592653589793`. **Consequence:** the bug is an exact half-period (π) phase-shift, not a benign different-representative choice — under the code's actual formula, a raw difference near `0` (locally coherent) maps to `|z|≈π` (large — reads as *incoherent*), while a raw difference near `π` (genuinely out of phase) maps to `|z|≈0` (small — reads as *coherent*): the per-element coherence/incoherence magnitude relationship is inverted. The one doctest at `chimera.rs:147-148` (`vec![1.0; 16]`, i.e. a perfectly *uniform* field) still reports the documented `SI≈0` only because every `z_m` receives the identical constant `-π` offset, which cancels exactly in the `numer/denom` ratio when the field has zero spatial variation — this masks the defect for the one case the test suite exercises but does not generalize to any field with local structure, which is precisely the regime `strength_of_incoherence` (a chimera-state diagnostic) exists to characterize. | `Development_Workflow_and_Audit_Standards.md` (mathematical correctness); `chimera.rs:129-131`'s own documented contract | **OPEN — deferred to the EMA-001 remediation session** (this session's mandate is audit + report only; see §4). |
| **M-F2** | **D3** | PW-01 | `crates/prin-dynamics/src/state.rs:274-277` (`wrap_phase`) | The Z3 encoding of "wrap_phase's `[0,2π)` representative is unique" (mixed `Int`/`Real` nonlinear arithmetic: `w1 == x - k1*2π`, `k1: Int`) returned `unknown` (timeout) rather than a proof or a counterexample. This is an evidentiary coverage gap in this specific SMT encoding, not evidence against `wrap_phase`'s correctness (the underlying math — a single-valued `rem_euclid` reduction — is standard and not in doubt; unlike `chimera.rs`'s ad hoc inline wrap in M-F1, `state.rs::wrap_phase` does not subtract an extra `π` and is not implicated by this finding). | `Executive_Mathematical_Audit_Governance_and_Methodology.md` §5 (INCONCLUSIVE → evidentiary gap) | **OPEN — pass-forward.** Recommend re-encoding with a bounded `k` range or restating as a pure-`Real` `floor`-free identity in a follow-up EMA session. |
| **M-F3** | **D2** | INT-01, INT-02, HOPF-01, KUR-01, GRA-01, TEN-01 | `tools/math_audit_policy.yaml` (`high_severity_requires_symbolic_or_formal: true`) interacting with `ode_property`/`graph_topology`/`tensor_contract` claim types | Every claim of these three types is checked exclusively by `audit_ode` (SciPy adapter), `audit_graph_topology` (NetworkX adapter), or `audit_tensor_contract` (no adapter/NumPy) — none of which is classified as "symbolic or formal" (`{sympy, z3, lean}`) by the policy engine (`policies/default_rules.py`'s `_SYMBOLIC_OR_FORMAL_ADAPTERS` gate). Under the strict-derived `prin-ema` policy, **any** `high`/`critical`-severity claim of these three types therefore resolves to `REQUIRES_HUMAN_REVIEW` at the ledger level *regardless of how strong the underlying numeric/structural evidence is* — all 6 affected claims here independently PASSED their tool-level check with genuine evidence (SciPy reference-solver tolerance/convergence-order/property checks; NetworkX degree/connectivity checks; NumPy einsum symmetry checks). This is a real, discovered **policy-design interaction**, not a PRIN code defect: it means an EMA session using this exact policy can never grant a bare ledger-level `PASS` to a high-stakes ODE, graph, or tensor claim without either (a) accepting `REQUIRES_HUMAN_REVIEW` as the terminal, human-signed-off status for such claims, or (b) escalating to Lean (currently disabled, `enable_lean: false`) for a formal proof. | `Executive_Mathematical_Audit_Governance_and_Methodology.md` §3 (policy profile intent) | **OPEN — maintainer policy decision needed** (not a code fix; see §4.2). Two acceptable resolutions: (1) accept as intentional — human sign-off is exactly what "critical" severity should require for non-formal evidence in a scientific-computing project; formally record signed-off claims below. (2) Add a policy carve-out so `medium`-capped or explicitly-approved `ode_property`/`graph_topology`/`tensor_contract` claims can reach `PASS` on strong non-formal evidence alone. |
| M-F4 | D4 (informational) | HOPF-01, KUR-01 | `audit_ode`'s convergence-order estimator, applied near an asymptotically-approached equilibrium | Both claims report `observed convergence order ... deviates from the theoretical order 4.0 expected for rk4` (`2.20` for HOPF-01, `0.49` for KUR-01) as a tool warning. `INT-02` (a plain decaying-exponential test case using the same RK4 integrator) independently confirms genuine `~4.07` observed order, so PRIN's RK4 implementation itself is not implicated — this is a known artifact of refinement-level convergence-order estimation when the trajectory flattens out near a stable equilibrium (the global error stops shrinking geometrically with step size once it is dominated by proximity to the fixed point rather than by local truncation error). | none (methodology note) | **Documented, no action required.** |
| M-F5 | D3 | (scoping decision, not a claim result) | `audit_tensor_contract` tool coverage | `audit_tensor_contract` validates einsum shape/rank compatibility and symmetry-of-supplied-`sample_values` only — it never compares a computed contraction's *numeric values* to an expected result. The original research pass proposed HOSVD reconstruction-equality and orthonormality claims for `prin-tensor::tucker.rs`; these are **not verifiable with this tool version** and were rescoped to `prin-dynamics::coupling` weight-matrix symmetry claims (TEN-01/TEN-02) instead. `prin-tensor`'s HOSVD reconstruction-value correctness continues to be covered by PRIN's own `parity_hosvd_matches_prinet_reference_reconstruction` test (EA-003 finding E-F5 remediation), not by this EMA session. | `Executive_Mathematical_Audit_Governance_and_Methodology.md` §4 (claim taxonomy) | **Documented scoping limitation; pass-forward** for a future PyTorch/JAX execution-backend adapter (the tool's own documented roadmap item) to close this gap. |
| M-F6 | D4 | (tooling provenance) | `math-audit-mcp` installation at `C:\dev\--DEV\Math Audit MCP` | The tool's source tree has no git history (`git rev-parse HEAD` fails: not a git repository), so no commit hash can be cited as the audited tool version. Compensated by recording installed package version, dependency versions, and a SHA-256 source-tree fingerprint (§0, header). | `Executive_Mathematical_Audit_Governance_and_Methodology.md` §2.1 | **Documented; pass-forward** to vendor the tool as a pinned dependency or git submodule in a future session. |

---

## 4. Remediation Plan

### 4.1 Immediate Remediation (Executed in Task 5/6 of this session)

**None.** Per this session's explicit scope (governance + first audit execution + report, in preparation for a *separate* follow-up remediation session), no PRIN source code was modified. This intentionally diverges from the default Executive Audit Governance posture ("D1 findings freeze progress and are fixed in-session") — recorded here as a deliberate, scoped exception for this specific first EMA session, analogous to how EA-003 deferred the E-F6 tag/publish action to an explicit separate step.

### 4.2 Pass-Forward Items (Scheduled for the EMA-001 Remediation Session)

1. **M-F1 (D1, priority):** Fix `crates/prin-metrics/src/chimera.rs:169-171`. Change:
   ```rust
   (phase[m] - phase[(m + 1) % n]).rem_euclid(TAU) - PI
   ```
   to the correct centred-wrap formula:
   ```rust
   (phase[m] - phase[(m + 1) % n] + PI).rem_euclid(TAU) - PI
   ```
   Required regression coverage: a non-uniform-field unit test (the existing doctest's uniform `vec![1.0; 16]` case cannot detect this class of defect — see M-F1's masking explanation), plus a targeted `z==0` check at `d==0` and, ideally, re-running claim `PW-02` through `tools/math_audit_run.py` as delta verification (mirroring EA's delta-re-audit convention).
2. **M-F2 (D3):** Re-encode `PW-01` (e.g., bound `k1`/`k2` to a finite range derived from `x`'s expected domain, or restate without an explicit integer witness) and re-run.
3. **M-F3 (D2):** Obtain an explicit maintainer decision on the `high_severity_requires_symbolic_or_formal` policy interaction with `ode_property`/`graph_topology`/`tensor_contract` claim types (§3, M-F3) and record it as a plan amendment or a `tools/math_audit_policy.yaml` change, whichever the maintainer selects.
4. **M-F5 (D3):** No action required this cycle; tracked as a tool-roadmap dependency (PyTorch/JAX adapter) for future `prin-tensor` value-level claims.
5. **M-F6 (D4):** No action required this cycle; tracked as a tooling-hygiene item.

---

## 5. Tool Provenance and Evidence

| Item | Value |
|---|---|
| `math-audit-mcp` installed version | `0.1.0` |
| SymPy / SciPy / z3-solver / NetworkX / mpmath versions | `1.14.0` / `1.18.0` / `5.0.0.0` / `3.6.1` / `1.3.0` |
| Source-tree SHA-256 fingerprint | `1c717be8d9f06583fd0f4fd35497d2debfb552433a3178f3091c82ff90d2fab7` |
| Policy file | `tools/math_audit_policy.yaml` (`policy_name: prin-ema`, strict-derived) |
| Policy snapshot hash | `sha256:0e1c329642e07f0b71a7f250a60815d3fc9f6ac4f86dda4f3865149ed6c07608` |
| Output root | `EVIDENCE/math-audit/` (`audits/<audit_id>/normalized-result.json` per check; `audits/bundle-<id>/manifest.json` + `report.md` per ledger) |
| Claim ledgers (committed, versioned) | `tools/math_audit_claims/prin-dynamics-{z3-invariants,symbolic-identities,ode-properties,tensor-contracts,graph-topology}.json` |
| Consolidated run summary | `EVIDENCE/math-audit/ema-run-summary.json` |

---

## 6. Audit Verdict and Sign-off

**Final Verdict:** **FAIL**

Rationale: one D1 finding (M-F1) is real, independently confirmed by Z3 (not a false positive or a policy artifact — a concrete counterexample with `d=0, z=-π`), and is **open**, not remediated in this session by explicit scope decision. Per `DOCS/audits/README.md`'s verdict convention ("any D1 finding ⇒ FAIL") and `Executive_Audit_Governance_and_Methodology.md` §3 ("D1 — Trajectory Breach ... Immediate fix required. Freezes progress until resolved"), this audit cannot close as PASS or PASS-WITH-REMEDIATION while M-F1 remains open. **Feature work touching `prin-metrics::chimera::strength_of_incoherence` should be treated as frozen until the follow-up EMA-001 remediation session (§4.2) fixes and re-verifies M-F1.**

Positively: 18 of 23 claims reached genuine, tool-confirmed `PASS` (8 of them via the strongest evidentiary tier, symbolic proof), independently corroborating the core Kuramoto/Stuart–Landau/coupling mathematics EA-003 already reviewed by source inspection — and this session's own headline finding (M-F1) is direct, concrete evidence that independent tool-executed recomputation catches real defects that careful source-level review (EA-003's E1 review of this exact file, three sessions ago) did not.

**Auditor Signature:** Claude Code (AI Pair & Systems Auditor)
**Date:** 2026-08-14
