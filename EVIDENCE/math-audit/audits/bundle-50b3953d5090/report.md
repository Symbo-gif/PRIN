# Audit Evidence Report: bundle-50b3953d5090

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T19:57:34.838Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### HUN-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** The Hungarian/Kuhn-Munkres assignment solver in assignment.rs's solve_assignment claims optimal cost 5 for the concrete 3x3 cost matrix [[4,1,3],[2,0,5],[3,2,2]] (per the Rust test square_matrix_matches_known_optimum's brute-force check). This claim independently re-derives the same lower bound from scratch via Z3: over the full integer-programming assignment polytope (row-sum=1, col-sum=1, 0/1 entries) for this exact matrix, no feasible assignment achieves a total cost below 5. This is a from-scratch combinatorial-optimization re-derivation, not a re-execution of the Rust brute-force test or the Rust solver itself.  
- **Code references:** crates/prin-daemon/src/assignment.rs:141-209, crates/prin-daemon/src/assignment.rs:281-296  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-56cc3951f903

### IOU-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** BBox::iou's non-degenerate branch (i_vol > 0) computes intersection/union, which is bounded in [0,1] whenever the intersection area does not exceed either box's own area (i_vol <= a_vol, i_vol <= b_vol) -- the geometric fact that makes 1-IoU a valid distance in mot.rs's iou_distance_matrix.  
- **Code references:** crates/prin-daemon/src/mot.rs:72-94, crates/prin-daemon/src/mot.rs:103-121  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-d2b45ab172dd

### COHEN-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** cohens_d's pooled-standard-deviation formula sqrt(((n_A-1)*var_A + (n_B-1)*var_B)/(n_A+n_B-2)) (stats.rs:169-182) reduces, in the equal-sample-size/equal-variance special case (n_A=n_B=n, var_A=var_B=v), to exactly sqrt(v) -- the textbook single-group standard deviation, corroborating the pooling formula is not mis-weighted.  
- **Code references:** crates/prin-train/src/stats.rs:156-182  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-cf6cd602bbed

### WELCH-DF-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** welch_t_test's Welch-Satterthwaite degrees-of-freedom formula (a_term+b_term)^2 / (a_term^2/(n_A-1) + b_term^2/(n_B-1)) (stats.rs:237-241), in the equal-variance/equal-sample-size special case (a_term=b_term=t, n_A=n_B=n), reduces to exactly 2*(n-1) -- the standard pooled degrees of freedom n_A+n_B-2 in that limit, corroborating the Satterthwaite formula is encoded correctly rather than transposed or mis-squared.  
- **Code references:** crates/prin-train/src/stats.rs:208-250  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-8bae2bf10d6b

### GAMMA-REFLECT-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** log_gamma's reflection-formula branch (stats.rs:294-296, used for x < 0.5) relies on Euler's reflection formula Gamma(x)*Gamma(1-x) = pi/sin(pi*x); this claim independently re-derives that identity via SymPy, corroborating the mathematical fact the branch depends on (not a re-execution of the Lanczos-approximation code itself).  
- **Code references:** crates/prin-train/src/stats.rs:282-307  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-ffde243fb0b5

### BETA-SYM-01 -- `PASS`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** student_t_two_tailed_p_value's regularized_incomplete_beta (stats.rs:365-379) normalizes by the complete Beta function B(a,b) = Gamma(a)*Gamma(b)/Gamma(a+b), computed via the log_gamma/exp identity at stats.rs:372-373 (`log_gamma(a+b) - log_gamma(a) - log_gamma(b)`). This claim independently re-derives that normalization from Euler's Beta-integral definition B(a,b) = Integral_0^1 t^(a-1)*(1-t)^(b-1) dt, verifying it equals the Gamma-ratio closed form via SymPy's own (independent) symbolic integration -- not a re-execution of this crate's Lanczos/continued-fraction port.  
- **Code references:** crates/prin-train/src/stats.rs:365-379  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-5a3798818011

## Tool invocations

### check_constraint_model (`audit-56cc3951f903`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 11 ms
- **Summary:** All 1 quer(y/ies) held: hungarian-3x3-lower-bound-5: pass

