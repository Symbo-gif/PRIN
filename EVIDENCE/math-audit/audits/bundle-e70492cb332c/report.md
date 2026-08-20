# Audit Evidence Report: bundle-e70492cb332c

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-08-20T04:30:51.188Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### HSL-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Hungarian similarity loss on a uniform (all-zero) NxN similarity matrix with temperature T=0.1 yields -log(1/N) = log(N). For N=2: all logits are 0, softmax is uniform over 2 classes, so -log(1/2) = ln(2). This verifies the cross-entropy-over-softmax-diagonal formula in losses.rs:28-44 reduces to the correct entropy of the uniform distribution.  
- **Code references:** crates/prin-train/src/losses.rs:28-44  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-9c105b0a5c5c

### DSILU-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The derivative of SiLU(z) = z*sigma(z) is sigma(z) + z*sigma(z)*(1-sigma(z)), which is exactly what d_silu computes. At z=0: sigma(0)=1/2, so dSiLU(0) = 1/2 + 0*(1/2)*(1/2) = 1/2. This verifies the activation formula in activations.rs:82-86.  
- **Code references:** crates/prin-train/src/activations.rs:82-86  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-028d3bbc6c5d

### SCALR-LR-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** Scalr's compute_lr_scale at r=1 yields exactly 1 (full base lr when fully synchronized): r_min + (1-r_min)*1^alpha = r_min + 1 - r_min = 1, independent of r_min and alpha. This verifies scalr.rs:228-232.  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-7f0a51533faf

### SCALR-LR-02 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Scalr's compute_lr_scale at r=0 yields exactly r_min (minimum lr fraction when fully desynchronized): r_min + (1-r_min)*0^alpha = r_min for any alpha > 0. This verifies the boundary behavior in scalr.rs:228-232.  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-f9567a14a55d

### RIP-HEBB-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** RIP Hebbian update with all-equal phases (synchronized, cos(0)=1) and amplitude exactly at target yields zero coupling change: delta = lr * cos(0) * r_target * (r_target - r_target) = lr * 1 * r_target * 0 = 0. This verifies rip.rs:195-218's core Hebbian formula at the equilibrium point.  
- **Code references:** crates/prin-train/src/rip.rs:195-218  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-ebf3d23613f3

### SYNC-PEN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** SyncGd's sync penalty gradient scale equals the derivative of the penalty with respect to the order parameter: d/dK[lambda*max(0, K_c-K)^2] = -2*lambda*max(0, K_c-K) for K < K_c, and 0 for K >= K_c. The code computes grad_scale = 2*lambda*deficit (the magnitude), used to reduce the effective learning rate. This verifies sync_gd.rs:267-278.  
- **Code references:** crates/prin-train/src/sync_gd.rs:267-278  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-8b30a6dab253

### GPA-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** GatedPhaseActivation's output is bounded in [0, 2*pi): the gate sigmoid produces values in [0,1], phase_activation produces values in [0, 2*pi), so their elementwise product is in [0, 2*pi). This is the load-bearing invariant for phase-valued oscillator outputs.  
- **Code references:** crates/prin-train/src/activations.rs:301-312, crates/prin-train/src/activations.rs:82-95  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-0e9ed60e6e3b

### SCALR-SCALE-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** Scalr's compute_lr_scale output is bounded in [r_min, 1] for any clamped r in [0,1] and alpha >= 1: f(r) = r_min + (1-r_min)*r^alpha. Since r^alpha in [0,1] for r in [0,1] and alpha>=1, f(r) in [r_min, r_min + (1-r_min)] = [r_min, 1].  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-0ae7b8852961

### SYNC-PEN-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** SyncGd's compute_sync_penalty always returns a non-negative penalty: lambda*max(0, K_c-K)^2 >= 0 for lambda >= 0 and any K, K_c. The penalty is a squared term scaled by a non-negative weight.  
- **Code references:** crates/prin-train/src/sync_gd.rs:267-278  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-e26e0f901712

### RIP-DIAG-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** RIP's Hebbian update always produces a zero diagonal (no self-coupling): for any i, delta[i,i] * mask[i,i] = delta[i,i] * 0 = 0, since the mask is (1 - I) where I is the identity matrix. The diagonal of the updated coupling matrix is always zero regardless of the Hebbian delta values.  
- **Code references:** crates/prin-train/src/rip.rs:215-218  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-ead1373ce8f1

## Tool invocations

### verify_identity (`audit-9c105b0a5c5c`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 4 ms
- **Summary:** Symbolic proof established: -(1/2)*(log(exp(0/T)/(exp(0/T)+exp(0/T))) + log(exp(0/T)/(exp(0/T)+exp(0/T)))) == log(2).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:000f626c15dc18a7ef73d80b7bb140865ead2ad10d3067b264671f39559c3506`
- **Output content hash:** `sha256:5784690c99ee84775258c13df3471cba865e930f9998dc44a38a4e8b6113d251`

### wolfram_crosscheck (`audit-3f1fb313fc45`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:731667d581ffbbadb32df00cc5c81576e027826e0a1a3c43bfbf84310d20c797`
- **Output content hash:** `sha256:6d040003cbd3d67075f465f47261cb3704b2bd721783c8a906866e29c539e171`

### verify_identity (`audit-028d3bbc6c5d`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 15 ms
- **Summary:** Symbolic proof established: 1/(1+exp(-z)) + z*(1/(1+exp(-z)))*(1 - 1/(1+exp(-z))) == 1/(1+exp(-z)) + z*exp(-z)/(1+exp(-z))**2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:7ce2baeb64c1890928f6264329b6fd3d6f9da044e0fb089568a721ef0499de79`
- **Output content hash:** `sha256:9f147528db42f7ce2496921eae290860ade3de1fd025428e107e241759b7b22f`

### wolfram_crosscheck (`audit-62c74b121a73`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:c4e397834012bc2d2510bf1755232e07cba6a28411dda8f747f2120f1699d999`
- **Output content hash:** `sha256:d2c41fcaf21ecd97a633abd6aa3c4895276f13a1a4fbc64142e348d7d8352c57`

### verify_identity (`audit-7f0a51533faf`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Symbolic proof established: r_min + (1 - r_min)*1**alpha == 1.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:44dbf603d42a52d982ca96059647d4f691393e1fcd16b7aaedaccac561b0523c`
- **Output content hash:** `sha256:06e3e80d53ea74bce4d18d3ec510945fe960c50c06bd15ca9081306988a495c8`

### wolfram_crosscheck (`audit-d3deb6459d82`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0fb028fd918ebf41e7deb5dce54741939dbfa9a1ad0185b37ce92d8922aa63e8`
- **Output content hash:** `sha256:5dc87ad3c3b95811dd63fd3725d7f03c6255f141a13e78ba4d20d44a243d83f8`

### verify_identity (`audit-f9567a14a55d`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** Symbolic proof established: r_min + (1 - r_min)*0**alpha == r_min.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- alpha > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:9764b7320d4ecf3a6997b742f3cdb65c41b178fde3e6432015e9acb3fd98e57f`
- **Output content hash:** `sha256:42f3375d87063cbd59e4de791c440cf310ad381f2b51c397b4a97d5ecea6c723`

### wolfram_crosscheck (`audit-c4f6a8bf787d`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0937659c3710395941c41b45781176f07164c86a4f049cdefa2a4b3d15dbfa10`
- **Output content hash:** `sha256:78d35accd168d57803edda03df1844ac6655685caee0b21fc8e5157af4ee092a`

### verify_identity (`audit-ebf3d23613f3`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Symbolic proof established: lr * cos(0) * r_target * (r_target - r_target) == 0.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:69ee16efe2f261501eece803e69f53e4f103f3f0ca613cc428116c391675b010`
- **Output content hash:** `sha256:3602381bd39e17df7120c500642cb10e226c403fdfd3cab40888cbfcd184a074`

### wolfram_crosscheck (`audit-2b2416d81f93`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:4074a0223ced89e37d5fb0db6f265579b54df10f846e4bffa230c83610557abe`
- **Output content hash:** `sha256:c33ce4a79dcbd38543a5c55de7f82687e655976051499d4426d35ad4b1eca024`

### verify_identity (`audit-8b30a6dab253`) -- `PASS`

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
- **Output content hash:** `sha256:ab4763f64d1efc6641bcf8cad4e0e5f84dd0c9a2fcd76375152e0243ef2842f7`

### wolfram_crosscheck (`audit-ee212ff36321`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:ce59d456744475fc9fae749568e3939a20d79157feb2410f23653473e0d032b6`
- **Output content hash:** `sha256:b141a53082b0e91702d94a51c296e2d71d3cf959fc0ae66cb06963857e028a06`

### check_constraint_model (`audit-0e9ed60e6e3b`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 10 ms
- **Summary:** All 1 quer(y/ies) held: gpa-output-bounded: pass

**Reasoning:** gpa-output-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:947ec564234f48949b64cceb8a5c527de776578fdd57e2ddc4c484027e385003`
- **Output content hash:** `sha256:cd597c61395dc926075b4294fb89f9037a6efdc2c462330f7d31580d7c5be62d`

### check_constraint_model (`audit-0ae7b8852961`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 8 ms
- **Summary:** All 1 quer(y/ies) held: scalr-scale-bounded: pass

**Reasoning:** scalr-scale-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:675fa51852a393a2369d61b62780595efc41e23ede1eb2bcc2b572ff6c86a77b`
- **Output content hash:** `sha256:7a3fa85fa6e034afdc3c1485a06de16c34a0be4a6293cbc7aec8fb3560e16b2a`

### check_constraint_model (`audit-e26e0f901712`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 7 ms
- **Summary:** All 1 quer(y/ies) held: penalty-non-negative: pass

**Reasoning:** penalty-non-negative: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:c648f0b159f18cea15273825a4b4ec6a0968f1349e0d558d5cbf76ecf86b9f27`
- **Output content hash:** `sha256:6dfaaaeb70abea374bf48de1c1b020fcf48029d1617d5c2a6cceb1f854c4a8ab`

### check_constraint_model (`audit-ead1373ce8f1`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** All 1 quer(y/ies) held: diagonal-always-zero: pass

**Reasoning:** diagonal-always-zero: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:2e0c1e2bfa23e1410726bb2aa516b322e395be8bbc7d4460e042140040f73c90`
- **Output content hash:** `sha256:ef84c1d85d0c514a45501a255176bb757d29b098a6d6b45b2653bf635e69b2b4`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
