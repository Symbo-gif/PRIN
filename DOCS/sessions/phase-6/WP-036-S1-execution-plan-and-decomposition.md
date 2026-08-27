# WP-036 S1 (session 0141) — execution plan and decomposition proposal

**Status:** ADOPTED (2026-08-27, MichaelMaillet). Recorded as **Plan amendment
#32**. Maintainer approved **M1** (sub-passes `0141A`–`0141E`), **D-2.1**
(Bucket G = real construct/callable implementation + new-symbol unit tests,
behavioral parity deferred to WP-036B/C), **D-2.2** (symbols with no faithful
non-numeric implementation get a documented disposition + Migration-Guide row,
S2 veto), and the **D-3** D-D dispositions (S2 audit veto retained). Not itself
an execution contract; the governing contracts are the 0141 brief, amendment
#31, amendment #32, and the five sub-session briefs `0141A`–`0141E`.

**Prepared for:** session 0141 (WP-036 S1 — compatibility surface, freeze
machinery, stubs, DV-012 bindings, Migration Guide symbol table).
**Author:** Claude Sonnet 5 (AI pair).
**Date:** 2026-08-27.
**Authority:** Project Plan §6/§8; Development Workflow and Audit Standards §7
("An S1 session that grows beyond its WP declaration must stop and either split
the WP (new declaration) or descope"); Testing Standards §1.1–1.2; Plan
amendment #31.

---

## 1. Why this document exists

Amendment #31 (2026-08-27) split the original WP-036 into WP-036 / WP-036B /
WP-036C and narrowed **WP-036** to: the `prin` PRINet-3.0-compatible symbol
surface (all 172 `prinet.__all__` symbols resolve from `prin`),
`prin._deprecation` freeze/deprecation machinery, `.pyi` stubs, the DV-012
`prin-py` sweep/engine bindings, and the consolidated symbol-by-symbol
Migration Guide table, with **new-symbol unit/property/gradient tests only**
(no acceptance-suite port).

Repository verification performed at the start of 0141 (commands in §2) shows
that **even the narrowed WP-036 S1 exceeds a single reviewable commit range**:
101 of the 172 symbols do not resolve from `prin` today, ~55 of them require
new PyO3 bindings and/or new thin Python wrapper modules across five crates
(`prin-tensor`, `prin-train`, `prin-kernels`, `prin-sim`, `prin-py`) plus a
maturin rebuild, and ~40 are net-new Python surface. Delivered as one S1 this
would force either (a) scope creep past any auditable commit range (D3 by
Development Workflow §7) or (b) deferred tests / weakened coverage (prohibited
by the 0141 brief "Prohibited" list and Testing Standards §1.1–1.2).

This is the same situation amendment #31 itself addressed one level up, and the
same remedy is proposed: decompose first, get maintainer approval, then
execute. **Until this is approved, no WP-036 code is written.**

---

## 2. Scope inventory (repository-verified, 2026-08-27, `main` @ `0693fc7`)

### 2.1 Verification commands

```
python -c "import prinet; print(len(prinet.__all__))"                  # 172
# combined prin public surface: prin + 11 submodules' __all__
# → 211 symbols; 71 of prinet.__all__ resolve by name, 101 do not
python -c "import prin; print(prin.__all__)"                           # ['__version__', 'core_version']  (2)
wc -l "DOCS/archive .../src/prinet/_deprecation.py"                    # 238
```

### 2.2 The 71 already-resolving symbols (re-export plumbing only)

| Owning `prin` submodule | Count | Work in 0141 |
|---|---:|---|
| `prin.reporting` | 21 | top-level re-export + `__all__` assembly |
| `prin.daemon` | 12 | re-export |
| `prin.nn` | 11 | re-export |
| `prin.metrics` | 9 | re-export |
| `prin.eval` | 9 | re-export |
| `prin.dynamics` | 7 | re-export |
| `prin.experiments` / `prin.train` | 2 | re-export |

No new numerics, no new bindings — assemble `prin.__all__` (top level) and
audit each submodule `__all__`. Every alias is exercised by the
`verify_api_surface` + construct/callable smoke test (brief acceptance; also
closes the R4 coverage-dilution risk from the amendment #31 execution plan).

### 2.3 The 101 missing symbols, by work type

| # | Bucket | Count | Nature | Rust owner (verified) |
|---|---|---:|---|---|
| A | **Pure Python alias** — target already built *and* already exposed in `prin.*` | ~8 | rename shim, no Rust | `Scalr`/`Rip`/`SyncGd` (`prin.nn`), `TemporalPropagator` (`prin.dynamics`), `recovery_speed` (`prin.eval`), `OscillatorModel` (ABC/Protocol), `ThetaGammaNetwork`/`DeltaThetaGammaNetwork` (helpers over `BandNetwork`) |
| B | **GPU/Triton/CUDA — D-D disposition** (documented stub + Migration-Guide row) | ~10 | `BackendUnavailableError`-class stub; no CPU rebuild | `triton_*` (6), `*_cuda` (2), `cuda_fused_kernel_available`, `AsyncCPUGPUPipeline` |
| C | **`prin-kernels` CPU reference exists → new PyO3 binding** | ~15 | thin binding over `step_cpu`/`sparse_knn`/`pac`/hierarchical CPU refs | `pytorch_*` family (10), `csr_coupling_step`, `sparse_knn_coupling_step`, `build_knn_neighbors`, `sparse_coupling_matrix{,_csr}` |
| D | **`prin-tensor` exists (WP-014) → new PyO3 binding** | 2 | binding over HOSVD/CP owners | `PolyadicTensor`, `CPDecomposition` |
| E | **`prin-train` exists (WP-022/023) → new PyO3 binding + torch bridge** | ~18 | binding + `autograd.Function` where trainable (gradcheck) | `inhibition.rs`/`feedback.rs` (4), `energy.rs`/`hep.rs` (2), `activations.rs` (3), `layers.rs` (`oscillatory_weight_init`, `PhaseToRate*`, `DenseAutoencoder`, `SparsityRegularizationLoss`, `HierarchicalResonanceLayer`, `PhaseAmplitudeCouplingLayer`, `PRINetModel`, `compile_model`) |
| F | **DV-012 — `prin-sim`/`prin-py` sweep/engine bindings** | 3 | new binding (carried scope) | `sweep_coupling_params`, `detect_oscillation`, `phase_to_rate` |
| G | **Net-new Python surface** — no faithful Rust owner; needs new wrapper or a per-symbol disposition | ~45 | wrapper over composed owners, or Migration-Guide "thin shim / use X" | `OscilloSim`/`SimulationResult`/`quick_simulate`, `LargeScaleOscillatorSystem`, `OscillatorPruner`, `BatchedRK45Solver`/`FixedStepRK4Solver`/`SolverResult`, `HybridPRINet`/`HybridCLEVRN`/`HybridPRINetV2CLEVRN`/`InterleavedHybridPRINet`/`TemporalHybridPRINet`/`AlternatingOptimizer`, `ActiveControlTrainer`/`retrain_controller` (DV-025)/`StateCollector`/`TelemetryLogger`/`create_ablation_tracker`, `ControlSignalBuffer`/`collect_system_state`, `SlotAttentionCLEVRN`, `ring_topology`/`small_world_topology`, `y4q1_tools` grab-bag (8), `temporal_training` grab-bag (10) |

Totals: **A ~8, B ~10, C ~15, D 2, E ~18, F 3, G ~45** = 101.

### 2.4 Non-symbol deliverables (unchanged from the 0141 brief)

- `python/prin/_deprecation.py` — `deprecated`, `deprecated_parameter`,
  `verify_api_surface`, `FROZEN_PUBLIC_API` **seeded from PRIN's own RC1
  `__all__`** (not PRINet's; brief Contract line).
- `.pyi` stubs for every symbol added.
- `verify_api_surface(prin.__all__)` regression test.
- Traceability-matrix regeneration (`tools/wp001_*`,
  `DOCS/baselines/wp001_api_traceability.md`).
- Consolidated 172-row Migration Guide table, machine-checked against
  `DOCS/baselines/wp001_api_traceability.md`.
- D-D per-symbol disposition appendix (§3.2), decided in S1 subject to S2 veto.
- S1 handoff note mapping each acceptance criterion to evidence.

---

## 3. Decisions required from the maintainer

### D-1 — Decomposition mechanism

| | Mechanism | Register impact | Recommendation |
|---|---|---|---|
| M1 | **Sequential S1 coding sub-passes `0141A`–`0141E`**, each committing at its own local gate, all feeding the single S2 audit `0142`; the whole `0141`+`0141A..E` range pushed once with `0142` per amendment #28 | `SESSION_REGISTER.md` / phase-6 README gain five sub-rows under the amendment-#31 additive-sub-session convention; 0142's predecessor becomes `0141E` | **Recommended** — smallest deviation, reuses the convention just established by #31, keeps one S2 over one contiguous range. Mirrors option C2 of the #31 execution plan but with the register mechanism #31 adopted |
| M2 | Split WP-036 again into WP-036 / WP-036A2 with their own S1–S4 mini-cycles (`0144I`–`0144L`) | second full mini-cycle; second Audit Report + PSR | Heavier; only warranted if the maintainer wants an independent audit of the binding work separate from the surface work |
| M3 | Keep 0141 as one session; grind | none | Rejected — Development Workflow §7 |

### D-2 — Bucket G sizing (the ~45 net-new symbols)

Bucket G is the largest and least Rust-backed. Two sub-questions:

1. **Depth in WP-036 S1.** The 0141 brief's acceptance is *"resolves from
   `prin` and passes a construct/callable smoke check"* — behavioral parity is
   explicitly a non-goal (proven later by the WP-036B/C ported suite). Proposal:
   Bucket G symbols get a **real, importable, construct/callable
   implementation** (thin wrapper composing existing owners, or a faithful
   new Python orchestration class with **no numerics**), plus new-symbol unit
   tests — but their *behavioral* verification is the WP-036B/C port. Confirm
   this reading.
2. **Any Bucket G symbol with no faithful non-numeric implementation** (e.g.
   `MixedPrecisionTrainer`, `AsyncCPUGPUPipeline` if it cannot be a CPU no-op)
   → D-D-style disposition: documented stub + Migration-Guide "removed / use X"
   row, S2 veto. Confirm this is acceptable rather than blocking.

### D-3 — D-D dispositions (delegated to S1 by #31; recorded here for S2 veto)

Proposed dispositions for the ~30 inherently GPU/Triton/CUDA or
no-CPU-analogue symbols (full table delivered as the S1 handoff appendix;
summary here):

| Symbol class | Proposed disposition |
|---|---|
| `pytorch_*` (10) — Bucket C | **Real CPU binding** over the `prin-kernels` `step_cpu`/`sparse_knn`/`pac`/hierarchical CPU references (these are the numerical authority per DV-012 closure). Not stubs. |
| `triton_*` (6), `fused_discrete_step_cuda`, `cuda_fused_kernel_available`, `triton_available` | **Documented stub** raising a `BackendUnavailableError`-class exception on call; `triton_available()`/`cuda_fused_kernel_available()` return `False`; Migration-Guide row "GPU-only reference path; use the `pytorch_*` CPU equivalent or the fused Rust kernel via `prin.dynamics`". Matches the reference suite's own `test_gpu.py` / `test_triton_kernels.py` skip markers (D-A). |
| `AsyncCPUGPUPipeline` | CPU-synchronous no-op wrapper if faithful; else documented stub. (D-2.2) |
| `BatchedRK45Solver` / `FixedStepRK4Solver` / `SolverResult` | **Real** torch-batched wrapper over `prin.dynamics.RK45Integrator` / `RK4Integrator` (already exposed). |
| `gradient_checkpoint_integration` | Thin wrapper over `torch.utils.checkpoint` + the existing integrator bridge; real. |

---

## 4. Proposed decomposition (assumes M1)

Dependency order: freeze machinery and the pure-re-export surface first (they
gate `verify_api_surface` and the Migration Guide table); bindings next
(surface must exist before its unit tests import it); consolidation last.

Each sub-pass: code + tests in tandem, local gate green (`cargo fmt`, clippy
`-D warnings`, Rust tests/rustdoc where Rust changed; ruff, mypy `--strict`,
interrogate 100% public, bandit, pytest, `cargo audit`, `pip-audit`; Snyk
Code on modified first-party source, Snyk Open Source if a manifest changes),
≥95% coverage on new/changed code, commit locally only.

### 0141A — Freeze machinery + pure re-export surface + D-D appendix

- `python/prin/_deprecation.py` (Buckets: none) — `deprecated`,
  `deprecated_parameter`, `verify_api_surface`, `FROZEN_PUBLIC_API` from
  PRIN RC1 `__all__`.
- Assemble `prin.__all__` (top level) from the **71** already-resolving
  symbols (§2.2) + audit submodule `__all__`s.
- Bucket A (~8 pure aliases) + their `.pyi`.
- Bucket B (~10) D-D stubs + `BackendUnavailableError`-class + `.pyi`.
- `verify_api_surface(prin.__all__)` regression test; smoke construct/callable
  test for the ~89 symbols covered so far.
- D-D disposition appendix (all ~30 symbols) committed as
  `DOCS/experiments/0141-wp036-s1-dd-dispositions.md`.
- Migration-Guide table rows for the ~89 covered symbols.

### 0141B — `prin-tensor` + `prin-train` Python bindings (Buckets D, E — ~20)

- New PyO3 bindings in `crates/prin-py/src/bindings/` over `prin-tensor`
  (HOSVD/CP) and `prin-train` (`inhibition`, `feedback`, `energy`, `hep`,
  `activations`, `layers`).
- New `python/prin/` wrapper surface (`prin.nn` / a new `prin.tensor` or
  `prin.core`-compat module — namespace decided in-pass, recorded).
- `autograd.Function` + float64 gradcheck for every trainable binding
  (Testing Standards; brief Expected-work item 3).
- `.pyi`, unit + property tests, maturin rebuild, Rust gates.
- Parity-evidence disposition per Development Workflow §S1 exit (grep/import
  check against the archived reference for each new binding).

### 0141C — `prin-kernels` reference-fn bindings + DV-012 sweep bindings (Buckets C, F — ~18)

- PyO3 bindings over `prin-kernels` `step_cpu` / `sparse_knn` / `pac` /
  hierarchical CPU references for the `pytorch_*` family and the sparse
  coupling helpers.
- DV-012: `sweep_coupling_params`, `detect_oscillation`, `phase_to_rate`
  bindings over `prin-sim` (closes the `prin-py` half of DV-012).
- Kernel-equivalence unit tests (CPU reference vs binding output); `.pyi`;
  maturin rebuild; Rust gates.

### 0141D — Net-new Python surface (Bucket G — ~45)

- Thin composition wrappers / faithful non-numeric orchestration classes for
  `OscilloSim`, hybrid-model family, `y4q1_tools`, `temporal_training`
  grab-bags, solver wrappers, `ring_topology`/`small_world_topology`,
  `ControlSignalBuffer`, `retrain_controller` (DV-025), etc.
- Any symbol failing D-2.2 → documented disposition instead.
- `.pyi`, new-symbol unit tests.
- **If this pass alone exceeds a reviewable range** (likely — it is ~45
  symbols across ~6 reference modules), it splits `0141D1` / `0141D2` on the
  same rule; flagged now so S2 is not surprised.

### 0141E — Consolidation

- Full 172-row Migration Guide table, machine-checked against
  `DOCS/baselines/wp001_api_traceability.md` (no silent removals).
- `verify_api_surface` green against the complete `prin.__all__`; full
  construct/callable smoke matrix over all 172.
- Traceability matrix regeneration; `tools/check_*` gates.
- S1 handoff note: every acceptance criterion → evidence.

---

## 5. Proposed Plan amendment #32 — draft text

> **#32 | 2026-08-27 | Project Plan §6 / WP-036 S1 (session 0141) /
> Development Workflow and Audit Standards §7 / `DOCS/sessions/SESSION_REGISTER.md` |**
> _(This is the draft text; the authoritative row is Project Plan §8.3
> amendment #32.)_ WP-036 S1, as narrowed by amendment #31, is executed as five sequential S1
> coding sub-passes `0141A`–`0141E` rather than one session, because
> repository verification at S1 start (`DOCS/sessions/phase-6/WP-036-S1-execution-plan-and-decomposition.md`)
> shows 101 of 172 `prinet.__all__` symbols do not resolve from `prin`, ~55
> need new PyO3 bindings / thin wrappers across `prin-tensor`, `prin-train`,
> `prin-kernels`, `prin-sim`, `prin-py` plus a maturin rebuild, and ~45 are
> net-new Python surface — one commit range too large to review at S2 without
> deferring tests or weakening coverage (both prohibited by the 0141 brief and
> Testing Standards §1.1–1.2). Each sub-pass commits at its own local gate with
> ≥95% coverage on new code; the contiguous `0141`+`0141A`–`0141E` range feeds
> the single S2 audit `0142` and is pushed once with it (amendment #28 cadence).
> `0141D` may split further (`0141D1`/`0141D2`) under the same §7 rule. The
> `0141A`–`0141E` identifiers follow the amendment-#31 additive-sub-session
> register convention and do not renumber the 0001–0198 integer sequence
> (0142's predecessor becomes `0141E`). Bucket-G symbols receive a real
> importable construct/callable implementation with no numerics plus
> new-symbol unit tests; behavioral parity remains a WP-036B/C obligation
> (0141 brief non-goal). D-D dispositions for the ~30 GPU/Triton/no-CPU-analogue
> symbols are recorded in `DOCS/experiments/0141-wp036-s1-dd-dispositions.md`
> and are subject to S2 audit veto. WP-036's acceptance criteria and non-goals
> are unchanged. Same disposition class as amendment #31 (additive-sub-session
> mechanism) and #20 (scope decomposition). | maintainer approval (pending) |

---

## 6. Risks

- **R1 — Bucket E gradcheck breadth.** Every trainable `prin-train` binding
  needs a float64 gradcheck; some (`HolomorphicEPTrainer`, HEP) have
  closed-form adjoints that must match Burn autodiff. Mitigation: 0141B is
  bindings-only over already-audited WP-022/023 Rust; the adjoints exist.
- **R2 — Namespace for the compat surface.** PRINet groups symbols under
  `prinet.core.*` / `prinet.utils.*`; PRIN uses `prin.dynamics` / `prin.nn` /
  etc. Some symbols (`PolyadicTensor`) have no current PRIN home. 0141B/D
  records each namespace decision; the top-level `prin.__all__` is the
  contract the brief names, so sub-module placement is subordinate.
- **R3 — Bucket G faithfulness (D-2.2).** Mitigated by the explicit
  per-symbol disposition requirement (no silent divergence) and S2 veto.
- **R4 — `_prin_core.pyi` drift.** 407 stub entries today; every new binding
  must update it. Mitigation: `mypy --strict` + a stub-completeness check in
  0141E.
- **R5 — maturin rebuild on this host.** Windows / Python 3.14 / Rust 1.92.
  Mitigation: 0141B is the first pass that rebuilds; if the toolchain blocks,
  it is reported as blocked per CLAUDE.md, not worked around.

---

## 7. Recommendation

Approve **M1** (sub-passes `0141A`–`0141E`), **D-2.1** (Bucket G = real
construct/callable + unit tests, parity deferred to WP-036B/C), **D-2.2**
(no-faithful-impl symbols get a documented disposition), and the **D-3**
dispositions (S2 veto retained). Record amendment #32. Then execute `0141A`
at §4.

Until then, no WP-036 code is written.
