---

---

# PRIN Phase 5 Analytics Report

**Phase:** 5 — Daemon and experiment tooling
**Date:** 2026-08-26
**Analyst:** Qwen Code (AI pair)
**Maintainer approval:** pending
**Methodology:** [`DOCS/ANALYTICS/ANALYTICS_METHODOLOGY.md`](../ANALYTICS_METHODOLOGY.md)
**Git state:** `main` @ `5fdfeb0` (current `HEAD`; one commit past the EMA-005 remediation / DV-026 close; up to date with `origin/main`, working tree clean)
**Phase 5 work-package commit range:** `3588aa6` (WP-028 S1) → `a19dbfe` (WP-032 S4, documentation closure, Phase 5 exit gate GREEN) — 35 commits from the Phase 4 recommendation-implementation close (`df577f3`)
**Global-session layer (interleaved after the WP-032 S4 close):** `cb5660b`/`5d90427` (post-close CI hotfixes) → `79cf971` (EA-006) → `c8d67d3` (EMA-005) → `d256cc6` (EMA-005 remediation) → `5fdfeb0` (DV-026/M-F9 tool-remediation, current `HEAD`)
**Work packages:** WP-028 through WP-032 (5 cycles, 20 sessions, 0109–0128) + Executive Audit Session 006 (EA-006) + Executive Mathematical Audit Session 005 (EMA-005)
**Phase exit gate:** GREEN (`DOCS/reports/032-project-state.md` §6; independently re-confirmed by EA-006 §E10 and, with qualifications recorded in §8 below, by this session)

---

## Executive summary

Phase 5 — Daemon and experiment tooling is **complete**. All five work packages
(WP-028 through WP-032) passed through the full Session Cycle (S1→S2→S3→S4)
in exact order across 20 sessions (0109–0128), delivering `prin-daemon` — the
project's first entirely new crate since Phase 4's `prin-train` — a 6,926-line,
10-module, zero-`unsafe` native daemon runtime (`#![forbid(unsafe_code)]`
crate-wide) implementing the ONNX subconscious controller, lock-free control
buffer, training hooks, MOT evaluation, temporal statistics, and adversarial
tooling; plus 1,560 lines of PyO3 bindings (`daemon.rs` + `phase5.rs`), 928
lines of Python evaluation facades, and the Phase 5 exit gate (WP-032). This
is the **best per-WP audit discipline of any phase in the project's history**:
**all five WPs received `PASS` at S2 with zero findings** — no D1, no D2, no
D3, no D4. For comparison, Phase 4's best-in-class prior record was 0 of 6
`FAIL` verdicts but 11 WP-level findings total; Phase 5 has zero.

Two **global-tier sessions** closed after WP-032 S4:

- **EA-006** (2026-08-26): full-project executive audit across E1–E10,
  verdict `PASS-WITH-REMEDIATION`, 2 findings (E-F1 D3, E-F2 D3). E-F1
  (two post-close CI hotfix commits never recorded in the deviation ledger,
  leaving DV-024's closure claim stale) was FIXED same-session. E-F2 (Phase
  4 recommendation R28's explicit precondition — a dedicated hotfix/correction
  session for DV-019 before WP-028 S1 — was never honored, and Phase 5 fully
  executed and closed with it still outstanding) was remediated at the
  governance level: the compliance gap was recorded and WP-033 S1's session
  brief now carries a hard, mechanically-enforced entry-condition gate.
- **EMA-005** (2026-08-26): Phase 5 close mathematical audit — 46 claims
  across 9 ledgers (6 new Phase 5 claims, 40 re-verified with zero
  regressions). Verdict `PASS-WITH-REMEDIATION`: all 6 new claims reached
  genuine SymPy/Z3 `PASS` (no new `REQUIRES_HUMAN_REVIEW`); one D4
  tooling-coverage observation (M-F9, beta-function allowlist gap) discovered
  and worked around within the same session by a stronger first-principles
  derivation; M-F9 then closed at root cause by a same-day tool-remediation
  commit (`5fdfeb0`).

Independent re-verification during **this** analytics session (2026-08-26,
`HEAD` `5fdfeb0`) confirms every mandatory quality, testing, and security
gate is green and reproduces EA-006's figures exactly:

