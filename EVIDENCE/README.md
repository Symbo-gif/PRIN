# EVIDENCE/ — Cycle evidence artefacts

Machine-readable and human-readable evidence files produced during Session
Cycle work (S1 handoffs, S2 audit reproductions, S3 remediation verifications,
S4 gate runs).

## Finding Evidence

Evidence files follow the naming convention `NNNN-wpNNN-sN-<slug>.<ext>`:

| Pattern | Meaning | Example |
|---|---|---|
| `NNNN` | Session number (zero-padded to 4 digits) | `0017` = session 0017 |
| `wpNNN` | Work package | `wp005` = WP-005 |
| `sN` | Session phase | `s1` = Coding, `s2` = Audit, `s3` = Remediation |
| `<slug>` | Descriptive label | `ort-probe`, `phase0-gate` |

To find evidence for a specific work package, look for files matching
`*-wpNNN-*`. For example, all WP-036F evidence starts with `0144U-wp036f-` or
`0144W-wp036f-`.

## Current contents

- [`math-audit/`](math-audit/) — Executive Mathematical Audit evidence:
  every `math-audit-mcp` `AuditResult` (`audits/<audit_id>/normalized-result.json`),
  evidence bundle (`audits/bundle-<id>/manifest.json` + `report.md`), the
  append-only `logs/audit-trace.jsonl`, and the consolidated
  `ema-run-summary.json` from `tools/math_audit_run.py`. Append-only per
  `Executive_Mathematical_Audit_Governance_and_Methodology.md` §6; a re-run
  writes fresh evidence with new `audit_id`s rather than overwriting prior
  runs.

- [`0005-wp002-s1-handoff.md`](0005-wp002-s1-handoff.md) — WP-002 S1 handoff
  to the S2 audit for the golden-trajectory corpus and differential harness.
- [`0017-wp005-s1-ort-probe.json`](0017-wp005-s1-ort-probe.json) — WP-005 S1
  ONNX Runtime provider-probe evidence (selected backend, active providers,
  model load/run result, output shape).
- [`0017-wp005-s1-phase0-gate.json`](0017-wp005-s1-phase0-gate.json) — WP-005
  S1 Phase 0 exit-gate evidence (corpus, wheel matrix, spike decisions, ORT
  probe, aggregate readiness).
- [`0109-wp028-s1-controller-provider-report.json`](0109-wp028-s1-controller-provider-report.json)
  — WP-028 S1 subconscious-controller evidence: model manifest verification and
  graph contract, the selection policy over every provider subset, real session
  attempts and their resolved backends on this host, cross-provider output
  agreement, differential parity against PRINet 3.0.0, and the measured
  batch-size sensitivity of the float32 GEMM path.
- [`0113-wp029-s1-control-buffer-pilot.json`](0113-wp029-s1-control-buffer-pilot.json)
  — WP-029 S1 latency pilot evidence: p50/p95/max read latency of the
  lock-free `ControlSignalBuffer` vs. a same-language `Mutex`-guarded
  re-implementation of PRINet 3.0's design (5 runs each) and the actual
  archived PRINet 3.0 `ControlSignalBuffer` measured directly (5 runs),
  methodology, and environment capture.
- [`0144S-wp036e-s3-changed-line-coverage.md`](0144S-wp036e-s3-changed-line-coverage.md)
  — WP-036E S3 (`0144S`) finding WP036E-F3: union changed-line coverage of the
  feature-gated GPU crates across the `nofeat/cpu/wgpu/cuda/cuda,wgpu`
  `cargo-llvm-cov` matrix (98.71 % after the one DV-004 `#[cube]` exclusion),
  the per-line residual justification, and the nine regression tests added.
