# Audit Evidence Report: bundle-184ec90b735d

**Overall status:** `FAIL`
**Policy profile:** `prin-ema` (`sha256:d19a23a4dff2c96be27ed82c26cd51cfb61bd3161583fce8b8f50aec39219053`)
**Generated:** 2026-08-20T02:40:30.161Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### HSL-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Hungarian similarity loss on a uniform (all-zero) NxN similarity matrix with temperature T=0.1 yields -log(1/N) = log(N). For N=2: all logits are 0, softmax is uniform over 2 classes, so -log(1/2) = ln(2). This verifies the cross-entropy-over-softmax-diagonal formula in losses.rs:28-44 reduces to the correct entropy of the uniform distribution.  
- **Code references:** crates/prin-train/src/losses.rs:28-44  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-d4380b623ee6

### DSILU-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The derivative of SiLU(z) = z*sigma(z) is sigma(z) + z*sigma(z)*(1-sigma(z)), which is exactly what d_silu computes. At z=0: sigma(0)=1/2, so dSiLU(0) = 1/2 + 0*(1/2)*(1/2) = 1/2. This verifies the activation formula in activations.rs:82-86.  
- **Code references:** crates/prin-train/src/activations.rs:82-86  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-30e422c5530e

### SCALR-LR-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** Scalr's compute_lr_scale at r=1 yields exactly 1 (full base lr when fully synchronized): r_min + (1-r_min)*1^alpha = r_min + 1 - r_min = 1, independent of r_min and alpha. This verifies scalr.rs:228-232.  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-a74b3293363e

### SCALR-LR-02 -- `FAIL`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Scalr's compute_lr_scale at r=0 yields exactly r_min (minimum lr fraction when fully desynchronized): r_min + (1-r_min)*0^alpha = r_min for any alpha > 0. This verifies the boundary behavior in scalr.rs:228-232.  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** a required check could not reach a proof or counterexample (INCONCLUSIVE)  
- **Contributing audits:** audit-0ea7711c4934

### RIP-HEBB-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** RIP Hebbian update with all-equal phases (synchronized, cos(0)=1) and amplitude exactly at target yields zero coupling change: delta = lr * cos(0) * r_target * (r_target - r_target) = lr * 1 * r_target * 0 = 0. This verifies rip.rs:195-218's core Hebbian formula at the equilibrium point.  
- **Code references:** crates/prin-train/src/rip.rs:195-218  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-64cfb7dd9dd4

### SYNC-PEN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** SyncGd's sync penalty gradient scale equals the derivative of the penalty with respect to the order parameter: d/dK[lambda*max(0, K_c-K)^2] = -2*lambda*max(0, K_c-K) for K < K_c, and 0 for K >= K_c. The code computes grad_scale = 2*lambda*deficit (the magnitude), used to reduce the effective learning rate. This verifies sync_gd.rs:267-278.  
- **Code references:** crates/prin-train/src/sync_gd.rs:267-278  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-3dcbe2e2f0b0

### GPA-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** GatedPhaseActivation's output is bounded in [0, 2*pi): the gate sigmoid produces values in [0,1], phase_activation produces values in [0, 2*pi), so their elementwise product is in [0, 2*pi). This is the load-bearing invariant for phase-valued oscillator outputs.  
- **Code references:** crates/prin-train/src/activations.rs:301-312, crates/prin-train/src/activations.rs:82-95  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-bb24f91d7bf8

### SCALR-SCALE-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** Scalr's compute_lr_scale output is bounded in [r_min, 1] for any clamped r in [0,1] and alpha >= 1: f(r) = r_min + (1-r_min)*r^alpha. Since r^alpha in [0,1] for r in [0,1] and alpha>=1, f(r) in [r_min, r_min + (1-r_min)] = [r_min, 1].  
- **Code references:** crates/prin-train/src/scalr.rs:228-232  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-3178bcb89a0c

### SYNC-PEN-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** SyncGd's compute_sync_penalty always returns a non-negative penalty: lambda*max(0, K_c-K)^2 >= 0 for lambda >= 0 and any K, K_c. The penalty is a squared term scaled by a non-negative weight.  
- **Code references:** crates/prin-train/src/sync_gd.rs:267-278  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-89d9f1eb8702

