"""Import-only strict port for 0144M4 (WP-036C S1 sub-pass 4/8).

Copies the PRINet 3.0 reference test files ``test_y3q3.py``, ``test_y3q4.py``,
``test_y3q45.py``, and ``test_y3q49.py`` under stable ``tests/test_acceptance_*``
names, adapting only import module paths from ``prinet.*`` to the corresponding
``prin`` owner.  Assertions, expected values, parametrization, call order, and
semantics are unchanged (Testing Standards s1.1).
"""

from __future__ import annotations

import re
from pathlib import Path

ref_root = Path(
    r"C:\dev\PRIN\DOCS\archive and reference from PRINet 3.0\PRINet-3.0.0-main\tests"
)
out_root = Path(r"C:\dev\PRIN\tests")


def _common(text: str) -> str:
    """Apply import adaptations shared across all four files."""
    text = text.replace(
        "from prinet.nn.hybrid import HybridPRINetV2",
        "from prin.nn.hybrid import HybridPRINetV2",
    )
    text = text.replace(
        "from prinet.nn.hybrid import HybridPRINetV2CLEVRN",
        "from prin.nn.hybrid import HybridPRINetV2CLEVRN",
    )
    text = text.replace(
        "from prinet.core.propagation import DiscreteDeltaThetaGamma",
        "from prin.nn import DiscreteDeltaThetaGamma",
    )
    return text


def _fused_kernels(text: str) -> str:
    """Remap ``from prinet.utils.fused_kernels import X`` to the PRIN owner."""
    _OWNER: dict[str, str] = {
        "pytorch_fused_discrete_step_full": "prin.kernels",
        "cuda_fused_kernel_available": "prin.kernels",
        "MixedPrecisionTrainer": "prin.training_hooks",
        "AsyncCPUGPUPipeline": "prin.training_hooks",
        "sparse_coupling_matrix_csr": "prin.kernels",
        "csr_coupling_step": "prin.kernels",
        "build_knn_neighbors": "prin.kernels",
        "sparse_knn_coupling_step": "prin.kernels",
        "LargeScaleOscillatorSystem": "prin.simulation",
        "OscillatorPruner": "prin.simulation",
        "_find_msvc_cl": "prin.kernels",
        "_ensure_msvc_on_path": "prin.kernels",
    }

    def _repl(match: re.Match[str]) -> str:
        indent = match.group(1)
        names_raw = match.group(2)
        parsed = [n.strip() for n in names_raw.split(",") if n.strip()]
        groups: dict[str, list[str]] = {}
        for name in parsed:
            owner = _OWNER.get(name, "prin.kernels")
            groups.setdefault(owner, []).append(name)
        parts = []
        for owner in sorted(groups):
            syms = groups[owner]
            if len(syms) == 1:
                parts.append(f"{indent}from {owner} import {syms[0]}")
            else:
                parts.append(f"{indent}from {owner} import ({', '.join(syms)})")
        return "\n".join(parts)

    text = re.sub(
        r"^(\s*)from prinet\.utils\.fused_kernels import ([^\n(]+)$",
        _repl,
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"^(\s*)from prinet\.utils\.fused_kernels import \(\n((?:[^\n]*\n)*?)\s*\)",
        lambda m: _repl_multiline(m, _OWNER),
        text,
        flags=re.MULTILINE,
    )
    return text


def _repl_multiline(match: re.Match[str], owner_map: dict[str, str]) -> str:
    """Remap a multi-line ``from prinet.utils.fused_kernels import ( ... )`` block."""
    indent = match.group(1)
    block = match.group(2)
    parsed = [n.strip() for n in block.splitlines() if n.strip().rstrip(",")]
    parsed = [n.rstrip(",") for n in parsed]
    groups: dict[str, list[str]] = {}
    for name in parsed:
        owner = owner_map.get(name, "prin.kernels")
        groups.setdefault(owner, []).append(name)
    parts = []
    for owner in sorted(groups):
        syms = groups[owner]
        if len(syms) == 1:
            parts.append(f"{indent}from {owner} import {syms[0]}")
        else:
            inner = ", ".join(syms)
            parts.append(f"{indent}from {owner} import ({inner})")
    return "\n".join(parts)


