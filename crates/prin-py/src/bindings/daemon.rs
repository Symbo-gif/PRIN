//! PyO3 bindings for `prin_daemon` — subconscious controller state/control
//! types, execution-provider selection, and ONNX model validation (WP-028).
//!
//! # Division of labour
//!
//! Every numeric transformation and every selection decision lives in Rust:
//! packing telemetry into the 32-float controller input, decoding and clamping
//! the 8-float control vector, ranking execution providers, building the
//! fallback ladder, hashing model artefacts, and validating the ONNX graph
//! contract. The Python layer (`python/prin/daemon.py`) contributes only what
//! Rust cannot reach — the `onnxruntime` session object itself, and the
//! environment/filesystem values that feed these functions (Project Plan §7
//! risk register #4; see `crates/prin-daemon/src/backend.rs` for why the ONNX
//! session is created Python-side).
//!
//! Nothing here reads an environment variable or the clock, so a Python caller
//! that supplies the same inputs always gets the same answer.

use std::path::PathBuf;
use std::time::Duration;

use numpy::{PyArray1, PyArrayMethods, PyReadonlyArray1};
use pyo3::exceptions::{PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use prin_daemon::backend::{
    firmware_candidates, provider_options, resolve_firmware, select_backend, Backend,
    BackendSelection, SelectionReason, VitisAiConfig, BACKEND_PRIORITY, DEFAULT_CACHE_KEY,
    DEFAULT_NPU_TARGET, DEFAULT_XCLBIN,
};
use prin_daemon::daemon::{DaemonConfig, InferenceBackend, SubconsciousDaemon};
use prin_daemon::hooks::TrainingHooks;
use prin_daemon::model::{
    sha256_file, ControllerModel, ModelManifest, CONTROLLER_INPUT_NAME, CONTROLLER_OUTPUT_NAME,
    MANIFEST_FILE_NAME,
};
use prin_daemon::onnx::{inspect_onnx_file, Dim, OnnxModelInfo, TensorSpec};
use prin_daemon::state::{ControlSignals, Regime, SubconsciousState, CONTROL_DIM, STATE_DIM};
use prin_daemon::DaemonError;

/// Map a `prin-daemon` error onto a Python exception.
///
/// I/O failures become `OSError` so that callers can use the usual
/// filesystem-error handling; everything else is a `ValueError`, matching the
/// convention used by the other binding modules.
pub(crate) fn daemon_err_to_py(err: DaemonError) -> PyErr {
    match err {
        DaemonError::Io { ref path, .. } => {
            PyErr::new::<pyo3::exceptions::PyOSError, _>(format!("{path}: {err}"))
        }
        other => PyValueError::new_err(other.to_string()),
    }
}

// ---------------------------------------------------------------------------
// SubconsciousState
// ---------------------------------------------------------------------------

/// Compressed system snapshot handed to the subconscious controller.
///
/// Field names mirror PRINet 3.0 `prinet.core.subconscious.SubconsciousState`.
#[pyclass(
    name = "SubconsciousState",
    module = "prin._prin_core",
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PySubconsciousState {
    pub(crate) inner: SubconsciousState,
}

#[pymethods]
impl PySubconsciousState {
    #[new]
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (
        r_per_band=None,
        r_global=0.0,
        loss_ema=0.0,
        loss_variance=0.0,
        grad_norm_ema=0.0,
        lr_current=1e-3,
        scalr_alpha=1.0,
        gpu_temp=0.0,
        gpu_util=0.0,
        vram_pct=0.0,
        cpu_util=0.0,
        step_latency_p50=0.0,
        step_latency_p95=0.0,
        throughput=0.0,
        epoch=0,
        regime="mean_field",
        timestamp=0.0,
    ))]
    fn py_new(
        r_per_band: Option<Vec<f64>>,
        r_global: f64,
        loss_ema: f64,
        loss_variance: f64,
        grad_norm_ema: f64,
        lr_current: f64,
        scalr_alpha: f64,
        gpu_temp: f64,
        gpu_util: f64,
        vram_pct: f64,
        cpu_util: f64,
        step_latency_p50: f64,
        step_latency_p95: f64,
        throughput: f64,
        epoch: i64,
        regime: &str,
        timestamp: f64,
    ) -> Self {
        Self {
            inner: SubconsciousState {
                r_per_band: r_per_band.unwrap_or_else(|| vec![0.0, 0.0, 0.0]),
                r_global,
                loss_ema,
                loss_variance,
                grad_norm_ema,
                lr_current,
                scalr_alpha,
                gpu_temp,
                gpu_util,
                vram_pct,
                cpu_util,
                step_latency_p50,
                step_latency_p95,
                throughput,
                epoch,
                // An unrecognised regime name encodes as index 0, exactly as
                // PRINet 3.0's `_REGIME_MAP.get(regime, 0)` does.
                regime: Regime::from_name_or_default(regime),
                timestamp,
            },
        }
    }

    /// Per-band Kuramoto order parameters.
    #[getter]
    fn r_per_band(&self) -> Vec<f64> {
        self.inner.r_per_band.clone()
    }

    #[setter]
    fn set_r_per_band(&mut self, value: Vec<f64>) {
        self.inner.r_per_band = value;
    }

    /// Global order parameter.
    #[getter]
    fn r_global(&self) -> f64 {
        self.inner.r_global
    }

    #[setter]
    fn set_r_global(&mut self, value: f64) {
        self.inner.r_global = value;
    }

    /// Exponential moving average of the training loss.
    #[getter]
    fn loss_ema(&self) -> f64 {
        self.inner.loss_ema
    }

    #[setter]
    fn set_loss_ema(&mut self, value: f64) {
        self.inner.loss_ema = value;
    }

    /// Variance of the training loss over the recent window.
    #[getter]
    fn loss_variance(&self) -> f64 {
        self.inner.loss_variance
    }

    #[setter]
    fn set_loss_variance(&mut self, value: f64) {
        self.inner.loss_variance = value;
    }

    /// EMA of the gradient L2 norm.
    #[getter]
    fn grad_norm_ema(&self) -> f64 {
        self.inner.grad_norm_ema
    }

    #[setter]
    fn set_grad_norm_ema(&mut self, value: f64) {
        self.inner.grad_norm_ema = value;
    }

    /// Current learning rate.
    #[getter]
    fn lr_current(&self) -> f64 {
        self.inner.lr_current
    }

    #[setter]
    fn set_lr_current(&mut self, value: f64) {
        self.inner.lr_current = value;
    }

    /// Current SCALR coupling-strength modifier.
    #[getter]
    fn scalr_alpha(&self) -> f64 {
        self.inner.scalr_alpha
    }

    #[setter]
    fn set_scalr_alpha(&mut self, value: f64) {
        self.inner.scalr_alpha = value;
    }

    /// GPU temperature in degrees Celsius.
    #[getter]
    fn gpu_temp(&self) -> f64 {
        self.inner.gpu_temp
    }

    #[setter]
    fn set_gpu_temp(&mut self, value: f64) {
        self.inner.gpu_temp = value;
    }

    /// GPU utilisation fraction.
    #[getter]
    fn gpu_util(&self) -> f64 {
        self.inner.gpu_util
    }

    #[setter]
    fn set_gpu_util(&mut self, value: f64) {
        self.inner.gpu_util = value;
    }

    /// GPU VRAM utilisation fraction.
    #[getter]
    fn vram_pct(&self) -> f64 {
        self.inner.vram_pct
    }

    #[setter]
    fn set_vram_pct(&mut self, value: f64) {
        self.inner.vram_pct = value;
    }

    /// CPU utilisation fraction.
    #[getter]
    fn cpu_util(&self) -> f64 {
        self.inner.cpu_util
    }

    #[setter]
    fn set_cpu_util(&mut self, value: f64) {
        self.inner.cpu_util = value;
    }

    /// Median step latency in seconds.
    #[getter]
    fn step_latency_p50(&self) -> f64 {
        self.inner.step_latency_p50
    }

    #[setter]
    fn set_step_latency_p50(&mut self, value: f64) {
        self.inner.step_latency_p50 = value;
    }

    /// 95th-percentile step latency in seconds.
    #[getter]
    fn step_latency_p95(&self) -> f64 {
        self.inner.step_latency_p95
    }

    #[setter]
    fn set_step_latency_p95(&mut self, value: f64) {
        self.inner.step_latency_p95 = value;
    }

    /// Training throughput in samples per second.
    #[getter]
    fn throughput(&self) -> f64 {
        self.inner.throughput
    }

    #[setter]
    fn set_throughput(&mut self, value: f64) {
        self.inner.throughput = value;
    }

    /// Current epoch index.
    #[getter]
    fn epoch(&self) -> i64 {
        self.inner.epoch
    }

    #[setter]
    fn set_epoch(&mut self, value: i64) {
        self.inner.epoch = value;
    }

    /// Active coupling regime name.
    #[getter]
    fn regime(&self) -> &'static str {
        self.inner.regime.name()
    }

    #[setter]
    fn set_regime(&mut self, value: &str) {
        self.inner.regime = Regime::from_name_or_default(value);
    }

    /// Unix timestamp of the snapshot, in seconds.
    #[getter]
    fn timestamp(&self) -> f64 {
        self.inner.timestamp
    }

    #[setter]
    fn set_timestamp(&mut self, value: f64) {
        self.inner.timestamp = value;
    }

    /// Timestamp reduced to a fraction of a day in `[0, 1)`.
    #[getter]
    fn timestamp_fraction(&self) -> f64 {
        self.inner.timestamp_fraction()
    }

    /// Pack this snapshot into the controller's `(32,)` float32 input vector.
    fn to_tensor<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyArray1<f32>>> {
        let packed = self.inner.to_tensor().map_err(daemon_err_to_py)?;
        Ok(PyArray1::from_slice(py, &packed))
    }

    /// Return an independent copy of this snapshot.
    fn clone_state(&self) -> Self {
        self.clone()
    }

    fn __repr__(&self) -> String {
        format!(
            "SubconsciousState(r_global={}, epoch={}, regime='{}', timestamp={})",
            self.inner.r_global,
            self.inner.epoch,
            self.inner.regime.name(),
            self.inner.timestamp
        )
    }
}

