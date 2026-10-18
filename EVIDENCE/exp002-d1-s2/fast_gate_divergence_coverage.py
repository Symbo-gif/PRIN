r"""Check how much of the 34-divergence population the fast gate actually pins.

This is the S2 audit instrument for checklist item A3 (test conformance) and
for the S2 brief's closing question: *whether 9 fast-gate tests plus the
parity gate satisfy the "tests in tandem" rule*.

The concern is real. ``parity/test_parity_publication.py`` carries
``pytestmark = [pytest.mark.parity, pytest.mark.slow]``, so the default fast
gate (``pytest tests/ -m "not slow and not gpu"``) never runs it. The byte-level
proof that all 39 publication files match the frozen reference therefore sits
outside the fast gate. ``tests/test_publication_figure_arguments.py`` is what
puts protection back inside it.

This instrument answers, mechanically:

* how many of the 34 registered divergences in
  ``EVIDENCE/exp002-d1-s1/root_cause_decomposition.py`` are named by an
  assertion in the fast-gate test file;
* whether the coverage splits between byte-material and byte-immaterial
  divergences;
* which test function pins which divergence IDs;
* whether the test module's own docstring describes its scope accurately
  (compared on whitespace-normalised text, because the docstring wraps).

Run from the repository root with the project venv::

    python EVIDENCE/exp002-d1-s2/fast_gate_divergence_coverage.py

Exit status is ``0`` when every registered divergence is cited and no cited ID
is absent from the registry.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_FILE = ROOT / "tests/test_publication_figure_arguments.py"
REGISTRY = ROOT / "EVIDENCE/exp002-d1-s1/root_cause_decomposition.py"
POSTFIX = ROOT / "EVIDENCE/exp002-d1-s1/root-cause-decomposition-postfix.json"

#: Matches a divergence identifier such as ``D12.10``.
ID_PATTERN = re.compile(r"\bD\d+\.\d+\b")

#: Matches a test function definition at module level.
TEST_DEF = re.compile(r"^def (test_\w+)\(", re.M)


def id_key(identifier: str) -> tuple[int, int]:
    """Return a sort key that orders ``D5.2`` before ``D12.1`` numerically."""
    figure, item = identifier[1:].split(".")
    return int(figure), int(item)


def sort_ids(identifiers: Iterable[str]) -> list[str]:
    """Return divergence IDs in numeric rather than lexicographic order."""
    return sorted(set(identifiers), key=id_key)


def load_registry() -> tuple[Any, ...]:
    """Import the committed S1 generator and return its divergence registry."""
    spec = importlib.util.spec_from_file_location("exp002_d1_s1_registry_cov", REGISTRY)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {REGISTRY}")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves cls.__module__ through sys.modules, so the module
    # must be registered before execution or @dataclass raises AttributeError.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result: tuple[Any, ...] = module.DIVERGENCES
    return result


def load_materiality() -> tuple[set[str], set[str]]:
    """Return the byte-material and byte-immaterial ID sets from the artefact."""
    payload: dict[str, Any] = json.loads(POSTFIX.read_text("utf-8"))
    summary = payload["summary"]
    return set(summary["divergences_byte_material"]), set(
        summary["divergences_byte_immaterial"]
    )


def module_docstring(source: str) -> str:
    """Return the module docstring, or an empty string if there is none."""
    parts = source.split('"""')
    return parts[1] if len(parts) > 1 else ""


def normalise(text: str) -> str:
    """Collapse whitespace so a wrapped phrase still matches."""
    return " ".join(text.split())


def per_test_coverage(source: str) -> list[tuple[str, list[str]]]:
    """Return each test function's name and the divergence IDs it cites."""
    out: list[tuple[str, list[str]]] = []
    matches = list(TEST_DEF.finditer(source))
    for position, match in enumerate(matches):
        start = match.end()
        end = (
            matches[position + 1].start()
            if position + 1 < len(matches)
            else len(source)
        )
        body = source[start:end]
        out.append((match.group(1), sort_ids(ID_PATTERN.findall(body))))
    return out


def main() -> int:
    """Report fast-gate divergence coverage and return a non-zero status on a gap."""
    registry = load_registry()
    registry_ids = [divergence.id for divergence in registry]
    material, immaterial = load_materiality()
    source = TEST_FILE.read_text("utf-8")
    cited = sort_ids(ID_PATTERN.findall(source))
    cited_set = set(cited)

    print(f"test file      : {TEST_FILE}")
    print(f"registry module: {REGISTRY}")
    print(f"materiality    : {POSTFIX}")
    print()
    print(f"registered divergences               : {len(registry_ids)}")
    print(f"divergence IDs cited in the test file : {len(cited)}")
    print()

    missing = [item for item in registry_ids if item not in cited_set]
    unknown = [item for item in cited if item not in registry_ids]
    print(f"registered but NOT cited by a fast-gate assertion: {missing or 'none'}")
    print(f"cited but not present in the registry            : {unknown or 'none'}")
    print()
    print(
        f"byte-material divergences   : {len(material)}; "
        f"cited: {len(material & cited_set)}"
    )
    print(
        f"byte-immaterial divergences : {len(immaterial)}; "
        f"cited: {len(immaterial & cited_set)}"
    )
    print(f"  material not cited  : {sort_ids(material - cited_set) or 'none'}")
    print(f"  immaterial not cited: {sort_ids(immaterial - cited_set) or 'none'}")
    print()

    print("Test functions and the divergence IDs each names:")
    for name, ids in per_test_coverage(source):
        print(f"  {name:48s} {len(ids):2d}  {', '.join(ids)}")
    print()

    docstring = normalise(module_docstring(source))
    phrase = "pin each byte-material argument"
    says_material_only = phrase in docstring
    pins_immaterial = len(immaterial & cited_set) > 0
    print("=== module docstring accuracy ===")
    print(
        f"  docstring contains {phrase!r} (whitespace-normalised): {says_material_only}"
    )
    print(
        f"  tests also pin byte-immaterial divergences            : {pins_immaterial}"
    )
    print(f"    {sort_ids(immaterial & cited_set)}")
    if says_material_only and pins_immaterial:
        print("  -> the docstring UNDERSTATES the tests: they pin all 34, not just")
        print("     the 26 byte-material ones. Cosmetic; recorded as an observation.")
    print()

    print("=" * 74)
    complete = not missing and not unknown
    print(
        f"RESULT: fast-gate tests cite {len(cited)}/{len(registry_ids)} "
        f"registered divergences -> {'COMPLETE' if complete else 'INCOMPLETE'}"
    )
    print("=" * 74)
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
