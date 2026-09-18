"""Tests for ``tools/check_global_session_registration.py`` (EDA-002 D-F1).

The headline case this tool exists for is the real, recurring gap EDA-002
found: EMA-007 (``DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_007.md``) had no
row in ``SESSION_REGISTER.md`` at all — the third occurrence of this exact
class of gap (after EMA-001 and EMA-003). ``test_flags_real_ema007_gap``
reproduces that exact shape (real filename, real pre-fix register content)
and asserts the tool would have caught it.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from check_global_session_registration import (
    AuditReport,
    derive_session_id,
    find_reports,
    find_violations,
    main,
    registered_session_ids,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

_SESSION_REGISTER_TEXT = (
    "# PRIN Master Session Register\n\n"
    "## Global sessions — Executive Audits\n\n"
    "| EA | Date | Session brief | Git state | Status |\n"
    "|---|---|---|---|---|\n"
    "| EA-006 | 2026-08-26 | Executive Audit Session 006 | `main` @ "
    "`5d90427` | COMPLETE |\n\n"
    "## Global sessions — Executive Mathematical Audits\n\n"
    "| EMA | Date | Session brief | Git state | Status |\n"
    "|---|---|---|---|---|\n"
    "| EMA-006 | 2026-09-01 | Executive Mathematical Audit Session 006 | "
    "`main` @ `fa427ad` | COMPLETE |\n\n"
    "## Global sessions — Executive Documentation Audits\n\n"
    "| EDA | Date | Session brief | Git state | Status |\n"
    "|---|---|---|---|---|\n"
    "| EDA-001 | 2026-09-01 | Executive Documentation Audit Session 001 | "
    "`main` @ `cf81f05` | COMPLETE |\n\n"
    "## Global sessions — Executive Testing and CI Audits\n\n"
    "| ETCA | Date | Session brief | Git state | Status |\n"
    "|---|---|---|---|---|\n"
    "| ETCA-002 | 2026-09-02 | Executive Testing and CI Audit Session 002 | "
    "`main` @ `adbb1e3` | COMPLETE |\n"
)


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _make_reports_dir(tmp_path: Path, filenames: list[str]) -> Path:
    audits_dir = tmp_path / "audits"
    audits_dir.mkdir()
    for filename in filenames:
        _write(audits_dir / filename, "placeholder report content\n")
    return audits_dir


class TestDeriveSessionId:
    def test_ea_report(self) -> None:
        assert derive_session_id("EXECUTIVE_AUDIT_REPORT_006.md") == "EA-006"

    def test_ema_report(self) -> None:
        assert derive_session_id("EXECUTIVE_MATH_AUDIT_REPORT_007.md") == "EMA-007"

    def test_eda_report(self) -> None:
        assert (
            derive_session_id("EXECUTIVE_DOCUMENTATION_AUDIT_REPORT_002.md")
            == "EDA-002"
        )

    def test_etca_report(self) -> None:
        assert (
            derive_session_id("EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_002.md")
            == "ETCA-002"
        )

    def test_ema_preparation_document_is_not_a_report(self) -> None:
        """The EMA-002 preparation document is not itself an audit report
        and must not be mistaken for one (it has no own register row)."""
        assert derive_session_id("EXECUTIVE_MATH_AUDIT_PREPARATION_002.md") is None

    def test_template_files_are_not_reports(self) -> None:
        assert derive_session_id("TEMPLATE_Executive_Audit_Report.md") is None
        assert derive_session_id("TEMPLATE_Executive_Math_Audit_Report.md") is None

    def test_per_wp_audit_is_not_a_global_report(self) -> None:
        assert derive_session_id("036f-wp036f-audit.md") is None
        assert derive_session_id("001-wp001-audit.md") is None

    def test_readme_is_not_a_report(self) -> None:
        assert derive_session_id("README.md") is None


class TestFindReports:
    def test_discovers_only_matching_files(self, tmp_path: Path) -> None:
        audits_dir = _make_reports_dir(
            tmp_path,
            [
                "EXECUTIVE_MATH_AUDIT_REPORT_007.md",
                "EXECUTIVE_MATH_AUDIT_PREPARATION_002.md",
                "TEMPLATE_Executive_Audit_Report.md",
                "036f-wp036f-audit.md",
                "README.md",
            ],
        )
        reports = find_reports(audits_dir)
        assert [r.session_id for r in reports] == ["EMA-007"]


class TestRegisteredSessionIds:
    def test_parses_ids_across_all_four_tables(self, tmp_path: Path) -> None:
        path = tmp_path / "sessions.md"
        _write(path, _SESSION_REGISTER_TEXT)
        ids = registered_session_ids(path)
        assert ids == {"EA-006", "EMA-006", "EDA-001", "ETCA-002"}

    def test_missing_id_is_absent(self, tmp_path: Path) -> None:
        path = tmp_path / "sessions.md"
        _write(path, _SESSION_REGISTER_TEXT)
        assert "EMA-007" not in registered_session_ids(path)


class TestFindViolations:
    def test_flags_real_ema007_gap(self, tmp_path: Path) -> None:
        """The exact real-world gap EDA-002 found by hand: EMA-007's report
        exists with no matching SESSION_REGISTER.md row (the register text
        above reproduces the real pre-fix EMA table, ending at EMA-006)."""
        session_path = tmp_path / "sessions.md"
        _write(session_path, _SESSION_REGISTER_TEXT)
        reports = [
            AuditReport(
                filename="EXECUTIVE_MATH_AUDIT_REPORT_007.md",
                session_id="EMA-007",
            )
        ]
        violations = find_violations(reports, registered_session_ids(session_path))
        assert len(violations) == 1
        assert "EMA-007" in violations[0]

    def test_no_violation_once_registered(self, tmp_path: Path) -> None:
        session_path = tmp_path / "sessions.md"
        _write(
            session_path,
            _SESSION_REGISTER_TEXT.replace(
                "## Global sessions — Executive Documentation Audits",
                "| EMA-007 | 2026-09-17 | Executive Mathematical Audit "
                "Session 007 | `main` @ `233c93a` | COMPLETE |\n\n"
                "## Global sessions — Executive Documentation Audits",
            ),
        )
        reports = [
            AuditReport(
                filename="EXECUTIVE_MATH_AUDIT_REPORT_007.md",
                session_id="EMA-007",
            )
        ]
        violations = find_violations(reports, registered_session_ids(session_path))
        assert violations == []

    def test_no_violation_for_non_report_files(self, tmp_path: Path) -> None:
        session_path = tmp_path / "sessions.md"
        _write(session_path, _SESSION_REGISTER_TEXT)
        assert find_violations([], registered_session_ids(session_path)) == []


class TestLiveRepository:
    def test_current_repository_state_is_clean(self) -> None:
        """Every Executive Audit report actually committed to this
        repository must have its own SESSION_REGISTER.md row."""
        reports = find_reports(REPO_ROOT / "DOCS" / "audits")
        registered_ids = registered_session_ids(
            REPO_ROOT / "DOCS" / "sessions" / "SESSION_REGISTER.md"
        )
        assert find_violations(reports, registered_ids) == []
        assert len(reports) > 0


class TestMain:
    def test_main_exits_1_on_violation(self, tmp_path: Path) -> None:
        audits_dir = _make_reports_dir(tmp_path, ["EXECUTIVE_MATH_AUDIT_REPORT_007.md"])
        session_path = tmp_path / "sessions.md"
        _write(session_path, _SESSION_REGISTER_TEXT)

        assert main([str(audits_dir), str(session_path)]) == 1

    def test_main_exits_0_on_clean(self, tmp_path: Path) -> None:
        audits_dir = _make_reports_dir(tmp_path, ["EXECUTIVE_MATH_AUDIT_REPORT_006.md"])
        session_path = tmp_path / "sessions.md"
        _write(session_path, _SESSION_REGISTER_TEXT)

        assert main([str(audits_dir), str(session_path)]) == 0

    def test_main_exits_2_on_missing_directory(self, tmp_path: Path) -> None:
        assert main([str(tmp_path / "missing"), str(tmp_path / "also.md")]) == 2

    def test_main_defaults_to_repository_files(self) -> None:
        assert main([]) == 0
