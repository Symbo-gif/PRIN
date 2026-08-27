# Session 0141E — WP-036 S1 (sub-pass 5/5): Consolidation — Migration Guide table, smoke matrix, traceability, handoff

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036
**Session type:** S1 — Coding
**Predecessor:** [0141D — net-new Python surface](0141D-wp036-s1d-net-new-python-surface.md)
**Successor:** [0142 — WP-036 S2 Audit](0142-wp036-s2-api-completion-acceptance-suite-and-migration.md)
**Authority:** Project Plan §6/§8, amendments #31/#32, the decomposition plan
[`WP-036-S1-execution-plan-and-decomposition.md`](WP-036-S1-execution-plan-and-decomposition.md). Standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Close WP-036 S1: assemble the consolidated **172-row** Migration Guide symbol
table, machine-check it against `DOCS/baselines/wp001_api_traceability.md`,
prove every one of the 172 `prinet.__all__` symbols resolves from `prin` and
passes a construct/callable smoke check, regenerate the traceability matrix,
and write the S1 handoff note mapping every acceptance criterion to evidence.

## Contract

- **Acceptance (the full WP-036 S1 acceptance criteria — 0141 brief Contract):**
  - Every one of the 172 `prinet.__all__` symbols resolves from `prin` and
    passes a construct/callable smoke check (full parametrized matrix).
  - `verify_api_surface` regression test green against PRIN's RC1 `__all__`.
  - The Migration Guide table (all 172 rows: `prinet.<symbol>` →
    `prin.<symbol>` / renamed / GPU-only stub / documented disposition) is
    machine-checked against `DOCS/baselines/wp001_api_traceability.md` by a
    committed test — no silent removals.
  - No Python numerics introduced anywhere in the 0141A–0141E range
    (Coding Standards §2.1) — evidenced by an AST/grep check.
  - Traceability matrix regenerated (`tools/wp001_*`); `tools/check_*` gates
    pass.
  - The D-D per-symbol disposition appendix is complete and final (S2 veto).
  - S1 handoff note: every acceptance criterion → evidence, plus the
    parity-evidence disposition for every new binding.
- **Non-goals:** the acceptance-suite port (WP-036B/C); final documentation
  prose (WP-037); release publishing.

## Required reading

- The running S1 handoff draft accumulated across 0141A–0141D
- `DOCS/standards/Documentation_Standards.md` §7; `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §S1 exit
- `DOCS/baselines/wp001_api_traceability.md` and `tools/wp001_ownership.json`
- `DOCS/sphinx/migration_guide.rst`
- Latest PSR and cumulative deviation ledger

## Entry conditions

- 0141A–0141D committed; all covered symbols importable.
- No unresolved D1/D2 finding exists.

## Expected work

1. Build the 172-row table; add the machine-check test.
2. Add the full 172-symbol smoke matrix test.
3. Add the no-Python-numerics AST/grep regression check for the touched tree.
4. Regenerate traceability; run `tools/check_deviation_ledger.py`,
   `tools/check_dv_register_gates.py`, `tools/wp001_baseline.py check`.
5. Finalize the D-D appendix and the S1 handoff note.
6. Run the complete local gate over the whole 0141A–0141E range.

## Required evidence and outputs

- The table, machine-check test, smoke matrix, and numerics check in this
  commit; ≥95% coverage on new/changed code.
- Full local gate (Rust + Python) reproduced and recorded for the whole range.
- `DOCS/experiments/0141-wp036-s1-handoff.md` (final) and
  `DOCS/experiments/0141-wp036-s1-dd-dispositions.md` (final).
- Sphinx `-W` build clean with the new Migration Guide table rendered.

## Prohibited

- Deferred tests, weakened assertions, undocumented public API, Python
  numerics, hidden RNG, scope creep, unregistered experimentation, S1
  self-certification of completion.

## Exit gate

The full WP-036 S1 local gate is green and every acceptance criterion is
evidence-mapped in `DOCS/experiments/0141-wp036-s1-handoff.md`. Commit
locally. Hand off to the mandatory S2 audit (0142) — S1 may not self-certify.
The contiguous `0141`+`0141A`–`0141E` range is pushed once with 0142.
