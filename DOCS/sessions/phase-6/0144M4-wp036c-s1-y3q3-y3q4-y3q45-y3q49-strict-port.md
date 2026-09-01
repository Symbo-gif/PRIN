# Session 0144M4 — WP-036C S1 (sub-pass 4/8): Y3Q3/Y3Q4/Y3Q45/Y3Q49 strict port

**Status:** COMPLETE (2026-08-31; committed locally at commit a0b7c2b, not pushed; register status backfilled in 0144M5)
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036C
**Session type:** S1 — Coding
**Predecessor:** [0144M3 — Coding (sub-pass 3/8)](0144M3-wp036c-s1-y3q1-y3q2-strict-port.md)
**Successor:** [0144M5 — Coding (sub-pass 5/8)](0144M5-wp036c-s1-y4q1-y4q1-2-y4q1-3-strict-port.md)
**Authority:** Project Plan §6/§8, amendments #31/#33/#36/#39, and [`WP-036C-S1-execution-plan-and-decomposition.md`](WP-036C-S1-execution-plan-and-decomposition.md). The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Strict-port the assigned PRINet 3.0 reference files (117 functions / 2,095 lines total):

- `test_y3q3.py` — 32 functions / 676 lines
- `test_y3q4.py` — 32 functions / 417 lines
- `test_y3q45.py` — 23 functions / 370 lines
- `test_y3q49.py` — 30 functions / 632 lines

## Focus

`prinet.utils.fused_kernels` family (`AsyncCPUGPUPipeline`, `LargeScaleOscillatorSystem`, `MixedPrecisionTrainer`, `OscillatorPruner`, `build_knn_neighbors`, `sparse_coupling_matrix_csr`, MSVC-path helpers, `cuda_fused_kernel_available`); OscilloSim (`prin.simulation`); `prinet.nn.slot_attention`. GPU / CUDA cases stay `skipif`-guarded.

## Contract

- Copy each reference file under a stable `tests/test_acceptance_*.py` name and
  adapt imports only. Assertions, expected values, parametrization, call order,
  and semantics remain unchanged (Testing Standards §1.1).
- Fix missing compatibility behavior in the owning Rust crate, exposed through
  thin PyO3 / Python delegation; no Python numerics and no semantic-test adapter.
- Preserve the existing governed tolerance / backend-availability mechanisms
  (amendments #14/#16/#17/#25 → per-test annotation + Parity Report entry);
  neither permits weakened assertions or unapproved skips.
- GPU / Triton / CUDA reference cases keep the reference file's own
  `skipif` / availability guard and reuse WP-036D's `_torch_compat.py` device
  dispatch — no parallel GPU path.
- **Non-goals:** all other `0144M*` sub-pass files, WP-036 public-symbol expansion beyond DV-025, GPU-runner execution of skipped tests, final S1 consolidation, the S2 audit.

## Required reading

- The `0144M` parent brief, amendment #39, and the adopted decomposition plan
- Testing Standards §1.1 and Development Workflow §3/§7
- Latest Project State Report and cumulative deviation ledger
- Running handoff `DOCS/experiments/0144M-wp036c-s1-handoff.md`
- The assigned reference files and applicable Rust / PyO3 compatibility owners

## Entry conditions

Amendment #39 is adopted; WP-036D (`0144L`) is closed; the preceding sub-pass
gate is green; no unresolved D1/D2 exists.

## Expected work

1. Copy the assigned files and make import-only adaptations.
2. Record a reference-vs-port diff proving no semantic test rewrite.
3. Run collection and execution; fix product behavior only through Rust-backed
   owners with same-pass regression / coverage evidence.
4. Run applicable local quality / security gates; ≥95% changed-code coverage
   (CI authoritative where host coverage instrumentation is blocked).
5. Append file counts, results, tolerance annotations, backend guards, and
   out-of-scope discoveries to the running handoff.

## Prohibited

Assertion / value / parametrization rewrites, Python numerics, test-local
behavior shims, deferred tests, unapproved skips, undocumented tolerance
changes, hidden RNG, unapproved `unsafe`, scope creep, or push.

## Exit gate

Every assigned reference function is accounted for and the sub-pass local gate
is green. Commit locally only; proceed to 0144M5.
