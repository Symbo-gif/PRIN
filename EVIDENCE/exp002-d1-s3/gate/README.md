# Closing gate evidence

The local gate under Plan amendment #48 (hosted checks are disabled; this is not a
CI result, and Linux and macOS were not tested). Instruments are in the parent
directory ([`../README.md`](../README.md)). The long legs ran on a clean tree at
commit `248bb586` (tracked changes 0, untracked files 0 before and after), strictly
one after another, with the out-of-process sampler watching each pytest run and
**no** diagnostic plugin, so the shipped per-notebook bounds applied.

| Leg | Result | Record |
|---|---|---|
| Required fast suite `pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20` | **exit 0**: `4044 passed, 178 skipped, 55 deselected, 59 warnings in 3225.14 s (0:53:45)`. A clean single pass. (S2: 4038 passed; the 6 additional tests are S3's: 5 notebook-bound tests and 1 fig13-label test.) | [`fast-suite/`](fast-suite/run.txt) |
| Required full suite `pytest tests/ parity/ --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20`, first run | **exit 1**: `1 failed, 6330 passed, 184 skipped, 61 warnings in 7517.90 s (2:05:17)`. The one failure is `tests/test_exp002_driver.py::TestCheckRunComplete::test_wrong_parent_rejected`: `PermissionError: [WinError 5] Access is denied` on a `rename` inside `.pytest_basetemp`, the Windows file-handle contention class `AGENTS.md` documents (S1 recorded two of the same). **All four notebook legs passed inside their shipped bounds**: notebook 02 took 1,636.2 s (limit 10,800 s; it was killed at 900 s in S1 and S2), 01 took 562.2 s, 03 took 176.6 s (04 is not among the 20 slowest tests). | [`full-suite-1/`](full-suite-1/run.txt), [`analysis-full-suite-1-notebooks.txt`](analysis-full-suite-1-notebooks.txt), [`analysis-full-suite-1-timeline.txt`](analysis-full-suite-1-timeline.txt) |
| The failed node, and its whole file, re-run in isolation | node: `1 passed in 2.34 s`; `tests/test_exp002_driver.py`: `323 passed in 21.74 s`. Supplementary evidence only (`AGENTS.md`; S1 precedent): the full-suite record above stays at exit 1. | [`isolated-rerun.txt`](isolated-rerun.txt) |
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
| [`isolated-rerun.txt`](isolated-rerun.txt) | The isolated re-runs of the failed node and its file. |

The console logs are saved as `.txt` because the repository ignores `*.log`.
