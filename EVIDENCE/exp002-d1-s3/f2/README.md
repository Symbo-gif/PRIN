# F2 evidence — the notebook leg of the full suite

Finding `EXP002D1-S2-F2` (D2): `pytest tests/ parity/` exited 1 because
`test_notebook_executes_end_to_end[02_clevr_n_binding.ipynb]` exceeded the 900 s
per-cell bound, in two consecutive sessions. This directory is the measurement
behind S3's disposition (route (a): re-size the bound from cited evidence).
Instruments are in the parent directory
([`../README.md`](../README.md)); every output here was produced by one of them.

## What the evidence shows

**1. The notebook is not slow.** Run alone on a quiet host, no pytest, the four
notebooks complete in **73 / 71 / 45 / 37 s** (`alone-*.json`). Notebooks 01, 03
and 04 are single-threaded (kernel CPU/wall 0.89–1.13). Notebook 02 does 435
CPU-seconds of work across about six cores with a 3.2 GB working set.

**2. Inside the full suite the same notebooks take 8–42× longer.** The observed
run (`diagnostic-full-suite/`: clean tree at `2f796ddf`, 2026-10-16
03:20:04Z → 06:03:32Z, the required `tests/ parity/` invocation with the notebook
per-cell timeout lifted by the diagnostic plugin so nothing was killed) finished
with exit 0, `6326 passed, 184 skipped` in 2 h 42 m. Its `--durations` lines give
the first *uncensored* in-suite durations:
[`analysis-in-suite-vs-alone.txt`](analysis-in-suite-vs-alone.txt).

| notebook | alone | S1 in-suite | S2 in-suite | S3 observed | S3 / alone |
|---|---|---|---|---|---|
| 01_oscillosim_quickstart | 73.3 s | 639.6 s | 800.1 s | 678.9 s | 9.3× |
| 02_clevr_n_binding | 71.1 s | ≥ 1052.8 s (killed) | ≥ 1064.0 s (killed) | **2975.0 s** | **41.8×** |
| 03_custom_coupling | 44.5 s | 409.0 s | 222.4 s | 367.3 s | 8.3× |
| 04_torch_bridge | 37.0 s | 389.8 s | 52.5 s | 382.1 s | 10.3× |

**3. The cause is CPU starvation by processes outside PRIN, not memory and not the
notebook.** [`analysis-observed-run-timeline.txt`](analysis-observed-run-timeline.txt)
puts the host's CPU next to the CPU seconds per second that pytest received:

- from 03:21Z to 03:32:55Z pytest received a median of **2.8 CPU-s/s** (range
  0.8–4.7) while the host varied between 15% and 89% CPU;
- from 03:35Z, when the first `tests/test_exp002_*` tests have started (the host
  first reads 93.5% at 03:33:47Z), **all 102 samples to 06:00Z show the host at
  98–100%** and pytest receiving a median of **0.01 CPU-s/s** (maximum 0.23), a
  drop of about 280×, for 2 h 27 m;
- the CPU is used by `System`, `mc-fw-host.exe`, `Devin.exe` and `svchost.exe`
  throughout, and from 03:44Z (in the top three from 03:56Z) also by `rg.exe`: at 04:37Z **134 concurrent
  `rg.exe --files --hidden --case-sensitive --no-require-git …` processes, all
  children of one `Devin.exe` Node utility process, with 37 distinct `-g` patterns
  (`PLAN.md`, `.cursorrules`, `ARCHITECTURE.md`, `AGENT.md`, …) and 2,093
  cumulative CPU-seconds** ([`rg-storm-snapshot-during-suite.txt`](rg-storm-snapshot-during-suite.txt));
- during the notebook kernels ([`analysis-observed-run-kernels.txt`](analysis-observed-run-kernels.txt))
  the kernel received **0.17–0.33 CPU-s per wall-second**, `rg.exe` alone used
  202–8,799 CPU-seconds in the same windows, host available memory never fell
  below **5.5 GB**, and hard-fault paging averaged **at most 26 pages/s**: not
  memory pressure;
- when pytest exited, the host fell from 100% to 33% within about a minute and
  `rg.exe` processes fell from 116 to 2.

**4. A smaller group reproduces it.** `contention_experiment.sh` measured one
notebook twice, changing only the company it kept
([`analysis-paired-comparison.txt`](analysis-paired-comparison.txt)):

| | wall | kernel CPU | CPU / wall | host CPU |
|---|---|---|---|---|
| control: notebook 02 alone, quiet host | 80.7 s | 465.7 s | 5.77 | 73.5% |
| treatment: notebook 02 while only `tests/test_exp002_driver.py` and `tests/test_exp002_e4_analysis.py` run | **3484.0 s (43.2×)** | 1116.9 s (2.4×) | 0.32 | 99.9% |

The training cell alone went from 35.7 s to 1,926 s (54×). The 499-test load
generator ran 30 m 37 s, and the host stayed at ~100% with 87 → 29 → 64 `rg.exe`
processes for more than 28 minutes after it had exited
([`analysis-contention-timeline.txt`](analysis-contention-timeline.txt)).

## What is measured and what is not

- **Measured:** the notebook's standalone cost; its in-suite and beside-the-exp002-tests
  durations; the CPU share it received; which processes were using the CPU; that
  memory and paging were not limiting; that the saturation began when the
  `test_exp002_*` group started in both the observed run and the experiment, and
  that the experiment's slowdown (43×) exceeds the full-suite's (42×).
