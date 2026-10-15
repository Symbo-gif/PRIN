# EVIDENCE/0159/verification/full-gate — index

Byte-exact copies of the closed session-0159 full-gate captures from
`DOCS/test_and_benchmark_results/0159-full-gate/` (ignored scratch root;
originals retained there). All files here are manifest-hashed.

## Contents

- `01-…08-*.log` — Python static legs (ruff check/format, mypy strict,
  interrogate, bandit).
- `09-pytest-fast.log`, `09b-*`, `09c-pytest-fast-rerun.log`, `09d-*` —
  fast-pytest leg, crash + retry + isolated diagnostics.
- `10-…19-*.log` — Rust legs (fmt, clippy, tests, llvm-cov, docs).
- `20-cargo-audit.log`, `21-/22-pip-audit*.log` — native dependency audits.
- `23-snyk-code.log`, `24b-*`, `24c-*` — Snyk Code scans (initial,
  corrected scope, final frozen test source) at medium threshold, all 0
  issues; `sast-copy-attestation.txt` proves scanned bytes equal reviewed
  bytes.
- `24-gitleaks.log`, `gitleaks-7859030.json` — full-history secret scan
  (redacted report); 1 checksum finding, exception pending.
- `25-pytest-full-*.log/.md` — interrupted full-suite raw prefix,
  augmented capture, resumption note (no cause attributed).
- `c01…c05-*.log`, `0159-driver-correction-coverage.json` — focused
  correction-verification runs, including preserved failed attempts. The
  c05 combined run exited 1 with three pre-packaging manifest-completeness
  failures; the later 17-test manifest check passed separately. The c05
  capture labels its start minute approximate and does not provide a host
  header; no exact start timestamp or complete header is inferred.
- `correction-source-hashes.txt` — final working-tree SHA-256 set for the
  corrected driver/test/protocol sources.
- `GATE-STATUS.md` — honest per-leg status matrix (incomplete/pending
  legs recorded, none relabeled).
- `09c-inventory-failure-facts.md` — verbatim lead root-cause facts for
  the 09c WP001 inventory failure.
- `0159-publication-validation-proposal.py.txt`,
  `0159-publication-validation-proof.py.txt`,
  `0159-publication-validation-proof.log` — lead-authored fixture recipes
  and their raw proof output. The proof ran once before integration via
  `.venv/Scripts/python -c "import runpy;
  runpy.run_path('DOCS/test_and_benchmark_results/0159-publication-validation-proof.py',run_name='__main__')"`
  (exit 0, tool-recorded); unheaded capture — command known, no exact
  start timestamp claimed. Not re-run after integration (its
  old-normalizer assertions intentionally predated the fix). No real RUN
  or reference input was involved.
