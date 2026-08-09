//! # prin-py
//!
//! PyO3 binding crate for PRIN — the **only** crate that links against
//! Python. Exposes the Rust core (`prin-dynamics`, `prin-metrics`,
//! `prin-tensor`, `prin-kernels`, `prin-sim`, `prin-train`, `prin-daemon`)
//! as the `prin._prin_core` extension module.
//!
//! Tensor exchange with PyTorch is zero-copy via DLPack; trainable components
//! are surfaced Python-side as `torch.autograd.Function`s whose forward and
//! backward call into Rust (see `python/prin/nn/`).
//!
//! Type stubs are generated to `python/prin/_prin_core.pyi`.

// Deny `unsafe_code` crate-wide and allow it only in the audited `dlpack`
// module (which uses `#![allow(unsafe_code)]`). `forbid` is not used because
// it cannot be scoped to a single module. This arrangement is approved via
// Project Plan amendment #6 / Coding Standards §2.1 Python-FFI exception.
#![deny(unsafe_code)]
#![deny(unsafe_op_in_unsafe_fn)]
#![warn(missing_docs)]

use pyo3::prelude::*;

mod bindings;
mod dlpack;

/// Version string of the compiled PRIN core.
#[pyfunction]
fn core_version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

/// The `prin._prin_core` extension module.
#[pymodule]
fn _prin_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(core_version, m)?)?;
    m.add_function(wrap_pyfunction!(dlpack::dlpack_negate, m)?)?;
    m.add_function(wrap_pyfunction!(dlpack::dlpack_negate_batched, m)?)?;
    m.add_function(wrap_pyfunction!(dlpack::dlpack_round_trip, m)?)?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;

    // Dynamics: state, seed, coupling, PAC, models, integrators
    bindings::state::register(m)?;
    bindings::coupling::register(m)?;
    bindings::models::register(m)?;
    bindings::integrators::register(m)?;

    // Metrics
    bindings::metrics::register(m)?;

    Ok(())
}
