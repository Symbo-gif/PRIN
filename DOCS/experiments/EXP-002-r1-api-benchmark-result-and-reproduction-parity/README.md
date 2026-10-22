# EXP-002-r1 — API, benchmark-result, and reproduction parity, re-run (track C1)

**Status:** **E5 REPORTED (2026-10-22 UTC, branch `campaign/exp002-r1-e5`) — NON-REVERSAL VERDICT (H1 CONFIRMED, H2 CONFIRMED, H3 CONFIRMED under approved §5.4 policy, H4 CONFIRMED; D1 = False). Stage complete; awaiting maintainer verification and acceptance.**
Created as a skeleton by `EXP-002-D1` S4 (2026-10-16 UTC) under campaign plan
§10.4 item 4; E1 declared by the maintainer 2026-10-20 UTC after settling the
pre-E1 open decisions below. [`preregistration.md`](preregistration.md) is
`DRAFT`; [`benchmarks/campaign/exp002_r1_driver.py`](../../../benchmarks/campaign/exp002_r1_driver.py)
refuses execution until `EXP-002-r1-E2` records scientific approval.

**Drafting AI pair:** Qwen3.8-max (S4 skeleton); Devin (`EXP-002-r1` E1 protocol,
driver, tests, and handoff/review packet). Every later E-stage document names
its own drafting AI pair and records the maintainer's verification (campaign
plan §12 item 7; Experimentation Standards §4).

**Predecessor:** [`EXP-002`](../EXP-002-api-benchmark-result-and-reproduction-parity/README.md)
(E5 reported 2026-10-14 UTC, verified and accepted 2026-10-15 UTC; H1, H2, H4
`CONFIRMED`; **H3 `REFUTED`**, campaign plan §10.4 **D1** raised).
**Correction cycle:** [`DOCS/audits/2026-10-15-exp002-d1-correction-audit.md`](../../audits/2026-10-15-exp002-d1-correction-audit.md)
(S1 complete, S2 `PASS-WITH-FINDINGS`, S3 delta re-audit `CLEAN`, S4 closure
appended, PR #34 merged at `305416fb0f85e690b12640b3f32fad48b55d9077`, PR #35
merged at `5677858c15d784d881b23d43dff5029d199b0a18`).
**Campaign plan row:** [`campaign-plan.md`](../campaign-plan.md) §2.1 EXP-002 / C1
(this re-run inherits that row's reconciled targets; it is not a new registry
entry and no session number changes).
**Isolated raw-artefact root:** [`benchmarks/results/EXP-002-r1/`](../../../benchmarks/results/EXP-002-r1/README.md)
(never `benchmarks/results/EXP-002/`).
**Isolated generated-output root (gitignored):**
`DOCS/test_and_benchmark_results/EXP-002-r1/` (never
`DOCS/test_and_benchmark_results/EXP-002/`).
**Isolated stage evidence root:**
[`EVIDENCE/exp002-r1-e1/`](../../../EVIDENCE/exp002-r1-e1/README.md) (and
`-e2`..`-e5` for subsequent stages).

This is a **new experiment record** per campaign plan §10.4 item 4. The
original `EXP-002` record is **immutable**: its verdicts, tolerances,
normalization policies, digests, protocol, `preregistration.md` and everything
under `benchmarks/results/EXP-002/` are never edited, and its only post-issue
change is the dated erratum pointer in `report.md` §15 that names this record.
**r1 does not revise `EXP-002`'s `H3 REFUTED` verdict.** Only r1's own E4/E5,
applying r1's own frozen decision rule to r1's own new runs, can produce a new
verdict.

## Why a re-run exists

`EXP-002`'s H3 was refuted on the **PRIN side**: the WP-034 port of nine figure
generators dropped or re-encoded **34 drawing arguments**, so 18 of the 39
registered publication files (the `.pdf` and `.png` of figures 5, 7, 8, 9, 10,
11, 12, 14, 15) differed from an independent render by the frozen
`prinet==3.0.0` reference generator. The `EXP-002-D1` correction cycle fixed
the port and attributed every differing byte by controlled substitution on the
frozen reference, with **0 unexplained** — so campaign plan §10.4 item 3 (the
"the 3.0 conclusion was itself defective" route, which needs an EMA-style
mathematical audit) was **not** invoked and is not available to r1.

On the corrected generator, measured after the fix
([`EVIDENCE/exp002-d1-s2/both-policies-post-fix.txt`](../../../EVIDENCE/exp002-d1-s2/both-policies-post-fix.txt)):

