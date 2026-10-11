# PRIN Project State Report - Cycle 040

**Date:** 2026-10-11 UTC
**Cycle:** 040 (EA-007 global Executive Audit and pre-EXP-002 readiness —
global session outside the planned 0001–0198 and campaign E-stage sequences)
**Completed sessions:** EA-007 (global session; no planned-trajectory
session 0001–0198 or campaign E-stage is completed by this cycle — 0159
remains READY, not started)
**Author:** Devin (AI pair); PR #32 review-round corrections by Claude Sonnet 5.5
(AI pair), `DOCS/audits/PR032-multi-review-audit.md`
**Git state:** `audit/ea007-exp002-readiness` — issued at base
`fdd28d88e4c57d544e5d30fa52cce85807ab15a9` + the three EA-007 commits
(`199b82a`, `0738714`, `add7386a`); the PR #32 review-round remediation commits
follow (no commit SHA claimed here — a commit cannot name itself)
**Status:** **ISSUED** — local validation complete under the Plan amendment
#48 regime (hosted CI paused; Linux/macOS suspended). Python per-change
coverage remains unmeasured (DV-033 open); the platform/hosted gates stay
suspended. Audit verdict `PASS-WITH-REMEDIATION` per
`DOCS/audits/EXECUTIVE_AUDIT_REPORT_007.md`; main delivery via PR pending.

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 7 — Experimentation campaign. Session 0159 (EXP-002 E1)
  remains **READY**: `EXP-001-r1` E5 was accepted by the maintainer
  (MichaelMaillet, 2026-09-29 UTC) with all five hypotheses `CONFIRMED` — a
  non-reversal verdict — which releases 0159 per campaign plan §10.4 item 5.
  The original EXP-001 `REFUTED` results (H1, H2a) remain unchanged and
  immutable.
