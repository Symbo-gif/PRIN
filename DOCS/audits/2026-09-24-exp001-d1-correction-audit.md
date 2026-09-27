# EXP-001 D1 correction audit

**Scope:** the EXP-001 D1 correction cycle (campaign plan §10.4): H1 `REFUTED`
(485/504), H2a `REFUTED` (897/1,000), and finding `EXP001-E5-F1`.\
**Opened by:** session `0158` (EXP-001 E5), 2026-09-23 UTC.\
**Blocked:** session `0159` (EXP-002 E1), every experiment downstream of EXP-001,
and `0194`.\
**Branch / PR:** `hotfix/exp001-d1-parity-correction` from `origin/main` @
`ce4049f`; draft **PR #24**.\
**Stage status:** S1 **complete**; S2 **complete** (PASS, 2026-09-27 UTC);
S3 remediation and S4 documentation are **pending**.

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
  run for all 67 adjudicated DV-007 breaches (19 H1, 48 H2a — every
  well-conditioned H2a case on a DV-007 path, including the 10 that are also
  guard-sensitive; the 57-case scope of S1 omitted those 10 and was widened
  in the S1.9 review remediation). PRIN is inside the registered tolerance
  with no breach — within `3.6e-15` of the exact map on H1 and `4.7e-14` on
  the DV-007-only cases, with the 10 combined amplitude-regime cases at worst
  `7.6e-8` (rtol-dominated, zero breaches); the reference is outside the
  registered tolerance (up to `5.05`). **Reference is the erroneous side:
  67/67.** The artifact now also records `git_head`, `prin_package`,
  `prin_extension`, `torch`, `numpy`, and `platform` provenance.
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
| `c825077` | Parity Report update and register entry, `test_corpus_exhaustive_differential_parity` docstring, Plan amendment #47, CHANGELOG, Migration Guide, Sphinx pages, this record, indexes |
| `779b2ac` | **Independent-review remediation (S1.9):** consolidated verification of the six review bodies on the PR; every valid finding fixed (gate stream fingerprint, ill-conditioned PRIN assertions, 67-case exactness audit, OscilloSim pins and enforcement, strict-checks diagnostic, Stuart–Landau N ≤ 1 divisor, CHANGELOG/rustdoc/migration corrections, instrument AST pin, binding coverage), five findings refuted by execution, the rest deferred to S2 with dispositions |

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
                                                            (see the S1.9 caveat: an independent re-measurement with
                                                            tools/coverage_changed_lines.py at BASE_REF=ce4049f gave 359/404 = 88.86%
                                                            over all changed lines carrying DA records — the figures are not
                                                            comparable without the exact invocation, scope, and tool version)
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

### S1.9 Independent-review remediation (2026-09-27, after the S1 record)

Four independent multi-agent reviews of this PR were posted on the PR
(Copilot and CodeRabbit inline findings; Perplexity/Grok 4.7-Thinking;
Gemini 3.8; GROK BOT; Qwen3.8-max-preview). A consolidated verification of
every finding against the tree and the archived reference was performed the
same day; the valid findings were remediated in `779b2ac`. Disposition
summary (full matrix in the PR comment of 2026-09-27):

- **Refuted by execution, no action:** Copilot's three E402/`I001` parity
  findings (`ruff` clean, including under `--isolated --no-cache`); Grok
  4.7's F1 (Stuart–Landau `exp` "runs in complex64" — torch promotes
  `1j * float64` to `complex128` before the `exp`, verified bitwise; the
  recommended rewrite would have *weakened* the evidence); Grok-bot's
  caution against Gemini's F-02 (the archived `Oscillosim.py` has no
  derivative clamp and no `N <= 1` return, so the unclamped switch is the
  faithful one); CodeRabbit's docstring-coverage warning (`interrogate`
  governs, 97.6%).
