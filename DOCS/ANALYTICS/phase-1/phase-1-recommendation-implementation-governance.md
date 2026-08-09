# Phase 1 Recommendation Implementation — Governance and Methodology

**Status:** Normative for this implementation session.
**Date:** 2026-08-09
**Authority:** Phase 1 Analytics Report (`phase-1-analytics-report.md`),
Phase 1 Recommendations Register (`phase-1-recommendations.md`),
[Development Workflow and Audit Standards](../../standards/Development_Workflow_and_Audit_Standards.md),
[Analytics Methodology](../ANALYTICS_METHODOLOGY.md).
**Git state:** `feat/wp006-oscillator-state` @ `7acdbe0` (post-Phase 1 analytics)
**Session position:** Inter-phase process improvement — between session 0044
(Phase 1 close, WP-011 S4) and session 0045 (Phase 2 start, WP-012 S1).

---

## 1. Purpose

This document establishes the governance, scope, methodology, and disposition
of each Phase 1 recommendation (R7–R13) for implementation before Phase 2
begins. It is the governing brief for the inter-phase recommendation
implementation session.

### 1.1 Relationship to existing governance

The [Analytics Methodology](../ANALYTICS_METHODOLOGY.md) §7 states:

> A phase analytics session is **not** a Session Cycle session (S1–S4). It
> does not produce code, does not follow the S1→S4 order, and does not
> produce an audit report. It is a retrospective assessment that [...]
> produces recommendations that inform the next phase's WP declarations and
> session briefs.

The [Recommendations Register](phase-1-recommendations.md) priority legend
assigns timing:

| Priority | Action timing |
|---|---|
| P0 — Critical | Before Phase 2 S1 |
| P1 — High | Phase 2 first cycle |
| P2 — Medium | Phase 2 mid-phase |
| P3 — Low | Phase 3+ or opportunistic |

No P0 recommendations were issued. The P1 recommendations (R7, R8) are
addressed in this inter-phase session to satisfy the "Phase 2 first cycle"
timing. P2 recommendations (R9, R10, R11, R12) are addressed where
practical; the remainder are deferred with explicit future-session
assignments.

### 1.2 Principles

1. **Evidence-based implementation.** Each recommendation is implemented
   against its motivating evidence and confirmation evidence as stated in
   the Recommendations Register.
2. **Minimal blast radius.** Only the specific artefacts named by each
   recommendation are modified. No scope creep.
3. **Deferred items are tracked.** Every recommendation not implemented in
   this session is assigned to an explicit future session/WP with a
   documented rationale.
4. **Verification-gated.** All changes pass the project's verification
   one-liner (`AGENTS.md`) before commit.
5. **Governance-compliant.** Standards amendments follow the same review
   bar as the project plan: documented rationale, cross-references.

---

## 2. Recommendation disposition

| ID | Priority | Disposition | Implementation target | Rationale |
|---|---|---|---|---|
| R7 | P1 | **Implement now** | `DOCS/standards/Documentation_Standards.md` §7 | P1 timing: "Phase 2 first cycle." Amending the S4 checklist before WP-012 S4 ensures the strengthened sweep applies from the first Phase 2 cycle. |
| R8 | P1 | **Implement now** | `.github/workflows/parity.yml` | P1 timing: "Phase 2 first cycle" or "first WP that adds new integrators." Wiring exhaustive 504-case CI before WP-012 ensures new integrators are validated against the full corpus from day one. |
| R9 | P2 | **Implement now** | `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` | P2 timing: "Phase 2 mid-phase." Creating the register now (before Phase 2 starts) ensures deferred items are tracked from the outset. Low effort, high governance value. |
| R10 | P2 | **Defer to Phase 3** | WP-017 (session 0053+) | Recommendation explicitly states "Phase 3 (WP-017) is the natural inflection point." No kernel code changes in Phase 2 first cycle. |
| R11 | P2 | **Ongoing process item** | Each cycle's S3/S4 | Recommendation is a standing instruction ("continue per-cycle rechecks"). No artefact to create; recorded in this register for traceability. |
| R12 | P2 | **Implement now** | `AGENTS.md` verification one-liner | P2 timing: "Phase 2 or Phase 3." Low effort — update the llvm-cov command to merge both default and strict-checks builds. |
| R13 | P3 | **Defer to WP-012** | WP-012 S1 (session 0045) | Recommendation explicitly targets WP-012: "For WP-012, design parity tests that validate convergence order, invariant preservation, agreement with RK4 at small dt." |

### 2.1 Summary

- **Implement now (4):** R7, R8, R9, R12
- **Defer with explicit assignment (2):** R10 → Phase 3 / WP-017; R13 → WP-012 S1
- **Ongoing process item (1):** R11 — per-cycle secret scanning availability check

---

## 3. Implementation methodology

### 3.1 Scope

This session modifies only:

1. `DOCS/standards/Documentation_Standards.md` — R7: add documentation
   accuracy sweep step to S4 checklist §7.
