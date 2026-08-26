# Audit Evidence Report: bundle-ceec34b3417d

**Overall status:** `FAIL`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-08-26T05:10:19.735Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### HUN-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** The Hungarian/Kuhn-Munkres assignment solver in assignment.rs's solve_assignment claims optimal cost 5 for the concrete 3x3 cost matrix [[4,1,3],[2,0,5],[3,2,2]] (per the Rust test square_matrix_matches_known_optimum's brute-force check). This claim independently re-derives the same lower bound from scratch via Z3: over the full integer-programming assignment polytope (row-sum=1, col-sum=1, 0/1 entries) for this exact matrix, no feasible assignment achieves a total cost below 5. This is a from-scratch combinatorial-optimization re-derivation, not a re-execution of the Rust brute-force test or the Rust solver itself.  
- **Code references:** crates/prin-daemon/src/assignment.rs:141-209, crates/prin-daemon/src/assignment.rs:281-296  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-530bd6edfd9d

### IOU-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** BBox::iou's non-degenerate branch (i_vol > 0) computes intersection/union, which is bounded in [0,1] whenever the intersection area does not exceed either box's own area (i_vol <= a_vol, i_vol <= b_vol) -- the geometric fact that makes 1-IoU a valid distance in mot.rs's iou_distance_matrix.  
- **Code references:** crates/prin-daemon/src/mot.rs:72-94, crates/prin-daemon/src/mot.rs:103-121  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-bb5921f882cd

### COHEN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** cohens_d's pooled-standard-deviation formula sqrt(((n_A-1)*var_A + (n_B-1)*var_B)/(n_A+n_B-2)) (stats.rs:169-182) reduces, in the equal-sample-size/equal-variance special case (n_A=n_B=n, var_A=var_B=v), to exactly sqrt(v) -- the textbook single-group standard deviation, corroborating the pooling formula is not mis-weighted.  
- **Code references:** crates/prin-train/src/stats.rs:156-182  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-2fcd683545e1

### WELCH-DF-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** welch_t_test's Welch-Satterthwaite degrees-of-freedom formula (a_term+b_term)^2 / (a_term^2/(n_A-1) + b_term^2/(n_B-1)) (stats.rs:237-241), in the equal-variance/equal-sample-size special case (a_term=b_term=t, n_A=n_B=n), reduces to exactly 2*(n-1) -- the standard pooled degrees of freedom n_A+n_B-2 in that limit, corroborating the Satterthwaite formula is encoded correctly rather than transposed or mis-squared.  
- **Code references:** crates/prin-train/src/stats.rs:208-250  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-7f39255d4eb0

### GAMMA-REFLECT-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** log_gamma's reflection-formula branch (stats.rs:294-296, used for x < 0.5) relies on Euler's reflection formula Gamma(x)*Gamma(1-x) = pi/sin(pi*x); this claim independently re-derives that identity via SymPy, corroborating the mathematical fact the branch depends on (not a re-execution of the Lanczos-approximation code itself).  
- **Code references:** crates/prin-train/src/stats.rs:282-307  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-c40b12e9c007

### BETA-SYM-01 -- `FAIL`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** student_t_two_tailed_p_value's regularized_incomplete_beta (stats.rs:365-379) normalizes by the complete Beta function B(a,b) = Gamma(a)*Gamma(b)/Gamma(a+b), computed via the log_gamma/exp identity at stats.rs:372-373 (`log_gamma(a+b) - log_gamma(a) - log_gamma(b)`). This claim independently re-derives that normalization from Euler's Beta-integral definition B(a,b) = Integral_0^1 t^(a-1)*(1-t)^(b-1) dt, verifying it equals the Gamma-ratio closed form via SymPy's own (independent) symbolic integration -- not a re-execution of this crate's Lanczos/continued-fraction port.  
- **Code references:** crates/prin-train/src/stats.rs:365-379  
- **Reason:** a required check failed to execute (TOOL_ERROR); a missing/errored tool is never treated as PASS  
- **Contributing audits:** audit-c013d6fa087d

## Tool invocations

