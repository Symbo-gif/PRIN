# Session 0144Y — WP-036G S1: Coding — Deferred-Validation register consolidation and permanent dispositions

**Status:** COMPLETE — S1 delivered and committed locally; handoff
[`DOCS/experiments/0144Y-wp036g-s1-handoff.md`](../../experiments/0144Y-wp036g-s1-handoff.md).
Awaiting the mandatory S2 audit `0144Z`.
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036G
**Session type:** S1 — Coding
**Predecessor:** [0144X — Documentation (WP-036F S4)](0144X-wp036f-s4-directml-controller-graph-execution.md)
**Successor:** [0144Z — Audit](0144Z-wp036g-s2-dv-register-consolidation-and-permanent-dispositions.md)
**Authority:** Project Plan §6/§8 and amendment #38, and [`WP-036E-036F-036G-execution-plan-and-decomposition.md`](WP-036E-036F-036G-execution-plan-and-decomposition.md). If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

> **New work package (Plan amendment #38).** After WP-036E/F, the Deferred
> Validation Register still carries items no work package can close: external
> infrastructure (DV-001, DV-009, DV-022), third-party advisories with no
> upstream fix (DV-008, DV-011, DV-017, `chacha20`), third-party library
> behaviour (DV-018), and by-design governance gates (DV-007, DV-013, DV-028).
> Left as undated "re-audit every cycle" rows they create a false impression
> of unresolved risk going into Phase 7 and — per Phase 5 analytics R35 — no
> cycle discharges them. WP-036G assigns every remaining open item an
> explicit, dated disposition, formalises one un-registered advisory, and
> resolves two pre-existing test-fragility issues so the campaign does not
> inherit them. This is a governance + light test-hardening WP: **no source
> numerics**.

## Mission

Bring the Deferred Validation Register to a state where every row is in
exactly one of: `CLOSED`, `AMENDED` (with amendment ref), **permanent
disposition** (dated, maintainer-signed, no further re-audit gate), or
**standing-external-disposition** (dated, evidenced, explicitly "not a
Phase 7 entry blocker"). Formalise the `chacha20` yanked advisory as a
register row. Resolve or formally document-as-CI-authoritative the two named
pre-existing test-fragility issues. Produce a Phase 7 entry statement.

## Contract

- **Acceptance:**
  - **Permanent dispositions** authored for **DV-007** (f64/f32 preserved
    hazard — governed by the `1e-6` derivative tolerance + corpus `rtol=2e-6`
    + Parity Report, amendments #14/#16/#17/#25), **DV-013** (`M-F3`/`M-F7`
    `REQUIRES_HUMAN_REVIEW` — sign-off re-granted each EMA when the claim set
    changes), **DV-018** (`burn-tensor` f32-internal `sigmoid` — documented
    per-call-site with `eps=1e-4`, re-check only on a `burn` bump), **DV-028**
    (vendoring `math-audit-mcp` — R36 decision final). Each row states the
    standing governance mechanism and "no further re-audit gate".
  - **Standing-external-disposition** authored for **DV-001** (Linux Triton
    runner — plus a dormant `.github/workflows/gpu-triton.yml` skeleton gated
    on `[self-hosted, linux, gpu]` so runner registration is the sole
    remaining step), **DV-008**, **DV-009**, **DV-011**, **DV-017**,
    **DV-022** — one consolidated evidenced re-verification pass
    (`cargo audit`, `pip-audit`, Snyk, `gh api .../secret-scanning/alerts`,
    runner status, `.snyk` currency) and a per-row "external / third-party,
    not repo-closeable, not a Phase 7 entry blocker" statement.
  - A **new register row** for the `chacha20` yanked advisory under the
    DV-008 governance class (full visibility, threat assessment, compensating
    control, `cargo audit` exit-0 evidence, per-cycle re-check cadence).
  - **DV-010** confirmed owned by WP-038 S1 (the `0149` brief was updated by
    amendment #38); WP-036G does **not** push the tag. **DV-027** recorded as
    routed to EMA-006.
  - **Test-fragility resolution:** the DV-019 Python-side
    `test_process_frame_gradcheck_with_prev_slots` gradcheck sub-item is
    either fixed with a regression guard (confirming the shared root cause
    with `Hotfix-DV019`'s `burn-autodiff` global-server mechanism and applying
    the same serialization guard) **or** a new dedicated DV item is opened
    with a concrete next gate (per DV-019's handoff §6);
    `test_no_gpu_throughput_regression` is either hardened (fixed iteration
    count + warm-up + relative-median gate, with a regression test) **or**
    registered + documented as CI-authoritative with an explicit tolerance.
  - A **Phase 7 entry statement** drafted for the S4 PSR: every remaining
    OPEN DV item enumerated with a one-line assertion that it does not block
    campaign pre-registration (`0153` E0) or execution.
  - `tools/check_dv_register_gates.py` passes; `tools/check_no_python_numerics.py`
    clean (unchanged); `≥95%` coverage on any changed first-party code.
  - No `prin.__all__` / `FROZEN_PUBLIC_API` change.
- **Non-goals:** any new numerics; closing DV-001's Triton comparison or
  DV-006's VitisAI half (both hardware-blocked); the WP-038 tag push (DV-010);
  re-litigating the R36 vendoring decision; `bands.rs`-class Rust autodiff
  flakes (closed by `Hotfix-DV019`); DV-005 (closed as `AMENDED` by amendment
  #38 — record, do not re-open).

## Required reading

- `DOCS/PRIN_Project_Plan.md` §5 (preserved hazards), §8.3 amendments
  #5/#9/#13/#14/#16/#17/#25/#27/#30/#36/#37/#38
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §3/§7;
  `Coding_Standards.md` §6 (advisory governance); `Testing_Standards.md` §1
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` — every open row, and the
  update protocol and "Closed items" structure
- `DOCS/reports/036f-project-state.md`, `036d-project-state.md` §5, and the
  cumulative deviation ledger
- `DOCS/experiments/hotfix-dv019-handoff.md` §6 (Python-side sub-item)
- `DOCS/audits/EXECUTIVE_AUDIT_REPORT_006.md` E-F2; Phase 5 analytics R34/R35
- `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_005.md` §8 (DV-013 sign-off pattern)
- [`WP-036E-036F-036G-execution-plan-and-decomposition.md`](WP-036E-036F-036G-execution-plan-and-decomposition.md) §2 (disposition matrix), §3 (WP-036G), §7 (risk R5)

## Entry conditions

- WP-036F S4 (`0144X`) is closed and committed.
- No unresolved D1/D2 finding exists.
- WP-036G scope, acceptance criteria, and non-goals have maintainer approval
  (Plan amendment #38; PSR-036F §6 hand-off).

## Expected work

1. Run the consolidated re-verification pass; capture all evidence into
   `EVIDENCE/0144Y-wp036g-s1-dv-reverification/`.
2. Draft the per-row disposition text for every open DV item (permanent or
   standing-external), following the DV-004/R35 and DV-021/#30 wording
   pattern; do not edit the register's status cells in a way that trips
   `check_dv_register_gates.py` (avoid the literal "before session NNNN"
   phrasing in gate columns).
3. Add the `chacha20` register row.
4. Add `.github/workflows/gpu-triton.yml` (dormant; `runs-on: [self-hosted,
   linux, gpu]`; documented header comment that it activates on Linux runner
   registration).
5. Resolve or formally document the two test-fragility items, with regression
   tests / explicit tolerances as applicable.
6. Draft the Phase 7 entry statement.
7. Tests in tandem with any code change; record out-of-scope discoveries.

## Required evidence and outputs

- Register disposition drafts, the `chacha20` row, the dormant workflow, and
  any test change in one S1 commit range; `≥95%` coverage on changed
  first-party code (test-hardening only).
- The consolidated re-verification evidence bundle.
- `cargo audit` / `pip-audit` / Snyk / `ruff` / `mypy --strict` /
  `interrogate` / `bandit` / `pytest` / `cargo fmt` / clippy / `cargo test`.
- `DOCS/experiments/0144Y-wp036g-s1-handoff.md` mapping each acceptance
  criterion to evidence, including the per-item disposition class.

## Prohibited

- New numerics or public API; closing a hardware-blocked half; pushing the
  WP-038 tag; weakened assertions/tolerances to make a fragile test "pass"
  without a documented rationale; finding suppression; editing a DV status
  cell to `CLOSED` without the evidence chain; unregistered experimentation.

## Exit gate

All S1 gates green; every open DV item has a drafted dated disposition; the
`chacha20` row and dormant Triton workflow exist; the two test-fragility
items are resolved or formally documented; `check_dv_register_gates.py`
passes; the Phase 7 entry statement is drafted. Hand off to the mandatory S2
audit `0144Z`.
