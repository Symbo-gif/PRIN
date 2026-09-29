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
| 0159 | EXP-002 | E1 — Pre-registration | [API, benchmark-result, and reproduction parity](0159-exp002-e1-api-benchmark-result-and-reproduction-parity.md) | **BLOCKED — release condition MET, awaiting maintainer verification.** The [correction cycle](../contingencies/2026-09-23-exp001-d1-s1-correction-implementation.md) S1→S4 closed 2026-09-27 and `EXP-001-r1` returned a **non-reversal** E5 verdict on 2026-09-29 (all five hypotheses `CONFIRMED`, D1 not raised), satisfying campaign plan §10.4 item 5. The release takes effect on the maintainer's verification of [`EXP-001-r1/report.md`](../../experiments/EXP-001-r1-golden-trajectory-numerical-parity/report.md) §13, which is E5's exit gate and is **not yet recorded** |
| 0160 | EXP-002 | E2 — Review and approval | [API, benchmark-result, and reproduction parity](0160-exp002-e2-api-benchmark-result-and-reproduction-parity.md) | PLANNED |
| 0161 | EXP-002 | E3 — Execution | [API, benchmark-result, and reproduction parity](0161-exp002-e3-api-benchmark-result-and-reproduction-parity.md) | PLANNED |
| 0162 | EXP-002 | E4 — Analysis | [API, benchmark-result, and reproduction parity](0162-exp002-e4-api-benchmark-result-and-reproduction-parity.md) | PLANNED |
| 0163 | EXP-002 | E5 — Report | [API, benchmark-result, and reproduction parity](0163-exp002-e5-api-benchmark-result-and-reproduction-parity.md) | PLANNED |
| 0164 | EXP-003 | E1 — Pre-registration | [CPU scaling and sweep performance](0164-exp003-e1-cpu-scaling-and-sweep-performance.md) | PLANNED |
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
