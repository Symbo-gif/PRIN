DLPack Bridge API (prin.dlpack)
================================

Zero-copy tensor exchange between PyTorch and the PRIN Rust core via the
DLPack C ABI. The Python layer only marshals capsules; all numerics live in
the compiled ``prin._prin_core`` extension (built from ``crates/prin-py``).

.. automodule:: prin.dlpack
   :members:
   :undoc-members:
