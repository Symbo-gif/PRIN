# API Reference — Coupling Topologies

PRIN oscillator models accept a coupling specification selecting how each
oscillator is influenced by the others. All modes are implemented in the Rust
core (`crates/prin-dynamics/src/coupling.rs`).

There are **two surfaces**, and they are not interchangeable:

| Surface | Coupling argument | Accepted values |
|---|---|---|
| Rust core (`prin.dynamics`) | a `CouplingMode` **value** | `CouplingMode.mean_field()`, `CouplingMode.full(matrix=...)`, `CouplingMode.sparse_knn(k=...)` |
| Simulator (`prin.OscilloSim`) | a `coupling_mode` **string** | `"auto"`, `"mean_field"`, `"csr"`, `"ring"`, `"small_world"`, `"sparse_knn"` |

`"full"` is not a valid `OscilloSim` mode; a dense custom interaction matrix is
only reachable through the core's `CouplingMode.full`.

The rendered version of this reference, with the full catalogue and the
`"auto"` resolution thresholds, is `DOCS/sphinx/coupling_topologies.rst`.

## Core surface

`CouplingMode` is **not** re-exported at the top level — import it from
`prin.dynamics`. `KuramotoOscillator` takes five required arguments and is
driven by an explicit integrator:

```python
import numpy as np
import torch
from prin import kuramoto_order_parameter
from prin.dynamics import (
    CouplingMode,
    KuramotoOscillator,
    OscillatorState,
    RK4Integrator,
    Seed,
)

model = KuramotoOscillator(
    4096,                            # n_oscillators
    1.5,                             # coupling_strength (K)
    0.1,                             # decay_rate
    0.0,                             # freq_adaptation_rate
    CouplingMode.sparse_knn(k=16),   # coupling_mode — a value, not a string
)
state = OscillatorState.create_random(4096, (1.0, 5.0), Seed(0, 42))
integrator = RK4Integrator()
for _ in range(200):
    state = integrator.step(model, state, 0.01)
print(kuramoto_order_parameter(torch.from_numpy(state.phase)).item())
```

### `mean_field`

Every oscillator couples to the population mean phase. Cost is `O(N)` per step.
This is the right choice for global synchronization studies.

### `full`

All-to-all pairwise coupling, `O(N^2)` per step. Use for small populations
where the exact interaction matrix matters. `matrix` is a **flat row-major
`float64` NumPy array of length `N * N`**; a 2-D array raises `TypeError` and a
wrong length raises `ValueError: field 'coupling_matrix' length ... does not
match expected ...`.

```python
n = 32
weights = np.zeros((n, n))
weights[: n // 2, : n // 2] = 1.0        # two clusters
weights[n // 2 :, n // 2 :] = 1.0

model = KuramotoOscillator(
    n, 2.0, 0.1, 0.0,
    CouplingMode.full(matrix=np.ascontiguousarray(weights.ravel())),
)
```

### `sparse_knn`

Each oscillator couples only to its `k` nearest neighbours in phase space; the
neighbour set is rebuilt each step. Cost is `O(N k)`. This is the scalable mode
for large populations.

Degenerate arguments are **rejected with a typed error, not silently repaired**.
The invariant is `1 <= k < N`:

```python
CouplingMode.sparse_knn(k=0)   # with N=8 -> ValueError: invalid k-NN count: k=0 must be less than N=8
CouplingMode.sparse_knn(k=100) # with N=8 -> ValueError: invalid k-NN count: k=100 must be less than N=8
```

A single-oscillator network has no neighbours and must use `mean_field()` or
`full()`.

### `Topology` builders

`Topology.build_matrix(n, coupling_strength)` returns the same flat row-major
layout `CouplingMode.full` consumes, so the two compose directly:

```python
from prin.dynamics import Seed, Topology

Topology.all_to_all().build_matrix(8, 2.0).shape                 # (64,) — 56 non-zero
Topology.ring(4).build_matrix(8, 2.0).shape                      # (64,) — 32 non-zero
Topology.small_world(4, 0.3, Seed(0, 42)).build_matrix(8, 2.0)   # (64,)
```

## Simulator surface

```python
from prin import OscilloSim

sim = OscilloSim(n_oscillators=256, coupling_strength=2.5,
                 coupling_mode="small_world", k_neighbors=8,
                 p_rewire=0.2, integrator="rk4", seed=0)
result = sim.run(n_steps=200, dt=0.01)
print(sim.coupling_mode)      # the *resolved* mode
```

`"auto"` resolves once at construction from `n_oscillators`: `"csr"` below
1 000, `"sparse_knn"` from 1 000 to 99 999, `"mean_field"` at 100 000 and above.

`coupling_weights` supplies an `(N, k)` per-edge weight tensor for the
neighbour-based modes; passing one with a mode that has no `k` columns raises
`ValueError: dimension mismatch`. `prin.simulation.cosine_coupling_kernel(n, k, A)`
produces exactly such a tensor (the Abrams–Strogatz kernel).

> **`OscilloSim` coupling strength is not the textbook Kuramoto `K`.** The
> simulator is a line-for-line port of the PRINet 3.0 step equations, which
> scale the coupling term differently from the core's mean-field Kuramoto model.
> Verified differentially against `prinet==3.0.0` at WP-037 S1: at
> `freq_std=0.5` the simulator needs `K ≈ 8` to synchronize where the core
> synchronizes at `K = 1` for a comparable spread, and PRIN tracked the
> reference to within 0.04 in `R` across the whole sweep. Do not compare an
> `OscilloSim` `K` against a `KuramotoOscillator` `K`, or either against the
> analytic `K_c = 2 / (pi * g(0))`.

## Neighbour-index tensors and chimera diagnostics

```python
import torch
from prin import local_order_parameter, ring_topology, small_world_topology
from prin.simulation import chimera_index, cosine_coupling_kernel, strength_of_incoherence

neighbours = ring_topology(256, 6)                    # (256, 6) int64
small_world_topology(256, 6, p_rewire=0.3, seed=0)    # (256, 6) int64

phase = torch.rand(256) * 2 * torch.pi
local_order_parameter(phase, neighbours)              # (256,)
chimera_index(phase, neighbours, threshold=0.5)       # float
strength_of_incoherence(phase, window_size=10)        # 0-dim tensor
```

`chimera_index`, `cosine_coupling_kernel`, and `strength_of_incoherence` are in
`prin.simulation`, **not** at the top level. A custom topology at this level is
just an `(N, k)` integer tensor of neighbour indices — every diagnostic above
accepts one unchanged.

`strength_of_incoherence` is deliberately **not** parity-matched to the PRINet
3.0 fixture: the reference's wrap-centring formula is an upstream defect
(EMA-001 M-F1, Z3-confirmed), so PRIN's corrected `prin-metrics::chimera`
implementation is authoritative (Project Plan amendment #25).

## Hierarchical band networks

`HierarchicalResonanceLayer` and `DiscreteDeltaThetaGamma` partition oscillators
into delta / theta / gamma bands. Intra-band dynamics use the per-band coupling
strength; cross-band interaction is phase–amplitude coupling (slow mean phase
modulates fast amplitude).

| Parameter | Meaning |
|---|---|
| `coupling_strength` | intra-band Kuramoto gain K |
| `pac_depth` | single modulation depth in [0, 1] — `DiscreteDeltaThetaGamma`, `DiscreteDeltaThetaGammaLayer`, `HierarchicalResonanceLayer` |
| `pac_depth_dt` / `pac_depth_tg` | delta→theta and theta→gamma depths. On `HierarchicalResonanceLayer` these are its **two learnable `nn.Parameter`s** — `[n for n, _ in layer.named_parameters()]` returns exactly `['pac_depth_dt', 'pac_depth_tg']` |
| `n_delta`, `n_theta`, `n_gamma` | per-band oscillator counts; `n_total` is their sum (the output width) |
| `sparse_k` | optional; switches intra-band coupling to sparse k-NN |

```python
import torch
from prin.nn import DiscreteDeltaThetaGamma, HierarchicalResonanceLayer

layer = HierarchicalResonanceLayer(n_delta=4, n_theta=8, n_gamma=32,
                                   n_dims=64, n_steps=5)
amplitudes = layer(torch.randn(8, 64))                    # (8, 44)
amplitudes, phases = layer(torch.randn(8, 64), return_phase=True)

net = DiscreteDeltaThetaGamma(n_delta=4, n_theta=8, n_gamma=32)
phase = torch.rand(16, net.n_total) * 2 * torch.pi
r_delta, r_theta, r_gamma = net.order_parameters(phase)   # each in [0, 1]
```

Per-band order parameters are available from
`DiscreteDeltaThetaGamma.order_parameters(phase)` and return values in `[0, 1]`.
The continuous `BandNetwork.theoretical_capacity(state)` gives the θ/γ nesting
ratio — see `DOCS/sphinx/capacity_analysis.rst`.

---

Every code block above was executed against PRIN 0.3.0 (CPython 3.14, torch
2.11, CPU) at WP-037 S1 (session `0145`), per Documentation Standards §1.4
("Examples must run").
