# PRIN Rust workspace crates

| Crate | Responsibility | Phase |
|---|---|---|
| `prin-dynamics` | Oscillator state, models (Kuramoto/Stuart–Landau/Hopf), integrators, PAC, coupling topologies, continuous band networks, temporal propagation | 1–2 |
| `prin-metrics` | Order parameters, coherence, PSD, chimera metrics, sparse variants | 1 |
| `prin-tensor` | Tucker/HOSVD and CP/PARAFAC decomposition | 2 |
| `prin-kernels` | Single-source fused GPU/CPU kernels (CubeCL) + CPU SIMD fallback. Phase 0 mean-field RK4 spike is active (`cpu`/`wgpu`/`cuda` features). WP-017 delivered the backend abstraction, preallocated buffer pools (`MeanFieldRk4Buffers`, `CubeclBufferPool`), cross-backend equivalence harness, and automatic `step_auto` dispatch with graceful CPU fallback. WP-018 added the hierarchical device-side order-parameter reduction (`order_param_block_reduce`/`order_param_device`) and real device-event timing (`TimingMethod`, `StepReport::timing_method`). WP-019 added sparse k-NN coupling (`SparseKnnGraph`, `sparse_knn_derivatives_cpu`, `sparse_knn_coupling_cubecl`) and PAC modulation (`PacParams`, `pac_modulate_cpu`, `pac_modulate_cubecl`) kernels with CSR/index interoperability. WP-020 added the fused three-band discrete-time step (`discrete_step_cpu`, `discrete_step_cubecl`) with reusable hierarchical order-parameter/mean-phase reductions (10-launch fused path). WP-021 delivered dispatch-priority fixes, hardware CUDA kernel-equivalence validation across all four kernel families, and Phase 3 exit gate closure | 0+3 |
| `prin-sim` | OscilloSim engine: CSR sparse, 1M+ oscillators, pruning, sweeps, CPU dispatch, and GPU kernel integration (`GpuSparseKuramoto`, `GpuMeanFieldEngine`, `GpuBandStepper`) | 2+3 |
| `prin-train` | Burn-based trainable layers, inhibition/STE, activations, HEP, optimizers | 4 |
| `prin-daemon` | Subconscious ONNX controller, backend detection, ring buffer | 5 |
| `prin-py` | PyO3 extension crate (the only crate that links Python) | 0+ |

Dependency rule: crates may depend only on crates above them in the layering
`dynamics → metrics/tensor/kernels → sim/train/daemon → py`. `prin-py` is the
sole Python link point. See `DOCS/PRIN_Project_Plan.md` §5.
