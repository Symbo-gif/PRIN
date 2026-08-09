# prin.eval (Evaluation utilities)

MOT and temporal metrics sub-package (Phase 5).

## Overview

Ports of PRINet 3.0 `nn/mot_evaluation.py` and `utils/temporal_metrics.py`:
- MOTA, MOTP, IDF1, identity switches, and identity preservation.
- Synthetic sequence generators for multi-object tracking evaluation.

Pure Python orchestration layer calling into Rust core kernels for hot inner metric computation.
