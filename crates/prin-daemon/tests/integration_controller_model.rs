//! End-to-end validation of the committed subconscious-controller artefacts.
//!
//! These tests run against the real `models/` directory rather than a
//! fabricated graph: they verify the SHA-256 manifest, decode the actual
//! `subconscious_controller.onnx` produced by PRINet 3.0's
//! `SubconsciousController.export_to_onnx`, and assert that its graph honours
//! the controller contract the Rust state/control types are built around.
//!
//! Together they close the loop between [`prin_daemon::state`]'s
//! `STATE_DIM`/`CONTROL_DIM` constants and the artefact those constants
//! describe — if the model is ever replaced with an incompatible export, or
//! silently altered on disk, these tests fail rather than the runtime.

use std::path::{Path, PathBuf};

use prin_daemon::model::{
    validate_controller_contract, validate_external_data, ControllerModel, ModelManifest,
    CONTROLLER_INPUT_NAME, CONTROLLER_OUTPUT_NAME, MANIFEST_FILE_NAME,
};
use prin_daemon::onnx::{inspect_onnx_file, Dim, ELEM_TYPE_FLOAT};
use prin_daemon::state::{CONTROL_DIM, STATE_DIM};
use prin_daemon::DaemonError;

/// Absolute path to the repository's `models/` directory.
fn models_dir() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("models")
}

fn model_path() -> PathBuf {
    models_dir().join("subconscious_controller.onnx")
}

#[test]
fn the_committed_manifest_verifies_every_model_artefact() {
    let manifest = ModelManifest::load(models_dir().join(MANIFEST_FILE_NAME)).expect("manifest");
    assert_eq!(manifest.schema_version, 1);
    assert_eq!(manifest.files.len(), 2);

    let verified = manifest.verify(models_dir()).expect("artefacts verify");
    assert_eq!(verified.len(), 2);

    // WP-036F (session 0144U) re-exported the graph with three-input `Gemm`
    // nodes (explicit zero bias) so DirectML's `DmlFusedGemm` fusion accepts it;
    // the function is unchanged (bit-identical on CPUExecutionProvider) but the
    // digest and size move. WP-005's `EVIDENCE/0017-wp005-s1-ort-probe.json`
    // records the pre-transform digest and is left as the historical artefact.
    let graph = manifest
        .entry("subconscious_controller.onnx")
        .expect("graph entry");
    assert_eq!(
        graph.sha256,
        "d7d7935b70b3faab7af303be088bd82698f2140ff27a9d9f74a811d609d8341a"
    );
    assert_eq!(graph.bytes, 19_428);

    let data = manifest
        .entry("subconscious_controller.onnx.data")
        .expect("external data entry");
    assert_eq!(data.bytes, 86_016);
}

#[test]
fn the_committed_graph_decodes_with_the_expected_metadata() {
    let info = inspect_onnx_file(model_path()).expect("decodes");
    assert_eq!(info.ir_version, 10);
    assert_eq!(info.default_opset(), Some(18));
    assert_eq!(info.producer_name, "pytorch");
    assert_eq!(info.graph_name, "main_graph");

    // The exported head: three Gemm/ReLU stages then the per-channel
    // activation slices of `SubconsciousController.forward`.
    assert!(info.op_types.iter().filter(|op| *op == "Gemm").count() == 3);
    assert!(info.op_types.contains(&"Softmax".to_string()));
    assert!(info.op_types.contains(&"Sigmoid".to_string()));
    assert!(info.op_types.iter().any(|op| op == "Softplus"));

    // Weights live in the committed external-data companion.
    assert_eq!(
        info.external_data_files,
        vec!["subconscious_controller.onnx.data".to_string()]
    );
    assert!(info.initializers.iter().any(|i| i.name == "net.0.weight"));
}

#[test]
fn the_committed_graph_matches_the_controller_contract() {
    let info = inspect_onnx_file(model_path()).expect("decodes");
    validate_controller_contract(&info).expect("contract holds");

    let input = &info.inputs[0];
    assert_eq!(input.name, CONTROLLER_INPUT_NAME);
    assert_eq!(input.elem_type, ELEM_TYPE_FLOAT);
    assert_eq!(input.dims[0], Dim::Param("batch".to_string()));
    assert_eq!(input.dims[1], Dim::Fixed(STATE_DIM as i64));

    let output = &info.outputs[0];
    assert_eq!(output.name, CONTROLLER_OUTPUT_NAME);
    assert_eq!(output.elem_type, ELEM_TYPE_FLOAT);
    assert_eq!(output.dims[0], Dim::Param("batch".to_string()));
    assert_eq!(output.dims[1], Dim::Fixed(CONTROL_DIM as i64));
}

#[test]
fn the_external_data_companion_is_present() {
    let info = inspect_onnx_file(model_path()).expect("decodes");
    let companions = validate_external_data(model_path(), &info).expect("companion present");
    assert_eq!(companions.len(), 1);
    assert!(companions[0].is_file());
}

#[test]
fn full_validation_succeeds_against_the_manifest_digest() {
    let manifest = ModelManifest::load(models_dir().join(MANIFEST_FILE_NAME)).expect("manifest");
    let expected = &manifest
        .entry("subconscious_controller.onnx")
        .expect("graph entry")
        .sha256;

    let model = ControllerModel::validate(model_path(), Some(expected)).expect("valid");
    assert_eq!(&model.sha256, expected);
    assert_eq!(model.external_data.len(), 1);
    assert_eq!(model.info.graph_name, "main_graph");
}

#[test]
fn full_validation_rejects_a_wrong_digest() {
    let err = ControllerModel::validate(model_path(), Some(&"0".repeat(64)))
        .expect_err("digest mismatch");
    assert!(matches!(err, DaemonError::HashMismatch { .. }));
    let message = err.to_string();
    assert!(message.contains(&"0".repeat(64)));
    assert!(message.contains("d7d7935b70b3faab7af303be088bd82698f2140ff27a9d9f74a811d609d8341a"));
}

#[test]
fn validation_without_an_expected_digest_still_enforces_the_contract() {
    let model = ControllerModel::validate(model_path(), None).expect("valid");
    assert_eq!(
        model.sha256,
        "d7d7935b70b3faab7af303be088bd82698f2140ff27a9d9f74a811d609d8341a"
    );
}
