# Hosted-check failure record: PR #40 (EXP-002-r1 E4)

Recorded verbatim under plan amendment #52. The failure is not waived, skipped
or hidden; no workflow or required check was edited.

- **Workflow / job:** `snyk` / `Secret Scan` (`gitleaks/gitleaks-action@v3`, gitleaks 8.24.3)
- **Runs:**
  - pull_request `39719901599` (job `119630722584`): https://github.com/Symbo-gif/PRIN/actions/runs/39719901599
  - push `39719743625` (job `119630216484`): https://github.com/Symbo-gif/PRIN/actions/runs/39719743625
- **Head SHA:** `1f0f1b91594a9114d1f70625df0c8602c3b572bd` (branch `campaign/exp002-r1-e4`)
- **Conclusion:** failure (exit 2), `leaks found: 2`, rule `generic-api-key`
- **Locations:**
  `DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/analysis/summary.json:270-271`
  (`public_api_sha256`, `reference_api_sha256`)
- **Fingerprints:** `1f0f1b91594a9114d1f70625df0c8602c3b572bd:<that path>:generic-api-key:270` and `:271`

## Triage

False positive. Both values are 64-hex SHA-256 content digests:

| Key | Digest (source file) | Corroboration |
|---|---|---|
| `public_api_sha256` | `dd5745ababa809483b8d52198a096a1e9fa0de7e13e246245b13f47066853a6d` (`python/prin/_public_api.py`) | `preregistration.md:73,113`; `exp002_r1_e4_analysis.py:447` |
| `reference_api_sha256` | `ede92afc6771f2e29206534905e2820598ba841662a93d59f669f803a382f182` (`REFERENCE/src/prinet/__init__.py`) | `preregistration.md:78,120`; `exp002_r1_e4_analysis.py:444`; already approved at `EVIDENCE/0159/entry-state.json:87` (PR33-F34) |

The `api` token in the key names triggers the `generic-api-key` rule. Why the
existing `.gitleaksignore` did not cover these: its fingerprints embed commit
SHA, path and line, so they match only the exact commit that introduced them.

## Secondary warning

`Resource not accessible by integration` when gitleaks-action tried to comment
on the PR (`snyk.yml` grants `pull-requests: read`). Non-blocking; findings
still reach the job summary and SARIF artifact. No permission change made.

## Other checks on this head

All green: python `39719901603`, rust `39719901717`, parity `39719901694`,
repro `39719901639`, gpu `39719901666`, Snyk Code.

## Remediation

Maintainer (MichaelMaillet) approved the narrowest option on 2026-10-22: add
exactly two commit-bound fingerprints for `1f0f1b9…` to `.gitleaksignore`, in a
new commit on top (no amend or force-push, so the fingerprints stay valid and
the red runs remain in history). `.gitleaks.toml` and all workflows are
unchanged. The PR-event scan covers only `head^..head`, so the next run is
expected to scan the remediation commit alone; the suppression is therefore
recorded here rather than relied on to turn the check green.
