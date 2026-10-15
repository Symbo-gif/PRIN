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
| F-08 | Low | **Partly confirmed.** `crossleg_consistency.py` parses each whole result file into memory although it only reads metadata and, on the publication legs, the `renderer` capture; the docstring and log say it "never opened" payloads. The whole-`environment` equality is a conservative superset and cannot assert absolute values — the per-record validator does that | **Wording corrected by a clarification entry in the log (§10)**; the tool is unchanged because its capture is bound to the committed file. See the clarification on what "not examined" means |
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

---

# Round 2 — the follow-up commit `e425971` (2026-10-13)

Same reviewers, same invocations and the same read-only rules; task files `agy-e3-round2-task.md` and
`devin-e3-round2-task.md`, verbatim stdout `agy-e3-round2-report.txt` and `devin-e3-round2-report.txt`, windows in
`*-round2-run.txt` (both 2026-10-13, 00:34:37Z → 00:42:41Z and → 00:41:38Z, exit 0). The diffs given to them are
`delta2-name-status.txt` and `delta2-records.diff`. I again scanned both reports for outcome content and found none.
Antigravity reviewed the new text and numbers; Devin reviewed validator revision 3 and its self-test. Antigravity found one
item, Devin eight (none High). Each was checked against the files before any action.

| # | Reviewer | Sev. | Verified? | Disposition |
|---|---|---|---|---|
| A2-1 | Antigravity | Low | **Confirmed.** The F-08 row above said the clarification is in log "§8"; it is in §10 | **Fixed** in this file |
| R2-01 | Devin | Medium | **Confirmed as a validator gap.** S1 tests the generated root and its ancestors only; F1's `is_symlink()` is false for a junction at `publication/` or `inputs/`; the inventories follow links | The validator is **not** revised again (a fourth revision for a condition that does not exist here). I checked the real tree instead: a reparse-point scan of the raw record root, the retained generated-output root and the evidence bundle, and of every ancestor of each, found **none** (`legs/reparse-point-scan.txt`) |
| R2-02 | Devin | Medium | **Confirmed.** Revision 3 replaced revision 2's "no stray file, no modified tracked file" repository-state checks (G1, G2) with a comparison of the frozen paths against `R`, because after the E3 commit the tree is legitimately no longer "`R` plus the record". The new check does not report dirty or untracked files elsewhere. `LOG_REL` is now unused | **Disclosed** here and in log §12. What admissibility depends on is the frozen set (product, driver, shared benchmark code, tests, tools, paper, parity, protocol, e2-review against `R`) and the record's own files; the full `git status` was recorded after every leg and the stricter revision-2 G1/G2 passed on every record at its leg. The unused constant is left, because the file's SHA-256 is cited elsewhere |
| R2-03 | Devin | Low | **Confirmed.** A relocated publication-mode copy validated without `--generated-root` emits no F-lines | Accepted limitation. On the real records F1–F4 do appear (87 checks against 81 and 80 for the non-publication modes) |
| R2-04 | Devin | Low | **Confirmed.** The driver can emit `font_cache.sha256: null` when the cache file is absent; revision 3 requires a digest | **Intentional.** Protocol §5.4 requires the font-cache digest to be logged, so a null digest is an incomplete required capture (§4.2 item 3). On this host the cache exists |
| R2-05 | Devin | Low | **Confirmed** (a wall-clock step of more than 1 s between the two timestamps would false-fail S5) | Accepted; rare. The largest observed difference is 0.0013 ms |
| R2-06 | Devin | Low | **Confirmed against the transcripts**: `flipped_byte_without_manifest_update` fires S3 (invalid JSON) in every mode, not B2; `case_family_changed` lists a dead `S4` expectation; `label_renamed` also trips C1; further mutations are possible | Accepted. B2's content path is exercised by `manifest_stale_digest`, `manifest_bytes_float` and `manifest_missing_entry`; the extra mutation ideas are noted and not added |
| R2-07 | Devin | Low | **Confirmed** (two `merge-base` calls without timeout or capture; an unvalidated value reaches argv) | Accepted: list argv, no shell, and a bad value fails closed |
| R2-08 | Devin | Low | **Confirmed** (`cmd /c mklink` with an operator-supplied scratch path; `rmtree` recursing through the junction) | Accepted: a local self-test run on my own scratch path, and the junction's target lies inside the scratch root |

Devin also re-verified that every round-1 fix (F-01…F-07) is present and non-vacuous, that the hard-coded key sets are
identical to the driver's emitted structures (the one mismatch is R2-04), that revision 3 judges no outcome, and that
the counts and SHA-256 values quoted in the log and in this file agree with the transcripts. Antigravity recomputed every
duration, sum and count in log §8–§11 and found them exact. No item changed an admissibility result, the protocol, the driver,
a registered input or a record.
