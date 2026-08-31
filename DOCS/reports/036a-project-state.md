---

# PRIN Project State Report — Cycle 036A

**Date:** 2026-08-31
**Cycle:** 036A (WP-036A "Trainable compatibility layers — `prin-train` extension")
**Completed sessions:** 0144A + 0144A1–0144A4 (S1), 0144B (S2), 0144C (S3), 0144D (S4)
**Author:** Qwen Code (AI pair)
**Git state:** `main` @ S4 closure

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1 (**5 of 7**
  phase-6 WPs complete: WP-033, WP-034, WP-035, WP-036, WP-036A).
- **This cycle delivered:**
  - **13 D-D-appendix trainable-layer symbols** (rows 31–42, 44) delivered as
    real `prin-train` Burn implementations, replacing the D-2.2 stubs shipped
    by WP-036 S1:
    - **0144A1** (inhibition & sparsification): `FeedforwardInhibition`,
      `DentateGyrusConverter`, `DGLayer`, `oscillatory_weight_init`,
      `SparsityRegularizationLoss` — new `prin-train::inhibition_layers` +
      `weight_init` + `losses` extension.
    - **0144A2** (phase-to-rate & autoencoder): `PhaseToRateConverter`,
      `PhaseToRateAutoencoder`, `DenseAutoencoder` — new
      `prin-train::autoencoders`.
    - **0144A3** (hierarchical / PAC / discrete):
      `HierarchicalResonanceLayer`, `PhaseAmplitudeCouplingLayer`,
      `DiscreteDeltaThetaGammaLayer` — new `prin-train::hierarchical_layers`.
    - **0144A4** (model container + consolidation): `PRINetModel` — new
      `prin-train::model`; `compile_model` — pure-Python `torch.compile`
      passthrough (D-2 disposition).
  - **12 new PyO3/DLPack bridges** in `crates/prin-py/src/bindings/`
    (`train_inhibition_layers.rs`, `train_autoencoders.rs`,
    `train_hierarchical_layers.rs`, `train_model.rs`) — thin marshalling, no
    numerics in `prin-py`, `#![deny(unsafe_code)]` unchanged.
  - **Python `nn.Module` wrappers** in `python/prin/nn/`
    (`inhibition_layers.py`, `autoencoders.py`, `hierarchical_layers.py`,
    `model.py`); `deferred_layers.py` re-exports from implementation modules.
  - **Float64 gradcheck** for all 11 trainable modules (all except
    `oscillatory_weight_init` — init function — and `compile_model` — pure
    Python passthrough).
  - **Forward-parity tests** against PRINet 3.0 reference within documented
    tolerance for every symbol (DV-018 and D-4 governed where applicable).
  - **52 new Python tests** across four new test files.
  - **`_prin_core.pyi` stubs** updated for all 12 new bridge classes and
    their `*Ctx` backward contexts.
  - **Migration Guide** updated for all 13 symbols (from "D-2.2 stub" to
    "real implementation" with Rust owner and delegation path).
  - **S2 audit** (`DOCS/audits/036a-wp036a-audit.md`): verdict PASS, zero
    findings.
  - **S3 remediation:** no-change closure (zero findings to remediate),
    delta re-audit CLEAN.
  - **S4 documentation:** This report; CHANGELOG updated; crate READMEs
    updated (`prin-train`, `prin-py`, `prin.nn`, workspace `crates/README.md`);
    session registers current.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendments #1–#34
  remain in force. Amendments #33 (WP-036A creation) and #34 (S1
  decomposition into sub-passes) were adopted and executed this cycle.
- **Audit:** `DOCS/audits/036a-wp036a-audit.md` — S2 verdict PASS (zero
  findings). S3 no-change closure, delta re-audit CLEAN. No unresolved
  D1/D2 finding exists.
- **Session Register:** 0144A + 0144A1–0144A4 (S1), 0144B (S2), 0144C (S3),
  0144D (S4) all marked COMPLETE; 0144E (WP-036B S1) is the registered
  successor.

---

## 2. Metric trends

