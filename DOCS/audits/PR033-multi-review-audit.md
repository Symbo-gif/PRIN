# PRIN Audit Report — PR #33 multi-review round (session 0159, EXP-002 E1)

**Date:** 2026-10-11 UTC
**Auditor:** Claude Opus 5.5 (AI pair). Every claim was re-derived from the
repository and from executed commands; no reviewer's assertion was taken on
its word. This report follows
[`TEMPLATE_Audit_Report.md`](TEMPLATE_Audit_Report.md), the severity scale of
[`Development_Workflow_and_Audit_Standards.md`](../standards/Development_Workflow_and_Audit_Standards.md)
§5, and the external-review event class of
[`PR032-multi-review-audit.md`](PR032-multi-review-audit.md),
[`PR023-multi-review-audit.md`](PR023-multi-review-audit.md) and
[`PR017-devin-review-audit.md`](PR017-devin-review-audit.md). PR #33 is session
0159's E1 publication, not a Session-Cycle S2.
**Scope:** every review and audit comment on PR #33
(`campaign/0159-exp002-e1` → `main`) at head
`78d360029028c0571bdc272bef39e901c85f09da`, and the repository state those
comments describe: `benchmarks/campaign/exp002_driver.py`, its tests, the
DRAFT pre-registration, the E1 handoff and E2 review packet, the session and
experiment indexes, the amendment #49 standards edits, and the
`EVIDENCE/0159/` bundle.
**Trigger:** GitHub PR #33. Seven review sources (27 GitHub artefacts: 14 inline
comments, 4 reviews, 8 issue comments, plus the PR body):

| Reviewer | Kind | Raised |
|---|---|---|
| Devin Review (`devin-ai-integration[bot]`) | automated | 3 inline (1 bug, 2 analysis) |
| Copilot (`copilot-pull-request-reviewer[bot]`) | automated | 6 inline (2 Medium, 4 Low) |
| CodeRabbit (`coderabbitai[bot]`) | automated | 5 inline, 2 nitpicks, 1 failed pre-merge check (docstring coverage) |
| Sourcery (`sourcery-ai[bot]`) | automated | none — PR exceeds its 150,000-character limit (twice) |
| Perplexity-Deep-Research (posted as a maintainer review) | independent LLM review | 15 items: 11 confirmations, 4 qualifications |
| qwen-3.6-plus (maintainer issue comment) | independent multi-agent review | 2 Critical, 12 Should-fix, 11 Nice-to-have, 10 refuted claims |
| SWE-2 HIGH (maintainer issue comment) | independent multi-agent review | 2 Critical, 10 Major, 13 Minor, 6 refuted claims |

