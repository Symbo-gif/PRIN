# DOCS/baselines/ — measured project baselines

This directory stores immutable, evidence-backed baseline artefacts produced by
governed work packages. Baselines describe observed repository state; they are
not audit verdicts, scientific results, or substitutes for Project State
Reports.

## WP-001 artefacts

- `wp001_repository_inventory.json` — deterministic active/archive repository
  inventory.
- `wp001_api_traceability.md` — complete PRINet 3.0 module and public-symbol
  ownership matrix.
- `wp001_baseline_report.md` — quality, security, CI, packaging, governance, and
  gap measurements.
- `wp001_s1_handoff.md` — S1 acceptance-to-evidence map and mandatory S2 handoff.

Regenerate machine-derived artefacts from the repository root:

```bash
python tools/wp001_baseline.py inventory > DOCS/baselines/wp001_repository_inventory.json
python tools/wp001_baseline.py traceability > DOCS/baselines/wp001_api_traceability.md
python tools/wp001_baseline.py check
```

`DOCS/baselines/` is excluded from its own active-file counts to prevent
self-referential inventory drift. Archived PRINet 3.0 files are measured
separately and are never imported or executed.
