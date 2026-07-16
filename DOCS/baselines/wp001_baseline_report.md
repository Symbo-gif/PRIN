# WP-001 foundation baseline report

**Session:** 0001 — WP-001 S1
**Date:** 2026-07-16
**Baseline commit:** `655521df49b0f2088190f244d98ef65043243bc8`
**Measurement branch:** `feat/wp001-foundation-baseline`
**Status:** S1 characterization evidence; not an audit verdict

## 1. Scope and method

This report measures the pre-numerical PRIN scaffold required by WP-001. It
covers repository state, PRINet 3.0 API ownership, metadata, quality, security,
CI configuration, packaging, and governance. It makes no performance or
scientific claim and generates no golden data.

The archived PRINet 3.0 package is parsed with the Python `ast` module. It is
never imported or executed. A literal module `__all__` is authoritative when
present; otherwise public top-level classes, functions, and assignments are
included. Package re-exports are resolved statically to their definition before
future-WP ownership is assigned.

Machine-derived evidence:

- `wp001_repository_inventory.json`
- `wp001_api_traceability.md`
- `../../tools/wp001_ownership.json`
- `../../tools/wp001_baseline.py`

## 2. Environment

| Item | Measured value |
|---|---|
| OS | Windows 11 (`10.0.26200`, x86-64) |
| Python | 3.13.12 |
| Rust | `rustc 1.92.0` |
| Cargo | 1.92.0 |
| Maturin | 1.12.6 |
| Ruff | 0.15.5 |
| Mypy | 1.19.1 |
| Pytest | 8.4.2 |
| Interrogate | 1.7.0 |
| Bandit | 1.9.2 |
| Cargo Audit | 0.22.2, isolated temporary install |
| Pip Audit | 2.10.1, isolated `uvx` environment |

No benchmark was run. Hardware performance is therefore intentionally not
reported.

## 3. Repository-state inventory

The generated inventory excludes VCS/build/cache directories and its own
`DOCS/baselines/` output path. The archived reference tree is measured
separately to avoid treating reference code as active PRIN code.

| Metric | Value |
|---|---:|
| Active files | 323 |
| Active text lines | 18,176 |
| Active bytes | 901,665 |
| Rust workspace members | 8 |
| Active Python package modules | 6 |
| Pytest files | 2 |
| CI workflow files | 6 |
| Numbered session briefs | 198 |
| Archived files | 451 |
| Archived PRINet Python modules | 43 |
| Archived PRINet Python lines | 25,530 |

The active tree contains only scaffold implementations. Rust crate tests report
zero unit tests because numerical work begins in later WPs. Python contains the
pre-launch scaffold smoke test and the WP-001 automation suite.

## 4. PRINet 3.0 API traceability

| Metric | Value |
|---|---:|
| Archived modules assigned to future WPs | 43 / 43 |
| Module-symbol rows assigned to future WPs | 657 / 657 |
| Canonical top-level `prinet.__all__` symbols | 172 / 172 |
| Symbols in archived `FROZEN_PUBLIC_API` | 98 |
| Later top-level exports absent from frozen set | 74 |
| Unresolved static re-exports | 0 |
| Unowned modules or symbols | 0 |

Ownership spans approved implementation WPs `WP-006` through `WP-036`.
Module-level defaults follow the numbered S1 briefs. Explicit symbol overrides
handle legacy mixed-purpose modules such as hierarchical networks, fused
kernels, OscilloSim, and `y4q1_tools`.

The archived frozen API set is a strict 98-symbol subset of the 172-symbol
canonical top-level export list. No frozen symbol is missing, but 74 later
exports were never added to the frozen set. This is recorded below for WP-036
and is not corrected in the read-only archive.

## 5. Automation and test evidence

Initial characterization test state:

```text
pytest tests/test_wp001_baseline.py -q
ERROR: ModuleNotFoundError: No module named 'tools'
```

Final focused evidence:

```text
37 passed
Changed-code coverage: 95.03% (503 statements, 25 missed)
```

The tests cover:

- metadata drift in version, license, repository, Python support, Maturin/PyO3,
  Rust toolchain, workspace inheritance, and required workflows;
- all 198 register rows, numbered briefs, statuses, metadata, and ordered links;
- static API discovery without archived imports;
- deterministic output and complete ownership;
- malformed/dynamic `__all__`, wildcard imports, cycles, missing re-exports,
  stale frozen API, malformed ownership JSON, invalid WPs, and unknown entries;
- CLI success/failure behavior and generated Markdown/JSON hygiene.

`python tools/wp001_baseline.py check` exits zero on the measured scaffold.

## 6. Mandatory local gate

All Coding Standards local-gate commands passed on the completed S1 tree.

| Command | Result | Evidence summary |
|---|---|---|
| `cargo fmt --all -- --check` | PASS | Exit 0 |
| `cargo clippy --workspace --all-targets -- -D warnings` | PASS | Exit 0 |
| `cargo test --workspace` | PASS | All crate/doc tests pass; zero Rust tests defined |
| `cargo test --workspace --features strict-checks` | PASS | Exit 0 |
| `RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps` | PASS | Eight crate docs generated |
| `ruff check python tests benchmarks tools` | PASS | No findings |
| `ruff format --check python tests benchmarks tools` | PASS | 12 files formatted |
| `mypy python/prin --strict` | PASS | Seven source files clean |
| `interrogate -c pyproject.toml python/prin` | PASS | 100.0% |
| `bandit -r python/prin -c pyproject.toml` | PASS | Zero findings |
| `bandit -r tools -c pyproject.toml` | PASS | Zero findings in S1 tooling |
| `pytest tests -v -m "not slow and not gpu"` | PASS | 38 passed |

The local Interrogate launcher had user-site module shadowing; the unchanged
command was run with a process-local import-path precedence correction. No
repository setting was weakened.

Parity, property-numerics, gradcheck, and kernel-equivalence tests are not
applicable: S1 introduced no numerical primitive, bridge, gradient, or kernel.

## 7. Security baseline

| Measurement | Result | Evidence |
|---|---|---|
| Ruff security rules | PASS | Included in full Ruff rule set |
| Bandit, shipped Python | PASS | Zero low/medium/high findings |
| Bandit, repository tools | PASS | Zero low/medium/high findings |
| Targeted credential-pattern sweep | PASS | No credential-like matches in S1 files |
| `pip-audit .` | PASS | No known vulnerabilities |
| `pip-audit -r DOCS/sphinx/requirements.txt` | PASS | No known vulnerabilities |
| `cargo audit` | **FAIL** | Two advisories in `pyo3 0.22.6` |

RustSec results:

| Advisory | Description | Fixed version |
|---|---|---|
| `RUSTSEC-2025-0020` | `PyString::from_object` buffer-overflow risk | `pyo3 >=0.24.1` |
| `RUSTSEC-2026-0177` | Missing `Sync` bound on closure API | `pyo3 >=0.29.0` |

Both advisories have fixes. They are baseline gap candidates for S2
classification and likely WP-001 S3 action; the bridge-domain follow-through is
owned by WP-003. S1 does not silently perform an unplanned PyO3 migration.

GitHub secret-scanning/push-protection settings and hosted alerts cannot be
verified from the local checkout. S2 must verify those external controls.

## 8. CI baseline

All six workflow files parse as YAML. Local execution cannot prove hosted-job
status, permissions, branch protection, runner labels, or repository secrets.

| Workflow | Baseline observation |
|---|---|
| `rust.yml` | fmt, clippy, test, rustdoc, and Cargo Audit jobs declared |
| `python.yml` | lint/test matrix declared for Python 3.11–3.13 on Linux/Windows |
| `parity.yml` | Empty corpus safely skips the differential job |
| `gpu.yml` | Opt-in self-hosted GPU job declared; not run in WP-001 |
| `repro.yml` | Active job calls an intentionally unimplemented Phase 6 script |
| `release.yml` | Wheel/sdist matrix declared; crates.io publication uses a token |

