# Audit Evidence Report: bundle-8607173ac18f

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-08-26T05:07:44.760Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### HSL-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Hungarian similarity loss on a uniform (all-zero) NxN similarity matrix with temperature T=0.1 yields -log(1/N) = log(N). For N=2: all logits are 0, softmax is uniform over 2 classes, so -log(1/2) = ln(2). This verifies the cross-entropy-over-softmax-diagonal formula in losses.rs:28-44 reduces to the correct entropy of the uniform distribution.  
- **Code references:** crates/prin-train/src/losses.rs:28-44  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-816326000ab8

### DSILU-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The derivative of SiLU(z) = z*sigma(z) is sigma(z) + z*sigma(z)*(1-sigma(z)), which is exactly what d_silu computes. At z=0: sigma(0)=1/2, so dSiLU(0) = 1/2 + 0*(1/2)*(1/2) = 1/2. This verifies the activation formula in activations.rs:82-86.  
- **Code references:** crates/prin-train/src/activations.rs:82-86  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-53bdfae5c9c4

### SCALR-LR-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** Scalr's compute_lr_scale at r=1 yields exactly 1 (full base lr when fully synchronized): r_min + (1-r_min)*1^alpha = r_min + 1 - r_min = 1, independent of r_min and alpha. This verifies scalr.rs:228-232.  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-8342e2fa0c50

### SCALR-LR-02 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Scalr's compute_lr_scale at r=0 yields exactly r_min (minimum lr fraction when fully desynchronized): r_min + (1-r_min)*0^alpha = r_min for any alpha > 0. This verifies the boundary behavior in scalr.rs:228-232.  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-0efc502f09c0

### RIP-HEBB-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** RIP Hebbian update with all-equal phases (synchronized, cos(0)=1) and amplitude exactly at target yields zero coupling change: delta = lr * cos(0) * r_target * (r_target - r_target) = lr * 1 * r_target * 0 = 0. This verifies rip.rs:195-218's core Hebbian formula at the equilibrium point.  
- **Code references:** crates/prin-train/src/rip.rs:195-218  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-933c45103c06

### SYNC-PEN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** SyncGd's sync penalty gradient scale equals the derivative of the penalty with respect to the order parameter: d/dK[lambda*max(0, K_c-K)^2] = -2*lambda*max(0, K_c-K) for K < K_c, and 0 for K >= K_c. The code computes grad_scale = 2*lambda*deficit (the magnitude), used to reduce the effective learning rate. This verifies sync_gd.rs:267-278.  
- **Code references:** crates/prin-train/src/sync_gd.rs:267-278  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-efdc090638a3

### GPA-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** GatedPhaseActivation's output is bounded in [0, 2*pi): the gate sigmoid produces values in [0,1], phase_activation produces values in [0, 2*pi), so their elementwise product is in [0, 2*pi). This is the load-bearing invariant for phase-valued oscillator outputs.  
- **Code references:** crates/prin-train/src/activations.rs:301-312, crates/prin-train/src/activations.rs:82-95  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-65f59eccaa74

### SCALR-SCALE-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** Scalr's compute_lr_scale output is bounded in [r_min, 1] for any clamped r in [0,1] and alpha >= 1: f(r) = r_min + (1-r_min)*r^alpha. Since r^alpha in [0,1] for r in [0,1] and alpha>=1, f(r) in [r_min, r_min + (1-r_min)] = [r_min, 1].  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-0d7cbe32250c

### SYNC-PEN-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** SyncGd's compute_sync_penalty always returns a non-negative penalty: lambda*max(0, K_c-K)^2 >= 0 for lambda >= 0 and any K, K_c. The penalty is a squared term scaled by a non-negative weight.  
- **Code references:** crates/prin-train/src/sync_gd.rs:267-278  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-faf3107ca99d

### RIP-DIAG-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** RIP's Hebbian update always produces a zero diagonal (no self-coupling): for any i, delta[i,i] * mask[i,i] = delta[i,i] * 0 = 0, since the mask is (1 - I) where I is the identity matrix. The diagonal of the updated coupling matrix is always zero regardless of the Hebbian delta values.  
- **Code references:** crates/prin-train/src/rip.rs:215-218  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-3b8252c3cfb3

## Tool invocations

### verify_identity (`audit-816326000ab8`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: -(1/2)*(log(exp(0/T)/(exp(0/T)+exp(0/T))) + log(exp(0/T)/(exp(0/T)+exp(0/T)))) == log(2).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:000f626c15dc18a7ef73d80b7bb140865ead2ad10d3067b264671f39559c3506`
- **Output content hash:** `sha256:c3b95654145c6b00f585d39cfc71f4662ff459026efac24120afcf48010fbd26`

### wolfram_crosscheck (`audit-92d08a2df8d5`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:731667d581ffbbadb32df00cc5c81576e027826e0a1a3c43bfbf84310d20c797`
- **Output content hash:** `sha256:87f9dbf0b498c86c7b6add9aab618afa814ecab7699d81a52c51796875f128c8`

