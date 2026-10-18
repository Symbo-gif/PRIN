# `gate/dv032-fix/` — file index

Every file in this directory, for `index_selfcheck.py`. The narrative record is
[`FIX.md`](FIX.md); the instruments that produced these outputs live one level up
in [`../`](../) (`dv032-fix-probe.py`, `dv032-bound-probe.py`,
`dv032-tolerance-probe.py`, `verify-dv032-fix.sh`,
`measure-ratio-sensitivity.sh`, `collect_dv032_fix.sh`).

## Narrative and harness

| File | What it is |
|---|---|
| [`FIX.md`](FIX.md) | **The fix record.** Why no choice of clock could rescue the assertion, the measured ~1.1 %-signal-vs-30 %-tolerance finding, how the 1.60 bound was sized, the verification table, the residual limitation, and the two harness defects found and corrected. |
| [`dv032negctl.py`](dv032negctl.py) | The pytest plugin driving the negative controls (`cpu`, `errors`, `report`, `cpu-report`). Kept **outside** the repository at run time and loaded with `-p dv032negctl`; patches the ratio limit via `item.module`, because `tests/` has no `__init__.py` and a `tests.*` import binds a different module object than the one pytest collects. |
| [`verify_negctl.py`](verify_negctl.py) | The **engagement check** for the metric probe's negative control: proves the daemon actually ran (200/200 inferences, 0 errors, session initialised) and measures the per-inference and per-window costs that show the signal was ~27x below tolerance. |

## Probes that shaped the fix

| File | What it is |
|---|---|
| [`metric-probe.txt`](metric-probe.txt) | Four candidate metrics (blocked wall, paired wall, `process_time`, `thread_time`) × two host conditions × two daemon arms. **No metric detected the hog** — the finding that forced a change of *what* is measured rather than *how* it is timed. |
| [`tolerance-probe.txt`](tolerance-probe.txt) | 8 repetitions each, quiet and saturated, of the cpu-ratio and wall-ratio in the exact shape the replacement test uses. Normal-daemon cpu-ratio **1.03 quiet / 1.02 saturated**; worst observed **1.1429**, which sizes the 1.60 bound. Also shows the quantisation (0.8000 / 0.8750 / 1.1429) that forced the larger sample. |
| [`bound-probe-partial.txt`](bound-probe-partial.txt) | **Incomplete, and kept as-is.** The loaded arm never returned because the drain awaited a target *inference count* that dropped states made unreachable. Its quiet arm is valid (daemon CPU 1.5625–2.6562 ms per inference, 500 inferences, 0 errors) and its flaw is what produced the corrected drain in the test. |

## Verification — corrected run

| File | What it is |
|---|---|
| [`verify/summary.txt`](verify/summary.txt) | **The authoritative verification record**: static checks rc=0; quiet 3/3 passed; **saturated 3/3 passed**; CPU-hog control **failed as required** (`ratio 2.03 > 1.6`); error control **failed as required** (`daemon reported 3 inference errors`); `loaded-negctl-cpu` MISMATCH, which is the residual limitation measured in `sensitivity/`. |
| [`verify/ruff-check.txt`](verify/ruff-check.txt) · [`verify/ruff-format.txt`](verify/ruff-format.txt) | The static checks on the changed test file, both rc=0. |
| [`verify/quiet-1.txt`](verify/quiet-1.txt) · [`quiet-2.txt`](verify/quiet-2.txt) · [`quiet-3.txt`](verify/quiet-3.txt) | The three quiet-host runs of the fixed test. |
| [`verify/loaded-1.txt`](verify/loaded-1.txt) · [`loaded-2.txt`](verify/loaded-2.txt) · [`loaded-3.txt`](verify/loaded-3.txt) | The three runs under a host saturated with one busy process per logical CPU — the condition that broke the original. |
| [`verify/negctl-cpu.txt`](verify/negctl-cpu.txt) | The CPU-hog negative control, failing on the **ratio** assertion with `ratio 2.03 > 1.6`. |
| [`verify/negctl-errors.txt`](verify/negctl-errors.txt) | The erroring-daemon negative control, failing on the deterministic counts with `daemon reported 3 inference errors`. |
| [`verify/loaded-negctl-cpu.txt`](verify/loaded-negctl-cpu.txt) | The CPU-hog control **under saturation**, which passed — the measured residual limitation, not a passing result to be celebrated. |

## Verification — superseded first attempt

Retained because it is the record of a real defect in the fix, not a duplicate.

| File | What it is |
|---|---|
| [`verify-first-attempt/negctl-cpu.txt`](verify-first-attempt/negctl-cpu.txt) | **The instructive failure**: the CPU control failed on `daemon completed 2 inferences, want >= 3` — the *wrong* assertion — because the emptiness-based drain read `inference_count` mid-flight. Accepting it would have left the ratio's non-vacuity unproven while appearing to pass. |
| [`verify-first-attempt/ruff-check.txt`](verify-first-attempt/ruff-check.txt) · [`verify-first-attempt/ruff-format.txt`](verify-first-attempt/ruff-format.txt) | The first attempt's static checks, **both rc=1** — an `RUF002` EN DASH and a format deviation, fixed before the corrected run. |
| [`verify-first-attempt/quiet-1.txt`](verify-first-attempt/quiet-1.txt) · [`quiet-2.txt`](verify-first-attempt/quiet-2.txt) · [`quiet-3.txt`](verify-first-attempt/quiet-3.txt) | The first attempt's quiet-host runs (all passed). |
| [`verify-first-attempt/loaded-1.txt`](verify-first-attempt/loaded-1.txt) · [`loaded-2.txt`](verify-first-attempt/loaded-2.txt) · [`loaded-3.txt`](verify-first-attempt/loaded-3.txt) | The first attempt's saturated-host runs (all passed). |
| [`verify-first-attempt/negctl-errors.txt`](verify-first-attempt/negctl-errors.txt) | The first attempt's error control (failed as required). |
| [`verify-first-attempt/loaded-negctl-cpu.txt`](verify-first-attempt/loaded-negctl-cpu.txt) | The first attempt's saturated CPU control (passed — same residual limitation). |

## Sensitivity of the ratio bound

| File | What it is |
|---|---|
| [`sensitivity/run1-harness-defect.txt`](sensitivity/run1-harness-defect.txt) | The **first** sensitivity run, retained because it exposed the module-patching defect: `report` mode returned rc=0 with no ratio, proving `mod._DAEMON_CPU_RATIO_LIMIT = 0.0` never took effect. |
| [`sensitivity/run2-corrected.txt`](sensitivity/run2-corrected.txt) | The **corrected** run: normal daemon **1.03 quiet / 1.02 saturated**; with the CPU hog **2.00 quiet** but **1.02 saturated** — the bound fires only when the host is not saturated. |
| [`sensitivity-runs/quiet-report.txt`](sensitivity-runs/quiet-report.txt) | Per-run pytest record, quiet host, normal daemon, limit forced to 0.0 to reveal the ratio. |
| [`sensitivity-runs/quiet-cpu-report.txt`](sensitivity-runs/quiet-cpu-report.txt) | Per-run pytest record, quiet host, CPU hog, ratio revealed. |
| [`sensitivity-runs/loaded-report.txt`](sensitivity-runs/loaded-report.txt) | Per-run pytest record, saturated host, normal daemon, ratio revealed. |
| [`sensitivity-runs/loaded-cpu-report.txt`](sensitivity-runs/loaded-cpu-report.txt) | Per-run pytest record, saturated host, CPU hog, ratio revealed. |
