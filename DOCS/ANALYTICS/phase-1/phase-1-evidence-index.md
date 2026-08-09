# Phase 1 Evidence Index

**Phase:** 1 — Dynamics core
**Date:** 2026-08-09
**Companion to:** [`phase-1-analytics-report.md`](phase-1-analytics-report.md)

This index lists every evidence artefact cited in the Phase 1 Analytics
Report, with file path, purpose, and the dimension(s) it supports.

---

## 1. Governance documents

| Path | Purpose | Dimensions |
|---|---|---|
| `DOCS/PRIN_Project_Plan.md` | Official project plan; Phase 1 scope, exit criteria, amendment log (§8.3) | P6, P8, P9 |
| `DOCS/standards/Development_Workflow_and_Audit_Standards.md` | Session Cycle methodology, audit checklist, deviation classification | P6 |
| `DOCS/standards/Coding_Standards.md` | Rust + Python coding standards, security standards (§6) | P4, P7 |
| `DOCS/standards/Testing_Standards.md` | Testing layers, tolerances, coverage gates | P3 |
| `DOCS/standards/Documentation_Standards.md` | Documentation thresholds, S4 checklist | P2 |
| `DOCS/standards/Benchmarking_and_Reproducibility_Standards.md` | Reproducibility and benchmarking requirements | P1 |
| `DOCS/standards/Experimentation_Standards.md` | Pre-registration, campaign rules, scientific integrity | P6 |
| `DOCS/standards/Versioning_and_Release_Standards.md` | Versioning, CI/CD gates, release procedure | P5, P8 |
| `DOCS/standards/Executive_Audit_Governance_and_Methodology.md` | Executive audit criteria E1–E10, deviation severities, remediation | P6 |

## 2. Audit reports (Phase 1)

| Path | Verdict | Findings | Dimensions |
|---|---|---|---|
| `DOCS/audits/006-wp006-audit.md` | PASS-WITH-FINDINGS → clean | 3 (1 D2, 1 D3, 1 D4) | P3, P4, P5, P9 |
| `DOCS/audits/007-wp007-audit.md` | PASS-WITH-FINDINGS → clean | 5 (2 D2, 1 D3, 2 D4) | P1, P3, P4, P7 |
| `DOCS/audits/008-wp008-audit.md` | PASS-WITH-FINDINGS → clean | 5 (1 D2, 1 D3, 3 D4) | P2, P3, P4 |
| `DOCS/audits/009-wp009-audit.md` | PASS-WITH-FINDINGS → clean | 7 (2 D2, 2 D3, 3 D4) | P3, P4, P5 |
| `DOCS/audits/010-wp010-audit.md` | PASS (zero findings) | 0 | P1, P3, P4, P5, P7 |
| `DOCS/audits/011-wp011-audit.md` | PASS (1 D4 FIXED in S3) | 1 (1 D4) | P3, P4, P5, P7 |
| `DOCS/audits/EXECUTIVE_AUDIT_REPORT_001.md` | PASS-WITH-REMEDIATION | 5 (E-F1–E-F5) | P5, P6, P7 |
| `DOCS/audits/EXECUTIVE_AUDIT_REPORT_002.md` | PASS-WITH-REMEDIATION | 13 (E-F1–E-F13) | P2, P5, P6, P7 |

## 3. Audit reports (Phase 0, retained)

| Path | Verdict | Findings | Dimensions |
|---|---|---|---|
| `DOCS/audits/001-wp001-audit.md` | FAIL → PASS (S3) | 11 | P5, P6, P7 |
| `DOCS/audits/002-wp002-audit.md` | PASS-WITH-FINDINGS → clean | 4 | P1, P5, P6 |
| `DOCS/audits/003-wp003-audit.md` | PASS-WITH-FINDINGS → clean | 5 | P4, P5, P7 |
| `DOCS/audits/004-wp004-audit.md` | PASS-WITH-FINDINGS → clean | 9 | P3, P4, P5, P7 |
| `DOCS/audits/005-wp005-audit.md` | PASS-WITH-FINDINGS → clean | 4 | P5, P8 |

## 4. Project state reports (Phase 1)

| Path | Cycle | Key content | Dimensions |
|---|---|---|---|
| `DOCS/reports/006-project-state.md` | 006 | WP-006 closure, WP-007 declaration | P6 |
| `DOCS/reports/007-project-state.md` | 007 | WP-007 closure, WP-008 declaration | P6 |
| `DOCS/reports/008-project-state.md` | 008 | WP-008 closure, WP-009 declaration | P6 |
| `DOCS/reports/009-project-state.md` | 009 | WP-009 closure, WP-010 declaration | P6 |
| `DOCS/reports/010-project-state.md` | 010 | WP-010 closure, WP-011 declaration | P6 |
| `DOCS/reports/011-project-state.md` | 011 | WP-011 closure, Phase 1 exit gate GREEN | P6, P8, P9 |

## 5. Session briefs (Phase 1)

