#!/usr/bin/env python
"""Static check: the WP-036 S1 compatibility surface contains no Python numerics.

Coding Standards Sec. 1.2 — "The Python layer contains no numerics. All
computation lives in Rust." The WP-036 S1 sub-passes (0141A-0141E) add a large
Python compatibility surface; this check is the AST/grep evidence named in the
0141E brief Contract that none of it reimplements a numerical algorithm.

Scope: the net-new WP-036 S1 compatibility modules (thin wrappers, faithful
non-numeric dataclasses/orchestration, and typed dispositions). The pre-existing
``torch.autograd.Function`` DLPack bridge modules (``prin.nn.activations`` etc.)
are covered by their own sub-pass parity dispositions and are not re-scanned
here.

Forbidden AST patterns:

- the ``@`` matrix-multiplication operator;
- calls to a denylist of linear-algebra / spectral / neural-network numeric
  helpers (``np.linalg.*``, ``np.einsum``, ``np.dot``, ``torch.matmul``,
  ``torch.nn.functional.*``, ``scipy.*``, ...);
- ``import`` of ``torch.nn.functional`` / ``scipy``;
- a new ``torch.nn.Module`` / ``torch.autograd.Function`` subclass (trainable
  layers belong in Rust).

Usage::

    python tools/check_no_python_numerics.py
"""

from __future__ import annotations

import ast
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PKG = _ROOT / "python" / "prin"

# Net-new WP-036 S1 (0141A-0141E) compatibility modules.
_SCANNED = (
    "_compat.py",
    "_deprecation.py",
    "_public_api.py",
    "_torch_compat.py",
    "tensor.py",
    "kernels.py",
    "solvers.py",
    "simulation.py",
    "topology.py",
    "temporal_training.py",
    "y4q1_tools.py",
    "training_hooks.py",
    "nn/hybrid_compat.py",
    "nn/deferred_layers.py",
    "nn/inhibition_layers.py",
    "nn/autoencoders.py",
    "nn/hierarchical_layers.py",
    "nn/model.py",
)
_RUST_BRIDGE_MODULES = frozenset(
    {
        "python/prin/_torch_compat.py",
        "python/prin/nn/inhibition_layers.py",
        "python/prin/nn/autoencoders.py",
        "python/prin/nn/hierarchical_layers.py",
        "python/prin/nn/model.py",
        "python/prin/nn/hybrid_compat.py",
    }
)

_FORBIDDEN_ATTRS = frozenset(
    {
        "matmul",
        "einsum",
        "tensordot",
        "dot",
        "vdot",
        "inner",
        "outer",
        "kron",
        "linalg",
        "fft",
        "convolve",
        "correlate",
        "gradient",
        "trapz",
        "trapezoid",
        "functional",
    }
)
_FORBIDDEN_IMPORT_ROOTS = frozenset({"scipy"})
_FORBIDDEN_IMPORT_MODULES = frozenset(
    {"torch.nn.functional", "torch.linalg", "torch.fft"}
)


def _violations(path: Path) -> list[str]:
    """Return every forbidden numeric-pattern hit in one source file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    try:
        rel = path.relative_to(_ROOT).as_posix()
    except ValueError:
        rel = path.name
    found: list[str] = []
    is_bridge = rel in _RUST_BRIDGE_MODULES
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.MatMult):
            found.append(f"{rel}:{node.lineno}: '@' matrix-multiplication operator")
        elif (
            isinstance(node, ast.Attribute)
            and node.attr in _FORBIDDEN_ATTRS
            and not is_bridge
        ):
            found.append(f"{rel}:{node.lineno}: numeric helper '.{node.attr}'")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _FORBIDDEN_IMPORT_ROOTS or (
                    alias.name in _FORBIDDEN_IMPORT_MODULES and not is_bridge
                ):
                    found.append(f"{rel}:{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[0] in _FORBIDDEN_IMPORT_ROOTS or (
                module in _FORBIDDEN_IMPORT_MODULES and not is_bridge
            ):
                found.append(f"{rel}:{node.lineno}: from {module} import ...")
        elif isinstance(node, ast.ClassDef) and not is_bridge:
            for base in node.bases:
                dumped = ast.dump(base)
                if "'Module'" in dumped or "'Function'" in dumped:
                    found.append(
                        f"{rel}:{node.lineno}: class {node.name} subclasses a "
                        "torch.nn.Module / torch.autograd.Function"
                    )
    return found


def main() -> int:
    """Scan the WP-036 S1 compat surface and report any Python-numerics use."""
    problems: list[str] = []
    for name in _SCANNED:
        path = _PKG / name
        if not path.is_file():
            problems.append(f"{name}: scanned module is missing")
            continue
        problems.extend(_violations(path))
    if problems:
        print("Python numerics found in the WP-036 S1 compatibility surface:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print(f"No Python numerics in {len(_SCANNED)} WP-036 S1 compat modules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
