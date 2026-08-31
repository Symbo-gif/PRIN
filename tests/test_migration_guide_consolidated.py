"""Machine-check for the consolidated WP-036 S1 Migration Guide symbol table.

0141 brief Contract: "The Migration Guide table (all 172 rows) ... is
machine-checked against ``DOCS/baselines/wp001_api_traceability.md`` by a
committed test - no silent removals."
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import prin
import pytest

prinet = pytest.importorskip("prinet")

_ROOT = Path(__file__).resolve().parents[1]
_TOOL = _ROOT / "tools" / "wp036_migration_table.py"
_GUIDE = _ROOT / "DOCS" / "sphinx" / "migration_guide.rst"

_spec = importlib.util.spec_from_file_location("_wp036_migration_table", _TOOL)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def _table_rows() -> list[tuple[str, str, str, str]]:
    text = _GUIDE.read_text(encoding="utf-8")
    block = text[text.find(_mod._TABLE_BEGIN) : text.find(_mod._TABLE_END)]
    rows: list[tuple[str, str, str, str]] = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith('"'):
            continue
        cells = re.findall(r'"([^"]*)"', stripped)
        if len(cells) == 4:
            rows.append((cells[0], cells[1], cells[2], cells[3]))
    return rows


def test_tool_check_passes() -> None:
    """The generator's own check (table vs surface vs WP-001 baseline) is green."""
    assert _mod.check() == 0


def test_cli_render_and_check(capsys: pytest.CaptureFixture[str]) -> None:
    """Both CLI subcommands run and ``render`` emits a guarded 172-row block."""
    assert _mod.main(["render"]) == 0
    rendered = capsys.readouterr().out
    assert _mod._TABLE_BEGIN in rendered and _mod._TABLE_END in rendered
    assert rendered.count('", "prin.') == 172
    assert _mod.main(["check"]) == 0


def test_check_flags_a_stale_or_mangled_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A dropped row is reported as a stale table and a symbol mismatch."""
    good = _GUIDE.read_text(encoding="utf-8")
    begin = good.find(_mod._TABLE_BEGIN)
    mangled = good[:begin] + good[begin:].replace(
        '   "OscilloSim", "prin.OscilloSim"', "   XX", 1
    )
    fake = tmp_path / "migration_guide.rst"
    fake.write_text(mangled, encoding="utf-8")
    monkeypatch.setattr(_mod, "_MIGRATION_GUIDE", fake)
    assert _mod.check() == 1
    err = capsys.readouterr().err
    assert "stale" in err
    assert "OscilloSim" in err


def test_committed_table_requires_guard_markers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A guide with no guard markers is a hard error, not a silent pass."""
    fake = tmp_path / "no_markers.rst"
    fake.write_text("nothing here\n", encoding="utf-8")
    monkeypatch.setattr(_mod, "_MIGRATION_GUIDE", fake)
    with pytest.raises(SystemExit):
        _mod._committed_table()


def test_table_has_exactly_the_172_legacy_symbols() -> None:
    """One row per ``prinet.__all__`` name; nothing missing, nothing extra."""
    rows = _table_rows()
    assert len(rows) == 172
    symbols = {row[0] for row in rows}
    assert symbols == set(prinet.__all__)


def test_every_table_symbol_resolves_from_prin() -> None:
    """Each row's symbol resolves from the ``prin`` package root."""
    for symbol, resolves, _class, _subpass in _table_rows():
        assert hasattr(prin, symbol), symbol
        assert resolves == f"prin.{symbol}"


def test_no_silent_removals_against_wp001_baseline() -> None:
    """Every legacy symbol keeps a ``prinet`` ownership row in the baseline."""
    baseline = _ROOT / "DOCS" / "baselines" / "wp001_api_traceability.md"
    row = r"^\|\s*prinet\s*\|\s*([A-Za-z_][A-Za-z0-9_]*)\s*\|"
    baseline_symbols = set(re.findall(row, baseline.read_text(encoding="utf-8"), re.M))
    assert set(prinet.__all__) <= baseline_symbols


def test_disposition_class_matches_runtime_behaviour() -> None:
    """A stub row raises a typed error; a real row does not raise NotImplemented."""
    for symbol, _resolves, disposition, _subpass in _table_rows():
        obj = getattr(prin, symbol)
        is_stub_row = "stub" in disposition
        try:
            obj()
        except NotImplementedError:
            raised_disposition = True
        except Exception as exc:
            raised_disposition = type(exc).__name__ == "BackendUnavailableError"
        else:
            raised_disposition = False
        if is_stub_row:
            assert raised_disposition, f"{symbol}: table says stub but did not raise"
        else:
            assert not raised_disposition, f"{symbol}: table says real but raised"
