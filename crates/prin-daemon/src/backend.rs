//! Execution-provider selection and deterministic fallback.
//!
//! Rebuild of PRINet 3.0 `prinet/utils/npu_backend.py`. This module owns the
//! *policy*: the priority order VitisAI → DirectML → CPU, how an explicit
//! override interacts with what ONNX Runtime actually registered, the ordered
//! provider list handed to a session, and the fallback ladder walked when a
//! provider refuses to execute the graph. It performs no I/O beyond a single
//! `is_file` probe in [`resolve_firmware`] and reads no environment variables,
//! so every decision is reproducible from its inputs alone.
//!
//! Session creation itself stays on the Python `onnxruntime` path (Project
//! Plan §7 risk register #4): the VitisAI execution provider ships only as the
//! Ryzen AI SDK's custom ONNX Runtime Python wheel, and DirectML only as a
//! Windows-specific wheel/NuGet package, so neither is reachable from the
//! `ort` crate's prebuilt binaries. The `npu` cargo feature stays reserved for
//! a future native binding.

use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::DaemonError;

/// ONNX Runtime provider name for the AMD XDNA NPU (Ryzen AI / VitisAI).
pub const PROVIDER_VITISAI: &str = "VitisAIExecutionProvider";

/// ONNX Runtime provider name for DirectML.
pub const PROVIDER_DIRECTML: &str = "DmlExecutionProvider";

/// ONNX Runtime provider name for the always-present CPU provider.
pub const PROVIDER_CPU: &str = "CPUExecutionProvider";

/// Default VitisAI compilation target: `X1` = Phoenix / Hawk Point (AIE2).
/// `X2` selects Strix Point (AIE2P).
pub const DEFAULT_NPU_TARGET: &str = "X1";

/// Default VitisAI compilation-cache key.
pub const DEFAULT_CACHE_KEY: &str = "subconscious_v1";

/// Default NPU firmware overlay — the 1×4 overlay has the lowest latency.
pub const DEFAULT_XCLBIN: &str = "1x4.xclbin";

/// VitisAI EP runtime directory inside a Ryzen AI SDK installation.
pub const VOE_DIR: &str = "voe-4.0-win_amd64";

/// Backends in descending preference order.
pub const BACKEND_PRIORITY: [Backend; 3] = [Backend::Npu, Backend::DirectMl, Backend::Cpu];

/// An execution provider the subconscious controller can target.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Backend {
    /// AMD XDNA NPU via the VitisAI execution provider.
    Npu,
    /// GPU (or NPU) via the DirectML execution provider.
    DirectMl,
    /// Always-available CPU execution provider.
    Cpu,
}

impl Backend {
    /// The ONNX Runtime provider name for this backend.
    #[must_use]
    pub fn provider(self) -> &'static str {
        match self {
            Backend::Npu => PROVIDER_VITISAI,
            Backend::DirectMl => PROVIDER_DIRECTML,
            Backend::Cpu => PROVIDER_CPU,
        }
    }

    /// The short identifier used in configuration and telemetry
    /// (`npu`, `directml`, `cpu`), matching PRINet 3.0's `BackendType`.
    #[must_use]
    pub fn name(self) -> &'static str {
        match self {
            Backend::Npu => "npu",
            Backend::DirectMl => "directml",
            Backend::Cpu => "cpu",
        }
    }

    /// Selection priority; lower sorts first.
    #[must_use]
    pub fn priority(self) -> u8 {
        match self {
            Backend::Npu => 0,
            Backend::DirectMl => 1,
            Backend::Cpu => 2,
        }
    }

    /// Parse a backend identifier, ignoring surrounding whitespace and case.
    ///
    /// # Errors
    ///
    /// Returns [`DaemonError::UnknownBackend`] for anything other than
    /// `npu`, `directml`, or `cpu`.
    ///
    /// # Examples
    ///
    /// ```
    /// use prin_daemon::backend::Backend;
    ///
    /// assert_eq!(Backend::parse("  DirectML ")?, Backend::DirectMl);
    /// assert!(Backend::parse("tpu").is_err());
    /// # Ok::<(), prin_daemon::DaemonError>(())
    /// ```
    pub fn parse(value: &str) -> Result<Self, DaemonError> {
        match value.trim().to_ascii_lowercase().as_str() {
            "npu" => Ok(Backend::Npu),
            "directml" => Ok(Backend::DirectMl),
            "cpu" => Ok(Backend::Cpu),
            _ => Err(DaemonError::UnknownBackend {
                value: value.to_string(),
            }),
        }
    }

    /// The ordered provider list handed to one ONNX Runtime session attempt.
    ///
    /// Accelerator backends are always trailed by the CPU provider so that
    /// ONNX Runtime can place unsupported subgraphs on CPU, exactly as
    /// PRINet 3.0's `_build_provider_list` does.
    ///
    /// # Examples
    ///
    /// ```
    /// use prin_daemon::backend::Backend;
    ///
    /// assert_eq!(Backend::Npu.provider_chain(), &[Backend::Npu, Backend::Cpu]);
    /// assert_eq!(Backend::Cpu.provider_chain(), &[Backend::Cpu]);
    /// ```
    #[must_use]
    pub fn provider_chain(self) -> &'static [Backend] {
        match self {
            Backend::Npu => &[Backend::Npu, Backend::Cpu],
            Backend::DirectMl => &[Backend::DirectMl, Backend::Cpu],
            Backend::Cpu => &[Backend::Cpu],
        }
    }

    /// The provider chain of [`Backend::provider_chain`] as ORT names.
    #[must_use]
    pub fn provider_names(self) -> Vec<&'static str> {
        self.provider_chain().iter().map(|b| b.provider()).collect()
    }
}

