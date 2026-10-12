# Session 0160 — EXP-002 / C1 E2: Review and approval — API, benchmark-result, and reproduction parity

**Status:** COMPLETE — EXP-002 APPROVED 2026-10-12 UTC under the maintainer's delegated E2 decision authority; decisions, reasons and the E3 entry checklist in [e2-review.md](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/e2-review.md)
**Roadmap phase:** 7 — Experimentation campaign and stable release
**Execution unit:** EXP-002 / C1
**Session type:** E2 — Review and approval
**Predecessor:** [0159 — Pre-registration](0159-exp002-e1-api-benchmark-result-and-reproduction-parity.md)
**Successor:** [0161 — Execution](0161-exp002-e3-api-benchmark-result-and-reproduction-parity.md)
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Public API mapping, legacy benchmark conclusion equivalence, and byte-comparable figure/table regeneration.

## Contract

- **Acceptance:** PRIN's public surface satisfies its own frozen contract — `verify_api_surface(__all__)` returns empty missing and extra sets for the frozen 175-symbol `prin.__all__` — and, as a separately required comparison, all 175 symbols are mapped against the frozen PRINet 3.0 canonical `__all__` (172 symbols); all historical scientific conclusion orderings remain unchanged; the 14 figures × 2 formats + 11 tables = 39 generated files are compared exactly, and the 172 legacy JSON inputs are verified against the `paper/artefact_manifest.json` records.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** PRIN's public surface satisfies its own frozen contract — `verify_api_surface(__all__)` = `(set(), set())` for the frozen 175-symbol `prin.__all__` — and, as a separately required comparison, all 175 symbols are mapped against the frozen PRINet 3.0 canonical `__all__` (172 symbols); all historical scientific conclusion orderings remain unchanged; the 14 figures × 2 formats + 11 tables = 39 generated files are compared exactly, and the 172 legacy JSON inputs are verified against the `paper/artefact_manifest.json` records (campaign plan §2.1).
- **Failure/abort boundary to formalize:** Missing symbols, changed scientific conclusions, or unexplained artefact mismatch is a D1; corrupt source artefacts abort.
- **Raw artefact root:** `benchmarks/results/EXP-002/`
- **Record root:** `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/`

## Entry conditions

- E1 draft is committed; no execution or result inspection has occurred.

## Reconciliation pointer (session 0159 E1, 2026-10-11)

The E1 artefacts under review are the lead-authored DRAFT
[preregistration](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/preregistration.md)
and driver (`benchmarks/campaign/exp002_driver.py`, synthetic-fixture
tested). Review must resolve — without advancing approval status here —
the preregistration §10 E2 items, notably: the 175-symbol PRIN `__all__`
contract versus the separate frozen 172-name PRINet 3.0 reference contract
(three PRIN additions); the 14 figures × 2 formats + 11 tables = 39-file
output census versus the 172-record `paper/artefact_manifest.json` input
population; the tested driver's provenance/admission/abort guards; and the
scientific review requirements of §10 (approval cannot precede closure of
driver/review findings). The lead-authored
[e2-review-packet](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/e2-review-packet.md)
assembles the reviewed source, hashes, methods, validation results and the
five decision gates for the maintainer's independent review (PREPARED FOR
REVIEW — NOT APPROVED; its existence does not start E2 or approve E1).

## Expected work — independent review

1. Review falsifiability, quantitative decision rules, expected-result basis,
   failure/abort criteria, fairness controls, power/seed count, statistics,
   hardware feasibility, and artefact plan.
2. Resolve review findings before approval; log every pre-execution amendment.
3. Record maintainer name/date and set status APPROVED; freeze content at the
   instant E3 starts.

## Prohibited

Approval with missing expected results/failure conditions, or execution before
signed approval.

## Exit gate

Approved pre-registration is committed and frozen; E3 is authorized.
