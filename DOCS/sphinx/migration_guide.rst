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
  kernel set with CPU/wgpu/cuda dispatch and automatic ``step_auto`` fallback
  (tries wgpu → CUDA → CubeCL CPU, finally native ``step_cpu``). PRINet 3.0
  kept separate Triton/CUDA/PyTorch-fallback kernel files; PRIN collapses them
  into one Rust/CubeCL implementation. The Rust public API has no direct
  PRINet 3.0 Python equivalent at this phase.

  **WP-018 additions:** ``order_param_block_reduce`` (a new
  ``#[cube(launch)]`` kernel) and ``order_param_device`` (host helper)
  implement a hierarchical device-side reduction — each 256-thread cube
  block reduces its slice on-device, and the host finishes over
  ``ceil(N/256)`` partials with an ``f64`` accumulator — replacing the prior
  ``O(N)`` full-state host read-back with an ``O(N/256)`` partial read-back.
  The single authoritative ``order_param`` CPU reference now also accumulates
  in ``f64``. ``step_cubecl_with_pool`` wraps its 8-launch sequence in
  ``ComputeClient::profile``; the new ``TimingMethod`` enum
  (``Device``/``System``) and ``StepReport::timing_method`` field report
  whether the reported time is a real hardware device-event timestamp (wgpu)
  or a host wall-clock fallback (CubeCL-CPU), replacing the WP-004/WP-017
  wall-clock-only prototype. PRINet 3.0's Triton kernel performs the
  equivalent two-level reduction (per-block partial, then a device-side
  ``f32`` atomic accumulate); PRIN's one deliberate, documented divergence is
  a host-side ``f64`` final combine, chosen because ``f64`` accumulation of
  reductions is a Coding Standards §2.2 requirement and the local wgpu (DX12)
  backend has no portable device-side ``f64``. New
  ``MeanFieldRk4Error::ProfilingFailed`` error variant.
- ``prin-kernels::sparse_knn`` — ``SparseKnnGraph`` (CSR sparse phase-neighbor
  graph with ``from_csr`` / ``from_phase_knn`` constructors),
  ``sparse_knn_derivatives_cpu`` (CPU reference for Kuramoto-style sparse
  coupling with per-row ``K/degree(i)`` normalization and ``f64``-accumulated
  sums), ``sparse_knn_coupling_cubecl`` / ``try_*`` / ``_auto`` (single-source
  CubeCL gather kernel, one GPU thread per oscillator walking its own CSR row).
  PRINet 3.0 computed sparse k-NN coupling in Python via
  ``oscillator_models.py``'s ``CouplingMode.SparseKnn``; PRIN moves it to a
  single-source CubeCL kernel with the same per-row ``K/degree(i)``
  normalization convention.

  **WP-019 additions:** ``pac::PacParams`` / ``pac::PacError`` /
  ``pac_modulate_cpu`` / ``pac_modulate_cubecl`` — PAC modulation kernel set
  (``A_out = clamp(A_fast · [1 + m·cos(mean(φ_slow) + offset)], amp_min,
  amp_max)``) with a two-stage CubeCL kernel (``pac_phase_sum_block_reduce``
  + ``pac_modulate``) and ``f64``-accumulated mean, matching
  ``prin_dynamics::pac::PhaseAmplitudeCoupling::modulate``.
- ``prin-kernels::discrete_step`` — ``discrete_step_cpu`` /
  ``discrete_step_cubecl`` — fused three-band (delta/theta/gamma)
  discrete-time step kernel combining phase advance, PAC gating, and
  Stuart–Landau amplitude dynamics in one 10-launch sequence.
  ``BandStepParams`` / ``PacGateParams`` / ``DiscreteStepParams`` /
  ``DiscreteStepOutput`` / ``DiscreteStepError`` / ``StepReport``. The CPU
  reference reuses ``mean_field_rk4::mean_field_derivatives_into`` /
  ``wrap_phase`` / ``clamp_amp`` (promoted to ``pub(crate)``) for per-band
  Kuramoto/Stuart–Landau derivatives (Coding Standards §1). The CubeCL path
  provides four ``#[cube(launch)]`` kernels (``complex_order_reduce``,
  ``real_sum_reduce``, ``band_euler_step``, ``pac_gate``) with host dispatch
  mirroring ``mean_field_rk4::cubecl``'s pattern. PRINet 3.0 implemented
  the discrete-time stepper in ``DeltaThetaGammaNetwork`` (Python); PRIN
  moves it to a single-source CubeCL kernel with ``f64``-accumulated
  reductions matching the CPU reference exactly.

  **WP-020 additions:** reusable hierarchical order-parameter reductions
  (``complex_order_reduce`` called 3× — once per band, ``real_sum_reduce``
  called 2× — once per PAC pair) are ``discrete_step``-local
  implementations structurally identical to ``mean_field_rk4``'s
  ``order_param_block_reduce`` and ``pac``'s ``pac_phase_sum_block_reduce``
  (deliberately separate, not a cross-WP refactor — matching WP-019's
  precedent). ``mean_field_rk4::wrap_phase`` / ``clamp_amp`` /
  ``mean_field_derivatives_into`` promoted from private to ``pub(crate)``
  with doc comments; no behavior change. New criterion benchmark
  (``benches/discrete_step_bench.rs``) at band sizes ``[4096, 16384,
  65536]`` (N=86,016): fused ~3.7–3.8× faster than hand-composed unfused
  baseline.
- ``prin-kernels::backend`` — ``Device`` enum (CUDA, wgpu, CPU),
  ``backend_priority``, and ``auto_detect_order``. Decouples backend
  *preference* from *availability* so unsupported devices fall back safely.
  PRINet 3.0 selected kernels by module path; PRIN exposes a typed
  ``BackendError`` and priority list.
- ``prin-kernels::buffers`` — preallocated buffer pools
  ``MeanFieldRk4Buffers`` (CPU ``Vec<f32>``) and
  ``CubeclBufferPool<R: Runtime>`` (CubeCL device handles). Both eliminate
  per-step allocations and expose ``capacity()``; ``step_cpu_with_pool`` and
  ``step_cubecl_with_pool`` reject reuse at a mismatched oscillator count with
  ``MeanFieldRk4Error::PoolSizeMismatch``.
- ``prin-kernels::equivalence`` — ``EquivalenceHarness``, ``EquivalenceCase``,
  and ``assert_allclose`` for cross-backend testing. The CPU reference is the
  numerical authority; GPU backends are compared at ``rtol=1e-5,
  atol=1e-6``. PRINet 3.0 had no equivalent cross-backend validation harness.
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
- ``prin-tensor`` tensor decompositions (WP-014) — Rust
  ``PolyadicTensor``, ``hosvd()``, ``CPDecomposition``, ``cp_als()``, and
  ``CPResult`` rebuilding PRINet 3.0 ``core/decomposition.py``. All arithmetic
  is ``f64``; SVD is via ``faer``. Replaces the reference's
  ``PolyadicTensor``/``CPDecomposition`` classes. **API differences:** the
  reference ``PolyadicTensor`` takes a single rank clamped to ``min(shape)`` for
  all modes, while PRIN ``hosvd`` takes per-mode ranks clamped to
  ``min(I_n, prod_{k != n} I_k)``; the reference ``CPDecomposition`` uses
  ``torch.randn`` initialization and all-factor normalization (column norms
  clamped at ``1e-12``), while PRIN uses a deterministic ``Seed`` authority
  (uniform ``[0, 1)``) and the same all-factor normalization. CP-ALS
  convergence is monitored via the relative change in reconstruction error
  ``||X - X_hat||_F``. 9 Rust-vs-PRINet 3.0.0 parity tests in
  ``crates/prin-tensor/tests/parity_decomposition.rs`` verify reconstruction,
  orthonormality, shapes, normalization, seed reproducibility, and round-trip at
  ``rtol = 1e-10`` (float64, single-runtime). No Python bindings are exposed
  yet.
- ``prin-sim`` OscilloSim sparse simulation engine (WP-015) — Rust
  ``SparseCoupling``, ``OscilloSim``, ``SparseKuramoto``, ``SparseStuartLandau``,
  ``PruningStrategy``, ``PruningResult``, and ``ChimeraMetrics`` rebuilding PRINet
  3.0 ``utils/oscillosim.py`` and ``core/propagation/sweep_utils.py``. All sparse
  coupling and engine numerics run in ``f64``.

  **Sparse matrix representation:** PRIN uses a strict Compressed Sparse Row
  (CSR) storage format (``SparseCoupling``) with :math:`O(\mathrm{nnz})` SpMV
  evaluation, eliminating dense :math:`N \times N` matrix allocations. Kuramoto
  coupling exploits trigonometric decomposition :math:`\sin(\theta_j - \theta_i)
  = \sin\theta_j \cos\theta_i - \cos\theta_j \sin\theta_i`, computing coupling
  torques in two sparse matrix-vector products.

  **Dynamic pruning:** Dynamic system-size reduction is implemented via
  ``PruningStrategy`` (amplitude thresholding) and ``PruningResult``, which tracks
  explicit bidirectional index mappings (``pruned_to_original``,
  ``original_to_pruned``) and supports lossless and sub-network state restoration
  with configurable ``default_amplitude``.

  **Parity and invariants:** Verified against dense dynamics models
  (``KuramotoOscillator``, ``StuartLandauOscillator``) at :math:`N \in \{8, 64, 256\}`
  for Kuramoto and :math:`N \in \{8, 16\}` for Stuart–Landau at tolerances
  ``rtol = 1e-10`` to ``1e-12`` (21 parity integration tests in
  ``crates/prin-sim/tests/parity_sparse_vs_dense.rs``). Property-tested across
  arbitrary :math:`N \in [3, 64)` and seed combinations via ``proptest`` (4
  property tests in ``crates/prin-sim/tests/proptest_properties.rs``). Memory
  scaling is measured and bounded (:math:`<5\,\mathrm{MB}` for :math:`N = 10{,}000`,
  :math:`\mathrm{nnz} = 200{,}000`).
