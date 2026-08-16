//! # prin-kernels
//!
//! Single-source fused kernels for PRIN, collapsing the three PRINet 3.0
//! implementations (Triton / CUDA JIT / PyTorch fallback) into one kernel set:
//!
//! - Fused mean-field RK4 (target: ≥ Triton parity at N = 1M).
//! - Sparse k-NN coupling (target: ≥ 3× torch at N = 16K, k = 14).
//! - PAC modulation.
//! - Fused discrete step (three-band phase advance + PAC gating +
//!   Stuart–Landau amplitude dynamics, reusable hierarchical
//!   order-parameter reductions) — no runtime JIT, precompiled at
//!   wheel-build time.
//!
//! ## Architecture
//!
//! - [`backend`] — [`Device`](backend::Device) enum and priority-based
//!   fallback selection. Decouples *what* backends exist from *how* they are
//!   instantiated.
//! - [`buffers`] — Preallocated buffer pools (`MeanFieldRk4Buffers` for CPU,
//!   `CubeclBufferPool` for GPU) that eliminate per-step heap/device
//!   allocations.
//! - [`mean_field_rk4`] — CPU reference (numerical authority) and CubeCL
//!   single-source GPU kernels (the `cubecl` submodule requires the `cpu`,
//!   `cuda`, or `wgpu` feature).
//! - [`sparse_knn`] — CSR sparse phase-neighbor coupling: CPU reference and
//!   CubeCL gather kernel (same feature gating).
//! - [`pac`] — Phase–amplitude coupling modulation: CPU reference and CubeCL
//!   reduce + broadcast kernels (same feature gating).
//! - [`discrete_step`] — Fused three-band (delta/theta/gamma) discrete-time
//!   step: CPU reference and CubeCL kernels reusing hierarchical
//!   order-parameter/mean-phase reductions across bands (same feature
//!   gating).
//! - [`equivalence`] — Cross-backend equivalence testing harness.
//! - [`ops`] — Element-wise utility kernels (DLPack bridge spike).
//!
//! Design rule: **one algorithm, one implementation.** Backend dispatch
//! (CPU SIMD + rayon / CUDA / wgpu via CubeCL) happens inside this crate,
//! never by duplicating math at call sites.
//!
//! This is the only crate permitted to contain audited `unsafe` (kernel FFI);
//! audited kernel-FFI modules use `#![allow(unsafe_code)]` and
//! `#![deny(unsafe_op_in_unsafe_fn)]` per Coding Standards §2.1.

#![deny(unsafe_code)]
#![deny(unsafe_op_in_unsafe_fn)]
#![warn(missing_docs)]

pub mod backend;
pub mod buffers;
pub mod discrete_step;
pub mod equivalence;
pub mod mean_field_rk4;
pub mod ops;
pub mod pac;
pub mod sparse_knn;
