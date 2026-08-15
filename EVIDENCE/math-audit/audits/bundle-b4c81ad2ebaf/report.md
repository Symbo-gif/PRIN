# Audit Evidence Report: bundle-b4c81ad2ebaf

**Overall status:** `FAIL`
**Policy profile:** `prin-ema` (`sha256:0e1c329642e07f0b71a7f250a60815d3fc9f6ac4f86dda4f3865149ed6c07608`)
**Generated:** 2026-08-14T23:45:55.625Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### PW-01 -- `FAIL`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** wrap_phase(x) = x.rem_euclid(2*pi), which wraps into [0, 2*pi) (not (-pi, pi]; see integrate.rs:20-21 module doc), has a unique representative: any two integer-multiple-of-2*pi-shifted values of x that both land in [0, 2*pi) must be equal.  
- **Code references:** crates/prin-dynamics/src/state.rs:274-277, crates/prin-dynamics/src/state.rs:21  
- **Reason:** a required check could not reach a proof or counterexample (INCONCLUSIVE)  
- **Contributing audits:** audit-bea324884875

### PW-02 -- `FAIL`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** chimera.rs's strength-of-incoherence phase-difference wrap is centred on zero: two neighbouring phases that are exactly in phase (raw difference d=0) must produce a wrapped difference z=0, as required for a difference measure whose baseline is perfect coherence (chimera.rs:129-131 documents a centred definition).  
- **Code references:** crates/prin-metrics/src/chimera.rs:169-171, crates/prin-metrics/src/chimera.rs:129-131  
- **Reason:** at least one required check returned FAIL with a counterexample  
- **Contributing audits:** audit-4c8eb29a1462

### CL-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** clamp_amplitude bounds any input to [1e-6, 10.0] and is non-decreasing (order-preserving), so it cannot reorder two amplitude values relative to each other during RK-stage clamping.  
- **Code references:** crates/prin-dynamics/src/state.rs:312-329, crates/prin-dynamics/src/state.rs:24-27  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-ccd19c4af0ae

### CL-02 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `high`  
- **Statement:** clamp_derivative bounds any input to |d| <= 1e4 and never flips its sign (a sign flip would reverse the integration direction).  
- **Code references:** crates/prin-dynamics/src/state.rs:331-343, crates/prin-dynamics/src/state.rs:30  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-e1970aabe910

### OP-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `critical`  
- **Statement:** The Kuramoto order parameter magnitude r = min(|Z|, 1) is bounded in [0, 1] for any non-negative |Z|, including floating-point overshoot above 1 (WP-010 acceptance invariant).  
- **Code references:** crates/prin-metrics/src/order.rs:33-36, crates/prin-metrics/src/order.rs:123  
- **Reason:** all required checks passed (formal/symbolic corroboration present)  
- **Contributing audits:** audit-5a8d0f72a2bc

### SI-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** For chimera.rs's strength-of-incoherence over a 4-node windowed field, the windowed numerator (mean of |window-averaged z|) never exceeds the unwindowed denominator (mean of |z|), by the triangle inequality -- which is required for SI = 1 - numer/denom to stay in [0, 1].  
- **Code references:** crates/prin-metrics/src/chimera.rs:173-199  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-f627216940eb

### PAC-01 -- `PASS`

- **Type:** `z3_invariant`  
- **Severity:** `medium`  
- **Statement:** Phase-amplitude coupling's pre-clamp modulation A*(1 + m*cos(theta)) stays non-negative and at most 2*A for any modulation depth m in [0,1] and any cosine value, and the post-clamp result stays within the amplitude bounds [1e-6, 10.0].  
- **Code references:** crates/prin-dynamics/src/pac.rs:216, crates/prin-dynamics/src/pac.rs:228-229, crates/prin-dynamics/src/pac.rs:161-169  
- **Reason:** all required checks passed  
- **Contributing audits:** audit-8234878a385f

## Tool invocations

### check_constraint_model (`audit-bea324884875`) -- `INCONCLUSIVE`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 10045 ms
- **Summary:** One or more queries returned Z3 `unknown` (undecidable in the given theory or timed out).

