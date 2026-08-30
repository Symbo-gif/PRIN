# Session 0144A / WP-036A S1 running handoff

**Date:** 2026-08-30
**Status:** S1 **PAUSED at start** pending maintainer approval of the
decomposition proposal. No WP-036A code written.

## Session-start protocol (Development Workflow §6)

Read: latest Project State Report (`DOCS/reports/036-project-state.md`),
WP-036A declaration (Plan amendment #33), the 0144A brief, Project Plan
§6/§8, Coding Standards §1.2/§2/§3.2, Testing Standards §1, the D-D
disposition appendix rows 31–44, and the existing `prin-train` /
`prin-py` bridge patterns.

**Session ID/type:** 0144A — WP-036A S1 (Coding).
**Planned outputs (0144A brief):** 13 trainable-layer Rust implementations +
PyO3 bindings + Python stub replacements + gradcheck/parity/error tests +
Migration Guide update + S1 handoff note.

## Blocking finding — S1 exceeds one reviewable commit range

Repository verification (`main` @ `237f21a`) shows WP-036A S1 as a single
session violates Development Workflow §7:

- The 13 symbols are **13 new trainable Burn modules**, not thin bindings
  over audited owners (contrast sub-pass 0141B, which was bindings-only over
  audited WP-022/023 Rust and was still one of five sub-passes).
- **Five composed primitives have no trainable Rust owner** and must be
  ported to Burn first: continuous `DeltaThetaGammaNetwork`,
  `PhaseAmplitudeCoupling`, `phase_to_rate` (currently `prin-sim`,
  non-autodiff), the FFI phase-delay gate, the DG EMA-integration stage.
- Per-symbol PyO3 `autograd.Function` bridges + Python `nn.Module`s +
  `_prin_core.pyi` updates + float64 gradcheck + PRINet-3.0 forward-parity +
  ≥95% coverage + one maturin rebuild per unit.
- Estimated delta ≈ 3.5–4.5k Rust + 1.2–1.6k bridges + 0.6–0.9k Python +
  2–2.8k tests. Every prior Phase 3–6 S1 delivered 300–1,500 source lines.

Delivered as one session this forces scope creep past any auditable commit
range (D3) or deferred tests / weakened coverage / weakened gradcheck
tolerances (prohibited by the 0144A brief and Testing Standards §1).

## Action taken

Drafted `DOCS/sessions/phase-6/WP-036A-S1-execution-plan-and-decomposition.md`
— repository-verified scope inventory, five maintainer decisions (D-1
decomposition mechanism, D-2 `compile_model`, D-3 `phase_to_rate`
differentiability, D-4 parity-tolerance governance, D-5
`HierarchicalResonanceLayer` batched), a dependency-ordered four-sub-pass
decomposition (`0144A1`–`0144A4`, `0144A3` pre-authorised to split), draft
Plan amendment #34, risks, and recommendation.

Mirrors the amendment #32 precedent for WP-036 S1 (session 0141 →
`0141A`–`0141E`).

## Next step (requires maintainer)

1. Maintainer reviews the decomposition proposal and D-1…D-5.
2. On approval: record Plan amendment #34; add `0144A1`–`0144A4` sub-rows to
   `DOCS/sessions/phase-6/README.md`, `DOCS/sessions/SESSION_REGISTER.md`,
   `TRACEABILITY.md`; author the four sub-pass briefs; update the 0144A brief
   Successor line and `0144B` Predecessor line; update
   `DOCS/reports/036-project-state.md`.
3. Execute `0144A1` at §4 of the decomposition plan.

No governance files (Project Plan amendment table, register, README,
brief statuses) were modified in this session — those changes are part of
recording the approved amendment.
