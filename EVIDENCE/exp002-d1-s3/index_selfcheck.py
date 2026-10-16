"""Check that an EVIDENCE bundle's README indexes every file and every link works.

Backs the closure of audit finding ``EXP002D1-S2-F4`` (a committed S1 evidence
file that its own README did not list) and applies the same mechanical standard
to the S3 bundle. S2 found the defect by inspection; this makes it a command.

For one bundle ``EVIDENCE/<name>/`` it reports:

* **unindexed** — a file in the bundle (tracked or not yet committed, excluding
  ignored files) whose name is not linked from the bundle's ``README.md``;
* **dangling** — a relative Markdown link in the README that does not resolve to
  an existing file or directory.

The bundle is selected by *name* from the closed set of directories that exist
under ``EVIDENCE/``, so no caller-supplied string is turned into a filesystem
path. Files are listed with ``git ls-files --cached --others --exclude-standard``
so a not-yet-committed file is checked too, and ``__pycache__`` is ignored by
the repository's own ``.gitignore`` rules.

Run from the repository root::

    .venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/index_selfcheck.py exp002-d1-s1

Exit status is 0 when there are no unindexed files and no dangling links, 1
otherwise, 2 on a usage error.
"""

from __future__ import annotations

import re
import subprocess  # nosec B404 - fixed argv, no shell
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "EVIDENCE"
LINK = re.compile(r"\]\(([^)\s]+)\)")


def bundle_files(name: str) -> list[str]:
    """List a bundle's files (tracked or untracked-but-not-ignored).

    Args:
        name: The bundle directory name under ``EVIDENCE/``.

    Returns:
        Repository-relative POSIX paths, sorted.
    """
    out = subprocess.run(  # noqa: S603  # nosec B603 B607 - fixed argv, no shell
        [  # noqa: S607
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            f"EVIDENCE/{name}",
        ],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8")
    return sorted(set(out.splitlines()))


def readme_targets(readme: Path) -> list[str]:
    """Return the relative link targets in a README, without anchors.

    Args:
        readme: The README to parse.

    Returns:
        Link targets that are relative paths (URLs and pure anchors excluded).
    """
    targets = []
    for raw in LINK.findall(readme.read_text(encoding="utf-8")):
        target = unquote(raw.split("#", maxsplit=1)[0])
        if target and "://" not in target and not target.startswith("mailto:"):
            targets.append(target)
    return targets


def main(argv: list[str]) -> int:
    """Check one bundle named on the command line.

    Args:
        argv: Command-line arguments without the program name.

    Returns:
        The process exit status.
    """
    known = sorted(p.name for p in EVIDENCE.iterdir() if p.is_dir())
    if len(argv) != 1 or argv[0] not in known:
        print(f"usage: index_selfcheck.py <bundle>   (one of: {', '.join(known)})")
        return 2
    name = argv[0]
    bundle = EVIDENCE / name
    readme = bundle / "README.md"
    if not readme.is_file():
        print(f"{name}: no README.md")
        return 1
    linked = {Path(target).as_posix() for target in readme_targets(readme)}
    files = bundle_files(name)
    prefix = f"EVIDENCE/{name}/"
    local = [f[len(prefix) :] for f in files if f.startswith(prefix)]
    unindexed = [f for f in local if f != "README.md" and f not in linked]
    dangling = sorted(
        t for t in readme_targets(readme) if not (bundle / t).resolve().exists()
    )
    print(f"bundle {name}: {len(local)} files (README included)")
    print(f"  unindexed files : {unindexed or 'none'}")
    print(f"  dangling links  : {dangling or 'none'}")
    return 0 if not unindexed and not dangling else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
