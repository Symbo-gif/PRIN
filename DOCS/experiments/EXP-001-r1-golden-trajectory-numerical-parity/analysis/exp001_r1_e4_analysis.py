#!/usr/bin/env python
"""Registered E4 analysis for EXP-001-r1 — golden-trajectory numerical parity.

This module is the committed analysis code campaign plan §7.4 item 2 requires
("Analysis code ... committed under the experiment's record root"). It applies
the **frozen** pre-registration §8 decision rule to the six immutable E3 run
artefacts and regenerates every E4 output deterministically. The predecessor's
``EXP-001/analysis/exp001_e4_analysis.py`` is pinned to its own four original
runs and is neither imported nor retargeted here (pre-registration §8
preamble).

What it does, in the order §8 lists it:

1. **Input admissibility (§8 rule 1).** Reads only the explicit six-entry E3
   run index in :data:`RUN_LEGS` — never a ``RUN-*`` glob. For each leg it
   runs ``tools.reproduce.verify_manifest``, re-reads the result artefact
   through ``read_verified_no_follow`` so the bytes adjudicated are provably
   the bytes manifested, then verifies the campaign sidecar, the result
   envelope (``environment``/``config``), the recorded execution SHA ``R``,
   the protocol revision, the seed pair, the backend/dtype and label pairing,
   the E3 build-log extension hash for that leg, every registered input
   fingerprint, and the leg's complete case inventory and its uniqueness.
   Run-directory *names* are enumerated once, purely to prove §8's "six
   distinct r1 run IDs overall"; no input is ever selected that way.
2. **Re-evaluation from retained records (§8 rule 2).** Every native,
   corrected and reference-sensitivity decision is recomputed from the stored
   per-array comparison records and required to agree with the stored
   classification. H2b's registered per-case paired summaries are recomputed
   from the stored paired metric arrays before the committed statistical
   helper is applied. No trajectory is re-run and no kernel is dispatched.
3. **Adjudication (§8 rules 3 to 7).** H1, H2a, H2b, H3 and H4 are decided by
   the registered rules only. H2b is delegated verbatim to
   :func:`benchmarks.campaign.exp001_r1_driver.adjudicate_h2b`, the single
   committed implementation of the registered three-way equivalence predicate;
   this module never re-implements it.
4. **Outputs (§8's fixed output table).** ``summary.json``, ``summary.md``,
   ``case-comparisons.json`` and ``error-distributions.json`` under the
   gitignored ``DOCS/test_and_benchmark_results/EXP-001-r1/``, plus a SHA-256
   ``report-manifest.json`` committed to the record root (campaign plan §7.4
   item 4).

**A valid breach is escalated, never rescued.** Any ``REFUTED`` verdict is a
campaign plan §10.4 D1 (pre-registration §4.1); :func:`is_d1` reports it and
every output records it. No tolerance, denominator, decision rule or case
population is adjusted here, and no statistic is introduced beyond H2b's
registered bootstrap inside the driver (campaign plan §9.2).

**H4 is verified, not re-measured.** The E3 driver retained per-case
comparator records (``within_tolerance``, ``failed_count``, error maxima) and
per-case backend proofs (``dlpack_devices``, plus ``backend_name`` for wgpu) —
not the raw float32 derivative arrays. §8 rule 7 forbids claiming an
independent numerical ``isclose`` re-evaluation from absent raw arrays, so
this module checks each retained comparator record for *internal consistency*
against the registered ``rtol=1e-5, atol=1e-6`` rule — necessary conditions
only: ``within_tolerance == (failed_count == 0)``, a breach implies
``max_abs_diff > atol``, element counts match the case's shape — and verifies
the backend proofs. It never asserts that it recomputed ``numpy.isclose``.

**Single implementations.** The registered predicates this analysis depends on
are imported, not restated: H2b's adjudicator, the fixed 22-case sensitivity
index set, the 14 repeatability representatives, the DV-007 path predicate,
the fuzz sampler and its stream digest, the kernel tolerance, the horizon and
the H2b statistical configuration all come from
``benchmarks.campaign.exp001_r1_driver`` and ``benchmarks.campaign.exp001_driver``
(the latter's module-private names included, exactly as the r1 driver itself
already consumes them, so exactly one implementation of each rule exists).
The tolerances come from ``prin.parity.schema``.

**Determinism.** No wall clock is read: ``generated_at`` is an explicit input
defaulting to :data:`GENERATED_AT`. No randomness is drawn here; the only
resampling anywhere in the analysis is H2b's registered bootstrap, seeded
inside the driver. JSON is emitted with sorted keys, ``allow_nan=False`` and
LF newlines; Markdown rows are emitted in a fixed order; every number goes
through :func:`_render`. Re-running on a clean checkout from the same fixed
input index reproduces each output byte for byte (campaign plan §7.4 step 5).

Usage:
    Run it from the repository root, giving the path to this file. The record
    root's ``analysis.md`` quotes the exact command and the expected output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict, dataclass
from math import floor, isfinite, log10
from pathlib import Path
from typing import Any

import numpy as np

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from prin.parity.loader import CorpusLoader  # noqa: E402
from prin.parity.schema import (  # noqa: E402
    METRIC_ATOL,
    METRIC_RTOL,
    TRAJECTORY_ATOL,
    TRAJECTORY_RTOL,
)
from prin.reporting import generate_benchmark_report  # noqa: E402

from benchmarks.campaign import exp001_driver as legacy  # noqa: E402
from benchmarks.campaign import exp001_r1_driver as r1  # noqa: E402
from tools.reproduce import (  # noqa: E402
    read_no_follow,
    read_verified_no_follow,
    verify_manifest,
    write_no_follow,
)

#: Experiment identifier, matching every r1 run's campaign metadata sidecar.
EXPERIMENT_ID = "EXP-001-r1"

#: The E3 session that produced the six input runs.
E3_SESSION = "EXP-001-r1-E3"

#: The session that owns this analysis. The r1 stages carry no integer session
#: number, so campaign plan §12 rule 3's ``campaign/<session>-<exp>-<stage>``
#: branch shape becomes ``campaign/exp001-r1-e4``; the register's next numbered
#: session, 0159, stays BLOCKED until this experiment's E5 verdict.
SESSION = "EXP-001-r1-E4"

#: ``F`` — the last pre-registration edit, frozen at the first ``RUN-``
#: creation and quoted on ``log.md`` line 1 (campaign plan §12.4).
FREEZE_COMMIT = "5d5ae3521317af47a11afa8d689935ac2fc0f447"

#: ``R`` — the single clean campaign execution checkout all six runs record as
#: ``environment.git_commit`` and embed as their run-ID ``<sha>``. ``F`` and
#: ``R`` name the same commit here; their roles remain distinct (``log.md``).
EXECUTION_COMMIT = "5d5ae3521317af47a11afa8d689935ac2fc0f447"

#: ``M`` — the distinct, already-merged green-main baseline carrying DV-043,
#: recorded in the E3 log and required by pre-registration §8 rule 1.
MAIN_BASELINE = "9b79d2e5b246bead1243074659dc99d049762a40"

#: The two E3 build-log extension hashes, each associated with the backend
#: label built for it (pre-registration §5.1, ``log.md``). They differ by
#: design — two feature-exclusive builds from one execution commit — so §8
#: rule 1 requires each to be verified against **its own** log entry rather
#: than demanding binary identity.
WGPU_EXTENSION_SHA256 = (
    "2f902e806a3cab860f3fbdf9b4e7ad7d4928329df63aaf46df4010ed430e748b"
)
CUDA_EXTENSION_SHA256 = (
    "701bb529965a6916a71a5f5350e286428346e81f541a0c46f6e509b2008753c2"
)

#: Explicit provenance stamp. Never a wall-clock read — campaign plan §7.4
#: step 5 requires a clean checkout to reproduce every digest byte for byte.
GENERATED_AT = "2026-09-29T12:00:00Z"

#: Raw artefact root, shared with the predecessor's four original runs.
RAW_ARTEFACT_ROOT = Path("benchmarks/results/EXP-001")

#: Record root (pre-registration "Record root").
RECORD_ROOT = Path("DOCS/experiments/EXP-001-r1-golden-trajectory-numerical-parity")

#: Gitignored generated-output root (campaign plan §7.4 item 4).
OUTPUT_ROOT = Path("DOCS/test_and_benchmark_results") / EXPERIMENT_ID

#: Registered corpus directory, whose manifest is a pinned input fingerprint.
CORPUS_DIR = Path("parity/corpus")

#: The four fixed outputs §8's table names. ``write_outputs`` always writes all
#: four under ``OUTPUT_ROOT``; a ``--manifest-path`` colliding with any of them
#: would let ``write_report_manifest`` overwrite an output after its digest was
#: already recorded, leaving the committed manifest describing bytes no longer
#: on disk.
SUMMARY_JSON_FILENAME = "summary.json"
SUMMARY_MD_FILENAME = "summary.md"
CASE_COMPARISONS_FILENAME = "case-comparisons.json"
ERROR_DISTRIBUTIONS_FILENAME = "error-distributions.json"
GENERATED_FILENAMES: tuple[str, ...] = (
    CASE_COMPARISONS_FILENAME,
    ERROR_DISTRIBUTIONS_FILENAME,
    SUMMARY_JSON_FILENAME,
    SUMMARY_MD_FILENAME,
)

#: Registered tolerances, quoted for the report (pre-registration §1.1).
TOLERANCES = {
    "trajectory": f"rtol={TRAJECTORY_RTOL:g}, atol={TRAJECTORY_ATOL:g}",
    "metric": f"rtol={METRIC_RTOL:g}, atol={METRIC_ATOL:g}",
    "kernel": f"rtol={legacy.KERNEL_RTOL:g}, atol={legacy.KERNEL_ATOL:g}",
}

#: Per-quantity ``(rtol, atol)`` for the CPU comparisons, taken from the frozen
#: ``prin.parity.schema`` constants rather than restated locally.
QUANTITY_TOLERANCE: dict[str, tuple[float, float]] = {
    "trajectory": (TRAJECTORY_RTOL, TRAJECTORY_ATOL),
    "metric": (METRIC_RTOL, METRIC_ATOL),
}

#: The two coherence arrays carry the metric tolerance; every other CPU
#: comparison array carries the trajectory tolerance.
METRIC_ARRAY_NAMES: frozenset[str] = frozenset(legacy._BEYOND_HORIZON_ARRAY_NAMES)

#: The full 11-array corpus comparison inventory, in ``compare_case`` order.
CORPUS_ARRAY_NAMES: tuple[str, ...] = (
    "phase_init",
    "amplitude_init",
    "frequency_init",
    "phase_final",
    "amplitude_final",
    "frequency_final",
    *legacy._TRAJ_ARRAY_NAMES,
)

#: The within-horizon fuzz comparison inventory: the three explicit initial
#: arrays plus the five horizon-sliced trajectory/metric arrays.
FUZZ_ARRAY_NAMES: tuple[str, ...] = (
    "phase_init",
    "amplitude_init",
    "frequency_init",
    *legacy._TRAJ_ARRAY_NAMES,
)

#: The three float32 derivative arrays H4 compares, in driver order.
KERNEL_ARRAY_NAMES: tuple[str, ...] = ("dphase", "damplitude", "dfrequency")

#: Registered denominators (pre-registration §2, §8).
H1_DENOMINATOR = 504
H2A_ELIGIBLE_DENOMINATOR = 978
H2A_CHARACTERIZED_DENOMINATOR = 22
H2A_DENOMINATOR = 1000
H3_DENOMINATOR = 14
H4_DENOMINATOR = 72

#: Run-directory name grammar, campaign plan §7.1. Anchored with ``\Z``:
#: Python's ``$`` also matches just before a trailing newline.
RUN_ID_PATTERN = re.compile(
    r"^RUN-(?P<utc>\d{8}T\d{6}Z)-(?P<sha>[0-9a-f]{7,40})"
    r"-(?P<label>[A-Za-z0-9][A-Za-z0-9._-]*)\Z"
)

#: Pre-registration §3's frozen predictions, quoted for the expected-versus-
#: observed table. These are predictions from prior governed evidence, never
#: acceptance targets, and no verdict here is derived from them.
EXPECTED_RESULTS: tuple[tuple[str, str, str], ...] = (
    (
        "H1",
        "Confirmed under the registered rule",
        "504 accepted; approximately 19 native DV-007 breaches positively "
        "explained; zero unexplained breaches",
    ),
    (
        "H2a",
        "Confirmed with the fixed characterization stratum",
        "978 accepted pointwise; 22 sensitivity proofs and valid PRIN outputs; "
        "zero unexplained eligible breaches",
    ),
    (
        "H2b",
        "Equivalent ensemble means",
        "Each mean difference near zero, with both CI endpoints strictly "
        "inside its margin; no directional bias predicted",
    ),
    (
        "H3",
        "Identical",
        "14/14 byte-identical within each invocation; zero separate-run "
        "digest differences",
    ),
    (
        "H4",
        "Both backends within the same kernel tolerance",
        "CUDA 72/72 and wgpu 72/72, zero failed derivative elements on either",
    ),
)


@dataclass(frozen=True)
class RunLeg:
    """One E3 run directory in the explicit index §8 rule 1 requires.

    Attributes:
        label: The pre-registered run label.
        run_id: The ``RUN-<UTC>-<sha>-<label>`` directory name.
        artefact: The ``<mode>_<label>.json`` result filename.
        mode: The registered driver mode that produced it.
        backend: The ``environment.backend`` the envelope must carry.
        dtype: The ``environment.dtype`` the envelope must carry.
        hypotheses: The hypothesis tags the run's own
            ``campaign-metadata.json`` sidecar carries for this artefact. These
            are the campaign's registered tags (the driver's
            ``_VALID_HYPOTHESES`` set: H1, H2, H3, H4), so the fuzz leg carries
            ``H2`` and not its two sub-hypotheses; see
            :data:`ADJUDICATED_HYPOTHESES` for what this analysis derives from
            each leg.
        timed: Whether the sidecar entry is the GPU object form carrying
            ``timing_method`` (campaign plan §7.2, §11.5).
        extension_sha256: The E3 build-log extension hash this leg must carry.
    """

    label: str
    run_id: str
    artefact: str
    mode: str
    backend: str
    dtype: str
    hypotheses: tuple[str, ...]
    timed: bool
    extension_sha256: str


#: The six registered E3 runs, in ``log.md``'s recorded execution order. This
#: tuple **is** the input index: nothing outside it is read as evidence.
RUN_LEGS: tuple[RunLeg, ...] = (
    RunLeg(
        label="r1-kernel-path-wgpu",
        run_id="RUN-20260929T091735Z-5d5ae35-r1-kernel-path-wgpu",
        artefact="kernel-path_r1-kernel-path-wgpu.json",
        mode="kernel-path",
        backend="wgpu",
        dtype="f32",
        hypotheses=("H4",),
        timed=True,
        extension_sha256=WGPU_EXTENSION_SHA256,
    ),
    RunLeg(
        label="r1-corpus-cpu",
        run_id="RUN-20260929T092619Z-5d5ae35-r1-corpus-cpu",
        artefact="corpus_r1-corpus-cpu.json",
        mode="corpus",
        backend="cpu",
        dtype="f64",
        hypotheses=("H1",),
        timed=False,
        extension_sha256=CUDA_EXTENSION_SHA256,
    ),
    RunLeg(
        label="r1-repeatability-cpu",
        run_id="RUN-20260929T092626Z-5d5ae35-r1-repeatability-cpu",
        artefact="repeatability_r1-repeatability-cpu.json",
        mode="repeatability",
        backend="cpu",
        dtype="f64",
        hypotheses=("H3",),
        timed=False,
        extension_sha256=CUDA_EXTENSION_SHA256,
    ),
    RunLeg(
        label="r1-seedrep0-cpu",
        run_id="RUN-20260929T092631Z-5d5ae35-r1-seedrep0-cpu",
        artefact="repeatability_r1-seedrep0-cpu.json",
        mode="repeatability",
        backend="cpu",
        dtype="f64",
        hypotheses=("H3",),
        timed=False,
        extension_sha256=CUDA_EXTENSION_SHA256,
    ),
    RunLeg(
        label="r1-fuzz-cpu",
        run_id="RUN-20260929T092641Z-5d5ae35-r1-fuzz-cpu",
        artefact="fuzz_r1-fuzz-cpu.json",
        mode="fuzz",
        backend="cpu",
        dtype="f64",
        hypotheses=("H2",),
        timed=False,
        extension_sha256=CUDA_EXTENSION_SHA256,
    ),
    RunLeg(
        label="r1-kernel-path-cuda",
        run_id="RUN-20260929T093035Z-5d5ae35-r1-kernel-path-cuda",
        artefact="kernel-path_r1-kernel-path-cuda.json",
        mode="kernel-path",
        backend="cuda",
        dtype="f32",
        hypotheses=("H4",),
        timed=True,
        extension_sha256=CUDA_EXTENSION_SHA256,
    ),
)

#: Run label to the pre-registration §2 hypotheses this analysis adjudicates
#: from that leg. Identical to :attr:`RunLeg.hypotheses` except on the fuzz
#: leg, whose sidecar carries the campaign's registered ``H2`` tag while §2
#: splits it into the two separately decided H2a and H2b. Both are reported:
#: the sidecar tag is what E3 committed, this mapping is what E4 derives.
ADJUDICATED_HYPOTHESES: dict[str, tuple[str, ...]] = {
    leg.label: (("H2a", "H2b") if leg.mode == "fuzz" else leg.hypotheses)
    for leg in RUN_LEGS
}


class AnalysisError(RuntimeError):
    """Raised when an input artefact cannot support the registered analysis.

    Always fail-closed: a missing artefact, a provenance mismatch against
    :data:`EXECUTION_COMMIT`, an unverified manifest, an unexpected case
    inventory, a non-finite scientific field, or a stored classification the
    retained per-array records do not reproduce. None of these may be worked
    around by the analysis — §8 rule 1 requires aborting an invalid analysis
    instead of inferring a result from a partial or mixed experiment. They
    invalidate the input; they are not a hypothesis verdict.
    """


def _require(condition: bool, message: str) -> None:
    """Raise :class:`AnalysisError` unless ``condition`` holds.

    Args:
        condition: The registered requirement being checked.
        message: The failure message, naming the leg and the rule.

    Raises:
        AnalysisError: If ``condition`` is false.
    """
    if not condition:
        raise AnalysisError(message)


def _as_dict(value: Any, context: str) -> dict[str, Any]:
    """Narrow one stored value to a JSON object, failing closed.

    Args:
        value: The stored value.
        context: Human-readable location, for the failure message.

    Returns:
        The value as a ``dict``.

    Raises:
        AnalysisError: If the value is not a JSON object.
    """
    if not isinstance(value, dict):
        raise AnalysisError(f"{context}: expected a JSON object, got {value!r}")
    return value


def _as_list(value: Any, context: str) -> list[Any]:
    """Narrow one stored value to a JSON array, failing closed.

    Args:
        value: The stored value.
        context: Human-readable location, for the failure message.

    Returns:
        The value as a ``list``.

    Raises:
        AnalysisError: If the value is not a JSON array.
    """
    if not isinstance(value, list):
        raise AnalysisError(f"{context}: expected a JSON array, got {value!r}")
    return value


def _finite_float(value: Any, context: str) -> float:
    """Return one required finite real, rejecting bools and non-numbers.

    Args:
        value: The stored field.
        context: Human-readable field location, for the failure message.

    Returns:
        The value as a finite ``float``.

    Raises:
        AnalysisError: If the value is a bool, not a real number, or not
            finite (§8 rule 1: reject non-finite scientific fields).
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AnalysisError(f"{context}: expected a real number, got {value!r}")
    number = float(value)
    if not isfinite(number):
        raise AnalysisError(f"{context}: non-finite scientific field {value!r}")
    return number


