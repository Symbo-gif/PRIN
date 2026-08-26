# Audit Evidence Report: bundle-b572520d9da2

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-08-26T05:07:44.144Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### GPU-RK4-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** The GPU mean-field RK4 finalize kernel (mean_field_rk4_finalize in mean_field_rk4/cubecl.rs:213-237) computes the standard classical RK4 weighted sum: y_{n+1} = y_n + dt/6 * (k1 + 2*(k2 + k3) + k4), with Butcher tableau coefficients (1/6, 2/6, 2/6, 1/6) = (1/6, 1/3, 1/3, 1/6). This is the same weighted-sum formula the CPU RK4 path uses (integrate.rs:406-503), verified independently by EMA-001 claim INT-02 at the ODE-property level. The GPU kernel implements it as: base + dt/6 * (k1 + 2*(k2 + k3) + k4), which is algebraically identical.  
- **Code references:** crates/prin-kernels/src/mean_field_rk4/cubecl.rs:213-237, crates/prin-dynamics/src/integrate.rs:406-503  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-122bc0d1c513

### GPU-RED-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The hierarchical device-side reduction used by order_param_block_reduce, complex_order_reduce, pac_phase_sum_block_reduce, and real_sum_reduce (each 256-thread cube block sums its slice into one f32 partial sum, then the host accumulates ceil(N/256) partial sums in f64) is mathematically equivalent to a flat sum over all N elements. Instantiated at N=512 (2 blocks of 256): sum(a_0..a_511) = sum(a_0..a_255) + sum(a_256..a_511). The f32/f64 precision split introduces numerical (not mathematical) error, bounded by f32 machine epsilon per partial sum; the kernel-equivalence test suite (113 CUDA tests at rtol=1e-5, atol=1e-6) covers the numerical bound. This claim verifies the mathematical decomposition is exact over the reals.  
- **Code references:** crates/prin-kernels/src/mean_field_rk4/cubecl.rs:153-186, crates/prin-kernels/src/discrete_step/cubecl.rs:97-128, crates/prin-kernels/src/pac/cubecl.rs:44-67  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-03818b23d05e

### GPU-KNN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The sparse k-NN coupling kernel (sparse_knn_coupling in sparse_knn/cubecl.rs:43-89) normalizes coupling strength by K/degree(i) per edge, so that the total coupling contribution to the phase derivative for oscillator i is: sum_{j in NN(i)} (K/degree(i)) * sin(phi_j - phi_i) * amp_j. When all amplitudes equal 1 and all phases equal 0 (uniform field, perfect synchrony), every sin(phi_j - phi_i) = sin(0) = 0, so the total coupling is exactly 0 regardless of the graph structure or degree sequence. This is the same coupling normalization the CPU reference uses (sparse_knn.rs) and is required for the coupling to be intensive (independent of network size) rather than extensive.  
- **Code references:** crates/prin-kernels/src/sparse_knn/cubecl.rs:43-89, crates/prin-kernels/src/sparse_knn.rs:1-50  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-d2578da09772

## Tool invocations

### verify_identity (`audit-122bc0d1c513`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 33 ms
- **Summary:** Symbolic proof established: y + (dt/6)*(k1 + 2*(k2 + k3) + k4) == y + (dt/6)*k1 + (dt/3)*k2 + (dt/3)*k3 + (dt/6)*k4.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:92483bf45fa9265fa1a7c5f18289024b259bd5575b6d519489fd803ecef66ed6`
- **Output content hash:** `sha256:72c670380e472d92155146ce6db79e94139e5e098bb882c59c6b407c4d58f5ef`

### wolfram_crosscheck (`audit-c71a6f8ada44`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:aaa962cea8f8b8160f283606f60085ef4e150721b375cb9c7e1a1f661a699aaf`
- **Output content hash:** `sha256:4a8bce6ae5bd097ba4a698a7ba613daeeb23d55edf188d38fd170ad5758ef3f5`

### verify_identity (`audit-03818b23d05e`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Symbolic proof established: a0 + a1 + a2 + a3 + a4 + a5 + a6 + a7 == (a0 + a1 + a2 + a3) + (a4 + a5 + a6 + a7).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:7f2d2083931062bd5b9a02ab430ee6ee7ce4a749f8284900fdbe23f3203f2685`
- **Output content hash:** `sha256:b6cbcaaf8b560931b83923f212284d87e52dce2b7b0290aa3dc2d8205608eaf7`

### wolfram_crosscheck (`audit-22e68f5482d9`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:4ecd817024ff4f2cceaf822ad95de38232630814b75f3c11ab683d5b0df3a60a`
- **Output content hash:** `sha256:11559f5bebf174193a16fc82cd48d4c975a77983d8f5b93c870828d239abedb2`

### verify_identity (`audit-d2578da09772`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Symbolic proof established: (K/d)*sin(0 - 0) + (K/d)*sin(0 - 0) + (K/d)*sin(0 - 0) == 0.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:c4210d72a21e73170f2cb11a4e80c88be957ea404d727b1f3a27cb45b9df688b`
- **Output content hash:** `sha256:fc89c7b1bdf923ae85785cc460fc3ba19628ed5942436a48c2a00cbc7aa0b70d`

### wolfram_crosscheck (`audit-0eb18fac8539`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:8752c904cf65ff3948816013d5a674f0d274a858a28af435a6ae8ca6c4adf4b2`
- **Output content hash:** `sha256:1389ee680984a1722943977d4acde8ba7971f3be71a261657a3e66fbd16efe79`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
