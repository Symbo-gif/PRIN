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

WP-009 — PAC and coupling topology parity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Rust ``PhaseAmplitudeCoupling::modulate`` is compared against hard-coded PRINet
3.0 reference values in ``crates/prin-dynamics/tests/parity_pac.rs`` (9 golden
cases covering basic modulation, default/max/zero depth, single oscillator,
different sizes, phase offset, and amplitude clamping at both the lower and
upper bounds). The modulation formula
``A_out = A_in · [1 + m · cos(mean(φ_slow) + offset)]`` is verified by
hand-computation to full ``f64`` precision against the reference values; the
parity tolerance is ``1e-6`` (amendment #14 f32-truncation tolerance, since
PRINet 3.0's internal ``torch.complex64`` arithmetic introduces up to ~``1e-7``
drift on the modulation path).

The ``1/N`` versus ``1/k`` normalization distinction is asserted by three
tests: ``sparse_knn_k_equals_n_minus_1_equals_full_default`` verifies the exact
``(N-1)/N`` ratio between sparse (``K/k`` with ``k=N-1``) and full (``K/N``)
coupling; ``normalization_one_over_n_explicit_in_mean_field`` verifies specific
derivative values for the synchronized state under mean-field coupling; and
``normalization_one_over_k_explicit_in_sparse`` asserts the explicit ``K/k``
per-edge weight against the actual ``build_phase_knn_index`` neighbour set for
``k=2`` and ``k=3`` (distinguishing ``1/k`` from ``1/N`` via a ``1/N`` divergence
check) plus a shared-neighbour ``K/2`` vs ``K/3`` = ``3/2`` ratio check.

Sparse/full equivalence and k-NN edge properties are covered by 5 edge-property
tests (exact ``k`` neighbours, no self-loops, phase-nearest ordering, symmetric
neighbour property, wrap-around), 1 proptest, and a topology equivalence test.
The ``K / degree`` normalization invariant (total coupling energy per oscillator
= ``K``) is asserted for the odd-clamp case in both ``Ring`` and ``SmallWorld``
builders via ``topology_ring_odd_clamp_preserves_k_over_degree_invariant`` and
``topology_small_world_odd_clamp_preserves_edge_count_and_energy``.

EA-002 — Cross-platform torch reduction noise in derived corpus metrics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The golden corpus stores two derived metric arrays per case
(``order_parameter_traj``, ``mean_phase_coherence_traj``) computed by PRINet
3.0's own measurement functions (``prinet.core.measurement``) on torch CPU
tensors. The corpus was authored on a Windows torch build; the ``parity.yml``
differential job regenerates cases on Linux runners. Torch CPU reductions of
the underlying complex-exponential sums are deterministic per platform but
differ between OS/torch builds at the reduction-order level.

Measured on CI (ubuntu, Python 3.12, EA-002): the two ``kuramoto_mean_field_euler``
representative cases diverged from the committed Windows-authored arrays by up
to ``max_abs_diff ≈ 7.0e-11`` / ``max_rel_diff ≈ 1.27e-9`` on exactly the two
derived metric arrays; all trajectory arrays (the integrated dynamics) passed
the ``rtol=1e-6, atol=1e-8`` trajectory tolerances on every platform.

Disposition: accepted as a preserved reference-implementation numerical hazard
(Project Plan §5, amendment #16). The corpus differential-harness METRIC
tolerance is set to ``rtol=1e-8`` (covers the observed ~1.27e-9 noise floor
with margin, and future macOS regeneration) while remaining two orders of
magnitude tighter than the trajectory tier. The corpus itself is immutable and
unchanged; trajectory tolerances are unchanged; single-runtime metric
verification (WP-010/WP-014 acceptance criteria) still targets ``rtol=1e-10``
because those comparisons do not cross torch builds.