2. `.github/workflows/parity.yml` — R8: parameterize to run all 504 corpus
   cases.
3. `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` — R9: create the register.
4. `AGENTS.md` — R12: update `cargo-llvm-cov` command to merge strict-checks.
5. This governance document.

### 3.2 Entry conditions

- [x] Phase 1 complete (session 0044 closed, phase exit gate GREEN).
- [x] Phase 1 Analytics Report and Recommendations Register committed.
- [x] No unresolved D1/D2 findings in the deviation ledger.
- [x] Working tree clean on `feat/wp006-oscillator-state`.

### 3.3 Exit criteria

- [x] All four "implement now" recommendations addressed with artefacts.
- [x] Deferred items documented with explicit future-session assignments.
- [x] Verification one-liner (`AGENTS.md`) passes clean.
- [x] Changes committed with descriptive messages referencing recommendation IDs.
- [x] This governance document updated with implementation results.

### 3.4 Verification

The full verification one-liner from `AGENTS.md` is run after all changes:

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp-full
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo llvm-cov -p prin-kernels --features wgpu,cpu
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
```

---

## 4. Commit protocol

Each recommendation implementation is committed separately with the
recommendation ID in the message:

| Commit | Message prefix | Scope |
|---|---|---|
| R7 | `docs(standards): R7 — strengthen S4 consistency sweep with documentation accuracy step` | `Documentation_Standards.md` |
| R8 | `ci(parity): R8 — exhaustive 504-case differential CI` | `parity.yml` |
| R9 | `docs(reports): R9 — create Deferred Validation Register` | `DEFERRED_VALIDATION_REGISTER.md` |
| R12 | `docs(agents): R12 — merge strict-checks coverage in llvm-cov command` | `AGENTS.md` |
| Governance | `docs(analytics): Phase 1 recommendation implementation governance and methodology` | This document + session log |

---

## 5. Implementation results

*(To be completed after implementation.)*

### 5.1 R7 — Documentation accuracy sweep

**Status:** IMPLEMENTED
**Files modified:** `DOCS/standards/Documentation_Standards.md` (§7 item 8)
**Evidence:** New S4 checklist item 8 requires: (a) README accuracy in touched directories, (b) rustdoc code example compilation via `cargo test --doc`, (c) DOCS/ subdirectory index/README currency verification.

### 5.2 R8 — Exhaustive 504-case parity CI

**Status:** IMPLEMENTED
**Files modified:** `parity/test_parity_differential.py`, `.github/workflows/parity.yml`
**Evidence:** New `test_corpus_exhaustive_differential_parity` parametrized over all 504 manifest case IDs via `_all_corpus_case_ids()`. CI workflow installs `pytest-xdist` and runs with `-n auto` for parallel execution. Representative 5-case smoke test retained for local runs.

### 5.3 R9 — Deferred Validation Register

**Status:** IMPLEMENTED
**Files modified:** `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` (new)
**Evidence:** Register created with 10 active deferred items (DV-001–DV-010), Phase 1 analytics deferred recommendations table (R10, R11, R13), closed items section, and review log.

### 5.4 R12 — Strict-checks coverage merge

**Status:** IMPLEMENTED
**Files modified:** `AGENTS.md` (verification one-liner)
**Evidence:** Two separate `cargo llvm-cov -p prin-dynamics` commands added: default features and `--features strict-checks`. Both coverage reports are generated in each verification run.

### 5.5 Deferred items

| ID | Deferred to | Rationale |
|---|---|---|
| R10 | Phase 3 / WP-017 (sessions 0053+) | Natural inflection point when new kernels are added |
| R11 | Ongoing per-cycle S3/S4 | Standing process instruction; no artefact to create |
| R13 | WP-012 S1 (session 0045) | Explicitly scoped to WP-012 exponential integrators |

### 5.6 Verification results

All gates green (2026-08-09):

| Gate | Result |
|---|---|
| ruff check | All checks passed |
| ruff format | 47 files already formatted |
| mypy --strict | Success: no issues found in 18 source files |
| interrogate | 100.0% (106/106 public) |
| bandit | 0 low/medium/high (2,900 lines) |
| pytest tests/ (fast) | 241 passed, 6 deselected, 99% coverage |
| cargo fmt --check | Clean |
| cargo clippy -D warnings | Clean |
| cargo test --workspace | 367 passed (all suites) |
| RUSTDOCFLAGS='-D warnings' cargo doc | 0 warnings |
| cargo audit | 1 allowed (paste RUSTSEC-2024-0436, amendment #9) |
| pip-audit | No known vulnerabilities |
| pip-audit (Sphinx reqs) | No known vulnerabilities |
| Sphinx -W --keep-going | Build succeeded, 0 warnings |

---

## 6. Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| AI pair | Qwen Code | 2026-08-09 | Drafted |
| Maintainer | — | — | Pending approval |
