"""Mutation self-test of validate_run_record.py on COPIES of a real record (scratch only).

Each mutation must make the validator fail on the intended check(s). The copies live
outside the repository and are run with --allow-outside-raw-root.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

SCRATCH = Path(sys.argv[1])
SRC = Path(sys.argv[2])
MODE = sys.argv[3]
RESULT = {"api": "api.json", "conclusions": "conclusions.json"}.get(MODE, "reproduction.json")
VALIDATOR = SCRATCH / "validate_run_record.py"
PY = sys.executable


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rewrite_manifest(run: Path) -> None:
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        item["bytes"] = (run / item["path"]).stat().st_size
        item["sha256"] = digest(run / item["path"])
    (run / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def fresh(name: str) -> Path:
    root = SCRATCH / "mut" / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    run = root / SRC.name
    shutil.copytree(SRC, run)
    return run


def load(run: Path) -> dict:
    return json.loads((run / RESULT).read_text(encoding="utf-8"))


def save(run: Path, doc: dict) -> None:
    (run / RESULT).write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
    rewrite_manifest(run)


def run_validator(run: Path) -> tuple[int, list[str]]:
    proc = subprocess.run(
        [PY, "-I", str(VALIDATOR), str(run), "--mode", MODE, "--allow-outside-raw-root"],
        capture_output=True,
        text=True,
    )
    fails = [line for line in proc.stdout.splitlines() if line.startswith("FAIL")]
    return proc.returncode, fails


MUTATIONS = []


def mutation(fn):
    MUTATIONS.append(fn)
    return fn


@mutation
def baseline_copy(run):  # must pass entirely
    return "NONE"


@mutation
def stray_file(run):
    (run / "extra.txt").write_text("x")
    return "A3"


@mutation
def flipped_byte_without_manifest_update(run):
    data = bytearray((run / RESULT).read_bytes())
    data[len(data) // 2] ^= 0x01
    (run / RESULT).write_bytes(bytes(data))
    return "B2"


@mutation
def seed_key_changed(run):
    doc = load(run)
    doc["config"]["seed_key"] = 3
    save(run, doc)
    return "D4"


@mutation
def seed_counter_bool(run):
    doc = load(run)
    doc["config"]["seed_counter"] = False
    save(run, doc)
    return "D4"


@mutation
def status_aborted(run):
    doc = load(run)
    doc["status"] = "ABORTED"
    doc["abort_reason"] = "synthetic"
    save(run, doc)
    return "D1"


@mutation
def wrong_source_sha(run):
    doc = load(run)
    doc["environment"]["git_commit"] = "0" * 40
    doc["identity"]["source_sha"] = "0" * 40
    save(run, doc)
    return "D3"


@mutation
def wrong_protocol_digest(run):
    doc = load(run)
    doc["identity"]["preregistration_sha256"] = "1" * 64
    save(run, doc)
    return "D5"


@mutation
def wrong_input_manifest(run):
    doc = load(run)
    doc["identity"]["input_manifest_sha256"] = "2" * 64
    save(run, doc)
    return "D5"


@mutation
def dropped_input_record(run):
    doc = load(run)
    doc["identity"]["input_records"] = doc["identity"]["input_records"][:-1]
    save(run, doc)
    return "D5"


@mutation
def backend_not_cpu(run):
    doc = load(run)
    doc["environment"]["backend"] = "cuda"
    save(run, doc)
    return "D3"


@mutation
def environment_field_null(run):
    doc = load(run)
    doc["environment"]["rust_version"] = None
    save(run, doc)
    return "D3"


@mutation
def sidecar_wrong_operator(run):
    side = json.loads((run / "campaign-metadata.json").read_text(encoding="utf-8"))
    side["operator"] = "someone-else"
    (run / "campaign-metadata.json").write_text(json.dumps(side, indent=2, sort_keys=True), encoding="utf-8")
    rewrite_manifest(run)
    return "C1"


@mutation
def sidecar_wrong_mapping(run):
    side = json.loads((run / "campaign-metadata.json").read_text(encoding="utf-8"))
    side["artefacts"] = {RESULT: ["H9"]}
    (run / "campaign-metadata.json").write_text(json.dumps(side, indent=2, sort_keys=True), encoding="utf-8")
    rewrite_manifest(run)
    return "C1"


@mutation
def manifest_missing_entry(run):
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    manifest["files"] = manifest["files"][:1]
    (run / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return "B1"


@mutation
def observation_population_broken(run):
    doc = load(run)
    obs = doc["observations"]
    if MODE == "api":
        obs["rows"] = obs["rows"][:-1]
        return_check = "E1"
    elif MODE == "conclusions":
        obs["cases"] = obs["cases"][:-1]
        return_check = "E2"
    else:
        obs["expected_files"] = obs["expected_files"][:-1]
        return_check = "E3"
    save(run, doc)
    return return_check


@mutation
def elapsed_negative(run):
    doc = load(run)
    doc["elapsed_seconds"] = -1.0
    save(run, doc)
    return "D6"


def main() -> int:
    bad = 0
    for fn in MUTATIONS:
        run = fresh(fn.__name__)
        expect = fn(run)
        code, fails = run_validator(run)
        if expect == "NONE":
            ok = code == 0 and not fails
        else:
            ok = code != 0 and any(line.startswith(f"FAIL  {expect}") for line in fails)
        bad += 0 if ok else 1
        print(f"{'OK ' if ok else 'BAD'}  {fn.__name__:<42} expect={expect:<5} exit={code} fails={[f[6:60] for f in fails][:3]}")
    print(f"MUTATION SELF-TEST: {len(MUTATIONS) - bad} behaved as expected, {bad} did not")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
