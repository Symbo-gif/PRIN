# Contributing to PRIN

Thank you for your interest in contributing to PRIN! This document describes the
contribution workflow. The authoritative engineering standards live in
[`DOCS/standards/`](DOCS/standards/) — read them before opening a pull request:

- [Development Workflow and Audit Standards](DOCS/standards/Development_Workflow_and_Audit_Standards.md) — how all work is executed
- [Coding Standards](DOCS/standards/Coding_Standards.md) (Rust + Python + security)
- [Testing Standards](DOCS/standards/Testing_Standards.md)
- [Documentation Standards](DOCS/standards/Documentation_Standards.md)
- [Benchmarking and Reproducibility Standards](DOCS/standards/Benchmarking_and_Reproducibility_Standards.md)
- [Experimentation Standards](DOCS/standards/Experimentation_Standards.md)
- [Versioning and Release Standards](DOCS/standards/Versioning_and_Release_Standards.md)

## The Session Cycle

All planned work — including maintainer and AI-pair work — advances through
the fixed session order **S1 Coding (tests in tandem) → S2 Audit →
S3 Remediation → S4 Documentation**, with artefacts in `DOCS/audits/` and
`DOCS/reports/`. The complete prospective sequence and one brief per session
are in `DOCS/sessions/`; contributors must read the active brief before work.
External PRs are treated as S1 input and pass through the same audit gates.
Scientific experiments additionally require an approved pre-registration
**before** execution (expected results and failure conditions documented in
advance).

## Code of Conduct

By participating in this project, you agree to abide by our
[Code of Conduct](CODE_OF_CONDUCT.md).

---

## How to Contribute

### Reporting Bugs

Before filing a bug report:
1. Check existing issues to avoid duplicates.
2. Use the latest version of PRIN.
3. Reproduce the issue with the minimum code possible.

Include in the report:
- Python version, PRIN version, PyTorch version, Rust toolchain version
- OS and CUDA version (if applicable)
- Complete error traceback / panic backtrace
- Minimal reproducible example

### Feature Requests

Open an issue with the `enhancement` label describing the motivating use case,
the proposed API, and whether you intend to implement it.

### Pull Requests

1. **Fork** and branch from `main` using a typed branch name:
   ```bash
   git checkout -b feat/my-new-feature
   ```

2. **Set up** the development environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate            # Windows (source .venv/bin/activate on Linux/macOS)
   pip install maturin
   maturin develop -m crates/prin-py/Cargo.toml
   pip install -e ".[dev]"
   ```

3. **Write tests in tandem with code** — same PR, same commits; "tests later"
   is non-conforming. New code requires ≥ 95% coverage. Changes touching
   numerics require parity/property tests
   (see [Testing Standards](DOCS/standards/Testing_Standards.md)).

4. **Run the full local gate** before pushing:
   ```bash
   cargo fmt --all -- --check
   cargo clippy --workspace --all-targets -- -D warnings
   cargo test --workspace
   RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps
   ruff check python/ tests/ benchmarks/ tools/
   ruff format --check python/ tests/ benchmarks/ tools/
   mypy python/prin --strict
   interrogate -c pyproject.toml python/prin
   bandit -r python/prin -c pyproject.toml
   pytest tests/ -v -m "not slow and not gpu"
   ```

5. **Update documentation** for any added or changed public API
   (docstrings/rustdoc + Sphinx pages + Migration Guide if a 3.0 symbol is affected).

6. **Submit the PR** with a clear description, linked issues, and a test summary.
   CI must be fully green; at least one maintainer review is required.

---

## Commit Messages

PRIN uses [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add community topology coupling mode
fix: correct phase wrap-around in ring coupling
docs: add OscilloSim chimera tutorial
test: add kernel-equivalence test for fused RK4
perf: 2x speedup in local order parameter computation
refactor: extract binding logic into prin-dynamics::bands
chore: bump ndarray to 0.16
```

Add `[gpu]` to a commit message to trigger the opt-in self-hosted GPU CI job.

---

## Questions?

Open an issue with the `question` label or email **therealmichaelmaillet@gmail.com**.
