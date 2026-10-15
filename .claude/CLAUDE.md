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
Exception: Plan amendment #50 (2026-10-11) re-enables the seven workflows for
the EXP-002 experiments only (sessions 0159–0163). Record hosted results
verbatim as additional evidence, keep the local gate authoritative, and disable
the workflows again when EXP-002 E5 closes or the maintainer says so.

`DOCS/archive/` is historical and non-authoritative. Do not use retired
VibeCheck state as current project truth and do not emit safety badges without
real evidence.
