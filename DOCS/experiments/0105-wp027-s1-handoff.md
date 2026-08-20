# Session 0105 — WP-027 S1 Handoff Note

**Session:** 0105 — WP-027 S1: Coding — Trainable-stack integration and Phase 4 gate
**Date:** 2026-08-19/20
**Status:** S1 delivered; handoff to S2 audit (session 0106)

## Mission recap

"Run controlled temporal CLEVR-N integration, full gradcheck, bridge
profiling, serialization, and trainable API acceptance." Contract
(`DOCS/sessions/phase-4/0105-wp027-s1-trainable-stack-integration-and-phase-4-gate.md`):
PhaseTracker reaches at least the registered 3.0 IP threshold in validation
runs; gradchecks green; bridge overhead <5%; Phase 4 tag gate passes without
treating pilot data as campaign evidence. Non-goals: final scientific
publication claims.

## Scope decision (record per "do not expand scope silently")

Declared scope (PSR-026 §6): `crates/prin-train/` (integration into a
unified training pipeline), `crates/prin-py/` (bridge profiling,
serialization acceptance), `python/prin/nn/` (trainable API acceptance,
`torch.optim.Optimizer` wrapper over `SyncGd`/`Rip`/`Scalr`). All work below
stays inside this scope; the one addition beyond the PSR's file-level list
is `python/prin/train.py` (a new, narrowly-scoped module — see
"Architecture" below for why it doesn't belong in `prin.nn` or the
Phase-5-reserved `prin.experiments`/`prin.datasets` stubs).

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-train/src/dataset.rs` | **New.** `SequenceData`, `TemporalClevrNConfig`, `generate_temporal_clevr_n`, `generate_dataset` — structural port of PRINet 3.0's temporal CLEVR-N sequence generator. |
| `crates/prin-train/src/losses.rs` | **New.** `hungarian_similarity_loss`, `temporal_smoothness_loss` — direct ports of the reference training losses. |
| `crates/prin-train/src/trainer.rs` | **New.** `TemporalTrainerConfig`, `TrainingResult`, `ValMetrics`, `train_phase_tracker`, `evaluate_phase_tracker` — the Rust-native training loop (Burn `Adam` + warmup/cosine LR + gradient clipping + early stopping). |
| `crates/prin-train/benches/phase_tracker_bridge.rs` | **New.** Criterion baseline for `PhaseTracker::forward` (mirrors `PhaseTrackerBridge::match_frames`), extending DV-021's `ResonanceLayer` bench to a second module. |
| `crates/prin-train/Cargo.toml` | Registered the `phase_tracker_bridge` `[[bench]]`. |
| `crates/prin-train/src/lib.rs` | Registered `dataset`/`losses`/`trainer` modules; corrected the stale doc comment claiming the WP-026 bridges have no PyO3 binding (they do, since Exec-WP-026 S1). |
| `crates/prin-train/tests/integration_temporal_clevr_n.rs` | **New.** The acceptance-criterion validation run (3 seeds, canonical protocol), `#[ignore]`d by default (~150s in `--release`) — see "Why `#[ignore]`" in the file's module docs. |
| `crates/prin-train/tests/integration_checkpoint_resume.rs` | **New.** Serialization acceptance: checkpoints a *trained* (not freshly-initialized) `PhaseTracker`, reloads into a fresh instance, confirms bit-identical validation/`track_sequence` behavior. |
| `crates/prin-py/src/bindings/trainer.rs` | **New.** `train_phase_tracker` PyO3 entry point running the Rust trainer end to end; `TrainingResult` pyclass. |
| `crates/prin-py/src/bindings/optim.rs` | **New.** `SyncGdBridge`/`ScalrBridge`/`RipBridge` — non-differentiable optimizer-step bridges. |
| `crates/prin-py/src/bindings/mod.rs`, `src/lib.rs` | Registered the two new binding modules. |
| `crates/prin-py/Cargo.toml` | Added `serde`/`serde_json` (direct dependencies; previously only reached transitively) for optimizer-state JSON round-trips. |
| `python/prin/nn/optimizers.py` | **New.** `SyncGd`/`Scalr`/`Rip` `torch.optim.Optimizer` subclasses. |
| `python/prin/train.py` | **New.** `train_phase_tracker`/`TrainingResult` — thin Python entry point for the Rust-native trainer. |
| `python/prin/nn/__init__.py`, `python/prin/__init__.py` | Export the new optimizer classes; doc updates. |
| `python/prin/_prin_core.pyi` | Stubs for `TrainingResult`, `train_phase_tracker`, `SyncGdBridge`, `ScalrBridge`, `RipBridge`. |
| `tests/test_train_bridge_optim.py` | **New.** 13 tests: `SyncGd`/`Scalr`/`Rip` correctness, state-dict round trip, error boundaries. |
| `tests/test_train_pipeline.py` | **New.** 4 tests: `prin.train.train_phase_tracker` end-to-end, reproducibility, error handling. |
| `tests/test_train_bridge_phase_tracker.py` | Added a composed `encode -> evolve -> phase_similarity` gradcheck ("full gradcheck") and a `TestPhaseTrackerBenchmarks` pytest-benchmark class. |
| `DOCS/experiments/0105-wp027-temporal-clevr-n-validation.json` | **New.** Raw evidence for the IP-threshold acceptance criterion. |

