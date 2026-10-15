Pre-registration freeze: **`9a9889d08dcaf2ad0ce31659ed67721b54b114d0`** - the git SHA of the last `preregistration.md` edit, recorded at the creation of the first `RUN-` directory (2026-10-12T21:27:05Z; campaign plan section 12.4); the pre-registration is frozen from that point. (Line added at session 0162 as an erratum.)

# EXP-002 — E3 execution log (session 0161)

**Append-only.** An entry is never edited after it is written; a mistake is
repaired by a dated, labelled correction entry further down. This file is exempt
from the driver's clean-checkout check (protocol §5.5). It records observations
and procedure only. **No hypothesis verdict is computed, stated or implied in
this log** — E3 is execution; H1–H4 are adjudicated at E4 (session 0162).

- **Operator of record:** MichaelMaillet (the `--operator` value on every leg, as instructed).
- **Commands issued by:** Claude Sonnet 5.5 (AI pair), at the maintainer's direction,
  in the maintainer's Claude Code session on the maintainer's Windows host.
- **Session / stage:** 0161 — EXP-002 / C1, E3 (Execution). Predecessor 0160 (E2), successor 0162 (E4).
- **Branch / PR:** `campaign/0159-exp002-e1` / PR #33.
- **Protocol:** [`preregistration.md`](preregistration.md), `APPROVED` 2026-10-12 UTC
  (E2, session 0160). Frozen at the first `RUN-` creation (leg 1 below).
- **Regime:** Plan amendment #48 local-validation regime (hosted CI paused; Linux/macOS not tested),
  with amendment #50's EXP-002 hosted-check window. Hosted results below are additional evidence only;
  the Windows local gate stays authoritative. Nothing here claims Linux/macOS behaviour.

## 1. Recorded identities

| Symbol | Value |
|---|---|
| `R` — execution source for all five legs | `fae24c4393c7a0232e6c8f0a6388b1775aa5fc05` (`R7` = `fae24c4`) |
| `F` — last protocol commit at first `RUN-` creation | `9a9889d08dcaf2ad0ce31659ed67721b54b114d0` (E2 approval commit) |
| Protocol SHA-256 (blob at `F`, byte-identical at `R`) | `0f3073dd2ed73b64071bcf3ae182510a69a26bd575b81b5a97cc5a1f9bbc8c8b` |
| Approval line | `MichaelMaillet, 2026-10-12 UTC` (`approval_date_utc` = `2026-10-12`) |
| Input manifest `paper/artefact_manifest.json` SHA-256 | `300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5` (172 records) |
| Seed pair `(counter, key)` | `(0, 2)` on every leg |
| Raw record root | `benchmarks/results/EXP-002/` |
| Generated-output root (gitignored; retained unmodified until E5 is accepted — E2 decision 8) | `DOCS/test_and_benchmark_results/EXP-002/<run-id>/` |

**`R` against the approval commit `9a9889d`.** `R` is a descendant of `9a9889d`
(`git merge-base --is-ancestor 9a9889d HEAD` → exit 0) and differs from it by
exactly one commit, `fae24c4` (`docs(0160): record hosted results for 9a9889d and
disposition the nightly`), touching 8 files (`git diff --name-status 9a9889d fae24c4`):

| Status | Path | Nature |
|---|---|---|
| M | `DOCS/experiments/EXP-002-…/e2-review.md` | document (+25 lines: §6 hosted results and nightly disposition) |
| M | `EVIDENCE/0160/README.md` | evidence index |
| M | `EVIDENCE/0160/verification/SHA256SUMS.txt` | evidence manifest (+4 lines) |
| A | `EVIDENCE/0160/verification/ci-fixes/H2-forced-nightly-38238913518.json` | evidence |
| A | `EVIDENCE/0160/verification/ci-fixes/H2a-…-attempt1-bench-regression.log` | evidence |
| A | `EVIDENCE/0160/verification/ci-fixes/H2b-…-attempt2-bench-regression.log` | evidence |
| A | `EVIDENCE/0160/verification/ci-fixes/H3-hosted-runs-9a9889d.json` | evidence |
| M | `tests/test_0160_manifest.py` | **+4 lines**: adds the four new evidence file names to that test's `REQUIRED_BUNDLE` completeness list |

No file under `python/`, `crates/`, `benchmarks/`, `tools/`, `paper/`, `parity/`,
the driver, the protocol or any registered input differs between `9a9889d` and `R`.
The only Python file touched is the 0160 evidence-manifest test, whose change only
lists the evidence files shipped in the same commit. I classified this as
documents/evidence-only bookkeeping, so the nightly disposition of e2-review.md §6
applies to `R` (checklist item 3). The report to the maintainer repeats this
classification so it can be overruled.

## 2. Pre-flight (read-only; no `RUN-` directory exists or was created)

Pre-flight began 2026-10-12T21:15:34Z. All commands ran from `C:\dev\PRIN`.

### 2.1 Source state

| Check | Command | Result |
|---|---|---|
| HEAD | `git rev-parse HEAD` | `fae24c4393c7a0232e6c8f0a6388b1775aa5fc05` = expected `R` |
| Branch | `git branch --show-current` | `campaign/0159-exp002-e1`; equal to `origin/campaign/0159-exp002-e1` |
| Tracked/untracked state | `git status --porcelain` | empty, exit 0 |
| Untracked non-ignored | `git ls-files --others --exclude-standard` | empty, exit 0 |
| Untracked top-level `*.py`/`*.pth` (ignored or not) | `git ls-files --others -- ":(glob)*.py" ":(glob)*.pth"` | empty, exit 0 |
| Shallow clone? | `Test-Path .git\shallow` | `False` (full history) |
| Pre-existing run directories | listing of `benchmarks/results/EXP-002/` | only `README.md` (1,774 bytes); no `RUN-*` |
| Pre-existing generated outputs | `DOCS/test_and_benchmark_results/EXP-002` | does not exist |
| Campaign tracked-storage baseline | `benchmarks/results/EXP-*` | 38 files, 13,416,905 bytes (12.795 MiB) of the 64 MiB cap; EXP-002 raw root 1,774 bytes; EXP-002 record root 89,736 bytes before this log |

### 2.2 Hosted checks for `R` (amendment #50 window; protocol §11.3 item 3)

`gh run list -R Symbo-gif/PRIN --commit fae24c4393c7a0232e6c8f0a6388b1775aa5fc05` — all
seven runs are on branch `campaign/0159-exp002-e1`, head SHA `R`, attempt 1, `completed` /
`success`. Durations are `updatedAt − startedAt` (UTC, 2026-10-12); `updatedAt` is the API's
closest end-time field. They are not charged to the protocol §9 hosted cap (E2 decision 10).

| Run ID | Workflow | Event | Started | Updated (end) | Duration |
|---|---|---|---|---|---|
| 38260606024 | snyk | push | 14:07:24Z | 14:08:35Z | 1 m 11 s |
| 38260614029 | rust | pull_request | 14:07:27Z | 15:05:30Z | 58 m 03 s |
| 38260614031 | gpu | pull_request | 14:07:27Z | 14:49:41Z | 42 m 14 s |
| 38260614034 | repro | pull_request | 14:07:27Z | 14:12:03Z | 4 m 36 s |
| 38260614092 | snyk | pull_request | 14:07:27Z | 14:08:13Z | 46 s |
| 38260614099 | parity | pull_request | 14:07:27Z | 14:12:45Z | 5 m 18 s |
| 38260614101 | python | pull_request | 14:07:27Z | 14:22:38Z | 15 m 11 s |

No `nightly` run exists for `R`, and none was dispatched in this session.

**Forced nightly on the approval commit.** Run `38238913518` (`workflow_dispatch`, head SHA
`9a9889d08dcaf2ad0ce31659ed67721b54b114d0`, attempt 2, created 10:51:15Z): `full-suite`
success (10:51:20Z → 11:06:42Z, 15 m 22 s); `bench-regression` **failure** (attempt 2
12:27:38Z → 14:02:18Z, 94 m 40 s; failed in both attempts). It is **not green**. It is
dispositioned in [`e2-review.md`](e2-review.md) §6 as measurement variance (a different
smallest-size benchmark breached ~11 % in each attempt and stayed within threshold in the
other; no `prin-sim`/`prin-dynamics`/`prin-core` source changed between the green forced
nightly on `0d4278d` and `9a9889d`). That disposition applies to any E3 source differing
from `9a9889d` by documents/evidence only; §1 above records why `R` qualifies. Evidence:
`EVIDENCE/0160/verification/ci-fixes/H2*`, `H3*`.

### 2.3 Admission dry check (read-only; creates no `RUN-` directory)

```
.venv\Scripts\python -I -c "import sys,json; sys.path.insert(0, r'C:\dev\PRIN'); from benchmarks.campaign import exp002_driver as d; print(json.dumps(d._admission('fae24c4393c7a0232e6c8f0a6388b1775aa5fc05'), sort_keys=True))"
```

Output (exit 0):

```
{"approval_date_utc": "2026-10-12", "preregistration_commit": "9a9889d08dcaf2ad0ce31659ed67721b54b114d0", "preregistration_sha256": "0f3073dd2ed73b64071bcf3ae182510a69a26bd575b81b5a97cc5a1f9bbc8c8b", "source_sha": "fae24c4393c7a0232e6c8f0a6388b1775aa5fc05"}
```

Matches the expected values: approval date `2026-10-12`, protocol commit `9a9889d…`, protocol
SHA-256 `0f3073dd2ed73b64071bcf3ae182510a69a26bd575b81b5a97cc5a1f9bbc8c8b`.
`git status --porcelain` was empty again afterwards.

### 2.4 Host environment (operator record; the driver captures its own copy in every record)

| Item | Value |
|---|---|
| Machine | HP OMEN 16L Gaming Desktop TG03-0xxx |
| OS | Microsoft Windows 11 Home 10.0.26300 (build 26300), 64-bit; `platform.platform()` = `Windows-11-10.0.26300-SP0` |
| Local time zone | UTC−03:00 (Atlantic, daylight time); all times in this log are UTC |
| CPU | AMD Ryzen 7 8700F 8-Core Processor — 8 cores / 16 logical CPUs, 4,101 MHz max; `platform.processor()` = `AMD64 Family 25 Model 117 Stepping 2, AuthenticAMD`; `os.cpu_count()` = 16 |
| RAM | 31.6 GiB installed (32,355 MiB visible); 7,015 MiB free at pre-flight |
| Disk | `C:` 188.1 GiB free |
| Last boot | 2026-10-12 14:17:26 local (17:17:26Z) |
| Python | 3.14.0 (tags/v3.14.0:ebf955d, Oct 7 2025) [MSC v.1944 64 bit (AMD64)], `C:\dev\PRIN\.venv\Scripts\python.exe` |
| Rust | `rustc 1.99.0 (b940084d7 2026-09-28)`, `cargo 1.99.0 (5f94df478 2026-08-27)` |
| NumPy / Matplotlib / Pillow | 2.5.1 / 3.11.1 / 12.3.0 |
| Other relevant packages | prin-core 1.0.0rc1, fonttools 4.63.0, kiwisolver 1.5.0, contourpy 1.3.3, cycler 0.12.1, pyparsing 3.3.2, packaging 26.3, python-dateutil 2.9.0.post0, torch 2.11.0+cu128, maturin 1.14.1, pytest 9.1.1 |
| PRIN import origin | `prin.__file__` = `C:\dev\PRIN\python\prin\__init__.py`; `prin._prin_core.__file__` = `C:\dev\PRIN\python\prin\_prin_core.pyd`; `prin.__version__` = `1.0.0rc1`; `core_version()` = `1.0.0-rc1`; `len(prin.__all__)` = 175 (175 unique) |
| Reference import origin | `prinet` 3.0.0 is an editable install of the frozen reference tree (`__editable__.prinet-3.0.0.pth` → `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src`) |
| Matplotlib | data path `C:\dev\PRIN\.venv\Lib\site-packages\matplotlib\mpl-data`; cache dir `C:\Users\there\.matplotlib`; font cache `fontlist-v3.11.0.json` = 146,692 bytes, SHA-256 `9c00441405ce72925562e017858a729b402612a203b0682b2e7fd79329c8f6bb`; default backend before importing PRIN is `tkagg`, and `prin.reporting.figure_generation` forces `Agg` on import (the reference module also calls `matplotlib.use("Agg")`) |
| Environment variables that could affect imports | `PYTHONPATH`, `PYTHONHOME`, `MPLBACKEND`, `MPLCONFIGDIR` all empty; `VIRTUAL_ENV` = `c:\dev\PRIN\.venv` |
| Installed extension | `python/prin/_prin_core.pyd`, 62,792,192 bytes, SHA-256 `64ea1a2cf38cdbe43fc029c55e791e244b771b2909360c3890ae6f9224b47349`, last written 2026-09-28T23:01:06Z. A GPU-capable build (attributes `GpuBandStepper`, `GpuMeanFieldEngine`, `GpuSparseKuramoto` are present); EXP-002 registers backend `cpu` and no GPU dispatch. 207 public attributes |

### 2.5 Quiescence (checklist item 5)

