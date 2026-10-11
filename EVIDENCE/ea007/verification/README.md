# EA-007 verification evidence

Preserved per-command verification logs from the EA-007 full local gate
(host `HP`, base SHA `fdd28d88e4c57d544e5d30fa52cce85807ab15a9`,
branch `audit/ea007-exp002-readiness`, Plan amendment #48 local-validation
regime). Text artifacts only — no binaries, virtual environments, or
generated HTML are committed here.

- `full-gate/` — every gate-leg log (each embeds its command, host and UTC
  time; most also the SHA and an `EXIT_CODE` — see the census in
  `GATE-STATUS.md`), plus `GATE-STATUS.md` (the leg-by-leg index), the redacted
  `gitleaks-redacted.json` report (`[]` — no leaks), and the resolved
  dependency manifest used for the governed Snyk SCA scan
  (`prin-requirements.txt` / `prin-resolved/requirements.txt`).
- `dv042-*.log`, `dv042-gpu-rs.diff` — DV-042 pre-fix rustdoc failure
  reproduction and post-fix wgpu/cpu/cuda legs.
- `dv040-*.log` — DV-040 coverage probes (incl. the vacuous-bandit and
  frozen-Markdown findings) and the old-vs-new config regression-test
  proof runs.
- `ea007-check-*.log` — offline governance checkers (deviation ledger
  038→039, DV-register gates, global session registration).
- `post-commit/` — the verbatim post-commit full-history gitleaks scans
  (706 commits @ `0738714`, 707 commits @ `add7386a`, 709 commits @ `0a0f700`; all
  no leaks, exit 0; plus the default-view scan of `0a0f700` that reports the one
  already-approved false positive in a shallow repository),
  copied byte-exact from the gitignored local scratch tree (PR #32 review
  round, `PR32-F2`).
- `pr32-review/` — the PR #32 review round's local gate (`PR32-F1`…`PR32-F15`):
  `pr32-gate-run.log` (legs L00–L20, verbatim, user-profile paths redacted),
  `full-suite-0a0f700.log` (the full Python suite on the remediation head),
  `pr32-source-hashes.txt` (SHA-256 of the edited first-party files, the proof
  harness, and the uncommitted serial runner), `pr32-staged-gitleaks.json`
  (`[]`), and `proof_defect_catching.py` (the host-specific harness behind leg
  L11 — evidence tooling, not part of any CI gate). The serial runner that
  produced the log is deliberately not committed (it hard-codes host paths and
  Snyk Code flags its environment-variable plumbing); each leg's `COMMAND:` line
  is the reproducible unit.
- `SHA256SUMS.txt` — SHA-256 inventory of every file in this directory
  except itself, plus the three frozen top-level artefacts one level up
  (`../readiness-state.json` and the two `../*.log` captures). Verify with
  `sha256sum -c SHA256SUMS.txt` from this directory, or with
  `pytest tests/test_ea007_manifest.py`, which also fails on any evidence
  file the manifest omits (`PR32-F7`).

Headline result: full uninterrupted pytest passed — 5,667 passed /
184 skipped / 0 failed / 61 warnings in 1,782.21 s (leg 25,
`full-gate/25-pytest-final.log`). Final required executable checks passed;
earlier timeout/scan-failure artifacts retained; Python coverage blocked,
hosted/platform gates suspended (DV-033 and amendment #48 retained).
