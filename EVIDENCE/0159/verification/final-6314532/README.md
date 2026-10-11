# EVIDENCE/0159/verification/final-6314532 — index

Byte-exact copies of the final local-validation captures for session 0159,
run on source `63145325c01fd837fd55e2796ea0fa34aa7eb234`. Originals remain
in the external scratch root — `<EXTERNAL>` / `<EXT>` in log headers expands
to:

```text
C:\Users\there\AppData\Local\Temp\prin-0159-final-6314532-20261011T144627Z
```

All pytest legs ran with a process-local Git-Bash PATH prefix
(`C:\Program Files\Git\bin`) and `--basetemp=.pytest_basetemp`; no writes
were made inside the repository while any suite ran. Earlier 7859030 legs
(static, Rust, native audits) in `../full-gate/` remain valid for their
unchanged scopes; this directory covers the components that ran on 6314532.

## Files

- `00-environment.log` — tool/host metadata. **Partial capture:** it
  contains two failed shell-quoting attempts before the corrected,
  labeled OS/CPU/RAM section was appended; do not index it as a single
  clean exit-0 pass. No credentials were read or printed.
- `01-ruff-narrow.log` — ruff check + format on the 3 changed Python
  files: exit 0 / 0.
- `02-focused-pytest.log`, `focused-coverage.json` — focused 4-file gate:
  256 passed, driver coverage 99.61% (changed-driver scope only; DV-033
  remains OPEN).
- `03-pytest-fast.log` — FAST (`not slow and not gpu`): 3710 passed,
  178 skipped, 55 deselected, 59 warnings, 995.73s, exit 0.
- `04-pytest-full.log` — first FULL attempt: 5903 passed, 184 skipped,
  61 warnings, 1 fixture-setup ERROR (`PermissionError` WinError 32 on
  `.pytest_basetemp` cleanup; the lock holder is unproven), exit 1.
  Retained as a real nonzero attempt.
- `04b-error-diagnostic.log` — isolated rerun of the errored node:
  passed; diagnostic only, not a substitute for the leg.
- `04c-pytest-full-isolated.log` — supervised FULL retry: **5904 passed,
  184 skipped, 61 warnings, 1621.36s, exit 0**. Whole-`prin` coverage:
  7326/7727 = 94.810405% (terminal prints rounded `95`; the unrounded
  value is below 95 and DV-033 is not closed by it).
- `05-sphinx.log` — `-W --keep-going` HTML build to a fresh external
  output dir: succeeded, exit 0. The generated HTML tree is not
  duplicated into the repo.
- `06-governance.log` — deviation-ledger (142↔146 rows), DV gates
  (44 rows / 197 entries), session registration, skipif probes,
  wp001 check, `git diff --check`: all exit 0.
- `07-gitleaks.log`, `gitleaks-6314532.json`, `SESSION` — full-history
  secret scan (713 commits; empty SESSION file used as the
  process-local `GIT_SHALLOW_FILE`; repo not shallow, fsck clean):
  **exit 1, exactly 1 finding** — the known noncredential
  `reference_api_sha256` checksum at `EVIDENCE/0159/entry-state.json:87`
  (fingerprint on commit 78590305). Not a pass; the exception awaits
  explicit maintainer approval. No `.gitleaksignore` change.
- `08-manifest-tests-postpackage.log` — the post-packaging manifest
  regression run (17/17 passed, exit 0) against this bundle.
- `08b-snyk-manifest-test.log`, `sast-e-copy-attestation.txt` — Snyk
  Code at medium threshold on the changed supported source
  `tests/test_0159_manifest.py` only (byte-identical isolated copy;
  attestation binds the source SHA-256 `86e06981…` to the scanned
  bytes): 0 issues, exit 0. Unchanged driver/test/dependency scopes
  were not rescanned.
- `09-sphinx-postchangelog.log` — **TAIL EXCERPT ONLY**: the pipeline
  kept only the final stream lines of a post-CHANGELOG `-W` build that
  finished exit 0 (real recorded exit; not a full raw capture — the
  authoritative full capture is `10-…` below).
- `10-sphinx-final-fullcapture.log` — the fresh clean Sphinx
  `-W --keep-going` build after all document edits, **full stdout and
  stderr captured** (no filtering), output to the external
  `sphinx-html-final-fullcapture/` directory: build succeeded, exit 0.
- `11-manifest-tests-final.log` — 17 passed, exit 0 after the control
  captures were packaged. This log is recorded afterward; it does not
  claim to verify its own later addition. The final staged-blob check
  covers the complete record at commit preparation.