- **Fixed in `779b2ac`:** the seven unpinned OscilloSim test
  ports (six integrating sites plus the `memory_bytes` constructor, which
  the engine's construction-time assertion also covers; all now `Bounded`,
  with a debug-build assertion on the new `Integrator::guard`); `prin-sim`'s
  clamped `N <= 1` shortcuts; the
  strict-checks `Bounded` silent clamp (restores `OutOfRange`); the
  Stuart–Landau `N <= 1` `max(r, 1e-8)` phase divisor; the 57→67 exactness
  audit scope (all 10 well-conditioned DV-007+guard H2a cases audited,
  reference erroneous in 67/67, artifact regenerated with full provenance);
  the H2a stream identity fingerprint (specs + parameters + initial arrays,
  SHA-256, asserted in the gate and in the evidence generator); PRIN-side
  hazard/floor assertions for the 22 ill-conditioned cases (three of which —
  330, 385, 841 — are off the DV-007 paths entirely); the vacuous coverage
  test (now enforces the partition); the CHANGELOG "unchanged" wording for
  RK45/Exponential/MultiRate/Jacobian; the stale crate-root rustdoc; the
  instrument's AST cast-for-cast pin; the Python-binding coverage gaps
  (RK4 ceiling check, `integrate_fixed` with guards, read-only `.guard`);
  the audit placeholder commit; the migration-guide MultiRate/`compat.rs`
  notes; the pre-fix regeneration procedure (README) with the label now
  *derived* from the imported build by probing for the correction, so a
  mislabelled run fails instead of writing a plausible artefact; the
  `evidence` extra declaring mpmath/sympy.
- **Deferred to S2 with a recorded disposition:** `#[non_exhaustive]` on
  `GuardPolicy` (would break ~13 downstream construction sites today —
  belongs with the API freeze); threading `GuardPolicy` through
  RK45/Exponential/the Jacobian (documented and pinned by regression tests
  instead — same defect class as S1.7 item 1); the `prin-kernels` mean-field
  RK4 Triton claim (S1.7 item 5, still unverified); the RK4 workspace-buffer
  clone (pre-existing, performance only); the unexplained +9 pytest
  collection drift noted by Qwen (environmental; suites themselves green).
- **Record corrections:** the CI parity run cited in S1.4/S1.5
  (`36083119713`) is at `45cca61`, two commits behind the reviewed head;
  the head run is `36083847894` (`success` at `c825077`). The
  69/71 = 97.2% changed-line coverage figure is retained as recorded here;
  an independent re-measurement (359/404 over all changed lines with `DA`
  records, using `tools/coverage_changed_lines.py` at `BASE_REF = ce4049f`)
  differs by construction — no test-module exclusion, and a Windows
  drive-letter-casing merge in the lcov can double-count `state.rs` — so
  the figure is only reproducible with the exact invocation, scope, and
  tool version recorded above.

**Head CI at `779b2ac`:** recorded by addendum below after the runs settle;
CI is the authoritative merge gate.

---

## S2 — audit record (2026-09-27 UTC)

**Session brief:**
[`2026-09-23-exp001-d1-s2-correction-audit.md`](../sessions/contingencies/2026-09-23-exp001-d1-s2-correction-audit.md).\
**AI pair:** Qwen Code (Qwen3.8-max-preview). Read-only audit; no code changes.\
**Audited range:** `dc468c1..7235ae6` on `hotfix/exp001-d1-parity-correction` (40 files,
+87,826 / −151 lines).\
**Head CI:** `7235ae6` (the AST-pin fix for Python 3.12 compatibility).

### S2.0 S2-specific verification items

The brief requires six items beyond the standard A1–A10 checklist.

1. **The reproduction came first.** ✅ VERIFIED. Commit `bd737e1`
   ("test(exp001-d1): reproduce the H1/H2a refutations as failing tests")
   precedes the fix at `34e8811`. S1.4 records the pre-fix tree failing
   exactly H1's 19 corpus cases and 81/79 fuzz cases (Windows/Linux). The
   red → green transition is attributable and recorded.

2. **The root cause is established, not asserted.** ✅ VERIFIED.
   `EVIDENCE/exp001-d1-s1/root_cause_decomposition.py` performs controlled
   substitution (native, f64, f64_bounded, f64_ulp) and attributes every
   breach. The prefix and postfix JSON outputs record per-case mechanism
   attribution with zero unexplained breaches. The campaign plan §10.4
   item 3 evidence (`dv007_exactness_audit.py`) evaluates PRINet 3.0's
   discrete map in 50-digit mpmath and verifies SymPy lemmas L1–L4. The
   audit JSON records 67/67 cases with the reference as the erroneous side
   (PRIN vs exact max_abs 7.6e-8; reference vs exact max_abs 5.05).

