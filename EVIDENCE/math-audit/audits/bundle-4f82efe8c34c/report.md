# Audit Evidence Report: bundle-4f82efe8c34c

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T19:52:36.927Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### PD-01-SIN -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** safe_phase_diff(a,b) = atan2(sin(a-b), cos(a-b)) preserves sin(a-b) exactly, which is the load-bearing property integrate.rs:26-31 relies on to skip wrapping phase differences at RK stages.  
- **Code references:** crates/prin-dynamics/src/state.rs:284-291, crates/prin-dynamics/src/integrate.rs:26-31  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-ccb14a8694bf

### PD-01-COS -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** safe_phase_diff(a,b) = atan2(sin(a-b), cos(a-b)) preserves cos(a-b) exactly, the companion identity to PD-01-SIN.  
- **Code references:** crates/prin-dynamics/src/state.rs:284-291, crates/prin-dynamics/src/integrate.rs:26-31  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-83a138955fc6

### MF-01-PHASE -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For N=2, the mean-field Kuramoto phase-velocity term K*R*sin(psi-phi0) (with R*e^{i*psi} the complex order parameter over BOTH oscillators, i.e. including the self term) equals the full-matrix form K/2 * sum_j r_j*sin(phi_j - phi0) with self-coupling included.  
- **Code references:** crates/prin-dynamics/src/models.rs:191-231, crates/prin-dynamics/src/models.rs:233-281  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-de70d18026d6

### MF-01-AMPLITUDE -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** The companion amplitude-channel identity to MF-01-PHASE: K*R*cos(psi-phi0) equals K/2 * sum_j r_j*cos(phi_j - phi0) with self-coupling included. Because cos(0)=1 (unlike sin(0)=0), the self term contributes non-trivially here -- this is the channel where prin-dynamics::coupling's zero-diagonal build_all_to_all matrix would NOT reproduce mean-field coupling if fed through CouplingMode::Full (see finding MF-DIAG in the audit report).  
- **Code references:** crates/prin-dynamics/src/models.rs:191-231, crates/prin-dynamics/src/models.rs:226, crates/prin-dynamics/src/coupling.rs:193-201  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-9b3e166c30fe

### SL-01-RADIAL -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For z = r*e^{i*phi} and dz/dt = (mu + i*omega)*z - |z|^2*z, the radial component dr/dt = Re(dz * e^{-i*phi}) reduces exactly to mu*r - r^3.  
- **Code references:** crates/prin-dynamics/src/models.rs:473-480, crates/prin-dynamics/src/models.rs:371-373  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-c0298e5044c3

### SL-01-ANGULAR -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For the same Stuart-Landau flow, the angular component dphi/dt = Im(dz * e^{-i*phi}) / r reduces exactly to omega (constant, independent of r), for r > 0.  
- **Code references:** crates/prin-dynamics/src/models.rs:473-480, crates/prin-dynamics/src/models.rs:602-611  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-0a4ec0561ee2

### MPC-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** Mean phase coherence MPC = mean over pairs i<j of cos(phi_i - phi_j) equals (N*R^2 - 1)/(N - 1) for N=3, an exact algebraic consistency constraint between coherence.rs's O(N^2) pairwise sum and order.rs's order parameter R.  
- **Code references:** crates/prin-metrics/src/coherence.rs:39-57, crates/prin-metrics/src/order.rs:59-71  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-ac89c35cc906

### PSD-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Parseval's theorem for the unnormalized 2-point DFT periodogram used by spectral.rs: sum_k |X[k]|^2 = M * sum_n A_n^2 for x_n = A_n*e^{i*phi_n}, instantiated at N=M=2.  
- **Code references:** crates/prin-metrics/src/spectral.rs:24-27, crates/prin-metrics/src/spectral.rs:48-92  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-9972e6db7bb9

## Tool invocations

### verify_identity (`audit-ccb14a8694bf`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 668 ms
- **Summary:** Symbolic proof established: sin(atan2(sin(a - b), cos(a - b))) == sin(a - b).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:cc8ac758a054a712ad6bcb3dcab5108a9019bb11bfcdaddef96e9a3cc12c7dca`
- **Output content hash:** `sha256:59db5225756dd4895146ba2eeb303c78b8e7c53990b045e905a0dfe2851ed2f5`

### wolfram_crosscheck (`audit-b0e4990ab4fe`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:443e03490196e173d6f94df39be70a10653ece2b872c19b88528950c529e3cd1`
- **Output content hash:** `sha256:07f024621abd61e88f6707e8b88a2a46331dec3a154f71c072234bbbf085505c`

### verify_identity (`audit-83a138955fc6`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 594 ms
- **Summary:** Symbolic proof established: cos(atan2(sin(a - b), cos(a - b))) == cos(a - b).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:d57dc6e6fdd9f80f101f3053556cdd0dd619328766c37fb69dbe80a616ffebaa`
- **Output content hash:** `sha256:4b253f83cb7eeb831f4eb72a9088bbaa2144bb08fbfc8fc4726dee801f95723f`

### wolfram_crosscheck (`audit-4470edc1f00e`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:755ce3d683f8507311380e6995ac506129bf3cffc11039434a546e073143535f`
- **Output content hash:** `sha256:802b4ea98c226327adcd0340821038c5bbc14cb6e3b7e0b7c2219edf72d72668`

