# benchmarks/results/ (canonical benchmark artefacts)

Canonical, tracked output directory for `benchrunner` results (Benchmarking
and Reproducibility Standards §3: "Canonical benchmark results:
`benchmarks/results/` (tracked)."). `python -m benchmarks.benchrunner
--category <cat> --out benchmarks/results/` writes here by default.

This directory is currently empty: WP-033 S1 builds the `benchrunner`
machinery and the nine category modules and validates them with small,
fast, characterization-scale parameters (Non-goal: drawing conclusions from
final measurements). Production-scale campaign results are future work.

Generated reports/figures derived from these artefacts go to
`DOCS/test_and_benchmark_results/` (gitignored), not here.
