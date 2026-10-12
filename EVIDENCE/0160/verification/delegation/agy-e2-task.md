# Cold self-audit (read-only) — EXP-002 E2 approval round, records and governance

Repository `C:\dev\PRIN`; working tree = commit `ed993e9` plus staged changes.
No shell, no edits; print the report to stdout. QUOTE VERBATIM with real line
numbers; label any paraphrase as such. Do not invent IDs, values or quotes —
earlier runs of yours did, and quote accuracy is part of how this review is
judged.

Diffs since commit `0d4278d`:
- `C:\Users\there\AppData\Local\Temp\claude\c--dev-PRIN\caa74057-f2dc-43bd-8cf8-b18f5c141339\scratchpad\e2\delta-records.diff`
- `...\scratchpad\e2\delta-code.diff` (same directory)

Read in full: `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/e2-review.md`,
`.../preregistration.md` (header, §8, §9, §10, §11.3), `DOCS/standards/Experimentation_Standards.md`,
`DOCS/standards/Development_Workflow_and_Audit_Standards.md` §3 and §8,
`DOCS/sessions/SESSION_REGISTER.md` (line 5 and rows 0159–0161), the 0159/0160/0161
session briefs under `DOCS/sessions/phase-7/`, `DOCS/PRIN_Project_Plan.md`
amendment rows #50/#51, `DOCS/audits/PR033-multi-review-audit.md` §12,
`EVIDENCE/0160/README.md`, `CHANGELOG.md` top entries.

Check, reporting concrete defects only:
1. Authority: is every approval recorded with the maintainer's verbatim words
   and date? Is anything claimed approved/ratified/accepted that the quotes do
   not cover? Is the delegation disclosed honestly (who decided, independence)?
2. Consistency: session statuses (0159 COMPLETE, 0160 COMPLETE, 0161 READY)
   agree across the briefs, the register, `DOCS/sessions/phase-7/README.md`,
   the EXP-002 README and CHANGELOG? Any record still saying DRAFT / NOT
   APPROVED / PLANNED for these sessions without a superseding note?
3. Scientific integrity: did any E2 edit change a hypothesis, prediction,
   population, threshold, sample, seed, statistic, abort criterion or cap?
   Does §11.3 fully bind E4/E5 to report both H3 policies? Is decision 9's
   reasoning consistent with Experimentation Standards §1 and §4 (HARKing,
   post-hoc labelling)?
4. Evidence: do the numbers in e2-review.md (28/28, 29,524 strings, Lean
   version, Z3 version, nightly durations 87/14 min) match the logs under
   `EVIDENCE/0160/verification/`? Any claim with no supporting file?
5. Stale text: anything still saying "hosted checks remain paused" without
   the #50 window, "15 figures" for EXP-002, or E1 "pending publication".
6. Relative links in changed/new Markdown: does each target exist?

End with a numbered list of findings (file:line, verbatim quote, why wrong,
fix) and a list of areas checked and found sound.
