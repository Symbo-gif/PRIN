# Audit Evidence Report: bundle-1f4209359607

**Overall status:** `FAIL`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T19:55:20.804Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### POLYFIT-01 -- `FAIL`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** polyfit's Vandermonde normal-equations solver (y4q1_stats.rs:301-398) recovers exact coefficients for a linear polynomial y=2x+1 evaluated at x=[0,1,2,3,4]. The normal equations V^T V c = V^T y for the Vandermonde matrix V with exact linear data yield slope=2, intercept=1 -- verifying the Gaussian elimination with partial pivoting is not transposed or mis-indexed.  
- **Code references:** crates/prin-sim/src/y4q1_stats.rs:301-398  
- **Reason:** a required check failed to execute (TOOL_ERROR); a missing/errored tool is never treated as PASS  
- **Contributing audits:** audit-d05452d3fe12

### POLYFIT-02 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** polyfit's normal-equations solution for a quadratic y=x^2 evaluated at x=[-2,-1,0,1,2] recovers coefficients [1,0,0] (a=1, b=0, c=0). The Vandermonde system for exact quadratic data is well-conditioned at these symmetric points, verifying the back-substitution is correct for degree >= 2.  
- **Code references:** crates/prin-sim/src/y4q1_stats.rs:301-398  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-6d05565a5818

### SPATCORR-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** spatial_correlation's lag-0 value is always 1.0 for any non-degenerate (nonzero-variance) 1-D field. At lag=0, the autocorrelation sum reduces to sum(centered_i^2)/N / var, which equals var/var = 1 by definition. This verifies the circular-index formula at the identity lag.  
- **Code references:** crates/prin-sim/src/y4q1_stats.rs:257-285  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-22f2802f2656

### BOOTSTRAP-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** bootstrap_ci for a constant input (all values equal to c) produces a CI of width 0, because every resample mean equals c exactly. This verifies the resampler's degenerate-case behavior: the percentile band collapses to a point when there is no sampling variability.  
- **Code references:** crates/prin-sim/src/y4q1_stats.rs:165-207  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-b79e2f8f63c7

### LNGAMMA-INT-01 -- `FAIL`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** The Lanczos ln_gamma approximation (y4q1_stats.rs:66-89) satisfies ln_gamma(n) = ln((n-1)!) for positive integers n=1,2,3,4,5. This verifies the Lanczos g=7 coefficients and the reflection formula branch produce the correct log-factorial values at integer arguments -- the canonical check for log-gamma implementations.  
- **Code references:** crates/prin-sim/src/y4q1_stats.rs:66-89  
- **Reason:** a required check failed to execute (TOOL_ERROR); a missing/errored tool is never treated as PASS  
- **Contributing audits:** audit-2d3bb4fb35e7

### BETAI-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** The regularized incomplete beta function I_x(a,b) (betai, y4q1_stats.rs:92-108) is bounded in [0,1] for x in [0,1] and positive a,b. At the boundaries: I_0(a,b)=0 and I_1(a,b)=1. This verifies the continued-fraction computation stays within the valid probability range.  
- **Code references:** crates/prin-sim/src/y4q1_stats.rs:92-145  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-810b4e24352a

## Tool invocations

### verify_identity (`audit-d05452d3fe12`) -- `TOOL_ERROR`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Could not route claim to verify_identity.

**Reasoning:** failed to route claim 'POLYFIT-01' to 'verify_identity': claim.assumptions did not validate against VerifyIdentityRequest: [{'type': 'greater_than', 'loc': ('numeric_samples',), 'msg': 'Input should be greater than 0', 'input': 0, 'ctx': {'gt': 0}, 'url': 'https://errors.pydantic.dev/2.13/v/greater_than'}]

- **Random seed:** n/a
- **Input content hash:** `sha256:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`
- **Output content hash:** `sha256:242246a5acd5171b5d45870283f4c92cf7085e652a353020ed4b1b0079ce61f7`

### verify_identity (`audit-6d05565a5818`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 8 ms
- **Summary:** Symbolic proof established: integrate((x**2 - 0*x - 0)**2, (x, -2, 2)) == integrate((x**2)**2, (x, -2, 2)).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:956d9fbe941d8da98de4ac059379cd68e77b00358230ebdd8e7bd6a3dde0ff3c`
- **Output content hash:** `sha256:b18a8e8f428764fdd5ce8fc72b987816923bae754bee9714839fd1e78d71b170`

### wolfram_crosscheck (`audit-f0df19564f70`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 4 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:dfbb6cd339528af3ff44d31f55259784813b68219ebb11f12a5e52fcdd0997a8`
- **Output content hash:** `sha256:236ee0bedcd78c646f1eb98a6d668ee396ef9aa77d995d965707bc25e36ec5a1`

### check_constraint_model (`audit-22f2802f2656`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 11 ms
- **Summary:** All 1 quer(y/ies) held: spatcorr-lag0-is-one: pass

**Reasoning:** spatcorr-lag0-is-one: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:930d264491b58258a7200d3ba5bbb295c158324d333323d354428341b4a9ffbc`
- **Output content hash:** `sha256:4c3e0fd1c5d15f4f879aeec17f1e9243df42ad69c67db3fb7a28bb855c00a60e`

### check_constraint_model (`audit-b79e2f8f63c7`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 4 ms
- **Summary:** All 1 quer(y/ies) held: bootstrap-constant-zero-width: pass

**Reasoning:** bootstrap-constant-zero-width: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:62a3677b19036c0257f1c8e3adde52cc74369c288d8241cdba3cd737ea0c684e`
- **Output content hash:** `sha256:2d9980d04bf9dd4cab8114d0b6fe602e0069ebbafdab97df22b076d3ccc1cb8d`

### verify_identity (`audit-2d3bb4fb35e7`) -- `TOOL_ERROR`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Could not route claim to verify_identity.

**Reasoning:** failed to route claim 'LNGAMMA-INT-01' to 'verify_identity': claim.assumptions did not validate against VerifyIdentityRequest: [{'type': 'greater_than', 'loc': ('numeric_samples',), 'msg': 'Input should be greater than 0', 'input': 0, 'ctx': {'gt': 0}, 'url': 'https://errors.pydantic.dev/2.13/v/greater_than'}]

- **Random seed:** n/a
- **Input content hash:** `sha256:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`
- **Output content hash:** `sha256:22f8543c658e9711cc8864edde94978937911e17edb7085969df66a79ae3eeee`

### check_constraint_model (`audit-810b4e24352a`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 14 ms
- **Summary:** All 1 quer(y/ies) held: betai-bounded-unit-interval: pass

**Reasoning:** betai-bounded-unit-interval: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:e01b11e576e6da501fe28c729d237574e1ebd8b6dd87f6cd1f84386122735785`
- **Output content hash:** `sha256:6b22eeb9ffdc9d2d3e8e19ca4f8782aecc83b77c66721e2fbd7aefd0e90aa1a8`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
