# EXP-002 E1 — Entry evidence and handoff

**Session:** `0159` (EXP-002 / C1, E1 — Pre-registration).<br>
**Date:** 2026-10-11 UTC. **AI pair:** Devin.<br>
**Deliverable:** a DRAFT protocol and a prepared, tested collection driver
for independent E2 review — **not** execution approval and not an
experiment result.<br>
**Branch:** `campaign/0159-exp002-e1`.<br>
**Protocol:** [`preregistration.md`](preregistration.md) — lead-authored.

## Entry and authority

The maintainer explicitly declared this session's E1 scope and authorized
E1 driver preparation/testing ("permitted to do or create what is needed
to honestly complete the tasks at hand") with the scientific protocol and
collection rules owned by the lead. Session-scope records: the
[0159 brief](../../sessions/phase-7/0159-exp002-e1-api-benchmark-result-and-reproduction-parity.md)
added-scope section and Project Plan **amendment #49** (supervised local
validation / timeout governance — supervision changes only, no scientific
parameters).

Source baseline: `da53ea11a3f38cd0d5c27c40bbefbeaf6d6dbf53` (PR #32 merge
to `main`, merged 2026-10-11T10:39:51Z, head `8b4d1803`; fetched
`origin/main` equals it; checkout non-shallow). Attribute commit
`85b779297be0642f5c64853c1590ef341e7ff77e` landed the
`EVIDENCE/0159/**` byte-exactness rule before the evidence files.
Frozen E1 entry observations:
[`EVIDENCE/0159/entry-state.json`](../../../EVIDENCE/0159/entry-state.json)
(captured 2026-10-11T11:32:04Z; GitHub observations settled there,
including the completed `[]` native open-alert read — do not re-query).

## Deliverables under review

| Artefact | State |
|---|---|
| [`preregistration.md`](preregistration.md) | Lead-authored **DRAFT**; the E2 review items of its §10 are open for session 0160 and the maintainer |
| [`benchmarks/campaign/exp002_driver.py`](../../../benchmarks/campaign/exp002_driver.py) | Lead-authored, including the post-review publication-container correction (classic-xref PDF validation + xref/startxref canonicalization; PNG CRC/critical-chunk/decoded-image validation; nonregular-output rejection; exact-`APPROVED` status match); working-tree bytes SHA-256 `52edad9291a475f702182a78ff7cc738fa7e94875e0ba9a9d1da2d368f3c59f6` (1178 lines; refresh if the source changes before commit — the prior hash set is in `EVIDENCE/0159/verification/source-hashes.txt` and the post-correction set (same driver hash, updated test hash) in `EVIDENCE/0159/verification/full-gate/correction-source-hashes.txt`) |
| [`tests/test_exp002_driver.py`](../../../tests/test_exp002_driver.py) | Synthetic-fixture regression tests (no archived inputs, no real generators, no execution) |
| [`tests/test_0159_manifest.py`](../../../tests/test_0159_manifest.py) | `EVIDENCE/0159` manifest regression tests reusing the EA-007 validators |
| [`EVIDENCE/0159/`](../../../EVIDENCE/0159/) | `verification/full-gate/` (7859030 legs + correction evidence) and `verification/final-6314532/` (final gate on checkpoint `63145325c01fd837fd55e2796ea0fa34aa7eb234`) packaged; raw captures immutable, index narrative mutable, `SHA256SUMS.txt` regenerated in the same change |
| [`e2-review-packet.md`](e2-review-packet.md) | Lead-authored 0160 maintainer-review packet (PREPARED FOR REVIEW — NOT APPROVED): reviewed source/hashes, methods, validation results and the five decision gates for E2 |

## Open for session 0160 (E2 — Review and approval)

- Every preregistration §10 review item (the E2 decision list), including
  the 175-symbol PRIN contract vs. the separate frozen 172-name PRINet
  reference contract, the five-family/62-predicate conclusion census, the
  14-figure/39-output/172-input reproduction reconciliation, the
  `n=1`/no-inference exception, and the driver/review finding closure.
- Independent review of the driver against the protocol; approval cannot
  precede closure of driver/review findings.
- The H3 publication normalization policy — registered-container
  validation (classic-xref PDF structure; PNG CRC, critical-chunk and
  decoded-image checks) including xref/startxref pointer-field
  canonicalization — is a metadata-only policy that needs explicit E2
  approval (protocol §5.4); the pointer fields are inside that review.
- Scientific approval is recorded only by 0160; freeze occurs at the first
  E3 run.

## Gates and supervision notes

- **Executable local quality checks: complete on `63145325`** (the
  security exception below still blocks E1 exit — this is not a blanket
  all-clean statement) — captures in
  [`EVIDENCE/0159/verification/final-6314532/`](../../../EVIDENCE/0159/verification/final-6314532/):
  FAST 3710 passed / 178 skipped / 55 deselected / 59 warnings (995.73 s,
  exit 0); FULL 5904 passed / 184 skipped / 61 warnings (1621.36 s, exit 0
  — leg `04c`; the earlier `04` attempt's WinError-32 fixture-setup lock
  error is preserved with an unproven holder, and its isolated diagnostic
  does not substitute); focused driver gate 256 passed at 99.61 %
  changed-driver coverage; whole-`prin` coverage 7326/7727 =
  **94.810405 %** (the terminal's `95` is rounded — no unrounded ≥95
  claim; DV-033 remains OPEN); Sphinx `-W` build and the governance
  battery all exit 0. Rust/static/native-audit legs remain valid from the
  7859030 gate for their unchanged scopes.
- **Security:** Snyk Code on the three changed Python files — 0
  medium-or-higher findings at both the corrected and final frozen-source
  scans (byte-identical copy attestation). The full-history secret scan
  is a real **exit 1** — exactly one known finding: the noncredential
  `reference_api_sha256` checksum at `EVIDENCE/0159/entry-state.json:87`.
  The exception is **pending explicit maintainer approval**; no
  `.gitleaksignore` change has been made. This decision plus publication
  is what blocks E1 exit — E1 stays `IN_PROGRESS`; there is no
  scientific approval.
- **Remaining E1 work:** evidence packaging of the final-gate captures,
  the checksum-finding decision, then publication/PR (lead action).
  Scientific maintainer review is reserved for session 0160 (E2).
- **E3 aggregate CPU budget (campaign plan §8, 12 h):** the driver records
  per-run `elapsed_seconds` and enforces the per-leg wall check plus
  storage caps at closure; it is **not** a multi-process campaign
  scheduler. The E3 operator log must supervise the ≤12 h aggregate across
  **all** attempts, including aborted/incomplete ones — no automatic
  global-budget pass may be claimed.
- **Record closure:** storage-cap/closure failures can leave a raw
  `status=COMPLETED` result while the run exits non-zero; such a run is
  inadmissible — status alone never constitutes a pass.
- **Fixture format gap closed:** the earlier synthetic PDF/PNG fixtures
  deliberately lacked xref structure and valid CRCs, matching the former
  magic-byte-only guards. The corrected driver validates the registered
  containers, so the fixtures were upgraded to structurally valid
  classic-xref PDFs and CRC-correct PNGs (lead-authored recipes);
  malformed containers now fail as `DriverError` before comparison.
- Historical predecessor evidence for the record — verbatim frozen output
  of the EXP-001-r1 merge CI check (source:
  [`EVIDENCE/ea007/exp001-r1-merge-ci-green.log`](../../../EVIDENCE/ea007/exp001-r1-merge-ci-green.log);
  a historical artifact only — hosted checks remain paused under
  amendment #48 and it asserts nothing about current CI):

  ```text
  CI-green check — branch 'main', commit 32cfed8a0b4d915a04e18efbfadd146a2ecb7e32
    rust       green     — run 36641713788
    python     green     — run 36641713282
    parity     green     — run 36641713312
    repro      green     — run 36641713284
    snyk       green     — run 36641713362
    gpu        green     — run 36641713384
  RESULT: all required workflows green

  EXIT_CODE=0
  ```

## Outstanding publication

The 0159 branch is unpushed; no PR is opened. Publication (push/PR),
GitHub queries and the security re-scan belong to the lead after E1 lead
code review of the source head.

## Dated corrections — PR #33 review round (2026-10-11 UTC)

The sections above are kept as written at `78d3600`. These corrections
supersede them where they conflict (PR33-F10,
[`PR033-multi-review-audit.md`](../../audits/PR033-multi-review-audit.md)):

- **Publication:** the branch was pushed and opened as PR #33 on
  2026-10-11. The "Outstanding publication" section and the publication
  part of "Remaining E1 work" are historical.
- **Evidence packaging** of the final-gate captures was already complete at
  `78d3600` (`verification/final-6314532/`, manifested). The "Remaining E1
  work" bullet contradicted the deliverables table above.
- **Checksum exception:** MichaelMaillet approved the exact fingerprint
  exception on 2026-10-11, and `.gitleaksignore` records it. The review
  round's full-history scan is in `EVIDENCE/0159/verification/pr33-review/`.
- **Source changed after review:** the driver, its tests and the DRAFT
  protocol were amended to resolve the review findings (protocol section 11).
  The driver hash in the deliverables table describes the pre-review
  checkpoint. The current reviewed hashes, and the gate that covers them,
  are in [`e2-review-packet.md`](e2-review-packet.md) section 1.
- **Outcome exposure:** before E2, two independent reviews posted H2/H3
  outcome information from real-input runs. See protocol section 11.2 and
  section 10 item 9.
- **E1 status:** the exit conditions in the session brief are met by
  committed evidence. Session 0159 stays `IN_PROGRESS` until the maintainer
  accepts the E1 exit. No scientific approval is implied.
