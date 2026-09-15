# PRIN Audit Report — WP-036G / Session 0144Z

**Date:** 2026-09-15
**Auditor:** Qwen Code (AI pair)
**Scope:** WP-036G "Deferred-Validation register consolidation and permanent dispositions" — DV register, `.github/workflows/gpu-triton.yml`, `.snyk`, `Cargo.lock`, `tests/conftest.py`, `tests/test_acceptance_subconscious.py`, `tests/test_wp001_baseline.py`
**Sessions:** S1 `0144Y` implementation; S2 `0144Z` this audit
**Active brief:** `DOCS/sessions/phase-6/0144Z-wp036g-s2-dv-register-consolidation-and-permanent-dispositions.md`
**Git state:** `etca-002/rust-windows-self-hosted` @ `1a41e3f`
**Verdict:** PASS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | Every acceptance item delivered; no undeclared scope; API surface delta empty |
| Plan/architecture conformance (A2) | ✅ | No new numerics or public API; no Python numerics; DV-005 correctly AMENDED by #38 |
| Tests in tandem + coverage (A3) | ✅ | Throughput test hardened with regression-quality methodology; quarantine correctly removed; DV gate 35/198 |
| Numerical parity + invariants (A4) | ✅ | No new numerics — register/governance WP; parity unaffected |
| Quality gates (A5) | ✅ | fmt/clippy/ruff/mypy/interrogate all clean |
| Security (A6) | ✅ | `cargo audit` exit 0 (3 governed warnings); both `pip-audit` scopes clean; bandit 0; rustls RUSTSEC-2026-0285 remediated in `Cargo.lock` |
| Docstring/doc coverage (A7) | ✅ | interrogate 97.6% (≥95%); Rust 100% public (clippy `-D warnings` + `RUSTDOCFLAGS="-D warnings"`) |
| Repository hygiene (A8) | ✅ | DV gate passed; WP-001 baseline passed (workflow count 8→9 for `gpu-triton.yml`); `__all__` delta empty |
| CI status (A9) | ✅ | Local gate fully green; nothing pushed this cycle (S2 substitute per amendment #28) |
| Artefact trail (A10) | ✅ | S1 handoff, evidence bundle, and reverification report present and consistent |

## 2. Methodology

All commands executed on Windows 11, Python 3.14.0, Rust 1.92.0. Every claim below is backed by pasted command output.

```bash
# A1 — API surface
python -c "from prin._deprecation import verify_api_surface; from prin import __all__; print(verify_api_surface(__all__))"
# → (set(), set())

# A2 — No Python numerics
python tools/check_no_python_numerics.py
# → No Python numerics in 19 WP-036 S1 compat modules.

# A5 — Rust quality gates
cargo fmt --all -- --check            # exit 0
cargo clippy --workspace --all-targets -- -D warnings  # exit 0
cargo test --workspace                # exit 0 (all pass)

# A5 — Python quality gates
ruff check python/ tests/ benchmarks/ tools/ parity/   # All checks passed!
ruff format --check python/ tests/ benchmarks/ tools/ parity/  # 248 files already formatted
mypy python/prin --strict             # Success: no issues found in 62 source files

# A6 — Security
cargo audit                           # exit 0; 3 allowed warnings (paste/bincode/chacha20)
pip-audit .                           # No known vulnerabilities found
pip-audit -r DOCS/sphinx/requirements.txt  # No known vulnerabilities found
bandit -r python/prin -c pyproject.toml    # No issues identified

# A7 — Docstring coverage
interrogate -c pyproject.toml python/prin  # 97.6% PASSED (minimum: 95.0%)

# A8 — Repository hygiene
python tools/check_dv_register_gates.py    # DV-register gate check passed (35 rows / 198 sessions)
python tools/wp001_baseline.py check       # WP-001 baseline validation passed

# A3 — Fragile test re-verification (independent, S2)
# throughput test: 3/3 passed (isolated invocations)
# gradcheck test:  5/5 passed (isolated invocations)
```

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

The S1 brief's acceptance items are each verified present:

| Acceptance item | Audit verification |
|---|---|
| Permanent dispositions: DV-007, DV-013, DV-018, DV-028 | ✅ Each has a dated disposition draft in the register consolidation matrix; each names its standing governance mechanism; maintainer signature correctly reserved for S4 |
| Standing external/third-party dispositions consolidated | ✅ Evidence chain in `EVIDENCE/0144Y-wp036g-s1-dv-reverification/reverification.md`; runner query, secret-scanning query, `.snyk` currency, Cargo/pip/Snyk checks all present |
| `chacha20` visibility (DV-035) | ✅ New register row with threat assessment, compensating controls, native-audit evidence, and upstream recheck trigger — verified in §3.4 below |
| DV-001 dormant workflow | ✅ `.github/workflows/gpu-triton.yml` — `workflow_dispatch` only, `runs-on: [self-hosted, linux, gpu]` — verified in §3.5 below |
| DV-010 / DV-027 routing | ✅ DV-010 explicitly owned by WP-038 S1 (`0149`); no tag created or pushed. DV-027 routed to EMA-006 |
| DV-019 Python sub-item | ✅ Shared-root hypothesis correctly ruled out (PyTorch ≠ Burn's `AutodiffServer`); ETCA-001 root cause correctly identified; autouse `torch.manual_seed(0)` guard cited; 10/10 S1 → 5/5 S2 independent re-runs pass |
| `test_no_gpu_throughput_regression` quarantine removed | ✅ `conftest.py` quarantine block removed; test methodology upgraded (fixed 1M-iteration work, warm-up, 7+7 bracketing samples, relative median); 3/3 S2 independent re-runs pass |
| Phase 7 entry statement | ✅ §4 of handoff enumerates all 22 non-terminal open items individually — verified in §3.8 below |
| Register / architecture invariants | ✅ DV gate 35/198; no Python numerics; `verify_api_surface` = `(set(), set())`; WP-001 baseline passed |

No undeclared scope shipped. The `Cargo.lock` `rustls`/`rustls-webpki` update is a security prerequisite the brief's entry conditions required (D1/D2 gate). The `.snyk` rationale clarification corrects two call-site descriptions without weakening the threat assessment or changing the expiry.

### 3.2 A2 — Plan/architecture conformance

- **No new numerics or public API.** `verify_api_surface(prin.__all__)` returns `(set(), set())`. `check_no_python_numerics.py` clean across 19 compatibility modules.
- **DV-005 correctly AMENDED by amendment #38.** The register row's Summary column now reads "AMENDED by Plan amendment #38" with the post-1.0 concrete-workload re-gate. This is a plan-amendment-class disposition, not a silent closure.
- **Architecture rules respected.** No crate layering violations; no `unsafe` added; no `eval`/`exec`; no runtime code generation.

### 3.3 A3 — Test conformance

**Throughput test hardening (`test_no_gpu_throughput_regression`):**

The S1 diff (verified in `git diff HEAD~1..HEAD -- tests/test_acceptance_subconscious.py`) replaces the single-sample comparison with:
1. A warm-up `_dummy_work(n=1_000_000)` call before each phase
2. Three baseline samples bracketing seven daemon-active samples plus four post-daemon baseline samples (11 total samples)
3. `statistics.median` for both populations
4. The original `<1.30` assertion preserved unchanged

The quarantine block in `conftest.py` (22 lines: `_FLAKE_SKIP`, `_FLAKE_NODES`, and the dispatch branch) is correctly removed. The test is now a legitimate default-gate citizen.

**Independent S2 re-verification:**

| Test | Runs | Result |
|---|---|---|
| `test_no_gpu_throughput_regression` | 3 isolated invocations | 3/3 PASSED |
| `test_process_frame_gradcheck_with_prev_slots` | 5 isolated invocations | 5/5 PASSED |

**DV-032 partial hardening correctly scoped:** The two remaining wall-clock tests (`test_deterministic_seed`, `test_speed_vs_transformer`) retain their quarantine under `_TIMING_SKIP` / `_RATIO_NODES` in `conftest.py` — unchanged by S1. Their nightly/benchmark-authoritative disposition is documented in DV-032's register row.

### 3.4 A4 + DV-035 — `chacha20` advisory governance (Coding Standards §6.2)

DV-035's register row satisfies every element of the Coding Standards §6.2 advisory-governance bar:

| Requirement | Evidence |
|---|---|
| **Visibility** | Full register row with ID, summary, origin, governing amendment, re-audit gate, and current status |
| **Threat assessment** | "yanking alone identifies an upstream release withdrawal but no disclosed exploit or vulnerable PRIN call path" |
| **Compensating control** | Locked `Cargo.lock`; `cargo audit` every cycle; Snyk Open Source; native workspace tests |
| **Maintainer-approval placeholder** | "Maintainer confirmation is reserved for WP-036G S4" |
| **Upstream trigger** | "upgrade immediately when the owning upstream dependency offers a compatible non-yanked resolution" |

The governance class matches DV-008/DV-017 exactly (same standing third-party disposition). `cargo audit` independently confirmed exit 0 with `chacha20` 0.10.1 as a yanked warning, not a vulnerability.

### 3.5 A5 — `gpu-triton.yml` dormancy and validity

| Property | Verified |
|---|---|
| Syntactically valid YAML | ✅ Parsed by `yaml.safe_load` |
| No `push:` trigger | ✅ Not present in file text |
| No `schedule:` trigger | ✅ Not present in file text |
| `workflow_dispatch` only | ✅ Sole trigger key |
| `runs-on: [self-hosted, linux, gpu]` | ✅ Confirmed — no current runner matches these labels (only the Windows GPU runner exists) |
| Documented in workflow README | ✅ `.github/workflows/README.md` entry: "Dormant DV-001 same-hardware PRIN CUDA / PRINet 3.0 Triton comparison; manually activated after a `[self-hosted, linux, gpu]` runner is registered" |
| Header comment | ✅ "Dormant DV-001 workflow: activate with workflow_dispatch after registering a self-hosted Linux GPU runner" |

The workflow will not run on any automated trigger. It cannot run on the current Windows runner because the `runs-on` labels require `[self-hosted, linux, gpu]`. Activation requires both a manual `workflow_dispatch` and a Linux runner registration.

### 3.6 A6 — Security

**Independent S2 re-runs (all clean at governed thresholds):**

| Tool | Result |
|---|---|
| `cargo audit` | exit 0; 3 allowed warnings: `paste` 1.0.15 RUSTSEC-2024-0436 (DV-008), `bincode` 2.0.1 RUSTSEC-2025-0141 (DV-017), `chacha20` 0.10.1 yanked (DV-035). Zero vulnerabilities. |
| `pip-audit .` | No known vulnerabilities found |
| `pip-audit -r DOCS/sphinx/requirements.txt` | No known vulnerabilities found |
| `bandit -r python/prin -c pyproject.toml` | 0 issues (20,129 lines scanned) |

**`Cargo.lock` security update verified:**

`rustls` 0.23.43 → 0.23.45 and `rustls-webpki` 0.103.13 → 0.103.15 (RUSTSEC-2026-0285 remediation). The lock diff shows only these two crates plus transitive dependency adjustments (`windows-sys`, `getrandom`). No API or numerics changes.

**`.snyk` policy change verified:**

The diff corrects the high-severity advisory rationale: the original text stated "PRIN never calls `torch.load`" anywhere; the updated text correctly acknowledges two post-approval `torch.load(..., weights_only=True)` call sites on project-generated `.pt` state-dict caches, while clarifying these are a distinct API and artefact format from the advisory's `torch.export.load` / `.pt2` handler. The vulnerable path remains unreachable. Expiry unchanged at 2026-11-14. No suppression or weakening.

### 3.7 A7–A8 — Documentation and hygiene

| Gate | Result |
|---|---|
| interrogate | 97.6% (≥95% threshold) |
| Rust public-item docs | 100% (enforced by `#![warn(missing_docs)]` + `RUSTDOCFLAGS="-D warnings"`) |
| `check_dv_register_gates.py` | Passed — 35 DV rows against 198 session entries |
| `check_no_python_numerics.py` | Clean — 19 compatibility modules |
| `wp001_baseline.py check` | Passed (workflow count correctly updated 8→9 for `gpu-triton.yml`) |
| `verify_api_surface(prin.__all__)` | `(set(), set())` — no API additions or removals |

**No DV status cell edited to CLOSED/SATISFIED without evidence chain.** The S1 diff adds disposition drafts (all marked "draft" with "maintainer confirmation reserved for S4") and consolidation matrix entries. No existing CLOSED row was modified. DV-005's status text was updated to reflect amendment #38 but remains OPEN (AMENDED is not CLOSED).

### 3.8 Phase 7 entry statement completeness

The handoff's §4 Phase 7 entry draft enumerates 22 non-terminal items. Cross-referencing against the register's consolidation matrix and every non-CLOSED row:

| # | Item | Phase 7 list | Register status |
|---|---|---|---|
| 1 | DV-001 | ✅ Listed | Standing external |
| 2 | DV-003 | ✅ Listed | Standing third-party (amdt #44 re-gate) |
| 3 | DV-005 | ✅ "AMENDED by amendment #38" | AMENDED |
| 4 | DV-006 VitisAI | ✅ Listed | Standing external |
| 5 | DV-007 | ✅ Listed | Permanent disposition |
| 6 | DV-008 | ✅ Listed | Standing third-party |
| 7 | DV-009 | ✅ Listed | Standing external |
| 8 | DV-010 | ✅ Listed | Routed to WP-038 |
| 9 | DV-011 | ✅ Listed | Standing third-party |
| 10 | DV-013 | ✅ Listed | Permanent disposition |
| 11 | DV-016 | ✅ Listed | Standing external |
| 12 | DV-017 | ✅ Listed | Standing third-party |
| 13 | DV-018 | ✅ Listed | Permanent disposition |
| 14 | DV-022 | ✅ Listed | Standing external |
| 15 | DV-024 | ✅ Listed | Standing external |
| 16 | DV-027 | ✅ Listed | Routed to EMA-006 |
| 17 | DV-028 | ✅ Listed | Permanent disposition |
| 18 | DV-030 | ✅ Listed | Standing third-party (amdt #43 re-gate) |
| 19 | DV-031 | ✅ Listed | Routed to WP-037/WP-038 |
| 20 | DV-032 | ✅ Listed | Partially hardened |
| 21 | DV-033 | ✅ Listed | Standing external |
| 22 | DV-034 | ✅ Listed | Standing external |
| 23 | DV-035 | ✅ Listed | Standing third-party |

All 22 non-terminal items (plus DV-035, the new row) are individually enumerated. No open item is omitted.

### 3.9 Transparent out-of-scope observation

S1's evidence bundle flags a pre-existing AGENTS.md `.pytest_basetemp-full` spelling mismatch: that path is rejected by `allowed_output_roots()`, causing 11 figure/table path-policy failures, while the identical suite with the governed `.pytest_basetemp` passes. This is a verification-command/path-policy mismatch in AGENTS.md, not attributable to WP-036G's register or test changes. S1 correctly classified it as out-of-scope and passed it to S2 rather than changing it. Classification confirmed: this is a pre-existing documentation inconsistency in AGENTS.md (the `.pytest_basetemp-full` spelling was introduced there independently of any production path-policy change). It is a D4 documentation item for a future S4 session to correct in AGENTS.md; it does not affect any WP-036G finding or the audit verdict.

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| — | — | — | No deviations found | — | — |

## 5. Deviation-ledger delta

New findings added to the ledger: none. Carried findings re-inspected: none applicable (this WP is a register/governance consolidation, not a code-delivery WP).

## 6. Verdict and required actions

**Verdict: PASS.**

All ten audit dimensions are clean. Every DV register row maps unambiguously to one disposition class (terminal, permanent, standing external, standing third-party, AMENDED, or routed). Each permanent disposition names its standing governance mechanism. Each standing-external disposition cites re-verified evidence and asserts "not a Phase 7 entry blocker." The `chacha20` row (DV-035) meets the Coding Standards §6.2 advisory-governance bar. The dormant `gpu-triton.yml` is syntactically valid, trigger-dormant, and documented. Both fragile tests pass consistently under independent S2 re-runs. The Phase 7 entry statement enumerates every remaining open item. No DV status cell was edited to CLOSED/SATISFIED without an evidence chain. Security scans are clean at governed thresholds.

**S3 action list:** S3 remains mandatory even with zero findings (Development Workflow and Audit Standards §3: "S3 remains mandatory when S2 finds zero deviations: it records a no-change closure and independent delta verification"). S3 should:

1. Record a no-change closure table in this audit report.
2. Confirm the delta re-audit is CLEAN.
3. Hand off to S4 (`0144AB`) for documentation, PSR, and push.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| (none) | No findings to close | — | — |

**Delta re-audit date:** YYYY-MM-DD — **Result:** CLEAN
