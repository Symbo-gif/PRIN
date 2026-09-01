# Audit Evidence Report: bundle-52fd5abec367

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T20:00:23.467Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### PD-01-SIN -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** safe_phase_diff(a,b) = atan2(sin(a-b), cos(a-b)) preserves sin(a-b) exactly, which is the load-bearing property integrate.rs:26-31 relies on to skip wrapping phase differences at RK stages.  
- **Code references:** crates/prin-dynamics/src/state.rs:284-291, crates/prin-dynamics/src/integrate.rs:26-31  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-0488f6da94df

### PD-01-COS -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** safe_phase_diff(a,b) = atan2(sin(a-b), cos(a-b)) preserves cos(a-b) exactly, the companion identity to PD-01-SIN.  
- **Code references:** crates/prin-dynamics/src/state.rs:284-291, crates/prin-dynamics/src/integrate.rs:26-31  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-c9c0a30d733a

### MF-01-PHASE -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For N=2, the mean-field Kuramoto phase-velocity term K*R*sin(psi-phi0) (with R*e^{i*psi} the complex order parameter over BOTH oscillators, i.e. including the self term) equals the full-matrix form K/2 * sum_j r_j*sin(phi_j - phi0) with self-coupling included.  
- **Code references:** crates/prin-dynamics/src/models.rs:191-231, crates/prin-dynamics/src/models.rs:233-281  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-d63d235a1198

### MF-01-AMPLITUDE -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** The companion amplitude-channel identity to MF-01-PHASE: K*R*cos(psi-phi0) equals K/2 * sum_j r_j*cos(phi_j - phi0) with self-coupling included. Because cos(0)=1 (unlike sin(0)=0), the self term contributes non-trivially here -- this is the channel where prin-dynamics::coupling's zero-diagonal build_all_to_all matrix would NOT reproduce mean-field coupling if fed through CouplingMode::Full (see finding MF-DIAG in the audit report).  
- **Code references:** crates/prin-dynamics/src/models.rs:191-231, crates/prin-dynamics/src/models.rs:226, crates/prin-dynamics/src/coupling.rs:193-201  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-b190a60f6815

### SL-01-RADIAL -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For z = r*e^{i*phi} and dz/dt = (mu + i*omega)*z - |z|^2*z, the radial component dr/dt = Re(dz * e^{-i*phi}) reduces exactly to mu*r - r^3.  
- **Code references:** crates/prin-dynamics/src/models.rs:473-480, crates/prin-dynamics/src/models.rs:371-373  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-39f9b6ad0b63

### SL-01-ANGULAR -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For the same Stuart-Landau flow, the angular component dphi/dt = Im(dz * e^{-i*phi}) / r reduces exactly to omega (constant, independent of r), for r > 0.  
- **Code references:** crates/prin-dynamics/src/models.rs:473-480, crates/prin-dynamics/src/models.rs:602-611  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-4ad55c1d91a6

### MPC-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** Mean phase coherence MPC = mean over pairs i<j of cos(phi_i - phi_j) equals (N*R^2 - 1)/(N - 1) for N=3, an exact algebraic consistency constraint between coherence.rs's O(N^2) pairwise sum and order.rs's order parameter R.  
- **Code references:** crates/prin-metrics/src/coherence.rs:39-57, crates/prin-metrics/src/order.rs:59-71  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-1c42e28acd58

### PSD-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Parseval's theorem for the unnormalized 2-point DFT periodogram used by spectral.rs: sum_k |X[k]|^2 = M * sum_n A_n^2 for x_n = A_n*e^{i*phi_n}, instantiated at N=M=2.  
- **Code references:** crates/prin-metrics/src/spectral.rs:24-27, crates/prin-metrics/src/spectral.rs:48-92  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-7fd175c59e8f

## Tool invocations

### verify_identity (`audit-0488f6da94df`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 153 ms
- **Summary:** Symbolic proof established: sin(atan2(sin(a - b), cos(a - b))) == sin(a - b).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:cc8ac758a054a712ad6bcb3dcab5108a9019bb11bfcdaddef96e9a3cc12c7dca`
- **Output content hash:** `sha256:897241e3a71d845f184a60b7e3681b5a9f92a459806195d2c14191c89b1bea57`

### wolfram_crosscheck (`audit-de40ce9d9607`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:443e03490196e173d6f94df39be70a10653ece2b872c19b88528950c529e3cd1`
- **Output content hash:** `sha256:525f8aeb9af0af1b97fd669fed5c576f296c9330e1427acb2214fb1e6480a20e`

### verify_identity (`audit-c9c0a30d733a`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 373 ms
- **Summary:** Symbolic proof established: cos(atan2(sin(a - b), cos(a - b))) == cos(a - b).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:d57dc6e6fdd9f80f101f3053556cdd0dd619328766c37fb69dbe80a616ffebaa`
- **Output content hash:** `sha256:407317c5962c9ce7503e415c8918e0b41309e8765a6c31c47d5ad9a64ce86225`

### wolfram_crosscheck (`audit-17a346fb5649`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:755ce3d683f8507311380e6995ac506129bf3cffc11039434a546e073143535f`
- **Output content hash:** `sha256:1691452f8c67d1471c543f7785cee5686c9398ac73b1b3a3586a768bf7bc65d5`