### verify_identity (`audit-53bdfae5c9c4`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 18 ms
- **Summary:** Symbolic proof established: 1/(1+exp(-z)) + z*(1/(1+exp(-z)))*(1 - 1/(1+exp(-z))) == 1/(1+exp(-z)) + z*exp(-z)/(1+exp(-z))**2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:7ce2baeb64c1890928f6264329b6fd3d6f9da044e0fb089568a721ef0499de79`
- **Output content hash:** `sha256:e3eaaace0186ca9e6b0b7fd255f9599817e8b1457d693f1c9d451baa89c2958d`

### wolfram_crosscheck (`audit-a22ca19bfc16`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:c4e397834012bc2d2510bf1755232e07cba6a28411dda8f747f2120f1699d999`
- **Output content hash:** `sha256:6887a522be58374657ca39ffdb9892e1c15742a1bab44fe745ff8c17ac59f761`

### verify_identity (`audit-8342e2fa0c50`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Symbolic proof established: r_min + (1 - r_min)*1**alpha == 1.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:44dbf603d42a52d982ca96059647d4f691393e1fcd16b7aaedaccac561b0523c`
- **Output content hash:** `sha256:1321d7961406936d06f78fa91d2dd38a8abff6f4a6e0f812d6d19bf0debf4345`

### wolfram_crosscheck (`audit-aa071faf6c9e`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0fb028fd918ebf41e7deb5dce54741939dbfa9a1ad0185b37ce92d8922aa63e8`
- **Output content hash:** `sha256:cb64e040cad6e1cf190d16d2f993cf9e34befc3dbd9f44645a974acbc1445277`

### verify_identity (`audit-0efc502f09c0`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: r_min + (1 - r_min)*0**alpha == r_min.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- alpha > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:9764b7320d4ecf3a6997b742f3cdb65c41b178fde3e6432015e9acb3fd98e57f`
- **Output content hash:** `sha256:9dc34334f109521c514368d00aeca970177c86f5b0c5608b9cace3a11c14ece0`

### wolfram_crosscheck (`audit-e06256b97d0c`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0937659c3710395941c41b45781176f07164c86a4f049cdefa2a4b3d15dbfa10`
- **Output content hash:** `sha256:87606c2ec854d026e5687a0b570ea51f7dc6e3af15154d91fd80c86038114fa1`

### verify_identity (`audit-933c45103c06`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Symbolic proof established: lr * cos(0) * r_target * (r_target - r_target) == 0.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:69ee16efe2f261501eece803e69f53e4f103f3f0ca613cc428116c391675b010`
- **Output content hash:** `sha256:5b672dfaeadfefd08d49725dd3c62b0eebe39e860639c3842471c314c9bdb7f0`

### wolfram_crosscheck (`audit-455f4a7956e8`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:4074a0223ced89e37d5fb0db6f265579b54df10f846e4bffa230c83610557abe`
- **Output content hash:** `sha256:9f83227913330e8f775c3d19630cb3f4354b40f1601b6bfa90ea4b4ec0a92ad7`

### verify_identity (`audit-efdc090638a3`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 6 ms
- **Summary:** Symbolic proof established: 2*lam*(K_c - K) == 2*lam*(K_c - K).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- K < K_c
- lam > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:79f990e1947fe7fe297712e6fc0609ca12df945169bf102adb9d69db67419d3a`
- **Output content hash:** `sha256:b8889ac230d9ba4aea8611e3b981f8aa78353886fd9eb277a2b81adf41921ef8`

### wolfram_crosscheck (`audit-eb05123ef071`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:ce59d456744475fc9fae749568e3939a20d79157feb2410f23653473e0d032b6`
- **Output content hash:** `sha256:581d363bf333e28c12cbeca54b28ee7359163b3de9a215aa7acfe2df2eca59b5`

### check_constraint_model (`audit-65f59eccaa74`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 8 ms
- **Summary:** All 1 quer(y/ies) held: gpa-output-bounded: pass

**Reasoning:** gpa-output-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:947ec564234f48949b64cceb8a5c527de776578fdd57e2ddc4c484027e385003`
- **Output content hash:** `sha256:76180e67ab08ebae116311b0a5df3b5f89a34597e5c2c2ffbd7bfd804e6ff7e3`

### check_constraint_model (`audit-0d7cbe32250c`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 7 ms
- **Summary:** All 1 quer(y/ies) held: scalr-scale-bounded: pass

**Reasoning:** scalr-scale-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:675fa51852a393a2369d61b62780595efc41e23ede1eb2bcc2b572ff6c86a77b`
- **Output content hash:** `sha256:2d87a23bfbe5b43d25bed77e36ada65287f54fa9e0876c3968b0670572c94fe3`

### check_constraint_model (`audit-faf3107ca99d`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 7 ms
- **Summary:** All 1 quer(y/ies) held: penalty-non-negative: pass

**Reasoning:** penalty-non-negative: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:c648f0b159f18cea15273825a4b4ec6a0968f1349e0d558d5cbf76ecf86b9f27`
- **Output content hash:** `sha256:9b1fb1bbd4422319b00a302fb62a64f6726dafba32e878a731ae5b2589008207`

### check_constraint_model (`audit-3b8252c3cfb3`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** All 1 quer(y/ies) held: diagonal-always-zero: pass

**Reasoning:** diagonal-always-zero: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:2e0c1e2bfa23e1410726bb2aa516b322e395be8bbc7d4460e042140040f73c90`
- **Output content hash:** `sha256:fa153749fa8ef9bdc821b7a28754a03dc1cd8e682b426fce0ac38a86b7a131ad`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
