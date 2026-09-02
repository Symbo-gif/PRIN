---

# PRIN Project State Report — Cycle 036F

**Date:** 2026-09-02
**Cycle:** 036F (WP-036F "DirectML controller-graph execution")
**Completed sessions:** 0144U (S1), 0144V (S2), 0144W (S3), 0144X (S4)
**Author:** Claude Sonnet 5 (AI pair)
**Git state:** `main` @ S4 closure (local; the batched `0144U`–`0144X` push is
a maintainer action)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1. WP-036F is
  the second of the three amendment-#38 Deferred-Validation closure work
  packages (WP-036E → WP-036F → WP-036G); WP-036G (`0144Y`–`0144AB`) is the
  registered successor and the last before WP-037 (`0145`).
- **This cycle delivered:**
  - **Re-exported controller ONNX graph** (`0144U`):
    `models/subconscious_controller.onnx` re-exported with **three-input
    `Gemm` nodes** — an explicit zero-valued `float32` bias per layer
    (`net.0.bias` / `net.3.bias` / `net.6.bias`) — so ONNX Runtime's
    `DmlExecutionProvider` executes it (its `DmlFusedGemm` fusion rejects the
    two-input `Gemm` form PyTorch exported). `Y = α·A'·B' + 1·0` is exact in
    IEEE-754, so the graph function is unchanged: **bit-identical** to the
    pristine PRINet 3.0 graph on `CPUExecutionProvider` over the 48-case
    differential set (`max_abs_diff = 0.0`). `DmlExecutionProvider` executes
    the re-exported graph (active provider `DmlExecutionProvider`, not a CPU
    fallback) and agrees with CPU at `max_abs_diff_vs_cpu = 7.15e-7`, within
    Testing Standards §3's `rtol=1e-5, atol=1e-6`. Digest
    `3396bfdd…4102` → `d7d7935b…341a` (18,270 → 19,428 bytes);
    `subconscious_controller.onnx.data` unchanged (biases inline).
  - **New tooling** (`0144U`): `tools/wp036f_reexport_controller.py`
    (idempotent transform + `--check` verifier, refreshes
    `models/manifest.json`), `tools/wp036f_provider_latency.py` (writes the
    DV-006 "provider and latency acceptance" evidence
    `EVIDENCE/0144U-wp036f-s1-controller-provider-report.json`).
  - **Tests** (`0144U` + `0144W`): `tests/test_wp036f_reexport.py` (30 tests
    after the S3 remediation added nine error-path / drift-branch cases); a
    DirectML case in
    `tests/test_daemon_controller.py::TestCrossProviderAgreement`; the
    `crates/prin-daemon` integration-test digest constants updated.
  - **S2 audit** (`DOCS/audits/036f-wp036f-audit.md`): verdict
    **PASS-WITH-FINDINGS** (no D1). Independently reproduced the CPU
    bit-identity and DirectML agreement; confirmed scope (a graph-transform
    pass + tools + tests + docs — no controller algorithm, daemon runtime,
    backend-selection, DV-025, or `prin` public-API change). Two findings:
    WP036F-F1 (D2, changed-code coverage 94% < 95% on the two new tools),
    WP036F-F2 (D4, `mypy --strict` nits in the two new tools).
  - **S3 remediation** (`0144W`): both findings **FIXED**, no amendment.
    WP036F-F1 — nine targeted tests → scoped changed-code coverage 100% on
    both modules (commit `a9ad913`). WP036F-F2 — `cast("list[dict[str,
    object]]", …)` and explicit `rtol=`/`atol=` into `np.allclose`; `mypy
    --strict` on both tools 3 errors → 0 (commit `70781ca`). Delta re-audit
    **CLEAN** (`DOCS/audits/036f-wp036f-audit.md` §7; commit `2155e54`).
  - **S4 documentation** (`0144X`): READMEs refreshed (`tests/`, `models/`);
    `CHANGELOG.md` entries; Sphinx `api/daemon.rst` and `migration_guide.rst`
    document the re-exported graph and the provider-latency figures;
    `DOCS/sphinx/parity_report.rst` gains a "WP-036F — DirectML
    controller-graph execution" deviation-register entry;
    `DEFERRED_VALIDATION_REGISTER.md` — **DV-006 DirectML half CLOSED**, row
    re-scoped to the VitisAI/NPU hardware-gated remainder (OPEN); Project
    Plan amendment #13's WP-005 DirectML deferral marked **discharged**; this
    PSR issued.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendments #1–#44
  remain in force; no new amendment this cycle (both S2 findings FIXED in
  code).
