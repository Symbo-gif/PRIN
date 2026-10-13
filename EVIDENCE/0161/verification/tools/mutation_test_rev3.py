"""Mutation self-test of validate_run_record_rev3.py on COPIES of a real record (scratch only).

Each mutation must make the validator fail on the intended check; the unmodified control must
pass. The copies live outside the repository's raw root (``--allow-outside-raw-root``), the
copy's ``out_dir`` is first rewritten to the copy's own path so the exact-``out_dir`` check (S6)
can be exercised, and publication modes use ``--generated-root`` (the retained original is
only read; retention mutations act on a private copy).

Usage: python mutation_test_rev3.py <scratch-dir> <run-dir> <mode> [<generated-root>]
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

SCRATCH = Path(sys.argv[1])
SRC = Path(sys.argv[2])
MODE = sys.argv[3]
GEN_SRC = Path(sys.argv[4]) if len(sys.argv) > 4 else None
VALIDATOR = SCRATCH / "validate_run_record_rev3.py"
PUBLICATION = MODE in {"reference", "prin", "repeatability"}
RESULT = {"api": "api.json", "conclusions": "conclusions.json"}.get(MODE, "reproduction.json")
LABEL = {
    "api": "api-cpu",
    "conclusions": "conclusions-cpu",
    "reference": "reproduction-reference-cpu",
    "prin": "reproduction-prin-cpu",
    "repeatability": "seedrep0-prin-cpu",
}[MODE]
PY = sys.executable
NONE = ["NONE"]

CASES: list[tuple[str, Callable, bool, tuple[str, ...] | None]] = []


def case(gen: bool = False, modes: tuple[str, ...] | None = None):
    def register(fn: Callable) -> Callable:
        CASES.append((fn.__name__, fn, gen, modes))
        return fn

    return register


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, doc: object) -> None:
    path.write_text(json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def rewrite_manifest(run: Path) -> None:
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        item["bytes"] = (run / item["path"]).stat().st_size
        item["sha256"] = digest(run / item["path"])
    write_json(run / "manifest.json", manifest)


def load(run: Path) -> dict:
    return json.loads((run / RESULT).read_text(encoding="utf-8"))


def save(run: Path, doc: dict) -> None:
    write_json(run / RESULT, doc)
    rewrite_manifest(run)


def edit_text(run: Path, fn: Callable[[str], str]) -> None:
    path = run / RESULT
    text = path.read_bytes().decode("utf-8")
    path.write_bytes(fn(text).encode("utf-8"))
    rewrite_manifest(run)


def edit_sidecar(run: Path, fn: Callable[[dict], None]) -> None:
    doc = json.loads((run / "campaign-metadata.json").read_text(encoding="utf-8"))
    fn(doc)
    write_json(run / "campaign-metadata.json", doc)
    rewrite_manifest(run)


def edit_manifest(run: Path, fn: Callable[[dict], None]) -> None:
    doc = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    fn(doc)
    write_json(run / "manifest.json", doc)


def fresh(name: str, with_generated: bool) -> tuple[Path, Path | None]:
    root = SCRATCH / "mut3" / MODE / name
    if root.exists():
        shutil.rmtree(root)
    # the copy sits at <root>/benchmarks/results/EXP-002/<RUN>, so the registered tail of out_dir holds
    raw = root / "benchmarks" / "results" / "EXP-002"
    raw.mkdir(parents=True)
    run = raw / SRC.name
    shutil.copytree(SRC, run)
    doc = load(run)
    doc["config"]["out_dir"] = str(run)
    save(run, doc)  # normalised baseline: out_dir is the copy's own path
    gen = None
    if PUBLICATION:
        assert GEN_SRC is not None
        if with_generated:
            gen = root / "generated"
            shutil.copytree(GEN_SRC, gen)
        else:
            gen = GEN_SRC
    return run, gen


def invoke(run: Path, gen: Path | None) -> tuple[int, list[str]]:
    command = [PY, "-I", str(VALIDATOR), str(run), "--mode", MODE, "--allow-outside-raw-root", "--exact-out-dir"]
    if gen is not None:
        command += ["--generated-root", str(gen)]
    proc = subprocess.run(command, capture_output=True, text=True)
    return proc.returncode, [line for line in proc.stdout.splitlines() if line.startswith("FAIL")]


# ---------------------------------------------------------------- generic cases
@case()
def baseline_control(run, gen):
    return NONE


@case()
def stray_file(run, gen):
    (run / "extra.txt").write_text("x")
    return ["A3"]


@case()
def label_renamed(run, gen):
    new = run.with_name(run.name.replace(LABEL, "wrong-label"))
    run.rename(new)
    return ["A1"], new


@case()
def flipped_byte_without_manifest_update(run, gen):
    data = bytearray((run / RESULT).read_bytes())
    data[len(data) // 2] ^= 0x01
    (run / RESULT).write_bytes(bytes(data))
    return ["B2", "S3", "Z0"]


@case()
def seed_key_changed(run, gen):
    doc = load(run)
    doc["config"]["seed_key"] = 3
    save(run, doc)
    return ["D4"]


@case()
def seed_counter_bool(run, gen):
    doc = load(run)
    doc["config"]["seed_counter"] = False
    save(run, doc)
    return ["D4"]


@case()
def status_aborted(run, gen):
    doc = load(run)
    doc["status"] = "ABORTED"
    doc["abort_reason"] = "synthetic"
    save(run, doc)
    return ["D1", "D2"]


@case()
def wrong_source_sha(run, gen):
    doc = load(run)
    doc["environment"]["git_commit"] = "0" * 40
    doc["identity"]["source_sha"] = "0" * 40
    save(run, doc)
    return ["D3", "D5"]


@case()
def wrong_protocol_digest(run, gen):
    doc = load(run)
    doc["identity"]["preregistration_sha256"] = "1" * 64
    save(run, doc)
    return ["D5"]


@case()
def wrong_input_manifest(run, gen):
    doc = load(run)
    doc["identity"]["input_manifest_sha256"] = "2" * 64
    save(run, doc)
    return ["D5"]


@case()
def dropped_input_record(run, gen):
    doc = load(run)
    doc["identity"]["input_records"] = doc["identity"]["input_records"][:-1]
    save(run, doc)
    return ["D5"]


@case()
def backend_not_cpu(run, gen):
    doc = load(run)
    doc["environment"]["backend"] = "cuda"
    save(run, doc)
    return ["D3"]


@case()
def environment_field_null(run, gen):
    doc = load(run)
    doc["environment"]["rust_version"] = None
    save(run, doc)
    return ["D3"]


@case()
def envelope_extra_key(run, gen):
    doc = load(run)
    doc["note"] = "extra"
    save(run, doc)
    return ["D1"]


@case()
def seed_used_zero(run, gen):
    doc = load(run)
    doc["seed_used"] = 0
    save(run, doc)
    return ["D2"]


@case()
def iterations_float(run, gen):
    doc = load(run)
    doc["config"]["iterations"] = 10.0
    save(run, doc)
    return ["S2"]


@case()
def replicates_bool(run, gen):
    doc = load(run)
    doc["config"]["replicates"] = True
    save(run, doc)
    return ["S2"]


@case()
def out_dir_other_root(run, gen):
    doc = load(run)
    doc["config"]["out_dir"] = "D:\\mirror\\benchmarks\\results\\EXP-002\\" + run.name
    save(run, doc)
    return ["S6"]


@case()
def identity_extra_key(run, gen):
    doc = load(run)
    doc["identity"]["note"] = "extra"
    save(run, doc)
    return ["S4"]


@case()
def input_record_extra_key(run, gen):
    doc = load(run)
    doc["identity"]["input_records"][0]["note"] = "extra"
    save(run, doc)
    return ["S4"]


@case()
def recorded_offset_plus_two(run, gen):
    doc = load(run)
    doc["recorded_at_utc"] = doc["recorded_at_utc"].replace("+00:00", "+02:00")
    save(run, doc)
    return ["S5"]


@case()
def elapsed_inconsistent(run, gen):
    doc = load(run)
    doc["elapsed_seconds"] = 5.0 + float(doc["elapsed_seconds"])
    save(run, doc)
    return ["S5"]


@case()
def elapsed_negative(run, gen):
    doc = load(run)
    doc["elapsed_seconds"] = -1.0
    save(run, doc)
    return ["S5"]


@case()
def elapsed_infinity_literal(run, gen):
    edit_text(run, lambda t: re.sub(r'("elapsed_seconds":\s*)[^,\r\n]+', r"\1Infinity", t, count=1))
    return ["S3"]


@case()
def duplicate_top_level_key(run, gen):
    edit_text(run, lambda t: t.replace("{", '{\n  "status": "COMPLETED",', 1))
    return ["S3"]


@case()
def byte_order_mark(run, gen):
    edit_text(run, lambda t: "\ufeff" + t)
    return ["S3"]


@case()
def sidecar_wrong_operator(run, gen):
    edit_sidecar(run, lambda d: d.update(operator="someone-else"))
    return ["C1"]


@case()
def sidecar_wrong_mapping(run, gen):
    edit_sidecar(run, lambda d: d.update(artefacts={RESULT: ["H9"]}))
    return ["C1"]


@case()
def sidecar_missing_key(run, gen):
    edit_sidecar(run, lambda d: d.pop("operator"))
    return ["C1"]


@case()
def sidecar_extra_key(run, gen):
    edit_sidecar(run, lambda d: d.update(note="extra"))
    return ["C1"]


@case()
def sidecar_run_id_mismatch(run, gen):
    edit_sidecar(run, lambda d: d.update(run_id="RUN-20000101T000000Z-fae24c4-" + LABEL))
    return ["C1"]


@case()
def manifest_missing_entry(run, gen):
    edit_manifest(run, lambda d: d.update(files=d["files"][:1]))
    return ["B1", "B2"]


@case()
def manifest_extra_key(run, gen):
    edit_manifest(run, lambda d: d.update(note="extra"))
    return ["S6"]


@case()
def manifest_schema_true(run, gen):
    edit_manifest(run, lambda d: d.update(schema_version=True))
    return ["B1"]


@case()
def manifest_bytes_float(run, gen):
    def mutate(d):
        d["files"][0]["bytes"] = float(d["files"][0]["bytes"])

    edit_manifest(run, mutate)
    return ["B2"]


@case()
def manifest_stale_digest(run, gen):
    def mutate(d):
        d["files"][0]["sha256"] = "3" * 64

    edit_manifest(run, mutate)
    return ["B2"]


@case()
def junction_ancestor(run, gen):
    # <root>/benchmarks is replaced by a junction to a real directory holding the same tree
    root = run.parents[3]
    real = root / "real_benchmarks"
    shutil.move(str(root / "benchmarks"), str(real))
    made = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(root / "benchmarks"), str(real)],
        capture_output=True,
        text=True,
    )
    if made.returncode != 0:
        return "SKIP", None
    return ["S1"], run


# ------------------------------------------------------------- mode-specific cases
@case(modes=("api",))
def api_observations_extra_key(run, gen):
    doc = load(run)
    doc["observations"]["note"] = "extra"
    save(run, doc)
    return ["S4"]


@case(modes=("api",))
def api_row_extra_key(run, gen):
    doc = load(run)
    doc["observations"]["rows"][0]["note"] = "extra"
    save(run, doc)
    return ["E1"]


@case(modes=("api",))
def api_expected_names_dropped(run, gen):
    doc = load(run)
    doc["observations"]["expected_names"] = doc["observations"]["expected_names"][:-1]
    save(run, doc)
    return ["E1"]


@case(modes=("conclusions",))
def case_extra_key(run, gen):
    doc = load(run)
    doc["observations"]["cases"][0]["note"] = "extra"
    save(run, doc)
    return ["S4"]


@case(modes=("conclusions",))
def case_family_changed(run, gen):
    doc = load(run)
    doc["observations"]["cases"][0]["family"] = "C09"
    save(run, doc)
    return ["E2", "S4"]


@case(modes=("conclusions",))
def case_operator_invalid(run, gen):
    doc = load(run)
    doc["observations"]["cases"][0]["operator"] = "=="
    save(run, doc)
    return ["E2"]


@case(modes=("conclusions",))
def cases_truncated(run, gen):
    doc = load(run)
    doc["observations"]["cases"] = doc["observations"]["cases"][:-1]
    save(run, doc)
    return ["E2"]


@case(modes=("reference", "prin", "repeatability"))
def publication_observations_extra_key(run, gen):
    doc = load(run)
    doc["observations"]["note"] = "extra"
    save(run, doc)
    return ["S4"]


@case(modes=("reference", "prin", "repeatability"))
def renderer_extra_key(run, gen):
    doc = load(run)
    doc["observations"]["renderer"]["note"] = "extra"
    save(run, doc)
    return ["S4"]


@case(modes=("reference", "prin", "repeatability"))
def font_cache_digest_null(run, gen):
    doc = load(run)
    doc["observations"]["renderer"]["font_cache"]["sha256"] = None
    save(run, doc)
    return ["E3"]


@case(modes=("reference", "prin", "repeatability"))
def file_record_extra_key(run, gen):
    doc = load(run)
    doc["observations"]["files"][0]["note"] = "extra"
    save(run, doc)
    return ["S4"]


@case(modes=("reference", "prin", "repeatability"))
def file_record_missing_key(run, gen):
    doc = load(run)
    doc["observations"]["files"][0].pop("sensitivity_sha256")
    save(run, doc)
    return ["S4", "E3"]


@case(modes=("reference", "prin", "repeatability"))
def expected_files_truncated(run, gen):
    doc = load(run)
    doc["observations"]["expected_files"] = doc["observations"]["expected_files"][:-1]
    save(run, doc)
    return ["E3"]


@case(modes=("reference", "prin", "repeatability"))
def implementation_swapped(run, gen):
    doc = load(run)
    doc["observations"]["implementation"] = "prin" if MODE == "reference" else "reference"
    save(run, doc)
    return ["E3"]


@case(gen=True, modes=("reference", "prin", "repeatability"))
def retention_file_tampered(run, gen):
    target = sorted(p for p in (gen / "publication").rglob("*") if p.is_file())[0]
    data = bytearray(target.read_bytes())
    data[len(data) // 2] ^= 0x01
    target.write_bytes(bytes(data))
    return ["F3"]


@case(gen=True, modes=("reference", "prin", "repeatability"))
def retention_file_missing(run, gen):
    sorted(p for p in (gen / "publication").rglob("*") if p.is_file())[0].unlink()
    return ["F2"]


@case(gen=True, modes=("reference", "prin", "repeatability"))
def retention_extra_file(run, gen):
    (gen / "publication" / "stray.txt").write_text("x")
    return ["F2"]


@case(gen=True, modes=("reference", "prin", "repeatability"))
def retention_inputs_tampered(run, gen):
    target = sorted(p for p in (gen / "inputs").rglob("*") if p.is_file())[0]
    data = bytearray(target.read_bytes())
    data[len(data) // 2] ^= 0x01
    target.write_bytes(bytes(data))
    return ["F4"]


@case(gen=True, modes=("reference", "prin", "repeatability"))
def retention_publication_dir_missing(run, gen):
    shutil.rmtree(gen / "publication")
    return ["F1"]


def main() -> int:
    bad = 0
    ran = 0
    for name, fn, with_gen, modes in CASES:
        if modes is not None and MODE not in modes:
            continue
        run, gen = fresh(name, with_gen)
        outcome = fn(run, gen)
        override = None
        if isinstance(outcome, tuple):
            outcome, override = outcome
        if outcome == "SKIP":
            print(f"SKIP {name:<44} (could not create the link on this host)")
            continue
        expected = outcome
        code, fails = invoke(override or run, gen)
        ran += 1
        if expected == NONE:
            ok = code == 0 and not fails
        else:
            ok = code != 0 and any(
                line.startswith(f"FAIL  {prefix} ") for line in fails for prefix in expected
            )
        bad += 0 if ok else 1
        shown = [line[6:44] for line in fails][:2]
        print(f"{'OK ' if ok else 'BAD'}  {name:<44} expect={'/'.join(expected):<10} exit={code} fails={shown}")
    print(f"MUTATION SELF-TEST rev3 ({MODE}): {ran - bad} of {ran} cases behaved as expected, {bad} did not")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
