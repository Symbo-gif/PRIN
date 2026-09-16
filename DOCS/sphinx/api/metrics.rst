Metrics API (``prin.metrics``)
==============================

Synchronization, coherence, spectral, energy, and chimera metrics: Kuramoto
order parameter ``R``, mean phase coherence, phase-coherence matrix, local
order parameter, bimodality index, power spectral density, synchronization
energy, and inter-frame phase correlation.

All numerical authority lives in the compiled Rust core
(``prin._prin_core``, crate ``prin-metrics``); this module re-exports the
Rust-backed functions for ergonomic Python access and adds the thin
``torch.Tensor`` wrappers that the acceptance suite imports.

Two documented metric conventions matter when comparing against PRINet 3.0:

* ``chimera.strength_of_incoherence`` and
  ``strength_of_incoherence_temporal`` are deliberately **not** parity-matched
  to the PRINet 3.0 fixture — that fixture's wrap-centring formula is an
  upstream defect (EMA-001 M-F1, Z3-confirmed), so PRIN's corrected
  implementation is authoritative (Project Plan amendment #25).
* Cross-platform reduction noise in the derived metric arrays is an accepted
  reference-implementation hazard at ``rtol=2e-6`` for corpus regeneration
  (amendments #16, #17; :doc:`../parity_report`).

.. automodule:: prin.metrics
   :members:
