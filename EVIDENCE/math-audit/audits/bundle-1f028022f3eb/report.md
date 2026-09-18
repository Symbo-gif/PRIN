# Audit Evidence Report: bundle-1f028022f3eb

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-18T01:12:16.011Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### HUN-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** The Hungarian/Kuhn-Munkres assignment solver in assignment.rs's solve_assignment claims optimal cost 5 for the concrete 3x3 cost matrix [[4,1,3],[2,0,5],[3,2,2]] (per the Rust test square_matrix_matches_known_optimum's brute-force check). This claim independently re-derives the same lower bound from scratch via Z3: over the full integer-programming assignment polytope (row-sum=1, col-sum=1, 0/1 entries) for this exact matrix, no feasible assignment achieves a total cost below 5. This is a from-scratch combinatorial-optimization re-derivation, not a re-execution of the Rust brute-force test or the Rust solver itself.  
- **Code references:** crates/prin-daemon/src/assignment.rs:141-209, crates/prin-daemon/src/assignment.rs:281-296  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-c97011cb97d2

### IOU-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** BBox::iou's non-degenerate branch (i_vol > 0) computes intersection/union, which is bounded in [0,1] whenever the intersection area does not exceed either box's own area (i_vol <= a_vol, i_vol <= b_vol) -- the geometric fact that makes 1-IoU a valid distance in mot.rs's iou_distance_matrix.  
- **Code references:** crates/prin-daemon/src/mot.rs:72-94, crates/prin-daemon/src/mot.rs:103-121  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-6ee38002a273

### COHEN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** cohens_d's pooled-standard-deviation formula sqrt(((n_A-1)*var_A + (n_B-1)*var_B)/(n_A+n_B-2)) (stats.rs:169-182) reduces, in the equal-sample-size/equal-variance special case (n_A=n_B=n, var_A=var_B=v), to exactly sqrt(v) -- the textbook single-group standard deviation, corroborating the pooling formula is not mis-weighted.  
- **Code references:** crates/prin-train/src/stats.rs:156-182  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-048c8241531a

### WELCH-DF-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** welch_t_test's Welch-Satterthwaite degrees-of-freedom formula (a_term+b_term)^2 / (a_term^2/(n_A-1) + b_term^2/(n_B-1)) (stats.rs:237-241), in the equal-variance/equal-sample-size special case (a_term=b_term=t, n_A=n_B=n), reduces to exactly 2*(n-1) -- the standard pooled degrees of freedom n_A+n_B-2 in that limit, corroborating the Satterthwaite formula is encoded correctly rather than transposed or mis-squared.  
- **Code references:** crates/prin-train/src/stats.rs:208-250  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-ac44047fd7b1

### GAMMA-REFLECT-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** log_gamma's reflection-formula branch (stats.rs:294-296, used for x < 0.5) relies on Euler's reflection formula Gamma(x)*Gamma(1-x) = pi/sin(pi*x); this claim independently re-derives that identity via SymPy, corroborating the mathematical fact the branch depends on (not a re-execution of the Lanczos-approximation code itself).  
- **Code references:** crates/prin-train/src/stats.rs:282-307  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-9899e9826d5f

### BETA-SYM-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** student_t_two_tailed_p_value's regularized_incomplete_beta (stats.rs:365-379) normalizes by the complete Beta function B(a,b) = Gamma(a)*Gamma(b)/Gamma(a+b), computed via the log_gamma/exp identity at stats.rs:372-373 (`log_gamma(a+b) - log_gamma(a) - log_gamma(b)`). This claim independently re-derives that normalization from Euler's Beta-integral definition B(a,b) = Integral_0^1 t^(a-1)*(1-t)^(b-1) dt, verifying it equals the Gamma-ratio closed form via SymPy's own (independent) symbolic integration -- not a re-execution of this crate's Lanczos/continued-fraction port.  
- **Code references:** crates/prin-train/src/stats.rs:365-379  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-e4ff8159c4f7

## Tool invocations

### check_constraint_model (`audit-c97011cb97d2`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 11 ms
- **Summary:** All 1 quer(y/ies) held: hungarian-3x3-lower-bound-5: pass

**Reasoning:** hungarian-3x3-lower-bound-5: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:fb830d45ecf44edc8f33e2196302a05116302af5fdd0d26d045cc22225e20f8d`
- **Output content hash:** `sha256:6a771078a6a16fe471751fcc5a316e35431bb5014df6de4a3fef8251f218a244`

### check_constraint_model (`audit-6ee38002a273`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 4 ms
- **Summary:** All 1 quer(y/ies) held: iou-bounded-unit-interval: pass

**Reasoning:** iou-bounded-unit-interval: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:8dbee2f8d815cae37e1b9d4cdfff61945b34fe0d2b9276b4d36ce7754cde2053`
- **Output content hash:** `sha256:263e52bab4c3de9f35cbbabaf373d81f377d4cb2389e36b3f81246a528ec146e`

### verify_identity (`audit-048c8241531a`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 133 ms
- **Summary:** Symbolic proof established: sqrt(((n-1)*v + (n-1)*v)/(n+n-2)) == sqrt(v).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- n > 1
- v > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:807d327957188d9a24458afa91424707e879635b453aa65453ca937a47cb1b79`
- **Output content hash:** `sha256:6000d948592677ffed03d033b21d74d2e8981c4c9a8e5eb5e0b5b8e551072283`

### wolfram_crosscheck (`audit-498e13099e38`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:98b483e8b270a0f97f2f3cebf331a0ee1b45b550b126f280059cfd70338b233d`
- **Output content hash:** `sha256:f58d5e0d36031b2515c861ff94917cf09b65febb2d50159a436cc594868329ae`

### verify_identity (`audit-ac44047fd7b1`) -- `PASS`

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
- **Output content hash:** `sha256:514444e800c986010273ffb0febb1fd6e530df7ed475cc9ca66b56a13321105e`

### wolfram_crosscheck (`audit-3110d7dfaf93`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:848f6d54364e00df33eb8b48e0b7cf273859f309397611e5c5170afd5ec70b2b`
- **Output content hash:** `sha256:5c95dab580d8ea62ce9edf6a1ba7e8087420f5d3a5bdcdea0c45026648ecdac8`

### verify_identity (`audit-9899e9826d5f`) -- `PASS`

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
- **Output content hash:** `sha256:4eb1a5fc9d842974338c7d65be9b4117108d97493e78bd6a84cca4e947367491`

### wolfram_crosscheck (`audit-867b5b166f57`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:3956155d86365f9dd25baeaa266fde4ef8550a2b50f31224f6ac7ff79b8cf882`
- **Output content hash:** `sha256:4bfdef198a57bd14401033c7e7faace1ac1daba501a0b7aa1c29fc2266d33bc5`

### verify_identity (`audit-e4ff8159c4f7`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 1732 ms
- **Summary:** Symbolic proof established: integrate(t**(a-1)*(1-t)**(b-1), (t, 0, 1)) == gamma(a)*gamma(b)/gamma(a+b).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- a > 0
- b > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:11e47c597823c8bc6d9e8c62c944f248c3bd95d12a578e992073b8bd69eaceb2`
- **Output content hash:** `sha256:821603ee4701b5a5430fc7a4224463340719a4bf12d27d37484ec6dffc014ee2`

### wolfram_crosscheck (`audit-b94d174b2503`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:605877257e3c6ba21e9a50e9a7608241a805f65b256fc85221a10473664921bc`
- **Output content hash:** `sha256:fa353e020b1c1dcb568ace8f005032229e0b83b193a843c696ae133df1215693`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
