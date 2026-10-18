# `gate/dv032-fix/` — the `EXP002D1-S4-F3` fix and its evidence

Implements DV-032's registered fix path for
`tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression`,
which turned the required full-suite leg red at `814b670c`
(`Throughput ratio 22.07 > 1.30`). Committed as `67100a69`. Narrative record:
audit §S4.14; ledger row `EXP002D1-S4-F3` in `DOCS/reports/041-project-state.md`;
the red leg itself is in [`../red-leg-814b670c/`](../red-leg-814b670c/).

## Why the assertion could not be repaired by choosing a better clock

`metric-probe.txt` compares **four** candidate metrics — the current blocked
wall-clock design, an interleaved paired wall-clock design, `time.process_time()`
and `time.thread_time()` — under a quiet host and under a host saturated with one
busy process per logical CPU, each against a normal daemon and against a
deliberately CPU-hogging daemon.

**No metric detected the hog**, and `process` and `thread` returned *identical*
values (1.000 quiet, 1.143 loaded) for both arms. Rather than accept that, the
control was checked for engagement — the same class of error as the earlier
`negctl.py` `PYTHONPATH` defect, where a control measured nothing and falsely
reported success. `verify_negctl.py` confirmed the daemon **had** engaged
(200/200 inferences, 0 errors, session initialised) and measured why the signal
was absent:

| quantity | measured |
|---|---|
| one daemon inference | **1.491 ms** |
| `_dummy_work(n=1_000_000)` | **60.13 ms** |
| inferences inside the test's real window | **3** |
| that window | **419.7 ms** |
| maximum expressible effect | **~1.1 %** |
| the allowance it was compared against | **30 %** |

The signal sat **~27x below its own tolerance**. The assertion could not detect
daemon overhead at *any* tolerance; it only ever detected host noise. So the fix
had to change **what is measured**, not how it is timed.

## Sizing the bound

`tolerance-probe.txt` measures the cpu-ratio and wall-ratio distributions, 8
repetitions each, quiet and saturated. Normal-daemon cpu-ratio: **1.03 quiet,
1.02 saturated** — essentially load-invariant, against 22.07 / 2.13 / 3.42 for the
old wall-clock metric under the same saturation. Worst observed **1.1429**, which
is what `_DAEMON_CPU_RATIO_LIMIT = 1.60` is sized from (Testing Standards §7 item
2), not the 1.30 it replaces.

That probe also shows the ratios **quantising** to 0.8000 / 0.8750 / 1.1429 —
ratios of small integers — because the ~15.6 ms Windows process-time tick is
coarse against a ~60 ms sample, where one tick moves the ratio ~25 %. Hence the
sample grew to `n=8_000_000` (~480 ms), where a tick moves it ~3 %. This
**lengthens** a sample; §7 item 6 forbids shortening one.

`bound-probe-partial.txt` is **incomplete and kept as-is**: its loaded arm never
returned. The drain waited for a target *inference count*, but `submit_state`
drops the oldest state when the queue is full, so the target was unreachable and
each repetition spun to its cap. That flaw is what produced the corrected drain in
the test — wait on every submitted state being *handled*
(`inference_count + error_count`), not on the queue reading empty. The quiet arm's
data (daemon CPU 1.5625–2.6562 ms per inference, 500 inferences, 0 errors) is
valid and is the only content the file carries.

## Verification, in both directions

`verify/summary.txt` is the corrected run; `verify-first-attempt/` is the
superseded one, kept because it is the record of a real defect.

| check | result |
|---|---|
| `ruff check` / `ruff format --check` on the changed file | **rc=0** both |
| quiet host, 3 runs | **3 passed** (12.4–13.0 s) |
| **saturated host (100 % CPU), 3 runs** | **3 passed** (24.2–25.5 s) |
| negative control — CPU-hogging daemon | **FAILED as required**: `ratio 2.03 > 1.6` |
| negative control — erroring daemon | **FAILED as required**: `daemon reported 3 inference errors` |
| whole changed file | **49 passed** |

**The first attempt is retained because it failed in an instructive way.** Its
`negctl-cpu` case failed on `daemon completed 2 inferences, want >= 3` — the
**wrong** assertion. The emptiness-based drain read `inference_count` mid-flight,
because the queue is empty once the daemon *dequeues* an item and before it
*finishes inferring* it. Had that been accepted, the ratio's non-vacuity would have
gone unproven while the control appeared to pass.

`sensitivity/run1-harness-defect.txt` is likewise retained: its `report` mode
returned rc=0 with no ratio, exposing that `import tests.test_acceptance_subconscious`
binds a **different module object** than the one pytest collects — `tests/` has no
`__init__.py`, so under prepend import mode the collected module is top-level.
Patched via `item.module` in `pytest_runtest_setup`. This is the **same trap** as
the `parity/` plugin defect earlier in this cycle, recurring in a fresh harness.

## Residual limitation, measured rather than claimed away

`sensitivity/run2-corrected.txt` forced the assertion to report its ratio in both
conditions:

| condition | normal daemon | with a 3.0 s-per-inference CPU hog | bound | fires? |
|---|---|---|---|---|
| quiet | **1.03** | **2.00** | 1.60 | **yes** |
| saturated (100 %) | **1.02** | **1.02** | 1.60 | **no** |

Under saturation a single in-process hog is itself starved, so it accumulates
almost no process CPU and the bound does not fire. The ratio is therefore a
**gross-regression detector**; the **deterministic assertions** (`error_count`,
`dlq_size`, `inference_count`) are what retain full sensitivity under load, and
they are load-invariant. This matches DV-032's own disposition, which assigns the
sensitive quantitative comparison to the nightly benchmark gate. It is recorded
here so the bound is never later credited with sensitivity it was measured not to
have.

## Harness files

`dv032negctl.py` is the pytest plugin driving the controls. It is kept **outside**
the repository at run time and loaded with `-p dv032negctl` (`PYTHONPATH` set to a
Windows-style path, because an MSYS `/c/...` path is invisible to native Windows
Python — the defect that silently voided an earlier control). `verify_negctl.py`
is the engagement check described above.
