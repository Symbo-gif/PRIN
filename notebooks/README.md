# notebooks/

Tutorial notebooks for PRIN — three ported from PRINet 3.0 and one net-new
(project plan §11, Definition of Done #8). All four are committed **with their
executed outputs**, so reading a notebook shows what the API actually produced.

## Notebooks

| Notebook | Description | Measured runtime |
|---|---|---|
| [`01_oscillosim_quickstart.ipynb`](01_oscillosim_quickstart.ipynb) | **Oscillator dynamics and synchronization basics** — `quick_simulate` throughput, `OscilloSim` trajectory recording, a coupling-strength sweep through the Kuramoto transition, a coupling-mode comparison, and a ring chimera state diagnosed with `local_order_parameter` / `chimera_index`. | 86.4 s |
| [`02_clevr_n_binding.ipynb`](02_clevr_n_binding.ipynb) | **Hierarchical δ/θ/γ binding and multi-object tracking** — model architecture and parameter counts, a short real training run on synthetic temporal CLEVR-N, an object-count scaling sweep, oscillator phase dynamics during binding, and MOT evaluation via `evaluate_tracking`. | 65.6 s |
| [`03_custom_coupling.ipynb`](03_custom_coupling.ipynb) | **Custom coupling topologies and PAC** — the built-in topology builders, a custom two-cluster graph driven through the Rust core, a coupling-mode comparison, the PAC modulation curve, the Abrams–Strogatz cosine kernel, and rewiring probability vs synchronization speed. | 51.2 s |
| [`04_torch_bridge.ipynb`](04_torch_bridge.ipynb) | **New:** using the Rust core from PyTorch training loops — DLPack round-trips, the `autograd.Function` bridge, float64 `gradcheck`, Rust-native parameter checkpointing, and a canonical-parameter Adam loop that changes the next Rust-backed `ResonanceLayer` forward. | 35.4 s |

Runtimes are wall-clock for a full `nbclient` execution (kernel start included),
measured on the maintainer's Windows workstation, CPU-only, during WP-037 S4
(session `0148`) via `pytest tests/test_notebooks.py -m slow`. All four
together: **238.8 s**. Treat them as an order-of-magnitude budget for CI
sizing, not as a benchmark — Benchmarking and Reproducibility Standards require
the environment to travel with any quoted timing.

## Naming

`01`–`03` carry the PRINet 3.0 filenames because the ported acceptance suite is
parametrized over them (`tests/test_acceptance_y4q3.py::TestNotebooks.EXPECTED`)
and Project Plan amendment #35 froze ported-test parametrization and expected
values. The mapping from the names originally sketched for PRIN is:

| Originally sketched | Delivered as |
|---|---|
| `01_getting_started.ipynb` | `01_oscillosim_quickstart.ipynb` |
| `02_hierarchical_binding.ipynb` | `02_clevr_n_binding.ipynb` (δ/θ/γ bands, PAC, binding) |
| `03_multi_object_tracking.ipynb` | `02_clevr_n_binding.ipynb` (PhaseTracker MOT section) |
| — | `03_custom_coupling.ipynb` (coupling topologies, from the reference set) |
| `04_torch_bridge.ipynb` | `04_torch_bridge.ipynb` (unchanged) |

Four notebooks are delivered, satisfying Definition of Done #8 ("all four
notebooks run end-to-end") and the reference contract simultaneously.

## Getting started

```bash
pip install -e ".[dev]"
maturin develop -m crates/prin-py/Cargo.toml   # build the Rust core
jupyter notebook notebooks/
```

The notebooks need the compiled extension (`prin._prin_core`), so `maturin
develop` or an installed wheel is a prerequisite.

## Execution is a tested property

`tests/test_notebooks.py` executes all four end-to-end through `nbclient` and
fails on any error output — that harness, not this README, is the evidence for
Definition of Done #8. Its executing tests carry `@pytest.mark.slow`
(Testing Standards §4) and run in the full-suite leg; the cheap structural
invariants (`nbformat == 4`, cell counts, outputs present, stated runtime
budget, explicit seeding) run in the default gate.

```bash
# structural checks (fast gate)
pytest tests/test_notebooks.py -m "not slow"

# full end-to-end execution (~65 s)
pytest tests/test_notebooks.py -m slow
```

## Scaling

The reference notebooks targeted a CUDA workstation and were committed
unexecuted. PRIN's are sized to run on a shared CPU runner, so they use smaller
populations, fewer steps, and fewer epochs; each notebook says explicitly where
it scaled a reference value down and why.

**A notebook demonstrates an API. It does not establish a scientific result.**
Nothing here should be quoted as a measurement — the governed numbers live in
`benchmarks/results/` with their environment block, and PRIN's confirmatory
measurements are Phase 7 campaign work under the Experimentation Standards.

## License

MIT — see [LICENSE](../LICENSE).