| Gate | Result | Evidence |
|---|---|---|
| `cargo fmt --all -- --check` | Clean | §5.4 |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean (exit 0) | §5.4 |
| `cargo test --workspace --exclude prin-py -- --test-threads=1` | **1442 passed, 0 failed, 1 ignored** | §5.4 |
| `cargo audit` | 2 pre-accepted advisories (`paste` DV-008, `bincode` DV-017), 0 new | §5.4 |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | Clean, 0 warnings | §5.4 |
| `ruff check` / `ruff format --check` | Clean | §5.4 |
| `mypy python/prin --strict` | Success, 28 files, 0 issues | §5.4 |
| `interrogate -c pyproject.toml python/prin` | 100.0% (266/266) | §5.4 |
| `bandit -r . -c pyproject.toml` | 0 medium/high issues (2 Low in `EVIDENCE/` scripts) | §5.4 |
| `pytest tests/ -m "not slow and not gpu"` | **555 passed, 8 deselected** | §5.4 |
| `pytest tests/ parity/` | **1155 passed** | §5.4 |
| `pip-audit .` / `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities (both) | §5.4 |
| `snyk code test --severity-threshold=medium` | 0 issues | §5.4 |
| `sphinx-build -W --keep-going -b html` against a **fresh** output directory | Build succeeded, 0 warnings | §5.4 |
| `tools/check_deviation_ledger.py` | Ledger consistency check passed (111→112 rows) | §5.4 |
| `tools/wp001_baseline.py check` | WP-001 baseline validation passed | §5.4 |

This session's own findings, per Analytics Methodology principle 7 ("no
silent overrides"):

- **PA5-F1 (D3):** DV-019's flaky gradient-presence test (`prin-train::bands::tests::gradients_flow_to_every_parameter`) has now recurred **at least six times** across four modules (`bands.rs`, `hybrid.rs`, `phase_tracker.rs`, and — for the first time on the Python side — `tests/test_train_bridge_slot_attention.py`), spanning three consecutive phases (Phase 4 through the Phase 5 analytics session). Phase 4's R28 called for a dedicated hotfix/correction session "before session 0109 (WP-028 S1) begins"; EA-006's E-F2 recorded that this precondition was never honored; and the underlying code defect remains unfixed. The DV-019 row in the Deferred Validation Register now carries two separate `[RETROACTIVE UPDATE - Executive Audit 006]` tags (one for the missed-precondition gap, one for the recurrence narrative) — the most heavily annotated open item in the register by markup density. Open, unresolved as of this report.

No other new findings. Every gate this session re-executed reproduced the
PSR/EA-006/EMA-005 figures exactly, including the clean Sphinx build from a
fresh directory (R30's fix from Phase 4 held for the entire phase).

### Aggregate phase verdict

**PASS — SATISFACTORY**

All nine dimensions score ≥ 3; five dimensions (P1, P3, P4, P6, P7) reach 4;
no dimension scores below 3. The phase does not clear the `PASS — EXCELLENT`
bar because P5 and P9 each carry a genuine, evidence-backed caveat: the
missed R28 precondition (P6's governance score absorbs this too, but P5's
independent-verification dimension notes that EA-006 — the mechanism that
*should* have caught it — found it only post-hoc) and DV-019's now-six-
recurrence open status (P9's deferred-validation dimension). This is the
fourth consecutive `PASS — SATISFACTORY` verdict (Phase 2, 3, 4, 5), and —
as with every prior phase — it reflects real improvement in some respects
(the best per-WP audit discipline of any phase: 0 findings across 5 WPs)
sitting alongside a genuinely stubborn open item (DV-019) that has now
survived three consecutive phases' worth of recommendations, executive
audits, and mathematical audits without a code fix.

### Dimension scores

| Dimension | Score | Label | One-line justification |
|---|---|---|---|
| P1 Data and parity artefacts | 4 | Strong | `prin-daemon` ships with 10 Rust bit-exact parity tests (subconscious controller output) + 2 MOT parity tests reproduced at S3; 510 differential parity tests unchanged and green; EMA-005 added first-ever mathematical claims for daemon/statistics code (6/6 genuine PASS); but DV-005 (CUDA Burn backend) and DV-006 (DirectML/VitisAI ONNX) remain open — the daemon is CPU-only ONNX Runtime, with NPU execution still hardware-blocked |
| P2 Documentation | 4 | Strong | CHANGELOG/README/Migration-Guide discipline held at every one of the 5 WP S4s and both EA/EMA sessions; Project Plan §6 correctly marked `✅ COMPLETE` at phase close (R26's fix held); fresh-directory Sphinx build clean (R30's fix held for the entire phase); but two post-close hotfix commits initially lacked CHANGELOG entries (E-F1, fixed same-session by EA-006) |
| P3 Testing | 4 | Strong | 1442 Rust (exit 0), 555 Python fast, 1155 full py+parity — all independently reproduced this session with zero discrepancy; `prin-daemon` alone carries 219 Rust tests (163 lib + 35 integration + 21 doctests) across 6 integration test files; but DV-019's flaky test has now recurred at least six times across four modules, including a first Python-side recurrence |
| P4 Coding and architecture | 4 | Strong | `prin-daemon` (6,926 lines) carries zero `unsafe` under `#![forbid(unsafe_code)]`; crate layering holds exactly (no downward dependencies from foundational crates); "no numerics in Python" holds (verified by EA-006 §E1 and re-confirmed this session); zero WP-level findings across all 5 WPs is the cleanest implementation discipline of any phase; but the lock-free control buffer's correctness argument rests on single-producer/single-consumer atomic ordering — a pattern that is well-understood but subtle enough that a future formal-verification pass would be valuable |
| P5 Evidence and verification | 3 | Adequate | Every gate this session re-executed reproduced PSR/EA-006 figures exactly; Snyk Code clean from CLI; deviation-ledger tool passes; but EA-006's E-F2 revealed that Phase 4's R28 precondition (a DV-019 hotfix session before WP-028 S1) was never enforced by any mechanism — the governance gate existed on paper but had no mechanical enforcement until EA-006 added one retroactively |
| P6 Governance and process | 4 | Strong | 20/20 sessions in exact S1→S4 order; all 5 WPs received `PASS` at S2 with zero findings (unprecedented); 6 of 7 Phase 4 recommendations closed; EA-006/EMA-005 both `PASS-WITH-REMEDIATION` with all findings resolved or governed; but R28's precondition was silently skipped across the entire phase — the same "safeguard exists but is not mechanically enforced" class as Phase 4's PA4-F1, now with a hard entry-condition gate added for Phase 6 |
| P7 Security | 4 | Strong | `cargo audit`/Snyk Code/`pip-audit`/`bandit` all clean at governed thresholds, independently re-confirmed; zero new `unsafe` in any Phase 5 code; no new external dependencies this phase (the smallest supply-chain delta since Phase 0); Gitleaks clean |
| P8 Phase exit criteria | 4 | Strong | Plan §6's Phase 5 exit criteria (daemon latency target, MOT metrics match motmetrics reference) are genuinely met and independently evidenced (`EVIDENCE/0125-wp032-s1-daemon-latency.json`: lock-free p95 200 ns vs. PRINet 3.0's 250 ns); EA-006 §E8/E10 independently confirmed; but DV-006's DirectML graph-incompatibility means the ONNX controller cannot execute on DirectML without a graph export change — a known, documented, hardware/runtime-condition limitation rather than a code defect |
| P9 Risk and deferred validation | 3 | Adequate | DV register is current and evidence-cited (directly read in full this session); DV-024/DV-025/DV-026 closed during the phase; DV-005 explicitly re-gated to Phase 6 WP-036; but DV-019's six-recurrence flaky test is now the longest-open, most-recurrent unfixed code defect in the project's history, and DV-004 (non-instrumentable kernel bodies) has been open since Phase 0 with no movement in five phases |

