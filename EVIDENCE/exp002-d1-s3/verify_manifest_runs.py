"""Re-verify the five EXP-002 raw run directories and the frozen input manifest.

Part of the S3 delta re-audit (brief section 7): the EXP-002 record must still
verify against its own manifests after the S3 changes. It uses the same registered,
read-only verifier the EXP-002 driver uses, ``tools.reproduce.verify_manifest``,
called the way ``benchmarks/campaign/exp002_driver.py:1364`` calls it:

* for every ``benchmarks/results/EXP-002/RUN-*`` directory,
  ``verify_manifest(run_dir, run_dir / "manifest.json")``;
* for the frozen 172-input manifest, the SHA-256 of ``paper/artefact_manifest.json``
  against the pinned ``INPUT_MANIFEST_SHA``, then ``verify_manifest`` of the
  reference results root against it.

It writes nothing and takes no arguments::

    .venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/verify_manifest_runs.py

Exit status is 0 when every directory and the input manifest verify, 1 otherwise.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.campaign import exp002_driver as driver  # noqa: E402
from tools.reproduce import verify_manifest  # noqa: E402


def check_runs() -> int:
    """Verify every registered run directory.

    Returns:
        The number of directories that failed to verify.
    """
    runs = sorted(
        path for path in driver.RAW_ROOT.iterdir() if path.name.startswith("RUN-")
    )
    print(f"raw record root  : {driver.RAW_ROOT}")
    print(f"RUN-* directories: {len(runs)}")
    failures = 0
    for run in runs:
        print()
        try:
            records = verify_manifest(run, run / "manifest.json")
        except Exception as error:
            failures += 1
            print(f"[FAIL] {run.name}\n       {type(error).__name__}: {error}")
            continue
        names = sorted(record.path for record in records)
        print(f"[PASS] {run.name}")
        print(f"       manifested records={len(records)}  entries: {names}")
    return failures


def check_inputs() -> int:
    """Verify the frozen input manifest and the reference results it indexes.

    Returns:
        The number of failures (0 or 1).
    """
    print()
    print("=" * 74)
    print("Frozen input manifest (paper/artefact_manifest.json) against the")
    print("reference results root.")
    print("=" * 74)
    recomputed = hashlib.sha256(driver.INPUT_MANIFEST.read_bytes()).hexdigest()
    print(f"INPUT_MANIFEST_SHA : {driver.INPUT_MANIFEST_SHA}")
    print(f"recomputed sha256  : {recomputed}")
    matches = recomputed == driver.INPUT_MANIFEST_SHA
    print(f"matches the pinned constant: {matches}")
    if not matches:
        return 1
    try:
        records = verify_manifest(
            driver.REFERENCE / "benchmarks/results", driver.INPUT_MANIFEST
        )
    except Exception as error:
        print(f"[FAIL] {type(error).__name__}: {error}")
        return 1
    print(f"[PASS] verify_manifest(reference results, INPUT_MANIFEST): {len(records)}")
    return 0


def main() -> int:
    """Run both checks and report the total.

    Returns:
        The process exit status.
    """
    failures = check_runs() + check_inputs()
    print()
    print(f"TOTAL FAILURES: {failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