- **Audit:** `DOCS/audits/036f-wp036f-audit.md` — S2 verdict
  PASS-WITH-FINDINGS; S3 both findings FIXED, delta re-audit CLEAN. No
  unresolved D1/D2 finding exists.
- **Session Register:** 0144U (S1), 0144V (S2), 0144W (S3), 0144X (S4) all
  marked COMPLETE; 0144Y (WP-036G S1) is the registered successor.
- **WP-036F is CLOSED.**

---

## 2. Metric trends

| Metric | Previous (PSR-036E) | Current (PSR-036F) | Gate |
|---|---|---|---|
| Rust tests passing (default) | 1540 passed, 0 failed, 1 ignored | **1540 passed**, 0 failed, 1 ignored (unchanged); `cargo test --workspace` 48 "test result: ok", 0 FAILED | 100% where defined |
| Python tests passing (CPU fast) | 2740 passed, 202 skipped, 30 deselected | **2774 passed**, 202 skipped, 30 deselected (new: 30 `test_wp036f_reexport.py` + 1 `test_daemon_controller.py` DirectML case) | 100% (host `wp001_baseline` register-status string corrected this S4 — see §7) |
| DirectML cross-provider agreement | N/A | **`max_abs_diff_vs_cpu = 7.15e-7`**, within `rtol=1e-5, atol=1e-6` (`EVIDENCE/0144U-…json`) | ≤ Testing Standards §3 default |
| Controller graph CPU bit-identity | N/A | **`max_abs_diff = 0.0`** vs the pristine PRINet 3.0 graph over 48 cases (`np.array_equal` on `uint32` views) | bit-identical |
| Controller inference latency (batch 48, median of 500 warm calls) | N/A | CPU ≈ 0.033 ms, DirectML ≈ 0.27 ms (dispatch-bound, recorded, not a regression) | recorded |
| Changed-code coverage (two new tools) | N/A | **100% / 100%** (`wp036f_reexport_controller.py`, `wp036f_provider_latency.py`; 30 tests) after S3, up from 92% / 97% / 94% at S2 | ≥95% changed |
| Docstring coverage (interrogate) | 97.6% overall | **97.6%** overall (unchanged) | ≥95% overall |
| Clippy/ruff/mypy/bandit/audit | 0 across all gates | 0 across all gates; `mypy --strict` on both new tools 0; `cargo audit` exit 0 (3 governed allowed warnings: `paste` RUSTSEC-2024-0436, `bincode` RUSTSEC-2025-0141, `chacha20` yanked); bandit 0 | 0 at gate threshold |
| Sphinx warning-as-error build | 0 warnings | **0 warnings** (fresh-directory build) | 0 warnings |
| `check_no_python_numerics.py` | clean (19 modules) | **clean (19 modules)** | clean |
| `verify_api_surface` | `(set(), set())` | **`(set(), set())`** — no new `prin` public symbol | `(set(), set())` |
| `check_dv_register_gates.py` | pass | **pass** (33 DV rows × 198 session entries) | pass |
| `check_deviation_ledger.py` | pass | **pass** (delegates to PSR-036 §3; 120 rows, all commit hashes resolve) | pass |

**Verification commands re-run in S4 (2026-09-02, this host, Windows 11 /
Rust 1.92.0 / Python 3.14.0 / `onnxruntime` 1.24.4 with
`get_available_providers() == ['DmlExecutionProvider', 'CPUExecutionProvider']`):**

