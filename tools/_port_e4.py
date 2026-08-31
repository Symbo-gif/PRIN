"""Import-only strict port for 0144E4 (q3_new + nn + scalr_enhanced).

Copies each PRINet 3.0 reference test under a stable ``tests/`` name, adapting
only import module paths from ``prinet.*`` to the corresponding ``prin`` owner.
Assertions, expected values, parametrization, call order, and semantics are
unchanged (Testing Standards s1.1).
"""

import re
from pathlib import Path

ref_root = Path(
    r"C:\dev\PRIN\DOCS\archive and reference from PRINet 3.0\PRINet-3.0.0-main\tests"
)
out_root = Path(r"C:\dev\PRIN\tests")

mappings = [
    (
        r"^from prinet\.core\.propagation import \(\n",
        "from prin._torch_compat import (\n",
    ),
    (
        r"^from prinet\.core\.measurement import kuramoto_order_parameter\n",
        "from prin._torch_compat import kuramoto_order_parameter\n",
    ),
    (r"^from prinet\.nn\.layers import \(\n", "from prin.nn import (\n"),
    (
        r"^from prinet\.nn\.layers import "
        r"DenseAutoencoder, DGLayer, PhaseToRateAutoencoder\n",
        "from prin.nn import DenseAutoencoder, DGLayer, PhaseToRateAutoencoder\n",
    ),
    (r"^from prinet\.nn\.optimizers import \(\n", "from prin import (\n"),
    (
        r"^from prinet\.nn\.optimizers import SCALROptimizer\n",
        "from prin import SCALROptimizer\n",
    ),
    (
        r"^from prinet\.utils\.benchmark_reporting import \(\n",
        "from prin.reporting import (\n",
    ),
    (
        r"^from prinet\.utils\.triton_kernels import \(\n",
        "from prin.kernels import (\n",
    ),
]

targets = {
    "test_q3_new.py": "test_acceptance_q3_new.py",
    "test_nn.py": "test_acceptance_nn.py",
    "test_scalr_enhanced.py": "test_acceptance_scalr_enhanced.py",
}

for name, out_name in targets.items():
    text = (ref_root / name).read_text(encoding="utf-8")
    for pat, repl in mappings:
        text = re.sub(pat, repl, text, flags=re.MULTILINE)
    (out_root / out_name).write_text(text, encoding="utf-8")
    print(f"wrote {out_root / out_name}")