def port_y3q3(text: str) -> str:
    """Adapt ``test_y3q3.py`` imports."""
    text = _common(text)
    text = _fused_kernels(text)
    return text


def port_y3q4(text: str) -> str:
    """Adapt ``test_y3q4.py`` imports."""
    text = text.replace("import prinet", "import prin")
    text = text.replace("prinet.__version__", "prin.__version__")
    text = text.replace(
        "from prinet import SlotAttentionCLEVRN, SlotAttentionModule",
        "from prin import SlotAttentionCLEVRN, SlotAttentionModule",
    )
    text = text.replace(
        "from prinet import OscilloSim, SimulationResult, quick_simulate",
        "from prin import OscilloSim, SimulationResult, quick_simulate",
    )
    text = text.replace(
        "from prinet.nn import SlotAttentionCLEVRN, SlotAttentionModule",
        "from prin.nn import SlotAttentionCLEVRN, SlotAttentionModule",
    )
    text = text.replace(
        "from prinet.utils import OscilloSim, SimulationResult, quick_simulate",
        "from prin import OscilloSim, SimulationResult, quick_simulate",
    )
    text = text.replace(
        "from prinet.utils.oscillosim import OscilloSim",
        "from prin.simulation import OscilloSim",
    )
    text = text.replace(
        "from prinet.utils.oscillosim import OscilloSim, SimulationResult",
        "from prin.simulation import OscilloSim, SimulationResult",
    )
    text = text.replace(
        "from prinet.utils.oscillosim import SimulationResult, quick_simulate",
        "from prin.simulation import SimulationResult, quick_simulate",
    )
    text = text.replace(
        "from prinet.utils.oscillosim import quick_simulate",
        "from prin.simulation import quick_simulate",
    )
    text = text.replace(
        "from prinet.nn.slot_attention import SlotAttentionModule",
        "from prin.nn.slot_attention import SlotAttentionModule",
    )
    text = text.replace(
        "from prinet.nn.slot_attention import SlotAttentionCLEVRN",
        "from prin.nn.slot_attention import SlotAttentionCLEVRN",
    )
    text = _common(text)
    text = _fused_kernels(text)
    return text


def port_y3q45(text: str) -> str:
    """Adapt ``test_y3q45.py`` imports."""
    text = _common(text)
    text = _fused_kernels(text)
    text = text.replace(
        "from prinet.utils.oscillosim import OscilloSim",
        "from prin.simulation import OscilloSim",
    )
    text = text.replace(
        "from prinet.core.subconscious import SubconsciousState",
        "from prin.subconscious_compat import SubconsciousState",
    )
    text = text.replace("import prinet", "import prin")
    text = text.replace("prinet.__version__", "prin.__version__")
    return text


def port_y3q49(text: str) -> str:
    """Adapt ``test_y3q49.py`` imports."""
    text = text.replace(
        "from prinet.core.measurement import kuramoto_order_parameter",
        "from prin.metrics import kuramoto_order_parameter",
    )
    text = text.replace(
        "from prinet.core.propagation import KuramotoOscillator, OscillatorState",
        "from prin._torch_compat import KuramotoOscillator, OscillatorState",
    )
    text = text.replace(
        "from prinet.utils.oscillosim import OscilloSim",
        "from prin.simulation import OscilloSim",
    )
    text = _common(text)
    text = _fused_kernels(text)
    return text


JOBS = [
    ("test_y3q3.py", "test_acceptance_y3q3.py", port_y3q3),
    ("test_y3q4.py", "test_acceptance_y3q4.py", port_y3q4),
    ("test_y3q45.py", "test_acceptance_y3q45.py", port_y3q45),
    ("test_y3q49.py", "test_acceptance_y3q49.py", port_y3q49),
]

for ref_name, out_name, fn in JOBS:
    src = (ref_root / ref_name).read_text(encoding="utf-8")
    out = fn(src)
    leftover = [
        ln
        for ln in out.splitlines()
        if ln.strip().startswith(("from prinet", "import prinet"))
    ]
    if leftover:
        raise SystemExit(f"{ref_name}: unadapted prinet import(s): {leftover}")
    (out_root / out_name).write_text(out, encoding="utf-8")
    print(f"wrote {out_root / out_name}")