**Reasoning:** hungarian-3x3-lower-bound-5: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:fb830d45ecf44edc8f33e2196302a05116302af5fdd0d26d045cc22225e20f8d`
- **Output content hash:** `sha256:f8078ee428855f95f4b2392f9bef5c87b1a26e97dee5cd06726295e5c3572b32`

### check_constraint_model (`audit-d2b45ab172dd`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 7 ms
- **Summary:** All 1 quer(y/ies) held: iou-bounded-unit-interval: pass

**Reasoning:** iou-bounded-unit-interval: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:8dbee2f8d815cae37e1b9d4cdfff61945b34fe0d2b9276b4d36ce7754cde2053`
- **Output content hash:** `sha256:07f6a77e46135d9d1d994ee1ed12c818fb3a0dae8716e6392b24c81992956469`

### verify_identity (`audit-cf6cd602bbed`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 148 ms
- **Summary:** Symbolic proof established: sqrt(((n-1)*v + (n-1)*v)/(n+n-2)) == sqrt(v).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- n > 1
- v > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:807d327957188d9a24458afa91424707e879635b453aa65453ca937a47cb1b79`
- **Output content hash:** `sha256:c443dd7dfcb76497221d4a216b661a0fe8adb194ac6f960e4bdf8964131127fb`

### wolfram_crosscheck (`audit-f31dd77e0737`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:98b483e8b270a0f97f2f3cebf331a0ee1b45b550b126f280059cfd70338b233d`
- **Output content hash:** `sha256:7043ead491d8d094a166444690f9515004d6c11d5e09997e0ccdd93e5fa48265`

### verify_identity (`audit-8bae2bf10d6b`) -- `PASS`

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
- **Output content hash:** `sha256:0025cd97151c875ee052e3355e5ac27c0c1f78ca8a4a1560925915393681b38a`

### wolfram_crosscheck (`audit-1e15e3a7deae`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:848f6d54364e00df33eb8b48e0b7cf273859f309397611e5c5170afd5ec70b2b`
- **Output content hash:** `sha256:d6a519822518c6bc9cd1e3784c7ee20f2746da686496dd824f6094de2a8239af`

### verify_identity (`audit-ffde243fb0b5`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 69 ms
- **Summary:** Symbolic proof established: gamma(x)*gamma(1-x) == pi/sin(pi*x).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- x > 0
- x < 1

- **Random seed:** n/a
- **Input content hash:** `sha256:3acb573cc328c668bfdff592032364c448897e494eeb32f2725ec9bd70d4a5be`
- **Output content hash:** `sha256:9ae3ef082d199a3752c83992c7c60f00317c76ab9d73dbdf1a76bab666bd08e4`

### wolfram_crosscheck (`audit-dccd597e9935`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:3956155d86365f9dd25baeaa266fde4ef8550a2b50f31224f6ac7ff79b8cf882`
- **Output content hash:** `sha256:dea535cc2aaee9ff9a4973f64bd040ccc31e588d6fe2de27dc2758d843d3bb18`

### verify_identity (`audit-5a3798818011`) -- `PASS`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 3575 ms
- **Summary:** Symbolic proof established: integrate(t**(a-1)*(1-t)**(b-1), (t, 0, 1)) == gamma(a)*gamma(b)/gamma(a+b).

**Reasoning:** SymPy reduced (lhs - rhs) to 0 via simplification/assumption refinement. This is a genuine symbolic equivalence proof, not a numeric approximation.

**Assumptions:**
- a > 0
- b > 0

- **Random seed:** n/a
- **Input content hash:** `sha256:11e47c597823c8bc6d9e8c62c944f248c3bd95d12a578e992073b8bd69eaceb2`
- **Output content hash:** `sha256:212ad9ebd766c68e68a9ab2ce990a1289b670220907e7d87c5b93e55011253cf`

### wolfram_crosscheck (`audit-8995877c0e91`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `high`
- **Duration:** 0 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:605877257e3c6ba21e9a50e9a7608241a805f65b256fc85221a10473664921bc`
- **Output content hash:** `sha256:39c3e1c6ea1ba2cfc2dffb8914bdf4a6943d973d0f6ca3fe7e518b1cc365e706`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
