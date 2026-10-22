# EXP-002-r1 E4 Analysis Execution Log

Pre-registration freeze: **`10ac3c04f44a1f68869c94c1dfae1c1c1a189460`** - git SHA of the approved protocol (`preregistration.md`).
Protocol SHA-256: `903d65bcae7287042a3ebf6498ffaa9f45d13a697666249bdf5fe5bbaaa84e72`.
Execution source commit `R`: `e65076eb7ae97100d40ea32c60229dd40ed51033` (clean E3 execution commit).
Analysis execution HEAD SHA: `c7c54d186ffb912070498f78e9931ebd4ff8f8e7`.
Session: `EXP-002-r1-E4`.
Date: 2026-10-21 / 2026-10-22 UTC.
Host: Windows 11 Home x86_64 (`Windows-11-10.0.26300-SP0`), AMD Ryzen 7 8700F, Python 3.14.0.
Operator: MichaelMaillet.
AI Pair: Antigravity.

---

## 1. Baseline Verification & Pre-Flight

```powershell
# 1.1 Verify git HEAD and clean working tree
git rev-parse HEAD
# Output: c7c54d186ffb912070498f78e9931ebd4ff8f8e7

# 1.2 Verify predecessor immutability
git diff HEAD -- "DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/" "benchmarks/results/EXP-002/" "DOCS/test_and_benchmark_results/EXP-002/" "EVIDENCE/0159/" "EVIDENCE/0160/" "EVIDENCE/0161/" "EVIDENCE/0162/" "EVIDENCE/0163/" "EVIDENCE/exp002-d1-s1/" "EVIDENCE/exp002-d1-s2/" "EVIDENCE/exp002-d1-s3/" "EVIDENCE/exp002-d1-s4/"
# Exit code: 0, Output: (empty - 0 bytes)

# 1.3 Verify all 5 E3 run directories
# RUN-20261021T183011Z-e65076e-r1-api-cpu (api) - manifest verified, status COMPLETED, abort.json absent
# RUN-20261021T183952Z-e65076e-r1-conclusions-cpu (conclusions) - manifest verified, status COMPLETED, abort.json absent
# RUN-20261021T184447Z-e65076e-r1-reproduction-reference-cpu (reference) - manifest verified, status COMPLETED, abort.json absent
# RUN-20261021T184600Z-e65076e-r1-reproduction-prin-cpu (prin) - manifest verified, status COMPLETED, abort.json absent
# RUN-20261021T184707Z-e65076e-r1-seedrep0-prin-cpu (repeatability) - manifest verified, status COMPLETED, abort.json absent
```

---

## 2. Analysis Unit Test Suite Execution

```powershell
.venv\Scripts\python -m pytest tests/test_exp002_r1_e4_analysis.py --basetemp=.pytest_basetemp -o faulthandler_timeout=300
```

Console Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.1.1, pluggy-1.6.0 -- C:\dev\PRIN\.venv\Scripts\python.exe
cachedir: .pytest_cache
hypothesis profile 'default'
benchmark: 5.2.3
rootdir: C:\dev\PRIN
configfile: pyproject.toml
plugins: anyio-4.15.1, hypothesis-6.165.2, benchmark-5.2.3, cov-7.1.0
collecting ... collected 176 items

tests/test_exp002_r1_e4_analysis.py .................................... [ 20%]
........................................................................ [ 61%]
....................................................................     [100%]

====================== 176 passed in 3441.14s (0:57:21) =======================
Exit Code: 0
```

---

## 3. Real E3 Data Analysis Execution

```powershell
.venv\Scripts\python DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/analysis/exp002_r1_e4_analysis.py
```

Console Output:
```text
H1: CONFIRMED
H2: CONFIRMED
H3: CONFIRMED
H4: CONFIRMED
H3_sensitivity_policy: REFUTED
D1 flag: False
DOCS/test_and_benchmark_results/EXP-002-r1/analysis/summary.json fcdb56250165f18d65c22d07f9caae1a9e0ff632f3dbcab0047046dabc9e01ad
DOCS/test_and_benchmark_results/EXP-002-r1/analysis/api-mapping.csv 5656cb9b570889a911b35283b8a5cfdc55c5ec8e0f28ba35d34d8fec526e10c3
DOCS/test_and_benchmark_results/EXP-002-r1/analysis/conclusion-comparisons.csv 0c01c59c8e1f32ea3ad173dddde117ad9a94b187289328da760e1c906e0bba85
DOCS/test_and_benchmark_results/EXP-002-r1/analysis/reproduction-comparisons.csv 925b40b4b13f6e76ec62eed08f65b400d13da66c446f54766963804781f5e532
DOCS/test_and_benchmark_results/EXP-002-r1/analysis/error-distributions.json afd3d1454dabdd12e12b504300b07996a12553cc262a16f6748c38d7a3fffb1e
DOCS/test_and_benchmark_results/EXP-002-r1/analysis/expected-vs-observed.md 1a27f264f02cd7e2bea0f1d6649ded3f797982d288b4ac870d358accd26bd4d7
DOCS/test_and_benchmark_results/EXP-002-r1/analysis/coverage-and-deferrals.md 4e82524ff0fa8b20cc2dbc2a13b5202730b4d5d6c01a0e107ec100574fb74dad
DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/report-manifest.json 6cd12f2d1bf0ed5f841d8e3945443a4fd16b689f7fd489f0435fd61baf8d9dc2
DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/analysis/api-census.csv 5656cb9b570889a911b35283b8a5cfdc55c5ec8e0f28ba35d34d8fec526e10c3
DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/analysis/conclusions-census.csv 0c01c59c8e1f32ea3ad173dddde117ad9a94b187289328da760e1c906e0bba85
DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/analysis/reproduction-comparisons.csv 925b40b4b13f6e76ec62eed08f65b400d13da66c446f54766963804781f5e532
DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/analysis/repeatability-comparisons.csv 18f91d6bf46bc0006225ab2d78ceaa058362466faaea63de753ff50035653027
DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/analysis/summary.json fcdb56250165f18d65c22d07f9caae1a9e0ff632f3dbcab0047046dabc9e01ad
DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/analysis/sensitivity-residuals.json 884c0c6ce0344e8e4757c99e5555e24ddb314be62a89f8619ed9108644a4de06
DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/analysis/report-manifest.json 6cd12f2d1bf0ed5f841d8e3945443a4fd16b689f7fd489f0435fd61baf8d9dc2
Exit Code: 0
```

---

## 4. Local Quality Gates (DV-040 Compliance)

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/
# Exit code: 0, Output: All checks passed!

.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
# Exit code: 0, Output: 336 files already formatted

.venv\Scripts\ruff format --check DOCS/experiments/ --config "include = ['*.py', '*.pyi', '*.ipynb']"
# Exit code: 0, Output: 4 files already formatted

.venv\Scripts\mypy DOCS/experiments/ --strict
# Exit code: 0, Output: Success: no issues found in 4 source files

.venv\Scripts\python -m bandit -r python/prin DOCS/experiments -c pyproject.toml
# Exit code: 0, Output: No issues identified. Total issues: 0
```

---

## 5. Evidence Bundle Integrity Self-Check

```powershell
.venv\Scripts\python EVIDENCE/exp002-d1-s3/index_selfcheck.py exp002-r1-e4
# Exit code: 0
```
