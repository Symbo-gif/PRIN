# EVIDENCE/exp002-r1-e3/ — Verification evidence for `EXP-002-r1` E3

**Stage:** `EXP-002-r1-E3` (Experiment Execution and Raw Evidence Collection, track C1).<br>
**Date:** 2026-10-21 UTC.<br>
**Branch:** `campaign/exp002-r1-e3` (branched from merged `origin/main` HEAD commit `R = e65076eb7ae97100d40ea32c60229dd40ed51033`).<br>
**Experiment record:** [`DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/`](../../DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md).<br>
**Operator:** MichaelMaillet.<br>
**AI pair of record:** Antigravity.

Under the **Re-run (`-r1`/`-rN`) Namespace & Evidence Isolation Rule** (campaign
plan §7.1, §7.5, §8, amendment #10), all stage verification evidence for
`EXP-002-r1` E3 lives in this dedicated `EVIDENCE/exp002-r1-e3/` directory and
never modifies `EVIDENCE/0159/`..`0163/`, `EVIDENCE/exp002-d1-s1/`..`s4/`,
`EVIDENCE/exp002-r1-e1/`, or `EVIDENCE/exp002-r1-e2/`.

Verify this bundle with:

```powershell
.venv\Scripts\python.exe -I EVIDENCE/exp002-d1-s3/index_selfcheck.py exp002-r1-e3
```

## Indexed files

| File | Description |
|---|---|
| [`README.md`](README.md) | This evidence index |
| [`log.md`](log.md) | Full operator console execution log, entry verification, execution sequence, timestamps, and post-execution summaries |
| [`manifest-verifications.txt`](manifest-verifications.txt) | Verification records confirming manifest integrity and `check_run_complete()` passing for all 5 executed runs |
| [`predecessor-immutability.txt`](predecessor-immutability.txt) | Proof that `git diff HEAD` across all predecessor `EXP-002`, `0159`–`0163`, and `exp002-d1-s1`–`s4` roots is completely empty |
| [`storage-audit.txt`](storage-audit.txt) | Storage audit documenting per-run sizes (all <= 2 MiB), combined raw storage (339,902 B <= 10 MiB), and publication file counts (39 per reproduction leg) |
| [`SHA256SUMS.txt`](SHA256SUMS.txt) | SHA-256 digests of the evidence files in this directory |
