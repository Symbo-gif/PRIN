Migration Guide (PRINet 3.0 → PRIN)
===================================

.. note::
   Written incrementally as symbols land; finalized in Phase 6. Contains the
   symbol-by-symbol mapping table for all 175+ PRINet 3.0 public exports and
   numerical tolerance notes.

New PRIN-only symbols
---------------------

The following symbols are new in PRIN and have no direct PRINet 3.0 equivalent:

- ``prin.parity`` — golden-trajectory corpus, manifest/loader, differential
  harness, and Hypothesis strategies used by the numerical parity program
  (project plan §5).
- ``prin.dlpack`` — zero-copy DLPack tensor exchange between PyTorch and the
  PRIN Rust core (``negate``, ``negate_batched``, ``round_trip``). PRINet 3.0
  performed all computation in Python; PRIN moves numerics to Rust and crosses
  the boundary via DLPack capsules, so this module has no 3.0 counterpart. The
  CPU round-trip and batched boundary paths are validated in WP-003; the CUDA
  round-trip and ``<5%`` training-step overhead target are deferred to the
  Phase 4 trainable-stack work (project plan amendment #7).
- ``prin-kernels::mean_field_rk4`` — single-source CubeCL fused mean-field RK4
  kernel set with CPU/wgpu/cuda dispatch. PRINet 3.0 kept separate
  Triton/CUDA/PyTorch-fallback kernel files; PRIN collapses them into one
  Rust/CubeCL implementation (Phase 0 spike, production suite in Phase 3). The
  Rust public API has no direct PRINet 3.0 Python equivalent at this phase.
- ``prin._ort`` — ONNX Runtime execution-provider probe for the subconscious
  controller (CPU/DirectML/VitisAI with graceful fallback). PRINet 3.0 ran the
  controller in-process with no provider abstraction; PRIN introduces backend
  selection and fallback as a Phase 0 spike, with the full daemon runtime owned
  by WP-028. This is an internal module (underscore prefix) not re-exported from
  ``prin.__all__``.
- ``prin._phase0`` — Phase 0 exit-gate evidence consolidation. Validates the
  three foundation spikes, the golden-trajectory corpus, the abi3 wheel matrix,
  and the recorded go/no-go decisions before the Phase 0 pre-release tag. This
  is an internal module (underscore prefix) not re-exported from
  ``prin.__all__``.
- ``prin-dynamics`` oscillator state and seed (WP-006) — Rust struct-of-arrays
  ``OscillatorState``, deterministic counter-based ``Seed`` authority on
  ``Pcg64``, typed ``StateError``/``SeedError``, numerical guards/clamps
  (phase wrap to ``[0, 2π)``, ``atan2``-safe phase differences, amplitude clamp
  ``[1e-6, 10]``, derivative clamp ``±1e4``), and sort-based phase k-NN index.
  Replaces PRINet 3.0's Python oscillator state in ``core/propagation/oscillator_state.py``.
- ``prin-dynamics`` oscillator models (WP-007) — Rust ``Dynamics`` trait and
  ``KuramotoOscillator``, ``StuartLandauOscillator``, and ``HopfOscillator``
  models with enum-dispatched ``CouplingMode`` (``MeanField``, ``Full``,
  ``SparseKnn``) and ``StateDerivatives`` (``dphase``/``damplitude``/``dfrequency``).
  Replaces PRINet 3.0's Python models in
  ``core/propagation/oscillator_models.py``. The Rust implementation uses ``f64``
  real and ``Complex64`` arithmetic; PRINet 3.0 uses ``torch.complex64`` (f32)
  internally for mean-field order parameters and Stuart–Landau complex amplitudes,
  producing up to ~``1e-7`` per-step drift on the affected paths. This is accepted
  as a preserved numerical hazard (Project Plan §5, amendment #14); derivative
  parity tests use a ``1e-6`` tolerance for affected paths and ``1e-12`` for pure
  float64 paths (see the Parity Report). Python bindings are provided via
  ``prin.dynamics`` (WP-011).
- ``prin-dynamics`` basic integrators (WP-008) — Rust ``Integrator`` trait and
  ``EulerIntegrator``, ``RK4Integrator``, and ``RK45Integrator`` (adaptive
  Dormand–Prince) with explicit reusable buffers, numerical guards, and typed
  ``IntegrateError`` (seven variants at WP-008; ten after WP-012 below).
  Replaces PRINet 3.0's Python integrators
  in ``core/propagation/integrators.py``. The Rust implementation uses ``f64``
  arithmetic throughout; PRINet 3.0's ``torch.float64`` trajectory reference is
  matched at ``rtol=1e-6, atol=1e-8`` (and tighter for pure f64 paths) via 16
  golden-trajectory parity cases in ``crates/prin-dynamics/tests/parity_integrators.rs``.
  RK4 order-``h^4`` convergence and RK45 tolerance properties are asserted in
  both unit and parity tests. Python bindings are provided via ``prin.dynamics``
  (WP-011).
- ``prin-dynamics`` exponential and multi-rate integrators (WP-012) — Rust
  ``ExponentialIntegrator`` (exponential Euler, ``y_{n+1} = exp(hA) y_n +
  h·φ₁(hA)·g(y_n)``, direct Padé(13) scaling-and-squaring or Krylov–Arnoldi
  with adaptive stiff-mode rank) and ``MultiRateIntegrator`` (uniform
  sub-stepping: the outer timestep is divided into ``sub_steps`` equal inner
  RK4/Euler steps applied to all oscillators, matching the PRINet 3.0
  reference implementation — Project Plan amendment #18; band-aware
  per-``freq_band`` scheduling is a deferred capability). Replaces PRINet
  3.0's exponential/multi-rate integrators in
  ``core/propagation/integrators.py``. Adds ``IntegrateError::InvalidDim``,
  ``InvalidKrylovRank``, and ``LinearSolveFailed`` (matrix-exponential/Krylov
  linear-solve failures propagate as typed errors rather than silently
  returning the identity matrix). Verified against PRINet 3.0
  ``torch.float64`` reference trajectories at ``rtol=1e-6, atol=1e-8`` via 7
  golden-trajectory parity cases (4 ``ExponentialIntegrator``, 3
  ``MultiRateIntegrator``) in ``crates/prin-dynamics/tests/parity_integrators.rs``.
  Python bindings ``ExponentialIntegrator`` and ``MultiRateIntegrator`` are
  provided via ``prin.dynamics`` (``python/prin/dynamics.py`` grew from 18 to
  20 symbols); the inner ``MultiRateMethod`` is exposed as a ``"rk4"`` /
  ``"euler"`` string constructor argument rather than a separate Python class.
  21 new Python acceptance tests in ``tests/test_dynamics_bindings.py``.
- ``prin-dynamics`` continuous hierarchical band networks and temporal
  propagation (WP-013) — Rust ``BandParams``, ``PacPair``, ``BandNetwork``
  (implementing ``Dynamics``), ``theta_gamma_network`` /
  ``delta_theta_gamma_network`` factories, ``theoretical_capacity`` (the
  Lisman–Jensen ``floor(f_fast / f_slow)`` working-memory capacity, ~7 for
  typical θ/γ frequencies), ``create_band_state``, and ``BandError`` in
  ``src/bands.rs``; and ``ComplexPhasorBlender``, ``EmaAmplitudeBlender``,
  ``TemporalPropagator``, and ``TemporalError`` in ``src/temporal.rs``.
  Replaces PRINet 3.0's Python ``ThetaGammaNetwork`` /
  ``DeltaThetaGammaNetwork`` in ``core/propagation/networks.py`` and
  ``TemporalPhasePropagator`` in ``core/propagation/temporal.py``.

  **Composition decision (Project Plan amendment #19, finding WP013-F2 D2):**
  PRINet 3.0's band networks are *steppers* — a per-band ``KuramotoOscillator``
  (``coupling_mode="sparse_knn"``), PAC applied as an instantaneous amplitude
  assignment between band steps, and a per-band ``MultiRateIntegrator`` with
  ``sub_steps = floor(f_fast / f_slow)`` embedded in the network. PRIN's
  ``BandNetwork`` is instead a single continuous ODE right-hand side over the
  concatenated state, so it composes with every PRIN ``Integrator`` (RK4, RK45,
  exponential, multi-rate) rather than embedding one. Three consequences are
  accepted as the intended trajectory: (a) intra-band terms are the identical
  Kuramoto equations for the configured ``CouplingMode``, including the
  reference's ``sparse_knn``, and are parity-verified per mode against
  ``prinet==3.0.0`` in ``crates/prin-dynamics/tests/parity_bands.rs``;
  (b) PAC enters ``dA_fast/dt`` as the relaxation term
  ``λ_fast·(A_target − A_fast)`` toward the reference's modulation target
  ``A_fast·[1 + m·cos(mean(φ_slow) + offset)]``, which is the continuous-time
  analogue of the reference's discrete assignment and is parity-verified
  against the reference's ``PhaseAmplitudeCoupling.modulate`` target;
  (c) per-band sub-stepping is supplied by driving the network with
  ``MultiRateIntegrator``, with the reference's sub-step count exposed as
  ``BandNetwork::theoretical_capacity``. Whole-network step-for-step trajectory
  parity with the reference stepper is therefore not claimed and is not a
  WP-013 acceptance criterion; band/temporal golden-trajectory acceptance is
  evidenced by ``parity_bands.rs`` and ``parity_temporal.rs``.

  **Blending-convention complement (finding WP013-F6 D4):** PRIN's
  ``ComplexPhasorBlender::alpha`` and ``EmaAmplitudeBlender::alpha`` weight the
  **new** frame, while PRINet's ``TemporalPhasePropagator.carry_strength`` /
  ``amplitude_decay`` weight the **carried** (previous) frame. The mapping is
  ``alpha = 1 − carry_strength`` and ``alpha = 1 − amplitude_decay`` (the
  conventions are complements, not synonyms). PRIN's "α near 1" means fast
  adaptation to the new frame; PRINet's "carry_strength near 1" means strong
  temporal inertia. The mapping is documented on every type and PyO3 class and
  enforced by ``parity_temporal::parity_reversed_convention_does_not_match``.

  Python bindings ``BandNetwork``, ``BandParams``, ``PacPair``,
  ``create_band_state_py``, ``ComplexPhasorBlender``,
  ``EmaAmplitudeBlender``, and ``TemporalPropagator`` are provided via
  ``prin.dynamics`` (``python/prin/dynamics.py`` grew from 20 to 27 symbols);
  the inner ``BandParams::with_coupling`` exposes the per-band ``CouplingMode``
  rather than a separate Python class. 44 Python acceptance tests in
  ``tests/test_wp013_bands_temporal.py`` cover all binding paths.
- ``prin-dynamics`` phase–amplitude coupling and coupling topologies (WP-009) —
- ``prin-dynamics`` phase–amplitude coupling and coupling topologies (WP-009) —
  Rust ``PhaseAmplitudeCoupling`` struct implementing cross-frequency PAC
  ``A_fast = A_0·[1 + m·cos(φ_slow + offset)]`` with mean slow-band phase,
  broadcast modulation, and amplitude clamp ``[1e-6, 10]``. Replaces PRINet 3.0's
  Python ``PhaseAmplitudeCoupling`` in ``core/propagation/coupling.py``. The Rust
  implementation uses ``f64`` arithmetic; PRINet 3.0's ``torch.complex64`` (f32)
  internal arithmetic produces up to ~``1e-7`` drift on the modulation path, so
  PAC parity tests use a ``1e-6`` tolerance (amendment #14). Also adds the
  ``Topology`` enum (``AllToAll``, ``Ring``, ``SmallWorld``) with ``build_matrix``
  builders producing ``N × N`` coupling matrices with ``K / degree`` per-edge
  normalization, the ``CouplingError`` and ``PacError`` typed error enums, and the
  ``validate_coupling_matrix`` helper. The ``SmallWorld`` variant is a **directed**
  Watts–Strogatz rewiring (outgoing edges only); ``k_ring`` is clamped to the
  largest even number ``≤ N - 1`` to preserve the ``K / degree`` energy invariant.
  Python bindings are provided via ``prin.dynamics`` (WP-011).
- ``prin-metrics`` phase metrics and chimera measures (WP-010) — Rust
  synchronization metrics rebuilding PRINet 3.0 ``core/measurement.py`` and
  the chimera utilities in ``utils/oscillosim.py``. Public API:
  ``kuramoto_order_parameter``, ``kuramoto_order_parameter_complex``,
  ``inter_frame_phase_correlation``, ``order_parameter_series``,
  ``mean_phase_coherence``, ``phase_coherence_matrix``,
  ``sparse_mean_phase_coherence``, ``power_spectral_density``,
  ``extract_concept_probabilities``, ``synchronization_energy``,
  ``sparse_synchronization_energy``, ``local_order_parameter``,
  ``bimodality_index``, ``strength_of_incoherence``,
  ``discontinuity_measure``, ``chimera_index``,
  ``strength_of_incoherence_temporal``, ``metastability``,
  ``build_phase_knn``, and ``MetricError`` (9 variants). All metrics run in
  ``f64``; single-runtime parity targets ``rtol=1e-10`` (measured ≤ 8.58e-16
  on f64 paths). PSD and chimera paths affected by PRINet 3.0's
  ``complex64``/``float32`` internal arithmetic use the documented ``1e-6``
  tolerance (amendment #14). ``metastability`` is a PRIN extension with no
  PRINet 3.0 counterpart (population standard deviation of the per-snapshot
  order parameter, bounded by ``[0, 0.5]``). ``rustfft 6.4.1`` is a new
  workspace dependency for the PSD. Python bindings are provided via
  ``prin.metrics`` (WP-011).
- ``prin-py`` Phase 1 Python API (WP-011) — PyO3 bindings for the complete
  Phase 1 dynamics and metrics surface, accessible through ``prin.dynamics``
  (18 symbols at WP-011, grown to 20 by WP-012 below:
  ``OscillatorState``, ``Seed``, ``StateDerivatives``,
  ``KuramotoOscillator``, ``StuartLandauOscillator``, ``HopfOscillator``,
  ``CouplingMode``, ``Topology``, ``PhaseAmplitudeCoupling``,
  ``EulerIntegrator``, ``RK4Integrator``, ``RK45Integrator``,
  ``AdaptiveResult``, and numeric constants) and ``prin.metrics`` (22 symbols:
  all order, coherence, spectral, energy, chimera, metastability, and k-NN
  functions). Both modules are pure re-exports from ``prin._prin_core`` — no
  Python numerics; all numerical authority remains in Rust. Complete type stubs
  in ``_prin_core.pyi``. 69 Python acceptance tests in
  ``tests/test_dynamics_bindings.py`` exercise all binding paths.
