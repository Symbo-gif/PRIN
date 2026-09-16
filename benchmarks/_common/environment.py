"""Environment capture for benchmark artefacts.

Implements Benchmarking and Reproducibility Standards §1.4: every benchmark
artefact records PRIN version + git SHA, Rust/Python versions, hardware, OS,
backend, dtype, and seed. Mirrors the environment block already used by
``tools/wp029_control_buffer_pilot.py`` and ``EVIDENCE/0125-wp032-s1-daemon-
latency.json``, extended with the fields this standard additionally requires
(PRIN version, git SHA, Rust version, GPU/VRAM).

This module reads process/platform/subprocess metadata only; it performs no
numerical computation.
"""

from __future__ import annotations

import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(args: list[str]) -> str | None:
    """Run an absolute-path, argument-list subprocess and return stripped stdout.

    Returns ``None`` on any failure (missing executable, non-zero exit,
    timeout) rather than raising, since environment capture must never abort
    a benchmark run.
    """
    try:
        completed = subprocess.run(
            args,
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _git_sha() -> str | None:
    git = _which("git")
    if git is None:
        return None
    return _run([git, "rev-parse", "HEAD"])


def _which(name: str) -> str | None:
    import shutil

    return shutil.which(name)


def _rust_version() -> str | None:
    rustc = _which("rustc")
    if rustc is None:
        return None
    return _run([rustc, "--version"])


def _prin_version() -> str | None:
    """Return the installed PRIN distribution version, or ``None`` if absent.

    The distribution is ``prin-core``, not ``prin``: Project Plan amendment
    #46 moved the published name because PyPI's ``prin`` is owned by an
    unrelated 2015 project, while the ``prin`` import name is unchanged. The
    pre-amendment name is still probed so a benchmark environment installed
    before the rename records a real version rather than silently reporting
    ``None``.
    """
    for distribution_name in ("prin-core", "prin"):
        try:
            return metadata.version(distribution_name)
        except metadata.PackageNotFoundError:
            continue
    return None


def _gpu_info() -> dict[str, Any]:
    """Best-effort NVIDIA GPU name/VRAM via ``nvidia-smi``; absent otherwise."""
    nvidia_smi = _which("nvidia-smi")
    if nvidia_smi is None:
        return {"gpu": None, "vram_mb": None}
    output = _run(
        [
            nvidia_smi,
            "--query-gpu=name,memory.total",
            "--format=csv,noheader,nounits",
        ]
    )
    if not output:
        return {"gpu": None, "vram_mb": None}
    first_line = output.splitlines()[0]
    name, _, mem = first_line.rpartition(",")
    try:
        vram_mb = int(mem.strip())
    except ValueError:
        vram_mb = None
    return {"gpu": name.strip() or None, "vram_mb": vram_mb}


def capture_environment(
    *, backend: str, dtype: str, seed: int | None
) -> dict[str, Any]:
    """Capture the environment fields Benchmarking Standards §1.4 requires.

    Args:
        backend: Compute backend used for the measurement (e.g. ``"cpu"``,
            ``"cuda"``, ``"wgpu"``, ``"host CPU"``).
        dtype: Numeric dtype of the measured quantities (e.g. ``"f64"``).
        seed: Seed value used, or ``None`` for measurements with no
            stochastic component.

    Returns:
        A JSON-serializable dict with PRIN version, git SHA, Rust/Python
        versions, hardware, OS, backend, dtype, and seed.
    """
    gpu = _gpu_info()
    return {
        "prin_version": _prin_version(),
        "git_commit": _git_sha(),
        "rust_version": _rust_version(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpus": _logical_cpus(),
        "gpu": gpu["gpu"],
        "gpu_vram_mb": gpu["vram_mb"],
        "backend": backend,
        "dtype": dtype,
        "seed": seed,
    }


def _logical_cpus() -> int | None:
    import os

    return os.cpu_count()
