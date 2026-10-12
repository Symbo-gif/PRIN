"""Check that what is STAGED (the git index) is byte-identical to the working tree and to the manifests.

Read-only. Covers (1) every staged EXP-002 raw record file against the working tree and against the
per-run manifest.json entries, and (2) every EVIDENCE/<session>/verification file against its
SHA256SUMS.txt entry. With --head it checks the committed blobs of HEAD instead of the index.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(r"C:\dev\PRIN")
USE_HEAD = "--head" in sys.argv
SESSION = next((a for a in sys.argv[1:] if not a.startswith("--")), "0161")
REF = "HEAD" if USE_HEAD else ""  # 'git show :path' reads the index, 'git show HEAD:path' a commit


def blob(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{REF}:{path}"], cwd=REPO, capture_output=True, check=True
    ).stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def listed(prefix: str) -> list[str]:
    cmd = ["git", "ls-tree", "-r", "--name-only", "HEAD", "--", prefix] if USE_HEAD else [
        "git",
        "ls-files",
        "--",
        prefix,
    ]
    out = subprocess.run(cmd, cwd=REPO, capture_output=True, check=True, text=True).stdout
    return [line for line in out.splitlines() if line]


failures = 0
checked = 0


def verdict(ok: bool, text: str) -> None:
    global failures, checked
    checked += 1
    if not ok:
        failures += 1
        print(f"FAIL  {text}")


where = "HEAD commit" if USE_HEAD else "git index"
print(f"Byte-exactness check of the {where} against the working tree and manifests")

# (1) raw records
raw_files = [p for p in listed("benchmarks/results/EXP-002") if "/RUN-" in p]
runs = sorted({p.split("/")[3] for p in raw_files})
for run in runs:
    base = f"benchmarks/results/EXP-002/{run}"
    members = [p for p in raw_files if p.startswith(base + "/")]
    manifest = json.loads(blob(f"{base}/manifest.json"))
    entries = {e["path"]: e for e in manifest["files"]}
    for path in members:
        data = blob(path)
        work = (REPO / path).read_bytes()
        verdict(data == work, f"{path}: {where} blob differs from the working tree")
        name = path.rsplit("/", 1)[1]
        if name != "manifest.json":
            e = entries.get(name)
            verdict(
                e is not None and e["bytes"] == len(data) and e["sha256"] == sha(data),
                f"{path}: {where} blob does not match its manifest entry",
            )
    verdict(
        sorted(p.rsplit("/", 1)[1] for p in members)
        == sorted([*entries, "manifest.json"]),
        f"{base}: file set differs from the manifest entries plus manifest.json",
    )
    print(f"  {run}: {len(members)} files checked")

# (2) evidence bundle
evidence_root = f"EVIDENCE/{SESSION}/verification"
sums_path = f"{evidence_root}/SHA256SUMS.txt"
try:
    lines = blob(sums_path).decode("ascii").splitlines()
except subprocess.CalledProcessError:
    lines = []
    print(f"  (no {sums_path} in the {where})")
expected = {}
for line in lines:
    digest, _, rel = line.partition(" *./")
    expected[rel] = digest
members = [p for p in listed(evidence_root) if not p.endswith("/SHA256SUMS.txt")]
verdict(
    sorted(p[len(evidence_root) + 1 :] for p in members) == sorted(expected),
    f"{evidence_root}: SHA256SUMS.txt entries differ from the files in the {where}",
)
for path in members:
    rel = path[len(evidence_root) + 1 :]
    data = blob(path)
    verdict(sha(data) == expected.get(rel), f"{path}: {where} blob does not match SHA256SUMS.txt")
    work = REPO / path
    if work.exists():
        verdict(data == work.read_bytes(), f"{path}: {where} blob differs from the working tree")
print(f"  {evidence_root}: {len(members)} files checked against {len(expected)} manifest entries")
print(f"SUMMARY: {checked} comparisons, {failures} failed")
sys.exit(1 if failures else 0)
