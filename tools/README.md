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

Run the WP-001 validator from the repository root:

```bash
python tools/wp001_baseline.py check
python tools/wp001_baseline.py inventory
python tools/wp001_baseline.py traceability
```
