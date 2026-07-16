# notebooks/

Tutorial notebooks (ported and new, per project plan §11):

1. `01_getting_started.ipynb` — oscillator dynamics and synchronization basics.
2. `02_hierarchical_binding.ipynb` — δ/θ/γ band networks and PAC.
3. `03_multi_object_tracking.ipynb` — PhaseTracker MOT on temporal CLEVR-N.
4. `04_torch_bridge.ipynb` — **new**: using the Rust core from PyTorch training
   loops via the DLPack/autograd bridges.

All notebooks must run end-to-end in CI documentation builds (Definition of
Done #8).