- [`0144S-wp036e-s3-dv003-timing-reprobe.md`](0144S-wp036e-s3-dv003-timing-reprobe.md)
  — WP-036E S3 (`0144S`) finding WP036E-F1: DV-003 host-residual re-probe on
  `PRIN-GPU-Runner` confirming CUDA `StepReport.timing_method == "system"` and
  a bounded ~0.03 ms host residual (plan amendment #44).
- [`0144Y-wp036g-s1-dv-reverification/`](0144Y-wp036g-s1-dv-reverification/)
  — WP-036G S1 consolidated external/security/test-fragility re-verification:
  runner and secret-scanning state, native and Snyk dependency scans, DV-019
  and DV-032 repeated tests, local gates, and the transparent basetemp finding.
- [`0144U-wp036f-s1-controller-provider-report.json`](0144U-wp036f-s1-controller-provider-report.json)
  — WP-036F S1 (`0144U`) DV-006 "provider and latency acceptance" evidence for
  the re-exported controller graph (three-input `Gemm` nodes): the pristine-vs-
  re-exported `Gemm` input arities and the CPU bit-identity over the 48-case
  set, `DmlExecutionProvider` execution and its agreement with CPU
  (`max_abs_diff_vs_cpu`, `rtol=1e-5, atol=1e-6`), and the DirectML-vs-CPU
  median inference latency. Regenerate with
  `tools/wp036f_provider_latency.py`.
- [`0144W-wp036f-s3-remediation-gate.md`](0144W-wp036f-s3-remediation-gate.md)
  — WP-036F S3 (`0144W`) closure evidence for audit findings WP036F-F1 (D2,
  changed-code coverage 94 % → 100 % on the two new tools after nine added
  tests) and WP036F-F2 (D4, `mypy --strict` on both tools 3 errors → 0), plus
  the touched-area delta re-audit gate re-run.
- [`exp002-d1-s4/`](exp002-d1-s4/) — EXP-002 D1 correction, S4 (the
  documentation and closure session). A **documentation-and-evidence** session
  that changed no first-party source, so its bundle leads with a **measured**
  change set (0 `.rs`, 0 dependency manifests, 0 first-party `.py`, 0 workflow
  files) that decides which conditional gate legs apply rather than assuming it.
  It holds: the cold review that S3's four-round cap left owing
  ([`o2-review/`](exp002-d1-s4/o2-review/triage.md)) — performed read-only **by
  measurement**, reproducing every suspected defect with a command and
  classifying it CONFIRMED / REFUTED / NOT REPRODUCIBLE, which found **one
  CONFIRMED defect** (`EXP002D1-S4-F1`, D2, **latent**: `final_legs.sh`
  aggregated five legs with `grep MARKER | grep -qv OK && overall=1`, and
  `grep -qv` exits 1 on empty input, so a leg whose record was missing, empty or
  marker-less read as *passing*) with a red-before/green-after demonstration and
  a fail-closed superseding copy — plus twelve checks verifying S3's round-4
  fixes as claimed; the local gate under amendment #48 (fast suite 4044 passed
  exit 0; the required full suite run **once**, **exit 0**, 6331 passed / 184
  skipped / 0 failed in 1:43:09, under a measured host CPU median of 96.5 % with
  pytest receiving 0.192 CPU-s per wall-second; static, governance, Sphinx,
  gitleaks, Snyk Code, manifest verification and delta re-audit all exit 0);
  five immutability rules including the one append this cycle is allowed to make
  to the frozen EXP-002 record; and the `gh workflow list --all` listings before
  and after Plan amendment #52 re-enabled the seven hosted check workflows, with
  `.github/` verified unmodified. See its `README.md`.
- [`exp002-d1-s3/`](exp002-d1-s3/) — EXP-002 D1 correction, S3 (the remediation
  session). The F2 measurement (standalone baselines, an observed full-suite run
  with the notebook timeout lifted, a paired contention experiment, and the
  out-of-process sampler), the per-finding verification records for F4–F7, the
  Snyk Code scans and the F8 re-check, the delta re-audit instruments, the
  closing local gate (fast suite exit 0; the required full suite exit 1 twice on
  host-contention tests that pass alone), and the cold-review loop (briefs, raw
  reviewer output and the measured triage for four rounds; round 4, the cap, still
  returned CONFIRMED claims). See its `README.md`.
- [`exp002-d1-s2/`](exp002-d1-s2/) — EXP-002 D1 correction, S2 (the read-only
  correction audit). Six committed instruments and their verbatim outputs,
  re-executing every S1 claim rather than accepting it: the pre-fix reproduction
  (18 failed on exactly the E3 set, plus all 9 fast-gate argument tests), an
  independent decomposition re-run compared field-for-field with the committed
  artefacts, a static AST cross-validation of all 34 divergence specifications
  against the frozen reference source, an artist-level comparison of all 14
  stems (**14/14 EQUAL**, so no plotted value differs), a re-derivation of H3
  under **both** registered comparison policies with every residual classified,
  `verify_manifest` over all five `RUN-*` records, the frozen E4 module
  reproducing all seven outputs and `report-manifest.json` byte-for-byte from a
  clean worktree outside the repository, both Snyk Code legs (MCP completed,
  CLI **blocked** on expired credentials), the full local gate, and a retained
  Testing Standards §7 stall diagnostic. See its `README.md`.
- [`exp002-d1-s1/`](exp002-d1-s1/) — EXP-002 D1 correction, S1 (an unnumbered
  contingency session). It holds the failing-test-first red and green gate
  runs, and a root-cause decomposition of the 18-file H3 divergence at the
  pre-fix and post-fix ports. The decomposition uses controlled substitution
  on the frozen PRINet 3.0 generator, and the 34 registered divergences
  explain every differing byte with 0 unexplained (PRIN side). The directory
  also holds the verification of the retained E3 bytes, the verbatim local
  gate and the secret scans; see its `README.md`.