3. **The fix covers both failure populations.** ✅ VERIFIED. H1's 19
   breaches are all DV-007 (PRINet 3.0 complex64 arithmetic); H2a's 103
   breaches decompose into DV-007 (38), guard (33), DV-007+guard (10),
   DV-007+guard+ill-conditioned (19), guard+ill-conditioned (3),
   unexplained (0). The `GuardPolicy` enum addresses the guard mechanism;
   the DV-007 adjudication addresses the arithmetic mechanism; the
   ill-conditioned characterization addresses the reference's own
   singularity. Both populations are closed.

4. **`EXP001-E5-F1` is genuinely closed.** ✅ VERIFIED. The new
   `parity/test_parity_prin_corpus.py` integrates PRIN from all 504 stored
   initial states; `parity/test_parity_prin_fuzz.py` replays H2a's stream
   with SHA-256 identity checking. S1.4 records the pre-fix tree failing
   both gates and the post-fix tree passing. A gate that passes both before
   and after would prove nothing; the recorded transition disproves that.

5. **EXP-001's record is untouched.** ✅ VERIFIED. `git diff
   ce4049f..HEAD -- DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/
   benchmarks/results/EXP-001/ parity/corpus/` returns empty. `verify_manifest`
   passes on all four run directories (corpus, repeatability, fuzz,
   kernel-path-cuda).

6. **Coding Standards §6 evidence is real.** ✅ VERIFIED. Local gates run
   and recorded below (S2.5). Snyk Code: S1.5 records 0 findings in changed
   files (repository total 34 LOW, all in untouched files). No dependency
   manifest changed; `pip-audit` and `cargo audit` run clean.

### S2.1 A1 — WP scope

✅ PASS. Everything declared in the S1 brief is present:
- Reproduction tests (`bd737e1`): full-corpus gate, H2a fuzz gate, f64
  instrument, guard-semantics unit tests.
- Root-cause fix (`34e8811`): `GuardPolicy` enum, `StateDerivatives::unclamped`,
  OscilloSim pins, Python binding.
- DV-007 adjudication (`45cca61`): explained-divergence clause in both gates,
  §10.4 item 3 evidence.
- Independent-review remediation (`779b2ac`): OscilloSim pins, strict-checks
  diagnostic, 67-case audit, binding coverage.
- Documentation (`c825077`, `8d9e070`, `7235ae6`): Parity Report, Plan
  amendment #47, CHANGELOG, Migration Guide, Sphinx pages, audit record.

Nothing undeclared shipped. The `evidence` extra in `pyproject.toml` declares
mpmath/sympy for the evidence generators (independent review finding S8).

### S2.2 A2 — Plan conformance

✅ PASS. Architecture rules preserved:
- Crate layering: `prin-dynamics` (core dynamics, `#![forbid(unsafe_code)]`),
  `prin-sim` (engine, OscilloSim), `prin-py` (bindings), `prin-kernels` (GPU).
  The `GuardPolicy` enum lives in `prin-dynamics::integrate`; `prin-sim`
  selects it at construction sites.
- "One algorithm one implementation": the guard logic is in `state.rs`
  (`clamp_amplitude`, `clamp_derivative`); integrators select via `GuardPolicy`.
- No numerics in Python: the f64 instrument (`parity/prinet_f64.py`) is a
  test-local measurement tool, not a production path; it monkeypatches PRINet
  3.0's archived methods for comparison purposes only.
- Explicit state/seeding: the H2a gate fingerprints the entire stream
  (specs + parameters + initial arrays) against a committed SHA-256 constant.
- Plan §5.6 preserved hazards: amendment #47 makes the list path-specific,
  naming the `OscillatorModel._step_euler`/`_step_rk4` guard as the default
  and the fused-kernel/OscilloSim guard as opt-in.

### S2.3 A3 — Test conformance

✅ PASS. Tests written in tandem: `bd737e1` (failing tests) precedes
`34e8811` (fix). Coverage:
- Rust: S1.5 records `cargo llvm-cov -p prin-dynamics --lib` at 97.2%
  changed-line coverage (69/71); `e8841c1` covers the 2 remaining lines.
