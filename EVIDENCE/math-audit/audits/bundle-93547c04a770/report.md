# Audit Evidence Report: bundle-93547c04a770

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:d19a23a4dff2c96be27ed82c26cd51cfb61bd3161583fce8b8f50aec39219053`)
**Generated:** 2026-08-20T02:40:29.348Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### GPU-RK4-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** The GPU mean-field RK4 finalize kernel (mean_field_rk4_finalize in mean_field_rk4/cubecl.rs:213-237) computes the standard classical RK4 weighted sum: y_{n+1} = y_n + dt/6 * (k1 + 2*(k2 + k3) + k4), with Butcher tableau coefficients (1/6, 2/6, 2/6, 1/6) = (1/6, 1/3, 1/3, 1/6). This is the same weighted-sum formula the CPU RK4 path uses (integrate.rs:406-503), verified independently by EMA-001 claim INT-02 at the ODE-property level. The GPU kernel implements it as: base + dt/6 * (k1 + 2*(k2 + k3) + k4), which is algebraically identical.  
- **Code references:** crates/prin-kernels/src/mean_field_rk4/cubecl.rs:213-237, crates/prin-dynamics/src/integrate.rs:406-503  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-4cc19bf99421

### GPU-RED-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The hierarchical device-side reduction used by order_param_block_reduce, complex_order_reduce, pac_phase_sum_block_reduce, and real_sum_reduce (each 256-thread cube block sums its slice into one f32 partial sum, then the host accumulates ceil(N/256) partial sums in f64) is mathematically equivalent to a flat sum over all N elements. Instantiated at N=512 (2 blocks of 256): sum(a_0..a_511) = sum(a_0..a_255) + sum(a_256..a_511). The f32/f64 precision split introduces numerical (not mathematical) error, bounded by f32 machine epsilon per partial sum; the kernel-equivalence test suite (113 CUDA tests at rtol=1e-5, atol=1e-6) covers the numerical bound. This claim verifies the mathematical decomposition is exact over the reals.  
- **Code references:** crates/prin-kernels/src/mean_field_rk4/cubecl.rs:153-186, crates/prin-kernels/src/discrete_step/cubecl.rs:97-128, crates/prin-kernels/src/pac/cubecl.rs:44-67  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-f594173e451b

### GPU-KNN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The sparse k-NN coupling kernel (sparse_knn_coupling in sparse_knn/cubecl.rs:43-89) normalizes coupling strength by K/degree(i) per edge, so that the total coupling contribution to the phase derivative for oscillator i is: sum_{j in NN(i)} (K/degree(i)) * sin(phi_j - phi_i) * amp_j. When all amplitudes equal 1 and all phases equal 0 (uniform field, perfect synchrony), every sin(phi_j - phi_i) = sin(0) = 0, so the total coupling is exactly 0 regardless of the graph structure or degree sequence. This is the same coupling normalization the CPU reference uses (sparse_knn.rs) and is required for the coupling to be intensive (independent of network size) rather than extensive.  
- **Code references:** crates/prin-kernels/src/sparse_knn/cubecl.rs:43-89, crates/prin-kernels/src/sparse_knn.rs:1-50  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-10512ff9dc57

## Tool invocations

### verify_identity (`audit-4cc19bf99421`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 35 ms
- **Summary:** Symbolic proof established: y + (dt/6)*(k1 + 2*(k2 + k3) + k4) == y + (dt/6)*k1 + (dt/3)*k2 + (dt/3)*k3 + (dt/6)*k4.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:92483bf45fa9265fa1a7c5f18289024b259bd5575b6d519489fd803ecef66ed6`
- **Output content hash:** `sha256:73e63335b73580a257bdaab8595516b8e39b899b28fc941cf93a1894272c0943`

### wolfram_crosscheck (`audit-4c59144e6f33`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:aaa962cea8f8b8160f283606f60085ef4e150721b375cb9c7e1a1f661a699aaf`
- **Output content hash:** `sha256:b042199bc6ff16cd6dc52c7fb45283ee97135f0c2a7dcdfac1ab5b03b5a04d8a`

### verify_identity (`audit-f594173e451b`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: a0 + a1 + a2 + a3 + a4 + a5 + a6 + a7 == (a0 + a1 + a2 + a3) + (a4 + a5 + a6 + a7).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:7f2d2083931062bd5b9a02ab430ee6ee7ce4a749f8284900fdbe23f3203f2685`
- **Output content hash:** `sha256:a78ba223b44554267c01ac33a82ceee5b6c4fe14a26311d14521d9e8ca4f63f5`

### wolfram_crosscheck (`audit-daa0e278ca2d`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 3 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:4ecd817024ff4f2cceaf822ad95de38232630814b75f3c11ab683d5b0df3a60a`
- **Output content hash:** `sha256:1d62421f26c3aee09932f5d37e56efcc65fc5799ef3d6b3d20965b791a000a81`

### verify_identity (`audit-10512ff9dc57`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 23 ms
- **Summary:** Symbolic proof established: (K/d)*sin(0 - 0) + (K/d)*sin(0 - 0) + (K/d)*sin(0 - 0) == 0.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:c4210d72a21e73170f2cb11a4e80c88be957ea404d727b1f3a27cb45b9df688b`
- **Output content hash:** `sha256:958a2c101ac126d59d4d8ec5a8f8f858f8de51f1ffefd5aa688da8d760351f8b`

### wolfram_crosscheck (`audit-bf8c009e8cc7`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:8752c904cf65ff3948816013d5a674f0d274a858a28af435a6ae8ca6c4adf4b2`
- **Output content hash:** `sha256:1da6e96998468c1abe2820179df87eb1286e6c4a2d0226f3c8222342fd1eec65`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
