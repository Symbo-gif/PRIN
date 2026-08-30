# Session 0144E — WP-036B S1: Coding — Acceptance suite port (core, dynamics, model stack, subconscious)

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036B
**Session type:** S1 — Coding
**Predecessor:** [0144 — Documentation](0144-wp036-s4-api-completion-acceptance-suite-and-migration.md)
**Successor:** [0144F — Audit](0144F-wp036b-s2-acceptance-suite-port-core-dynamics-model-stack.md)
**Authority:** Project Plan §6/§8 and amendment #31; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Port the first half of the PRINet 3.0 acceptance suite — reference test files
`test_core`, `test_utils`, `test_phases`, `test_hierarchical`,
`test_phase_to_rate`, `test_q2`, `test_q2_remaining`, `test_q3_new`, `test_nn`,
`test_scalr_enhanced`, `test_hybrid`, `test_clevr_n`, `test_subconscious`
(~805 `def test_` functions) — into `tests/` against the `prin` compatibility
surface delivered by WP-036, adapting imports only.

## Contract

- **Acceptance:** Every ported test in scope passes on CPU, Linux + Windows,
  Python 3.11–3.13. Assertions are unchanged from the reference except where a
  failure is attributable *solely* to a documented preserved numerical hazard
  (amendments #14/#16/#17/#25), in which case a per-test tolerance annotation
  is added and recorded in the Parity Report — never a deletion, skip, or
  weakened logical assertion. Purely GPU/Triton reference tests in these files
  are `skipif`-guarded on backend availability (reference-suite precedent).
- **Non-goals:** New `prin` public symbols (WP-036 owns those; a genuine gap is
  an out-of-scope discovery recorded for WP-036 follow-up, not silently filled
  here); the integration/y-series/kernel clusters (WP-036C); final
  documentation prose or release publishing.

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendment #31
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- `DOCS/standards/Testing_Standards.md` §1 (esp. §1.1 "adapt imports only")
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- `DOCS/sphinx/parity_report.rst` and the parity-tolerance governance mechanism
- WP-036's S1 handoff note and its Migration Guide symbol table
- `DOCS/sessions/phase-6/WP-036-execution-plan-and-decomposition.md` §2.5, §3 (D-A)

## Entry conditions

- WP-036 S4 (0144) is closed and committed; the `prin` compatibility surface
  resolves all 172 `prinet.__all__` symbols.
- No unresolved D1/D2 finding exists.
- WP-036B scope, acceptance criteria, and non-goals have maintainer approval.

## Expected work

1. Copy each reference test file into `tests/` under a stable name; rewrite
   `from prinet...` / `import prinet` to the `prin` equivalents per the
   Migration Guide symbol table. No other edit to test logic.
2. Run the ported subset; triage every failure as (a) a real PRIN defect →
   fix in the owning crate/module with a regression test, or record as an
   out-of-scope discovery if it needs a new public symbol; (b) a documented
   preserved-hazard tolerance case → per-test annotation + Parity Report entry;
   (c) a GPU/Triton-only case → `skipif` guard.
3. Keep numerical authority in Rust; add no Python numerics.
4. Preserve deterministic `Seed` flow; no hidden RNG.
5. Record every tolerance annotation and every out-of-scope discovery.

## Required evidence and outputs

- Ported test files and any fix commits in the same S1 commit range.
- Coverage does not decrease on `main`; ≥95% on any changed first-party code.
- `ruff`, `ruff format --check`, `mypy --strict` (where applicable to test
  helpers), `pytest` for the ported subset, `bandit`, dependency audits.
- A Parity Report delta listing every added tolerance annotation with its
  hazard attribution.
- An S1 handoff note mapping each reference test file to: ported / count /
  tolerance annotations / skips / discoveries.

## Prohibited

- Deferred tests, weakened or deleted assertions, tolerance drift not tied to a
  documented hazard, undocumented public API, duplicated Python numerics,
  hidden RNG, unapproved `unsafe`, scope creep into WP-036C or new-symbol work,
  or unregistered experimentation.

## Exit gate

All S1 gates are green and every acceptance criterion is evidence-mapped. Hand
off to the mandatory S2 audit; S1 may not self-certify completion.