No `python`, `pytest`, `cargo`, `rustc`, `gitleaks`, `maturin`, `mypy`, `bandit`,
`pip-audit` or `sphinx-build` process was running; no Snyk scan, `agy` or `devin` task
was running. Idle IDE-hosted background services were present and were **not** stopped
(they belong to the maintainer's editor, which also hosts this session): `rust-analyzer`
(3.1 GB working set), Pyright language servers, `ruff server`, the Snyk language server
and several `snyk mcp` stdio servers, MCP servers (playwright, puppeteer, memory,
filesystem, perplexity), ACP agent servers (gemini, qwen, auggie, kilo, cursor-agent,
deepagents), CodeQL JVMs. Over a 6 s sample all processes together consumed 3.28 CPU-seconds
of the 96 available, and `Win32_Processor.LoadPercentage` read 2 %. EXP-002 measures
no timing, so this does not affect any registered quantity; it is recorded for honesty
about "nothing else is running". No gate, test, scan or other tool will be run while a
leg is running, and this log and the repository will not be written while a leg runs.

### 2.6 Observations recorded before the first leg (none is a registered abort criterion)

1. **The installed extension predates the latest Rust-source commits at `R`.**
   `_prin_core.pyd` was written 2026-09-28T23:01:06Z (20:01:06 local). Commits touching
   `crates/` after that: `e4f5b4e` (2026-09-28 21:48 −03:00, DV-043 re-clamp removal),
   `199b82a` (2026-10-11, DV-042 doc-attribute change), `9a9889d` (2026-10-12, argument
   validation in `cross_band_coupling_cpu`). The extension was not rebuilt in sessions 0159–0160,
   so the E2 approved-source gate (6,047 passed) also ran against it. EXP-002 resolves exported
   names and renders from stored JSON; it exercises no Rust numerics (protocol §5.1, §6). I did
   **not** rebuild it: that would change the environment the E2 gate validated and the
   protocol does not register a rebuild. The driver does not record the extension's hash, so
   this log is the only place it is recorded. Reported to the maintainer as an open point.
2. **`prin_core.pth` points at a second tree.** `site-packages/prin_core.pth` →
   `C:\dev\PRIN-r1-amendment\python` (a leftover EXP-001-r1 worktree) and `prin.pth` →
   `C:\dev\PRIN\python`. `prin.pth` sorts first, `prin` resolves to `C:\dev\PRIN\python`
   (verified above), and the driver's `_check_origin` refuses any other origin.
3. **Read-only probes performed during pre-flight.** The driver module was imported (as the
   driver itself does), which imports `prin.reporting.figure_generation`; no figure/table
   generator function was called and the reference `prinet` publication modules were not
   imported. One no-argument export was called once, `core_version()` (returned
   `1.0.0-rc1`), plus passive `dir()` introspection of `prin._prin_core`. No other export was
   called; no registered input was read by a probe; nothing was rendered. `git status
   --porcelain` stayed empty after the probes.

## 3. Aggregate CPU-wall tracker (protocol §9 cap: ≤ 12 h = 43,200 s across all attempts)

Wall time of each attempt as measured by the launch wrapper (process launch to exit, including
interpreter start-up and imports); the driver's own `elapsed_seconds` is quoted next to it.
Pre-flight probes above (a few seconds of Python start-up each) are not legs and are not counted.

| # | Run ID | Wall (s) | Driver `elapsed_seconds` | Cumulative wall (s) | Remaining of cap (s) |
|---|---|---|---|---|---|
| — | (no leg run yet) | 0 | — | 0 | 43,200 |

## 4. Legs (registered order: api → conclusions → reference → prin → repeatability)

Each leg is launched once, in its own interpreter process, at `R`, with no commit or
repository edit between legs. Launch wrapper: a PowerShell script outside the repository that
takes the UTC stamp, runs the registered command exactly, and records start/end UTC, exit
code and wall time. The command shape (protocol §5.5) is:

```
.venv\Scripts\python -m benchmarks.campaign.exp002_driver --mode <mode> --run-dir "benchmarks/results/EXP-002/RUN-<UTC>-fae24c4-<label>" --operator MichaelMaillet --source-sha fae24c4393c7a0232e6c8f0a6388b1775aa5fc05 --seed-counter 0 --seed-key 2
```

### 4.1 Leg 1 — mode `api`, label `api-cpu` (payload `api.json`, registered for H1)

**Protocol freeze.** The first `RUN-` directory of the experiment was created at
2026-10-12T21:27:05Z, so `preregistration.md` (SHA-256 `0f3073dd…`, last commit `F` =
`9a9889d08dcaf2ad0ce31659ed67721b54b114d0`) is frozen from this instant
(Experimentation Standards §1.3; protocol §11.3).

| Field | Value |
|---|---|
| Run ID | `RUN-20261012T212705Z-fae24c4-api-cpu` |
| Operator | MichaelMaillet |
| Exact command (from `C:\dev\PRIN`) | `.venv\Scripts\python -m benchmarks.campaign.exp002_driver --mode api --run-dir "benchmarks/results/EXP-002/RUN-20261012T212705Z-fae24c4-api-cpu" --operator MichaelMaillet --source-sha fae24c4393c7a0232e6c8f0a6388b1775aa5fc05 --seed-counter 0 --seed-key 2` |
| UTC start / end (launch wrapper) | 2026-10-12T21:27:05.708Z / 2026-10-12T21:27:16.461Z |
| Exit code | **0** |
| Elapsed wall (wrapper, process launch → exit) | 10.733 s |
| Driver `elapsed_seconds` | 0.3223612999991019 (`started_at_utc` 2026-10-12T21:27:15.465014+00:00, `recorded_at_utc` 2026-10-12T21:27:15.787374+00:00); the rest of the wall time is interpreter start-up and imports |
| Cumulative wall over all attempts | 10.733 s of 43,200 s (cap ≤ 12 h) |
| stdout / stderr | both empty (0 bytes each) |
| Abort-criterion trips (§4.2) | none; record `status` = `COMPLETED`, no `abort_reason`, closure check exit 0 |
| Anomalies | none observed |
| Run directory (exactly three entries) | `api.json` 97,194 B `b76aedab424582dec72ede165c6a136e62c802b395519cba56975fa75f0fade9`; `campaign-metadata.json` 215 B `d51f9c7b4ae1f9b32e20cf211a55bfc416470eae1e332c823df645ead8b5e355`; `manifest.json` 554 B `d4eee92905addee67c210192a7a97a35b4e52e5f623f1fe34b04fcae9f8eaa90` |
| Driver-captured environment | backend `cpu`, dtype `f64`, `seed` 0 (documentary; `seed_used` false), `git_commit` = `R`, `prin_version` 1.0.0rc1, rustc 1.99.0 (b940084d7 2026-09-28), Python 3.14.0, `Windows-11-10.0.26300-SP0`, AMD64 Family 25 Model 117 Stepping 2, 16 logical CPUs; `gpu` = NVIDIA GeForce RTX 4060, 8,188 MB (present and captured; not used — this leg registers backend `cpu`) |
| Driver-captured config | `iterations` 10, `warmup` 0, `replicates` 1, `measurement_kind` `deterministic_census`, `seed_counter` 0, `seed_key` 2, `out_dir` = the absolute run directory |
| Publication listing digest | not applicable (no publication output) |

**Per-record validation (before acceptance).** An independent validator written outside the
repository, which imports nothing from the driver (stdlib + `git`), checked 69 properties: directory
name/label/`R7`/UTC stamp and location; exactly sidecar + result + manifest, all plain files; manifest
schema, entry set and recomputed sizes/SHA-256; sidecar keys, `exp_id`, `session`, `run_id`, operator,
mode and the exact artefact mapping `{"api.json": ["H1"]}`; the envelope's keys and `COMPLETED` /
`seed_used=false`; environment completeness; config incl. the `(0,2)` seed pair (ints, not bools);
`HEAD == R`; protocol commit/digest recomputed from the git blob, ancestor of `R`, `APPROVED` +
dated approval line; the input manifest digest and the 172 input records against the committed
`paper/artefact_manifest.json`; timestamps; the observation schema and registered 175-name population
(re-derived from the pinned reference `__all__` plus the three PRIN additions); and the repository state
(only EXP-002 raw records and this log differ from a clean checkout; no untracked top-level
`*.py`/`*.pth`). **Result: 69 passed, 0 failed, exit 0 → the record is ADMISSIBLE.** The validator
does not read or judge any outcome field (`resolved`, `callable`, `observed`, …); the contents of the
observations were not examined at E3.
Validator SHA-256 `5703fad41b5bf8466643694cc9a711ee423012762992bb2def1eb8074964fd4d`; transcript
SHA-256 `c97888037e947f779bbd12e25fa421fc9bec6df5e3256b9b2bcd908cdd07009d`. A mutation
self-test on scratch copies of this record (16 mutations: stray file, flipped byte, seed key, seed
counter as bool, aborted status, wrong source SHA, wrong protocol digest, wrong input-manifest digest,
dropped input record, wrong backend, null environment field, wrong operator, wrong artefact mapping,
missing manifest entry, broken population, negative elapsed time; plus one unmodified control)
confirmed that each mutation fails the intended check and the control passes (17 of 17 cases behaved as
expected; `mutation_test.py` SHA-256 `d91d679185de1552121d3b4dbebc891f9f481d3e444258cc2b6341dedfc40d64`).
After the leg and the validation, `git status --porcelain` listed only this log and the three new files.

### 4.2 Leg 2 — mode `conclusions`, label `conclusions-cpu` (payload `conclusions.json`, registered for H2)

| Field | Value |
|---|---|
| Run ID | `RUN-20261012T213054Z-fae24c4-conclusions-cpu` |
| Operator | MichaelMaillet |
| Exact command (from `C:\dev\PRIN`) | `.venv\Scripts\python -m benchmarks.campaign.exp002_driver --mode conclusions --run-dir "benchmarks/results/EXP-002/RUN-20261012T213054Z-fae24c4-conclusions-cpu" --operator MichaelMaillet --source-sha fae24c4393c7a0232e6c8f0a6388b1775aa5fc05 --seed-counter 0 --seed-key 2` |
| UTC start / end (launch wrapper) | 2026-10-12T21:30:54.253Z / 2026-10-12T21:31:04.800Z |
| Exit code | **0** |
| Elapsed wall (wrapper) | 10.521 s |
| Driver `elapsed_seconds` | 0.2889907000007952 (`started_at_utc` 2026-10-12T21:31:03.860266+00:00, `recorded_at_utc` 2026-10-12T21:31:04.149256+00:00) |
| Cumulative wall over all attempts | 21.254 s of 43,200 s (10.733 + 10.521) |
| stdout / stderr | both empty (0 bytes each) |
| Abort-criterion trips (§4.2) | none; `status` = `COMPLETED`, no `abort_reason`, closure check exit 0 |
| Anomalies | none observed |
| Run directory (exactly three entries) | `conclusions.json` 59,206 B `2d1cdc5fa76b247da1b8544606708b6fa0ffe9afaaf274604bc4c1115e9bed84`; `campaign-metadata.json` 239 B `1f59f1e078fce9154703feb93499da62f8d3c183406de9e3ebfded3cc2a04756`; `manifest.json` 562 B `d5247c24728c26d21bc4677036091ac4665888a526b9825df231ff5ef2439bd9` |
| Driver-captured config / environment | same schema and values as leg 1 (`seed_counter` 0, `seed_key` 2, `iterations` 10, `warmup` 0, `replicates` 1, `deterministic_census`; backend `cpu`, dtype `f64`, `git_commit` = `R`) |
| Publication listing digest | not applicable |

**Per-record validation.** 67 checks, **67 passed, 0 failed, exit 0 → ADMISSIBLE.** Same
validator as leg 1, with the mode-specific observation checks: unit `claim_comparator_record`; 62
cases with 62 unique `case_id`s; registered family cardinalities C01=5, C02=42, C03=4, C04=5, C05=6;
every `case_id` begins with its family label; `expected`/`observed` are real Booleans; operands are
finite numbers and the operator is `>` or `<`. As at leg 1, the validator does not compare any
`expected` with any `observed` and the observation contents were not examined at E3.
Transcript SHA-256 `5d501fea1a43192a22dba688af95a20e564c9a92802cf659f759a1bde6508d8d`.

**Validator revision (disclosure).** Running the mutation self-test in `conclusions` mode showed that
the first validator revision (SHA-256 `5703fad…`, used for leg 1 above) ended in a traceback and
exit 1, with no `FAIL` line, when a result file had been corrupted into invalid JSON. A crash still
rejects a record, but it should be reported as a failed check, so I fixed it (an unexpected error is now
a `FAIL` line `Z0`; two `SystemExit` raises became `RuntimeError`). Revision 2: SHA-256
`34fa0c950658422a9fb936bb539653242388647590cb4ac49adcf4f3bfa45b18`. Revision 2 re-validated leg 1
(69/69, transcript byte-identical to revision 1's) and leg 2 (67/67), and the self-test passes 17/17
in both modes (transcripts: api `9b62aa2dad19b5875e59766eb8215501fbdc65304dbd5726978b0b505c3f8e69`,
conclusions `0632458165c82fa5b1af9e1f16bb8d8e671822ff195cea75c75dcfad3acfdc26`). No record or
check outcome changed. The validator checks only record validity, never an experimental outcome.

### 4.3 Leg 3 — mode `reference`, label `reproduction-reference-cpu` (payload `reproduction.json`, registered for H3)

| Field | Value |
|---|---|
| Run ID | `RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu` |
| Operator | MichaelMaillet |
| Exact command (from `C:\dev\PRIN`) | `.venv\Scripts\python -m benchmarks.campaign.exp002_driver --mode reference --run-dir "benchmarks/results/EXP-002/RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu" --operator MichaelMaillet --source-sha fae24c4393c7a0232e6c8f0a6388b1775aa5fc05 --seed-counter 0 --seed-key 2` |
| UTC start / end (launch wrapper) | 2026-10-12T21:38:21.711Z / 2026-10-12T21:38:35.945Z |
| Exit code | **0** |
| Elapsed wall (wrapper) | 14.212 s |
| Driver `elapsed_seconds` | 4.004785899998751 (`started_at_utc` 2026-10-12T21:38:31.138373+00:00, `recorded_at_utc` 2026-10-12T21:38:35.143158+00:00) |
| Cumulative wall over all attempts | 35.466 s of 43,200 s (10.733 + 10.521 + 14.212) |
| stdout / stderr | both empty (0 bytes each) |
| Abort-criterion trips (§4.2) | none; `status` = `COMPLETED`, no `abort_reason`, closure check exit 0 |
| Anomalies | none observed |
| Run directory (exactly three entries) | `reproduction.json` 59,584 B `70f9677c7523c2decf3dc0b9e3e1ba8763ee56838ff63deca93587b42c89e7e3`; `campaign-metadata.json` 249 B `722fc141089fc0ece7fb043cb67b0bba574beca85fc3b45c5fceacb8b60b25c2`; `manifest.json` 563 B `f5410f4f0d5d3f6835575b377e211d6e704b0759f0457df4751a6ad0abee9d6d` |
| Renderer capture (driver, before and after generation equal) | Matplotlib 3.11.1, NumPy 2.5.1, Pillow 12.3.0, FreeType 2.14.3, backend `Agg`; font cache `fontlist-v3.11.0.json` SHA-256 `9c00441405ce72925562e017858a729b402612a203b0682b2e7fd79329c8f6bb` (equal to the pre-flight value; the file's size and mtime were also unchanged after the leg); 40 bundled `.ttf` files hashed (SHA-256 of the canonical font map `168e1aee710ca4496f65d7dc0689ed93257ed3e1ab3711dad4494940b51c8189`) |
| Generated-output root (gitignored, **retained unmodified**) | `DOCS/test_and_benchmark_results/EXP-002/RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu/` — `inputs/` (verified snapshot of the 172 input records, 16,047,018 B) and `publication/` (1,502,048 B in 39 files, descriptive only) |
| **Publication listing digest** (e2-review.md §8 command, verbatim) | `d674de7d4b5830c9abf525fcc484a5ebc01e3620ca38b63badd037e289487323` (listing of 39 entries; the validator's independent implementation of the same formula printed the same value). The count is descriptive; no comparison with the registered inventory was made at E3 |

**Per-record validation.** Validator revision 2 (`34fa0c95…`), mode `reference`: 73 checks,
**73 passed, 0 failed, exit 0 → ADMISSIBLE.** The mode-specific checks: unit `generated_file`;
`implementation` = `reference`; `expected_files` equals the registered 39-file list parsed from the
frozen protocol blob; renderer capture carries the registered keys with a non-null font-cache digest;
file records are unique strings with non-negative integer sizes and 64-hex digests for the raw,
normalized and sensitivity (§11.3 item 1) fields. Retention checks (integrity only): the output
root, `publication/` and `inputs/` exist and are not links; the retained file set equals the record's
file set; every retained file matches its own recorded raw size and SHA-256; the retained input snapshot
equals the 172 recorded input records. No publication file was compared with another arm and none was
opened for content. Transcript SHA-256 `d9c9ddb92b1ac2f05b782957beb64aa2a583e54b498f807e87a666f3bd5e8b0b`.

### 4.4 Leg 4 — mode `prin`, label `reproduction-prin-cpu` (payload `reproduction.json`, registered for H3 and H4)

| Field | Value |
|---|---|
| Run ID | `RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu` |
| Operator | MichaelMaillet |
| Exact command (from `C:\dev\PRIN`) | `.venv\Scripts\python -m benchmarks.campaign.exp002_driver --mode prin --run-dir "benchmarks/results/EXP-002/RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu" --operator MichaelMaillet --source-sha fae24c4393c7a0232e6c8f0a6388b1775aa5fc05 --seed-counter 0 --seed-key 2` |
| UTC start / end (launch wrapper) | 2026-10-12T21:39:36.175Z / 2026-10-12T21:39:50.366Z |
| Exit code | **0** |
| Elapsed wall (wrapper) | 14.172 s |
| Driver `elapsed_seconds` | 4.082989100001214 (`started_at_utc` 2026-10-12T21:39:45.503175+00:00, `recorded_at_utc` 2026-10-12T21:39:49.586164+00:00) |
| Cumulative wall over all attempts | 49.638 s of 43,200 s (10.733 + 10.521 + 14.212 + 14.172) |
| stdout / stderr | both empty (0 bytes each) |
| Abort-criterion trips (§4.2) | none; `status` = `COMPLETED`, no `abort_reason`, closure check exit 0 |
| Anomalies | none observed |
| Run directory (exactly three entries) | `reproduction.json` 59,572 B `776a926df8edb333e38d61e9fc4ba2966385df56bcfc3d9eda6540c7c47b590e`; `campaign-metadata.json` 252 B `6316a9e03f53cc966d70f8c83d1d70f7962857edc09f7dc8b4c6d4fe507d0e7e`; `manifest.json` 563 B `0213ac284abf55b04a6cd5641abecb4b25d00be1b8e488e562c9b6cb399e18c8` |
| Renderer capture (driver, before and after generation equal) | Matplotlib 3.11.1, NumPy 2.5.1, Pillow 12.3.0, FreeType 2.14.3, backend `Agg`; font cache `fontlist-v3.11.0.json` SHA-256 `9c00441405ce72925562e017858a729b402612a203b0682b2e7fd79329c8f6bb` (size and mtime also unchanged after the leg); 40 bundled `.ttf` files hashed, canonical font-map SHA-256 `168e1aee710ca4496f65d7dc0689ed93257ed3e1ab3711dad4494940b51c8189` — the same scalar fields and font-map digest as leg 3 |
| Generated-output root (gitignored, **retained unmodified**) | `DOCS/test_and_benchmark_results/EXP-002/RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu/` — `inputs/` (172 files, 16,047,018 B) and `publication/` (1,500,705 B in 39 files, descriptive only) |
| **Publication listing digest** (e2-review.md §8 command, verbatim) | `c1ca4ada167c50a28db2dfe4365d004cdb3621903f43e38cc6de75c2e4904669` (listing of 39 entries; the validator's independent implementation of the same formula printed the same value). Descriptive; not compared with any other digest or inventory at E3 |

**Per-record validation.** Validator revision 2, mode `prin`: 73 checks, **73 passed, 0 failed,
exit 0 → ADMISSIBLE** (same checks as leg 3 with `implementation` = `prin`; retention checks pass: file
set and every retained file match the record's own raw sizes and digests; input snapshot equals the
172 records). No publication file was compared with another arm or opened for content. Transcript
SHA-256 `abe14b42ecf6c5b287b10daa8381148944c1542da3b7bd365d2022fc6b51664d`.

### 4.5 Leg 5 — mode `repeatability`, label `seedrep0-prin-cpu` (payload `reproduction.json`, registered for H4)

Second invocation of replicate 0 of the same PRIN reproduction configuration (protocol §7).

| Field | Value |
|---|---|
| Run ID | `RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu` |
| Operator | MichaelMaillet |
| Exact command (from `C:\dev\PRIN`) | `.venv\Scripts\python -m benchmarks.campaign.exp002_driver --mode repeatability --run-dir "benchmarks/results/EXP-002/RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu" --operator MichaelMaillet --source-sha fae24c4393c7a0232e6c8f0a6388b1775aa5fc05 --seed-counter 0 --seed-key 2` |
| UTC start / end (launch wrapper) | 2026-10-12T21:40:40.138Z / 2026-10-12T21:40:54.339Z |
| Exit code | **0** |
| Elapsed wall (wrapper) | 14.183 s |
| Driver `elapsed_seconds` | 4.172898700000587 (`started_at_utc` 2026-10-12T21:40:49.387992+00:00, `recorded_at_utc` 2026-10-12T21:40:53.560890+00:00) |
| Cumulative wall over all attempts | 63.821 s of 43,200 s (10.733 + 10.521 + 14.212 + 14.172 + 14.183) |
| stdout / stderr | both empty (0 bytes each) |
| Abort-criterion trips (§4.2) | none; `status` = `COMPLETED`, no `abort_reason`, closure check exit 0 |
| Anomalies | none observed |
| Run directory (exactly three entries) | `reproduction.json` 59,568 B `ec615eb48008bcc112ad73a10fc6ea42ddf5619ecb33b87e880a1e7977084127`; `campaign-metadata.json` 244 B `77cf576fb454cd32b9247e1392112d1a67c0a927ab4707c45393e091554a25ec`; `manifest.json` 563 B `5722cb93ac87c4bf448ee76b53721c0d030bc0b0d3a465db7ab6db403db78388` |
| Renderer capture | font cache `fontlist-v3.11.0.json` SHA-256 `9c00441405ce72925562e017858a729b402612a203b0682b2e7fd79329c8f6bb` (size and mtime unchanged after the leg); 40 `.ttf` files hashed, canonical font-map SHA-256 `168e1aee710ca4496f65d7dc0689ed93257ed3e1ab3711dad4494940b51c8189` |
| Generated-output root (gitignored, **retained unmodified**) | `DOCS/test_and_benchmark_results/EXP-002/RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu/` — `inputs/` (172 files, 16,047,018 B) and `publication/` (1,500,705 B in 39 files, descriptive only) |
| **Publication listing digest** (e2-review.md §8 command, verbatim) | `c1ca4ada167c50a28db2dfe4365d004cdb3621903f43e38cc6de75c2e4904669` (listing of 39 entries; the validator's independent implementation of the same formula printed the same value). Recorded as measured; no comparison with any other leg is made or implied at E3 |

**Per-record validation.** Validator revision 2, mode `repeatability`: 73 checks, **73 passed, 0 failed,
exit 0 → ADMISSIBLE** (same checks and retention checks as leg 4). Transcript SHA-256
`7472298c16188bdaa563ffbbfc1f5d1a789ea2316077d20191190863308a72e5`.

### 4.6 Cross-leg metadata consistency (abort criteria §4.2 items 1 and 3; not an outcome comparison)

A second scratch script compared only **metadata** across the five records and never opened an
observation payload (no API row, claim case or publication file record was read or compared):

- the driver-captured `environment` block (hardware, OS, interpreter, Rust version, backend, dtype, `git_commit`, seed) is identical on all five legs;
- the `identity` block (source SHA, protocol commit/digest/approval date, input-manifest digest, 172 input records) is identical on all five legs;
- `config` is identical on all five legs except for `out_dir`; `(seed_counter, seed_key)` = `(0, 2)` on all five;
- the renderer / font-stack capture (versions, backend, font-cache digest, 40 font digests) is identical on the three publication legs, so no "renderer/font-stack change between compared runs" occurred;
- five distinct run directories, UTC stamps strictly increasing in the registered order.

Result: **0 failures** (transcript SHA-256 `93d600c1268aa6312af8e6381a721e02975769ef2dcf8b4e8a3b0d32f68f94aa`).

## 5. Execution phase summary (all attempts; entered 2026-10-12, after leg 5)

Every registered leg ran exactly once at `R`, each in its own interpreter process, in the registered
order. There were **no aborted, incomplete, retried or rerun attempts** and no abort-criterion trip, so
the five records below are all of the `RUN-` directories created. No D1 condition occurred. No file
other than this log and the new `RUN-` directories changed between the first and the last leg
(validator checks G1–G3 passed after every leg, plus `git status --porcelain=v1` after every leg).

| # | Mode / label | Run ID | UTC start → end | Exit | Wall (s) | Driver elapsed (s) | `status` | Admissible | Publication listing digest |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `api` / `api-cpu` | `RUN-20261012T212705Z-fae24c4-api-cpu` | 21:27:05.708 → 21:27:16.461 | 0 | 10.733 | 0.3224 | COMPLETED | yes (69/69) | n/a |
| 2 | `conclusions` / `conclusions-cpu` | `RUN-20261012T213054Z-fae24c4-conclusions-cpu` | 21:30:54.253 → 21:31:04.800 | 0 | 10.521 | 0.2890 | COMPLETED | yes (67/67) | n/a |
| 3 | `reference` / `reproduction-reference-cpu` | `RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu` | 21:38:21.711 → 21:38:35.945 | 0 | 14.212 | 4.0048 | COMPLETED | yes (73/73) | `d674de7d4b5830c9abf525fcc484a5ebc01e3620ca38b63badd037e289487323` |
| 4 | `prin` / `reproduction-prin-cpu` | `RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu` | 21:39:36.175 → 21:39:50.366 | 0 | 14.172 | 4.0830 | COMPLETED | yes (73/73) | `c1ca4ada167c50a28db2dfe4365d004cdb3621903f43e38cc6de75c2e4904669` |
| 5 | `repeatability` / `seedrep0-prin-cpu` | `RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu` | 21:40:40.138 → 21:40:54.339 | 0 | 14.183 | 4.1729 | COMPLETED | yes (73/73) | `c1ca4ada167c50a28db2dfe4365d004cdb3621903f43e38cc6de75c2e4904669` |

(All times 2026-10-12 UTC; operator MichaelMaillet; seed pair `(0, 2)`; the listing digests are the
output of the e2-review.md §8 command, recorded as measured and not compared at E3.)

**Aggregate CPU wall across all attempts (protocol §9 cap ≤ 12 h = 43,200 s):** 10.733 + 10.521 +
14.212 + 14.172 + 14.183 = **63.821 s** (about 1 min 4 s, 0.15 % of the cap). The drivers' own
`elapsed_seconds` sum to 12.872 s; the rest is interpreter start-up and import time. GPU wall 0 s
(no GPU leg); hosted CI wall charged to the experiment 0 s (E2 decision 10).

**Tracked bytes of the new raw records against the registered caps** (measured with
`measure_bytes.py` after leg 5, before any other repository change; transcript SHA-256
recorded in the evidence bundle):

| Quantity | Measured | Cap | Headroom |
|---|---|---|---|
| Largest single run (`api-cpu`, 3 files) | 97,963 B (0.0934 MiB) | 2 MiB per run | 1,999,189 B |
| Other four runs | 60,007 / 60,396 / 60,387 / 60,375 B | 2 MiB per run | > 2.03 MB each |
| All five new raw run records | 339,128 B (0.3234 MiB) | ≤ 10 MiB new tracked artefacts | — |
| Driver's closure measure (EXP-002 raw root incl. its `README.md` + record root incl. this log) | 463,913 B (0.4424 MiB) | 10 MiB | 10,021,847 B |
| Campaign-wide `benchmarks/results/EXP-*` | 13,756,033 B (13.119 MiB; EXP-001 13,404,517 B) | 64 MiB | 50.881 MiB |

The caps leave ample room. The totals are re-measured on the staged change in §7.

**Retained, untracked artefacts.** The three generated-output roots under
`DOCS/test_and_benchmark_results/EXP-002/` (gitignored; `inputs/` 16,047,018 B and `publication/`
39 files each) are kept unmodified until the E5 report is accepted (E2 decision 8). They were
re-verified against their records' own raw digests by validator checks F2–F4 after each publication leg.

**No verdict.** No hypothesis (H1–H4) verdict was computed, stated or implied in this log. The
observation payloads of the five records were not examined at E3. Interpretation, the
comparison of the arms and the repeat, and every D1 determination belong to E4 (session 0162).

## 6. Local gate (Plan amendment #48: the Windows local gate is authoritative; entered after the gate ran)

No gate, test, scan or other tool ran while a leg was running, and none of the legs below ran before
leg 5 had finished. Candidate: `HEAD` = `92cf696` (`R` plus the one-rule `.gitattributes` commit,
`chore(0161): byte-preserve EXP-002 E3 execution evidence`) with all session-0161 changes staged (the five
raw run records, this log, the record updates and `EVIDENCE/0161/`). The final run is "gate run 3", started
from **Git Bash** (explained below), on the maintainer's Windows host (Windows 11 10.0.26300, Python 3.14.0,
Rust 1.99.0); nothing else was running except the idle editor services of §2.5. No leg was
subject to a whole-run wall-clock kill (amendment #49). The legs follow the list in
`EVIDENCE/0160/verification/gate/`; each capture in `EVIDENCE/0161/verification/gate/` carries its verbatim
`COMMAND:`, `UTC-START:` and `EXIT_CODE:`.

| Leg | What ran | Exit | Result |
|---|---|---|---|
| G01 | `ruff check python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/` | 0 | All checks passed |
| G02 / G03 | `ruff format --check` (product roots; `DOCS/experiments/` source-only) | 0 / 0 | 329 / 2 files already formatted |
| G04 / G05 / G06 | `mypy --strict` on `python/prin`, `DOCS/experiments/`, `exp002_driver.py` | 0 / 0 / 0 | no issues in 62 / 2 / 1 source files |
| G07 | `interrogate -c pyproject.toml python/prin` | 0 | PASSED, 97.6 % (minimum 95 %) |
| G08 | `bandit -r python/prin DOCS/experiments -c pyproject.toml` | 0 | no issues identified (24,864 lines) |
| G09 | focused pytest: `test_exp002_driver`, `test_0159_manifest`, `test_0160_manifest`, `test_basetemp`, `test_ea007_manifest`, `test_campaign_quality_gates`, `test_wp001_baseline` | 0 | 460 passed in 260.15 s; `exp002_driver.py` 99 % (706 statements, 3 missed: lines 545, 891, 1370) |
| G10 / G10b / G10c / G10d / G10e | deviation ledger 039→040; DV-register gates; global-session registration; skipif probes; WP-001 baseline | 0 each | passed (ledger: 142 → 146 rows; DV gates: 44 rows against 198 session entries; 18 Executive Audit reports) |
| G10f | `git diff --cached --check` | 0 | clean (see `G10fa` below) |
| G11 | `sphinx -W --keep-going -b html DOCS/sphinx` into a fresh directory | 0 | full build of 35 sources, "build succeeded", no warning |
| G12 | fast pytest `tests/ -m "not slow and not gpu" --cov=prin` | 0 | 3,853 passed, 178 skipped, 55 deselected, 59 warnings in 1,170.71 s; coverage TOTAL 95 % |
| G13 | full pytest `tests/ parity/ --cov=prin` | 0 | 6,047 passed, 184 skipped, 61 warnings in 1,985.99 s; coverage TOTAL 95 % |
| G14 | Snyk Code (`--severity-threshold=medium --org=symbo-gif`) over byte-identical copies of the 8 new first-party Python files | 0 | 0 issues. **Not blocked**: the scan ran to completion and returned (the monthly private-test limit reported for the org on 2026-10-12 did not stop it) |
| G17 | gitleaks full history (pinned 8.30.1; repository is not shallow) | 0 | 719 commits scanned, no leaks |
| R01–R04 | `cargo --version`; `cargo fmt --all -- --check`; `cargo clippy --workspace --all-targets -- -D warnings` (default, and with `--features strict-checks`) | 0 each | clean |
| R05 / R06 | `cargo test --workspace` (default, and `--features strict-checks`) | 0 / 0 | 1,604 and 1,608 passed, 0 failed, 1 ignored each |
| R07 | `cargo llvm-cov -p prin-kernels --features wgpu,cpu` | 0 | TOTAL regions 85.10 %, functions 88.54 %, lines 84.24 % |

The pytest, cargo and llvm-cov totals are identical to the session-0160 gate on the approved source
(FAST 3,853 / 178; FULL 6,047 / 184; 1,604 / 1,608 Rust tests; the same llvm-cov TOTAL), as expected:
this session changes no product, driver, test-logic or Rust file. The coverage figures are the
repository totals the gate has always reported; DV-033 (per-change coverage cannot be measured on this
host) is unchanged and not closed by them.

**Kept failed and diagnostic captures (never relabelled):**
- `G10fa` — `git diff --cached --check` reported trailing whitespace on the `Status` line I had changed in the
  0162 brief (two spaces left over from the original line). Fixed, restaged, and the whole phase-1 set was
  re-run on the corrected candidate.
- `G09a` and `G12a` — the first focused and fast pytest attempts were started from PowerShell, where `bash` on
  `PATH` is `C:\windows\system32\bash.exe`, the WSL launcher. WSL's virtual machine did not start
  (`HCS_E_CONNECTION_TIMEOUT`), so four `tests/test_wp001_baseline.py` release-workflow tests that shell out to
  `bash` failed (`G09a`: 4 failed, 456 passed). I stopped the run (`G12a` is the incomplete fast-suite capture, with no
  exit-code footer; no process was left running) and restarted the gate from Git Bash, whose `bash` is Git's, as
  in sessions 0159–0160. Cause: the shell environment of the launch, not the candidate; the same 460 tests passed
  from Git Bash (`G09`).
- `G14a` and `G14b` — see §6.1.

### 6.1 Snyk Code history for the shipped scripts

`G14a` scanned the seven tool scripts that existed first: 0 issues. `G14b` scanned nine files after adding the
gate harness (scratch `run_gate.py`, SHA-256 `0488b6b25b328d49f7e43915aa6e3b1669790c0e47c71f048fec6e554812eede`) and the byte-check
script: **one Medium finding**, "Command Injection" at the harness's `subprocess.Popen` call (the log-directory
command-line argument flows into some of the commands' argument lists). Remediation: the harness is scratch tooling that
only sequenced the commands recorded in each log's `COMMAND:` header, so it is **not committed** (its SHA-256 is
recorded here and in `EVIDENCE/0161/README.md`); `G14` rescanned the eight scripts that are committed and is clean at the
governed `medium` threshold. Nothing was suppressed or excluded.

### 6.2 Not run, with the reason

- `G15` pip-audit / Snyk Open Source / `cargo audit`: **not applicable** — no dependency manifest or lock changed.
- A forced nightly: **not dispatched** (not requested).
- Linux and macOS: **not tested** (amendment #48); nothing here claims their behaviour.

## 7. Secret scan of the staged change, byte-exactness of what is staged, and the re-measured caps

- **`G18` gitleaks on the staged diff** (`gitleaks git C:/dev/PRIN --pre-commit --staged --redact`, pinned
  8.30.1): 2.41 MB scanned, **no leaks found**, exit 0. It ran on the staged index before its own capture and the `G16`
  capture were added (a scan cannot contain its own output; the output is redacted). GitHub-native secret scanning and push
  protection remain separate, independent controls that I cannot see from here; push protection was flagged as
  disabled at amendment #48 and this log makes no claim about it. (`G17`, the full-history scan, is in §6.)
- **`G16` staged byte-exactness check** (`EVIDENCE/0161/verification/tools/staged_bytes_check.py`): 191 comparisons, **0 failed**.
  Every staged raw-record blob equals its working-tree file and its entry in the run's `manifest.json` (and each
  manifest's file set is exactly its entries plus itself); all 80 evidence files then in the index equal their
  `SHA256SUMS.txt` entries and their working-tree bytes. The raw result and sidecar files are CRLF as the Windows
  driver wrote them (each `manifest.json` is LF); `.gitattributes` (`benchmarks/results/** -text`,
  `EVIDENCE/0161/** -text`) keeps those bytes unconverted in git, so a clean checkout verifies against its own
  manifests. (`git ls-files --eol` shows `i/crlf w/crlf attr/-text` for the result and sidecar files.)
- **Caps re-measured on the staged change** (the re-measurement promised in §5; blob sizes via
  `git cat-file -s`, whole size for added files, growth only for modified files):

| Area | Files | New tracked bytes |
|---|---|---|
| Raw run records (`benchmarks/results/EXP-002/RUN-*`) | 15 | 339,128 B (0.3234 MiB) |
| This log (as staged when measured; this entry adds about 3 kB) | 1 | 43,299 B |
| Record and documentation updates (9 modified files, growth only) | 9 | 9,705 B |
| **EXP-002 raw/record artefacts, total** (cap ≤ 10 MiB) | 25 | **392,132 B (0.374 MiB)** |
| Evidence bundle `EVIDENCE/0161/` (gate logs, transcripts, tools; not an EXP-002 raw/record artefact) | 84 | 2,021,337 B (1.93 MiB) |
| Whole staged change | 109 | 2,413,469 B (2.30 MiB) |

  Largest single run 97,963 B (cap 2 MiB per run); campaign-wide `benchmarks/results/EXP-*` 13,756,033 B = 13.119 MiB
  (cap 64 MiB). No cap is near its limit and none was breached.

## 8. Hosted results for the E3 commit `89f21f5` (Plan amendment #50; additional evidence only)

Entered 2026-10-13T00:31Z. `92cf696` and `89f21f5` were pushed at about 2026-10-12T23:33:55Z
(`fae24c4..89f21f5`, branch `campaign/0159-exp002-e1`, PR #33). Nothing was merged, no tag was pushed, no
workflow was changed and no nightly was dispatched. All seven runs below are head SHA
`89f21f5b42c195e46d172808fb39941c47451de8`, attempt 1; the duration is `updatedAt − startedAt`
(`EVIDENCE/0161/verification/hosted/hosted-runs-89f21f5.json`). They are not charged to the protocol §9 cap.

| Run ID | Workflow | Event | Conclusion | Started (2026-10-12) | Updated (end) | Duration |
|---|---|---|---|---|---|---|
| 38322795453 | snyk | push | success | 23:33:55Z | 23:34:47Z | 52 s |
| 38322799666 | snyk | pull_request | success | 23:33:58Z | 23:34:40Z | 42 s |
| 38322799631 | parity | pull_request | success | 23:33:58Z | 23:38:50Z | 4 m 52 s |
| 38322799707 | repro | pull_request | success | 23:33:58Z | 23:39:17Z | 5 m 19 s |
| 38322799742 | python | pull_request | success | 23:33:58Z | 23:48:07Z | 14 m 09 s |
| 38322799650 | rust | pull_request | **failure** | 23:33:58Z | 23:54:23Z | 20 m 25 s |
| 38322799687 | gpu | pull_request | success | 23:33:58Z | 00:29:16Z (2026-10-13) | 55 m 18 s |

The `rust` run failed in exactly one of its ten jobs, `audit` (job 115054529384, 23:34:01Z → 23:37:08Z); `fmt`,
`docs`, `clippy`, `clippy-strict`, `test-strict`, `bench-smoke` and `test` on ubuntu, macOS and Windows all succeeded
(`H3-hosted-rust-jobs-38322799650.json`). The `gpu` run's `gpu-cuda` job started at 23:54:23Z, twenty minutes after the
run began; the wait was not investigated. The failure is discussed in §9. The hosted runs of any later commit are reported to the
maintainer and are not written here: a document cannot contain the result of its own commit's checks.

## 9. `cargo audit` — the one red check: new external advisories, not attributable to this session, not remediated here

- **Hosted.** `rust` job `audit` failed with "error: 5 vulnerabilities found!" and "3 allowed warnings found". All five are
  `quinn-proto 0.11.16`: RUSTSEC-2026-0341 (severity 7.5, fixed in ≥ 0.11.17), -0339 and -0342 (≥ 0.11.17), -0340 (severity 7.5,
  ≥ 0.11.18) and -0338 (≥ 0.11.18). Verbatim log: `EVIDENCE/0161/verification/hosted/H1-…`.
- **It is new since the previous hosted run.** The same job passed on `R` (job 114849834855, 14:07:32Z → 14:10:36Z) after loading
  **1,299** advisories and reporting only the 3 allowed warnings; at 23:37Z the database held **1,307** (`H2-…`).
- **Reproduced locally** (`R08`, `cargo audit` at `89f21f5`, exit 1): the same five vulnerabilities and the same three allowed warnings
  (bincode RUSTSEC-2025-0141, paste RUSTSEC-2024-0436, chacha20 yanked: the standing DV-008, DV-017 and DV-035 dispositions). Its
  yank check also timed out on the network ("request could not be completed in the allotted timeframe"), which does not change the result.
- **Not attributable.** `Cargo.lock` and every `Cargo.toml` are unchanged since `R` (the diff `fae24c4..89f21f5` touches no dependency
  manifest), and E3 adds no dependency. `cargo audit` is not one of the legs the 0160 gate listed because no dependency changed; it
  is a periodic control whose result can change without a change to the repository, and this is such a change.
- **Reachability.** The lockfile records `reqwest 0.12.28 → quinn 0.11.11 → quinn-proto 0.11.16`, and `reqwest` is reached through
  `tracel-llvm-bundler` (the MLIR toolchain of `cubecl-cpu`). `cargo tree --workspace --all-features --target all -e all -i quinn-proto`
  prints "nothing to print": the package is in no resolved dependency graph of any workspace feature set or target, so no PRIN build compiles or
  links it. `cargo audit` flags it because it is in the lockfile.
- **Disposition: not remediated in E3.** Changing a dependency is outside an execution-only session and is the maintainer's decision.
  Options for the maintainer: (a) a governed, lockfile-only update (`cargo update -p quinn-proto`, to ≥ 0.11.18) with `cargo audit`, Snyk
  Open Source and the full gate; or (b) a dated Deferred Validation row carrying the non-reachability evidence above. Plan amendment
  #50 says a red hosted job is dispositioned like a red local leg, and Development Workflow §3 dispositions a red nightly like a red
  push: fixed, or given a dated DV row, before the next work package closes. I opened no DV row and changed no file for it.
- **Effect on EXP-002:** none. The five records were produced before the advisories entered the database, EXP-002 exercises no Rust numerics,
  and no EXP-002 input depends on the lockfile.

## 10. Cold reviews, adjudication, validator revision 3, and a clarification of "not examined"

Entered 2026-10-13T00:31Z. Two read-only cold reviews ran on `89f21f5`: **Antigravity**
(`gemini-3.8-flash-high`, 2026-10-12 23:35Z → 23:50Z, report with no finding) and **Devin** (`swe-2-high`, 23:35Z → 23:42Z, twelve items
F-01…F-12, none High). Both were forbidden from
opening the raw result files and the retained roots and from comparing digests across arms; I scanned both reports and neither contains
outcome content or a statement about equality or difference of digests. Task files, verbatim reports and the adjudication are in
`EVIDENCE/0161/verification/delegation/`. I checked every item against the repository before acting on it.

- **What was real.** Validator revisions 1–2 were less strict than the driver's own closure in several details, and their self-tests did not
  cover the publication modes or the retention checks (F-01 symlink/junction ancestors; F-02 `10.0` and `true` accepted as integers; F-03 duplicate
  JSON keys; F-04 subset instead of exact key sets below the envelope; F-05 UTC offset, finite and consistent timing; F-06 manifest typing and a
  tail-only `out_dir`; F-07 missing mutations). None of this could have changed an admissibility result here, because the driver's closure had
  already passed on every record (exit 0), but it weakened the claim that the validation was independent.
- **What I did.** Validator **revision 3** (SHA-256 `310e1c21a231cc72955a1942c6ae1bc8b6aad37d8d6efe54983e183384617c87`) adds checks S1–S6
  for those items. It **re-validated all five records: 81, 80, 87, 87 and 87 checks, 0 failed**
  (`*.validation.rev3.txt`). A new self-test (`mutation_test_rev3.py`, SHA-256 `a5aabc9682cf3c3f59bc1022cc14a42fb452a7587bab70026de06f6d4422d199`)
  runs 40, 41, 49, 49 and 49 cases per mode, covering the publication modes, the retention checks (F1–F4), duplicate keys, a junction ancestor, a
  wrong label and a stale manifest digest: every case behaved as expected and none was skipped. Snyk Code over the ten committed Python scripts
  is clean at the governed threshold (`G14c`). Revisions 1 and 2 and their transcripts are kept. No record, registered input, protocol text or
  driver changed, and no admissibility outcome changed.
- **What I did not change.** `crossleg_consistency.py`, `staged_bytes_check.py`, `measure_bytes.py` and `run_leg.ps1` are unchanged because
  their captures are bound to the committed files; the limitations Devin found in them (F-08…F-11) are recorded in the adjudication and none
  affects a result here. The driver's own gaps (junction ancestors, last-wins JSON, subset key checks) are frozen with the driver; they are
  disclosed here for E4/E5, and rev3 shows that none occurs in these records.
- **Antigravity's citations.** Accurate except two imprecise line references (the freeze statement is at `log.md:204-207`, and the Rust test
  total is a sum, not one line); recorded in the adjudication, no action.

**Clarification (2026-10-13T00:31Z) of an earlier phrase.** Entries §4–§5 say the observation payloads "were not examined at E3" and that
a cross-leg script "never opened an observation payload". Precisely: no person and no tool compared, printed, summarised or interpreted any
observation **value**. The validators and scripts did parse the complete JSON documents; the validators read observation **structure**
(key sets, types, cardinalities, identities, and the Boolean *types* of each claim case's `expected` and `observed`, never their values);
`crossleg_consistency.py` also read the `renderer` capture on the three publication legs and nothing else from `observations`; and the
retention checks read the retained publication bytes only to hash them against the record's own digests. Nothing in this clarification
changes any other statement.

## 11. State at the close of E3

- **Commits.** `92cf696` (`.gitattributes` rule only) and `89f21f5` (records, log, evidence, gate) are pushed; the commit that carries §8–§11 and
  the rev3 evidence follows them and cannot name itself.
- **Sessions.** 0161 `COMPLETE`; 0162 `READY`. The E3 exit gate is met: all five registered runs are logged, none was aborted or rerun, and the raw
  records are manifested and byte-exact in git (`G16`, and rev3 validation of every record).
- **Caps at the close.** EXP-002 raw/record artefacts newly tracked: 392,132 B in `89f21f5` (§7) plus about 11 kB in the follow-up
  commit (this log's §8–§11 and the README / CHANGELOG notes), about 0.38 MiB of the 10 MiB cap; the per-run and campaign-wide figures
  of §7 are unchanged. The evidence bundle grows by about 0.36 MiB in the follow-up and is not an EXP-002 raw/record artefact.
- **Open items carried, none an experiment matter:** the red hosted/local `cargo audit` (§9, maintainer decision); the installed extension that
  predates three Rust commits (§2.6); DV-033 and the standing Deferred Validation items, unchanged.
- **Not run:** a forced nightly; Linux and macOS; `pip-audit` and Snyk Open Source (no dependency change).
- **No verdict.** No hypothesis verdict was computed or implied anywhere in this log.

## 12. Round 2 of the cold reviews (follow-up commit `e425971`) and what it changed

Entered 2026-10-13T00:45Z. The same two reviewers, with the same read-only rules, reviewed the follow-up commit between 00:34Z and 00:42Z:
**Antigravity** reported one item and **Devin** eight (none High); neither report contains outcome content. Task files, verbatim reports,
the diffs they were given and the adjudication (a new "Round 2" section) are in `EVIDENCE/0161/verification/delegation/`. Antigravity
recomputed every duration, sum and count in §8–§11 and found them exact, and confirmed the `cargo audit` narrative against the cited files. I verified each item before
acting:

- **Fixed (documentation).** The adjudication cited the "not examined" clarification at log "§8"; it is in §10 (Antigravity). Corrected in the
  adjudication.
- **Checked on the real tree instead of changing the validator.** Devin noted that validator revision 3's link checks (S1) cover the retained
  root's ancestors but not `publication/`, `inputs/` or entries inside them (R2-01). A reparse-point scan of the raw record root, the retained
  generated-output root and the evidence bundle, and of every ancestor of each, found **no reparse point** (`legs/reparse-point-scan.txt`).
- **Disclosed.** Revision 3's repository-state check differs from revision 2's: it compares the frozen paths (product, driver, shared benchmark
  code, tests, tools, paper, parity, the protocol and e2-review) with `R` instead of requiring a clean tree, because after the E3 commit the tree is
  legitimately no longer "`R` plus the record". It no longer reports dirty or untracked files elsewhere. The stricter revision-2 checks passed on every
  record at its leg, and the full `git status` was recorded after every leg (R2-02).
- **Accepted as limitations, with reasons in the adjudication:** retention lines are absent when a relocated publication copy is validated without
  `--generated-root` (R2-03); a genuine record with a null font-cache digest is rejected on purpose, because protocol §5.4 requires that digest
  (R2-04); a wall-clock step of more than 1 s would false-fail S5 (R2-05); mutation-test precision and extra ideas (R2-06); two `merge-base`
  calls without a timeout (R2-07); the harness's `mklink` and `rmtree` behaviour on my own scratch path (R2-08).

No record, registered input, protocol text or driver changed in this round, and no admissibility outcome changed. This entry and the
evidence it cites are carried by the commit that follows `e425971`.

<!-- LOG-TAIL: append new entries above this line -->