| Metric | Previous (PSR-036) | Current (PSR-036A) | Gate |
|---|---|---|---|
| Rust tests passing | 1447 passed, 0 failed, 1 ignored | **1540 passed**, 0 failed, 1 ignored; +93 from WP-036A (new `prin-train` lib tests for inhibition/autoencoder/hierarchical/model modules + integration tests) | 100% where defined |
| Python tests passing | 1214 passed, 9 deselected (fast suite) | **1266 passed**, 9 deselected (fast suite); +52 from WP-036A (4 new test files) | 100% |
| Coverage (changed code) | 99% overall (`python/prin/`) | **99% overall** (`python/prin/`); all 4 new WP-036A Python modules at 98–100% | ≥95% on instrumented changed code |
| Docstring coverage (interrogate) | 97.1% overall | **97.4%** overall (604/620); all new WP-036A modules at 100% | ≥95% overall |
| Parity cases passing | 172-symbol smoke matrix green | 172-symbol smoke matrix green; 13 WP-036A symbols now have real forward-parity tests at documented tolerances; gradcheck green for 11 trainable modules | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit | 0 across all gates | 0 across all gates; `cargo audit` exit 0 with 3 governed allowed warnings (`paste`/`bincode`/`chacha20`); `pip-audit` clean | 0 at gate threshold |
| Sphinx warning-as-error build | 0 warnings | 0 warnings (fresh-directory build; Migration Guide renders all 13 WP-036A symbol rows as real implementations) | 0 warnings |
| Snyk Code / Snyk Open Source | CI authoritative | Snyk Code: 0 issues on every new/modified first-party file (per S1 handoff note); Snyk Open Source: N/A (no dependency manifest changed) | 0 at gate threshold |
| Benchmark regression gates | none tripped | none tripped (no benchmark code changed) | none tripped |

**Verification commands re-run in S4 (2026-08-31, this host, Windows 11 /
Rust 1.92.0 / Python 3.14.0):**

```
cargo fmt --all -- --check                                                    # clean
cargo clippy --workspace --all-targets -- -D warnings                         # exit 0
cargo test --workspace                                                        # 1540 passed, 0 failed, 1 ignored
RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps                      # exit 0
cargo audit                                                                   # exit 0; 3 governed allowed warnings
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/            # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/   # 166 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # 53 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 97.4%, PASS
.venv\Scripts\python -m bandit -r . -c pyproject.toml                         # 0 issues (26490 LOC)
.venv\Scripts\python -m pip_audit .                                           # 0 vulnerabilities
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt             # 0 vulnerabilities
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin    # 1266 passed, 9 deselected, 99% cov
.venv\Scripts\python tools/wp001_baseline.py check                            # passed
.venv\Scripts\python tools/check_deviation_ledger.py ...                      # passed (120 vs 120 rows)
.venv\Scripts\python tools/check_dv_register_gates.py                         # 29 rows / 198 sessions, passed
.venv\Scripts\python tools/wp036_migration_table.py check                     # OK (172 symbols)
.venv\Scripts\python tools/check_no_python_numerics.py                        # clean (17 modules)
python -c "import prin; from prin._deprecation import verify_api_surface; ..."  # (set(), set())
sphinx-build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html      # build succeeded (fresh dir)
```

---

## 3. Deviation ledger (cumulative)

No new findings this cycle. The cumulative table carries forward every row
from PSR-036 §3 unchanged (verified by `tools/check_deviation_ledger.py`).
WP-036A's S2 audit recorded zero findings; S3 performed the mandatory
no-change closure with independent delta re-audit CLEAN.

The full cumulative deviation ledger is maintained in PSR-036 §3 and carried
forward unchanged. The two WP-036 rows (WP036-F1 FIXED, WP036-F2 AMENDED)
remain the most recent additions.

---

## 4. Plan amendments this cycle

Two new amendments adopted and executed:

- **Amendment #33** (2026-08-29): D-D-appendix rows 31–44 owning-WP
  decision. Created WP-036A ("Trainable compatibility layers — `prin-train`
  extension") for the 13 symbols (rows 31–42, 44) requiring new trainable
  Rust numerics. Sessions `0144A`–`0144D` assigned to WP-036A; existing
  WP-036B/C sessions shifted to `0144E`–`0144H`/`0144I`–`0144L`.
- **Amendment #34** (2026-08-30): WP-036A S1 executed as four sequential
  coding sub-passes `0144A1`–`0144A4` (dependency-ordered), all feeding the
  single S2 audit `0144B`.

---

## 5. Risks and blockers

- **DV-005 (CUDA Burn backend):** Scoping decision per R31 disposition —
  deferred out of Phase 6; RC1's exit criteria do not require GPU training.
  Standing disposition (plan amendment #7) unchanged.
- **DV-008/DV-017 (`paste`/`bincode` RUSTSEC) + `chacha20` yanked:**
  unchanged — allowed warnings per amendments #9/#27, re-verified this cycle
  (`cargo audit` exit 0, only these three warnings).
- **DV-009 (GitHub secret scanning):** unchanged — Gitleaks + branch
  protection substitute per amendment #5.
- **DV-010 (Phase 1/2 pre-release tag):** unchanged — pending explicit
  maintainer tag-push action.
- **DV-022 (ubuntu runner disk exhaustion):** external infrastructure
  condition. Status: OPEN, unchanged.
- **DV-025 (`retrain_controller`):** Stub delivered in WP-036 S1 (0141E);
  real implementation owned by WP-036C S1 (session 0144I) per register row.
- **`DiscreteDeltaThetaGamma` standalone binding:** The composed
  `DiscreteDeltaThetaGammaLayer` (WP-036A, row 44) is real; the independent
  core binding (row 43) is assigned to WP-036B S1 (session 0144E,
  binding-only, no new numerics).
- All other DV register items closed at or before PSR-036 remain closed;
  `tools/check_dv_register_gates.py` passes (29 rows / 198 sessions).
- No new risks introduced.

---

## 6. Next work package declaration — WP-036B

Quoted directly from the registered successor session brief
(`DOCS/sessions/phase-6/0144E-wp036b-s1-acceptance-suite-port-core-dynamics-model-stack.md`),
per Documentation Standards §7 item 5:

- **Title:** Acceptance suite port — core, dynamics, model stack, subconscious.
- **Scope (files/crates/modules):** Port reference test clusters
  `test_core`, `test_utils`, `test_phases`, `test_hierarchical`,
  `test_phase_to_rate`, `test_q2`, `test_q2_remaining`, `test_q3_new`,
  `test_nn`, `test_scalr_enhanced`, `test_hybrid`, `test_clevr_n`,
  `test_subconscious` (~805 reference `def test_` functions). Imports adapted
  to `prin`; assertions unchanged.
- **Plan sections advanced:** §6 (Phase 6 roadmap).
- **Acceptance criteria:** Every ported test in scope passes on CPU,
  Linux + Windows, Python 3.11–3.13. Assertions are unchanged from the
  reference except where a failure is attributable *solely* to a documented
  preserved numerical hazard (amendments #14/#16/#17/#25), in which case a
  per-test tolerance annotation is added and recorded in the Parity Report —
  never a deletion, skip, or weakened logical assertion. Purely GPU/Triton
  reference tests in these files are `skipif`-guarded on backend availability
  (reference-suite precedent). Coverage non-decreasing; zero skipped tests
  without a linked, maintainer-approved quarantine issue.
- **Non-goals:** New `prin` public symbols (WP-036 owns those; a genuine gap
  is an out-of-scope discovery recorded for WP-036 follow-up, not silently
  filled here); the integration/y-series/kernel clusters (WP-036C); final
  documentation prose or release publishing.
- **First session brief:**
  `DOCS/sessions/phase-6/0144E-wp036b-s1-acceptance-suite-port-core-dynamics-model-stack.md`
  (present in `SESSION_REGISTER.md`/`DOCS/sessions/phase-6/` as `PLANNED`).
- **Maintainer approval:** Required before WP-036B S1 begins.

---

## 7. Cross-cutting document currency

Per Documentation Standards §7: the three documents it names are verified
current:

**(a) `DOCS/PRIN_Project_Plan.md` §6 roadmap-table:** Phase 6 in progress
(5/7 WPs complete: WP-033, WP-034, WP-035, WP-036, WP-036A).

**(b) `DOCS/experiments/README.md`:** Verified current — includes
`0144A-wp036a-s1-handoff.md` (WP-036A S1 handoff note, 575 lines).

**(c) `DOCS/sessions/SESSION_REGISTER.md` Global Sessions section:**
Verified current — 0144A + 0144A1–0144A4 (S1), 0144B (S2), 0144C (S3),
0144D (S4) all marked COMPLETE; 0144E–0144H (WP-036B) and 0144I–0144L
(WP-036C) marked PLANNED.