### RIP-DIAG-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** RIP's Hebbian update always produces a zero diagonal (no self-coupling): for any i, delta[i,i] * mask[i,i] = delta[i,i] * 0 = 0, since the mask is (1 - I) where I is the identity matrix. The diagonal of the updated coupling matrix is always zero regardless of the Hebbian delta values.  
- **Code references:** crates/prin-train/src/rip.rs:215-218  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-d02e27cab208

## Tool invocations

### verify_identity (`audit-d4380b623ee6`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 5 ms
- **Summary:** Symbolic proof established: -(1/2)*(log(exp(0/T)/(exp(0/T)+exp(0/T))) + log(exp(0/T)/(exp(0/T)+exp(0/T)))) == log(2).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:000f626c15dc18a7ef73d80b7bb140865ead2ad10d3067b264671f39559c3506`
- **Output content hash:** `sha256:57390ddf16310e9638cb5dfee30df07ed708b8933080d8d41ac6953adf63eec1`

### wolfram_crosscheck (`audit-4d7a21c316e0`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:731667d581ffbbadb32df00cc5c81576e027826e0a1a3c43bfbf84310d20c797`
- **Output content hash:** `sha256:03bed0614da500412760aa36f6fae3ab2b2e8516ce5d6eadb8fd879605cd2a7a`

### verify_identity (`audit-30e422c5530e`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 61 ms
- **Summary:** Symbolic proof established: 1/(1+exp(-z)) + z*(1/(1+exp(-z)))*(1 - 1/(1+exp(-z))) == 1/(1+exp(-z)) + z*exp(-z)/(1+exp(-z))**2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:7ce2baeb64c1890928f6264329b6fd3d6f9da044e0fb089568a721ef0499de79`
- **Output content hash:** `sha256:8dc51e07fa3f1c5b436b169384546a2bede892fda2aea0c91268908581fec28d`

### wolfram_crosscheck (`audit-190ece32b78c`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:c4e397834012bc2d2510bf1755232e07cba6a28411dda8f747f2120f1699d999`
- **Output content hash:** `sha256:6511456c27b98ca5c527754864efd73ae62040047dd687f4920bb90e9831b570`

### verify_identity (`audit-a74b3293363e`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Symbolic proof established: r_min + (1 - r_min)*1**alpha == 1.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:44dbf603d42a52d982ca96059647d4f691393e1fcd16b7aaedaccac561b0523c`
- **Output content hash:** `sha256:2ee2fe6035fee439aae78def1f5b7f39a0b9059c2838e063fe52b2738e5ff87d`

### wolfram_crosscheck (`audit-76f54a07aaed`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0fb028fd918ebf41e7deb5dce54741939dbfa9a1ad0185b37ce92d8922aa63e8`
- **Output content hash:** `sha256:a4e809d2b3ae3268790639cd3fb69350d7ddac48ff3997fc019c7489ec60bfd3`

### verify_identity (`audit-0ea7711c4934`) -- `INCONCLUSIVE`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 216 ms
- **Summary:** Numeric agreement across 20 sampled point(s), but policy requires symbolic proof for PASS.

**Reasoning:** No counterexample was found numerically, but the active policy profile does not permit probabilistic numeric evidence alone to yield a PASS verdict for an identity claim.

**Assumptions:**
- alpha > 0

**Limitations:**
- Symbolic proof was not established; only finite numeric evidence is available.

**Residuals:**
- {'r_min': -9.850170598828257, 'alpha': 8.219519248982483}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': 8.785379947275281, 'alpha': 1.6445514611789829}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': -9.3837195654678, 'alpha': 5.77545434472567}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': -3.078220688057538, 'alpha': 2.46562950078337}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': 1.1286512111243123, 'alpha': 2.892684683565655}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': -5.016957572775819, 'alpha': 8.670309960846932}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': -0.9322396104701287, 'alpha': 0.6032241382318055}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': -9.614008673805664, 'alpha': 0.16203851559584415}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': -8.916496027077143, 'alpha': 1.750570162621388}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': -6.719935525160777, 'alpha': 1.146604748829363}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': -7.115085567961835, 'alpha': 8.746141693924493}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': 5.419599430395499, 'alpha': 9.138662446988107}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': -6.908589705784207, 'alpha': 9.094373114047897}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': -6.90897199821914, 'alpha': 6.677785883024637}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': 6.3468801371628345, 'alpha': 7.631351973112128}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': -1.2080720464072066, 'alpha': 5.62127195584962}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': 0.5959828351576633, 'alpha': 6.588423228348848}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': -0.29597694027130217, 'alpha': 6.354680034036079}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': 3.1278324507883664, 'alpha': 2.820860623033809}: 0.0 (tolerance 1e-08, within: True)
- {'r_min': -3.0930214959147957, 'alpha': 4.053178980966496}: 0.0 (tolerance 1e-08, within: True)

