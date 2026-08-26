# Session 0129 — WP-033 S1 handoff

**Date:** 2026-08-26
**Session:** 0129 — WP-033 S1
**Status:** S1 delivered; handoff to mandatory S2 audit (session 0130)
**Predecessor:** WP-032 S4 at PSR-032 (Phase 5 exit gate GREEN)

## Mission and entry conditions

Mission: implement `benchrunner` CLI, shared configuration/environment
capture, and migrate legacy benchmark scripts into nine topic categories
without schema changes.

Entry conditions were met:

- WP-032 S4 is closed and committed; PSR-032 records Phase 5 exit gate GREEN
  and no unresolved D1/D2 finding.
- The DV-019/R28 hard gate (`Hotfix-DV019`, `DOCS/experiments/hotfix-dv019-
  handoff.md`) closed 2026-08-26, satisfying the session brief's retroactive
  precondition.
- The maintainer directly requested execution of this session, matching this
  project's established in-session-approval precedent for the pending
  WP-033 declaration (PSR-032 §6).

## Scope decisions

1. **Verified script count is 58, not 62.** The session brief's Mission and
   the Rebuild Planning Document both say 62 benchmark scripts. A directory
   listing of the archived PRINet 3.0 source — the repository's actual
   state, not the planning-document figure — gives 58 `.py` scripts,
   excluding `README.md` and `results/`. Recorded as a verified factual
   correction in `DOCS/baselines/wp033_benchmark_traceability.md`, not
   silently reconciled to either number; every one of the 58 scripts present
   has a traceability row. This is a factual correction for the S2
   auditor/maintainer to formally disposition, not a plan-text amendment
   made unilaterally in S1.
2. **Category migration is many-to-one, by design.** Many legacy scripts are
   quarterly "grab bags" spanning several topics; consolidating them onto
   nine shared per-category drivers is the point of this WP. Each script got
   one *primary* category (docstring topic, cross-checked against a
   keyword-frequency ranking over the category vocabulary and, for large
   ambiguous files, their `def`/`class` listing) — see the traceability
   doc's "Category mapping methodology" section for the full method and every
   override decision.
3. **`kernels/` orchestrates `cargo bench`, it does not re-measure in
   Python.** `prin-kernels` has no PyO3 binding surface (verified: no kernel
   class/`step_auto`-style function in `python/prin/_prin_core.pyi`). GPU
   kernel performance is measured exclusively by the existing Rust
   `criterion` benches (`crates/prin-kernels/benches/*.rs`, all already
   present from earlier WPs), per Benchmarking and Reproducibility Standards
   §2.1 ("Rust microbenchmarks use `criterion`") and Coding Standards §1
   ("no numerics in Python"). `benchmarks/kernels/criterion_bridge.py` runs
   `cargo bench -p prin-kernels --features cpu` as a subprocess (absolute
   `cargo` path, argument list, `check=False` + explicit exit-code handling,
   no `shell=True` — Coding Standards §6.1) and republishes each target's
   `estimates.json` under the unified schema; it measures nothing itself.
4. **Every other category is real Rust-backed orchestration, not a stub.**
   `scaling`/`chimera`/`integrators` call `prin.dynamics`/`prin.metrics`
   directly; `mot`/`adversarial` reuse `prin.experiments.adversarial_evaluate_*`
   (already parity-dispositioned in WP-031/WP-032, including its
   deterministic synthetic-sequence generation); `ablations` uses the
   Rust-backed ablation bridges in `prin.nn.ablation`; `training` times
   `prin.train.train_phase_tracker`; `daemon` measures the real native
   `SubconsciousDaemon` (`prin.daemon`) through its Python binding. No
   category module computes a scientific quantity itself.
5. **`ablations` reports Rust-owned state size, not a torch parameter
   count.** Every ablation/baseline tracker class's weights live entirely in
   the Rust bridge — gradients flow through a custom
   `torch.autograd.Function`, not `torch.nn.Parameter` registration — so
   `module.parameters()` is always empty (verified directly: `sum(p.numel()
   for p in PhaseTracker(4).parameters())` is `0`). `rust_state_dict()`'s
   byte length is used instead; this was caught by a failing test during S1,
   not asserted from assumption.
