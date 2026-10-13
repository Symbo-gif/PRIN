# Session-0161 evidence (EXP-002 E3 — execution)

Session 0161, 2026-10-12 UTC. This directory holds the evidence behind the E3
execution log
([`log.md`](../../DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/log.md)):
the launch records and the independent per-record validation of the five registered
runs, the tools that produced them, the re-captured pre-flight facts, the Windows
local gate, the hosted results and the read-only cold reviews. It contains **no
experiment result and no analysis**: the raw records are under
`benchmarks/results/EXP-002/`, and the generated publication roots stay outside git
(`DOCS/test_and_benchmark_results/EXP-002/`, retained until the E5 report is accepted).
No hypothesis verdict was computed in this session.

Every file under `verification/` is hashed in `verification/SHA256SUMS.txt`
(`sha256sum`-style, binary mode, paths relative to `verification/`). This README and
that manifest are the only unhashed files. `.gitattributes` keeps `EVIDENCE/0161/**`
byte-exact; that rule landed alone in its own commit, before any file here. Captures
that come from the gate are headed with command, working directory, source state, UTC
start, host and actual exit code; failed or diagnostic legs keep their names and are
never relabelled.

- `verification/legs/` — for each of the five legs, in registered order:
  - `legN-<mode>.meta.txt` — the launch record written by `tools/run_leg.ps1`: exact
    command, run ID, UTC start and end, exit code, wall time, `git status` after the leg,
    and the run directory's entries;
  - `legN-<mode>.stdout.txt` / `.stderr.txt` — the child's output (all ten are empty);
  - `legN-<mode>.validation.txt` — the independent per-record validation transcript. For
    legs 1–2 this is validator **revision 1**; `*.validation.rev2.txt` is revision 2 on the
    same record (byte-identical output). Legs 3–5 were validated with revision 2 only. After
    the cold review (below) **all five records were re-validated with revision 3**
    (`*.validation.rev3.txt`: 81, 80, 87, 87, 87 checks, 0 failed);
  - `leg1-api.mutation-selftest*.txt`, `leg2-conclusions.mutation-selftest*.txt` — the
    validator's mutation self-test on scratch copies of the leg-1 and leg-2 records. The
    unsuffixed leg-2 transcript is revision 1 and **keeps its one `BAD` case** (a result file
    corrupted into invalid JSON made revision 1 crash instead of failing a check); the
    `.rev2` transcripts are 17/17. `legN-*.mutation-selftest.rev3.txt` are the revision-3
    self-tests for every mode (40, 41, 49, 49 and 49 cases, all as expected), including the
    publication modes and the retention checks;
  - `leg3/4/5-*.listing-digest.txt` — the publication listing digest of each publication
    root (the e2-review.md §8 command, verbatim output);
  - `crossleg.txt` — metadata-only consistency across the five records (environment,
    identity, config, renderer / font stack); no observation payload is read;
  - `bytes-after-legs.txt` — tracked-byte totals against the registered caps.
- `verification/tools/` — `run_leg.ps1` (launcher), `validate_run_record.py` (revision 2),
  `validate_run_record.rev1.py` (revision 1, reconstructed by `reconstruct_rev1.py` and
  accepted only because its SHA-256 equals the digest recorded in `log.md`),
  `validate_run_record_rev3.py` (revision 3: the strictness the cold review found missing),
  `mutation_test.py` and `mutation_test_rev3.py`, `crossleg_consistency.py`,
  `measure_bytes.py`, `staged_bytes_check.py`, `preflight_recapture.ps1` and
  `make_sha256sums.py` (writes `SHA256SUMS.txt`). The validators validate record structure and
  identity only and never evaluate or compare an outcome.
- `verification/preflight/` — `preflight-recapture.txt` (the read-only pre-flight facts
  re-captured after leg 5 while the tracked tree was still clean, including a second
  passing admission dry check) and `hosted-runs-fae24c4.json` (the verbatim
  `gh run list --commit` output for the execution source `R`).