// ---------------------------------------------------------------------------
// ControlSignals
// ---------------------------------------------------------------------------

/// Control suggestions produced by the subconscious controller.
///
/// Field names mirror PRINet 3.0 `prinet.core.subconscious.ControlSignals`,
/// including its capitalised `suggested_K_min`/`suggested_K_max`.
#[pyclass(
    name = "ControlSignals",
    module = "prin._prin_core",
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyControlSignals {
    pub(crate) inner: ControlSignals,
}

#[pymethods]
impl PyControlSignals {
    #[new]
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (
        suggested_K_min=0.5,
        suggested_K_max=5.0,
        lr_multiplier=1.0,
        regime_mf_weight=0.33,
        regime_sk_weight=0.33,
        regime_full_weight=0.34,
        alert_level=0.0,
        coupling_mode_suggestion=0.0,
    ))]
    #[allow(non_snake_case)]
    fn py_new(
        suggested_K_min: f64,
        suggested_K_max: f64,
        lr_multiplier: f64,
        regime_mf_weight: f64,
        regime_sk_weight: f64,
        regime_full_weight: f64,
        alert_level: f64,
        coupling_mode_suggestion: f64,
    ) -> Self {
        Self {
            inner: ControlSignals {
                suggested_k_min: suggested_K_min,
                suggested_k_max: suggested_K_max,
                lr_multiplier,
                regime_mf_weight,
                regime_sk_weight,
                regime_full_weight,
                alert_level,
                coupling_mode_suggestion,
            },
        }
    }

    /// Decode control signals from a controller output array.
    ///
    /// The array is narrowed to float32 before unpacking, matching the
    /// reference's `np.asarray(arr, dtype=np.float32)`.
    #[staticmethod]
    fn from_tensor(values: PyReadonlyArray1<f64>) -> PyResult<Self> {
        let slice = values
            .as_slice()
            .map_err(|_| PyTypeError::new_err("control tensor must be contiguous"))?;
        Ok(Self {
            inner: ControlSignals::from_tensor_f64(slice).map_err(daemon_err_to_py)?,
        })
    }

    /// Lower bound suggested for the coupling strength `K`.
    #[getter]
    #[allow(non_snake_case)]
    fn suggested_K_min(&self) -> f64 {
        self.inner.suggested_k_min
    }

    /// Upper bound suggested for the coupling strength `K`.
    #[getter]
    #[allow(non_snake_case)]
    fn suggested_K_max(&self) -> f64 {
        self.inner.suggested_k_max
    }

    /// Multiplicative learning-rate adjustment.
    #[getter]
    fn lr_multiplier(&self) -> f64 {
        self.inner.lr_multiplier
    }

    /// Preference weight for the mean-field regime.
    #[getter]
    fn regime_mf_weight(&self) -> f64 {
        self.inner.regime_mf_weight
    }

    /// Preference weight for the sparse k-NN regime.
    #[getter]
    fn regime_sk_weight(&self) -> f64 {
        self.inner.regime_sk_weight
    }

    /// Preference weight for the full-coupling regime.
    #[getter]
    fn regime_full_weight(&self) -> f64 {
        self.inner.regime_full_weight
    }

    /// Alert level in `[0, 1]`.
    #[getter]
    fn alert_level(&self) -> f64 {
        self.inner.alert_level
    }

    /// Suggested coupling-mode index, as a raw logit.
    #[getter]
    fn coupling_mode_suggestion(&self) -> f64 {
        self.inner.coupling_mode_suggestion
    }

    /// The regime with the highest preference weight.
    #[getter]
    fn preferred_regime(&self) -> &'static str {
        self.inner.preferred_regime().name()
    }

    /// Whether every control signal is finite.
    fn is_finite(&self) -> bool {
        self.inner.is_finite()
    }

    /// Pack these signals into an `(8,)` float32 array.
    fn to_tensor<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<f32>> {
        PyArray1::from_slice(py, &self.inner.to_tensor())
    }

    fn __repr__(&self) -> String {
        format!(
            "ControlSignals(suggested_K_min={}, suggested_K_max={}, lr_multiplier={}, alert_level={})",
            self.inner.suggested_k_min,
            self.inner.suggested_k_max,
            self.inner.lr_multiplier,
            self.inner.alert_level
        )
    }
}

// ---------------------------------------------------------------------------
// Native daemon and training hooks
// ---------------------------------------------------------------------------

struct PythonInferenceBackend {
    callback: Py<PyAny>,
}

impl InferenceBackend for PythonInferenceBackend {
    fn infer(&mut self, input: &[f32; STATE_DIM]) -> Result<[f32; CONTROL_DIM], DaemonError> {
        Python::attach(|py| {
            let input = PyArray1::from_slice(py, input);
            let result =
                self.callback
                    .call1(py, (input,))
                    .map_err(|error| DaemonError::Inference {
                        message: error.to_string(),
                    })?;
            let array = result.bind(py).cast::<PyArray1<f32>>().map_err(|error| {
                DaemonError::Inference {
                    message: format!("callback must return a contiguous float32 vector: {error}"),
                }
            })?;
            let readonly = array.readonly();
            let values = readonly
                .as_slice()
                .map_err(|error| DaemonError::Inference {
                    message: format!("callback result must be contiguous: {error}"),
                })?;
            values.try_into().map_err(|_| DaemonError::Inference {
                message: format!(
                    "callback must return exactly {CONTROL_DIM} values, got {}",
                    values.len()
                ),
            })
        })
    }
}

/// Rust-native subconscious daemon backed by a Python inference callback.
#[pyclass(name = "SubconsciousDaemon", module = "prin._prin_core")]
pub struct PySubconsciousDaemon {
    inner: Option<SubconsciousDaemon>,
}

