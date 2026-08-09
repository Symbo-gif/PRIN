# prin-py

PyO3 extension crate for PRIN — the only crate that links Python. Built with
maturin into the `prin._prin_core` extension module inside the `prin` wheel.

WP-001 upgraded the compatible PyO3/rust-numpy pair to 0.29.0 and set the
workspace MSRV to Rust 1.83. WP-003 added the DLPack bridge
(`src/dlpack.rs`), which exposes `dlpack_negate`, `dlpack_negate_batched`, and
`dlpack_round_trip` for zero-copy Torch↔Rust tensor exchange. The `dlpack`
module is the audited Python-FFI boundary (Project Plan amendment #6 / Coding
Standards §2.1): it is the only module in this crate permitted to use `unsafe`,
under `#![deny(unsafe_op_in_unsafe_fn)]` with a `// SAFETY:` comment on every
`unsafe` block. Rust-backed forward/backward autograd bridges and the full
trainable stack land in Phase 4 (WP-022…WP-027).

WP-011 (Phase 1 Python API and dynamics integration) added PyO3 bindings for
the complete Phase 1 dynamics and metrics surface:

- **`bindings/state.rs`** — `PyOscillatorState`, `PyStateDerivatives`, `PySeed`,
  and numeric constants (`TAU`, `AMPLITUDE_MIN`, `AMPLITUDE_MAX`, `DERIV_CLAMP`,
  `SPARSE_EPS`).
- **`bindings/models.rs`** — `PyKuramotoOscillator`, `PyStuartLandauOscillator`,
  `PyHopfOscillator`.
- **`bindings/integrators.rs`** — `PyEulerIntegrator`, `PyRK4Integrator`,
  `PyRK45Integrator`, `PyAdaptiveResult`.
- **`bindings/coupling.rs`** — `PyCouplingMode`, `PyTopology`,
  `PyPhaseAmplitudeCoupling`.
- **`bindings/metrics.rs`** — 22 `#[pyfunction]`s covering the full
  `prin-metrics` surface (order, coherence, spectral, energy, chimera,
  metastability, k-NN).

All bindings are pure delegation — no Python numerics; numerical authority
remains in `prin-dynamics` and `prin-metrics`. The Python re-export modules
`python/prin/dynamics.py` (20 symbols) and `python/prin/metrics.py` (22 symbols)
provide ergonomic access. Type stubs at `python/prin/_prin_core.pyi` cover all
new symbols. 69 Python acceptance tests in `tests/test_dynamics_bindings.py`
exercise all binding paths.

Type stubs are maintained at `python/prin/_prin_core.pyi` and regenerated
whenever the extension API changes.

Build for development:

```bash
maturin develop -m crates/prin-py/Cargo.toml
```
