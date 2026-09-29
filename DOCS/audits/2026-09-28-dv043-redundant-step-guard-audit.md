# DV-043 — Redundant fixed-step derivative guard: independent audit report

**Session:** `Hotfix-DV043` (ad hoc hotfix/correction session, Development
Workflow and Audit Standards §7).<br>
**Date:** 2026-09-28 UTC.<br>
**Subject:** the DV-043 fix on branch `hotfix/dv043-redundant-step-guard`, off
`main` @ `5615edab5b53afd6602907343a596cdc3f8dff4a`.<br>
**Auditor:** an independent fresh-context reviewer that did not author the
change and was briefed to break it. Barred from running any build, test or
benchmark so it could not perturb the measurement window; every conclusion below
is therefore derived from source reading and read-only `git`, and the auditor
listed explicitly what it could not verify (§5).<br>
**Implementer:** Qwen Code (AI pair). **Maintainer:** MichaelMaillet.<br>
**Related records:** [`DEFERRED_VALIDATION_REGISTER.md`](../reports/DEFERRED_VALIDATION_REGISTER.md)
DV-043; [`campaign-plan.md`](../experiments/campaign-plan.md) §11.8 and §14.2
amendment #9; [`triage-dv043-handoff.md`](../experiments/triage-dv043-handoff.md).

