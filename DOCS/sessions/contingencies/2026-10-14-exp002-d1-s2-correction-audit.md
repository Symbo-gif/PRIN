# EXP-002 D1 S2 — Correction audit

**Status:** COMPLETE (S2, 2026-10-15 UTC; verdict **PASS-WITH-FINDINGS**, one D2 + one D3 + six D4, no D1, no systemic drift — recorded in the [correction audit](../../audits/2026-10-15-exp002-d1-correction-audit.md) §S2.0–§S2.13); committed locally only, **not pushed** (a delegated decision, §S2.13 call 2); **S3 is next**
**Triggering deviation:** `EXP-002 H3 REFUTED` (campaign plan §10.4 D1; pre-registration §4.3)
**Blocked numbered session:** `0164` (EXP-003 E1), and every later campaign session (`0165`–`0194`)
**Opened by:** session `0163` (EXP-002 E5), 2026-10-14 UTC
**Predecessor:** [S1 — correction implementation](2026-10-14-exp002-d1-s1-correction-implementation.md)
**Successor:** [S3 — correction remediation](2026-10-14-exp002-d1-s3-correction-remediation.md)
**Governing record:** [EXP-002 E5 report](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md) §8

## Expectation

Read-only audit of the correction against A1–A10, the triggering experiment evidence, and the violated requirement; issue findings and verdict.

## Exit evidence

Record commands, artefacts, approvals, commits, and handoff in the correction
WP's audit and Project State Report. The blocked session remains blocked until
all four conditional sessions close.

## Audit scope specific to this correction

Beyond the standard checklist A1–A10, the audit independently verifies:

1. **The reproduction came first.** The failing regression/parity tests S1 cites existed and failed on the pre-fix tree; the auditor re-runs them on the pre-fix state rather than accepting the claim on authority.
2. **The root cause is established, not asserted.** Every one of the 9 differing figure stems (`18` files: `.pdf` and `.png` of figures 5, 7, 8, 9, 10, 11, 12, 14, 15) is accounted for. If S1 concluded that any part of the PRINet 3.0 reference generator is the defective side (campaign plan §10.4 item 3), the audit verifies the EMA-style mathematical claim and its Z3/SymPy verification directly; an inspection argument is not sufficient.
3. **No regression on the already-matching outputs.** All `11/11` `.tex` tables and the `5/14` already-matching figures (`fig2`, `fig3`, `fig4`, `fig6`, `fig13`), as well as PRIN-versus-PRIN raw-byte determinism (H4), remain intact.
4. **EXP-002's record is untouched.** No file under `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/` (except any dated erratum appended at S4) or `benchmarks/results/EXP-002/RUN-*` was modified; `verify_manifest` passes on all five run directories, and `analysis/exp002_e4_analysis.py` (`3731fc2`) still reproduces the seven E4 outputs and `report-manifest.json` (`6b15dcc1…68781`) byte-for-byte.
5. **Coding Standards §6 evidence is real.** Snyk Code (and Snyk Open Source + ecosystem-native audits if any dependency changed) was run on the exact changed files, or any unavailable scan is reported as blocked — never claimed.

## Verdict rule

`PASS` (no findings above D4), `PASS-WITH-FINDINGS` (none D1), or `FAIL` (any D1, or systemic drift). A `FAIL` sends every finding to S3; no fix is committed during this read-only audit session.

## Completion and handoff (2026-10-15 UTC)

