//! Controller model integrity and graph-contract validation.
//!
//! Before the subconscious controller hands a file to an inference runtime it
//! establishes three facts:
//!
//! 1. **Integrity** — the bytes on disk hash to the SHA-256 digest recorded in
//!    `models/manifest.json` ([`ModelManifest::verify`]).
//! 2. **Completeness** — every external-data companion the graph references
//!    exists next to the model ([`validate_external_data`]).
//! 3. **Contract** — the graph exposes exactly one `state_vector`
//!    `[batch, 32]` float input and one `control_signals` `[batch, 8]` float
//!    output ([`validate_controller_contract`]).
//!
//! All three are runtime-independent: they hold whether the session would
//! eventually run on VitisAI, DirectML, or CPU, which is what makes a
//! cross-provider output comparison meaningful in the first place.

use std::io::Read;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::error::DaemonError;
use crate::onnx::{inspect_onnx_file, Dim, OnnxModelInfo, TensorSpec, ELEM_TYPE_FLOAT};
use crate::state::{CONTROL_DIM, STATE_DIM};

/// Graph input name produced by PRINet 3.0's
/// `SubconsciousController.export_to_onnx`.
pub const CONTROLLER_INPUT_NAME: &str = "state_vector";

/// Graph output name produced by PRINet 3.0's
/// `SubconsciousController.export_to_onnx`.
pub const CONTROLLER_OUTPUT_NAME: &str = "control_signals";

/// File name of the model manifest inside the `models/` directory.
pub const MANIFEST_FILE_NAME: &str = "manifest.json";

/// Number of bytes read per hashing iteration.
const HASH_CHUNK: usize = 64 * 1024;

// ---------------------------------------------------------------------------
// Hashing
// ---------------------------------------------------------------------------

/// SHA-256 hex digest of a byte slice.
///
/// # Examples
///
/// ```
/// use prin_daemon::model::sha256_bytes;
///
/// assert_eq!(
///     sha256_bytes(b""),
///     "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
/// );
/// ```
#[must_use]
pub fn sha256_bytes(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    hex_digest(&hasher.finalize())
}

/// Streaming SHA-256 hex digest of a file, with the byte count it covered.
///
/// The digest and the size come from the same pass, so a manifest check can
/// never compare a digest against a size measured from a different revision of
/// the file.
///
/// # Errors
///
/// Returns [`DaemonError::Io`] if the file cannot be opened or read.
pub fn sha256_file_with_size(path: impl AsRef<Path>) -> Result<(String, u64), DaemonError> {
    let path = path.as_ref();
    let io_err = |source| DaemonError::Io {
        path: path.display().to_string(),
        source,
    };
    let mut file = std::fs::File::open(path).map_err(io_err)?;
    let mut hasher = Sha256::new();
    let mut buffer = vec![0_u8; HASH_CHUNK];
    let mut total: u64 = 0;
    loop {
        let read = file.read(&mut buffer).map_err(io_err)?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
        total = total.saturating_add(read as u64);
    }
    Ok((hex_digest(&hasher.finalize()), total))
}

/// Streaming SHA-256 hex digest of a file.
///
/// The file is read in fixed-size chunks, so the memory cost is independent of
/// the model size (the controller's external-data companion is already 84 KiB
/// and future controllers may be far larger).
///
/// # Errors
///
/// Returns [`DaemonError::Io`] if the file cannot be opened or read.
pub fn sha256_file(path: impl AsRef<Path>) -> Result<String, DaemonError> {
    sha256_file_with_size(path).map(|(digest, _)| digest)
}

fn hex_digest(digest: &[u8]) -> String {
    use std::fmt::Write as _;
    digest.iter().fold(String::with_capacity(64), |mut acc, b| {
        // Writing to a String is infallible; the result is discarded
        // deliberately rather than unwrapped.
        let _ = write!(acc, "{b:02x}");
        acc
    })
}