### check_constraint_model (`audit-530bd6edfd9d`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 9 ms
- **Summary:** All 1 quer(y/ies) held: hungarian-3x3-lower-bound-5: pass

**Reasoning:** hungarian-3x3-lower-bound-5: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:fb830d45ecf44edc8f33e2196302a05116302af5fdd0d26d045cc22225e20f8d`
- **Output content hash:** `sha256:343ebfd50973d25a1761ec02c09c0c3a015b826eef2cf8e799872332379e668a`

### check_constraint_model (`audit-bb5921f882cd`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 4 ms
- **Summary:** All 1 quer(y/ies) held: iou-bounded-unit-interval: pass

**Reasoning:** iou-bounded-unit-interval: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:8dbee2f8d815cae37e1b9d4cdfff61945b34fe0d2b9276b4d36ce7754cde2053`
- **Output content hash:** `sha256:f3b267f791660c01ec5ad51ad1418ecf4b40a153b186b00b20152213ec0a7f61`

### verify_identity (`audit-2fcd683545e1`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 87 ms
- **Summary:** Symbolic proof established: sqrt(((n-1)*v + (n-1)*v)/(n+n-2)) == sqrt(v).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- n > 1
- v > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:807d327957188d9a24458afa91424707e879635b453aa65453ca937a47cb1b79`
- **Output content hash:** `sha256:7daf87f306ccdd529440d0b6a776121e9b3eec1b17a40f0f4cfea3c40be3f792`

### wolfram_crosscheck (`audit-c56d1ec0a4ff`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:98b483e8b270a0f97f2f3cebf331a0ee1b45b550b126f280059cfd70338b233d`
- **Output content hash:** `sha256:646594f227e47cf085f93aeddd0dea2c4601cdd0c3e3ab0593c8423baa7852e9`

### verify_identity (`audit-7f39255d4eb0`) -- `PASS`

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
- **Output content hash:** `sha256:628111056fe07682214bc810c83b86713c49ec971a54ee576a824a9533221828`

### wolfram_crosscheck (`audit-86c83c94b68d`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:848f6d54364e00df33eb8b48e0b7cf273859f309397611e5c5170afd5ec70b2b`
- **Output content hash:** `sha256:7f3411958d1628c551855e0af66c5fe7e4cdf27fdfd72e2019e724d5ae5ffc96`

### verify_identity (`audit-c40b12e9c007`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 45 ms
- **Summary:** Symbolic proof established: gamma(x)*gamma(1-x) == pi/sin(pi*x).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- x > 0
- x < 1

- **Random seed:** n/a
- **Input content hash:** `sha256:3acb573cc328c668bfdff592032364c448897e494eeb32f2725ec9bd70d4a5be`
- **Output content hash:** `sha256:5c87b6eeea87d08f3dcab46d81c383fe9be21f1e4aa034b77c9003324a759300`

### wolfram_crosscheck (`audit-56dfdffac12a`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:3956155d86365f9dd25baeaa266fde4ef8550a2b50f31224f6ac7ff79b8cf882`
- **Output content hash:** `sha256:bb25d33e09c27504a2e706a14d49966f5b46c79610ac74eb07de915dedf8ea80`

### verify_identity (`audit-c013d6fa087d`) -- `TOOL_ERROR`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Expression rejected by security guard.

**Reasoning:** unknown identifier: 't'

**Limitations:**
- Input failed restricted-parser validation before any mathematical evaluation occurred.

- **Random seed:** n/a
- **Input content hash:** `sha256:43fc61add8a4123dc2bbbf356546f8778f049ddf40a51912cbf0cfc411b6982e`
- **Output content hash:** `sha256:c87e440d5d26283669f5dbfbf0f5415e1182e0a010cb4bf27eaa232172aa27e8`

### wolfram_crosscheck (`audit-c14f9a7eef09`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:605877257e3c6ba21e9a50e9a7608241a805f65b256fc85221a10473664921bc`
- **Output content hash:** `sha256:9afb28dcbf75a1bac8b5794b8efa36abb1bcbf9b79e30b322f0d1c00c151dffd`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