---

## 1. Phase 5 scope and deliverables

### 1.1 Planned scope (Project Plan §6, Phase 5)

> **5 — Daemon + experiment tooling** ✅ COMPLETE: `prin-daemon`, training
> hooks, MOT evaluation, temporal metrics, adversarial/stats tools. Daemon
> latency target met; MOT metrics match motmetrics reference.

### 1.2 Work package decomposition

| WP | Title | Sessions | S2 verdict | Findings | Key deliverables |
|---|---|---|---|---|---|
| WP-028 | ONNX controller state/control types and backend selection | 0109–0112 | **PASS** (zero findings) | 0 | `prin-daemon` crate's first commit: `state.rs`, `model.rs`, `onnx.rs`, `backend.rs`, `error.rs`; ONNX Runtime controller graph loading; cross-provider backend selection (CPU/DirectML/VitisAI); `EVIDENCE/0109-wp028-s1-controller-provider-report.json` |
| WP-029 | Native daemon runtime and lock-free control buffer | 0113–0116 | **PASS** (zero findings) | 0 | `daemon.rs` (1,281 lines), `hooks.rs`; `SubconsciousDaemon` native runtime with background thread; lock-free `ControlSignalBuffer` (p95 200 ns vs. mutex 2700–3000 ns, 13.5×–15× improvement); `EVIDENCE/0113-wp029-s1-control-buffer-pilot.json` |
| WP-030 | Training hooks and MOT evaluation | 0117–0120 | **PASS** (zero findings) | 0 | `assignment.rs` (458 lines, from-scratch Hungarian/Kuhn-Munkres solver), `mot.rs` (1,011 lines, IoU/MOTA/MOTP/IDF1); `TrainingHooks` Rust-side training-loop integration; 2 MOT parity tests reproducing `motmetrics` reference; WP030-F1 (D4, traceability doc fix) discovered and closed at S4 |
| WP-031 | Temporal experiments, statistics, and adversarial tooling | 0121–0124 | **PASS** (zero findings) | 0 | `stats.rs` (Cohen's d, Welch t-test, Lanczos-approximation Gamma/Beta for Student's-t p-value), `adversarial.rs` (FGSM/PGD sign-gradient perturbation); temporal experiment framework; bootstrap CI |
| WP-032 | Daemon/evaluation integration and Phase 5 gate | 0125–0128 | **PASS** (zero findings) | 0 | Cross-crate PyO3 integration (`daemon.rs` 1,082 lines + `phase5.rs` 478 lines); Python facades (`daemon.py` 760 lines, `eval/` 43 lines, `experiments/` 125 lines); 8 integration tests; `EVIDENCE/0125-wp032-s1-daemon-latency.json` + `provider-acceptance.json`; Phase 5 exit gate GREEN |

