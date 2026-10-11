# PRIN Audit Report — PR #32 multi-review round (EA-007 EXP-002 readiness)

**Date:** 2026-10-11 UTC
**Auditor:** Claude Sonnet 5.5 (AI pair), re-deriving every claim from the
repository and from executed commands — not taking any reviewer's assertion on
its word. This report follows
[`TEMPLATE_Audit_Report.md`](TEMPLATE_Audit_Report.md) and the severity scale
of
[`Development_Workflow_and_Audit_Standards.md`](../standards/Development_Workflow_and_Audit_Standards.md)
§5, reusing the event-class precedent of
[`PR023-multi-review-audit.md`](PR023-multi-review-audit.md) and
[`PR017-devin-review-audit.md`](PR017-devin-review-audit.md) for external
review on an open PR. No dedicated governance document exists for this class,
and PR #32 is not a Session-Cycle S2: EA-007 is a global executive audit
outside sessions 0001–0198.
**Scope:** every review and audit comment on PR #32
(`audit/ea007-exp002-readiness` → `main`) at head `add7386a`, and the
repository state they describe — `AGENTS.md`, `.github/workflows/{python,rust}.yml`,
`pyproject.toml`, `tests/test_campaign_quality_gates.py`,
`crates/prin-sim/src/{lib,gpu}.rs`, `DOCS/audits/EXECUTIVE_AUDIT_REPORT_007.md`,
`DOCS/reports/{040-project-state,DEFERRED_VALIDATION_REGISTER}.md`,
`DOCS/sessions/SESSION_REGISTER.md`, `CHANGELOG.md`, and the whole
`EVIDENCE/ea007/` bundle with its `SHA256SUMS.txt`.
**Trigger:** GitHub PR #32. Seven independent review runs (14 GitHub
artefacts: 5 inline comments, 4 reviews, 5 issue comments):

| Reviewer | Kind | Findings raised |
|---|---|---|
| `sourcery-ai[bot]` | automated | 2 inline (both 🟡 Medium), reviewer's guide |
| `coderabbitai[bot]` | automated | 3 inline (🟡 Minor) + 1 failed pre-merge check (docstring coverage) |
| Devin Review | automated | 1 flag — **not published to GitHub** (project setting); the review page requires a login, so there is no text to validate |
| Kimi k2.7-code-highspeed | independent LLM review | 2 distinct (validated the bot findings) |
| PERPLEXITY-Deep-Research | independent LLM review | 2 distinct (validated the bot findings) |
| Qwen 3.8-Max-Preview | independent LLM review | 2 High, 9 Medium, 11 Low, nits; adjudicated every prior finding |
| SWE-2-High | independent LLM review | 0 new; re-verified Qwen's findings and the bot findings |

