# 0144W — WP-036F S3 remediation gate evidence

**Session:** `0144W` (WP-036F S3 — Remediation)
**Date:** 2026-09-02
**Predecessor audit:** `DOCS/audits/036f-wp036f-audit.md` (verdict
`PASS-WITH-FINDINGS`; findings `WP036F-F1` D2, `WP036F-F2` D4)
**Fix commits:** `a9ad913` (WP036F-F1), `70781ca` (WP036F-F2)
**Git state:** `main` local, not pushed (amendment #28 — the WP-036F
`0144U`–`0144X` range pushes once at S4 `0144X`).

---

## WP036F-F1 (D2) — changed-code coverage

Baseline reproduced (pre-fix, `b90c1ff`):

```
pytest tests/test_wp036f_reexport.py \
  --cov=tools.wp036f_reexport_controller \
  --cov=tools.wp036f_provider_latency --cov-report=term-missing
  tools/wp036f_provider_latency.py       79   2   97%   99, 191
  tools/wp036f_reexport_controller.py   131  11   92%   71-72, 121-122, 174,
                                                        184-185, 188, 201-202, 206
  TOTAL                                 210  13   94%      (21 passed)
```

Nine tests added to `tests/test_wp036f_reexport.py` (`a9ad913`):

| Test | Branch closed |
|---|---|
| `TestTransformErrorPaths::test_transform_rejects_a_non_rank2_weight` | `_gemm_out_features` non-rank-2 weight `ValueError` (reexport 71-72) |
| `TestTransformErrorPaths::test_transform_rejects_a_colliding_bias_name` | bias-name collision `ValueError` (reexport 121-122) |
| `TestCheckDriftBranches::test_check_reports_no_gemm_nodes` | `_check` "no Gemm nodes" (reexport 174) |
| `TestCheckDriftBranches::test_check_reports_a_non_initializer_bias` | `_check` bias input is not an inline initializer (reexport 184-185) |
| `TestCheckDriftBranches::test_check_reports_a_non_zero_bias` | `_check` bias not `float32` zero (reexport 188) |
| `TestCheckDriftBranches::test_check_reports_a_manifest_missing_file` | `_check` manifest names a missing file (reexport 201-202) |
| `TestCheckDriftBranches::test_check_reports_a_stale_manifest_digest` | `_check` manifest size correct, `sha256` stale (reexport 206) |
| `TestProviderLatencyToolEdgeCases::test_pre_transform_check_handles_an_absent_archive` | `_pre_transform_check` archive absent (latency 99) |
| `TestProviderLatencyToolEdgeCases::test_main_returns_zero_when_directml_unregistered` | `main` DirectML not registered (latency 191) |

Post-fix scoped re-measure:

```
pytest tests/test_wp036f_reexport.py \
  --cov=tools.wp036f_reexport_controller \
  --cov=tools.wp036f_provider_latency --cov-report=term-missing
  tools/wp036f_provider_latency.py       81   0   100%
  tools/wp036f_reexport_controller.py   132   0   100%
  TOTAL                                 213   0   100%      (30 passed)
```

No residual defensive/unreachable line remains to document — every
previously-uncovered line is now exercised. ≥95% gate: **met (100%)**.

## WP036F-F2 (D4) — mypy --strict nits

Baseline (pre-fix): `mypy --strict tools/wp036f_reexport_controller.py
tools/wp036f_provider_latency.py` → 3 errors
(`unused-ignore` + `call-overload` at `reexport:148`; `arg-type` at
`latency:131`).

Fix (`70781ca`): `cast("list[dict[str, object]]", manifest["files"])` at
`reexport` `_write_manifest`; `_RTOL` / `_ATOL` constants passed explicitly to
`np.allclose` at `latency` `build_report` (`_TOL` retained for the evidence
JSON as `{"rtol": _RTOL, "atol": _ATOL}`). Run-time behaviour byte-identical.

Post-fix: `mypy --strict` on both tools → **`Success: no issues found in 2
source files`**. Resolution: **FIXED** (not carried).

---

## Delta re-audit — touched-area gate re-run (2026-09-02, `main` @ `70781ca`)

| Gate | Result |
|---|---|
| `pytest tests/test_wp036f_reexport.py tests/test_daemon_controller.py parity/test_parity_subconscious.py` | 135 passed, 1 skipped |
| scoped `--cov` (both tools) | 100% / 100% / TOTAL 100%, 30 passed |
| `pytest -m "not slow and not gpu" -p no:cov` | 2774 passed, 202 skipped, 30 deselected (was 2765 at S2; +9) |
| `python tools/wp036f_reexport_controller.py --check` | `OK: 3 Gemm nodes, all three-input; manifest current` |
| `cargo test -p prin-daemon` | lib 163 + doc + `integration_controller_model` 7 + `parity_subconscious` 8, 0 failed |
| `cargo fmt --all -- --check` | clean |
| `cargo clippy --workspace --all-targets -- -D warnings` | clean |
| `ruff check` / `ruff format --check` (`tests/`, `tools/`) | clean / formatted |
| `mypy python/prin --strict` | Success, 62 files |
| `mypy --strict` (both new tools) | Success, 2 files |
| `interrogate -c pyproject.toml python/prin` | 97.6% PASS |
| `bandit -c pyproject.toml` (both tools + test file) | 0 issues (all confidences) |
| `cargo audit` | exit 0 — 3 governed warnings (`paste` RUSTSEC-2024-0436, `bincode` RUSTSEC-2025-0141, `chacha20` yanked); no `Cargo.toml`/`Cargo.lock` change |
| `pip-audit .` | No known vulnerabilities found |
| `snyk code test` (both tools + test file, `--severity-threshold=low`) | 0 issues |

`git diff b7d3ee7..70781ca` touches no `Cargo.toml` / `Cargo.lock` /
`pyproject.toml` / requirements file — Snyk Open Source not triggered; the
DV-008 / DV-017 `cargo audit` governance is untouched.

**Result: CLEAN.** Both findings `FIXED`; no new finding.