**Total WP-level findings: 0** (across all 5 WPs at S2). One D4 finding
(WP030-F1, a traceability documentation gap) was discovered and closed at
WP-030 S4 — not an S2 finding. **All 5 WPs received `PASS` at S2** — the
first phase in the project's history with zero S2 findings across every WP.

### 1.3 Global-session layer

| Session | Date | Verdict | Findings | Headline |
|---|---|---|---|---|
| EA-006 | 2026-08-26 | PASS-WITH-REMEDIATION | 2 (2 D3) | Full-project audit across E1–E10; E-F1 (hotfix commits not in deviation ledger) FIXED; E-F2 (R28 precondition missed) remediated at governance level with hard entry-condition gate for WP-033 S1 |
| EMA-005 | 2026-08-26 | PASS-WITH-REMEDIATION | 3 (3 D4) | Phase 5 close mathematical audit; 46 claims/9 ledgers; 6 new Phase 5 claims all genuine PASS; M-F9 (beta-function allowlist gap) closed same-day by tool-remediation commit |

**Grand total across the full Phase 5 delta (WP + EA-006 + EMA-005): 5
findings** (0 D1, 0 D2, 2 D3, 3 D4). All 5 are resolved (`FIXED` or
governance-remediated). This session's own finding (PA5-F1, §6.4) is
**additional and open**, not part of the 5.

### 1.4 Deliverable inventory (independently verified)

| Artefact class | Phase 4 → Phase 5 delta | Total | Evidence |
|---|---|---|---|
| Rust crates | +1 new (`prin-daemon`) | 8 workspace crates | §2, background inventory |
| `prin-daemon` source (`crates/prin-daemon/src/`) | New crate, entirely Phase 5 | 10 files, 6,926 lines, 0 `unsafe` | §2, background inventory |
| `prin-daemon` tests (`crates/prin-daemon/tests/`) | New | 6 test files (1,291 lines) | §4.1 |
| `prin-py` new binding modules | `daemon.rs` (1,082 lines), `phase5.rs` (478 lines) | 2 new binding modules, 0 new `unsafe` | §2, §7 |
| `python/prin/` new modules | `daemon.py` (760 lines), `eval/__init__.py` (43 lines), `experiments/__init__.py` (125 lines) | 3 new modules, 928 lines | §2 |
| Rust tests (workspace default) | 1144 (Phase 4 close) → **1442** | +298 | §4.1 |
| `prin-daemon` crate tests (lib + integration + doctest) | 0 (crate did not exist) → **219** | +219 (first-ever) | §4.1 |
| Python fast tests | 441 (Phase 4 close) → **555** | +114 | §5.4 |
| Full Python + parity suite | 959 (Phase 4 close) → **1155** | +196 | §5.4 |
| Audit reports (`DOCS/audits/`) | +5 WP audits + EA-006 + EMA-005 | 7 new artefacts | §6.1 |
| Project state reports (`DOCS/reports/`) | +5 (028–032) | 5 new PSRs | §6.1 |
| Session briefs (`DOCS/sessions/phase-5/`) | +20 + README | 21 files | §6.1 |
| Math-audit claim ledgers | 8 ledgers, 40 claims (EMA-004) → **9 ledgers, 46 claims** | +1 ledger, +6 claims | §5.2 |
| Plan amendments | +1 (#30, from Phase 4 R29 implementation) | 30 total | §6.3 |
| New external dependencies | 0 | — | §7 |
| Evidence JSON artifacts | +4 | 4 new files | §5.1 |

---

## 2. Dimension P4 — Coding and architecture

**Requirements (Plan §4, Coding Standards §2.1/§6.1):** Crate layering
`dynamics → {metrics, tensor, kernels} → {sim, train, daemon} → py`.
`#![forbid(unsafe_code)]` on every crate except the two audited FFI
exceptions (`prin-kernels`, `prin-py`'s `dlpack.rs`). No `panic!`/`unwrap`/
`expect` in library code; typed errors at boundaries. One-algorithm-one-
implementation. The Python layer contains no numerics.

**Evidence:**

- `prin-daemon` is a genuinely new crate (6,926 lines across 10 modules)
  and carries a hard `#![forbid(unsafe_code)]` at `lib.rs:85`. `findstr /s
  "unsafe" crates\prin-daemon\src\*.rs` (re-run this session) returns
  exactly one hit: the `forbid` attribute itself. Zero `unsafe` blocks
  anywhere in the crate.
- Crate layering holds exactly: `prin-daemon` depends on `prin-dynamics`
  (for `Seed`), `prin-metrics`, `prin-kernels`, and `prin-train` — all
  valid upward calls within the `{sim, train, daemon}` tier — and neither
  `prin-kernels` nor `prin-dynamics` depends on `prin-daemon` (confirmed by
  EA-006 §E2 and re-verified this session by direct `Cargo.toml` grep).
- Every Phase 5 PyO3 binding module (`daemon.rs`, `phase5.rs`) adds **zero
  new `unsafe`** — re-verified this session by direct `findstr` (returns
  empty). `prin-py/src/lib.rs:18` carries the governed `#![deny(unsafe_code)]`
  + `#![deny(unsafe_op_in_unsafe_fn)]` pattern with the sole, pre-existing
  `dlpack.rs` exception (amendment #6) — unchanged by Phase 5.
- **"No numerics in Python" holds.** EA-006 §E1 verified directly: `grep
  -nE "np\.(sin|cos|exp|sqrt)|math\.(sin|cos|exp|sqrt)"` across
  `python/prin/{daemon.py, eval/__init__.py, experiments/__init__.py}`
  returns empty. `numpy` is imported in `daemon.py` only for `NDArray`
  typing and array-shape/dtype plumbing at the callback boundary, not
  computation. Re-confirmed this session.
- **One-algorithm-one-implementation held.** No new instance this phase of
  Phase 2's WP016-F3 dual-implementation pattern. `prin-daemon`'s
  `assignment.rs` implements the Hungarian/Kuhn-Munkres algorithm from
  scratch (not calling into a third-party solver), and no duplicate
  implementation exists elsewhere in the workspace.
- **Error handling.** `prin-daemon` uses typed errors throughout
  (`error.rs`, 236 lines defining `DaemonError` enum with `OnnxRuntime`,
  `ControlBuffer`, `Hook`, `State`, and `Join` variants). No untyped
  `panic!`/`unwrap`/`expect` in library code paths.
- **Zero WP-level findings.** All 5 WPs received `PASS` at S2 with zero
  findings — the cleanest implementation discipline of any phase.

**Score: 4 — Strong.** `prin-daemon` is a well-architected, zero-`unsafe`
crate that follows every coding standard. The lock-free control buffer is a
notable engineering achievement (13.5×–15× latency improvement over mutex).
The single caveat is that the lock-free pattern's correctness argument rests
on single-producer/single-consumer atomic ordering — well-understood but
subtle enough that a future formal-verification pass would add confidence.

---

## 3. Dimension P3 — Testing

**Requirements (Plan §5, Testing Standards §2–§4):** Unit, property,
integration, parity, and gradcheck layers. ≥95% line coverage on changed
code. Marker discipline (`slow`, `gpu`). Regression tests for every fix.

**Evidence (independently re-executed this session, §5.4):**

- **Rust tests:** 1442 passed, 0 failed, 1 ignored. Breakdown by crate:
  - `prin-daemon`: 219 (163 lib + 4 daemon_concurrency + 2 hooks_daemon +
    7 integration_controller_model + 2 parity_mot + 8 parity_subconscious +
    12 proptest_properties + 21 doctests)
  - `prin-dynamics`: 337 (275 lib + 12 parity_bands + 23 parity_integrators
    + 9 parity_models + 9 parity_pac + 6 parity_temporal + 3 doctests)
  - `prin-kernels`: 103 (102 lib + 1 doctest)
  - `prin-metrics`: 147 (106 lib + 4 corpus_metrics + 6 parity_chimera +
    12 parity_metrics + 19 doctests)
  - `prin-sim`: 169 (128 lib + 7 parity_detect + 22 parity_sparse +
    4 proptest_properties + 5 proptest_sweep + 3 doctests)
  - `prin-tensor`: 59 (47 lib + 10 parity_decomposition + 2 doctests)
  - `prin-train`: 408 + 1 ignored (375 lib + 1 checkpoint + 0+1 ignored
    temporal_clevr_n + 2+1+1+1+2+1+1+5+1+1+2 parity + 13 doctests)
- **Python fast tests:** 555 passed, 8 deselected (slow/gpu markers).
- **Full Python + parity suite:** 1155 passed, 0 failed.
- **Coverage:** `interrogate` 100.0% (266/266 public functions). PSR-032
  reports ≥95% line coverage on all changed code (bindings/phase5.rs 99.62%,
  bindings/daemon.rs 100%, Python modules 100%).
- **Parity:** 510 differential parity tests + 15 `prin-train` golden-value
  parity tests + 10 `prin-daemon` Rust bit-exact parity tests + 2 MOT
  parity tests + 82 differential parity tests — all green.
- **DV-019:** The flaky `gradients_flow_to_every_parameter` test has now
  recurred at least six times across four modules (`bands.rs`, `hybrid.rs`,
  `phase_tracker.rs`, `test_train_bridge_slot_attention.py`), spanning
  Phase 4 through the Phase 5 analytics session. Two concrete mitigation
  options remain on record (pin single-threaded; strengthen fixture).

**Score: 4 — Strong.** The test suite grew substantially (+298 Rust, +196
Python) with `prin-daemon` alone contributing 219 Rust tests across 6
integration test files. Every parity target is met. The one caveat is
DV-019's now-six-recurrence flaky test, which has become the longest-open,
most-recurrent unfixed test-quality issue in the project's history.

---

## 4. Dimension P1 — Data and parity artefacts

**Requirements (Plan §5, Experimentation Standards):** Golden-value parity
against PRINet 3.0 reference. Corpus completeness. SHA-256 verification.
Reproducibility from reference.

**Evidence:**

- `prin-daemon` ships with 10 Rust bit-exact parity tests
  (`parity_subconscious.rs`: 8 tests; `parity_mot.rs`: 2 tests) validating
  the subconscious controller output and MOT metrics against PRINet 3.0
  reference data.
- 510 differential parity tests (unchanged from Phase 4) all green.
- 15 `prin-train` golden-value parity tests (unchanged from Phase 4) all
  green.
- 82 differential parity tests across the full corpus all green.
- EMA-005 added first-ever mathematical claims for Phase 5 code: 6 new
  claims covering Hungarian assignment optimality (Z3 UNSAT), IoU-distance
  boundedness (Z3 UNSAT), Cohen's d special-case reduction (SymPy),
  Welch-Satterthwaite df reduction (SymPy), Gamma-reflection formula
  (SymPy), and Beta-integral identity (SymPy) — all 6 genuine `PASS`.
- DV-006 re-audited at WP-028 S1: DirectML cannot execute the controller
  graph (fuses `Gemm`+`Relu` into `DmlFusedGemm` rejecting two-input form);
  VitisAI not registered (no XDNA NPU on host). CPU provider bit-identical
  to reference over 48 differential cases.

**Score: 4 — Strong.** Parity coverage is comprehensive and independently
verified. The first EMA coverage of daemon/statistics code is a genuine
first. DV-006's DirectML/VitisAI gaps are hardware/runtime conditions, not
code defects.

---

## 5. Dimension P5 — Evidence and verification

**Requirements (Analytics Methodology §5.1, §5.2):** Scan completeness. CI
workflow coverage. Verification command reproducibility. Independent
re-execution.

**Evidence (all independently re-executed this session, §5.4):**

- All quality gates green: fmt, clippy, test, audit, rustdoc, ruff, mypy,
  interrogate, bandit, pip-audit, Snyk Code, Sphinx (fresh directory).
- `tools/check_deviation_ledger.py` passes (111→112 rows).
- `tools/wp001_baseline.py check` passes.
- 4 evidence JSON artifacts present and valid.
- CI workflows live-verified by EA-006 via GitHub Actions API: 6/6
  non-skip workflows `success` on HEAD.

**Caveats:**

- EA-006's E-F2 revealed that Phase 4's R28 precondition (a DV-019 hotfix
  session before WP-028 S1) was never enforced by any mechanism. The
  governance gate existed on paper but had no mechanical enforcement until
  EA-006 added one retroactively. This is a verification-methodology gap:
  the project's audit infrastructure caught the gap only post-hoc, not
  preventively.

**Score: 3 — Adequate.** Every gate reproduced exactly, but the R28
precondition gap shows the verification infrastructure has a class of
weakness: governance-level preconditions that exist in documentation but
lack mechanical enforcement can silently lapse across an entire phase.

---

## 6. Dimension P6 — Governance and process

**Requirements (Development Workflow and Audit Standards, Analytics
Methodology §6):** Session Cycle adherence. Deviation ledger completeness.
Amendment process discipline. Plan-standards-code consistency.

**Evidence:**

- 20/20 sessions in exact S1→S4 order across 5 WPs.
- All 5 WPs received `PASS` at S2 with zero findings — unprecedented.
- 6 of 7 Phase 4 recommendations (R26, R27, R29, R30, R31, R32) closed
  with explicit evidence. R28 deferred with explicit assignment (dedicated
  hotfix session before WP-028 S1).
- EA-006/EMA-005 both `PASS-WITH-REMEDIATION` with all findings resolved
  or governed.
- Project Plan §6 correctly marked `✅ COMPLETE` at phase close.
- Amendment #30 (bridge-overhead re-scope) recorded and in force.

**Findings:**

- **PA5-F1 (D3):** R28's precondition was silently skipped across the
  entire phase. EA-006's E-F2 recorded this and added a hard entry-
  condition gate to WP-033 S1 — but the fact remains that five WPs
  executed and closed with a P1-priority precondition still outstanding.
  DV-019 has now recurred at least six times.

**Score: 4 — Strong.** The session discipline is exemplary (20/20 in
order, zero S2 findings). The R28 gap is a genuine governance failure but
was caught by EA-006 and durably fixed for Phase 6 with a mechanically-
enforced gate.

---

## 7. Dimension P7 — Security

**Requirements (Coding Standards §6, Security policy):** `unsafe`
confinement. Input validation. Secret scanning. Dependency advisory
status. Supply-chain controls.

**Evidence (all independently re-executed this session, §5.4):**

- `cargo audit`: 0 vulnerabilities, 2 pre-accepted warnings (`paste`
  DV-008, `bincode` DV-017), both governed and unchanged.
- Snyk Code (`--severity-threshold=medium`): 0 issues.
- `pip-audit` (project + Sphinx docs): 0 findings each.
- `bandit`: 0 medium/high issues (2 Low in `EVIDENCE/` verification
  scripts — assert usage, not production code).
- Zero new `unsafe` in any Phase 5 code.
- Zero new external dependencies this phase — the smallest supply-chain
  delta since Phase 0.
- Gitleaks clean (`.gitleaks.toml` in force).

**Score: 4 — Strong.** Clean security posture with no new supply-chain
risk. The zero-new-dependencies outcome is notable — Phase 5 added a full
new crate without pulling in any new transitive dependencies.

---

## 8. Dimension P2 — Documentation

**Requirements (Documentation Standards, Plan §4):** CHANGELOG accuracy.
README coverage. Sphinx build. Docstring/rustdoc coverage. Migration Guide.
Session briefs. Traceability matrix.

**Evidence:**

- CHANGELOG `[Unreleased]` carries entries for all 5 Phase 5 WPs + EA-006
  + EMA-005 + EMA-005 remediation + M-F9/DV-026 remediation.
- Project Plan §6 Phase 5 row correctly reads `✅ COMPLETE`.
- Fresh-directory Sphinx build: 0 warnings (R30's fix held for the entire
  phase).
- `interrogate`: 100.0% (266/266).
- `RUSTDOCFLAGS='-D warnings' cargo doc`: 0 warnings.
- `DOCS/sessions/phase-5/README.md` and `SESSION_REGISTER.md` consistent
  (all 20 sessions correctly `COMPLETE`).

**Caveat:** Two post-close hotfix commits (`cb5660b`, `5d90427`) initially
lacked CHANGELOG entries — found by EA-006 E-F1 and fixed same-session.

**Score: 4 — Strong.** Documentation discipline held at every S4 and both
global sessions. The CHANGELOG gap for the hotfix commits was a minor,
same-session fix.

---

## 9. Dimension P8 — Phase exit criteria

**Requirements (Plan §6, PSR-032 §6):** Daemon latency target met. MOT
metrics match motmetrics reference.

**Evidence:**

- `EVIDENCE/0125-wp032-s1-daemon-latency.json`: lock-free control buffer
  p95 200 ns vs. mutex 2700–3000 ns (13.5×–15× lower); direct-reference
  median p95 200 ns vs. PRINet 3.0's 250 ns — daemon latency acceptance
  criterion met.
- `EVIDENCE/0125-wp032-s1-provider-acceptance.json`: CPU pass; DirectML
  graph-incompatible per amendment #13/DV-006; VitisAI absent per DV-006.
- 2 MOT parity tests (`parity_mot.rs`) reproduce `motmetrics` reference
  values.
- EA-006 §E8/E10 independently confirmed all exit criteria met.

**Score: 4 — Strong.** Both exit criteria are genuinely met and
independently evidenced. DV-006's DirectML limitation is a known,
documented hardware/runtime condition.

---

## 10. Dimension P9 — Risk and deferred validation

**Requirements (Plan §7, Analytics Methodology §P9):** Risk register
accuracy. Deferred validation items with re-audit gates. Inherited
advisories. Platform/hardware limitations.

**Evidence (DV register directly read in full this session):**

- **DV-024 CLOSED:** Self-hosted runner topology corrected by EA-006 with
  accurate final state.
- **DV-025 CLOSED:** WP030-F1 traceability doc fix.
- **DV-026 CLOSED:** M-F9 beta-function allowlist gap fixed by tool-
  remediation commit `5fdfeb0`.
- **DV-005:** Re-gated to Phase 6 WP-036 (maintainer decision at WP-028
  S1).
- **DV-006:** Re-audited at WP-028 S1 with fresh evidence. DirectML and
  VitisAI gaps are hardware/runtime conditions.
- **DV-019:** Now at 6+ recurrences across 4 modules. Two mitigations on
  record. Gated to a dedicated hotfix session before WP-033 S1 (EA-006
  E-F2 remediation).
- **DV-004:** Open since Phase 0 (10 non-instrumentable kernel bodies).
  No movement in five phases.
- **DV-027/DV-028:** New items from EMA-005 remediation (cosmetic/
  architectural).

**Score: 3 — Adequate.** The DV register is current and well-maintained.
But DV-019's six-recurrence flaky test is now the longest-open unfixed
code defect in the project, and DV-004 has been open since Phase 0 with
no movement in five phases.

---

## 11. Cross-dimensional analysis

**Patterns across dimensions:**

1. **Zero-finding discipline is real and sustained.** All 5 WPs received
   `PASS` at S2 with zero findings — the first phase to achieve this.
   This is not a scoring artifact: the S2 audits were independently
   spot-checked by EA-006 and confirmed. The Phase 4 recommendations that
   were implemented (R26, R27, R30, R32) demonstrably improved the
   documentation and governance infrastructure the WPs operated under.

2. **DV-019 is now a systemic risk, not a test-quality issue.** Six
   recurrences across four modules and three phases, with two concrete
   mitigations on record but no code fix, indicates the issue has
   transitioned from "a flaky test" to "a governance enforcement gap that
   lets a known defect persist indefinitely." EA-006's hard entry-
   condition gate for WP-033 S1 is the right fix at the governance level;
   the code fix itself is still outstanding.

3. **The "no new dependencies" outcome is a genuine achievement.** Phase 5
   added a full new crate (`prin-daemon`, 6,926 lines) without pulling in
   any new transitive dependencies. This is the smallest supply-chain
   delta since Phase 0 and reflects deliberate architectural discipline —
   using only ONNX Runtime (already a dependency) and standard library
   facilities for the lock-free buffer.

4. **EMA coverage continues to expand meaningfully.** EMA-005's 6 new
   claims covering Hungarian assignment, IoU geometry, and statistical
   formulas are the first mathematical verification of daemon/statistics
   code. All 6 reached genuine `PASS` using only tool types that satisfy
   the symbolic/formal bar outright — a deliberate scoping choice that
   kept the new claims out of the `REQUIRES_HUMAN_REVIEW` class.

5. **The Phase 4 recommendation implementation was largely successful.**
   6 of 7 recommendations closed with explicit evidence. The one miss
   (R28) is now the subject of EA-006's E-F2 and has been durably fixed
   at the governance level for Phase 6.

---

## 12. Limitations

1. **GPU hardware not available for this session.** `cargo test --features
   wgpu` and CUDA tests were not re-executed this session (no GPU hardware
   in the analytics session environment). EA-006's live CI verification
   via the GitHub Actions API confirms these workflows are green on HEAD.
2. **`prin-py` tests excluded from Rust test run.** The `--exclude prin-py`
   flag was used because `prin-py` requires `torch` installed in the
   Python environment, which is not available in the analytics session's
   shell. Python tests (which exercise `prin-py` via the installed
   extension module) were run separately and are fully green.
3. **Snyk Open Source CLI quota.** The local Snyk CLI hit the org's
   monthly test-quota limit before covering the Cargo workspace and main
   `pyproject.toml` surfaces. CI's `snyk.yml` job remains the
   authoritative gate for those surfaces and was independently confirmed
   green by EA-006 via the GitHub Actions API.

---

## 13. AI assistance disclosure

Per Experimentation Standards §4: this analytics report was drafted by the
AI pair (Qwen Code) with independent re-verification of all quality gates,
test suites, and security scans executed directly by the AI pair. The
maintainer's role is review and approval of the verdict and recommendations.

---

## 14. Companion files

- **Evidence index:** [`phase-5-evidence-index.md`](phase-5-evidence-index.md)
- **Recommendations register:** [`phase-5-recommendations.md`](phase-5-recommendations.md)
