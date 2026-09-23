# benchmarks/results/EXP-001/ — raw artefacts for EXP-001 (Golden-trajectory numerical parity)

**Status:** **4 runs executed** (session 0156 E3, 2026-09-23 UTC) —
`RUN-20260923T134012Z-6b9d6b6-corpus-cpu` (H1, 504 cases),
`RUN-20260923T134226Z-6b9d6b6-repeatability-cpu` (H3, 14),
`RUN-20260923T134250Z-6b9d6b6-fuzz-cpu` (H2, 1,000), and
`RUN-20260923T134255Z-6b9d6b6-kernel-path-cuda` (H4, 72). None aborted;
each closed with `check_run_complete` + `append_manifest` +
`verify_manifest`. Total 5.921 MiB under campaign plan amendment 6
(EXP-001 tracked cap 8 MiB; §7.5 per-run cap waived for the `fuzz` leg).
Verdicts were assigned at E4 (session 0157) on the frozen pre-registration §8
rule: **H1 `REFUTED`, H2a `REFUTED`, H2b/H3/H4 `CONFIRMED`**, raising the campaign
plan §10.4 D1 flag. These artefacts are unchanged by that adjudication and are
never edited; the re-run after the correction cycle gets a new experiment record
(`EXP-001-r1`) with new `RUN-` directories. Record root:
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
all of this up front (`benchmarks/campaign/exp001_driver.py::_reserve_run_dir`):
`--out` must be a not-yet-existing direct child of this directory named
exactly `RUN-<UTC yyyymmddThhmmssZ>-<short git SHA>-<label>`, where `<label>`
is validated separately (`_validate_label`) as a single safe filename
component before the directory is ever touched, and the directory itself is
created with an atomic exclusive `mkdir()` (not a check-then-create) so two
concurrent runs can never both win the same run ID. Otherwise the run
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
failures the driver itself handles, i.e. exceptions it catches. It does **not**
cover process termination (`SIGKILL`, a power loss, `TerminateProcess`): a
kill between the two writes leaves a sidecar-only directory, and
`append_manifest` on its own would inventory that single JSON file and
`verify_manifest` would then accept the manifest. `check_run_complete` raises
`IncompleteRunError` for such a directory: record it as an aborted run in
`log.md` (Experimentation Standards §2 E3: aborted runs are never deleted),
retry under a new `RUN-` ID, and do not manifest it.

`check_run_complete` validates the **whole** campaign plan §7.2 sidecar
schema, not just that every named artefact exists, and treats the sidecar as
untrusted input from a possibly-tampered directory. It rejects:

- a `campaign-metadata.json` that is a symbolic link (checked no-follow,
  before anything that would follow it) or is not a JSON object;
- a missing or wrong `exp_id`, a `run_id` that is not the directory's own
  name, an empty or non-string `session`/`operator`, or an `artefacts` value
  that is not a non-empty object;
- an artefact key that is not a plain filename directly in the run directory
  (path separator or `..` segment), that is a reserved infrastructure name
  (`campaign-metadata.json`, `manifest.json`, matched case-insensitively), or
  that is not a canonical `<mode>_<label>.json` result name;
- hypothesis tags that are not a non-empty list of registered `H1`–`H4`
  strings, or that are not the tags registered for that result's mode. A tag
  value given as the string `"H9"` is rejected, never coerced into
  `["H", "9"]`. A GPU result entry uses the object form
  `{"hypotheses": [...], "timing_method": ...}` that campaign plan §7.2
  requires, with a registered `timing_method`;
- a declared artefact that is a symbolic link (CWE-59: `Path.is_file()`
  follows links, so linked-to content would otherwise be manifested as if
  this run had written it);
- a declared result whose own `environment`/`config` envelope is missing
  required campaign plan §7.2 fields, or disagrees with the sidecar
  (`config.out_dir` must resolve to this run directory; a GPU entry's
  `environment.backend` must be `cuda`);
- a top-level `*.json` result file the sidecar's `artefacts` mapping does not
  name.

**Case contract.** `append_manifest`/`verify_manifest` inventory this
directory with `Path.glob("*.json")`, which is case-insensitive on Windows and
case-sensitive on Linux — both are in this project's CI matrix — so a
`rogue.JSON` would be manifested on one platform and invisible on the other.
`check_run_complete` therefore *recognises* a `.json` suffix
case-insensitively and then *requires* canonical lowercase, for declared names
and present files alike: a top-level `rogue.JSON` fails closure exactly as
`rogue.json` does, and a declared `notes.txt` fails because the manifest could
never cover it. The closure inventory and the manifest glob therefore agree on
every supported platform rather than depending on the host filesystem.

`verify_manifest` fails closed on any missing, modified, resized, or
unmanifested `*.json` in the run directory. Artefacts carry the standard
`environment` / `config` envelope (`benchmarks/_common/result.py`) and the
unchanged category payload. Campaign provenance is separate in
`campaign-metadata.json` as specified by campaign plan §7.2. Tracked size cap: 2 MiB per
run; larger arrays go to the gitignored `DOCS/test_and_benchmark_results/EXP-001/`
with their digests recorded in a committed sidecar.
