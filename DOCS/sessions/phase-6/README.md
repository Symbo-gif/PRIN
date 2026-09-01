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

Plan amendment #33 inserted **WP-036A** ("Trainable compatibility layers —
`prin-train` extension", sessions `0144A`–`0144D`) before WP-036B. The
existing WP-036B sessions shifted from `0144A`–`0144D` to `0144E`–`0144H`;
the existing WP-036C sessions shifted from `0144E`–`0144H` to
`0144I`–`0144L`.

Plan amendment #34 further decomposes **WP-036A S1 (session 0144A)** into
four sequential S1 coding sub-passes `0144A1`–`0144A4`, inserted between
`0144A` and the S2 audit `0144B`, all feeding the single S2 audit `0144B`.
The 13 trainable-layer symbols are 13 new trainable Burn modules — five of
the primitives they compose have no trainable Rust owner and must be
Burn-ported first — one commit range too large to review at S2 without
deferring tests or weakening gradcheck tolerances (Development Workflow §7).
`0144A3` is pre-authorised to split `0144A3a`/`0144A3b` under the same rule.
See
[`WP-036A-S1-execution-plan-and-decomposition.md`](WP-036A-S1-execution-plan-and-decomposition.md).

Plan amendment #35 decomposes **WP-036B S1 (session 0144E)** into six
sequential strict-port coding sub-passes `0144E1`–`0144E6`, all feeding the
single S2 audit `0144F`. The verified scope is 498 test functions / 8,570 lines
across 13 reference files (initial collect-only: 481 plus `test_clevr_n` import
error from missing `benchmarks.clevr_n`). Testing Standards §1.1 remains
literal: adapt imports only, assertions unchanged; compatibility gaps are
rebuilt through Rust-backed layers, never semantic-test rewrites. See
[`WP-036B-S1-execution-plan-and-decomposition.md`](WP-036B-S1-execution-plan-and-decomposition.md).

Plan amendment #36 inserts a new work package **WP-036D** ("GPU execution
path for the ported acceptance suite") at `0144I`–`0144L`, between WP-036B
and WP-036C; the existing WP-036C sessions shift `0144I`–`0144L` →
`0144M`–`0144P`. WP-036D closes the WP-036B S2 audit's §8-addendum gap: 8 of
the 9 acceptance-suite skips are CUDA guards on tests with a real reference
GPU path, red on every CPU host because `python/prin/_torch_compat.py` has no
GPU execution path — while the Rust CubeCL kernels, the `prin-sim` GPU
engines, and the self-hosted `PRIN-GPU-Runner` all already exist. WP-036D S1
(session `0144I`) is executed as three sequential coding sub-passes
`0144I1`–`0144I3` feeding the single S2 audit `0144J`. No new `prin` public
symbol; the CPU path is untouched; DV-005 / DV-001 are not closed by it. See
[`WP-036D-S1-execution-plan-and-decomposition.md`](WP-036D-S1-execution-plan-and-decomposition.md).

Plan amendment #38 inserts three new sibling work packages **WP-036E**
("GPU device-resident execution path", `0144Q`–`0144T`, closes DV-030/DV-003),
**WP-036F** ("DirectML controller-graph execution", `0144U`–`0144X`, closes the
DirectML half of DV-006), and **WP-036G** ("Deferred-Validation register
consolidation and permanent dispositions", `0144Y`–`0144AB`) between the
WP-036C block (`0144P`) and `0145`. Together they close or assign a dated
disposition to every open Deferred Validation Register item before Phase 7;
**DV-005** is closed as `AMENDED` (out of scope for 1.0.0), **DV-010** moves to
WP-038 S1 scope, **DV-027** routes to EMA-006. WP-036E S1 is pre-authorised to
decompose into `0144Q1`–`0144Qn` under Development Workflow §7. Identifiers
roll single-letter `0144Q`–`0144Z` to two-letter `0144AA`–`0144AB`. See
[`WP-036E-036F-036G-execution-plan-and-decomposition.md`](WP-036E-036F-036G-execution-plan-and-decomposition.md).

Plan amendment #39 decomposes **WP-036C S1** (session `0144M`) into eight
sequential strict-port coding sub-passes `0144M1`–`0144M8` feeding the single S2
audit `0144N`. Repository verification corrects the brief's "~790 `def test_`
functions" to **1,097 functions / ~15,810 lines across 24 reference files**
(1,172 collected) plus DV-025's `retrain_controller` resolution (in `0144M2`).
Testing Standards §1.1 stays literal: imports only, assertions unchanged;
compatibility gaps rebuilt through Rust-backed layers, never semantic-test
rewrites; GPU/Triton tests stay `skipif`-guarded and reuse WP-036D's
`_torch_compat.py` device dispatch. `0144M8` is pre-authorised to split under
Development Workflow §7. Planned session count 245 → 253. See
[`WP-036C-S1-execution-plan-and-decomposition.md`](WP-036C-S1-execution-plan-and-decomposition.md).

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
| 0143 | WP-036 | S3 — Remediation | [API completion, acceptance suite, and migration](0143-wp036-s3-api-completion-acceptance-suite-and-migration.md) | COMPLETE |
| 0144 | WP-036 | S4 — Documentation | [API completion, acceptance suite, and migration](0144-wp036-s4-api-completion-acceptance-suite-and-migration.md) | COMPLETE |
| 0144A | WP-036A | S1 — Coding | [Trainable compatibility layers — `prin-train` extension](0144A-wp036a-s1-trainable-compatibility-layers-prin-train-extension.md) | COMPLETE (sub-passes 0144A1–0144A4) |
| 0144A1 | WP-036A | S1 — Coding | [Inhibition and sparsification family](0144A1-wp036a-s1-inhibition-and-sparsification-family.md) | COMPLETE |
| 0144A2 | WP-036A | S1 — Coding | [Phase-to-rate and autoencoder family](0144A2-wp036a-s1-phase-to-rate-and-autoencoder-family.md) | COMPLETE |
| 0144A3 | WP-036A | S1 — Coding | [Hierarchical, PAC, and discrete-layer family](0144A3-wp036a-s1-hierarchical-pac-and-discrete-layer-family.md) | COMPLETE |
| 0144A4 | WP-036A | S1 — Coding | [Model container and consolidation](0144A4-wp036a-s1-model-container-and-consolidation.md) | COMPLETE |
| 0144B | WP-036A | S2 — Audit | [Trainable compatibility layers — `prin-train` extension](0144B-wp036a-s2-trainable-compatibility-layers-prin-train-extension.md) | COMPLETE |
| 0144C | WP-036A | S3 — Remediation | [Trainable compatibility layers — `prin-train` extension](0144C-wp036a-s3-trainable-compatibility-layers-prin-train-extension.md) | COMPLETE |
| 0144D | WP-036A | S4 — Documentation | [Trainable compatibility layers — `prin-train` extension](0144D-wp036a-s4-trainable-compatibility-layers-prin-train-extension.md) | COMPLETE |
| 0144E | WP-036B | S1 — Coding | [Acceptance suite port — core, dynamics, model stack, subconscious](0144E-wp036b-s1-acceptance-suite-port-core-dynamics-model-stack.md) | PLANNED (decomposed into 0144E1–0144E6) |
| 0144E1 | WP-036B | S1 — Coding | [Core and utils strict port](0144E1-wp036b-s1-core-and-utils-strict-port.md) | COMPLETE |
| 0144E2 | WP-036B | S1 — Coding | [Phases, hierarchical, and phase-to-rate strict port](0144E2-wp036b-s1-phases-hierarchical-and-phase-to-rate-strict-port.md) | COMPLETE |
| 0144E3 | WP-036B | S1 — Coding | [Q2 and Q2-remaining strict port](0144E3-wp036b-s1-q2-and-q2-remaining-strict-port.md) | COMPLETE |
| 0144E4 | WP-036B | S1 — Coding | [Q3-new, NN, and SCALR-enhanced strict port](0144E4-wp036b-s1-q3-nn-and-scalr-enhanced-strict-port.md) | COMPLETE |
| 0144E5 | WP-036B | S1 — Coding | [Hybrid and CLEVR-N strict port](0144E5-wp036b-s1-hybrid-and-clevr-n-strict-port.md) | COMPLETE |
| 0144E6 | WP-036B | S1 — Coding | [Subconscious strict port and consolidation](0144E6-wp036b-s1-subconscious-and-consolidation.md) | COMPLETE |
| 0144F | WP-036B | S2 — Audit | [Acceptance suite port — core, dynamics, model stack, subconscious](0144F-wp036b-s2-acceptance-suite-port-core-dynamics-model-stack.md) | COMPLETE |
| 0144G | WP-036B | S3 — Remediation | [Acceptance suite port — core, dynamics, model stack, subconscious](0144G-wp036b-s3-acceptance-suite-port-core-dynamics-model-stack.md) | COMPLETE |
| 0144H | WP-036B | S4 — Documentation | [Acceptance suite port — core, dynamics, model stack, subconscious](0144H-wp036b-s4-acceptance-suite-port-core-dynamics-model-stack.md) | PLANNED |
| 0144I | WP-036D | S1 — Coding | [GPU execution path for the ported acceptance suite](0144I-wp036d-s1-gpu-execution-path-ported-acceptance-suite.md) | PLANNED |
| 0144I1 | WP-036D | S1 — Coding | [PyO3 GPU binding layer](0144I1-wp036d-s1-pyo3-gpu-binding-layer.md) | PLANNED |
| 0144I2 | WP-036D | S1 — Coding | [Python device dispatch and DLPack marshalling](0144I2-wp036d-s1-device-dispatch-and-dlpack-marshalling.md) | PLANNED |
| 0144I3 | WP-036D | S1 — Coding | [GPU test activation, CI, and consolidation](0144I3-wp036d-s1-gpu-test-activation-and-ci.md) | PLANNED |
| 0144J | WP-036D | S2 — Audit | [GPU execution path for the ported acceptance suite](0144J-wp036d-s2-gpu-execution-path-ported-acceptance-suite.md) | COMPLETE |
| 0144K | WP-036D | S3 — Remediation | [GPU execution path for the ported acceptance suite](0144K-wp036d-s3-gpu-execution-path-ported-acceptance-suite.md) | PLANNED |
| 0144L | WP-036D | S4 — Documentation | [GPU execution path for the ported acceptance suite](0144L-wp036d-s4-gpu-execution-path-ported-acceptance-suite.md) | PLANNED |
| 0144M | WP-036C | S1 — Coding | [Acceptance suite port — integration, y-series, kernels; DV-025](0144M-wp036c-s1-acceptance-suite-port-integration-y-series-kernels.md) | PLANNED (decomposed into 0144M1–0144M8) |
| 0144M1 | WP-036C | S1 — Coding | [Integration-Q3 and Y2Q1/Y2Q4 strict port](0144M1-wp036c-s1-integration-q3-and-y2q1-y2q4-strict-port.md) | COMPLETE |
| 0144M2 | WP-036C | S1 — Coding | [Y2Q2/Y2Q3 strict port and DV-025 retrain_controller](0144M2-wp036c-s1-y2q2-y2q3-strict-port-and-dv025.md) | COMPLETE |
| 0144M3 | WP-036C | S1 — Coding | [Y3Q1/Y3Q2 strict port](0144M3-wp036c-s1-y3q1-y3q2-strict-port.md) | COMPLETE |
| 0144M4 | WP-036C | S1 — Coding | [Y3Q3/Y3Q4/Y3Q45/Y3Q49 strict port](0144M4-wp036c-s1-y3q3-y3q4-y3q45-y3q49-strict-port.md) | PLANNED |
| 0144M5 | WP-036C | S1 — Coding | [Y4Q1/Y4Q1_2/Y4Q1_3 strict port](0144M5-wp036c-s1-y4q1-y4q1-2-y4q1-3-strict-port.md) | PLANNED |
| 0144M6 | WP-036C | S1 — Coding | [Y4Q1_4/Y4Q1_5/Y4Q1_9 strict port](0144M6-wp036c-s1-y4q1-4-y4q1-5-y4q1-9-strict-port.md) | PLANNED |
| 0144M7 | WP-036C | S1 — Coding | [Y4Q1_7/Y4Q1_8 strict port](0144M7-wp036c-s1-y4q1-7-y4q1-8-strict-port.md) | PLANNED |
| 0144M8 | WP-036C | S1 — Coding | [Y4Q2/Y4Q3/Y4Q4, GPU/Triton guards, and consolidation](0144M8-wp036c-s1-y4q2-y4q3-y4q4-kernels-and-consolidation.md) | PLANNED |
| 0144N | WP-036C | S2 — Audit | [Acceptance suite port — integration, y-series, kernels; DV-025](0144N-wp036c-s2-acceptance-suite-port-integration-y-series-kernels.md) | PLANNED |
| 0144O | WP-036C | S3 — Remediation | [Acceptance suite port — integration, y-series, kernels; DV-025](0144O-wp036c-s3-acceptance-suite-port-integration-y-series-kernels.md) | PLANNED |
| 0144P | WP-036C | S4 — Documentation | [Acceptance suite port — integration, y-series, kernels; DV-025](0144P-wp036c-s4-acceptance-suite-port-integration-y-series-kernels.md) | PLANNED |
| 0144Q | WP-036E | S1 — Coding | [GPU device-resident execution path](0144Q-wp036e-s1-gpu-device-resident-execution-path.md) | PLANNED |
| 0144R | WP-036E | S2 — Audit | [GPU device-resident execution path](0144R-wp036e-s2-gpu-device-resident-execution-path.md) | PLANNED |
| 0144S | WP-036E | S3 — Remediation | [GPU device-resident execution path](0144S-wp036e-s3-gpu-device-resident-execution-path.md) | PLANNED |
| 0144T | WP-036E | S4 — Documentation | [GPU device-resident execution path](0144T-wp036e-s4-gpu-device-resident-execution-path.md) | PLANNED |
| 0144U | WP-036F | S1 — Coding | [DirectML controller-graph execution](0144U-wp036f-s1-directml-controller-graph-execution.md) | PLANNED |
| 0144V | WP-036F | S2 — Audit | [DirectML controller-graph execution](0144V-wp036f-s2-directml-controller-graph-execution.md) | PLANNED |
| 0144W | WP-036F | S3 — Remediation | [DirectML controller-graph execution](0144W-wp036f-s3-directml-controller-graph-execution.md) | PLANNED |
| 0144X | WP-036F | S4 — Documentation | [DirectML controller-graph execution](0144X-wp036f-s4-directml-controller-graph-execution.md) | PLANNED |
| 0144Y | WP-036G | S1 — Coding | [Deferred-Validation register consolidation and permanent dispositions](0144Y-wp036g-s1-dv-register-consolidation-and-permanent-dispositions.md) | PLANNED |
| 0144Z | WP-036G | S2 — Audit | [Deferred-Validation register consolidation and permanent dispositions](0144Z-wp036g-s2-dv-register-consolidation-and-permanent-dispositions.md) | PLANNED |
| 0144AA | WP-036G | S3 — Remediation | [Deferred-Validation register consolidation and permanent dispositions](0144AA-wp036g-s3-dv-register-consolidation-and-permanent-dispositions.md) | PLANNED |
| 0144AB | WP-036G | S4 — Documentation | [Deferred-Validation register consolidation and permanent dispositions](0144AB-wp036g-s4-dv-register-consolidation-and-permanent-dispositions.md) | PLANNED |
| 0145 | WP-037 | S1 — Coding | [Documentation, notebooks, paper, and Parity Report draft](0145-wp037-s1-documentation-notebooks-paper-and-parity-report-draft.md) | PLANNED |
| 0146 | WP-037 | S2 — Audit | [Documentation, notebooks, paper, and Parity Report draft](0146-wp037-s2-documentation-notebooks-paper-and-parity-report-draft.md) | PLANNED |
| 0147 | WP-037 | S3 — Remediation | [Documentation, notebooks, paper, and Parity Report draft](0147-wp037-s3-documentation-notebooks-paper-and-parity-report-draft.md) | PLANNED |
| 0148 | WP-037 | S4 — Documentation | [Documentation, notebooks, paper, and Parity Report draft](0148-wp037-s4-documentation-notebooks-paper-and-parity-report-draft.md) | PLANNED |
| 0149 | WP-038 | S1 — Coding | [RC1 packaging and Phase 6 gate](0149-wp038-s1-rc1-packaging-and-phase-6-gate.md) | PLANNED |
| 0150 | WP-038 | S2 — Audit | [RC1 packaging and Phase 6 gate](0150-wp038-s2-rc1-packaging-and-phase-6-gate.md) | PLANNED |
| 0151 | WP-038 | S3 — Remediation | [RC1 packaging and Phase 6 gate](0151-wp038-s3-rc1-packaging-and-phase-6-gate.md) | PLANNED |
| 0152 | WP-038 | S4 — Documentation | [RC1 packaging and Phase 6 gate](0152-wp038-s4-rc1-packaging-and-phase-6-gate.md) | PLANNED |

