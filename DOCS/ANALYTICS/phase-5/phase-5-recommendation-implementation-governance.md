# Phase 5 Recommendation Implementation — Governance and Methodology

**Status:** Normative for this implementation session.
**Date:** 2026-08-26
**Authority:** Phase 5 Analytics Report (`phase-5-analytics-report.md`),
Phase 5 Recommendations Register (`phase-5-recommendations.md`),
[Development Workflow and Audit Standards](../../standards/Development_Workflow_and_Audit_Standards.md),
[Analytics Methodology](../ANALYTICS_METHODOLOGY.md), and the Phase 1–4
precedent (`../phase-1/phase-1-recommendation-implementation-governance.md`,
`../phase-2/phase-2-recommendation-implementation-governance.md`,
`../phase-3/phase-3-recommendation-implementation-governance.md`,
`../phase-4/phase-4-recommendation-implementation-governance.md`).
**Git state:** `main` @ `7d3fd30` (post-Phase-5-analytics, pre-implementation)
**Session position:** Inter-phase process improvement — between session 0128
(Phase 5 close, WP-032 S4), EA-006, EMA-005, the EMA-005 remediation session,
and the M-F9/DV-026 tool-remediation session, and session 0129 (Phase 6
start, WP-033 S1, currently `PLANNED`).

---

## 1. Purpose

This document establishes the governance, scope, methodology, and
disposition of each Phase 5 recommendation (R33–R36) for implementation
before Phase 6 begins, following the identical precedent established by the
Phase 1 (R7–R13), Phase 2 (R14–R20), Phase 3 (R21–R25), and Phase 4
(R26–R32) recommendation implementation sessions.

### 1.1 Relationship to existing governance

The [Analytics Methodology](../ANALYTICS_METHODOLOGY.md) §7 states a phase
analytics session is not itself a Session Cycle session; it produces
recommendations that inform the next phase. The
[Recommendations Register](phase-5-recommendations.md) priority legend
assigns timing:

| Priority | Action timing |
|---|---|
| P0 — Critical | Before Phase 6's next S4/global session |
| P1 — High | Phase 6 first cycle |
| P2 — Medium | Phase 6 mid-phase |
| P3 — Low | Phase 7+ or opportunistic |

### 1.2 Key finding that reshapes this session's scope

