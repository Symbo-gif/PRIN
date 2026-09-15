Core API (``prin``)
===================

The flat top-level namespace. ``prin.__all__`` re-exports every public symbol
from the 25 modules that make up the package, so ``from prin import X`` works
for the whole PRINet 3.0 compatibility surface plus PRIN's own additions —
175 names at |release|.

.. code-block:: python

   import prin

   print(prin.__version__)              # 0.3.0 — must equal prin.core_version()
   print(prin.core_version())           # version of the loaded Rust extension
   print(len(prin.__all__))             # 175

   from prin._deprecation import verify_api_surface

   missing, unexpected = verify_api_surface(prin.__all__)
   print(missing, unexpected)           # set() set()

The freeze is enforced by ``tests/test_api_surface.py`` and
``tests/test_api_surface_matrix.py`` against the canonical
``prin._public_api.RC1_PUBLIC_API`` tuple, and the per-symbol mapping from
PRINet 3.0 is in the :doc:`../migration_guide`.

Where each symbol is documented
-------------------------------

This page renders the ``prin`` module docstring only. Its members are
documented — with their fields, signatures, and source links — on the page of
the module that defines them, which is what the toctree below is organized by.

That split is a build requirement, not a stylistic one. ``prin`` re-exports
objects that are also documented on their owning module's page, and Sphinx
resolves a re-export to a canonical name; describing the same object twice is a
"duplicate object description" warning, which ``sphinx-build -W`` turns into a
build failure. Autodoc'ing the flat namespace with ``:members:`` here — even
under ``:no-index:``, which suppresses a class description but not the
descriptions generated for its ``@dataclass`` fields — reproduces exactly that
failure for every re-exported dataclass. The CI documentation job builds with
``-W``, so this is a checked invariant rather than a convention.

Two namespace details that trip people up:

* ``CouplingMode``, ``Seed``, ``RK4Integrator``, ``BandNetwork``, and the other
  core value types are in :doc:`dynamics`, not at the top level.
* ``chimera_index``, ``cosine_coupling_kernel``, and
  ``strength_of_incoherence`` are in :mod:`prin.simulation`, not at the top
  level.

.. automodule:: prin
   :no-index:
