# Session-0159 full-gate — status matrix

Honest per-leg status for the E1 local validation campaign. Source HEAD for
all recorded legs: `78590305e1c0a78d92153ef2a55a9e76aeb7af79` (baseline
`da53ea11…`); driver/test corrections applied as an uncommitted working diff
— see `correction-source-hashes.txt` for the exact working-tree digests.

## Legs

| Leg | Check | Result |
|---|---|---|
| 01–06 | ruff check / format (repo, experiments), mypy strict ×3 | PASS (exit 0 each) |
| 07 | interrogate `python/prin` | PASS |
| 08 | bandit `python/prin` + `DOCS/experiments` (nonzero LOC) | PASS |
| 09 | pytest fast (`not slow and not gpu`) | FAILED — nonzero exit (process-level fault during run; see log) |
| 09b | isolated crash-diagnostic reruns | PASS (informational; not a substitute for the leg) |
| 09c | pytest fast rerun | EXIT 1 — 3671 passed, 178 skipped, 55 deselected, 1 failed (`test_repository_inventory_is_deterministic_and_separates_archive`; scanned-population change mid-test — see `09c-inventory-failure-facts.md`) |
| 09d | isolated inventory-test rerun | PASS (informational; not a substitute for the leg) |
| 10–12 | cargo fmt --check, clippy, clippy strict-checks | PASS |
| 13–14 | cargo test workspace, strict-checks | PASS |
| 15–17 | cargo llvm-cov kernels/dynamics/dynamics-strict | PASS (TOTAL recorded; not a new ≥95% changed-line claim — Rust unchanged) |
| 18–19 | cargo doc workspace, prin-sim cpu | PASS |
| 20 | cargo audit | PASS — exit 0, 3 pre-existing governed advisories (bincode/paste/chacha), no new suppressions |
| 21–22 | pip-audit `.` and sphinx requirements | PASS — exit 0 each |
| 23 | Snyk Code (initial scope) | PASS — 0 issues at medium threshold |
| 24 | gitleaks full-history on 7859030 | EXIT 1 — exactly 1 finding: `EVIDENCE/0159/entry-state.json` generic-api-key line 87; identified as the noncredential `reference_api_sha256` checksum. **Exception PENDING explicit maintainer approval; no `.gitleaksignore` change made.** |
| 24b | Snyk Code, corrected 3-file scope (sast-input-c) | PASS — 0 issues at medium threshold; copy attestation recorded |
| 24c | Snyk Code, final frozen test source (sast-input-d) | PASS — 0 issues at medium threshold; copy attestation recorded |
| 25 | pytest full (`tests/ parity/ --cov=prin`) | **INCOMPLETE — unknown exit**; raw capture ends at 53% with no exit trailer; cause not attributed (see `25-pytest-full-resumption-note.md`) |
| c01–c04 | focused correction pytest iterations | c01–c02 failed runs preserved (test-fixture defects, fixed); c04 PASS — 255 tests, driver coverage 99.61% |
| c05 | focused combined gate, final frozen test source | FAILED (exit 1) — 253 passed, 3 pre-packaging manifest-completeness failures, 3 warnings; driver coverage 99.61%. Preserved, not relabeled as a pass. |
| Post-packaging manifest check | `tests/test_0159_manifest.py` | 17 passed after the bundle/index was completed; a separate scope, not a rewritten c05 result. |
| Sphinx html build | **PENDING** (required once in final pass on clean source) |
| Governance battery (deviation ledger, DV gates, session registration, skipif probes, wp001 check) | **PENDING** on clean source |
| Full pytest final run | **PENDING** — must log outside repo, no in-repo writes during run |

## Standing constraints

- GitHub hosted workflows: **PAUSED** (amendment #48); Linux/macOS/wheel
  matrix: suspended; push protection: disabled on this path — no hosted or
  platform claims are made.
- Protocol remains `DRAFT`; no EXP-002 execution, no real inputs, no RUN
  directories; E1 status `IN_PROGRESS`.
- Coverage admission: driver-focused 99.6%+ applies to the changed driver
  scope only; DV-033 remains OPEN.
