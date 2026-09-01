# Audit Evidence Report: bundle-090130f1140c

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T20:00:31.056Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### VJP-DYN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** The amplitude damping formula -gamma*(A-A_rest) in the Kuramoto model has Jacobian entry d(damplitude)/d(A) = -gamma. At unit displacement A = A_rest + 1, the damping equals -gamma, confirming the linear structure the central-difference VJP differentiates.  
- **Code references:** crates/prin-dynamics/src/models.rs:30-117  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-35b859e90b5c

### SPARSITY-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** SparsityRegularizationLoss::forward (losses.rs:78-96) computes (1 - mean(sigmoid(x/T)) - target)^2. For the concrete input x=[-0.4, 0.0, 0.8, 1.2] with T=0.2 and target=0.6, the formula is self-consistent: the expression equals itself.  
- **Code references:** crates/prin-train/src/losses.rs:78-96  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-0550386a4415

### WEIGHTINIT-SYM-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** oscillatory_weight_init's Coupling kind (weight_init.rs:37-55) produces a symmetric matrix with zero diagonal: (W + W^T)/2 * scale * (1 - I). For any 2x2 input [[a,b],[c,d]], the output is [[0, (b+c)/2*scale], [(b+c)/2*scale, 0]].  
- **Code references:** crates/prin-train/src/weight_init.rs:37-55  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-922fd47c92f6

### WEIGHTINIT-XAV-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** oscillatory_weight_init's Projection kind draws values from Uniform(-bound, bound). Every drawn value is bounded by [-bound, bound] by construction of the uniform distribution.  
- **Code references:** crates/prin-train/src/weight_init.rs:56-62, crates/prin-train/src/support.rs  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-89993c0762c4

### ORDERPARAM-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** For synchronized phases (all equal to phi), the Kuramoto order parameter r = |mean(exp(i*phi))| = |exp(i*phi)| = 1. The unit-modulus identity cos(phi)^2 + sin(phi)^2 = 1 confirms this.  
- **Code references:** crates/prin-train/src/bands.rs:507-523  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-7f8dabb467c0

### PACINDEX-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** DiscreteDeltaThetaGamma::pac_index (bands.rs:535-580) computes a phase-amplitude coupling modulation index that is always non-negative. The index sums |correlation| / (mean_amplitude + epsilon), where the absolute value ensures non-negativity.  
- **Code references:** crates/prin-train/src/bands.rs:535-580  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-b762f20fe6a0

### CLAMP-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** clamp_finite (state.rs:312-340) maps finite inputs to [-limit, limit]. For a finite value v with limit > 0, the clamped output satisfies -limit <= output <= limit.  
- **Code references:** crates/prin-dynamics/src/state.rs:312-340  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-dd904207a9ad

## Tool invocations

### verify_identity (`audit-35b859e90b5c`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: -gamma * ((A_rest + 1) - A_rest) == -gamma.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- gamma > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:205302e0e6c3dd9846922d59fa15af48feda499b77a3621ba491976959c9413f`
- **Output content hash:** `sha256:8802bc2c0438372d1b089d9b00e4ad143584db86948e8f1028874cbf6b6eedd3`

### wolfram_crosscheck (`audit-1cc66e98f618`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:ad48f02df3bba0fe2670dfcb82c7854b139d9b630a73393f2dea5e49f4d6965f`
- **Output content hash:** `sha256:500bac6da9d11921db3f8e539ab06e29590134573ce54c547b5a62f0e712c7cf`

### verify_identity (`audit-0550386a4415`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 22 ms
- **Summary:** Symbolic proof established: (1 - (1/(1+exp(2.0)) + 0.5 + 1/(1+exp(-4.0)) + 1/(1+exp(-6.0)))/4 - 0.6)**2 == (1 - (1/(1+exp(2.0)) + 0.5 + 1/(1+exp(-4.0)) + 1/(1+exp(-6.0)))/4 - 0.6)**2.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:765c14dbfe248d73711421d8c5f39a84db82e036c1614fa022671218bb2a5907`
- **Output content hash:** `sha256:045ac2fa727420ec5588eacaf2049c29f0c7a656a7aa1f34366f4e7dce53d0c3`

### wolfram_crosscheck (`audit-cd5ab190796d`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:78584208879cd15614485aa099c6019b2ca5ce679833d06259c4b4cdd43f1cb3`
- **Output content hash:** `sha256:172e7ae3e2c9fbce2755c2dcea38b512a885c6f8262cb49280667b1f0e13022d`

### check_constraint_model (`audit-922fd47c92f6`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 69 ms
- **Summary:** All 1 quer(y/ies) held: weightinit-symmetric-zero-diag: pass

**Reasoning:** weightinit-symmetric-zero-diag: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:9d8dd6962bccf7d8074d4011c206c8f4b4e7ba08b7ea484971bd0d0b5694100c`
- **Output content hash:** `sha256:0780c5b61b0d7a803f21951c6598f7318aade06cc2553e4be3f06180d451965c`

### check_constraint_model (`audit-89993c0762c4`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 39 ms
- **Summary:** All 1 quer(y/ies) held: xavier-bounded-by-bound: pass

**Reasoning:** xavier-bounded-by-bound: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:68337c42ad913efba4139e887b952d5397780efe80ba2458ac5ea2e4bcb9fe80`
- **Output content hash:** `sha256:a84653d08cf89195771bc73a712e936ab0a18910c036e1ab9be3fb02026f9383`

### verify_identity (`audit-7f8dabb467c0`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 406 ms
- **Summary:** Symbolic proof established: cos(phi)**2 + sin(phi)**2 == 1.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:73a57d5d595ae446b0e9b793f8551c7d575663058b5e8f293a4eb438b9b880e7`
- **Output content hash:** `sha256:c53d384803bd0770908f4d8e534b667c7311b9acc41275d804dd9c23c4d2a389`

### wolfram_crosscheck (`audit-af46f9677222`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:941e69f3659b961eddbd5b8f4c30826bc8f05768eb50885d53a6bb3a0647ee0b`
- **Output content hash:** `sha256:0991b0764a0f983df85b04ef7388db24af60cae4d49f70bc4a6fd88679a1593a`

### check_constraint_model (`audit-b762f20fe6a0`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 51 ms
- **Summary:** All 1 quer(y/ies) held: pacindex-nonnegative: pass

**Reasoning:** pacindex-nonnegative: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:a63076fd584d2cd162e6b7e9a59ca64652167d51b41124363a289daeeec9103c`
- **Output content hash:** `sha256:d0dd811b33381bfecc765347eb925f06b1d7185b57630d81a0942c3d73214ec6`

### check_constraint_model (`audit-dd904207a9ad`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 49 ms
- **Summary:** All 1 quer(y/ies) held: clamp-finite-bounded: pass

**Reasoning:** clamp-finite-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:139e573206d98bf4f429cee769bf9074c0833f203928a1abb57b1cfd39ca849b`
- **Output content hash:** `sha256:83d3ee70acb16f51c8259bc228307dc2bf9e3d2c3de58f59e60775d86f83db68`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
