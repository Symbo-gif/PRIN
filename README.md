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

Phase 0 pre-alpha foundation. WP-001 established a deterministic repository
inventory, complete PRINet 3.0 API-to-work-package traceability, metadata
validation, and measured quality/security baselines. WP-002 delivered the
versioned golden-trajectory corpus (504 cases) and differential parity harness.
WP-003 prototyped the PyO3/DLPack zero-copy Torch↔Rust bridge with batched
boundary calls, ownership/lifetime handling, dtype/device validation, and
microbenchmark instrumentation. WP-004 prototyped the first single-source
CubeCL fused mean-field RK4 kernel in `crates/prin-kernels` (`step_cpu`,
`try_step_wgpu`/`try_step_cpu`/`try_step_cuda`), with a CPU reference, wgpu
kernel-equivalence validation at N=1M, and a typed `MeanFieldRk4Error`
fallback. See the latest
[Project State Report](DOCS/reports/README.md) for the authoritative active
session and trajectory.

## Installation (development)

The released PyPI distribution is **`prin-core`**; the import name is **`prin`**
(`pip install prin-core` → `import prin`). Project Plan amendment #46 moved the
distribution name because PyPI's `prin` belongs to an unrelated project last
released in 2015.

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
├── tests/                # pytest acceptance and repository-control tests
├── tools/                # baseline/traceability tooling; guarded reproduction
├── models/               # subconscious_controller.onnx
├── notebooks/            # tutorial notebooks
├── paper/                # NeurIPS paper artefacts
├── DOCS/                 # plan, standards, baselines, audits, reports, Sphinx
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
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Contribution workflow |
| [`AGENTS.md`](AGENTS.md) | Agent/IDE notes and local verification commands (kept in sync with CI) |

## License

MIT — see [LICENSE](LICENSE).
