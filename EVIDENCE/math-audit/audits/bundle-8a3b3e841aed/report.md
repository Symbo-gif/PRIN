# Audit Evidence Report: bundle-8a3b3e841aed

**Overall status:** `PASS`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T19:57:51.635Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### PW-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** wrap_phase(x) = x.rem_euclid(2*pi), which wraps into [0, 2*pi) (not (-pi, pi]; see integrate.rs:20-21 module doc), has a unique representative: restated without an explicit integer witness tied to x (EMA-001 M-F2 re-encoding after the original 3-free-variable/x-linked encoding timed out) as -- any two reals w1, w2 both lying in [0, 2*pi) whose difference is an integer multiple of 2*pi must be equal. This is a strictly more general statement that implies the original (any x's wrap_phase(x) is the unique representative of x's residue class in [0, 2*pi)), using a single Int witness for the multiple rather than two Ints tied through a shared free Real x.  
- **Code references:** crates/prin-dynamics/src/state.rs:274-277, crates/prin-dynamics/src/state.rs:21  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-be8f32ff29a0

### PW-02 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** chimera.rs's strength-of-incoherence phase-difference wrap is centred on zero: two neighbouring phases that are exactly in phase (raw difference d=0) must produce a wrapped difference z=0, as required for a difference measure whose baseline is perfect coherence (chimera.rs:129-131 documents a centred definition). EMA-001 M-F1 remediation: this claim's constraints now model the corrected formula `((d + pi).rem_euclid(2*pi)) - pi` (chimera.rs's private `centred_wrap` helper post-fix), replacing the pre-fix `d.rem_euclid(2*pi) - pi` this claim originally (correctly) refuted -- see EXECUTIVE_MATH_AUDIT_REPORT_001.md M-F1 for the original Z3-confirmed counterexample (d=0, k=0, w=0, z=-pi) against the unfixed formula.  
- **Code references:** crates/prin-metrics/src/chimera.rs:169-176, crates/prin-metrics/src/chimera.rs:129-131  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-840399a7fb2a

### CL-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** clamp_amplitude bounds any input to [1e-6, 10.0] and is non-decreasing (order-preserving), so it cannot reorder two amplitude values relative to each other during RK-stage clamping.  
- **Code references:** crates/prin-dynamics/src/state.rs:312-329, crates/prin-dynamics/src/state.rs:24-27  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-d9f6a876bdb1

### CL-02 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** clamp_derivative bounds any input to |d| <= 1e4 and never flips its sign (a sign flip would reverse the integration direction).  
- **Code references:** crates/prin-dynamics/src/state.rs:331-343, crates/prin-dynamics/src/state.rs:30  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-86e43fb90efb

### OP-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `critical`  
- **Statement:** The Kuramoto order parameter magnitude r = min(|Z|, 1) is bounded in [0, 1] for any non-negative |Z|, including floating-point overshoot above 1 (WP-010 acceptance invariant).  
- **Code references:** crates/prin-metrics/src/order.rs:33-36, crates/prin-metrics/src/order.rs:123  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-73671ecc1036

### SI-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** For chimera.rs's strength-of-incoherence over a 4-node windowed field, the windowed numerator (mean of |window-averaged z|) never exceeds the unwindowed denominator (mean of |z|), by the triangle inequality -- which is required for SI = 1 - numer/denom to stay in [0, 1].  
- **Code references:** crates/prin-metrics/src/chimera.rs:173-199  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-9a3148bd67e3

### PAC-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** Phase-amplitude coupling's pre-clamp modulation A*(1 + m*cos(theta)) stays non-negative and at most 2*A for any modulation depth m in [0,1] and any cosine value, and the post-clamp result stays within the amplitude bounds [1e-6, 10.0].  
- **Code references:** crates/prin-dynamics/src/pac.rs:216, crates/prin-dynamics/src/pac.rs:228-229, crates/prin-dynamics/src/pac.rs:161-169  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-002a2eb409b3

## Tool invocations

### check_constraint_model (`audit-be8f32ff29a0`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 20 ms
- **Summary:** All 1 quer(y/ies) held: wrap-phase-unique: pass

**Reasoning:** wrap-phase-unique: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:2b5be0592472c424501015882d4b377969e6814a59b1bf8db9e0d4c630ab6aea`
- **Output content hash:** `sha256:c0c775e85dcb8035acca78230113ad09f7b0dbbda3e95cc02d695a0fb7f875ab`

### check_constraint_model (`audit-840399a7fb2a`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 19 ms
- **Summary:** All 1 quer(y/ies) held: si-wrap-centred-at-zero: pass

**Reasoning:** si-wrap-centred-at-zero: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:3f8007351b8f15e4625b5ca10fb6e39f38a1df185ba99f9cd2985b03c4547774`
- **Output content hash:** `sha256:5e11d4235bf19bf733b6d46ceee185b15cd7adbd898d01c0957dafce6be747c5`

### check_constraint_model (`audit-d9f6a876bdb1`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 35 ms
- **Summary:** All 1 quer(y/ies) held: amp-clamp-bounded-monotone: pass

**Reasoning:** amp-clamp-bounded-monotone: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:97d33272c2f5971171d26aff705f345a3c12a072f257a0b6aa930b28bc208ff5`
- **Output content hash:** `sha256:0b98455a2c42eb93faffdaad3ecbe1c62c2f3b16217cb3c2428bb3ccc28cf20c`

### check_constraint_model (`audit-86e43fb90efb`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 11 ms
- **Summary:** All 1 quer(y/ies) held: deriv-clamp-bounded-sign-preserving: pass

**Reasoning:** deriv-clamp-bounded-sign-preserving: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:53ee57a36a3c1a1e957dda375343b0f3e0389bdd37553f0ef263cbaab95e3651`
- **Output content hash:** `sha256:e8ee106d2552e78f7e9ec5aa130ea40877774a577dd24fd2089af4bdcbece198`

### check_constraint_model (`audit-73671ecc1036`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `critical`
- **Duration:** 11 ms
- **Summary:** All 1 quer(y/ies) held: order-parameter-bounded: pass

**Reasoning:** order-parameter-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:7211a196406edb9557cc1f9a7d15b4610519c5b376b796840a3da0f8fb1a1613`
- **Output content hash:** `sha256:4d41242c59c12bb2fd1e8eb46630376f7fa1f33bbf275b07f526327a5865344b`

### check_constraint_model (`audit-9a3148bd67e3`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 14 ms
- **Summary:** All 1 quer(y/ies) held: si-numerator-le-denominator: pass

**Reasoning:** si-numerator-le-denominator: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:2384e783973c0854bade09eed8275ef64b960ae7d7b472b67cd00ab2b2439314`
- **Output content hash:** `sha256:3e4bd93fa474ebff0e17bef87c0998659f7efc3c2642e083924f7bad3f8b6062`

### check_constraint_model (`audit-002a2eb409b3`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 43 ms
- **Summary:** All 1 quer(y/ies) held: pac-modulation-bounded: pass

**Reasoning:** pac-modulation-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:5d4a8483cdfd763a4e17b9ca9ac1c25ec73e10f0202008200069caef7af386a7`
- **Output content hash:** `sha256:f329c31294871d335cd45a04d23eb89a378c999d85d46a69c008fb285b04e84d`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