#[pymethods]
impl PySubconsciousDaemon {
    /// Spawn the daemon and begin accepting telemetry states.
    #[new]
    #[pyo3(signature = (
        callback,
        interval_ms=15_000,
        queue_size=100,
        warmup=true,
        dlq_maxlen=100,
        max_errors_before_escalation=10,
    ))]
    fn new(
        callback: Py<PyAny>,
        interval_ms: u64,
        queue_size: usize,
        warmup: bool,
        dlq_maxlen: usize,
        max_errors_before_escalation: u64,
    ) -> PyResult<Self> {
        if queue_size == 0 {
            return Err(PyValueError::new_err("queue_size must be positive"));
        }
        let config = DaemonConfig {
            interval: Duration::from_millis(interval_ms),
            queue_size,
            warmup,
            dlq_maxlen,
            max_errors_before_escalation,
        };
        let backend = PythonInferenceBackend { callback };
        let daemon =
            SubconsciousDaemon::spawn(Box::new(backend), config, None).map_err(daemon_err_to_py)?;
        Ok(Self {
            inner: Some(daemon),
        })
    }

    /// Submit a telemetry state without blocking.
    fn submit_state(&self, state: &PySubconsciousState) -> PyResult<()> {
        self.running()?.submit_state(state.inner.clone());
        Ok(())
    }

    /// Return the latest published control signals.
    fn get_control(&self) -> PyResult<PyControlSignals> {
        Ok(PyControlSignals {
            inner: self.running()?.get_control(),
        })
    }

    /// Stop the daemon, releasing the interpreter while waiting.
    #[pyo3(signature = (timeout_ms=5_000))]
    fn stop(&mut self, py: Python<'_>, timeout_ms: u64) -> bool {
        let Some(daemon) = self.inner.as_mut() else {
            return true;
        };
        let stopped = py.detach(|| daemon.stop(Duration::from_millis(timeout_ms)));
        if stopped {
            self.inner = None;
        }
        stopped
    }

    /// Number of successful callback inferences.
    #[getter]
    fn inference_count(&self) -> u64 {
        self.inner
            .as_ref()
            .map_or(0, SubconsciousDaemon::inference_count)
    }

    /// Number of callback or state-packing failures.
    #[getter]
    fn error_count(&self) -> u64 {
        self.inner
            .as_ref()
            .map_or(0, SubconsciousDaemon::error_count)
    }

    /// Number of queued states not yet processed.
    #[getter]
    fn pending_states(&self) -> usize {
        self.inner
            .as_ref()
            .map_or(0, SubconsciousDaemon::pending_states)
    }
}

