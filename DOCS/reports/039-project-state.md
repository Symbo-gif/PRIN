# PRIN Project State Report — Cycle 039

**Date:** 2026-09-27
**Cycle:** 039 (EXP-001 D1 correction documentation — campaign plan §10.4)
**Completed sessions:** Contingency correction S1 (2026-09-24), S2 (2026-09-27),
S3 (2026-09-27), S4 (2026-09-27)
**Author:** Qwen Code (AI pair)
**Git state:** `hotfix/exp001-d1-parity-correction` @ `4516961` (post-S3; PR #24
draft, not yet merged to `main`)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 7 — Experimentation campaign. The campaign is **BLOCKED**
  at session 0159 (EXP-002 E1) per campaign plan §10.4 item 2.
- **This cycle delivered:** The four-session EXP-001 D1 correction cycle
  mandated by campaign plan §10.4. S1 established the root cause of both H1
  and H2a refutations by controlled substitution and arbitrary-precision audit:
  (a) PRIN's Euler/RK4 guard divergence — PRIN applied `[1e-6, 10]` amplitude
  and `±1e4` derivative bounds from PRINet 3.0's fused-kernel/OscilloSim paths
  to the `OscillatorModel._step_euler`/`_step_rk4` port, while the reference
  path floors amplitude at `0` with no ceiling; (b) PRINet 3.0's DV-007
  `complex64` arithmetic in the Stuart–Landau and mean-field derivatives — the
  corpus is the erroneous side (campaign plan §10.4 item 3, established by
  50-digit mpmath exactness audit, 67/67 cases). The fix introduces
  `GuardPolicy::NonNegative` as the default, with `GuardPolicy::Bounded` for
  OscilloSim ports. S2 audited the range `dc468c1..7235ae6` (40 files,
  +87,826/−151 lines) and returned **PASS** (zero findings above D4). S3
  produced a **CLEAN** delta re-audit with all five D4 findings resolved or
  carrying governed dispositions. S4 (this cycle) issues this PSR, updates all
  registers, appends the erratum pointer to the E5 report, and authorizes
  `EXP-001-r1`.
- **EXP-001 E5 report announced** (Experimentation Standards §2 E5). The E5
  report (`DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/report.md`)
  was issued 2026-09-23 UTC by session 0158, verified and accepted by the
  maintainer the same day, and carried to `main` by PR #23. Verdicts: H1
  `REFUTED` (485/504), H2a `REFUTED` (897/1,000), H2b `CONFIRMED`, H3
  `CONFIRMED`, H4 `CONFIRMED`. Second D1 **EXP001-E5-F1** raised (the `parity`
  CI corpus gate did not exercise PRIN).
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS. Campaign plan
  amendment #47 (Plan §5.6 path-specific guard hazards) is in force. No new
  plan amendment was adopted in this correction cycle.
- **Audit:** `DOCS/audits/2026-09-24-exp001-d1-correction-audit.md` — S2
  verdict **PASS** (A1–A10, five D4 findings); S3 delta re-audit **CLEAN**;
  S4 documentation complete.
- **Session Register:** Contingency correction S1–S4 marked COMPLETE.
  Session 0159 stays **BLOCKED** (see §5).

---

## 2. Metric trends

| Metric | Previous (PSR-038) | Current (PSR-039) | Gate |
|---|---|---|---|
| Rust tests passing (default) | 1,577 passed, 1 ignored | **1,590 passed, 0 failed, 1 ignored** (sequential per-crate; S3 delta) | 100% where defined |
| Python full suite + parity | 3,496 passed, 185 skipped | **3,275 passed, 0 failed, 181 skipped, 48 deselected** (fast suite; S3 delta) + **2,144 passed, 1 skipped** (parity suite) | 100% at registered tolerance |
| Coverage | 95% total | **95% total** (S1.5: `prin-dynamics` changed-line 97.2%) | ≥95% |
| Docstring coverage | 97.6% | **97.6%** | ≥95% overall |
| Sphinx warning-as-error build | 0 warnings | **0 warnings** | 0 warnings |
| Clippy/ruff/mypy/interrogate/bandit | 0 findings | **0 findings** | 0 |
| Snyk Code | 0 issues | **0 issues** (34 LOW in untouched files, unchanged) | governed scope clean |
| Native dependency audits | cargo audit 3 governed warnings | **cargo audit exit 0** (3 governed: paste, bincode, chacha20) | governed warnings only |
| `check_dv_register_gates.py` | pass (37 rows) | **pass (40 rows / 198 sessions)** | pass |
| Parity gates (new) | N/A | **504/504 corpus pass; 978+22 fuzz pass** | 100% at tolerance |

---

## 3. Deviation ledger (cumulative)

### 3.1 New findings this cycle

