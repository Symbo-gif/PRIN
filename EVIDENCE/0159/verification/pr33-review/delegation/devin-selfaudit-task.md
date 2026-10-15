# Cold self-audit task for Devin SWE-2 (read-only) — PR #33 remediation, code

You are an adversarial, read-only code reviewer. Repository: `C:\dev\PRIN`
(working tree = commit `78d3600` + uncommitted remediation). Do NOT run shell
commands, do NOT edit files. Print the report to stdout.

Inputs:
- Driver diff: `C:\Users\there\AppData\Local\Temp\claude\c--dev-PRIN\caa74057-f2dc-43bd-8cf8-b18f5c141339\scratchpad\pr33\delta-driver.diff`
- Test diff: `...\scratchpad\pr33\delta-tests.diff` (same directory)
- Current files: `benchmarks/campaign/exp002_driver.py`, `tests/test_exp002_driver.py`,
  `tests/test_0159_manifest.py`, `EVIDENCE/0159/verification/pr33-review/proof_defect_catching.py`,
  `EVIDENCE/0159/verification/pr33-review/proof_plugin.py`, `tools/reproduce.py`.
- Finding list and intended fixes: `DOCS/audits/PR033-multi-review-audit.md` §4.

Context: EXP-002 is a DRAFT pre-registered experiment. The driver collects
observations; it must fail closed (DriverError) on anything outside the
registered contract, and it must never make two different scientific outputs
compare equal. Status: 303 driver tests + 20 manifest tests pass locally; a
mutation proof reports 19/19 caught.

Hunt for REAL defects introduced or left by the remediation, e.g.:
1. `_canonical_info` / `_pdf_value_end`: can any input make two PDFs with
   different scientific content (outside the Info object) normalize equal?
   Can a crafted Info body hide bytes from comparison (e.g. a value token that
   swallows following entries, unbalanced parentheses, escapes, `>>` inside a
   string, a greedy `(.*)>>` mis-split)? Can a valid Matplotlib Info dict be
   rejected (false DriverError)? Is removing a key whose name is written with
   `#xx` escapes a problem?
2. `_validate_png` colour rules: any valid Matplotlib RGBA/RGB PNG wrongly
   rejected? Any PNG-spec rule misstated (bit depths per colour type; PLTE
   optional for types 2/6; tRNS allowed for 0/2/3)?
3. `_check_provenance`: is `git merge-base A B == A` a correct ancestry test?
   What if `source_sha` is not a commit known to the repo? What exceptions can
   escape (e.g. `subprocess.TimeoutExpired`, UnicodeDecodeError in
   `_approval_date` on non-UTF-8 bytes)? Is ordering inside `check_run_complete`
   safe?
4. `_check_observations`: any genuine record produced by `collect_api`,
   `collect_conclusions` or `collect_reproduction` that the new checks would
   wrongly reject (compare key sets exactly: archived_* extra keys on table
   rows; rows sorted order vs `sorted(expected)`; `right_path` None; C02 rows
   carry extra keys `K`, `alpha_radians`)? Any TypeError/KeyError path that
   escapes as non-DriverError?
5. `_admission`: does `git ls-files --others --exclude-standard -- . ':!benchmarks/results' ':!<log>'`
   behave as intended? Does the `:(glob)*.py` pathspec match only top-level?
   Could the whole-checkout untracked rule make E3 impossible in normal use
   (e.g. files the driver itself writes before admission)?
6. `run_registered` restructure: any path where a RUN directory is created but
   no ABORTED record is written? Is `OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)`
   safe w.r.t. symlinks? Does closure's directory inventory reject a genuine
   run (e.g. a `__pycache__` or the manifest temp file)?
7. Tests: any test that would pass vacuously (e.g. asserts on a fixture that
   never exercises the new code path; `pytest.raises(match=...)` matching a
   different error than intended; the real-git tests skipping silently on
   CI; symlink tests that would fail on Linux CI)? Any test that depends on
   Windows-only behaviour and would FAIL on hosted ubuntu runners
   (hosted CI is about to run on ubuntu-latest and windows-latest)?
8. Mutation proof: could a mutant "fail" for an unrelated reason (import
   error) and be counted as caught?

By design — do NOT report: the driver refusing to run while DRAFT; synthetic
fixtures only; the global storage-cap coupling across runs (registered
campaign-wide caps); not counting publication files at closure (H3
falsifier must stay admissible); leaving `_snapshot` JSON errors as
ValueError; frozen evidence snapshots unchanged.

Report each finding as: severity (High/Medium/Low), file:line, the concrete
failing input or scenario, and why. Say "no finding" for areas you checked
and found sound. Be precise; do not speculate without a concrete scenario.
