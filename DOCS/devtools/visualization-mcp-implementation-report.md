# Implementation Report — Code-Intelligence Subsystem

**Subsystem:** `tools/code-intelligence/` · **Delivered at:** commit `6006b41`
(local, not pushed) · **This report's verification pass:** 2026-09-18,
UTC 05:30–05:56, against repository HEAD `6006b41` on `main`, working tree
clean, 5 commits ahead of `origin/main`.

**Purpose.** [`visualization-mcp-plan.md`](visualization-mcp-plan.md) §12–13
commits to running every governed gate and the real-repository acceptance
workflow with "exact commands and outputs recorded in the final report."
[`visualization-mcp-security.md`](visualization-mcp-security.md) references
"the implementation report" for exact scan commands and results. This is
that report. It records a full independent re-run of every gate — not a
restatement of the build session's claims — so any drift between what was
true when the subsystem was built and what is true now is caught and stated
plainly, per `CLAUDE.md`'s instruction to verify implementation facts from
the repository rather than invented or remembered evidence.

All commands below were run from the repository root, PowerShell-equivalent
paths (`.venv\Scripts\python.exe`), using the existing PRIN virtual
environment with `pip install -e ".[devtools]"` already applied (`mcp`
1.30.0, `networkx` 3.6.1, PyYAML 6.0.3, `pathspec` 1.1.1 present).

## 1. Subsystem test suite

```
.venv/Scripts/python.exe -m pytest tools/code-intelligence/tests -q
```

```
tools\code-intelligence\tests\test_analytics.py ...........              [ 18%]
tools\code-intelligence\tests\test_indexer.py ............               [ 37%]
tools\code-intelligence\tests\test_mcp_server.py .......                 [ 49%]
tools\code-intelligence\tests\test_mermaid.py .................          [ 77%]
tools\code-intelligence\tests\test_security.py .......                   [ 88%]
tools\code-intelligence\tests\test_telemetry.py .......                  [100%]
61 passed in 2.95s
```

## 2. Static analysis and type checking

```
.venv/Scripts/python.exe -m ruff check tools/code-intelligence          -> All checks passed!
.venv/Scripts/python.exe -m ruff format --check tools/code-intelligence -> 44 files already formatted
.venv/Scripts/python.exe -m mypy --strict tools/code-intelligence \
    --exclude tests/fixtures                                            -> Success: no issues found in 39 source files
```

Tool versions: ruff 0.16.1, mypy 2.3.0 (compiled).

## 3. Secure development gate (Coding Standards §6)

```
.venv/Scripts/python.exe -m bandit -r tools/code-intelligence \
    -x tools/code-intelligence/tests -q
```

- Total: **4 Low, 0 Medium+, 0 High** (bandit 1.9.4; 5,182 lines scanned).
- `B404`/`B603` (`ci_analytics/churn.py:58`): the one `subprocess.run` call
  in the subsystem — fixed absolute executable resolved via `shutil.which`,
  list-form args, `shell=False`, bounded timeout (`_GIT_TIMEOUT_SECONDS`).
  Matches Coding Standards §6.1's required subprocess pattern.
- `B101` ×2 (`ci_graph/store.py:144`, `ci_telemetry/instrument.py:75`):
  internal-invariant `assert` statements (SQLite `INSERT` always assigns a
  `lastrowid`; a precondition already checked by the caller). The root
  `pyproject.toml` ignores `S101` repo-wide for the same reason.
- Gate threshold ("0 Medium+") met.

```
snyk code test tools/code-intelligence
```

- **0 issues at any severity.** Snyk CLI 1.1306.2, org `symbo-gif`,
  authenticated (confirmed via a live scan, not `snyk whoami`).

Dependency scan (Snyk Open Source), run against the subsystem's actual
resolved dependency tree rather than a hand-typed guess: `uv pip compile
pyproject.toml --extra devtools` to resolve the `devtools` extra, then
`snyk test --file=requirements.txt --package-manager=pip --severity-threshold=low
--command=<path to the project's own .venv python>` so Snyk builds the graph
using the same interpreter/pip that actually has these packages installed:

```
Tested 54 dependencies for known issues, found 2 issues, 4 vulnerable paths.
Upgrade setuptools@78.1.0 to setuptools@83.0.0 to fix
  Improper Handling of Unicode Encoding [Medium] SNYK-PYTHON-SETUPTOOLS-17895075
  Directory Traversal [Medium] SNYK-PYTHON-SETUPTOOLS-9964606
```

Both findings are in `setuptools@78.1.0`, resolved as a transitive
dependency of `torch` (declared, unconditional, in `[project] dependencies`
**before** this subsystem was added) — not of `mcp`, `networkx`, `pyyaml`,
`pathspec`, or the `devtools-extra` packages. Confirmed by the resolved
requirements file's `# via torch` annotation. Per Coding Standards
§6.2/§6.4's remediation-attribution scope, this is not attributable to this
change; it is reported here as-is, not suppressed or ignored, and is not
something this isolated-tooling change can remediate without editing the
governed `torch` pin in root `[project] dependencies` — out of scope for a
"well-isolated, does not restructure existing PRIN functionality" addition.

```
.venv/Scripts/python.exe -m pip_audit --progress-spinner off
```

