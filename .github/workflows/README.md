# .github/workflows/ — hosted CI/CD gates

| Workflow | Current role |
|---|---|
| `rust.yml` | Formatting, Clippy, cross-platform tests, rustdoc, Cargo Audit, and CubeCL CPU kernel-equivalence tests (`cargo test -p prin-kernels --features cpu`) |
| `python.yml` | Lint/type/doc/security gates and Python 3.11–3.13 Linux/Windows tests; installs the `onnx` extra on every matrix cell so the real ORT probe runs cross-platform |
| `parity.yml` | Differential corpus gate; runs when `parity/` cases are present |
| `gpu.yml` | Opt-in self-hosted GPU validation |
| `repro.yml` | Reproduction pipeline: tamper tests + verified figure/table regeneration from the SHA-256 manifest (WP-035) |
| `nightly.yml` | Scheduled (05:00 UTC) full suite — `pytest tests/ parity/` incl. `slow`, `cargo test --features strict-checks` — plus the enforcing criterion / pytest-benchmark regression gate (`tools/check_bench_regression.py`, >10% mean slowdown fails); Testing Standards §2/§4, ETCA-001 T-F7 |
| `release.yml` | Three-OS abi3 wheel matrix (manylinux x86_64/aarch64, Windows x86_64, macOS universal2), sdist, wheel smoke test, and PyPI OIDC / crates.io publication path |
| `snyk.yml` | Snyk Code plus required full-history Gitleaks secret scanning |

`main` requires the applicable checks. Native GitHub secret scanning is currently
unavailable for this private repository, so plan amendment #5 governs the
required Gitleaks and branch-protection substitute until native controls become
available.
