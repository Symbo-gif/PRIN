Datasets API (``prin.datasets``)
================================

Dataset utilities for standard image-classification benchmarks: cached
CIFAR-10 and Fashion-MNIST loaders (``torchvision``) plus a quick top-1
accuracy helper. Strict port of PRINet 3.0 ``prinet.utils.datasets``.

This module is data plumbing only — no numerics live here. Data is cached
under ``~/.cache/prinet/datasets`` by default, so the loaders need network
access only on first use; tests use cached fixtures and never reach the
network (Testing Standards §4).

The synthetic temporal CLEVR-N sequence generators used for binding and
multi-object-tracking experiments are **not** here — they are owned by
:mod:`prin.temporal_training` and by ``prin_train::dataset`` in Rust.

.. automodule:: prin.datasets
   :members:
