# Audit Evidence Report: bundle-9d3beddf8c10

**Overall status:** `FAIL`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-08-26T04:47:08.317Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### HUN-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** The Hungarian/Kuhn-Munkres assignment solver in assignment.rs's solve_assignment claims optimal cost 5 for the concrete 3x3 cost matrix [[4,1,3],[2,0,5],[3,2,2]] (per the Rust test square_matrix_matches_known_optimum's brute-force check). This claim independently re-derives the same lower bound from scratch via Z3: over the full integer-programming assignment polytope (row-sum=1, col-sum=1, 0/1 entries) for this exact matrix, no feasible assignment achieves a total cost below 5. This is a from-scratch combinatorial-optimization re-derivation, not a re-execution of the Rust brute-force test or the Rust solver itself.  
- **Code references:** crates/prin-daemon/src/assignment.rs:141-209, crates/prin-daemon/src/assignment.rs:281-296  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-3960d27486fc

### IOU-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** BBox::iou's non-degenerate branch (i_vol > 0) computes intersection/union, which is bounded in [0,1] whenever the intersection area does not exceed either box's own area (i_vol <= a_vol, i_vol <= b_vol) -- the geometric fact that makes 1-IoU a valid distance in mot.rs's iou_distance_matrix.  
- **Code references:** crates/prin-daemon/src/mot.rs:72-94, crates/prin-daemon/src/mot.rs:103-121  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-6c58d9e04ff1

### COHEN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** cohens_d's pooled-standard-deviation formula sqrt(((n_A-1)*var_A + (n_B-1)*var_B)/(n_A+n_B-2)) (stats.rs:169-182) reduces, in the equal-sample-size/equal-variance special case (n_A=n_B=n, var_A=var_B=v), to exactly sqrt(v) -- the textbook single-group standard deviation, corroborating the pooling formula is not mis-weighted.  
- **Code references:** crates/prin-train/src/stats.rs:156-182  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-4f34c764309e

### WELCH-DF-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** welch_t_test's Welch-Satterthwaite degrees-of-freedom formula (a_term+b_term)^2 / (a_term^2/(n_A-1) + b_term^2/(n_B-1)) (stats.rs:237-241), in the equal-variance/equal-sample-size special case (a_term=b_term=t, n_A=n_B=n), reduces to exactly 2*(n-1) -- the standard pooled degrees of freedom n_A+n_B-2 in that limit, corroborating the Satterthwaite formula is encoded correctly rather than transposed or mis-squared.  
- **Code references:** crates/prin-train/src/stats.rs:208-250  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-4d8600968ea5

### GAMMA-REFLECT-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** log_gamma's reflection-formula branch (stats.rs:294-296, used for x < 0.5) relies on Euler's reflection formula Gamma(x)*Gamma(1-x) = pi/sin(pi*x); this claim independently re-derives that identity via SymPy, corroborating the mathematical fact the branch depends on (not a re-execution of the Lanczos-approximation code itself).  
- **Code references:** crates/prin-train/src/stats.rs:282-307  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-f92b774926ca

### BETA-SYM-01 -- `FAIL`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** student_t_two_tailed_p_value computes P(|T|>=|t|) = I_x(df/2, 1/2) via the regularized incomplete beta function (stats.rs:266-277). This claim independently re-derives the beta-function symmetry identity I_x(a,b) + I_(1-x)(b,a) = 1 that the survival-function relation itself rests on, using SymPy's own regularized incomplete beta (betainc_regularized) -- an independent implementation from this crate's hand-rolled Lanczos/continued-fraction port (log_gamma/betacf/regularized_incomplete_beta).  
- **Code references:** crates/prin-train/src/stats.rs:266-379  
- **Reason:** a required check failed to execute (TOOL_ERROR); a missing/errored tool is never treated as PASS  
- **Contributing audits:** audit-48f864c6e0fb

## Tool invocations

### check_constraint_model (`audit-3960d27486fc`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 9 ms
- **Summary:** All 1 quer(y/ies) held: hungarian-3x3-lower-bound-5: pass

**Reasoning:** hungarian-3x3-lower-bound-5: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:fb830d45ecf44edc8f33e2196302a05116302af5fdd0d26d045cc22225e20f8d`
- **Output content hash:** `sha256:b9ac999979415dcbd4629f490f359a8852282bcf0f881589981bd2371a8ee067`

### check_constraint_model (`audit-6c58d9e04ff1`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 4 ms
- **Summary:** All 1 quer(y/ies) held: iou-bounded-unit-interval: pass

**Reasoning:** iou-bounded-unit-interval: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:8dbee2f8d815cae37e1b9d4cdfff61945b34fe0d2b9276b4d36ce7754cde2053`
- **Output content hash:** `sha256:71ac95947c4ec0a69195188832bcb16b17af0f065e8639b26608087c08b76dc5`

### verify_identity (`audit-4f34c764309e`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 105 ms
- **Summary:** Symbolic proof established: sqrt(((n-1)*v + (n-1)*v)/(n+n-2)) == sqrt(v).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- n > 1
- v > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:807d327957188d9a24458afa91424707e879635b453aa65453ca937a47cb1b79`
- **Output content hash:** `sha256:bf98aa967684e11b396b86de82debc4e3edcfc36c640a6edd52b68fb02e91317`

### wolfram_crosscheck (`audit-d5e4e93fafc2`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:98b483e8b270a0f97f2f3cebf331a0ee1b45b550b126f280059cfd70338b233d`
- **Output content hash:** `sha256:beb5bebc66da611622a0e2995adcf31415d5c4a4a8e49ed6adb92fd703a56ba0`

### verify_identity (`audit-4d8600968ea5`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 2 ms
- **Summary:** Symbolic proof established: (t + t)**2 / (t**2/(n-1) + t**2/(n-1)) == 2*(n-1).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- n > 1
- t > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:4845f547378a5d4226c43f94240a746db8a55a7058e2633159ea6809346e5869`
- **Output content hash:** `sha256:4de9069f4fb023abddafbc03372f323e6aea7f538c6141854ca463837283c741`

### wolfram_crosscheck (`audit-4a70bc015e0b`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:848f6d54364e00df33eb8b48e0b7cf273859f309397611e5c5170afd5ec70b2b`
- **Output content hash:** `sha256:46318e78c11bf9d2e94cb476e36b99f360a8653a8bdc99a57aa63615866dbf7b`

### verify_identity (`audit-f92b774926ca`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 41 ms
- **Summary:** Symbolic proof established: gamma(x)*gamma(1-x) == pi/sin(pi*x).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- x > 0
- x < 1

- **Random seed:** n/a
- **Input content hash:** `sha256:3acb573cc328c668bfdff592032364c448897e494eeb32f2725ec9bd70d4a5be`
- **Output content hash:** `sha256:bf73176748c03a2d9a5a7558e65bbf66bc16b65d17173406e79cdf442e84ae3a`

### wolfram_crosscheck (`audit-4152dc7e1623`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:3956155d86365f9dd25baeaa266fde4ef8550a2b50f31224f6ac7ff79b8cf882`
- **Output content hash:** `sha256:4d15d6fdc069c9b2598237be2b1940f67c587a78ab05fe9d184b875f57009137`

### verify_identity (`audit-48f864c6e0fb`) -- `TOOL_ERROR`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Expression rejected by security guard.

**Reasoning:** function not allowed: 'betainc_regularized'

**Limitations:**
- Input failed restricted-parser validation before any mathematical evaluation occurred.

- **Random seed:** n/a
- **Input content hash:** `sha256:eeba92fb54bf2917a21aa6f2a7d97ce08dead306a128233c61eabddcc83d527f`
- **Output content hash:** `sha256:d48b7683bffe3ca3ce52527204b30d07f1c374714550877adafdfc9aaa40c711`

### wolfram_crosscheck (`audit-8492f871ed4a`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:7563bd1bef63f3d4ab0d099dcf1c992450ebae1310c683319685188e8ab520d3`
- **Output content hash:** `sha256:0f9cc73375316da7a39ad8916b237fb5c41be4ef4f8a549b8a7bf514b763f278`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
