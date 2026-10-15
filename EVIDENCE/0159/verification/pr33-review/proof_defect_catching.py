"""PR #33 review audit: prove the new regression tests catch each defect.

For every remediated driver finding this harness rebuilds the pre-fix
behaviour as a *mutant* of the current ``benchmarks/campaign/exp002_driver.py``
(one targeted source substitution), runs the finding's regression tests
against that mutant, and requires at least one failure. It also runs the same
tests against the unmutated driver and requires them all to pass. A finding
whose tests pass against its own mutant would be a vacuous test.

The mutant is built and loaded by ``proof_plugin.py`` (same directory), which
receives only the mutation's index in this constant table, under the real
module name and the real ``__file__``, so ``ROOT`` and every path constant are
unchanged; nothing in the repository is modified. Synthetic fixtures only —
no registered input is read and no EXP-002 run is created.

Usage (from the repository root)::

    .venv/Scripts/python EVIDENCE/0159/verification/pr33-review/proof_defect_catching.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DRIVER = ROOT / "benchmarks" / "campaign" / "exp002_driver.py"
HERE = Path(__file__).resolve().parent
TESTS = "tests/test_exp002_driver.py"

# (finding, description, current text, pre-fix text, test node selectors)
MUTATIONS: list[tuple[str, str, str, str, list[str]]] = [
    (
        "PR33-F1",
        "tables compared as raw bytes (no CRLF canonicalization)",
        'return payload.replace(b"\\r\\n", b"\\n")',
        "return payload",
        [
            "TestNormalizedBytes::test_tex_crlf_canonicalizes_to_lf",
            "TestArchivedTableNormalization",
        ],
    ),
    (
        "PR33-F2",
        "Info values masked in place (key set and wrapping kept)",
        "parts.append(_canonical_info(segment) if key == info_key else segment)",
        r'parts.append(re.sub(rb"/(CreationDate|ModDate|Creator|Producer)\s+'
        r'\((?:\\.|[^\\)])*\)", rb"/\1 (normalized)", segment) '
        r"if key == info_key else segment)",
        ["TestPdfInfoCanonicalization"],
    ),
    (
        "SA-1",
        "Info selected by object number only (self-audit F-B)",
        "parts.append(_canonical_info(segment) if key == info_key else segment)",
        "parts.append(_canonical_info(segment) if info_key is not None"
        " and key[0] == info_key[0] else segment)",
        ["TestSelfAuditPdf::test_same_number_other_generation_is_not_info"],
    ),
    (
        "SA-2",
        "repeated trailer structural keys accepted (self-audit F-H)",
        "        len(re.findall(key, dictionary.group(1))) > 1\n",
        "        False and len(re.findall(key, dictionary.group(1))) > 1\n",
        ["TestSelfAuditPdf::test_repeated_structural_key_rejected"],
    ),
    (
        "SA-3",
        "palette larger than the bit depth allows (self-audit F-G)",
        "        or (colour == 3 and palette_entries > 2**depth)\n",
        "",
        ["TestSelfAuditPng"],
    ),
    (
        "SA-4",
        "git timeout at closure escapes as SubprocessError (self-audit F-D)",
        "    except subprocess.SubprocessError as exc:\n"
        "        raise DriverError(\n"
        '            "recorded pre-registration commit cannot be resolved"',
        "    except subprocess.CalledProcessError as exc:\n"
        "        raise DriverError(\n"
        '            "recorded pre-registration commit cannot be resolved"',
        [
            "TestSelfAuditAdmissionAndClosure::test_git_timeout_at_closure_is_driver_error"
        ],
    ),
    (
        "SA-5",
        "tracked raw-record changes exempt from the clean-tree check (F-C)",
        '        ".",\n        f":!{log_relative}",\n    )\n    # Any modified',
        '        ".",\n        ":!benchmarks/results",\n        f":!{log_relative}",\n'
        "    )\n    # Any modified",
        ["TestSelfAuditAdmissionAndClosure::test_only_new_exp002_raw_files_are_exempt"],
    ),
    (
        "PR33-F3",
        "closure checks provenance shape only",
        "    _check_provenance(identity, source_sha)\n",
        "",
        [
            "TestCheckRunComplete::test_result_mutations_rejected",
            "TestClosureProvenance",
        ],
    ),
    (
        "PR33-F4",
        "closure never inspects observations",
        '    _check_observations(mode, result.get("observations"))\n',
        "",
        [
            "TestCheckRunComplete::test_result_mutations_rejected",
            "TestClosureObservations",
        ],
    ),
    (
        "PR33-F5",
        "generated-output guard missing before the RUN directory is created",
        "    if generated.exists() or generated.is_symlink():\n"
        '        raise DriverError("generated-output run root is never reused")\n'
        "    try:\n"
        "        run.mkdir()",
        "    try:\n        run.mkdir()",
        [
            "TestRunRegistered::test_generated_output_root_reuse_rejected",
            "TestReservationAtomicity",
        ],
    ),
    (
        "PR33-F7",
        "unbounded startxref decimal",
        r'rb"(?m)^startxref[ \t]*[\r\n]+([0-9]{1,10})[ \t]*[\r\n]+%%EOF[ \t\r\n]*\Z"',
        r'rb"(?m)^startxref[ \t]*[\r\n]+([0-9]+)[ \t]*[\r\n]+%%EOF[ \t\r\n]*\Z"',
        ["TestPdfDecimalBounds"],
    ),
    (
        "PR33-F7",
        "present-but-oversized /Info treated as absent",
        '    if info is None and re.search(rb"/Info\\b", dictionary.group(1)):\n',
        "    if False:\n",
        ["TestPdfDecimalBounds"],
    ),
    (
        "PR33-F8",
        "PLTE/tRNS placement and IHDR colour rules not enforced",
        "        or (colour == 3 and not palette)\n",
        "        or False\n",
        ["TestPngColourRules"],
    ),
    (
        "PR33-F8",
        "PLTE after the first IDAT accepted",
        '        or (palette and chunks.index(b"PLTE") > data_indices[0])\n',
        "        or False\n",
        ["TestPngColourRules"],
    ),
    (
        "PR33-F14",
        "unmeasurable storage entry escapes as ManifestMismatchError",
        "    except (OSError, ReproductionError) as exc:\n"
        '        raise DriverError(f"tracked storage cannot be measured: {exc}")'
        " from exc\n",
        "    except ZeroDivisionError:\n        raise\n",
        ["TestStorageMeasurement"],
    ),
    (
        "PR33-F15",
        "main() does not catch ReproductionError",
        "        ValueError,\n"
        "        ReproductionError,\n"
        "        subprocess.SubprocessError,",
        "        ValueError,\n        subprocess.SubprocessError,",
        ["TestMainReporting"],
    ),
    (
        "PR33-F21",
        "unresolved API row lacks the resolved-row keys",
        '                "callable": None,\n'
        '                "defining_module": None,\n'
        '                "type": None,\n',
        "",
        ["TestApiCensusInvariants::test_unresolved_row_has_the_resolved_row_schema"],
    ),
    (
        "PR33-F21",
        "no 172 + 3 population guard",
        "    if legacy & PRIN_ADDITIONS or len(expected) != API_SYMBOL_COUNT:\n",
        "    if False:\n",
        ["TestApiCensusInvariants::test_overlapping_additions_rejected"],
    ),
    (
        "PR33-F23",
        "closure ignores undeclared directory entries",
        "    if {entry.name for entry in run_dir.iterdir()} != {\n",
        "    if False and {entry.name for entry in run_dir.iterdir()} != {\n",
        ["TestClosureDirectoryHygiene"],
    ),
    (
        "PR33-F23",
        "closure does not validate the run-name UTC stamp",
        '    _utc_stamp(match.group("utc"))\n    _no_symlink_ancestors(run_dir)\n',
        "    _no_symlink_ancestors(run_dir)\n",
        ["TestClosureDirectoryHygiene::test_impossible_utc_stamp_rejected"],
    ),
    (
        "PR33-F29",
        "font-cache state not recorded",
        '        "font_cache": _font_cache_state(),\n',
        "",
        ["TestRenderEnvironment::test_font_cache_state_recorded"],
    ),
    (
        "PR33-F30",
        "untracked top-level shadowing modules not checked",
        "    if changed or source_untracked or shadowing:\n",
        "    if changed or source_untracked:\n",
        ["TestAdmissionScope::test_untracked_or_shadowing_file_refused"],
    ),
    (
        "PR33-F30",
        "committed protocol compared after strip()",
        '    if _git_bytes("show", f"HEAD:{protocol_relative}") != protocol_bytes:\n',
        '    if _git_bytes("show", f"HEAD:{protocol_relative}").strip()'
        " != protocol_bytes.strip():\n",
        ["TestAdmissionScope::test_committed_bytes_must_match_exactly"],
    ),
    (
        "PR33-F33",
        "missing conclusion keys escape as KeyError",
        "    except (KeyError, TypeError, IndexError) as exc:\n",
        "    except ZeroDivisionError as exc:\n",
        ["TestConclusionValidation"],
    ),
]


def _pytest(selectors: list[str], mutation: int | None) -> tuple[int, str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(HERE), str(ROOT), environment.get("PYTHONPATH", "")]
    )
    environment.pop("PR33_MUTATION_INDEX", None)
    if mutation is not None:
        environment["PR33_MUTATION_INDEX"] = str(mutation)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "-p",
        "proof_plugin",
        "-k",
        " or ".join(selector.replace("::", " and ") for selector in selectors),
        TESTS,
    ]
    completed = subprocess.run(  # noqa: S603 - fixed argv, this interpreter
        command,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    summary = [line for line in completed.stdout.splitlines() if line.strip()]
    return completed.returncode, summary[-1] if summary else "(no output)"


def main() -> int:
    """Run every mutation and report whether its regression tests catch it."""
    source = DRIVER.read_text(encoding="utf-8")
    failures = 0
    print(f"driver: {DRIVER.relative_to(ROOT).as_posix()}")
    for position, (finding, label, current, _, selectors) in enumerate(MUTATIONS):
        index = position + 1
        count = source.count(current)
        if count != 1:
            print(f"[{index:02d}] {finding} ANCHOR-ERROR ({count} matches): {label}")
            failures += 1
            continue
        base_code, base_summary = _pytest(selectors, None)
        mutant_code, mutant_summary = _pytest(selectors, position)
        caught = base_code == 0 and mutant_code == 1 and "failed" in mutant_summary
        failures += not caught
        print(
            f"[{index:02d}] {finding} {'CAUGHT' if caught else 'NOT-CAUGHT'}: "
            f"{label}\n     current -> exit {base_code}: {base_summary}\n"
            f"     mutant  -> exit {mutant_code}: {mutant_summary}"
        )
    print(f"RESULT: {len(MUTATIONS) - failures}/{len(MUTATIONS)} mutations caught")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
