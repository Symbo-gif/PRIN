# EXP-001 D1 correction — S1 evidence

Root-cause evidence for the EXP-001 D1 correction cycle, session S1
([brief](../../DOCS/sessions/contingencies/2026-09-23-exp001-d1-s1-correction-implementation.md);
record in [`DOCS/audits/2026-09-24-exp001-d1-correction-audit.md`](../../DOCS/audits/2026-09-24-exp001-d1-correction-audit.md)).
Every file here was generated on the E3 host (Windows 11, project venv,
`torch 2.11.0+cu128`, `numpy 2.5.1`) by the committed scripts below, run from
the repository root.

| File | What it is |
|---|---|
| [`root_cause_decomposition.py`](root_cause_decomposition.py) | Generator. Re-derives every H1 and H2a breach and attributes each one by controlled substitution: PRINet 3.0 re-run with its DV-007 casts widened to float64, with PRIN's pre-correction guard swapped in, or from initial phases moved by one ulp. |
| [`root-cause-decomposition-prefix.json`](root-cause-decomposition-prefix.json) | That run against the **pre-fix** build (`bd737e1`, the reproduction commit; extension built from a worktree and imported via `PYTHONPATH`, as the file's `prin_extension` field records). The build reproduces E3 exactly (19/504 and 103/1,000, same sets) and equals PRINet 3.0 evaluated in float64 with the pre-correction guard to `3.3e-12` on every well-conditioned case. |
| [`root-cause-decomposition-postfix.json`](root-cause-decomposition-postfix.json) | The same run against the **post-fix** build (`34e8811`). PRIN matches PRINet 3.0 evaluated in float64 with its native guard on all 978 well-conditioned fuzz cases, 973 of them to `≤ 4e-14`, and on all 504 corpus cases to `2.0e-15`. |
| [`dv007_exactness_audit.py`](dv007_exactness_audit.py) | Generator for the campaign plan §10.4 item 3 evidence. It evaluates PRINet 3.0's own discrete map (equations, Euler/RK4 update, guards, phase wrap modulo the float64 `2π`, metrics) in 50-digit mpmath from each case's exact float64 initial state, and runs SymPy lemmas L1–L4. |
| [`dv007-exactness-audit.json`](dv007-exactness-audit.json) | For all 57 DV-007-only breaches (19 H1, 38 H2a), PRIN is within `4.7e-14` of the exact map, with no breach, and the reference is outside the registered tolerance. The reference is the erroneous side in 57/57. All five SymPy lemmas hold. |

In both decomposition files `git_head` is the checkout the script ran from
(`34e8811`, which supplied the script, the gates, and the PRINet 3.0 reference).
The PRIN build under test is identified by `prin_package` / `prin_extension`:
`C:\dev\PRIN-prefix\…` is the `bd737e1` worktree build, and `C:\dev\PRIN\…` is
the post-fix build.

Mechanism attribution over H2a's 103 breaches, identical at both builds:
DV-007 alone 38; guard alone 33; DV-007 + guard 10; DV-007 + guard +
ill-conditioned 19; guard + ill-conditioned 3; unexplained **0**. Every H1
breach is DV-007 alone. All 33 H2a breaches at or above `1e-3` (by the E3
artefact's own magnitudes) are guard-sensitive.
