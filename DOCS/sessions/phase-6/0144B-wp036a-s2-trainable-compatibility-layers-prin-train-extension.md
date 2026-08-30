---

# Session 0144B — WP-036A S2: Audit — Trainable compatibility layers (`prin-train` extension)

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036A
**Session type:** S2 — Audit
**Predecessor:** [0144A — Coding](0144A-wp036a-s1-trainable-compatibility-layers-prin-train-extension.md)
**Successor:** [0144C — Remediation](0144C-wp036a-s3-trainable-compatibility-layers-prin-train-extension.md)
**Authority:** Project Plan §6/§8 and amendment #33; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Read-only audit of WP-036A S1: the 13 trainable-layer Rust implementations,
PyO3 bindings, Python stub replacements, and gradcheck/parity evidence.

## Contract

- **Acceptance:** Audit report issued against A1–A10; every finding receives
  ID/severity/clause/remedy. Verdict: `PASS` / `PASS-WITH-FINDINGS` / `FAIL`.
- **Non-goals:** Source changes; remediation (that is S3).

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendments #31, #33
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The 0144A brief (WP-036A S1) and its acceptance criteria
- `DOCS/standards/Coding_Standards.md`, `Testing_Standards.md`
- `DOCS/reports/036-project-state.md` and the cumulative deviation ledger
- `DOCS/experiments/0141-wp036-s1-dd-dispositions.md` rows 31–44
- The 0144A S1 handoff note

## Entry conditions

- 0144A (WP-036A S1) is closed and committed; all S1 gates green.
- The S1 handoff note is complete and committed.

## Expected audit areas

1. **Scope conformance (A1):** all 13 symbols delivered as real implementations;
   no stubs remain; `verify_api_surface` still `(set(), set())`.
2. **Architecture conformance (A2):** all Rust code in `prin-train`; all PyO3
   bindings thin marshalling; no Python numerics; `#![deny(unsafe_code)]`
   unchanged in `prin-py`.
3. **Tests + coverage (A3):** gradcheck green for every trainable module;
   ≥95% coverage on new code; parity tests present.
4. **Numerical parity (A4):** forward-pass outputs match PRINet 3.0 reference
   within documented tolerance; `oscillatory_weight_init` matches reference
   initialization scheme.
5. **Quality gates (A5):** `cargo fmt`/`clippy`/`test`/`doc` clean;
   `ruff`/`mypy --strict`/`interrogate`/`bandit` pass.
6. **Security (A6):** `cargo audit`/`pip-audit`/`bandit` clean; no new deps
   without governance.
7. **Docstring/doc coverage (A7):** `interrogate` ≥95%; Sphinx clean.
8. **Repository hygiene (A8):** no `TODO`/`FIXME`; `__all__` discipline;
   `.pyi` stubs current.
9. **CI/regressions (A9):** all governance gates pass.
10. **Artefact trail (A10):** handoff note, Migration Guide updates, D-D
    appendix cross-references.

## Required outputs

- Audit report at `DOCS/audits/036a-wp036a-audit.md`.
- Finding list with ID/severity/clause/remedy for each issue.

## Exit gate

Audit report committed. Hand off to mandatory S3 remediation.
