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
