# EXP-002 - Maintainer review packet for session 0160

**Status:** PREPARED FOR REVIEW - NOT APPROVED
**Prepared by:** Devin, E1 drafting AI pair
**Date:** 2026-10-11 UTC
**Independent reviewer:** MichaelMaillet - review/decision pending
**Active stage:** 0159 E1 evidence/closure; 0160 remains PLANNED
**Protocol:** [preregistration.md](preregistration.md)

This is an author-prepared decision packet, not an independent non-author
review, signed E2 approval, or E3 authorization. Complete the E1 exit gate
before starting 0160 as a separate stage. The maintainer performs the
independent scientific review; any optional second AI reviewer must not
have drafted E1.

## 1. Reviewed source and evidence

Baseline: PR #32 merge
`da53ea11a3f38cd0d5c27c40bbefbeaf6d6dbf53`.

Reviewed/tested checkpoint:
`63145325c01fd837fd55e2796ea0fa34aa7eb234`.
It contains the DRAFT, hardened driver, synthetic regression tests,
amendment #49 and the preserved recovery record. Later evidence/index
commits do not claim that the full suite ran on their own SHA.

| Scientific artefact | SHA-256 of reviewed bytes |
|---|---|
| `preregistration.md` | `847c54c0ed77fa7908f8426b6178d02eec77dde000bbb52df5a4c0ac33addd52` |
| `benchmarks/campaign/exp002_driver.py` | `52edad9291a475f702182a78ff7cc738fa7e94875e0ba9a9d1da2d368f3c59f6` |

Local Windows validation:

- Focused gate: 256 passed; driver coverage 99.61%; Ruff and strict mypy
  clean. Snyk Code reports zero medium-or-higher issues on byte-identical
  copies of the driver and two test files.
- Fast suite: 3,710 passed, 178 skipped, 55 deselected, 59 warnings,
  exit 0.
- Full isolated suite: 5,904 passed, 184 skipped, 61 warnings, exit 0,
  27:01. The earlier exit-1 run had one WinError-32 setup error and is
  retained; its separate diagnostic is not substituted for this full pass.
- Overall `--cov=prin` statement coverage is 7,326/7,727 = 94.810405%.
  The terminal rounds this to 95%; it is not an unrounded >=95% or
  per-change coverage claim. The changed driver has its separate 99.61%
  gate. DV-033 remains OPEN.
- Rust tests/lints/coverage/docs, native dependency audits, clean Sphinx
  and governance checks pass in their recorded scopes. Rust source and
  dependency inputs are unchanged; existing governed advisory dispositions
  remain visible.
- Full-history scan of checkpoint 6314532 covers 713 commits and reports
  one checksum false positive, exit 1. No new credential finding is
  reported; the narrow exception is not applied without approval.

Evidence: [session index](../../../EVIDENCE/0159/README.md).
No EXP-002 RUN directory, pilot, new outcome inspection or experimental
publication regeneration occurred. Ordinary verification tests do not
become campaign observations.

## 2. Scientific decisions requiring review

| Decision | Proposed contract | Maintainer decision needed |
|---|---|---|
| H1 | 175 PRIN exports; independent mapping to 172 frozen reference names plus three PRIN additions; no duplicate/missing/extra/unresolved/unsupported values | Accept namespace/ownership scope, not proof of every callable's numerical or behavioral parity |
| H2 | Five archival families and all 62 labelled predicates, including negative grid classifications and CPU Goldilocks entries | Review independent historical expectations and the full downstream owner matrix; this is not fresh training/GPU/performance replication |
| H3 | Exact 39-file census: 14 figures in PDF/PNG and 11 raw-byte tables; independent reference generator arm; matched fonts/renderer/environment | Approve the format and metadata-only normalization policy, including classic-xref structural byte offsets; no scientific stream/value masking |
| H4 | Two separate PRIN render processes; all 39 raw sizes/digests and canonical scientific projections agree | Raw identity cannot be rescued by H3 normalization |
| Samples/statistics | One deterministic census per leg; `(counter,key)=(0,2)`; no RNG consumed; separate replicate-0 rerun | Explicit n=1/no-inference approval; `iterations=10` is unused envelope metadata, not ten samples |
| Resources/admission | CPU <=12 h, GPU <=2 h, hosted campaign CI <=2 h, tracked <=10 MiB; per-run <=2 MiB, campaign <=64 MiB | Review software/provenance guards, storage feasibility, and operator supervision of aggregate budgets |