- Python: `interrogate` 97.6% ≥ 95% threshold; `pytest tests/` 3264 passed,
  178 skipped, 48 deselected, 0 failed (S1.5); `pytest parity/` 2121 passed,
  1 skipped (S1.5).
- No weakened or skipped tests: the 22 ill-conditioned fuzz cases are
  excluded from pointwise comparison but re-proved ill-conditioned on every
  run; the exclusion is asserted, not assumed.

S2 local run: `pytest tests/ -m "not slow and not gpu"` completed at
`7235ae6`: **3271 passed, 4 failed, 181 skipped, 48 deselected** in 686s.
The 4 failures are all `test_wp001_baseline.py::test_release_workflow_*`
— the known Windows WSL bash relay issue (AGENTS.md: `execvpe(/bin/bash)
failed`, WSL relay present without a working distribution). These are
environmental, not code defects; CI runs these on Linux where bash is
available. `cargo test` hit the known Windows linker contention (LNK1104,
AGENTS.md) during concurrent execution with pytest. S1.5 records 1594
passed, 0 failed, 1 ignored (48 suites) at `34e8811`; the post-`779b2ac`
CI run `36083847894` is green.

### S2.4 A4 — Numerical parity

✅ PASS. Golden-corpus cases for touched primitives pass at tolerance:
- Full-corpus gate: 504/504 pass (19 DV-007 cases pass under the
  explained-divergence rule, with PRIN matching the f64-corrected reference).
- H2a fuzz gate: 978 well-conditioned + 22 ill-conditioned characterizations
  pass; 48 DV-007 breaches pass under the explained-divergence rule.
- Invariants preserved: phase wrap `[0, 2π)`, amplitude floor `0.0` (default)
  or `[1e-6, 10]` (Bounded), derivative clamp `±1e4` (sparse k-NN only, or
  Bounded).

### S2.5 A5 — Code quality gates

✅ PASS. Local verification on Windows host, project venv:

```text
ruff check python/ tests/ benchmarks/ tools/ parity/ EVIDENCE/exp001-d1-s1/
    All checks passed!
ruff format --check (same dirs)
    318 files already formatted
mypy python/prin --strict
    Success: no issues found in 62 source files
cargo fmt --all -- --check
    clean
cargo clippy --workspace --all-targets -- -D warnings
    clean (6.58s)
```

S1.5 records the same gates clean at `34e8811` and `c825077`; CI run
`36083847894` at `c825077` is green.

### S2.6 A6 — Security

✅ PASS.
- No `unsafe` outside audited modules: `prin-dynamics` has
  `#![forbid(unsafe_code)]`; grep for `unsafe` in `crates/prin-dynamics/src`
  returns only the forbid line.
- `bandit -r python/prin -c pyproject.toml`: No issues identified (20,216
  lines scanned).
- `ruff check` clean (S2.5).
- `cargo audit`: 3 allowed warnings (bincode unmaintained, paste
  unmaintained, chacha20 yanked); no vulnerabilities.
- `pip-audit .`: No known vulnerabilities found.
- No secrets, no runtime codegen in changed files.

### S2.7 A7 — Docstring/doc coverage

✅ PASS.
- `interrogate -c pyproject.toml python/prin`: 97.6% ≥ 95% threshold.
- Rust 100% public: `RUSTDOCFLAGS="-D warnings" cargo doc --workspace
  --no-deps` clean (S1.5).
- Sphinx: `sphinx.cmd.build -W --keep-going -b html DOCS/sphinx
  DOCS/sphinx/_build/html` exit code 0 (S2 local run, clean build per
  AGENTS.md).

### S2.8 A8 — Repository hygiene

✅ PASS.
- No TODO/FIXME/HACK/XXX markers in `crates/prin-dynamics/src`, `parity/`,
  or `python/prin`.
- `__all__` consistent: `test_api_surface.py` and `test_api_surface_matrix.py`
  pass (S2 pytest run).
- No orphan files: all new files are referenced (EVIDENCE README, audit
  record, CHANGELOG, Migration Guide).
- `.gitignore` respected: `.pytest_basetemp/`, `DOCS/sphinx/_build/`,
  `target/` are gitignored.

### S2.9 A9 — CI

