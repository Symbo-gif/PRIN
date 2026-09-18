# PRIN Project State Report — Cycle 038

**Date:** 2026-09-17
**Cycle:** 038 (WP-038 "RC1 packaging and Phase 6 gate")
**Completed sessions:** 0149 (S1), 0150 (S2), 0151 (S3), 0152 (S4)
**Author:** Qwen Code (AI pair)
**Git state:** `main` @ `233c93a` (post-EMA-007; working tree clean)

---

## 1. Current position on the planned trajectory

- **Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1. WP-038 is
  the final work package of Phase 6, responsible for RC1 packaging and the
  Phase 6 exit gate.
- **This cycle delivered:**
  - Version bump to `1.0.0-rc1` / `1.0.0rc1` across all four version sources
    (`Cargo.toml`, `pyproject.toml`, `__init__.py`, `CITATION.cff`).
  - Tag `v1.0.0-rc1` created and pushed to `origin`.
  - `release.yml` prepared with 7 crates publishing to crates.io in
    dependency order; `prin-py` excluded (`publish = false`).
  - Distribution renamed `prin` → `prin-core` (plan amendment #46) after
    discovering PyPI's `prin` is owned by an unrelated project.
  - WP038-F1/F2 (release.yml self-hosted runner `shell: bash` and Ubuntu
    disk exhaustion) FIXED; WP038-F3 (workspace dependency version pins)
    FIXED; WP038-F4 (distribution rename) AMENDED; WP038-F5/F6 (repository
    settings) routed to DV-037.
  - **Publication COMPLETED (2026-09-17):** `release.yml` run `35245682857`
    at commit `a4f90f6` succeeded — all 4 wheel jobs + sdist completed,
    `publish-pypi` uploaded `prin-core` 1.0.0rc1 to PyPI
    (https://pypi.org/project/prin-core/), `publish-crates` published all 7
    crates to crates.io at version 1.0.0-rc1.
  - DV-010 CLOSED on successful publication.
  - Post-review fixes (PR #16): code review findings from Sourcery,
    CodeRabbit, and Devin resolved (`762f4d6`).
  - EMA-007 (Phase 6 close mathematical audit): **PASS**, zero regressions
    across 59 claims, zero new D1/D2/D3 findings.
- **Plan conformance:** ON TRAJECTORY. Amendments #1–#46 remain in force.
  No new plan amendment was adopted in WP-038.
- **Audit:** `DOCS/audits/038-wp038-audit.md` — S2 verdict
  **PASS-WITH-FINDINGS** (2 D2). S3 closed all findings: F1/F2 FIXED, F3
  FIXED, F4 AMENDED (amdt #46), F5/F6 → DV-037; delta re-audit **CLEAN**.
  Publication completed after S3.
- **Session Register:** 0149, 0150, 0151, and 0152 are marked COMPLETE.
- **Phase 6 is CLOSED.** All 13 work packages (WP-033 through WP-038,
  including WP-036 sub-WPs) have completed their full S1→S4 cycles. The
  `v1.0.0-rc1` tag is pushed; `prin-core` is published on PyPI; 7 crates
  are on crates.io.

---

## 2. Metric trends

| Metric | Previous (PSR-037) | Current (PSR-038) | Gate |
|---|---|---|---|
| Rust tests passing (default) | 1,577 passed, 1 ignored | **1,577 passed, 1 ignored** (unchanged) | 100% where defined |
| Python full suite + parity | 3,496 passed, 185 skipped | **3,496+ passed** (PSR-037 S4 figures authoritative) | 100% at registered tolerance |
| Python fast suite | 2,873 passed, 178 skipped, 38 deselected | **2,873 passed** (unchanged) | 100% |
| Coverage | 95% total | **95% total** | ≥95% |
| Docstring coverage | 97.6% | **97.6%** | ≥95% overall |
| Sphinx warning-as-error build | 0 warnings | **0 warnings** | 0 warnings |
| Clippy/ruff/mypy/interrogate/bandit | 0 findings | **0 findings** | 0 |
| Snyk Code | 0 issues | **0 issues** | governed scope clean |
| Native dependency audits | cargo audit 3 governed warnings | **cargo audit exit 0** (3 governed: paste, bincode, chacha20) | governed warnings only |
| `check_dv_register_gates.py` | pass (36 rows) | **pass (37 rows / 198 sessions)** | pass |
| `check_deviation_ledger.py` | pass (128 rows) | **pass** | pass |
| `verify_api_surface` | `(set(), set())` | **`(set(), set())`** | frozen |
| Publication | not published | **`prin-core` 1.0.0rc1 on PyPI; 7 crates on crates.io** | published |

---

## 3. Deviation ledger (cumulative)

### 3.1 New findings this cycle

No new findings at S4. WP038-F1 through F6 were raised at S2/S3 and all
resolved (see `DOCS/audits/038-wp038-audit.md` §7 closure table).

### 3.2 Cumulative ledger

The cumulative table carries forward every row from PSR-037 §3 unchanged
and appends the six WP-038 rows (F1–F6, all resolved). No earlier finding
was reopened.

---

## 4. Phase 6 exit gate

**Phase 6 exit criteria (Plan §6):**

| Criterion | Status | Evidence |
|---|---|---|
| Reproducibility byte-identical | ✅ MET | `tools/reproduce.py --verify-manifest`: 172 artefacts verified, 39 files generated |
| All CI green | ✅ MET | 6/6 workflows green on HEAD (`233c93a`); ETCA-002 closure confirmed |
| `1.0.0-rc1` wheels published | ✅ MET | `release.yml` run `35245682857` at `a4f90f6`: PyPI + crates.io complete |
| Every DV item closed or dated | ✅ MET | WP-036G consolidation; every row classified, dated, dispositioned |

**Phase 6 verdict: COMPLETE.**

---

## 5. Next work package declaration

Phase 6 is complete. The next work package (WP-039 or Phase 7 WP-001) will
be declared at Phase 7 planning. No WP is declared here.

---

## 6. Risk register

No new risks. All DV items carry dated dispositions per WP-036G. The
remaining open items (DV-001 Linux Triton, DV-003 device-event timing,
DV-006 VitisAI half, DV-030 bidirectional zero-copy) are hardware/toolchain-
gated and explicitly not Phase 7 entry blockers.

---

## 7. Verification commands (S4, 2026-09-17)

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace --exclude prin-py -- --test-threads=1
# -> 1,577 passed, 0 failed, 1 ignored
cargo audit
# -> exit 0; 3 governed warnings
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
# -> 0 warnings
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
# -> all clean at governed thresholds
.venv\Scripts\python tools/check_deviation_ledger.py
.venv\Scripts\python tools/check_dv_register_gates.py
.venv\Scripts\python tools/wp001_baseline.py check
.venv\Scripts\python tools/wp036_migration_table.py check
.venv\Scripts\python tools/check_no_python_numerics.py
.venv\Scripts\python -c "from prin._deprecation import verify_api_surface; from prin import __all__; print(verify_api_surface(__all__))"
# -> all pass
```