**Active brief:**
[`0159`](../sessions/phase-7/0159-exp002-e1-api-benchmark-result-and-reproduction-parity.md)
(E1, `IN_PROGRESS`); the DRAFT protocol is still editable before E2
(Experimentation Standards §2, E2: "Amendments before execution are normal
edits").
**Git state:** `campaign/0159-exp002-e1` @ `78d3600` (pre-remediation). The
remediation commit follows; a commit cannot name itself.
**Regime:** Plan amendment #48, with the maintainer-approved EXP-002 hosted-check
window of amendment #50 (adopted in this round). The Windows local gate (§7)
is authoritative. Hosted results are recorded separately once they exist and
are never back-filled into this commit.
**Verdict:** `PASS-WITH-FINDINGS` → remediated in the same round. **No D1.**
No experiment executed, and no hypothesis, prediction, population, threshold,
tolerance, sample, budget or abort criterion changed. Two DRAFT-protocol
defects (PR33-F1, PR33-F2) would have produced a spurious campaign D1 at E4 if
executed as written. They are classified D2, prevented before execution.

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| Independent re-derivation | ✅ | 27 artefacts, 7 reviewers, 38 distinct findings `PR33-F1`…`PR33-F38`; each re-derived by an executed probe, a test, or a quoted line (§3, §4). |
| False positives / over-reach | ✅ | 1 refuted (`§5.9`, PR33-F28), 2 not a defect (PR33-F20, PR33-F32), 1 waived check (CodeRabbit docstring, PR33-F35); 2 remedies redirected from frozen evidence to the live driver (PR33-F36); 1 remedy narrowed (census counts, PR33-F4). |
| Severity | ✅ | 6 × D2, 7 × D3, 19 × D4; 6 without severity (refuted, not a defect, redirected, no review). **No D1.** |
| Regression tests (A3) | ✅ | 101 new driver test cases (214 → 315) and 3 new manifest tests (17 → 20). A mutation proof rebuilt each pre-fix behaviour (19 for the review findings, 5 for the self-audit fixes): **24/24 mutations caught**, and every selected test passes on the fixed driver (§6, leg P2). |
| Numerical parity (A4) | ➖ | Not applicable: no numerical or Rust source changed. |
| Quality gates (A5) | ✅ | ruff, ruff format, mypy `--strict` (driver), interrogate, bandit — §6. |
| Security (A6) | ✅ | Snyk Code on the changed Python; gitleaks full-history clean with the maintainer-approved exact fingerprint (PR33-F34). No dependency manifest changed. |
| Doc coverage (A7) | ✅ | `interrogate` unchanged; CodeRabbit's check waived with evidence (PR33-F35). |
| Hygiene (A8) | ✅ | Frozen evidence untouched except the mutable `GATE-STATUS.md` index, which is corrected with `SHA256SUMS.txt` regenerated; hidden files and `*.log` force-added and covered by the manifest tests. |
| CI status (A9) | ➖ | Local gate authoritative; the hosted window (amendment #50) opens after this commit is pushed. Its results are recorded after they exist (§9). |
| Artefact trail (A10) | ✅ | This report, protocol §11, the E2 packet, the handoff and index dated corrections, CHANGELOG, the DV-register dated section, Plan amendments #50/#51, and the `pr33-review/` evidence bundle. |

## 2. Methodology

Reviews were fetched from the API, not read from a summary:

```bash
gh pr view 33 --json body,reviews,comments,files
gh api repos/Symbo-gif/PRIN/pulls/33/comments  --paginate   # 14 inline
gh api repos/Symbo-gif/PRIN/pulls/33/reviews   --paginate   # 4 reviews
gh api repos/Symbo-gif/PRIN/issues/33/comments --paginate   # 8 issue comments
```

Claims were de-duplicated across reviewers, then each was re-derived
**before** any fix was written. Static claims were checked by reading the cited
code at `78d3600`. Behavioural claims were checked by executed probes using
**synthetic inputs only**
(`EVIDENCE/0159/verification/pr33-review/ground-truth-probes.py.txt`, output
`ground-truth-probes.log`). The probes call the real PRIN and pinned reference
*writers* (`_save_table`, `_save_fig`) on a synthetic table and a synthetic
figure. They never call a generator over the registered input snapshot, never
read a registered JSON input, and never create a RUN directory. One probe read
the 11 archived reference tables only to test them for CR bytes (none). That
is a byte property of frozen inputs, not a comparison with any generated
output.

**Outcome discipline.** Two reviews published EXP-002 outcome information
(PR33-F38). This audit read those passages only as review text. It did not
reproduce them, and it chose no protocol change because of them. Every
protocol change rests on the static and synthetic bases in protocol §11.1.

**Delegation record.** The maintainer authorized orchestrating the Antigravity
(`agy`, `gemini-3.1-pro-high`) and Devin (`swe-2-high`) CLI agents. Both ran
in read-only mode, with no shell, no edits and the report on stdout (the
permission-bypass modes are blocked by this session's safety classifier, as
in PR #32).

- *Ground-truth round:* `agy` checked 18 documentation and governance claims
  (D1–D18) and Devin checked 17 driver and test claims (K1–K17). Their
  reports are preserved in `pr33-review/delegation/`. Devin's code verdicts
  matched the executed probes on every claim. `agy`'s verdicts were
  directionally right, but several of its "verbatim quotes" were not
  verbatim: the CHANGELOG and `SESSION_REGISTER.md` line-5 quotes were
  paraphrased with invented text, and it misnamed the 0161–0163 brief
  files. No `agy` quote was relied on; each fact it reported was re-read
  by the auditor.
- *Self-audit round:* both agents cold-reviewed the remediation delta (§8).

**Remediation order.** Ordered so that no step invalidates another, with
hash-pinned files last:

1. Ground truth (§3–§4), no edits.
2. Driver fixes with regression tests in the same change, then the mutation
   proof.
3. DRAFT protocol amendments (protocol §11) and the E2 packet.
4. Mutable records: handoff, indexes, register, CHANGELOG, READMEs,
   `AGENTS.md`, standards clarifications, Plan amendments #50/#51 and the
   #49 errata.
5. Append-only records: this report, the DV-register dated section and the
   audits index.
6. Frozen evidence: the `GATE-STATUS.md` correction and the new
   `pr33-review/` bundle, with `SHA256SUMS.txt` regenerated **last**.
7. Local gate (§6), cold self-audit (§8), fixes, re-verification.
8. Commit, post-commit secret scan, push, then the amendment #50 hosted
   window.

## 3. Reviewer adjudication (ground truth)

| Reviewer | Right | Wrong or imprecise |
|---|---|---|
| Devin Review | All 3: the Windows CRLF table defect (the most consequential finding, raised first), the unvalidated census payload, and the raw-byte reconstruction dependency | The "Completed status does not prove a complete census" remedy needs narrowing: a publication arm must not be counted (PR33-F4) |
| Copilot | All 6 in substance | `EVIDENCE/README.md`: the "no final full-gate pass is asserted" sentence was technically true at `78d3600` because gitleaks was red. The real defect is that the bullet omitted `full-gate/` and `final-6314532/` (PR33-F10) |
| CodeRabbit | Orphan RUN directory, stale handoff, the MD056 rows, `REQUIRED_BUNDLE`, and the gitleaks false positive | Its orphan-fix ordering tests a name before validating it (PR33-F5). Its two parser findings target a frozen historical snapshot rather than the live driver (PR33-F36). "Renderers drop data" overstates MD056. Its docstring-coverage check is a false positive (PR33-F35) |
| Sourcery | — | Produced no review (size limit) |
| Perplexity | All 15 in substance, including the redirect of the parser defects to production code and the docstring qualification | Its "enforce mode-specific cardinalities" remedy would discard H3 falsification evidence if applied to publication arms (PR33-F4) |
| qwen-3.6-plus | C1 and the new C2 (the PDF Info dictionary). The CodeRabbit ordering flaw. The `c02` mislabel, the stale proof log, `AGENTS.md`, the figure count, the #49 row, Testing Standards §7, and most nice-to-haves | "Poisoning a sibling manifest" does not couple closures; only an **unmeasurable** entry (symlink or unreadable file) does (PR33-F14, probe P9/P9c). The `§5.9` it cites does not exist (PR33-F28). **It ran the real generators over the registered snapshot and evaluated H2 on archived data, then published the outcomes before E2** (PR33-F38) |
| SWE-2 HIGH | Every confirmation. New: the EXP-001-r1 index cell, `SESSION_REGISTER.md` line 5, font-cache state, root-level module shadowing, the output-root TOCTOU, and dead `/ID` masking. Correctly refuted the `RUSTDOCFLAGS` claim | Published the C03 N=128 operand margin (PR33-F38) |

## 4. Master findings ledger

Verdict: **C** confirmed, **P** partially confirmed, **R** refuted, **N**
not a defect. Disposition: **FIXED** (with a regression test where
applicable), **AMENDED** (Plan amendment), **E2** (recorded as an explicit E2
decision in protocol §10), **DECLINED** / **WAIVED** (with reason).

| ID | Sev | Sources | V | Ground truth (evidence) | Disposition |
|---|---|---|---|---|---|
| PR33-F1 | D2 | Devin, Perplexity 1, Qwen C1, SWE-2 C1 | C | The reference `_save_table` (`table_generation.py:62-63`) uses `open(path, "w")` with no `newline=`; PRIN's (`:49`) uses `newline="\n"`; the driver returned `.tex` bytes unchanged. Probe P1: the same synthetic content through both writers gives 46 B with 3 CRLF vs 43 B with 0 CRLF, so the normalized digests differ; after CRLF→LF alone the bytes are equal. Archived tables: 11 files, no CR byte. The pinned writer cannot be patched | FIXED + E2: symmetric CRLF→LF canonicalization of tables, also applied to the archived baseline (protocol §5.4, §10 item 7) |
| PR33-F2 | D2 | Qwen C2, SWE-2 C2 | C | PRIN `_save_fig` passes 4 Info keys; the reference passes no metadata, so Matplotlib writes 3 (no `ModDate`). Value masking kept the key set and the original line wraps. Probe P2 with the real writers on a synthetic figure: normalized **unequal**. Same keys with different value lengths: **unequal**, from wrap residue | FIXED + E2: the referenced Info dictionary is parsed; the four registered entries are removed (key and value) and the rest re-serialized; non-dictionary or malformed Info fails closed (protocol §5.4, §10 item 7) |
| PR33-F3 | D2 | Copilot, Perplexity 2, Qwen S5, SWE-2 M1 | C | `check_run_complete` regex-checked the digest and commit; `approval_date_utc` was never read. Probe P7: a fabricated `"f"*64` digest with no approval date was **ACCEPTED**. The auditor also found that admission compared `strip()`-ed text, so working and committed protocol bytes could differ in trailing whitespace while the recorded digest described the working bytes | FIXED: closure resolves `git show <commit>:<protocol>`, compares SHA-256, re-parses the committed approval, and requires the commit to be an ancestor of the source. Admission compares exact bytes |
| PR33-F4 | D3 | Devin, Perplexity 3, Qwen (refuted remedy), SWE-2 M2 | C (remedy narrowed) | `observations` was never read at closure. Probe P8: a `reference` record carrying `implementation: "prin"` was **ACCEPTED**. Counting publication files would turn H3's registered falsifier ("a valid completed render omits/adds an output") into an invalid record | FIXED: per-mode schema and identity checks. The 175-name and 62-case populations are enforced because their collectors refuse anything else. Publication files are never counted, and a test proves an incomplete render stays admissible |
| PR33-F5 | D3 | CodeRabbit, Perplexity 4, Qwen S1, SWE-2 | C | Probe P3: a colliding output root left an **empty, unrecorded** RUN directory. Sidecar and output-root creation also sat outside the abort block. CodeRabbit's hoist would test the name before it is validated | FIXED: the guard sits inside `_reserve`, after name validation and before `mkdir`. Sidecar and output-root creation are inside the abort block, so any failure leaves an `ABORTED` record |
| PR33-F6 | D2 | Copilot, CodeRabbit, Perplexity 5, Qwen S2, SWE-2 M4 | C | 77 required entries vs an 81-line manifest (75 hashed required). Exactly the six named `final-6314532/` controls were missing, and nothing asserted manifest ⊆ required | FIXED: the six entries are added, the new test requires manifest = required, and controlled negatives cover the double deletion |
| PR33-F7 | D4 | CodeRabbit (snapshot), Perplexity 6, Qwen, SWE-2 | C | Probe P4: a 5,000-digit `startxref` raised `ValueError`. The test written for this fix found a second defect: a present but oversized `/Info` was silently treated as **absent** | FIXED: every decimal capture is bounded, and a present but unparseable `/Info` is malformed. Frozen snapshot unchanged |
| PR33-F8 | D4 | CodeRabbit (snapshot), Perplexity 7, Qwen, SWE-2 | C | Probe P5: an indexed PNG with PLTE after IDAT was **ACCEPTED**; IHDR data was never parsed. matplotlib emits no indexed PNGs, so this is not a false-equality vector | FIXED: IHDR parsed; colour-type rules for PLTE/tRNS and their placement before IDAT |
| PR33-F9 | D3 | Devin, Perplexity 8 | C | Run manifests hash only the JSON records; generated bytes live in the gitignored output root, so §8.2 byte verification needs reconstruction | E2: protocol §10 item 8 |
| PR33-F10 | D4 | Copilot ×4, CodeRabbit, Perplexity 9/11, Qwen S7, SWE-2 M7 | C | Stale or contradictory status lines: `CHANGELOG.md`, `e1-handoff.md` (lines 85–86 contradict line 40; lines 124–126), `DOCS/experiments/README.md` (gate pending; EXP-001-r1 "not yet opened" after PR #28), the `EVIDENCE/README.md` 0159 bullet, and `SESSION_REGISTER.md` line 5 | FIXED: dated corrections, appended rather than rewritten, in the handoff, CHANGELOG and experiments index; indexes updated |
| PR33-F11 | D4 | CodeRabbit, Perplexity 10, Qwen, SWE-2 | C | Three two-cell rows under a three-column header in `GATE-STATUS.md`. The effect is column misplacement, not dropped data | FIXED with a dated correction section; `SHA256SUMS.txt` regenerated |
| PR33-F12 | D4 | Qwen S3, SWE-2 M5 | C | Row `c01–c04` called c02 failed; `c02-…log` reads `248 passed`, `EXIT_CODE: 0` | FIXED (same correction) |
| PR33-F13 | D4 | Qwen S4, SWE-2 | P | The proof log's live-driver PASS lines predate the container fix. `full-gate/README.md` already discloses "Not re-run after integration". Only the status matrix lacked it | FIXED: caveat added to the `GATE-STATUS.md` corrections; the current driver is covered by the regression suite and the mutation proof |
| PR33-F14 | D4 | Qwen S6, SWE-2 M6 | P | Probe P9: corrupting a sibling's manifest content does **not** affect another run's closure. Probe P9c: a symlink in a sibling run fails every closure with `ManifestMismatchError`, which escaped `main()`. The global coupling follows from the registered campaign-wide caps | FIXED (reporting): an unmeasurable entry becomes a reported `DriverError`. The coupling is kept by design |
| PR33-F15 | D3 | Qwen S6, SWE-2 M3 | C | Probe P6: `ManifestMismatchError` MRO is `ReproductionError → Exception`, not caught by `main()` | FIXED: `main()` catches `ReproductionError` |
| PR33-F16 | D3 | Qwen S8, SWE-2 M8 | C | `AGENTS.md` §7 calls the instrumented invocation required; the one-liner list omitted the flags on the FAST and FULL lines | FIXED |
| PR33-F17 | D3 | Qwen S9, SWE-2 M9 | C | Briefs 0161–0163 (lines 20, 25) and Plan F4 said 15 figures; the registered target is 14 × 2 + 11 = 39 | FIXED (briefs) + AMENDED (F4, amendment #51, flagged for ratification) |
| PR33-F18 | D4 | Qwen S10, SWE-2 M10 | C | The #49 row omits Benchmarking §2.2, Experimentation §2 and the standards README, which the 0159 brief names | FIXED: dated erratum in the row; the policy is unchanged |
| PR33-F19 | D4 | Qwen S11, SWE-2 | C | "the §6 suite invocations" is ambiguous (Coding §6 is Security; Testing §6 is Commands), and the scope list omitted Sphinx `-W`, `cargo audit`, `pip-audit` and `llvm-cov` | FIXED (clarification under the #49 erratum) |
| PR33-F20 | — | Qwen S12 | N | `Coding_Standards.md:156` carries an inline `# pwsh: $env:RUSTDOCFLAGS=…` alternative on the same line (SWE-2 and `agy` D10 agree) | No change |
| PR33-F21 | D4 | Qwen, SWE-2 | C | Unresolved API rows had 5 keys vs 8; there was no 172 + 3 population guard | FIXED |
| PR33-F22 | D4 | Qwen, SWE-2 | C | Protocol C03 said "N"; the input key is `n_oscillators`, as the driver reads it | FIXED (protocol §5.2) |
| PR33-F23 | D4 | Qwen, SWE-2 | C | Closure had no UTC `strptime`, no ancestor-symlink walk, and was blind to non-JSON entries. Probe P12: a stray `stray.bin` was **ACCEPTED** | FIXED: exact directory inventory, `strptime`, ancestor walk |
| PR33-F24 | D4 | Qwen, SWE-2 | C | §2 called C02's basis "independent"; §3 correctly calls it the stored flag | FIXED (wording only). The C03 margin reported by reviewers is outcome information; it is not acted on (PR33-F38) |
| PR33-F25 | D4 | Qwen | C | The #49 evidence-table cells omit the `ea007/` prefix; the 0159 tree reuses leg numbers 08 and 25 for other legs | FIXED: dated erratum under the table |
| PR33-F26 | D4 | Qwen | C | Output-root non-pollution was asserted, not enforced | FIXED: a test asserts `git check-ignore` on the output root |
| PR33-F27 | D4 | Qwen | C | Four standards cite "amendment #49" without naming the Plan file | FIXED: the four citations now read "Project Plan §8.3, amendment #49" |
| PR33-F28 | — | Qwen | R | No `§5.9` with timeout bounds exists in any standard or in the campaign plan (repository grep; `agy` D13 agrees) | No change |
| PR33-F29 | D4 | SWE-2 | C | Protocol §5.4 names font-cache state as a control; the driver did not record it | FIXED: font-cache file digest recorded and compared before and after rendering |
| PR33-F30 | D3 | SWE-2 | C | The untracked scan covered six directories. An untracked top-level `json.py` or `sitecustomize.py` (on `sys.path[0]` under `python -m`) or an untracked `DOCS/`/`tests/` file passed | FIXED: whole-checkout untracked scan, plus top-level `*.py`/`*.pth` even if ignored. A real-git test proves the pathspec is top-level only and matches dotfiles |
| PR33-F31 | D4 | SWE-2 | C | Ancestor check before `mkdir(parents=True)`, with no re-check | FIXED: re-checked after creation; the residual window needs local write access |
| PR33-F32 | — | SWE-2 | N | `/ID` masking is dead for the installed matplotlib | No change: forward-compatible, and the synthetic fixtures exercise it |
| PR33-F33 | D4 | SWE-2 | C | Missing conclusion keys raised `KeyError`, not `DriverError` (fail-closed, wrong type) | FIXED. `_snapshot`'s `JSONDecodeError` is on hash-verified bytes and already aborts, so it is unchanged |
| PR33-F34 | D2 | CodeRabbit, Perplexity 13, E2 packet §4 | C | Gitleaks flags the `reference_api_sha256` checksum at `entry-state.json:87` (verified to be the pinned reference digest). It blocked E1 exit and would turn the hosted `Secret Scan` red | FIXED: MichaelMaillet approved the exact fingerprint on 2026-10-11; `.gitleaksignore` records only that line; the frozen file is byte-identical; full history rescanned |
| PR33-F35 | — | CodeRabbit | N | Not a project gate: `pyproject.toml` exempts `tests/**` and `benchmarks/**` from `D`; the gate is `interrogate python/prin` (fail-under 95), which this PR does not touch | WAIVED |
| PR33-F36 | — | CodeRabbit | P | The two parser findings are real but target the frozen `0159-publication-validation-proposal.py.txt` | Redirected to the live driver (PR33-F7/F8); snapshot unchanged |
| PR33-F37 | — | Sourcery | — | No review was produced | None |
| PR33-F38 | D2 | Auditor (from the Qwen and SWE-2 texts) | C | Before E2, a review executed the real publication generators over the verified 172-input snapshot, evaluated all 62 H2 predicates on archived data, and posted per-file H3 and H2 outcomes publicly; another posted the C03 operand margin. E2's entry condition ("no execution or result inspection has occurred") no longer holds as written. Predictions and decision rules were committed at `7859030`, before the reviews | E2: disclosure in protocol §11.2 and decision §10 item 9. No change in this round was chosen from those outcomes. Recommendation G2 (§10) |

**Count:** 38 IDs. 6 × D2 (F1, F2, F3, F6, F34, F38); 7 × D3 (F4, F5, F9,
F15, F16, F17, F30); 19 × D4 (F7, F8, F10–F14, F18, F19, F21–F27, F29, F31,
F33); 6 without severity (F20, F28, F32, F35, F36, F37). Every D2–D4 finding
is FIXED, AMENDED, or recorded as an explicit E2 decision. None is carried.

## 5. Notes on the D2 protocol findings

**Why canonicalization rather than a driver patch (F1/F2).** The reference
generators are digest-pinned (`REFERENCE_PINS`), and the driver aborts if they
change, so the reference writer cannot be altered. Making PRIN's writer
imitate the reference (dropping `ModDate`) would change the product to pass a
parity test. Both new rules are symmetric: the same function applies to both
arms, and for tables to the archived baseline too. They remove only host-I/O
and metadata bytes. A lone CR, every other whitespace byte, every
content-stream byte and every unregistered Info entry stay significant
(`TestNormalizedBytes::test_tex_other_bytes_stay_significant`,
`TestPdfInfoCanonicalization::test_unregistered_entries_retained_in_order`,
`::test_content_difference_stays_significant`). Real Matplotlib output with
PRIN-style metadata compares equal with default-metadata output, and a
changed line does not
(`::test_real_matplotlib_writers_compare_equal`). H4 still compares raw bytes.

**Why the decision stays with E2.** The protocol is DRAFT, so drafting the
correction is E1 work. The policy is the scientist's call, though, so
protocol §10 item 7 offers E2 three choices: approve, amend, or declare the leg
unrunnable on Windows.

**Outcome exposure (F38).** It cannot be undone, and its effect on
confirmatory status is a scientific judgement, so it goes to E2 (§10 item 9).
This round's changes are invariant to which files match: they are symmetric
canonicalizations fixed by static code facts. That is why they are offered
rather than withheld.

## 6. Verification (local gate, Windows)

Host `HP`, Windows 11 `10.0.26300`, Python 3.14.0, matplotlib 3.11.1. Every
leg's verbatim command, UTC start, source state and exit code are in the
`EVIDENCE/0159/verification/pr33-review/` capture it names.

The legs ran on the final pre-commit tree: `78d3600` plus the
uncommitted remediation, including the self-audit fixes. Captures are under
`EVIDENCE/0159/verification/pr33-review/`; failed attempts are kept with an
`a` suffix and never relabelled. Rust sources and every dependency manifest
are unchanged, so `cargo` legs, `cargo audit`, `pip-audit` and Snyk Open
Source have no changed input and were not re-run. The hosted `rust`
workflow of the amendment #50 window covers Rust independently.

| Leg | Check | Result |
|---|---|---|
| P1/P1b | Probes against a clean worktree of `78d3600` | Defects reproduced (§4 ground truth) |
| P1c/P1d | Same probes on the remediated tree | Defects closed; some probes now stop at the new guards |
| G01–G03 | `ruff check` (AGENTS.md scope); `ruff format --check` ×2 | exit 0 |
| G04–G06 | `mypy --strict`: `python/prin`, `DOCS/experiments/`, the driver | exit 0 |
| G07 | `interrogate python/prin` | 97.6 % (987/1011), exit 0 |
| G08 | `bandit -r python/prin DOCS/experiments` | 24,864 LOC, exit 0 |
| G09a | Focused gate (first attempt) | **exit 1**: 357 passed, **3 errors** — `WinError 32` while pytest removed another test's `tmp_path` directory under `.pytest_basetemp`. Kept |
| G09 | Focused gate: driver, both manifest suites, campaign quality gates | **360 passed**, exit 0; driver coverage 690/693 = 99.57 % |
| P2 | Mutation proof | **24/24 caught** (19 review findings + 5 self-audit) |
| G10–G10f | Deviation ledger, DV gates, global session registration, skipif probes, WP-001 baseline, `git diff --check` | all exit 0 |
| G11 | Sphinx `-W --keep-going` | exit 0 |
| G12a | FAST (first attempt) | **exit 1**: 3813 passed, **1 failed** — `test_secret_scan_is_blocking_and_covers_full_history` pins `.gitleaksignore` to one entry; the approved second fingerprint broke it (fixed, §8 SA-6). Kept |
| G12 | FAST `-m "not slow and not gpu"` | **3814 passed, 178 skipped, 55 deselected**, 59 warnings, exit 0 (15:43) |
| G13 | FULL `tests/ parity/ --cov=prin` | **exit 1**: 5999 passed, 184 skipped, **9 errors** — the same `WinError 32` class, at `tmp_path` setup in `tests/test_0159_manifest.py`'s controlled negatives (the directory being removed belonged to an unrelated test). Kept, not relabelled |
| G13a | Isolated diagnostic of the 9 nodes, `basetemp` outside the repository | 20 passed — diagnostic only, not a substitute |
| G13b | FULL rerun, same tree | **6008 passed, 184 skipped, 61 warnings, exit 0 (33:31)**; whole-`prin` coverage 7326/7727 = 94.81 % (the terminal's `95` is rounded; DV-033 stays OPEN) |
| G14a | Snyk Code (first) | **1 Medium**: env-var → `exec` code injection in the mutation-proof plugin. Kept |
| G14 | Snyk Code on byte-identical copies of the 6 changed Python files | **0 issues**, exit 0. The plugin was redesigned to take only an index into the harness's constant table |
| G15 | gitleaks 8.30.1 full history (714 commits) with the approved fingerprint | no leaks, exit 0 |
| G15b | gitleaks `--pre-commit --staged` on the staged remediation | no leaks, exit 0 |
| G16a | Post-package tests, first attempt | **exit 2**: the auditor's runner resolved a relative interpreter path to a system Python without matplotlib (tooling error). Kept |
| G16 | Post-package: manifest, driver and WP-001 suites after the final `REQUIRED_BUNDLE`/`SHA256SUMS.txt` update | **396 passed**, exit 0 |

**`WinError 32` (G09a, G13).** Both are fixture-time `rmtree` failures
inside `.pytest_basetemp`, which sits in the workspace. During both runs the
maintainer's IDE (the Devin/Windsurf editor, with pyright, spell-checker and
other language servers watching the workspace) was running. It is a
plausible handle holder, but this is **not proven**; no process was
attributed and none was killed. Reruns on the unchanged tree passed. This
is the class already recorded at `final-6314532/04` and is not caused by
this change.

**Scope of G13b.** After G13b, only evidence packaging changed: the
`REQUIRED_BUNDLE` entries in `tests/test_0159_manifest.py`, `SHA256SUMS.txt`,
and this report's §6/§11 text. G16 re-ran the affected suites after that
packaging. No source file changed after G13b.

## 7. Frozen-evidence handling

- `GATE-STATUS.md` is a mutable narrative index inside a hashed bundle. It
  is corrected in place with a dated corrections section, and its
  `SHA256SUMS.txt` line is regenerated in the same commit (the `78d3600`
  precedent).
- Raw captures (`*.log`, the proposal/proof snapshots, `entry-state.json`) are
  untouched; `entry-state.json` stays byte-identical, and the gitleaks
  exception is a fingerprint, not an edit.
- New evidence is `pr33-review/`: the gate captures, the probe source and
  output, the mutation-proof harness and log, and the delegation reports. It is
  added to `REQUIRED_BUNDLE` and the manifest, and force-added because `*.log`
  is ignored.

## 8. Self-audit of the remediation

Both delegated agents cold-reviewed the uncommitted remediation. Their task
files and verbatim reports are in `pr33-review/delegation/*-selfaudit-*`. Each
item was re-derived before it was acted on.

**Devin (`swe-2-high`), code — 11 items:**

| Item | Verdict | Action |
|---|---|---|
| F-A `REQUIRED_BUNDLE` lacks the `pr33-review/` files (High) | Stale: the set was extended while the review ran; leg G09 shows 20/20 manifest tests passing | None |
| F-B Info selected by object *number*, so a same-number object of another generation was also canonicalized: a crafted **false-equality** path | **Confirmed** | Fixed: the full `(number, generation)` key is carried; regression test plus mutation SA-1 |
| F-C `git diff … ':!benchmarks/results'` exempted **modified tracked** raw records (pre-existing) | **Confirmed** | Fixed, more strictly than suggested: the tracked-change check has no raw-root exemption; only *new* files under `benchmarks/results/EXP-002/` are exempt (test, SA-5) |
| F-D a git `TimeoutExpired` at closure escaped as a non-`DriverError` | Confirmed | Fixed: closure catches `SubprocessError` (test, SA-4). Admission-time git failures still reach `main()`'s `SubprocessError` branch, so they are reported |
| F-E docstring claimed *every* post-reserve failure is recorded | Confirmed (over-claim) | Docstring corrected: a failure while writing the record itself leaves an unmanifested directory that closure rejects |
| F-F greedy `<<(.*)>>` mis-split a dictionary ending in a flush hex value (`<AB>>>`): a false rejection | Confirmed | Fixed: forward tokenization to the dictionary's own `>>` (tests) |
| F-G PLTE entries not bounded by bit depth; tRNS lengths unchecked | Confirmed | Fixed (4 tests, SA-3) |
| F-H `/Info` could be picked out of a trailer string value | Confirmed (crafted) | Fixed: a repeated `/Size`, `/Root` or `/Info` token in the trailer is malformed (tests, SA-2) |
| F-I a cold font cache could false-abort once | Not reproduced: `font_manager` is imported, and the cache written, when the driver module loads, before any capture | None; recorded |
| F-J the double-deletion negatives exercise the helper rather than the real-bundle test | Accepted as designed: the real-bundle test is a one-line call of that helper | None |
| F-K real-git test could break under a global `commit.gpgsign` | Plausible on hosted runners | Fixed: `-c commit.gpgsign=false` |

**Antigravity (`gemini-3.1-pro-high`), records — 5 items:**

| Item | Verdict | Action |
|---|---|---|
| 1 `REQUIRED_BUNDLE` omits `pr33-review/` | Stale, and its quoted test code does not exist (it cites a `test_manifest_has_exact_required_count` and `ROOT / …` entries that are not in the file) | None |
| 2, 3, 5 gate logs and the clean gitleaks report "do not exist yet" | True only while the review ran; they are packaged before the commit | Closed by packaging (§6) |
| 4 `EVIDENCE/README.md` placed the fingerprint exception in `pr33-review/` | **Confirmed** | Fixed: the exception lives in `.gitleaksignore`; the rescan is in `pr33-review/` |

Antigravity also invented supporting detail: GitHub comment IDs and a C03
margin value (`0.540707`) that appear in no review. As in the ground-truth
round, its verdicts were mostly right but its quotations were unreliable.
Devin's report checked out on every point except F-A, which was overtaken
by events.

The mutation proof was extended with SA-1…SA-5 for the self-audit fixes; leg
P2 records the result.

## 9. Hosted-check window (Plan amendment #50)

The maintainer approved hosted CI checks and a forced nightly run for
EXP-002 only. The ruleset's required-status-check rule stays removed. The seven
workflows are enabled after this commit is pushed, and `nightly.yml` is
dispatched on `campaign/0159-exp002-e1`. A commit cannot record its own hosted
runs, so run IDs and conclusions are reported to the maintainer when they exist
and recorded in a later record commit. A red hosted job is a finding for a
later round, not a retroactive change to this report. This window does not
discharge the #48-suspended Linux/macOS or wheel-matrix items.

## 10. Carried items and recommendations

- **Maintainer:** ratify or override amendment #51 (F4 wording). Accept or
  reject the E1 exit; 0159 stays `IN_PROGRESS` until then. At E2, decide
  protocol §10 items 7–9. Disable the seven workflows when EXP-002 closes
  (amendment #50).
- **G1:** future reviewer prompts for a DRAFT experiment should forbid running
  registered inputs or generators and posting outcomes (PR33-F38).
- **G2:** before E2 approves, review whether the PR #33 thread's outcome
  disclosure requires reporting H2/H3 as non-confirmatory, and record the
  reason.
- Unchanged and carried: DV-033, DV-034, DV-036/DV036-F5, DV-040 (re-audit at
  0162), PR32-F13, OBS-1/OBS-2, native push protection (disabled; flagged).

## 11. Closure table

| Item | State |
|---|---|
| D2 findings (F1, F2, F3, F6, F34, F38) | F1/F2 FIXED, plus E2 decision (protocol §10 item 7); F3/F6/F34 FIXED; F38 disclosed, E2 decision (§10 item 9) |
| D3 findings (F4, F5, F9, F15, F16, F17, F30) | FIXED; F9 recorded as E2 decision (§10 item 8); F17 includes amendment #51, flagged for ratification |
| D4 findings (19) | FIXED |
| Not a defect / refuted / redirected / no review (6) | Recorded with reasons; no change |
| Self-audit (Devin F-B, F-C, F-D, F-E, F-F, F-G, F-H, F-K; Antigravity 4; SA-6) | FIXED; others stale or accepted as designed (§8) |
| Gate | G09, G12, G13b, G14, G15, G15b and G16 exit 0; failed attempts G09a, G12a, G13, G14a and G16a are kept |
| Delta re-audit | §8 (two cold reviewers) plus P2 (24/24) — **CLEAN** after fixes |
| Open, not a finding | 0159 E1 exit acceptance; E2 decisions §10 items 7–9; amendment #51 ratification; amendment #50 window closure at EXP-002 E5 |

**SA-6 (found by the gate, not a reviewer).** Adding the approved fingerprint
broke `tests/test_wp001_baseline.py::test_secret_scan_is_blocking_and_covers_full_history`,
which pinned `.gitleaksignore` to exactly one entry (leg G12a). The fix keeps
the guard: the test now pins the *exact* two approved fingerprints and their
approval comments, so any unapproved addition still fails.

## 12. Addendum (2026-10-12): kept failures diagnosed, hosted results

Appended after the maintainer asked for the kept failures to be diagnosed
and, where possible, fixed. The text above is unchanged.

- **`WinError 32` (G09a, G13; also `final-6314532/04`).** The cause is now
  reproduced, so the earlier "holder unproven" no longer applies to the
  mechanism. With `--basetemp=X`, pytest deletes the *previous* session's
  `X` lazily inside `TempPathFactory.getbasetemp()` — the setup of the
  first test that requests `tmp_path` — with no retry. A transient handle
  on any leftover file makes that test error. The factory stays unset, so
  the next tests retry and may error too. That matches both captures: the
  errored nodes were the session's first `tmp_path` users, and the
  directories named belonged to the previous session. A synthetic
  reproduction (`EVIDENCE/0160/verification/test-reliability/W1`) gives the
  same errors. The fix is a `tests/conftest.py` session-start hook
  (`tests/_basetemp.py`) that deletes the same directory up front. It
  retries sharing violations within a bounded budget, clears read-only bits
  (git objects), refuses the rootdir and its ancestors, and turns a
  persistent holder into one clear usage error (`W2` passes; `W3` exits
  4 with the message). The external holder process itself is still not
  identified, and does not need to be.
- **G12a** was a real defect (SA-6), already fixed. **G14a** was a real
  Snyk finding, already fixed. **G16a** was an operator error (a relative
  interpreter path in the scratch runner); the runner now takes an absolute
  path.
- **Hosted results for `0d4278d`** (amendment #50 window): `gpu`, `parity`,
  `repro`, `snyk` (push and pull_request) and the forced `nightly`
  (`38184198596`; `bench-regression` and `full-suite`) succeeded. Two jobs
  failed:
  - `python` (`38184181265`), `lint` job: `mypy DOCS/experiments/
    --strict`, `no-any-return` in `exp001_driver.py:1230`. The lint job
    never installed numpy, so `np` resolved to `Any`. The step was added
    while hosted checks were paused, so it had never run hosted.
    Reproduced exactly in a venv that mirrors the job, and fixed by
    pinning the `.venv` numpy (`EVIDENCE/0160/verification/ci-fixes/C3*`).
  - `rust` (`38184181298`), `clippy` / `clippy-strict`: hosted stable
    Rust 1.99 flags a single-element `for` loop in
    `crates/prin-kernels/src/compat.rs`. Local Rust was 1.98; it was
    updated to 1.99, the failure reproduced, and the loop was rewritten
    with identical behaviour.

  These are latent pre-existing defects that hosted CI exposed, not
  regressions from this round's change.
- **Access violation in the fast suite (leg 09 of the 0159 bundle; also
  `EVIDENCE/0160/verification/gate/G12a`).** Both crashes happened in
  `os.walk`, called from the WP-001 repository-inventory test. Standalone
  reruns, with and without coverage, did not reproduce the crash, so its
  native root cause is **not proven**. The walk crossed about 110,800
  files (4.2 GB), mostly git-ignored scratch. Inside a work tree,
  `tools/wp001_baseline.py` now lists only git-visible files (about 4,500),
  and it still walks the tree outside git. Regression tests cover both
  paths. This removes most of the code path that crashed, but the root
  cause is still open.
