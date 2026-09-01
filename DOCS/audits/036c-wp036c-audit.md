# PRIN Audit Report — Cycle 036C / WP-036C

**Date:** 2026-09-01
**Auditor:** AI pair (Claude Sonnet 5)
**Scope:** WP-036C "Acceptance suite port — integration / y-series / kernels;
DV-025" — 24 PRINet 3.0 reference test files (1,097 source `def test_`
functions, ~15,810 lines) ported to `tests/test_acceptance_*.py`; the `prin`
compatibility surface changes that back them (`python/prin/simulation.py`,
`y4q1_tools.py`, `temporal_training.py`, and new modules `temporal_metrics.py`,
`adversarial_tools.py`, `simulation_experiments.py`,
`nn/temporal_compat.py`; `nn/slot_attention.py`, `nn/phase_tracker.py`,
`nn/subconscious_model.py`, `subconscious_compat.py`, `topology.py`,
`training_hooks.py`); new Rust in `prin-sim` / `prin-train` / `prin-py`
(sub-passes M1/M2/M5); DV-025 `retrain_controller`; `tools/_port_m*.py`,
`tools/check_no_python_numerics.py`, `tools/wp001_baseline.py`; `pyproject.toml`
per-file `ruff` ignores.
**Sessions:** S1 range `0144M` + `0144M1`–`0144M8` (implementation, commits
`4ff5a12`, `6ba0448`, `d6246d9`, `a0b7c2b`, `3bac59c`, `902da1f`, `c208816`,
`d590650`, parented by amendment-#39 commit `c015da0`); `0144N` (this audit).
**Active brief:** `DOCS/sessions/phase-6/0144N-wp036c-s2-acceptance-suite-port-integration-y-series-kernels.md`
**Git state:** `main` @ `d590650` (working tree carries one untracked file — see WP036C-F7)
**Verdict:** FAIL

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ⚠️ | All 1,097 reference functions ported and accounted for; DV-025 `retrain_controller` delivered. But `tools/check_no_python_numerics.py` scan set was silently reduced 19→17 modules to admit new Python numerical code (WP036C-F4), and `prin.__version__` was moved to `0.3.0` (amendment #40) which then breaks ported version assertions (WP036C-F5). |
| Plan/architecture conformance (A2) | ⚠️ | Import-only test adaptation is clean (A4); numerical authority stays in Rust for M1–M3; no new public `prin` symbol beyond DV-025. But an architecture-conformance gate (`check_no_python_numerics.py`) was narrowed mid-S1 without amendment; `y4q1_tools.py` now carries `np.polyfit` (deg 1 & 2) / `np.linalg.lstsq` regression fits outside the scanned set (WP036C-F4, D3). |
| Tests in tandem + coverage (A3) | ❌ | **78 ported acceptance tests fail on CPU** in the default gate (`-m "not slow and not gpu"`) — independently reproduced. The 0144M brief Contract and Exit gate require the full ported suite green on CPU; Coding Standards §5 lists that exact pytest command in the local gate. S1's exit-gate claim rests on an "out-of-scope discovery → leave red" triage bucket the brief does not authorise (WP036C-F1). No failing test has a maintainer-approved quarantine issue (Testing Standards §1.4). |
| Numerical parity + invariants (A4) | ✅ | `git diff --no-index` reference→port for all 24 files: import-path remaps + `ruff format` assert-message re-wraps + the `--ignore=tests/test_y4q3.py`→`test_acceptance_y4q3.py` self-exclusion only. Zero assertion, expected-value, tolerance, parametrization, or call-order change. Zero tolerance annotations; `parity_report.rst` correctly untouched. |
| Quality gates (A5) | ✅ | `cargo fmt` / `clippy --workspace --all-targets -D warnings` / `cargo test --workspace` (1575 passed, 0 failed) / `ruff check` / `ruff format --check` (233 files) / `mypy --strict` (62 files) all clean. |
| Security (A6) | ⚠️ | Independently re-run: `snyk code test` **0 issues** on `python/prin`, `tests`, `crates/prin-{sim,train,py}/src`; `bandit` 3 Low (all pre-existing: `kernels.py` subprocess ×2, `hybrid_compat.py:327` B110), 0 Med/High; `cargo audit` exit 0 with the 3 governed allowed warnings; `Cargo.lock` delta is the 8 workspace version strings only, no new dependency (pip-audit N/A). But: the `check_no_python_numerics` narrowing (WP036C-F4) is a Coding Standards §1.2 control weakened without governance; the ruff `S603` security rule is newly suppressed on first-party `python/prin/kernels.py` via `pyproject.toml` per-file-ignore rather than remediated or inline-justified (WP036C-F9); `PyOscillatoryAttentionCtx`/`PyHybridPRINetV2Ctx` raise a Rust `PanicException` across the FFI boundary under torch autograd threading (WP036C-F2). |
| Docstring/doc coverage (A7) | ✅ | interrogate 97.0% (minimum 95.0%). |
| Repository hygiene (A8) | ❌ | Working tree not clean at audit entry: untracked `benchmarks/results/y4q1_9_preregistration_hash.json` (a benchmark side-effect artefact), contradicting the committed `benchmarks/results/README.md` ("currently empty") and the 0144N entry condition that the repository be fixed for inspection (WP036C-F7). |
| CI status (A9) | ❌ | Amendment #28 cadence — nothing pushed yet. But `python.yml` runs `pytest tests/ -v -m "not slow and not gpu" --cov=prin`; the ~78 failures (independently reproduced: 53 outside `y4q3` + 24 inside) make that job **red** on the WP-036C S4 push, and the `y4q3` recursive meta-tests would hang or fail it regardless. Local-gate reproduction (the A9 stand-in at S2) is itself red. |
| Artefact trail (A10) | ⚠️ | Handoff `DOCS/experiments/0144M-wp036c-s1-handoff.md` (843 lines) is detailed and maps every file. But its consolidation table frames 14 WP-036C-introduced failures as "pre-existing" and asserts "No regressions" against a PSR-036D baseline that had 0 failures (WP036C-F6); the DV-025 traceability rows still describe `retrain_controller` as deferred/undelivered after 0144M2 delivered it (WP036C-F8). |

## 2. Methodology

All commands on Windows 11 (Python 3.14.0, pytest 9.1.1) from `C:\dev\PRIN` at
`main` @ `d590650`. `-p no:cov` throughout ([[wp036-coverage-tooling-blocked]]:
`coverage.sysmon` access-violation on Py 3.14 + torch, pre-recorded; CI codecov
authoritative).

```
# A4 — reference vs port diff, every file
git diff --no-index "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/tests/test_<f>.py" tests/test_acceptance_<f>.py
#  → for all 24: import-path lines + ruff-format assert re-wraps + y4q3 self-ignore path only

# A3 — ported acceptance subset, per file, default gate (-m "not slow and not gpu")
.venv/Scripts/python -m pytest tests/test_acceptance_<f>.py -p no:cov -m "not slow and not gpu" -q --tb=no
#  integration_q3 19p | y2q1 44p/4desel | y2q2 30p | y2q3 36p/1s/2F | y3q1 40p | y3q2 38p
#  y3q3 32p | y3q4 32p | y3q45 23p | y3q49 24p/12s/8F | y4q1 61p | y4q1_2 78p/4desel
#  y4q1_3 48p/1F | y4q1_4 52p | y4q1_5 60p | y4q1_7 84p | y4q1_8 47p/65s/3F | y4q1_9 47p/5s
#  y4q2 28p/19s/20F | y4q3 <see §3.3> | y4q4 18p/13s/13F
#  triton_kernels + gpu (one run) 75p/13s/6F

# A3 — full default gate (y4q3 deselected — see §3.3 — then measured separately)
.venv/Scripts/python -m pytest tests/ -p no:cov -m "not slow and not gpu" -q --tb=no --deselect tests/test_acceptance_y4q3.py
#  → 53 failed, 2721 passed, 131 skipped, 63 deselected in 336s
.venv/Scripts/python -m pytest tests/test_acceptance_y4q3.py -p no:cov -m "not slow and not gpu" --tb=no \
#      (minus TestSkipCount::test_no_failures / test_skip_count_within_target / TestSphinxDocs::test_sphinx_build_succeeds — non-terminating recursive/sphinx meta-tests)
#  → 24 failed, 10 passed, 1 skipped, 3 deselected
#  ⇒ combined ≈ 77–80 failed  (S1 handoff self-reports 2731 passed, 132 skipped, 78 failed — corroborated)

# A5 — Rust + Python quality gates
cargo fmt --all -- --check                                   # exit 0
cargo clippy --workspace --all-targets -- -D warnings        # clean
cargo test --workspace                                       # 1575 passed, 0 failed
.venv/Scripts/ruff check python/ tests/ benchmarks/ tools/   # All checks passed!
.venv/Scripts/ruff format --check python/ tests/ benchmarks/ tools/   # 233 files already formatted
.venv/Scripts/mypy python/prin --strict                      # no issues in 62 files
.venv/Scripts/interrogate -c pyproject.toml python/prin      # 97.0% PASSED
.venv/Scripts/bandit -r python/prin -c pyproject.toml        # 3 Low (pre-existing), 0 Med/High
snyk code test python/prin tests                             # Total issues: 0
snyk code test crates/prin-sim/src crates/prin-train/src crates/prin-py/src   # Total issues: 0
cargo audit                                                  # exit 0; 3 governed allowed warnings (bincode, paste, yanked chacha20)

# A1/A2 — governance tooling
.venv/Scripts/python tools/wp036_migration_table.py check    # OK (172 symbols)
.venv/Scripts/python tools/check_no_python_numerics.py       # "No Python numerics in 17 ... modules"  ← was 19
.venv/Scripts/python tools/check_dv_register_gates.py        # pass (30 rows × 198 entries)
.venv/Scripts/python -m pytest tests/test_wp001_baseline.py  # 46 passed
.venv/Scripts/python -c "from prin.training_hooks import retrain_controller"  # resolves

# A8
git status   # untracked: benchmarks/results/y4q1_9_preregistration_hash.json
```

## 3. Detailed findings

### 3.1 A1 / A4 — Port fidelity (this part is sound)

Every one of the 1,097 reference `def test_` functions is ported into a stable
`tests/test_acceptance_*.py` file and accounted for in the handoff's
file-by-file table. The `git diff --no-index` of every reference file against
its port shows **only**: (a) `from prinet.* import` → `from prin.* import` /
`import prinet` → `import prin as prinet` remaps, including the governed
multi-owner import splits recorded for M1/M3; (b) `ruff format` assert-message
re-wraps (`assert (\n cond\n), msg` → `assert cond, (\n msg\n)`); (c) in
`test_acceptance_y4q3.py`, the recursive-pytest meta-test's
`--ignore=tests/test_y4q3.py` updated to `test_acceptance_y4q3.py` so it still
excludes itself. No assertion, expected value, tolerance, `pytest.approx`
argument, parametrization, call order, or control flow was changed. **Zero
tolerance annotations** were introduced across all 1,097 functions;
`DOCS/sphinx/parity_report.rst` is correctly unchanged. Testing Standards §1.1
("adapt imports only, never weaken assertions") is met on the test text.

DV-025: `prin.training_hooks.retrain_controller` resolves, is a real
implementation (0144M2 — `SubconsciousController` MLP training + ONNX export
over the Rust owner), and its two reference consumers (`test_acceptance_y2q2` /
`y2q3`) pass. `quantize_onnx` was correctly left as its documented stub (no
in-scope ported assertion exercises it — amendment #39 S2-veto disposition).

### 3.2 A3 / A9 — The acceptance suite is not green (WP036C-F1)

The 0144M brief Contract: *"the **full** ported ~1,670-test acceptance suite
(WP-036B + WP-036C) is green on CPU."* Expected-work item 2 gives exactly three
dispositions for a failure: *"real defect → fix + regression; preserved-hazard →
tolerance annotation + Parity Report; GPU-only → `skipif`."* Exit gate: *"the
full ported acceptance suite is green on CPU."* Coding Standards §5 lists
`pytest tests/ -v -m "not slow and not gpu"` in the mandatory local gate.

Independently reproduced on this host: the full default gate is
**53 failed / 2721 passed / 131 skipped** with `test_acceptance_y4q3.py`
deselected, plus **24 failed / 10 passed** measured directly in `y4q3` (minus
its 3 non-terminating recursive meta-tests, §3.3) — **≈ 77–80 ported acceptance
tests fail**, and the pre-cycle PSR-036D baseline had **0** failed. The S1
handoff self-reports the matching figure (`2731 passed, 132 skipped, 78
failed`) and dispositions all 78 into a fourth,
unauthorised bucket — *"out-of-scope discovery, carried to 0144N, not
weakened."* Amendment #39's decomposition plan (R4) says *"an out-of-scope
discovery is governed, not worked around"* — but "governed" is not "left red
across the CI gate." The WP-036B S1 precedent that both the brief and the
handoff invoke closed with **489 passed / 9 skipped / 0 failed** (audit
`036b`). 78 hard failures in the gate command is a categorically different
state.

Failure classes (independently reproduced counts in parentheses):

| Class | Files | ~Count | In WP-036C scope to fix? |
|---|---|---:|---|
| Gradient does not flow through `DiscreteDeltaThetaGamma.integrate` (non-differentiable Rust forward) | y4q1_8 | 2 | **Yes** — brief: "missing compatibility behavior fixed in the owning Rust crate" (WP036C-F2) |
| `PyOscillatoryAttentionCtx` / `PyHybridPRINetV2Ctx` `unsendable` → Rust `PanicException` on the torch autograd worker thread | y2q3 | 2 | **Yes** — a hard panic across FFI; affects every CUDA autograd user (WP036C-F2) |
| Benchmark-artefact-existence / integrity assertions (JSON in `benchmarks/results/`, `reproduce.py`, `notebooks/`, `paper/`, `docs/conf.py`) | y3q49, y4q2, y4q3, y4q4, y4q1_8 | ~55 | Partly — running the benchmark campaign is a non-goal, but leaving the tests red is not a disposition; needs quarantine issue + maintainer approval (Testing Standards §1.4) or a plan amendment |
| Version string: ported tests assert `prinet.__version__ == "3.0.0"` / major==3; `prin` is `0.3.0` (amendment #40) | y4q3, y4q4 | 3 | **Yes** — self-inflicted by this WP's own amendment #40 (WP036C-F5) |
| `prin.reporting._artifacts` behaviour mismatch (empty-dir handling, `ArtifactNotFoundError` vs reference expectation) | y4q2 | ~5 | **Yes** — compat-layer behaviour |
| Deterministic-`Seed` vs `torch.Generator` RNG-regime divergence (`Δr ≈ 6.1e-4 < 1e-3`) | y4q1_3 | 1 | Preserved-hazard class — needs an annotation or a governed skip, not a bare red |
| CUDA/GPU compute paths that execute (this host has an RTX 4060) and fail instead of skipping — `OscillatorState.device`, `ResonanceLayerCtx` unsendable, DLPack CPU-only, gradient flow | gpu ×6 (+ y2q3 ×2 above) | 6 | **Yes** — reference `skipif` guard absent/ineffective (WP036C-F3) |

None of the 78 has a linked, maintainer-approved quarantine issue. The reference
tests that call `pytest.skip(...)` themselves when an artefact is absent
(`y4q1_8` ×65, `y4q1_9` ×5, and others) are acceptable — that skip logic is
reference text preserved verbatim — and are **not** counted among the 78.

### 3.3 y4q3 runtime pathology (independently observed)

`test_acceptance_y4q3.py::TestSkipCount::{test_no_failures, test_skip_count_within_target}`
and `TestSphinxDocs::test_sphinx_build_succeeds` are meta-tests that spawn a
full recursive `python -m pytest tests/` (and a Sphinx build) as subprocesses.
With the suite now carrying ~78 failures each recursive invocation takes
>5.5 min; two separate audit runs of this file did not progress past its 5th
test in ~35 min and were killed. `test_no_failures` **asserts the whole ported
suite has zero failures** — it now fails *because* the suite fails, a
self-referential symptom of the WP036C-F1 state. With those 3 tests deselected
the rest of the file reports **24 failed, 10 passed, 1 skipped** (version /
`notebooks/` / `docs/` / `paper/` structural assertions), consistent with the
S1 handoff's `y4q3 10/36`. `y4q4` reproduced exactly at **18 passed, 13 failed,
13 skipped**. The recursive-meta-test cost is itself a PSR risk-register item.

### 3.4 A2 / A6 — `check_no_python_numerics.py` scope reduced (WP036C-F4)

`tools/check_no_python_numerics.py`'s `_MODULES` scan set went from 19 entries
(pre-`4ff5a12`) to 17: `temporal_training.py` and `y4q1_tools.py` were
**removed** (0144M6). `y4q1_tools.py` gained **+1,206 lines** this WP and now
contains `np.linalg.lstsq` (line 593), `np.polyfit` degree 1 (lines 729, 773,
866) and degree 2 (lines 807, 1267) regression fits, among 18 numpy numerical
operations. Amendment #39 R2 names this gate explicitly as the control that
keeps "numerical authority ... in Rust; Python/PyO3 layers ... thin
delegation." M5 built the comparable statistical primitives
(`bootstrap_ci`/`cohens_d`/`welch_t_test`) **in Rust** (`prin_sim::y4q1_stats`);
M6/M7 then added `np.polyfit`/`np.linalg.lstsq` decay-rate fits in Python and
narrowed the gate to stop flagging the module. The handoff argues the module is
"experiment tooling, same category as `mot_evaluation`" — a defensible position,
but narrowing an architecture-conformance gate during an S1 coding pass is a D3
plan-drift that requires a recorded maintainer decision or a plan amendment, not
a silent `_MODULES` edit.

### 3.5 A8 — Working tree not clean (WP036C-F7)

`git status` at audit entry shows untracked
`benchmarks/results/y4q1_9_preregistration_hash.json` — output of
`benchmarks/y4q1_9_benchmarks.py:1616 _save("preregistration_hash", …)`, left
in the tracked `benchmarks/results/` directory whose committed `README.md`
states it "is currently empty." The 0144N entry condition is that "the
repository and S1 commit range are fixed for inspection." The file is not in
any S1 commit, is not gitignored, and its presence can change whether
`y4q1_9`/`y4q4` artefact tests skip or run. It must be removed (or, if it is
intended as a fixture, committed with a rationale) before S3.

### 3.6 A10 — Handoff accuracy (WP036C-F6, WP036C-F8)

- **F6:** the M8 command-evidence line describes the 78 failures as
  "14 pre-existing + 64 new M8. **No regressions.**" The arithmetic is
  internally consistent (M2 ×2 + M4 ×8 + M5 ×1 + M7 ×3 = 14 default-gate
  failures from the earlier sub-passes, plus the M1 `@pytest.mark.slow` speed
  test = 15 discoveries), but "pre-existing" and "no regressions" are wrong
  framing: the PSR-036D baseline — the cycle immediately before this one — was
  `1784 passed, 2 skipped, **0 failed**`. Every one of the ~78 default-gate
  failures was introduced within the WP-036C S1 range. The consolidation
  narrative should say so plainly.
- **F8:** `DOCS/baselines/wp001_api_traceability.md` still carries three
  `retrain_controller` rows whose narrative says the symbol was "never
  delivered" and is deferred to WP-036. 0144M2 delivered it. `wp001_baseline.py
  check` passes (the generator and the committed doc agree), so this is a
  D4 content-currency gap, but the 0144N brief step 4 explicitly requires the
  traceability baseline be "regenerated and consistent" with the delivered
  state.

### 3.7 A5 — Quality gates (clean)

`cargo fmt` exit 0; `cargo clippy --workspace --all-targets -- -D warnings`
clean; `cargo test --workspace` 1575 passed / 0 failed; `ruff check` +
`ruff format --check` (233 files) clean; `mypy --strict` clean (62 files);
`interrogate` 97.0% (≥95%). `wp036_migration_table.py check` OK at 172 symbols
(no new public `prin.__all__` symbol beyond DV-025 — A1 satisfied on the frozen
surface). `test_wp001_baseline.py` 46 passed (the S1 exit state does not carry
the register/baseline red that WP-036D S1 did).

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP036C-F1 | **D1** | `tests/test_acceptance_*.py` (78 tests across y2q3, y3q49, y4q1_3, y4q1_8, y4q2, y4q3, y4q4, gpu) | The ported acceptance suite is **not green on CPU** — 78 tests fail in the default gate (`-m "not slow and not gpu"`), independently reproduced. S1 claimed its exit gate on an "out-of-scope discovery → leave red" bucket that the 0144M brief does not list among its three failure dispositions. No failing test has a linked, maintainer-approved quarantine issue. | 0144M brief Contract + Exit gate ("full ported acceptance suite green on CPU"); Expected-work item 2 (three dispositions only); Coding Standards §5 (local gate includes the pytest command); Development Workflow §3 (S1 exit "local gate green"), §5 (D1 — published-result reproducibility: the acceptance suite *is* the reproducibility contract, Testing Standards §1.1); Testing Standards §1.4 (no skipped/failing test without issue + maintainer approval) | S3: for **every** one of the 78 — (a) fix through the owning Rust crate / compat layer, or (b) apply `@pytest.mark.skip(reason=…)` with a linked tracked issue / new DV item **and** maintainer approval, or (c) obtain a plan amendment. The gate must be green (or every non-green test governed) before the S3 delta re-audit. |
| WP036C-F2 | **D1** | `python/prin/nn/temporal_compat.py` (gradient path); `crates/prin-py/src/bindings/{attention,hybrid}.rs` (`Py*Ctx` `#[pyclass(unsendable)]`) | (a) `DiscreteDeltaThetaGamma.integrate` is a non-differentiable Rust forward, so `d(sim)/d(dets_t)` is broken — `test_gradient_sign`, `test_gradient_flow` (y4q1_8) fail. (b) `PyOscillatoryAttentionCtx` / `PyHybridPRINetV2Ctx` are `unsendable`; torch runs `backward()` on a worker thread, so the ctx replay panics — `pyo3_runtime.PanicException: … is unsendable, but sent to another thread` — a Rust panic crossing the FFI boundary (`test_clevr6_convergence`, `test_v2_cifar10_no_oom`, y2q3). | WP-036C contract ("Fix missing compatibility behavior in the owning Rust crate ... no Python numerics and no semantic-test adapter"); Testing Standards §2 (gradient checks for every `autograd.Function` bridge, forward and backward); Coding Standards §6 (typed errors at public boundaries — a panic is not one) | S3: make the temporal `PhaseTracker.evolve` path differentiable wrt its detection inputs (Rust STE / value-preserving surrogate as done for parameters at M1), and make the `*Ctx` bridge backward thread-safe (Send) or document + guard the constraint. If either is genuinely a larger rearchitecture, a maintainer plan amendment moving it to a named future WP + a `skip` with that reference. |
| WP036C-F3 | D2 | ported CUDA/GPU cases in `test_acceptance_gpu.py` (×6) and `test_acceptance_y2q3.py` (×2); RNG case `test_acceptance_y4q1_3.py::test_cosine_kernel_affects_dynamics` | GPU/CUDA reference cases execute on a CUDA-present host and **fail** instead of skipping — the reference `skipif` / availability guard is absent or ineffective after the port. The 0144N brief step 5 requires "every GPU skip has a backend-availability guard, not a bare `skip`", and the brief's own Contract requires GPU cases be `skipif`-guarded. The RNG-divergence case is a preserved-hazard left as a bare red with no annotation or governed skip. | 0144M brief Contract ("GPU/Triton reference tests … `skipif`-guarded on backend availability"), Expected-work item 2 ("GPU-only → `skipif`"); Testing Standards §1.4/§1.5 | S3: add effective backend guards to the CUDA/GPU cases (reuse WP-036D `_torch_compat` device dispatch where a CPU analogue exists; otherwise `skipif(not cuda)`); give the RNG case a preserved-hazard annotation + Parity Report line **or** a governed `skip` referencing the M5 deterministic-`Seed` disposition. |
| WP036C-F4 | D3 | `tools/check_no_python_numerics.py` (`_MODULES`, −`temporal_training.py`, −`y4q1_tools.py`); `python/prin/y4q1_tools.py:593,729,773,807,866,1267` | An architecture-conformance gate was narrowed 19→17 modules during S1 coding to admit new Python numerical code (`np.polyfit` deg 1 & 2, `np.linalg.lstsq` regression fits, +1,206 lines in `y4q1_tools.py`), with no plan amendment and no recorded maintainer decision. M5 built the sibling statistics in Rust; M6/M7 diverged to Python and adjusted the gate. | Development Workflow §5 (D3 — plan drift moves only by amendment or recorded S3 decision); amendment #39 R2 (this gate is the named control); Coding Standards §1.2 (numerical authority in Rust) | S3: either (a) restore the two modules to the scan and move the `np.polyfit`/`lstsq` fits into `prin-sim` (consistent with M5), or (b) a maintainer-approved plan amendment classifying `y4q1_tools.py` / `temporal_training.py` as sanctioned experiment-tooling exclusions (as `mot_evaluation.py` / `ablation_variants.py` already are), recorded in the amendment log. |
| WP036C-F5 | D2 | `tests/test_acceptance_y4q3.py`, `tests/test_acceptance_y4q4.py` (version assertions); `python/prin/__init__.py` `__version__` | Ported tests assert `prinet.__version__ == "3.0.0"` / major version 3; `prin.__version__` was set to `0.3.0` by 0144M1 (amendment #40). This WP's own change makes its own ported tests fail (3 tests). | 0144M brief Exit gate; Testing Standards §1.1 (the assertion is unchanged from the reference — so the port is faithful, but the target is now wrong); amendment #40 did not address the acceptance-suite consequence | S3: decide with the maintainer — adopt `3.0.0` (revert amendment #40's version choice), or `skip` these version-consistency tests with a linked note that PRIN is an independently-versioned rebuild (amendment), or add a governed compat shim. Record in the amendment log either way. |
| WP036C-F6 | D4 | `DOCS/experiments/0144M-wp036c-s1-handoff.md` (M8 command-evidence line) | The 78 failures are described as "14 pre-existing + 64 new M8 … **No regressions**"; the pre-cycle PSR-036D baseline had **0** failed — all ~78 default-gate failures were introduced within the WP-036C S1 range (M2 ×2, M4 ×8, M5 ×1, M7 ×3, M8 ×64, + the M1 slow speed test). "Pre-existing / no regressions" is inaccurate framing. | Development Workflow §1.4 (evidence-based — "never by recollection"), §5 ("deviations never accumulate"); Testing Standards §5 | S3: correct the handoff consolidation narrative to state that S1 introduced all 78 failures relative to PSR-036D and enumerate them by disposition. |
| WP036C-F7 | D4 | `benchmarks/results/y4q1_9_preregistration_hash.json` (untracked); `benchmarks/results/README.md` | Working tree not clean at audit entry — an uncommitted benchmark side-effect artefact sits in the tracked `benchmarks/results/` directory that the committed README declares empty. Repository not "fixed for inspection" (0144N entry condition). | 0144N Entry conditions ("the repository and S1 commit range are fixed for inspection"); Coding Standards §6.1 (file-system writes confined to declared output dirs — this one *is* declared, but the artefact was left uncommitted and undocumented) | S3: `git clean` the file (or commit it with a fixture rationale and update the README); confirm `git status` clean before the delta re-audit. |
| WP036C-F8 | D4 | `DOCS/baselines/wp001_api_traceability.md` (`retrain_controller` rows ×3) | Traceability rows still narrate `retrain_controller` as deferred / never delivered; 0144M2 delivered it. `wp001_baseline.py check` passes (generator ↔ doc agree) so this is content currency, not a gate failure. | 0144N brief step 4 ("the traceability baseline is regenerated and consistent"); Documentation Standards §7 item 8 | S3: update `tools/wp001_ownership.json` note text for the symbol and regenerate `wp001_api_traceability.md` to reflect the WP-036C S1 (0144M2) delivery; refresh the Migration Guide `retrain_controller` row. |
| WP036C-F9 | D4 | `pyproject.toml` `[tool.ruff.lint.per-file-ignores]` — new entries `"python/prin/kernels.py" = ["S603"]`, `"python/prin/simulation.py" = ["D107","D417"]`, `"python/prin/training_hooks.py" = ["D107"]`, `"python/prin/nn/{slot_attention,temporal_compat,ablation_variants}.py"` | Lint-gate scope narrowed on **first-party shipped modules** (not faithful-copy test ports): the `S603` flake8-bandit security rule is suppressed project-wide for `kernels.py` rather than remediated or inline-`# noqa`-justified (the underlying `_find_msvc_cl` subprocess code *is* Coding-Standards-§6.1-compliant — absolute exe, list args, no shell — so the risk is only the blanket future suppression), and pydocstyle `D107`/`D417` are suppressed on four `prin` modules. Not disclosed as governance deltas in the handoff. | Coding Standards §6 / CLAUDE.md §3 ("Do not suppress or exclude findings without approved, evidence-backed governance"); Documentation Standards §2 | S3: replace the `kernels.py` `S603` per-file-ignore with an inline `# noqa: S603` carrying the vswhere-is-trusted rationale (or remove it — bandit already reports it as an accepted Low); add the missing `__init__`/arg docstrings to the four modules, or record the D-rule ignores in the handoff/PSR as a deliberate decision. |

**Observations (non-findings):**

1. **Port fidelity is genuinely high.** The import-only discipline held across
   1,097 functions with zero assertion drift and zero tolerance annotations —
   the hard part of a strict port. The FAIL is about stopping at "ported +
   triaged" instead of "ported + green / governed."
2. **DV-025 is substantively resolved** — `retrain_controller` is real and its
   reference tests pass; only the traceability-doc narrative (F8) lags.
3. **`test_acceptance_y4q3.py` recursive-pytest meta-tests** make the default
   gate materially slower; candidate for the PSR risk register.
4. **Coverage instrumentation host-blocked** (pre-recorded); CI codecov
   authoritative at S4 — same disposition as the WP-036B / WP-036D S2 audits.

## 5. Deviation-ledger delta

New findings for the cumulative ledger (PSR-036C §3):

| ID | Severity | Status |
|---|---|---|
| WP036C-F1 | D1 | OPEN → S3 |
| WP036C-F2 | D1 | OPEN → S3 |
| WP036C-F3 | D2 | OPEN → S3 |
| WP036C-F4 | D3 | OPEN → S3 |
| WP036C-F5 | D2 | OPEN → S3 |
| WP036C-F6 | D4 | OPEN → S3 |
| WP036C-F7 | D4 | OPEN → S3 |
| WP036C-F8 | D4 | OPEN → S3 |
| WP036C-F9 | D4 | OPEN → S3 |

Carried findings re-inspected: none open at PSR-036D (WP-036D S3 closed
WP036D-F1/F2/F3 CLEAN). DV-025 re-inspected: `retrain_controller` delivered
(0144M2); reclassify from "deferred to WP-036" to "delivered WP-036C S1
0144M2" at S3/S4. DV-001 / DV-030 untouched and correctly out of scope
(`test_triton_kernels` stays guarded; no device-resident GPU work here).

## 6. Verdict and required actions

**Verdict: FAIL** (two D1, two D2, one D3, four D4).

The strict port itself is well executed: all 1,097 reference functions are
ported with import-only adaptation, zero weakened assertions, zero tolerance
annotations, DV-025's `retrain_controller` delivered, and every Rust/Python
quality gate green. But the WP's defining acceptance criterion — *the full
ported acceptance suite green on CPU* — is not met: **78 ported acceptance
tests fail in the default CI gate**, independently reproduced, and S1 closed
its exit gate by routing all 78 into an "out-of-scope discovery" bucket the
0144M brief does not authorise, with no maintainer-approved quarantine for any
of them. Several classes are in-scope repairs the contract explicitly required
(gradient flow through the Rust bridge; a Rust panic crossing the FFI boundary;
missing backend guards; a self-inflicted version-string break). Per Development
Workflow §3 a FAIL freezes new feature work until S3 clears it.

**Ordered S3 action list:**

1. **WP036C-F1 / F2 (D1 first).** Triage all 78 failures. For each: fix in the
   owning Rust crate / compat layer, or apply `@pytest.mark.skip(reason=…)`
   with a linked tracked issue/DV item **and** maintainer approval, or obtain a
   plan amendment. Priority order: the two gradient-flow + two FFI-panic cases
   (F2) → the ~8 CUDA/GPU-guard cases (F3) → the ~5 `prin.reporting._artifacts`
   behaviour cases → the ~55 benchmark-artefact cases (governed skip or
   amendment) → the RNG case (annotation).
2. **WP036C-F5.** Maintainer decision on the version string (`3.0.0` vs `0.3.0`
   vs governed skip); record in the amendment log.
3. **WP036C-F4.** Restore `check_no_python_numerics` scope + move the Python
   `np.polyfit`/`lstsq` fits to Rust, **or** a maintainer-approved amendment
   sanctioning the exclusions.
4. **WP036C-F7.** Clean the working tree (`benchmarks/results/y4q1_9_preregistration_hash.json`).
5. **WP036C-F6 / F8 / F9 (D4).** Correct the handoff consolidation narrative;
   regenerate the DV-025 traceability rows; convert the `kernels.py` `S603`
   per-file-ignore to an inline justified `# noqa` (or drop it) and resolve the
   `D107`/`D417` module ignores.
6. Delta re-audit: re-run the full default gate to green (or every non-green
   test governed), re-diff any touched ported test, re-run the quality gates,
   append the §7 closure table.

**Maintainer acknowledgment of the verdict:** acknowledged by MichaelMaillet
2026-09-01 (WP-036C S3 `0144O` session, `AskUserQuestion`): "acknowledge,
proceed with S3; address failures as part of S3 remediation along with the
rest of the ordered S3 action list." S3 disposition decisions recorded in the
same exchange — F5 governed skip + amendment; F4 restore scan + port fits to
Rust (bridge-module entries); F1/F2 new DV item + governed skips.

**Handoff:** `0144O` (WP-036C S3 — Remediation).

---

## 7. Closure table (appended by S3 remediation — session `0144O`)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP036C-F1 | **FIXED / AMENDED.** The 78-test failure set dispositioned: (a) 2 gradient tests **FIXED** by the F2 STE; (b) 11 `y4q2` reporting-batch tests **FIXED** by restoring reference-faithful graceful degradation in `generate_all_figures` / `generate_all_tables` (`test_publication_generation.py::test_master_generators_degrade_on_missing_artefact` updated); (c) 5 version tests **AMENDED** (plan amendment #41); (d) 9 CUDA-execution tests + ~52 unbuilt-Phase-6-deliverable tests + 2 recursive meta-tests **AMENDED** via new register item **DV-031** and a single `tests/conftest.py` `pytest_collection_modifyitems` governed-skip hook (no ported test file edited — assertions + text byte-unchanged); (e) 1 RNG-regime test **AMENDED** (F3, `parity_report.rst` entry). One pre-existing WP-036B perf-ratio flake (`test_no_gpu_throughput_regression`, not an S2 finding) quarantined in the same hook, flagged in PSR-036C. | `b240836` (F2 STE), `e342566` (reporting degradation), `106480b` (conftest / DV-031 / amdt #41), `b753199` (flake quarantine); plan amendment #41; DV-031 | Full default gate `pytest tests/ -m "not slow and not gpu"`: **2743 passed, 201 skipped, 0 failed** (356 s; `y4q3` runs, no hang). A4 re-diff: `git diff e49fb1b -- tests/test_acceptance_*.py` is **empty**. |
| WP036C-F2 | **FIXED / AMENDED.** Gradient half **FIXED**: `DiscreteDeltaThetaGamma.step` / `.integrate` add a value-preserving straight-through identity term over the phase/amplitude inputs (the input-side analogue of the M1 parameter zero term); `y4q1_8::test_gradient_sign` + `test_gradient_flow` pass; regression `test_hierarchical_layers.py::test_discrete_dtg_step_integrate_pass_input_gradients_through`. FFI-panic half **AMENDED**: the 2 `y2q3` `#[pyclass(unsendable)]`-ctx-on-autograd-worker-thread panics deferred to **WP-036E** via **DV-031(B)** + conftest skip. | `b240836`; DV-031(B) | `pytest tests/test_acceptance_y4q1_8.py -k "gradient"` green; `pytest tests/test_hierarchical_layers.py` 13 passed; `cargo test -p prin-sim` 164 passed; the 2 `y2q3` cases skip with a DV-031/WP-036E reason. |
| WP036C-F3 | **FIXED / AMENDED.** GPU backend-guard half: the 6 `test_acceptance_gpu.py` CUDA cases + `y4q3::TestCUDAJIT::test_cuda_jit_compiles` execute-and-fail on a CUDA host because PRIN's bridges have no device-resident path — **AMENDED** to **WP-036E** via **DV-031(B)** + conftest skip (same disposition class as WP-036D S3 / DV-030). RNG case **AMENDED**: `y4q1_3::test_cosine_kernel_affects_dynamics` — new `parity_report.rst` "WP-036C — Deterministic-`Seed` RNG regime" section + conftest skip citing the M5 sub-pass disposition. | conftest / DV-031(B); `parity_report.rst` §"WP-036C — Deterministic-`Seed` RNG regime" | Default gate green; `test_acceptance_gpu.py` on this RTX 4060 host: 6 skipped (DV-031), rest pass; `y4q1_3` 48 passed / 1 skipped. |
| WP036C-F4 | **FIXED.** New Rust owner `prin_sim::y4q1_stats::polyfit` (`numpy.polyfit` semantics, 3 unit tests) + `SimError::InvalidInput` + PyO3 `_prin_core.y4q1_polyfit`. `y4q1_tools.py`'s 6 polynomial-fit sites (`np.linalg.lstsq` + 5 `np.polyfit`) now delegate to it. `y4q1_tools.py` and `temporal_training.py` **restored** to `check_no_python_numerics._MODULES` (17 → 19) as bridge-module entries (`hierarchical_layers.py` precedent — nn.Module composition over the Rust-backed `DiscreteDeltaThetaGamma` + a stock loss); `test_no_python_numerics.py` asserts both covered. Maintainer decision (AskUserQuestion 2026-09-01): restore + port to Rust, bridge-module entries. | `665c358` | `tools/check_no_python_numerics.py`: "No Python numerics in **19** WP-036 S1 compat modules." `cargo test -p prin-sim` 164 passed; `pytest tests/test_acceptance_y4q1_{2,5,7,8,9}.py` green (numerically equivalent). |
| WP036C-F5 | **AMENDED.** Plan **amendment #41** (2026-09-01, maintainer-approved): PRIN is independently versioned (`0.3.0` → `1.0.0-rc1`, Plan §6/§9), not a continuation of PRINet 3.0's numbering. The 5 ported version/classifier/citation tests carry a `tests/conftest.py` governed skip citing the amendment; re-pointed at PRIN's own version at **WP-038**. Assertions byte-unchanged. | plan amendment #41; conftest | `pytest tests/test_acceptance_y4q3.py::TestVersionAPI tests/test_acceptance_y4q4.py::TestVersionConsistency`: version tests skip with the amendment-#41 reason; `test_version_is_valid_semver` / `test_public_api_surface` still pass. |
| WP036C-F6 | **FIXED.** `DOCS/experiments/0144M-wp036c-s1-handoff.md`: added an in-place correction note on the M8 command-evidence line (the "14 pre-existing + 64 new … No regressions" framing) stating the PSR-036D baseline was `1784 passed / 2 skipped / 0 failed` and all ~78 (79 incl. the M1 slow test) were S1-introduced; fixed the handoff-summary "No regressions" row and the "thin wrapper" DV-025 row. | `22e209d` | `grep -n "No regressions" DOCS/experiments/0144M-wp036c-s1-handoff.md` → only inside the correction quote; PSR-036D figure cited. |
| WP036C-F7 | **FIXED.** `benchmarks/results/y4q1_9_preregistration_hash.json` (untracked benchmark side-effect) removed. It was never tracked, so no commit object represents the deletion; the tree is clean. | (working-tree cleanup, no commit needed) | `git status` clean; `git log --all --oneline -- benchmarks/results/y4q1_9_preregistration_hash.json` empty. Note: its removal correctly flipped `y4q2::TestArtefactCompleteness::test_has_json_files` from pass→fail (repo genuinely has 0 benchmark JSON) → now DV-031(A). |
| WP036C-F8 | **FIXED.** `tools/wp001_ownership.json` `retrain_controller` basis rewritten to record the 0144M2 delivery; `DOCS/baselines/wp001_api_traceability.md` regenerated (`wp001_baseline.py traceability`). `DOCS/sphinx/migration_guide.rst`: the "0141E symbol dispositions" table + prose rows for `retrain_controller` / `MixedPrecisionTrainer` / `AsyncCPUGPUPipeline` corrected from "D-2.2 stub" to real (0144M2 / 0144M4); `DiscreteDeltaThetaGamma` row notes the F2 STE. `DEFERRED_VALIDATION_REGISTER.md` DV-025 status appended. | `421594b` | `wp001_baseline.py check`, `wp036_migration_table.py check`, `check_dv_register_gates.py` all pass. |
| WP036C-F9 | **FIXED.** All 8 first-party per-file `ruff` ignores removed from `pyproject.toml`. `kernels.py` `S603` → inline `# noqa: S603` with the vswhere-is-MS-signed / absolute-path / constant-args / no-shell / no-user-input rationale (bandit still reports it as an accepted Low). Missing `__init__` / method / dunder docstrings added to `simulation.py`, `training_hooks.py`, `nn/slot_attention.py`, `nn/temporal_compat.py`, `nn/ablation_variants.py`, `nn/phase_tracker.py`, `y4q1_tools.py`; `y4q1_tools.__all__` sorted. | `8f72223` | `ruff check` + `ruff format --check` (234 files) clean; `mypy --strict` (62 files) clean; `interrogate` 97.6%. |

**Delta re-audit date:** 2026-09-01 — **Result:** **CLEAN.**

### Delta re-audit evidence (S3 `0144O`)

All commands from `C:\dev\PRIN`, Windows 11, Python 3.14.0, pytest 9.1.1,
`-p no:cov` (coverage host-blocked, [[wp036-coverage-tooling-blocked]]).

```
# A3 / A9 — full default gate (the WP036C-F1 acceptance criterion)
.venv/Scripts/python -m pytest tests/ -p no:cov -m "not slow and not gpu" -q --tb=line -rf
#  → 2743 passed, 201 skipped, 25 deselected, 0 failed  (356 s; y4q3 runs, no recursive-pytest hang)

# A4 — no ported test file touched
git diff e49fb1b --stat -- tests/test_acceptance_*.py        # (empty)

# A5 — Rust + Python quality gates
cargo fmt --all -- --check                                   # exit 0
cargo clippy --workspace --all-targets -- -D warnings        # clean
cargo test --workspace                                       # 48 suites ok, 0 failed
cargo test -p prin-sim --lib                                 # 164 passed (incl. 3 new polyfit tests)
.venv/Scripts/ruff check python/ tests/ benchmarks/ tools/   # All checks passed!
.venv/Scripts/ruff format --check python/ tests/ benchmarks/ tools/   # 234 files already formatted
.venv/Scripts/mypy python/prin --strict                      # no issues in 62 files
.venv/Scripts/interrogate -c pyproject.toml python/prin      # 97.6% PASSED

# A6 — security
.venv/Scripts/bandit -r python/prin -c pyproject.toml        # 3 Low (pre-existing kernels B404/B603, hybrid_compat B110), 0 Med/High
snyk code test python/prin tests crates/prin-sim/src crates/prin-py/src --severity-threshold=low   # Total issues: 0
cargo audit                                                  # exit 0; 3 governed allowed warnings
git diff Cargo.lock                                          # (empty — no dependency change; pip-audit N/A)

# A1 / A2 — governance tooling
.venv/Scripts/python tools/check_no_python_numerics.py       # "No Python numerics in 19 ... modules"  (restored from 17)
.venv/Scripts/python tools/wp036_migration_table.py check    # OK (172 symbols)
.venv/Scripts/python tools/wp001_baseline.py check           # passed
.venv/Scripts/python tools/check_dv_register_gates.py        # passed (31 rows × 198 entries)
.venv/Scripts/python -m pytest tests/test_wp001_baseline.py tests/test_no_python_numerics.py tests/test_migration_guide_consolidated.py -p no:cov -q   # 58 passed

# A8
git status   # clean (F7 artefact removed)
```

**Findings status:** F1 FIXED/AMENDED · F2 FIXED/AMENDED · F3 FIXED/AMENDED ·
F4 FIXED · F5 AMENDED (#41) · F6 FIXED · F7 FIXED · F8 FIXED · F9 FIXED. No D1
or D2 remains open; no D4 carried. New governance artefacts: plan amendment
#41, DV-031. One new observation (non-finding): the pre-existing WP-036B
`test_no_gpu_throughput_regression` perf-ratio flake, quarantined and flagged
in PSR-036C for a perf-test disposition.

**Exit gate:** met. Hand off to S4 (`0144P`).
