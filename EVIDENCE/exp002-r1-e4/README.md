# EVIDENCE/exp002-r1-e4/ — Verification Evidence for `EXP-002-r1` E4

**Stage:** `EXP-002-r1-E4` (Analysis and Hypothesis Adjudication, track C1).<br>
**Date:** 2026-10-21 / 2026-10-22 UTC.<br>
**Branch:** `campaign/exp002-r1-e4`.<br>
**Experiment record:** [`DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/`](../../DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md).<br>
**Operator:** MichaelMaillet.<br>
**AI pair of record:** Antigravity.

Under the **Re-run (`-r1`/`-rN`) Namespace & Evidence Isolation Rule** (campaign
plan §7.1, §7.5, §8, amendment #10), all stage verification evidence for
`EXP-002-r1` E4 lives in this dedicated `EVIDENCE/exp002-r1-e4/` directory and
never modifies `EVIDENCE/0159/`..`0163/`, `EVIDENCE/exp002-d1-s1/`..`s4/`,
`EVIDENCE/exp002-r1-e1/`, `EVIDENCE/exp002-r1-e2/`, or `EVIDENCE/exp002-r1-e3/`.

Verify this bundle with:

```powershell
.venv\Scripts\python.exe -I EVIDENCE/exp002-d1-s3/index_selfcheck.py exp002-r1-e4
```

## Indexed files

| File | Description |
|---|---|
| [`README.md`](README.md) | This evidence index |
| [`log.md`](log.md) | Full operator console execution log, entry verification, execution sequence, timestamps, and post-execution summaries |
| [`analysis-verification.txt`](analysis-verification.txt) | Verification records confirming test suite results, deliverable digest verifications, and hypothesis verdicts |
| [`predecessor-immutability.txt`](predecessor-immutability.txt) | Proof that `git diff HEAD` across all predecessor `EXP-002`, `0159`–`0163`, and `exp002-d1-s1`–`s4` roots is completely empty (0 diff bytes) |
| [`SHA256SUMS.txt`](SHA256SUMS.txt) | SHA-256 digests of all evidence files in this directory |
