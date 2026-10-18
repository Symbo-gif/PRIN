# Phase 7 sessions — Experimentation campaign and stable release

These files are prospective execution contracts governed by
`DOCS/standards/Development_Workflow_and_Audit_Standards.md` and the master
[`SESSION_REGISTER.md`](../SESSION_REGISTER.md). Complete them strictly in
sequence; actual evidence belongs in audits/reports/experiment records.

| Seq | Unit | Type | Session brief | Current status |
|---:|---|---|---|---|
| 0153 | Campaign | E0 — Campaign planning | [Approve and freeze Phase 7 campaign plan](0153-campaign-e0-planning.md) | COMPLETE — campaign plan `DOCS/experiments/campaign-plan.md` APPROVED/FROZEN 2026-09-21; EXP-001 E1 authorized; DV-038/DV-039 opened, DV-036 gate executed |
| 0154 | EXP-001 | E1 — Pre-registration | [Golden-trajectory numerical parity](0154-exp001-e1-golden-trajectory-numerical-parity.md) | COMPLETE (historical, as of E1 close) — DRAFT pre-registration `DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/preregistration.md`; H1–H3 driver + tests committed; H4 driver support left pending a `--features cuda` rebuild (§5.4) for E2 review. **Superseded by 0155: H4 closed and pre-registration APPROVED the same day.** |
| 0155 | EXP-001 | E2 — Review and approval | [Golden-trajectory numerical parity](0155-exp001-e2-golden-trajectory-numerical-parity.md) | COMPLETE — pre-registration APPROVED; H4 closed (§5.4); PR #20 code review findings (Devin/CodeRabbit/Copilot) triaged and fixed as a second pre-execution amendment (§5.5) |
| 0156 | EXP-001 | E3 — Execution | [Golden-trajectory numerical parity](0156-exp001-e3-golden-trajectory-numerical-parity.md) | COMPLETE — 4/4 runs, 0 aborted; H1/H2a breaches escalated to E4 |
| 0157 | EXP-001 | E4 — Analysis | [Golden-trajectory numerical parity](0157-exp001-e4-golden-trajectory-numerical-parity.md) | COMPLETE — §8 rule applied: H1 `REFUTED` (485/504), H2a `REFUTED` (897/1,000), H2b/H3/H4 `CONFIRMED`; **campaign plan §10.4 D1 raised**; analysis code + `report-manifest.json` committed; DV-040 opened |
| 0158 | EXP-001 | E5 — Report | [Golden-trajectory numerical parity](0158-exp001-e5-golden-trajectory-numerical-parity.md) | **COMPLETE — report issued 2026-09-23; exit gate open on the correction cycle.** All five verdicts reported (H1/H2a `REFUTED`, H2b/H3/H4 `CONFIRMED`); §10.4 **D1** carried; second D1 **EXP001-E5-F1** raised (the `parity` CI corpus gate does not exercise PRIN, and no gate covers the full 504-case corpus — the only PRIN-vs-corpus gate covers 4 representative cases, none breaching) with a Parity Report erratum; four contingency sessions instantiated; **verified and accepted by the maintainer 2026-09-23 UTC**, E1–E5 PR approved |
| 0159 | EXP-002 | E1 — Pre-registration | [API, benchmark-result, and reproduction parity](0159-exp002-e1-api-benchmark-result-and-reproduction-parity.md) | **COMPLETE — E1 exit accepted 2026-10-12 UTC (released 2026-09-29 UTC, began 2026-10-11 UTC).** The [correction cycle](../contingencies/2026-09-23-exp001-d1-s1-correction-implementation.md) S1→S4 closed 2026-09-27, `EXP-001-r1` returned a **non-reversal** E5 verdict (all five hypotheses `CONFIRMED`, D1 not raised), and MichaelMaillet verified and accepted that report on 2026-09-29 UTC, meeting E5's exit gate. Campaign plan §10.4 item 5's condition is discharged; no Project Plan §8.3 amendment was needed. Proceed in §3's dependency order |
| 0160 | EXP-002 | E2 — Review and approval | [API, benchmark-result, and reproduction parity](0160-exp002-e2-api-benchmark-result-and-reproduction-parity.md) | COMPLETE — EXP-002 APPROVED 2026-10-12 UTC |
| 0161 | EXP-002 | E3 — Execution | [API, benchmark-result, and reproduction parity](0161-exp002-e3-api-benchmark-result-and-reproduction-parity.md) | COMPLETE — 5/5 registered runs executed 2026-10-12 UTC at `fae24c4`, 0 aborted, all manifested and independently validated; no verdict computed (E4 owns it) |
| 0162 | EXP-002 | E4 — Analysis | [API, benchmark-result, and reproduction parity](0162-exp002-e4-api-benchmark-result-and-reproduction-parity.md) | COMPLETE — analysed 2026-10-13 UTC with the committed module `3731fc2`; H1/H2/H4 CONFIRMED, H3 REFUTED (both policies); D1 flag raised |
| 0163 | EXP-002 | E5 — Report | [API, benchmark-result, and reproduction parity](0163-exp002-e5-api-benchmark-result-and-reproduction-parity.md) | **COMPLETE — report issued 2026-10-14 UTC; exit gate open on the triggered D1 correction cycle.** All verdicts reported in full (H1/H2/H4 `CONFIRMED`, H3 `REFUTED` under both approved `21/39` and sensitivity `5/39` policies); §10.4 **D1** carried; retained bytes verified `39/39`, E4 outputs regenerated `8/8` byte-identically, §8.2 reconstruction completed (`prin` `39/39` raw-identical, `reference` `25/39` raw / `39/39` normalized); Parity Report erratum issued; four contingency sessions (`2026-10-14-exp002-d1-s1..s4`) instantiated; **verified and accepted by the maintainer 2026-10-15 UTC** with the `EXP-002-D1` S1 scope approved (acceptance does not release `0164`) |
| 0164 | EXP-003 | E1 — Pre-registration | [CPU scaling and sweep performance](0164-exp003-e1-cpu-scaling-and-sweep-performance.md) | **BLOCKED** — EXP-002 D1 (campaign plan §10.4 items 2 & 5, §3.3); released only after the [correction cycle](../contingencies/2026-10-14-exp002-d1-s1-correction-implementation.md) S1→S4 closes and `EXP-002-r1` returns a non-reversal verdict (or a Project Plan §8.3 amendment is adopted) |
| 0165 | EXP-003 | E2 — Review and approval | [CPU scaling and sweep performance](0165-exp003-e2-cpu-scaling-and-sweep-performance.md) | PLANNED |
| 0166 | EXP-003 | E3 — Execution | [CPU scaling and sweep performance](0166-exp003-e3-cpu-scaling-and-sweep-performance.md) | PLANNED |
| 0167 | EXP-003 | E4 — Analysis | [CPU scaling and sweep performance](0167-exp003-e4-cpu-scaling-and-sweep-performance.md) | PLANNED |
| 0168 | EXP-003 | E5 — Report | [CPU scaling and sweep performance](0168-exp003-e5-cpu-scaling-and-sweep-performance.md) | PLANNED |
| 0169 | EXP-004 | E1 — Pre-registration | [GPU kernels and Torch bridge performance](0169-exp004-e1-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0170 | EXP-004 | E2 — Review and approval | [GPU kernels and Torch bridge performance](0170-exp004-e2-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0171 | EXP-004 | E3 — Execution | [GPU kernels and Torch bridge performance](0171-exp004-e3-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0172 | EXP-004 | E4 — Analysis | [GPU kernels and Torch bridge performance](0172-exp004-e4-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0173 | EXP-004 | E5 — Report | [GPU kernels and Torch bridge performance](0173-exp004-e5-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0174 | EXP-005 | E1 — Pre-registration | [Dynamics, chimera, and capacity replication](0174-exp005-e1-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0175 | EXP-005 | E2 — Review and approval | [Dynamics, chimera, and capacity replication](0175-exp005-e2-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0176 | EXP-005 | E3 — Execution | [Dynamics, chimera, and capacity replication](0176-exp005-e3-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0177 | EXP-005 | E4 — Analysis | [Dynamics, chimera, and capacity replication](0177-exp005-e4-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0178 | EXP-005 | E5 — Report | [Dynamics, chimera, and capacity replication](0178-exp005-e5-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0179 | EXP-006 | E1 — Pre-registration | [Temporal binding, PhaseTracker, and ablation replication](0179-exp006-e1-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0180 | EXP-006 | E2 — Review and approval | [Temporal binding, PhaseTracker, and ablation replication](0180-exp006-e2-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0181 | EXP-006 | E3 — Execution | [Temporal binding, PhaseTracker, and ablation replication](0181-exp006-e3-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0182 | EXP-006 | E4 — Analysis | [Temporal binding, PhaseTracker, and ablation replication](0182-exp006-e4-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0183 | EXP-006 | E5 — Report | [Temporal binding, PhaseTracker, and ablation replication](0183-exp006-e5-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0184 | EXP-007 | E1 — Pre-registration | [Daemon, MOT, and adversarial replication](0184-exp007-e1-daemon-mot-and-adversarial-replication.md) | PLANNED |
| 0185 | EXP-007 | E2 — Review and approval | [Daemon, MOT, and adversarial replication](0185-exp007-e2-daemon-mot-and-adversarial-replication.md) | PLANNED |
| 0186 | EXP-007 | E3 — Execution | [Daemon, MOT, and adversarial replication](0186-exp007-e3-daemon-mot-and-adversarial-replication.md) | PLANNED |
| 0187 | EXP-007 | E4 — Analysis | [Daemon, MOT, and adversarial replication](0187-exp007-e4-daemon-mot-and-adversarial-replication.md) | PLANNED |
| 0188 | EXP-007 | E5 — Report | [Daemon, MOT, and adversarial replication](0188-exp007-e5-daemon-mot-and-adversarial-replication.md) | PLANNED |
| 0189 | EXP-008 | E1 — Pre-registration | [Cross-platform and new-capability characterization](0189-exp008-e1-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0190 | EXP-008 | E2 — Review and approval | [Cross-platform and new-capability characterization](0190-exp008-e2-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0191 | EXP-008 | E3 — Execution | [Cross-platform and new-capability characterization](0191-exp008-e3-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0192 | EXP-008 | E4 — Analysis | [Cross-platform and new-capability characterization](0192-exp008-e4-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0193 | EXP-008 | E5 — Report | [Cross-platform and new-capability characterization](0193-exp008-e5-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0194 | Campaign | E6 — Campaign synthesis | [Campaign synthesis and evidence reconciliation](0194-campaign-e6-synthesis.md) | PLANNED |
| 0195 | WP-039 | S1 — Coding | [Stable-release evidence closure](0195-wp039-s1-stable-release-evidence-closure.md) | PLANNED |
| 0196 | WP-039 | S2 — Comprehensive audit | [Stable-release evidence closure](0196-wp039-s2-stable-release-evidence-closure.md) | PLANNED |
| 0197 | WP-039 | S3 — Remediation | [Stable-release evidence closure](0197-wp039-s3-stable-release-evidence-closure.md) | PLANNED |
| 0198 | WP-039 | S4 — Documentation and release | [Stable-release evidence closure](0198-wp039-s4-stable-release-evidence-closure.md) | PLANNED |

> **Campaign blocked, 2026-09-23 UTC.** EXP-001's E5 report raised a campaign
> plan §10.4 D1 (H1 and H2a `REFUTED`) plus finding `EXP001-E5-F1`. Per §3.3,
> every session from 0159 onward inherits the block — EXP-002 … EXP-008 and
> 0194 — until the four contingency correction sessions close and `EXP-001-r1`
> returns a non-reversal verdict, or the maintainer records a Project Plan
> §8.3 amendment accepting a changed conclusion. Planned session numbers do
> not change.
>
> **Correction cycle COMPLETE, 2026-09-27 UTC.** All four contingency sessions
> (S1→S2→S3→S4) closed. S1: root cause established and fixed; S2: **PASS**;
> S3: delta re-audit **CLEAN**; S4: PSR-039 issued, `EXP-001-r1` authorized.
> The correction branch (`hotfix/exp001-d1-parity-correction`) merged as
> PR #24 `149cf2d88ab6be401951b63d1d7e8fad209f52a5` (2026-09-28 UTC); all six
> required workflows are green per the
> [EXP-001-r1 E1 handoff](../../experiments/EXP-001-r1-golden-trajectory-numerical-parity/e1-handoff.md).
> **0159 stays
> BLOCKED** until `EXP-001-r1` returns a non-reversal verdict.
>
> **EXP-001-r1 E1 COMPLETE — DRAFT, 2026-09-28 UTC.** The maintainer declared
> this E1 session. The [draft pre-registration](../../experiments/EXP-001-r1-golden-trajectory-numerical-parity/preregistration.md)
> and [E1 handoff](../../experiments/EXP-001-r1-golden-trajectory-numerical-parity/e1-handoff.md)
> record the prospective protocol and local validation. E2 must independently
> review the protocol and resolve the required wgpu coverage and
> shared-storage budget gates before execution. E1 does not approve E2,
> execute E3, or release session 0159.
>
> **E2 follow-up H4 method APPROVED 2026-09-29 UTC; NOT FROZEN; E3
> BLOCKED on DV-043/DV-044 and clean M/R source identity.** DV-041
> binding capability closed on PR #25/required CI. DV-043 is local and
> OPEN pending required-CI merge plus a green nightly; DV-044's governed
> ledger correction is also open. No E3 run/freeze; session 0159
> remains BLOCKED.
>
> **EXP-001-r1 E3 EXECUTED 2026-09-29 UTC.** Every §10 entry gate closed
> first: DV-043 merged to `main` as `9b79d2e` (PR #26) with a green forced
> nightly `bench-regression` (`36525353031` attempt 2), DV-044 closed through
> its own S1→S4 cycle, and `M = 9b79d2e…` was incorporated with
> `check_ci_green.py` green on all six required workflows. The
> pre-registration then froze at its first `RUN-` creation at
> `F = 5d5ae35…`, and all six registered runs executed from the clean campaign
> checkout `R = 5d5ae35…` — 72-case wgpu kernel-path (`wgpu<wgsl>` proven per
> case), 72-case CUDA kernel-path, 504-case corpus, 2× 14-case repeatability
> and the 1,000-draw fuzz leg. Zero aborts, every directory manifested; see
> the [E3 log](../../experiments/EXP-001-r1-golden-trajectory-numerical-parity/log.md).
> E3 computed no verdict. Session 0159 remains BLOCKED.
>
> **EXP-001-r1 E4 ANALYSED 2026-09-29 UTC — ALL FIVE HYPOTHESES `CONFIRMED`,
> D1 FLAG NOT RAISED.** The r1-specific analysis module was committed before
> adjudication (campaign plan §7.4 item 2) and applied the frozen §8 rule to
> all six artefacts: H1 504/504 accepted (485 native-parity + 19
> explained-dv007, zero unexplained breaches), H2a **978 pointwise + 22
> characterized**, H2b both metrics' 95 % CIs strictly inside ±δ on 657
> contributors each, H3 14/14 byte-identical in both invocations with
> identical separate-run projections, H4 72/72 on **each** of CUDA and wgpu
> with zero failed derivative elements. Zero cases aborted anywhere. The four
> §8 outputs regenerate byte-identically from a clean checkout at `3270699`;
> see the [E4 analysis record](../../experiments/EXP-001-r1-golden-trajectory-numerical-parity/analysis.md).
> **This is a non-reversal detection, but it does not release 0159**: §10.4
> item 5 keys the release to E5's verdict. **0159 stays BLOCKED until
> EXP-001-r1 E5 reports.**
>
> **EXP-001-r1 E5 REPORTED 2026-09-29 UTC — non-reversal; 0159's release
> condition MET, release pending maintainer verification.** The
> [E5 report](../../experiments/EXP-001-r1-golden-trajectory-numerical-parity/report.md)
> restates all five `CONFIRMED` verdicts with the expected-versus-observed
> table, both 72-case H4 GPU legs in full, PD-1…PD-6 (PD-5 is the
> `149cf2d..M` baseline delta §10 item 5 requires: 23 files, 2,253 insertions,
> 34 deletions — exactly DV-041/PR #25 and DV-043/PR #26 plus their
> documentation, with `R` identified as the experiment's distinct source SHA),
> ten threats to validity including §4.2's clamp-trip limitation restated for
> the 22 characterized cases, and the full artefact index. Regeneration was
> re-verified in the E5 checkout: all four committed output digests reproduced
> byte-identically. **No D1 correction cycle is triggered.** EXP-001's record
> gains append-only erratum **E-4** and the Parity Report gains a dated
> admonition; neither revises EXP-001's own `REFUTED` verdicts. Budget: 6.855
> of 8 MiB (r1), 12.784 of 16 MiB (shared root), 12.777 of 64 MiB (campaign),
> ~13 min E3 wall time of 8 CPU hours, zero hosted-CI hours charged to r1.
> **0159, EXP-002 … EXP-008 and 0194 are released on the maintainer's
> verification of that report (§13), which is E5's exit gate and is not yet
> recorded — they remain BLOCKED until it is.** Nothing was pushed and no PR
> exists; §12 item 3 makes the E5 PR carry the whole r1 E1–E5 range, and
> opening it awaits authorization.
>
> **EXP-001-r1 E5 VERIFIED AND ACCEPTED 2026-09-29 UTC — THE CAMPAIGN BLOCK IS
> LIFTED; EXP-001-r1 IS COMPLETE.** MichaelMaillet completed the report's §13
> verification block, accepting all five `CONFIRMED` verdicts, the "no D1
> raised" non-reversal determination, and PD-6's reading of §10 item 5 (report
> both 72-case H4 legs; execute none at E5). E5's exit gate is met, so under
> campaign plan §10.4 item 5 **session 0159 (EXP-002 E1), every experiment
> downstream of EXP-001 and session 0194 are RELEASED** and may proceed in §3's
> dependency order. No Project Plan §8.3 amendment was needed — a confirmed
> parity result is not a changed conclusion. Before verification the report's
> 194 quoted figures were cross-checked programmatically against the committed
> artefacts; that found one real error (the four generated outputs total
> 10,506,349 bytes, not 10,506,347), corrected under errata **E-1**/**A-1** with
> the original figures retained, plus a histogram-unit ambiguity recorded as
> report §9 item 11 and `analysis.md` **A-2** for DV-040's re-audit gate at
> EXP-002 E4. Disclosed and not remediated: §9 item 9 — E4 and E5 share one AI
> pair, and no fresh-context independent review was run before verification.
> **Still open:** opening the E1–E5 pull request (authorized by the same
> verification, not yet exercised — nothing is pushed) and its §14.1
> tested-head-SHA/required-check addendum; and announcing the report in the next
> Project State Report, which is not an experiment session's to issue. *(Dated
> update, 2026-10-11 UTC: the EXP-001-r1 E1–E5 pull request was opened and
> merged as PR #28 `32cfed8`, and PSR-040 was issued at EA-007 via PR #32
> `da53ea1`.)*
>
> **EXP-002 E5 REPORTED 2026-10-14 UTC (session 0163) — D1 RAISED ON H3;
> CAMPAIGN BLOCKED AT SESSION 0164.** The
> [EXP-002 E5 report](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md)
> issues all verdicts in full: **H1 `CONFIRMED`** (`175/175` `api_symbols`
> resolved, `172/172` `legacy_api_names` owned, `0` duplicate/removed/unexpected,
> frozen sets empty), **H2 `CONFIRMED`** (`62/62` `claim_comparator_records`
> agree across `C01`–`C05`), **H3 `REFUTED` (D1)** under both the approved §5.4
> policy (`21/39` `generated_files` equal, `18/39` differing: `.pdf` and `.png`
> of figures 5, 7, 8, 9, 10, 11, 12, 14, and 15, while all `11/11` `.tex` tables
> and `5/14` figures match) and the §11.3 sensitivity policy (`5/39` equal,
> `34/39` differing), and **H4 `CONFIRMED`** (`39/39` `generated_files`
> raw-identical across two PRIN processes, canonical projections equal). In
> session `0163`, the retained E3 publication bytes (`39/39` per run) and input
> snapshots (`172/172` per run) were verified first against their manifested
> digests, the 7 E4 analysis outputs and `report-manifest.json` regenerated
> byte-identically (`8/8`) in a detached worktree outside the repository, the
> §8.2 reconstruction reproduced `39/39` PRIN-arm raw files and `39/39`
> normalized/sensitivity digests on both arms (`25/39` reference-arm raw files,
> disclosed as the unpinned reference PDF `CreationDate` limitation under §11.3
> item 2), and an independent recount matched E4 with zero discrepancies.
> **Per campaign plan §3.3 and §10.4 items 2–5, session `0164` (EXP-003 E1) and
> every later campaign session (`0165`–`0194`, covering EXP-003 … EXP-008 and
> Campaign E6 synthesis) inherit the block** until the four contingency
> correction sessions
> ([`2026-10-14-exp002-d1-s1..s4`](../contingencies/2026-10-14-exp002-d1-s1-correction-implementation.md))
> close and `EXP-002-r1` returns a non-reversal E5 verdict (or the maintainer
> adopts a Project Plan §8.3 amendment; note that while campaign plan §3.2 lists
> only EXP-001 as EXP-003's hard prerequisite, §3.3 and §10.4 items 2 & 5 block
> the immediate numbered successor `0164`, and running EXP-003 in parallel would
> require a Plan §8.3 amendment). Planned session numbers do not change.
> The report was **verified and accepted by the maintainer (MichaelMaillet)
> 2026-10-15 UTC** and the `EXP-002-D1` S1 correction scope approved as
> written (`report.md` §14); acceptance does not release `0164` or the
> correction cycle.
> **`EXP-002-D1` S1 COMPLETE 2026-10-15 UTC** (draft PR #34): root cause on
> the PRIN side, namely 34 drawing arguments dropped or re-encoded by the
> WP-034 port of nine figure generators, with 0 unexplained. The
> failing-test-first gate went red → green, and all 39 outputs now equal the
> frozen reference
> ([correction audit](../../audits/2026-10-15-exp002-d1-correction-audit.md)).
> S2 is next; `0164` stays BLOCKED.
> *(Retained as its point-in-time record; this index accumulates dated entries
> rather than rewriting them. S2 and S3 completed later the same day and on
> 2026-10-16 UTC — see the entry below.)*
>
> **`EXP-002-D1` CORRECTION CYCLE COMPLETE — S4 CLOSED 2026-10-16 UTC.**
> All four contingency sessions ran in strict S1→S4 order. **S2 COMPLETE
> 2026-10-15 UTC** — read-only audit of `ab9e4225..8fd0ecc9`, verdict
> **`PASS-WITH-FINDINGS`** (one D2, one D3, six D4, **no D1**, no systemic
> drift), all five brief-specific items **VERIFIED** by independent
> re-execution. **S3 COMPLETE 2026-10-16 UTC** — every open S2 finding
> dispositioned (`-F2` D2 **FIXED** with evidence-sized per-notebook cell
> bounds; `-F1` D3 **ASSIGNED** to S4 and `EXP-002-r1`; `-F4`…`-F7` D4
> **FIXED**; `-F8` D4 **RATIFIED** and re-checked; `-F3` already **RESOLVED**),
> delta re-audit **`CLEAN`**, four cold-review rounds triaged by measurement,
> and two observations carried to S4: **O-1** (the required full suite exited 1
> in both S3 runs, on two different single host-contention-sensitive tests that
> pass alone) and **O-2** (the cold-review loop reached its four-round cap with
> round 4's fixes unreviewed). **S4 COMPLETE 2026-10-16 UTC** — **PSR-041**
> issued ([`041-project-state.md`](../../reports/041-project-state.md)),
> carrying the cumulative deviation-ledger rows for the `EXP-002` D1
> (`H3 REFUTED`), all eight `EXP002D1-S2-F1`..`-F8` findings at their final
> status, and O-1/O-2, and formally announcing the EXP-002 E5 report
> (Experimentation Standards §2 E5; campaign plan §10.4 item 3). Registers
> updated (this index, [`SESSION_REGISTER.md`](../SESSION_REGISTER.md),
> [`DOCS/experiments/README.md`](../../experiments/README.md),
> [`contingencies/README.md`](../contingencies/README.md) — EXP-002 D1 moved to
> "Closed corrections", [`DEFERRED_VALIDATION_REGISTER.md`](../../reports/DEFERRED_VALIDATION_REGISTER.md));
> the [Parity Report](../../sphinx/parity_report.rst) gained a dated
> 2026-10-16 update and its reproduction rows were corrected to what the fixed
> generator supports; append-only erratum **2** naming `EXP-002-r1` was added to
> the [E5 report](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md)
> §15; and **`EXP-002-r1` was authorized** as a new record
> ([`EXP-002-r1`](../../experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md))
> carrying `EXP002D1-S2-F1`. O-1 is recorded **D3** with its local full-suite
> run at its actual exit status; O-2 is **RESOLVED (D4)** — the missing cold
> review was performed by measurement on S3's committed round-4 fixes, finding
> one latent fail-open in `final_legs.sh`'s grep-based leg aggregation,
> superseded by a corrected copy in
> [`EVIDENCE/exp002-d1-s4/`](../../../EVIDENCE/exp002-d1-s4/README.md); and
> `EXP002D1-S2-F8`'s third location
> (`EVIDENCE/exp002-d1-s2/snyk_sarif_filter.py:142`) is **RATIFIED** as an
> accepted, visible LOW with a Coding Standards §6.2 threat assessment.
> **Plan amendment #52** was adopted on the maintainer's authority: the seven
> hosted check workflows are re-enabled and stay active until the campaign's
> experimentation is complete (the close of `0194`, or earlier on maintainer
> instruction), superseding amendment #48's pause and amendment #50's
> EXP-002-only window; the Windows local gate stays mandatory and
> authoritative, and the branch ruleset is unchanged. PR #34's push and merge
> are authorized by the maintainer for this session.
> **`EXP-002`'s H3 verdict is unchanged — it stays `REFUTED`;** the correction
> fixed the generator *after* E3, so only `EXP-002-r1` can produce a new
> verdict, and **no r1 stage has run and no `RUN-` directory exists**.
> **Session `0164` (EXP-003 E1) and every later campaign session
> (`0165`–`0194`) remain BLOCKED.** The S4 closure, the merge of PR #34 and the
> re-enabling of the hosted workflows do **not** release them; release requires
> `EXP-002-r1`'s E5 verdict to be a non-reversal, verified and accepted by the
> maintainer, or a Project Plan §8.3 amendment (campaign plan §10.4 item 5).
> The next action is the maintainer's: declare `EXP-002-r1` E1, which must first
> settle the open H3 comparison-policy decision named in that record.
