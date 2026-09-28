Dynamics API (``prin.dynamics``)
================================

Oscillator state, models, integrators, coupling modes, phase–amplitude
coupling, band networks, and temporal propagation. Every type here is a
direct re-export of the compiled Rust core (``prin._prin_core``, crate
``prin-dynamics``), so states and parameters are NumPy ``float64`` and the
preserved numerical hazards of :doc:`../parity_report` apply exactly, each on
the path where PRINet 3.0 applies it. Phase wraps ``% 2π`` everywhere.
``EulerIntegrator`` and ``RK4Integrator`` follow PRINet 3.0's
``OscillatorModel`` guard by default: amplitude floored at exactly ``0`` with
no ceiling, and derivatives clamped to ``±1e4`` only on sparse k-NN coupling.
Pass ``guard="bounded"`` for the ``[1e-6, 10]`` / ``±1e4`` guard of PRINet
3.0's fused-kernel and OscilloSim paths.

Use this surface when you want the reference integrator semantics and
float64 authority. For the PRINet 3.0-compatible ``torch.Tensor``-facing
oscillator models (``KuramotoOscillator(..., coupling_mode="auto")``,
``OscillatorState.create_random(n, seed=...)``) see :doc:`compat`; for the
high-level batched simulator see :doc:`simulation`.

Deterministic seeding flows through the ``Seed`` type — there is no hidden
RNG (Project Plan §4 rule 4).

.. automodule:: prin.dynamics
   :members:
