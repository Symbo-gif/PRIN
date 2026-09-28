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
