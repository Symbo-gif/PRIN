# prin-train

Trainable layer stack for PRIN: DiscreteDeltaThetaGamma, resonance layers,
inhibition with straight-through-estimator top-k, phase activations, the HEP
(Holomorphic Equilibrium Propagation) trainer, and resonance-aware optimizers
(SyncGD, SCALR, RIP, AlternatingOptimizer).

Used natively via Burn **and** exposed to PyTorch training loops through
`torch.autograd.Function` bridges in `prin-py` / `python/prin/nn/`.

Rebuild target for PRINet 3.0 `nn/{layers,optimizers,activations,hep}.py` and
the trainable half of `core/propagation/{networks,inhibition}.py`.
