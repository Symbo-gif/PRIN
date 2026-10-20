"""Governed-skip registry for the ported PRINet 3.0 acceptance suite.

WP-036C S3 (session ``0144O``) remediation of audit ``036c-wp036c-audit.md``
findings WP036C-F1 / F2 / F3 / F5. A block of ported acceptance tests assert
project artefacts and execution paths that PRIN's roadmap has not built yet —
Phase-6 deliverables (docs site, notebooks, LaTeX paper, benchmark-result JSON,
SHA-256 manifest, RC1 version/classifier surface) and the device-resident CUDA
execution path. They are **not** port-fidelity defects and are not weakenable
(Testing Standards §1.1): the assertions and test text are byte-unchanged.

Rather than edit each faithful-copy port, the deferral is applied here as one
auditable adaptation-layer hook. Every entry names its governing item:

* ``DV-031`` — `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`; un-skipped as the
  owning WP (WP-037 docs/notebooks/paper, WP-038 reproduce.py + benchmark
  campaign + manifest, WP-036E CUDA execution) lands its deliverable. The
  WP-037 half was fully discharged at WP-037 S1 (session ``0145``); what
  remains here is the WP-038 half, the CUDA-execution half, and three
  non-deliverable classes (version, RNG regime, host timing).
* Plan amendment #41 — PRIN is independently versioned toward ``1.0.0-rc1``;
  the PRINet-3.0 ``__version__ == "3.0.0"`` assertions are re-pointed at WP-038.

Maintainer-approved: MichaelMaillet, 2026-09-01 (WP-036C S3 ``AskUserQuestion``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

# --- WP036C-F5 / plan amendment #41: PRIN is independently versioned ----------
_VERSION_SKIP = (
    "WP036C-F5 / plan amendment #41: PRIN is independently versioned "
    "(0.3.0 -> 1.0.0-rc1), not a continuation of PRINet 3.0's numbering; "
    "re-pointed at PRIN's own version at WP-038."
)

_VERSION_NODES = frozenset(
    {
        "tests/test_acceptance_y4q3.py::TestVersionAPI::test_version_is_3_0_0",
        "tests/test_acceptance_y4q3.py::TestVersionAPI::test_major_version_at_least_3",
        "tests/test_acceptance_y4q3.py::TestVersionAPI::test_pyproject_production_stable",
        "tests/test_acceptance_y4q4.py::TestVersionConsistency::test_prinet_version_3",
        "tests/test_acceptance_y4q4.py::TestCitationCFF::test_citation_version_matches",
    }
)

# --- WP036C-F2 / F3 / DV-031(B): device-resident CUDA execution path (WP-036E) -
_CUDA_SKIP = (
    "WP036C-F2/F3 / DV-031(B): CUDA execution path (OscillatorState.device, "
    "#[pyclass(unsendable)] ctx panic on the torch autograd worker thread, "
    "DLPack CPU-only marshal, CUDA JIT) is owned by WP-036E; adjacent to "
    "DV-030 / DV-005."
)

_CUDA_NODES = frozenset(
    {
        "tests/test_acceptance_gpu.py::TestCPDecompositionGPU::test_decompose_and_reconstruct",
        "tests/test_acceptance_gpu.py::TestOscillatorStateGPU::test_random_state_on_gpu",
        "tests/test_acceptance_gpu.py::TestResonanceLayerGPU::test_gradient_flow_gpu",
        "tests/test_acceptance_gpu.py::TestPRINetModelGPU::test_oscillatory_weight_init_gpu",
        "tests/test_acceptance_gpu.py::TestSynchronizedGradientDescentGPU::test_step_on_gpu",
        "tests/test_acceptance_gpu.py::TestRIPOptimizerGPU::test_step_on_gpu",
        "tests/test_acceptance_y2q3.py::TestHybridPRINetV2::test_clevr6_convergence",
        "tests/test_acceptance_y2q3.py::TestFashionMNIST::test_v2_cifar10_no_oom",
        "tests/test_acceptance_y4q3.py::TestCUDAJIT::test_cuda_jit_compiles",
    }
)

# --- WP036C-F1 / DV-031(A): unbuilt Phase-6 deliverables ---------------------
_WP038_SKIP = (
    "WP036C-F1 / DV-031(A): asserts a Phase-6 reproducibility deliverable "
    "(root reproduce.py / benchmark-result JSON / SHA-256 manifest / release "
    "classifier) built by WP-038; the benchmark campaign is a Phase-7 activity."
)

# The whole WP-037 half of DV-031(A) was discharged at WP-037 S1 (session
# `0145`) and its nodes removed from this registry: the Sphinx site
# (`y4q3::TestSphinxDocs`;
# `y4q4::TestDocumentationCompleteness::test_sphinx_conf_exists`), the notebooks
# (`y4q3::TestNotebooks` x12, `y4q4::TestArtefactCounts::test_notebook_count`),
# the LaTeX paper (`y4q3::TestLaTeXPaper`;
# `y4q4::TestDocumentationCompleteness::test_latex_paper_exists`), and the
# publication output roots
# (`y4q2::TestStyleConsistency::test_*_default_output_dir`).
# `TestSphinxDocs`' three path-existence tests needed a `docs/` -> `DOCS/sphinx/`
# path adaptation first (Documentation Standards §3 supersedes the lowercase
# convention; ETCA-001 T-F4 follow-up (b) precedent) — assertions, expected
# values, and call order unchanged. `TestSphinxDocs::test_sphinx_build_succeeds`
# now runs under `pytest.mark.slow` (see _WP037_SLOW_NODES).

# --- WP-037 S1 (`0145`): nested-build meta-test marked slow ------------------
# `TestSphinxDocs::test_sphinx_build_succeeds` spawns a full `sphinx-build`
# subprocess (up to its own 300 s timeout) inside the test session. Testing
# Standards §4 defines `slow` as >5 s and keeps the default CI gate at
# `-m "not slow and not gpu"`, so it belongs in the nightly/full-suite leg
# rather than the fast gate. The marker is applied here in the adaptation layer
# rather than edited into the ported test (Testing Standards §1.1).
_WP037_SLOW_NODES = frozenset(
    {
        "tests/test_acceptance_y4q3.py::TestSphinxDocs::test_sphinx_build_succeeds",
    }
)

# Parametrised / prefix-matched WP-038 benchmark-artefact cases.
_WP038_PREFIXES = (
    "tests/test_acceptance_y3q49.py::TestResultArtefacts::test_artefact_exists[",
)

_WP038_NODES = frozenset(
    {
        "tests/test_acceptance_y4q1_8.py::TestInfrastructure::test_preregistration_exists",
        "tests/test_acceptance_y4q2.py::TestGenerateAllFigures::test_output_files_created",
        "tests/test_acceptance_y4q2.py::TestReproduceScript::test_script_exists",
        "tests/test_acceptance_y4q2.py::TestReproduceScript::test_script_is_importable",
        "tests/test_acceptance_y4q2.py::TestReproduceScript::test_validate_artefacts_returns_list",
        "tests/test_acceptance_y4q2.py::TestReproduceScript::test_compute_sha256",
        "tests/test_acceptance_y4q2.py::TestReproduceScript::test_help_flag",
        "tests/test_acceptance_y4q2.py::TestArtefactCompleteness::test_has_json_files",
        "tests/test_acceptance_y4q2.py::TestArtefactCompleteness::test_minimum_json_count",
        "tests/test_acceptance_y4q4.py::TestArtefactCounts::test_json_artefact_count",
        "tests/test_acceptance_y4q4.py::TestQ1BenchmarkIntegrity::test_q1_chimera_artefacts",
        "tests/test_acceptance_y4q4.py::TestQ1BenchmarkIntegrity::test_q1_temporal_advantage_artefacts",
        "tests/test_acceptance_y4q4.py::TestQ1BenchmarkIntegrity::test_q1_reviewer_gap_artefacts",
        "tests/test_acceptance_y4q4.py::TestQ1BenchmarkIntegrity::test_q1_adversarial_artefacts",
        "tests/test_acceptance_y4q4.py::TestSHA256Manifest::test_can_generate_manifest",
        "tests/test_acceptance_y4q4.py::TestSHA256Manifest::test_artefacts_have_benchmark_name",
        "tests/test_acceptance_y4q4.py::TestDocumentationCompleteness::test_reproduce_script_exists",
        "tests/test_acceptance_y4q3.py::TestReproducibility::test_reproduce_py_exists",
        "tests/test_acceptance_y4q3.py::TestBenchmarkArtefacts::test_has_benchmark_results",
        # Recursive-pytest release-readiness meta-tests: skip budget is tracked
        # by DV-031 now; CI is the authoritative zero-failures gate (audit §3.3).
        "tests/test_acceptance_y4q3.py::TestSkipCount::test_skip_count_within_target",
        "tests/test_acceptance_y4q3.py::TestSkipCount::test_no_failures",
    }
)

# --- WP036C-F3: deterministic-Seed RNG-regime divergence (M5 disposition) ----
_RNG_SKIP = (
    "WP036C-F3: PRIN's deterministic Seed frequency draw lands the "
    "uniform-vs-cosine ring order-parameter delta at ~6.1e-4 for seed=42 "
    "(test asserts > 1e-3); other seeds give 1.2e-3..2.1e-3 and the phases do "
    "diverge. RNG-regime divergence recorded in the M5 sub-pass disposition and "
    "DOCS/sphinx/parity_report.rst; not a numerics defect."
)

_RNG_NODES = frozenset(
    {
        "tests/test_acceptance_y4q1_3.py::TestWeightedCoupling::test_cosine_kernel_affects_dynamics",
    }
)

# --- Forward-pass wall-clock ratio flake (ETCA-002 T-F5) --------------------
# `nightly.yml`'s `full-suite` job (the only gate that runs @pytest.mark.slow)
# has been red since it began running on this: a hard `assert ratio <= 5.0` on
# the DiscreteDTG-vs-Transformer forward-pass wall-clock ratio, measured 5.66x
# on the shared ubuntu runner (and 60.2x wall / 19.4x process-CPU after
# WP037-F1's 15-parameter DLPack synchronization in dev profile; same small-shape
# bridge-dispatch class as Plan amendment #30 / DV-021). Ported verbatim from
# PRINet 3.0, not weakenable. Dated maintainer quarantine (2026-09-02,
# re-ratified 2026-10-19: comparative timing stays under nightly.yml's
# benchmark harness). Note: DV-032 test (2) `test_deterministic_seed` was
# converted to a seeded frame-count check (`max_frames=100, warmup_frames=20`)
# on 2026-10-19 and its `_TIMING_NODES` quarantine removed.
_RATIO_SKIP = (
    "DV-032 (ETCA-002 T-F5): forward-pass wall-clock ratio flake — asserts "
    "DiscreteDTG is <=5x an equivalent Transformer layer, measures ~5.7x on "
    "shared CI runners. Ported verbatim from PRINet 3.0; dated maintainer "
    "quarantine; fix tracked in the Deferred Validation Register."
)
_RATIO_NODES = frozenset(
    {
        "tests/test_acceptance_y2q1.py::TestDiscreteDeltaThetaGamma::test_speed_vs_transformer",
    }
)


def _reason_for(nodeid: str) -> str | None:
    """Return the governed-skip reason for ``nodeid``, or ``None`` to run it."""
    if nodeid in _VERSION_NODES:
        return _VERSION_SKIP
    if nodeid in _CUDA_NODES:
        return _CUDA_SKIP
    if nodeid in _WP038_NODES or nodeid.startswith(_WP038_PREFIXES):
        return _WP038_SKIP
    if nodeid in _RNG_NODES:
        return _RNG_SKIP
    if nodeid in _RATIO_NODES:
        return _RATIO_SKIP
    return None


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Apply the WP-036C S3 governed skips to the ported acceptance suite."""
    for item in items:
        reason = _reason_for(item.nodeid)
        if reason is not None:
            item.add_marker(pytest.mark.skip(reason=reason))
        elif item.nodeid in _WP037_SLOW_NODES:
            item.add_marker(pytest.mark.slow)


def pytest_sessionstart(session: pytest.Session) -> None:
    """Delete a stale ``--basetemp`` up front, retrying sharing violations.

    PR #33 review audit (G09a/G13): pytest's own lazy deletion of the previous
    session's ``--basetemp`` runs inside the first ``tmp_path`` setup and has
    no retry, so a transient Windows handle on a leftover file turned into
    setup errors. See ``tests/_basetemp.py``.
    """
    from _basetemp import clear_stale_basetemp

    given = session.config.option.basetemp
    # pytest-xdist workers share the controller's --basetemp; only the
    # controller (no ``workerinput``) may delete it.
    if not given or hasattr(session.config, "workerinput"):
        return
    try:
        clear_stale_basetemp(Path(given), Path(str(session.config.rootpath)))
    except PermissionError as exc:
        raise pytest.UsageError(
            f"stale --basetemp {given} is still held by another process after "
            f"retrying: {exc}"
        ) from exc
    except ValueError as exc:
        raise pytest.UsageError(str(exc)) from exc
