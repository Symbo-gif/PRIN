Pre-registration freeze: **`5d5ae3521317af47a11afa8d689935ac2fc0f447`** — the git SHA of the last `preregistration.md` edit. `F` is recorded here on line 1 at the creation of the first `RUN-` directory (campaign plan §12.4); the preregistration is frozen from this point.

# EXP-001-r1 — E3 execution log

**Operator:** Devin (AI pair), acting on MichaelMaillet's instructions.
**Session:** EXP-001-r1-E3.
**Branch:** `campaign/exp001-r1-preexecution`.

## Recorded identities

- **`F` (last pre-registration edit, frozen at first `RUN-`):** `5d5ae3521317af47a11afa8d689935ac2fc0f447`
- **`M` (merged-main baseline carrying DV-043):** `9b79d2e5b246bead1243074659dc99d049762a40` — PR #26 merged 2026-09-29T05:15:36Z; forced nightly `36525353031` attempt 2 `bench-regression` PASSED (63 gated benchmarks within +10%).
- **`R` (single execution checkout for all six runs):** `5d5ae3521317af47a11afa8d689935ac2fc0f447` — clean, committed `campaign/exp001-r1-preexecution` head incorporating `M`, the r1 driver, the approved H4 two-build method and the DV-044 correction. `F` and `R` coincidentally name the same commit; their roles remain distinct.

## Entry evidence

- `tools/check_ci_green.py 9b79d2e5b246bead1243074659dc99d049762a40` → `RESULT: all required workflows green` (rust `36525333009`, python `36525332993`, parity `36525333011`, repro `36525333000`, snyk `36525333001`, gpu `36531307306`). Verified 2026-09-29 UTC immediately before E3.
- DV-041, DV-043, DV-044 recorded **CLOSED** in `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`.
- E2 approval of the H4 two-build method and wgpu leg recorded in `preregistration.md` (2026-09-29 UTC).
- Independent non-author M/R/F delta audit: PASS-WITH-FINDINGS; its single finding (stale gate-status text) remediated in `5d5ae35`.
- Tracked-source status at first `RUN-` creation: clean (`git status --porcelain` empty) at `5d5ae35`.

## Extension build record — leg 1 (wgpu)

- **Build command:** `.venv\Scripts\python.exe -m maturin develop -m crates/prin-py/Cargo.toml --features wgpu` (via the shared `C:\dev\PRIN\.venv`; `VIRTUAL_ENV` set; no tracked source change between build and run).
- **Imported `prin.__file__`:** `C:\dev\PRIN-r1-amendment\python\prin\__init__.py` (execution checkout `R`, enforced via `PYTHONPATH`).
- **Imported `prin._prin_core.__file__`:** `C:\dev\PRIN-r1-amendment\python\prin\_prin_core.pyd`
- **Extension SHA-256:** `2f902e806a3cab860f3fbdf9b4e7ad7d4928329df63aaf46df4010ed430e748b`
- **Backend probe (fresh process):** `tests/_env.py::wgpu_kernel_executes()` → `True` — a live wgpu kernel dispatch was observed, not merely a compiled module.

## Runs (execution order)

| # | UTC | Command (mode / label) | Directory | Result |
|---|---|---|---|---|
| 1 | 2026-09-29T09:17:35Z | `kernel-path` / `r1-kernel-path-wgpu` (wgpu build) | `RUN-20260929T091735Z-5d5ae35-r1-kernel-path-wgpu` | completed — 72 cases, `environment.backend="wgpu"`, per-case `backend_name="wgpu<wgsl>"`, `dlpack_devices` retained on all three output capsules, `git_commit=5d5ae35…`; manifest verified |

## Extension build record — leg 2 (cuda)

- **Build command:** `.venv\Scripts\python.exe -m maturin develop -m crates/prin-py/Cargo.toml --features cuda` (same `R` checkout; dev-profile build finished in 3m 12s; no tracked source change).
- **Imported `prin.__file__`:** `C:\dev\PRIN-r1-amendment\python\prin\__init__.py`
- **Imported `prin._prin_core.__file__`:** `C:\dev\PRIN-r1-amendment\python\prin\_prin_core.pyd`
- **Extension SHA-256:** `701bb529965a6916a71a5f5350e286428346e81f541a0c46f6e509b2008753c2` — distinct from the wgpu hash, as designed; the git source SHA is identical (`5d5ae35…`).
- **Backend probe (fresh process):** `tests/_env.py::cuda_kernel_executes()` → `True`.

## Runs 2–6 (under the cuda build, in registered order)

| # | UTC | Command (mode / label) | Directory | Result |
|---|---|---|---|---|
| 2 | 2026-09-29T09:26:19Z | `corpus` / `r1-corpus-cpu` | `RUN-20260929T092619Z-5d5ae35-r1-corpus-cpu` | completed — 504 cases, `backend="cpu"`; manifest verified |
| 3 | 2026-09-29T09:26:26Z | `repeatability` / `r1-repeatability-cpu` | `RUN-20260929T092626Z-5d5ae35-r1-repeatability-cpu` | completed — 14 cases; manifest verified |
| 4 | 2026-09-29T09:26:31Z | `repeatability` / `r1-seedrep0-cpu` | `RUN-20260929T092631Z-5d5ae35-r1-seedrep0-cpu` | completed — 14 cases; manifest verified |
| 5 | 2026-09-29T09:26:41Z | `fuzz` / `r1-fuzz-cpu` | `RUN-20260929T092641Z-5d5ae35-r1-fuzz-cpu` | completed — 1,000 draws; manifest verified |
| 6 | 2026-09-29T09:30:35Z | `kernel-path` / `r1-kernel-path-cuda` (cuda build) | `RUN-20260929T093035Z-5d5ae35-r1-kernel-path-cuda` | completed — 72 cases, `environment.backend="cuda"`, all three output capsules `kDLCUDA`; manifest verified |

All six invocations finished at 2026-09-29T09:30:39Z with `Wrote and manifested` — the driver's closure check for `EXP-001-r1`, `append_manifest` and `verify_manifest` passed on every directory. Every record carries `git_commit=5d5ae3521317af47a11afa8d689935ac2fc0f447` (`R`); GPU metadata declares `timing_method="not-timed"` and tags `H4`. No aborts, no retries, no reused directories.

## Protocol-deviation disclosure

Source changes since the predecessor EXP-001 E2 baseline, all landed through governed corrections **before** `R` and recorded here per campaign rule:

- DV-043 redundant-step guard (merged to `main` as `9b79d2e` = `M`, incorporated into `R`).
- DV-041 wgpu backend identification (`backend_name`); closed through PR #25.
- D1 correction for EXP-001 (its own S1–S4 record).
- DV-044 cumulative ledger/parser hardening (S1–S4 on `hotfix/dv044-ledger-delta`, merged to the campaign branch).
- The r1 driver and preregistration amendments themselves (`campaign/exp001-r1-preexecution`), reviewed at E2 and approved by the maintainer.

## Post-execution notes

- No hypothesis verdict, metric adjudication or statistical test was computed during E3; that is E4's role. Case-level `within_tolerance` fields exist in the artefacts but are unadjudicated raw comparisons.
- The two extension SHA-256 values intentionally differ (separate feature builds); the git source SHA is identical for all six runs.
- Tracked source remained clean throughout E3; the six `RUN-` directories and this log are the only added artefacts.
- Historical predecessor `RUN-2026…-6b9d6b6-*` directories are retained untouched.
