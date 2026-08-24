//! # prin-daemon
//!
//! The subconscious controller for PRIN (rebuild of PRINet 3.0
//! `core/subconscious*.py` and `utils/npu_backend.py`).
//!
//! Delivered in WP-028 (Phase 5):
//!
//! - [`state`] — [`state::SubconsciousState`] and [`state::ControlSignals`],
//!   the fixed-schema controller I/O types (`STATE_DIM = 32`,
//!   `CONTROL_DIM = 8`), with PRINet 3.0's exact packing, normalisation, and
//!   clamping semantics.
//! - [`backend`] — [`backend::Backend`] and [`backend::select_backend`]:
//!   execution-provider priority (VitisAI → DirectML → CPU), explicit-override
//!   handling, and the deterministic CPU-terminated fallback ladder.
//! - [`onnx`] — runtime-independent inspection of an ONNX `ModelProto`'s graph
//!   inputs, outputs, opsets, and external-data references.
//! - [`model`] — SHA-256 integrity verification against
//!   `models/manifest.json`, external-data completeness, and the controller
//!   graph contract.
//!
//! Delivered in WP-029 (Phase 5):
//!
//! - [`daemon`] — [`daemon::SubconsciousDaemon`], the native background
//!   thread that drains submitted [`state::SubconsciousState`] snapshots
//!   through a pluggable [`daemon::InferenceBackend`] and publishes
//!   [`state::ControlSignals`] through the lock-free
//!   [`daemon::ControlSignalBuffer`] — the WP-029 rebuild of PRINet 3.0's
//!   `subconscious_daemon.py` and `ControlSignalBuffer`.
//!
//! # Scope boundaries
//!
//! **Inference execution** runs through the Python `onnxruntime` bindings
//! (`prin.daemon`), per Project Plan §7 risk register #4: the VitisAI
//! execution provider ships only inside the Ryzen AI SDK's custom ONNX
//! Runtime Python wheel, and DirectML only as a platform-specific wheel, so
//! neither is reachable from the `ort` crate's prebuilt binaries. This crate
//! therefore owns every decision and every numeric transformation around that
//! call — including the whole [`daemon`] runtime — but does not link an
//! inference runtime itself; the `npu` cargo feature stays reserved for a
//! future native binding, and [`daemon::InferenceBackend`] is the seam a
//! Python-backed session is wired in through.
//!
//! # Example
//!
//! ```
//! use prin_daemon::backend::{select_backend, Backend};
//! use prin_daemon::state::{ControlSignals, Regime, SubconsciousState};
//!
//! // Pack a telemetry snapshot into the controller's 32-float input.
//! let snapshot = SubconsciousState {
//!     r_per_band: vec![0.81, 0.64, 0.42],
//!     r_global: 0.62,
//!     regime: Regime::SparseKnn,
//!     ..SubconsciousState::default()
//! };
//! let input = snapshot.to_tensor()?;
//! assert_eq!(input.len(), prin_daemon::state::STATE_DIM);
//!
//! // Pick a provider from what ONNX Runtime reported, with a fallback ladder.
//! let selection = select_backend(&["DmlExecutionProvider", "CPUExecutionProvider"], None)?;
//! assert_eq!(selection.backend, Backend::DirectMl);
//! assert_eq!(selection.attempt_order.last(), Some(&Backend::Cpu));
//!
//! // Decode whatever the session returned.
//! let control = ControlSignals::from_tensor(&[0.5, 5.0, 1.0, 0.2, 0.5, 0.3, 0.0, 0.0])?;
//! assert_eq!(control.preferred_regime(), Regime::SparseKnn);
//! # Ok::<(), prin_daemon::DaemonError>(())
//! ```

#![forbid(unsafe_code)]
#![warn(missing_docs)]

pub mod backend;
pub mod daemon;
pub mod error;
pub mod model;
pub mod onnx;
pub mod state;

pub use backend::{
    provider_options, select_backend, Backend, BackendSelection, SelectionReason, VitisAiConfig,
};
pub use daemon::{
    ControlSignalBuffer, DaemonConfig, DaemonStats, DeadLetterEntry, EscalationCallback,
    EscalationEvent, InferenceBackend, SubconsciousDaemon,
};
pub use error::DaemonError;
pub use model::{
    sha256_file, validate_controller_contract, ControllerModel, ManifestEntry, ModelManifest,
};
pub use onnx::{inspect_onnx_file, Dim, OnnxModelInfo, TensorSpec};
pub use state::{ControlSignals, Regime, SubconsciousState, CONTROL_DIM, STATE_DIM};
