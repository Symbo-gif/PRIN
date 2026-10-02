# PRIN Project State Report — Cycle NNN

**Date:** YYYY-MM-DD
**Cycle:** NNN (WP-NNN "<title>")
**Completed sessions:** <global IDs NNNN–NNNN>
**Author:** <AI pair (Cascade), approved by maintainer name>
**Git state:** main @ <SHA>

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** <Phase K — name> (<n of m> WPs complete)
- **This cycle delivered:** <one-paragraph summary>
- **Plan conformance:** <ON TRAJECTORY | ON TRAJECTORY WITH AMENDMENTS | DEVIATING (explain)>
- **Audit:** `DOCS/audits/NNN-wpNNN-audit.md` — verdict <…>, findings <n>,
  all closed <YES/NO>
- **Session Register:** <completed IDs marked COMPLETE; successor ID marked READY>

## 2. Metric trends

| Metric | Previous | Current | Gate |
|---|---|---|---|
| Rust tests passing | | | 100% |
| Python tests passing | | | 100% |
| Coverage (new/changed code) | | | ≥95% |
| Docstring coverage (interrogate) | | | ≥95% overall, 100% public |
| Parity cases passing / total defined | | | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit findings | | | 0 |
| Benchmark regression gates | | | none tripped |

## 3. Deviation ledger (cumulative)

Two accepted forms (enforced by `tools/check_deviation_ledger.py`):

- **Full snapshot** — carry every prior row plus this cycle's additions in
  the six-column table below.
- **Delegated delta** — state `**Cumulative ledger delta:** Inherit
  PSR-NNN §3` in prose, then list ONLY this cycle's new/updated rows in the
  six-column table below. An inherited ID may be restated only to update
  Status/Reference; its Summary must stay identical or the row is a new
  finding with a new ID. A five-column `ID | Severity | ...` table is a
  local finding summary, never a ledger.

| ID | Raised (cycle) | Severity | Summary | Status | Reference |
|---|---|---|---|---|---|
| WPNNN-F1 | NNN | D2 | | FIXED / AMENDED / CARRIED(1) | commit/amendment |

## 4. Plan amendments this cycle

| Amendment | Plan/standard section | Rationale | Approved by |
|---|---|---|---|

## 5. Risks and blockers

<top risks from the plan register that moved; new risks; blockers>

## 6. Next work package declaration — WP-NNN+1

- **Title:**
- **Scope (files/crates/modules):**
- **Plan sections advanced:**
- **Acceptance criteria:** <tests, parity cases, docs, perf targets>
- **Non-goals:**
- **First session brief:** `DOCS/sessions/phase-N/NNNN-wpNNN-s1-<slug>.md`
- **Maintainer approval:** <name / date>