/// Why [`select_backend`] chose the backend it did.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SelectionReason {
    /// An explicit request was honoured.
    Requested,
    /// An explicit request named a provider ONNX Runtime has not registered,
    /// so priority order was used instead.
    RequestedUnavailable,
    /// No request was made; priority order was used.
    AutoDetected,
}

/// The outcome of backend selection, including the fallback ladder.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BackendSelection {
    /// The backend a session should be attempted on first.
    pub backend: Backend,
    /// Why that backend was chosen.
    pub reason: SelectionReason,
    /// The backend explicitly requested, if any.
    pub requested: Option<Backend>,
    /// Every backend to try, in order, until a session is created.
    pub attempt_order: Vec<Backend>,
    /// Provider names that were offered, in the order ONNX Runtime reported.
    pub available_providers: Vec<String>,
}

impl BackendSelection {
    /// Whether the selection degraded away from an explicit request.
    #[must_use]
    pub fn is_degraded(&self) -> bool {
        self.reason == SelectionReason::RequestedUnavailable
    }
}

/// Which of `available` correspond to known backends, in priority order.
fn detected<S: AsRef<str>>(available: &[S]) -> Vec<Backend> {
    BACKEND_PRIORITY
        .into_iter()
        .filter(|backend| available.iter().any(|p| p.as_ref() == backend.provider()))
        .collect()
}

/// Choose an execution provider and compute the deterministic fallback ladder.
///
/// Selection is:
///
/// 1. `requested`, when ONNX Runtime registered its provider;
/// 2. otherwise the highest-priority registered backend
///    (VitisAI → DirectML → CPU).
///
/// [`BackendSelection::attempt_order`] lists the chosen backend followed by
/// every *lower-priority* registered backend, so a session attempt that fails
/// walks strictly downwards and terminates at CPU whenever the CPU provider is
/// registered. The ladder depends only on `available` and `requested`, never
/// on the environment, so two callers given the same inputs always get the
/// same order.
///
/// # Errors
///
/// Returns [`DaemonError::NoProviderAvailable`] when `available` contains none
/// of the three supported providers — including when ONNX Runtime is absent
/// and the list is empty.
///
/// # Examples
///
/// ```
/// use prin_daemon::backend::{select_backend, Backend, SelectionReason};
///
/// // VitisAI was requested but only DirectML and CPU are registered.
/// let available = ["DmlExecutionProvider", "CPUExecutionProvider"];
/// let selection = select_backend(&available, Some(Backend::Npu))?;
/// assert_eq!(selection.backend, Backend::DirectMl);
/// assert_eq!(selection.reason, SelectionReason::RequestedUnavailable);
/// assert_eq!(selection.attempt_order, vec![Backend::DirectMl, Backend::Cpu]);
/// # Ok::<(), prin_daemon::DaemonError>(())
/// ```
pub fn select_backend<S: AsRef<str>>(
    available: &[S],
    requested: Option<Backend>,
) -> Result<BackendSelection, DaemonError> {
    let candidates = detected(available);
    let first = *candidates
        .first()
        .ok_or_else(|| DaemonError::NoProviderAvailable {
            available: available.iter().map(|p| p.as_ref().to_string()).collect(),
        })?;

    let (backend, reason) = match requested {
        Some(want) if candidates.contains(&want) => (want, SelectionReason::Requested),
        Some(_) => (first, SelectionReason::RequestedUnavailable),
        None => (first, SelectionReason::AutoDetected),
    };

    let attempt_order = candidates
        .into_iter()
        .filter(|c| c.priority() >= backend.priority())
        .collect();

    Ok(BackendSelection {
        backend,
        reason,
        requested,
        attempt_order,
        available_providers: available.iter().map(|p| p.as_ref().to_string()).collect(),
    })
}

