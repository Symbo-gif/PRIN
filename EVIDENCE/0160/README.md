# Session-0160 evidence (EXP-002 E2 — review and approval)

Session 0160, 2026-10-12 UTC. This directory holds the E2 review's verification
evidence, the fixes for the hosted failures and the flaky test fixture that
were made in the same session, the approved-source local gate, and the
read-only cold reviews. It contains no EXP-002 run, registered input, or
generated publication output.

Every file under `verification/` is hashed in `verification/SHA256SUMS.txt`
and is checked by `tests/test_0160_manifest.py`. This README and the manifest
are the only unhashed files. `.gitattributes` keeps `EVIDENCE/0160/**`
byte-exact; that rule landed alone in `ed993e9`, before any file here.
Captures are headed with command, working directory, source state, UTC start,
host and actual exit code. Failed or diagnostic legs keep their names and are
never relabelled.

- `verification/e2-review/` — the E2 checks cited in
  [`e2-review.md`](../../DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/e2-review.md):
  - E1: static re-derivation of the E1 claims (28 checks).
  - E2: exhaustive check that the Lean models match real Python I/O.
  - E3: Z3 equivalence of the driver's PNG colour rules with the PNG
    specification, plus a non-vacuity probe.
  - E4: the Lean 4 proof `CrlfCanonical.lean`.
- `verification/test-reliability/` — the `WinError 32` reproduction:
  - W1: pytest's own lazy `--basetemp` deletion errors at setup.
  - W2: the `tests/conftest.py` hook passes in the same scenario.
  - W3: a holder that never releases becomes one clear usage error.
- `verification/ci-fixes/` — the two failed hosted jobs on `0d4278d`
  (verbatim `--log-failed`), and `mypy` in a venv that mirrors the hosted
  lint job: without numpy (C3a fails exactly as CI did) and with the
  pinned numpy (C3c passes). H1 is the green forced nightly on `0d4278d`.
  For `9a9889d`: H3 lists the hosted runs (every pull-request workflow
  green), H2 is the forced nightly's metadata, and H2a/H2b are its failed
  `bench-regression` step in attempts 1 and 2 (verbatim `--log-failed`;
  dispositioned as measurement variance in `e2-review.md` §6).
- `verification/gate/` — the approved source's Windows local gate (G* and
  Rust R*), Snyk Code (G14; G14b/G14c show three pre-existing Low findings
  below the governed Medium threshold), pip-audit and Snyk Open Source for
  the numpy pin (G15, G15b), the post-package manifest tests (G16) and
  gitleaks (G17 full history, G18 staged). Kept failures: G16a (the ignored
  `*.log` files were not yet force-added), G10fa (a
  trailing space), G11a (a CHANGELOG link Sphinx cannot resolve) and G12a
  (an access violation in `os.walk` in the WP-001 inventory test; native
  root cause not proven, mitigated by the git-scoped inventory). From the
  void run 4, also kept: G09a (round-3 files not yet packaged), G12b (two
  timing-sensitive tests on a host that was not idle; cause not established)
  and G13b (that run's full suite, 6,047 passed, kept for completeness).
  See `e2-review.md` §7.
- `verification/delegation/` — task files and verbatim stdout of the
  Antigravity and Devin read-only cold reviews, and the adjudication notes.