/// Whether `value` is a well-formed lowercase SHA-256 hex digest.
#[must_use]
pub fn is_valid_digest(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

/// Verify that `path` hashes to `expected`, returning the computed digest.
///
/// # Errors
///
/// * [`DaemonError::InvalidDigest`] if `expected` is not 64 lowercase hex
///   characters — a malformed manifest entry must never be able to pass.
/// * [`DaemonError::Io`] if the file cannot be read.
/// * [`DaemonError::HashMismatch`] if the digests differ.
pub fn verify_sha256(path: impl AsRef<Path>, expected: &str) -> Result<String, DaemonError> {
    verify_sha256_with_size(path, expected).map(|(digest, _)| digest)
}

/// Verify that `path` hashes to `expected`, returning the digest and its size.
///
/// # Errors
///
/// The same errors as [`verify_sha256`].
pub fn verify_sha256_with_size(
    path: impl AsRef<Path>,
    expected: &str,
) -> Result<(String, u64), DaemonError> {
    if !is_valid_digest(expected) {
        return Err(DaemonError::InvalidDigest {
            value: expected.to_string(),
        });
    }
    let path = path.as_ref();
    let (actual, bytes) = sha256_file_with_size(path)?;
    if actual == expected {
        Ok((actual, bytes))
    } else {
        Err(DaemonError::HashMismatch {
            path: path.display().to_string(),
            expected: expected.to_string(),
            actual,
        })
    }
}

// ---------------------------------------------------------------------------
// Manifest
// ---------------------------------------------------------------------------

/// One entry of the model manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManifestEntry {
    /// Path relative to the manifest's own directory.
    pub path: String,
    /// Expected file size in bytes.
    pub bytes: u64,
    /// Expected lowercase SHA-256 hex digest.
    pub sha256: String,
}

/// SHA-256 manifest for the committed model artefacts.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ModelManifest {
    /// Manifest schema version.
    pub schema_version: u32,
    /// Human-readable description of the artefacts covered.
    pub description: String,
    /// Every covered file.
    pub files: Vec<ManifestEntry>,
}

/// Result of verifying one manifest entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct VerifiedFile {
    /// Absolute path that was hashed.
    pub path: PathBuf,
    /// The digest computed from disk (equal to the manifest entry).
    pub sha256: String,
    /// The file's size in bytes.
    pub bytes: u64,
}

impl ModelManifest {
    /// Parse a manifest from JSON text.
    ///
    /// # Errors
    ///
    /// Returns [`DaemonError::ManifestParse`] if the text is not a valid
    /// manifest document, or [`DaemonError::EmptyManifest`] if it covers no
    /// files — an empty manifest would make verification vacuously succeed.
    pub fn from_json(source: &str, origin: &str) -> Result<Self, DaemonError> {
        let manifest: ModelManifest =
            serde_json::from_str(source).map_err(|err| DaemonError::ManifestParse {
                path: origin.to_string(),
                reason: err.to_string(),
            })?;
        if manifest.files.is_empty() {
            return Err(DaemonError::EmptyManifest {
                path: origin.to_string(),
            });
        }
        Ok(manifest)
    }

    /// Load a manifest from disk.
    ///
    /// # Errors
    ///
    /// Returns [`DaemonError::Io`] if the file cannot be read, plus any error
    /// from [`ModelManifest::from_json`].
    pub fn load(path: impl AsRef<Path>) -> Result<Self, DaemonError> {
        let path = path.as_ref();
        let source = std::fs::read_to_string(path).map_err(|source| DaemonError::Io {
            path: path.display().to_string(),
            source,
        })?;
        Self::from_json(&source, &path.display().to_string())
    }

    /// Verify every entry against files in `root`.
    ///
    /// # Errors
    ///
    /// Returns the first failure encountered: [`DaemonError::InvalidDigest`],
    /// [`DaemonError::Io`], or [`DaemonError::HashMismatch`].
    pub fn verify(&self, root: impl AsRef<Path>) -> Result<Vec<VerifiedFile>, DaemonError> {
        let root = root.as_ref();
        let mut verified = Vec::with_capacity(self.files.len());
        for entry in &self.files {
            let path = root.join(&entry.path);
            let (sha256, bytes) = verify_sha256_with_size(&path, &entry.sha256)?;
            if bytes != entry.bytes {
                return Err(DaemonError::SizeMismatch {
                    path: path.display().to_string(),
                    expected: entry.bytes,
                    actual: bytes,
                });
            }
            verified.push(VerifiedFile {
                path,
                sha256,
                bytes,
            });
        }
        Ok(verified)
    }

