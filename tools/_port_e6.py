"""Import-only strict port for 0144E6 (subconscious + consolidation).

Copies the PRINet 3.0 ``test_subconscious.py`` reference test under a stable
``tests/`` name, adapting only import module paths from ``prinet.*`` to the
corresponding ``prin`` owner. Assertions, expected values, parametrization,
call order, and semantics are unchanged (Testing Standards s1.1).

Every reference symbol the file imports -- the ``core.subconscious`` data
types, the ``core.subconscious_daemon`` lifecycle helpers, the
``nn.subconscious_model`` PyTorch controller, and the ``utils.npu_backend``
execution-provider probes -- is re-exported from the single PRIN acceptance
owner ``prin.subconscious_compat`` (WP-036-execution-plan row: owner
``prin.daemon``; the compat module is the sibling shim over the Rust-backed
``prin.daemon`` / ``prin._prin_core`` owners, the same pattern as
``prin.nn.hybrid_compat`` / ``prin.nn.optimizers`` in 0144E4/0144E5).
"""

import re
from pathlib import Path

ref_root = Path(
    r"C:\dev\PRIN\DOCS\archive and reference from PRINet 3.0\PRINet-3.0.0-main\tests"
)
out_root = Path(r"C:\dev\PRIN\tests")

mappings = [
    (
        r"^from prinet\.core\.subconscious import \(\n",
        "from prin.subconscious_compat import (\n",
    ),
    (
        r"^from prinet\.core\.subconscious_daemon import \(\n",
        "from prin.subconscious_compat import (\n",
    ),
    (
        r"^from prinet\.nn\.subconscious_model import SubconsciousController\n",
        "from prin.subconscious_compat import SubconsciousController\n",
    ),
    (
        r"^from prinet\.utils\.npu_backend import \(\n",
        "from prin.subconscious_compat import (\n",
    ),
]

targets = {
    "test_subconscious.py": "test_acceptance_subconscious.py",
}

for name, out_name in targets.items():
    text = (ref_root / name).read_text(encoding="utf-8")
    for pat, repl in mappings:
        text = re.sub(pat, repl, text, flags=re.MULTILINE)
    (out_root / out_name).write_text(text, encoding="utf-8")
    print(f"wrote {out_root / out_name}")
