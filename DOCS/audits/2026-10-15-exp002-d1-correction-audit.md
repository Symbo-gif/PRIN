# EXP-002 D1 correction audit

**Scope:** the EXP-002 D1 correction cycle (campaign plan §10.4). H3
publication fidelity is `REFUTED`: 18 of 39 registered `generated_files`
differ between PRIN and the frozen PRINet 3.0 reference generator under the
approved §5.4 policy, namely the `.pdf` and `.png` of figures 5, 7, 8, 9, 10,
11, 12, 14 and 15.\
**Opened by:** session `0163` (EXP-002 E5), 2026-10-14 UTC.\
**Blocked:** session `0164` (EXP-003 E1) and every later campaign session
(`0165`–`0194`).\
**Branch / PR:** `hotfix/exp002-d1-figure-parity` from `origin/main` @
`fd8854ed87a21e01f16e2f7128b431e74085a26e` (the PR #33 merge); draft
**PR #34**.\
**Stage status:** S1 **complete** (2026-10-15 UTC); S2, S3, S4 pending.

This is the correction work package's audit of record. S1 records its
implementation here: approvals, the reproduction, the root cause, commits, the
red → green transition, commands, and handoff. S2 appends the audit proper
(A1–A10, findings, verdict) below this record, S3 appends its closure table,
and S4 appends the closure. Nothing in this S1 record is an audit verdict, a
merge authorization, an `EXP-002-r1` authorization, or a release of session
`0164`.

---

## S1 — implementation record (2026-10-15 UTC)

**Session brief:** [`2026-10-14-exp002-d1-s1-correction-implementation.md`](../sessions/contingencies/2026-10-14-exp002-d1-s1-correction-implementation.md).\
**AI pair:** Claude Opus 5.5. The maintainer's decisions are recorded below.

### S1.1 Approvals

- **Scope approved as written.** MichaelMaillet, 2026-10-15 UTC, verbatim
  "approve correction cycle scope"
  ([`maintainer-decisions-2026-10-15.md`](../../EVIDENCE/0163/verification/acceptance/maintainer-decisions-2026-10-15.md)
  item 2). No refinements were stated.
- **Retained E3 roots kept until S1 completes** (same record, item 4). S1 read
  them and did not modify or delete them.
- **Push and draft PR pre-authorized.** MichaelMaillet, 2026-10-15 UTC, in the
  instruction that started this session; this mirrors the EXP-001 S1 brief's
  decision 3. It is recorded in the brief's "Approved scope and decisions"
  (`ab9e422`). The failing-test commit was pushed before the fix. The seven
  hosted check workflows are disabled (`gh workflow list --all`: all seven
  `disabled_manually`), so no hosted check ran. The Windows local gate is
  authoritative under Plan amendment #48. Merging stays with the maintainer.

### S1.2 Reproduction (failing test first)

`parity/test_parity_publication.py` (`d90eeab`) is the gate that EXP-002
showed was missing. No earlier test compared PRIN's figures with the
reference: `tests/test_publication_generation.py` checks table bytes against
the archived tables and checks figure completeness, not figure equality. The
gate runs in one process:

- It renders the reference arm: `prinet.utils.figure_generation` and
  `table_generation`, with origin and SHA-256 asserted against the E3
  driver's `REFERENCE_PINS`.
- It renders the PRIN arm with the registered call,
  `tools.reproduce.run_reproduction(..., verify=True)`.
- It compares all 39 registered files under the registered H3 rule,
  `benchmarks.campaign.exp002_driver.normalized_bytes`, which is the function
  E4 applied. No file is skipped or toleranced.

It also ties itself to E3:

- the committed E3 records differ on exactly the D1 set;
- the in-process reference arm equals E3's reference arm on all 39 normalized
  digests;
- PRIN's tables equal the archived tables;
- a second PRIN render repeats every raw byte.

At `d90eeab` it fails on **exactly the 18 E3 files** (18 failed, 75 passed;
[`gate-red-d90eeab.txt`](../../EVIDENCE/exp002-d1-s1/gate-red-d90eeab.txt)).
The probe that preceded it showed the pattern is independent of render order.

### S1.3 Root cause

**Method: controlled substitution on the frozen reference**
([`EVIDENCE/exp002-d1-s1/`](../../EVIDENCE/exp002-d1-s1/README.md),
`dd05afa`). For each of the 14 stems the generator renders four variants:

- **R**, the reference;
- **P**, the port;
- **A**, the reference with all registered divergences applied;
- **R_d**, the reference with exactly one divergence `d` applied.

A divergence is applied without editing or re-executing reference source. The
named `matplotlib.axes.Axes` method is wrapped, and only calls made directly
from `prinet.utils.figure_generation` are transformed. Each transform asserts
that its target argument is present, and each divergence must fire at least
once.

**Results (pre-fix, `root-cause-decomposition-prefix.json`):**

| Claim | Result |
|---|---|
| Completeness: **A == P** (normalized) for each D1 stem, both formats | **9/9 stems, 18/18 files.** The 34 registered divergences explain every differing byte. No plotted value, data series, limit, title or annotation number differs. |
| Unexplained stems | **0** |
| Byte-material divergences (`R_d != R`) | 26 of 34. The 8 immaterial ones equal the active rcParam or have no visible effect: D5.1, D5.3, D9.2, D11.4, D12.5, D12.7, D15.4, D15.7. |
| In-process reference arm vs E3 reference arm (normalized) | 39/39 equal |
| In-process PRIN tree vs E3 PRIN arm (raw) | 39/39 equal |
| Retained E3 roots vs manifested `reproduction.json` (reference, PRIN, seed-replicate 0) | 39/39 raw and 39/39 normalized for each leg; each `reproduction.json` matches its `manifest.json` |
| Matching figures (fig2/3/4/6/13) | No registered divergence. Their residual source differences (call order, `ax.set(...)` grouping, fig13's unused `label=`) change no byte. |

**Per-stem attribution** (full table in the
[evidence README](../../EVIDENCE/exp002-d1-s1/README.md)):

- **fig5:** `markersize=4` dropped on the errorbar and on the SA line.
- **fig7:** `va="bottom"` dropped on the accuracy labels.
- **fig8:** `zorder=5` dropped on the scatter, so the markers fell under the
  grid.
- **fig9:** `linewidth=1.2` dropped on four curves; `va="bottom"` dropped on
  the IP labels.
- **fig10:** the outcome note's `bbox` dropped.
- **fig11:** bar `edgecolor`/`linewidth` dropped; Unicode `×10³` and `×`
  re-encoded as mathtext; `va="bottom"` dropped.
- **fig12:** bar `linewidth` dropped; δ/θ/γ band labels with en dashes
  re-encoded as mathtext; `axhline` `linewidth`/`alpha` dropped; twin-line
  `linewidth` dropped; twin `tick_params(labelcolor=…)` omitted; `×` labels
  re-encoded as mathtext; `va="bottom"` dropped.
- **fig14:** `alpha=0.85` dropped.
- **fig15:** marker sizes 3/4 dropped; the fit line's `alpha`/`linewidth`
  dropped; the `×` x-label re-encoded as mathtext.

**Side.** Every divergence is a drawing argument that the WP-034 S1 port
(`d88a331`, `python/prin/reporting/figure_generation.py`) changed relative to
the frozen reference function it ports. None touches a computed quantity: the
completeness result shows that the plotted data are identical. The defective
side is **PRIN**, as an unfaithful port. H3's registered independent basis is
"faithful generator ports" (pre-registration §3). **Campaign plan §10.4
item 3 is not invoked.** No claim is made that any part of the PRINet 3.0
reference is defective, so no EMA-style mathematical audit is required.

**Why it was not caught earlier.**

1. No test compared figure bytes across the two generators. The WP-034
   acceptance tests check figure completeness and the normalizer, and
   compare only the tables with the reference bytes.
2. The Unicode-to-mathtext re-encodings coincide with `ruff`'s `RUF001`
   ambiguous-character rule (`×` reads as `x`, `γ` as `y`), which
   `pyproject.toml` selects repository-wide. The fix spells these characters
   with `\N{...}` escapes. Escapes satisfy `RUF001` and yield the reference's
   runtime strings.
3. Half the dropped keyword arguments read as plausible condensation. Two
   examples: `markersize=5` equals the rcParam, and `framealpha=0.8` equals
   `legend.framealpha`. The other half are not no-ops, and no gate could tell
   the two kinds apart.

### S1.4 Fix

`10d84f2` (`fix(reporting)`). Each of the nine generators now passes the
reference's exact drawing arguments and label strings, including the 8
immaterial ones, so the port is argument-faithful and stays faithful if an
rcParam default ever changes. No plotted value, data series, other generator,
table, normalizer, or public symbol changes. No dependency changes.

Tests in tandem:

- **`parity/test_parity_publication.py`** (red at `d90eeab`) is now green: 93
  passed.
- **`tests/test_publication_figure_arguments.py`** adds 9 fast-gate tests.
  The `tests/ -m "not slow and not gpu"` gate does not run `parity/`, so these
  tests pin each restored argument on the live `Figure` objects. Each
  assertion names its divergence ID. Run against the pre-fix module
  (`git show d90eeab:python/prin/reporting/figure_generation.py`, restored
  afterwards), **all 9 fail**; on the fixed tree all 9 pass.

### S1.5 Commits

| Commit | Purpose |
|---|---|
| `ab9e422` | docs: push and draft-PR pre-authorization recorded in the S1 brief; status IN PROGRESS |
| `d90eeab` | **test (failing first):** `parity/test_parity_publication.py`. 18 failed, exactly the E3 population. **Pushed before the fix.** |
| `dd05afa` | test: root-cause decomposition generator, prefix artefact, red-gate and gitleaks records |
| `10d84f2` | **fix:** reference drawing arguments restored in fig5/7/8/9/10/11/12/14/15, plus the 9 fast-gate argument tests |
| `9371596` | test: in a postfix run, the decomposition compares A against the committed prefix artefact (prefix behaviour unchanged) |
| `10d196c` | test: post-fix decomposition artefact and green-gate record |
| S1 documentation commit (follows `10d196c`) | docs: this record, the evidence README, the Snyk Code record, the S1 brief completion, CHANGELOG, `SESSION_REGISTER.md`, the contingencies, phase-7, audits and EVIDENCE indexes |
| local-gate record commit (last S1 commit) | test: `EVIDENCE/exp002-d1-s1/local-gate.txt` and the §S1.7 summary, for the gate run on the documentation commit. It adds evidence text only. |

### S1.6 Red → green transition (S1 acceptance)

| Tree | `parity/test_parity_publication.py` | `tests/test_publication_figure_arguments.py` | Decomposition |
|---|---|---|---|
| `d90eeab` (pre-fix; pushed) | **18 failed**, 75 passed: exactly the E3 18-file set | 9 failed (pre-fix module restored into the fixed tree) | prefix: 18 differing files; A == P on 9/9 stems; 0 unexplained |
| `9371596` (post-fix) | **93 passed** | **9 passed** | postfix: 0 differing files; A still equals the prefix port digests on 9/9 stems; 21 previously matching files raw-identical to E3; exactly the 18 D1 files changed; two-process raw identity holds (H4) |

The transition is attributable by construction. The fix changes only the 34
registered call arguments, and the postfix artefact shows that the 21
previously matching outputs (11 tables, 10 figure files) are raw-byte
unchanged.

### S1.7 Local verification (Windows host, project venv)

Recorded verbatim in
[`EVIDENCE/exp002-d1-s1/local-gate.txt`](../../EVIDENCE/exp002-d1-s1/local-gate.txt).
Pending: the gate block is appended when the runs complete.

### S1.8 EXP-002 record immutability

`git diff --stat fd8854ed..HEAD` over
`DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/` and
`benchmarks/results/EXP-002/` is empty: no file in the immutable record or any
raw run directory changed. The retained `DOCS/test_and_benchmark_results/EXP-002/RUN-*`
roots were only read. No EXP-002 leg, `EXP-002-r1` run, or other campaign
execution took place. The out-of-scope items `DV-045`, `DV-046` and `DV-047`
were not touched, and neither were `.github/workflows/` or any dependency
manifest.

### S1.9 Parity-evidence disposition (Development Workflow §3, R15)

The correction adds no numerical primitive. The changed code ports
`prinet.utils.figure_generation`, which exists in the archived reference;
`import prinet.utils.figure_generation` resolves to
`DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/utils/figure_generation.py`
with SHA-256 `575eca5a…1520` (= `REFERENCE_PINS`). Parity evidence against it
is included in this S1: the byte-level gate and the decomposition.

### S1.10 Observations outside the approved scope (candidates, not done)

1. **H3 under the §11.3 sensitivity policy, post-fix: 14/39 equal.** All 14
   PNGs are equal. The 11 tables differ only in line terminators: the
   reference opens tables in text mode, so Windows writes CRLF, while PRIN
   writes LF. The 14 PDFs differ only in the Info key set: PRIN writes four
   fixed entries, and the reference writes three with a wall-clock
   `CreationDate`. Both are writer and host properties that the approved §5.4
   policy registers as non-scientific, and E2 decision 9 already disclosed
   them. PRIN's fixed metadata is what makes H4 hold, so S1 does not change
   it. `EXP-002-r1`'s E1/E2 should decide how the two policies are registered
   for the re-run. If both are carried unchanged, the policies would disagree,
   and §11.3 requires that disagreement to be reported.
2. **Parity Report.** The 2026-10-14 erratum admonition in
   `DOCS/sphinx/parity_report.rst` still describes the E5 state (9/14 figures
   differ). The S4 brief assigns aligning the Parity Report to S4, so S1 left
   it unchanged.
3. **Gate coupling.** As in the EXP-001 D1 gates, the new gate imports the
   frozen EXP-002 driver and reads committed E3 run records. This couples a
   permanent gate to an immutable campaign record. It is deliberate, because
   it guarantees the registered comparison and E3's reference arm, and is
   noted for S2.
4. **Host load.** An IDE `snyk-win` language-server process that this session
   did not start held most of the host CPU (about 18,000 s of CPU time since
   03:55). As a result, wall-clock times in this session's records (for
   example, the 289 s green-gate run) are inflated against the uncontended
   runs (12–41 s). No run was killed.
5. **fig13's per-series `label=f"Obj {lbl}"`** (reference) is omitted by the
   port. It is byte-immaterial because no legend is drawn, it is not a
   registered divergence, and it was left unchanged.

### S1.11 Handoff to S2

S2 audits `ab9e422..HEAD` on `hotfix/exp002-d1-figure-parity` against the
brief and the standards, and records A1–A10 here. Points worth independent
re-derivation rather than acceptance:

- Re-run `parity/test_parity_publication.py` on `d90eeab`. It must show the
  18 failures; the S2 brief's item 1 requires the re-run.
- Re-run the decomposition. Check that the 34 divergence specifications
  match the reference source call for call. The transforms' presence
  assertions and fire counts are the mechanical check.
- Check that the 21 previously matching outputs and H4 are intact (S2 brief
  item 3; `prin_tree` in the postfix artefact).
- Check the immutability statement in S1.8 (S2 brief item 4). This includes
  `analysis/exp002_e4_analysis.py` reproducing the seven E4 outputs and
  `report-manifest.json`, which S1 did not re-run.
- Weigh the sensitivity-policy observation (S1.10 item 1) for the
  `EXP-002-r1` handoff.

**Not authorized by S1:** merging PR #34, `EXP-002-r1`, or releasing session
`0164`. Session `0164` stays `BLOCKED`.
