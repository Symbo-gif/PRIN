# Audit Evidence Report: bundle-3289ce8136f9

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T19:55:21.775Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### HSL-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Hungarian similarity loss on a uniform (all-zero) NxN similarity matrix with temperature T=0.1 yields -log(1/N) = log(N). For N=2: all logits are 0, softmax is uniform over 2 classes, so -log(1/2) = ln(2). This verifies the cross-entropy-over-softmax-diagonal formula in losses.rs:28-44 reduces to the correct entropy of the uniform distribution.  
- **Code references:** crates/prin-train/src/losses.rs:28-44  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-e5d4d038ca8f

### DSILU-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The derivative of SiLU(z) = z*sigma(z) is sigma(z) + z*sigma(z)*(1-sigma(z)), which is exactly what d_silu computes. At z=0: sigma(0)=1/2, so dSiLU(0) = 1/2 + 0*(1/2)*(1/2) = 1/2. This verifies the activation formula in activations.rs:82-86.  
- **Code references:** crates/prin-train/src/activations.rs:82-86  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-2037e283349a

### SCALR-LR-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** Scalr's compute_lr_scale at r=1 yields exactly 1 (full base lr when fully synchronized): r_min + (1-r_min)*1^alpha = r_min + 1 - r_min = 1, independent of r_min and alpha. This verifies scalr.rs:228-232.  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-0be52334b43d

### SCALR-LR-02 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Scalr's compute_lr_scale at r=0 yields exactly r_min (minimum lr fraction when fully desynchronized): r_min + (1-r_min)*0^alpha = r_min for any alpha > 0. This verifies the boundary behavior in scalr.rs:228-232.  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-792aaac65981

### RIP-HEBB-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** RIP Hebbian update with all-equal phases (synchronized, cos(0)=1) and amplitude exactly at target yields zero coupling change: delta = lr * cos(0) * r_target * (r_target - r_target) = lr * 1 * r_target * 0 = 0. This verifies rip.rs:195-218's core Hebbian formula at the equilibrium point.  
- **Code references:** crates/prin-train/src/rip.rs:195-218  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-46be93fd00c9

### SYNC-PEN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** SyncGd's sync penalty gradient scale equals the derivative of the penalty with respect to the order parameter: d/dK[lambda*max(0, K_c-K)^2] = -2*lambda*max(0, K_c-K) for K < K_c, and 0 for K >= K_c. The code computes grad_scale = 2*lambda*deficit (the magnitude), used to reduce the effective learning rate. This verifies sync_gd.rs:267-278.  
- **Code references:** crates/prin-train/src/sync_gd.rs:267-278  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-5090277ed905

### GPA-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** GatedPhaseActivation's output is bounded in [0, 2*pi): the gate sigmoid produces values in [0,1], phase_activation produces values in [0, 2*pi), so their elementwise product is in [0, 2*pi). This is the load-bearing invariant for phase-valued oscillator outputs.  
- **Code references:** crates/prin-train/src/activations.rs:301-312, crates/prin-train/src/activations.rs:82-95  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-42d9ef57473c

### SCALR-SCALE-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** Scalr's compute_lr_scale output is bounded in [r_min, 1] for any clamped r in [0,1] and alpha >= 1: f(r) = r_min + (1-r_min)*r^alpha. Since r^alpha in [0,1] for r in [0,1] and alpha>=1, f(r) in [r_min, r_min + (1-r_min)] = [r_min, 1].  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-461746574f7e

### SYNC-PEN-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** SyncGd's compute_sync_penalty always returns a non-negative penalty: lambda*max(0, K_c-K)^2 >= 0 for lambda >= 0 and any K, K_c. The penalty is a squared term scaled by a non-negative weight.  
- **Code references:** crates/prin-train/src/sync_gd.rs:267-278  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-e4a82d6b2025

### RIP-DIAG-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** RIP's Hebbian update always produces a zero diagonal (no self-coupling): for any i, delta[i,i] * mask[i,i] = delta[i,i] * 0 = 0, since the mask is (1 - I) where I is the identity matrix. The diagonal of the updated coupling matrix is always zero regardless of the Hebbian delta values.  
- **Code references:** crates/prin-train/src/rip.rs:215-218  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-dc558f788929

## Tool invocations

### verify_identity (`audit-e5d4d038ca8f`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: -(1/2)*(log(exp(0/T)/(exp(0/T)+exp(0/T))) + log(exp(0/T)/(exp(0/T)+exp(0/T)))) == log(2).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:000f626c15dc18a7ef73d80b7bb140865ead2ad10d3067b264671f39559c3506`
- **Output content hash:** `sha256:9eba53305bebc667bcea39de58974125f5fdc95c7b8385fbb053c4b5635064a8`

### wolfram_crosscheck (`audit-5e7255d0006f`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:731667d581ffbbadb32df00cc5c81576e027826e0a1a3c43bfbf84310d20c797`
- **Output content hash:** `sha256:30b042d53f96b5b45a6c64fcecb516bdd9980a6d1892c881041c4884e640ef7e`