### verify_identity (`audit-de70d18026d6`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 5100 ms
- **Summary:** Symbolic proof established: K*sqrt(((r0*cos(p0) + r1*cos(p1))/2)**2 + ((r0*sin(p0) + r1*sin(p1))/2)**2)*sin(atan2((r0*sin(p0) + r1*sin(p1))/2, (r0*cos(p0) + r1*cos(p1))/2) - p0) == K*(r0*sin(p0 - p0) + r1*sin(p1 - p0))/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:e9f149975d6623a02ad7f45dfbf28e98dcbb6bebfbd28d750b3dc3d3c44ff634`
- **Output content hash:** `sha256:fda9e1242a2e929a673b359e765261f9c783d2773faac422fbd628ebfcbaf7d7`

### wolfram_crosscheck (`audit-c7142a8e7a5e`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:fa721f9b663e925b435a7aa613aa1d3ec1bb3a9cab15116483793b33e2ebe1ef`
- **Output content hash:** `sha256:b4a115ae448c4969afd017818fb416de7e65706b777630a837588e4952b43793`

### verify_identity (`audit-9b3e166c30fe`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 3762 ms
- **Summary:** Symbolic proof established: K*sqrt(((r0*cos(p0) + r1*cos(p1))/2)**2 + ((r0*sin(p0) + r1*sin(p1))/2)**2)*cos(atan2((r0*sin(p0) + r1*sin(p1))/2, (r0*cos(p0) + r1*cos(p1))/2) - p0) == K*(r0*cos(p0 - p0) + r1*cos(p1 - p0))/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:0ff1be2bafe7dfc8d6d1e9a0627c95107f31615f78ae631db9a964de6866bafe`
- **Output content hash:** `sha256:c91b51f861bcaeac1e2c49895d9946d59330002f36509938f57d4d32ae49567e`

### wolfram_crosscheck (`audit-bb13977c23a8`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:a705fb9ce8059372b327b7fbaeb5d81f2d6a263aed5652a598b590aaefaabc95`
- **Output content hash:** `sha256:d141dab76803d1db80e639f9ead7a76fa7a01b3dd0621bc269f86eb99145e00e`

### verify_identity (`audit-c0298e5044c3`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 678 ms
- **Summary:** Symbolic proof established: re(((mu + I*w)*(r*exp(I*p)) - r**2*(r*exp(I*p)))*exp(-I*p)) == mu*r - r**3.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:77e0f8377ae09a85bbcd7e1f8d5cdfeb0a2b30bef0944a7886ca722a65a89468`
- **Output content hash:** `sha256:be210065b53f1faa9be160a32004c02c00c3227961647ee498962166bea1b948`

### wolfram_crosscheck (`audit-319927951389`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:42689b00b5a8d06ace77cc5ca53bd449f5043d4bd2682f57c868063d8679cc41`
- **Output content hash:** `sha256:43852babdab22dbe90f7f512e2798e7028ae4237b9f2c9a30ef087d2fbf7b0b1`

### verify_identity (`audit-0a4ec0561ee2`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 372 ms
- **Summary:** Symbolic proof established: im(((mu + I*w)*(r*exp(I*p)) - r**2*(r*exp(I*p)))*exp(-I*p))/r == w.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- r > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:aea1bfd3dfe50a2295ddfb4697b3d09fca05533fb396ea93d197e7cf15d295ed`
- **Output content hash:** `sha256:a31243fb526b5087f2fcdbe9d6f891dab088cefb0e812b897c35ff79872f98bc`

### wolfram_crosscheck (`audit-93f829e63985`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0923170bb89d305fcd4b264d1db1494a8b6e35e86e8ba8c68149a14b880654c2`
- **Output content hash:** `sha256:8fb1fcd5804f372ffde29b2b2f49695d97c4eeb672ce8869c13af9be716b678f`

### verify_identity (`audit-ac89c35cc906`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 1661 ms
- **Summary:** Symbolic proof established: (cos(p0 - p1) + cos(p0 - p2) + cos(p1 - p2))/3 == (3*(((cos(p0) + cos(p1) + cos(p2))/3)**2 + ((sin(p0) + sin(p1) + sin(p2))/3)**2) - 1)/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:1bcf1f95c40fe0ab8a7a10b5d64b8057b04336fc9f2c65c67d4db0d1778ca741`
- **Output content hash:** `sha256:545abe01ad1946e80a758964832fa7cb40007ecafb9d1ec325494abb67ef5ced`

### wolfram_crosscheck (`audit-640a01480aba`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:c020023423172d73faa6285b3b8d603cadfbdcc2e01ea3f9f64ddb7c69f4a474`
- **Output content hash:** `sha256:389a15f3842eca33b2ed55ad8c809a850309f68693bec49b9e08ce4f617d924a`

### verify_identity (`audit-9972e6db7bb9`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 668 ms
- **Summary:** Symbolic proof established: (a0*cos(p0) + a1*cos(p1))**2 + (a0*sin(p0) + a1*sin(p1))**2 + (a0*cos(p0) - a1*cos(p1))**2 + (a0*sin(p0) - a1*sin(p1))**2 == 2*(a0**2 + a1**2).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:d1f0e06a6c01bc490c6a1223debae00ab6aee7c1004a551ccf03ca5cdcecdfc3`
- **Output content hash:** `sha256:e832507b68f9ed67dd9ee89fe6878149ea67e725196e32cce3a843bdddd770ab`

### wolfram_crosscheck (`audit-bf33ce879cd8`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:57829b463a1ef4063a1080673d7567af7af45afa996ff124e984a514987daebf`
- **Output content hash:** `sha256:61814999af2dc73fae27690168a30de9cf9602050d864a1d749309815257338a`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
