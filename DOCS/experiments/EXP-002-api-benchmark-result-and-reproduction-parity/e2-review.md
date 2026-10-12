# EXP-002 E2 — Review, decisions and approval

**Session:** `0160` (EXP-002 / C1, E2 — Review and approval).<br>
**Date:** 2026-10-12 UTC.<br>
**Decision authority:** MichaelMaillet, who delegated the E2 decisions to the
AI pair on 2026-10-12, verbatim:

> "I authorize for you to make the E2 decisions that are most in line with the
> established plans, governance, methodologies, established goals, is grounded
> in thruth, and is scientifically rigorous."
>
> — MichaelMaillet, 2026-10-12 UTC

**Reviewer of record:** Claude Opus 5.5 (AI pair). **Independence
disclosure:** this reviewer did not draft the E1 protocol body or the driver
(Devin did), but it did draft the PR #33 pre-E2 amendments of protocol §11.1
and the remediation of the driver. On those parts it is not an independent
reviewer. Two read-only cold reviewers that drafted no part of E1 checked this
record and the decisions it contains. Their reports are in
`EVIDENCE/0160/verification/delegation/` and are adjudicated in §7.<br>
**Protocol:** [`preregistration.md`](preregistration.md), APPROVED by this
review (the header records the delegated approval).<br>
**Inputs:** the [E2 review packet](e2-review-packet.md), the
[PR #33 review audit](../../audits/PR033-multi-review-audit.md) and protocol
§10–§11.

## 1. Independent re-derivation (static)

`EVIDENCE/0160/verification/e2-review/e2_static_verification.py` re-derives the E1
provenance and population claims from committed sources and input inventories
only (`E1-e2-static-verification.log`: **28/28 checks pass**):

- every §1.1 digest and every driver pin;
- reference `__all__` = 172 unique names; PRIN literal `__all__` = 175
  unique; the three additions are disjoint from the reference names;
- the input manifest has 172 records and contains all five conclusion inputs;
- 14 figure stems (figures 2–15), 39 registered files, 11 archived tables,
  14 figure generators in the pinned reference module;
- the protocol and driver digests.

The script imports no generator, renders nothing, evaluates no H2 predicate,
resolves no `prin` export and creates no RUN directory. No H1–H4 outcome
was observed at E2.

## 2. Formal and exhaustive checks of the comparison policy

- **Table canonicalization (Lean 4, `CrlfCanonical.lean`, checked by Lean
  4.34.1, no errors or warnings).** `canon_translate` proves that the
  driver's `replace(b"\r\n", b"\n")` exactly inverts CPython's Windows
  text-mode newline translation. `canon_noCRLF` proves it is the identity
  on strings without CR LF. Together they show that equality of canonical
  tables means "same content up to a CR immediately before an LF", and no
  weaker relation. `crlf_model_crosscheck.py` ties both Lean models to the
  real operations: all 29,524 strings of length ≤ 9 over {CR, LF, `A`}
  agree with `bytes.replace` and with an actual text-mode file write on this
  host (`E2-crlf-crosscheck.log`).
- **PNG colour rules (Z3 5.1.0, `z3_png_colour_rules.py`).** The driver's
  PLTE/tRNS/IHDR rejection expression, transcribed term by term, is
  equivalent to the PNG specification's rules on the whole bounded domain
  (`unsat` for disagreement). Dropping one driver term yields a
  counterexample, so the check is not vacuous (`E3-z3-png.log`).
- **Tested driver.** See §6 for the gate evidence on the approved source.

## 3. Review against Experimentation Standards §2 (E2)

- **Falsifiability.** Each hypothesis has a deterministic three-way rule
  (§4.1): one valid counterexample refutes it, and missing coverage gives
  `INCONCLUSIVE`, never a pass. No statistic, subset or normalization can
  rescue a falsifier, and H4 compares raw bytes.
- **Statistical adequacy.** These are deterministic censuses of fixed
  populations (175 / 172 / 62 / 39). Repeating identical deterministic
  inputs would not create independent samples (campaign plan §9.1).
  Reporting exact counts, with confidence intervals marked not applicable,
  is the correct analysis.
- **Fair baselines.** The reference arm runs the pinned PRINet 3.0
  generators on the same verified 172-input snapshot, with matched
  renderer, fonts and font cache. The archived tables are a second,
  independent baseline. H2's comparators are published claims, except C02,
  whose basis is disclosed as archival self-consistency.
- **Resource sanity.** At most 12 h CPU wall (expected under 1 h); no GPU;
  tracked storage is JSON only, against a 10 MiB cap.
- **Hardware feasibility.** The maintainer's Windows host is the only
  registered host. Linux/macOS stay suspended under amendment #48 and are
  not claimed.

## 4. Decisions

| # | Item (protocol §10 / packet §2) | Decision and reason |
|---|---|---|
| 1 | H1 scope; the 175-name PRIN contract vs the 172-name reference contract | **APPROVED** as a namespace/ownership census only. It makes no behavioural or numerical parity claim (EXP-001 owns numerical parity). |
| 2 | H2: five families / 62 predicates, CPU Goldilocks entries, owner matrix | **APPROVED.** The scope is exactly the campaign §2.1 "conclusion orderings re-derivable without training or GPU". Every excluded class has a named owner (§5.3), so nothing is silently dropped. C02's basis stays disclosed as archival self-consistency. |
| 3 | H3: matched reference arm, raw archived tables, 39 files, renderer and font controls | **APPROVED**, including the font-cache digest (PR33-F29). |
| 4 | H4: separate-process raw identity and canonical projection | **APPROVED**; no normalization applies. |
| 5 | n = 1 deterministic census; unused `iterations=10` envelope fields; `(0,2)` seed metadata | **APPROVED.** `iterations`/`warmup` are envelope metadata and must never be read as a sample size. `replicates=1` and `measurement_kind=deterministic_census` are the binding fields. |
| 6 | Driver guards and reviewed source | **APPROVED.** The reviewed and approved source is the commit that carries this record; E3 must execute a clean HEAD that descends from it, with the protocol byte-identical (enforced by admission and closure). |
| 7 | The PR #33 comparison amendments (table CRLF→LF; removal of the four registered PDF Info entries) | **APPROVED.** Both are symmetric, metadata-only and outcome-independent. The table rule is proven in §2 to compare content exactly up to a CR before an LF. The Info rule removes only keys that both writers use for provenance. Content streams, unregistered Info entries and raw H4 bytes stay significant. |
| 8 | Raw publication bytes depend on reconstruction | **DECIDED: retain.** Generated publication roots are kept unmodified, outside git, until the E5 report is accepted. The E3 log records a listing digest per root. E5 verifies the retained bytes against the manifested raw digests before reconstructing (protocol §11.3 item 2). This makes byte verification independent of renderer drift without breaking the tracked-storage cap. |
| 9 | Outcome exposure before E2 (PR33-F38) | **DECIDED.** H1 and H4: no outcome was published, so unaffected. **H2 remains confirmatory.** Its predictions and rules were committed at `7859030`, before the exposure. Its operands are frozen archival data. No post-exposure edit changed a predicate, operand, threshold, expected value or population: the C03 label edit matches the key the driver has read since `7859030`. **H3 remains confirmatory under the approved policy, with a registered sensitivity analysis.** The driver records each file's digest under the pre-exposure (`6314532`) policy, and E4/E5 must report H3 under both policies. If the verdicts differ, the report must say that H3 depends on a post-exposure amendment (protocol §11.3 item 1). E3/E4 use only the registered runs; the reviewers' published outcomes are never inputs. |
| 10 | Hosted-CI accounting (packet §4 item 4) | **DECIDED.** Campaign §8 charges "campaign-specific workflow dispatches" for experiment legs on the hosted hosts. EXP-002's only such leg, the cross-OS `reproduce.py` run, stays suspended. Amendment #50 PR checks and the forced nightly validate the source; they are not charged, and their run IDs and durations are logged (nightly `38184198596`: `bench-regression` 87 min, `full-suite` 14 min). |
| 11 | Checksum exception / E1 closure (packet §4 item 1) | Approved and applied on 2026-10-11 (PR33-F34). The E1 exit was accepted by the maintainer on 2026-10-12 (§5). |

## 5. Maintainer acceptances recorded at this session

- **E1 exit accepted.** Verbatim directive, 2026-10-12: "Accept the E1 exit."
  Session 0159 is `COMPLETE`.
- **Amendment #51 ratified.** Verbatim directive, 2026-10-12: "Ratify figure
  count if that reflects the truth." Truth re-derived in §1: the pinned
  reference defines 14 figure generators and archives figures 2–15 in two
  formats, and no figure 1 exists. Ratified in the Plan row.

## 6. Approved-source gate

The approved source's local gate, its hosted results under amendment #50 and
the forced nightly are recorded in `EVIDENCE/0160/` and in the E3 entry
checklist below. No E2 claim depends on a hosted result. The Windows
local gate is authoritative.

## 7. Cold review of this record

Antigravity (`gemini-3.8-flash-high`) and Devin (`swe-2-high`) ran read-only
and reviewed this record, the protocol diff and the code diff. Neither drafted
any part of E1. Their task files and verbatim reports are in
`EVIDENCE/0160/verification/delegation/`. The reviewer of record re-derived
every point before acting on it:

| Source / item | Verdict | Action |
|---|---|---|
| Devin F1: a relative `--basetemp` was resolved differently from pytest | Partly right. pytest uses `os.path.abspath` (the invocation directory), not the rootpath Devin assumed, but the hook's `resolve()` could still diverge on a symlink | Fixed: the hook now uses pytest's exact `abspath` and leaves symlinks, files and missing paths to pytest (test added) |
| Devin F2: non-`PermissionError` races could crash the session at startup; xdist workers race | Confirmed | Fixed: a vanished directory counts as done, attempts are bounded in every path, and xdist workers skip the hook (tests added) |
| Devin F3: no sensitivity size, so §8.1's "sizes" could not be met from manifested records | Confirmed | Fixed: `sensitivity_bytes` is recorded and schema-checked at closure (tests added) |
| Devin F4: the sensitivity policy selected Info by `(number, generation)`, but `6314532` selected it by number | Confirmed; it matters only on crafted files | Fixed for fidelity, documented in protocol §11.3 (test added) |
| Devin F5 / Antigravity F2–F3: evidence paths and packaging | Paths confirmed wrong; packaging was in progress | Paths fixed; `gate/` and `delegation/` are packaged before the commit |
| Antigravity F1: nightly durations had no evidence file | Confirmed | `ci-fixes/H1-forced-nightly-38184198596.json` added |
| Antigravity F4–F7, F9: stale DRAFT/PLANNED/paused text in the campaign README, review packet, tests README, E1 handoff and protocol §8 | Confirmed | Fixed with dated or superseding notes |
| Antigravity F8: E1 handoff body still lists publication as pending | Already superseded by that file's dated-corrections section, which states it overrides conflicting text | No change |

Both reviewers found no E3-blocking defect and no change to any hypothesis,
prediction, population, threshold, sample, seed, statistic, abort criterion
or cap. Both found decision 9's dual-policy reporting binding as registered.

**Round 2 (verification of the fixes).** Antigravity reported every round-1
item fixed or correctly declined and found no new defect. Devin's first two
round-2 attempts stopped early: each tried a tool that needs confirmation. The
second attempt's partial output is kept; the first was overwritten by the
relaunch. Its third attempt confirmed every fix and that
the header still admits, and raised two new low items plus residuals:

| Item | Verdict | Action |
|---|---|---|
| N1: `tests/README.md` cited `EVIDENCE/0160/test-reliability/` | Confirmed | Path fixed |
| N2: read-only retry did not match pytest on POSIX (no search bit, no parent chmod) | Confirmed; latent on the Windows host | Fixed: owner read/write (+search for directories) on the entry and its parent, as pytest does (test added) |
| Residual: other `OSError`s aborted the session; a root/ancestor `--basetemp` raised `ValueError` | Confirmed | Fixed: other `OSError`s are left to pytest's own deletion; `ValueError` becomes a `UsageError` (test added) |

The local gate also caught two defects that neither reviewer flagged: a
trailing-space line in the 0161 brief (`git diff --check`) and a CHANGELOG
link Sphinx cannot resolve (`-W`). Both are fixed, and their failed captures
are kept (`gate/G10fa`, `gate/G11a`).

A later gate run's fast suite then stopped with a Windows access violation
(exit `3221225477`) inside `os.walk`, called by the WP-001 repository-inventory
test (`gate/G12a`). The full suite in the same run passed. Session 0159's leg
09 crashed the same way in the same test. Standalone reruns, with and without
coverage, did not reproduce it, so the native root cause is **not proven**.
The walk covered about 110,800 files (4.2 GB), mostly git-ignored scratch such
as tool worktrees and pytest base directories. The inventory now lists only
git-visible files inside a work tree (about 4,500 files, 58 MB, about 2.5 s),
and it still walks the tree outside git. Regression tests cover both paths.
This narrows the code path that crashed. It does not prove the crash is gone.
The final gate below is the evidence for this candidate.

**Round 3 (the inventory change).** Both reviewers again ran read-only
(`delegation/*-round3-*`). Antigravity found no defect. Devin raised two
Medium and five Low items:

| Item | Verdict | Action |
|---|---|---|
| M1: `--exclude-standard` reads the host's `.git/info/exclude` and `core.excludesFile`, so counts can differ between hosts | True, but the walk it replaces counted every host-local file, so it varied more. Untracked content was never host-independent | Documented in the docstring. Standard rules kept so the inventory agrees with the clean-checkout test in E3 admission |
| M2: the git path drops symlinked files and does not descend into untracked nested repositories; the walk does | Symlinks: confirmed (the git path filtered them). Nested repositories: confirmed; none exist here | Symlink filter removed, so symlinked files count on both paths. The nested-repository difference is documented |
| L3: a `ValueError` (NUL, absolute or `..` names) escaped the fall-back | Confirmed | `ValueError` caught. Absolute, `..` and drive-qualified names now make the tool walk instead (tests added) |
| L4: `rev-parse` used the locale codec; `ls-files` used UTF-8 | Confirmed | Both decode UTF-8 |
| L5: `stdin` was inherited | Confirmed | `stdin=DEVNULL` (asserted in a test) |
| L6: the scratch-repository tests read the host's git configuration | Confirmed | Test git runs with `GIT_CONFIG_NOSYSTEM=1` and `GIT_CONFIG_GLOBAL` set to the null device |
| L7: exclusion filters untested on the git path; `monkeypatch` patches module globals | First part confirmed; second is standard `monkeypatch` use that is undone at teardown, in a single-threaded test | Git-path exclusion test added; second part declined |
| Devin's note: the docstring cited 0159 leg 09c as an ignored-scratch determinism failure | Confirmed wrong. The 09c operator note attributes that failure to files written during the scan, not to ignored scratch | Citation removed |

**Void gate attempt (run 4).** The first gate after round 3 is void, and
both of its failures are kept. Its focused leg failed because the round-3
review files had not yet been packaged (`gate/G09a`). Stopping the background
task did not stop the gate script, and the remaining legs ran while the
manifest was being regenerated in the repository. That broke the rule of no
repository writes during a run. The fast suite in that run (`gate/G12b`) then
failed two timing-sensitive tests. The first was the DV-032 throughput ratio
(5.45 against the `< 1.30` limit). The second was a Hypothesis per-example
deadline (239 ms against 200 ms). Both tests passed in every earlier fast
and full run this session. Their cause is not established: the host was not
idle and the run was already void. Neither assertion was changed. The gate
was rerun from the start with no other activity on the host.

## 8. E3 go/no-go checklist (session 0161)

1. Clean checkout at the E3 source R, a descendant of the approval commit:
   no tracked change, no untracked non-ignored file outside
   `benchmarks/results/EXP-002/` or `log.md`, and no untracked top-level
   `*.py`/`*.pth`. The driver's admission enforces all of this and fails
   closed.
2. Protocol status `APPROVED` with the dated approval line, byte-identical
   to the committed blob.
3. The required hosted workflows for R are green (amendment #50 window),
   and the latest forced nightly on that source is green or dispositioned.
4. The five legs run in the registered order, each in its own interpreter
   process, using the §5.5 command with the real UTC/R values. Keep each
   `publication/` root and log its listing digest:

   ```powershell
   .venv\Scripts\python -c "import hashlib,pathlib,sys; r=pathlib.Path(sys.argv[1]); print(hashlib.sha256(''.join(f'{p.relative_to(r).as_posix()} {p.stat().st_size} {hashlib.sha256(p.read_bytes()).hexdigest()}\n' for p in sorted(r.rglob('*')) if p.is_file()).encode()).hexdigest())" DOCS/test_and_benchmark_results/EXP-002/<run-id>/publication
   ```

5. Supervise the ≤ 12 h aggregate CPU wall across all attempts. A nonzero
   closure exit makes a record inadmissible. Never delete an aborted run.

**EXP-002 is APPROVED. Sessions 0159 and 0160 executed no experiment leg. E3
is authorized once the entry checklist holds.**
