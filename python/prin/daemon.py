"""Subconscious controller: ONNX inference and execution-provider selection.

Rebuild of PRINet 3.0 ``prinet.utils.npu_backend`` and the inference half of
``prinet.nn.subconscious_model``. Every numeric transformation and every
selection decision lives in the Rust ``prin-daemon`` crate and is reached
through ``prin._prin_core``; this module contributes only what Rust cannot
reach — the ``onnxruntime`` session object and the environment/filesystem
values that feed the Rust functions (Project Plan §4 design rule 2, "the
Python layer contains no numerics").

The ONNX session is created here rather than in Rust by Project Plan §7 risk
register #4: the VitisAI execution provider ships only inside the Ryzen AI
SDK's custom ONNX Runtime Python wheel and DirectML only as a
platform-specific wheel, so neither is reachable from the ``ort`` crate's
prebuilt binaries.

Environment variables:
    ``PRIN_SUBCONSCIOUS_BACKEND``
        Force a backend: ``npu``, ``directml``, or ``cpu``. An unrecognised
        value is logged and ignored, matching the reference's fail-soft
        behaviour.
    ``RYZEN_AI_INSTALLATION_PATH``
        Root of the Ryzen AI SDK installation. Firmware, VitisAI config, and
        cache directories are derived from it.
    ``XLNX_VART_FIRMWARE``
        Explicit path to the ``.xclbin`` NPU firmware overlay.
    ``PRIN_NPU_TARGET``
        VitisAI compilation target (``X1`` for Phoenix / Hawk Point, ``X2``
        for Strix Point).
    ``PRIN_CONTROLLER_MODEL``
        Explicit path to the controller ``.onnx`` graph, overriding the
        repository default.

Example:
    >>> from prin.daemon import backend_info
    >>> info = backend_info()
    >>> info["best_backend"] in {"npu", "directml", "cpu"}
    True
"""

