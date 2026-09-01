# Audit Evidence Report: bundle-c3d4ccbfa088

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T19:57:47.041Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### PD-01-SIN -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** safe_phase_diff(a,b) = atan2(sin(a-b), cos(a-b)) preserves sin(a-b) exactly, which is the load-bearing property integrate.rs:26-31 relies on to skip wrapping phase differences at RK stages.  
- **Code references:** crates/prin-dynamics/src/state.rs:284-291, crates/prin-dynamics/src/integrate.rs:26-31  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-45e00e5ddab5

### PD-01-COS -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** safe_phase_diff(a,b) = atan2(sin(a-b), cos(a-b)) preserves cos(a-b) exactly, the companion identity to PD-01-SIN.  
- **Code references:** crates/prin-dynamics/src/state.rs:284-291, crates/prin-dynamics/src/integrate.rs:26-31  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-190ef3df3856

### MF-01-PHASE -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For N=2, the mean-field Kuramoto phase-velocity term K*R*sin(psi-phi0) (with R*e^{i*psi} the complex order parameter over BOTH oscillators, i.e. including the self term) equals the full-matrix form K/2 * sum_j r_j*sin(phi_j - phi0) with self-coupling included.  
- **Code references:** crates/prin-dynamics/src/models.rs:191-231, crates/prin-dynamics/src/models.rs:233-281  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-231a4bee93eb

### MF-01-AMPLITUDE -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** The companion amplitude-channel identity to MF-01-PHASE: K*R*cos(psi-phi0) equals K/2 * sum_j r_j*cos(phi_j - phi0) with self-coupling included. Because cos(0)=1 (unlike sin(0)=0), the self term contributes non-trivially here -- this is the channel where prin-dynamics::coupling's zero-diagonal build_all_to_all matrix would NOT reproduce mean-field coupling if fed through CouplingMode::Full (see finding MF-DIAG in the audit report).  
- **Code references:** crates/prin-dynamics/src/models.rs:191-231, crates/prin-dynamics/src/models.rs:226, crates/prin-dynamics/src/coupling.rs:193-201  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-cf863e6228bc

### SL-01-RADIAL -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For z = r*e^{i*phi} and dz/dt = (mu + i*omega)*z - |z|^2*z, the radial component dr/dt = Re(dz * e^{-i*phi}) reduces exactly to mu*r - r^3.  
- **Code references:** crates/prin-dynamics/src/models.rs:473-480, crates/prin-dynamics/src/models.rs:371-373  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-ec89b0f12c4f

### SL-01-ANGULAR -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For the same Stuart-Landau flow, the angular component dphi/dt = Im(dz * e^{-i*phi}) / r reduces exactly to omega (constant, independent of r), for r > 0.  
- **Code references:** crates/prin-dynamics/src/models.rs:473-480, crates/prin-dynamics/src/models.rs:602-611  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-e41af4e3195e

### MPC-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** Mean phase coherence MPC = mean over pairs i<j of cos(phi_i - phi_j) equals (N*R^2 - 1)/(N - 1) for N=3, an exact algebraic consistency constraint between coherence.rs's O(N^2) pairwise sum and order.rs's order parameter R.  
- **Code references:** crates/prin-metrics/src/coherence.rs:39-57, crates/prin-metrics/src/order.rs:59-71  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-91dad0711c6f

### PSD-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Parseval's theorem for the unnormalized 2-point DFT periodogram used by spectral.rs: sum_k |X[k]|^2 = M * sum_n A_n^2 for x_n = A_n*e^{i*phi_n}, instantiated at N=M=2.  
- **Code references:** crates/prin-metrics/src/spectral.rs:24-27, crates/prin-metrics/src/spectral.rs:48-92  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-cce2a7918164

## Tool invocations

### verify_identity (`audit-45e00e5ddab5`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 469 ms
- **Summary:** Symbolic proof established: sin(atan2(sin(a - b), cos(a - b))) == sin(a - b).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:cc8ac758a054a712ad6bcb3dcab5108a9019bb11bfcdaddef96e9a3cc12c7dca`
- **Output content hash:** `sha256:7a1e13065d7117789774d503fe9cdd748bca3143500719508a9ffa1287cd6967`

### wolfram_crosscheck (`audit-2a8a510e2f35`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:443e03490196e173d6f94df39be70a10653ece2b872c19b88528950c529e3cd1`
- **Output content hash:** `sha256:642ba91486f64456a8d0818c816b42807685e0cd737b44d89926c290287d7f8a`

### verify_identity (`audit-190ef3df3856`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 248 ms
- **Summary:** Symbolic proof established: cos(atan2(sin(a - b), cos(a - b))) == cos(a - b).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:d57dc6e6fdd9f80f101f3053556cdd0dd619328766c37fb69dbe80a616ffebaa`
- **Output content hash:** `sha256:3705a37281386d499d7aef29858867ad6ec771e660686df4a2f4d644d454285d`

### wolfram_crosscheck (`audit-948ffb2c8fc2`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:755ce3d683f8507311380e6995ac506129bf3cffc11039434a546e073143535f`
- **Output content hash:** `sha256:94f919105d48c0832c2dffcb8a50eea4e4f398efbae2540ab980db0107bce8c1`

### verify_identity (`audit-231a4bee93eb`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 2340 ms
- **Summary:** Symbolic proof established: K*sqrt(((r0*cos(p0) + r1*cos(p1))/2)**2 + ((r0*sin(p0) + r1*sin(p1))/2)**2)*sin(atan2((r0*sin(p0) + r1*sin(p1))/2, (r0*cos(p0) + r1*cos(p1))/2) - p0) == K*(r0*sin(p0 - p0) + r1*sin(p1 - p0))/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:e9f149975d6623a02ad7f45dfbf28e98dcbb6bebfbd28d750b3dc3d3c44ff634`
- **Output content hash:** `sha256:34b4706aaedce11cce2a1780caf6cc12a25b2e9d990e79c74fdf2360c9c1c215`

### wolfram_crosscheck (`audit-442c47979396`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:fa721f9b663e925b435a7aa613aa1d3ec1bb3a9cab15116483793b33e2ebe1ef`
- **Output content hash:** `sha256:d1c397c387d5567ad0ae2e1dca5b37cbabee9d1e9d57b405336c2891e9b6aa0f`

### verify_identity (`audit-cf863e6228bc`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 1631 ms
- **Summary:** Symbolic proof established: K*sqrt(((r0*cos(p0) + r1*cos(p1))/2)**2 + ((r0*sin(p0) + r1*sin(p1))/2)**2)*cos(atan2((r0*sin(p0) + r1*sin(p1))/2, (r0*cos(p0) + r1*cos(p1))/2) - p0) == K*(r0*cos(p0 - p0) + r1*cos(p1 - p0))/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:0ff1be2bafe7dfc8d6d1e9a0627c95107f31615f78ae631db9a964de6866bafe`
- **Output content hash:** `sha256:ff2d62799f4bea083b761cfb0bb017da6079e3b22ae341bea9cee2a20338f8cb`

### wolfram_crosscheck (`audit-294ed31e75d6`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:a705fb9ce8059372b327b7fbaeb5d81f2d6a263aed5652a598b590aaefaabc95`
- **Output content hash:** `sha256:03fbcb70a5a087747569727d1d888495085d47c608f1a420970c7b36bbc2c5d8`

### verify_identity (`audit-ec89b0f12c4f`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 307 ms
- **Summary:** Symbolic proof established: re(((mu + I*w)*(r*exp(I*p)) - r**2*(r*exp(I*p)))*exp(-I*p)) == mu*r - r**3.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:77e0f8377ae09a85bbcd7e1f8d5cdfeb0a2b30bef0944a7886ca722a65a89468`
- **Output content hash:** `sha256:8a51e4c6d803b4026ad3d470502b965cd89b4d89cce08bd34616fe5acc2ab75f`

### wolfram_crosscheck (`audit-620ee2ec5a08`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:42689b00b5a8d06ace77cc5ca53bd449f5043d4bd2682f57c868063d8679cc41`
- **Output content hash:** `sha256:94df076eec1f1e1bc65a776aa969a817213b8f81a97d37f3730b3b1a8fd94568`

### verify_identity (`audit-e41af4e3195e`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 209 ms
- **Summary:** Symbolic proof established: im(((mu + I*w)*(r*exp(I*p)) - r**2*(r*exp(I*p)))*exp(-I*p))/r == w.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- r > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:aea1bfd3dfe50a2295ddfb4697b3d09fca05533fb396ea93d197e7cf15d295ed`
- **Output content hash:** `sha256:57c09a8bd033734ba839ac8128a44f493a9cdac0ed5f97a2c68d3c343134b0a1`

### wolfram_crosscheck (`audit-d3edce31592a`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0923170bb89d305fcd4b264d1db1494a8b6e35e86e8ba8c68149a14b880654c2`
- **Output content hash:** `sha256:ee079f94f9cf7a2b609e5e3b76c7d74a7e4a9c155468dd39aa6326389e1002a7`

### verify_identity (`audit-91dad0711c6f`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 707 ms
- **Summary:** Symbolic proof established: (cos(p0 - p1) + cos(p0 - p2) + cos(p1 - p2))/3 == (3*(((cos(p0) + cos(p1) + cos(p2))/3)**2 + ((sin(p0) + sin(p1) + sin(p2))/3)**2) - 1)/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:1bcf1f95c40fe0ab8a7a10b5d64b8057b04336fc9f2c65c67d4db0d1778ca741`
- **Output content hash:** `sha256:6c9e75c2ff0224c92682c279c144b9d3bc0df8eb6e9db49a5fecf2fbd38ece7c`

### wolfram_crosscheck (`audit-4548d0aa6f52`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:c020023423172d73faa6285b3b8d603cadfbdcc2e01ea3f9f64ddb7c69f4a474`
- **Output content hash:** `sha256:9490c6cf036357dad5918e910b59eceaee7ffcb8b7338f5aaf04eaf3b9741d91`

### verify_identity (`audit-cce2a7918164`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 231 ms
- **Summary:** Symbolic proof established: (a0*cos(p0) + a1*cos(p1))**2 + (a0*sin(p0) + a1*sin(p1))**2 + (a0*cos(p0) - a1*cos(p1))**2 + (a0*sin(p0) - a1*sin(p1))**2 == 2*(a0**2 + a1**2).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:d1f0e06a6c01bc490c6a1223debae00ab6aee7c1004a551ccf03ca5cdcecdfc3`
- **Output content hash:** `sha256:216720d77d08d1ccf5020f1a529b44f1aac9d580a9787541a4e633c69fb19241`

### wolfram_crosscheck (`audit-2dc901dc6dbc`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:57829b463a1ef4063a1080673d7567af7af45afa996ff124e984a514987daebf`
- **Output content hash:** `sha256:9172fdfa089eb096b4ffa1b8a6844937669e5ab3cf719cb17e9a3845bc4b0f73`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
