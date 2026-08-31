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

WP-010 — Phase metrics and chimera measure parity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Rust ``prin-metrics`` implements the full PRINet 3.0 measurement surface
(``core/measurement.py`` and ``utils/oscillosim.py`` chimera utilities) in
``f64``. Parity is verified at three tolerance tiers:

- **f64 single-runtime paths** at ``rtol=1e-10, atol=1e-12``: order
  parameter, complex order parameter, mean phase coherence, coherence matrix,
  synchronization energy (default + explicit matrix), sparse coherence/energy
  (k=3, k=11), inter-frame correlation. Measured worst-case drift
  **8.58e-16** (~2× machine epsilon, five orders of magnitude inside
  target). 12 parity tests in ``crates/prin-metrics/tests/parity_metrics.rs``.
- **Corpus golden cases** at the registered METRIC tolerance ``rtol=1e-8,
  atol=1e-12`` (amendment #16): 6 cases × 21 snapshots = 126 snapshots
  compared against PRINet-authored golden-corpus arrays. Measured worst-case
  drift **2.75e-15**. 4 corpus tests in
  ``crates/prin-metrics/tests/corpus_metrics.rs``. The
  ``C = (N r² − 1)/(N − 1)`` identity is cross-checked on all corpus data.
- **PSD/chimera f32-hazard paths** at ``1e-6`` (amendment #14 pattern):
  PRINet 3.0 evaluates the PSD resonance signal through a ``complex64``
  intermediate and the chimera utilities in ``torch.float32``; PRIN keeps
  the pure-f64 path. Measured worst-case drift **9.99e-7**. 6 parity tests
  in ``crates/prin-metrics/tests/parity_chimera.rs``. The discrete outputs
  (discontinuity mask, η) match PRINet exactly.

**Invariants verified:** ``R ∈ [0, 1]`` on all 126 corpus snapshots and in
property tests; ``C ∈ [−1, 1]`` likewise; sparse/full coherence both equal
exactly 1 for synchronized phases; sparse energy at ``k=N−1`` equals dense
energy × ``N/(N−1)`` (the ``1/N`` vs ``1/k`` normalization invariant).

**New dependency:** ``rustfft 6.4.1`` (pure-Rust FFT for PSD); ``cargo
audit`` clean, no advisories.

**Metastability** is a PRIN extension (population standard deviation of the
per-snapshot order parameter, bounded by ``[0, 0.5]``) with no PRINet 3.0
analogue; confirmed acceptable under the WP-010 declaration's "metastability"
scope item by the S2 audit.

WP-012 — Exponential and multi-rate integrator parity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Rust ``ExponentialIntegrator`` (direct Padé(13) scaling-and-squaring or
Krylov–Arnoldi exponential Euler) and ``MultiRateIntegrator`` (uniform
RK4/Euler sub-stepping) are compared against PRINet 3.0 ``torch.float64``
reference trajectories in ``crates/prin-dynamics/tests/parity_integrators.rs``
(7 golden-trajectory cases: 4 ``ExponentialIntegrator`` covering Kuramoto
mean-field/full and Stuart–Landau full for 1/5-step integrations, 3
``MultiRateIntegrator`` covering Kuramoto mean-field/full with RK4 and Euler
inner methods for 5-step integrations). Tolerances follow the same tiers as
the WP-008 integrator parity: ``rtol=1e-6, atol=1e-8`` for f32-hazard paths
(amendment #14) and tighter for pure f64 paths.

Two numerical-hazard findings from the S2 audit (``DOCS/audits/012-wp012-audit.md``,
findings WP012-F3 and WP012-F5) were closed in S3 remediation (commit
``2dc641e``):

- ``matrix_exp``, ``phi1_matrix``, and the Krylov solve paths previously
  returned the identity matrix silently when the Padé denominator LU solve
  was singular or near-singular, which could produce a wrong trajectory
  without any error signal. They now propagate
  ``IntegrateError::LinearSolveFailed``, verified by the regression test
  ``matrix_exp_singular_denominator_returns_typed_error``.
- ``ExponentialIntegrator::step``/``::integrate`` did not validate that the
  constructed ``dim`` matched the state size (``3 · state.phase.len()``); a
  mismatch could silently desynchronize the direct/Krylov path decision from
  the actual Jacobian size. They now return
  ``IntegrateError::InvalidDim``, verified by
  ``exp_integrator_dim_mismatch_returns_typed_error`` and
  ``exp_integrator_integrate_dim_mismatch_returns_typed_error``.

**Multi-rate scope clarification (finding WP012-F4, D3, plan amendment #18):**
the S2 audit found that ``MultiRateIntegrator`` applies uniform sub-stepping
to every oscillator rather than band-aware scheduling keyed on
``OscillatorState::freq_band``. This is a justified match to the PRINet 3.0
reference implementation (which also sub-steps uniformly), so it was resolved
by amending the Project Plan §6 WP-012 declaration text rather than by
changing the implementation. Band-aware per-``freq_band`` scheduling remains a
deferred capability.

**No new dependency.** Both integrators reuse ``ndarray`` (already a
workspace dependency for ``matrix_exp``/Arnoldi linear algebra); ``cargo
audit`` and Snyk Open Source report no new advisories.

WP-013 — Continuous band network and temporal-propagation parity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Rust ``BandNetwork`` (continuous ODE right-hand side), its
``theta_gamma_network`` / ``delta_theta_gamma_network`` factories, and the
``TemporalPropagator`` (complex-phasor phase blending + EMA amplitude
blending) are compared against PRINet 3.0 ``prinet==3.0.0``
``ThetaGammaNetwork``, ``DeltaThetaGammaNetwork``, and
``TemporalPhasePropagator`` in two new parity files added in WP-013.

**Band-network parity** (``crates/prin-dynamics/tests/parity_bands.rs``, 12
golden cases):

- Per-mode intra-band derivatives against
  ``prinet ... KuramotoOscillator.compute_derivatives`` for ``mean_field``,
  ``full``, and the reference's ``sparse_knn`` (the mode the reference band
  networks actually use).
- The composed 2-band (``theta_gamma``) and 3-band (``delta_theta_gamma``)
  right-hand sides, including the reference PAC target
  ``A_fast·[1 + m·cos(mean(φ_slow) + offset)]``.
- RK4 golden trajectories at ``n = 1`` and ``n = 10`` steps, ``dt = 0.01``,
  for both ``mean_field`` and the reference networks' ``sparse_knn``.
- ``theoretical_capacity`` vs the reference ``MultiRateIntegrator`` sub-step
  count (``sub_steps = max(1, int(f_fast / f_slow))``) for four frequency
  pairs.

Measured worst-case drift: ``2.22e-16`` (sparse k-NN, the reference mode —
~1 ulp), ``2.74e-9`` (full), ``1.19e-7`` (mean-field, the amendment #14
f32-complex hazard on the order-parameter reduction). Tolerances follow the
same tiers as the WP-007/WP-008 parity: ``1e-12`` for pure f64 paths
(sparse/full), ``1e-6`` relative / ``5e-7`` absolute for the mean-field
f32-complex path.

**Temporal-propagation parity** (``crates/prin-dynamics/tests/parity_temporal.rs``,
6 golden cases):

- A single blend against ``prinet ... TemporalPhasePropagator.propagate``.
- A chained 5-frame golden sequence.
- ``0`` / ``2π`` wrap-around.
- Amplitude-clamp saturation at the lower and upper bounds.
- A directional guard (``parity_reversed_convention_does_not_match``) that
  fails if the ``alpha = 1 − carry_strength`` mapping is read in the reversed
  direction.

Both sides are fully ``f64`` (PRIN's blenders use ``f64`` real and
``Complex64``; PRINet's reference uses ``torch.float64`` and
``torch.complex64`` only where the order-parameter reduction requires it, which
the temporal paths do not). Comparisons are at ``1e-12``; measured drift is
~1 ulp.

**Composition decision (finding WP013-F2 D2, plan amendment #19):** PRINet
3.0's band networks are *steppers* — a per-band ``KuramotoOscillator``, PAC
applied as an instantaneous amplitude assignment between band steps, and a
per-band ``MultiRateIntegrator`` with ``sub_steps = floor(f_fast / f_slow)``
embedded in the network. PRIN's ``BandNetwork`` is instead a single continuous
ODE right-hand side over the concatenated state, so it composes with every
PRIN ``Integrator`` rather than embedding one. Three consequences are accepted
as the intended trajectory and parity-verified: (a) intra-band terms are
identical to the reference for the configured ``CouplingMode``; (b) PAC enters
``dA_fast/dt`` as the relaxation term ``λ_fast·(A_target − A_fast)`` toward the
reference's modulation target (the continuous-time analogue of the reference's
discrete assignment); (c) per-band sub-stepping is supplied by driving the
network with ``MultiRateIntegrator``, with the reference's sub-step count
exposed as ``BandNetwork::theoretical_capacity``. **Whole-network step-for-step
trajectory parity with the reference stepper is therefore not claimed and is
not a WP-013 acceptance criterion**; band/temporal golden-trajectory
acceptance is evidenced by ``parity_bands.rs`` and ``parity_temporal.rs``.

**Blending-convention complement (finding WP013-F6 D4):** PRIN's
``ComplexPhasorBlender::alpha`` and ``EmaAmplitudeBlender::alpha`` weight the
**new** frame; PRINet's ``TemporalPhasePropagator.carry_strength`` /
``amplitude_decay`` weight the **carried** frame. The mapping is
``alpha = 1 − carry_strength`` and ``alpha = 1 − amplitude_decay`` (the
conventions are complements, not synonyms). The parity tests run PRIN with
``alpha = 0.8`` / ``0.7`` against PRINet references generated with
``carry_strength = 0.2`` / ``amplitude_decay = 0.3`` and verify the
complement; the directional guard fails the test if the mapping is read
reversed.

**Integrator-stage defect found and fixed while producing parity evidence
(audit §7.1):** generating band-network golden trajectories required
integrating a ``BandNetwork``, which surfaced a defect not raised in S2:
``make_intermediate_state`` and the DOPRI5 ``stage_state`` in
``crates/prin-dynamics/src/integrate.rs`` set ``freq_band: None`` on every
stage state, so a ``BandNetwork`` could not be driven by RK4/RK45/exponential
integrators at all — stages 2+ lost the band labels and ``compute_derivatives``
failed with ``MissingBandLabels``, contradicting the ``bands`` module
documentation. Both sites now carry ``freq_band`` from the base state; the
labels are fixed rather than evolving, so this is numerically exact and no
existing parity value changed (``parity_integrators.rs``,
``parity_models.rs``, and the 510 corpus cases are unchanged and green).
Regression tests: ``bands::tests::band_network_integrates_with_rk4`` and
``band_network_integrates_with_multi_rate``.

**No new dependency.** The band-network and temporal modules reuse
``KuramotoOscillator`` and ``PhaseAmplitudeCoupling`` from earlier WPs;
``cargo audit``, ``pip-audit``, and Snyk Open Source report no new advisories.

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

WP-036A — Inhibition and sparsification parity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sub-pass 0144A1 compares the Rust-backed ``FeedforwardInhibition``,
``DentateGyrusConverter``, and ``DGLayer`` forwards directly with installed
PRINet 3.0 float64 references in ``tests/test_inhibition_layers.py``. The
measured maximum absolute differences on the registered deterministic case are
``3.33e-16`` (FFI), ``1.67e-16`` (DG converter), and ``1.39e-16`` (DG layer);
all three tests therefore use ``rtol=1e-10, atol=1e-12`` rather than invoking a
hazard tolerance.

``SparsityRegularizationLoss`` uses Burn 0.16.1's f32-internal sigmoid
(DV-018). Its measured absolute reference delta is ``1.19e-9`` on the
registered case, so the parity assertion uses the existing DV-018 tier
``rtol=1e-6, atol=1e-8`` and gradcheck uses ``eps=1e-4`` with the session's
required ``rtol=1e-3, atol=1e-3``.

The DG family composes the existing hard-forward/soft-backward FBI
straight-through estimator. Such an estimator is deliberately not the
Jacobian of one globally smooth forward function; generic finite-difference
``gradcheck`` would therefore be mathematically invalid. The Python gradchecks
run at the stationary FFI readout point ``phase=pi``, where analytical and
finite-difference Jacobians legitimately coincide. Independent Rust autodiff
tests verify nonzero finite gradients to phase, amplitude, ``ffi_scale``, and
``fbi_temperature`` away from that stationary point.

WP-036A — Phase-to-rate and autoencoder parity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sub-pass 0144A2 compares the Rust-backed ``PhaseToRateConverter``,
``PhaseToRateAutoencoder``, and ``DenseAutoencoder`` forwards with installed
PRINet 3.0 float64 references in ``tests/test_autoencoders.py``. The
``phase_to_rate`` softmax, ``softplus``/``relu``/``log_softmax``, and the
``Linear`` stacks use only ``burn-tensor`` elementwise/reduction ops, so none
inherit the DV-018 ``f32``-internal ``sigmoid`` floor. Measured maximum
absolute reference deltas on the registered deterministic cases:
``PhaseToRateConverter`` ``soft`` / ``hard`` / ``annealed``
``2.8e-17`` / ``0.0`` / ``2.8e-17``; ``PhaseToRateAutoencoder``
reconstruction / rates / ``classify`` ``1.1e-16`` / ``5.6e-17`` / ``4.4e-16``;
``DenseAutoencoder`` reconstruction / codes / ``classify``
``1.1e-16`` / ``1.7e-16`` / ``4.4e-16``. All parity assertions use
``rtol=1e-9, atol<=1e-11`` (autoencoders) or ``rtol=1e-12`` (``hard``); no
hazard tolerance is invoked.

Autoencoder forward-parity is measured with the reference model's exact
parameters injected via ``load_reference_weights`` — PRIN's seeded
Xavier-uniform ``Linear`` init deliberately differs from PyTorch's default
Kaiming-uniform ``nn.Linear`` init (only the initial scale is load-bearing;
the ``ResonanceLayer`` precedent).

``PhaseToRateConverter`` keeps a Rust-owned learnable temperature that receives
a softmax gradient in the ``soft`` / ``annealed`` regimes; PRINet 3.0 detaches
it with ``.item()``. This is a forward-identical superset, so it does not
affect parity. The ``annealed`` blend coefficient
``sigmoid(1/max(T, 1e-6) - 1)`` is computed by PRINet 3.0 in the default
float32 dtype (``torch.tensor(...)``) even for a float64 model; at the default
unit temperature it evaluates to exactly ``0.5`` in both dtypes, so no D-4
tolerance loosening is required. A non-unit fixed temperature would surface a
``~1e-7`` float32 artifact governed by the D-4 mechanism.

``hard`` mode reproduces PRINet 3.0's non-differentiable top-``k`` selection
exactly in the forward pass (``rate * top_k_mask``, forward-identical to
``zeros.scatter_(topk_idx, topk_vals)``); Burn autodiff never differentiates
through the discrete selection, so the Python gradcheck runs on ``soft`` only
and ``hard`` gets a straight-through gradient-shape/finiteness assertion plus
an independent Rust autodiff test.

WP-036A — Hierarchical, PAC, and discrete-layer parity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sub-pass 0144A3 compares the Rust-backed ``HierarchicalResonanceLayer``,
``PhaseAmplitudeCouplingLayer``, and ``DiscreteDeltaThetaGammaLayer`` directly
with installed PRINet 3.0 float64 references in
``tests/test_hierarchical_layers.py``. The reference models' exact projection
and dynamics parameters are injected before comparison.

The continuous hierarchical layer's amplitude and wrapped-phase outputs use
``rtol=1e-9, atol=1e-11``. Its fully batched Burn path also matches a stack of
independent vector calls at ``rtol=1e-12, atol=1e-12``; replacing PRINet's
per-sample Python loop is the documented D-5 better-design deviation and does
not alter the equations or parameter layout.

The standalone PAC layer uses ``rtol=1e-8, atol=1e-9`` because PRINet stores
``initial_depth`` as float32 before ``.double()``, leaving an approximately
``6e-9`` scalar discrepancy from PRIN's direct f64 parameter. The discrete
layer uses the governed DV-018 envelope ``rtol=2e-7, atol=2e-8``: Burn 0.16.1's
f32-internal sigmoid produces a measured three-step maximum relative delta of
``1.39e-7`` on the registered case.

All three layers pass float64 ``torch.autograd.gradcheck`` at the required
``rtol=1e-3, atol=1e-3``. The hierarchical check includes both amplitude and
phase cotangents. The discrete check uses ``eps=1e-5`` to rise above the
registered DV-018 finite-difference floor; its required relative and absolute
tolerances are unchanged.

WP-036A — Model container parity (sub-pass 0144A4)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sub-pass 0144A4 rebuilds ``PRINetModel`` in ``prin_train::model`` as an input
``ResonanceLayer``, ``n_layers - 1`` stacked ``ResonanceLayer``\\ s, a
``LayerNorm`` after each, a concept-readout ``Linear``, a logit clamp to
``[-50, 50]``, and a final ``log_softmax``.

**No float64 end-to-end reference exists.** PRINet 3.0's
``PRINetModel.forward`` unconditionally casts the post-resonance hidden state
to ``float32`` (``h = h.float()``) before the readout; on a ``.double()``
model the ``float64`` ``concept_proj`` weights then raise
``RuntimeError: mat1 and mat2 must have the same dtype``. Forward-parity is
therefore established two ways, both on ``tests/test_model.py`` with the
reference model's exact weights injected via ``load_reference_weights``:

- **float64 readout reproduction.** The reference's own submodules
  (``input_layer``, ``layer_norms``, ``concept_proj``) run correctly in
  float64; only the composed ``forward``'s cast is broken. Reproducing the
  documented forward in float64 and comparing to PRIN at a zero input gives a
  measured maximum absolute delta of ``0.0`` (assertion tier
  ``rtol=1e-9, atol=1e-11``).
- **reference float32 forward.** Calling the real
  ``prinet.nn.layers.PRINetModel.forward`` (its working float32 mode) at a
  zero input and comparing to PRIN's float64 output cast back to float32 gives
  a measured maximum absolute delta of ``0.0`` on the registered case; the
  assertion uses the D-4 envelope ``rtol=1e-4, atol=1e-5`` because the only
  source of disagreement in that regime is the f32-vs-f64 hazard.

Both comparisons use a **zero input**, the regime where the composed
``ResonanceLayer`` initial-state encoding coincides exactly with the
reference. ``PRINetModel`` composes the audited ``ResonanceLayer`` unchanged
and inherits its documented FFT-vs-matmul feature-to-oscillator encoding
deviation (plan amendment #19, WP-022/WP-025): for an arbitrary non-zero input
the end-to-end log-probability delta grows to order 1 (measured ``0.99`` on a
small registered case), bounded by — not newly introduced by — that inherited
deviation. The readout head that ``PRINetModel`` itself adds (``LayerNorm`` +
``concept_proj`` + clamp + ``log_softmax``) is additionally checked in
isolation against a hand-computed ``log_softmax(clamp(h @ Wᵀ + b))`` in
``prin_train::model``'s Rust tests (``< 1e-12``).

The float64 ``torch.autograd.gradcheck`` passes at the required
``rtol=1e-3, atol=1e-3`` for ``n_layers = 1`` and ``n_layers = 2``. No
DV-018 tolerance is invoked: the added head is ``LayerNorm`` (mean/variance
reduction), ``Linear``, ``clamp``, and ``log_softmax`` — all ``burn-tensor``
elementwise/reduction ops, none touching the ``f32``-internal ``sigmoid``
floor.

``compile_model`` performs no numerics — it is a guarded ``torch.compile``
passthrough — so it has no parity comparison; it is exercised by a
construct/callable + ``torch.compile`` smoke test and a guard-branch test
(``torch.compile`` removed → the model is returned unchanged).

WP-036D — GPU sparse k-NN f32 dispatch parity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

WP-036D's ``_torch_compat`` GPU dispatch branch (session ``0144I2``) routes a
sparse k-NN derivative evaluation through the ``GpuSparseKuramoto.from_knn_phase``
PyO3 binding to the CubeCL sparse k-NN coupling kernel. Per plan amendment #37
the marshalling boundary is CPU ``float32`` (``prin-kernels`` dispatch is
host-in/host-out); the numerical work runs on the GPU backend CubeCL selects
(CUDA on ``PRIN-GPU-Runner``). The kernel therefore computes in ``f32`` while the
CPU reference path (``KuramotoOscillator.compute_derivatives``) is ``f64`` — the
same f32-vs-f64 truncation hazard class as the amendment #14 mechanism, here
arising from the GPU kernel's working precision rather than a ``torch.complex64``
intermediate.

Measured maximum deviation of the CubeCL ``f32`` sparse k-NN kernel against the
``f64`` CPU reference across the registered dispatch-test cases
(``tests/test_wp036d_gpu_dispatch.py``: ``n=32`` unbatched seed 42; ``n=16``
batch 2 seed 3; ``n=128`` CUDA seed 7):

- ``dphase`` / ``damplitude``: ``max|Δ| ≈ 9.5e-7`` absolute, ``≈ 4.5e-7``
  relative.
- ``dfrequency``: ``max|Δ| ≈ 1.7e-10`` absolute (the frequency-adaptation term
  is near zero for these inputs), ``≈ 5.8e-6`` relative on that vanishing scale.

Disposition: the dispatch-test agreement assertions use ``rtol=1e-5,
atol=1e-5`` (``GPU_ATOL`` / ``GPU_RTOL`` in ``tests/test_wp036d_gpu_dispatch.py``).
This tier matches the Testing Standards §3 default relative tolerance and
loosens only the absolute tolerance one order of magnitude, because the observed
absolute delta (``9.5e-7``) sits at the §3 default ``atol`` of ``1e-6`` with no
working margin for GPU-kernel run-to-run and driver-to-driver ``f32`` variation.
The Rust-side ``from_knn_phase`` kernel-equivalence test
(``crates/prin-py/src/bindings/gpu.rs``) independently asserts agreement with the
``KuramotoOscillator`` ``SparseKnn`` reference within ``1e-4``. This deviation is
tracked with DV-030 (device-resident GPU buffers); a future device-resident path
does not change the kernel's working precision, so this tolerance tier is
expected to persist.
