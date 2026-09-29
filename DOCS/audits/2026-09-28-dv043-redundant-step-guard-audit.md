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

**Pending.** Per Development Workflow and Audit Standards §7 a hotfix is
retro-audited, and per the DV041-F4 lesson this report does not grade its own
remediation. A delta re-audit should target, at minimum: the two new tests
(`clamp_derivative_is_idempotent_where_the_guard_skip_relies_on` and the
`-0.0` addition) and whether they are non-vacuous; the four re-cited Versioning
clauses and whether the pre-1.0 bullet genuinely authorises this break at
`1.0.0-rc1`; the corrected `models.rs` line numbers; the `lib.rs` crate-doc
wording; and the Sphinx `-W` build result now that it has been run.

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