```
cargo fmt --all -- --check                                                        # clean
cargo clippy --workspace --all-targets -- -D warnings                             # exit 0
cargo test --workspace                                                            # 48 "test result: ok", 0 FAILED
RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps                           # clean
cargo test --doc -p prin-daemon                                                   # 21 passed
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/               # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/      # 245 files already formatted
.venv\Scripts\mypy python/prin --strict                                           # 62 files, 0 issues
.venv\Scripts\mypy --strict tools/wp036f_reexport_controller.py tools/wp036f_provider_latency.py  # 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin                # 97.6%, PASS
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml                  # 0 findings
cargo audit                                                                       # exit 0 (3 governed warnings)
.venv\Scripts\python -m pip_audit .                                               # No known vulnerabilities found
snyk code test tools/wp036f_reexport_controller.py tools/wp036f_provider_latency.py tests/test_wp036f_reexport.py --severity-threshold=low  # 0 issues each
.venv\Scripts\python tools/wp036f_reexport_controller.py --check                  # OK: 3 Gemm nodes, all three-input; manifest current
.venv\Scripts\python tools/check_no_python_numerics.py                            # clean (19 modules)
.venv\Scripts\python tools/check_dv_register_gates.py                             # pass (33 DV rows, 198 sessions)
.venv\Scripts\python tools/check_deviation_ledger.py DOCS/reports/036e-project-state.md  # pass
.venv\Scripts\python tools/wp001_baseline.py check                                # WP-001 baseline validation passed
.venv\Scripts\python -c "import prin; ...verify_api_surface(prin.__all__)"        # (set(), set())
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp  # 2774 passed, 202 skipped, 30 deselected
rm -rf DOCS/sphinx/_build && sphinx-build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html  # build succeeded (fresh dir)
```

Snyk Open Source not triggered — `git diff b7d3ee7..HEAD` touches no
`Cargo.toml` / `Cargo.lock` / `pyproject.toml` / requirements file.

---

## 3. Deviation ledger (cumulative)

### New findings this cycle

| ID | Severity | Status | Resolution |
|---|---|---|---|
| WP036F-F1 | D2 | **FIXED** | Changed-code coverage 94% → 100% on the two new tools. Nine targeted tests added to `tests/test_wp036f_reexport.py` (`TestTransformErrorPaths`, `TestCheckDriftBranches`, `TestProviderLatencyToolEdgeCases`) covering every previously-uncovered `transform_graph` / `_gemm_out_features` error path and `_check` drift branch. No tool source or assertion changed. Commit `a9ad913`. |
| WP036F-F2 | D4 | **FIXED** | `mypy --strict` on the two new tools 3 errors → 0. `wp036f_reexport_controller.py:148` stale `# type: ignore[arg-type]` → `cast("list[dict[str, object]]", …)`; `wp036f_provider_latency.py:131` `**_TOL` splat into `np.allclose` → explicit `rtol=_RTOL, atol=_ATOL` (new module constants; `_TOL` retained verbatim for the evidence JSON). Run-time behaviour byte-identical. Commit `70781ca`. |

### Cumulative ledger

The full cumulative deviation ledger is maintained in PSR-036 §3 and carried
forward. The WP-036F findings above are the most recent additions. All
previous findings from PSR-036/PSR-036A/PSR-036B/PSR-036C/PSR-036D/PSR-036E
remain at their last recorded status.

### Deferred-validation adjudication

- **DV-006 — DirectML half: CLOSED (2026-09-02, WP-036F S4 `0144X`).** The
  re-exported three-input-`Gemm` controller graph is bit-identical to the
  PRINet 3.0 reference on `CPUExecutionProvider` over the 48-case set,
  `DmlExecutionProvider` executes it (real placement, not a CPU fallback),
  and cross-provider agreement holds within Testing Standards §3's
  `rtol=1e-5, atol=1e-6` (`max_abs_diff_vs_cpu = 7.15e-7`), with provider and
  latency acceptance recorded. Evidence chain:
  `DOCS/audits/036f-wp036f-audit.md` (S2 PASS-WITH-FINDINGS + S3 CLEAN
  closure table), `DOCS/experiments/0144U-wp036f-s1-handoff.md`,
  `EVIDENCE/0144U-wp036f-s1-controller-provider-report.json`. Plan amendment
  #13's WP-005 DirectML deferral is **discharged**; Project Plan §3.1 F5 /
  §9 item 7's DirectML condition is met.