| Path | Scope | Dimensions |
|---|---|---|
| `DOCS/sessions/phase-1/README.md` | Phase 1 session status table (all 24 COMPLETE) | P6 |
| `DOCS/sessions/phase-1/0021-0044-*.md` | 24 individual session briefs | P6 |
| `DOCS/sessions/phase-1/wp009-s1-handoff-note.md` | WP-009 S1 handoff | P5, P6 |
| `DOCS/sessions/SESSION_REGISTER.md` | Master register (sessions 0021–0044 Phase 1) | P6 |
| `DOCS/sessions/TRACEABILITY.md` | Requirement/risk/DoD traceability matrix | P6 |

## 6. Evidence files

| Path | Content | Dimensions |
|---|---|---|
| `EVIDENCE/0005-wp002-s1-handoff.md` | WP-002 S1 handoff (retained from Phase 0) | P1, P5 |
| `EVIDENCE/0017-wp005-s1-ort-probe.json` | ORT probe (retained; timestamp fix E-F1) | P1, P8 |
| `EVIDENCE/0017-wp005-s1-phase0-gate.json` | Phase 0 gate: ready=true, cases_match=true | P1, P8 |

## 7. Experiment handoffs (Phase 1)

| Path | Content | Dimensions |
|---|---|---|
| `DOCS/experiments/0021-wp006-s1-handoff.md` | WP-006 S1 handoff | P4, P5 |
| `DOCS/experiments/0025-wp007-s1-handoff.md` | WP-007 S1 handoff | P4, P5 |
| `DOCS/experiments/0029-wp008-s1-handoff.md` | WP-008 S1 handoff | P4, P5 |
| `DOCS/experiments/0033-wp009-s1-handoff.md` | WP-009 S1 handoff | P4, P5 |
| `DOCS/experiments/0037-wp010-s1-handoff.md` | WP-010 S1 handoff | P4, P5 |

## 8. Parity corpus (retained from Phase 0)

| Path | Content | Dimensions |
|---|---|---|
| `parity/corpus/manifest.json` | 504-case manifest with SHA-256 digests | P1 |
| `parity/corpus/cases/*.npz` | 504 golden-trajectory case files | P1 |
| `parity/test_parity_differential.py` | 6 differential tests | P1, P3 |

## 9. Python package (Phase 1 additions)

| Path | Lines | Purpose | Dimensions |
|---|---|---|---|
| `python/prin/dynamics.py` | 70 | Re-export 20 dynamics symbols | P4 |
| `python/prin/metrics.py` | 68 | Re-export 22 metrics symbols | P4 |
| `python/prin/_prin_core.pyi` | ~200 | Type stubs for Rust bindings | P2, P4 |
| `python/prin/__init__.py` | 35 | Package root (updated) | P4 |

## 10. Rust crates (Phase 1 new code)

### prin-dynamics (`crates/prin-dynamics/src/`)

| Path | Lines | Purpose | Dimensions |
|---|---|---|---|
| `state.rs` | ~800 | OscillatorState, guards, k-NN index | P4, P7 |
| `seed.rs` | ~300 | Counter-based deterministic Seed (Pcg64) | P4, P7 |
| `models.rs` | ~1,200 | Dynamics trait, Kuramoto/StuartLandau/Hopf | P1, P4 |
| `coupling.rs` | ~600 | CouplingMode, Topology, matrix builders | P4 |
| `integrate.rs` | ~800 | Integrator trait, Euler/RK4/RK45 | P1, P4 |
| `pac.rs` | ~500 | PhaseAmplitudeCoupling | P1, P4 |
| `bands.rs` | ~200 | Frequency band utilities | P4 |
| `temporal.rs` | ~200 | Temporal propagation stubs | P4 |
| `lib.rs` | ~100 | Crate root, module declarations | P4 |

### prin-metrics (`crates/prin-metrics/src/`)

| Path | Lines | Purpose | Dimensions |
|---|---|---|---|
| `order.rs` | ~300 | Kuramoto order parameter, inter-frame correlation | P1, P4 |
| `coherence.rs` | ~300 | Mean phase coherence, sparse coherence | P1, P4 |
| `spectral.rs` | ~300 | PSD, concept probabilities (rustfft) | P1, P4 |
| `energy.rs` | ~250 | Synchronization energy, sparse energy | P1, P4 |
| `chimera.rs` | ~500 | Local order, bimodality, SI, chimera index | P1, P4 |
| `metastability.rs` | ~100 | Temporal std of order parameter | P4 |
| `knn.rs` | ~150 | Measurement k-NN wrapper (delegates to dynamics) | P4 |
| `error.rs` | ~200 | MetricError enum, validation helpers | P4, P7 |
| `lib.rs` | ~100 | Crate root, re-exports | P4 |

### prin-py bindings (`crates/prin-py/src/bindings/`)

