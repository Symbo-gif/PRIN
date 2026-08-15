# Audit Evidence Report: bundle-031e1b7fe032

**Overall status:** `FAIL`
**Policy profile:** `prin-ema` (`sha256:d19a23a4dff2c96be27ed82c26cd51cfb61bd3161583fce8b8f50aec39219053`)
**Generated:** 2026-08-15T02:29:27.822Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### PW-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** wrap_phase(x) = x.rem_euclid(2*pi), which wraps into [0, 2*pi) (not (-pi, pi]; see integrate.rs:20-21 module doc), has a unique representative: restated without an explicit integer witness tied to x (EMA-001 M-F2 re-encoding after the original 3-free-variable/x-linked encoding timed out) as -- any two reals w1, w2 both lying in [0, 2*pi) whose difference is an integer multiple of 2*pi must be equal. This is a strictly more general statement that implies the original (any x's wrap_phase(x) is the unique representative of x's residue class in [0, 2*pi)), using a single Int witness for the multiple rather than two Ints tied through a shared free Real x.  
- **Code references:** crates/prin-dynamics/src/state.rs:274-277, crates/prin-dynamics/src/state.rs:21  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-99ad1a0188a6

### PW-02 -- `FAIL`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** chimera.rs's strength-of-incoherence phase-difference wrap is centred on zero: two neighbouring phases that are exactly in phase (raw difference d=0) must produce a wrapped difference z=0, as required for a difference measure whose baseline is perfect coherence (chimera.rs:129-131 documents a centred definition).  
- **Code references:** crates/prin-metrics/src/chimera.rs:169-171, crates/prin-metrics/src/chimera.rs:129-131  
- **Reason:** at least one required check returned FAIL with a counterexample  
- **Contributing audits:** audit-4f6340cb5f49

### CL-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** clamp_amplitude bounds any input to [1e-6, 10.0] and is non-decreasing (order-preserving), so it cannot reorder two amplitude values relative to each other during RK-stage clamping.  
- **Code references:** crates/prin-dynamics/src/state.rs:312-329, crates/prin-dynamics/src/state.rs:24-27  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-56cfc68b447d

### CL-02 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** clamp_derivative bounds any input to |d| <= 1e4 and never flips its sign (a sign flip would reverse the integration direction).  
- **Code references:** crates/prin-dynamics/src/state.rs:331-343, crates/prin-dynamics/src/state.rs:30  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-ec4fc9725773

### OP-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `critical`  
- **Statement:** The Kuramoto order parameter magnitude r = min(|Z|, 1) is bounded in [0, 1] for any non-negative |Z|, including floating-point overshoot above 1 (WP-010 acceptance invariant).  
- **Code references:** crates/prin-metrics/src/order.rs:33-36, crates/prin-metrics/src/order.rs:123  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-dedf285efbab

### SI-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** For chimera.rs's strength-of-incoherence over a 4-node windowed field, the windowed numerator (mean of |window-averaged z|) never exceeds the unwindowed denominator (mean of |z|), by the triangle inequality -- which is required for SI = 1 - numer/denom to stay in [0, 1].  
- **Code references:** crates/prin-metrics/src/chimera.rs:173-199  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-f38ff2504926

### PAC-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** Phase-amplitude coupling's pre-clamp modulation A*(1 + m*cos(theta)) stays non-negative and at most 2*A for any modulation depth m in [0,1] and any cosine value, and the post-clamp result stays within the amplitude bounds [1e-6, 10.0].  
- **Code references:** crates/prin-dynamics/src/pac.rs:216, crates/prin-dynamics/src/pac.rs:228-229, crates/prin-dynamics/src/pac.rs:161-169  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-9fd895c4de8b

## Tool invocations

### check_constraint_model (`audit-99ad1a0188a6`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 12 ms
- **Summary:** All 1 quer(y/ies) held: wrap-phase-unique: pass

**Reasoning:** wrap-phase-unique: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:2b5be0592472c424501015882d4b377969e6814a59b1bf8db9e0d4c630ab6aea`
- **Output content hash:** `sha256:60ba6cbfb93ca5c5f878f9bcaed3872bb500450fb1bde4dcbac979f58e4b8abe`

### check_constraint_model (`audit-4f6340cb5f49`) -- `FAIL`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 7 ms
- **Summary:** 1 of 1 quer(y/ies) failed: si-wrap-centred-at-zero: fail - found a model satisfying assumptions AND NOT(invariant): the invariant is violated.

**Reasoning:** si-wrap-centred-at-zero: found a model satisfying assumptions AND NOT(invariant): the invariant is violated.

**Counterexamples:**
- counterexample for query si-wrap-centred-at-zero: `{'k': '0', 'z': '-3141592653589793/1000000000000000', 'd': '0', 'w': '0'}`

- **Random seed:** n/a
- **Input content hash:** `sha256:e97786a29116eac3ee93390e7faa0f687e082a0585683d17b43c32a7635d6042`
- **Output content hash:** `sha256:874c2a1035a21e351b2483601c01d01a6a02082735d9f0b0f2d554f063ac03b9`

### check_constraint_model (`audit-56cfc68b447d`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 18 ms
- **Summary:** All 1 quer(y/ies) held: amp-clamp-bounded-monotone: pass

**Reasoning:** amp-clamp-bounded-monotone: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:97d33272c2f5971171d26aff705f345a3c12a072f257a0b6aa930b28bc208ff5`
- **Output content hash:** `sha256:b5998cec5032906a5412610bde8b50998233da56b4ba75a34677218ffe799bb5`

### check_constraint_model (`audit-ec4fc9725773`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 6 ms
- **Summary:** All 1 quer(y/ies) held: deriv-clamp-bounded-sign-preserving: pass

**Reasoning:** deriv-clamp-bounded-sign-preserving: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:53ee57a36a3c1a1e957dda375343b0f3e0389bdd37553f0ef263cbaab95e3651`
- **Output content hash:** `sha256:c28a1b9bb7ddd6ccc4fcbbc2045e89133138d4f80c14591de263009850fb084c`

### check_constraint_model (`audit-dedf285efbab`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `critical`
- **Duration:** 8 ms
- **Summary:** All 1 quer(y/ies) held: order-parameter-bounded: pass

**Reasoning:** order-parameter-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:7211a196406edb9557cc1f9a7d15b4610519c5b376b796840a3da0f8fb1a1613`
- **Output content hash:** `sha256:f4bc26d481babb31290f2f23c2461bc312f01f8b1af68ad86e3fc96a6977198c`

### check_constraint_model (`audit-f38ff2504926`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 10 ms
- **Summary:** All 1 quer(y/ies) held: si-numerator-le-denominator: pass

**Reasoning:** si-numerator-le-denominator: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:2384e783973c0854bade09eed8275ef64b960ae7d7b472b67cd00ab2b2439314`
- **Output content hash:** `sha256:819f9f296a62d27f8656d8219b1760388c1325eca5202117864c336cff44a69b`

### check_constraint_model (`audit-9fd895c4de8b`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 23 ms
- **Summary:** All 1 quer(y/ies) held: pac-modulation-bounded: pass

**Reasoning:** pac-modulation-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:5d4a8483cdfd763a4e17b9ca9ac1c25ec73e10f0202008200069caef7af386a7`
- **Output content hash:** `sha256:d65e6d7e87cb87b3700744c75ed42bc8c5dfccd88ee536983e9d13f0246ba082`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