### verify_identity (`audit-d63d235a1198`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 2960 ms
- **Summary:** Symbolic proof established: K*sqrt(((r0*cos(p0) + r1*cos(p1))/2)**2 + ((r0*sin(p0) + r1*sin(p1))/2)**2)*sin(atan2((r0*sin(p0) + r1*sin(p1))/2, (r0*cos(p0) + r1*cos(p1))/2) - p0) == K*(r0*sin(p0 - p0) + r1*sin(p1 - p0))/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:e9f149975d6623a02ad7f45dfbf28e98dcbb6bebfbd28d750b3dc3d3c44ff634`
- **Output content hash:** `sha256:a1f38215e1152d97ce2888dcea96f849fc15b27cd1c1ff2ee2ddcaac60e3a679`

### wolfram_crosscheck (`audit-0dd7ce267e4f`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:fa721f9b663e925b435a7aa613aa1d3ec1bb3a9cab15116483793b33e2ebe1ef`
- **Output content hash:** `sha256:d674e0202995d79f51e2501f667dd07429cae280f74404c558ef30481c9fa7bf`

### verify_identity (`audit-b190a60f6815`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 3043 ms
- **Summary:** Symbolic proof established: K*sqrt(((r0*cos(p0) + r1*cos(p1))/2)**2 + ((r0*sin(p0) + r1*sin(p1))/2)**2)*cos(atan2((r0*sin(p0) + r1*sin(p1))/2, (r0*cos(p0) + r1*cos(p1))/2) - p0) == K*(r0*cos(p0 - p0) + r1*cos(p1 - p0))/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:0ff1be2bafe7dfc8d6d1e9a0627c95107f31615f78ae631db9a964de6866bafe`
- **Output content hash:** `sha256:1c889ab256e3edda3136c90ca3550e1d09de91270ace33575a8a15211e4ecdae`

### wolfram_crosscheck (`audit-1951bd9f5ab5`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:a705fb9ce8059372b327b7fbaeb5d81f2d6a263aed5652a598b590aaefaabc95`
- **Output content hash:** `sha256:948b8e94f60048cef9ab4edb7041635d583a6671f59ae5f2b1ffba54a7d91bd8`

### verify_identity (`audit-39f9b6ad0b63`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 418 ms
- **Summary:** Symbolic proof established: re(((mu + I*w)*(r*exp(I*p)) - r**2*(r*exp(I*p)))*exp(-I*p)) == mu*r - r**3.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:77e0f8377ae09a85bbcd7e1f8d5cdfeb0a2b30bef0944a7886ca722a65a89468`
- **Output content hash:** `sha256:34fb55297694d09b0d8ea8793b56f946b7f50f8226cf3576f03b6e414ed84f1b`

### wolfram_crosscheck (`audit-eda542724596`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:42689b00b5a8d06ace77cc5ca53bd449f5043d4bd2682f57c868063d8679cc41`
- **Output content hash:** `sha256:bbc1050d618f4d27a96cba2dbfc801619a17aa371607e84193123b43633fbece`

### verify_identity (`audit-4ad55c1d91a6`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 432 ms
- **Summary:** Symbolic proof established: im(((mu + I*w)*(r*exp(I*p)) - r**2*(r*exp(I*p)))*exp(-I*p))/r == w.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- r > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:aea1bfd3dfe50a2295ddfb4697b3d09fca05533fb396ea93d197e7cf15d295ed`
- **Output content hash:** `sha256:34282522c776c775dbeea474cf1542da76750416ad7f9167a303c29ee32f3932`

### wolfram_crosscheck (`audit-8656d1433bdf`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0923170bb89d305fcd4b264d1db1494a8b6e35e86e8ba8c68149a14b880654c2`
- **Output content hash:** `sha256:fa6a03470065937a79a7969d0f8a99d5c0003f7e07ff8d6256b0bfb38a6e36e9`

### verify_identity (`audit-1c42e28acd58`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 686 ms
- **Summary:** Symbolic proof established: (cos(p0 - p1) + cos(p0 - p2) + cos(p1 - p2))/3 == (3*(((cos(p0) + cos(p1) + cos(p2))/3)**2 + ((sin(p0) + sin(p1) + sin(p2))/3)**2) - 1)/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:1bcf1f95c40fe0ab8a7a10b5d64b8057b04336fc9f2c65c67d4db0d1778ca741`
- **Output content hash:** `sha256:eedde7f22a10b99a4619c3e92d98ecf267bfdbae07ca0f122c473d8c0eda7a21`

### wolfram_crosscheck (`audit-488b9332ecca`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:c020023423172d73faa6285b3b8d603cadfbdcc2e01ea3f9f64ddb7c69f4a474`
- **Output content hash:** `sha256:84c07812d226e1e333f83e9e0fe7eb92cad6cc97130f7c2c015dbef7354e3917`

### verify_identity (`audit-7fd175c59e8f`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 243 ms
- **Summary:** Symbolic proof established: (a0*cos(p0) + a1*cos(p1))**2 + (a0*sin(p0) + a1*sin(p1))**2 + (a0*cos(p0) - a1*cos(p1))**2 + (a0*sin(p0) - a1*sin(p1))**2 == 2*(a0**2 + a1**2).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:d1f0e06a6c01bc490c6a1223debae00ab6aee7c1004a551ccf03ca5cdcecdfc3`
- **Output content hash:** `sha256:50ca59d49c070bf516a4f0dd722d0b4e95c594a5fcd5599d0e52831d5fbce589`

### wolfram_crosscheck (`audit-c1cebbe7b89e`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:57829b463a1ef4063a1080673d7567af7af45afa996ff124e984a514987daebf`
- **Output content hash:** `sha256:a5a7b0faf1c10de947b8ebb1f16a7788e7251cb27f93668538613b38a6145747`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