impl PySubconsciousDaemon {
    fn running(&self) -> PyResult<&SubconsciousDaemon> {
        self.inner
            .as_ref()
            .ok_or_else(|| PyValueError::new_err("daemon has already stopped"))
    }
}

impl Drop for PySubconsciousDaemon {
    fn drop(&mut self) {
        if let Some(daemon) = self.inner.take() {
            let _ = std::thread::Builder::new()
                .name("prin-python-daemon-cleanup".to_string())
                .spawn(move || drop(daemon));
        }
    }
}

/// Python-facing training telemetry collector.
#[pyclass(name = "TrainingHooks", module = "prin._prin_core")]
pub struct PyTrainingHooks {
    inner: TrainingHooks,
}

#[pymethods]
impl PyTrainingHooks {
    /// Construct a collector with the reference defaults.
    #[new]
    #[pyo3(signature = (loss_ema_alpha=0.1, latency_window=100))]
    fn new(loss_ema_alpha: f64, latency_window: usize) -> PyResult<Self> {
        Ok(Self {
            inner: TrainingHooks::new(loss_ema_alpha, latency_window).map_err(daemon_err_to_py)?,
        })
    }

    /// Accumulate one step using an explicit elapsed duration in milliseconds.
    #[pyo3(signature = (elapsed_ms, loss, grad_norms=None))]
    fn on_step_end(
        &mut self,
        elapsed_ms: f64,
        loss: f64,
        grad_norms: Option<Vec<f64>>,
    ) -> PyResult<()> {
        if !elapsed_ms.is_finite() || elapsed_ms < 0.0 {
            return Err(PyValueError::new_err(
                "elapsed_ms must be finite and non-negative",
            ));
        }
        self.inner.on_step_end_with_elapsed(
            Duration::from_secs_f64(elapsed_ms / 1_000.0),
            loss,
            grad_norms.as_deref(),
        );
        Ok(())
    }

    /// Package accumulated telemetry into a controller state.
    #[pyo3(signature = (
        epoch,
        loss=None,
        r_per_band=None,
        r_global=None,
        lr_current=1e-3,
        scalr_alpha=1.0,
        regime="mean_field",
        timestamp=0.0,
    ))]
    #[allow(clippy::too_many_arguments)]
    fn on_epoch_end(
        &mut self,
        epoch: i64,
        loss: Option<f64>,
        r_per_band: Option<Vec<f64>>,
        r_global: Option<f64>,
        lr_current: f64,
        scalr_alpha: f64,
        regime: &str,
        timestamp: f64,
    ) -> PySubconsciousState {
        PySubconsciousState {
            inner: self.inner.on_epoch_end(
                epoch,
                loss,
                r_per_band.unwrap_or_default(),
                r_global,
                lr_current,
                scalr_alpha,
                Regime::from_name_or_default(regime),
                timestamp,
            ),
        }
    }

    /// Current loss exponential moving average.
    #[getter]
    fn loss_ema(&self) -> f64 {
        self.inner.loss_ema()
    }

    /// Current gradient-norm exponential moving average.
    #[getter]
    fn grad_norm_ema(&self) -> f64 {
        self.inner.grad_norm_ema()
    }

    /// Total recorded step count.
    #[getter]
    fn step_count(&self) -> u64 {
        self.inner.step_count()
    }
}