- **Historical closures confirmed by re-verification, not recomputation:**
  - `EXP-001-r1` carried to `main` by PR #28 merge
    `32cfed8a0b4d915a04e18efbfadd146a2ecb7e32`; the `tools/check_ci_green.py`
    pre-pause check on that SHA exits 0 (verbatim output
    `EVIDENCE/ea007/exp001-r1-merge-ci-green.log`). This is historical
    entry-condition evidence, not current-branch validation.
  - DV-041 (PR #25, `5615eda`), DV-043 (PR #26, `9b79d2e`, plus green nightly
    run `36525353031` attempt 2), and DV-044 (carried into `main` by the
    `EXP-001-r1` range via PR #28) remain historically CLOSED.
  - Latest pre-pause nightly `36818721762` @ `bbf97dc` (2026-10-01) is green —
    pre-pause evidence only, **not** current-`main` evidence.
- **This cycle's bounded work:** DV-040 option (a) — the maintainer-selected
  remediation extending existing quality-gate roots and their AGENTS.md local
  equivalents to `DOCS/experiments/` (ruff check root extension, a separate
  source-only `ruff format` campaign leg, a separate `mypy --strict` campaign
  leg, and bandit recursion over `python/prin` + `DOCS/experiments`), plus
  tightening of `[tool.bandit] exclude_dirs` from bare substrings to directory
  component globs; and DV-042 — the `crates/prin-sim/src/gpu.rs` module-doc
  `kDLCUDA` export section made feature-accurate via `#![cfg_attr]`-gated doc
  attributes. Neither change alters numerical behavior. No experiment runs,
  drivers, analysis code, or protocol changes were created.
- **Security remediation this cycle (EA007-E-F4):** a Snyk SCA scan flagged
  `urllib3` 2.7.0 in `DOCS/sphinx/requirements.txt` under three published
  advisories (SNYK-PYTHON-URLLIB3-20302844 / CVE-2026-97687 HIGH,
  -20302845 / CVE-2026-97688 MEDIUM, -20302846 / CVE-2026-97689 HIGH, all
  `fixedIn` 2.8.0). The documentation dependency floor was raised to
  `urllib3>=2.8.0`, the gate venv upgraded 2.7.0→2.8.0 only, and file-scoped
  Snyk SCA plus both `pip-audit` legs re-verified clean; a regression test
  pins the floor. No runtime dependency changed. The five `torch` 2.14.1
  advisories seen by the resolved main-manifest scan are the pre-existing
  governed `.snyk` dispositions (EA-003 E-F7, expires 2026-11-14) — not new
  findings; the affected torch APIs have no call sites in this repository.
- **Regime:** Plan amendment #48 local-validation regime in force — hosted
  checks paused; all gates run locally on the maintainer's Windows host;
  Linux/macOS not tested (suspended, not satisfied).

## 2. Metric trends (known facts only)

| Metric | Previous (PSR-039) | Current (PSR-040) | Gate |
|---|---|---|---|
| Rust tests passing (default) | 1,590 passed, 0 failed, 1 ignored | **1,604 passed, 0 failed, 1 ignored** (`cargo test --workspace`, leg 11a); strict 1,608, cuda 1,659, wgpu 1,675, kernels-cpu 143, sim-cpu 239 — all 0 failed | 100% where defined |
| Python tests passing | 3,275 passed / 181 skipped (fast suite) + 2,144 passed / 1 skipped (parity suite) | **5,667 passed / 184 skipped / 0 failed / 61 warnings** (`pytest tests/ parity/`, leg 25, 29:42, exit 0; includes the 19 gate tests that existed at gate time — 22 after the PR #32 round) | 100% |
| Coverage (new/changed code) | 95% total | **not measured — DV-033 OPEN.** The coverage-mode attempt timed out, so no Python percentage is claimed. Rust raw line totals (87.18% kernels wgpu/cpu, 63.59% dynamics default, 63.67% strict) are totals, not ≥95% assertions; this diff adds no executable production lines | ≥95% — **NOT MET (unmeasured)** |
| Docstring coverage (interrogate) | 97.6% | **97.6%** (`interrogate -c pyproject.toml python/prin`, leg 06) | ≥95% overall, 100% public |
| Parity cases passing / total defined | 504/504 corpus; 978+22 fuzz | **`parity/` suite 2,144 passed / 1 skipped / 0 failed** inside leg 25 (counted from the log's node ids); corpus and fuzz case counts were not re-derived this cycle | 100% at tolerance |
| Clippy/ruff/mypy/bandit/audit findings | 0 findings; cargo audit 3 governed warnings | **0 findings** (clippy default+strict, ruff, mypy ×2, non-vacuous bandit); `cargo audit` 0 vulnerabilities / 3 governed warnings; `pip-audit` ×2 clean; Snyk Code clean at governed thresholds; Snyk SCA doc manifest 0 issues, main manifest passed with the 5 no-fix Torch advisories under EA-003's disposition | 0 (governed warnings only) |
| Benchmark regression gates | — | **not exercised** — the nightly workflow is paused (#48); audit §E8 transcribes the last pre-pause nightly | none tripped |
| New gate tests | — | **19 passed** at gate time (`tests/test_campaign_quality_gates.py`; 13 of the original 18 legs failed against pre-change config — defect-catching proof); 22 after the PR #32 round | 100% |
| `cargo doc -p prin-sim` wgpu leg (`RUSTDOCFLAGS="-D warnings"`) | exit 101 (3 unresolved intra-doc links, DV-042) | **exit 0**; cpu leg exit 0; cuda leg exit 0 | 0 warnings |
| `check_deviation_ledger.py` | 038→039: exit 0 (128 → 142 rows) | **039→040: exit 0 (142 → 146 rows)** | pass |
| Full local gate (pytest+cov, cargo matrix, audits, Sphinx, governance) | PSR-039 §7 | **Executable checks PASS; coverage-mode attempt timed out — DV-033 OPEN.** Full pytest as above; coverage leg blocked per DV-033; evidence `EVIDENCE/ea007/verification/full-gate/` (index `GATE-STATUS.md`) | — |

## 3. Deviation ledger (cumulative)

### 3.1–3.3 (unchanged)

Sections 3.1–3.3 of PSR-039 are carried forward unchanged; see that report.
No earlier finding is reopened by this delta.

### 3.4 EA-007 corrective cumulative-ledger delta (2026-10-11 UTC)

**Cumulative ledger delta:** Inherit PSR-039 §3 (which inherits
PSR-038 §3); append four new findings and update the five existing rows
below without changing their summaries. Historical PSRs remain unchanged.

| ID | Raised (cycle) | Severity | Summary | Status | Reference |
|---|---|---|---|---|---|
| EXP001-D1-H1 | 039 | D1 | EXP-001 H1 `REFUTED` (485/504): 19 corpus cases breach registered tolerance | AMENDED | EXP-001-r1 E5 accepted 2026-09-29; all hypotheses CONFIRMED; original result immutable; PR #28 `32cfed8` |
| EXP001-D1-H2a | 039 | D1 | EXP-001 H2a `REFUTED` (897/1,000): 103 fuzz cases breach | FIXED | EXP-001-r1 E5 accepted 2026-09-29; 978 pointwise + 22 characterized, not 1,000 pointwise passes; PR #28 `32cfed8` |
| EXP001-E5-F1 | 039 | D1 | `parity` CI corpus gate does not exercise PRIN | FIXED | Real PRIN corpus/fuzz gates retained; execution is local while Plan amendment #48 suspends hosted workflows |
| S2-F3 | 039 | D4 | `#[non_exhaustive]` on `GuardPolicy` deferred | CARRIED(2) | EA-007 source re-check; API-freeze decision remains outstanding; no silent closure |
| S2-F4 | 039 | D4 | RK45/Exponential/Jacobian guard clamp | CARRIED(2) | EA-007 source/doc re-check; documented and regression-pinned; existing future-WP disposition retained |
| EA007-E-F1 | EA-007 | D3 | Campaign analysis quality gates omit record roots and Bandit substring exclusions mask their source | FIXED | DV-040 option (a); workflow/local gates and non-vacuous discovery tests; EXECUTIVE_AUDIT_REPORT_007.md |
| EA007-E-F2 | EA-007 | D3 | Non-CUDA prin-sim documentation links to absent CUDA-only exports | FIXED | DV-042 cfg-gated module prose; warning-as-error wgpu/cpu/cuda checks; EXECUTIVE_AUDIT_REPORT_007.md |
| EA007-E-F3 | EA-007 | D4 | Readiness registers omit post-PSR-039 closures and the local-validation regime | FIXED | EA-007 dated deltas, issued PSR-040, closure indices and append-only register dispositions; EXECUTIVE_AUDIT_REPORT_007.md |
| EA007-E-F4 | EA-007 | D2 | `urllib3` 2.7.0 doc-build requirement carried three published advisories (CVE-2026-97687/-88/-89) | FIXED | Floor raised to `urllib3>=2.8.0`; venv upgraded 2.7.0→2.8.0; scoped Snyk SCA + pip-audit rescans clean; regression pin test; EXECUTIVE_AUDIT_REPORT_007.md |

## 4. Plan amendments this cycle

None adopted this cycle. Plan amendment #48 (local-validation regime) applies
verbatim; recorded maintainer approval
(`EVIDENCE/ea007/readiness-state.json`, MichaelMaillet, 2026-10-11 UTC):

> "I approve whatever you need to do, you have full access. keep in mind, we
> are no longer running github hosted checks, that is on pause until further
> notice. in the meantime we will run local equivequivalent checks. complete
> your tasks with that in mind."

| Amendment | Plan/standard section | Rationale | Approved by |
|---|---|---|---|
| — | — | No new plan amendment this cycle | — |

## 5. Risks and blockers

- **DV-033** — Python per-change coverage remains open; both 30-minute
  pytest attempts timed out at different nodes, cause not established;
  hosted Codecov upload is paused. Rust coverage is separate and does not
  close DV-033.
- **DV-034** — one online GPU runner (`PRIN-GPU-Runner`, online/idle at
  observation) remains a single point of failure; the required-check rule
  stays paused under #48.
- **DV-036** — `DV036-F5` at session 0166 and the reference-host re-baselines
  before 0168/0173, plus EXP-004+ hardware gates, are downstream and
  deliberately not actioned by this readiness audit.
- **S2-F3 / S2-F4** — carried a second cycle (see §3.4); API-freeze and
  future-WP dispositions retained.
- **Native push protection** remains disabled (pre-existing, flagged at #48);
  the full-history local secret scan (pinned, checksum-verified gitleaks
  8.30.1, session-local) completed — 704 commits scanned, **no leaks found**
  (historical: base `fdd28d88`, before any commit of this PR existed).
  Post-commit scans, preserved in `EVIDENCE/ea007/verification/post-commit/`:
  706 commits @ `0738714` and **707 commits @ `add7386a`**
  (2026-10-11T06:47:37Z, 76.07 MB, **no leaks**, exit 0) — each result is about
  the commit it names. The PR #32 review-round commit that follows `add7386a`
  has a staged-diff scan (leg L18 of
  `EVIDENCE/ea007/verification/pr32-review/pr32-gate-run.log`) and a post-commit
  full-history scan reported in the PR description (a document cannot contain
  the result of a scan of itself); any further commit needs its own rescan.
- **Linux/macOS and the three-OS wheel matrix** stay suspended, not
  satisfied (DoD items 2 and 4 remain open until the regime lifts).

## 6. Next work package declaration

No new WP is declared. Session **0159 (EXP-002 E1) remains READY** and is the
next action. E1 carries DV-040 option (a) gate coverage for campaign record
roots; campaign plan §12 item 3 requires the historical merge SHA
(`32cfed8a0b4d915a04e18efbfadd146a2ecb7e32`) plus verbatim checker output at
entry (already captured: `EVIDENCE/ea007/exp001-r1-merge-ci-green.log`).
E1 must honor the `EXP-001-r1` report §9 item 11 histogram caution
(216 retained comparator records vs 72 per-case worst values in field names);
reconciled artefact counts: 14 figures × 2 formats + 11 tables = 39 generated
files, paper manifest 172 records, `__all__` 175 PRIN vs 172 reference
symbols, `seed_key` 2, budgets CPU ≤ 12 h / GPU ≤ 2 h / CI ≤ 2 h / tracked ≤
10 MiB — the CI budget is not permission to run hosted workflows during the
pause.

## 7. Verification

Executed: every leg of the single full local gate for EA-007 completed
(lint, format, types, docstring coverage, bandit, cargo fmt/clippy/test
matrix, cargo llvm-cov, audits, Snyk Code/SCA, gitleaks, Sphinx, governance
checkers), including the final uninterrupted full pytest — **5,667 passed /
184 skipped / 0 failed / 61 warnings in 1,782.21 s (exit 0)**; the
coverage-mode attempt exhausted its bound and is reported blocked per
DV-033, not failed.
Per-command logs (command/host/UTC, and in most the SHA and exit code) are
committed under `EVIDENCE/ea007/verification/` with a status index
(`full-gate/GATE-STATUS.md`) and a SHA-256 inventory (see
`EVIDENCE/ea007/verification/README.md` and `SHA256SUMS.txt`); the scratch
originals in the gitignored `DOCS/test_and_benchmark_results/ea007/` are
local to the maintainer workstation and are not part of the record. See §5 for
retained open items and `DOCS/audits/EXECUTIVE_AUDIT_REPORT_007.md` for the
audit record.
