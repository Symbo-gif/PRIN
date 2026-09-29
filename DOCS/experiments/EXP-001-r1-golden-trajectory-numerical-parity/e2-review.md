# EXP-001-r1 E2 — Independent review and maintainer decisions

**Session:** `EXP-001-r1-E2`, declared by MichaelMaillet.<br>
**Date:** 2026-09-28 UTC.<br>
**Reviewer:** Claude Sonnet 5 — did not draft E1 (Devin drafted the
pre-registration and driver); serves as the "second AI reviewer that did
not draft the E1 document" campaign plan §2.2 names alongside the
maintainer.<br>
**Deliverable:** independent verification of E1's factual claims, technical
review of falsifiability/statistical adequacy/fair baselines/resource
sanity (Experimentation Standards §2 E2), and the maintainer's decisions on
the four items the pre-registration reserves to E2 (§10).<br>
**Protocol reviewed:** [`preregistration.md`](preregistration.md) as
committed at `3f04460` on `campaign/exp001-r1-e1`.

## 1. Independent verification (not taken on E1's assertion)

Per this repository's own governance ("Verify implementation facts from the
repository; do not invent commands, APIs, paths, configuration, or
evidence") and campaign plan §2.2's independent-reviewer role, every
provenance and machinery claim in `e1-handoff.md` was re-derived from the
repository rather than trusted:

| Claim | Independent re-derivation | Result |
|---|---|---|
| Corpus manifest SHA-256 | `sha256sum parity/corpus/manifest.json` | Exact match: `fcbaad1c…62edd2cf` |
| `parity/prinet_f64.py` SHA-256 | `sha256sum parity/prinet_f64.py` | Exact match: `c6972d5f…1631c2` |
| Pinned PRINet 3.0 `oscillator_models.py` SHA-256 | `sha256sum` on the file the importable `prinet` package actually resolves to (`DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/core/propagation/oscillator_models.py`, confirmed via `prinet.__file__`) | Exact match: `89d19734…9d77d4b9` |
| Built extension's default guard is `non_negative` | Called `exp001_r1_driver.preflight("corpus", Path("parity/corpus"))` live | Confirmed: `guard_policy: 'non_negative'`, plus every hash above independently reproduced by the same call |
| 1,000-case fuzz stream digest (`STREAM_SHA256`) | Called the driver's own `_draw_stream()` (draws inputs only, no integration) and hashed with `legacy.h2a_stream_digest` | Exact match: `9804fc09…854cff76` |
| 22 ill-conditioned indices | Read `driver.ILL_CONDITIONED` after the redraw above | Exact match to preregistration §5.4's list |
| Fresh bootstrap seed | `prin._prin_core.Seed(0,1).next_u64()` | Exact match: `12455822396014146421` |
| Existing raw-file size (6,208,871 bytes) | Summed `stat` sizes of all `benchmarks/results/EXP-001/RUN-*/*.json` | Exact match |
| r1 driver test suite (56 passed, 274/275 = 99.64%) | Re-ran `pytest tests/test_exp001_r1_driver.py --cov=...` | Exact match |
| ruff / mypy --strict clean | Re-ran both on both driver files and both test files | Confirmed clean |
| `check_dv_register_gates.py`, `check_global_session_registration.py` | Re-ran both | Confirmed passing (40 DV rows / 198 sessions; 17 Executive Audit reports) |
| `origin/main` CI green at `149cf2d` | Re-ran `tools/check_ci_green.py 149cf2d…` | Confirmed: same six run IDs, all green; `origin/main` unchanged since E1 |

No discrepancy was found between any E1 claim and the repository's actual
state. This does not itself validate the scientific hypotheses (no r1 case
has been integrated); it validates that E1's inputs, provenance pins, and
machinery are what the pre-registration says they are.

## 2. Falsifiability and statistical review

H1, H2a, H3, H4 have clean, deterministic, falsifiable decision rules
(§4.1); none can be rescued by a statistic. The DV-007 positive-explanation
method (§5.3) and the 22-case ill-conditioned witness (§5.4) are both
non-circular — the witness depends only on the reference's own sensitivity,
never on a PRIN residual — and neither can inflate the pointwise
denominators for H1/H2a.

