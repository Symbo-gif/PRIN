Pre-registration freeze: NOT STARTED — no `RUN-` directory has been created.

# EXP-001 — Session 0156 E3 execution log

**Status:** BLOCKED AT PREFLIGHT — E3 execution has not begun.
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