// ---------------------------------------------------------------------------
// Backend selection
// ---------------------------------------------------------------------------

fn reason_name(reason: SelectionReason) -> &'static str {
    match reason {
        SelectionReason::Requested => "requested",
        SelectionReason::RequestedUnavailable => "requested_unavailable",
        SelectionReason::AutoDetected => "auto_detected",
    }
}

/// The outcome of execution-provider selection.
#[pyclass(
    name = "BackendSelection",
    module = "prin._prin_core",
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyBackendSelection {
    inner: BackendSelection,
}

#[pymethods]
impl PyBackendSelection {
    /// Backend to attempt first (`npu`, `directml`, or `cpu`).
    #[getter]
    fn backend(&self) -> &'static str {
        self.inner.backend.name()
    }

    /// Why that backend was chosen.
    #[getter]
    fn reason(&self) -> &'static str {
        reason_name(self.inner.reason)
    }

    /// The backend that was explicitly requested, if any.
    #[getter]
    fn requested(&self) -> Option<&'static str> {
        self.inner.requested.map(Backend::name)
    }

    /// Backends to try, in order, until a session is created.
    #[getter]
    fn attempt_order(&self) -> Vec<&'static str> {
        self.inner.attempt_order.iter().map(|b| b.name()).collect()
    }

    /// Provider names offered by ONNX Runtime.
    #[getter]
    fn available_providers(&self) -> Vec<String> {
        self.inner.available_providers.clone()
    }

    /// Whether selection degraded away from an explicit request.
    #[getter]
    fn is_degraded(&self) -> bool {
        self.inner.is_degraded()
    }

    /// ONNX Runtime provider names for one attempt on `backend`.
    fn provider_names(&self, backend: &str) -> PyResult<Vec<&'static str>> {
        let backend = Backend::parse(backend).map_err(daemon_err_to_py)?;
        Ok(backend.provider_names())
    }

    fn __repr__(&self) -> String {
        format!(
            "BackendSelection(backend='{}', reason='{}')",
            self.inner.backend.name(),
            reason_name(self.inner.reason)
        )
    }
}

/// Rank the available execution providers and build the fallback ladder.
///
/// `available` is the list ONNX Runtime reported; `requested` optionally names
/// `npu`, `directml`, or `cpu`.
#[pyfunction]
#[pyo3(signature = (available, requested=None))]
fn select_execution_backend(
    available: Vec<String>,
    requested: Option<&str>,
) -> PyResult<PyBackendSelection> {
    let requested = match requested {
        Some(value) => Some(Backend::parse(value).map_err(daemon_err_to_py)?),
        None => None,
    };
    Ok(PyBackendSelection {
        inner: select_backend(&available, requested).map_err(daemon_err_to_py)?,
    })
}

/// The ONNX Runtime provider chain for one session attempt on `backend`.
#[pyfunction]
fn backend_provider_names(backend: &str) -> PyResult<Vec<&'static str>> {
    Ok(Backend::parse(backend)
        .map_err(daemon_err_to_py)?
        .provider_names())
}

/// Backend identifiers in descending preference order.
#[pyfunction]
fn backend_priority() -> Vec<&'static str> {
    BACKEND_PRIORITY.iter().map(|b| b.name()).collect()
}

/// Per-provider option maps for one session attempt on `backend`.
///
/// Returns one dict per entry of [`backend_provider_names`]. The VitisAI entry
/// carries `config_file`, `xclbin`, `target`, `cache_dir`, and `cache_key`;
/// every other provider gets an empty dict.
#[pyfunction]
#[pyo3(signature = (backend, sdk_root=None, firmware=None, cache_dir=None, target=None))]
fn backend_provider_options<'py>(
    py: Python<'py>,
    backend: &str,
    sdk_root: Option<PathBuf>,
    firmware: Option<PathBuf>,
    cache_dir: Option<PathBuf>,
    target: Option<&str>,
) -> PyResult<Bound<'py, PyList>> {
    let backend = Backend::parse(backend).map_err(daemon_err_to_py)?;
    let config = match (sdk_root, firmware, cache_dir) {
        (Some(root), Some(fw), Some(cache)) => Some(VitisAiConfig::from_sdk_root(
            &root,
            &fw,
            &cache,
            target.unwrap_or(DEFAULT_NPU_TARGET),
        )),
        _ => None,
    };
    let options = provider_options(backend, config.as_ref()).map_err(daemon_err_to_py)?;
    let out = PyList::empty(py);
    for entry in options {
        let dict = PyDict::new(py);
        for (key, value) in entry {
            dict.set_item(key, value)?;
        }
        out.append(dict)?;
    }
    Ok(out)
}