## Architecture

### Dataset generator — structural, not bit-parity, port

`crates/prin-train/src/dataset.rs` ports PRINet 3.0's
`generate_temporal_clevr_n`/`generate_dataset`
(`temporal_training.py:68-253`) algorithm — constant-velocity motion with
elastic boundary bounce, occlusion zeroing, appearance-feature swap,
velocity reversal, additive noise — using the project's single
counter-based `Seed` (Project Plan §4 rule 3) instead of PRINet 3.0's
per-perturbation `torch.Generator(seed + offset)` streams. This RNG
substitution is a standing, repo-wide architecture decision (already true
of every other `prin-train` seeded-init helper), not a new exception; see
the module's own doc comment for the full parity-evidence disposition.

### Rust-native trainer — why training doesn't live in Python

`crates/prin-train/src/trainer.rs` ports PRINet 3.0's `TemporalTrainer`
(`temporal_training.py:454-869`: Adam, linear-warmup/cosine-anneal LR,
gradient clipping, smoothed-validation-loss early stopping with
best-checkpoint restore) entirely in Rust, using Burn's `AdamConfig`/
`GradientsParams`/`Optimizer::step`. Two documented deviations from the
PyTorch reference (full rationale in the module's own doc comment):
gradient clipping uses Burn's per-tensor `GradientClippingConfig::Norm`
rather than PyTorch's single global-norm `clip_grad_norm_`; the LR schedule
is a directly-computed scalar cosine formula rather than replicating
`CosineAnnealingLR`'s exact `.step()`-count-driven internal state (same
schedule shape, an up-to-one-epoch cosmetic phase difference). Training
lives in Rust — not orchestrated from Python via the individual
`encode`/`evolve`/`phase_similarity` bridge calls — because Project Plan §4
rule 2 ("the Python layer contains no numerics") applies to the training
loop itself, not just the forward/backward math; `crates/prin-py/src/bindings/trainer.rs`'s
`train_phase_tracker` is the thin PyO3 orchestration entry point, and
`python/prin/train.py` converts its result into `prin.nn.PhaseTracker` +
a `TrainingResult` dataclass. This is why `python/prin/train.py` is a new,
narrow module rather than living in `prin.nn` (a layer/bridge namespace) or
Phase-5's reserved `prin.experiments` stub (the bigger fair-comparison
statistical framework) — see that module's own docstring for the
distinction.

### Optimizer bridges — rank convention

`SyncGd`/`Scalr` are rank-generic in `prin-train`; the PyO3 bridge fixes
`D = 1` and the Python `torch.optim.Optimizer` wrapper flattens each
parameter to 1-D before calling `step`, reshaping the result back — the
standard flatten/update/reshape pattern for wrapping a per-element
optimizer over arbitrary parameter shapes. `Rip` is inherently rank-2 (one
square coupling matrix, fixed at construction), matching `RIPOptimizer`'s
actual reference contract. Full rationale: `crates/prin-py/src/bindings/optim.rs`
and `python/prin/nn/optimizers.py` module docs. **Deliberate MVP scope
boundary**: `state_dict`/`load_state_dict` round-trip only the scalar/history
optimizer state (JSON); the momentum buffer (non-empty only when
`momentum != 0.0`, not the reference default) is not yet included —
documented, not silently dropped.

