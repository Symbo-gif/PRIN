Getting Started
===============

.. note::
   Ported from the PRINet 3.0 Getting Started Tutorial during Phase 1/6.

Installation
------------

.. code-block:: bash

   pip install prin

Development install:

.. code-block:: bash

   pip install maturin
   maturin develop -m crates/prin-py/Cargo.toml
   pip install -e ".[dev]"
