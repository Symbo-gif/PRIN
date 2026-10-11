# EA-007 full local verification gate — status index

Host: HP (Windows) | Base SHA: `fdd28d88e4c57d544e5d30fa52cce85807ab15a9`
| Branch: `audit/ea007-exp002-readiness` | Plan amendment #48 regime:
local validation authoritative; hosted CI paused (not satisfied).
All commands serial; logs embed verbatim command/host/SHA/UTC/exit code.

## Completed legs

| # | Check | Log | Result |
|---|-------|-----|--------|
| 00 | Environment / tool versions / backend build facts | `00-environment.log` | recorded (cuda_kernel_executes=True, wgpu_kernel_executes=False, directml_executes=True — build facts only, not full backend verification) |
| 01 | `ruff check python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/` | `01-ruff-check.log` | PASS (exit 0) |
| 02 | `ruff format --check` normal roots | `02-ruff-format-normal.log` | PASS — 322 files (exit 0) |
| 03 | `ruff format --check DOCS/experiments/ --config include=[*.py,*.pyi,*.ipynb]` | `03-ruff-format-campaign.log` | PASS — 2 files (exit 0) |
| 04 | `mypy python/prin --strict` | `04-mypy-prin.log` | PASS — 62 source files (exit 0) |
| 05 | `mypy DOCS/experiments/ --strict` | `05-mypy-campaign.log` | PASS — 2 source files (exit 0) |
| 06 | `interrogate -c pyproject.toml python/prin` | `06-interrogate.log` | PASS — 97.6% ≥ 95.0% (exit 0) |
| 07 | `bandit -r python/prin DOCS/experiments -c pyproject.toml` | `07-bandit.log` | PASS — non-vacuous, 0 issues (exit 0) |
| 09 | `cargo fmt --all -- --check` | `09-cargo-fmt.log` | PASS (exit 0) |
| 10a | `cargo clippy --workspace --all-targets -- -D warnings` | `10a-clippy.log` | PASS (exit 0) |
| 10b | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | `10b-clippy-strict.log` | PASS (exit 0) |
| 11a | `cargo test --workspace` | `11a-cargo-test-workspace.log` | PASS — all suites green (exit 0) |
| 11b | `cargo test --workspace --features strict-checks` | `11b-cargo-test-strict.log` | PASS (exit 0) |
| 11c | `cargo test --workspace --features cuda -- --test-threads=1` | `11c-cargo-test-cuda.log` | PASS (exit 0) |
| 11d | `cargo test --workspace --features wgpu -- --test-threads=1` | `11d-cargo-test-wgpu.log` | PASS (exit 0) |
| 11e | `cargo test -p prin-kernels --features cpu` | `11e-cargo-test-kernels-cpu.log` | PASS (exit 0) |
| 11f | `cargo test -p prin-sim --features cpu -- --test-threads=1` | `11f-cargo-test-sim-cpu.log` | PASS (exit 0) |
| 12a | `cargo llvm-cov -p prin-kernels --features wgpu,cpu` | `12a-llvm-cov-kernels.log` | DONE — TOTAL 87.30% regions / 87.18% lines (exit 0) |
| 12b | `cargo llvm-cov -p prin-dynamics` | `12b-llvm-cov-dynamics.log` | DONE — TOTAL 64.48% regions / 63.59% lines (exit 0) |
| 12c | `cargo llvm-cov -p prin-dynamics --features strict-checks` | `12c-llvm-cov-dynamics-strict.log` | DONE — TOTAL 64.59% regions / 63.67% lines (exit 0) |
| 13a | `cargo audit` | `13a-cargo-audit.log` | PASS (exit 0) — 3 allowed warnings (`bincode` unmaintained RUSTSEC-2025-0141, `paste` unmaintained RUSTSEC-2024-0436, `chacha20` yanked); no vulnerabilities |
| 13b | `pip_audit .` | `13b-pip-audit-repo.log` | PASS — no known vulnerabilities (exit 0) |
| 13c | `pip_audit -r DOCS/sphinx/requirements.txt` | `13c-pip-audit-sphinx.log` | PASS — no known vulnerabilities (exit 0; PyPA DB clean at time of run) |
| 13d | Snyk SCA `all_projects`, severity low | `13d-snyk-sca.log` | **FINDING (EA007-E-F4, D2):** urllib3 2.7.0 three CVEs (2 high/1 med, fixedIn 2.8.0) in `DOCS/sphinx/requirements.txt` + foreign `.kilo`/`.qwen` worktree copies; zod CVE in `.kilo/package.json` (non-repo manifest). Snyk Code `gpu.rs`: 0 issues → **remediated, see 13e–13h** |
| 13e | `pip install urllib3>=2.8.0` (venv) | `13e-urllib3-upgrade.log` | DONE — urllib3 2.7.0 → 2.8.0, no other packages touched; requirements.txt floor raised to `>=2.8.0` |
| 13f | `pip_audit -r DOCS/sphinx/requirements.txt` (rescan) | `13f-pip-audit-sphinx-post.log` | PASS — no known vulnerabilities (exit 0) |
| 13g | `pip_audit .` (rescan) | `13g-pip-audit-repo-post.log` | PASS — no known vulnerabilities (exit 0) |
| 13h | Snyk SCA scoped file rescan (`all_projects=false`, file=`DOCS/sphinx/requirements.txt`, severity low) | `13h-snyk-sca-rescan.log` | PASS — **issueCount=0**; E-F4 FIXED at repository-manifest scope (repo-wide scan still sees foreign `.kilo`/`.qwen` copies — out of repo scope, no exclusions added) |
| 14 | Gitleaks provisioning (pinned v8.30.1, SHA-256 verified, session-local) | `14-gitleaks-install.log` | installed; official checksum match |
| 15 | `gitleaks git C:/dev/PRIN --redact` full history | `15-gitleaks-scan.log`, `gitleaks-redacted.json` | PASS — 704 commits / 72.4 MB scanned, **no leaks found** (exit 0; report `[]`) |
| 16 | `tools/wp001_baseline.py check` | `16-wp001-baseline.log` | PASS (exit 0) |
| 17 | `check_global_session_registration.py` | `17-global-session-registration.log` | PASS — 18 EA reports incl. EA-007 (exit 0) |
| 18 | `check_dv_register_gates.py` | `18-dv-register-gates.log` | PASS — 44 rows / 198 entries (exit 0) |
| 19 | `check_deviation_ledger.py 039 → 040` | `19-deviation-ledger-039-040.log` | PASS — 142 → 146 rows after E-F4 append (exit 0) |
| 20 | Sphinx clean build `-W --keep-going` to fresh `sphinx-html/` | `20-sphinx.log` | PASS — build succeeded, 0 warnings (exit 0) |
| 21 | Focused `pytest tests/test_campaign_quality_gates.py` + ruff (post-E-F4, strict 3-part version regex) | `21-focused-tests-post-ef4.log` | PASS — 19/19 (exit 0); Snyk Code on test file: 0 issues |
| 22 | `uv pip compile pyproject.toml --extra dev` → resolved manifest | `22-uv-compile.log`, `prin-requirements.txt` | DONE — 274 pins (exit 0); direct Snyk scans of the file failed SNYK-OS-PYTHON-0013 (env/pin mismatch) |
| 22c | Session-local audit venv at resolved pins | `22c-audit-env-install.log` | DONE — governed resolved-input env (`.audit-venv`, mirrors CI "Install Snyk audit environments"; `.venv` untouched) |
| 22d | `snyk test --file=prin-resolved/requirements.txt --package-manager=pip --severity-threshold=low` (CLI 1.1304.2, governed workflow form) | `22d-snyk-sca-mainmanifest.log` | **FINDINGS (exit 1) — torch@2.14.1, all "no upgrade or patch available":** SNYK-PYTHON-TORCH-10332643 (MED), 10337825 (MED), 10337826 (MED), 10337834 (MED), 15746467 (HIGH, deserialization). **Pre-existing platform exposure — NOT attributable to this diff** (torch pin unchanged; PyPA DB does not carry these, consistent with clean pip_audit). Reported for lead judgment; no suppressions |
| 22e | `snyk test --file=prin-resolved/requirements.txt --package-manager=pip --severity-threshold=low --fail-on=all --policy-path=.snyk` (exact CI form, resolved audit env) | `22e-snyk-sca-mainmanifest-exact.log` | **PASS — 100 dependencies, no vulnerable paths found (exit 0).** Local policy found; the five torch advisories of 22d are the pre-existing EA003-E-F7 governed dispositions (expires 2026-11-14). No new ignore added |
| 23 | 3-node isolated pytest diagnostic `-o faulthandler_timeout=120 --durations=3` (timeout 600) | `23-pytest-diagnostic.log` | **ALL 3 PASSED.** inventory test 66.51s, latency benchmark 39.34s (5 rounds), gradcheck 0.67s. Total 108.9s — inherent node hang NOT reproduced; imposed 30-min bounds simply exhausted |
| 24 | `RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps` | `24-rustdoc-workspace.log` | PASS (exit 0) |

Prior focused evidence (earlier in session, parent dir `ea007/`):
DV-042 rustdoc legs (`dv042-*.log`: wgpu pre-fix exit 101 → wgpu/cpu/cuda
exit 0), DV-040 probes and regression-test proof (`dv040-*.log`), offline
governance checks 038→039 (`ea007-check-*.log`), Snyk Code
(`dv040-snyk-code.log`).

## Blocked legs (timeouts — mechanism unproven)

| # | Check | Log | State |
|---|-------|-----|-------|
| 08 | `pytest tests/ parity/ --cov=prin --cov-report=term-missing` (timeout 1800s) | `08-pytest-full-cov.log` | **TIMEOUT at 60% — EXIT_CODE=124**; last node `test_wp001_baseline.py::test_repository_inventory_is_deterministic_and_separates_archive` mid-run; all executed tests PASSED, zero FAILED/ERROR. Coverage leg = **BLOCKED** (DV-033 is a Python per-change coverage gap; not scoped to cargo llvm-cov). Timeout mechanism unproven — location ≠ cause |
| 08b | `pytest tests/ parity/ --basetemp=.pytest_basetemp` — full suite, NO coverage, isolated retry (timeout 1800s) | `08b-pytest-full-nocov.log` | **TIMEOUT at 58% — EXIT_CODE=124**; last node `test_train_bridge.py::TestTrainBridgeBenchmarks::test_resonance_layer_forward_backward_round_trip_latency_moderate` mid-run; 3,238 PASSED / 0 FAILED before kill. Original run's process tree verified fully exited before retry |