- **Not established:** what starts the `rg.exe` scans or why `System` and
  `mc-fw-host.exe` are busy. The timing says the file-heavy `test_exp002_*` tests
  trigger them (workspace changes under the in-repository `.pytest_basetemp`, 37,591
  files at the time of the snapshot), but no process was stopped to test that, and
  nothing here proves the IDE's scans, rather than another process, are what
  starve the kernel. These are the maintainer's processes and were observed, not
  killed. Why the contention drained within a minute of the end of the full suite
  but persisted for over 28 minutes after the experiment's load generator exited
  is not explained either.
- **Not PRIN code.** Nothing in the notebooks, the library or the tests is
  implicated by this evidence.

## Disposition (route (a))

Testing Standards §7 item 2 sizes a finite bound from cited completed evidence for
that workload plus substantial margin for host variability. The shipped 900 s bound
was sized from the notebooks' stated ~40 s budget and is below every contended
duration recorded. `tests/test_notebooks.py` now carries a per-notebook bound of
**3 × the largest completed contended duration, rounded up to a multiple of 900 s**:

| notebook | largest completed contended duration | bound |
|---|---|---|
| 01_oscillosim_quickstart | 800.07 s (S2, full suite) | 2,700 s |
| 02_clevr_n_binding | 3,484.0 s (S3 experiment) | 10,800 s |
| 03_custom_coupling | 408.96 s (S1, full suite) | 1,800 s |
| 04_torch_bridge | 389.81 s (S1, full suite) | 1,800 s |

No test was deselected, skipped, xfailed or shortened, and no assertion changed;
the execution test still fails on any cell error output or timeout. The bound is
now a ceiling for a leg that is starved but progressing, not a performance check
(the quiet-host durations are 37–73 s). Two new fast tests pin the relationship
so a bound cannot be lowered, or a slower worst case recorded, without the other
moving: [`test-red-before-fix.txt`](test-red-before-fix.txt) (4 failed with the old
900 s bounds) and [`test-green-after-fix.txt`](test-green-after-fix.txt)
(33 passed, 4 slow executing tests still collected).

## Files

The runner writes the console output as `console.log` under `~/prin-s3-scratch/`; the copies kept here are named `console.txt` because the repository ignores `*.log`.

| File | What it is |
|---|---|
| [`alone-01_oscillosim_quickstart.json`](alone-01_oscillosim_quickstart.json), [`alone-02_clevr_n_binding.json`](alone-02_clevr_n_binding.json), [`alone-03_custom_coupling.json`](alone-03_custom_coupling.json), [`alone-04_torch_bridge.json`](alone-04_torch_bridge.json) | Standalone baseline: `notebook_timing.py` on each notebook, one after another, quiet host, no pytest. |
| [`diagnostic-full-suite/run.txt`](diagnostic-full-suite/run.txt) | The observed run's header and footer: git HEAD `2f796ddf`, 0 tracked changes and 0 untracked files before and after, plugin loaded, pytest args, start/end UTC, exit status 0. |
| [`diagnostic-full-suite/console.txt`](diagnostic-full-suite/console.txt) | The full pytest console output with a UTC timestamp on every line, including the `--durations` table and the final summary. |
| [`diagnostic-full-suite/samples.jsonl`](diagnostic-full-suite/samples.jsonl) | The sampler's 132 samples (30 s cadence). |
| [`rg-storm-snapshot-during-suite.txt`](rg-storm-snapshot-during-suite.txt) | A read-only snapshot of the 134 `rg.exe` processes at 04:37Z: parent, count, cumulative CPU, `-g` patterns. Nothing was stopped. Its console-tail field is empty (a harmless slice error in the snapshot command). |
| [`contention-experiment/run.txt`](contention-experiment/run.txt), [`contention-experiment/control.json`](contention-experiment/control.json), [`contention-experiment/treatment.json`](contention-experiment/treatment.json) | The paired experiment's log and the two `notebook_timing.py` records. |
| [`contention-experiment/load/run.txt`](contention-experiment/load/run.txt), [`contention-experiment/load/console.txt`](contention-experiment/load/console.txt), [`contention-experiment/load/samples.jsonl`](contention-experiment/load/samples.jsonl) | The load generator's header/footer (499 passed in 30:37), console log and sampler output. |
| [`analysis-in-suite-vs-alone.txt`](analysis-in-suite-vs-alone.txt) | `f2_in_suite_vs_alone.py` on the observed console log: the table above. |
| [`analysis-observed-run-kernels.txt`](analysis-observed-run-kernels.txt) | `suite_sampler.py --summarize` on the observed samples: one row per notebook kernel. |
| [`analysis-observed-run-timeline.txt`](analysis-observed-run-timeline.txt) | `suite_sampler.py --timeline` on the observed samples: the host-versus-pytest table. |
| [`analysis-paired-comparison.txt`](analysis-paired-comparison.txt) | `paired_comparison.py`: control versus treatment. |
| [`analysis-contention-timeline.txt`](analysis-contention-timeline.txt) | `suite_sampler.py --timeline` and `--summarize` on the load generator's samples. |
| [`test-red-before-fix.txt`](test-red-before-fix.txt), [`test-green-after-fix.txt`](test-green-after-fix.txt) | The new bound tests failing against the old bounds, and passing after. |
