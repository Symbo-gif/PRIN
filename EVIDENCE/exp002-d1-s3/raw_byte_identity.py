"""Show that a change to ``figure_generation.py`` moved no output byte.

Backs the closure of audit finding ``EXP002D1-S2-F6``. Restoring the reference's
fig13 per-series ``label=`` is meant to be byte-immaterial, because fig13 draws
no legend. S2 reported the two generators equal under the registered
*normalized* comparison and equal at artist level, but a change that was
"immaterial" has to be shown to stay immaterial, and the strongest available
statement is the plain one: render every figure with the module before and after
the change, and compare the **raw** bytes.

For each of the two revisions this renders all fourteen historical figures
(``generate_all_figures``) from the archived PRINet 3.0 benchmark JSON into a
temporary directory and records the SHA-256 of every ``.pdf`` and ``.png``. The
two digest tables must be identical. PRIN's raw output is deterministic (EXP-002
hypothesis H4), so any difference is a real change in the output, not noise.

Each revision's module source is read with ``git show`` as bytes (UTF-8) and
imported from a temporary file under a distinct module name, so the two variants
coexist in one process without editing the working tree. ``worktree`` as the
after-revision means the file as it currently is on disk.

Revisions must be hexadecimal commit ids (or the word ``worktree`` for the
after-revision only); no caller-supplied string becomes a filesystem path.

Run from the repository root::

    .venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/raw_byte_identity.py \
        --before <rev> [--after <rev>|worktree]

Exit status is 0 when the digest tables are identical (and non-empty), 1 when
any file differs, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import shutil
import subprocess  # nosec B404 - fixed argv, no shell
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MODULE_REL = "python/prin/reporting/figure_generation.py"
MODULE_PATH = ROOT / "python" / "prin" / "reporting" / "figure_generation.py"
RESULTS = (
    ROOT
    / "DOCS"
    / "archive and reference from PRINet 3.0"
    / "PRINet-3.0.0-main"
    / "benchmarks"
    / "results"
)
REVISION = re.compile(r"[0-9a-f]{7,40}")

#: ``git`` resolved once to an absolute path (Coding Standards section 6.1:
#: "absolute executables"), as ``tools/check_deviation_ledger.py`` does.
_GIT = shutil.which("git")
if _GIT is None:
    raise SystemExit("git was not found on PATH")
GIT: str = _GIT


def module_source(revision: str) -> bytes:
    """Return the module's source bytes at a revision (or on disk).

    Args:
        revision: A hexadecimal commit id, or ``worktree``.

    Returns:
        The file's bytes.

    Raises:
        SystemExit: If the revision is malformed.
    """
    if revision == "worktree":
        return MODULE_PATH.read_bytes()
    if not REVISION.fullmatch(revision):
        raise SystemExit(f"not a hexadecimal revision: {revision!r}")
    return subprocess.run(  # noqa: S603  # nosec B603 - absolute git, fixed argv, no shell
        [GIT, "show", f"{revision}:{MODULE_REL}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout


def load_variant(source: bytes, name: str, scratch: Path) -> ModuleType:
    """Import a copy of the module from ``source`` under the name ``name``.

    Args:
        source: The module's source bytes.
        name: A unique module name.
        scratch: A directory the copy may be written to.

    Returns:
        The imported module.
    """
    path = scratch / f"{name}.py"
    path.write_bytes(source)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import the {name} variant")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def digests(module: Any, output: Path) -> dict[str, str]:
    """Render every figure with ``module`` and hash the raw output files.

    Args:
        module: A loaded variant of ``figure_generation``.
        output: Directory to render into (made an allowed output root).

    Returns:
        A mapping from file name to the SHA-256 of its raw bytes.
    """
    output.mkdir(parents=True)
    module.ALLOWED_OUTPUT_ROOTS = (output.resolve(),)
    module.generate_all_figures(RESULTS, output)
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output.iterdir())
    }


def main(argv: list[str]) -> int:
    """Compare the raw digest tables of two revisions.

    Args:
        argv: Command-line arguments without the program name.

    Returns:
        The process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", maxsplit=1)[0])
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", default="worktree")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="prin-s3-rawid-") as scratch_name:
        scratch = Path(scratch_name)
        before = digests(
            load_variant(module_source(args.before), "figgen_before", scratch),
            scratch / "before",
        )
        after = digests(
            load_variant(module_source(args.after), "figgen_after", scratch),
            scratch / "after",
        )
    differing = sorted(
        n for n in before.keys() | after.keys() if before.get(n) != after.get(n)
    )
    print(f"before: {args.before}   after: {args.after}")
    print(f"files rendered: before {len(before)}, after {len(after)}")
    print(f"raw-byte identical: {len(before) - len(differing)}")
    print(f"raw-byte differing: {len(differing)} {differing or ''}")
    for name in sorted(before):
        print(f"  {before[name]}  {name}")
    return 0 if before and not differing else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
