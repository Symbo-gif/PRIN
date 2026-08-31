#!/usr/bin/env python
"""Generate and verify the consolidated WP-036 S1 Migration Guide symbol table.

WP-036 S1 (session 0141, amendment #32) makes every one of the 172
``prinet.__all__`` symbols resolve from ``prin``. This tool renders the single
consolidated 172-row disposition table for ``DOCS/sphinx/migration_guide.rst``
and, in ``check`` mode, verifies it against three independent sources so that
no symbol is silently dropped or misclassified:

1. ``prinet.__all__`` — the frozen legacy contract (exactly 172 names).
2. ``prin`` — every row's symbol must resolve from the package root.
3. ``DOCS/baselines/wp001_api_traceability.md`` — the static WP-001 baseline
   must carry a ``| prinet | <symbol> | ...`` ownership row for every symbol
   (the "no silent removals" guarantee named in the 0141 brief Contract).

The per-symbol *disposition class* is derived at runtime (a construct/callable
probe) plus the sub-pass bucket recorded in ``python/prin/_public_api.py``, so
the table cannot drift from the delivered surface without this check failing.

Usage::

    python tools/wp036_migration_table.py render   # emit the csv-table body
    python tools/wp036_migration_table.py check    # verify the committed table
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PUBLIC_API = _ROOT / "python" / "prin" / "_public_api.py"
_MIGRATION_GUIDE = _ROOT / "DOCS" / "sphinx" / "migration_guide.rst"
_TRACEABILITY = _ROOT / "DOCS" / "baselines" / "wp001_api_traceability.md"

_TABLE_BEGIN = ".. wp036-consolidated-table-begin"
_TABLE_END = ".. wp036-consolidated-table-end"

# Exception type names that mean "real callable, needs a valid input/environment"
# — not a documented WP-036 disposition. A no-argument probe legitimately hits
# these for constructors with required parameters and for report/figure
# functions that need a benchmark artefact tree.
_INPUT_ERRORS = frozenset(
    {"TypeError", "ValueError", "ArtifactNotFoundError", "FileNotFoundError"}
)
_DISPOSITION_ERRORS = frozenset({"NotImplementedError", "BackendUnavailableError"})

_SUBPASS_MARKER = re.compile(r"#\s*WP-036 S1 sub-pass (0141[A-E]\d?)")
_STRING_LITERAL = re.compile(r'"([A-Za-z_][A-Za-z0-9_]*)"')
_TRACE_ROW = re.compile(r"^\|\s*prinet\s*\|\s*([A-Za-z_][A-Za-z0-9_]*)\s*\|")


def _subpass_buckets() -> dict[str, str]:
    """Map each RC1 public name to the sub-pass whose block introduced it."""
    buckets: dict[str, str] = {}
    current = "0141A"
    in_tuple = False
    for line in _PUBLIC_API.read_text(encoding="utf-8").splitlines():
        if "RC1_PUBLIC_API" in line and "(" in line:
            in_tuple = True
            continue
        if not in_tuple:
            continue
        if line.strip() == ")":
            break
        marker = _SUBPASS_MARKER.search(line)
        if marker is not None:
            current = marker.group(1)
            continue
        name = _STRING_LITERAL.search(line.strip())
        if name is not None and not line.strip().startswith("#"):
            buckets.setdefault(name.group(1), current)
    return buckets


def _probe_disposition(name: str, obj: object) -> str:
    """Classify a resolved symbol by a no-argument construct/callable probe."""
    if not (inspect.isclass(obj) or callable(obj)):
        return "real (module constant)"
    try:
        obj()  # type: ignore[operator]
    except Exception as exc:
        kind = type(exc).__name__
        if kind in _DISPOSITION_ERRORS:
            return "disposition"
        if kind in _INPUT_ERRORS:
            return "real"
        raise
    return "real"


_GPU_STUBS = frozenset(
    {
        "triton_fused_mean_field_rk4_step",
        "triton_sparse_knn_coupling",
        "triton_pac_modulation",
        "triton_hierarchical_order_param",
        "triton_fused_discrete_step",
        "fused_discrete_step_cuda",
    }
)
_WP036A_SUBPASSES = {
    "DGLayer": "0144A1",
    "DentateGyrusConverter": "0144A1",
    "FeedforwardInhibition": "0144A1",
    "SparsityRegularizationLoss": "0144A1",
    "oscillatory_weight_init": "0144A1",
    "PhaseToRateConverter": "0144A2",
    "PhaseToRateAutoencoder": "0144A2",
    "DenseAutoencoder": "0144A2",
    "HierarchicalResonanceLayer": "0144A3",
    "PhaseAmplitudeCouplingLayer": "0144A3",
    "DiscreteDeltaThetaGammaLayer": "0144A3",
    "PRINetModel": "0144A4",
    "compile_model": "0144A4",
}
_RENAME_ALIASES = frozenset(
    {
        "SCALROptimizer",
        "RIPOptimizer",
        "SynchronizedGradientDescent",
        "TemporalPhasePropagator",
        "temporal_recovery_speed",
        "OscillatorModel",
        "ThetaGammaNetwork",
        "DeltaThetaGammaNetwork",
    }
)


def _disposition_class(name: str, subpass: str, probe: str) -> str:
    """Human-readable disposition class for the consolidated table."""
    if name in _GPU_STUBS:
        return "GPU-only stub (typed BackendUnavailableError)"
    if name == "compile_model":
        return "real - pure-Python torch.compile passthrough (WP-036A)"
    if probe == "disposition":
        return "D-2.2 deferred stub (typed NotImplementedError)"
    if name in _RENAME_ALIASES:
        return "real - rename alias"
    if subpass == "0141A":
        return "real - direct re-export"
    if subpass in ("0141B", "0141C"):
        return f"real - Rust PyO3 binding ({subpass})"
    if subpass.startswith("0144A"):
        return "real - Rust PyO3 binding (WP-036A)"
    if subpass in ("0141D1", "0141D2"):
        return f"real - non-numeric orchestration ({subpass})"
    return f"real ({subpass})"


def _rows() -> list[tuple[str, str, str, str]]:
    """Build one ``(symbol, resolution, disposition, sub-pass)`` row per legacy name."""
    prin = importlib.import_module("prin")
    prinet = importlib.import_module("prinet")
    buckets = _subpass_buckets()
    rows: list[tuple[str, str, str, str]] = []
    for name in sorted(prinet.__all__):
        if not hasattr(prin, name):
            raise SystemExit(f"prinet symbol does not resolve from prin: {name}")
        obj = getattr(prin, name)
        subpass = _WP036A_SUBPASSES.get(name, buckets.get(name, "0141A"))
        probe = _probe_disposition(name, obj)
        rows.append(
            (
                name,
                f"prin.{name}",
                _disposition_class(name, subpass, probe),
                subpass,
            )
        )
    return rows


def render() -> str:
    """Render the reStructuredText csv-table body (between the guard markers)."""
    lines = [
        _TABLE_BEGIN,
        "",
        ".. csv-table:: WP-036 S1 consolidated 172-symbol disposition index",
        '   :header: "PRINet 3.0 symbol", "Resolves from", "Disposition", "Sub-pass"',
        "   :widths: 30, 24, 34, 12",
        "",
    ]
    for name, resolves, disposition, subpass in _rows():
        lines.append(f'   "{name}", "{resolves}", "{disposition}", "{subpass}"')
    lines.extend(["", _TABLE_END])
    return "\n".join(lines)


def _committed_table() -> str:
    text = _MIGRATION_GUIDE.read_text(encoding="utf-8")
    start = text.find(_TABLE_BEGIN)
    end = text.find(_TABLE_END)
    if start == -1 or end == -1:
        raise SystemExit(
            "consolidated-table guard markers missing from migration_guide.rst"
        )
    return text[start : end + len(_TABLE_END)].replace("\r\n", "\n").strip()


def check() -> int:
    """Verify the committed table against the surface and the WP-001 baseline."""
    errors: list[str] = []
    prinet = importlib.import_module("prinet")
    legacy = frozenset(prinet.__all__)
    if len(legacy) != 172:
        errors.append(f"prinet.__all__ has {len(legacy)} names, expected 172")

    expected = render().strip()
    committed = _committed_table()
    if committed != expected:
        errors.append(
            "migration_guide.rst consolidated table is stale; "
            "run `python tools/wp036_migration_table.py render`"
        )

    table_symbols = {
        m.group(1)
        for line in committed.splitlines()
        if (m := re.match(r'\s+"([A-Za-z_][A-Za-z0-9_]*)",', line))
    }
    if table_symbols != legacy:
        missing = sorted(legacy - table_symbols)
        extra = sorted(table_symbols - legacy)
        errors.append(f"table/prinet.__all__ mismatch: missing={missing} extra={extra}")

    trace_symbols = {
        m.group(1)
        for line in _TRACEABILITY.read_text(encoding="utf-8").splitlines()
        if (m := _TRACE_ROW.match(line))
    }
    dropped = sorted(legacy - trace_symbols)
    if dropped:
        errors.append(
            "symbols missing a WP-001 traceability row (silent removal): "
            + ", ".join(dropped)
        )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"WP-036 consolidated migration table OK ({len(legacy)} symbols).")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Render or verify the consolidated WP-036 migration table."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("render", "check"))
    arguments = parser.parse_args(argv)
    if arguments.command == "render":
        print(render())
        return 0
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
