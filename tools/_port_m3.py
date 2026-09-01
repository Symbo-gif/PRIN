"""Import-only strict port for 0144M3 (WP-036C S1 sub-pass 3/8).

Copies the PRINet 3.0 reference test files ``test_y3q1.py`` and ``test_y3q2.py``
under stable ``tests/test_acceptance_*`` names, adapting only import module
paths from ``prinet.*`` to the corresponding ``prin`` owner. Assertions,
expected values, parametrization, call order, and semantics are unchanged
(Testing Standards s1.1).

The one structural adaptation is splitting a single
``from prinet.core.propagation import (...)`` statement into two
(``from prin._torch_compat import (...)`` + ``from prin.nn import (...)``)
because PRIN partitions that reference module's surface across two owners --
identical in kind to the ``test_integration_q3`` split in 0144M1.
"""

from __future__ import annotations

import re
from pathlib import Path

ref_root = Path(
    r"C:\dev\PRIN\DOCS\archive and reference from PRINet 3.0\PRINet-3.0.0-main\tests"
)
out_root = Path(r"C:\dev\PRIN\tests")

# propagation symbols owned by ``prin.nn`` rather than ``prin._torch_compat``
_NN_PROP = {
    "DiscreteDeltaThetaGamma",
    "FeedbackInhibition",
    "FeedforwardInhibition",
}

_Y3Q1_BIG_BLOCK_OLD = (
    "        from prinet.core.propagation import (  # noqa: F401\n"
    "            DeltaThetaGammaNetwork,\n"
    "            DentateGyrusConverter,\n"
    "            DiscreteDeltaThetaGamma,\n"
    "            ExponentialIntegrator,\n"
    "            FeedbackInhibition,\n"
    "            FeedforwardInhibition,\n"
    "            HopfOscillator,\n"
    "            KuramotoOscillator,\n"
    "            MultiRateIntegrator,\n"
    "            OscillatorModel,\n"
    "            OscillatorState,\n"
    "            OscillatorSyncError,\n"
    "            PhaseAmplitudeCoupling,\n"
    "            StuartLandauOscillator,\n"
    "            TemporalPhasePropagator,\n"
    "            ThetaGammaNetwork,\n"
    "            detect_oscillation,\n"
    "            phase_to_rate,\n"
    "            sweep_coupling_params,\n"
    "        )\n"
)
_Y3Q1_BIG_BLOCK_NEW = (
    "        from prin._torch_compat import (  # noqa: F401\n"
    "            DeltaThetaGammaNetwork,\n"
    "            DentateGyrusConverter,\n"
    "            ExponentialIntegrator,\n"
    "            HopfOscillator,\n"
    "            KuramotoOscillator,\n"
    "            MultiRateIntegrator,\n"
    "            OscillatorModel,\n"
    "            OscillatorState,\n"
    "            OscillatorSyncError,\n"
    "            PhaseAmplitudeCoupling,\n"
    "            StuartLandauOscillator,\n"
    "            TemporalPhasePropagator,\n"
    "            ThetaGammaNetwork,\n"
    "            detect_oscillation,\n"
    "            phase_to_rate,\n"
    "            sweep_coupling_params,\n"
    "        )\n"
    "        from prin.nn import (  # noqa: F401\n"
    "            DiscreteDeltaThetaGamma,\n"
    "            FeedbackInhibition,\n"
    "            FeedforwardInhibition,\n"
    "        )\n"
)


def _prop_single(match: re.Match[str]) -> str:
    """Route a single-line ``from prinet.core.propagation import X, Y`` line."""
    indent, names = match.group(1), match.group(2)
    parsed = [n.strip() for n in names.split(",") if n.strip()]
    tc = [n for n in parsed if n not in _NN_PROP]
    nn = [n for n in parsed if n in _NN_PROP]
    lines = []
    if tc:
        lines.append(f"{indent}from prin._torch_compat import {', '.join(tc)}")
    if nn:
        lines.append(f"{indent}from prin.nn import {', '.join(nn)}")
    return "\n".join(lines)


def port_y3q1(text: str) -> str:
    """Adapt ``test_y3q1.py`` imports."""
    assert _Y3Q1_BIG_BLOCK_OLD in text, "y3q1: 19-symbol propagation block not found"
    text = text.replace(_Y3Q1_BIG_BLOCK_OLD, _Y3Q1_BIG_BLOCK_NEW)
    text = re.sub(
        r"^(\s*)from prinet\.core\.propagation import ([^\n(]+)$",
        _prop_single,
        text,
        flags=re.MULTILINE,
    )
    text = text.replace(
        "from prinet.core.subconscious_daemon import SubconsciousDaemon",
        "from prin.subconscious_compat import SubconsciousDaemon",
    )
    text = text.replace(
        "from prinet.nn.layers import HierarchicalResonanceLayer",
        "from prin.nn import HierarchicalResonanceLayer",
    )
    text = text.replace(
        "from prinet.nn.hybrid import HybridPRINetV2",
        "from prin.nn import HybridPRINetV2",
    )
    text = text.replace(
        "from prinet.nn.hybrid import HybridPRINet\n",
        "from prin.nn import HybridPRINet\n",
    )
    text = text.replace(
        "from prinet.utils.datasets import (  # noqa: F401",
        "from prin.datasets import (  # noqa: F401",
    )
    text = text.replace(
        "from prinet.utils.profiler import (  # noqa: F401",
        "from prin.reporting import (  # noqa: F401",
    )
    text = text.replace(
        "from prinet.utils.profiler import ProfileReport",
        "from prin.reporting import ProfileReport",
    )
    text = text.replace(
        "from prinet.utils.profiler import PRINetProfiler",
        "from prin.reporting import PRINetProfiler",
    )
    return text


def port_y3q2(text: str) -> str:
    """Adapt ``test_y3q2.py`` imports."""
    text = text.replace(
        "from prinet.nn.adaptive_allocation import",
        "from prin.nn.allocation import",
    )
    text = text.replace(
        "from prinet.nn.mot_evaluation import",
        "from prin.nn.mot_evaluation import",
    )
    text = text.replace(
        "from prinet.nn.hybrid import PhaseTracker",
        "from prin.nn import PhaseTracker",
    )
    text = text.replace(
        "        from prinet.nn import (\n",
        "        from prin.nn import (\n",
    )
    return text


JOBS = [
    ("test_y3q1.py", "test_acceptance_y3q1.py", port_y3q1),
    ("test_y3q2.py", "test_acceptance_y3q2.py", port_y3q2),
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
