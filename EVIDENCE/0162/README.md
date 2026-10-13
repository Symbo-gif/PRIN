# Session-0162 evidence (EXP-002 E4 — analysis)

Session 0162, 2026-10-13 UTC. This directory holds the evidence behind the E4 record
([`analysis.md`](../../DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/analysis.md)):
the read-only pre-flight, the Phase-A gate of the analysis module, the read-only cold reviews and the
post-run self-audit, the two analysis runs, the DV-040 re-audit, the final-candidate gate and the hosted
results. The seven analysis outputs themselves stay gitignored under
`DOCS/test_and_benchmark_results/EXP-002/analysis/`; their digests are in the committed
`report-manifest.json` and in `runs/`.

Every file under `verification/` is hashed in `verification/SHA256SUMS.txt` (`sha256sum`-style, paths
relative to `verification/`). This README and that manifest are the only unhashed files.
`.gitattributes` keeps `EVIDENCE/0162/**` byte-exact; that rule landed alone in its own commit
(`42f0eb3`) before any file here. Gate captures are headed with command, working directory, source,
`HEAD`, UTC start and host, and end with UTC end, elapsed seconds and the real exit code. Failed legs keep
their names and are never relabelled.

- `verification/preflight/` — the E4 entry condition: validator revision 3 re-run on the five records
  (`rev3-validation-*.txt`: 81, 80, 87, 87, 87 checks, 0 failed); the fifteen record SHA-256 anchors
  (`anchors.txt`); the hosted runs for the handoff HEAD `73dd6da` (`hosted-73dd6da.json`); and a
  re-capture of the three publication listing digests (`listing-digests-recapture.txt`, e2-review.md §8
  command). The pre-flight itself printed the same three values to the session console before any
  analysis code existed; the file was captured after the run, and its values are identical.
- `verification/gate-phase-a/` — the full local gate on the Phase-A candidate (`7d850ba` + the staged
  module and tests), from Git Bash: `G01`–`G13`, `G14` (Snyk Code on byte-identical copies of the two new
  files, with attestations; `G14a` before the cold review and `G14b` after round 1 are kept), `G17`,
  `G18`, `R01`–`R08`, and the progress list `gate-progress.txt`. **`G13` (full pytest) exited 1** on two
  host-sensitive tests unrelated to the change (the DV-032 throughput ratio, 1.60 against `< 1.30`, and a
  notebook cell that exceeded its 900 s timeout). **`G13a`** reran both in isolation as a diagnostic: the
  notebook passed and the throughput test failed again (ratio 3.32). **`R08` (`cargo audit`) exited 1**:
  the five known `quinn-proto 0.11.16` advisories (`log.md` §9); not actioned. `G09-focused-coverage.json`
  is the module's branch-coverage report. The gate script passed it a POSIX path that Windows Python
  resolved to a stray `C:\c\…` tree; the file was moved here and the stray tree removed. The host carried
  the maintainer's desktop applications during the gate, so wall times are long.
- `verification/delegation/` — the two read-only cold-review rounds of the module and tests **before any
  real run** (task files, verbatim reports, run windows, the round-2 diffs; Devin's first round-2 attempt
  stopped early on a tool that needed confirmation, and its output is kept as `*-attempt1-*`), the
  post-run self-audit (`selfaudit-*`), and `adjudication.md` (every finding verified before any action).
- `verification/runs/` — `run1.log` and `run2.log`: the exact command, `HEAD`, UTC start and end, exit
  code and the printed verdicts and digests of the two runs; byte identity of all eight files between the
  runs is recorded in `analysis.md`. `run1.log`'s computed `ELAPSED_S` line is empty because `bc` is
  missing in Git Bash; the line appended after it gives the value computed from the two UTC stamps.
- `verification/dv040/` — the DV-040 re-audit: `DV040-option-a-coverage.txt` (ruff `--show-files`,
  source-only format check, `mypy -v` sources, bandit per-file LOC, all including the new module) and the
  hosted `python.yml` `lint` job log for `3731fc2` (run `38428378236`, job `115403709218`).
- `verification/gate-final/` — the gate on the final candidate (`42f0eb3` + every session change staged;
  product, test and Rust trees identical to `3731fc2`): `G01`–`G13`, `R08`, `G17`, `G18`, all exit 0
  except **`R08` (`cargo audit`, exit 1, the same five advisories)**. **`G13` (full pytest) passed:
  6,223 passed, 184 skipped, 0 failed.** `G13v-…-VOID-…` is a first full-suite attempt that I stopped and
  voided because I wrote one file into `EVIDENCE/0162/` while it ran (the file was moved out; `G13`,
  `R08`, `G18` and `G17` were then rerun from scratch). `G10f-post-gate` and `G18b-post-gate` are the
  `git diff --cached --check` and staged-gitleaks checks after the gate logs themselves were staged.
- `verification/hosted/` — the hosted runs for the module commit `3731fc2` (`hosted-runs-3731fc2.json`;
  `rust-38428378271-jobs.json` shows the single failing job, `audit`) — Plan amendment #50, additional
  evidence only.
- `verification/tools/` — `gate.sh` and `gate-extra.sh` exactly as used for the Phase-A gate (scratch
  shell tooling that only sequences the commands in each capture's `COMMAND:` header); `gate-final.sh`
  is the same script with the `C:\c\…` path fix, used for the final gate.
