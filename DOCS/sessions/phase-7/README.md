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
| 0158 | EXP-001 | E5 — Report | [Golden-trajectory numerical parity](0158-exp001-e5-golden-trajectory-numerical-parity.md) | **COMPLETE — report issued 2026-09-23; exit gate open on the correction cycle.** All five verdicts reported (H1/H2a `REFUTED`, H2b/H3/H4 `CONFIRMED`); §10.4 **D1** carried; second D1 **EXP001-E5-F1** raised (the `parity` CI corpus gate does not exercise PRIN) with a Parity Report erratum; four contingency sessions instantiated; **verified and accepted by the maintainer 2026-09-23 UTC**, E1–E5 PR approved |
| 0159 | EXP-002 | E1 — Pre-registration | [API, benchmark-result, and reproduction parity](0159-exp002-e1-api-benchmark-result-and-reproduction-parity.md) | **BLOCKED** — EXP-001 D1 (campaign plan §10.4 item 2, §3.3); released only after the [correction cycle](../contingencies/2026-09-23-exp001-d1-s1-correction-implementation.md) S1→S4 closes and `EXP-001-r1` returns a non-reversal verdict |
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
