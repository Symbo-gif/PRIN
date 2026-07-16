# prin-py

PyO3 extension crate for PRIN — the only crate that links Python. Built with
maturin into the `prin._prin_core` extension module inside the `prin` wheel.

- Zero-copy tensor exchange with PyTorch via DLPack.
- Rust forward/backward exposed for `torch.autograd.Function` bridges.
- Generated type stubs: `python/prin/_prin_core.pyi`.

Build for development:

```bash
maturin develop -m crates/prin-py/Cargo.toml
```
