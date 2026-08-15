# PRIN Executive Mathematical Audit Governance and Methodology

**Status:** Normative. This document establishes the governance, scope, tooling,
methodology, findings classification, remediation protocols, and reporting
requirements for **Executive Mathematical Audit (EMA) Sessions** in the PRIN
project.

**Relationship to existing governance:** This document extends — and never
overrides — the [Executive Audit Governance and Methodology](Executive_Audit_Governance_and_Methodology.md),
[Development Workflow and Audit Standards](Development_Workflow_and_Audit_Standards.md),
[Coding Standards](Coding_Standards.md), [Testing Standards](Testing_Standards.md),
[Benchmarking and Reproducibility Standards](Benchmarking_and_Reproducibility_Standards.md),
and [Official Project Plan](../PRIN_Project_Plan.md). It is registered by Project
Plan amendment #23 (§8.3), following the same "global session, outside the
planned sequence" registration precedent established for Executive Audit (EA)
sessions by amendment #15.

---

## 1. Purpose and Scope

An **Executive Audit Session** (EA, governed by
`Executive_Audit_Governance_and_Methodology.md`) verifies dimension **E1
(Mathematical & Oscillator Dynamics Core)** primarily by direct source
inspection: an auditor reads the Rust implementation, compares it to the
documented formula, and reasons about correctness. This is necessary but has a
structural limitation the EA methodology itself has already surfaced twice
(EA-003 finding E-F5: a test suite that claimed "parity" verified only
internal invariants, not an independent reference; EA-002/EA-003's own
`docs/audit-methodology.md`-style principle that "an agent's own confidence,
test output, or explanation is never itself evidence" applies equally to an
*auditing* agent's unaided prose derivation).

An **Executive Mathematical Audit (EMA) Session** closes that gap. It is a
project-level audit dedicated to **independent, tool-executed recomputation**
of PRIN's mathematical claims — using `math-audit-mcp`, a local-first audit
tool that never reads or trusts the target code's own reasoning and instead
re-derives, re-integrates, re-contracts, or re-proves each claim from scratch
with SymPy, SciPy, mpmath, Z3, and NetworkX (optionally Lean 4 / Wolfram
Engine). EMA sessions:

1. Audit the mathematical content of dimension **E1** (and any E3/E8 claims
   that are themselves mathematical propositions, e.g. convergence order,
   parity-tolerance derivations) with a second, independent evidentiary
   channel that EA sessions do not have.
2. Produce durable, hashed, machine-checkable evidence (an `AuditResult` per
   claim, an evidence bundle per session) that is stronger than a prose audit
   finding: a symbolic proof, a Z3 model or refutation, or a scoped numeric
   comparison against a reference solver.
3. **Do not replace** EA sessions' E1 review, the parity corpus
   (`parity/corpus/`), or the Rust/Python test suites. EMA is an additional,
   independent verification layer over a curated set of **claims** — formal
   restatements of specific mathematical properties PRIN's code is supposed to
   have — not a replacement for executing PRIN's own code or its own tests.

## 2. Tooling

### 2.1 The audit tool

`math-audit-mcp` (installed at `C:\dev\--DEV\Math Audit MCP` on the
maintainer's workstation, `pyproject.toml` version `0.1.0`) is an external,
local-first MCP server. It is **not vendored into this repository**: PRIN owns
only its own policy configuration, claim ledgers, and evidence — the same
separation of concerns already used for Snyk, `cargo-audit`, and `pip-audit`
(Coding Standards §6), none of which are vendored either.

**Provenance caveat (recorded, not remediated by this session):** the
`math-audit-mcp` source tree has no git history of its own (`git -C
"<tool path>" rev-parse HEAD` fails — not a git repository). There is
therefore no commit hash to cite as the audited tool version. EMA sessions
compensate by recording, as evidence, the installed package version
(`pip show math-audit-mcp`), the resolved dependency versions (SymPy, SciPy,
Z3, NetworkX, mpmath), and a SHA-256 content hash of the `src/math_audit_mcp/`
tree at audit time (§6). Vendoring the tool as a pinned git submodule or a
version-pinned PyPI dependency is logged as a pass-forward item (§7).

### 2.2 PRIN-side integration artifacts

Everything PRIN owns for this workflow lives under version control in this
repository:

| Path | Purpose |
|---|---|
| `tools/math_audit_policy.yaml` | PRIN's policy profile for `math-audit-mcp` (derived from the tool's bundled `strict` profile; see §3). |
| `tools/math_audit_claims/*.json` | Claim ledgers: PRIN's own formal restatements of specific mathematical properties, one ledger per audited subsystem. These are authored by a human or an authoring agent and audited independently — never self-graded. |
| `tools/math_audit_run.py` | Runner: locates the `math-audit-mcp` installation via `MATH_AUDIT_MCP_HOME`, loads `tools/math_audit_policy.yaml`, runs every ledger under `tools/math_audit_claims/` through `audit_claim_ledger`, aggregates verdicts, and writes a consolidated gate report. |
| `EVIDENCE/math-audit/` | `MATH_AUDIT_OUTPUT_ROOT` — every `AuditResult`, evidence bundle, and the append-only `audit-trace.jsonl` produced against this repository. Evidence is append-only, per `math-audit-mcp`'s own architecture (never overwritten by a later run). |

### 2.3 IDE-agent (MCP client) configuration

For interactive use inside an MCP-compatible IDE agent session (not required
for the batch `tools/math_audit_run.py` gate), the following server entry is
the reference configuration; it is not committed as a live `.mcp.json` in this
repository because the tool's absolute path is workstation-specific:

```json
{
  "mcpServers": {
    "math-audit": {
      "command": "C:\\dev\\--DEV\\Math Audit MCP\\.venv\\Scripts\\python.exe",
      "args": ["-m", "math_audit_mcp"],
      "env": {
        "MATH_AUDIT_POLICY_PATH": "C:\\dev\\PRIN\\tools\\math_audit_policy.yaml",
        "MATH_AUDIT_ALLOWED_ROOTS": "C:\\dev\\PRIN",
        "MATH_AUDIT_OUTPUT_ROOT": "C:\\dev\\PRIN\\EVIDENCE\\math-audit"
      }
    }
  }
}
```

## 3. Policy profile

`tools/math_audit_policy.yaml` is derived from the bundled `strict` profile
(`config/strict-policy.yaml` in the tool's own repository), not `default` or
`development`, because EMA verdicts feed governance findings (D1–D4) with the
same evidentiary weight as an EA finding:

- `tool_error_treatment: fail`, `inconclusive_treatment: fail` — an
  inconclusive or erroring required check is never treated as passing
  evidence for a PRIN mathematical claim.
- `allow_probabilistic_numeric_pass: false` — numeric sampling agreement alone
  never satisfies a claim under this policy; only symbolic/formal proof
  (SymPy reduction to zero, Z3 unsat) or `audit_ode`'s scoped
  reference-solver/tolerance comparison (which is not "probabilistic
  sampling," it is deterministic re-integration) counts.
- `high_severity_requires_symbolic_or_formal: true` — a `high`/`critical`
  severity claim (anything touching the core oscillator ODE, order-parameter
  bounds, or a numerical-hazard clamp from Project Plan §5) requires at least
  one required check's `PASS` to come from SymPy or Z3, never numeric-only
  agreement.
- `severities_requiring_crosscheck: [medium, high, critical]` — broadened from
  the upstream strict default (`[high, critical]`... the upstream `strict`
  profile already sets `[medium, high, critical]`, so this is inherited
  unchanged) to keep the highest evidentiary bar available for PRIN's
  numerical-hazard-heavy core.
- `repository.allowed_roots: ["C:\\dev\\PRIN"]`, `repository.output_root`
  resolved to `EVIDENCE/math-audit` at runtime by `tools/math_audit_run.py`
  (absolute path, set via `MATH_AUDIT_OUTPUT_ROOT`, never inside
  `allowed_roots`' own source tree per the tool's own security model).
- Optional adapters (`lean`, `wolfram`) remain disabled by default, matching
  Project Plan §4/§8: no new external toolchain dependency is introduced
  without a separate plan amendment. A claim that would otherwise want Lean
  escalation is instead scoped to what SymPy/Z3/SciPy can decide, and any
  residual gap is recorded as `INCONCLUSIVE` → a D3 finding, not silently
  dropped.

## 4. Claim taxonomy — mapping PRIN mathematics to `math-audit-mcp` claim types

| PRIN subsystem | Representative claim | `claim_type` | Tool |
|---|---|---|---|
| `prin-metrics::order` (Kuramoto order parameter) | Magnitude of the complex order parameter is bounded in `[0, 1]` for any phase configuration | `z3_invariant` | `check_constraint_model` (Z3) |
| `prin-dynamics::coupling` / model RHS trig identities | Coupling-term algebraic identities (e.g. sum-of-sines reductions used in the Kuramoto RHS) | `symbolic_identity` | `verify_identity` (SymPy) |
| `prin-dynamics::integrate` (Euler, RK4) | Local truncation order and linear-stability-region behavior on the scalar test equation `y' = λy` | `ode_property` / `numerical_convergence` | `audit_ode` (SciPy reference) |
| `prin-dynamics::state` (phase wrap `% 2π`, amplitude clamp `[1e-6, 10]`, derivative clamp `±1e4`) | The stated clamp/wrap guard holds for every real input, not just tested samples | `z3_invariant` | `check_constraint_model` (Z3) |
| `prin-tensor::tucker` (HOSVD) | Reconstruction/orthonormality-type contraction identities on a concrete small tensor | `tensor_contract` | `audit_tensor_contract` (NumPy einsum vs. supplied sample values) |
| `prin-dynamics::coupling` (ring/topology construction) | A constructed coupling topology has the declared graph-theoretic shape (e.g. every node at the declared degree, single connected component) | `graph_topology` | `audit_graph_topology` (NetworkX) |

Each claim in `tools/math_audit_claims/*.json` cites the exact `code_refs`
(`file:line-range`) of the PRIN source it restates. **The claim's `assumptions`
are an independent restatement, never a copy of the implementation's own
comments or docstring** — per `docs/audit-methodology.md`'s "independent
recomputation" principle, a claim ledger that merely echoes the code under
test would defeat the purpose of the audit.

## 5. Severity classification

EMA findings use the same D1–D4 scale as Executive Audits
(`Executive_Audit_Governance_and_Methodology.md` §3), mapped from
`math-audit-mcp`'s six-status result vocabulary
(`docs/audit-methodology.md` in the tool's repository):

| Tool status on a required check | PRIN severity | Rationale |
|---|---|---|
| `FAIL` | **D1 — Trajectory Breach** | A concrete counterexample or violated property was found — this is definitive evidence the mathematical claim, as stated, is false. Freezes progress on the affected subsystem per EA governance §3. |
| `REQUIRES_HUMAN_REVIEW` | **D2 — Subsystem Deviation** | Contradictory independent results, a missing required tool result, or evidence strength below policy's bar for the claim's severity — the claim cannot be trusted as-is and needs a human (or a follow-up S3) to resolve the ambiguity. |
| `TOOL_ERROR` | **D2 or D3** (D2 if it masks an unverified high/critical claim; D3 otherwise) | The independent check itself could not execute — never conflated with a mathematical finding, but a gap in coverage that must be closed or explicitly deferred. |
| `INCONCLUSIVE` | **D3 — Process / Quality Deviation** | Neither proof nor counterexample was obtained — a genuine evidentiary gap in the audit's coverage, not a defect finding against the code. |
| `SKIPPED_BY_POLICY` (optional adapter disabled) on a claim that did not require it | **D4 — Hygiene** | Documented, policy-conformant skip; recorded for completeness. |
| `SKIPPED_BY_POLICY` on a claim whose severity needed the escalation | **D3** | The claim's severity warranted Lean/Wolfram escalation that policy left disabled; logged as a scoping gap, not silently dropped. |
| `PASS` | No finding | Independent, tool-executed evidence supports the claim as stated. |

A claim ledger's **overall ledger status** (`resolve_ledger_status`: any
`FAIL` wins, then `REQUIRES_HUMAN_REVIEW`, then `TOOL_ERROR`, then
`INCONCLUSIVE`, else `PASS`) determines the EMA report's per-subsystem summary
row, but every individual claim's status is still recorded as its own
finding — a ledger-level `PASS` with one `INCONCLUSIVE` claim inside it is
still a D3 finding for that specific claim.

## 6. Evidence and reproducibility

1. Every `audit_claim_ledger` run persists a normalized request, a normalized
   result, and (for claim-ledger runs) a complete evidence bundle
   (`manifest.json`, `report.md`, hashed artifacts) under
   `EVIDENCE/math-audit/audits/<audit_id>/` and
   `EVIDENCE/math-audit/bundles/<bundle_id>/` respectively — append-only,
   never overwritten by a later run (§2.2).
2. Each `AuditResult` records the active policy's `policy_snapshot_hash`
   (a SHA-256 over the full policy document), so it is always possible to
   tell exactly which policy produced a given verdict.
3. The EMA report (§7) additionally records the tool provenance fingerprint
   from §2.1 (installed version + dependency versions + source-tree hash),
   since no git commit hash is available.
4. `EVIDENCE/math-audit/` artifacts are committed alongside the EMA report,
   following the same evidence-chain rule as `EVIDENCE/README.md` (S2 audit
   reproductions may write fresh evidence with a new timestamp; the original
   baseline is never silently replaced).

## 7. Executive Mathematical Audit Workflow Lifecycle

An EMA Session proceeds through 7 mandatory sequential tasks, mirroring the EA
lifecycle (`Executive_Audit_Governance_and_Methodology.md` §4) with
math-audit-mcp-specific substance:

```
Task 1: Tool Setup & Governance/Methodology Definition (this document)
   │
   ▼
Task 2: Claim Ledger Authoring (independent restatement of E1 mathematics)
   │
   ▼
Task 3: Independent Audit Execution (audit_claim_ledger over every ledger)
   │
   ▼
Task 4: Executive Mathematical Audit Report Compilation
   │
   ▼
Task 5: Remediation Planning (Immediate vs Pass-Forward)
   │
   ▼
Task 6: Remediation Execution & Re-audit of Touched Claims
   │
   ▼
Task 7: Final Documentation, Session Register/Traceability, Git Commit
```

**Governance principles** (identical intent to EA §2, restated for the
independent-recomputation context):

1. **Independent recomputation only.** A claim's `PASS` must come from
   `math-audit-mcp` actually re-deriving/re-integrating/re-proving it — never
   from citing the target code's own tests, comments, or an EA session's
   prose review as if it were independent evidence.
2. **Counterexample-first.** A `FAIL` is definitive; it is never downgraded
   without either a fix or a formally approved plan amendment explaining why
   the claim, as originally stated, was mis-scoped (mirroring EA §2.2's
   "any divergence... is classified as a deviation").
3. **No silent gaps.** `INCONCLUSIVE`/`TOOL_ERROR`/`SKIPPED_BY_POLICY` are
   always recorded as findings (§5), never treated as passing evidence and
   never omitted from the report.
4. **Clean verification gate.** An EMA session cannot close until every D1/D2
   finding is `FIXED` or `AMENDED`, matching EA §2.5 and Development Workflow
   Standards §1's "deviations never accumulate" principle.

## 8. Reporting and Artifact Rules

1. **Executive Mathematical Audit Report:** saved as
   `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_NNN.md` using
   `DOCS/audits/TEMPLATE_Executive_Math_Audit_Report.md`. Findings use the
   `M-FN` identifier prefix (distinct from EA's `E-FN`) to keep the two audit
   types' finding histories independently traceable.
2. **Session registration:** EMA sessions are global sessions, registered in
   `DOCS/sessions/SESSION_REGISTER.md` under a dedicated "Global sessions —
   Executive Mathematical Audits" section, outside the planned 0001–0198
   sequence, following the identical precedent plan amendment #15 established
   for EA sessions (`EMA-NNN` identifiers, never renumbering planned
   sessions).
3. **Remediation plan:** embedded in the EMA report or saved alongside it if
   extensive, identical convention to EA §5.2.
4. **Project State Report:** cross-referenced or updated to reflect EMA
   conclusions, identical convention to EA §5.4.
5. **Recurrence:** an EMA session is warranted whenever `prin-dynamics`,
   `prin-metrics`, or `prin-tensor` gains new mathematical content (new
   model, integrator, metric, or decomposition), and at minimum once per
   Executive Audit cycle thereafter, so the two audit types' cadences stay
   aligned without one silently lapsing.