- [`exp001-d1-s1/`](exp001-d1-s1/) — EXP-001 D1 correction, S1 (an unnumbered
  contingency session). A root-cause decomposition of every H1/H2a breach at
  the pre-fix and post-fix builds, attributing each by controlled substitution
  in PRINet 3.0 (0 unexplained). A campaign plan §10.4 item 3 exactness audit:
  50-digit mpmath evaluation of PRINet 3.0's own map, plus SymPy lemmas, puts
  the reference on the erroneous side in 57/57 DV-007 breaches. Both generator
  scripts are included; see that directory's `README.md`.
- [`ea007/`](ea007/) — EA-007 (2026-10-11) readiness evidence: the frozen
  `readiness-state.json` snapshot (maintainer approval verbatim, GitHub
  observations, runner/secret-scanning state, carry-forward gates), the
  EXP-001-r1 merge `check_ci_green` output, and the latest pre-pause
  nightly capture. Frozen input evidence; not regenerated.
  [`ea007/verification/`](ea007/verification/) preserves the full local
  gate's per-command logs, its post-commit secret scans, the PR #32 review
  round's gate log, and a `SHA256SUMS.txt` integrity inventory (executed by
  `tests/test_ea007_manifest.py`)
  (logs/text artifacts only — see that directory's `README.md`).
- [`0159/`](0159/) — session 0159 (EXP-002 E1, 2026-10-11) preparation
  evidence: the frozen `entry-state.json` (source baseline, GitHub
  observations, settled `[]` native open-alert read) and, under
  `verification/`, the focused driver captures, the `full-gate/` legs on
  `7859030` (failed and interrupted attempts preserved), the
  `final-6314532/` final local gate on checkpoint `63145325` (FAST and FULL
  exit 0, Sphinx and governance exit 0), and the `pr33-review/` PR #33
  review-round gate and probes, all covered by the `SHA256SUMS.txt`
  integrity inventory (executed by `tests/test_0159_manifest.py`). Each leg
  set's claims are scoped to the source it ran on. The full-history secret
  scan's one checksum finding is resolved by the maintainer-approved exact
  fingerprint exception in the repository's `.gitleaksignore`; the
  review round's clean rescan is recorded in `pr33-review/`. Verification evidence
  only: no EXP-002 execution has run (see that directory's `README.md`).
- [`0160/`](0160/) — session 0160 (EXP-002 E2, 2026-10-12): the E2
  review's static re-derivation, Lean 4 proof and Z3 check; the `WinError 32`
  reproduction and fix check; the hosted-failure reproductions and fixes;
  the approved source's local gate; and the read-only cold reviews, all
  covered by `verification/SHA256SUMS.txt` (executed by
  `tests/test_0160_manifest.py`). No EXP-002 execution has run.
- [`0161/`](0161/) — session 0161 (EXP-002 E3, 2026-10-12): launch records
  and independent per-record validation (revisions 1–3) of the five E3 legs,
  the Windows local gate, hosted results and two read-only cold-review rounds,
  covered by `verification/SHA256SUMS.txt`.
- [`0162/`](0162/) — session 0162 (EXP-002 E4, 2026-10-13): pre-flight,
  Phase-A gate of the registered analysis module, two pre-run cold-review
  rounds, the two byte-identical analysis runs, the post-run self-audit, the
  DV-040 re-audit, the final-candidate gate and hosted results, covered by
  `verification/SHA256SUMS.txt`.
- [`0163/`](0163/) — session 0163 (EXP-002 E5, 2026-10-14): pre-flight,
  retained-bytes verification (Step 1), detached-worktree regeneration of the
  seven E4 outputs (Step 2), protocol §8.2 reconstruction of the 39
  publication files (Step 3), independent recount (Step 4), cold reviews and
  self-audit, documentation/evidence delta gate and hosted results, covered by
  `verification/SHA256SUMS.txt`.

## Rules

- This directory holds machine-checkable probe/gate artefacts specifically —
  hardware/runtime capability probes, exit-gate readiness snapshots — not a
  mandatory per-WP deliverable. Most work packages verify claims through
  their audit report, Project State Report, and the test/parity/benchmark
  suites themselves; a WP with no hardware probe or gate check of its own
  legitimately adds nothing here (EA-003 finding E-F11, D4 — clarified after
  WP-010..016 added no new files here, which is expected, not a gap).
- Evidence files are committed artefacts; they are not regenerated silently.
- S2 audit reproductions may write fresh evidence with a new timestamp, then
  restore the original S1 baseline to preserve the evidence chain.
- The WP-001 baseline validator and the Phase 0 gate checker reference these
  files by path.
