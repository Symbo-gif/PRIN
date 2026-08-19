//! PyO3 binding modules for the PRIN Rust core.
//!
//! Each submodule exposes Rust types and functions to Python via PyO3.
//! All numerical authority remains in Rust — these bindings are thin
//! wrappers that convert between Python and Rust types.

pub(crate) mod bands;
pub(crate) mod coupling;
pub(crate) mod integrators;
pub(crate) mod metrics;
pub(crate) mod models;
pub(crate) mod state;
pub(crate) mod temporal;
pub(crate) mod train;
