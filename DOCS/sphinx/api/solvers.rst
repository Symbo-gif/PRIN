Solvers API (``prin.solvers``)
==============================

The PRINet 3.0 ``prinet.utils.cuda_kernels`` solver family
(``BatchedRK45Solver``, ``FixedStepRK4Solver``, ``SolverResult``,
``gradient_checkpoint_integration``) over its Rust integrator owners. This
module orchestrates batching, step budgets, and checkpoint boundaries; the
integration arithmetic is owned by ``prin-dynamics`` and reached through
:mod:`prin.dynamics`.

Convergence order is a tested invariant, not a documented hope: RK4 error
scales as ``h⁴`` (Testing Standards §2, Rust property layer).

.. automodule:: prin.solvers
   :members:
