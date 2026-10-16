# EXP-002 D1 correction — S2 audit evidence

Status: **current** (S2 complete, 2026-10-15 UTC). This directory holds the
independent re-execution behind the S2 audit record, which is the `## S2 — audit
record (2026-10-15 UTC)` section of
[`DOCS/audits/2026-10-15-exp002-d1-correction-audit.md`](../../DOCS/audits/2026-10-15-exp002-d1-correction-audit.md).
The S1 evidence it audits is
[`EVIDENCE/exp002-d1-s1/`](../exp002-d1-s1/README.md), which this session read
but did **not** modify.

S2 was **read-only** with respect to source, tests, the S1 evidence and the S1
sections of the audit. Nothing was fixed in the audited code; every defect found
is a finding for S3. All seven instruments below are new in this directory, and
every text file is the verbatim output of the command its header names.

**Provenance common to every run:** branch
`hotfix/exp002-d1-figure-parity`, `HEAD =
8fd0ecc9949a607f2a7090fe39205f00bb0078c9`, equal to `origin` and to the `PRIN`
remote; working tree clean (0 tracked changes) at audit start; branch point
`fd8854ed`. Host `MINGW64_NT-10.0-26300 3.6.5-22c95533.x86_64`, Python
`3.14.0`, pytest `9.1.1`, Matplotlib `3.11.1`, NumPy `2.5.1`, project venv,
Agg backend. Run from the repository root. Windows x86_64 only — Linux and
macOS were **not** tested (Plan amendment #48 item 4).

Scratch artefacts (the re-run's decomposition JSON, the coverage JSON, and
every runner script) were written **outside** the repository, to
`C:\Users\there\prin-s2-scratch`, so no scratch file entered the tree and the
committed S1 artefacts were never at risk of being overwritten.

## Instruments

Each is `ruff check`, `ruff format --check`, `mypy --strict` and `bandit` clean,
and is the committed generator for the output file beside it.

| File | What it establishes |
|---|---|
| [`ast_spec_validation.py`](ast_spec_validation.py) | **Brief item 2, statically.** Cross-validates all 34 registered divergences against the *source text* of both modules, without executing matplotlib. **Part B:** each specification names an argument the frozen reference really carries, at the call indices it restricts — the check that S1's runtime transforms are not self-confirming. **Part C:** the fixed port carries the reference's value for each specification, and no mathtext rewrite survives. **Part D:** the `\N{...}` escape claim — the port's *decoded* strings equal the reference's literal Unicode strings while its source stays ASCII (which is what satisfies `ruff` `RUF001`). Resolves constants, lists, f-strings (by literal parts) and simple local name bindings; its docstring records the two things a static count cannot see. |
| [`artist_level_equivalence.py`](artist_level_equivalence.py) | **Brief item 2, "no divergence alters a plotted value".** Renders all 14 stems from both modules, intercepts each `Figure` at `savefig`, and compares the full artist inventory — `Line2D` x/y data (SHA-256 over the `float64` buffer plus shape), linewidth, markersize, marker, linestyle, alpha, zorder, colour, label; `Collection` offsets and styling; `Patch` vertices and styling; `Text` string, position, alignment, size, rotation, colour; `Axes` limits, scales, title, labels, ticks, tick labels, legend. Also counts drawing calls made directly by each generator, which is what separates a real argument divergence from harmless restructuring. |
| [`decomposition_rerun_check.py`](decomposition_rerun_check.py) | **Brief item 2, "re-run the decomposition".** Compares an independent re-run of S1's generator with the committed postfix artefact field by field, treating `generated_utc` and `git_head` as the only expected differences; prints the prefix/postfix red → green transition, the full 21-file no-regression set and 18-file changed set (**brief item 3**), and the retained-E3-root verification. Its input path goes through `guarded_input_path` (see below). |
| [`both_policies_post_fix.py`](both_policies_post_fix.py) | **S1.10 item 1, independently re-derived.** Renders both arms once on the corrected tree and computes raw, approved-§5.4 and §11.3-sensitivity digests for all 39 files, then **classifies** every sensitivity-policy residual rather than counting it: line terminators for `.tex`, Info key set for `.pdf`, critical chunks for `.png`. Writes only to a temporary directory. |
| [`fast_gate_divergence_coverage.py`](fast_gate_divergence_coverage.py) | **A3.** The parity gate is marked `parity` + `slow`, so the default fast gate never runs it. This measures how much of the 34-divergence population the nine `tests/test_publication_figure_arguments.py` tests actually pin, split by byte-materiality, per test function. |
| [`changed_line_coverage.py`](changed_line_coverage.py) | **A3's ≥95 % changed-code gate.** Intersects `git diff -U0 fd8854ed` added lines with a path-form coverage JSON report. Written because `tools/coverage_changed_lines.py` unions **Rust** `cargo-llvm-cov` lcov runs and does not read Python coverage data, and because the `--cov=prin` module form fails on this host (**DV-033**). Its input path goes through `guarded_input_path` (see below). |
| [`snyk_sarif_filter.py`](snyk_sarif_filter.py) | **Brief item 5 / finding `EXP002D1-S2-F8`.** Filters a `snyk code test --sarif-file-output` report into the two buckets this audit governs — the four changed first-party files and the six S2 instruments — and separates git-tracked findings from the gitignored on-disk agent-worktree copies that `snyk code test .` also scans. Its docstring records two SARIF properties established by inspection, not assumption: Snyk Code sets `result.level="note"` for **every** finding and stores **no severity** anywhere in the SARIF, so the authoritative severity breakdown is the CLI's own `Test Summary` block; and a repo-wide total is therefore not a census of tracked files. |

### The input-path guard in the two instruments that take a path argument

`decomposition_rerun_check.py` and `changed_line_coverage.py` each accept a
caller-supplied path. Snyk Code reports that as `python/PT` (CWE-23, **Low**) in
both, and it was **remediated rather than suppressed**, on the repository's own
audited `PR23-F1` pattern (`tools/reproduce.py::_reject_symlink` /
`_reject_non_regular`). `guarded_input_path()` rejects a `..` component, refuses
a symbolic link **without following it**, refuses anything that is not a regular
file, then resolves the path and confines it to an explicit allowlist — the
repository root, the platform temp root, and `PRIN_S2_SCRATCH` when set — so a
symlinked *parent* directory is refused too. The resolved path and its SHA-256
are printed into the evidence, tying each artefact to the exact bytes measured.

This is an **evidence-integrity** control, not only a confidentiality one: these
are verification tools, so a symlinked input would be compared while the
evidence named a different file — precisely `PR23-F1`'s "content verified, path
provenance not" failure mode.

Snyk still reports both findings after two remediation iterations, with its
dataflow pointing *inside* the guard at `candidate = Path(raw)`; its `python/PT`
model does not treat those checks as sanitizers. The residual is recorded as
audit finding **`EXP002D1-S2-F8`** with a full threat assessment in
[`snyk-low-findings-threat-assessment.md`](snyk-low-findings-threat-assessment.md).
The applicable Coding Standards §6.2 gate is "0 medium+ findings" and repo-wide
at `medium` is **0**, so the gate is met.

## Verification outputs

| File | What it is |
|---|---|
| [`prefix-gate-d90eeab-module.txt`](prefix-gate-d90eeab-module.txt) | **Brief item 1 — the reproduction came first.** `python/prin/reporting/figure_generation.py` restored from `d90eeabb` (`sha256 e0f59253…d533`, equal to S1's recorded prefix `port_module_sha256`), then `parity/test_parity_publication.py` → **18 failed, 75 passed**, exit 1, on exactly the E3 population; and `tests/test_publication_figure_arguments.py` → **9 failed**, exit 1. Header records the module digest and `git status` proving only that one file was modified. |
| [`postfix-gate-8fd0ecc9.txt`](postfix-gate-8fd0ecc9.txt) | **Brief item 1, green half.** After `git restore`, both files together → **102 passed**, exit 0, with the module back at `sha256 b41dfc13…c048` and 0 tracked changes. |
| [`decomposition-postfix-s2-rerun.txt`](decomposition-postfix-s2-rerun.txt) | **Brief item 2.** S1's generator re-run with `--label postfix` and `--out` pointing outside the repository. Exit 0: `port_vs_reference_differing_count 0`, 34 registered, 26 material / 8 immaterial, completeness `true`, `unexplained_stems []`, reference reproduces E3's arm. |
| [`decomposition-rerun-vs-committed.txt`](decomposition-rerun-vs-committed.txt) | **Brief items 2 and 3.** That re-run against the committed artefacts: every field `SAME` except `generated_utc` and `git_head`; the red → green transition; the full 21 raw-identical and 18 changed file lists; `two_process_raw_identical: true` (H4); all three retained E3 legs 39/39 raw and normalized with manifests matching. |
| [`ast-spec-validation.txt`](ast-spec-validation.txt) | **Brief item 2.** Part B **34/34 OK, 0 failures**; Part C **34/34 restored, 0 failures** (one static-count observation, `D9.1 ref=4 port=2`, explained as loop multiplicity); Part D escape claim OK. |
| [`artist-level-equivalence.txt`](artist-level-equivalence.txt) | **Brief item 2.** **14/14 stems EQUAL** on the full artist inventory, so no plotted value, limit, tick, label, colour, alpha or z-order differs. Reference digest `575eca5a…1520` equals `REFERENCE_PINS`. The only differences are drawing-call multisets (`set_xlabel`/`set_ylabel` vs `ax.set(...)`). |
| [`both-policies-post-fix.txt`](both-policies-post-fix.txt) | **S1.10 item 1.** Approved §5.4 **39/39 equal**; §11.3 sensitivity **14/39 equal, 25 differ**; **0 unclassified residuals** — 14 PDFs Info-key-set-only (reference 3 keys, PRIN 4 fixed keys) and 11 `.tex` line-terminators-only (reference 13–25 CRLF per table, PRIN 0). Per-file detail included. |
| [`fast-gate-divergence-coverage.txt`](fast-gate-divergence-coverage.txt) | **A3.** The nine fast-gate tests cite **34/34** registered divergences — all 26 byte-material and all 8 byte-immaterial — with no unknown IDs, per test function. Also records that the module docstring understates this (finding `EXP002D1-S2-F5`). |
| [`verify-manifest-five-runs.txt`](verify-manifest-five-runs.txt) | **Brief item 4.** `tools.reproduce.verify_manifest` **PASS on all five** `benchmarks/results/EXP-002/RUN-*` directories, plus the frozen 172-input `paper/artefact_manifest.json` (recomputed `300cdc09…2cce5`, equal to `INPUT_MANIFEST_SHA`). Lists the retained roots to show they were read, not modified. |
| [`e4-analysis-clean-worktree-reproduction.txt`](e4-analysis-clean-worktree-reproduction.txt) | **Brief item 4 — the check S1 did not re-run.** A detached worktree of `HEAD` **outside** the repository ran the frozen `analysis/exp002_e4_analysis.py` (digest `7a400aa6…4e4`, last touched `3731fc2`) with `-I`: exit 0, all **seven** outputs byte-identical to the retained copies, and `report-manifest.json` regenerated as `6b15dcc1…68781`, equal to the committed file. Worktree removed; main tree clean; retained roots intact. |
| [`snyk-code.txt`](snyk-code.txt) | **Brief item 5, first attempt.** Both legs as originally run. **CLI leg BLOCKED**: `snyk code test . --severity-threshold=low --sarif-file-output=…` → `SNYK-0005`, `401 Unauthorized`, exit 2, **no SARIF**. **MCP leg COMPLETED** (Coding Standards §6.4 permits it): 0 findings at `low` in each of the four changed files, 0 repo-wide at `medium`, with the scanned files' SHA-256s recorded. Superseded for the CLI leg by `snyk-code-cli.txt` once the maintainer re-authenticated. |
| [`snyk-code-cli.txt`](snyk-code-cli.txt) | **Brief item 5, CLI leg completed** after the maintainer re-authenticated the CLI (`snyk whoami` → `Symbo-gif`). `snyk code test . --severity-threshold=low --sarif-file-output=…`, snyk `1.1306.2`, exit 1 (findings reported — not a scan failure), SARIF written (`sha256 ebc92c86…`, 530,562 B). CLI Test Summary: **77 issues — 0 HIGH, 0 MEDIUM, 77 LOW**, so the §6.2 gate ("0 medium+") is **met**. Filtered by `snyk_sarif_filter.py`: the **four changed first-party files → 0 findings**, confirming S1's claim through the route the brief specified; the **six S2 instruments → 2 findings** (`python/PT`, `changed_line_coverage.py:98`, `decomposition_rerun_check.py:92`), independently corroborating the MCP result behind `EXP002D1-S2-F8`. Repo-wide 77 raw / **44 in git-tracked paths**, the other 33 being gitignored `.claude`/`.kilo` worktree copies of files already counted. S1's recorded "75 LOW" plus the 2 findings in the instruments S2 added accounts for the 77. Also records why the first inline filter's severity line was unusable. |
| [`pytest-suites.txt`](pytest-suites.txt) | **Brief item g / A9.** The required legs, sequential, with per-leg commands, UTC start/end, elapsed and exit codes. **P1 fast suite exit 0** — `4038 passed, 178 skipped, 55 deselected (0:51:38)`, a **clean single pass**. **P2 full suite exit 1** — `1 failed, 6324 passed, 184 skipped (2:03:35)`, the failure being `test_notebook_executes_end_to_end[02_clevr_n_binding.ipynb]`, `nbclient` `CellTimeoutError` after the 900 s per-cell limit (finding `EXP002D1-S2-F2`). **P3** targeted coverage exit 0. **P4** exit 1 in 0 s — an auditor error, `tools/coverage_changed_lines.py` invoked as a Python coverage tool when it is a Rust lcov tool; superseded by `static-gate-reruns.txt` R08. Includes both faulthandler dumps verbatim. |
| [`stall-diagnosis-clevr6-no-nan.txt`](stall-diagnosis-clevr6-no-nan.txt) | **Testing Standards §7 item 3.** The retained stall diagnostic for the first faulthandler dump: two timestamped observations 151 s apart (same PID alive, CPU **+35.8 s**, working set **+338 MB**, stack in `prin/nn/_bridge.py:108 backward`), plus the node's expected duration from S1's own `--durations=20` (`1086.16 s`, ~3.6× the 300 s threshold). Conclusion: **not a stall**; nothing killed, re-run, deselected or weakened. |
| [`static-gate.txt`](static-gate.txt) | **A5/A6/A7/A9.** The static, quality, security, documentation and cargo legs L01–L21 with exit codes: `ruff`, `mypy --strict` ×3, `interrogate` (**97.6 %**), `bandit` ×2, the four governance checkers, `cargo fmt`/`clippy -D warnings`/`test`, a from-scratch Sphinx `-W --keep-going` build, `gitleaks` full history (**738 commits, no leaks**) and `--staged`, and the empty EXP-002/CI/dependency immutability diff. Five legs exited non-zero here; each is diagnosed in `static-gate-reruns.txt`. |
| [`static-gate-reruns.txt`](static-gate-reruns.txt) | **A5/A6/A3.** The corrected re-runs R01–R08, **all exit 0**: `ruff check`/`format --check` over every root including both EVIDENCE dirs, `bandit` over both instrument dirs (**0 issues**), `check_deviation_ledger.py` with report paths (the phase-2 `039 040` form was an auditor error), `cargo test --workspace` (the phase-2 `os error 32` `ERROR_SHARING_VIOLATION` was the documented Windows contention class, and it passed on re-run in 56 s without `-j 1`), the targeted coverage re-run, and the **changed-line coverage analysis: 11/11 changed executable lines = 100 %**, whole-file 99.41 % (missed 191, 196). |
| [`targeted-coverage-phase2-attempt.txt`](targeted-coverage-phase2-attempt.txt) | **Superseded, retained for honesty.** The phase-2 coverage leg: its `pytest --cov=python/prin/reporting --cov-report=term-missing` half is valid and shows `figure_generation.py` at 99 % missing 191, 196, but its analysis half **aborted** because an MSYS `/c/...` path was passed to a native Windows Python, so the JSON was never written (an auditor error, not a repository defect). Superseded by `static-gate-reruns.txt` R07/R08 and by `changed-line-coverage.txt`. |
| [`changed-line-coverage.txt`](changed-line-coverage.txt) | **A3's ≥95 % gate, authoritative.** `changed_line_coverage.py` run against the R07 coverage JSON: whole-file **99.41 %** (340 statements, missed 191 and 196), and of the 82 lines the diff added, **11 are executable and 11 executed — 100.00 %**, 0 uncovered. Records the resolved-and-confined input path and its SHA-256. Regenerated after the CWE-23 guard was added, so the committed output matches the committed instrument. |
| [`path-guard-negative-tests.txt`](path-guard-negative-tests.txt) | **Proof the CWE-23 guard is not vacuous.** Exercises `guarded_input_path` in both instruments: a path outside every allowed root, a directory, a `..` traversal component, and a **real symbolic link** to a live artefact are all **REFUSED**; a legitimate in-repo artefact and the declared `PRIN_S2_SCRATCH` file are **ACCEPTED**. `guard negative-test failures: 0`, exit 0. |
| [`snyk-low-findings-threat-assessment.md`](snyk-low-findings-threat-assessment.md) | **Coding Standards §6.2/§6.4 record for finding `EXP002D1-S2-F8`.** Names the two residual LOW `python/PT` findings, the affected API and data flow, the exploit prerequisites (argv control implies existing code execution as the auditor — no privilege boundary crossed), both remediation iterations, the negative-test proof, the compensating controls, and the ACCEPTED-WITH-ASSESSMENT disposition flagged for maintainer ratification. Nothing was added to `.snyk`; no ignore or severity exclusion was created. |
| [`phase2-sequencer.txt`](phase2-sequencer.txt) | The sequencing record: the wait for the phase-1 pytest legs to complete before any cargo or second pytest leg started (`AGENTS.md` forbids running them concurrently on this host), the phase-1 leg results, and the order the remaining legs ran in. |
| [`post-record-gate.txt`](post-record-gate.txt) | **Two dated runs of the doc-affecting legs, after S2's own Markdown edits.** *First run* (G01–G07): the four governance checkers, a from-scratch Sphinx `-W --keep-going` build, and instrument lint. *Second run* (H01–H12), after the §S2.13 addendum, finding `EXP002D1-S2-F8`, the CWE-23 guard and the register/index tally updates: `ruff check`/`format --check` over every root, `mypy --strict` over all six instruments, `bandit` over both instrument dirs, the four governance checkers, Sphinx from a deleted `_build`, and **both immutability diffs** — H11 (EXP-002 record / `.github/` / dependency manifests) and H12 (S1 evidence and all of `python/`, `tests/`, `parity/`, `benchmarks/`, `tools/`) — each empty, confirming S2 changed no source, test or S1 evidence. All legs exit 0 in both runs. |

## Results in one place

| Question | Answer | Where |
|---|---|---|
| Did the reproduction come first, and fail on exactly the 18 E3 files? | **Yes** — 18 failed / 75 passed, and 9 failed, on the restored pre-fix module; 102 passed after | `prefix-gate-d90eeab-module.txt`, `postfix-gate-8fd0ecc9.txt` |
| Does the decomposition reproduce? | **Yes** — every field `SAME` but `generated_utc`/`git_head`; 0/39 differ, 0 unexplained | `decomposition-postfix-s2-rerun.txt`, `decomposition-rerun-vs-committed.txt` |
| Do the 34 specifications match the reference source call for call? | **Yes** — Part B 34/34, 0 failures; Part C 34/34 restored | `ast-spec-validation.txt` |
| Does any divergence alter a plotted value? | **No** — 14/14 stems EQUAL on the full artist inventory | `artist-level-equivalence.txt` |
| Are the 11 tables, the 5 matching figures and H4 intact? | **Yes** — 21 raw-identical to E3, exactly 18 changed, `two_process_raw_identical: true` | `decomposition-rerun-vs-committed.txt`, `pytest-suites.txt` |
| Is EXP-002's record untouched, and does E4 still reproduce? | **Yes** — empty diffs; `verify_manifest` 5/5 PASS + 172 inputs; seven outputs and `report-manifest.json` `6b15dcc1…68781` byte-for-byte | `verify-manifest-five-runs.txt`, `e4-analysis-clean-worktree-reproduction.txt` |
| Is the §6 Snyk evidence real? | **Yes, on both routes.** MCP: 0 findings in the four changed files, 0 repo-wide at `medium`. CLI (after the maintainer re-authenticated): **0 findings in the same four files**, Test Summary **0 HIGH / 0 MEDIUM / 77 LOW**, so the §6.2 "0 medium+" gate is met. The 2 residual LOW `python/PT` findings are in S2's own instruments (`EXP002D1-S2-F8`, ratified). The original CLI attempt is retained as **BLOCKED**, never as passed | `snyk-code.txt`, `snyk-code-cli.txt` |
| Do both registered H3 policies agree post-fix? | **No** — approved 39/39 equal, sensitivity 14/39 equal, all 25 residuals writer/host properties, 0 unclassified | `both-policies-post-fix.txt` |
| Is the fast suite green in a single pass? | **Yes** — 4038 passed, 0 failed, exit 0 | `pytest-suites.txt` |
| Is the full suite green? | **No** — exit 1, one pre-existing notebook 900 s cell timeout (`EXP002D1-S2-F2`) | `pytest-suites.txt` |
| Is changed-code coverage ≥95 %? | **Yes** — 11/11 changed executable lines = 100 %; whole-file 99.41 % | `static-gate-reruns.txt` |

## Regenerating

From the repository root with the project venv. The five analysis instruments
are read-only and take seconds to a minute each; the two rendering instruments
render both arms and take one to two minutes.

```bash
.venv/Scripts/python EVIDENCE/exp002-d1-s2/ast_spec_validation.py
.venv/Scripts/python EVIDENCE/exp002-d1-s2/artist_level_equivalence.py
.venv/Scripts/python EVIDENCE/exp002-d1-s2/both_policies_post_fix.py
.venv/Scripts/python EVIDENCE/exp002-d1-s2/fast_gate_divergence_coverage.py

# The two path-taking instruments confine their input to the repository root,
# the platform temp root, and PRIN_S2_SCRATCH when set. Declare the scratch root
# first, or the guard refuses the out-of-tree artefact (as it is designed to).
export PRIN_S2_SCRATCH='C:\Users\there\prin-s2-scratch'

# the decomposition re-run: write the JSON OUTSIDE the repository, then compare
.venv/Scripts/python EVIDENCE/exp002-d1-s1/root_cause_decomposition.py \
    --label postfix --out /c/Users/there/prin-s2-scratch/root-cause-decomposition-postfix-s2.json
.venv/Scripts/python EVIDENCE/exp002-d1-s2/decomposition_rerun_check.py \
    /c/Users/there/prin-s2-scratch/root-cause-decomposition-postfix-s2.json

# changed-line coverage (path form; the --cov=prin module form fails, DV-033)
.venv/Scripts/python -m pytest tests/test_publication_figure_arguments.py \
    tests/test_publication_generation.py parity/test_parity_publication.py \
    --cov=python/prin/reporting --cov-report=term-missing \
    --cov-report=json:C:/Users/there/prin-s2-scratch/coverage-reporting.json \
    --basetemp=.pytest_basetemp -o faulthandler_timeout=300
.venv/Scripts/python EVIDENCE/exp002-d1-s2/changed_line_coverage.py \
    C:/Users/there/prin-s2-scratch/coverage-reporting.json fd8854ed \
    python/prin/reporting/figure_generation.py
```

Alternatively put the scratch artefacts under the platform temp root, which is
allowed by default, and omit `PRIN_S2_SCRATCH`.

The pre-fix reproduction requires temporarily restoring the pre-fix module and
restoring it afterwards; the exact commands are in the header of
`prefix-gate-d90eeab-module.txt`:

```bash
git restore --source d90eeabb -- python/prin/reporting/figure_generation.py
# ... run the two test files ...
git restore python/prin/reporting/figure_generation.py
```

Two Windows-specific notes for reproducing the suite legs. Prepend
`C:\Program Files\Git\bin` **process-locally** so `bash` resolves to Git Bash
rather than the WSL relay (`AGENTS.md`); from PowerShell `bash` resolves to the
WSL launcher. Pass coverage and other tool output paths in **Windows** form
(`C:/...`), not MSYS form (`/c/...`) — a native Windows Python does not
translate the latter, which is why `targeted-coverage-phase2-attempt.txt`
aborted. Keep the exact `.pytest_basetemp` name, run pytest and cargo
sequentially, and supervise per Testing Standards §7: a faulthandler dump alone
is not a hang, and an incomplete run is never a pass.
