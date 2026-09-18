# PRIN — Phase-Resonance Interference Network

**PRIN** is a scientific ML framework for temporal object binding and
multi-object tracking, built on coupled-oscillator dynamics. It provides
PyTorch-compatible trainable layers that use phase synchronization, hierarchical
frequency bands, and phase–amplitude coupling to bind and track objects over
time — capabilities that standard attention-based architectures struggle with
for long temporal sequences.

PRIN is the from-scratch rebuild of [PRINet 3.0](https://github.com/Symbo-gif/PRINet-3.0.0),
reimplementing all numerics in Rust for performance and reproducibility while
preserving the original API surface.

## Who is this for?

| If you are… | Start here |
|---|---|
| **A user** wanting to try PRIN | [Quick Start](#quick-start) → [Tutorial Notebooks](notebooks/) |
| **A contributor** wanting to help | [CONTRIBUTING.md](CONTRIBUTING.md) → [Development Standards](DOCS/standards/Development_Workflow_and_Audit_Standards.md) |
| **A researcher** evaluating the science | [Architecture](#architecture) → [Sphinx Documentation](https://prin.readthedocs.io/) → [Paper](paper/) |
| **A reviewer** checking governance | [Governance Documents](#governance-documents) → [Latest Project State Report](DOCS/reports/README.md) |

## Architecture

PRIN is a **two-layer system**: a Rust core for numerics, a thin Python layer
for API ergonomics and PyTorch integration.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Python Layer (python/prin/)                  │
│  Public API · torch.autograd.Function bridges · DLPack exchange │
│  Matplotlib figures · Benchmark drivers · Reporting pipeline    │
├─────────────────────────────────────────────────────────────────┤
│                     PyO3 / DLPack Bridge                         │
│              Zero-copy tensor exchange (no data copy)            │
├─────────────────────────────────────────────────────────────────┤
│                      Rust Core (crates/)                         │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │prin-dynamics │ │ prin-kernels │ │  prin-train  │             │
│  │ Oscillators  │ │ GPU/CPU fused│ │ Burn trainable│             │
│  │ Integrators  │ │ CubeCL kernels│ │ layers, optim│             │
│  │ Coupling     │ │              │ │              │             │
│  └─────────────┘ └──────────────┘ └──────────────┘             │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ prin-metrics │ │ prin-tensor  │ │  prin-sim    │             │
│  │ Sync, coherence│ │ Tucker/CP   │ │ OscilloSim   │             │
│  │ PSD, chimera │ │ decomposition│ │ 1M+ oscillators│            │
│  └─────────────┘ └──────────────┘ └──────────────┘             │
│  ┌─────────────────────────────────────────────────┐            │
│  │ prin-daemon (ONNX controller) · prin-py (PyO3)  │            │
│  └─────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

GPU kernels use [CubeCL](https://github.com/tracel-ai/cubecl) — a single source
compiling to CUDA, Metal, Vulkan, and CPU SIMD.

## Quick Start

Try PRIN in under 5 minutes:

```bash
# 1. Install (requires Rust stable + Python >= 3.11)
python -m venv .venv
.venv\Scripts\activate          # Windows (source .venv/bin/activate on Linux/macOS)
pip install maturin
maturin develop -m crates/prin-py/Cargo.toml
pip install -e ".[dev]"

# 2. Run the first tutorial notebook
jupyter notebook notebooks/01_oscillosim_quickstart.ipynb

# 3. Or run a quick simulation from Python
python -c "
import prin
state = prin.OscillatorState.new(100)
params = prin.KuramotoParams(frequency=1.0, coupling=2.0)
result = prin.quick_simulate(state, params, dt=0.01, steps=1000)
print(f'Order parameter R = {result.order_parameter:.4f}')
"
```

The [four tutorial notebooks](notebooks/) walk through oscillator dynamics,
hierarchical binding, custom coupling, and PyTorch training — all runnable on
CPU with measured runtime budgets (~4 min total).

## Installation (development)

The released PyPI distribution is **`prin-core`**; the import name is **`prin`**
(`pip install prin-core` → `import prin`).

```bash
# Requires Rust (stable) and Python >= 3.11
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install maturin
maturin develop -m crates/prin-py/Cargo.toml
pip install -e ".[dev]"
```

## Project Status

PRIN is at **release candidate** stage (v1.0.0-rc1). Six roadmap phases are
complete; Phase 7 (campaign execution and pre-release) is next.

| Phase | Status | Highlights |
|---|---|---|
| **Phase 0** — Foundation | ✅ Complete | Deterministic inventory, golden corpus (504 cases), PyO3/DLPack bridge, CubeCL kernel spike |
| **Phase 1** — Dynamics | ✅ Complete | Oscillator models, integrators, coupling topologies, PAC, band networks |
| **Phase 2** — Tensor & Metrics | ✅ Complete | Tucker/CP decomposition, synchronization/coherence/chimera metrics |
| **Phase 3** — GPU Kernels | ✅ Complete | Single-source CubeCL kernels (CUDA/Metal/Vulkan/CPU), 1M+ oscillator simulation |
| **Phase 4** — Training | ✅ Complete | Burn trainable layers, oscillator-aware optimizers, attention, tracking architectures |
| **Phase 5** — Evaluation | ✅ Complete | MOT evaluation, ablation framework, adversarial robustness, daemon controller |
| **Phase 6** — Integration | ✅ Complete | Compatibility layers, DirectML execution, GPU dispatch, documentation close |
| **Phase 7** — Campaign | 🔜 Next | Pre-registered confirmatory experiments, paper revision, stable 1.0.0 release |

**Quality gates:** 3,496 Python tests passed, 1,577 Rust tests passed, security
scans clean, Sphinx builds warning-free. See the latest
[Project State Report](DOCS/reports/README.md) for the authoritative trajectory.

## Key Concepts

| Term | Meaning |
|---|---|
| **Coupled oscillators** | Mathematical units that synchronize their rhythms — the foundation of PRIN's temporal binding |
| **Phase–amplitude coupling (PAC)** | Cross-frequency interaction where the phase of a slow rhythm modulates the amplitude of a fast one (e.g. θ/γ in working memory) |
| **Order parameter R** | A scalar (0–1) measuring how synchronized a population of oscillators is — R≈0 means desynchronized, R≈1 means phase-locked |
| **Chimera state** | A pattern where synchronized and desynchronized oscillators coexist in the same network |
| **δ/θ/γ bands** | Frequency bands from neuroscience: delta (1–4 Hz), theta (4–8 Hz), gamma (30–100 Hz) — PRIN models their hierarchical interaction |
| **Kuramoto model** | The canonical model of oscillator synchronization — PRIN extends it with amplitude dynamics and sparse coupling |
| **DLPack** | A zero-copy tensor exchange format — PRIN uses it to pass data between Rust and PyTorch without copying |

For deeper explanations, see the [Architecture Guide](https://prin.readthedocs.io/en/latest/architecture.html)
and [Capacity Analysis](https://prin.readthedocs.io/en/latest/capacity_analysis.html).

## Repository layout

```
PRIN/
├── Cargo.toml            # Rust workspace
├── crates/               # prin-dynamics, prin-metrics, prin-tensor, prin-kernels,
│                         # prin-sim, prin-train, prin-daemon, prin-py (PyO3)
├── python/prin/          # pure-Python layer (public API, torch bridges, reporting)
├── parity/               # golden-trajectory corpus + differential tests vs PRINet 3.0
├── benchmarks/           # 9 category packages + benchrunner CLI
├── tests/                # pytest acceptance and repository-control tests
├── tools/                # baseline/traceability tooling; guarded reproduction;
│                         # code-intelligence/ (optional local codebase
│                         # visualization + MCP subsystem, see DOCS/devtools/)
├── models/               # subconscious_controller.onnx
├── notebooks/            # tutorial notebooks
├── paper/                # NeurIPS paper artefacts
├── DOCS/                 # plan, standards, baselines, audits, reports, Sphinx,
│                         # devtools/ (code-intelligence subsystem docs)
└── .github/workflows/    # quality, security, parity, repro, GPU, release CI
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
| [`DOCS/standards/Executive_Readability_Audit_Governance_and_Methodology.md`](DOCS/standards/Executive_Readability_Audit_Governance_and_Methodology.md) | Human readability audit governance (ERA sessions) |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Contribution workflow |
| [`AGENTS.md`](AGENTS.md) | Agent/IDE notes and local verification commands (kept in sync with CI) |
| [`DOCS/devtools/visualization-mcp.md`](DOCS/devtools/visualization-mcp.md) | Local codebase visualization + runtime-observability MCP subsystem (`tools/code-intelligence/`) — an isolated developer-tooling add-on, not part of the Session Cycle |

## License

MIT — see [LICENSE](LICENSE).
