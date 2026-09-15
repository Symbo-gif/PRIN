# Session 0144Z — WP-036G S2: Audit — Deferred-Validation register consolidation and permanent dispositions

**Status:** COMPLETE (2026-09-15) — verdict PASS (zero findings), see `DOCS/audits/036g-wp036g-audit.md`.
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036G
**Session type:** S2 — Audit
**Predecessor:** [0144Y — Coding](0144Y-wp036g-s1-dv-register-consolidation-and-permanent-dispositions.md)
**Successor:** [0144AA — Remediation](0144AA-wp036g-s3-dv-register-consolidation-and-permanent-dispositions.md)
**Authority:** Project Plan §6/§8 and amendment #38; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Read-only audit of the WP-036G S1 range: the per-row DV dispositions, the
`chacha20` register row, the dormant `gpu-triton.yml`, the two
test-fragility resolutions, the re-verification evidence bundle, and the
draft Phase 7 entry statement.

## Contract

- **Acceptance:** as `0144Y` — every open DV item has a dated disposition in
  exactly one valid class; each permanent disposition names its standing
  governance mechanism; each standing-external disposition cites re-verified
  evidence and asserts "not a Phase 7 entry blocker"; the `chacha20` row is
  a complete DV-008-class entry; DV-010 is confirmed owned by WP-038 S1 and
  DV-027 by EMA-006; the two test-fragility items are fixed with regression
  coverage or documented as CI-authoritative with an explicit tolerance; no
  new numerics or public API; `check_dv_register_gates.py` and
  `check_no_python_numerics.py` pass.
- **Non-goals:** any source or register fix (S3 owns that).

## Required reading

- `DOCS/PRIN_Project_Plan.md` §5, §8.3 amendment #38
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §4 (A1–A10), §5
- `DOCS/standards/Coding_Standards.md` §6; `Testing_Standards.md` §1
- `DOCS/audits/TEMPLATE_Audit_Report.md`
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` (post-S1 state) and the
  DV-004/R35, DV-021/#30 disposition precedents
- WP-036G S1 handoff `DOCS/experiments/0144Y-wp036g-s1-handoff.md`;
  `EVIDENCE/0144Y-wp036g-s1-dv-reverification/`

## Entry conditions

- S1 has claimed its exit gate and supplied its evidence map.
- The repository and S1 commit range are fixed for inspection.

## Expected audit (read-only)

1. Create `DOCS/audits/036g-wp036g-audit.md` from the template.
2. Execute A1–A10 with command evidence (A6 especially — re-run
   `cargo audit` / `pip-audit` / Snyk independently and compare with the S1
   bundle).
3. Verify each DV row's disposition class is valid and its evidence chain
   resolves; verify no permanent disposition hides an item that a WP could
   actually close.
4. Verify the `chacha20` row meets the Coding Standards §6.2 advisory-
   governance bar (visibility, threat assessment, compensating control,
   maintainer-approval placeholder for S4).
5. Verify `gpu-triton.yml` is syntactically valid, dormant (no schedule/push
   trigger that would run on the current Windows runner), and documented.
6. Independently re-run the two named fragile tests (`test_process_frame_
   gradcheck_with_prev_slots`; `test_no_gpu_throughput_regression`) enough
   times to confirm the S1 resolution holds, or confirm the documented
   CI-authoritative disposition is explicit.
7. Verify `check_dv_register_gates.py` passes and no DV status cell was
   edited to `CLOSED`/`SATISFIED` without an evidence chain.
8. Verify the draft Phase 7 entry statement enumerates every remaining OPEN
   item.
9. Give each finding `WP036G-Fn`, severity D1–D4, evidence, violated clause,
   remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed `DOCS/audits/036g-wp036g-audit.md`.
- Deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source or register fix, plan rewrite, finding suppression, or evidence-free
assertion.

## Exit gate

Audit Report and verdict committed. Hand off to S3 even with zero findings.
