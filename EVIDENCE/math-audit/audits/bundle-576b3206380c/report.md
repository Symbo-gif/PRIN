# Audit Evidence Report: bundle-576b3206380c

**Overall status:** `REQUIRES_HUMAN_REVIEW`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T20:00:29.793Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### TCK-01 -- `REQUIRES_HUMAN_REVIEW`

- **Type:** `tensor_contract`  
- **Severity:** `high`  
- **Statement:** HOSVD (Tucker) reconstruction at full multilinear rank 2=[3, 4, 2] on PRIN's hosvd() (crates/prin-tensor/src/tucker.rs) reproduces the original tensor within 1e-10 absolute tolerance, using the SAME reference fixture already captured as genuine differential parity evidence against PRINet 3.0's PolyadicTensor (EA-003 finding E-F5 remediation, crates/prin-tensor/tests/data/prinet_reference_hosvd.json, crates/prin-tensor/tests/parity_decomposition.rs). math-audit-mcp's own reported relative_error field in that fixture is NOT trusted as evidence -- this claim independently re-derives the residual via audit_tensor_contract's expected_output comparison (NumPy elementwise diff of the two captured arrays), executed by the audit tool itself, not read from the fixture's self-reported metadata. EMA-004: first EMA coverage of prin-tensor / closes M-F5 (audit_tensor_contract previously could not verify HOSVD reconstruction values at all).  
- **Code references:** crates/prin-tensor/src/tucker.rs, crates/prin-tensor/tests/data/prinet_reference_hosvd.json, crates/prin-tensor/tests/parity_decomposition.rs  
- **Reason:** high/critical-severity claim passed only numerically; policy requires symbolic or formal (SymPy/Z3/Lean) corroboration before a PASS verdict  
- **Contributing audits:** audit-0a7c2a41976b

## Tool invocations

### audit_tensor_contract (`audit-0a7c2a41976b`) -- `PASS`

- **Adapter:** `none`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Contraction compatibility, output signature, and 0 symmetry claim(s) all checked out. Reconstruction: reconstruction matched expected_output (max abs residual 7.11e-15 <= tolerance 1.0e-10).

**Reasoning:** Validated 0 contraction pair(s) across 1 shape trial(s); output rank matched output_signature. Symmetry checks: none requested. reconstruction matched expected_output (max abs residual 7.11e-15 <= tolerance 1.0e-10).

**Limitations:**
- Contraction/output-signature checks without sample_values use synthetic random trial tensors (they validate shape/einsum plumbing, not real code output).
- The `expression` field is documentation only and was not evaluated.

**Metrics:**
- reconstruction_max_abs_residual: 7.105427357601002e-15
- contraction_trials_executed: 1.0

- **Random seed:** 0
- **Input content hash:** `sha256:b0e791bccdf135444b054f935c601684074b301b43b1fff095422b1125d35542`
- **Output content hash:** `sha256:f0615ef5313d5e6884fac3dcb24ab4ed0ded68972392902144397ef43c991735`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
