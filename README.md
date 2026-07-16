# PRIN — Phase-Resonance Interference Network

**PRIN** is the from-scratch rebuild of [PRINet 3.0](https://github.com/Symbo-gif/PRINet-3.0.0):
a scientific ML framework built on coupled-oscillator dynamics (Kuramoto, Stuart–Landau,
Hopf), hierarchical δ/θ/γ band networks with phase–amplitude coupling (PAC), polyadic
tensor decomposition, and PyTorch-compatible trainable layers for temporal object
binding and multi-object tracking (MOT).

PRIN is a **two-layer system**:

- **Rust core** (`crates/`) — all oscillator dynamics, integrators, coupling topologies,
  sparse ops, phase metrics, tensor decomposition, simulation engine, and GPU kernels
  (single-source CubeCL kernels compiling to CUDA / Metal / Vulkan / CPU SIMD).
- **Thin Python package** (`python/prin/`) — the public API (PRINet-3.0-compatible
  symbols), `torch.autograd.Function` bridges with zero-copy DLPack tensor exchange,
  matplotlib figure generation, benchmark drivers, and the reproducibility pipeline.

## Status

Pre-alpha scaffold. See [`DOCS/PRIN_Project_Plan.md`](DOCS/PRIN_Project_Plan.md) for the
official project plan and phased roadmap.

## Installation (development)

```bash
# Requires Rust (stable) and Python >= 3.11
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install maturin
maturin develop -m crates/prin-py/Cargo.toml
pip install -e ".[dev]"
```

## Repository layout

```
PRIN/
├── Cargo.toml            # Rust workspace
├── crates/               # prin-dynamics, prin-metrics, prin-tensor, prin-kernels,
│                         # prin-sim, prin-train, prin-daemon, prin-py (PyO3)
├── python/prin/          # pure-Python layer (public API, torch bridges, reporting)
├── parity/               # golden-trajectory corpus + differential tests vs PRINet 3.0
├── benchmarks/           # 9 category packages + benchrunner CLI
├── tests/                # pytest acceptance suite (ported from PRINet 3.0)
├── tools/reproduce.py    # reproducibility pipeline (figures + tables)
├── models/               # subconscious_controller.onnx
├── notebooks/            # tutorial notebooks
├── paper/                # NeurIPS paper artefacts
├── DOCS/                 # official plan, standards, Sphinx site (DOCS/sphinx/)
└── .github/workflows/    # rust, python, parity, gpu, repro, release CI
```

## Governance documents

| Document | Purpose |
|---|---|
| [`DOCS/PRIN_Project_Plan.md`](DOCS/PRIN_Project_Plan.md) | Official project plan, roadmap, and Session Cycle methodology |
| [`DOCS/standards/Development_Workflow_and_Audit_Standards.md`](DOCS/standards/Development_Workflow_and_Audit_Standards.md) | The self-auditing Session Cycle (code → audit → remediate → document) |
| [`DOCS/sessions/README.md`](DOCS/sessions/README.md) | Complete 198-session execution plan from WP-001 through stable `1.0.0` |
| [`DOCS/sessions/SESSION_REGISTER.md`](DOCS/sessions/SESSION_REGISTER.md) | Exact global session order, status, and links to every brief |
| [`DOCS/standards/Coding_Standards.md`](DOCS/standards/Coding_Standards.md) | Rust + Python coding and security standards |
| [`DOCS/standards/Testing_Standards.md`](DOCS/standards/Testing_Standards.md) | Testing and numerical-parity standards |
| [`DOCS/standards/Documentation_Standards.md`](DOCS/standards/Documentation_Standards.md) | Documentation standards |
| [`DOCS/standards/Benchmarking_and_Reproducibility_Standards.md`](DOCS/standards/Benchmarking_and_Reproducibility_Standards.md) | Benchmarking and reproducibility standards |
| [`DOCS/standards/Experimentation_Standards.md`](DOCS/standards/Experimentation_Standards.md) | Pre-registered scientific experimentation standards |
| [`DOCS/standards/Versioning_and_Release_Standards.md`](DOCS/standards/Versioning_and_Release_Standards.md) | Versioning, CI/CD, and release standards |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Contribution workflow |

## License

MIT — see [LICENSE](LICENSE).
