# tests/ — pytest acceptance suite

The PRINet 3.0 pytest suite (37 files, ~1,670 tests) is the **acceptance
contract** for PRIN: it defines the public API. It will be ported incrementally
with imports adapted (`prinet` → `prin`) and assertions otherwise unchanged.

Additional PRIN-specific suites (per the Testing Standards):

- `test_wp001_baseline.py` — 44 fail-closed metadata, session-ledger,
  traceability, CI, release-guard, and security-control tests. Validates that
  `rust-toolchain.toml` includes `rustfmt` and `clippy`, optionally `llvm-tools`
  for `cargo-llvm-cov`.
- `test_parity_*.py` — fast unit tests for `prin.parity` schema, loader,
  manifest, harness, and Hypothesis strategies.
- `test_dlpack_bridge.py` — CPU round-trip, batched boundary, dtype/device
  validation, ownership/error-path, and `pytest-benchmark` latency tests for
  the WP-003 PyO3/DLPack bridge (marker `slow` for the benchmark cases).
- `test_gradcheck_*.py` — `torch.autograd.gradcheck` (float64) for every
  `autograd.Function` bridge.
- `test_gpu_*.py` — GPU integration tests, marker `gpu` (opt-in, self-hosted
  runner, `[gpu]` commit-message trigger).
- Differential parity tests live in `../parity/`.
- Rust unit/property tests live next to each crate (`cargo test`).

Run locally:

```bash
pytest tests/ -v -m "not slow and not gpu"
```
