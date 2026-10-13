# Adjudication of the session-0162 cold reviews

## Phase A — the analysis module and its tests, before any real run

Reviewers (read-only, no shell, no edits). Task files, verbatim stdout and run windows are in this
directory.

| Round | Reviewer | Invocation | Window (UTC, 2026-10-13) | Reviewed |
|---|---|---|---|---|
| 1 | Antigravity | `agy -p … --model gemini-3.8-flash-high --mode plan --output-format text` | 11:09:38 → 11:22:52, exit 0 | module + tests (`phaseA-task.md`) |
| 1 | Devin | `devin --model swe-2-high --respect-workspace-trust false -p …` | 11:09:37 → 11:25:51, exit 0 | module + tests (`phaseA-task.md`) |
| 2 | Antigravity | as round 1 | 11:47:25 → 11:58:49, exit 0 | the fixes (`phaseA-round2-task.md`, `phaseA-round2-*.diff`) |
| 2 | Devin, attempt 1 | as round 1 | 11:47:27 → 11:49:35, exit 0 | stopped early: "rejected a tool call that requires confirmation" (output kept: `devin-phaseA-round2-attempt1-*`) |
| 2 | Devin, attempt 2 | as round 1, prompt names every file path so no directory listing is needed | 11:55:02 → 12:08:08, exit 0 | the fixes |

**HARD RULE.** Both reviewers were forbidden to open `benchmarks/results/EXP-002/RUN-*`, anything under
`DOCS/test_and_benchmark_results/`, anything under `DOCS/archive and reference from PRINet 3.0/` (its
JSON inputs decide H2), the E3 validation transcripts and PR #33 comments. Both reports state compliance;
Devin also read `paper/artefact_manifest.json` (an input inventory, no outcome). I scanned all four
reports for outcome content and found none. No real record had been analysed when the reviews ran.

Every item below was checked against the code before any action.

### Round 1

Antigravity: no defect.

| # | Sev. | Verified? | Disposition |
|---|---|---|---|
| F1 | Medium | **Confirmed** (tests only). The fast path reused the session context when only `source_sha` and the input-manifest digest matched; a test that edited the protocol or the reference API would have run against stale globals | **Fixed:** the guard compares every registration field except the run index |
| F2 | Low | **Confirmed in fact, declined in code.** Only `*.json` entries of the frozen results directory are inventoried | This is the registered inventory rule of `tools.reproduce.verify_manifest`, which the driver used at E3; a non-JSON file cannot be an input. The docstring now says so |
| F3 | Low | **Confirmed.** `frozen_missing`/`frozen_extra` were the only driver-computed identity not re-derived | **Fixed:** `_public_api.py` and `_deprecation.py` are read at `R`, must carry their pre-registration §1.1 digests (`dd5745ab…`, `132e86e9…`, both verified equal at `R`), `RC1_PUBLIC_API` is parsed as a literal tuple, and the record's sets must equal `sorted(FROZEN − observed)` / `sorted(observed − FROZEN)` (the semantics of `verify_api_surface`); a disagreement makes the record inadmissible. Tests added |
| F4 | Low | **Confirmed.** Owner-matrix row 4 dropped a clause | **Fixed** verbatim; a test now compares all seven rows with protocol §5.3 |
| F5 | Low | **Confirmed.** `ast`/decode/listing/read errors could escape as raw exceptions | **Fixed** (wrapped into `AnalysisError`/`RecordError`); tests added |
| F6 | Low | **Confirmed.** Dates were shape-checked only | **Fixed:** approval date and run-name stamps are calendar-validated; test added |
| F7 | Low | **Confirmed.** Ambient `GIT_DIR` etc. would redirect the git queries | **Fixed:** `GIT_*` variables are removed for every git query; test added |
| F8 | Low | **Confirmed** (dead constants) | **Fixed:** the registered case key sets drive the exact-key check |

### Round 2 (the fixes)

Both reviewers confirmed F1 and F3–F8 correct, with tests that fail without them. Neither found a new
false pass.

