# Audit Evidence Report: bundle-8f5043debf14

**Overall status:** `REQUIRES_HUMAN_REVIEW`
**Policy profile:** `prin-ema` (`sha256:ce2a55569334b141336622ea947a63c0da13fdc43f4b0d1bff0fe71df9586bb5`)
**Generated:** 2026-09-01T20:00:14.472Z

> This report is generated evidence from independent audit tools. It is NOT a self-certification by the coding agent that produced the change under review.

## Claim verdicts

### INT-01 -- `REQUIRES_HUMAN_REVIEW`

- **Type:** `ode_property`  
- **Severity:** `high`  
- **Statement:** The forward-Euler integrator (integrate.rs:293-324) is first-order accurate, stays positive, monotone-decreasing, and bounded in [0,1] on the linear test equation y'=-2y, h=0.05, over [0,1].  
- **Code references:** crates/prin-dynamics/src/integrate.rs:293-324, crates/prin-dynamics/src/integrate.rs:256-262  
- **Reason:** high/critical-severity claim passed only numerically; policy requires symbolic or formal (SymPy/Z3/Lean) corroboration before a PASS verdict  
- **Contributing audits:** audit-0b8930eb3242

### INT-02 -- `REQUIRES_HUMAN_REVIEW`

- **Type:** `ode_property`  
- **Severity:** `critical`  
- **Statement:** The RK4 integrator (integrate.rs:406-503, tableau at :330-335) is fourth-order accurate, stays positive, monotone-decreasing, and bounded in [0,1] on the same linear test equation y'=-2y, h=0.1, over [0,1].  
- **Code references:** crates/prin-dynamics/src/integrate.rs:406-503, crates/prin-dynamics/src/integrate.rs:330-335  
- **Reason:** high/critical-severity claim passed only numerically; policy requires symbolic or formal (SymPy/Z3/Lean) corroboration before a PASS verdict  
- **Contributing audits:** audit-66466c938752

### HOPF-01 -- `REQUIRES_HUMAN_REVIEW`

- **Type:** `ode_property`  
- **Severity:** `critical`  
- **Statement:** The Stuart-Landau/Hopf radial flow dr/dt = mu*r - r^3 (limit_cycle_amplitude contract at models.rs:730-737) converges monotonically from below to the stable equilibrium r*=sqrt(mu), instantiated at mu=4 so r*=2.0, without overshoot, staying within [0.5, 2.0] starting from r(0)=0.5.  
- **Code references:** crates/prin-dynamics/src/models.rs:730-737, crates/prin-dynamics/src/models.rs:777  
- **Reason:** high/critical-severity claim passed only numerically; policy requires symbolic or formal (SymPy/Z3/Lean) corroboration before a PASS verdict  
- **Contributing audits:** audit-6792bf23a5d8

### KUR-01 -- `REQUIRES_HUMAN_REVIEW`

- **Type:** `ode_property`  
- **Severity:** `critical`  
- **Statement:** For a 2-oscillator Kuramoto pair with frequency mismatch delta_omega=1 and coupling K=2 (locking regime |delta_omega|<=K), the phase-difference reduction dDelta/dt = delta_omega - K*sin(Delta) converges monotonically to the locked offset Delta*=asin(delta_omega/K)=pi/6, starting from Delta(0)=0.1, without exceeding Delta*.  
- **Code references:** crates/prin-dynamics/src/models.rs:246-281  
- **Reason:** high/critical-severity claim passed only numerically; policy requires symbolic or formal (SymPy/Z3/Lean) corroboration before a PASS verdict  
- **Contributing audits:** audit-82f54d970b25

## Tool invocations

### audit_ode (`audit-0b8930eb3242`) -- `PASS`

- **Adapter:** `scipy`
- **Severity:** `high`
- **Duration:** 207 ms
- **Summary:** Candidate euler integration passed all configured finite-interval checks.

