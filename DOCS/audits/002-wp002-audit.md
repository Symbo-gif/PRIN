# PRIN Audit Report — Cycle 002 / WP-002

**Date:** 2026-08-06
**Auditor:** Devin (AI pair)
**Scope:** WP-002 "Golden corpus and differential harness" — `python/prin/parity/`, `parity/`, `tests/test_parity_*.py`, `.github/workflows/parity.yml`, `pyproject.toml`, `.gitattributes`
**Sessions:** 0005 S1 implementation; 0006 S2 this audit
**Active brief:** `DOCS/sessions/phase-0/0006-wp002-s2-golden-corpus-and-differential-harness.md`
**Git state:** `feat/wp001-foundation-baseline` @ `0908b461594c64920b4b51e64ad0aa93f15c3d24`
**Pre-S1 baseline:** `ec4cc2b` (WP-001 S4 closure)
**Implementation commit:** `0908b46` — "feat(WP-002 S1): golden corpus and differential harness against PRINet 3.0.0"
**Verdict:** **PASS-WITH-FINDINGS**
**Maintainer acknowledgment:** pending

---

## 1. Executive summary

WP-002 delivered the versioned PRINet 3.0.0 golden-trajectory corpus, schema/manifest validators, corpus loader, differential pytest harness, and hypothesis strategies. The implementation is in scope: it does not introduce PRIN numerical kernels or modify archived reference outputs. The 504-case corpus covers every declared model × coupling mode × basic integrator, the SHA-256 manifest and immutable metadata are present, and the differential harness independently reproduces and detects planted deviations at the documented tolerances.

The audit found four deviations: two D2 standard-gate findings and two D4 hygiene findings. No D1 trajectory breach was found. The S1 handoff overclaimed the coverage gate for the fast test suite, and Snyk Open Source reports unaddressed transitive advisories in the documentation build requirements. Both must be cleared in S3.

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | PASS | Adds only the declared parity/corpus/harness artefacts; no PRIN numerics or archived-output changes |
| Plan/architecture conformance (A2) | PASS | `prin.parity` is a comparison/test package; `parity/generate_corpus.py` uses archived PRINet 3.0.0 to generate cases |
| Tests in tandem + coverage (A3) | ⚠️ | Tests committed with code; full suite reaches 95% on `prin.parity`, but the fast `tests/` suite is 94.5% (`WP002-F1`) |
| Numerical parity + invariants (A4) | PASS | 504 cases, all 14 model×coupling×integrator combos; parity tests pass; planted deviations fail |
| Quality gates (A5) | PASS | ruff, ruff format, mypy strict, cargo fmt/clippy/test/rustdoc all clean |
| Security (A6) | ⚠️ | bandit, cargo audit, pip-audit (project + docs req) clean; Snyk Code 0; Snyk Open Source reports 12 findings in `DOCS/sphinx/requirements.txt` (`WP002-F2`) |
| Docstring/doc coverage (A7) | ⚠️ | interrogate 100%; public `prin.parity` API fully documented; parent `__init__.py` and `parity/README.md` are stale (`WP002-F3`) |
| Repository hygiene (A8) | ⚠️ | `__all__` consistent, `.gitattributes` updated; `bandit -r parity/` flags a test assert and `pyproject.toml` does not exclude `parity/` (`WP002-F4`) |
| CI status (A9) | ⚠️ | `python.yml` fast/lint jobs pass; the security job is expected to fail at the Snyk docs-dependency step (`WP002-F2`) unless remediated before merge |
| Artefact trail (A10) | PASS | S1 handoff note, `EVIDENCE/0005-wp002-s1-handoff.md`, and `DOCS/reports/001-project-state.md` WP-002 declaration are present and consistent |

## 1.1 Acceptance reproduction

