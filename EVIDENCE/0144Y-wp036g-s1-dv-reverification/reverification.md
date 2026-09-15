# WP-036G S1 consolidated deferred-validation re-verification

**Session:** 0144Y  
**Date:** 2026-09-15  
**Host:** Windows 11, Python 3.14.0, Rust 1.92.0

## External controls

| Control | Result |
|---|---|
| `gh api repos/Symbo-gif/PRIN/actions/runners` | One runner: `PRIN-GPU-Runner`, Windows, labels `[self-hosted, Windows, X64, gpu]`, `status: online` (busy during the query). No Linux-labelled runner exists. |
| `gh api repos/Symbo-gif/PRIN/secret-scanning/alerts` | HTTP 404: `Secret scanning is disabled on this repository.` Amendment #5's Gitleaks + branch-protection substitute therefore remains in force. |
| `.snyk` policy currency | The six torch advisory entries expire 2026-11-14; the three audit-tool entries expire 2026-11-06. The high advisory's rationale was corrected for two later ordinary `torch.load(..., weights_only=True)` `.pt` cache call sites; `torch.export.load` / `.pt2` remain absent. Scope, expiry, and approval are unchanged; no finding was newly suppressed. |
| Snyk Open Source MCP, repository, `all_projects=true`, severity `low`, venv Python | 0 issues. |
| `pip-audit .` | No known vulnerabilities found. |
| `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities found. |

## Rust advisory pass

The first `cargo audit` refresh found actionable RUSTSEC-2026-0285 in locked
`rustls` 0.23.43 (medium, fixed in 0.23.45) and returned exit 1. S1 work paused.
`cargo update -p rustls@0.23.43 --precise 0.23.45` updated `rustls` to 0.23.45
and `rustls-webpki` to 0.103.15. The post-update scan returned exit 0 with only:

- `paste` 1.0.15, RUSTSEC-2024-0436, unmaintained — DV-008;
- `bincode` 2.0.1, RUSTSEC-2025-0141, unmaintained — DV-017;
- `chacha20` 0.10.1, yanked — newly registered as DV-035.

No vulnerability remains. Snyk Open Source was re-run after the lock update and
reported zero issues.

## Test-fragility verification

| Item | Method | Result |
|---|---|---|
| DV-019 Python sub-item | Ten separate invocations of `test_process_frame_gradcheck_with_prev_slots` under the existing autouse `torch.manual_seed(0)` guard | 10/10 passed. The prior Python recurrence is the ETCA-001 global-Torch-RNG/order-dependent fixture issue, not Burn's process-global `AutodiffServer`; no serialization lock is applicable. |
| `test_no_gpu_throughput_regression` | Fixed 1,000,000-iteration work; warm-up in each phase; seven baseline samples bracketing seven daemon-active samples; relative median; original `<1.30` limit retained | Three consecutive isolated invocations passed, and both the fast and full suites passed with the quarantine removed. |

## Consolidated gates

| Gate | Result |
|---|---|
| `tools/check_dv_register_gates.py` | Passed; 35 DV rows checked against 198 session entries. |
| `tools/check_no_python_numerics.py` | Clean; 19 compatibility modules. |
| `tools/wp001_baseline.py check` | Passed. |
| `verify_api_surface(prin.__all__)` | `(set(), set())`. |
| Snyk Code: `tests/test_acceptance_subconscious.py` | 0 issues at low threshold. |
| Snyk Code: `tests/conftest.py` | 0 issues at low threshold. |
| Snyk Code: `tests/test_wp001_baseline.py` | 0 issues at low threshold. |
| Snyk Code: `.github/workflows/gpu-triton.yml` | Unsupported file type (`SNYK-CODE-0006`); YAML syntax was parsed locally. No claim of a passed Snyk Code scan is made for this workflow. |
| Ruff check / format | Passed; 248 files formatted. |
| mypy `python/prin --strict` | 62 files, 0 issues. |
| interrogate | 97.6%, passed. |
| Bandit | 0 issues. |
| Python fast suite | 2775 passed, 201 skipped, 30 deselected; 95% coverage. |
| Python full suite + parity, governed `.pytest_basetemp` | 3395 passed, 203 skipped; 95% coverage. |
| Cargo fmt / clippy / workspace tests / rustdoc | Passed. |

## Transparent out-of-scope observation

The AGENTS.md full-suite spelling `--basetemp=.pytest_basetemp-full` produced 11
`test_acceptance_y4q2.py` path-policy failures because
`allowed_output_roots()` permits the in-repo `.pytest_basetemp` path but not the
suffixed sibling. Re-running the identical 3,598-test suite with the governed
`.pytest_basetemp` root passed 3,395/3,395 non-skipped tests. This is a
pre-existing verification-command/path-policy mismatch, not attributable to
WP-036G's register or test changes; it is passed to S2 for classification rather
than changed outside S1 scope.