**Reasoning:** Integrated over [0.0, 1.0] and compared against a tight-tolerance DOP853 reference. Max error vs reference at the primary grid: 0.0192. Observed convergence order across 4 refinement level(s): 1.02. Property checks: positivity(y): min value observed = 0.121577 (required > 0.0); monotonicity(y): trajectory is non-increasing; boundedness(y): observed range [0.121577, 1], required [0.0, 1.0].

**Limitations:**
- Numeric evidence is scoped to the tested interval, step size, and tolerances; it is not a proof of convergence for all parameterizations.

**Residuals:**
- max_abs_error_vs_DOP853_reference: 0.01920100107177436
- max_abs_error[y]: 0.01920100107177436 (tolerance 0.02, within: True)

**Metrics:**
- max_global_error_vs_reference: 0.01920100107177436
- observed_convergence_order: 1.0178586311649285

**Artifacts:**
- [Refinement-level global error vs step size](artifacts/convergence.csv) (`sha256:9cc342c6fb1ea2b8f572332e6b9c172d1789426f70b42f60128314171b16dc68`)
- [Candidate trajectory (primary run)](artifacts/trajectory.csv) (`sha256:8d77b28b9608dc3815536129c2beecf16fbe7a471eaa19f6d6ff2092e63bbd3e`)

- **Random seed:** n/a
- **Input content hash:** `sha256:12aa81b13f63da8ed3d09c10c1b451d6ab2a212d5dfeaadee037efc29983cefa`
- **Output content hash:** `sha256:ef946e2346545c775fcd5842a2f6ad6b6082e85f5a46c2fbe3d9b3ead788e578`

### audit_ode (`audit-66466c938752`) -- `PASS`

- **Adapter:** `scipy`
- **Severity:** `critical`
- **Duration:** 161 ms
- **Summary:** Candidate rk4 integration passed all configured finite-interval checks.

**Reasoning:** Integrated over [0.0, 1.0] and compared against a tight-tolerance DOP853 reference. Max error vs reference at the primary grid: 5.8e-06. Observed convergence order across 4 refinement level(s): 4.07. Property checks: positivity(y): min value observed = 0.13534 (required > 0.0); monotonicity(y): trajectory is non-increasing; boundedness(y): observed range [0.13534, 1], required [0.0, 1.0].

**Limitations:**
- Numeric evidence is scoped to the tested interval, step size, and tolerances; it is not a proof of convergence for all parameterizations.

**Residuals:**
- max_abs_error_vs_DOP853_reference: 5.796953527426041e-06
- max_abs_error[y]: 5.796953527426041e-06 (tolerance 0.0001, within: True)

**Metrics:**
- max_global_error_vs_reference: 5.796953527426041e-06
- observed_convergence_order: 4.068398018252371

**Artifacts:**
- [Refinement-level global error vs step size](artifacts/convergence.csv) (`sha256:e2bbcb33aa738b1d51124ad697fd843b234cf67c90ed3c338ad0f37081b4d690`)
- [Candidate trajectory (primary run)](artifacts/trajectory.csv) (`sha256:0add69c6078279c2afe42d727b166ce6308978a182e11755d3b690b4465d12e7`)

- **Random seed:** n/a
- **Input content hash:** `sha256:d00bee3edfb4207bb61608ffdb29f72258fa0cf03ad78e4b9f17af4e2289ddab`
- **Output content hash:** `sha256:ee15f434139ff1ec1e28226c9b41d2f90d312a014cbaa38840dd4f6195672700`

### audit_ode (`audit-6792bf23a5d8`) -- `PASS`

- **Adapter:** `scipy`
- **Severity:** `critical`
- **Duration:** 2031 ms
- **Summary:** Candidate rk4 integration passed all configured finite-interval checks.

