# `analysis/` — EXP-002 committed E4 analysis code

| File | Role |
|---|---|
| [`exp002_e4_analysis.py`](exp002_e4_analysis.py) | The registered E4 analysis for EXP-002. It reads the five indexed E3 run records, verifies provenance and input-byte identity before reading any observation, re-derives the pre-registration §4.1 decisions, and writes the seven §8.1 outputs plus `../report-manifest.json` deterministically. |

It was committed (`3731fc2`) and pushed before its first run on a real record (campaign plan §7.4
item 2; pre-registration §8). Its tests are
[`tests/test_exp002_e4_analysis.py`](../../../../tests/test_exp002_e4_analysis.py) (synthetic fixtures
only). DV-040 option (a) puts this directory under `ruff check`, source-only `ruff format --check`,
`mypy --strict` and `bandit`, locally and in `python.yml`'s lint job.

It uses the standard library only. It never imports `prin`, `prinet`, the E3 driver or
`tools.reproduce`, and never reads the retained publication roots (E5 verifies those bytes).

## How to run it

From the repository root of a checkout that holds the five run directories and the frozen inputs:

```powershell
.venv\Scripts\python.exe -I "DOCS\experiments\EXP-002-api-benchmark-result-and-reproduction-parity\analysis\exp002_e4_analysis.py"
```

It prints the verdicts and the SHA-256 of every file it writes. It exits `0` when the analysis
completed, whatever the verdicts, and `1` when a global precondition failed, in which case nothing is
written. The outputs go to `DOCS/test_and_benchmark_results/EXP-002/analysis/` (gitignored) and
`report-manifest.json` in the record root. A second run reproduces every byte. The record of the
session-0162 run is [`../analysis.md`](../analysis.md).
