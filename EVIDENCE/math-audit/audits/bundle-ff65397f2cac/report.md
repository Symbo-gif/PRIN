# Audit Evidence Report: bundle-ff65397f2cac

**Overall status:** `REQUIRES_HUMAN_REVIEW`
**Policy profile:** `prin-ema` (`sha256:0e1c329642e07f0b71a7f250a60815d3fc9f6ac4f86dda4f3865149ed6c07608`)
**Generated:** 2026-08-14T23:45:45.398Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### TEN-01 -- `REQUIRES_HUMAN_REVIEW`

- **Type:** `tensor_contract`  
- **Severity:** `high`  
- **Statement:** build_ring's weighted coupling matrix for N=6, k_ring=4, K=1.0 (each node connected to its +-1 and +-2 neighbours mod N, weight K/k_ring=0.25) is symmetric, as required for the undirected coupling topologies coupling.rs documents (Note: audit_tensor_contract only verifies shape/contraction compatibility and symmetry against these literal sample_values -- it does not execute coupling.rs itself.)  
- **Code references:** crates/prin-dynamics/src/coupling.rs:222-263, crates/prin-dynamics/src/coupling.rs:203-220  
- **Reason:** high/critical-severity claim passed only numerically; policy requires symbolic or formal (SymPy/Z3/Lean) corroboration before a PASS verdict  
- **Contributing audits:** audit-086df1d32463

### TEN-02 -- `PASS`

- **Type:** `tensor_contract`  
- **Severity:** `medium`  
- **Statement:** build_all_to_all's weighted coupling matrix for N=4, K=1.0 (weight K/N=0.25 off-diagonal, zero diagonal, per coupling.rs:193-201) is symmetric, an independent second confirmation across topologies that the coupling term sum_j W_ij*sin(phi_j-phi_i) uses an undirected weight matrix.  
- **Code references:** crates/prin-dynamics/src/coupling.rs:193-201  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-2262d913c407

## Tool invocations

### audit_tensor_contract (`audit-086df1d32463`) -- `PASS`

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
- **Input content hash:** `sha256:e30509324cc18ab57f7c428d68dbc3dced8e76f7645b1c9e15055cc2e26fbac3`
- **Output content hash:** `sha256:af40b2fee27263789f96a4808d136d92a69294b8d771529327ece6e7d9605e9f`

### audit_tensor_contract (`audit-2262d913c407`) -- `PASS`

- **Adapter:** `none`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** Contraction compatibility, output signature, and 1 symmetry claim(s) all checked out.

**Reasoning:** Validated 0 contraction pair(s) across 1 shape trial(s); output rank matched output_signature. Symmetry checks: W.symmetric['i', 'j']: held on provided sample_values.

**Limitations:**
- Contraction/output-signature checks without sample_values use synthetic random trial tensors (they validate shape/einsum plumbing, not real code output).
- The `expression` field is documentation only and was not evaluated.

**Metrics:**
- contraction_trials_executed: 1.0

- **Random seed:** 0
- **Input content hash:** `sha256:1a4d42bfa60eff92c916517cf0ea6768e77814199ede01e63211632a9f62b819`
- **Output content hash:** `sha256:77a859f6265240384db3266058906873373d10cdc652fb80100ccca5ff67db31`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
