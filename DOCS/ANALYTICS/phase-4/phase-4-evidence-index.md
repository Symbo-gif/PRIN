# Phase 4 Evidence Index

**Phase:** 4 — Trainable stack and Torch bridge
**Date:** 2026-08-21
**Companion to:** [`phase-4-analytics-report.md`](phase-4-analytics-report.md)

This index lists every evidence artefact cited in the Phase 4 Analytics
Report, with file path, purpose, and the dimension(s) it supports.

---

## 1. Governance documents

| Path | Purpose | Dimensions |
|---|---|---|
| `DOCS/PRIN_Project_Plan.md` | Official project plan; Phase 4 scope (§6, no completion marker — PA4-F1), amendment log §8.3 (ends at #29) | P2, P6, P8, P9 |
| `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §3, §7 | Session Cycle methodology; hotfix exception (used for WP022-F3) | P4, P6 |
| `DOCS/standards/Coding_Standards.md` §2.1/§6.1 | `unsafe`/kernel-FFI and Python-FFI policy | P4, P7 |
| `DOCS/standards/Coding_Standards.md` §6.2 | Security scanning mandate; advisory threat-assessment requirement (amendment #27) | P5, P7 |
| `DOCS/standards/Testing_Standards.md` §2/§3 | Parity/gradcheck test-layer requirements, tolerances | P1, P3 |
| `DOCS/standards/Documentation_Standards.md` §7 items 8–9 | S4 documentation-accuracy sweep; phase-closing cross-cutting document currency (R22's fix) | P2, P6 |
| `DOCS/ANALYTICS/phase-3/phase-3-recommendations.md` | Phase 3 recommendations R21–R25, tracked to closure in §9.1 | P1, P2, P5, P6, P9 |
| `DOCS/ANALYTICS/phase-3/phase-3-recommendation-implementation-governance.md` | Confirms R21–R25 disposition before WP-022 S1 | P6, P9 |

## 2. Audit reports (Phase 4)

| Path | Verdict | Findings | Dimensions |
|---|---|---|---|
| `DOCS/audits/022-wp022-audit.md` | PASS-WITH-FINDINGS → CLEAN | 2 (2 D4) + post-close D1 hotfix (WP022-F3) | P4, P7 |
| `DOCS/audits/023-wp023-audit.md` | PASS-WITH-FINDINGS → CLEAN | 1 (D4) | P4 |
| `DOCS/audits/024-wp024-audit.md` | PASS-WITH-FINDINGS → CLEAN | 1 (D3, declaration-text drift) | P6 |
| `DOCS/audits/025-wp025-audit.md` | PASS-WITH-FINDINGS → CLEAN | 4 (1 D2, 1 D3, 2 D4) | P1, P4, P8 |
| `DOCS/audits/026-wp026-audit.md` | PASS-WITH-FINDINGS → CLEAN | 2 (2 D4) | P1, P4 |
| `DOCS/audits/027-wp027-audit.md` | **PASS** (zero findings) | 0 | P1, P3, P8 |
| `DOCS/audits/EXECUTIVE_AUDIT_REPORT_005.md` | PASS-WITH-REMEDIATION | 5 (1 D2, 2 D3, 2 D4) | P2, P3, P4, P5, P6, P7 |
| `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_003.md` | PASS-WITH-REMEDIATION | 1 new (M-F8, D3) | P1, P5 |
| `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_004.md` | PASS-WITH-REMEDIATION | 0 new; M-F8/M-F5/M-F6 closed | P1, P5, P9 |

## 3. Audit reports (Phase 3, retained for trend comparison)

| Path | Verdict | Findings | Dimensions |
|---|---|---|---|
| `DOCS/audits/017-wp017-audit.md` – `DOCS/audits/021-wp021-audit.md` | Various (1 FAIL) | 8 total (1 D1) | §11 comparison |
| `DOCS/audits/EXECUTIVE_AUDIT_REPORT_004.md`, `EXECUTIVE_MATH_AUDIT_REPORT_002.md` | PASS-WITH-REMEDIATION | 2 total | §11 comparison |

## 4. Project state reports (Phase 4)

| Path | Cycle | Key content | Dimensions |
|---|---|---|---|
| `DOCS/reports/022-project-state.md` | 022 | WP-022 closure; `bincode` advisory governed (amendment #27); GPU CI runner strategy decided (amendment #26) | P4, P7, P9 |
| `DOCS/reports/023-project-state.md` | 023 | WP-023 closure; DV-018/DV-019 first recorded; **WP-024 declaration text naming error later corrected by amendment #29** | P1, P6 |
| `DOCS/reports/024-project-state.md` | 024 | WP-024 closure; amendment #29 recorded | P6 |
| `DOCS/reports/025-project-state.md` | 025 | WP-025 closure; DV-021 opened; DV-002 closed (self-hosted runner registered) | P1, P5, P8, P9 |
| `DOCS/reports/026-project-state.md` | 026 | WP-026 closure; WP026-F1/F2 both FIXED, one revealing a real missing-`ReLU` bug | P1, P4 |
| `DOCS/reports/027-project-state.md` | 027 | WP-027 closure; **Phase 4 exit-gate verdict GREEN §6**; PhaseTracker/gradcheck/bridge-overhead evidence; §8 cross-cutting-document-currency review (Project Plan marker flagged, not fixed) | P1, P2, P3, P6, P8, P9 |
| `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` | — | 15 active + 8 closed items (DV-001–DV-023); read in full this session | P9 |

## 5. Session briefs and register (Phase 4)

| Path | Scope | Dimensions |
|---|---|---|
| `DOCS/sessions/phase-4/README.md` | Phase 4 session status table — all 24 (0085–0108) COMPLETE | P6 |
| `DOCS/sessions/phase-4/0085-0108-*.md` | 24 individual session briefs | P6 |
| `DOCS/sessions/SESSION_REGISTER.md` | Master register — sessions 0085–0108 plus Global Sessions section (EMA-003, EMA-004, EA-005) | P6 |
| `DOCS/experiments/0085-wp022-s1-handoff.md` | WP-022 S1 handoff | P1, P4 |
| `DOCS/experiments/0093-wp024-s1-handoff.md` | WP-024 S1 handoff (records DV-020 naming discrepancy) | P6 |
| `DOCS/experiments/0097-wp025-s1-handoff.md` | WP-025 S1 handoff (bridge overhead pilot measurement, later found noise-masked) | P1, P8 |
| `DOCS/experiments/0101-wp026-s1-handoff.md`, `0101-exec-wp026-s1-handoff.md` | WP-026 S1 handoffs (scope-deferral documentation, then the executive secondary session's delivery) | P1, P4 |
| `DOCS/experiments/0105-wp027-s1-handoff.md`, `0105-wp027-temporal-clevr-n-validation.json` | WP-027 S1 handoff and the PhaseTracker acceptance-criterion evidence artefact | P1, P8 |

## 6. Evidence files — math-audit chain (EMA-003, EMA-004)

| Path | Content | Dimensions |
|---|---|---|
| `EVIDENCE/math-audit/ema-run-summary.json` | Consolidated 40-claim run summary (8 ledgers); dated 2026-08-20, matching current `HEAD` | P5, P9 |
| `EVIDENCE/math-audit/audits/bundle-e70492cb332c/` | `prin-train-trainable-stack-properties.json` bundle, final PASS state (all 10 claims), generated 2026-08-20T04:30:51Z | P1, P5 |
| `EVIDENCE/math-audit/audits/bundle-184ec90b735d/` | Earlier run of the same ledger showing the pre-fix FAIL state (`SCALR-LR-02` INCONCLUSIVE), generated 2026-08-20T02:40:30Z — superseded ~1h50m later | P5 |
| `tools/math_audit_claims/prin-train-trainable-stack-properties.json` | New claim ledger (10 claims, EMA-003), committed and versioned | P1, P5 |
| `tools/math_audit_claims/prin-tensor-hosvd-reconstruction.json` | New claim ledger (`TCK-01`, EMA-004) — first EMA coverage of `prin-tensor` | P1, P5 |
| `tools/math_audit_claims/prin-dynamics-graph-topology.json` | Gained `GRA-01-SAT` (EMA-004, PySAT corroboration) | P5 |
| `tools/math_audit_policy.yaml` | EMA policy (`prin-ema`); `enable_pysat: true` added at EMA-004 | P5, P6 |
| `crates/prin-tensor/tests/data/prinet_reference_hosvd.json` | Existing PRINet-3.0 HOSVD reference fixture, reused by `TCK-01` | P1, P5 |

## 7. Rust crates (Phase 4 new code)

### `prin-train` (new crate)

| Path | Lines | Purpose | Dimensions |
|---|---|---|---|
| `crates/prin-train/src/lib.rs` | 131 | Crate root; `#![forbid(unsafe_code)]` (line 97) | P4, P7 |
| `crates/prin-train/src/bands.rs` | 977 | `DiscreteDeltaThetaGamma` (WP-022) | P1, P4 |
| `crates/prin-train/src/layers.rs` | 888 | `ResonanceLayer` (WP-022) | P1, P4 |
| `crates/prin-train/src/inhibition.rs` | 515 | `FeedbackInhibition` STE top-k WTA (WP-023) | P1, P4 |
| `crates/prin-train/src/activations.rs` | 757 | `d_silu`, `HolomorphicActivation`, `GatedPhaseActivation` (WP-023); DV-018 (`sigmoid` f32 precision floor) discovered here | P1, P4 |
| `crates/prin-train/src/energy.rs` | 421 | `HolomorphicEnergy` (WP-023) | P1, P4 |
| `crates/prin-train/src/hep.rs` | 573 | `HolomorphicEp` ±β Equilibrium Propagation (WP-023) | P1, P4 |
| `crates/prin-train/src/feedback.rs` | 230 | `OrderParameter`/`StepFeedback`/`OscillatorOptimizer` trait (WP-024) | P4 |
| `crates/prin-train/src/sync_gd.rs` | 600 | `SyncGd` (WP-024) | P1, P4 |
| `crates/prin-train/src/rip.rs` | 490 | `Rip` (WP-024) | P1, P4 |
| `crates/prin-train/src/scalr.rs` | 855 | `Scalr` (WP-024) | P1, P4 |
| `crates/prin-train/src/attention.rs` | 619 | `OscillatoryAttention` (WP-026) | P1, P4 |
| `crates/prin-train/src/phase_tracker.rs` | 788 | `PhaseTracker`, `TrackingResult` (WP-026) — `TrackingResult` re-export is the source of PA4-F2's duplicate-object Sphinx warnings | P1, P2, P4 |
| `crates/prin-train/src/hybrid.rs` | 880 | `HybridPRINetV2` (WP-026) — WP026-F2's parity test revealed a missing `ReLU`, fixed same commit | P1, P4 |
| `crates/prin-train/src/slot_attention.rs` | 948 | `SlotAttentionModule`/`TemporalSlotAttentionMOT` (WP-026) | P1, P4 |
| `crates/prin-train/src/ablation.rs` | 835 | 4 ablation variants (WP-026) | P1, P4 |
| `crates/prin-train/src/allocation.rs` | 969 | `AdaptiveOscillatorAllocator`/`DynamicPhaseTracker` (WP-026) — WP026-F1's strategy-mismatch fix | P1, P4, P7 |
| `crates/prin-train/src/dataset.rs` | 751 | Temporal CLEVR-N generator (WP-027) | P1 |
| `crates/prin-train/src/losses.rs` | 215 | `hungarian_similarity_loss`, `temporal_smoothness_loss` (WP-027) | P1 |
| `crates/prin-train/src/trainer.rs` | 549 | `train_phase_tracker` Rust-native trainer (WP-027) | P1, P8 |
| `crates/prin-train/src/support.rs` | 398 | Shared tensor/numerical-guard helpers | P4 |
| `crates/prin-train/src/error.rs` | 201 | `TrainError` typed errors | P4, P7 |

**Total: 13,590 lines, 0 `unsafe` blocks, hard `#![forbid(unsafe_code)]`.**

### `prin-py` (extended)

| Path | Lines | Purpose | Dimensions |
|---|---|---|---|
| `crates/prin-py/src/bindings/train.rs` | 508 | `PyResonanceLayerBridge`/`PyGatedPhaseActivationBridge` (WP-025); WP025-F1 checkpoint-shape-validation fix; `tensor2_from_dlpack_with_data` (DV-021 optimization) | P1, P4, P7 |
| `crates/prin-py/src/bindings/{attention,phase_tracker,hybrid,slot_attention,ablation,allocation}.rs` | — | Six new WP-026 binding modules | P1, P4 |
| `crates/prin-py/src/bindings/train_support.rs` | — | Shared rank-generic DLPack helper (WP-026, absorbing a WP-025 refactor) | P4 |
| `crates/prin-py/src/bindings/{optim,trainer}.rs` | — | `SyncGdBridge`/`ScalrBridge`/`RipBridge`, `train_phase_tracker` entry (WP-027) | P1, P4 |
| `crates/prin-py/src/dlpack.rs` | — | `read_dlpack_f64`/`export_dlpack_f64` additive helpers (WP-025); pre-existing governed `unsafe` exception, unchanged | P4, P7 |
| `crates/prin-py/src/lib.rs` | — | `#![deny(unsafe_code)]` + `#![deny(unsafe_op_in_unsafe_fn)]`, unchanged | P4, P7 |

### Python (`python/prin/nn/`, new package)

| Path | Lines | Purpose | Dimensions |
|---|---|---|---|
| `python/prin/nn/__init__.py` | 344 | `ResonanceLayer`/`GatedPhaseActivation` original bridge pattern (WP-025) | P1, P4 |
| `python/prin/nn/_bridge.py` | 123 | Shared `apply_rust_bridge` generic `torch.autograd.Function` glue | P4 |
| `python/prin/nn/{attention,phase_tracker,hybrid,slot_attention,ablation,allocation}.py` | 112–373 each | WP-026 wrapper modules | P1, P4 |
| `python/prin/nn/optimizers.py` | 383 | `SyncGd`/`Scalr`/`Rip` `torch.optim.Optimizer` subclasses (WP-027) | P1, P4 |
| `python/prin/train.py` | 175 | Rust-native training pipeline orchestration (WP-027) | P4 |

**`prin.nn` total: 2,202 lines across 9 files.**

## 8. Test artefacts (Phase 4)

| Path | Content | Dimensions |
|---|---|---|
| `crates/prin-train/tests/parity_{bands,layers,inhibition,activations,energy,optimizers,attention,phase_tracker,hybrid}.rs` | 15 golden-value parity tests vs. PRINet 3.0, first-ever for `prin-train` | P1, P3 |
| `crates/prin-train/tests/public_api.rs` | Compile-time crate-root re-export regression tests (WP022-F2/WP023-F1) | P4 |
| `crates/prin-train/tests/integration_temporal_clevr_n.rs` | `#[ignore]`d acceptance run — PhaseTracker IP threshold (WP-027) | P1, P8 |
| `crates/prin-train/tests/integration_checkpoint_resume.rs` | Trained-state serialization round-trip (WP-027) | P1 |
| `crates/prin-train/benches/{resonance_layer_bridge,phase_tracker_bridge}.rs` | Criterion baselines feeding DV-021's bridge-overhead comparison | P1, P8 |
| `tests/test_train_bridge*.py` (9 files) | Python-side gradcheck/bridge tests, incl. WP-027's composed "full gradcheck" | P1, P3, P8 |
| `tests/test_train_pipeline.py` | WP-027 pipeline-level tests | P1 |

## 9. Security artefacts

| Path | Content | Dimensions |
|---|---|---|
| `Cargo.lock` | `h2` 0.4.15→0.4.16 (commit `1b7a8e9`, closing WP022-F3/RUSTSEC-2026-0258) | P4, P7 |
| `DOCS/PRIN_Project_Plan.md` §8.3 amendment #27 | `bincode` RUSTSEC-2025-0141 threat assessment and acceptance | P7 |
| `tools/wp001_baseline.py` | Version-consistency check | P5 |
| `tools/check_deviation_ledger.py` | Ledger consistency check (CI-enforced since Phase 3) | P5, P6 |

## 10. CI workflows

| Path | Purpose | Phase 4 changes | Dimensions |
|---|---|---|---|
| `.github/workflows/rust.yml` | Rust quality | `audit` job caught WP022-F3 same-day; `test (windows-latest)` migrated to self-hosted `PRIN-GPU-Runner` (EA-005 follow-up, closing DV-016/DV-023) | P3, P5, P7 |
| `.github/workflows/python.yml` | Python quality | `lint` job gained `torch` in its pip install (E-F1 fix, EA-005); `test` jobs install torch/torchvision for gradcheck coverage; `windows-latest` legs migrated to self-hosted runner | P3, P5 |
| `.github/workflows/parity.yml` | Parity suite | Retains `ubuntu-latest` with documented WSL2 fallback comment for DV-022 | P1, P9 |
| `.github/workflows/gpu.yml` | GPU CI (opt-in) | Unchanged structurally this phase; `[self-hosted, gpu]` runner now registered (closing DV-002 at WP-025 S4) | P1, P9 |
| `.github/workflows/release.yml` | Release | `windows-latest` legs migrated to self-hosted runner | P9 |

## 11. Independent re-verification (this session, 2026-08-21)

| Command | Result | Dimensions |
|---|---|---|
| `cargo fmt --all -- --check` | Clean | P4 |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean | P4 |
| `cargo test --workspace -- --test-threads=1` | Exit 0, all crates pass | P1, P3, P4 |
| `cargo audit` | 2 allowed advisories, 0 new | P7 |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | Clean, 0 warnings | P2 |
| `ruff check` / `mypy python/prin --strict` | Clean / 27 files, 0 issues | P4 |
| `bandit -r python/prin -c pyproject.toml` | 0 issues | P7 |
| `interrogate -c pyproject.toml python/prin` | 100.0% (231/231) | P2 |
| `pytest tests/ -m "not slow and not gpu"` | 441 passed, 8 deselected | P3 |
| `pytest tests/ parity/` | 959 passed | P1, P3 |
| `pip-audit .` / `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities (both) | P7 |
| `snyk code test --severity-threshold=medium` | 0 issues | P5, P7 |
| `sphinx-build -W --keep-going -b html` against reused `_build/html` | Falsely reports 0 warnings | P2, P5, PA4-F2 |
| `sphinx-build -W --keep-going -b html` against 2 independent fresh output dirs | **12 warnings-as-errors, both times** | P2, P5, PA4-F2 |
| `grep -rn "unsafe" crates/prin-train/src/` | 1 hit (`#![forbid(unsafe_code)]` itself) | P4, P7 |
| `grep -rn "unsafe" crates/prin-py/src/bindings/{train,optim,trainer}.rs` | 0 code hits (doc-comment mentions only) | P4, P7 |

## 12. This session's own findings

| ID | Severity | Location | Dimensions |
|---|---|---|---|
| PA4-F1 | D3 | `DOCS/PRIN_Project_Plan.md` §6 (Phase 4 roadmap-table completion marker missing — third consecutive phase, this time after the R22 safeguard correctly flagged it) | P2, P6 |
| PA4-F2 | D2 | `DOCS/sphinx/_build/html` (stale incremental-build cache silently masking 12 genuine `-W` warnings-as-errors, false "0 warnings" claim repeated across PSR-022 through PSR-027 and EA-005) | P2, P5 |

## 13. Git history

| Range | Commits | Content |
|---|---|---|
| `8d7a6b7..8bce1a2` | 1 | Phase 3 recommendation implementation close → WP-022 S1 |
| `8bce1a2..48eade3` | ~43 | WP-022 through WP-027 S1–S3 |
| `48eade3..cb2d83c` | 1 | EMA-003 |
| `cb2d83c..29d5e06` | 2 | EMA-004 (tool remediation + sign-off record) |
| `29d5e06..2b32e49` | 1 | EA-005 |
| `2b32e49..85b3c79` | 1 | EA-005 follow-up: self-hosted Windows CI runner migration |
| `85b3c79..2552b86` | 1 | WP-027 S4 (documentation closure, PSR-027, Phase 4 exit gate GREEN) |
| `2552b86..b93bbaa` | 1 | README accuracy sweep (current `HEAD`) |
