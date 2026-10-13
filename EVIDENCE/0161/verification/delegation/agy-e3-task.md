# Cold self-audit (read-only) — EXP-002 E3 execution round: the log, the records and the per-record validations

Repository `C:\dev\PRIN`; working tree = commit `89f21f5` (clean), whose parent chain is
`fae24c4` (the execution source `R`) → `92cf696` (.gitattributes rule) → `89f21f5` (E3 records).
You have NO shell and may not edit anything. Print the report to stdout.
QUOTE VERBATIM with real line numbers; label any paraphrase as such. Do not invent IDs, values or
quotes: quote accuracy is part of how this review is judged.

## HARD RULE — do not read experimental outcomes

E3 is execution only. Its prohibition is: no interpretation of results and no H1–H4 verdict. The
raw result files hold the experiment's observations, and nobody has examined them yet.

- Do NOT open `benchmarks/results/EXP-002/RUN-*/api.json`, `conclusions.json` or `reproduction.json`,
  and do not open anything under `DOCS/test_and_benchmark_results/`. You MAY open every
  `campaign-metadata.json` and `manifest.json`.
- Do NOT compare or comment on equality or inequality between any listing digests, hashes or sizes of
  different publication arms, and do not say whether anything "matches" or "differs". Any such remark is
  verdict leakage and will be treated as a defect of your report.
- If you nevertheless see observation content, do not quote, summarise or allude to it.

## What to read

Diffs from the execution source `R` = `fae24c4` to `89f21f5`:
- `C:\Users\there\AppData\Local\Temp\claude\c--dev-PRIN\8a021180-4f6b-439e-9fe7-62b13011e219\scratchpad\e3\delegation\delta-name-status.txt`
- `C:\Users\there\AppData\Local\Temp\claude\c--dev-PRIN\8a021180-4f6b-439e-9fe7-62b13011e219\scratchpad\e3\delegation\delta-records.diff`
  (records and docs only; raw run files and `EVIDENCE/0161/verification` are excluded from the diff)

Read in full:
- `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/log.md` (the E3 log under review)
- `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/README.md` (incl. the new
  "E3 to E4 handoff" section)
- `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/e2-review.md` (§6 and §8 = the E3
  checklist) and `.../preregistration.md` (§4.2 abort criteria, §5.5 procedure, §7, §9, §11.3)
- the user-facing session brief requirements, restated here: log per leg = UTC start/end, operator
  MichaelMaillet, exact command, run ID, exit code, elapsed wall time, anomalies, abort trips, and the
  publication listing digest for the three publication legs; hosted run IDs, head SHAs and durations for `R`;
  the aggregate CPU wall against the ≤ 12 h cap; tracked byte totals against the caps (≤ 2 MiB per run,
  ≤ 10 MiB new artefacts, ≤ 64 MiB campaign); no protocol/driver/hypothesis/scientific-input change; no
  cherry-picking; no deleted or edited run; no verdicts
- `DOCS/sessions/phase-7/0161-*.md`, `0162-*.md`, `DOCS/sessions/SESSION_REGISTER.md` (line 5 and rows
  0159–0163), `DOCS/sessions/phase-7/README.md`, `CHANGELOG.md` (top two entries),
  `benchmarks/results/EXP-002/README.md`, `benchmarks/campaign/README.md` (the `exp002_driver.py` row and the
  note ending "Session 0161"), `DOCS/experiments/README.md` (the last two EXP-002 paragraphs)
- `EVIDENCE/0161/README.md`, `EVIDENCE/0161/verification/SHA256SUMS.txt`, and the launch records and
  transcripts under `EVIDENCE/0161/verification/legs/` and `.../preflight/` and `.../gate/` (the `.meta.txt`,
  `.validation*.txt`, `.mutation-selftest*.txt`, `crossleg.txt`, `bytes-after-legs.txt`, `G*.log`, `R*.log`)

## Check, reporting concrete defects only

1. Completeness of the log against the required fields above, for each of the five legs.
2. Consistency between log numbers/hashes/times and the evidence files (run IDs, UTC times, wall times,
   exit codes, file sizes and SHA-256 of the three files in each run directory as printed in the
   `*.meta.txt`/transcripts, validation counts 69/67/73/73/73, cumulative and aggregate wall arithmetic,
   byte totals, gate counts). Recompute every sum you can.
3. Claims without support: every assertion in log §2 (pre-flight), §6 (gate), §7 (scans and caps) and in the
   README handoff — is there a file in the repo that supports it? Anything that reads as a result,
   an interpretation or a verdict?
4. Scientific integrity: does anything in the diff change the protocol, the driver, the tests, a registered
   input, a hypothesis, a prediction, a population, a threshold, a seed, a statistic, an abort criterion or a
   cap? (Use `delta-name-status.txt`.) Is the freeze statement correct? Is "no rerun, no abort, no D1"
   supported?
5. Consistency of session statuses across the 0161/0162 briefs, the register, the phase-7 README, the
   EXP-002 README, the CHANGELOG and the two benchmarks READMEs; stale text still saying E3 is READY /
   "no run has executed" / "SKELETON" for EXP-002 without a superseding note. (The 0160-era paragraphs that
   say "READY" carry a dated update; judge whether the note is sufficient.)
6. Relative links in changed/new Markdown: does each target exist? Is the anchor in the 0161 brief's link
   `README.md#e3-to-e4-handoff-session-0161-2026-10-12-utc` consistent with the heading it points to?
7. Honesty of the disclosures in log §1 (R against the approval commit), §2.6 (installed extension predates
   later Rust commits; second `.pth`; probes), §4.2 (validator revision), §6 (kept failures, the
   PowerShell/WSL `bash` finding, the Snyk finding and the uncommitted scratch harness), and the
   operator/executor statement at the top of the log.

## By design — do NOT report

- The commit trailer `Co-Authored-By: Claude Opus 5.5` on commits made by a Claude Sonnet 5.5 session: the
  maintainer instructed that exact trailer; the log and commit bodies disclose the executing model.
- The scratch gate harness (`run_gate.py`) not being committed: explained in `EVIDENCE/0161/README.md`
  and log §6.1.
- `log.md` being long, or containing a tracker table whose single row says "no leg run yet" (append-only
  design; the full table is in §5).
- The raw result files being CRLF and `manifest.json` LF (driver behaviour; `.gitattributes` keeps bytes).
- Hosted-CI results for the new head not yet being recorded (they run now; a follow-up commit records them).
- Anything about the driver, the protocol text or the E2 decisions: frozen, out of scope for E3.

## Output

A numbered list of findings (file:line, verbatim quote, why wrong, suggested fix, your confidence), then a
list of areas checked and found sound. If you find nothing in an area, say so explicitly.
