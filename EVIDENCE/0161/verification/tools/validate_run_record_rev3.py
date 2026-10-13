"""Independent admissibility check of one EXP-002 E3 run record (revision 3).

Scope (protocol section 5.5, last paragraph; session 0161 brief): this checks the
record's metadata, result envelope, declared artefact mapping, manifest, source /
protocol / input identity, seed pair and directory inventory. It does NOT
evaluate any hypothesis, does NOT compare an observation with a prediction and
does NOT compare any publication output with another. It is deliberately written
without importing the driver, so a driver-side error cannot make a record look
admissible.

Revision 3 adds the strictness that the read-only cold review of the E3 round
found missing in revisions 1-2 (Devin F-01..F-06): symlink / junction ancestors
(S1), integer types of the registered numbers (S2), strict JSON without duplicate
keys or non-finite constants (S3), exact key sets below the envelope (S4), UTC
offsets, finite and consistent timing (S5), manifest typing and an exact
``out_dir`` (S6). It also accepts ``--generated-root`` so the retention checks
(F1-F4) can be exercised against a relocated copy.

Usage:
    python -I validate_run_record_rev3.py <run_dir> --mode <mode>
        [--allow-outside-raw-root] [--generated-root <dir>]

Exit status 0 only when every check passes.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
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
C02_EXTRA_CASE_KEYS = {"K", "alpha_radians"}
RENDERER_KEYS = {
    "font_cache",
    "matplotlib",
    "numpy",
    "pillow",
    "freetype",
    "backend",
    "font_sha256",
}
FONT_CACHE_KEYS = {"name", "sha256"}
FILE_INT_KEYS = ("raw_bytes", "normalized_bytes", "sensitivity_bytes")
FILE_DIGEST_KEYS = ("raw_sha256", "normalized_sha256", "sensitivity_sha256")
FILE_BASE_KEYS = {"path", *FILE_INT_KEYS, *FILE_DIGEST_KEYS}
FILE_TABLE_KEYS = FILE_BASE_KEYS | {
    "archived_bytes",
    "archived_sha256",
    "archived_normalized_bytes",
    "archived_normalized_sha256",
}
IDENTITY_KEYS = {
    "source_sha",
    "preregistration_sha256",
    "preregistration_commit",
    "approval_date_utc",
    "input_manifest_sha256",
    "input_record_count",
    "input_records",
}
INPUT_RECORD_KEYS = {"path", "bytes", "sha256"}
API_OBS_KEYS = {
    "expected_names",
    "legacy_names",
    "observed_names",
    "frozen_missing",
    "frozen_extra",
    "rows",
    "unit",
}
CONC_OBS_KEYS = {"cases", "unit"}
PUB_OBS_KEYS = {"implementation", "renderer", "expected_files", "files", "unit"}
MANIFEST_KEYS = {"schema_version", "description", "source", "files"}
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


def linked_ancestors(path: Path) -> list[str]:
    """Return the path and every ancestor that is a symlink or a junction."""
    found = []
    for candidate in (path.absolute(), *path.absolute().parents):
        if candidate.is_symlink() or (
            hasattr(candidate, "is_junction") and candidate.is_junction()
        ):
            found.append(str(candidate))
    return found


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = [key for key, _ in pairs]
    if len(set(keys)) != len(keys):
        raise ValueError(f"duplicate JSON key in {sorted(k for k in keys if keys.count(k) > 1)}")
    return dict(pairs)


def _reject_constant(name: str) -> object:
    raise ValueError(f"non-finite JSON constant {name}")


def strict_load(path: Path) -> object:
    """UTF-8 (no BOM) JSON without duplicate keys or NaN / Infinity constants."""
    text = path.read_bytes().decode("utf-8")
    if text.startswith("\ufeff"):
        raise ValueError("byte-order mark")
    return json.loads(
        text, object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant
    )


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


def is_int(value: object) -> bool:
    return type(value) is int


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
    parser.add_argument("--generated-root", type=Path, default=None)
    parser.add_argument(
        "--exact-out-dir",
        action="store_true",
        help="require out_dir to equal the run directory even with --allow-outside-raw-root",
    )
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
    check(
        "A2 run directory is a real directory (not a link)",
        run.is_dir() and not run.is_symlink(),
    )
    linked = linked_ancestors(run)
    check(
        "S1 neither the run directory nor any ancestor is a symlink or junction",
        not linked,
        f"{linked}",
    )
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

    # ---- S3. strict JSON of the three files --------------------------------
    loaded: dict[str, object] = {}
    for name in ("manifest.json", "campaign-metadata.json", result_name):
        try:
            loaded[name] = strict_load(run / name)
            check(
                f"S3 {name} is strict JSON (UTF-8, no BOM, no duplicate key, no NaN/Infinity)",
                True,
            )
        except (ValueError, UnicodeDecodeError) as exc:
            check(
                f"S3 {name} is strict JSON (UTF-8, no BOM, no duplicate key, no NaN/Infinity)",
                False,
                repr(exc),
            )
    if len(loaded) != 3:
        return finish()

    # ---- B. manifest -------------------------------------------------------
    manifest = loaded["manifest.json"]
    check("B1 manifest is a JSON object", isinstance(manifest, dict))
    manifest = manifest if isinstance(manifest, dict) else {}
    files = manifest.get("files")
    check(
        "S6 manifest keys are exactly schema_version, description, source, files",
        set(manifest) == MANIFEST_KEYS,
        f"{sorted(set(manifest) ^ MANIFEST_KEYS)}",
    )
    check(
        "B1 manifest schema_version is the integer 1",
        is_int(manifest.get("schema_version")) and manifest["schema_version"] == 1,
    )
    check("B1 manifest has a files list", isinstance(files, list))
    listed: dict[str, dict[str, object]] = {}
    if isinstance(files, list):
        for item in files:
            if isinstance(item, dict) and set(item) == {"path", "bytes", "sha256"}:
                listed[str(item["path"])] = item
        check(
            "B1 manifest lists exactly sidecar and result (not itself), each with exact keys",
            sorted(listed) == sorted(["campaign-metadata.json", result_name])
            and len(files) == 2,
            f"{sorted(listed)}",
        )
    for name in ("campaign-metadata.json", result_name):
        item = listed.get(name)
        data = (run / name).read_bytes()
        check(
            f"B2 {name} size equals manifest bytes (integer)",
            item is not None and is_int(item["bytes"]) and item["bytes"] == len(data),
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
    sidecar = loaded["campaign-metadata.json"]
    check("C1 sidecar is a JSON object", isinstance(sidecar, dict))
    sidecar = sidecar if isinstance(sidecar, dict) else {}
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
    result = loaded[result_name]
    check("D1 result is a JSON object", isinstance(result, dict))
    result = result if isinstance(result, dict) else {}
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
    check(
        "D3 environment/config/identity are objects",
        all(isinstance(x, dict) for x in (env, cfg, ident)),
    )
    env = env if isinstance(env, dict) else {}
    cfg = cfg if isinstance(cfg, dict) else {}
    ident = ident if isinstance(ident, dict) else {}
    check(
        "D3 environment keys are exactly the standard capture",
        set(env) == ENV_KEYS,
        f"{sorted(set(env) ^ ENV_KEYS)}",
    )
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
        is_int(env.get("logical_cpus")) and env["logical_cpus"] >= 1,
        str(env.get("logical_cpus")),
    )
    check("D3 backend == cpu", env.get("backend") == "cpu")
    check("D3 dtype == f64", env.get("dtype") == "f64")
    check("D3 environment.seed == 0 (int)", is_int(env.get("seed")) and env["seed"] == 0)
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
        is_int(cfg.get("seed_counter"))
        and is_int(cfg.get("seed_key"))
        and (cfg["seed_counter"], cfg["seed_key"]) == (0, 2),
        f"({cfg.get('seed_counter')},{cfg.get('seed_key')})",
    )
    check(
        "S2 iterations, warmup and replicates are integers equal to 10, 0 and 1",
        all(is_int(cfg.get(k)) for k in ("iterations", "warmup", "replicates"))
        and (cfg["iterations"], cfg["warmup"], cfg["replicates"]) == (10, 0, 1),
        f"{[cfg.get(k) for k in ('iterations', 'warmup', 'replicates')]}",
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
    if not args.allow_outside_raw_root or args.exact_out_dir:
        check(
            "S6 out_dir is exactly the absolute run directory",
            isinstance(out_dir, str) and Path(out_dir) == run,
            f"{out_dir} vs {run}",
        )

    # ---- D5. source / protocol / input identity ----------------------------
    head = git("rev-parse", "HEAD").decode().strip()
    check(
        "D5 repository HEAD descends from R (HEAD == R, or R is an ancestor of HEAD)",
        head == SOURCE_SHA
        or subprocess.run(
            ["git", "merge-base", "--is-ancestor", SOURCE_SHA, head], cwd=REPO
        ).returncode
        == 0,
        head,
    )
    check("D5 identity.source_sha == R", ident.get("source_sha") == SOURCE_SHA)
    check(
        "S4 identity keys are exactly the registered seven",
        set(ident) == IDENTITY_KEYS,
        f"{sorted(set(ident) ^ IDENTITY_KEYS)}",
    )
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
        is_int(ident.get("input_record_count"))
        and ident["input_record_count"] == 172
        and isinstance(records, list)
        and len(records) == 172,
    )
    check(
        "S4 every input record has exactly the keys path, bytes, sha256",
        isinstance(records, list)
        and all(isinstance(r, dict) and set(r) == INPUT_RECORD_KEYS for r in records),
    )
    check(
        "D5 input_records equal the committed input manifest's records exactly",
        isinstance(records, list)
        and all(isinstance(r, dict) and INPUT_RECORD_KEYS <= set(r) for r in records)
        and sorted((r["path"], r["bytes"], r["sha256"]) for r in records)
        == sorted((r["path"], r["bytes"], r["sha256"]) for r in manifest_files),
    )

    # ---- D6. timestamps ------------------------------------------------------
    try:
        started = datetime.fromisoformat(result["started_at_utc"])
        recorded = datetime.fromisoformat(result["recorded_at_utc"])
        wall = (recorded - started).total_seconds()
        elapsed = result["elapsed_seconds"]
        elapsed_ok = (
            isinstance(elapsed, (int, float))
            and not isinstance(elapsed, bool)
            and math.isfinite(elapsed)
            and elapsed >= 0
        )
        check(
            "S5 both timestamps carry a zero UTC offset and are ordered; elapsed_seconds is a finite number >= 0",
            started.utcoffset() == timedelta(0)
            and recorded.utcoffset() == timedelta(0)
            and recorded >= started
            and elapsed_ok,
            f"started={result['started_at_utc']} recorded={result['recorded_at_utc']} "
            f"elapsed_seconds={elapsed}",
        )
        check(
            "S5 elapsed_seconds agrees with the timestamps (within 1 s)",
            elapsed_ok and abs(wall - elapsed) <= 1.0,
            f"timestamp difference {wall:.3f} s vs elapsed_seconds {elapsed}",
        )
    except (KeyError, TypeError, ValueError) as exc:
        check("S5 timestamps parse, are UTC and ordered", False, repr(exc))

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
    registered_tables = {f"tables/{s}.tex" for s in table_stems}
    if args.mode == "api":
        legacy = legacy_names()
        population = sorted(set(legacy) | PRIN_ADDITIONS)
        rows = obs.get("rows")
        check(
            "S4 api observations have exactly the registered seven keys",
            set(obs) == API_OBS_KEYS,
            f"{sorted(set(obs) ^ API_OBS_KEYS)}",
        )
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
            "E1 rows: one per expected name, in sorted order, with exactly the registered row keys",
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
        check(
            "S4 conclusions observations have exactly the keys cases and unit",
            set(obs) == CONC_OBS_KEYS,
            f"{sorted(set(obs) ^ CONC_OBS_KEYS)}",
        )
        check("E2 unit == claim_comparator_record", obs.get("unit") == "claim_comparator_record")
        ok_cases = isinstance(cases, list) and all(
            isinstance(c, dict) and CASE_KEYS <= set(c) for c in cases
        )
        check("E2 cases is a list of objects carrying the registered keys", ok_cases)
        if ok_cases:
            check(
                "S4 every case has exactly the registered keys (C02 cases add K and alpha_radians)",
                all(
                    set(c)
                    == (CASE_KEYS | C02_EXTRA_CASE_KEYS if c.get("family") == "C02" else CASE_KEYS)
                    for c in cases
                ),
            )
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
                    and math.isfinite(c["left"])
                    and isinstance(c["right"], (int, float))
                    and not isinstance(c["right"], bool)
                    and math.isfinite(c["right"])
                    and c["operator"] in {">", "<"}
                    for c in cases
                ),
            )
    else:
        want_impl = "reference" if args.mode == "reference" else "prin"
        check(
            "S4 publication observations have exactly the registered five keys",
            set(obs) == PUB_OBS_KEYS,
            f"{sorted(set(obs) ^ PUB_OBS_KEYS)}",
        )
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
            "S4 renderer capture has exactly the registered seven keys",
            isinstance(renderer, dict) and set(renderer) == RENDERER_KEYS,
        )
        if isinstance(renderer, dict):
            fc = renderer.get("font_cache")
            check(
                "E3 font cache digest was captured (not null) with exactly the keys name and sha256, and fonts were hashed",
                isinstance(fc, dict)
                and set(fc) == FONT_CACHE_KEYS
                and isinstance(fc.get("sha256"), str)
                and HEX64.fullmatch(fc["sha256"]) is not None
                and isinstance(renderer.get("font_sha256"), dict)
                and len(renderer["font_sha256"]) > 0
                and all(
                    isinstance(v, str) and HEX64.fullmatch(v) is not None
                    for v in renderer["font_sha256"].values()
                ),
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
                "S4 every file record has exactly the registered keys (the 11 archived-table files add four archived_* keys)",
                all(
                    set(f) == (FILE_TABLE_KEYS if f.get("path") in registered_tables else FILE_BASE_KEYS)
                    for f in file_records
                ),
            )
            check(
                "E3 raw/normalized/sensitivity byte sizes are non-negative ints",
                all(
                    is_int(f.get(k)) and f[k] >= 0
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
    frozen_paths = [
        "python",
        "crates",
        "benchmarks/campaign/exp002_driver.py",
        "benchmarks/_common",
        "tests",
        "tools",
        "paper",
        "parity",
        PROTOCOL_REL,
        "DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/e2-review.md",
    ]
    drift = git("diff", "--name-only", SOURCE_SHA, "--", *frozen_paths).decode().split()
    check(
        "G1 no product, driver, shared-benchmark, test, tool, paper, parity, protocol or e2-review file differs between R and the working tree",
        not drift,
        f"{drift[:5]}",
    )
    check(
        "G3 no untracked top-level *.py / *.pth (ignored or not)",
        git("ls-files", "--others", "--", ":(glob)*.py", ":(glob)*.pth")
        .decode()
        .strip()
        == "",
    )

    # ---- F. retained publication roots (integrity only) --------------------
    publication = args.mode in {"reference", "prin", "repeatability"}
    if publication and (not args.allow_outside_raw_root or args.generated_root is not None):
        generated = args.generated_root or (
            REPO / "DOCS/test_and_benchmark_results/EXP-002" / run.name
        )
        generated = generated.absolute()
        pub = generated / "publication"
        inputs = generated / "inputs"
        check(
            "F1 generated-output root, publication/ and inputs/ exist and are not links",
            all(p.is_dir() and not p.is_symlink() for p in (generated, pub, inputs)),
        )
        linked_generated = linked_ancestors(generated)
        check(
            "S1 neither the generated-output root nor any ancestor is a symlink or junction",
            not linked_generated,
            f"{linked_generated}",
        )
        if pub.is_dir() and inputs.is_dir():
            on_disk = {
                p.relative_to(pub).as_posix(): p for p in pub.rglob("*") if p.is_file()
            }
            recorded_files = {
                f["path"]: f
                for f in obs.get("files", [])
                if isinstance(f, dict) and "path" in f
            }
            check(
                "F2 retained file set equals the record's file set (retention check only)",
                set(on_disk) == set(recorded_files),
                f"disk-only={sorted(set(on_disk) - set(recorded_files))[:5]} "
                f"record-only={sorted(set(recorded_files) - set(on_disk))[:5]}",
            )
            bad = [
                name
                for name, path in on_disk.items()
                if name in recorded_files
                and (
                    path.stat().st_size != recorded_files[name].get("raw_bytes")
                    or sha256_bytes(path.read_bytes()) != recorded_files[name].get("raw_sha256")
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
