Tutorial Notebooks
==================

Four runnable Jupyter notebooks live in ``notebooks/`` at the repository root.
They are the hands-on counterpart to the guides on this site: every one is
committed **with its executed outputs**, so reading the rendered notebook is
sufficient — you do not have to run it to see what the API produces.

.. list-table::
   :header-rows: 1
   :widths: 30 46 24

   * - Notebook
     - Covers
     - Reference analogue
   * - ``01_oscillosim_quickstart.ipynb``
     - Oscillator dynamics and synchronization basics: ``quick_simulate``
       throughput, trajectory recording, the coupling-strength sweep through the
       Kuramoto transition, a coupling-mode comparison, and a ring chimera state
       diagnosed with ``local_order_parameter`` / ``chimera_index``.
     - PRINet 3.0 ``01_oscillosim_quickstart``
   * - ``02_clevr_n_binding.ipynb``
     - Hierarchical δ/θ/γ binding and multi-object tracking: model architecture
       and parameter counts, a short real training run on synthetic temporal
       CLEVR-N, an object-count scaling sweep, oscillator phase dynamics during
       binding, and MOT evaluation via ``evaluate_tracking``.
     - PRINet 3.0 ``02_clevr_n_binding``
   * - ``03_custom_coupling.ipynb``
     - Coupling topologies and phase–amplitude coupling: the built-in topology
       builders, a custom two-cluster graph driven through the Rust core,
       simulation comparison across coupling modes, the PAC modulation curve, the
       Abrams–Strogatz cosine kernel, and rewiring probability versus
       synchronization speed.
     - PRINet 3.0 ``03_custom_coupling``
   * - ``04_torch_bridge.ipynb``
     - **New, no reference counterpart.** Using the Rust core from PyTorch
       training loops: DLPack round-trips, an ``autograd.Function`` bridge
       forward and backward, float64 ``gradcheck``, Rust-owned parameter state
       via ``rust_state_dict()``, and a complete Adam training loop.
     - —

Names ``01``–``03`` follow the reference implementation because the ported
acceptance suite is parametrized over them
(``tests/test_acceptance_y4q3.py::TestNotebooks.EXPECTED``), and Project Plan
amendment #35 froze ported-test parametrization. ``notebooks/README.md`` maps
each name to the PRIN tutorial content it carries.

Measured runtime budget
------------------------

.. list-table:: Wall-clock for a full ``nbclient`` execution, kernel start included
   :header-rows: 1
   :widths: 50 20 30

   * - Notebook
     - Runtime
     - Cells (code / markdown)
   * - ``01_oscillosim_quickstart.ipynb``
     - 20.3 s
     - 7 / 8
   * - ``02_clevr_n_binding.ipynb``
     - 19.9 s
     - 7 / 8
   * - ``03_custom_coupling.ipynb``
     - 14.8 s
     - 8 / 8
   * - ``04_torch_bridge.ipynb``
     - 9.4 s
     - 10 / 10
   * - **All four**
     - **64.4 s**
     - —

Measured CPU-only on the maintainer's Windows workstation during WP-037 S1
(session ``0145``). These are a CI-sizing budget, not a benchmark: Benchmarking
and Reproducibility Standards require the environment to travel with any quoted
timing, and no environment block accompanies these numbers.

Running them
------------

.. code-block:: bash

   pip install -e ".[dev]"
   maturin develop -m crates/prin-py/Cargo.toml
   jupyter notebook notebooks/

The notebooks need the compiled extension, so ``maturin develop`` (or an
installed wheel) is a prerequisite. They run on CPU only and make no network
access.

Execution is a tested property, not a claim
-------------------------------------------

``tests/test_notebooks.py`` executes all four end-to-end through ``nbclient``
and fails on any error output, so a notebook that stops running is a red test
rather than a stale artefact. Those tests carry ``@pytest.mark.slow`` and run
in the full-suite leg; the cheap structural invariants (``nbformat == 4``, cell
counts, outputs present) run in the default gate. Definition of Done #8 —
"all four notebooks run end-to-end" — is discharged by that harness.

Scaling note
------------

The reference notebooks were written for a CUDA workstation and were committed
unexecuted. PRIN's are sized to run in CI on a shared CPU runner, so they use
smaller populations, fewer steps, and fewer epochs than the reference did.
Each notebook states its own runtime budget in its title cell and says
explicitly where it scaled a reference value down.

.. admonition:: Scaled-down runs are not results
   :class: important

   A notebook demonstrates an API. It does not establish a scientific claim,
   and nothing in ``notebooks/`` should be quoted as a measurement. The
   governed numbers live in ``benchmarks/results/`` with their environment
   block (Benchmarking and Reproducibility Standards), and PRIN's confirmatory
   measurements are Phase 7 campaign work under the Experimentation Standards.
