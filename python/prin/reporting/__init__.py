"""Reporting: benchmark JSON reports, figures, tables, profiler.

Near-verbatim ports of PRINet 3.0 ``utils/{benchmark_reporting,
figure_generation, table_generation, profiler}.py``. The JSON artefact schema
is unchanged so PRINet 3.0 artefacts remain valid. Figures are 300 DPI
matplotlib; tables are LaTeX fragments; the profiler wraps torch.profiler and
Rust ``tracing`` spans. Implemented during Phases 1 and 6.
"""

from __future__ import annotations

__all__: list[str] = []
