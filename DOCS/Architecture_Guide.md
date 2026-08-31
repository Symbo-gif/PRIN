# PRIN Architecture Guide

## Overview

**PRIN** (Phase-Resonance Interference Network) is the from-scratch rebuild of
the **PRINet 3.0** research prototype. It processes information through coupled
oscillator dynamics, polyadic tensor decomposition, and phase synchronization,
exposed as a PyTorch-compatible Python API.

The defining architectural rule: **all numerics live in the compiled Rust
core** (`prin._prin_core`, built from the `crates/` workspace). The Python
package `prin` provides API ergonomics, PyTorch autograd bridges (via DLPack),
plotting, orchestration, and parity tooling — and contains no numerical
reimplementation. This split is enforced by `tools/check_no_python_numerics.py`
and the `tests/test_no_python_numerics.py` AST regression.

## Workspace layout

```
crates/
├── prin-dynamics/     # oscillator state, models, coupling, PAC, integrators, bands
├── prin-tensor/       # polyadic (CP / Tucker) tensor decomposition
├── prin-metrics/      # order parameter, coherence, spectral, chimera metrics
├── prin-sim/          # simulation orchestration, sweeps, OscilloSim
├── prin-kernels/      # fused discrete-step / mean-field / sparse-kNN kernels
├── prin-train/        # trainable stack: layers, attention, hybrid, bands,
│                      #   optimizers (SCALR / RIP / SyncGD), HEP, slot attention
├── prin-daemon/       # subconscious controller: ONNX inference, EP selection
└── prin-py/           # PyO3 bindings — thin marshalling only, zero numerics
python/prin/
├── dynamics.py, metrics.py, kernels.py, solvers.py, tensor.py, simulation.py
├── _torch_compat.py   # internal Torch-facing compatibility facade
├── nn/                # torch.nn.Module wrappers over the Rust-backed bridges
├── daemon.py, subconscious_compat.py, training_hooks.py, temporal_training.py
├── parity/            # golden-corpus loader, manifest, differential harness
└── reporting/, eval/, experiments/
```

## Data flow

1. A Python `torch.nn.Module` wrapper (e.g. `prin.nn.ResonanceLayer`,
   `DiscreteDeltaThetaGammaLayer`, `OscillatoryAttention`) marshals float32/64
   CPU tensors to the Rust bridge through `prin.nn._bridge.apply_rust_bridge`.
2. The bridge (`crates/prin-py/src/bindings/*.rs`) converts tensors via DLPack,
   calls the owning `prin-train` / `prin-dynamics` routine, and returns results
   plus a recompute closure for the backward pass.
3. `torch.autograd.Function` orchestration in Python stitches the forward and
   VJP calls into the autograd graph; gradients flow back into Rust-owned
   parameters, which are checkpointed as opaque bytes.

## Compatibility surface

Every symbol in the frozen PRINet 3.0 public API (`prinet.__all__`, 172 names)
resolves from `prin`. Symbols map to one of: a real Rust-backed implementation,
a thin Python composition over Rust-backed layers (documented in the Migration
Guide), or a typed `NotImplementedError` stub for components whose rebuild is
owned by a later work package. The authoritative per-symbol disposition table
is `DOCS/sphinx/migration_guide.rst`, machine-checked by
`tools/wp036_migration_table.py`.

## Determinism

All stochastic construction routes through the Rust `Seed` type
(counter/key halves). There is no hidden RNG in the Python layer. Parity
against `prinet==3.0.0` is verified on a versioned golden-trajectory corpus
under `parity/` with `rtol=1e-6`, `atol=1e-8` for trajectories.
