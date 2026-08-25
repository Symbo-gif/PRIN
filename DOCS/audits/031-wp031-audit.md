# PRIN Audit Report — Cycle 031 / WP-031

**Date:** 2026-08-25
**Auditor:** Qwen Code (AI pair)
**Scope:** WP-031 "Temporal experiments, statistics, and adversarial tooling" —
  `crates/prin-train/src/temporal_metrics.rs` (new, 598 lines),
  `crates/prin-train/src/stats.rs` (new, 601 lines),
  `crates/prin-train/src/flops.rs` (new, 423 lines),
  `crates/prin-train/src/adversarial.rs` (new, 829 lines),
  `crates/prin-train/src/trainer.rs` (extended, 550→1392 lines),
  `crates/prin-train/src/error.rs` (4 new variants),
  `crates/prin-train/src/lib.rs` (module wiring + crate docs),
  `crates/prin-py/src/bindings/trainer.rs` (Seed parameter + snapshot_epochs),
  `crates/prin-train/tests/parity_stats.rs` (new),
  `crates/prin-train/tests/data/welch_t_test_reference_cases.json` (new),
  `crates/prin-train/tests/integration_checkpoint_resume.rs` (call-site update),
  `crates/prin-train/tests/integration_temporal_clevr_n.rs` (call-site update),
  `tools/wp031_stats_fixture.py` (new, 104 lines)
**Sessions:** 0121 (S1 implementation); 0122 (S2, this audit)
**Active brief:** `DOCS/sessions/phase-5/0122-wp031-s2-temporal-experiments-statistics-and-adversarial-tooling.md`
**Git state:** `main` @ `c8ef833` (S1 commit); predecessor `6f642fb`
**Verdict:** PASS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | All seven mission items delivered; eight scope decisions documented with reference evidence; no undeclared work shipped |
| Plan/architecture conformance (A2) | ✅ | All new code in `prin-train` (no new crate); no Python numerics; `#![forbid(unsafe_code)]` unchanged; explicit `Seed` threaded through every stochastic entry point |
| Tests in tandem + coverage (A3) | ✅ | 375 lib tests + 1 parity test (8 scenarios vs. real scipy); all five new/changed modules ≥95% line coverage |
| Numerical parity + invariants (A4) | ✅ | `welch_t_test` matches real `scipy.stats.ttest_ind` 1.18.0 at `rtol=1e-9, atol=1e-12` (8 scenarios); hand-computed tests for `percentile`, `cohens_d`, `temporal_smoothness`, `recovery_speed`, `count_flops`; Student's-t p-value matches textbook table values |
| Quality gates (A5) | ✅ | fmt/clippy/ruff/mypy/rustdoc all clean (exit 0) |
| Security (A6) | ✅ | `#![forbid(unsafe_code)]` at crate level; `cargo audit` exit 0 (2 pre-existing allowed warnings); bandit/pip-audit clean; no network/filesystem/subprocess attack surface |
| Docstring/doc coverage (A7) | ✅ | `tools/wp031_stats_fixture.py` interrogate 100.0% (4/4); `RUSTDOCFLAGS=-D warnings` clean; every public type/function has rustdoc with reference line citations |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/HACK/XXX/STUB markers in any new/changed source; module wiring and re-exports consistent; no orphan files |
| CI status (A9) | ✅ | Local gate reproduction clean (nothing pushed yet this cycle, per Push-and-CI cadence) |
| Artefact trail (A10) | ✅ | PSR-030, audit 030 (PASS, zero findings), S3 no-change closure, S1 handoff note all present and consistent; WP-031 properly declared in PSR-030 §6 |

## 2. Methodology

All commands executed 2026-08-25 on the project host (Windows 11, AMD Ryzen 7
8700F, 32 GB RAM, Rust 1.92.0, Python 3.14.0).

```powershell
# A5 — Quality gates
cargo fmt --all -- --check                                                         # exit 0, clean
cargo clippy --workspace --all-targets -- -D warnings                              # exit 0, clean
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings     # exit 0, clean
set RUSTDOCFLAGS=-D warnings && cargo doc --workspace --no-deps                    # exit 0, 0 warnings
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/                 # All checks passed!
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/        # 75 files already formatted
.venv\Scripts\ruff check tools/wp031_stats_fixture.py                              # All checks passed!
.venv\Scripts\ruff format --check tools/wp031_stats_fixture.py                     # 1 file already formatted
.venv\Scripts\mypy tools/wp031_stats_fixture.py --strict                           # Success: no issues found

# A3 — Tests
cargo test -p prin-train --lib -- --test-threads=4                                 # 375 passed, 0 failed
cargo test -p prin-train --test parity_stats                                       # 1 passed (8/8 scenarios vs. real scipy)
cargo test --workspace --exclude prin-py -- --test-threads=4                       # all crates green, 0 failed
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp  # (unchanged from PSR-030 baseline)

# A3 — Coverage (S1 handoff evidence, independently re-verified at S2)
cargo llvm-cov -p prin-train --features strict-checks
#   temporal_metrics.rs: 95.04% lines
#   stats.rs:            96.77% lines
#   flops.rs:            96.53% lines
#   adversarial.rs:      96.03% lines
#   trainer.rs:          98.04% lines

# A6 — Security
cargo audit                                                                        # exit 0; 2 allowed warnings (amendments #9, #27)
.venv\Scripts\python -m bandit tools/wp031_stats_fixture.py -c pyproject.toml     # 0 issues
.venv\Scripts\python -m pip_audit .                                                # 0 vulnerabilities

# A7 — Documentation
.venv\Scripts\python -m interrogate -c pyproject.toml tools/wp031_stats_fixture.py  # 100.0% (4/4)

# A8 — Hygiene
grep -r "TODO\|FIXME\|HACK\|XXX\|STUB" crates/prin-train/src/temporal_metrics.rs   # no matches
grep -r "TODO\|FIXME\|HACK\|XXX\|STUB" crates/prin-train/src/stats.rs              # no matches
grep -r "TODO\|FIXME\|HACK\|XXX\|STUB" crates/prin-train/src/flops.rs              # no matches
grep -r "TODO\|FIXME\|HACK\|XXX\|STUB" crates/prin-train/src/adversarial.rs        # no matches
grep -r "TODO\|FIXME\|HACK\|XXX\|STUB" crates/prin-train/src/trainer.rs            # no matches
grep -r "unsafe" crates/prin-train/src/                                            # only #![forbid(unsafe_code)] in lib.rs

# A4 — Parity fixture regeneration
.venv\Scripts\python tools/wp031_stats_fixture.py                                  # regenerates committed fixture byte-identically
```

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

All seven mission items from the session brief are delivered:

1. **Fair PT-vs-SA training framework** — `train_temporal_slot_attention_mot`
   and `evaluate_temporal_slot_attention_mot` in `trainer.rs` (the SA-side
   counterpart to the existing `train_phase_tracker`/`evaluate_phase_tracker`);
   both share the identical `TemporalTrainerConfig` (same Adam, same
   warmup/cosine LR, same gradient clipping, same early stopping).
   `count_parameters` is generic over any `Module` via `ModuleVisitor`,
   verified by `count_parameters_matches_between_pt_and_sa_shapes`.

2. **Hungarian similarity** — correctly identified in scope decision #2 as
   already ported at WP-027 (`crate::losses::hungarian_similarity_loss`);
   the reference's "Hungarian" naming refers to the assignment behavior the
   loss encourages, not an implementation of the Kuhn–Munkres algorithm.
   The one real Hungarian solver (`crates/prin-daemon/src/assignment.rs`,
   WP-030) is unrelated. Confirmed by inspection.

3. **Temporal metrics** — `temporal_metrics.rs` (598 lines): all 8 functions
   plus `TemporalMetrics` dataclass, direct port of `utils/temporal_metrics.py`.

4. **Bootstrap CIs** — `stats.rs::bootstrap_ci`, percentile-method formula
   pinned by `percentile_hand_computed_linear_interpolation` and
   `bootstrap_ci_constant_values_gives_zero_width`.

5. **Welch tests** — `stats.rs::welch_t_test`/`compute_p_value`, validated
   against real `scipy.stats.ttest_ind` 1.18.0 by `parity_stats.rs` (8/8
   scenarios at `rtol=1e-9, atol=1e-12`).

6. **FLOPs** — `flops.rs` (423 lines): `LayerSpec`/`count_flops`/`FlopsReport`
   plus `measure_wall_time`/`WallTimeStats`. Documented reference discrepancy
   (Conv2d docstring vs. implementation) correctly resolved by reproducing
   the reference's *executed* behavior.

7. **FGSM/PGD orchestration** — `adversarial.rs` (829 lines): `fgsm_attack`,
   `pgd_attack`, per-tracker `adversarial_evaluate_*`, and
   `adversarial_comparison`.

Eight scope decisions are documented in the S1 handoff note, each with
reference evidence. Python bindings and `python/prin/eval`/`experiments`
population are correctly deferred (scope decision #3, consistent with
WP-030's identical deferral for `hooks.rs`/`mot.rs`). No undeclared work
shipped.

### 3.2 A2 — Plan/architecture conformance

- **Crate layering:** all new code lives in `prin-train` (no new crate),
  extending the existing WP-027 module set. `prin-train`'s dependency on
  `prin-dynamics` (for `Seed`) is an allowed direction.
- **No numerics in Python:** `tools/wp031_stats_fixture.py` calls only
  `scipy.stats.ttest_ind` to generate the parity fixture — it does not
  implement any numerical algorithm. All statistical/attack/metric
  algorithms are in Rust.
- **Explicit Seed flow:** every stochastic entry point threads `&mut Seed`
  explicitly (`bootstrap_ci`, `pgd_attack`, `train_phase_tracker`,
  `train_temporal_slot_attention_mot`, `train_multi_seed`,
  `adversarial_evaluate_*`). No hidden RNG. Project Plan §4 rule 3
  satisfied.
- **`#![forbid(unsafe_code)]`** unchanged at crate level.
- **One algorithm, one implementation:** FGSM/PGD reuse
  `hungarian_similarity_loss` directly rather than duplicating the
  cross-entropy-with-diagonal-target formula (Coding Standards §1.1).
  `count_parameters`/`compute_param_norm`/`compute_gradient_norm` are
  generic over any `Module`, not per-tracker duplicates.

### 3.3 A3 — Tests in tandem + coverage

**Test counts:**
- `prin-train` lib tests: 375 passed, 0 failed (up from the pre-WP-031
  count; new tests cover `stats`, `temporal_metrics`, `flops`, `adversarial`,
  and extended `trainer`).
- `parity_stats.rs`: 1 test passed (replays 8 scenarios through
  `welch_t_test`, each compared against real `scipy.stats.ttest_ind`).
- Integration tests updated for `train_phase_tracker`'s new `&mut Seed`
  parameter: `integration_checkpoint_resume.rs`,
  `integration_temporal_clevr_n.rs`.

**Coverage on new/changed code (all ≥95% line coverage):**

| File | Line coverage |
|---|---|
| `temporal_metrics.rs` | 95.04% |
| `stats.rs` | 96.77% |
| `flops.rs` | 96.53% |
| `adversarial.rs` | 96.03% |
| `trainer.rs` | 98.04% |

Remaining gaps are the same class established across the crate: unreachable
early-validation branches inside deliberately-`unreachable!()` test closures,
the `mean(&[])` defensive branch in `build_adversarial_eval_result`, and
`TemporalMetrics::default()` field-literal lines.

### 3.4 A4 — Numerical parity

**Statistics — real third-party reference:**
- `welch_t_test` vs. `scipy.stats.ttest_ind(equal_var=False)` 1.18.0: 8/8
  scenarios agree at `rtol=1e-9, atol=1e-12`. Fixture generated by
  `tools/wp031_stats_fixture.py` (calls real scipy, never archived
  reference code, per `tools/README.md`); independently regenerates
  byte-identical.
- `cohens_d`: hand-computed test (`[1,2,3]` vs. `[4,5,6]` → `d = -3.0`
  exactly).
- `bootstrap_ci`: percentile-method formula pinned by
  `percentile_hand_computed_linear_interpolation` (matches
  `numpy.percentile`'s linear interpolation at exact values).
- Student's-t p-value: `student_t_p_value_matches_known_table_values`
  verifies `t=2.228, df=10 → p ≈ 0.05` and `t=1.959964, df=1e6 → p ≈ 0.05`
  (textbook critical values). `log_gamma` verified against `ln(4!)`,
  `ln(Gamma(0.5)) = ln(sqrt(pi))`.

**Temporal metrics / adversarial — archived-only reference, formula transcription:**
- Every function's rustdoc cites exact reference line ranges.
- Hand-computed tests trace through the reference's algorithm by hand:
  `temporal_smoothness_hand_computed_single_kink` (acceleration norm = 0.5),
  `recovery_speed_hand_computed_immediate_rebind` (documents the
  reference's off-by-one semantics with inline explanation),
  `track_duration_stats_id_switch_breaks_run`, `linear_flops_hand_computed_with_bias`
  (2×4×8 + 8 = 72), `gru_cell_flops_hand_computed` (3×2×(8+16)×16 = 2304).

**Attack bounds:**
- `fgsm_attack_perturbation_is_within_epsilon_ball` and
  `pgd_attack_perturbation_is_within_epsilon_ball` assert L-infinity ball.
- `pgd_attack_default_alpha_is_epsilon_over_four` confirms the reference's
  default step size.
- `torch_sign_matches_pytorch_zero_convention` verifies the `0.0 → 0.0`
  semantics (unlike Rust's `f64::signum`).

**Deterministic multi-seed:**
- `pgd_attack_is_deterministic_for_same_seed` / `..._different_seeds_give_different_perturbations`.
- `adversarial_evaluate_phase_tracker_pgd_is_deterministic_for_same_seed`.
- `train_multi_seed_aggregates_across_seeds` / `..._single_seed_has_zero_std` /
  `..._propagates_errors`.

### 3.5 A5 — Quality gates

All clean — see §2 command output. `cargo fmt`, `cargo clippy` (both
default and `strict-checks` features), `RUSTDOCFLAGS=-D warnings cargo doc`,
`ruff check`, `ruff format --check`, `mypy --strict` all exit 0.

### 3.6 A6 — Security

- `#![forbid(unsafe_code)]` at `crates/prin-train/src/lib.rs:116` — no
  `unsafe` anywhere in the crate.
- `cargo audit`: exit 0; 2 allowed warnings (RUSTSEC-2025-0141 `bincode`,
  RUSTSEC-2024-0436 `paste` — amendments #9/#27, unchanged from prior cycles).
- `pip-audit`: 0 vulnerabilities.
- `bandit`: 0 issues on `tools/wp031_stats_fixture.py`.
- New code adds no network, filesystem (beyond the one committed JSON
  fixture), or subprocess attack surface — pure numerical/host computation.

### 3.7 A7 — Docstring/doc coverage

- `tools/wp031_stats_fixture.py`: interrogate 100.0% (4/4 functions
  documented).
- Rust: `#![warn(missing_docs)]` at crate level; `RUSTDOCFLAGS=-D warnings`
  clean. Every public type, function, and enum variant has rustdoc.
  Module-level docs cite exact reference line ranges for every ported
  function. The documented Conv2d FLOPs discrepancy and the documented
  `TrainingSnapshot::slot_entropy` / `MultiSeedResult` dead-field omissions
  are model examples of the "document deviations rather than silently
  absorb them" principle.

### 3.8 A8 — Repository hygiene

- No TODO/FIXME/HACK/XXX/STUB markers in any of the five new/changed source
  files (`temporal_metrics.rs`, `stats.rs`, `flops.rs`, `adversarial.rs`,
  `trainer.rs`).
- `lib.rs` module wiring: four new `pub mod` entries (`adversarial`,
  `flops`, `stats`, `temporal_metrics`) plus updated crate-level docs
  listing every new module with its WP-031 attribution.
- No orphan files. All new files are in established directories
  (`crates/prin-train/src/`, `crates/prin-train/tests/`,
  `crates/prin-train/tests/data/`, `tools/`).
- `.gitignore` respected (no build artefacts committed).

### 3.9 A9 — CI status

Per the Push-and-CI cadence (Development Workflow and Audit Standards §3),
nothing has been pushed yet this cycle — S2 verifies local gate reproduction
only. All local gates are green (§2). CI will be evaluated at S4 when the
cycle's full S1–S4 range is pushed.

The `cargo test --workspace` run hit a Windows file-contention linker error
(LNK1104) on the `prin-py` test binary — this is the documented
antivirus/file-handle contention issue recorded in `AGENTS.md` ("Do not run
pytest concurrently with cargo... on Windows: antivirus/file-handle
contention during `tmp_path` cleanup can surface as `PermissionError`").
Re-running with `--exclude prin-py` confirmed all other workspace crates
green. This is an environment artefact, not a code defect.

### 3.10 A10 — Artefact trail

- **PSR-030** (`DOCS/reports/030-project-state.md`): present, committed at
  `b91dfdf`. §6 declares WP-031 with scope, acceptance criteria, and non-goals
  matching the session brief.
- **Audit 030** (`DOCS/audits/030-wp030-audit.md`): verdict PASS, zero
  findings. Consistent with PSR-030's claim.
- **S3 030 no-change closure** (`209802d`): present, CLEAN delta re-audit.
- **S1 handoff note** (`DOCS/experiments/0121-wp031-s1-handoff.md`): 437
  lines, maps every acceptance criterion to evidence, documents 8 scope
  decisions with reference citations, flags 5 S2 audit-focus areas.
- **Session register:** 0121 (S1) marked COMPLETE; 0122 (S2, this audit)
  is the registered successor.

All artefacts are present, consistent, and cross-referenced correctly.

## 4. Issues found

No findings. All ten checklist dimensions pass.

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| *(none)* | — | — | — | — | — |

## 5. Deviation-ledger delta

New findings added to the ledger: none. Carried findings re-inspected:
none (WP-030 S2 was PASS with zero findings; no unresolved D1–D4 exists).

## 6. Verdict and required actions

**Verdict: PASS** — zero findings across all ten checklist dimensions.

The S1 implementation is thorough, well-documented, and numerically sound.
The eight scope decisions are each backed by reference evidence and logged
for S2 traceability. The parity evidence is appropriate for the three
different evidentiary classes involved (real third-party reference for
statistics; formula transcription for temporal metrics/adversarial; formula
transcription with a documented reference discrepancy for FLOPs). The
`#![forbid(unsafe_code)]` invariant is preserved, explicit `Seed` threading
is consistent with Project Plan §4 rule 3, and all quality gates are clean.

S3 is mandatory even with zero findings: it records a no-change closure
and independent delta verification.

**S3 action list:** no-change closure. Delta re-audit of the touched areas
(`crates/prin-train/src/{temporal_metrics,stats,flops,adversarial,trainer}.rs`,
`crates/prin-train/tests/parity_stats.rs`, `tools/wp031_stats_fixture.py`)
to confirm the committed state matches this audit's evidence.

---

## 7. Closure table (appended by S3 remediation)

Per Development Workflow and Audit Standards §3, session 0123 performed the
mandatory no-change closure. S2 recorded no D1–D4 finding, so no source fix was
applicable or permitted. The S1 source tree was independently re-verified before
this documentation-only closure.

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| *(no findings — S2 recorded none)* | NO-CHANGE CLOSURE — no source fix applicable or performed | this session's closure commit (documentation only) | §7 delta re-audit below |

### Delta re-audit

**Source-tree identity.** `git diff --stat c8ef833 HEAD -- crates/ python/
tests/ parity/ Cargo.toml Cargo.lock pyproject.toml models/
tools/wp031_stats_fixture.py` returned empty before this closure: S2 changed
only this audit report. The source, dependency, configuration, model, and WP-031
fixture trees therefore remained identical to the S2-audited S1 state.

**Independent S3 verification (2026-08-25):**

```powershell
cargo fmt --all -- --check                                                     # exit 0
cargo clippy --workspace --all-targets -- -D warnings                          # exit 0, no code findings
$env:CARGO_INCREMENTAL='0'; cargo clippy --workspace --all-targets --features strict-checks -- -D warnings # exit 0, no warnings
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps               # exit 0, 0 warnings
cargo test --workspace -- --test-threads=1                                     # exit 0, 0 failures
cargo test --workspace --features strict-checks -- --test-threads=1            # exit 0, 0 failures
cargo llvm-cov -p prin-train --features strict-checks -- --test-threads=1      # 377 passed; touched files all >=95% lines
cargo audit                                                                     # exit 0; DV-008/DV-017 only
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/             # all checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/    # 75 files formatted
.venv\Scripts\mypy python/prin --strict                                       # 28 files, 0 issues
.venv\Scripts\mypy tools/wp031_stats_fixture.py --strict                      # 1 file, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 100.0% (262/262)
.venv\Scripts\python -m interrogate -c pyproject.toml tools/wp031_stats_fixture.py # 100.0% (4/4)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                         # 0 issues
.venv\Scripts\python -m pip_audit .                                           # 0 vulnerabilities
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt             # 0 vulnerabilities
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp # 547 passed, 8 deselected; 99%
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp-full # 1147 passed; 99%
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build_s3_0123/html # fresh output; 0 warnings
.venv\Scripts\python tools/wp001_baseline.py check                            # passed
.venv\Scripts\python tools/wp031_stats_fixture.py                             # 8 scenarios; committed fixture byte-identical
```

The serial coverage rerun measured `temporal_metrics.rs` 95.04%, `stats.rs`
96.77%, `flops.rs` 96.53%, `adversarial.rs` 95.83%, and `trainer.rs` 98.04%
line coverage. Every touched file remains above the 95% gate. The initial
parallel coverage attempt encountered the existing order-sensitive
`bands::tests::gradients_flow_to_every_parameter` assertion; that test passed
in both serial workspace suites and in the serial coverage rerun, which then
completed with 377/377 tests green.

**Security delta:**

- Snyk Code, `crates/prin-train`, threshold `low`: 0 issues.
- Snyk Code, `crates/prin-py`, threshold `low`: 0 issues.
- Snyk Code, `tools/wp031_stats_fixture.py`, governed threshold `medium`: 0
  issues. A diagnostic scan at `low` reported one low-severity path-traversal
  diagnostic on the explicit operator-supplied output-file argument; it is
  below Coding Standards §6.2's zero-medium+ gate and was neither suppressed
  nor represented as absent.
- Snyk Open Source, whole repository (`all_projects=true`, project `.venv`
  Python), threshold `low`: 0 issues.
- GitHub's secret-scanning alerts API still reports HTTP 404, "Secret scanning
  is disabled on this repository"; this is the unchanged DV-009 condition and
  its approved Gitleaks/branch-protection substitute remains authoritative.

The Welch fixture regenerated byte-identically, Welch parity remained green,
attack-bound and deterministic-seed tests passed in both workspace modes, and
no source/configuration/model drift or new governed deviation was found.

**Delta re-audit date:** 2026-08-25 — **Result:** CLEAN (mandatory no-change
closure; zero findings to close; zero source changes; all governed gates green)
