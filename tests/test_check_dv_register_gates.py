"""Tests for ``tools/check_dv_register_gates.py`` (Phase 5 analytics R34).

The headline case this tool exists for is the historical R28/DV-019 gap
Executive Audit 006 (finding E-F2) caught by hand: Phase 4's R28 required a
dedicated hotfix/correction session for DV-019 "before session 0109 (WP-028
S1) begins", but nothing mechanically checked it, and Phase 5 fully executed
and closed with the precondition unsatisfied. ``test_flags_historical_r28_dv019_gap``
reproduces that exact shape (real gate phrasing, real session number,
DV-019's real pre-fix "OPEN" status) and asserts the tool would have caught
it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from check_dv_register_gates import (
    DvRow,
    find_gate_sessions,
    find_violations,
    is_satisfied,
    main,
    parse_dv_register,
    parse_session_register,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

# The real DV-019 row's gate phrasing and pre-fix status, as they existed at
# commit 5fdfeb0 (immediately before `Hotfix-DV019`, commit 7376437, closed
# it) — independently reproduced via `git show 5fdfeb0:DOCS/reports/
# DEFERRED_VALIDATION_REGISTER.md`.
_DV019_PRE_FIX_CURRENT_STATUS = (
    "Originally: OPEN — non-blocking (re-running the test suite reliably "
    "passes); root-cause narrowed to bands.rs:801's w_gamma "
    "gradient-presence assertion and two candidate fixes identified, but "
    "not yet implemented. Phase 4 analytics R28 (2026-08-21): this item "
    "has recurred four times across Phase 4 with no concrete session "
    "assignment; a dedicated hotfix/correction session must run before "
    "session 0109 (WP-028 S1) begins, following the WP-025 S3-exec / "
    "Exec-WP-026 S1 ad hoc-session precedent."
)
_DV019_POST_FIX_CURRENT_STATUS = (
    "**CLOSED (2026-08-26, Hotfix-DV019)** — root cause corrected, not "
    "merely mitigated; see DOCS/experiments/hotfix-dv019-handoff.md."
)


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _dv_register_text(current_status: str) -> str:
    return (
        "# Deferred Validation Register\n\n"
        "## Active deferred items\n\n"
        "| ID | Summary | Origin | Governing amendment | Re-audit gate | "
        "Current status |\n"
        "|---|---|---|---|---|---|\n"
        "| DV-019 | `gradients_flow_to_every_parameter` is intermittently "
        "flaky. | WP-023 (session 0089) | `Hotfix-DV019`; no plan amendment | "
        "CLOSED — see Current status | " + current_status + " |\n"
        "| DV-099 | An unrelated item with no session gate. | WP-001 | None | "
        "Ongoing | OPEN — unrelated, no gate named |\n\n"
        "---\n\n"
        "## Closed items\n\n"
        "irrelevant trailing section\n"
    )


def _session_register_text(session_0109_status: str) -> str:
    return (
        "# PRIN Master Session Register\n\n"
        "| EA | Date | Session brief | Git state | Status |\n"
        "|---|---|---|---|---|\n"
        "| EA-006 | 2026-08-26 | Executive Audit Session 006 | `main` @ "
        "`5d90427` | COMPLETE |\n\n"
        "| Session | Phase | WP | Type | Title | Status |\n"
        "|---|---|---|---|---|---|\n"
        "| 0108 | 4 | WP-027 | S4 — Documentation | [Phase 4 close](x.md) | "
        "COMPLETE |\n"
        f"| 0109 | 5 | WP-028 | S1 — Coding | [ONNX controller and backend "
        f"selection](phase-5/0109-wp028-s1-onnx-controller-and-backend-"
        f"selection.md) | {session_0109_status} |\n"
    )


class TestParseDvRegister:
    def test_parses_rows_and_columns(self, tmp_path: Path) -> None:
        path = tmp_path / "dv.md"
        _write(path, _dv_register_text(_DV019_PRE_FIX_CURRENT_STATUS))
        rows = parse_dv_register(path)
        ids = [row.dv_id for row in rows]
        assert ids == ["DV-019", "DV-099"]
        dv019 = rows[0]
        assert "WP-023 (session 0089)" in dv019.prose
        assert "Hotfix-DV019" in dv019.prose
        assert "session 0109" in dv019.current_status

    def test_handles_missing_middle_column(self, tmp_path: Path) -> None:
        """Real, live rows (DV-010 through DV-014) are missing the Re-audit
        gate column entirely (7 cells instead of 8). Current status must
        still resolve correctly - it is extracted from the right, not the
        left."""
        path = tmp_path / "dv.md"
        _write(
            path,
            "## Active deferred items\n\n"
            "| ID | Summary | Origin | Governing amendment | Re-audit gate | "
            "Current status |\n"
            "|---|---|---|---|---|---|\n"
            "| DV-010 | Tag push pending. | WP-011 | Maintainer approval | "
            "OPEN — tag push still pending |\n\n"
            "---\n",
        )
        rows = parse_dv_register(path)
        assert len(rows) == 1
        assert rows[0].dv_id == "DV-010"
        assert rows[0].current_status == "OPEN — tag push still pending"

    def test_handles_extra_embedded_pipe(self, tmp_path: Path) -> None:
        """Real, live DV-020 has an inline-code ``|`` (a shell alternation,
        `grep -rl "A\\|B"`) inside its Summary column, producing 9 cells
        instead of 8. Current status must still resolve from the right."""
        path = tmp_path / "dv.md"
        _write(
            path,
            "## Active deferred items\n\n"
            "| ID | Summary | Origin | Governing amendment | Re-audit gate | "
            "Current status |\n"
            "|---|---|---|---|---|---|\n"
            '| DV-020 | `grep -rl "A\\|B"` finds nothing. | WP-024 S1 | '
            "amendment #29 | S2 audit confirmed | **CLOSED** (2026-08-19) |\n\n"
            "---\n",
        )
        rows = parse_dv_register(path)
        assert len(rows) == 1
        assert rows[0].dv_id == "DV-020"
        assert rows[0].current_status == "**CLOSED** (2026-08-19)"

    def test_missing_section_header_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "dv.md"
        _write(path, "# No active items section here\n")
        with pytest.raises(ValueError, match="Active deferred items"):
            parse_dv_register(path)

    def test_skips_too_short_and_header_rows(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = tmp_path / "dv.md"
        _write(
            path,
            "## Active deferred items\n\n"
            "| ID | Summary | Origin | Governing amendment | Re-audit gate | "
            "Current status |\n"
            "|---|---|---|---|---|---|\n"
            "| too short |\n"
            "\n---\n",
        )
        assert parse_dv_register(path) == []
        assert "malformed DV register row" in capsys.readouterr().err

    def test_skips_blank_lines_and_empty_id_cell(self, tmp_path: Path) -> None:
        path = tmp_path / "dv.md"
        _write(
            path,
            "## Active deferred items\n\n"
            "| ID | Summary | Origin | Governing amendment | Re-audit gate | "
            "Current status |\n"
            "|---|---|---|---|---|---|\n"
            "\n"
            "|  | no id here | o | g | r | OPEN |\n"
            "| DV-030 | real row | o | g | r | OPEN |\n"
            "\n---\n",
        )
        ids = [row.dv_id for row in parse_dv_register(path)]
        assert ids == ["DV-030"]


class TestParseSessionRegister:
    def test_parses_numbered_sessions_only(self, tmp_path: Path) -> None:
        path = tmp_path / "sessions.md"
        _write(path, _session_register_text("COMPLETE"))
        statuses = parse_session_register(path)
        assert statuses["0109"] == "COMPLETE"
        assert statuses["0108"] == "COMPLETE"
        # The EA-006 global-session row's ID is not a 4-digit number and
        # must not be picked up as a numbered session.
        assert "EA-006" not in statuses

    def test_planned_status_parsed(self, tmp_path: Path) -> None:
        path = tmp_path / "sessions.md"
        _write(path, _session_register_text("PLANNED"))
        assert parse_session_register(path)["0109"] == "PLANNED"


class TestGateDetection:
    def test_finds_gate_session_from_current_status(self) -> None:
        row = DvRow(
            dv_id="DV-019",
            prose="flaky test, WP-023",
            current_status=_DV019_PRE_FIX_CURRENT_STATUS,
        )
        assert find_gate_sessions(row) == ["0109"]
        assert not is_satisfied(row)

    def test_no_gate_phrase_returns_empty(self) -> None:
        row = DvRow(
            dv_id="DV-099",
            prose="unrelated, WP-001, ongoing",
            current_status="OPEN — unrelated, no gate named",
        )
        assert find_gate_sessions(row) == []

    def test_closed_status_is_satisfied(self) -> None:
        row = DvRow(
            dv_id="DV-019",
            prose="flaky test, WP-023, Hotfix-DV019",
            current_status=_DV019_POST_FIX_CURRENT_STATUS,
        )
        assert is_satisfied(row)

    def test_satisfied_keyword_also_recognized(self) -> None:
        row = DvRow(
            dv_id="DV-XYZ",
            prose="s, o, g, r",
            current_status="Hard gate — SATISFIED (2026-08-26, Hotfix-DV019)",
        )
        assert is_satisfied(row)


class TestFindViolations:
    def test_flags_historical_r28_dv019_gap(self, tmp_path: Path) -> None:
        """The exact real-world gap EA-006 caught by hand: session 0109 is
        COMPLETE while DV-019's own gate ("before session 0109") is
        unsatisfied. This is R34's required historical-case confirmation
        evidence."""
        dv_path = tmp_path / "dv.md"
        _write(dv_path, _dv_register_text(_DV019_PRE_FIX_CURRENT_STATUS))
        session_path = tmp_path / "sessions.md"
        _write(session_path, _session_register_text("COMPLETE"))

        violations = find_violations(
            parse_dv_register(dv_path), parse_session_register(session_path)
        )
        assert len(violations) == 1
        assert "DV-019" in violations[0]
        assert "0109" in violations[0]

    def test_no_violation_once_closed(self, tmp_path: Path) -> None:
        """Same gate, same reached session — but DV-019 is now CLOSED, the
        actual post-`Hotfix-DV019` state, so no violation should fire."""
        dv_path = tmp_path / "dv.md"
        _write(dv_path, _dv_register_text(_DV019_POST_FIX_CURRENT_STATUS))
        session_path = tmp_path / "sessions.md"
        _write(session_path, _session_register_text("COMPLETE"))

        violations = find_violations(
            parse_dv_register(dv_path), parse_session_register(session_path)
        )
        assert violations == []

    def test_no_violation_when_gate_not_yet_reached(self, tmp_path: Path) -> None:
        """DV-019 still open, but the gate session hasn't run yet — not a
        violation, since the precondition hasn't actually been reached."""
        dv_path = tmp_path / "dv.md"
        _write(dv_path, _dv_register_text(_DV019_PRE_FIX_CURRENT_STATUS))
        session_path = tmp_path / "sessions.md"
        _write(session_path, _session_register_text("PLANNED"))

        violations = find_violations(
            parse_dv_register(dv_path), parse_session_register(session_path)
        )
        assert violations == []


