Kernels API (``prin.kernels``)
==============================

Tensor marshalling for the Rust-owned compatibility kernels and parameter
sweeps. This module performs shape orchestration and tensor/list conversion
only; every numerical result is produced by ``prin._prin_core`` (crate
``prin-kernels``, single-source CubeCL kernels with a CPU reference).

The ``pytorch_*`` family are the CPU-reference entry points for the fused
kernels — mean-field RK4 step, sparse k-NN coupling, fused discrete step,
hierarchical order parameter, PAC modulation, multi-rate derivatives, and the
CSR coupling step. The ``triton_*`` and ``*_cuda`` names from PRINet 3.0 are
documented availability stubs in :doc:`compat`
(``triton_available()`` → ``False``): they raise a typed
``BackendUnavailableError``-class error rather than silently falling back,
per the D-D dispositions in
``DOCS/experiments/0141-wp036-s1-dd-dispositions.md``.

See :doc:`../kernel_architecture` for the single-source kernel design and the
per-kernel GPU-vs-CPU tolerances, and :doc:`../parity_report` for the measured
f32 dispatch deviations.

.. automodule:: prin.kernels
   :members:
