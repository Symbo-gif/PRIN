# PR #34 — adjudication of the Perplexity Deep-Research review

The maintainer posted an independent **Perplexity Deep-Research** review of PR #34
and asked for its findings to be independently validated before anything is acted
on. Every checkable claim was **measured** against the real hosted logs, the real
PR diff and the real repository configuration — not accepted on the reviewer's
authority. The review is reproduced verbatim in
[`perplexity-review-verbatim.txt`](perplexity-review-verbatim.txt).

The reviewer states its own limitation plainly: *"A fully independent local
execution was not possible in my isolated checkout without first building the PyO3
extension and installing the frozen `prinet` reference."* So its findings are
inferences from workflow metadata. Two of them are wrong in consequence of that,
one of them materially.

**Summary: 4 CONFIRMED, 1 CONFIRMED-in-part, 1 REFUTED (fabricated), 2 recorded
as recommendations without independent verification. One CONFIRMED finding
(`EXP002D1-S4-F2`) was fixed in this session; the rest are out of this bounded
correction's scope and are recorded, not actioned.**

## Claim-by-claim

| # | Claim (severity as posted) | Measured verdict | Evidence |
|---|---|---|---|
| 1 | **High** — the Rust `audit` failure is a real dependency gate failure matching DV-045, not runner flakiness; update the transitive graph, do not blanket-ignore | **CONFIRMED (diagnosis).** The `audit` job log reads `Scanning Cargo.lock for vulnerabilities (621 crate dependencies)`, `error: 9 vulnerabilities found!`, `warning: 4 allowed warnings found`. The RUSTSEC ids present are `2026-0338`..`0342` (`quinn-proto` ×5) and `2026-0346`..`0349` (`rustls` ×4) = **exactly 9 = the DV-045 set**; `2024-0436` (`paste`, DV-008) and `2025-0141` (`bincode`, DV-017) are among the 4 allowed warnings. **Remediation feasibility also measured:** `cargo update --dry-run -p quinn-proto --precise 0.11.18` → exit 0, `Updating quinn-proto v0.11.16 -> v0.11.18`; `-p rustls --precise 0.23.46` → exit 0. `cargo tree -i quinn-proto` → *"nothing to print"*, confirming DV-045's unreachable-optional-entry claim; `rustls` reaches the graph via `hyper-rustls` ← `reqwest` ← `tracel-llvm-bundler` ← `tracel-mlir-rs-macros`. | [`pre-decision-investigations.txt`](pre-decision-investigations.txt) |
| 2 | **High** — parity and nightly full-suite need exact failing-node triage before merge; the check summary exposes only exit code 1 | **CONFIRMED as a need, and discharged here.** The logs were retrieved: **both** jobs fail on exactly the same **28** parametrizations of `test_reference_arm_reproduces_e3_reference_arm` — **14 figures × 2 formats**. `nightly`: `28 failed, 6185 passed, 302 skipped in 622.95s`; `parity`: `28 failed, 2208 passed, 2 skipped in 48.46s`. All **11 `.tex` tables pass**, and every other test in the file passes — including `test_prin_matches_reference_under_registered_comparison` **39/39**, the registered H3 rule. Root cause and fix: see `EXP002D1-S4-F2` below. | [`parity-attempt2-failures.txt`](parity-attempt2-failures.txt), [`failure-identity-and-schema.txt`](failure-identity-and-schema.txt) |
| 2b | *"this PR raises one notebook base timeout from 180s to 600s"* | **REFUTED — fabricated.** The real diff of `tests/test_notebooks.py` is `- timeout=900` → `+ timeout=NOTEBOOK_CELL_TIMEOUT_SECONDS[name]`, with bounds **2700 / 10800 / 1800 / 1800** and `BOUND_ROUNDING_SECONDS = 900`. **No 180 s or 600 s constant exists anywhere in this PR's diff of that file.** The only `180`/`600` tokens in the whole diff are fuzz-test parametrizations (`test_prin_matches_prinet_within_horizon[180]`, `[600]`) and unrelated prose inside committed evidence JSON. Independently: **all four notebooks PASSED on Linux**. Acting on this claim would have sent the investigation to a file and a mechanism that do not exist. | [`adjudication-evidence.txt`](adjudication-evidence.txt) §D |
| 2c | *"determine whether the nightly failure is the same parity node or a notebook timeout"* | **Resolved: the same parity node.** No `WinError`, no `CellTimeoutError`, no throughput-ratio failure appears anywhere in the nightly log. So **neither of observation O-1's two registered failure classes occurred on the hosted run** — which is why O-1's hosted corroboration was blocked by this defect rather than by contention. | [`failure-identity-and-schema.txt`](failure-identity-and-schema.txt) §1 |
| 3 | **High** — the benchmark gate measured both arms then failed on a >10 % regression; treat shared-runner results as advisory, add a two-stage policy, bootstrap CI / Cliff's delta, `concurrency` cancellation | **CONFIRMED in part (facts), recommendation OUT OF SCOPE.** Measured: **exactly one** gating breach — `criterion/engine_step/step_parallel/16384: 4.185e+06 -> 4.62e+06 (+10.4 %)`; 69 comparison rows, **6 advisory, 63 gating**; the only past-threshold advisory row is `control_buffer_read_under_contention/mutex/1` +14.3 %, explicitly non-gating. Job ran ~1 h 29 m. **This PR changes 0 `.rs` files**, so it cannot be the cause; that identity is precisely the one DV-043 recorded as *"explicitly not claimed as explained … a hosted-runner artefact"*, and DV-036 owns the reference-host re-baseline at session `0166`. `nightly` is `schedule`/`workflow_dispatch` only — **not a PR check** — so it does not block the merge. Its remediations are **Benchmarking Standards changes needing a Plan §8.3 amendment**; making gating rows advisory or loosening the 10 % threshold would be exactly the "loosen a tolerance to get green" this session's rules forbid. **Recorded as recommendations, not actions.** | [`bench-regression-rows.txt`](bench-regression-rows.txt) |
| 4 | **Medium** — CI diagnostics are insufficient; all four failures expose only `Process completed with exit code 1`; add `--junitxml`, upload under `if: always()`, write `$GITHUB_STEP_SUMMARY`, split nightly into separate jobs | **CONFIRMED as fact.** The annotations carry no pytest summary; the exact nodes had to be retrieved through the REST log API. Partly self-answering — that retrieval is what produced claim 2's node list. **Remediation is a `.github/` workflow edit**, out of scope for this bounded correction and it would break the recorded immutability invariant that `.github/` is empty for this cycle. **Recorded as a recommendation** for a dedicated CI-robustness session. | [`hosted-run-triage.txt`](hosted-run-triage.txt) |
| 5 | **Medium** — Node.js 20 actions are being forced onto Node 24 (`actions/checkout@v4`, `actions/setup-python@v5`), and `ubuntu-latest` migrates to Ubuntu 26 on **2026-10-19**; pin the image and roll out Node-24-native majors | **CONFIRMED as fact, and time-sensitive.** Both notices appear verbatim in the job annotations. The migration date is **two days out** and could turn checks red campaign-wide, which matters because amendment #52 keeps hosted checks active through session `0194`. **Workflow edit → out of scope here; recorded as an URGENT recommendation** for the maintainer to schedule before 2026-10-19. | [`adjudication-evidence.txt`](adjudication-evidence.txt) §B, [`hosted-inventory-final.txt`](hosted-inventory-final.txt) |
| 6 | **Medium** — setup is duplicated and largely uncached; `--no-cache-dir` defeats pip caching; cache wheels, preinstall `cargo-audit`, use a composite action | **Recorded without independent verification.** Plausible on its face (parity and nightly each rebuild environments), but it is a cost/efficiency improvement requiring workflow edits, out of scope for this correction. Not measured in detail and **not asserted as confirmed**. | — |
| 7 | **Low** — the parity step is still named "504 cases" but the PR adds a 39-file parametrized module | **CONFIRMED.** The parity job collected **2,238** tests (`28 failed, 2208 passed, 2 skipped`), so the step name no longer describes what runs. **Workflow edit → out of scope; recorded.** | [`adjudication-evidence.txt`](adjudication-evidence.txt) §E |
| CQ1 | The gate's top-level `pytest.importorskip("prinet")` is acceptable only because the workflows install the reference; otherwise a missing reference silently becomes a module skip. Add a CI preflight assertion / "reference required" mode | **REFUTED as a materialized risk here.** On Linux the reference arm **genuinely ran**: all 39 `test_reference_arm_reproduces_e3_reference_arm` parametrizations executed (28 failed, 11 passed), so the module was not skipped. S2 had already dispositioned the convention as *"not a finding"* (four sibling modules do the same; mitigated because the nine fast-gate argument tests import only `prin.reporting`). The recommendation is reasonable forward-looking hardening and is **recorded**, but adding it now would be a new feature inside a bounded correction. | [`adjudication-evidence.txt`](adjudication-evidence.txt) §F |
| CQ2 | The full-suite job serializes Python and Rust in one job, reducing signal | **CONFIRMED as fact** (`nightly.yml` runs pytest then `cargo test` in one job; the Rust step was skipped because Python failed first). Workflow edit → out of scope; **recorded**. | [`failure-identity-and-schema.txt`](failure-identity-and-schema.txt) |