**H2b three-way rule — APPROVED.** The proposed
`CONFIRMED`/`REFUTED`/`INCONCLUSIVE` decision (CI wholly inside the margin
confirms; CI wholly outside on one side refutes; a straddling CI is
inconclusive) is standard TOST-style (two one-sided tests) equivalence-test
logic. It corrects a real statistical error in the predecessor's binary
rule, which conflated "the data fail to demonstrate equivalence" with "the
data demonstrate non-equivalence" — those are not the same claim, and only
the three-way rule reports the difference honestly. Approved by
MichaelMaillet, 2026-09-28 UTC.

**Single-stream sample-size justification — APPROVED.** Experimentation
Standards §2 item 8 defaults to ≥10 seeds for confirmatory claims; this
experiment justifies one fixed 1,000-case stream instead. The justification
holds: EXP-001-r1 is a **targeted verification that a specific correction
fixes a specific, previously-identified failing population** (campaign plan
§10.4 item 4), not a fresh discovery study estimating a population
parameter under sampling variation. Re-testing the exact identified
population is the directly relevant confirmatory evidence for "did the fix
work on the cases that failed" — a design ≥10 independently-reseeded
replications would not improve, since it would each time draw a different,
less specifically diagnostic population. No old result is reused as a new
measurement (§1: "old outcomes are never used as new measurements").
Approved by MichaelMaillet, 2026-09-28 UTC.

## 3. Storage budget — APPROVED as requested

E1's request (preregistration §9) was independently checked against actual
file sizes (§1 table above: 6,208,871 bytes across the 4 existing runs,
exactly as claimed; 2,179,737 bytes of the inherited 8 MiB shared
allocation remained). MichaelMaillet approved the request as written:

- Shared `benchmarks/results/EXP-001/` allocation: **16 MiB** (covers the
  existing 4 runs plus new r1 runs together).
- New r1 runs, in aggregate: **8 MiB**.
- New r1 fuzz run: **6 MiB** exception to the generic per-run rule (mirrors
  the original amendment 6 precedent for the same reason — the 1,000-case
  fuzz artefact carries per-case beyond-horizon arrays H2b's analysis
  consumes and cannot be reduced without changing the registered protocol).
- Every other new r1 run: the generic **2 MiB** per-run cap, unchanged.
- Campaign-wide **64 MiB** cap: unaffected either way.

Recorded as campaign plan §14.2 amendment #7 (`campaign-plan.md` §14.2 row
7, matching the original amendment #6 storage-budget precedent) and DV
register update. Implemented in
`benchmarks/campaign/exp001_r1_driver.py`: `RAW_ROOT_CAP_BYTES` raised
8→16 MiB; new `R1_ROOT_CAP_BYTES` (8 MiB) checked only against
`RUN-*-r1-*/` directories, independent of the shared-root cap; new
`FUZZ_RUN_CAP_BYTES` (6 MiB) applied when `mode == "fuzz"`; `RUN_CAP_BYTES`
(2 MiB) unchanged for every other leg. Two new tests
(`test_fuzz_leg_gets_the_approved_wider_per_run_cap`,
`test_r1_subtree_cap_is_independent_of_the_shared_root_cap`) cover both new
limits; the full suite was re-run after the change (58 passed, 279/280 =
99.64%, the same one pre-existing defensive line uncovered) along with
ruff, ruff format --check, mypy --strict, and bandit, all clean on both
touched files. Snyk Code (`severity_threshold=low`) run separately on both
touched files (`snyk code test benchmarks/campaign/exp001_r1_driver.py`,
`snyk code test tests/test_exp001_r1_driver.py`, org `symbo-gif`): **0
issues** on each. Driver-commit changes during E2, before freeze, are normal
per campaign plan §12 rule 1.

## 4. Required wgpu coverage gate — NOT RESOLVED, blocks E3

