# EA-007 verification evidence

Preserved per-command verification logs from the EA-007 full local gate
(host `HP`, base SHA `fdd28d88e4c57d544e5d30fa52cce85807ab15a9`,
branch `audit/ea007-exp002-readiness`, Plan amendment #48 local-validation
regime). Text artifacts only — no binaries, virtual environments, or
generated HTML are committed here.

- `full-gate/` — every gate-leg log, verbatim command/host/SHA/UTC/exit
  code each, plus `GATE-STATUS.md` (the leg-by-leg index), the redacted
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
- `SHA256SUMS.txt` — SHA-256 inventory of every file in this directory
  (verify with `sha256sum -c SHA256SUMS.txt` from this directory).

Headline result: full uninterrupted pytest passed — 5,667 passed /
184 skipped / 0 failed / 61 warnings in 1,782.21 s (leg 25,
`full-gate/25-pytest-final.log`). Final required executable checks passed;
earlier timeout/scan-failure artifacts retained; Python coverage blocked,
hosted/platform gates suspended (DV-033 and amendment #48 retained).
