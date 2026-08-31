"""Import-only strict port for 0144M1 (WP-036C S1 sub-pass 1/8).

Copies the PRINet 3.0 reference test files ``test_integration_q3.py``,
``test_y2q1.py`` and ``test_y2q4.py`` under stable ``tests/test_acceptance_*``
names, adapting only import module paths from ``prinet.*`` to the corresponding
``prin`` owner. Assertions, expected values, parametrization, call order, and
semantics are unchanged (Testing Standards s1.1).
"""

from __future__ import annotations

import re
from pathlib import Path

ref_root = Path(
    r"C:\dev\PRIN\DOCS\archive and reference from PRINet 3.0\PRINet-3.0.0-main\tests"
)
out_root = Path(r"C:\dev\PRIN\tests")

# (reference filename, output filename, list of (pattern, replacement))
JOBS: list[tuple[str, str, list[tuple[str, str]]]] = [
    (
        "test_integration_q3.py",
        "test_acceptance_integration_q3.py",
        [
            (
                r"from prinet import \(\n"
                r"    DeltaThetaGammaNetwork,\n"
                r"    HierarchicalResonanceLayer,\n"
                r"    OscillatorState,\n"
                r"    PhaseAmplitudeCoupling,\n"
                r"    PhaseToRateConverter,\n"
                r"    SparsityRegularizationLoss,\n"
                r"    phase_to_rate,\n"
                r"\)\n",
                "from prin._torch_compat import (\n"
                "    DeltaThetaGammaNetwork,\n"
                "    OscillatorState,\n"
                "    PhaseAmplitudeCoupling,\n"
                "    phase_to_rate,\n"
                ")\n"
                "from prin.nn import (\n"
                "    HierarchicalResonanceLayer,\n"
                "    PhaseToRateConverter,\n"
                "    SparsityRegularizationLoss,\n"
                ")\n",
            ),
        ],
    ),
    (
        "test_y2q1.py",
        "test_acceptance_y2q1.py",
        [
            (
                r"from prinet\.core\.propagation import DiscreteDeltaThetaGamma\n",
                "from prin.nn import DiscreteDeltaThetaGamma\n",
            ),
            (
                r"from prinet\.core import DiscreteDeltaThetaGamma\n",
                "from prin.nn import DiscreteDeltaThetaGamma\n",
            ),
            (
                r"from prinet\.nn\.layers import ",
                "from prin.nn import ",
            ),
            (
                r"from prinet\.nn\.hybrid import ",
                "from prin.nn import ",
            ),
            (
                r"from prinet\.nn\.training_hooks import ",
                "from prin.training_hooks import ",
            ),
            (
                r"        from prinet\.nn import \(\n",
                "        from prin.nn import (\n",
            ),
            (
                r"        from prinet import \(\n",
                "        from prin import (\n",
            ),
        ],
    ),
    (
        "test_y2q4.py",
        "test_acceptance_y2q4.py",
        [
            (r"^import prinet\n", "import prin as prinet\n"),
            (
                r"from prinet\._deprecation import \(",
                "from prin._deprecation import (",
            ),
            (
                r"from prinet\.nn\.hybrid import HybridPRINetV2\n",
                "from prin.nn import HybridPRINetV2\n",
            ),
            (
                r"from prinet import KuramotoOscillator, OscillatorState, "
                r"kuramoto_order_parameter\n",
                "from prin._torch_compat import KuramotoOscillator, "
                "OscillatorState, kuramoto_order_parameter\n",
            ),
            (r"from prinet import _deprecation\n", "from prin import _deprecation\n"),
        ],
    ),
]

for ref_name, out_name, mappings in JOBS:
    text = (ref_root / ref_name).read_text(encoding="utf-8")
    for pat, repl in mappings:
        new_text, n = re.subn(pat, repl, text, flags=re.MULTILINE)
        if n == 0:
            raise SystemExit(f"{ref_name}: pattern not found: {pat!r}")
        text = new_text
    (out_root / out_name).write_text(text, encoding="utf-8")
    print(f"wrote {out_root / out_name}")
