# PRIN Agent Notes

## Windows pytest temp-directory workaround

On Windows the default `%TEMP%` root used by `pytest` can leave stale
`pytest-current` directory junctions that fail cleanup with
`PermissionError: [WinError 5] Access is denied`.

If you hit this, run pytest with an in-repo basetemp:

```powershell
.venv\Scripts\python -m pytest <targets> --basetemp=.pytest_basetemp
```

The `.pytest_basetemp/` directory is ignored in `.gitignore`.

## Local verification one-liner (Python + Rust + security)

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo llvm-cov -p prin-kernels --features wgpu,cpu
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
```

## Snyk MCP scanning

The Snyk MCP server is authenticated for the repository's Snyk account. For
Python projects use the **absolute path** to the `.venv` Python in the
`command` argument and `all_projects=true` for the whole repo, or `all_projects=false`
with an explicit `file` for a single manifest:

```json
{
  "server_name": "snyk",
  "tool_name": "snyk_sca_scan",
  "arguments": {
    "path": "C:\\dev\\PRIN",
    "all_projects": true,
    "severity_threshold": "low",
    "command": "C:\\dev\\PRIN\\.venv\\Scripts\\python"
  }
}
```
