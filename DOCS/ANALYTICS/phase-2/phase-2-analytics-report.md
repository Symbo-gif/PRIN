---

# PRIN Phase 2 Analytics Report

**Phase:** 2 — Advanced numerics and simulation
**Date:** 2026-08-15
**Analyst:** Claude Code (AI pair)
**Maintainer approval:** pending
**Methodology:** [`DOCS/ANALYTICS/ANALYTICS_METHODOLOGY.md`](../ANALYTICS_METHODOLOGY.md)
**Git state:** `main` @ `4d0f75b` (post-EMA-001-remediation; current `HEAD`)
**Phase 2 work-package commit range:** `d02e478` (WP-012 S1) → `dac017e` (WP-016 S3 baseline) → `fbe1c92` (`v0.3.0-alpha.1` Phase 2 exit release) — 52 commits
**Global-session layer (conducted immediately after the Phase 2 exit gate, folded into this assessment):** `fbe1c92` → `6777ef1` → `c228264` → `f1204ed` (EA-003 complete) → `630c5d6` (EMA-001 audit) → `4d0f75b` (EMA-001 remediation, current `HEAD`)
**Work packages:** WP-012 through WP-016 (5 cycles, 20 sessions) + Executive Audit Session 003 (EA-003) + Executive Mathematical Audit Session 001 (EMA-001 + EMA-001R remediation)
**Phase exit gate:** GREEN (`DOCS/reports/016-project-state.md` §5)

---

## Executive summary

Phase 2 — Advanced numerics and simulation is **complete**. All five work
packages (WP-012 through WP-016) passed through the full Session Cycle
(S1→S2→S3→S4) in exact order across 20 sessions (0045–0064), with a clean
S4 hand-off to Phase 3 (WP-017, session 0065). The phase delivered
exponential and multi-rate integrators, continuous hierarchical band
networks with temporal propagation, Tucker/HOSVD and CP-ALS tensor
decompositions, a sparse `OscilloSim` simulation engine (CSR coupling,
pruning, chimera detection), and rayon-parallel parameter sweeps with a
size-gated CPU dispatcher — three new crates (`prin-tensor`, `prin-sim`,
plus continued `prin-dynamics` growth) and roughly 25,000 new lines of Rust.

Unlike Phase 1, where 0 of 22 findings were D1, **every one of Phase 2's
five work packages received a `FAIL` verdict at S2 with at least one D1
finding** (7 D1 findings across 31 WP-level findings: 7 D1, 9 D2, 10 D3,
5 D4). Missing PRINet 3.0 parity evidence was the dominant D1 pattern
(WP-012, WP-013, WP-014 all shipped S1 commits with no differential parity
test for their headline deliverable — the identical class of gap in three
consecutive cycles), joined by a silent-wrong-value defect (`matrix_exp`
falling back to the identity matrix on a singular Padé denominator,
WP012-F3), a reachable panic on contract-valid input (`hosvd`, WP014-F3),
and a red `strict-checks` CI gate the S1 handoff had not run (WP015-F1). All
31 findings were fixed (or fixed-plus-amended) in S3, and every delta
re-audit is genuinely CLEAN — independently confirmed in this session by
re-running the full local gate suite, not merely re-reading the audit
reports' own closure claims.

Two **Executive-tier sessions** closed immediately after the Phase 2 exit
gate and are folded into this assessment because their audit windows cover
the entire Phase 2 delta:

- **EA-003** (2026-08-14): a full-project executive audit across E1–E10,
  verdict `PASS-WITH-REMEDIATION`, 14 findings (E-F1–E-F14: 2 D1, 5 D2,
  3 D3, 4 D4). Its headline finding, **E-F1 (D1)**, is a silently
  corrupted cumulative deviation ledger — fabricated commit hashes and one
  invented finding, introduced at WP-014 S4 and undetected through two
  further S2 audits (WP-015, WP-016) — restored from the last verified
  table. **E-F2 (D1)** found that a PSR ledger entry overstated what CI had
  actually verified; both were independently re-verified live against
  git objects and the GitHub Actions API and fully remediated in-session.
- **EMA-001** (2026-08-14) + **EMA-001R remediation** (2026-08-14): the
  first Executive Mathematical Audit — 23 mathematical claims independently
  **recomputed** (not read) with SymPy, SciPy, Z3, NetworkX, and (in the
  remediation) Lean 4, via the external `math-audit-mcp` tool. Original
  verdict `FAIL` on one Z3-confirmed **D1** finding, **M-F1**: a phase-wrap
  defect in `prin-metrics::chimera::strength_of_incoherence`
  (`chimera.rs:169–171`) that inverted the coherence/incoherence magnitude
  relationship for any field with local structure — live in the codebase
  since **WP-010 (Phase 1)**, undetected by three subsequent S2 audits, the
  Phase 1 analytics session, EA-001, EA-002, and EA-003's own direct-source
  E1 review. The remediation session fixed and Z3-reverified M-F1, resolved
  a Z3 timeout (M-F2, D3), and closed a policy-design interaction (M-F3,
  D2) with new Lean 4 formal proofs plus recorded Wolfram Engine
  corroboration; final verdict **PASS-WITH-REMEDIATION**.

Independent re-verification during **this** analytics session (2026-08-15,
`HEAD` `4d0f75b`) confirms every mandatory quality, coverage, security, and
documentation gate is green, **with one exception discovered fresh in this
session**:

| Gate | Result | Evidence |
|---|---|---|
| `ruff check python/ tests/ benchmarks/ tools/ parity/` | **3 errors** — `tools/math_audit_run.py` (I001 unsorted imports, 2× E501) | §5.4, **new finding PA2-F1** |
| `ruff format --check` | **1 file** (`tools/math_audit_run.py`) would be reformatted | §5.4, PA2-F1 |
| `mypy python/prin --strict` | Success: no issues found in 18 source files | §5.4 |
| `interrogate` | 100.0% (106/106 public), minimum 95% | §5.4 |
| `bandit -r . -c pyproject.toml` | 0 issues | §5.4 |
| `pytest tests/ -m "not slow and not gpu" --cov=prin` | 306 passed, 6 deselected, 99% coverage (677 stmts, 10 missed) | §5.4 |
| `pytest parity/ -m parity` | **510 passed** (504-case exhaustive corpus + planted-deviation harness test) | §5.4 |
| `cargo fmt --all -- --check` | Clean | §5.4 |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean | §5.4 |
| `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | Clean | §5.4 |
| `cargo test --workspace` | **731 passed**, 0 failed | §5.4 |
| `cargo test --workspace --features strict-checks` | **734 passed**, 0 failed | §5.4 |
| `cargo audit` | 1 allowed inherited `paste` RUSTSEC-2024-0436 (amendment #9) | §5.4 |
| `pip-audit .` / `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities (both) | §5.4 |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | Build succeeded, 0 warnings | §5.4 |
| `sphinx-build -W --keep-going -b html` | Build succeeded, 0 warnings | §5.4 |
| `tools/wp001_baseline.py check` | WP-001 baseline validation passed (version consistency holds — E-F3 fix confirmed stable) | §5.4 |
| Snyk Code / Snyk Open Source | **Not re-run this session** (MCP tool unavailable); last verified 2026-08-14 by EA-003 (0/0 issues at gate threshold, 6 torch advisories accepted in `.snyk` through 2026-11-14) | §5.4, limitation |

