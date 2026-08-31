# API Reference — Coupling Topologies

PRIN oscillator models accept a `coupling_mode` selecting how each oscillator
is influenced by the others. All three modes are implemented in the Rust core
(`crates/prin-dynamics/src/coupling.rs`) and exposed through the Python
`coupling_mode=` argument or a `prin.CouplingMode` value.

## `mean_field`

Every oscillator couples to the population mean phase. Cost is `O(N)` per step.
This is the default and the right choice for global synchronization studies.

```python
from prin import KuramotoOscillator
osc = KuramotoOscillator(n_oscillators=64, coupling_strength=2.0,
                         coupling_mode="mean_field")
```

## `full`

All-to-all pairwise coupling, `O(N^2)` per step. Use for small populations
(N ≤ ~256) where the exact interaction matrix matters, e.g. phase-diagram
sweeps at fixed N.

## `sparse_knn`

Each oscillator couples only to its `k` nearest neighbours in phase space; the
neighbour set is rebuilt each step. Cost is `O(N k)`. This is the scalable
mode for large populations. For `N <= 1` or `k < 1` PRIN falls back to `full`
coupling so degenerate cases stay well defined.

```python
from prin import CouplingMode, KuramotoOscillator
osc = KuramotoOscillator(n_oscillators=4096, coupling_strength=1.5,
                         coupling_mode=CouplingMode.sparse_knn(k=16))
```

## Hierarchical band networks

`DeltaThetaGammaNetwork` and `DiscreteDeltaThetaGamma` partition oscillators
into delta / theta / gamma bands. Intra-band dynamics use the per-band
`coupling_mode`; cross-band interaction is phase-amplitude coupling (slow phase
modulates fast amplitude) with depths `pac_depth_dt` and `pac_depth_tg`.

| Parameter | Meaning |
|---|---|
| `coupling_strength` | intra-band Kuramoto gain K |
| `pac_depth_dt` | delta→theta modulation depth ∈ [0, 1] |
| `pac_depth_tg` | theta→gamma modulation depth ∈ [0, 1] |
| `n_delta`, `n_theta`, `n_gamma` | per-band oscillator counts |

Order parameters per band are available from `net.order_parameters(state)` and
return values in `[0, 1]`.
