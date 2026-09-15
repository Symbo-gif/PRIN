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

Do not run pytest concurrently with cargo (or two pytest invocations
back-to-back) on Windows: antivirus/file-handle contention during `tmp_path`
cleanup can surface as `PermissionError: [WinError 32]` fixture-setup errors.
Run the suites sequentially; if lock errors appear, re-run the suite in
isolation (EA-002 E-F13).

## Local verification one-liner (Python + Rust + security)

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo llvm-cov -p prin-kernels --features wgpu,cpu
cargo llvm-cov -p prin-dynamics
cargo llvm-cov -p prin-dynamics --features strict-checks
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
Remove-Item -Recurse -Force DOCS/sphinx/_build -ErrorAction SilentlyContinue
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
```

**Clean-build discipline (Phase 4 analytics R30/PA4-F2):** Sphinx's
incremental build tracks only `.rst`/`.md` source-file timestamps — it does
not detect that an `automodule`-sourced Python docstring changed underneath
an unmodified `.rst` page, so a reused, gitignored `DOCS/sphinx/_build/html`
directory can silently mask a genuine `autodoc`-sourced warning for an
arbitrary number of subsequent sessions. Always delete
`DOCS/sphinx/_build` (or build to a freshly created output directory)
immediately before running the build command above; never report a Sphinx
"0 warnings" result from a reused output directory.

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