| ID | Severity | Summary | Status | Reference |
|---|---|---|---|---|
| EXP001-D1-H1 | D1 | EXP-001 H1 `REFUTED` (485/504): 19 corpus cases breach registered tolerance | **RESOLVED** — root cause: DV-007 `complex64` (corpus is erroneous side, §10.4 item 3, 67/67 exactness audit). Full-corpus PRIN gate now passes. | S1 record, audit §S1.2; amendment #47 |
| EXP001-D1-H2a | D1 | EXP-001 H2a `REFUTED` (897/1,000): 103 fuzz cases breach | **RESOLVED** — two mechanisms: DV-007 (38) + PRIN guard (33) + interaction (10) + ill-conditioned (19) + guard+ill-conditioned (3). Guard fixed; DV-007 adjudicated; ill-conditioned characterized. | S1 record, audit §S1.2 |
| EXP001-E5-F1 | D1 | `parity` CI corpus gate does not exercise PRIN | **RESOLVED** — `parity/test_parity_prin_corpus.py` (504 cases) and `parity/test_parity_prin_fuzz.py` (1,000 cases) now run in `parity` job. Pre-fix tree fails both; post-fix tree passes. | S1 commits `bd737e1`, `45cca61`; S3 delta re-audit |

### 3.2 S2 findings (all D4, all resolved or deferred)

| ID | Severity | Summary | Status | Reference |
|---|---|---|---|---|
| S2-F1 | D4 | Windows linker contention (LNK1104) | ENVIRONMENTAL — sequential execution workaround verified | S3 §3.1 |
| S2-F2 | D4 | WSL bash relay (4 test failures) | RESOLVED — Git Bash prepended on PATH | S3 §3.1 |
| S2-F3 | D4 | `#[non_exhaustive]` on `GuardPolicy` deferred | DEFERRED to API freeze | S3 §3.1 |
| S2-F4 | D4 | RK45/Exponential/Jacobian guard clamp | DEFERRED to future WP; documented and regression-pinned | S3 §3.1 |
| S2-F5 | D4 | `prin-kernels` Triton RK4 clamp unverified | DEFERRED; hardware-gated (DV-001) | S3 §3.1 |

### 3.3 Cumulative ledger

The cumulative table carries forward every row from PSR-038 §3 unchanged and
appends the three D1 rows above (all RESOLVED) and the five D4 rows (all
resolved or deferred with governed dispositions). No earlier finding was
reopened.

---

## 4. Plan amendments this cycle

| Amendment | Plan/standard section | Rationale | Approved by |
|---|---|---|---|
| #47 | Plan §5.6 (preserved numerical hazards) | Makes the hazard list path-specific: `OscillatorModel._step_euler`/`_step_rk4` guard is the default (`NonNegative`); fused-kernel/OscilloSim guard is opt-in (`Bounded`). | MichaelMaillet (S1.1, 2026-09-24 UTC) |

---

## 5. Risks and blockers

- **Session 0159 (EXP-002 E1) remains BLOCKED.** Campaign plan §10.4 item 5
  requires `EXP-001-r1`'s E5 verdict to not be a reversal before 0159 may
  proceed, or the maintainer records a Plan §8.3 amendment accepting a changed
  conclusion. S4 closing on its own does **not** release 0159.
- **PR #24 not yet merged.** The correction branch
  `hotfix/exp001-d1-parity-correction` is a draft PR. Merge requires the
  maintainer's explicit approval. CI-green evidence for the merge SHA will be
  recorded by the next governed session (per campaign plan §12 item 3).
- **DV-036 reference-host re-baseline gates** (before 0168 and 0173) and
  **DV036-F5** (at 0166) remain open and are additionally gated behind the
  campaign block.
- **DV-040** (campaign E4 analysis code outside CI lint paths) remains OPEN
  with its EXP-002 E4 / session 0162 re-audit gate.

---

## 6. Next work package declaration

No new WP is declared. The next action is the merge of PR #24, followed by
`EXP-001-r1` E1 (pre-registration, session to be declared by the maintainer).
Session 0159 remains blocked until `EXP-001-r1` returns a non-reversal
verdict.

---

## 7. Verification commands (S4, 2026-09-27)

S4 is a documentation-only session. No source code changed. The verification
commands are those of the S3 delta re-audit, which S4 inherits:

```powershell
# S3 delta re-audit (inherited; authoritative for the correction)
cargo fmt --all -- --check                                          # clean
cargo clippy --workspace --all-targets -- -D warnings               # clean
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings  # clean
# cargo test per-crate (sequential, Windows): 1,590 passed, 0 failed, 1 ignored
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/ EVIDENCE/exp001-d1-s1/  # clean
.venv\Scripts\ruff format --check (same paths)                      # clean
.venv\Scripts\mypy python/prin --strict                             # clean
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin   # 97.6%
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml    # clean
cargo audit                                                         # exit 0
.venv\Scripts\python -m pip_audit .                                 # clean
# Parity gates: 504/504 corpus pass; 978+22 fuzz pass; 2,144 passed, 1 skipped
# Sphinx clean build: 0 warnings
# tools/check_dv_register_gates.py: pass (40 rows)
```

S4 adds no new code, tests, or gates. S4's deliverables are documentation
artefacts only (this PSR, register updates, erratum pointer, EXP-001-r1
authorization).