Before implementing anything, this session verified the current repository
state against each recommendation's own text, per this project's standing
rule (CLAUDE.md: "verify implementation facts from the repository; do not
invent commands, APIs, paths, configuration, or evidence"). That check
found **R33 (P0) was already fully satisfied before this session began**:

- `git log` shows commit `7376437` ("fix(Hotfix-DV019): close DV-019 —
  burn-autodiff cross-thread graph corruption, not fixture noise") is an
  **ancestor** of `7d3fd30` — the very commit that added
  `phase-5-analytics-report.md`/`phase-5-recommendations.md`/
  `phase-5-evidence-index.md` to the repository (`git log --oneline
  --follow` on those three files shows exactly one commit, `7d3fd30`
  itself). The two commits are 21 seconds apart in the same push
  (`Wed Aug 26 04:44:42 2026` vs. `04:45:03`).
- `DEFERRED_VALIDATION_REGISTER.md`'s DV-019 row already reads **`CLOSED
  (2026-08-26, Hotfix-DV019)`**, with a full root-cause/fix/verification
  narrative (51 consecutive clean runs pre-existing evidence, 10/10 clean
  under the exact contention scenario that reproduced the defect).
- `DOCS/sessions/phase-6/0129-wp033-s1-unified-benchmark-runner-and-category-migration.md`'s
  Entry Conditions section already reads **"Hard gate — SATISFIED
  (2026-08-26, `Hotfix-DV019`)"**.

So `phase-5-recommendations.md`'s own framing of R33 ("Open, unresolved as
of this report") was stale at the moment it was committed — the underlying
fix had already landed in the same push, immediately before it. This is
recorded explicitly, not silently reproduced (which would duplicate
`Hotfix-DV019`'s work) and not silently skipped (which would leave R33
formally un-dispositioned). R34, R35, and R36 are genuinely open and are
implemented in full in this session.

### 1.3 Principles

Identical to the Phase 1–4 precedent:

1. **Evidence-based implementation.** Each recommendation is implemented (or,
   for R33, verified) against its motivating evidence and confirmation
   evidence as stated in the Recommendations Register.
2. **Minimal blast radius.** Only the specific artefacts named by each
   recommendation are modified. No scope creep.
3. **Deferred items are tracked.** Every recommendation not fully
   implemented in this session is assigned to an explicit future
   session/WP with a documented rationale. (Not applicable this session —
   all four recommendations reach a terminal disposition here.)
4. **Verification-gated.** All changes pass the project's verification
   one-liner (`AGENTS.md`) before commit.
5. **Governance-compliant.** Standards amendments follow the same review
   bar as the project plan: documented rationale, cross-references.
6. **Maintainer decisions are recorded, not assumed.** R35 and R36 are
   maintainer-approval-class dispositions where the recommendation's own
   text states either outcome is legitimate; both are made directly in
   this session (following the Phase 3 R23/Phase 4 R29 precedent for a
   directly-available-maintainer decision) and recorded with full
   rationale for the maintainer to review or override.

---

## 2. Recommendation disposition

| ID | Priority | Disposition | Implementation target | Rationale |
|---|---|---|---|---|
| R33 | P0 | **Already satisfied — verified, no new code** | `DEFERRED_VALIDATION_REGISTER.md` (Phase 5 analytics table, review log) | `Hotfix-DV019` (commit `7376437`) closed DV-019 before the recommendations register that raised R33 was even committed. Re-verified directly rather than re-implementing an already-closed fix (§1.2, §5.1). |
| R34 | P1 | **Implement now** | `tools/check_dv_register_gates.py` (new); `tests/test_check_dv_register_gates.py` (new); `.github/workflows/python.yml`; `Development_Workflow_and_Audit_Standards.md` §3 | Recommendation's own suggested approach ("extend `check_deviation_ledger.py`... or add a companion tool"); confirmation evidence explicitly required exercising the tool against the historical R28/DV-019 case, satisfied here with the real pre-fix repository state rather than a hand-approximated fixture. |
| R35 | P3 | **Implement now (explicit disposition recorded)** | `DEFERRED_VALIDATION_REGISTER.md` (DV-004) | Recommendation's own text: "either is a legitimate outcome; what is missing is a formal disposition." Five consecutive phases of unchanged "re-audited, unaffected" carry-forward with no toolchain-advancement candidate on record justify closing now rather than deferring a sixth time. |
| R36 | P3 | **Implement now (evaluation and decision recorded)** | `DEFERRED_VALIDATION_REGISTER.md` (DV-028) | Recommendation asks for an evaluation and a recorded decision, not necessarily "vendor." No `.gitmodules`/publishable remote exists for the tool; standing one up is an infrastructure decision out of this session's scope, so the decision is "do not vendor at this time," recorded with full rationale. |

### 2.1 Summary

- **Already satisfied (1):** R33 — verified, no code action.
- **Implemented now (3):** R34 (P1), R35 (P3), R36 (P3).
- **Deferred (0):** none — every Phase 5 recommendation reaches a terminal
  disposition in this session.

---

## 3. Implementation methodology

### 3.1 Scope

This session modifies only:

1. `tools/check_dv_register_gates.py` (new) — R34's mechanical-enforcement
   tool.
2. `tests/test_check_dv_register_gates.py` (new) — 20 tests, 100% line
   coverage of the new module.
3. `.github/workflows/python.yml` — R34: new `lint`-job step running the
   tool on every push/PR.
4. `DOCS/standards/Development_Workflow_and_Audit_Standards.md` — R34: §3
   S4 gains a new mandatory action (action 7) documenting the tool,
   mirroring how DV-015 added action 6 for `check_deviation_ledger.py`.
5. `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` — R33: DV-019/Phase-5
   analytics table annotated with the already-satisfied finding and
   drift-check evidence. R34: closed in the new Phase 5 analytics table.
   R35: DV-004 closed with an explicit disposition. R36: DV-028 updated
   with the vendoring evaluation and decision. New "Phase 5 analytics —
   deferred and ongoing items" section; new closed-items rows; review-log
   entry appended.
6. `CHANGELOG.md` — new `[Unreleased]` entry for this session.
7. `tools/README.md` — new tool documented alongside
   `check_deviation_ledger.py`'s existing entry.
8. This governance document.

No Rust source, no dependency manifests, no session-brief/PSR/
`SESSION_REGISTER.md` files are touched — this is not a numbered
Session-Cycle session (same as all four prior recommendation-implementation
sessions), so no PSR is written and `SESSION_REGISTER.md` is not edited.

### 3.2 Entry conditions

- [x] Phase 5 complete (session 0128 closed; phase exit gate GREEN per
  `DOCS/reports/032-project-state.md`, independently re-confirmed by EA-006
  and the Phase 5 Analytics Report).
- [x] Phase 5 Analytics Report, Evidence Index, and Recommendations
  Register drafted and indexed (`DOCS/ANALYTICS/phase-5/`,
  `DOCS/ANALYTICS/README.md` @ `7d3fd30`).
- [x] No unresolved D1/D2 findings — EA-006's two findings (E-F1, E-F2) are
  both D3 and both already remediated (E-F1 fixed in-session; E-F2's DV-019
  precondition closed by `Hotfix-DV019`, which is exactly R33's subject).
- [x] `main` up to date with `origin/main`, working tree clean at session
  start (`git status` confirmed nothing to commit before this session's own
  changes began).
- [x] WP-033 (Phase 6, session 0129) confirmed still `PLANNED`, not
  started — this session genuinely precedes Phase 6 S1.

### 3.3 Exit criteria

- [x] R33 verified already-satisfied with fresh drift-check evidence, not
  silently reproduced or silently skipped.
- [x] R34 implemented in full, including the historical-case confirmation
  evidence its own text requires.
- [x] R35/R36 maintainer-class decisions obtained directly and recorded
  with rationale.
- [x] Verification one-liner (`AGENTS.md`) passes clean.
- [x] Changes committed with descriptive messages referencing
  recommendation IDs.
- [x] This governance document updated with implementation results.

---

## 4. Commit protocol

| Commit | Message prefix | Scope |
|---|---|---|
| R34 | `feat(R34): DV-register session-gate enforcement tool` | `tools/check_dv_register_gates.py`, `tests/test_check_dv_register_gates.py`, `.github/workflows/python.yml`, `Development_Workflow_and_Audit_Standards.md`, `tools/README.md` |
| R33/R35/R36 + register | `docs(reports): R33 already-satisfied, close R35/R36, Phase 5 recommendation implementation` | `DEFERRED_VALIDATION_REGISTER.md`, `CHANGELOG.md` |
| Governance | `docs(analytics): Phase 5 recommendation implementation governance and methodology` | This document |

---

## 5. Implementation results

### 5.1 R33 — Already satisfied (verified, not re-implemented)

**Status:** ALREADY SATISFIED — no code action; verified with fresh evidence.
**Evidence:** See §1.2 for the commit-ancestry/DV-register/session-brief
evidence establishing that `Hotfix-DV019` (commit `7376437`) closed DV-019
before the Phase 5 recommendations register itself was committed. As a
drift check (not a re-fix), this session independently re-ran:
- `cargo test -p prin-train --lib` — **10 consecutive runs at default
  concurrency, 375/375 tests passing every time, zero failures.**
- `cargo test -p prin-train --lib gradients_flow_to_every` (targeted filter)
  — 6/6 gradient-presence tests pass in one run, including the two DV-019
  named by name: `bands::tests::gradients_flow_to_every_parameter` and
  `hybrid::tests::gradients_flow_to_every_layer_class`.

No drift from `Hotfix-DV019`'s own verification evidence (51 consecutive
clean runs, 10/10 under contention) was found.

### 5.2 R34 — DV-register gate-enforcement tool

**Status:** IMPLEMENTED
**Files added:** `tools/check_dv_register_gates.py`,
`tests/test_check_dv_register_gates.py`
**Files modified:** `.github/workflows/python.yml`,
`Development_Workflow_and_Audit_Standards.md`, `tools/README.md`

**Design:** Parses `DEFERRED_VALIDATION_REGISTER.md`'s "Active deferred
items" table and `SESSION_REGISTER.md`'s numbered-session table; detects
"before session NNNN"/"before WP-0NN S1 (session NNNN)" precondition
phrases in a DV row's text; flags a violation when the named session is
`COMPLETE` while the row's own Current status does not read
`CLOSED`/`SATISFIED`. Column extraction is right-anchored (`cells[-2]` for
Current status) rather than left-indexed, discovered necessary during
implementation: the live register has genuinely malformed rows —
DV-010 through DV-014 are missing the Re-audit gate column entirely (7
cells instead of 8), and DV-020 has an extra cell from a literal `|`
inside inline-code prose (`` `grep -rl "PhaseAdam\|KuramotoOptimizer"` ``,
9 cells) — and a naive left-indexed parse silently misaligned Current
status for 5 of 28 real rows. Right-anchoring fixes this because the
anomalies occur in the early free-text columns, never in the last real
column; both malformed-row shapes are covered by dedicated tests.

**Confirmation evidence (the recommendation's own explicit requirement):**
exercised against the real historical R28/DV-019 gap by feeding the tool
`git show 5fdfeb0:DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` and `git
show 5fdfeb0:DOCS/sessions/SESSION_REGISTER.md` (the actual pre-fix
repository state, one commit before `Hotfix-DV019`) — the tool correctly
reports exactly one violation: `DV-019: gate session 0109 is COMPLETE but
the item is not closed/satisfied`. The same historical shape is also
reproduced as a self-contained pytest fixture
(`test_flags_historical_r28_dv019_gap`) so the regression stays covered
without depending on git history remaining available. Against the current,
real, live register and session register, the tool reports 0 violations
(`test_current_repository_state_is_clean`), confirming it does not flag
the post-fix state.

**Test evidence:** `pytest tests/test_check_dv_register_gates.py -v
--cov=check_dv_register_gates --cov-report=term-missing` — 20 passed, 100%
line coverage (91/91 statements). `ruff check`/`ruff format --check`/
`bandit -c pyproject.toml` all clean on both new files.

**CI wiring:** `.github/workflows/python.yml`'s `lint` job runs `python
tools/check_dv_register_gates.py` immediately after the existing
deviation-ledger consistency step, on every push/PR.

**Standards documentation:** `Development_Workflow_and_Audit_Standards.md`
§3 S4 gains action 7, documenting the tool as a mandatory S4 verification
command, mirroring action 6's precedent for `check_deviation_ledger.py`.

### 5.3 R35 — DV-004 explicit disposition

**Status:** IMPLEMENTED (decision recorded)
**Files modified:** `DEFERRED_VALIDATION_REGISTER.md` (DV-004)
**Decision:** Kernel-equivalence tests are the accepted, permanent coverage
mechanism for `#[cube(launch)]` bodies; line coverage does not apply to
them.
**Rationale:** DV-004 was re-audited unchanged at every WP gate from Phase 0
(WP-004) through Phase 5 — ten non-instrumentable kernel bodies,
instrumentable surrounding code consistently ≥95% (`gpu.rs` 99.67%,
`discrete_step.rs` 97.65%, most recently re-confirmed at WP-021) — with no
Rust/CubeCL toolchain advancement on record that would make kernel-launch
bodies instrumentable. Kernel-equivalence tests, validated against the
CPU/wgpu/CUDA backends across Phase 3's WP-017–WP-021, independently
confirm numerical correctness for exactly the code `cargo-llvm-cov` cannot
see into. The recommendation's own text names this as one of two legitimate
outcomes and asks only for a formal, dated disposition rather than a sixth
consecutive "re-audited, unaffected" — recorded directly in this session
per the Phase 3 R23/Phase 4 R29 precedent for maintainer-class decisions
made when the evidence clearly supports one outcome and the maintainer is
the session's principal.

### 5.4 R36 — DV-028 vendoring evaluation and decision

**Status:** IMPLEMENTED (evaluation and decision recorded)
**Files modified:** `DEFERRED_VALIDATION_REGISTER.md` (DV-028)
**Decision:** Do not vendor `math-audit-mcp` into PRIN at this time.
**Evaluation:** A git submodule requires a remote URL reachable from CI and
any other clone; `math-audit-mcp` exists only as a local workstation git
repository at `C:\dev\--DEV\Math Audit MCP` with no published remote on
record anywhere in this project's governance documents, and this
repository has no `.gitmodules` today (confirmed by inspection — `test -f
.gitmodules` returns false). A subtree merge has the same dependency on a
fetchable remote. Standing up such a remote is an infrastructure decision
(hosting choice, the tool's own release/versioning process) outside the
scope of a DV-register disposition, for a P3, opportunistic item.
**Rationale:** Keep `math-audit-mcp` external, consistent with the
project's existing separation-of-concerns precedent for Snyk/`cargo
audit`/`pip-audit` (Coding Standards §6) — re-evaluate if a publishable
remote for the tool is ever established.

### 5.5 Verification results

All gates green (2026-08-26, `main` @ `7d3fd30` + this session's commits):

| Gate | Result |
|---|---|
| `ruff check python/ tests/ benchmarks/ tools/ parity/` | All checks passed |
| `ruff format --check` (same paths) | Already formatted |
| `mypy python/prin --strict` | Success, 0 issues (scope excludes `tools/`; confirmed by inspecting `AGENTS.md`'s one-liner) |
| `interrogate -c pyproject.toml python/prin` | Unaffected (scope excludes `tools/`) |
| `bandit -r . -c pyproject.toml` | 0 issues, including the two new files |
| `pytest tests/test_check_dv_register_gates.py --cov=check_dv_register_gates` | 20 passed, 100% coverage (91/91 statements) |
| `pytest tests/ -m "not slow and not gpu" --cov=prin` | 575 passed, 8 deselected; 99% coverage (1387/1399) |
| `pytest tests/ parity/ --cov=prin` | 1175 passed, 0 failed |
| `cargo fmt --all -- --check` | Clean |
| `cargo clippy --workspace --all-targets -- -D warnings` | Clean, 0 warnings-as-errors |
| `cargo test --workspace` | 1447 passed, 0 failed (unit + integration + doctests across all crates) |
| `cargo llvm-cov -p prin-kernels --features wgpu,cpu` | 149/149 tests pass; 89.84% line / 90.29% region coverage (unchanged class — non-instrumentable `#[cube(launch)]` bodies, DV-004/R35) |
| `cargo llvm-cov -p prin-dynamics` | Clean; 97.74% line coverage |
| `cargo llvm-cov -p prin-dynamics --features strict-checks` | Clean; 97.66% line coverage |
| `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | Clean, 0 warnings |
| `cargo audit` | 2 allowed advisories (`bincode` DV-017, `paste` DV-008), 0 new |
| `pip-audit .` | No known vulnerabilities |
| `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities |
| Fresh-directory `sphinx-build -W --keep-going -b html` | **Build succeeded, 0 warnings** |
| `python tools/check_dv_register_gates.py` (real repo state) | Passed — 28 rows checked against 198 session-register entries, 0 violations |
| `python tools/check_deviation_ledger.py 031-project-state.md 032-project-state.md` (unaffected regression check) | Passed — 111 vs. 112 rows compared, clean |
| `cargo test -p prin-train --lib` × 10 (R33 drift check) | 10/10 clean, 375/375 tests each run |

**Snyk Code (per Coding Standards §6, mandatory for new first-party Python):**
Snyk MCP was unavailable this session (not among the connected MCP servers);
per the standing R23 decision, the Snyk CLI is the position of record.
`snyk code test tools/check_dv_register_gates.py --severity-threshold=medium`
and `snyk code test tests/test_check_dv_register_gates.py
--severity-threshold=medium` — **0 issues, both files.**

**Known pre-existing, out-of-scope finding (not fixed, not introduced by
this session):** `bandit -r . -c pyproject.toml` reports 2 low-severity
`B101` (`assert_used`) findings in
`EVIDENCE/math-audit/manual/mf9-beta-allowlist-verification.py`. `git log`
confirms this file was added by commit `5fdfeb0` ("fix(DV-026): close M-F9"),
a different, unrelated session from earlier the same day — not touched by
R33–R36. Recorded here per this project's own precedent (Phase 4's R30
disposition: "noted rather than silently skipped") rather than fixed, to
avoid scope creep into an unrelated evidence artefact (Coding Standards §1,
Development Workflow Standards §2's WP scope-discipline principle applied
by analogy to this inter-phase session's own declared scope, §3.1 above).

### 5.6 Push, CI, and GPU verification

Pushed to `origin/main` in three commits (`e927d8f` R34; `774ac7d` R33/R35/
R36 + register; `75e6aa5` this governance document, tagged `[gpu]` per this
task's explicit "make sure GPU tasks are run" instruction). Live CI on that
push (`75e6aa5`, run set starting `32948083...`):

| Workflow | Result |
|---|---|
| `repro` | success |
| `snyk` | success |
| `parity` | success |
| `python` | success |
| `rust` | success |
| `gpu` | **failure** — both `gpu-cuda`/`gpu-wgpu` failed at `dtolnay/rust-toolchain@stable` (WSL bash unavailable on the self-hosted runner) |

5/6 green; `gpu` failed at a step unrelated to R33–R36's own changes — the
same DV-024 root cause already fixed for `rust.yml`/`python.yml`'s
self-hosted legs (commit `cb5660b`) but never applied to `gpu.yml`. Since
this was this project's first `[gpu]`-tagged push since `cb5660b` landed,
the gap had never surfaced before. Fixed as a Development Workflow
Standards §7 hotfix (broken CI): `gpu.yml` commit `6c608cb` removes the
step outright (no hosted-runner leg exists to make it conditional against;
Rust is pre-installed on `PRIN-GPU-Runner`).

Re-verified live on the hotfix push (`6c608cb`, run set starting
`32949...`):

| Workflow | Result |
|---|---|
| `repro`, `snyk`, `parity`, `python`, `rust` | success (unchanged) |
| `gpu` → `gpu-wgpu` | **success** — full end-to-end pass |
| `gpu` → `gpu-cuda` | **failure**, but substantially further than ever before: `Rust kernel-equivalence tests (CUDA)` and `Build extension with CUDA and install` both pass live on real GPU hardware; only the final `Python GPU tests` step fails (`pytest tests/ -v -m gpu` selects 0 tests, exit 1, no test failures shown) |

The remaining `gpu-cuda` gap is recorded as new `DEFERRED_VALIDATION_REGISTER.md`
item **DV-029** with two candidate root causes (neither confirmed without
live runner access: a missing `onnx` pip extra in the CUDA build step, or a
`pwsh`-wrapped stderr/exit-code quirk) and disposed opportunistic/
not-WP-gated, matching the DV-016/DV-022/DV-023 precedent for this class of
CI-infrastructure gap — investigating further requires either live
self-hosted-runner access or authoring this project's first
`@pytest.mark.gpu` Python test, both out of scope for this documentation/
tooling recommendation-implementation session. This is a genuine,
substantial improvement over the prior state (where `gpu.yml` had never
successfully executed a single step past the toolchain setup on any push),
not a full closure of every GPU CI gap — recorded honestly rather than
either claimed as complete or left undiagnosed.

### 5.7 DV-029 deep-dive (continuation, at user request)

The user asked to continue investigating DV-029 rather than leave it as an
opportunistic unknown. This section's dispositions above (§5.6, "neither
confirmed without live runner access") are superseded by this deeper
investigation, which fully root-caused and fixed all three real bugs behind
`gpu-cuda`'s remaining failure:

1. **`shell: bash` on the venv-creation step (`55ba62b`)** — copied from
   `python.yml` verbatim, but `gpu.yml` has no hosted-runner leg to safely
   inherit that from; requires WSL, unavailable on `PRIN-GPU-Runner`. Same
   failure class as the already-fixed `dtolnay/rust-toolchain` step. Fixed
   by switching to PowerShell (this job's actual default shell).
2. **`$GITHUB_PATH` prepending not taking effect (`f03da04`)** — even after
   venv creation, a bare `python`/`pip` in the next step still resolved to
   the shared global Miniforge install (live evidence: `pip install
   maturin` reported "already satisfied ... in
   C:\Users\there\miniforge3\Lib\site-packages", and the pytest header
   showed unrelated extra plugins — `xdist`/`anyio`/`asyncio`/`timeout` —
   this project depends on none of). Fixed by invoking
   `.venv\Scripts\python.exe` by absolute path for every command. Verified
   live: the next run's pytest header showed the correct isolated
   interpreter path and a clean plugin list for the first time.
3. **Zero `@pytest.mark.gpu` tests exist in this codebase (`8f45a5b`)** —
   even fully isolated, the step still failed with the same "0 selected"
   pattern plus 1–2 items skipped at collection. Added `-rs` (`da61d72`) to
   reveal skip reasons directly: two harmless, expected
   `pytest.importorskip` guards (`onnxruntime`, `prinet`) firing because
   this job's minimal `.[dev]` install never installs those optional
   extras. Reproduced the *exact* CI package set in a local venv and ran
   the identical command directly (not through a masking shell pipe, which
   had given a misleading "exit 0" reading on a first local attempt):
   **pytest's real exit code is 5** ("no tests collected") — not a bug,
   the structurally correct outcome, since `grep`-confirmed zero tests
   anywhere in this codebase carry `@pytest.mark.gpu` (the marker is
   registered in `pyproject.toml` but never applied — authoring the
   project's first GPU-marked Python test is a real future feature, not a
   CI defect). GitHub Actions' `pwsh` step wrapper reports any nonzero
   `$LASTEXITCODE` as a failure regardless of the specific code, which is
   why CI showed "exit code 1" rather than 5. Fixed: the step now catches
   exit 5 explicitly and treats it as success; any other nonzero code
   (a genuine test failure) still fails the step.

**Verification status — blocked, not failed.** This fix (`8f45a5b`, current
`main` HEAD) is derived from an exact local reproduction of the failure,
not a guess, and is believed correct. It has not yet been confirmed by a
live CI run: the push landed inside a run where `rust`/`python`/`parity`/
`snyk` all show `startup_failure`/`failure` with jobs permanently stuck
`queued` (`conclusion: failure`, zero steps executed, no job logs — `gh run
view --log` returns "log not found") and `gpu.yml` never registered a run
at all for that commit — unchanged after a 5-minute recheck. This exactly
matches this register's own `DV-014` precedent (a GitHub Actions
billing/spending-limit block): the immediately prior push (`da61d72`) ran
cleanly end-to-end minutes earlier, ruling out the `gpu.yml` changes
themselves as the cause. Per `DV-014`'s own disposition, this is an
external, account-level condition outside this session's control, passed
forward to the maintainer rather than worked around by further pushes.
`DEFERRED_VALIDATION_REGISTER.md` DV-029 is updated accordingly and stays
**OPEN** — not because the root cause is unknown (it no longer is) but
because CI itself is currently unavailable to prove the fix live.

**Update — DV-029 closed.** The maintainer confirmed the billing/
spending-limit condition resolved; the queued fix push (`8f45a5b`, folded
into `dd9979c` below) ran immediately and cleanly. Once "Python GPU tests"
passed for the first time, the job reached a step never exercised before —
"Kernel performance regression gates" (`cargo bench --workspace --features
cuda -- --save-baseline ci`) — and hit a **fourth** real bug: `cargo bench
--workspace` forwards criterion-specific CLI args to every bench-profile
binary it builds, including each crate's own implicit `[lib]` target
(`bench = true` is Cargo's default unless a crate opts out), not just
`[[bench]]`-declared criterion targets — `prin-daemon`'s plain unit tests
don't understand `--save-baseline`, so this gate had apparently never once
succeeded in this workflow's history. Fixed (`dd9979c`) by listing all 9
`[[bench]]` targets explicitly (one `--bench <name>` per crate's Cargo.toml
declaration across `prin-daemon`/`prin-kernels`/`prin-sim`/`prin-train`),
verified locally (all 9 run clean via criterion's `--test` smoke mode)
before the live push. **Live result (run `32995941536`): `gpu-cuda` and
`gpu-wgpu` both `success`** — the first fully green `gpu.yml` run ever
recorded for this project. `DEFERRED_VALIDATION_REGISTER.md` DV-029 is now
**CLOSED**. Four real, distinct, CI-configuration-only bugs were found and
fixed across this investigation (`55ba62b`, `f03da04`, `8f45a5b`,
`dd9979c`) — none required any Cargo.toml or source-code change.

---

## 6. Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| AI pair | Claude Sonnet 5 | 2026-08-26 | Drafted; R35/R36 decisions made directly in-session per the Phase 3/4 precedent for maintainer-class calls with unambiguous evidence — flagged here for the maintainer to review or override |
| Maintainer | MichaelMaillet | — | Pending review |
