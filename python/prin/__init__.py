"""PRIN -- Phase-Resonance Interference Network.

Public Python API for PRIN, the from-scratch rebuild of PRINet 3.0. The
numerical core lives in the compiled Rust extension ``prin._prin_core``; this
package holds API ergonomics, PyTorch bridges, plotting, and orchestration
only (no numerics -- see the Target Architecture design rules in
``DOCS/PRIN_Project_Plan.md``).

Subpackages:
    prin.dlpack: zero-copy DLPack tensor exchange between PyTorch and the
        PRIN Rust core.
    prin.nn: torch.nn.Module wrappers, autograd.Function bridges, baselines.
    prin.eval: MOT evaluation and temporal metrics.
    prin.experiments: ablation, stats, adversarial, and training frameworks.
    prin.parity: golden-trajectory corpus, manifest/loader, and differential
        harness for numerical parity against PRINet 3.0.
    prin.reporting: benchmark JSON reports, figures, tables, profiler.
"""

from __future__ import annotations

__version__ = "0.1.0-alpha.1"

try:
    from prin._prin_core import core_version
except ImportError as _exc:  # pragma: no cover - build-environment guard
    raise ImportError(
        "The compiled PRIN core extension (prin._prin_core) is not available. "
        "Build it with: maturin develop -m crates/prin-py/Cargo.toml"
    ) from _exc

__all__ = [
    "__version__",
    "core_version",
]
