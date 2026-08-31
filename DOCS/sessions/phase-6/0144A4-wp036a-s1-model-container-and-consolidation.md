# Session 0144A4 — WP-036A S1 (sub-pass 4/4): Model container and consolidation

**Status:** COMPLETE (2026-08-31)
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036A
**Session type:** S1 — Coding
**Predecessor:** [0144A3 — hierarchical, PAC, and discrete-layer family](0144A3-wp036a-s1-hierarchical-pac-and-discrete-layer-family.md)
**Successor:** [0144B — Audit](0144B-wp036a-s2-trainable-compatibility-layers-prin-train-extension.md)
**Authority:** Project Plan §6/§8, amendments #33/#34, the decomposition plan
[`WP-036A-S1-execution-plan-and-decomposition.md`](WP-036A-S1-execution-plan-and-decomposition.md).
Standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Replace the last 2 of the 13 D-2.2 stubs and consolidate WP-036A S1:

| Row | Symbol | Nature |
|---:|---|---|
| 41 | `PRINetModel` | full trainable model container: input `ResonanceLayer` + stacked `ResonanceLayer` + LayerNorm-between-layers + concept readout + clamped log-softmax, over the existing `layers::ResonanceLayer` |
| 42 | `compile_model` | pure-Python `torch.compile` passthrough (**D-2** — no PRIN numerics; the one symbol with no Rust component) |

## Contract

- **Acceptance:**
  - New Rust `crates/prin-train/src/model.rs`: `PRINetModel` over the
    existing `layers::ResonanceLayer` (input + `n_layers-1` stacked) +
    LayerNorm + concept readout + clamped log-softmax. New PyO3 bridge (thin
    marshalling; unsafe-free; audited DLPack). No Python numerics.
  - `compile_model` is a real guarded `torch.compile` wrapper in
    `python/prin/nn/`; construction/callable + `torch.compile` smoke test;
    no `# pragma: no cover`.
  - `PRINetModel` resolves from `prin` / `prin.nn` as a real implementation;
    float64 `gradcheck(rtol=1e-3, atol=1e-3)` passes; forward-pass parity vs
    `prinet.nn.layers.PRINetModel` within documented tolerance (**D-4**).
  - `compile_model` constructs a `PRINetModel` from a configuration dict and
    returns a callable model (0144A brief acceptance line).
  - **Consolidation:**
    - Migration Guide (`DOCS/sphinx/migration_guide.rst`): all 13 rows read
      "real implementation" with the delegation path; no silent removals.
    - `tools/check_no_python_numerics.py` clean with the updated allowed
      module count.
    - `verify_api_surface(prin.__all__) == (set(), set())` re-confirmed
      (WP-036A adds no public symbols).
    - Full construct/callable smoke over all 13 symbols.
    - `_prin_core.pyi` completeness check (0141E check) green;
      `mypy --strict` clean.
    - **S1 handoff note** in `DOCS/experiments/0144A-wp036a-s1-handoff.md`:
      each of the 13 symbols → Rust owner module, PyO3 binding, test count,
      gradcheck result; every 0144A acceptance criterion → evidence
      (aggregate across `0144A1`–`0144A4`).
  - Rust + Python gates green across the full `0144A1`–`0144A4` range.
- **Non-goals:** the S2 audit (`0144B`); acceptance-suite port; GPU/CUDA;
  `retrain_controller` (DV-025, WP-036C S1 / `0144I`).

## Required reading

- The 0144A brief, the decomposition plan, the `0144A1`–`0144A3` sub-pass
  handoffs
- `crates/prin-train/src/layers.rs` (`ResonanceLayer`),
  `crates/prin-py/src/bindings/train.rs` (`PyResonanceLayerBridge`)
- `prinet/nn/layers.py` `PRINetModel` / `compile_model` /
  `oscillatory_weight_init`
- `DOCS/sphinx/migration_guide.rst`; `tools/check_no_python_numerics.py`
- `DOCS/standards/Coding_Standards.md` §2.1/§2/§6; `Testing_Standards.md` §1/§4
- `DOCS/sphinx/parity_report.rst`; latest PSR and cumulative deviation ledger

## Entry conditions

- `0144A1`–`0144A3` (and `0144A3a`/`0144A3b` if split) committed at their
  green local gates; no unresolved D1/D2.
- maturin builds on this host; else reported blocked per CLAUDE.md.

## Expected work

1. `PRINetModel` Rust + autodiff gradient tests; PyO3 bridge; `maturin
   develop`; verify import.
2. Replace the `PRINetModel` / `compile_model` stubs.
3. gradcheck + parity + `compile_model` integration + construction/error
   tests; ≥95% coverage on new/changed code.
4. Consolidation deliverables (Migration Guide 13 rows, numerics check,
   `verify_api_surface`, smoke matrix, stub-completeness).
5. Full local gate over the whole `0144A1`–`0144A4` range; Snyk Code / Open
   Source / `cargo audit` / `pip-audit` as applicable.
6. Write the S1 handoff note. S1 may not self-certify — hand off to `0144B`.

## Prohibited

Deferred tests, weakened assertions/tolerances, Python or `prin-py` numerics
(beyond the D-2 `compile_model` `torch.compile` passthrough), undocumented
public API changes, hidden RNG, unapproved `unsafe`, scope creep,
unregistered experimentation, S1 self-certification.

## Exit gate

All S1 gates green across `0144A`+`0144A1`–`0144A4`; every 0144A acceptance
criterion is evidence-mapped in the handoff note. Commit locally only. Hand
off to the mandatory S2 audit `0144B`; the contiguous range is pushed once
with `0144B` (amendment #28 cadence).