> This report records the auditor's verdict and findings as the auditor gave
> them. It does not self-grade: the implementer's remediation of each finding is
> listed separately in §4 and is **not** asserted to be clean. A delta re-audit
> by the same or another independent reviewer is required before this hotfix is
> treated as closed (DV041-F4 precedent — a register row that self-asserted the
> auditor's verdict before the delta re-audit ran was itself graded D2).

---

## 1. Auditor's verdict

**`PASS-WITH-FINDINGS`.** Verbatim justification: *"the numerical-equivalence
argument is sound and I could not break it in either feature configuration, but
four verification gates the project's own standards require were not run, and
the breaking-change authority is cited from the wrong clause of the Versioning
standard."*

**No D1.** The auditor states it actively tried to construct one — an
unguarded-out-of-range value reaching a skipping integrator, stale buffer
elements surviving into the next step, and a lost `NaN` repair — and that each
is closed.

## 2. What the auditor confirmed

| Question | Verdict | Substance |
|---|---|---|
| **A. Numerical equivalence** | **Holds** | `StateDerivatives::new` routes all three arrays through `guard_derivatives` *before* the `guarded: true` literal, so `Ok` ⇒ every value finite and within `±DERIV_CLAMP`. Under `strict-checks`, `guard_derivative_value` then returns `Ok(d)` unchanged; under the default build it returns `Ok(clamp_derivative(d))`, and `clamp_derivative` is the identity on an in-range finite value. The old `guard_derivative_value(...)?; *d = clamp_derivative(*d);` and the new `*d = guard_derivative_value(...)?;` are equivalent in **both** configurations *including the error path*: on `Err` at index *i* neither version has written element *i*, and elements `0..i` hold the input value in both. No caller can observe a difference, because `deriv_buf` and `k1`–`k4` are `clear()`ed and re-`reserve()`d before `extend_from_slice`, so no stale element survives. The new condition `Bounded && !source_guarded` is identical to the old `Bounded` when the flag is false and strictly narrower otherwise. |
| **B. No false `guarded: true`** | **Confirmed** | All 20 workspace construction sites enumerated. `new` at 9 sites → `true`; `unclamped` at 11 → `false`; 4 struct literals → `false`, all correctly: the two finite-difference gradient sites are finite-checked but never clamped, and the two test models deliberately inject `NaN` bypassing the constructors. The auditor notes `true` at any of those four **would have been a D1** — it would silently drop the `NaN`→`0.0` repair and the gradient bound. It also independently verified the mutation caveat: no code anywhere writes to a constructed `StateDerivatives`' arrays. |
| **C. The `n <= 1` trap** | **Handled** | Because the flag rides the constructor, the `unclamped` single-oscillator branches report `false` and the `new` branches report `true`; no integrator path can skip a guard that used to run. The new `prin-sim` test pins both branches for both sparse models. |
| **D. Error-message stability** | **No change** | Under `strict-checks` an out-of-range value cannot survive `new()`, so the integrator's flat-`3N` `index` diagnostic can never be the first to fire for a guarded source; the constructor's per-component diagnostic fires earlier, exactly as before. Under the default build the pass is infallible. `StateError` is unchanged. |
| **E. Semver claims** | **Verified** (but see F4) | `StateDerivatives` re-exported at `lib.rs:60`; `guarded` is `pub(crate)`; the only struct literals/destructurings are inside `prin-dynamics`; the manual `PartialEq` compares the same three fields the derive did; `#[serde(skip)]` preserves the wire format and deserializes to `false`; `PyStateDerivatives` has no `#[new]` and exposes only the three arrays, so `_prin_core.pyi` needs no change. |
| **F. Test adequacy** | **Adequate, not exhaustive** | The bit-identity test is **non-vacuous** — it would fail if the guard pass altered in-range or at-bound values, or if `is_guarded()` leaked to `unclamped`. All four pre-existing guard tests were independently confirmed to sit on `unclamped`-returning models, so none was weakened. |
| **G. Documentation accuracy** | **Mostly accurate** | The amendment-numbering claim was **verified**: `main` carries §11.1–§11.6 only while `campaign/exp001-r1-e1` carries §11.7 and rows #7/#8, so §11.8/#9 is correct and the 6→9 gap is genuinely explained. Citations spot-checked exact: `engine.rs:191`/`:329`, `bands.rs:580`, `gpu.rs:616`/`:647`/`:662`, `sweep.rs:305-308`, `sweep_bench.rs:144`, `dispatch.rs:28`. The DV-043 row correctly says `OPEN — FIX COMMITTED` and does **not** claim closure; no self-graded verdict appears. "Five tests in tandem" is accurate. The new RST is well-formed. |
| **H. Anything missing** | **Nothing structural** | Test-in-tandem satisfied; `#![warn(missing_docs)]` satisfied including on `PartialEq::eq`; `DOCS/sphinx/api/dynamics.rst` needs no change (it documents the Python module). The auditor notes Testing Standards' "every bug fix ships a regression test that fails before the fix" is technically unmet — **impossible here**, since the fix is defined by value-identity — and judges the green-nightly closure gate the right substitute. |

## 3. Findings

| ID | Sev | Location | Finding |
|---|---|---|---|
| **DV043-F1** | **D2** | `DOCS/sphinx/migration_guide.rst`; `AGENTS.md` verification list | RST was edited but the Sphinx `-W --keep-going` build was not run; `cargo llvm-cov -p prin-dynamics`, `cargo audit` and `pip-audit` were also absent from the reported evidence. The auditor manually confirmed the heading underline is ≥ the title length and that the new block contains no `:doc:` role, so it is *probably* clean — but unproven. |
| **DV043-F2** | **D2** | `Testing_Standards.md:90` | `cargo test --workspace --features strict-checks` was not run; only `-p prin-dynamics --lib`. That leaves the new `prin-sim` test and every integration test unexercised in the exact configuration where `new()` can raise and where the skip's premise lives. |
| **DV043-F3** | **D3** | DV-043 register row; `SESSION_REGISTER.md` `Hotfix-DV043` row; handoff §11 | The prose said "FIX COMMITTED", "local commits, not pushed, no PR" and "Local commits only" while `git log` showed HEAD == `5615eda` == `PRIN/main` and `git status` showed 9 modified + 1 untracked — **nothing committed**. Inaccurate as read; the auditor notes the same class as DV041-F4, graded D2 there. |
| **DV043-F4** | **D3** | `CHANGELOG.md` "Changed"; `migration_guide.rst`; `campaign-plan.md` §11.8; DV-043 register row | All four cited *"Public API stability **post-1.0**"* as **permitting** the break. `Cargo.toml` is `1.0.0-rc1` → pre-1.0. The cited clause is the *restrictive* one (major bump **and** a ≥1-minor `_deprecation` cycle **and** Migration Guide entries); this change supplies only the third, so read literally the cited clause **forbids** it. Correct authority: the adjacent pre-1.0 bullet. |
| **DV043-F5** | D4 | DV-043 register row; handoff §5 | `models.rs:427`/`:694`/`:996` are `push` lines inside the k-NN loops, not the clamping `StateDerivatives::new` calls, which are at `:431`/`:698`/`:1000`. |
| **DV043-F6** | D4 | the bit-identity test's rate list | Rates omitted `-0.0`, although §11.8, the DV-043 row and the handoff all cite `-0.0` as an idempotency case the argument rests on. `assert_bit_identical` compares `to_bits()`, so it would have caught a sign flip. |
| **DV043-F7** | D4 | `prin-dynamics/src/lib.rs` crate doc | Still said `Bounded` "reproduces the … `±1e4` guard" with no mention of the provenance skip or `is_guarded()`. Not false, but it is the first place a reader looks. |

The auditor's own "most serious thing found" was **F4**: *"a breaking public-API
change justified by citing the one clause of the Versioning standard that would
prohibit it as implemented… Left uncorrected across four documents, it
establishes a precedent that a Migration Guide entry alone licenses a post-1.0
break — a governance defect that outlives this hotfix."*

## 4. Remediation

| ID | Action taken |
|---|---|
| **DV043-F1** | Sphinx `_build` deleted and the `-W --keep-going` HTML build re-run from clean, per `AGENTS.md`'s clean-build discipline (an incremental build cannot detect that an `automodule`-sourced docstring changed under an unmodified `.rst`, so a reused output directory can mask a genuine warning). The first attempt exited 0 but its log showed a reused pickled environment; only the post-deletion run counts. `cargo llvm-cov -p prin-dynamics` run — **default configuration only**; the `--features strict-checks` coverage run was not repeated. `cargo audit`/`pip-audit` not triggered, see §6. |
| **DV043-F2** | **Partially closed, and the gap is recorded rather than papered over.** `cargo test -p prin-dynamics -p prin-sim --lib -j 1 --features prin-dynamics/strict-checks` was run in a separate target directory (310 + 165 passed / 0 failed), which does cover the new `prin-sim` test the finding named, in the configuration where `new()` can raise. The **workspace-wide** `--features strict-checks` run the finding asked for was *not* completed: it is blocked by the same `LNK1104` host linker contention as the default-configuration workspace re-run (§8; handoff §9.4). `prin-dynamics`' own integration parity tests were exercised instrumented under `cargo llvm-cov`, but not under `strict-checks`. |
| **DV043-F3** | The finding is correct and is an ordering defect, not a wording one: the prose was written before the commits existed. Remediated by actually committing, which makes all three statements true, rather than by weakening them. The register row, session row and handoff §11 are unchanged in substance because their content describes the committed state. |
| **DV043-F4** | Re-cited to Versioning and Release Standards §1's **pre-1.0** bullet in all four documents, with the reasoning made explicit (the workspace is at a pre-release; `1.0.0`, the feature-complete milestone, has not shipped, so the post-1.0 regime is not yet in force) **and** an explicit statement that the post-1.0 clause is *not* the authority here and would forbid the change as implemented. The Migration Guide entry is supplied regardless. |
| **DV043-F5** | Corrected to `:431`/`:698`/`:1000` in both places; re-verified by `grep` against the post-edit tree rather than taken from the auditor's word. |
| **DV043-F6** | `-0.0` added to the bit-identity test's rate list, with the test comment extended to say why it matters (the comparison is on `to_bits()`, so a sign flip fails rather than comparing equal). Additionally a direct `clamp_derivative` idempotency test was added over `0.0, -0.0, 1.0, -2.5, ±DERIV_CLAMP, NaN, ±Inf`, which pins the claim the documents actually rest on rather than reaching it only indirectly through a step. |
| **DV043-F7** | `prin-dynamics/src/lib.rs` crate doc now names `state::StateDerivatives::is_guarded` and states that a `Bounded` integrator does not re-clamp a buffer the model already guarded. |

## 5. Claims the auditor could not verify

Recorded so that no reader mistakes them for independently confirmed: every
build/test/lint result (`fmt`, `clippy`, `cargo test` 1603/0, `strict-checks`
309/0, `cargo doc`, Snyk Code 0 issues, `pytest` 3277+5, `parity/` 2144); all
benchmark ratios, the ten nightly breaches, the ~25 ns per-oscillator
fingerprint and the reference-host A/B; that `StateDerivatives` "is serialized
into no persisted artefact" (the auditor verified construction sites, not
serialization sinks); and ≥95% coverage of the changed lines.

## 6. Items not run, with rationale

`cargo audit`, `pip-audit` and Snyk Open Source are **not** triggered by this
change: no dependency, lockfile or manifest changed (`git status` shows only
four Rust source files and six documents). This follows the DV-041 precedent,
which recorded the same reasoning. Snyk **Code** was run, at
`severity_threshold=low`, on `crates/prin-dynamics/src` and
`crates/prin-sim/src/engine.rs`: 0 issues each.

## 7. Delta re-audit

**Complete — `PASS-WITH-FINDINGS`, no D1/D2/D3.** Performed 2026-09-28 UTC by
a second independent fresh-context reviewer that did not author the commits
and did not contribute to the S2 remediation, on the committed tree `1f57c45`
(`hotfix/dv043-redundant-step-guard`, clean worktree; four commits `e4f5b4e`,
`f0a7079`, `eca0f5d`, `1f57c45` over `main` @ `5615eda`). §1–§6 and §8 record
the original auditor's verdict and stand unmodified; this section is the
independent delta and does not retrograde or restate that verdict. The S3
correction applied on top of this audit is recorded separately in §7.4 and is
**not** self-cleared here — the F8/F9 edits were lead-reviewed on 2026-09-28
UTC for exact textual corrections only; no full-suite rerun or CI claim.

