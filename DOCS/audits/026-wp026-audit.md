# PRIN Audit Report — Cycle 026 / WP-026

**Date:** 2026-08-19
**Auditor:** Qwen Code (AI pair), maintainer-reviewed
**Scope:** WP-026 "PhaseTracker, Hybrid, baselines, and allocation" — `crates/prin-train/src/{attention,phase_tracker,hybrid,slot_attention,ablation,allocation,support,error}.rs` (new/touched); `crates/prin-py/src/bindings/{attention,phase_tracker,hybrid,slot_attention,ablation,allocation,train_support}.rs` (new); `crates/prin-py/src/bindings/train.rs` (refactored); `python/prin/nn/{__init__,_bridge,attention,phase_tracker,hybrid,slot_attention,ablation,allocation}.py` (new/rewritten); `python/prin/_prin_core.pyi` (extended); `crates/prin-train/tests/{parity_attention,parity_phase_tracker}.rs` (new); `tests/test_train_bridge_{attention,phase_tracker,hybrid,slot_attention,ablation,allocation}.py` (new)
**Sessions:** 0101 (S1 — Coding) + executive secondary coding session (PyO3/Python wrappers) implementation; 0102 (S2 — Audit) this audit
**Active brief:** `DOCS/sessions/phase-4/0102-wp026-s2-phasetracker-hybrid-baselines-and-allocation.md`
**Git state:** `main` @ `96e6ce4` (S1 commit range `24cba8e..96e6ce4`, two commits: `f34de14` Rust core + `96e6ce4` PyO3/Python wrappers); working tree clean at audit time
**Verdict:** **PASS-WITH-FINDINGS**

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | All six modules delivered (Rust core + PyO3 bridges + Python wrappers); out-of-scope discoveries explicitly recorded, not silently expanded |
| Plan/architecture conformance (A2) | ✅ | Crate layering respected; zero `unsafe` in new code; no Python numerics; explicit `Seed` flow throughout (no `Backend::seed` calls) |
| Tests in tandem + coverage (A3) | ✅ | 1096 Rust workspace tests (0 failed); 939 Python tests (0 failed); all new/touched Rust files ≥95% region/function/line; Python `nn/` 100% (372/372 statements) |
| Numerical parity + invariants (A4) | ✅ | Two new golden-value parity tests (`OscillatoryAttention`, `PhaseTracker.phase_similarity`); component-level parity for `HybridPRINetV2` follows established amendment #19 precedent |
| Quality gates (A5) | ✅ | fmt/clippy/ruff/mypy/rustdoc all independently reproduced clean |
| Security (A6) | ✅ | Zero `unsafe` in new modules; bandit/ruff-S/bandit clean; `cargo audit` exit 0 with 2 allowed warnings (amendments #9, #27); `pip-audit` clean |
| Docstring/doc coverage (A7) | ✅ | interrogate 100% (213/213); rustdoc 0 warnings under `-D warnings` |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/stub markers; `__all__` complete (16 symbols); `.pyi` stubs present; no orphan files |
| CI status (A9) | ✅ (local-gate stand-in) | Nothing pushed yet this cycle; every gate independently reproduced locally, all green |
| Artefact trail (A10) | ✅ | PSR-025, prior audits 001–025, session register, S1 handoff notes, and deviation ledger all present and consistent |

**Verdict rationale:** two D4 findings (documented design limitations with no correctness impact). No D1/D2/D3. Per Development Workflow and Audit Standards §5, this yields `PASS-WITH-FINDINGS`.

---

## 2. Methodology

All commands executed on Windows (local host), Python 3.14.0, Rust toolchain per `rust-toolchain.toml`. Every claim below is backed by command output captured during this audit session.

```powershell
# Format and lint
cargo fmt --all -- --check                                              # exit 0, clean
cargo clippy --workspace --all-targets -- -D warnings                   # exit 0, clean
set RUSTDOCFLAGS=-D warnings && cargo doc --workspace --no-deps         # exit 0, 0 warnings

# Rust tests
cargo test --workspace                                                  # 1096 passed, 0 failed

# Rust coverage (prin-train)
cargo llvm-cov -p prin-train --summary-only                             # all new/touched files ≥95%

# Python lint and type check
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/      # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/  # 64 files already formatted
.venv\Scripts\mypy python/prin --strict                                 # 25 files, 0 issues

# Python docstring coverage
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin       # 100.0% (213/213)

# Security
.venv\Scripts\python -m bandit -r . -c pyproject.toml                   # 0 issues
cargo audit                                                             # exit 0; 2 allowed warnings (amendments #9, #27)
.venv\Scripts\python -m pip_audit .                                     # 0 issues
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt       # 0 issues

# Python tests
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp   # 421 passed, 8 deselected
.venv\Scripts\python -m pytest tests/ parity/ --basetemp=.pytest_basetemp-full                # 939 passed

# Python coverage (nn modules)
.venv\Scripts\python -m pytest tests/test_train_bridge.py tests/test_train_bridge_ablation.py tests/test_train_bridge_allocation.py tests/test_train_bridge_attention.py tests/test_train_bridge_hybrid.py tests/test_train_bridge_phase_tracker.py tests/test_train_bridge_slot_attention.py --cov=prin.nn --cov-report=term-missing -m "not slow" --basetemp=.pytest_basetemp-cov   # 100% on all 8 nn files (372/372)

# Sphinx
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html   # build succeeded, 0 warnings

# Deviation ledger
.venv\Scripts\python tools/check_deviation_ledger.py DOCS/reports/024-project-state.md DOCS/reports/025-project-state.md   # ledger consistency check passed

# Working tree
git status --short                                                      # clean (empty)
```

---

## 3. Detailed findings

### 3.1 A1 — WP/session-brief scope conformance

**Status: ✅ PASS**

All six declared modules delivered with substantive implementations across three layers:

| Module | Rust core (`prin-train/src/`) | PyO3 bridge (`prin-py/src/bindings/`) | Python wrapper (`python/prin/nn/`) |
|---|---|---|---|
| OscillatoryAttention | `attention.rs` (619 lines) | `attention.rs` (256 lines) | `attention.py` (112 lines) |
| PhaseTracker | `phase_tracker.rs` (788 lines) | `phase_tracker.rs` (488 lines) | `phase_tracker.py` (241 lines) |
| HybridPRINetV2 | `hybrid.rs` (642 lines) | `hybrid.rs` (214 lines) | `hybrid.py` (139 lines) |
| SlotAttentionModule + TemporalSlotAttentionMOT | `slot_attention.rs` (948 lines) | `slot_attention.rs` (595 lines) | `slot_attention.py` (292 lines) |
| Ablation variants (4) | `ablation.rs` (835 lines) | `ablation.rs` (914 lines) | `ablation.py` (373 lines) |
| AdaptiveOscillatorAllocator + DynamicPhaseTracker | `allocation.rs` (847 lines) | `allocation.rs` (327 lines) | `allocation.py` (195 lines) |

Supporting infrastructure: `train_support.rs` (159 lines, generic DLPack helpers), `_bridge.py` (123 lines, generic `apply_rust_bridge`), `_prin_core.pyi` (344 lines of new type stubs), `support.rs` (+238 lines of shared helpers), `error.rs` (+47 lines of new error variants).

Two new golden-value parity test files (`parity_attention.rs`, `parity_phase_tracker.rs`); six new Python test files (86 new tests); 15 new `validate_shapes` regression tests across 6 Rust files.

Out-of-scope discoveries explicitly recorded in both S1 handoff notes: `use_conv_stem` CNN stem, masked attention, `SlotAttentionCLEVRN`, `create_ablation_tracker` string factory. No silent scope expansion.

### 3.2 A2 — Plan/architecture conformance

**Status: ✅ PASS**

- **Crate layering:** `prin-train` depends only on `burn`, `prin-dynamics`, and standard library — no dependency on `prin-py` or any Python-related crate. `prin-py` depends on `prin-train` (one-directional, correct).
- **No Python numerics:** All `python/prin/nn/` files delegate computation to Rust via `apply_rust_bridge` (the generic `torch.autograd.Function` in `_bridge.py`). The only `torch.*` references in Python are type annotations, docstring examples, and DLPack capsule decode (`from_dlpack`) — no arithmetic.
- **Explicit Seed flow:** No `Backend::seed` or `rand::` calls in any new `prin-train` module. The `Backend::seed` hazard (shared global `static Mutex`, unsafe under parallel tests) was discovered and fixed during S1 by introducing `support::seeded_linear`/`seeded_gru`/`seeded_standard_normal`, which construct Burn layers directly from this crate's own `Seed` without touching the backend-global RNG. `SlotAttentionModule` takes `&mut Seed` for per-call stochastic noise — a documented, deliberate signature deviation.
- **Checkpoint contract:** Every `Module` has `validate_shapes()` called after `load_record`, preventing the WP025-F1 class of checkpoint-corruption defect. 15 regression tests verify this.

### 3.3 A3 — Tests in tandem + coverage

**Status: ✅ PASS**

**Rust test counts (verified):**
- `cargo test --workspace`: **1096 passed**, 0 failed (was 998 at WP-025 close; +98)
- `cargo test -p prin-train`: **275 total** — 246 unit (`--lib`), 14 parity (7 files), 2 `public_api`, 13 doctests
- New unit tests by file: `attention.rs` 11, `phase_tracker.rs` 16, `hybrid.rs` 9, `allocation.rs` 12, `slot_attention.rs` 17, `ablation.rs` 11, `support.rs` 1 = **77 new** (S1) + **15 `validate_shapes`** (exec) = 92 new unit tests

**Python test counts (verified):**
- Fast suite: **421 passed**, 8 deselected (was 335; +86)
- Full suite: **939 passed** (was 853; +86)
- 86 new tests across 6 files: `test_train_bridge_{attention,phase_tracker,hybrid,slot_attention,ablation,allocation}.py`

**Coverage (Rust, `cargo llvm-cov -p prin-train`, verified):**

| File | Regions | Functions | Lines |
|---|---|---|---|
| `ablation.rs` | 98.54% | 100.00% | 99.60% |
| `allocation.rs` | 98.14% | 97.22% | 97.16% |
| `attention.rs` | 97.40% | 100.00% | 99.40% |
| `hybrid.rs` | 98.10% | 100.00% | 97.51% |
| `phase_tracker.rs` | 96.01% | 97.50% | 96.60% |
| `slot_attention.rs` | 98.41% | 100.00% | 98.90% |
| `support.rs` (touched) | 99.05% | 100.00% | 99.54% |
| `bands.rs` (touched) | 98.11% | 100.00% | 99.25% |

All eight files clear 95% on every metric.

**Coverage (Python, `pytest --cov=prin.nn`, verified):**

| File | Stmts | Miss | Cover |
|---|---|---|---|
| `nn/__init__.py` | 69 | 0 | 100% |
| `nn/_bridge.py` | 26 | 0 | 100% |
| `nn/ablation.py` | 89 | 0 | 100% |
| `nn/allocation.py` | 29 | 0 | 100% |
| `nn/attention.py` | 22 | 0 | 100% |
| `nn/hybrid.py` | 25 | 0 | 100% |
| `nn/phase_tracker.py` | 53 | 0 | 100% |
| `nn/slot_attention.py` | 59 | 0 | 100% |
| **TOTAL** | **372** | **0** | **100%** |

**Gradient tests:** Every differentiable entry point is `torch.autograd.gradcheck`-verified in float64 (13 entry points per exec handoff). Every `Module` has a `gradients_flow_to_*`-class test (or `*_does_not_require_grad` for frozen ablation variants). `OscillatoryAttention` has an analytic-vs-numerical gradcheck (`alpha_gradient_matches_central_finite_difference`).

**No weakened tests:** No tolerance reductions on existing tests observed in the diff. New gradcheck tests use `eps=1e-4, atol=3e-3` (documented DV-018-class precision floor, same as WP-025's established pattern).

### 3.4 A4 — Numerical parity + invariants

**Status: ✅ PASS**

**New golden-value parity tests:**
1. `tests/parity_attention.rs::oscillatory_attention_forward_matches_prinet_3_0` — calls the actual PRINet 3.0 `OscillatoryAttention` class with extracted `state_dict()` weights, `alpha` overridden nonzero, `dropout=0`, external `phase` tensor. `rtol=1e-6, atol=1e-6`. Passed.
2. `tests/parity_phase_tracker.rs::phase_similarity_matches_prinet_3_0` — calls the actual PRINet 3.0 `PhaseTracker.phase_similarity` directly (parameter-free formula). `rtol=1e-6, atol=1e-6`. Passed.

**Component-level parity argument (HybridPRINetV2, trackers, ablation variants):**
`HybridPRINetV2` composes `DiscreteDeltaThetaGamma` (WP-022, `parity_bands.rs`) and `OscillatoryAttention` (this session, `parity_attention.rs`) — both independently parity-tested. The wiring is verified via shape tests, gradient-flow tests, and mathematical invariants (e.g. `forward_returns_log_probabilities` checks `log_softmax` row-sums-to-1). This follows the same "component parity, not whole-network parity" precedent Project Plan amendment #19 established for `BandNetwork`.

**Parity-evidence disposition:** Per the S1 exit-gate requirement, confirmed via `grep`/direct inspection against `DOCS/archive and reference from PRINet 3.0/` before writing any Rust. All ported modules exist and were read in full in the reference tree. Two new golden-value parity tests call the actual PRINet 3.0 reference classes directly.

**Invariant tests:** `phase_similarity_identical_phases_gives_similarity_one`, `phase_similarity_opposite_phases_gives_similarity_near_negative_one`, `proptests::phase_similarity_always_in_range`, `forward_returns_log_probabilities` (row-sums-to-1), `forward_always_finite_and_in_range` (multiple modules), `record_roundtrip_preserves_parameters` (every `Module`).

### 3.5 A5 — Quality gates

**Status: ✅ PASS**

All gates independently reproduced (see §2 for full command output):
- `cargo fmt --all -- --check`: clean
- `cargo clippy --workspace --all-targets -- -D warnings`: exit 0 (Windows incremental-compilation file-lock warnings only, not code warnings)
- `ruff check`: All checks passed
- `ruff format --check`: 64 files already formatted
- `mypy --strict`: 25 files, 0 issues
- `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps`: 0 warnings

### 3.6 A6 — Security

**Status: ✅ PASS**

- **`unsafe` scan:** Zero `unsafe` blocks in any new `prin-train` module (`attention.rs`, `phase_tracker.rs`, `hybrid.rs`, `slot_attention.rs`, `ablation.rs`, `allocation.rs`, `support.rs`, `error.rs`). Zero `unsafe` in new PyO3 bridge files (`train_support.rs`, `attention.rs`, `phase_tracker.rs`, `hybrid.rs`, `slot_attention.rs`, `ablation.rs`, `allocation.rs`). The only `unsafe` references in `bindings/train.rs` are doc comments explaining the zero-`unsafe` design.
- **bandit:** 0 issues (5513 lines scanned)
- **`cargo audit`:** exit 0; 2 allowed warnings (`paste` RUSTSEC-2024-0436/amendment #9, `bincode` RUSTSEC-2025-0141/amendment #27) — unchanged from WP-025 close, no new dependency added
- **`pip-audit`:** 0 issues (project + docs requirements)
- **No secrets:** No API keys, tokens, or credentials in any new file
- **No runtime codegen:** No `eval`, `exec`, or dynamic code generation in Python wrappers

### 3.7 A7 — Docstring/doc coverage

**Status: ✅ PASS**

- **Python:** interrogate 100.0% (213/213) — all new `nn/` files fully documented (see §2 coverage table for per-file breakdown)
- **Rust:** `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` — 0 warnings, including `#![warn(missing_docs)]` and intra-doc-link resolution
- **READMEs:** `crates/prin-train/README.md`, `crates/prin-py/README.md`, `crates/README.md`, `python/prin/nn/README.md` all updated with WP-026 content

### 3.8 A8 — Repository hygiene

**Status: ✅ PASS**

- **TODO/FIXME/HACK/STUB scan:** Zero markers in any new Rust or Python file
- **`__all__`:** `python/prin/nn/__init__.py` line 72 declares `__all__: list[str]` with 16 symbols — all imported names accounted for (`AdaptiveOscillatorAllocator`, `DynamicPhaseTracker`, `GatedPhaseActivation`, `HybridPRINetV2`, `OscillatorBudget`, `OscillatoryAttention`, `PhaseTracker`, `PhaseTrackerFrozen`, `PhaseTrackerStatic`, `ResonanceLayer`, `SlotAttentionFrozen`, `SlotAttentionModule`, `SlotAttentionNoGRU`, `TemporalSlotAttentionMOT`, `TrackingResult`, `estimate_complexity`)
- **Type stubs:** `python/prin/_prin_core.pyi` extended with 344 lines of new stubs covering every Rust-exposed class/function
- **No orphan files:** `git status --short` clean; all new files are in the commit tree
- **`.gitignore`:** Ad-hoc reference generator script (`DOCS/test_and_benchmark_results/wp026_generate_prinet_references.py`) is gitignored per established precedent

### 3.9 A9 — CI status

**Status: ✅ (local-gate stand-in)**

Per the Push and CI cadence (Development Workflow and Audit Standards §3), nothing has been pushed yet this cycle — S1 commits are local only. A9 is verified against local gate reproduction (see §2), all green. Live CI will be evaluated at S4 when the cycle's sole push occurs.

### 3.10 A10 — Artefact trail

**Status: ✅ PASS**

- **PSR-025:** Present at `DOCS/reports/025-project-state.md`, consistent with PSR-024 (verified by `tools/check_deviation_ledger.py`)
- **Prior audits:** `DOCS/audits/025-wp025-audit.md` present, verdict `PASS-WITH-FINDINGS`, all four findings (WP025-F1–F4) recorded as FIXED in PSR-025
- **Session register:** Sessions 0101–0104 registered; 0101 marked COMPLETE, 0102–0104 PLANNED
- **S1 handoff notes:** Two handoff notes present (`DOCS/experiments/0101-wp026-s1-handoff.md` for Rust core, `DOCS/experiments/0101-exec-wp026-s1-handoff.md` for PyO3/Python wrappers), both with detailed acceptance-criteria evidence maps
- **Deviation ledger:** Cumulative table in PSR-025 consistent with PSR-024 (100 → 104 rows, all carried rows unchanged)

---

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP026-F1 | D4 | `crates/prin-train/src/allocation.rs` — `AdaptiveOscillatorAllocator::validate_shapes` | `validate_shapes` does not detect a strategy mismatch (`Rule` vs. `Learned`) between the source and target allocator. `Option<[Linear<B>; 3]>`'s `load_record` silently keeps `self`'s `Some`/`None` variant on a mismatch — a checkpoint from a differently-strategied allocator discards the MLP load without error. No value corruption occurs (the loaded record is simply ignored), but the user receives no diagnostic. | Documentation Standards §2 (rustdoc accuracy) — the limitation is documented in the type's rustdoc, but the runtime behavior is silently permissive where a typed error would be more informative | Consider adding a strategy-variant check to `validate_shapes` (e.g. comparing `self.learned.is_some()` against the record's strategy indicator) and returning `TrainError` on mismatch. Low priority — no data corruption, documented limitation |
| WP026-F2 | D4 | `crates/prin-train/tests/` (absence) | No whole-module golden-value parity test for `HybridPRINetV2.forward`. The module composes already-parity-tested primitives (`DiscreteDeltaThetaGamma` + `OscillatoryAttention` + standard Burn layers), and wiring correctness is verified via shape/gradient/invariant tests — but a full end-to-end weight-transcription parity test (transcribing a `torch.manual_seed`-initialized reference's entire `state_dict` and comparing outputs) would provide an additional wiring-correction safety net. | Testing Standards §1.3 (parity cases for touched primitives) — component-level parity follows amendment #19 precedent, but `HybridPRINetV2` is the canonical hybrid architecture whose wiring is arguably the novel contribution | A bounded, well-scoped remediation: add a `parity_hybrid.rs` test transcribing a small `HybridPRINetV2`'s full weight set from the PRINet 3.0 reference. The weight-transcription pattern is already established by this session's `parity_attention.rs`. Low priority — component parity + invariant tests provide strong coverage already |

---

## 5. Deviation-ledger delta

New findings raised: **WP026-F1** (D4), **WP026-F2** (D4). No D1/D2/D3 findings.

Carried findings re-inspected:
- **DV-005** (CUDA DLPack path): unchanged — still checkpointed to WP-027 S1. WP-026's bridges inherit the same CPU-only DLPack architecture as WP-025's.
- **DV-018** (`burn-tensor` sigmoid f32-downcast): unchanged — WP-026's gradchecks use the same loosened tolerances (`eps=1e-4, atol=3e-3`) as WP-025's, documented at each call site.
- **DV-019** (`gradients_flow_to_every_parameter` flake): unchanged — not triggered during this audit's test runs, but the pre-existing risk remains.
- **DV-021** (boundary overhead): unchanged — WP-026's bridges inherit the same PyO3/DLPack dispatch architecture; no new measurement attempted.

---

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS**

Two D4 findings, no D1/D2/D3. The WP-026 delivery is comprehensive, well-tested, and architecturally sound. The Rust numerical core is authoritative; the PyO3 bridges and Python wrappers are thorough and correctly delegate all computation to Rust. Coverage exceeds gates on every metric. Security posture is clean.

**Ordered S3 action list:**

1. **WP026-F1** (D4): Add strategy-variant check to `AdaptiveOscillatorAllocator::validate_shapes`, or explicitly document the silent-discard behavior as an accepted limitation in the deviation ledger.
2. **WP026-F2** (D4): Add `parity_hybrid.rs` whole-module golden-value parity test for `HybridPRINetV2.forward`, or formally accept component-level parity as sufficient (same class as amendment #19's `BandNetwork` disposition).

Both findings are low-priority D4 items. S3 may fix, amend, or explicitly carry either to the next cycle (max one carry per Development Workflow and Audit Standards §5).

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| *(pending S3)* | | | |

**Delta re-audit date:** *(pending S3)* — **Result:** *(pending S3)*