| Comparison policy | Result on the corrected generator |
|---|---|
| Approved §5.4 policy | **39/39 equal** |
| §11.3 pre-exposure sensitivity policy | **14/39 equal** |

All **25** residuals under the sensitivity policy are classified, **0
unclassified**, and every one is a writer or host property rather than a
scientific difference:

- **14 PDFs** differ only in the Info **key set** — the reference writes 3 keys
  including a wall-clock `CreationDate`; PRIN writes 4 fixed keys including
  `ModDate`. PRIN's fixed metadata is what makes its H4 (raw determinism) hold.
- **11 `.tex` tables** differ only in **line terminators** — the reference's
  text-mode writer on Windows emits CRLF; PRIN emits LF.

`EXP-002`'s own verdict is unchanged by any of this and stays `H3 REFUTED`.

## Maintainer-ratified pre-E1 decisions (2026-10-20 UTC)

Before E1 began, the maintainer ratified the three governing decisions that the
S4 skeleton held open:

1. **Re-run (`-r1`/`-rN`) Namespace & Evidence Isolation Rule (campaign plan
   §7.1, §10.4 item 4, §14.2 amendment #10):** `EXP-002-r1` uses completely
   disjoint roots from `EXP-002` (`benchmarks/results/EXP-002-r1/`,
   `DOCS/test_and_benchmark_results/EXP-002-r1/`, `EVIDENCE/exp002-r1-e1/`..`e5/`,
   `exp002_r1_driver.py`, `test_exp002_r1_driver.py`, and at E4
   `exp002_r1_e4_analysis.py`), with `exp_id="EXP-002-r1"`,
   `session="EXP-002-r1-E3"`, and `r1-` run labels. Both the per-root
   `EXP-002-r1` cap and the combined `EXP-002` + `EXP-002-r1` cap are bounded by
   the existing 10 MiB allocation.
2. **Resolution of `EXP002D1-S2-F1` ([`preregistration.md`](preregistration.md)
   §4.1, §5.4, §11.1):** The approved **§5.4 comparison policy** (`CRLF`→`LF`
   table canonicalization + 4-key PDF `/Info` removal and `xref`/`startxref`
   pointer canonicalization + PNG critical-chunk normalization) is registered as
   the **sole primary decision rule for H3**. The **§11.3 pre-exposure policy**
   is retained as a **reported, non-gating writer-property diagnostic**,
   replacing `EXP-002`'s §11.3 item 1 clause with the requirement that every
   residual between §5.4 and §11.3 belong to one of the two registered
   writer/host I/O classes (`pdf_info_keyset` or `tex_crlf_line_terminator`)
   with `0` unclassified residuals. Outcome exposure is disclosed in the
   pre-registration header, §1, and §11.2, and neither writer is altered.
3. **DV-047 closure ([`DEFERRED_VALIDATION_REGISTER.md`](../../reports/DEFERRED_VALIDATION_REGISTER.md)):**
   Removed the stale `.venv/Lib/site-packages/prin_core.pth` (which pointed at
   `C:\dev\PRIN-r1-amendment\python`), rebuilt `python/prin/_prin_core.pyd` from
   clean `main` (`5677858c15d784d881b23d43dff5029d199b0a18`) using
   `maturin develop --release -m crates/prin-py/Cargo.toml` (`9,290,240` bytes,
   SHA-256 `37392d067efa3983e384c94f4ac2268c4fad2f5ea929c529b3db50bff4fee99e`),
   and pinned its SHA-256 and byte size in `exp002_r1_driver.py` and
   `preregistration.md` §1.1.

## Rules inherited from the campaign plan

- This experiment **does not reuse** `EXP-002`'s run IDs, raw root, output root,
  or artefacts (campaign plan §7.1, §10.4 item 4, amendment #10). Every raw
  artefact goes to a **new** `RUN-<UTC>-<SHA>-r1-<label>/` directory under
  `benchmarks/results/EXP-002-r1/` with its own per-run `manifest.json`
  (§7.1–§7.3); `EXP-002`'s five existing `RUN-` directories under
  `benchmarks/results/EXP-002/` are never appended to, edited, or re-manifested.
- Hypotheses, expected results, and failure/abort conditions are committed
  **before** execution (Experimentation Standards §1.1–§1.2).
- Pre-register against the **reconciled** targets in campaign plan §2.1 and cite
  the reconciliation — including amendment #51's **14 verifiable figures**
  (figures 2–15; there was never a figure 1), giving the registered reproduction
  target of **14 figures × 2 formats + 11 tables = 39 generated files** against
  the 172-record `paper/artefact_manifest.json`. Hardware only from §5; seeds
  per §6 (`seed_key = 2`); artefact layout per §7; budget caps per §8;
  statistics per §9; abort/D1 rules per §10.
- One E-stage per session, no stage collapsing (§12 item 2); each stage commits
  on its own `campaign/exp002-r1-<stage>` branch (§12 item 3); drivers are
  authored in E1 with tests in tandem and Snyk Code, approved in E2, and
  **frozen at E3 start** (§12 item 1).
- Analysis scripts under `analysis/` carry **globally unique** file names
  (prefix `exp002_r1_`, i.e. `analysis/exp002_r1_e4_analysis.py` at E4;
  `tests/test_campaign_quality_gates.py`, PR32-F12).

## Carried obligations and E1 dispositions

| Obligation | Source | Status at E1 close |
|---|---|---|
| Rebuild `python/prin/_prin_core.pyd` and remove the stale `prin_core.pth`, recording the new `.pyd` SHA-256 in the driver | **DV-047** | **CLOSED at E1 (2026-10-20 UTC)** — rebuilt at `5677858c` (`9,290,240 B`, SHA-256 `37392d06…ee99e`), pinned and enforced in `exp002_r1_driver.py` |
| Settle the H3 comparison-policy decision and register both policies deliberately | **`EXP002D1-S2-F1`** (D3) | **RATIFIED by maintainer & REGISTERED in `preregistration.md` (§4.1, §5.4, §11.1)** — subject to E2 review and frozen before the first `RUN-` |
| `cargo audit` transitive advisories | **DV-045** | **CLOSED on `main` (`5677858c`, PR #35)** — `cargo audit` exits `0` locally and on hosted `rust` (`39405463375`) |
| `gpu-cuda` intermittent `flops` test failure; re-check on every `gpu-cuda` run | **DV-046** (OPEN) | Re-checked on `gpu` run `39405463413` (`5677858c`): `gpu-cuda` and `gpu-wgpu` both `success` (`0` occurrences); stays OPEN for per-run check |
| Local full-suite contention sensitivity and DV-032 conversion | **O-1 / DV-032** | O-1 corroborated by two consecutive green hosted `nightly.yml` runs (`39203786555`, `39373976832`); DV-032 tests (1) and (2) fixed in required gate, test (3) permanently dispositioned under `nightly.yml` |
| Queued S2-class retro-audit of `EXP002D1-S4-F2` (`814b670c`) and `EXP002D1-S4-F3` (`67100a69`) | Correction audit §S4.16 item 4 | **QUEUED for `EXP-002-r1` E2** — checklist prepared in [`e2-review-packet.md`](e2-review-packet.md) §4 |

## Blocking condition — IN FORCE

Session **`0164`** (EXP-003 E1) and every later campaign session
(**`0165`–`0194`**) are **BLOCKED** under campaign plan §3.3 and §10.4 items
2–5 until this experiment's E5 verdict **is not a reversal** and is
**verified and accepted by the maintainer**, or the maintainer records a Project
Plan §8.3 amendment accepting a changed conclusion with full justification.
E1 completion does **not** release `0164` or authorize E3 execution.

## Current artefacts

| File | Created by | State / Frozen when |
|---|---|---|
| `README.md` | S4 / updated through E5 (this file) | Updated as the experiment progresses |
| [`preregistration.md`](preregistration.md) | E1 / approved E2 | Frozen at `F = 10ac3c04f44a1f68869c94c1dfae1c1c1a189460` at first `RUN-` creation in E3 |
| [`e1-handoff.md`](e1-handoff.md) | E1 | Entry verification, DV-047 closure, and E1 local-gate evidence record |
| [`e2-review-packet.md`](e2-review-packet.md) | E1 | Decision and S4 retro-audit packet for `EXP-002-r1-E2` |
| [`e2-review.md`](e2-review.md) | E2 | Independent review, S4 retro-audit, Lean 4 / Z3 proofs, and approval record |
| [`log.md`](log.md) | E3 | Five registered runs executed; frozen at E3 close |
| [`analysis/`](analysis/) | E4 | Committed analysis module [`analysis/exp002_r1_e4_analysis.py`](analysis/exp002_r1_e4_analysis.py) and deliverables |
| [`analysis.md`](analysis.md) | E4 | E4 analysis record: all hypotheses confirmed, D1 flag not raised (`False`) |
| [`report.md`](report.md) | E5 | Authoritative E5 report: non-reversal verdict, retained-bytes verification, clean-worktree regeneration, clean-checkout reconstruction |
| [`report-manifest.json`](report-manifest.json) | E4 / verified E5 | SHA-256 manifest of regenerated outputs, input manifests, and publication files (`6cd12f2d…`) |