The pre-registration's own §2 note states the Python driver cannot prove a
CPU-resident capsule came from wgpu rather than a fallback. This review
checked whether that claim understates the true state (i.e., whether a
disposition or a cheap fix already exists) by reading the actual binding
code, not just the driver:

- `crates/prin-sim/src/gpu.rs`: `SimRuntime` is a compile-time type alias —
  `#[cfg(all(feature = "wgpu", not(feature = "cuda")))]` makes it
  `cubecl::wgpu::WgpuRuntime` unconditionally in a wgpu-only build. So a
  successful `try_create_client()` in that build **is** a wgpu client by
  construction; the ambiguity is whether it silently fell back further to a
  host-slice (pure-CPU) path when client creation failed.
- `crates/prin-py/src/bindings/gpu.rs` / `mod.rs`: the DLPack export is
  zero-copy device-resident (`kDLCUDA`) only on the true CUDA path; the
  wgpu path and the host-slice fallback both copy back to host memory and
  return an indistinguishable CPU-resident capsule. This is a documented,
  intentional binding property (module docstring), not a bug the driver
  could work around — **there is currently no Python-visible signal at
  all** that distinguishes "wgpu executed" from "client creation failed,
  fell back to host-slice."
- `benchmarks/campaign/exp001_driver.py::compare_kernel_path_case` already
  raises `GpuBindingUnavailableError` on any non-CUDA-resident capsule
  (verified by reading the function directly) — correct behavior for H4,
  but it means the existing kernel-path driver cannot be reused for a wgpu
  leg either; it would reject every wgpu result as if it were a failed
  fallback.

This confirms the gap is real and sits below the Python layer, in the Rust
binding. Closing it needs a new accessor exposing whether
`try_create_client()` actually produced a device client (vs. falling back)
for the `--features wgpu`-only build — a small, well-scoped change, but one
that touches the GPU binding layer shared by every kernel-path experiment
and needs its own tests, S2 audit, and Snyk Code scan; it does not fit
inside an E2 review.

**Maintainer decision (2026-09-28 UTC):** presented with (a) a dated gap
disposition marking the wgpu leg `INCONCLUSIVE — capability unavailable`
(the §11.5 `timing_method` precedent's class of resolution), (b) blocking
on a coding fix first, or (c) dropping the requirement (not recommended —
would need a Project Plan §8.3 amendment), MichaelMaillet selected **(b)**.

**Recorded as DV-041** (`DEFERRED_VALIDATION_REGISTER.md`) and campaign
plan §11.7 (gap discovered) / §14.2 amendment #8 (remediation path
selected). Closure requires a governed hotfix/correction session (opened
only when actually started, per the ad hoc session table's own rule against
pre-reserving names) that adds the backend-identification accessor with
tests in tandem, a full local gate, and Snyk Code, before **EXP-001-r1 E3**
can begin; the same capability is independently required before **EXP-004
E1** (0169), which has a genuine wgpu *timing* claim with the identical
ambiguity.

## E2 exit

Three of the four gates in preregistration §10 are approved (items 1, 3,
4-as-independent-review); item 2 (wgpu) is open and blocks freeze/E3. This
session does not create any `RUN-` directory, execute any case, or freeze
the pre-registration. The next unit of work is the DV-041 hotfix session;
this review does not start it.

## 5. Follow-up E2 pre-execution amendment (proposed, not approved)

The earlier independent E2 review and MichaelMaillet's three
approvals in §§1–3 are unchanged. After DV-041's PR #25 merged to
`main` (`5615eda`; six required CI workflows green, recorded in
`DOCS/experiments/triage-dv043-handoff.md` §2), this proposed
pre-execution amendment adds the missing H1 wgpu coverage:
`r1-kernel-path-wgpu`, 72 identical manifest-selected sparse-k-NN
cases, the unchanged H4 tolerance, an actual post-dispatch
`backend_name` getter rejecting host-slice/CUDA fallback, three
host-exported DLPack checks, and an independently manifested H4
result. The existing CUDA leg retains three-CUDA-capsule proof.
At E3, two sequential `maturin develop` builds (`wgpu` then `cuda`)
will be made from one clean, unchanged approved-`main` checkout; each
will have its own extension hash, while both retain the same source SHA
(§5.1/§5.5). The pre-execution H1 tests on the unmerged candidate branch
are not evidence that E3's `main` build/CI/nightly already exists.
Neither the corpus nor the fuzz population/seed is altered; the 8 MiB
r1 allocation includes the sixth run. The NEW r1-driver tests use
synthetic inputs; the previously registered predecessor acceptance test
for the 72 sparse cases also runs as a code regression gate, not as a
new r1 RUN artefact or a scientific E3 result. Inputs and tolerances
were fixed before those tests ran.

**Review needed:** an independent reviewer who did not draft this
amendment must check both backend-proof paths (including silent
CPU/CUDA fallback rejection), synthetic test results under *both*
feature builds on H1, closure/backend-label tamper tests, the
per-backend 72/72 decision rule, resource cap, and baseline-delta
handling. Record exact commands/exit codes, extension hashes and
source SHA only from actual verification. Then request
MichaelMaillet's explicit dated approval of the revised H4
hypothesis and two-build order. Until that approval, this entry
is a **proposal, not an E2 approval or an E3 authorization**.

**Baseline-delta gate (§10.2):** E2's starting baseline was the
D1 correction merge `149cf2d`; PR #25 `5615eda` changed
`prin-sim`, `prin-kernels` and `prin-py` GPU paths after E2,
and DV-043 subsequently changed guarded integration on an
unmerged hotfix branch. E3/E4 must record the actual updated
main/source SHA and run both full 72-case GPU legs under that
SHA. E5 must list `149cf2d..E3_SHA` as a protocol deviation
(code changed after E2) and report the fresh H4 results;
it may not reclassify old EXP-001 runs as regression evidence.
If another numeric change lands before E3, repeat this
entry check rather than absorbing a mid-run SHA change.

**Pending:** maintainer determination that the disclosed non-author
technical check in §7 meets the independent E2 review requirement
(or a separate reviewer if required); Snyk Code result;
DV-043 merge with required CI green and next green nightly;
exact E3 main SHA; MichaelMaillet's explicit H4/two-build
approval. No result, freeze or verdict is recorded here.

**New local governance blocker, found at this amendment's
validation:** `python tools/check_deviation_ledger.py
DOCS/reports/038-project-state.md
DOCS/reports/039-project-state.md` exits 1: 128 inherited
IDs from PSR-038 are reported missing from PSR-039
(`parse_ledger`: 128 vs 8). The checker mistakes PSR-039's
§3.1/§3.2 local finding tables for a cumulative table and
never follows/combines its §3.3 PSR-038 delegation; PSR-038
also lacks six machine-readable WP-038 delta rows. Tracked as
**DV-044** (OPEN; no correction approved or executed). This
pre-existing, untouched governance surface will fail the
current `python.yml` ledger gate if the r1 branch merges
as-is. It is not a wgpu-result finding and is not silently
waived or fixed inside this pre-execution amendment.
A separately scoped, governed correction with tests and
independent review is required before merge/E3. This
session does not claim the governance suite or CI is green.

## 6. Local verification of the proposed amendment (not E2 approval)

**Scope and source identity.** These are engineering checks of a DRAFT
instrument on `campaign/exp001-r1-preexecution`, at committed parent
`256cc99be29d210ea8d7b9f45eaa73f9cff0751a` **plus the uncommitted
amendment diff**. That parent SHA alone does not identify the tested Python
driver or prove an E3 source baseline. The final approved execution code SHA
does not yet exist on `main`. Neither `--mode` r1 driver nor a real new r1
`RUN-` directory was invoked/created. The four historical EXP-001 runs
were not touched. New r1 tests used synthetic inputs; the old
`tests/test_exp001_driver.py` CUDA H4 acceptance regression test also exercised
the original corpus's 72 configurations as a **code test**, not a new
EXP-001-r1 experiment observation or E3 verdict. Inputs and bounds in this
proposal were selected before those tests ran.

