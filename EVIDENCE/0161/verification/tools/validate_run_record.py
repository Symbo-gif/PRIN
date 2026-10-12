"""Independent admissibility check of one EXP-002 E3 run record.

Scope (protocol section 5.5, last paragraph; session 0161 brief): this checks the
record's metadata, result envelope, declared artefact mapping, manifest, source /
protocol / input identity, seed pair and directory inventory. It does NOT
evaluate any hypothesis, does NOT compare an observation with a prediction and
does NOT compare any publication output with another. It is deliberately written
without importing the driver, so a driver-side error cannot make a record look
admissible.

Usage:
    python -I validate_run_record.py <run_dir> --mode <mode> [--allow-outside-raw-root]

Exit status 0 only when every check passes.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath

REPO = Path(r"C:\dev\PRIN")
SOURCE_SHA = "fae24c4393c7a0232e6c8f0a6388b1775aa5fc05"
PROTOCOL_REL = (
    "DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/"
    "preregistration.md"
)
LOG_REL = (
    "DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/log.md"
)
EXPECT_PROTOCOL_SHA = "0f3073dd2ed73b64071bcf3ae182510a69a26bd575b81b5a97cc5a1f9bbc8c8b"
EXPECT_PROTOCOL_COMMIT = "9a9889d08dcaf2ad0ce31659ed67721b54b114d0"
EXPECT_APPROVAL_DATE = "2026-10-12"
EXPECT_INPUT_MANIFEST_SHA = (
    "300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5"
)
EXPECT_REFERENCE_INIT_SHA = (
    "ede92afc6771f2e29206534905e2820598ba841662a93d59f669f803a382f182"
)
REFERENCE_INIT = (
    "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/"
    "__init__.py"
)
PRIN_ADDITIONS = {"BackendUnavailableError", "__version__", "core_version"}
OPERATOR = "MichaelMaillet"
MODES = {
    "api": ("api-cpu", "api.json", ["H1"]),
    "conclusions": ("conclusions-cpu", "conclusions.json", ["H2"]),
    "reference": ("reproduction-reference-cpu", "reproduction.json", ["H3"]),
    "prin": ("reproduction-prin-cpu", "reproduction.json", ["H3", "H4"]),
    "repeatability": ("seedrep0-prin-cpu", "reproduction.json", ["H4"]),
}
RUN_RE = re.compile(
    r"RUN-(?P<utc>\d{8}T\d{6}Z)-(?P<sha>[0-9a-f]{7})-(?P<label>[a-z0-9-]+)\Z"
)
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
FAMILY_COUNTS = {"C01": 5, "C02": 42, "C03": 4, "C04": 5, "C05": 6}
API_ROW_KEYS = {
    "name",
    "resolved",
    "callable",
    "defining_module",
    "type",
    "error",
    "legacy",
    "ownership_present",
}
CASE_KEYS = {
    "case_id",
    "family",
    "input_file",
    "left_path",
    "right_path",
    "left",
    "operator",
    "right",
    "operand_unit",
    "expected",
    "observed",
}
RENDERER_KEYS = {
    "font_cache",
    "matplotlib",
    "numpy",
    "pillow",
    "freetype",
    "backend",
    "font_sha256",
}
FILE_INT_KEYS = ("raw_bytes", "normalized_bytes", "sensitivity_bytes")
FILE_DIGEST_KEYS = ("raw_sha256", "normalized_sha256", "sensitivity_sha256")
ENV_KEYS = {
    "prin_version",
    "git_commit",
    "rust_version",
    "python_version",
    "platform",
    "processor",
    "logical_cpus",
    "gpu",
    "gpu_vram_mb",
    "backend",
    "dtype",
    "seed",
}

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append((name, bool(ok), detail))
    return bool(ok)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, check=True, timeout=60
    ).stdout


def is_plain_file(path: Path) -> bool:
    return (
        path.is_file()
        and not path.is_symlink()
        and not (hasattr(path, "is_junction") and path.is_junction())
    )


def load_json(path: Path) -> object:
    return json.loads(path.read_bytes().decode("utf-8"))


def protocol_stems(protocol: str) -> tuple[list[str], list[str]]:
    figures = re.search(r"Registered figure stems.*?```text\n(.*?)```", protocol, re.S)
    tables = re.search(r"Registered table stems.*?```text\n(.*?)```", protocol, re.S)
    if figures is None or tables is None:
        raise RuntimeError("cannot parse the registered stems from the protocol blob")
    return figures.group(1).split(), tables.group(1).split()


def legacy_names() -> list[str]:
    payload = git("show", f"{SOURCE_SHA}:{REFERENCE_INIT}")
    if sha256_bytes(payload) != EXPECT_REFERENCE_INIT_SHA:
        raise RuntimeError("reference __init__ blob digest is not the pinned digest")
    for node in ast.parse(payload).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            return list(ast.literal_eval(node.value))
    raise RuntimeError("reference literal __all__ missing")


def main() -> int:
    """Run every check; an unexpected error is a FAIL, never a silent crash."""
    try:
        return _run()
    except Exception as exc:  # noqa: BLE001 - a crash must not look like a pass
        check("Z0 validator completed without an unexpected error", False, repr(exc))
        return finish()


def _run() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--mode", choices=sorted(MODES), required=True)
    parser.add_argument("--allow-outside-raw-root", action="store_true")
    args = parser.parse_args()

    run = args.run_dir.absolute()
    label, result_name, tags = MODES[args.mode]
    raw_root = REPO / "benchmarks/results/EXP-002"

    # ---- A. directory name, location and inventory ------------------------
    match = RUN_RE.fullmatch(run.name)
    check("A1 run directory name matches RUN-<UTC>-<R7>-<label>", match is not None)
    if match is not None:
        check(
            "A1 label is the registered label for the mode",
            match.group("label") == label,
            f"{match.group('label')} vs {label}",
        )
        check(
            "A1 embedded SHA is the first 7 characters of R",
            match.group("sha") == SOURCE_SHA[:7],
            match.group("sha"),
        )
        try:
            datetime.strptime(match.group("utc"), "%Y%m%dT%H%M%SZ")
            check("A1 embedded UTC stamp is a real timestamp", True, match.group("utc"))
        except ValueError:
            check("A1 embedded UTC stamp is a real timestamp", False)
    if not args.allow_outside_raw_root:
        check(
            "A2 run directory is a direct child of benchmarks/results/EXP-002",
            run.parent == raw_root,
            str(run.parent),
        )
    check("A2 run directory is a real directory (not a link)", run.is_dir() and not run.is_symlink())
    entries = sorted(os.scandir(run), key=lambda e: e.name)
    names = [e.name for e in entries]
    expected_names = sorted(["campaign-metadata.json", result_name, "manifest.json"])
    check(
        "A3 directory holds exactly sidecar, result and manifest",
        names == expected_names,
        f"{names}",
    )
    check(
        "A3 every entry is a plain regular file",
        all(is_plain_file(Path(e.path)) for e in entries),
    )
    if names != expected_names:
        return finish()

    # ---- B. manifest -------------------------------------------------------
    manifest = load_json(run / "manifest.json")
    assert isinstance(manifest, dict)
    files = manifest.get("files")
    check("B1 manifest schema_version == 1", manifest.get("schema_version") == 1)
    check("B1 manifest has a files list", isinstance(files, list))
    listed = {}
    if isinstance(files, list):
        for item in files:
            if isinstance(item, dict) and set(item) == {"path", "bytes", "sha256"}:
                listed[item["path"]] = item
        check(
            "B1 manifest lists exactly sidecar and result (not itself)",
            sorted(listed) == sorted(["campaign-metadata.json", result_name])
            and len(files) == 2,
            f"{sorted(listed)}",
        )
    for name in ("campaign-metadata.json", result_name):
        item = listed.get(name)
        data = (run / name).read_bytes()
        check(
            f"B2 {name} size equals manifest bytes",
            item is not None and item["bytes"] == len(data),
            f"{len(data)} vs {item and item['bytes']}",
        )
        check(
            f"B2 {name} SHA-256 equals manifest sha256 (recomputed)",
            item is not None
            and isinstance(item["sha256"], str)
            and HEX64.fullmatch(item["sha256"]) is not None
            and item["sha256"] == sha256_bytes(data),
            sha256_bytes(data),
        )

    # ---- C. campaign metadata sidecar -------------------------------------
    sidecar = load_json(run / "campaign-metadata.json")
    assert isinstance(sidecar, dict)
    check(
        "C1 sidecar keys are exactly the registered set",
        set(sidecar) == {"exp_id", "session", "run_id", "operator", "mode", "artefacts"},
        f"{sorted(sidecar)}",
    )
    check("C1 exp_id == EXP-002", sidecar.get("exp_id") == "EXP-002")
    check("C1 session == 0161", sidecar.get("session") == "0161")
    check("C1 run_id == directory name", sidecar.get("run_id") == run.name)
    check("C1 operator == MichaelMaillet", sidecar.get("operator") == OPERATOR)
    check("C1 mode == requested mode", sidecar.get("mode") == args.mode)
    check(
        "C1 artefact mapping is exactly {result: tags}",
        sidecar.get("artefacts") == {result_name: tags},
        f"{sidecar.get('artefacts')}",
    )

    # ---- D. result envelope ------------------------------------------------
    result = load_json(run / result_name)
    assert isinstance(result, dict)
    check(
        "D1 top-level keys are exactly the registered envelope",
        set(result)
        == {
            "environment",
            "config",
            "identity",
            "seed_used",
            "observations",
            "status",
            "elapsed_seconds",
            "started_at_utc",
            "recorded_at_utc",
        },
        f"{sorted(result)}",
    )
    check("D1 no abort_reason present", "abort_reason" not in result)
    check("D2 status == COMPLETED", result.get("status") == "COMPLETED", str(result.get("status")))
    check("D2 seed_used is False", result.get("seed_used") is False)
    env = result.get("environment")
    cfg = result.get("config")
    ident = result.get("identity")
    check("D3 environment/config/identity are objects", all(isinstance(x, dict) for x in (env, cfg, ident)))
    env = env if isinstance(env, dict) else {}
    cfg = cfg if isinstance(cfg, dict) else {}
    ident = ident if isinstance(ident, dict) else {}
    check("D3 environment keys are exactly the standard capture", set(env) == ENV_KEYS, f"{sorted(set(env) ^ ENV_KEYS)}")
    check("D3 prin_version == 1.0.0rc1", env.get("prin_version") == "1.0.0rc1")
    check("D3 git_commit == R", env.get("git_commit") == SOURCE_SHA)
    for field in ("rust_version", "python_version", "platform", "processor"):
        check(
            f"D3 environment.{field} is a non-empty string",
            isinstance(env.get(field), str) and bool(env[field].strip()),
            str(env.get(field)),
        )
    check(
        "D3 logical_cpus is an int >= 1",
        type(env.get("logical_cpus")) is int and env["logical_cpus"] >= 1,
        str(env.get("logical_cpus")),
    )
    check("D3 backend == cpu", env.get("backend") == "cpu")
    check("D3 dtype == f64", env.get("dtype") == "f64")
    check("D3 environment.seed == 0 (int)", type(env.get("seed")) is int and env["seed"] == 0)
    check(
        "D4 config keys are exactly the registered set",
        set(cfg)
        == {
            "iterations",
            "warmup",
            "seed_counter",
            "seed_key",
            "out_dir",
            "measurement_kind",
            "replicates",
        },
        f"{sorted(cfg)}",
    )
    check(
        "D4 seed pair (counter,key) == (0,2), both int",
        type(cfg.get("seed_counter")) is int
        and type(cfg.get("seed_key")) is int
        and (cfg["seed_counter"], cfg["seed_key"]) == (0, 2),
        f"({cfg.get('seed_counter')},{cfg.get('seed_key')})",
    )
    check(
        "D4 iterations==10, warmup==0, replicates==1 (envelope metadata)",
        (cfg.get("iterations"), cfg.get("warmup"), cfg.get("replicates")) == (10, 0, 1),
    )
    check(
        "D4 measurement_kind == deterministic_census",
        cfg.get("measurement_kind") == "deterministic_census",
    )
    out_dir = cfg.get("out_dir")
    parts = (
        PurePosixPath(out_dir.replace("\\", "/")).parts if isinstance(out_dir, str) else ()
    )
    check(
        "D4 out_dir ends benchmarks/results/EXP-002/<run name>, no '..'",
        ".." not in parts and parts[-4:] == ("benchmarks", "results", "EXP-002", run.name),
        str(out_dir),
    )

    # ---- D5. source / protocol / input identity ----------------------------
    head = git("rev-parse", "HEAD").decode().strip()
    check("D5 repository HEAD == R at validation time", head == SOURCE_SHA, head)
    check("D5 identity.source_sha == R", ident.get("source_sha") == SOURCE_SHA)
    commit = ident.get("preregistration_commit")
    check(
        "D5 preregistration_commit is the expected approval commit",
        commit == EXPECT_PROTOCOL_COMMIT,
        str(commit),
    )
    blob = b""
    if isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit):
        blob = git("show", f"{commit}:{PROTOCOL_REL}")
    check(
        "D5 preregistration_sha256 == digest of the blob at that commit (recomputed)",
        ident.get("preregistration_sha256") == sha256_bytes(blob) == EXPECT_PROTOCOL_SHA,
        f"{ident.get('preregistration_sha256')}",
    )
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", str(commit), SOURCE_SHA], cwd=REPO
    ).returncode
    check("D5 preregistration_commit is an ancestor of R", ancestor == 0)
    check(
        "D5 protocol blob at R is byte-identical to the blob at the approval commit",
        git("show", f"{SOURCE_SHA}:{PROTOCOL_REL}") == blob,
    )
    check(
        "D5 protocol blob is APPROVED with the dated MichaelMaillet approval",
        re.search(rb"^\*\*Status:\*\*[ \t]*APPROVED[ \t]*\r?$", blob, re.M) is not None
        and re.search(
            rb"^\*\*Maintainer approval:\*\*[ \t]*MichaelMaillet, 2026-10-12 UTC\b",
            blob,
            re.M,
        )
        is not None,
    )
    check(
        "D5 approval_date_utc == 2026-10-12",
        ident.get("approval_date_utc") == EXPECT_APPROVAL_DATE,
        str(ident.get("approval_date_utc")),
    )
    manifest_blob = git("show", f"{SOURCE_SHA}:paper/artefact_manifest.json")
    check(
        "D5 paper/artefact_manifest.json at R has the pinned digest",
        sha256_bytes(manifest_blob) == EXPECT_INPUT_MANIFEST_SHA,
    )
    check(
        "D5 identity.input_manifest_sha256 == pinned digest",
        ident.get("input_manifest_sha256") == EXPECT_INPUT_MANIFEST_SHA,
    )
    manifest_files = json.loads(manifest_blob)["files"]
    records = ident.get("input_records")
    check(
        "D5 input_record_count == 172 == len(input_records)",
        ident.get("input_record_count") == 172
        and isinstance(records, list)
        and len(records) == 172,
    )
    check(
        "D5 input_records equal the committed input manifest's records exactly",
        isinstance(records, list)
        and sorted(
            (r["path"], r["bytes"], r["sha256"]) for r in records if isinstance(r, dict)
        )
        == sorted((r["path"], r["bytes"], r["sha256"]) for r in manifest_files),
    )

    # ---- D6. timestamps ------------------------------------------------------
    try:
        started = datetime.fromisoformat(result["started_at_utc"])
        recorded = datetime.fromisoformat(result["recorded_at_utc"])
        wall = (recorded - started).total_seconds()
        elapsed = result["elapsed_seconds"]
        check(
            "D6 timestamps parse, are UTC and ordered; elapsed_seconds is a finite number",
            started.utcoffset() is not None
            and started.utcoffset().total_seconds() == 0
            and recorded >= started
            and isinstance(elapsed, (int, float))
            and not isinstance(elapsed, bool)
            and elapsed >= 0,
            f"started={result['started_at_utc']} recorded={result['recorded_at_utc']} "
            f"elapsed_seconds={elapsed} (timestamp difference {wall:.3f} s)",
        )
    except (KeyError, TypeError, ValueError) as exc:
        check("D6 timestamps parse and are ordered", False, repr(exc))

    # ---- E. observation schema (identity / cardinality only) ----------------
    obs = result.get("observations")
    check("E0 observations is an object", isinstance(obs, dict))
    obs = obs if isinstance(obs, dict) else {}
    protocol_text = blob.decode("utf-8")
    figure_stems, table_stems = protocol_stems(protocol_text)
    registered_files = sorted(
        [f"figures/{s}.{f}" for s in figure_stems for f in ("pdf", "png")]
        + [f"tables/{s}.tex" for s in table_stems]
    )
    if args.mode == "api":
        legacy = legacy_names()
        population = sorted(set(legacy) | PRIN_ADDITIONS)
        rows = obs.get("rows")
        check(
            "E1 frozen reference __all__ has 172 unique names; with the 3 PRIN additions the population is 175",
            len(legacy) == 172 and len(set(legacy)) == 172 and len(population) == 175,
        )
        check(
            "E1 observations.expected_names is exactly that registered 175-name population",
            obs.get("expected_names") == population,
        )
        check("E1 unit == api_symbol", obs.get("unit") == "api_symbol")
        check(
            "E1 rows: one per expected name, in sorted order, with the registered row keys",
            isinstance(rows, list)
            and [r.get("name") for r in rows if isinstance(r, dict)] == population
            and all(isinstance(r, dict) and set(r) == API_ROW_KEYS for r in rows),
        )
        for key in ("legacy_names", "observed_names", "frozen_missing", "frozen_extra"):
            value = obs.get(key)
            check(
                f"E1 {key} is a list of strings (content not judged)",
                isinstance(value, list) and all(isinstance(v, str) for v in value),
            )
        check(
            "E1 legacy_names equals the pinned reference __all__ (as a set)",
            sorted(obs.get("legacy_names") or []) == sorted(legacy),
        )
    elif args.mode == "conclusions":
        cases = obs.get("cases")
        check("E2 unit == claim_comparator_record", obs.get("unit") == "claim_comparator_record")
        ok_cases = isinstance(cases, list) and all(
            isinstance(c, dict) and CASE_KEYS <= set(c) for c in cases
        )
        check("E2 cases is a list of objects carrying the registered keys", ok_cases)
        if ok_cases:
            ids = [c["case_id"] for c in cases]
            check(
                "E2 62 uniquely labelled cases",
                len(cases) == 62 and len(set(ids)) == 62 and all(isinstance(i, str) for i in ids),
                f"{len(cases)} cases, {len(set(ids))} unique ids",
            )
            counts: dict[str, int] = {}
            for c in cases:
                counts[c["family"]] = counts.get(c["family"], 0) + 1
            check(
                "E2 registered family cardinalities C01=5 C02=42 C03=4 C04=5 C05=6",
                counts == FAMILY_COUNTS,
                f"{counts}",
            )
            check(
                "E2 every case_id starts with its family label",
                all(c["case_id"].startswith(c["family"] + ":") for c in cases),
            )
            check(
                "E2 expected and observed are real Booleans on every case (values not compared)",
                all(type(c["expected"]) is bool and type(c["observed"]) is bool for c in cases),
            )
            check(
                "E2 operands are finite numbers and operator is > or <",
                all(
                    isinstance(c["left"], (int, float))
                    and not isinstance(c["left"], bool)
                    and isinstance(c["right"], (int, float))
                    and not isinstance(c["right"], bool)
                    and c["operator"] in {">", "<"}
                    for c in cases
                ),
            )
    else:
        want_impl = "reference" if args.mode == "reference" else "prin"
        check("E3 unit == generated_file", obs.get("unit") == "generated_file")
        check(
            f"E3 implementation == {want_impl}",
            obs.get("implementation") == want_impl,
            str(obs.get("implementation")),
        )
        check(
            "E3 expected_files is exactly the registered 39-file list parsed from the protocol",
            obs.get("expected_files") == registered_files and len(registered_files) == 39,
        )
        renderer = obs.get("renderer")
        check(
            "E3 renderer capture carries the registered keys (font cache, versions, fonts)",
            isinstance(renderer, dict) and RENDERER_KEYS <= set(renderer),
        )
        if isinstance(renderer, dict):
            fc = renderer.get("font_cache")
            check(
                "E3 font cache digest was captured (not null) and fonts were hashed",
                isinstance(fc, dict)
                and isinstance(fc.get("sha256"), str)
                and HEX64.fullmatch(fc["sha256"]) is not None
                and isinstance(renderer.get("font_sha256"), dict)
                and len(renderer["font_sha256"]) > 0,
                f"font_cache={fc}",
            )
        file_records = obs.get("files")
        ok_files = isinstance(file_records, list) and all(
            isinstance(f, dict) for f in file_records
        )
        check("E3 files is a list of objects", ok_files)
        if ok_files:
            paths = [f.get("path") for f in file_records]
            check(
                "E3 file paths are unique strings",
                all(isinstance(p, str) for p in paths) and len(set(paths)) == len(paths),
            )
            check(
                "E3 raw/normalized/sensitivity byte sizes are non-negative ints",
                all(
                    type(f.get(k)) is int and f[k] >= 0
                    for f in file_records
                    for k in FILE_INT_KEYS
                ),
            )
            check(
                "E3 raw/normalized/sensitivity digests are 64-hex",
                all(
                    isinstance(f.get(k), str) and HEX64.fullmatch(f[k]) is not None
                    for f in file_records
                    for k in FILE_DIGEST_KEYS
                ),
            )

    # ---- G. repository state at validation time -----------------------------
    status = git("status", "--porcelain=v1", "--untracked-files=all").decode("utf-8")
    stray = []
    for line in status.splitlines():
        path = line[3:].strip().strip('"')
        if line.startswith("?? ") and (
            path.startswith("benchmarks/results/EXP-002/") or path == LOG_REL
        ):
            continue
        stray.append(line)
    check(
        "G1 only EXP-002 raw records and the E3 log differ from the clean checkout",
        not stray,
        f"{stray[:5]}",
    )
    check(
        "G2 no tracked file differs from HEAD",
        git("diff", "--name-only", "HEAD").decode().strip() == "",
    )
    check(
        "G3 no untracked top-level *.py / *.pth (ignored or not)",
        git("ls-files", "--others", "--", ":(glob)*.py", ":(glob)*.pth")
        .decode()
        .strip()
        == "",
    )

    # ---- F. retained publication roots (integrity only) --------------------
    if (
        args.mode in {"reference", "prin", "repeatability"}
        and not args.allow_outside_raw_root
    ):
        generated = REPO / "DOCS/test_and_benchmark_results/EXP-002" / run.name
        pub = generated / "publication"
        inputs = generated / "inputs"
        check(
            "F1 generated-output root, publication/ and inputs/ exist and are not links",
            all(p.is_dir() and not p.is_symlink() for p in (generated, pub, inputs)),
        )
        if pub.is_dir() and inputs.is_dir():
            on_disk = {
                p.relative_to(pub).as_posix(): p for p in pub.rglob("*") if p.is_file()
            }
            recorded = {
                f["path"]: f
                for f in obs.get("files", [])
                if isinstance(f, dict) and "path" in f
            }
            check(
                "F2 retained file set equals the record's file set (retention check only)",
                set(on_disk) == set(recorded),
                f"disk-only={sorted(set(on_disk) - set(recorded))[:5]} "
                f"record-only={sorted(set(recorded) - set(on_disk))[:5]}",
            )
            bad = [
                name
                for name, path in on_disk.items()
                if name in recorded
                and (
                    path.stat().st_size != recorded[name].get("raw_bytes")
                    or sha256_bytes(path.read_bytes()) != recorded[name].get("raw_sha256")
                )
            ]
            check(
                "F3 every retained file matches its own recorded raw size and SHA-256",
                not bad,
                f"mismatched={bad[:5]}",
            )
            snap = {
                p.relative_to(inputs).as_posix(): p
                for p in inputs.rglob("*")
                if p.is_file()
            }
            want = {
                r["path"]: r
                for r in (ident.get("input_records") or [])
                if isinstance(r, dict)
            }
            check(
                "F4 retained input snapshot equals the 172 recorded input records",
                set(snap) == set(want)
                and all(
                    snap[n].stat().st_size == want[n]["bytes"]
                    and sha256_bytes(snap[n].read_bytes()) == want[n]["sha256"]
                    for n in want
                ),
                f"snapshot files={len(snap)}",
            )
            listing = "".join(
                f"{p.relative_to(pub).as_posix()} {p.stat().st_size} "
                f"{hashlib.sha256(p.read_bytes()).hexdigest()}\n"
                for p in sorted(pub.rglob("*"))
                if p.is_file()
            )
            print(
                "LISTING-DIGEST (validator, formula of e2-review.md section 8): "
                f"{hashlib.sha256(listing.encode()).hexdigest()} "
                f"({len(listing.splitlines())} listed entries; no expectation applied)"
            )

    return finish()


def finish() -> int:
    width = max(len(name) for name, _, _ in results)
    failed = 0
    for name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        failed += 0 if ok else 1
        suffix = f"  [{detail}]" if detail and (not ok or len(detail) <= 140) else ""
        print(f"{mark}  {name.ljust(width)}{suffix}")
    print(f"SUMMARY: {len(results) - failed} passed, {failed} failed of {len(results)} checks")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
