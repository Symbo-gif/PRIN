# `analysis/` — EXP-001-r1 committed E4 analysis code

## What is here

| File | Role |
|---|---|
| [`exp001_r1_e4_analysis.py`](exp001_r1_e4_analysis.py) | The registered E4 analysis and renderer for EXP-001-r1. Reads the six indexed E3 run artefacts, applies the frozen pre-registration §8 decision rule, and regenerates every E4 output deterministically. |

Its tests live in
[`tests/test_exp001_r1_e4_analysis.py`](../../../../tests/test_exp001_r1_e4_analysis.py),
not here — DV-040 records that a module under a campaign record root sits
outside CI's lint/type/SAST paths, so the compensating control is that its
behaviour is CI-enforced from the `tests/` tree.

## Why this directory exists

Campaign plan §7.4 item 2 requires each experiment's analysis code to be
committed under the experiment's record root (or `python/prin/reporting/`)
**before** E4 adjudicates, and Experimentation Standards §2 E4 requires that
figures and tables regenerate deterministically from stored artefacts. This
directory is that committed code for EXP-001-r1.

The predecessor's
[`EXP-001/analysis/exp001_e4_analysis.py`](../../EXP-001-golden-trajectory-numerical-parity/analysis/exp001_e4_analysis.py)
is **not** reused, imported or retargeted: it is pinned to the original four
`RUN-…-6b9d6b6-*` runs and to EXP-001's own identity, and the frozen
pre-registration §8 forbids it as a source of r1 verdicts. EXP-001's record and
verdicts stay immutable.

## How to use it

From the repository root of the checkout that holds the six r1 run
directories:

```powershell
.venv\Scripts\python.exe "DOCS\experiments\EXP-001-r1-golden-trajectory-numerical-parity\analysis\exp001_r1_e4_analysis.py"
```

It writes `summary.json`, `summary.md`, `case-comparisons.json` and
`error-distributions.json` under the gitignored
`DOCS/test_and_benchmark_results/EXP-001-r1/`, and `report-manifest.json`
(the SHA-256 manifest of those outputs) into the record root. It prints one
line per hypothesis plus the campaign plan §10.4 D1 flag, and always exits 0:
a refutation is a scientific result, not a tool error. An inadmissible input
raises `AnalysisError` instead — the analysis aborts rather than inferring a
result from a partial or mixed experiment.

`--output-dir`, `--manifest-path` and `--generated-at` exist for the
regeneration check and for tests. Passing `--generated-at` anything other than
the registered default changes every output digest and is **not** a
regeneration. The input root is deliberately not a command-line option: the
analysis is bound to its own checkout, which is what campaign plan §7.4 step 5
wants.

## Status

**Committed before adjudication**, as §7.4 item 2 requires. Local gate at
commit time: `ruff check` and `ruff format --check` clean, `mypy --strict`
clean, `interrogate` 100 %, `bandit` 0 issues, `snyk code test
--severity-threshold=medium` 0 issues, and
`pytest tests/test_exp001_r1_e4_analysis.py` green. The verdicts this module
produces, and the evidence for them, are recorded in
[`../analysis.md`](../analysis.md).
