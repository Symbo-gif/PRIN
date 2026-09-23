Pre-registration freeze: **`c22db0b7559dd572b368966bb0c72f283ddcd626`** — the git SHA of the last `preregistration.md` edit, frozen 2026-09-23T13:40:12Z when the first `RUN-` directory (`RUN-20260923T134012Z-6b9d6b6-corpus-cpu`) was created (campaign plan §12.4).

# EXP-001 — Session 0156 E3 execution log

**Status:** EXECUTED — all four registered runs complete; **two candidate D1 conditions and one
registered budget-cap breach are escalated below**. The preflight history that follows is
retained verbatim (it is never rewritten); execution begins at §"E3 execution — 2026-09-23 UTC".
**Record date:** 2026-09-23 UTC (maintainer session dated 2026-09-22 locally).
**Operator:** Devin (AI pair), acting on MichaelMaillet's instructions.
**Branch:** `campaign/0156-exp001-e3`.
**Latest pre-registration edit:** `c22db0b` — correct the E2 validation note
from 15 new tests to 13; the eight restored tests remain separate.

## Entry evidence

- E2 approval is recorded in `preregistration.md`; PR #20 merged as
  `e9974318b2d1ced3beb7506ca217dbb92864158e`.
- `tools/check_ci_green.py e9974318b2d1ced3beb7506ca217dbb92864158e`
  returned `RESULT: all required workflows green`: rust `35795966268`,
  python `35795966378`, parity `35795966294`, repro `35795966241`,
  snyk `35795966408`, gpu `35795966280`.
- PR #19 merged as `90c0334499156750f12ad859ec42a81634fecdbb`.
  `tools/check_ci_green.py 90c0334499156750f12ad859ec42a81634fecdbb --limit 120`
  also returned `RESULT: all required workflows green`.
- Nightly dispatch `35659096698` and scheduled run `35689809619`, both at
  `90c0334499156750f12ad859ec42a81634fecdbb`, completed with `full-suite`
  successful and `bench-regression` failed. Neither workflow was green.

## Maintainer gate decision

MichaelMaillet explicitly selected **Require whole nightly green** when asked
whether the successful dispatched `full-suite` job could satisfy DV-039 while
retaining the failed benchmark job under DV-036. That alternative disposition
was **not approved**. Campaign plan §11.2 / §14.2 amendment 1 and DV-039's
pre-0156 closure gate remain unchanged. No DV item is closed by this log.

## Fresh nightly dispatch requested by the maintainer

Command:

```powershell
gh workflow run nightly.yml --repo Symbo-gif/PRIN --ref main
```

Run: [35804529743](https://github.com/Symbo-gif/PRIN/actions/runs/35804529743).
SHA: `e9974318b2d1ced3beb7506ca217dbb92864158e`.
Trigger: `workflow_dispatch`. Terminal workflow conclusion: **failure**.

| Job | Started (UTC) | Completed (UTC) | Conclusion |
|---|---|---|---|
| `full-suite` (`107002234234`) | 2026-09-23T01:01:08Z | 2026-09-23T01:15:24Z | success |
| `bench-regression` (`107002233963`) | 2026-09-23T01:01:08Z | 2026-09-23T01:28:38Z | failure |

The failed step was `Compare against baseline (>10% mean regression fails)`.
The successful full-suite job does not satisfy the maintainer's whole-workflow
gate. This record makes no new root-cause claim about the benchmark failure.

Terminal evidence was obtained with:

```powershell
gh run watch 35804529743 --repo Symbo-gif/PRIN --interval 60 --exit-status
gh run view 35804529743 --repo Symbo-gif/PRIN --json databaseId,headSha,status,conclusion,jobs,url
```

The watch exited 1. No check was bypassed, no threshold was changed, and no
manual baseline reset or repeated dispatch was performed. The existing
workflow's `Refresh baseline` step reported success; that is not a passing
benchmark comparison or a claim that the regression was resolved.

## Run inventory and handoff

- No EXP-001 campaign driver was invoked; no campaign `RUN-` directory,
  result artefact, or run manifest was created. This is a pre-execution block,
  not an aborted experiment run.
- The pre-registration and drivers have not frozen under campaign plan §12.4;
  record the actual freeze SHA when the first authorized `RUN-` directory is
  created, preserving this preflight history.
- Session 0156 is incomplete. H1–H4 were not executed and no hypothesis was
  adjudicated. Sessions 0157/0158 were not started.
- Resume only after evidence of a wholly successful nightly and the remaining
  E3 entry checks. Any required CI/code/baseline correction must follow its
  governing correction process; it is not an implicit part of E3 execution.

## Correction authorization — 2026-09-23 UTC

After the failed dispatch, MichaelMaillet requested assessment, correction,
and another nightly. He explicitly approved the same-job fixed-reference
comparison in campaign plan §11.6 and authorized a dedicated hotfix-branch
push, PR, and branch nightly. The conditional DV-036 correction runs outside
E3; EXP-001 still has no campaign runs. Original failure evidence and the
whole-nightly-green entry condition are retained.

## DV-036 S1 local implementation evidence

The initial fail-closed regression run against the original checker returned
37 failed / 8 passed. The corrected checker and workflow-contract tests
returned 49 passed with 100% checker line coverage (96/96 statements).
Ruff and strict mypy on the checker passed; Bandit and Snyk Code (low threshold,
checker and test file) reported zero issues. YAML parsing and eight extracted
Bash blocks passed syntax checks; this alone is not GitHub expression validation.

The full local gate passed cargo fmt, workspace Clippy with warnings denied,
workspace tests (one pre-existing ignored test), and warnings-denied rustdoc;
repository Ruff check/format (310 files), strict mypy (62 package files),
interrogate (97.6%), and Bandit (zero issues). Cargo Audit reported only the
three existing governed warnings (bincode, paste, chacha20); project and docs
pip-audit each reported no known vulnerabilities. DV-register and repository
baseline checks passed.

The first full pytest invocation used a suffixed basetemp and the WSL bash
relay: 15 failed / 3151 passed / 176 skipped. No test or output guard was
weakened. Using the documented `.pytest_basetemp` and process-local Git Bash
PATH produced 3166 passed / 176 skipped / 48 deselected. The original failed
invocation remains disclosed rather than relabeled a pass.

Precommit review corrected an unavailable `runner` expression in job-level
environment configuration to a run-and-attempt-specific path under
`benchmarks/results/`; GitHub's context-availability table does not permit
`runner` at `jobs.<job_id>.env`. No timing, threshold, or reference changed.

## DV-036 S2 audit

Local implementation commit: `8bcea55`. The [correction audit](../../audits/2026-09-23-dv036-nightly-correction-audit.md) records PASS for local scope, with hosted validation and S4 closure pending. Real actionlint v1.7.7 returned zero findings. No E3 execution has begun.

## DV-036 S3 no-change remediation

S2 commit `e09b7f5` raised no additional source finding. S3 verified the
workflow, checker, and tests are unchanged from locally validated S1 commit
`8bcea55`; local delta re-audit CLEAN. S4 and hosted validation remain pending.

## DV-036 S4 preparation

S1 `8bcea55`, S2 `e09b7f5`, and S3 `a0c1d2b` are locally complete.
Documentation/index updates are prepared for the authorized hotfix push and
nightly test. S4, final Project State Report, hosted success, and main-merge
confirmation remain pending; no E3 run is authorized by these local commits.

## DV-036 hosted validation round 1

S4 documentation committed as `c736ef1`; branch pushed and PR #21 opened.
Branch nightly dispatch `35810787820` failed `bench-regression` in the
environment build step (`maturin` not on PATH for `--no-build-isolation`
editable installs) — new finding DV036-F3, recorded in the correction audit.
Fixed by per-venv activation; focused suite and lint/format/type/actionlint
checks clean. No benchmark comparison was reached; no E3 run authorized.

## DV-036 hosted validation round 2

Branch dispatch `35811372090` and post-merge main nightly `35826531821`
(`de411d0`) reached the comparison; `full-suite` passed and `bench-regression`
failed (resonance moderate +14.4%/+14.7%, contention and DLPack float64
breaches). Investigation of both evidence artefacts, plus a local interleaved
A/B, found identical binaries and no code regression (DV036-F4; harness
defect DV036-F5 deferred to 0166). The maintainer approved campaign
amendment 4 (symmetric arms, counterbalanced order, contention group
advisory on hosted runners). The fix is pushed to the hotfix branch and a
hosted run is pending. No E3 run is authorized, and session 0156 stays
blocked.

---

# E3 execution — 2026-09-23 UTC

**Operator (registered `--operator` value):** MichaelMaillet.
**AI pair executing the committed drivers:** Claude Opus 5 (Experimentation
Standards §4 authorship disclosure).
**Branch:** `campaign/0156-exp001-e3`, fast-forwarded to `origin/main`.
**Code SHA for every run:** `6b9d6b621a2a46e37373bbcafafd475c1d0f644f`
(`6b9d6b6`), working tree clean at each invocation.
**Pre-registration freeze SHA:** `c22db0b` (log line 1, campaign plan §12.4).

## Entry conditions — all met

| Condition | Evidence |
|---|---|
| E2 approval recorded | `preregistration.md` header, MichaelMaillet 2026-09-21; PR #20 merged `e997431` |
| `origin/main` green at E3 start (campaign plan §10.2) | `tools/check_ci_green.py b43455405055d189b74441642ab32c96513b2e57 --limit 120` → `RESULT: all required workflows green` (rust `35847498343`, python `35847498316`, parity `35847498434`, repro `35847498332`, snyk `35847498489`, gpu `35847498331`) |
| Red nightly dispositioned; maintainer's **whole-nightly-green** gate | `nightly.yml` dispatch `35847692136` at `b434554` concluded **success** for the whole workflow — `full-suite` (`107137725899`) and `bench-regression` (`107137725730`) both green |
| DV-036 blocking correction closed | Conditional cycle S1 `8bcea55` → S2 `e09b7f5` → S3 `a0c1d2b` → S4 closed 2026-09-23; DV036-F1/F2/F3 FIXED, F4 CLOSED, F5 deferred to 0166. Independently re-verified here by re-running the committed checker against the run's preserved evidence artefact (exit 0, identical ratios) |
| DV-038 closed before 0156 | PR #19 merged `90c0334`, required CI green |
| DV-039 closed before 0156 | Same merge plus the wholly green nightly above |
| Baseline code unchanged since E2 (campaign plan §10.2) | `git diff campaign/0156-exp001-e3 origin/main -- crates/ python/prin/ benchmarks/ parity/ paper/` → **empty**. No regression leg is required; the extension built at E2 with `--features cuda` remains valid |
| Execution environment | `prin` 1.0.0rc1; `prinet` 3.0.0 importable from the archived reference source; `hasattr(prin._prin_core, "GpuSparseKuramoto") == True`; Python 3.14.0; rustc 1.98.1; Windows-11-10.0.26200; AMD64 16 logical CPUs; NVIDIA GeForce RTX 4060, 8188 MiB (host H1) |

No timing claim is made by this experiment (preregistration §5.1), so the
campaign plan §5.3 quiescence rule does not apply and the CI runner service
was not stopped.

## H3 representative-case selection (authorized at E3 by preregistration §5.1)

§5.1 registers "the four already identified in `parity/test_parity_differential.py`'s
`_REPRESENTATIVE_CASES` plus ten more selected at E3 to complete the grid".
The selection rule adopted, stated before the run and applied uniformly with
no inspection of results: **the first case in corpus-manifest order within
each of the 14 `(model, coupling, integrator)` cells.** That single mechanical
rule reproduces all four pre-identified cases exactly and supplies the ten
remaining cells, so nothing is cherry-picked. Each cell holds 36 cases
(14 × 36 = 504, matching the manifest's `n_cases`).

## Run inventory

All four runs used the committed driver `benchmarks/campaign/exp001_driver.py`
exactly as registered in preregistration §5.3. No driver code was added or
modified during E3 (campaign plan §12.1). No `RUN-` directory pre-existed;
none was reused, edited, or deleted. Each was closed in the registered
three-step order — `check_run_complete` → `append_manifest` →
`verify_manifest` — all of which passed for all four.

| H | Mode | Run ID | Wall | Cases | Aborted | Outcome as recorded |
|---|---|---|---|---|---|---|
| H1 | `corpus` | `RUN-20260923T134012Z-6b9d6b6-corpus-cpu` | 3.7 s | 504 | 0 | **19 cases breach the registered tolerance**; 485 pass |
| H3 | `repeatability` | `RUN-20260923T134226Z-6b9d6b6-repeatability-cpu` | <1 s | 14 | 0 | **14/14 bit-identical** |
| H2 | `fuzz` | `RUN-20260923T134250Z-6b9d6b6-fuzz-cpu` | 19 s | 1000 | 0 | **103 cases breach the within-horizon tolerance**; 897 pass; 657 cases carry beyond-horizon data |
| H4 | `kernel-path` | `RUN-20260923T134255Z-6b9d6b6-kernel-path-cuda` | 4.0 s | 72 | 0 | **72/72 within `rtol=1e-5, atol=1e-6`**; worst `max_abs_diff` 8.9775e-07 |

Exact commands are those in preregistration §5.3, with `--session 0156
--operator MichaelMaillet` and the H3 `--case-id` list above. H2 used
`--n-fuzz-cases 1000 --seed-counter 0 --seed-key 1`; the artefact's `config`
envelope records `fuzz_batch_class: "confirmatory"`,
`prinet_version: "3.0.0"`, and the reference source path.

**No case in any run aborted.** Every registered §4 abort criterion was
mechanically evaluated by the driver — NaN/Inf, `order_parameter` outside
`[0, 1]`, `mean_phase_coherence` outside `[-1, 1]`, phase-wrap range,
environment completeness, and (H4) CUDA device-residency of all three
derivative capsules — and none tripped. H4's `environment.backend` is
`cuda` with the RTX 4060 and 8188 MiB recorded, and its sidecar entry carries
the amendment-2 `timing_method: "not-timed"`. The §4 item 1 residual
boundary stands as registered: a clamp trip that leaves outputs finite and
in-range is not detectable by this driver.

## Observed conditions requiring adjudication or maintainer decision

E3 executes and records; it does not adjudicate (campaign plan §10.4 item 1
places detection at E4, and this brief prohibits interpreting results during
execution). The following are stated as recorded facts, with no diagnosis,
cause, or verdict attached.

### (1) H1 — 19 of 504 corpus cases outside the registered tolerance → candidate D1

Registered tolerances applied by `prin.parity.harness.compare_case`:
trajectories `rtol=1e-6, atol=1e-8` (corpus manifest), metrics
`rtol=2e-6, atol=1e-12` (`prin.parity.schema`). 504 non-aborted cases;
485 within tolerance; **19 outside**. Breaching arrays: `phase_traj` (15
cases), `mean_phase_coherence_traj` (8), `phase_final` (5). Concentration by
cell: `stuart_landau/full/euler` 10, `stuart_landau/full/rk4` 7,
`kuramoto/mean_field/euler` 1, `kuramoto/mean_field/rk4` 1. Breaches are
sparse within each array (1–4 failing elements out of 12–504) and small in
absolute terms: the largest `max_abs_diff` across the whole run is
**2.0086e-07**; the largest `max_rel_diff` is 1.2714e-03.

Under preregistration §8, H1's rule is `CONFIRMED` only if **all** non-aborted
cases are within tolerance and the non-aborted count is exactly 504. The
first clause is not satisfied. **E4 adjudicates; on the registered rule this
is a REFUTED/D1 trajectory, which campaign plan §10.4 routes to a correction
cycle rather than a publishable novelty.**

### (2) H2a — 103 of 1,000 fuzzed cases breach within the shadowing horizon → candidate D1

1,000 non-aborted cases; 897 within tolerance at steps `0..min(20, n_steps)`;
**103 outside**. Magnitude split of each breaching case's worst
`max_abs_diff`: 34 cases below 1e-6, 36 in `[1e-6, 1e-3)`, and **33 at or
above 1e-3**, the largest being 2.6549e+01. The large-magnitude cases are
not confined to one cell; breaches appear in 12 of the 14 combinations, most
often `stuart_landau/full/euler` (34), `kuramoto/mean_field/rk4` (12) and
`kuramoto/mean_field/euler` (10). Under §8, H2a is `CONFIRMED` only with no
within-horizon breach across all non-aborted cases; that is not satisfied.

**H2b was not adjudicated here** — §8 assigns it to
`exp001_driver.adjudicate_h2b` at E4. The raw material is present: 657
non-aborted cases carry `beyond_horizon` summaries, comfortably above the
registered minimum of 30 contributing cases per metric.

### (3) Registered budget cap exceeded → maintainer §14.2 decision required

Bytes written under `benchmarks/results/EXP-001/`:

| Run | Bytes | MiB |
|---|---|---|
| corpus-cpu | 1,725,249 | 1.645 |
| repeatability-cpu | 3,992 | 0.004 |
| **fuzz-cpu** | **4,402,765** | **4.199** |
| kernel-path-cuda | 76,865 | 0.073 |
| **Total** | **6,208,871** | **5.921** |

Two registered limits are exceeded:

- **Campaign plan §7.5 per-run cap** — "Raw JSON per run ≤ 2 MiB tracked".
  The fuzz run is 4.199 MiB, more than twice the cap.
- **Campaign plan §8 EXP-001 tracked-storage cap** — ≤ 5 MiB. The four runs
  total 5.921 MiB.

Campaign plan §10.1 item 5 registers "budget exceeded" as an **abort
criterion**, and §7.5 and §8 both state that exceeding a cap "requires a
§14.2 budget amendment". §7.5's in-plan remedy — move the large arrays to
the gitignored `DOCS/test_and_benchmark_results/EXP-001/` and record their
SHA-256 in a committed sidecar — cannot be applied inside E3, because
§12.1 forbids E3 from adding or modifying driver code ("a needed driver fix
at E3 is an abort → fix → new run ID, logged").

**Maintainer decision, 2026-09-23 UTC — campaign plan amendment 6 granted.**
MichaelMaillet raised EXP-001's §8 tracked cap from 5 MiB to **8 MiB** and
waived §7.5's 2 MiB per-run cap for this experiment's `fuzz` leg. All four
runs are committed as written, unmodified and unreduced. The §10.1 item 5
abort criterion is discharged by the amendment rather than by invalidating a
completed run, so **no run is aborted on budget grounds**. The campaign-wide
64 MiB cap is unchanged and far from binding. The fuzz artefact could not be
shrunk without changing the registered protocol: its per-case
`beyond_horizon` arrays are exactly what H2b's registered E4 analysis
consumes. No run directory was deleted, edited, or re-run.

## Artefact integrity — git EOL normalization defect found and fixed at commit time

Staging the four run directories surfaced a defect that would have made this
session's evidence unverifiable. The driver writes JSON through Python text
mode, so on Windows every result artefact carries CRLF; the repository's
`.gitattributes` began with `* text=auto eol=lf`, so git normalized those
artefacts to LF on commit. Measured, not inferred: the staged blob for
`corpus_corpus-cpu.json` was **1,667,489 bytes, sha256 `c6a13f5d…`**, while
its own `manifest.json` records **1,724,465 bytes, sha256 `882da36d…`**. Any
clean checkout — on Linux or Windows, since `eol=lf` forces LF in the working
tree — would therefore have read the artefact as *modified and resized*, and
`tools/reproduce.py::verify_manifest` would have failed closed on the
campaign's own raw evidence. Campaign plan §7.4's regeneration check ("a
clean checkout reproduces every output digest byte-for-byte") could not have
held.

**Fix:** one `.gitattributes` rule, `benchmarks/results/** -text`, disabling
EOL conversion for raw campaign evidence so the committed blob is exactly the
bytes that were measured. `-text` rather than `binary` keeps diffs visible,
which §7.3 relies on as a further immutable record. **No artefact was
rewritten, re-run, or re-manifested** — the bytes on disk are the bytes the
drivers produced at execution time, and the manifests are unchanged.

Verified after staging: for all four runs, every staged git blob matches its
manifest record in both size and SHA-256 (8/8 files). This is a repository
configuration fix, not a driver, protocol, hypothesis, tolerance, or run
change, so campaign plan §12.1's prohibition on E3 driver edits is not
engaged. No first-party source in a Snyk-supported language and no dependency
manifest changed in this session, so Coding Standards §6's Snyk Code, Snyk
Open Source, `cargo audit`, and `pip-audit` gates have no changed input to
scan here; CI remains the authoritative merge gate.

### Verified property of `check_run_complete` (recorded for E4/E5)

`check_run_complete` is a **closure-time** validator bound to the directory a
run was written into: it requires each result's `config.out_dir` to resolve to
the run directory being closed, and `out_dir` is recorded as an absolute path
at execution time. Re-running it against the same commit checked out at a
different path therefore raises `IncompleteRunError` by design, as observed
here from a clean worktree. That is not a defect and not an artefact
mutation. The **portable** integrity check is
`tools.reproduce.verify_manifest`, which passed for all four runs from a
fresh checkout of this session's commit, with every file matching its
manifest in both size and SHA-256. E4 and E5 should use `verify_manifest`
(campaign plan §7.4 step 1) rather than `check_run_complete` when validating
these inputs from any other location.

## Handoff

- The E3 exit gate's execution clauses are met: all four registered runs
  executed, none aborted, every run logged, and all four run directories
  closed with `check_run_complete` + `append_manifest` + `verify_manifest`
  passing. Raw artefacts and manifests are complete and immutable.
- **Both escalated conditions received a maintainer decision in-session
  (2026-09-23 UTC):**
  1. *Storage cap* — **campaign plan amendment 6** granted; EXP-001's tracked
     cap 5 → 8 MiB, §7.5 per-run cap waived for the `fuzz` leg, all four runs
     committed as written. Closed.
  2. *H1/H2a tolerance breaches* — **routed to E4 (session 0157)** exactly as
     campaign plan §10.4 item 1 prescribes: E3 records and escalates, E4
     applies the registered §8 decision rule and flags the D1. No correction
     cycle is opened by this session, and no root-cause claim is made here.
- No hypothesis was adjudicated in this session, no seed was re-drawn, no run
  was repeated to obtain a different outcome, no tolerance or protocol was
  changed, and no failing case was excluded. H2b's analysis and every
  hypothesis verdict belong to E4.
