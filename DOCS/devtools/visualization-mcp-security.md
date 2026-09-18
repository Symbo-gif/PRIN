# Security Model and Trust Boundaries — Code-Intelligence Subsystem

## Threat model summary

This subsystem reads source files in `C:\dev\PRIN` and answers structured
queries about them, locally, to a local MCP client. It has no network
listener, no hosted service, no credential store of its own, and no write
access to anything outside two gitignored directories it owns.

## What it can do

- Read files under the repository root (and any explicit
  `extra_allowed_roots`, none configured by default) to build a graph.
- Write to `tools\code-intelligence\.data\` (the SQLite graph database and
  optional JSONL telemetry) and `tools\code-intelligence\output\` (Mermaid
  diagrams).
- Answer read-only structured queries over that graph via the CLI or the
  MCP server.
- Optionally run `git log` (read-only, bounded commit count) for the
  `churn` hotspot metric.

## What it cannot do (by design)

- **No write, shell, deployment, destructive, credential, or arbitrary
  filesystem MCP tool is exposed.** `tests/test_mcp_server.py::test_no_tool_exposes_an_arbitrary_filesystem_path_parameter`
  asserts no tool schema accepts a `file_path`/`path`/`cwd`/`command`/`shell`
  parameter.
- **`index_repository` cannot write outside its own database.** It calls
  `ci_indexer.orchestrator.run_index`, which only ever calls
  `Path.read_bytes()` on discovered files and writes exclusively through
  `GraphStore` to the configured `db_path`.
- **No tool returns raw file contents.** Node/edge responses carry
  location metadata (path, line numbers) and a small `evidence` string
  captured once at index time (e.g. a matched import line) — never a file
  read on demand.
- **No secret material ever enters the graph.** Any file whose *name*
  matches a secret-like pattern (`.env`, `.env.*`, `*.pem`, `*.key`,
  `*.p12`, `*.pfx`, `id_rsa*`, `id_ed25519*`, `*.jks`, `*credentials*`,
  `*secret*`, `*.gpg`) is represented only as a structural node
  (`attributes.secret_like: true`) — its content is never opened for
  parsing. This is enforced in `ci_indexer/orchestrator.py` before any
  adapter runs, not as an afterthought filter on output.
- **Defense in depth on evidence.** Even though evidence is captured only
  from non-secret files, `ci_mcp_server/security.py::redact_evidence`
  re-checks every evidence string against the same secret-like patterns
  before an MCP response is returned, and redacts if matched.
- **No network calls.** The MCP server is STDIO-only. The optional
  OpenTelemetry bridge (`ci_telemetry/otel_bridge.py`) never configures its
  own exporter or endpoint — it only republishes onto a `TracerProvider`
  the *host environment* already configured (a no-op tracer if none was
  configured), so importing it cannot cause a network call on its own.
- **No hosted/paid dependency.** SQLite, local JSONL, and STDIO are the
  only storage/transport mechanisms.

## Path containment

`ci_mcp_server/security.py::ensure_contained(candidate, allowed_roots)`
resolves a candidate path and raises `PathEscapeError` unless it is
contained within one of the allowed roots (default: the repository root
only). This is exercised even though no current tool accepts a raw path
argument, so any future tool addition inherits the same containment check
by construction rather than by convention. `tests/test_security.py` covers
direct paths, `..`-traversal attempts, and multi-root configurations.

## Secrets and credentials

- No credentials are read, stored, or required by this subsystem.
- `SNYK_TOKEN`/other CI secrets are never referenced by any file here.
- GitHub secret scanning and push protection remain independent,
  repository-level controls (Coding Standards §6.2) — this subsystem does
  not replace, weaken, or interact with them.

## Dependencies and supply chain

New dependencies are declared in the root `pyproject.toml` under two new,
optional extras (Coding Standards §6.3: added via `pyproject.toml` only,
with justification):

- `devtools`: `mcp`, `networkx`, `pyyaml`, `pathspec` — required for the
  subsystem to function.
- `devtools-extra`: `tree-sitter`, `opentelemetry-api`,
  `opentelemetry-sdk` — optional accelerators; the subsystem functions
  fully without them.

Scans run against this change (exact commands and results in the
implementation report):

- **Snyk Code** (`snyk code test tools/code-intelligence`): 0 issues at any
  severity.
- **Snyk Open Source** (resolved `devtools` extra via
  `uv pip compile pyproject.toml --extra devtools`, then
  `snyk test --file=... --package-manager=pip --severity-threshold=low`,
  matching this repository's own CI invocation pattern): 2 Medium findings,
  both in `setuptools@78.1.0`/paths through it — confirmed (via the
  resolved requirements file's `# via` annotation) to originate from the
  pre-existing, unconditional `torch>=2.0` dependency declared in
  `[project] dependencies` **before** this change, not from `mcp`,
  `networkx`, `pyyaml`, or `pathspec`. Not attributable to this change per
  Coding Standards §6.2/§6.4's remediation-attribution scope; not
  suppressed or ignored — reported here as-is.
- **`pip-audit .`** (the exact invocation `.github/workflows/python.yml`
  uses): no known vulnerabilities found.
- **`bandit -r tools/code-intelligence`**: 4 Low-severity findings, 0
  Medium+ (the repository's own gate threshold is "0 medium+ findings").
  All four are expected, reviewed patterns: `B404`/`B603` for the one
  `subprocess.run` call in `ci_analytics/churn.py` (fixed absolute
  executable resolved via `shutil.which`, argument list, no `shell=True`,
  bounded timeout — exactly Coding Standards §6.1's required subprocess
  pattern), and `B101` for two internal-invariant `assert` statements
  (SQLite `INSERT` always assigns a `lastrowid`; a precondition already
  checked by the caller) — the root repository's own `pyproject.toml`
  ignores `S101`/`assert` repo-wide for the same reason.
- **`cargo audit`**: not applicable — this change touches no Rust code or
  `Cargo.lock` entry.

## What to review before trusting a result

Every MCP tool response distinguishes:

- `provenance` per edge (`exact_parser` vs. heuristic) — see the
  architecture doc's confidence table.
- `evidence_kind: "static_centrality"` vs. `"runtime_evidence"` on hotspot
  results.
- Explicit `heuristic: true` on every dead-code candidate.
- A `known_limitation` field where a tool's coverage is intentionally
  partial (e.g. `list_proof_solver_benchmark_links`).

Treat any claim without one of these markers as worth double-checking
against `explain_graph_evidence`, which shows the exact stored evidence for
a node or edge.
