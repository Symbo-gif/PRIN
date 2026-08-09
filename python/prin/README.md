# prin (Python layer)

The pure-Python layer of PRIN. Design rule: **this layer contains no numerics**
— it holds API ergonomics, torch glue, plotting, and orchestration only. All
math lives in the Rust core, reached through the `prin._prin_core` extension
(built from `crates/prin-py`).

| Module | Contents | Phase |
|---|---|---|
| `__init__.py` | Public API (PRINet-3.0-compatible symbols) | 1–6 |
| `dynamics.py` | Re-export module for oscillator state, models, integrators, coupling, and PAC (20 symbols from `prin._prin_core`) | 1 |
| `metrics.py` | Re-export module for synchronization, coherence, spectral, energy, and chimera metrics (22 symbols from `prin._prin_core`) | 1 |
| `dlpack.py` | Zero-copy DLPack tensor exchange between PyTorch and the Rust core | 0 |
| `parity/` | Golden-trajectory corpus, manifest, loader, and differential harness | 0 |
| `_ort.py` | ONNX Runtime execution-provider probe for the subconscious controller (CPU/DirectML/VitisAI with graceful fallback); Phase 0 spike, daemon runtime owned by WP-028 | 0 |
| `_phase0.py` | Phase 0 exit-gate evidence consolidation — validates the three foundation spikes, golden corpus, abi3 wheel matrix, and recorded go/no-go decisions before the Phase 0 pre-release tag | 0 |
| `nn/` | torch wrappers, `autograd.Function` bridges, SlotAttention baselines | 4 |
| `eval/` | MOT evaluation, temporal metrics | 5 |
| `experiments/` | ablation, stats, adversarial, fair-training frameworks | 5 |
| `reporting/` | benchmark JSON, figures, tables, profiler | 1, 6 |
| `datasets.py` | CIFAR-10 / Fashion-MNIST loaders, temporal CLEVR-N generator | 1 |
| `_prin_core.pyi` | generated stubs for the compiled extension | 0+ |
