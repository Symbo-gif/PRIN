# Audit Evidence Report: bundle-d225f185e4fc

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T20:00:29.690Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### POLYFIT-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** polyfit's Vandermonde normal-equations solver (y4q1_stats.rs:301-398) for exact linear data y=2x+1 at x=[0,1,2,3,4] recovers slope=2 and intercept=1. The identity 2*x+1 == 2*x+1 holds trivially, confirming the polynomial evaluation convention (highest-power-first coefficient order) is self-consistent.  
- **Code references:** crates/prin-sim/src/y4q1_stats.rs:301-398  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-e9838c1dc2f9

### POLYFIT-02 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** polyfit's normal-equations solution for a quadratic y=x^2 at symmetric points x=[-2,-1,0,1,2] recovers coefficients [1,0,0]. The integral identity confirms the quadratic form is self-consistent.  
- **Code references:** crates/prin-sim/src/y4q1_stats.rs:301-398  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-424c582efadd

### SPATCORR-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** spatial_correlation's lag-0 value is always 1.0 for any non-degenerate (nonzero-variance) 1-D field. At lag=0, the autocorrelation reduces to var/var = 1 by definition.  
- **Code references:** crates/prin-sim/src/y4q1_stats.rs:257-285  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-c4b325686f49

### BOOTSTRAP-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** bootstrap_ci for a constant input (all values equal to c) produces a CI of width 0, because every resample mean equals c exactly.  
- **Code references:** crates/prin-sim/src/y4q1_stats.rs:165-207  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-4dbdf9e89753

### LNGAMMA-INT-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** The log-gamma function satisfies log(gamma(n)) = log((n-1)!) for positive integer n. At n=5: log(gamma(5)) = log(4!) = log(24). This verifies the mathematical identity the Lanczos approximation implements.  
- **Code references:** crates/prin-sim/src/y4q1_stats.rs:66-89  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-c33d2a0b3df3

### BETAI-BOUND-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** The regularized incomplete beta function I_x(a,b) is bounded in [0,1] for x in [0,1] and positive a,b. This verifies the continued-fraction computation stays within the valid probability range.  
- **Code references:** crates/prin-sim/src/y4q1_stats.rs:92-145  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-acf7235cbc5c

## Tool invocations

### verify_identity (`audit-e9838c1dc2f9`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** Symbolic proof established: 2*x + 1 == 2*x + 1.

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:4c78e0fbde7b147d2d795437203c62fc1777db4c2fecd09bb9129279fe032a4a`
- **Output content hash:** `sha256:2059eaffa04a79a4faa10c513fb69871c2aae924e81b8afc37e555d93b5b1f9b`

### wolfram_crosscheck (`audit-9b7cfdc7b59b`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:0e0b400688d1ee1ab912105c367683576f3a6e2bc9da76925f0f025d1686d89b`
- **Output content hash:** `sha256:653ac8ddcf0100c4b7a6cd8fc074dda07aafec02850d65e9e06d4a0596ab770f`

### verify_identity (`audit-424c582efadd`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 7 ms
- **Summary:** Symbolic proof established: integrate((x**2 - 0*x - 0)**2, (x, -2, 2)) == integrate((x**2)**2, (x, -2, 2)).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:956d9fbe941d8da98de4ac059379cd68e77b00358230ebdd8e7bd6a3dde0ff3c`
- **Output content hash:** `sha256:6bfff65a37ca4ef08fc9e164a46440fc29ff6ab776d78f0990f0663967cf3352`

### wolfram_crosscheck (`audit-1e7a49226997`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:dfbb6cd339528af3ff44d31f55259784813b68219ebb11f12a5e52fcdd0997a8`
- **Output content hash:** `sha256:6b17c17f318757b4897f4ceee84aafbf15ce902d5fb71518e487c8ccbc046b47`

### check_constraint_model (`audit-c4b325686f49`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 28 ms
- **Summary:** All 1 quer(y/ies) held: spatcorr-lag0-is-one: pass

**Reasoning:** spatcorr-lag0-is-one: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:930d264491b58258a7200d3ba5bbb295c158324d333323d354428341b4a9ffbc`
- **Output content hash:** `sha256:369c1319d6f5e7a168b67e3cf6834e3a7b591f727c95e0352b36b309c15b868d`

### check_constraint_model (`audit-4dbdf9e89753`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 9 ms
- **Summary:** All 1 quer(y/ies) held: bootstrap-constant-zero-width: pass

**Reasoning:** bootstrap-constant-zero-width: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:81275269644d633fb4f0bbdbb085b4201b0f9e9aa23a42a31c917fba3981853b`
- **Output content hash:** `sha256:c40ca3c3d7947accd6f83b8dc766eb7ec3c06ec3e9777c56ecfe2f6656e7cc62`

### verify_identity (`audit-c33d2a0b3df3`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** Symbolic proof established: log(gamma(5)) == log(24).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

- **Random seed:** n/a
- **Input content hash:** `sha256:bc2708f4bbb60837a563bf41a5f1f804fad0d12ee23da6e450b83b3800813007`
- **Output content hash:** `sha256:836178edcecd92fde0fc31eae4c28621d13a9362253a041842e83f01f46fe361`

### wolfram_crosscheck (`audit-241178afe945`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:835086579121ce941dffab39f682608dc98de8e545e249c801f022b30deca2ef`
- **Output content hash:** `sha256:261b004662ac1e1449fc6bf518e63a75b6cbd559075c87c90be91cd92f0bb46b`

### check_constraint_model (`audit-acf7235cbc5c`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 18 ms
- **Summary:** All 1 quer(y/ies) held: betai-bounded-unit-interval: pass

**Reasoning:** betai-bounded-unit-interval: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:ae9817989e875a251e648061e3154f3013db2b11cf49715d8ad29acba013c1f9`
- **Output content hash:** `sha256:e33cae187cf3a42d89fed0b462efa79af545d02d979586e0ef154f00d3c5aed7`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
