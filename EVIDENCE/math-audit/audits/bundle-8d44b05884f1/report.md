# Audit Evidence Report: bundle-8d44b05884f1

**Overall status:** `REQUIRES_HUMAN_REVIEW`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T20:00:28.015Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### TEN-01 -- `REQUIRES_HUMAN_REVIEW`

- **Type:** `tensor_contract`  
- **Severity:** `high`  
- **Statement:** build_ring's weighted coupling matrix for N=6, k_ring=4, K=1.0 (each node connected to its +-1 and +-2 neighbours mod N, weight K/k_ring=0.25) is symmetric, as required for the undirected coupling topologies coupling.rs documents (Note: audit_tensor_contract only verifies shape/contraction compatibility and symmetry against these literal sample_values -- it does not execute coupling.rs itself.)  
- **Code references:** crates/prin-dynamics/src/coupling.rs:222-263, crates/prin-dynamics/src/coupling.rs:203-220  
- **Reason:** high/critical-severity claim passed only numerically; policy requires symbolic or formal (SymPy/Z3/Lean) corroboration before a PASS verdict  
- **Contributing audits:** audit-c95f8785de54

### TEN-02 -- `PASS`

- **Type:** `tensor_contract`  
- **Severity:** `medium`  
- **Statement:** build_all_to_all's weighted coupling matrix for N=4, K=1.0 (weight K/N=0.25 off-diagonal, zero diagonal, per coupling.rs:193-201) is symmetric, an independent second confirmation across topologies that the coupling term sum_j W_ij*sin(phi_j-phi_i) uses an undirected weight matrix.  
- **Code references:** crates/prin-dynamics/src/coupling.rs:193-201  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-8db2c788f3f9

### TEN-01-LEAN -- `PASS`

- **Type:** `lean_theorem`  
- **Severity:** `high`  
- **Statement:** Formal (Lean 4 kernel-checked `decide`) corroboration of TEN-01: build_ring(N=6, k_ring=4, K=1.0)'s weighted coupling matrix (literal sample_values from the TEN-01 claim, represented as an exact 4x integer scaling to keep decide inside kernel-reducible Nat arithmetic) is symmetric. EMA-001 M-F3: added to let this high-severity tensor_contract claim earn genuine symbolic/formal corroboration (policy.verdict_rules.high_severity_requires_symbolic_or_formal) via a third independent channel (Lean's kernel) alongside TEN-01's own NumPy-einsum evidence, rather than relying on human sign-off alone.  
- **Code references:** crates/prin-dynamics/src/coupling.rs:222-263, crates/prin-dynamics/src/coupling.rs:203-220  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-ead19d5da00e

## Tool invocations

### audit_tensor_contract (`audit-c95f8785de54`) -- `PASS`

- **Adapter:** `none`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Contraction compatibility, output signature, and 1 symmetry claim(s) all checked out.

**Reasoning:** Validated 0 contraction pair(s) across 1 shape trial(s); output rank matched output_signature. Symmetry checks: W.symmetric['i', 'j']: held on provided sample_values.

**Limitations:**
- Contraction/output-signature checks without sample_values use synthetic random trial tensors (they validate shape/einsum plumbing, not real code output).
- The `expression` field is documentation only and was not evaluated.

**Metrics:**
- contraction_trials_executed: 1.0

- **Random seed:** 0
- **Input content hash:** `sha256:82660d254947b7672735487334e29f28972ce7f79b4623f334b089bc44ca7194`
- **Output content hash:** `sha256:115b2b59d673302d1932e07ea0c5f6ae20da72d0b7d25f80baaf8a31c87b5b11`

### audit_tensor_contract (`audit-8db2c788f3f9`) -- `PASS`

- **Adapter:** `none`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Contraction compatibility, output signature, and 1 symmetry claim(s) all checked out.

**Reasoning:** Validated 0 contraction pair(s) across 1 shape trial(s); output rank matched output_signature. Symmetry checks: W.symmetric['i', 'j']: held on provided sample_values.

**Limitations:**
- Contraction/output-signature checks without sample_values use synthetic random trial tensors (they validate shape/einsum plumbing, not real code output).
- The `expression` field is documentation only and was not evaluated.

**Metrics:**
- contraction_trials_executed: 1.0

- **Random seed:** 0
- **Input content hash:** `sha256:352661aa9c593cb8dd9ab81ad0c7e7a0d16d05d0246d4fbbaab5bb99f7d6d3f6`
- **Output content hash:** `sha256:a31ef4398942c2df82e6c836648fcb6e71dfce08fe1220eadd6040e7b05869e0`

### verify_lean_claim (`audit-ead19d5da00e`) -- `PASS`

- **Adapter:** `lean`
- **Severity:** `high`
- **Duration:** 4419 ms
- **Summary:** Lean elaborated successfully; expected_outcome='proves'.

**Reasoning:** Ran `C:\Users\there\.elan\bin\lean.EXE C:\dev\PRIN\EVIDENCE\math-audit\scratch\lean\tmp_vr33eh6.lean`. Elaboration succeeded. See lean-diagnostics.txt artifact for full sanitized output.

**Limitations:**
- This adapter drives the Lean CLI and inspects exit status/diagnostics; it does not perform interactive elaboration introspection (a Lean LSP bridge is a documented future extension).

**Artifacts:**
- [Sanitized Lean/lake stdout+stderr](artifacts/lean-diagnostics.txt) (`sha256:84da06236f0c97f2cfd68a5cda16b034efef4ea68db088fbe7a932e851045e30`)

- **Random seed:** n/a
- **Input content hash:** `sha256:f31248f3a37d84b9ce4d1903b3bc95ad9d4d4aaa52ed533c2834847c3a867e27`
- **Output content hash:** `sha256:559681dcfc55e011e041a98782703dc9b84ff9366d650ee41b45ec97c309df8b`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
