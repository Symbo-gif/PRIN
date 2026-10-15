"""Compare an independent decomposition re-run with the committed S1 artefacts.

This is the S2 audit instrument for the first half of item 2 of the EXP-002
D1 S2 brief: *re-run the decomposition and compare its stems and summary with
the committed postfix JSON*.

``EVIDENCE/exp002-d1-s1/root_cause_decomposition.py`` is re-run with
``--label postfix`` and ``--out`` pointing **outside** the repository, so the
committed artefacts are never overwritten by an audit re-run. This script then
compares that scratch output with the committed postfix artefact field by
field, and reports the prefix artefact's summary alongside so the red to green
transition is visible in one place.

Two fields are *expected* to differ and are reported as such rather than as
failures:

* ``generated_utc`` -- the re-run happens at a different time;
* ``git_head`` -- the re-run happens at a later commit on the same branch.

Everything substantive must match exactly: ``stems`` (the per-stem digests and
attribution), ``summary``, ``prin_tree`` (which carries the H4 two-process
raw-identity result and the 21-file no-regression set), ``e3_records``,
``comparison``, and all four module digests.

Run from the repository root with the project venv::

    python EVIDENCE/exp002-d1-s2/decomposition_rerun_check.py <scratch-json>

Exit status is ``0`` when only the two expected provenance fields differ.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "EVIDENCE/exp002-d1-s1"
COMMITTED_POSTFIX = EVIDENCE / "root-cause-decomposition-postfix.json"
COMMITTED_PREFIX = EVIDENCE / "root-cause-decomposition-prefix.json"


def allowed_roots() -> tuple[Path, ...]:
    """Return the roots a caller-supplied input path may resolve inside.

    Returns:
        The repository root, the platform temporary root, and — when set —
        the directory named by ``PRIN_S2_SCRATCH``, each fully resolved.
    """
    roots = [ROOT, Path(tempfile.gettempdir()).resolve()]
    extra = os.environ.get("PRIN_S2_SCRATCH")
    if extra:
        roots.append(Path(extra).resolve())
    return tuple(roots)


def is_within(path: Path, root: Path) -> bool:
    """Return whether ``path`` is ``root`` itself or lives beneath it."""
    return path == root or root in path.parents


def guarded_input_path(raw: str, role: str) -> Path:
    """Resolve a caller-supplied input path safely and return it.

    Snyk Code flags an unsanitised ``argv`` path flowing into
    :class:`pathlib.Path` as CWE-23 path traversal. For an
    **evidence-producing** tool the sharper risk is integrity, not
    confidentiality: ``Path.is_file`` and ``Path.read_text`` follow symbolic
    links, so a linked input would be compared while the evidence named a
    different file — the "content verified, path provenance not" failure mode
    that audit finding ``PR23-F1`` fixed in ``tools/reproduce.py``. This guard
    mirrors that module's no-follow discipline and confines the *resolved*
    path to :func:`allowed_roots`, so a symlinked parent directory pointing
    outside is refused too.

    Args:
        raw: The path exactly as passed on the command line.
        role: Human-readable role used in any failure message.

    Returns:
        The resolved, confined path to a regular file.

    Raises:
        SystemExit: If the path is a symbolic link, is not a regular file, or
            resolves outside every allowed root.
    """
    candidate = Path(raw)
    if ".." in raw.replace("\\", "/").split("/"):
        raise SystemExit(f"{role}: refusing a path containing a '..' component: {raw}")
    if candidate.is_symlink():
        raise SystemExit(f"{role}: refusing symbolic link {candidate}")
    if candidate.exists() and not candidate.is_file():
        raise SystemExit(f"{role}: {candidate} is not a regular file")
    resolved = candidate.resolve()
    roots = allowed_roots()
    if not any(is_within(resolved, root) for root in roots):
        listed = ", ".join(str(root) for root in roots)
        raise SystemExit(f"{role}: {resolved} is outside the allowed roots ({listed})")
    if not resolved.is_file():
        raise SystemExit(f"{role}: no regular file at {resolved}")
    return resolved


#: Fields that legitimately differ between two runs of the same generator.
EXPECTED_PROVENANCE_DIFFERENCES = frozenset({"generated_utc", "git_head"})

#: Fields whose equality the audit treats as load-bearing.
SUBSTANTIVE_FIELDS = (
    "stems",
    "summary",
    "prin_tree",
    "e3_records",
    "comparison",
    "label",
    "port_module",
    "port_module_sha256",
    "reference_module_sha256",
    "reference_module_pin",
    "environment",
    "git_tracked_changes",
)


def load(path: Path) -> dict[str, Any]:
    """Return a JSON artefact parsed into a dictionary."""
    payload: dict[str, Any] = json.loads(path.read_text("utf-8"))
    return payload


def digest(path: Path) -> str:
    """Return the SHA-256 of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_size(value: Any) -> int:
    """Return the canonical-JSON length of a value, as a rough weight hint."""
    return len(json.dumps(value, sort_keys=True, default=str))


