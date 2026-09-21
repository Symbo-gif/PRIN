# benchmarks/results/ (canonical benchmark artefacts)

Canonical, tracked output directory for `benchrunner` results (Benchmarking
and Reproducibility Standards §3: "Canonical benchmark results:
`benchmarks/results/` (tracked)."). `python -m benchmarks.benchrunner
--category <cat> --out benchmarks/results/` writes here by default.

WP-033 S1 built the `benchrunner` machinery and the nine category modules and
validated them with small, fast, characterization-scale parameters (Non-goal:
drawing conclusions from final measurements). Production-scale results are
produced only by the Phase 7 campaign.

## Phase 7 campaign layout (session 0153, `DOCS/experiments/campaign-plan.md` §7)

```
benchmarks/results/
├── EXP-001/ … EXP-008/            # one raw-artefact root per experiment
│   ├── README.md                  # the run-directory rule for that experiment
│   └── RUN-<UTC>-<SHA>-<label>/   # one directory per execution, never reused
│       ├── <category>_<name>.json # write_result envelope + campaign payload fields
│       └── manifest.json          # per-run SHA-256 manifest (tools/reproduce.py)
└── y4q1_9_preregistration_hash.json
```

Rules: pass a **new** `RUN-…` directory to `--out` for every execution (re-runs
and corrections get a new run ID — raw artefacts are append-only,
Experimentation Standards §4); close each run with
`tools.reproduce.append_manifest`/`verify_manifest` on that directory;
`write_result` itself has no overwrite guard (DV-038), so the run-directory
rule is the control until that row closes. Tracked size cap 2 MiB per run,
64 MiB campaign-wide.

Generated reports/figures derived from these artefacts go to
`DOCS/test_and_benchmark_results/` (gitignored), not here.