## The one finding acted on — `EXP002D1-S4-F2` (D2), FIXED

**The defect.** `parity/test_parity_publication.py::test_reference_arm_reproduces_e3_reference_arm`
asserted that a fresh in-process render by the frozen `prinet==3.0.0` reference
generator reproduces the `normalized_sha256` recorded in the committed E3
reference run **on any platform**. That is false as a universal claim: Matplotlib
rasterizes and typesets through the host's FreeType build and font set, so the
same frozen generator does not produce byte-identical figures under a different
operating system. The E3 record was authored on Windows — and **the record says
so itself**: `environment.platform = "Windows-11-10.0.26300-SP0"`, a field
`exp002_driver` *requires* in every record. The gate was added by S1 in
`d90eeabb`, is not on `main`, and PR #34's push was its **first Linux execution**
— invisible under amendment #48's Linux/macOS suspension, and surfaced within
minutes of amendment #52 re-enabling the hosted checks.

**Why it is not a PRIN or reference defect.** Both arms shift together: the
registered H3 comparison (`test_prin_matches_reference_under_registered_comparison`)
passes **39/39 on Linux and on Windows**, because it renders both arms in the same
process. The 11 `.tex` tables reproduce byte-exactly on Linux. Only the
*cross-platform byte-identity of a single-platform record* was false.

