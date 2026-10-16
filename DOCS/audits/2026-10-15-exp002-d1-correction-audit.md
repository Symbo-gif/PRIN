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
| `af89499` | test: the fast-gate argument tests made `mypy --strict` clean (no assertion changed), plus the record of the nine tests failing against the pre-fix module |
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

Recorded verbatim, with commands, start and end times and exit codes, in
[`EVIDENCE/exp002-d1-s1/local-gate.txt`](../../EVIDENCE/exp002-d1-s1/local-gate.txt).
The run was on commit `af89499` (0 tracked changes), from Git Bash with
`C:\Program Files\Git\bin` prepended process-locally.

Host and toolchain:

- Windows 11 (`MINGW64_NT-10.0-26300`), Python 3.14.0,
  `rustc 1.99.0 (b940084d7 2026-09-28)`;
- Matplotlib 3.11.1, NumPy 2.5.1.

This is local evidence only. It is not a hosted CI result, and Linux and
macOS were not tested.

```text
ruff check python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/ EVIDENCE/exp002-d1-s1/   exit 0
ruff format --check python/ tests/ benchmarks/ tools/ parity/ EVIDENCE/exp002-d1-s1/            exit 0
ruff format --check DOCS/experiments/ (source-only include)                                       exit 0
mypy python/prin --strict                                                                         exit 0
mypy DOCS/experiments/ --strict                                                                   exit 0
mypy --strict parity/test_parity_publication.py tests/test_publication_figure_arguments.py \
              EVIDENCE/exp002-d1-s1/root_cause_decomposition.py                                   exit 0
interrogate -c pyproject.toml python/prin                                                         exit 0
bandit -r python/prin DOCS/experiments -c pyproject.toml   (+ the evidence script)                exit 0, no issues
tools/check_deviation_ledger.py 039 040, check_dv_register_gates.py,
  check_skipif_probes.py, check_global_session_registration.py                                    exit 0 (all four)
pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -o faulthandler_timeout=300
    exit 1: 4037 passed, 178 skipped, 55 deselected, 1 failed (1:00:43)
pytest tests/ parity/ --basetemp=.pytest_basetemp -o faulthandler_timeout=300
    exit 1: 6323 passed, 184 skipped, 2 failed (4:11:33)
isolated re-runs of the 3 failed tests (same commit, sequential)                                  exit 0, 3/3 passed
sphinx -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html (after rm -rf DOCS/sphinx/_build)   exit 0
cargo fmt --all -- --check                                                                        exit 0
cargo clippy --workspace --all-targets -- -D warnings                                             exit 0
gitleaks git . (full history, 737 commits) / gitleaks git . --staged                             exit 0, no leaks
git diff --stat fd8854ed HEAD -- EXP-002 record, benchmarks/results/EXP-002/, .github/,
  dependency manifests                                                                            empty
coverage (path-form, targeted): python/prin/reporting/figure_generation.py 99% (missed 191, 196:
  untouched malformed-PNG branches); every line changed by 10d84f2 executed
snyk code test . --severity-threshold=low   0 findings in the 4 new/modified source files
                                            (75 LOW repository-wide, all in untouched files; 0 medium/high)
```

**The three suite failures** were all in code this change does not touch,
and each passed when re-run alone on the same commit:

- `tests/test_exp002_e4_analysis.py::test_linked_raw_root_aborts` (fast
  suite): `PermissionError [WinError 5]` renaming a directory inside
  `.pytest_basetemp`. It passed in the full suite and passed alone (55 s).
- `tests/test_reproduce.py::TestWriteNoFollow::test_does_not_corrupt_a_hard_linked_sibling`
  (full suite): `PermissionError [WinError 5]` on an atomic rename inside
  `.pytest_basetemp`. It passed in the fast suite and passed alone (27 s).
- `tests/test_notebooks.py::test_notebook_executes_end_to_end[02_clevr_n_binding.ipynb]`
  (full suite, `slow`): `nbclient` `CellTimeoutError` after the 900 s
  per-cell limit, in the notebook's training cell. It passed alone (232 s).

The two `WinError 5` failures are the Windows file-handle contention class
that `AGENTS.md` documents, and the notebook timeout is load-induced. The
host was heavily loaded (S1.10 item 4): the full suite took 4 h 11 m against
about 30 min on an idle host. Per Testing Standards §7 item 6, the two suite
runs are recorded as **exit 1**, not as passes. The isolated re-runs are
supplementary evidence. A clean single-pass full-suite run on an idle host
remains open for S2's own reproduction.

**Not run, with reasons:**

- `cargo test` and `cargo doc`: no Rust source changed.
- Snyk Open Source, `pip-audit` and `cargo audit`: no dependency or lockfile
  changed (`cargo audit` red is DV-045, out of scope).
- `--cov=prin` across the full suite: the known host coverage limitation,
  DV-033.

**Aborted first gate run.** A first run on `50d302d` was stopped by this
session at the start of the fast suite. Its extra `mypy --strict` leg over the
new test files had failed with 4 typing errors in
`tests/test_publication_figure_arguments.py`. They were fixed in `af89499`
with no assertion changed, and the gate restarted from the beginning.
Only the session-owned process tree was terminated.

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

---

## S2 — audit record (2026-10-15 UTC)

