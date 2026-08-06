# prin-py

PyO3 extension crate for PRIN — the only crate that links Python. Built with
maturin into the `prin._prin_core` extension module inside the `prin` wheel.

The Phase 0 scaffold currently exposes version metadata only. WP-001 upgraded
the compatible PyO3/rust-numpy pair to 0.29.0 and set the workspace MSRV to
Rust 1.83. DLPack exchange, Rust-backed forward/backward bridges, and generated
extension stubs land in their registered future work packages.

Build for development:

```bash
maturin develop -m crates/prin-py/Cargo.toml
```
