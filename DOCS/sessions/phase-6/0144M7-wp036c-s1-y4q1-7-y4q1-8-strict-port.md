# Session 0144M7 — WP-036C S1 (sub-pass 7/8): Y4Q1_7/Y4Q1_8 strict port

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036C
**Session type:** S1 — Coding
**Predecessor:** [0144M6 — Coding (sub-pass 6/8)](0144M6-wp036c-s1-y4q1-4-y4q1-5-y4q1-9-strict-port.md)
**Successor:** [0144M8 — Coding (sub-pass 8/8)](0144M8-wp036c-s1-y4q2-y4q3-y4q4-kernels-and-consolidation.md)
**Authority:** Project Plan §6/§8, amendments #31/#33/#36/#39, and [`WP-036C-S1-execution-plan-and-decomposition.md`](WP-036C-S1-execution-plan-and-decomposition.md). The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Strict-port the assigned PRINet 3.0 reference files (194 functions / 1,911 lines total):

- `test_y4q1_7.py` — 79 functions / 840 lines
- `test_y4q1_8.py` — 115 functions / 1071 lines

## Focus

`prinet.nn.ablation_variants`; `prinet.utils.temporal_metrics`; `prinet.utils.temporal_training.TemporalTrainer`; `prinet.utils.adversarial_tools`. Largest function count of the eight sub-passes; two files only.

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
is green. Commit locally only; proceed to 0144M8.