**Session brief:**
[`2026-10-14-exp002-d1-s2-correction-audit.md`](../sessions/contingencies/2026-10-14-exp002-d1-s2-correction-audit.md).\
**AI pair:** Qwen Code. Read-only audit: no source, test, S1-evidence or
S1-record change was committed. Nothing was fixed; every defect found is
recorded as a finding for S3.\
**Audited range:** `ab9e4225..8fd0ecc9` on `hotfix/exp002-d1-figure-parity`
(9 commits, 23 files, +4,261 / −19).\
**Provenance:** `git fetch --all --prune` run first. Local `HEAD` =
`8fd0ecc9949a607f2a7090fe39205f00bb0078c9` = `origin/hotfix/exp002-d1-figure-parity`
= `PRIN/hotfix/exp002-d1-figure-parity`; working tree clean (0 tracked
changes) at audit start. Branch point `fd8854ed` (the PR #33 merge). Draft
**PR #34** `OPEN`, `isDraft: true`, `headRefOid: 8fd0ecc9…`, `mergeable:
MERGEABLE` — left untouched.\
**Host:** `MINGW64_NT-10.0-26300 3.6.5-22c95533.x86_64`, Python `3.14.0`,
pytest `9.1.1`, project venv. Windows x86_64 only; Linux/macOS not tested
(amendment #48 item 4).\
**Evidence:** [`EVIDENCE/exp002-d1-s2/`](../../EVIDENCE/exp002-d1-s2/README.md).
Every command below is recorded there verbatim with its exit code.

**Host load before starting** (brief item g): measured ~89 % idle
(`\Process(*)\% Processor Time`: `_total` 1589.4, `idle` 1416.8). The IDE
`snyk-win` language server S1 reported as pegging the CPU (PID 5912) is still
resident with ~18,207 s accumulated CPU, but advanced only ~4 s over a 20-minute
window — resident, **not** currently consuming. Also resident and not started by
this session: three `Devin` processes (~5,928 / ~3,348 / ~3,182 s), `java`
(~5,999 s), `pyrefly`, `kilo`. **Reported, not killed**, per the brief.

### S2.0 The five brief-specific verification items

#### Item 1 — The reproduction came first. ✅ VERIFIED

Re-run by this session, not accepted on authority.

`parity/test_parity_publication.py` is **byte-identical between `d90eeab` and
`HEAD`** — `git diff --name-only d90eeabb..HEAD --
parity/test_parity_publication.py` returns empty. The only functional file in
`d90eeab..HEAD` is `python/prin/reporting/figure_generation.py`, so restoring
that one module into `HEAD` reproduces the exact pre-fix state the gate saw at
`d90eeab`. (The brief's alternative — a separate `d90eeab` worktree — was not
needed, and this route avoids the `.venv` `.pth` resolution hazard that a
sibling worktree carries.)

| Step | Command | Result |
|---|---|---|
| restore pre-fix module | `git restore --source d90eeabb -- python/prin/reporting/figure_generation.py` | `sha256 = e0f59253…d533` — **equals the `port_module_sha256` recorded in S1's prefix artefact**; `git diff d90eeabb -- <file>` empty |
| red gate | `.venv/Scripts/python -m pytest parity/test_parity_publication.py -q -rf --basetemp=.pytest_basetemp -o faulthandler_timeout=300 -p no:cacheprovider` | **18 failed, 75 passed** in 14.14 s, **exit 1** |
| red fast-gate tests | same flags, `tests/test_publication_figure_arguments.py` | **9 failed** in 3.52 s, **exit 1** |
| restore | `git restore python/prin/reporting/figure_generation.py` | `sha256 = b41dfc13…c048`; `git status --porcelain` clean |
| green | both files together | **102 passed** in 14.69 s, **exit 0** |

The 18 failures are **exactly** the E3 population — the `.pdf` and `.png` of
`fig5`, `fig7`, `fig8`, `fig9`, `fig10`, `fig11`, `fig12`, `fig14`, `fig15` —
and each failure names its normalized-digest pair. All 9 fast-gate argument
tests failed, each on the specific restored argument (`5.0 == 4`,
`{'baseline'} == {'bottom'}`, `{1} == {5}`, `{1.5} == {1.2}`, `None is not
None`, `1.0 == 0.5`, `{None} == {0.85}`, …).

The gate was committed at `d90eeab` and **pushed before** the fix at `10d84f2`
(commit order verified in `git log`), so the red → green transition is recorded
on the remote. Development Workflow §3 and Testing Standards §1.2/§1.3 are
satisfied: reproduction first, tests in tandem.

Evidence: [`prefix-gate-d90eeab-module.txt`](../../EVIDENCE/exp002-d1-s2/prefix-gate-d90eeab-module.txt),
[`postfix-gate-8fd0ecc9.txt`](../../EVIDENCE/exp002-d1-s2/postfix-gate-8fd0ecc9.txt).

#### Item 2 — The root cause is established, not asserted. ✅ VERIFIED

Re-derived three independent ways, none of which relies on S1's runtime
monkeypatching being correct.

**(a) The decomposition reproduces.**
`.venv/Scripts/python EVIDENCE/exp002-d1-s1/root_cause_decomposition.py
--label postfix --out <scratch outside the repository>` → **exit 0**, printing
`port_vs_reference_differing_count: 0`, `divergences_registered: 34`, 26
byte-material, 8 immaterial, `completeness_all_applied_equals_prefix_port:
true`, `unexplained_stems: []`, `reference_reproduces_e3_reference_arm_all:
true`. Compared field-by-field with the committed postfix artefact
([`decomposition_rerun_check.py`](../../EVIDENCE/exp002-d1-s2/decomposition_rerun_check.py)):
**every field `SAME`** — `stems` (17,818 chars), `summary`, `prin_tree`,
`e3_records`, `comparison`, all four module digests — except `generated_utc`
and `git_head`, which necessarily differ (this run is at `8fd0ecc9`, S1's at
`93715964`). The scratch output was written **outside** the repository, so the
committed artefacts were never at risk.

**(b) The 34 specifications match the reference source call for call** —
statically, without executing matplotlib
([`ast_spec_validation.py`](../../EVIDENCE/exp002-d1-s2/ast_spec_validation.py)).
This is the check that the transforms are not self-confirming:

- **Part B — 34/34 OK, 0 failures.** Each spec names a method the frozen
  reference actually calls, and the claimed argument is present at exactly the
  call indices the spec restricts: `errorbar(linewidth=1.5, markersize=4)`,
  `text(va="bottom")`, `scatter(zorder=5)`, `plot(linewidth=1.2)` ×4,
  `legend(loc="upper right", framealpha=0.8)`, `annotate(bbox=…, va="bottom")`,
  `bar(edgecolor="black", linewidth=0.5)` ×2, `axhline(linewidth=0.8,
  alpha=0.7)`, `plot(markersize=5, linewidth=1.2, label="$\lambda$
  (convergence)")`, `barh(alpha=0.85)`, `plot(markersize=3/4, alpha=0.5,
  linewidth=1)`, `legend(loc="lower left")` ×2, `tick_params` present,
  `set_ylabel("FLOPs (×10³)")`, `set_xticklabels(["δ (1–4 Hz)", …])`,
  `set_xlabel("Speed Multiplier (×)")`, and the two f-string `×` labels.
  An earlier draft of this instrument reported three false failures
  (`D11.5`, `D12.2`, `D12.9`) because it resolved only bare constants; the
  shipped version resolves f-strings by their literal parts and simple local
  name bindings, which is what the reference actually uses
  (`annotate(f"{ratio:.0f}×", …)` at line 807, `set_xticklabels(band_labels, …)`
  at line 866 with `band_labels = ["δ (1–4 Hz)", …]` at line 845,
  `text(i, r + 2, f"{r:.0f}×", …)` at line 886).
- **Part C — 34/34 restored, 0 failures.** The fixed port carries the
  reference's value for every spec, and **no mathtext rewrite survives**.
- **Part D — the `\N{...}` claim holds.** The port's *decoded* strings equal
  the reference's literal Unicode strings for all three re-encoded labels, the
  port source **does** use `\N{...}` escapes and contains **no raw**
  multiplication sign — so `ruff` `RUF001` is satisfied without changing the
  rendered text.

One Part C row is an **observation, not a defect**: `D9.1 plot(linewidth=)
ref=4 port=2`. The reference writes four separate `plot(..., linewidth=1.2)`
calls; the port emits two inside a two-iteration loop, i.e. four runtime calls.
A static literal count cannot see loop multiplicity. It is settled by (c).

**(c) No divergence alters a plotted value**
([`artist_level_equivalence.py`](../../EVIDENCE/exp002-d1-s2/artist_level_equivalence.py)).
All 14 stems were rendered from both modules and compared at matplotlib's own
object model — `Line2D` x/y data (SHA-256 over the `float64` buffer plus shape),
linewidth, markersize, marker, linestyle, alpha, zorder, colour, label;
`Collection` offsets and styling; `Patch` path vertices and styling; `Text`
string, position, alignment, size, rotation, colour; `Axes` limits, scales,
title, axis labels, tick positions and tick-label strings, legend texts.
Result: **14/14 stems EQUAL**. The only differences anywhere are drawing-call
*multisets* — the reference's `set_xlabel`/`set_ylabel` versus the port's
`ax.set(...)` grouping — which produce identical artists. The imported
reference's digest is `575eca5a…1520`, equal to `REFERENCE_PINS`.

**(d) The fix changes nothing else.** `git diff 10d84f2b^ 10d84f2b` touches
exactly 2 files. Every hunk of `figure_generation.py` is a restored drawing
keyword argument, a `\N{...}`-escaped label string, the added
`tick_params(axis="y", labelcolor="#AA3377")` call, or the module docstring.
No data expression, plotted value, other generator, table, normalizer or public
symbol changes.

**Campaign plan §10.4 item 3 is correctly not invoked.** Every one of the 34
divergences is a drawing argument the WP-034 port changed relative to the
frozen reference function it ports; (c) shows no computed quantity differs, so
no reference calculation is implicated and no claim is made that the reference
is defective. No EMA-style mathematical audit is therefore required, and none
was substituted for one. The brief's escalation condition ("any evidence
suggests the reference side, not PRIN, is defective") was **not** met.

Evidence: [`decomposition-postfix-s2-rerun.txt`](../../EVIDENCE/exp002-d1-s2/decomposition-postfix-s2-rerun.txt),
[`decomposition-rerun-vs-committed.txt`](../../EVIDENCE/exp002-d1-s2/decomposition-rerun-vs-committed.txt),
[`ast-spec-validation.txt`](../../EVIDENCE/exp002-d1-s2/ast-spec-validation.txt),
[`artist-level-equivalence.txt`](../../EVIDENCE/exp002-d1-s2/artist-level-equivalence.txt).

#### Item 3 — No regression on the already-matching outputs. ✅ VERIFIED

- **11/11 `.tex` tables** equal both the reference arm and the archived PRINet
  3.0 tables (the gate's `test_prin_tables_match_archived_tables` and
  `test_prin_matches_reference_under_registered_comparison`, both green).
- **The 5 already-matching figures** (`fig2`, `fig3`, `fig4`, `fig6`, `fig13`
  — 10 files) equal the reference, and are **raw-byte-identical to E3's PRIN
  arm**.
- The postfix artefact's `prin_tree` gives `raw_equal_to_e3_prin_arm` = **21**
  files (11 tables + those 10 figure files) and `raw_differing_from_e3_prin_arm`
  = exactly the **18** D1 files. So the correction changed *only* what it had
  to, and changed it to the reference's bytes.
- **H4 holds**: `two_process_raw_identical: true` in the artefact (two separate
  PRIN processes), independently corroborated in-process by the gate's
  `test_prin_rerender_is_raw_byte_identical`.
- **Retained E3 roots intact**: all three legs report `retained_root_present:
  true`, `retained_files: 39`, `39/39` raw and `39/39` normalized digests
  matching their manifested `reproduction.json`, and each `reproduction.json`
  matches its run `manifest.json`. Read only; never modified or deleted.
- **No suite regression**: the fast suite completed a **clean single pass** —
  `4038 passed, 178 skipped, 55 deselected, 0 failed`, exit 0. S1 recorded
  `4037 passed … 1 failed`, i.e. the *same* 4,038-test population with one
  environmental failure; that failure did not reproduce here.

Evidence: [`postfix-artefact-summary-dump.txt`](../../EVIDENCE/exp002-d1-s2/postfix-artefact-summary-dump.txt),
[`pytest-suites.txt`](../../EVIDENCE/exp002-d1-s2/pytest-suites.txt).

#### Item 4 — EXP-002's record is untouched. ✅ VERIFIED

- **Diff is empty.** `git diff --stat fd8854ed..HEAD --
  DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/
  benchmarks/results/EXP-002/` → no output. Also empty for `.github/`,
  `Cargo.lock`, `Cargo.toml`, `pyproject.toml`. No `.tex`/`.md`/`.json` in the
  immutable record changed, so no erratum was appended and none was needed.
- **`verify_manifest` passes on all five `RUN-*` directories** (the registered
  read-only verifier, invoked as `verify_manifest(run_dir,
  run_dir/"manifest.json")` per `exp002_driver.py:1364`): `api-cpu`,
  `conclusions-cpu`, `reproduction-reference-cpu`, `reproduction-prin-cpu`,
  `seedrep0-prin-cpu` — each **PASS**, 2 manifested records, no missing,
  modified or unmanifested entry. The frozen 172-input
  `paper/artefact_manifest.json` recomputes to `300cdc09…2cce5`, equal to
  `INPUT_MANIFEST_SHA`, and verifies **172 records** against the reference
  results root.
- **The E4 analysis still reproduces byte-for-byte — the check S1 did not
  re-run.** A detached worktree of `HEAD` was created **outside** the
  repository (`git worktree add --detach C:/dev/PRIN-s2-e4wt HEAD`), and the
  frozen module was executed there with `-I`:
  `.venv/Scripts/python.exe -I C:/dev/PRIN-s2-e4wt/DOCS/experiments/…/analysis/exp002_e4_analysis.py`
  → **exit 0** in ~2 s, printing `H1: CONFIRMED / H2: CONFIRMED / H3: REFUTED
  / H4: CONFIRMED / H3_sensitivity_policy: REFUTED / D1 flag: True`. The
  worktree copy's digest `7a400aa6…4e4` equals the main checkout's, and the
  module was last touched by `3731fc2` — so the *frozen* analysis ran, not a
  modified one. All **seven** generated outputs are byte-identical to the
  retained copies, and the regenerated `report-manifest.json` equals
  **`6b15dcc112513cdce9cb2d923208f93d3616898225efed545706c56526e68781`** —
  identical to the committed file and to the digest E5 §6.2 records. The
  worktree was removed (`git worktree remove --force`); `git worktree list`
  confirms it is gone; the main tree stayed clean and the retained
  `DOCS/test_and_benchmark_results/EXP-002/` roots (5 `RUN-*` + `analysis`)
  were left in place, unmodified.
- No EXP-002 leg, no `EXP-002-r1` run and no other campaign execution took
  place. `DV-045`, `DV-046`, `DV-047` were not touched or pulled into scope.

Evidence: [`verify-manifest-five-runs.txt`](../../EVIDENCE/exp002-d1-s2/verify-manifest-five-runs.txt),
[`e4-analysis-clean-worktree-reproduction.txt`](../../EVIDENCE/exp002-d1-s2/e4-analysis-clean-worktree-reproduction.txt).

#### Item 5 — Coding Standards §6 evidence is real. ✅ VERIFIED (both legs completed)

**CLI leg — initially BLOCKED, then completed.** The first attempt,
`snyk code test . --severity-threshold=low --sarif-file-output=<scratch>`
(snyk `1.1306.2`), returned `ERROR Authentication error (SNYK-0005) … Status:
401 Unauthorized`, **exit 2**, and wrote **no SARIF**. The local CLI token had
expired and `snyk auth` only prints a browser redirect, so recovery needed an
interactive login by the maintainer. That state was **recorded as blocked, not
as passed** (amendment #48 item 2).

**Resolution (2026-10-16 UTC).** The maintainer re-authenticated the CLI
(`snyk whoami` → `Symbo-gif`, exit 0), and the leg the brief specified was then
run for real: same command, snyk `1.1306.2`, **exit 1** (findings reported — not
a scan failure), **SARIF written** (`sha256 ebc92c86…`, 530,562 B). Its Test
Summary is authoritative for severity: **77 issues — 0 HIGH, 0 MEDIUM, 77 LOW**,
so the §6.2 gate ("0 medium+ findings") is **met**.

**MCP leg — COMPLETED.** Coding Standards §6.4 permits Snyk Code "through the
configured IDE or MCP integration". The authenticated Snyk MCP server
(`mcp__snyk__snyk_code_scan`) was used, and the scan really ran:

| Scope | Threshold | Result |
|---|---|---|
| `C:\dev\PRIN` (whole repository) | `medium` | `{"success":true,"issueCount":0}` |
| `python/prin/reporting/figure_generation.py` | `low` | `{"success":true,"issueCount":0}` |
| `tests/test_publication_figure_arguments.py` | `low` | `{"success":true,"issueCount":0}` |
| `parity/test_parity_publication.py` | `low` | `{"success":true,"issueCount":0}` |
| `EVIDENCE/exp002-d1-s1/root_cause_decomposition.py` | `low` | `{"success":true,"issueCount":0}` |

**0 findings in all four changed first-party source files**, and 0 repo-wide at
`medium` — which is the §6.2 gate ("0 medium+ findings"). The CLI leg now
confirms the same result for those four files **independently of the MCP route**,
through the exact command the brief named.

**The repository-wide LOW total, now re-derived.** The MCP tool returns findings
inline rather than as SARIF, so while the CLI was blocked this figure was
*carried from S1, not re-verified*, and was explicitly not claimed. The CLI leg
supplies it: **77 LOW**, of which **44 are in git-tracked paths** and 33 are in
gitignored on-disk agent-worktree copies (`.claude/worktrees/…`,
`.kilo/worktrees/…`) of files already counted — `snyk code test .` scans the
filesystem, not git. S1's recorded 75 plus the 2 findings in the instruments
this session added accounts for the 77.

**Not triggered:** no dependency or lockfile changed in the audited range (the
diff over `Cargo.lock`, `Cargo.toml`, `pyproject.toml` is empty), so Snyk Open
Source, `pip-audit` and `cargo audit` are not triggered by this correction.
`cargo audit` red is **DV-045**, explicitly out of scope.

Evidence: [`snyk-code.txt`](../../EVIDENCE/exp002-d1-s2/snyk-code.txt) (the
blocked CLI attempt and the MCP leg), [`snyk-code-cli.txt`](../../EVIDENCE/exp002-d1-s2/snyk-code-cli.txt)
(the completed CLI leg and its SARIF filter), filtered by
[`snyk_sarif_filter.py`](../../EVIDENCE/exp002-d1-s2/snyk_sarif_filter.py).

### S2.1 A1 — WP scope

✅ **PASS.** The 23 files in `ab9e4225..HEAD` are all inside the approved
scope: the reproduction gate, the decomposition instrument and its two
artefacts, the fix, the 9 fast-gate tests, the S1 record and brief updates, the
registers and indexes, `CHANGELOG.md`, and `EVIDENCE/exp002-d1-s1/`. **Nothing
undeclared shipped**: no dependency manifest, no `.github/workflows/`, no
EXP-002 record file, no Rust source, no unrelated refactor or performance work.
The out-of-scope items S1 listed (`DV-045`/`046`/`047`, the Parity Report, the
PSR and ledger) were correctly left alone. No scope creep (Development
Workflow §7).

### S2.2 A2 — Plan conformance

✅ **PASS**, with one observation. No numerics were added to Python: the fix
restores drawing arguments and label strings only. "One algorithm, one
implementation" holds — the port renders, it does not re-implement. No crate
layering is touched (no Rust changed). Explicit state/seeding is unaffected.

*Observation (not a finding against this correction):* the module evaluates a
stored exponential fit over a fine grid (`fit["IP_0"] * np.exp(-fine /
fit["sigma_c"])`, line 1079). This is **pre-existing from WP-034**, mirrors the
frozen reference exactly (line 1053), and byte parity with the reference
*requires* it. WP-034's audit already classified this module as
"reporting/rendering … No scientific computation" (`034-wp034-audit.md` §3.2),
so the question is adjudicated; it is restated here only because the wording
interacts with finding `EXP002D1-S2-F7`.

### S2.3 A3 — Test conformance

⚠️ **PASS WITH FINDINGS** (`EXP002D1-S2-F2`, `-F5`).

- **Tests in tandem:** the failing gate was committed at `d90eeab` *before* the
  fix at `10d84f2`, and the fix commit itself carries its 9 tests. Verified by
  commit order and by re-running both (item 1).
- **Every bug fix ships a regression test that fails before the fix**
  (Testing Standards §4): confirmed by direct re-execution — 18 failed and 9
  failed pre-fix, 102 passed post-fix.
- **Changed-code coverage ≥95%:** measured with the **path** form
  (`--cov=python/prin/reporting`); the module form `--cov=prin` fails on this
  host with the PyO3 "cannot load module more than once" error (**DV-033**), so
  no module-form coverage is claimed. `figure_generation.py` whole-file
  **99.41 %** (340 statements, 2 missed: lines 191 and 196, the untouched
  malformed-PNG branches — matching S1's figure exactly). Changed-line
  analysis against base `fd8854ed`: of 82 added/changed lines, **11 are
  executable statements and 11 are executed — 100.00 %**, 0 uncovered.
  ([`changed_line_coverage.py`](../../EVIDENCE/exp002-d1-s2/changed_line_coverage.py);
  `tools/coverage_changed_lines.py` was *not* usable for this — it unions Rust
  `cargo-llvm-cov` lcov runs and does not read Python coverage data.)
- **No test weakened:** no `skip`, `skipif` or `xfail` marker in either new
  test file; no assertion deleted; no tolerance loosened. The parity gate
  compares all 39 files under the registered rule with nothing skipped,
  sampled or toleranced.
- **The fast gate genuinely protects the fix.** Because
  `parity/test_parity_publication.py` is marked `parity` + `slow`, the default
  fast gate never runs it. Measured directly
  ([`fast_gate_divergence_coverage.py`](../../EVIDENCE/exp002-d1-s2/fast_gate_divergence_coverage.py)):
  the 9 tests cite **34/34** registered divergences — all 26 byte-material
  *and* all 8 byte-immaterial — with no unknown IDs. So a re-dropped argument
  fails the default `tests/` run, not just the parity suite.
- **Gap:** the required full suite is **red** — see S2.9 and `EXP002D1-S2-F2`.

### S2.4 A4 — Numerical parity

✅ **PASS**, with one protocol-registration finding (`EXP002D1-S2-F1`).

Under the registered H3 rule all **39/39** publication files now equal the
frozen reference (`port_vs_reference_differing_count: 0`; the gate is green on
all 39 parametrizations). The 21 previously matching outputs are raw-identical
to E3's PRIN arm, and H4's raw determinism holds across two processes. Artist
comparison is 14/14 EQUAL, so no plotted value, limit, tick, label, colour,
alpha or z-order differs. Tables match the archived PRINet 3.0 tables 11/11.

Independently re-derived for this audit
([`both_policies_post_fix.py`](../../EVIDENCE/exp002-d1-s2/both_policies_post_fix.py)),
H3 on the corrected tree under **both** registered policies:

| Comparison | Equal | Differ |
|---|---|---|
| raw bytes (H4's rule) | 0/39 | 39/39 |
| **approved §5.4 policy (H3 primary)** | **39/39** | **0/39** |
| **§11.3 sensitivity policy (pre-exposure `6314532`)** | **14/39** | **25/39** |

All 25 sensitivity-policy residuals are **classified, with 0 unclassified**:

- **14 PDFs — Info key set only.** Reference writes 3 keys
  (`Creator`, `Producer`, `CreationDate`, the last wall-clock); PRIN writes 4
  (`Creator`, `Producer`, `CreationDate`, `ModDate`), all fixed. Every one is
  equal under the approved policy. PRIN's fixed metadata is what makes H4 hold,
  so S1 was right not to change it.
- **11 `.tex` tables — line terminators only.** Equal after CRLF→LF in both
  arms; the reference's text-mode writer emits 13–25 CRLF sequences per table
  on Windows, PRIN emits 0.

This confirms S1.10 item 1 exactly, and confirms it is a **writer/host
property**, not a scientific difference — which is why it is an `EXP-002-r1`
E1/E2 *registration* matter and **not an S1 defect**. It is raised as a finding
only because the two policies now disagree about the verdict, which the
registered text does not govern (see `EXP002D1-S2-F1`).

### S2.5 A5 — Code quality gates

✅ **PASS.** Reproduced locally on `8fd0ecc9`, sequentially (never pytest
concurrently with cargo, per `AGENTS.md`):

| Leg | Result |
|---|---|
| `ruff check python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/ EVIDENCE/exp002-d1-s1/ EVIDENCE/exp002-d1-s2/` | exit 0, all checks passed |
| `ruff format --check` (same roots) | exit 0 |
| `ruff format --check DOCS/experiments/` (source-only include) | exit 0 |
| `mypy python/prin --strict` | exit 0 |
| `mypy DOCS/experiments/ --strict` | exit 0 |
| `mypy --strict` on the changed + new first-party files (7 files) | exit 0 |
| `cargo fmt --all -- --check` | exit 0 |
| `cargo clippy --workspace --all-targets -- -D warnings` | exit 0 |
| `cargo test --workspace` | exit 0, every suite `ok … 0 failed` |
| `sphinx -W --keep-going -b html` after `rm -rf DOCS/sphinx/_build` | exit 0, clean build from scratch (PA4-F2 discipline) |

Two legs initially failed and were **corrected and re-run**, with both attempts
recorded: the first `ruff`/`bandit` failures were caused by two S2 instruments
this session added after its own earlier lint pass (now clean), and the first
`cargo test` died with `os error 32` (`ERROR_SHARING_VIOLATION` building
`lib_prin_core.rlib`) — the documented Windows AV/file-handle contention class,
not a code defect. It passed on re-run in 56 s without needing `-j 1`.

### S2.6 A6 — Security

✅ **PASS**, with one blocked-leg finding (`EXP002D1-S2-F3`).

- `bandit -r python/prin DOCS/experiments -c pyproject.toml` → exit 0, no
  issues. `bandit -r EVIDENCE/exp002-d1-s1 EVIDENCE/exp002-d1-s2` → exit 0,
  **0 issues at every severity**.
- Snyk Code: **both routes now complete and agreeing.** The MCP leg reported 0
  findings in the four changed files and 0 repo-wide at `medium`; after the
  maintainer re-authenticated the CLI, the leg the brief named
  (`snyk code test . --severity-threshold=low --sarif-file-output=…`) ran for
  real and independently confirms **0 findings in the same four files**, with a
  Test Summary of **0 HIGH / 0 MEDIUM / 77 LOW** — so the §6.2 "0 medium+" gate
  is met on both routes. The blocked-CLI state was recorded as blocked while it
  lasted, and its resolution is dated in §S2.0 item 5 (`EXP002D1-S2-F3`,
  **RESOLVED**).
  Per §6.4 the six new S2 instruments were then scanned as new first-party code:
  **2 LOW `python/PT` findings**, remediated twice with a `PR23-F1`-style guard
  and proven non-vacuous by negative tests, but not cleared because Snyk's model
  does not recognise the sanitizer. Recorded as `EXP002D1-S2-F8` with a full
  threat assessment rather than suppressed, **ratified by the maintainer
  2026-10-16 UTC**, and corroborated by the CLI leg at the same two locations.
- **gitleaks** (pinned binary
  `DOCS/test_and_benchmark_results/ea007/full-gate/.tools/gitleaks/bin/gitleaks.exe`):
  full history **738 commits**, ~94.76 MB, **no leaks found**, exit 0;
  `--staged` exit 0. Run although no push is authorized, so the branch is
  known clean.
- No `unsafe` Rust introduced (no Rust changed). No `eval`/`exec`/`compile` of
  dynamic strings, no `pickle.load`, no `shell=True` in any changed file
  (grepped). The single `subprocess.run` in the new S2 coverage instrument uses
  a fixed argv list and carries `# nosec B603 B607` in S1's instrument's style.
- Not triggered: Snyk Open Source, `pip-audit`, `cargo audit` (no dependency or
  lockfile change). `cargo audit` red is DV-045, out of scope.

### S2.7 A7 — Docstring/doc coverage

✅ **PASS.** `interrogate -c pyproject.toml python/prin` → **97.6 %**
(1,011 total, 24 missed) ≥ the 95 % floor. Sphinx `-W --keep-going` clean build
exit 0 from a deleted `_build`. All six new S2 instruments carry module and
public-function docstrings and pass `mypy --strict`. One wording imprecision in
the touched module docstring is recorded as `EXP002D1-S2-F7` (D4).

### S2.8 A8 — Repository hygiene

✅ **PASS**, with one artefact-index finding (`EXP002D1-S2-F4`).

- No `TODO`/`FIXME`/`XXX`/`HACK`/`stub`/`NotImplementedError` marker in
  `python/prin/reporting/figure_generation.py`, and no
  `skip`/`skipif`/`xfail` in either new test file.
- `__all__` unchanged by the fix; the frozen-public-surface tests pass inside
  both suites.
- Gitignore respected: `.pytest_basetemp/`, `.coverage`, `DOCS/sphinx/_build/`,
  `target/` all untracked; the decomposition's scratch output and all S2 runner
  scripts were written **outside** the repository
  (`C:\Users\there\prin-s2-scratch`), so no scratch artefact entered the tree.
  `git status --porcelain` shows only `?? EVIDENCE/exp002-d1-s2/`.
- No orphan files in the audited range — but one committed **S1** evidence file
  is not indexed by its own README (`EXP002D1-S2-F4`).

### S2.9 A9 — CI

✅ **PASS as local gate reproduction. No CI is claimed.**

Amendment #48's local-validation regime is in force and amendment #50's
EXP-002 hosted-check window **closed** when E5 closed. Verified live:
`gh workflow list --all` reports `rust`, `python`, `parity`, `repro`, `snyk`,
`gpu`, `nightly` all **`disabled_manually`** (only the tag-triggered `release`,
manual `gpu-triton`, and GitHub's own Copilot/Dependabot/Dependency-Graph apps
are active). **No hosted check ran on this branch and none is cited.** A9 rests
on local reproduction only, and this record is not evidence about Linux or
macOS.

Reproduced local gate on `8fd0ecc9` (Git Bash with `C:\Program Files\Git\bin`
prepended process-locally; `bash` resolved to `/usr/bin/bash`, so the WSL relay
was not on the path):

| Leg | Result |
|---|---|
| **P1** `pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20` | **exit 0** — `4038 passed, 178 skipped, 55 deselected, 59 warnings in 3098.17 s (0:51:38)`. **Clean single pass** — the result S1 could not obtain and handed to S2. |
| **P2** `pytest tests/ parity/ --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20` | **exit 1** — `1 failed, 6324 passed, 184 skipped, 61 warnings in 7415.80 s (2:03:35)`. The single failure is `tests/test_notebooks.py::test_notebook_executes_end_to_end[02_clevr_n_binding.ipynb]`, `nbclient.exceptions.CellTimeoutError` after the 900 s per-cell limit. See `EXP002D1-S2-F2`. |
| **P3** targeted coverage run (`--cov=python/prin/reporting`, path form) | **exit 0** — `115 passed`; `figure_generation.py` 99.41 %, changed executable lines 11/11 = **100 %** |
| governance checkers (`check_dv_register_gates.py`, `check_skipif_probes.py`, `check_global_session_registration.py`, `check_deviation_ledger.py DOCS/reports/039-… DOCS/reports/040-…`) | exit 0, all four |

Supervised per Testing Standards §7. **No run was killed.** One faulthandler
`Timeout (0:05:00)!` dump appeared on
`test_acceptance_y2q1.py::…::test_clevr6_no_nan` and a second on the notebook
leg; per §7 item 3 these were **not** treated as hangs. Two timestamped
observations 151 s apart were taken (same PID 37760 alive, process CPU
**+35.8 s**, working set **+338 MB**, stack inside
`prin/nn/_bridge.py:108 backward` under `torch.autograd`), and the node's
expected duration was established from committed evidence — S1's own
`--durations=20` records `1086.16 s` for `test_clevr6_no_nan`, ~3.6× the 300 s
threshold, and it is `@pytest.mark.slow` so the fast suite never reaches it.
That test subsequently **passed**. The diagnostic is retained at
[`stall-diagnosis-clevr6-no-nan.txt`](../../EVIDENCE/exp002-d1-s2/stall-diagnosis-clevr6-no-nan.txt).
Per §7 item 6 the full suite is recorded at its **actual exit status 1**; the
incomplete/failed leg is never reported as a pass, and no test was deselected,
skipped or weakened to obtain a green result.

Benchmark regression gates: not tripped and not exercisable — `nightly.yml` is
paused under amendment #48; the in-suite `pytest-benchmark` table recorded no
gate failure.

### S2.10 A10 — Artefact trail

✅ **PASS**, with one index gap (`EXP002D1-S2-F4`).

The prior cycle's artefacts exist and are consistent: PSR-040 is issued; the
EXP-001 D1 precedent (`2026-09-24-exp001-d1-correction-audit.md`, S1→S4
complete) is intact; `EVIDENCE/exp001-d1-s1/` and `EVIDENCE/ea007/` are
present. Within this cycle: `EVIDENCE/exp002-d1-s1/` holds the generator, both
artefacts and the verbatim gate records, and its README indexes **10 of 11**
files. The S1 record (§S1.1–§S1.11) was **read but not edited** by this
session, as the brief requires. The E4 clean-worktree reproduction
independently confirms the record chain end-to-end: frozen module digest →
seven outputs → `report-manifest.json` `6b15dcc1…68781`.

This S2 record adds [`EVIDENCE/exp002-d1-s2/`](../../EVIDENCE/exp002-d1-s2/README.md):
29 files plus its README — seven executable instruments, their verbatim outputs,
and the §6.2 threat assessment behind `EXP002D1-S2-F8`. Every output is
reproducible from a committed instrument; two files whose generators were
uncommitted scratch drafts were deleted rather than indexed, and one superseded
attempt is retained and labelled as such. A mechanical index self-check
(every committed file named in the README, every README link resolving) reports
**0 unindexed, 0 dangling** — the standard this audit applied to S1 in
`EXP002D1-S2-F4`, applied to its own bundle, where it caught and fixed one
missing row.

### S2.11 Findings

| ID | Severity | Dimension | Description | Disposition |
|---|---|---|---|---|
| `EXP002D1-S2-F1` | **D3** | A4 | **The two registered H3 comparison policies now disagree about the verdict.** Post-correction the approved §5.4 policy gives **39/39 equal** (H3 would be `CONFIRMED`) while the §11.3 sensitivity policy gives **14/39 equal** (H3 would still be `REFUTED`). Independently re-derived with all 25 residuals classified and **0 unclassified**: 14 PDFs differ only in the Info **key set** (reference 3 keys incl. a wall-clock `CreationDate`; PRIN 4 fixed keys incl. `ModDate`), and 11 `.tex` tables differ only in **line terminators** (reference CRLF from its text-mode writer on Windows, PRIN LF). Both are writer/host properties the approved policy registers as non-scientific and E2 decision 9 already disclosed. Pre-registration §11.3 item 1's clause — "If the two verdicts differ, E5 must state that H3's verdict depends on a comparison amendment made after outcome exposure" — was drafted for the pre-correction state, where *both* policies refuted; it does not govern a *corrected* generator, whose sensitivity-policy residual is no longer about outcome exposure at all. **This is not an S1 defect**: S1 disclosed it (S1.10 item 1) and correctly assigned it to `EXP-002-r1`. It is raised because the registered text and the post-correction reality have diverged, and because if both policies were carried into `EXP-002-r1` unchanged its E5 could return a policy-dependent verdict and re-block the campaign. | **S3** records the assignment explicitly against this ID; **S4** carries it into the `EXP-002-r1` authorization so that its **E1/E2 deliberately registers** how the two policies are to be read for the re-run (e.g. approve §5.4 as sole primary and retain §11.3 as a disclosed writer-property sensitivity, or register a corrected sensitivity policy). `EXP-002`'s frozen pre-registration is **not** edited — the change belongs in the new record. |
| `EXP002D1-S2-F2` | **D2** | A3 | **The required full suite is red, and the same node has now failed in two consecutive sessions.** `pytest tests/ parity/` exits **1**: `1 failed, 6324 passed, 184 skipped (2:03:35)`. The failure is `tests/test_notebooks.py::test_notebook_executes_end_to_end[02_clevr_n_binding.ipynb]` — `nbclient.exceptions.CellTimeoutError: A cell timed out … after 900 seconds`, in the notebook's training cell. S1 recorded the identical failure and reported it passing alone in 232 s. **S2's run does not support a purely load-induced attribution**: it was far less contended than S1's (2:03:35 vs 4:11:33, ~89 % idle at start, this session deliberately added no concurrent load), S1's two `WinError 5` failures both **passed** here, and the other three notebooks passed in both sessions — yet this node still exceeded 900 s in-suite. Testing Standards §1.5 treats flaky tests as bugs and §4 requires tests be independent and order-insensitive; §7 item 2 requires a finite bound be sized from cited evidence with substantial margin, and 900 s is not sufficient for this cell under full-suite conditions. Not caused by this correction and unrelated to figure generation, but it leaves the cycle unable to record a green full local gate. | **S3** must disposition it, in one of three governed ways: (a) re-size the per-cell bound from cited in-suite evidence per §7 item 2; (b) run the notebook leg as a separately documented workload with its own evidenced bound; or (c) open a **dated DV register row** on the DV-046 precedent (an intermittent, host-sensitive node with a standing disposition). Recorded at its **actual exit status 1** per §7 item 6 — never as a pass. No test may be deselected or weakened to green it. |
| `EXP002D1-S2-F3` | **D4** | A6 | **The local `snyk` CLI's credentials have expired**, so the CLI route to the §6.2 Snyk Code gate is unavailable: `snyk code test . --severity-threshold=low --sarif-file-output=…` → `SNYK-0005`, `401 Unauthorized`, exit **2**, **no SARIF written**. `snyk auth` only prints a browser redirect, so recovery needs an interactive login by the maintainer. The control itself **was** satisfied this session through the MCP integration that §6.4 expressly permits (0 findings in all four changed files; 0 repo-wide at `medium`), so no gate went unmet — but S4's full gate will hit the same wall on the CLI route, and amendment #48 item 2 requires an unavailable control be reported as *blocked*, never as passed. | **RESOLVED (2026-10-16 UTC).** The maintainer re-authenticated the CLI (`snyk whoami` → `Symbo-gif`, exit 0), and the leg the brief named was then run for real: `snyk code test . --severity-threshold=low --sarif-file-output=…`, exit 1 (findings reported, not a scan failure), SARIF written (`ebc92c86…`, 530,562 B), Test Summary **0 HIGH / 0 MEDIUM / 77 LOW**. It independently confirms **0 findings in the four changed files**, agreeing with the MCP route, and supplies the repo-wide LOW figure that could not be re-derived while the CLI was blocked (77 raw; 44 in git-tracked paths). The blocked state is retained in the record rather than overwritten: it was true when observed, and amendment #48 item 2 required it be reported as blocked and never as passed. **Nothing outstanding for S3 or S4.** |
| `EXP002D1-S2-F4` | **D4** | A10 | **A committed S1 evidence file is not indexed by its own README.** `EVIDENCE/exp002-d1-s1/` contains 11 files but its README's index table lists 10 — `fast-tests-against-prefix-module.txt` (the record of the 9 fast-gate tests failing against the pre-fix module) is absent. The file's content is genuine and this session **reproduced it exactly** (9 failed, exit 1), so the evidence is sound; only the index is incomplete, which weakens the artefact trail a reader relies on to know the bundle is complete. That directory carries **no `SHA256SUMS.txt`**, so adding an index row breaks no hash freeze (contrast the manifested `EVIDENCE/ea007/` bundles). | **S3** adds the missing README row. README edit only — the evidence file's bytes are **not** touched, and no S1 evidence is re-manifested. |
| `EXP002D1-S2-F5` | **D4** | A3 | **The fast-gate module docstring understates its own scope.** `tests/test_publication_figure_arguments.py` says the tests "pin each **byte-material** argument", but they pin **all 34** registered divergences, including the 8 byte-immaterial ones (`D5.1`, `D5.3`, `D9.2`, `D11.4`, `D12.5`, `D12.7`, `D15.4`, `D15.7`) — measured at 34/34 with no unknown IDs. The protection is stronger than documented, so a future reader could wrongly conclude the immaterial arguments are unguarded and "tidy" them away. | **S3** corrects the docstring wording. Comment-only; **no assertion changes**, so no test behaviour moves. |
| `EXP002D1-S2-F6` | **D4** | A2 | **One known argument infidelity survives the fix.** The reference's fig13 per-series `label=f"Obj {lbl}"` (with `if j < 5 else None`) is still omitted by the port. It is byte-immaterial because fig13 draws no legend, it was never a registered divergence, and this session's artist-level comparison reports fig13 **EQUAL**. S1 disclosed it (S1.10 item 5) and left it unchanged. It is raised only because the correction's stated principle is an *argument-faithful* port, so a surviving known omission is an inconsistency worth an explicit decision rather than silence. | **S3** either restores it for argument-faithfulness (with a byte-identity re-check, since it must stay immaterial) or records why it is deliberately left. Either outcome closes it. |
| `EXP002D1-S2-F7` | **D4** | A7 | **An absolute claim in the touched module docstring is imprecise.** `python/prin/reporting/figure_generation.py` states "Stored benchmark values are only rendered; **no scientific quantity is recomputed**" — a sentence this fix *expanded*. The module does evaluate a stored exponential fit over a fine grid (`fit["IP_0"] * np.exp(-fine / fit["sigma_c"])`, line 1079), mirroring the frozen reference (line 1053). The behaviour is correct and byte parity **requires** it, and WP-034's audit already classified the module as reporting/rendering, so nothing here is a defect — but the unqualified wording would mislead a reader applying Coding Standards §1.2 ("no numerics in Python"). | **S3** qualifies the wording (e.g. note that stored fit parameters are evaluated for rendering, mirroring the reference) or records the exception. Documentation-only; no behaviour change. |
| `EXP002D1-S2-F8` | **D4** | A6 | **Two residual Snyk Code `python/PT` (CWE-23) LOW findings in S2's own instruments**, raised after §6.4's rescan of the new first-party code this session added: `changed_line_coverage.py:98` and `decomposition_rerun_check.py:92`, both "unsanitized input from a command line argument flows into `pathlib.Path`". **Remediated twice, not suppressed**: a guard was added mirroring `tools/reproduce.py`'s `PR23-F1` discipline — `..`-component rejection, no-follow symlink refusal, regular-file check, resolve-and-confine to an explicit root allowlist, and the resolved path plus SHA-256 recorded in the output. Both instruments were then proven non-vacuous by negative tests (out-of-root, directory, `..`, and a **real symlink** all refused; positive controls accepted; `0 failures`). Snyk still reports both, with the dataflow now pointing *inside* the guard at `candidate = Path(raw)` — its `python/PT` model does not recognise those checks as sanitizers. Clearing it further would require removing the tools' ability to read an out-of-tree scratch artefact, which this brief mandates. Exploit prerequisites: an attacker able to supply argv to a process already running as the auditor, i.e. existing code execution as that user — **no privilege boundary crossed**, read-only sinks, non-shipped tooling under `EVIDENCE/`. The applicable §6.2 gate is **"0 medium+"** and repo-wide at `medium` is **0**, so the gate is met; `bandit` reports 0 issues on the same files. Full assessment: [`snyk-low-findings-threat-assessment.md`](../../EVIDENCE/exp002-d1-s2/snyk-low-findings-threat-assessment.md). | **ACCEPTED WITH ASSESSMENT — RATIFIED by the maintainer 2026-10-16 UTC** ("ratified"), which is the approval §6.2's recorded-threat-assessment route contemplates. Nothing added to `.snyk`, no ignore or severity exclusion, no scan skipped. The subsequently completed **CLI leg corroborates the MCP result at the same two locations** (`changed_line_coverage.py:98`, `decomposition_rerun_check.py:92`), so two independent Snyk routes agree on both the finding and its extent, and the repo-wide severity profile is **0 HIGH / 0 MEDIUM** — the applicable gate. **Re-check at S3's delta re-audit and S4's full gate**, per §6.2's requirement that accepted items stay visible and be re-checked every cycle. |

**Not raised as findings** (verified and dispositioned here so they do not drift
untracked, per Development Workflow §1.3):

- **Gate coupling** (S1.10 item 3): the gate imports the frozen EXP-002 driver
  and reads committed E3 records. Deliberate, mirrors the EXP-001 D1 gates, and
  **durable** — everything it reads is *tracked* (`benchmarks/results/EXP-002/`,
  the archived reference, `paper/artefact_manifest.json`); only the
  *decomposition* script uses the untracked retained roots, and it reports
  `retained_root_present: false` once they are removed.
- **`pytest.importorskip("prinet")`**: if the editable `prinet` install were
  absent, the gate's 93 tests would silently skip. This follows an established
  repository-wide convention (4 other modules do the same), and it is
  **mitigated**: the 9 fast-gate tests import only `prin.reporting`, so all 34
  divergences stay pinned even without the reference installed. Not a finding.
- **Parity Report staleness** (S1.10 item 2): `DOCS/sphinx/parity_report.rst`
  still describes the E5 state (9/14 figures differ). The S4 brief already
  assigns this alignment to S4, so it is tracked there, not raised twice.
- **PSR, deviation ledger, Parity Report** deliberately left to S4 under the
  `DOCS/reports/README.md` one-report-per-closed-cycle rule. Correct.

### S2.12 Verdict

**`PASS-WITH-FINDINGS`.**

Per the brief's rule: `PASS` requires no finding above D4, `FAIL` requires a D1
or systemic drift. This audit raises **one D2, one D3 and six D4** findings and
**no D1**, and finds **no systemic drift** — so the verdict is
`PASS-WITH-FINDINGS`.

All **five** brief-specific items are **VERIFIED**, each by independent
re-execution rather than by accepting S1's record:

1. the reproduction came first — 18 failed / 75 passed and 9 failed on the
   restored pre-fix module, 102 passed after;
2. the root cause is established — the decomposition reproduces field-for-field,
   all 34 specifications validate statically against the reference source, the
   fix diff contains nothing but drawing arguments and label strings, and
   artist-level comparison is 14/14 EQUAL so no plotted value differs;
   §10.4 item 3 correctly not invoked;
3. no regression — 11/11 tables, the 5 already-matching figures, the 21
   raw-identical outputs and H4 all intact, with a clean single-pass fast suite;
4. EXP-002's record is untouched — empty diffs, `verify_manifest` green on all
   five runs and the 172-input manifest, and the frozen E4 module reproducing
   all seven outputs plus `report-manifest.json` `6b15dcc1…68781` byte-for-byte
   from a clean worktree outside the repository;
5. the §6 evidence is real — 0 Snyk Code findings in the four changed files via
   the MCP integration, with the expired-CLI leg reported as **blocked**, never
   as passed.

The correction itself is sound and is corroborated by three independent methods
that agree. **Neither red leg reflects on it**: the full suite's sole failure is
a pre-existing notebook-cell timeout in code this change does not touch
(`EXP002D1-S2-F2`), and the blocked Snyk leg is a host credential expiry
(`EXP002D1-S2-F3`).

`EXP002D1-S2-F1` is the finding that matters beyond this cycle: post-correction
the two registered H3 policies point at different verdicts, and that must be
resolved by registration in `EXP-002-r1`'s own E1/E2 — not by editing
`EXP-002`'s frozen record.

**A `PASS-WITH-FINDINGS` releases nothing.** S3 is mandatory even though no D1
was found, and must resolve `EXP002D1-S2-F2` (D2) first, then `-F1` (D3), then
the six D4 items in order; S4 follows; and session `0164` stays **BLOCKED**
until all four conditional sessions close **and** `EXP-002-r1`'s E5 returns a
non-reversal verdict verified and accepted by the maintainer (or a Project Plan
§8.3 amendment is adopted).

**Not authorized by S2:** merging PR #34, marking it ready for review,
`EXP-002-r1`, or releasing session `0164`. Session `0164` stays `BLOCKED`.

### S2.13 Addendum — two calls delegated to this session (2026-10-15 UTC)

After the record above was committed as `fadc8ce8`, the maintainer answered the
two items S2 had escalated with a delegation rather than a decision:

> "i authorize you to make the call that follows etablished methodologies and
> governance rigorously to meet the standards, goals, and plans in project."

Both calls are therefore made here on the governance record, with their
reasoning, and are flagged for ratification.

**Call 1 — the Snyk route, and two findings in S2's own code.**
Coding Standards §6.4 requires that *new or modified first-party code* be
scanned and that findings attributable to the change be remediated and rescanned
until the applicable gate is clean. S2's original scan predated six of its own
instruments, so that obligation was unmet. Scanning them raised **2 LOW
`python/PT` (CWE-23) findings** — in `changed_line_coverage.py` and
`decomposition_rerun_check.py`, both S2-authored, neither shipped.

The call: **remediate for real, then record an assessment — do not suppress.**
A guard was added on the repository's own audited `PR23-F1` pattern
(`tools/reproduce.py::_reject_symlink`/`_reject_non_regular`): `..`-component
rejection, no-follow symlink refusal, regular-file check, resolve-and-confine to
an explicit root allowlist, and the resolved path plus SHA-256 recorded in the
output. This matters beyond confidentiality, because these are
**evidence-producing** tools — a symlinked input would be compared while the
evidence named a different path, which is exactly `PR23-F1`'s "content verified,
provenance not" failure mode. The guard was proven non-vacuous by negative tests
(out-of-root, directory, `..`, and a **real symlink** all refused; positive
controls accepted; `0 failures`). Two remediation iterations were rescanned;
Snyk still reports both, with the dataflow now pointing *inside* the guard at
`candidate = Path(raw)`, so its `python/PT` model does not treat those checks as
sanitizers.

The applicable §6.2 gate is **"0 medium+ findings"**, and repo-wide at `medium`
is **0** — the gate is met. The residual is recorded as
**`EXP002D1-S2-F8` (D4), ACCEPTED WITH ASSESSMENT**, with a full threat
assessment naming the finding, affected API, exploit prerequisites and
compensating controls, per §6.2's pattern for items with no available fix.
Nothing was added to `.snyk`; no ignore or severity exclusion was created; no
scan was skipped. The **CLI leg stays recorded as BLOCKED** (`401 SNYK-0005`) —
the MCP route §6.4 permits is the governing route for this cycle, and
re-authenticating the CLI remains a maintainer-only action.

**Call 2 — do not push at S2.** S2's commit stays **local**.

The governing text is explicit and points one way. Development Workflow §3's S2
rules state: "Commit the Audit Report locally; do **not** push." Amendment #28
states that "Every session **commits** locally at its own exit gate. Only the
**S4** commit that closes a cycle is **pushed**," and that "S1, S2, and S3 exit
gates are satisfied by the **local** gate … they do not push." The §7 hotfix
exception *permits* an immediate push but does not require one.

S1's push is not a precedent that carries forward: it was a **specific**
maintainer pre-authorization taken for a **specific** evidentiary purpose — "The
failing-test commit is pushed before the fix commit, so the red → green
transition is recorded on the remote." That purpose does not recur at S2; the
audit record is documentation, not a state transition anyone needs to observe on
the remote mid-cycle.

Three further reasons reinforce the rule rather than merely permitting it:

1. **Pushing now would publish an audit with eight unremediated findings** —
   including a **D2** whose required full-suite gate is red — to PR #34's
   reviewers before S3 has recorded any disposition. Amendment #28's design is
   that a cycle's diff is reviewed **once**, at S4, over the whole S1–S4 range.
2. **No hosted check would run.** All seven check workflows are verified
   `disabled_manually` and amendment #50's window is closed, so a push buys no CI
   evidence — only partial visibility of an incomplete cycle.
3. **Amendment #48 item 6** requires a full-history secret scan before *every*
   push. Deferring avoids a push/scan cycle that governance does not ask for.
   (The branch is nonetheless known clean: 738 commits scanned, no leaks.)

So the cycle's push point remains **S4**, which will carry S1's already-pushed
commits plus S2's, S3's and its own in one range. The full-history gitleaks scan
will be re-run at that push, since a scan result is about the commit it names.

**Ratification.** Both calls are recorded as flagged defaults under the
maintainer's delegation, not as settled exemptions. `EXP002D1-S2-F8` in
particular invites reversal: if the maintainer prefers the two LOW findings
cleared over the instruments' ability to read an out-of-tree scratch artefact —
which this brief mandates — the alternative is to confine them to the repository
and the platform temp root and move the scratch location, a usability change to
the documented regeneration workflow rather than a security improvement.

Evidence added by this addendum:
[`snyk-low-findings-threat-assessment.md`](../../EVIDENCE/exp002-d1-s2/snyk-low-findings-threat-assessment.md),
[`path-guard-negative-tests.txt`](../../EVIDENCE/exp002-d1-s2/path-guard-negative-tests.txt),
[`changed-line-coverage.txt`](../../EVIDENCE/exp002-d1-s2/changed-line-coverage.txt).

### S2.14 Addendum — ratification, and the CLI leg completed (2026-10-16 UTC)

The maintainer responded to §S2.13's two escalated calls with:

> "ratified, and I believe snyk is authenticated now on cli. you are authorized
> to complete the remaining s2 related work now on my behalf in preparation for
> s3."

Three things followed, all recorded here rather than folded silently into the
sections above, so the sequence stays auditable.

**1. `EXP002D1-S2-F8` is ratified.** The maintainer's "ratified" is the approval
that Coding Standards §6.2's recorded-threat-assessment route contemplates, so
the acceptance moves from *flagged default* to *approved*. The finding stays
visible in the ledger and is re-checked at S3 and S4, per §6.2's requirement
that accepted items not disappear.

**2. `EXP002D1-S2-F3` is resolved, not merely noted.** Authentication was
verified before being relied on — `snyk whoami` returns `Symbo-gif`, exit 0 —
rather than accepting "I believe snyk is authenticated" on assertion. The leg the
brief specified then ran for real:

```text
snyk code test . --severity-threshold=low --sarif-file-output=<scratch>
  snyk 1.1306.2, exit 1 (findings reported — not a scan failure)
  SARIF written: sha256 ebc92c86…bb0d, 530,562 bytes
  Test Summary: Total issues 77 | Ignored 0 | Open 77 [ 0 HIGH  0 MEDIUM  77 LOW ]
```

Filtered by the new committed instrument
[`snyk_sarif_filter.py`](../../EVIDENCE/exp002-d1-s2/snyk_sarif_filter.py):

| Bucket | Result |
|---|---|
| The **four changed first-party files** (brief item f) | **0 findings** — independently confirms S1's claim through the exact route the brief named, and agrees with the MCP leg |
| The **six S2 instruments** (`EXP002D1-S2-F8`) | **2 findings**, `python/PT`, at `changed_line_coverage.py:98` and `decomposition_rerun_check.py:92` — the same two locations the MCP route reported |
| Repository-wide | **77 raw**; **44 in git-tracked paths**; rules `python/PT` ×71, `python/PT/test` ×6 |
| §6.2 gate ("0 medium+ findings") | **MET** — 0 HIGH, 0 MEDIUM |

Two independent Snyk routes (MCP and CLI) now agree on both the clean result for
the changed files and the exact extent of the F8 residual. The repo-wide LOW
figure that §S2.0 item 5 had to leave as *carried, not re-verified* is now
re-derived: **77**, against S1's recorded **75** — a delta of exactly the 2
findings in the instruments this session added.

**3. Two properties of Snyk's output were established by inspection and are
recorded so the next gate does not misread them.** They are the reason a first
inline filter produced an unusable severity line, and both are now documented in
the committed instrument's docstring:

- **Snyk Code's SARIF carries no severity.** Every `result.level` is `"note"`,
  and neither `result.properties` (only `isAutofixable`, `priorityScore`,
  `priorityScoreFactors`) nor `rule.properties` (only `tags`, `categories`,
  `precision`, `cwe`, example fixes) holds a severity name or a
  `security-severity` score. The authoritative severity breakdown is the CLI's
  own `Test Summary` block, which must be transcribed from the console output.
  An earlier filter reported `by severity: {note: 77}` and `LOW total: 0`; both
  were artefacts of that, and are corrected here rather than left standing.
- **`snyk code test .` scans the filesystem, not git.** This repository
  directory also holds gitignored agent worktrees, so the same logical file is
  reported once per copy — `tools/reproduce.py` appears three times (5 findings
  each). Of the 77, **33 are such untracked copies** (`.claude` 10, `.kilo` 23).
  A repo-wide total is therefore **not** a census of tracked files, and two
  totals taken at different times are comparable only if the on-disk worktree
  set is unchanged. This is why the filter reports tracked and raw totals
  separately.

**Verdict and tally.** Unchanged: **`PASS-WITH-FINDINGS`**, no D1, no systemic
drift. Eight findings were raised; **`-F3` is now RESOLVED** and **`-F8` is
RATIFIED**, leaving **six for S3**: `-F2` (D2) first, then `-F1` (D3), then
`-F4`, `-F5`, `-F6`, `-F7` (D4). `-F8` carries no S3 action beyond the standing
re-check.

**Push.** Still **not pushed**, per §S2.13 call 2, which the maintainer's
"ratified" confirms. Development Workflow §3's S2 rule and amendment #28 put the
cycle's push point at S4; the branch is ahead of `origin` by the S2 commits and
will be carried in S4's single push with a fresh full-history secret scan.

Evidence added by this addendum:
[`snyk-code-cli.txt`](../../EVIDENCE/exp002-d1-s2/snyk-code-cli.txt),
[`snyk_sarif_filter.py`](../../EVIDENCE/exp002-d1-s2/snyk_sarif_filter.py).


---

## S3 — remediation and delta verification (2026-10-16 UTC)

**Session brief:**
[`2026-10-14-exp002-d1-s3-correction-remediation.md`](../sessions/contingencies/2026-10-14-exp002-d1-s3-correction-remediation.md).\
**AI pair:** Claude Sonnet 5.5 (Claude Code), working to the maintainer's session
prompt (the S3 execution contract). The cold reviewers were Devin `swe-2-high`,
Antigravity `agy` (`gemini-3.8-flash-high`) and Qwen Code (`qwen3.8-max-preview`).\
**Branch / PR:** `hotfix/exp002-d1-figure-parity`; draft **PR #34**, `OPEN`,
`isDraft: true`, head `8fd0ecc9…` — not touched. **Nothing is pushed** (Development
Workflow §3 and Plan amendment #28 put the cycle's push point at S4).\
**Evidence:** [`EVIDENCE/exp002-d1-s3/`](../../EVIDENCE/exp002-d1-s3/README.md). Every
command below is recorded there verbatim with its exit code.\
**Status:** the resolutions, the F2 measurement and the review loop are recorded
in §S3.1–§S3.6. The closing gate (§S3.7), the delta re-audit result (§S3.8) and the
verdict (§S3.10) are appended to this section after the last review round has
converged.

### S3.0 Entry state

`git fetch --all --prune` was run first. Everything the brief asserted was checked
rather than assumed:

| Item | Observed |
|---|---|
| Branch / `HEAD` | `hotfix/exp002-d1-figure-parity` @ `5ba0129e8f225c62de92593d329be63ca7e7cf7e` |
| Ahead of `origin` | 4 commits (`fadc8ce8`, `9c3f5edd`, `eae1fab8`, `5ba0129e`); `origin/hotfix/exp002-d1-figure-parity` = `8fd0ecc9949a607f2a7090fe39205f00bb0078c9` |
| Working tree | clean (`git status --porcelain` empty) |
| PR #34 | `OPEN`, `isDraft: true`, `headRefOid` `8fd0ecc9…` |
| Branch point | `fd8854ed87a21e01f16e2f7128b431e74085a26e` (the PR #33 merge) |
| Host | HP OMEN 16L desktop, AMD Ryzen 7 8700F (8 cores / 16 threads), 31.6 GB RAM, Windows 11 (`MINGW64_NT-10.0-26300`), Python 3.14.0, pytest 9.1.1, Matplotlib 3.11.1, NumPy 2.5.1, torch 2.11.0+cu128, nbclient 0.11.0 |

Windows x86_64 only; Linux and macOS were **not** tested (Plan amendment #48 item 4).
No hosted check ran or is cited. The seven check workflows stay disabled.

### S3.1 Finding resolutions

Work started with F2, the finding the brief and §S2.12 order first. Its
disposition needs an observed full-suite run of about three hours, so while the
standalone measurements and then that run were in progress the independent
findings were resolved; the **commit order therefore does not follow D1→D4**
(see §S3.9, item 1).

| ID | Severity | Resolution | Commit(s) | Evidence |
|---|---|---|---|---|
| `EXP002D1-S2-F2` | D2 | **FIXED** (route (a), re-size from cited evidence) | `91f3327a` | §S3.2; [`f2/README.md`](../../EVIDENCE/exp002-d1-s3/f2/README.md) |
| `EXP002D1-S2-F1` | D3 | **ASSIGNED** to S4 and `EXP-002-r1` E1/E2; no amendment | `9583eb4d` | §S3.3; the S4 brief's "Carried from S3" section |
| `EXP002D1-S2-F4` | D4 | **FIXED** | `d53ab885` | `index-selfcheck-s1.txt` |
| `EXP002D1-S2-F5` | D4 | **FIXED** | `2db18fc3` | `docstring-only-check.txt`, `f6-verification.txt` V3 |
| `EXP002D1-S2-F6` | D4 | **FIXED** (restored, byte-immateriality re-proved) | `2b8b7a55` | `f6-test-red-before-fix.txt`, `f6-verification.txt` |
| `EXP002D1-S2-F7` | D4 | **FIXED**, then corrected after a cold review found the first rewording over-claimed | `1403451c`, `33923be5` | `docstring-only-check.txt`; `cold-review/triage.md` R1-1 |
| `EXP002D1-S2-F8` | D4 | **RATIFIED**; standing re-check done, **one further same-class finding recorded** | none | §S3.4; `snyk-code-s3-after-review-fixes.txt` |
| `EXP002D1-S2-F3` | D4 | **RESOLVED in §S2.14**; not reopened. `snyk whoami` → `Symbo-gif` (exit 0) was verified before the CLI was relied on | none | `snyk-code-s3.txt` |

Per-finding detail for F4–F7:

- **F4.** Before editing, `EVIDENCE/exp002-d1-s1/` was re-checked for a hash freeze:
  12 tracked files, no `SHA256SUMS` or manifest. One README row was added
  (+1 line, 0 deleted). The evidence file's bytes are untouched (sha256 `fdfa17cc…04dd`,
  last modified by `af894998`). `index_selfcheck.py` reports the file unindexed
  before the edit and 0 unindexed / 0 dangling after it.
- **F5.** The module docstring now says the tests pin all 34 registered
  divergences, including the 8 byte-immaterial ones. `docstring_only_check.py`
  shows the AST is identical outside the module docstring; the file runs 9 passed
  before and after; `fast_gate_divergence_coverage.py` still reports 34/34 and no
  longer prints the "UNDERSTATES" line.
- **F6.** Restored `label=f"Obj {label}" if index < 5 else None` in `fig13`. The
  regression test was written first and failed (`'_child0' != 'Obj 0'`), then
  passed. Matplotlib files an omitted label and `label=None` identically as
  `_child<n>`, so the `index < 5` cut-off is observable only through a synthetic
  seven-group copy of the archived data (the archived data has exactly five label
  groups); the test builds one. Byte immateriality was re-proved rather than
  assumed: `parity/test_parity_publication.py` 93 passed; artist-level
  equivalence 14/14 EQUAL; and **all 28 figure files are raw-byte identical
  before and after the change** (`raw_byte_identity.py`), with a negative control
  (the pre-fix port) that differs on exactly the 18 D1 files.
- **F7.** The docstring now lists the display-level arithmetic. The audit's example
  named only the Fig. 15 fit; the module also plots Fig. 12's `K_c` ratio and
  annotates Fig. 11's FLOPs ratios, so the first rewording ("the only arithmetic is
  …") was itself an over-claim. A cold reviewer's transcript pointed at Fig. 10's
  difference of means; reading the code confirmed it, and `33923be5` lists the
  derived quantities by kind, explicitly not exhaustively. Both commits are
  docstring-only (AST identical outside the module docstring).

### S3.2 F2 — the required full suite

**Disposition: route (a), re-size the per-cell bound from cited in-suite
evidence.** No test was deselected, skipped, xfailed or shortened and no assertion
changed. The route needs no register edit, so no maintainer-approval trail is
needed or claimed.

*What was measured* (all in [`f2/`](../../EVIDENCE/exp002-d1-s3/f2/README.md)):

1. **The notebooks are not slow.** Alone on a quiet host the four complete in
   73.3 / 71.1 / 44.5 / 37.0 s. Notebooks 01, 03, 04 are single-threaded; notebook
   02 does 435 CPU-seconds across about six cores with a 3.2 GB working set.
2. **Inside the full suite they take 8–42× longer.** An observed run of the
   required `tests/ parity/` invocation on a clean tree (`2f796ddf`, 2026-10-16
   03:20:04Z–06:03:32Z) with the notebook timeout lifted by a diagnostic plugin,
   so nothing was killed, finished **exit 0, `6326 passed, 184 skipped`, 2 h 42 m**
   and gave the first uncensored in-suite durations: 678.9 / **2975.0** / 367.3 /
   382.1 s for notebooks 01 / 02 / 03 / 04 (9.3× / **41.8×** / 8.3× / 10.3× their
   standalone time). S1 and S2's 02 durations (1052.8 s, 1064.0 s) were killed at
   the 900 s bound and are censored.
3. **The cause is CPU starvation by processes outside PRIN, not memory.** From the
   moment the first `tests/test_exp002_*` tests began (03:33:47Z), all 102 samples to
   06:00Z show the host at 98–100% CPU while pytest received a median **0.01
   CPU-s/s** (it had received a median 2.8 before): a drop of about 280×. Over those
   2 h 27 m the CPU was used by `System`, `mc-fw-host.exe`, `Devin.exe` and
   `svchost.exe`, and by `rg.exe`: at 04:37Z there were **134 concurrent
   `rg.exe --files --hidden …` processes, all children of one `Devin.exe` Node
   service**, 2,093 cumulative CPU-seconds. The notebook kernels received 0.17–0.33
   CPU-s per wall-second, host available memory never fell below 5.5 GB, and paging
   averaged at most 26 pages/s. When pytest exited the host fell from 100% to 33%
   within about a minute.
4. **A smaller group reproduces it.** A paired experiment ran notebook 02 alone
   (control: **80.7 s**, 5.8 cores) and again while only `tests/test_exp002_driver.py`
   and `tests/test_exp002_e4_analysis.py` ran beside it (treatment: **3,484 s, 43.2×**,
   0.32 CPU/wall, host 99.9%). The training cell went from 35.7 s to 1,926 s.

*What is not established.* What starts the `rg.exe` scans, and why `System` and
`mc-fw-host.exe` are busy: the timing puts the onset at the `test_exp002_*` group
in both runs, but no process was stopped to test causation, and these are the
maintainer's processes — they were observed, never killed. Why the contention
drained within a minute of the end of the full suite but persisted for over 28
minutes after the experiment's load generator exited is not explained. Nothing
here implicates PRIN code.

*The change* (`tests/test_notebooks.py`, `91f3327a`). Each notebook has its own
per-cell bound: **3 × the largest completed contended duration recorded for it,
rounded up to a multiple of 900 s**.

| Notebook | Largest completed contended duration | Bound (was 900 s) |
|---|---|---|
| `01_oscillosim_quickstart` | 800.07 s (S2, full suite) | 2,700 s |
| `02_clevr_n_binding` | 3,484.0 s (S3 experiment) | 10,800 s |
| `03_custom_coupling` | 408.96 s (S1, full suite) | 1,800 s |
| `04_torch_bridge` | 389.81 s (S1, full suite) | 1,800 s |

Two fast tests pin each bound to its recorded worst case, so neither can move
without the other. They **fail against the old 900 s bounds (4 failed) and pass
after (33 passed, the 4 slow executing tests still collected)**
(`f2/test-red-before-fix.txt`, `f2/test-green-after-fix.txt`). Three pre-existing
`mypy --strict` errors in the same file (bare `dict` annotations) were fixed
incidentally, typing only; they are present at `HEAD~` (`5ba0129e`).

*The trade-off, stated plainly.* The bound is now a ceiling for a leg that is
starved but progressing, not a performance check: the quiet-host durations are
37–73 s. A genuine hang takes up to three hours to be caught by the bound, so hang
detection in this suite rests, as Testing Standards §7 item 3 already requires,
on supervised observation rather than on the timeout. Re-sizing is the route the
audit offered and §7 item 2 prescribes ("sized from cited completed/incomplete
evidence for that workload, plus substantial margin for … host variability"); it
does not make the host quieter, and the required gate will be slow whenever the
same tooling is active.

### S3.3 F1 — the two registered H3 policies

Resolved by **assignment**, as S2 specified; no plan amendment is requested and
none is adopted. The S4 brief now carries the finding into the `EXP-002-r1`
authorization (closure item 5, plus a "Carried from S3" section):

1. `EXP-002-r1`'s pre-registration must **name the deciding rule** for H3 and the
   status of the other policy. S3 does not choose.
2. It must **replace or restate the §11.3 item 1 clause** ("if the two verdicts
   differ, E5 must state that H3's verdict depends on a comparison amendment made
   after outcome exposure, and must not report either verdict alone"), which was
   written for a state in which both policies refuted, before any `r1` data exist.
3. The choice must be **fixed before the first `RUN-` directory exists**, and
   must **disclose outcome exposure**: it is made with knowledge of `EXP-002`'s
   results and of S2's residual classification (14 PDF Info key sets, 11 table line
   terminators, 0 unclassified).
4. PRIN's fixed PDF metadata — what makes H4 hold — and the frozen reference must
   **not** be altered to chase §11.3 equality.
5. `EXP-002`'s frozen `preregistration.md` is never edited.

Campaign plan §10.4 item 4 already requires a new pre-registration for the
re-run, which is the governed place for this registration. If `EXP-002-r1`'s E1 or
E2 finds the choice cannot be made inside a pre-registration (for example if the
"not a reversal" test of §10.4 item 5 itself needed reinterpreting), that is an
amendment matter to be drafted for maintainer approval.

### S3.4 F8 — the standing Snyk re-check

Coding Standards §6.2 requires accepted items to stay visible and be re-checked
every cycle. `snyk code test . --severity-threshold=low` (snyk `1.1306.2`, account
`Symbo-gif`) was run for the S3 tree. The Snyk MCP route was **not available** in
this session (no Snyk MCP tool was exposed) and is not claimed. Nothing was added
to `.snyk`; no ignore or severity exclusion was created.

- **The gate holds:** Test Summary **0 HIGH / 0 MEDIUM / 97 LOW** on the final
  rescan; 45 findings are in git-known paths and 52 in gitignored on-disk agent
  worktree copies (the scan counts the filesystem, not git).
- **S3's own code:** **0 findings** in the two changed first-party files and in the
  S3-added instruments. The *first* scan had reported **one MEDIUM**,
  `python/CommandInjection`, in the new `suite_sampler.py` (the `typeperf.exe` path
  was built from an environment variable). It was remediated, not suppressed, by a
  fixed absolute path, and the first-scan record is kept
  (`snyk-code-s3-first-scan-medium.txt`). After the round 2 fixes the scan was
  repeated (`snyk-code-s3-after-review-fixes.txt`): resolving `git` to an absolute
  path with `shutil.which` introduced nothing.
- **The two ratified locations are unchanged:** `changed_line_coverage.py:98` and
  `decomposition_rerun_check.py:92` (`python/PT`, LOW).
- **One further finding of the same class, not in the F8 record:**
  `EVIDENCE/exp002-d1-s2/snyk_sarif_filter.py:142` (`python/PT`, LOW, "unsanitized
  input from a command line argument flows into `pathlib.Path`"). It is S2's
  seventh instrument, written after S2's own CLI scan, so no S2 scan could have
  reported it. Its dataflow, prerequisites (argv control implies existing code
  execution as the auditor), read-only sink and non-shipped location match the
  assessment ratified for the other two. **It is recorded here for the maintainer
  to extend F8's ratification to a third location; S3 does not ratify it and did
  not edit S2's instrument.** S3's own instruments avoid the class by reading
  standard input or a closed set of names.
- **A correction to a conclusion S2 drew.** S2 recorded that "Snyk Code's SARIF
  carries no severity" because every `result.level` in its report was `note`. Its
  report had no MEDIUM finding. S3's first scan had exactly one, and exactly one
  result carried `warning` (the other 97 carried `note`), matching the console's
  `0 HIGH 1 MEDIUM 97 LOW`. So `note` = LOW and `warning` = MEDIUM on the
  evidence (`error` = HIGH is the SARIF convention and has not been observed). The
  CLI's Test Summary remains the authoritative breakdown. S2's text is not edited.

### S3.5 The cold review loop

Three reviewers received an identical brief file and no account of what changed;
the change set was supplied as `git diff` and `git log --stat` files. Interfaces
were discovered from each tool's `--help` and model listing: Devin
(`devin --model swe-2-high -p --prompt-file <brief> --permission-mode smart
--export <out>`), `agy` (`--model gemini-3.8-flash-high --mode plan -p`), Qwen
(`-m qwen3.8-max-preview -o text -p`). There is no sandbox on Windows, so
read-only was enforced in the brief and checked afterwards: `git status
--porcelain` was empty before and after each round. Full indexes, raw outputs and
the triage are in [`cold-review/`](../../EVIDENCE/exp002-d1-s3/cold-review/README.md).

| Round | Tree | Reviewers that reported | Claims | CONFIRMED | REFUTED | NOT REPRODUCIBLE |
|---|---|---|---|---|---|---|
| 1 — **degraded** | `7dbfc546`, brief v1 | none (see below) | 1 (Devin narration) | 1 | 0 | 0 |
| 2 | `33923be5`, brief v2 | Devin 8, agy 6 (+9 refuted narrative assertions), Qwen 11 | 25 findings → 15 distinct | 15 | 9 | 0 |
| 3 | to be recorded | | | | | |
| 4 | to be recorded | | | | | |

**Round 1** produced no reviewer report. Devin aborted when `--permission-mode
smart` rejected a `git check-ignore` command; `agy` aborted at its first shell
attempt (headless mode cannot prompt); Qwen was terminated by the caller after
about 24 minutes with empty output. **That termination was premature**: Qwen's own
session log was being written continuously until the moment it was killed, and `-o
text` prints only at the end, so empty stdout and low CPU were the wrong signals;
Testing Standards §7 item 3's "completed-work count" was not checked. Qwen
delivered a full report in round 2. Round 1 did yield one claim worth measuring (Devin's
narration that the F7 docstring's list of arithmetic omitted Fig. 10), which was
**confirmed** and fixed in `33923be5`.

**Round 2** used brief v2, which forbids shell commands for all three reviewers
(a denied command ended two sessions in round 1). The Devin and `agy` flags are
unchanged; the brief is stricter than the S3 brief's §6.2, which allows read-only
commands. All three reported. The triage reproduced each checkable claim and
searched for each thing agy named: **agy's report contained nine assertions that
name commits, files, tests and a `Testing_Standards.md` edit which do not exist**
(for example commit subjects such as `fix(reporting): document and assert
series-label arg on fig13 (EXP002D1-S2-F4)` and a test
`test_negative_control_detects_deliberate_signature_drift`); these are refuted by
search, and the real findings it also made are kept. The 15 distinct confirmed
claims, all fixed or dispositioned (some were transient and close with this
section), included: the sampler could never exit if pytest was never seen — and, found
while fixing it, it counted any shell whose command line merely mentioned pytest as
a pytest process; the run label could climb out of the scratch directory;
`immutability.sh` printed but did not enforce its S1-evidence rule; the Snyk
filter's exit status did not encode its gate; four instruments called `git` by bare
name against Coding Standards §6.1; and several README claims were stale or too
strong. Qwen's explicit "checked, no finding" statements held.

### S3.6 Evidence discipline

`index_selfcheck.py` (every committed file indexed by its directory's README, every
link resolving) reports **0 unindexed, 0 dangling** for `exp002-d1-s1` (after F4),
`exp002-d1-s2` and `exp002-d1-s3`. It was used to catch two defects in S3's own
bundle: `*.log` is gitignored, so two console logs would silently not have been
committed (renamed `.txt`), and the first version of the README claimed lint
cleanliness that no committed output evidenced (now evidenced by the closing gate).

### S3.7 Closing gate

*Appended after the last review round.*

### S3.8 Delta re-audit

*Appended after the last review round.*

### S3.9 Deviations and observations

1. **Commit order does not follow D1→D4.** F5, F7, F4 and F6 (D4) and F1 (D3) were
   committed before F2's disposition (D2). The history is not rewritten. The
   *work* order did start with F2: its standalone baselines ran 01:38Z–01:42Z, before
   the first S3 commit at 01:43Z, and its disposition needed a roughly three-hour
   observed run during which only independent changes could be made. The findings
   are independent, so the order changed no content.
2. **Qwen's round 1 termination was premature** (§S3.5). Recorded in the triage.
3. **The brief was changed between rounds 1 and 2** (v1 → v2), stricter about
   shell commands, for the reason in §S3.5. The Devin invocation (`--permission-mode
   smart`) was kept.
4. **S3 loaded the maintainer's machine for several hours**: the observed full suite
   (2 h 42 m) and the contention experiment (about one hour, including the 499-test
   load generator), in addition to the gates. Both were run on a clean tree, output
   went outside the repository, and nothing belonging to the maintainer was stopped.
5. **A process slip, caught and corrected:** a Python `write_text` edit on Windows
   converted `tests/test_publication_figure_arguments.py` to CRLF in the working
   copy. The committed blobs were LF (`.gitattributes` `text=auto eol=lf`); the
   working copies were normalised and verified.
6. **Out of scope, recorded as candidates and not done:** (a) operating guidance
   for the gate (for example excluding `.pytest_basetemp` from IDE workspace
   scanning and security-software real-time scanning, or asking the maintainer to
   run the gate with those tools quiet) — `AGENTS.md` is the maintainer's;
   (b) extending F8's ratification to `snyk_sarif_filter.py:142`; (c) the
   `tests/test_exp002_*` tests are the heaviest file-churn tests in the suite and
   the trigger in both observations; whether their temporary trees could live
   outside the workspace is a design question, blocked by `AGENTS.md`'s mandated
   in-repo basetemp name; (d) the Parity Report, the PSR, the deviation ledger and
   the E5 erratum, which belong to S4.

### S3.10 Verdict and handoff

*Appended after the last review round.*

**Not authorized by S3:** merging PR #34, marking it ready for review,
`EXP-002-r1`, or releasing session `0164`. Session `0164` stays `BLOCKED`. S3 commits
locally only; nothing is pushed.
