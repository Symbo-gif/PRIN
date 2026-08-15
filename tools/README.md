# tools/ — repository tooling

This directory contains maintenance and reproducibility command-line tools.
Tools must be deterministic, typed, non-interactive in CI, and must not import
or execute archived reference code.

## Current tools

- `wp001_baseline.py` statically validates project metadata, all 198 physical
  and uniquely numbered session briefs, the exact 43-module/657-symbol/172-
  export PRINet 3.0 ownership contract, and the `rust-toolchain.toml` profile
  (`rustfmt`/`clippy` required; `llvm-tools` optional for `cargo-llvm-cov`); it
  also emits deterministic repository inventory JSON and API traceability
  Markdown.
- `wp001_ownership.json` is the declarative module/symbol-to-future-WP ownership
  source consumed by the baseline validator.
- `reproduce.py` is the Phase 6 reproducibility-pipeline placeholder owned by
  WP-035.
- `wp005_ort_probe.py` runs the ONNX Runtime provider probe against
  `models/subconscious_controller.onnx` and writes the evidence to
  `EVIDENCE/0017-wp005-s1-ort-probe.json`.
- `wp005_phase0_gate.py` refreshes the ORT evidence (with `--refresh-ort`),
  validates the golden corpus, wheel matrix, and recorded spike decisions,
  and writes the consolidated gate report to
  `EVIDENCE/0017-wp005-s1-phase0-gate.json`.
- `math_audit_run.py` runs every claim ledger under `math_audit_claims/`
  through the external `math-audit-mcp` tool's `audit_claim_ledger`, using
  `math_audit_policy.yaml`, and writes a consolidated report to
  `EVIDENCE/math-audit/ema-run-summary.json`. See
  `DOCS/standards/Executive_Mathematical_Audit_Governance_and_Methodology.md`.
  Requires `MATH_AUDIT_MCP_HOME` set to the tool's repository root (defaults
  to the maintainer workstation path recorded in that governance doc).
- `math_audit_policy.yaml` is PRIN's strict-derived policy profile for
  `math-audit-mcp`.
- `math_audit_claims/*.json` are the committed claim ledgers: independent
  formal restatements of PRIN mathematical claims, audited (not authored) by
  `math-audit-mcp`.

Run the WP-001 validator from the repository root:

```bash
python tools/wp001_baseline.py check
python tools/wp001_baseline.py inventory
python tools/wp001_baseline.py traceability
```

- `check_deviation_ledger.py` validates the cumulative deviation-ledger
  tables in `DOCS/reports/NNN-project-state.md`. It checks that every commit
  hash resolves and that a finding's summary does not change between two
  consecutive reports without a new finding ID (Phase 2 analytics
  recommendation R17).

Run the Executive Mathematical Audit gate (requires `math-audit-mcp`
installed separately; see the governance doc):

```bash
MATH_AUDIT_MCP_HOME="C:\dev\--DEV\Math Audit MCP" python tools/math_audit_run.py
```

Run the deviation-ledger consistency check:

```bash
python tools/check_deviation_ledger.py DOCS/reports/016-project-state.md
python tools/check_deviation_ledger.py DOCS/reports/016-project-state.md DOCS/reports/017-project-state.md
```
