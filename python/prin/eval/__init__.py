"""Evaluation utilities: MOT metrics and temporal metrics.

Ports of PRINet 3.0 ``nn/mot_evaluation.py`` and ``utils/temporal_metrics.py``:
MOTA/MOTP/IDF1, identity switches, identity preservation, synthetic sequence
generators. Orchestration lives here; hot inner metric loops call the Rust
core. Implemented during Phase 5.
"""

from __future__ import annotations

__all__: list[str] = []