/// Provider options for the VitisAI execution provider.
///
/// Mirrors the keys the Ryzen AI SDK's ONNX Runtime build expects; paths are
/// supplied by the caller so that this crate stays free of environment reads.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct VitisAiConfig {
    /// Path to `vaip_config.json`.
    pub config_file: PathBuf,
    /// Path to the `.xclbin` NPU firmware overlay.
    pub xclbin: PathBuf,
    /// Compilation target (`X1` for Phoenix / Hawk Point, `X2` for Strix).
    pub target: String,
    /// Directory for the VitisAI compilation cache.
    pub cache_dir: PathBuf,
    /// Cache key identifying this compiled model.
    pub cache_key: String,
}

impl VitisAiConfig {
    /// Build a configuration rooted at a Ryzen AI SDK installation.
    ///
    /// `firmware` is the resolved `.xclbin` path (see [`resolve_firmware`]).
    ///
    /// # Examples
    ///
    /// ```
    /// use std::path::Path;
    /// use prin_daemon::backend::{VitisAiConfig, DEFAULT_NPU_TARGET};
    ///
    /// let config = VitisAiConfig::from_sdk_root(
    ///     Path::new("C:/Program Files/RyzenAI/1.7.0"),
    ///     Path::new("C:/fw/1x4.xclbin"),
    ///     Path::new("C:/cache"),
    ///     DEFAULT_NPU_TARGET,
    /// );
    /// assert!(config.config_file.ends_with("vaip_config.json"));
    /// ```
    #[must_use]
    pub fn from_sdk_root(sdk_root: &Path, firmware: &Path, cache_dir: &Path, target: &str) -> Self {
        Self {
            config_file: sdk_root.join(VOE_DIR).join("vaip_config.json"),
            xclbin: firmware.to_path_buf(),
            target: target.to_string(),
            cache_dir: cache_dir.to_path_buf(),
            cache_key: DEFAULT_CACHE_KEY.to_string(),
        }
    }

    /// The provider-option key/value pairs, in PRINet 3.0's key order.
    #[must_use]
    pub fn options(&self) -> Vec<(&'static str, String)> {
        vec![
            ("config_file", self.config_file.display().to_string()),
            ("xclbin", self.xclbin.display().to_string()),
            ("target", self.target.clone()),
            ("cache_dir", self.cache_dir.display().to_string()),
            ("cache_key", self.cache_key.clone()),
        ]
    }
}

/// Provider options for every entry of `backend.provider_chain()`.
///
/// The VitisAI entry carries [`VitisAiConfig::options`]; every other provider
/// gets an empty option map, matching PRINet 3.0's `_build_provider_list`.
///
/// # Errors
///
/// Returns [`DaemonError::FirmwareNotFound`] when the NPU backend is requested
/// without a `vitis` configuration — a VitisAI session cannot be configured
/// without firmware and a config file.
pub fn provider_options(
    backend: Backend,
    vitis: Option<&VitisAiConfig>,
) -> Result<Vec<Vec<(&'static str, String)>>, DaemonError> {
    backend
        .provider_chain()
        .iter()
        .map(|provider| match (provider, vitis) {
            (Backend::Npu, Some(config)) => Ok(config.options()),
            (Backend::Npu, None) => Err(DaemonError::FirmwareNotFound {
                searched: Vec::new(),
            }),
            _ => Ok(Vec::new()),
        })
        .collect()
}

