# DOCS/sphinx/

Sphinx + Markdown documentation for PRIN, published to ReadTheDocs.

> **Note on location:** the archived plan placed the Sphinx site at `docs/`,
> but Windows filesystems are case-insensitive, so `docs/` would collide with
> the governance directory `DOCS/`. The Sphinx site therefore lives at
> `DOCS/sphinx/`. The ported acceptance tests that hard-coded `docs/` were
> path-adapted to `DOCS/sphinx/` at WP-037 S1 (session `0145`), following the
> ETCA-001 T-F4 follow-up (b) precedent — assertions unchanged.

Published to ReadTheDocs (`prin.readthedocs.io`). Rust API docs are published
separately to docs.rs and linked from `rust_api.rst`.

## Content (project plan §11 — all delivered at WP-037 S1)

| Page | Status |
|---|---|
| `getting_started.rst` | Complete. Every code block executed against PRIN 0.3.0 (CPython 3.14 / torch 2.11, CPU); printed values are real output. |
| `architecture.rst` | Complete. Two-layer Rust/Python design, workspace layout, data flow, backend-dispatch status by DV item, compatibility surface, determinism. |
| `coupling_topologies.rst` | Complete. Ported and corrected from `DOCS/API_Reference_Coupling_Topologies.md`; both coupling surfaces, `"auto"` thresholds, per-edge weights, band networks. |
| `capacity_analysis.rst` | Complete. The implemented `theoretical_capacity` relation with its verified invariants, plus the archived PRINet 3.0 K.3 sweep labelled REFERENCE-HISTORICAL. |
| `migration_guide.rst` | Complete. 172-row symbol-by-symbol disposition table, machine-checked by `tools/wp036_migration_table.py`. |
| `kernel_architecture.rst` | Complete. Single-source CubeCL design and per-kernel tolerances. |
| `parity_report.rst` | **Draft** (WP-037). Tolerance register, 504-case golden-corpus results, an explicit "benchmark re-run not yet run" section, an evidence index, and the numerical-deviation register. Labels every claim VALIDATION / CONFIRMATORY / REFERENCE-HISTORICAL. |
| `notebooks.rst` | Complete. The four notebooks with measured runtime budgets. |
| `paper.rst` | Complete. LaTeX sources, the reproduction pipeline, artefact wiring, compilation. |
| `rust_api.rst` | Complete. Per-crate docs.rs links and `[package.metadata.docs.rs]` build settings. Publication is gated on WP-038 enabling `release.yml`'s `publish-crates` job; the page says so. |
| `changelog.rst` | Delegation stub — `.. include:: ../../CHANGELOG.md` via MyST. |

## API reference (`api/`)

23 pages. `core.rst` renders the flat `prin` namespace **docstring-only**; the
per-module pages own the object descriptions and the index entries.

That split is a build requirement. `prin.__all__` re-exports objects that are
also documented on their owning module's page, and Sphinx resolves a re-export
to a canonical name — describing the same object twice is a "duplicate object
description" warning, which `-W` turns into a failure. `:no-index:` suppresses a
*class* description but **not** the descriptions autodoc generates for that
class's `@dataclass` fields, which is why the re-export facades
(`prin._torch_compat`, `prin._compat`) are rendered docstring-only rather than
`no-index`'d with `:members:`.

`:undoc-members:` is deliberately absent from every `api/*.rst`. PRIN enforces
docstrings on all public symbols (ruff pydocstyle `D`, `interrogate
--fail-under 95`), so the option added nothing except a second description of
each dataclass field — napoleon already renders the class's `Attributes:`
section as a field table.

`tests/test_sphinx_docs.py` guards all of this: orphaned pages, toctree entries
that do not resolve, a `prin` submodule whose public names reach no documented
page, `conf.py`'s `release` drifting from `pyproject.toml`, any module
member-documented on two indexed pages, and guides that regress to stubs.
`tests/test_sphinx_examples.py` executes the shipped guide code blocks end-to-end.

## Build

```bash
pip install -r DOCS/sphinx/requirements.txt
pip install -e ".[dev]"
maturin develop -m crates/prin-py/Cargo.toml   # autodoc imports prin

# Clean-build discipline (Documentation Standards §7 item 3, AGENTS.md):
# always delete the output directory first. Sphinx's incremental build tracks
# only .rst/.md timestamps, so a reused _build can silently mask a genuine
# autodoc-sourced warning for any number of subsequent sessions.
rm -rf DOCS/sphinx/_build
sphinx-build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
```

CI runs exactly that in `python.yml`'s `docs` job, followed by the shipped
guide-example harness (`pytest tests/test_sphinx_examples.py -m slow`) and the
notebook execution harness (`pytest tests/test_notebooks.py -m slow`) — the
evidence for Definition of Done #8. The project README is intentionally
excluded from the Sphinx source toctree.

## Known gap (routed to WP-038)

`.readthedocs.yaml` installs only `DOCS/sphinx/requirements.txt`, so ReadTheDocs
cannot import `prin` and its `automodule` directives render empty — silently,
because `fail_on_warning` is `false`. The authoritative warning-as-error gate is
the CI `docs` job, which does build the extension. The fix is a `build.jobs.pre_build`
block that installs `maturin` and CPU-only `torch` and runs
`maturin develop -m crates/prin-py/Cargo.toml`; it is not applied here because
it cannot be verified without a real ReadTheDocs build, and a failed RTD job
takes the published site down. Recorded in
`DOCS/experiments/0145-wp037-s1-handoff.md` and routed to WP-038 (RC1
packaging), which owns "docs deployed" per Versioning and Release Standards.

## Conventions

- One README per source directory (3.0 convention, kept).
- Benchmark reports are written to `DOCS/test_and_benchmark_results/`
  (gitignored); canonical artefacts live in `benchmarks/results/`.
- Publication figures and tables are generated into `paper/figures` and
  `paper/tables` and are gitignored — see `DOCS/sphinx/paper.rst`.
