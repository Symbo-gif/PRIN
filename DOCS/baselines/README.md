# DOCS/baselines/ — measured project baselines

This directory stores immutable, evidence-backed baseline artefacts produced by
governed work packages. Baselines describe observed repository state; they are
not audit verdicts, scientific results, or substitutes for Project State
Reports.

## WP-001 artefacts

- `wp001_repository_inventory.json` — deterministic active/archive repository
  inventory.
- `wp001_api_traceability.md` — complete ownership matrix for 43 PRINet 3.0
  modules, 657 module-symbol rows, and 172 canonical top-level exports.
- `wp001_baseline_report.md` — quality, security, CI, packaging, governance, and
  gap measurements.
- `wp001_s1_handoff.md` — S1 acceptance-to-evidence map and mandatory S2 handoff.

Validate the current repository and render comparison artefacts from its root:

```bash
python tools/wp001_baseline.py check
python tools/wp001_baseline.py inventory > <temporary-inventory.json>
python tools/wp001_baseline.py traceability > <temporary-traceability.md>
```

The committed WP-001 files preserve the S1 measurement point and are not
regenerated during later sessions. Compare temporary output rather than
rewriting baseline history.

## WP-033 artefacts

- `wp033_benchmark_traceability.md` — maps every verified legacy PRINet 3.0
  benchmark script (58, not the session brief's quoted 62 — see the file's
  own "Verified script count" section) to its `benchrunner` topic category
  and new module.

`DOCS/baselines/` is excluded from its own active-file counts to prevent
self-referential inventory drift. Archived PRINet 3.0 files are measured
separately and are never imported or executed.
