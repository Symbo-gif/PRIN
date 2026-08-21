---

# PRIN Phase 4 Analytics Report

**Phase:** 4 — Trainable stack and Torch bridge
**Date:** 2026-08-21
**Analyst:** Claude Code (AI pair)
**Maintainer approval:** pending
**Methodology:** [`DOCS/ANALYTICS/ANALYTICS_METHODOLOGY.md`](../ANALYTICS_METHODOLOGY.md)
**Git state:** `main` @ `b93bbaa` (current `HEAD`; one commit past the WP-027 S4 / PSR-027 close; up to date with `origin/main`, working tree clean)
**Phase 4 work-package commit range:** `8bce1a2` (WP-022 S1) → `2552b86` (WP-027 S4, documentation closure, PSR-027, exit gate GREEN) — 46 commits from the Phase 3 recommendation-implementation close (`8d7a6b7`)
**Global-session layer (interleaved before the formal WP-027 S4 close, folded into this assessment):** `48eade3` (WP-027 S3) → `cb2d83c` (EMA-003) → `8b11115`/`29d5e06` (EMA-004) → `2b32e49` (EA-005) → `85b3c79` (EA-005 follow-up: self-hosted Windows CI runner migration) → `2552b86` (WP-027 S4) → `b93bbaa` (README accuracy sweep, current `HEAD`)
**Work packages:** WP-022 through WP-027 (6 cycles, 24 sessions, 0085–0108) + Executive Audit Session 005 (EA-005) + Executive Mathematical Audit Sessions 003 and 004 (EMA-003, EMA-004)
**Phase exit gate:** GREEN (`DOCS/reports/027-project-state.md` §6; independently re-confirmed by EA-005 §E10 and, with one qualification recorded in §8 below, by this session)

---

## Executive summary

Phase 4 — Trainable stack and Torch bridge is **complete**. All six work
packages (WP-022 through WP-027) passed through the full Session Cycle
(S1→S2→S3→S4) in exact order across 24 sessions (0085–0108), delivering
`prin-train` — the project's first Burn-based trainable stack (13,590 lines,
22 source modules, zero `unsafe`) rebuilding PRINet 3.0's `nn/` internals:
trainable bands and resonance primitives (WP-022), inhibition/activations/
Equilibrium Propagation (WP-023), oscillator-aware optimizers SCALR/RIP/
SyncGD (WP-024), a production PyO3/DLPack `torch.autograd.Function` bridge
(WP-025), PhaseTracker/HybridPRINetV2/baselines/adaptive allocation
(WP-026), and the temporal-CLEVR-N integration layer plus Phase 4 exit gate
(WP-027). This is the best first-pass implementation discipline of any phase
to date by S2 verdict: **zero of the six WPs received a `FAIL` verdict**
(Phase 2: 5 of 5; Phase 3: 1 of 5), with 11 WP-level findings total (1 D1, 1
D2, 2 D3, 7 D4) — all resolved (`FIXED` or `AMENDED`). The single D1
(WP022-F3, a `h2` DoS-class supply-chain advisory pulled in transitively by
the new `burn` dependency) was not an S2 finding at all: it was caught the
same day by the CI `audit` job's routine `cargo audit` run, after the WP-022
cycle had already closed, and fixed via a same-day hotfix dependency bump
under the Development Workflow Standards §7 hotfix exception — a genuine,
if narrow, demonstration that the project's automated safety net catches
what a point-in-time audit cannot (an advisory disclosed after the code was
written).

Two **Executive-tier sessions** and two **Executive Mathematical Audit
sessions** closed in the days immediately following WP-027 S3 and are
folded into this assessment. Notably, and unlike every prior phase, this
global-session layer ran **before** WP-027's own formal S4 documentation
closure (`2552b86`) rather than strictly after it — EA-005's own E7
dimension text records "Session 0108 (WP-027 S4) is correctly PLANNED" at
the time of its audit, meaning EA-005 (and both EMA sessions) assessed a
phase that was substantively, but not yet formally, closed.

