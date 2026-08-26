# benchmarks/benchrunner/ (unified CLI)

The single entry point for all nine benchmark categories (WP-033;
Benchmarking and Reproducibility Standards §2.1: "executed via the single
`benchrunner` CLI. No one-off scripts.").

## Usage

```bash
python -m benchmarks.benchrunner --list
python -m benchmarks.benchrunner --category scaling --out benchmarks/results/
python -m benchmarks.benchrunner --category scaling --name oscillator_count --iterations 20
```

`--category` selects one of `scaling`/`chimera`/`mot`/`ablations`/`kernels`/
`integrators`/`training`/`daemon`/`adversarial`; `--name` narrows to one
registered benchmark within it. `--iterations` (default 10, must be ≥10) and
`--warmup` (default 2) map onto `BenchmarkConfig`. Results are written as
`<category>_<name>.json` under `--out` (default `benchmarks/results/`).

## Contents

- `__main__.py` — argument parsing, category-package import (which triggers
  each module's `@register` self-registration), dispatch, and result
  writing.
