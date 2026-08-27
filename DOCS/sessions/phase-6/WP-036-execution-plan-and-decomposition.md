# WP-036 S1 — Execution plan and decomposition proposal

**Status:** ADOPTED (2026-08-27, MichaelMaillet) and superseded as authority by
**Plan amendment #31**. Retained for rationale and inventory. Not an execution
contract; the governing contracts are the (narrowed) WP-036 briefs 0141–0144
and the new WP-036B/WP-036C briefs `0144A`–`0144H`.

## 0. Outcome (2026-08-27)

The maintainer approved: **D-A** (parity-tolerance governance reused for
hazard-attributed assertion gaps), **D-B** (`prin`-native surface, no `prinet`
shim), **D-E** (DV-005 stays a scoping decision), and **D-D delegated to
WP-036 S1 under S2 audit veto**. On the split mechanism, **option C1 as first
drafted was withdrawn**: §4 below claimed the renumber "touches only Phase 6",
which was wrong — sessions 0145–0198 span all of WP-037/WP-038 *and the entire
Phase 7 campaign* (EXP-001–008, WP-039), so a true C1 renumber is ~54
brief-file renames. The maintainer instead chose **C1''**: three work packages
(WP-036 / WP-036B / WP-036C), with WP-036B/C's eight sessions inserted as the
sub-numbered block `0144A`–`0144H` between planned integers 0144 and 0145,
leaving 0145–0198 untouched. Recorded as amendment #31 with the
additive-sub-session register convention. The §4 stage content stands; only
its "renumber" paragraph is void (replaced by the `0144A`–`0144H` block).

