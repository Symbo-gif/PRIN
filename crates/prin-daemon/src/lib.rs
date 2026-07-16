//! # prin-daemon
//!
//! The subconscious controller for PRIN (rebuild of PRINet 3.0
//! `core/subconscious*.py` and `utils/npu_backend.py`):
//!
//! - State/control dataclasses (`STATE_DIM = 32`, `CONTROL_DIM = 8`).
//! - Background daemon on a real OS thread (no GIL contention) with a lock-free
//!   control-signal ring buffer.
//! - ONNX inference via the `ort` crate with backend auto-detection:
//!   VitisAI (Ryzen AI NPU) → DirectML → CPU.
//!
//! Target: lower p95 latency than the 3.0 Python-thread implementation.
//!
//! Implementation lands in Phase 5 (see `DOCS/PRIN_Project_Plan.md`).

#![forbid(unsafe_code)]
#![warn(missing_docs)]
