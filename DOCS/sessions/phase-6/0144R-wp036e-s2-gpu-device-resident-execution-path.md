# Session 0144R — WP-036E S2: Audit — GPU device-resident execution path

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036E
**Session type:** S2 — Audit
**Predecessor:** [0144Q — Coding](0144Q-wp036e-s1-gpu-device-resident-execution-path.md)
**Successor:** [0144S — Remediation](0144S-wp036e-s3-gpu-device-resident-execution-path.md)
**Authority:** Project Plan §6/§8 and amendments #31/#33/#36/#37/#38; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Read-only audit of the aggregate WP-036E S1 range (`0144Q` + any
`0144Q1`–`0144Qn`): the `prin-kernels` device-handle dispatch layer, the
`prin-sim` persistent device buffers, the DV-003 on-device `f64` combine, the
`prin-py` zero-copy DLPack path, the `_torch_compat.py` upgrade, and the
activation of `test_sparse_vram_subquadratic`.

## Contract

- **Acceptance:** as `0144Q` — all 8 GPU acceptance tests pass on
  `PRIN-GPU-Runner` and still skip on a CPU host; DV-030 and DV-003 are
  closed (device-resident buffers; on-device combine; device-event timing
  recorded); the CPU marshalling path and the 489 CPU acceptance tests are
  byte-for-byte unchanged; GPU-vs-CPU agreement is within Testing Standards
  §3 tolerances or carries a hazard-attributed Parity Report annotation;
  numerical authority is in Rust (`check_no_python_numerics` clean); the
  host-slice `prin-kernels` API still exists as a thin wrapper (one algorithm,
  one implementation); no new `prin` public symbol; `verify_api_surface` still
  `(set(), set())`; `unsafe` confined to audited FFI modules with `// SAFETY:`
  blocks and recorded second-reviewer sign-off.
- **Non-goals:** any source fix (S3 owns that).

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendments #31/#33/#36/#37/#38
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §4 (A1–A10)
- `DOCS/standards/Coding_Standards.md` §1, §2.1/§6.1; `Testing_Standards.md` §1, §3
- `DOCS/audits/TEMPLATE_Audit_Report.md`
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-003, DV-030
- WP-036E S1 handoff `DOCS/experiments/0144Q-wp036e-s1-handoff.md` and the
  commit range

## Entry conditions

- S1 has claimed its exit gate and supplied its evidence map.
- The repository and S1 commit range are fixed for inspection.

## Expected audit (read-only with respect to source)

1. Create `DOCS/audits/036e-wp036e-audit.md` from the template.
2. Execute A1–A10 with command evidence.
3. Independently re-run the 8 activated GPU tests on the self-hosted runner
   (or, if it is offline, record that and rely on the S1 handoff evidence
   plus the next `gpu.yml` run); record runner state live.
4. Independently re-run the full CPU acceptance suite (expect 489 pass / 9
   skip minus the now-activated `test_sparse_vram_subquadratic`) and diff the
   CPU marshalling path in `_torch_compat.py` to confirm it is unchanged.
5. Confirm the `prin-kernels` host-slice entry points are retained as thin
   wrappers over the device path (no duplicated algorithm); confirm
   `prin-sim` engines hold device buffers across `step` and download only on
   `to_host()`.
6. Confirm the DV-003 on-device `f64` combine is in place and device-event
   timing over the 8-launch sequence is recorded with a stated residual.
7. Confirm the zero-copy DLPack path performs no host round-trip for a CUDA
   input; confirm no Python numerics, no new `unsafe` without approval, no
   new public symbol.
8. Confirm every GPU-vs-CPU tolerance annotation cites a specific hazard
   amendment and a Parity Report line; confirm `test_sparse_vram_subquadratic`
   passes at `* 0.10` (not a loosened bound) or that S1 correctly escalated a
   documented alternative.
9. Confirm the WP-036E / DV-005 / Triton / exponential-integrator boundary
   was respected.
10. Give each finding `WP036E-Fn`, severity D1–D4, evidence, violated clause,
    remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed `DOCS/audits/036e-wp036e-audit.md`.
- Deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion.

## Exit gate

Audit Report and verdict committed. Hand off to S3 even with zero findings.
