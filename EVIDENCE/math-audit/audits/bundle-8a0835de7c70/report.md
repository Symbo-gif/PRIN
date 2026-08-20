# Audit Evidence Report: bundle-8a0835de7c70

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:d19a23a4dff2c96be27ed82c26cd51cfb61bd3161583fce8b8f50aec39219053`)
**Generated:** 2026-08-20T02:40:27.264Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### PD-01-SIN -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** safe_phase_diff(a,b) = atan2(sin(a-b), cos(a-b)) preserves sin(a-b) exactly, which is the load-bearing property integrate.rs:26-31 relies on to skip wrapping phase differences at RK stages.  
- **Code references:** crates/prin-dynamics/src/state.rs:284-291, crates/prin-dynamics/src/integrate.rs:26-31  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-e7736e215659

### PD-01-COS -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** safe_phase_diff(a,b) = atan2(sin(a-b), cos(a-b)) preserves cos(a-b) exactly, the companion identity to PD-01-SIN.  
- **Code references:** crates/prin-dynamics/src/state.rs:284-291, crates/prin-dynamics/src/integrate.rs:26-31  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-a513d1c48409

### MF-01-PHASE -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For N=2, the mean-field Kuramoto phase-velocity term K*R*sin(psi-phi0) (with R*e^{i*psi} the complex order parameter over BOTH oscillators, i.e. including the self term) equals the full-matrix form K/2 * sum_j r_j*sin(phi_j - phi0) with self-coupling included.  
- **Code references:** crates/prin-dynamics/src/models.rs:191-231, crates/prin-dynamics/src/models.rs:233-281  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-0fc7432f4291

### MF-01-AMPLITUDE -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** The companion amplitude-channel identity to MF-01-PHASE: K*R*cos(psi-phi0) equals K/2 * sum_j r_j*cos(phi_j - phi0) with self-coupling included. Because cos(0)=1 (unlike sin(0)=0), the self term contributes non-trivially here -- this is the channel where prin-dynamics::coupling's zero-diagonal build_all_to_all matrix would NOT reproduce mean-field coupling if fed through CouplingMode::Full (see finding MF-DIAG in the audit report).  
- **Code references:** crates/prin-dynamics/src/models.rs:191-231, crates/prin-dynamics/src/models.rs:226, crates/prin-dynamics/src/coupling.rs:193-201  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-961118d8bd09

### SL-01-RADIAL -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For z = r*e^{i*phi} and dz/dt = (mu + i*omega)*z - |z|^2*z, the radial component dr/dt = Re(dz * e^{-i*phi}) reduces exactly to mu*r - r^3.  
- **Code references:** crates/prin-dynamics/src/models.rs:473-480, crates/prin-dynamics/src/models.rs:371-373  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-5c33513c9ad5

### SL-01-ANGULAR -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For the same Stuart-Landau flow, the angular component dphi/dt = Im(dz * e^{-i*phi}) / r reduces exactly to omega (constant, independent of r), for r > 0.  
- **Code references:** crates/prin-dynamics/src/models.rs:473-480, crates/prin-dynamics/src/models.rs:602-611  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-c027fde7aca2

### MPC-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** Mean phase coherence MPC = mean over pairs i<j of cos(phi_i - phi_j) equals (N*R^2 - 1)/(N - 1) for N=3, an exact algebraic consistency constraint between coherence.rs's O(N^2) pairwise sum and order.rs's order parameter R.  
- **Code references:** crates/prin-metrics/src/coherence.rs:39-57, crates/prin-metrics/src/order.rs:59-71  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-a8f46714b047

### PSD-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Parseval's theorem for the unnormalized 2-point DFT periodogram used by spectral.rs: sum_k |X[k]|^2 = M * sum_n A_n^2 for x_n = A_n*e^{i*phi_n}, instantiated at N=M=2.  
- **Code references:** crates/prin-metrics/src/spectral.rs:24-27, crates/prin-metrics/src/spectral.rs:48-92  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-8df10f69db44

## Tool invocations

### verify_identity (`audit-e7736e215659`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 135 ms
- **Summary:** Symbolic proof established: sin(atan2(sin(a - b), cos(a - b))) == sin(a - b).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:cc8ac758a054a712ad6bcb3dcab5108a9019bb11bfcdaddef96e9a3cc12c7dca`
- **Output content hash:** `sha256:c85460723653036b417abeddf4838ee388d0a6a80e6ce2948be3bc745a4059e0`

### wolfram_crosscheck (`audit-fa9a84632221`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:443e03490196e173d6f94df39be70a10653ece2b872c19b88528950c529e3cd1`
- **Output content hash:** `sha256:54bf2c974d25b9fe982f12519dd8625228a55ec249ce440561f3b8f0e4d7eb81`

### verify_identity (`audit-a513d1c48409`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 58 ms
- **Summary:** Symbolic proof established: cos(atan2(sin(a - b), cos(a - b))) == cos(a - b).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:d57dc6e6fdd9f80f101f3053556cdd0dd619328766c37fb69dbe80a616ffebaa`
- **Output content hash:** `sha256:8cd3407985b59f040c3b6bbf692177ce69c3bd1ee13979c55773b23eb35d6e45`

### wolfram_crosscheck (`audit-af90794e9894`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:755ce3d683f8507311380e6995ac506129bf3cffc11039434a546e073143535f`
- **Output content hash:** `sha256:69793e3b08a291bd8c88944b6db30771cba187962d463b01b77f788e0b41fe05`

### verify_identity (`audit-0fc7432f4291`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 296 ms
- **Summary:** Symbolic proof established: K*sqrt(((r0*cos(p0) + r1*cos(p1))/2)**2 + ((r0*sin(p0) + r1*sin(p1))/2)**2)*sin(atan2((r0*sin(p0) + r1*sin(p1))/2, (r0*cos(p0) + r1*cos(p1))/2) - p0) == K*(r0*sin(p0 - p0) + r1*sin(p1 - p0))/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:e9f149975d6623a02ad7f45dfbf28e98dcbb6bebfbd28d750b3dc3d3c44ff634`
- **Output content hash:** `sha256:8ea2848842a26a106cbe592b44d13942a7beb77ceac153553b35c68661ba065f`

### wolfram_crosscheck (`audit-2abf7b180055`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:fa721f9b663e925b435a7aa613aa1d3ec1bb3a9cab15116483793b33e2ebe1ef`
- **Output content hash:** `sha256:e4601d434785e24110cfebc233ddb9dd121a6290ce446561bed8b7eff630abfe`

### verify_identity (`audit-961118d8bd09`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 277 ms
- **Summary:** Symbolic proof established: K*sqrt(((r0*cos(p0) + r1*cos(p1))/2)**2 + ((r0*sin(p0) + r1*sin(p1))/2)**2)*cos(atan2((r0*sin(p0) + r1*sin(p1))/2, (r0*cos(p0) + r1*cos(p1))/2) - p0) == K*(r0*cos(p0 - p0) + r1*cos(p1 - p0))/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:0ff1be2bafe7dfc8d6d1e9a0627c95107f31615f78ae631db9a964de6866bafe`
- **Output content hash:** `sha256:69018daeda92e76534470899a81425caf6b149939d5d54425a671fa2c4af3b2f`

### wolfram_crosscheck (`audit-b1028266bc42`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:a705fb9ce8059372b327b7fbaeb5d81f2d6a263aed5652a598b590aaefaabc95`
- **Output content hash:** `sha256:c6154371b2fd533ec0a10699e220b4d14e1cb7ebaa665052c258e27e85952bcc`

### verify_identity (`audit-5c33513c9ad5`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 41 ms
- **Summary:** Symbolic proof established: re(((mu + I*w)*(r*exp(I*p)) - r**2*(r*exp(I*p)))*exp(-I*p)) == mu*r - r**3.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:77e0f8377ae09a85bbcd7e1f8d5cdfeb0a2b30bef0944a7886ca722a65a89468`
- **Output content hash:** `sha256:93ab76e970dc11e6bc67e3915727b0dd386999cf218ba90253b66c014019b920`

### wolfram_crosscheck (`audit-a35ec92c80f5`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:42689b00b5a8d06ace77cc5ca53bd449f5043d4bd2682f57c868063d8679cc41`
- **Output content hash:** `sha256:a04c740c912ac2e1ec5b6535684cb4403d3b274705232264548417dfe7279cdc`

### verify_identity (`audit-c027fde7aca2`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 21 ms
- **Summary:** Symbolic proof established: im(((mu + I*w)*(r*exp(I*p)) - r**2*(r*exp(I*p)))*exp(-I*p))/r == w.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- r > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:aea1bfd3dfe50a2295ddfb4697b3d09fca05533fb396ea93d197e7cf15d295ed`
- **Output content hash:** `sha256:26cc4db1a013705336d743ebe72cf2cd47aa44c6bb99518201e4aebf81523be4`

### wolfram_crosscheck (`audit-3ee155927b5b`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0923170bb89d305fcd4b264d1db1494a8b6e35e86e8ba8c68149a14b880654c2`
- **Output content hash:** `sha256:bab40e1024d2aedf4e19e51cfaa61e2cb83555fb12ab92e8d91cdf3b2b0dde21`

### verify_identity (`audit-a8f46714b047`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 91 ms
- **Summary:** Symbolic proof established: (cos(p0 - p1) + cos(p0 - p2) + cos(p1 - p2))/3 == (3*(((cos(p0) + cos(p1) + cos(p2))/3)**2 + ((sin(p0) + sin(p1) + sin(p2))/3)**2) - 1)/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:1bcf1f95c40fe0ab8a7a10b5d64b8057b04336fc9f2c65c67d4db0d1778ca741`
- **Output content hash:** `sha256:47e424738aa5b9a2e43c28a571b92dc79eadad9f5a87ed9645839f2dc1a3b98a`

### wolfram_crosscheck (`audit-a67b53418aa3`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:c020023423172d73faa6285b3b8d603cadfbdcc2e01ea3f9f64ddb7c69f4a474`
- **Output content hash:** `sha256:4dbee884668d393e6cfefbaf56e8d2ca6427442e9180e0f9e43f0f8be9d3c4ab`

### verify_identity (`audit-8df10f69db44`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 44 ms
- **Summary:** Symbolic proof established: (a0*cos(p0) + a1*cos(p1))**2 + (a0*sin(p0) + a1*sin(p1))**2 + (a0*cos(p0) - a1*cos(p1))**2 + (a0*sin(p0) - a1*sin(p1))**2 == 2*(a0**2 + a1**2).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:d1f0e06a6c01bc490c6a1223debae00ab6aee7c1004a551ccf03ca5cdcecdfc3`
- **Output content hash:** `sha256:1c695e83b1f1b62fb8868a218349eaf4bb02af455a0564bffc8c6098ef9f4889`

### wolfram_crosscheck (`audit-4c718a18f092`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:57829b463a1ef4063a1080673d7567af7af45afa996ff124e984a514987daebf`
- **Output content hash:** `sha256:d794fcd75813cd44f8497d68a9423f21f1a81734172d13dac91406f2f64da776`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
