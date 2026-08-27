# Session 0141D2 — WP-036 S1 (sub-pass 4b/5): Net-new Python surface, part 2 — Bucket G remainder

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036
**Session type:** S1 — Coding
**Predecessor:** [0141D1 — net-new Python surface, part 1 (solver family)](0141D1-wp036-s1d1-net-new-python-surface-solver-family.md)
**Successor:** [0141E — consolidation and handoff](0141E-wp036-s1e-consolidation-and-handoff.md)
**Parent brief:** [0141D — net-new Python compatibility surface](0141D-wp036-s1d-net-new-python-surface.md)
**Authority:** Project Plan §6/§8, amendments #31/#32, the decomposition plan
[`WP-036-S1-execution-plan-and-decomposition.md`](WP-036-S1-execution-plan-and-decomposition.md); the
0141D parent brief. Standard wins on conflict.

> Prospective execution contract, not completion evidence. Split from 0141D
> under Development Workflow §7 and the 0141D brief "Expected work" item 3.

## Mission

Deliver the remaining **Bucket G** net-new Python compatibility surface — every
`prinet.__all__` symbol not covered by 0141A–0141C or 0141D1 — as real,
importable construct/callable implementations that are thin composition
wrappers / faithful non-numeric orchestration classes over existing `prin`
owners, **or**, where no faithful non-numeric implementation exists (D-2.2), a
documented stub raising a typed error with a Migration-Guide row and a D-D
disposition-appendix entry (S2 veto). **No Python numerics** (Coding Standards
§1.2). Behavioral parity is not in scope (WP-036B/WP-036C).

## Symbol scope (repository-verify at session start)

Grouped, with the provisional disposition from
`DOCS/experiments/0141-wp036-s1-dd-dispositions.md` ("0141D split" section):

1. **OscilloSim family** — `OscilloSim`, `SimulationResult`, `quick_simulate`.
2. **Topology builders** — `ring_topology`, `small_world_topology`
   (representation adaptation vs `prin.dynamics.Topology`; RNG-seed hazard).
3. **Large-scale / pruning** — `LargeScaleOscillatorSystem`, `OscillatorPruner`.
4. **Solver adjuncts** — `MixedPrecisionTrainer`, `AsyncCPUGPUPipeline`
   (D-2.2 rows 24–25).
5. **Hybrid-model family** — `HybridPRINet`, `HybridCLEVRN`,
   `HybridPRINetV2CLEVRN`, `InterleavedHybridPRINet`, `TemporalHybridPRINet`,
   `AlternatingOptimizer`.
6. **`temporal_training` grab-bag (10)** — `SequenceData`,
   `generate_temporal_clevr_n`, `generate_dataset`, `hungarian_similarity_loss`,
   `temporal_smoothness_loss`, `count_parameters`, `TrainingSnapshot`,
   `TemporalTrainer`, `MultiSeedResult`, `train_multi_seed`.
7. **`y4q1_tools` grab-bag (8)** — `AblationConfig`, `AblationHybridPRINetV2`,
   `create_ablation_model`, `ExtendedTrainingResult`,
   `train_clevr_n_single_seed`, `train_clevr_n_extended`, `count_flops`,
   `measure_wall_time`.
8. **Active-control family** — `ActiveControlTrainer`, `StateCollector`,
   `create_ablation_tracker`, `ControlSignalBuffer`, `collect_system_state`,
   `retrain_controller` (DV-025).
9. **Slot-attention adapter** — `SlotAttentionCLEVRN`.
10. **Surface-accounting stragglers** — `DiscreteDeltaThetaGamma`,
    `DiscreteDeltaThetaGammaLayer` (confirm the WP-023 owner and namespace).

Re-verify the exact set against `prinet.__all__` minus what already resolves;
the total 172-symbol reconciliation is 0141E's job, not this pass's.

## Maintainer decisions required before or during this pass

- **D2-a — Hybrid-model family disposition.** Deferred to this brief by the
  maintainer (2026-08-27). The six symbols are trainable `nn.Module`s with
  `nn.Linear` projections (Python numerics, prohibited), and
  `python/prin/nn/__init__.py` already declares `HybridPRINet` /
  `AlternatingOptimizer` as "no Rust owner, needs a trainable-layer rebuild".
  Choose: (i) D-2.2 documented stubs + Migration-Guide "deferred rebuild" rows
  + a maintainer-declared owning WP; or (ii) real composed `nn.Module`s (needs
  a standards waiver for the `nn.Linear` numerics). Recommendation: (i),
  consistent with the 0141B rows 31–42 precedent.