- ``prin-sim`` parallel parameter sweeps and CPU dispatch (WP-016) — Rust
  ``run_sweep``, ``SweepConfig``, ``SweepResult``, ``SweepAxis``, ``SweepModel``,
  and ``detect_oscillation`` rebuilding PRINet 3.0
  ``core/propagation/sweep_utils.py`` (``sweep_coupling_params`` and
  ``detect_oscillation``).

  **Parallel sweeps:** ``run_sweep`` executes a Cartesian-product grid of parameter
  configurations in parallel via rayon, each an independent ``OscilloSim`` simulation
  with deterministic per-configuration ``Seed`` derivation. Sweep axes: coupling
  strength, decay rate, frequency adaptation rate, and bifurcation parameter.

  **Oscillation detection:** ``detect_oscillation`` flags destabilizing oscillations
  in order-parameter histories via windowed variance, reusing
  ``prin_metrics::order::kuramoto_order_parameter`` (one algorithm, one
  implementation). PRINet 3.0 parity verified across 384 combinations in
  ``tests/parity_detect_oscillation.rs``. One intentional divergence: Python's
  ``r_history[-0:]`` slices the whole list for ``window=0``; Rust returns ``false``.
  No call site uses ``window=0``.

  **CPU dispatch:** Size-gated sequential/parallel dispatch (``dispatch`` module,
  ``PARALLEL_LEN_THRESHOLD = 32{,}768``) replaces the unconditional ``par_bridge()``
  / ``par_iter()`` calls from S1. Sequential reference path below threshold;
  rayon-parallel at or above. Peak sweep speedup: ~3.9× at 8 configs on 8 physical
  cores (plan amendment #21).

  **Arc-based coupling sharing:** ``SparseKuramoto``, ``SparseStuartLandau``, and
  ``OscilloSim`` store ``Arc<SparseCoupling>`` (constructors accept
  ``impl Into<Arc<SparseCoupling>>``), eliminating the per-configuration CSR
  deep-clone.

  Python bindings (``prin-py`` sweep/engine exposure) are deferred to Phase 6 WP-036
  (plan amendment #20).
- ``prin-sim::gpu`` GPU kernel simulation integration (WP-021) — Rust
  ``GpuSparseKuramoto``, ``GpuMeanFieldEngine``, and ``GpuBandStepper``
  integrating ``prin-kernels`` single-source CubeCL dispatch directly into
  simulation workflows:

  **Simulation integration:** ``GpuSparseKuramoto`` implements the ``Dynamics``
  trait, delegating sparse coupling derivative evaluations to
  ``prin_kernels::sparse_knn::cubecl::sparse_knn_coupling_auto`` while reusing
  the CSR topology of ``SparseCoupling``. ``GpuMeanFieldEngine`` executes
  fused dense RK4 steps via ``prin_kernels::mean_field_rk4::cubecl::step_auto``,
  recording trajectories into ``engine::Trajectory``. ``GpuBandStepper`` executes
  fused three-band discrete steps via ``prin_kernels::discrete_step::cubecl::discrete_step_auto``.

  **Precision boundary:** Conversions between ``f64`` (the simulation layer authority)
  and ``f32`` (device kernel precision) are performed explicitly at call boundaries
  (``to_f32``/``to_f64`` helpers), consistent with the kernel-equivalence convention.

  **Dispatch-priority fix:** All four kernel auto-dispatch entry points in ``prin-kernels``
  were aligned to try CUDA before wgpu (CUDA → wgpu → CPU), validated by priority
  regression tests and hardware CUDA kernel-equivalence runs.
- ``prin-train`` trainable bands and resonance primitives (WP-022) — the first
  implementation of the Burn-based (``burn`` 0.16, ``std``/``ndarray``/``autodiff``)
  trainable layer stack: ``bands::DiscreteDeltaThetaGamma`` rebuilding PRINet 3.0
  ``core.propagation.networks.DiscreteDeltaThetaGamma`` and
  ``layers::ResonanceLayer`` rebuilding PRINet 3.0 ``nn.layers.ResonanceLayer``,
  plus the typed ``TrainError`` enum (``EmptyBand``, ``ShapeMismatch``,
  ``NonFiniteParameter``, ``InvalidTimestep``, ``NonFiniteState``).

  **Contracts:** Both are ``#[derive(Module)]`` Burn modules generic over
  ``B: Backend``, exposing a validated ``Config``
  (``DiscreteDeltaThetaGammaConfig`` / ``ResonanceLayerConfig``) with seeded-random
  (``init``, drawing from the project's deterministic ``prin_dynamics::Seed``) and
  explicit-parameter (``init_from_params``) initializers, a ``Params`` struct for
  golden-reference tests and non-``burn::record`` checkpoint paths
  (``DiscreteDeltaThetaGammaParams`` / ``ResonanceLayerParams``, re-exported at the
  crate root), and a validated ``State`` contract (``DiscreteBandState`` /
  ``ResonanceState``). ``step``/``integrate`` return ``Result<State, TrainError>``;
  shape mismatches and (under the ``strict-checks`` feature) non-finite outputs are
  typed errors, not panics.

  **Dynamics:** ``DiscreteDeltaThetaGamma::step`` is a line-for-line Burn port of the
  reference's discrete step: phase advance with learned intra-band coupling,
  delta→theta/theta→gamma PAC gating (multiplicative, sigmoid-gated), and
  Stuart–Landau amplitude update with learned per-band growth rate — a discrete-time
  counterpart to ``prin_dynamics::bands::BandNetwork``'s continuous ODE (WP-013).
  ``ResonanceLayer::step`` ports the core Kuramoto loop of the reference's
  ``forward`` (coupling, decay, frequency modulation, evaluated from pre-step state).

  **Deliberate deviation:** ``ResonanceLayer::init_state`` substitutes a real-valued,
  fully differentiable input→initial-state projection for PRINet 3.0's FFT-based
  initializer (Burn has no complex-tensor autodiff); the step dynamics are unaffected
  and golden-tested. The reference's diagnostic helpers (``get_order_parameter``,
  ``order_parameters``, ``pac_index``) are measurement utilities, not part of the
  forward/gradient contract, and are not ported.

  **Parity and gradients:** Golden-value parity against formulas transcribed from the
  PRINet 3.0 source and evaluated independently in ``torch==2.13.0+cpu`` float64:
  ``tests/parity_bands.rs`` at ``rtol=1e-7, atol=5e-8`` (measured worst case
  ``1.65e-8`` — Burn ``matmul``/``sum_dim`` reduction order vs. torch's, the same
  discrepancy class as ``prin-dynamics``' ``parity_bands.rs``) and
  ``tests/parity_layers.rs`` at ``rtol=1e-10, atol=1e-12``. Gradient correctness is
  verified by autodiff-vs.-central-finite-difference tests (``eps=1e-6``, float64,
  agreement ``<1e-3``) and every-parameter gradient-flow tests. Phase wrap
  ``[0, 2π)`` and amplitude clamp ``[1e-6, 10]`` invariants are unit- and
  property-tested; ``burn::record`` serialization round-trips preserve parameters
  exactly (float64 ``DoublePrecisionSettings``).

- ``prin-train`` inhibition, activations, energy functions, and HEP (WP-023) —
  the second increment of the Burn-based trainable stack:
  ``inhibition::FeedbackInhibition`` rebuilding the trainable half of PRINet 3.0
  ``core.propagation.inhibition.FeedbackInhibition``,
  ``activations`` (``d_silu``, ``ComplexTensor``, ``HolomorphicActivation``,
  ``phase_activation``, ``GatedPhaseActivation``) rebuilding PRINet 3.0
  ``nn.activations``,
  ``energy::HolomorphicEnergy`` rebuilding PRINet 3.0 ``nn.hep.HolomorphicEnergy``,
  and ``hep::HolomorphicEp`` rebuilding PRINet 3.0
  ``nn.hep.HolomorphicEquilibriumPropagation``.

  **Contracts and Primitives:**

  - ``FeedbackInhibition`` provides competitive k-WTA lateral inhibition with a
    straight-through estimator (STE): hard top-:math:`k` selection in the forward
    pass and soft temperature-scaled sigmoid gradients in backward propagation,
    parameterized either by explicit :math:`k` or fractional sparsity
    (:math:`k = \lfloor (1 - s) \cdot N \rfloor`).
  - ``activations`` provides ``d_silu`` (closed-form derivative :math:`\sigma(x) \cdot (1 + x \cdot (1 - \sigma(x)))`),
    ``ComplexTensor`` (real and imaginary tensor pair), ``HolomorphicActivation``
    (split-complex :math:`\tanh` activation), ``phase_activation`` (:math:`2\pi`-modular
    periodic phase wrapping to :math:`[-\pi, \pi)`), and ``GatedPhaseActivation``
    (trainable module with learned gate bias, initialized to zero giving initial gate
    values of :math:`0.5`).
  - ``HolomorphicEnergy`` evaluates the holomorphic scalar energy of complex states:
    coupling energy :math:`E_{\text{coup}} = -\frac{1}{2} \text{Re}(z^\dagger W z)`,
    self-energy :math:`E_{\text{self}} = \sum_i (|z_i| - 1)^2`, and supervised task loss
    weighted by :math:`\beta`.
  - ``HolomorphicEp`` manages Equilibrium Propagation training across free and nudged
    (:math:`+\beta, -\beta`) phases, computing contrastive coupling gradients via the
    symmetric difference formula :math:`\frac{1}{2\beta} (z_{+\beta} z_{+\beta}^\dagger - z_{-\beta} z_{-\beta}^\dagger)`.

  **Deliberate deviations and hazards:**

  - *Split-complex holomorphic activation:* Burn does not support complex autodiff;
    PRIN implements the :math:`\text{holomorphic}=\text{False}` split-complex path
    (:math:`f(u + iv) = \tanh(u) + i \tanh(v)`).
  - *Zero-phase complex state in HEP:* Matching PRINet 3.0, HEP operates on real-valued
    oscillator states embedded into complex form via ``ComplexTensor::from_real(z, zero)``.
  - *Burn sigmoid precision floor (DV-018):* ``burn-tensor`` 0.16.1's default ``sigmoid``
    trait implementation downcasts through ``f32`` internally. Parity and gradcheck
    tolerances for sigmoid-dependent paths use :math:`\text{rtol}=10^{-6}` and
    :math:`\epsilon=10^{-4}`.
  - *Feedforward inhibition and dentate gyrus exclusions:* PRINet 3.0's parameter-free
    ``FeedforwardInhibition`` and ``DentateGyrusConverter`` have no trainable parameters or
    differentiability concerns and are excluded from ``prin-train``.

  **Parity and validation:**
  Golden-value parity tests against PRINet 3.0 (evaluated in ``torch==2.13.0+cpu`` float64):
  ``tests/parity_inhibition.rs`` (:math:`\text{rtol}=10^{-10}, \text{atol}=10^{-12}`),
  ``tests/parity_activations.rs`` (:math:`\text{rtol}=10^{-6}` due to DV-018), and
  ``tests/parity_energy.rs`` (:math:`\text{rtol}=10^{-10}, \text{atol}=10^{-12}`).
  Closed-form HEP coupling gradients cross-checked against central finite differences
  (:math:`<10^{-3}`), Burn autodiff (:math:`<10^{-8}`), and independent manual
  outer-product derivation (:math:`<10^{-9}`).

  **WP-025 Python bridge (``prin.nn``):** the production ``torch.autograd.Function``
  bridge is now delivered. ``prin.nn.ResonanceLayer`` and
  ``prin.nn.GatedPhaseActivation`` are ``torch.nn.Module`` wrappers whose
  ``forward``/``backward`` call into the Rust core via DLPack zero-copy
  tensor exchange (``crates/prin-py/src/bindings/train.rs``). Trainable
  parameters remain owned by the Rust bridge (not ``torch.nn.Parameter``);
  train them with ``prin-train`` oscillator-aware optimizers
  (``SyncGd``/``Rip``/``Scalr``). Checkpointing uses
  ``rust_state_dict``/``load_rust_state_dict`` (Rust-native ``burn::record``
  bytes), with shape validation at load time (WP025-F1 fix). Every bridge
  requires ``float64`` CPU, contiguous input. 31 Python tests pass
  ``torch.autograd.gradcheck`` in float64. GPU-backed Burn backends
  (``wgpu``/``cuda``) remain unbridged (DV-005; no Burn CUDA backend in
  workspace).

- ``prin-train`` PhaseTracker, Hybrid, baselines, and allocation (WP-026) —
  the fifth increment of the Burn-based trainable stack, rebuilding PRINet 3.0
  ``nn/{layers,hybrid,slot_attention,ablation_variants,adaptive_allocation}.py``:

  - ``attention::OscillatoryAttention`` rebuilding PRINet 3.0
    ``nn.layers.OscillatoryAttention``: multi-head attention with additive
    oscillatory coherence bias
    (:math:`\text{score} = QK^T/\sqrt{d_k} + \alpha \cdot \cos(\varphi_i - \varphi_j)`).
    Masked-attention support not ported (no exercising caller in this WP).
  - ``phase_tracker::PhaseTracker`` rebuilding PRINet 3.0
    ``nn.hybrid.PhaseTracker``: PRIN's primary contribution — phase-based
    multi-object tracker. Encodes detections to phase/amplitude via MLP,
    evolves through ``DiscreteDeltaThetaGamma``, matches frames by
    phase-coherence similarity (real-valued reformulation of PRINet 3.0's
    ``torch.complex64`` cosine similarity — Burn has no complex-tensor
    autodiff) with greedy descending-similarity assignment.
  - ``hybrid::HybridPRINetV2`` rebuilding PRINet 3.0
    ``nn.hybrid.HybridPRINetV2``: canonical hybrid oscillator + attention
    classifier: input → token projection → adaptive oscillator phase
    (``DiscreteDeltaThetaGamma``) interleaved with ``OscillatoryAttention``
    + FFN blocks → pool → classify. CNN stem (``use_conv_stem``) not ported
    (out of scope, no exercising caller).
  - ``slot_attention::{SlotAttentionModule, TemporalSlotAttentionMOT}``
    rebuilding PRINet 3.0 ``nn.slot_attention``: non-oscillatory Slot
    Attention (Locatello et al. 2020) comparison baseline. Both draw fresh
    per-call stochastic noise from ``&mut Seed`` (a genuine per-call
    stochastic entry point). ``SlotAttentionCLEVRN`` not ported (out of
    scope).
  - ``ablation::{PhaseTrackerFrozen, PhaseTrackerStatic,
    SlotAttentionNoGRU, SlotAttentionFrozen}`` rebuilding PRINet 3.0
    ``nn.ablation_variants``. The reference's string-keyed
    ``create_ablation_tracker`` factory not ported (variants' ``forward``
    signatures genuinely differ in Rust's static type system).
  - ``allocation::{AdaptiveOscillatorAllocator, DynamicPhaseTracker}``
    rebuilding PRINet 3.0 ``nn.adaptive_allocation``: rule-based and learned
    (MLP) strategies, ``estimate_complexity``, lazily-caching per-budget
    ``PhaseTracker`` factory.

  **Symbol mapping:**

  - ``prinet.nn.layers.OscillatoryAttention`` → ``prin_train::attention::OscillatoryAttention``
  - ``prinet.nn.hybrid.PhaseTracker`` → ``prin_train::phase_tracker::PhaseTracker``
  - ``prinet.nn.hybrid.HybridPRINetV2`` → ``prin_train::hybrid::HybridPRINetV2``
  - ``prinet.nn.slot_attention.SlotAttentionModule`` → ``prin_train::slot_attention::SlotAttentionModule``
  - ``prinet.nn.slot_attention.TemporalSlotAttentionMOT`` → ``prin_train::slot_attention::TemporalSlotAttentionMOT``
  - ``prinet.nn.ablation_variants.*`` → ``prin_train::ablation::{PhaseTrackerFrozen, PhaseTrackerStatic, SlotAttentionNoGRU, SlotAttentionFrozen}``
  - ``prinet.nn.adaptive_allocation.AdaptiveOscillatorAllocator`` → ``prin_train::allocation::AdaptiveOscillatorAllocator``
  - ``prinet.nn.adaptive_allocation.DynamicPhaseTracker`` → ``prin_train::allocation::DynamicPhaseTracker``

  **Deliberate deviations:**

  - *PhaseTracker phase-coherence similarity:* PRINet 3.0 uses
    ``torch.complex64`` cosine similarity; PRIN uses a real-valued
    reformulation (``cos(φ_i − φ_j)`` weighted by amplitudes) because Burn
    has no complex-tensor autodiff. Same numerical result at ``float64``.
  - *HybridPRINetV2 CNN stem:* ``use_conv_stem`` path not ported — out of
    this WP's oscillatory-binding scope, no exercising caller.
  - *Allocation strategy mismatch:* ``AdaptiveOscillatorAllocator::validate_shapes``
    detects ``Rule``↔``Learned`` strategy mismatches at checkpoint load
    (``TrainError::StrategyMismatch``); the inverse direction (``Rule``
    target with ``Learned`` checkpoint) silently discards the MLP load
    without error, documented as an accepted limitation (``Rule`` path
    never reads MLP weights, no data corruption).

  **Parity and validation:**
  Golden-value parity tests against the actual PRINet 3.0 reference classes
  (``torch==2.13.0+cpu`` float64): ``tests/parity_attention.rs``
  (:math:`\text{rtol}=10^{-6}, \text{atol}=10^{-6}`),
  ``tests/parity_phase_tracker.rs``
  (:math:`\text{rtol}=10^{-6}, \text{atol}=10^{-6}`),
  ``tests/parity_hybrid.rs``
  (:math:`\text{rtol}=10^{-6}, \text{atol}=10^{-6}`).
  ``HybridPRINetV2`` composes already-parity-tested primitives
  (``DiscreteDeltaThetaGamma`` + ``OscillatoryAttention`` + standard Burn
  layers); the whole-module parity test transcribes the full weight set via
  ``HybridPRINetV2Params``/``init_from_params``. S3 remediation found and
  fixed a missing ReLU in the classifier head during this test's creation.

  **WP-026 Python bridge (``prin.nn``):** PyO3/DLPack bridges for all six
  new modules. ``prin.nn.{OscillatoryAttention, PhaseTracker,
  HybridPRINetV2, SlotAttentionModule, TemporalSlotAttentionMOT}`` are
  ``torch.nn.Module`` wrappers; ``{PhaseTrackerFrozen, PhaseTrackerStatic,
  SlotAttentionNoGRU, SlotAttentionFrozen}`` are ablation wrappers;
  ``{AdaptiveOscillatorAllocator, DynamicPhaseTracker}`` are entirely
  non-differentiable (discrete outputs). Differentiable methods use the
  generic ``apply_rust_bridge`` in ``_bridge.py``; non-differentiable
  methods are plain PyO3 calls. 86 new Python tests; 100% coverage on all
  ``python/prin/nn/`` files (372/372 statements). Every differentiable
  entry point passes ``torch.autograd.gradcheck`` in float64.

- ``prin-train`` oscillator-aware optimizers (WP-024) —
  the third increment of the Burn-based trainable stack, rebuilding PRINet 3.0
  ``nn/optimizers.py``:
  ``feedback::OrderParameter`` (global-or-per-group order parameter with Q3 dict
  resolution), ``feedback::StepFeedback`` (per-step input),
  ``feedback::OscillatorOptimizer`` (uniform step/state_dict/load_state_dict trait),
  ``sync_gd::SyncGd`` rebuilding PRINet 3.0 ``SynchronizedGradientDescent``,
  ``rip::Rip`` rebuilding PRINet 3.0 ``RIPOptimizer``,
  and ``scalr::Scalr`` rebuilding PRINet 3.0 ``SCALROptimizer``.

  **Symbol mapping:**

  - ``prinet.nn.optimizers.SynchronizedGradientDescent`` → ``prin_train::sync_gd::SyncGd``
  - ``prinet.nn.optimizers.RIPOptimizer`` → ``prin_train::rip::Rip``
  - ``prinet.nn.optimizers.SCALROptimizer`` → ``prin_train::scalr::Scalr``

  **Deliberate deviations:**

  - *Rip fixed square shape:* PRINet 3.0's ``RIPOptimizer`` silently skips the
    Hebbian term for non-square-matching parameters; ``Rip`` fixes ``n_oscillators``
    at construction and returns ``TrainError::ShapeMismatch`` on mismatch, per
    Coding Standards §2.2 (validate public inputs at every public boundary).

  **Parity and validation:**
  Golden-value parity tests against the actual PRINet 3.0 optimizer classes
  (``torch==2.13.0+cpu`` float64): ``tests/parity_optimizers.rs`` at
  :math:`\text{rtol}=10^{-9}, \text{atol}=10^{-12}` (5 cases: SyncGD 2-step,
  RIP combined gradient+Hebbian, SCALR basic 3-step, SCALR oscillation+adaptive
  r_min 5-step, Q3 dict resolution). Deterministic resume verified (step N
  uninterrupted vs. step k → snapshot → restore → step N−k,
  :math:`<10^{-12}` final parameters). ``load_state_dict`` re-validates
  every hyperparameter through the original constructor.

- ``prin-train`` trainable-stack integration and Phase 4 gate (WP-027) —
  the final increment of the Phase 4 trainable stack: temporal CLEVR-N dataset
  generator, training losses, Rust-native training loop, optimizer bridges,
  and Phase 4 acceptance-criterion validation.

  **New modules:**

  - ``prin_train::dataset`` — ``SequenceData``, ``TemporalClevrNConfig``,
    ``generate_temporal_clevr_n``, ``generate_dataset``: structural port of
    PRINet 3.0 ``utils/temporal_training.py:68-253`` (constant-velocity motion
    with elastic boundary bounce, occlusion zeroing, appearance-feature swap,
    velocity reversal, additive noise). Uses the project's counter-based
    ``Seed`` instead of PRINet 3.0's per-perturbation ``torch.Generator``
    streams.
  - ``prin_train::losses`` — ``hungarian_similarity_loss``,
    ``temporal_smoothness_loss``: direct ports of PRINet 3.0
    ``utils/temporal_training.py:261-336``.
  - ``prin_train::trainer`` — ``TemporalTrainerConfig``, ``TrainingResult``,
    ``ValMetrics``, ``train_phase_tracker``, ``evaluate_phase_tracker``:
    Rust-native training loop (Burn Adam + warmup/cosine LR + gradient
    clipping + early stopping), porting PRINet 3.0 ``TemporalTrainer``
    (``temporal_training.py:454-869``).

  **Symbol mapping:**

  - ``prinet.utils.temporal_training.generate_temporal_clevr_n`` → ``prin_train::dataset::generate_temporal_clevr_n``
  - ``prinet.utils.temporal_training.generate_dataset`` → ``prin_train::dataset::generate_dataset``
  - ``prinet.utils.temporal_training.hungarian_similarity_loss`` → ``prin_train::losses::hungarian_similarity_loss``
  - ``prinet.utils.temporal_training.temporal_smoothness_loss`` → ``prin_train::losses::temporal_smoothness_loss``
  - ``prinet.utils.temporal_training.TemporalTrainer`` → ``prin_train::trainer::train_phase_tracker`` (function, not class)

  **Deliberate deviations:**

  - *Gradient clipping:* Burn's per-tensor ``GradientClippingConfig::Norm``
    vs. PyTorch's global ``clip_grad_norm_``. Both bound gradient magnitude;
    distinction does not affect the IP-threshold acceptance criterion.
  - *LR schedule:* directly-computed scalar cosine formula vs. PyTorch's
    ``CosineAnnealingLR`` step-count state. Same schedule shape, up-to-one-
    epoch cosmetic phase difference.

  **WP-027 Python bridge (``prin.nn``/``prin.train``):**
  ``prin.nn.{SyncGd, Scalr, Rip}`` are ``torch.optim.Optimizer`` subclasses
  wrapping the Rust optimizer-step bridges. ``prin.train.train_phase_tracker``
  is a thin Python entry point for the Rust-native trainer, returning a
  ``TrainingResult`` dataclass. 17 new Python tests (13 optimizer, 4 pipeline).

  **Phase 4 gate acceptance:**
  PhaseTracker mean IP = 1.00000 ≥ registered 0.99868 threshold across seeds
  (42, 123, 456) on the canonical temporal CLEVR-N protocol. Composed
  "full gradcheck" (``encode → evolve → phase_similarity``) green. Trained-
  state serialization round-trip validated. DV-021 bridge overhead
  independently re-corroborated (+37.8%/+6.5%).

- ``prin-daemon`` ONNX controller and backend selection (WP-028) —
  subconscious controller state/control types, hand-written ONNX model
  validation, execution-provider detection (VitisAI→DirectML→CPU), and
  deterministic CPU-terminated fallback. Rebuilds PRINet 3.0
  ``core/subconscious.py`` and ``utils/npu_backend.py``.

  **New modules:**

  - ``prin_daemon::state`` — ``SubconsciousState``, ``ControlSignals``,
    ``Regime``, ``STATE_DIM = 32``, ``CONTROL_DIM = 8``: PRINet 3.0's exact
    float32 packing, normalisation, and clamping semantics (bit-exact parity).
  - ``prin_daemon::backend`` — ``Backend``, ``BackendSelection``,
    ``SelectionReason``, ``select_backend``, ``provider_options``,
    ``VitisAiConfig``, ``firmware_candidates``, ``resolve_firmware``:
    VitisAI→DirectML→CPU priority policy and deterministic fallback ladder.
  - ``prin_daemon::onnx`` — ``OnnxModelInfo``, ``TensorSpec``, ``Dim``,
    ``OpsetId``, ``InitializerSpec``, ``inspect_onnx_bytes``,
    ``inspect_onnx_file``: bounded, total ONNX ``ModelProto`` reader
    (hand-written, no ``protoc`` dependency).
  - ``prin_daemon::model`` — ``ModelManifest``, ``sha256_file``,
    ``verify_sha256``, ``ControllerModel::validate``,
    ``validate_controller_contract``: SHA-256 integrity verification against
    ``models/manifest.json``.
  - ``prin.daemon`` — ``SubconsciousController``, ``create_session``,
    ``select_backend``, ``detect_best_backend``, ``backend_info``,
    ``verify_model_artefacts``, ``OrtUnavailableError``: Python orchestration
    layer (no numerics; ONNX Runtime session creation stays in Python per
    risk register #4).

  **Symbol mapping:**

  - ``prinet.core.subconscious.SubconsciousState`` → ``prin_daemon::state::SubconsciousState``
  - ``prinet.core.subconscious.ControlSignals`` → ``prin_daemon::state::ControlSignals``
  - ``prinet.utils.npu_backend.detect_best_backend`` → ``prin.daemon.detect_best_backend``
  - ``prinet.utils.npu_backend.create_session`` → ``prin.daemon.create_session``
  - ``prinet.nn.subconscious_model.SubconsciousController`` (inference half) → ``prin.daemon.SubconsciousController``

  **Deliberate deviations:**

  - *Fallback ladder:* PRINet 3.0's ``create_session`` has no fallback — an
    unexecutable provider propagates the ORT error, and an unregistered
    provider silently yields a CPU session still labelled ``npu``. PRIN
    computes the ladder in Rust from the provider list alone (pure,
    reproducible, strictly descending, CPU-terminating) and reports the
    backend actually landed on plus a ``SelectionReason``.
  - *``clone_state`` vs. ``clone``:* PRINet 3.0's ``SubconsciousState`` uses
    the name ``clone`` for its copy method; PRIN uses ``clone_state`` to avoid
    shadowing Rust's ``Clone`` trait convention.
  - *``create_session`` return shape:* returns a
    ``(session, backend_selection)`` tuple rather than a bare session, so
    callers can inspect which backend was actually selected and why.
  - *NumPy NEP 50 clipping:* ``np.clip(flat[2], 0.1, 10.0)`` on a
    ``float32`` operand keeps ``float32`` in the reference; the Rust port
    clips in ``f32`` to match, not ``f64``.
  - *Python modulo:* ``timestamp % 86400.0`` takes the sign of the divisor in
    Python; the Rust port uses ``f64::rem_euclid`` to match.

- ``prin-daemon`` daemon runtime and lock-free control buffer (WP-029) —
  native background thread, lock-free control-signal ring buffer, pluggable
  inference seam, dead-letter queue, escalation callbacks, and bounded
  shutdown. Rebuilds PRINet 3.0
  ``core/subconscious_daemon.py`` (daemon lifecycle) and the
  ``ControlSignalBuffer`` class in ``core/subconscious.py`` (thread-safe
  ring buffer).

  **New module:**

  - ``prin_daemon::daemon`` — ``SubconsciousDaemon`` (native background
    thread with bounded ``stop()`` returning ``bool``),
    ``ControlSignalBuffer`` (lock-free, ``ArcSwap``-backed replacement for
    PRINet 3.0's ``threading.Lock``-guarded buffer), ``InferenceBackend``
    (pluggable inference seam with blanket closure impl), ``DaemonConfig``,
    ``DaemonStats``, ``DeadLetterEntry``, ``EscalationEvent``,
    ``EscalationCallback``: the full daemon lifecycle with dead-letter
    queue, escalation callbacks, non-finite control-signal fallback, and
    warm-up failure tolerance.

  **Symbol mapping:**

  - ``prinet.core.subconscious_daemon.SubconsciousDaemon`` → ``prin_daemon::daemon::SubconsciousDaemon``
  - ``prinet.core.subconscious.ControlSignalBuffer`` → ``prin_daemon::daemon::ControlSignalBuffer``

  **Deliberate deviations:**

  - *Lock-free buffer:* PRINet 3.0's ``ControlSignalBuffer`` uses
    ``threading.Lock``; PRIN's uses ``ArcSwap`` (atomic pointer swap, no
    lock). Lock-free p95 latency is 13–20× lower than a same-language
    ``Mutex`` re-implementation of the 3.0 design (see
    ``EVIDENCE/0113-wp029-s1-control-buffer-pilot.json``).
  - *Bounded shutdown with result:* PRINet 3.0's ``stop()`` takes a timeout
    and logs a warning on timeout but never tells the caller whether it
    succeeded. PRIN's ``SubconsciousDaemon::stop`` returns ``bool`` —
    ``true`` if the backend thread exited within the timeout, ``false``
    otherwise.
  - *PyO3 binding not yet delivered:* ``InferenceBackend`` is the pluggable
    seam a Python-backed ``SubconsciousController`` session wires through,
    but the PyO3 binding (whose background thread calls back into Python
    under the GIL) is not delivered this WP. The follow-up session must
    implement ``Drop`` for the PyO3 wrapper type as
    ``Python::with_gil(|py| py.allow_threads(|| { /* stop */ }))`` to avoid
    GIL deadlock. See ``DOCS/experiments/0113-wp029-s1-handoff.md`` for the
    full scope decision and GIL-release design.

  **Deferred to later WPs:**

  - ``SubconsciousController.export_to_onnx`` / ``.quantize_onnx`` →
    **WP-036** (re-targeted at WP-030 S4 from an original WP-030 estimate;
    WP-030's actual maintainer-approved scope — training hooks and MOT
    evaluation — never named these symbols, and neither does the Project
    Plan §6 Phase 5 roadmap row; see
    `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-025).
  - ``retrain_controller`` → **WP-036** (same re-targeting; see DV-025).

- ``prin-daemon`` training hooks and MOT evaluation (WP-030) — loss
  EMA/variance, gradient-norm EMA, and step-latency percentile hooks feeding
  ``SubconsciousState``; CLEAR-MOT/IDF1 evaluation core validated against
  real ``py-motmetrics``; deterministic synthetic MOT sequence generators.
  Rebuilds PRINet 3.0 ``prinet.nn.training_hooks`` (``StateCollector``) and
  the metrics core of ``prinet.nn.mot_evaluation``.

  **New modules:**

  - ``prin_daemon::hooks`` — ``TrainingHooks``: loss EMA/variance
    (``StateCollector.loss_ema``/``loss_var`` recurrences, ported exactly),
    gradient-norm EMA from caller-supplied per-parameter L2 norms, and
    step-latency window/p50/p95/throughput. ``on_step_start``/
    ``on_step_end``/``on_step_end_with_elapsed``/``on_epoch_end`` build a
    ``SubconsciousState`` for ``SubconsciousDaemon::submit_state``.
  - ``prin_daemon::mot`` — ``MotAccumulator``/``MotSummary`` (MOTA, MOTP,
    IDF1, identity switches, misses, false positives), ``BBox``/
    ``iou_distance_matrix``, ``Detection``, ``generate_linear_sequence``/
    ``generate_crowded_sequence`` (``prin_dynamics::Seed``-driven,
    deterministic).
  - ``assignment`` (crate-private) — rectangular Hungarian/Kuhn–Munkres
    assignment solver with ``motmetrics``-style NaN/Inf "do-not-pair"
    handling, used by ``MotAccumulator`` for per-frame and global (IDF1)
    identity matching.

  **Symbol mapping:**

  - ``prinet.nn.training_hooks.StateCollector`` → ``prin_daemon::hooks::TrainingHooks``
  - ``prinet.nn.mot_evaluation.MOTAccumulator`` (metrics core) → ``prin_daemon::mot::MotAccumulator``

  **Deliberate deviations:**

  - *``on_epoch_end`` returns instead of submitting:* PRINet 3.0's
    ``StateCollector`` owns the daemon and calls ``submit_state`` itself;
    ``TrainingHooks::on_epoch_end`` returns the built ``SubconsciousState``
    and leaves submission to the caller, keeping unit tests free of thread
    spawning. Daemon integration is proven end-to-end by
    ``tests/hooks_daemon_integration.rs``.
  - *No hidden ``r_per_band`` default:* PRINet 3.0 defaults to
    ``[0.5, 0.5, 0.5]`` when band ratios are unavailable; PRIN requires an
    explicit ``Vec<f64>`` (empty when unavailable), which
    ``SubconsciousState::band()`` zero-fills — no silent defaulting.
  - *``evaluate_tracking``'s tracker-wiring loop is not reproduced:*
    ``crates/README.md``'s layering places `prin-train` (where
    ``PhaseTracker`` lives) at the same tier as ``prin-daemon``, so wiring a
    real tracker's per-frame hypotheses into ``MotAccumulator`` is a Python
    orchestration concern (``python/prin/eval``), not yet delivered — see
    `DOCS/experiments/0117-wp030-s1-handoff.md` out-of-scope discovery #1.
  - *``TRANSFER``/``ASCEND``/``MIGRATE`` event subtypes and the full
    per-event ``RAW`` log are not reproduced:* the four target metrics
    (MOTA, MOTP, IDF1, identity switches) only ever consume
    ``MATCH``/``SWITCH``/``MISS``/``FP`` counts, a running distance sum, and
    (for IDF1) three frame-presence counters — ``MotAccumulator`` keeps only
    those running counters, independently verified against real
    ``motmetrics`` output rather than the reference's internal dataframe
    representation.

- ``prin-train`` temporal experiments, statistics, and adversarial tooling
  (WP-031) — fair PT-vs-SA training framework, temporal tracking-quality
  metrics, statistical utilities, FLOPs estimation, and FGSM/PGD adversarial
  robustness evaluation. All in Rust (``prin-train``); no Python numerics.

  **New modules:**

  - ``prin_train::temporal_metrics`` — ``identity_switches``,
    ``track_fragmentation``, ``mostly_tracked_mostly_lost``,
    ``track_duration_stats``, ``recovery_speed``, ``binding_robustness``,
    ``temporal_smoothness``, ``TemporalMetrics`` aggregate. Direct port of
    PRINet 3.0 ``utils/temporal_metrics.py``.
  - ``prin_train::stats`` — ``bootstrap_ci`` (percentile-method bootstrap
    confidence intervals), ``welch_t_test``/``compute_p_value`` (Welch's
    t-test with hand-rolled Student's-t p-value via log-gamma),
    ``cohens_d`` (effect size). Validated against real
    ``scipy.stats.ttest_ind`` 1.18.0 (8/8 scenarios at ``rtol=1e-9,
    atol=1e-12``).
  - ``prin_train::flops`` — ``LayerSpec``/``count_flops``/``FlopsReport``
    (per-layer FLOPs for Linear, Conv2d, GRU, LayerNorm, BatchNorm2d,
    Embedding, MultiHeadAttention), ``measure_wall_time``/``WallTimeStats``.
  - ``prin_train::adversarial`` — ``fgsm_attack``/``pgd_attack``
    (L-infinity-bounded adversarial perturbation), per-tracker
    ``adversarial_evaluate_pt``/``adversarial_evaluate_sa`` orchestration,
    ``adversarial_comparison`` (head-to-head PT-vs-SA robustness).

  **Trainer extensions:**

  - ``train_temporal_slot_attention_mot``/
    ``evaluate_temporal_slot_attention_mot`` — SA-side counterpart to the
    existing PT trainer, sharing identical ``TemporalTrainerConfig`` for a
    fair matched-budget comparison.
  - ``count_parameters`` — generic over any ``Module`` via
    ``ModuleVisitor``; verified equal between PT and SA shapes.
  - ``TrainingSnapshot`` — per-epoch training state snapshot.
  - ``train_multi_seed`` — multi-seed statistical reliability aggregation
    (mean/std of loss/metrics across seeds).
  - ``train_phase_tracker`` now threads ``&mut Seed`` explicitly (Project
    Plan §4 rule 3).

  **Symbol mapping:**

  - ``prinet.utils.temporal_metrics.*`` → ``prin_train::temporal_metrics::*``
  - ``prinet.utils.statistics.*`` (bootstrap, Welch, Cohen's d) → ``prin_train::stats::*``
  - ``prinet.utils.flops.*`` → ``prin_train::flops::*``
  - ``prinet.utils.adversarial.*`` (FGSM, PGD) → ``prin_train::adversarial::*``
  - ``prinet.nn.temporal_training.TemporalTrainer`` → ``prin_train::trainer::{train_phase_tracker, train_temporal_slot_attention_mot}``

  **Deliberate deviations:**

  - *Python bindings deferred:* ``prin-py`` PyO3 bindings for the four new
    modules and ``python/prin/eval``/``experiments`` population are deferred
    to a future WP (consistent with WP-030's identical deferral for
    ``hooks.rs``/``mot.rs``). The Rust implementations are complete and
    tested; only the Python orchestration layer is outstanding.
  - *Conv2d FLOPs reference discrepancy:* the reference's Conv2d docstring
    and implementation disagree; PRIN reproduces the reference's *executed*
    behavior (documented in ``flops.rs`` rustdoc).
  - *``TrainingSnapshot::slot_entropy`` and ``MultiSeedResult`` dead-field
    omissions:* the reference defines fields that are never populated by any
    caller; PRIN omits them (documented in rustdoc, model example of
    "document deviations rather than silently absorb").

- ``prin-py`` / ``python/prin`` daemon, evaluation, and experiment
  integration (WP-032) — cross-crate PyO3 bindings and Python facades that
  wire the WP-028..WP-031 daemon and experiment-tooling modules into a
  cohesive evaluation pipeline. All numerics remain in Rust; the Python
  layer only selects and composes.

  **New PyO3 bindings (``crates/prin-py/src/bindings/``):**

  - ``daemon.rs`` — native ``SubconsciousDaemon`` and ``TrainingHooks``
    PyO3 classes; GIL-safe stop/drop (background thread detaches Python
    while waiting for the daemon to join); callback shape/dtype/contiguity
    validation.
  - ``phase5.rs`` — ``MotAccumulator``, ``compute_full_temporal_metrics``,
    ``py_bootstrap_ci``, ``py_welch_t_test``, ``py_cohens_d``,
    ``adversarial_evaluate_phase_tracker``,
    ``adversarial_evaluate_slot_attention``.

  **New Python modules:**

  - ``prin.daemon`` — ``SubconsciousController.spawn_daemon()`` and public
    daemon/hooks exports.
  - ``prin.eval`` — cohesive MOT and temporal evaluation facade
    (``MotAccumulator``, ``compute_full_temporal_metrics``, etc.).
  - ``prin.experiments`` — statistical (``bootstrap_ci``, ``welch_t_test``,
    ``cohens_d``) and public-model adversarial
    (``adversarial_evaluate_*``) facade.
  - ``prin._prin_core`` type stubs — 8 new Phase 5 types:
    ``SubconsciousDaemon``, ``TrainingHooks``, ``MotSummary``,
    ``MotAccumulator``, ``TemporalMetrics``, ``BootstrapCi``,
    ``WelchTTest``, ``AdversarialEvalResult``.

  **Symbol mapping:**

  - ``prinet.nn.subconscious_model.SubconsciousController`` daemon spawn →
    ``prin.daemon.SubconsciousController.spawn_daemon()``
  - ``prinet.nn.mot_evaluation.evaluate_tracking`` →
    ``prin.eval.MotAccumulator`` (metrics core only; tracker-wiring is a
    Python orchestration concern)
  - ``prinet.utils.temporal_metrics.*`` → ``prin.eval.compute_full_temporal_metrics``
  - ``prinet.utils.statistics.*`` → ``prin.experiments.{bootstrap_ci, welch_t_test, cohens_d}``
  - ``prinet.utils.adversarial.*`` → ``prin.experiments.adversarial_evaluate_*``

- ``benchmarks/`` unified benchmark runner and category migration (WP-033)
  — the legacy PRINet 3.0 quarterly benchmark scripts (y2q/y3q/y4q naming,
  58 verified present) are reorganised into nine topic category packages
  executed through a single ``benchrunner`` CLI. No numerical computation
  lives in the suite; every measured quantity comes from Rust.

  **Category packages:**

  - ``benchmarks.scaling`` — oscillator-count scaling, sweep throughput
    (``oscillator_count``, ``coupling_complexity``).
  - ``benchmarks.chimera`` — chimera phase diagrams and metrics
    (``phase_diagram``).
  - ``benchmarks.mot`` — multi-object tracking: PhaseTracker vs
    SlotAttention (``tracker_comparison``).
  - ``benchmarks.ablations`` — ablation variants: frozen/static/no-GRU,
    adaptive allocation (``variant_comparison``).
  - ``benchmarks.kernels`` — fused-kernel performance via ``cargo bench``
    criterion subprocess bridge (``criterion_suite``).
  - ``benchmarks.integrators`` — integrator accuracy/cost: RK45,
    exponential, multi-rate (``accuracy_cost``).
  - ``benchmarks.training`` — training throughput (``throughput``).
  - ``benchmarks.daemon`` — subconscious controller latency p50/p95
    (``control_latency``).
  - ``benchmarks.adversarial`` — FGSM/PGD robustness evaluation
    (``robustness``).

  **Shared infrastructure (``benchmarks._common``):**

  - ``BenchmarkConfig`` — iterations, warmup, seed counter/key.
  - ``capture_environment`` — Rust/Python/hardware snapshot.
  - ``timed_run`` — ≥10-iteration timing rule, warmup exclusion, median/p95.
  - ``BenchmarkRegistry`` — category/name dispatch.
  - ``write_result`` — JSON writer with output-path confinement.

  **CLI usage:**

  .. code-block:: bash

     python -m benchmarks.benchrunner --list
     python -m benchmarks.benchrunner --category scaling --out benchmarks/results/
     python -m benchmarks.benchrunner --category scaling --name oscillator_count --iterations 20

  **Legacy mapping:** see
  ``DOCS/baselines/wp033_benchmark_traceability.md``
  for the complete 58-row traceability table.

- ``prin.reporting`` publication reporting, figures, tables, and profiling
  (WP-034) — near-verbatim ports of the PRINet 3.0 ``utils/`` reporting tools.
  All numerics stay in stored JSON or the Rust core; this package only renders
  and profiles. Reports carry no implicit wall-clock timestamp, so unchanged
  inputs produce byte-stable output; figures normalize to deterministic
  PDF/PNG bytes; the 11 LaTeX fragments regenerate bytes-identical to the
  stored ``paper/tables/`` files.

  **Module mapping:**

  - ``prinet.utils.benchmark_reporting.{generate_benchmark_report,
    generate_leaderboard,generate_scalr_metrics_report}`` →
    ``prin.reporting.benchmark_reporting.*`` (same names). The 3.0 implicit
    ``datetime.now()`` timestamp is replaced by a caller-supplied
    ``generated_at`` normalized to UTC minute precision.
  - ``prinet.utils.figure_generation`` → ``prin.reporting.figure_generation``
    — 14 generators ``fig_ablation_results`` … ``fig_training_curves``
    (historical ``fig2``–``fig15``), plus ``configure_neurips_style``,
    ``generate_all_figures``, and the new ``normalize_matplotlib_output``
    helper for deterministic byte comparison.
  - ``prinet.utils.table_generation`` → ``prin.reporting.table_generation``
    — 11 generators ``table_ablation_variants`` … ``table_supercritical_regime``
    and ``generate_all_tables``.
  - ``prinet.utils.profiler`` → ``prin.reporting.profiler`` —
    ``PRINetProfiler``, ``ProfileReport`` (legacy shape/trace name preserved),
    ``profile_training_loop``, and ``PRINetProfiler.record_function(label)``
    as the explicit boundary that surfaces Rust-backed operations in
    ``torch.profiler`` key averages and Chrome traces.

  **Behavioural notes:**

  - **Figure count is 14, not 15.** The reference implementation numbers its
    figures ``fig2``–``fig15``; there is no ``fig1``. Session briefs quoting
    "15 figures" are factually corrected in
    ``DOCS/reports/034-project-state.md`` (finding WP034-F1).
  - **Typed errors.** All public functions raise from the ``ReportingError``
    hierarchy (``prin.reporting.ReportingError`` root; each subtype keeps its
    original stdlib base such as ``ValueError``/``RuntimeError``/
    ``FileNotFoundError`` for backward-compatible ``isinstance`` catches).
  - **Output-path confinement.** Writers reject any target outside
    ``benchmarks/results/``, ``DOCS/test_and_benchmark_results/``, or the OS
    temp tree. Historical ``paper/`` paths are read-only parity references.
  - The end-to-end reproduction CLI (``tools/reproduce.py``) and the checked
    SHA-256 output manifest are WP-035, not part of ``prin.reporting``.

- ``tools/reproduce.py`` reproduction pipeline and
  ``paper/artefact_manifest.json`` SHA-256 manifest (WP-035) — deterministic
  end-to-end regeneration of all 14 figures and 11 LaTeX tables from the
  immutable stored JSON artefacts, without GPU execution, training, or
  random sampling.

  **CLI usage:**

  .. code-block:: bash

     python tools/reproduce.py --verify-manifest     # full pipeline + manifest check
     python tools/reproduce.py --figures-only        # skip tables
     python tools/reproduce.py --tables-only         # skip figures
     python tools/reproduce.py --append-manifest     # add new artefacts after verifying existing

  **Key properties:**

  - **Append-only manifest.** ``paper/artefact_manifest.json`` (schema
    version 1, 172 records) covers every stored JSON artefact with plain
    filename, exact byte size, and lowercase SHA-256 digest. Existing
    records are verified before new ones are added; mutation or removal of
    an accepted artefact is a hard failure (``ManifestMismatchError``).
  - **Tamper detection.** Missing, corrupted (same-size content change), or
    unmanifested artefacts all fail closed before any rendering occurs.
  - **Output confinement.** The manifest destination is restricted to
    ``paper/``, ``benchmarks/results/``, or the OS temp directory. Manifest
    record paths are validated as plain filenames (no path separators or
    parent references).
  - **No archived code imported.** The pipeline reads JSON data from the
    archived ``benchmarks/results/`` directory but imports only current
    ``prin.reporting`` generators — exactly as ``tools/`` policy requires.
  - **Typed errors.** ``ReproductionError`` (base), ``ReproductionConfigurationError``,
    ``ManifestFormatError``, and ``ManifestMismatchError`` provide specific
    failure modes for CLI and API consumers.

WP-036 compatibility surface (sub-pass 0141A)
---------------------------------------------

The first WP-036 coding sub-pass establishes PRIN's top-level API freeze and
maps the following PRINet 3.0 symbols. ``prin.__all__`` and
``prin._deprecation.FROZEN_PUBLIC_API`` are derived from the same PRIN-owned RC1
name inventory; removals are detected by ``verify_api_surface``.

.. csv-table:: 0141A symbol dispositions
   :header: "PRINet 3.0 symbol", "PRIN symbol", "Disposition"
   :widths: 34, 34, 32

   "OscillatorState", "prin.OscillatorState", "direct re-export"
   "KuramotoOscillator", "prin.KuramotoOscillator", "direct re-export"
   "StuartLandauOscillator", "prin.StuartLandauOscillator", "direct re-export"
   "HopfOscillator", "prin.HopfOscillator", "direct re-export"
   "ExponentialIntegrator", "prin.ExponentialIntegrator", "direct re-export"
   "kuramoto_order_parameter", "prin.kuramoto_order_parameter", "direct re-export"
   "mean_phase_coherence", "prin.mean_phase_coherence", "direct re-export"
   "phase_coherence_matrix", "prin.phase_coherence_matrix", "direct re-export"
   "build_phase_knn", "prin.build_phase_knn", "direct re-export"
   "sparse_mean_phase_coherence", "prin.sparse_mean_phase_coherence", "direct re-export"
   "sparse_synchronization_energy", "prin.sparse_synchronization_energy", "direct re-export"
   "PhaseAmplitudeCoupling", "prin.PhaseAmplitudeCoupling", "direct re-export"
   "MultiRateIntegrator", "prin.MultiRateIntegrator", "direct re-export"
   "ResonanceLayer", "prin.ResonanceLayer", "direct re-export"
   "GatedPhaseActivation", "prin.GatedPhaseActivation", "direct re-export"
   "generate_benchmark_report", "prin.generate_benchmark_report", "direct re-export"
   "generate_leaderboard", "prin.generate_leaderboard", "direct re-export"
   "generate_scalr_metrics_report", "prin.generate_scalr_metrics_report", "direct re-export"
   "SubconsciousState", "prin.SubconsciousState", "direct re-export"
   "ControlSignals", "prin.ControlSignals", "direct re-export"
   "STATE_DIM", "prin.STATE_DIM", "direct re-export"
   "CONTROL_DIM", "prin.CONTROL_DIM", "direct re-export"
   "SubconsciousDaemon", "prin.SubconsciousDaemon", "direct re-export"
   "SubconsciousController", "prin.SubconsciousController", "direct re-export"
   "BackendType", "prin.BackendType", "direct re-export"
   "detect_best_backend", "prin.detect_best_backend", "direct re-export"
   "npu_available", "prin.npu_available", "direct re-export"
   "directml_available", "prin.directml_available", "direct re-export"
   "create_session", "prin.create_session", "direct re-export"
   "backend_info", "prin.backend_info", "direct re-export"
   "OscillatoryAttention", "prin.OscillatoryAttention", "direct re-export"
   "inter_frame_phase_correlation", "prin.inter_frame_phase_correlation", "direct re-export"
   "HybridPRINetV2", "prin.HybridPRINetV2", "direct re-export"
   "PhaseTracker", "prin.PhaseTracker", "direct re-export"
   "SlotAttentionModule", "prin.SlotAttentionModule", "direct re-export"
   "TemporalSlotAttentionMOT", "prin.TemporalSlotAttentionMOT", "direct re-export"
   "local_order_parameter", "prin.local_order_parameter", "direct re-export"
   "bimodality_index", "prin.bimodality_index", "direct re-export"
   "compute_p_value", "prin.compute_p_value", "direct re-export"
   "PhaseTrackerFrozen", "prin.PhaseTrackerFrozen", "direct re-export"
   "PhaseTrackerStatic", "prin.PhaseTrackerStatic", "direct re-export"
   "SlotAttentionNoGRU", "prin.SlotAttentionNoGRU", "direct re-export"
   "SlotAttentionFrozen", "prin.SlotAttentionFrozen", "direct re-export"
   "TemporalMetrics", "prin.TemporalMetrics", "direct re-export"
   "temporal_smoothness", "prin.temporal_smoothness", "direct re-export"
   "identity_switches", "prin.identity_switches", "direct re-export"
   "track_fragmentation_rate", "prin.track_fragmentation_rate", "direct re-export"
   "identity_overcount", "prin.identity_overcount", "direct re-export"
   "mostly_tracked_lost", "prin.mostly_tracked_lost", "direct re-export"
   "track_duration_stats", "prin.track_duration_stats", "direct re-export"
   "binding_robustness_score", "prin.binding_robustness_score", "direct re-export"
   "compute_full_temporal_metrics", "prin.compute_full_temporal_metrics", "direct re-export"
   "TrainingResult", "prin.TrainingResult", "direct re-export"
   "configure_neurips_style", "prin.configure_neurips_style", "direct re-export"
   "fig_clevr_n_capacity", "prin.fig_clevr_n_capacity", "direct re-export"
   "fig_chimera_heatmap", "prin.fig_chimera_heatmap", "direct re-export"
   "fig_mot_identity_preservation", "prin.fig_mot_identity_preservation", "direct re-export"
   "fig_oscillosim_scaling", "prin.fig_oscillosim_scaling", "direct re-export"
   "fig_ablation_results", "prin.fig_ablation_results", "direct re-export"
   "fig_parameter_efficiency", "prin.fig_parameter_efficiency", "direct re-export"
   "fig_training_curves", "prin.fig_training_curves", "direct re-export"
   "fig_gold_standard_chimera", "prin.fig_gold_standard_chimera", "direct re-export"
   "fig_statistical_summary", "prin.fig_statistical_summary", "direct re-export"
   "generate_all_figures", "prin.generate_all_figures", "direct re-export"
   "table_ablation_variants", "prin.table_ablation_variants", "direct re-export"
   "table_parameter_efficiency", "prin.table_parameter_efficiency", "direct re-export"
   "table_chimera_gold_standard", "prin.table_chimera_gold_standard", "direct re-export"
   "table_statistical_summary", "prin.table_statistical_summary", "direct re-export"
   "table_occlusion_sweep", "prin.table_occlusion_sweep", "direct re-export"
   "table_oscillosim_scaling", "prin.table_oscillosim_scaling", "direct re-export"
   "generate_all_tables", "prin.generate_all_tables", "direct re-export"
   "SCALROptimizer", "prin.SCALROptimizer", "alias of prin.nn.Scalr"
   "RIPOptimizer", "prin.RIPOptimizer", "alias of prin.nn.Rip"
   "SynchronizedGradientDescent", "prin.SynchronizedGradientDescent", "alias of prin.nn.SyncGd"
   "TemporalPhasePropagator", "prin.TemporalPhasePropagator", "alias of TemporalPropagator"
   "temporal_recovery_speed", "prin.temporal_recovery_speed", "alias of recovery_speed"
   "OscillatorModel", "prin.OscillatorModel", "runtime-checkable protocol"
   "ThetaGammaNetwork", "prin.ThetaGammaNetwork", "BandNetwork factory alias"
   "DeltaThetaGammaNetwork", "prin.DeltaThetaGammaNetwork", "BandNetwork factory alias"
   "triton_available", "prin.triton_available", "predicate; always false"
   "triton_fused_mean_field_rk4_step", "prin.triton_fused_mean_field_rk4_step", "typed unavailable stub"
   "triton_sparse_knn_coupling", "prin.triton_sparse_knn_coupling", "typed unavailable stub"
   "triton_pac_modulation", "prin.triton_pac_modulation", "typed unavailable stub"
   "triton_hierarchical_order_param", "prin.triton_hierarchical_order_param", "typed unavailable stub"
   "triton_fused_discrete_step", "prin.triton_fused_discrete_step", "typed unavailable stub"
   "cuda_fused_kernel_available", "prin.cuda_fused_kernel_available", "predicate; always false"
   "fused_discrete_step_cuda", "prin.fused_discrete_step_cuda", "typed unavailable stub"
   "BackendUnavailableError", "prin.BackendUnavailableError", "shared typed migration error"

WP-036 compatibility surface (sub-pass 0141B)
---------------------------------------------


The second WP-036 coding sub-pass binds the already-implemented ``prin-tensor``
(WP-014) and ``prin-train`` (WP-023) numerics to Python as thin PyO3 bridges
(no numerics added in ``prin-py`` — Coding Standards §2.1). Every trainable
binding exposed as a ``torch.autograd.Function`` has a float64
``torch.autograd.gradcheck`` test; ``FeedbackInhibition`` is a
straight-through estimator (forward and backward compute deliberately
different functions), so its gradient contract is verified against the
closed-form soft-term VJP instead, matching
``crates/prin-train/src/inhibition.rs``'s own gradient test.

Namespace: ``PolyadicTensor`` / ``CPDecomposition`` land in a new
``prin.tensor`` submodule (PRINet 3.0's ``core/decomposition.py`` has no
existing PRIN home); the five activation/inhibition/energy symbols land in
``prin.nn`` alongside ``ResonanceLayer`` / ``GatedPhaseActivation``. All eight
also resolve from the top-level ``prin`` namespace (the frozen RC1 contract).

.. csv-table:: 0141B symbol dispositions — bindings
   :header: "PRINet 3.0 symbol", "PRIN symbol", "Disposition"
   :widths: 30, 34, 36

   "PolyadicTensor", "prin.PolyadicTensor / prin.tensor.PolyadicTensor", "PyO3 binding over ``prin_tensor::hosvd`` (Tucker/HOSVD)"
   "CPDecomposition", "prin.CPDecomposition / prin.tensor.CPDecomposition", "PyO3 binding over ``prin_tensor::cp_als`` (CP/PARAFAC ALS)"
   "dSiLU", "prin.dSiLU / prin.nn.dSiLU", "``torch.autograd.Function`` over ``prin_train::activations::d_silu``; gradcheck at DV-018 epsilon"
   "PhaseActivation", "prin.PhaseActivation / prin.nn.PhaseActivation", "``torch.autograd.Function`` over ``prin_train::activations::phase_activation``; custom inner activation raises ``NotImplementedError`` (WP-036B/C parity)"
   "HolomorphicActivation", "prin.HolomorphicActivation / prin.nn.HolomorphicActivation", "``torch.autograd.Function`` over ``prin_train::activations::HolomorphicActivation`` (split-complex only; ``holomorphic=True`` raises — permanent Burn-autodiff deviation)"
   "FeedbackInhibition", "prin.FeedbackInhibition / prin.nn.FeedbackInhibition", "``torch.autograd.Function`` over ``prin_train::inhibition::FeedbackInhibition`` (hard-forward / soft-backward STE); ``delay_steps`` accepted but inert; 2-D ``rates`` only (arbitrary batch dims are WP-036B/C)"
   "HolomorphicEnergy", "prin.HolomorphicEnergy / prin.nn.HolomorphicEnergy", "``torch.autograd.Function`` over ``prin_train::energy::HolomorphicEnergy``; takes a precomputed ``task_loss`` ``(B,1)`` rather than ``target_logits``/``target_labels`` (the ``concept_proj`` head is WP-027)"
   "HolomorphicEPTrainer", "prin.HolomorphicEPTrainer / prin.nn.HolomorphicEPTrainer", "±β equilibrium-propagation *estimator* over ``prin_train::hep::HolomorphicEp``; exposes ``coupling_gradient`` / ``free_energy`` / ``beta``. ``train_step`` (SGD update) and ``loss_history`` / ``grad_norm_history`` population are WP-024 / WP-027"

.. csv-table:: 0141B symbol dispositions — deferred rebuild (no Rust owner)
   :header: "PRINet 3.0 symbol", "PRIN symbol", "Disposition"
   :widths: 30, 20, 50

   "FeedforwardInhibition", "(deferred)", "Parameter-free phase-delay gate; deliberately excluded from the WP-023 Rust rebuild (023 audit §Non-goals). Needs a ``prin-dynamics``/``prin-train`` rebuild — deferred to a future WP; see ``DOCS/experiments/0141-wp036-s1-dd-dispositions.md``"
   "DentateGyrusConverter", "(deferred)", "FFI→integration→FBI pipeline; deliberately excluded from the WP-023 rebuild (023 audit §Non-goals). Deferred rebuild"
   "DGLayer", "(deferred)", "Trainable ``nn.Module`` wrapper over ``DentateGyrusConverter``; no Rust owner. Deferred rebuild"
   "oscillatory_weight_init", "(deferred)", "Weight-initialization helper (``nn/layers.py``); no Rust owner. Deferred rebuild"
   "PhaseToRateConverter", "(deferred)", "Trainable ``nn.Module`` (``nn/layers.py``); no Rust owner. Deferred rebuild"
   "PhaseToRateAutoencoder", "(deferred)", "Trainable ``nn.Module`` (``nn/layers.py``); no Rust owner. Deferred rebuild"
   "DenseAutoencoder", "(deferred)", "Trainable ``nn.Module`` (``nn/layers.py``); no Rust owner. Deferred rebuild"
   "SparsityRegularizationLoss", "(deferred)", "Trainable-loss ``nn.Module`` (``nn/layers.py``); no Rust owner. Deferred rebuild"
   "HierarchicalResonanceLayer", "(deferred)", "Trainable ``nn.Module`` over ``DeltaThetaGammaNetwork`` with learnable projections/PAC depths; no Rust owner. Deferred rebuild"
   "PhaseAmplitudeCouplingLayer", "(deferred)", "Trainable ``nn.Module`` over ``PhaseAmplitudeCoupling`` with a learnable modulation depth; no Rust owner. Deferred rebuild"
   "PRINetModel", "(deferred)", "Top-level trainable model (``nn/layers.py``); no Rust owner. Deferred rebuild"
   "compile_model", "(deferred)", "``torch.compile`` helper (``nn/layers.py``); no Rust owner. Deferred rebuild"

WP-036 compatibility surface (sub-pass 0141C)
---------------------------------------------

The third WP-036 coding sub-pass binds the ``prin-kernels`` CPU-reference
compatibility family (the ``pytorch_*`` kernel set, sparse-coupling helpers,
and the ``prin-sim`` sweep/engine surface) to Python. All numerics remain in
Rust; ``prin.kernels`` only marshals tensors and restores tensor placement.
This sub-pass closes the ``prin-py`` half of DV-012.

.. csv-table:: 0141C symbol dispositions — real bindings
   :header: "PRINet 3.0 symbol", "PRIN symbol", "Disposition"
   :widths: 36, 34, 30

   "pytorch_mean_field_rk4_step", "prin.pytorch_mean_field_rk4_step / prin.kernels.pytorch_mean_field_rk4_step", "PyO3 binding over ``prin_kernels::mean_field_rk4::step_cpu``"
   "pytorch_sparse_knn_coupling", "prin.pytorch_sparse_knn_coupling / prin.kernels.pytorch_sparse_knn_coupling", "PyO3 binding over ``prin_kernels::sparse_knn::sparse_knn_derivatives_cpu``"
   "pytorch_pac_modulation", "prin.pytorch_pac_modulation / prin.kernels.pytorch_pac_modulation", "PyO3 binding over ``prin_kernels::pac::pac_modulate_cpu``"
   "pytorch_hierarchical_order_param", "prin.pytorch_hierarchical_order_param / prin.kernels.pytorch_hierarchical_order_param", "PyO3 binding over ``prin_kernels::compat::hierarchical_order_parameter_cpu``"
   "pytorch_multi_rate_rk4_step", "prin.pytorch_multi_rate_rk4_step / prin.kernels.pytorch_multi_rate_rk4_step", "PyO3 binding over ``prin_kernels::compat::multi_rate_rk4_step_cpu``"
   "pytorch_multi_rate_derivatives", "prin.pytorch_multi_rate_derivatives / prin.kernels.pytorch_multi_rate_derivatives", "PyO3 binding over ``prin_kernels::compat::multi_rate_derivatives_cpu``"
   "pytorch_fused_sub_step_rk4", "prin.pytorch_fused_sub_step_rk4 / prin.kernels.pytorch_fused_sub_step_rk4", "PyO3 binding over ``prin_kernels::compat::fused_sub_step_rk4_cpu``"
   "pytorch_cross_band_coupling", "prin.pytorch_cross_band_coupling / prin.kernels.pytorch_cross_band_coupling", "PyO3 binding over ``prin_kernels::compat::cross_band_coupling_cpu``"
   "pytorch_fused_discrete_step", "prin.pytorch_fused_discrete_step / prin.kernels.pytorch_fused_discrete_step", "PyO3 binding over ``prin_kernels::compat::fused_discrete_step_cpu``"
   "pytorch_fused_discrete_step_full", "prin.pytorch_fused_discrete_step_full / prin.kernels.pytorch_fused_discrete_step_full", "PyO3 binding over ``prin_kernels::compat::fused_discrete_step_full_cpu``"
   "build_knn_neighbors", "prin.build_knn_neighbors / prin.kernels.build_knn_neighbors", "PyO3 binding over ``prin_sim::compat::build_knn_neighbors``"
   "sparse_coupling_matrix", "prin.sparse_coupling_matrix / prin.kernels.sparse_coupling_matrix", "PyO3 binding over ``prin_sim::compat::sparse_coupling_matrix``"
   "sparse_coupling_matrix_csr", "prin.sparse_coupling_matrix_csr / prin.kernels.sparse_coupling_matrix_csr", "PyO3 binding over ``prin_sim::compat::sparse_coupling_matrix`` + CSR conversion"
   "csr_coupling_step", "prin.csr_coupling_step / prin.kernels.csr_coupling_step", "PyO3 binding over ``prin_sim::compat::csr_coupling_step``"
   "sparse_knn_coupling_step", "prin.sparse_knn_coupling_step / prin.kernels.sparse_knn_coupling_step", "PyO3 binding over ``prin_sim::compat::sparse_knn_coupling_step``"
   "sweep_coupling_params", "prin.sweep_coupling_params / prin.kernels.sweep_coupling_params", "PyO3 binding over ``prin_sim::compat::sweep_coupling_params``"
   "detect_oscillation", "prin.detect_oscillation / prin.kernels.detect_oscillation", "PyO3 binding over ``prin_sim::detect_oscillation``"
   "phase_to_rate", "prin.phase_to_rate / prin.kernels.phase_to_rate", "PyO3 binding over ``prin_sim::compat::phase_to_rate``"

**Deliberate deviations and preserved hazards:**

- *Mean-field order-parameter precision (D1):* PRINet 3.0 computed the
  mean-field order parameter with ``torch.complex64`` (f32 complex)
  intermediates. PRIN accumulates the same real and imaginary components in
  ``f64`` and stores the final state in ``f32``; this can introduce ~1e-7
  per-step rounding differences on the affected path. Parity tests use
  ``rtol=1e-5, atol=1e-6`` (Project Plan amendment #14 / DV-007).
- *k-NN seed determinism (D2):* ``build_knn_neighbors`` is deterministic for a
  given ``prin.Seed`` or integer counter, but the sampling order differs from
  PRINet 3.0's ``torch.Generator`` streams. The same scalar seed value does not
  guarantee the same neighbor table across implementations; compare topologies
  through the same PRIN call path.
- *Batch-dimension validation (D3):* The public ``pytorch_mean_field_rk4_step``
  wrapper explicitly validates that ``phase``, ``amplitude``, and ``frequency``
  have identical shape before dispatching any batch row to the Rust owner.
