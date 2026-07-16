//! # prin-py
//!
//! The PyO3 binding crate for PRIN — the **only** crate that links against
//! Python. Exposes the Rust core (`prin-dynamics`, `prin-metrics`,
//! `prin-tensor`, `prin-kernels`, `prin-sim`, `prin-train`, `prin-daemon`)
//! as the `prin._prin_core` extension module.
//!
//! Tensor exchange with PyTorch is zero-copy via DLPack; trainable components
//! are surfaced Python-side as `torch.autograd.Function`s whose forward and
//! backward call into Rust (see `python/prin/nn/`).
//!
//! Type stubs are generated to `python/prin/_prin_core.pyi`.

#![warn(missing_docs)]

use pyo3::prelude::*;

/// Version string of the compiled PRIN core.
#[pyfunction]
fn core_version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

/// The `prin._prin_core` extension module.
#[pymodule]
fn _prin_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(core_version, m)?)?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