- **D2-b — `prin-sim` binding vs pure Python.** `prin_sim::OscilloSim` (engine)
  and `prin_sim::pruning` Rust owners exist but are unbound. Choose: (i) add
  thin PyO3 bindings (maturin rebuild + Rust gate — moves the work toward an
  0141B/C-style bindings pass); or (ii) pure-Python composition for
  `OscilloSim`/`quick_simulate` over `prin.dynamics` + `prin.kernels`, and
  D-2.2 stubs for `LargeScaleOscillatorSystem`/`OscillatorPruner` citing the
  unbound owner.
- **D2-c — DV-025 (`retrain_controller`).** The 0141D parent brief (line 51)
  asks for a construct/callable surface; `DEFERRED_VALIDATION_REGISTER.md`
  DV-025 re-targets the symbol to WP-036C S1 (session 0144E). Reconcile:
  either deliver the surface here and note the register is satisfied early, or
  descope to 0144E with an amendment note. Do not leave the conflict for 0141E.

## Contract

- **Acceptance:**
  - Every covered symbol resolves from `prin`, is in the appropriate `__all__`,
    and passes a construct/callable smoke check.
  - Each is a real no-numerics implementation (composition over
    `prin.dynamics` / `prin.nn` / `prin.train` / `prin.metrics` / `prin.eval` /
    the 0141B–D1 surface) **or** a documented D-2.2 stub with a Migration-Guide
    "removed / use X" row and a D-D disposition-appendix entry (S2 veto).
  - New-symbol unit tests for every symbol; ≥95% coverage on new code.
  - `.pyi` re-exports; `mypy --strict` clean; `interrogate` 100% on new modules.
  - Migration Guide rows added for every covered symbol.
  - Every out-of-scope discovery from 0141D1 (§"Out-of-scope discoveries") is
    acted on: the topology representation adaptation is recorded, the
    `temporal_smoothness_loss` D-2.2 disposition is written, D2-a/D2-b/D2-c are
    resolved.
- **Non-goals:** behavioral parity (WP-036B/C); the full 172-row table and
  smoke matrix (0141E); new Rust numerics.

## Required reading

- The 0141A–D1 handoff draft and the D-D disposition appendix (incl. the
  "0141D split" section and rows 31–42)
- Archived `src/prinet/utils/{oscillosim,fused_kernels,y4q1_tools,temporal_training,cuda_kernels}.py`
  and `src/prinet/nn/{hybrid,training_hooks,ablation_variants,slot_attention,subconscious_model}.py`
  (surface shape only — never imported or executed)
- `DOCS/standards/Coding_Standards.md` §1.2 / §3 (no Python numerics);
  `DOCS/standards/Testing_Standards.md` §1
- `DEFERRED_VALIDATION_REGISTER.md` DV-025
- `crates/prin-sim/src/{engine,pruning}.rs` (for the D2-b decision)
- Latest PSR and cumulative deviation ledger

## Entry conditions

- 0141D1 committed; the 0141B–D1 surface is importable.
- No unresolved D1/D2 finding exists.
- D2-a / D2-b / D2-c decisions obtained (or obtained during the pass and
  recorded as amendment notes).

## Expected work

1. Implement each symbol as a thin wrapper / faithful orchestration class, or
   record a D-2.2 disposition — never inline numerics.
2. Record each namespace placement.
3. If this pass alone still exceeds a reviewable commit range, split further
   (`0141D2a` / `0141D2b`) on the same §7 rule and note it.
4. `.pyi` re-exports; full local gate; record out-of-scope discoveries.

## Required evidence and outputs

- Code + tests in the same commit range; ≥95% coverage on new/changed code.
- Full local gate reproduced and recorded (Python; Rust + maturin only if
  D2-b chooses bindings).
- The per-symbol disposition appendix updated (real impl vs documented stub);
  the "0141D split" provisional table replaced with the final decisions.
- Snyk Code on modified first-party source; ecosystem audits if manifests change.
- Sub-pass handoff note appended to the running S1 handoff draft.

## Prohibited

- Deferred tests, weakened assertions, **any** Python numerics, silent
  divergence (every non-faithful symbol must have a documented disposition),
  undocumented public API, hidden RNG, scope creep, unregistered
  experimentation.

## Exit gate

Local gate green; acceptance items evidence-mapped; D2-a/D2-b/D2-c resolved;
every 0141D1 discovery acted on. Commit locally only. Proceed to 0141E.
