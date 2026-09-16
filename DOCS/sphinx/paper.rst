Paper Artefacts
===============

The publication sources live in ``paper/`` at the repository root. They are
carried over unchanged from PRINet 3.0 (Project Plan §14) and wired to PRIN's
reproduction pipeline; ``paper/README.md`` is the authoritative inventory.

.. admonition:: What these numbers are
   :class: caution

   Every figure and table in the paper renders a **stored PRINet 3.0 benchmark
   artefact**. They are historical reference results, reproduced byte-comparably
   — not PRIN measurements. PRIN's own confirmatory results are a pre-registered
   Phase 7 campaign activity, and revising the paper's claims is explicitly out
   of scope for WP-037. See :doc:`parity_report` for what PRIN has actually
   verified.

Sources and derived output
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 16 50

   * - Path
     - Tracked
     - Role
   * - ``paper/main.tex``
     - yes
     - Main paper: 841 lines, 8 numbered sections plus an unnumbered
       Reproducibility Statement, a hand-written 15-entry
       ``thebibliography``.
   * - ``paper/supplementary.tex``
     - yes
     - Supplementary material, 10 bibliography entries.
   * - ``paper/artefact_manifest.json``
     - yes
     - Governed SHA-256 manifest for the 172 stored benchmark JSON artefacts;
       append-only.
   * - ``paper/figures/README.md``, ``paper/tables/README.md``
     - yes
     - Per-artefact description tables.
   * - ``paper/figures/*.pdf``, ``*.png``
     - **no**
     - 14 figures × 2 formats. Generated.
   * - ``paper/tables/tab_*.tex``
     - **no**
     - 11 LaTeX table fragments. Generated.

The generated artefacts are gitignored because they are derived output with a
byte-comparable regeneration path — the same reasoning that keeps
``DOCS/test_and_benchmark_results/`` out of the repository
(Benchmarking and Reproducibility Standards). A fresh clone has the sources and
the READMEs; you regenerate the rest.

Regenerating
------------

From the repository root:

.. code-block:: bash

   python tools/reproduce.py --output-dir paper --verify-manifest

``--verify-manifest`` checks all 172 stored artefacts against their SHA-256
digests **before** rendering anything, and fails closed on a missing, modified,
or unmanifested file. A full run writes 39 files (14 × 2 figures + 11 tables)
and needs no training, no GPU, and no random sampling.

Rendering is deterministic: ``matplotlib.use("Agg", force=True)``, a fixed
``_FIXED_DATE`` of 2000-01-01 stamped into every PDF, and no sampling anywhere
in the generators. That is what makes the output byte-comparable — the property
``repro.yml`` and ``tests/test_publication_generation.py`` both rely on.

To generate one class only:

.. code-block:: bash

   python tools/reproduce.py --figures-only --output-dir paper --verify-manifest
   python tools/reproduce.py --tables-only  --output-dir paper --verify-manifest

Without ``--output-dir paper`` the pipeline writes to
``DOCS/test_and_benchmark_results/reproduction/`` instead, which is where
``repro.yml`` compares it against the reference.

Calling the generators directly
-------------------------------

The two batch entry points default to the paper tree, so this is equivalent:

.. code-block:: python

   from prin.reporting.figure_generation import (
       DEFAULT_OUTPUT_DIR,
       DEFAULT_RESULTS_DIR,
       generate_all_figures,
   )
   from prin.reporting.table_generation import generate_all_tables

   print(DEFAULT_OUTPUT_DIR.name)        # figures   (under <repo>/paper)

   figures = generate_all_figures()      # -> dict[str, list[Path]], PDF + PNG each
   tables = generate_all_tables()        # -> dict[str, Path]

Output paths are confined. ``_dirs()`` resolves the target and raises
``OutputPathError`` unless it is equal to or nested under one of
``ALLOWED_OUTPUT_ROOTS`` — ``benchmarks/results``,
``DOCS/test_and_benchmark_results``, ``paper``, and the system temp directory.
The confinement is asserted by
``tests/test_publication_generation.py::test_output_paths_are_confined``.

Compiling
---------

Regenerate first, then:

.. code-block:: bash

   cd paper
   pdflatex -interaction=nonstopmode main.tex
   pdflatex -interaction=nonstopmode main.tex
   pdflatex -interaction=nonstopmode supplementary.tex
   pdflatex -interaction=nonstopmode supplementary.tex

The second pass resolves the cross-references. No LaTeX build runs in CI;
compilation is a manual pre-submission step. ``main.tex`` is venue-neutral
(``\documentclass[11pt]{article}``) and loads no conference style file.

Artefact wiring
---------------

``main.tex`` includes five figures and inputs seven tables;
``supplementary.tex`` includes five figures and inputs two tables.
``\includegraphics`` paths carry an explicit ``.pdf`` extension and ``\input``
paths carry none; both are relative to ``paper/`` because there is no
``\graphicspath``.

``tests/test_paper_wiring.py`` parses both sources and asserts every reference
resolves to an entry of ``prin.reporting.figure_generation.FIGURE_GENERATORS``
or ``table_generation.TABLE_GENERATORS``. Renaming a generator therefore breaks
a fast unit test rather than a ``pdflatex`` run days later.

Four figures (``fig5_mot_occlusion_comparison``, ``fig11_flops_scaling``,
``fig12_supercritical_regime``, ``fig15_noise_velocity``) and two tables
(``tab_geometry``, ``tab_supercritical``) are generated but referenced by
neither source. They are retained because the generators are a faithful port of
the reference's full publication set and
``tests/test_publication_generation.py`` asserts all 14 and all 11 by name.
There is no ``fig1_*``: figure 1 never existed in the reference implementation.

Provenance and known inconsistencies
-------------------------------------

The sources are verbatim reference material, so the inconsistencies they carry
are recorded rather than silently corrected — see ``paper/README.md`` §"Known
inconsistencies inherited from the reference" for the full list (single-author
``\author{}`` block versus a three-author citation, ``thebibliography`` width
arguments larger than the entry counts, two bibitem label/key mismatches).

``neurips_2026.sty`` and the reference's compiled PDFs were deliberately not
carried over: the style file is loaded by neither source, and the PDFs are
derived output.
