# PRIN Getting Started Tutorial

## Installation

```bash
git clone https://github.com/michaelmaillet/PRIN.git
cd PRIN
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS
pip install -e ".[dev]"
maturin develop --release      # build the Rust core (prin._prin_core)
```

### Verify the installation

```python
import prin

print(prin.__version__)                 # 0.3.0
print(prin.core_version())              # version of the loaded Rust extension
print(f"public symbols: {len(prin.__all__)}")

from prin._deprecation import verify_api_surface

print(verify_api_surface(prin.__all__))  # (set(), set()) — freeze satisfied
```

`verify_api_surface` lives in `prin._deprecation`, not at the top level.

## Tutorial 1: Kuramoto synchronization

The float64 Rust core takes five required arguments and a `CouplingMode` value
(not a string), and is driven by an explicit integrator:

```python
import torch
from prin import kuramoto_order_parameter
from prin.dynamics import (
    CouplingMode,
    KuramotoOscillator,
    OscillatorState,
    RK4Integrator,
    Seed,
)

model = KuramotoOscillator(32, 4.0, 0.1, 0.0, CouplingMode.mean_field())
state = OscillatorState.create_random(32, (1.0, 5.0), Seed(0, 0))
integrator = RK4Integrator()
for _ in range(200):
    state = integrator.step(model, state, 0.01)
print("r =", kuramoto_order_parameter(torch.from_numpy(state.phase)).item())
```

For a higher-level, `torch.Tensor`-facing simulator with throughput reporting
and trajectory recording, use `prin.OscilloSim` / `prin.quick_simulate` — see
`DOCS/sphinx/getting_started.rst` and `notebooks/01_oscillosim_quickstart.ipynb`.
Note that `OscilloSim`'s `coupling_strength` is scaled differently from the
core's Kuramoto `K`; do not compare the two directly.

## Tutorial 2: A hierarchical resonance layer

`prin.nn` layers are ordinary `torch.nn.Module`s. Numerics run in Rust; the
autograd graph is stitched through DLPack bridges.

```python
import torch
from prin.nn import DiscreteDeltaThetaGamma

net = DiscreteDeltaThetaGamma(n_delta=4, n_theta=8, n_gamma=32)
phase = torch.rand(16, net.n_total) * 2 * torch.pi
amplitude = torch.ones(16, net.n_total)

phase, amplitude = net.step(phase, amplitude, dt=0.01)
(phase.sum() + amplitude.sum()).backward()
print(sum(p.grad is not None for p in net.parameters()))   # 13
```

`DiscreteDeltaThetaGamma` declares its per-band frequencies, coupling matrices,
PAC gates, and amplitude growth rates as real `nn.Parameter`s, so a torch
optimizer can train it. **Not every layer does:** `DiscreteDeltaThetaGammaLayer`
and `ResonanceLayer` keep their weights inside the Rust bridge — input gradients
still flow, but `parameters()` is empty or disconnected from `forward`. Check
`sum(p.numel() for p in layer.parameters())` before handing a layer to an
optimizer; see `notebooks/04_torch_bridge.ipynb` §6.

## Tutorial 3: Phase-to-rate readout

```python
import torch
from prin.nn import PhaseToRateConverter

conv = PhaseToRateConverter(n_oscillators=44, mode="soft", sparsity=0.1)
phase = torch.randn(8, 44)
amplitude = torch.ones(8, 44)
rates = conv(phase, amplitude)
print(rates.shape)       # (8, 44)
```

## Migrating from prinet

PRIN keeps the PRINet 3.0 public API. In most code you only change the import
root:

```python
# old
from prinet import KuramotoOscillator, PRINetModel
import prinet

# new
from prin import KuramotoOscillator, PRINetModel
import prin
```

Two namespace changes trip people up: `CouplingMode`, `Seed`, `RK4Integrator`,
and the other core value types are in `prin.dynamics`; `chimera_index`,
`cosine_coupling_kernel`, and `strength_of_incoherence` are in
`prin.simulation`.

Symbols that moved namespace, or whose rebuild is owned by a later work
package, are listed with their disposition in
`DOCS/sphinx/migration_guide.rst`. Anything importable from `prinet` is
importable from `prin`; `verify_api_surface(prin.__all__)` returns no
missing symbols.

---

Every code block above was executed against PRIN 0.3.0 (CPython 3.14, torch
2.11, CPU) at WP-037 S1 (session `0145`), per Documentation Standards §1.4
("Examples must run"). The rendered version of this tutorial, with printed
output, is `DOCS/sphinx/getting_started.rst`.