    /// The manifest entry for `name`, if present.
    #[must_use]
    pub fn entry(&self, name: &str) -> Option<&ManifestEntry> {
        self.files.iter().find(|entry| entry.path == name)
    }
}

// ---------------------------------------------------------------------------
// Graph contract
// ---------------------------------------------------------------------------

/// Check one graph input/output against the controller contract.
fn validate_tensor(
    spec: &TensorSpec,
    kind: &'static str,
    expected_name: &'static str,
    expected_extent: usize,
) -> Result<(), DaemonError> {
    if spec.name != expected_name {
        return Err(DaemonError::GraphName {
            kind,
            expected: expected_name,
            got: spec.name.clone(),
        });
    }
    if spec.elem_type != ELEM_TYPE_FLOAT {
        return Err(DaemonError::GraphElemType {
            kind,
            name: spec.name.clone(),
            expected: ELEM_TYPE_FLOAT,
            got: spec.elem_type,
        });
    }
    if !spec.has_shape || spec.dims.len() != 2 {
        return Err(DaemonError::GraphRank {
            kind,
            name: spec.name.clone(),
            expected: 2,
            got: if spec.has_shape { spec.dims.len() } else { 0 },
        });
    }
    // Dimension 0 is the batch axis: symbolic (the exported default) or any
    // positive static extent.
    match &spec.dims[0] {
        Dim::Param(_) => {}
        Dim::Fixed(n) if *n > 0 => {}
        other => {
            return Err(DaemonError::GraphDim {
                kind,
                name: spec.name.clone(),
                index: 0,
                expected: "a symbolic batch axis or a positive extent".to_string(),
                got: other.clone(),
            })
        }
    }
    let expected = i64::try_from(expected_extent).unwrap_or(i64::MAX);
    if spec.dims[1] != Dim::Fixed(expected) {
        return Err(DaemonError::GraphDim {
            kind,
            name: spec.name.clone(),
            index: 1,
            expected: expected.to_string(),
            got: spec.dims[1].clone(),
        });
    }
    Ok(())
}

/// Validate that `info` describes the subconscious-controller graph.
///
/// The contract is exactly one float input `state_vector` of shape
/// `[batch, STATE_DIM]` and exactly one float output `control_signals` of
/// shape `[batch, CONTROL_DIM]`.
///
/// # Errors
///
/// Returns the [`DaemonError`] `Graph*` variant describing the first
/// violation: wrong arity, name, element type, rank, or extent.
///
/// # Examples
///
/// ```
/// use prin_daemon::model::validate_controller_contract;
/// use prin_daemon::onnx::{Dim, OnnxModelInfo, TensorSpec, ELEM_TYPE_FLOAT};
///
/// let spec = |name: &str, extent: i64| TensorSpec {
///     name: name.to_string(),
///     elem_type: ELEM_TYPE_FLOAT,
///     dims: vec![Dim::Param("batch".to_string()), Dim::Fixed(extent)],
///     has_shape: true,
/// };
/// let info = OnnxModelInfo {
///     ir_version: 10,
///     producer_name: String::new(),
///     producer_version: String::new(),
///     opset_import: Vec::new(),
///     graph_name: "main_graph".to_string(),
///     inputs: vec![spec("state_vector", 32)],
///     outputs: vec![spec("control_signals", 8)],
///     op_types: Vec::new(),
///     initializers: Vec::new(),
///     external_data_files: Vec::new(),
/// };
/// validate_controller_contract(&info)?;
/// # Ok::<(), prin_daemon::DaemonError>(())
/// ```
pub fn validate_controller_contract(info: &OnnxModelInfo) -> Result<(), DaemonError> {
    if info.inputs.len() != 1 {
        return Err(DaemonError::GraphArity {
            kind: "input",
            expected: 1,
            got: info.inputs.len(),
        });
    }
    if info.outputs.len() != 1 {
        return Err(DaemonError::GraphArity {
            kind: "output",
            expected: 1,
            got: info.outputs.len(),
        });
    }
    validate_tensor(&info.inputs[0], "input", CONTROLLER_INPUT_NAME, STATE_DIM)?;
    validate_tensor(
        &info.outputs[0],
        "output",
        CONTROLLER_OUTPUT_NAME,
        CONTROL_DIM,
    )
}

