"""DV-044: PSR-039 inherits the historical cumulative ledger plus its deltas."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools import check_deviation_ledger as ledger

ROOT = Path(__file__).resolve().parents[1]
HEADER = "| ID | Raised (cycle) | Severity | Summary | Status | Reference |"
SEP = "|---|---|---|---|---|---|"


def _write_psr(path: Path, section: str) -> Path:
    """Write a tiny, local report with only one ledger section."""
    path.write_text(
        "# Local fixture\n\n## 3. Deviation ledger (cumulative)\n\n"
        + section
        + "\n\n## 4. Other\n",
        encoding="utf-8",
    )
    return path


def test_explicit_delta_inherits_base_and_ignores_short_local_table(
    tmp_path: Path,
) -> None:
    """A five-column finding table cannot replace 128 earlier findings."""
    base = _write_psr(
        tmp_path / "038-project-state.md",
        HEADER + "\n|---|---|---|---|---|---|\n"
        "| A-F1 | 038 | D4 | base summary | FIXED | no hash |",
    )
    child = _write_psr(
        tmp_path / "039-project-state.md",
        "| ID | Severity | Summary | Status | Reference |\n"
        "|---|---|---|---|---|\n"
        "| B-F1 | D4 | child summary | FIXED | no hash |\n\n"
        "### 3.4 Cumulative delta\n\n"
        "**Cumulative ledger delta:** Inherit PSR-038 \u00a73.\n\n"
        + HEADER
        + "\n|---|---|---|---|---|---|\n"
        "| B-F1 | 039 | D4 | child summary | FIXED | no hash |",
    )
    assert [row.finding_id for row in ledger.parse_ledger(base)] == ["A-F1"]
    rows = ledger.parse_ledger(child)
    assert [(row.finding_id, row.summary) for row in rows] == [
        ("A-F1", "base summary"),
        ("B-F1", "child summary"),
    ]
    assert ledger.diff_ledgers(ledger.parse_ledger(base), rows) == []


def test_short_local_table_without_canonical_delta_fails_closed(
    tmp_path: Path,
) -> None:
    """A delegation in prose cannot excuse dropping local findings."""
    _write_psr(
        tmp_path / "038-project-state.md",
        HEADER + "\n|---|---|---|---|---|---|\n"
        "| A-F1 | 038 | D4 | base summary | FIXED | no hash |",
    )
    child = _write_psr(
        tmp_path / "039-project-state.md",
        "| ID | Severity | Summary | Status | Reference |\n"
        "|---|---|---|---|---|\n"
        "| B-F1 | D4 | child summary | FIXED | no hash |\n\n"
        "Inherits PSR-038 \u00a73, but has no canonical delta table.",
    )
    with pytest.raises(ValueError, match="local finding tables require"):
        ledger.parse_ledger(child)


def test_delta_cannot_rewrite_an_inherited_summary(tmp_path: Path) -> None:
    """An overlapping ID is allowed only with an identical summary."""
    _write_psr(
        tmp_path / "038-project-state.md",
        HEADER + "\n|---|---|---|---|---|---|\n"
        "| A-F1 | 038 | D4 | base summary | FIXED | no hash |",
    )
    child = _write_psr(
        tmp_path / "039-project-state.md",
        "**Cumulative ledger delta:** Inherit PSR-038 \u00a73.\n\n"
        + HEADER
        + "\n|---|---|---|---|---|---|\n"
        "| A-F1 | 039 | D4 | altered summary | FIXED | no hash |",
    )
    with pytest.raises(ValueError, match="changes an inherited summary"):
        ledger.parse_ledger(child)


def test_cyclic_or_missing_delegation_fails_closed(tmp_path: Path) -> None:
    """Never turn a cycle or a vanished predecessor into an empty ledger."""
    cycle = _write_psr(
        tmp_path / "039-project-state.md",
        "The full ledger is in PSR-039 \u00a73.",
    )
    with pytest.raises(ValueError, match="cyclic"):
        ledger.parse_ledger(cycle)
    absent = _write_psr(
        tmp_path / "040-project-state.md",
        "The full ledger is in PSR-038 \u00a73.",
    )
    with pytest.raises(ValueError, match="missing delegated ledger"):
        ledger.parse_ledger(absent)


def test_malformed_canonical_row_or_empty_marked_delta_fails(
    tmp_path: Path,
) -> None:
    """A syntactically plausible partial row cannot silently disappear."""
    malformed = _write_psr(
        tmp_path / "041-project-state.md",
        HEADER + "\n|---|---|---|---|---|---|\n| X-F1 | 041 | D4 | too short | FIXED |",
    )
    with pytest.raises(ValueError, match="malformed canonical"):
        ledger.parse_ledger(malformed)
    empty = _write_psr(
        tmp_path / "042-project-state.md",
        "**Cumulative ledger delta:** Inherit PSR-041 \u00a73.",
    )
    with pytest.raises(ValueError, match="marker has no canonical rows"):
        ledger.parse_ledger(empty)


def test_psr039_erratum_preserves_every_inherited_and_added_id(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The actual 038-to-039 governance comparison is the regression gate."""
    previous_path = ROOT / "DOCS/reports/038-project-state.md"
    current_path = ROOT / "DOCS/reports/039-project-state.md"
    previous = ledger.parse_ledger(previous_path)
    current = ledger.parse_ledger(current_path)
    assert len(previous) == 128
    assert len(current) == 142
    assert len({row.finding_id for row in current}) == 142
    current_ids = {row.finding_id for row in current}
    assert {row.finding_id for row in previous} <= current_ids
    assert {f"WP038-F{i}" for i in range(1, 7)} <= current_ids
    assert {"EXP001-D1-H1", "EXP001-D1-H2a", "EXP001-E5-F1"} <= current_ids
    assert {f"S2-F{i}" for i in range(1, 6)} <= current_ids
    assert ledger.diff_ledgers(previous, current) == []
    # WP005-F1 has escaped pipes in an older reference; its hash and whole
    # reference must survive parsing instead of being truncated at \\|.
    historical = next(row for row in current if row.finding_id == "WP005-F1")
    assert "| 13 |" in historical.reference
    assert (
        ledger.main([str(previous_path), str(current_path), "--repo", str(ROOT)]) == 0
    )
    assert "Compared 128 rows" in capsys.readouterr().out