- **EMA-003** (2026-08-19): the third Executive Mathematical Audit and the
  first to cover the trainable stack — 38 claims across 7 ledgers (28
  carried, zero regressions; 10 new `prin-train` claims). Verdict
  `PASS-WITH-REMEDIATION`: 9 of 10 new claims reached genuine SymPy/Z3
  `PASS`; the tenth (`SCALR-LR-02`) returned `INCONCLUSIVE` on `0**alpha`
  for a symbolic positive `alpha` — a documented `math-audit-mcp` tool
  limitation (M-F8), not a code defect (20/20 numeric samples exact, and
  the Rust implementation's `f64::powf` is correct per IEEE 754).
- **EMA-004** (2026-08-20): a **tool remediation session**, not a
  re-verification pass. Fixed M-F8 at its root cause inside
  `math-audit-mcp`'s own `verify_identity` tool (the tool never promoted a
  claim's declared `"alpha > 0"` premise into a SymPy `Symbol`-level
  assumption, so SymPy's own `0**x → 0` auto-evaluation never fired).
  Separately fixed EMA-001's three-audit-old M-F5 pass-forward item by
  adding genuine numeric reconstruction-value comparison to
  `audit_tensor_contract`, demonstrated against real PRINet-3.0 HOSVD
  reference data (new claim `TCK-01`, residual `7.1e-15` at `1e-10`
  tolerance — first EMA coverage of `prin-tensor`). Added an independent
  PySAT (CNF/CDCL SAT) corroboration channel and gave `math-audit-mcp`
  itself its first-ever git history (closing M-F6). Re-ran the full audit:
  **40 claims across 8 ledgers, 33 PASS, 0 FAIL, 0 INCONCLUSIVE, 7
  `REQUIRES_HUMAN_REVIEW`** (the same by-design policy-gate class carried
  since EMA-001R) — maintainer sign-off freshly re-granted for the full
  current set, including a first-time sign-off for `TCK-01`.
- **EA-005** (2026-08-20): a full-project executive audit across E1–E10,
  verdict `PASS-WITH-REMEDIATION`, 5 findings (E-F1 D2, E-F2/E-F3 D3, E-F4/
  E-F5 D4). E-F1 (a CI-only mypy lint failure — `torch` was never installed
  in the `python.yml` lint job, so bridge-code `# type: ignore` comments
  registered as "unused" once torch's own types became unresolvable) was
  fixed same-session. E-F2 (GitHub-hosted `ubuntu-latest` disk exhaustion)
  and E-F3 (`windows-latest` CubeCL timeout, the DV-016 pattern manifesting
  as an actual failure rather than mere slowness) were external
  infrastructure conditions, passed forward as DV-022/DV-023; DV-023 and
  the underlying DV-016 were both closed the same day by a same-session
  follow-up commit migrating all `windows-latest` CI jobs to a newly
  registered self-hosted `PRIN-GPU-Runner`. E-F4/E-F5 were minor
  documentation-currency gaps (phase-4 session README status mismatch;
  `CHANGELOG.md` missing a WP-027 entry), both fixed same-session.

Independent re-verification during **this** analytics session (2026-08-21,
`HEAD` `b93bbaa`) confirms every mandatory quality, testing, and security
gate is green and reproduces PSR-027/EA-005's figures exactly, with **one
genuine, previously-unreported exception** discovered by this session (§4.2,
finding PA4-F2):

| Gate | Result | Evidence |
|---|---|---|
| `cargo fmt --all -- --check` | Clean | §5.4 |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean | §5.4 |
| `cargo test --workspace -- --test-threads=1` | Exit 0, all crates pass (doctests incl. all 13 `prin-train` doctests); code unchanged since PSR-027/EA-005's independently re-run **1144/1144, 0 failed, 1 ignored** — `HEAD` is one docs-only commit ahead | §5.4 |
| `cargo audit` | 2 pre-accepted advisories (`paste` DV-008, `bincode` DV-017), 0 new | §5.4 |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | Clean, 0 warnings | §5.4 |
| `ruff check` / `ruff format --check` | Clean | §5.4 |
| `mypy python/prin --strict` | Success, 27 files, 0 issues | §5.4 |
| `bandit -r python/prin -c pyproject.toml` | 0 issues | §5.4 |
| `interrogate -c pyproject.toml python/prin` | 100.0% (231/231) — exact match | §5.4 |
| `pytest tests/ -m "not slow and not gpu"` | **441 passed, 8 deselected** — exact match | §5.4 |
| `pytest tests/ parity/` | **959 passed** — exact match | §5.4 |
| `pip-audit .` / `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities (both) | §5.4 |
| `snyk code test --severity-threshold=medium` | 0 issues — exact match to EA-005 | §5.4 |
| **`sphinx-build -W --keep-going -b html` against a fresh output directory** | **Build finished with 12 warnings-as-errors (3 docutils ERRORs + 9 WARNINGs)** — reproduced twice in two independent fresh output directories; **contradicts** PSR-022 through PSR-027's and EA-005's repeated "0 warnings" claims | §4.2, §5.4, new finding **PA4-F2** |

This session's own new findings, per Analytics Methodology principle 7
("no silent overrides"):

- **PA4-F1 (D3):** `DOCS/PRIN_Project_Plan.md` §6's roadmap table still
  shows no completion marker for Phase 4 (`"**4 — Trainable stack + torch
  bridge**"`, no `✅ COMPLETE`), even though PSR-027 §6 declares the exit
  gate GREEN. This is the **third consecutive phase** with this exact
  finding class (Phase 2: PA2-F1/PA2-F2; Phase 3: PA3-F1/PA3-F2, itself
  fixed by Phase 3's own recommendation R21) — and this time it is
  materially different from a pure blind spot: Documentation Standards §7
  item 9, added specifically by R22 to prevent this recurrence, was
  **consulted and correctly triggered** at WP-027 S4 (PSR-027 §8(a)
  explicitly names the gap) but its own imperative text ("explicitly
  verify and, **if stale, update**") was not followed — PSR-027 instead
  recorded the marker as "recommended for the next cycle" and left it
  unset. The very next commit (`b93bbaa`, a five-file README accuracy
  sweep) also did not fix it. Open, unresolved as of this report.
- **PA4-F2 (D2):** The "Sphinx build: 0 warnings" claim, repeated
  identically across every Phase 4 S4/PSR (022 through 027) and EA-005's
  own independent re-run, is an artefact of an incrementally-cached,
  gitignored `DOCS/sphinx/_build/html` directory that every one of those
  sessions reused rather than rebuilding from clean. Sphinx's incremental
  build tracks only `.rst`/`.md` source-file timestamps; it does not detect
  that an `automodule`-pulled Python docstring changed underneath an
  unmodified `.rst` page, so a docstring edit at WP-027 S1 (`ae504ea`,
  `python/prin/__init__.py`'s `Subpackages:` list gained the `prin.train`/
  updated `prin.nn` entries) and a `phase_tracker.TrackingResult`
  re-export at WP-026 (documented once via `prin.nn`'s `automodule` and
  once via its defining submodule) both silently escaped every subsequent
  incremental Sphinx run. A clean build — independently reproduced twice
  this session, in two separate fresh output directories — surfaces **12
  genuine warnings-as-errors** (3 docutils "Unexpected indentation" ERRORs
  and 6 associated "Block quote/Definition list ends without a blank line"
  WARNINGs from the malformed nested-indentation docstring, plus 5
  "duplicate object description" WARNINGs for `TrackingResult`'s
  attributes); re-running the identical command against the pre-existing,
  reused `DOCS/sphinx/_build/html` directory reproduces the false "0
  warnings" result exactly, confirming the cache is the mechanism. This is
  a verification-methodology gap, not a documentation-content gap: the
  Sphinx "clean build" gate has been silently non-functional for the
  entire phase's worth of S4/audit claims that used it. Open, unresolved
  as of this report.

Both are recorded in §6.4/§10 and the Recommendations Register and trigger
the normal Session Cycle remediation process per Analytics Methodology §7;
this analytics session does not fix them.

### Aggregate phase verdict

**PASS — SATISFACTORY**

All nine dimensions score ≥ 3; no dimension scores below 3; four dimensions
(P1, P3, P4, P7) reach 4, but the phase does not clear the `PASS —
EXCELLENT` bar because P2, P5, P6, and P8 each carry a genuine,
evidence-backed caveat this session did not wave away. This is the third
consecutive `PASS — SATISFACTORY` verdict (Phase 2, Phase 3, Phase 4), and
— as with Phase 3 — it reflects real, independently-measured improvement in
some respects (the best first-pass WP discipline of any phase: 0 of 6 `FAIL`
verdicts) sitting alongside genuinely new classes of finding this session
discovered rather than merely re-reading: a third recurrence of the
cross-cutting-document-currency gap (this time with the safeguard correctly
triggering but not being followed through), and a previously-undetected
verification-methodology defect (the Sphinx incremental-cache masking) that
caused a real gate to be misreported as green across the entire phase.

### Dimension scores

| Dimension | Score | Label | One-line justification |
|---|---|---|---|
| P1 Data and parity artefacts | 4 | Strong | Golden-value parity + float64 gradcheck shipped in the same S1 commit for every WP (R15's fix from Phase 2 held for a second full phase); PhaseTracker's registered acceptance threshold independently exceeded (mean IP 1.00000 ≥ 0.99868); first EMA coverage of `prin-train` (40/40 claims genuine evidence) and, via EMA-004, of `prin-tensor`; but DV-005 (CUDA Burn backend) remains entirely unbuilt — the whole trainable stack is CPU-only `NdArray` — and DV-021 (bridge overhead) is an open, unmet target |
| P2 Documentation | 3 | Adequate | CHANGELOG/README/Migration-Guide discipline held at every one of the 6 WP S4s and both EA/EMA sessions (R16's fix, now a third consecutive clean phase on this specific point); but this session's own re-verification found the third consecutive occurrence of the roadmap-marker gap (PA4-F1) — this time with the R22 safeguard correctly flagging it and the session choosing to defer rather than fix a one-line edit |
| P3 Testing | 4 | Strong | 1144 Rust (exit 0, unchanged), 441 Python fast, 959 full py+parity — all independently reproduced this session with zero discrepancy; gradcheck float64 green on every differentiable bridge including the new composed "full gradcheck"; but DV-019 (a genuine, root-caused, still-unfixed flaky test) recurred four times across the phase and now spans three modules |
| P4 Coding and architecture | 4 | Strong | `prin-train` (13,590 lines) carries zero `unsafe` under a hard `#![forbid(unsafe_code)]`; crate layering and "no numerics in Python" hold exactly; the phase's sole D1 was a same-day-fixed dependency CVE, not a first-party defect; but WP025-F1 was a genuine first-party correctness gap (a malformed checkpoint could panic or silently corrupt a trainable layer) |
| P5 Evidence and verification | 3 | Adequate | Nearly every gate this session re-executed reproduced PSR-027/EA-005's figures exactly, including a from-scratch Snyk Code re-run; but this session's own independent re-verification (the methodology's own principle 3) caught PA4-F2 — a real, previously-unreported gate-integrity gap that let a false "0 warnings" claim stand across the entire phase |
| P6 Governance and process | 3 | Adequate | 24/24 sessions in exact S1→S4 order; best-ever first-pass WP discipline (0/6 `FAIL`); 11 WP + 5 EA-005 findings all resolved; but EMA-003 skipped its own required closing-checklist entries (caught only retroactively by EMA-004, the same failure class R16 was built to prevent for global sessions specifically), and PA4-F1 shows a governance checklist item correctly firing without being acted on |
| P7 Security | 4 | Strong | `cargo audit`/Snyk Code/`pip-audit`/`bandit` all clean at governed thresholds, independently re-confirmed; zero new `unsafe`; but Burn's arrival (first use in this repo) brought the phase's only two new supply-chain advisories, including a real DoS-class CVE (`h2`, same-day fixed) — the largest supply-chain delta since Phase 0/1 |
| P8 Phase exit criteria | 3 | Adequate | 2 of 3 Plan §6 exit criteria (PhaseTracker IP, gradcheck) are genuinely met and independently over-confirmed; the third (bridge overhead `<5%`) is honestly and thoroughly evidenced as **not met** (+37.8%/+6.5%, architecturally attributed) but is carried as an open deviation (DV-021) rather than closed by the plan-amendment mechanism the project used for the directly analogous Phase 2 sweep-target case (amendment #21) |
| P9 Risk and deferred validation | 4 | Strong | Every Phase 3 recommendation (R21–R25) tracked to explicit closure before WP-022 S1; DV register is exceptionally current and evidence-cited (directly read in full this session, zero discrepancies); DV-021/DV-005 concretely checkpointed to WP-027 S1 rather than left as vague future-WP placeholders; but DV-019's flaky test has recurred four times with two identified fixes still unscheduled into any concrete session |

---

## 1. Phase 4 scope and deliverables

### 1.1 Planned scope (Project Plan §6, Phase 4)

> Trainable stack + torch bridge: `prin-train`, Python `prin.nn` autograd
> bridges, PhaseTracker, HybridPRINetV2, baselines, ablations.

**Exit criteria (Project Plan §6, PSR-027 §6):** PhaseTracker ≥3.0 IP scores
on temporal CLEVR-N; gradcheck green; bridge overhead <5%.

**Note (PA4-F1, this session):** as of `HEAD` `b93bbaa`, this table row in
`DOCS/PRIN_Project_Plan.md` still carries no completion marker — see the
Executive Summary and §6.4.

### 1.2 Work package decomposition

| WP | Title | Sessions | S2 verdict | Findings | Key deliverables |
|---|---|---|---|---|---|
| WP-022 | Trainable bands and resonance primitives | 0085–0088 | PASS-WITH-FINDINGS → CLEAN | 2 (2 D4) + post-close hotfix (1 D1) | `prin-train`'s first commit: `DiscreteDeltaThetaGamma`, `ResonanceLayer` (Burn `Module`s); first use of `burn` in the repo; GPU CI runner strategy decided (amendment #26) |
| WP-023 | Inhibition, activations, and HEP | 0089–0092 | PASS-WITH-FINDINGS → CLEAN | 1 (D4) | `FeedbackInhibition` (STE top-k WTA), `activations` (`d_silu`, `HolomorphicActivation`, `GatedPhaseActivation`), `HolomorphicEnergy`, `HolomorphicEp` (±β Equilibrium Propagation) |
| WP-024 | Oscillator-aware optimizers | 0093–0096 | PASS-WITH-FINDINGS → CLEAN | 1 (D3) | `SyncGd`, `Rip`, `Scalr` (SCALR/RIP/SyncGD rebuilds); `OscillatorOptimizer` trait; declaration-text drift corrected via amendment #29 |
| WP-025 | Production Torch autograd bridge | 0097–0100 (+S3-exec) | PASS-WITH-FINDINGS → CLEAN | 4 (1 D2, 1 D3, 2 D4) | `PyResonanceLayerBridge`/`PyGatedPhaseActivationBridge` PyO3/DLPack `torch.autograd.Function` bridges; checkpoint shape validation; DV-021 (bridge overhead) opened |
| WP-026 | PhaseTracker, Hybrid, baselines, and allocation | 0101–0104 (+Exec-S1) | PASS-WITH-FINDINGS → CLEAN | 2 (2 D4) | `PhaseTracker`, `HybridPRINetV2`, `SlotAttentionModule` baseline, 4 ablation variants, `AdaptiveOscillatorAllocator`; full PyO3 bridges + `prin.nn` wrappers for all six |
| WP-027 | Trainable-stack integration and Phase 4 gate | 0105–0108 | **PASS** (zero findings) | 0 | Temporal CLEVR-N dataset generator, training losses, Rust-native trainer, optimizer/trainer PyO3 bridges; Phase 4 acceptance-criterion validation; exit gate |

**Total WP-level findings: 11** (1 D1, 1 D2, 2 D3, 7 D4). All resolved
(`FIXED` or `AMENDED`). **0 of 6 WPs received `FAIL`** at S2 — the best
per-WP first-pass trajectory of any phase to date (Phase 1: 0 D1 across 22
findings but with 3 `FAIL` verdicts; Phase 3: 1 of 5 `FAIL`; Phase 2: 5 of
5 `FAIL`).

### 1.3 Global-session layer folded into this assessment

| Session | Date | Verdict | Findings | Headline |
|---|---|---|---|---|
| EMA-003 | 2026-08-19 | PASS-WITH-REMEDIATION | 1 new (M-F8, D3) | First EMA coverage of `prin-train`: 38 claims/7 ledgers, 9/10 new trainable-stack claims genuine PASS; `SCALR-LR-02` INCONCLUSIVE on a tool-level `0**alpha` gap |
| EMA-004 | 2026-08-20 | PASS-WITH-REMEDIATION | 0 new; M-F8/M-F5/M-F6 CLOSED | Tool remediation session: fixed 3 carried-forward tool gaps at root cause, added PySAT corroboration + first-ever git history for `math-audit-mcp`; 40 claims/8 ledgers, 33 PASS/0 FAIL/0 INCONCLUSIVE/7 REQUIRES_HUMAN_REVIEW; fresh maintainer sign-off for all 7 |
| EA-005 | 2026-08-20 | PASS-WITH-REMEDIATION | 5 (1 D2, 2 D3, 2 D4) | Full-project audit across E1–E10; live GitHub Actions API check found 3 genuine CI failures (mypy-missing-torch, disk exhaustion, CubeCL timeout); all local gates green (1144 Rust, 959 Python) |

**Grand total across the full Phase 4 delta (WP + EMA-003 + EA-005): 17
findings** (1 D1, 2 D2, 4 D3, 10 D4). All 17 are resolved (`FIXED`,
`AMENDED`, or passed forward as a governed DV item with a same-day or
same-window closure — DV-023/DV-016 closed the same day via the runner
migration; DV-022 remains open as an external infrastructure condition with
a documented fallback). This session's own two findings (PA4-F1, PA4-F2,
§6.4) are **additional and open**, not part of the 17. One further
governance-hygiene item surfaced during evidence-gathering for this report
(not separately severity-classified, since EMA-004 itself already caught
and fixed it): EMA-003's own commit never added its required
`SESSION_REGISTER.md`/`DEFERRED_VALIDATION_REGISTER.md`/`CHANGELOG.md`
entries at close time — a recurrence, for a global session specifically, of
the same closing-checklist-skip failure mode Phase 2's R16 targeted; see
§6.4.

### 1.4 Deliverable inventory (independently verified)

| Artefact class | Phase 3 → Phase 4 delta | Total | Evidence |
|---|---|---|---|
| Rust crates | +1 new (`prin-train`) | 11 workspace crates | §2, background inventory |
| `prin-train` source (`crates/prin-train/src/`) | New crate, entirely Phase 4 | 22 files, 13,590 lines, 0 `unsafe` | §2, background inventory |
| `prin-train` tests (`crates/prin-train/tests/`, `benches/`) | New | 12 test files (3,746 lines) + 2 bench files | §4.1 |
| `prin-py` new binding modules | `train.rs` (508 lines), `optim.rs`, `trainer.rs`, `train_support.rs`, `{attention,phase_tracker,hybrid,slot_attention,ablation,allocation}.rs` | 12 new binding modules, 0 new `unsafe` | §2, §7 |
| `python/prin/nn/` | New package | 9 files, 2,202 lines | §2, background inventory |
| Rust tests (workspace default) | 821 (Phase 3 close) → **1144** | +323 | §4.1 |
| `prin-train` crate tests (lib + integration + doctest) | 0 (crate did not exist) → **307** | +307 (first-ever) | §4.1 |
| Python fast tests | 306 (Phase 3 close) → **441** | +135 | §4.1 |
| Full Python + parity suite | 816 (306+510, Phase 3 close) → **959** | +143 | §4.1 |
| `prin-train` golden-value parity tests | 0 → **15** | +15 (first-ever) | §4.1 |
| Audit reports (`DOCS/audits/`) | +6 WP audits + EA-005 + EMA-003 + EMA-004 | 9 new artefacts | §6.1 |
| Project state reports (`DOCS/reports/`) | +6 (022–027) | 6 new PSRs | §6.1 |
| Session briefs (`DOCS/sessions/phase-4/`) | +24 + README | 25 files | §6.1 |
| Math-audit claim ledgers | 6 ledgers, 28 claims (EMA-002) → **8 ledgers, 40 claims** | +2 ledgers, +12 claims | §5.2 |
| Plan amendments | +4 (#26–#29) | 29 total | §6.3 |
| New external dependencies | 1 (`burn` — pulling in `cubecl`, `bincode`, transitively `h2`/`reqwest`) | — | §7 |

---

## 2. Dimension P4 — Coding and architecture

**Requirements (Plan §4, Coding Standards §2.1/§6.1):** Crate layering
`dynamics → {metrics, tensor, kernels} → {sim, train, daemon} → py`.
`#![forbid(unsafe_code)]` on every crate except the two audited FFI
exceptions (`prin-kernels`, `prin-py`'s `dlpack.rs`). No `panic!`/`unwrap`/
`expect` in library code; typed errors at boundaries. One-algorithm-one-
implementation. The Python layer contains no numerics; every trainable
op's Torch bridge is a `torch.autograd.Function` with forward **and**
backward calling Rust, boundary crossings batched.

**Evidence:**

- `prin-train` is a genuinely new crate (13,590 lines across 22 modules)
  and carries a hard `#![forbid(unsafe_code)]` at `lib.rs:97` — not the
  governed `#[allow(unsafe_code)]` exception pattern used by `prin-kernels`
  or `prin-py`'s `dlpack.rs`. `grep -rn "unsafe" crates/prin-train/src/`
  (re-run this session) returns exactly one hit: the `forbid` attribute
  itself. Zero `unsafe` blocks anywhere in the crate.
- Crate layering holds exactly: `prin-train` depends on `prin-dynamics`
  (for `Seed`), `prin-metrics`, and `prin-kernels` — all valid upward calls
  within the `{sim, train, daemon}` tier — and neither `prin-kernels` nor
  `prin-dynamics` depends on `prin-train` (confirmed by both this session's
  own grep of `Cargo.toml` dependency graphs and, independently, by EA-005
  §E2).
- Every WP-022..027 PyO3 binding module (`train.rs`, `optim.rs`,
  `trainer.rs`, `train_support.rs`, and the six WP-026 binding modules)
  adds **zero new `unsafe`** — re-verified this session by direct grep
  (`train.rs` mentions "unsafe" only inside doc comments explaining the
  zero-`unsafe` design). `prin-py/src/lib.rs:18` carries the governed
  `#![deny(unsafe_code)]` + `#![deny(unsafe_op_in_unsafe_fn)]` pattern with
  the sole, pre-existing `dlpack.rs` exception (amendment #6) — unchanged
  by Phase 4.
- **"No numerics in Python" holds.** A repository-wide grep for numpy/torch
  math operations inside `python/prin/nn/` and `python/prin/train.py`
  (re-confirmed this session and independently by EA-005 §E2) finds none —
  every differentiable operation is a batched, single-crossing PyO3/DLPack
  call into `prin-train`'s Burn `Module`s. Trainable parameters live in
  Rust and are checkpointed via `rust_state_dict()`/`load_rust_state_dict()`
  (`burn::record` bytes), not `torch.nn.Module.state_dict`.
- **One-algorithm-one-implementation held.** No new instance this phase of
  Phase 2's WP016-F3 pattern (a private reimplementation of an
  already-existing algorithm) was found in either the WP-level audits or
  this session's own review — a second consecutive clean phase on this
  specific architectural rule (Phase 3 was also clean).
- **Torch-bridge design discipline:** every differentiable bridge enforces
  `float64` CPU-contiguous input (matching `gradcheck`'s requirement) and
  crosses the Rust/Python boundary exactly once per call — WP-025's
  `ResonanceLayerBridge`/`GatedPhaseActivationBridge` run the full
  `n_steps` Kuramoto integration inside a single Rust call; backward
  recomputes the forward pass rather than retaining Burn's autodiff graph
  (Burn has no `retain_graph` equivalent), a real design constraint
  discovered and correctly handled during WP-025 S1 (a first design
  attempt failed `gradcheck`'s `retain_graph=True` contract before this
  fix).

**Weaknesses — one D1 dependency vulnerability and one D2 genuine
first-party correctness gap:**

1. **WP022-F3 (D1, not an S2 finding — caught post-close by CI):** the CI
   `rust` workflow's `audit` job discovered `h2` RUSTSEC-2026-0258 (an
   unbounded-empty-DATA-frames DoS) in `h2` 0.4.15, a transitive
   build-time dependency of the newly-added `burn`/`cubecl-cpu` stack
   (`cubecl-cpu → tracel-llvm-bundler → reqwest → hyper → h2`). Fixed the
   same day via `1b7a8e9` (`h2` 0.4.15 → 0.4.16 in `Cargo.lock`); `cargo
   audit` clean at the governed threshold, independently re-confirmed by
   this session's own `cargo audit` run. This is not a WP-022 audit
   finding in the normal S2 sense — it surfaced through routine CI
   scanning after the cycle had formally closed, and was remediated as a
   hotfix under Development Workflow Standards §7, the correct process for
   exactly this situation (a live security finding).
2. **WP025-F1 (D2):** `load_state_dict` validated malformed checkpoint
   *bytes* but not a well-formed record carrying the *wrong tensor shape*
   for the current layer — independently reproduced at S2: a shape
   mismatch on `GatedPhaseActivation` produced an uncaught
   `pyo3_runtime.PanicException`, and on `ResonanceLayer` a misleading,
   unrelated `ValueError`. This is a genuine first-party robustness gap,
   not a dependency issue: a caller loading an incompatible checkpoint
   could panic the process or, in principle, leave a layer in a partially
   corrupted state. Fixed in S3 (commit `7b49e4e`) with
   `ResonanceLayer::validate_shapes`/`GatedPhaseActivation::validate_shapes`
   and a load-into-clone-validate-commit pattern, with 4 new regression
   tests. The identical class of gap (Burn's `Module::load_record` leaving
   plain `usize`/`f64` struct fields completely untouched by a checkpoint
   load, so a first naive `validate_shapes` implementation would compare a
   post-load field to itself and unconditionally pass) was independently
   rediscovered and fixed across all eight WP-026 trainable types before
   it could ship, this time caught by the WP-026 S1 session's own testing
   rather than by a later audit — direct evidence the WP025-F1 lesson
   propagated forward within the phase.

**Score: 4 (Strong).** The architecture — a hard `#![forbid(unsafe_code)]`
on an entirely new 13,590-line crate, exact crate layering, zero Python
numerics, disciplined batched-crossing torch-bridge design — is sound and
extends the standard established since Phase 0 to a materially larger
surface (the largest single-phase crate addition of any phase). The score
is 4 rather than 5 because the phase's sole D1 was a real, if swiftly
remediated, supply-chain vulnerability entering through a newly-added
heavyweight dependency, and WP025-F1 was a genuine first-party correctness
gap at exactly the checkpoint-loading boundary a production bridge most
needs to get right — the same class of "boundary validation gap in
freshly-added, safety-critical code" that kept Phase 3's P4 score at 4
rather than 5 (there, WP017-F1's `unsafe` FFI boundary; here, WP025-F1's
checkpoint-loading boundary).

---

## 3. Dimension P1 — Data and parity artefacts

**Requirements (Plan §5, Testing Standards §2/§3, Development Workflow
Standards §3 S1 exit criteria per R15):** For trainable-stack work, the
parity program's Phase 4-specific instruments are golden-value parity
tests against the actual PRINet 3.0 reference implementation (evaluated in
`torch==2.13.0+cpu` float64) and `torch.autograd.gradcheck` in float64 for
every differentiable bridge. Every S1 session states whether a directly
comparable PRINet 3.0 reference exists and either includes parity evidence
in the same commit or explicitly defers it with a reviewable reason (R15,
Phase 2 recommendation, implemented before WP-017 S1).

**R15's fix held for a full second phase.** Phase 2's dominant failure mode
— three consecutive D1 findings for landing a headline deliverable with
zero differential parity evidence — has no recurrence anywhere in Phase 4:
every one of WP-022 through WP-026's S1 commits shipped golden-value parity
tests against real, independently-evaluated PRINet 3.0 reference values in
the same commit that introduced the primitive (`parity_bands.rs`,
`parity_layers.rs`, `parity_inhibition.rs`, `parity_activations.rs`,
`parity_energy.rs`, `parity_optimizers.rs`, `parity_attention.rs`,
`parity_phase_tracker.rs`, `parity_hybrid.rs` — 15 golden-value cases
total, first-ever for `prin-train`). WP-025 and WP-026's bridges are
additionally gradchecked in float64 for every differentiable entry point
(27 tests at WP-025, 13 differentiable entry points / 86 tests at
WP-026), and WP-027 added a **composed** `full gradcheck`
(`test_composed_encode_evolve_similarity_gradcheck`, chaining
`encode → evolve → phase_similarity` into a single `gradcheck` call) — a
materially stronger claim than per-op gradchecks alone, since it verifies
gradients survive composition through the actual pipeline shape a caller
would use.

**Parity tests caught real bugs, not just documented compliance.** Two
concrete instances this phase (a positive signal that the parity-test
requirement is doing genuine verification work, not merely satisfying a
checklist):

- WP-026's `tests/parity_hybrid.rs` (added to close WP026-F2, a
  process-level "no whole-module parity test exists" finding) revealed
  that `HybridPRINetV2`'s classifier head was missing a `ReLU` between
  linear layers (reference: `Linear→ReLU→Dropout→Linear`; the shipped
  Rust code had `Linear→Linear`) — a genuine numerical/architectural
  defect that component-level parity tests alone had not caught, fixed in
  the same S3 commit (`2135077`) that added the test.
- WP-025's design bug (a single-use backward context failing
  `gradcheck`'s `retain_graph=True` contract, §2 above) was caught by the
  gradcheck requirement itself during S1, before the flawed design shipped
  at all.

**PhaseTracker acceptance criterion, independently re-confirmed:** the
registered PRINet 3.0 comparator (`y4q1_7_statistical_summary.json`, mean
IP **0.99868**, per-seed `[1.0, 1.0, 0.99605]` at seeds 42/123/456) is
exceeded by PRIN's reproduction (`0105-wp027-temporal-clevr-n-validation.json`,
mean IP **1.00000**, per-seed `[1.0, 1.0, 1.0]`, wall time 115.62s) — this
session did not re-execute the `#[ignore]`d ~115-second integration test
itself (methodology principle 3's re-execution scope this session focused
on the mandatory fast-gate suite; see §4.1's limitation note), but
independently confirmed the recorded evidence artefact and its citation
chain are internally consistent across `DOCS/experiments/`,
`DOCS/audits/027-wp027-audit.md`, and PSR-027.

**First EMA coverage of the trainable stack, and of `prin-tensor`.**
EMA-003/EMA-004 (§1.3) independently, tool-executed re-derived 10 new
`prin-train` mathematical claims (Hungarian-loss entropy identity, dSiLU
derivative, SCALR lr-scale boundary behaviors, RIP Hebbian equilibrium,
SyncGd penalty gradient, 4 Z3-proved bound/non-negativity/diagonal
invariants) — 10/10 reached genuine SymPy/Z3 `PASS` after EMA-004's M-F8
fix — and, via the same remediation session, EMA-004 closed a
three-audit-old tool-coverage gap (M-F5) by adding real numeric
reconstruction-value verification and demonstrating it against
`prin-tensor`'s existing PRINet-3.0 HOSVD reference fixture (residual
`7.1e-15` at `1e-10`), the first EMA coverage of that crate.

**Score: 4 (Strong).** Comprehensive, real-bug-catching parity/gradcheck
discipline held across an entire phase for the first time, extended by
first-ever tool-executed mathematical verification of the trainable stack.
The score is 4 rather than 5 because two structural gaps remain genuinely
open, not merely deferred on paper: **DV-005** — the entire trainable
stack's Burn backend is CPU-only `NdArray` (`Cargo.toml`:
`features = ["std", "ndarray", "autodiff"]`, no `burn-cuda`/`burn-wgpu`
anywhere in the workspace), so despite this being the phase whose Plan §6
text names "Torch bridge," no CUDA execution path exists for any trainable
component, and WP-027 S1's own recorded recommendation is to *not* pull a
CUDA Burn backend into near-term Phase 5 scope absent a concrete workload —
and **DV-021** — the bridge-overhead performance target genuinely was not
met at the shape sizes measured (§8).

---

## 4. Dimensions P2, P3 — Documentation and testing

### 4.1 Testing (P3)

**Independently re-verified this session (2026-08-21, `HEAD` `b93bbaa`):**

```text
cargo fmt --all -- --check                                 → clean
cargo clippy --workspace --all-targets -- -D warnings       → clean
cargo test --workspace -- --test-threads=1                  → exit 0, all crates pass
                                                                 (incl. all 13 prin-train doctests, all ok)
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps   → clean, 0 warnings
pytest tests/ -m "not slow and not gpu"                      → 441 passed, 8 deselected
pytest tests/ parity/                                        → 959 passed
```

Every reproducible figure is an **exact match** to PSR-027's and EA-005's
claims, independently re-executed rather than re-read. This session's
`cargo test --workspace` run confirms exit 0 (no failures) rather than a
literal re-derived pass count, because the command's output was inspected
per-crate rather than via a single aggregate line (Cargo does not print
one); the working tree is clean and `HEAD` (`b93bbaa`) is exactly one
docs-only commit (5 README files) past PSR-027's own close, so the
1144/1144 figure PSR-027 and EA-005 both independently recorded is
necessarily unchanged. Coverage on touched code, cited from PSR-022
through PSR-027 (not independently re-derived this session — `cargo
llvm-cov` was not re-run, a stated limitation): every new `prin-train`
source file lands at ≥95% lines across all six WPs, with several at
97–100% (e.g. `losses.rs` 100%/97.71%/100%, `feedback.rs` 100%/100%/100%);
Python `prin/nn/` reaches 100% (372/372 statements) by WP-026's close.

**Limitation stated (Analytics Methodology principle 4):** this session did
not independently re-run `cargo llvm-cov`, the `#[ignore]`d
`integration_temporal_clevr_n` acceptance test (~115s), or the criterion
benchmark suites (`resonance_layer_bridge.rs`, `phase_tracker_bridge.rs`) —
all three are cited from the recorded PSR/audit evidence rather than
re-derived. This is a narrower re-execution scope than Phase 3's session
achieved (which had hardware GPU tests to re-run); nothing in this phase's
deliverables requires GPU hardware, so the narrowing is a time-budget
choice, not a hardware-access limitation.

**DV-019, a genuine, recurring, non-blocking flaky test.**
`prin-train::bands::tests::gradients_flow_to_every_parameter` is
intermittently flaky under high parallel test-thread contention — first
discovered at WP-023 S1 (thread contention from newly-added test files),
recurred at WP-024 S1, recurred a third time at the WP-025 S3-exec session
(root-caused to `bands.rs:801`'s `w_gamma` gradient-presence assertion
sitting on a documented "knife-edge" gradient value that Burn's autodiff
graph optimizer occasionally prunes entirely under certain thread-pool
summation orderings), and WP-027 S1 recorded a **fourth** recurrence,
newly affecting `hybrid.rs` and `phase_tracker.rs` in addition to
`bands.rs` — three modules now affected. Two concrete, low-risk mitigation
options are on record (pin the test single-threaded; strengthen the
fixture so the gradient is robustly bounded away from zero) but neither
has been implemented; per Development Workflow Standards §3, `bands.rs` is
WP-022's closed, frozen scope, so no later WP has fixed it in passing —
correctly, since a drive-by patch to frozen scope would itself be a
process violation, but the item has also not yet been assigned to a
dedicated governed hotfix/correction session (§9, Recommendation R28).

**Score: 4 (Strong).** Every test class this project runs on this
platform — default Rust (including a first-ever 13,590-line crate at zero
regressions), Python fast, full Python + parity — is green and was
independently re-verified this session with zero discrepancy from the
recorded claims; gradcheck coverage (including the new composed variant)
is comprehensive. Not a 5: DV-019 is a real, recurring, still-unfixed test
defect (four occurrences, now three affected modules) that the phase's own
governance correctly declined to patch opportunistically but has also not
yet concretely scheduled, and the `cargo llvm-cov`/GPU-adjacent re-runs
this session skipped (a time-budget choice, stated as a limitation rather
than silently omitted) keep the reproduction slightly narrower than Phase
3's.

### 4.2 Documentation (P2)

**What held from Phase 2/3's R16/R22 fixes:** every one of Phase 4's 6 WP
S4 sessions and both global-session families (EMA-003/004, EA-005) carries
a substantive `CHANGELOG.md [Unreleased]` entry citing its audit report
path, verdict, and finding disposition inline (R16's fix, now clean for a
third consecutive phase); `crates/prin-train/README.md`,
`DOCS/sphinx/migration_guide.rst`, and `DOCS/sessions/phase-4/README.md`
were all independently spot-checked this session and found current against
the actual delivered scope.

**But this session found two genuinely new instances of documentation- and
evidence-integrity gaps, one a direct recurrence and one a novel class:**

1. **PA4-F1 (D3, recurrence):** the Project Plan §6 roadmap-table
   completion marker for Phase 4 is still unset (§6.4 below has the full
   detail on why this is a materially different instance of the same
   pattern than Phases 2/3's — the safeguard fired correctly this time and
   was overridden by a deferral decision rather than never consulted).
2. **PA4-F2 (D2, novel):** the Sphinx "0 warnings" claim is false on a
   clean build (§4.1's testing evidence and the Executive Summary have the
   full technical detail). This is filed under Documentation because its
   symptom is a docs-build gate, but its root cause — a stale, gitignored,
   never-cleaned local build-cache directory silently suppressing
   `autodoc`-sourced warnings across every session that reused it — is
   equally a P5 (Evidence and verification) concern; both dimensions'
   scores reflect it.

**Score: 3 (Adequate).** The R16/R22 mechanisms continue to work precisely
within the scope they were built for — CHANGELOG currency for every WP and
global session, and per-WP README/Migration-Guide accuracy, are both
clean. The score is 3, not 4, because this session's own independent
verification — not any S4 checklist, not EA-005's own E5/E7 dimensions —
caught two real documentation/evidence-integrity gaps this cycle, one of
them (PA4-F2) a previously entirely unknown-to-the-project class of gap
(a false "gate green" claim silently repeated by every session that
reused it) and the other (PA4-F1) showing that even a correctly-triggering
safeguard can still be overridden by a same-session decision to defer
rather than fix a one-line edit.

---

## 5. Dimension P5 — Evidence and verification

### 5.1 Scan completeness

| Scan | Tool | Result | Evidence |
|---|---|---|---|
| Rust advisories | `cargo audit` | 0 vulnerabilities; 2 allowed advisories (`paste` DV-008 amendment #9, `bincode` DV-017 amendment #27) | §5.4, independently re-run |
| Python advisories | `pip-audit .` + `pip-audit -r DOCS/sphinx/requirements.txt` | 0 vulnerabilities (both) | §5.4, independently re-run |
| Python security | `bandit -r python/prin -c pyproject.toml` | 0 issues | §5.4, independently re-run |
| Snyk Code | `snyk code test --severity-threshold=medium` (CLI `v1.1306.2`, org `symbo-gif`) | 0 issues — independently re-run this session, exact match to EA-005 | §5.4 |
| Snyk Open Source | Not independently re-run this session (structurally unsupported for Cargo per the standing WP-001/R23 disposition; Python side covered by `pip-audit`) | Consistent with every prior phase's posture | §5.3 |
| Secret scanning | Gitleaks substitute (amendment #5) | Active; GitHub native still unavailable (DV-009, re-checked WP-025 S3-exec) | Deferred Validation Register |

### 5.2 EMA-003/EMA-004 as the strongest evidentiary strengthening to date

Combined, the two Phase 4 mathematical-audit sessions did more than extend
coverage — EMA-004 is the first EMA session whose primary mandate was
**fixing the audit tool itself** rather than re-running it, and it
succeeded on two of its three targeted tool gaps (M-F8, M-F5) with
before/after evidence: `SCALR-LR-02` moved from `INCONCLUSIVE` to a
genuine SymPy symbolic `PASS` by promoting a claim's own already-declared
premise into a form SymPy's auto-evaluation could use (not by re-scoping
the claim to dodge the gap), and `audit_tensor_contract` gained a real
numeric-reconstruction-value check demonstrated against genuine
already-collected reference data (`TCK-01`, first EMA coverage of
`prin-tensor`). A third capability (PySAT, an independent CNF/CDCL SAT
solver family) was added and immediately used for real corroborating
evidence (`GRA-01-SAT`), and the tool itself gained its first-ever git
history (M-F6), closing a provenance gap that had persisted across three
consecutive EMA sessions (EMA-001→EMA-003) as an unattributable, session-
to-session-changing SHA-256 content hash. **Zero regressions** across every
claim carried forward — direct evidence the phase's new `prin-train`
mathematics did not disturb any previously-verified invariant.

### 5.3 Limitations stated

Per Analytics Methodology principle 4:

- Snyk Open Source (Cargo) was not independently re-run — structurally
  unsupported since WP-001 (R23's standing disposition; `cargo audit`
  remains the authoritative Rust dependency gate).
- `cargo llvm-cov`, the `#[ignore]`d ~115-second temporal CLEVR-N
  integration acceptance test, and both criterion benchmark suites were
  not independently re-run this session (§4.1) — cited from PSR-022
  through PSR-027 rather than re-derived.
- Per Analytics Methodology §5.1 item 11 (as amended by Phase 3's R23
  disposition), the Snyk-CLI-only posture is intentional and permanent
  per maintainer decision (2026-08-18); this is no longer a standing
  escalation and Snyk MCP availability was not re-checked this session,
  consistent with that closed disposition.

### 5.4 Independent re-verification (this session, 2026-08-21)

All commands executed on Windows, Python 3.14.0, Rust 1.92.0, against
`HEAD` `b93bbaa`.

| Command | Result |
|---|---|
| `cargo fmt --all -- --check` | Clean |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean |
| `cargo test --workspace -- --test-threads=1` | Exit 0, all crates pass (incl. all 13 `prin-train` doctests) |
| `cargo audit` | 2 allowed advisories (`paste`, `bincode`), 0 new |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | Clean, 0 warnings |
| `ruff check python/ tests/ benchmarks/ tools/ parity/` | Clean |
| `mypy python/prin --strict` | Success, 27 files, 0 issues |
| `bandit -r python/prin -c pyproject.toml` | 0 issues |
| `interrogate -c pyproject.toml python/prin` | 100.0% (231/231) |
| `pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp_analytics` | 441 passed, 8 deselected |
| `pytest tests/ parity/ --basetemp=.pytest_basetemp_analytics_full` | 959 passed |
| `pip-audit .` | No known vulnerabilities |
| `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities |
| `snyk code test --severity-threshold=medium` | 0 issues |
| `sphinx-build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html` (reused, pre-existing output dir) | Reports 0 warnings — **reproduces the false claim** |
| `sphinx-build -W --keep-going -b html DOCS/sphinx <fresh output dir>` (×2, independent fresh dirs) | **12 warnings-as-errors both times** — exit 1; see PA4-F2 |

**Zero discrepancies against PSR-027 or EA-005's claims for every gate
except the Sphinx build**, where this session's own re-verification
(deliberately run against both a fresh and the pre-existing output
directory to isolate the cause) is the discrepancy — documented as PA4-F2
above and in §6.4, not glossed over.

**Score: 3 (Adequate).** The overwhelming majority of gates this session
re-executed reproduced the recorded claims exactly, including a genuine
from-scratch Snyk Code re-run and the largest independent Rust test-suite
re-verification of any phase to date by absolute test count. The score is
3 rather than 4 because this session's own re-verification — exercising
exactly the "independent verification" principle the methodology names as
its third scientific-integrity rule — surfaced a real, previously
undetected gate-integrity defect (PA4-F2) that had let a false "clean
docs build" claim stand across every S4 and audit session in the phase;
finding it is the methodology working as intended, but its existence is a
genuine evidentiary weakness, not merely a documentation nit.

---

## 6. Dimension P6 — Governance and process

### 6.1 Session Cycle adherence

**24/24 Phase-4 sessions completed** in exact S1→S2→S3→S4 order across 6
WPs, independently confirmed against `DOCS/sessions/SESSION_REGISTER.md`
(rows for sessions 0085–0108, all `COMPLETE`) and
`DOCS/sessions/phase-4/README.md` (both consistent, no discrepancies found
by this session — E-F4's session-0105–0107 status mismatch, found and
fixed by EA-005 before this session began, is confirmed durably fixed).
Global sessions EMA-003, EMA-004, and EA-005 are correctly recorded in the
dedicated "Global sessions" register sections per amendment #15's
precedent, outside the planned 0001–0198 sequence. Two secondary executive
sessions (WP-025 S3-exec, Exec-WP-026 S1) ran with explicit maintainer-
authorized added scope inside their parent WP's cycle, correctly recorded
as such rather than silently folded into the numbered S1–S4 sessions.

### 6.2 Deviation ledger

**11 WP-level findings across 6 audits, plus 5 EA-005 findings, plus 1
EMA-003 finding — 17 total. All 17 resolved** (`FIXED`, `AMENDED`, or
closed the same window as a governed DV item).

| Source | D1 | D2 | D3 | D4 | Total |
|---|---|---|---|---|---|
| WP-022 | 1* | 0 | 0 | 2 | 3 |
| WP-023 | 0 | 0 | 0 | 1 | 1 |
| WP-024 | 0 | 0 | 1 | 0 | 1 |
| WP-025 | 0 | 1 | 1 | 2 | 4 |
| WP-026 | 0 | 0 | 0 | 2 | 2 |
| WP-027 | 0 | 0 | 0 | 0 | 0 |
| **WP subtotal** | **1** | **1** | **2** | **7** | **11** |
| EA-005 | 0 | 1 | 2 | 2 | 5 |
| EMA-003 | 0 | 0 | 1 | 0 | 1 |
| **Grand total** | **1** | **2** | **5** | **9** | **17** |

*WP022-F3 (D1) was caught post-close by CI, not by the S2 audit — see §2.

**This session's own findings (open, not in the 17 above):** PA4-F1 (D3),
PA4-F2 (D2).

**Trend vs. Phase 3:** Phase 3 raised 8 WP findings with 1 D1 (1 of 5 WPs
`FAIL`). Phase 4 raised 11 WP findings with 1 D1 (0 of 6 WPs `FAIL`) —
slightly more findings in absolute count (reflecting a materially larger
delivered surface: an entirely new 13,590-line crate plus a
production-grade Torch bridge, versus Phase 3's deepening of two existing
crates), but the best per-WP pass/fail trajectory yet, and every finding
this phase resolved cleanly with no second-round carry.

### 6.3 Plan amendments (Phase 4)

**Four new plan amendments this phase** (#26–#29), the most of any phase
since Phase 2 (#18–#25, eight):

- **#26** (WP-022 S1): GPU CI runner strategy — self-hosted, closing Phase
  3's R24 at its assigned checkpoint.
- **#27** (WP-022 S3): formal threat-assessment acceptance of the
  `bincode` RUSTSEC-2025-0141 advisory (DV-017), same disposition class
  and cadence as amendment #9 (`paste`).
- **#28** (WP-022 S4): the push/CI cadence change — S1–S3 commit locally
  only, S4 is the sole push/CI trigger per cycle.
- **#29** (WP-024 S3): formal correction of PSR-023 §7's WP-024
  declaration text (`PhaseAdam`/`KuramotoOptimizer`, which never existed
  in the PRINet 3.0 reference) to read as the delivered, reference-
  verified `SCALR`/`RIP`/`SyncGD` scope.

Independently confirmed against `DOCS/PRIN_Project_Plan.md` §8.3, whose
amendment log ends at #29, matching PSR-027 §4's own statement that
"Amendments #1–#29 remain in force. No new amendment was required this
[final Phase 4] cycle." Amendment #29 is the fourth consecutive-phase
instance of the same declaration-text-drift pattern (amendments #18–#20 in
Phase 2, #29 here) — a session brief's actual mission text and the
Rebuild Planning Document's normative mapping are the ground truth,
correctly followed by S1 each time; the drift is consistently in a
previous cycle's *own PSR* paraphrasing the next WP's declaration
inaccurately, not in the delivered code. This recurring, low-severity,
always-caught-and-corrected pattern is addressed by Recommendation R27.

### 6.4 A structural gap this session confirms is not yet closed, and one novel gap this session found

**PA4-F1 shows the R22 safeguard firing correctly but being overridden.**
Documentation Standards §7 item 9 (added by Phase 3's R22, specifically to
prevent a third occurrence of the Project-Plan-roadmap-marker gap) *was*
consulted at WP-027 S4: PSR-027 §8(a) explicitly names the requirement and
states "Phase 4 is the sixth roadmap phase. The plan's roadmap table
should mark Phase 4 as complete." — a materially different outcome than
Phase 2/3's total blind spot, since the safeguard genuinely triggered. But
the session then chose to defer the one-line edit ("recommended for the
next cycle... the substantive engineering work is complete regardless of
the marker's presence") rather than follow the checklist item's own
imperative text ("explicitly verify and, **if stale, update**"). This is a
distinct and, in one sense, more concerning failure mode than Phase 2/3's:
those were oversights the checklist item did not yet exist to catch; this
is a checklist item correctly identifying the gap and then not being acted
on in the same session that found it.

**A novel governance-hygiene gap, caught and fixed within the phase
itself:** while gathering evidence for this report, EMA-003's own closing
commit (`cb2d83c`) was found to have never added its own required
`SESSION_REGISTER.md`/`DEFERRED_VALIDATION_REGISTER.md`/`CHANGELOG.md`
entries — the exact same closing-checklist-skip failure mode Phase 2's R16
was built to prevent for global sessions specifically
(`Executive_Mathematical_Audit_Governance_and_Methodology.md` §8's closing
checklist). This is not left as a new finding of this analytics session
because it was already caught and fully remediated **inside the phase**,
by the very next global session (EMA-004), which added the missing entries
retroactively as part of its own closing pass — a genuine, positive
self-correction, but one worth naming here because it shows the R16
safeguard, like R22's, can still be skipped by the exact session type it
was built to constrain, and was caught only by the next session of the
same type rather than by any WP-N cycle's own checklist (which is not
scoped to global-session artefacts at all).

**Score: 3 (Adequate).** 24/24 sessions in correct order; the best-ever
per-WP first-pass discipline (0/6 `FAIL`); all 17 findings across the WP
and global-session layers resolved cleanly with zero second-round carries;
four plan amendments correctly and transparently recorded. Not a 4: this
phase produced two concrete, evidence-backed instances (PA4-F1's
override-after-correct-trigger, and EMA-003's self-corrected closing-
checklist skip) showing that the project's checklist-based safeguards —
even when they demonstrably work as designed — remain only as reliable as
each session's decision to act on what they surface, a genuine and
recurring governance risk class this report names explicitly rather than
treating as resolved because the specific instances happened to be caught.

---

## 7. Dimension P7 — Security

### 7.1 `unsafe` confinement

No new architectural `unsafe` exposure this phase, despite the largest
single-phase source-code addition of any phase to date (13,590 new lines
in `prin-train` alone). `prin-train` carries a hard
`#![forbid(unsafe_code)]` with zero exceptions — a stricter posture than
`prin-kernels`/`prin-py`'s governed-exception pattern, and correctly so,
since nothing in the trainable stack requires FFI. Every new `prin-py`
binding module (§2) adds zero `unsafe`, confirmed by this session's own
grep and independently by EA-005 §E2. The pre-existing governed exceptions
(`prin-kernels`'s kernel-FFI modules, `prin-py`'s `dlpack.rs`) are
unchanged.

### 7.2 Input validation

New typed-error surface added this phase: `TrainError` (`prin-train`, 8
variants across WP-022/WP-023/WP-024 including `EmptyBand`,
`ShapeMismatch`, `InvalidK`, `DivisionByZero`, `StepLimitExceeded`,
`BetaTooSmall`, plus 8 optimizer-specific variants at WP-024 —
`InvalidLearningRate`, `InvalidMomentum`, `InvalidWeightDecay`,
`InvalidSyncPenalty`, `InvalidCriticalOrder`, `InvalidTargetAmplitude`,
`InvalidRMin`, `InvalidAlpha`); `TrainError::StrategyMismatch` (WP-026,
closing WP026-F1, detecting a Rule-vs-Learned allocator-checkpoint
mismatch that previously silently discarded a checkpoint load with no
diagnostic). `ResonanceLayer::validate_shapes`/
`GatedPhaseActivation::validate_shapes` and their propagation to all eight
WP-026 trainable types (§2) close the WP025-F1 checkpoint-shape-validation
gap comprehensively, not just at the two types where it was first found.

### 7.3 Dependency security

- `cargo audit` (independently re-run this session): 0 vulnerabilities, 2
  allowed advisories — the pre-existing `paste` RUSTSEC-2024-0436
  (amendment #9, unchanged since WP-004) and the phase's new `bincode`
  RUSTSEC-2025-0141 (amendment #27, formally governed at WP-022 S3 with a
  full Coding Standards §6.2 threat assessment: informational-only,
  no CVE, no exploit/affected-API disclosure, compensating control is the
  existing `record_roundtrip_preserves_parameters` regression coverage).
- `pip-audit` (project + Sphinx requirements, both independently re-run):
  0 vulnerabilities.
- `bandit` (independently re-run): 0 issues.
- Snyk Code (independently re-run this session, CLI `v1.1306.2`): 0
  issues at the governed medium-threshold gate — exact match to EA-005.
- **The phase's only genuinely new supply-chain risk event:** the
  transient `h2` RUSTSEC-2026-0258 DoS advisory (§2), introduced
  transitively by `burn`/`cubecl-cpu`'s build toolchain, caught by
  routine CI scanning the same day it could have shipped, fixed via a
  version bump. `burn` is this phase's sole new direct external
  dependency — the largest single-dependency supply-chain delta of any
  phase since Phase 0/1 (Phase 3 added zero new external dependencies).

### 7.4 Secret scanning

Gitleaks substitute (amendment #5) remains in force; GitHub native secret
scanning remains unavailable (DV-009, re-checked at the WP-025 S3-exec
session — `404 disabled` for this private repository — per Phase 1
recommendation R11's ongoing cadence).

**Score: 4 (Strong).** Every dependency and static-analysis scan is clean
at its governed threshold, independently re-confirmed including a
from-scratch Snyk Code run; zero new `unsafe` anywhere despite the
phase's large new-code surface; the checkpoint-validation gap class
(WP025-F1) was fixed comprehensively, not just at its first discovery
site. Not a 5: `burn`'s arrival brought the phase's only two new
supply-chain advisories, one of them a real (if swiftly closed) DoS-class
CVE — evidence that a large new dependency materially raises the attack
surface, exactly as the risk register anticipated when Burn was first
introduced (Project Plan §4.3 risk register #5), and the phase's security
posture, while clean at every measured point, has not yet had a
full-cycle CVE-free track record the way Phase 3's zero-new-dependency
delta did.

---

## 8. Dimension P8 — Phase exit criteria

### 8.1 Exit gate

The Phase 4 exit gate is declared **GREEN** per
`DOCS/reports/027-project-state.md` §6, independently re-confirmed by
EA-005's E10 dimension ("Phase 4 (WP-022..027) substantively complete").
This session's own assessment of the three explicit Plan §6 criteria:

| Criterion | Evidence | Verdict |
|---|---|---|
| PhaseTracker ≥3.0 IP scores on temporal CLEVR-N | Registered PRINet 3.0 threshold (mean IP 0.99868) exceeded by PRIN's reproduction (mean IP **1.00000**, per-seed `[1.0, 1.0, 1.0]`, 3 seeds); citation chain internally consistent across `DOCS/experiments/0105-wp027-temporal-clevr-n-validation.json`, `DOCS/audits/027-wp027-audit.md`, and PSR-027 (this session's independent-verification scope did not re-execute the underlying `#[ignore]`d ~115s test itself — §4.1 limitation) | **GREEN** |
| gradcheck green | Every differentiable bridge (`ResonanceLayer`, `GatedPhaseActivation`, `OscillatoryAttention`, `PhaseTracker`, `HybridPRINetV2`, `SlotAttentionModule`/`TemporalSlotAttentionMOT`, all four ablation variants) passes `torch.autograd.gradcheck` in float64, including the new WP-027 composed `encode → evolve → phase_similarity` full-pipeline gradcheck; independently confirmed present and passing via this session's `pytest tests/ -m "not slow and not gpu"` re-run (441/441, exact match, includes the gradcheck-marked test files) | **GREEN** |
| Bridge overhead <5% | **Not met.** WP-025 S3's rigorous 5-run process-level median-of-medians measurement: small shape (`small_32osc_16dims_8batch`) **+39.8%** overhead, moderate shape **+5.3%** (marginally over). A same-window performance-engineering attempt (WP-025 S3-exec, commit `e720a24`) genuinely fixed a redundant Tensor→data round-trip but only marginally moved the figures (+40.6%/+4.5%) — confirmed architectural (Python-side `torch.autograd.Function.apply()`/`from_dlpack()` fixed dispatch cost, not reachable from the Rust side without abandoning the mandated bridge architecture), not an unfixed oversight. WP-027 S1 independently re-corroborated with fresh measurements: **+37.8%/+6.5%**. Recorded and carried as **DV-021**, OPEN, not amended | **NOT MET — carried as an open, governed deviation, not a closed criterion** |

**Phase 4 exit-gate verdict, as stated by PSR-027:** GREEN, on the basis
that "All acceptance criteria met **or governed by existing deviations**."
This session's independent assessment agrees the underlying evidence is
complete, honestly reported, and not spun — DV-021's numbers appear
identically and prominently in the WP-025 audit, the WP-027 CHANGELOG
entry, PSR-027 §5, and the Deferred Validation Register, with no
softer or rounder figure substituted anywhere. But read strictly against
Plan §6's own text ("bridge overhead <5%," no qualifying language), one of
three explicit exit criteria is not met, by a wide margin at the small-
shape case (+37.8%, roughly 7.5× the stated target) — and unlike the
directly comparable Phase 2 precedent, where an unmet original performance
target (the ≥8×/16-core sweep-speedup figure) was resolved by a formal
plan amendment (#21) that re-scoped the Plan's own text to hardware-
evidenced values before the phase closed, DV-021 has not been closed by
any amendment revising or accepting Plan §6's "<5%" language — it remains
an open deviation sitting alongside a "GREEN" declaration.

### 8.2 Deferred and carried-forward scope

| Item | Origin | Disposition |
|---|---|---|
| CUDA Burn backend / DV-005 (CUDA DLPack full validation) | WP-003 (amendment #7), checkpointed to WP-027 S1 | OPEN — WP-027 S1 recorded a concrete recommendation: do not pull into near-term Phase 5 scope absent a concrete workload that needs it |
| Bridge overhead `<5%` / DV-021 | WP-025 S2/S3, checkpointed to WP-027 S1 | OPEN — see §8.1; independently re-corroborated three times (S3, S3-exec, WP-027 S1), consistently architectural, consistently unmet |
| `burn-tensor` `sigmoid` f32 precision floor / DV-018 | WP-023 | OPEN — documented, non-blocking third-party library behavior; accommodated via `eps=1e-4`/`rtol=1e-6` where it matters |
| Flaky `gradients_flow_to_every_parameter` test / DV-019 | WP-023, recurred ×4 through WP-027 S1 | OPEN — non-blocking; two candidate fixes identified, unscheduled (§9, R28) |

**Score: 3 (Adequate).** Two of the three explicit exit criteria are
genuinely met and, in PhaseTracker's case, exceeded with strong,
independently-consistent evidence. The score is 3, not 4, because the
third criterion is honestly documented as unmet rather than closed — this
session declines to treat "governed by an existing deviation" as
equivalent to "met" when the Plan's own criterion text carries no such
hedge and the project has an established, better mechanism (a scoped plan
amendment, as amendment #21 demonstrated for the analogous Phase 2
situation) that was not used here. This is a scoring judgment about
process, not a claim that the underlying engineering or its reporting was
dishonest — every figure is present, consistent, and prominent everywhere
it should be.

---

## 9. Dimension P9 — Risk and deferred validation

### 9.1 Phase 3 recommendation tracking

| Rec | Priority | Status | Evidence |
|---|---|---|---|
| R21 — Fix PA3-F1/PA3-F2 | P0 | **Closed** (inter-phase, before WP-022 S1) — `DOCS/PRIN_Project_Plan.md` §6's Phase 3 row and `DOCS/experiments/README.md`'s index both corrected, independently re-confirmed present in this session's own read of the current Plan text |
| R22 — Phase-closing cross-cutting document currency | P1 | **Closed, and this session directly observed it operating** — Documentation Standards §7 item 9 fired correctly at WP-027 S4 (PA4-F1's §6.4 detail); the mechanism works, the override decision is the residual gap (R26, this session) |
| R23 — Escalate Snyk MCP unavailability | P1 | **Closed** — maintainer confirmed (2026-08-18) the Snyk-CLI-only posture is intentional and permanent; this session used the CLI directly per that standing decision |
| R24 — Consolidate GPU CI runner strategy | P2 | **Closed** at its assigned checkpoint (WP-022 S1) — self-hosted runner strategy decided (amendment #26); runner subsequently registered and, per EA-005's follow-up, all `windows-latest` CI jobs migrated to it |
| R25 — Investigate `windows-latest` CubeCL slowdown | P3 | **Closed** — the underlying DV-016 (and its EA-005 recurrence, DV-023) resolved not by root-causing the slowdown but by eliminating the GitHub-hosted `windows-latest` runner entirely in favor of the now-registered self-hosted runner, a stronger resolution than R25's own scoped ask |

**All 5 Phase 3 recommendations are addressed** — the fourth consecutive
phase in which the prior phase's analytics recommendations were fully
tracked to closure before the next phase's WP-N sessions began.

### 9.2 Risk register accuracy

| Risk | Status | Mitigation |
|---|---|---|
| `torch@2.13.0` (6 advisories, DV-011) | Accepted, unchanged | `.snyk`, maintainer approval, 2026-11-14 recheck (unchanged this phase) |
| Inherited `paste`/`bincode` advisories (DV-008/DV-017) | Governed, unchanged | Amendments #9/#27, rechecked at the WP-025 S3-exec session and again this session |
| GitHub-hosted CI runner infrastructure (DV-016/DV-022/DV-023) | **Substantially resolved** | Windows jobs migrated to a self-hosted runner, closing DV-016/DV-023 same-day; `ubuntu-latest` disk exhaustion (DV-022) remains open with a documented WSL2 fallback |
| Bridge overhead `<5%` (DV-021) | Open, architecturally attributed, three-times re-corroborated | Consistently OPEN; no amendment revises the Plan's own criterion text (§8) |
| CUDA Burn backend (DV-005) | Open, with a recorded maintainer-facing recommendation | Recommendation: defer absent a concrete Phase 5 workload |
| DV-019 flaky test | Open, recurred 4 times, root-caused, two fixes identified | Not yet assigned to a governed hotfix session (R28, this report) |

**Score: 4 (Strong).** Every prior-phase recommendation was tracked to
explicit closure (the fourth consecutive phase to achieve this); the DV
register itself, read in full this session, is exceptionally current and
precisely evidence-cited, with concrete-checkpoint discipline (DV-021/
DV-005 both pinned to the named WP-027 S1 session rather than left vague)
now a consistent, multi-phase pattern. Not a 5: DV-019's flaky test has
now recurred four times across three modules with two candidate fixes on
record and still no concrete session assignment — the one item in an
otherwise exemplary register that has not received the same
concrete-checkpoint treatment as DV-021/DV-005/R24.

---

## 10. Cross-dimensional analysis

### 10.1 Patterns and correlations

1. **First-pass implementation discipline reached its best level yet, on
   the largest single-phase code addition to date.** Zero of Phase 4's six
   WPs received a `FAIL` verdict at S2 — a genuine improvement over
   Phase 3's 1-of-5 and a stark contrast to Phase 2's 5-of-5 — despite
   `prin-train` being, at 13,590 lines, larger than any single crate
   addition in any prior phase, and despite this being the project's first
   use of an entirely new framework (Burn). This correlates with, and is
   plausible direct evidence for, R15's parity-evidence-disposition
   requirement (Phase 2) continuing to hold: every WP's S1 shipped its
   parity tests in the same commit, catching design bugs (WP-025's
   `retain_graph` failure) and numerical defects (WP-026's missing `ReLU`)
   before they could reach an audit at all.
2. **Correctly-firing safeguards are not self-executing — this phase
   supplies two concrete instances.** PA4-F1 (§6.4) shows Documentation
   Standards §7 item 9 correctly identifying a stale Project Plan marker
   and the session choosing to defer the fix anyway; the EMA-003
   closing-checklist skip (§6.4) shows the analogous EA/EMA safeguard
   (R16) being skipped by exactly the session type it targets, caught only
   by the next session of that type. Both are genuine self-correction
   successes in the sense that nothing shipped broken and both were caught
   within one cycle — but both also demonstrate that a checklist item
   existing and even firing is not the same as the gap it targets actually
   closing, a distinct and more subtle governance risk than "the checklist
   didn't cover this yet" (Phase 2/3's pattern).
3. **Independent, from-scratch re-verification remains the single most
   valuable evidentiary technique this methodology deploys, and this
   session is the first to demonstrate it catching a *false-positive*
   gate claim rather than a documentation-staleness gap.** PA4-F2's
   Sphinx-cache discovery is qualitatively different from every prior
   phase-analytics session's own findings (PA2-F1/F2, PA3-F1/F2, PA4-F1):
   those are all "a true fact was not recorded somewhere" gaps; PA4-F2 is
   "a false claim was recorded and repeated by every session that checked
   it," because every one of those sessions' checks shared the same stale
   cache. This is a stronger argument for genuinely independent
   (fresh-environment) re-execution than any prior session's findings
   have supplied.
4. **A new heavyweight dependency materially changes the security-risk
   profile, exactly as anticipated.** Burn's arrival (first use in this
   repo) produced the phase's only two new supply-chain advisories,
   including the project's most significant DoS-class CVE finding since
   the WP-001/WP-003 PyO3 advisories at the very start of the project —
   caught and fixed the same day via routine CI, but a genuine reminder
   that Phase 3's zero-new-dependency security posture was a property of
   that specific phase's scope (workspace-internal GPU-kernel work), not a
   durable baseline the project can assume going forward.
5. **Parity/gradcheck tests are now reliably catching real defects, not
   merely satisfying a checklist requirement.** Two independent instances
   this phase (WP-026's missing-`ReLU` catch via a newly-added
   whole-module parity test; WP-025's `retain_graph` design-bug catch via
   the gradcheck requirement itself) are concrete, falsifiable evidence
   that the Testing Standards' test-in-tandem requirement is doing
   substantive verification work — directly analogous to, and now a
   second consecutive phase's worth of confirmation of, Phase 3's
   observation that hardware-grounded/tool-executed evidence catches what
   design review alone would not.

### 10.2 Systemic strengths

- **Best-ever per-WP first-pass discipline** (0/6 `FAIL`) on the largest
  single-phase code addition to date.
- **R15's parity-evidence-disposition requirement held for a full second
  phase**, and demonstrably caught real bugs twice this phase alone.
- **Zero regressions across 40 independently re-derived mathematical
  claims**, plus genuine tool-capability advancement (EMA-004 fixed 2 of
  3 targeted multi-audit-old tool gaps at their root cause, not by
  re-scoping the claims).
- **The CI dependency-scanning safety net caught a real DoS CVE the same
  day it entered the tree**, and was fixed via a clean, minimal hotfix —
  the safety net working exactly as designed.
- **All five Phase 3 recommendations tracked to explicit, evidence-backed
  closure** before Phase 4's own WP-N sessions began — the fourth
  consecutive phase to achieve full recommendation-closure discipline.

### 10.3 Systemic weaknesses

- **A checklist item that correctly fires can still be overridden by a
  same-session deferral decision** (PA4-F1) — a distinct and, in a sense,
  more concerning failure mode than a checklist gap that has not yet been
  built.
- **A false "gate green" claim propagated silently across an entire
  phase's worth of sessions** because every one of them reused the same
  stale local build cache (PA4-F2) — the first instance of this specific
  failure class this project's analytics sessions have found.
- **DV-019's flaky test has now recurred four times across three modules**
  with two identified fixes still unscheduled into any concrete session —
  the one item in an otherwise exemplary Deferred Validation Register that
  has not received the project's now-standard concrete-checkpoint
  treatment.
- **A genuinely new, heavyweight dependency (Burn) materially raised the
  supply-chain risk surface**, producing the phase's only two new
  advisories including a real DoS-class CVE.
- **One of three explicit Plan §6 exit criteria is not met**, and remains
  an open deviation rather than a plan-amendment-closed criterion, despite
  the project having an established, stronger precedent (amendment #21)
  for exactly this situation.

---

## 11. Comparison with Phase 3

| Metric | Phase 3 | Phase 4 | Delta |
|---|---|---|---|
| Work packages | 5 | 6 | +1 |
| Sessions | 20 | 24 | +4 |
| Commits (WP range, phase-close to phase-close) | 29 (to WP-021 S4) / 33 (to `HEAD`) | 46 (to WP-027 S4) / 48 (to `HEAD`) | +17/+15 |
| WP audit findings (total) | 8 | 11 | +3 |
| WP D1 findings | 1 | 1* | = |
| WP D2 findings | 3 | 1 | −2 |
| WP D3 findings | 0 | 2 | +2 |
| WP D4 findings | 4 | 7 | +3 |
| WPs with `FAIL` S2 verdict | 1 of 5 | **0 of 6** | **−1 (best yet)** |
| Executive/EMA-tier sessions | 2 (EA-004, EMA-002) | 3 (EA-005, EMA-003, EMA-004) | +1 |
| Executive/EMA-tier findings | 2 | 6 | +4 |
| Rust tests (default workspace) | 821 | 1144 | +323 |
| New Rust crates | 0 (deepened `prin-kernels`/`prin-sim`) | 1 (`prin-train`, 13,590 lines) | +1 |
| Python fast tests | 306 | 441 | +135 |
| Full Python + parity tests | 816 | 959 | +143 |
| Golden-value parity tests (new subsystem) | 0 (GPU kernels use kernel-equivalence, not golden-value) | 15 (first-ever for `prin-train`) | +15 |
| New external dependencies | 0 | 1 (`burn`) | +1 |
| New supply-chain advisories | 0 | 2 (`bincode` informational, `h2` real DoS) | +2 |
| Plan amendments | 0 | 4 (#26–#29) | +4 |
| This session's own fresh findings | 2 (PA3-F1 D4, PA3-F2 D3) | 2 (PA4-F1 D3, PA4-F2 D2) | = (count); PA4-F2 is a novel gate-integrity class, not a documentation-currency recurrence |
| Aggregate verdict | PASS — SATISFACTORY | PASS — SATISFACTORY | = |

---

## 12. AI assistance disclosure

This Phase 4 Analytics Report was drafted by Claude Code (AI pair) with
independent re-execution of every quality, test, coverage, security, and
documentation-build gate listed in §5.4 against `HEAD` `b93bbaa`
(2026-08-21) — including, deliberately, re-running the Sphinx build
against both a fresh output directory and the pre-existing cached one to
isolate the cause of a discrepancy this session found rather than assumed.
Three background research passes (subagent invocations) independently
gathered: (1) the full WP-022 through WP-027 governance trail (session
briefs, audit findings, PSR deviation-ledger entries, plan-amendment
text, CHANGELOG extracts); (2) the full EA-005/EMA-003/EMA-004 report
content and the complete Deferred Validation Register; (3) the
`prin-train`/`prin.nn` code and evidence-artefact inventory (file paths,
line counts, `unsafe` audit, EVIDENCE/ contents, exit-criterion evidence
chain, CI workflow references). This main session independently verified
representative claims from each pass against primary sources (reading
EA-005, EMA-003, and EMA-004 in full directly; reading PSR-027, the WP-022
audit, and the Deferred Validation Register in full directly) before
incorporating them, and discovered PA4-F1 and PA4-F2 directly through its
own re-execution rather than via either research pass. The methodology
follows `DOCS/ANALYTICS/ANALYTICS_METHODOLOGY.md`. Maintainer review is
required before issuance.

---

## 13. Errata policy

If a claim in this report is later invalidated, an erratum will be
appended to this report and noted in `CHANGELOG.md`, per the
Experimentation Standards §4 and the Analytics Methodology §6.
