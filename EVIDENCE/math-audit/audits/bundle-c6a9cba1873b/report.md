# Audit Evidence Report: bundle-c6a9cba1873b

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T19:57:53.520Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### HSL-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Hungarian similarity loss on a uniform (all-zero) NxN similarity matrix with temperature T=0.1 yields -log(1/N) = log(N). For N=2: all logits are 0, softmax is uniform over 2 classes, so -log(1/2) = ln(2). This verifies the cross-entropy-over-softmax-diagonal formula in losses.rs:28-44 reduces to the correct entropy of the uniform distribution.  
- **Code references:** crates/prin-train/src/losses.rs:28-44  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-4004ae833060

### DSILU-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The derivative of SiLU(z) = z*sigma(z) is sigma(z) + z*sigma(z)*(1-sigma(z)), which is exactly what d_silu computes. At z=0: sigma(0)=1/2, so dSiLU(0) = 1/2 + 0*(1/2)*(1/2) = 1/2. This verifies the activation formula in activations.rs:82-86.  
- **Code references:** crates/prin-train/src/activations.rs:82-86  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-132a7f7f84f0

### SCALR-LR-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** Scalr's compute_lr_scale at r=1 yields exactly 1 (full base lr when fully synchronized): r_min + (1-r_min)*1^alpha = r_min + 1 - r_min = 1, independent of r_min and alpha. This verifies scalr.rs:228-232.  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-d20ad9ac3c20

### SCALR-LR-02 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Scalr's compute_lr_scale at r=0 yields exactly r_min (minimum lr fraction when fully desynchronized): r_min + (1-r_min)*0^alpha = r_min for any alpha > 0. This verifies the boundary behavior in scalr.rs:228-232.  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-a8419f8b76c3

### RIP-HEBB-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** RIP Hebbian update with all-equal phases (synchronized, cos(0)=1) and amplitude exactly at target yields zero coupling change: delta = lr * cos(0) * r_target * (r_target - r_target) = lr * 1 * r_target * 0 = 0. This verifies rip.rs:195-218's core Hebbian formula at the equilibrium point.  
- **Code references:** crates/prin-train/src/rip.rs:195-218  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-2975407bcd43

### SYNC-PEN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** SyncGd's sync penalty gradient scale equals the derivative of the penalty with respect to the order parameter: d/dK[lambda*max(0, K_c-K)^2] = -2*lambda*max(0, K_c-K) for K < K_c, and 0 for K >= K_c. The code computes grad_scale = 2*lambda*deficit (the magnitude), used to reduce the effective learning rate. This verifies sync_gd.rs:267-278.  
- **Code references:** crates/prin-train/src/sync_gd.rs:267-278  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-a12403091aa6

### GPA-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** GatedPhaseActivation's output is bounded in [0, 2*pi): the gate sigmoid produces values in [0,1], phase_activation produces values in [0, 2*pi), so their elementwise product is in [0, 2*pi). This is the load-bearing invariant for phase-valued oscillator outputs.  
- **Code references:** crates/prin-train/src/activations.rs:301-312, crates/prin-train/src/activations.rs:82-95  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-4b499b56330b

### SCALR-SCALE-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** Scalr's compute_lr_scale output is bounded in [r_min, 1] for any clamped r in [0,1] and alpha >= 1: f(r) = r_min + (1-r_min)*r^alpha. Since r^alpha in [0,1] for r in [0,1] and alpha>=1, f(r) in [r_min, r_min + (1-r_min)] = [r_min, 1].  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-353904da0a46

### SYNC-PEN-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** SyncGd's compute_sync_penalty always returns a non-negative penalty: lambda*max(0, K_c-K)^2 >= 0 for lambda >= 0 and any K, K_c. The penalty is a squared term scaled by a non-negative weight.  
- **Code references:** crates/prin-train/src/sync_gd.rs:267-278  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-6eca46e100fa

### RIP-DIAG-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** RIP's Hebbian update always produces a zero diagonal (no self-coupling): for any i, delta[i,i] * mask[i,i] = delta[i,i] * 0 = 0, since the mask is (1 - I) where I is the identity matrix. The diagonal of the updated coupling matrix is always zero regardless of the Hebbian delta values.  
- **Code references:** crates/prin-train/src/rip.rs:215-218  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-d4bed685fe7d

## Tool invocations

### verify_identity (`audit-4004ae833060`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: -(1/2)*(log(exp(0/T)/(exp(0/T)+exp(0/T))) + log(exp(0/T)/(exp(0/T)+exp(0/T)))) == log(2).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:000f626c15dc18a7ef73d80b7bb140865ead2ad10d3067b264671f39559c3506`
- **Output content hash:** `sha256:9111263d0038b3b706779d0dc95b48a6667a71e0d5c119c56dfd6ce7c0c86e8e`

### wolfram_crosscheck (`audit-4ee96b048c1d`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:731667d581ffbbadb32df00cc5c81576e027826e0a1a3c43bfbf84310d20c797`
- **Output content hash:** `sha256:7e5e63b758f19204c81b610261c41fa27a407b93ff9682a4fba062d69276175b`

