# Closing gate evidence

The local gate under Plan amendment #48 (hosted checks are disabled; this is not a
CI result, and Linux and macOS were not tested). Instruments are in the parent
directory ([`../README.md`](../README.md)). The long legs ran on a clean tree at
commit `248bb586` (tracked changes 0, untracked files 0 before and after), strictly
one after another, with the out-of-process sampler watching each pytest run and
**no** diagnostic plugin, so the shipped per-notebook bounds applied. The full suite
was then run a second time on `76a97384`, which differs from `248bb586` only by
evidence files.

| Leg | Result | Record |
|---|---|---|
| Required fast suite `pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20` | **exit 0**: `4044 passed, 178 skipped, 55 deselected, 59 warnings in 3225.14 s (0:53:45)`. A clean single pass. (S2: 4038 passed; the 6 additional tests are S3's: 5 notebook-bound tests and 1 fig13-label test.) | [`fast-suite/`](fast-suite/run.txt) |
| Required full suite `pytest tests/ parity/ --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20`, first run | **exit 1**: `1 failed, 6330 passed, 184 skipped, 61 warnings in 7517.90 s (2:05:17)`. The one failure is `tests/test_exp002_driver.py::TestCheckRunComplete::test_wrong_parent_rejected`: `PermissionError: [WinError 5] Access is denied` on a `rename` inside `.pytest_basetemp`, the Windows file-handle contention class `AGENTS.md` documents (S1 recorded two of the same). **All four notebook legs passed inside their shipped bounds**: notebook 02 took 1,636.2 s (limit 10,800 s; it was killed at 900 s in S1 and S2), 01 took 562.2 s, 03 took 176.6 s (04 is not among the 20 slowest tests). | [`full-suite-1/`](full-suite-1/run.txt), [`analysis-full-suite-1-notebooks.txt`](analysis-full-suite-1-notebooks.txt), [`analysis-full-suite-1-timeline.txt`](analysis-full-suite-1-timeline.txt) |
| Required full suite, **second run** (`76a97384`) | **exit 1**: `1 failed, 6330 passed, 184 skipped, 61 warnings in 5117.76 s (1:25:17)`. A **different** single failure: `tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression`, `Throughput ratio 2.18 > 1.30`. That node is registered in **DV-032** as host-timing-sensitive (a wall-clock ratio that "measures ~1.28–1.32 under load" there), and in this run the host was saturated by non-PRIN processes from 12:39Z to 13:48Z (55 of 90 samples at or above 95% CPU while pytest received a median 0.02 CPU-s/s). **All four notebook legs passed inside their shipped bounds**: 02 took 1,326.5 s, 01 took 647.9 s, 03 took 49.2 s and 04 took 41.2 s (the contention eased during notebook 02, so 03 and 04 ran at 1.1× their standalone time). | [`full-suite-2/`](full-suite-2/run.txt), [`analysis-full-suite-2-notebooks.txt`](analysis-full-suite-2-notebooks.txt), [`analysis-full-suite-2-timeline.txt`](analysis-full-suite-2-timeline.txt) |
| Each run's one failed node, and its whole file, re-run in isolation | run 1: `test_wrong_parent_rejected` `1 passed in 2.34 s`; `tests/test_exp002_driver.py` `323 passed in 21.74 s`. Run 2: `test_no_gpu_throughput_regression` `1 passed in 9.75 s`; `tests/test_acceptance_subconscious.py` `49 passed in 14.60 s`. Supplementary evidence only (`AGENTS.md`; S1 precedent): both full-suite records stay at exit 1. | [`isolated-rerun.txt`](isolated-rerun.txt) |

**Reading the two full-suite results.** Neither required full-suite run exited 0,
and each failed on a *different* single node that is unrelated to this change, is
host-contention sensitive, and passes alone: a file-handle `WinError 5` (the class
`AGENTS.md` documents) and a wall-clock throughput ratio (DV-032). The F2 node is
not among them: its four notebook legs finished inside the new bounds in both runs
and in the earlier diagnostic run (`../f2/`). The suite as a whole is therefore
flaky on this host while the maintainer's IDE and security tooling are active, in
more than the one way F2 named. S3 did not run it a third time hoping for a clean
pass, which would select a favourable outcome rather than report one; the facts are
recorded, and S4 and the maintainer decide whether the gate should be run with that
tooling quiet.
| Targeted path-form coverage (`--cov=python/prin/reporting`; the module form fails on this host, DV-033) and the changed-line analysis | `figure_generation.py` **99.41%** (340 statements, missed lines 201 and 206, the untouched malformed-PNG branches, shifted from 191 and 196 by S3's ten added docstring lines). Against the cycle base `fd8854ed`: **11 of 11** changed executable lines executed (100.00%). Against the S3 base `5ba0129e`: 15 lines changed and **0 are executable statements** (docstring lines and one keyword-argument line inside the executed `ax.scatter(...)` statement), so that 100.00% is **vacuous**; the line itself is exercised by the fig13-label test. | [`closing-gate-legs.txt`](closing-gate-legs.txt) |
| `cargo fmt --all -- --check`; `cargo clippy --workspace --all-targets -- -D warnings`; `cargo test --workspace` | all **exit 0**; `cargo test` on the first attempt (no contention retry needed): 48 `test result: ok` lines summing to 1,604 passed and 0 failed. | [`closing-gate-legs.txt`](closing-gate-legs.txt) |
| Sphinx `-W --keep-going -b html` from a deleted `DOCS/sphinx/_build` | **exit 0**, `build succeeded`. | [`closing-gate-legs.txt`](closing-gate-legs.txt) |
| `gitleaks` (pinned binary 8.30.1), full history and `--staged` | **exit 0** each: 758 commits scanned, no leaks; nothing staged. | [`closing-gate-legs.txt`](closing-gate-legs.txt) |

## Files

| File | What it is |
|---|---|
| [`closing-gate-legs.txt`](closing-gate-legs.txt) | `closing_gate.sh`'s record of every non-pytest leg and the two suites' exit statuses, each with its verbatim command, UTC times and exit code. |
| [`fast-suite/run.txt`](fast-suite/run.txt), [`fast-suite/console.txt`](fast-suite/console.txt), [`fast-suite/samples.jsonl`](fast-suite/samples.jsonl) | The fast suite's header and footer, timestamped console output (including `--durations=20` and the summary), and the sampler's output. |
| [`full-suite-1/run.txt`](full-suite-1/run.txt), [`full-suite-1/console.txt`](full-suite-1/console.txt), [`full-suite-1/samples.jsonl`](full-suite-1/samples.jsonl) | The same for the full suite's first run. The console log keeps the failure's traceback. |
| [`analysis-full-suite-1-notebooks.txt`](analysis-full-suite-1-notebooks.txt) | `f2_in_suite_vs_alone.py` on that run: the notebook durations beside the standalone, S1 and S2 values. |
| [`analysis-full-suite-1-timeline.txt`](analysis-full-suite-1-timeline.txt) | `suite_sampler.py --timeline` and `--summarize` on that run's samples. |
| [`full-suite-2/run.txt`](full-suite-2/run.txt), [`full-suite-2/console.txt`](full-suite-2/console.txt), [`full-suite-2/samples.jsonl`](full-suite-2/samples.jsonl) | The same for the full suite's second run. |
| [`analysis-full-suite-2-notebooks.txt`](analysis-full-suite-2-notebooks.txt), [`analysis-full-suite-2-timeline.txt`](analysis-full-suite-2-timeline.txt) | The comparison and the host-versus-pytest timeline for that run. |
| [`isolated-rerun.txt`](isolated-rerun.txt) | The isolated re-runs of each run's failed node and its file. |

The console logs are saved as `.txt` because the repository ignores `*.log`.
