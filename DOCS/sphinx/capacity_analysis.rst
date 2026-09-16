Capacity Analysis
=================

.. admonition:: Status of the numbers on this page
   :class: important

   This page separates three kinds of claim, and the separation is deliberate
   (Experimentation Standards; WP-037 acceptance criterion "draft clearly
   labels validation vs confirmatory campaign results"):

   1. **Implemented and verified** — the capacity relation PRIN computes, its
      Rust invariants, and its differential check against ``prinet==3.0.0``.
      These are statements about the code and are reproducible today.
   2. **Historical reference measurements** — the PRINet 3.0 empirical
      CLEVR-N capacity sweep, carried in the archived tree and reproduced
      byte-comparably from stored artefacts by ``tools/reproduce.py``. They
      describe the *reference implementation*, measured on the reference's
      hardware in February 2026. They are **not** PRIN measurements.
   3. **Confirmatory** — PRIN's own capacity measurement, which is a
      pre-registered Phase 7 campaign activity and has not been run. Nothing
      in category 3 appears on this page.

The implemented relation
------------------------

PRIN exposes working-memory capacity as the number of fast-band sub-cycles per
slow-band cycle:

.. math::

   C \;=\; \left\lfloor \frac{\bar f_\text{fast}}{\bar f_\text{slow}} \right\rfloor

where :math:`\bar f` is the **mean frequency of the band as drawn in the
state**, not the nominal band centre. This is the Lisman–Jensen θ/γ nesting
relation, which predicts on the order of seven items for a 6 Hz θ / 40 Hz γ
pair [LJ2013]_, and it is the same quantity PRINet 3.0's ``ThetaGammaNetwork``
used as its ``MultiRateIntegrator`` sub-step count.

Implementation: ``prin_dynamics::bands::BandNetwork::theoretical_capacity``
(``crates/prin-dynamics/src/bands.rs``), reachable from Python as
``BandNetwork.theoretical_capacity(state)``.

.. code-block:: python

   from prin.dynamics import BandNetwork, BandParams, Seed, create_band_state_py

   theta = BandParams(1.0, 0.1)
   gamma = BandParams(0.5, 0.1)
   net = BandNetwork.theta_gamma(4, 8, theta, gamma, 0.3)

   state = create_band_state_py(net, [(5.0, 7.0), (35.0, 45.0)], Seed(42, 0))
   net.theoretical_capacity(state)          # 6
   net.n_bands()                            # 2
   net.band_sizes()
   net.total_oscillators()                  # 12

For a three-band network the capacity is taken across the **extreme** bands
(δ and γ), not adjacent pairs:

.. code-block:: python

   delta = BandParams(1.0, 0.1)
   net3 = BandNetwork.delta_theta_gamma(4, 8, 32, delta, theta, gamma, 0.3, 0.3)
   state3 = create_band_state_py(
       net3, [(1.0, 3.0), (5.0, 7.0), (35.0, 45.0)], Seed(42, 0)
   )
   net3.theoretical_capacity(state3)        # 16
   net3.n_bands()                           # 3

Both printed values are the real output of a seeded run against PRIN |release|.
Because :math:`\bar f` is the mean of a *drawn* frequency population, the
value depends on the seed: a ``(4, 8)`` θ/γ network drawn over
``[(5, 7), (35, 45)]`` gives 6, and the same nominal bands under a different
draw can give 5 or 7. Quote the seed with the number.

Verified invariants
-------------------

The relation is not merely implemented; it is tested at three levels
(WP-013, session ``0049``):

.. list-table::
   :header-rows: 1
   :widths: 46 54

   * - Test
     - Invariant
   * - ``bands::tests::theta_gamma_capacity_matches_frequency_ratio``
     - Capacity equals ``floor(f_gamma / f_theta)`` and falls in ``[3, 15]``
       for the tested frequencies.
   * - ``bands::tests::delta_theta_gamma_capacity_uses_extreme_bands``
     - The three-band network uses δ and γ, not θ and γ.
   * - ``bands::tests::capacity_single_band_is_zero``
     - A one-band network has no nesting and returns ``0``.
   * - ``bands::tests::capacity_zero_for_non_positive_slow_frequency``
     - A non-positive or non-finite slow-band mean returns ``0`` rather than
       dividing.
   * - proptest ``capacity_positive_for_valid_frequencies``
     - Capacity is positive for every valid generated frequency pair.
   * - ``parity_bands::parity_capacity_matches_prinet_sub_step_count``
     - **Differential:** ``theoretical_capacity`` equals the
       ``sub_steps = max(1, int(f_fast / f_slow))`` that PRINet 3.0's
       ``ThetaGammaNetwork`` gives its ``MultiRateIntegrator``, for four
       frequency pairs.

The last row is the parity evidence: PRIN's capacity is the reference's
sub-step count, which is why the continuous ``BandNetwork`` can replace the
reference's per-band stepper without changing the capacity claim (Project Plan
amendment #19; see :doc:`coupling_topologies`).

Construction guards
~~~~~~~~~~~~~~~~~~~

Capacity is only meaningful for a well-formed network, and malformed bands are
rejected at construction:

.. code-block:: python

   try:
       BandNetwork.theta_gamma(4, 0, theta, gamma, 0.3)
   except ValueError as exc:
       print(f"rejected: {exc}")

The typed ``BandError`` variants are ``NoBands``, ``EmptyBand``,
``PopulationMismatch``, and the frequency-validation cases.

Historical reference measurements (PRINet 3.0, K.3)
---------------------------------------------------

The archived PRINet 3.0 ``docs/Capacity_Analysis.md`` (dated 2026-02-17,
PRINet 3.0.0, benchmark ``benchmarks/y2q4_benchmarks.py --workstream K1``)
reports an **empirical** capacity sweep on CLEVR-N: "are all *N* object colours
unique?", a binary classification that requires binding *N* objects
simultaneously. Because the palette has 8 colours, the meaningful range is
:math:`N \in \{2, \dots, 8\}`; above that the positive class is impossible.

.. admonition:: These are reference-implementation numbers
   :class: caution

   The protocol was 500 training / 200 test samples per *N*, 30 epochs, Adam at
   ``lr = 1e-3``, NLL loss, a 70 % accuracy threshold, CUDA on an RTX 4060
   8 GB, seeds 42 (train) / 99 (test), and a 19-dimensional one-hot feature
   encoding (8 colours + 8 shapes + 3 sizes). PRIN has **not** re-run this
   sweep. Quoting these values as PRIN results would be a D1 trajectory breach
   (published-result reproducibility).

Reported maximum *N* sustaining ≥ 70 % accuracy, and mean accuracy over
:math:`N \in [2, 8]`:

.. list-table::
   :header-rows: 1
   :widths: 30 22 22 26

   * - Architecture
     - Max *N* ≥ 70 %
     - Mean accuracy
     - Pattern
   * - ``DiscreteDTG`` (oscillatory)
     - 8
     - 71.9 %
     - Non-monotonic; dips at *N* = 5–6
   * - Transformer (attention baseline)
     - 8
     - 82.1 %
     - Improves monotonically past *N* = 5
   * - LSTM (sequential baseline)
     - 3
     - 68.3 %
     - Monotonic decline past *N* = 3
   * - ``HybridPRINetV2``
     - 8
     - 77.7 %
     - Non-monotonic; recovers at *N* = 6, 8

The reference's own interpretation, which PRIN carries forward as a hypothesis
rather than a finding:

* The LSTM collapse beyond :math:`N \approx 3` is the binding bottleneck that
  motivates oscillatory models, and is consistent with the working-memory
  literature on a :math:`4 \pm 1` item limit [Cowan2001]_.
* The mid-range dip in the oscillatory models was hypothesised to be a
  resonance mismatch: 4/8/16-oscillator δ/θ/γ bands create natural capacity
  bins, and :math:`N \in \{5, 6, 7\}` falls between the 4- and 8-oscillator
  bins.
* The reference listed its own limitations: a fixed 30-epoch budget, a single
  seed pair, an 8-colour palette capping meaningful *N*, and identical
  ``d_model = 64`` across architectures.

Artefact provenance
~~~~~~~~~~~~~~~~~~~

The reference sweep's stored JSON is
``benchmarks/benchmark_y2q4_k1_capacity.json`` in the archived tree, and it is
one of the 172 records in the governed SHA-256 manifest
``paper/artefact_manifest.json``. ``tools/reproduce.py --verify-manifest``
checks every stored artefact against that manifest before regenerating the
publication figures and tables, so the numbers behind
``fig2_clevr_n_capacity`` are reproducible without training or GPU access.

What PRIN must still establish
------------------------------

Three things are open, and all three are Phase 7 campaign work under the
Experimentation Standards (pre-registration with expected results and failure
conditions documented **before** execution):

1. **PRIN's own empirical capacity sweep.** ``benchmarks/y2q4_benchmarks.py``
   exposes ``run_k1_capacity_sweep``; it has not been run at production scale
   in PRIN. WP-033 built the runner and validated it at characterization scale
   only — its brief's explicit non-goal was "drawing conclusions from final
   measurements".
2. **The band-bin hypothesis.** Whether tuning ``n_delta`` / ``n_theta`` /
   ``n_gamma`` to match the target *N* removes the mid-range dip is a testable
   prediction that has never been run in either implementation.
3. **The relation between :math:`C` and empirical *N*.** ``theoretical_capacity``
   counts nested sub-cycles; the sweep measures classification accuracy. That
   the two should agree at all is an assumption, not a result — for
   6 Hz / 40 Hz bands :math:`C = 6` while the reference sustained accuracy to
   :math:`N = 8`.

Until those run, the honest summary is: PRIN computes and verifies the same
capacity relation the reference used, and the reference's empirical capacity
numbers are historical data about a different implementation.

References
----------

.. [LJ2013]
   Lisman, J. E., & Jensen, O. (2013). The theta-gamma neural code.
   *Neuron*, 77(6), 1002–1016.

.. [Cowan2001]
   Cowan, N. (2001). The magical number 4 in short-term memory: A
   reconsideration of mental storage capacity. *Behavioral and Brain Sciences*,
   24(1), 87–114.
