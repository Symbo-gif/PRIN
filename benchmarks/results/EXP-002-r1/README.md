# benchmarks/results/EXP-002-r1/ — isolated raw artefacts for EXP-002-r1 (API, benchmark-result, and reproduction parity, re-run)

**Status:** **PREPARED AT E1 (2026-10-20 UTC) — NO `RUN-` DIRECTORY EXISTS YET.**
No E3 execution, pilot, or observation collection occurs at E1. The committed
driver [`benchmarks/campaign/exp002_r1_driver.py`](../../campaign/exp002_r1_driver.py)
refuses execution while [`preregistration.md`](../../../DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/preregistration.md)
is `DRAFT`. Record root:
[`DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/`](../../../DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md).

## Namespace and evidence isolation (campaign plan §7.1, §10.4 item 4, amendment #10)

Under the **Re-run (`-r1`/`-rN`) Namespace & Evidence Isolation Rule**:

- **Dedicated raw-artefact root:** `benchmarks/results/EXP-002-r1/` (this
  directory). Predecessor [`benchmarks/results/EXP-002/`](../EXP-002/README.md)
  and its five frozen `RUN-` directories (`0161`–`0163`) are **immutable** and
  are **never** opened for writing, modified, or reused by `EXP-002-r1`.
  `exp002_r1_driver.py` explicitly rejects any `--run-dir` or `config.out_dir`
  under `benchmarks/results/EXP-002/`.
- **Dedicated generated-output root (gitignored):**
  `DOCS/test_and_benchmark_results/EXP-002-r1/` (never
  `DOCS/test_and_benchmark_results/EXP-002/`).
- **Dedicated stage-labelled evidence roots:** `EVIDENCE/exp002-r1-e1/`..`e5/`
  (never `EVIDENCE/0159`..`0163` or `EVIDENCE/exp002-d1-*`).
- **Run directory naming and metadata:** every E3 leg creates a new direct-child
  directory `RUN-<UTC yyyymmddThhmmssZ>-<short git SHA>-<label>/` using the
  `r1-` labels (`r1-api-cpu`, `r1-conclusions-cpu`,
  `r1-reproduction-reference-cpu`, `r1-reproduction-prin-cpu`,
  `r1-seedrep0-prin-cpu`), with `campaign-metadata.json` carrying
  `exp_id="EXP-002-r1"` and `session="EXP-002-r1-E3"`.

## Run-directory and storage rules (campaign plan §7.1, §7.3, §7.5, §8)

Every execution uses the committed campaign driver
`benchmarks/campaign/exp002_r1_driver.py` after E2 approval. Direct campaign use
of `python -m benchmarks.benchrunner` is prohibited. A `RUN-` directory that
already exists is never reused: re-runs, retries after an abort, and corrections
receive a new run ID. Each run directory is closed by generating and verifying
its own SHA-256 manifest:

```python
from pathlib import Path
from tools.reproduce import append_manifest, verify_manifest

run = Path("benchmarks/results/EXP-002-r1/RUN-...")
append_manifest(results_dir=run, manifest_path=run / "manifest.json")
verify_manifest(results_dir=run, manifest_path=run / "manifest.json")
```

`verify_manifest` fails closed on any missing, modified, resized, or
unmanifested `*.json` in the run directory. Tracked storage caps enforced at
closure by `exp002_r1_driver.py`:

- **Per-run cap:** ≤ 2 MiB per `RUN-` directory.
- **Per-root and combined `EXP-002` + `EXP-002-r1` cap:** both
  `size(benchmarks/results/EXP-002-r1) + size(DOCS/experiments/EXP-002-r1-*)`
  and the combined total across `EXP-002` + `EXP-002-r1` (both raw roots plus
  both record roots) must remain ≤ 10 MiB.
- **Campaign-wide cap:** ≤ 64 MiB across all `benchmarks/results/EXP-*`
  directories.