**Build isolation and positive dispatch.** The shared venv had
`prin.pth` pointing at `C:\dev\PRIN\python` and `prin_core.pth` pointing at
`C:\dev\PRIN-r1-amendment\python`; a plain `import prin` from this worktree
would therefore import the *wrong* package/extension. For every run cited
here, `PYTHONPATH=C:\dev\PRIN-r1-amendment\python` selected the proposed
source, verified in a fresh Python process by printing `prin.__file__`
and `_prin_core.__file__` (both under this worktree, with the latter at
`python\prin\_prin_core.pyd`). Both offline builds set
`CARGO_NET_OFFLINE=true` and `PIP_NO_INDEX=1`; builds were **sequential**,
never `--features cuda,wgpu` together:

| Build/test stage (2026-09-28 UTC, H1) | Observed result |
|---|---|
| `python -m maturin develop -m crates/prin-py/Cargo.toml --features wgpu` (root venv interpreter) | Exit 0; feature-exclusive worktree build; imported extension SHA-256 `44b101a183ea48c3086365974e4fec316631399d529eef07f0d0eebd58eb73ed` |
| Fresh-process `tests/_env.py` executability probes after wgpu build | `wgpu_kernel_executes()=True`, `cuda_kernel_executes()=False`; exit 0, actual tiny kernel launched before the backend getter was read |
| `python -m pytest -v tests/test_exp001_r1_driver.py::test_wgpu_synthetic_sparse_comparison_on_real_adapter tests/test_gpu_backend_name.py --basetemp=.pytest_basetemp` | Exit 0; **8 passed, 3 skipped**. The live synthetic r1 wgpu test passed and asserted all three host-exported `dlpack_devices`; all three DV-041 wgpu-positive backend-name tests passed; only the three CUDA-only tests skipped. A skip is not a wgpu success. |
| `python -m maturin develop -m crates/prin-py/Cargo.toml --features cuda` after the wgpu test | Exit 0; imported extension SHA-256 `d4218a872dd7f7fac7d6b3d51df7b1163d5e602d005742eb4f4229d9e69aafe5` |
| Fresh-process executability probes after CUDA build | `cuda_kernel_executes()=True`, `wgpu_kernel_executes()=False`; exit 0, distinct new process and imported extension |
| `python -m pytest -v tests/test_exp001_driver.py::TestKernelPath::test_representative_cases_within_tolerance tests/test_exp001_r1_driver.py::test_wgpu_metadata_and_closure_reject_backend_mismatch --basetemp=.pytest_basetemp` | Exit 0; **3 passed, 0 skipped**. Both CUDA H4 representatives passed while asserting three actual CUDA capsule devices; synthetic wgpu metadata/label/closure check passed. |

The final tests/builds and their raw stdout/stderr are retained only in the
local gitignored `C:\dev\PRIN\.qwen\tmp\final-{wgpu,cuda}-{build,probe,tests}.log`.
They are **not** durable raw campaign evidence. Those two binary hashes
identify these particular candidate builds and differ; no conclusion about
why the binaries differ or about build reproducibility follows from that.
Each E3 feature build must be repeated on the **same approved clean main
checkout** and its real binary hash logged before the respective run; none
of these E2 hashes may be treated as an E3 run hash or baseline.

**Additional local checks.** On the earlier candidate diff, a broad
synthetic/predecessor test selection passed under the wgpu build
(74 passed, 3 expected CUDA-only skips) and under the CUDA build
(287 passed, 4 expected wgpu-only skips); `pytest-cov` reported 99%
statement coverage on `exp001_r1_driver.py` (289 statements, two misses).
Those broad counts were obtained **before** the final `dlpack_devices`
evidentiary-field/test adjustment, so they are supporting evidence only,
not a claim that a full suite was re-run on the final diff. After that
adjustment, a CUDA focused test selection passed 7/7, and the final
feature-specific checks are the logged rows above. The final diff passes
Ruff check/format on touched Python files, `mypy python/prin
benchmarks/campaign --strict` (65 files), `git diff --check`,
`tools/check_dv_register_gates.py` (43 rows/198 entries) and
`tools/check_global_session_registration.py` (17 reports). No numeric
threshold, seed, case selection or storage cap was changed.

