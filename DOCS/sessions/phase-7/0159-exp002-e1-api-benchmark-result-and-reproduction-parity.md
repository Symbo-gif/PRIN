# Session 0159 — EXP-002 / C1 E1: Pre-registration — API, benchmark-result, and reproduction parity

**Status:** COMPLETE — **E1 exit accepted by MichaelMaillet 2026-10-12 UTC** ("Accept the E1 exit."; record: [e2-review.md](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/e2-review.md) §5). **Released 2026-09-29 UTC; began 2026-10-11 UTC.** This session had been
blocked by the campaign plan §10.4 D1 that EXP-001 raised at E5 (session 0158).
Both release conditions are now met: the four contingency correction sessions
closed (S1→S4, 2026-09-27), and `EXP-001-r1` returned a **non-reversal** E5
verdict — all five hypotheses `CONFIRMED`, D1 flag not raised — which
MichaelMaillet verified and accepted on 2026-09-29 UTC, meeting E5's exit gate
(campaign plan §3.3, §10.4 items 2–5). No Project Plan §8.3 amendment was
needed. See
[`EXP-001-r1/report.md`](../../experiments/EXP-001-r1-golden-trajectory-numerical-parity/report.md)
§1, §8 and §13. **Note for this session's entry evidence:** record the EXP-001-r1
E1–E5 merge SHA and paste `check_ci_green.py <merge-SHA>` output (campaign plan
§12 item 3); DV-040's re-audit gate falls at EXP-002 E4 (session 0162), and
`EXP-001-r1` report §9 item 11 records a histogram-unit labelling defect that
0162's analysis module should not repeat.
**Roadmap phase:** 7 — Experimentation campaign and stable release
**Execution unit:** EXP-002 / C1
**Session type:** E1 — Pre-registration
**Predecessor:** [0158 — Report](0158-exp001-e5-golden-trajectory-numerical-parity.md)
**Successor:** [0160 — Review and approval](0160-exp002-e2-api-benchmark-result-and-reproduction-parity.md)
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Public API mapping, legacy benchmark conclusion equivalence, and byte-comparable figure/table regeneration.

## Contract

- **Acceptance:** PRIN's public surface satisfies its own frozen contract — `verify_api_surface(__all__)` returns empty missing and extra sets for the frozen 175-symbol `prin.__all__` — and, as a separately required comparison, all 175 symbols are mapped against the frozen PRINet 3.0 canonical `__all__` (172 symbols); all historical scientific conclusion orderings remain unchanged; the 14 figures × 2 formats + 11 tables = 39 generated files are compared exactly, and the 172 legacy JSON inputs are verified against the `paper/artefact_manifest.json` records (reconciled to campaign plan §2.1, 2026-10-11).
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** PRIN's public surface satisfies its own frozen contract — `verify_api_surface(__all__)` = `(set(), set())` for the frozen 175-symbol `prin.__all__` — and, as a separately required comparison, all 175 symbols are mapped against the frozen PRINet 3.0 canonical `__all__` (172 symbols); all historical scientific conclusion orderings remain unchanged; the 14 figures × 2 formats + 11 tables = 39 generated files are compared exactly, and the 172 legacy JSON inputs are verified against the `paper/artefact_manifest.json` records (campaign plan §2.1).
- **Failure/abort boundary to formalize:** Missing symbols, changed scientific conclusions, or unexplained artefact mismatch is a D1; corrupt source artefacts abort.
- **Raw artefact root:** `benchmarks/results/EXP-002/`
- **Record root:** `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/`

## Entry conditions

- Campaign plan is approved; predecessor report/correction cycle is closed.
- No result from this experiment has been inspected.

## Expected work — pre-registration only

1. Create `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/preregistration.md` from the template.
2. State quantitative, falsifiable H1…Hn; expected direction, magnitude/range,
   and basis independently for each hypothesis.
3. Convert the registered expectation and failure boundary above into exact
   decision rules, abort criteria, controls, sample/seed plan, alpha, effect
   sizes, CIs, multiple-comparison correction, analysis code/outputs, and budget.
4. Distinguish negative results from invalid/aborted runs and define how both are reported.

## Prohibited

No experiment execution, pilot outcome inspection, post-hoc hypothesis, or
analysis selected after seeing results.

## Exit gate

A complete DRAFT pre-registration is committed and handed to E2.

**Added exit requirement (2026-10-11 added scope):** the adopted governance
amendment (Plan amendment #49), the consistent normative and local updates
implementing it, and the applicable verified evidence are committed. The E1
pre-registration remains a DRAFT — adoption of amendment #49 is not its
scientific approval.

## Added scope — 2026-10-11 (maintainer-authorized)

By maintainer directive of 2026-10-11 UTC, supervised-local-validation
timeout governance is added to this session's existing E1 scope, verbatim:

> “this next session will also add governance that will address the single run timeout issues we had... the way i see it, the tests need to be run, so as long as checks arent snagged then time limits should be removed or significantly extended to reflect the reality of the testing landscape. this governance change will be added to the already planned next session.”
>
> — MichaelMaillet, 2026-10-11 UTC

Adopted as Project Plan amendment #49 (§8.3): `DOCS/standards/Testing_Standards.md`
§7 is the normative policy, cross-referenced from Development Workflow and
Audit Standards §3, Coding Standards §5, Benchmarking and Reproducibility
Standards §2.2, Experimentation Standards §2, the standards README, and
`AGENTS.md`. The acceptance text above was reconciled to the campaign plan
§2.1 registry values in the same edit.

This added scope is supervision governance and bounded session-0159
documentation only. It grants no scientific approval, authorizes no EXP-002
E3 execution, changes no sample/seed/tolerance/threshold or budget
parameter, lifts none of the amendment-#48 hosted-validation pause, and adds
no session IDs or sequence changes.

Under the maintainer's 2026-10-11 authorization — "you are permitted to do
or create what is needed to honestly complete the tasks at hand" —
preparation and testing of the committed, versioned campaign driver that
campaign plan §7.2 and §12 item 1 require of E1 is permitted E1 work. The
driver's scientific rules and exact interface are drafted by the AI pair at
E1, subject to independent review and maintainer scientific approval at
0160; the permission is preparation, never scientific approval. No
experiment decision, analysis module, or experimental run is authorized by
this amendment.
