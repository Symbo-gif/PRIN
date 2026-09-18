# PRIN Rust workspace crates

| Crate | Responsibility | Phase |
|---|---|---|
| `prin-dynamics` | Oscillator state, models (Kuramoto/Stuart–Landau/Hopf), integrators, PAC, coupling topologies, continuous band networks, temporal propagation | 1–2 |
| `prin-metrics` | Order parameters, coherence, PSD, chimera metrics, sparse variants | 1 |
| `prin-tensor` | Tucker/HOSVD and CP/PARAFAC decomposition | 2 |
| `prin-kernels` | Single-source fused GPU/CPU kernels (CubeCL) + CPU SIMD fallback. Mean-field RK4, sparse k-NN, PAC modulation, discrete-time step, and PRINet 3.0 compatibility functions. See [crate README](prin-kernels/README.md) for details. | 0+3+6 |
| `prin-sim` | OscilloSim engine: CSR sparse, 1M+ oscillators, pruning, sweeps, CPU/GPU dispatch, and PRINet 3.0 compatibility functions. See [crate README](prin-sim/README.md) for details. | 2+3+6 |
| `prin-train` | Burn-based trainable layers, optimizers, attention, tracking architectures, ablations, and compatibility layers (13 D-D-appendix symbols as real Burn implementations). See [crate README](prin-train/README.md) for details. | 4+6 |
| `prin-daemon` | Subconscious ONNX controller, daemon thread, training hooks, and MOT accumulator (CLEAR-MOT/IDF1). See [crate README](prin-daemon/README.md) for details. | 5 |
| `prin-py` | PyO3 extension crate — the sole Python link point. DLPack bridges for all trainable layers, tensor decomposition, kernels, and compatibility surfaces. See [crate README](prin-py/README.md) for the full breakdown. | 0+4+6 |

Dependency rule: crates may depend only on crates above them in the layering
`dynamics → metrics/tensor/kernels → sim/train/daemon → py`. `prin-py` is the
sole Python link point. See `DOCS/PRIN_Project_Plan.md` §5.
