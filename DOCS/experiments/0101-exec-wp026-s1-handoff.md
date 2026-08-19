# Exec-WP-026 S1 Handoff Note

**Session:** Exec-WP-026 S1 — executive secondary coding session, run outside
the numbered WP-026 S1–S4 cycle (sessions 0101–0104), maintainer-directed
(same disposition class as the WP-025 S3-exec session — see
`DOCS/sessions/SESSION_REGISTER.md` changelog, entry dated 2026-08-19)
**Date:** 2026-08-19
**Status:** Delivered; both this session's and WP-026 S1's (session 0101)
deliverables are handed off together to the already-registered WP-026 S2
audit (session 0102), currently `PLANNED`. This session does not
self-certify completion (Development Workflow and Audit Standards).

## Mission recap

WP-026 S1 (session 0101, commit `f34de14`) delivered six new `prin-train`
modules with full Rust correctness but explicitly deferred their
`crates/prin-py/` PyO3 bindings and `python/prin/nn/` `torch.nn.Module`
wrappers — both declared in WP-026's own scope
(`DOCS/reports/025-project-state.md` §6) — as a documented, evidence-backed
scope decision (`DOCS/experiments/0101-wp026-s1-handoff.md`, "Not delivered
this session"), reasoning that replicating WP-025's full bridge depth for six
modules in one S1 session budget was disproportionate and risked under-tested
bridge code. The maintainer directed that this deferred scope be executed now,
in this dedicated executive session, rather than left for a future WP.

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-py/src/bindings/train_support.rs` | **New.** Generalizes WP-025's `train.rs` rank-2-specific DLPack decode/encode/checkpoint helpers to arbitrary tensor rank `D` via const generics (`tensor_from_dlpack_with_data`, `optional_tensor_from_dlpack_with_data`, `tensor_from_dlpack`, `plain_tensor_from_dlpack`, `export_tensor`, `load_checkpoint_record`, `record_to_bytes`), so every bridge module below reuses one implementation. |
| `crates/prin-py/src/bindings/train.rs` | Refactored (behavior-preserving) to call the shared `train_support` helpers at `D = 2` instead of its private rank-2 copies. |
| `crates/prin-py/src/bindings/attention.rs` | **New.** `OscillatoryAttentionBridge`/`Ctx` — single differentiable `forward(x, phase=None)`; rejects non-zero `dropout` (see "Discovered hazards" below). |
| `crates/prin-py/src/bindings/phase_tracker.rs` | **New.** `PhaseTrackerBridge` — `encode`/`evolve`/`phase_similarity` differentiable (multi-output vector-Jacobian-product); `match_frames` (renamed from `forward`)/`track_sequence` non-differentiable; `TrackingResult` Python mirror. |
| `crates/prin-py/src/bindings/hybrid.rs` | **New.** `HybridPRINetV2Bridge`/`Ctx` — single differentiable `forward(x)`; also rejects non-zero `dropout`. |
| `crates/prin-py/src/bindings/slot_attention.rs` | **New.** `SlotAttentionModuleBridge`, `TemporalSlotAttentionMOTBridge` — differentiable `forward`/`process_frame`/`slot_similarity` with the seed-snapshot recompute contract (see below); non-differentiable `match_frames`/`track_sequence`. |
| `crates/prin-py/src/bindings/ablation.rs` | **New.** `PhaseTrackerFrozenBridge`/`SlotAttentionFrozenBridge` (`.inner` accessor over a clone of the wrapped tracker, reusing `phase_tracker.rs`/`slot_attention.rs`'s bridges); `PhaseTrackerStaticBridge`/`SlotAttentionNoGRUBridge` (own reimplemented differentiable methods). |
| `crates/prin-py/src/bindings/allocation.rs` | **New.** `AdaptiveOscillatorAllocatorBridge`, `DynamicPhaseTrackerBridge`, `OscillatorBudget`, `estimate_complexity` — all non-differentiable. |
| `crates/prin-py/src/lib.rs`, `bindings/mod.rs` | Register the six new bridge modules. |
| `crates/prin-train/src/{attention,phase_tracker,hybrid,slot_attention,ablation,allocation}.rs` | Added `validate_shapes()` to `OscillatoryAttention`, `HybridPRINetV2`, `PhaseTracker`, `SlotAttentionModule`, `TemporalSlotAttentionMOT`, `PhaseTrackerStatic`, `SlotAttentionNoGRU`, `AdaptiveOscillatorAllocator` (WP025-F1 precedent) — see "Discovered hazards" below for why this was necessary, not optional polish. `AdaptiveOscillatorAllocator` also gained a `complexity_dim: usize` field (needed for the check; previously implicit in the MLP's own shape). |
| `python/prin/nn/_bridge.py` | **New.** Generic `apply_rust_bridge`/`_RustBridgeFunction`: one `torch.autograd.Function` covering arbitrary tensor input/output arity, so each differentiable entry point below is a few lines of glue. |
| `python/prin/nn/{attention,phase_tracker,hybrid,slot_attention,ablation,allocation}.py` | **New.** `torch.nn.Module` wrappers (`AdaptiveOscillatorAllocator`/`DynamicPhaseTracker` are plain classes — no differentiable `forward` to justify `nn.Module`). |
| `python/prin/nn/__init__.py` | Re-exports all new symbols; docstring header updated (moved delivered names out of "planned symbols"). |
| `python/prin/_prin_core.pyi` | Type stubs for every new Rust-exposed class/function. |
| `python/prin/nn/README.md` | Rewritten from a stale pre-WP-025 stub to describe delivered symbols. |
| `tests/test_train_bridge_{attention,phase_tracker,hybrid,slot_attention,ablation,allocation}.py` | **New.** 86 new tests. |
| `crates/prin-py/README.md`, `crates/prin-train/README.md`, `crates/README.md` | Updated to describe this session's delivery and close the WP-026 S1 carried-scope note. |

## Discovered hazards (found and fixed this session, not pre-existing bugs carried forward)

1. **Checkpoint-validation bug (real correctness defect, fixed).** Burn's
   `constant!` macro (`crates/prin-py`'s dependency, `burn-core`) gives plain
   `usize`/`f64` struct fields a `Record = ConstantRecord` whose
   `load_record(self, _record) -> Self { self }` **ignores the record
   entirely** — only `Param<Tensor>` fields take on a loaded record's values.
   My first `load_state_dict` implementations compared a post-load field
   (e.g. `candidate.n_osc()`) against the pre-load value on `self` — since
   that field is never touched by `load_record`, the comparison always
   passed trivially, meaning a checkpoint from a differently-configured
   module would silently corrupt the `Param` tensors (which *do* take the
   loaded shape) while leaving the metadata fields internally inconsistent.
   Caught by this session's own `test_checkpoint_rejects_complexity_dim_mismatch`
   test (initially failing — the first `AdaptiveOscillatorAllocator::
   validate_shapes` draft checked `mlp[2]`'s shape, which is invariant to
   `complexity_dim`; fixed to check `mlp[0]` against a newly-added
   `complexity_dim` field), not by inspection. Fixed by adding
   `validate_shapes()` to every affected `prin-train` type (WP025-F1
   precedent) and calling it after every `load_record`, before committing.
2. **`Dropout` non-determinism under autodiff.** `burn::nn::Dropout::forward`
   applies a stochastic Bernoulli mask whenever `B::ad_enabled()` and
   `prob != 0.0`, drawn from the backend's own unseeded RNG — breaking both
   `torch.autograd.gradcheck` determinism and the recompute-on-backward
   design (the backward recompute would apply a *different* mask than the
   original forward). `OscillatoryAttentionBridge`/`HybridPRINetV2Bridge`
   reject any non-zero `dropout` at construction with a documented
   `ValueError`, rather than silently producing incorrect gradients.
3. **Per-call stochastic recompute (`SlotAttentionModule`/
   `TemporalSlotAttentionMOT`).** Both draw fresh noise from a caller-supplied
   `Seed` on every call, not just at construction. Each `*Ctx` snapshots a
   `Seed::clone()` from immediately before the original forward call and
   re-clones that snapshot for every `backward()` recompute — `Seed` is
   deterministic and `Clone` (its `Pcg64` state is captured exactly), so this
   reproduces bit-identical noise without consuming the caller's own stream a
   second time. Verified by `gradcheck` (which requires a *fresh* `Seed`
   passed into the wrapped closure at every finite-difference call, not one
   mutable object reused across calls — documented at length in
   `tests/test_train_bridge_slot_attention.py`'s module docstring, since this
   is a genuine gotcha for anyone writing further tests against these
   bridges).
4. **`gradcheck` precision floor (DV-018-class, not a new hazard).** The
   GRU's sigmoid/tanh gates and `PhaseTracker`/`PhaseTrackerStatic`'s
   multi-step PAC coupling hit the same `burn-tensor` f32-downcast precision
   floor `GatedPhaseActivation`'s gradcheck already documented at WP-025,
   requiring the same loosened `eps=1e-4, atol=3e-3` tolerance (empirically
   verified: the default `eps=1e-6, atol=1e-4` fails by a
   further-loosening-resolves-it margin, confirming precision floor, not a
   structural defect).
5. **`gradcheck` flakiness from a `relu` kink (test-methodology issue, not a
   bridge defect).** Two tests using unseeded `torch.rand`/`torch.randn`
   occasionally (~1-in-5 runs, observed empirically) drew an input whose
   post-linear pre-activation landed close enough to a `relu` kink for the
   finite-difference probe to straddle it. Fixed with a local
   `torch.Generator` (not global `torch.manual_seed`, which leaked into
   other tests) pinning a draw confirmed clear of the kink; stress-tested 20
   consecutive clean runs of the full new suite after the fix.

## Acceptance criteria → evidence map

| Criterion | Verdict | Evidence |
|---|---|---|
| **Every differentiable entry point is a `torch.autograd.Function` with forward and backward calling Rust** (Coding Standards §3.2) | **GREEN** | `OscillatoryAttention.forward`, `HybridPRINetV2.forward`, `PhaseTracker.{encode,evolve,phase_similarity}`, `SlotAttentionModule.forward`, `TemporalSlotAttentionMOT.{process_frame,slot_similarity}`, `PhaseTrackerStatic.{encode,evolve,phase_similarity}`, `SlotAttentionNoGRU.{process_frame,slot_similarity}` — 13 entry points, each `torch.autograd.gradcheck`-verified in float64. |
| **Non-differentiable methods are not forced into a fake-gradient bridge** | **GREEN** | `match_frames`/`track_sequence` (greedy matching, no gradient) and `allocation`'s entire surface (discrete counts) are plain PyO3 methods; documented in every relevant module's docstring. |
| **Public APIs and checkpoints are compatible** | **GREEN** | Every `Module`-backed bridge has `rust_state_dict`/`load_rust_state_dict` with the WP025-F1 load-into-clone-validate-commit contract; checkpoint round-trip + shape-mismatch-rejection tested for all 9 checkpointable bridges. |
| **Unit/integration/gradient tests cover all variants** | **GREEN** | 86 new Python tests across 6 files; 100% coverage on every new `python/prin/nn` file (`pytest --cov`). 15 new Rust `validate_shapes` regression tests (WP025-F1 pattern) across 6 `prin-train` files. |
| **≥95% coverage on new/changed code** | **GREEN** | Python: 100% (`python/prin/nn/{__init__,_bridge,ablation,allocation,attention,hybrid,phase_tracker,slot_attention}.py`, 372/372 statements). Rust (`prin-train`, the six touched files — `crates/prin-py`'s own PyO3 surface is validated via the Python suite per WP-025's own reporting precedent, not `cargo llvm-cov`, since it is only exercised through the compiled extension): `ablation.rs` 98.54%/100.00%/99.60% (region/function/line), `allocation.rs` 98.14%/97.22%/97.15%, `attention.rs` 97.40%/100.00%/99.40%, `hybrid.rs` 98.10%/100.00%/97.52%, `phase_tracker.rs` 96.01%/97.50%/96.60%, `slot_attention.rs` 98.41%/100.00%/98.90%. |
| **Every quality/security gate green** | **GREEN** | See tables below. |

## Test counts

- **Rust:** `cargo test -p prin-train`: **275** total (was 260 at WP-026 S1
  close) — 246 unit (was 231, **+15** `validate_shapes` regression tests), 14
  parity, 2 `public_api`, 13 doctests (unchanged). `cargo test -p prin-py`: 6
  unit (unchanged — bridge logic is exercised via Python, matching
  `train.rs`'s own WP-025 precedent). `cargo test --workspace`: **1096**
  passed, 0 failed (was 998 at WP-025 close per PSR-025; +98 combines
  WP-026 S1's own additions and this session's 15).
- **Python:** fast suite (`pytest tests/ -m "not slow and not gpu"`): **421**
  passed, 8 deselected (was 335/8 — WP-026 S1 touched no Python; **+86** this
  session). Full suite (`pytest tests/ parity/`): **939** passed (was 853;
  **+86**).

## Quality gates (verification commands, re-run this session)

```powershell
cargo fmt --all -- --check                                              # clean
cargo clippy --workspace --all-targets -- -D warnings                   # clean (exit 0)
set RUSTDOCFLAGS=-D warnings && cargo doc --workspace --no-deps         # 0 warnings
cargo audit                                                             # exit 0; 2 allowed warnings (amendments #9, #27), unchanged — no new dependency
cargo test --workspace                                                  # 1096 passed, 0 failed
cargo llvm-cov -p prin-train --summary-only                             # all 6 touched files >=95% region/function/line
.venv\Scripts\ruff check python/ tests/                                 # clean
.venv\Scripts\ruff format --check python/ tests/                        # clean
.venv\Scripts\mypy python/prin --strict                                 # 0 issues (tests/ not covered by this gate, matching WP-025 precedent)
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin       # 100.0% (213/213)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                   # 0 issues
.venv\Scripts\python -m pip_audit .                                     # 0 issues
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu"         # 421 passed, 8 deselected
.venv\Scripts\python -m pytest tests/ parity/                          # 939 passed
.venv\Scripts\python -m pytest tests/test_train_bridge*.py --cov=prin.nn --cov-report=term-missing -m "not slow"  # 100% on every new file
snyk code test crates/prin-train                                       # 0 issues (authenticated this session)
snyk code test crates/prin-py                                          # 0 issues
snyk code test python/prin/nn                                          # 0 issues
```

Snyk Open Source: N/A for Cargo (R23 disposition, unchanged); no new Python
dependency added, so no new `pip-audit`-covered surface either. GitHub secret
scanning/push protection: unchanged standing condition (disabled for this
private repo, R23/DV-009).

## Parity-evidence disposition

No new numerical formulas were introduced this session — every bridge
delegates entirely to the already-parity-tested Rust core WP-026 S1 closed
(`tests/parity_attention.rs`, `tests/parity_phase_tracker.rs`, and the
component-parity argument for `HybridPRINetV2`/trackers documented in
`crates/prin-train/README.md`). This session's own tests validate the FFI
boundary contract (dtype/shape/`gradcheck`/checkpoint), not numerics —
duplicating WP-026 S1's parity evidence here would be redundant, not
additive.

## Out-of-scope items (unaffected by this session, recorded not silently dropped)

- `use_conv_stem` CNN stem, masked attention, `SlotAttentionCLEVRN`,
  `create_ablation_tracker` string factory — already recorded as WP-026 S1
  out-of-scope discoveries.
- CUDA DLPack path (DV-005) and the `<5%` boundary-overhead target (DV-021)
  — both already concretely checkpointed to WP-027 S1; this session's
  bridges inherit the same CPU-only, DLPack-`torch.autograd.Function`
  architecture as WP-025's, so neither DV item is re-litigated here.
- A `torch.optim.Optimizer` wrapper over `SyncGd`/`Rip`/`Scalr` — still
  unbridged; every bridge parameter in this crate is Rust-owned and trained
  the same way WP-025's are, not via `torch.optim`.
- `AdaptiveOscillatorAllocator::validate_shapes`'s residual gap: a checkpoint
  produced by a *different strategy* (`Rule` vs. `Learned`) than the target
  allocator is not rejected — `Option<[Linear<B>; 3]>`'s `load_record`
  silently keeps `self`'s `Some`/`None` variant on a mismatch (a silent
  no-op, not a shape-corruption risk the way the `complexity_dim`-within-
  `Learned` case was), documented in the Rust type's own rustdoc. Lower
  severity than the fixed bug (no value corruption, just a discarded load)
  and out of this session's bounded scope; flagged for the S2 auditor.
