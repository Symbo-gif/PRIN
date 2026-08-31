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

print(prin.__version__)
print(f"public symbols: {len(prin.__all__)}")
```

## Tutorial 1: Kuramoto synchronization

Create a mean-field Kuramoto network and watch the order parameter rise as the
oscillators synchronize:

```python
import torch
from prin import KuramotoOscillator, OscillatorState, kuramoto_order_parameter

osc = KuramotoOscillator(n_oscillators=32, coupling_strength=4.0,
                         coupling_mode="mean_field")
state = OscillatorState.create_random(32, seed=0)
for _ in range(200):
    state = osc.step(state, dt=0.01)
print("r =", kuramoto_order_parameter(state.phase).item())
```

## Tutorial 2: A hierarchical resonance layer

`prin.nn` layers are ordinary `torch.nn.Module`s. Numerics run in Rust; the
autograd graph is stitched through DLPack bridges:

```python
import torch
from prin.nn import DiscreteDeltaThetaGammaLayer

layer = DiscreteDeltaThetaGammaLayer(n_delta=4, n_theta=8, n_gamma=32,
                                     n_dims=128, n_steps=5)
x = torch.randn(16, 128)
amps = layer(x)          # (16, 44)
amps.sum().backward()
```

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

Symbols that moved namespace, or whose rebuild is owned by a later work
package, are listed with their disposition in
`DOCS/sphinx/migration_guide.rst`. Anything importable from `prinet` is
importable from `prin`; `prin.verify_api_surface(prin.__all__)` returns no
missing symbols.
