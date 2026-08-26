# benchmarks/ablations/ (structural ablation variants)

Rust-owned state size, identity preservation, and per-call wall time for each
structural ablation vs. its full baseline (frozen/static/no-GRU, adaptive
allocation) (WP-033). Consolidates 2 PRINet 3.0 legacy scripts — see
`DOCS/baselines/wp033_benchmark_traceability.md`.

## Contents

- `variant_comparison.py` — `ablation_variant_comparison`: compares
  `PhaseTrackerFrozen`/`PhaseTrackerStatic`/`SlotAttentionFrozen`/
  `SlotAttentionNoGRU` against their full baselines on a fixed, RNG-free
  detection sequence.

Measurement uses the Rust-backed ablation bridges in `prin.nn.ablation`; no
tracking numerics happens in this package. `n_parameters` is not used as the
comparison metric — every one of these classes' weights lives in the Rust
bridge (gradients flow through a custom `torch.autograd.Function`, not
`torch.nn.Parameter` registration), so `torch.nn.Module.parameters()` is
always empty. `rust_state_dict()`'s byte length is used instead.