| WP-002 acceptance criterion | Independent result | Assessment |
|---|---|---|
| ~500 seeded float64 cases cover every model × coupling × basic integrator | 504 cases; 14 combos × 36 (N, K, dt) variants; no missing combo | MET |
| Bit-for-bit reproducible from PRINet 3.0.0 | `pytest parity/ -m parity` regenerates representative cases via archived `prinet` and all 6 tests pass | MET |
| Immutable source/version metadata and SHA-256 manifest | `CorpusManifest` has `schema_version`, `generator`, `generator_version`, `prin_version`, `reference_source`, `created_at`, per-file `sha256`; 504 digests present | MET |
| Differential harness detects planted deviations at mandated tolerances | `test_harness_detects_planted_deviation_on_corpus` and `test_assert_parity_raises_on_divergence` pass; perturbations fail `np.isclose` at `rtol=1e-6, atol=1e-8` (trajectory) | MET |
| Hypothesis strategies generate valid seeded cases | `tests/test_parity_strategies.py` 6/6 pass with `@given` | MET |
| Corpus loader and schema validators robust | `tests/test_parity_loader.py`, `test_parity_manifest.py`, `test_parity_schema.py` pass, including missing/corrupt/duplicate cases | MET |
| Coverage on new/changed code ≥95% | Full suite `pytest tests/ parity/ --cov=prin.parity` = 95%; fast `pytest tests/ -m "not slow and not gpu" --cov=prin.parity` = 94.5% (`loader.py` 91%, `manifest.py` 94%) | MET WITH FINDING (`WP002-F1`) |
| Security and quality gates green | ruff, mypy, bandit `python/prin`, cargo audit, pip-audit (project + docs) clean; Snyk Code 0; Snyk Open Source docs req 12 findings | MET WITH FINDING (`WP002-F2`) |

## 2. Methodology

### 2.1 Environment

- OS: Windows 11, PowerShell
- Python: `C:\dev\PRIN\.venv\Scripts\python` 3.14.0
- Rust / Cargo: 1.92.0
- `prinet` 3.0.0 installed editable from `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main`
- `prin` installed editable with `maturin develop -m crates/prin-py/Cargo.toml`

### 2.2 Scope commands

```powershell
git log --oneline -5
git diff --stat 0908b46^..0908b46
```

Key results:

```text
0908b46 feat(WP-002 S1): golden corpus and differential harness against PRINet 3.0.0
 ... 523 files changed, 10830 insertions(+), 3 deletions(-)
```

### 2.3 Quality, test, and coverage commands

```powershell
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/
.venv\Scripts\ruff check parity/
.venv\Scripts\ruff format --check parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml
.venv\Scripts\python -m bandit -r parity/ -c pyproject.toml
.venv\Scripts\python -m pytest tests/ -v -m "not slow and not gpu"
.venv\Scripts\python -m pytest parity/ -v -m parity
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin.parity --cov-report=term-missing
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin.parity --cov-report=term-missing
```

Key results:

```text
ruff check python/...: All checks passed
ruff format --check: 28 files already formatted
ruff check parity/: All checks passed
ruff format --check parity/: 3 files already formatted
mypy: Success: no issues found in 13 source files
interrogate: 100.0% (min 95%)
bandit -r python/prin: No issues identified
bandit -r parity/: B101 assert_used in parity/test_parity_differential.py:68
pytest tests/: 79 passed, 2 deselected
pytest parity/: 6 passed
pytest tests/ --cov=prin.parity: TOTAL 381 stmts, 21 miss, 94%
pytest tests/ parity/ --cov=prin.parity: TOTAL 381 stmts, 18 miss, 95%
```

### 2.4 Rust commands

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
```

Key results:

```text
cargo fmt: exit 0
cargo clippy: Finished; 0 warnings
cargo test: 0 tests per crate, all ok
RUSTDOCFLAGS=-D warnings cargo doc: Generated docs with 0 warnings
```

### 2.5 Dependency and security audit commands

```powershell
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
# Snyk MCP authenticated and executed:
# snyk_code_scan path=C:\dev\PRIN severity_threshold=medium
# snyk_sca_scan path=C:\dev\PRIN severity_threshold=medium
```

Key results:

```text
cargo audit: 0 advisories
pip-audit .: No known vulnerabilities found
pip-audit -r DOCS/sphinx/requirements.txt: No known vulnerabilities found
Snyk Code: issueCount=0
Snyk Open Source: issueCount=12 (idna, jinja2, pygments, requests, soupsieve, urllib3 in DOCS\sphinx\requirements.txt)
```

### 2.6 Corpus validation commands

```powershell
.venv\Scripts\python -c "from pathlib import Path; from prin.parity.loader import CorpusLoader; m=CorpusLoader(Path('parity/corpus')).manifest; print(m.n_cases, m.generator, m.generator_version, m.prin_version, m.reference_source)"
.venv\Scripts\python -c "from collections import Counter; from pathlib import Path; from prin.parity.loader import CorpusLoader; r=[lc.spec for lc in CorpusLoader(Path('parity/corpus'))]; print('models', Counter(s.model for s in r)); print('couplings', Counter(s.coupling for s in r)); print('integrators', Counter(s.integrator for s in r))"
```

Key results:

```text
504 prinet 3.0.0 0.1.0 DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main (prinet==3.0.0)
models Counter({'kuramoto': 216, 'hopf': 216, 'stuart_landau': 72})
couplings Counter({'full': 216, 'mean_field': 144, 'sparse_knn': 144})
integrators Counter({'euler': 252, 'rk4': 252})
```

## 3. Detailed findings

### 3.1 Coverage — `WP002-F1`

The fast test gate (`pytest tests/ -m "not slow and not gpu"`) is the test run used by `.github/workflows/python.yml` for the Codecov upload. On `prin.parity` it measures:

```text
Name                          Stmts   Miss  Cover   Missing
python\prin\parity\harness.py   62      3    95%   34, 132, 180
python\prin\parity\loader.py    47      6    87%   41, 60, 88, 96-98
python\prin\parity\manifest.py 104      6    94%   42, 82, 85, 166, 169, 196
python\prin\parity\schema.py   116      6    95%   39, 46, 48, 134, 137, 247
python\prin\parity\strategies.py 45    0   100%
TOTAL                          381     21    94%
```

The full suite (`pytest tests/ parity/ --cov=prin.parity`) reaches exactly 95% because the slow `parity/` differential tests and `tests/test_generate_corpus.py` exercise additional success/error paths. The 95% gate in Testing Standards §4 is therefore only met when slow/parity tests are included, which the fast CI job does not run. The S1 handoff claims the new modules collectively meet the 95% gate, but it does not distinguish the fast gate from the full suite.

### 3.2 Snyk Open Source docs-dependency findings — `WP002-F2`

Snyk Open Source (`snyk_sca_scan`) reports 12 unaddressed transitive advisories associated with `DOCS\sphinx\requirements.txt`:

| ID | Package | Version | Severity | Fixed in |
|---|---|---|---|---|
| SNYK-PYTHON-IDNA-16769942 | idna | 3.11 | medium | 3.15 |
| SNYK-PYTHON-JINJA2-8548181 | jinja2 | 3.1.4 | medium | 3.1.5 |
| SNYK-PYTHON-JINJA2-8548987 | jinja2 | 3.1.4 | medium | 3.1.5 |
| SNYK-PYTHON-JINJA2-9292516 | jinja2 | 3.1.4 | medium | 3.1.6 |
| SNYK-PYTHON-PYGMENTS-15746419 | pygments | 2.19.2 | medium | 2.20.0 |
| SNYK-PYTHON-REQUESTS-15763443 | requests | 2.32.5 | medium | 2.33.0 |
| SNYK-PYTHON-SOUPSIEVE-17911084 | soupsieve | 2.8 | high | 2.8.4 |
| SNYK-PYTHON-SOUPSIEVE-17911087 | soupsieve | 2.8 | high | 2.8.4 |
| SNYK-PYTHON-URLLIB3-14192442 | urllib3 | 2.5.0 | high | 2.6.0 |
| SNYK-PYTHON-URLLIB3-14192443 | urllib3 | 2.5.0 | high | 2.6.0 |
| SNYK-PYTHON-URLLIB3-14896210 | urllib3 | 2.5.0 | high | 2.6.0 |
| SNYK-PYTHON-URLLIB3-16642024 | urllib3 | 2.5.0 | high | 2.7.0 |

The file declares only `sphinx>=7.0`, `furo>=2024.1.29`, and `myst-parser>=3.0`. The authoritative native audit `pip-audit -r DOCS/sphinx/requirements.txt` reports no vulnerabilities, and the current `.venv` already has patched versions of the flagged packages. However, `.github/workflows/python.yml` line 84-87 runs:

```yaml
npx --yes snyk@1.1304.2 test --file=DOCS/sphinx/requirements.txt --package-manager=pip --severity-threshold=low --fail-on=all
```

If Snyk resolves the same vulnerable set, the security job will fail. The issue is classified D2 because the affected packages are in the documentation build path, the native `pip-audit` is clean, and the finding is a required tool-chain gate rather than a product-security breach. S3 must either produce a resolved lock/pins that Snyk accepts, or provide evidence-backed approved governance if the Snyk resolution is determined to be a false positive.

### 3.3 Documentation/hygiene — `WP002-F3`

- `python/prin/__init__.py` lists subpackages `prin.nn`, `prin.eval`, `prin.experiments`, `prin.reporting` in its docstring but omits the new `prin.parity` subpackage.
- `parity/README.md` still instructs `pip install "prinet==3.0.0"` and refers to "first 100 steps"; the corpus uses 20 steps and the install is now archive-based.
- `pyproject.toml` parity marker comment and `.github/workflows/parity.yml` header still refer to `prinet==3.0.0` as a PyPI install.

These are D4 documentation/hygiene gaps. They do not affect correctness but should be corrected before S4.

### 3.4 Bandit exclusion for `parity/` tests — `WP002-F4`

```text
.venv\Scripts\python -m bandit -r parity/ -c pyproject.toml
>> Issue: [B101:assert_used] ...
   Location: parity/test_parity_differential.py:68:4
