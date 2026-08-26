# Audit Evidence Report: bundle-e9b63d7a12c3

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-08-26T05:06:29.705Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### GPU-RK4-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** The GPU mean-field RK4 finalize kernel (mean_field_rk4_finalize in mean_field_rk4/cubecl.rs:213-237) computes the standard classical RK4 weighted sum: y_{n+1} = y_n + dt/6 * (k1 + 2*(k2 + k3) + k4), with Butcher tableau coefficients (1/6, 2/6, 2/6, 1/6) = (1/6, 1/3, 1/3, 1/6). This is the same weighted-sum formula the CPU RK4 path uses (integrate.rs:406-503), verified independently by EMA-001 claim INT-02 at the ODE-property level. The GPU kernel implements it as: base + dt/6 * (k1 + 2*(k2 + k3) + k4), which is algebraically identical.  
- **Code references:** crates/prin-kernels/src/mean_field_rk4/cubecl.rs:213-237, crates/prin-dynamics/src/integrate.rs:406-503  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-254c9a2fadd5

### GPU-RED-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The hierarchical device-side reduction used by order_param_block_reduce, complex_order_reduce, pac_phase_sum_block_reduce, and real_sum_reduce (each 256-thread cube block sums its slice into one f32 partial sum, then the host accumulates ceil(N/256) partial sums in f64) is mathematically equivalent to a flat sum over all N elements. Instantiated at N=512 (2 blocks of 256): sum(a_0..a_511) = sum(a_0..a_255) + sum(a_256..a_511). The f32/f64 precision split introduces numerical (not mathematical) error, bounded by f32 machine epsilon per partial sum; the kernel-equivalence test suite (113 CUDA tests at rtol=1e-5, atol=1e-6) covers the numerical bound. This claim verifies the mathematical decomposition is exact over the reals.  
- **Code references:** crates/prin-kernels/src/mean_field_rk4/cubecl.rs:153-186, crates/prin-kernels/src/discrete_step/cubecl.rs:97-128, crates/prin-kernels/src/pac/cubecl.rs:44-67  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-73eeaabeec52

### GPU-KNN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The sparse k-NN coupling kernel (sparse_knn_coupling in sparse_knn/cubecl.rs:43-89) normalizes coupling strength by K/degree(i) per edge, so that the total coupling contribution to the phase derivative for oscillator i is: sum_{j in NN(i)} (K/degree(i)) * sin(phi_j - phi_i) * amp_j. When all amplitudes equal 1 and all phases equal 0 (uniform field, perfect synchrony), every sin(phi_j - phi_i) = sin(0) = 0, so the total coupling is exactly 0 regardless of the graph structure or degree sequence. This is the same coupling normalization the CPU reference uses (sparse_knn.rs) and is required for the coupling to be intensive (independent of network size) rather than extensive.  
- **Code references:** crates/prin-kernels/src/sparse_knn/cubecl.rs:43-89, crates/prin-kernels/src/sparse_knn.rs:1-50  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-3cc9cf65ddf9

## Tool invocations

### verify_identity (`audit-254c9a2fadd5`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 39 ms
- **Summary:** Symbolic proof established: y + (dt/6)*(k1 + 2*(k2 + k3) + k4) == y + (dt/6)*k1 + (dt/3)*k2 + (dt/3)*k3 + (dt/6)*k4.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:92483bf45fa9265fa1a7c5f18289024b259bd5575b6d519489fd803ecef66ed6`
- **Output content hash:** `sha256:93fb43b302575f406f1264007feefd896a4f88cd7d0909d39fd62b313a987576`

### wolfram_crosscheck (`audit-282c302fd736`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:aaa962cea8f8b8160f283606f60085ef4e150721b375cb9c7e1a1f661a699aaf`
- **Output content hash:** `sha256:15139cd49421d9df3c97130cf6dcd33eddca39c3d7b67d8adb5f49df6511984f`

### verify_identity (`audit-73eeaabeec52`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: a0 + a1 + a2 + a3 + a4 + a5 + a6 + a7 == (a0 + a1 + a2 + a3) + (a4 + a5 + a6 + a7).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:7f2d2083931062bd5b9a02ab430ee6ee7ce4a749f8284900fdbe23f3203f2685`
- **Output content hash:** `sha256:cf61f38ebf3d09f6549efe3c7594a06d271b920e295c3eeec9eb129f83cb44f8`

### wolfram_crosscheck (`audit-140474259fd2`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:4ecd817024ff4f2cceaf822ad95de38232630814b75f3c11ab683d5b0df3a60a`
- **Output content hash:** `sha256:7268726e89e08821e846a818a76cb3d490b8c7853a55660826a934a523de09d6`

### verify_identity (`audit-3cc9cf65ddf9`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: (K/d)*sin(0 - 0) + (K/d)*sin(0 - 0) + (K/d)*sin(0 - 0) == 0.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:c4210d72a21e73170f2cb11a4e80c88be957ea404d727b1f3a27cb45b9df688b`
- **Output content hash:** `sha256:27ad5ad3628f601449a46bbe9f6983e8c3f10f9d3d27d2aec6a507f8a8ec92a9`

### wolfram_crosscheck (`audit-6e4ed5aa5251`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:8752c904cf65ff3948816013d5a674f0d274a858a28af435a6ae8ca6c4adf4b2`
- **Output content hash:** `sha256:8d4742f8a4e95e000f4410e0be0f7159b296cc33e3ca248a785f54cbe5910f70`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
