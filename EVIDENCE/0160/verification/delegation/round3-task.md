# Cold self-audit round 3 (read-only) — git-scoped WP-001 inventory

Repository `C:\dev\PRIN` (commit `ed993e9` + staged changes). No shell, no
edits; print the report to stdout. Quote verbatim with real line numbers.

Context: the local fast pytest suite twice crashed with a Windows access
violation inside `os.walk`, called from
`tests/test_wp001_baseline.py::test_repository_inventory_is_deterministic_and_separates_archive`.
Standalone reruns did not reproduce it; the native root cause is NOT proven.
The walk covered ~110,800 files (4.2 GB), mostly git-ignored scratch. The
mitigation makes `tools/wp001_baseline.py` inventory only git-visible files
(`git ls-files -z --cached --others --exclude-standard`) when the root is a
work-tree top level, and walk otherwise.

The full code diff is
`C:\Users\there\AppData\Local\Temp\claude\c--dev-PRIN\caa74057-f2dc-43bd-8cf8-b18f5c141339\scratchpad\e2\delta-code-r3.diff`.
Read it, then read `C:\dev\PRIN\tools\wp001_baseline.py` lines 1000-1140.
The records describing it are
`C:\dev\PRIN\DOCS\experiments\EXP-002-api-benchmark-result-and-reproduction-parity\e2-review.md` (end of section 7),
`C:\dev\PRIN\DOCS\audits\PR033-multi-review-audit.md` (end of section 12),
`C:\dev\PRIN\CHANGELOG.md` (the first "Fixed" bullet) and
`C:\dev\PRIN\EVIDENCE\0160\README.md`.

1. Is `_git_visible_files` / `_active_project_files` correct? Consider: the
   toplevel comparison on Windows (drive-letter case, forward vs back
   slashes, 8.3 short names, symlinked roots), deleted-but-tracked files,
   submodules or nested repositories, non-UTF-8 names, `core.quotepath`,
   excluded directories and files, archive/evidence roots, sort order and
   determinism, and every fallback path.
2. Is a subprocess call here safe (argv, no shell, timeouts, PATH lookup)?
3. Do the new tests actually exercise each branch they claim to, and could
   any be flaky or environment-dependent?
4. Do the records state the crash and the mitigation honestly (no claim that
   the root cause is proven or that the crash is fixed)?
5. Does the change alter any EXP-002 protocol, driver or registered input?

Report each finding with severity (High/Medium/Low), file:line and a
concrete failure scenario, or state that you found none. Keep it factual; do
not invent quotes or values.

Use only file-reading tools on the specific files named above. Do not run any
command, search tool that needs confirmation, or shell; never open a
directory path or probe whether a path exists. If a tool asks for
confirmation, skip that step and continue.
