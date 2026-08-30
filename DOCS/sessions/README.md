# PRIN Session Execution Plan

**Status:** Normative execution ledger  
**Coverage:** Project execution start through stable `1.0.0` completion  
**Planned sessions:** **198** integer + **8** sub-sessions `0144A`–`0144H` (plan amendment #31) + **5** sub-sessions `0141A`–`0141E` (plan amendment #32) = **211**, **+ 4 sub-sessions pending (WP-036A `0144A`–`0144D`, plan amendment #33, adopted 2026-08-29, mechanical renumber not yet executed) = 216 on execution**  
**Current entry point:** [Session 0001](phase-0/0001-wp001-s1-foundation-baseline-and-traceability.md)  
**Master order/status register:** [`SESSION_REGISTER.md`](SESSION_REGISTER.md)

This directory turns the project roadmap into individually addressable session
contracts. There is one Markdown file for every currently planned collaborative
session, from the first governed Foundation session through the final stable
release. It is the prospective answer to **what must happen next**; actual
results and completion evidence remain in `DOCS/audits/`, `DOCS/reports/`,
`DOCS/experiments/`, CI, and benchmark artefacts.

## 1. Authority and interpretation

The authority order is:

1. `DOCS/PRIN_Project_Plan.md`.
2. Normative standards in `DOCS/standards/`.
3. The latest approved Project State Report (actual position and deviations).
4. This Session Execution Plan (prospective sequencing and expectations).
5. Operational `.windsurf/workflows/` checklists.

A lower item never overrides a higher one. If reality justifies a different
future path, amend the plan/standard/session brief openly, record the amendment,
and update the register during S4. **Never make the code fit a stale brief, and
never change a brief silently to hide code drift.**

## 2. Complete execution shape

| Stage | Execution units | Numbered sessions | Governing pattern |
|---|---:|---:|---|
| Phase 0 — Foundation | WP-001…WP-005 | 0001–0020 | S1 → S2 → S3 → S4 per WP |
| Phase 1 — Dynamics core | WP-006…WP-011 | 0021–0044 | S1 → S2 → S3 → S4 per WP |
| Phase 2 — Advanced numerics/simulation | WP-012…WP-016 | 0045–0064 | S1 → S2 → S3 → S4 per WP |
| Phase 3 — GPU kernels | WP-017…WP-021 | 0065–0084 | S1 → S2 → S3 → S4 per WP |
| Phase 4 — Trainable stack/bridge | WP-022…WP-027 | 0085–0108 | S1 → S2 → S3 → S4 per WP |
| Phase 5 — Daemon/experiment tooling | WP-028…WP-032 | 0109–0128 | S1 → S2 → S3 → S4 per WP |
| Phase 6 — Benchmarks/repro/docs/RC1 | WP-033…WP-038 (WP-036 split into WP-036/036B/036C, amdt #31; WP-036 S1 → `0141A`–`0141E`, amdt #32; WP-036A `0144A`–`0144D` inserted, amdt #33) | 0129–0152 + `0141A`–`0141E` + `0144A`–`0144H` (+ `0144A`–`0144D` WP-036A on execution) | S1 → S2 → S3 → S4 per WP |
| Phase 7 campaign planning | Campaign E0 | 0153 | Approval before science |
| Phase 7 confirmatory campaign | EXP-001…EXP-008 | 0154–0193 | E1 → E2 → E3 → E4 → E5 per experiment |
| Campaign synthesis | Campaign E6 | 0194 | Evidence reconciliation |
| Stable release closure | WP-039 | 0195–0198 | S1 → comprehensive S2 → S3 → S4/release |

No calendar estimates are assigned. Progress is evidence-gated, not date-gated.
Phases 2 and 3 are architecturally parallelizable in the project plan, but this
register serializes them by default to preserve the one-WP-in-flight rule.
Parallel execution requires an approved amendment, disjoint scopes, and separate
audit trails.

## 3. Mandatory session rules

### Development cycles (S1–S4)

- **S1 Coding:** code and tests in tandem; scope only; ≥95% changed-code
  coverage; parity/property/gradcheck/kernel tests as applicable; all quality,
  security, typing, and documentation gates met at write time.
- **S2 Audit:** read-only source inspection against A1–A10; evidence-backed
  Audit Report; every finding receives ID/severity/clause/remedy.
- **S3 Remediation:** findings only; regression tests; amendments only with
  approval; CLEAN delta re-audit. **S3 is mandatory even when S2 reports zero
  findings**—it records no-change closure and independent delta verification.
- **S4 Documentation:** affected READMEs, CHANGELOG, API/Sphinx/Migration docs,
  warning-free documentation gates, Project State Report, next-session
  activation, phase tag where applicable.

A session may not self-certify its successor's entry conditions.

### Scientific campaign (E0/E1–E5/E6)

- **E0:** approve/freeze campaign order, resources, schemas, hardware matrix,
  and escalation rules.
- **E1:** pre-register quantitative hypotheses, expected direction/magnitude,
  falsification and abort criteria, controls, sample/statistics plan, and
  outputs **before viewing results**.
- **E2:** independent review and maintainer approval; protocol freezes at E3.
- **E3:** execute only registered drivers; append-only artefacts and complete
  environment/log capture; no interpretation.
- **E4:** run registered analysis; exploratory work is explicitly separated.
- **E5:** report every outcome with effect sizes/CIs, expected-vs-observed
  table, deviations, threats, and artefact index.
- **E6:** synthesize all evidence and confirm no unresolved D1 remains.

Any C1–C3 scientific conclusion reversal or normative requirement breach is a
D1 and inserts a complete correction cycle from `contingencies/` before the
next numbered session.

## 4. Session activation and status

Each session starts as `PLANNED`; **Session 0001 alone starts `READY`** under
the bootstrap declaration and maintainer-requested plan amendment #2. Permitted
status transitions are:

```text
PLANNED → READY → IN_PROGRESS → BLOCKED (optional) → COMPLETE
```

- S4 updates the completed cycle's session files and the Master Session Register
  from committed evidence; experiment E5 does the same for its E1–E5 block.
- `COMPLETE` requires the brief's exit gate—not merely elapsed work.
- `BLOCKED` names the blocking finding/experiment/resource and its owner.
- The latest Project State Report is authoritative if a status display becomes
  stale; stale register status is a D4 finding (D2 if it could authorize work
  incorrectly).

## 5. File and artefact conventions

Session briefs are named:

```text
NNNN-wpNNN-sK-title.md
NNNN-expNNN-eK-title.md
```

- `NNNN`: immutable global sequence. Plan amendment #31 additionally permits a
  two-part `NNNNX` form for planned sub-sessions inserted between two integer
  sessions by an approved amendment, without renumbering the 0001–0198 integer
  sequence — the same additive-by-amendment principle as the EA/EMA global
  sessions, applied inside the phase order. In use: `0144A`–`0144H` (WP-036B/C
  mini-cycles, amendment #31), `0141A`–`0141E` (WP-036 S1 coding sub-passes,
  amendment #32), and `0144A`–`0144D` (WP-036A trainable compatibility layers,
  amendment #33; pending mechanical renumber — existing WP-036B/C sessions
  shift to `0144E`–`0144H`/`0144I`–`0144L` when WP-036A is declared).
- `WP-NNN`: development work package; four consecutive S1–S4 files.
- `EXP-NNN`: campaign experiment; five consecutive E1–E5 files.
- Each brief specifies predecessor, successor, mission, acceptance criteria,
  non-goals, entry conditions, work/evidence expectations, prohibitions, and
  exit/handoff gate.
- Audit/State Report numbering matches WP numbering, not global session number.

## 6. Collaboration responsibilities

- **AI pair (Cascade):** read the active brief and authoritative context;
  execute/draft within scope; gather reproducible evidence; disclose
  uncertainty; never advance status without satisfying gates.
- **Maintainer:** approve WP activation, audit verdicts, amendments,
  pre-registrations, experiment reports, phase exits, and releases.
- **Both:** stop on scope ambiguity, D1/security/reproducibility risk, or an
  unmet entry condition; preserve a repository-only trail sufficient for a new
  collaborator with no chat history.

## 7. Amendment and contingency protocol

Future briefs are precise plans, not immutable guesses. A change to future
scope/order requires:

1. A documented rationale tied to evidence.
2. Maintainer approval.
3. The appropriate plan/standard amendment when trajectory changes.
4. Updates to all affected briefs, phase index, traceability matrix, and Master
   Session Register in the same S4 documentation closure.
5. A CHANGELOG entry.

Unexpected correction sessions use [`contingencies/`](contingencies/README.md).
Inserted sessions receive a correction WP ID and dated copied briefs; they do
not renumber the 198 planned sessions.

## 8. Navigation

- [`SESSION_REGISTER.md`](SESSION_REGISTER.md) — exact global order and links.
- [`TRACEABILITY.md`](TRACEABILITY.md) — requirements/risks/DoD to session map.
- [`phase-0/`](phase-0/README.md) through [`phase-7/`](phase-7/README.md) — phase
  indexes and individual briefs.
- [`contingencies/`](contingencies/README.md) — conditional correction-cycle
  templates.
