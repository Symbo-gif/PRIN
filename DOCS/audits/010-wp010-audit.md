# PRIN Audit Report — Cycle 010 / WP-010

**Date:** 2026-08-08
**Auditor:** Qwen Code (AI pair)
**Scope:** WP-010 "Phase metrics and chimera measures" — `crates/prin-metrics` (`lib.rs`, `error.rs`, `order.rs`, `coherence.rs`, `spectral.rs`, `energy.rs`, `chimera.rs`, `metastability.rs`, `knn.rs`; integration tests `tests/parity_metrics.rs`, `tests/parity_chimera.rs`, `tests/corpus_metrics.rs`; fixtures `tests/data/*.json`), workspace `Cargo.toml`/`Cargo.lock` (rustfft), S1 handoff note
**Sessions:** 0037 (S1 implementation); 0038 (S2 this audit)
**Active brief:** `DOCS/sessions/phase-1/0038-wp010-s2-phase-metrics-and-chimera-measures.md`
**Git state:** `feat/wp006-oscillator-state` @ `0909691`
**Verdict:** PASS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | All declared metrics present (order parameters, coherence full+sparse, PSD+concept probabilities, synchronization energy full+sparse, local order, bimodality, SI, discontinuity, chimera index, temporal SI, metastability, k-NN wrapper); non-goals respected (no tensor decompositions, no report generation, no Python changes); no undeclared files |
| Plan/architecture conformance (A2) | ✅ | Numerics in Rust f64; `#![forbid(unsafe_code)]` preserved; no Python numerics (`python/prin` untouched); no RNG anywhere (pure deterministic metrics); k-NN index delegates to `prin-dynamics` (one algorithm, one implementation); crate layering `metrics → dynamics` per plan §4.5 |
| Tests in tandem + coverage (A3) | ✅ | 145 new tests in the same commit as the code (104 unit/property + 22 parity/corpus + 19 doctests); coverage lines 99.53% / regions 96.28% / functions 100% (gate metric is line coverage, Testing Standards §4); no ignored or weakened tests |
| Numerical parity + invariants (A4) | ✅ | Independently reproduced: fixture arrays bit-identical to the golden corpus; first-principles numpy recomputation drift ≤ 1.62e-15 (target rtol=1e-10); `prinet==3.0.0` re-run regenerates every embedded reference at drift 0.0; R ∈ [0,1] and C ∈ [−1,1] hold on all 126 corpus snapshots; sparse/full agreement verified independently |
| Quality gates (A5) | ✅ | `cargo fmt --check`, clippy `-D warnings` (default + `strict-checks`), ruff check + format, mypy `--strict` all clean (re-run by this audit) |
| Security (A6) | ✅ | No `unsafe` (only `#![forbid(unsafe_code)]`); bandit 0; Snyk Code 0 issues on `crates/prin-metrics/src`; `cargo audit` only inherited `paste` RUSTSEC-2024-0436 (amendment #9); `pip-audit` clean ×2; Snyk SCA covered by the green CI `snyk` workflow on the S1 SHA (local SCA blocked per EA-002); rustfft 6.4.1 introduced no advisories |
| Docstring/doc coverage (A7) | ✅ | Rustdoc 100% public (`#![warn(missing_docs)]` + `-D warnings` doc build clean); interrogate 100% (104/104, Python unchanged); 19 executable doctests; Sphinx `-W --keep-going` build clean |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/HACK/stub markers; no orphan files; gitignore respected (working tree clean after full gate run); `tools/wp001_baseline.py check` passes |
| CI status (A9) | ✅ | All workflows green on S1 SHA `0909691`: parity ✓, rust ✓, python ✓, repro ✓, snyk ✓; gpu skipped (no runner) |
| Artefact trail (A10) | ✅ | Cycle-009 audit report (CLEAN closure) and `009-project-state.md` (declares WP-010, maintainer approval recorded) exist; session register 0037 READY / 0038–0039 PLANNED; S1 handoff note committed at `DOCS/experiments/0037-wp010-s1-handoff.md` |

## 2. Methodology

Commands executed by this audit on `feat/wp006-oscillator-state` @ `0909691`
(Windows, Python 3.14.0 venv `.venv`, `prinet==3.0.0`, `torch==2.13.0+cpu`;
every claim below is evidence-backed):

```powershell
# Scope and diff inspection
git status --short                                        # clean
git log -n 8 --oneline                                    # HEAD = 0909691 (S1)
git show 0909691 --stat                                   # 19 files, +6332/-8, all in declared scope
git show 0909691 -- Cargo.toml crates/prin-metrics/Cargo.toml  # rustfft 6.2 workspace dep + serde_json dev-dep only
git show 21c91b2:crates/prin-metrics/src/lib.rs           # pre-S1 state: 15-line doc stub

# Semantic cross-check against the reference implementation (read-only)
# Read in full: prinet/core/measurement.py and prinet/utils/oscillosim.py
# chimera section (lines 679-1038) from the PRINet 3.0.0 archive, and
# compared formula-by-formula against the Rust rebuild (see §3.4).

# Quality gates (all re-executed by this audit)
cargo fmt --all -- --check                                 # exit 0, no diff
cargo clippy --workspace --all-targets -- -D warnings      # exit 0
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings  # exit 0
set RUSTDOCFLAGS=-D warnings&& cargo doc --workspace --no-deps                  # exit 0

# Tests
cargo test --workspace                                 # 367/367 (see §3.3)
cargo test --workspace --features strict-checks        # all green (170 dynamics unit = 167 + 3 strict)

# Coverage (gate metric: lines, Testing Standards §4)
cargo llvm-cov -p prin-metrics --summary-only
#   chimera.rs        99.10% lines / 95.65% regions
#   coherence.rs     100.00% lines / 97.12% regions
#   energy.rs         98.86% lines / 95.50% regions
#   error.rs         100.00% lines / 97.25% regions
#   knn.rs           100.00% lines / 94.92% regions
#   metastability.rs 100.00% lines / 95.77% regions
#   order.rs         100.00% lines / 96.88% regions
#   spectral.rs       99.50% lines / 96.74% regions
#   TOTAL             99.53% lines / 96.28% regions / 100.00% functions

# Python gates (no Python changed; regression)
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/    # All checks passed
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/  # 44 files already formatted
.venv\Scripts\mypy python/prin --strict                               # no issues in 16 files
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin     # 100% (104/104)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                 # 0 issues
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --basetemp=.pytest_basetemp  # 172 passed, 6 deselected
.venv\Scripts\python -m pytest tests/ parity/ --cov=prin --basetemp=.pytest_basetemp-full               # 184 passed

# Security
cargo audit                            # 1 allowed warning: inherited paste RUSTSEC-2024-0436 (amendment #9); rustfft clean
.venv\Scripts\python -m pip_audit .    # No known vulnerabilities found
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt  # No known vulnerabilities found
snyk code test --severity-threshold=low crates\prin-metrics\src    # Total issues: 0 (org symbo-gif)
# Snyk SCA: not runnable locally for this repo's manifests (SNYK-CLI-0000/SNYK-OS-0001,
# documented in EA-002); the CI snyk workflow (Code + SCA) ran green on 0909691.

# Documentation
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html
# build succeeded, 0 warnings

# Hygiene / artefact trail
.venv\Scripts\python tools/wp001_baseline.py check       # WP-001 baseline validation passed
Select-String TODO|FIXME|HACK|todo!|unimplemented!|stub over crates/prin-metrics  # none
Select-String "#[ignore" over crates/prin-metrics         # none
gh run list --branch feat/wp006-oscillator-state --json ... # all workflows success on 0909691 (gpu skipped)

# Independent acceptance reproduction (read-only; script in %TEMP%, not committed)
.venv\Scripts\python %TEMP%\wp010_audit\verify_wp010.py   # ALL CHECKS PASSED (§3.4)
```

## 3. Detailed findings

### 3.1 A1 — Scope conformance

The S1 commit `0909691` touches exactly the declared scope: 8 new/expanded
source modules in `crates/prin-metrics/src`, 3 integration test files, 3 JSON
fixtures, the crate manifest (`rustfft.workspace = true`, `serde_json`
dev-dependency), the workspace manifest (`rustfft = "6.2"` in
`[workspace.dependencies]` with a justification comment), `Cargo.lock`
(rustfft 6.4.1 + transitive deps), and the S1 handoff note. No files outside
the WP-010 scope were modified; `python/prin`, `prin-dynamics`, and all other
crates are untouched (verified via `git show --stat`).

Every declared scope item is present and evidence-mapped:

| Scope item (WP declaration, `009-project-state.md` §6) | Delivery |
|---|---|
| Full order parameters | `order.rs`: `kuramoto_order_parameter`, `kuramoto_order_parameter_complex`, `inter_frame_phase_correlation`, `order_parameter_series` |
| Sparse variants (where PRINet defines them) | `coherence.rs::sparse_mean_phase_coherence`, `energy.rs::sparse_synchronization_energy` — the exact sparse surface of PRINet 3.0 `measurement.py` |
| Coherence | `mean_phase_coherence`, `phase_coherence_matrix` |
| PSD | `spectral.rs`: `power_spectral_density`, `extract_concept_probabilities` (rustfft-backed) |
| Local order | `chimera.rs::local_order_parameter` |
| Metastability | `metastability.rs::metastability` (PRIN extension, §3.4 item 5) |
| Chimera metrics | `bimodality_index`, `strength_of_incoherence`, `discontinuity_measure`, `chimera_index`, `strength_of_incoherence_temporal`, `BIMODALITY_CHIMERA_THRESHOLD`, `DEFAULT_CHIMERA_THRESHOLD` |
| Measurement-facing k-NN | `knn.rs::build_phase_knn` (part of the `measurement.py` rebuild; delegates, does not duplicate) |

Non-goals verified: no tensor decompositions, no report generation; WP-010 is
Rust-only (Python API exposure is WP-011); CPU-only as specified for Phase 1.
Out-of-scope discoveries (batched `(B, N)` variants, neighbour-index topology
builders, concept-bin semantics) are recorded in the handoff note for later
WPs, not implemented — correct scope discipline per Workflow Standards §3/S1.

The pre-S1 baseline was a 15-line doc-only stub
(`git show 21c91b2:crates/prin-metrics/src/lib.rs`), so the entire
implementation is new code subject to the ≥95% coverage gate.

**New dependency review (rustfft):** required for the PSD rebuild (naive DFT
would be O(N²)); pure-Rust, widely used; added to `[workspace.dependencies]`
with an inline justification comment; `cargo audit` and the green CI `snyk`
workflow report no advisories for rustfft 6.4.1 or its transitive deps
(strum/strum_macros, num-traits already present). Consistent with prior
workspace-dependency introductions; no amendment required.

### 3.2 A2 — Plan/architecture conformance

- **Numerics in Rust, none in Python (plan §4.2):** all metric math is Rust
  f64; `python/prin` is byte-identical to the pre-S1 state. ✓
- **Crate layering (plan §4.5):** `prin-metrics` depends on `prin-dynamics`
  (`metrics → dynamics`), never the reverse; no upward dependencies added. ✓
- **One algorithm, one implementation (plan §4.1):** the phase k-NN index is
  not reimplemented — `build_phase_knn` delegates to
  `prin_dynamics::state::build_phase_knn_index` and the wrapped phase
  difference reuses `prin_dynamics::state::safe_phase_diff` (verified
  `atan2(sin Δ, cos Δ)`, matching PRINet's `torch.atan2(torch.sin, torch.cos)`).
  `build_phase_knn_matches_prin_dynamics_index` asserts byte-identical output
  of the two entry points. ✓
- **Explicit state, deterministic seeding (plan §4.3):** WP-010 introduces no
  stochastic entry points — every metric is a pure deterministic function of
  its inputs; a grep for `rand|Seed|thread_rng|SystemTime|Instant::now` over
  `crates/prin-metrics/src` finds only the proptest strategy parameter named
  `seed` in a permutation-invariance test. No hidden RNG. ✓
- **`unsafe` policy (plan/Coding Standards §6):** `#![forbid(unsafe_code)]`
  preserved in `lib.rs:45`; the only occurrence of the word "unsafe" in the
  crate is that attribute. ✓
- **Typed errors and boundary validation (Coding Standards):** every public
  function validates emptiness, finiteness, lengths, neighbour indices, and
  parameter ranges and returns a `MetricError` variant (9 variants); no panic
  paths on invalid input (degenerate cases like `n < 4` bimodality return
  `0.0` exactly as PRINet does). ✓

### 3.3 A3 — Tests in tandem + coverage

Code and tests land in the same commit (`0909691`): 104 inline unit/property
tests + 22 integration parity/corpus tests + 19 doctests = 145 new tests, all
green. This audit re-ran the full workspace suite:

```
cargo test --workspace → 367/367:
  167 dynamics unit + 16 parity_integrators + 9 parity_models + 9 parity_pac
  + 13 kernels + 104 metrics unit + 4 corpus_metrics + 6 parity_chimera
  + 12 parity_metrics + 6 _prin_core + 2 dynamics doctests + 19 metrics doctests
cargo test --workspace --features strict-checks → all green (170 dynamics unit)
```

Coverage on new/changed code (`cargo llvm-cov -p prin-metrics`), gate metric
= line coverage per Testing Standards §4 ("≥95% line coverage for new/changed
code"):

| File | Lines | Regions |
|---|---|---|
| chimera.rs | 99.10% | 95.65% |
| coherence.rs | 100.00% | 97.12% |
| energy.rs | 98.86% | 95.50% |
| error.rs | 100.00% | 97.25% |
| knn.rs | 100.00% | 94.92% |
| metastability.rs | 100.00% | 95.77% |
| order.rs | 100.00% | 96.88% |
| spectral.rs | 99.50% | 96.74% |
| **TOTAL** | **99.53%** | **96.28%** (functions 100%) |

Every file meets the ≥95% line-coverage gate. `knn.rs` region coverage
(94.92%) sits just under 95% on the non-normative region metric (missed
regions are short-circuit/macro-expansion regions in a 66-line delegation
wrapper with 100% line coverage); recorded here for transparency, not a
finding. No test is skipped or ignored (`#[ignore]` grep: none); no assertion
or tolerance was weakened — the parity tolerance stratification matches plan
§5 exactly (§3.4). Property tests cover the invariant surface (unit interval
bounds, shift/permutation invariance, Parseval, metastability ≤ 0.5, k-NN
edge properties).

### 3.4 A4 — Numerical parity + invariants (independently reproduced)

This audit did not rely on S1's claims. It re-ran the Rust parity suites
(§3.3) **and** independently reproduced the acceptance evidence with a
read-only verification script (kept in `%TEMP%`, deliberately not committed),
whose checks all passed:

**Part A — corpus fixture fidelity.** All 6 cases in
`corpus_metric_cases.json` exist in `parity/corpus/cases/`, and the fixture's
`phase_traj` / `order_parameter_traj` / `mean_phase_coherence_traj` arrays are
**bit-identical** (`np.array_equal`) to the committed golden-corpus npz arrays
(6 cases × 21 snapshots = 126 snapshots). The fixture is a faithful extraction,
not a regeneration.

**Part B — first-principles numpy f64 recomputation.** Independent
implementations of `r = |mean exp(iφ)|` and `C = (2/N(N−1)) Σ_{i<j} cos(φi−φj)`
reproduce the fixture expected arrays with max relative drift **4.83e-16**
(order parameter) and **1.62e-15** (coherence) — ~5 orders of magnitude inside
the rtol=1e-10 acceptance target. `R ∈ [0,1]` and `C ∈ [−1,1]` hold for all
126 snapshots; the identity `C = (N r² − 1)/(N − 1)` holds on the corpus
arrays to **1.67e-16**.

**Part C — PRINet 3.0.0 reference regeneration.** Re-running `prinet==3.0.0`
(`torch==2.13.0+cpu`, the pinned venv install) on the fixture's embedded inputs
reproduces **every** embedded reference value at drift **0.0**: order parameter,
complex order parameter, mean phase coherence, coherence matrix,
synchronization energy (default + explicit matrix), inter-frame correlation,
sparse coherence/energy k=3 and k=11, full-metric cross-checks (f64 paths);
PSD (default + 12 bins), concept probabilities, local order parameter,
bimodality index (fixture + uniform + degenerate controls), SI (w=5),
chimera index, temporal SI (f32-hazard paths); discontinuity mask and η match
**exactly**. The fixture provenance blocks are therefore truthful, and since
the Rust parity tests (re-run green by this audit) compare the Rust
implementation against these same values, the parity chain
`Rust ↔ fixture ↔ PRINet 3.0.0` is independently closed.

**Part D — sparse/full agreement (acceptance criterion 3), first principles.**
- Synchronized phases: full coherence = sparse coherence = 1 exactly (both
  my numpy recomputation and the Rust test
  `parity_sparse_full_agreement_for_synchronized_phases`).
- Sparse energy at k=N−1, K=1 equals the dense default energy × the exact
  normalization ratio N/(N−1) (my recomputation: both sides
  0.957298196776531; Rust test `parity_sparse_energy_ratio_to_full_at_k_n_minus_1`).
- The fixture's embedded full energy/coherence equal my independent dense
  recomputation to 0.0 drift.

**Semantic cross-check against PRINet sources.** The Rust rebuild was compared
formula-by-formula against the PRINet 3.0.0 archive
(`core/measurement.py`, `utils/oscillosim.py` lines 679–1038):
f64 paths (order parameter, coherence, matrix, energy, inter-frame, sparse
variants) match operation-for-operation; the PSD complex64 truncation hazard,
chimera float32/complex64 hazards, SI pad+conv+slice semantics (including
Python slice clamping for `window_size > N`), discontinuity wrap/mask/η
counting, Sarle bimodality formula and guards, and the `1e-10` concept-prob
denominator guard are all faithfully reproduced or documented as preserved
hazards with the amendment #14-pattern `1e-6` parity tolerance. Where PRIN is
deliberately more defensive than PRINet (e.g. `window_size > N` cannot panic),
the divergence is covered by dedicated tests and cannot affect parity
fixtures.

**Metastability (handoff note item 4 for S2 confirmation).** The WP-010
declaration explicitly lists "metastability" in scope. The delivered
definition (population standard deviation of the per-snapshot order parameter,
bounded by [0, 0.5], asserted by `metastability_bounded_by_half`) is the
standard oscillator-literature definition, documented in rustdoc as a PRIN
extension with no PRINet analogue. Confirmed acceptable.

**Tolerance stratification vs plan §5 / amendments #14 and #16:**
- f64 single-runtime paths at `rtol=1e-10, atol=1e-12` — the WP-010
  acceptance target (plan §5.2 "single-runtime metric/decomposition
  verification still targeting rtol=1e-10"). ✓
- Corpus comparisons at the registered METRIC tolerance `rtol=1e-8,
  atol=1e-12` — exactly the values in `python/prin/parity/schema.py`
  (amendment #16). ✓
- PSD/concept/chimera paths at `1e-6` under the documented PRINet
  complex64/float32 hazards (amendment #14 pattern, plan §5.6). ✓

No tolerance drift, no weakened assertions.

### 3.5 A5 — Quality gates

All gates re-executed by this audit (commands and results in §2): format,
clippy (default + strict), rustdoc `-D warnings`, ruff check + format, mypy
`--strict`, interrogate 100%, bandit 0. All clean. The transient
`error finalizing incremental compilation session directory (os error 32)`
messages in two command outputs are Windows incremental-build file-lock
artefacts of this audit's own sequential runs; both commands exited 0 and the
warning carries no code content.

### 3.6 A6 — Security

| Scan | Result |
|---|---|
| `unsafe` scan | Only `#![forbid(unsafe_code)]`; zero `unsafe` blocks |
| Secret scan | No secrets in the diff |
| Runtime codegen | None (no build-script codegen, no eval-style patterns; rustfft is a pure-Rust library dependency) |
| bandit | 0 issues |
| Snyk Code (`crates/prin-metrics/src`, low+) | 0 issues (CLI, authenticated, org symbo-gif) |
| Snyk SCA | Local CLI blocked for this repo's manifests per EA-002; CI `snyk` workflow (Code + SCA) green on `0909691` |
| `cargo audit` | Only inherited `paste` RUSTSEC-2024-0436 (amendment #9, allowed warning); rustfft 6.4.1 clean |
| `pip-audit .` / `-r DOCS/sphinx/requirements.txt` | No known vulnerabilities |

### 3.7 A7 — Documentation coverage

- Rustdoc: 100% public items documented (`#![warn(missing_docs)]` enforced;
  `cargo doc --workspace --no-deps` with `RUSTDOCFLAGS=-D warnings` exits 0).
  Module docs state the numerics policy, tolerance stratification, preserved
  hazards, and invariant clamps. 19 doctests execute green.
- Interrogate: 100% (104/104) — Python surface unchanged.
- Sphinx: `-W --keep-going` build succeeds with 0 warnings.
- README/CHANGELOG updates are S4 deliverables, not S1/S2 scope.

### 3.8 A8 — Repository hygiene

- No TODO/FIXME/HACK/XXX/stub markers and no `todo!`/`unimplemented!`/
  `unreachable!` anywhere in `crates/prin-metrics` (grep clean).
- No orphan files: every new file is in the declared scope; fixtures carry
  embedded provenance blocks.
- `.gitignore` respected: working tree clean after the full gate run
  (`.pytest_basetemp*` ignored).
- `tools/wp001_baseline.py check` passes (inventory, traceability, session
  register consistency; the `0037-` prefixed handoff note in
  `DOCS/experiments/` follows the cycles-004–008 convention; the WP-009
  rename lesson applied to `DOCS/sessions/` briefs, which remain unique).
- `__all__` N/A (no Python changes).

### 3.9 A9 — CI status

CI on the S1 SHA `0909691` (PR event, checked via `gh run list --json`):

| Workflow | Status |
|---|---|
| parity | ✅ success |
| rust | ✅ success |
| python | ✅ success |
| repro | ✅ success |
| snyk | ✅ success |
| gpu | ⊘ skipped (no GPU runner; amendment #12) |

All five runnable workflows are green on the exact audited commit (the
`python` workflow was still in progress early in this audit and completed
successfully before the verdict was issued). Benchmark regression gates: none
defined for `prin-metrics`; no performance work in this WP — not tripped.

### 3.10 A10 — Artefact trail

- Cycle-009 audit report `DOCS/audits/009-wp009-audit.md`: exists, closure
  table appended, delta re-audit CLEAN (all seven findings FIXED). ✓
- Cycle-009 project state report `DOCS/reports/009-project-state.md`: exists,
  declares WP-010 with scope/acceptance/non-goals, records maintainer
  approval (EA-002, 2026-08-08). ✓
- Session register: 0037 READY, 0038/0039 PLANNED — consistent with S2 in
  flight (register status updates are S4's responsibility). ✓
- S1 handoff note committed at `DOCS/experiments/0037-wp010-s1-handoff.md`
  with a complete acceptance-criteria → evidence mapping. Every handoff claim
  this audit re-verified (test counts 367/145, coverage 99.53%, fmt/clippy
  results, pytest 172/184, gate outcomes, fixture provenance) held — no
  factual inaccuracies of the WP009-F5 kind. ✓

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| — | — | — | No findings | — | — |

## 5. Deviation-ledger delta

New findings added to the ledger: **none**.

Carried findings re-inspected: none (cycle 009 closed CLEAN; no findings were
carried into WP-010).

## 6. Verdict and required actions

**Verdict: PASS**

**Maintainer acknowledgment:** granted by the maintainer in session 0038,
2026-08-08, after presentation of this verdict and its evidence.

All ten audit dimensions are green and every WP-010 acceptance criterion was
independently reproduced by this audit:

- ✅ **Metrics/decompositions tolerance target rtol=1e-10 met:** Rust parity
  against exact-regenerated PRINet f64 references passes at `rtol=1e-10`
  (re-run by this audit); independent first-principles recomputation agrees
  with the references to ≤ 1.62e-15. Corpus cases pass at the registered
  `rtol=1e-8` (amendment #16); f32-hazard paths at the documented `1e-6`
  (amendment #14 pattern).
- ✅ **R stays in [0,1]:** asserted in Rust unit, property, parity, and all
  126 corpus snapshots; independently re-verified; coherence clamped to
  [−1,1]; local order parameters and chimera index likewise bounded.
- ✅ **Sparse/full variants agree where equivalent:** both equal exactly 1 for
  synchronized phases; sparse energy at k=N−1 equals dense energy × N/(N−1)
  (the 1/N vs 1/k normalization invariant); both independently recomputed.

S1 handoff claims were checked one by one and all held. Scope discipline,
architecture rules, security posture, documentation gates, hygiene, CI, and
the artefact trail are conforming. Zero findings.

**Ordered S3 action list (mandatory no-change closure):**

1. Record the no-change closure: verify `git status` clean at the audited
   SHA, confirm zero findings require source edits, and append the closure
   table to this report (§7).
2. Independent delta verification: re-run the fast gate subset
   (`cargo fmt --check`, `cargo clippy -D warnings`,
   `cargo test -p prin-metrics`, `tools/wp001_baseline.py check`) to confirm
   the tree is unchanged since the audit, and record the outputs in §7.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| — | — | — | — |

**Delta re-audit date:** YYYY-MM-DD — **Result:** pending S3