def test_duplicate_id_invalid_severity_and_empty_field_rejected(
    tmp_path: Path,
) -> None:
    """Rows that look plausible but are incomplete must fail closed."""
    duplicate = _write_psr(
        tmp_path / "043-project-state.md",
        HEADER + "\n" + SEP + "\n"
        "| D-F1 | 043 | D4 | a | FIXED | no hash |\n"
        "| D-F1 | 043 | D4 | a | FIXED | no hash |",
    )
    with pytest.raises(ValueError, match="duplicate ledger ID"):
        ledger.parse_ledger(duplicate)
    bad_severity = _write_psr(
        tmp_path / "044-project-state.md",
        HEADER + "\n" + SEP + "\n| E-F1 | 044 | D9 | a | FIXED | no hash |",
    )
    with pytest.raises(ValueError, match="incomplete canonical"):
        ledger.parse_ledger(bad_severity)
    empty_field = _write_psr(
        tmp_path / "045-project-state.md",
        HEADER + "\n" + SEP + "\n| F-F1 | 045 | D4 |  | FIXED | no hash |",
    )
    with pytest.raises(ValueError, match="incomplete canonical"):
        ledger.parse_ledger(empty_field)


def test_lettered_psr_delegation_resolves_zero_padded_numeric(
    tmp_path: Path,
) -> None:
    """`PSR-036a §3` resolves `036a-project-state.md`, not `36a-...` (DV044-F1)."""
    base = _write_psr(
        tmp_path / "036a-project-state.md",
        HEADER + "\n" + SEP + "\n| G-F1 | 036 | D4 | base | FIXED | no hash |",
    )
    child = _write_psr(
        tmp_path / "037-project-state.md",
        "The full ledger is in PSR-036a \u00a73.",
    )
    assert [row.finding_id for row in ledger.parse_ledger(base)] == ["G-F1"]
    assert [row.finding_id for row in ledger.parse_ledger(child)] == ["G-F1"]


def test_header_only_canonical_table_requires_delta_marker(
    tmp_path: Path,
) -> None:
    """An empty canonical table cannot silently delegate to a valid base."""
    _write_psr(
        tmp_path / "038-project-state.md",
        HEADER + "\n" + SEP + "\n| A-F1 | 038 | D4 | base | FIXED | no hash |",
    )
    child = _write_psr(
        tmp_path / "039-project-state.md",
        HEADER + "\n" + SEP + "\n\nInherits PSR-038 \u00a73.",
    )
    with pytest.raises(ValueError, match="canonical table has no rows"):
        ledger.parse_ledger(child)


def test_psr_literal_inside_table_cell_cannot_redirect_delegation(
    tmp_path: Path,
) -> None:
    """A `PSR-NNN §3` string in a summary cell is data, not a pointer (F2)."""
    _write_psr(
        tmp_path / "030-project-state.md",
        HEADER + "\n" + SEP + "\n| H-F1 | 030 | D4 | base | FIXED | no hash |",
    )
    _write_psr(
        tmp_path / "038-project-state.md",
        HEADER + "\n" + SEP + "\n| A-F1 | 038 | D4 | base | FIXED | no hash |",
    )
    child = _write_psr(
        tmp_path / "039-project-state.md",
        "**Cumulative ledger delta:** Inherit PSR-038 \u00a73.\n\n"
        + HEADER
        + "\n"
        + SEP
        + "\n"
        "| B-F1 | 039 | D4 | see PSR-030 \u00a73 for origin | FIXED | no hash |",
    )
    rows = ledger.parse_ledger(child)
    assert {row.finding_id for row in rows} == {"A-F1", "B-F1"}


def test_escaped_backslash_before_delimiter_keeps_parity(
    tmp_path: Path,
) -> None:
    """`\\\\|` is a literal backslash + delimiter; `\\|` is an escaped pipe."""
    _write_psr(
        tmp_path / "038-project-state.md",
        HEADER + "\n" + SEP + "\n| A-F1 | 038 | D4 | base | FIXED | no hash |",
    )
    child = _write_psr(
        tmp_path / "039-project-state.md",
        "**Cumulative ledger delta:** Inherit PSR-038 \u00a73.\n\n"
        + HEADER
        + "\n"
        + SEP
        + "\n"
        "| B-F1 | 039 | D4 | trail\\\\ | FIXED | no hash |\n"
        "| C-F1 | 039 | D4 | inner\\|pipe | FIXED | no hash |",
    )
    rows = {row.finding_id: row for row in ledger.parse_ledger(child)}
    assert rows["B-F1"].summary == "trail\\"
    assert rows["C-F1"].summary == "inner|pipe"


def test_main_returns_2_when_git_or_file_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Environment failures are clean exit-2 errors, not consistency failures."""
    missing = _write_psr(
        tmp_path / "038-project-state.md",
        HEADER + "\n" + SEP + "\n| A-F1 | 038 | D4 | base | FIXED | `663e3cf` |",
    )
    monkeypatch.setattr(
        ledger.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("git missing")),
    )
    assert ledger.main([str(missing)]) == 2