Every valid counterexample is retained. Invalid/missing coverage,
refutation and campaign D1 escalation remain separate. No statistical
aggregation, changed normalizer or favorable subset can rescue a falsifier.
No scientific verdict is available before E3/E4.

## 3. Pre-execution correction disclosure

The former synthetic fixtures covered signatures/chunk lengths but did
not exercise real container integrity or metadata-derived PDF relocation.
A synthetic-only proof exposed both gaps. The committed correction:

- Validates the registered classic-xref PDF container and PNG CRCs,
  critical chunks and decoded image data.
- Masks named PDF fields only in the referenced Info object, document ID
  only in the trailer, and canonicalizes structural byte-offset fields.
- Preserves object identities, drawing/image/font streams, scientific
  values and unregistered Info fields; retains raw files unchanged.
- Rejects nonregular outputs. Missing/extra regular publication files
  remain observations for H3's valid-counterexample rule, not hidden passes.

This is container validation, not a general PDF interpreter. The complete
normalization policy still needs explicit E2 approval.

## 4. Distinct approvals and prerequisites

1. **Checksum exception / E1 closure.** Approve only fingerprint
   `78590305e1c0a78d92153ef2a55a9e76aeb7af79:EVIDENCE/0159/entry-state.json:generic-api-key:87`.
   Its value is the verified reference API SHA-256
   `ede92afc6771f2e29206534905e2820598ba841662a93d59f669f803a382f182`,
   not a credential. Preserve the raw finding, record name/date authority,
   add only that fingerprint, and rescan before publication.
2. **Scientific E2 approval.** After E1 closure, review section 2 and the
   committed DRAFT. Record MichaelMaillet's explicit name/date decision
   and any pre-execution amendments in 0160. Author preparation or
   validation success cannot supply approval.
3. **Hosted-pause lift and forced nightly.** Give a separate explicit
   instruction for a later Plan amendment. This packet does not lift #48.
   Re-enable the seven check workflows, restore the exact removed required
   checks on ruleset 22150076, and obtain results on the exact published
   source through normal PR review/merge. Preserve PR-only, no deletion
   and no force-push protections.
4. **Nightly/source/budget readiness.** Once reviewed source reaches main,
   explicitly authorize
   `gh workflow run nightly.yml --ref main -R Symbo-gif/PRIN`.
   Record actual run ID/head SHA/attempt and require the whole nightly,
   including full-suite and bench-regression, to pass or enter governed
   remediation. Resolve how manual dispatch minutes count under campaign
   section 8 before execution; do not assume an exemption, widen EXP-002's
   CI cap, shorten ABBA measurements or change thresholds.
5. **E3 go/no-go.** Recheck clean approved source, protocol identity, current
   required workflow results, whole-nightly outcome and experiment admission
   conditions. Freeze at the first actual RUN creation. Readiness approval
   is not itself permission to execute EXP-002 or publish a release/tag.

## 5. Carried limits

DV-033, DV-034, DV-040's 0162 re-audit, DV036-F5 at 0166, DV-036 before
0168/0173 and EXP-004+ hardware gates remain carried. Native push
protection is a separate flagged external control. Windows validation
does not satisfy Linux/macOS or the wheel matrix; lifting the pause alone
does not validate them.

**EXP-002 remains DRAFT. E2 approval is pending. No experiment execution
occurred. Hosted checks and nightly remain paused.**
