# Session 0088 — WP-022 S4: Documentation — Trainable bands and resonance primitives

**Status:** COMPLETE  
**Roadmap phase:** 4 — Trainable stack and Torch bridge  
**Execution unit:** WP-022  
**Session type:** S4 — Documentation  
**Predecessor:** [0087 — Remediation](0087-wp022-s3-trainable-bands-and-resonance-primitives.md)  
**Successor:** [0089 — Coding](0089-wp023-s1-inhibition-activations-and-hep.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Implement Burn DiscreteDeltaThetaGamma, ResonanceLayer, parameter/state contracts, and differentiable forward references.

## Contract

- **Acceptance:** Forward and gradient reference tests pass; serialization, shape, dtype, and numerical guards are covered.
- **Non-goals:** Inhibition, HEP, optimizers, or full models.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/022-wp022-audit.md` including its CLEAN closure table
- Documentation Standards §7 and Versioning/Release Standards

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update the README of every directory touched in S1–S3.
2. Update `CHANGELOG.md`, rustdoc/docstrings, stubs, Sphinx API pages, examples,
   and the Migration Guide wherever behavior/public API changed.
3. Run documentation, example, link, quality, security, and relevant full-suite gates.
4. Write `DOCS/reports/022-project-state.md` with measured metric trends, cumulative deviation ledger,
   amendments, risks, and trajectory verdict.
5. Declare the next sequential WP from the Session Register; record maintainer approval before its S1 begins.
6. Update this session's status and the master register only from verified evidence.

## Required outputs

- Updated affected-directory READMEs and all relevant user/scientist docs.
- Changelog entry and warning-free docs/docstring coverage evidence.
- Approved Project State Report at `DOCS/reports/022-project-state.md`.
- Fully green CI; phase tag/release evidence when this closes a phase.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
hotfix/correction cycle; it is not silently repaired during documentation.

## S4.1 Post-commit security finding and hotfix

After the S4 documentation commit was pushed to `main`, the CI `rust` workflow
`audit` job discovered a new, ungoverned `h2` RUSTSEC-2026-0258 vulnerability
(low-severity DoS: unbounded empty DATA frames). The affected path is
`cubecl-cpu` → `tracel-llvm` → `tracel-mlir-rs` → `tracel-mlir-rs-macros` →
`tracel-llvm-bundler` → `reqwest` → `hyper` → `h2`, a build-time dependency of
the Burn/CubeCL stack introduced with WP-022.

Remediation (commit `1b7a8e9`): `cargo update -p h2 --precise 0.4.16` in
`Cargo.lock`; local re-verification (`cargo audit`, `cargo clippy` default and
`strict-checks`, `cargo doc`, `cargo test -p prin-train` default and
`strict-checks`, `cargo fmt`) is clean. Final CI re-verification (commit
`2fa9d0f`, `rust` workflow run `32169272050`, 2026-08-18): all 10 jobs green,
including `audit`. All other push-triggered workflows (`parity`, `snyk`,
`repro`, `python`; `gpu` skipped by design) are also green on the same commit.
The S4 exit gate is closed; this brief is `COMPLETE`.

## Exit gate

All S4 artefacts are committed and CI is green. The cycle is closed; only then
may the registered successor begin.
