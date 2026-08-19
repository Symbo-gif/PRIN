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

  Python bindings (``prin.nn``) are not exposed yet — the production
  ``torch.autograd.Function`` bridge is WP-025's scope, and GPU-backed Burn backends
  (``wgpu``/``cuda``) are deferred to the same WP per the Project Plan risk register.

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
