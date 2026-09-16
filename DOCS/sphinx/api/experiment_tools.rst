Experiment Tools API (``prin.y4q1_tools``)
==========================================

The PRINet 3.0 ``prinet.utils.y4q1_tools`` public API: the Year-4-Q1
experiment utilities that the paper-critical benchmark scripts are built
from. Profiling helpers (``count_flops``, ``measure_wall_time``) and the
result dataclasses are real; the ablation framework (``AblationConfig``,
``AblationHybridPRINetV2``, ``create_ablation_model``) and the CLEVR-N
training drivers (``train_clevr_n_single_seed``, ``train_clevr_n_extended``)
delegate to the Rust-native training pipeline in :mod:`prin.train` and to the
hybrid models in :mod:`prin.nn`.

Benchmark environment capture is mandatory for anything that reports a timing
(Benchmarking and Reproducibility Standards); ``measure_wall_time`` returns
the environment block alongside the measurement so a result cannot be quoted
without it.

.. automodule:: prin.y4q1_tools
   :members:
