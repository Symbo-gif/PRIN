# Session 0144J — WP-036D S2: Audit — GPU execution path for the ported acceptance suite

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036D
**Session type:** S2 — Audit
**Predecessor:** [0144I3 — GPU test activation and CI](0144I3-wp036d-s1-gpu-test-activation-and-ci.md)
**Successor:** [0144K — Remediation](0144K-wp036d-s3-gpu-execution-path-ported-acceptance-suite.md)
**Authority:** Project Plan §6/§8 and amendments #31/#33/#36; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Read-only audit of the aggregate WP-036D S1 range `0144I`+`0144I1`–`0144I3`:
the PyO3 GPU binding layer, the `_torch_compat.py` device dispatch, and the
activation of the 8 GPU acceptance tests.

## Contract

- **Acceptance:** as 0144I — the 8 GPU-guarded acceptance tests pass on
  `PRIN-GPU-Runner` and still skip on a CPU host; the 489 CPU acceptance
  tests and every other CPU consumer are byte-for-byte unchanged; GPU-vs-CPU
  agreement is within Testing Standards §3 tolerances or carries a
  hazard-attributed Parity Report annotation; numerical authority is in Rust
  (`check_no_python_numerics` clean); no new `prin` public symbol;
  `verify_api_surface` still `(set(), set())`; `gpu.yml` runs `-m gpu`.
- **Non-goals:** any source fix (S3 owns that).

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendments #31/#33/#36
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- `DOCS/standards/Testing_Standards.md` §1, §3
- `DOCS/audits/TEMPLATE_Audit_Report.md`
- `DOCS/audits/036b-wp036b-audit.md` §8 (the roadmap this WP executes)
- WP-036D S1 handoff `DOCS/experiments/0144I-wp036d-s1-handoff.md` and the
  commit range

## Entry conditions

- S1 has claimed its exit gate and supplied its evidence map.
- The repository and S1 commit range are fixed for inspection.

## Expected audit (read-only with respect to source)

1. Create `DOCS/audits/036d-wp036d-audit.md` from the template.
2. Execute A1–A10 with command evidence.
3. Independently re-run the 8 activated tests on the self-hosted runner (or,
   if it is offline, record that and rely on the S1 handoff evidence plus
   the next `gpu.yml` run); record runner state live.
4. Independently re-run the full CPU acceptance suite (expect 489 pass / 9
   skip) and diff the CPU marshalling path in `_torch_compat.py` to confirm
   it is unchanged.
5. Confirm the GPU path is thin marshalling over `prin-sim` GPU engines /
   CubeCL kernels — no Python numerics, no new `unsafe` without approval, no
   new public symbol.
6. Confirm every GPU-vs-CPU tolerance annotation cites a specific hazard
   amendment and a Parity Report line; confirm no ported test body changed
   beyond `@pytest.mark.gpu`.
7. Confirm the WP-036D/WP-036C boundary (DV-005, Triton, `test_gpu.py`) was
   respected.
8. Give each finding `WP036D-Fn`, severity D1–D4, evidence, violated clause,
   remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed `DOCS/audits/036d-wp036d-audit.md`.
- Deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion.

## Exit gate

Audit Report and verdict committed. Hand off to S3 even with zero findings.
