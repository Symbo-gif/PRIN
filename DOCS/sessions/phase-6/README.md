# Phase 6 sessions — Benchmarks, reproduction, docs, and RC1

These files are prospective execution contracts governed by
`DOCS/standards/Development_Workflow_and_Audit_Standards.md` and the master
[`SESSION_REGISTER.md`](../SESSION_REGISTER.md). Complete them strictly in
sequence; actual evidence belongs in audits/reports/experiment records.

Plan amendment #31 split WP-036 into WP-036 / WP-036B / WP-036C and inserted
eight sub-sessions `0144A`–`0144H` between planned integer sessions 0144 and
0145; the 0145–0152 integer numbers are unchanged. See
[`WP-036-execution-plan-and-decomposition.md`](WP-036-execution-plan-and-decomposition.md).

Plan amendment #32 further decomposes **WP-036 S1 (session 0141)** into five
sequential S1 coding sub-passes `0141A`–`0141E`, inserted between integer
sessions 0141 and 0142, all feeding the single S2 audit 0142. See
[`WP-036-S1-execution-plan-and-decomposition.md`](WP-036-S1-execution-plan-and-decomposition.md).
`0141D` was split into `0141D1` / `0141D2` under Development Workflow §7
(2026-08-27), as the 0141D brief pre-authorised.

| Seq | Unit | Type | Session brief | Current status |
|---:|---|---|---|---|
| 0129 | WP-033 | S1 — Coding | [Unified benchmark runner and category migration](0129-wp033-s1-unified-benchmark-runner-and-category-migration.md) | COMPLETE |
| 0130 | WP-033 | S2 — Audit | [Unified benchmark runner and category migration](0130-wp033-s2-unified-benchmark-runner-and-category-migration.md) | COMPLETE |
| 0131 | WP-033 | S3 — Remediation | [Unified benchmark runner and category migration](0131-wp033-s3-unified-benchmark-runner-and-category-migration.md) | COMPLETE |
| 0132 | WP-033 | S4 — Documentation | [Unified benchmark runner and category migration](0132-wp033-s4-unified-benchmark-runner-and-category-migration.md) | COMPLETE |
| 0133 | WP-034 | S1 — Coding | [Reporting, figures, tables, and profiling](0133-wp034-s1-reporting-figures-tables-and-profiling.md) | COMPLETE |
| 0134 | WP-034 | S2 — Audit | [Reporting, figures, tables, and profiling](0134-wp034-s2-reporting-figures-tables-and-profiling.md) | COMPLETE |
| 0135 | WP-034 | S3 — Remediation | [Reporting, figures, tables, and profiling](0135-wp034-s3-reporting-figures-tables-and-profiling.md) | COMPLETE |
| 0136 | WP-034 | S4 — Documentation | [Reporting, figures, tables, and profiling](0136-wp034-s4-reporting-figures-tables-and-profiling.md) | COMPLETE |
| 0137 | WP-035 | S1 — Coding | [Reproduction pipeline and manifest](0137-wp035-s1-reproduction-pipeline-and-manifest.md) | COMPLETE |
| 0138 | WP-035 | S2 — Audit | [Reproduction pipeline and manifest](0138-wp035-s2-reproduction-pipeline-and-manifest.md) | COMPLETE |
| 0139 | WP-035 | S3 — Remediation | [Reproduction pipeline and manifest](0139-wp035-s3-reproduction-pipeline-and-manifest.md) | COMPLETE |
| 0140 | WP-035 | S4 — Documentation | [Reproduction pipeline and manifest](0140-wp035-s4-reproduction-pipeline-and-manifest.md) | COMPLETE |
| 0141 | WP-036 | S1 — Coding | [API completion, acceptance suite, and migration](0141-wp036-s1-api-completion-acceptance-suite-and-migration.md) | PLANNED |
| 0141A | WP-036 | S1 — Coding | [Freeze machinery, re-export surface, aliases, D-D stubs](0141A-wp036-s1a-freeze-machinery-and-reexport-surface.md) | COMPLETE |
| 0141B | WP-036 | S1 — Coding | [prin-tensor and prin-train Python bindings](0141B-wp036-s1b-tensor-and-train-bindings.md) | COMPLETE |
| 0141C | WP-036 | S1 — Coding | [prin-kernels reference-fn bindings and DV-012 sweep bindings](0141C-wp036-s1c-kernels-bindings-and-dv012.md) | COMPLETE |
| 0141D | WP-036 | S1 — Coding | [Net-new Python compatibility surface](0141D-wp036-s1d-net-new-python-surface.md) | SPLIT → 0141D1 / 0141D2 |
| 0141D1 | WP-036 | S1 — Coding | [Net-new Python surface, part 1 — Bucket G solver family](0141D1-wp036-s1d1-net-new-python-surface-solver-family.md) | COMPLETE |
| 0141D2 | WP-036 | S1 — Coding | [Net-new Python surface, part 2 — Bucket G remainder](0141D2-wp036-s1d2-net-new-python-surface-remainder.md) | COMPLETE |
| 0141E | WP-036 | S1 — Coding | [Consolidation — Migration Guide table, smoke matrix, traceability, handoff](0141E-wp036-s1e-consolidation-and-handoff.md) | COMPLETE |
| 0142 | WP-036 | S2 — Audit | [API completion, acceptance suite, and migration](0142-wp036-s2-api-completion-acceptance-suite-and-migration.md) | COMPLETE |
| 0143 | WP-036 | S3 — Remediation | [API completion, acceptance suite, and migration](0143-wp036-s3-api-completion-acceptance-suite-and-migration.md) | PLANNED |
| 0144 | WP-036 | S4 — Documentation | [API completion, acceptance suite, and migration](0144-wp036-s4-api-completion-acceptance-suite-and-migration.md) | PLANNED |
| 0144A | WP-036B | S1 — Coding | [Acceptance suite port — core, dynamics, model stack, subconscious](0144A-wp036b-s1-acceptance-suite-port-core-dynamics-model-stack.md) | PLANNED |
| 0144B | WP-036B | S2 — Audit | [Acceptance suite port — core, dynamics, model stack, subconscious](0144B-wp036b-s2-acceptance-suite-port-core-dynamics-model-stack.md) | PLANNED |
| 0144C | WP-036B | S3 — Remediation | [Acceptance suite port — core, dynamics, model stack, subconscious](0144C-wp036b-s3-acceptance-suite-port-core-dynamics-model-stack.md) | PLANNED |
| 0144D | WP-036B | S4 — Documentation | [Acceptance suite port — core, dynamics, model stack, subconscious](0144D-wp036b-s4-acceptance-suite-port-core-dynamics-model-stack.md) | PLANNED |
| 0144E | WP-036C | S1 — Coding | [Acceptance suite port — integration, y-series, kernels; DV-025](0144E-wp036c-s1-acceptance-suite-port-integration-y-series-kernels.md) | PLANNED |
| 0144F | WP-036C | S2 — Audit | [Acceptance suite port — integration, y-series, kernels; DV-025](0144F-wp036c-s2-acceptance-suite-port-integration-y-series-kernels.md) | PLANNED |
| 0144G | WP-036C | S3 — Remediation | [Acceptance suite port — integration, y-series, kernels; DV-025](0144G-wp036c-s3-acceptance-suite-port-integration-y-series-kernels.md) | PLANNED |
| 0144H | WP-036C | S4 — Documentation | [Acceptance suite port — integration, y-series, kernels; DV-025](0144H-wp036c-s4-acceptance-suite-port-integration-y-series-kernels.md) | PLANNED |
| 0145 | WP-037 | S1 — Coding | [Documentation, notebooks, paper, and Parity Report draft](0145-wp037-s1-documentation-notebooks-paper-and-parity-report-draft.md) | PLANNED |
| 0146 | WP-037 | S2 — Audit | [Documentation, notebooks, paper, and Parity Report draft](0146-wp037-s2-documentation-notebooks-paper-and-parity-report-draft.md) | PLANNED |
| 0147 | WP-037 | S3 — Remediation | [Documentation, notebooks, paper, and Parity Report draft](0147-wp037-s3-documentation-notebooks-paper-and-parity-report-draft.md) | PLANNED |
| 0148 | WP-037 | S4 — Documentation | [Documentation, notebooks, paper, and Parity Report draft](0148-wp037-s4-documentation-notebooks-paper-and-parity-report-draft.md) | PLANNED |
| 0149 | WP-038 | S1 — Coding | [RC1 packaging and Phase 6 gate](0149-wp038-s1-rc1-packaging-and-phase-6-gate.md) | PLANNED |
| 0150 | WP-038 | S2 — Audit | [RC1 packaging and Phase 6 gate](0150-wp038-s2-rc1-packaging-and-phase-6-gate.md) | PLANNED |
| 0151 | WP-038 | S3 — Remediation | [RC1 packaging and Phase 6 gate](0151-wp038-s3-rc1-packaging-and-phase-6-gate.md) | PLANNED |
| 0152 | WP-038 | S4 — Documentation | [RC1 packaging and Phase 6 gate](0152-wp038-s4-rc1-packaging-and-phase-6-gate.md) | PLANNED |