Nothing in this section infers numeric performance or CI status from prose.
Every benchmark magnitude (the ~25 ns/oscillator fingerprint, the 1.075 vs
1.023 A/B medians, the ten nightly breaches and the `step_parallel/16384`
+28.8 %), the nightly run contents, required-CI status, Snyk results, the
`pytest` 3277+5 tally, the 2144-case parity run and all `llvm-cov` coverage
numbers remain **unverified** — not re-run by this reviewer.

### 7.1 Gates run independently

The Rust tests ran sequentially with `-j 1`; the Sphinx build followed.
Logs are local scratch under the gitignored `.qwen/tmp/` (`.gitignore:59`).

| Command (verbatim) | Result | Exit |
|---|---|---|
| `cargo test -p prin-dynamics -j 1 --lib` | 309 passed / 0 failed; all five lib tests this change ships are named and green — `integrate::tests::bounded_step_skips_the_redundant_pass_without_changing_any_value`, `integrate::tests::bounded_step_still_clamps_derivatives_the_model_left_unclamped`, `state::tests::clamp_derivative_is_idempotent_where_the_guard_skip_relies_on_it`, `state::tests::guarded_flag_records_which_constructor_ran`, `state::tests::guarded_flag_is_provenance_and_changes_no_public_contract` | 0 |
| `cargo test -p prin-dynamics -j 1 --lib --features strict-checks` | 310 passed / 0 failed; the bit-identity test (not cfg-gated) also passes in the strict configuration | 0 |
| `cargo test -p prin-sim -j 1 --lib --features prin-dynamics/strict-checks` | 165 passed / 0 failed; `engine::tests::sparse_models_report_the_guard_they_actually_applied` green where `new()` can raise | 0 |
| `.venv/Scripts/python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx .qwen/tmp/sphinx-audit-html` | `build succeeded`, **0 warnings**, `updating environment: [new config] 35 added, 0 changed, 0 removed`, all 35 sources read and written | 0 |

Log files: `.qwen/tmp/dv043-delta-audit-prin-dynamics-lib.log`,
`dv043-delta-audit-prin-dynamics-strict-lib.log`,
`dv043-delta-audit-prin-sim-strict-lib.log`, `dv043-delta-audit-sphinx.log`.
The Sphinx build targeted a *freshly created* output directory — the
`AGENTS.md`-sanctioned alternative to deleting `DOCS/sphinx/_build` — so the
`[new config] … 35 added` line is a genuinely clean environment, not a reused
pickled one. This independently confirms the post-deletion run §4 records for
DV043-F1.