This session also independently discovered **two new findings** not present
in any prior audit or the deviation ledger, per Analytics Methodology
principle 7 ("no silent overrides"):

- **PA2-F1 (D2):** `tools/math_audit_run.py`, added by the EMA-001 session
  (commit `630c5d6`), fails the mandatory `ruff check` / `ruff format
  --check` gate (`AGENTS.md` verification one-liner explicitly scopes
  `tools/`). EMA-001's own verification (§6/§8 of its report) never ran a
  Python lint pass on the tooling it introduced. Open, unresolved as of
  this report.
- **PA2-F2 (D3):** `CHANGELOG.md`'s `[Unreleased]` section documents EA-003
  in full (lines 12–50) but contains **zero mention** of EMA-001 or its
  remediation, despite EMA-001 fixing a real D1 mathematical defect
  (M-F1) and introducing three new plan amendments (#23–#25). Open,
  unresolved as of this report.

Both are recorded in §5.4 and the Recommendations Register and trigger the
normal Session Cycle remediation process per Analytics Methodology §7; this
analytics session does not fix them.

### Aggregate phase verdict

**PASS — SATISFACTORY**

All nine dimensions score ≥ 3; no dimension scores below 3; not every
dimension reaches ≥ 4 (P2 Documentation scores 3), so the phase does not
meet the `PASS — EXCELLENT` bar Phase 0 and Phase 1 both achieved. This is
a genuine, evidence-driven downgrade, not a rounding artifact: Phase 2's
S1→S2 trajectory was materially rockier than Phase 1's (7 D1 findings
across 5 WPs vs. 0 D1 across 6 WPs in Phase 1), and this analytics session
itself surfaced two previously unrecorded gate/documentation gaps that the
strengthened S4 sweep (Phase 1 recommendation R7) did not catch because
they fall outside a WP-N cycle's own scope. The compensating strength —
and the reason the phase still clears the bar — is that every single D1
finding, from all three verification layers (S2 WP audits, EA-003,
EMA-001), was caught, genuinely fixed, and independently re-verified, not
glossed over or downgraded to close the ledger.

### Dimension scores

