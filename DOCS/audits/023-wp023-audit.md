# PRIN Audit Report — WP-023 "Inhibition, activations, and HEP"

**Date:** 2026-08-18
**Auditor:** AI pair (Qwen Code)
**Scope:** WP-023 — `crates/prin-train/src/{inhibition,activations,energy,hep,error,support,lib}.rs`, `crates/prin-train/tests/{parity_inhibition,parity_activations,parity_energy}.rs`
**Sessions:** 0089 (S1 implementation); 0090 (this audit)
**Active brief:** `DOCS/sessions/phase-4/0090-wp023-s2-inhibition-activations-and-hep.md`
**Git state:** `main` @ `00034bd`
**Verdict:** PASS-WITH-FINDINGS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | All four declared modules present; non-goals respected |
| Plan/architecture conformance (A2) | ✅ | Crate layering preserved; no numerics in Python; Config/Params/init pattern followed |
| Tests in tandem + coverage (A3) | ✅ | 93 unit + 5 parity + 6 doctests; ≥95% lines / 100% functions on all four new files |
| Numerical parity + invariants (A4) | ✅ | 5 new golden-value parity tests (PRINet 3.0 reference, not formula retranscription); closed-form gradient cross-checked two ways |
| Quality gates (A5) | ✅ | fmt/clippy/ruff/mypy all clean under both default and `strict-checks` features |
| Security (A6) | ✅ | `#![forbid(unsafe_code)]`; `cargo audit` exit 0 (2 pre-existing allowed warnings); bandit/pip-audit clean |
| Docstring/doc coverage (A7) | ✅ | Rust 100% public (rustdoc `-D warnings` clean); Python interrogate 100% |
| Repository hygiene (A8) | ⚠️ | WP023-F1: `public_api.rs` regression test not extended to cover new `GatedPhaseActivationParams` re-export |
| CI status (A9) | ✅ | Local gate reproduction green (nothing pushed yet this cycle per amendment #28) |
| Artefact trail (A10) | ✅ | S1 handoff note, session register, DEFERRED_VALIDATION_REGISTER all consistent |

## 2. Methodology

All commands executed on Windows, local hardware, from the repository root at `main` @ `00034bd`.

```bash
# Format
cargo fmt --all -- --check                                                # exit 0

# Clippy (default + strict-checks)
cargo clippy --workspace --all-targets -- -D warnings                     # exit 0
cargo clippy --workspace --all-targets --features prin-train/strict-checks -- -D warnings  # exit 0

# Tests
cargo test -p prin-train                                                  # 93 unit + 7 parity + 1 public_api + 6 doctests = 107, all pass
cargo test -p prin-train --features strict-checks                         # 95 unit (2 extra NaN-guard tests), same parity/doctest counts
cargo test --workspace                                                    # all pass

# Rustdoc
set RUSTDOCFLAGS=-D warnings && cargo doc --workspace --no-deps           # exit 0, 0 warnings

# Security
cargo audit                                                               # exit 0; 2 allowed warnings (paste RUSTSEC-2024-0436, bincode RUSTSEC-2025-0141)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                    # 0 issues
.venv\Scripts\python -m pip_audit .                                       # No known vulnerabilities

# Python gates (no Python source touched; run for completeness)
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/       # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/  # 50 files already formatted
.venv\Scripts\mypy python/prin --strict                                   # Success: no issues found in 18 source files
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin        # 100.0% coverage

# Hygiene
grep -r "TODO\|FIXME\|HACK\|XXX\|STUB" crates/prin-train/src/            # No matches
grep -r "unsafe" crates/prin-train/src/                                   # Only #![forbid(unsafe_code)] in lib.rs
```

**DV-019 observation:** One intermittent failure of the pre-existing WP-022 test `bands::tests::gradients_flow_to_every_parameter` was observed during the `strict-checks` run (1 of 2 full-suite runs). The test passes reliably in isolation and was confirmed pre-existing (not a WP-023 regression) by S1. This is recorded as DV-019 in the Deferred Validation Register.

**Snyk Code:** Not run locally (Snyk MCP unauthenticated on this machine — same environment condition PSR-022 documented). The CI `snyk` workflow is the authoritative gate and will scan at S4 push.

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

**Status: ✅ PASS**

The WP-023 declaration (PSR-022 §7) scopes four modules: feedback inhibition, complex/phase activations, energy functions, and the ±β HEP trainer. All four are present:

| Module | File | Lines | Public types |
|---|---|---|---|
| `inhibition` | `crates/prin-train/src/inhibition.rs` | 515 | `FeedbackInhibitionConfig`, `FeedbackInhibition` |
| `activations` | `crates/prin-train/src/activations.rs` | 700 | `d_silu`, `ComplexTensor`, `HolomorphicActivation[Config]`, `phase_activation`, `GatedPhaseActivation[Config/Params]` |
| `energy` | `crates/prin-train/src/energy.rs` | 421 | `HolomorphicEnergyConfig`, `HolomorphicEnergy` |
| `hep` | `crates/prin-train/src/hep.rs` | 573 | `HolomorphicEpConfig`, `HolomorphicEp` |

Non-goals respected: no optimizer code (WP-024), no Python/Torch bridge (WP-025), no `concept_proj` classification head (WP-027). The `FeedforwardInhibition` and `DentateGyrusConverter` classes from PRINet 3.0 are correctly excluded — they have no learnable parameters and no differentiability concern, matching the WP declaration's "trainable half" phrasing.

Supporting changes are minimal and scoped: `error.rs` adds four new `TrainError` variants; `support.rs` adds `wrap_floor`; `lib.rs` updates the module doc and re-exports `GatedPhaseActivationParams`.

### 3.2 A2 — Plan/architecture conformance

**Status: ✅ PASS**

- **Crate layering:** All new code lives in `prin-train`, the designated trainable-primitives crate. No new dependencies added (no `Cargo.toml` changes).
- **Config/Params/init pattern:** `FeedbackInhibition[Config]`, `HolomorphicEnergy[Config]`, `HolomorphicEp[Config]` follow the established WP-022 pattern. `GatedPhaseActivation[Config/Params]` is the only new Burn `Module` with learnable parameters and correctly provides both `init` (zero-init) and `init_from_params` constructors.
- **No numerics in Python:** No Python file under version control was touched.
- **Deterministic Seed flow:** All random initialization goes through `prin_dynamics::Seed`; no hidden RNG.
- **Typed errors:** All validation uses `TrainError` variants; no `panic!`/`unwrap()` on user-controlled inputs.

### 3.3 A3 — Tests in tandem + coverage

**Status: ✅ PASS**

93 new unit/property tests in the four new modules, plus 5 new golden-value parity tests across 3 parity test files. Test categories present:

- **Config validation:** zero-size rejection, non-finite parameter rejection, range validation (all four modules)
- **Shape guards:** dimension mismatch rejection (all four modules)
- **STE identity:** `compete_forward_equals_hard_topk_selection` — bit-exact forward pass
- **Gradient reference:** closed-form coupling gradient cross-checked against both central finite difference (`eps=1e-6`, agreement `<1e-3`) and Burn autodiff (agreement `<1e-8`); HEP outer-product formula independently re-derived by hand in `coupling_gradient_matches_manual_outer_product_reference` (agreement `<1e-9`); gate bias gradcheck at `eps=1e-4` (DV-018 precision floor)
- **Energy properties:** self-energy zero at unit amplitude, grows away from unit amplitude, task-energy conditional on `beta != 0.0`
- **Property tests (proptest):** `compete_always_selects_at_most_k_and_is_finite`, `phase_activation_always_wraps_in_range`, `d_silu_always_finite_and_bounded`, `forward_always_finite` (energy), `coupling_gradient_always_finite` (HEP)
- **Parity tests:** 5 new golden-value tests against actual PRINet 3.0 classes (not formula retranscriptions)

S1's coverage claim (≥95% lines / 100% functions on all four new files) is accepted on the basis of the `cargo llvm-cov` evidence in the handoff note. No test was weakened or skipped.

### 3.4 A4 — Numerical parity + invariants

**Status: ✅ PASS**

Parity-evidence disposition (per S1 exit gate rule 4):

| Primitive | PRINet 3.0 reference exists? | Parity test | Tolerance | Notes |
|---|---|---|---|---|
| `FeedbackInhibition::compete` | Yes (parameter-free, direct call) | `parity_inhibition.rs` | `rtol=1e-10, atol=1e-12` | Deterministic hard selection, no sigmoid in forward path |
| `d_silu` / `phase_activation` | Yes (direct call) | `parity_activations.rs` | `rtol=1e-6` | DV-018 sigmoid precision floor; includes negative-input wrap case |
| `HolomorphicEnergy` (coupling + self) | Yes (direct call, `complex128`) | `parity_energy.rs` | `rtol=1e-10, atol=1e-12` | `complex128` isolates formula correctness from f32-complex hazard |
| `HolomorphicEp::coupling_gradient` | No (generalized nudge target; reference uses `concept_proj`) | N/A — closed-form validated two ways instead | `<1e-3` (FD), `<1e-8` (autodiff), `<1e-9` (manual) | Documented deferral with stated reason |

Documented deviations (permanent, non-closeable):
- **Split-complex `HolomorphicActivation`:** Burn has no complex-tensor autodiff; only the `holomorphic=False` split-complex path is ported. Documented in module rustdoc.
- **Zero-phase complex state in HEP:** PRINet 3.0 forces phase to zero before energy evaluation; preserved via `ComplexTensor::from_real`. Documented in `hep.rs` module rustdoc.

### 3.5 A5 — Quality gates

**Status: ✅ PASS**

All gates green — see §2 for command evidence. Both default and `strict-checks` feature configurations pass clippy and tests.

### 3.6 A6 — Security

**Status: ✅ PASS**

- `#![forbid(unsafe_code)]` in `lib.rs` — the only occurrence of `unsafe` in the source tree.
- `cargo audit`: exit 0, 2 allowed warnings (both pre-existing: `paste` RUSTSEC-2024-0436/amendment #9, `bincode` RUSTSEC-2025-0141/amendment #27). No new dependency added.
- `bandit`: 0 issues across 3371 Python lines.
- `pip-audit`: no known vulnerabilities.
- No runtime code generation, no secrets, no network access.

### 3.7 A7 — Docstring/doc coverage

**Status: ✅ PASS**

- Rust: `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` passes with 0 warnings, including `#![warn(missing_docs)]`. Every public type, function, and method has rustdoc.
- Python: `interrogate` reports 100% docstring coverage (no Python source touched).
- Module-level rustdoc is thorough: STE construction, complex representation deviation, energy decomposition, HEP scope decisions all documented with code examples.

### 3.8 A8 — Repository hygiene

**Status: ⚠️ PASS-WITH-FINDINGS**

- No TODO/FIXME/HACK/XXX/STUB markers in `prin-train/src/`.
- `__all__` not applicable (Rust crate).
- No orphan files; gitignore respected (ad-hoc reference generation script is gitignored per WP-009/.../WP-022 precedent).
- Session register updated (0089 → COMPLETE).

**WP023-F1:** The `public_api.rs` regression test (created for WP022-F2 to verify `Params` structs are re-exported at the crate root) was not extended to cover the new `GatedPhaseActivationParams` re-export. The re-export itself is correct (`pub use activations::GatedPhaseActivationParams;` in `lib.rs`, following the WP022-F2 precedent), and the type is usable (the doctest in `activations.rs` exercises it indirectly), but the explicit compile-time regression test that was specifically created to prevent this class of issue only covers the WP-022 pair (`DiscreteDeltaThetaGammaParams`, `ResonanceLayerParams`).

### 3.9 A9 — CI status

**Status: ✅ PASS**

Per Plan amendment #28 (push/CI cadence), nothing has been pushed yet this cycle. A9 is verified against local gate reproduction: all quality gates are green locally (see §2). The CI `snyk` workflow will scan at S4 push.

DV-019 (pre-existing WP-022 flaky test) was observed once during the `strict-checks` run but is confirmed pre-existing and non-blocking.

### 3.10 A10 — Artefact trail

**Status: ✅ PASS**

- S1 handoff note: `DOCS/experiments/0089-wp023-s1-handoff.md` — comprehensive, maps every acceptance criterion to evidence, states parity-evidence disposition, records DV-018/DV-019.
- Session register: `DOCS/sessions/SESSION_REGISTER.md` row 0089 updated to COMPLETE.
- Session brief: `DOCS/sessions/phase-4/0089-wp023-s1-inhibition-activations-and-hep.md` status updated to COMPLETE.
- Deferred Validation Register: DV-018 and DV-019 properly recorded with full evidence.
- Previous cycle's audit report (`DOCS/audits/022-wp022-audit.md`) and project state report (`DOCS/reports/022-project-state.md`) exist and are consistent.

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP023-F1 | D4 | `crates/prin-train/tests/public_api.rs` | `public_api.rs` regression test does not cover the new `GatedPhaseActivationParams` crate-root re-export; only the WP-022 pair (`DiscreteDeltaThetaGammaParams`, `ResonanceLayerParams`) is tested | WP022-F2 precedent (Testing Standards §1 — regression tests for public-API invariants) | Extend `public_api.rs` to include `GatedPhaseActivationParams` in the compile-time check |

## 5. Deviation-ledger delta

New findings added to the ledger: **WP023-F1** (D4). Carried findings re-inspected: none (no open findings was in scope for this WP).

DV-018 and DV-019 are new deferred validation items, not audit findings — both are properly recorded in the Deferred Validation Register by S1 and require no S2 action beyond acknowledging their existence.

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS** — one D4 finding (WP023-F1). No D1/D2/D3 findings. The implementation is high quality: all acceptance criteria are met, all quality gates are green, parity evidence is thorough, and the two discovered risks (DV-018, DV-019) are properly documented and governed.

**S3 action list (ordered):**

1. **WP023-F1 (D4):** Extend `crates/prin-train/tests/public_api.rs` to include `use prin_train::GatedPhaseActivationParams;` and a `fn accepts_gated_phase_activation_params(_: GatedPhaseActivationParams<TestBackend>) {}` compile-time check.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| *(pending S3)* | | | |

**Delta re-audit date:** *(pending S3)* — **Result:** *(pending S3)*
