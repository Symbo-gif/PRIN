---

# PRIN Project State Report — Cycle 036G

**Date:** 2026-09-15
**Cycle:** 036G (WP-036G "Deferred-Validation register consolidation and permanent dispositions")
**Completed sessions:** 0144Y (S1), 0144Z (S2), 0144AA (S3), 0144AB (S4)
**Author:** Devin (AI pair)
**Git state:** `etca-002/rust-windows-self-hosted` @ S4 closure (local; the batched
`0144Y`–`0144AB` push is a maintainer action per amendment #28)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1. WP-036G is
  the third and final of the three amendment-#38 Deferred-Validation closure
  work packages (WP-036E → WP-036F → WP-036G); it closes the amendment-#38
  DV-closure block immediately before WP-037 (`0145`).
- **This cycle delivered:**
  - **Permanent dispositions** (`0144Y` drafted, `0144AB` signed) for
    **DV-007** (PRINet 3.0 `torch.complex64`/f32 reference hazard — governed
    by the `1e-6` derivative tolerance + corpus `rtol=2e-6` + Parity Report,
    amendments #14/#16/#17/#25), **DV-013** (`M-F3`/`M-F7` policy-gate claims
    permanently `REQUIRES_HUMAN_REVIEW` — governed by fresh maintainer
    sign-off whenever an EMA claim set changes), **DV-018** (`burn-tensor`
    f32-internal `sigmoid` precision floor — documented per call site with
    `eps=1e-4` / `rtol=1e-6`), and **DV-028** (R36's decision not to vendor
    `math-audit-mcp` — final absent a CI-reachable published remote). Each
    row states its standing governance mechanism and "no further re-audit
    gate"; the maintainer sign-off is recorded in §3.3.
  - **Standing external / third-party dispositions** for **DV-001** (Linux
    Triton runner — plus the dormant `.github/workflows/gpu-triton.yml`
    skeleton gated on `[self-hosted, linux, gpu]`), **DV-008**, **DV-009**,
    **DV-011**, **DV-017**, **DV-022** — one consolidated evidenced
    re-verification pass (§3.4) and a per-row "external / third-party, not
    repo-closeable, not a Phase 7 entry blocker" statement.
  - **A new register row, DV-035**, for the `chacha20` 0.10.1 yanked release
    under the DV-008/Coding Standards §6.2 governance class (visibility,
    threat assessment, compensating controls, `cargo audit` exit-0 evidence,
    per-cycle re-check).
  - **DV-010** confirmed owned by WP-038 S1 (`0149`) — WP-036G does not push
    the tag; **DV-027** recorded as routed to EMA-006.
  - **Test-fragility resolution:** the DV-019 Python-side
    `test_process_frame_gradcheck_with_prev_slots` gradcheck sub-item was
    confirmed as the already-fixed ETCA-001 global-Torch-RNG/order issue (the
    shared Burn `AutodiffServer` root cause was ruled out — PyTorch has no
    such process-global server), with the existing autouse
    `torch.manual_seed(0)` guard the regression control (10/10 S1, 5/5 S2
    independent re-runs); no new DV item was required.
    `test_no_gpu_throughput_regression` was hardened (fixed 1,000,000-iteration
    work, warm-up, seven-sample relative median) with its original `<1.30`
    assertion preserved and its quarantine removed (3/3 S1, 3/3 S2).
  - **Phase 7 entry statement** (§8) enumerating every remaining open DV item
    with a per-item "does not block campaign pre-registration or execution"
    assertion.
  - **S1 security prerequisite:** the 2026-09-15 advisory refresh exposed
    actionable RUSTSEC-2026-0285 in locked `rustls` 0.23.43; `Cargo.lock` was
    advanced to `rustls` 0.23.45 / `rustls-webpki` 0.103.15 before S1
    continued (no API or numerics change), after which `cargo audit` returns
    exit 0 with only the three governed warning-class rows DV-008/DV-017/DV-035.
- **Plan conformance:** ON TRAJECTORY WITH AMENDMENTS — amendments #1–#45
  remain in force; no new amendment this cycle. This cycle discharges the
  amendment-#38 WP-036G obligation and completes the amendment-#38 DV-closure
  block (WP-036E/F/G).
- **Audit:** `DOCS/audits/036g-wp036g-audit.md` — S2 verdict **PASS** (zero
  findings); S3 mandatory no-change closure with delta re-audit **CLEAN**
  (§7). No unresolved D1/D2 finding exists.
- **Session Register:** 0144Y (S1), 0144Z (S2), 0144AA (S3), 0144AB (S4) all
  marked COMPLETE; 0145 (WP-037 S1) is the registered successor.
- **WP-036G is CLOSED. WP-036E, WP-036F, and WP-036G are all complete; the
  amendment-#38 Deferred-Validation closure block is complete.**

---

## 2. Metric trends

| Metric | Previous (PSR-036F) | Current (PSR-036G) | Gate |
|---|---|---|---|
| Rust tests passing (default) | 1540 passed, 0 failed, 1 ignored | **1540 passed, 0 failed, 1 ignored** (unchanged); `cargo test --workspace` 48 "test result: ok", 0 FAILED | 100% where defined |
| Python tests passing (CPU fast) | 2774 passed, 202 skipped, 30 deselected | **2775 passed, 201 skipped, 30 deselected** (quarantine removed → `test_no_gpu_throughput_regression` +1 passed / −1 skipped) | 100% |
| Python full suite + parity | (not tabulated in PSR-036F) | **3395 passed, 203 skipped**; 95% coverage under the governed `.pytest_basetemp` | 100% at tolerance |
| Fragile-test re-verification | N/A | Throughput test 3/3 isolated runs; DV-019 gradcheck 5/5 isolated runs (S2) / 10/10 (S1) | deterministic |
| Docstring coverage (interrogate) | 97.6% overall | **97.6%** overall (unchanged) | ≥95% overall |
| Clippy/ruff/mypy/bandit/audit | 0 across all gates | 0 across all gates; `cargo audit` exit 0 (3 governed warnings: `paste` RUSTSEC-2024-0436, `bincode` RUSTSEC-2025-0141, `chacha20` yanked DV-035); both `pip-audit` scopes clean; Snyk SCA 0 issues; bandit 0 | 0 at gate threshold |
| Sphinx warning-as-error build | 0 warnings | **0 warnings** (fresh-directory build) | 0 warnings |
| `check_no_python_numerics.py` | clean (19 modules) | **clean (19 modules)** | clean |
| `verify_api_surface` | `(set(), set())` | **`(set(), set())`** — no new `prin` public symbol | `(set(), set())` |
| `check_dv_register_gates.py` | pass (33 rows) | **pass** (35 DV rows × 198 session entries) | pass |
| `check_deviation_ledger.py` | pass | **pass** (delegates to PSR-036 §3; 120 rows, all commit hashes resolve) | pass |
| `wp001_baseline.py check` | pass | **pass** (workflow inventory 9, incl. `gpu-triton.yml`) | pass |

**Verification commands re-run in S4 (2026-09-15, this host, Windows 11 /
Rust 1.92.0 / Python 3.14.0), matching the S3 delta re-audit §7.1 (no source
or test change between S3 and S4 — S4 is documentation-only):**

```
cargo fmt --all -- --check                                                        # clean
cargo clippy --workspace --all-targets -- -D warnings                             # exit 0
cargo test --workspace                                                            # 48 "test result: ok", 0 FAILED
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps                  # clean
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/               # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/      # 248 files already formatted
.venv\Scripts\mypy python/prin --strict                                           # 62 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin                # 97.6%, PASS
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml                  # 0 issues
cargo audit                                                                       # exit 0 (3 governed warnings)
.venv\Scripts\python -m pip_audit .                                               # No known vulnerabilities found
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt                # No known vulnerabilities found
.venv\Scripts\python tools/check_no_python_numerics.py                            # clean (19 modules)
.venv\Scripts\python tools/check_dv_register_gates.py                             # pass (35 rows, 198 sessions)
.venv\Scripts\python tools/check_deviation_ledger.py DOCS/reports/036e-project-state.md  # pass
.venv\Scripts\python tools/wp001_baseline.py check                                # WP-001 baseline validation passed
.venv\Scripts\python -c "from prin._deprecation import verify_api_surface; from prin import __all__; print(verify_api_surface(__all__))"  # (set(), set())
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp  # 2775 passed, 201 skipped, 30 deselected
Remove-Item -Recurse -Force DOCS/sphinx/_build -ErrorAction SilentlyContinue
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html  # build succeeded (fresh dir)
```

---

## 3. Deviation ledger (cumulative)

### 3.1 New findings this cycle

None. The WP-036G S2 audit (`0144Z`) returned **PASS with zero findings**;
the mandatory S3 (`0144AA`) recorded a no-change closure with a CLEAN delta
re-audit (`DOCS/audits/036g-wp036g-audit.md` §7). No source, test, plan
amendment, or finding commit was applicable or performed.

### 3.2 Cumulative ledger

The full cumulative deviation ledger is maintained in PSR-036 §3 and carried
forward. No new finding ID is added by WP-036G. All previous findings from
PSR-036 through PSR-036F remain at their last recorded status.

### 3.3 Maintainer sign-off — permanent dispositions (DV-007, DV-013, DV-018, DV-028)

The four by-design / third-party items below are **permanently accepted with
no further re-audit gate**, per the DV-004/R35 and DV-021/#30 disposition
precedent (long-open item resolved by an explicit, dated disposition rather
than an indefinite "re-audit every cycle"). Each names its standing
governance mechanism:

- **DV-007** — PRINet 3.0 `torch.complex64` (f32) internal arithmetic is a
  reference-implementation numerical hazard; governed by the `1e-6`
  derivative tolerance, the corpus `rtol=2e-6`, and the Parity Report
  (amendments #14/#16/#17/#25).
- **DV-013** — `M-F3`/`M-F7` policy-gate claims (`INT-01`, `INT-02`, `HOPF-01`,
  `KUR-01`, `GRA-01`, `TEN-01`, `TCK-01`) are permanently
  `REQUIRES_HUMAN_REVIEW`; governed by fresh maintainer sign-off whenever an
  EMA claim set changes (last re-granted at EMA-006, 2026-09-01).
- **DV-018** — `burn-tensor` 0.16.1's `sigmoid` downcasts through f32
  internally on `NdArray<f64>`; documented at every affected call site with
  `eps=1e-4` / `rtol=1e-6`; re-examined only on a `burn` version bump.
- **DV-028** — R36's decision not to vendor `math-audit-mcp` into PRIN is
  final; re-evaluated only if a CI-reachable published remote appears.

**Signed: MichaelMaillet (maintainer), 2026-09-15.**

This completes the WP-036G permanent-disposition acceptance item. The
register rows for DV-007 / DV-013 / DV-018 / DV-028 are updated from
`PERMANENT DISPOSITION DRAFT` to `PERMANENT DISPOSITION` with this sign-off
referenced, and DV-035's standing-third-party disposition is recorded signed
(PSR-036G §3.3).

### 3.4 Consolidated re-verification evidence summary

The one-pass re-verification required by the WP-036G brief for every standing
external/third-party item is captured in
`EVIDENCE/0144Y-wp036g-s1-dv-reverification/reverification.md` and
independently re-run by the S2 audit (`036g-wp036g-audit.md` §3.6):

- **External controls:** `gh api .../actions/runners` → one online
  `PRIN-GPU-Runner` (`[self-hosted, Windows, X64, gpu]`), no Linux-labelled
  runner (DV-001/DV-034). `gh api .../secret-scanning/alerts` → HTTP 404
  "disabled" (DV-009). `.snyk` torch entries current through 2026-11-14, the
  three audit-tool entries through 2026-11-06; the high-advisory rationale
  corrected for two ordinary `torch.load(..., weights_only=True)` call sites
  without changing scope/expiry (DV-011).
- **Dependency advisories:** `cargo audit` exit 0 with only `paste`
  RUSTSEC-2024-0436 (DV-008), `bincode` RUSTSEC-2025-0141 (DV-017), and the
  newly-registered `chacha20` yanked warning (DV-035); both `pip-audit`
  scopes clean; Snyk Open Source (MCP, all_projects) 0 issues; bandit 0.
- **Host tooling:** `verify_api_surface` `(set(), set())`; `check_no_python_numerics`
  clean; `check_dv_register_gates` 35 rows / 198 sessions; `wp001_baseline`
  pass; ruff/mypy/interrogate/clippy/rustdoc all clean.
- **Fragility re-verification:** DV-019 gradcheck 10/10 (S1) and 5/5 (S2
  independent); hardened throughput test 3/3 (S1) and 3/3 (S2 independent).

**Transparent out-of-scope observation (from the audit §3.9):** the
AGENTS.md full-suite spelling `--basetemp=.pytest_basetemp-full` is rejected
by `prin.reporting._artifacts.allowed_output_roots()`, causing 11 figure/table
path-policy failures, while the identical suite with the governed
`.pytest_basetemp` root passes 3,395/3,395 non-skipped tests. This is a
pre-existing verification-command/path-policy mismatch, not attributable to
WP-036G. It is corrected in AGENTS.md this S4 (a one-line documentation edit
with no code risk — Documentation Standards §7 item 9 deferral rule "fix now").

**Deferred-validation adjudication (final state):** every DV register row is
now in exactly one of `CLOSED`, `AMENDED` (DV-005, amendment #38),
`PARTIALLY CLOSED` (DV-003 amendment #44, DV-030 amendment #43 — each with a
named upstream CubeCL re-gate), permanent-disposition (DV-007/DV-013/DV-018/
DV-028, signed above), or standing-external/third-party disposition (DV-001,
DV-006 VitisAI half, DV-008, DV-009, DV-011, DV-016, DV-017, DV-022, DV-024,
DV-033, DV-034, DV-035 — dated, evidenced, "not a Phase 7 entry blocker").
No row remains in an undated open-ended "re-audit every cycle" state.

---

## 4. Plan amendments this cycle

None. WP-036G executed the amendment-#38 WP-036G disposition matrix without
new scope, source numerics, or public-API change. The amendment-#38
DV-closure block (WP-036E → WP-036F → WP-036G) is now complete; only then
may WP-037 (`0145`) begin (amendment #38 / this PSR §6).

---

## 5. Risks and blockers

- **DV-001 (Linux Triton runner):** OPEN, standing-external — Triton has no
  Windows support; the dormant `.github/workflows/gpu-triton.yml` stages the
  comparison on `[self-hosted, linux, gpu]` so runner registration is the
  sole remaining step. Not a Phase 7 entry blocker.
- **DV-006 (VitisAI / Ryzen AI NPU half):** OPEN, standing-external —
  hardware/wheel-gated (no XDNA NPU; no CPython-3.14 VitisAI wheel). Not a
  Phase 7 entry blocker.
- **DV-030 / DV-003:** `PARTIALLY CLOSED by WP-036E` — bidirectional zero-copy
  kernel-input and genuine CUDA device-event timing re-gated on a CubeCL
  external-memory API / `TimingMethod::Device` release (amendments #43/#44).
  Not a Phase 7 entry blocker.
- **DV-008 / DV-017 / DV-035 (`paste` / `bincode` / `chacha20`):** governed
  warning-class advisories with no PRIN-level fix; `cargo audit` exit 0 and
  the compensating controls remain in force. Not Phase 7 entry blockers.
- **DV-024 / DV-034 (single self-hosted `PRIN-GPU-Runner` SPOF):** the runner
  is now an auto-start Windows service (DV-024 root cause resolved); the
  residual single-machine risk (DV-034) is explicitly accepted with a second
  runner as the named mitigation. Not a Phase 7 entry blocker.
- **Phase 6 not yet closed:** WP-037 (`0145`) and WP-038 (`0149`–`0152`)
  remain before the Phase 6 exit gate; this PSR closes only the DV-closure
  block, not the phase.
- No new risks introduced. `check_dv_register_gates.py` and
  `check_deviation_ledger.py` both pass.

---

## 6. Next work package declaration — WP-037

Quoted directly from the registered successor session brief
(`DOCS/sessions/phase-6/0145-wp037-s1-documentation-notebooks-paper-and-parity-report-draft.md`),
per Documentation Standards §7 item 5 (quote, do not paraphrase):

- **Title:** "Coding — Documentation, notebooks, paper, and Parity Report draft."
- **Mission:** "Complete Sphinx guides/API, four notebooks, docs.rs links,
  paper artefact wiring, and evidence-backed draft Parity Report from
  pre-campaign validation."
- **Acceptance (verbatim):** "Docs build warning-free; examples/notebooks
  execute; claims cite artefacts; draft clearly labels validation vs
  confirmatory campaign results."
- **Non-goals (verbatim):** "Publishing 1.0 or replacing Phase 7
  pre-registration."
- **First session brief:**
  `DOCS/sessions/phase-6/0145-wp037-s1-documentation-notebooks-paper-and-parity-report-draft.md`
  (present in `SESSION_REGISTER.md` as `PLANNED`; predecessor `0144AB` set by
  amendment #38).
- **Sessions:** `0145` (S1) → `0146` (S2) → `0147` (S3) → `0148` (S4).

### WP-037 entry conditions

Quoted from the `0145` brief "Entry conditions":

1. "The preceding S4 (or campaign synthesis for WP-039) is closed and
   committed." — ✅ this S4 (`0144AB`).
2. "WP-037 scope, acceptance criteria, and non-goals have maintainer
   approval." — ✅ the `0145` brief is registered and approved; amendment #38
   wired its predecessor to `0144AB` and scoped its Parity Report to the
   post-DV state.
3. "No unresolved D1/D2 finding exists; any carried D4 is explicitly in this
   scope." — ✅ (S2 PASS zero findings; S3 delta re-audit CLEAN).

**Maintainer approval recorded: MichaelMaillet, 2026-09-15 (this PSR §6
hand-off).** Only after this S4's closure may WP-037 (`0145`) begin
(amendment #38).

---

## 7. Cross-cutting document currency

Per Documentation Standards §7 items 7–8 (consistency and documentation-
accuracy sweep) and the brief's item-9 cross-cutting verification (Project
Plan §6 roadmap table, `DOCS/experiments/README.md` index,
`SESSION_REGISTER.md` Global Sessions section — WP-036G S4 is not a
phase-closing S4, so item 9 does not strictly apply; the three documents are
verified nonetheless, per the brief's explicit instruction):

- **READMEs in touched directories:** `.github/workflows/README.md` (the
  dormant `gpu-triton.yml` entry, updated in S1 and verified by the S2 audit
  §3.5) and `tests/README.md` (throughput-test hardening + GPU/DirectML
  counts) were updated in S1–S3 and remain accurate; no further S4 change was
  required.
- **Sphinx:** `DOCS/sphinx/parity_report.rst` and
  `DOCS/sphinx/migration_guide.rst` already carry the DV-007 f32-vs-f64
  permanent-hazard language (Parity Report §"WP-007 — f64 vs `torch.complex64`
  reference drift"; Migration Guide §"Mean-field order-parameter precision
  (D1)" citing "Project Plan amendment #14 / DV-007"), the DV-003 device-event
  entry, the DV-030 tolerance note, and the WP-036F DirectML entry. No WP-036G
  parity-report change is required (governance-only WP, no numerics).
  Fresh-directory `sphinx-build -W` is clean.
- **`DOCS/` index files:** `DOCS/reports/README.md` and `DOCS/audits/README.md`
  gained the `036g-project-state.md` and `036g-wp036g-audit.md` entries (the
  audit README was missing the `036g` row after S2 created the audit file).
- **CHANGELOG.md:** S4 entry added under `[Unreleased]`.
- **`DOCS/sessions/SESSION_REGISTER.md`:** `0144AB` set to `COMPLETE` (bare
  keyword, per `wp001_baseline.py check`); `0145` remains `PLANNED` as the
  successor.
- **`DOCS/sessions/phase-6/README.md`:** `0144AB` row set to `COMPLETE`.
- **Project Plan §6 roadmap table:** already carries the WP-036E/F/G
  Deferred-Validation closure row (amendment #38); no phase marker changes
  (Phase 6 is not yet closed).
- **`DOCS/experiments/README.md` index:** already lists the
  `0144Y-wp036g-s1-handoff.md` entry (added in S1).
- **`SESSION_REGISTER.md` Global Sessions section:** EMA-006 and EDA-001 are
  committed without their own register rows/sections — a pre-existing gap
  already flagged in the register itself for a future EMA/EDA or EA session
  to reconcile; it is not WP-036G scope and is left with that recorded
  rationale (Documentation Standards §7 item 9 deferral-requires-rationale).
- **AGENTS.md:** the full-suite `--basetemp=.pytest_basetemp-full` spelling
  (flagged D4 by the S2 audit §3.9) is corrected to the governed
  `.pytest_basetemp` path-policy spelling.

---

## 8. Phase 7 entry statement

Every remaining open Deferred Validation item carries a dated disposition and
**does not block campaign pre-registration (`0153` E0) or execution**. Each
item:

- **DV-001** — Linux Triton comparison is hardware-runner-gated; the dormant
  `gpu-triton.yml` is staged. Not a blocker.
- **DV-003** — CubeCL CUDA device-event timing residual has amendment #44's
  upstream CubeCL release trigger. Not a blocker.
- **DV-005** — `AMENDED` by amendment #38 (CUDA Burn training out of scope for
  1.0.0; post-1.0 re-gate). Not a blocker.
- **DV-006 (VitisAI/NPU half)** — absent NPU/provider hardware is explicitly
  hardware-gated. Not a blocker.
- **DV-007** — accepted PRINet f32-reference hazard, permanently bounded by
  registered tolerances and the Parity Report. Not a blocker.
- **DV-008** — transitive unmaintained `paste` warning, no PRIN-level fix;
  native audit active. Not a blocker.
- **DV-009** — GitHub native secret scanning unavailable; amendment #5
  Gitleaks + branch-protection controls active. Not a blocker.
- **DV-010** — WP-038 S1 (`0149`) owns the release tag action. Not a blocker.
- **DV-011** — six no-fix torch advisories retain current threat assessments
  through 2026-11-14. Not a blocker.
- **DV-013** — by-design human-review status, governed by fresh sign-off
  whenever the EMA claim set changes. Not a blocker.
- **DV-016** — hosted-Windows slowdown avoided by the service-backed
  self-hosted leg and bounded timeout. Not a blocker.
- **DV-017** — transitive unmaintained `bincode` warning, amendment #27
  controls retained. Not a blocker.
- **DV-018** — pinned Burn f32 sigmoid floor controlled at each call site,
  rechecked only on a Burn bump. Not a blocker.
- **DV-022** — hosted-runner disk capacity mitigated by disk reclaim and
  CPU-only torch installation. Not a blocker.
- **DV-024** — runner availability is service-backed; residual single-machine
  risk represented by DV-034. Not a blocker.
- **DV-027** — stale external-tool editable metadata is cosmetic, zero
  runtime/evidence effect. Not a blocker.
- **DV-028** — R36's no-vendoring decision is final absent a CI-reachable
  published remote. Not a blocker.
- **DV-030** — input-direction zero-copy awaits a CubeCL external-memory API
  or governed storage shim (amendment #43). Not a blocker.
- **DV-031** — deliverables have WP-037/WP-038 owners; CUDA residuals follow
  DV-030's trigger. Not a blocker.
- **DV-032** — one named test hardened and active; two unrelated
  benchmark-class checks retain explicit limits and nightly/CI authority. Not
  a blocker.
- **DV-033** — CI codecov remains authoritative for per-change coverage where
  the maintainer-host tool is unavailable. Not a blocker.
- **DV-034** — second-runner redundancy is external infrastructure; required
  GPU checks remain enforced. Not a blocker.
- **DV-035** — yanked `chacha20` remains visible and rechecked until upstream
  resolution changes. Not a blocker.

All other DV rows are `CLOSED`. The Phase 7 experimentation campaign
(`0153` E0) may be pre-registered and executed with no open Deferred
Validation item blocking entry.

---

## 9. Trajectory verdict

**ON TRAJECTORY.** WP-036G assigned a dated, evidenced disposition to every
remaining open Deferred Validation item — four permanent dispositions
maintainer-signed in §3.3, the standing external/third-party confirmations
re-verified in one evidenced pass, the `chacha20` advisory formalised as
DV-035, DV-010/DV-027 routed to their concrete owners, and the two
test-fragility items resolved — with a zero-finding S2 audit and a CLEAN S3
delta re-audit. No source numerics or public API changed. The register now
contains zero rows in an undated open-ended "re-audit every cycle" state. The
Phase 7 entry statement (§8) asserts, per item, that nothing blocks campaign
pre-registration or execution. **WP-036G is CLOSED; WP-036E, WP-036F, and
WP-036G are complete; the amendment-#38 Deferred-Validation closure block is
complete.** WP-037 (`0145`) entry conditions are confirmed and maintainer
approval recorded (§6).
