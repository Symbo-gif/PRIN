# PRIN Executive Audit Report — Session 002 (EA-002)

**Date:** 2026-08-08
**Auditor:** Qwen Code (AI Pair & Systems Auditor)
**Scope:** Full Project Executive Audit (Mathematics, Codebase Architecture, Testing & Parity, Security & Supply Chain, Standards & Documentation, Evidence & Analytics, Governance & Traceability, Performance & Benchmarking, CI/CD Infrastructure, Roadmap & Handoff)
**Audit window:** Delta since EA-001 (`d1e6e0a`, 2026-08-07) through `f5ae5b7` — Sessions 0025–0036 (WP-007, WP-008, WP-009 cycles) plus full-project re-verification
**Git Branch/State:** `feat/wp006-oscillator-state` @ `f5ae5b7`
**Verdict:** **PASS-WITH-REMEDIATION**

---

## 1. Executive Summary Table

| Audit Dimension | Status | Summary & Key Observations |
|---|---|---|
| **E1: Math & Oscillator Dynamics Core** | ✅ PASS | New dynamics core since EA-001 verified: `Dynamics` trait with Kuramoto/Stuart–Landau/Hopf models (mean-field O(N), full O(N²), sparse k-NN O(N·k)); Euler/RK4/adaptive DOPRI5 RK45 integrators (Butcher tableau verified coefficient-by-coefficient; FSAL invalidation correct); `PhaseAmplitudeCoupling`; `Topology` builders with `K/degree` energy invariant. All guards (phase wrap, amplitude/derivative clamps, `1e-8` radius floors) in place. Three documentation-accuracy findings (E-F7..E-F9), no mathematical defects. |
| **E2: Codebase & Architecture Conformance** | ✅ PASS | Crate layering intact (`prin-dynamics` → `prin-kernels` → `_prin_core` → `python/prin`); `#![forbid(unsafe_code)]` on all crates except the two audited FFI exceptions (`prin-py/src/dlpack.rs`, `prin-kernels` kernel-FFI module) per amendments #6/#8; "no numerics in Python" holds (bridge layer is pure orchestration). |
| **E3: Test Suite & Parity Corpus** | ⚠️ REMEDIATION | 184 Python tests (172 fast + 6 parity differential + benchmarks), 222 default / 225 strict Rust tests all pass in isolated runs. **Finding E-F1 (D2):** `test_phase0_gate_integration_with_ort` rewrites the committed `EVIDENCE/0017-wp005-s1-ort-probe.json` on every full suite run — reopened root cause behind WP007-F4. Fixed in Task 5. |
| **E4: Security & Supply Chain** | ⚠️ REMEDIATION | `cargo audit` 0 vulnerabilities (1 allowed advisory, amendment #9); `pip-audit` 0 findings (project + sphinx); bandit 0; ruff-S clean. Snyk Code (CLI, low threshold): 9 low findings — 6 in the archived PRINet 3.0 tree due to a **broken `.snyk` exclude pattern** (E-F3), 3 in `tools/wp001_baseline.py` accepted by documented policy exception (E-F4). Snyk SCA not executable in this session (MCP server absent; CLI pip paths unsupported) — compensated by pip-audit/cargo-audit locally and the `python.yml` Snyk SCA CI job on push (E-F5). |
| **E5: Standards & Documentation Adherence** | ⚠️ REMEDIATION | `interrogate` 100% public; mypy --strict clean; ruff/format clean; `cargo doc` and Sphinx verified in Task 6. Findings: stale README indexes in `DOCS/experiments/` (E-F10) and `DOCS/audits/` (E-F11); crate-level rustdoc drift (E-F7); integrate.rs typo (E-F8); workflow recipes hard-coded to audit "001" (E-F12). |
| **E6: Evidence, Baselines & Analytics** | ⚠️ REMEDIATION | ONNX controller model SHA-256 matches evidence record (`3396bfdd…4102`); `tools/wp001_baseline.py check` green; corpus manifest digests re-validated by the parity differential suite (504 cases). **However** the committed ORT-probe evidence file was found mutated in the working tree (timestamp drift) — traced to E-F1; restored in Task 5. Phase 0 analytics report unchanged and consistent. |
| **E7: Session Cycle & Governance Traceability** | ⚠️ REMEDIATION | Cycles 007–009 executed full S1–S4 with closure tables; deviation ledger complete with no carried findings. **Finding E-F2 (D2):** EA-001's report and CHANGELOG claim a session-register update (EA-001 registered as Global Session 0025, WP-007 re-mapped to 0026) that was **never committed** — commit `d1e6e0a` touches no session files, and the register (authoritative, validator-green) numbers WP-007 S1 as 0025. EA sessions are now formally registered outside the planned 0001–0198 sequence via amendment #15. |
| **E8: Performance, Benchmarking & Reproducibility** | ✅ PASS | DLPack bridge latency benchmarks reproducible (round-trip ~4.4 µs f32 / ~5.4 µs f64 median; batched ~26–30 µs); Rust kernel-equivalence and RK4-order tests green. Note: `benchmarks/` category scripts remain Phase 6 (WP-033) scope — EA-001's E8 wording overstated their existence (corrected under E-F2). |
| **E9: CI/CD & Build Infrastructure** | ✅ PASS | All seven workflows present (`python.yml`, `rust.yml`, `snyk.yml`, `parity.yml`, `repro.yml`, `release.yml`, `gpu.yml`); `rust.yml` runs default + `strict-checks` clippy/test plus `prin-kernels --features cpu`; `python.yml` security job runs pip-audit + Snyk SCA (`uv pip compile` recipe) at low threshold with `--fail-on=all`; `snyk.yml` runs Snyk Code (medium) + full-history gitleaks. |
| **E10: Roadmap, Risks & Future Session Handoff** | ⚠️ REMEDIATION | Phase 1 at 4 of 6 WPs complete; WP-010 declared with brief `0037` READY and maintainer approval pending (E-F6). Plan amendment #14 recorded but approval pending since WP-007 S3 (E-F6). Pass-forward placeholders WP-010..WP-039 verified in the session register. |

---

## 2. Detailed Findings across Audit Dimensions

### E1: Mathematical & Oscillator Dynamics Core Integrity

New since EA-001 (WP-007/008/009 scope), all directly reviewed:

- **`Dynamics` trait** (`crates/prin-dynamics/src/models.rs`): uniform `compute_derivatives(&OscillatorState) -> Result<StateDerivatives, StateError>`; population-size validation, `n ≤ 1` degenerate handling, enum-dispatched `CouplingMode` (no string dispatch).
- **Kuramoto** (mean-field/full/sparse): amplitude-weighted complex order parameter `Z = (1/N) Σ r_j e^{iφ_j}`; `dφ = ω + KR·sin(ψ−φ)`; amplitude decay `−λr + KR·cos(ψ−φ)`; frequency adaptation scaled `1/N` (mean-field/full) and `1/k` (sparse) — normalization invariants per Plan §5 preserved. Full-mode custom-matrix path uses `safe_phase_diff` and skips zero entries.
- **Stuart–Landau**: `dz/dt = (μ + iω)z − |z|²z + C` with `C = K(Z − z)` mean-field; polar extraction via `dz·e^{−iφ}` with radius floor `1e-8`. Matrix-less `Full` fallback delegates to mean-field — the documented equivalence `K(Z−z_i) ≡ Σ_{j≠i}(K/N)(z_j−z_i)` holds algebraically and is parity-tested.
- **Hopf**: `dr/dt = μr − r³ + C^cos`, `dφ/dt = ω + C^sin/r` (radius-floored), `dω/dt = (γ/N)·C^sin`; `limit_cycle_amplitude = √μ` for `μ > 0`.
- **Integrators** (`integrate.rs`): Euler and RK4 are faithful PRINet 3.0 ports (intermediate stages unwrapped — exact because all phase operations are 2π-periodic; final state wraps/clamps). RK45 DOPRI5 tableau verified coefficient-by-coefficient against the standard Dormand–Prince 5(4) values; error norm `sqrt(mean((err/(atol+rtol·max|y|))²))`; accept/reject with `clamp(0.9·err^(−1/5), 0.2, 5.0)`; FSAL cache invalidated at call entry (WP008-F1 regression-covered), on rejection, and guarded by buffer-size check; `MIN_DT = 1e-14` underflow guard; typed budget errors.
- **PAC** (`pac.rs`): `A_fast = A₀·[1 + m·cos(mean(φ_slow) + offset)]` — direct PRINet port (arithmetic, not circular, phase mean — preserved reference behavior, parity-verified at `1e-6` per amendment #14); modulation depth validated `[0,1]`; clamp range validated finite/ordered (WP009-F4).
- **Topologies** (`coupling.rs`): AllToAll `K/N` zero-diagonal; Ring with even-`k_ring` clamp to `≤ N−1` preserving `K/degree` energy invariant (WP009-F3 regression-tested); directed Watts–Strogatz small-world with deterministic `Seed`, edge-count preservation tested; `validate_coupling_matrix` length/finiteness checks.
- **Seed authority** unchanged since EA-001: `Pcg64` `(counter, key)` streams; only `(counter, key)` serialized, never internal state.

Documentation-accuracy findings only (E-F7, E-F8, E-F9); no mathematical or guard defects found.

### E2: Codebase & Architecture Conformance

- Crate layering verified: `prin-dynamics` depends only on numerics/serde/thiserror/tracing (no intra-workspace upward deps); `prin-kernels`, `_prin_core`, `python/prin` layering unchanged since EA-001.
- Unsafe posture (grep-verified across all crates): `#![forbid(unsafe_code)]` in `prin-dynamics`, `prin-metrics`, `prin-tensor`, `prin-sim`, `prin-train`, `prin-daemon`; `#![deny(unsafe_code)]` + module-scoped `#![allow(unsafe_code)]` only in the two audited FFI modules (`prin-py/src/dlpack.rs`, `prin-kernels/src/mean_field_rk4/cubecl.rs`) per amendments #6 and #8.
- "No numerics in Python": `python/prin/dlpack.py` is a pure capsule bridge ("No numerics live in Python" — module docstring); `_ort.py`/`_phase0.py` are orchestration/gate logic; `parity/` harness computes test comparisons only (WP-002-approved design).

### E3: Test Suite & Parity Corpus

- Isolated full-suite run: **184 passed in 19.07s** (`tests/` + `parity/`, coverage 99% on `prin`); fast suite 172 passed / 6 deselected.
- Rust: **222 default** (167 `prin-dynamics` unit + 16 `parity_integrators` + 9 `parity_models` + 9 `parity_pac` + 13 `prin-kernels` + 6 `_prin_core` + 2 doctests) and **225 with `--features strict-checks`** — all green, matching PSR-009 claims.
- Golden corpus: 504 cases; manifest SHA-256 digests re-validated at load by the differential suite (6 representative cases re-generated bit-identically against archived PRINet 3.0 during this audit).
- **E-F1 (D2)** found: `test_phase0_gate_integration_with_ort` invokes `phase0_gate_report(refresh_ort=True)` against the live repository root; `_check_ort(..., refresh=True)` overwrites `EVIDENCE/0017-wp005-s1-ort-probe.json`. Reproduced live during this audit (timestamp re-written to `2026-08-08T06:23:07Z`). This violates the EVIDENCE immutability rule and is the unaddressed root cause of the "timestamp drift" treated symptomatically in WP007-F4. It also executes in CI (`python.yml` installs the `onnx` extra on every matrix cell), silently dirtying the checkout. Fixed in Task 5 by redirecting the refresh write to `tmp_path` via the existing `evidence_path` parameter and restoring the committed evidence file.
- **E-F13 (D4)** observation: running two pytest invocations back-to-back, or pytest concurrently with cargo, produced 6 fixture-setup `PermissionError [WinError 32]` errors during `tmp_path` cleanup on Windows; the identical suite passes 184/184 when run in isolation. Same family as EA-001 E-F1; documented as operational guidance rather than a code defect.

### E4: Security & Supply Chain

- `cargo audit`: 0 vulnerabilities; 1 allowed warning (`paste` RUSTSEC-2024-0436 via `cubecl` 0.10.0, amendment #9, re-checked).
- `pip-audit`: 0 findings for the project and for `DOCS/sphinx/requirements.txt`.
- Bandit (`-c pyproject.toml`): 0 issues; ruff security rules clean; no secrets detected (gitleaks enforced in CI per amendment #5).
- **Snyk Code** (CLI `snyk code test --severity-threshold=low`, authenticated org `symbo-gif`): 9 low path-traversal findings —
  - 6 in `DOCS/archive and reference from PRINet 3.0/...` (archived reference tree, never imported/built). Root cause: `.snyk` excludes `DOCS/archive/**`, which does not match the actual directory name (E-F3). Pattern corrected in Task 5.
  - 3 in `tools/wp001_baseline.py` (lines 339, 402, 759): operator-supplied CLI root argument flowing into path operations. The tool already validates the root (`_validate_root_path`); as a local, operator-invoked audit CLI the input is trusted by design. Accepted via `.snyk` policy exception with justification and expiry (E-F4), consistent with the amendment-#4 exception pattern.
  - CI gate unaffected: `snyk.yml` enforces the medium threshold (these are low).
- **Snyk SCA**: the MCP-based `snyk_sca_scan` used by prior sessions is not configured in this session; CLI equivalents failed (`SNYK-CLI-0000` with `--command`, `SNYK-OS-0001` for `pyproject.toml`, `SNYK-OS-PYTHON-0013` for a freeze file). SCA coverage for this audit therefore rests on fresh `pip-audit` + `cargo audit` runs (both clean) plus the `python.yml` security job, which executes the project's Snyk SCA recipe (`uv pip compile` → `snyk test --file … --fail-on=all`, low threshold) on the push performed in Task 7 (E-F5).
- **Dependabot posture (default branch)**: the Task 7 push surfaced 6 open GitHub Dependabot alerts — three pyo3 GHSAs (`GHSA-chgr-c6px-7xpp`, `GHSA-36hh-v3qg-5jq4`, patched in 0.29.0; `GHSA-pph8-gcv7-4qj5`, patched in 0.24.1) each reported against `Cargo.lock` and `crates/prin-py/Cargo.toml`. These are **not** findings against the audited branch, which pins `pyo3 0.29.0` (the WP-001-F1 remediation; `cargo audit` clean): Dependabot scans the default branch `main`, which still carries `pyo3 0.22` because no work package since WP-001 has been merged. The alerts will auto-close when this branch merges. Recorded as a pass-forward risk (see §4.2) rather than a deviation.

### E5: Standards & Documentation Adherence

- `interrogate`: 100.0% public coverage (104/104); `mypy --strict`: 16 files clean; ruff check/format clean (44 files).
- `crates/prin-dynamics/README.md` is current through WP-009 (models, integrators, PAC, topologies, parity tolerances, feature flags).
- Findings: `DOCS/experiments/README.md` index omits the WP-006/WP-007 handoff notes present in the directory and does not document the WP-009 handoff-note placement in `DOCS/sessions/phase-1/` (E-F10); `DOCS/audits/README.md` index omits the WP-009 audit and EA-001 report (E-F11); `prin-dynamics` lib.rs overstates capability ("delayed" coupling; "Philox/PCG64") (E-F7); `integrate.rs` typo "periodal" (E-F8); `coupling.rs` SmallWorld doc overstates rewiring coverage (E-F9); both executive-audit workflow recipes are hard-coded to "001" artifacts (E-F12).

### E6: Evidence, Baselines & Analytics Integrity

- Model hash check: `models/subconscious_controller.onnx` SHA-256 `3396BFDD…4102` matches `EVIDENCE/0017-wp005-s1-ort-probe.json → model_sha256`.
- `tools/wp001_baseline.py check`: PASS (metadata, session-plan, ownership, traceability validators all green — this also proves register structural integrity, incl. gap-free 0001–0198).
- Corpus integrity: manifest digests validated at load; differential regeneration bit-identical (Task 6 run).
- Drift detected and remediated: `EVIDENCE/0017-wp005-s1-ort-probe.json` working-tree mutation (root cause E-F1); committed baseline restored in Task 5.

### E7: Session Cycle & Governance Traceability

- Cycles 007, 008, 009 each executed S1→S4 in order with S2 audit reports, S3 closure tables, S4 Project State Reports; cumulative deviation ledger (PSR-009 §3) shows all findings `FIXED`/`AMENDED`, none carried.
- **E-F2 (D2)**: EA-001's report (§2 E7, §4.1 item 4) and the CHANGELOG `[Unreleased] → Changed` section claim that `SESSION_REGISTER.md`/`TRACEABILITY.md` were updated to register EA-001 as Global Session 0025 and re-map WP-007 S1 to 0026. Commit `d1e6e0a` contains **no** changes to any `DOCS/sessions/` file, and the register numbers WP-007 S1 as 0025 (validator-green, authoritative). Subsequent cycles correctly used the planned numbering, so the claim was never operative — but a signed audit report and the CHANGELOG asserted an artefact change that did not happen, violating Development Workflow and Audit Standards §1.4 (evidence-based audits).
  - Remediation (Task 5): EA sessions are registered in a dedicated "Global sessions — Executive Audits" register section **outside** the planned 0001–0198 sequence (inserting into it would violate TRACEABILITY invariant 4), EA-001's report receives a tagged correction note, the CHANGELOG entry is corrected with the same tag, and plan amendment #15 records the convention and the retroactive correction. EA-001's secondary inaccuracy (E8: "benchmark scripts in `benchmarks/` functional" — the directory holds only the Phase 6 plan README) is corrected by the same note.

### E8: Performance, Benchmarking & Reproducibility

- `pytest-benchmark` DLPack latencies reproduced this session: round-trip median 4.3 µs (f32) / 5.2 µs (f64); batched median 26.4 µs (f32) / 29.2 µs (f64) — consistent with EA-001-era results; no regression gate trip (none defined yet; gates arrive with WP-033).
- RK4 order-`h⁴` convergence and RK45 tolerance-property tests green; kernel-equivalence (CubeCL CPU vs reference) green under `--features cpu`.
- `benchmarks/` category packages remain Phase 6 (WP-033) scope per their README; EA-001's E8 wording corrected (see E-F2).

### E9: CI/CD & Build Infrastructure

- Seven workflows verified present and reviewed: `python.yml` (3-OS × 3-Python matrix, onnx extra on all cells, pip-audit + Snyk SCA security job), `rust.yml` (fmt, clippy default+strict, tests default+strict, `prin-kernels --features cpu`, cargo audit, rustdoc), `snyk.yml` (Snyk Code medium + gitleaks full history), `parity.yml` (differential suite vs archived PRINet 3.0), `repro.yml`, `release.yml` (3-OS abi3 wheel matrix + smoke), `gpu.yml` (opt-in).
- Feature-flag coverage in CI confirmed for `strict-checks` (clippy-strict + test-strict jobs) per WP006-F2 fix.

### E10: Roadmap, Risks & Future Session Handoff

- Phase 1: 4 of 6 WPs complete (WP-006..WP-009 closed); WP-010 "Phase metrics and chimera measures" declared in PSR-009 §6; brief `0037-wp010-s1-…md` is READY with entry conditions and maintainer approval pending (E-F6).
- Plan amendment #14 (f32-complex preserved numerical hazard) has governed parity tolerances since WP-007 S3 with "maintainer approval pending" — approval recorded during EA-002 (E-F6).
- Pass-forward placeholders WP-011..WP-039 verified present in the session register (sessions 0041–0198) and unchanged.
- Risks carried: `paste` advisory (amendment #9), f32-complex hazard (amendment #14), Windows pytest temp-dir flakiness (E-F13 guidance added), GitHub native secret scanning still unavailable (amendment #5 substitute in force), Snyk MCP availability in local agent sessions (E-F5).

---

## 3. Discovered Deviations and Findings Table

| ID | Severity | Category | Location / Subsystem | Issue Description | Violated Clause | Proposed Remediation |
|---|---|---|---|---|---|---|
| **E-F1** | D2 | Testing / Evidence | `tests/test_phase0_gate.py::test_phase0_gate_integration_with_ort` | Test calls `phase0_gate_report(refresh_ort=True)` against the live repo root; every full pytest run overwrites committed `EVIDENCE/0017-wp005-s1-ort-probe.json` (reproduced live during EA-002). Root cause of WP007-F4's "timestamp drift" was never fixed. | EVIDENCE/README.md immutability rule; Testing Standards (test isolation) | Redirect refresh write to `tmp_path` via the existing `evidence_path` parameter; restore committed evidence file; regression-assert no repo mutation. |
| **E-F2** | D2 | Governance / Traceability | `EXECUTIVE_AUDIT_REPORT_001.md` §2/§4.1; `CHANGELOG.md` `[Unreleased]` | EA-001 claims session-register/traceability updates (EA-001 as Session 0025; WP-007 → 0026) that commit `d1e6e0a` never made; register shows no EA entry. Secondary: EA-001 E8 overstates `benchmarks/` scripts (Phase 6 scope). | Development Workflow Standards §1.4 (evidence-based audits) | Register EA-001/EA-002 in a dedicated global-sessions section outside the planned 0001–0198 sequence; tagged correction notes on EA-001 report + CHANGELOG; plan amendment #15. |
| **E-F3** | D3 | Security tooling | `.snyk` | Exclude pattern `DOCS/archive/**` does not match the actual archive directory `DOCS/archive and reference from PRINet 3.0/`; archived code remains scanned (6 low findings). | Coding Standards §6 (security controls effective) | Correct the exclude path to the real directory; re-run Snyk Code to confirm archive findings disappear. |
| **E-F4** | D3 | Security / Supply chain | `tools/wp001_baseline.py` (Snyk Code low: 3 path-traversal findings) | Operator-supplied CLI root flows into path operations; tool already validates root and is a trusted local CLI, but findings remain open at low threshold. | Coding Standards §6.2 (findings resolved or formally accepted) | Acceptance recorded in `.snyk` (reason + 2026-11-06 expiry + per-cycle recheck, amendment-#4 pattern) with maintainer approval in EA-002. Note: the local CLI does not apply `.snyk` ignores to SAST findings (platform-side mechanism); the enforced gate is the medium threshold used by `snyk.yml` and EA-001, which is clean (0 issues). |
| **E-F5** | D3 | Security tooling / Environment | Snyk SCA in local agent sessions | Snyk MCP `snyk_sca_scan` unavailable this session; CLI pip paths fail (SNYK-CLI-0000 / SNYK-OS-0001 / SNYK-OS-PYTHON-0013). | Executive Audit Governance E4 | Compensated by fresh pip-audit + cargo audit (clean) and the `python.yml` Snyk SCA CI job on push; restore Snyk MCP configuration for future local sessions (pass-forward, environment). |
| **E-F6** | D3 | Governance | Plan amendment log #14; PSR-009; WP-010 declaration | Amendment #14 (in force since WP-007 S3), PSR-009, and the WP-010 declaration all remain "maintainer approval pending" while cycles 008–009 proceeded. | Development Workflow Standards §6 (approvals recorded in artefacts) | Maintainer approval solicited and recorded during EA-002 (amendment #14, PSR-009 verdict, WP-010 declaration). |
| **E-F7** | D4 | Documentation | `crates/prin-dynamics/src/lib.rs` | Crate doc lists "delayed, directed/weighted coupling topologies" (no delayed coupling exists) and "(Philox/PCG64)" though only `Pcg64` is implemented. | Documentation Standards (accuracy) | Align crate rustdoc with implemented capability. |
| **E-F8** | D4 | Documentation | `crates/prin-dynamics/src/integrate.rs` | Typo "`2π`-periodal" in RK4Integrator rustdoc. | Documentation Standards | Correct to "periodic". |
| **E-F9** | D4 | Documentation | `crates/prin-dynamics/src/coupling.rs` | `SmallWorld` docs claim "each outgoing edge" is rewired; implementation rewires only forward (right-neighbour) outgoing edges — a valid directed WS variant, but the docs overstate coverage. | Documentation Standards (accuracy) | Clarify rustdoc (forward edges only; left-neighbour edges retained). |
| **E-F10** | D4 | Documentation | `DOCS/experiments/README.md` | Index omits `0021-wp006-s1-handoff.md` and `0025-wp007-s1-handoff.md` (present in directory); WP-009 handoff-note placement in `DOCS/sessions/phase-1/` undocumented. | Documentation Standards §3 (directory README completeness) | Update index; document placement convention incl. the WP-009 exception. |
| **E-F11** | D4 | Documentation | `DOCS/audits/README.md` | "Current reports" omits `009-wp009-audit.md` and `EXECUTIVE_AUDIT_REPORT_001.md`. | Documentation Standards §3 | Update index (add WP-009 audit, EA-001, EA-002). |
| **E-F12** | D4 | Process / Docs | `workflows/executive-audit.md`, `.windsurf/workflows/executive-audit.md` | Recipes hard-code `EXECUTIVE_AUDIT_REPORT_001.md` and the "Executive Audit 001" retroactive tag. | Executive Audit Governance §5 | Parameterize to `NNN` for reuse by future executive audits. |
| **E-F13** | D4 | Testing / Environment | Windows pytest temp handling | Back-to-back or cargo-concurrent pytest runs produce `WinError 32` fixture-setup errors during `tmp_path` cleanup; isolated runs are clean (184/184). Lineage of EA-001 E-F1. | Testing Standards §5 (Windows workaround) | Operational guidance added to `AGENTS.md` (run suites sequentially, re-run clean on lock errors); no code change. |

---

## 4. Remediation Plan

### 4.1 Immediate Remediation (Executed in Task 5)

1. **E-F1:** `test_phase0_gate_integration_with_ort` now writes refreshed ORT evidence to `tmp_path` (via `evidence_path`), keeping the real model/repo read-only; committed `EVIDENCE/0017-wp005-s1-ort-probe.json` restored from `HEAD`.
2. **E-F2:** `SESSION_REGISTER.md` gains a "Global sessions — Executive Audits" section registering EA-001 and EA-002 (tagged `[RETROACTIVE UPDATE - Executive Audit 002]` for EA-001); EA-001 report and CHANGELOG receive tagged correction notes; plan amendment #15 records the convention (EA sessions live outside the planned 0001–0198 sequence; planned numbering untouched).
3. **E-F3:** `.snyk` exclude corrected to `DOCS/archive and reference from PRINet 3.0/**`; Snyk Code re-run confirms archive findings no longer reported.
4. **E-F4:** `.snyk` policy records the acceptance of the three `tools/wp001_baseline.py` findings (justification, maintainer approval, 2026-11-06 expiry, per-cycle recheck). The local CLI does not honor `.snyk` ignores for SAST findings, so the enforced gate remains the medium threshold (`snyk.yml` parity): `snyk code test --severity-threshold=medium` → 0 issues.
5. **E-F6:** Maintainer approval for plan amendment #14, PSR-009 (cycle 009 verdict), and the WP-010 declaration recorded in the respective artefacts.
6. **E-F7 / E-F8 / E-F9:** rustdoc corrections in `lib.rs`, `integrate.rs`, `coupling.rs` (doc-only edits).
7. **E-F10 / E-F11:** README index updates in `DOCS/experiments/` and `DOCS/audits/`.
8. **E-F12:** Both executive-audit workflow recipes parameterized to `NNN`.
9. **E-F13:** Windows concurrency guidance added to `AGENTS.md`, and the two chained pytest invocations in the local verification one-liner now use distinct basetemp directories (`.pytest_basetemp` / `.pytest_basetemp-full`) so the second run never races the first run's `tmp_path` cleanup.

### 4.2 Pass-Forward Items (Scheduled for Future WPs/Sessions)

- **E-F5 (environment):** Restore the Snyk MCP server configuration for local agent sessions so `snyk_sca_scan` is available outside CI. Owner: next session with MCP configuration access; interim gate = pip-audit + cargo audit + `python.yml` Snyk SCA job.
- **Dependabot alerts on `main` (security posture):** 6 open pyo3 alerts exist because the default branch predates the WP-001-F1 pyo3 0.29.0 upgrade; the audited branch is not affected. Resolution path: merge the phase work into `main` per the project's phase cadence (alerts auto-close), or maintainer-directed dismissal with reason. Owner: maintainer, at the next merge decision.
- **WP-010 (Sessions 0037–0040):** Phase metrics and chimera measures (`prin-metrics`). Brief READY; approval recorded in EA-002.
- **WP-011 (Sessions 0041–0044):** Phase 1 Python API and dynamics integration — also owns the currently-stub Python sub-packages (`prin.datasets`, `prin.eval`, `prin.nn`, `prin.experiments`, `prin.reporting`).
- **WP-012..WP-016 (Phase 2):** exponential/multi-rate integrators (`integrate.rs` stub scope), continuous band networks (`bands.rs`), temporal propagation (`temporal.rs`), sweeps + Phase 2 gate.
- **WP-017..WP-021 (Phase 3):** production kernel architecture incl. the `benchmarks/kernels/` category and benchmark regression gates.
- **WP-022..WP-027 (Phase 4):** trainable stack and Torch autograd bridge.
- **WP-028..WP-032 (Phase 5):** daemon runtime, controller providers, experiment tooling.
- **WP-033..WP-038 (Phase 6):** unified `benchrunner` CLI and `benchmarks/` category packages, reporting, reproduction pipeline, RC1.
- **WP-039 + Campaign (Phase 7):** experimentation campaign per pre-registration standards.

---

## 5. Verification Suite Results (Task 6)

| Verification Step | Command / Workflow | Result | Notes / Evidence |
|---|---|---|---|
| Python Linting | `.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/` | PASS | All checks passed |
| Python Formatting | `.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/` | PASS | 44 files already formatted |
| Python Static Typing | `.venv\Scripts\mypy python/prin --strict` | PASS | 16 source files clean |
| Python Docstrings | `.venv\Scripts\python -m interrogate -c pyproject.toml python/prin` | PASS | 100.0% public (104/104) |
| Python Security | `.venv\Scripts\python -m bandit -r . -c pyproject.toml` | PASS | 0 issues |
| Fast Python Tests | `pytest tests/ -m "not slow and not gpu" --cov=prin --basetemp=.pytest_basetemp` | PASS | 172 passed, 6 deselected; coverage 99% |
| Full Parity Suite | `pytest tests/ parity/ --cov=prin --basetemp=.pytest_basetemp-full` | PASS | 184 passed in 15.67s (isolated run); one back-to-back run reproduced the E-F13 `WinError 32` fixture lock on a stale temp dir from the preceding run — no test failures; EVIDENCE artefacts verified unmodified after every run (E-F1 fix) |
| Baseline Tool Check | `.venv\Scripts\python tools/wp001_baseline.py check` | PASS | Baseline contract validated |
| Evidence Integrity | `Get-FileHash models/subconscious_controller.onnx` vs evidence record | PASS | SHA-256 `3396BFDD…4102` matches; drifted evidence file restored |
| Rust Formatting | `cargo fmt --all -- --check` | PASS | Clean |
| Rust Clippy (Default) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS | 0 warnings |
| Rust Clippy (Strict) | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS | 0 warnings |
| Rust Tests (Default) | `cargo test --workspace` | PASS | 222 tests (167 unit + 34 parity/integration + 6 core + 13 kernels + 2 doctests) |
| Rust Tests (Strict) | `cargo test --workspace --features strict-checks` | PASS | 225 tests |
| Rust Coverage (prin-dynamics) | `cargo llvm-cov -p prin-dynamics --features strict-checks --summary-only` | PASS | Lines: coupling.rs 99.40%, pac.rs 100.00%, seed.rs 99.50%, models.rs 98.24%, state.rs 97.63%, integrate.rs 97.48% — all ≥95% |
| Rust Coverage (prin-kernels) | `cargo llvm-cov -p prin-kernels --features wgpu,cpu --summary-only` | PASS | 88.21% lines overall; mean_field_rk4.rs 99.67%, ops.rs 100%; cubecl.rs 80.42% under the amendment-#10 non-instrumentable kernel-stub caveat; 21 tests incl. wgpu N=1M kernel-equivalence pass on this host |
| Rustdoc Check | `cargo doc --workspace --no-deps` (`RUSTDOCFLAGS='-D warnings'`) | PASS | 0 warnings post-remediation |
| Cargo Security Audit | `cargo audit` | PASS | 0 vulnerabilities; 1 allowed advisory (amendment #9) |
| Pip Security Audit | `pip_audit .` | PASS | No known vulnerabilities |
| Pip Security Audit (docs) | `pip_audit -r DOCS/sphinx/requirements.txt` | PASS | No known vulnerabilities |
| Snyk Code | `snyk code test --severity-threshold=medium` (enforced gate, `snyk.yml` parity) | PASS | 0 issues post-remediation; low-threshold advisory run cleared 6 archive findings via corrected `.snyk` exclude (E-F3); 3 accepted low findings recorded (E-F4) |
| Snyk Open Source | `python.yml` CI job (`uv pip compile` → `snyk test --fail-on=all`) | PASS (CI on push) | Local MCP unavailable (E-F5); local gate = pip-audit + cargo audit |
| Sphinx HTML Build | `python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html` | PASS | Build succeeded, 0 warnings |

### 5.1 Detailed results

Post-remediation verification (Task 6, sequential execution per E-F13 guidance):

- **Python static gates:** ruff check clean; ruff format 44 files clean; mypy --strict 16 files clean; interrogate 100.0% (104/104); bandit 0 issues. All re-run after the `tests/test_phase0_gate.py` remediation edit.
- **Python suites:** fast suite 172 passed / 6 deselected; full suite 184 passed in 15.67s on the isolated post-remediation run. `EVIDENCE/0017-wp005-s1-ort-probe.json` verified byte-identical to `HEAD` after every full-suite run (regression proof for E-F1).
- **Rust gates:** `cargo fmt --check` clean; clippy default + strict clean; `cargo test --workspace` 222 passed; `cargo test --workspace --features strict-checks` 225 passed; `cargo doc -D warnings` clean. All re-run after the E-F7/E-F8/E-F9 rustdoc edits.
- **Security:** Snyk Code medium threshold 0 issues (enforced gate); `.snyk` archive exclude verified effective (6 archive findings cleared at low threshold); cargo audit / pip-audit ×2 clean; baseline validator green against the amended session register.
- **Docs:** Sphinx HTML build succeeded with `-W --keep-going`, 0 warnings, changelog page rebuilt consistently.

---

## 6. Audit Verdict and Sign-off

**Final Verdict:** **PASS-WITH-REMEDIATION**
No D1 findings. Two D2 findings (E-F1 evidence-artifact mutation by tests; E-F2 EA-001 unexecuted session-register claim) and four D3 findings were remediated in Task 5 or formally passed forward with owners; seven D4 findings fixed in Task 5. All verification gates in §5 pass after remediation.

**Auditor Signature:** Qwen Code (AI Pair & Systems Auditor)
**Date:** 2026-08-08