**The fix.** Scope the byte-exact figure tie to the platform the frozen record
**itself declares** — read from `environment.platform`, never hard-coded as an OS
name, so the branch cannot be relaxed by hand and a future record authored
elsewhere carries its own scope. Off that platform: the 11 `.tex` tables are
**still compared byte-exactly**, and each figure must still render, be non-empty,
and survive `driver.normalized_bytes` (which validates PNG critical chunks and the
PDF Info/xref structure, so a truncated or malformed figure still fails). A new
test, `test_digest_tie_is_scoped_by_the_records_own_platform`, pins the mechanism:
the record must declare a platform, must carry a digest for all 39 files, and if
this host *is* the authoring platform the byte-exact branch must be the one taken.

**Non-vacuity proven by four negative controls**, driven by a pytest plugin kept
outside the repository that patches `item.module`
([`negative-controls.txt`](negative-controls.txt)):

| Control | Expected | Measured | Proves |
|---|---|---|---|
| `corrupt-figure`, platform matches | FAIL | **1 failed, 38 passed** | the byte-exact comparison is live on the authoring platform — not a no-op |
| `corrupt-tex`, platform matches | FAIL | **1 failed, 38 passed** | tables are byte-exact on the authoring platform |
| `bogus+corrupt-figure`, platform differs | PASS | **39 passed** | off-platform, figures correctly take the structural branch |
| `bogus+corrupt-tex`, platform differs | FAIL | **1 failed, 38 passed** | **off-platform the table tie is still byte-exact** — tables were not relaxed along with figures |

Rows 1 and 3 are the discriminating experiment: **the identical corruption fails on
the authoring platform and passes off it**, so the branch is demonstrably selected
by the record's declared platform rather than by the host OS. The unmodified run on
this host is **94 passed** ([`fix-verification.txt`](fix-verification.txt)), and
`ruff check`, `ruff format --check` and `mypy --strict` are clean on the changed
file. **Snyk Code: 0 issues** on the file
([`snyk-code-changed-file.txt`](snyk-code-changed-file.txt)) — which is the
applicable SAST control here, because `[tool.bandit] exclude_dirs` omits
`parity/*`, so a `bandit -r parity` run scans **0 LOC** and must not be reported as
"0 issues".

**Why this is a correction of a false assertion, not a weakening.** Stated
explicitly because the distinction is the whole question:

- On the platform where the **authoritative local gate** runs (Windows, matching
  the record), the byte-exact comparison is **unchanged and fully live** — control 1.
