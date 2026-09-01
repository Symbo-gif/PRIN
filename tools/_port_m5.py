"""Import-only strict port for 0144M5 (WP-036C S1 sub-pass 5/8).

Copies the PRINet 3.0 reference test files ``test_y4q1.py``, ``test_y4q1_2.py``,
and ``test_y4q1_3.py`` under stable ``tests/test_acceptance_*`` names, adapting
only import module paths from ``prinet.*`` to the corresponding ``prin`` owner.
Assertions, expected values, parametrization, call order, and semantics are
unchanged (Testing Standards s1.1).
"""

from __future__ import annotations

from pathlib import Path

ref_root = Path(
    r"C:\dev\PRIN\DOCS\archive and reference from PRINet 3.0\PRINet-3.0.0-main\tests"
)
out_root = Path(r"C:\dev\PRIN\tests")

_REPLACEMENTS = (
    ("from prinet.nn.slot_attention import", "from prin.nn.slot_attention import"),
    ("from prinet.utils.oscillosim import", "from prin.simulation import"),
    ("from prinet.utils.y4q1_tools import", "from prin.y4q1_tools import"),
)

JOBS = (
    ("test_y4q1.py", "test_acceptance_y4q1.py"),
    ("test_y4q1_2.py", "test_acceptance_y4q1_2.py"),
    ("test_y4q1_3.py", "test_acceptance_y4q1_3.py"),
)

for ref_name, out_name in JOBS:
    text = (ref_root / ref_name).read_text(encoding="utf-8")
    for old, new in _REPLACEMENTS:
        text = text.replace(old, new)
    leftover = [
        ln
        for ln in text.splitlines()
        if ln.strip().startswith(("from prinet", "import prinet"))
    ]
    if leftover:
        raise SystemExit(f"{ref_name}: unadapted prinet import(s): {leftover}")
    (out_root / out_name).write_text(text, encoding="utf-8")
    print(f"wrote {out_root / out_name}")