/// Candidate `.xclbin` firmware paths, in probe order.
#[pyfunction]
#[pyo3(signature = (env_override, sdk_root, xclbin=None))]
fn npu_firmware_candidates(
    env_override: Option<&str>,
    sdk_root: PathBuf,
    xclbin: Option<&str>,
) -> Vec<String> {
    firmware_candidates(env_override, &sdk_root, xclbin)
        .into_iter()
        .map(|p| p.display().to_string())
        .collect()
}

/// Resolve the NPU firmware overlay to the first existing candidate path.
#[pyfunction]
#[pyo3(signature = (env_override, sdk_root, xclbin=None))]
fn resolve_npu_firmware(
    env_override: Option<&str>,
    sdk_root: PathBuf,
    xclbin: Option<&str>,
) -> PyResult<String> {
    resolve_firmware(env_override, &sdk_root, xclbin)
        .map(|p| p.display().to_string())
        .map_err(daemon_err_to_py)
}

// ---------------------------------------------------------------------------
// Model validation
// ---------------------------------------------------------------------------

fn dim_to_object<'py>(py: Python<'py>, dim: &Dim) -> PyResult<Bound<'py, PyAny>> {
    match dim {
        Dim::Fixed(value) => Ok(value.into_pyobject(py)?.into_any()),
        Dim::Param(name) => Ok(name.into_pyobject(py)?.into_any()),
        Dim::Unknown => Ok(py.None().into_bound(py)),
    }
}

fn tensor_spec_to_dict<'py>(py: Python<'py>, spec: &TensorSpec) -> PyResult<Bound<'py, PyDict>> {
    let dict = PyDict::new(py);
    dict.set_item("name", &spec.name)?;
    dict.set_item("elem_type", spec.elem_type)?;
    dict.set_item("has_shape", spec.has_shape)?;
    let dims = PyList::empty(py);
    for dim in &spec.dims {
        dims.append(dim_to_object(py, dim)?)?;
    }
    dict.set_item("shape", dims)?;
    Ok(dict)
}

fn model_info_to_dict<'py>(py: Python<'py>, info: &OnnxModelInfo) -> PyResult<Bound<'py, PyDict>> {
    let dict = PyDict::new(py);
    dict.set_item("ir_version", info.ir_version)?;
    dict.set_item("producer_name", &info.producer_name)?;
    dict.set_item("producer_version", &info.producer_version)?;
    dict.set_item("graph_name", &info.graph_name)?;
    dict.set_item("default_opset", info.default_opset())?;

    let opsets = PyList::empty(py);
    for opset in &info.opset_import {
        let entry = PyDict::new(py);
        entry.set_item("domain", &opset.domain)?;
        entry.set_item("version", opset.version)?;
        opsets.append(entry)?;
    }
    dict.set_item("opset_import", opsets)?;

    let inputs = PyList::empty(py);
    for spec in &info.inputs {
        inputs.append(tensor_spec_to_dict(py, spec)?)?;
    }
    dict.set_item("inputs", inputs)?;

    let outputs = PyList::empty(py);
    for spec in &info.outputs {
        outputs.append(tensor_spec_to_dict(py, spec)?)?;
    }
    dict.set_item("outputs", outputs)?;

    dict.set_item("op_types", info.op_types.clone())?;
    dict.set_item("external_data_files", info.external_data_files.clone())?;

    let initializers = PyList::empty(py);
    for init in &info.initializers {
        let entry = PyDict::new(py);
        entry.set_item("name", &init.name)?;
        entry.set_item("data_type", init.data_type)?;
        entry.set_item("dims", init.dims.clone())?;
        entry.set_item("external", init.external)?;
        initializers.append(entry)?;
    }
    dict.set_item("initializers", initializers)?;
    Ok(dict)
}

