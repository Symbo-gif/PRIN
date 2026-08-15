# Audit Evidence Report: bundle-492de710aafb

**Overall status:** `REQUIRES_HUMAN_REVIEW`
**Policy profile:** `prin-ema` (`sha256:d19a23a4dff2c96be27ed82c26cd51cfb61bd3161583fce8b8f50aec39219053`)
**Generated:** 2026-08-15T02:30:10.792Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### TEN-01 -- `REQUIRES_HUMAN_REVIEW`

- **Type:** `tensor_contract`  
- **Severity:** `high`  
- **Statement:** build_ring's weighted coupling matrix for N=6, k_ring=4, K=1.0 (each node connected to its +-1 and +-2 neighbours mod N, weight K/k_ring=0.25) is symmetric, as required for the undirected coupling topologies coupling.rs documents (Note: audit_tensor_contract only verifies shape/contraction compatibility and symmetry against these literal sample_values -- it does not execute coupling.rs itself.)  
- **Code references:** crates/prin-dynamics/src/coupling.rs:222-263, crates/prin-dynamics/src/coupling.rs:203-220  
- **Reason:** high/critical-severity claim passed only numerically; policy requires symbolic or formal (SymPy/Z3/Lean) corroboration before a PASS verdict  
- **Contributing audits:** audit-73abbcfd735d

### TEN-02 -- `PASS`

- **Type:** `tensor_contract`  
- **Severity:** `medium`  
- **Statement:** build_all_to_all's weighted coupling matrix for N=4, K=1.0 (weight K/N=0.25 off-diagonal, zero diagonal, per coupling.rs:193-201) is symmetric, an independent second confirmation across topologies that the coupling term sum_j W_ij*sin(phi_j-phi_i) uses an undirected weight matrix.  
- **Code references:** crates/prin-dynamics/src/coupling.rs:193-201  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-16c82def202e

### TEN-01-LEAN -- `PASS`

- **Type:** `lean_theorem`  
- **Severity:** `high`  
- **Statement:** Formal (Lean 4 kernel-checked `decide`) corroboration of TEN-01: build_ring(N=6, k_ring=4, K=1.0)'s weighted coupling matrix (literal sample_values from the TEN-01 claim, represented as an exact 4x integer scaling to keep decide inside kernel-reducible Nat arithmetic) is symmetric. EMA-001 M-F3: added to let this high-severity tensor_contract claim earn genuine symbolic/formal corroboration (policy.verdict_rules.high_severity_requires_symbolic_or_formal) via a third independent channel (Lean's kernel) alongside TEN-01's own NumPy-einsum evidence, rather than relying on human sign-off alone.  
- **Code references:** crates/prin-dynamics/src/coupling.rs:222-263, crates/prin-dynamics/src/coupling.rs:203-220  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-1dc7509a220d

## Tool invocations

### audit_tensor_contract (`audit-73abbcfd735d`) -- `PASS`

- **Adapter:** `none`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Contraction compatibility, output signature, and 1 symmetry claim(s) all checked out.

**Reasoning:** Validated 0 contraction pair(s) across 1 shape trial(s); output rank matched output_signature. Symmetry checks: W.symmetric['i', 'j']: held on provided sample_values.

**Limitations:**
- Contraction/output-signature checks without sample_values use synthetic random trial tensors (they validate shape/einsum plumbing, not real code output).
- The `expression` field is documentation only and was not evaluated.

**Metrics:**
- contraction_trials_executed: 1.0

- **Random seed:** 0
- **Input content hash:** `sha256:e30509324cc18ab57f7c428d68dbc3dced8e76f7645b1c9e15055cc2e26fbac3`
- **Output content hash:** `sha256:eab8eb365a6e9aa84837d0d24b9417524586a3e830eab1660924fb81e63d0a1f`

### audit_tensor_contract (`audit-16c82def202e`) -- `PASS`

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
- **Input content hash:** `sha256:1a4d42bfa60eff92c916517cf0ea6768e77814199ede01e63211632a9f62b819`
- **Output content hash:** `sha256:f04d18dde47845b08405a5cb0d4460c053aad82645911c2b7868ed784b1dc32d`

### verify_lean_claim (`audit-1dc7509a220d`) -- `PASS`

- **Adapter:** `lean`
- **Severity:** `high`
- **Duration:** 1322 ms
- **Summary:** Lean elaborated successfully; expected_outcome='proves'.

**Reasoning:** Ran `C:\Users\there\.elan\bin\lean.EXE C:\dev\PRIN\EVIDENCE\math-audit\scratch\lean\tmpo8c6v4s3.lean`. Elaboration succeeded. See lean-diagnostics.txt artifact for full sanitized output.

**Limitations:**
- This adapter drives the Lean CLI and inspects exit status/diagnostics; it does not perform interactive elaboration introspection (a Lean LSP bridge is a documented future extension).

**Artifacts:**
- [Sanitized Lean/lake stdout+stderr](artifacts/lean-diagnostics.txt) (`sha256:596b3a82b1d006020f35176dd7c765b605a34af552445f066053db58d3de5400`)

- **Random seed:** n/a
- **Input content hash:** `sha256:f31248f3a37d84b9ce4d1903b3bc95ad9d4d4aaa52ed533c2834847c3a867e27`
- **Output content hash:** `sha256:1344d7ee3529ce7005133e0c76f1d845382472cb95b4afbcdc460d2989f09b0e`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
