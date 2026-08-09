"""ONNX Runtime execution-provider probe for the PRIN subconscious controller.

This is a Phase 0 spike: it detects available ONNX Runtime execution providers,
builds a provider list in the priority order VitisAI -> DirectML -> CPU, and
proves that the pre-trained subconscious controller model loads and runs with a
graceful fallback to CPU when an accelerator provider cannot execute the graph.

The full daemon runtime, NPU SDK configuration, and backend contracts are owned
by WP-028.
"""

from __future__ import annotations

import hashlib
import importlib
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from collections.abc import Sequence

Backend = Literal["npu", "directml", "cpu"]
"""Execution-provider identifier for the controller."""

_PROVIDER_NAMES: dict[Backend, str] = {
    "npu": "VitisAIExecutionProvider",
    "directml": "DmlExecutionProvider",
    "cpu": "CPUExecutionProvider",
}

_RYZEN_AI_INSTALL_DIR: str = os.environ.get(
    "RYZEN_AI_INSTALLATION_PATH",
    r"C:\Program Files\RyzenAI\1.7.0",
)
_VOE_DIR: Path = Path(_RYZEN_AI_INSTALL_DIR) / "voe-4.0-win_amd64"
_DEFAULT_XCLBIN_DIR: Path = _VOE_DIR / "xclbins" / "phoenix"
_DEFAULT_XCLBIN: str = "1x4.xclbin"
_VITISAI_CONFIG_FILE: Path = _VOE_DIR / "vaip_config.json"
_DEFAULT_TARGET: str = os.environ.get("PRIN_NPU_TARGET", "X1")
_CACHE_DIR: Path = (
    Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "prin" / "vitisai_cache"
)

__all__: list[str] = [
    "Backend",
    "OrtProbeError",
    "OrtProbeReport",
    "available_providers",
    "build_provider_list",
    "probe_model",
    "select_best_backend",
    "try_create_session",
]


class OrtProbeError(Exception):
    """Raised when an ONNX Runtime probe cannot be completed."""


