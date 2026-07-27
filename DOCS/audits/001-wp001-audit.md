# PRIN Audit Report — Cycle 001 / WP-001

**Date:** 2026-07-21
**Auditor:** Devin (AI pair), supported by three independent read-only reviews
**Scope:** WP-001 "Foundation baseline and traceability" — the fixed S1 range,
baseline automation, tests, generated evidence, workflows, packaging, and
applicable repository governance
**Sessions:** 0001 implementation; 0002 this audit
**Active brief:**
`DOCS/sessions/phase-0/0002-wp001-s2-foundation-baseline-and-traceability.md`
**Git state:** `feat/wp001-foundation-baseline` at
`c2f5e342f2c80cf94183dbd04d63dd1c8b3fd017`
**Pre-S1 baseline:** `655521df49b0f2088190f244d98ef65043243bc8`
**Implementation commit:** `c9c3cded4e0b2bc83277351584c6400a4f850340`
**Audit range:**
`655521df49b0f2088190f244d98ef65043243bc8..c2f5e342f2c80cf94183dbd04d63dd1c8b3fd017`
**Verdict:** **FAIL**
**Maintainer acknowledgment:** **ACKNOWLEDGED** — repository maintainer
(`Symbo-gif`), 2026-07-21; applies to the revised 11-finding verdict

---

## 1. Executive summary

WP-001 remained within its non-numerical scope and produced a reproducible
current-state inventory and a complete current traceability matrix: independent
AST counting found 43 archived modules, 657 module-symbol rows, 172 canonical
top-level exports, and no unowned row. The S1 implementation and its 37 focused
tests were committed together, and the measured changed-code coverage is
478/503 statements, or 95.03%.

The audit nevertheless found eleven deviations. Four are D1 security findings:
a PyO3 dependency with two fixed advisories, a non-gating and incomplete Python
dependency audit, long-lived-token crates.io publishing, and disabled hosted
secret scanning/push protection. Six are D2 standard violations involving fail-open baseline
checks, a guaranteed-failing repro path, non-packageable workspace crates,
absent
`main` protection, and a broken Linux CI bootstrap. One D4 finding covers the
warning-as-error Sphinx gate and an inaccurate warning attribution in the S1
baseline report. Any D1 requires a `FAIL` verdict under the Development Workflow
and Audit Standards §3/§5.

| Area | Status | Evidence summary |
|---|---|---|
| WP/session-brief scope conformance (A1) | PASS | Ten added files, 3,371 insertions, no numerical/source-package or dependency change |
| Plan/architecture conformance (A2) | PASS | Static standard-library AST tooling; archive never imported; no numerics, unsafe block, or runtime code generation added |
| Tests in tandem + coverage (A3) | FAIL | Same implementation commit; 37/37 pass and 95.03%, but mutation probes expose fail-open traceability and session-ledger checks (`WP001-F4`, `WP001-F5`) |
| Numerical parity + invariants (A4) | N/A | No numerical primitive, tolerance, stochastic path, gradient, or kernel changed |
| Quality gates (A5) | PASS | Rust and Python local gates reproduced cleanly |
| Security (A6) | FAIL | Two RustSec advisories plus three CI/supply-chain control breaches (`WP001-F1`–`WP001-F3`, `WP001-F8`); local SAST, Pip Audit, and S1 secret scan clean |
| Docstring/doc coverage (A7) | WARN | Rustdoc clean and Interrogate 100%; Sphinx `-W` has two warnings (`WP001-F9`) |
| Repository hygiene (A8) | FAIL | Generated files were byte-equal at fixed state `c2f5e34`; no changed-file secret/stub issue; duplicate brief IDs can pass validation (`WP001-F5`) |
| CI status (A9) | FAIL | PR #1 has Rust-audit, Linux-Python, and repro failures; `main` is unprotected (`WP001-F1`, `WP001-F6`, `WP001-F10`, `WP001-F11`) |
| Artefact trail (A10) | WARN | Bootstrap handoff and generated artefacts are present and consistent; evidence checks are not fail-closed and one warning is misattributed |

### 1.1 Acceptance reproduction

| WP-001 acceptance criterion | Independent result | Assessment |
|---|---|---|
| Baseline automation is tested | 37 focused tests pass; 95.03% line coverage | MET WITH FINDINGS — `WP001-F4`, `WP001-F5` |
| Repository-state inventory exists | At fixed state `c2f5e34`, regenerated JSON is byte-equal; SHA-256 `21c4bd93b72b593e188304cd51100f91b9d4d2582d87693715c8ce6c3814773f` | MET |
| Every PRINet 3.0 module has a future WP | 43/43 rows; all owner IDs resolve to approved future S1 briefs | MET |
| Every PRINet 3.0 public symbol has a future WP | 657/657 rows; 172/172 top-level exports; no unused override | MET IN CURRENT STATE; gate weakness is `WP001-F4` |
| Metadata consistency is automated | Current metadata and 198-session sequence pass | MET WITH FINDING — duplicate IDs fail open in `WP001-F5` |
| Quality/security baseline is measured | Local quality, dependency, SAST, packaging, docs, and workflow probes reproduced | MET |
| Baseline gaps are evidence-backed and recorded | S1 recorded the principal red baselines, but S2 found additional control defects and corrected the Sphinx warning attribution | PARTIAL — findings below provide the authoritative delta |
| No numerical implementation is introduced | No diff under `crates/`, `python/`, `parity/`, `benchmarks/`, `models/`, `notebooks/`, or `paper/` | MET |

## 2. Methodology

### 2.1 Environment and audit controls

| Item | Audit value |
|---|---|
| OS | Windows 11 Home, `10.0.26200` |
| Supported Python test runners | CPython 3.13.12 / pytest 8.4.2; CPython 3.12.9 / pytest 9.0.1 cross-check |
| Rust / Cargo | 1.92.0 / 1.92.0 |
| Cargo Audit | 0.22.2, installed to an isolated temporary root |
| Pip Audit | 2.10.1 through an isolated `uvx` environment |
| Sphinx | 9.0.4 with declared Furo and MyST requirements and a wheel-backed PRIN import |
| GitHub evidence | Authenticated repository-admin read access; private repository; PR #1 at `c2f5e34` |
| Audit discipline | Source read-only; only this report is added in S2 |

Authenticated read-only queries confirmed that all six workflows are active and
PR #1 targets `main` from the audited commit. Its Rust audit, three Linux Python
jobs, and repro job are red; the corresponding Windows Python and non-audit Rust
jobs are green. The `main` protection endpoint returns "Branch not protected",
there are no repository rulesets, and the secret-scanning endpoint returns
"Secret scanning is disabled on this repository." These hosted facts replace
the earlier local-only evidence limitation.

### 2.2 Scope and artefact commands

```powershell
git log --format="%H`t%ad`t%s" --date=iso-strict 655521d..HEAD
git diff --stat 655521d..HEAD
git diff --name-status 655521d..HEAD
git diff --check 655521d..HEAD
git diff --name-only 655521d..HEAD -- crates/** python/** parity/** `
    benchmarks/** models/** notebooks/** paper/**
git ls-remote --heads origin main feat/wp001-foundation-baseline
```

Key results:

```text
c9c3cde  feat(WP-001): add foundation baseline automation
c2f5e34  docs(WP-001): record S1 evidence handoff
10 files changed, 3371 insertions(+)
No changed numerical/source-package path; no diff-check error.
origin/main -> 655521d; origin/feat/wp001-foundation-baseline -> c2f5e34.
```

At fixed state `c2f5e34`, before creating this report:

```powershell
python tools/wp001_baseline.py check
# Regenerate inventory and traceability in memory and compare exact text.
# Independently parse all archived Python ASTs without importing the archive.
```

Key results:

```text
WP-001 baseline validation passed.
inventory_equal=True
traceability_equal=True
modules=43 symbols=657 top_level=172 frozen=98 unfrozen=74
unused_overrides=[]
independent_modules=43 independent_symbol_rows=657 top_level=172
frozen=98 unfrozen=74 missing_frozen=0
```

### 2.3 Test, coverage, quality, and documentation commands

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test --workspace --features strict-checks
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
ruff check python/ tests/ benchmarks/ tools/
ruff format --check python/ tests/ benchmarks/ tools/
mypy python/prin --strict
$env:PYTHONPATH='C:\Python314\Lib\site-packages'
interrogate -c pyproject.toml python/prin
bandit -r python/prin -c pyproject.toml
bandit -r tools -c pyproject.toml
pytest tests/ -v -m "not slow and not gpu"
py -3.12 -m pytest tests/ -v -m "not slow and not gpu"
C:\Users\there\miniforge3\python.exe -m coverage run --source=tools `
    -m pytest tests/test_wp001_baseline.py -q
C:\Users\there\miniforge3\python.exe -m coverage report `
    --include="tools/wp001_baseline.py" --fail-under=95
```

Key results:

```text
Cargo fmt/clippy/tests/strict-checks/rustdoc: exit 0
Ruff: all checks passed; 12 files already formatted
Mypy: success, 7 source files
Interrogate: 100.0% (minimum 95.0%)
Bandit: 0 findings in 74 shipped-Python lines and 941 tool lines
Pytest: 38 passed on Python 3.13.12; 38 passed on Python 3.12.9
Focused tests: 37 passed
Coverage: 503 statements, 25 missed, 95.03%
```

The Interrogate command used a process-local path-precedence correction because
a user-site `py.py` shadows Interrogate's dependency. No repository setting was
changed. An initial Sphinx process without the declared MyST dependency was
discarded as an invalid environment; the controlled rerun used all declared
documentation requirements.

```powershell
maturin build --locked -m crates/prin-py/Cargo.toml --out <temp>/dist
python -m pip install --no-deps --target <temp>/site <wheel>
$env:PYTHONPATH='<temp>/site'
uvx --from sphinx==9.0.4 --with 'furo>=2024.1.29' `
    --with 'myst-parser>=3.0' sphinx-build -W --keep-going `
    -b html DOCS/sphinx <temp>/html
```

Key result: autodoc imported the wheel, but Sphinx exited 1 with two warnings:
missing `DOCS/sphinx/_static` and `DOCS/sphinx/README.md` absent from a toctree.
The Torch inventory redirect was informational in this run, not one of the two
counted warnings.

### 2.4 Security, packaging, and CI probes

```powershell
<temp>/bin/cargo-audit.exe audit
uvx --from pip-audit==2.10.1 pip-audit .
uvx --from pip-audit==2.10.1 pip-audit `
    -r DOCS/sphinx/requirements.txt
# detect-secrets 1.5.0 over exactly the ten S1-changed files
cargo package --workspace --allow-dirty --no-verify --offline
python tools/reproduce.py --verify-manifest
```

Key results:

```text
Cargo Audit: 2 vulnerabilities in pyo3 0.22.6
  RUSTSEC-2025-0020; fixed in >=0.24.1
  RUSTSEC-2026-0177; fixed in >=0.29.0
Pip Audit project: no known vulnerabilities
Pip Audit Sphinx requirements: no known vulnerabilities
S1 changed-file secret candidates: 0
Cargo package: exit 101; prin-kernels dependency prin-dynamics has no version
Reproduce: exit 1; Phase 6 NotImplementedError
```

Targeted scans also found no executable `unsafe`, `eval`, `exec`, dynamic
`compile`, `pickle.load`, `shell=True`, or credential-pattern match in S1 scope.
Every Rust crate currently retains `#![forbid(unsafe_code)]`. The only active
stub marker is the declared Phase 6 `tools/reproduce.py` placeholder.

### 2.5 Fail-closed mutation probes

The following probes changed only temporary or in-memory audit fixtures.

```powershell
python -c '<collect current traceability; remove its final symbol row; `
set symbol_count to 656; substitute that result into validate_baseline>'
```

```text
removed=prinet.utils.y4q1_tools.windowed_order_parameter_variance
mutated_symbol_count=656
validate_baseline_errors=[]
```

```powershell
python -c '<create a temporary session tree with a duplicate 0002 brief `
before copying the governed 198-brief tree; run validate_session_plan>'
```

```text
physical_numbered_briefs=199
indexed_numbered_briefs=198
validator_errors=[]
```

These results are independently explained by
`tools/wp001_baseline.py:593-599,632-634,905-926` and the permissive test at
`tests/test_wp001_baseline.py:155-163`.

### 2.6 Hosted repository and CI evidence

```powershell
gh workflow list --repo Symbo-gif/PRIN --all
gh run list --repo Symbo-gif/PRIN `
    --branch feat/wp001-foundation-baseline --limit 100 --json ...
gh pr list --repo Symbo-gif/PRIN `
    --head feat/wp001-foundation-baseline --state all --json ...
gh api repos/Symbo-gif/PRIN/branches/main/protection
gh api repos/Symbo-gif/PRIN/rulesets
gh api repos/Symbo-gif/PRIN/secret-scanning/alerts
```

Key results at audited branch SHA `c2f5e34`:

```text
PR #1: OPEN, head c2f5e34, base main
Six declared workflows: active
rust run 29560485016: failure (audit failed; other Rust jobs passed)
python run 29560484777: failure (all three Ubuntu builds failed;
  all three Windows tests, lint, and nominal security job passed)
repro run 29560484775: failure during the same Linux build bootstrap
gpu run 29560484758: skipped as designed without [gpu]
main protection: HTTP 404, "Branch not protected"
rulesets: []
secret scanning: HTTP 404, "Secret scanning is disabled on this repository."
vulnerability alerts: HTTP 404, disabled (additional observation)
```

The failed Linux logs identify `maturin develop` outside a virtualenv or Conda
environment as the common Python/repro bootstrap failure. The Rust audit log
independently reports the same two PyO3 advisories as the local audit. The Python
security job is green only because its command ends in `|| true`, corroborating
`WP001-F2` rather than clearing it.

## 3. Detailed findings

### 3.1 A1 — WP and session-brief scope

The fixed range contains the baseline tool, ownership data, tandem tests, four
baseline artefacts plus their README, and the S1 handoff. The implementation
commit contains both `tools/wp001_baseline.py` and
`tests/test_wp001_baseline.py`; the handoff is a documentation-only successor
commit. No existing test, tolerance, assertion, dependency, workflow, archive
file, numerical source, model, benchmark, notebook, or paper file changed.

**Result:** PASS.

### 3.2 A2 — Plan and architecture conformance

The new tool uses only the Python standard library, performs static AST
inspection, and never imports archived PRINet. Its no-import invariant is tested
at `tests/test_wp001_baseline.py:135-163`. No backend dispatch, numerical
algorithm, stochastic state, compiled binding, or public runtime API changed.
No new unsafe/code-generation mechanism or dependency was introduced.

**Result:** PASS.

### 3.3 A3 — Tests in tandem and coverage

All executable S1 behavior and its tests are in `c9c3cde`. Thirty-seven focused
tests pass and changed-code coverage is 95.03%, satisfying the numerical
coverage threshold. The all-addition diff contains no weakened or skipped test
and no tolerance change. Specialized parity, property, gradient, and
kernel-equivalence layers are not applicable.

Coverage alone did not expose two fail-open behaviors: exact symbol cardinality
is not bound, and duplicate numbered briefs collapse in a dictionary. These are
`WP001-F4` and `WP001-F5`.

**Result:** FAIL.

### 3.4 A4 — Numerical parity and invariants

No numerical primitive or invariant was touched. The absence of a golden corpus
is the planned entry state for WP-002, not a WP-001 deviation. No performance or
scientific conclusion was asserted.

**Result:** N/A.

### 3.5 A5 — Code quality gates

Fmt, Clippy with warnings denied, workspace tests, strict-check tests, Rustdoc
with warnings denied, Ruff lint/format, strict Mypy, Interrogate, Bandit, and the
fast Python suite all pass. The current Rust crates have zero unit tests because
the numerical implementation WPs have not begun; this is a declared planned gap,
not evidence of untested WP-001 behavior.

**Result:** PASS.

### 3.6 A6 — Security

`Cargo.lock:740-742` resolves PyO3 0.22.6. Current RustSec data reports two
fixed vulnerabilities, producing `WP001-F1`. The Python security workflow audits
only documentation requirements and suppresses its result at
`.github/workflows/python.yml:51-59`, producing `WP001-F2`. The release workflow
passes a long-lived `CARGO_REGISTRY_TOKEN` at
`.github/workflows/release.yml:78-89`, contrary to the explicit OIDC-only
supply-chain rule and producing `WP001-F3`.

Local Pip Audit runs are clean, Bandit and Ruff security rules are clean, and a
changed-file secret scan reports zero candidates. Authenticated admin queries
nevertheless confirm that hosted secret scanning is disabled; push protection
cannot be active while that facility is disabled. This directly produces
`WP001-F8`. GitHub vulnerability alerts are also disabled, recorded as an
additional observation because the normative clause specifically names secret
scanning and push protection.

**Result:** FAIL.

### 3.7 A7 — Documentation coverage

Rustdoc passes with warnings denied and Python callable documentation is 100%.
The wheel-backed Sphinx build resolves the active package but fails `-W` on the
missing `_static` path configured at `DOCS/sphinx/conf.py:39` and the unlisted
`DOCS/sphinx/README.md` (the project toctree is at
`DOCS/sphinx/index.rst:11-35`). S1 attributed the second warning to a Torch
inventory redirect at `DOCS/baselines/wp001_baseline_report.md:228-234`; that
redirect was informational in the controlled audit run. This is `WP001-F9`.

**Result:** WARN.

### 3.8 A8 — Repository hygiene

At fixed state `c2f5e34`, before creating this report, the generated JSON and
Markdown were byte-equal to fresh generation. All 43 modules and 657 symbol rows
are owned, no ownership override is unused, and `git diff --check` is clean. No
S1 file contains a secret candidate, TODO, FIXME, numerical stub, or orphan
output. The declared Phase 6 reproduction placeholder is the sole active
`NotImplementedError`.

The session validator does not count physical numbered briefs uniquely:
`_numbered_briefs` overwrites a duplicate key before the 198-entry check. A
199-file mutation therefore passes with no error (`WP001-F5`).

**Result:** FAIL.

### 3.9 A9 — CI and regressions

PR #1 and its four triggered workflows provide hosted branch evidence at the
fixed audited SHA. Rust run `29560485016` fails only its Cargo Audit job
(`WP001-F1`); the other Rust jobs pass. Python run `29560484777` passes lint,
all three Windows tests, and the nominal security job, but all three Ubuntu
matrix jobs fail during `maturin develop` before tests (`WP001-F11`). The
security job's success is false assurance because `|| true` suppresses its
incomplete audit (`WP001-F2`). Repro run `29560484775` fails at the same Linux
bootstrap; after that is repaired, direct invocation proves the Phase 6
placeholder remains a second deterministic failure (`WP001-F6`).

The release workflow's crate loop cannot package the current path-only workspace
dependencies (`WP001-F7`) and uses the prohibited token from `WP001-F3`.
Separately, authenticated settings show `main` has neither branch protection nor
a ruleset, so the mandatory PR/review/green-CI policy is not enforced
(`WP001-F10`). Hosted secret scanning is disabled (`WP001-F8`).

Benchmark regression gates are not applicable to this non-performance WP.

**Result:** FAIL.

### 3.10 A10 — Artefact trail

WP-001 is the bootstrap exception, so no prior cycle Audit Report, Project State
Report, or cumulative deviation ledger exists. The plan declaration, S1 brief,
implementation commit, baseline artefacts, and S1 handoff are present and
mutually identify the correct baseline/implementation SHAs. At the fixed S1
audit state, generated artefacts matched fresh generation exactly.

The validator does not bind the exact 657-row traceability contract, and the S1
report misattributes one Sphinx warning. Those limitations are captured by
`WP001-F4` and `WP001-F9` rather than silently accepted.

**Result:** WARN.

### 3.11 Formal findings

#### WP001-F1 — Fixed PyO3 vulnerabilities remain locked

- **Severity:** D1 — security trajectory breach.
- **Evidence:** `crates/prin-py/Cargo.toml:23-24`, `Cargo.lock:740-742`, and
  Cargo Audit 0.22.2 reporting `RUSTSEC-2025-0020` and
  `RUSTSEC-2026-0177`.
- **Violated clauses:** Coding Standards §6.2 (zero unaddressed advisories);
  Development Workflow and Audit Standards §5 (security breach is D1).
- **Required remedy:** Upgrade PyO3 and its compatible NumPy binding to a version
  resolving both advisories (PyO3 at least 0.29.0), update the lockfile, and run
  binding, wheel, type-stub, and full local-gate regression evidence in S3.

#### WP001-F2 — Python dependency audit is incomplete and non-gating

- **Severity:** D1 — security control breach.
- **Evidence:** `.github/workflows/python.yml:51-59` audits only
  `DOCS/sphinx/requirements.txt` and appends `|| true`; local project and docs
  audits are currently clean but CI would ignore future findings.
- **Violated clauses:** Coding Standards §6.2; Versioning and Release Standards
  §3 `python.yml` gate.
- **Required remedy:** Audit installed project/runtime and documentation
  dependencies, remove failure suppression, and prove a failing audit fails the
  job without weakening dependency policy.

#### WP001-F3 — Crates publication uses a long-lived registry token

- **Severity:** D1 — supply-chain security breach.
- **Evidence:** `.github/workflows/release.yml:78-89` passes
  `secrets.CARGO_REGISTRY_TOKEN` to every `cargo publish` call.
- **Violated clause:** Coding Standards §6.3 requires OIDC trusted publishing and
  no long-lived release token.
- **Required remedy:** Configure crates.io trusted publishing/OIDC with least
  permissions and remove token use, or obtain an explicit approved standards
  amendment if the required provider capability is unavailable.

#### WP001-F4 — Traceability evidence checks are not fail-closed

- **Severity:** D2 — testing and evidence-control standard violation.
- **Evidence:** `validate_baseline` checks 43 modules and 172 top-level exports
  but not the exact 657 module-symbol rows at
  `tools/wp001_baseline.py:905-926`; the test permits any count at least 652 at
  `tests/test_wp001_baseline.py:155-163`. An in-memory 656-row result returned
  no validation error. Current generated files are equal at the fixed audit
  state, so no current row is missing.
- **Violated clauses:** Project Plan §6.1 traceability acceptance; Testing
  Standards §5 audit hooks; Development Workflow and Audit Standards §1
  evidence-based requirement.
- **Required remedy:** Bind the immutable archive contract to the exact 657-row
  public-symbol count and add a mutation/regression test that fails on any lost
  row.

#### WP001-F5 — Duplicate numbered session briefs can pass validation

- **Severity:** D2 — governance metadata control violation.
- **Evidence:** `_numbered_briefs` stores files by sequence in a dictionary at
  `tools/wp001_baseline.py:593-599`, then validates only dictionary length at
  lines 632-634. A temporary fixture with 199 physical briefs and duplicate
  sequence 0002 indexed as 198 and returned no errors.
- **Violated clauses:** Project Plan §8.2; Development Workflow and Audit
  Standards §8 (broken session metadata that can authorize work incorrectly is
  D2); WP-001 metadata-consistency acceptance.
- **Required remedy:** Detect duplicate sequence IDs before indexing, count
  physical numbered briefs, and add a regression test that fails on a duplicate
  in any phase.

#### WP001-F6 — Repro CI deterministically fails on current tool changes

- **Severity:** D2 — CI standard violation.
- **Evidence:** `.github/workflows/repro.yml:9-13,25-31` triggers on `tools/**`
  and is intended to execute `tools/reproduce.py`; that script raises the
  declared Phase 6 `NotImplementedError` at `tools/reproduce.py:23-33`, and
  direct execution exits 1. Hosted run `29560484775` currently fails even
  earlier at the Linux bootstrap captured separately by `WP001-F11`.
- **Violated clauses:** Versioning and Release Standards §3 `repro.yml` gate;
  Development Workflow audit checklist A9.
- **Required remedy:** Repair `WP001-F11`, then add an explicit, testable
  pre-WP-035 guard or narrow the trigger so unrelated tool changes pass. Do not
  implement Phase 6 numerics or artefact generation in WP-001 S3.

#### WP001-F7 — Workspace crates cannot be packaged as release CI declares

- **Severity:** D2 — packaging/release standard violation.
- **Evidence:** `Cargo.toml:27-35` declares path-only internal dependencies;
  offline `cargo package --workspace --allow-dirty --no-verify` exits 101 at
  `prin-kernels` because `prin-dynamics` has no version. The active publication
  loop is `.github/workflows/release.yml:78-89`.
- **Violated clauses:** Versioning and Release Standards §3 `release.yml` gate
  and §4 crate-publication procedure.
- **Required remedy:** Add publishable version-plus-path metadata and package
  checks in dependency order, or explicitly guard crate publication until its
  approved Phase 0 owner. Silent deferral is not acceptable.

#### WP001-F8 — Hosted secret scanning and push protection are disabled

- **Severity:** D1 — hosted security-control breach.
- **Evidence:** The authenticated caller has repository-admin permission. The
  secret-scanning alerts endpoint returns HTTP 404 with "Secret scanning is
  disabled on this repository," and the repository response has no
  `security_and_analysis` object. Push protection cannot be enabled while secret
  scanning is disabled. Vulnerability alerts independently return disabled.
- **Violated clauses:** Coding Standards §6.2 requires hosted secret scanning and
  push protection enabled with zero alerts; Development Workflow and Audit
  Standards §5 classifies security breaches as D1.
- **Required remedy:** Enable GitHub secret scanning and push protection and
  record a zero-alert authenticated check. If the private-repository plan cannot
  provide those controls, implement an equivalent blocking control only through
  an explicit approved standards amendment rather than silent substitution.

#### WP001-F9 — Sphinx warning gate and baseline warning attribution are stale

- **Severity:** D4 — minor documentation/evidence gap.
- **Evidence:** Wheel-backed Sphinx 9.0.4 exits 1 under `-W` because
  `DOCS/sphinx/conf.py:39` names a missing `_static` path and
  `DOCS/sphinx/README.md` is absent from `index.rst:11-35`. The S1 report at
  `DOCS/baselines/wp001_baseline_report.md:228-234` instead names the Torch
  inventory redirect as the second warning.
- **Violated clauses:** Documentation Standards §7 documentation gate;
  Development Workflow and Audit Standards §1 evidence accuracy.
- **Required remedy:** Remove or satisfy the stale static path, include or
  explicitly exclude the README, and rerun wheel-backed Sphinx with warnings
  denied. Preserve this Audit Report as the correction to the immutable S1
  baseline rather than rewriting baseline history.

#### WP001-F10 — The default branch does not enforce governed merges

- **Severity:** D2 — merge-governance standard violation.
- **Evidence:** The authenticated `main` branch-protection endpoint returns HTTP
  404 with "Branch not protected," and the repository rulesets endpoint returns
  an empty array. Direct pushes, unreviewed merges, and merges with red checks are
  therefore not technically blocked.
- **Violated clauses:** Versioning and Release Standards §2 requires PR-only
  merges and an always-releasable `main`; Coding Standards §4 requires green CI
  and maintainer review; audit checklist A9 requires branch CI evidence.
- **Required remedy:** Protect `main` with required pull requests, maintainer
  review, required applicable status checks, force-push/deletion prevention, and
  equivalent ruleset controls; capture the resulting settings as evidence.

#### WP001-F11 — Linux Python and repro jobs cannot build the extension

- **Severity:** D2 — cross-platform CI standard violation.
- **Evidence:** PR runs `29560484777` and `29560484775` fail every Ubuntu Python
  matrix job and the repro job during `maturin develop`. Their logs state that
  Maturin cannot find a virtualenv or Conda environment. Windows Python jobs and
  non-audit Rust jobs pass, isolating the failure to Linux workflow bootstrap.
- **Location:** `.github/workflows/python.yml:39-43` and
  `.github/workflows/repro.yml:25-29`.
- **Violated clauses:** Versioning and Release Standards §3 requires the Python
  Linux/Windows matrix and repro gate to pass; Project Plan N2 requires Linux
  platform support.
- **Required remedy:** Build/install in an explicitly created environment or use
  `maturin build` plus wheel installation, then rerun Python 3.11–3.13 on Linux
  and the repro job. Keep the separate Phase 6 guard under `WP001-F6`.

### 3.12 Planned gaps that are not current deviations

| S1 candidate | S2 disposition |
|---|---|
| BG-006 — 98 frozen vs 172 canonical top-level exports | Confirmed archived-reference observation. No frozen export is missing from `__all__`; the 74 later additions are explicitly mapped to WP-036. The archive is read-only, so this is not a current PRIN deviation. |
| BG-007 — acceptance suite and Rust numerical tests absent | Planned pre-numerical state. Incremental implementation WPs and WP-036 own it. |
| BG-008 — golden parity corpus absent | Planned entry state for immediate successor WP-002; no touched numerical primitive requires parity in WP-001. |
| BG-009 — controller model/manifest absent | Planned WP-028/WP-035 deliverables; no model behavior is claimed now. |
| BG-010 — benchmarks, notebooks, and paper are placeholders | Planned WP-033/WP-037 deliverables; no performance/scientific claim was made. |

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP001-F1 | D1 | `crates/prin-py/Cargo.toml:23-24`; `Cargo.lock:740-742` | PyO3 0.22.6 has two fixed RustSec vulnerabilities | Coding §6.2; Workflow §5 | Upgrade to a compatible PyO3 >=0.29.0 and rerun bridge/wheel gates |
| WP001-F2 | D1 | `.github/workflows/python.yml:51-59` | Pip Audit omits project dependencies and cannot fail CI | Coding §6.2; Versioning §3 | Audit all dependency scopes and remove suppression |
| WP001-F3 | D1 | `.github/workflows/release.yml:78-89` | Crates publication uses a long-lived token | Coding §6.3 | Move crates publication to trusted OIDC |
| WP001-F4 | D2 | `tools/wp001_baseline.py:905-926`; `tests/test_wp001_baseline.py:155-163` | Exact public-symbol cardinality can silently drift | Plan §6.1; Testing §5; Workflow §1 | Enforce exactly 657 rows with a mutation regression test |
| WP001-F5 | D2 | `tools/wp001_baseline.py:593-599,632-634` | Duplicate brief IDs collapse and can pass | Plan §8.2; Workflow §8 | Reject duplicates before indexing and test the mutation |
| WP001-F6 | D2 | `.github/workflows/repro.yml:9-31`; `tools/reproduce.py:23-33` | Repro CI always fails for current `tools/**` PRs | Versioning §3; checklist A9 | Add a governed pre-WP-035 guard/narrow trigger |
| WP001-F7 | D2 | `Cargo.toml:27-35`; `.github/workflows/release.yml:78-89` | Internal crates cannot be packaged/published | Versioning §3/§4 | Add publishable versions/package gates or explicit guard |
| WP001-F8 | D1 | GitHub repository security settings | Secret scanning and push protection are disabled | Coding §6.2; Workflow §5 | Enable both controls and verify zero alerts, or approve an explicit amendment |
| WP001-F9 | D4 | `DOCS/sphinx/conf.py:39`; `DOCS/sphinx/index.rst:11-35`; baseline report 228-234 | Sphinx `-W` fails and one warning is misattributed | Documentation §7; Workflow §1 | Resolve both warnings; preserve this audit as the immutable-baseline correction |
| WP001-F10 | D2 | GitHub `main` protection and rulesets | Governed PR/review/green-check merges are not enforced | Versioning §2; Coding §4; checklist A9 | Protect `main` with required review/check controls |
| WP001-F11 | D2 | `.github/workflows/python.yml:39-43`; `.github/workflows/repro.yml:25-29` | Linux jobs run `maturin develop` without an environment and fail before tests | Versioning §3; Plan N2 | Create an environment or install built wheels, then rerun the Linux matrix |

## 5. Deviation-ledger delta

This bootstrap cycle has no preceding Project State Report or cumulative ledger.
Add the following open findings to the first ledger: `WP001-F1` through
`WP001-F11`. There are no carried findings to re-inspect.

| Severity | New findings | Count |
|---|---|---:|
| D1 | `WP001-F1`, `WP001-F2`, `WP001-F3`, `WP001-F8` | 4 |
| D2 | `WP001-F4`, `WP001-F5`, `WP001-F6`, `WP001-F7`, `WP001-F10`, `WP001-F11` | 6 |
| D3 | None | 0 |
| D4 | `WP001-F9` | 1 |

All remain open pending session 0003. No finding is suppressed or pre-marked
`FIXED`, `AMENDED`, or `CARRIED(1)`.

## 6. Verdict and required actions

**Verdict: FAIL.** Four D1 security findings independently require this verdict
and freeze new feature work. The complete current traceability matrix, scope
compliance, green local quality gates, and 95.03% coverage do not override the
mandatory severity rule.

Session 0003 must work only these findings, in this order:

1. Resolve `WP001-F1`–`WP001-F3` and `WP001-F8`, with dependency/bridge
   regression evidence, gating dependency audits, tokenless trusted publication,
   and enabled hosted secret controls.
2. Resolve `WP001-F4` and `WP001-F5` with fail-before/pass-after mutation tests.
3. Repair Linux workflow bootstrap (`WP001-F11`), then guard the premature repro
   path (`WP001-F6`) without implementing WP-035.
4. Make or explicitly guard crate packaging (`WP001-F7`) under the approved
   Phase 0 packaging trajectory.
5. Enforce governed merges on `main` (`WP001-F10`) and capture settings evidence.
6. Clear the two Sphinx warnings and retain this audit correction (`WP001-F9`).
7. Append the closure table below and independently delta re-audit every touched
   area. Repeat S3/delta audit until clean.

The maintainer must acknowledge this verdict in the header before the report is
committed. After that commit, hand off to session 0003; do not begin WP-002.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP001-F1 | PENDING | — | — |
| WP001-F2 | PENDING | — | — |
| WP001-F3 | PENDING | — | — |
| WP001-F4 | PENDING | — | — |
| WP001-F5 | PENDING | — | — |
| WP001-F6 | PENDING | — | — |
| WP001-F7 | PENDING | — | — |
| WP001-F8 | PENDING | — | — |
| WP001-F9 | PENDING | — | — |
| WP001-F10 | PENDING | — | — |
| WP001-F11 | PENDING | — | — |

**Delta re-audit date:** PENDING — **Result:** findings remain