```
Found 16 known vulnerabilities in 2 packages
pip        25.2    PYSEC-2026-1795 / -1796 / -2875 / -2876 / -196 / -3721   (fix: 25.3-26.2)
setuptools 78.1.0  PYSEC-2025-49 / PYSEC-2026-3447                          (fix: 78.1.1 / 83.0.0)
Skipped (not on PyPI, cannot audit): prin, prinet, torch
```

**Correction to the previously published security doc:** the original
build-session record of this exact command (see
[`visualization-mcp-security.md`](visualization-mcp-security.md), now
corrected alongside this report) stated "no known vulnerabilities found."
Re-running the identical command today shows 16 findings across `pip` and
`setuptools` that were not present when the subsystem was built — new
`PYSEC` advisories have been published against `pip==25.2` and
`setuptools==78.1.0` in the interim (this environment's already-installed,
pre-existing versions; neither package is declared by the `devtools` or
`devtools-extra` extras). This is `pip-audit`'s live-database nature, not a
regression introduced by any change to this subsystem — no first-party or
devtools-extra dependency code changed between the two runs. Documented here
accurately rather than left as a stale "clean" claim, per `CLAUDE.md`'s
prohibition on unverifiable or outdated safety claims. Not attributable to
this change and not remediable from within an isolated-tooling PR (`pip`
itself is bootstrap tooling outside `pyproject.toml`; `setuptools` is the
same pre-existing `torch`-transitive dependency Snyk flagged above).

```
cargo audit
```

Not applicable — this change touches no Rust source or `Cargo.lock` entry.

## 4. Governed repository invariant

```
.venv/Scripts/python.exe tools/wp001_baseline.py check
```

```
WP-001 baseline validation passed.
```

## 5. Root suite regression check (no interference with the governed surface)

```
.venv/Scripts/python.exe -m pytest tests/ -m "not slow and not gpu" -q
```

```
2909 passed, 178 skipped, 38 deselected, 56 warnings in 299.53s (0:04:59)
```

Identical pass/skip/deselect counts to the build session's record. The
`devtools`/`devtools-extra` extras and `tools/code-intelligence/` package
are not imported by anything under `tests/` (`testpaths = ["tests"]`
excludes `tools/code-intelligence/tests`), so this confirms no interference
with the governed test surface.

## 6. Real-repository acceptance workflow

Fresh full re-index against current HEAD (`6006b41`, 5 commits ahead of
`origin/main` at scan time):

```
.venv/Scripts/python.exe tools/code-intelligence/cli.py index --force
```

```
files_scanned: 2568, files_indexed: 2568, files_failed: 0, files_skipped: 0
node_count: 67858, edge_count: 76736
```

Identical to the build session's figures — confirms deterministic,
reproducible indexing of the real repository.

**Hotspots** (`hotspots --metric pagerank --limit 10`): top results include
`OscillatoryAttention` (both the `python/prin/nn/attention.py` and the
mirrored `crates/prin-train/src/attention.rs` symbol, identical PageRank
score) and `prin_dynamics` — genuinely central symbols, consistent with the
build session's finding after the call-site-frequency guard against
generic-name flooding (`len`, `get`, `to`).

**Cycles** (`cycles`): `cycle_count: 2` — a 34-node file-level cycle rooted
at `python/prin/__init__.py` (`_compat.py`, `_torch_compat.py`, `daemon.py`,
…) and the previously documented 3-node symbol cycle in
`reporting/_artifacts.py`. Matches the build session's finding exactly.

**Diagram generation** (`diagram repo_overview --max-nodes 20`): produced a
deterministic, sorted, bounded Mermaid flowchart, correctly reported
`truncated: true` with a `"node limit reached"` note, and wrote to
`tools/code-intelligence/output/` (gitignored).

**MCP server** (`serve-mcp`, stdio `initialize` handshake): server
responded with `protocolVersion: "2024-11-05"`, `serverInfo.name:
"prin-code-intelligence"`, and an `instructions` string confirming the
read-only/path-containment contract — verified programmatically via a raw
JSON-RPC `initialize` request over the subprocess's stdio pipes, not just a
startup-without-crash check.

**Tool count:** `grep -c "@mcp.tool" ci_mcp_server/server.py` → **16**,
matching every doc's stated count.

## 7. Summary verdict

Every gate committed to in the plan (§12–13) has now been independently
re-run against the delivered commit and produces the same pass/fail/finding
profile as the build session, with one accurate correction: `pip-audit`'s
live vulnerability database has moved since the subsystem was built, and now
reports pre-existing, not-attributable findings in `pip`/`setuptools` that
were not present before. No first-party code in `tools/code-intelligence/`
changed as a result of this verification pass — all findings from §3 remain
open only in the "not attributable, documented, not suppressed" sense the
plan and security doc already establish for the `setuptools`/`torch` path.
Root suite, WP-001 baseline, and the real-repository acceptance workflow are
all unaffected and reproducible.

No code changes were required by this verification pass. Documentation
corrections applied: [`visualization-mcp-security.md`](visualization-mcp-security.md)'s
`pip-audit` line updated from "no known vulnerabilities found" to point at
this report's current, accurate result.