def _required_int(value: Any, context: str) -> int:
    """Return one required non-bool ``int``.

    Args:
        value: The stored field.
        context: Human-readable field location, for the failure message.

    Returns:
        The value as an ``int``.

    Raises:
        AnalysisError: If the value is not an integer.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise AnalysisError(f"{context}: expected an integer, got {value!r}")
    return value


def _canonical_bytes(payload: Any) -> bytes:
    """Serialize one payload deterministically for writing and digesting.

    Args:
        payload: A JSON-serializable value with no non-finite number.

    Returns:
        UTF-8 bytes: two-space indent, sorted keys, ``allow_nan=False``, one
        trailing LF.

    Raises:
        AnalysisError: If the payload is not finite, strictly serializable
            JSON. A NaN or Infinity reaching an output would make the
            committed digest unreproducible and the verdict unauditable.
    """
    try:
        text = json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise AnalysisError(f"output is not finite JSON: {exc}") from exc
    return (text + "\n").encode("utf-8")


def _safe_temp_root(repository_root: Path) -> tuple[Path, ...]:
    """The system temp directory, omitted if it would legitimize the checkout.

    The temp root exists in the permitted-roots tuples purely to support a
    test's scratch directory. Containment is "is the destination under this
    root", checked by walking *every* ancestor — so if the checkout itself
    lives under the system temp directory (an ephemeral CI workspace, a
    sandboxed clone), admitting the temp root would transitively admit every
    path inside the checkout, including the frozen ``preregistration.md``.
    Omitting it in that one case is the correct trade.

    Args:
        repository_root: Repository root.

    Returns:
        ``(temp_root,)`` normally; ``()`` if the checkout is under, or is, the
        temp root.
    """
    temp_root = Path(tempfile.gettempdir()).resolve()
    checkout_root = repository_root.resolve()
    if checkout_root == temp_root or temp_root in checkout_root.parents:
        return ()
    return (temp_root,)


def _reject_configured_root_symlink(
    repository_root: Path, relative_root: Path, name: str
) -> None:
    """Refuse a governed root with a symbolic-link component, before resolving.

    The permitted-roots set is built by calling ``.resolve()`` on the
    configured roots, and every later containment check trusts that resolved
    set. ``.resolve()`` follows symlinks, so a configured root — or *any*
    ancestor of it below the checkout anchor — replaced with a symlink would
    silently turn the "permitted root" into the link's target and admit every
    path under it (CWE-59). Checked no-follow, before resolution. A component
    that does not exist yet (``OUTPUT_ROOT`` is gitignored) is not a symlink
    and passes unchanged. ``repository_root`` itself and everything above it
    are deliberately not checked: the checkout anchor is this module's trusted
    input.

    Args:
        repository_root: The trusted checkout anchor, unresolved.
        relative_root: The configured root, relative to ``repository_root``.
        name: Human-readable name of the root, for the failure message.

    Raises:
        AnalysisError: If any component of ``relative_root`` below
            ``repository_root`` is a symbolic link.
    """
    current = repository_root
    for part in relative_root.parts:
        current = current / part
        if current.is_symlink():
            raise AnalysisError(
                f"{name} {repository_root / relative_root} has a symbolic "
                f"link component at {current}; refusing to use it as a "
                "governed root"
            )


def allowed_output_roots(repository_root: Path) -> tuple[Path, ...]:
    """Return the only directories this analysis may write into.

    Mirrors the containment pattern the repository already uses for generated
    artefacts (``tools.reproduce.ALLOWED_MANIFEST_ROOTS``,
    ``prin.reporting._artifacts.allowed_output_roots``): the gitignored
    generated-output root, the experiment's record root, and the operating
    system temporary directory (see :func:`_safe_temp_root`).

    Args:
        repository_root: Repository root.

    Returns:
        The resolved permitted roots.

    Raises:
        AnalysisError: If ``OUTPUT_ROOT`` or ``RECORD_ROOT``, or any path
            component of either below the checkout anchor, is a symbolic link.
    """
    _reject_configured_root_symlink(repository_root, OUTPUT_ROOT, "output root")
    _reject_configured_root_symlink(repository_root, RECORD_ROOT, "record root")
    return (
        (repository_root / OUTPUT_ROOT).resolve(),
        (repository_root / RECORD_ROOT).resolve(),
        *_safe_temp_root(repository_root),
    )


def allowed_generated_output_dirs(repository_root: Path) -> tuple[Path, ...]:
    """Return the only directories the CLI may write generated E4 files into.

    Deliberately excludes the frozen record root, unlike
    :func:`allowed_output_roots`: ``--output-dir`` writes the four generated
    files under whatever directory it names, and admitting the record root
    would let a caller shadow ``preregistration.md`` or this module's own
    source. Only ``report-manifest.json`` — the one file this analysis is
    registered to add to the record root — may land there, and
    :func:`_checked_manifest_destination` checks it separately.

    Args:
        repository_root: Repository root.

    Returns:
        The resolved permitted roots.

    Raises:
        AnalysisError: If ``OUTPUT_ROOT``, or any path component of it below
            the checkout anchor, is a symbolic link.
    """
    _reject_configured_root_symlink(repository_root, OUTPUT_ROOT, "output root")
    return (
        (repository_root / OUTPUT_ROOT).resolve(),
        *_safe_temp_root(repository_root),
    )


def _checked_destination(path: Path, roots: tuple[Path, ...], name: str) -> Path:
    """Resolve one write destination and refuse anything outside ``roots``.

    Checked no-follow, before resolution: ``.resolve()`` follows a trailing
    symlink, so a symlinked destination pointing at a directory inside the
    permitted roots would otherwise resolve into, and be accepted as, that
    directory.

    Args:
        path: The requested destination.
        roots: Permitted roots from :func:`allowed_output_roots`.
        name: Human-readable name of the destination, for the error message.

    Returns:
        The resolved destination.

    Raises:
        AnalysisError: If the destination is itself a symbolic link, or
            escapes every permitted root.
    """
    path = Path(path)
    if path.is_symlink():
        raise AnalysisError(
            f"{name} {path} is a symbolic link; refusing to resolve it into a "
            "write destination"
        )
    resolved = path.resolve()
    if not any(resolved == root or root in resolved.parents for root in roots):
        permitted = ", ".join(str(root) for root in roots)
        raise AnalysisError(
            f"{name} {resolved} is outside the permitted output roots: {permitted}"
        )
    return resolved


def _checked_manifest_destination(
    path: Path, roots: tuple[Path, ...], record_root: Path
) -> Path:
    """Resolve ``report-manifest.json``'s destination, refusing to overwrite.

    A plain :func:`_checked_destination` call would accept any path inside the
    frozen record root, including ``preregistration.md``, ``log.md`` or this
    module's own source. A destination anywhere inside the record root, at any
    depth, is therefore required to be exactly
    ``record_root / "report-manifest.json"``. A destination under the
    generated-output root or the system temporary directory is unrestricted,
    since neither holds anything immutable. The requested path is also checked
    no-follow before resolution, so a symlink planted *at* the canonical name
    cannot sidestep the inside-record-root rule (CWE-59).

    Args:
        path: The requested manifest destination.
        roots: Permitted roots from :func:`allowed_output_roots`.
        record_root: The resolved experiment record root.

    Returns:
        The resolved destination.

    Raises:
        AnalysisError: If the requested destination is itself a symbolic link,
            escapes every permitted root, or lands inside the record root
            under any path other than
            ``record_root / "report-manifest.json"``.
    """
    if path.is_symlink():
        raise AnalysisError(
            f"manifest path {path} is a symbolic link; refusing to resolve it "
            "into a write destination"
        )
    resolved = _checked_destination(path, roots, "manifest path")
    canonical = record_root / "report-manifest.json"
    inside_record_root = resolved == record_root or record_root in resolved.parents
    if inside_record_root and resolved != canonical:
        raise AnalysisError(
            f"manifest path {resolved} is inside the frozen record root but is "
            f"not {canonical}; this analysis may not overwrite any other file "
            "there"
        )
    return resolved


def verify_e3_log(repository_root: Path) -> dict[str, Any]:
    """Verify the E3 log records the identities §8 rule 1 binds this analysis to.

    ``F``, ``R``, ``M`` and both build-log extension hashes are properties of
    the *execution*, recorded in ``log.md``; the run artefacts can only attest
    to what they themselves carry. Requiring the log to state each literal, and
    requiring the artefacts to agree with the same literals, closes the binding
    from both sides: a run whose ``git_commit`` or extension hash matched a
    forged constant would still have to appear in the committed E3 log, and a
    log edited to match a forged run would contradict the frozen ``F`` on its
    own line 1.

    Args:
        repository_root: Repository root.

    Returns:
        The verified identity mapping recorded in every output.

    Raises:
        AnalysisError: If ``log.md`` is absent or unreadable, its first line
            does not carry the freeze SHA, ``M`` and ``R`` are not distinct, or
            any required literal is missing.
    """
    _reject_configured_root_symlink(repository_root, RECORD_ROOT, "record root")
    log_path = repository_root / RECORD_ROOT / "log.md"
    try:
        text = read_no_follow(log_path, "E3 execution log").decode("utf-8")
    except OSError as exc:
        raise AnalysisError(f"E3 execution log is unreadable: {exc}") from exc
    lines = text.splitlines()
    _require(bool(lines), "log.md is empty; no freeze SHA is recorded")
    _require(
        FREEZE_COMMIT in lines[0],
        f"log.md line 1 does not quote the freeze SHA {FREEZE_COMMIT} "
        "(campaign plan §12.4)",
    )
    for label, literal in (
        ("execution checkout R", EXECUTION_COMMIT),
        ("green-main baseline M", MAIN_BASELINE),
        ("wgpu build extension hash", WGPU_EXTENSION_SHA256),
        ("cuda build extension hash", CUDA_EXTENSION_SHA256),
    ):
        _require(literal in text, f"log.md does not record the {label} {literal}")
    _require(
        MAIN_BASELINE != EXECUTION_COMMIT,
        "M and R must be distinct commits (pre-registration §5.1)",
    )
    _require(
        WGPU_EXTENSION_SHA256 != CUDA_EXTENSION_SHA256,
        "the two feature-exclusive builds must record distinct extension "
        "hashes (pre-registration §5.1)",
    )
    return {
        "freeze_commit": FREEZE_COMMIT,
        "execution_commit": EXECUTION_COMMIT,
        "main_baseline": MAIN_BASELINE,
        "extension_sha256": {
            "r1-kernel-path-wgpu": WGPU_EXTENSION_SHA256,
            "r1-kernel-path-cuda": CUDA_EXTENSION_SHA256,
        },
        "log_path": (RECORD_ROOT / "log.md").as_posix(),
    }


def verify_run_inventory(repository_root: Path) -> list[str]:
    """Prove §8's "six distinct r1 run IDs overall" from directory names only.

    This is *not* input selection: the evidence read is exactly
    :data:`RUN_LEGS`. Enumerating names is the only way to detect a seventh r1
    run directory, a duplicate label, or a retry the index silently omits — all
    of which §8 rule 1 requires rejecting rather than analysing around.

    Args:
        repository_root: Repository root.

    Returns:
        The sorted r1 run-directory names present under the raw root.

    Raises:
        AnalysisError: If the present r1 run IDs are not exactly the six in the
            index, or any of them fails the run-ID grammar or does not embed a
            prefix of ``R``.
    """
    _reject_configured_root_symlink(
        repository_root, RAW_ARTEFACT_ROOT, "raw artefact root"
    )
    raw_root = repository_root / RAW_ARTEFACT_ROOT
    if not raw_root.is_dir():
        raise AnalysisError(f"raw artefact root {raw_root} does not exist")
    present: list[str] = []
    for entry in sorted(raw_root.iterdir(), key=lambda item: item.name):
        match = RUN_ID_PATTERN.fullmatch(entry.name)
        if match is None or not match["label"].startswith("r1-"):
            continue
        if not entry.is_dir():
            raise AnalysisError(f"{entry.name} is not a directory")
        _require(
            EXECUTION_COMMIT.startswith(match["sha"]),
            f"{entry.name}: run-ID sha {match['sha']} does not prefix R "
            f"{EXECUTION_COMMIT}",
        )
        present.append(entry.name)
    expected = sorted(leg.run_id for leg in RUN_LEGS)
    _require(
        present == expected,
        f"r1 run inventory {present} is not exactly the six indexed runs "
        f"{expected} (§8 rule 1: reject an extra, duplicated or missing run)",
    )
    return present


def _verify_sidecar(run_dir: Path, leg: RunLeg) -> dict[str, Any]:
    """Verify one run's ``campaign-metadata.json`` against the index entry.

    Args:
        run_dir: The run directory, already manifest-verified.
        leg: The index entry naming it.

    Returns:
        The parsed sidecar.

    Raises:
        AnalysisError: If any required sidecar field is missing or disagrees
            with the registered identity (campaign plan §7.2).
    """
    path = run_dir / "campaign-metadata.json"
    sidecar = _as_dict(
        json.loads(read_no_follow(path, "campaign metadata sidecar").decode("utf-8")),
        f"{leg.run_id}: campaign-metadata.json",
    )
    for field in ("exp_id", "run_id", "session", "operator", "artefacts"):
        _require(field in sidecar, f"{leg.run_id}: sidecar is missing {field}")
    _require(
        sidecar["exp_id"] == EXPERIMENT_ID,
        f"{leg.run_id}: sidecar exp_id {sidecar['exp_id']!r} is not {EXPERIMENT_ID!r}",
    )
    _require(
        sidecar["run_id"] == leg.run_id,
        f"{leg.run_id}: sidecar run_id {sidecar['run_id']!r} does not match "
        "the directory name",
    )
    _require(
        sidecar["session"] == E3_SESSION,
        f"{leg.run_id}: sidecar session {sidecar['session']!r} is not {E3_SESSION!r}",
    )
    _require(
        isinstance(sidecar["operator"], str) and bool(sidecar["operator"].strip()),
        f"{leg.run_id}: sidecar operator must be a non-empty string",
    )
    artefacts = _as_dict(sidecar["artefacts"], f"{leg.run_id}: sidecar artefacts")
    _require(
        list(artefacts) == [leg.artefact],
        f"{leg.run_id}: sidecar artefacts {sorted(artefacts)} must name exactly "
        f"{leg.artefact!r}",
    )
    entry = artefacts[leg.artefact]
    if leg.timed:
        _require(
            isinstance(entry, dict)
            and entry.get("hypotheses") == list(leg.hypotheses)
            and entry.get("timing_method") == legacy.KERNEL_PATH_TIMING_METHOD,
            f"{leg.run_id}: GPU sidecar entry {entry!r} must carry hypotheses "
            f"{list(leg.hypotheses)} and timing_method "
            f"{legacy.KERNEL_PATH_TIMING_METHOD!r}",
        )
    else:
        _require(
            entry == list(leg.hypotheses),
            f"{leg.run_id}: sidecar hypotheses {entry!r} must be exactly "
            f"{list(leg.hypotheses)}",
        )
    return sidecar


def _verify_envelope(payload: dict[str, Any], leg: RunLeg) -> None:
    """Verify one result artefact's ``environment`` and ``config`` blocks.

    Checks the identity, provenance and input-fingerprint fields §8 rule 1
    lists: experiment identity, code SHA ``R``, protocol revision, seed pair,
    backend/dtype and label pairing, mode, iteration count, guard policy, the
    leg's own E3 build extension hash, the pinned corpus-manifest digest and,
    for the legs that used the native reference, the pinned reference-source,
    instrument, PRINet-version and fuzz-stream digests.

    Args:
        payload: The parsed result artefact.
        leg: The index entry naming it.

    Raises:
        AnalysisError: If any envelope field is missing or disagrees with the
            registered value.
    """
    environment = _as_dict(payload.get("environment"), f"{leg.run_id}: environment")
    config = _as_dict(payload.get("config"), f"{leg.run_id}: config")
    cases = _as_list(payload.get("cases"), f"{leg.run_id}: cases")
    for field in legacy._REQUIRED_ENV_FIELDS:
        _require(
            field in environment,
            f"{leg.run_id}: environment is missing required field {field}",
        )
    _require(
        environment.get("git_commit") == EXECUTION_COMMIT,
        f"{leg.run_id}: environment.git_commit "
        f"{environment.get('git_commit')!r} is not R {EXECUTION_COMMIT}",
    )
    _require(
        environment.get("backend") == leg.backend,
        f"{leg.run_id}: environment.backend {environment.get('backend')!r} is "
        f"not the registered {leg.backend!r} for label {leg.label!r}",
    )
    _require(
        environment.get("dtype") == leg.dtype,
        f"{leg.run_id}: environment.dtype {environment.get('dtype')!r} is not "
        f"the registered {leg.dtype!r}",
    )
    if leg.mode == "kernel-path":
        for field in legacy._GPU_REQUIRED_ENV_FIELDS:
            _require(
                environment.get(field) not in (None, ""),
                f"{leg.run_id}: GPU leg is missing {field} metadata "
                "(pre-registration §4.2 item 4)",
            )
    checks: tuple[tuple[str, Any, Any], ...] = (
        ("experiment_id", config.get("experiment_id"), EXPERIMENT_ID),
        ("protocol_revision", config.get("protocol_revision"), 1),
        ("mode", config.get("mode"), leg.mode),
        ("seed_counter", config.get("seed_counter"), 0),
        ("seed_key", config.get("seed_key"), 1),
        ("guard_policy", config.get("guard_policy"), "non_negative"),
        (
            "corpus_manifest_sha256",
            config.get("corpus_manifest_sha256"),
            r1.CORPUS_SHA256,
        ),
        (
            "prin_extension_sha256",
            config.get("prin_extension_sha256"),
            leg.extension_sha256,
        ),
    )
    for name, actual, expected in checks:
        _require(
            actual == expected,
            f"{leg.run_id}: config.{name} {actual!r} is not the registered "
            f"{expected!r}",
        )
    iterations = _required_int(
        config.get("iterations"), f"{leg.run_id}: config.iterations"
    )
    _require(
        iterations == len(cases),
        f"{leg.run_id}: config.iterations {iterations} disagrees with the "
        f"{len(cases)} stored cases",
    )
    out_dir = config.get("out_dir")
    _require(
        isinstance(out_dir, str) and Path(out_dir).name == leg.run_id,
        f"{leg.run_id}: config.out_dir {out_dir!r} does not name this run "
        "directory (only its basename is checked; the absolute prefix is the "
        "E3 execution checkout, not this one)",
    )
    extension = config.get("prin_extension")
    _require(
        isinstance(extension, str) and Path(extension).name == "_prin_core.pyd",
        f"{leg.run_id}: config.prin_extension {extension!r} does not name the "
        "built extension",
    )
    if leg.mode in ("corpus", "fuzz"):
        for name, expected in (
            ("reference_source_sha256", r1.REFERENCE_SOURCE_SHA256),
            ("instrument_sha256", r1.INSTRUMENT_SHA256),
            ("prinet_version", legacy.PRINET_REFERENCE_VERSION),
        ):
            _require(
                config.get(name) == expected,
                f"{leg.run_id}: config.{name} {config.get(name)!r} is not the "
                f"registered {expected!r}",
            )
    if leg.mode == "fuzz":
        _require(
            config.get("stream_sha256") == r1.STREAM_SHA256,
            f"{leg.run_id}: config.stream_sha256 "
            f"{config.get('stream_sha256')!r} is not the registered "
            f"{r1.STREAM_SHA256}",
        )


@dataclass(frozen=True)
class LoadedRun:
    """One verified input run and everything §8 rule 1 requires of it.

    Attributes:
        leg: The index entry it was loaded through.
        payload: The parsed result artefact.
        cases: ``payload["cases"]``, as verified JSON objects.
        sidecar: The verified ``campaign-metadata.json``.
        files: The run's verified manifest records.
        manifest_bytes: Size of ``manifest.json`` itself.
        manifest_sha256: SHA-256 of ``manifest.json`` itself.
    """

    leg: RunLeg
    payload: dict[str, Any]
    cases: list[dict[str, Any]]
    sidecar: dict[str, Any]
    files: list[dict[str, Any]]
    manifest_bytes: int
    manifest_sha256: str


def load_run(repository_root: Path, leg: RunLeg) -> LoadedRun:
    """Verify one indexed run directory and load its result artefact.

    Campaign plan §7.4 step 1's ``verify_manifest`` runs first, then the
    artefact is re-read through ``read_verified_no_follow`` against the
    manifest record, so the bytes adjudicated are provably the bytes
    manifested — a second, unverified read would leave a swap window between
    verification and use. The manifest records returned here are the ones this
    call verified, so the provenance listing in the outputs attests exactly the
    bytes the verdict was computed from.

    Args:
        repository_root: Repository root.
        leg: The index entry to load.

    Returns:
        The verified run.

    Raises:
        AnalysisError: If any path component of the run directory below the
            checkout anchor is a symbolic link, the run ID is not canonical or
            does not embed a prefix of ``R``, the artefact is absent or
            unmanifested, or the sidecar or envelope disagrees with the
            registered identity.
    """
    _reject_configured_root_symlink(
        repository_root, RAW_ARTEFACT_ROOT / leg.run_id, "raw artefact run directory"
    )
    run_dir = repository_root / RAW_ARTEFACT_ROOT / leg.run_id
    match = RUN_ID_PATTERN.fullmatch(leg.run_id)
    _require(match is not None, f"{leg.run_id}: not a canonical run ID")
    if match is None:
        raise AnalysisError(f"{leg.run_id}: not a canonical run ID")
    _require(
        match["label"] == leg.label,
        f"{leg.run_id}: run-ID label {match['label']!r} is not {leg.label!r}",
    )
    _require(
        EXECUTION_COMMIT.startswith(match["sha"]),
        f"{leg.run_id}: run-ID sha {match['sha']!r} does not prefix R",
    )
    records = verify_manifest(
        results_dir=run_dir, manifest_path=run_dir / "manifest.json"
    )
    record = next((item for item in records if item.path == leg.artefact), None)
    if record is None:
        raise AnalysisError(
            f"{leg.run_id}: {leg.artefact} is not a manifested artefact"
        )
    try:
        raw_bytes = read_verified_no_follow(
            run_dir / leg.artefact,
            record.bytes,
            record.sha256,
            leg.artefact,
            "result artefact",
        )
    except FileNotFoundError as exc:
        raise AnalysisError(
            f"{leg.run_id}: missing result artefact {leg.artefact}"
        ) from exc
    payload = _as_dict(
        json.loads(raw_bytes.decode("utf-8")), f"{leg.run_id}: result artefact"
    )
    sidecar = _verify_sidecar(run_dir, leg)
    _verify_envelope(payload, leg)
    cases = [
        _as_dict(case, f"{leg.run_id}: case at index {index}")
        for index, case in enumerate(_as_list(payload.get("cases"), "cases"))
    ]
    manifest_raw = read_no_follow(run_dir / "manifest.json", "run manifest")
    return LoadedRun(
        leg=leg,
        payload=payload,
        cases=cases,
        sidecar=sidecar,
        files=[
            {"path": item.path, "bytes": item.bytes, "sha256": item.sha256}
            for item in records
        ],
        manifest_bytes=len(manifest_raw),
        manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(),
    )


def _comparison_violation(
    record: Any,
    *,
    expected_name: str,
    expected_total: int | None,
    expected_quantity: str | None,
    atol: float,
    context: str,
) -> str | None:
    """Check one retained comparator record for internal consistency.

    These are **necessary-condition** checks on the stored record, not a
    re-evaluation of ``numpy.isclose``: the raw arrays are absent by design and
    §8 rule 7 forbids claiming otherwise. What the registered rule soundly
    implies is checked — ``within_tolerance`` must equal ``failed_count == 0``;
    a breach means at least one element exceeded ``atol + rtol * |operand|``,
    which is never below ``atol``, so ``max_abs_diff`` must exceed ``atol``; a
    zero maximum absolute difference must force every relative difference to
    zero; counts must be non-negative, ordered and bounded by the case shape.

    Args:
        record: One stored comparison object.
        expected_name: The array name this position must carry.
        expected_total: The element count the case's shape implies, or ``None``
            to skip the shape check.
        expected_quantity: The registered quantity label the record must carry,
            or ``None`` for the kernel records, which carry none.
        atol: The registered absolute tolerance for this comparison class.
        context: Human-readable location, for the failure message.

    Returns:
        ``None`` when the record is internally consistent, else the reason.
    """
    if not isinstance(record, dict):
        return f"{context}: comparison record is not an object"
    where = f"{context}/{expected_name}"
    if record.get("array_name") != expected_name:
        return (
            f"{where}: array_name {record.get('array_name')!r} is not {expected_name!r}"
        )
    if expected_quantity is not None and record.get("quantity") != expected_quantity:
        return (
            f"{where}: quantity {record.get('quantity')!r} is not the "
            f"registered {expected_quantity!r}"
        )
    within = record.get("within_tolerance")
    if not isinstance(within, bool):
        return f"{where}: within_tolerance is not a bool"
    try:
        failed = _required_int(record.get("failed_count"), f"{where}: failed_count")
        total = _required_int(record.get("total_count"), f"{where}: total_count")
        max_abs = _finite_float(record.get("max_abs_diff"), f"{where}: max_abs_diff")
        max_rel = _finite_float(record.get("max_rel_diff"), f"{where}: max_rel_diff")
    except AnalysisError as exc:
        return str(exc)
    if failed < 0 or total < 1:
        return f"{where}: failed_count/total_count out of range"
    if failed > total:
        return f"{where}: failed_count {failed} exceeds total_count {total}"
    if max_abs < 0.0 or max_rel < 0.0:
        return f"{where}: negative error maximum"
    if expected_total is not None and total != expected_total:
        return (
            f"{where}: total_count {total} is not the {expected_total} the "
            "registered case shape implies"
        )
    if within != (failed == 0):
        return f"{where}: within_tolerance {within} contradicts failed_count {failed}"
    if not within and max_abs <= atol:
        return (
            f"{where}: reported breach with max_abs_diff {max_abs!r} at or "
            f"below atol {atol!r}, which the registered isclose rule cannot "
            "produce"
        )
    if max_abs == 0.0 and max_rel != 0.0:
        return f"{where}: zero max_abs_diff with nonzero max_rel_diff {max_rel!r}"
    return None


def _quantity_for(array_name: str) -> str:
    """Return the registered quantity label for one CPU comparison array.

    Args:
        array_name: A corpus or fuzz comparison array name.

    Returns:
        ``"metric"`` for the two bounded coherence trajectories, else
        ``"trajectory"``.
    """
    return "metric" if array_name in METRIC_ARRAY_NAMES else "trajectory"


def _verify_comparison_list(
    records: Any,
    *,
    names: Sequence[str],
    totals: dict[str, int] | None,
    atol_for: Callable[[str], float],
    quantity_of: Callable[[str], str | None],
    context: str,
) -> list[dict[str, Any]]:
    """Verify one case's whole comparison list against its registered shape.

    Args:
        records: The stored ``comparisons``-style list.
        names: The exact array names, in order, this comparison class carries.
        totals: Per-array expected element counts, or ``None`` to skip.
        atol_for: Callable mapping an array name to its registered ``atol``.
        quantity_of: Callable mapping an array name to its registered quantity
            label, or ``None`` when the records carry no quantity.
        context: Human-readable location, for the failure message.

    Returns:
        The verified comparison records.

    Raises:
        AnalysisError: If the list is absent, mis-shaped, mis-ordered, or any
            record fails :func:`_comparison_violation`.
    """
    stored = _as_list(records, f"{context}: comparison list")
    if len(stored) != len(names):
        raise AnalysisError(
            f"{context}: {len(stored)} comparison records, expected {len(names)}"
        )
    verified: list[dict[str, Any]] = []
    for position, expected_name in enumerate(names):
        expected_total = None if totals is None else totals[expected_name]
        violation = _comparison_violation(
            stored[position],
            expected_name=expected_name,
            expected_total=expected_total,
            expected_quantity=quantity_of(expected_name),
            atol=atol_for(expected_name),
            context=context,
        )
        if violation is not None:
            raise AnalysisError(violation)
        verified.append(_as_dict(stored[position], context))
    return verified


def _cpu_atol(array_name: str) -> float:
    """Return the registered absolute tolerance for one CPU comparison array.

    Args:
        array_name: A corpus or fuzz comparison array name.

    Returns:
        The trajectory or metric ``atol``.
    """
    return QUANTITY_TOLERANCE[_quantity_for(array_name)][1]


def _kernel_atol(array_name: str) -> float:
    """Return the registered float32 kernel absolute tolerance.

    Args:
        array_name: One of :data:`KERNEL_ARRAY_NAMES` (unused; the bound is the
            same for all three derivative arrays).

    Returns:
        ``atol=1e-6``, the unchanged Testing Standards §3 bound.
    """
    del array_name
    return legacy.KERNEL_ATOL


def _no_quantity(array_name: str) -> str | None:
    """Return ``None``: the kernel comparator records carry no quantity label.

    Args:
        array_name: One of :data:`KERNEL_ARRAY_NAMES` (unused).

    Returns:
        ``None``.
    """
    del array_name
    return None


def _expected_totals(
    n_oscillators: int, horizon: int, *, with_final: bool
) -> dict[str, int]:
    """Return the registered per-array element counts for one CPU case.

    Args:
        n_oscillators: The case's ``N``.
        horizon: The number of integration steps the comparison covers.
        with_final: Whether the inventory includes the ``*_final`` arrays
            (full-corpus comparisons do; within-horizon fuzz comparisons do
            not).

    Returns:
        Array name to expected ``total_count``.
    """
    totals: dict[str, int] = {
        name: n_oscillators
        for name in ("phase_init", "amplitude_init", "frequency_init")
    }
    if with_final:
        for name in ("phase_final", "amplitude_final", "frequency_final"):
            totals[name] = n_oscillators
    for name in ("phase_traj", "amplitude_traj", "frequency_traj"):
        totals[name] = n_oscillators * (horizon + 1)
    for name in legacy._BEYOND_HORIZON_ARRAY_NAMES:
        totals[name] = horizon + 1
    return totals


def _reclassify_pointwise(
    case: dict[str, Any], *, ill_conditioned: bool
) -> dict[str, Any]:
    """Recompute §5.3/§5.4's classification from the retained per-array records.

    This is §8 rule 2's re-evaluation. The stored ``classification``,
    ``accepted``, ``pointwise_eligible`` and ``native_within_tolerance`` fields
    are treated as claims; the retained comparison lists are the evidence, and
    :func:`_verify_pointwise_case` requires the two to agree.

    Args:
        case: A non-aborted corpus or fuzz case record.
        ill_conditioned: Whether this case is one of the fixed 22 registered
            reference-sensitivity indices.

    Returns:
        The recomputed decision fields.

    Raises:
        AnalysisError: If an eligible-path breach retained no corrected
            reference comparison, or an ill-conditioned case retained no
            sensitivity witness — §4.2 item 2 makes that characterization
            unavailable rather than silently counting it as a pass.
    """
    comparisons = _as_list(case.get("comparisons"), "comparisons")
    native_ok = all(bool(item["within_tolerance"]) for item in comparisons)
    if ill_conditioned:
        sensitivity = case.get("sensitivity_comparisons")
        if not isinstance(sensitivity, list) or not sensitivity:
            raise AnalysisError(
                f"case {case.get('case_index')!r}: registered reference-"
                "sensitivity witness is missing, so its characterization is "
                "unavailable (§4.2 item 2)"
            )
        return {
            "pointwise_eligible": False,
            "accepted": None,
            "classification": "ill-conditioned-characterization",
            "native_within_tolerance": native_ok,
            "sensitivity_reproduced": any(
                not bool(item["within_tolerance"]) for item in sensitivity
            ),
        }
    if native_ok:
        return {
            "pointwise_eligible": True,
            "accepted": True,
            "classification": "native-parity",
            "native_within_tolerance": True,
        }
    # The driver's own registered path predicate, imported rather than restated
    # so exactly one implementation decides DV-007 eligibility. A model name or
    # a historical case ID alone cannot excuse a breach (§5.3 step 3).
    if not r1._dv007({"model": case["model"], "coupling": case["coupling"]}):
        return {
            "pointwise_eligible": True,
            "accepted": False,
            "classification": "unexplained-breach",
            "native_within_tolerance": False,
        }
    corrected = case.get("f64_comparisons")
    if not isinstance(corrected, list) or not corrected:
        raise AnalysisError(
            f"case {case.get('case_id', case.get('case_index'))!r}: native "
            "breach on a DV-007-eligible path retained no float64-reference "
            "comparison, so §5.3 step 5 cannot be evaluated"
        )
    corrected_ok = all(bool(item["within_tolerance"]) for item in corrected)
    return {
        "pointwise_eligible": True,
        "accepted": corrected_ok,
        "classification": ("explained-dv007" if corrected_ok else "unexplained-breach"),
        "native_within_tolerance": False,
    }


def _verify_pointwise_case(
    case: dict[str, Any], *, ill_conditioned: bool, fuzz: bool
) -> None:
    """Verify one corpus/fuzz case record and its stored decision fields.

    Args:
        case: The stored case record.
        ill_conditioned: Whether this is one of the fixed 22 registered
            sensitivity indices.
        fuzz: Whether the case comes from the within-horizon fuzz leg (eight
            horizon-sliced arrays and an explicit ``horizon``) rather than the
            full-corpus leg (eleven arrays).

    Raises:
        AnalysisError: If the case is structurally invalid, carries a
            non-finite scientific field, or its stored decision fields disagree
            with the recomputation from its retained comparisons.
    """
    key = str(case.get("case_id", case.get("case_index")))
    context = f"case {key}"
    _require(
        isinstance(case.get("aborted"), bool), f"{context}: aborted must be a bool"
    )
    if case["aborted"]:
        _require(
            isinstance(case.get("abort_reason"), str)
            and bool(case["abort_reason"].strip()),
            f"{context}: aborted case must carry a non-empty abort_reason",
        )
        return
    for field in ("model", "coupling", "integrator"):
        _require(
            isinstance(case.get(field), str) and bool(case[field]),
            f"{context}: {field} must be a non-empty string",
        )
    n_oscillators = _required_int(
        case.get("n_oscillators"), f"{context}: n_oscillators"
    )
    n_steps = _required_int(case.get("n_steps"), f"{context}: n_steps")
    _finite_float(case.get("dt"), f"{context}: dt")
    _require(n_oscillators >= 1 and n_steps >= 1, f"{context}: non-positive shape")
    if fuzz:
        horizon = _required_int(case.get("horizon"), f"{context}: horizon")
        _require(
            horizon == min(legacy.T_STAR, n_steps),
            f"{context}: horizon {horizon} is not min(T_STAR, n_steps)",
        )
    else:
        _require(
            "horizon" not in case,
            f"{context}: a full-corpus comparison carries no horizon",
        )
        horizon = n_steps
    names = FUZZ_ARRAY_NAMES if fuzz else CORPUS_ARRAY_NAMES
    totals = _expected_totals(n_oscillators, horizon, with_final=not fuzz)
    _verify_comparison_list(
        case.get("comparisons"),
        names=names,
        totals=totals,
        atol_for=_cpu_atol,
        quantity_of=_quantity_for,
        context=f"{context} native",
    )
    for kind in ("f64_comparisons", "sensitivity_comparisons"):
        if case.get(kind) is None:
            continue
        _verify_comparison_list(
            case[kind],
            names=names,
            totals=totals,
            atol_for=_cpu_atol,
            quantity_of=_quantity_for,
            context=f"{context} {kind}",
        )
    recomputed = _reclassify_pointwise(case, ill_conditioned=ill_conditioned)
    for field, expected in recomputed.items():
        _require(
            field in case,
            f"{context}: stored record is missing the registered {field} field",
        )
        _require(
            case[field] == expected,
            f"{context}: stored {field} {case[field]!r} is not reproduced by "
            f"the retained per-array records ({expected!r}) — §8 rule 2",
        )
    if ill_conditioned:
        _require(
            case.get("sensitivity_reproduced") is True,
            f"{context}: registered reference sensitivity was not reproduced, "
            "so this characterization is unavailable (§5.4)",
        )
    needs_f64 = ill_conditioned or (
        not bool(recomputed["native_within_tolerance"])
        and r1._dv007({"model": case["model"], "coupling": case["coupling"]})
    )
    _require(
        (case.get("f64_comparisons") is not None) == needs_f64,
        f"{context}: float64-reference evidence presence "
        f"{case.get('f64_comparisons') is not None} contradicts the registered "
        f"collection rule ({needs_f64})",
    )
    _require(
        ("sensitivity_comparisons" in case) == ill_conditioned,
        f"{context}: sensitivity evidence is present exactly for the fixed 22 "
        "registered indices",
    )


def _corpus_case_ids(repository_root: Path) -> list[str]:
    """Return the registered 504 corpus case IDs from the pinned corpus.

    Also re-verifies the corpus manifest's SHA-256 against the frozen pin, so
    the inventory H1 and H4 are adjudicated against is provably the registered
    population and not whatever happens to be on disk.

    Args:
        repository_root: Repository root.

    Returns:
        Every corpus case ID, in manifest order.

    Raises:
        AnalysisError: If the corpus manifest digest differs from the
            registered pin, or the corpus does not hold exactly 504 cases.
    """
    corpus_dir = repository_root / CORPUS_DIR
    digest = hashlib.sha256(
        read_no_follow(corpus_dir / "manifest.json", "corpus manifest")
    ).hexdigest()
    _require(
        digest == r1.CORPUS_SHA256,
        f"corpus manifest SHA-256 {digest} is not the registered {r1.CORPUS_SHA256}",
    )
    loader = CorpusLoader(corpus_dir)
    _require(
        len(loader) == H1_DENOMINATOR,
        f"registered corpus holds {len(loader)} cases, expected {H1_DENOMINATOR}",
    )
    return [row.case_id for row in loader.manifest.cases]


def _kernel_case_ids(repository_root: Path) -> list[str]:
    """Return the 72 ``kuramoto_sparse_knn_*`` case IDs H4 registers.

    Args:
        repository_root: Repository root.

    Returns:
        The H4 case population, in manifest order.
    """
    loader = CorpusLoader(repository_root / CORPUS_DIR)
    return [
        row.case_id
        for row in loader.manifest.cases
        if row.model == "kuramoto" and row.coupling == "sparse_knn"
    ]


def verify_corpus_cases(run: LoadedRun, expected_ids: Sequence[str]) -> None:
    """Verify the H1 corpus leg's complete case inventory and every case.

    Args:
        run: The loaded ``r1-corpus-cpu`` run.
        expected_ids: The registered 504 corpus case IDs, in manifest order.

    Raises:
        AnalysisError: If the case IDs are not exactly the registered
            population in order and unique, or any case record is invalid.
    """
    actual = [str(case.get("case_id")) for case in run.cases]
    _require(
        len(actual) == H1_DENOMINATOR,
        f"{run.leg.run_id}: {len(actual)} corpus cases, expected {H1_DENOMINATOR}",
    )
    _require(
        actual == list(expected_ids),
        f"{run.leg.run_id}: corpus case inventory does not match the "
        "registered 504-case manifest population in order",
    )
    _require(
        len(set(actual)) == H1_DENOMINATOR,
        f"{run.leg.run_id}: duplicate corpus case IDs",
    )
    for case in run.cases:
        _verify_pointwise_case(case, ill_conditioned=False, fuzz=False)


def verify_corpus_population(run: LoadedRun, repository_root: Path) -> None:
    """Verify the H1 corpus leg against the pinned corpus inventory.

    Args:
        run: The loaded ``r1-corpus-cpu`` run.
        repository_root: Repository root.

    Raises:
        AnalysisError: If the corpus fingerprint or inventory check in
            :func:`_corpus_case_ids` fails, or any case record is invalid.
    """
    verify_corpus_cases(run, _corpus_case_ids(repository_root))


def verify_fuzz_population(run: LoadedRun) -> None:
    """Verify the H2 fuzz leg's inventory, every case, and its pinned input stream.

    The 1,000 pinned draws are replayed from the campaign's single registered
    randomness authority and their digest is required to equal the frozen
    ``h2a_stream_digest`` pin; each case's own ``input_sha256`` and every
    recorded spec field is then required to equal the replayed draw at that
    index. This verifies the *input* fingerprint and inventory only — no
    trajectory is re-integrated (§8 rule 2).

    Args:
        run: The loaded ``r1-fuzz-cpu`` run.

    Raises:
        AnalysisError: If the stream digest, the per-case input digests, the
            index inventory, or any case record disagrees with the registered
            population.
    """
    cases = run.cases
    _require(
        len(cases) == H2A_DENOMINATOR,
        f"{run.leg.run_id}: {len(cases)} fuzz cases, expected {H2A_DENOMINATOR}",
    )
    indices = [_required_int(case.get("case_index"), "case_index") for case in cases]
    _require(
        indices == list(range(H2A_DENOMINATOR)),
        f"{run.leg.run_id}: fuzz case_index values are not exactly 0..999 in "
        "registered order and unique",
    )
    stream = r1._draw_stream()
    _require(
        len(stream) == H2A_DENOMINATOR,
        f"replayed fuzz stream has {len(stream)} draws, expected {H2A_DENOMINATOR}",
    )
    digest = legacy.h2a_stream_digest(stream)
    _require(
        digest == r1.STREAM_SHA256,
        f"replayed fuzz stream digest {digest} is not the registered "
        f"{r1.STREAM_SHA256}",
    )
    for index, drawn in enumerate(stream):
        case = cases[index]
        spec, phase, amplitude, frequency = drawn
        expected_input = legacy.h2a_stream_digest([(spec, phase, amplitude, frequency)])
        _require(
            case.get("input_sha256") == expected_input,
            f"{run.leg.run_id} case_index {index}: input_sha256 does not match "
            "the pinned stream draw",
        )
        for field in (
            "model",
            "coupling",
            "integrator",
            "n_oscillators",
            "n_steps",
            "dt",
            "parameters",
        ):
            _require(
                case.get(field) == spec[field],
                f"{run.leg.run_id} case_index {index}: recorded {field} does "
                "not match the pinned stream draw",
            )
        _verify_pointwise_case(
            case, ill_conditioned=index in r1.ILL_CONDITIONED, fuzz=True
        )


def _array_digest_names() -> tuple[str, ...]:
    """Return the array names H3's per-array digests must cover.

    Returns:
        The registered ``CaseArrays`` array names, sorted.
    """
    return tuple(sorted(CORPUS_ARRAY_NAMES))


def verify_repeatability_population(run: LoadedRun) -> None:
    """Verify one H3 leg's 14-case inventory and its retained byte evidence.

    Args:
        run: A loaded ``repeatability`` run.

    Raises:
        AnalysisError: If the case IDs are not exactly the 14 registered
            representatives, a case is structurally invalid, or its two
            retained digest maps disagree with its ``bit_identical`` and
            ``mismatched_arrays`` claims.
    """
    expected = sorted(r1.REPEATABILITY_CASES)
    actual = sorted(str(case.get("case_id")) for case in run.cases)
    _require(
        len(run.cases) == H3_DENOMINATOR,
        f"{run.leg.run_id}: {len(run.cases)} repeatability cases, expected "
        f"{H3_DENOMINATOR}",
    )
    _require(
        actual == expected,
        f"{run.leg.run_id}: repeatability case inventory is not exactly the 14 "
        "registered representatives",
    )
    names = list(_array_digest_names())
    for case in run.cases:
        key = str(case.get("case_id"))
        where = f"{run.leg.run_id} case {key}"
        _require(
            isinstance(case.get("aborted"), bool), f"{where}: aborted must be a bool"
        )
        if case["aborted"]:
            _require(
                isinstance(case.get("abort_reason"), str)
                and bool(case["abort_reason"].strip()),
                f"{where}: aborted case must carry an abort_reason",
            )
            continue
        digests: dict[str, dict[str, Any]] = {}
        for label in ("first", "second"):
            stored = _as_dict(
                case.get(f"{label}_array_sha256"), f"{where}: {label}_array_sha256"
            )
            _require(
                sorted(stored) == names,
                f"{where}: {label}_array_sha256 must cover exactly the "
                "registered array names",
            )
            _require(
                all(
                    isinstance(value, str) and len(value) == 64
                    for value in stored.values()
                ),
                f"{where}: {label}_array_sha256 must hold SHA-256 hex digests",
            )
            digests[label] = stored
        mismatched = _as_list(
            case.get("mismatched_arrays"), f"{where}: mismatched_arrays"
        )
        _require(
            all(isinstance(name, str) for name in mismatched),
            f"{where}: mismatched_arrays must be a list of array names",
        )
        recomputed = sorted(
            name for name in names if digests["first"][name] != digests["second"][name]
        )
        _require(
            sorted(mismatched) == recomputed,
            f"{where}: mismatched_arrays {mismatched!r} is not reproduced by "
            f"the retained digests {recomputed!r}",
        )
        _require(
            isinstance(case.get("bit_identical"), bool)
            and case["bit_identical"] == (not recomputed),
            f"{where}: bit_identical {case.get('bit_identical')!r} contradicts "
            "the retained per-array digests",
        )


def _repeatability_projection(payload: dict[str, Any]) -> str:
    """Return one repeatability run's canonical scientific projection.

    §8 rule 6 removes **only** ``environment``, ``config.out_dir`` and any
    per-run ``run_id``; no scientific field and no array digest is removed.

    Args:
        payload: The parsed result artefact.

    Returns:
        The canonical JSON text of the projection.
    """

    def strip(value: Any) -> Any:
        """Recursively drop ``run_id`` keys from one projection value."""
        if isinstance(value, dict):
            return {key: strip(item) for key, item in value.items() if key != "run_id"}
        if isinstance(value, list):
            return [strip(item) for item in value]
        return value

    projection = strip(payload)
    projection.pop("environment", None)
    config = projection.get("config")
    if isinstance(config, dict):
        config.pop("out_dir", None)
    return json.dumps(projection, sort_keys=True, ensure_ascii=True, allow_nan=False)


def verify_kernel_cases(run: LoadedRun, expected_ids: Sequence[str]) -> None:
    """Verify one H4 leg's 72-case inventory, comparator records and proofs.

    Args:
        run: A loaded ``kernel-path`` run.
        expected_ids: The registered 72 ``kuramoto_sparse_knn_*`` case IDs, in
            manifest order.

    Raises:
        AnalysisError: If the case IDs are not exactly the registered
            population, a comparator record is internally inconsistent, or a
            per-case backend proof is absent or conflicts with the leg's
            registered backend (§8 rules 1 and 7).
    """
    actual = [str(case.get("case_id")) for case in run.cases]
    _require(
        len(actual) == H4_DENOMINATOR,
        f"{run.leg.run_id}: {len(actual)} kernel-path cases, expected {H4_DENOMINATOR}",
    )
    _require(
        actual == list(expected_ids),
        f"{run.leg.run_id}: kernel-path case inventory does not match the "
        "registered 72 kuramoto/sparse_knn corpus cases in order",
    )
    _require(
        len(set(actual)) == H4_DENOMINATOR,
        f"{run.leg.run_id}: duplicate kernel-path case IDs",
    )
    required_device = "cuda" if run.leg.backend == "cuda" else "cpu"
    for case in run.cases:
        key = str(case.get("case_id"))
        context = f"{run.leg.run_id} case {key}"
        _require(
            case.get("model") == "kuramoto" and case.get("coupling") == "sparse_knn",
            f"{context}: H4 requires a kuramoto/sparse_knn case",
        )
        n_oscillators = _required_int(
            case.get("n_oscillators"), f"{context}: n_oscillators"
        )
        _required_int(case.get("sparse_k"), f"{context}: sparse_k")
        _require(
            isinstance(case.get("aborted"), bool),
            f"{context}: aborted must be a bool",
        )
        devices = _as_dict(case.get("dlpack_devices"), f"{context}: dlpack_devices")
        _require(
            sorted(devices) == sorted(KERNEL_ARRAY_NAMES)
            and all(devices[name] == required_device for name in KERNEL_ARRAY_NAMES),
            f"{context}: dlpack_devices {devices!r} must retain all three "
            f"capsules and each must be {required_device!r} on a "
            f"{run.leg.backend} leg (§8 rule 1)",
        )
        if run.leg.backend == "wgpu":
            backend_name = case.get("backend_name")
            _require(
                isinstance(backend_name, str) and backend_name.startswith("wgpu"),
                f"{context}: backend_name {backend_name!r} read after dispatch "
                "does not report the wgpu backend family; a non-wgpu or absent "
                "getter is a backend abort, never a passing case",
            )
        else:
            _require(
                "backend_name" not in case,
                f"{context}: a CUDA record must not carry a wgpu backend_name",
            )
        if case["aborted"]:
            _require(
                isinstance(case.get("abort_reason"), str)
                and bool(case["abort_reason"].strip()),
                f"{context}: aborted case must carry an abort_reason",
            )
            continue
        comparisons = _verify_comparison_list(
            case.get("comparisons"),
            names=KERNEL_ARRAY_NAMES,
            totals={name: n_oscillators for name in KERNEL_ARRAY_NAMES},
            atol_for=_kernel_atol,
            quantity_of=_no_quantity,
            context=f"{context} kernel",
        )
        _require(
            isinstance(case.get("within_tolerance"), bool)
            and case["within_tolerance"]
            == all(bool(item["within_tolerance"]) for item in comparisons),
            f"{context}: case within_tolerance contradicts its three retained "
            "comparator records",
        )


def verify_kernel_population(run: LoadedRun, repository_root: Path) -> None:
    """Verify one H4 leg against the pinned corpus's sparse k-NN inventory.

    Args:
        run: A loaded ``kernel-path`` run.
        repository_root: Repository root.

    Raises:
        AnalysisError: If the corpus fingerprint check in
            :func:`_kernel_case_ids` fails, or any case or proof is invalid.
    """
    verify_kernel_cases(run, _kernel_case_ids(repository_root))


def verify_h2b_summaries(cases: Sequence[dict[str, Any]]) -> int:
    """Recompute H2b's registered per-case summaries from the stored arrays.

    §8 rule 2 requires the registered summaries to be recomputed from the
    stored paired metric arrays *before* the committed statistical helper is
    applied, so the bootstrap operates on values this analysis has itself
    derived rather than on a stored claim. The stored ``reference_mean``,
    ``produced_mean`` and ``mean_paired_difference`` must be reproduced
    exactly: the arrays round-trip through JSON as binary64 and ``np.mean`` is
    deterministic for a fixed array, so any difference is a real discrepancy
    and not a floating-point artefact.

    Args:
        cases: The verified fuzz case records.

    Returns:
        The number of contributing cases (``n_steps > T_STAR``).

    Raises:
        AnalysisError: If a case's ``beyond_horizon`` presence contradicts its
            step count, a stored array is mis-shaped or non-finite, or a stored
            summary is not exactly reproduced.
    """
    contributors = 0
    for case in cases:
        key = str(case.get("case_index"))
        if case.get("aborted"):
            # An aborted case contributes nothing to H2b whatever its step
            # count, and §7 makes any abort render the metric inconclusive
            # through the driver's own completeness check.
            continue
        n_steps = _required_int(case.get("n_steps"), f"fuzz case {key}: n_steps")
        beyond = case.get("beyond_horizon")
        if n_steps <= legacy.T_STAR:
            _require(
                beyond is None,
                f"fuzz case {key}: beyond_horizon present with n_steps "
                f"{n_steps} <= T_STAR {legacy.T_STAR}",
            )
            continue
        contributors += 1
        metrics = _as_dict(beyond, f"fuzz case {key}: beyond_horizon")
        _require(
            sorted(metrics) == sorted(legacy._BEYOND_HORIZON_ARRAY_NAMES),
            f"fuzz case {key}: beyond_horizon must carry exactly the two "
            "registered coherence metrics",
        )
        expected_points = n_steps - legacy.T_STAR
        for metric in legacy._BEYOND_HORIZON_ARRAY_NAMES:
            where = f"fuzz case {key}/{metric}"
            record = _as_dict(metrics[metric], where)
            reference = _as_list(record.get("reference"), f"{where}: reference")
            produced = _as_list(record.get("produced"), f"{where}: produced")
            _require(
                len(reference) == len(produced) == expected_points,
                f"{where}: {len(reference)}/{len(produced)} stored points, "
                f"expected {expected_points} beyond step {legacy.T_STAR}",
            )
            _require(
                _required_int(record.get("n_points"), f"{where}: n_points")
                == expected_points,
                f"{where}: n_points disagrees with the stored array length",
            )
            ref = np.asarray(reference, dtype=np.float64)
            prod = np.asarray(produced, dtype=np.float64)
            if not (bool(np.all(np.isfinite(ref))) and bool(np.all(np.isfinite(prod)))):
                raise AnalysisError(
                    f"{where}: non-finite paired metric value (§8 rule 1)"
                )
            for field, recomputed in (
                ("reference_mean", float(np.mean(ref))),
                ("produced_mean", float(np.mean(prod))),
                ("mean_paired_difference", float(np.mean(prod - ref))),
            ):
                stored = _finite_float(record.get(field), f"{where}: {field}")
                _require(
                    stored == recomputed,
                    f"{where}: stored {field} {stored!r} is not exactly "
                    f"reproduced from the stored paired arrays "
                    f"({recomputed!r}) — §8 rule 2",
                )
    return contributors


def _decade_histogram(values: Iterable[float]) -> dict[str, int]:
    """Bucket magnitudes by power of ten, exactly and without estimation.

    ``0.0`` gets its own ``"0"`` bucket (a decade is undefined there) and any
    non-finite magnitude gets ``"non-finite"``; every other value falls in
    ``"1e<k>"`` where ``k = floor(log10(v))``. Counts are exact, so this is a
    faithful distribution report and introduces no estimator (campaign plan
    §9.1/§9.2).

    Args:
        values: Non-negative error magnitudes.

    Returns:
        Bucket label to count, ordered by increasing magnitude.
    """
    counts: Counter[str] = Counter()
    for value in values:
        if value == 0.0:
            counts["0"] += 1
        elif not isfinite(value):
            counts["non-finite"] += 1
        else:
            counts[f"1e{floor(log10(value))}"] += 1

    def order(label: str) -> tuple[int, float]:
        """Sort ``0`` first, decades by exponent, ``non-finite`` last."""
        if label == "0":
            return (0, 0.0)
        if label == "non-finite":
            return (2, 0.0)
        return (1, float(label[2:]))

    return {label: counts[label] for label in sorted(counts, key=order)}


def _partition(
    cases: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split a case population into non-aborted and aborted lists.

    An aborted case is excluded from every pass/fail count (§8) and reported
    through its ``abort_reason`` instead. Invalid does not mean scientifically
    harmless: §4.2 requires aborts to be reported distinctly, and a partial
    denominator can never confirm a hypothesis.

    Args:
        cases: The run's verified case records.

    Returns:
        ``(non_aborted, aborted)``.
    """
    return (
        [case for case in cases if not case["aborted"]],
        [case for case in cases if case["aborted"]],
    )


