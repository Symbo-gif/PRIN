# benchmarks/results/EXP-001/ — raw artefacts for EXP-001 (Golden-trajectory numerical parity)

**Status:** SKELETON — no run has executed. Record root:
[`DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/`](../../../DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/README.md).

## Run-directory rule (campaign plan §7.1, §7.3)

Every execution uses the committed campaign driver named in the approved
pre-registration to create a **new** directory named
`RUN-<UTC yyyymmddThhmmssZ>-<short git SHA>-<label>/`. Direct campaign use of
`python -m benchmarks.benchrunner` is prohibited because it does not emit the
required campaign metadata sidecar; the driver validates metadata before
invoking `benchrunner` or `write_result`. A `RUN-` directory that already exists
is never reused: re-runs,
retries after an abort, and corrections get a new run ID. The driver enforces
all of this up front (`benchmarks/campaign/exp001_driver.py::_validate_run_dir`):
`--out` must be a not-yet-existing direct child of this directory named
exactly `RUN-<UTC yyyymmddThhmmssZ>-<short git SHA>-<label>`, or the run
aborts before any comparison executes. Each run directory is closed by
checking it is complete and then generating its own SHA-256 manifest:

```python
from pathlib import Path
from benchmarks.campaign.exp001_driver import check_run_complete
from tools.reproduce import append_manifest, verify_manifest

run = Path("benchmarks/results/EXP-001/RUN-...")
check_run_complete(run)  # every artefact campaign-metadata.json names must exist
append_manifest(results_dir=run, manifest_path=run / "manifest.json")
verify_manifest(results_dir=run, manifest_path=run / "manifest.json")
```

`check_run_complete` is not optional. The driver publishes the
`campaign-metadata.json` sidecar *before* the result artefact and rolls the
sidecar back if the result write fails — but that rollback only covers
failures the driver itself handles. A process kill between the two writes
leaves a sidecar-only directory, and `append_manifest` on its own would
inventory that single JSON file and `verify_manifest` would then accept the
manifest. `check_run_complete` raises `IncompleteRunError` for such a
directory: record it as an aborted run in `log.md` (Experimentation Standards
§2 E3: aborted runs are never deleted), retry under a new `RUN-` ID, and do
not manifest it.

`verify_manifest` fails closed on any missing, modified, resized, or
unmanifested `*.json` in the run directory. Artefacts carry the standard
`environment` / `config` envelope (`benchmarks/_common/result.py`) and the
unchanged category payload. Campaign provenance is separate in
`campaign-metadata.json` as specified by campaign plan §7.2. Tracked size cap: 2 MiB per
run; larger arrays go to the gitignored `DOCS/test_and_benchmark_results/EXP-001/`
with their digests recorded in a committed sidecar.
