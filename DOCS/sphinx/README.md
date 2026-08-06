# DOCS/sphinx/

Sphinx + Markdown documentation for PRIN, published to ReadTheDocs.

> **Note on location:** the archived plan placed the Sphinx site at `docs/`,
> but Windows filesystems are case-insensitive, so `docs/` would collide with
> the governance directory `DOCS/`. The Sphinx site therefore lives at
> `DOCS/sphinx/`.

Published to ReadTheDocs (`prin.readthedocs.io`). Rust API docs are published
separately to docs.rs and linked from here.

## Planned content (project plan §11)

- **Getting Started Tutorial** (`getting_started.rst`) — ported from 3.0.
- **Architecture Guide** (`architecture.rst`) — ported and updated for the
  two-layer Rust/Python design.
- **Migration Guide (PRINet 3.0 → PRIN)** — symbol-by-symbol mapping table and
  tolerance notes.
- **Kernel Architecture** — the single-source CubeCL kernel design.
- **Parity Report** — published results of the numerical parity program
  (placeholder until Phase 6; the WP-002 golden corpus is in `parity/`).
- **API Reference** (`api/`) — autodoc for `prin`, `prin.parity`, `prin.nn`,
  `prin.eval`, `prin.experiments`, `prin.reporting`.

## Build

```bash
pip install -r DOCS/sphinx/requirements.txt
pip install .
sphinx-build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
```

WP-001 verified the warning-as-error build against an installed wheel. The
project README is intentionally excluded from the Sphinx source toctree.

## Conventions

- One README per source directory (3.0 convention, kept).
- Benchmark reports are written to `DOCS/test_and_benchmark_results/`
  (gitignored); canonical artefacts live in `benchmarks/results/`.