def _abort_reasons(aborted: Sequence[dict[str, Any]]) -> list[str]:
    """Collect the distinct abort reasons of a population.

    Args:
        aborted: Aborted case records.

    Returns:
        Sorted distinct reasons; empty when nothing aborted.
    """
    return sorted({str(case.get("abort_reason", "")) for case in aborted})


def _classification_counts(cases: Sequence[dict[str, Any]]) -> dict[str, int]:
    """Count each registered classification over a pointwise population.

    Args:
        cases: Non-aborted corpus or fuzz case records.

    Returns:
        Classification to count, over the four registered labels, always
        present so the denominators in ``summary.json`` are explicit.
    """
    counts: Counter[str] = Counter(str(case.get("classification")) for case in cases)
    return {
        label: counts.get(label, 0)
        for label in (
            "native-parity",
            "explained-dv007",
            "unexplained-breach",
            "ill-conditioned-characterization",
        )
    }


def _breach_breakdown(cases: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Count breaching arrays and grid cells among unexplained-breach cases.

    Args:
        cases: Non-aborted cases classified ``unexplained-breach``.

    Returns:
        Per-array and per-``(model, coupling, integrator)`` counts. Descriptive
        only — campaign plan §10.4 assigns diagnosis to the correction cycle.
    """
    arrays: Counter[str] = Counter()
    cells: Counter[str] = Counter()
    for case in cases:
        cell = "/".join(
            str(case.get(key, "?")) for key in ("model", "coupling", "integrator")
        )
        cells[cell] += 1
        for comparison in _as_list(case.get("comparisons"), "comparisons"):
            if not comparison["within_tolerance"]:
                arrays[str(comparison["array_name"])] += 1
    return {
        "breaching_arrays": dict(sorted(arrays.items())),
        "breaching_cells": dict(sorted(cells.items())),
    }


def adjudicate_h1(run: LoadedRun) -> dict[str, Any]:
    """Adjudicate H1 on §8 rule 3: the 504-case corpus with §5.3's explanation.

    ``REFUTED`` on any valid unexplained breach; ``CONFIRMED`` only with 504
    valid accepted cases; incomplete valid coverage is ``INCONCLUSIVE``. Native
    passes, explained divergences, unexplained breaches and aborts are published
    separately, as §2 requires — confirmation is not a claim that every native
    PRINet array was reproduced within tolerance.

    Args:
        run: The verified ``r1-corpus-cpu`` run.

    Returns:
        The H1 adjudication record.
    """
    non_aborted, aborted = _partition(run.cases)
    unexplained = [
        case for case in non_aborted if case["classification"] == "unexplained-breach"
    ]
    accepted = [case for case in non_aborted if case.get("accepted") is True]
    counts = _classification_counts(non_aborted)
    if unexplained:
        verdict = "REFUTED"
    elif (
        len(run.cases) == H1_DENOMINATOR
        and len(non_aborted) == H1_DENOMINATOR
        and len(accepted) == H1_DENOMINATOR
    ):
        verdict = "CONFIRMED"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "hypothesis": "H1",
        "description": (
            "Full-corpus parity with the registered DV-007 explanation — 504 "
            "golden-corpus cases across all 11 arrays"
        ),
        "verdict": verdict,
        "full_denominator": H1_DENOMINATOR,
        "n_cases": len(run.cases),
        "n_non_aborted": len(non_aborted),
        "n_aborted": len(aborted),
        "abort_reasons": _abort_reasons(aborted),
        "n_accepted": len(accepted),
        "n_native_parity": counts["native-parity"],
        "n_explained_dv007": counts["explained-dv007"],
        "n_unexplained_breach": counts["unexplained-breach"],
        "tolerance": (
            f"trajectory {TOLERANCES['trajectory']}; metric {TOLERANCES['metric']}"
        ),
        "breaches": _breach_breakdown(unexplained),
        "n_failing": len(unexplained),
        "unexplained_breach_case_ids": sorted(
            str(case["case_id"]) for case in unexplained
        ),
        "explained_dv007_case_ids": sorted(
            str(case["case_id"])
            for case in non_aborted
            if case["classification"] == "explained-dv007"
        ),
        "source_run": run.leg.run_id,
    }


def adjudicate_h2a(run: LoadedRun) -> dict[str, Any]:
    """Adjudicate H2a on §8 rule 4: ``978 pointwise + 22 characterized``.

    ``REFUTED`` on any valid eligible unexplained breach; ``CONFIRMED`` only
    with 978 valid accepted eligible cases **plus** all 22 valid registered
    characterizations. A missing or aborted sensitivity witness cannot reduce
    the registered denominator and yield confirmation, and no new exclusion may
    be selected from a PRIN error.

    Args:
        run: The verified ``r1-fuzz-cpu`` run.

    Returns:
        The H2a adjudication record.
    """
    non_aborted, aborted = _partition(run.cases)

    def is_ill(case: dict[str, Any]) -> bool:
        """Report whether one case is in the fixed 22-index sensitivity set."""
        return int(case["case_index"]) in r1.ILL_CONDITIONED

    eligible = [case for case in non_aborted if not is_ill(case)]
    characterized = [case for case in non_aborted if is_ill(case)]
    unexplained = [
        case for case in eligible if case["classification"] == "unexplained-breach"
    ]
    accepted = [case for case in eligible if case.get("accepted") is True]
    valid_characterizations = [
        case
        for case in characterized
        if case["classification"] == "ill-conditioned-characterization"
        and case.get("pointwise_eligible") is False
        and case.get("accepted") is None
        and case.get("sensitivity_reproduced") is True
    ]
    counts = _classification_counts(non_aborted)
    if unexplained:
        verdict = "REFUTED"
    elif (
        len(run.cases) == H2A_DENOMINATOR
        and not aborted
        and len(accepted) == H2A_ELIGIBLE_DENOMINATOR
        and len(valid_characterizations) == H2A_CHARACTERIZED_DENOMINATOR
    ):
        verdict = "CONFIRMED"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "hypothesis": "H2a",
        "description": (
            "Registered fuzz population within the comparison horizon — steps "
            "0..min(20, n_steps)"
        ),
        "verdict": verdict,
        "reported_as": (
            "978 pointwise + 22 characterized (never 1,000 pointwise passes)"
        ),
        "full_denominator": H2A_DENOMINATOR,
        "eligible_denominator": H2A_ELIGIBLE_DENOMINATOR,
        "characterized_denominator": H2A_CHARACTERIZED_DENOMINATOR,
        "n_cases": len(run.cases),
        "n_non_aborted": len(non_aborted),
        "n_aborted": len(aborted),
        "abort_reasons": _abort_reasons(aborted),
        "n_aborted_eligible": len([case for case in aborted if not is_ill(case)]),
        "n_aborted_characterized": len([case for case in aborted if is_ill(case)]),
        "n_eligible": len(eligible),
        "n_eligible_accepted": len(accepted),
        "n_failing": len(unexplained),
        "n_characterized": len(characterized),
        "n_valid_characterizations": len(valid_characterizations),
        "n_native_parity": counts["native-parity"],
        "n_explained_dv007": counts["explained-dv007"],
        "n_unexplained_breach": counts["unexplained-breach"],
        "n_ill_conditioned_characterization": counts[
            "ill-conditioned-characterization"
        ],
        "tolerance": (
            f"trajectory {TOLERANCES['trajectory']}; metric {TOLERANCES['metric']}"
        ),
        "breaches": _breach_breakdown(unexplained),
        "unexplained_breach_case_indices": sorted(
            int(case["case_index"]) for case in unexplained
        ),
        "characterized_case_indices": sorted(
            int(case["case_index"]) for case in valid_characterizations
        ),
        "source_run": run.leg.run_id,
    }


def adjudicate_h2b_leg(run: LoadedRun, contributors: int) -> dict[str, Any]:
    """Adjudicate H2b through the single committed r1 driver implementation.

    The registered three-way TOST-style predicate lives in
    :func:`benchmarks.campaign.exp001_r1_driver.adjudicate_h2b` precisely so
    that exactly one implementation exists and is covered by that module's
    tests (pre-registration §7). This wrapper adds identification and §8 rule
    5's completeness requirement only.

    Args:
        run: The verified ``r1-fuzz-cpu`` run.
        contributors: The contributing-case count :func:`verify_h2b_summaries`
            recomputed.

    Returns:
        The H2b adjudication record.
    """
    result = r1.adjudicate_h2b(list(run.cases))
    complete = len(run.cases) == H2A_DENOMINATOR and not any(
        case.get("aborted") for case in run.cases
    )
    return {
        "hypothesis": "H2b",
        "description": (
            "Beyond-horizon ensemble mean coherence equivalence — steps "
            "21..n_steps, per metric, against the unmodified PRINet 3.0 "
            "reference"
        ),
        "adjudicator": "benchmarks.campaign.exp001_r1_driver.adjudicate_h2b",
        "all_cases_accounted_for": complete,
        "n_cases": len(run.cases),
        "n_contributors": contributors,
        "min_contributors": legacy.H2B_MIN_CASES,
        "bootstrap_resamples": legacy.H2B_BOOTSTRAP_RESAMPLES,
        "alpha": legacy.H2B_ALPHA,
        "bootstrap_seed": r1.BOOTSTRAP_SEED,
        "verdict": result["verdict"] if complete else "INCONCLUSIVE",
        "driver_verdict": result["verdict"],
        "metrics": result["metrics"],
        "source_run": run.leg.run_id,
    }


def adjudicate_h3(first: LoadedRun, second: LoadedRun) -> dict[str, Any]:
    """Adjudicate H3 on §8 rule 6: byte identity within and between runs.

    Both runs' metadata validate independently (in :func:`load_run`); all 14
    cases in each must be byte-identical internally, recomputed here from the
    retained per-array digests rather than taken from ``bit_identical``; and the
    two canonical scientific result projections must agree after removing only
    ``environment``, ``config.out_dir`` and any per-run ``run_id``. Any valid
    mismatch refutes; missing or aborted coverage is inconclusive.

    Args:
        first: The verified ``r1-repeatability-cpu`` run.
        second: The verified ``r1-seedrep0-cpu`` run.

    Returns:
        The H3 adjudication record.
    """
    per_run: dict[str, Any] = {}
    internal_mismatch: list[str] = []
    aborted_total = 0
    for run in (first, second):
        non_aborted, aborted = _partition(run.cases)
        aborted_total += len(aborted)
        failing = [case for case in non_aborted if not case["bit_identical"]]
        internal_mismatch.extend(
            f"{run.leg.label}:{case['case_id']}" for case in failing
        )
        per_run[run.leg.label] = {
            "run_id": run.leg.run_id,
            "n_cases": len(run.cases),
            "n_non_aborted": len(non_aborted),
            "n_aborted": len(aborted),
            "abort_reasons": _abort_reasons(aborted),
            "n_bit_identical": len(non_aborted) - len(failing),
            "n_failing": len(failing),
            "mismatched_arrays": {
                str(case["case_id"]): list(case["mismatched_arrays"])
                for case in failing
            },
            "projection_sha256": hashlib.sha256(
                _repeatability_projection(run.payload).encode("utf-8")
            ).hexdigest(),
        }
    projections_equal = (
        per_run[first.leg.label]["projection_sha256"]
        == per_run[second.leg.label]["projection_sha256"]
    )
    complete = all(
        record["n_cases"] == H3_DENOMINATOR
        and record["n_non_aborted"] == H3_DENOMINATOR
        for record in per_run.values()
    )
    if internal_mismatch or not projections_equal:
        verdict = "REFUTED"
    elif complete and aborted_total == 0:
        verdict = "CONFIRMED"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "hypothesis": "H3",
        "description": (
            "CPU bit-level repeatability — 14 fixed representatives, twice "
            "within each invocation and across two separately manifested "
            "invocations"
        ),
        "verdict": verdict,
        "full_denominator": H3_DENOMINATOR,
        "tolerance": "byte-identical (dtype, shape, and raw bytes)",
        "runs": per_run,
        "n_aborted": aborted_total,
        "internal_mismatches": sorted(internal_mismatch),
        "projections_equal": projections_equal,
        "projection_comparison": (
            "canonical JSON of {cases, config} after removing only "
            "environment, config.out_dir and any run_id"
        ),
        "case_ids": sorted(str(case["case_id"]) for case in first.cases),
    }


def _h4_backend_record(run: LoadedRun) -> dict[str, Any]:
    """Summarize one H4 backend leg's verified coverage and comparator records.

    Args:
        run: A verified ``kernel-path`` run.

    Returns:
        The per-backend coverage record, including the retained proof values.
    """
    non_aborted, aborted = _partition(run.cases)
    failing = [case for case in non_aborted if not case["within_tolerance"]]
    maxima_abs: list[float] = []
    maxima_rel: list[float] = []
    failed_elements = 0
    for case in non_aborted:
        for comparison in _as_list(case.get("comparisons"), "comparisons"):
            maxima_abs.append(float(comparison["max_abs_diff"]))
            maxima_rel.append(float(comparison["max_rel_diff"]))
            failed_elements += int(comparison["failed_count"])
    environment = _as_dict(run.payload.get("environment"), "environment")
    config = _as_dict(run.payload.get("config"), "config")
    devices = sorted(
        {
            str(value)
            for case in run.cases
            for value in _as_dict(case.get("dlpack_devices"), "dlpack_devices").values()
        }
    )
    return {
        "label": run.leg.label,
        "run_id": run.leg.run_id,
        "backend": run.leg.backend,
        "environment_backend": str(environment.get("backend", "")),
        "dtype": str(environment.get("dtype", "")),
        "gpu": str(environment.get("gpu", "")),
        "gpu_vram_mb": environment.get("gpu_vram_mb"),
        "git_commit": str(environment.get("git_commit", "")),
        "prin_extension_sha256": str(config.get("prin_extension_sha256", "")),
        "timing_method": legacy.KERNEL_PATH_TIMING_METHOD,
        "full_denominator": H4_DENOMINATOR,
        "n_cases": len(run.cases),
        "n_non_aborted": len(non_aborted),
        "n_aborted": len(aborted),
        "abort_reasons": _abort_reasons(aborted),
        "n_pass": len(non_aborted) - len(failing),
        "n_fail": len(failing),
        "failed_derivative_elements": failed_elements,
        "max_abs_diff": max(maxima_abs, default=0.0),
        "max_rel_diff": max(maxima_rel, default=0.0),
        "abs_diff_decade_histogram": _decade_histogram(maxima_abs),
        "rel_diff_decade_histogram": _decade_histogram(maxima_rel),
        "backend_name_values": sorted(
            {str(case["backend_name"]) for case in run.cases if "backend_name" in case}
        ),
        "dlpack_device_values": devices,
        "failing_case_ids": sorted(str(case["case_id"]) for case in failing),
    }


def adjudicate_h4(wgpu: LoadedRun, cuda: LoadedRun) -> dict[str, Any]:
    """Adjudicate H4 on §8 rule 7: both 72-case backend proofs, never pooled.

    ``CONFIRMED`` requires all 72 non-aborted comparisons on **both** backends;
    any valid breach on either backend ``REFUTES`` H4 and is a D1; absent,
    invalid or partial coverage without a valid breach is ``INCONCLUSIVE``. A
    CUDA result never counts as the wgpu run.

    Args:
        wgpu: The verified ``r1-kernel-path-wgpu`` run.
        cuda: The verified ``r1-kernel-path-cuda`` run.

    Returns:
        The H4 adjudication record.
    """
    backends = {
        "cuda": _h4_backend_record(cuda),
        "wgpu": _h4_backend_record(wgpu),
    }
    breaches = sum(record["n_fail"] for record in backends.values())
    complete = all(
        record["n_cases"] == H4_DENOMINATOR
        and record["n_non_aborted"] == H4_DENOMINATOR
        for record in backends.values()
    )
    if breaches:
        verdict = "REFUTED"
    elif complete:
        verdict = "CONFIRMED"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "hypothesis": "H4",
        "description": (
            "CUDA and wgpu derivative-kernel agreement — the same 72 "
            "kuramoto_sparse_knn corpus cases on each backend against the same "
            "float64 Rust CPU reference"
        ),
        "verdict": verdict,
        "full_denominator": H4_DENOMINATOR,
        "denominator_per_backend": H4_DENOMINATOR,
        "n_fail_total": breaches,
        "pooled": False,
        "tolerance": TOLERANCES["kernel"],
        "re_evaluated_from_raw_arrays": False,
        "raw_derivative_arrays_retained": False,
        "verification": (
            "retained per-case comparator records checked for internal "
            "consistency against the registered rule, plus per-case "
            "dlpack_devices and (wgpu only) the post-dispatch backend_name; no "
            "independent isclose re-evaluation is claimed and no kernel was "
            "run (§8 rule 7)"
        ),
        "required_backend_coverage": {
            "required": ["cuda", "wgpu"],
            "present": sorted(backends),
            "distinct_run_ids": sorted({backends[name]["run_id"] for name in backends}),
            "distinct_environments": sorted(
                {backends[name]["environment_backend"] for name in backends}
            ),
            "distinct_extension_hashes": sorted(
                {backends[name]["prin_extension_sha256"] for name in backends}
            ),
        },
        "backends": backends,
    }


def adjudicate_all(runs: dict[str, LoadedRun], contributors: int) -> dict[str, Any]:
    """Adjudicate every registered hypothesis from the six verified runs.

    Args:
        runs: Run label to verified run.
        contributors: The H2b contributing-case count.

    Returns:
        Hypothesis identifier to adjudication record, in registered order.
    """
    return {
        "H1": adjudicate_h1(runs["r1-corpus-cpu"]),
        "H2a": adjudicate_h2a(runs["r1-fuzz-cpu"]),
        "H2b": adjudicate_h2b_leg(runs["r1-fuzz-cpu"], contributors),
        "H3": adjudicate_h3(runs["r1-repeatability-cpu"], runs["r1-seedrep0-cpu"]),
        "H4": adjudicate_h4(runs["r1-kernel-path-wgpu"], runs["r1-kernel-path-cuda"]),
    }


def is_d1(adjudications: dict[str, Any]) -> bool:
    """Report whether any hypothesis is a campaign plan §10.4 D1 reversal.

    Every r1 hypothesis is C1 parity, so *any* ``REFUTED`` verdict is a D1
    (pre-registration §4.1) and is escalated rather than rescued.

    Args:
        adjudications: The output of :func:`adjudicate_all`.

    Returns:
        ``True`` if at least one hypothesis is ``REFUTED``.
    """
    return any(record["verdict"] == "REFUTED" for record in adjudications.values())


def _case_key(case: dict[str, Any]) -> str:
    """Return one case's stable sort key for the error distributions.

    Args:
        case: A corpus, fuzz or kernel-path case record.

    Returns:
        The case ID, or ``fuzz-<index>`` for the fuzz population.
    """
    if "case_id" in case:
        return str(case["case_id"])
    return f"fuzz-{int(case['case_index']):04d}"


def _stratum_entries(
    cases: Sequence[dict[str, Any]], comparisons_key: str
) -> list[tuple[str, dict[str, Any]]]:
    """Pair each non-aborted case key with its retained comparison records.

    Args:
        cases: Verified case records.
        comparisons_key: ``comparisons``, ``f64_comparisons`` or
            ``sensitivity_comparisons``.

    Returns:
        ``(case_key, comparison_record)`` pairs, in case order.
    """
    entries: list[tuple[str, dict[str, Any]]] = []
    for case in cases:
        if case.get("aborted"):
            continue
        records = case.get(comparisons_key)
        if not isinstance(records, list):
            continue
        key = _case_key(case)
        entries.extend((key, _as_dict(record, key)) for record in records)
    return entries


@dataclass(frozen=True)
class _ArrayError:
    """One retained comparator record's errors, typed for deterministic sorting.

    Attributes:
        case: The owning case's stable sort key.
        array_name: The compared array.
        max_abs_diff: The retained maximum absolute difference.
        max_rel_diff: The retained maximum relative difference.
        failed_count: The retained count of out-of-tolerance elements.
        total_count: The retained element count.
        within_tolerance: The retained per-array decision.
    """

    case: str
    array_name: str
    max_abs_diff: float
    max_rel_diff: float
    failed_count: int
    total_count: int
    within_tolerance: bool


@dataclass(frozen=True)
class _CaseError:
    """One case's worst per-array errors, typed for deterministic sorting.

    Attributes:
        case: The owning case's stable sort key.
        max_abs_diff: The worst absolute difference over that case's arrays.
        max_rel_diff: The worst relative difference over that case's arrays.
    """

    case: str
    max_abs_diff: float
    max_rel_diff: float


def _error_stratum(
    name: str,
    population: str,
    comparison_kind: str,
    entries: Sequence[tuple[str, dict[str, Any]]],
) -> dict[str, Any]:
    """Build one registered error-distribution stratum, sorted and exact.

    Args:
        name: Stratum identifier.
        population: The registered population the stratum covers.
        comparison_kind: ``native``, ``corrected``, ``reference-sensitivity``
            or ``kernel``.
        entries: ``(case_key, comparison_record)`` pairs.

    Returns:
        Sorted per-array and per-case maxima, their extremes and exact decade
        histograms (campaign plan §9.1's registered reported statistics).
    """
    per_array = sorted(
        (
            _ArrayError(
                case=key,
                array_name=str(record["array_name"]),
                max_abs_diff=float(record["max_abs_diff"]),
                max_rel_diff=float(record["max_rel_diff"]),
                failed_count=int(record["failed_count"]),
                total_count=int(record["total_count"]),
                within_tolerance=bool(record["within_tolerance"]),
            )
            for key, record in entries
        ),
        key=lambda item: (-item.max_abs_diff, item.case, item.array_name),
    )
    worst_abs: dict[str, float] = {}
    worst_rel: dict[str, float] = {}
    for item in per_array:
        worst_abs[item.case] = max(worst_abs.get(item.case, 0.0), item.max_abs_diff)
        worst_rel[item.case] = max(worst_rel.get(item.case, 0.0), item.max_rel_diff)
    per_case = sorted(
        (
            _CaseError(
                case=key,
                max_abs_diff=worst_abs[key],
                max_rel_diff=worst_rel[key],
            )
            for key in worst_abs
        ),
        key=lambda item: (-item.max_abs_diff, item.case),
    )
    return {
        "stratum": name,
        "population": population,
        "comparison_kind": comparison_kind,
        "n_cases": len(per_case),
        "n_array_comparisons": len(per_array),
        "max_abs_diff": max(worst_abs.values(), default=0.0),
        "max_rel_diff": max(worst_rel.values(), default=0.0),
        "min_case_worst_abs_diff": min(worst_abs.values(), default=0.0),
        "min_case_worst_rel_diff": min(worst_rel.values(), default=0.0),
        "abs_diff_decade_histogram": _decade_histogram(worst_abs.values()),
        "rel_diff_decade_histogram": _decade_histogram(worst_rel.values()),
        "per_case_sorted": [asdict(item) for item in per_case],
        "per_array_sorted": [asdict(item) for item in per_array],
    }


def build_error_distributions(runs: dict[str, LoadedRun]) -> dict[str, Any]:
    """Build ``error-distributions.json`` (§8's fourth fixed output).

    Sorted per-case and per-array maximum absolute and relative errors,
    separated by native / corrected / reference-sensitivity comparison kind and
    by the eligible and characterized populations.

    Args:
        runs: Run label to verified run.

    Returns:
        The output payload.
    """
    corpus = runs["r1-corpus-cpu"].cases
    fuzz = runs["r1-fuzz-cpu"].cases

    def is_ill(case: dict[str, Any]) -> bool:
        """Report whether one fuzz case is a registered characterized case."""
        return int(case["case_index"]) in r1.ILL_CONDITIONED

    eligible = [case for case in fuzz if not is_ill(case)]
    characterized = [case for case in fuzz if is_ill(case)]
    strata: list[dict[str, Any]] = [
        _error_stratum(
            "corpus/native",
            "H1 — 504 corpus cases",
            "native",
            _stratum_entries(corpus, "comparisons"),
        ),
        _error_stratum(
            "corpus/corrected",
            "H1 — corpus cases on a DV-007-eligible breached path",
            "corrected",
            _stratum_entries(corpus, "f64_comparisons"),
        ),
        _error_stratum(
            "fuzz-eligible/native",
            "H2a — 978 eligible fuzz cases",
            "native",
            _stratum_entries(eligible, "comparisons"),
        ),
        _error_stratum(
            "fuzz-eligible/corrected",
            "H2a — eligible fuzz cases on a DV-007-eligible breached path",
            "corrected",
            _stratum_entries(eligible, "f64_comparisons"),
        ),
        _error_stratum(
            "fuzz-characterized/native",
            "H2a — the 22 registered ill-conditioned cases",
            "native",
            _stratum_entries(characterized, "comparisons"),
        ),
        _error_stratum(
            "fuzz-characterized/corrected",
            "H2a — the 22 registered ill-conditioned cases",
            "corrected",
            _stratum_entries(characterized, "f64_comparisons"),
        ),
        _error_stratum(
            "fuzz-characterized/reference-sensitivity",
            "H2a — one-ulp reference witness for the 22 characterized cases",
            "reference-sensitivity",
            _stratum_entries(characterized, "sensitivity_comparisons"),
        ),
    ]
    for backend in ("cuda", "wgpu"):
        run = runs[f"r1-kernel-path-{backend}"]
        strata.append(
            _error_stratum(
                f"kernel-{backend}/derivative",
                f"H4 — 72 sparse k-NN derivative cases on {backend}",
                "kernel",
                _stratum_entries(run.cases, "comparisons"),
            )
        )
    return {
        "experiment": EXPERIMENT_ID,
        "session": SESSION,
        "stage": "E4",
        "status": (
            f"{sum(int(s['n_array_comparisons']) for s in strata)} retained "
            f"comparator records over {len(strata)} registered strata"
        ),
        "note": (
            "Exact order statistics and decade counts only; no estimator is "
            "introduced (campaign plan §9.1/§9.2). Relative maxima inherit the "
            "+1e-300 guard in prin.parity.harness.compare_arrays, so a "
            "relative maximum is meaningless where the reference element is "
            "exactly zero; the registered pass/fail rule uses numpy.isclose "
            "and is unaffected."
        ),
        "strata": {str(stratum["stratum"]): stratum for stratum in strata},
    }


def _case_comparison_record(case: dict[str, Any], population: str) -> dict[str, Any]:
    """Project one case into ``case-comparisons.json``.

    Args:
        case: A verified case record.
        population: The registered population this case belongs to.

    Returns:
        The case's identity, decision fields and every retained comparison
        list, including breaches and aborts.
    """
    identity_keys = (
        "case_id",
        "case_index",
        "model",
        "coupling",
        "integrator",
        "n_oscillators",
        "n_steps",
        "dt",
        "horizon",
        "seed",
        "sparse_k",
        "parameters",
        "input_sha256",
    )
    evidence_keys = (
        "aborted",
        "abort_reason",
        "accepted",
        "classification",
        "pointwise_eligible",
        "native_within_tolerance",
        "sensitivity_reproduced",
        "within_tolerance",
        "bit_identical",
        "mismatched_arrays",
        "backend_name",
        "dlpack_devices",
    )
    comparison_keys = (
        "comparisons",
        "f64_comparisons",
        "sensitivity_comparisons",
        "first_array_sha256",
        "second_array_sha256",
    )
    record: dict[str, Any] = {"population": population}
    for key in (*identity_keys, *evidence_keys):
        if key in case:
            record[key] = case[key]
    for key in comparison_keys:
        if case.get(key) is not None:
            record[key] = case[key]
    return record


def build_case_comparisons(runs: dict[str, LoadedRun]) -> dict[str, Any]:
    """Build ``case-comparisons.json`` (§8's third fixed output).

    Every registered case and its native, corrected and reference-sensitivity
    comparison evidence, including every breach and every abort.

    Args:
        runs: Run label to verified run.

    Returns:
        The output payload, keyed by registered population.
    """
    fuzz = runs["r1-fuzz-cpu"].cases

    def is_ill(case: dict[str, Any]) -> bool:
        """Report whether one fuzz case is a registered characterized case."""
        return int(case["case_index"]) in r1.ILL_CONDITIONED

    def population(
        name: str, run_label: str, denominator: int, cases: Sequence[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build one registered population block of case comparison evidence."""
        return {
            "run_id": runs[run_label].leg.run_id,
            "denominator": denominator,
            "n_cases": len(cases),
            "cases": [_case_comparison_record(case, name) for case in cases],
        }

    populations: dict[str, Any] = {
        "h1-corpus": population(
            "h1-corpus", "r1-corpus-cpu", H1_DENOMINATOR, runs["r1-corpus-cpu"].cases
        ),
        "h2a-fuzz-eligible": population(
            "h2a-fuzz-eligible",
            "r1-fuzz-cpu",
            H2A_ELIGIBLE_DENOMINATOR,
            [case for case in fuzz if not is_ill(case)],
        ),
        "h2a-fuzz-characterized": population(
            "h2a-fuzz-characterized",
            "r1-fuzz-cpu",
            H2A_CHARACTERIZED_DENOMINATOR,
            [case for case in fuzz if is_ill(case)],
        ),
        "h3-repeatability": population(
            "h3-repeatability",
            "r1-repeatability-cpu",
            H3_DENOMINATOR,
            runs["r1-repeatability-cpu"].cases,
        ),
        "h3-seedrep0": population(
            "h3-seedrep0",
            "r1-seedrep0-cpu",
            H3_DENOMINATOR,
            runs["r1-seedrep0-cpu"].cases,
        ),
    }
    for backend in ("cuda", "wgpu"):
        label = f"r1-kernel-path-{backend}"
        populations[f"h4-kernel-{backend}"] = population(
            f"h4-kernel-{backend}", label, H4_DENOMINATOR, runs[label].cases
        )
    total = sum(int(block["n_cases"]) for block in populations.values())
    aborted = sum(
        1
        for block in populations.values()
        for case in block["cases"]
        if case.get("aborted")
    )
    return {
        "experiment": EXPERIMENT_ID,
        "session": SESSION,
        "stage": "E4",
        "status": f"{total} registered cases; {aborted} aborted",
        "n_cases": total,
        "n_aborted": aborted,
        "populations": populations,
    }


def _render(value: object) -> str:
    """Render one number or string for a Markdown cell, deterministically.

    Args:
        value: The cell value.

    Returns:
        Fixed-width scientific notation for non-zero floats, ``null`` for
        ``None``, ``str`` otherwise.
    """
    if isinstance(value, float):
        return f"{value:.6e}" if value else "0"
    if value is None:
        return "null"
    return str(value)


def _histogram_row(histogram: dict[str, int]) -> str:
    """Render a decade histogram as a single fixed-order Markdown cell.

    Args:
        histogram: Bucket label to count.

    Returns:
        A comma-separated ``label=count`` list, or an em dash when empty.
    """
    if not histogram:
        return "—"
    return ", ".join(f"`{label}`={count}" for label, count in histogram.items())


def _observed_for(hypothesis: str, adjudications: dict[str, Any]) -> str:
    """Render one hypothesis's observed outcome for the §3 comparison table.

    Args:
        hypothesis: The hypothesis identifier.
        adjudications: The output of :func:`adjudicate_all`.

    Returns:
        A deterministic one-line description of what was measured.
    """
    record = adjudications[hypothesis]
    if hypothesis == "H1":
        return (
            f"{record['n_accepted']}/{H1_DENOMINATOR} accepted "
            f"({record['n_native_parity']} native-parity + "
            f"{record['n_explained_dv007']} explained-dv007); "
            f"{record['n_unexplained_breach']} unexplained breaches; "
            f"{record['n_aborted']} aborted"
        )
    if hypothesis == "H2a":
        return (
            f"{record['n_eligible_accepted']}/"
            f"{record['eligible_denominator']} eligible accepted pointwise + "
            f"{record['n_valid_characterizations']}/"
            f"{record['characterized_denominator']} characterized; "
            f"{record['n_failing']} unexplained eligible breaches; "
            f"{record['n_aborted']} aborted"
        )
    if hypothesis == "H2b":
        parts: list[str] = []
        metrics = record["metrics"]
        for name in sorted(metrics):
            metric = metrics[name]
            if "ci_lower" not in metric:
                parts.append(
                    f"`{name}` n={metric['n_cases']} — {metric['verdict']} "
                    f"({metric.get('reason', 'undersized sample')})"
                )
                continue
            parts.append(
                f"`{name}` n={metric['n_cases']} mean "
                f"{_render(metric['mean_paired_difference'])}, CI "
                f"[{_render(metric['ci_lower'])}, "
                f"{_render(metric['ci_upper'])}] inside ±"
                f"{_render(metric['equivalence_margin'])} — "
                f"{metric['verdict']}"
            )
        return "; ".join(parts)
    if hypothesis == "H3":
        runs = record["runs"]
        internal = "; ".join(
            f"`{label}` {runs[label]['n_bit_identical']}/"
            f"{runs[label]['n_non_aborted']} byte-identical"
            for label in sorted(runs)
        )
        agreement = "identical" if record["projections_equal"] else "DIFFER"
        return f"{internal}; separate-run projections {agreement}"
    backends = record["backends"]
    return "; ".join(
        f"{name} {backends[name]['n_pass']}/"
        f"{backends[name]['full_denominator']} passing, "
        f"{backends[name]['failed_derivative_elements']} failed elements"
        for name in sorted(backends)
    )


def _summary_rows(adjudications: dict[str, Any]) -> list[str]:
    """Build the registered hypothesis summary table's body rows.

    Args:
        adjudications: The output of :func:`adjudicate_all`.

    Returns:
        Markdown table rows, one per hypothesis, in registered order.
    """
    rows: list[str] = []
    for key, record in adjudications.items():
        flag = " **(D1)**" if record["verdict"] == "REFUTED" else ""
        if key == "H2b":
            counts = (
                f"{record['n_contributors']} contributors per metric "
                f"(floor {record['min_contributors']})"
            )
            metrics = record["metrics"]
            endpoints = [
                max(abs(metrics[name]["ci_lower"]), abs(metrics[name]["ci_upper"]))
                for name in sorted(metrics)
                if "ci_lower" in metrics[name]
            ]
            error = (
                f"max \\|CI endpoint\\| {_render(max(endpoints))}"
                if endpoints
                else "n/a (undersized sample)"
            )
        elif key == "H3":
            runs = record["runs"]
            counts = "; ".join(
                f"`{label}` {runs[label]['n_bit_identical']}/"
                f"{record['full_denominator']}"
                for label in sorted(runs)
            )
            error = "n/a (bit-identity)"
        elif key == "H4":
            backends = record["backends"]
            counts = "; ".join(
                f"{name} {backends[name]['n_pass']}/"
                f"{backends[name]['full_denominator']}"
                for name in sorted(backends)
            )
            error = "abs " + "; ".join(
                f"{name} {_render(backends[name]['max_abs_diff'])}"
                for name in sorted(backends)
            )
        elif key == "H2a":
            counts = (
                f"{record['n_eligible_accepted']}/"
                f"{record['eligible_denominator']} pointwise + "
                f"{record['n_valid_characterizations']}/"
                f"{record['characterized_denominator']} characterized "
                f"(aborted {record['n_aborted']})"
            )
            error = f"{record['n_failing']} unexplained eligible breaches"
        else:
            counts = (
                f"{record['n_accepted']}/{record['full_denominator']} accepted "
                f"(aborted {record['n_aborted']})"
            )
            error = f"{record['n_failing']} unexplained breaches"
        rows.append(
            f"| {key} | {record['description']} | **{record['verdict']}**{flag} "
            f"| {counts} | {error} |"
        )
    return rows


def _expected_vs_observed_rows(adjudications: dict[str, Any]) -> list[str]:
    """Build the expected-versus-observed table E5 must carry forward.

    The expected column quotes the frozen pre-registration §3, which states
    these are predictions from prior governed evidence and that the native
    breach count is host-dependent and **not** an acceptance target.

    Args:
        adjudications: The output of :func:`adjudicate_all`.

    Returns:
        Markdown table rows, one per hypothesis, in registered order.
    """
    rows: list[str] = []
    for hypothesis, direction, magnitude in EXPECTED_RESULTS:
        observed = _observed_for(hypothesis, adjudications)
        verdict = adjudications[hypothesis]["verdict"]
        rows.append(
            f"| {hypothesis} | {direction} | {magnitude} | {observed} | **{verdict}** |"
        )
    return rows


def _h2b_rows(record: dict[str, Any]) -> list[str]:
    """Build H2b's registered per-metric equivalence and descriptive tables.

    Args:
        record: The H2b adjudication record.

    Returns:
        Markdown lines.
    """
    lines = [
        "",
        "## H2b — per-metric equivalence (pre-registration §7, §8 rule 5)",
        "",
        "Adjudicated by `benchmarks.campaign.exp001_r1_driver.adjudicate_h2b`,",
        "the single committed implementation of the registered three-way rule.",
        "Each metric is decided independently on one predefined paired summary",
        "per contributing case (`n_steps > 20`); the two are never pooled and",
        "serial time points are never treated as independent observations.",
        "`CONFIRMED` iff `-margin < CI_low` and `CI_high < margin`; `REFUTED`",
        "iff `CI_low > margin` or `CI_high < -margin`; otherwise",
        "`INCONCLUSIVE`, including a touching or overlapping boundary.",
        "Cohen's *d* and Welch's *t* are descriptive and gate nothing.",
        "",
        f"Bootstrap: `prin.y4q1_tools.bootstrap_ci`, "
        f"{record['bootstrap_resamples']} resamples, alpha {record['alpha']},",
        f"seed {record['bootstrap_seed']} (= `Seed(0, 1).next_u64()`). "
        f"Contributors per metric: {record['n_contributors']}",
        f"(floor {record['min_contributors']}). All {H2A_DENOMINATOR} draws "
        f"accounted for: {record['all_cases_accounted_for']}.",
        "",
        "| Metric | n | margin | mean paired diff | CI lower | CI upper | verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    metrics = record["metrics"]
    for name in sorted(metrics):
        metric = metrics[name]
        margin = _render(metric["equivalence_margin"])
        if "ci_lower" not in metric:
            lines.append(
                f"| `{name}` | {metric['n_cases']} | {margin} | — | — | — "
                f"| **{metric['verdict']}** ({metric.get('reason', '')}) |"
            )
            continue
        lines.append(
            f"| `{name}` | {metric['n_cases']} | ±{margin} "
            f"| {_render(metric['mean_paired_difference'])} "
            f"| {_render(metric['ci_lower'])} | {_render(metric['ci_upper'])} "
            f"| **{metric['verdict']}** |"
        )
    lines.extend(
        [
            "",
            "| Metric | Cohen's *d* (descriptive) | Welch *t* | Welch *p* |",
            "|---|---|---|---|",
        ]
    )
    for name in sorted(metrics):
        descriptive = metrics[name].get("descriptive")
        if descriptive is None:
            lines.append(f"| `{name}` | — | — | — |")
            continue
        lines.append(
            f"| `{name}` | {_render(descriptive.get('cohens_d'))} "
            f"| {_render(descriptive.get('welch_t_stat'))} "
            f"| {_render(descriptive.get('welch_p_value'))} |"
        )
    undefined = sorted(
        {
            str(item)
            for metric in metrics.values()
            for item in metric.get("undefined_descriptive", [])
        }
    )
    if undefined:
        lines.extend(
            [
                "",
                "Undefined descriptive statistics recorded as `null`, not "
                "zero: " + ", ".join(f"`{name}`" for name in undefined),
            ]
        )
    return lines


def _h4_rows(record: dict[str, Any]) -> list[str]:
    """Build H4's per-backend coverage table.

    Args:
        record: The H4 adjudication record.

    Returns:
        Markdown lines.
    """
    lines = [
        "",
        "## H4 — both 72-case backend proofs (pre-registration §8 rule 7)",
        "",
        "Verified separately, never pooled, and never relabelled: a CUDA",
        "result does not count as the wgpu run. E4 checks the retained",
        "per-case comparator records for internal consistency against the",
        "unchanged `rtol=1e-5, atol=1e-6` rule and verifies each per-case",
        "backend proof. The raw float32 derivative arrays were not retained,",
        "so **no independent `isclose` re-evaluation is claimed** and no",
        "kernel was run to construct one.",
        "",
        "| Backend | run ID | env backend | dtype | cases | pass | fail "
        "| aborted | failed elements | max abs | dlpack devices "
        "| backend_name | extension SHA-256 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    backends = record["backends"]
    for name in sorted(backends):
        backend = backends[name]
        devices = ", ".join(backend["dlpack_device_values"]) or "—"
        names = ", ".join(backend["backend_name_values"]) or "not recorded"
        lines.append(
            f"| {name} | `{backend['run_id']}` "
            f"| {backend['environment_backend']} | {backend['dtype']} "
            f"| {backend['n_cases']} | {backend['n_pass']} "
            f"| {backend['n_fail']} | {backend['n_aborted']} "
            f"| {backend['failed_derivative_elements']} "
            f"| {_render(backend['max_abs_diff'])} | {devices} | {names} "
            f"| `{backend['prin_extension_sha256'][:16]}…` |"
        )
    coverage = record["required_backend_coverage"]
    lines.extend(
        [
            "",
            f"Required backend coverage: {', '.join(coverage['required'])}; "
            f"present: {', '.join(coverage['present'])}; "
            f"{len(coverage['distinct_run_ids'])} distinct run IDs, "
            f"{len(coverage['distinct_environments'])} distinct "
            f"manifest-verified environments, "
            f"{len(coverage['distinct_extension_hashes'])} distinct E3 build "
            "extension hashes on the one execution SHA `R`.",
        ]
    )
    return lines


def _distribution_rows(distributions: dict[str, Any]) -> list[str]:
    """Build the registered error-distribution section.

    Args:
        distributions: The ``error-distributions.json`` payload.

    Returns:
        Markdown lines.
    """
    lines = [
        "",
        "## Registered reported statistics (campaign plan §9.1)",
        "",
        "For a C1 parity hypothesis the registered statistics are pass counts,",
        "maximum relative and absolute error, and their distribution. The",
        "distribution is reported as exact decade-bucket counts over each",
        "non-aborted case's worst per-array error — counts and order",
        "statistics only, so no estimator is introduced. The full sorted",
        "per-case and per-array maxima are in `error-distributions.json`.",
        "",
        "| Stratum | cases | array comparisons | max abs | max rel "
        "| min case-worst abs | abs-error decades |",
        "|---|---|---|---|---|---|---|",
    ]
    strata = _as_dict(distributions["strata"], "strata")
    for name in sorted(strata):
        stratum = strata[name]
        lines.append(
            f"| `{name}` | {stratum['n_cases']} "
            f"| {stratum['n_array_comparisons']} "
            f"| {_render(stratum['max_abs_diff'])} "
            f"| {_render(stratum['max_rel_diff'])} "
            f"| {_render(stratum['min_case_worst_abs_diff'])} "
            f"| {_histogram_row(stratum['abs_diff_decade_histogram'])} |"
        )
    return lines


def _breach_rows(adjudications: dict[str, Any]) -> list[str]:
    """Build the breach-breakdown section for every refuted hypothesis.

    Args:
        adjudications: The output of :func:`adjudicate_all`.

    Returns:
        Markdown lines (empty when nothing is refuted).
    """
    refuted = [
        (key, record)
        for key, record in adjudications.items()
        if record["verdict"] == "REFUTED" and "breaches" in record
    ]
    if not refuted:
        return []
    lines = [
        "",
        "## Breach breakdown (refuted hypotheses)",
        "",
        "Descriptive counts over the failing cases only. No cause is",
        "attributed here: campaign plan §10.4 assigns diagnosis to the",
        "correction cycle, and §8 requires a valid breach to be escalated as a",
        "D1 rather than rescued.",
    ]
    for key, record in refuted:
        breaches = record["breaches"]
        lines.extend(
            [
                "",
                f"### {key} — {record['n_failing']} failing case(s)",
                "",
                "| Breaching array | cases |",
                "|---|---|",
            ]
        )
        lines.extend(
            f"| `{name}` | {count} |"
            for name, count in breaches["breaching_arrays"].items()
        )
        lines.extend(["", "| Grid cell | cases |", "|---|---|"])
        lines.extend(
            f"| `{name}` | {count} |"
            for name, count in breaches["breaching_cells"].items()
        )
    return lines


def _input_index_rows(runs: dict[str, LoadedRun]) -> list[str]:
    """Build the input artefact index (campaign plan §7.4 step 1).

    Args:
        runs: Run label to verified run.

    Returns:
        Markdown lines.
    """
    lines = [
        "",
        "## Input artefact index (campaign plan §7.4 step 1)",
        "",
        "Every input was read through the explicit six-entry index in",
        "`analysis/exp001_r1_e4_analysis.py`, never a `RUN-*` glob; each run",
        "directory passed `tools.reproduce.verify_manifest`, and each result",
        "artefact was re-read against its manifest record before use.",
        "",
        "| Run | File | bytes | SHA-256 |",
        "|---|---|---|---|",
    ]
    for leg in RUN_LEGS:
        run = runs[leg.label]
        lines.append(
            f"| `{leg.run_id}` | `manifest.json` | {run.manifest_bytes} "
            f"| `{run.manifest_sha256}` |"
        )
        lines.extend(
            f"| `{leg.run_id}` | `{record['path']}` | {record['bytes']} "
            f"| `{record['sha256']}` |"
            for record in run.files
        )
    return lines


def build_summary_md(
    adjudications: dict[str, Any],
    distributions: dict[str, Any],
    comparisons: dict[str, Any],
    runs: dict[str, LoadedRun],
    generated_at: str,
    reporting_section: str,
) -> str:
    """Render the registered ``summary.md`` (§8's second fixed output).

    Args:
        adjudications: The output of :func:`adjudicate_all`.
        distributions: The ``error-distributions.json`` payload.
        comparisons: The ``case-comparisons.json`` payload.
        runs: Run label to verified run.
        generated_at: Explicit provenance stamp.
        reporting_section: The ``prin.reporting``-rendered Markdown block.

    Returns:
        The complete Markdown document.
    """
    lines = [
        "# EXP-001-r1 E4 analysis summary — golden-trajectory numerical parity",
        "",
        f"_Generated: {generated_at}_ · _Session {SESSION} (E4)_ · "
        f"_Execution commit `R = {EXECUTION_COMMIT[:7]}`_ · "
        f"_Freeze `F = {FREEZE_COMMIT[:7]}`_ · "
        f"_Main baseline `M = {MAIN_BASELINE[:7]}`_",
        "",
        "Regenerated deterministically from the six immutable E3 run artefacts",
        "by `analysis/exp001_r1_e4_analysis.py`, after `verify_manifest`",
        "passed on every input run directory. Verdicts apply the frozen",
        "pre-registration §8 decision rule and nothing else. The predecessor",
        "`EXP-001` analysis module was not used and its verdicts are unchanged.",
        "",
        "## Summary table (pre-registration §8 rules 3 to 7)",
        "",
        "| Hypothesis | Statement | Verdict | Denominators | Breaches / error |",
        "|---|---|---|---|---|",
    ]
    lines.extend(_summary_rows(adjudications))
    lines.extend(
        [
            "",
            "**Campaign plan §10.4 D1 flag: "
            f"{'RAISED' if is_d1(adjudications) else 'not raised'}.**",
            "",
            "## Expected versus observed (pre-registration §3)",
            "",
            "§3's predictions come from prior governed evidence, not from r1",
            "results; the native breach count is host-dependent and is not an",
            "acceptance target.",
            "",
            "| Hypothesis | Predicted direction | Predicted magnitude/range "
            "| Observed | Verdict |",
            "|---|---|---|---|---|",
        ]
    )
    lines.extend(_expected_vs_observed_rows(adjudications))
    lines.extend(_h2b_rows(adjudications["H2b"]))
    lines.extend(_h4_rows(adjudications["H4"]))
    lines.extend(_distribution_rows(distributions))
    lines.extend(_breach_rows(adjudications))
    lines.extend(_input_index_rows(runs))
    lines.extend(
        [
            "",
            "## Registered case evidence",
            "",
            f"`case-comparisons.json` retains {comparisons['n_cases']} "
            f"registered cases ({comparisons['n_aborted']} aborted) with every",
            "native, corrected and reference-sensitivity comparison record,",
            "including every breach.",
            "",
            "## Deterministic `prin.reporting` render (campaign plan §7.4 step 3)",
            "",
            "The block below is produced by",
            "`prin.reporting.generate_benchmark_report` over the three JSON",
            "outputs in this directory, with the same explicit `generated_at`",
            "and no implicit clock read.",
            "",
            reporting_section.rstrip(),
            "",
        ]
    )
    return "\n".join(lines)


def build_summary_json(
    adjudications: dict[str, Any],
    distributions: dict[str, Any],
    comparisons: dict[str, Any],
    runs: dict[str, LoadedRun],
    provenance: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    """Build ``summary.json`` (§8's first fixed output).

    Carries the verdicts, exact denominators, the native / explained /
    characterized / failed / aborted counts, per-metric H2b statistics, the
    repeatability result, the required backend coverage and the explicit input
    manifest digests. The ``status`` and ``benchmarks`` fields follow the
    ``prin.reporting`` artefact conventions so that
    ``generate_benchmark_report`` renders this payload's hypotheses instead of
    an uninformative ``OK``.

    Args:
        adjudications: The output of :func:`adjudicate_all`.
        distributions: The ``error-distributions.json`` payload.
        comparisons: The ``case-comparisons.json`` payload.
        runs: Run label to verified run.
        provenance: The verified identity mapping.
        generated_at: Explicit provenance stamp.

    Returns:
        The output payload.
    """
    d1 = is_d1(adjudications)
    distribution_keys = (
        "population",
        "comparison_kind",
        "n_cases",
        "n_array_comparisons",
        "max_abs_diff",
        "max_rel_diff",
        "min_case_worst_abs_diff",
        "min_case_worst_rel_diff",
        "abs_diff_decade_histogram",
        "rel_diff_decade_histogram",
    )
    return {
        "experiment": EXPERIMENT_ID,
        "session": SESSION,
        "stage": "E4",
        "generated_at": generated_at,
        "status": (
            "E4 ADJUDICATED — D1 RAISED" if d1 else "E4 ADJUDICATED — D1 NOT RAISED"
        ),
        "decision_rule": f"preregistration.md §8, frozen at F = {FREEZE_COMMIT}",
        "d1_flag": d1,
        "generator": (
            "DOCS/experiments/EXP-001-r1-golden-trajectory-numerical-parity/"
            "analysis/exp001_r1_e4_analysis.py"
        ),
        "benchmarks": [
            {"name": f"{key} — {record['description']}", "status": record["verdict"]}
            for key, record in adjudications.items()
        ],
        "provenance": provenance,
        "verdicts": {key: record["verdict"] for key, record in adjudications.items()},
        "denominators": {
            "H1": H1_DENOMINATOR,
            "H2a": H2A_DENOMINATOR,
            "H2a_eligible": H2A_ELIGIBLE_DENOMINATOR,
            "H2a_characterized": H2A_CHARACTERIZED_DENOMINATOR,
            "H2b_min_contributors": legacy.H2B_MIN_CASES,
            "H3": H3_DENOMINATOR,
            "H3_runs": len([leg for leg in RUN_LEGS if leg.mode == "repeatability"]),
            "H4_per_backend": H4_DENOMINATOR,
            "H4_backends": len([leg for leg in RUN_LEGS if leg.mode == "kernel-path"]),
        },
        "counts": {
            key: {
                name: value
                for name, value in record.items()
                if (name.startswith("n_") or name.endswith("_denominator"))
                and isinstance(value, int)
            }
            for key, record in adjudications.items()
        },
        "hypotheses": adjudications,
        "h2b_statistics": adjudications["H2b"]["metrics"],
        "repeatability": adjudications["H3"],
        "required_backend_coverage": adjudications["H4"]["required_backend_coverage"],
        "h4_backends": adjudications["H4"]["backends"],
        "error_distribution_summary": {
            name: {key: stratum[key] for key in distribution_keys}
            for name, stratum in _as_dict(distributions["strata"], "strata").items()
        },
        "case_evidence": {
            name: {
                "run_id": block["run_id"],
                "denominator": block["denominator"],
                "n_cases": block["n_cases"],
            }
            for name, block in _as_dict(
                comparisons["populations"], "populations"
            ).items()
        },
        "inputs": {
            leg.run_id: {
                "label": leg.label,
                "mode": leg.mode,
                "backend": leg.backend,
                "sidecar_hypotheses": list(leg.hypotheses),
                "adjudicated_hypotheses": list(ADJUDICATED_HYPOTHESES[leg.label]),
                "operator": runs[leg.label].sidecar.get("operator"),
                "session": runs[leg.label].sidecar.get("session"),
                "manifest_bytes": runs[leg.label].manifest_bytes,
                "manifest_sha256": runs[leg.label].manifest_sha256,
                "files": runs[leg.label].files,
            }
            for leg in RUN_LEGS
        },
    }


@dataclass(frozen=True)
class GeneratedOutput:
    """One written output file, with the digest of the bytes just written.

    ``size``/``sha256`` are computed from the in-memory payload before it is
    written, not by reopening the path afterward — the latter would leave a
    window in which a concurrent regular-file replacement between the write and
    a later digest step is silently recorded as the generated output's own
    content (TOCTOU, CWE-59).

    Attributes:
        path: The written destination.
        size: Byte length of the written payload.
        sha256: SHA-256 of the written payload.
    """

    path: Path
    size: int
    sha256: str


def _write_generated(output_dir: Path, filename: str, data: bytes) -> GeneratedOutput:
    """Write one generated output no-follow and digest the bytes written.

    Args:
        output_dir: The generated-output directory, already created.
        filename: The registered output filename.
        data: The exact bytes to publish.

    Returns:
        The written output's path, size and digest.
    """
    path = output_dir / filename
    write_no_follow(path, data, "generated output")
    return GeneratedOutput(
        path=path, size=len(data), sha256=hashlib.sha256(data).hexdigest()
    )


def write_outputs(
    adjudications: dict[str, Any],
    distributions: dict[str, Any],
    comparisons: dict[str, Any],
    runs: dict[str, LoadedRun],
    provenance: dict[str, Any],
    output_dir: Path,
    generated_at: str,
) -> list[GeneratedOutput]:
    """Write the four fixed §8 outputs, deterministically, with LF newlines.

    The three JSON outputs are written first because
    ``prin.reporting.generate_benchmark_report`` renders ``summary.md``'s
    registered-reporting section *from* that directory; the render is then
    embedded and ``summary.md`` written last. Nothing reads a wall clock.

    Args:
        adjudications: The output of :func:`adjudicate_all`.
        distributions: The ``error-distributions.json`` payload.
        comparisons: The ``case-comparisons.json`` payload.
        runs: Run label to verified run.
        provenance: The verified identity mapping.
        output_dir: Gitignored generated-output directory.
        generated_at: Explicit provenance stamp.

    Returns:
        The four written outputs, sorted by filename, each carrying the size
        and SHA-256 of the bytes handed to ``write_no_follow``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = build_summary_json(
        adjudications, distributions, comparisons, runs, provenance, generated_at
    )
    outputs = [
        _write_generated(
            output_dir, CASE_COMPARISONS_FILENAME, _canonical_bytes(comparisons)
        ),
        _write_generated(
            output_dir, ERROR_DISTRIBUTIONS_FILENAME, _canonical_bytes(distributions)
        ),
        _write_generated(output_dir, SUMMARY_JSON_FILENAME, _canonical_bytes(summary)),
    ]
    reporting_section = generate_benchmark_report(
        output_dir,
        title=("EXP-001-r1 E4 analysis outputs — golden-trajectory numerical parity"),
        generated_at=generated_at,
    )
    summary_md = build_summary_md(
        adjudications,
        distributions,
        comparisons,
        runs,
        generated_at,
        reporting_section,
    ).encode("utf-8")
    outputs.append(_write_generated(output_dir, SUMMARY_MD_FILENAME, summary_md))
    return sorted(outputs, key=lambda output: output.path.name)


def write_report_manifest(
    outputs: Sequence[GeneratedOutput],
    runs: dict[str, LoadedRun],
    manifest_path: Path,
    generated_at: str,
    adjudications: dict[str, Any],
) -> dict[str, Any]:
    """Write the committed ``report-manifest.json`` (campaign plan §7.4 item 4).

    The generated outputs are gitignored, so this manifest is the only committed
    machine-readable E4 artefact. It therefore carries the per-hypothesis
    verdicts, the exact denominators and the §10.4 D1 flag alongside the
    digests, rather than leaving them recoverable only from a regenerated file.

    Args:
        outputs: Generated outputs from :func:`write_outputs`, already carrying
            the size/digest of the bytes actually written.
        runs: Run label to verified run.
        manifest_path: Destination inside the record root.
        generated_at: Explicit provenance stamp.
        adjudications: The output of :func:`adjudicate_all`.

    Returns:
        The manifest payload.
    """
    payload = {
        "schema_version": 1,
        "experiment": EXPERIMENT_ID,
        "session": SESSION,
        "stage": "E4",
        "generated_at": generated_at,
        "decision_rule": f"preregistration.md §8, frozen at F = {FREEZE_COMMIT}",
        "verdicts": {key: record["verdict"] for key, record in adjudications.items()},
        "denominators": {
            "H1": H1_DENOMINATOR,
            "H2a_eligible": H2A_ELIGIBLE_DENOMINATOR,
            "H2a_characterized": H2A_CHARACTERIZED_DENOMINATOR,
            "H3": H3_DENOMINATOR,
            "H4_per_backend": H4_DENOMINATOR,
        },
        "d1_flag": is_d1(adjudications),
        "generator": (
            "DOCS/experiments/EXP-001-r1-golden-trajectory-numerical-parity/"
            "analysis/exp001_r1_e4_analysis.py"
        ),
        "output_root": OUTPUT_ROOT.as_posix(),
        "execution_commit": EXECUTION_COMMIT,
        "freeze_commit": FREEZE_COMMIT,
        "main_baseline": MAIN_BASELINE,
        "outputs": [
            {"path": output.path.name, "bytes": output.size, "sha256": output.sha256}
            for output in outputs
        ],
        "inputs": [
            {
                "run_id": leg.run_id,
                "label": leg.label,
                "mode": leg.mode,
                "backend": leg.backend,
                "sidecar_hypotheses": list(leg.hypotheses),
                "adjudicated_hypotheses": list(ADJUDICATED_HYPOTHESES[leg.label]),
                "manifest_bytes": runs[leg.label].manifest_bytes,
                "manifest_sha256": runs[leg.label].manifest_sha256,
                "files": runs[leg.label].files,
            }
            for leg in RUN_LEGS
        ],
    }
    write_no_follow(manifest_path, _canonical_bytes(payload), "manifest path")
    return payload


def run_analysis(
    repository_root: Path,
    output_dir: Path,
    manifest_path: Path,
    generated_at: str,
) -> dict[str, Any]:
    """Execute the whole registered E4 analysis end to end.

    Args:
        repository_root: Repository root.
        output_dir: Gitignored generated-output directory.
        manifest_path: ``report-manifest.json`` destination.
        generated_at: Explicit provenance stamp.

    Returns:
        The adjudication mapping.

    Raises:
        AnalysisError: If any §8 rule 1 admissibility check fails, any stored
            decision is not reproduced by its retained records, or an output is
            not finite JSON. The destinations are taken as given; containment
            is applied at the command-line boundary in :func:`main`, which is
            where the untrusted input is — a programmatic caller (this
            module's tests) supplies its own trusted scratch directory.
    """
    provenance = verify_e3_log(repository_root)
    provenance["r1_run_ids"] = verify_run_inventory(repository_root)
    provenance["corpus_manifest_sha256"] = r1.CORPUS_SHA256
    provenance["fuzz_stream_sha256"] = r1.STREAM_SHA256
    provenance["reference_source_sha256"] = r1.REFERENCE_SOURCE_SHA256
    provenance["instrument_sha256"] = r1.INSTRUMENT_SHA256
    runs: dict[str, LoadedRun] = {
        leg.label: load_run(repository_root, leg) for leg in RUN_LEGS
    }
    verify_corpus_population(runs["r1-corpus-cpu"], repository_root)
    verify_fuzz_population(runs["r1-fuzz-cpu"])
    for label in ("r1-repeatability-cpu", "r1-seedrep0-cpu"):
        verify_repeatability_population(runs[label])
    for backend in ("cuda", "wgpu"):
        verify_kernel_population(runs[f"r1-kernel-path-{backend}"], repository_root)
    contributors = verify_h2b_summaries(runs["r1-fuzz-cpu"].cases)
    adjudications = adjudicate_all(runs, contributors)
    distributions = build_error_distributions(runs)
    comparisons = build_case_comparisons(runs)
    outputs = write_outputs(
        adjudications,
        distributions,
        comparisons,
        runs,
        provenance,
        output_dir,
        generated_at,
    )
    write_report_manifest(outputs, runs, manifest_path, generated_at, adjudications)
    return adjudications


def _parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Returns:
        The configured parser. The input root is never a command-line option:
        the analysis is bound to its own checkout, which is what campaign plan
        §7.4 step 5's clean-regeneration requirement wants.
    """
    parser = argparse.ArgumentParser(
        description="Registered E4 analysis for EXP-001-r1."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=f"Generated-output directory (default: {OUTPUT_ROOT.as_posix()}).",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=None,
        help="report-manifest.json destination (default: the record root).",
    )
    parser.add_argument(
        "--generated-at",
        default=GENERATED_AT,
        help=(
            "Explicit provenance stamp. The default is the registered value; "
            "changing it changes every output digest."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the analysis and print each hypothesis verdict.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        ``0`` always — a refutation is a scientific result, not a tool error.
        The D1 flag is reported on stdout and recorded in every output.

    Raises:
        AnalysisError: If a command-line destination escapes its permitted
            roots, names anything but ``report-manifest.json`` inside the
            record root, or collides with one of the four files
            ``write_outputs`` itself writes. This is the trust boundary.
    """
    args = _parser().parse_args(argv)
    root = _REPOSITORY_ROOT
    output_dir = _checked_destination(
        Path(args.output_dir or root / OUTPUT_ROOT),
        allowed_generated_output_dirs(root),
        "output directory",
    )
    manifest_path = _checked_manifest_destination(
        Path(args.manifest_path or root / RECORD_ROOT / "report-manifest.json"),
        allowed_output_roots(root),
        (root / RECORD_ROOT).resolve(),
    )
    generated = {
        str((output_dir / name).resolve()).casefold() for name in GENERATED_FILENAMES
    }
    if str(manifest_path).casefold() in generated:
        raise AnalysisError(
            f"manifest path {manifest_path} collides with a generated output "
            f"this analysis also writes under {output_dir}; choose a "
            "--manifest-path outside that set"
        )
    adjudications = run_analysis(
        root, output_dir, manifest_path, str(args.generated_at)
    )
    for key, record in adjudications.items():
        print(f"{key}: {record['verdict']}")
    print(f"D1 flag: {'RAISED' if is_d1(adjudications) else 'not raised'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
