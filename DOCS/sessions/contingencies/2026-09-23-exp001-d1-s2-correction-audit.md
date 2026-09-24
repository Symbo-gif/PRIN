# EXP-001 D1 S2 — Correction audit

**Status:** OPEN — blocked on S1\
**Triggering deviation:** `EXP-001 H1/H2a REFUTED` (campaign plan §10.4 D1) and
`EXP001-E5-F1` (D1)\
**Blocked numbered session:** `0159`\
**Opened by:** session `0158` (EXP-001 E5), 2026-09-23 UTC\
**Predecessor:** [S1 — correction implementation](2026-09-23-exp001-d1-s1-correction-implementation.md)

## Expectation

Read-only audit of the correction against A1–A10, the triggering experiment
evidence, and the violated requirement; issue findings and verdict.

## Exit evidence

Record commands, artefacts, approvals, commits, and handoff in the correction
WP's audit and Project State Report. The blocked session remains blocked until
all four conditional sessions close.

## Audit scope specific to this correction

Beyond the standard checklist, the audit independently verifies:

1. **The reproduction came first.** The failing tests S1 cites existed and
   failed on the pre-fix tree; the auditor re-runs them there rather than
   accepting the claim.
2. **The root cause is established, not asserted.** If S1 concluded that the
   PRINet 3.0 side is defective (campaign plan §10.4 item 3), the audit
   verifies the EMA-style mathematical claim and its Z3/SymPy verification
   directly; an inspection argument is not sufficient.
3. **The fix covers both failure populations.** H1's `1e-10`…`1e-7` tail and
   H2a's ≥`1e-3` population (33 cases, max `2.654853e+01`) are not assumed to
   share a mechanism. Whether one fix closes both is a finding, not a
   premise.
4. **`EXP001-E5-F1` is genuinely closed.** The new parity gate must fail on
   the pre-fix tree — a gate that passes both before and after proves
   nothing. The auditor reproduces that red/green transition.
5. **EXP-001's record is untouched.** No file under
   `DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/` or
   `benchmarks/results/EXP-001/` changed; `verify_manifest` still passes on
   all four run directories and the E4 digests still reproduce.
6. **Coding Standards §6 evidence is real.** Snyk Code / Open Source and the
   ecosystem-native audits were run on the changed inputs, or the validation
   is reported as blocked — never claimed.

## Verdict rule

`PASS` (no findings above D4), `PASS-WITH-FINDINGS` (none D1), or `FAIL` (any
D1, or systemic drift). A `FAIL` sends every finding to S3; no fix is
committed during this session.
