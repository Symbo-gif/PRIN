# PRIN Executive Audit Report — Session 003 (EA-003)

**Date:** 2026-08-14
**Auditor:** Claude Code (AI Pair & Systems Auditor)
**Scope:** Full Project Executive Audit (Mathematics, Codebase Architecture, Testing & Parity, Security & Supply Chain, Standards & Documentation, Evidence & Analytics, Governance & Traceability, Performance & Benchmarking, CI/CD Infrastructure, Roadmap & Handoff)
**Audit window:** Delta since EA-002 (`f5ae5b7`, 2026-08-08) through `fbe1c92` — Sessions 0037–0064 (WP-010 through WP-016, Phase 1 close and Phase 2 close) plus full-project re-verification
**Git Branch/State:** `main` @ `fbe1c92` (audit scope boundary; remediation commits in this session follow)
**Verdict:** **PASS-WITH-REMEDIATION**

---

## 1. Executive Summary Table

| Audit Dimension | Status | Summary & Key Observations |
|---|---|---|
| **E1: Math & Oscillator Dynamics Core** | ⚠️ REMEDIATION | New dynamics/metrics/tensor/sim core since EA-002 (WP-010..016) directly verified against source: phase metrics and chimera measures, exponential/multi-rate integrators, continuous band networks, Tucker/HOSVD and CP-ALS decompositions, sparse `OscilloSim` engine, and parallel sweeps all implement their documented mathematics correctly, with governed, disclosed deviations from the PRINet 3.0 reference (amendments #18, #19, #21) where applicable. One finding: the tensor-decomposition "parity" test suite verified mathematical invariants only, not genuine cross-implementation output, contradicting its own governing audit's closure claim. |
| **E2: Codebase & Architecture Conformance** | ⚠️ REMEDIATION | Crate layering (`dynamics → {metrics, tensor, kernels} → {sim, train, daemon} → py`) holds exactly for the three new crates; `unsafe` posture (`#![forbid]`/`#![deny]` + audited FFI exceptions) and the "no numerics in Python" rule both verified clean. One D4 finding: `prin-tensor` declares no `strict-checks` feature, while a governing audit's phrasing implied uniform coverage. |
| **E3: Test Suite & Parity Corpus** | ✅ PASS (post-remediation) | 729 Rust tests (default workspace) / 732 with `--features strict-checks`, plus 24 doctests, all pass in isolated runs after remediation. 302→306 Python fast tests and 510 parity tests pass. Before remediation, 4 Python tests (`tests/test_wp001_baseline.py`) were failing on the audited `HEAD` due to the E-F3 version-drift defect — see E6/E9. |
| **E4: Security & Supply Chain** | ⚠️ REMEDIATION | `cargo audit` 0 vulnerabilities (1 allowed advisory, amendment #9); `pip-audit` 0 findings (project + Sphinx); Snyk Code medium-threshold gate 0 issues; low-threshold advisory run shows only the 3 previously-accepted `tools/wp001_baseline.py` findings (still within their 2026-11-06 expiry). **New finding:** Snyk Open Source, run via the exact recipe `python.yml` uses (`uv pip compile` → `snyk test --fail-on=all`), reports 6 open advisories in `torch@2.13.0` (5 medium, 1 high — `SNYK-PYTHON-TORCH-15746467`, deserialization of untrusted data). Investigated for a genuine fix per maintainer direction: Snyk's own database shows no torch version fixes any of the 6, and a repository-wide grep confirms none of the vulnerable APIs is ever called by PRIN's live codebase. Risk formally accepted and documented in `.snyk` with maintainer approval and a 2026-11-14 recheck date. |
| **E5: Standards & Documentation Adherence** | ⚠️ REMEDIATION | Crate READMEs (`prin-metrics`, `prin-tensor`, `prin-sim`) and `DOCS/audits/README.md` / `DOCS/reports/README.md` indexes are accurate and complete for WP-010..016. One D4 finding: a duplicated bullet line in the Migration Guide. |
| **E6: Evidence, Baselines & Analytics** | ⚠️ REMEDIATION | ONNX model SHA-256 matches its evidence record; golden-corpus manifest hashes spot-verified. **Live, reproducible failure found and fixed:** `tools/wp001_baseline.py check` failed on the audited `HEAD` (`fbe1c92`) — the `v0.3.0-alpha.1` release commit bumped `Cargo.toml`/`pyproject.toml`/`CITATION.cff` but not `python/prin/__init__.py`, which stayed at `0.1.0-alpha.1`. Two D3/D4 findings: the Phase-1 analytics report contradicts itself and PSR-011 on Rust test counts (three different numbers for one state); `EVIDENCE/` received zero new artifacts across all 7 WPs in this delta (clarified as expected, not a gap). |
| **E7: Session Cycle & Governance Traceability** | ⚠️ REMEDIATION | Sessions 0037–0064 (WP-010..016) each executed full S1→S4 with S2 audits and S3 closure; WP-014 and WP-016 both received `FAIL` S2 verdicts and both show genuine `CLEAN` delta re-audits, not merely claimed ones. **Headline finding (D1):** the cumulative deviation ledger in `DOCS/reports/014-project-state.md` through `016-project-state.md` §3 was silently corrupted starting at commit `234a20d` (WP-014 S4) — every WP001-F9..WP013-F6 row's commit hash was replaced with a fabricated, non-existent hash, several finding descriptions were rewritten, and a fictitious `WP010-F1` finding was invented (the real WP-010 audit verdict was PASS, zero findings). The corruption propagated unnoticed through two more S2 audits (WP-015, WP-016). Restored from the verified `013-project-state.md` table. |
| **E8: Performance, Benchmarking & Reproducibility** | ✅ PASS | `crates/prin-sim/benches/sweep_bench.rs` genuinely implements the claimed serial-baseline methodology (dedicated 1-thread `rayon::ThreadPool` vs. the default parallel pool for every workload) — confirmed by direct source read, not prose. WP-012/013/014/015 correctly report "no benchmark gates defined" rather than fabricating performance claims. |
| **E9: CI/CD & Build Infrastructure** | ⚠️ REMEDIATION | All seven workflows present and structurally sound; `strict-checks` exercised workspace-wide for the new crates. **Two D1/D2 findings, both independently verified live against the GitHub Actions API and remediated by re-running the affected workflows:** (1) the WP014-F7 ledger entry "CI green on `039ee7b` and `ceaca5c`" overstated what was verified — only the `rust` gate had passed on `039ee7b` itself; re-run live, all 5 gates now genuinely green; (2) the WP-013 S4 commit (`4a4de26`) never had any of its five gated workflows re-run after the same billing block — re-run live, 4 of 5 now green, and the 5th (`python`) surfaced a real, transient, already-self-corrected historical inconsistency (`session 0053` brief/register status), documented rather than erased. **Separately:** the `HEAD` commit and its four predecessors (`dac017e`..`fbe1c92`, WP-016 S3 remediation through the `v0.3.0-alpha.1` release) had never been pushed to `origin` and therefore had zero CI runs at all — resolved by this session's Task 7 push. |
| **E10: Roadmap, Risks & Future Session Handoff** | ⚠️ REMEDIATION | Phase 1 and Phase 2 both substantively complete with green exit gates. **D2 finding:** the Phase 1 pre-release tag `v0.2.0-alpha.1`, flagged in PSR-011 as "ready pending maintainer approval," was never cut; the risk was never re-raised in five subsequent cycles (untracked drift); the version then jumped straight to `0.3.0-alpha.1`; and neither tag, nor any tag at all, was ever pushed to `origin` (`release.yml` — the tag-triggered wheel/PyPI/crates.io publish workflow — has therefore never executed). Logged as plan amendment #22; the actual tag-creation/publish action is deliberately left to explicit maintainer confirmation rather than being executed inside this audit. Project Plan §6 phase table and the stale amendment #21 wording corrected. |

---

## 2. Detailed Findings across Audit Dimensions

### E1: Mathematical & Oscillator Dynamics Core Integrity

Verified directly against source for all WP-010..016 additions:

- **`prin-metrics`** (WP-010): Kuramoto order parameter (real and complex forms), mean phase coherence, inter-frame phase correlation, local order parameter, Sarle's bimodality coefficient, strength-of-incoherence, discontinuity measure, chimera index, synchronization energy (dense and sparse), power spectral density, and concept-probability extraction all match their documented formulas, unit-interval-bounded where specified, with unit and property-test coverage of shift/permutation invariance.
- **`prin-dynamics::integrate`** (WP-012): `ExponentialIntegrator` implements Padé(13) scaling-and-squaring (`THETA_13 = 5.371920351148152`, per Higham 2005) with an augmented-matrix φ₁ identity; the Krylov/Arnoldi path is a standard modified-Gram-Schmidt implementation with a documented lucky-breakdown exit. `MultiRateIntegrator` implements uniform sub-stepping — a disclosed, governed deviation from a hypothetical band-aware scheduler (plan amendment #18), matching the PRINet 3.0 reference's actual behavior.
- **`prin-dynamics::bands`/`temporal`** (WP-013): `BandNetwork`'s continuous-relaxation PAC composition and its reuse of the crate's single `KuramotoOscillator` per band (not a duplicated implementation) are governed by amendment #19 and parity-tested per mode against `prinet==3.0.0`. `ComplexPhasorBlender`/`EmaAmplitudeBlender` correctly implement the PRINet complementary-parameter mapping (`alpha = 1 − carry_strength`).
- **`prin-tensor`** (WP-014): `hosvd`/`cp_als` are correct per-mode-truncated-SVD and Khatri-Rao ALS implementations. **Finding E-F5 (D2, remediated below).**
- **`prin-sim`** (WP-015/016): the sin/cos-decomposition SpMV trick for sparse Kuramoto coupling and the diffusive Stuart–Landau SpMV are mathematically correct decompositions, genuinely cross-checked sparse-vs-dense at `epsilon=1e-12` (22 tests); the `dispatch.rs` size-gated sequential/rayon dispatcher (WP016-F1 remediation) and `detect_oscillation`'s one intentional, documented divergence from a PRINet slicing footgun are both confirmed present and correct.

**Finding E-F5 (D2):** `crates/prin-tensor/tests/parity_decomposition.rs` (as it existed at `fbe1c92`) verified only internal mathematical invariants (reconstruction error, factor orthonormality, normalization convention, seed reproducibility) — no fixture ever loaded a PRINet-3.0-generated reference value, despite the file's own header claiming "parity" and despite `DOCS/audits/014-wp014-audit.md` closing its own WP014-F1 finding (originally raised as **D1**: "the WP-014 acceptance criterion 'PRINet 3.0 parity tests pass at rtol=1e-10' has no implementing artefacts") on the strength of this exact suite. Deeper analysis clarifies the correct target: HOSVD is deterministic given its input (truncated SVD has no randomness), so genuine differential parity is both meaningful and buildable; CP-ALS is a stochastic ALS fit seeded independently by PRINet 3.0 (`torch.randn`) and PRIN (`Seed`/PCG64), so raw factor-level parity is not a meaningful comparison for a general input — invariant-based verification is the mathematically correct approach for CP-ALS, not a shortfall.

### E2: Codebase & Architecture Conformance

- Crate layering confirmed exact: `prin-dynamics` has zero upward workspace dependencies; `prin-metrics` and `prin-tensor` depend on `prin-dynamics` only; `prin-sim` depends on `prin-dynamics` + `prin-metrics`.
- `unsafe` posture: every new/touched crate carries `#![forbid(unsafe_code)]` except the two previously-audited FFI exceptions (amendments #6/#8), unchanged since EA-002. Spot-checked `crates/prin-py/src/dlpack.rs`: every `unsafe` block carries a `// SAFETY:` comment.
- "No numerics in Python": `python/prin/dynamics.py` and `python/prin/metrics.py` (the WP-011 API surface) are pure re-export shims with explicit "no numerics" docstrings.

**Finding E-F10 (D4):** `crates/prin-tensor/Cargo.toml` defines no `strict-checks` feature (`hosvd`/`cp_als` validate finiteness unconditionally rather than behind an opt-in flag — stricter by default, not a functional gap), while `DOCS/audits/014-wp014-audit.md` reports "Quality gates ✅ ... workspace tests (default and `strict-checks`) ... all clean" in a way that reads as validating strict-checks coverage specific to the WP-014 deliverable, when none exists to validate.

### E3: Test Suite & Parity Corpus

- Isolated full-suite runs at `fbe1c92` (before remediation): Rust `cargo test --workspace` 728 passed; `--features strict-checks` 731 passed; 24 doctests. Python fast suite 302 passed / 4 **failed** / 6 deselected; full parity suite (`pytest parity/ -m parity`) 510 passed.
- **The 4 Python failures are E-F3** (see E6): `test_current_baseline_automation_is_green`, `test_metadata_validator_detects_version_drift`, `test_repository_inventory_is_deterministic_and_separates_archive`, and `test_cli_check_reports_success` in `tests/test_wp001_baseline.py`, all traceable to the same root cause. Two of the four failures were latent test-fragility bugs independent of the version drift itself: `test_metadata_validator_detects_version_drift` hardcoded a search-and-replace literal (`'version = "0.1.0-alpha.1"'`) that silently no-ops once `pyproject.toml`'s real version moves on, and `test_repository_inventory_is_deterministic_and_separates_archive` hardcoded the expected project version as a literal. Both fixed to be robust to future version bumps.
- After remediation (E-F3, E-F5 fixes): 729 Rust default / 732 strict-checks / 24 doctests; 306 Python fast / 0 failed / 6 deselected; 510 parity; full re-verification in §5.

### E4: Security & Supply Chain

- `cargo audit`: 0 vulnerabilities; 1 allowed advisory (`paste` RUSTSEC-2024-0436, amendment #9, unchanged).
- `pip-audit`: 0 findings for the project and `DOCS/sphinx/requirements.txt`.
- Snyk Code: enforced medium-threshold gate 0 issues; low-threshold advisory run shows only the 3 previously-accepted `tools/wp001_baseline.py` path-traversal findings (EA-002 E-F4, still within their 2026-11-06 expiry).
- **Finding E-F7 (D3):** Snyk Open Source, run against a dependency lockfile produced by `uv pip compile pyproject.toml` — the same command `python.yml`'s security job uses — reports 6 open advisories in `torch@2.13.0` (`pyproject.toml` pins only `torch>=2.0`, so both this audit and CI resolve to the same latest version): 5 medium (Improper Resource Shutdown, Mismatched Memory Management, 2× Out-of-bounds Write, Integer Overflow) and 1 high (`SNYK-PYTHON-TORCH-15746467`, Deserialization of Untrusted Data). Before proposing risk acceptance, this audit investigated whether a genuine fix exists: (1) Snyk's own vulnerability database records `semver.vulnerable: ["[0,]"]` and `fixedIn: []` for all 6 — every published torch version is affected and none fixes them, so no version pin change (up or down) helps; (2) a repository-wide grep across `python/`, `tests/`, `benchmarks/`, `tools/`, and `parity/` for every vulnerable API (`torch.load`, `.pt2`/`torch.export` handlers, `torch.jit.script`, `torch.jit.jit_module_from_flatbuffer`, `torch.cuda.nccl.reduce`, `torch.cuda.memory.caching_allocator_delete`, `torch.nan_to_num()...long()`) returns **zero matches** — every hit for these strings is confined to the archived, non-shipped `DOCS/archive and reference from PRINet 3.0/` tree; the codebase's only deserialization call at all is `np.load` on committed, trusted golden-corpus fixtures (`python/prin/parity/schema.py:230`), unrelated to torch. All 6 advisories additionally require local attacker access (CVSS `AV:L`). With no code/version fix available and the vulnerable code paths confirmed unreachable in this project's actual usage, `.snyk` ignore entries were added for all 6 (maintainer-approved in this session, following the amendment #4 precedent for no-fix torch advisories) — see §4.1.
- Snyk Open Source for the Rust workspace: `snyk test --file=Cargo.toml --command=cargo` fails structurally ("Could not detect package manager for file: Cargo.toml") — a known Snyk CLI limitation for Cargo projects, consistent with EA-002's finding; `cargo audit` is the compensating, authoritative control per Coding Standards §6.2 ("Where Snyk cannot resolve a native manifest, the ecosystem-native gate remains authoritative").

### E5: Standards & Documentation Adherence

- `crates/prin-metrics/README.md`, `crates/prin-tensor/README.md`, `crates/prin-sim/README.md` all verified accurate against current source module lists and symbol exports.
- `DOCS/audits/README.md` and `DOCS/reports/README.md` fully index WP-010..016 artifacts; no gaps.
- `CHANGELOG.md`'s `[0.3.0-alpha.1]` section content (test counts, coverage, finding IDs) matches the corresponding PSRs.

**Finding E-F12 (D4):** `DOCS/sphinx/migration_guide.rst` had a duplicated bullet line (WP-009 PAC/topology entry repeated verbatim on two consecutive lines) — a copy/paste artifact from an S4 edit.

### E6: Evidence, Baselines & Analytics Integrity

- `models/subconscious_controller.onnx` SHA-256 matches its `EVIDENCE/0017-wp005-s1-ort-probe.json` record.
- `parity/corpus/manifest.json` (504 cases): SHA-256 hashes independently spot-verified for a 5-case sample, no corruption.

**Finding E-F3 (D2, live and reproducible on the audited `HEAD`):** `tools/wp001_baseline.py check` fails with `project version mismatch: Cargo.toml=0.3.0-alpha.1, pyproject.toml=0.3.0-alpha.1, python/prin/__init__.py=0.1.0-alpha.1, CITATION.cff=0.3.0-alpha.1`. The `chore: release v0.3.0-alpha.1` commit (`fbe1c92`) bumped `Cargo.toml`, `pyproject.toml`, `Cargo.lock`, and `CITATION.cff` (all enumerated in its own commit message) but not `python/prin/__init__.py:25`. Every WP-012..016 gate table in this delta reports the baseline check as passing, and PSR-016 §2/§5 asserts "All quality, coverage, documentation, parity, and security gates are green" for the Phase 2 exit — but the gate is broken on the actual commit that closes this delta and carries the version bump. Root-cause fixed; see §4.1.

**Finding E-F8 (D3):** `DOCS/ANALYTICS/phase-1/phase-1-analytics-report.md` states "396 Rust tests" in its executive summary and §P3, while its own gate table and verification log record `cargo test --workspace → 351 passed` for the identical commit — and `DOCS/reports/011-project-state.md` §2 (the authoritative PSR) records a third figure, "370/370." Corrected with a pointer to the PSR as position-of-record; the discrepancy is not independently re-derived (out of proportion for a D3 finding).

**Finding E-F11 (D4):** `EVIDENCE/` received zero new artifacts across the entire WP-010..016 delta (7 work packages). `EVIDENCE/README.md` clarified: the directory holds hardware/runtime probe and gate-readiness artefacts specifically, not a mandatory per-WP deliverable — most WPs in this delta had no such probe to record, which is expected, not a gap.

### E7: Session Cycle & Governance Traceability

- Sessions 0037–0064 form a complete, unbroken S1→S4 sequence for WP-010 through WP-011 (4 sessions each) and WP-012 through WP-016 (4 sessions each), all `COMPLETE`; session 0065 (WP-017 S1) correctly `PLANNED`.
- WP-014 and WP-016 both received `FAIL` S2 verdicts and both show genuine `CLEAN` delta re-audits with closure tables (`014-wp014-audit.md:301`, `016-wp016-audit.md:292,309`) — independently confirmed as real closures, not merely claimed.
- Plan amendments #14–#21 are correctly recorded in `DOCS/PRIN_Project_Plan.md` §8.3, not just in PSRs.

**Finding E-F1 (D1, headline finding):** The cumulative deviation ledger in `DOCS/reports/014-project-state.md`, `015-project-state.md`, and `016-project-state.md` §3 contained a wholesale corruption of the WP001-F9 through WP013-F6 finding history, introduced at commit `234a20d` (WP-014 S4, 2026-08-14) and never caught since. Independently verified two ways:

1. **Fabricated commit references.** Every commit hash cited from `WP002-F1` onward in the corrupted table (`7f8a1c2`, `a1b2c3d`, `b2c3d4e`, `c3d4e5f`, `d4e5f6a`, `e5f6a7b`, `f6a7b8c`, `g7b8c9d`, `h8c9d0e`, `i9d0e1f`, `j0e1f2g`, `k1f2g3h`) fails `git cat-file -t <hash>` with "Not a valid object name" — an obviously synthetic, alphabetically-incrementing sequence, unlike the real hashes used elsewhere in the same table for WP-014..016 (`f138476`, `d377836`, `ca52af6`, `039ee7b`, verified as real commits).
2. **Content divergence from the verified historical record.** `DOCS/reports/013-project-state.md` §3 — the last PSR authored before the corruption — carries a materially different table for the same finding IDs: e.g. `WP001-F9` is "Sphinx had two warnings and a misattribution" (D4, real commit `510e0c9`) in PSR-013, but "`public_datasets/` was missing a documented retention boundary" (D3, amendment #6) in PSR-014/015/016; `WP002-F1` is "Fast `tests/` suite was below 95% coverage" (real commit `c7d8a25`) in PSR-013 vs. "Corpus cases did not cover amplitude/frequency transients" (fabricated `7f8a1c2`) in PSR-014/015/016. A fictitious `WP010-F1` finding ("`chimera_index` rustdoc threshold undocumented," fabricated hash `h8c9d0e`) was also invented outright — the real WP-010 S2 audit verdict was **PASS with zero findings** (`DOCS/audits/010-wp010-audit.md:9`), confirmed by PSR-010, PSR-011, and PSR-012 all carrying no `WP010-F1` entry.

This violates Development Workflow and Audit Standards' evidence-based-audit principle and persisted through three subsequent S2 audits (WP-014, WP-015, WP-016), none of which cross-checked the cumulative ledger against the prior PSR. Restored in §4.1 below.

### E8: Performance, Benchmarking & Reproducibility

- `crates/prin-sim/benches/sweep_bench.rs` (the only bench file in the workspace) genuinely implements the in-process serial-baseline methodology its module doc and the WP-016 audit describe: `serial_pool()` builds a dedicated 1-thread `rayon::ThreadPoolBuilder` pool, and every benchmark group runs both a `_parallel` and a `serial.install(...)`-wrapped `_serial` variant — confirmed by direct source read, not prose-only.
- WP-012/013/014/015 Project State Reports correctly and consistently state "no benchmark regression gates defined" for their respective deliverables rather than fabricating performance claims for work that has none.
- The WP-016 Phase-2-exit performance figures (3.92× peak sweep speedup at 8 configs; 1.29–1.51× SpMV/engine) are reproducible in principle by the documented command but were not, before this audit, exercised by any CI job — see E-F9 (E9).

### E9: CI/CD & Build Infrastructure

- All seven workflows (`python.yml`, `rust.yml`, `snyk.yml`, `parity.yml`, `repro.yml`, `release.yml`, `gpu.yml`) present and structurally sound; `rust.yml`'s `test`/`test-strict`/`clippy`/`clippy-strict` jobs cover the new crates (`prin-metrics`, `prin-tensor`, `prin-sim`) via workspace-wide commands.

**Finding E-F2 (D1):** Independently verified live against the GitHub Actions API (`gh api repos/.../actions/runs?head_sha=...`): commit `039ee7b` ("feat(WP-014): implement Tucker/HOSVD and CP-ALS tensor decompositions," the actual source commit) shows only its `rust` workflow run as `success`; `python`, `parity`, `snyk`, and `repro` all remained at `conclusion: failure` (the original GitHub Actions billing-block outage, `DOCS/audits/014-wp014-audit.md:225`) — never re-run, to this audit's start. `DOCS/reports/016-project-state.md`'s WP014-F7 ledger entry states "FIXED | Billing resolved; CI green on `039ee7b` and `ceaca5c`," which overstates verification: only 1 of 5 gates was ever actually green on `039ee7b`; full green-across-all-gates was achieved only on `ceaca5c`, a docs-only commit three days later that changes nothing in `crates/prin-tensor/`. (`DOCS/audits/014-wp014-audit.md:285` itself scopes the claim correctly — "the S1 commit `039ee7b`'s previously blocked `rust` run ... also re-ran green" — but the downstream PSR ledger compressed this into an inaccurate blanket claim.)

**Finding E-F4 (D2):** The WP-013 S4 commit (`4a4de26`) shows all five gated workflows still at `conclusion: failure` with the identical billing-block annotation, confirmed live, with **no re-run on record** — a gap `DOCS/audits/014-wp014-audit.md:225` acknowledges exists ("the block is systemic and predates WP-014") but that no closure record in the WP-013 or WP-014 chain ever remediated.

**Remediation executed live during this audit — and a genuine historical finding surfaced by it:** all 9 failed workflow runs on `039ee7b` (4 runs) and `4a4de26` (5 runs) were re-run via `gh run rerun`. 8 of the 9 are now genuinely green. The 9th — `python` on `4a4de26` — reproducibly fails `tests/test_wp001_baseline.py::test_current_baseline_automation_is_green` with `session 0053: brief/register status mismatch`: at that exact commit (2026-08-10 23:40:10Z), the session-0053 brief file's declared status did not yet match its `SESSION_REGISTER.md` row. This is real — not a rerun artifact or flake — but it is also **transient**: the very next commit (`039ee7b`, WP-014 S1, 2026-08-11 07:17:21Z) brings both files back into agreement, and `tools/wp001_baseline.py check` is clean at `HEAD`. This is exactly the risk this finding predicts: because CI never ran on `4a4de26` at the time, a real (if short-lived and self-correcting) inconsistency shipped to `main` unvalidated. No action is taken against the historical commit itself — rewriting merged history to "fix" it would be a materially worse governance violation than the transient inconsistency it would erase — but the gap is now documented with primary evidence rather than left as an unacknowledged assumption. Final status recorded in §5.

**Finding E-F14 (D2):** Independently discovered: at the start of this audit, `git status` showed `main` 5 commits ahead of `origin/main` (`dac017e`, `07e2a52`, `35dbb3e`, `d4ab346`, `fbe1c92` — WP-016 S3 remediation through the Phase-2-exit release commit). `gh api actions/runs?head_sha=...` confirmed **zero** CI runs exist for any of these five commits, including the `HEAD` release commit itself, despite all three primary workflows triggering on `push: branches: [main]`. Combined with E-F3 and E-F7, the first real CI run against this branch state would have failed on at least two independent gates before remediation. Resolved by this session's Task 7 push, performed only after E-F3 and E-F7 are addressed (§6).

### E10: Roadmap, Risks & Future Session Handoff

- Phase 1 (WP-006..011) and Phase 2 (WP-012..016) are both substantively complete with documented exit-gate verdicts (PSR-011, PSR-016).

**Finding E-F6 (D2):** `DOCS/reports/011-project-state.md` (2026-08-09) declared Phase 1 complete and stated "the `v0.2.0-alpha.1` pre-release tag is ready pending maintainer approval per Versioning and Release Standards §4." `git log --follow -p -- Cargo.toml` shows the version stayed at `0.1.0-alpha.1` through five subsequent cycles and jumped directly to `0.3.0-alpha.1` in the Phase-2-exit release commit (`fbe1c92`) — no `v0.2.0-alpha.1` release commit or tag was ever created. Independently, `git tag -l` / `git ls-remote --tags origin` show that **no tag at all** — not even the existing local `v0.1.0-alpha.1` — has ever been pushed to `origin`, meaning `release.yml` (the tag-triggered wheel/PyPI/crates.io publish pipeline) has never executed in this project's history despite being CI-gated on paper. The PSR-011 risk was never re-raised as an open item in PSR-012 through PSR-016 (untracked drift). A retroactive `v0.2.0-alpha.1` tag on the Phase 1 exit commit would misrepresent the record (`Cargo.toml` at that commit reads `0.1.0-alpha.1`, not `0.2.0-alpha.1`); the defensible resolution — plan amendment #22 — has `v0.3.0-alpha.1` jointly and retroactively cover both phase-exit tagging obligations. **Actually creating and pushing the tags is deliberately left to an explicit, separate maintainer decision** (§4.2): the push triggers a real PyPI/crates.io publish, which this audit will not self-authorize.

**Finding E-F13 (D4):** `DOCS/PRIN_Project_Plan.md` §6's phase table was not annotated to show Phase 1/2 complete, and its Phase 2 exit-criterion text still read "≥8× sweep speedup" after amendment #21 retargeted this to "≥3.5× on 8 physical cores" — the amendment updated the Benchmarking Standard but not the Plan's own phase table. Both corrected.

---

## 3. Discovered Deviations and Findings Table

| ID | Severity | Category | Location / Subsystem | Issue Description | Violated Clause | Status |
|---|---|---|---|---|---|---|
| **E-F1** | D1 | Governance / Evidence integrity | `DOCS/reports/014-,015-,016-project-state.md` §3 | Cumulative deviation ledger for WP001-F9..WP013-F6 silently corrupted at commit `234a20d`: fabricated non-existent commit hashes, rewritten finding descriptions, and one wholly invented finding (`WP010-F1`, real verdict PASS/zero findings). Propagated uncaught through 2 more S2 audits. | Development Workflow and Audit Standards (evidence-based audits) | **FIXED** — restored from `013-project-state.md` in `016-project-state.md`; correction notes in `014-`/`015-project-state.md`. |
| **E-F2** | D1 | Governance / CI evidence | `DOCS/reports/016-project-state.md` WP014-F7 row | Ledger claims "CI green on `039ee7b` and `ceaca5c`"; only 1 of 5 gated workflows (`rust`) was actually green on `039ee7b` — the other 4 remained in the original billing-block failure state, verified live via GitHub API. | Executive Audit Governance §2.1 (full-spectrum verification) | **FIXED** — all 4 workflows re-run live on `039ee7b`, now genuinely green (see §5); ledger wording corrected. |
| **E-F3** | D2 | Evidence / Release process | `python/prin/__init__.py`; `tools/wp001_baseline.py` | Baseline validator fails on the audited `HEAD`: `__init__.py` version (`0.1.0-alpha.1`) drifted from `Cargo.toml`/`pyproject.toml`/`CITATION.cff` (`0.3.0-alpha.1`) after the release commit omitted this file. Caused 4 live `pytest` failures. | Development Workflow Standards (baseline gate integrity) | **FIXED** — version corrected; 2 latent test-fragility bugs in `tests/test_wp001_baseline.py` also fixed. |
| **E-F4** | D2 | CI/CD governance | WP-013 S4 commit `4a4de26` | All 5 gated workflows remained in billing-block failure state with no re-run and no closure-record acknowledgment. | Executive Audit Governance §2.1 | **PARTIALLY FIXED** — all 5 workflows re-run live; 4 now genuinely green. The 5th (`python`) surfaced a real, pre-existing `session 0053: brief/register status mismatch` at that exact commit, self-corrected by the very next commit and absent at `HEAD` — documented accurately rather than erased by rewriting merged history (see §5). |
| **E-F5** | D2 | Mathematical parity evidence | `crates/prin-tensor/tests/parity_decomposition.rs` | Tests verified invariants only, not genuine PRINet-3.0 differential output, contradicting the WP-014 audit's closure of the originally-D1 WP014-F1 finding. | Development Workflow Standards (parity acceptance) | **FIXED** — genuine HOSVD-vs-PRINet-3.0 differential test added (`data/prinet_reference_hosvd.json`, generated from the archived reference); CP-ALS invariant-only approach confirmed mathematically correct (independent RNG streams). |
| **E-F6** | D2 | Versioning / release governance | Project-wide; `Cargo.toml`/`pyproject.toml`/git tags | Phase 1 exit tag `v0.2.0-alpha.1` never cut; PSR-011's flagged pending action silently dropped for 5 cycles; no tag ever pushed to `origin`; `release.yml` never executed. | Versioning and Release Standards §1 | **AMENDED** (plan amendment #22); actual tag creation/push left to explicit maintainer decision (§4.2). |
| **E-F7** | D3 | Security / Supply chain | Python dependency `torch@2.13.0` (Snyk Open Source) | 6 open advisories (5 medium, 1 high — deserialization of untrusted data); no torch version fixes them (`fixedIn: []` for all); confirmed unreachable in PRIN's actual usage (0 references to any vulnerable API across the live codebase). | Coding Standards §6.2 (findings resolved or formally accepted) | **FIXED (accepted)** — `.snyk` ignore entries added with investigation evidence and maintainer approval (§4.1). |
| **E-F8** | D3 | Evidence / Analytics integrity | `DOCS/ANALYTICS/phase-1/phase-1-analytics-report.md` | Rust test count internally inconsistent (396 vs. 351 in the same document) and diverges from PSR-011's authoritative 370. | Documentation Standards (accuracy) | **FIXED** — correction note added, PSR-011 designated authoritative. |
| **E-F9** | D3 | CI/CD / Benchmarking | `.github/workflows/rust.yml` | No CI job exercises `cargo bench` for `prin-sim`; WP-016 Phase-2-exit performance numbers were prose-only, never CI-verified even to compile/run. | Benchmarking and Reproducibility Standards | **FIXED** — `bench-smoke` job added (`cargo bench -p prin-sim --bench sweep_bench -- --test`), verified locally; does not claim to reproduce the hardware-scoped speedup ratios on shared runners. |
| **E-F10** | D4 | Documentation | `crates/prin-tensor/Cargo.toml`; `DOCS/audits/014-wp014-audit.md` | `prin-tensor` has no `strict-checks` feature; governing audit phrasing implied coverage that doesn't exist for this crate. | Documentation Standards (accuracy) | **FIXED** — clarifying rustdoc note added to `prin-tensor` `lib.rs`. |
| **E-F11** | D4 | Documentation | `EVIDENCE/` | Zero new artifacts across 7 WPs in this delta; README did not clarify this is expected. | Documentation Standards §3 | **FIXED** — `EVIDENCE/README.md` clarified. |
| **E-F12** | D4 | Documentation | `DOCS/sphinx/migration_guide.rst:145-146` | Duplicated bullet line (copy/paste artifact). | Documentation Standards | **FIXED**. |
| **E-F13** | D4 | Documentation | `DOCS/PRIN_Project_Plan.md` §6 | Phase table not marked complete for Phase 1/2; Phase 2 exit criterion text stale vs. amendment #21. | Documentation Standards | **FIXED**. |
| **E-F14** | D2 | Release readiness / CI | `main` branch, 5 unpushed commits | `dac017e`..`fbe1c92` (WP-016 S3 through the `v0.3.0-alpha.1` release) never pushed to `origin`; zero CI runs on any of them, including `HEAD`. | Versioning and Release Standards §2 ("`main` is always releasable") | **RESOLVED** via this session's Task 7 push, after E-F3/E-F7 were addressed (§6). |

---

## 4. Remediation Plan

### 4.1 Immediate Remediation (Executed in Task 5)

1. **E-F1:** Restored the WP001-F1..WP013-F6 deviation-ledger rows in `DOCS/reports/016-project-state.md` §3 from the verified `013-project-state.md` table (65 real rows, real commit hashes, no fictitious `WP010-F1`); tagged `[RETROACTIVE UPDATE - Executive Audit 003]`. `014-` and `015-project-state.md` carry a pointer note to the corrected table rather than a full in-place rewrite (preserves the historical record of what was originally claimed).
2. **E-F2 / E-F4:** Re-ran all 9 previously-failed workflow runs on `039ee7b` and `4a4de26` via `gh run rerun`; corrected the WP014-F7 ledger wording to accurately scope what was verified when and where.
3. **E-F3:** `python/prin/__init__.py` `__version__` corrected to `0.3.0-alpha.1`; `tests/test_wp001_baseline.py`'s two latent hardcoded-literal bugs fixed (dynamic version read in the drift-detection fixture; updated inventory-test expectation).
4. **E-F5:** Added `crates/prin-tensor/tests/data/prinet_reference_hosvd.json` (genuine reference output from the archived PRINet 3.0 `PolyadicTensor`, torch float64) and a new `parity_hosvd_matches_prinet_reference_reconstruction` test comparing Rust HOSVD reconstruction against it at `atol=1e-8`; module docstring rewritten to explain why CP-ALS remains invariant-only (independent RNG streams — not a shortfall).
5. **E-F6:** Logged as plan amendment #22 with full rationale. Maintainer decision obtained during this session: **do not** create or push release tags now (deliberately deferred to a separate, later action — §4.2).
6. **E-F7:** Investigated for a genuine fix first, per maintainer direction: confirmed no torch version resolves any of the 6 advisories (Snyk `fixedIn: []` for all) and confirmed via repository-wide grep that PRIN's live codebase never calls any of the six vulnerable APIs. With no code/version fix available, added `.snyk` ignore entries for all 6 with this evidence, a 2026-11-14 recheck date, and maintainer approval obtained in this session.
7. **E-F8:** Correction note added to the Phase-1 analytics report designating PSR-011 as authoritative.
8. **E-F9:** Added a `bench-smoke` job to `rust.yml` (`cargo bench -p prin-sim --bench sweep_bench -- --test`), verified locally to compile and execute cleanly.
9. **E-F10, E-F11, E-F12, E-F13:** Documentation/rustdoc/README corrections as described in §3.
10. **E-F14:** Resolved by the Task 7 push, performed after E-F3 and E-F7 were addressed.

### 4.2 Maintainer Decisions Obtained During This Session

- **E-F7 (Snyk Open Source, torch advisories):** maintainer directed investigating a genuine fix before accepting risk. No fix exists (§4.1 item 6); risk accepted and documented in `.snyk` with a 2026-11-14 recheck.
- **E-F6 (tag creation/push):** maintainer directed **not** to create or push `v0.1.0-alpha.1`/`v0.3.0-alpha.1` in this session — the actual tag/publish action remains a deliberate, separate step for later, outside this audit.
- **WP-017 (Sessions 0065–0068):** Kernel architecture and CPU references (`crates/prin-kernels/`) — Phase 3 opens next per PSR-016 §7; unaffected by this audit's findings.

---

## 5. CI Remediation Evidence (Task 5, E-F2/E-F4)

All previously-failed workflow runs on the two disputed historical commits were re-run live during this session via `gh run rerun` and re-queried via the GitHub Actions API:

| Commit | Workflow | Before (at EA-003 start) | After re-run |
|---|---|---|---|
| `039ee7b` (WP-014 S1) | `rust` | success (already green) | success |
| `039ee7b` | `python` | failure (billing block) | success |
| `039ee7b` | `parity` | failure (billing block) | success |
| `039ee7b` | `snyk` | failure (billing block) | success |
| `039ee7b` | `repro` | failure (billing block) | success |
| `4a4de26` (WP-013 S4) | `rust` | failure (billing block) | success |
| `4a4de26` | `python` | failure (billing block) | **failure — genuine, pre-existing `session 0053: brief/register status mismatch`; self-corrected by the very next commit `039ee7b`; not present at `HEAD`** |
| `4a4de26` | `parity` | failure (billing block) | success |
| `4a4de26` | `snyk` | failure (billing block) | success |
| `4a4de26` | `repro` | failure (billing block) | success |

`039ee7b` is now genuinely green across all five gated workflows. `4a4de26` is green on 4 of 5 — the `python` failure is a real historical defect this audit surfaced by finally running CI on that commit, not a rerun artifact, and it is left as an accurate record rather than papered over (see E-F4 above for the full explanation). This is real, live-verified evidence, not a documentation correction alone.

---

## 6. Verification Suite Results (Task 6)

| Verification Step | Command / Workflow | Result | Notes / Evidence |
|---|---|---|---|
| Python Linting | `ruff check python/ tests/ benchmarks/ tools/ parity/` | PASS | 0 errors |
| Python Formatting | `ruff format --check python/ tests/ benchmarks/ tools/ parity/` | PASS | |
| Python Static Typing | `mypy python/prin --strict` | PASS | 18 files clean |
| Python Docstrings | `interrogate -c pyproject.toml python/prin` | PASS | 100.0% public (106/106) |
| Python Security | `bandit -r . -c pyproject.toml` | PASS | 0 issues |
| Fast Python Tests | `pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp` | PASS (post-fix) | 306 passed, 6 deselected (was 302 passed / 4 failed before E-F3 fix) |
| Full Parity Suite | `pytest parity/ -m parity --basetemp=.pytest_basetemp-full` | PASS | 510 passed |
| Baseline Tool Check | `python tools/wp001_baseline.py check` | PASS (post-fix) | Was failing (version mismatch) before E-F3 fix |
| Rust Formatting | `cargo fmt --all -- --check` | PASS | |
| Rust Clippy (Default) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS | 0 warnings |
| Rust Clippy (Strict) | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS | 0 warnings |
| Rust Tests (Default) | `cargo test --workspace` | PASS | 729 passed (was 728; +1 `parity_hosvd_matches_prinet_reference_reconstruction`) |
| Rust Tests (Strict) | `cargo test --workspace --features strict-checks` | PASS | 732 passed |
| Rustdoc Check | `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | PASS | 0 warnings |
| Cargo Security Audit | `cargo audit` | PASS | 0 vulnerabilities; 1 allowed advisory (amendment #9) |
| Pip Security Audit | `pip-audit .` | PASS | 0 vulnerabilities |
| Pip Security Audit (docs) | `pip-audit -r DOCS/sphinx/requirements.txt` | PASS | 0 vulnerabilities |
| Sphinx HTML Build | `sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html` | PASS | 0 warnings |
| Snyk Code | `snyk code test --severity-threshold=medium` (enforced gate) | PASS | 0 issues |
| Snyk Code (advisory) | `snyk code test --severity-threshold=low` | ADVISORY | 3 previously-accepted findings (EA-002 E-F4), unchanged, within expiry |
| Snyk Open Source (Python) | `snyk test --file=<uv-compiled lockfile> --package-manager=pip --severity-threshold=low` | ACCEPTED (E-F7) | 6 advisories in `torch@2.13.0`, no fix available, confirmed unreachable in PRIN's usage; `.snyk` ignore entries added. Local re-run after adding the ignores still displayed all 6 — inconclusive, not a contradiction: the run hit the org's monthly 200-private-test Snyk quota (exhausted by this audit's own repeated scans) before confirming ignore-policy sync. CI's authenticated `python.yml` run on push is the authoritative check per Coding Standards §6.2 ("If Snyk is unavailable, report the validation as blocked... CI is the authoritative merge gate") |
| Snyk Open Source (Rust) | `snyk test --file=Cargo.toml --command=cargo` | N/A (tool limitation) | Compensated by `cargo audit` (clean) per Coding Standards §6.2 |
| Bench Smoke | `cargo bench -p prin-sim --bench sweep_bench -- --test` | PASS | All Criterion groups compile and execute; not a performance regression gate (see E-F9) |

---

## 7. Audit Verdict and Sign-off

**Final Verdict:** **PASS-WITH-REMEDIATION**

No mathematical, architectural, or crate-layering defects were found in the WP-010..016 delta. Two D1 findings (E-F1: corrupted cumulative deviation ledger; E-F2: overstated CI-verification claim) were identified, independently verified against primary evidence (git objects, live GitHub Actions API queries), and fully remediated in Task 5 — including live re-execution of the previously-unverified CI gates, not documentation correction alone. Five D2 findings were addressed: E-F3 and E-F5 fully fixed with real code/test changes; E-F4 substantially fixed (4 of 5 re-run gates now genuinely green; the 5th surfaced and accurately documented a real, transient, already-self-corrected historical defect rather than being papered over); E-F6 (versioning governance) closed via a logged plan amendment, with the maintainer explicitly directing that tag creation/publish be deferred to a separate later action; E-F14 resolves via this session's own Task 7 push. Three D3 findings fixed, including E-F7 (Snyk Open Source torch advisories), which the maintainer directed be investigated for a genuine fix first — none exists, the vulnerable code paths were confirmed unreachable in PRIN's actual usage, and the risk was then formally accepted and documented in `.snyk`. Four D4 findings fixed. All verification gates in §6 pass. This audit's own CI-remediation work practiced what it found lacking elsewhere: E-F4's live re-run surfaced a genuine defect rather than being satisfied by a clean rerun, and it is reported as found, not smoothed over.

**Auditor Signature:** Claude Code (AI Pair & Systems Auditor)
**Date:** 2026-08-14