**Unclosed gates, not represented as successes:** Snyk Code (new/modified
supported first-party source) has **not** run: external-network
authorization is pending. No dependency/manifest changed; Snyk Open
Source, `cargo audit` and `pip-audit` were not triggered by this amendment.
`tools/check_deviation_ledger.py 038 039` exits 1 as documented in §5
(DV-044: pre-existing ledger/parser failure; 128 inherited rows
are misreported missing). The DV-043 hotfix is not merged into `main`, its required CI
and next green nightly have not been checked, and the independent E2
review/maintainer's dated approval of this amendment are pending.
**No freeze or E3 execution is authorized by these local checks.**

## 7. Non-author technical check of the proposal (not maintainer approval)

On 2026-09-28 UTC a second AI reviewer, who did not author the H4
decision rule, backend-dispatch checks, code snippets, tests or
pre-registration, examined the proposed amendment against source and
the local build/test logs. The reviewer **did mechanically apply**
the lead-authored snippets during implementation, so this is
disclosed as a non-author technical check rather than asserted
to be independent of the implementation mechanics. It cannot
grant the campaign's E2 maintainer approval, a freeze, or an E3 run.
The maintainer must determine whether another separate E2 review
is needed before giving the explicit dated H4/two-build sign-off.

The reviewer found no D1/D2/D3. Its first pass raised one D4:
an H4 case's `backend_name`/`dlpack_devices` were assembled before
the hazard-abort return but no test asserted that an *aborted*
record retained the fields. The lead authored
`test_wgpu_hazard_abort_retains_backend_provenance` to exercise
that branch with a simulated wgpu engine and a synthetic invalid
derivative, plus assertions that the synthetic writer roundtrip
preserves both fields. The focused run of those two tests passed
(2/2, exit 0); the second source inspection found the D4
test-pin gap resolved. **These are simulated tests, not a new live
wgpu dispatch**; the actual live H1 wgpu and CUDA results
are separately logged in §6 and were not repeated just to
close this branch-coverage finding.

The actual selection seam is
`exp001_r1_driver.collect_cases`: the same manifest-filtered
`kuramoto`/`sparse_knn` case ID list is forwarded to the default
CUDA and explicitly selected wgpu paths. The reviewer initially
mis-cited a nonexistent `_load_sparse_knn_cases` at line 349;
that citation was withdrawn and checked against the real source
before this record was written. It also withdrew an unsupported
assertion that a Python `dlpack_devices` edit *caused* the
two extension hash values to differ. Only the observed hashes,
import paths, and positive executability probes in §6 are
claimed, with no causal claim about build byte differences.

Source/test coverage of the scoped questions: a wgpu getter is
read only after a kernel call and CPU/CUDA fallback is rejected;
the three raw DLPack exports on both backends are checked before
the saved per-case proofs; CUDA still requires all three
CUDA-resident capsules; one H4 denominator of 72 is enforced
**per** run, with no pooling. Label-to-backend and
backend-to-envelope closure checks are exercised with a synthetic
tamper test, and publication still requires its per-run manifest.
The numerical kernel tolerance, seed, case population, and
approved storage caps are unchanged. E4's prospective rule
checks saved comparison summaries; it does not claim to
reconstruct raw derivatives it did not store.

Remaining gates are not reviewer findings waved away: Snyk Code
has not run; DV-044's pre-existing PSR-039 deviation-ledger CI gate
fails as recorded in §5; DV-043 still needs a `main` merge,
required CI, and the next green nightly; the exact E3 baseline
SHA and E2 maintainer approval do not yet exist. No E3 execution
or result was reviewed here. The independent DV-043
retro-audit is recorded separately in
`DOCS/audits/2026-09-28-dv043-redundant-step-guard-audit.md` §7,
covering bit-identity, `n <= 1`, and the mutable-array caveat.
