# prin (Python layer)

The pure-Python layer of PRIN. Design rule: **this layer contains no numerics**
— it holds API ergonomics, torch glue, plotting, and orchestration only. All
math lives in the Rust core, reached through the `prin._prin_core` extension
(built from `crates/prin-py`).

| Module | Contents | Phase |
|---|---|---|
| `__init__.py` | Public API (PRINet-3.0-compatible symbols) | 1–6 |
| `parity/` | Golden-trajectory corpus, manifest, loader, and differential harness | 0 |
| `nn/` | torch wrappers, `autograd.Function` bridges, SlotAttention baselines | 4 |
| `eval/` | MOT evaluation, temporal metrics | 5 |
| `experiments/` | ablation, stats, adversarial, fair-training frameworks | 5 |
| `reporting/` | benchmark JSON, figures, tables, profiler | 1, 6 |
| `datasets.py` | CIFAR-10 / Fashion-MNIST loaders, temporal CLEVR-N generator | 1 |
| `_prin_core.pyi` | generated stubs for the compiled extension | 0+ |
