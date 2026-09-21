"""Campaign drivers for the Phase 7 Experimentation and Benchmarking Campaign.

Each ``exp00n_driver`` module is the committed, tested driver named by that
experiment's pre-registration (campaign plan §7.2, §12.1). Campaign runs
never invoke ``benchrunner`` directly; a driver validates campaign metadata,
performs the pre-registered comparison, and writes results through
``benchmarks._common.result.write_result`` plus its own
``campaign-metadata.json`` sidecar.
"""

from __future__ import annotations