**Prepared for:** session 0141 (`0141-wp036-s1-api-completion-acceptance-suite-and-migration.md`)
**Author:** Claude Sonnet 5 (AI pair)
**Date:** 2026-08-27
**Authority:** Project Plan §6/§8; Development Workflow and Audit Standards §7
("An S1 session that grows beyond its WP declaration must stop and either split
the WP (new declaration) or descope"); Testing Standards §1.1.

---

## 1. Why this document exists

Two blocking conditions prevent WP-036 S1 from starting as written:

1. **Entry condition unmet.** The 0141 brief requires "WP-036 scope, acceptance
   criteria, and non-goals have maintainer approval." PSR-035 §6 records this as
   *pending* ("approval required before WP-036 S1 begins").

2. **Declared scope is not a single S1.** The 0141 Mission is: "Finish 175+
   symbol mapping, port ~1,670 acceptance tests, API-freeze/deprecation
   machinery, stubs, and symbol-by-symbol Migration Guide data." Verified
   against the repository, this is by a wide margin the largest coding session
   in the 198-session ledger — every prior S1 in Phases 3–6 delivered on the
   order of 300–1,500 lines of source plus 20–90 tests. Executing it as one S1
   would either force scope creep past any reviewable commit range (a D3
   finding by Development Workflow §7) or force deferred tests / weakened
   assertions (prohibited by the brief and Testing Standards §1.1–1.2).

The maintainer has directed that an execution plan and dependency-ordered
decomposition be drafted first. This is that draft.

---

## 2. Scope inventory (repository-verified)

### 2.1 Top-level compatibility symbol surface

`prinet.__all__` has **172** symbols (Definition-of-Done item 1 says "175+";
the 3-symbol gap is `__version__`/`__author__`-class module attributes plus the
`_deprecation` helpers — see 2.2). Cross-referencing every name against the live
`prin` public surface (`prin` + `prin.dynamics` + `prin.metrics` + `prin.nn` +
`prin.train` + `prin.daemon` + `prin.eval` + `prin.experiments` +
`prin.reporting` + `prin.datasets` + `prin.parity` + `prin.dlpack`):

| Category | Count | Examples |
|---|---:|---|
| **Same name already exported by a `prin` submodule** | 71 | `KuramotoOscillator`, `HopfOscillator`, `MultiRateIntegrator`, `PhaseTracker`, `HybridPRINetV2`, `kuramoto_order_parameter`, `bimodality_index`, all `fig_*`/`table_*`, `SubconsciousController`, `SubconsciousDaemon` |
| **Implemented but renamed** (Migration-Guide rename, needs a compat alias) | ~14 | `SCALROptimizer`→`Scalr`, `RIPOptimizer`→`Rip`, `SynchronizedGradientDescent`→`SyncGd`, `TemporalPhasePropagator`→`TemporalPropagator`, `temporal_recovery_speed`→`recovery_speed`, `ThetaGammaNetwork`/`DeltaThetaGammaNetwork`→`BandNetwork` construction helpers, topology enums |
| **Numerics exist in a Rust crate but are not exposed to Python** | ~45 | `PolyadicTensor`/`CPDecomposition` (`prin-tensor`), `FeedforwardInhibition`/`FeedbackInhibition`/`DentateGyrusConverter`/`HolomorphicEnergy`/`HolomorphicEPTrainer`/`PhaseActivation`/`dSiLU` (`prin-train` WP-023), `pytorch_*`/`triton_*` kernel reference fns (`prin-kernels` WP-017–020), `sweep_coupling_params`/`detect_oscillation` (`prin-sim` — the DV-012 `prin-py` binding gap), `ring_topology`/`small_world_topology`/`sparse_coupling_matrix` (`prin-dynamics` WP-009) |
| **No equivalent anywhere — net-new Python surface** | ~42 | `PRINetModel`, `compile_model`, `HybridPRINet`, `HybridCLEVRN`, `AlternatingOptimizer`, `InterleavedHybridPRINet`, `TemporalHybridPRINet`, `ActiveControlTrainer`, `OscilloSim`/`SimulationResult`/`quick_simulate`, `LargeScaleOscillatorSystem`, `AsyncCPUGPUPipeline`, `OscillatorPruner`, `MixedPrecisionTrainer`, `BatchedRK45Solver`/`FixedStepRK4Solver`/`SolverResult`, the `y4q1_tools` grab-bag (`AblationConfig`, `count_flops`, `measure_wall_time`, `train_clevr_n_*`, `create_ablation_model`), `SequenceData`/`TemporalTrainer`/`MultiSeedResult`/`train_multi_seed`, `retrain_controller` (DV-025) |

"175+ symbol mapping" is therefore **not** a re-export exercise. ~87 of 172
symbols need either a new PyO3 binding, a new thin Python wrapper, or a
maintainer decision that the symbol is deliberately GPU-only / reference-only
and gets a documented `NotImplementedError`-class stub or Migration-Guide
"removed, use X" entry.

### 2.2 Deprecation / API-freeze machinery

Reference `prinet/_deprecation.py` (238 lines): `deprecated`,
`deprecated_parameter`, `FROZEN_PUBLIC_API` (a `frozenset` contract),
`verify_api_surface`. PRIN owns this module per the traceability matrix
(`prinet._deprecation` → WP-036). Small and self-contained; the only judgement
call is what goes in PRIN's `FROZEN_PUBLIC_API` (PRIN's own `__all__` at RC1,
not PRINet's).

### 2.3 Type stubs

`.pyi` stubs for the compat surface. Precedent exists (`python/prin/nn/*.pyi`,
`python/prin/dlpack.pyi`). Scope scales with 2.1.

### 2.4 Migration Guide symbol-by-symbol data

`DOCS/sphinx/migration_guide.rst` today documents Rust-symbol mappings grouped
by WP. WP-036's deliverable is the consolidated
`prinet.<symbol>` → `prin.<symbol>` (or "removed / GPU-only / renamed") table
covering all 172 entries, machine-checkable against
`DOCS/baselines/wp001_api_traceability.md`.

### 2.5 Ported acceptance suite

Reference `tests/`: **37 files, 1,595 `def test_` functions**, ~1,670 after
parametrization. Testing Standards §1.1: "adapt imports only, never weaken
assertions." Cluster map (import roots → PRIN owner):

| Reference test files | `def test_` | Dominant imports | PRIN target area |
|---|---:|---|---|
| `test_core.py`, `test_utils.py`, `test_phases.py` | 231 | `core.decomposition`, `core.measurement`, `core.propagation`, `utils.cuda_kernels` | `prin.dynamics`, `prin.metrics`, tensor surface |
| `test_hierarchical.py`, `test_phase_to_rate.py`, `test_q2.py`, `test_q2_remaining.py`, `test_q3_new.py` | 214 | `core.propagation`, `nn.layers`, `nn.hep`, `nn.activations` | band networks, inhibition, activations, HEP |
| `test_nn.py`, `test_scalr_enhanced.py`, `test_hybrid.py`, `test_clevr_n.py` | 80 | `nn.layers`, `nn.optimizers`, `nn.hybrid` | model stack, optimizers |
| `test_subconscious.py` | 49 | `core.subconscious*`, `nn.subconscious_model`, `utils.npu_backend` | `prin.daemon` |
| `test_triton_kernels.py`, `test_gpu.py` | 80 | `utils.triton_kernels`, `utils.cuda_kernels` | kernel reference fns (GPU-guarded) |
| `test_integration_q3.py`, `test_y2q1`–`test_y2q4`, `test_y3q1`–`test_y3q49` | 519 | top-level `prinet`, mixed | integration across all of the above |
| `test_y4q1*.py` (7 files), `test_y4q2.py`, `test_y4q3.py`, `test_y4q4.py` | 653 | `nn.slot_attention`, `nn.ablation_variants`, `utils.oscillosim`, `utils.temporal_*`, `utils.y4q1_tools`, `utils.adversarial_tools` | OscilloSim, temporal metrics/training, ablations, publication, adversarial |

The `torch.complex64`/f32 reference vs PRIN's f64 Rust core (preserved hazards,
amendments #14/#16/#17/#25) means a fraction of these assertions will not pass
byte-for-byte under "imports only" and need the same tolerance-governance
treatment the parity corpus already uses. That governance path must be agreed
before porting starts (decision D-A below).

### 2.6 Carried Deferred-Validation items landing on WP-036

- **DV-012** — `prin-py` sweep/engine PyO3 bindings (needed to back
  `sweep_coupling_params`, `detect_oscillation`).
- **DV-005** — CUDA Burn backend re-gate (R31 disposition: "re-gate at Phase 6
  WP-036"). This is a *scoping decision*, not necessarily implementation.
- **DV-025** — `retrain_controller` / `SubconsciousController.export_to_onnx` /
  `.quantize_onnx` (supervised retraining from telemetry).

---

## 3. Decisions required from the maintainer

**D-A — Acceptance-suite parity governance.** How are reference assertions that
fail under "imports only" solely due to the documented f32/f64 hazard handled?
Recommended: reuse the parity-corpus tolerance mechanism — a per-test
`@pytest.mark.parity_tolerance(...)` (or equivalent) with each loosening
recorded in the Parity Report, exactly as amendments #16/#17 did for corpus
metrics. No assertion is deleted or skipped; a reference test with no
PRIN-compatible behavior (pure GPU/Triton) is `skipif`-guarded on backend
availability, matching the reference suite's own `test_gpu.py` markers.

**D-B — Namespace.** `prinet` is occupied by the editable-installed reference
package (`.venv/…/__editable__.prinet-3.0.0.pth`) that the `parity/` job needs.
The compat surface is therefore `prin`-native and the ported tests import
`prin` (Plan §36: "the Migration Guide documents the import rename").
Recommended: confirm — no `prinet` shim package.

**D-C — Split mechanism.** Three options:

| | Mechanism | Register impact | Recommendation |
|---|---|---|---|
| C1 | Split into **WP-036 / WP-036B / WP-036C**, each its own S1–S4, inserted as sessions 0141–0152; cascade WP-037→0153–0156, WP-038→0157–0160 | 3 new WP declarations; renumber 8 downstream session files + register + traceability + phase-6 README | **Recommended** — this is the standard's prescribed "split the WP (new declaration)" path; renumber is mechanical and touches only Phase 6 |
| C2 | Keep one WP-036; authorize **three S1 coding sub-sessions** (0141, 0141-b, 0141-c) feeding one S2 audit (0142) | No renumber; register gains 2 sub-rows | Weaker audit story — one S2 auditing three commit ranges; departs from the fixed S1–S4 shape |
| C3 | Keep as declared; grind | None | Rejected — violates Development Workflow §7 |

**D-D — Reference-only symbols.** For the ~30 symbols that are inherently
GPU/Triton/CUDA (`triton_*`, `fused_discrete_step_cuda`,
`cuda_fused_kernel_available`, `AsyncCPUGPUPipeline`, …): expose a real
CPU-reference implementation where one already exists in `prin-kernels`
(the `pytorch_*` names — WP-018/019/020 built these in Rust), or a documented
`BackendUnavailableError` stub + Migration-Guide entry where PRIN deliberately
did not rebuild the path (`triton_*`). Needs a symbol-by-symbol maintainer
sign-off, delivered as an appendix to the approved plan.

**D-E — DV-005.** Confirm the R31 disposition still holds: make the CUDA Burn
backend a *scoping decision* recorded in WP-036's PSR (defer to Phase 7 campaign
or a dedicated post-RC WP), **not** implementation work inside this WP. RC1 does
not require it (Plan §6 Phase 6 exit criteria do not mention GPU training).

---

## 4. Proposed decomposition (assumes C1)

Dependency order: the surface must exist before its tests can import it; the
freeze contract must exist before it can be verified; the Migration Guide table
is finalized once symbol decisions are locked.

### WP-036 — Compatibility surface, freeze machinery, and migration data

*Sessions 0141–0144. No test porting — new-symbol unit tests only.*

- **S1 (0141):**
  1. `python/prin/_deprecation.py` — `deprecated`, `deprecated_parameter`,
     `verify_api_surface`, `FROZEN_PUBLIC_API` seeded from PRIN's RC1 `__all__`.
  2. Compat re-exports + renamed-symbol aliases for the 71 + ~14 already-built
     symbols, assembled into `prin.__all__` (top level) with matching
     submodule `__all__` updates.
  3. New PyO3 bindings / thin wrappers for the ~45 "Rust exists, not exposed"
     symbols — dominated by `prin-tensor` (`PolyadicTensor`, `CPDecomposition`),
     `prin-train` WP-023 inhibition/activation/HEP, the `pytorch_*` kernel
     reference fns, and the DV-012 sweep/engine bindings.
  4. `.pyi` stubs for everything added.
  5. Unit + property tests for every new binding (≥95% coverage, mypy strict,
     interrogate 100% public), gradcheck for any new `autograd.Function`.
  6. `verify_api_surface(prin.__all__)` regression test; traceability-matrix
     regeneration.
  7. Migration Guide consolidated symbol table (all 172 rows) + the D-D
     appendix decisions.
  8. S1 handoff note.
- **S2–S4 (0142–0144):** audit / remediation / documentation as normal.
- **Acceptance:** every one of the 172 symbols *resolves* from `prin`
  (import + construct/callable smoke test); freeze contract verified;
  Migration Guide table machine-checked; no silent removals; no Python
  numerics introduced (Coding Standards §2.1 — wrappers only).

### WP-036B — Acceptance suite port, part 1: core / dynamics / model stack

*Sessions 0145–0148. ~805 reference `def test_` (clusters 1–3 + `test_subconscious.py`).*

- Port `test_core`, `test_utils`, `test_phases`, `test_hierarchical`,
  `test_phase_to_rate`, `test_q2`, `test_q2_remaining`, `test_q3_new`,
  `test_nn`, `test_scalr_enhanced`, `test_hybrid`, `test_clevr_n`,
  `test_subconscious` — imports adapted to `prin`, assertions unchanged.
- Every tolerance loosening → Parity Report entry (D-A).
- **Acceptance:** ported subset green on CPU, Linux + Windows,
  Python 3.11–3.13; coverage non-decreasing; zero skipped tests without a
  linked, maintainer-approved quarantine issue.

### WP-036C — Acceptance suite port, part 2: integration / y-series / kernels

*Sessions 0149–0152. ~790 reference `def test_` (clusters 5–7).*

- Port `test_integration_q3`, `test_y2q1`–`test_y3q49`, `test_y4q1*`,
  `test_y4q2`, `test_y4q3`, `test_y4q4`, `test_triton_kernels`, `test_gpu`
  (GPU files `skipif`-guarded per D-A / reference precedent).
- Resolve DV-025 (`retrain_controller`) if its reference tests are in scope.
- **Acceptance:** full ported ~1,670-test suite green on CPU; DoD items 1–2
  satisfied; `SESSION_REGISTER` / `TRACEABILITY` updated; Phase 6 can proceed
  to WP-037.

### Session block (C1'' — adopted)

No renumber. WP-036B = `0144A`–`0144D` (S1–S4); WP-036C = `0144E`–`0144H`
(S1–S4), inserted between planned integers 0144 and 0145. `SESSION_REGISTER.md`,
`DOCS/sessions/README.md`, `DOCS/sessions/phase-6/README.md`, and
`TRACEABILITY.md` gain the block plus the sub-session convention text; 0144's
successor becomes `0144A` and 0145's predecessor becomes `0144H`. Planned count:
198 integer + 8 sub-sessions = 206. (The withdrawn C1 renumber would instead
have shifted every brief 0145–0198 by 8 — WP-037, WP-038, and the whole Phase 7
campaign — ~54 files.)

---

## 5. Proposed Plan §6 amendment (#31) — draft text

> **#31 | 2026-08-2x | Project Plan §6 / WP-036 declaration (PSR-035 §6) |**
> WP-036 ("API completion, acceptance suite, and migration") is split into
> three sequential work packages, each executed through a full S1–S4 Session
> Cycle, because the single declaration (172-symbol compatibility surface + the
> ~1,670-test acceptance-suite port + freeze machinery + stubs + Migration
> Guide data) cannot be delivered in one reviewable S1 without deferring tests
> or scope-creeping past any auditable commit range (Development Workflow §7).
> **WP-036** delivers the `prin` compatibility symbol surface (all 172
> `prinet.__all__` symbols resolve from `prin`), `prin._deprecation`
> freeze/deprecation machinery, `.pyi` stubs, the DV-012 `prin-py` sweep/engine
> bindings, and the consolidated symbol-by-symbol Migration Guide table, with
> new-symbol unit/property/gradient tests only. **WP-036B** ports reference
> test clusters `test_core`…`test_subconscious` (~805 functions). **WP-036C**
> ports the remaining integration / y-series / kernel clusters (~790
> functions) and resolves DV-025. Testing Standards §1.1 ("adapt imports only,
> never weaken assertions") is unchanged; assertion loosenings attributable to
> the documented f32/f64 preserved hazards (amendments #14/#16/#17/#25) are
> governed exactly as corpus-metric tolerances are — per-test annotation +
> Parity Report entry, never deletion or skip. DV-005 (CUDA Burn backend)
> remains a scoping decision recorded in WP-036's PSR, not implementation work;
> RC1 does not require it. Sessions 0141–0152 are WP-036/B/C S1–S4; WP-037 and
> WP-038 renumber to 0153–0160; planned session count 198 → 206. Acceptance
> criteria and non-goals of the original declaration are preserved in
> aggregate across the three WPs. | maintainer approval (pending) |

---

## 6. Risks

- **R1 — Behavioral parity depth.** The largest unknown is how many of the
  ~1,670 assertions need tolerance governance vs. pass clean. Mitigation:
  WP-036B is deliberately the "known-numerics" clusters first, so the parity
  workload is characterized before WP-036C's larger integration surface.
- **R2 — Net-new Python surface (2.1, ~42 symbols).** Some reference symbols
  (`OscilloSim` Python class, `AsyncCPUGPUPipeline`, `MixedPrecisionTrainer`)
  may have no faithful CPU rebuild. D-D forces an explicit per-symbol decision
  rather than silent divergence; each "stub" outcome is a Migration-Guide
  "removed / use X" row, which DoD item 1 ("working equivalent … renames
  documented") permits.
- **R3 — Renumber churn (C1).** Mechanical but touches governance files.
  Mitigation: confined to Phase 6; done as the first commit of WP-036 S1 with
  its own verification (`tools/` traceability + register checks).
- **R4 — Coverage gate on wrappers.** Thin re-export modules can dilute
  coverage %. Mitigation: `# pragma: no cover` is not permitted here; instead
  every alias is exercised by the `verify_api_surface` + smoke-import test.

---

## 7. Recommendation

Approve **C1** (three-WP split), **D-A** (parity-tolerance governance reused),
**D-B** (`prin`-native, no `prinet` shim), **D-E** (DV-005 stays a scoping
decision). Provide the **D-D** per-symbol dispositions (or delegate them to
WP-036 S1 with S2 audit veto). On approval: record amendment #31, execute the
renumber, then begin WP-036 S1 (0141) at step 1 of §4.

Until then, no WP-036 code is written.
