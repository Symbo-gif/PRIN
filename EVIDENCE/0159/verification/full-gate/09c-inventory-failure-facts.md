# 09c inventory failure — lead root-cause facts (verbatim)

Source: lead-provided facts, 2026-10-11 UTC, recorded verbatim. This note does
not overwrite or annotate `09c-pytest-fast-rerun.log`; it is the operator
record for the WP001 determinism failure in that leg.

## Lead-provided facts (verbatim)

- The lead created TWO proof/source Python files DURING the 09c inventory
  window: files created UTC 13:44:29.581844 and 13:47:06.002429; final
  sizes 7368+5607=12975B, lines 183+147=330.
- The 09c failed inventory diff was +2 files, +2 text files, +330 lines,
  +16257B. These two files account EXACTLY for the file/text/line
  increments; the lead owns contributing to the failure.
- The byte increment exceeds the file bytes by 3282, so the entire byte
  change is NOT claimed explained; live 09c faulthandler-output log growth
  is plausible but not yet proven.
- No 'recovered transient unknown files' exoneration applies beyond the
  writes that predate the test; no attribution to an earlier access
  violation or interruption is made.
- `tools/wp001_baseline.py` correctly detects a changing scanned
  population; neither the tool nor the assertion is weakened.

## Consequence

- The 09c fast rerun result (3671 passed / 1 failed — this inventory test)
  is recorded as-is. The isolated diagnostics (09b, 09d) passed but do
  not substitute for the leg.
- Any upcoming large pytest run MUST log outside the repository (unique
  OS-temp directory, parent verified), with NO writes anywhere in the
  scanned repo during the run — no drafts, packaging, log copies, notes,
  or report updates. All log copying/headers/documentation happens after
  the process finishes.
