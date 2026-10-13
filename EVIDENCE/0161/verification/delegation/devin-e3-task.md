# Cold self-audit (read-only) — EXP-002 E3 execution round: the per-record validation tooling and the raw records' structure

Repository `C:\dev\PRIN`; working tree = commit `89f21f5` (clean); execution source `R` = `fae24c4`.
Do NOT run shell commands or edit files. Open only the files named here. Print the report to stdout.

## HARD RULE — do not read experimental outcomes

E3 (execution) must not interpret results or compute any H1–H4 verdict. The result files hold the
experiment's observations, which nobody has examined yet.

- Do NOT open `benchmarks/results/EXP-002/RUN-*/api.json`, `conclusions.json` or `reproduction.json`, and
  nothing under `DOCS/test_and_benchmark_results/`. You MAY open every `campaign-metadata.json` and
  `manifest.json`, and everything under `EVIDENCE/0161/`.
- Do NOT compare or comment on equality or inequality between hashes, sizes or listing digests of different
  publication arms, and do not say whether anything "matches". That would be verdict leakage and counts as a
  defect of your report. If you see observation content anyway, do not quote or summarise it.

## What to read

Tools (all under `EVIDENCE/0161/verification/tools/`):
`validate_run_record.py` (revision 2), `validate_run_record.rev1.py`, `mutation_test.py`,
`crossleg_consistency.py`, `measure_bytes.py`, `staged_bytes_check.py`, `reconstruct_rev1.py`,
`make_sha256sums.py`, `run_leg.ps1`, `preflight_recapture.ps1`.
Their captured outputs: `EVIDENCE/0161/verification/legs/*` and `.../preflight/*`, `.../gate/G16-staged-bytes-check.txt`.
Context: `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/log.md` (§3–§7),
`preregistration.md` §4.2 and §5.5 (last paragraph: what "per-record validation" must cover),
`benchmarks/campaign/exp002_driver.py` functions `_admission`, `check_run_complete`, `run_registered`
(the driver itself is frozen and out of scope; read it only to judge whether the validator's checks are
independent of, and at least as strict as, the driver's own closure).

The brief's requirement for per-record validation, verbatim: "A nonzero exit or closure failure makes the
record inadmissible even if its status says COMPLETED. Independently check: complete metadata; the result
envelope; the exact declared artefact mapping; the run manifest; source, protocol and input identity; seed
(0,2); and the run directory holding only its sidecar, result and manifest. Do not judge whether outputs
\"match\"; that is E4. Never delete an ABORTED or incomplete RUN directory."

## Hunt for real defects, each with a concrete scenario

1. `validate_run_record.py`: which invalid record could it still pass (false pass)? Think of: extra keys,
   wrong types (bool vs int), duplicate JSON keys, symlinks/junctions/hidden files, a manifest that lists the
   right names but stale digests, protocol blob vs working file differences, `HEAD != R` after validation,
   a wrong-but-plausible `out_dir`, a sidecar that maps the wrong H-ids, timestamps out of order, a result
   envelope with an extra top-level key, API rows/claim cases/file records that are present but malformed.
   Is every check really evaluated (no vacuous `all([])`, no swallowed exception, no unreachable branch)?
2. Does the validator read or judge any experimental outcome (API `resolved`/`callable`, claim `observed`
   against `expected`, publication digests across arms)? It must only check structure and identity.
3. `mutation_test.py`: does each mutation really exercise the check it claims to (could a mutation fail for the
   wrong reason)? Which important mutations are missing?
4. `crossleg_consistency.py`: does it open any observation payload other than the `renderer` capture? Is
   comparing the whole `environment` block across legs a sound check for the abort criteria
   "renderer/font-stack change between compared runs" and "wrong backend/dtype"? Can it false-pass?
5. `staged_bytes_check.py`: could it false-pass (e.g. comparing a blob with itself), is `--head` correct, and
   does it handle CRLF/`-text` files byte-exactly?
6. `measure_bytes.py`, `preflight_recapture.ps1`, `run_leg.ps1`: any bug that would mis-record time, exit code,
   command line or UTC stamp? (`run_leg.ps1` computes the run ID from the launch time and runs the registered
   command; verify it matches protocol §5.5.)
7. The launch records (`legs/leg*.meta.txt`) vs the log: do command, UTC times, exit codes and walls agree?
8. `reconstruct_rev1.py`: is accepting a reconstruction only on a digest match sound?
9. Any command-injection, path-traversal or unsafe-write pattern in the shipped Python (Snyk Code reported
   none at the governed threshold; look for anything it could miss).

## By design — do NOT report

- Validator revision 2 differing from revision 1 (disclosed in log §4.2); `SystemExit`→`RuntimeError`.
- The scratch harness `run_gate.py` not being in the repo (explained in `EVIDENCE/0161/README.md`).
- The `Co-Authored-By: Claude Opus 5.5` commit trailer (maintainer's instruction).
- The driver, protocol and tests being unchanged and not reviewed here; `.gitattributes` choices.
- Identical or different listing digests between arms (out of scope — do not discuss).

## Output

Report each finding: severity (High/Medium/Low), file:line, a concrete scenario, why it is wrong, suggested
fix. Then list areas you checked and found sound.