## Acceptance criteria → evidence map

| Criterion | Verdict | Evidence |
|---|---|---|
| **PhaseTracker reaches at least the registered 3.0 IP threshold in validation runs** | **GREEN** | Registered threshold: `y4q1_7_statistical_summary.json` (the only PRINet 3.0 artifact using real `generate_dataset` sequences with actually-trained models, tied to a preregistration hash) — PhaseTracker mean IP `0.99868` across seeds `(42,123,456)`, protocol `train_seqs=50, val_seqs=10, n_objects=4, n_frames=20, max_epochs=20, patience=5, match_threshold=0.1`. PRIN reproduction (`crates/prin-train/tests/integration_temporal_clevr_n.rs`, identical protocol): **mean IP = 1.00000** (per-seed `[1.0, 1.0, 1.0]`, all three seeds ran the full 20 epochs without early stopping), wall time 115.6s. `1.00000 >= 0.99868` — criterion met. Raw evidence: `DOCS/experiments/0105-wp027-temporal-clevr-n-validation.json`. This is Phase-4-gate validation evidence, not a Phase 7 pre-registered scientific comparison (no SlotAttention head-to-head claim is made here). |
| **Gradchecks green** | **GREEN** | Every previously-existing per-method gradcheck (`encode`/`evolve`/`phase_similarity`, `HybridPRINetV2.forward`, `OscillatoryAttention.forward`, `SlotAttentionModule`/`TemporalSlotAttentionMOT`, four ablation variants — ~1,342 lines across 7 files) remains green, unmodified. **New this session ("full gradcheck")**: `tests/test_train_bridge_phase_tracker.py::TestPhaseTrackerGradients::test_composed_encode_evolve_similarity_gradcheck` chains `encode -> evolve -> phase_similarity` into one `torch.autograd.gradcheck` call — the composed graph the mission text asks for, previously only tested method-by-method. Full suite: `pytest tests/ -m "not slow and not gpu"` — 441 passed, 8 deselected. |
| **Bridge overhead <5%** | **NOT MET (confirms DV-021; flagged for S2/S3, not fixed here)** | Per the session brief's own instruction ("start from that evidence rather than re-deriving it"), re-measured DV-021's `ResonanceLayer` shapes with the identical 5-run, process-level median-of-medians protocol: `small_32osc_16dims_8batch` Rust **6.8475 ms** (spread 6.6517–6.9986 ms) vs. Python **9.4350 ms** (spread 9.3655–9.7061 ms) -> **+37.8% overhead**; `moderate_128osc_64dims_32batch` Rust **364.4204 ms** (spread 358.9076–367.5011 ms) vs. Python **388.2624 ms** (spread 373.9586–392.5126 ms) -> **+6.5% overhead**. Both numbers closely reproduce DV-021's originally-recorded figures (+39.8%/+5.3%), independently corroborating that this is a stable, reproducible architectural cost (`torch.autograd.Function.apply()`/`from_dlpack()` fixed dispatch), not measurement noise. **New bridge-profiling coverage** (`PhaseTracker::forward`/`match_frames`, no prior bench existed): small shape (4 objects) Rust **1.1292 ms** (spread 1.1187–1.1527 ms) vs. Python **1.0062 ms** (spread 0.9994–1.0219 ms) — Python measured *faster*, i.e. no positive overhead at this scale; moderate shape (32 objects) Rust **2.4440 ms** but with a wide 2.2291–3.9156 ms spread (~75%, this host was under other load during part of this run — reported honestly, not smoothed over) vs. Python's tight **2.1006 ms** (spread 2.0849–2.1066 ms). PhaseTracker's comparison is scoped to the forward-only `match_frames` path deliberately: unlike `ResonanceLayer`, PhaseTracker has no single composed *differentiable* Python entry point to measure a matching forward+backward round trip against (see `phase_tracker_bridge.rs`'s module docs). **Verdict: the `<5%` target remains unmet for the criterion's original, decisive case (`ResonanceLayer`)** — this is the same DV-021 gap, now with fresh independent corroboration; S1 cannot itself land a plan amendment or close a deviation-register item (that is an S3 mechanism gated on an S2 finding), so this is stated plainly here for S2/S3 disposition exactly as WP-025 S1 did. |
| **Phase 4 tag gate passes without treating pilot data as campaign evidence** | **Evidence assembled; gate itself is a maintainer/S4 action** | The IP-threshold validation run is explicitly labeled non-campaign evidence (see above and the JSON artifact's own `purpose` field); DV-005 (CUDA) is addressed with a recommendation, not silently left open (see below); DV-021 is re-measured and its architectural-cost conclusion independently corroborated, not asserted from a single pilot. S1 assembles the evidence the gate needs; the gate decision (tag/release) is out of S1's authority per the Session Cycle (S4/maintainer). |

## Bridge profiling — measurement detail

Both Rust (criterion) and Python (`pytest-benchmark`) sides measured via 5
independent process-level invocations (not just each tool's own in-process
sampling), reporting the median-of-medians and the run-to-run spread —
the exact protocol DV-021's S3 remediation established
(`DOCS/experiments/0097-wp025-s1-handoff.md`).

| Shape | Rust median-of-medians | Rust spread | Python median-of-medians | Python spread | Overhead |
|---|---|---|---|---|---|
| `resonance_layer_bridge_baseline/small_32osc_16dims_8batch` | 6.8475 ms | 6.6517–6.9986 ms (~5%) | 9.4350 ms | 9.3655–9.7061 ms (~3.6%) | **+37.8%** |
| `resonance_layer_bridge_baseline/moderate_128osc_64dims_32batch` | 364.4204 ms | 358.9076–367.5011 ms (~2.4%) | 388.2624 ms | 373.9586–392.5126 ms (~4.8%) | **+6.5%** |
| `phase_tracker_bridge_baseline/small_4obj_28osc` (new) | 1.1292 ms | 1.1187–1.1527 ms (~3%) | 1.0062 ms | 0.9994–1.0219 ms (~2.2%) | **−10.9%** (Python faster) |
| `phase_tracker_bridge_baseline/moderate_32obj_28osc` (new) | 2.4440 ms | 2.2291–3.9156 ms (~75%, host noise — see caveat) | 2.1006 ms | 2.0849–2.1066 ms (~1%) | not reliable at this spread |

Reproduce with:
```powershell
cargo bench -p prin-train --bench resonance_layer_bridge
cargo bench -p prin-train --bench phase_tracker_bridge
.venv\Scripts\python -m pytest tests/test_train_bridge.py::TestTrainBridgeBenchmarks tests/test_train_bridge_phase_tracker.py::TestPhaseTrackerBenchmarks --benchmark-only
```

## Serialization acceptance

`crates/prin-train/tests/integration_checkpoint_resume.rs`: trains
PhaseTracker for 4 epochs on a small dataset, checkpoints the *trained*
(non-freshly-initialized) model via `into_record`/`load_record`
(`BinBytesRecorder<DoublePrecisionSettings>`), reloads into a fresh
instance built from a *different* seed (so any post-load agreement is
attributable to the checkpoint, not coincidental identical init), and
confirms bit-identical `evaluate_phase_tracker` metrics and
`track_sequence` output (`identity_preservation`, `identity_matches`) on
held-out sequences. This extends the existing per-module
`record_roundtrip_preserves_parameters` unit tests (which only exercise
freshly-seeded, untrained parameters) to a genuinely trained-state
checkpoint — the gap "serialization" in the mission text calls for.

## DV-005 recommendation (CUDA Burn backend — Phase 5 scope decision)

Per the session brief, this is the concrete checkpoint to decide whether a
CUDA Burn backend enters Phase 5 scope. **Recommendation: do not pull it
into near-term Phase 5 scope absent a concrete workload that needs it.**
Rationale: every `prin-train` workload measured or delivered so far
(temporal CLEVR-N's `n_objects<=32` detections, `n_osc<=28` oscillators,
tiny MLPs) runs the full 3-seed, 20-epoch canonical training protocol in
115.6s on CPU (`--release`) — GPU dispatch overhead would very plausibly
*dominate* at this scale rather than help, the same class of finding
DV-021 already demonstrates for the bridge-crossing cost. CUDA acceleration
is a `prin-kernels`/large-N-simulation concern (already delivered in Phase
3 for `N=1M`-oscillator dynamics), not a `prin-train` MLP-scale concern. No
Rust code changes were made toward a CUDA Burn backend this session (out of
scope, and DV-005's own text already established this is materially larger
scope than bridge work). **This is a recommendation for S3/maintainer
disposition, not a self-issued amendment** — S1 cannot land a plan
amendment (Development Workflow and Audit Standards §3: that is an S3
mechanism, gated on an S2-raised finding); the formal DV-005 status update
is S4's register-review responsibility.

## DV-019 recurrence (unrelated pre-existing flake, new evidence)

`cargo test --workspace --features strict-checks` hit two *different*
tests failing across two separate runs under full-workspace parallel
thread contention: `hybrid::tests::gradients_flow_to_every_layer_class`
(first run) and `phase_tracker::tests::gradients_flow_to_encoder_and_dynamics_parameters`
(second run, immediately after). Both passed in isolation
(`cargo test -p prin-train --lib <test> -- --test-threads=1`) and the
entire workspace test suite (including `strict-checks`) passed cleanly
under `--test-threads=1`. Neither `hybrid.rs` nor `phase_tracker.rs` was
touched in a way that would introduce a new gradient-flow bug (the
existing gradient tests were not modified). This is the same DV-019 class
(WP-022's frozen-scope near-zero-gradient-pruning flake, thread-contention-dependent)
recurring under increased contention from this session's new test files
(`dataset.rs`, `losses.rs`, `trainer.rs`, two new integration test files) —
DV-019's documented mechanism explicitly predicts exactly this
(WP-023/WP-024/WP-025 each independently observed a new-test-count-driven
recurrence). **New evidence value for a future fix**: this recurrence
shows the flake is not confined to `bands.rs`'s originally-reported
`w_gamma` knife-edge gradient — it now affects at least three different
modules' gradient-presence assertions, strengthening the case for DV-019's
own candidate mitigation (a) (pin gradient-flow tests to single-threaded
execution) over (b) (per-test fixture strengthening), since (a) would fix
every occurrence uniformly regardless of which module's test trips it.

## Quality gates (S1 verification)

| Gate | Command | Result |
|---|---|---|
| Format (workspace) | `cargo fmt --all -- --check` | PASS |
| Clippy (workspace) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Workspace tests | `cargo test --workspace` | PASS — all crates `test result: ok` (prin-train lib: 292 passed; full workspace including doctests, parity, integration: green; the expensive `#[ignore]`d IP-threshold test excluded by default, run separately — see above) |
| Workspace tests (strict-checks) | `cargo test --workspace --features strict-checks -- --test-threads=1` | PASS (single-threaded to avoid the DV-019-class flake — see above) |
| Rustdoc | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS — 0 warnings |
| `cargo audit` | `cargo audit` | Exit code 0; 2 allowed warnings, both pre-existing and unchanged (`paste` RUSTSEC-2024-0436/amendment #9, `bincode` RUSTSEC-2025-0141/amendment #27) — no new advisory from the new `serde`/`serde_json` direct dependencies (both were already workspace dependencies, reached transitively through `prin-train`) |
| Coverage (new/changed Rust) | `cargo llvm-cov -p prin-train --lib --show-missing-lines` | `dataset.rs` 99.75% lines / 99.56% regions; `losses.rs` 100%; `trainer.rs` 96.26% lines — all ≥95% |
| Criterion benches | `cargo bench -p prin-train --bench resonance_layer_bridge` / `--bench phase_tracker_bridge` | PASS — see "Bridge profiling" above |
| ruff check/format | `ruff check python/ tests/ benchmarks/ tools/`, `ruff format --check ...` | PASS (0 findings) |
| mypy --strict | `mypy python/prin --strict` | PASS — 27 files, 0 issues |
| interrogate | `python -m interrogate -c pyproject.toml python/prin` | PASS — 100.0% (231/231) |
| bandit | `python -m bandit -r python/prin -c pyproject.toml` | PASS — 0 issues (2,813 lines) |
| `pip_audit` | `pip_audit .`, `pip_audit -r DOCS/sphinx/requirements.txt` | PASS — 0 issues both |
| Python fast suite | `pytest tests/ -m "not slow and not gpu"` | PASS — 441 passed, 8 deselected |
| Python full suite (+parity) | `pytest tests/ parity/` | PASS — 959 passed |
| Snyk Code | pre-flight check | **BLOCKED** — same standing condition as every prior cycle (R23: maintainer-confirmed permanent Snyk-CLI-only posture, unauthenticated on this host). CI `snyk` workflow is the authoritative gate at S4's push. |
| Snyk Open Source | Not run | Cargo/pip not Snyk-supported for local CLI scanning in this posture (R23); `cargo audit`/`pip_audit` are the authoritative ecosystem-native gates |

## Out-of-scope discoveries

- **Optimizer momentum-buffer checkpointing** — `SyncGd`/`Scalr`'s
  `state_dict`/`load_state_dict` round-trip scalar/history state only, not
  the momentum buffer (non-empty only when `momentum != 0.0`, not the
  PRINet 3.0 default). Documented in `crates/prin-py/src/bindings/optim.rs`'s
  module docs; deferred, not silently dropped.
- **`float32` bridge support** — unchanged from WP-025's original
  out-of-scope note; still `float64`-only throughout.
- **Standalone Python-facing temporal-CLEVR-N dataset API** —
  `python/prin/datasets.py` is an existing empty stub explicitly reserved
  for "the temporal CLEVR-N sequence generator" (plus CIFAR-10/Fashion-MNIST
  loaders, a materially larger and unrelated scope). This session's
  dataset generator (`crates/prin-train/src/dataset.rs`) is consumed
  entirely internally by the Rust-native trainer; no standalone
  `SequenceData`-returning Python API was built, since nothing in this
  session's contract required one. Left for whichever future WP actually
  populates `datasets.py`.
- **CUDA Burn backend** — see "DV-005 recommendation" above.
- **Global (vs. Burn's per-tensor) gradient-norm clipping** — documented
  deviation in `trainer.rs`'s module docs; not attempted this session
  (would require hand-rolling a cross-parameter norm reduction over
  `GradientsParams`).

## Parity-evidence disposition

Grepped/checked against the archived PRINet 3.0 reference
(`DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/`) for every
new numerical primitive in this session, per the S1 exit-gate requirement:

- **`generate_temporal_clevr_n`/`generate_dataset`** — a directly comparable
  reference exists (`src/prinet/utils/temporal_training.py:68-253`).
  Bit-parity is architecturally out of scope (RNG-stream substitution, see
  "Architecture" above); *formula* parity evidence is the hand-computed
  elastic-bounce test (`elastic_bounce_matches_hand_computed_trajectory`)
  plus per-perturbation unit/property tests verifying each formula's
  observable effect (occlusion zeroing, swap semantics, noise application,
  bounds).
- **`hungarian_similarity_loss`/`temporal_smoothness_loss`** — a directly
  comparable reference exists (`temporal_training.py:261-336`). Formula
  parity evidence: hand-computed values for both (perfect-diagonal-gives-
  near-zero-loss, uniform-similarity-gives-`ln(2)`, MSE-between-known-matrices)
  in `losses.rs`'s own unit tests.
- **`TemporalTrainer`** — a directly comparable reference exists
  (`temporal_training.py:454-869`). Structural parity (Adam + warmup/cosine
  LR + gradient clipping + early stopping with best-checkpoint restore) is
  documented with two explicit deviations (per-tensor vs. global gradient
  clipping; scalar cosine formula vs. PyTorch scheduler step-count state) —
  see "Architecture" above. No golden-value parity test was written for the
  trainer as a whole (the reference's own multi-epoch training runs are
  themselves stochastic and not deterministically comparable across RNG
  implementations); correctness is instead evidenced by the acceptance-
  criterion validation run reaching/exceeding the reference's own registered
  outcome.
- **`SyncGdBridge`/`ScalrBridge`/`RipBridge`** — no new numerics; each
  bridge calls the already-parity-tested `crates/prin-train/tests/parity_optimizers.rs`
  Rust implementations directly (`sync_gd_step_matches_prinet_3_0`,
  `scalr_step_basic_matches_prinet_3_0`, `rip_step_matches_prinet_3_0`, all
  unmodified this session).
