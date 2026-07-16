# PRIN Audit Report — Cycle NNN / WP-NNN

**Date:** YYYY-MM-DD
**Auditor:** <AI pair (Cascade) / maintainer name>
**Scope:** WP-NNN "<title>" — <files/crates/modules audited>
**Sessions:** <S1 global ID> implementation; <S2 global ID> this audit
**Active brief:** `DOCS/sessions/phase-N/NNNN-wpNNN-s2-<slug>.md`
**Git state:** <branch> @ <SHA>
**Verdict:** <PASS | PASS-WITH-FINDINGS | FAIL>

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅/⚠️/❌ | |
| Plan/architecture conformance (A2) | ✅/⚠️/❌ | |
| Tests in tandem + coverage (A3) | ✅/⚠️/❌ | e.g. "coverage 96.4% on new code" |
| Numerical parity + invariants (A4) | ✅/⚠️/❌ | |
| Quality gates (A5) | ✅/⚠️/❌ | fmt/clippy/ruff/mypy outputs |
| Security (A6) | ✅/⚠️/❌ | bandit/ruff-S/cargo-audit/pip-audit |
| Docstring/doc coverage (A7) | ✅/⚠️/❌ | interrogate %, missing_docs |
| Repository hygiene (A8) | ✅/⚠️/❌ | TODO/stub scan, `__all__` |
| CI status (A9) | ✅/⚠️/❌ | |
| Artefact trail (A10) | ✅/⚠️/❌ | |

## 2. Methodology

Commands executed and environments used (paste actual invocations and key
output lines — every claim must be evidence-backed):

```bash
# example
cargo clippy --workspace --all-targets -- -D warnings
pytest tests/ -v -m "not slow and not gpu" --cov=prin
interrogate -c pyproject.toml python/prin
```

## 3. Detailed findings

### 3.1 <checklist dimension>

<narrative, with file/line citations and command evidence>

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WPNNN-F1 | D1–D4 | `path/file.rs:123` | | Plan §… / Standard §… | |

## 5. Deviation-ledger delta

New findings added to the ledger: <IDs>. Carried findings re-inspected:
<IDs + status>.

## 6. Verdict and required actions

<verdict rationale; ordered S3 work list>

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WPNNN-F1 | FIXED / AMENDED / CARRIED(1) | `<sha>` / plan §… | |

**Delta re-audit date:** YYYY-MM-DD — **Result:** CLEAN / findings remain