- Off-platform the tables **remain byte-exact** — control 4.
- The **H3 rule itself is untouched** and passes 39/39 on both platforms.
- **No test was skipped, deselected or xfailed**; the collected count is unchanged
  (94 locally, verified equal under the `bogus-platform` control so nothing was
  silently dropped).
- The frozen `EXP-002` record and everything under `benchmarks/results/EXP-002/`
  are **untouched**.

**Alternatives considered and rejected:**

1. *Record per-platform digests.* Would require editing the frozen
   `benchmarks/results/EXP-002/` records or creating a new `RUN-` directory — the
   former is forbidden, the latter is an experiment execution that S4 must not
   perform and that belongs to `EXP-002-r1`.
2. *Pin `parity.yml` to a Windows runner.* Would surrender Linux coverage that
   Definition-of-Done item 2 requires and that amendments #16/#17 exist for
   (cross-platform corpus regeneration at `rtol=2e-6`).
3. *Normalize away font rendering.* The registered normalization policy is frozen
   in the `EXP-002` pre-registration; extending it would be loosening a registered
   comparison to reach a green result.
4. *`skipif`/`xfail` off-platform.* Forbidden by this session's rules, and it would
   hide the branch instead of scoping it.

**Governance note, flagged for ratification.** This is a **code change made in a
documentation (S4) session**, which the Session Cycle does not normally permit. It
was made under the maintainer's explicit in-session authorization (*"i authorize
you to make the required decisions that block our progress and that get hosted
actions passing green without compromizing the plan, govenance, methodologies, and
established standards. maintain our rigorous and scientific method."*), on the
branch that introduced the defect, because a separate branch would have left PR #34
red. Per Development Workflow §7 it is **flagged for retro-audit at the next
S2-class audit**. Severity **D2** (a normative quality gate failed); **D1 was
considered and rejected** because no numerical parity claim or published result is
wrong — the H3 rule passes on both platforms.

## Two harness defects of my own, corrected rather than left standing

The first verification attempt reported **"V3 DID NOT FAIL: the byte-exact
comparison would be vacuous"**, which would have led to the opposite conclusion
about a correct fix. Both causes were found and fixed, and both runs are kept:

1. **`PYTHONPATH` was exported as an MSYS path** (`/c/Users/...`). Native Windows
   Python never sees it, so `-p negctl` died with `No module named 'negctl'` and
   the controls measured nothing. Windows paths with `;` separators are required.
2. **`cmd | tail -4; rc=$?` captured `tail`'s status**, not the command's — which
   is how a genuine `ruff` **E501** (line 89 > 88) and a real `ruff format`
   deviation were first reported as `exit code: 0`. Both were then fixed in the
   source, and every status is now taken unpiped or from `${PIPESTATUS[0]}`.

The plugin also patched the wrong module object at first: `parity/` has no
`__init__.py`, so pytest's prepend import mode loads the file as top-level
`test_parity_publication`, while `from parity import test_parity_publication`
creates a **distinct** module object the collected tests never used. Patching
`item.module` is correct under any import mode, and each control now prints the
module name and id it actually patched.

## Decisions taken, and what was deliberately NOT done

**Not done, with reasons:**

- **No dependency, lockfile, advisory-ignore or audit-configuration change.** DV-045
  assigns the lockfile update to *a dedicated hotfix or maintainer-authorized
  session*, explicitly **not** inside this correction, whose approved scope is
  bounded to the H3 correction; changing `Cargo.lock` would also break the recorded
  immutability invariant that it is empty for this cycle and would require the full
  Rust matrix and `cargo llvm-cov` to re-verify. The `audit` check **does not block
  the merge**: ruleset 22150076 carries no `required_status_checks` rule
  (amendments #48/#50/#52), and this session's rules leave that to the ruleset.
  **Recommended as the immediate next governed action**, with feasibility already
  measured above.
- **No workflow file edited.** Claims 3–7 all require `.github/` edits. Amendment
  #52's record states enabling the workflows modified no workflow file, and this
  cycle's immutability rule I1b requires `.github/` to stay empty. Claims 5
  (Node 24 / Ubuntu 26 migration, **due 2026-10-19**) and 4 (junitxml, step
  summary, job splitting) are the highest-value follow-ups and are handed off.
- **No benchmark threshold loosened or gating row made advisory** (claim 3).
- **No test skipped, deselected, xfailed or tolerance loosened** to reach green.

**Done:** the `EXP002D1-S4-F2` fix above, with its four negative controls, static
gate and Snyk Code scan; and this adjudication record.
