# prin.reporting (Reporting & Visualization)

Benchmark JSON reports, publication figures, LaTeX tables, and profiling.
Near-verbatim ports of the PRINet 3.0 `utils/{benchmark_reporting,
figure_generation, table_generation, profiler}.py` tools (Phases 1 & 6;
publication surface delivered in WP-034, sessions 0133–0136).

## Design rules

- **No numerics in Python.** Every module only *renders* or *profiles* values
  that already live in stored benchmark JSON or in the Rust core. No scientific
  quantity is recomputed. The SCALR CV in `benchmark_reporting` is a reporting
  statistic over caller-supplied values, not a model primitive.
- **Deterministic output.** Reports carry no implicit wall-clock timestamp;
  `generated_at` is caller-supplied and normalized to UTC minute precision.
  Figures use the non-interactive `Agg` backend, a fixed PDF date/producer, and
  a fixed SVG `hashsalt`. Unchanged inputs produce byte-stable output.
- **Typed errors at the public boundary.** Every public function raises a typed
  error from the `ReportingError` hierarchy (see below); no bare `ValueError`
  or `KeyError` escapes.
- **Output-path confinement.** Every writer resolves its target with
  `Path.resolve()` (following symlinks) and rejects anything outside
  `benchmarks/results/`, `DOCS/test_and_benchmark_results/`, or the OS temp
  tree. Historical `paper/` paths are read-only parity references, never active
  output defaults.

## Modules

| Module | Public surface |
|---|---|
| `benchmark_reporting` | `generate_benchmark_report`, `generate_leaderboard`, `generate_scalr_metrics_report` — deterministic Markdown from stored benchmark JSON; preserves the 3.0 artefact schema, ranking, and tie-breaking. Errors: `ReportInputError`, `ReportOutputError`. |
| `figure_generation` | 14 stored-artefact figure generators `fig_ablation_results` … `fig_training_curves` (historical `fig2`–`fig15`), `configure_neurips_style`, `generate_all_figures`, `normalize_matplotlib_output`. 300 DPI matplotlib. Errors: `PublicationGenerationError`, `ArtifactNotFoundError`, `ArtifactSchemaError`, `OutputPathError`, `NormalizationError`. |
| `table_generation` | 11 byte-comparable LaTeX fragment generators `table_ablation_variants` … `table_supercritical_regime`, `generate_all_tables`. Each fragment regenerates bytes-identical to its stored `paper/tables/` counterpart. |
| `profiler` | `PRINetProfiler` (typed `torch.profiler` wrapper), legacy `ProfileReport`, `profile_training_loop`, and `record_function(label)` as the explicit boundary that surfaces Rust-backed operations in torch traces. No model numerics; RNG state untouched. Errors: `ProfilerConfigurationError`, `ProfilerStateError`. |
| `_artifacts` | Internal. Single home for stored-artefact JSON loading + schema validation and the typed error hierarchy, so `figure_generation` and `table_generation` never reach into each other's private names. |

## Figure count

There are **14** figure generators, not 15. The PRINet 3.0 reference
(`utils/figure_generation.py` and stored `paper/figures/`) numbers its figures
`fig2`–`fig15`; no `fig1` implementation or stored output has ever existed.
Session briefs that quote "15 figures" are factually corrected in
`DOCS/reports/034-project-state.md` (finding WP034-F1); this is not a dropped
deliverable.

## Error hierarchy

```
Exception
└── ReportingError                     (prin.reporting._artifacts; shared root)
    ├── PublicationGenerationError
    │   ├── ArtifactNotFoundError       (also FileNotFoundError)
    │   ├── ArtifactSchemaError         (also ValueError)
    │   ├── OutputPathError             (also ValueError)
    │   └── NormalizationError          (also ValueError)
    ├── ReportInputError                (also ValueError)
    ├── ReportOutputError               (also ValueError)
    ├── ProfilerConfigurationError      (also ValueError)
    └── ProfilerStateError              (also RuntimeError)
```

Each type keeps its original stdlib base so pre-existing
`isinstance`/`pytest.raises(ValueError, ...)` catches still hold, while
`except ReportingError` now catches the whole package.

## Regeneration

Figures and tables regenerate from the stored PRINet 3.0 JSON artefacts under
`benchmarks/results/` with no GPU or training. The end-to-end reproduction CLI
and SHA-256 output manifest are WP-035 (`tools/reproduce.py`), not part of this
package.