### verify_identity (`audit-2037e283349a`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 25 ms
- **Summary:** Symbolic proof established: 1/(1+exp(-z)) + z*(1/(1+exp(-z)))*(1 - 1/(1+exp(-z))) == 1/(1+exp(-z)) + z*exp(-z)/(1+exp(-z))**2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:7ce2baeb64c1890928f6264329b6fd3d6f9da044e0fb089568a721ef0499de79`
- **Output content hash:** `sha256:0f7eba0768f2e7286777b05e77294588cb7d4d6d298392dee9489c053ed6c3f3`

### wolfram_crosscheck (`audit-2107cbb92cad`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:c4e397834012bc2d2510bf1755232e07cba6a28411dda8f747f2120f1699d999`
- **Output content hash:** `sha256:466db18cfd6e9a03a0db4bc6dc3f4bebbfa9f2acd22e16b4c7ab6673842ab39f`

### verify_identity (`audit-0be52334b43d`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: r_min + (1 - r_min)*1**alpha == 1.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:44dbf603d42a52d982ca96059647d4f691393e1fcd16b7aaedaccac561b0523c`
- **Output content hash:** `sha256:4e906350f61a6e37a36c4106bbe8087e2d3babe220b2398406b6fd3f7eaebb98`

### wolfram_crosscheck (`audit-06d2e69c90ef`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0fb028fd918ebf41e7deb5dce54741939dbfa9a1ad0185b37ce92d8922aa63e8`
- **Output content hash:** `sha256:8b12be9aba4e496478f427b642de5c1555837f2ca3824201ee5ee41b941317d7`

### verify_identity (`audit-792aaac65981`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: r_min + (1 - r_min)*0**alpha == r_min.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- alpha > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:9764b7320d4ecf3a6997b742f3cdb65c41b178fde3e6432015e9acb3fd98e57f`
- **Output content hash:** `sha256:1d2f083d58561af04ca2ec39a6e840285ebe611daaa0c53bb9a82b5ade8bdaad`

### wolfram_crosscheck (`audit-c40475e8b89b`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0937659c3710395941c41b45781176f07164c86a4f049cdefa2a4b3d15dbfa10`
- **Output content hash:** `sha256:d384df3e90b5ef7783486ffec50c5e9c7ba09613a26bc2b9b3db38c148b128da`

### verify_identity (`audit-46be93fd00c9`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: lr * cos(0) * r_target * (r_target - r_target) == 0.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:69ee16efe2f261501eece803e69f53e4f103f3f0ca613cc428116c391675b010`
- **Output content hash:** `sha256:0640aa8ba15330345364ac78abc8da11d8d67ff047d464987666d91c50843bb1`

### wolfram_crosscheck (`audit-2222c7e81557`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 8 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:4074a0223ced89e37d5fb0db6f265579b54df10f846e4bffa230c83610557abe`
- **Output content hash:** `sha256:25935f183d434ee9dcee5cbfd64eeba90e154daa91e87eeb6eea8c2e70798a23`

### verify_identity (`audit-5090277ed905`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 3 ms
- **Summary:** Symbolic proof established: 2*lam*(K_c - K) == 2*lam*(K_c - K).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- K < K_c
- lam > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:79f990e1947fe7fe297712e6fc0609ca12df945169bf102adb9d69db67419d3a`
- **Output content hash:** `sha256:25e1b36392baedd55865fe7d2ffb3a69feb3609148049612de53b784adb77acb`

### wolfram_crosscheck (`audit-33ba1ec5107b`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:ce59d456744475fc9fae749568e3939a20d79157feb2410f23653473e0d032b6`
- **Output content hash:** `sha256:bde6e68bd568107e60533bc6f39ee5ca5854d9f64283f882abba89b822d6da54`

### check_constraint_model (`audit-42d9ef57473c`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 10 ms
- **Summary:** All 1 quer(y/ies) held: gpa-output-bounded: pass

**Reasoning:** gpa-output-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:947ec564234f48949b64cceb8a5c527de776578fdd57e2ddc4c484027e385003`
- **Output content hash:** `sha256:5a828dd0fbf8d7659d2a8b4fde27b1772294b79a0ca3e0da00e0d2ff85aa4fb8`

### check_constraint_model (`audit-461746574f7e`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 6 ms
- **Summary:** All 1 quer(y/ies) held: scalr-scale-bounded: pass

**Reasoning:** scalr-scale-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:675fa51852a393a2369d61b62780595efc41e23ede1eb2bcc2b572ff6c86a77b`
- **Output content hash:** `sha256:caa542cd4c61131c8fe02e3b8ff7e1199c09d15f53f802de8a21f13c65c7357d`

### check_constraint_model (`audit-e4a82d6b2025`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 8 ms
- **Summary:** All 1 quer(y/ies) held: penalty-non-negative: pass

**Reasoning:** penalty-non-negative: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:c648f0b159f18cea15273825a4b4ec6a0968f1349e0d558d5cbf76ecf86b9f27`
- **Output content hash:** `sha256:78945ca7016c8a5c676a154ed752e97fa951db3bc4ecc9aa7056338f78450a5c`

### check_constraint_model (`audit-dc558f788929`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 4 ms
- **Summary:** All 1 quer(y/ies) held: diagonal-always-zero: pass

**Reasoning:** diagonal-always-zero: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:2e0c1e2bfa23e1410726bb2aa516b322e395be8bbc7d4460e042140040f73c90`
- **Output content hash:** `sha256:1cda783a1fbe4208e1befd8ef31bd5101ecc0edb6e9c8bbcfb744d49f38b132f`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
