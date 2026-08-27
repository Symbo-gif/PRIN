# Session 0141A — WP-036 S1 (sub-pass 1/5): Freeze machinery, re-export surface, aliases, D-D stubs

**Status:** COMPLETE
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036
**Session type:** S1 — Coding
**Predecessor:** [0141 — WP-036 S1 (decomposed)](0141-wp036-s1-api-completion-acceptance-suite-and-migration.md)
**Successor:** [0141B — tensor and train bindings](0141B-wp036-s1b-tensor-and-train-bindings.md)
**Authority:** Project Plan §6/§8, amendments #31 and **#32**, and the decomposition plan
[`WP-036-S1-execution-plan-and-decomposition.md`](WP-036-S1-execution-plan-and-decomposition.md). If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Establish the foundation of the `prin` PRINet-3.0-compatible surface:
`prin._deprecation` freeze/deprecation machinery; the top-level `prin.__all__`
assembled from the **71** `prinet.__all__` symbols that already resolve by name
from a `prin` submodule; the **~8** pure rename aliases whose target is already
built and exposed; and the **~10** GPU/Triton D-D stubs. No new PyO3 bindings,
no maturin rebuild.

## Contract

- **Acceptance:**
  - `python/prin/_deprecation.py` provides `deprecated`, `deprecated_parameter`,
    `verify_api_surface`, and `FROZEN_PUBLIC_API` (a `frozenset`) seeded from
    **PRIN's own RC1 `__all__`** (not PRINet's).
  - `prin.__all__` (top level) re-exports the 71 already-resolving symbols; each
    resolves via `import prin; getattr(prin, name)` and passes a
    construct/callable smoke check.
  - The ~8 rename aliases (`SCALROptimizer`→`Scalr`, `RIPOptimizer`→`Rip`,
    `SynchronizedGradientDescent`→`SyncGd`, `TemporalPhasePropagator`→
    `TemporalPropagator`, `temporal_recovery_speed`→`recovery_speed`,
    `OscillatorModel`, `ThetaGammaNetwork`/`DeltaThetaGammaNetwork` helpers over
    `BandNetwork`) resolve and smoke-check; each alias is a thin Python shim
    with **no numerics**.
  - The ~10 GPU/Triton D-D stubs (`triton_available`,
    `triton_fused_mean_field_rk4_step`, `triton_sparse_knn_coupling`,
    `triton_pac_modulation`, `triton_hierarchical_order_param`,
    `triton_fused_discrete_step`, `cuda_fused_kernel_available`,
    `fused_discrete_step_cuda`, plus a shared `BackendUnavailableError`-class
    exception) resolve; predicate functions return `False`; kernel stubs raise
    the typed exception with a migration message on call.
  - `verify_api_surface(prin.__all__)` regression test is green.
  - `.pyi` stubs updated for every symbol added in this pass.
  - Migration Guide table rows added for every symbol covered in this pass.
  - `DOCS/experiments/0141-wp036-s1-dd-dispositions.md` created with the full
    per-symbol disposition table for all ~30 D-D symbols (this pass + the ones
    delivered as real bindings in 0141C), for S2 audit veto.
- **Non-goals:** PyO3 bindings, maturin rebuilds, net-new Python classes
  (0141B–0141D); the full 172-row table and full smoke matrix (0141E);
  behavioral parity beyond smoke checks.

## Required reading

- `DOCS/PRIN_Project_Plan.md` §5 (preserved hazards), §8.3 amendments #31/#32
- `DOCS/sessions/phase-6/WP-036-S1-execution-plan-and-decomposition.md`
- `DOCS/standards/Coding_Standards.md` §2.1 (no Python numerics), §6
- `DOCS/standards/Testing_Standards.md` §1
- `DOCS/standards/Documentation_Standards.md` §7 (Migration Guide)
- `DOCS/baselines/wp001_api_traceability.md`
- The archived `src/prinet/_deprecation.py` (reference for shape only)
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger

## Entry conditions

- Amendment #32 recorded; the decomposition plan is ADOPTED.
- WP-035 S4 (0140) is closed and committed.
- No unresolved D1/D2 finding exists.

## Expected work

1. Write `python/prin/_deprecation.py` with tests written in tandem; derive
   `FROZEN_PUBLIC_API` from PRIN's RC1 `__all__` (documented derivation).
2. Assemble `prin.__all__`; add re-exports and audit each submodule `__all__`.
3. Add the rename aliases and D-D stubs with docstrings at threshold.
4. Add the `verify_api_surface` regression test and a smoke construct/callable
   test parametrized over every symbol covered so far.
5. Add `.pyi` stubs; run `mypy --strict`, `interrogate` (100% public).
6. Add Migration Guide rows; add the D-D disposition appendix.
7. Record any out-of-scope discovery for a later sub-pass or WP.

## Required evidence and outputs

- Code and tests in the same commit; ≥95% coverage on new/changed code.
- `ruff`, `ruff format --check`, `mypy python/prin --strict`, `interrogate`,
  `bandit`, `pytest` (new tests), `pip-audit`; Snyk Code on modified
  first-party Python (Snyk Open Source not applicable — no manifest change).
- No Rust change in this pass (`cargo` gates unchanged; note this explicitly).
- A sub-pass handoff note (appended to the running S1 handoff draft) listing
  each covered symbol and its evidence.

## Prohibited

- Deferred tests, weakened assertions, undocumented public API, Python
  numerics, hidden RNG, `# pragma: no cover` on aliases, scope creep into
  binding work, or unregistered experimentation.

## Exit gate

Local gate green; every acceptance item evidence-mapped in the handoff draft.
Commit locally only. Proceed to 0141B.
