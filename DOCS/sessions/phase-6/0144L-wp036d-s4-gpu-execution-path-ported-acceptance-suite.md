# Session 0144L — WP-036D S4: Documentation — GPU execution path for the ported acceptance suite

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036D
**Session type:** S4 — Documentation
**Predecessor:** [0144K — Remediation](0144K-wp036d-s3-gpu-execution-path-ported-acceptance-suite.md)
**Successor:** [0144M — Coding (WP-036C S1)](0144M-wp036c-s1-acceptance-suite-port-integration-y-series-kernels.md)
**Authority:** Project Plan §6/§8 and amendments #31/#33/#36; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Document the GPU execution path, issue the WP-036D Project State Report, and
confirm WP-036C (session 0144M) entry conditions.

## Contract

- **Acceptance:** `tests/README.md` (GPU marker policy, the 8 activated
  tests), `crates/prin-py/README.md` (GPU binding module), and any other
  touched README updated; CHANGELOG entry; `DOCS/sphinx/parity_report.rst`
  GPU-vs-CPU tolerance table current; `.pyi` / Migration Guide current for
  any new binding callable; `gpu.yml` documented; docs gates green; PSR
  issued.
- **Non-goals:** functional feature work; WP-036C; DV-005 (CUDA Burn training
  backend — record the boundary, do not close it).

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendments #31/#33/#36
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- `DOCS/standards/Documentation_Standards.md` §7
- `DOCS/audits/036d-wp036d-audit.md` including its CLEAN closure table
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-001 / DV-002 / DV-005

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update `tests/README.md` (marker policy: `gpu` = runner-selected +
   `skipif`-guarded; the 8 activated acceptance tests), `crates/prin-py/`
   and any other README touched in S1–S3.
2. Update `CHANGELOG.md`; update `DOCS/sphinx/parity_report.rst` with the
   GPU-vs-CPU kernel-equivalence tolerance table; update the Migration Guide
   / `.pyi` if any new binding callable is user-visible.
3. Update `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`: record that
   WP-036D closed the *inference/dynamics* Python GPU-path gap from audit
   `036b` §8; DV-005 (training-stack CUDA Burn backend) and DV-001 (Linux
   Triton runner) remain OPEN and are explicitly **not** closed by this WP.
4. Run documentation, link, quality, security, and the CPU acceptance-subset
   gates; confirm the latest `gpu.yml` run is green.
5. Write `DOCS/reports/036d-project-state.md` with measured metric trends
   (GPU tests activated, GPU-vs-CPU tolerances, CPU-suite non-regression,
   coverage), cumulative deviation ledger, amendments, risks, and trajectory
   verdict.
6. Confirm WP-036C (session 0144M) entry conditions and record maintainer
   approval before its S1 begins.
7. Update this session's status and the master register from verified
   evidence.

## Required outputs

- Updated READMEs and docs; CHANGELOG entry; warning-free docs gates.
- Approved `DOCS/reports/036d-project-state.md`.
- Green local gates over the batched WP-036D range; green `gpu.yml` run.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
correction cycle.

## Exit gate

All S4 artefacts committed and local gates green. WP-036D is closed; only
then may WP-036C (0144M) begin.
