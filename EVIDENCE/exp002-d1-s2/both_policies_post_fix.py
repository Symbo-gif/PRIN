r"""Re-derive H3 under both registered comparison policies on the corrected tree.

This is the S2 audit instrument for the S2 brief's instruction to weigh
S1.10 item 1: *post-fix, the §11.3 sensitivity policy gives 14/39 equal, and
the residual is line terminators plus PDF Info key sets*.

EXP-002 registered two comparisons for H3:

* the **approved §5.4 policy** (``exp002_driver.normalized_bytes``) -- tables
  with CRLF canonicalized to LF, PDFs with the four registered Info entries
  removed and xref offsets zeroed, PNGs by critical chunk. This is the primary
  verdict and the rule the parity gate applies.
* the **§11.3 sensitivity policy** (``exp002_driver.sensitivity_bytes``,
  E2 decision 9) -- the pre-exposure policy committed at ``6314532``: tables as
  **raw bytes**, PDFs with the four Info **values masked in place** so the key
  set and line wrapping survive, PNGs unchanged.

This instrument renders both arms once on the corrected tree, computes all
three digest families (raw, approved, sensitivity) for all 39 registered
files, and then **classifies** every residual difference under the sensitivity
policy rather than merely counting it:

* for ``.tex``, whether canonicalizing CRLF to LF in both arms is sufficient
  to make them equal, and how many CRLF sequences each arm carries;
* for ``.pdf``, the Info key set each arm writes, and whether the difference
  is confined to that key set once the approved normalization is applied.

The classification is what makes the S2 judgement possible: if every residual
is a writer or host property that the approved policy deliberately registers
as non-scientific, then the disagreement between the two policies is a
registration question for ``EXP-002-r1``, not a defect in this correction.

Run from the repository root with the project venv::

    python EVIDENCE/exp002-d1-s2/both_policies_post_fix.py

Writes only to a temporary directory; never to ``benchmarks/results/`` or
``DOCS/test_and_benchmark_results/``.
"""

from __future__ import annotations

import hashlib
import re
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import prinet.utils.figure_generation as reference_figures  # noqa: E402
import prinet.utils.table_generation as reference_tables  # noqa: E402

from benchmarks.campaign import exp002_driver as driver  # noqa: E402
from tools.reproduce import run_reproduction  # noqa: E402

RESULTS = driver.REFERENCE / "benchmarks" / "results"

#: Matches the trailer's ``/Info N M R`` reference.
INFO_REF = re.compile(rb"/Info\s+(\d+)\s+(\d+)\s+R")

#: Matches a top-level ``/Key`` inside a dictionary.
DICT_KEY = re.compile(rb"/([A-Za-z][A-Za-z0-9_]*)")

#: Matches a PDF literal string, including escaped parens and backslashes.
#: Stripping these before key extraction is required: the reference's Info
#: ``/Creator`` value embeds ``https://matplotlib.org``, whose ``/matplotlib``
#: would otherwise be misread as a dictionary key.
PDF_STRING = re.compile(rb"\((?:\\.|[^\\()])*\)")


def sha(payload: bytes) -> str:
    """Return the SHA-256 hex digest of ``payload``."""
    return hashlib.sha256(payload).hexdigest()


def pdf_info_keys(payload: bytes) -> list[str]:
    """Return the key names of a PDF's ``/Info`` dictionary.

    Args:
        payload: The raw PDF bytes.

    Returns:
        The Info dictionary's keys in appearance order, or an empty list when
        the document carries no indirect ``/Info`` reference.
    """
    match = INFO_REF.search(payload)
    if match is None:
        return []
    number, generation = match.group(1), match.group(2)
    pattern = re.escape(number) + rb"\s+" + re.escape(generation) + rb"\s+obj"
    start = re.search(pattern, payload)
    if start is None:
        return []
    end = payload.find(b"endobj", start.end())
    body = payload[start.end() : end if end != -1 else len(payload)]
    dictionary_end = body.find(b">>")
    dictionary = body[: dictionary_end if dictionary_end != -1 else len(body)]
    # Blank out literal strings first so a URL inside a value (the reference's
    # /Creator carries https://matplotlib.org) is not read as a dictionary key.
    without_strings = PDF_STRING.sub(b"()", dictionary)
    return [key.decode("ascii") for key in DICT_KEY.findall(without_strings)]


def count_crlf(payload: bytes) -> int:
    """Return the number of CRLF sequences in ``payload``."""
    return payload.count(b"\r\n")


def classify_tex(reference: bytes, prin: bytes) -> str:
    """Classify a ``.tex`` residual difference under the sensitivity policy."""
    if reference == prin:
        return "raw-equal"
    if reference.replace(b"\r\n", b"\n") == prin.replace(b"\r\n", b"\n"):
        return (
            "LINE TERMINATORS ONLY: equal after CRLF->LF in both arms "
            f"(reference CRLF={count_crlf(reference)}, PRIN CRLF={count_crlf(prin)})"
        )
    return "UNCLASSIFIED: differs beyond line terminators"


def classify_pdf(reference: bytes, prin: bytes) -> str:
    """Classify a ``.pdf`` residual difference under the sensitivity policy."""
    if reference == prin:
        return "raw-equal"
    ref_keys = pdf_info_keys(reference)
    prin_keys = pdf_info_keys(prin)
    approved_equal = driver.normalized_bytes(
        reference, ".pdf"
    ) == driver.normalized_bytes(prin, ".pdf")
    note = (
        f"Info key sets differ: reference={ref_keys} PRIN={prin_keys}; "
        f"equal under the approved policy={approved_equal}"
    )
    if approved_equal and ref_keys != prin_keys:
        return "INFO KEY SET ONLY: " + note
    if approved_equal:
        return "equal under the approved policy, same Info keys: " + note
    return "UNCLASSIFIED: " + note


