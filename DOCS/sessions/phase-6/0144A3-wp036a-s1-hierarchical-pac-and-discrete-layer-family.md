# Session 0144A3 — WP-036A S1 (sub-pass 3/4): Hierarchical, PAC, and discrete-layer family

**Status:** COMPLETE (2026-08-31)
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036A
**Session type:** S1 — Coding
**Predecessor:** [0144A2 — phase-to-rate and autoencoder family](0144A2-wp036a-s1-phase-to-rate-and-autoencoder-family.md)
**Successor:** [0144A4 — model container and consolidation](0144A4-wp036a-s1-model-container-and-consolidation.md)
**Authority:** Project Plan §6/§8, amendments #33/#34, the decomposition plan
[`WP-036A-S1-execution-plan-and-decomposition.md`](WP-036A-S1-execution-plan-and-decomposition.md).
Standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Replace 3 of the 13 D-2.2 stubs with real `prin-train` Rust implementations +
PyO3 bridges + Python `nn.Module`s:

| Row | Symbol | Nature |
|---:|---|---|
| 39 | `HierarchicalResonanceLayer` | trainable `nn.Module`: batched Burn port of the **continuous** delta/theta/gamma network + learnable per-band projections + learnable PAC depths |
| 40 | `PhaseAmplitudeCouplingLayer` | trainable `nn.Module`: Burn PAC `modulate` + learnable `modulation_depth` |
| 44 | `DiscreteDeltaThetaGammaLayer` | trainable `nn.Module` over the existing batched `bands::DiscreteDeltaThetaGamma` (WP-022) + new `proj_phase` / `proj_amplitude` linear projections |

## Split authorisation

This sub-pass is **pre-authorised to split** into `0144A3a` (row 39 — the
continuous three-band-network Burn port, the single largest new-numerics
item) and `0144A3b` (rows 40, 44) under Development Workflow §7, on the same
rule and precedent as `0141D` → `0141D1`/`0141D2`. If it splits, each part
commits at its own green local gate, both feed `0144B`, and `0144A4`'s
predecessor becomes `0144A3b`.

## Contract

- **Acceptance:**
  - New Rust `crates/prin-train/src/hierarchical_layers.rs`: a batched
    (`[batch, n_total]`, **D-5** — no per-sample loop) Burn port of the
    continuous 3-band network (per-band Kuramoto phase coupling +
    Stuart–Landau amplitude + delta→theta and theta→gamma PAC),
    `HierarchicalResonanceLayer` (learnable `proj_delta`/`proj_theta`/
    `proj_gamma` + learnable `pac_depth_dt`/`pac_depth_tg`, `return_phase`
    path), `PhaseAmplitudeCouplingLayer`, `DiscreteDeltaThetaGammaLayer`.
    No Python numerics.
  - New PyO3 bridges (thin marshalling; unsafe-free; audited DLPack).
  - The 3 symbols resolve from `prin` / `prin.nn` as real implementations.
  - float64 `gradcheck(rtol=1e-3, atol=1e-3)` passes for all 3 (including the
    `return_phase` output for row 39). DV-018 tolerance where applicable,
    documented at the call site.
  - Forward-pass parity vs `prinet.nn.layers` within documented tolerance
    (**D-4**); the batched-vs-per-sample equivalence for row 39 is a
    documented D3 "better design" Migration-Guide note (**D-5**).
  - `_prin_core.pyi` + `.pyi` updated; `mypy --strict` clean.
  - Rust gates green (`fmt`, clippy `-D warnings`, tests, rustdoc).
  - `verify_api_surface(prin.__all__) == (set(), set())` unchanged.
  - Migration Guide rows for the 3 symbols → "real implementation".
- **Non-goals:** `PRINetModel` / `compile_model` / consolidation (`0144A4`);
  the `DiscreteDeltaThetaGamma` standalone core binding (row 43, WP-036B S1 /
  `0144E`); acceptance-suite port; GPU/CUDA.

## Required reading

- The 0144A brief, the decomposition plan, the 0144A1/0144A2 sub-pass handoffs
- `crates/prin-dynamics/src/{bands.rs,pac.rs}` (non-autodiff owners being
  ported), `crates/prin-train/src/bands.rs` (`DiscreteDeltaThetaGamma`
  batched-Kuramoto + Stuart–Landau + PAC reference structure)
