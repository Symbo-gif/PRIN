# DV-043 — nightly `bench-regression` triage and hotfix handoff

**Session:** `Hotfix-DV043`, opened when a maintainer-declared **EXP-001-r1 E3**
entry check found E3 blocked instead.<br>
**Date:** 2026-09-28 UTC. **AI pair:** Qwen Code.<br>
**Branch:** `hotfix/dv043-redundant-step-guard`, off `main` @
`5615edab5b53afd6602907343a596cdc3f8dff4a`.<br>
**Authority:** campaign plan §10.2 ("Red `nightly.yml` not dispositioned (fixed
or dated DV row) at an E3 start → Disposition first (§11)"), §11 (gap
dispositions), §14.2 amendment #9; Development Workflow and Audit Standards §7
(hotfix class — a defect on a live `main`); Deferred Validation Register
**DV-043**.<br>
**Deliverable:** a root-caused disposition of `nightly.yml` run `36380992897`
and the fix that disposition selected. **Not** an experiment result, **not** a
campaign verdict, and **not** an EXP-001-r1 E-stage.<br>
**Independent audit:** [`DOCS/audits/2026-09-28-dv043-redundant-step-guard-audit.md`](../audits/2026-09-28-dv043-redundant-step-guard-audit.md)
— verdict `PASS-WITH-FINDINGS`, no D1, seven findings `DV043-F1`…`DV043-F7`,
all remediated; delta re-audit pending.<br>
*Post-session, 2026-09-28 UTC:* Subsequent independent delta re-audit is
recorded in the audit report §7 (F8/F9 D4 fixed; full-workspace
strict-checks, hotfix merge and green nightly are not claimed).

---

## 1. Why this session exists

The maintainer declared `EXP-001-r1` **E3**. Its entry conditions were checked
rather than assumed, and E3 could not start. Four independent blockers, each
re-derived from the repository or from GitHub:

| # | Blocker | Authority | Status at this session's close |
|---|---|---|---|
| 1 | **The E2 wgpu gate is only half closed.** DV-041's fix merged (PR #25, `5615eda`, all six required workflows green — re-verified here), but `preregistration.md` §10 sets a *conjunctive* gate: the pre-registration "does not freeze and E3 does not start until DV-041 closes **and** a follow-up E2 amendment (a normal pre-execution edit) records the **tested wgpu leg**". `benchmarks/campaign/exp001_r1_driver.py` registers exactly four modes (`corpus`, `fuzz`, `repeatability`, `kernel-path`→CUDA) and contains no `wgpu` or `backend_name` reference. Campaign plan §5.2 marks the EXP-001 H1-wgpu leg "● required". | preregistration §10 item 2; campaign plan §5.2, §12 rules 1–2 | **OPEN** — needs a pre-execution amendment session. §12 rule 1 forbids adding driver code at E3; rule 2 forbids collapsing the stages. |
| 2 | **Red nightly, undispositioned.** Run `36380992897` (2026-09-28, `149cf2d`): `full-suite` green, `bench-regression` FAILED with ten gated breaches. Nothing in `DOCS/` or the DV register dispositioned it. | campaign plan §10.2 | **DISPOSITIONED AND FIXED by this session** (DV-043, §11.8, amendment #9). Closure gate: merge green + one green nightly. |
| 3 | **Baseline code changed between E2 and E3.** PR #25 landed `crates/prin-sim/src/gpu.rs` (+256), `crates/prin-kernels/src/sparse_knn/cubecl.rs` (+39) and `crates/prin-py/src/bindings/gpu.rs` (+29) *after* EXP-001-r1's E2. | campaign plan §10.2 | **OPEN** — E3/E4 must record the new SHA, E5 must list the diff as a protocol deviation, and because a numeric kernel crate changed, H4's 72 `kuramoto_sparse_knn` configurations are a regression leg. |
| 4 | **Stale governance records.** DV-041's register row still reads `OPEN — FIX COMMITTED … Not yet merged to main`; `SESSION_REGISTER.md`'s `EXP-001-D1` row still says "draft **PR #24**, not merged … S2–S4 pending" and its `Hotfix-DV041` row still says "**PR not yet opened**"; `DOCS/sessions/contingencies/README.md` still shows EXP-001 D1 as "OPEN … S2 is next". Both DV-041 rows also exist in **two divergent versions** (main's post-hotfix text vs the E2-era text on `campaign/exp001-r1-e1`), which will conflict when that branch merges. | campaign plan §12 rule 3; DV register update protocol | **OPEN, deliberately not touched here** — see §8. |

Presented with the choice of triaging blocker 2, doing blocker 1's amendment
work, or both, the maintainer selected **the nightly regression triage**. This
session is that triage plus the fix its disposition selected.

## 2. Entry evidence

```text
gh pr view 25 --json state,mergedAt,mergeCommit,headRefOid
  state: MERGED   mergedAt: 2026-09-28T19:28:17Z
  mergeCommit: 5615edab5b53afd6602907343a596cdc3f8dff4a
  headRefOid:  bc29ae50a7750709fdebab4597ed935bbef893e8

.venv\Scripts\python.exe tools/check_ci_green.py 5615edab5b53afd6602907343a596cdc3f8dff4a
  rust 36472465486 · python 36472465585 · parity 36472465709
  repro 36472465699 · snyk 36472465698 · gpu 36472465689
RESULT: all required workflows green
```

`nightly.yml` history at the entry check (`gh run list --workflow=nightly.yml`):

| Run | Date | Head SHA | Conclusion |
|---|---|---|---|
| `36380992897` | 2026-09-28 | `149cf2d` | **failure** — `bench-regression` red, `full-suite` green |
| `36296497434` | 2026-09-27 | `ce4049f` | success |
| `36220053956` | 2026-09-26 | `ce4049f` | success |
| `36097588776` | 2026-09-25 | `ce4049f` | success |

No CI run was in flight during the local measurement window below (`gh run list`
returned six completed runs and nothing queued or in progress), so the
self-hosted runner service was left running rather than stopped: campaign plan
§5.3's quiescence rule binds C2 *timing claims*, and this is a diagnostic A/B,
not a campaign timing leg. No push to `origin/main` overlapped the window
(§5.3 item 4).

## 3. The breach set

`gh run view 36380992897 --log-failed`, from `tools/check_bench_regression.py`
(`--threshold 0.10`, `--advisory criterion/control_buffer_read_under_contention/`,
fixed `REFERENCE_SHA: 4590d611f34eae5dfcdadb99b562aacf998d6e94`):

Ten gated breaches, +10.1 % … +28.8 %, **all** in two families:
`criterion/engine_step/step_parallel/{1024,4096,16384}` and
`criterion/sweep_parallel/run_sweep_{parallel,serial}/*`.

Everything else was flat, and the flat set is diagnostic:

| Family | Ratio range | Enters an integrator step? |
|---|---|---|
| `engine_step/step_parallel/*` | 1.048 – **1.288** | yes (RK4 over `SparseKuramoto`) |
| `sweep_parallel/run_sweep_*` | 1.077 – 1.125 | yes (RK4 over `SparseKuramoto`/`SparseStuartLandau`) |
| `engine_step/derivatives_{parallel,serial}/*` | 0.983 – 1.036 | **no** — same group, same model, same N and state, `compute_derivatives` only |
| `spmv_coupling/*` | 0.952 – 1.067 | no |
| `resonance_layer_bridge_baseline/moderate` | **0.914** (faster) | no |
| `phase_tracker_bridge_baseline/*`, `pytest/*`, `training_hooks_*`, `discrete_step_3band/*`, `sparse_knn_n16k_k14`, `mean_field_rk4_n1m` | 0.977 – 1.012 | no |
| `control_buffer_read_under_contention/*` | 0.989 – 1.398 | advisory only, not gating |

The `derivatives_*` arms are a **built-in control**: they sit in the same
criterion group, are constructed from the same `SparseKuramoto` and the same
`OscillatorState` as `step_parallel`, and differ only in that they never reach
an integrator (`sweep_bench.rs:163-176` vs `:152-159`). They stayed flat while
`step_parallel` breached.

## 4. Attribution

Two independent windows, both pointing at one commit:

1. **Green→red window.** `git log --oneline ce4049f..149cf2d` is PR #24 alone
   (the EXP-001 D1 correction). Three consecutive nights at `ce4049f` were green
   against the *same* fixed reference `4590d611`.
2. **Whole measured range.** `git log 4590d611..ce4049f -- <the eight step/sweep
   hot-path files>` (`prin-dynamics/src/{integrate,state,models}.rs`,
   `prin-sim/src/{engine,sweep,csr_coupling,dispatch}.rs`,
   `prin-sim/benches/sweep_bench.rs`) returns **empty**. Across all 69 commits
   between the fixed reference and the last green night, nothing touched the hot
   path. `Cargo.lock`, `rust-toolchain.toml`, `nightly.yml` and
   `tools/check_bench_regression.py` are also unchanged in `ce4049f..149cf2d`;
   the only other change there is `pyproject.toml` (+9), and every `pytest/*`
   group was flat.

So PR #24 is the only hot-path change in the *entire* comparison window, not
merely the only commit since the previous night. This is not the DV-036
host-variance class, and §11.6's rule applies: the breach was investigated, not
retried until green.

## 5. Root cause

`34e8811` (*fix(prin-dynamics): PRINet 3.0 OscillatorModel guard semantics for
Euler/RK4*) introduced `GuardPolicy { NonNegative (default), Bounded }` and a new
`GuardPolicy::derivatives(&mut buf)` that walks the flat `3N` derivative buffer,
wired into the fixed-step integrators at five sites: `EulerIntegrator::step` and
RK4's k1 (via `flatten`), k2, k3 and k4.

That pass is **load-bearing** for the models the same commit switched to
`StateDerivatives::unclamped` — the full and mean-field Kuramoto/Hopf paths and
the Stuart–Landau paths. It is **redundant** for the sparse k-NN paths, which
kept their own clamp at construction through `StateDerivatives::new`:
`prin-sim/src/engine.rs:191` and `:329`, `prin-dynamics/src/models.rs:431`,
`:698`, `:1000`, `prin-dynamics/src/bands.rs:580`, `prin-sim/src/gpu.rs:616`,
`:647`, `:662`.

And the benchmarked path is exactly the redundant one: `OscilloSim::new` rejects
a `NonNegative` fixed-step integrator in debug builds, `run_single_config`
(`sweep.rs:305-308`) pins `Bounded`, and `sweep_bench.rs:144` pins `Bounded` —
all over sparse models. Every RK4 step therefore re-walked **four `3N` buffers**
to re-clamp values already inside the bound.

The second pass is provably value-identical: both sites use the same
`guard_derivative_value` / `clamp_derivative` and the same `±DERIV_CLAMP`;
`clamp_derivative` is idempotent across `NaN`, `±Inf`, `-0.0` and values exactly
at the bound; and nothing mutates the buffer between construction and the pass
(`extend_from_slice`, no arithmetic in between). Under `strict-checks` the
constructor already rejects an out-of-range value, so the integrator's
diagnostic cannot be the first to fire.

In the default (non-`strict-checks`) build — which is what `nightly.yml` builds,
since it passes no `--features strict-checks` — the loop was doubly wasteful:
`guard_derivative_value` is defined as `Ok(clamp_derivative(d))`, its value was
discarded by the `?`, and `*d = clamp_derivative(*d)` computed the same clamp
again.

**Quantitative fingerprint.** Converting the breaches to per-oscillator-per-RK4-step
deltas:

| Identity | Δ ns / oscillator / step |
|---|---|
| `step_parallel/1024` | 25.5 |
| `step_parallel/4096` | 25.3 |
| `run_sweep_serial/32_configs` | 25.9 |
| `run_sweep_serial/64_configs` | 24.8 |
| `step_parallel/16384` | **73.0** — outlier, see §7 |

Four identities across two benchmark families agree on ~25 ns, i.e. ~2.1 ns per
guard element-visit over the 12 visits per RK4 step (4 stages × 3 components).

## 6. Independent verification

The root-cause claim was handed to a fresh-context reviewer with instructions to
break it, to answer five questions with `file:line` evidence, and to run no
build or benchmark (so it could not perturb the measurement window). Its
verdicts: the dead-work claim **CONFIRMED** (including the double
`clamp_derivative` and that `nightly.yml` builds non-strict); competing
explanations inside PR #24 **REFUTED** — no new allocations (the `self.k1.clone()`
workspace clones predate PR #24 and are already listed in the correction audit as
a separate pre-existing performance item deferred to S2), no rayon/dispatch/`reserve`
changes, and the `models.rs` edits are cost-*reducing* and off the sparse path;
the control **CONFIRMED**; prior documentation or acceptance of this overhead
**REFUTED** (`34e8811`'s "Bounded reproduces the pre-correction behaviour
exactly" is a semantics claim, and its verification list contains no benchmark
entry). The reviewer also produced the §4 whole-range attribution independently
and derived the ~25 ns fingerprint from the reported ratios.

It found one design trap this session had missed, which shaped the fix: see §7.

## 7. Reference-host A/B, and its honest limits

A four-pass counterbalanced A/B on H1, following campaign plan §11.6
amendment #4's methodology: equal-length sibling checkouts
`.qwen/tmp/arms/reference` @ `ce4049f` and `.qwen/tmp/arms/candidate` @
`149cf2d`, separate cold target directories, fixed order
reference → candidate → candidate → reference, each arm's value the arithmetic
mean of its two passes, `cargo bench --bench sweep_bench` filtered to
`engine_step/|sweep_parallel/`.

Result — median candidate/reference ratio:

| Family | Identities | Median ratio | Range |
|---|---|---|---|
| Integrator path (`step_parallel`, `run_sweep_*`) | 15 | **1.075** | 1.000 – 1.105 |
| Derivative-only control (`derivatives_parallel`) | 7 | 1.023 | 0.881 – 1.058 |

**The family selectivity reproduces on a second host**, which is the key
discriminator against "host noise": noise would not spare the derivative-only
arms sitting in the same criterion group, same process, same model and same N.

**But this A/B cannot resolve a ~10 % effect per identity, and is not claimed
to.** Within-arm pass-to-pass drift reached ±13 %; `derivatives_parallel/4096`
moved −12 % (a control that should not move at all, since PR #24 did not change
the sparse `compute_derivatives` path); and `run_sweep_parallel/16_configs` was
bimodal at 982 ms vs 1556 ms *inside the candidate arm*. Two passes per arm at
criterion's `sample_size(10)` / 3–5 s windows on this host is below the
resolution the question needs.

**Consequence for the headline number.** `step_parallel/16384`'s +28.8 % did
**not** reproduce locally (ratio 1.023). The `PARALLEL_LEN_THRESHOLD = 32_768`
boundary (`dispatch.rs:28`) does not explain it either: 16384 is the last
sequential size while 65536+ is parallel, and since the guard pass is a
sequential `for` loop while the base parallelises, that predicts ratios *rising*
above the threshold — they fall (1.288 → 1.057 → 1.076 → 1.048). Per-visit cost
by N is 2.12, 2.11, **6.08**, 0.94, 1.21, 0.85 ns — a spike with lower
neighbours on both sides, which no monotone cache-capacity story produces.

The +28.8 % is therefore recorded as a hosted-runner cache/measurement artefact
sitting on top of a real ~+10 %, and is explicitly **not** claimed as explained.
The fix is validated per identity, with `step_parallel/16384` re-measured
specifically, rather than by the aggregate gate.

## 8. The fix, and the design choice behind it

`StateDerivatives` now carries `#[serde(skip)] pub(crate) guarded: bool`, set
`true` by `new()` and `false` by `unclamped()` and by the two finite-difference
gradient sites (`models.rs`, and the adjoint gradient in `integrate.rs`) plus the
two test-only models that deliberately bypass the constructors. It is exposed
read-only as `pub fn is_guarded(&self) -> bool`. `GuardPolicy::derivatives` takes
that flag, returns immediately when it is set, and otherwise *assigns*
`guard_derivative_value`'s result instead of discarding it and clamping a second
time — which removes the duplicate work in both feature configurations with one
expression and keeps the strict-checks early-return semantics exactly.

**Why a flag on the value rather than a declaration on the model.** A defaulted
`Dynamics` trait method would avoid the API break, but it would duplicate each
model's `n <= 1` branch logic in a second place: `SparseKuramoto` returns
`unclamped` at `engine.rs:175` and `new` at `:191`, so a static per-model
declaration would be *wrong* at N=1, and a per-`n` one could drift from the branch
actually taken and silently drop the guard. That is the failure class the EXP-001
D1 correction exists to prevent. Setting the flag at the construction site makes
drift structurally impossible.

**The trade-off accepted, stated plainly.** The three derivative arrays remain
`pub`, so the flag is a construction-time fact, not an invariant maintained
across mutation: a caller that edits `dphase` after construction invalidates it,
and the integrator would then skip a bound it should have applied. Today's
unconditional re-clamp is robust to that and the fix is not. Nothing in this
workspace mutates a `StateDerivatives` after construction, and the `Dynamics`
contract is that `compute_derivatives` returns the values it just built — but
that is a claim about today's code, not a guarantee, and it is recorded here and
in the field's own doc comment rather than left implicit. This was the reviewer's
"main soundness regression" finding and the maintainer accepted it as part of
selecting the fix.

**Public API.** Adding a private field to a public struct with public fields
breaks downstream struct-literal construction and exhaustive destructuring.
Permissible at `1.0.0-rc1` under Versioning and Release Standards §1's
**pre-1.0** bullet ("Pre-1.0: minor bumps may break API; each roadmap phase
exit is tagged as a pre-release (`v0.Y.0-alpha.N` / `-rc.N`)"): the workspace
is at a pre-release and `1.0.0` — the feature-complete milestone — has not
shipped, so the *post*-1.0 stability regime (major bump, a deprecation cycle of
≥1 minor release through the `_deprecation` machinery, and Migration Guide
entries) is not yet in force. A Migration Guide entry is supplied regardless.
The post-1.0 clause is **not** the authority here and would forbid this change
as implemented; the independent audit raised that mis-citation as DV043-F4
(D3) and it is corrected in all four documents that carried it. `PartialEq` is
now a manual implementation over the three arrays so equality semantics are
*preserved* rather than changed, and `#[serde(skip)]` keeps the wire format
identical (a deserialized value reports `false`, the conservative answer).
`StateDerivatives` is not serialized into any persisted artefact, and `prin-py`
wraps it as `PyStateDerivatives { inner }` exposing only the three arrays, so no
Python surface or `.pyi` stub changes.

**Tests added in tandem** (Coding Standards §5):

| Test | Pins |
|---|---|
| `state::guarded_flag_records_which_constructor_ran` | the flag tracks the constructor |
| `state::guarded_flag_is_provenance_and_changes_no_public_contract` | equality and the serialized form ignore the flag; round-trip is the conservative `false` |
| `integrate::bounded_step_skips_the_redundant_pass_without_changing_any_value` | **the load-bearing one** — a `Bounded` Euler and RK4 step over a guarded source is *bit-identical* to one over an unguarded source with the same values, at rates inside and exactly at `±DERIV_CLAMP` |
| `integrate::bounded_step_still_clamps_derivatives_the_model_left_unclamped` | the skip is keyed on provenance, not policy: an out-of-range unguarded derivative is still repaired |
| `engine::sparse_models_report_the_guard_they_actually_applied` | `SparseKuramoto`/`SparseStuartLandau` report guarded at `n > 1` and **not** guarded at `n <= 1`, so the `Bounded` guard still runs on the single-oscillator branch |

Every pre-existing guard test still exercises the guard, because all of them
(`bounded_guard_silently_clamps_large_derivatives_like_pre_correction`,
`bounded_guard_clamps_every_derivative`,
`bounded_guard_rejects_out_of_range_derivatives_under_strict_checks`,
`rk45_and_exponential_use_model_derivatives_unclamped`) are built on models that
return `unclamped` — so none was weakened by the change, and none needed editing.

## 9. Verification ledger

### 9.1 Before the audit remediation (the state the independent auditor reviewed)

| Gate | Result |
|---|---|
| `cargo check --workspace --all-targets` | clean |
| `cargo check -p prin-dynamics -p prin-sim --all-targets --features prin-dynamics/strict-checks` | clean |
| `cargo fmt --all -- --check` | clean |
| `cargo clippy --workspace --all-targets -j 1 -- -D warnings` | clean |
| `cargo test --workspace -j 1` | **1603 passed / 0 failed / 1 ignored**, 48 test binaries |
| `cargo test -p prin-dynamics --lib -j 1 --features strict-checks` | 309 passed / 0 failed |
| `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | clean |
| `pytest parity/` | **2144 passed / 1 skipped** — includes the 504-case PRIN-vs-corpus gate and the 1,000-case registered `Seed(0,1)` stream gate |
| `pytest tests/ -m "not slow and not gpu"` | 3277 passed / 178 skipped / 54 deselected, **5 failed** (accounted for in §9.4) |
| `ruff check` / `ruff format --check` / `mypy --strict` / `interrogate` / `bandit` | clean / 316 files formatted / 62 files clean / 97.6 % / exit 0 |
| Snyk Code, `severity_threshold=low`, org `symbo-gif` | **0 issues** on `crates/prin-dynamics/src` and on `crates/prin-sim/src/engine.rs` |
| `tools/check_dv_register_gates.py` | passed — 43 DV rows against 198 session entries |
| `tools/check_global_session_registration.py` | passed — 17 Executive Audit reports |

`pytest parity/` is the load-bearing numerical evidence: 1,504 real integration
cases across every model/coupling/integrator cell, unchanged by a fix whose whole
claim is that it changes no value.

### 9.2 After the audit remediation

| Gate | Result |
|---|---|
| `cargo fmt --all -- --check` | clean |
| `cargo clippy -p prin-dynamics -p prin-sim --all-targets -j 1 -- -D warnings` | clean, first attempt |
| `cargo test -p prin-dynamics --lib -j 1` | **309 passed / 0 failed** (was 308; +1 for the new idempotency test) |
| `cargo test -p prin-sim --lib -j 1` | **165 passed / 0 failed** |
| `cargo test -p prin-dynamics -p prin-sim --lib -j 1 --features prin-dynamics/strict-checks` | **310 + 165 passed / 0 failed** — partially closes DV043-F2; the *workspace-wide* strict-checks run it asked for is still blocked (§9.4) |
| `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | clean; the new `state::StateDerivatives::is_guarded` intra-doc link resolves |
| Sphinx `-W --keep-going -b html`, `DOCS/sphinx/_build` deleted first | build succeeded, `[new config] 35 added, 0 changed, 0 removed`, all 35 sources read and written — closes DV043-F1's Sphinx half |
| `cargo llvm-cov -p prin-dynamics` | exit 0; 309 lib + 59 integration parity tests pass instrumented; table in §9.3 |

The 59 integration tests are worth naming, because they are independent
evidence on precisely the path this fix touches and they were not written for
it: `parity_models` covers `parity_kuramoto_sparse_knn_matches_prinet`,
`parity_hopf_sparse_knn_matches_prinet` and
`parity_stuart_landau_sparse_knn_matches_prinet` — the three sparse k-NN models
whose `StateDerivatives::new` clamp now makes the integrator skip its pass —
and `parity_integrators` covers 23 Euler/RK4/RK45/Exponential/MultiRate cases
against PRINet 3.0 references. All pass, instrumented, after the change. They
also ran in the pre-remediation `cargo test --workspace` at 1603/0/1.

The first Sphinx attempt exited 0 but was **not** a clean build — its log read
"loading pickled environment … 0 added, 2 changed", so it had reused
`_build/doctrees`. `AGENTS.md` forbids reporting a Sphinx result from a reused
output directory, because an incremental build tracks only `.rst` timestamps and
cannot see that an `automodule`-sourced docstring changed underneath an
unmodified page. The directory was deleted and the build re-run; the figures
above are from that clean run.

### 9.3 Coverage, and what is not claimed

`cargo llvm-cov -p prin-dynamics`, line coverage:

| File | Lines | Missed | Cover |
|---|---|---|---|
| `bands.rs` | 774 | 4 | 99.48 % |
| `coupling.rs` | 330 | 1 | 99.70 % |
| `integrate.rs` | 3586 | 1399 | 60.99 % |
| `models.rs` | 3379 | 1844 | 45.43 % |
| `pac.rs` | 287 | 0 | 100.00 % |
| `seed.rs` | 201 | 1 | 99.50 % |
| `state.rs` | 981 | 395 | 59.73 % |
| `temporal.rs` | 471 | 0 | 100.00 % |
| **TOTAL** | **10009** | **3644** | **63.59 %** |

These crate totals are low because `-p prin-dynamics` counts only that crate's
own test binaries and excludes the coverage `prin-sim`, `prin-py` and the Python
suite contribute. **No changed-line percentage is claimed** — diff coverage was
not measured. What is claimed is narrower and individually checkable: every line
this session added or altered is exercised by a named test.

| Changed code | Exercised by |
|---|---|
| `GuardPolicy::derivatives` early return (both arms) | `bounded_step_skips_the_redundant_pass_without_changing_any_value` (guarded *and* unguarded sources), `bounded_step_still_clamps_derivatives_the_model_left_unclamped` |
| `GuardPolicy::derivatives` loop body | the four pre-existing `bounded_guard_*` tests plus the two above |
| `is_guarded()`, manual `PartialEq::eq`, `#[serde(skip)]` | `guarded_flag_is_provenance_and_changes_no_public_contract` |
| `guarded: true` in `new()`, `false` in `unclamped()` | `guarded_flag_records_which_constructor_ran` |
| `guarded: false` at the two finite-difference gradient literals | `models::tests::dynamics_vjp_*`, `integrate::tests::multi_rate_step_vjp_*` |
| `guarded: false` at the two test-only NaN models | `non_negative_guard_propagates_nan_like_torch_clamp`, `strict_check_non_finite_value_error` |
| `sparse_models_report_the_guard_they_actually_applied` | itself; plus `clamp_derivative_is_idempotent_where_the_guard_skip_relies_on_it` |

### 9.4 The five `pytest` failures, and the two gates not re-run

**Not re-run — workspace-wide Rust gates after remediation, blocked by host
linker contention.** Eighteen-plus attempts at `cargo test --workspace -j 1
--no-run` each died on `LNK1104: cannot open file …exe` for a *different*
target (`prin_dynamics` lib test → `_prin_core` lib test → `parity_decomposition`
→ `prin_tensor` lib test → `proptest_sweep` → `parity_mot` →
`parity_subconscious` → `parity_attention` → `parity_activations`), alongside
`os error 32` "did not finalize incremental compilation session directory"
notes. A rotating target across attempts is the documented
antivirus/file-handle condition on this workstation, not a code defect — but it
is a gap, and it is recorded as one rather than filled by the earlier run.
**The evidence for the unchanged crates is the pre-remediation workspace run at
1603/0/1**, which already contained the substantive change; the entire
post-remediation delta is a crate doc comment, one new `#[test]`, and one array
element plus a comment, all inside `prin-dynamics`, and both changed crates are
green in both feature configurations (§9.2).

**Not triggered — `cargo audit`, `pip-audit`, Snyk Open Source.** No dependency,
lockfile or manifest changed (the diff is four Rust source files and seven
documents). Same reasoning the DV-041 row records. Snyk **Code** was run.

**The five `pytest` failures:**

1. `test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression`
   — **this session's own error.** A `--features strict-checks` `cargo check` was
   left running in the background while pytest measured a wall-clock ratio
   against a `< 1.30` threshold; `AGENTS.md` warns against running cargo
   concurrently with pytest on this host. Re-run alone on an idle machine:
   **passed in 7.09 s**.
2. `test_wp001_baseline.py::test_release_workflow_publish_or_skip_continues_under_errexit`
   (3 parameterisations) and `…_fails_on_unrelated_error` — all four die on
   `WSL (N - Relay) ERROR: CreateProcessCommon:798: execvpe(/bin/bash) failed:
   No such file or directory`, so the script under test never executed. This is
   the `AGENTS.md`-documented condition where the Windows WSL `bash.exe` relay
   precedes Git Bash on PATH; the documented remedy is to prepend
   `C:\Program Files\Git\bin` for the test process, which this session's shell
   guard rejects (`%PATH%` rewrites and `powershell -Command` are both refused),
   so it could not be applied here. **Unrelated to this change:** the diff
   touches no Python, no `tools/` and no workflow file. Both groups are green in
   CI — `python.yml`'s `test` job runs this same selection on `ubuntu-latest`
   *and* `windows-latest`, and PR #25's `python` required check was green at
   `5615eda`.

## 10. Fix validation on the reference host

The fixed tree was benchmarked with the same filter, the same criterion settings
and two passes (`--save-baseline fixed1`/`fixed2`), from `C:\dev\PRIN` with its
own target directory.

**The raw times are not comparable across arms, and saying so is the point.**
Every identity in this run — including the `derivatives_parallel` control that
the fix cannot affect — came in 12–33 % *faster* than in the reference and
candidate arms, so the host was in a different state (those arms were measured
while other session work was running). Comparing raw times would have
"confirmed" a recovery the data does not support.

The valid comparison is **within-run**. For an RK4 step,

```text
overhead(N) = step_parallel(N) − 4 × derivatives_parallel(N)
```

isolates the non-derivative work in a step — intermediate/final state
construction and the guard passes — from two identities measured in the same
process, on the same `SparseKuramoto` and the same state, minutes apart. Host
state cancels.

| N | overhead, reference `ce4049f` | overhead, candidate `149cf2d` | overhead, fixed |
|---|---|---|---|
| 256 | 5.00 µs | 10.22 µs | **5.76 µs** |
| 1024 | 28.64 µs | 41.73 µs | **24.37 µs** |
| 4096 | 111.72 µs | 186.25 µs | **111.52 µs** |
| 16384 | 193.70 µs | 194.74 µs | 160.24 µs |

At N=4096 the fixed overhead is **111.52 µs against the pre-regression
111.72 µs — 0.2 % apart**, while the candidate sits at 186.25 µs. The
candidate's excess is 74.5 µs across 4096 oscillators = **18.2 ns per oscillator
per step**, against the 25.3 ns/oscillator the nightly reported for the same
identity: same mechanism, same order of magnitude, different host. As a ratio to
the reference overhead, the candidate is 2.04× at N=256 and 1.46× at N=1024; the
fixed arm is 1.15× and 0.85×.

Two further things this settles:

1. **The fix restores the pre-regression overhead rather than merely improving
   it** — which is what removing provably dead work should produce, and the
   strongest local evidence available given that the bit-identity tests already
   carry the numerical claim.
2. **`step_parallel/16384`'s nightly +28.8 % does not reproduce on H1 even
   before the fix**: the candidate's overhead there is 194.74 µs against the
   reference's 193.70 µs — no measurable excess. §7's treatment of that
   magnitude as a hosted-runner artefact is therefore confirmed by measurement,
   not only by the failure of the `PARALLEL_LEN_THRESHOLD` alternative to
   predict its direction.

**Not claimed:** the N ≥ 65536 rows, and the `sweep_parallel` identities. The
decomposition assumes `step ≈ 4 × derivatives + overhead`, which holds while a
step is compute-bound and breaks down where memory bandwidth and rayon scaling
dominate — at N=1,000,000 it implies a fixed-arm overhead *above* both other
arms, which the bit-identity tests make impossible. Those rows are omitted
rather than explained away. The `sweep_parallel` identities were measured in the
same two passes, but `sweep_parallel` has no derivative-only control in its own
group, so no within-run decomposition is available for it; its recovery rests on
sharing the identical code path (`OscilloSim` + `GuardPolicy::Bounded` RK4 +
sparse model) with `engine_step`, and on the nightly gate that closes DV-043.

**Evidence-of-record caveat, applying to §7 and §10 alike.** All three arms were
built and measured under `.qwen/tmp/arms/{reference,candidate,corrected}`, which
`.gitignore` excludes. The raw criterion output is therefore local scratch that
does not survive cleanup and was never committed; the tables transcribed in §7
and §10 are the evidence of record, and the authoritative confirmation of the
fix is the closure gate in §12 — a green `nightly.yml` `bench-regression` on the
merged SHA, whose own evidence artefact the workflow preserves.

## 11. Scope boundary — what this session deliberately did not do

- **No EXP-001-r1 E-stage ran.** No `RUN-` directory, no `log.md`, no freeze, no
  case integrated, no verdict. The pre-registration is still DRAFT.
- **Blockers 1, 3 and 4 from §1 were not touched.** In particular DV-041's
  closure is *not* recorded here even though its evidence standard is now met
  (merge SHA + `check_ci_green.py` output, per the DV-038/DV-039 precedent and
  campaign plan §12 rule 3). It belongs to the next EXP-001-r1 session, where
  campaign plan §11.7 and amendments #7–#8 also live; recording it on this
  branch would split one disposition across two branches and repeat the
  divergent-row condition DV041-F1 was. Development Workflow Standards §7 scope
  discipline — auditors treat scope creep as D3.
- **The `campaign/exp001-r1-e1` branch was not merged or rebased.** Its
  divergent DV-041 row and its §11.7/#7/#8 are left for that branch's own
  session; §11.8 and amendment #9 are numbered to avoid colliding with them, and
  the resulting gap in main's amendment table is explained in §11.8's own
  numbering note.
- **Not pushed, no PR opened.** Local commits only.
- **The pre-existing RK4 workspace-buffer clone** (`let k1 = self.k1.clone()`,
  three per step) was left alone. It predates PR #24, is already recorded in the
  correction audit as a separate performance-only item deferred to S2, and
  removing it is a different change with a different risk profile.

## 12. Handoff

**Closure gate for DV-043** (campaign plan §11.8): this branch merges to `main`
with required CI green, **and** the next `nightly.yml` `bench-regression` is
green with `engine_step/step_parallel/*` and `sweep_parallel/*` back inside the
+10 % gate. Until both hold, DV-043 stays `OPEN — FIX COMMITTED` and §11.8 is
the dated disposition §10.2 requires.

**Next unit of work is not E3.** It is the EXP-001-r1 **pre-execution amendment
session**: add the tested wgpu leg to `benchmarks/campaign/exp001_r1_driver.py`
using DV-041's `backend_name()` with fallback rejected, resolve the two-build
problem (H4 needs `--features cuda`; `tests/_env.py::wgpu_kernel_executes()`
documents that wgpu compiles out under
`cfg(all(feature = "wgpu", not(feature = "cuda")))`, so the two GPU legs need
different extension builds against §5.1's single recorded clean-build command),
record the follow-up E2 amendment for maintainer approval, and fold in blockers
3 and 4. Only then does the pre-registration freeze and E3 execute — against a
`main` that now also carries this fix, which is why the maintainer chose to land
it before the freeze rather than after: E3 records one baseline SHA instead of
absorbing another mid-experiment change.

**Independent audit.** Per Development Workflow and Audit Standards §7, a hotfix
must be retro-audited in the next S2. This session's changes should be audited
by a reviewer who did not author them, with the bit-identity test, the `n <= 1`
branch coverage and the mutation-robustness trade-off in §8 as the primary
targets.
