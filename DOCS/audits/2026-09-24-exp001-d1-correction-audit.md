# EXP-001 D1 correction audit

**Scope:** the EXP-001 D1 correction cycle (campaign plan §10.4): H1 `REFUTED`
(485/504), H2a `REFUTED` (897/1,000), and finding `EXP001-E5-F1`.\
**Opened by:** session `0158` (EXP-001 E5), 2026-09-23 UTC.\
**Blocked:** session `0159` (EXP-002 E1), every experiment downstream of EXP-001,
and `0194`.\
**Branch / PR:** `hotfix/exp001-d1-parity-correction` from `origin/main` @
`ce4049f`; draft **PR #24**.\
**Stage status:** S1 **complete** (this record); S2 audit, S3 remediation and S4
documentation are **pending**.

This is the correction work package's audit of record. S1 records its
implementation here: approvals, root cause, commits, the red → green transition,
commands, and handoff. S2 appends the audit proper (A1–A10, findings, verdict)
below this record, S3 appends its closure table, and S4 appends the closure.
Nothing in this S1 record is an audit verdict, a merge authorization, an
`EXP-001-r1` authorization, or a release of session `0159`.

---

## S1 — implementation record (2026-09-24 UTC)

**Session brief:** [`2026-09-23-exp001-d1-s1-correction-implementation.md`](../sessions/contingencies/2026-09-23-exp001-d1-s1-correction-implementation.md).\
**AI pair:** Claude Opus 5.5. The maintainer's decisions are recorded below.

### S1.1 Approvals