- `prinet/nn/layers.py` `HierarchicalResonanceLayer` /
  `PhaseAmplitudeCouplingLayer` / `DiscreteDeltaThetaGammaLayer`,
  `prinet/core/propagation/` band network + PAC
- `crates/prin-py/src/bindings/{bands.rs,train.rs,train_layers.rs}`
- `DOCS/standards/Coding_Standards.md` §2.1/§2/§6; `Testing_Standards.md` §1/§4
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-018;
  `DOCS/sphinx/parity_report.rst`; latest PSR and deviation ledger

## Entry conditions

- 0144A2 committed at its green local gate; no unresolved D1/D2.
- maturin builds on this host; else reported blocked per CLAUDE.md.

## Expected work

1. Rust (continuous band-network port first) + autodiff gradient tests.
2. PyO3 bridges; `maturin develop`; verify import.
3. Replace the Python stubs; record module placement.
4. gradcheck + parity + construction/error tests; ≥95% coverage.
5. `.pyi`; full local gate; Snyk Code / Open Source / `cargo audit` /
   `pip-audit` as applicable.
6. If splitting, record the split in the handoff and the register (mirror
   `0141D`); append a sub-pass handoff note.

## Prohibited

Deferred tests, weakened assertions/tolerances, Python or `prin-py` numerics,
reproducing the reference's per-sample Python loop, undocumented public API,
hidden RNG, unapproved `unsafe`, scope creep into `0144A4`, unregistered
experimentation.

## Exit gate

Local gate green; acceptance items evidence-mapped. Commit locally only.
Proceed to 0144A4.

## Completion evidence (2026-08-31)

- Rust owner: `crates/prin-train/src/hierarchical_layers.rs` implements the
  fully batched continuous three-band RK4/PAC network, all three trainable
  modules, seeded projections, reference-parameter injection, checkpoint
  records, and autodiff. `crates/prin-train/src/bands.rs` exposes the existing
  discrete core's validated parameters for composition. No Python numerics.
- PyO3: `crates/prin-py/src/bindings/train_hierarchical_layers.rs` provides
  three thin DLPack bridges and recompute-on-backward contexts;
  `#![deny(unsafe_code)]` remains unchanged.
- Python: `prin.nn.hierarchical_layers` replaces all three D-2.2 stubs while
  `prin.nn.deferred_layers` retains compatibility re-exports. The frozen API
  check remains `verify_api_surface(prin.__all__) == (set(), set())`.
- Tests: 12 Python parity/gradcheck/API/error/checkpoint tests and 17 Rust unit/
  autodiff tests. Continuous amplitude/phase parity passes at
  `rtol=1e-9, atol=1e-11`; PAC at `rtol=1e-8, atol=1e-9`; discrete parity uses
  the documented DV-018 `rtol=2e-7, atol=2e-8` envelope (measured maximum
  relative delta `1.39e-7`). All three float64 gradchecks pass at the required
  `rtol=1e-3, atol=1e-3`. The D-5 batched path equals stacked vector calls at
  `rtol=1e-12, atol=1e-12`.
- Gates: Rust formatting, workspace clippy `-D warnings`, workspace tests, and
  rustdoc are green. `cargo llvm-cov -p prin-train --lib` reports 99.79% line
  coverage for `hierarchical_layers.rs`. Ruff check/format, `mypy --strict`,
  interrogate (97.4% package documentation), full Bandit, no-Python-numerics,
  the migration-table check, a clean Sphinx build, and the full fast Python
  suite (1253 passed, 9 deselected; 99% package coverage) are green.
  `maturin develop` succeeded on Windows / Python 3.14 / Rust 1.92.
- Security: scoped Snyk Code at severity `low` reports zero findings in every
  changed implementation/test/tool file. The whole-repository scan retains
  five pre-existing low path-traversal findings in three unrelated tools.
  No dependency manifest changed, so Snyk Open Source is not applicable.
  `cargo audit` exits 0 with the three governed warnings (`bincode`, `paste`,
  `chacha20`); both project and Sphinx-requirement `pip-audit` scans report no
  known vulnerabilities. Two pre-existing Bandit B101 findings in the manual
  M-F9 verification script were remediated with explicit failures and the
  script was rerun successfully.
- Migration Guide, consolidated 172-symbol table, parity report, session
  registers, and the 0144A handoff now record the real 0144A3 implementations,
  tolerances, D-5 batching note, and verification evidence.