def classify_png(reference: bytes, prin: bytes) -> str:
    """Classify a ``.png`` residual difference under the sensitivity policy."""
    if reference == prin:
        return "raw-equal"
    if driver.normalized_bytes(reference, ".png") == driver.normalized_bytes(
        prin, ".png"
    ):
        return "equal under PNG normalization (critical chunks identical)"
    return "UNCLASSIFIED: differs in critical chunks"


def render_arms(root: Path) -> dict[str, Path]:
    """Render the reference arm and the PRIN arm into ``root``.

    Args:
        root: A writable temporary directory.

    Returns:
        A mapping with the two arm directories.
    """
    reference = root / "reference"
    reference_figures.generate_all_figures(RESULTS, reference / "figures")
    reference_tables.generate_all_tables(RESULTS, reference / "tables")
    prin = root / "prin"
    run_reproduction(
        results_dir=RESULTS,
        output_dir=prin,
        manifest_path=driver.INPUT_MANIFEST,
        verify=True,
    )
    return {"reference": reference, "prin": prin}


def summarise(rows: Sequence[dict[str, Any]]) -> None:
    """Print per-policy equal/differ counts and the residual classification."""
    total = len(rows)
    for family, label in (
        ("raw", "raw bytes (H4's comparison)"),
        ("approved", "approved §5.4 policy (H3 primary)"),
        ("sensitivity", "§11.3 sensitivity policy (pre-exposure 6314532)"),
    ):
        equal = sum(1 for row in rows if row[f"{family}_equal"])
        print(
            f"  {label:48s} equal {equal:2d}/{total}  differ {total - equal:2d}/{total}"
        )
    print()

    differing = [row for row in rows if not row["sensitivity_equal"]]
    header = f"=== residual classification, sensitivity policy ({len(differing)}) ==="
    print(header)
    by_class: dict[str, int] = {}
    for row in differing:
        by_class.setdefault(row["classification"], 0)
        by_class[row["classification"]] += 1
    for classification, count in sorted(by_class.items(), key=lambda kv: -kv[1]):
        print(f"  x{count:2d}  {classification}")
    print()
    unclassified = [
        row["name"]
        for row in differing
        if row["classification"].startswith("UNCLASSIFIED")
    ]
    print(f"UNCLASSIFIED residuals: {unclassified or 'none'}")
    print()

    print("=== per-file detail (sensitivity policy) ===")
    print(f"{'file':46s} {'raw':5s} {'appr':5s} {'sens':5s} classification")
    for row in rows:
        print(
            f"{row['name']:46s} "
            f"{'=' if row['raw_equal'] else 'X':5s} "
            f"{'=' if row['approved_equal'] else 'X':5s} "
            f"{'=' if row['sensitivity_equal'] else 'X':5s} "
            f"{'' if row['sensitivity_equal'] else row['classification']}"
        )


def main() -> int:
    """Render both arms and report H3 under both registered policies."""
    pin_key = "src/prinet/utils/figure_generation.py"
    module_name = driver.normalized_bytes.__module__
    print(f"reference pin ({pin_key}) : {driver.REFERENCE_PINS[pin_key]}")
    print(f"comparison functions       : {module_name}.normalized_bytes")
    print(f"                             {module_name}.sensitivity_bytes")
    print()

    with tempfile.TemporaryDirectory(prefix="prin-s2-policies-") as temporary:
        arms = render_arms(Path(temporary))
        rows: list[dict[str, Any]] = []
        for name in sorted(driver.EXPECTED_FILES):
            suffix = Path(name).suffix
            reference = (arms["reference"] / name).read_bytes()
            prin = (arms["prin"] / name).read_bytes()
            row: dict[str, Any] = {
                "name": name,
                "raw_equal": reference == prin,
                "approved_equal": driver.normalized_bytes(reference, suffix)
                == driver.normalized_bytes(prin, suffix),
                "sensitivity_equal": driver.sensitivity_bytes(reference, suffix)
                == driver.sensitivity_bytes(prin, suffix),
                "reference_info_keys": pdf_info_keys(reference)
                if suffix == ".pdf"
                else None,
                "prin_info_keys": pdf_info_keys(prin) if suffix == ".pdf" else None,
            }
            if row["sensitivity_equal"]:
                row["classification"] = "equal"
            elif suffix == ".tex":
                row["classification"] = classify_tex(reference, prin)
            elif suffix == ".pdf":
                row["classification"] = classify_pdf(reference, prin)
            else:
                row["classification"] = classify_png(reference, prin)
            rows.append(row)

    print("=== H3 on the corrected tree, under both registered policies ===")
    summarise(rows)

    approved_equal = sum(1 for row in rows if row["approved_equal"])
    sensitivity_equal = sum(1 for row in rows if row["sensitivity_equal"])
    unclassified = [
        row for row in rows if row["classification"].startswith("UNCLASSIFIED")
    ]
    print("=" * 74)
    print(f"approved policy equal    : {approved_equal}/{len(rows)}")
    print(f"sensitivity policy equal : {sensitivity_equal}/{len(rows)}")
    print(f"policies agree           : {approved_equal == sensitivity_equal}")
    print(f"unclassified residuals   : {len(unclassified)}")
    print("=" * 74)
    return 1 if unclassified else 0


if __name__ == "__main__":
    sys.exit(main())