@dataclass(frozen=True)
class OrtProbeReport:
    """Evidence record from an ONNX Runtime provider probe."""

    model_path: str
    model_sha256: str
    available_providers: list[str]
    selected_backend: Backend
    active_providers: list[str]
    input_metadata: list[dict[str, Any]]
    output_metadata: list[dict[str, Any]]
    can_run: bool
    output_shape: tuple[int, ...] | None
    error: str | None
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report to a JSON-compatible dictionary."""
        return {
            "model_path": self.model_path,
            "model_sha256": self.model_sha256,
            "available_providers": self.available_providers,
            "selected_backend": self.selected_backend,
            "active_providers": self.active_providers,
            "input_metadata": self.input_metadata,
            "output_metadata": self.output_metadata,
            "can_run": self.can_run,
            "output_shape": list(self.output_shape) if self.output_shape else None,
            "error": self.error,
            "timestamp": self.timestamp,
        }


def _import_ort() -> Any:
    """Return the ``onnxruntime`` module or raise a clear error."""
    try:
        return importlib.import_module("onnxruntime")
    except ModuleNotFoundError as exc:
        raise OrtProbeError(
            "onnxruntime is not installed; install the 'onnx' extra"
        ) from exc


def _resolve_firmware_path(
    xclbin_dir: Path | None = None,
    xclbin: str | None = None,
) -> Path:
    """Resolve the VitisAI NPU firmware binary path.

    Resolution order:

    1. ``XLNX_VART_FIRMWARE`` environment variable.
    2. ``xclbin_dir / xclbin`` (defaults to the Ryzen AI SDK installation).

    Args:
        xclbin_dir: Optional directory to search for the xclbin.
        xclbin: Optional xclbin file name.

    Returns:
        Absolute path to the ``.xclbin`` firmware file.

    Raises:
        FileNotFoundError: If no firmware file can be located.
    """
    env_fw = os.environ.get("XLNX_VART_FIRMWARE", "").strip()
    if env_fw:
        path = Path(env_fw)
        if path.is_file():
            return path.resolve()

    default_dir = xclbin_dir or _DEFAULT_XCLBIN_DIR
    default = default_dir / (xclbin or _DEFAULT_XCLBIN)
    if default.is_file():
        return default.resolve()

    msg = (
        "NPU firmware not found. Set XLNX_VART_FIRMWARE to the path "
        f"of a valid .xclbin file, or ensure the Ryzen AI SDK is installed "
        f"at {_RYZEN_AI_INSTALL_DIR}."
    )
    raise FileNotFoundError(msg)


def _hash_file(path: Path) -> str:
    """Return the SHA-256 hex digest of ``path``."""
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _np_dtype_for_ort_type(ort_type: str) -> str:
    """Map an ONNX Runtime tensor type string to a NumPy dtype name."""
    mapping = {
        "tensor(float)": "float32",
        "tensor(double)": "float64",
        "tensor(int32)": "int32",
        "tensor(int64)": "int64",
        "tensor(uint8)": "uint8",
        "tensor(bool)": "bool_",
    }
    return mapping.get(ort_type, "float32")


def available_providers() -> list[str]:
    """Return the execution providers registered with ONNX Runtime.

    Returns an empty list when ONNX Runtime is not installed or cannot be
    queried.
    """
    try:
        ort = _import_ort()
    except OrtProbeError:
        return []
    try:
        return list(ort.get_available_providers())
    except Exception:
        return []


def select_best_backend(
    providers: Sequence[str],
    override: str | None = None,
) -> Backend:
    """Auto-detect the most capable backend from ``providers``.

    Priority: ``npu`` (VitisAI) -> ``directml`` -> ``cpu``.

    An explicit ``override`` (or the ``PRIN_SUBCONSCIOUS_BACKEND`` environment
    variable) can force one of ``"npu"``, ``"directml"``, or ``"cpu"``. If the
    requested provider is not listed, normal priority is used.

    Args:
        providers: List of available execution-provider names.
        override: Optional backend name to force.

    Returns:
        The best available backend.

    Raises:
        OrtProbeError: If no supported provider is available.
    """
    env_override = os.environ.get("PRIN_SUBCONSCIOUS_BACKEND", "").strip().lower()
    chosen = (override or "").strip().lower() or env_override
    if chosen in _PROVIDER_NAMES:
        backend = chosen
        if _PROVIDER_NAMES[backend] in providers:
            return backend

    for backend in ("npu", "directml", "cpu"):
        if _PROVIDER_NAMES[backend] in providers:
            return backend

    raise OrtProbeError(f"no supported execution provider found in {list(providers)}")


def build_provider_list(
    backend: Backend,
) -> tuple[list[str], list[dict[str, Any]]]:
    """Build ORT ``providers`` and ``provider_options`` for ``backend``.

    Args:
        backend: Target backend.

    Returns:
        ``(providers, provider_options)`` ready for
        :class:`onnxruntime.InferenceSession`.

    Raises:
        FileNotFoundError: For the ``npu`` backend if required firmware or
            configuration files cannot be found.
    """
    if backend == "npu":
        firmware = _resolve_firmware_path()
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return (
            [_PROVIDER_NAMES["npu"], _PROVIDER_NAMES["cpu"]],
            [
                {
                    "config_file": str(_VITISAI_CONFIG_FILE),
                    "xclbin": str(firmware),
                    "target": _DEFAULT_TARGET,
                    "cache_dir": str(_CACHE_DIR),
                    "cache_key": "subconscious_v1",
                },
                {},
            ],
        )
    if backend == "directml":
        return (
            [_PROVIDER_NAMES["directml"], _PROVIDER_NAMES["cpu"]],
            [{}, {}],
        )
    return ([_PROVIDER_NAMES["cpu"]], [{}])


def try_create_session(
    model_path: Path | str,
    backend: Backend | None = None,
) -> tuple[Any, list[str]]:
    """Create an ONNX Runtime session, falling back to CPU if needed.

    If the preferred provider list fails (e.g., DirectML cannot execute the
    graph, or VitisAI firmware is missing), the function retries with the CPU
    execution provider when available.

    Args:
        model_path: Path to the ``.onnx`` model file.
        backend: Optional backend to target. ``None`` selects the best provider.

    Returns:
        A ready-to-use session and the list of active providers.

    Raises:
        FileNotFoundError: If ``model_path`` does not exist.
        OrtProbeError: If no session can be created.
    """
    ort = _import_ort()
    model_path = Path(model_path)
    if not model_path.is_file():
        raise FileNotFoundError(f"ONNX model not found: {model_path}")

    providers = available_providers()
    if not providers:
        raise OrtProbeError("no ONNX Runtime execution providers are available")

    try:
        if backend is None:
            backend = select_best_backend(providers)

        preferred, options = build_provider_list(backend)
        session = ort.InferenceSession(
            str(model_path),
            providers=preferred,
            provider_options=options,
        )
    except Exception as exc:
        if _PROVIDER_NAMES["cpu"] not in providers:
            raise OrtProbeError(
                f"failed to create ONNX Runtime session: {exc}"
            ) from exc
        session = ort.InferenceSession(
            str(model_path),
            providers=[_PROVIDER_NAMES["cpu"]],
            provider_options=[{}],
        )

    return session, list(session.get_providers())


def probe_model(model_path: Path | str) -> OrtProbeReport:
    """Probe ONNX Runtime providers for ``model_path``.

    The function builds a report that records which providers are available,
    which backend was selected, whether a session could be created, and the
    shape of the output from a single dummy-input forward pass.

    Args:
        model_path: Path to the ``.onnx`` model file.

    Returns:
        An :class:`OrtProbeReport` with the probe evidence.

    Raises:
        FileNotFoundError: If ``model_path`` does not exist.
    """
    model_path = Path(model_path).resolve()
    if not model_path.is_file():
        raise FileNotFoundError(f"ONNX model not found: {model_path}")

    model_sha256 = _hash_file(model_path)
    providers = available_providers()
    timestamp = datetime.now(UTC).isoformat()

    if not providers:
        return OrtProbeReport(
            model_path=str(model_path),
            model_sha256=model_sha256,
            available_providers=[],
            selected_backend="cpu",
            active_providers=[],
            input_metadata=[],
            output_metadata=[],
            can_run=False,
            output_shape=None,
            error="onnxruntime is not installed or no providers are available",
            timestamp=timestamp,
        )

    backend: Backend = "cpu"
    try:
        backend = select_best_backend(providers)
        session, active = try_create_session(model_path, backend)
    except Exception as exc:
        return OrtProbeReport(
            model_path=str(model_path),
            model_sha256=model_sha256,
            available_providers=providers,
            selected_backend=backend,
            active_providers=[],
            input_metadata=[],
            output_metadata=[],
            can_run=False,
            output_shape=None,
            error=f"failed to create session: {exc}",
            timestamp=timestamp,
        )

    input_metadata = [
        {"name": inp.name, "shape": list(inp.shape), "type": inp.type}
        for inp in session.get_inputs()
    ]
    output_metadata = [
        {"name": out.name, "shape": list(out.shape), "type": out.type}
        for out in session.get_outputs()
    ]

    try:
        np = importlib.import_module("numpy")
        feed: dict[str, Any] = {}
        for inp in session.get_inputs():
            shape = [1 if isinstance(dim, str) else dim for dim in inp.shape]
            feed[inp.name] = np.zeros(
                shape,
                dtype=_np_dtype_for_ort_type(inp.type),
            )
        results = session.run(None, feed)
        output_shape = tuple(results[0].shape) if results else None
        can_run = True
        error = None
    except Exception as exc:
        output_shape = None
        can_run = False
        error = f"inference failed: {exc}"

    return OrtProbeReport(
        model_path=str(model_path),
        model_sha256=model_sha256,
        available_providers=providers,
        selected_backend=backend,
        active_providers=active,
        input_metadata=input_metadata,
        output_metadata=output_metadata,
        can_run=can_run,
        output_shape=output_shape,
        error=error,
        timestamp=timestamp,
    )