/// Check that every external-data companion referenced by the graph exists.
///
/// # Errors
///
/// Returns [`DaemonError::MissingExternalData`] naming the first missing
/// companion file.
pub fn validate_external_data(
    model_path: impl AsRef<Path>,
    info: &OnnxModelInfo,
) -> Result<Vec<PathBuf>, DaemonError> {
    let model_path = model_path.as_ref();
    let dir = model_path.parent().unwrap_or_else(|| Path::new("."));
    let mut found = Vec::with_capacity(info.external_data_files.len());
    for file in &info.external_data_files {
        let candidate = dir.join(file);
        if !candidate.is_file() {
            return Err(DaemonError::MissingExternalData {
                model: model_path.display().to_string(),
                file: candidate.display().to_string(),
            });
        }
        found.push(candidate);
    }
    Ok(found)
}

/// A controller model that passed integrity, completeness, and contract checks.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ControllerModel {
    /// Path to the `.onnx` graph.
    pub path: PathBuf,
    /// SHA-256 digest of the graph file.
    pub sha256: String,
    /// Companion files the graph loads its weights from.
    pub external_data: Vec<PathBuf>,
    /// The decoded graph metadata.
    pub info: OnnxModelInfo,
}

impl ControllerModel {
    /// Validate a controller model end to end.
    ///
    /// When `expected_sha256` is supplied the file is hashed and compared
    /// before anything else is inspected; passing `None` skips only the
    /// integrity step, never the contract.
    ///
    /// # Errors
    ///
    /// Any [`DaemonError`] raised by [`verify_sha256`], [`inspect_onnx_file`],
    /// [`validate_external_data`], or [`validate_controller_contract`].
    pub fn validate(
        path: impl AsRef<Path>,
        expected_sha256: Option<&str>,
    ) -> Result<Self, DaemonError> {
        let path = path.as_ref();
        let sha256 = match expected_sha256 {
            Some(expected) => verify_sha256(path, expected)?,
            None => sha256_file(path)?,
        };
        let info = inspect_onnx_file(path)?;
        let external_data = validate_external_data(path, &info)?;
        validate_controller_contract(&info)?;
        Ok(Self {
            path: path.to_path_buf(),
            sha256,
            external_data,
            info,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::onnx::OpsetId;

    fn spec(name: &str, extent: i64) -> TensorSpec {
        TensorSpec {
            name: name.to_string(),
            elem_type: ELEM_TYPE_FLOAT,
            dims: vec![Dim::Param("batch".to_string()), Dim::Fixed(extent)],
            has_shape: true,
        }
    }

    fn info_with(inputs: Vec<TensorSpec>, outputs: Vec<TensorSpec>) -> OnnxModelInfo {
        OnnxModelInfo {
            ir_version: 10,
            producer_name: "pytorch".to_string(),
            producer_version: "2.10.0".to_string(),
            opset_import: vec![OpsetId {
                domain: String::new(),
                version: 18,
            }],
            graph_name: "main_graph".to_string(),
            inputs,
            outputs,
            op_types: Vec::new(),
            initializers: Vec::new(),
            external_data_files: Vec::new(),
        }
    }

    fn valid_info() -> OnnxModelInfo {
        info_with(
            vec![spec(CONTROLLER_INPUT_NAME, STATE_DIM as i64)],
            vec![spec(CONTROLLER_OUTPUT_NAME, CONTROL_DIM as i64)],
        )
    }

    #[test]
    fn empty_and_known_digests_are_correct() {
        assert_eq!(
            sha256_bytes(b""),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
        assert_eq!(
            sha256_bytes(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }

    #[test]
    fn streaming_hash_matches_in_memory_hash_across_chunk_boundaries() {
        let dir = tempfile::tempdir().expect("temp dir");
        let path = dir.path().join("big.bin");
        let payload: Vec<u8> = (0..(HASH_CHUNK * 2 + 17))
            .map(|i| (i % 251) as u8)
            .collect();
        std::fs::write(&path, &payload).expect("write");
        assert_eq!(sha256_file(&path).expect("hash"), sha256_bytes(&payload));
    }

    #[test]
    fn hashing_a_missing_file_is_an_io_error() {
        let err = sha256_file("no-such-file.bin").expect_err("missing");
        assert!(matches!(err, DaemonError::Io { .. }));
    }

    #[test]
    fn digest_validation_rejects_malformed_values() {
        assert!(is_valid_digest(&"a".repeat(64)));
        assert!(!is_valid_digest(&"A".repeat(64))); // uppercase
        assert!(!is_valid_digest(&"g".repeat(64))); // non-hex
        assert!(!is_valid_digest("abc")); // too short
        assert!(!is_valid_digest(&"a".repeat(65))); // too long
    }

    #[test]
    fn verify_sha256_reports_mismatches_and_rejects_bad_expectations() {
        let dir = tempfile::tempdir().expect("temp dir");
        let path = dir.path().join("payload.bin");
        std::fs::write(&path, b"abc").expect("write");

        let digest = verify_sha256(
            &path,
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )
        .expect("matches");
        assert_eq!(digest, sha256_bytes(b"abc"));

        let err = verify_sha256(&path, &"0".repeat(64)).expect_err("mismatch");
        assert!(matches!(err, DaemonError::HashMismatch { .. }));

        let err = verify_sha256(&path, "not-a-digest").expect_err("bad digest");
        assert!(matches!(err, DaemonError::InvalidDigest { .. }));
    }

    #[test]
    fn manifest_round_trips_and_verifies() {
        let dir = tempfile::tempdir().expect("temp dir");
        std::fs::write(dir.path().join("model.onnx"), b"abc").expect("write");
        let manifest = ModelManifest {
            schema_version: 1,
            description: "test".to_string(),
            files: vec![ManifestEntry {
                path: "model.onnx".to_string(),
                bytes: 3,
                sha256: sha256_bytes(b"abc"),
            }],
        };
        let json = serde_json::to_string(&manifest).expect("serialises");
        let parsed = ModelManifest::from_json(&json, "memory").expect("parses");
        assert_eq!(parsed, manifest);
        assert!(parsed.entry("model.onnx").is_some());
        assert!(parsed.entry("absent").is_none());

        let verified = parsed.verify(dir.path()).expect("verifies");
        assert_eq!(verified.len(), 1);
        assert_eq!(verified[0].bytes, 3);
    }

    #[test]
    fn manifest_verification_detects_size_drift() {
        let dir = tempfile::tempdir().expect("temp dir");
        std::fs::write(dir.path().join("model.onnx"), b"abc").expect("write");
        let manifest = ModelManifest {
            schema_version: 1,
            description: "test".to_string(),
            files: vec![ManifestEntry {
                path: "model.onnx".to_string(),
                bytes: 4,
                sha256: sha256_bytes(b"abc"),
            }],
        };
        let err = manifest.verify(dir.path()).expect_err("size drift");
        assert!(matches!(err, DaemonError::SizeMismatch { .. }));
    }

    #[test]
    fn empty_and_malformed_manifests_are_rejected() {
        let err = ModelManifest::from_json(
            r#"{"schema_version":1,"description":"","files":[]}"#,
            "memory",
        )
        .expect_err("empty");
        assert!(matches!(err, DaemonError::EmptyManifest { .. }));

        let err = ModelManifest::from_json("{ not json", "memory").expect_err("malformed");
        assert!(matches!(err, DaemonError::ManifestParse { .. }));

        let err = ModelManifest::load("no-such-manifest.json").expect_err("missing");
        assert!(matches!(err, DaemonError::Io { .. }));
    }

    #[test]
    fn the_reference_contract_is_accepted() {
        validate_controller_contract(&valid_info()).expect("valid");
    }

    #[test]
    fn a_static_positive_batch_axis_is_accepted() {
        let mut info = valid_info();
        info.inputs[0].dims[0] = Dim::Fixed(4);
        validate_controller_contract(&info).expect("valid");
    }

    #[test]
    fn wrong_arity_is_rejected() {
        let info = info_with(Vec::new(), vec![spec(CONTROLLER_OUTPUT_NAME, 8)]);
        assert!(matches!(
            validate_controller_contract(&info).expect_err("no input"),
            DaemonError::GraphArity {
                kind: "input",
                got: 0,
                ..
            }
        ));

        let info = info_with(
            vec![spec(CONTROLLER_INPUT_NAME, 32)],
            vec![spec(CONTROLLER_OUTPUT_NAME, 8), spec("extra", 8)],
        );
        assert!(matches!(
            validate_controller_contract(&info).expect_err("two outputs"),
            DaemonError::GraphArity {
                kind: "output",
                got: 2,
                ..
            }
        ));
    }

    #[test]
    fn wrong_names_are_rejected() {
        let info = info_with(
            vec![spec("inputs", 32)],
            vec![spec(CONTROLLER_OUTPUT_NAME, 8)],
        );
        assert!(matches!(
            validate_controller_contract(&info).expect_err("bad input name"),
            DaemonError::GraphName { kind: "input", .. }
        ));

        let info = info_with(
            vec![spec(CONTROLLER_INPUT_NAME, 32)],
            vec![spec("logits", 8)],
        );
        assert!(matches!(
            validate_controller_contract(&info).expect_err("bad output name"),
            DaemonError::GraphName { kind: "output", .. }
        ));
    }

    #[test]
    fn non_float_element_types_are_rejected() {
        let mut info = valid_info();
        info.inputs[0].elem_type = 11; // double
        assert!(matches!(
            validate_controller_contract(&info).expect_err("f64 input"),
            DaemonError::GraphElemType { got: 11, .. }
        ));
    }

    #[test]
    fn wrong_rank_and_missing_shape_are_rejected() {
        let mut info = valid_info();
        info.inputs[0].dims = vec![Dim::Fixed(32)];
        assert!(matches!(
            validate_controller_contract(&info).expect_err("rank 1"),
            DaemonError::GraphRank { got: 1, .. }
        ));

        let mut info = valid_info();
        info.inputs[0].has_shape = false;
        info.inputs[0].dims = Vec::new();
        assert!(matches!(
            validate_controller_contract(&info).expect_err("no shape"),
            DaemonError::GraphRank { got: 0, .. }
        ));
    }

    #[test]
    fn a_non_positive_or_unknown_batch_axis_is_rejected() {
        for bad in [Dim::Fixed(0), Dim::Fixed(-1), Dim::Unknown] {
            let mut info = valid_info();
            info.inputs[0].dims[0] = bad;
            assert!(matches!(
                validate_controller_contract(&info).expect_err("bad batch axis"),
                DaemonError::GraphDim { index: 0, .. }
            ));
        }
    }

    #[test]
    fn wrong_feature_extents_are_rejected() {
        let mut info = valid_info();
        info.inputs[0].dims[1] = Dim::Fixed(16);
        assert!(matches!(
            validate_controller_contract(&info).expect_err("wrong state dim"),
            DaemonError::GraphDim { index: 1, .. }
        ));

        let mut info = valid_info();
        info.outputs[0].dims[1] = Dim::Param("control".to_string());
        assert!(matches!(
            validate_controller_contract(&info).expect_err("symbolic control dim"),
            DaemonError::GraphDim { index: 1, .. }
        ));
    }

    #[test]
    fn external_data_presence_is_checked() {
        let dir = tempfile::tempdir().expect("temp dir");
        let model = dir.path().join("model.onnx");
        std::fs::write(&model, b"stub").expect("write");
        let mut info = valid_info();
        info.external_data_files = vec!["model.onnx.data".to_string()];

        let err = validate_external_data(&model, &info).expect_err("missing companion");
        assert!(matches!(err, DaemonError::MissingExternalData { .. }));

        std::fs::write(dir.path().join("model.onnx.data"), b"weights").expect("write");
        let found = validate_external_data(&model, &info).expect("present");
        assert_eq!(found.len(), 1);
    }

    #[test]
    fn a_model_without_external_data_needs_no_companions() {
        let found = validate_external_data("model.onnx", &valid_info()).expect("no companions");
        assert!(found.is_empty());
    }

    #[test]
    fn validate_rejects_a_tampered_model_before_inspecting_it() {
        let dir = tempfile::tempdir().expect("temp dir");
        let model = dir.path().join("model.onnx");
        std::fs::write(&model, b"not really onnx").expect("write");
        let err = ControllerModel::validate(&model, Some(&"0".repeat(64))).expect_err("mismatch");
        assert!(matches!(err, DaemonError::HashMismatch { .. }));
    }
}
