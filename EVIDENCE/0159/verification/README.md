# Session-0159 verification evidence

Preserved verification logs for EXP-002 / C1 E1 (session 0159), host `HP`,
source baseline `da53ea11a3f38cd0d5c27c40bbefbeaf6d6dbf53` (the PR #32 merge
on `main`), branch `campaign/0159-exp002-e1`, under Plan amendments #48
(local-validation regime) and #49 (supervised-local-validation timeout
governance). Text artefacts only.

- `0159-focused-campaign-quality-gates.log` — prior unheaded tool capture:
  raw `pytest` output for `tests/test_campaign_quality_gates.py` (22 passed,
  3 warnings in 0.65 s; observed exit 0), captured 2026-10-11 on host `HP`
  with `.venv` Python, `--basetemp=.pytest_basetemp`, and a process-local
  Git-Bash PATH prefix. The capture carries no command/host/UTC/exit header
  and no run start time is asserted.
- `0159-focused-ea007-manifest.log` — prior unheaded tool capture: raw
  `pytest` output for `tests/test_ea007_manifest.py` (3 passed in 0.31 s;
  observed exit 0), same capture conditions and caveats.
- `0159-ps51-parse-check.log` — headed capture: Windows PowerShell 5.1
  (5.1.26100.9549) parse check, via `PSParser::Tokenize`, of the verbatim
  `AGENTS.md` supervised-validation `$previousPath`/`try`/`finally` example
  line and the existing ruff `--config "include = [...]"` gate line (0 parse
  errors each), plus a harmless `cmd /c echo` stub execution of the
  try/finally PATH wrapper (stub exit 0, PATH restored). No pytest run;
  source SHA `85b779297be0642f5c64853c1590ef341e7ff77e`, 2026-10-11T11:20:18Z,
  exit 0. **Provenance scope:** the recorded `85b…` HEAD is the
  attribute-only commit *plus the uncommitted* `AGENTS.md` working-tree
  edits being parsed — the log does not assert that commit `85b…` itself
  contained the new commands.
- `0159-ps51-parse-check.ps1` — byte-exact copy of the throwaway
  PowerShell driver that produced the log above, preserved so the invoked
  recipe can be reconstructed (original scratch path:
  `DOCS/test_and_benchmark_results/0159-ps51-parse-check.ps1`, gitignored).
- `0159-driver-initial-red-run.log` — retained raw diagnostic: the
  initial combined focused run (exit 1; 17 failures — two test-fixture
  defects in `tests/test_exp002_driver.py`, plus the then-unpackaged
  manifest expectations). Unheaded tool-overflow capture, no reconstructed
  timings; the fixture defects are recorded as test bugs, not driver
  defects. Retained per the no-silent-failure rule.
- `0159-driver-lint-type.log`, `0159-driver-pytest-coverage.log`,
  `0159-driver-coverage.json` — the first headed focused
  driver-validation batch (ruff check/format, `mypy --strict`, and the
  combined focused pytest+coverage run: 215 passed, 99.75 % package
  coverage of `exp002_driver.py`). Closed and immutable.
- `0159-driver-final-lint-type.log`,
  `0159-driver-final-pytest-coverage.log`,
  `0159-driver-final-coverage.json` — the post-review focused batch on the
  lead-corrected source (PDF-magic rejection and exact-`APPROVED` status
  match): 218 passed, 99.75 % coverage; see each log's header.
- `full-gate/` — the complete 7859030 local-gate capture set plus the
  publication-correction evidence: legs 01–25 (static, Rust, native
  audits, Snyk Code scans and copy attestations, the failed/interrupted
  fast/full attempts with diagnostics, the redacted gitleaks report),
  the c01–c05 correction-verification runs, `GATE-STATUS.md` per-leg
  matrix, `correction-source-hashes.txt`, the verbatim 09c inventory
  root-cause facts, and the lead-authored validation recipes/proof log.
  See `full-gate/README.md` for the per-file index.
- `final-6314532/` — the final local-validation captures on source
  `63145325c01fd837fd55e2796ea0fa34aa7eb234`, byte-exact copies of the
  external-run artifacts (external root stated in `final-6314532/README.md`):
  ruff/focused gate (256 passed, driver 99.61%), FAST (3710/178/55d, exit 0),
  FULL (04 exit 1 setup-lock error; 04c **5904 passed, 184 skipped,
  61 warnings, exit 0**; whole-`prin` coverage 7326/7727 = 94.810405% —
  the rounded `95` shown is not an unrounded ≥95 pass), Sphinx `-W` build,
  governance battery (all exit 0) and the full-history gitleaks scan
  (exit 1 — one known checksum finding, exception pending). The
  post-packaging control records (manifest test run, the
  manifest-test-file Snyk Code scan with its byte-identity attestation,
  and the Sphinx builds — `09` a retained tail excerpt, `10` the
  authoritative full capture) are indexed inside
  `final-6314532/README.md`.
- `source-hashes.txt` — working-tree SHA-256 byte hashes of the driver,
  the two new test files, and the lead-authored pre-registration, plus
  tool versions and the `git status` surface at capture. Working-tree
  bytes, not commit objects; no scan or gate claim is made by it.
- `SHA256SUMS.txt` — SHA-256 inventory of every hashed file in this
  directory (including the frozen `../entry-state.json`), excluding itself.
  Verify with `sha256sum -c SHA256SUMS.txt` from this directory.
  **Mutability:** raw capture files are immutable once committed; the
  indexed narrative (`README.md` files) may change, and when it does this
  manifest is regenerated in the same change — manifest lines are not
  promised to be never-rewritten.