```

`pyproject.toml` `[tool.bandit] exclude_dirs` lists `tests`, `benchmarks`, `.venv`, `target` but not `parity/`. Because `parity/test_parity_differential.py` is a test file, it legitimately uses `assert`. A full-repo `bandit -r .` or a future CI change that scans `parity/` will fail. This is a D4 hygiene issue.

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP002-F1 | D2 | `tests/test_parity_*.py` / `.github/workflows/python.yml` | Fast `tests/` suite gives `prin.parity` 94.5% coverage (below 95%); `loader.py` 91%, `manifest.py` 94% | Testing Standards §4; WP-002 acceptance | Add targeted unit tests for uncovered error branches (missing manifest, missing case file, duplicate IDs, `get_record`, malformed `ManifestRecord` fields, etc.) so the fast suite reaches ≥95% on `prin.parity` |
| WP002-F2 | D2 | `DOCS/sphinx/requirements.txt` / `.github/workflows/python.yml` | Snyk Open Source reports 12 unaddressed transitive advisories in docs build deps; CI `snyk test --fail-on=all` expected to fail | Coding Standards §6.2; Development Workflow §3 A6/A9 | Compile/pin docs dependencies to patched versions or add minimum lower bounds and re-run `snyk test` + `pip-audit -r DOCS/sphinx/requirements.txt` until clean; if Snyk resolution is false positive, document approved deviation |
| WP002-F3 | D4 | `python/prin/__init__.py`, `parity/README.md`, `pyproject.toml`, `.github/workflows/parity.yml` | Parent package docstring omits `prin.parity`; README and markers still reference PyPI `prinet==3.0.0` and "100 steps" | Documentation Standards §2; repository hygiene | Update `python/prin/__init__.py` docstring, `parity/README.md`, and stale `prinet==3.0.0` references to reflect archive-based install and 20-step corpus |
| WP002-F4 | D4 | `pyproject.toml` / `parity/test_parity_differential.py` | `bandit -r parity/` flags B101 in a test file because `parity/` is not in `tool.bandit.exclude_dirs` | Coding Standards §6.2; repository hygiene | Add `parity/` to `tool.bandit.exclude_dirs` in `pyproject.toml`, or add `# nosec B101` to the test assertion, and re-run `bandit -r .` |

## 5. Deviation-ledger delta

New findings added to the ledger: `WP002-F1` (D2), `WP002-F2` (D2), `WP002-F3` (D4), `WP002-F4` (D4).

Carried findings re-inspected: none. The cumulative ledger from cycle 001 has zero open findings; the four new findings above are the only delta at the end of this S2.

## 6. Verdict and required actions

**Verdict: PASS-WITH-FINDINGS.**

WP-002 implements the declared golden-trajectory corpus and differential harness. The 504-case corpus is complete, the manifest and SHA-256 digests are present, the differential harness detects planted deviations, and the quality gates (ruff, mypy, cargo, `pip-audit` project, Snyk Code, cargo audit) are clean. The two D2 findings must be cleared in S3 before the cycle can close with a clean delta re-audit and S4 documentation.

Ordered S3 action list:

1. `WP002-F1` (D2): add targeted unit tests for `prin.parity.loader` and `prin.parity.manifest` error branches so that `pytest tests/ -m "not slow and not gpu" --cov=prin.parity` reports ≥95%.
2. `WP002-F2` (D2): resolve or document the Snyk Open Source findings in `DOCS/sphinx/requirements.txt` and confirm `pip-audit -r DOCS/sphinx/requirements.txt` and Snyk SCA are both clean.
3. `WP002-F3` (D4): update parent package docstring, `parity/README.md`, and stale `prinet==3.0.0` references.
4. `WP002-F4` (D4): add `parity/` to bandit exclusions or suppress the test assert and confirm `bandit -r .` is clean.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP002-F1 |  |  |  |
| WP002-F2 |  |  |  |
| WP002-F3 |  |  |  |
| WP002-F4 |  |  |  |

**Delta re-audit date:** — **Result:**