- **DV-006 — VitisAI / Ryzen AI NPU half:** stays **OPEN**, hardware-gated —
  `VitisAIExecutionProvider` is not registered on the maintainer host (Ryzen
  7 8700F, no XDNA NPU; Ryzen AI SDK 1.7.0 ships VitisAI only as a CPython
  3.12 wheel). The row is re-scoped to this remainder with the same
  standing-external-disposition class as DV-001; not a Phase 7 entry
  blocker; WP-036G consolidates the permanent disposition.
- **DV-025** (`retrain_controller` / `export_to_onnx` / `quantize_onnx`):
  untouched — the WP-036F transform is a standalone tool, no symbol added.
  Boundary respected.
- **DV-033** (per-change coverage on the maintainer host): `pytest --cov`
  ran cleanly at the two-module scope this cycle, so WP036F-F1 was measured
  and fixed locally rather than deferred to CI.

---

## 4. Plan amendments this cycle

None. Both S2 findings were FIXED in code at S3; no plan-level obligation
changed. Plan amendment #13's WP-005 DirectML deferral is recorded as
**discharged** (the amendment #38 disposition matrix already provided for
this at WP-036F S4).

---

## 5. Risks and blockers

- **DV-006 (VitisAI / Ryzen AI NPU half):** OPEN — hardware/wheel-gated (no
  XDNA NPU; no CPython-3.14 VitisAI wheel). Standing-external disposition,
  same class as DV-001; WP-036G consolidates it. Not a Phase 7 entry
  blocker.
- **DV-030 / DV-003:** `PARTIALLY CLOSED by WP-036E` — unchanged this cycle.
- **DV-005 (CUDA Burn backend):** `CLOSED as AMENDED` by amendment #38 (out
  of scope for 1.0.0). Unchanged.
- **DV-001 (Linux Triton runner):** PARTIALLY VALIDATED — unchanged; WP-036G
  owns the consolidation.
- **DV-008 / DV-017 (`paste` / `bincode` RUSTSEC) + `chacha20` yanked:**
  unchanged — re-verified this cycle (`cargo audit` exit 0, 3 governed
  allowed warnings, no `Cargo.toml` change). WP-036G formalises the
  `chacha20` register row.
- **DV-009 (GitHub secret scanning):** unchanged — Gitleaks + branch
  protection substitute per amendment #5.
- **DV-010 (Phase 1/2 pre-release tag):** unchanged — routed to WP-038 S1;
  WP-036F does not push the tag.
- **CI:** _(superseded — see §9.)_ This cycle stated the batched
  `0144U`–`0144X` push would run CI as a maintainer action and relied on the
  local gate. The push (`adbb1e3`) happened and was **red**; ETCA-002 T-F1
  (D1) and the §9 addendum record the correction and the real green CI run
  the closure is now cited to.
- No new risks introduced. `check_dv_register_gates.py` and
  `check_deviation_ledger.py` both pass.

---

## 6. Next work package declaration — WP-036G

Quoted directly from the registered successor session brief
(`DOCS/sessions/phase-6/0144Y-wp036g-s1-dv-register-consolidation-and-permanent-dispositions.md`),
per Documentation Standards §7 item 5 (quote, do not paraphrase):

- **Title:** "Coding — Deferred-Validation register consolidation and
  permanent dispositions."
- **Mission:** "Bring the Deferred Validation Register to a state where every
  row is in exactly one of: `CLOSED`, `AMENDED` (with amendment ref),
  **permanent disposition** (dated, maintainer-signed, no further re-audit
  gate), or **standing-external-disposition** (dated, evidenced, explicitly
  'not a Phase 7 entry blocker'). Formalise the `chacha20` yanked advisory
  as a register row. Resolve or formally document-as-CI-authoritative the two
  named pre-existing test-fragility issues. Produce a Phase 7 entry
  statement."
- **Acceptance (verbatim highlights):** "**Permanent dispositions** authored
  for **DV-007** … **DV-013** … **DV-018** … **DV-028** …";
  "**Standing-external-disposition** authored for **DV-001** … **DV-008**,
  **DV-009**, **DV-011**, **DV-017**, **DV-022** …"; "A **new register row**
  for the `chacha20` yanked advisory under the DV-008 governance class …";
  "**DV-010** confirmed owned by WP-038 S1 … WP-036G does **not** push the
  tag. **DV-027** recorded as routed to EMA-006."; "**Test-fragility
  resolution:** the DV-019 Python-side
  `test_process_frame_gradcheck_with_prev_slots` gradcheck sub-item …
  `test_no_gpu_throughput_regression` …"; "A **Phase 7 entry statement**
  drafted for the S4 PSR …"; "`tools/check_dv_register_gates.py` passes;
  `tools/check_no_python_numerics.py` clean (unchanged); `≥95%` coverage on
  any changed first-party code."; "No `prin.__all__` / `FROZEN_PUBLIC_API`
  change."
- **Non-goals (verbatim):** "any new numerics; closing DV-001's Triton
  comparison or DV-006's VitisAI half (both hardware-blocked); the WP-038 tag
  push (DV-010); re-litigating the R36 vendoring decision; `bands.rs`-class
  Rust autodiff flakes (closed by `Hotfix-DV019`); DV-005 (closed as
  `AMENDED` by amendment #38 — record, do not re-open)."
- **First session brief:**
  `DOCS/sessions/phase-6/0144Y-wp036g-s1-dv-register-consolidation-and-permanent-dispositions.md`
  (present in `SESSION_REGISTER.md` as `PLANNED`).
- **Sessions:** `0144Y` (S1) → `0144Z` (S2) → `0144AA` (S3) → `0144AB` (S4).
- **Maintainer approval:** required before WP-036G S1 begins (Plan amendment
  #38; this PSR §6 hand-off).

### WP-036G entry conditions

Quoted from the `0144Y` brief "Entry conditions":

1. "WP-036F S4 (`0144X`) is closed and committed." — ✅ all S4 artefacts
   committed locally; the batched push is the maintainer's action.
2. "No unresolved D1/D2 finding exists." — ✅ (WP036F-F1 FIXED, WP036F-F2
   FIXED; delta re-audit CLEAN).
3. "WP-036G scope, acceptance criteria, and non-goals have maintainer
   approval (Plan amendment #38; PSR-036F §6 hand-off)." — pending maintainer
   acknowledgement of this PSR.

---

## 7. Cross-cutting document currency

Per Documentation Standards §7 items 7–8 (consistency and documentation-
accuracy sweep — this is a WP-N S4, not a phase-closing S4, so item 9 does
not apply):

- **READMEs in touched directories:** `tests/README.md` (`test_wp036f_reexport.py`
  21 → 30, S3 error-path classes noted; combined-suite fast-gate figure
  2,743 → 2,774), `models/README.md` (DirectML execution + DV-006
  DirectML-half closure note) updated. `tools/README.md` already described
  both new tools accurately from S1 (S3 changed only two type-hint lines,
  no API/behaviour change).
- **Sphinx:** `DOCS/sphinx/api/daemon.rst` gains a "Controller graph —
  three-input `Gemm` re-export (WP-036F)" section; `DOCS/sphinx/migration_guide.rst`
  WP-028 daemon section gains a controller-graph deviation bullet;
  `DOCS/sphinx/parity_report.rst` gains a "WP-036F — DirectML
  controller-graph execution" deviation-register entry with the
  provider-latency figures. Fresh-directory `sphinx-build -W` is clean.
- **`DOCS/` index files:** `DOCS/audits/README.md` 036f entry updated to the
  S3 CLEAN closure; `DOCS/reports/README.md` gained the `036e-project-state.md`
  (missed at WP-036E S4 `0144T`) and `036f-project-state.md` entries.
- **CHANGELOG.md:** S3 and S4 entries added under `[Unreleased]`.
- **Governance:** `DOCS/PRIN_Project_Plan.md` amendment #13 row records the
  DirectML discharge; `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-006
  row re-scoped.
- **`DOCS/sessions/SESSION_REGISTER.md`:** the `0144W` status cell had been
  left decorated ("COMPLETE — both findings FIXED, delta re-audit CLEAN") by
  the S3 session, which `tools/wp001_baseline.py check` rejects (it requires
  a bare status keyword). Corrected to `COMPLETE` as part of this S4's
  register update (a documentation-string correction, not a code change);
  `0144X` set to `COMPLETE`. `wp001_baseline.py check` now passes and the
  three `tests/test_wp001_baseline.py` cases it backs are green again.

---

## 8. Trajectory verdict

**ON TRAJECTORY.** WP-036F met both acceptance criteria — mathematical
identity of the re-exported controller graph (48-case CPU bit-identity vs the
PRINet 3.0 reference) and `DmlExecutionProvider` execution with in-tolerance
cross-provider agreement — independently verified at S2; the two S2 findings
(a changed-code coverage shortfall and cosmetic type-hint nits) were FIXED in
S3 with a CLEAN delta re-audit and no plan amendment. The DirectML half of
DV-006 is CLOSED and plan amendment #13's DirectML deferral is discharged;
the VitisAI/NPU half is re-scoped to a hardware-gated standing-external
disposition. Two of the three amendment-#38 closure work packages (WP-036E,
WP-036F) are now complete; WP-036G (`0144Y`) is the last, after which no open
DV row remains in an undated "re-audit every cycle" state going into Phase 7.

---

## 9. ETCA-002 remediation addendum (2026-09-02)

**This cycle's S4 closure was recorded over a red `origin/main` push.** ETCA-002
(`DOCS/audits/EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_002.md`, verdict `FAIL`,
finding **T-F1** D1) established that the batched `0144U`–`0144X` push
(`adbb1e3`, which also carried the WP-036E range) was **red**: `python` `lint`
(`mypy --strict`, 3 unused `type: ignore` — T-F2) and all three Windows `test`
legs (5 DirectML/provider tests — T-F3), with `gpu` skipped (no `[gpu]` tag —
T-F6) and `nightly` red (T-F5). §7 above ("CI: … a maintainer action … The full
local gate is reproduced in §2 and is green") and the `0144X` session doc's
"CI is green. WP-036F is closed" were **not** backed by a live CI check
(amendment #28's S4 exit criterion was unmet).

**Correction (ETCA-002 remediation session, 2026-09-02):**

- **T-F2** — the 3 `# type: ignore[no-untyped-call]` sites (WP-036E-era code,
  never touched by WP-036F) got `, unused-ignore` added so the strict-mode
  verdict no longer flips with the torch stub version; `python.yml`'s `lint`
  toolchain is now pinned (`ci/lint-constraints.txt`, amendment #45 G6).
- **T-F3** — the DirectML/provider tests' `skipif` guards probed
  `ort.get_available_providers()` (wheel registration), which does not fire on
  hosted `windows-latest` (no DX12 device). Replaced with
  `tests/_env.py::directml_executes()` (an executability probe) +
  `@pytest.mark.directml`; `wp036f_provider_latency` records a portable `close`
  (tolerance) signal alongside the ORT-build-specific `bit_identical`. The
  tests now **skip cleanly** on incapable hosts and **run on
  `PRIN-GPU-Runner`** (`gpu.yml`, every push — T-F6/amendment #45 G4). A CI
  guard (`tools/check_skipif_probes.py`) blocks the registration anti-pattern.
- **T-F5** — `test_speed_vs_transformer` quarantined into `tests/conftest.py`
  under **DV-032** (dated maintainer disposition); `nightly` `full-suite` green.
- **DirectML half of DV-006 + amendment #13 discharge — re-affirmed** over a
  real green `origin/main` CI run — HEAD **`9d4fd86`**, **all six workflows**
  (`rust`/`python`/`parity`/`repro`/`snyk`/`gpu`) `success`
  (`tools/check_ci_green.py 9d4fd86` exit 0; ETCA-002 report §7). On
  `PRIN-GPU-Runner`'s real DirectML adapter the `gpu-cuda` job's
  `TestDirectMLExecution` tests **run and pass**; on hosted `windows-latest`
  they **skip cleanly**. The `0144X` closure was substantively correct — the
  re-export is mathematically exact and DirectML-executes on real hardware —
  but was procedurally recorded ahead of CI confirmation; that gap is now
  closed.
- **Governance** — Plan amendment #45 adopts ETCA-002 recommendations G1–G8
  (per-WP blocking S4 push; `tools/check_ci_green.py` S4 gate; `main` branch
  ruleset; `gpu.yml` on every push; nightly-red dispositioned like push-red;
  pinned CI toolchains; ETCA auto-trigger; recurrence ⇒ class guard).