**Not run, not claimed:** the workspace-wide `cargo test --workspace
--features strict-checks` that DV043-F2 asked for remains unrun (the `LNK1104`
host-linker blockers recorded in handoff §9.4); `cargo llvm-cov`,
`cargo audit`, `pip-audit`, Snyk, and any pytest/parity leg were not re-run
here.

### 7.2 Technical claims re-derived at `1f57c45`

- **Bit-identity — holds, replayed at source.** `GuardPolicy::derivatives`
  (`integrate.rs:120-138`) returns early on `source_guarded || self !=
  Bounded`, else assigns `guard_derivative_value`'s result per element.
  `StateDerivatives::new` (`state.rs:482-499`) routes all three arrays through
  `guard_derivatives` *before* the `guarded: true` literal, so the skipped pass
  is bitwise identity on a `new()` output in both configurations: the default
  build needs `clamp_derivative ∘ clamp_derivative == clamp_derivative`
  bitwise — exactly what
  `clamp_derivative_is_idempotent_where_the_guard_skip_relies_on_it` asserts on
  `to_bits()` over `{0.0, -0.0, 1.0, -2.5, ±DERIV_CLAMP, NaN, ±Inf}` — and the
  strict build needs nothing (the pass returns `Ok(d)` unmodified on `new()`
  outputs). Error paths are equivalent: on `Err` at index *i* neither version
  writes element *i* and the `0..i` prefix writes are identical. The flat
  buffers are `clear()`ed and re-`extend_from_slice`d before every pass
  (`integrate.rs:436-441`, `550-555`, `596-600`, `617-621`, `638-642`), so no
  stale element survives. `assert_bit_identical` (`integrate.rs:2721-2733`)
  compares `to_bits()` across all three state arrays: **non-vacuous** — it
  fails if the skipped pass would have altered any in-range or at-bound value,
  and the `is_guarded()`/`!is_guarded()` asserts pin provenance both ways. The
  NaN/Inf and out-of-range cases are covered by the idempotency test plus the
  paired pre-existing guards (`bounded_step_still_clamps…` non-strict,
  `bounded_guard_rejects_out_of_range_derivatives_under_strict_checks` strict —
  both observed passing). See **DV043-F9** for the one caveat on the `-0.0`
  row.
- **`n <= 1` provenance — no false-positive `guarded=true` on an unguarded
  branch, no missing guard.** Both `prin-sim` sparse models early-return `unclamped` at `n <= 1`
  (`engine.rs:163-176`, `276-289`) and `new` above it (`:191`, `:329`);
  `models.rs:454`/`:734`/`:1024` do the same. `guarded: true` exists only at
  `state.rs:497`; the four struct literals are all `false` (`models.rs:137`,
  `integrate.rs:2161` — both verified finite-checked-only — and the test models
  `integrate.rs:2816`/`:3084`); serde deserializes to `false`. The only
  `derivatives` consumers are `integrate.rs:443` (Euler) and `555`/`601`/`622`/
  `643` (RK4 k1–k4); RK45/Exponential never had the pass and
  `MultiRateIntegrator` delegates to inner integrators at default
  `NonNegative`, which early-returns either way — identical to the old
  `self == Bounded` gate. End-to-end confirmation came free: the pre-existing
  pair `bounded_guard_silently_clamps_large_derivatives_like_pre_correction`
  (default) and `bounded_guard_rejects_out_of_range_derivatives_under_strict_checks`
  (strict) drive an out-of-range `3e4` derivative through a `Bounded` RK4 step
  over the n=1 `unclamped` branch — both passed, so the guard still fires
  exactly where the flag says it should.
- **Public-array mutation — invariant is construction-time, and the documents
  say so.** Zero post-construction writes to a `StateDerivatives`' fields exist
  in the workspace (field assignment, `iter_mut`, `push`/`extend`/`clear`/
  `truncate`/`resize` on `dphase`/`damplitude`/`dfrequency` were all grepped;
  `bands.rs:529-580` writes only local `Vec`s before `new`; PyO3 exposes
  clone-out getters and no `#[new]`). The invariant is *"is_guarded ⇒ the
  arrays **as constructed** passed `±DERIV_CLAMP` + finite"* — a
  construction-time fact, not a mutation invariant. What remains unproven is
  the deliberate residual: an external caller can edit the `pub` arrays after
  construction, the stale `true` flag survives (it is `pub(crate)`, so it
  cannot even be corrected from outside), and a `Bounded` integrator then
  silently skips — whereas the pre-change unconditional pass was robust to
  that. Accepted and recorded at `state.rs:448-452`, the register row and
  campaign plan §11.8; nothing in this workspace does it.

