# tests/ — pytest acceptance suite

The PRINet 3.0 pytest suite (37 files, ~1,670 tests) is the **acceptance
contract** for PRIN: it defines the public API. It will be ported incrementally
with imports adapted (`prinet` → `prin`) and assertions otherwise unchanged.

Additional PRIN-specific suites (per the Testing Standards):

- `test_wp001_baseline.py` — 44 fail-closed metadata, session-ledger,
  traceability, CI, release-guard, and security-control tests.
- `test_gradcheck_*.py` — `torch.autograd.gradcheck` (float64) for every
  `autograd.Function` bridge.
- `test_gpu_*.py` — GPU integration tests, marker `gpu` (opt-in, self-hosted
  runner, `[gpu]` commit-message trigger).
- Parity tests live in `../parity/`.
- Rust unit/property tests live next to each crate (`cargo test`).

Run locally:

```bash
pytest tests/ -v -m "not slow and not gpu"
```