Direct repro characterization:

```text
python tools/reproduce.py --verify-manifest
NotImplementedError: The reproduction pipeline is ported in Phase 6
```

Python security CI currently audits only Sphinx requirements and appends
`|| true`, so vulnerability results cannot fail the job. This contradicts the
normative security gate even though both local Pip Audit measurements are clean.

## 9. Packaging baseline

| Measurement | Result | Evidence |
|---|---|---|
| Locked Maturin wheel build | PASS | `prin-0.1.0-cp311-abi3-win_amd64.whl`, 102,457 bytes |
| Maturin sdist build | PASS | `prin-0.1.0.tar.gz`, 22,692 bytes |
| Extracted-wheel import smoke | PASS | Python/package/core versions all `0.1.0` |
| Offline Cargo workspace package | **FAIL** | Internal path dependency has no version |
| Cross-platform wheel smoke | NOT RUN | Requires hosted Linux/macOS runners |

`cargo package --workspace --allow-dirty --no-verify --offline` packages the
first crates, then rejects `prin-kernels` because `prin-dynamics` is path-only
and has no crates.io version requirement. The release workflow's crate publish
loop is therefore not currently viable. Packaging ownership lies with WP-005
for the Phase 0 matrix and WP-038 for RC1 publication.

## 10. Documentation/governance baseline

Governance validation passes:

- exactly 198 register rows and 198 numbered briefs;
- unique, gap-free global sequence `0001` through `0198`;
- every register target exists;
- brief/register unit, type, and status metadata agree;
- every predecessor/successor link is ordered and resolves;
- bootstrap session 0001 and terminal session 0198 are correctly bounded.

A wheel-backed Sphinx build resolves every PRIN autodoc import, then fails the
warning-as-error gate on two documentation warnings:

1. `DOCS/sphinx/README.md` is not included in a toctree.
2. The Torch intersphinx inventory redirects to its current canonical URL.

These are documentation gap candidates for S4/WP-037, not numerical or API
implementation work.

## 11. Baseline gap candidates for S2 classification

S1 records observations but does not assign audit finding IDs or severities.
Session 0002 must independently reproduce and classify them.

| Candidate | Evidence-backed gap | Likely owner/disposition |
|---|---|---|
| BG-001 | Cargo Audit reports two fixed PyO3 advisories | S2 classify; likely immediate S3, domain WP-003 |
| BG-002 | Python security CI suppresses Pip Audit failures and audits docs only | S2 classify; likely S3/Phase 0 CI |
| BG-003 | Repro CI invokes the Phase 6 placeholder and fails on `tools/**` changes | S2 classify; guard/remedy in S3 or WP-035 |
| BG-004 | Cargo workspace crates cannot be packaged due path-only internal deps | WP-005/WP-038 packaging |
| BG-005 | Warning-as-error Sphinx build has two warnings | S4/WP-037 |
| BG-006 | Frozen API has 98 entries while canonical `__all__` has 172 | WP-036 API freeze/migration |
| BG-007 | PRINet acceptance suite is not yet ported; Rust crates have no tests | Incremental numerical WPs; completion WP-036 |
| BG-008 | Golden parity corpus is absent; guarded workflow skips | WP-002 |
| BG-009 | Controller model and SHA-256 manifest are absent | WP-028/WP-035 |
| BG-010 | Benchmarks, notebooks, and paper remain README-only placeholders | WP-033/WP-037 |
| BG-011 | Hosted CI, branch protection, and secret scanning are locally unverified | S2 external verification |

## 12. Scope confirmation

`git diff` contains no changes under `crates/`, `python/prin/`, `parity/`,
`benchmarks/`, `models/`, or the archived reference tree. WP-001 adds only
static repository tooling, tandem tests, generated inventories, and S1 evidence.
No numerical implementation, performance experiment, or golden data was
introduced.
