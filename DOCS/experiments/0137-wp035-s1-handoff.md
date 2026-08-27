# Session 0137 — WP-035 S1 handoff

**Date:** 2026-08-27
**Session:** 0137 — WP-035 S1
**Status:** S1 delivered; handoff to mandatory S2 audit (session 0138)
**Predecessor:** WP-034 S4 at PSR-034

## Mission and entry conditions

Mission: complete `tools/reproduce.py`, append-only stored-artefact handling,
SHA-256 manifest verification, and active reproduction CI without training,
GPU execution, or new scientific claims.

Entry conditions were met:

- WP-034 S4 is closed and committed; PSR-034 records a clean delta re-audit
  and no unresolved D1/D2 finding.
- The maintainer directly requested execution of session 0137, supplying the
  approval that PSR-034 §6 recorded as pending for the declared WP-035 scope,
  acceptance criteria, and non-goals.
- PSR-034 closes WP034-F1 and directs this session to read the prospective
  brief's “15 figures” as the 14 verifiable generators, figures 2–15.

## Scope decisions

1. **The pipeline uses stored data, never archived executable code.** Its
   default input is the repository-carried PRINet 3.0 JSON result directory.
   It imports only the current `prin.reporting` generators. Nothing under the
   archived reference tree is imported or executed.
2. **The current manifest supersedes the stale historical manifest as the
   reproduction integrity authority.** The archived `sha256_manifest.json`
   contains 151 entries while the stored directory currently contains 172 JSON
   files, and its listed digests do not match the current repository-carried
   bytes. `paper/artefact_manifest.json` therefore records the exact current
   172-file inventory, sizes, and full SHA-256 digests. The historical manifest
   is itself treated as one immutable input file, not trusted as current
   governance.
3. **Manifest evolution is append-only.** `append_manifest()` first verifies
   every existing record and refuses missing, resized, or modified artefacts;
   it can add only previously unmanifested JSON files. Manifest writes are
   confined to `paper/`, `benchmarks/results/`, or the operating-system
   temporary tree.
4. **Verification is fail-closed and precedes rendering.** The verifier rejects
   malformed records, duplicate/path-traversing names, missing files,
   unmanifested additions, size changes, and digest changes. CI invokes
   `--verify-manifest`, so no figure or table is generated after an integrity
   failure.
5. **Generated output stays in the governed output tree.** The default is
   `DOCS/test_and_benchmark_results/reproduction/{figures,tables}/`; the
   existing reporting layer performs symlink-resolved output confinement.

## Delivered files

| File | Delivery |
|---|---|
| `tools/reproduce.py` | Typed CLI and API for SHA-256 hashing, schema-validated manifest loading, append-only manifest extension, fail-closed exact-inventory verification, figure/table selection, generation, and deterministic generated-file checksum reporting. |
| `paper/artefact_manifest.json` | Governed 172-record manifest with byte sizes and full SHA-256 digests for every stored JSON input. |
| `tests/test_reproduce.py` | 22 tests covering the repository manifest, append-only behavior, malformed manifests, path confinement, missing/modified/unmanifested tampering, mode selection, verify-before-render ordering, CLI failure, and generated checksum output. |
| `tests/test_wp001_baseline.py` | Replaces the retired pre-WP-035 guard assertion with regression assertions that repro CI runs tamper tests and the verified pipeline. |
| `.github/workflows/repro.yml` | Removes the pre-WP-035 disabled guard, adds relevant path triggers and tamper tests, and runs full regeneration with manifest verification. |

## Acceptance-criterion evidence map

### AC1 — All verifiable figures and all tables regenerate without GPU/training

`python tools/reproduce.py --verify-manifest` verified all 172 stored JSON files
and generated 39 outputs: 28 files for all 14 verifiable figures (PDF + PNG)
and 11 LaTeX tables. A timed full run completed in **9.437 seconds** on the
project host. The command imports no training or GPU driver and samples no RNG.
Two consecutive local runs emitted identical SHA-256 values for every generated
file. `tests/test_publication_generation.py` additionally verifies all generator
keys, exact historical LaTeX bytes, and deterministic matplotlib normalization.

Result: **PASS**, applying PSR-034's governed 14-not-15 factual correction.

### AC2 — SHA-256 manifest matches

`test_repository_manifest_matches_all_stored_json_artefacts` validates every
record in `paper/artefact_manifest.json`; the production command independently
reported `Verified 172 stored JSON artefacts.` before rendering.

Result: **PASS**.

### AC3 — Tampering fails closed

`test_verify_manifest_fails_closed_on_inventory_tampering` mutates the inventory
three ways: deletion, same-size byte corruption, and unmanifested addition.
Every case raises `ManifestMismatchError`. Separate tests cover size changes,
malformed JSON/schema/digests, duplicate and traversing paths, verify-before-
generation ordering, and mutation/removal attempts during manifest append.

Result: **PASS**.

### AC4 — Reproduction CI is active

