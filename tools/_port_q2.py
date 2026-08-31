import re
from pathlib import Path

ref_root = Path(
    r"C:\dev\PRIN\DOCS\archive and reference from PRINet 3.0\PRINet-3.0.0-main\tests"
)
out_root = Path(r"C:\dev\PRIN\tests")

mappings = [
    (
        r"^from prinet\.core\.measurement import kuramoto_order_parameter\n",
        "from prin._torch_compat import kuramoto_order_parameter\n",
    ),
    (
        r"^from prinet\.core\.propagation import \(\n",
        "from prin._torch_compat import (\n",
    ),
    (
        r"^from prinet\.nn\.hep import HolomorphicEnergy, HolomorphicEPTrainer\n",
        "from prin.nn import HolomorphicEnergy, HolomorphicEPTrainer\n",
    ),
    (r"^from prinet\.nn\.layers import \(\n", "from prin.nn import (\n"),
    (
        r"^from prinet\.nn\.optimizers import SCALROptimizer\n",
        "from prin import SCALROptimizer\n",
    ),
    (r"^from prinet\.nn\.activations import \(\n", "from prin.nn import (\n"),
    (r"^from prinet\.utils\.cuda_kernels import \(\n", "from prin.solvers import (\n"),
    (r"^from prinet import\n", "from prin import\n"),
    (r"import prinet\n", "import prin\n"),
    (
        r"from prinet\.utils\.cuda_kernels import SolverError",
        "from prin.solvers import SolverError",
    ),
]

for name in ["test_q2.py", "test_q2_remaining.py"]:
    src = ref_root / name
    text = src.read_text(encoding="utf-8")
    for pat, repl in mappings:
        text = re.sub(pat, repl, text, flags=re.MULTILINE)
    out_name = name.replace("test_q2.py", "test_acceptance_q2.py").replace(
        "test_q2_remaining.py", "test_acceptance_q2_remaining.py"
    )
    (out_root / out_name).write_text(text, encoding="utf-8")
    print(f"wrote {out_root / out_name}")