### 7.3 F1–F7 delta status

| ID | Delta status (verified at `1f57c45`) |
|---|---|
| **DV043-F1** | **Closed (Sphinx half).** Independently re-run clean to a fresh output dir — 0 warnings, `[new config] 35 added` (§7.1). `llvm-cov`/`cargo audit`/`pip-audit` not re-run by this reviewer and not claimed. |
| **DV043-F2** | **Partially closed — residual stands.** The crate-scoped strict runs are re-verified green (310 + 165); the workspace-wide `--features strict-checks` run remains unrun on the recorded `LNK1104` blockers — **not claimed**. |
| **DV043-F3** | **Closed.** The prose is now true: four commits exist on the branch, `git status` clean; the statements were fixed by committing rather than reworded. |
| **DV043-F4** | **Closed.** All four documents (`CHANGELOG` Changed block, `migration_guide.rst:150-181`, `campaign-plan.md` §11.8, the DV-043 register row) cite Versioning §1's **pre-1.0** bullet and explicitly state the post-1.0 clause is not the authority and would forbid the change as implemented; checked against `Versioning_and_Release_Standards.md:12-19` and `Cargo.toml:15` (`1.0.0-rc1`). |
| **DV043-F5** | **Closed.** `models.rs:431`/`:698`/`:1000`, `engine.rs:191`/`:329`, `bands.rs:580`, `gpu.rs:616`/`:647`/`:662` are all `StateDerivatives::new`; `sweep.rs:305-308` and `sweep_bench.rs:144` pin `GuardPolicy::Bounded`. |
| **DV043-F6** | **Closed.** `-0.0` is in the step test's rate list (`integrate.rs:2750`) and the direct idempotency test exists (`state.rs:794-818`); both pass in both configurations. The `-0.0` row's residual caveat is carried as F9 below. |
| **DV043-F7** | **Closed.** `lib.rs:32-36` names `state::StateDerivatives::is_guarded` and states the `Bounded` skip. |

**A1–A10 scoped assessment.** The checklist always applies; this table scopes
each item to what was actually done and no full-checklist PASS is implied.

| Item | This delta's status |
|---|---|
| A1/A2 scope and plan | Traced to source — the rubric items were re-derived from the committed tree at `1f57c45`, and campaign plan §11.8/amendment #9 were read against the committed text. |
| A3 scoped tests | The prescribed crate-scoped runs pass (309/310/165, §7.1); the ≥95 % changed-line coverage expectation is **unmeasured** — no `llvm-cov` run here. |
| A4 numerical invariants | Bit-identity and guard-provenance invariants verified at source and by test; the corpus parity legs were **not** re-run. |
| A5 lint gates | `cargo fmt --all -- --check` passed (exit 0) on the Rust comment edit; `clippy`, `ruff`, `mypy` not re-run. |
| A6 security gates | The S3 delta is comment/doc-only — no dependency or `unsafe` change — but `cargo audit`, `pip-audit` and Snyk were **not** re-run: unverified, not claimed clean. |
| A7 docs build | Fresh-output-dir Sphinx `-W --keep-going` run independently: 0 warnings, 35/35 sources (§7.1). |
| A8 worktree | Tracked worktree clean at `1f57c45` when audited; the only subsequent edits are this §7/S3 recording pass. |
| A9 integration and CI | Local targeted tests only; merge CI and the closing green nightly remain **OPEN** — not claimed. |
| A10 record consistency | Audit/handoff/register consistency checked; two stale enumerations found and corrected as DV043-F8/F9. |

Amendment #9 (campaign plan §14.2) remains the authorisation of record; no new
amendment is proposed or implied.

### 7.4 New findings and the S3 remediation applied on top of this audit

