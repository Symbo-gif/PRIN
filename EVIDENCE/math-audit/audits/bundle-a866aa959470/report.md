# Audit Evidence Report: bundle-a866aa959470

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-08-26T05:07:42.464Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### PD-01-SIN -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** safe_phase_diff(a,b) = atan2(sin(a-b), cos(a-b)) preserves sin(a-b) exactly, which is the load-bearing property integrate.rs:26-31 relies on to skip wrapping phase differences at RK stages.  
- **Code references:** crates/prin-dynamics/src/state.rs:284-291, crates/prin-dynamics/src/integrate.rs:26-31  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-f5ee60248b2c

### PD-01-COS -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** safe_phase_diff(a,b) = atan2(sin(a-b), cos(a-b)) preserves cos(a-b) exactly, the companion identity to PD-01-SIN.  
- **Code references:** crates/prin-dynamics/src/state.rs:284-291, crates/prin-dynamics/src/integrate.rs:26-31  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-c3d760585e5a

### MF-01-PHASE -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For N=2, the mean-field Kuramoto phase-velocity term K*R*sin(psi-phi0) (with R*e^{i*psi} the complex order parameter over BOTH oscillators, i.e. including the self term) equals the full-matrix form K/2 * sum_j r_j*sin(phi_j - phi0) with self-coupling included.  
- **Code references:** crates/prin-dynamics/src/models.rs:191-231, crates/prin-dynamics/src/models.rs:233-281  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-2848c8c2af62

### MF-01-AMPLITUDE -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** The companion amplitude-channel identity to MF-01-PHASE: K*R*cos(psi-phi0) equals K/2 * sum_j r_j*cos(phi_j - phi0) with self-coupling included. Because cos(0)=1 (unlike sin(0)=0), the self term contributes non-trivially here -- this is the channel where prin-dynamics::coupling's zero-diagonal build_all_to_all matrix would NOT reproduce mean-field coupling if fed through CouplingMode::Full (see finding MF-DIAG in the audit report).  
- **Code references:** crates/prin-dynamics/src/models.rs:191-231, crates/prin-dynamics/src/models.rs:226, crates/prin-dynamics/src/coupling.rs:193-201  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-ba68d18dc04f

### SL-01-RADIAL -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For z = r*e^{i*phi} and dz/dt = (mu + i*omega)*z - |z|^2*z, the radial component dr/dt = Re(dz * e^{-i*phi}) reduces exactly to mu*r - r^3.  
- **Code references:** crates/prin-dynamics/src/models.rs:473-480, crates/prin-dynamics/src/models.rs:371-373  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-4cb5a51b324b

### SL-01-ANGULAR -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `critical`  
- **Statement:** For the same Stuart-Landau flow, the angular component dphi/dt = Im(dz * e^{-i*phi}) / r reduces exactly to omega (constant, independent of r), for r > 0.  
- **Code references:** crates/prin-dynamics/src/models.rs:473-480, crates/prin-dynamics/src/models.rs:602-611  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-25252b615cb9

### MPC-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** Mean phase coherence MPC = mean over pairs i<j of cos(phi_i - phi_j) equals (N*R^2 - 1)/(N - 1) for N=3, an exact algebraic consistency constraint between coherence.rs's O(N^2) pairwise sum and order.rs's order parameter R.  
- **Code references:** crates/prin-metrics/src/coherence.rs:39-57, crates/prin-metrics/src/order.rs:59-71  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-e5bd71ab816b

### PSD-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** Parseval's theorem for the unnormalized 2-point DFT periodogram used by spectral.rs: sum_k |X[k]|^2 = M * sum_n A_n^2 for x_n = A_n*e^{i*phi_n}, instantiated at N=M=2.  
- **Code references:** crates/prin-metrics/src/spectral.rs:24-27, crates/prin-metrics/src/spectral.rs:48-92  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-4ad96c5d3abe

## Tool invocations

### verify_identity (`audit-f5ee60248b2c`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 69 ms
- **Summary:** Symbolic proof established: sin(atan2(sin(a - b), cos(a - b))) == sin(a - b).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:cc8ac758a054a712ad6bcb3dcab5108a9019bb11bfcdaddef96e9a3cc12c7dca`
- **Output content hash:** `sha256:713a9d85ecc111a4d6f64318d922d63c946598f2c01d545da433e70bdae6c088`

### wolfram_crosscheck (`audit-d2f07c318fb6`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:443e03490196e173d6f94df39be70a10653ece2b872c19b88528950c529e3cd1`
- **Output content hash:** `sha256:c488081dd37e504cf0b762de3c9d7fb3dcb6b0b6af27d31509c5432f21f838a2`

### verify_identity (`audit-c3d760585e5a`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 51 ms
- **Summary:** Symbolic proof established: cos(atan2(sin(a - b), cos(a - b))) == cos(a - b).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:d57dc6e6fdd9f80f101f3053556cdd0dd619328766c37fb69dbe80a616ffebaa`
- **Output content hash:** `sha256:7924acf5d6d5d7b0e2e95a3d617466b6b81cae094bc06b0425edac65d7483e8d`

### wolfram_crosscheck (`audit-3f731e6e32c2`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:755ce3d683f8507311380e6995ac506129bf3cffc11039434a546e073143535f`
- **Output content hash:** `sha256:0766a1c851531ceddbdbe792ac44ce5fc98ce109752d1b61effc29f34e4eea80`

### verify_identity (`audit-2848c8c2af62`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 350 ms
- **Summary:** Symbolic proof established: K*sqrt(((r0*cos(p0) + r1*cos(p1))/2)**2 + ((r0*sin(p0) + r1*sin(p1))/2)**2)*sin(atan2((r0*sin(p0) + r1*sin(p1))/2, (r0*cos(p0) + r1*cos(p1))/2) - p0) == K*(r0*sin(p0 - p0) + r1*sin(p1 - p0))/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:e9f149975d6623a02ad7f45dfbf28e98dcbb6bebfbd28d750b3dc3d3c44ff634`
- **Output content hash:** `sha256:084a88021af7d2c1dbadec58ea3e34607bb288be2706c42b56953f786eef761c`

### wolfram_crosscheck (`audit-447c98f4533c`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:fa721f9b663e925b435a7aa613aa1d3ec1bb3a9cab15116483793b33e2ebe1ef`
- **Output content hash:** `sha256:1c2fbfc7e83f28a416747efd6d146204be2595e09a6a742320adb93ff4642c4d`

### verify_identity (`audit-ba68d18dc04f`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 270 ms
- **Summary:** Symbolic proof established: K*sqrt(((r0*cos(p0) + r1*cos(p1))/2)**2 + ((r0*sin(p0) + r1*sin(p1))/2)**2)*cos(atan2((r0*sin(p0) + r1*sin(p1))/2, (r0*cos(p0) + r1*cos(p1))/2) - p0) == K*(r0*cos(p0 - p0) + r1*cos(p1 - p0))/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:0ff1be2bafe7dfc8d6d1e9a0627c95107f31615f78ae631db9a964de6866bafe`
- **Output content hash:** `sha256:ec8671e15ccaa97e63cc56df2b75c95e9ebc96f152ce7503093f53c3e72eec20`

### wolfram_crosscheck (`audit-fb343df439ac`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:a705fb9ce8059372b327b7fbaeb5d81f2d6a263aed5652a598b590aaefaabc95`
- **Output content hash:** `sha256:3d31d90ea6424a234d6ba3270d66127be50152a151e11bc50cd4de12d682d7bf`

### verify_identity (`audit-4cb5a51b324b`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 46 ms
- **Summary:** Symbolic proof established: re(((mu + I*w)*(r*exp(I*p)) - r**2*(r*exp(I*p)))*exp(-I*p)) == mu*r - r**3.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:77e0f8377ae09a85bbcd7e1f8d5cdfeb0a2b30bef0944a7886ca722a65a89468`
- **Output content hash:** `sha256:8137f74043ce7bf256b397d2f28e7527b8488c02332ce7267af6e00c186cfcd5`

### wolfram_crosscheck (`audit-ae45b2b05a5a`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:42689b00b5a8d06ace77cc5ca53bd449f5043d4bd2682f57c868063d8679cc41`
- **Output content hash:** `sha256:44cf827c44182f0f9c7fa0f104ecda98112089f0537f8c77c2fc27eacba3e2fd`

### verify_identity (`audit-25252b615cb9`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `critical`
- **Duration:** 32 ms
- **Summary:** Symbolic proof established: im(((mu + I*w)*(r*exp(I*p)) - r**2*(r*exp(I*p)))*exp(-I*p))/r == w.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- r > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:aea1bfd3dfe50a2295ddfb4697b3d09fca05533fb396ea93d197e7cf15d295ed`
- **Output content hash:** `sha256:7b7b4a9328df58040bcb419cc7bc6079b67c79f1f8c6b9baa8513c63dbb06c6c`

### wolfram_crosscheck (`audit-fecbab2a38d7`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `critical`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0923170bb89d305fcd4b264d1db1494a8b6e35e86e8ba8c68149a14b880654c2`
- **Output content hash:** `sha256:1d0c0d10bf5b18968ebaa4edc8fc77d0e99787dd2bf87b0b30b953601cbc81c7`

### verify_identity (`audit-e5bd71ab816b`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 94 ms
- **Summary:** Symbolic proof established: (cos(p0 - p1) + cos(p0 - p2) + cos(p1 - p2))/3 == (3*(((cos(p0) + cos(p1) + cos(p2))/3)**2 + ((sin(p0) + sin(p1) + sin(p2))/3)**2) - 1)/2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:1bcf1f95c40fe0ab8a7a10b5d64b8057b04336fc9f2c65c67d4db0d1778ca741`
- **Output content hash:** `sha256:9b7079457ebebf672ca1bc8eeec821dfeacd352b657afcb9fdd93460989c4b16`

### wolfram_crosscheck (`audit-85e891483b76`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:c020023423172d73faa6285b3b8d603cadfbdcc2e01ea3f9f64ddb7c69f4a474`
- **Output content hash:** `sha256:e0a47f6994bded9e4b86d2421a4d3649db078a2ceb615ba5252f3012e1f2c1c7`

### verify_identity (`audit-4ad96c5d3abe`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 44 ms
- **Summary:** Symbolic proof established: (a0*cos(p0) + a1*cos(p1))**2 + (a0*sin(p0) + a1*sin(p1))**2 + (a0*cos(p0) - a1*cos(p1))**2 + (a0*sin(p0) - a1*sin(p1))**2 == 2*(a0**2 + a1**2).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:d1f0e06a6c01bc490c6a1223debae00ab6aee7c1004a551ccf03ca5cdcecdfc3`
- **Output content hash:** `sha256:cafa7e56c775d81506da684eff3d1b48468a76e99ce823eb206789ea4154ce62`

### wolfram_crosscheck (`audit-f3a56ae832a7`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:57829b463a1ef4063a1080673d7567af7af45afa996ff124e984a514987daebf`
- **Output content hash:** `sha256:0f20fdafd0e4897c01ec040d70820df0b43cb3ee2af3bd075ac350fd2b672141`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