| # | Reviewer | Sev. | Verified? | Disposition |
|---|---|---|---|---|
| R2-F1 / R2-F4 | Antigravity / Devin | Low | **Confirmed.** No test distinguished the stronger fast-path guard from the old one | **Fixed:** a test edits the working reference `__all__` (still 172 unique names) and asserts that the helper falls back to full verification (H1 `INCONCLUSIVE`, record inconsistent with the re-derived population) |
| R2-F1 | Devin | Low | **Not reproduced.** `GIT_` matched case-sensitively | On Windows, `os.environ` upper-cases every key (checked: setting `git_probe_x` yields the key `GIT_PROBE_X`), and git reads only upper-case names on POSIX. No change |
| R2-F2 | Devin | Low | **Confirmed.** Three global listing/read paths could raise a bare `OSError` | **Fixed** (wrapped into `AnalysisError`); tests added for the two listings |
| R2-F3 | Devin | Low | **Checked; declined.** Whether the driver stored the frozen sets sorted | `benchmarks/campaign/exp002_driver.py` lines 333–334 (frozen since E2): `"frozen_missing": sorted(missing)`, `"frozen_extra": sorted(extra)`. If it were not so, the check would fail closed (inadmissible), never yield a wrong verdict |

After the fixes: `ruff check`, source-only `ruff format --check`, `mypy --strict` and `bandit` clean;
176 synthetic tests pass, 99 % branch coverage of the module; Snyk Code 0 issues at the governed
threshold on the exact committed bytes (`gate/G14*`).

## Post-run self-audit (Phase C) — outputs, records and documentation

Same reviewers, read-only; this time they **could** read the five run records and the seven outputs, but
not the retained publication roots (`DOCS/test_and_benchmark_results/EXP-002/RUN-*`) or PR #33 comments
(`selfaudit-task.md`).

| Reviewer | Window (UTC, 2026-10-13) | Result |
|---|---|---|
| Antigravity | 16:31:03 → 16:44:33, exit 0 | "0 findings" — **given little weight**: the report contains factual errors (it cites files at wrong paths such as `DOCS/test_and_benchmark_results/EXP-002/analysis.md`, names the wrong failing tests for G13, lists §5.3 owner rows that do not exist, and states that D1 blocks E5, whereas E5 completes and then blocks its successor). None of these errors is in the audited documents |
| Devin, attempt 1 | 16:31:00 → 16:39:26, exit 0 | stopped early on a tool that needed confirmation (`devin-selfaudit-attempt1-*`) |
| Devin, attempt 2 | 16:47:31 → 16:52:45, exit 0 | every number recounted from the records and the CSVs and found consistent; one Low and two informational items |

| # | Sev. | Verified? | Disposition |
|---|---|---|---|
| F-1 | Low | **Confirmed.** In the generated `expected-vs-observed.md` (and `summary.json`'s `tables_equal_to_archived`), "tables equal to archived 11/11" counts the PRIN arm; under the sensitivity policy all 11 reference tables are inconsistent with the archived tables, and that is reported in a separate field | A label in a module output, not a decision-logic defect. The module is not changed after its first real run; `analysis.md` and the README handoff now state that the label counts the PRIN arm |
| F-2 | Info | **Confirmed.** The 0162/0163 briefs' generic text asks for effect sizes and CIs | Protocol §7 makes them not applicable; noted in the E4-to-E5 handoff. Briefs are prospective contracts and are not rewritten |
| F-3 | Info | The DV-040 row was excluded from Devin's reading list (a single very long line) | Checked by me: `tools/check_dv_register_gates.py` passes after the edit (44 rows) |

I also recounted independently from the raw records (separate code, not the module): H1 175 rows, 175
resolved, 172 callable and 3 constants (`CONTROL_DIM`, `STATE_DIM`, `__version__`), 172/172 legacy names
owned, 175 unique observed names, empty frozen sets; H2 62 cases, family counts 5/42/4/5/6, all agreeing
(16 of the 42 C02 records are negative classifications); H3 18 approved-policy and 34 sensitivity-policy
differences, 11/11 PRIN tables equal to archived; H4 0 raw differences; the CSVs have 175, 62 and 39 data
rows; `report-manifest.json` lists 7 analysis outputs, 39 publication files and 5 inputs. No finding
implicated the analysis logic, the protocol or the data.
