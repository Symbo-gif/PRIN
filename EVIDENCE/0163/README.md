# Session-0163 evidence (EXP-002 E5 — report)

Session `0163`, 2026-10-14 UTC. This directory holds the verification evidence behind the EXP-002 E5 report ([`report.md`](../../DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md)): the read-only pre-flight checks, the Step 1 retained-bytes verification, the Step 2 clean-worktree regeneration of the seven E4 analysis outputs and `report-manifest.json`, the Step 3 protocol §8.2 reconstruction of the 39 publication files, the Step 4 independent recount, the Step 8 read-only cold reviews and programmatic self-audit, and the Step 7 documentation/evidence delta gate.

Every file under `verification/` is hashed in `verification/SHA256SUMS.txt` (`sha256sum`-style, binary mode, paths relative to `verification/`). This `README.md` and `verification/SHA256SUMS.txt` are the only unhashed files. `.gitattributes` keeps `EVIDENCE/0163/**` byte-exact (`-text whitespace=-trailing-space`); that rule landed alone in its own commit (`79a91a60d1f27be64317083d94003381f1ac19d6`) before any file in this directory was staged.

- `verification/preflight/` — read-only entry state at `HEAD = cad9a8c502bfd38800594336663f621990bb8b22`:
  - `preflight-summary.txt` — git/branch/PR #33 state, diff against `R = fae24c4`, host hardware/OS/RAM/CPU load, Python/Rust/renderer/font/security toolchain versions, and active GitHub workflows;
  - `anchors.txt` — `sha256sum` of `preregistration.md`, `paper/artefact_manifest.json`, `analysis/exp002_e4_analysis.py`, `report-manifest.json`, `python/prin/_prin_core.pyd`, and all 15 files across the five E3 `RUN-` directories;
  - `rev3-validation-{api,conclusions,reference,prin,repeatability}.txt` — read-only re-validation of the five E3 records with `EVIDENCE/0161/verification/tools/validate_run_record_rev3.py` (`80/81`, `79/80`, `86/87`, `86/87`, `86/87` checks passed; the single `FAIL` on each record is `G1`, which diffs `R = fae24c4` against the working tree across `frozen_paths` including `tests/` and flags `tests/test_exp002_e4_analysis.py` added at E4 commit `3731fc2`, while all record, manifest, provenance, schema, and `F1`–`F4` retention checks pass);
  - `hosted-cad9a8c.json`, `pr33-statusCheckRollup-cad9a8c.json`, `rust-38447171301-jobs.json`, `gpu-38447171376-jobs.json` — verbatim GitHub CLI captures of the hosted runs and PR #33 status check rollup for the tested head `cad9a8c502bfd38800594336663f621990bb8b22` (`python`, `parity`, `repro`, `snyk` PR/push green; `rust` red in `audit` only on `quinn-proto 0.11.16`; `gpu` red in `gpu-cuda` only on `prin-train` `flops::tests::measure_wall_time_calls_warmup_and_runs_exact_counts`).
- `verification/retained-bytes/` — Step 1 (executed first, before reconstruction; protocol §11.3 item 2, E2 decision 8):
  - `listing-digests.txt` — verbatim execution of the `e2-review.md` §8 PowerShell one-liner on the three retained `publication/` roots (`reference` `d674de7d4b5830c9abf525fcc484a5ebc01e3620ca38b63badd037e289487323`; `prin` and `repeatability` `c1ca4ada167c50a28db2dfe4365d004cdb3621903f43e38cc6de75c2e4904669`);
  - `retained-bytes-verification.txt` — independent read-only, no-follow (`lstat` + reparse-tag) verification of all `39/39` retained files under `publication/` (`1,502,048 B` in `reference`; `1,500,705 B` in `prin` and `repeatability`) against each run's manifested `reproduction.json` and all `172/172` retained files under `inputs/` (`16,047,018 B` per run) against `paper/artefact_manifest.json`.