**Audited:** `ab9e4225..8fd0ecc9` on `hotfix/exp002-d1-figure-parity` (draft
PR #34), local `HEAD` confirmed equal to `origin` and the tree clean after
`git fetch --all --prune`.

**Verdict: `PASS-WITH-FINDINGS`** — one D2, one D3, six D4, **no D1**, no
systemic drift. All five audit-scope items are **VERIFIED** by independent
re-execution, not by accepting S1's record:

1. **Reproduction first** — with `figure_generation.py` restored from
   `d90eeabb` (digest `e0f59253…d533`, equal to S1's prefix
   `port_module_sha256`), the gate failed on **exactly the 18 E3 files**
   (18 failed / 75 passed) and all **9** fast-gate argument tests failed;
   after restoring, **102 passed**. The gate file is byte-identical between
   `d90eeab` and `HEAD`, so restoring the one module reproduces the pre-fix
   state exactly.
2. **Root cause established** — the decomposition re-run reproduces the
   committed postfix artefact field-for-field (only `generated_utc`/`git_head`
   differ); a new static AST instrument validates **34/34** specifications
   against the frozen reference source with **0 failures** and confirms all 34
   restored with no surviving mathtext rewrite; a new artist-level instrument
   reports **14/14 stems EQUAL** across the full matplotlib object model, so
   **no plotted value differs**. §10.4 item 3 is correctly not invoked, and no
   escalation condition was met.
3. **No regression** — 11/11 tables, the 5 already-matching figures, the 21
   raw-identical outputs and H4 (`two_process_raw_identical: true`) all intact;
   the fast suite completed a **clean single pass** (4038 passed, 0 failed),
   which is the result S1 handed to S2.
4. **Record untouched** — empty diffs over the EXP-002 record,
   `benchmarks/results/EXP-002/`, `.github/` and every dependency manifest;
   `verify_manifest` **PASS on all five** `RUN-*` directories plus the
   172-input manifest; and, in a clean detached worktree **outside** the
   repository, the frozen E4 module reproduced all seven outputs and
   `report-manifest.json` `6b15dcc1…68781` **byte-for-byte** — the check S1 did
   not re-run.
5. **§6 evidence real** — Snyk Code **0 findings** in all four changed files
   and 0 repo-wide at `medium`, via the MCP integration §6.4 permits. The
   **CLI leg is recorded BLOCKED** (expired credentials, `401 SNYK-0005`, no
   SARIF), never as passed.

**Findings for S3, in severity order:**

| ID | Sev | One line |
|---|---|---|
| `EXP002D1-S2-F2` | **D2** | The required full suite is red (`exit 1`): `test_notebook_executes_end_to_end[02_clevr_n_binding.ipynb]` `CellTimeoutError` at the 900 s per-cell limit — the same node failed in S1's run, and S2's far less contended run (2:03:35 vs 4:11:33, with S1's two `WinError 5` failures passing here) no longer supports a purely load-induced attribution. S3 must re-size the bound from cited in-suite evidence, document the leg as its own workload, or open a dated DV row on the DV-046 precedent. |
| `EXP002D1-S2-F1` | **D3** | The two registered H3 policies now disagree about the verdict: approved §5.4 **39/39 equal** (`CONFIRMED`) vs §11.3 sensitivity **14/39 equal** (`REFUTED`). All 25 residuals are writer/host properties — 14 PDF Info key sets, 11 `.tex` line terminators — with **0 unclassified**. Not an S1 defect; S3 records the assignment and **S4 carries it into the `EXP-002-r1` authorization** so its E1/E2 registers both policies deliberately. `EXP-002`'s frozen pre-registration is not edited. |
| `EXP002D1-S2-F3` | D4 | Local `snyk` CLI credentials expired; S4 must use the MCP route or have the maintainer re-authenticate. |
| `EXP002D1-S2-F4` | D4 | `EVIDENCE/exp002-d1-s1/fast-tests-against-prefix-module.txt` is committed but absent from that README's index (10 of 11). No `SHA256SUMS.txt` there, so an added row breaks no hash freeze; evidence bytes untouched. |
| `EXP002D1-S2-F5` | D4 | The fast-gate docstring says "each byte-material argument" but the tests pin **all 34**; comment-only correction, no assertion changes. |
| `EXP002D1-S2-F6` | D4 | fig13's per-series `label=f"Obj {lbl}"` is still omitted — byte-immaterial, artist-level EQUAL, but inconsistent with an argument-faithful port. Restore or record why not. |
| `EXP002D1-S2-F7` | D4 | The touched module docstring's absolute "no scientific quantity is recomputed" sits against its stored-fit `np.exp` evaluation (mirroring the reference, required for byte parity). Qualify the wording. |
| `EXP002D1-S2-F8` | D4 | Two residual Snyk Code **LOW** `python/PT` (CWE-23) findings in S2's own instruments, surfaced by §6.4's rescan of the new first-party code. **Remediated twice, not suppressed** — a `..` / no-follow-symlink / regular-file / resolve-and-confine guard on the `PR23-F1` pattern, proven non-vacuous by negative tests including a real symlink — but Snyk's model does not recognise the sanitizer, so both persist. The applicable §6.2 gate is "0 medium+" and repo-wide at `medium` is **0**, so the gate is met. **ACCEPTED WITH ASSESSMENT**, flagged for maintainer ratification; re-check at S3 and S4. Full record: [`snyk-low-findings-threat-assessment.md`](../../../EVIDENCE/exp002-d1-s2/snyk-low-findings-threat-assessment.md). |

**Local gate reproduced** on `8fd0ecc9` under amendment #48, sequentially, from
Git Bash: `ruff check`/`format --check` (every root including both EVIDENCE
dirs), `mypy --strict` ×3, `interrogate` **97.6 %**, `bandit` ×2, the four
governance checkers, `cargo fmt`/`clippy -D warnings`/`test --workspace`,
Sphinx `-W --keep-going` from a deleted `_build`, `gitleaks` **738 commits, no
leaks** plus `--staged`, fast suite **exit 0**, full suite **exit 1**
(`EXP002D1-S2-F2`), changed-line coverage **11/11 = 100 %** (whole-file
99.41 %). Two legs initially failed and were corrected and re-run with both
attempts recorded; the `cargo` failure was the documented `os error 32`
contention class and passed on re-run. **No CI is claimed**: all seven check
workflows verified `disabled_manually` and the amendment #50 window is closed.
Supervised per Testing Standards §7 — one faulthandler dump was investigated
with two timestamped observations and the node's committed expected duration
(`1086.16 s`) rather than treated as a hang; nothing was killed, re-run,
deselected or weakened.

**Evidence:** [`EVIDENCE/exp002-d1-s2/`](../../../EVIDENCE/exp002-d1-s2/README.md)
— six committed instruments and their verbatim outputs. S2 was read-only: no
source, test, S1-evidence or S1-record change was committed.

**Handoff.** S3
([brief](2026-10-14-exp002-d1-s3-correction-remediation.md)) resolves all eight
findings in D1→D4 order (so `EXP002D1-S2-F2` first), each commit naming its
finding ID, then obtains a `CLEAN` delta re-audit that re-verifies the pre-fix
failing reproduction, the post-fix passing parity tests and the immutability of
the EXP-002 record. S3 is **mandatory** even though no D1 was found.

**Not authorized by S2:** merging PR #34, marking it ready for review,
`EXP-002-r1`, or releasing session `0164`. Session `0164` stays `BLOCKED`.

**Nothing was pushed — a delegated decision, not an omission.** The maintainer
answered S2's escalation by delegating the call ("i authorize you to make the
call that follows etablished methodologies and governance rigorously"). Applied
to the push question, governance points one way: Development Workflow §3's S2
rules say "Commit the Audit Report locally; do **not** push", and amendment #28
says only the **S4** commit that closes a cycle is pushed, carrying the whole
S1–S4 range. The §7 hotfix exception *permits* an early push but does not
require one, and S1's push was a specific pre-authorization taken for a specific
evidentiary purpose — recording the red → green transition on the remote — which
does not recur for a documentation commit. Deferring also avoids publishing an
audit whose eight findings S3 has not yet dispositioned, and avoids a push that
would run no hosted check (all seven workflows are `disabled_manually`). S4
remains the cycle's push point and will re-run the full-history secret scan,
since a scan result is about the commit it names. Full reasoning: audit §S2.13.
