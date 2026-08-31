//! PyO3 binding modules for the PRIN Rust core.
//!
//! Each submodule exposes Rust types and functions to Python via PyO3.
//! All numerical authority remains in Rust — these bindings are thin
//! wrappers that convert between Python and Rust types.

pub(crate) mod ablation;
pub(crate) mod allocation;
pub(crate) mod attention;
pub(crate) mod bands;
pub(crate) mod coupling;
pub(crate) mod daemon;
pub(crate) mod hybrid;
pub(crate) mod integrators;
pub(crate) mod kernels;
pub(crate) mod metrics;
pub(crate) mod models;
pub(crate) mod optim;
pub(crate) mod phase5;
pub(crate) mod phase_tracker;
pub(crate) mod slot_attention;
pub(crate) mod state;
pub(crate) mod sweep;
pub(crate) mod temporal;
pub(crate) mod tensor;
pub(crate) mod train;
pub(crate) mod train_autoencoders;
pub(crate) mod train_hierarchical_layers;
pub(crate) mod train_inhibition_layers;
pub(crate) mod train_layers;
pub(crate) mod train_model;
pub(crate) mod train_support;
pub(crate) mod trainer;