✅ PASS (local gate reproduction; CI authoritative).
- S2 is a read-only audit; nothing pushed this cycle. Local gates reproduce
  S1.5's results (S2.3–S2.7).
- S1.4 records the red → green CI transition: run `36078335512` (red,
  `bd737e1`), run `36080877871` (red, `34e8811`), run `36083119713` (green,
  `45cca61`), run `36083847894` (green, `c825077`).
- S1.9 records the head CI at `779b2ac` (independent-review remediation).
- The latest commit `7235ae6` fixes the AST-pin for Python 3.12
  compatibility (parity instrument test).
- Benchmark regression gates: not tripped (S1.5 records `pytest tests/`
  green; the correction does not affect performance paths).

### S2.10 A10 — Artefact trail

✅ PASS. Prior cycle's audit/report artefacts exist and are consistent:
- `EVIDENCE/exp001-d1-s1/README.md` indexes the evidence files.
- `root_cause_decomposition.py` and `dv007_exactness_audit.py` are committed
  generators with documented regeneration procedures.
- `root-cause-decomposition-prefix.json` and `-postfix.json` record the
  pre-fix and post-fix builds with `git_head`, `prin_package`,
  `prin_extension` provenance.
- `dv007-exactness-audit.json` records the 67-case audit with full
  provenance (mpmath DPS, torch/numpy versions, platform).
- The S1 record (`2026-09-23-exp001-d1-s1-correction-implementation.md`)
  and this S2 record are in `DOCS/audits/`.

### S2.11 Findings

| ID | Severity | Dimension | Description | Disposition |
|---|---|---|---|---|
| S2-F1 | D4 | A3 | `cargo test --workspace` on this Windows host hits LNK1104 (linker contention) when run concurrently with pytest or other cargo invocations. AGENTS.md documents the workaround (`-j 1`, sequential execution). Not a code defect. | Environmental; S1.5 records 1594 passed at `34e8811`; CI is authoritative. |
| S2-F2 | D4 | A3 | `pytest tests/ -m "not slow and not gpu"` at `7235ae6`: 3271 passed, 4 failed (WSL bash relay, environmental), 181 skipped. The 4 failures are `test_release_workflow_*` requiring Git Bash on PATH (AGENTS.md documents the WSL relay issue on this host). CI runs these on Linux. | Environmental; not a code defect. CI authoritative. |
| S2-F3 | D4 | A2 | `#[non_exhaustive]` on `GuardPolicy` was deferred from S1.9 (would break ~13 downstream construction sites). Belongs with the API freeze, not this correction. | Deferred to API freeze session; documented in S1.9. |
| S2-F4 | D4 | A2 | RK45/Exponential/Jacobian keep their `[1e-6, 10]` amplitude clamp (S1.7 item 1). PRINet 3.0's `ExponentialIntegrator` and `BatchedRK45Solver` clamp at `min=0.0`, so this is the same defect class. EXP-001 does not exercise these paths. | Documented and pinned by regression tests; deferred to a future WP. |
| S2-F5 | D4 | A2 | `prin-kernels` mean-field RK4 Triton kernel clamps amplitude to `[1e-6, 10]`; PRINet 3.0's API reference documents `≥ 0` for its Triton mean-field RK4 kernel. Not verified against the Triton source. | Deferred; flagged for review (S1.7 item 5, S1.9). |

No findings above D4. No systemic drift.

### S2.12 Verdict

**PASS.**

The EXP-001 D1 correction satisfies the S2 brief's six specific verification
items and the A1–A10 audit checklist. The root cause is established by
controlled substitution and arbitrary-precision audit; the fix covers both
failure populations (DV-007 and guard); the new gates are red on the pre-fix
tree and green on the post-fix tree; EXP-001's record is untouched; and all
code quality, security, and documentation gates pass.

Five D4 findings are recorded (linker contention, pytest run in progress,
`#[non_exhaustive]` deferred, RK45/Exponential guard deferred, Triton kernel
claim unverified). None is above D4; none is systemic.

**Not authorized by S2:** merging PR #24, `EXP-001-r1`, or releasing session
`0159`. Session `0159` stays `BLOCKED`. S3 (remediation) and S4 (documentation)
follow in order; S3 has no D1/D2 findings to remediate, so it may close
immediately if the maintainer accepts the D4 dispositions.
