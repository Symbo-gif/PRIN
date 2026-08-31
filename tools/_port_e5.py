"""Import-only strict port for 0144E5 (hybrid + clevr_n).

Copies each PRINet 3.0 reference test under a stable ``tests/`` name,
adapting only import module paths from ``prinet.*`` to the corresponding
``prin`` owner. Assertions, expected values, parametrization, call order,
and semantics are unchanged (Testing Standards s1.1).
"""

import re
from pathlib import Path

ref_root = Path(
    r"C:\dev\PRIN\DOCS\archive and reference from PRINet 3.0\PRINet-3.0.0-main\tests"
)
out_root = Path(r"C:\dev\PRIN\tests")

hybrid_mappings = [
    (
        r"^from prinet\.nn\.hybrid import \(\n",
        "from prin.nn import (\n",
    ),
    (
        r"^from prinet\.nn\.training_hooks import StateCollector\n",
        "from prin.training_hooks import StateCollector\n",
    ),
    (
        r"^    from prinet\.nn\.layers import PRINetModel\n",
        "    from prin.nn import PRINetModel\n",
    ),
]

clevr_n_mappings: list[tuple[str, str]] = []

targets = {
    "test_hybrid.py": ("test_acceptance_hybrid.py", hybrid_mappings),
    "test_clevr_n.py": ("test_acceptance_clevr_n.py", clevr_n_mappings),
}

for name, (out_name, mappings) in targets.items():
    text = (ref_root / name).read_text(encoding="utf-8")
    for pat, repl in mappings:
        text = re.sub(pat, repl, text, flags=re.MULTILINE)
    (out_root / out_name).write_text(text, encoding="utf-8")
    print(f"wrote {out_root / out_name}")