def main(argv: list[str]) -> int:
    """Compare the scratch re-run against the committed artefacts.

    Args:
        argv: A single element, the path to the re-run's scratch JSON.

    Returns:
        ``0`` when only the expected provenance fields differ, else ``1``.
    """
    if len(argv) != 1:
        print(__doc__)
        print("usage: decomposition_rerun_check.py <scratch-json>")
        return 2
    rerun_path = guarded_input_path(argv[0], "re-run artefact")

    committed = load(COMMITTED_POSTFIX)
    rerun = load(rerun_path)
    prefix = load(COMMITTED_PREFIX)

    print(f"committed postfix : {COMMITTED_POSTFIX}")
    print(f"                    sha256 {digest(COMMITTED_POSTFIX)}")
    print(f"independent re-run: {rerun_path}")
    print(f"                    sha256 {digest(rerun_path)}")
    print(f"committed prefix  : {COMMITTED_PREFIX}")
    print(f"                    sha256 {digest(COMMITTED_PREFIX)}")
    print()

    committed_keys = set(committed)
    rerun_keys = set(rerun)
    print("=== top-level key sets ===")
    print(f"committed only : {sorted(committed_keys - rerun_keys) or 'none'}")
    print(f"re-run only    : {sorted(rerun_keys - committed_keys) or 'none'}")
    print()

    print("=== field-by-field equality over shared keys ===")
    unexpected: list[str] = []
    expected: list[str] = []
    for key in sorted(committed_keys & rerun_keys):
        same = committed[key] == rerun[key]
        size = payload_size(committed[key])
        if same:
            print(f"SAME  {key}  (payload {size} chars)")
            continue
        print(f"DIFF  {key}  (payload {size} chars)")
        print(f"        committed: {json.dumps(committed[key], default=str)[:160]}")
        print(f"        re-run   : {json.dumps(rerun[key], default=str)[:160]}")
        if key in EXPECTED_PROVENANCE_DIFFERENCES:
            expected.append(key)
        else:
            unexpected.append(key)
    print()

    print("=== red to green transition, from the two committed artefacts ===")
    for label, artefact in (("prefix ", prefix), ("postfix", committed)):
        summary = artefact["summary"]
        print(
            f"  {label}  git_head={artefact['git_head'][:8]}  "
            f"port_sha256={artefact['port_module_sha256'][:16]}  "
            f"differing={summary['port_vs_reference_differing_count']}/39  "
            f"registered={summary['divergences_registered']}  "
            f"material={len(summary['divergences_byte_material'])}  "
            f"unexplained={len(summary['unexplained_stems'])}"
        )
    print()

    print("=== H4 and the no-regression set, from the committed postfix ===")
    tree = committed["prin_tree"]
    print(f"  files                        : {tree['files']}")
    print(f"  two_process_raw_identical    : {tree['two_process_raw_identical']}")
    print(f"  raw_equal_to_e3_prin_arm     : {len(tree['raw_equal_to_e3_prin_arm'])}")
    changed = len(tree["raw_differing_from_e3_prin_arm"])
    print(f"  raw_differing_from_e3_prin   : {changed}")
    print()
    print("  the 21 previously matching outputs, raw-identical to E3's PRIN arm:")
    for name in sorted(tree["raw_equal_to_e3_prin_arm"]):
        print(f"    = {name}")
    print("  the outputs that changed (must be exactly the 18-file D1 set):")
    for name in sorted(tree["raw_differing_from_e3_prin_arm"]):
        print(f"    X {name}")
    print()

    print("=== the prefix artefact's differing set (the red population) ===")
    for name in sorted(prefix["summary"]["port_vs_reference_differing_files"]):
        print(f"    X {name}")
    print()

    print("=== retained E3 roots versus their manifested records ===")
    for leg in ("reference", "prin", "seedrep0"):
        record = committed["e3_records"][leg]
        normalized = record["retained_normalized_sha256_matching_record"]
        print(
            f"  {leg:10s} present={record['retained_root_present']} "
            f"files={record['retained_files']} "
            f"raw_matches={record['retained_raw_sha256_matching_record']} "
            f"normalized_matches={normalized} "
            f"manifest_ok={record['reproduction_json_matches_manifest']}"
        )
    print()

    for field in SUBSTANTIVE_FIELDS:
        if field in unexpected:
            unexpected = [item for item in unexpected if item != field]
            unexpected.append(f"SUBSTANTIVE:{field}")

    print("=" * 78)
    print(f"expected provenance differences : {sorted(expected)}")
    print(f"unexpected differences          : {sorted(unexpected) or 'NONE'}")
    print("=" * 78)
    return 1 if unexpected else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
