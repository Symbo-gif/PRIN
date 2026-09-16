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

.. admonition:: Parameter ownership is not uniform
   :class: caution

   ``ResonanceLayer`` and ``DiscreteDeltaThetaGammaLayer`` are fully
   torch-trainable bridge layers: their ``torch.nn.Parameter`` objects are the
   canonical optimizer-visible values, each forward synchronizes them into the
   Rust/Burn owner, backward returns real Burn-computed parameter VJPs, and a
   ``torch.optim`` step changes the next Rust-owned forward.

   Other compatibility modules use documented value-preserving mirrors or
   straight-through terms for PRINet-3.0 API parity. For example,
   ``DiscreteDeltaThetaGamma`` pushes canonical values into a
   non-differentiable Rust stepper, while ``HierarchicalResonanceLayer`` keeps
   its numerically active PAC depths Rust-owned. A populated ``.grad`` on one
   of those mirrors is not a Burn parameter VJP. Check the class docstring
   before interpreting a parameter as a genuine torch-training path.

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
