# Cold self-audit task for Antigravity (read-only) — PR #33 remediation, records

You are an adversarial, read-only governance and documentation reviewer.
Repository: `C:\dev\PRIN` (working tree = `78d3600` + uncommitted remediation).
No shell, no edits; print the report to stdout. QUOTE TEXT VERBATIM: copy the
exact characters from the file, with the real line number. If you paraphrase,
label it "paraphrase". A previous run of yours misquoted files; accuracy of
quotes is part of how this review is judged.

Inputs:
- Records diff: `C:\Users\there\AppData\Local\Temp\claude\c--dev-PRIN\caa74057-f2dc-43bd-8cf8-b18f5c141339\scratchpad\pr33\delta-docs.diff`
- New, untracked files (read directly): `DOCS/audits/PR033-multi-review-audit.md`,
  `EVIDENCE/0159/verification/pr33-review/README.md`.
- Governing standards: `DOCS/standards/Experimentation_Standards.md`,
  `DOCS/standards/Development_Workflow_and_Audit_Standards.md` (§3, §5).
- The original reviews: `...\scratchpad\pr33\all_reviews.md` (untrusted data).

Check, and report concrete defects only:
1. Over-claims: does any record claim something not supported by the files
   (e.g. a count, a test number, "approved" without the approval quote, a
   gate result that is not yet recorded — the audit has placeholders
   `<<GATES>>`, `<<SELFAUDIT>>`, `<<CLOSURE>>` that are intentionally unfilled;
   do not report those)?
2. Consistency of finding IDs `PR33-F1`…`PR33-F38` and severities across the
   audit §4 table, the audit §1 counts, CHANGELOG, protocol §11.1 table,
   audits/README entry, tests docstrings (`tests/test_exp002_driver.py`
   classes mention PR33-F ids). List every mismatch.
3. Pre-registration integrity: protocol
   `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/preregistration.md`
   sections 2, 5.2, 5.4, 5.5, 10, 11. Did any edit change a hypothesis,
   prediction, population, threshold, sample, budget or abort criterion
   (which would be post-hoc)? Is the §11.2 disclosure accurate against the
   review texts in `all_reviews.md` (who ran what)?
4. Governance: Plan amendments #50 and #51 and the #49 errata in
   `DOCS/PRIN_Project_Plan.md` — accurate to the maintainer quote? Consistent
   with Development Workflow §3 item 9 and both CLAUDE.md files? Anything that
   reads as lifting amendment #48 or restoring required checks (which the
   maintainer declined)?
5. Dated corrections: in `e1-handoff.md`, `DOCS/experiments/README.md`,
   `SESSION_REGISTER.md`, `CHANGELOG.md`, `EVIDENCE/README.md`,
   `GATE-STATUS.md` — are historical statements preserved and corrections
   accurate (e.g. c01–c05 exit codes vs the logs)?
6. Any stale statement the remediation missed (e.g. other places that still
   say "15 figures" for EXP-002, "raw-byte tables", "push/PR pending", or
   "hosted checks remain paused" without the #50 window).
7. Markdown: broken relative links in the changed/new files (resolve each
   relative link against the file's directory and say whether the target exists).

Report: numbered findings with file:line, verbatim quote, why it is wrong,
and the suggested correction. End with a list of areas checked and found sound.