class TestLiveRepository:
    def test_current_repository_state_is_clean(self) -> None:
        """The live register, as committed, must have zero reached,
        unsatisfied gates — DV-019's real gate was closed by
        `Hotfix-DV019` before this test's own commit."""
        dv_rows = parse_dv_register(
            REPO_ROOT / "DOCS" / "reports" / "DEFERRED_VALIDATION_REGISTER.md"
        )
        session_status = parse_session_register(
            REPO_ROOT / "DOCS" / "sessions" / "SESSION_REGISTER.md"
        )
        assert find_violations(dv_rows, session_status) == []
        assert len(dv_rows) > 0
        assert len(session_status) > 0


class TestMain:
    def test_main_exits_1_on_violation(self, tmp_path: Path) -> None:
        dv_path = tmp_path / "dv.md"
        _write(dv_path, _dv_register_text(_DV019_PRE_FIX_CURRENT_STATUS))
        session_path = tmp_path / "sessions.md"
        _write(session_path, _session_register_text("COMPLETE"))

        assert main([str(dv_path), str(session_path)]) == 1

    def test_main_exits_0_on_clean(self, tmp_path: Path) -> None:
        dv_path = tmp_path / "dv.md"
        _write(dv_path, _dv_register_text(_DV019_POST_FIX_CURRENT_STATUS))
        session_path = tmp_path / "sessions.md"
        _write(session_path, _session_register_text("COMPLETE"))

        assert main([str(dv_path), str(session_path)]) == 0

    def test_main_exits_2_on_missing_file(self, tmp_path: Path) -> None:
        assert main([str(tmp_path / "missing.md")]) == 2

    def test_main_defaults_to_repository_files(self) -> None:
        assert main([]) == 0
