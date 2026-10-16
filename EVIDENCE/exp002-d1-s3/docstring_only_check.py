"""Prove that a commit changed only a module docstring and/or comments.

Backs the closure of audit findings ``EXP002D1-S2-F5`` and ``EXP002D1-S2-F7``,
whose dispositions are *"comment-only, no assertion changes"* and
*"documentation-only, no behaviour change"*. A reviewer should not have to take
that on trust, so this instrument checks it mechanically: for each requested
``(revision A, revision B, path)`` it parses the file at both revisions, drops
the module docstring, and compares the two abstract syntax trees. Comments never
appear in an AST, so a comment-only edit also compares equal. If the trees are
equal, the two revisions define exactly the same executable code: every
statement, expression, constant, decorator, default and import.

The file at each revision is read from ``git show`` as bytes and decoded as
UTF-8 (a text-mode read would decode with the Windows locale codepage and turn
a character such as ``R²`` into a different string, a false difference).

Revisions must be hexadecimal commit ids, and the path must be a tracked file at
revision B; the path is never turned into a filesystem path, it is only handed to
``git show REV:PATH`` after that membership test.

Run from the repository root::

    .venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/docstring_only_check.py \
        --check <revA> <revB> <path> [--check <revA> <revB> <path> ...]

Exit status is 0 when every checked file is AST-identical outside its module
docstring, 1 when any differs, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess  # nosec B404 - fixed argv, no shell
import sys

REVISION = re.compile(r"[0-9a-f]{7,40}")


def git_bytes(*args: str) -> bytes:
    """Run a read-only ``git`` command and return its raw standard output.

    Args:
        *args: Arguments after ``git``.

    Returns:
        The command's standard output as bytes.

    Raises:
        subprocess.CalledProcessError: If git exits non-zero.
    """
    return subprocess.run(  # noqa: S603  # nosec B603 B607 - fixed argv, no shell
        ["git", *args],  # noqa: S607
        capture_output=True,
        check=True,
    ).stdout


def source_at(revision: str, path: str) -> str:
    """Return a tracked file's text at a revision, decoded as UTF-8.

    Args:
        revision: A hexadecimal commit id.
        path: A path that is tracked at that revision.

    Returns:
        The file's text.

    Raises:
        SystemExit: If the revision is malformed or the path is not tracked there.
    """
    if not REVISION.fullmatch(revision):
        raise SystemExit(f"not a hexadecimal revision: {revision!r}")
    tracked = git_bytes("ls-tree", "-r", "--name-only", revision).decode("utf-8")
    if path not in tracked.splitlines():
        raise SystemExit(f"{path!r} is not tracked at {revision}")
    return git_bytes("show", f"{revision}:{path}").decode("utf-8")


def without_module_docstring(source: str) -> tuple[str, str | None]:
    """Parse a module and split off its docstring.

    Args:
        source: Python source text.

    Returns:
        ``(ast.dump of the module without its docstring, the docstring)``.
    """
    tree = ast.parse(source)
    docstring = ast.get_docstring(tree, clean=False)
    first = tree.body[0] if tree.body else None
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        tree.body = tree.body[1:]
    return ast.dump(tree), docstring


def check(revision_a: str, revision_b: str, path: str) -> bool:
    """Compare one file across two revisions and print the verdict.

    Args:
        revision_a: Earlier revision.
        revision_b: Later revision.
        path: Tracked file path.

    Returns:
        ``True`` if the files are AST-identical outside the module docstring.
    """
    body_a, doc_a = without_module_docstring(source_at(revision_a, path))
    body_b, doc_b = without_module_docstring(source_at(revision_b, path))
    identical = body_a == body_b
    print(f"{path}  {revision_a}..{revision_b}")
    print(f"  ast identical outside the module docstring: {identical}")
    print(f"  module docstring changed                  : {doc_a != doc_b}")
    return identical


def main(argv: list[str]) -> int:
    """Parse arguments and run every requested comparison.

    Args:
        argv: Command-line arguments without the program name.

    Returns:
        The process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", maxsplit=1)[0])
    parser.add_argument(
        "--check",
        nargs=3,
        action="append",
        metavar=("REV_A", "REV_B", "PATH"),
        required=True,
    )
    args = parser.parse_args(argv)
    results = [check(*triple) for triple in args.check]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