**Reasoning:** wrap-phase-unique: Z3 returned unknown (reason: timeout).

**Limitations:**
- Z3 could not decide at least one query; this is neither a proof nor a disproof.

- **Random seed:** n/a
- **Input content hash:** `sha256:710b8ab5001b3fb8146fdf36a9489b4cb5a6dd01964f04f9c1561b94e1c05ef6`
- **Output content hash:** `sha256:4eb2bbc35bcc7a0d9f9136c433223086fe8f3a54f8eb3eb15fe114a065c38875`

### check_constraint_model (`audit-4c8eb29a1462`) -- `FAIL`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 3 ms
- **Summary:** 1 of 1 quer(y/ies) failed: si-wrap-centred-at-zero: fail - found a model satisfying assumptions AND NOT(invariant): the invariant is violated.

**Reasoning:** si-wrap-centred-at-zero: found a model satisfying assumptions AND NOT(invariant): the invariant is violated.

**Counterexamples:**
- counterexample for query si-wrap-centred-at-zero: `{'k': '0', 'z': '-3141592653589793/1000000000000000', 'd': '0', 'w': '0'}`

- **Random seed:** n/a
- **Input content hash:** `sha256:e97786a29116eac3ee93390e7faa0f687e082a0585683d17b43c32a7635d6042`
- **Output content hash:** `sha256:20a901179da11020c2189c9ec5da362d67614d4f72b08b9a0a82c2c4e081e1aa`

### check_constraint_model (`audit-ccd19c4af0ae`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 3 ms
- **Summary:** All 1 quer(y/ies) held: amp-clamp-bounded-monotone: pass

**Reasoning:** amp-clamp-bounded-monotone: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:97d33272c2f5971171d26aff705f345a3c12a072f257a0b6aa930b28bc208ff5`
- **Output content hash:** `sha256:c34d9d7c57682de7fa9ebb27fbe26f965f301e880ebb576c7588b6fced3f560c`

### check_constraint_model (`audit-e1970aabe910`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `high`
- **Duration:** 4 ms
- **Summary:** All 1 quer(y/ies) held: deriv-clamp-bounded-sign-preserving: pass

**Reasoning:** deriv-clamp-bounded-sign-preserving: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:53ee57a36a3c1a1e957dda375343b0f3e0389bdd37553f0ef263cbaab95e3651`
- **Output content hash:** `sha256:26b03b27847863b6f99a6a6c5dd81fea771149f806547b9b37b1de179aef5b57`

### check_constraint_model (`audit-5a8d0f72a2bc`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `critical`
- **Duration:** 4 ms
- **Summary:** All 1 quer(y/ies) held: order-parameter-bounded: pass

**Reasoning:** order-parameter-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:7211a196406edb9557cc1f9a7d15b4610519c5b376b796840a3da0f8fb1a1613`
- **Output content hash:** `sha256:d39eb8a934d25facb9231bd5fe1d76375bea32d005bca27f9f307d854f368890`

### check_constraint_model (`audit-f627216940eb`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 7 ms
- **Summary:** All 1 quer(y/ies) held: si-numerator-le-denominator: pass

**Reasoning:** si-numerator-le-denominator: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:2384e783973c0854bade09eed8275ef64b960ae7d7b472b67cd00ab2b2439314`
- **Output content hash:** `sha256:30846094d98a5962b6893bb88d72251865f013994da106bac186ef7ba22b9a2c`

### check_constraint_model (`audit-8234878a385f`) -- `PASS`

- **Adapter:** `z3`
- **Severity:** `medium`
- **Duration:** 7 ms
- **Summary:** All 1 quer(y/ies) held: pac-modulation-bounded: pass

**Reasoning:** pac-modulation-bounded: assumptions AND NOT(invariant) is UNSAT: the invariant holds under all satisfying assignments.

- **Random seed:** n/a
- **Input content hash:** `sha256:5d4a8483cdfd763a4e17b9ca9ac1c25ec73e10f0202008200069caef7af386a7`
- **Output content hash:** `sha256:61e9644feefc8ae11645267f1e0fc8f43bb5234392da18947a4ed40cf2852ac4`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
