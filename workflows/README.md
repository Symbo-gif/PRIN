# workflows/ — agent orchestration recipes

Compact recipes that sequence specialized agents for common development tasks.
They supplement but do not replace the PRIN Session Cycle
(see [Development Workflow Standards](../DOCS/standards/Development_Workflow_and_Audit_Standards.md)).

## Available Workflows

| Workflow | Purpose | When to use |
|---|---|---|
| [`bug-fix.md`](bug-fix.md) | Write failing test → fix → verify | Bug reports, regression fixes |
| [`new-feature.md`](new-feature.md) | Test-first feature development | New functionality, enhancements |
| [`pre-commit.md`](pre-commit.md) | Quick code + test check | Before committing changes |
| [`pre-deploy.md`](pre-deploy.md) | Deploy readiness check | Before deployment |
| [`executive-audit.md`](executive-audit.md) | 7-step executive audit lifecycle | Phase boundaries, quality gates |
| [`full-audit.md`](full-audit.md) | 11 parallel auditors + fix planner | Comprehensive quality assessment |
| [`release-prep.md`](release-prep.md) | Full audit → fixes → deploy → PR | Release preparation |

## Evidence Policy

Use repository tests, security scans, Audit Reports, Project State Reports, and
hosted CI — not agent summaries — as completion evidence.
