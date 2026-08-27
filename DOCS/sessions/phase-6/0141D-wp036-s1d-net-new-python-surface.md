# Session 0141D — WP-036 S1 (sub-pass 4/5): Net-new Python compatibility surface

**Status:** SPLIT (2026-08-27) → [0141D1](0141D1-wp036-s1d1-net-new-python-surface-solver-family.md)
(Bucket G solver family + `TelemetryLogger`, COMPLETE) and
[0141D2](0141D2-wp036-s1d2-net-new-python-surface-remainder.md)
(the ~40-symbol Bucket G remainder, PLANNED), under Development Workflow §7 —
this brief's "Expected work" item 3 pre-authorised the split and the
decomposition plan §4 flagged it in advance. This file is retained as the
parent contract; the two sub-briefs govern execution. 0141E's predecessor
becomes 0141D2.

**Original status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036
**Session type:** S1 — Coding
**Predecessor:** [0141C — kernels bindings and DV-012](0141C-wp036-s1c-kernels-bindings-and-dv012.md)
**Successor:** [0141E — consolidation and handoff](0141E-wp036-s1e-consolidation-and-handoff.md)
**Authority:** Project Plan §6/§8, amendments #31/#32, the decomposition plan
[`WP-036-S1-execution-plan-and-decomposition.md`](WP-036-S1-execution-plan-and-decomposition.md). Standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Deliver the **Bucket G** net-new Python compatibility surface (~45 symbols with
no faithful single Rust owner): real, importable, construct/callable
implementations — thin composition wrappers over existing `prin` owners, or
faithful non-numeric Python orchestration classes — plus new-symbol unit
tests. Behavioral parity is **not** in scope here (0141 brief non-goal; proven
by the WP-036B/WP-036C ported suite).

Symbol groups: `OscilloSim`/`SimulationResult`/`quick_simulate`,
`LargeScaleOscillatorSystem`, `OscillatorPruner`,
`BatchedRK45Solver`/`FixedStepRK4Solver`/`SolverResult`,
`gradient_checkpoint_integration`, the hybrid-model family (`HybridPRINet`,
`HybridCLEVRN`, `HybridPRINetV2CLEVRN`, `InterleavedHybridPRINet`,
`TemporalHybridPRINet`, `AlternatingOptimizer`),
`ActiveControlTrainer`/`retrain_controller` (DV-025)/`StateCollector`/
`TelemetryLogger`/`create_ablation_tracker`,
`ControlSignalBuffer`/`collect_system_state`, `SlotAttentionCLEVRN`,
`ring_topology`/`small_world_topology`, the `y4q1_tools` grab-bag (8), the
`temporal_training` grab-bag (10: `SequenceData`, `generate_temporal_clevr_n`,
`generate_dataset`, `hungarian_similarity_loss`, `temporal_smoothness_loss`,
`count_parameters`, `TrainingSnapshot`, `TemporalTrainer`, `MultiSeedResult`,
`train_multi_seed`).

## Contract

- **Acceptance:**
  - Every Bucket G symbol resolves from `prin`, is in the appropriate
    `__all__`, and passes a construct/callable smoke check.
  - Each is a real implementation with **no numerics** (composition over
    `prin.dynamics` / `prin.nn` / `prin.train` / the 0141B–C bindings), or —
    where no faithful non-numeric implementation exists (D-2.2) — a documented
    stub raising a typed error, with a Migration Guide "removed / use X" row
    and an entry in the D-D-style disposition appendix (S2 veto).
  - New-symbol unit tests for every symbol; ≥95% coverage on new code.
  - `.pyi` stubs; `mypy --strict` clean; `interrogate` 100% public.
  - `retrain_controller` (DV-025): a real construct/callable surface is
    provided here; the DV-025 register row disposition is cited in the handoff.
  - Migration Guide rows added for every covered symbol.
- **Non-goals:** behavioral parity (WP-036B/C); the full 172-row table and
  full smoke matrix (0141E); new Rust numerics.

## Required reading

- The 0141A–C handoff drafts and the D-D disposition appendix
- Archived `src/prinet/utils/{oscillosim,fused_kernels,y4q1_tools,temporal_training,cuda_kernels}.py`
  and `src/prinet/nn/{hybrid,training_hooks,ablation_variants,slot_attention}.py`
  (reference for surface shape only — never imported or executed)
- `DOCS/standards/Coding_Standards.md` §2.1 (no Python numerics); `DOCS/standards/Testing_Standards.md` §1
- `DEFERRED_VALIDATION_REGISTER.md` DV-025
- Latest PSR and cumulative deviation ledger

## Entry conditions

- 0141C committed; the 0141B/C bindings are importable.
- No unresolved D1/D2 finding exists.

## Expected work

1. Implement each symbol as a thin wrapper / faithful orchestration class,
   tests in tandem. Where numerics would be required, stop and record a
   D-2.2 disposition instead — never inline numerics.
2. Record each namespace placement.
3. If this pass alone exceeds a reviewable commit range, split `0141D1` /
   `0141D2` (Development Workflow §7) and note it in the register/handoff.
4. `.pyi`; full local gate; record out-of-scope discoveries.

## Required evidence and outputs

- Code + tests in the same commit range; ≥95% coverage on new/changed code.
- Full local gate reproduced and recorded.
- The per-symbol disposition appendix updated (real impl vs documented stub).
- Snyk Code on modified first-party Python; ecosystem audits if manifests change.
- Sub-pass handoff note appended to the running S1 handoff draft.

## Prohibited

- Deferred tests, weakened assertions, **any** Python numerics, silent
  divergence (every non-faithful symbol must have a documented disposition),
  undocumented public API, hidden RNG, scope creep, unregistered
  experimentation.

## Exit gate

Local gate green; acceptance items evidence-mapped. Commit locally only.
Proceed to 0141E.