6. **`integrators/` has no legacy predecessor; `training/`'s scope is
   throughput only.** Both limitations are stated explicitly in the
   traceability doc and each package's README rather than invented: no
   PRINet 3.0 script has integrator accuracy/cost as its primary topic
   (these are PRIN-native Phase 2 constructs), and no current Python call
   boundary exposes a HEP-vs-BPTT toggle or the ported SCALR/RIP/SyncGD
   comparison harness for a throughput-style benchmark.
7. **Output-path confinement matches Coding Standards §6.1 literally.**
   `write_result()` validates every destination resolves inside
   `benchmarks/results/`, `DOCS/test_and_benchmark_results/`, or a temp
   directory before writing — enforced by a dedicated `OutputPathError`
   raised from both the shared writer and the CLI.

## Delivered files

| File | Delivery |
|---|---|
| `benchmarks/_common/{config,environment,timing,registry,result}.py` | Shared `BenchmarkConfig`, `capture_environment`, `timed_run` (≥10-iteration rule, warmup exclusion), category/benchmark registry, confined JSON writer. |
| `benchmarks/benchrunner/__main__.py` | `python -m benchmarks.benchrunner` CLI: `--list`, `--category`, `--name`, `--out`, `--iterations`, `--warmup`, `--seed-counter`, `--seed-key`. |
| `benchmarks/{scaling,chimera,mot,ablations,kernels,integrators,training,daemon,adversarial}/*.py` | 10 registered benchmarks across the 9 categories (`scaling` has 2), all Rust-backed. |
| `DOCS/baselines/wp033_benchmark_traceability.md` | All 58 verified legacy scripts, each with a category/new-module/notes row; category→module summary table; the verified-count correction. |
| `benchmarks/README.md`, every category's own `README.md`, `benchmarks/results/README.md` | New/updated directory documentation (Documentation Standards §1.3). |
| `tests/test_benchrunner.py` | 50 tests (49 fast + 1 `slow`-marked real `cargo bench` proof). |
| `tests/README.md`, `DOCS/baselines/README.md` | Updated indices for the new test file and traceability doc. |

## Acceptance-criterion evidence map

### AC1 — Every legacy benchmark has a traceability row and executable replacement

`DOCS/baselines/wp033_benchmark_traceability.md` gives all 58 verified
legacy scripts one row each: 56 map to one of the 10 registered benchmarks
(many-to-one, by design — see Scope decision 2); 2
(`y4q2_benchmarks.py`/`y4q4_benchmarks.py`) are recorded as non-benchmark
report/release tooling belonging to a separate future WP, not silently
dropped. Every one of the 10 registered benchmarks is independently proven
executable in `tests/test_benchrunner.py` (`TestSchemaCompatibility`,
`TestRemainingCategories`) at small, fast parameters, plus one full,
real, unmocked `cargo bench -p prin-kernels` subprocess run for `kernels/`
(`TestKernelCriterionBridgeSlow::test_criterion_suite_runs_end_to_end`,
102.64 s, all 4 CPU targets produced real `median_ns`/`mean_ns` values).

Result: **PASS**.

### AC2 — JSON schema compatibility is tested

`TestSchemaCompatibility` asserts the new `scaling`/`chimera`/`adversarial`
payloads keep the field names (and types) of their corresponding archived
legacy JSON (`benchmark_y4q1_ring_scaling.json`'s `N`/`wall_time_s`/
`throughput`/`final_order_param`; `AdversarialEvalResult`'s
`clean_ip`/`adv_ip`/`degradation`, republished as
`clean_identity_preservation`/`adversarial_identity_preservation`/
`degradation`). `write_result()` additionally has a dedicated reserved-key
collision test, and every category payload was manually inspected against
its cited legacy JSON sample during development.

