# Session 0125 — WP-032 S1 handoff

**Date:** 2026-08-25
**Session:** 0125 — WP-032 S1
**Status:** S1 delivered; handoff to mandatory S2 audit (session 0126)
**Predecessor:** WP-031 S4 at `49f7af4`

## Mission and entry conditions

Mission: integrate daemon, hooks, MOT, temporal, stats, and adversarial APIs;
complete provider and latency acceptance.

Entry conditions were met:

- WP-031 S4 is closed and committed at `49f7af4`.
- PSR-031 records no unresolved D1/D2 finding.
- The maintainer directly requested execution of session 0125, satisfying the
  pending in-session approval mechanism recorded in PSR-031 §6.

## Scope decisions

1. **Integration belongs in `prin-py`.** `prin-daemon` and `prin-train` are
   sibling crates at the same architecture tier. Neither now depends on the
   other. `prin-py`, the only crate allowed to link Python and already dependent
   on both siblings, owns the cross-crate binding surface. The Python modules
   only select and compose Rust operations; they implement no numerical
   algorithm.
2. **The deferred native-daemon callback seam is delivered.** A
   `SubconsciousDaemon` PyO3 class owns the Rust native daemon and accepts a
   Python inference callback. The background thread attaches to Python only for
   the callback. `stop()` uses `Python::detach` while waiting, and wrapper drop
   transfers cleanup to a separate Rust thread so a GIL-holding finalizer never
   waits for a callback that needs that same GIL. The dedicated in-flight-stop
   test exercises this contract.
3. **Evaluation and experiment numerics remain single-source Rust.** MOT calls
   `prin_daemon::mot`; temporal/statistical/adversarial calls
   `prin_train::{temporal_metrics,stats,adversarial}`. The Python facades do not
   reproduce formulas, assignment, confidence intervals, or attacks.
4. **Adversarial Python APIs accept public models.** The public
   `prin.experiments` functions accept `prin.nn.PhaseTracker` and
   `prin.nn.TemporalSlotAttentionMOT`, then pass their Rust bridges to the core.
   The lower-level extension functions are intentionally not the public API.
5. **No dependency change was needed.** Existing PyO3, NumPy, daemon, train,
   and dynamics dependencies cover the integration.
6. **Phase tag creation is not performed in S1.** Versioning Standards §4 makes
   a real tag invoke `release.yml` and publication. The Phase 5 tag gate is
   locally green on implementation, parity, quality, security, provider, and
   latency evidence, but the actual release/tag action remains a maintainer-
   approved S4/release operation. S1 does not push or publish.

## Delivered files

| File | Delivery |
|---|---|
| `crates/prin-daemon/src/error.rs` | Typed `DaemonError::Inference` for callback failures. |
| `crates/prin-py/src/bindings/daemon.rs` | Native `SubconsciousDaemon` and `TrainingHooks` PyO3 bindings; GIL-safe stop/drop; callback shape/dtype validation. |
| `crates/prin-py/src/bindings/phase5.rs` | Rust-backed MOT, temporal metrics, bootstrap/Welch/effect-size, and adversarial evaluation bindings. |
| `crates/prin-py/src/bindings/{mod,phase_tracker,slot_attention}.rs`, `src/lib.rs` | Module registration and crate-private tracker accessors for orchestration. |
| `python/prin/daemon.py` | Public daemon/hooks exports and `SubconsciousController.spawn_daemon()`. |
| `python/prin/eval/__init__.py` | Cohesive MOT and temporal evaluation facade. |
| `python/prin/experiments/__init__.py` | Statistical and public-model adversarial facade. |
| `python/prin/_prin_core.pyi` | Complete type stubs for the added extension surface. |
| `tests/test_phase5_integration.py` | Eight end-to-end integration tests, including failure/lifecycle and both tracker families. |
| `EVIDENCE/0125-wp032-s1-daemon-latency.json` | Fresh five-trial lock-free/mutex pilot plus direct-reference acceptance disposition. |
| `EVIDENCE/0125-wp032-s1-provider-acceptance.json` | Live provider probe and governed optional-hardware skips. |

## Acceptance-criterion evidence map

### AC1 — Integrate daemon, hooks, MOT, temporal, stats, and adversarial APIs

`tests/test_phase5_integration.py` proves:

- `TrainingHooks` telemetry → `SubconsciousState` → native
  `SubconsciousDaemon` → callback → `ControlSignals`;
- the committed CPU ONNX controller runs behind the native daemon through
  `SubconsciousController.spawn_daemon()`;
- stopping during an in-flight Python callback does not retain the GIL;
- callback exceptions, wrong dtype, wrong length, non-contiguous output,
  duplicate stop, stopped access, and constructor/input validation are handled;
- `MotAccumulator` and full temporal metrics share the `prin.eval` surface;
- bootstrap/Welch/Cohen and deterministic FGSM evaluation share
  `prin.experiments`;
- both public tracker families execute the adversarial orchestration.

Result: **PASS** — 8/8 targeted integration tests.

### AC2 — Daemon latency target

`EVIDENCE/0125-wp032-s1-daemon-latency.json` records the required environment,
protocol, all fresh samples, and prior registered evidence. In five fresh
controlled same-language trials, lock-free p95 is 200 ns versus 2700–3000 ns
for a synthetic Rust mutex implementation of the PRINet 3.0 locking design
(13.5×–15× lower); this row is not the historical Python implementation. Across
the complete repeated direct-reference pilot, median p95 is 200 ns for PRIN
versus 250 ns for PRINet 3.0. The fresh single direct trial tied at 200 ns and
is explicitly not misrepresented as independently lower.

Result: **PASS** at the registered single-host acceptance-pilot level; no final
campaign/scientific claim is made.

### AC3 — MOT equivalence

`cargo test -p prin-daemon --test parity_mot -- --test-threads=1`:
2 passed. The committed ten-scenario fixture remains generated from real
`py-motmetrics` 1.4.0. Python integration additionally validates a perfect
sequence through the new binding surface.

Result: **PASS**.

### AC4 — Provider acceptance and justified optional-hardware skips

`EVIDENCE/0125-wp032-s1-provider-acceptance.json` records the live probe:

- CPU: registered, executes, integration/parity tests pass.
- DirectML: registered, but this graph is rejected by `DmlFusedGemm` because
  its fused node has two inputs where the provider requires three. This is the
  unchanged amendment-#13 / DV-006 condition; the prior report demonstrates
  that the reference graph fails identically. Deterministic CPU fallback passes.
- VitisAI: not registered; this Ryzen 7 8700F host has no XDNA NPU and the SDK
  wheel is CPython 3.12 while the project uses Python 3.14.

Result: **PASS WITH JUSTIFIED OPTIONAL-HARDWARE SKIPS**. Runtime-probing tests
widen automatically when another provider becomes executable.

### AC5 — Phase 5 tag gate

Local equivalents of the tag gates are green: default/strict Rust workspace
tests, full Python/parity suite, MOT parity, rustdoc, lint/type/docstring gates,
native audits, Snyk Code, baseline validation, provider acceptance, and latency
acceptance. No tag or push occurred; S2/S3/S4 and maintainer release approval
remain mandatory.

Result: **GREEN FOR S2 AUDIT / TAG-READY LOCALLY**, not a release claim.

## Parity-evidence disposition

No new numerical primitive was introduced. Every newly bound operation delegates
to a primitive already parity-dispositioned in WP-028 through WP-031:

- state/control and controller inference: bit-exact/tolerance parity from WP-028;
- daemon/control-buffer semantics: PRINet 3.0 design comparison from WP-029;
- MOT: real `py-motmetrics` parity from WP-030;
- temporal metrics/adversarial: reference formula transcription and hand-worked
  invariants from WP-031;
- Welch statistics: real SciPy parity from WP-031.

The archived reference grep performed for this session confirmed the governing
reference entry points remain `nn/mot_evaluation.py::evaluate_tracking`,
`utils/temporal_metrics.py`, `utils/adversarial_tools.py`, and
`nn/training_hooks.py`:

```powershell
grep "def evaluate_tracking\|def identity_switches\|def fgsm_attack\|class StateCollector" "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main" -g "*.py"
```

Archived material was used only for parity provenance, not as current
repository truth.

## Coverage evidence

An instrumented PyO3 cdylib was built using `cargo llvm-cov show-env`, then
executed by `tests/test_phase5_integration.py`:

- `bindings/phase5.rs`: **99.62% lines**, **96.77% functions**; its sole
  uncovered line is the `#[pymethods]` attribute line, not executable logic.
- the new executable block in `bindings/daemon.rs` has no uncovered executable
  source lines after callback dtype/length/contiguity and drop-path tests; only
  its two `#[pymethods]` attribute lines are listed as uncovered.
- changed Python modules are **100%** in the full suite (`daemon.py`,
  `eval/__init__.py`, `experiments/__init__.py`).

This satisfies the ≥95% changed-code gate. The low whole-file `daemon.rs`
number emitted by this targeted binding run reflects pre-existing WP-028 binding
methods outside this session's diff; those methods are covered by their normal
Python suites, which report `daemon.py` at 100% in the full run.

## Verification evidence

Commands executed on Windows 11 / Rust 1.92.0 / Python 3.14.0:

```powershell
cargo fmt --all -- --check                                      # clean
cargo clippy --workspace --all-targets -- -D warnings           # exit 0
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings # exit 0
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps # exit 0
cargo test --workspace -- --test-threads=1                      # exit 0
cargo test --workspace --features strict-checks -- --test-threads=1 # exit 0
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/ # clean
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/ # 76 formatted
.venv\Scripts\mypy python/prin --strict                         # 0 issues; validates _prin_core.pyi consumers
grep "class SubconsciousDaemon\|class TrainingHooks\|class MotAccumulator\|class TemporalMetrics\|class AdversarialEvalResult" python/prin/_prin_core.pyi # all present
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin # 100% (266/266)
.venv\Scripts\python -m bandit -r . -c pyproject.toml          # 0 issues
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --basetemp=.pytest_basetemp # 555 passed, 8 deselected
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --basetemp=.pytest_basetemp-full # 1155 passed; 99% Python line coverage
cargo audit                                                      # exit 0; DV-008/DV-017 only
.venv\Scripts\python -m pip_audit .                             # 0 vulnerabilities
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt # 0 vulnerabilities
.venv\Scripts\python tools/wp001_baseline.py check             # passed
cargo test -p prin-daemon --test parity_mot -- --test-threads=1 # 2 passed
```

One clippy build emitted a Windows incremental-directory file-handle warning
from the filesystem/antivirus while still exiting 0; the strict re-run used
`CARGO_INCREMENTAL=0` and was clean.

## Security evidence

Snyk MCP was authenticated and run at threshold `low`:

| Scan | Scope | Result |
|---|---|---|
| Snyk Code | `crates/prin-py` | 0 findings |
| Snyk Code | `crates/prin-daemon` | 0 findings |
| Snyk Code | `python/prin` | 0 findings |
| Snyk Code | `tests/test_phase5_integration.py` | 0 findings |

No manifest changed, so no change-attributable Snyk Open Source scan was
required. Native audits are independently clean at their governed thresholds;
`cargo audit` reports only the two pre-approved unmaintained warnings (DV-008
`paste`, DV-017 `bincode`). Local `gitleaks` is unavailable; GitHub native
secret scanning remains disabled (live API recheck: HTTP 404), so amendment #5's
hosted full-history Gitleaks/branch-protection controls remain authoritative and
will execute at the S4 push. Neither unavailable control is claimed as passed.

## Out-of-scope discoveries

1. A real pre-release tag triggers publication and therefore remains an explicit
   maintainer-approved S4/release action, not an S1 side effect.
2. DirectML graph re-export with three-input `Gemm` nodes and VitisAI execution
   on compatible XDNA hardware remain hardware/export concerns, not defects in
   this integration. Their exact evidence remains in DV-006.
3. Final benchmark/category migration remains Phase 6; this session records an
   acceptance pilot only.

## Handoff to S2

Recommended audit focus:

1. GIL safety of callback, `stop`, and drop cleanup.
2. Whether changed-code coverage correctly excludes only non-executable PyO3
   attribute lines.
3. Crate-layering and no-Python-numerics compliance.
4. DirectML/VitisAI skip governance against amendment #13 and DV-006.
5. Latency interpretation, especially the explicit fresh direct-trial tie versus
   the repeated-pilot median and controlled same-language result.
6. Tag-readiness wording: confirm it does not claim a tag, push, CI run, or
   publication occurred during S1.
