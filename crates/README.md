# PRIN Rust workspace crates

| Crate | Responsibility | Phase |
|---|---|---|
| `prin-dynamics` | Oscillator state, models (Kuramoto/Stuart–Landau/Hopf), integrators, PAC, coupling topologies, continuous band networks, temporal propagation | 1–2 |
| `prin-metrics` | Order parameters, coherence, PSD, chimera metrics, sparse variants | 1 |
| `prin-tensor` | Tucker/HOSVD and CP/PARAFAC decomposition | 2 |
| `prin-kernels` | Single-source fused GPU/CPU kernels (CubeCL) + CPU SIMD fallback. Phase 0 mean-field RK4 spike is active (`cpu`/`wgpu`/`cuda` features). WP-017 delivered the backend abstraction, preallocated buffer pools (`MeanFieldRk4Buffers`, `CubeclBufferPool`), cross-backend equivalence harness, and automatic `step_auto` dispatch with graceful CPU fallback | 0+3 |
| `prin-sim` | OscilloSim engine: CSR sparse, 1M+ oscillators, pruning, sweeps | 2 |
| `prin-train` | Burn-based trainable layers, inhibition/STE, activations, HEP, optimizers | 4 |
| `prin-daemon` | Subconscious ONNX controller, backend detection, ring buffer | 5 |
| `prin-py` | PyO3 extension crate (the only crate that links Python) | 0+ |

Dependency rule: crates may depend only on crates above them in the layering
`dynamics → metrics/tensor/kernels → sim/train/daemon → py`. `prin-py` is the
sole Python link point. See `DOCS/PRIN_Project_Plan.md` §5.
