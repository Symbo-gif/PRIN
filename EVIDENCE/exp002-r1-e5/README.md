# EVIDENCE/exp002-r1-e5/ — Verification Evidence for `EXP-002-r1` E5

**Stage:** `EXP-002-r1-E5` (Report Stage, track C1).<br>
**Date:** 2026-10-22 UTC.<br>
**Branch:** `campaign/exp002-r1-e5`.<br>
**Experiment record:** [`DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/`](../../DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md).<br>
**Operator:** MichaelMaillet.<br>
**AI pair of record:** Antigravity.

Under the **Re-run (`-r1`/`-rN`) Namespace & Evidence Isolation Rule** (campaign
plan §7.1, §7.5, §8, amendment #10), all stage verification evidence for
`EXP-002-r1` E5 lives in this dedicated `EVIDENCE/exp002-r1-e5/` directory and
never modifies `EVIDENCE/0159/`..`0163/`, `EVIDENCE/exp002-d1-s1/`..`s4/`, or
`EVIDENCE/exp002-r1-e1/`..`e4/`.

Verify this bundle with:

```powershell
.venv\Scripts\python.exe -I EVIDENCE/exp002-d1-s3/index_selfcheck.py exp002-r1-e5
```

## Indexed files

| File | Description |
|---|---|
| [`README.md`](README.md) | This evidence index |
| [`log.md`](log.md) | Full operator execution log, entry verification, execution sequence, timestamps, and post-execution summaries |
| [`retained-bytes-verification.txt`](retained-bytes-verification.txt) | Step 1 verification of 39/39 retained publication files and 172/172 retained input snapshots against manifested raw digests and E3 listing hashes |
| [`regeneration-verification.txt`](regeneration-verification.txt) | Step 2 clean detached-worktree regeneration of the seven E4 analysis outputs and `report-manifest.json` confirming byte-for-byte identity (8/8) |
| [`reconstruction-verification.txt`](reconstruction-verification.txt) | Step 3 clean-checkout reconstruction of both publication arms into gitignored directory confirming 39/39 PRIN raw identity and cross-arm comparison |
| [`predecessor-immutability.txt`](predecessor-immutability.txt) | Proof that `git diff` across all predecessor `EXP-002`, `0159`–`0163`, `exp002-d1-s1`–`s4`, and `exp002-r1-e1`–`e4` roots is completely empty (0 diff bytes), with only Erratum 3 added to `EXP-002/report.md` §15 |
| [`SHA256SUMS.txt`](SHA256SUMS.txt) | SHA-256 digests of all evidence files in this directory |