### verify_identity (`audit-132a7f7f84f0`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 30 ms
- **Summary:** Symbolic proof established: 1/(1+exp(-z)) + z*(1/(1+exp(-z)))*(1 - 1/(1+exp(-z))) == 1/(1+exp(-z)) + z*exp(-z)/(1+exp(-z))**2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:7ce2baeb64c1890928f6264329b6fd3d6f9da044e0fb089568a721ef0499de79`
- **Output content hash:** `sha256:f632a78278d5f370deb815cd2e535e792870fdb83fd9eec42f6f67faaa583708`

### wolfram_crosscheck (`audit-1513ddfbde0c`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:c4e397834012bc2d2510bf1755232e07cba6a28411dda8f747f2120f1699d999`
- **Output content hash:** `sha256:f42dfcdab74179a092cf42386c7ca353b711b3e65ae9c43e973444e177abf26f`

### verify_identity (`audit-d20ad9ac3c20`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Symbolic proof established: r_min + (1 - r_min)*1**alpha == 1.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:44dbf603d42a52d982ca96059647d4f691393e1fcd16b7aaedaccac561b0523c`
- **Output content hash:** `sha256:b395d7caf01af4094ec617808a391b22db929f12b75d493d348ee9c5830403c2`

### wolfram_crosscheck (`audit-9f563fd5d56c`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0fb028fd918ebf41e7deb5dce54741939dbfa9a1ad0185b37ce92d8922aa63e8`
- **Output content hash:** `sha256:6c71c3915cc6e4dd44551f68d06ea4d712d430320f1638a49af32c0e4e125480`

### verify_identity (`audit-a8419f8b76c3`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: r_min + (1 - r_min)*0**alpha == r_min.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- alpha > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:9764b7320d4ecf3a6997b742f3cdb65c41b178fde3e6432015e9acb3fd98e57f`
- **Output content hash:** `sha256:b5b252fdd00ecc54df29947df240faa69809fcc9fc66558be4eb0e54a7c0ee42`

### wolfram_crosscheck (`audit-edeb109e9577`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0937659c3710395941c41b45781176f07164c86a4f049cdefa2a4b3d15dbfa10`
- **Output content hash:** `sha256:7cd0e2b08402ac55c0ff32b9695d41262b1fff847b201a3a2c661aa70842adb3`

### verify_identity (`audit-2975407bcd43`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Symbolic proof established: lr * cos(0) * r_target * (r_target - r_target) == 0.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:69ee16efe2f261501eece803e69f53e4f103f3f0ca613cc428116c391675b010`
- **Output content hash:** `sha256:68712bfae15cae59f4054df5087dafbd51a3519f10c2aff1c83ebaf02fd42b99`

### wolfram_crosscheck (`audit-fcad8b3502c4`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:4074a0223ced89e37d5fb0db6f265579b54df10f846e4bffa230c83610557abe`
- **Output content hash:** `sha256:5a6123b70246d30ba8616d582ac5c76d9d0dec731db8c84e4b78289f1969c941`

### verify_identity (`audit-a12403091aa6`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: 2*lam*(K_c - K) == 2*lam*(K_c - K).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- K < K_c
- lam > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:79f990e1947fe7fe297712e6fc0609ca12df945169bf102adb9d69db67419d3a`
- **Output content hash:** `sha256:b9c022fdd0c5c4d9a3366e79f301e6257a6bbf75cf99379cf64ccc6002cfb8a7`

### wolfram_crosscheck (`audit-4dfd5592d4f7`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:ce59d456744475fc9fae749568e3939a20d79157feb2410f23653473e0d032b6`
- **Output content hash:** `sha256:a92b45f097d173032887b2649105a79c7216a213dfa60b47477b31bc0a3b78c5`

### check_constraint_model (`audit-4b499b56330b`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 7 ms
- **Summary:** All 1 quer(y/ies) held: gpa-output-bounded: pass

**Reasoning:** gpa-output-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:947ec564234f48949b64cceb8a5c527de776578fdd57e2ddc4c484027e385003`
- **Output content hash:** `sha256:1d6116f0d9d05dc400e5db476f392f201ca197773c7169e1471588cc34623488`

### check_constraint_model (`audit-353904da0a46`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 6 ms
- **Summary:** All 1 quer(y/ies) held: scalr-scale-bounded: pass

**Reasoning:** scalr-scale-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:675fa51852a393a2369d61b62780595efc41e23ede1eb2bcc2b572ff6c86a77b`
- **Output content hash:** `sha256:584fc24853f40a8bca354dd0878359d5d352fc88ddb5e78b81f52a15946467f7`

### check_constraint_model (`audit-6eca46e100fa`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 6 ms
- **Summary:** All 1 quer(y/ies) held: penalty-non-negative: pass

**Reasoning:** penalty-non-negative: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:c648f0b159f18cea15273825a4b4ec6a0968f1349e0d558d5cbf76ecf86b9f27`
- **Output content hash:** `sha256:f105cc561eb530c5fab6f02edd14556db96473dfa93ad54380eaada45a04ebd3`

### check_constraint_model (`audit-d4bed685fe7d`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** All 1 quer(y/ies) held: diagonal-always-zero: pass

**Reasoning:** diagonal-always-zero: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:2e0c1e2bfa23e1410726bb2aa516b322e395be8bbc7d4460e042140040f73c90`
- **Output content hash:** `sha256:8d256da634bbd0c89f356ac539a9909a1047324ee6fe09b5a70fb37368375e62`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