| Dimension | Score | Label | One-line justification |
|---|---|---|---|
| P1 Data and parity artefacts | 4 | Strong | 504-case corpus now exhaustively CI-verified (R8 delivered: 510/510, up from 6 representative in Phase 1); 79+ new Rust-native parity tests post-remediation; genuine HOSVD-vs-PRINet differential parity added by EA-003 (E-F5) closing an invariant-only gap; but missing-parity was the D1 root cause in 3 of 5 WPs at S1 |
| P2 Documentation | 3 | Adequate | R7's S4 documentation-accuracy-sweep checklist item is in force and cited in every WP-014..016 closure table; but this session independently found EMA-001 entirely absent from `CHANGELOG.md` (PA2-F2) and WP-014's S1 handoff contained a refuted factual claim ("no reference code was found") that passed S1 review unchallenged |
| P3 Testing | 5 | Exemplary | 731/731 default + 734/734 strict-checks Rust tests, 306 Python fast + 510 exhaustive parity, all independently re-verified green this session; new proptest suites (`proptest_sweep.rs`, `proptest_properties.rs`); ≥95% coverage on every touched file post-remediation; R8 (exhaustive corpus CI) and R12 (strict-checks coverage merge) both delivered before Phase 2 S1 |
| P4 Coding and architecture | 4 | Strong | Crate layering (`dynamics → {metrics, tensor, sim}`) held exactly; zero new `unsafe`; `dispatch.rs` size-gated CPU dispatcher is a clean architectural addition; but S1 delivered a silent-wrong-value bug (`matrix_exp` identity fallback), a reachable panic on documented-valid input (`hosvd`), and a 6×-slower-than-serial regression (WP016-F1) in three separate cycles |
| P5 Evidence and verification | 4 | Strong | Every gate independently re-executed this session and green except one fresh finding (PA2-F1); EMA-001's tool-executed recomputation is a materially stronger evidentiary channel that caught a defect (M-F1) three prior audit layers missed; Snyk MCP unavailable this session, documented as a limitation, last-verified clean by EA-003 one day prior |
| P6 Governance and process | 4 | Strong | 20/20 sessions in exact S1→S4 order; EA-003 and EMA-001 add two genuinely independent verification layers that each caught and fixed a real D1 (E-F1 ledger corruption, M-F1 math defect); but E-F1's undetected propagation through two S2 audits, the 7-D1 WP trajectory, and this session's own two fresh findings show the self-verification net still has gaps |
| P7 Security | 4 | Strong | `cargo audit`/`pip-audit`/`bandit` clean modulo governed advisories; 6 `torch` advisories investigated for a genuine fix (none exists), confirmed unreachable in PRIN's live code, and formally accepted in `.snyk` with a 2026-11-14 recheck; zero new `unsafe` across 5 WPs |
| P8 Phase exit criteria | 4 | Strong | Exit gate GREEN; all 4 Plan §6 criteria met, including the honestly re-scoped performance targets (amendment #21) after S1 benchmark evidence showed the original targets were a memory-bandwidth/SMT ceiling — EA-003's E8 independently confirmed the benchmark methodology was genuine, not fabricated |
| P9 Risk and deferred validation | 4 | Strong | Deferred Validation Register (Phase 1 R9) is live and used; Phase 1 recommendations R7/R8/R9/R12 were all implemented in the inter-phase session before WP-012 S1; new Phase 2 deferrals (amendment #20 carried scope, M-F3's `REQUIRES_HUMAN_REVIEW` claims) are explicitly gated with owners and re-audit points |

---

## 1. Phase 2 scope and deliverables

### 1.1 Planned scope (Project Plan §6, Phase 2)

> Advanced numerics and simulation: exponential and multi-rate integrators;
> continuous hierarchical band networks and temporal propagation; Tucker/HOSVD
> and CP-ALS tensor decompositions; a sparse `OscilloSim` simulation engine
> (CSR coupling, pruning, chimera detection); parallel parameter sweeps and
> CPU-path optimization; the Phase 2 exit gate.

**Exit criteria (Project Plan §6, PSR-016 §5):** `OscilloSim` parity at
`N ≤ 1M` on CPU; sweep speedup on multi-core CPU (amended by #21 to
hardware-scoped targets); all five WPs complete; all quality/security/parity
gates green.

### 1.2 Work package decomposition

| WP | Title | Sessions | S2 verdict | Findings | Key deliverables |
|---|---|---|---|---|---|
| WP-012 | Exponential and multi-rate integrators | 0045–0048 | **FAIL** → CLEAN | 5 (3 D1, 1 D3, 1 D4) | `ExponentialIntegrator` (Padé(13)/Krylov), `MultiRateIntegrator`; 7 new parity tests; amendment #18 |
| WP-013 | Continuous band networks and temporal propagation | 0049–0052 | **FAIL** → CLEAN | 6 (1 D1, 1 D2, 1 D3, 3 D4) | `BandNetwork`, `ComplexPhasorBlender`, `EmaAmplitudeBlender`; 18 new parity tests; amendment #19 |
| WP-014 | Tensor decompositions | 0053–0056 | **FAIL** → CLEAN | 7 (1 D1, 3 D2, 2 D3, 1 D4) | `prin-tensor` crate: `hosvd`/`PolyadicTensor`, `cp_als`/`CPDecomposition`; 9 parity tests (+1 more from EA-003 E-F5) |
| WP-015 | OscilloSim sparse simulation engine | 0057–0060 | **FAIL** → CLEAN | 6 (1 D1, 2 D2, 3 D3) | `prin-sim` crate: `SparseCoupling` (CSR), `OscilloSim`, pruning, chimera; 21 parity + 4 property tests |
| WP-016 | Parallel sweeps, CPU optimization, and Phase 2 gate | 0061–0064 | **FAIL** → CLEAN | 7 (1 D1, 3 D2, 3 D3) | `sweep` module, size-gated `dispatch.rs`; amendments #20, #21; Phase 2 exit gate |

**Total WP-level findings: 31** (7 D1, 9 D2, 10 D3, 5 D4). All resolved
(FIXED or FIXED+AMENDED/AMENDED). **All five WPs received `FAIL` at S2** —
a first for this project; Phase 0 had one `FAIL` (WP-001) and Phase 1 had
zero.

### 1.3 Global-session layer folded into this assessment

| Session | Date | Verdict | Findings | Headline |
|---|---|---|---|---|
| EA-003 | 2026-08-14 | PASS-WITH-REMEDIATION | 14 (E-F1–E-F14: 2 D1, 5 D2, 3 D3, 4 D4) | Restored a silently corrupted cumulative deviation ledger (E-F1); live-reran 9 previously-unverified CI runs (E-F2/E-F4); closed the tensor-parity invariant-vs-differential gap (E-F5) |
| EMA-001 | 2026-08-14 | FAIL (original) | M-F1–M-F6 (1 D1, 1 D2, 2 D3, 2 D4) | Z3-confirmed phase-wrap defect in `chimera.rs`, live since Phase 1 WP-010, missed by 3+ prior audit layers |
| EMA-001R | 2026-08-14 | PASS-WITH-REMEDIATION | (same ledger, all closed) | Fixed M-F1 with Z3 re-proof; resolved M-F3 via 2 new Lean 4 formal proofs (amendment #24) and recorded Wolfram Engine corroboration; amendment #25 documents a PRINet-3.0 upstream defect exception |

**Grand total across the full Phase 2 delta (WP + EA-003 + EMA-001): 51
findings** (10 D1, 15 D2, 15 D3, 11 D4). All 51 are resolved. This
session's own two findings (PA2-F1, PA2-F2, §5.4) are **additional and
open**, not part of the 51.

### 1.4 Deliverable inventory (independently verified)

| Artefact class | Phase 1 → Phase 2 delta | Total | Evidence |
|---|---|---|---|
| Rust crates | +2 new (`prin-tensor`, `prin-sim`) | 10 workspace crates | §2 |
| Rust source (`crates/prin-dynamics/src/integrate.rs`, `bands.rs`, `temporal.rs`) | +2,309 lines (integrators) + 1,518 (bands) + 991 (temporal), net of the pre-existing files | `crates/prin-dynamics/` | §2 |
| Rust source (`crates/prin-tensor/src/`) | +4 files (from 0): `lib.rs`, `error.rs`, `utils.rs`, `tucker.rs`, `cp.rs` | ~2,200 lines | §2 |
| Rust source (`crates/prin-sim/src/`) | +6 files (from 0): `lib.rs`, `error.rs`, `csr_coupling.rs`, `engine.rs`, `pruning.rs`, `chimera.rs`, `sweep.rs`, `dispatch.rs` | ~4,500 lines | §2 |
| Rust tests (unit + integration + doctest) | 375 (Phase 1 close) → **731/734** (default/strict-checks) | +356/+359 | §4.1 |
| Python fast tests | 241 (Phase 1 close) → 306 | +65 | §4.1 |
| Parity-marked tests (Python) | 6 representative → **510** (504-case exhaustive + harness) | +504 | §4.1, R8 delivered |
| Rust-native parity tests | 56 (Phase 1) → 79+ (WP-012 +7, WP-013 +18, WP-014 +9+1, WP-015 +21, WP-016 +8) | +23+ | §2 |
| Audit reports (`DOCS/audits/`) | +5 WP audits + EA-003 + EMA-001 | 8 new reports | §5.1 |
| Project state reports (`DOCS/reports/`) | +5 (012–016) + Deferred Validation Register | 5 new PSRs | §5.1 |
| Session briefs (`DOCS/sessions/phase-2/`) | +20 + README | 21 files | §5.1 |
| Plan amendments | +8 (#18–#25) | 25 total | §6.2 |

---

## 2. Dimension P4 — Coding and architecture

**Requirements (Plan §4, Coding Standards §2):** Crate layering
`dynamics → {metrics, tensor, kernels} → {sim, train, daemon} → py`.
`#![forbid(unsafe_code)]` on every crate except audited FFI exceptions. No
`panic!`/`unwrap`/`expect` in library code; typed errors at boundaries.
One-algorithm-one-implementation.

**Evidence:**

- Two new crates, `prin-tensor` and `prin-sim`, both carry
  `#![forbid(unsafe_code)]`; independently confirmed zero `unsafe` blocks
  in either crate's source this session (`cargo clippy` clean at both
  default and `strict-checks` feature sets).
- Crate layering holds exactly: `prin-tensor` depends on `prin-dynamics`
  only for `Seed` (EA-003 E2, independently confirmed); `prin-sim` depends
  on `prin-dynamics` + `prin-metrics` + `prin-kernels` (later reduced —
  `prin-kernels` removed as an unused dependency in WP015-F4 remediation).
- `dispatch.rs` (WP-016 S3) is a clean size-gated sequential/rayon
  dispatcher (`PARALLEL_LEN_THRESHOLD = 32,768`) that replaced an
  unconditional `par_bridge()`/`par_iter()` implementation shown to be up
  to 6× *slower* than serial (WP016-F1, D1) — a genuine architectural fix,
  not a cosmetic one.
- `Arc<SparseCoupling>` sharing (WP016-F7) eliminated a ~136 MB
  per-configuration CSR deep-clone at `N = 1M`.

**Weaknesses — three D1-severity code defects in one phase (vs. zero in
Phase 1):**

1. **WP012-F3:** `matrix_exp` silently returned the identity matrix on a
   singular Padé LU denominator instead of a typed error — a
   silent-wrong-value failure mode the numerical-parity program explicitly
   exists to prevent. Fixed by propagating `IntegrateError::LinearSolveFailed`.
2. **WP014-F3:** `hosvd` panicked on contract-valid input (`shape=(10,2,2)`,
   `ranks=[10,2,2]`) because the validated bound (`R_n ≤ I_n`) was weaker
   than the actual truncation bound (`R_n ≤ min(I_n, ∏_{k≠n} I_k)`). Fixed
   with the correct bound and boundary regression tests.
3. **WP016-F1:** the S1 parallel-sweep implementation was up to 6× slower
   than sequential — the S1 handoff's performance claims were not
   independently checked against a serial baseline before being reported.

**Score: 4 (Strong).** The architecture itself — crate layering, trait
dispatch, typed errors, feature-flag discipline — is sound and matches
Phase 1's standard. The score is 4 rather than 5 because three separate
S1 deliveries this phase shipped defects (silent wrong values, a reachable
panic, a severe unmeasured performance regression) that a baseline
self-check before handoff should have caught, a pattern absent from Phase 1.

---

## 3. Dimension P1 — Data and parity artefacts

**Requirements (Plan §5, Testing Standards §3):** Golden-corpus parity
cases exist for every touched primitive, generally *before* the primitive
lands (Testing Standards §1.3).

**The dominant Phase 2 failure pattern.** Three of five WPs (WP-012,
WP-013, WP-014) shipped their S1 commit with **zero** PRINet 3.0 parity
evidence for the headline deliverable, despite PRINet 3.0 reference
implementations existing and being directly importable in the project venv
in every case:

- WP012-F2 (D1): no parity tests for `ExponentialIntegrator`/`MultiRateIntegrator`.
- WP013-F1 (D1): no parity tests for `BandNetwork`/`TemporalPropagator`, despite
  the archived `ThetaGammaNetwork`/`TemporalPhasePropagator` reference being
  directly comparable.
- WP014-F1 (D1): no parity tests for `hosvd`/`cp_als`; the S1 handoff's
  justification ("no reference code was found") was factually refuted by
  the auditor in minutes — `prinet.core.decomposition` is present in the
  archive, has its own PRINet acceptance tests, and is importable in the venv.

All three were fixed in S3 with genuine Rust-vs-PRINet differential tests
(7, 18, and 9 cases respectively) at documented tolerances. EA-003's E-F5
subsequently discovered that even the WP-014 fix (`0a2c95d`) was
invariant-only, not a genuine cross-implementation comparison, and added a
true differential HOSVD-vs-PRINet reconstruction test
(`data/prinet_reference_hosvd.json`) — closing a gap that had survived
both the original S2 finding and its own S3 remediation.

**R8 delivered.** Phase 1's R8 recommendation (exhaustive 504-case Python
differential CI, vs. 6 representative cases) was implemented in the
inter-phase session before WP-012 S1: `parity/test_parity_differential.py`
now parametrizes over all 504 manifest case IDs, and this session
independently re-ran `pytest parity/ -m parity` → **510 passed** (504
exhaustive + 5 representative-smoke + 1 planted-deviation harness test).

**Score: 4 (Strong).** Post-remediation parity coverage is comprehensive
and, for HOSVD, genuinely stronger than Phase 1's equivalent (a true
differential test against a real reference, not embedded reference
arrays). The score is 4 rather than 5 because the *root cause* — three
consecutive S1 deliveries treating parity evidence as optional rather than
a co-requirement of the primitive itself — recurred three times in one
phase despite being flagged as D1 the first time (WP-012), indicating the
lesson had not yet propagated across WPs within the same phase.

---

## 4. Dimensions P2, P3 — Documentation and testing

### 4.1 Testing (P3)

**Independently re-verified this session (2026-08-15, `HEAD` `4d0f75b`):**

```text
cargo test --workspace                              → 731 passed, 0 failed
cargo test --workspace --features strict-checks     → 734 passed, 0 failed
cargo fmt --all -- --check                          → clean
cargo clippy --workspace --all-targets -- -D warnings                    → clean
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings → clean
pytest tests/ -m "not slow and not gpu" --cov=prin  → 306 passed, 6 deselected, 99% coverage
pytest parity/ -m parity                            → 510 passed (44.9s)
```

Growth vs. Phase 1 close (375 Rust / 241 Python fast / 6 parity-marked):
Rust +356 (731 vs 375, default), Python fast +65 (306 vs 241), parity-marked
+504 (510 vs 6 — R8 delivered). New property-test suites:
`crates/prin-sim/tests/proptest_properties.rs` (WP015-F6: sparse-vs-dense
parity at arbitrary N, memory-footprint correctness, determinism) and
`crates/prin-sim/tests/proptest_sweep.rs` (5 sweep-invariant properties).
Coverage on every touched file reached ≥95% post-remediation (`cp.rs`
86.76%→96.30%; `bands.rs` 92.00%→98.68% functions; `tucker.rs` 95.22%→95%+).

**R12 delivered.** `AGENTS.md`'s verification one-liner now runs
`cargo llvm-cov -p prin-dynamics` under both default and `--features
strict-checks`, merging coverage from both builds per Phase 1's R12.

**Score: 5 (Exemplary).** Test volume, parity depth, and property-test
coverage all grew substantially and every gate is independently green.
This is the one dimension where Phase 2 unambiguously exceeds Phase 1.

### 4.2 Documentation (P2)

**R7 delivered and appears to be working for WP-level cycles.** Phase 1's
R7 recommendation added an explicit "documentation accuracy sweep" to the
S4 checklist (Documentation Standards §7 item 8): README accuracy,
`cargo test --doc` verification, and `DOCS/` subdirectory index currency.
Every WP-014 through WP-016 closure references it, and this session's own
`RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` re-verification
is clean (0 warnings) — no regression from the item-8 checklist's own scope.

**But two gaps survived R7, both found independently by this session, not
by any WP-N S4 checklist:**

1. **PA2-F2 (D3):** `CHANGELOG.md`'s `[Unreleased]` section fully documents
   EA-003 (39 lines) but has **zero mention** of EMA-001 or the EMA-001R
   remediation — despite EMA-001 fixing a real D1 defect and adding three
   plan amendments. Root cause: R7's checklist item 8 is scoped to
   "touched crates" and "`DOCS/` subdirectories" within a *WP-N cycle*;
   EA-003 and EMA-001 are global sessions that sit outside any single WP's
   S4, so no S4 checklist ever runs against them. (EA-003 itself *did*
   receive a full CHANGELOG entry — this is not a structural gap in every
   global session, only in EMA-001's case.)
2. WP-014's S1 handoff asserted "no reference code was found" for the
   PRINet 3.0 decomposition module — a claim refuted by the auditor in
   minutes (WP014-F1) — and this factually incorrect justification passed
   into the committed handoff note before S2 caught it. This is not a
   stale-documentation gap (R7's target) but a fresh, unverified claim
   accepted at face value.

**Score: 3 (Adequate).** The R7 mechanism works within its designed scope
and this session found no regression there. The score is 3, not 4, because
this session's own independent verification — not any S4 checklist —
caught a real, non-trivial documentation gap (EMA-001 absent from the
release notes for a shipped correctness fix), which is exactly the kind of
finding the methodology's "independent verification" principle exists to
surface, and it means the phase's own audit net still has a structural
blind spot for global sessions.

---

## 5. Dimension P5 — Evidence and verification

### 5.1 Scan completeness

| Scan | Tool | Result | Evidence |
|---|---|---|---|
| Rust advisories | `cargo audit` | 0 vulnerabilities; 1 allowed inherited `paste` RUSTSEC-2024-0436 (amendment #9) | §5.4 |
| Python advisories | `pip-audit .` + `pip-audit -r DOCS/sphinx/requirements.txt` | 0 vulnerabilities (both) | §5.4 |
| Python security | `bandit -r . -c pyproject.toml` | 0 issues | §5.4 |
| Snyk Code | Not re-run this session (MCP unavailable) | Last verified 2026-08-14 (EA-003): 0 issues at medium-threshold gate | §5.3 limitation |
| Snyk Open Source | Not re-run this session (MCP unavailable) | Last verified 2026-08-14 (EA-003): 6 `torch@2.13.0` advisories accepted in `.snyk`, recheck 2026-11-14; 0 issues elsewhere | §5.3 limitation |
| Secret scanning | Gitleaks substitute (amendment #5) | Active; GitHub native still unavailable (DV-009) | Deferred Validation Register |

### 5.2 EMA-001 as a new evidentiary channel

EMA-001 is the first session in this project to independently **recompute**
mathematical claims rather than read the code's own reasoning — 8 of 23
claims reached genuine SymPy symbolic proof (the strongest evidentiary
tier), 5 reached Z3-proved invariants, and 2 reached Lean 4 kernel-checked
formal proof (added in the remediation, amendment #24). The headline result
(M-F1) is direct evidence that this channel catches defects source-level
review does not: `strength_of_incoherence`'s phase-wrap bug survived the
original WP-010 implementation, the WP-010 S2 audit (zero findings — the
cleanest audit of Phase 1), the Phase 1 analytics session, EA-001, EA-002,
and EA-003's own direct-source E1 review of this exact file three sessions
earlier. Independently confirmed this session: `cargo test --workspace`
includes the post-fix regression tests (`centred_wrap_maps_zero_to_zero`,
`strength_of_incoherence_local_coherence_not_inverted`) and passes.

### 5.3 Limitation: Snyk MCP unavailable this session

Per Analytics Methodology principle 4, this limitation is stated
explicitly rather than silently omitted: the Snyk MCP server was not
accessible in this analytics session, so Snyk Code/Open Source were not
independently re-executed against the current `HEAD`. The most recent
verified result is EA-003 (2026-08-14, one day prior, `HEAD` at that time
`fbe1c92`+remediation), which found 0 issues at the enforced gate threshold
and formally accepted the 6 `torch` advisories with a documented,
unreachable-in-PRIN's-code investigation and a 2026-11-14 recheck date. No
dependency manifest has changed between EA-003's scan and this session's
`HEAD` (`cargo audit`/`pip-audit` — both independently re-run this
session — confirm no new advisories), so this position is carried forward
as informational, not independently re-verified.

### 5.4 Independent re-verification (this session, 2026-08-15)

All commands executed on Windows, Python 3.14.0, Rust toolchain per
`rust-toolchain.toml`, against `HEAD` `4d0f75b`.

| Command | Result |
|---|---|
| `ruff check python/ tests/ benchmarks/ tools/ parity/` | **3 errors** in `tools/math_audit_run.py` (I001 + 2× E501) — **PA2-F1, new finding** |
| `ruff format --check python/ tests/ benchmarks/ tools/ parity/` | **1 file** (`tools/math_audit_run.py`) would be reformatted — part of PA2-F1 |
| `mypy python/prin --strict` | Success: no issues found in 18 source files |
| `interrogate -c pyproject.toml python/prin` | 100.0% (106/106), PASSED |
| `bandit -r . -c pyproject.toml` | 0 issues (all severities) |
| `pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing` | 306 passed, 6 deselected, 99% coverage |
| `pytest parity/ -m parity` | 510 passed in 44.91s |
| `cargo fmt --all -- --check` | Clean |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean |
| `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | Clean |
| `cargo test --workspace` | 731 passed, 0 failed |
| `cargo test --workspace --features strict-checks` | 734 passed, 0 failed |
| `cargo audit` | 0 vulnerabilities; 1 allowed `paste` advisory |
| `pip-audit .` | No known vulnerabilities |
| `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | 0 warnings |
| `sphinx-build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html` | Build succeeded, 0 warnings |
| `tools/wp001_baseline.py check` | Passed |

**New findings discovered in this session (not in any prior audit's
deviation ledger):**

| ID | Severity | Location | Issue | Status |
|---|---|---|---|---|
| **PA2-F1** | D2 | `tools/math_audit_run.py` | Fails the mandatory `ruff check`/`ruff format --check` gate (AGENTS.md verification one-liner scopes `tools/`): an unsorted import block (I001) and two lines exceeding 88 columns (E501). Introduced by the EMA-001 session (`630c5d6`, 2026-08-14) and never linted — EMA-001's own §6/§8 verification scoped Python gates to nothing, since it treated itself as a Rust-only-touching session, but it committed a new Python file. | **OPEN** — auto-fixable (`ruff check --fix` + `ruff format`); per Analytics Methodology §7 this triggers the normal Session Cycle remediation process (a hotfix), not a fix inside this analytics session. |
| **PA2-F2** | D3 | `CHANGELOG.md` `[Unreleased]` | Zero mention of EMA-001 or the EMA-001R remediation, despite EMA-001 fixing a real D1 defect (`chimera.rs` phase-wrap bug) and introducing 3 plan amendments (#23–#25). Documentation Standards §7 item 2 requires all user-visible changes recorded under `[Unreleased]`; EA-003 received a full entry, EMA-001 did not. | **OPEN** — same remediation path as PA2-F1. |

**Score: 4 (Strong).** Every gate this session is capable of re-executing
was re-executed, and all but one (a newly discovered, narrowly-scoped
tooling-lint gap) are green. EMA-001's tool-executed recomputation is a
qualitatively stronger evidentiary channel that already paid for itself by
catching a live defect three prior review layers missed. The score is 4
rather than 5 because of PA2-F1 (a currently-red mandatory gate on `main`)
and the Snyk re-verification gap, both stated rather than glossed over.

---

## 6. Dimension P6 — Governance and process

### 6.1 Session Cycle adherence

**20/20 Phase-2 sessions completed** in exact S1→S2→S3→S4 order across 5
WPs, independently confirmed against `DOCS/sessions/SESSION_REGISTER.md`
and `DOCS/sessions/phase-2/README.md` (both list all 20 rows `COMPLETE`).
No sessions skipped, merged, or reordered. Global sessions EA-003, EMA-001,
and EMA-001R are correctly recorded in the dedicated "Global sessions"
register section per amendment #15's precedent, outside the planned
0045–0064 sequence.

### 6.2 Deviation ledger

**31 WP-level findings across 5 audits, plus 14 EA-003 and 6 EMA-001
findings — 51 total. All 51 resolved.**

| Source | D1 | D2 | D3 | D4 | Total |
|---|---|---|---|---|---|
| WP-012 | 3 | 0 | 1 | 1 | 5 |
| WP-013 | 1 | 1 | 1 | 3 | 6 |
| WP-014 | 1 | 3 | 2 | 1 | 7 |
| WP-015 | 1 | 2 | 3 | 0 | 6 |
| WP-016 | 1 | 3 | 3 | 0 | 7 |
| **WP subtotal** | **7** | **9** | **10** | **5** | **31** |
| EA-003 | 2 | 5 | 3 | 4 | 14 |
| EMA-001 | 1 | 1 | 2 | 2 | 6 |
| **Grand total** | **10** | **15** | **15** | **11** | **51** |

**This session's own findings (open, not in the 51 above):** PA2-F1 (D2),
PA2-F2 (D3).

**Trend vs. Phase 1:** Phase 1 raised 22 WP findings with **0 D1**. Phase 2
raised 31 WP findings with **7 D1** — every WP received at least one D1.
This is the most significant governance signal in this report: the S1
implementation discipline that Phase 1's analytics report credited with
"internalizing the Phase 0 lessons" did not carry forward into Phase 2's
first-pass parity and correctness discipline, even though the *remediation*
discipline (S3 fixes, delta re-audits) remained thorough throughout.

### 6.3 Plan amendments (Phase 2)

| # | Subject | Status |
|---|---|---|
| #18 | Clarified WP-012 "multi-rate" as uniform sub-stepping matching PRINet 3.0 | Approved |
| #19 | Recorded the WP-013 band-network composition decision (continuous ODE vs. PRINet stepper) | Approved |
| #20 | Narrowed WP-016 scope to `crates/prin-sim/` only; `prin-py`/`prin-kernels` work deferred | Approved |
| #21 | Re-scoped performance targets to hardware-scoped, evidence-based values after S1 showed the original targets were a memory-bandwidth/SMT ceiling | Approved |
| #22 | `v0.3.0-alpha.1` retroactively covers both the Phase 1 and Phase 2 exit-tagging obligations; tag creation/push deliberately deferred | Approved (EA-003) |
| #23 | Introduced Executive Mathematical Audit (EMA) sessions as a new global-session type | Approved (EMA-001) |
| #24 | Enabled the Lean 4 formal-proof adapter for `GRA-01`/`TEN-01` | Approved (EMA-001R) |
| #25 | Documented the `strength_of_incoherence` PRINet-3.0-upstream-defect parity exception | Approved (EMA-001R) |

All amendments follow the normative process: documented rationale,
maintainer approval, amendment-log entry.

### 6.4 A structural gap this session exposes

R7 (Phase 1's S4 documentation-sweep strengthening) and the per-WP S2 audit
both operate at the WP-N cycle granularity. Neither EA-003 nor EMA-001 is a
WP-N cycle, so neither triggers R7's checklist. EA-003 happened to receive
a full CHANGELOG entry anyway (by the auditor's own initiative); EMA-001
did not (PA2-F2). This is a governance-process gap, not a one-off
oversight: nothing in the current standards *requires* a global session to
update the CHANGELOG, even though Documentation Standards §7 item 2's
underlying principle ("all user-visible changes... recorded") applies
identically. See Recommendation R14.

**Score: 4 (Strong).** 20/20 sessions in correct order; 51/51 findings
resolved across three independent verification layers, two of which
(EA-003, EMA-001) each caught a real D1 that the layer below it missed —
a self-correcting process working as designed. Not a 5: the 7-D1 WP
trajectory, E-F1's two-audit-cycle propagation, and this session's own two
fresh findings show real, currently-open gaps in the net, not merely
historical ones already closed.

---

## 7. Dimension P7 — Security

### 7.1 `unsafe` confinement

No new `unsafe` code in Phase 2. `prin-tensor` and `prin-sim` both carry
`#![forbid(unsafe_code)]`; independently confirmed via `cargo clippy`
(default + `strict-checks`) this session. The workspace's only `unsafe`
remains the two previously-audited FFI exceptions (`dlpack.rs`,
`cubecl.rs`, amendments #6/#8), spot-checked by EA-003 (every `unsafe`
block still carries a `// SAFETY:` comment).

### 7.2 Input validation

New typed-error surface added this phase: `IntegrateError::LinearSolveFailed`/
`InvalidDim` (WP-012), `BandError::NoBands` (WP-013), `TensorError::InvalidRank`/
`InvalidMode`/`InvalidMaxIter` (WP-014), `SimError` (10 variants, WP-015).
Each traces to a specific finding that required it (WP012-F3/F5, WP013-F5,
WP014-F3/F6) — the typed-error discipline held even where the underlying
D1/D2 defects show the *validation coverage* did not always land in S1.

### 7.3 Dependency security

- `cargo audit` (independently re-run this session): 0 vulnerabilities, 1
  allowed inherited `paste` RUSTSEC-2024-0436 (amendment #9).
- `pip-audit` (project + Sphinx requirements, both independently re-run):
  0 vulnerabilities.
- `bandit` (independently re-run): 0 issues.
- Snyk Code/Open Source: last verified by EA-003 (2026-08-14) — 0 issues
  at the enforced gate; 6 `torch@2.13.0` advisories formally accepted in
  `.snyk` (investigated for a genuine fix, none exists per Snyk's own
  `fixedIn: []`; confirmed unreachable via repository-wide grep; recheck
  2026-11-14). Not re-run this session (§5.3 limitation).
- New dependencies this phase: `faer = "0.20"` (dense linear algebra for
  `prin-tensor`, `cargo audit` clean on the added subtree). No new Python
  dependencies.

### 7.4 Secret scanning

Gitleaks substitute (amendment #5) remains in force; GitHub native secret
scanning remains unavailable (DV-009, re-checked every cycle per R11).

**Score: 4 (Strong).** No new `unsafe`; dependency scans clean modulo
governed, actively-managed advisories; the `torch` risk-acceptance process
(investigate first, accept only with evidence and a recheck date) is a
genuine strength. Not a 5 because Snyk re-verification is a documented gap
this session (not a finding, but a real limitation on independent evidence).

---

## 8. Dimension P8 — Phase exit criteria

### 8.1 Exit gate

The Phase 2 exit gate is **GREEN** per `DOCS/reports/016-project-state.md`
§5, independently re-confirmed this session:

| Criterion | Evidence | Verdict |
|---|---|---|
| `OscilloSim` parity at `N ≤ 1M` on CPU | Dense-vs-sparse parity at `N ∈ {8,16,64,256}` (Kuramoto) / `{8,16}` (Stuart–Landau) at `rtol = 1e-10`–`1e-12`; `N = 100,000` deterministic regression (bit-identical, finite, order parameter ∈ [0,1], coupling memory < 20 MB); `N = 1,000,000` benchmark evidence. Full dense-vs-sparse parity at `N = 1M` is mathematically infeasible (~8 TB dense matrix). | **GREEN** |
| Sweep speedup on multi-core CPU | Amended (#21) to hardware-scoped targets after S1 evidence showed the original ≥8×/≥2× targets were a memory-bandwidth/SMT ceiling on the reference hardware; peak measured 3.92× at 8 configs (≥3.5× target met); SpMV/engine 1.29–1.51× at `N ≥ 65,536` (≥1.5× target met). EA-003's E8 independently confirmed the serial-baseline benchmark methodology is genuine (direct source read of `sweep_bench.rs`), not fabricated. | **GREEN** (amended) |
| All 5 WPs complete | WP-012 through WP-016, all COMPLETE with CLEAN delta re-audits. | **GREEN** |
| All quality/security/parity gates green | Independently re-verified this session (§5.4): 731/734 Rust tests, 306 Python fast, 510 parity, 0 clippy/mypy/bandit/audit findings (1 allowed advisory), Sphinx/rustdoc 0 warnings — with the one exception of PA2-F1, discovered after the exit gate was declared. | **GREEN at declaration time; PA2-F1 is a post-declaration regression, not a gate the exit criterion was evaluated against** |

**Phase 2 exit-gate verdict: GREEN**, consistent with PSR-016. PA2-F1 does
not retroactively invalidate the exit gate — `tools/math_audit_run.py` was
committed by the EMA-001 session, which post-dates the WP-016 S4 exit-gate
declaration (`dac017e`/`fbe1c92`) by design (EMA-001 is a Phase-2-adjacent
global session, not part of the exit criteria).

### 8.2 Deferred and carried-forward scope

| Item | Origin | Disposition |
|---|---|---|
| `prin-py` sweep/engine PyO3 bindings | WP-016 declared scope, amendment #20 narrowed it out | Deferred to a future WP; not a Phase 3 blocker but should land before Phase 7 scientific campaigns use the Python sweep API |
| `prin-kernels` CPU-reference work | Same as above | Same disposition |
| Exponential/multi-rate integrator GPU kernels | Original Phase 1 deferral | Phase 3 (WP-017/018) |
| Tensor decomposition GPU acceleration | Not in Phase 2 scope | Not yet scheduled |

**Score: 4 (Strong).** All exit criteria genuinely met, with an honestly
disclosed and evidence-backed amendment (#21) rather than a silently
lowered bar — EA-003 independently checked this and found no fabrication.
Not a 5 because of the same trajectory concerns noted in P4/P6.

---

## 9. Dimension P9 — Risk and deferred validation

### 9.1 Phase 1 recommendation tracking

| Rec | Priority | Status | Evidence |
|---|---|---|---|
| R7 — Strengthen S4 doc-accuracy sweep | P1 | **Implemented** — Documentation Standards §7 item 8; cited in WP-014..016 closures; but does not cover global sessions (§4.2, §6.4) |
| R8 — Exhaustive 504-case parity CI | P1 | **Implemented** — `parity/test_parity_differential.py` parametrized over all 504 cases; 510/510 independently re-verified this session |
| R9 — Deferred Validation Register | P2 | **Implemented** — `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` created, 10 active items tracked |
| R10 — Kernel coverage reporting | P2 | **Deferred to Phase 3 (WP-017)** as planned — no new kernel code in Phase 2 |
| R11 — Secret scanning availability checks | P2 | **Ongoing** — rechecked each cycle (DV-009) |
| R12 — `strict-checks` coverage merge | P2 | **Implemented** — `AGENTS.md` runs `cargo llvm-cov -p prin-dynamics` under both feature sets |
| R13 — Parameterize WP-012 tests against corpus | P3 | **Implemented** — WP-012 parity tests include convergence-order and RK4-agreement checks |

**All 7 Phase 1 recommendations are addressed.** This is a genuine
strength: the inter-phase recommendation-implementation session (governed
by `DOCS/ANALYTICS/phase-1/phase-1-recommendation-implementation-governance.md`)
delivered on every P1/P2 item before WP-012 S1 began.

### 9.2 Risk register accuracy

| Risk | Status | Mitigation |
|---|---|---|
| `torch@2.13.0` (6 advisories) | Accepted | `.snyk`, maintainer approval, 2026-11-14 recheck |
| Inherited `paste` advisory | Governed | Amendment #9, rechecked every cycle |
| Missing `v0.2.0-alpha.1` tag / untracked drift | Resolved | Amendment #22; `v0.3.0-alpha.1` jointly covers both phase-exit obligations; actual tag push deliberately deferred to explicit maintainer action |
| `prin-py`/`prin-kernels` carried scope | Tracked | Amendment #20; not a Phase 3 blocker |
| GitHub Actions billing block (WP-014/013) | Resolved | Restored 2026-08-14; all previously-blocked workflows re-run live and green (EA-003 E-F2/E-F4) |
| `strength_of_incoherence` phase-wrap defect (M-F1) | Resolved | EMA-001R fix + Z3 re-proof + amendment #25 |
| `M-F3` policy-gate interaction (4 ODE claims permanently `REQUIRES_HUMAN_REVIEW`) | Accepted | Documented, evidence-backed (SciPy + independent Wolfram corroboration), signed off — a deliberate policy design, not a defect |

**Score: 4 (Strong).** Every Phase 1 recommendation was implemented before
Phase 2 began — a stronger inter-phase discipline than Phase 0→1 achieved
(where R1/R2/R5 were only partially addressed). The risk register is
current and every open item has an explicit owner and gate.

---

## 10. Cross-dimensional analysis

### 10.1 Patterns and correlations

1. **First-pass parity/correctness discipline regressed from Phase 1's
   peak.** Phase 1 closed with 0 D1 findings across 22; Phase 2 opened
   with 7 D1 across 31, one in every single WP. The dominant pattern —
   missing parity evidence for the headline deliverable — recurred
   identically in WP-012, WP-013, and WP-014 despite being flagged D1 the
   first time. This is the single most actionable signal in this report
   (see R14/R15).
2. **Remediation and verification discipline did not regress — it
   strengthened.** Every S3 delta re-audit is genuinely CLEAN (not merely
   claimed), and two entirely new independent-verification layers
   (EA-003's live CI/git-object re-verification, EMA-001's tool-executed
   recomputation) were introduced and each caught a real defect the layer
   below it missed. The project's response to a rockier S1/S2 trajectory
   was to add more independent checking, not to relax the bar.
3. **Independent tool-executed verification outperforms source review for
   mathematical claims.** M-F1 survived a clean WP-010 S2 audit, the Phase
   1 analytics session, EA-001, EA-002, and EA-003's own direct E1 review
   — five prior passes, all reading the same ~15 lines of code, all
   missing the same bug. Z3 found it by construction. This validates
   EMA-001 as a structurally distinct control, not a redundant one.
4. **Governance-integrity defects can propagate silently even within a
   self-documenting process.** E-F1's ledger corruption survived two full
   S2 audits (WP-015, WP-016) because neither cross-checked the cumulative
   table against the prior PSR — the exact check that caught it when
   finally applied. The "restore from last verified" fix is sound; the
   structural gap (no automated ledger-diff check) is not yet closed.
5. **This analytics session's own findings repeat pattern 4 at a smaller
   scale.** PA2-F1 (a red lint gate) and PA2-F2 (a missing CHANGELOG
   entry) both exist because a global session (EMA-001) sits outside every
   automated or checklist-driven verification net in the current
   standards. The fix pattern from #4 — extend the check to cover the
   previously-uncovered case — applies here too (R14).

### 10.2 Systemic strengths

- **Remediation quality held the line.** All 31 WP findings + 14 EA-003 +
  6 EMA-001 = 51 findings are genuinely resolved, independently
  re-verified in this session down to the individual test/command level,
  not accepted on the strength of the closing report's own prose.
- **Honest amendment over silent goal-lowering.** Amendment #21
  (performance targets) is the clearest example: S1 evidence showed the
  original targets were physically unreachable on the reference hardware,
  and the response was a disclosed, evidence-backed amendment — verified
  genuine by an independent audit (EA-003 E8) — rather than a quietly
  adjusted benchmark.
- **Inter-phase recommendation discipline improved.** All 7 Phase 1
  recommendations were implemented before Phase 2 S1, a stronger record
  than Phase 0→1's partial completion of R1/R2/R5.
- **New crates are architecturally clean.** `prin-tensor` and `prin-sim`
  both hold `#![forbid(unsafe_code)]`, correct crate layering, and typed
  errors from their first commit — the defects found in each were
  correctness/coverage gaps, not architectural violations.

### 10.3 Systemic weaknesses

- **Parity evidence is still being treated as a follow-up task rather than
  a co-requirement**, three cycles running, despite explicit standards
  language ("written or identified *before* the algorithm lands," Testing
  Standards §1.3) and a D1 precedent from the first occurrence.
- **No automated safeguard against cumulative-ledger corruption or
  drift.** E-F1 was caught by a human/AI auditor manually diffing two
  PSRs; nothing in CI or the S2 checklist would catch a repeat.
- **Global sessions (EA/EMA) fall outside every WP-scoped checklist**,
  including R7's documentation sweep — a gap this session's PA2-F1/PA2-F2
  both trace to directly.
- **S1 handoffs occasionally assert unverified claims as fact** (WP-014's
  "no reference code was found"), and S1 exit review did not catch it
  before it reached the committed handoff note.

---

## 11. Comparison with Phase 1

| Metric | Phase 1 | Phase 2 | Delta |
|---|---|---|---|
| Work packages | 6 | 5 | −1 |
| Sessions | 24 | 20 | −4 |
| Commits (WP range) | 53 | 52 | −1 |
| WP audit findings (total) | 22 | 31 | +9 |
| WP D1 findings | 0 | 7 | **+7** |
| WP D2 findings | 7 | 9 | +2 |
| WP D3 findings | 5 | 10 | +5 |
| WP D4 findings | 10 | 5 | −5 |
| WPs with `FAIL` S2 verdict | 0 | 5 | **+5** |
| Executive/EMA-tier sessions | 2 (EA-001, EA-002) | 2 (EA-003, EMA-001+R) | = |
| Executive/EMA-tier findings | 18 | 20 | +2 |
| Rust tests (default) | 375 | 731 | +356 |
| Python fast tests | 241 | 306 | +65 |
| Parity-marked tests | 6 (representative) | 510 (exhaustive) | +504 |
| Python coverage | 99% | 99% | = |
| Plan amendments | 3 (#14–#16) | 8 (#18–#25) | +5 |
| New crates | 0 | 2 (`prin-tensor`, `prin-sim`) | +2 |
| Aggregate verdict | PASS — EXCELLENT | **PASS — SATISFACTORY** | **↓ one tier** |

---

## 12. AI assistance disclosure

This Phase 2 Analytics Report was drafted by Claude Code (AI pair) with
independent re-execution of every quality, test, coverage, security, and
documentation-build gate listed in §5.4 against `HEAD` `4d0f75b`
(2026-08-15) — not by re-reading the audit reports' own claims. The two new
findings (PA2-F1, PA2-F2) were discovered by this independent
re-verification, not carried from any prior document. The methodology
follows `DOCS/ANALYTICS/ANALYTICS_METHODOLOGY.md`. Snyk Code/Open Source
were not independently re-executed this session (MCP tool unavailable);
this limitation is stated in §5.3 and the corresponding evidence is scoped
to EA-003's last verification rather than claimed as re-confirmed.
Maintainer review is required before issuance.

---

## 13. Errata policy

If a claim in this report is later invalidated, an erratum will be
appended to this report and noted in `CHANGELOG.md`, per the
Experimentation Standards §4 and the Analytics Methodology §6.
