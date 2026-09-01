# Audit Evidence Report: bundle-47051c338f93

**Overall status:** `FAIL`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T19:55:21.151Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### VJP-DYN-01 -- `FAIL`

- **Type:** `symbolic_identity`  
- **Severity:** `high`  
- **Statement:** dynamics_vjp's central-difference VJP (models.rs:30-117) for a singleton Kuramoto oscillator with mean-field coupling (no coupling term) recovers the analytical Jacobian entries: d(dphase)/d(frequency)=1 (since dphase/dt=omega=frequency), d(damplitude)/d(amplitude)=-gamma (since damplitude/dt=-gamma*(A-A_rest)), and d(dphase)/d(amplitude)=0 (amplitude does not enter the phase equation for mean-field singleton). The central-difference approximation with epsilon=1e-6 matches these analytical values to within O(epsilon^2).  
- **Code references:** crates/prin-dynamics/src/models.rs:30-117  
- **Reason:** a required check failed to execute (TOOL_ERROR); a missing/errored tool is never treated as PASS  
- **Contributing audits:** audit-6e77725526a5

### SPARSITY-01 -- `FAIL`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** SparsityRegularizationLoss::forward (losses.rs:78-96) computes (1 - mean(sigmoid(x/T)) - target)^2. For the concrete input x=[-0.4, 0.0, 0.8, 1.2] with T=0.2 and target=0.6, the loss equals (1 - density - 0.6)^2 where density = mean(sigmoid(x_i/0.2)). This verifies the sigmoid-surrogate L0 penalty formula is encoded correctly.  
- **Code references:** crates/prin-train/src/losses.rs:78-96  
- **Reason:** a required check failed to execute (TOOL_ERROR); a missing/errored tool is never treated as PASS  
- **Contributing audits:** audit-be51dea58f5e

### WEIGHTINIT-SYM-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** oscillatory_weight_init's Coupling kind (weight_init.rs:37-55) produces a symmetric matrix with zero diagonal: (W + W^T)/2 * scale * (1 - I) where I is the identity mask. For any 2x2 input [[a,b],[c,d]], the output is [[0, (b+c)/2*scale], [(b+c)/2*scale, 0]] -- symmetric by construction and zero on the diagonal.  
- **Code references:** crates/prin-train/src/weight_init.rs:37-55  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-809523577608

### WEIGHTINIT-XAV-01 -- `FAIL`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** oscillatory_weight_init's Projection kind (weight_init.rs:56-62) draws values from Uniform(-bound, bound) where bound = gain * sqrt(6/(fan_in + fan_out)) -- the Xavier-uniform initialization formula. Every drawn value is bounded by [-bound, bound] by construction.  
- **Code references:** crates/prin-train/src/weight_init.rs:56-62, crates/prin-train/src/support.rs  
- **Reason:** a required check failed to execute (TOOL_ERROR); a missing/errored tool is never treated as PASS  
- **Contributing audits:** audit-fdd200f23d00

### ORDERPARAM-01 -- `FAIL`

- **Type:** `symbolic_identity`  
- **Severity:** `medium`  
- **Statement:** DiscreteDeltaThetaGamma::order_parameters (bands.rs:507-523) computes per-band Kuramoto order parameters. For synchronized phases (all phases in a band equal to phi), the order parameter r = |mean(exp(i*phi))| = |exp(i*phi)| = 1. This verifies the per-band decomposition correctly applies the Kuramoto order parameter formula to each frequency band independently.  
- **Code references:** crates/prin-train/src/bands.rs:507-523  
- **Reason:** a required check failed to execute (TOOL_ERROR); a missing/errored tool is never treated as PASS  
- **Contributing audits:** audit-1e540acf59e4

### PACINDEX-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** DiscreteDeltaThetaGamma::pac_index (bands.rs:535-580) computes a phase-amplitude coupling modulation index that is always non-negative. The index sums |correlation| / (mean_amplitude + epsilon) over batch elements, where the absolute value ensures each term is non-negative, and mean_amplitude + epsilon > 0 for positive amplitudes.  
- **Code references:** crates/prin-train/src/bands.rs:535-580  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-f28ccf753ff3

### CLAMP-01 -- `FAIL`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** clamp_finite (state.rs:312-340) maps any finite input to [-limit, limit] and any non-finite input (NaN, +inf, -inf) to 0. For finite inputs, the output satisfies -limit <= output <= limit. For non-finite inputs, the output is exactly 0.  
- **Code references:** crates/prin-dynamics/src/state.rs:312-340  
- **Reason:** a required check failed to execute (TOOL_ERROR); a missing/errored tool is never treated as PASS  
- **Contributing audits:** audit-85d7751e71b7

## Tool invocations

### verify_identity (`audit-6e77725526a5`) -- `TOOL_ERROR`

- **Adapter:** `sympy`
- **Severity:** `high`
- **Duration:** 1 ms
- **Summary:** Could not route claim to verify_identity.

