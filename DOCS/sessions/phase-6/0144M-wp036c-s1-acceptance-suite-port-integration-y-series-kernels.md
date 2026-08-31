# Session 0144M — WP-036C S1: Coding — Acceptance suite port (integration, y-series, kernels; DV-025)

**Status:** PLANNED (decomposed into `0144M1`–`0144M8` by plan amendment #39)
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036C
**Session type:** S1 — Coding
**Predecessor:** [0144L — Documentation (WP-036D S4)](0144L-wp036d-s4-gpu-execution-path-ported-acceptance-suite.md)
**Successor:** [0144M1 — Coding (sub-pass 1/8)](0144M1-wp036c-s1-integration-q3-and-y2q1-y2q4-strict-port.md)
**Authority:** Project Plan §6/§8 and amendments #31/#36; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> Renumbered `0144I` → `0144M` by plan amendment #36 (WP-036D, "GPU execution
> path for the ported acceptance suite", takes `0144I`–`0144L`). Scope,
> acceptance criteria, and non-goals are unchanged.

> This is a prospective execution contract, not completion evidence.

## Mission

Port the remaining PRINet 3.0 acceptance suite — reference test files
`test_integration_q3`, `test_y2q1`–`test_y2q4`, `test_y3q1`–`test_y3q49`,
`test_y4q1*` (7 files), `test_y4q2`, `test_y4q3`, `test_y4q4`,
`test_triton_kernels`, `test_gpu` (~790 `def test_` functions) — into `tests/`
against the `prin` compatibility surface, adapting imports only. Resolve DV-025
(`retrain_controller`, `SubconsciousController.export_to_onnx`/`.quantize_onnx`)
where its reference tests are in this scope.

## Contract

- **Acceptance:** Every ported test in scope passes on CPU, Linux + Windows,
  Python 3.11–3.13; the **full** ported ~1,670-test acceptance suite
  (WP-036B + WP-036C) is green on CPU. Assertions unchanged from the reference
  except documented preserved-hazard tolerance annotations (Parity Report).
  GPU/Triton reference tests (`test_gpu`, `test_triton_kernels`, and GPU cases
  elsewhere) are `skipif`-guarded on backend availability. DoD items 1–2 are
  satisfied on close.
- **Non-goals:** New `prin` public symbols beyond DV-025's; final documentation
  prose or release publishing; GPU-runner execution of the skipped tests;
  extending WP-036D's Python GPU execution path to `test_gpu` /
  `test_triton_kernels` (those stay `skipif`-guarded — `test_triton_kernels`
  has no CPU analogue and needs the Linux GPU runner tracked by DV-001).

> **Coordination with WP-036D (amendment #36).** WP-036D delivers the Python
> GPU execution path for the 8 CUDA-guarded acceptance tests in the WP-036B
> files and closes before this session. When porting `test_gpu.py` here,
> reuse whatever device-dispatch surface WP-036D established in
> `_torch_compat.py`; do not re-derive a parallel path.

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendment #31
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- `DOCS/standards/Testing_Standards.md` §1 (esp. §1.1)
- `DOCS/reports/036b-project-state.md` and the cumulative deviation ledger
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-025
- WP-036 and WP-036B S1 handoff notes; the Migration Guide symbol table

## Entry conditions

- WP-036B S4 (0144H) and WP-036D S4 (0144L) are closed and committed.
- No unresolved D1/D2 finding exists.
- WP-036C scope, acceptance criteria, and non-goals have maintainer approval.

## Expected work

1. Port each remaining reference test file, imports adapted only.
2. Triage failures exactly as in WP-036B S1: real defect → fix + regression;
   preserved-hazard → tolerance annotation + Parity Report; GPU-only →
   `skipif`.
3. Implement DV-025's `retrain_controller` path (supervised retraining from
   telemetry) as a thin `prin` wrapper over the Rust owner; unit + parity
   tests in tandem; update `tools/wp001_ownership.json` / regenerate the
   traceability baseline.
4. Keep numerical authority in Rust; no Python numerics; deterministic `Seed`.
5. Record every tolerance annotation and out-of-scope discovery.

## Required evidence and outputs

- Ported test files, DV-025 code, and fix commits in one S1 commit range.
- Full ported acceptance suite green on CPU; coverage non-decreasing; ≥95% on
  changed first-party code.
- `ruff`/`ruff format`/`mypy --strict`/`pytest`/`bandit`/dependency audits;
  `cargo fmt`/clippy/`cargo test` if any crate changed for DV-025 or a fix.
- Parity Report delta for all new tolerance annotations.
- An S1 handoff note mapping each acceptance criterion and each reference file
  to evidence, and mapping DV-025 to its resolution.

## Prohibited

- Deferred tests, weakened/deleted assertions, undocumented tolerance drift,
  undocumented public API, duplicated Python numerics, hidden RNG, unapproved
  `unsafe`, scope creep, or unregistered experimentation.

## Exit gate

All S1 gates green; the full ported acceptance suite is green on CPU; every
acceptance criterion is evidence-mapped. Hand off to the mandatory S2 audit.