Result: **PASS**.

### AC3 — The ≥10-iteration timing rule is tested

`BenchmarkConfig.__post_init__` and `timed_run()` both independently reject
`iterations < 10` (`TestBenchmarkConfig::test_iterations_below_minimum_raises`,
`TestTimedRun::test_rejects_fewer_than_minimum_iterations`,
`TestBenchrunnerCli::test_iterations_below_minimum_is_an_error`); a
dedicated test confirms warmup calls are executed but excluded from the
returned statistics (`test_warmup_excluded_from_samples`: 3 warmup + 10
measured = 13 total calls, exactly 10 samples returned). The `kernels/`
category maps `config.iterations` onto `criterion`'s own `--sample-size`
(criterion's own floor is also 10), re-checked independently in
`kernel_criterion_suite` rather than trusting only the caller's
`BenchmarkConfig`.

Result: **PASS**.

## Parity-evidence disposition

**No new numerical primitive was introduced.** Every category module is
pure orchestration over already-parity-dispositioned Rust primitives:

- `scaling`/`chimera`/`integrators`: `prin.dynamics`/`prin.metrics`
  (Kuramoto/RK4/RK45/exponential/multi-rate/order-parameter/chimera-index),
  parity-dispositioned in WP-006 through WP-013.
- `mot`/`adversarial`: `prin.experiments.adversarial_evaluate_*`, parity-
  dispositioned in WP-031/WP-032 (FGSM/PGD, deterministic synthetic
  sequences, identity preservation all computed in
  `crates/prin-train/src/adversarial.rs`).
- `ablations`: `prin.nn.ablation` bridges, parity-dispositioned in WP-026/
  Exec-WP-026.
- `training`: `prin.train.train_phase_tracker`, parity-dispositioned in
  WP-027 (IP-threshold acceptance run, `0105-wp027-temporal-clevr-n-
  validation.json`).
- `daemon`: `prin.daemon.SubconsciousDaemon`, parity-dispositioned in
  WP-029/WP-032 (`EVIDENCE/0113-wp029-s1-control-buffer-pilot.json`,
  `EVIDENCE/0125-wp032-s1-daemon-latency.json`).
- `kernels`: republishes `crates/prin-kernels/benches/*.rs`'s own
  `criterion` output; those benches are unchanged and were parity/
  equivalence-dispositioned across WP-017 through WP-021.

The only Python-side arithmetic added is measurement-harness plumbing
(nearest-rank percentile, median over a sample list) in
`benchmarks/_common/timing.py` — the same class of code as the already-
accepted `tools/wp029_control_buffer_pilot.py::_percentile` helper, not a
scientific-model primitive.

## Coverage evidence

```
pytest tests/test_benchrunner.py -m "not slow and not gpu" --cov=benchmarks --cov-report=term-missing
# 49 passed, 1 deselected
# benchmarks/: 607 statements, 1 missed, 99% (the 1 miss is an
#   unreachable-via-public-API `ValueError` guard in
#   scaling/coupling_complexity.py's coupling-mode dispatch helper)
```

This satisfies the ≥95% changed-code gate. `python/prin` (unchanged this
session) remains at 100% per the existing full-suite run below.

## Verification evidence

Commands executed on Windows 11 / Rust 1.92.0 / Python 3.14.0:

```powershell
cargo fmt --all -- --check                                                     # clean (no Rust source changed)
cargo clippy --workspace --all-targets -- -D warnings                          # exit 0
cargo audit                                                                     # exit 0; DV-008/DV-017 only (unchanged)
.venv\Scripts\ruff check benchmarks/ tests/test_benchrunner.py                  # clean
.venv\Scripts\ruff format --check benchmarks/ tests/test_benchrunner.py         # 30 files already formatted
.venv\Scripts\mypy python/prin --strict                                        # 0 issues (python/prin unaffected by this WP)
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin              # 100.0% (266/266)
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml                # 0 issues
.venv\Scripts\python -m pip_audit .                                            # 0 vulnerabilities
.venv\Scripts\python tools/wp001_baseline.py check                             # passed
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin     # 624 passed, 9 deselected; prin 99%
.venv\Scripts\python -m pytest tests/test_benchrunner.py -m slow -v            # 1 passed, 102.64s (real cargo bench)
```

`benchmarks/**` is intentionally outside `mypy --strict`'s and `bandit -r
python/prin`'s scope (Coding Standards §5's local gate targets `python/prin`
only; `pyproject.toml`'s `[tool.ruff.lint.per-file-ignores]` and
`[tool.bandit] exclude_dirs` already carve out `benchmarks/**`/`tests/**`
for `D`/`S` rules and bandit respectively — this predates S1 and was not
changed). `ruff`'s general rules (`E`/`F`/`W`/`I`/`UP`/`B`/`NPY`/`RUF`) are
the applicable gate for this WP's new code and are clean.

## Security evidence

Snyk CLI (not the MCP integration used by some prior sessions — unavailable
this session; the CLI gives equivalent evidence) was run directly:

| Scan | Scope | Result |
|---|---|---|
| Snyk Code | `benchmarks/` | 0 issues |
| Snyk Code | `tests/test_benchrunner.py` | 0 issues |

No dependency/manifest changed (`torch`/`numpy` were already base
dependencies), so no change-attributable Snyk Open Source scan was
required. `cargo audit`/`pip_audit` are clean at their governed thresholds
(§6.2); GitHub secret scanning/push protection status is unchanged from
prior sessions (amendment #5 substitute controls remain authoritative,
re-verified at the next S4 push per the established cadence).

## Out-of-scope discoveries

1. Production-scale campaign runs (N up to 1M for `scaling`, full 5-attack ×
   both-tracker `adversarial` sweeps, multi-hour `training` convergence) are
   explicitly not run this session (Non-goal: "Drawing conclusions from
   final measurements"); every category was validated at small,
   fast, characterization-scale parameters instead. `benchmarks/results/`
   is committed empty (with its own README) rather than seeded with
   placeholder or partial-scale numbers that could be mistaken for
   registered results.
2. The Parity Report comparing legacy PRINet 3.0 numbers against these new
   measurements, and the figure/table-generator work implied by
   `y4q2_benchmarks.py`/`y4q4_benchmarks.py`, are separate Project Plan §6
   Phase 6 deliverables, not this WP's scope.
3. `training/`'s HEP-vs-BPTT toggle and ported SCALR/RIP/SyncGD comparison
   harness (named in the category's own README description) are not yet
   exposed at a Python call boundary this WP can drive without introducing
   new Python-side training-loop logic — recorded as a scope gap for a
   future WP rather than worked around with an invented substitute.
4. `wgpu`/`cuda` `criterion` targets in `crates/prin-kernels/benches/*.rs`
   exist but are not run by `kernels/criterion_suite` (CPU-only, matching
   `rust.yml`'s established `--features cpu` convention); GPU-backed
   targets need the self-hosted runner.

## Handoff to S2

Recommended audit focus:

1. The verified 58-vs-62 script-count correction and its evidence
   (directory listing, single-commit archive history) — confirm it is
   accurately and non-speculatively stated.
2. Every traceability-doc category override (raw keyword rank vs. assigned
   category) against its stated basis.
3. `kernels/criterion_suite`'s subprocess construction (absolute path,
   argument list, no `shell=True`, confined output parsing) against Coding
   Standards §6.1.
4. Whether `ablations`' `state_size_bytes` substitution for a torch
   parameter count is adequately justified and not silently misleading.
5. Coverage-exclusion correctness (the one uncovered line) and whether the
   `mypy`/`bandit` scope carve-out for `benchmarks/**` is pre-existing
   project policy, not something this session weakened.
6. Whether the 4 out-of-scope discoveries above are genuinely out of this
   WP's declared scope, not silently-descoped acceptance-criterion work.