**Reasoning:** failed to route claim 'VJP-DYN-01' to 'verify_identity': claim.assumptions did not validate against VerifyIdentityRequest: [{'type': 'greater_than_equal', 'loc': ('precision_digits',), 'msg': 'Input should be greater than or equal to 15', 'input': 6, 'ctx': {'ge': 15}, 'url': 'https://errors.pydantic.dev/2.13/v/greater_than_equal'}]

- **Random seed:** n/a
- **Input content hash:** `sha256:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`
- **Output content hash:** `sha256:c10a0050600c3c6f1ebcc9e6f22e84a2a2e6057bb80040f47b7479158087c872`

### verify_identity (`audit-be51dea58f5e`) -- `TOOL_ERROR`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** Could not route claim to verify_identity.

**Reasoning:** failed to route claim 'SPARSITY-01' to 'verify_identity': claim.assumptions did not validate against VerifyIdentityRequest: [{'type': 'greater_than', 'loc': ('numeric_samples',), 'msg': 'Input should be greater than 0', 'input': 0, 'ctx': {'gt': 0}, 'url': 'https://errors.pydantic.dev/2.13/v/greater_than'}, {'type': 'greater_than_equal', 'loc': ('precision_digits',), 'msg': 'Input should be greater than or equal to 15', 'input': 12, 'ctx': {'ge': 15}, 'url': 'https://errors.pydantic.dev/2.13/v/greater_than_equal'}]

- **Random seed:** n/a
- **Input content hash:** `sha256:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`
- **Output content hash:** `sha256:e9116ad071286f650731857c87221949a30f88a6e72360351b06f48cbff17734`

### check_constraint_model (`audit-809523577608`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 27 ms
- **Summary:** All 1 quer(y/ies) held: weightinit-symmetric-zero-diag: pass

**Reasoning:** weightinit-symmetric-zero-diag: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:9d8dd6962bccf7d8074d4011c206c8f4b4e7ba08b7ea484971bd0d0b5694100c`
- **Output content hash:** `sha256:335cde186bd8eb5b15968a2143fd939ef7b8aad795163e42f0016488676753d0`

### check_constraint_model (`audit-fdd200f23d00`) -- `TOOL_ERROR`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 0 ms
- **Summary:** A constraint was rejected by the security guard.

**Reasoning:** only Implies/If/Not/Abs/And/Or function calls are allowed

- **Random seed:** n/a
- **Input content hash:** `sha256:ff36278e9159883d8f0d9ef373533307c8ee63a82f2bdd34acafaa616a19a2d3`
- **Output content hash:** `sha256:d955e16f4cb226ba23b407c3a52d3f3a0706269cf9fbd2ce6ce833bcf8a15676`

### verify_identity (`audit-1e540acf59e4`) -- `TOOL_ERROR`

- **Adapter:** `sympy`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** Expression rejected by security guard.

**Reasoning:** unknown identifier: 'k'

**Limitations:**
- Input failed restricted-parser validation before any mathematical evaluation occurred.

- **Random seed:** n/a
- **Input content hash:** `sha256:f2ed2bc88f8562560163c3037261b22cab85ae27d152518745eff06c8a7b64f7`
- **Output content hash:** `sha256:56e489bc7a12a80db0fde8d7bab5f695881bc601968deabcc90afee87d743617`

### wolfram_crosscheck (`audit-458520dc75c9`) -- `SKIPPED_BY_POLICY`

- **Adapter:** `wolfram`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** Wolfram adapter unavailable or disabled by policy.

**Reasoning:** Wolfram adapter disabled by policy (adapters.enable_wolfram=false)

**Limitations:**
- No Wolfram evaluation was attempted. This is never treated as a PASS.

- **Random seed:** n/a
- **Input content hash:** `sha256:fb4ed6a1eff30953f895563e0b002c72d524c88b92046a775b7ea5285b417d36`
- **Output content hash:** `sha256:e19888f7eba1e17af2b312f356eb34664fb9c29c1b2a41ac1b8e23d70eefbd7e`

### check_constraint_model (`audit-f28ccf753ff3`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 18 ms
- **Summary:** All 1 quer(y/ies) held: pacindex-nonnegative: pass

**Reasoning:** pacindex-nonnegative: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:a63076fd584d2cd162e6b7e9a59ca64652167d51b41124363a289daeeec9103c`
- **Output content hash:** `sha256:cb200a742c0320d3862325ee21da1550aea7cc78888590bf26df9051d0668e3b`

### check_constraint_model (`audit-85d7751e71b7`) -- `TOOL_ERROR`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 1 ms
- **Summary:** A constraint was rejected by the security guard.

**Reasoning:** only Implies/If/Not/Abs/And/Or function calls are allowed

- **Random seed:** n/a
- **Input content hash:** `sha256:06102a1a73484d74572bb8b01c10bdf866e8787bfac5fb703bcd8d83075a8b71`
- **Output content hash:** `sha256:b151fc8be594a79617be41e40d0351c6feb5aa649e347cc642628ae78aa9a022`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
