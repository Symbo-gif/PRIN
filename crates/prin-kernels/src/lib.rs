//! # prin-kernels
//!
//! Single-source fused kernels for PRIN, collapsing the three PRINet 3.0
//! implementations (Triton / CUDA JIT / PyTorch fallback) into one kernel set:
//!
//! - Fused mean-field RK4 (target: ≥ Triton parity at N = 1M).
//! - Sparse k-NN coupling (target: ≥ 3× torch at N = 16K, k = 14).
//! - PAC modulation.
//! - Fused discrete step (phase advance + PAC gating + Stuart–Landau in one
//!   launch) — no runtime JIT, precompiled at wheel-build time.
//! - Hierarchical order-parameter reductions.
//!
//! Design rule: **one algorithm, one implementation.** Backend dispatch
//! (CPU SIMD + rayon / CUDA / wgpu via CubeCL) happens inside this crate, never
//! by duplicating math at call sites.
//!
//! This is the only crate permitted to contain audited `unsafe` (kernel FFI);
//! `unsafe` remains forbidden until the Phase 3 kernel work begins and is then
//! confined to dedicated, reviewed modules.
//!
//! Implementation lands in Phase 3 (see `DOCS/PRIN_Project_Plan.md`).

#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod ops;
