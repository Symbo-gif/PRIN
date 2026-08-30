# Session 0143 — WP-036 S3: Remediation — API completion, acceptance suite, and migration

**Status:** COMPLETE
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036
**Session type:** S3 — Remediation
**Predecessor:** [0142 — Audit](0142-wp036-s2-api-completion-acceptance-suite-and-migration.md)
**Successor:** [0144 — Documentation](0144-wp036-s4-api-completion-acceptance-suite-and-migration.md)
**Findings remediated:** WP036-F1 FIXED (5 new branch-coverage tests), WP036-F2 AMENDED (process deviation acknowledged). Delta re-audit: CLEAN.
**Authority:** Project Plan §6/§8 and **amendment #31**; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

> **Scope note (amendment #31):** WP-036 covers the compatibility surface,
> freeze machinery, stubs, DV-012 bindings, and Migration Guide symbol table.

## Mission

Remediate every finding in `DOCS/audits/036-wp036-audit.md` against the WP-036
compatibility-surface scope; no feature work.

## Contract

- **Acceptance:** Every finding ends FIXED or AMENDED; CLEAN delta re-audit;
  the 172-symbol resolve/smoke check and `verify_api_surface` stay green.
- **Non-goals:** The acceptance-suite port; final documentation prose or
  release publishing.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/036-wp036-audit.md` and every cited violated clause

## Entry conditions

- S2 verdict is acknowledged and its finding list is immutable except for
  appended closure information.

## Expected remediation

1. Process every finding D1→D4; do no feature work.
2. Commit each correction with its finding ID and add a regression test where applicable.
3. Use an approved, logged plan amendment only when justified reality should
   move the trajectory; never normalize drift silently.
4. Re-run affected A1–A10 checks and the WP acceptance evidence after each fix.
5. Append the closure table to `DOCS/audits/036-wp036-audit.md` with FIXED / AMENDED / permitted
   CARRIED(1), commit/amendment reference, and delta evidence.
6. If S2 found nothing, perform and record a no-change delta verification so
   this mandatory session remains explicit and auditable.

## Required outputs

- All finding commits and regression tests.
- Completed closure table and CLEAN delta re-audit.
- Full local gate green with no newly introduced deviation.

## Prohibited

New features, opportunistic refactors, unapproved scope changes, unresolved
D1/D2 findings, or a second carry of any D4.

## Exit gate

Every finding is closed and delta re-audit is CLEAN. Hand off to S4; if not,
repeat remediation/delta verification within this session until clean.

---

## Addendum (2026-08-29) — Owning-WP decision, D-D appendix rows 31–44

The S2 audit's "Required S3 actions" (`DOCS/audits/036-wp036-audit.md` §6,
item 3) listed a third action alongside WP036-F1/F2: "Owning-WP decision
(rows 31–44): Maintainer to declare at PSR-036 or before WP-036B/C starts."
The closure table above (§7, as originally appended) closed only WP036-F1 and
WP036-F2; the Owning-WP item was left open through S3, S4 (PSR-036 §5), and
the D-D dispositions appendix's unresolved veto question 5. WP-036B S1
(session `0144A`) has not yet started, so the audit's alternate deadline
("or before WP-036B/C starts") has not passed — this addendum records the
maintainer's decision before that gate, in the same slot the finding-closure
table would have used had the decision been available at original S3 close.

**Decision — recorded as Project Plan amendment #33:**

- **`DiscreteDeltaThetaGamma` (row 43):** owned by **WP-036B S1 (`0144A`)**.
  Its Rust core (`prin_train::bands::DiscreteDeltaThetaGamma`, WP-022) is
  already audited and exists; only the PyO3 marshalling bridge is missing.
  Binding an existing audited owner needs no new numerics and is not "a new
  `prin` public symbol" (the symbol already resolves as a D-2.2 stub) — so
  fixing it in-line when `0144A`'s `test_hierarchical`/`test_q3_new` port
  first exercises it does not trip WP-036B's non-goal against new-symbol work.
- **The remaining 13 symbols (rows 31–42, 44):** `FeedforwardInhibition`,
  `DentateGyrusConverter`, `DGLayer`, `oscillatory_weight_init`,
  `PhaseToRateConverter`, `PhaseToRateAutoencoder`, `DenseAutoencoder`,
  `SparsityRegularizationLoss`, `HierarchicalResonanceLayer`,
  `PhaseAmplitudeCouplingLayer`, `PRINetModel`, `compile_model`,
  `DiscreteDeltaThetaGammaLayer` are trainable `nn.Module`s with **no
  existing Rust owner** — a faithful rebuild is new `prin-train` numerics,
  which is out of scope for WP-036 (compat surface, no numerics) and for
  WP-036B/C (test-porting only, no numerics; explicit non-goal against new
  public symbols). These are assigned to a **new work package, WP-036A**
  ("Trainable compatibility layers — `prin-train` extension"), sequenced to
  execute and close **before** WP-036B S1 ports `test_hierarchical`,
  `test_phase_to_rate`, `test_q2`, `test_q2_remaining`, `test_q3_new`,
  `test_nn`, and `test_hybrid` — the WP-036B clusters these 13 symbols gate.
  Porting those clusters against stubs would force either weakened assertions
  (prohibited, Testing Standards §1.1) or a quarantine large enough to gut
  WP-036B's own deliverable, so sequencing WP-036A first is preferred.
  WP-036C is unaffected (none of rows 31–44 fall in its test clusters).

Full rationale, symbol-to-cluster mapping, and the session-numbering
mechanism (`0144A`–`0144D` reassigned to WP-036A; existing WP-036B/C sessions
shift to `0144E`–`0144H`/`0144I`–`0144L`) are recorded in Project Plan §8.3
amendment #33. The mechanical file rename and the four new WP-036A session
briefs are **not executed here** — consistent with how amendment #31's own
renumber was executed as a later, dedicated step rather than inside the
decision record — and are the first required action of WP-036A's declaration.

This closes the S2 audit's Required S3 action 3 and D-D appendix veto
question 5. `DOCS/audits/036-wp036-audit.md`, `DOCS/reports/036-project-state.md`,
and `DOCS/experiments/0141-wp036-s1-dd-dispositions.md` are updated to
reference amendment #33 in the same commit as this addendum.
