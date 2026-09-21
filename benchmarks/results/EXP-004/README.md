# benchmarks/results/EXP-004/ — raw artefacts for EXP-004 (GPU kernels and Torch bridge performance)

**Status:** SKELETON — no run has executed. Record root:
[`DOCS/experiments/EXP-004-gpu-kernels-and-torch-bridge-performance/`](../../../DOCS/experiments/EXP-004-gpu-kernels-and-torch-bridge-performance/README.md).

## Run-directory rule (campaign plan §7.1, §7.3)

Every execution writes into a **new** directory named
`RUN-<UTC yyyymmddThhmmssZ>-<short git SHA>-<label>/`, passed to
`python -m benchmarks.benchrunner … --out benchmarks/results/EXP-004/RUN-…/`
(or to the committed driver's equivalent `write_result` call). A `RUN-`
directory that already exists is never passed to `--out` again: re-runs,
retries after an abort, and corrections get a new run ID. Each run directory
is closed by generating its own SHA-256 manifest:

```python
from pathlib import Path
from tools.reproduce import append_manifest, verify_manifest
run = Path("benchmarks/results/EXP-004/RUN-...")
append_manifest(results_dir=run, manifest_path=run / "manifest.json")
verify_manifest(results_dir=run, manifest_path=run / "manifest.json")
```

`verify_manifest` fails closed on any missing, modified, resized, or
unmanifested `*.json` in the run directory. Artefacts carry the standard
`environment` / `config` envelope (`benchmarks/_common/result.py`) plus the
campaign payload fields `exp_id`, `run_id`, `session`, `operator`,
`hypotheses` (and `timing_method` for GPU timing). Tracked size cap: 2 MiB per
run; larger arrays go to the gitignored `DOCS/test_and_benchmark_results/EXP-004/`
with their digests recorded in a committed sidecar.
