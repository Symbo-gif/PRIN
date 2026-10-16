# Claude Code Agents — Orchestrator

You are the orchestrator. Use the specialized agents in `.claude/agents/` for
focused audits, planning, fixes, tests, and release checks. Run independent
auditors in parallel and fixes in sequence. Do not treat generated agent output
as completion evidence until it is verified against the repository gates.

## Mandatory repository protocol

Before editing, read the active session brief, `DOCS/PRIN_Project_Plan.md`, the
applicable standards, latest Project State Report and deviation ledger, and any
governing audit. Repository code and configuration—not archived or generated
claims—are the source of implementation facts.

Follow Coding Standards §6. Run Snyk Code on new or modified supported source;
run Snyk Open Source and the ecosystem-native audits for dependency changes;
fix findings attributable to the change and rescan. Snyk is additive and does
not replace `cargo audit`, `pip-audit`, GitHub secret scanning, or push
protection. Never claim a scan passed when it was unavailable or not run.

## Local-validation regime (Plan amendment #48)

Hosted GitHub Actions check workflows are disabled until the maintainer says
otherwise. Run every gate locally on this Windows device, record verbatim
commands/exit codes/SHA as evidence, and never describe local results as "CI
green". Do not test or claim Linux/macOS behaviour. Do not re-enable workflows,
restore required checks, or push `v*` tags unless the maintainer instructs it.
See Development Workflow and Audit Standards §3 "Local-validation regime".
Exception: Plan amendment #52 (2026-10-16) re-enables the seven check workflows
and keeps them active until the campaign's experimentation is complete (the
close of session `0194`, or earlier on maintainer instruction), superseding
amendment #50's EXP-002-only window (sessions 0159–0163). Record each hosted
result verbatim (workflow, run ID, head SHA, conclusion, link) as additional
evidence for the exact SHA it ran on, keep the local gate mandatory and
authoritative, never call a local result "CI green", and never claim behaviour
on a platform a hosted run did not exercise. Triage and record a red hosted
check; never waive, skip, deselect or hide one by editing a workflow or removing
a required check. The ruleset's required-status-check rule stays removed, and
disabling the workflows again at the end condition is recorded.

`DOCS/archive/` is historical and non-authoritative. Do not use retired
VibeCheck state as current project truth and do not emit safety badges without
real evidence.