| Path | Lines | Purpose | Dimensions |
|---|---|---|---|
| `state.rs` | ~300 | PyOscillatorState, PySeed, constants | P4 |
| `models.rs` | ~200 | PyKuramoto, PyStuartLandau, PyHopf | P4 |
| `integrators.rs` | ~250 | PyEuler, PyRK4, PyRK45, PyAdaptiveResult | P4 |
| `coupling.rs` | ~200 | PyCouplingMode, PyTopology, PyPAC | P4 |
| `metrics.rs` | ~250 | 22 #[pyfunction] metrics wrappers | P4 |

## 11. Rust integration tests (Phase 1)

| Path | Tests | Purpose | Dimensions |
|---|---|---|---|
| `crates/prin-dynamics/tests/parity_models.rs` | 9 | Model × coupling parity vs PRINet 3.0 | P1, P3 |
| `crates/prin-dynamics/tests/parity_integrators.rs` | 16 | Integrator trajectory parity vs PRINet 3.0 | P1, P3 |
| `crates/prin-dynamics/tests/parity_pac.rs` | 9 | PAC modulation parity vs PRINet 3.0 | P1, P3 |
| `crates/prin-metrics/tests/parity_metrics.rs` | 12 | Metric parity vs PRINet 3.0 | P1, P3 |
| `crates/prin-metrics/tests/parity_chimera.rs` | 6 | Chimera metric parity vs PRINet 3.0 | P1, P3 |
| `crates/prin-metrics/tests/corpus_metrics.rs` | 4 | Metric validation against 504-case corpus | P1, P3 |

## 12. Python tests (Phase 1 additions)

| Path | Tests | Purpose | Dimensions |
|---|---|---|---|
| `tests/test_dynamics_bindings.py` | 69 | PyO3 bindings acceptance (13 classes) | P3, P4 |

## 13. CI workflows

| Path | Purpose | Phase 1 changes | Dimensions |
|---|---|---|---|
| `.github/workflows/rust.yml` | Rust quality (3 OS) | Added `strict-checks` feature job | P5 |
| `.github/workflows/python.yml` | Python quality (2 OS × 3 Py) | Fixed hypothesis lint, `/fake` path | P5 |
| `.github/workflows/parity.yml` | Differential testing | Fixed venv creation | P1, P5 |
| `.github/workflows/gpu.yml` | GPU tests (opt-in) | Unchanged | P5 |
| `.github/workflows/release.yml` | Wheel matrix + publish | Unchanged | P5, P8 |
| `.github/workflows/repro.yml` | Reproducibility | Unchanged | P5 |
| `.github/workflows/snyk.yml` | Snyk Code + Open Source | Unchanged | P5, P7 |

## 14. Config files

| Path | Key content | Phase 1 changes | Dimensions |
|---|---|---|---|
| `Cargo.toml` | 8 workspace members | Added `rustfft` workspace dep | P4 |
| `crates/prin-dynamics/Cargo.toml` | Dynamics crate | `strict-checks` feature, `rand_pcg` | P4 |
| `crates/prin-metrics/Cargo.toml` | Metrics crate | `rustfft`, `serde_json` dev-dep | P4 |
| `crates/prin-py/Cargo.toml` | PyO3 crate | Added `numpy = "0.29.0"` | P4 |
| `pyproject.toml` | maturin, ruff, mypy, etc. | Unchanged | P4, P3 |

## 15. Plan amendments (Phase 1)

| # | Subject | Dimensions |
|---|---|---|
| #14 | f32-complex numerical hazard; `1e-6` parity tolerance | P1, P4, P9 |
| #15 | Executive audits as global sessions | P6 |
| #16 | METRIC rtol `1e-10` → `1e-8` for corpus regeneration | P1, P3 |

## 16. Independent re-verification (this session)

| Command | Result | Dimensions |
|---|---|---|
| `ruff check python/ tests/ benchmarks/ tools/ parity/` | All checks passed! | P4 |
| `ruff format --check` | 47 files already formatted | P4 |
| `mypy python/prin --strict` | Success: no issues in 18 files | P4 |
| `interrogate -c pyproject.toml python/prin` | 100.0% (106/106) | P2 |
| `bandit -r . -c pyproject.toml` | 0 issues (2,900 lines) | P7 |
| `pytest tests/ -m "not slow and not gpu" --cov=prin` | 241 passed, 99% | P3 |
| `pytest parity/` | 6 passed | P1, P3 |
| `cargo fmt --all -- --check` | Clean | P4 |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean | P4 |
| `cargo test --workspace` | 351 passed | P3, P4 |
| `cargo test -p prin-dynamics` | 203 passed | P3, P4 |
| `cargo test -p prin-metrics` | 145 passed | P3, P4 |
| `cargo test -p prin-kernels --features wgpu,cpu` | 21 passed | P3, P4 |
| `cargo audit` | 1 allowed `paste` advisory | P7 |
| `pip-audit .` | No known vulnerabilities | P7 |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | 0 warnings | P2 |
| `sphinx-build -W --keep-going -b html` | Build succeeded | P2 |

## 17. Git history

| Range | Commits | Content |
|---|---|---|
| `d7fb8c8..5db3a1c` | 53 | Full Phase 1 (WP-006 through WP-011, plus EA-001/EA-002) |
