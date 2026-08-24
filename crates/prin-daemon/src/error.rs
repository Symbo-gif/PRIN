//! Typed errors for the PRIN subconscious controller.
//!
//! Every fallible operation in this crate returns [`DaemonError`]; the crate
//! contains no `panic!`/`unwrap`/`expect` in library code paths (Coding
//! Standards §2.2).

use thiserror::Error;

use crate::onnx::Dim;

/// Errors raised by controller state/control conversion, backend selection,
/// and ONNX model validation.
#[derive(Debug, Error)]
pub enum DaemonError {
    /// A filesystem operation failed.
    #[error("i/o error for `{path}`: {source}")]
    Io {
        /// Path the operation was attempted on.
        path: String,
        /// Underlying I/O error.
        #[source]
        source: std::io::Error,
    },

    /// A control-signal tensor was shorter than [`crate::state::CONTROL_DIM`].
    #[error("control tensor must have at least {expected} elements, got {got}")]
    ControlTooShort {
        /// Required element count.
        expected: usize,
        /// Element count actually supplied.
        got: usize,
    },

    /// A value was not finite (raised only under the `strict-checks` feature).
    #[error("non-finite value in `{name}`: {value}")]
    NonFiniteValue {
        /// Name of the offending field.
        name: &'static str,
        /// Offending value.
        value: f64,
    },

    /// A backend identifier string was not one of `npu`, `directml`, `cpu`.
    #[error("unknown backend `{value}` (expected one of `npu`, `directml`, `cpu`)")]
    UnknownBackend {
        /// The rejected identifier.
        value: String,
    },

    /// None of the supported execution providers was registered with ONNX
    /// Runtime, so no session — not even a CPU session — can be created.
    #[error("no supported execution provider found in {available:?}")]
    NoProviderAvailable {
        /// Provider names that were offered.
        available: Vec<String>,
    },

    /// A SHA-256 digest string was not 64 lowercase hex characters.
    #[error("invalid SHA-256 digest `{value}`: expected 64 lowercase hex characters")]
    InvalidDigest {
        /// The rejected digest string.
        value: String,
    },

    /// A model file's SHA-256 digest did not match the expected value.
    #[error("model SHA-256 mismatch for `{path}`: expected {expected}, got {actual}")]
    HashMismatch {
        /// Path of the hashed file.
        path: String,
        /// Digest recorded in the manifest.
        expected: String,
        /// Digest computed from the file on disk.
        actual: String,
    },

    /// A model file's size did not match the expected value.
    #[error("model size mismatch for `{path}`: expected {expected} bytes, got {actual}")]
    SizeMismatch {
        /// Path of the offending file.
        path: String,
        /// Size recorded in the manifest.
        expected: u64,
        /// Size measured on disk.
        actual: u64,
    },

    /// A model manifest could not be parsed.
    #[error("model manifest `{path}` is not valid: {reason}")]
    ManifestParse {
        /// Manifest path (or `"memory"` for in-memory documents).
        path: String,
        /// Parser diagnostic.
        reason: String,
    },

    /// A model manifest covered no files, so verification would be vacuous.
    #[error("model manifest `{path}` lists no files")]
    EmptyManifest {
        /// Manifest path.
        path: String,
    },

    /// An ONNX graph referenced an external-data companion that is absent.
    #[error("model `{model}` references external data file `{file}`, which is missing")]
    MissingExternalData {
        /// Path of the model that made the reference.
        model: String,
        /// Path the companion was expected at.
        file: String,
    },

    /// The VitisAI NPU firmware (`.xclbin`) could not be located.
    #[error("NPU firmware not found; searched {searched:?}")]
    FirmwareNotFound {
        /// Candidate paths that were probed, in order.
        searched: Vec<String>,
    },

    /// The ONNX protobuf stream is malformed.
    #[error("malformed ONNX protobuf at byte {offset}: {reason}")]
    MalformedOnnx {
        /// Byte offset at which decoding failed.
        offset: usize,
        /// Human-readable reason.
        reason: &'static str,
    },

    /// The ONNX graph declared the wrong number of inputs or outputs.
    #[error("ONNX graph has {got} {kind}(s); expected exactly {expected}")]
    GraphArity {
        /// Either `"input"` or `"output"`.
        kind: &'static str,
        /// Expected count.
        expected: usize,
        /// Actual count.
        got: usize,
    },

    /// An ONNX graph input/output had an unexpected name.
    #[error("ONNX {kind} name mismatch: expected `{expected}`, got `{got}`")]
    GraphName {
        /// Either `"input"` or `"output"`.
        kind: &'static str,
        /// Name required by the controller contract.
        expected: &'static str,
        /// Name found in the graph.
        got: String,
    },

    /// An ONNX graph input/output had an unexpected element type.
    #[error("ONNX {kind} `{name}` has element type {got}; expected {expected} (tensor(float))")]
    GraphElemType {
        /// Either `"input"` or `"output"`.
        kind: &'static str,
        /// Tensor name.
        name: String,
        /// Expected ONNX `TensorProto.DataType` code.
        expected: i32,
        /// Element type found in the graph.
        got: i32,
    },

    /// An ONNX graph input/output had an unexpected rank.
    #[error("ONNX {kind} `{name}` has rank {got}; expected {expected}")]
    GraphRank {
        /// Either `"input"` or `"output"`.
        kind: &'static str,
        /// Tensor name.
        name: String,
        /// Expected rank.
        expected: usize,
        /// Rank found in the graph.
        got: usize,
    },

    /// The daemon's background inference thread could not be spawned.
    #[error("failed to spawn the subconscious-daemon thread: {source}")]
    ThreadSpawn {
        /// Underlying OS error.
        #[source]
        source: std::io::Error,
    },

    /// An ONNX graph input/output dimension did not match the contract.
    #[error("ONNX {kind} `{name}` dimension {index} is {got}; expected {expected}")]
    GraphDim {
        /// Either `"input"` or `"output"`.
        kind: &'static str,
        /// Tensor name.
        name: String,
        /// Zero-based dimension index.
        index: usize,
        /// Expected dimension description.
        expected: String,
        /// Dimension found in the graph.
        got: Dim,
    },
}
