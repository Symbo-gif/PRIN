# Audit Evidence Report: bundle-83cd0a683ec1

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:d19a23a4dff2c96be27ed82c26cd51cfb61bd3161583fce8b8f50aec39219053`)
**Generated:** 2026-08-15T02:30:11.061Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### PW-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** wrap_phase(x) = x.rem_euclid(2*pi), which wraps into [0, 2*pi) (not (-pi, pi]; see integrate.rs:20-21 module doc), has a unique representative: restated without an explicit integer witness tied to x (EMA-001 M-F2 re-encoding after the original 3-free-variable/x-linked encoding timed out) as -- any two reals w1, w2 both lying in [0, 2*pi) whose difference is an integer multiple of 2*pi must be equal. This is a strictly more general statement that implies the original (any x's wrap_phase(x) is the unique representative of x's residue class in [0, 2*pi)), using a single Int witness for the multiple rather than two Ints tied through a shared free Real x.  
- **Code references:** crates/prin-dynamics/src/state.rs:274-277, crates/prin-dynamics/src/state.rs:21  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-78cdb8867ecc

### PW-02 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** chimera.rs's strength-of-incoherence phase-difference wrap is centred on zero: two neighbouring phases that are exactly in phase (raw difference d=0) must produce a wrapped difference z=0, as required for a difference measure whose baseline is perfect coherence (chimera.rs:129-131 documents a centred definition). EMA-001 M-F1 remediation: this claim's constraints now model the corrected formula `((d + pi).rem_euclid(2*pi)) - pi` (chimera.rs's private `centred_wrap` helper post-fix), replacing the pre-fix `d.rem_euclid(2*pi) - pi` this claim originally (correctly) refuted -- see EXECUTIVE_MATH_AUDIT_REPORT_001.md M-F1 for the original Z3-confirmed counterexample (d=0, k=0, w=0, z=-pi) against the unfixed formula.  
- **Code references:** crates/prin-metrics/src/chimera.rs:169-176, crates/prin-metrics/src/chimera.rs:129-131  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-6af81ed0820e

### CL-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** clamp_amplitude bounds any input to [1e-6, 10.0] and is non-decreasing (order-preserving), so it cannot reorder two amplitude values relative to each other during RK-stage clamping.  
- **Code references:** crates/prin-dynamics/src/state.rs:312-329, crates/prin-dynamics/src/state.rs:24-27  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-9060041dfe27

### CL-02 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** clamp_derivative bounds any input to |d| <= 1e4 and never flips its sign (a sign flip would reverse the integration direction).  
- **Code references:** crates/prin-dynamics/src/state.rs:331-343, crates/prin-dynamics/src/state.rs:30  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-5d3ac085511f

### OP-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `critical`  
- **Statement:** The Kuramoto order parameter magnitude r = min(|Z|, 1) is bounded in [0, 1] for any non-negative |Z|, including floating-point overshoot above 1 (WP-010 acceptance invariant).  
- **Code references:** crates/prin-metrics/src/order.rs:33-36, crates/prin-metrics/src/order.rs:123  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-2b64d39312f2

### SI-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** For chimera.rs's strength-of-incoherence over a 4-node windowed field, the windowed numerator (mean of |window-averaged z|) never exceeds the unwindowed denominator (mean of |z|), by the triangle inequality -- which is required for SI = 1 - numer/denom to stay in [0, 1].  
- **Code references:** crates/prin-metrics/src/chimera.rs:173-199  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-9e55efd1fcf7

### PAC-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** Phase-amplitude coupling's pre-clamp modulation A*(1 + m*cos(theta)) stays non-negative and at most 2*A for any modulation depth m in [0,1] and any cosine value, and the post-clamp result stays within the amplitude bounds [1e-6, 10.0].  
- **Code references:** crates/prin-dynamics/src/pac.rs:216, crates/prin-dynamics/src/pac.rs:228-229, crates/prin-dynamics/src/pac.rs:161-169  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-c20cf288c44b

## Tool invocations

### check_constraint_model (`audit-78cdb8867ecc`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 27 ms
- **Summary:** All 1 quer(y/ies) held: wrap-phase-unique: pass

**Reasoning:** wrap-phase-unique: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:2b5be0592472c424501015882d4b377969e6814a59b1bf8db9e0d4c630ab6aea`
- **Output content hash:** `sha256:de283991bbd60ac4b8ee48c1be632adba33956421ca364f954d310988414eccd`

### check_constraint_model (`audit-6af81ed0820e`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 9 ms
- **Summary:** All 1 quer(y/ies) held: si-wrap-centred-at-zero: pass

**Reasoning:** si-wrap-centred-at-zero: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:3f8007351b8f15e4625b5ca10fb6e39f38a1df185ba99f9cd2985b03c4547774`
- **Output content hash:** `sha256:5eaede81861f81f96492d27c0fec86e50beb97d40b897a6c2047e03f71c94dd3`

### check_constraint_model (`audit-9060041dfe27`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 4 ms
- **Summary:** All 1 quer(y/ies) held: amp-clamp-bounded-monotone: pass

**Reasoning:** amp-clamp-bounded-monotone: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:97d33272c2f5971171d26aff705f345a3c12a072f257a0b6aa930b28bc208ff5`
- **Output content hash:** `sha256:210560ae0271a07e618eef87dae227da54fe69c1750246c301827fc83c8101b1`

### check_constraint_model (`audit-5d3ac085511f`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 5 ms
- **Summary:** All 1 quer(y/ies) held: deriv-clamp-bounded-sign-preserving: pass

**Reasoning:** deriv-clamp-bounded-sign-preserving: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:53ee57a36a3c1a1e957dda375343b0f3e0389bdd37553f0ef263cbaab95e3651`
- **Output content hash:** `sha256:c4528a16fb7bbb937137c99d9f4f664b2029289536a3c96cf6e6e6c3d119f89d`

### check_constraint_model (`audit-2b64d39312f2`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `critical`
- **Duration:** 2 ms
- **Summary:** All 1 quer(y/ies) held: order-parameter-bounded: pass

**Reasoning:** order-parameter-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:7211a196406edb9557cc1f9a7d15b4610519c5b376b796840a3da0f8fb1a1613`
- **Output content hash:** `sha256:46d444ad60c086b5e55b940555cc7e3c037a95d126c492ad10470ef92dcd6344`

### check_constraint_model (`audit-9e55efd1fcf7`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 8 ms
- **Summary:** All 1 quer(y/ies) held: si-numerator-le-denominator: pass

**Reasoning:** si-numerator-le-denominator: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:2384e783973c0854bade09eed8275ef64b960ae7d7b472b67cd00ab2b2439314`
- **Output content hash:** `sha256:00ddde658aaedef8591106d6a622a29aefb539f7390b64afeee0a369975d418f`

### check_constraint_model (`audit-c20cf288c44b`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 12 ms
- **Summary:** All 1 quer(y/ies) held: pac-modulation-bounded: pass

**Reasoning:** pac-modulation-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:5d4a8483cdfd763a4e17b9ca9ac1c25ec73e10f0202008200069caef7af386a7`
- **Output content hash:** `sha256:6d3c6f5ec05b3855df130dd770ff74e23a303334f5814f7fcdbb9d007945fcf2`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
