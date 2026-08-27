# Session 0141C — WP-036 S1 (sub-pass 3/5): prin-kernels reference-fn bindings and DV-012 sweep bindings

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036
**Session type:** S1 — Coding
**Predecessor:** [0141B — tensor and train bindings](0141B-wp036-s1b-tensor-and-train-bindings.md)
**Successor:** [0141D — net-new Python surface](0141D-wp036-s1d-net-new-python-surface.md)
**Authority:** Project Plan §6/§8, amendments #31/#32, the decomposition plan
[`WP-036-S1-execution-plan-and-decomposition.md`](WP-036-S1-execution-plan-and-decomposition.md). Standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Bind the `prin-kernels` CPU reference kernels (the numerical authority per the
DV-012 closure) to Python as the `pytorch_*` compatibility family, bind the
sparse-coupling helpers, and close the `prin-py` half of **DV-012** with
`sweep_coupling_params`, `detect_oscillation`, and `phase_to_rate` over
`prin-sim`.

Bucket C (~15): `pytorch_mean_field_rk4_step`, `pytorch_sparse_knn_coupling`,
`pytorch_pac_modulation`, `pytorch_hierarchical_order_param`,
`pytorch_multi_rate_rk4_step`, `pytorch_multi_rate_derivatives`,
`pytorch_fused_sub_step_rk4`, `pytorch_cross_band_coupling`,
`pytorch_fused_discrete_step`, `pytorch_fused_discrete_step_full`,
`csr_coupling_step`, `sparse_knn_coupling_step`, `build_knn_neighbors`,
`sparse_coupling_matrix`, `sparse_coupling_matrix_csr`.
Bucket F (3): `sweep_coupling_params`, `detect_oscillation`, `phase_to_rate`.

## Contract

- **Acceptance:**
  - New PyO3 bindings over the existing `prin-kernels` `step_cpu` /
    `sparse_knn` / `pac` / hierarchical CPU references and `prin-sim` sweep
    engine; **no numerics added in Python or `prin-py`**.
  - Every covered symbol resolves from `prin`, is in the appropriate
    `__all__`, and passes a construct/callable smoke check.
  - Kernel-equivalence unit tests: each `pytorch_*` binding output matches the
    corresponding `prin-kernels` CPU reference within registered tolerance.
  - DV-012 `prin-py` half is closed: the `DEFERRED_VALIDATION_REGISTER.md`
    DV-012 row is updated to `CLOSED` with evidence (register edit belongs to
    S4, but the evidence is produced here and cited in the handoff).
  - `.pyi` updated; `mypy --strict` clean; Rust gates green.
  - Migration Guide rows added; the D-D appendix updated to mark the
    `pytorch_*` family as delivered-as-real-binding.
- **Non-goals:** `triton_*`/`*_cuda` real implementations (they stay D-D stubs
  from 0141A); net-new surface (0141D); full table/matrix (0141E).

## Required reading

- The 0141A/0141B handoff drafts and the D-D disposition appendix
- `crates/prin-kernels/` lib docs; WP-017/018/019/020 audits; DV-012 register row
- `crates/prin-sim/` sweep engine; WP-016 audit and amendment #20
- `DOCS/standards/Coding_Standards.md` §2.1, §6; `DOCS/standards/Testing_Standards.md` §1, §4
- Latest PSR and cumulative deviation ledger

## Entry conditions

- 0141B committed; maturin toolchain confirmed working in 0141B.
- No unresolved D1/D2 finding exists.

## Expected work

1. Add bindings; Rust + Python tests in tandem; maturin rebuild.
2. Kernel-equivalence tests against the CPU references.
3. DV-012 sweep/engine bindings + determinism tests (Seed flow preserved).
4. `prin` wrapper placement recorded; `.pyi` updated; full local gate.
5. Record out-of-scope discoveries.

## Required evidence and outputs

- Code + tests in the same commit range; ≥95% coverage on new/changed code.
- Full local gate (Rust + Python) reproduced and recorded.
- Kernel-equivalence evidence table; DV-012 closure evidence.
- Snyk Code on modified first-party source; ecosystem audits if manifests change.
- Sub-pass handoff note appended to the running S1 handoff draft.

## Prohibited

- Deferred tests, weakened tolerances, Python/`prin-py` numerics, undocumented
  public API, hidden RNG, unapproved `unsafe`, scope creep into `triton_*`
  real work or net-new surface, unregistered experimentation.

## Exit gate

Local gate green; acceptance items evidence-mapped. Commit locally only.
Proceed to 0141D.