- **Random seed:** 1234
- **Input content hash:** `sha256:9764b7320d4ecf3a6997b742f3cdb65c41b178fde3e6432015e9acb3fd98e57f`
- **Output content hash:** `sha256:a714f8e1d8300ca0b8379169726f5f202b8b9007a9db55dd99603cceee9c9644`

### wolfram_crosscheck (`audit-00534a499905`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0937659c3710395941c41b45781176f07164c86a4f049cdefa2a4b3d15dbfa10`
- **Output content hash:** `sha256:679dfe052065367d32c1a0da01b0590800d84bdc80f8c52400df02b27dde226b`

### verify_identity (`audit-64cfb7dd9dd4`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 3 ms
- **Summary:** Symbolic proof established: lr * cos(0) * r_target * (r_target - r_target) == 0.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:69ee16efe2f261501eece803e69f53e4f103f3f0ca613cc428116c391675b010`
- **Output content hash:** `sha256:29e87f64bb2cadda98408399f6957d94eb2127f112e418719cf2d974c4a18ce1`

### wolfram_crosscheck (`audit-5057de4c6f2a`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:4074a0223ced89e37d5fb0db6f265579b54df10f846e4bffa230c83610557abe`
- **Output content hash:** `sha256:f94f17426be8e96a5b1d93605a5da7d7580fb2c51d151dea24ce56d2579d8cf3`

### verify_identity (`audit-3dcbe2e2f0b0`) -- `PASS`

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
- **Output content hash:** `sha256:bf766200282cfbe054c4eba41ec081a6cebe90ac01e7f1181752444c62665b42`

### wolfram_crosscheck (`audit-e92204e0bd90`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:ce59d456744475fc9fae749568e3939a20d79157feb2410f23653473e0d032b6`
- **Output content hash:** `sha256:77b3e03034c5deb3bce60751bbb3a934e46ee7d8c376a1a37c9e5a8f3c553d59`

### check_constraint_model (`audit-bb24f91d7bf8`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 8 ms
- **Summary:** All 1 quer(y/ies) held: gpa-output-bounded: pass

**Reasoning:** gpa-output-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:947ec564234f48949b64cceb8a5c527de776578fdd57e2ddc4c484027e385003`
- **Output content hash:** `sha256:6c2bffa646ffb27633aa0d92880aa6a01a4c2fbf196aa5648ac52c19c6444c00`

### check_constraint_model (`audit-3178bcb89a0c`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 7 ms
- **Summary:** All 1 quer(y/ies) held: scalr-scale-bounded: pass

**Reasoning:** scalr-scale-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:675fa51852a393a2369d61b62780595efc41e23ede1eb2bcc2b572ff6c86a77b`
- **Output content hash:** `sha256:f233405b27a7ae507ca4c36381627cf64905e3db47b4c3cfaa632c16fe1a042b`

### check_constraint_model (`audit-89d9f1eb8702`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 6 ms
- **Summary:** All 1 quer(y/ies) held: penalty-non-negative: pass

**Reasoning:** penalty-non-negative: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:c648f0b159f18cea15273825a4b4ec6a0968f1349e0d558d5cbf76ecf86b9f27`
- **Output content hash:** `sha256:2a56e46b1f722a2821e95056fabbf872a6bb57ca3a91ec185e7e699565b96b21`

### check_constraint_model (`audit-d02e27cab208`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** All 1 quer(y/ies) held: diagonal-always-zero: pass

**Reasoning:** diagonal-always-zero: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:2e0c1e2bfa23e1410726bb2aa516b322e395be8bbc7d4460e042140040f73c90`
- **Output content hash:** `sha256:847d65fd343d7d50bc9392290943ff6c327f1b514218c475dc60e7aea4194592`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