| ID | Sev | Location | Finding |
|---|---|---|---|
| **DV043-F8** | D4 | `SESSION_REGISTER.md` `Hotfix-DV043` row; DV-043 register row | "Five tests in tandem" / a five-name enumeration predates the F6 remediation; six new tests actually ship — `state::clamp_derivative_is_idempotent_where_the_guard_skip_relies_on_it` was absent from both (named only in handoff §9.3). |
| **DV043-F9** | D4 | `integrate.rs` `bounded_step_skips_the_redundant_pass_without_changing_any_value` comment | The comment claimed a `-0.0` sign flip "would fail rather than compare equal", but `assert_bit_identical` compares the *stepped* state and `x + dt·(∓0.0) = x` bitwise on this nonzero starting state — a derivative sign flip cannot reach the comparison, so that row is individually non-discriminating. The direct `clamp_derivative` idempotency test is what pins `-0.0`. |

**S3 remediation applied** (by this reviewer, mechanically; **lead-reviewed on
2026-09-28 UTC for exact textual corrections only — the F8/F9 four-file
delta confirmed six test names now enumerated, the comment now accurately
noting `-0.0` can be masked, no executable code, `git diff --check` clean; no
full-suite rerun or CI claim — this report does not grade them**):

1. `crates/prin-dynamics/src/integrate.rs` — the signed-zero sentence of the
   test comment replaced with: *"Signed zero exercises this branch, but a step
   from a nonzero state can hide a derivative sign flip. The direct
   clamp_derivative idempotency test checks -0.0 with to_bits() instead."*
   Comment only; no executable code touched.
2. `DOCS/sessions/SESSION_REGISTER.md` — `Hotfix-DV043` row: "Five tests in
   tandem" → "Six tests in tandem (including the post-audit clamp idempotency
   test)".
3. `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` — DV-043 row's
   Tests-in-tandem list gained
   `state::clamp_derivative_is_idempotent_where_the_guard_skip_relies_on_it`.

F8/F9 are additive corrections to the record; they do not reopen the reviewed
code, and the original §1–§6 verdict provenance is untouched.

## 8. Verification ledger

Complete, in [`triage-dv043-handoff.md`](../experiments/triage-dv043-handoff.md)
§9: §9.1 the pre-remediation gates (the state this audit reviewed), §9.2 the
post-remediation re-runs that close DV043-F1 and DV043-F2, §9.3 the
`cargo llvm-cov -p prin-dynamics` table with an explicit statement of what is
*not* claimed (no diff-coverage percentage was measured; instead every changed
line is mapped to a named test), and §9.4 the accounting of the five unrelated
`pytest` failures plus the gates that were not re-run or not triggered.

Two gaps are recorded there rather than closed, and this report does not paper
over them. The **workspace-wide** `cargo test`/`clippy` re-run after remediation
is blocked by this host's `LNK1104` contention — 18+ attempts, a different
target each time — so the unchanged crates rest on the pre-remediation
1603/0/1 workspace run, with the post-remediation delta confined to
`prin-dynamics`. And the four `test_wp001_baseline.py` failures could not be
re-run with `AGENTS.md`'s documented Git-Bash PATH remedy, because this
session's shell guard rejects `%PATH%` rewrites.

Fix validation on the reference host is in §10 of the same document. It is
reported as a within-run decomposition (`step_parallel − 4 × derivatives_parallel`)
rather than a raw cross-arm comparison, because the fixed arm's *control*
identities also moved 12–33 % faster and a raw comparison would have overstated
the recovery. On that measure the fixed arm's N=4096 step overhead is 111.52 µs
against the pre-regression 111.72 µs, with the candidate at 186.25 µs.

Sphinx note: the first `-W --keep-going` build exited 0 but was **not** clean —
its log read "loading pickled environment … 0 added, 2 changed", so it had reused
`_build/doctrees`. DV043-F1 is closed on the second run, after deleting
`DOCS/sphinx/_build`, which reported `[new config] 35 added, 0 changed,
0 removed` with all 35 sources read and written. Reporting the first run would
have been exactly the false negative `AGENTS.md`'s clean-build discipline
exists to prevent.
