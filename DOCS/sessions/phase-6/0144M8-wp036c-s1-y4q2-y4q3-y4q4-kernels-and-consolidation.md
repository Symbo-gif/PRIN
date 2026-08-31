# Session 0144M8 — WP-036C S1 (sub-pass 8/8): Y4Q2/Y4Q3/Y4Q4, GPU/Triton guards, and consolidation

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036C
**Session type:** S1 — Coding
**Predecessor:** [0144M7 — Coding (sub-pass 7/8)](0144M7-wp036c-s1-y4q1-7-y4q1-8-strict-port.md)
**Successor:** [0144N — Audit (WP-036C S2)](0144N-wp036c-s2-acceptance-suite-port-integration-y-series-kernels.md)
**Authority:** Project Plan §6/§8, amendments #31/#33/#36/#39, and [`WP-036C-S1-execution-plan-and-decomposition.md`](WP-036C-S1-execution-plan-and-decomposition.md). The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Strict-port the assigned PRINet 3.0 reference files (221 functions / 3,093 lines total):

- `test_y4q2.py` — 67 functions / 703 lines
- `test_y4q3.py` — 30 functions / 475 lines
- `test_y4q4.py` — 44 functions / 442 lines
- `test_triton_kernels.py` — 40 functions / 874 lines
- `test_gpu.py` — 40 functions / 599 lines

## Focus

`prinet.utils.figure_generation` + `table_generation` (publication figures / tables; uses `matplotlib`); `fused_kernels` reproduction checks; `test_triton_kernels` and `test_gpu` ported with their reference `skipif` / `triton_available` guards intact, reusing WP-036D's `_torch_compat.py` device dispatch -- no new GPU path, no runner execution here (`test_triton_kernels` needs the DV-001 Linux GPU runner). **Consolidation:** complete file-by-file accounting for all 1,097 reference `def test_` functions across the 24 files, every tolerance annotation, every backend guard, and every out-of-scope discovery; run the full WP-036B + WP-036C ported acceptance suite on CPU; write the S1 handoff mapping each acceptance criterion and each reference file to evidence and DV-025 to its resolution. Pre-authorised to split `0144M8a` / `0144M8b` under Development Workflow §7.

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
- **Non-goals:** WP-036 public-symbol expansion beyond DV-025, GPU-runner execution of the skipped GPU / Triton tests, the S2 audit.

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
is green. Commit locally only; proceed to 0144N.