**Diagnosis (leg 23):** the imposed 30-minute bounds were **exhausted**,
not a hang — all three "last-node" suspects pass in isolation (inventory
66.5s + latency benchmark 39.3s are among the suite's slowest tests; the
kill landed mid-test both times). An inherent node hang was **not
reproduced**; a complete uninterrupted pass needs a larger bound, which
the lead has authorized exactly once (leg 25 below).

Notes: rustdoc legs already proved (`dv042-*.log`) — no rerun needed
(gpu.rs unchanged since). Focused gate tests: 19/19 pass incl. the
EA007-E-F4 urllib3 floor regression assertion.

## Final extended run (leg 25 — authorized once, completed)

| # | Check | Log | State |
|---|-------|-----|-------|
| 25 | `pytest tests/ parity/ --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20` — FINAL authorized uninterrupted run, no coverage, timeout 5400s | `25-pytest-final.log` | **PASS — 5,667 passed / 184 skipped / 0 failed / 61 warnings in 1,782.21s (29:42), exit 0.** One faulthandler dump at `test_ablation_oscillatory_bias` (>300s): stack shows genuine compute in `hierarchical_layers.py:387 integrate` via `hybrid_compat.py:565 forward`; test PASSED in 335.58s. Suite is bound by legitimately slow tests |

## Closure checks (leg 26 — post-issuance governance re-verification)

| # | Check | Log | Result |
|---|-------|-----|--------|
| 26a | `check_deviation_ledger.py 039→040` | `26a-ledger-039-040.log` | PASS — 142 → 146 rows (exit 0) |
| 26b | `check_dv_register_gates.py` | `26b-dv-register-gates.log` | PASS — 44 rows / 198 session entries (exit 0) |
| 26c | `check_global_session_registration.py` | `26c-global-registration.log` | PASS — 18 EA reports (exit 0) |
| 26d | `check_skipif_probes.py` | `26d-skipif-probes.log` | PASS — no registration-probe skipif guards (exit 0) |
| 26e | `wp001_baseline.py check` | `26e-wp001-baseline.log` | PASS (exit 0) |
| 26f | `git diff --check` | `26f-git-diff-check.log` | PASS — no whitespace errors (exit 0) |
| 26g | Closure environment snapshot (real OS + tool versions) | `26g-closure-env.log` | Windows-11-10.0.26300; Python 3.14.0; ruff 0.16.1; mypy 2.3.0; bandit 1.9.4; pytest 9.1.1; pip-audit 2.10.1; cargo/rustc 1.98.1; llvm-cov 0.8.7; cargo-audit 0.22.2 |
| 26h | Source-hash manifest binding verified files to the commit | `26h-source-hashes.txt` | SHA-256 of gpu.rs, gate test, python.yml, pyproject.toml, sphinx requirements, AGENTS.md |
