# Changelog

All notable changes to PRIN are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial repository scaffold: Cargo workspace (8 crates), Python package layer,
  parity/benchmark/test/docs directories, CI workflow skeletons, and governance
  documents (`DOCS/`), per the official project plan
  (`DOCS/PRIN_Project_Plan.md`).
- Self-auditing execution methodology (plan amendment #1): Development Workflow
  and Audit Standards (Session Cycle S1 code → S2 audit → S3 remediate →
  S4 document, deviation ledger), Experimentation Standards (mandatory
  pre-registration with expected results and failure conditions, Phase 7
  campaign), artefact directories with templates (`DOCS/audits/`,
  `DOCS/reports/`, `DOCS/experiments/`), and operational session workflows
  (`.windsurf/workflows/`).
- Tightened quality gates: docstring coverage (ruff pydocstyle `D`/Google +
  `interrogate --fail-under 95`, rustdoc `-D warnings` CI job), Python SAST
  (`bandit`), and a dedicated security standard (Coding Standards §6).
- Complete prospective Session Execution Plan (`DOCS/sessions/`): 198
  individually addressable session briefs spanning 39 governed work packages,
  eight E1–E5 pre-registered experiments, campaign planning/synthesis, and
  stable-release closure; includes a master status register, requirement/risk/
  DoD traceability matrix, phase indexes, and conditional D1/D2 correction
  templates (plan amendment #2).

### Fixed

- Parity CI workflow: added empty-corpus guard so the job is skipped until
  `parity/` cases exist (pre-WP-001 fix).
- `Cargo.lock`: now tracked for reproducible CI dependency resolution
  (pre-WP-001 fix).
- Python test scaffold: added a minimal collection smoke test so an empty suite
  does not fail the `pytest` gate with exit code 5 (pre-WP-001 fix).
- Scaffold gate pass: confirmed all quality gates green at `v0.1.0` scaffold
  state (pre-WP-001 fix).
