"""Import-only strict port for 0144M7 (WP-036C S1 sub-pass 7/8).

Copies the PRINet 3.0 reference test files ``test_y4q1_7.py`` and
``test_y4q1_8.py`` under stable ``tests/test_acceptance_*`` names, adapting only
import module paths from ``prinet.*`` to the corresponding ``prin`` owner.
Assertions, expected values, parametrization, call order, and semantics are
unchanged (Testing Standards §1.1).
"""

from __future__ import annotations

from pathlib import Path

ref_root = Path(
    r"C:\dev\PRIN\DOCS\archive and reference from PRINet 3.0\PRINet-3.0.0-main\tests"
)
out_root = Path(r"C:\dev\PRIN\tests")

_REPLACEMENTS = (
    (
        "from prinet.nn.ablation_variants import",
        "from prin.nn.ablation_variants import",
    ),
    (
        "from prinet.nn.hybrid import PhaseTracker",
        "from prin.nn.temporal_compat import PhaseTracker",
    ),
    (
        "from prinet.nn.slot_attention import TemporalSlotAttentionMOT",
        "from prin.nn.temporal_compat import TemporalSlotAttentionMOT",
    ),
    (
        "from prinet.utils.temporal_metrics import",
        "from prin.temporal_metrics import",
    ),
    (
        "from prinet.utils.temporal_training import",
        "from prin.temporal_training import",
    ),
    (
        "from prinet.utils.adversarial_tools import",
        "from prin.adversarial_tools import",
    ),
    ("from prinet.utils.oscillosim import", "from prin.simulation import"),
    ("from prinet.utils.y4q1_tools import", "from prin.y4q1_tools import"),
    ("import prinet\n", "import prin as prinet\n"),
)

JOBS = (
    ("test_y4q1_7.py", "test_acceptance_y4q1_7.py"),
    ("test_y4q1_8.py", "test_acceptance_y4q1_8.py"),
)

for ref_name, out_name in JOBS:
    text = (ref_root / ref_name).read_text(encoding="utf-8")
    for old, new in _REPLACEMENTS:
        text = text.replace(old, new)
    leftover = [
        ln
        for ln in text.splitlines()
        if ln.strip().startswith(("from prinet", "import prinet"))
        and "import prin as prinet" not in ln
    ]
    if leftover:
        raise SystemExit(f"{ref_name}: unadapted prinet import(s): {leftover}")
    (out_root / out_name).write_text(text, encoding="utf-8")
    print(f"wrote {out_root / out_name}")
