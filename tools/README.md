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
- `wp029_control_buffer_pilot.py` measures the archived PRINet 3.0
  `ControlSignalBuffer`'s read latency under contention, for the WP-029
  daemon-latency pilot (`EVIDENCE/0113-wp029-s1-control-buffer-pilot.json`).
- `wp030_mot_fixture.py` replays fixed oid/hid/distance sequences through the
  real `motmetrics` package (`mot` extra) and writes
  `crates/prin-daemon/tests/data/mot_reference_cases.json`, the golden
  fixture `crates/prin-daemon/tests/parity_mot.rs` validates
  `prin_daemon::mot::MotAccumulator` against.
- `wp031_stats_fixture.py` calls real `scipy.stats.ttest_ind` (1.18.0,
  `equal_var=False`) to generate
  `crates/prin-train/tests/data/welch_t_test_reference_cases.json`, the
  golden fixture `crates/prin-train/tests/parity_stats.rs` validates
  `prin_train::stats::welch_t_test` against (8 scenarios, `rtol=1e-9,
  atol=1e-12`). Calls only scipy — never implements any numerical algorithm
  (per `tools/` policy).

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
- `check_dv_register_gates.py` parses `DEFERRED_VALIDATION_REGISTER.md` for
  items whose text names an explicit "before session NNNN"/"before WP-0NN
  S1" precondition, cross-references `SESSION_REGISTER.md` for that
  session's status, and fails if the named session is `COMPLETE` while the
  item is not `CLOSED`/`SATISFIED` (Phase 5 analytics recommendation R34,
  EA-006 finding E-F2 remediation — mechanizes the check that would have
  caught R28's DV-019 precondition going unenforced through all of Phase 5).

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

Run the DV-register gate-enforcement check (no arguments needed):

```bash
python tools/check_dv_register_gates.py
```