/// SHA-256 hex digest of a file, computed with a streaming reader.
#[pyfunction]
fn model_sha256(path: PathBuf) -> PyResult<String> {
    sha256_file(path).map_err(daemon_err_to_py)
}

/// Decode an ONNX model's graph metadata without loading a runtime.
#[pyfunction]
fn inspect_onnx_model<'py>(py: Python<'py>, path: PathBuf) -> PyResult<Bound<'py, PyDict>> {
    let info = inspect_onnx_file(path).map_err(daemon_err_to_py)?;
    model_info_to_dict(py, &info)
}

/// Verify a model directory against its `manifest.json`.
///
/// Returns one dict per covered file with its absolute `path`, `sha256`, and
/// `bytes`. Raises `ValueError` on a digest or size mismatch and `OSError` if
/// a covered file is missing.
#[pyfunction]
fn verify_model_manifest<'py>(
    py: Python<'py>,
    models_dir: PathBuf,
) -> PyResult<Bound<'py, PyList>> {
    let manifest =
        ModelManifest::load(models_dir.join(MANIFEST_FILE_NAME)).map_err(daemon_err_to_py)?;
    let verified = manifest.verify(&models_dir).map_err(daemon_err_to_py)?;
    let out = PyList::empty(py);
    for file in verified {
        let entry = PyDict::new(py);
        entry.set_item("path", file.path.display().to_string())?;
        entry.set_item("sha256", file.sha256)?;
        entry.set_item("bytes", file.bytes)?;
        out.append(entry)?;
    }
    Ok(out)
}

/// Validate a controller model's integrity, companions, and graph contract.
///
/// Returns a dict with `path`, `sha256`, `external_data`, and the decoded
/// graph `info`.
#[pyfunction]
#[pyo3(signature = (path, expected_sha256=None))]
fn validate_controller_model<'py>(
    py: Python<'py>,
    path: PathBuf,
    expected_sha256: Option<&str>,
) -> PyResult<Bound<'py, PyDict>> {
    let model = ControllerModel::validate(&path, expected_sha256).map_err(daemon_err_to_py)?;
    let dict = PyDict::new(py);
    dict.set_item("path", model.path.display().to_string())?;
    dict.set_item("sha256", &model.sha256)?;
    dict.set_item(
        "external_data",
        model
            .external_data
            .iter()
            .map(|p| p.display().to_string())
            .collect::<Vec<_>>(),
    )?;
    dict.set_item("info", model_info_to_dict(py, &model.info)?)?;
    Ok(dict)
}

/// Register the subconscious-controller bindings on the extension module.
pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PySubconsciousState>()?;
    m.add_class::<PyControlSignals>()?;
    m.add_class::<PySubconsciousDaemon>()?;
    m.add_class::<PyTrainingHooks>()?;
    m.add_class::<PyBackendSelection>()?;
    m.add_function(wrap_pyfunction!(select_execution_backend, m)?)?;
    m.add_function(wrap_pyfunction!(backend_provider_names, m)?)?;
    m.add_function(wrap_pyfunction!(backend_priority, m)?)?;
    m.add_function(wrap_pyfunction!(backend_provider_options, m)?)?;
    m.add_function(wrap_pyfunction!(npu_firmware_candidates, m)?)?;
    m.add_function(wrap_pyfunction!(resolve_npu_firmware, m)?)?;
    m.add_function(wrap_pyfunction!(model_sha256, m)?)?;
    m.add_function(wrap_pyfunction!(inspect_onnx_model, m)?)?;
    m.add_function(wrap_pyfunction!(verify_model_manifest, m)?)?;
    m.add_function(wrap_pyfunction!(validate_controller_model, m)?)?;
    m.add("STATE_DIM", STATE_DIM)?;
    m.add("CONTROL_DIM", CONTROL_DIM)?;
    m.add("CONTROLLER_INPUT_NAME", CONTROLLER_INPUT_NAME)?;
    m.add("CONTROLLER_OUTPUT_NAME", CONTROLLER_OUTPUT_NAME)?;
    m.add("MODEL_MANIFEST_FILE_NAME", MANIFEST_FILE_NAME)?;
    m.add("DEFAULT_NPU_TARGET", DEFAULT_NPU_TARGET)?;
    m.add("DEFAULT_NPU_CACHE_KEY", DEFAULT_CACHE_KEY)?;
    m.add("DEFAULT_NPU_XCLBIN", DEFAULT_XCLBIN)?;
    Ok(())
}
