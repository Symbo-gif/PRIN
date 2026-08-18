---
description: S1 Coding session — implement the declared WP with tests in tandem
---

Authoritative definition: `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §3 (S1).

1. Read `DOCS/sessions/SESSION_REGISTER.md`, the active numbered S1 brief,
   and the latest `DOCS/reports/NNN-project-state.md`; confirm the predecessor
   is closed and the WP scope/acceptance/non-goals have approval. Stop if the
   brief and state report disagree.
2. Read the plan sections the WP advances (`DOCS/PRIN_Project_Plan.md`) and
   the standards relevant to the touched layers.
3. State the global session ID, type S1, WP ID, and brief outputs before
   writing code.
4. Implement strictly within WP scope. For each unit of behavior: write the
   code AND its tests in the same commit (unit, property, parity, gradcheck,
   kernel-equivalence as applicable — Testing Standards §2). Docstrings and
   security rules apply at write time.
5. Log out-of-scope discoveries in the session log section of the next Project
   State Report draft — do not implement them.
6. Before ending, run the full local gate:
// turbo
7. `cargo fmt --all -- --check; cargo clippy --workspace --all-targets -- -D warnings; cargo test --workspace`
8. `ruff check python/ tests/ benchmarks/ tools/; mypy python/prin --strict; interrogate -c pyproject.toml python/prin; bandit -r python/prin -c pyproject.toml; pytest tests/ -v -m "not slow and not gpu"`
9. Commit with Conventional Commits referencing the WP
   (`feat(WP-012): sparse k-NN coupling with parity cases`). **Commit only —
   do not push.** Per the Push and CI cadence (Development Workflow and Audit
   Standards §3, Plan amendment #28), only the S4 commit that closes this
   cycle pushes to `origin/main`; CI does not run per session.
10. Confirm the active brief's S1 exit gate (local gate green, coverage ≥95%
    on new code, acceptance evidence mapped) and hand off only to its listed
    S2 successor via `/audit-session`.
