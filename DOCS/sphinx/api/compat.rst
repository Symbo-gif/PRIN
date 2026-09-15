Compatibility Layers (``prin._torch_compat``, ``prin._compat``)
===============================================================

The two internal adaptation layers that let the ported PRINet 3.0 acceptance
suite run against PRIN unchanged. They are underscore-private by convention,
documented here because they appear in acceptance-suite imports and in
tracebacks, and because their contract is load-bearing:

* :mod:`prin._torch_compat` is the ``torch.Tensor``-facing facade. It performs
  tensor/state marshalling and orchestration only; every numerical result is
  delegated to the compiled Rust owners in :mod:`prin._prin_core`. This is
  where the PRINet-3.0-signature oscillator models live —
  ``KuramotoOscillator(n_oscillators, coupling_strength=1.0, decay_rate=0.1,
  freq_adaptation_rate=0.01, coupling_mode="auto", ...)`` and
  ``OscillatorState.create_random(n, seed=...)`` — as distinct from the
  float64 NumPy core types in :doc:`dynamics`.
* :mod:`prin._compat` holds name adaptation and fail-closed backend
  dispositions: the ``triton_*`` / ``*_cuda`` symbols with no CPU analogue
  raise a typed backend-unavailable error rather than silently substituting a
  different algorithm, and ``triton_available()`` / ``cuda_available()``
  report ``False`` on a host without the backend (Testing Standards §1.6 —
  an availability guard must probe executability, not registration).

Neither layer contains numerics; ``tools/check_no_python_numerics.py``
enforces that in CI (Project Plan §4 rule 2).

The remaining underscore modules are governance internals rather than API:
``prin._deprecation`` (the RC1 public-API freeze and ``verify_api_surface``),
``prin._public_api`` (the canonical ``RC1_PUBLIC_API`` tuple that seeds both
``prin.__all__`` and the freeze), ``prin._ort`` (the ONNX Runtime
execution-provider probe), and ``prin._phase0`` (Phase 0 exit-gate evidence
consolidation). They are described in :doc:`../migration_guide` and in
``DOCS/experiments/0141-wp036-s1-dd-dispositions.md``.

``prin._deprecation`` is documented below because its surface is used directly
by downstream code and by the freeze regression test:

.. code-block:: python

   from prin._deprecation import verify_api_surface

   missing, unexpected = verify_api_surface(prin.__all__)
   assert (missing, unexpected) == (set(), set())

``prin._prin_core`` — the compiled PyO3 extension — is not autodoc'd here.
PyO3 classes render poorly through autodoc; its authoritative typed surface is
the shipped stub ``python/prin/_prin_core.pyi``, and its behavior is documented
by the rustdoc of the crate that owns each binding (see :doc:`../rust_api`).

Both facades are rendered by **module docstring only** unless noted. That is
deliberate: nearly every object ``prin._torch_compat`` exposes is a re-export of
something already documented and indexed on its owning page, and Sphinx resolves
a re-export to a canonical name — so autodoc'ing its members emits a second
object description for each one. ``:no-index:`` suppresses that for classes and
functions but not for their ``@dataclass`` fields, which is enough to fail a
``-W`` build.

``prin._compat`` is the exception: it *defines* the availability predicates, the
typed backend-unavailable error, the ``OscillatorModel`` protocol, and the
fail-closed ``triton_*`` / ``*_cuda`` stubs, so those are documented here. Its
re-exports and aliases are excluded — each is documented on the page of the
module that owns it.

.. automodule:: prin._torch_compat
   :no-index:

.. automodule:: prin._compat
   :members:
   :exclude-members: RIPOptimizer, SCALROptimizer, SynchronizedGradientDescent, TemporalPhasePropagator, temporal_recovery_speed, ThetaGammaNetwork, DeltaThetaGammaNetwork, recovery_speed, TemporalPropagator, BandNetwork

.. automodule:: prin._deprecation
   :members: verify_api_surface, deprecated, deprecated_parameter, FROZEN_PUBLIC_API, RC1_PUBLIC_API
   :no-index:
