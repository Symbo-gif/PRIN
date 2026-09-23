# .github/workflows/ — hosted CI/CD gates

| Workflow | Current role |
|---|---|
| `rust.yml` | Formatting, Clippy, cross-platform tests, rustdoc, Cargo Audit, and CubeCL CPU kernel-equivalence tests (`cargo test -p prin-kernels --features cpu`) |
| `python.yml` | Lint/type/doc/security gates and Python 3.11–3.13 Linux/Windows tests; installs the `onnx` extra on every matrix cell so the real ORT probe runs cross-platform; the `docs` job builds Sphinx warning-free, executes shipped guide examples, and runs all four notebooks under the committed `ci/docs-constraints.txt` pin |
| `parity.yml` | Differential corpus gate; runs when `parity/` cases are present |
| `gpu.yml` | Required self-hosted Windows GPU validation on each push/PR and nightly schedule |
| `gpu-triton.yml` | Dormant DV-001 same-hardware PRIN CUDA / PRINet 3.0 Triton comparison; manually activated after a `[self-hosted, linux, gpu]` runner is registered |
| `repro.yml` | Reproduction pipeline: tamper tests + verified figure/table regeneration from the SHA-256 manifest (WP-035) |
| `nightly.yml` | Scheduled (05:00 UTC) full suite — `pytest tests/ parity/` incl. `slow`, `cargo test --features strict-checks` — plus the enforcing criterion / pytest-benchmark regression gate (`tools/check_bench_regression.py`, >10% mean slowdown fails); Testing Standards §2/§4, ETCA-001 T-F7. DV-036: reference SHA 4590d611f34eae5dfcdadb99b562aacf998d6e94 and candidate measured sequentially on the same runner with matched dependencies; raw paired evidence uploaded even on failure; incomplete measurements fail closed. |
| `release.yml` | Three-OS abi3 wheel matrix (manylinux x86_64/aarch64, Windows x86_64, macOS universal2), sdist, wheel smoke test, and PyPI OIDC / crates.io publication path |
| `snyk.yml` | Snyk Code plus required full-history Gitleaks secret scanning |

`main` requires the applicable checks. Native GitHub secret scanning is currently
unavailable for this private repository, so plan amendment #5 governs the
required Gitleaks and branch-protection substitute until native controls become
available.
