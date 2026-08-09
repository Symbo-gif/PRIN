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

Run the WP-001 validator from the repository root:

```bash
python tools/wp001_baseline.py check
python tools/wp001_baseline.py inventory
python tools/wp001_baseline.py traceability
```
