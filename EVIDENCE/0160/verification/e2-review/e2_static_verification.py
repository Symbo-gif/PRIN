"""EXP-002 E2: static re-derivation of the E1 provenance and population claims.

Reads committed sources and input *schemas/inventories* only. It does not
import the publication generators, render anything, evaluate an H2 predicate,
resolve a ``prin`` export, or create a RUN directory (no H1–H4 outcome).
Usage (repository root): python e2_static_verification.py
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
REF = ROOT / "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main"
PROTOCOL = (
    ROOT
    / "DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity"
    / "preregistration.md"
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def literal_all(path: Path) -> list[str]:
    for node in ast.parse(path.read_bytes()).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        ):
            value = ast.literal_eval(node.value)
            assert isinstance(value, list)
            return [str(v) for v in value]
    raise SystemExit(f"no literal __all__ in {path}")


checks: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str) -> None:
    checks.append((label, ok, detail))


protocol = PROTOCOL.read_text(encoding="utf-8")
table = dict(re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", protocol, re.M))
for name, expected in sorted(table.items()):
    path = (REF / name.removeprefix("REFERENCE/")) if name.startswith("REFERENCE/") else ROOT / name
    actual = sha(path)
    check(f"s1.1 digest {name}", actual == expected, actual[:16])

from benchmarks.campaign import exp002_driver as driver  # noqa: E402

check("driver INPUT_MANIFEST_SHA", sha(ROOT / "paper/artefact_manifest.json") == driver.INPUT_MANIFEST_SHA, driver.INPUT_MANIFEST_SHA[:16])
for rel, pinned in driver.REFERENCE_PINS.items():
    check(f"driver pin {rel}", sha(REF / rel) == pinned, pinned[:16])

legacy = literal_all(REF / "src/prinet/__init__.py")
prin_all = literal_all(ROOT / "python/prin/__init__.py")
check("reference __all__ = 172 unique", len(legacy) == 172 == len(set(legacy)), str(len(legacy)))
check("PRIN __all__ = 175 unique (static)", len(prin_all) == 175 == len(set(prin_all)), str(len(prin_all)))
check("PRIN additions disjoint from reference", not (driver.PRIN_ADDITIONS & set(legacy)), ", ".join(sorted(driver.PRIN_ADDITIONS)))
check("172 reference names + 3 additions = 175 expected", len(set(legacy) | driver.PRIN_ADDITIONS) == 175, "175")
check("PRIN literal __all__ = reference + additions (E1 static basis)", set(prin_all) == set(legacy) | driver.PRIN_ADDITIONS, "set equality")

manifest = json.loads((ROOT / "paper/artefact_manifest.json").read_text(encoding="utf-8"))
records = manifest["files"] if isinstance(manifest, dict) else manifest
names = {r["path"] for r in records}
check("input manifest has 172 records", len(records) == 172 == len(names), str(len(records)))
check("5 conclusion inputs are manifested", set(driver.CONCLUSION_FILES) <= names, ", ".join(driver.CONCLUSION_FILES))
check("14 figure stems, figures 2-15", len(driver.FIGURE_STEMS) == 14 and not any(s.startswith("fig1_") for s in driver.FIGURE_STEMS), str(len(driver.FIGURE_STEMS)))
check("39 registered publication files", len(driver.EXPECTED_FILES) == 39, str(len(driver.EXPECTED_FILES)))
archived = [REF / "paper" / name for name in driver.EXPECTED_FILES if name.startswith("tables/")]
check("11 archived tables present", len(archived) == 11 and all(p.is_file() for p in archived), str(len(archived)))
generators = re.findall(r"^def (fig_\w+)\(", (REF / "src/prinet/utils/figure_generation.py").read_text(encoding="utf-8"), re.M)
check("reference defines 14 figure generators (amendment #51)", len(generators) == 14, str(len(generators)))
status = re.search(r"^\*\*Status:\*\*[ \t]*([^\r\n]+)", protocol, re.M)
check("protocol header status", status is not None, status.group(1).strip() if status else "missing")
check("protocol SHA-256", True, sha(PROTOCOL))
check("driver SHA-256", True, sha(ROOT / "benchmarks/campaign/exp002_driver.py"))

width = max(len(label) for label, _, _ in checks)
for label, ok, detail in checks:
    print(f"{'PASS' if ok else 'FAIL'}  {label:<{width}}  {detail}")
failed = [label for label, ok, _ in checks if not ok]
print(f"RESULT: {len(checks) - len(failed)}/{len(checks)} checks passed")
raise SystemExit(1 if failed else 0)
