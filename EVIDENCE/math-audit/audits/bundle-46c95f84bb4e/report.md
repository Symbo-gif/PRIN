# Audit Evidence Report: bundle-46c95f84bb4e

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:d19a23a4dff2c96be27ed82c26cd51cfb61bd3161583fce8b8f50aec39219053`)
**Generated:** 2026-08-18T03:16:59.528Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### GPU-RK4-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** The GPU mean-field RK4 finalize kernel (mean_field_rk4_finalize in mean_field_rk4/cubecl.rs:213-237) computes the standard classical RK4 weighted sum: y_{n+1} = y_n + dt/6 * (k1 + 2*(k2 + k3) + k4), with Butcher tableau coefficients (1/6, 2/6, 2/6, 1/6) = (1/6, 1/3, 1/3, 1/6). This is the same weighted-sum formula the CPU RK4 path uses (integrate.rs:406-503), verified independently by EMA-001 claim INT-02 at the ODE-property level. The GPU kernel implements it as: base + dt/6 * (k1 + 2*(k2 + k3) + k4), which is algebraically identical.  
- **Code references:** crates/prin-kernels/src/mean_field_rk4/cubecl.rs:213-237, crates/prin-dynamics/src/integrate.rs:406-503  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-d3f67936ea91

### GPU-RED-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The hierarchical device-side reduction used by order_param_block_reduce, complex_order_reduce, pac_phase_sum_block_reduce, and real_sum_reduce (each 256-thread cube block sums its slice into one f32 partial sum, then the host accumulates ceil(N/256) partial sums in f64) is mathematically equivalent to a flat sum over all N elements. Instantiated at N=512 (2 blocks of 256): sum(a_0..a_511) = sum(a_0..a_255) + sum(a_256..a_511). The f32/f64 precision split introduces numerical (not mathematical) error, bounded by f32 machine epsilon per partial sum; the kernel-equivalence test suite (113 CUDA tests at rtol=1e-5, atol=1e-6) covers the numerical bound. This claim verifies the mathematical decomposition is exact over the reals.  
- **Code references:** crates/prin-kernels/src/mean_field_rk4/cubecl.rs:153-186, crates/prin-kernels/src/discrete_step/cubecl.rs:97-128, crates/prin-kernels/src/pac/cubecl.rs:44-67  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-a24924067d8a

### GPU-KNN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The sparse k-NN coupling kernel (sparse_knn_coupling in sparse_knn/cubecl.rs:43-89) normalizes coupling strength by K/degree(i) per edge, so that the total coupling contribution to the phase derivative for oscillator i is: sum_{j in NN(i)} (K/degree(i)) * sin(phi_j - phi_i) * amp_j. When all amplitudes equal 1 and all phases equal 0 (uniform field, perfect synchrony), every sin(phi_j - phi_i) = sin(0) = 0, so the total coupling is exactly 0 regardless of the graph structure or degree sequence. This is the same coupling normalization the CPU reference uses (sparse_knn.rs) and is required for the coupling to be intensive (independent of network size) rather than extensive.  
- **Code references:** crates/prin-kernels/src/sparse_knn/cubecl.rs:43-89, crates/prin-kernels/src/sparse_knn.rs:1-50  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-4a60812552a5

## Tool invocations

### verify_identity (`audit-d3f67936ea91`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 38 ms
- **Summary:** Symbolic proof established: y + (dt/6)*(k1 + 2*(k2 + k3) + k4) == y + (dt/6)*k1 + (dt/3)*k2 + (dt/3)*k3 + (dt/6)*k4.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:92483bf45fa9265fa1a7c5f18289024b259bd5575b6d519489fd803ecef66ed6`
- **Output content hash:** `sha256:c460fe0e3177c22495510a7c2b2d249eb78c58bf55f3947cfed2312398f409ef`

### wolfram_crosscheck (`audit-f0c441237363`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:aaa962cea8f8b8160f283606f60085ef4e150721b375cb9c7e1a1f661a699aaf`
- **Output content hash:** `sha256:15b8341eaaafdc30ef77e21b14f58c3db523c4811ce4a6a62945c7e66a485540`

### verify_identity (`audit-a24924067d8a`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 3 ms
- **Summary:** Symbolic proof established: a0 + a1 + a2 + a3 + a4 + a5 + a6 + a7 == (a0 + a1 + a2 + a3) + (a4 + a5 + a6 + a7).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:7f2d2083931062bd5b9a02ab430ee6ee7ce4a749f8284900fdbe23f3203f2685`
- **Output content hash:** `sha256:7cea56dfe6106c2d53aa810f4eca62ffe3ff6ecf5cccecc2138e7b5d0ffd7a64`

### wolfram_crosscheck (`audit-773acd2d8625`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:4ecd817024ff4f2cceaf822ad95de38232630814b75f3c11ab683d5b0df3a60a`
- **Output content hash:** `sha256:f6a05671b5ee4f88e095924c8473ac02796ad3fa5bb505a889d95046dfcc96fb`

### verify_identity (`audit-4a60812552a5`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 3 ms
- **Summary:** Symbolic proof established: (K/d)*sin(0 - 0) + (K/d)*sin(0 - 0) + (K/d)*sin(0 - 0) == 0.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:c4210d72a21e73170f2cb11a4e80c88be957ea404d727b1f3a27cb45b9df688b`
- **Output content hash:** `sha256:9ba6796ff83f24fa048ef372b151892170f88f3e6daf8b976d4b64303e084d1c`

### wolfram_crosscheck (`audit-9b42d05a0bda`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:8752c904cf65ff3948816013d5a674f0d274a858a28af435a6ae8ca6c4adf4b2`
- **Output content hash:** `sha256:b0c3637d94184d6f51dfc374efd42dddfe8266a04727fd6fa445c814b3bee0cb`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