/// Candidate `.xclbin` firmware paths, in probe order.
///
/// 1. `env_override` (the `XLNX_VART_FIRMWARE` value), when non-empty;
/// 2. `<sdk_root>/voe-4.0-win_amd64/xclbins/phoenix/<xclbin>`.
///
/// A candidate equal to one already listed is dropped, so an environment
/// override that simply repeats the SDK default yields a single probe rather
/// than a duplicated one. This function is pure — it never touches the
/// filesystem.
///
/// # Examples
///
/// ```
/// use std::path::Path;
/// use prin_daemon::backend::firmware_candidates;
///
/// let candidates = firmware_candidates(Some("  "), Path::new("/sdk"), None);
/// assert_eq!(candidates.len(), 1);
/// assert!(candidates[0].ends_with("1x4.xclbin"));
/// ```
#[must_use]
pub fn firmware_candidates(
    env_override: Option<&str>,
    sdk_root: &Path,
    xclbin: Option<&str>,
) -> Vec<PathBuf> {
    let mut candidates: Vec<PathBuf> = Vec::with_capacity(2);
    if let Some(value) = env_override {
        let trimmed = value.trim();
        if !trimmed.is_empty() {
            candidates.push(PathBuf::from(trimmed));
        }
    }
    let default = sdk_root
        .join(VOE_DIR)
        .join("xclbins")
        .join("phoenix")
        .join(xclbin.unwrap_or(DEFAULT_XCLBIN));
    if !candidates.contains(&default) {
        candidates.push(default);
    }
    candidates
}