from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from prin._prin_core import (
    CONTROL_DIM,
    CONTROLLER_INPUT_NAME,
    CONTROLLER_OUTPUT_NAME,
    DEFAULT_NPU_CACHE_KEY,
    DEFAULT_NPU_TARGET,
    DEFAULT_NPU_XCLBIN,
    MODEL_MANIFEST_FILE_NAME,
    STATE_DIM,
    BackendSelection,
    ControlSignals,
    SubconsciousState,
    backend_priority,
    backend_provider_names,
    backend_provider_options,
    inspect_onnx_model,
    model_sha256,
    npu_firmware_candidates,
    resolve_npu_firmware,
    select_execution_backend,
    validate_controller_model,
    verify_model_manifest,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray

logger = logging.getLogger(__name__)

BackendType = Literal["npu", "directml", "cpu"]
"""Execution-provider identifier understood by :func:`create_session`."""

ENV_BACKEND = "PRIN_SUBCONSCIOUS_BACKEND"
"""Environment variable that forces a backend."""

ENV_SDK_ROOT = "RYZEN_AI_INSTALLATION_PATH"
"""Environment variable holding the Ryzen AI SDK installation root."""

ENV_FIRMWARE = "XLNX_VART_FIRMWARE"
"""Environment variable holding an explicit NPU firmware path."""

ENV_NPU_TARGET = "PRIN_NPU_TARGET"
"""Environment variable overriding the VitisAI compilation target."""

ENV_MODEL_PATH = "PRIN_CONTROLLER_MODEL"
"""Environment variable overriding the controller model path."""

DEFAULT_SDK_ROOT = r"C:\Program Files\RyzenAI\1.7.0"
"""Ryzen AI SDK root assumed when :data:`ENV_SDK_ROOT` is unset."""

CONTROLLER_MODEL_NAME = "subconscious_controller.onnx"
"""File name of the committed controller graph inside ``models/``."""

_REPO_MODELS_DIR = Path(__file__).resolve().parents[2] / "models"

__all__: list[str] = [
    "CONTROLLER_INPUT_NAME",
    "CONTROLLER_MODEL_NAME",
    "CONTROLLER_OUTPUT_NAME",
    "CONTROL_DIM",
    "DEFAULT_NPU_CACHE_KEY",
    "DEFAULT_NPU_TARGET",
    "DEFAULT_NPU_XCLBIN",
    "DEFAULT_SDK_ROOT",
    "ENV_BACKEND",
    "ENV_FIRMWARE",
    "ENV_MODEL_PATH",
    "ENV_NPU_TARGET",
    "ENV_SDK_ROOT",
    "MODEL_MANIFEST_FILE_NAME",
    "STATE_DIM",
    "BackendSelection",
    "BackendType",
    "ControlSignals",
    "OrtUnavailableError",
    "SubconsciousController",
    "SubconsciousState",
    "available_providers",
    "backend_info",
    "backend_priority",
    "backend_provider_names",
    "backend_provider_options",
    "create_session",
    "default_model_path",
    "default_models_dir",
    "detect_best_backend",
    "directml_available",
    "inspect_onnx_model",
    "model_sha256",
    "npu_available",
    "npu_firmware_candidates",
    "resolve_npu_firmware",
    "select_backend",
    "validate_controller_model",
    "verify_model_artefacts",
    "verify_model_manifest",
]


class OrtUnavailableError(RuntimeError):
    """Raised when ONNX Runtime is needed but cannot be imported."""


def _import_ort() -> Any:
    """Import ``onnxruntime`` or raise a clear, actionable error.

    Returns:
        The imported ``onnxruntime`` module.

    Raises:
        OrtUnavailableError: If ``onnxruntime`` is not installed.
    """
    try:
        return importlib.import_module("onnxruntime")
    except ModuleNotFoundError as exc:
        msg = (
            "onnxruntime is required for the subconscious controller; "
            'install the "onnx" extra: pip install "prin[onnx]"'
        )
        raise OrtUnavailableError(msg) from exc


def available_providers() -> list[str]:
    """Return the execution providers registered with ONNX Runtime.

    Returns:
        Provider names in the order ONNX Runtime reports them, or an empty
        list when ONNX Runtime is absent or cannot be queried.
    """
    try:
        ort = _import_ort()
    except OrtUnavailableError:
        return []
    try:
        return list(ort.get_available_providers())
    except (AttributeError, RuntimeError):  # pragma: no cover - defensive
        logger.warning("onnxruntime failed to report its execution providers")
        return []


def _env_backend() -> str | None:
    """Return the backend requested through :data:`ENV_BACKEND`, if valid."""
    raw = os.environ.get(ENV_BACKEND, "").strip().lower()
    if not raw:
        return None
    if raw not in set(backend_priority()):
        logger.warning("ignoring unrecognised %s value %r", ENV_BACKEND, raw)
        return None
    return raw


def select_backend(
    available: Sequence[str] | None = None,
    requested: str | None = None,
) -> BackendSelection:
    """Rank the available execution providers and build the fallback ladder.

    Args:
        available: Provider names to choose from. ``None`` queries ONNX
            Runtime via :func:`available_providers`.
        requested: Backend to prefer (``npu``, ``directml``, or ``cpu``).
            ``None`` consults :data:`ENV_BACKEND` and otherwise auto-detects.

    Returns:
        A ``BackendSelection`` naming the chosen backend, why it was chosen,
        and the ordered list of backends to try.

    Raises:
        ValueError: If ``requested`` is not a known backend, or if no
            supported execution provider is available.
    """
    providers = list(available) if available is not None else available_providers()
    return select_execution_backend(providers, requested or _env_backend())


def detect_best_backend(
    available: Sequence[str] | None = None,
    requested: str | None = None,
) -> BackendType:
    """Auto-detect the most capable execution provider.

    Detection order is :data:`ENV_BACKEND`, then VitisAI (NPU), then DirectML,
    then CPU — the priority PRINet 3.0's ``detect_best_backend`` uses.

    Args:
        available: Provider names to choose from, or ``None`` to query ONNX
            Runtime.
        requested: Explicit backend request, or ``None``.

    Returns:
        The selected backend identifier.

    Raises:
        ValueError: If no supported execution provider is available.
    """
    backend: BackendType = select_backend(available, requested).backend
    return backend


def npu_available(available: Sequence[str] | None = None) -> bool:
    """Whether the VitisAI (NPU) execution provider is registered.

    Args:
        available: Provider names to inspect, or ``None`` to query ONNX
            Runtime.

    Returns:
        ``True`` if ``VitisAIExecutionProvider`` is present.
    """
    providers = list(available) if available is not None else available_providers()
    return backend_provider_names("npu")[0] in providers


def directml_available(available: Sequence[str] | None = None) -> bool:
    """Whether the DirectML execution provider is registered.

    Args:
        available: Provider names to inspect, or ``None`` to query ONNX
            Runtime.

    Returns:
        ``True`` if ``DmlExecutionProvider`` is present.
    """
    providers = list(available) if available is not None else available_providers()
    return backend_provider_names("directml")[0] in providers


def default_models_dir() -> Path:
    """Return the directory holding the committed model artefacts.

    Returns:
        The repository's ``models/`` directory. Installed wheels do not ship
        model artefacts, so callers outside a source checkout should pass an
        explicit path instead.
    """
    return _REPO_MODELS_DIR


def default_model_path() -> Path:
    """Return the controller graph path.

    Returns:
        :data:`ENV_MODEL_PATH` when set, otherwise
        ``<repo>/models/subconscious_controller.onnx``.
    """
    override = os.environ.get(ENV_MODEL_PATH, "").strip()
    if override:
        return Path(override)
    return default_models_dir() / CONTROLLER_MODEL_NAME


def verify_model_artefacts(
    models_dir: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Verify every model artefact against the committed SHA-256 manifest.

    Args:
        models_dir: Directory containing ``manifest.json``. ``None`` uses
            :func:`default_models_dir`.

    Returns:
        One record per covered file, with its absolute ``path``, ``sha256``,
        and ``bytes``.

    Raises:
        ValueError: If a digest or size does not match the manifest.
        OSError: If the manifest or a covered file cannot be read.
    """
    root = Path(models_dir) if models_dir is not None else default_models_dir()
    records: list[dict[str, Any]] = verify_model_manifest(root)
    return records


def _sdk_root() -> Path:
    """Return the Ryzen AI SDK root from the environment, or the default."""
    return Path(os.environ.get(ENV_SDK_ROOT, "").strip() or DEFAULT_SDK_ROOT)


def _npu_cache_dir() -> Path:
    """Return the VitisAI compilation-cache directory."""
    base = os.environ.get("LOCALAPPDATA", "").strip() or str(Path.home())
    return Path(base) / "prin" / "vitisai_cache"


def _vitisai_options() -> list[dict[str, str]]:
    """Build VitisAI provider options from the environment.

    Returns:
        One option dict per provider in the NPU chain.

    Raises:
        ValueError: If the NPU firmware overlay cannot be located.
    """
    sdk_root = _sdk_root()
    firmware = resolve_npu_firmware(
        os.environ.get(ENV_FIRMWARE),
        sdk_root,
        DEFAULT_NPU_XCLBIN,
    )
    cache_dir = _npu_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    options: list[dict[str, str]] = backend_provider_options(
        "npu",
        sdk_root,
        firmware,
        cache_dir,
        os.environ.get(ENV_NPU_TARGET, "").strip() or DEFAULT_NPU_TARGET,
    )
    return options


def _provider_config(backend: str) -> tuple[list[str], list[dict[str, str]]]:
    """Return ``(providers, provider_options)`` for one session attempt.

    Args:
        backend: Backend identifier.

    Returns:
        The ORT provider names and their matching option dicts.

    Raises:
        ValueError: If ``backend`` is unknown, or if the NPU firmware is
            missing when ``backend`` is ``"npu"``.
    """
    providers = list(backend_provider_names(backend))
    if backend == "npu":
        return providers, _vitisai_options()
    options: list[dict[str, str]] = backend_provider_options(backend)
    return providers, options


def _session_options(ort: Any, inter_op_threads: int, intra_op_threads: int) -> Any:
    """Build ONNX Runtime session options matching the reference defaults."""
    opts = ort.SessionOptions()
    opts.inter_op_num_threads = inter_op_threads
    opts.intra_op_num_threads = intra_op_threads
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return opts


def create_session(
    model_path: Path | str,
    backend: str | None = None,
    *,
    available: Sequence[str] | None = None,
    inter_op_threads: int = 1,
    intra_op_threads: int = 2,
) -> tuple[Any, BackendType, list[str]]:
    """Create an ONNX Runtime session, walking the deterministic fallback ladder.

    Each backend in ``BackendSelection.attempt_order`` is tried in turn; the
    first that yields a session wins. Because the ladder is computed in Rust
    from the provider list alone, it is strictly descending and — whenever the
    CPU provider is registered — always terminates at CPU, so a missing
    accelerator degrades predictably instead of raising.

    Args:
        model_path: Path to the ``.onnx`` graph.
        backend: Backend to prefer, or ``None`` to auto-detect.
        available: Provider names to choose from, or ``None`` to query ONNX
            Runtime.
        inter_op_threads: Inter-op parallelism threads.
        intra_op_threads: Intra-op parallelism threads.

    Returns:
        ``(session, backend, active_providers)`` — the session, the backend it
        was created on, and the providers ONNX Runtime actually activated.

    Raises:
        OrtUnavailableError: If ``onnxruntime`` is not installed.
        FileNotFoundError: If ``model_path`` does not exist.
        ValueError: If no supported execution provider is available.
        RuntimeError: If every backend on the ladder failed.
    """
    ort = _import_ort()
    path = Path(model_path)
    if not path.is_file():
        msg = f"ONNX model not found: {path}"
        raise FileNotFoundError(msg)

    selection = select_backend(available, backend)
    opts = _session_options(ort, inter_op_threads, intra_op_threads)

    failures: list[str] = []
    for candidate in selection.attempt_order:
        try:
            providers, provider_options = _provider_config(candidate)
            session = ort.InferenceSession(
                str(path),
                sess_options=opts,
                providers=providers,
                provider_options=provider_options,
            )
        except Exception as exc:
            # ONNX Runtime raises provider-specific exception types that all
            # derive straight from `Exception` with no common base
            # (`InvalidGraph`, `Fail`, `EPFail`, ...), and a native execution
            # provider can fail in ways no narrower clause would catch. A
            # broad clause is what makes the fallback deterministic; it is
            # bounded to session construction, every failure is recorded and
            # logged, and `BaseException` (KeyboardInterrupt, SystemExit) is
            # deliberately not caught.
            failures.append(f"{candidate}: {exc}")
            logger.info("backend %s unavailable for %s: %s", candidate, path.name, exc)
            continue
        active = list(session.get_providers())
        logger.info(
            "created ONNX session: model=%s backend=%s providers=%s",
            path.name,
            candidate,
            active,
        )
        resolved: BackendType = candidate
        return session, resolved, active

    msg = (
        f"could not create an ONNX Runtime session for {path} on any of "
        f"{list(selection.attempt_order)}: " + "; ".join(failures)
    )
    raise RuntimeError(msg)


def backend_info() -> dict[str, Any]:
    """Summarise the current backend configuration for telemetry and reports.

    Returns:
        A dictionary with the ONNX Runtime availability and version, the
        registered providers, the selected backend and its fallback ladder,
        and the resolved NPU firmware/SDK/cache configuration. Nothing in this
        function raises: unavailable pieces are reported as ``None`` or
        ``False`` so that it is always safe to embed in a report.
    """
    providers = available_providers()
    ort_version: str | None = None
    try:
        ort_version = str(getattr(_import_ort(), "__version__", "unknown"))
    except OrtUnavailableError:
        ort_version = None

    backend: str | None = None
    attempt_order: list[str] = []
    reason: str | None = None
    try:
        selection = select_backend(providers)
        backend = selection.backend
        attempt_order = list(selection.attempt_order)
        reason = selection.reason
    except ValueError:
        logger.info("no supported ONNX Runtime execution provider is available")

    firmware: str | None = None
    try:
        firmware = resolve_npu_firmware(
            os.environ.get(ENV_FIRMWARE),
            _sdk_root(),
            DEFAULT_NPU_XCLBIN,
        )
    except ValueError:
        firmware = None

    return {
        "ort_available": ort_version is not None,
        "ort_version": ort_version,
        "available_providers": providers,
        "best_backend": backend,
        "selection_reason": reason,
        "attempt_order": attempt_order,
        "npu_available": npu_available(providers),
        "directml_available": directml_available(providers),
        "npu_firmware_found": firmware is not None,
        "npu_firmware_path": firmware,
        "npu_firmware_candidates": npu_firmware_candidates(
            os.environ.get(ENV_FIRMWARE),
            _sdk_root(),
            DEFAULT_NPU_XCLBIN,
        ),
        "sdk_install_dir": str(_sdk_root()),
        "npu_target": os.environ.get(ENV_NPU_TARGET, "").strip() or DEFAULT_NPU_TARGET,
        "cache_dir": str(_npu_cache_dir()),
    }


class SubconsciousController:
    """ONNX-backed subconscious controller: system state to control signals.

    The controller validates its model before loading it — SHA-256 integrity,
    external-data completeness, and the ``state_vector``/``control_signals``
    graph contract — then creates a session on the best available execution
    provider, falling back deterministically when an accelerator cannot take
    the graph.

    The PyTorch-side training, ONNX export, and INT8 quantisation half of
    PRINet 3.0's ``SubconsciousController`` is **not** part of this class: it
    is WP-030 scope (training hooks). WP-028 delivers the inference path.

    Args:
        model_path: Path to the ``.onnx`` graph. ``None`` uses
            :func:`default_model_path`.
        backend: Backend to prefer, or ``None`` to auto-detect.
        expected_sha256: Digest the model must hash to. ``None`` looks the
            digest up in the model directory's manifest when one is present,
            and otherwise skips the integrity check.
        inter_op_threads: Inter-op parallelism threads.
        intra_op_threads: Intra-op parallelism threads.

    Raises:
        OrtUnavailableError: If ``onnxruntime`` is not installed.
        FileNotFoundError: If the model file does not exist.
        ValueError: If the model fails integrity or contract validation, or if
            no supported execution provider is available.
        RuntimeError: If no session could be created on any backend.

    Example:
        >>> from prin.daemon import SubconsciousController, SubconsciousState
        >>> controller = SubconsciousController()  # doctest: +SKIP
        >>> control = controller.predict(SubconsciousState())  # doctest: +SKIP
        >>> control.preferred_regime  # doctest: +SKIP
        'full'
    """

    def __init__(
        self,
        model_path: Path | str | None = None,
        backend: str | None = None,
        *,
        expected_sha256: str | None = None,
        inter_op_threads: int = 1,
        intra_op_threads: int = 2,
    ) -> None:
        """Validate the model, then open a session on the best backend."""
        path = Path(model_path) if model_path is not None else default_model_path()
        digest = expected_sha256 or _manifest_digest(path)
        self._validation: dict[str, Any] = validate_controller_model(path, digest)
        self._path = path
        session, resolved, active = create_session(
            path,
            backend,
            inter_op_threads=inter_op_threads,
            intra_op_threads=intra_op_threads,
        )
        self._session = session
        self._backend: BackendType = resolved
        self._active_providers = active

    @property
    def model_path(self) -> Path:
        """Path to the validated ONNX graph."""
        return self._path

    @property
    def sha256(self) -> str:
        """SHA-256 digest of the validated ONNX graph."""
        digest: str = self._validation["sha256"]
        return digest

    @property
    def graph(self) -> dict[str, Any]:
        """Decoded graph metadata: opsets, inputs, outputs, initializers."""
        info: dict[str, Any] = self._validation["info"]
        return info

    @property
    def backend(self) -> BackendType:
        """Backend the session was created on."""
        return self._backend

    @property
    def active_providers(self) -> list[str]:
        """Execution providers ONNX Runtime actually activated."""
        return list(self._active_providers)

    def run(self, batch: NDArray[np.float32]) -> NDArray[np.float32]:
        """Run the raw controller graph on a batch of state vectors.

        Args:
            batch: Array of shape ``(B, STATE_DIM)``. Any float dtype is
                accepted and narrowed to ``float32``.

        Returns:
            Array of shape ``(B, CONTROL_DIM)`` with ``dtype=float32``.

        Raises:
            ValueError: If ``batch`` is not two-dimensional or its trailing
                dimension is not :data:`STATE_DIM`.
        """
        array = np.asarray(batch, dtype=np.float32)
        if array.ndim != 2 or array.shape[1] != STATE_DIM:
            msg = (
                f"state batch must have shape (B, {STATE_DIM}), "
                f"got {tuple(array.shape)}"
            )
            raise ValueError(msg)
        outputs = self._session.run(None, {CONTROLLER_INPUT_NAME: array})
        result: NDArray[np.float32] = np.asarray(outputs[0], dtype=np.float32)
        return result

    def predict(self, state: SubconsciousState) -> ControlSignals:
        """Map one system snapshot to control signals.

        Args:
            state: The system snapshot to encode and evaluate.

        Returns:
            The decoded and clamped control signals.
        """
        return self.predict_batch([state])[0]

    def predict_batch(
        self, states: Sequence[SubconsciousState]
    ) -> list[ControlSignals]:
        """Map several system snapshots to control signals in one session call.

        ONNX Runtime selects its float32 GEMM path partly by batch size, so a
        single-row batch can differ from the same row inside a larger batch by
        roughly one float32 ULP (measured on this graph: max absolute
        difference 1.19e-7, max relative 1.56e-7; batch sizes of two and above
        agree bit-for-bit). Callers comparing single and batched results should
        use a tolerance of ``rtol=1e-6, atol=1e-7`` rather than equality.

        Args:
            states: Snapshots to evaluate. Must be non-empty.

        Returns:
            One ``ControlSignals`` per input snapshot, in the same order.

        Raises:
            ValueError: If ``states`` is empty.
        """
        if len(states) == 0:
            msg = "states must contain at least one snapshot"
            raise ValueError(msg)
        batch = np.stack([state.to_tensor() for state in states]).astype(np.float32)
        raw = self.run(batch)
        return [
            ControlSignals.from_tensor(np.asarray(row, dtype=np.float64)) for row in raw
        ]

    def close(self) -> None:
        """Release the underlying ONNX Runtime session."""
        self._session = None

    def __repr__(self) -> str:
        """Return a concise, provider-aware representation."""
        return (
            f"SubconsciousController(model={self._path.name!r}, "
            f"backend={self._backend!r}, providers={self._active_providers})"
        )


def _manifest_digest(model_path: Path) -> str | None:
    """Look up ``model_path``'s digest in its directory's manifest.

    Args:
        model_path: Path to the model whose digest is wanted.

    Returns:
        The recorded digest, or ``None`` when no manifest covers the file.
    """
    manifest_path = model_path.parent / MODEL_MANIFEST_FILE_NAME
    if not manifest_path.is_file():
        return None
    try:
        records = verify_model_manifest(model_path.parent)
    except (OSError, ValueError):
        logger.warning("model manifest verification failed for %s", manifest_path)
        raise
    for record in records:
        if Path(record["path"]).name == model_path.name:
            digest: str = record["sha256"]
            return digest
    return None
