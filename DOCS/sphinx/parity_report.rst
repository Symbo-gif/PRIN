Parity Report
=============

.. note::
   Published before the first release candidate (Definition of Done #3).
   Reports golden-corpus differential results, tolerances achieved, the full
   benchmark re-run comparison, and any documented numerical deviations from
   PRINet 3.0.

Numerical-deviation register
----------------------------

WP-007 — f64 vs ``torch.complex64`` reference drift
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The PRINet 3.0 reference implementation computes mean-field order parameters
(Kuramoto, Hopf) and the Stuart–Landau complex-amplitude coupling in
``torch.complex64`` (f32) even when the model is constructed with
``dtype=torch.float64``. PRIN's Rust implementation uses ``f64`` real arithmetic
for Kuramoto/Hopf mean-field order parameters and ``num_complex::Complex64``
(f64 complex) for Stuart–Landau.

Consequence: per-step derivative comparisons between PRIN and PRINet 3.0 can
differ by up to approximately ``1e-7`` on the affected paths (Kuramoto mean-field,
Hopf mean-field, all Stuart–Landau coupling modes). Purely real float64 paths
(Kuramoto full/sparse, Hopf full/sparse) agree to within ``1e-12``.

Disposition: accepted as a preserved numerical hazard in Project Plan §5
(amendment #14). Derivative-level parity tests for the affected paths use an
absolute/relative tolerance of ``1e-6`` (see
``crates/prin-dynamics/tests/parity_models.rs``). Trajectory-level comparisons
continue to use the Project Plan tolerances of ``rtol=1e-6, atol=1e-8``; where
per-step drift accumulates beyond those bounds, the comparison is treated as a
statistical or model-order metric rather than a pointwise trajectory failure.

This deviation is tracked and will be re-evaluated when a bit-for-bit f64
reference corpus is regenerated or when an optional f32-complex reference path
is added to ``prin-dynamics``.

WP-008 — Integrator trajectory parity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Rust Euler and RK4 integrators are compared against PRINet 3.0
``torch.float64`` reference trajectories in
``crates/prin-dynamics/tests/parity_integrators.rs`` (16 golden-trajectory
cases covering Kuramoto mean-field/full, Hopf mean-field, and Stuart–Landau
full for 1/5/10-step integrations). Tolerances follow Project Plan §5:
``rtol=1e-6, atol=1e-8`` for single-step comparisons and ``rtol=1e-5,
atol=1e-7`` for multi-step comparisons; pure f64 paths (Kuramoto full) use
``rtol=1e-10, atol=1e-12``. RK4 order-``h^4`` convergence (error ratio ≈ 16)
and RK45 tolerance-property (tighter tolerance → smaller error) are asserted in
both unit and parity tests. The adaptive RK45 (Dormand–Prince) integrator is
validated by property and unit tests rather than direct PRINet trajectory
parity, since PRINet 3.0 did not ship an adaptive RK45 reference path.