/// Resolve the NPU firmware overlay to the first existing candidate path.
///
/// # Errors
///
/// Returns [`DaemonError::FirmwareNotFound`], listing every probed path, when
/// none of the candidates from [`firmware_candidates`] is a file.
pub fn resolve_firmware(
    env_override: Option<&str>,
    sdk_root: &Path,
    xclbin: Option<&str>,
) -> Result<PathBuf, DaemonError> {
    let candidates = firmware_candidates(env_override, sdk_root, xclbin);
    for candidate in &candidates {
        if candidate.is_file() {
            return Ok(candidate.clone());
        }
    }
    Err(DaemonError::FirmwareNotFound {
        searched: candidates.iter().map(|p| p.display().to_string()).collect(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    const ALL: [&str; 3] = [PROVIDER_VITISAI, PROVIDER_DIRECTML, PROVIDER_CPU];
    const DML_CPU: [&str; 2] = [PROVIDER_DIRECTML, PROVIDER_CPU];
    const CPU_ONLY: [&str; 1] = [PROVIDER_CPU];

    #[test]
    fn provider_names_match_onnx_runtime() {
        assert_eq!(Backend::Npu.provider(), "VitisAIExecutionProvider");
        assert_eq!(Backend::DirectMl.provider(), "DmlExecutionProvider");
        assert_eq!(Backend::Cpu.provider(), "CPUExecutionProvider");
    }

    #[test]
    fn short_names_match_reference_backend_type() {
        assert_eq!(Backend::Npu.name(), "npu");
        assert_eq!(Backend::DirectMl.name(), "directml");
        assert_eq!(Backend::Cpu.name(), "cpu");
    }

    #[test]
    fn parse_round_trips_every_backend_case_insensitively() {
        for backend in BACKEND_PRIORITY {
            assert_eq!(Backend::parse(backend.name()).expect("parses"), backend);
            let shouted = backend.name().to_ascii_uppercase();
            assert_eq!(Backend::parse(&shouted).expect("parses"), backend);
            let padded = format!("  {}\t", backend.name());
            assert_eq!(Backend::parse(&padded).expect("parses"), backend);
        }
    }

    #[test]
    fn parse_rejects_unknown_identifiers() {
        let err = Backend::parse("tpu").expect_err("unknown");
        assert!(matches!(err, DaemonError::UnknownBackend { value } if value == "tpu"));
        assert!(Backend::parse("").is_err());
    }

    #[test]
    fn priority_order_is_npu_directml_cpu() {
        assert!(Backend::Npu.priority() < Backend::DirectMl.priority());
        assert!(Backend::DirectMl.priority() < Backend::Cpu.priority());
        assert_eq!(
            BACKEND_PRIORITY,
            [Backend::Npu, Backend::DirectMl, Backend::Cpu]
        );
    }

    #[test]
    fn accelerator_chains_are_cpu_terminated() {
        assert_eq!(
            Backend::Npu.provider_names(),
            vec![PROVIDER_VITISAI, PROVIDER_CPU]
        );
        assert_eq!(
            Backend::DirectMl.provider_names(),
            vec![PROVIDER_DIRECTML, PROVIDER_CPU]
        );
        assert_eq!(Backend::Cpu.provider_names(), vec![PROVIDER_CPU]);
    }

    #[test]
    fn auto_detection_prefers_the_npu() {
        let selection = select_backend(&ALL, None).expect("selects");
        assert_eq!(selection.backend, Backend::Npu);
        assert_eq!(selection.reason, SelectionReason::AutoDetected);
        assert_eq!(
            selection.attempt_order,
            vec![Backend::Npu, Backend::DirectMl, Backend::Cpu]
        );
        assert!(!selection.is_degraded());
    }

    #[test]
    fn auto_detection_falls_back_to_directml_then_cpu() {
        let selection = select_backend(&DML_CPU, None).expect("selects");
        assert_eq!(selection.backend, Backend::DirectMl);
        assert_eq!(
            selection.attempt_order,
            vec![Backend::DirectMl, Backend::Cpu]
        );

        let selection = select_backend(&CPU_ONLY, None).expect("selects");
        assert_eq!(selection.backend, Backend::Cpu);
        assert_eq!(selection.attempt_order, vec![Backend::Cpu]);
    }

    #[test]
    fn an_available_request_is_honoured_even_below_priority() {
        let selection = select_backend(&ALL, Some(Backend::Cpu)).expect("selects");
        assert_eq!(selection.backend, Backend::Cpu);
        assert_eq!(selection.reason, SelectionReason::Requested);
        assert_eq!(selection.requested, Some(Backend::Cpu));
        // A downgrade request must not silently re-ladder upwards.
        assert_eq!(selection.attempt_order, vec![Backend::Cpu]);
    }

    #[test]
    fn an_unavailable_request_degrades_to_priority_order() {
        let selection = select_backend(&DML_CPU, Some(Backend::Npu)).expect("selects");
        assert_eq!(selection.backend, Backend::DirectMl);
        assert_eq!(selection.reason, SelectionReason::RequestedUnavailable);
        assert_eq!(selection.requested, Some(Backend::Npu));
        assert!(selection.is_degraded());
    }

    #[test]
    fn unknown_provider_names_are_ignored() {
        let available = ["TensorrtExecutionProvider", PROVIDER_CPU];
        let selection = select_backend(&available, None).expect("selects");
        assert_eq!(selection.backend, Backend::Cpu);
        assert_eq!(
            selection.available_providers,
            vec![
                "TensorrtExecutionProvider".to_string(),
                PROVIDER_CPU.to_string()
            ]
        );
    }

    #[test]
    fn no_supported_provider_is_a_typed_error() {
        let empty: [&str; 0] = [];
        let err = select_backend(&empty, None).expect_err("no providers");
        assert!(
            matches!(err, DaemonError::NoProviderAvailable { available } if available.is_empty())
        );

        let err = select_backend(&["TensorrtExecutionProvider"], Some(Backend::Cpu))
            .expect_err("no supported providers");
        assert!(matches!(err, DaemonError::NoProviderAvailable { .. }));
    }

    #[test]
    fn selection_accepts_owned_strings() {
        let available = vec![PROVIDER_CPU.to_string()];
        let selection = select_backend(&available, None).expect("selects");
        assert_eq!(selection.backend, Backend::Cpu);
    }

    #[test]
    fn attempt_order_is_strictly_descending_and_cpu_terminated() {
        for requested in [None, Some(Backend::Npu), Some(Backend::DirectMl)] {
            let selection = select_backend(&ALL, requested).expect("selects");
            for pair in selection.attempt_order.windows(2) {
                assert!(pair[0].priority() < pair[1].priority());
            }
            assert_eq!(selection.attempt_order.last(), Some(&Backend::Cpu));
        }
    }

    #[test]
    fn provider_options_pair_with_the_provider_chain() {
        let options = provider_options(Backend::DirectMl, None).expect("options");
        assert_eq!(options.len(), Backend::DirectMl.provider_chain().len());
        assert!(options.iter().all(Vec::is_empty));

        let config = VitisAiConfig::from_sdk_root(
            Path::new("/sdk"),
            Path::new("/fw/1x4.xclbin"),
            Path::new("/cache"),
            DEFAULT_NPU_TARGET,
        );
        let options = provider_options(Backend::Npu, Some(&config)).expect("options");
        assert_eq!(options.len(), 2);
        let keys: Vec<&str> = options[0].iter().map(|(k, _)| *k).collect();
        assert_eq!(
            keys,
            vec!["config_file", "xclbin", "target", "cache_dir", "cache_key"]
        );
        assert_eq!(options[0][2].1, "X1");
        assert_eq!(options[0][4].1, DEFAULT_CACHE_KEY);
        assert!(options[1].is_empty());
    }

    #[test]
    fn npu_options_without_configuration_are_a_typed_error() {
        let err = provider_options(Backend::Npu, None).expect_err("no config");
        assert!(matches!(err, DaemonError::FirmwareNotFound { .. }));
    }

    #[test]
    fn vitis_config_paths_follow_the_sdk_layout() {
        let config = VitisAiConfig::from_sdk_root(
            Path::new("/sdk"),
            Path::new("/fw/1x4.xclbin"),
            Path::new("/cache"),
            "X2",
        );
        assert!(config
            .config_file
            .ends_with(Path::new(VOE_DIR).join("vaip_config.json")));
        assert_eq!(config.target, "X2");
    }

    #[test]
    fn firmware_candidates_prefer_a_non_empty_override() {
        let candidates = firmware_candidates(Some("/explicit.xclbin"), Path::new("/sdk"), None);
        assert_eq!(candidates[0], PathBuf::from("/explicit.xclbin"));
        assert_eq!(candidates.len(), 2);

        let candidates = firmware_candidates(None, Path::new("/sdk"), Some("4x4.xclbin"));
        assert_eq!(candidates.len(), 1);
        assert!(candidates[0].ends_with("4x4.xclbin"));

        // Whitespace-only overrides are discarded, like the reference's
        // `os.environ.get(...).strip()` guard.
        assert_eq!(
            firmware_candidates(Some("   "), Path::new("/sdk"), None).len(),
            1
        );
    }

    #[test]
    fn an_override_equal_to_the_sdk_default_is_not_probed_twice() {
        let default = Path::new("/sdk")
            .join(VOE_DIR)
            .join("xclbins")
            .join("phoenix")
            .join(DEFAULT_XCLBIN);
        let candidates = firmware_candidates(
            Some(&default.display().to_string()),
            Path::new("/sdk"),
            None,
        );
        assert_eq!(candidates, vec![default]);
    }

    #[test]
    fn missing_firmware_reports_every_probed_path() {
        let err = resolve_firmware(
            Some("/definitely/missing.xclbin"),
            Path::new("/definitely/missing/sdk"),
            None,
        )
        .expect_err("missing");
        assert!(matches!(err, DaemonError::FirmwareNotFound { .. }));
        let message = err.to_string();
        assert!(message.contains("missing.xclbin"));
        assert!(message.contains(DEFAULT_XCLBIN));
    }

    #[test]
    fn an_existing_firmware_file_resolves() {
        let dir = tempfile::tempdir().expect("temp dir");
        let firmware = dir.path().join("1x4.xclbin");
        std::fs::write(&firmware, b"overlay").expect("write");
        let resolved = resolve_firmware(
            Some(&firmware.display().to_string()),
            Path::new("/unused"),
            None,
        )
        .expect("resolves");
        assert_eq!(resolved, firmware);
    }

    #[test]
    fn the_sdk_default_path_resolves_when_the_override_is_absent() {
        let dir = tempfile::tempdir().expect("temp dir");
        let phoenix = dir.path().join(VOE_DIR).join("xclbins").join("phoenix");
        std::fs::create_dir_all(&phoenix).expect("mkdir");
        let firmware = phoenix.join(DEFAULT_XCLBIN);
        std::fs::write(&firmware, b"overlay").expect("write");
        let resolved = resolve_firmware(None, dir.path(), None).expect("resolves");
        assert_eq!(resolved, firmware);
    }
}