**Active brief:** no session-brief file — a PR review-response round on a
closed global audit, the same ad-hoc governance class as the two precedents.
EA-007's report is committed history and is amended by appended errata only
(`EXECUTIVE_AUDIT_REPORT_007.md` §7; `DOCS/audits/README.md`: audits are
append-only).
**Git state:** `audit/ea007-exp002-readiness` @ `add7386a` (pre-remediation);
the remediation commits follow — a commit cannot name itself.
**Regime:** Plan amendment #48 — hosted workflows disabled, the Windows local
gate is authoritative, Linux/macOS are **not tested**. Nothing here is a hosted
or CI result, and no merge-to-`main` claim is made.
**Verdict:** `PASS-WITH-FINDINGS` → remediated in the same round (§8).
**No D1.** No finding touches a numerical result, a hypothesis verdict, a
tolerance, a seed, or any production code path; `crates/prin-sim/src/gpu.rs`
is untouched and the EA-007 verdict (`PASS-WITH-REMEDIATION`, four findings
fixed, zero unresolved D1/D2) stands exactly as issued.

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| Independent re-derivation of every reported claim | ✅ | 14 artefacts, 7 reviewers; every claim re-derived by an executed command or a quoted line at head (§3). |
| False positives / over-reach | ✅ | One check waived (CodeRabbit docstring coverage — not a project gate); one headline rejected while its instruction was kept (CodeRabbit `GATE-STATUS.md`); Qwen's and SWE-2's blanket "reject" of it was itself imprecise (§3.1). No reviewer fact was found wrong, but several remedies were. |
| Severity classification | ✅ | 2 × D2, 6 × D3, 7 × D4. **No D1.** |
| Regression tests (A3) | ✅ | 6 new tests + 2 strengthened; a defect-catching proof runs each new test and both strengthened ones against the pre-fix or a mutated input: **63/63 expectations met** (§6, leg L11). |
| Numerical parity + invariants (A4) | ➖ | Not applicable and not claimed: no runtime, numerical or Rust source changed. |
| Quality gates (A5) | ✅ | ruff, ruff format, mypy `--strict` ×2, bandit (24,864 LOC scanned, non-vacuous), interrogate 97.6 % — all exit 0 (§6). |
| Security (A6) | ✅ | Snyk Code 0 issues on the two test modules and the proof harness; gitleaks 8.30.1 staged-diff scan clean; no dependency manifest changed, so Snyk Open Source / `cargo audit` / `pip-audit` have no changed input. Native push protection stays disabled (flagged by #48); no claim that it passed. |
| Docstring / doc coverage (A7) | ✅ | `interrogate` unchanged at 97.6 %; CodeRabbit's docstring check waived with evidence (§7). |
| Repository hygiene (A8) | ✅ | `git diff --check` clean; no hidden/bidi control characters in the files changed against the PR base (leg L20); a latent `git add` hazard (`*.log` is gitignored) found and now guarded by a test (§4, `PR32-F7`). |
| CI status (A9) | ➖ | Hosted CI is paused (amendment #48). Local gate evidence replaces it; the new `rust.yml` step is **not** hosted-validated (§8). |
| Artefact trail (A10) | ✅ | This report, `CHANGELOG.md`, `DOCS/audits/README.md`, EA-007 report §7 errata, the DV-register dated section, PSR-040 corrections, and the evidence bundle. |

## 2. Methodology

Reviews were fetched from the GitHub API rather than read from a summary:

```bash
gh pr view 32 --json title,state,headRefName,headRefOid,body,statusCheckRollup
gh api repos/Symbo-gif/PRIN/pulls/32/comments  --paginate   # 5 inline comments
gh api repos/Symbo-gif/PRIN/pulls/32/reviews   --paginate   # 4 reviews
gh api repos/Symbo-gif/PRIN/issues/32/comments --paginate   # 5 issue comments
```

The distinct claims were compiled (the bot findings recur in the four LLM
reviews), then each was re-derived **before** any fix was written: by reading
the cited line at `add7386a` (`git show add7386a:<path>`), by recomputing a
digest or count, or by running the cited command. The live-state claims in the
EA-007 report were re-queried (`gh api` workflows, ruleset `22150076`, runners,
`security_and_analysis`; `tools/check_ci_green.py 32cfed8a…` → `RESULT: all
required workflows green`): all reproduce.

**Local gate** (Windows 11 `10.0.26300`, Python 3.14.0, ruff 0.16.1, mypy 2.3.0,
bandit 1.9.4, Rust 1.98.1, Snyk CLI 1.1306.2, gitleaks 8.30.1, Windows
PowerShell 5.1.26100.9549 and PowerShell 7.6.6) is the leg list in §6, executed
serially by one runner (evidence tooling, not committed — §6) whose verbatim
output is committed as
`EVIDENCE/ea007/verification/pr32-review/pr32-gate-run.log`. Where a gate was
not run, §6 says so rather than claiming it passed (Coding Standards §6
item 5).

**Security gates (Coding Standards §6).** The new/modified first-party Python is
`tests/test_campaign_quality_gates.py`, the new `tests/test_ea007_manifest.py` and
the new proof harness `EVIDENCE/ea007/verification/pr32-review/proof_defect_catching.py`,
so Snyk Code applies (leg L16). No dependency manifest changed, so Snyk Open
Source, `cargo audit` and `pip-audit` have no changed input; EA-007's own
clean runs stand and are not repeated here. GitHub secret scanning and push
protection are independent controls that this round neither exercises nor
replaces; push protection remains disabled.

**Delegation record.** The maintainer authorized orchestrating the Antigravity
(`agy`) and Devin (SWE-2) CLI agents. The first launches needed
permission-bypass options (`--dangerously-skip-permissions`; Devin's
`--permission-mode smart` with `--respect-workspace-trust false`), which the
session's safety classifier refused — before and after the maintainer's
mid-session grant — and they were not worked around. Both agents were instead
run in their **read-only mode** (file reads only: no shell, no edits, report on
standard output), which needs no bypass. They were used for independent cold
review of the remediation (§9); everything that required executing commands
was run by the auditor.

**Remediation plan (execution order).** Ordered so that no step invalidates
another — hash-pinned files last:

1. Ground truth (§3): no edits.
2. Mutable records: `AGENTS.md`, PSR-040, `SESSION_REGISTER.md`, `CHANGELOG.md`,
   the READMEs, `DOCS/experiments/README.md`.
3. Append-only records: EA-007 report §7 errata, the DV-register dated section,
   this report and its index entry (`DOCS/audits/README.md` forbids editing a
   committed audit body).
4. Guards and configuration: the regression tests and `rust.yml`.
5. Frozen evidence: the new `post-commit/` and `pr32-review/` files and the
   `GATE-STATUS.md` corrections, then `SHA256SUMS.txt` regenerated **last**.
6. Verification (§6) on the staged tree, then a confirmation re-run of the
   manifest checks after regeneration.
7. Independent cold review (§9), fixes, re-verification.
8. Commit; post-commit secret scan and full suite; hand-off (§8).

## 3. Reviewer adjudication (ground truth)

### 3.1 The two bots and the three LLM reviews that followed them

| ID | Claim | Verdict | Ground truth | Disposition |
|---|---|---|---|---|
| Sourcery S1 / CodeRabbit CR1 | Audit report and PSR-040 retain the 704-commit scan and say a post-commit scan is required, although the PR body reports a clean 707-commit scan at `add7386a` | **PARTIALLY CONFIRMED** | The reports are *accurate about the committed tree* (`15-gitleaks-scan.log` header: `SHA: fdd28d88…`, `2026-10-11T04:07:48Z`; `git rev-list --count fdd28d88..add7386a` = 3, so 704 + 3 = 707). The real defect is that the 707-commit result had **no repository-resident evidence**. | `PR32-F2` |
| Sourcery S2 / CodeRabbit CR2 | PSR-040's ledger metric repeats the 038→039 result | **CONFIRMED** | `check_deviation_ledger.py` 039 → 040 = 142 → 146 rows (L13a); 038 → 039 = 128 → 142 | `PR32-F4` |
| CodeRabbit CR2 (anchor) | "Line 68 … update the *Full local gate* row" | **MIS-TARGETED** | The stale row is line **67**; line 68 is the *Full local gate* row. Applying the agent prompt literally would edit the wrong row. | noted |
| CodeRabbit CR3 | "Fix the commit count in leg 15" of `GATE-STATUS.md` | **PARTIALLY CONFIRMED** | The headline is wrong — 704 is the correct count for what leg 15 scanned and must not change. The *instruction* ("clarify that the 704-commit scan ran before later commits … preserve the existing scan result") is right and equals Qwen's own `H-2c` fix. Qwen's and SWE-2's blanket "REJECT" holds only for a count change or an edit without regenerating `SHA256SUMS.txt`. | accepted as an additive scope note, manifest regenerated (`PR32-F3`) |
| CodeRabbit pre-merge | Docstring coverage 60 % < 80 % | **WAIVED** | Not a project gate (§7) | waived, §7 |
| Devin | 1 flag | **NOT REVIEWABLE** | Unpublished; the page requires a login (re-attempted with a fetch: no content) | recorded |
| Kimi | "no additional source defect"; tests "environment-independent" | **PARTIALLY REFUTED** | Missed `PR32-F1` (its validation table lists the line as passed, consistent with a Git Bash or PowerShell 7 run, both of which accept the bad quoting). "Environment-independent" is right in conclusion for the wrong reason: the bandit tests pass on both platforms because `fnmatch` applies `normcase` to name and pattern, not because they are platform-agnostic. | noted |
| Perplexity | Two record defects; "no new functional defect in the source/configuration changes"; `GATE-STATUS` leg 15 needs a 704-versus-707 distinction | **SUBSTANTIALLY CORRECT, INCOMPLETE** | Both record defects and the self-reference caveat (a scan of `add7386a` can only be recorded by a *later* commit about an ancestor) are right. It missed `PR32-F1` (a configuration defect) and the `PR32-F3` fidelity breaks. Its reproduced checks re-ran clean here (82/82 manifest, 6/6 source hashes at the `add7386a` blobs, all governance checkers). | `PR32-F2`, `PR32-F3` |
| SWE-2-High | Re-verified Qwen's findings | **CORRECT** | Every checkable claim reproduces, including its correction that `039-project-state.md` carries no ledger-checker row (the bare-label convention is evidenced by `038:66` alone, which this audit confirmed). | — |

### 3.2 Qwen 3.8-Max-Preview

| ID | Claim | Verdict | Evidence re-derived here | Disposition |
|---|---|---|---|---|
| H-1 | `AGENTS.md:36` fails under Windows PowerShell 5.1 | **CONFIRMED (executed)** | L03a: PS 5.1.26100.9549, the verbatim `AGENTS.md` line → `error: invalid value 'include = [*.py, *.pyi, *.ipynb]'`, exit 2. PowerShell 7 and Git Bash accept it (L04a, L05). | `PR32-F1` |
| H-2a | Leg 19 says 146, its log says 145 | **CONFIRMED** | `19-deviation-ledger-039-040.log` (04:08:22Z): 142 → **145**; `26a-…` (06:35:17Z): 142 → 146 | `PR32-F3` |
| H-2b | Leg 22 says "274 pins", the resolver says 100 | **CONFIRMED** | `22-uv-compile.log`: `Resolved 100 packages`; `prin-requirements.txt`: 274 lines = 100 `name==version` + 174 comment lines (100 `# via` headers, 72 continuations, 2 header lines), 0 `--hash` | `PR32-F3` |
| H-2c | Leg 15 `PASS` has no scope caveat; no log records `add7386a` | **CONFIRMED** | Census of 77 `.log` files: 66 record `fdd28d88`, 8 record `cb40584a`, 3 record no SHA, 0 record `add7386a` | `PR32-F2`, `PR32-F3` |
| A / B / C | Adjudication of the bot findings | **A, B CONFIRMED; C imprecise** | Above (§3.1). | — |
| M-1 | DV-042 delta cites a vacuous workspace-rustdoc leg | **CONFIRMED (D4)** | `lib.rs:77-78` gates `pub mod gpu` on `cpu`/`cuda`/`wgpu`; `Cargo.toml` `default = []`; `24-rustdoc-workspace.log` ran at the defective base `fdd28d88` and exited 0 | `PR32-F8` |
| M-2 | `rust.yml` never documents the gated module | **CONFIRMED** — a *disclosed* EA-007 decision ("optional hosted workflow doc leg is not added"), but the exposure is real, and the **local** gate (`AGENTS.md`) had the same blind spot | `rust.yml:135`: `cargo doc --workspace --no-deps`, no `--features` | `PR32-F9` |
| M-3 | Five citations into a gitignored tree | **CONFIRMED** | `git grep` at `add7386a` outside the bundle: `EXECUTIVE_AUDIT_REPORT_007.md:268`, `040-project-state.md:68` and `:156`, `DEFERRED_VALIDATION_REGISTER.md:64`, `EVIDENCE/ea007/README.md:17`; `.gitignore:104`; `git ls-tree` empty | `PR32-F6` |
| M-4 | Nothing executes `SHA256SUMS.txt` | **CONFIRMED** | `git grep SHA256SUMS add7386a -- tools tests .github` → no hit | `PR32-F7` |
| M-5 | 5 of 87 tracked evidence files are outside the manifest | **CONFIRMED** | `README.md`, `readiness-state.json`, the two top-level `.log` captures, and `SHA256SUMS.txt` itself | `PR32-F7` |
| M-6 | The `.gitattributes` rule failed once inside the PR | **CONFIRMED (historical)** | 36 of 82 digests mismatch at `0738714`, 0 at `add7386`; `add7386` = 38 files, +13,420 / −13,420 | `PR32-F7` (guard) |
| M-7 | PSR-040 §2 drops the seven template rows | **CONFIRMED** | `TEMPLATE_Project_State_Report.md` §2 fixes seven rows; PSR-040 carried four | `PR32-F5` |
| M-8 | No EA-007 Review-log entry or dated section | **CONFIRMED (D4)** | `EA-007` occurs in the register only in seven DV cells; latest dated sections are 2026-09-28/29 | `PR32-F10` |
| M-9 | Two `EXIT_CODE=2` logs unreachable from the index | **CONFIRMED** | `22-` and `22b-snyk-sca-mainmanifest.log` are the only `EXIT_CODE=2` logs and neither is named in the index | `PR32-F3` |
| L-1 | `mypy DOCS/experiments/ --strict` dies on duplicate basenames | **CONFIRMED (reproduced)** | Two sibling trees sharing `quality.py` → `Duplicate module named …`, `errors prevented further checking` | `PR32-F12` |
| L-2 | Test job installs bandit unpinned; the test imports a private symbol | **CONFIRMED, DECLINED** | §7 | `PR32-F13` |
| L-3 | The component-glob test asserts shape, not effect | **CONFIRMED** | `does-not-exist/*`, `../../*` pass a suffix check | `PR32-F14` |
| L-4 | `13a-cargo-audit.log:5` prints a home-directory path | **CONFIRMED, DECLINED** | §7 | — |
| L-5 | Eight logs record a third SHA; the header over-claims | **CONFIRMED** | Census above; `gpu.rs` byte-identical at both SHAs | `PR32-F3` |
| L-6 | Report says "18 … failed" next to "13 failed, 5 passed" | **CONFIRMED** | `dv040-newtests-oldconfig.log`: `13 failed, 5 passed` | `PR32-F11` |
| L-7 | Future-tense re-staging already done | **CONFIRMED** | `add7386` performed it | `PR32-F11` |
| L-8 | `SESSION_REGISTER.md:266` Git-state cell stale | **CONFIRMED** (also the PSR-040 header) | `@ fdd28d8 + worktree changes` vs three commits | `PR32-F11` |
| L-9 | `26h` says "the files this diff touches", hashes six | **CONFIRMED** | `git diff --name-only fdd28d88 add7386a` outside `EVIDENCE/ea007/` lists 19 files (Qwen and SWE-2 say 18; immaterial). All six hashes match the `add7386a` blobs. | `PR32-F11` |
| L-10 | No CHANGELOG entry for the `.gitattributes` exemption | **CONFIRMED** | Only precedent at `CHANGELOG.md:1137` | `PR32-F11` |
| L-11 | Two byte-identical requirement files; "frozen" overstates | **CONFIRMED, DECLINED** | `cmp` identical; 0 `--hash` lines | §7 |
| Nits | See §7 | mixed | | `PR32-F11`, `PR32-F15`, §7 |

**Qwen's accuracy.** Every checkable finding reproduced. Imprecisions, none
affecting a verdict: it cited `038:66` *and* `039:63` for the bare-label
convention (`039` has no such row); its census of "87 files" is a different
denominator from the 77 `.log` files counted here (66 / 8 / 3 versus 67 / 8 /
12); and its Part 4 sequence recommends editing `GATE-STATUS.md` for `H-2`
while its adjudication `C` rejects the same edit — consistent only if "reject"
means "never without regenerating the manifest", which is the reading adopted
here.

### 3.3 Claims checked and found sound

Not every statement needed action, but each was verified rather than assumed:

- The headline test result: `25-pytest-final.log` → `5667 passed, 184 skipped,
  61 warnings in 1782.21s`, `EXIT_CODE=0`; `parity/` accounts for 2,144 passed
  and 1 skipped of those.
- DV-040's mechanism: the pre-change log `dv040-bandit-experiments-prefix.log`
  reports `Total lines of code: 0` (a vacuous gate); the fixed configuration
  scans **24,864** LOC (L09), 4,648 of them campaign code.
- `crates/prin-sim/src/gpu.rs` is documentation-only; under `--features cpu`
  the `gpu` module page is emitted and rustdoc exits 0 with `-D warnings`
  (L12, L12b).
- `26h-source-hashes.txt`: 6/6 entries match the `add7386a` blobs.
- `SHA256SUMS.txt`: 82/82 at `add7386a` (recomputed); 93 entries after this
  round, all matching. The committed leg L15 (`sha256sum -c`, 93 OK) ran
  against the manifest as it stood before the last packaging pass; the four
  `pr32-review/` files it lists are replaced by this log's final bytes after
  the run and the manifest regenerated, and that last re-verification
  (93 OK; `tests/test_ea007_manifest.py` 3 passed) is not logged — a log inside
  the manifest cannot cover itself — but the committed test re-checks it on
  every run.
- The EA-007 report's hedging is present verbatim: "suspended, not satisfied",
  "no merge-to-main … claim", E6 "historical entry evidence, not current-branch
  CI validation", and no push-protection claim.
- No hidden or bidirectional Unicode controls in the files changed by the PR and
  this round (leg L20: 117 of the 118 files changed against the PR base scanned, 0 hits; the
  118th, the raw `historical-nightly-and-merge-capture.log`, is not UTF-8).

## 4. Detailed findings

### 4.1 `PR32-F1` (D2) — the documented local gate failed on Windows PowerShell 5.1

*Raised by Qwen (`H-1`); confirmed by SWE-2-High. Missed by Sourcery,
CodeRabbit, Kimi and Perplexity.*

`AGENTS.md` is the authoritative local-gate document while amendment #48 is in
force, on a Windows host whose stock `powershell.exe` is 5.1. Its fenced
`powershell` block carried

```text
.venv\Scripts\ruff format --check DOCS/experiments/ --config 'include = ["*.py", "*.pyi", "*.ipynb"]'
```

PowerShell 5.1 strips double quotes embedded in a single-quoted native-command
argument, so ruff receives `include = [*.py, *.pyi, *.ipynb]`, which is not
TOML. Executed verbatim (L03a): the error is
`invalid value 'include = [*.py, *.pyi, *.ipynb]' …`, **exit 2**, on a gate that
is actually clean. PowerShell 7 and Git
Bash accept the line (L04a, L05), which is why two reviews listed it as
`Passed`. The 19 original tests text-match the line with `shlex`, so they could
not detect it.

**Severity: D2, not D1.** No result or property changed and the gate itself is
green (L03b: `2 files already formatted`); a normative gate command that fails
on its declared host is a standard violation.

**Fix.** Swap which quotes are outer, using TOML literal strings:
`--config "include = ['*.py', '*.pyi', '*.ipynb']"` — exit 0 on Windows
PowerShell 5.1, PowerShell 7 and Git Bash (L03b, L04b, L05 for the unchanged
bash form in `python.yml`). **Regression test:**
`test_agents_powershell_block_has_no_embedded_double_quotes` rejects any
single-quoted argument containing a double quote in a `powershell` block
(tokenized left to right, so `cmd 'a' "b" 'c'` is not a false fail and a CRLF
checkout still parses); it fails against the `add7386a` file (L11).

### 4.2 `PR32-F2` (D2) — the final secret scans had no repository-resident evidence

*Raised by Sourcery, CodeRabbit, Kimi, Perplexity, Qwen (`A`), SWE-2-High.*

`EXECUTIVE_AUDIT_REPORT_007.md` §E4 and `040-project-state.md` §5 recorded the
704-commit gitleaks scan and said a post-commit scan "remains required". That
was **true of the committed tree** — and stale in effect: the trigger ("if new
commits are added") fired, the rescans were run, and the PR body reports them,
but they existed only under the gitignored
`DOCS/test_and_benchmark_results/ea007/post-commit/` (`.gitignore:104`;
`git ls-tree -r add7386a -- DOCS/test_and_benchmark_results` is empty):

| Scan | SHA | UTC | Commits | Bytes | Result | SHA-256 of log |
|---|---|---|---|---|---|---|
| leg 15 (historical, base) | `fdd28d88` | 04:07:48Z | 704 | 72,396,365 | no leaks, exit 0 | in `SHA256SUMS.txt` |
| post-commit (intermediate; mentioned by no reviewer) | `0738714` | 06:45:21Z | 706 | 74,660,300 | no leaks, exit 0 | `c352394a…` |
| post-commit (final) | `add7386a` | 06:47:37Z | 707 | 76,069,831 | no leaks, exit 0 | `7dc9eeb3…` |

**Severity: D2** — a mandatory Coding Standards §6 control was asserted in the
PR body without evidence in the record. Not D1: the results are clean and
nothing leaked.

**The self-reference trap.** A scan of `add7386a` cannot be written *into*
`add7386a`: the write changes the head. Sourcery's and CodeRabbit's remedy
("preserve the 704 result as historical and record the 707 scan") is sound only
as a statement made by a **later** commit about an **ancestor**, worded about
the commit it names — and this round's own commit cannot contain its own scan
result either (§6).

**Fix.** The four artefacts are committed byte-exact under
`EVIDENCE/ea007/verification/post-commit/` (`git add -f`: `*.log` is
gitignored) and hashed in the manifest; PSR-040 §5 keeps the 704 result as
historical and appends the two later scans; EA-007 report §7 `ER-1`
supersedes the "remains required" sentence; `EVIDENCE/ea007/README.md`
states the self-reference rule.

### 4.3 `PR32-F3` (D3) — `GATE-STATUS.md` was not a faithful transcription of its logs

*Raised by CodeRabbit (`CR3`, leg 15) and Qwen (`H-2a/b/c`, `M-9`, `L-5`).*

The index is the bundle's reader-facing entry point and is hash-pinned, so it
was corrected **in place with `SHA256SUMS.txt` regenerated in the same
commit** (git history keeps the earlier text; recorded for readers of the
EA-007 report as its errata `ER-6`, and the same wording fix was applied to
`verification/README.md`, which repeated the header's over-claim):

| Cell | Before | After | Source of truth |
|---|---|---|---|
| Header | "logs embed verbatim command/host/SHA/UTC/exit code" | command, host and UTC in every log; SHA and `EXIT_CODE` in most; census and scope note added | 66 / 8 / 3 SHA census; 5 logs without `EXIT_CODE`; two header formats |
| Leg 15 | unqualified `PASS — 704 commits …` | result unchanged; **scope: history through base `fdd28d88` only**, pointer to `../post-commit/` | log header `SHA: fdd28d88…` |
| Leg 19 | `142 → 146 rows after E-F4 append` | `142 → 145 rows at this leg (04:08Z …); the final 142 → 146 result is leg 26a` | `19-…log`: 145; `26a-…log`: 146 |
| Leg 22 | `274 pins`; Log cell names two files | `100 pinned packages` (274-line manifest = 100 pins + 174 comment lines); Log cell adds the two `EXIT_CODE=2` Snyk logs | `22-uv-compile.log`; `prin-requirements.txt` |

Severity **D3**: no verdict flips (all legs exit 0), but an auditor
reconciling index against logs hit a false mismatch on the first cross-check
and an unqualified `PASS` implied a scope the scan did not have.

### 4.4 `PR32-F4` (D3) — PSR-040's ledger metric repeated the previous cycle

*Raised by Sourcery, CodeRabbit, Kimi, Perplexity, Qwen (`B`), SWE-2-High.*

`040-project-state.md:67` read `Deviation-ledger checker 038→039 | exit 0 (128
→ 142 rows) | exit 0 (128 inherited → 142 rows)`. Root cause: a label-convention
break — `038-project-state.md:66` labels the row with the bare tool name and
lets the Previous/Current columns carry each cycle's pair; PSR-040 baked a
cycle pair into the label, which forced Current to repeat Previous. Truth
(L13a): 039 → 040 = **142 → 146**; 038 → 039 = 128 → 142. **Fix:** bare label,
`038→039: exit 0 (128 → 142 rows)` previous, `039→040: exit 0 (142 → 146
rows)` current.

### 4.5 `PR32-F5` (D3) — PSR-040 §2 dropped the seven template rows

*Raised by Qwen (`M-7`, plus the missing `Completed sessions` header field).*

`TEMPLATE_Project_State_Report.md` §2 fixes seven metric rows; PSR-040 carried
four and none of the seven — including `Coverage (new/changed code) ≥95 %`,
the one gated row that is *currently unmeasured* (DV-033 open), which is
precisely the row whose trend must not disappear. Restored from the
EA-007 logs only, with `Coverage` stated as `not measured — DV-033 OPEN … NOT
MET (unmeasured)`, parity stated as the `parity/` node count inside leg 25
(corpus/fuzz counts were not re-derived this cycle), and benchmark gates stated
as not exercised. The `Completed sessions` field is added.

### 4.6 `PR32-F6` (D3) — reports cited a gitignored tree as their evidence

*Raised by Qwen (`M-3`).* Five sites cite
`DOCS/test_and_benchmark_results/ea007/…`, which is ignored and unreachable from
any clone; two are sole-source,
including the headline 5,667-test claim. Repointed to the committed
`EVIDENCE/ea007/verification/full-gate/` in `040-project-state.md` (both
sites) and `EVIDENCE/ea007/README.md` (the scratch tree is now labelled
gitignored and local); recorded as errata `ER-4` for the audit report and in
the register's dated section for `DV-033` (the report and register are
append-only).

### 4.7 `PR32-F7` (D3) — the evidence manifest was neither executable nor complete

*Raised by Qwen (`M-4`, `M-5`, `M-6`).* Nothing ran `SHA256SUMS.txt`
(`tools/reproduce.py::verify_manifest` verifies a JSON `manifest.json` inventory of
`*.json` artefacts, not a coreutils `SHA256SUMS.txt` of logs);
5 of 87 tracked files were outside it, including `readiness-state.json` (the
maintainer-approval artefact) and the two top-level captures; and the
manifest **failed for 36 of its 82 entries at `0738714`** because the
`.gitattributes` byte-exactness rule landed in the same commit as the files it
protects (`add7386` repaired it; the head verified 82/82). History is not
rewritten.

**Fix.** `tests/test_ea007_manifest.py` (3 tests) parses the manifest
fail-closed (malformed line, duplicate, absolute or `..`-escaping path,
missing file or wrong letter case, digest mismatch), requires every other file
under `EVIDENCE/ea007/` to be listed (the manifest itself and the top-level
`README.md` are the only exemptions; OS metadata such as `.DS_Store` is
ignored), and requires every hashed file to be tracked by git. Paths are
compared as exact-case POSIX strings, not resolved on disk, so a wrong letter
case fails on Windows and macOS exactly as it does on Linux. The third test
exists because `*.log` is gitignored repository-wide: **this round almost
committed the post-commit gitleaks logs hashed but unstaged** — locally green,
absent from every clone. The manifest now also lists `../readiness-state.json`
and the two `../*.log` captures (93 entries once this round's four evidence
files are added). Each test fails against the matching mutation (L11: drifted
byte, omitted file, missing file, wrong letter case, escaping path, malformed
line, duplicate line, hashed-but-untracked log).

### 4.8 `PR32-F8` (D4) — the DV-042 delta cited a leg that cannot validate

*Raised by Qwen (`M-1`).* The register's EA-007 delta says "the workspace
`cargo doc --workspace --no-deps` leg also exits 0". True and non-evidential:
`prin_sim::gpu` is `#[cfg(any(feature = "cpu", "cuda", "wgpu"))]` with
`default = []`, and the same leg exited 0 at the *defective* base
(`24-rustdoc-workspace.log`). The three feature legs carry the evidence.
Recorded as report errata `ER-5` and in the register's dated section (both
append-only).

### 4.9 `PR32-F9` (D3) — the rustdoc gate could not catch DV-042 again

*Raised by Qwen (`M-2`).* EA-007 deliberately did not add a hosted doc leg
("the bounded fix's local feature legs provide evidence"). The decision was
disclosed, but under #48 the **local** gate in `AGENTS.md` is authoritative and
it had the same blind spot (`cargo doc --workspace --no-deps`), so a future
regression of DV-042's class would pass every gate that exists. **Fix:**
`AGENTS.md` gains `$env:RUSTDOCFLAGS='-D warnings'; cargo doc -p prin-sim
--no-deps --features cpu`; `rust.yml` gains the matching step (job-level
`RUSTDOCFLAGS` already applies);
`test_rustdoc_gate_documents_the_feature_gated_gpu_module` pins the hosted step
(a `cpu`/`cuda`/`wgpu` feature, with `-D warnings` set in that job's job-level
`env`)
and the `AGENTS.md` line, and fails against `add7386a`, against a non-backend
feature such as `strict-checks`, against a lost job `env`, and against a deleted
local line (L11). The local leg ran (L12:
exit 0; L12b: the `gpu` module page is emitted, so the leg is non-vacuous).
**The hosted step is not validated** — workflows are paused — and `cpu` is the
cheapest backend that compiles the module, not a substitute for the `wgpu`/`cuda`
legs EA-007 ran.

### 4.10 `PR32-F10` (D4) — no dated EA-007 section in the DV register

*Raised by Qwen (`M-8`).* The register's update protocol was met by seven
append-only in-cell deltas, but every cycle since the Review log lapsed on
2026-09-18 also records a dated `##` narrative section, and EA-007 had none.
Added (`DEFERRED_VALIDATION_REGISTER.md`, last section) — it also carries the
corrections for `PR32-F6` and `PR32-F8`. The proposal to extend
`check_global_session_registration.py` to require it is declined (§7).

### 4.11 `PR32-F11` (D4) — record-currency and wording defects

*Raised by Qwen (`L-6`–`L-10`, nits).*

- EA-007 report §2 E3: "The 18 quality-gate tests failed … (13 failed, 5
  passed)" → errata `ER-2` (13 of 18 failed).
- EA-007 report §2 E6: "will be re-staged byte-exact" → errata `ER-3` (done in
  `add7386`).
- `SESSION_REGISTER.md` EA-007 row and PSR-040 header: `@ fdd28d8 + worktree
  changes` → the three commits plus "remediation commits"; "no commit SHA
  claimed yet" is *correct* (the main-delivery state) and kept.
- `26h-source-hashes.txt` scope wording → explained in `EVIDENCE/ea007/README.md`
  (the file is hashed; it binds the six executed-against files, not all 19
  non-evidence files of the PR).
- `CHANGELOG.md`: the `.gitattributes` `EVIDENCE/ea007/** -text` exemption has
  no entry (precedent at the `benchmarks/results/**` bullet) and the EA-007
  entry under-lists the PR's artefacts → added.
- `verification/README.md`: "every file in this directory" (82 of 83) →
  reworded.

### 4.12 `PR32-F12` (D4) — duplicate campaign analysis basenames break the mypy gate

*Raised by Qwen (`L-1`).* Reproduced: two sibling campaign trees with a
`quality.py` each make `mypy DOCS/experiments/ --strict` abort with
`Duplicate module named "quality"` — not a typing error, and
`--explicit-package-bases` does not help. Green today only because the two
existing scripts happen to be uniquely prefixed (`exp001_e4_analysis.py`,
`exp001_r1_e4_analysis.py`) while seven more `EXP-*` roots exist. **Fix:** the
rule is stated in `DOCS/experiments/README.md` (the frozen campaign plan is
deliberately not edited) and `test_campaign_analysis_script_basenames_are_unique`
turns a confusing future CI failure into a named one. It computes module names
the way mypy crawls packages (so differently named packages with
`__init__.py` files are not false failures, and two campaigns shipping a package
`util` are real ones), covers `.pyi` stubs (a module beside its own stub is one
module), and fails on two campaigns sharing a name (L11).

### 4.13 `PR32-F13` (D4) — bandit floats in the hosted `test` job — **declined**

See §7.

### 4.14 `PR32-F14` (D4) — the exclusion-glob test asserted shape, not effect

*Raised by Qwen (`L-3`).* `test_bandit_exclusions_are_component_globs` accepted
any pattern ending `/*`: `does-not-exist/*`, `zzz/*` and `../../*` pass while
excluding nothing, and a Windows-only `.venv\*` spelling would silently exclude
nothing on a POSIX runner. **Fix:** a truth table — every pattern must be
`d/*` or `*/d/*` with a single component, the `tests`/`benchmarks`/`parity`
components must be present, each component must have both forms, files at the
top level and nested under it must be excluded, and a campaign slug that merely
contains the name must stay in scope. Against five mutated lists the old
suffix check would have passed **all five** and the new test fails all five
(L11).

### 4.15 `PR32-F15` (D4) — the `urllib3` floor test was brittle

*Raised by Qwen (nits).* The regex ended `\s*$` (a trailing `# CVE-…` comment
would fail it) and `re.search` inspected only the first match; a cold review
then showed that patching the regex would still reject `urllib3<3,>=2.8.0`,
`>=2.8` and environment markers. The test now parses each non-comment line as
a PEP 508 requirement (`packaging`, a `pytest` dependency): every `urllib3`
entry must admit 2.8.0 and exclude 2.7.0, 2.7.99, 2.0.0 and 1.26.20, and a
commented-out entry is not a requirement, so it cannot satisfy it.

## 5. Issues found

| ID | Severity | Location | Issue | Remedy | Status |
|---|---|---|---|---|---|
| `PR32-F1` | **D2** | `AGENTS.md:36` | Gate line fails on Windows PowerShell 5.1 | TOML literal-string quoting + test | FIXED |
| `PR32-F2` | **D2** | `EXECUTIVE_AUDIT_REPORT_007.md` §E4, `040-project-state.md` §5, PR body | Final secret-scan results (706/707 commits) not in the record; reports said "rescan required" | Artefacts committed; PSR updated; errata `ER-1` | FIXED |
| `PR32-F3` | D3 | `GATE-STATUS.md` | Index misquotes legs 19 and 22, unscoped leg 15, unindexed logs, overstated header | Corrected in place; manifest regenerated | FIXED |
| `PR32-F4` | D3 | `040-project-state.md:67` | Ledger metric repeated 038→039 | Bare label; 142 → 146 | FIXED |
| `PR32-F5` | D3 | `040-project-state.md` §2, header | Seven template rows and `Completed sessions` dropped | Restored from logs | FIXED |
| `PR32-F6` | D3 | five sites | Evidence cited in a gitignored tree | Repointed; errata `ER-4`; register note | FIXED |
| `PR32-F7` | D3 | `EVIDENCE/ea007/verification/SHA256SUMS.txt` | Not executable, incomplete, failed at `0738714` | `tests/test_ea007_manifest.py` (3); manifest extended | FIXED |
| `PR32-F9` | D3 | `rust.yml`, `AGENTS.md` | Rustdoc gate never documents the feature-gated module | Feature-bearing leg + test | FIXED (hosted leg unvalidated) |
| `PR32-F8` | D4 | `DEFERRED_VALIDATION_REGISTER.md` DV-042 | Vacuous leg cited as validation | Errata `ER-5`; dated section | FIXED |
| `PR32-F10` | D4 | `DEFERRED_VALIDATION_REGISTER.md` | No dated EA-007 section | Added | FIXED |
| `PR32-F11` | D4 | report, `SESSION_REGISTER.md`, PSR, `CHANGELOG.md`, READMEs | Wording / currency defects | Errata + in-place edits | FIXED |
| `PR32-F12` | D4 | `DOCS/experiments/` | Duplicate basenames break mypy | README rule + test | FIXED |
| `PR32-F14` | D4 | `tests/test_campaign_quality_gates.py` | Shape-only exclusion test | Truth table | FIXED |
| `PR32-F15` | D4 | `tests/test_campaign_quality_gates.py` | Brittle `urllib3` floor regex | Tolerant, all-match | FIXED |
| `PR32-F13` | D4 | `python.yml` `test` job | bandit unpinned for a private-API test | — | DECLINED (carried, §7) |

**Deviation-ledger delta.** No new ledger rows. The ledger lives in the
numbered Project State Reports, and this round is not a Session Cycle — the
disposition `PR017-devin-review` and `PR023` took. PSR-040's ledger (§3.4) is
unchanged (142 → 146, L13a). The next PSR inherits this report as prior art.
Carried findings re-inspected: `DV-033` (coverage), `DV-034` (single-runner
SPOF) — unchanged, OPEN; `DV-040` (campaign analysis code in the gates) —
strengthened by `PR32-F1`/`F12`/`F14`, re-audit gate unchanged (EXP-002 E4).

## 6. Verification

Executed on the staged remediation tree (HEAD `add7386a` + the round's edits,
Windows 11 `10.0.26300`, host `HP`), serially, by one runner whose output is
committed verbatim as `EVIDENCE/ea007/verification/pr32-review/pr32-gate-run.log`
(user-profile paths redacted to `%USERPROFILE%`). The runner is evidence tooling
that hard-codes host paths and whose environment-variable plumbing Snyk Code
flags, so it is **not committed** — only its SHA-256 is recorded
(`pr32-source-hashes.txt`); each leg's `COMMAND:` line is the reproducible unit.
The proof harness behind L11, which Snyk Code finds clean, is committed beside
the log.

| Leg | Command | Result |
|---|---|---|
| L01 | `ruff check python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/` | exit 0 |
| L02 | `ruff format --check python/ tests/ benchmarks/ tools/ parity/` | exit 0 |
| L03a | `AGENTS.md` campaign-format line from `add7386a`, **Windows PowerShell 5.1** | **exit 2** (defect reproduced) |
| L03b | same line, working tree | exit 0 — `2 files already formatted` |
| L04a/b | same, PowerShell 7 (pre-fix / post-fix) | exit 0 / exit 0 |
| L05 | `python.yml` bash form (unchanged) | exit 0 |
| L06 | `mypy python/prin --strict` | exit 0 — 62 source files |
| L07 | `mypy DOCS/experiments/ --strict` | exit 0 — 2 source files |
| L08 | `interrogate -c pyproject.toml python/prin` | exit 0 — **97.6 %** (min 95.0 %) |
| L09 | `bandit -r python/prin DOCS/experiments -c pyproject.toml` | exit 0 — no issues, **24,864 LOC** scanned (non-vacuous) |
| L10 | `pytest tests/test_campaign_quality_gates.py tests/test_ea007_manifest.py -v` | exit 0 — **25 passed** (22 + 3) |
| L11 | defect-catching proof | exit 0 — **63/63** expectations met |
| L12 | `RUSTDOCFLAGS=-D warnings cargo doc -p prin-sim --no-deps --features cpu` | exit 0 |
| L12b | `target/doc/prin_sim/gpu/index.html` exists after L12 | exit 0 (leg is non-vacuous) |
| L12c | `rust.yml` parses as YAML; the `docs` job carries `RUSTDOCFLAGS: -D warnings` and the new step | exit 0 |
| L13a–e | ledger 039 → 040; DV-register gates; global registration; skipif probes; WP-001 baseline | all exit 0 — **142 → 146** rows; **44** DV rows / **198** session entries; **18** EA reports |
| L14 | `git diff --check --cached` | exit 0 |
| L20 | hidden/bidirectional Unicode control scan (U+202A–202E, U+2066–2069, U+200B–200F, U+2060, U+00AD, interior U+FEFF) over every file changed against the PR base | exit 0 — 117 of 118 changed files scanned (the raw historical capture is not UTF-8), 0 hits |
| L15 | `sha256sum -c SHA256SUMS.txt` (from `verification/`) | exit 0 — **93 OK** (against the manifest before the last packaging pass; the final regeneration's re-check is described, unlogged, in §3.3) |
| L19 | Sphinx clean build, `-W --keep-going` (`DOCS/sphinx/changelog.rst` includes `CHANGELOG.md`) | exit 0 — `build succeeded`, 0 warnings |
| L16 | Snyk Code (CLI 1.1306.2, org `symbo-gif`), `--severity-threshold=low`, on the new/modified first-party Python in the commit (two test modules and the proof harness) | exit 0 — **0 issues** |
| L17 | SHA-256 of the five edited first-party files (`AGENTS.md`, `rust.yml`, `DOCS/experiments/README.md`, the two test modules), the proof harness and the uncommitted runner | `pr32-source-hashes.txt` |
| L18 | `gitleaks 8.30.1 git --staged --redact` (content of the commit) | exit 0 — no leaks |

`pr32-source-hashes.txt` (same directory) binds the gate results to the bytes
committed. It supersedes `26h-source-hashes.txt` for the files it lists
(`AGENTS.md` and the gate-test module are in both; `26h` remains the record of
the EA-007 gate-time bytes and is not rewritten).

**Secret scanning of this round's own commit.** L18 scans the staged diff;
the post-commit **full-history** scan of the resulting head is run after the
commits and its result is reported in the hand-off and belongs in the PR
description, **not here** — a document cannot contain the result of a scan of itself, the
rule `PR32-F2` records. This report therefore makes no claim about the head
that contains it.

**Not run, and why.**

- The full Python suite (`pytest tests/ parity/`, ≈ 30 minutes) — run on the
  committed head after the commit; its result is reported with the post-commit
  scan, not pre-claimed here.
- Rust `cargo test`, `clippy`, `llvm-cov` — no Rust source changed in this
  round (`gpu.rs` is untouched; EA-007's runs stand).
- The hosted `rust.yml` step — workflows are paused (#48); never executed.
- Snyk Open Source, `cargo audit`, `pip-audit` — no changed input.
- Linux/macOS — not tested; no claim is made.

## 7. Findings declined or rejected, with rationale

**CodeRabbit pre-merge check — docstring coverage 60 % < 80 %.** Waived. It is
CodeRabbit's generic default, not this project's gate: `interrogate` is
configured `fail-under = 95` and run on `python/prin` only (L08: 97.6 %), and
`pyproject.toml` `[tool.ruff.lint.per-file-ignores]` sets
`"tests/**" = ["S", "D"]` — pydocstyle is deliberately off for tests. The new test modules follow
the existing `tests/**` norm (self-descriptive names; docstrings where the
reason is non-obvious). Four reviewers (Perplexity, Qwen, SWE-2, Kimi) reached
the same conclusion.

**`PR32-F13` — bandit floats in the hosted `test` job (`L-2`).** Real but
declined, carried. The test imports bandit's private `_is_file_included`, and
the `test` job installs `-e ".[dev,onnx]"` with `bandit[toml]>=1.7`
(unpinned); the pinned `bandit==1.9.4` is in `ci/lint-constraints.txt`, used by
the `lint` job and the local `.venv`. The proposed fix — `-c
ci/lint-constraints.txt` on the `test` install — would also apply that file's
`torch==2.13.0` pin against the job's separate unpinned CPU-wheel `torch`
install, a conflict this round cannot validate while the hosted workflows are
paused. The failure mode is a **loud** `ImportError`/collection error on a
bandit upgrade, never a false pass, and the gate that matters under #48 (local
`.venv`, bandit 1.9.4) is pinned. Carried to the checklist for re-enabling the
hosted workflows.

**`L-4` — `13a-cargo-audit.log:5` prints a home-directory path.** Declined.
It is tool output (the `cargo` advisory-database path), not a credential; it is
the only such occurrence in any tracked file; raw logs are the evidence and
their byte-exactness is the bundle's design. Full-history gitleaks found no
secret. Noted in `EVIDENCE/ea007/README.md`. (This round's own log redacts the
user-profile prefix because the runner is new and its output is not a preserved
raw capture.)

**`L-11` — duplicate requirements files.** Declined: legs 22d/22e invoked the
`prin-resolved/` path and their logs are verbatim, so removing either copy
breaks log fidelity for 5,428 bytes. The "frozen" wording is corrected in the
README: the files are version-pinned, not hash-pinned.

**`M-8` sub-proposal — extend `check_global_session_registration.py` to
require a DV-register dated section.** Declined: the dated section is a
recorded convention, not a normative requirement, and the checker's scope is
`SESSION_REGISTER.md` registration. `PR32-F10` fixes the instance.

**Qwen nits not actioned.** `_RUN_LINE` captures only single-line `run:` values
and the parsers scan whole files rather than the `lint` job — a YAML parser
would fix both but `pyyaml` is only in the `devtools` extra, not `dev`, and both
weaknesses fail closed; `gpu.rs` prose duplicated across the two `cfg_attr`
blocks (doc-only, renders correctly; optional); `25-pytest-final.log` and
`13d-snyk-sca.log` readability (raw captures); `parity/` absent from the
`python.yml` ruff legs and three unreferenced `EVIDENCE/*.json` files —
**both pre-existing at the base**, not introduced by this PR (observations
`OBS-1`, `OBS-2`, carried).

**Not remediable here.** Native push protection is disabled (flagged by #48,
unchanged); the Devin flag is unpublished.

## 8. Verdict and required actions

**`PASS-WITH-FINDINGS` → 14 of 15 actionable findings FIXED in this round, one
declined and carried; no D1; no verdict, tolerance or measured value changed.**
The EA-007 verdict `PASS-WITH-REMEDIATION` stands.

**Required maintainer actions (outward-facing, not taken by this round):**

1. **Push** the remediation commit to `audit/ea007-exp002-readiness`; the PR
   description's statements about the final scan and "later commits only package
   the same source" should be updated — the round changes `AGENTS.md`, adds a
   `rust.yml` step, tests and evidence, and `26h` binds only the EA-007
   gate-time bytes.
2. Record the post-commit full-history gitleaks result and the full-suite
   result reported with the commit in the PR description.
3. Native push protection remains the maintainer's call (#48).

**Carried forward (not this round's work):** `PR32-F13` and `OBS-1`/`OBS-2`
to the hosted-workflow re-enable checklist; the unvalidated hosted `rust.yml`
step to the first hosted run after the regime lifts; `DV-033`, `DV-034`, and
the downstream hardware/reference-host gates unchanged.

## 9. Self-audit of the remediation

The remediation was reviewed cold by two external CLI agents in their
**read-only** mode (file reads and search only — no shell, no edits; they could
read diffs and logs but not execute anything) and by the auditor's own second
pass. Every item was re-derived before acting, in the same way as the original
reviews. This section records what those reviews found; it is a record of
rounds, not a claim about the head that contains it (§6).

### 9.1 Round 1 — code and configuration (Antigravity, Gemini 3.1 Pro High)

Scope: `AGENTS.md`, `rust.yml`, `tests/test_campaign_quality_gates.py`,
`tests/test_ea007_manifest.py`. Eleven items: seven were real defects **in the
remediation's own test logic** (each fixed and given a mutation case in L11), one
was a harmless decode choice, one a false positive, one refuted, one already
known and declined.

| # | Reviewer severity | Finding | Verdict | Action |
|---|---|---|---|---|
| 1 | High | The fence regex `\n` fails on a CRLF checkout | **False positive** — `Path.read_text` applies universal newlines; reproduced on a copy of `AGENTS.md` with 86 CRLF line endings: the test passes | none; a CRLF case added to L11 |
| 2 | High | The quote regex can match across two separate quoted arguments (false fail for `cmd 'a' "b" 'c'`) | **Confirmed** | Replaced by left-to-right tokenization; four mutation cases |
| 3 | High | The rustdoc test accepted any `--features` (false pass for `strict-checks`, which does not compile `gpu`) | **Confirmed** | Feature must intersect `cpu`/`cuda`/`wgpu`; mutation cases incl. a list value |
| 4 | Medium | `RUSTDOCFLAGS` was searched file-wide, so a comment satisfied it | **Confirmed** | Job-scoped match; case "job env lost, a comment still mentions it" |
| 5 | Medium | The `AGENTS.md` local leg was not covered by the test | **Confirmed** | Added; case "local leg deleted" |
| 6 | Medium | Basename uniqueness collides on `__init__.py` | **Confirmed in part** — mypy names modules by crawling up `__init__.py` packages, so differently named packages are not duplicates and same-named ones are | Module names computed as mypy does; three cases |
| 7 | Medium | OS metadata (`.DS_Store`, `Thumbs.db`) makes the coverage test fail | **Confirmed** (false fail on a developer machine) | Tolerated explicitly; case added |
| 8 | Low | Basename check is case-sensitive | **Refuted** — executed: mypy on Windows accepts `Quality.py` and `quality.py` in sibling directories | none |
| 9 | Low | Manifest decoded as ASCII | Confirmed (harmless) | UTF-8 |
| 10 | Low | `.resolve()` masks a wrong-letter-case manifest entry on Windows (false pass there, fail on Linux) | **Confirmed** | Exact-case POSIX comparison with no `resolve()`; case added |
| 11 | Nit | `_RUN_LINE` handles single-line `run:` only | Known, declined (§7) | none |

### 9.2 Round 1 — records (Antigravity and Devin SWE-2-High)

Both were given a pre-packaging snapshot. Devin's run ended when it attempted a
shell command that read-only mode rejected, after reporting what it had
verified: the errata quotes verbatim, the post-commit scans, the `GATE-STATUS`
corrections against their logs, the test counts (12 functions → 22 items + 3),
and the workflows — and one **real miss**: `verification/README.md:9` repeated
the over-claim ("verbatim command/host/SHA/UTC/exit code each") that the
`GATE-STATUS.md` correction note disproves. Fixed. Antigravity's eight items:
two were artefacts of the snapshot (the `pr32-review/` evidence directory and
this section are created at packaging); one (`cb40584a` described as an
immediate parent) and two (claims that pointed to §6 for scan results and
hashes §6 does not hold) had already been corrected in the same pass; one
(`DOCS/experiments/README.md` "never edited") was a false positive — the rule is
in the layout notes above the experiment table, where the reviewer did not
look; one (`ER-6` corrects an evidence-index cell, not EA-007 report text) is
kept and now cross-referenced in §4.3; one (the "five files" wording) was
clarified in the §6 table.

### 9.3 Auditor's second pass

Defects found by re-reading the remediation against the repository, each fixed
before review:

- `cb40584a` is the **second parent** of the `fdd28d88` merge (the tip of PR
  #31's branch), not "its immediate parent".
- The README and PSR-040 pointed to this report's §6 for the result of the
  scan of the remediation commit, which §6 deliberately does not contain (a
  document cannot hold the result of a scan of itself).
- `*.log` is gitignored repository-wide: the post-commit gitleaks logs had been
  hashed into the manifest but were **not staged** — green locally, absent from
  every clone. Force-added, and `test_every_hashed_evidence_file_is_tracked_by_git`
  added (L11 mutation case).
- `DOCS/sphinx/changelog.rst` includes `CHANGELOG.md`, so a Sphinx `-W` build is
  a required leg for this round (L19) — the first draft of §6 wrongly listed
  Sphinx as unaffected.
- The new gate logs would have introduced further user-profile paths into the
  bundle (declined for the existing raw log, `L-4`); the runner redacts them.
- Qwen's and SWE-2's blanket "reject" of CodeRabbit's `GATE-STATUS.md` request
  was itself imprecise (§3.1).
- A dangling-reference check over every path cited by the added documentation
  lines found one unresolved reference — the gate log this section cites — which
  exists once the evidence is packaged (§6).

### 9.4 Round 2 — complete tree

**Devin (SWE-2-High), records, on the packaged tree.** It traced every number in
§6 to `pr32-gate-run.log`, the 93-entry manifest and the proof-harness digest,
verified the errata quotes verbatim and the post-commit scans, and found no
dangling reference and no undisposed reviewer item. Eight items (2 Low, 6 Nit),
all accepted and fixed: (1) the `GATE-STATUS.md` census said "77 `.log` files in
the bundle" while the bundle now holds 80 → "the 77 original"; (2) "93 OK
re-verified after packaging" had no committed output → reworded (a log inside the
manifest cannot cover itself; the committed test re-checks it); (3) "`AGENTS.md`
is in both" understated the overlap with `26h` (the gate-test module is too);
(4) the proof claim was wider than its cases (no `PR32-F15` case) → cases added;
(5) the "seven real defects" count in §9.1 → reworded; (6) PSR-040's "19 new gate
tests" was unscoped → scoped to gate time; (7) the CHANGELOG's "five reports"
→ "five citation sites across four records"; (8) path-like code spans wrapped
across a newline in PSR-040 and `tests/README.md` (and in this report), which
renders a stray space inside the path → rewrapped.

**Antigravity (Gemini 3.1 Pro High), tests, after the Round 1 fixes.** It
confirmed the manifest-test fixes (exact-case POSIX paths, UTF-8, `git ls-files
-z`) and the `__init__.py` crawl, and found real defects in the *new* code, all
fixed and each given a mutation case (the proof harness grew from 35 to 54
expectations):

| Finding | Verdict | Action |
|---|---|---|
| `RUSTDOCFLAGS` is satisfied by another step's `env:` while the `prin-sim` step is unflagged | **Confirmed** | Anchored to the job-level `env:` (4-space indent) |
| The flag regex rejects YAML single quotes | **Confirmed** (false fail) | `["']?` |
| `--features` handling reads only the first flag and ignores `--features=`, `-F` | **Confirmed** | `_flag_values` reads all spellings and repeats |
| `.pyi` stubs are ignored by the uniqueness test but not by `mypy` | **Confirmed** | `.py` and `.pyi` covered; a module beside its own stub is one module |
| The package crawl is unbounded | **In part** — mypy itself crawls every enclosing package; only the root-of-filesystem loop guard was missing | Loop guard added |
| A comment such as `# don't use "foo" with 'bar'` desynchronizes the quote scanner; `""` escapes are unhandled | **Confirmed** | Comment lines skipped; `""` escape accepted |
| The unhashed-by-design files are never checked for existence | **Confirmed** | Asserted |
| The `urllib3` regex rejects `>=2.8.0,<3` and environment markers | **Confirmed** (false fail) | Suffixes and markers accepted; every match still checked |
| `_gate_commands` mis-handles `python -m ruff check` | **Declined** — pre-existing DV-040 helper, not changed by this round; the gate lines use direct executables | none |

**Antigravity (Gemini 3.1 Pro High), tests, third look.** It confirmed the
Round 2 fixes were in place and found five more edge cases in the *fix code*,
all confirmed and fixed with mutation cases (harness: 63 expectations):

| Finding | Action |
|---|---|
| The package crawl ignores stub-only packages (`__init__.pyi` without `__init__.py`), so two such packages collapse onto one empty module name | Crawl accepts `__init__.pyi`; cases for a real duplicate and for differently named stub packages |
| Only the first `prin-sim` rustdoc job in `rust.yml` is checked, so a second job without the flag could pass | Every job running the leg is checked; case "a SECOND job" |
| The `AGENTS.md` filter hard-codes the substring `cargo doc -p prin-sim` | Filters on `cargo doc` and `prin-sim`; case with `--package` and reordered options |
| The job-level `env:` regex rejects a valid blank line, comment line or inline comment | Allowed; case |
| The `urllib3` regex rejects `urllib3<3,>=2.8.0`, a two-segment floor and extras | Replaced by a PEP 508 parse (`packaging`) that asks whether the specifier admits 2.8.0 and excludes the vulnerable releases; four cases |

**Devin (SWE-2-High), records, third round.** It traced the numbers again and
found no dangling reference and no undisposed reviewer item, and reported three
items, all fixed: (1) **Medium** — the §6 table and §3.3 quoted L15 as "89 OK"
while the committed log records "93 OK" (the same index-versus-log defect class
as `PR32-F3`, in this very report) → the cell now quotes the committed leg and
discloses that only the *last* regeneration's re-check is unlogged; (2) **Nit** —
"174 `# via`" mislabelled the comment lines (100 `# via` headers, 72
continuations, 2 header lines) in this report and in `GATE-STATUS.md` →
corrected; (3) **Low** — the hidden-character scan was asserted but not logged →
now leg L20.

The pattern across the four rounds is worth stating plainly: every round found
defects in the remediation itself, none of them numerical and none changing a
finding's disposition, and the defect classes (a check that could pass
vacuously; a claim wider than its evidence; a count quoted from memory instead of
from the log) are the same classes the original reviews found in EA-007. The
loop stopped after the fourth round because the last two produced only edge
cases in the fix code and wording corrections, with no change to any finding's
disposition; that is not a claim that no defect remains.
