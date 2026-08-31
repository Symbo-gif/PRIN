---

# PRIN Project State Report — Cycle 036B

**Date:** 2026-08-31
**Cycle:** 036B (WP-036B "Acceptance suite port — core, dynamics, model stack,
subconscious")
**Completed sessions:** 0144E + 0144E1–0144E6 (S1), 0144F (S2), 0144G (S3),
0144H (S4)
**Author:** Qwen Code (AI pair)
**Git state:** `main` @ S4 closure

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1 (**6 of 7**
  phase-6 WPs complete: WP-033, WP-034, WP-035, WP-036, WP-036A, WP-036B).
- **This cycle delivered:**
  - **13 PRINet 3.0 reference files strict-ported** under stable
    `tests/test_acceptance_*.py` names: 498 `def test_` functions across
    8,085 reference lines. Import-only adaptation (Testing Standards §1.1):
    zero assertion edits, zero tolerance annotations, zero unapproved skips.
  - **Execution:** 489 passed, 9 skipped (8 CUDA `skipif` + 1 `psutil`-absent,
    all matching reference guards).
  - **Six sequential S1 sub-passes** (plan amendment #35): `0144E1` (core +
    utils, 125 functions), `0144E2` (phases + hierarchical + phase-to-rate,
    95), `0144E3` (q2 + q2_remaining, 118), `0144E4` (q3_new + nn +
    scalr_enhanced, 75), `0144E5` (hybrid + clevr_n, 36), `0144E6`
    (subconscious + consolidation, 49).
  - **Compatibility behavior** rebuilt through Rust-backed layers with thin
    PyO3/Python delegation; no Python numerics (`check_no_python_numerics.py`
    clean for 19 modules).
  - **S2 audit** (`DOCS/audits/036b-wp036b-audit.md`): verdict PASS, zero
    findings. §8 addendum documented the GPU skip assessment and remediation
    roadmap, leading to amendment #36 (WP-036D).
  - **S3 remediation:** no-change closure (zero findings to remediate),
    delta re-audit CLEAN.
  - **S4 documentation:** This report; `tests/README.md` updated with
    ported-suite inventory (13 files, 498 tests, per-file counts, marker
    policy); CHANGELOG updated; session registers current.
  - **Plan amendment #36** (2026-08-31): new work package WP-036D ("GPU
    execution path for the ported acceptance suite") declared as WP-036's
    sibling, taking sessions `0144I`–`0144L`; WP-036C sessions shifted
    `0144I`–`0144L` → `0144M`–`0144P`.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendments #1–#36
  remain in force. Amendments #35 (WP-036B S1 decomposition) and #36
  (WP-036D creation + WP-036C renumber) were adopted and executed this cycle.
- **Audit:** `DOCS/audits/036b-wp036b-audit.md` — S2 verdict PASS (zero
  findings). S3 no-change closure, delta re-audit CLEAN. No unresolved
  D1/D2 finding exists.
- **Session Register:** 0144E + 0144E1–0144E6 (S1), 0144F (S2), 0144G (S3),
  0144H (S4) all marked COMPLETE; 0144I (WP-036D S1) is the registered
  successor.

---

## 2. Metric trends

| Metric | Previous (PSR-036A) | Current (PSR-036B) | Gate |
|---|---|---|---|
| Rust tests passing | 1540 passed, 0 failed, 1 ignored | **1540 passed**, 0 failed, 1 ignored (unchanged — WP-036B is test-porting only, no crate changes) | 100% where defined |
| Python tests passing | 1266 passed, 9 deselected (fast suite) | **1770 passed**, 9 deselected (fast suite); +498 from WP-036B (13 new `test_acceptance_*.py` files) + 6 pre-existing WP-036B support tests | 100% |
| Coverage (changed code) | 99% overall (`python/prin/`) | **97.4%** overall (`python/prin/`); the 3 reporting modules below 95% (`_artifacts.py` 50%, `figure_generation.py` 90%, `table_generation.py` 65%) are pre-existing and outside WP-036B scope | ≥95% overall |
| Docstring coverage (interrogate) | 97.4% overall | **97.4%** overall (unchanged) | ≥95% overall |
| Parity cases passing | 172-symbol smoke matrix green; 13 WP-036A symbols with forward-parity tests | 172-symbol smoke matrix green; **498 acceptance tests green** (489 pass + 9 reference guards); zero tolerance annotations | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit | 0 across all gates | 0 across all gates; `cargo audit` exit 0 with 3 governed allowed warnings (`paste`/`bincode`/`chacha20`); `pip-audit` clean; bandit 1 Low (B110, `hybrid_compat.py:327`, `# noqa: S110`, governed) | 0 at gate threshold |
| Sphinx warning-as-error build | 0 warnings | 0 warnings (fresh-directory build) | 0 warnings |
| Snyk Code / Snyk Open Source | CI authoritative | Snyk Code: 0 issues on every new/modified first-party file; Snyk Open Source: N/A (no dependency manifest changed) | 0 at gate threshold |
| Benchmark regression gates | none tripped | none tripped (no benchmark code changed) | none tripped |
| `check_no_python_numerics.py` | clean (17 modules) | **clean (19 modules)**; WP-036B's ported acceptance suite exercises all 19 governed compat modules | clean |

**Verification commands re-run in S4 (2026-08-31, this host, Windows 11 /
Rust 1.92.0 / Python 3.14.0):**

```
cargo fmt --all -- --check                                                    # clean
cargo clippy --workspace --all-targets -- -D warnings                         # exit 0
cargo test --workspace                                                        # 48 test result: ok lines, 0 failed, 1 ignored
RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps                      # (unchanged from PSR-036A)
cargo audit                                                                   # exit 0; 3 governed allowed warnings
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/            # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/   # 193 files already formatted
.venv\Scripts\mypy python/prin --strict                                       # 55 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 97.4%, PASS
.venv\Scripts\python -m bandit -r . -c pyproject.toml                         # 1 Low (B110, governed, noqa annotated)
.venv\Scripts\python -m pip_audit .                                           # 0 vulnerabilities
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt             # 0 vulnerabilities
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp  # 1770 passed, 9 skipped, 9 deselected
.venv\Scripts\python -m pytest tests/test_acceptance_*.py --basetemp=.pytest_basetemp         # 498 collected, 489 passed, 9 skipped
.venv\Scripts\python tools/check_no_python_numerics.py                        # clean (19 modules)
sphinx-build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html      # build succeeded (fresh dir)
```

---

## 3. Deviation ledger (cumulative)

No new findings this cycle. The cumulative table carries forward every row
from PSR-036A §3 unchanged. WP-036B's S2 audit recorded zero findings; S3
performed the mandatory no-change closure with independent delta re-audit
CLEAN.

The full cumulative deviation ledger is maintained in PSR-036 §3 and carried
forward unchanged. The two WP-036 rows (WP036-F1 FIXED, WP036-F2 AMENDED)
remain the most recent additions.

---

## 4. Plan amendments this cycle

Two new amendments adopted and executed:

- **Amendment #35** (2026-08-31): WP-036B S1 (session `0144E`) decomposed
  into six sequential strict-port coding sub-passes `0144E1`–`0144E6`,
  inserted between `0144E` and the S2 audit `0144F`. The 13 reference files
  contain 498 test functions / 8,085 lines; a single S1 pass exceeded one
  reviewable commit range (Development Workflow §7). All six commit at their
  own green local gate and feed the single S2 audit `0144F`. Planned session
  count 220 → 226.
- **Amendment #36** (2026-08-31): new work package WP-036D ("GPU execution
  path for the ported acceptance suite") declared as WP-036's sibling in the
  alphabetic-suffix family, taking sessions `0144I`–`0144L`; the existing
  WP-036C sessions shifted `0144I`–`0144L` → `0144M`–`0144P`. WP-036D
  closes the gap the WP-036B S2 audit §8 addendum surfaced: 8 of the 9
  acceptance-suite skips are CUDA guards on tests with a real reference GPU
  path, permanently red because `python/prin/_torch_compat.py` has no GPU
  execution path — while the Rust CubeCL kernels (`prin-kernels`), the
  `prin-sim` GPU engines, and the self-hosted `PRIN-GPU-Runner` all already
  exist. WP-036D S1 (session `0144I`) decomposed into three sub-passes
  `0144I1`–`0144I3`. Planned session count 226 → **233**.

---

## 5. Risks and blockers

- **8 CUDA-guarded acceptance tests remain skipped.** The GPU execution path
  (WP-036D) is the registered remediation. The Rust kernels, sim engines, and
  self-hosted runner all exist; the gap is exclusively the PyO3 GPU binding
  layer and Python-side device dispatch. WP-036D S1 decomposes into three
  sub-passes to close this gap.
- **DV-005 (CUDA Burn backend):** Scoping decision per R31 disposition —
  deferred out of Phase 6; RC1's exit criteria do not require GPU training.
  WP-036D does **not** close DV-005 (it targets the inference/dynamics GPU
  path only, not `prin-train`/autodiff). Standing disposition (plan
  amendment #7) unchanged.
- **DV-001 (Linux Triton runner):** Unchanged; WP-036D targets the CUDA/wgpu
  path the existing Windows `PRIN-GPU-Runner` already serves.
- **DV-008/DV-017 (`paste`/`bincode` RUSTSEC) + `chacha20` yanked:**
  unchanged — allowed warnings per amendments #9/#27, re-verified this cycle
  (`cargo audit` exit 0, only these three warnings).
- **DV-009 (GitHub secret scanning):** unchanged — Gitleaks + branch
  protection substitute per amendment #5.
- **DV-010 (Phase 1/2 pre-release tag):** unchanged — pending explicit
  maintainer tag-push action.
- **DV-022 (ubuntu runner disk exhaustion):** external infrastructure
  condition. Status: OPEN, unchanged.
- **DV-025 (`retrain_controller`):** Assigned to WP-036C S1 (session
  `0144M` after amendment #36 renumber). Stub delivered in WP-036 S1
  (0141E); real implementation owned by WP-036C.
- All other DV register items closed at or before PSR-036A remain closed;
  `tools/check_dv_register_gates.py` passes.
- No new risks introduced.

---

## 6. Next work package declaration — WP-036D

Quoted directly from the registered successor session brief
(`DOCS/sessions/phase-6/0144I-wp036d-s1-gpu-execution-path-ported-acceptance-suite.md`),
per Documentation Standards §7 item 5:

- **Title:** GPU execution path for the ported acceptance suite.
- **Scope (files/crates/modules):** Close the GPU execution path gap the
  WP-036B S2 audit §8 addendum identified: add PyO3 GPU bindings over
  `prin-sim`'s GPU engines (`0144I1`), add device dispatch to
  `python/prin/_torch_compat.py` (`0144I2`), activate the 8 CUDA-guarded
  acceptance tests with `@pytest.mark.gpu` and update `gpu.yml` (`0144I3`).
- **Plan sections advanced:** §6 (Phase 6 roadmap).
- **Acceptance criteria:** The 8 CUDA-guarded tests pass on the self-hosted
  `PRIN-GPU-Runner` with real GPU execution (not CPU round-trip). CPU path
  is byte-for-byte unaffected (489 passing tests remain green). Kernel
  equivalence: GPU vs CPU results within Testing Standards §3 tolerances
  (`rtol=1e-5`, `atol=1e-6` for f32 GPU kernel vs CPU reference). No new
  `prin` public symbol; no Python numerics.
- **Non-goals:** DV-005 (CUDA Burn training backend); DV-001 (Linux Triton
  runner); WP-036C (integration/y-series/kernel cluster port).
- **First session brief:**
  `DOCS/sessions/phase-6/0144I-wp036d-s1-gpu-execution-path-ported-acceptance-suite.md`
  (present in `SESSION_REGISTER.md`/`DOCS/sessions/phase-6/` as `PLANNED`).
- **Maintainer approval:** Required before WP-036D S1 begins.

---

## 7. Cross-cutting document currency

Per Documentation Standards §7: the three documents it names are verified
current:

**(a) `DOCS/PRIN_Project_Plan.md` §6 roadmap-table:** Phase 6 in progress
(6/7 WPs complete: WP-033, WP-034, WP-035, WP-036, WP-036A, WP-036B).

**(b) `DOCS/experiments/README.md`:** Verified current — includes
`0144E-wp036b-s1-handoff.md` (WP-036B S1 handoff note).

**(c) `DOCS/sessions/SESSION_REGISTER.md` Global Sessions section:**
Verified current — 0144E + 0144E1–0144E6 (S1), 0144F (S2), 0144G (S3),
0144H (S4) all marked COMPLETE; 0144I–0144L (WP-036D) and 0144M–0144P
(WP-036C) marked PLANNED.
