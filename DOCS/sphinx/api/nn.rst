Neural Network API (``prin.nn``)
================================

``torch.nn.Module`` wrappers over the Rust-backed bridges. Each module
marshals tensors to its owner in ``prin-train`` (or ``prin-dynamics``) through
``prin.nn._bridge.apply_rust_bridge`` and stitches the forward and VJP calls
into the PyTorch autograd graph; no numerics run in Python.

Sixty names are re-exported at package level. The submodule sections below
document the same objects at their defining location, plus the few symbols that
are **not** re-exported — the ablation-variant framework, the MOT-17 loader,
the subconscious-model compatibility aliases, and the bridge entry point
itself.

.. admonition:: Where the weights live differs by layer
   :class: caution

   ``DiscreteDeltaThetaGamma`` and ``HierarchicalResonanceLayer`` declare real
   ``torch.nn.Parameter``s that an optimizer can update.
   ``DiscreteDeltaThetaGammaLayer`` and ``ResonanceLayer`` keep their weights
   inside the Rust bridge: input gradients flow, but ``parameters()`` is empty
   or disconnected from ``forward``, and the weights are reachable only as
   opaque bytes through ``rust_state_dict()``. Check
   ``sum(p.numel() for p in layer.parameters())`` before handing a layer to an
   optimizer. Recorded as an out-of-scope discovery in
   ``DOCS/experiments/0145-wp037-s1-handoff.md``.

.. automodule:: prin.nn
   :members:

Submodules
----------

.. automodule:: prin.nn._bridge
   :members:
   :no-index:

.. automodule:: prin.nn.ablation_variants
   :members:
   :no-index:

.. automodule:: prin.nn.mot_evaluation
   :members:
   :no-index:

.. automodule:: prin.nn.subconscious_model
   :members:
   :no-index:

.. automodule:: prin.nn.hierarchical_layers
   :members:
   :no-index:

.. automodule:: prin.nn.phase_tracker
   :members:
   :no-index:

.. automodule:: prin.nn.temporal_compat
   :members:
   :no-index:

.. automodule:: prin.nn.slot_attention
   :members:
   :no-index:

.. automodule:: prin.nn.hybrid
   :members:
   :no-index:

.. automodule:: prin.nn.hybrid_compat
   :members:
   :no-index:

.. automodule:: prin.nn.optimizers
   :members:
   :no-index:

.. automodule:: prin.nn.inhibition_layers
   :members:
   :no-index:

.. automodule:: prin.nn.autoencoders
   :members:
   :no-index:

.. automodule:: prin.nn.energy
   :members:
   :no-index:

.. automodule:: prin.nn.allocation
   :members:
   :no-index:

.. automodule:: prin.nn.model
   :members:
   :no-index:

.. automodule:: prin.nn.deferred_layers
   :members:
   :no-index:
