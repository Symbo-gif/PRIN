# PRIN Project Intelligence

## Repository authority

Before editing, read the active session brief, `DOCS/PRIN_Project_Plan.md`, the
applicable files in `DOCS/standards/`, the latest Project State Report and
deviation ledger, and any governing audit. Verify implementation facts from the
repository; do not invent commands, APIs, paths, configuration, or evidence.

The material under `DOCS/archive/` is historical and non-authoritative. Do not
regenerate or consult retired `.vibecheck` state as a source of current truth.

## Secure development

Follow Coding Standards §6, including these mandatory controls:

1. Run Snyk Code for new or modified first-party code in supported languages.
2. Run Snyk Open Source for supported dependency changes, plus every applicable
   ecosystem-native audit (`cargo audit`, `pip-audit`, and the existing gates).
3. Remediate findings attributable to the change and rescan until clean at the
   governed threshold. Do not suppress or exclude findings without approved,
   evidence-backed governance.
4. Treat GitHub secret scanning and push protection as independent mandatory
   controls; Snyk does not replace them.
5. If Snyk is unavailable, report the validation as blocked and do not claim it
   passed. CI is the authoritative merge gate.

Use the repository skill `snyk-secure-development` when its workflow applies.
Do not emit unverifiable safety badges; cite actual command or scan evidence.

---

<!-- vibe-flow:start -->
# Vibe Flow — Workflow Guide

Use `/vibe-help` anytime for context-aware guidance on what to do next.

## Analysis

- **`CB`** Create Product Brief — A guided experience to nail down your product idea into an executive brief *(Radar)*
- **`MR`** Market Research — Market analysis, competitive landscape, customer needs and trends *(Radar)*
- **`DR`** Domain Research — Industry domain deep dive, subject matter expertise and terminology *(Radar)*
- **`TR`** Technical Research — Technical feasibility, architecture options and implementation approaches *(Radar)*

## Planning

- **`CP`** Create PRD — Expert led facilitation to produce your Product Requirements Document *(Rhythm)*
- **`VP`** Validate PRD — Validate a Product Requirements Document is comprehensive, lean, well organized and cohesive *(Rhythm)*
- **`EP`** Edit PRD — Update an existing Product Requirements Document *(Rhythm)*
- **`CU`** Create UX Design — Guidance through realizing the plan for your UX to inform architecture and implementation *(Prism)*

## Architecture

- **`CA`** Create Architecture — Guided workflow to document technical decisions to keep implementation on track *(Blueprint)*
- **`CE`** Create Epics & Stories — Create the Epics and Stories Listing — the specs that will drive development *(Rhythm)*
- **`IR`** Implementation Readiness — Ensure the PRD, UX, Architecture, and Epics/Stories are all aligned *(Blueprint)*

## Implementation

- **`DS`** Dev Story — Write the next or specified story's tests and code *(Pulse)*
- **`CR`** Code Review — Comprehensive code review across multiple quality facets *(Pulse)*
- **`SP`** Sprint Planning — Generate or update the record that sequences tasks for the full project *(Tempo)*
- **`CS`** Context Story — Prepare a story with all required context for implementation *(Tempo)*
- **`ER`** Epic Retrospective — Multi-agent review of all work completed across an epic *(Tempo)*
- **`CC`** Course Correction — Determine how to proceed if major need for change is discovered mid implementation *(Tempo)*
- **`SS`** Sprint Status — Review and update sprint progress *(Tempo)*
- **`QA`** Generate Tests — Generate API and E2E tests for existing features *(Signal)*

## Quick Flow

- **`QS`** Quick Spec — Architect a quick but complete technical spec with implementation-ready stories *(Dash)*
- **`QD`** Quick Dev — Implement a story tech spec end-to-end (core of Quick Flow) *(Dash)*
- **`QQ`** Quick Dev New — Unified quick flow — clarify intent, plan, implement, review, present *(Dash)*

## Utility

- **`BP`** Brainstorm — Expert guided facilitation through single or multiple brainstorming techniques *(Radar)*
- **`DP`** Document Project — Analyze an existing project to produce useful documentation for both human and LLM *(Echo)*
- **`GC`** Generate Project Context — Analyze the project and produce a context document for AI agents *(Echo)*
- **`SM`** Squad Mode — Bring multiple agent personas into one session to collaborate and discuss *(Maestro)*

<!-- vibe-flow:end -->
