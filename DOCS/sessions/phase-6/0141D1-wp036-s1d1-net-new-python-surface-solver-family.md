# Session 0141D1 — WP-036 S1 (sub-pass 4a/5): Net-new Python surface, part 1 — Bucket G solver family

**Status:** COMPLETE
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036
**Session type:** S1 — Coding
**Predecessor:** [0141C — kernels bindings and DV-012](0141C-wp036-s1c-kernels-bindings-and-dv012.md)
**Successor:** [0141D2 — net-new Python surface, part 2](0141D2-wp036-s1d2-net-new-python-surface-remainder.md)
**Parent brief:** [0141D — net-new Python compatibility surface](0141D-wp036-s1d-net-new-python-surface.md)
**Authority:** Project Plan §6/§8, amendments #31/#32, the decomposition plan
[`WP-036-S1-execution-plan-and-decomposition.md`](WP-036-S1-execution-plan-and-decomposition.md); the
0141D brief. Standard wins on conflict.

> Split from 0141D under Development Workflow §7 and the 0141D brief "Expected
> work" item 3 (the decomposition plan §4 flagged this split in advance).

## Mission

Deliver the first, self-contained slice of **Bucket G**: the PRINet 3.0
`prinet.utils.cuda_kernels` **solver family** (`SolverResult`,
`BatchedRK45Solver`, `FixedStepRK4Solver`, `gradient_checkpoint_integration`)
plus the standalone `TelemetryLogger` observation hook — real, importable,
construct/callable implementations that are thin orchestration over existing
PRIN owners with **zero Python numerics**, plus new-symbol unit tests.
Behavioral parity is not in scope (WP-036B/WP-036C). The ~40 remaining Bucket G
symbols move to 0141D2.

## Contract

- **Acceptance:**
  - Every covered symbol resolves from `prin`, is in the appropriate `__all__`,
    and passes a construct/callable smoke check.
  - Each is a real implementation with **no numerics** — composition over
    `prin.dynamics.RK45Integrator` / `prin.dynamics.RK4Integrator` for the
    solvers; pure bookkeeping for `TelemetryLogger`.
  - Every non-faithful behaviour has a documented Migration-Guide deviation
    (no silent divergence).
  - New-symbol unit tests for every symbol; ≥95% coverage on new code.
  - `mypy --strict` clean; `interrogate` 100% on new modules.
  - Migration Guide rows for every covered symbol.
- **Non-goals:** behavioral parity (WP-036B/C); the other Bucket G symbols
  (0141D2); the full 172-row table and smoke matrix (0141E); new Rust numerics
  or new PyO3 bindings.

## Expected work — completed

1. `python/prin/solvers.py` (new): `SolverResult`, `BatchedRK45Solver`,
   `FixedStepRK4Solver`, `gradient_checkpoint_integration`, `SolverError`.
2. `python/prin/training_hooks.py` (new): `TelemetryLogger`.
3. `prin.__all__` + `python/prin/_public_api.py::RC1_PUBLIC_API` +
   `python/prin/__init__.pyi` extended together; `verify_api_surface` clean.
4. `tests/test_solver_surface.py` (new): 11 tests.
5. Migration Guide "sub-pass 0141D1" section; D-D appendix rows 27–30 updated;
   0141D2 disposition analysis added to the D-D appendix.
6. Full local Python gate reproduced.

## Namespace placement

| Symbol | Module | Rationale |
|---|---|---|
| `SolverResult`, `BatchedRK45Solver`, `FixedStepRK4Solver`, `gradient_checkpoint_integration` | `prin.solvers` (new) | PRINet 3.0's `utils/cuda_kernels.py` has no existing PRIN home; grouped by reference module. Also top-level. |
| `TelemetryLogger` | `prin.training_hooks` (new) | PRINet 3.0's `nn/training_hooks.py`; 0141D2 adds the rest of that module's surface here. Also top-level. |
| `SolverError` | `prin.solvers` only | Not a PRINet 3.0 top-level export; module-scoped like `prin.tensor.DecompositionError`. |

## Completion evidence

- **Code:** `python/prin/solvers.py`, `python/prin/training_hooks.py`;
  `python/prin/__init__.py`, `python/prin/_public_api.py`,
  `python/prin/__init__.pyi` updated.
- **Tests:** `tests/test_solver_surface.py` — 11 tests; new-module line
  coverage 100% (`solvers.py`, `training_hooks.py`).
- **Docs:** `DOCS/sphinx/migration_guide.rst` "sub-pass 0141D1" section (5
  rows + D1–D4 deviations); `DOCS/experiments/0141-wp036-s1-dd-dispositions.md`
  rows 27–30 marked "Delivered (real)" + the 0141D-split section with the
  per-group 0141D2 disposition analysis.
- **Handoff:** `DOCS/experiments/0141-wp036-s1-handoff.md` "0141D1" section
  (acceptance map, parity-evidence disposition, verification record,
  out-of-scope discoveries).
- **Local gate (reproduced on this session, Windows / Python 3.14):**
  - `ruff check` / `ruff format --check` — clean
  - `mypy python/prin --strict` — 43 files, 0 issues
  - `interrogate -c pyproject.toml python/prin` — 96.6% overall; new modules 100%
  - `bandit -r python/prin -c pyproject.toml` — no issues
  - `pytest tests/ -m "not slow and not gpu" -p no:randomly --cov=prin` —
    **806 passed, 9 deselected**, 99% coverage (`solvers.py` 100%,
    `training_hooks.py` 100%)
  - `pytest --doctest-modules python/prin/solvers.py python/prin/training_hooks.py`
    — 4 passed
  - `pip-audit .` — no known vulnerabilities
  - `cargo audit` — exit 0 (3 governed allowed warnings; no manifest changed)
  - `snyk code test --severity-threshold=low` on the 3 modified/new first-party
    files — 0 issues each; Snyk Open Source N/A (no dependency input changed)
  - `sphinx-build -W --keep-going` — build succeeded
  - `tools/wp001_baseline.py check` — passed
  - `tools/check_dv_register_gates.py` — passed
  - `verify_api_surface(prin.__all__)` — `(set(), set())`
- **No Rust source, Cargo/Python manifest, or PyO3 surface changed** → Rust
  gates and `maturin develop` are not applicable to this sub-pass.

## Out-of-scope discoveries

Recorded in the handoff "Out-of-scope discoveries (0141D1)" section: the DV-025
target conflict (0141D brief vs the register's WP-036C/0144E re-target), the
`ring_topology`/`small_world_topology` representation mismatch, the unbound
`prin_sim::OscilloSim`/`prin_sim::pruning` owners, and `temporal_smoothness_loss`
having no faithful `prin.eval` owner. 0141D2's brief must act on all four.

## Exit gate

Local gate green; acceptance items evidence-mapped. Committed locally only.
Proceed to 0141D2.