**Reasoning:** Integrated over [0.0, 10.0] and compared against a tight-tolerance DOP853 reference. Max error vs reference at the primary grid: 2.94e-08. Observed convergence order across 4 refinement level(s): 2.20. Property checks: positivity(y): min value observed = 0.5 (required > 0.0); monotonicity(y): trajectory is non-decreasing; boundedness(y): observed range [0.5, 2], required [0.5, 2.0]; equilibrium(y): final value 2, expected equilibrium 2.0 (tol 0.0001).

**Limitations:**
- Numeric evidence is scoped to the tested interval, step size, and tolerances; it is not a proof of convergence for all parameterizations.

**Warnings:**
- observed convergence order 2.20 deviates from the theoretical order 4.0 expected for rk4

**Residuals:**
- max_abs_error_vs_DOP853_reference: 2.9431746151331595e-08
- max_abs_error[y]: 2.9431746151331595e-08

**Metrics:**
- max_global_error_vs_reference: 2.9431746151331595e-08
- observed_convergence_order: 2.1985840600027173

**Artifacts:**
- [Refinement-level global error vs step size](artifacts/convergence.csv) (`sha256:7fad39e8f1a2332261bef941db1deb18cd099aa883196ebd55d5c5a72eb35f68`)
- [Candidate trajectory (primary run)](artifacts/trajectory.csv) (`sha256:4b71e4885417db7a25bf1fa67be95fa4be90e5fdf0f42cea77706f066b88393b`)

- **Random seed:** n/a
- **Input content hash:** `sha256:1459a4d070407d617d9de56ed4332742d02405f24d9ae56988c551d5ae727c78`
- **Output content hash:** `sha256:3b060a0684be6639a2d1ef7834d1e9f03e68cfb4cf82da07479e528feadd2cfa`

### audit_ode (`audit-82f54d970b25`) -- `PASS`

- **Adapter:** `scipy`
- **Severity:** `critical`
- **Duration:** 2176 ms
- **Summary:** Candidate rk4 integration passed all configured finite-interval checks.

**Reasoning:** Integrated over [0.0, 20.0] and compared against a tight-tolerance DOP853 reference. Max error vs reference at the primary grid: 1.68e-10. Observed convergence order across 4 refinement level(s): 0.49. Property checks: monotonicity(y): trajectory is non-decreasing; boundedness(y): observed range [0.1, 0.523599], required [0.1, 0.5235987755982988]; equilibrium(y): final value 0.523599, expected equilibrium 0.5235987755982988 (tol 0.0001).

**Limitations:**
- Numeric evidence is scoped to the tested interval, step size, and tolerances; it is not a proof of convergence for all parameterizations.

**Warnings:**
- observed convergence order 0.49 deviates from the theoretical order 4.0 expected for rk4

**Residuals:**
- max_abs_error_vs_DOP853_reference: 1.6757734089267728e-10
- max_abs_error[y]: 1.6757734089267728e-10

**Metrics:**
- max_global_error_vs_reference: 1.6757734089267728e-10
- observed_convergence_order: 0.49327825320264523

**Artifacts:**
- [Refinement-level global error vs step size](artifacts/convergence.csv) (`sha256:2060409544329b6c9994707c08d65f932e81de5a7f0f568afbad4387f3ed9de7`)
- [Candidate trajectory (primary run)](artifacts/trajectory.csv) (`sha256:4298a355d6e158b1b50d654c1c08c947979547a25844602d476fb4f6d8eb4b4f`)

- **Random seed:** n/a
- **Input content hash:** `sha256:b38c4c440ee5f1ae568b79de5d755c119e99f71f71b5f997a70b934ac6490b4a`
- **Output content hash:** `sha256:d330f7ba75d90a4ebc85c193a6f41edd1a01ab3b3736c484121a8316dfd77806`

## Reproducibility

This bundle's `normalized-request.json` and `normalized-result.json` files, together with `policy-snapshot.yaml`, contain everything needed to re-run each tool invocation with the same inputs, policy limits, and (where applicable) random seed.
