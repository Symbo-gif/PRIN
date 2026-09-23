# tools/ — repository tooling

This directory contains maintenance and reproducibility command-line tools.
Tools must be deterministic, typed, non-interactive in CI, and must not import
or execute archived reference code.

## Tool Categories

### Validation & Baselines
- `wp001_baseline.py` — statically validates project metadata, session briefs,
  the 43-module/657-symbol PRINet 3.0 ownership contract, and the
  `rust-toolchain.toml` profile; emits repository inventory JSON and API
  traceability Markdown.
- `wp001_ownership.json` — declarative module/symbol-to-WP ownership source.
- `check_deviation_ledger.py` — validates cumulative deviation-ledger tables
  in Project State Reports.
- `check_dv_register_gates.py` — fails when any DV register item's
  precondition session is COMPLETE while the item is not CLOSED.
- `check_global_session_registration.py` — cross-references every Executive
  Audit report against its session-register row.
- `check_bench_regression.py` — fail-closed comparison of fresh same-job
  Criterion and pytest-benchmark reference/candidate measurements; all
  identities must match and every mean must be finite and positive. More than
  10% mean slowdown fails; missing data never seeds a pass. Each arm may
  have several runs (`--reference`/`--candidate RUN...`, averaged; the
  nightly uses counterbalanced ABBA order). `--advisory PREFIX` ids are
  reported but not gating; a blank or unmatched prefix, or a prefix set that
  leaves no gated benchmark, is an input error.

### Reproducibility
- `reproduce.py` — Phase 6 reproducibility pipeline (WP-035). Regenerates all
  14 figures and 11 LaTeX tables from stored JSON artefacts with SHA-256
  manifest verification.

  ```bash
  python tools/reproduce.py --verify-manifest          # full pipeline + manifest check
  python tools/reproduce.py --figures-only             # skip tables
  python tools/reproduce.py --tables-only              # skip figures
  python tools/reproduce.py --append-manifest          # add new artefacts after verifying existing
  ```

### ONNX Runtime & Phase Gates
- `wp005_ort_probe.py` — runs the ONNX Runtime provider probe against the
  subconscious controller model.
- `wp005_phase0_gate.py` — refreshes ORT evidence, validates golden corpus,
  wheel matrix, and spike decisions; writes consolidated gate report.

### Mathematical Audit
- `math_audit_run.py` — runs every claim ledger through `math-audit-mcp`.
- `math_audit_policy.yaml` — strict-derived policy profile for `math-audit-mcp`.
- `math_audit_claims/*.json` — committed claim ledgers (audited, not authored).

### Pilot & Fixture Generation
- `wp029_control_buffer_pilot.py` — measures archived `ControlSignalBuffer`
  read latency under contention.
- `wp030_mot_fixture.py` — generates golden MOT fixture for
  `prin_daemon::mot::MotAccumulator` parity tests.
- `wp031_stats_fixture.py` — generates golden Welch t-test fixture for
  `prin_train::stats::welch_t_test` parity tests.

### Controller Graph (WP-036F)
- `wp036f_reexport_controller.py` — rewrites the ONNX controller graph so
  every `Gemm` node carries an explicit zero bias (required by
  `DmlExecutionProvider`). Idempotent; `--check` verifies drift.
- `wp036f_provider_latency.py` — records DV-006 provider/latency evidence.

### Code Intelligence (optional add-on)
- `code-intelligence/` — self-contained local codebase visualization and
  runtime-observability subsystem: SQLite code knowledge graph, graph
  analytics, bounded Mermaid diagrams, a read-only local MCP server (16
  tools), and opt-in JSONL runtime telemetry. Not part of the Session Cycle.
  See [`code-intelligence/README.md`](code-intelligence/README.md) and
  [`DOCS/devtools/visualization-mcp.md`](../DOCS/devtools/visualization-mcp.md).

  ```powershell
  python -m pip install -e ".[devtools]"
  python tools\code-intelligence\cli.py verify-installation
  python tools\code-intelligence\cli.py index
  python tools\code-intelligence\cli.py serve-mcp
  ```

## Quick Reference

Run the WP-001 validator from the repository root:

```bash
python tools/wp001_baseline.py check
python tools/wp001_baseline.py inventory
python tools/wp001_baseline.py traceability
```

Run the deviation-ledger consistency check:

```bash
python tools/check_deviation_ledger.py DOCS/reports/016-project-state.md
python tools/check_deviation_ledger.py DOCS/reports/016-project-state.md DOCS/reports/017-project-state.md
```

Run the DV-register gate-enforcement check (no arguments needed):

```bash
python tools/check_dv_register_gates.py
```

Run the Executive Mathematical Audit gate (requires `math-audit-mcp`
installed separately; see the governance doc):

```bash
MATH_AUDIT_MCP_HOME="C:\dev\--DEV\Math Audit MCP" python tools/math_audit_run.py
```
