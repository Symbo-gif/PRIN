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
