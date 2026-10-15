# PR #33 review round — evidence (session 0159, 2026-10-11 UTC)

Evidence for [`DOCS/audits/PR033-multi-review-audit.md`](../../../../DOCS/audits/PR033-multi-review-audit.md).
Every file here is hashed in `../SHA256SUMS.txt`. Captures are headed with their
command, working directory, source state, UTC start, host, elapsed time and
actual exit code; failed legs are kept and labelled, never relabelled.
No file here records an EXP-002 run, a registered input or a generated
publication output.

## Ground truth (before any fix)

- `ground-truth-probes.py.txt`, `ground-truth-probes-p9-symlink.py.txt` — the
  auditor's probe sources (synthetic inputs only; the real PRIN and pinned
  reference *writers* are called on a synthetic table and figure, never a
  generator over the registered snapshot).
- `P1-ground-truth-probes-78d3600.log`,
  `P1b-ground-truth-probes-p9-symlink-78d3600.log` — the probes against a
  clean detached worktree of the reviewed head `78d3600`. They reproduce
  the defects: CRLF tables unequal, PDF Info key-set and wrap residue,
  `ValueError` on an oversized `startxref`, PLTE after IDAT accepted,
  `ManifestMismatchError` outside `main()`'s catch list, fabricated
  provenance and a mislabelled `implementation` accepted at closure, an
  orphan RUN directory, a sibling symlink failing an unrelated closure, and a
  stray non-JSON file accepted.
- `P1c-…-remediated.log`, `P1d-…-remediated.log` — the same probes against the
  remediated working tree, for contrast. Some probes now stop at the new
  guards; that is the fix, not a probe failure.

## Remediation proof and gate

- `proof_defect_catching.py`, `proof_plugin.py` — mutation proof. Each
  remediated driver finding is rebuilt as a one-substitution mutant of the
  current driver, loaded under the real module name; its regression tests
  must fail on the mutant and pass on the fixed driver.
  `P2-mutation-proof.log` records the result.
- `G*.log` — the local gate legs on the remediation source (see the audit §6
  for the leg table).
- `gitleaks-*.json` — redacted secret-scan reports.

## Delegation (read-only cold reviewers)

`delegation/` keeps the task files and verbatim stdout of the Antigravity
(`gemini-3.1-pro-high`) and Devin (`swe-2-high`) runs, in both the
ground-truth round and the self-audit round. They are reviewer input, not
evidence of any fact: the audit re-derives every claim it uses, and it
records where a delegated report misquoted the repository.
