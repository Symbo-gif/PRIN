# EXP-002 D1 S2 — Correction audit

**Status:** OPEN — blocked on S1
**Triggering deviation:** `EXP-002 H3 REFUTED` (campaign plan §10.4 D1; pre-registration §4.3)
**Blocked numbered session:** `0164` (EXP-003 E1), and every later campaign session (`0165`–`0194`)
**Opened by:** session `0163` (EXP-002 E5), 2026-10-14 UTC
**Predecessor:** [S1 — correction implementation](2026-10-14-exp002-d1-s1-correction-implementation.md)
**Successor:** [S3 — correction remediation](2026-10-14-exp002-d1-s3-correction-remediation.md)
**Governing record:** [EXP-002 E5 report](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md) §8

## Expectation

Read-only audit of the correction against A1–A10, the triggering experiment evidence, and the violated requirement; issue findings and verdict.

## Exit evidence

Record commands, artefacts, approvals, commits, and handoff in the correction
WP's audit and Project State Report. The blocked session remains blocked until
all four conditional sessions close.

## Audit scope specific to this correction

Beyond the standard checklist A1–A10, the audit independently verifies:

1. **The reproduction came first.** The failing regression/parity tests S1 cites existed and failed on the pre-fix tree; the auditor re-runs them on the pre-fix state rather than accepting the claim on authority.
2. **The root cause is established, not asserted.** Every one of the 9 differing figure stems (`18` files: `.pdf` and `.png` of figures 5, 7, 8, 9, 10, 11, 12, 14, 15) is accounted for. If S1 concluded that any part of the PRINet 3.0 reference generator is the defective side (campaign plan §10.4 item 3), the audit verifies the EMA-style mathematical claim and its Z3/SymPy verification directly; an inspection argument is not sufficient.
3. **No regression on the already-matching outputs.** All `11/11` `.tex` tables and the `5/14` already-matching figures (`fig2`, `fig3`, `fig4`, `fig6`, `fig13`), as well as PRIN-versus-PRIN raw-byte determinism (H4), remain intact.
4. **EXP-002's record is untouched.** No file under `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/` (except any dated erratum appended at S4) or `benchmarks/results/EXP-002/RUN-*` was modified; `verify_manifest` passes on all five run directories, and `analysis/exp002_e4_analysis.py` (`3731fc2`) still reproduces the seven E4 outputs and `report-manifest.json` (`6b15dcc1…68781`) byte-for-byte.
5. **Coding Standards §6 evidence is real.** Snyk Code (and Snyk Open Source + ecosystem-native audits if any dependency changed) was run on the exact changed files, or any unavailable scan is reported as blocked — never claimed.

## Verdict rule

`PASS` (no findings above D4), `PASS-WITH-FINDINGS` (none D1), or `FAIL` (any D1, or systemic drift). A `FAIL` sends every finding to S3; no fix is committed during this read-only audit session.