- `verification/regeneration/` — Step 2 and Step 4:
  - `worktree-regeneration.txt` — detached worktree `C:\dev\PRIN-0163-e5-wt` at `cad9a8c`, execution of `python -I .../exp002_e4_analysis.py` (`49.402 s`, exit `0`), and byte-for-byte identity verification of all 7 analysis outputs and `report-manifest.json` (`8/8` files identical), followed by worktree removal;
  - `independent-recount.txt` — standalone stdlib-only recount of H1 (`175/175`, `172/172`), H2 (`62/62`: `5/42/4/5/6`), H3 (`21/39` approved, `5/39` sensitivity, `11/11` PRIN tables vs archived), and H4 (`39/39` raw-identical) from the five raw records, cross-checked against the E4 outputs (`0` discrepancies).
- `verification/reconstruction/` — Step 3 (protocol §8.2):
  - `reconstruction.txt` — verification that the current renderer/font environment equals the E3 records before and after rendering, followed by `collect_reproduction` for `reference` and `prin` into a fresh gitignored scratch directory (`prin`: `39/39` raw-identical, `39/39` normalized-identical, `39/39` sensitivity-identical, listing digest `c1ca4ada…`; `reference`: `25/39` raw-identical — `14/14` PNGs, `11/11` tables, `0/14` PDFs due to unpinned reference PDF `CreationDate` — and `39/39` normalized/sensitivity-identical).
- `verification/delegation/` — Step 8 cold reviews and self-audit:
  - `cold-review-task.md` — the read-only review prompt naming all 29 permitted file paths and forbidding access to the retained roots, the reference tree, and PR #33 comments;
  - `agy-round1-{run,report}.txt` and `agy-round2-{run,report}.txt` — two completed read-only review rounds with `agy --model gemini-3.8-flash-high --mode plan --output-format text` (disclosed as same-family as the E5 author `Gemini 4 Argon High`);
  - `devin-attempt1-{run,report}.txt` — verbatim capture of `devin --model swe-2-high --respect-workspace-trust false -p …` exiting `1` (`Error: Not logged in. Run devin.exe auth login to authenticate.`);
  - `gpt-oss-attempt1-{run,report}.txt` and `gpt-oss-attempt2-{run,report}.txt` — verbatim captures of `agy --model gpt-oss-120b-medium` (attempt 1 stopped at a plan prompt; attempt 2 exited `3` on HTTP `503 UNAVAILABLE`);
  - `programmatic-self-audit.txt` — deterministic Python verification of all 308 digest, byte-size, figure-table, and link assertions across the E5 documents (`308/308` passed);
  - `adjudication.md` — verification and disposition of every reviewer finding.
- `verification/gate/` — Step 7 documentation/evidence delta gate (run from Git Bash on the maintainer's Windows host):
  - `G01-git-diff-check.log` — `git diff --cached --check` (exit `0`);
  - `G02-deviation-ledger.log` — `tools/check_deviation_ledger.py DOCS/reports/039-project-state.md DOCS/reports/040-project-state.md` (exit `0`);
  - `G03-dv-register-gates.log` — `tools/check_dv_register_gates.py` (exit `0`);
  - `G04-global-session-registration.log` — `tools/check_global_session_registration.py` (exit `0`);
  - `G05-skipif-probes.log` — `tools/check_skipif_probes.py` (exit `0`);
  - `G06-wp001-baseline.log` — `tools/wp001_baseline.py check` (exit `0`);
  - `G07-pytest-wp001-baseline.log` — `pytest tests/test_wp001_baseline.py --basetemp=.pytest_basetemp -o faulthandler_timeout=300` (exit `0`);
  - `G08-sphinx-html.log` — `sphinx.cmd.build -W --keep-going -b html DOCS/sphinx <fresh dir>` (exit `0`, 0 warnings);
  - `G09-gitleaks-staged.log` and `G10-gitleaks-history.log` — pinned `gitleaks` `8.30.1` on the staged diff and full history (exit `0`, 0 leaks);
  - `R08-cargo-audit.log` — `cargo audit` recorded verbatim (exit `1`, **not green**: 9 vulnerabilities — the 5 `quinn-proto 0.11.16` advisories `RUSTSEC-2026-0338`..`0342` and 4 new `2026-10-14` `rustls 0.23.45` advisories `RUSTSEC-2026-0346`..`0349` — plus 3 standing allowed warnings);
  - `G01b-post-gate-git-diff-check.log` and `G09b-post-gate-gitleaks-staged.log` — post-gate `git diff --cached --check` and staged-diff `gitleaks` after the gate captures themselves were staged (both exit `0`).
