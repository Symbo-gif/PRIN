# EVIDENCE/exp002-r1-e1/ — Verification evidence for `EXP-002-r1` E1

**Stage:** `EXP-002-r1-E1` (Pre-registration and Driver Preparation, track C1).<br>
**Date:** 2026-10-20 UTC.<br>
**Branch:** `campaign/exp002-r1-e1` (base `M = 5677858c15d784d881b23d43dff5029d199b0a18`).<br>
**Experiment record:** [`DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/`](../../DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md).

Under the **Re-run (`-r1`/`-rN`) Namespace & Evidence Isolation Rule** (campaign
plan §7.1, §10.4 item 4, amendment #10), all stage verification evidence for
`EXP-002-r1` E1 lives in this dedicated `EVIDENCE/exp002-r1-e1/` directory and
never modifies `EVIDENCE/0159/`..`0163/` or `EVIDENCE/exp002-d1-s1/`..`s4/`.

## Indexed files

| File | Description |
|---|---|
| [`README.md`](README.md) | This evidence index |
| [`check-ci-green-5677858c.txt`](check-ci-green-5677858c.txt) | Verbatim output of `.venv\Scripts\python.exe tools/check_ci_green.py 5677858c15d784d881b23d43dff5029d199b0a18` at E1 entry (`RESULT: all required workflows green`, exit `0`) |
| [`dv047-closure.txt`](dv047-closure.txt) | Record of removing stale `.venv/Lib/site-packages/prin_core.pth`, rebuilding `python/prin/_prin_core.pyd` (`9,290,240 B`, SHA-256 `37392d067efa3983e384c94f4ac2268c4fad2f5ea929c529b3db50bff4fee99e`) from clean `main` at `5677858c`, and verifying `prin`/`_prin_core` origin |
| [`provenance-hashes.txt`](provenance-hashes.txt) | Byte sizes and SHA-256 digests of all 12 pinned input/implementation/extension files in `preregistration.md` §1.1 plus the 3 E1 deliverables (`preregistration.md`, `exp002_r1_driver.py`, `test_exp002_r1_driver.py`) |
| [`verification-gate.txt`](verification-gate.txt) | E1 local and security gate results (`ruff`, `mypy --strict`, `interrogate`, `bandit`, Snyk Code MCP, `cargo audit`, `pip-audit`, governance checkers, clean Sphinx `-W` build, `gitleaks`, `pytest tests/test_exp002_r1_driver.py`, and the full local `pytest tests/ parity/` gate). First recorded for E1 head `62680946` (`320 passed` / `99.60%` driver coverage); **regenerated for the PR #36 remediation head** (`343 passed, 1 skipped` — the skip is the opt-in registered-host `_prin_core.pyd` pin test — / `98%` driver coverage) |
| [`pr36-remediation.txt`](pr36-remediation.txt) | PR #36 review remediation record: hosted-check failure triage and the eight findings fixed on `campaign/exp002-r1-e1` (opt-in live-pin gating, resolved-path confinement, prospective storage cap + durable `abort.json`, reference bootstrap, all-pin enforcement, environment shadowing, `pdf_info_keyset` clarification, `.gitattributes` stage-root widening) |
| [`SHA256SUMS.txt`](SHA256SUMS.txt) | SHA-256 digests of the evidence files in this directory |