`.github/workflows/repro.yml` no longer contains `PRIN_REPRO_ENABLED` or the
pre-WP-035 guard. It runs `tests/test_reproduce.py` and then executes
`python tools/reproduce.py --verify-manifest`. The updated WP-001 workflow
regression test passes.

Result: **PASS locally**. Per plan amendment #28, S1 does not push; live CI is
therefore deferred by governance to the cycle-closing S4 push, not claimed here.

## Parity-evidence disposition

Directly comparable PRINet 3.0 reference material exists and was checked:

- historical `reproduce.py`;
- stored `benchmarks/results/*.json` artefacts;
- `utils/figure_generation.py` / `utils/table_generation.py` contracts; and
- stored `paper/figures/fig2`–`fig15` and `paper/tables/tab_*.tex` outputs.

WP-035 adds orchestration, integrity validation, and CI activation only. It
introduces no oscillator equation, numerical primitive, kernel, optimizer,
gradient, stochastic process, or scientific result. Numerical parity,
gradcheck, property, and kernel-equivalence tests are therefore not applicable
to the changed behavior; exact manifest checks, stored-output comparisons, and
tamper tests are the applicable golden evidence.

## Coverage and verification evidence

Commands executed on Windows 11 / Rust 1.92.0 / Python 3.14.0:

```powershell
.venv\Scripts\python -m pytest tests/test_reproduce.py --cov=tools.reproduce --cov-report=term-missing --basetemp=.pytest_basetemp-wp035-repro -q
# 22 passed; tools/reproduce.py 100% (161 statements, 0 missed)

.venv\Scripts\python -m pytest tests/test_reproduce.py tests/test_wp001_baseline.py tests/test_publication_generation.py --cov=tools.reproduce --cov-report=term-missing --basetemp=.pytest_basetemp-wp035-targeted-final -q
# 79 passed; tools/reproduce.py 100%

.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp-wp035-fast-final -q
# 718 passed, 9 deselected; prin 99%

.venv\Scripts\python -m pytest tests/ parity/ --basetemp=.pytest_basetemp-wp035-full-retry -q
# 1319 passed

.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
# All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
# 127 files already formatted
.venv\Scripts\mypy python/prin --strict
# 33 files, 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
# 95.6% (351/367), PASS

cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
# All exit 0; one established expensive Rust test ignored
```

The first full Python-suite run had one unrelated, unseeded
`TestPhaseTrackerStatic.test_encode_gradcheck` Jacobian mismatch after the
benchmark-heavy portion of the process. The test passed immediately in
isolation, and a complete clean rerun then passed all 1,319 tests. No assertion,
tolerance, or source code was changed. This pre-existing nondeterministic test
input is recorded below for independent S2 disposition rather than silently
folded into WP-035.

## Security evidence

| Scan | Scope | Threshold/result |
|---|---|---|
| Snyk Code | `tools/reproduce.py` | Low; 0 issues |
| Snyk Code | `tests/test_reproduce.py` | Low; 0 issues |
| Snyk Code | `tests/test_wp001_baseline.py` | Low; 0 issues |
| Bandit | `tools/reproduce.py` | 0 issues |
| Bandit defense in depth | Whole repository | Two pre-existing Low `assert` findings in `EVIDENCE/math-audit/manual/mf9-beta-allowlist-verification.py`; no changed-file finding |
| `cargo audit` | `Cargo.lock` | Exit 0; only governed DV-008/DV-017 warnings |
| `pip-audit` | Project and Sphinx requirements | 0 vulnerabilities in both scans |

No dependency manifest or resolved lock file changed, so a change-attributable
Snyk Open Source scan is not applicable. GitHub secret scanning availability is
unchanged from PSR-034; amendment #5's full-history Gitleaks and protected-branch
substitute remains the authoritative hosted control.

## Out-of-scope discoveries

1. `tests/test_train_bridge_ablation.py::TestPhaseTrackerStatic::test_encode_gradcheck`
   creates an unseeded random input and produced one non-repeating gradcheck
   failure during the first full-suite run. The complete rerun passed. This is
   unrelated to reproduction-pipeline scope and is handed to S2 for severity
   and disposition under Testing Standards §1 determinism requirements.
2. Scientific benchmark re-measurement and interpretation remain outside
   WP-035 and are not performed.
3. The Project State Report and cumulative deviation ledger remain unchanged in
   S1. They are S4 and audit/remediation artefacts respectively; this handoff
   records the only discovered candidate for S2 review without pre-judging it.

## Handoff to S2

Recommended audit focus:

1. Independently verify all 172 current manifest records and all 39 outputs.
2. Repeat missing, modified, resized, and unmanifested-file tamper cases and
   confirm rendering never begins after verification failure.
3. Review append-only semantics and manifest-output confinement for traversal,
   symlink, and replacement hazards.
4. Confirm the pipeline reads archived JSON data but imports/executes only
   current `prin.reporting` code.
5. Review the 14-vs-15 disposition against PSR-034/WP034-F1.
6. Disposition the observed pre-existing unseeded gradcheck anomaly without
   expanding WP-035 S1 scope retroactively.
