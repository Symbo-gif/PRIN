# Adjudication of the E3 cold reviews (session 0161)

Reviewers (read-only, no shell, no edits; task files and verbatim stdout in this directory):

| Reviewer | Invocation | Window (UTC, 2026-10-12) | Reviewed |
|---|---|---|---|
| Antigravity | `agy -p … --model gemini-3.8-flash-high --mode plan --output-format text` | 23:35:13 → 23:50:41, exit 0 | the log, the records, the statuses, the evidence numbers (`agy-e3-task.md`) |
| Devin | `devin --model swe-2-high --respect-workspace-trust false -p …` | 23:35:13 → 23:42:22, exit 0 | the per-record validation tooling and its captures (`devin-e3-task.md`) |

Both reviewed commit `89f21f5`. Both were told not to open the raw result files or the retained
publication roots and not to compare any digest across arms. I scanned both reports for outcome
content and for any statement about equality or difference of digests: there is none (every
"identical"/"differ" in them concerns tool behaviour or the log's own disclosures). Every finding
below was checked against the repository before any action was taken. No finding implicates the
protocol, the driver, the registered inputs or the data, so none stops the session.

## Antigravity — 0 findings

The report lists no defect and the areas it checked as sound. I spot-checked its citations: the log rows,
the cumulative-wall and byte sums, the validation counts and the gate lines it quotes are accurate. Two
citations are imprecise and are not relied upon: the protocol-freeze statement is at `log.md:204-207`,
not `355-358` as quoted, and `R05-cargo-test.log:1905` is one crate's "13 passed" line, not the 1,604
total (which I computed by summing every `test result:` line, and which equals the session-0160 gate's
figure). No action.

## Devin — 12 items, none High

| # | Sev. | Verified? | Disposition |
|---|---|---|---|
| F-01 | Medium | **Confirmed.** Validator revisions 1–2 checked `run.parent == raw_root` textually and tested links only on the run directory and its three entries; the driver's closure walks every ancestor (`_no_symlink_ancestors`, `exp002_driver.py:1359-1363`). The driver's own closure had passed on every record (exit 0). Devin's second point is also right: `Path.is_symlink()` is false for a junction, so the driver (which uses only `is_symlink`) has a blind spot for junction ancestors | **Fixed in validator rev3 (S1):** every ancestor of the run directory and of the generated-output root is tested for symlink *and* junction; a mutation that replaces `benchmarks` with a junction fails S1 in all five modes; all five records pass. The driver's junction blind spot is recorded for E4/E5; the driver is frozen and was not changed |
| F-02 | Medium | **Confirmed.** `(iterations, warmup, replicates) == (10, 0, 1)` admits `10.0` and `True`; the driver requires `type(...) is int` (`exp002_driver.py:1431-1436`) | **Fixed (S2).** Mutations with `10.0` and `true` fail S2; records pass |
| F-03 | Medium | **Confirmed**, and shared with the driver (`json.loads` keeps the last duplicate member) | **Fixed in the validator (S3):** strict loading rejects duplicate keys, `NaN`/`Infinity` and a byte-order mark for the sidecar, result and manifest; mutations fail S3; none of the 15 files has any of them. The driver was not changed |
| F-04 | Medium | **Confirmed.** Below the envelope the checks were subset tests (`CASE_KEYS <= set(c)`, `RENDERER_KEYS <= set(renderer)`) or absent (`identity`, `observations`, file records) | **Fixed (S4, S6):** exact key sets for the identity block, input records, each mode's observations, renderer and font cache, cases (C02 adds `K`, `alpha_radians`), publication file records (the 11 archived-table files add four `archived_*` keys) and the manifest. Mutations with an extra or missing key fail; all five records pass, which also confirms the key sets I derived from the driver are the real ones |
| F-05 | Low | **Confirmed** (offset of `recorded_at_utc` unchecked; `Infinity` accepted; elapsed vs timestamps never compared) | **Fixed (S5):** both offsets must be zero, `elapsed_seconds` finite and ≥ 0, and within 1 s of the timestamp difference. The five records agree to within 2 µs (largest difference 0.0013 ms, computed from the timestamp fields only) |
| F-06 | Low | **Confirmed** (manifest key set, `True == 1`, `215.0 == 215`, tail-only `out_dir`) | **Fixed:** exact manifest keys, `type(...) is int` for `schema_version` and `bytes` (B1, B2, S6), and `out_dir` must equal the absolute run directory (S6). All five records have exactly that |
| F-07 | Medium | **Confirmed.** The earlier self-tests covered only `api` and `conclusions` and none of the retention checks | **Fixed:** `mutation_test_rev3.py` runs 40–49 cases per mode, including the publication modes, the retention checks (F1–F4), duplicate keys, a junction ancestor, a wrong label and a stale manifest digest. Results: api 40/40, conclusions 41/41, reference 49/49, prin 49/49, repeatability 49/49 behave as expected (no case skipped) |
| F-08 | Low | **Partly confirmed.** `crossleg_consistency.py` parses each whole result file into memory although it only reads metadata and, on the publication legs, the `renderer` capture; the docstring and log say it "never opened" payloads. The whole-`environment` equality is a conservative superset and cannot assert absolute values — the per-record validator does that | **Wording corrected by a clarification entry in the log (§8)**; the tool is unchanged because its capture is bound to the committed file. See the clarification on what "not examined" means |
| F-09 | Low | **Confirmed** (staged files outside a `RUN-` directory are skipped; a manifest-only staged run passes the file-set test vacuously; a missing working file skips its comparison) | **No tool change.** Impact is nil here: every `RUN-` directory's three-file set is verified on disk by the validators (A3, B1) and the same check at `--head` compares committed blobs with the working tree. Recorded as a known limitation |
| F-10 | Low | **Confirmed** (`stat` follows links; `split()` breaks on spaces) | **No tool change.** The numbers it produced are reproduced by the driver's own closure measure; rev3 S1/A3 show no link exists in the tree and no measured name contains a space |
| F-11 | Low | **Confirmed in principle** (`$LASTEXITCODE` could be stale if the interpreter failed to launch) | **No change.** The interpreter launched on all five legs: each run directory was created and each driver wrote its own `COMPLETED` record. Recorded as a limitation |
| F-12 | Info | Acknowledged | The validator is session-bound. Rev3 now accepts any `HEAD` that descends from `R`, so it can be re-run from the E3 commit or later; the `C:\dev\PRIN` path is still pinned |

## Consequences

- Validator **revision 3** (SHA-256 `310e1c21a231cc72955a1942c6ae1bc8b6aad37d8d6efe54983e183384617c87`)
  re-validated all five records: 81, 80, 87, 87 and 87 checks, 0 failed. Revisions 1 and 2 and their
  transcripts remain as the first and second validation; nothing was overwritten.
- No record, no registered input and no protocol text changed. No finding changed an admissibility
  outcome.
- Snyk Code over the ten committed Python scripts (including the two new ones): 0 issues at the
  governed threshold (`G14c`).
