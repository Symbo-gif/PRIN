# Session 0117 — WP-030 S1 Handoff Note

**Session:** 0117 — WP-030 S1: Coding — Training hooks and MOT evaluation
**Date:** 2026-08-25
**Status:** S1 delivered; handoff to S2 audit (session 0118)

## Mission recap

"Implement loss EMA/gradient/latency hooks, daemon integration, MOTA/MOTP/
IDF1/identity switches, and synthetic MOT sequences."
Contract (`DOCS/sessions/phase-5/0117-wp030-s1-training-hooks-and-mot-evaluation.md`):
metrics match motmetrics reference; hook overhead/bounds are tested;
deterministic sequence fixtures cover identity edge cases. Non-goals:
temporal training framework or adversarial tooling.

## Entry conditions

| Condition | Status |
|---|---|
| Preceding S4 closed and committed | Yes — session 0116 (WP-029 S4) closed the cycle; `DOCS/reports/029-project-state.md` §6 declares WP-030 with the scope/acceptance criteria quoted above |
| WP-030 scope, acceptance criteria, and non-goals have maintainer approval | PSR-029 §6 recorded approval as *pending, required before WP-030 S1 begins*. **Obtained in-session** — this session was executed at the direct instruction of the repository's maintainer (`MichaelMaillet`, matching the git identity and configured user email), which this project's own precedent (WP-028 S1, WP-029 S1 handoffs) treats as an in-session approval when no separate written sign-off exists yet. Recorded here per that precedent |
| No unresolved D1/D2 finding | Yes — PSR-029 §1: WP-029 S2 verdict `PASS`, zero findings; S3 no-change closure with a clean delta re-audit |

## Scope decisions (record per "do not expand scope silently")

Declared scope (PSR-029 §6, quoted verbatim above): loss EMA/gradient/latency
hooks, daemon integration, MOTA/MOTP/IDF1/identity switches, and synthetic
MOT sequences.

1. **Crate placement: both deliverables live in `prin-daemon`, not a new
   crate.** The Project Plan §6 Phase-5 roadmap row names exactly one crate
   for this phase (`prin-daemon`), and `crates/README.md`'s layering
   (`dynamics → metrics/tensor/kernels → sim/train/daemon → py`) puts
   `prin-train` (where `PhaseTracker` lives) at the *same* tier as
   `prin-daemon`, so `prin-daemon` cannot depend on it anyway. Two new
   modules were added: `hooks` (loss/gradient/latency → `SubconsciousState`)
   and `mot` (CLEAR-MOT/IDF1 accumulator, IoU distances, synthetic
   generators), plus a crate-private `assignment` module (the Hungarian
   solver both `mot::MotAccumulator::update` and its IDF1 global assignment
   need). `prin-dynamics` was added as a new dependency of `prin-daemon`
   (an allowed layering direction) solely so the synthetic sequence
   generators can take a `prin_dynamics::Seed` and stay within the "preserve
   deterministic Seed flow" mandate rather than inventing a second RNG
   authority.

2. **`mot` does not reproduce the reference's `evaluate_tracking(sequence,
   tracker, ...)` loop.** PRINet 3.0's `prinet.nn.mot_evaluation.evaluate_tracking`
   wires a `PhaseTracker`/`DynamicPhaseTracker` instance directly into the
   MOT accumulator. Because `prin-daemon` cannot depend on `prin-train` (see
   above), that wiring is inherently a Python orchestration concern —
   exactly what `python/prin/eval/__init__.py`'s existing docstring already
   says: "Pure Python orchestration layer calling into Rust core kernels for
   hot inner metric computation." What is delivered here is that Rust core:
   given ground-truth/hypothesis identities and a per-frame distance matrix
   (from any source — IoU, appearance, or a real tracker via a future
   `prin-py` binding), compute MOTA/MOTP/IDF1/switches exactly as
   `py-motmetrics` does. Wiring `PhaseTracker` itself into this accumulator
   through a `prin-py` binding and the `python/prin/eval` package is
   out-of-scope discovery #1 below.

3. **The reference's `TRANSFER`/`ASCEND`/`MIGRATE` event subtypes and the
   full per-event `RAW` log are not reproduced.** `motmetrics.mot.MOTAccumulator`
   tracks these for its full metrics surface (`num_transfer`, `num_ascend`,
   `num_migrate`, `mostly_tracked`, `num_fragmentations`, etc.); the four
   target metrics this WP declares (MOTA, MOTP, IDF1, identity switches) only
   ever consume `MATCH`/`SWITCH`/`MISS`/`FP` counts, a running distance sum,
   and — for IDF1 specifically — three frame-presence counters (`ocs`/`hcs`/
   `tps` in the reference's `extract_counts_from_df_map`). `MotAccumulator`
   therefore keeps only those running counters rather than a full pandas-style
   event dataframe; every formula that consumes them was independently
   verified against real `motmetrics` output (see "Parity-evidence
   disposition" below), not against a re-derivation of the reference's
   internal representation.

4. **A pre-existing, unrelated `cargo audit` finding was discovered and
   fixed as routine hygiene, not treated as WP-030 scope.** `cargo audit`
   flagged `RUSTSEC-2026-0267` (published 2026-08-24, the day before this
   session) against `stable-vec` 0.4.2, a transitive dependency of
   `cubecl-opt` (part of the pre-existing Phase-0/3 `cubecl` GPU-kernel
   stack `prin-daemon` does not touch). The advisory describes a real
   panic-safety double-free/use-after-free in `BitVecCore::clear`, reachable
   from safe Rust, fixed upstream in 0.4.3. `cargo update -p stable-vec`
   resolved cleanly to 0.4.3 with no other lockfile churn; `cargo build -p
   prin-kernels -p prin-sim -p prin-train` and the full workspace test suite
   were re-verified green afterward. Recorded here rather than left as a new
   deviation because the fix was a one-line, zero-behavior-change lockfile
   bump with no compatibility risk — the same disposition class as WP022-F3
   (`h2` RUSTSEC-2026-0258).

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-daemon/src/hooks.rs` | **New.** `TrainingHooks` — loss EMA/variance, gradient-norm EMA (from caller-supplied per-parameter L2 norms), step-latency window + p50/p95/throughput, `on_step_start`/`on_step_end`/`on_step_end_with_elapsed`/`on_epoch_end`. |
| `crates/prin-daemon/src/assignment.rs` | **New.** `solve_assignment` — rectangular Hungarian/Kuhn–Munkres solver with `motmetrics`-style NaN/Inf "do-not-pair" handling (`add_expensive_edges` + post-hoc filtering); crate-private. |
| `crates/prin-daemon/src/mot.rs` | **New.** `BBox`/`iou_distance_matrix`, `MotAccumulator`/`MotSummary` (MOTA/MOTP/IDF1/switches/misses/FP), `Detection`, `generate_linear_sequence`/`generate_crowded_sequence` (deterministic, `Seed`-driven). |
| `crates/prin-daemon/src/error.rs` | Added `DaemonError::InvalidParameter`, `DaemonError::MotShapeMismatch`. |
| `crates/prin-daemon/src/lib.rs` | Wired `hooks`/`mot`/`assignment` modules; re-exported `TrainingHooks`, `MotAccumulator`, `MotSummary`, `BBox`, `Detection`, `iou_distance_matrix`, `ObjId`, `HypId`; updated crate-level docs. |
| `crates/prin-daemon/Cargo.toml` | Added `prin-dynamics` dependency (justified inline); registered the `training_hooks` bench. |
| `crates/prin-daemon/tests/hooks_daemon_integration.rs` | **New.** End-to-end `TrainingHooks` → `SubconsciousState` → `SubconsciousDaemon::submit_state` → `InferenceBackend` → `get_control()` proof, plus a strict-checks/non-strict-checks cross-check that hooks compose correctly with `SubconsciousState::to_tensor`'s existing finiteness guard. |
| `crates/prin-daemon/tests/parity_mot.rs` | **New.** Replays `tests/data/mot_reference_cases.json` (10 scenarios) through `MotAccumulator` and asserts its summary matches the committed real-`motmetrics` output. |
| `crates/prin-daemon/tests/data/mot_reference_cases.json` | **New.** Golden fixture generated by `tools/wp030_mot_fixture.py`. |
| `crates/prin-daemon/benches/training_hooks.rs` | **New.** `criterion` per-call cost of `on_step_end_with_elapsed`/`on_epoch_end`. |
| `tools/wp030_mot_fixture.py` | **New.** Generates the MOT parity fixture by replaying scenarios through the real `motmetrics` package. |
| `tools/README.md` | Added entries for `wp029_control_buffer_pilot.py` (previously undocumented) and `wp030_mot_fixture.py`. |
| `pyproject.toml` | No change needed — the `mot` extra (`motmetrics>=1.4.0`) was already declared. |
| `crates/prin-daemon/README.md`, `crates/README.md` | Documented the new modules and the crate-placement/layering rationale. |
| `Cargo.lock` | `stable-vec` 0.4.2 → 0.4.3 (RUSTSEC-2026-0267 fix, see scope decision #4); plus the new `prin-dynamics` edge for `prin-daemon`. |

## Parity-evidence disposition (Development Workflow Standards §3, S1 exit item)

**A directly comparable reference exists for both deliverables, but of two
different kinds.** Training hooks are behavioral parity against PRINet 3.0's
`StateCollector` (the EMA/percentile *formulas*, ported exactly); MOT
evaluation is numerical parity against the real, currently-installed
`py-motmetrics` package (the acceptance criterion's literal wording, "MOT
metrics match motmetrics reference" — not PRINet 3.0's own
`mot_evaluation.py`, which merely *calls* `motmetrics`).

### Training hooks vs. PRINet 3.0 `StateCollector`

| Reference behaviour (`prinet/nn/training_hooks.py`) | PRIN implementation |
|---|---|
| `loss_ema = alpha*loss + (1-alpha)*loss_ema` | `hooks::tests::loss_ema_matches_hand_computed_recurrence` |
| `loss_var = alpha*diff**2 + (1-alpha)*loss_var` (diff from the *updated* ema) | `hooks::tests::loss_variance_uses_deviation_from_updated_ema` |
| `grad_norm = sqrt(sum(p.grad.norm(2)**2 for p in model.parameters()))` | `hooks::tests::grad_norm_ema_is_l2_of_supplied_per_parameter_norms` (per-parameter norms supplied by the caller — see "Design notes") |
| `p50 = sorted[n//2]`, `p95 = sorted[min(int(n*0.95), n-1)]` | `hooks::tests::percentiles_match_hand_computed_values_for_known_latencies` |
| `deque(maxlen=latency_window)` drop-oldest | `hooks::tests::latency_window_never_exceeds_capacity`, `hooks::proptests::latency_count_never_exceeds_window` |
| "Override loss EMA if explicit loss provided" in `on_epoch_end` | `hooks::tests::on_epoch_end_overrides_loss_ema_when_provided` |
| Default `r_per_band=[0.5,0.5,0.5]` when unavailable | **Deliberate deviation**: PRIN requires an explicit `Vec<f64>` (empty when unavailable), which `SubconsciousState::band()` zero-fills — no hidden default, matching Coding Standards' "validate public inputs" over silent defaulting. `on_epoch_end_empty_bands_default_r_global_to_zero` pins this. |
| `StateCollector` owns the daemon and calls `submit_state` itself | **Deliberate deviation**: `TrainingHooks::on_epoch_end` returns the built `SubconsciousState`; the caller submits it. See `hooks.rs` module docs for the rationale (keeps unit tests free of thread spawning) and `hooks_daemon_integration.rs` for the wired-up proof. |

### MOT evaluation vs. real `py-motmetrics` 1.4.0

`tools/wp030_mot_fixture.py` replays 10 scenarios — perfect tracking,
misses, false positives, a forced identity switch, an occlusion
reappearance that must *not* switch, a `max_switch_time` boundary,
rectangular per-frame shapes (5 objects vs. 2 hypotheses and the reverse),
an empty frame, an all-forbidden-pairing frame (`MOTA` goes negative,
`MOTP` is `0/0 = NaN`), and an IoU-bbox-derived distance matrix — through a
real `motmetrics.MOTAccumulator` + `motmetrics.metrics.create().compute(...)`,
and commits the inputs plus `motmetrics`'s own MOTA/MOTP/IDF1/switches/FP/
misses as `crates/prin-daemon/tests/data/mot_reference_cases.json`.
`tests/parity_mot.rs` replays the identical inputs through
`MotAccumulator::update`/`summary` and asserts agreement at `rtol=1e-9,
atol=1e-12` (both sides compute the same closed-form arithmetic over the
same `f64` inputs — a real discrepancy would show up far above float noise).

```
$ .venv/Scripts/python -c "import motmetrics; print(motmetrics.__version__)"
1.4.0
$ cargo test -p prin-daemon --test parity_mot
running 2 tests
test fixture_has_the_expected_scenario_count ... ok
test every_scenario_matches_the_motmetrics_reference_summary ... ok
test result: ok. 2 passed; 0 failed
```

All 10 scenarios pass, including the two hardest to get right without a
faithful reimplementation: the IDF1 global min-cost identity assignment
(`with_identity_switch`: idf1 0.5, `perfect_tracking`: idf1 1.0) and the
`max_switch_time` boundary (`max_switch_time_bounded`: a reassignment 3
frames after the object's last occurrence, with `max_switch_time=1`, is
correctly counted as a plain `MATCH`, not a `SWITCH`).

## Design notes worth an auditor's attention

### The Hungarian solver's `NaN`-handling recipe is transcribed from `motmetrics.lap`, not invented

`motmetrics` cannot hand `scipy.optimize.linear_sum_assignment` a matrix
containing `NaN`/`inf` (SciPy has no "forbidden edge" concept), so
`motmetrics.lap.add_expensive_edges` replaces every non-finite entry with
`2 * r * c + 1` (`r = min(rows, cols)`, `c = max(|finite costs|) + 1`) —
large enough that the optimal solution never chooses one unless forced to —
solves the now-fully-finite matrix, then `_exclude_missing_edges` drops any
returned pair whose *original* cost was non-finite. `assignment::solve_assignment`
reproduces this exact two-step recipe (`assignment.rs` module docs cite both
source functions by name), then solves with a from-scratch Rust
implementation of the classical O(n²m) shortest-augmenting-path Hungarian
algorithm (not a translation of SciPy's solver internals — a different,
independently-verified algorithm reaching the same optimum). Verified two
ways: `assignment::tests` includes adversarial cases (`a_row_with_only_forbidden_entries_is_left_unmatched`,
`forced_infeasible_pair_is_filtered_even_when_matrix_is_square`) where a
naive implementation would wrongly force an infeasible pair, and
`assignment::proptests::solve_assignment_is_always_optimal_and_valid`
checks arbitrary small rectangular matrices against an independent
brute-force optimum (all `k`-permutations of the larger dimension).

**A real bug this caught before it shipped:** the first implementation used
`(row != 0).then_some((row - 1, j - 1))` to build the final pair list.
`bool::then_some` evaluates its argument *eagerly*, even when the receiver
is `false` — so `row - 1` underflowed (`attempt to subtract with overflow`
in debug builds) for every unassigned column, before the guard had a chance
to reject it. `cargo test` caught this immediately (9 failing tests) because
the property test and several `mot::tests` cases exercise genuinely
unassigned rows/columns (more objects than hypotheses, forbidden-only rows).
Fixed by switching to `.then(|| (row - 1, j - 1))`, which defers the
subtraction until after the guard passes. A second, independent bug in the
*test* helper (`brute_force_min_cost` assumed the optimal `rows > cols`
solution always uses rows `0..k`, which is only true when `rows <= cols`)
was caught the same way and fixed by choosing the `k`-permutation from
whichever dimension is larger. Neither bug reached `mot.rs`'s own tests —
both were caught by `assignment.rs`'s own test suite before `mot.rs` ever
called it.

### `motmetrics.distances.iou_matrix` is broken on NumPy 2.0; the fixture computes IoU distances directly instead

`iou_matrix` calls `np.asfarray`, removed in NumPy 2.0 (this environment has
2.5.1 installed), so calling it raises `AttributeError`. This is an
environment/library-version incompatibility in `motmetrics` itself, not a
defect in anything this session delivered or is validating.
`tools/wp030_mot_fixture.py::_box_iou` transcribes the same formula
(`distances.boxiou`/`rect_min_max`, verbatim) in plain Python for the
`iou_based` scenario's handful of boxes, which cannot itself introduce a
numerical discrepancy — the scenario still validates `MotAccumulator`
against real `motmetrics.MOTAccumulator`/`metrics` output; only the input
distance matrix's construction bypasses the one broken reference function.
`prin_daemon::mot::iou_distance_matrix` is unit-tested directly against
hand-computed IoU values (`half_overlap_iou_matches_hand_computed_value`,
1/3 for a 50%-width-overlap unit-square pair) independent of this fixture.

### Non-finite JSON values need a tagging convention, not bare tokens

`json.dumps` happily emits bare `NaN`/`Infinity` tokens (valid Python,
invalid JSON); `serde_json` rejects them on parse. The `all_forbidden_frame`
scenario's `MOTP` is genuinely `0/0` (zero matches), so this is not a
hypothetical: `tools/wp030_mot_fixture.py::_json_safe_float` tags non-finite
metric values as the strings `"NaN"`/`"Infinity"`/`"-Infinity"`, and
`parity_mot.rs::expected_f64` maps them back to the corresponding `f64`
constant before comparison.

## Acceptance-criterion evidence map

### AC1 — "Metrics match motmetrics reference"

See "Parity-evidence disposition" above. `cargo test -p prin-daemon --test
parity_mot`: 2/2 passed (10/10 scenarios agree with real `motmetrics` 1.4.0
at `rtol=1e-9, atol=1e-12`).

### AC2 — "Hook overhead/bounds are tested"

**Bound (pass/fail):** `hooks::tests::step_accumulation_overhead_is_bounded`
— 100,000 `on_step_end_with_elapsed` calls (with a 3-element gradient-norm
slice) complete in well under the 2-second ceiling (a ~1000x-generous bound
chosen to avoid CI flakiness while still catching an accidental O(n) or
allocation-per-call regression). `hooks::proptests::latency_count_never_exceeds_window`
independently proves the latency-window capacity bound holds for arbitrary
call sequences and window sizes 1–32.

**Overhead (pilot evidence, not a scientific claim, per Development Workflow
Standards §3):** `cargo bench -p prin-daemon --bench training_hooks`, this
host:

| Call | Time |
|---|---|
| `on_step_end_with_elapsed`, 0 gradient params | 4.69 ns |
| `on_step_end_with_elapsed`, 8 gradient params | 7.08 ns |
| `on_step_end_with_elapsed`, 64 gradient params | 29.8 ns |
| `on_epoch_end` (100-sample latency window, includes a sort) | 425 ns |

All four sit orders of magnitude below any realistic training-step duration
(microseconds to milliseconds), consistent with "safe to call on every
step."

### AC3 — "Deterministic sequence fixtures cover identity edge cases"

Two complementary fixture kinds, as scoped in decision #2/#3 above:

* **Ground-truth generators** (`generate_linear_sequence`,
  `generate_crowded_sequence`) are `Seed`-driven and deterministic
  (`linear_sequence_is_deterministic_for_a_fixed_seed`,
  `crowded_sequence_is_deterministic_for_a_fixed_seed`: identical `Seed`
  state always produces an identical sequence, checked via `Vec<Vec<Detection>>`
  equality) and cover occlusion (`crowded_sequence_has_no_live_detections_when_occlusion_rate_is_one`)
  and distractor injection (`crowded_sequence_contains_distractors_when_rate_is_one`).
* **Accumulator-level identity-edge-case fixtures**
  (`crates/prin-daemon/tests/data/mot_reference_cases.json`, hand-authored
  and deterministic — no RNG involved, so every scenario is exactly
  reproducible) cover a forced identity switch, an occlusion reappearance
  that must *not* switch, and a `max_switch_time` boundary, all validated
  against real `motmetrics` (AC1 above handles the "match reference"
  half; the scenarios themselves are the "cover identity edge cases" half).
  `mot::tests` additionally hand-verifies each edge case's *mechanism*
  independently of the fixture (e.g. `reappearance_with_the_same_hypothesis_after_a_miss_is_not_a_switch`,
  `max_switch_time_suppresses_switches_beyond_the_window`).

## Gate evidence (2026-08-25, this host)

```powershell
cargo fmt --all -- --check                                                    # clean
cargo clippy --workspace --all-targets -- -D warnings                         # clean (exit 0)
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings # clean (exit 0)
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps                     # 0 warnings (exit 0)
cargo test --workspace -- --test-threads=1                                    # all crates green, 0 failed
cargo test -p prin-daemon --features strict-checks                            # all green
cargo bench -p prin-daemon --bench training_hooks                             # pilot evidence, see AC2
cargo audit                                                                    # exit 0; 2 allowed warnings (amendments #9/#27 — unchanged; RUSTSEC-2026-0267 fixed this session, see scope decision #4)
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/             # clean
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/    # clean (74 files already formatted, incl. the new tools/wp030_mot_fixture.py)
.venv\Scripts\mypy python/prin --strict                                       # 28 files, 0 issues (unchanged — this WP touches no python/prin/ source)
.venv\Scripts\mypy tools/wp030_mot_fixture.py --strict                        # 0 issues
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin             # 100.0% (262/262, unchanged)
.venv\Scripts\python -m interrogate -c pyproject.toml tools/wp030_mot_fixture.py  # 100.0% (9/9)
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml               # 0 issues (unchanged)
.venv\Scripts\python -m bandit tools/wp030_mot_fixture.py -c pyproject.toml   # 0 issues (228 lines)
.venv\Scripts\python -m pip_audit .                                           # 0 vulnerabilities (incl. the new motmetrics/pandas/xmltodict/tzdata `mot`-extra installs)
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp  # 547 passed, 8 deselected (unchanged)
.venv\Scripts\python tools/wp001_baseline.py check                            # WP-001 baseline validation passed
cargo llvm-cov -p prin-daemon --features strict-checks                        # see Coverage below
```

### Coverage on new/changed code (`cargo llvm-cov -p prin-daemon --features strict-checks`)

| File | Regions | Functions | Lines |
|---|---|---|---|
| `crates/prin-daemon/src/hooks.rs` | **99.75%** | **100.00%** | **99.61%** |
| `crates/prin-daemon/src/mot.rs` | **99.72%** | **100.00%** | **100.00%** |
| `crates/prin-daemon/src/assignment.rs` | **98.89%** | **100.00%** | **98.18%** |

All three clear the ≥95% bar comfortably. Every remaining uncovered region
in `assignment.rs` is a `rows == 0`/`cols == 0` early return inside the
*test-only* `brute_force_min_cost` helper (never exercised because no test
compares `solve_assignment` against a brute-force check on a genuinely
empty matrix — `empty_matrix_returns_no_pairs` checks `solve_assignment`
directly, without the brute-force comparison) — not an untested product
code path. `hooks.rs`'s one remaining uncovered line is the `assert!`
failure-message format string in `step_accumulation_overhead_is_bounded`,
which by construction only executes if that test fails (the same "0%
function coverage is the exact point of the test" pattern documented in the
WP-029 handoff). `backend.rs`/`daemon.rs`/`model.rs`/`onnx.rs`/`state.rs`
are unchanged from PSR-029 (99.50%/97.16%/96.52%/95.16%/99.29% regions
respectively).

### Snyk (Coding Standards §6, mandatory control)

Not run this session — no interactive Snyk CLI/IDE session available in
this non-interactive execution environment. Per Coding Standards §6.1 item
5 and the standing condition on record since WP-001 (R23, maintainer
decision 2026-08-18: "Snyk-CLI-only accepted as permanent; CI is the
authoritative gate"), this is reported as **blocked**, not claimed as
passed; CI's Snyk job remains the authoritative gate for this change.
`cargo audit`/`pip-audit` (ecosystem-native, independent of Snyk per Coding
Standards §6.2) are both clean, as recorded above. Snyk Open Source is
additionally relevant to this change's new Python dependencies
(`motmetrics`, `pandas`, `xmltodict`, `tzdata` — all dev/test-only, gated
behind the `mot` extra, never imported by `python/prin/` runtime code) —
`pip_audit .` covers the installed environment and is clean.

## Out-of-scope discoveries (logged, not acted on)

1. **Wiring `PhaseTracker`/`DynamicPhaseTracker` into `MotAccumulator`
   through a `prin-py` binding, and building out `python/prin/eval`'s
   orchestration layer.** This session delivers the Rust core
   (`MotAccumulator`, distances, synthetic generators) that
   `python/prin/eval/__init__.py`'s existing docstring already commits to;
   actually calling a real tracker frame-by-frame and feeding its output
   into this accumulator (PRINet 3.0's `evaluate_tracking`) needs a
   `prin-py` binding exposing `MotAccumulator`/`iou_distance_matrix` to
   Python plus the `python/prin/eval` package itself, neither of which this
   WP's declaration named. Concrete recommendation for whichever session
   picks this up: bind `MotAccumulator::update`/`summary` and
   `iou_distance_matrix` via PyO3 (following the `bindings/phase_tracker.rs`
   pattern already established for `PhaseTracker` itself), then have
   `python/prin/eval` do exactly what PRINet 3.0's `evaluate_tracking` does
   — run the tracker frame-by-frame, build the distance matrix, call the
   bound accumulator.
2. **`benchmarks/` has no MOT-evaluation or training-hooks category
   package.** Same disposition as the WP-029 handoff's out-of-scope
   discovery #2: `benchrunner` itself is Phase 6 scope; this session's
   `benches/training_hooks.rs` is a `criterion` bench in the same style as
   `benches/control_buffer.rs`, not a `benchmarks/` category package.
3. **`RUSTSEC-2026-0267` (`stable-vec`)** — discovered and fixed this
   session (scope decision #4); recorded here only so the S2 audit does not
   need to independently re-derive that it was in scope to fix rather than
   defer.

## Handoff to S2 (session 0118)

Suggested audit focus, in descending order of risk:

1. **The Hungarian solver's correctness**, independent of this note's
   claims — re-derive `hungarian`'s potentials/augmenting-path logic from
   `assignment.rs`'s source, and independently verify the `NaN`-padding
   recipe (`add_expensive_edges`) against `motmetrics.lap`'s actual source
   (installed at `.venv/Lib/site-packages/motmetrics/lap.py`) rather than
   trusting this note's transcription.
2. **The IDF1 global-assignment matrix construction**
   (`MotAccumulator::compute_idf1`) — this is the least obviously-correct
   piece of the whole delivery (a `(no+nh) x (no+nh)` cost matrix with a
   specific forbidden-region/self-diagonal structure); confirm it against
   `motmetrics.metrics.id_global_assignment`'s actual source, not just the
   passing parity test (a bug that happened to cancel out across all 10
   fixture scenarios cannot be ruled out by the fixture alone — consider
   whether an 11th adversarial scenario is warranted before closing this
   item).
3. **The crate-placement and scope-boundary decisions** (both `mot` living
   in `prin-daemon` rather than a new crate, and `evaluate_tracking`-style
   tracker wiring being ruled out-of-scope) — judge whether the layering
   argument in "Scope decisions" #1/#2 is sound, or whether a dedicated
   `prin-mot` crate would have been the better call.
4. **The `stable-vec` bump** (scope decision #4) — confirm it was
   proportionate to fix inline rather than deferred as a new deviation, and
   that `cargo audit`/full-workspace-test re-verification after the bump was
   adequate (not just "it compiled").
5. **The training-hooks API's departure from the reference's daemon-owning
   design** (`on_epoch_end` returns a state instead of submitting it) —
   confirm this is a defensible Rust-idiom correction rather than a
   scope-narrowing that quietly drops "daemon integration" from the
   delivery (the integration itself is proven by
   `hooks_daemon_integration.rs`, not by `TrainingHooks` owning the daemon).
