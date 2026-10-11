# 25-pytest-full — resumption note

## What is recorded

- `25-pytest-full-raw-prefix.log` — byte-identical raw capture of the original
  full-suite invocation on `78590305e1c0a78d92153ef2a55a9e76aeb7af79`, exactly
  as emitted by the `_run-leg.ps1` wrapper. It ends mid-stream at the last
  recorded progress line (`53%`, `tests/test_migration_guide_consolidated.py`
  block) with no `UTC-END`/`EXIT_CODE` trailer.
- `25-pytest-full-interrupted.log` — the same capture with a later
  provenance annotation appended (first-recovery note). Retained unchanged
  for transparency.

## What the absence of output does NOT establish

- The original full-suite process was absent at the first recovery
  inspection (no python/pytest process; the tool-shell handle `778ea7` was no
  longer live).
- The last recorded progress is `53%`. **No exit code, no end timestamp, and
  no mechanism was captured.** The cause of termination is unknown and is
  **not** attributed to a timeout, a test crash, coverage tooling, or any
  other specific mechanism — there is no evidence discriminating among
  these.
- `53%` is not a pass, a partial result, or an inferred terminal state; it is
  only the last written progress line.

## Handling

- A fresh full-suite invocation is **PENDING** the new reviewed clean
  checkpoint on the finalized source. The earlier 25b plan was paused
  before any resumption ran; no `25b-*` log exists and no resumption
  timestamp or terminal status is claimed. The original raw prefix and
  the augmented capture above are preserved unmodified.
- No process was terminated by this inspection.