The investigation was read-only up to this point. MichaelMaillet then approved
the brief's scope as written, on 2026-09-24 UTC via in-session
`AskUserQuestion` selections, with three decisions (recorded verbatim in the
brief's "Approved scope and decisions"):

1. **Guard divergence: faithful default.** PRIN's Euler/RK4 default to PRINet
   3.0's `OscillatorModel` guard, and the PRINet `[1e-6, 10]` paths keep that
   bound explicitly. A Project Plan §8.3 amendment makes §5.6 path-specific.
   This is recorded as amendment #47.
2. **DV-007 cases in the full-corpus gate: explained divergence** (the
   amendment #25 pattern). No tolerance is widened and nothing is skipped.
3. **Push and draft PR authorized** so that the `parity` workflow records the
   transition. No merge is implied.

### S1.2 Root cause

Every breach was attributed by controlled substitution. PRINet 3.0 was re-run
with exactly one behaviour changed at a time, and PRIN was compared with each
variant at both the pre-fix and post-fix builds:

- **native** — the archived reference, unmodified;
- **f64** — the three DV-007 `complex64` paths evaluated in float64;
- **f64_bounded** — f64 with PRIN's pre-correction guard swapped into
  `OscillatorModel._step_euler`/`_step_rk4`;
- **f64_ulp** — f64 from initial phases moved by one ulp.

Evidence: `EVIDENCE/exp001-d1-s1/`.

| Mechanism | Side | H1 (19) | H2a (103) | H2a ≥ `1e-3` (33, E3 magnitudes) |
|---|---|---|---|---|
| **DV-007:** PRINet 3.0 evaluates the Stuart–Landau derivative (`oscillator_models.py` 575-593) and the Kuramoto/Hopf mean-field order parameter (362-364, 732-734) in `complex64` inside a float64 model; PRIN is pure float64 | reference | 19 | 38 alone | 0 alone |
| **Guard:** PRIN's `EulerIntegrator`/`RK4Integrator` applied `[1e-6, 10]` amplitude and `±1e4` derivative bounds, taken from PRINet 3.0's fused-kernel/OscilloSim paths. `OscillatorModel._step_euler`/`_step_rk4` instead clamps amplitude with `torch.clamp(min=0.0)` (no ceiling) and clamps derivatives only inside its sparse k-NN models | **PRIN** | 0 | 33 alone | 9 alone |
| DV-007 + guard | both | — | 10 | 2 |
| DV-007 + guard + **ill-conditioned** (the reference's own float64 map breaches under a one-ulp phase change) | reference is ill-posed | — | 19 | 19 |
| guard + ill-conditioned | — | — | 3 | 3 |
| **unexplained** | — | **0** | **0** | **0** |

Supporting measurements:

- **The pre-fix build reproduces E3 exactly:** 19/504 and 103/1,000, with the
  same case sets. It equals the f64_bounded reference to `3.3e-12` on every
  well-conditioned fuzz case, and to `2.0e-15` on the corpus, so the two
  mechanisms plus ill-conditioning account for everything.
- **The post-fix build** matches the f64 reference (native guard) on all 978
  well-conditioned fuzz cases. 973 agree to `≤ 4e-14`; five sit in the
  amplitude-collapse or amplitude-growth regime (cases 148, 185, 191, 223, 374)
  and agree to `1.9e-9`–`4.9e-7`, inside the registered tolerance.
- **The reference regenerates the stored corpus bit-exactly** on this host
  (504/504), so the corpus is PRINet 3.0's output.
- **Campaign plan §10.4 item 3 (the DV-007 side is the reference):**
  `dv007_exactness_audit.py` evaluates PRINet 3.0's own discrete map in 50-digit
  mpmath. That covers its equations, Euler/RK4 update, `max(·, 0)` and
  `max(r, 1e-8)` guards, phase wrap modulo the float64 `2π`, and metrics. It was
  run for all 57 DV-007-only breaches (19 H1, 38 H2a). PRIN is within
  `4.7e-14` of the exact map with no breach; the reference is outside the
  registered tolerance (up to `6.2e-6`). **Reference is the erroneous side:
  57/57.**
- **SymPy lemmas.** L1: polar extraction `Re/Im(ż·e^{-iφ}) = ṙ, rφ̇`. L2:
  mean-field ≡ pairwise sum. L3: Stuart–Landau `Σ_{j≠i} (K/N)(z_j − z_i) =
  K(Z − z_i)`. Together these show PRIN and PRINet 3.0 evaluate one
  mathematical map. L4: `|∇ atan2| = 1/r`, and the phase velocity's
  sensitivity at the floor is `1/ε`, which explains the ill-conditioning at
  PRINet's `ε = 1e-8`. All hold. Z3 does not apply: the claims are
  transcendental, and the one piecewise-linear step is closed-form.

**Why it was not caught earlier.**

1. EXP001-E5-F1: no gate ran PRIN against the full corpus.
2. The WP-008 integrator parity fixtures never drive an amplitude outside
   `[1e-6, 10]`.
3. Project Plan §5.6 listed "amplitude clamp `[1e-6, 10]`; derivative clamp
   `±1e4`" without naming the paths. That list was inherited from the rebuild
   planning document, which describes PRINet 3.0's fused and OscilloSim paths.
   PRINet 3.0's own API reference documents `≥ 0` for the model path.

### S1.3 Commits

| Commit | Purpose |
|---|---|
| `dc468c1` | docs: approved scope and maintainer decisions recorded in the S1 brief |
| `bd737e1` | **test (failing first):** full-corpus PRIN-vs-corpus gate, H2a registered-stream gate, the f64 instrument and its validation tests, six `prin-dynamics` guard-semantics unit tests |
| `64b9696` | test: the instrument checks compare against a same-host regeneration. The first Linux CI run showed stored-corpus bit-identity is Windows-only (amendments #16/#17) |
| `34e8811` | **fix:** `GuardPolicy` (default `NonNegative`), `StateDerivatives::unclamped` on the non-sparse paths, OscilloSim ports pinned `Bounded`, Python `guard=` keyword and `.guard`, stub, and binding tests |
| `45cca61` | **test:** DV-007 explained-divergence clause in both gates, plus the §10.4 item 3 evidence |
| `e8841c1` | test: pins the unclamped `N ≤ 1` derivative shortcut (coverage) |
| (docs commit) | Parity Report update and register entry, `test_corpus_exhaustive_differential_parity` docstring, Plan amendment #47, CHANGELOG, Migration Guide, Sphinx pages, this record, indexes |

### S1.4 Red → green transition (S1 acceptance)

| Tree | Corpus gate (504) | H2a gate (978 well-conditioned + 22 ill-conditioned characterizations) | Rust `prin-dynamics` guard tests | CI (`parity` job, ubuntu-latest) |
|---|---|---|---|---|
| `bd737e1` (pre-fix) | **19 fail** — exactly H1's set (Windows and Linux) | **81 fail** on Windows, exactly H2a − ill-conditioned; **79** on Linux (cases 201 and 366 are DV-007 cases inside tolerance on Linux); 22 characterizations pass | **6 fail**, 1 regression guard passes | run `36078335512`: **red**, 108 failed = 19 + 79 + 10 instrument-test failures corrected by `64b9696`. Rust run `36078335479` red on the new tests; Python run `36078335506` green |
| `34e8811` (guard fix) | **19 fail** (all DV-007) | **48 fail** on Windows / **46** on Linux, all on DV-007 paths, each matching the f64 reference | pass | run `36080877871`: **red**, 65 failed = 19 + 46. Rust run `36080877909` green on all legs incl. strict; Python run `36080878068` green |
| `45cca61` (DV-007 adjudication) | **pass** | **pass** | pass | run `36083119713`: **green**, 2,120 passed, 2 skipped, conclusion `success` (head `45cca61`). The remaining workflows are recorded in the S1.8 CI addendum |

The corpus gate's red → green is attributable, by construction, to the
approved DV-007 adjudication. No PRIN code change moves a corpus case,
because the guard never engages in the corpus. The H2a gate's 81 → 48
transition is the PRIN fix; its 48 → 0 transition is the adjudication.

### S1.5 Local verification (Windows host, project venv)

```text
cargo fmt --all -- --check                                  clean
cargo clippy --workspace --all-targets -- -D warnings       clean
cargo clippy --workspace --all-targets --features strict-checks -- -D warnings   clean
cargo test --workspace                                      1594 passed, 0 failed, 1 ignored (48 suites)
CARGO_TARGET_DIR=target/strict cargo test --workspace --features strict-checks   1599 passed, 0 failed, 1 ignored
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps  clean
cargo llvm-cov -p prin-dynamics --lib                       changed non-test lines 69/71 = 97.2%, then e8841c1 covers the 2 remaining
ruff check / ruff format --check python/ tests/ benchmarks/ tools/ parity/ EVIDENCE/exp001-d1-s1/   clean
mypy python/prin --strict                                   no issues (62 files)
mypy --strict (parity/ new files, EVIDENCE scripts)          no issues
interrogate -c pyproject.toml python/prin                   97.6% (>= 95%)
bandit -r python/prin -c pyproject.toml                     no issues
pytest tests/ -m "not slow and not gpu"                     3264 passed, 178 skipped, 48 deselected, 0 failed
pytest parity/ -m parity                                    2121 passed, 1 skipped (post-45cca61)
sphinx -W --keep-going -b html DOCS/sphinx                  clean
tools/check_dv_register_gates.py, check_global_session_registration.py, check_skipif_probes.py   pass
pytest tests/test_sphinx_docs.py tests/test_wp001_baseline.py   93 passed
snyk code test --severity-threshold=low                     0 findings in any changed file (repository total 34 LOW, all in untouched files, unchanged from before the change)
```

- No dependency manifest changed, so Snyk Open Source, `pip-audit` and
  `cargo audit` were not triggered by this change. The evidence scripts use
  `mpmath`/`sympy`, which are already in the environment through `torch`, and
  add no declared dependency.
- The first strict-checks workspace run hit one failure in `prin-train`
  (`bands::tests::gradient_matches_central_finite_difference`, `unwrap()` on a
  `None` gradient). It passed 5/5 in isolation and in a full strict run from a
  separate target directory. That code path uses only `prin_dynamics::Seed`,
  which this change does not touch; see observation 6.
- Two further full strict runs failed only at link time (`LNK1104`, file
  locks) and executed no test. They are not counted.

### S1.6 A test that encoded the defect

`integrate::tests::euler_amplitude_clamped` asserted the `[1e-6, …]` floor for
the default Euler guard, which is the divergence itself. It now asserts
exactly `0.0` for the default and `AMPLITUDE_MIN` for `GuardPolicy::Bounded`
(`34e8811`). No other pre-existing test changed.

### S1.7 Observations outside the approved scope (candidates, not done)

1. **RK45 / Exponential / Jacobian helper** keep their `[1e-6, 10]` amplitude
   clamp. PRINet 3.0's `ExponentialIntegrator` (`integrators.py:352`) and
   `BatchedRK45Solver` (`utils/cuda_kernels.py:216`) clamp at `min=0.0`, so
   this is the same defect class. EXP-001 does not exercise these paths.
2. **`_torch_compat` `step()`** rebuilds the state through
   `OscillatorState::new` on every call, which re-guards amplitude to
   `[1e-6, 10]`. `integrate()` is faithful; single-stepping is not. This is
   documented in the Migration Guide.
3. **`N = 1` mean-field Kuramoto/Hopf:** PRIN's `N ≤ 1` shortcut treats every
   mode as uncoupled. PRINet 3.0's mean-field path at `N = 1` includes the
   self-term, e.g. Kuramoto `dr/dt = (K − λ) r`. Not exercised (`N ≥ 8`).
4. The `integrate.rs` module doc still says PRINet 3.0 has no adaptive RK45,
   but it ships `BatchedRK45Solver`. This is a pre-existing inaccuracy and was
   left unchanged.
5. `prin-kernels`' mean-field RK4 kernel clamps amplitude to `[1e-6, 10]`,
   while PRINet 3.0's API reference documents `≥ 0` for its Triton mean-field
   RK4 kernel (`API_Reference_Coupling_Topologies.md:153`). Not verified
   against the Triton source; flagged for review.
6. **Possible DV-019-class recurrence** (S1.5), despite `autodiff_test_guard`.
   DV-019's closure note directs a new DV item, not a reopening. This is for
   S2/S4 to register.
7. **Platform dependence of the unmodified reference:** cases 201 and 366
   breach on Windows but not Linux before the fix (DV-007 paths; amendments
   #16/#17). The adjudication is platform-neutral because it compares against
   the float64 reference.
8. **For `EXP-001-r1` (its own E1/E2, not S1):**
   (a) how H1/H2a register the DV-007 cases — the explained-divergence rule,
   a float64-regenerated corpus, or another registered mechanism;
   (b) the 22 ill-conditioned fuzz cases, where pointwise comparison is
   ill-posed for any faithful implementation;
   (c) whether campaign experiments that use the default Euler/RK4 (e.g. the
   EXP-005 chimera benchmarks) need a regression note. Results change only
   when an amplitude leaves `[1e-6, 10]` or a non-sparse derivative exceeds
   `±1e4`.
9. The fuzz gate imports the frozen EXP-001 driver and reads the committed E3
   fuzz artefact, so it couples a permanent gate to an immutable campaign
   record. This was deliberate: it guarantees the gate tests exactly H2a's
   cases. It is noted for S2.

### S1.8 Handoff to S2

S2 audits the range `dc468c1..HEAD` on `hotfix/exp001-d1-parity-correction`
against the brief and the standards, and records A1–A10 here. Points worth
independent re-derivation rather than acceptance:

- the attribution table, re-derived from `EVIDENCE/exp001-d1-s1/` or by
  re-running both generators;
- the exactness audit's model code against `oscillator_models.py`;
- the instrument's claim to change only the DV-007 paths (`test_prinet_f64.py`);
- the `GuardPolicy::Bounded` claim of bit-identical pre-correction behaviour;
- the choice of which `prin-sim` call sites to pin (`sweep.rs`, engine
  tests/doc, GPU test, benches) and which to leave on the default
  (`compat.rs` band sweep, since it ports `DeltaThetaGammaNetwork.integrate`);
- the ill-conditioning criterion (one-ulp phase perturbation on the float64
  reference) and its 22-case list;
- the observations in S1.7.

**CI record.** The final S1 CI results are recorded here by an addendum after
the runs settle. CI is the authoritative merge gate.

**Not authorized by S1:** merging PR #24, `EXP-001-r1`, or releasing session
`0159`. Session `0159` stays `BLOCKED`.