- `verification/gate/` — the Windows local gate (authoritative under Plan amendment #48) on
  `92cf696` (`R` plus the `.gitattributes` rule) with the session-0161 changes staged: the
  Python legs `G*` and the Rust legs `R*`, in the leg list of `EVIDENCE/0160/verification/gate/`.
  Every capture is headed with command, working directory, source state, UTC start and host,
  and ends with elapsed seconds and the actual exit code. The final candidate's legs are
  `G01`–`G14`, `G17`, `G18` and `R01`–`R07`, all exit 0. Leg `G15` (pip-audit and Snyk Open
  Source) is **not applicable**: no dependency manifest changed. `G16` is the staged
  byte-exactness check (`tools/staged_bytes_check.py`): it compares every staged raw record
  and every evidence file with the working tree and with the manifests. It replaces 0160's
  manifest test, because this session adds no manifest test. `G16` and `G18` were captured
  before those two files were added to the index (a capture cannot contain itself); both were
  then added and hashed.
  Kept diagnostic and failed captures, never relabelled:
  - `G10fa` — `git diff --cached --check` failed on two trailing spaces I had left on the
    modified `Status` line of the 0162 brief; fixed and re-run as `G10f`;
  - `G09a`, `G12a` — the first focused and fast pytest attempts were started from PowerShell,
    where `bash` resolves to `C:\windows\system32\bash.exe` (the WSL launcher). WSL's VM did not
    start (`HCS_E_CONNECTION_TIMEOUT`), so four `tests/test_wp001_baseline.py` release-workflow
    tests that shell out to `bash` failed (`G09a`: 4 failed, 456 passed); `G12a` was stopped
    mid-run for that reason and has no exit-code footer. The gate was restarted from Git Bash,
    whose `bash` is Git's (as in sessions 0159 and 0160), and every leg was re-run there;
  - `G14a` — the first Snyk Code scan, over the seven tool scripts that existed then;
    `G14b` — the scan over nine files, which added the scratch gate harness
    (`run_gate.py`, SHA-256 `0488b6b25b328d49f7e43915aa6e3b1669790c0e47c71f048fec6e554812eede`) and
    reported one Medium finding (Command Injection: the harness's log-directory argument flowed
    into `subprocess.Popen` arguments). The harness is scratch tooling that only sequenced the
    commands recorded in each log's `COMMAND:` header, so it was **not committed**; `G14` is the
    clean scan (0 issues at the governed `medium` threshold) of the eight scripts that are.
  `G09-focused-coverage.json` is the focused leg's coverage report for
  `benchmarks.campaign.exp002_driver`. `G14*-sast-copy-attestation*.txt` list the SHA-256 of the
  exact files each Snyk scan read.

  Captured after the commit `89f21f5` was pushed:
  - `G14c` — Snyk Code over the ten committed scripts (adds validator rev3 and its self-test):
    0 issues at the governed `medium` threshold;
  - `G17b` — gitleaks over the full history at `89f21f5`: 720 commits, no leaks;
  - `R08` — **`cargo audit` on the unchanged `Cargo.lock`: exit 1, five vulnerabilities, all
    `quinn-proto 0.11.16`** (RUSTSEC-2026-0338/-0339/-0340/-0341/-0342, new in the advisory
    database since the earlier hosted run on `R`: 1,299 → 1,307 advisories). It reproduces the
    failed hosted `audit` job. `quinn-proto` is in the lockfile only through the optional
    `quinn` dependency of `reqwest` (via `tracel-llvm-bundler`); `cargo tree` finds no path to it
    in any feature set or target of the workspace. It is **not attributable to this session, not
    remediated here** (a dependency change is outside E3's remit) and is reported to the
    maintainer for a decision. `R08` is not part of the 0160 leg list; it was added because the
    hosted audit failed.
  - `gate/delta-follow-up/` — the documentation delta gate on the follow-up commit that carries
    the rev3 evidence, the cold-review record and log sections 8–11: governance legs `G10`–`G10f`,
    the Sphinx `-W` full rebuild `G11`, gitleaks on the staged diff `G18` and the staged byte check
    `G16b`, all exit 0. Only documents and evidence changed, so the product, test and Rust trees are
    byte-identical to the fully gated candidate and the pytest and cargo legs were not repeated.
- `verification/hosted/` — the hosted results (Plan amendment #50, additional evidence only):
  `hosted-runs-89f21f5.json` (all seven runs for the pushed head), `H1-…audit-failed-…log` (the
  verbatim `--log-failed` of the one red job) and `H2-…advisory-counts.txt` (the earlier passing
  `audit` job on `R`, for the advisory counts).
- `verification/delegation/` — the Antigravity and Devin cold reviews: task files, verbatim stdout,
  run windows, the diffs given to them, and `adjudication.md` (every finding verified before any
  action; no finding implicated the protocol, the driver, the registered inputs or the data).
