# Session 0133 — WP-034 S1 handoff

**Date:** 2026-08-26
**Session:** 0133 — WP-034 S1
**Status:** S1 delivered; handoff to mandatory S2 audit (session 0134)
**Predecessor:** WP-033 S4 at PSR-033

## Mission and entry conditions

Mission: port benchmark reports/leaderboards, publication figures and LaTeX
fragments, and torch/Rust profiling integration without re-running scientific
training.

Entry conditions were met:

- WP-033 S4 is closed and committed; PSR-033 records a clean delta re-audit and
  no unresolved D1/D2 finding.
- The maintainer directly requested execution of session 0133, providing the
  approval that PSR-033 §6 recorded as pending for the already-declared scope,
  acceptance criteria, and non-goals.

## Scope decisions

1. **The verified PRINet 3.0 reference contains 14 generated figures, not 15.**
   `figure_generation.py` implements and `generate_all_figures()` registers
   figures 2 through 15. There is no `fig1` implementation or stored `fig1`
   output in either historical `figures/` tree. This implementation therefore
   ports all 14 verifiable generators and records the session brief's count as
   a factual discrepancy for S2 disposition rather than inventing an artefact.
2. **All 11 historical LaTeX fragments are byte-comparable.** The stored 3.0
   JSON artefacts regenerate every fragment with bytes identical to the stored
   files under the historical `paper/tables/` tree, including LF normalization.
3. **Matplotlib outputs use documented deterministic normalization.** PNG
   comparison retains image-defining chunks and discards ancillary metadata;
   PDF generation fixes dates/producer metadata and normalization masks backend
   object identifiers and dates. Repeated generation is byte-identical after
   this normalization. This avoids claiming raw cross-version matplotlib bytes
   are portable when font/backend metadata can differ.
4. **Report timestamps are explicit.** Report and leaderboard output omits a
   timestamp by default. A caller-supplied aware `datetime` is normalized to
   UTC minute precision; an explicit stored provenance string is preserved.
   Unchanged inputs therefore produce unchanged report bytes.
5. **Profiling exposes an explicit Rust-call trace boundary.** A caller wraps a
   Python-to-Rust operation with `PRINetProfiler.record_function(label)`, which
   delegates to `torch.profiler.record_function`; the label is present in key
   averages and Chrome traces. The reporting package introduces no numerical
   model implementation or hidden randomness.
6. **Writes follow current security policy, not historical output defaults.**
   Reports, figures, tables, and profiler traces are confined to
   `benchmarks/results/`, `DOCS/test_and_benchmark_results/`, or the operating-
   system temporary tree. Historical `paper/` paths are read-only parity
   references, not active output defaults.

## Delivered files

| File | Delivery |
|---|---|
| `python/prin/reporting/benchmark_reporting.py` | Deterministic Markdown benchmark reports, leaderboards, SCALR summaries, typed validation/errors, Markdown escaping, and confined writes. |
| `python/prin/reporting/figure_generation.py` | Fourteen stored-artefact figure generators, headless 300-DPI style, typed artefact/schema/output errors, deterministic PDF/PNG normalization, and master generation. |
| `python/prin/reporting/table_generation.py` | Eleven byte-comparable LaTeX fragment generators and master generation. |
| `python/prin/reporting/profiler.py` | Typed `torch.profiler` wrapper, legacy `ProfileReport`, Chrome trace export, training-loop helper, and explicit Rust-backed operation labels. |
| `python/prin/reporting/__init__.py` | Public reporting API exports. |
| `tests/test_reporting_profiler.py` | 59 report, leaderboard, SCALR, profiler lifecycle, trace, validation, and training-loop tests. |
| `tests/test_publication_generation.py` | 11 tests covering all 14 figure generators, all 11 table generators, stored 3.0 artefacts, exact table bytes, deterministic normalization, schema errors, and output confinement. |

## Acceptance-criterion evidence map

### AC1 — Stored 3.0 artefacts generate expected outputs

`test_stored_3_0_artefacts_regenerate_all_outputs` points the new generators at
the repository's stored PRINet 3.0 JSON artefacts. It generates all 14
verifiable figures in both PDF and PNG (28 files) and all 11 LaTeX fragments.
Every generated table is byte-compared against its stored 3.0 counterpart.
`test_repeat_figure_generation_has_deterministic_normalized_bytes` proves the
documented PDF/PNG normalization is stable across repeated generation.

Result: **PASS**, with the 14-vs-15 factual discrepancy explicitly handed to
S2.

### AC2 — Reports and leaderboards preserve stored schemas deterministically

Reporting tests cover the legacy top-level status/metric fields, nested
`benchmarks`, CLEVR-N per-model rows, OscilloBench rows, malformed artefact
isolation, deterministic ordering/tie-breaking, explicit UTC timestamp
normalization, Markdown escaping, and confined output paths.

Result: **PASS**.

### AC3 — Examples and schema tests pass

All public figure/table APIs have typed Google-style docstrings. Module doctests
pass. Schema tests prove missing required keys, malformed JSON, non-object JSON,
missing artefacts, invalid public inputs, profiler state errors, and output-path
escapes fail loudly through typed errors.

Result: **PASS**.

### AC4 — Torch/Rust profiling integration is present

`PRINetProfiler` integrates torch CPU/CUDA profiler activities, scheduled warmup
and active steps, key averages, device timing, and Chrome trace export.
`test_profiles_and_labels_rust_backed_operation` verifies an explicit
`prin::rust_backed_step` label is reported. `profile_training_loop` covers
forward and optional backward execution without sampling data or mutating RNG
state.

Result: **PASS**.

## Parity-evidence disposition

Directly comparable PRINet 3.0 reference modules and stored outputs exist for
all delivered behavior:

- `utils/benchmark_reporting.py`
- `utils/figure_generation.py`
- `utils/table_generation.py`
- `utils/profiler.py`
- `benchmarks/results/*.json`
- `paper/figures/fig2` through `fig15`
- `paper/tables/tab_*.tex`

The implementation ports their reporting/rendering/profiling contracts while
applying current typed-validation, deterministic-output, and output-confinement
standards. No numerical primitive, kernel, optimizer, stochastic process, or
scientific result was introduced or recomputed. Therefore numerical parity,
gradcheck, property, and kernel-equivalence tests are not applicable to this
WP's changed behavior; stored-artefact and exact/normalized output comparisons
are the applicable golden evidence.

## Coverage evidence

```powershell
.venv\Scripts\python -m pytest tests/test_reporting_profiler.py tests/test_publication_generation.py --cov=prin.reporting --cov-report=term-missing --basetemp=.pytest_basetemp-wp034
# 70 passed; prin.reporting 99% (1,044 statements, 13 missed)
```

Changed-module coverage is 98–100%, satisfying the ≥95% gate.

## Verification evidence

Commands executed on Windows 11 / Rust 1.92.0 / Python 3.14.0:

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/             # clean
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/    # 125 files formatted
.venv\Scripts\mypy python/prin --strict                                       # 32 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 95.6%, PASS
.venv\Scripts\python -m doctest python/prin/reporting/figure_generation.py python/prin/reporting/table_generation.py  # exit 0
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp  # 694 passed, 9 deselected; prin 99%
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp-full  # 1295 passed; prin 99%
cargo fmt --all -- --check                                                     # clean
cargo clippy --workspace --all-targets -- -D warnings                          # clean
$env:CARGO_INCREMENTAL='0'; cargo test --workspace --quiet                     # all test binaries/doctests passed; 1 established expensive test ignored
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps               # clean
```

A redundant immediate Rust re-run first encountered the documented Windows
`LNK1104` antivirus/file-handle condition. The isolated retry after a handle-
release pause passed completely; no source change was required.

## Security evidence

| Scan | Scope | Threshold/result |
|---|---|---|
| Snyk Code | `python/prin/reporting/` | Low; 0 issues |
| Snyk Code | `tests/test_reporting_profiler.py` | Low; 0 issues |
| Snyk Code | `tests/test_publication_generation.py` | Low; 0 issues |
| Bandit | `python/prin` | 0 issues |
| Bandit defense-in-depth | Whole repository | Two pre-existing Low `assert` findings in `EVIDENCE/math-audit/manual/mf9-beta-allowlist-verification.py`; no changed-file finding |
| `cargo audit` | `Cargo.lock` | Exit 0; DV-008/DV-017 allowed warnings only |
| `pip-audit` | Project and Sphinx resolved requirements | 0 vulnerabilities in both scans |

No dependency manifest changed, so no change-attributable Snyk Open Source scan
was required. GitHub's API still reports native secret scanning disabled (HTTP
404); plan amendment #5's full-history Gitleaks workflow and protected-branch
substitute remain the governed controls.

## Out-of-scope discoveries

1. The session brief's 15-figure count has no fifteenth implementation or stored
   output in PRINet 3.0. S2 must disposition this factual mismatch.
2. `tools/reproduce.py` and a checked SHA-256 output manifest belong to WP-035,
   the registered next work package; this S1 exposes deterministic generators
   and normalization but does not pre-empt that pipeline.
3. Production scientific training and new benchmark measurements were not run,
   matching the explicit non-goal.

## Handoff to S2

Recommended audit focus:

1. Confirm the 14-vs-15 figure discrepancy against the historical module and
   both stored figure trees.
2. Re-run the stored-artefact acceptance test and inspect all 11 exact LaTeX
   comparisons plus the PDF/PNG normalization contract.
3. Review output-root confinement and symlink resolution for every writer.
4. Review report escaping and malformed-JSON isolation.
5. Review profiler lifecycle/state validation and verify Rust-call labels appear
   without implying native Rust `tracing` subscriber integration that does not
   exist in the current bindings.
6. Confirm WP-035, not WP-034, owns the final reproduction CLI and manifest.
