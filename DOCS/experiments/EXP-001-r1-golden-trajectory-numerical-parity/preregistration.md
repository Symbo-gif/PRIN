# Pre-registration — EXP-001-r1: Golden-trajectory numerical parity

**Status:** **E2 FOLLOW-UP H4 METHOD APPROVED 2026-09-29 UTC; NOT FROZEN
AND NOT AUTHORIZED TO EXECUTE.** E3 remains BLOCKED on DV-043's
merged-main CI/green-nightly closure, DV-044's separately governed
ledger correction, and a recorded clean campaign execution checkout.
Frozen only at E3's first `RUN-` creation.<br>
**Authors:** Devin (AI pair, protocol and driver); MichaelMaillet (maintainer,
session declaration; E2 review pending).<br>
**Date:** 2026-09-28 UTC (the session was declared on September 27 local time).<br>
**Maintainer approval:** **E2 PARTIAL APPROVAL — MichaelMaillet, 2026-09-28
UTC.** Independent review conducted by Claude Sonnet 5 (did not draft E1;
campaign plan §2.2), who re-derived every E1 provenance claim (corpus/
reference/instrument hashes, the 1,000-case fuzz stream digest, the 22
ill-conditioned indices, the fresh bootstrap seed, the built extension's
default guard) from the repository rather than accepting them on assertion,
and independently re-ran the driver's test suite, ruff, mypy --strict,
`check_dv_register_gates.py` and `check_global_session_registration.py` —
all reproduced exactly as E1 reported, zero discrepancies. At the
original 2026-09-28 E2 review, three of four gates were
approved and the wgpu gate remained open. The 2026-09-29
follow-up H4 method approval below closes that protocol-design
gate only; E3 still waits for DV-043, DV-044 and the
M/R/F execution identity. See `e2-review.md` for the full record.

**Follow-up E2 maintainer decision (2026-09-29 UTC):** MichaelMaillet
approved the revised two-backend H4 design, two feature-exclusive
builds from one execution commit, and the disclosed non-author
technical review's adequacy for E2. In direct response to those
presented decisions and a separately governed DV-044 correction,
the maintainer wrote: "I approve everything that keeps this
project going, i approve a forced nightly for faster results on
progress, and anything that stays true to established goals."
Approval is scoped to the reviewed pre-execution method and a
prospective DV-044 correction; it does not mark DV-043 merged,
close DV-044, accept a failed nightly, authorize E3, or freeze
the protocol. A forced `nightly.yml` dispatch on **main after
DV-043 merges** is approved, subject to its actual result.
The corrected M/R/F source identity in §5.1/§8 is part of this
approval because campaign plan §12 forbids E3 on main without
the r1 driver; it changes no science, denominator, tolerance,
seed, hypothesis or backend inclusion. `e2-review.md` §8
records the decision and evidence.

| E2 gate (§10) | Decision | Record |
|---|---|---|
| §7 single-stream (not ≥10 replications) sample-size justification | **APPROVED** | e2-review.md §2 |
| §7 three-way H2b equivalence decision rule (replacing the predecessor's binary rule) | **APPROVED** | e2-review.md §2 |
| §9 storage budget (16 MiB shared / 8 MiB new r1 / 6 MiB fuzz exception) | **APPROVED** — campaign plan §14.2 amendment #7 | e2-review.md §3; driver updated (`RAW_ROOT_CAP_BYTES`, new `R1_ROOT_CAP_BYTES`, new `FUZZ_RUN_CAP_BYTES`) |
| §2 required wgpu driver/coverage gate | **APPROVED 2026-09-29 UTC (follow-up E2 method only; E3 blocked on DV-043/DV-044 and execution SHA gates)** | e2-review.md §§4–8; `DEFERRED_VALIDATION_REGISTER.md` DV-041; campaign plan §11.7, §14.2 amendment #8 |

DV-041's backend-identification hotfix merged as PR #25
(`5615edab5b53afd6602907343a596cdc3f8dff4a`;
six required CI workflows green per `triage-dv043-handoff.md`
§2). MichaelMaillet approved this follow-up E2 H4
**method** on 2026-09-29 UTC. No r1 result, analysis,
main-branch DV-043 merge SHA, DV-044 correction, green
post-hotfix nightly, or E3 freeze follows from that
approval. The first E3 `RUN-` directory still freezes
the last approved pre-registration edit; until all
§10 entry gates close this record is unfrozen and E3
does not start.<br>
**Code version:** `prin-core` distribution `1.0.0rc1`, Rust `1.0.0-rc1`;
E1 starting tree `a7ef308acffbf3ecd09aa1b4fbe55a9b09d09e74`, incorporating
correction merge `149cf2d88ab6be401951b63d1d7e8fad209f52a5` and the correction's
S2–S4 documentation. The E1 commit versions the new driver and this draft;
E3 records the exact approved freeze and execution SHAs.<br>
**Session:** `EXP-001-r1-E1`, declared by the maintainer against
[`README.md`](README.md). Successor: `EXP-001-r1-E2`, independent review and
maintainer approval. The original global sessions 0154–0158 stay complete;
their IDs are not reused or renumbered.<br>
**Related plan items:** Project Plan F2, F4, §4.3, §5, §6 Phase 7, §8 and
DoD #12; Experimentation Standards §§1–4; campaign plan §2.1 EXP-001/C1,
§§5–10 and §12; amendment #47.<br>
**Record root:** this directory. **Raw root:** `benchmarks/results/EXP-001/`,
new `RUN-<UTC>-<SHA>-r1-<leg>/` directories only. Sidecars identify
`exp_id="EXP-001-r1"` and `session="EXP-001-r1-E3"`.

## 1. Background and motivation

The original [EXP-001 report](../EXP-001-golden-trajectory-numerical-parity/report.md)
refuted H1 and H2a under its frozen rules. Its verdicts, pre-registration,
log, analyses, manifests and raw results remain immutable. This new record
implements campaign plan §10.4 item 4 after the
[correction audit](../../audits/2026-09-24-exp001-d1-correction-audit.md):
S2 PASS, S3 CLEAN, S4 complete, correction PR #24 merged. The merged code's
six required workflows are green; exact entry evidence is in
[`e1-handoff.md`](e1-handoff.md).

The correction established two distinct mechanisms. PRIN's Euler/RK4
amplitude/derivative guards did not match the reference model path; amendment
#47 corrects the default to `GuardPolicy::NonNegative`. Independently, the
PRINet 3.0 Stuart–Landau and mean-field derivatives narrow to `complex64`
inside a float64 model (DV-007). The correction's 50-digit exactness audit
identifies the reference as the erroneous side in all 67 adjudicated cases.
These are prior findings, not observations from this re-run.

The question is whether freshly collected evidence from the corrected PRIN
implementation meets the registered parity rules, including the already
adjudicated reference defect, and retains reproducibility and CUDA kernel
agreement. The 22 previously identified ill-conditioned fuzz inputs require
fresh reference-sensitivity evidence and valid PRIN outputs. Their
characterization is not a pointwise-parity success.

This is a prospective **verification of a correction on a known input
population**, not an independent holdout study. The original experiment and
correction results were known when this protocol was drafted. The same seed
and inputs are deliberately reused to test the correction; **old outcomes
are never used as new measurements**. No r1 workload or pilot is run in E1.
Driver tests use synthetic arrays with both numerical runners replaced.

### 1.1 Binding reconciliation

Campaign plan §2.1, Project Plan §5 and amendment #47 govern these values.

| Quantity or path | Registered rule |
|---|---|
| CPU trajectories, including initial/final arrays | `rtol=1e-6`, `atol=1e-8` |
| CPU order parameter and mean phase coherence | `rtol=2e-6`, `atol=1e-12`, cross-implementation comparison; amendments #16/#17 |
| Single-runtime metrics/decompositions | The `1e-10` target remains applicable to its existing tests; this experiment does not measure decompositions or establish new single-runtime claims |
| CUDA derivative kernel | `rtol=1e-5`, `atol=1e-6`, float32 kernel against the existing CPU reference; Testing Standards §3 |
| Euler/RK4 model path | Default `guard="non_negative"`: amplitude floor exactly `0`, no ceiling; sparse k-NN retains its path-specific derivative clamp |
| Bounded/OscilloSim paths | `guard="bounded"` retains its separate semantics; this experiment does not switch the registered model integrations to that guard |
| DV-007 | A native-reference breach can be explained only by the positive float64-reference test in §5.3; the `1e-6` derivative disposition is **not** a widened trajectory tolerance |
| `strength_of_incoherence*` | Expected-divergence exception under amendment #25 remains in force, but these quantities are absent from this experiment's `CaseArrays`; no parity claim is made for them |

CPU comparisons call the existing `prin.parity.harness.compare_arrays` /
`compare_case` without changing their implementation. In particular, their
elementwise test is `numpy.isclose(reference, produced, rtol, atol)`, whose
relative term uses the **second operand**. The separately reported relative
error uses `abs(reference) + 1e-300`. Neither a different operand order nor a
relative-error summary replaces the actual elementwise decision. Near-zero
relative errors can be very large; report the absolute error and failure
count alongside them.

## 2. Hypotheses

**H1 — full-corpus parity with the registered DV-007 explanation.** All
**504/504** corpus cases satisfy either native-reference parity or the
positive explained-divergence rule in §5.3, across all 11 arrays. Publish
native passes, explained divergences, unexplained breaches and aborts
separately. Confirmation is not a claim that every native PRINet array was
reproduced within tolerance.

**H2a — registered fuzz population within the comparison horizon.** All
**1,000** inputs from the fingerprinted `Seed(0, 1)` stream are accounted for:
the **978** inputs outside the fixed sensitivity set satisfy the same
native-or-explained rule through steps `0..min(20, n_steps)`; the **22**
registered sensitivity cases satisfy §5.4's reference-only re-proof and
PRIN validity checks. No new exclusion may be selected from a PRIN error.
Report `978 pointwise + 22 characterized`, never `1,000 pointwise passes`.

**H2b — beyond-horizon ensemble mean coherence equivalence.** For each of
`order_parameter_traj` and `mean_phase_coherence_traj`, the mean of the
per-case paired differences over steps `21..n_steps` lies within the
registered equivalence margin: **0.01** and **0.02**, respectively. The
reference for this hypothesis is the **unmodified PRINet 3.0** trajectory,
including for DV-007 and ill-conditioned inputs. Both metrics must establish
equivalence under §7's interval rule.

This tests ensemble mean differences. It does not establish equality of the
full distributions, equivalence of every regime, a phase-boundary theorem,
or the absence of canceling case-level differences. The fixed 20-step cutoff
is inherited from the original protocol and corpus length; it is not a
newly measured Lyapunov shadowing horizon. Ill-conditioning alone is not
proof of chaos.

**H3 — CPU bit-level repeatability.** Each of the **14** fixed representative
cases in §5.2 produces identical dtype, shape and bytes on two integrations.
Two separately manifested E3 invocations also produce identical canonical
scientific result projections, including per-array digests.

**H4 — CUDA and wgpu derivative-kernel agreement.** Each backend
independently executes the same **72/72** `kuramoto_sparse_knn_*` corpus
cases from their stored initial states, comparing three float32 GPU
derivative arrays against the same float64 Rust CPU reference with
`rtol=1e-5, atol=1e-6` (Testing Standards §3). A CUDA result requires all
three raw DLPack capsules to be CUDA-resident. A wgpu result requires all
three capsules to be host-exported (the binding's documented behavior)
**and** `GpuSparseKuramoto.backend_name` read **after each actual kernel
dispatch** to report the wgpu backend family. `"cpu-native"`, `"cuda"`,
an absent getter or an unexpected capsule device is a build/backend
**abort**, not a passing or refuting wgpu case. Each H4 case record
retains a three-key `dlpack_devices` mapping (`dphase`, `damplitude`,
`dfrequency`) with the raw capsule device types; the wgpu record also
retains `backend_name` after that case's dispatch. E4 can verify those
proofs without re-running a kernel. The two results have
different registered labels and manifests; a CUDA result never counts
as the wgpu run. H4 `CONFIRMED` requires 72 valid passing cases on each
backend; any valid breach on either backend `REFUTES` H4 (D1); absent,
invalid or partial coverage without a valid breach is `INCONCLUSIVE`.

**E2 follow-up H4 method approval (2026-09-29 UTC):**
DV-041 supplied the `backend_name` capability on
`main` at PR #25. The four-mode r1 driver has a
second `kernel-path` label for the wgpu companion
(not a new mode or tolerance), positive per-case
backend identification, and fail-closed run closure.
The same 72 manifest-selected configurations run on
each backend; no r1 outcome selected a case, bound
or exclusion. Synthetic and live-adapter tests were
independently inspected, and MichaelMaillet accepted
the disclosed non-author review as sufficient for the
method decision (`e2-review.md` §§6–8). This is
*not* a §5.4 hardware-unavailability disposition
or permission to execute before §10's other gates.

## 3. Expected results

These are predictions based on prior governed evidence, not r1 results.

| Hypothesis | Predicted direction | Predicted magnitude/range | Basis |
|---|---|---|---|
| H1 | Confirmed under the registered rule | 504 accepted; approximately 19 native DV-007 breaches positively explained; zero unexplained breaches | Correction audit §S1.2 and §S3.2; native breach count is host-dependent and is not an acceptance target |
| H2a | Confirmed with the fixed characterization stratum | 978 accepted pointwise; 22 sensitivity proofs and valid PRIN outputs; zero unexplained eligible breaches | Same audit; the corrected guard addresses the PRIN mechanism and the corrected reference isolates DV-007 |
| H2b | Equivalent ensemble means | Each mean difference near zero, with both CI endpoints strictly inside its margin; no directional bias predicted | Original H2b confirmed; the corrected guard and published sensitivity evidence motivate remeasurement, without guaranteeing its outcome |
| H3 | Identical | 14/14 byte-identical within each invocation; zero separate-run digest differences | Explicit-state deterministic Rust integration; original H3 and existing repeatability controls |
| H4 | Both backends within the same kernel tolerance | CUDA 72/72 and wgpu 72/72, zero failed derivative elements on either | Prior CUDA kernel-equivalence controls and DV-041's live backend-identification tests; no r1 case result has been examined |

H2b's margins retain the predecessor's choice of 1% of each metric's bounded
range. They are engineering equivalence margins; a difference below them does
not by itself prove that a scientific classification near a boundary cannot
change.

## 4. Failure conditions

### 4.1 Valid negative results

| Hypothesis | Refutation rule |
|---|---|
| H1 | At least one valid case fails native parity and lacks a successful, eligible DV-007 explanation |
| H2a | At least one valid case outside the fixed 22-case set fails the native-or-explained rule within the horizon |
| H2b | With complete valid sampling and at least 30 contributors, at least one metric's entire 95% CI lies strictly above `+margin` or strictly below `-margin` |
| H3 | Any valid within-invocation byte mismatch or mismatch between the two validated canonical result projections |
| H4 | Any valid derivative comparison on either CUDA or wgpu fails the unchanged float32 tolerance |

Every such C1 refutation carries a D1 under campaign plan §10.4. E4 applies
the rule; E5 reports the negative result in full and preserves the block on
0159, all downstream experiments and 0194. Correction follows S1–S4; no
rerun-until-green, altered tolerance, optional stopping or post-hoc exclusion
rescues it.

### 4.2 Invalid or aborted measurements

The following invalidate the affected run/case and are reported distinctly:

1. Non-finite arrays; wrong shape/dtype; phase outside `[0, 2π)`; order
   parameter outside `[0, 1]`; mean phase coherence outside `[-1, 1]`;
   negative amplitude under the registered model guard. These checks apply
   to PRIN, native reference and any corrected/perturbed reference used.
2. A sensitivity proof for one of the fixed 22 inputs is not reproduced,
   or its reference output is invalid. This makes its registered
   characterization unavailable; it cannot be silently counted as a pass
   or replaced by another input. The remaining native/corrected comparison
   evidence is retained when available.
3. A corpus, stream, reference source or instrument fingerprint differs;
   the cast-only AST check fails; PRINet 3.0.0 is unavailable/wrong-version;
   or the loaded extension does not expose the corrected defaults.
4. Required environment fields are missing; a GPU leg lacks GPU/VRAM
   metadata; any CUDA capsule is not `kDLCUDA`; or the required feature/
   device path cannot execute. No fallback is published as the requested
   backend. A wgpu kernel returning a non-wgpu `backend_name` after dispatch
   (or no getter) or a non-host-exported capsule is also an
   environment/backend abort. The wgpu client must execute, not merely
   exist; a host-slice CPU or CUDA fallback may not publish a wgpu result.
5. Run-ID/label/SHA/session mismatch, reused directory, incomplete sidecar,
   manifest failure, unexpected result inventory or corrupted evidence.
6. The approved CPU/GPU/storage budget is exceeded. All preserved original
   runs count toward shared storage; the old fuzz waiver is not inherited.
7. An unexplained seed/configuration reproducibility failure. A mismatch in
   H3's otherwise valid repeated outputs is also a D1 counterexample and
   must not disappear merely because the configuration is marked invalid
   for other downstream uses.

An invariant violation or unexplained reproducibility problem is escalated
as a possible D1 independently of the invalid-run label. Invalid does not
mean scientifically harmless.

**Validity limit retained from the driver:** an internal clamp-trip signal
is not exposed at the Python boundary. The driver checks the observable
envelope and the new amplitude floor; it does not claim to observe every
derivative clamp event. Positive float64-reference parity constrains the
eligible paths, but does not replace missing trip instrumentation. E5 must
repeat this limitation, particularly for the 22 characterized cases.

No timing measurement or ONNX provider comparison is part of this protocol.
Campaign timing-invalidity and provider-fallback rules still apply if such
a measurement is proposed; it requires a pre-execution amendment rather
than being added to these untimed legs.

**Reporting commitment:** all registered cases, failed comparisons, aborts
and unexecuted required legs are reported. Aborted directories are retained;
retries receive new IDs and remain linked to their predecessors. Partial
denominators cannot confirm a hypothesis.

## 5. Method

### 5.1 Inputs, configurations and provenance

The corpus is schema 1, generator `prinet==3.0.0`, 504 cases, committed at
`parity/corpus/`. Its manifest SHA-256 is:

```text
fcbaad1cb16edb3445c9b9ce122131bf4361d9c4ce17c4bc67edd74c62edd2cf
```

The manifest and every NPZ are validated by `CorpusLoader`. No corpus is
regenerated or replaced for r1.

| Configuration | Registered population |
|---|---|
| Corpus | Kuramoto 216, Hopf 216, Stuart–Landau 72; Euler/RK4; mean-field/full/sparse k-NN where supported; Stuart–Landau full only |
| Corpus grid | `N ∈ {8,12,16,24}`, `K ∈ {0.5,1,2}`, `dt ∈ {0.005,0.01,0.02}`, 20 steps |
| Fuzz models/couplings/integrators | The same seven valid model/coupling cells × two integrators; selected by the existing `draw_fuzz_spec` |
| Fuzz size/steps | Integer `N ∈ [8,64]`, `n_steps ∈ [5,50]` |
| Fuzz timestep/coupling | `dt ∈ [0.001,0.05)`, `K ∈ [0.1,4.0)` |
| Kuramoto extras | `decay_rate ∈ [0,0.5)`, `freq_adaptation_rate ∈ [0,0.05)` |
| Hopf extras | `bifurcation_param ∈ [-0.5,2)`, `freq_adaptation_rate ∈ [0,0.05)` |
| Stuart–Landau extra | `bifurcation_param ∈ [-0.5,2)` |
| Sparse degree | Integer `k ∈ [2,min(12,N-1)]` |
| Fuzz initial state | Direct `Seed` draws: phase `[0,2π)`, amplitude `[0.5,1.5)`, frequency `[-1,1)`; identical explicit arrays supplied to both implementations |
| CPU path | `legacy.run_prin_trajectory` → `prin.dynamics` → Rust; float64; corrected Euler/RK4 default |
| CUDA path | Existing `compare_kernel_path_subset` → raw `GpuSparseKuramoto`; three float32 derivative arrays, actual CUDA residency checked |
| wgpu path | The same 72 corpus initial states and CPU reference as H4 CUDA, direct raw `GpuSparseKuramoto` call, f32 CubeCL computation; all three outputs are host-exported and `backend_name` proves wgpu after dispatch |

The first **exactly 1,000** spec/initial-state draws are pinned by the
existing `h2a_stream_digest` encoding:

```text
9804fc09e4a510ef0c34dfa5b58c6639a62baf15cf4f38f481ed1c8b854cff76
```

The driver materializes and verifies this input fingerprint **before any
integration**. Each fuzz record also retains all parameters and a per-input
digest. It neither reads predecessor result JSON nor uses a prior verdict
to decide which new inputs run.

CPU, CUDA and wgpu use campaign host **H1**, the registered Windows workstation /
`PRIN-GPU-Runner`. Record the actual environment at execution; the campaign's
historical OS/driver versions are not assumed current. H2/H3/H4 hosted
cross-OS runs are optional and unscheduled. wgpu is separately gated above.
No Triton timing, NPU, DirectML, training or throughput claim is made.

**Two mutually exclusive extension builds, one execution
commit and a separately recorded main baseline.** Let
`M` denote the *actual future* merged-main SHA carrying
DV-043 with required CI green and a following green
`nightly.yml` `bench-regression` (campaign plan §11.8);
`M` is not yet known or claimed here. Let `R` denote a
single, clean, committed EXP-001-r1 campaign-branch
execution checkout that includes the approved
pre-registration/driver and incorporates `M` **before**
E3. Campaign plan §12 rule 3 retains E1–E5 on the
campaign branch until its E5 PR, so **E3 cannot execute
from `main` directly**: `main` does not carry this r1
driver yet. Do not merge a newer numeric baseline or
edit source mid-experiment; a new `main` change before
E3 triggers the §10.2 entry check again. E3 logs
`M` (upstream baseline), `R` (the only execution
`git_commit`/run-directory SHA for all six runs),
and `F` (the last pre-registration-edit SHA, recorded
on `log.md` line 1 at the first `RUN-` creation).
`F`, `M` and `R` have different roles; they are not
casually equated. Start from the clean `R` checkout
after DV-044's independent correction and E2's
approval have been recorded. With **no tracked
source change between builds or runs**, use the
following two commands sequentially in the SAME
execution checkout:

```powershell
.venv\Scripts\python.exe -m maturin develop -m crates/prin-py/Cargo.toml --features wgpu
# Start a fresh Python process, assert tests/_env.py::wgpu_kernel_executes()
# actually ran a kernel and reports true, record extension path and SHA-256;
# execute only the registered r1-kernel-path-wgpu label.
.venv\Scripts\python.exe -m maturin develop -m crates/prin-py/Cargo.toml --features cuda
# Start a DIFFERENT fresh Python process, assert cuda_kernel_executes()
# reports true, record extension path and SHA-256; execute the CPU and
# r1-kernel-path-cuda labels under this extension.
```

In each new process, verify that `prin.__file__` resolves under the clean
execution checkout's `python/prin` directory and that
`_prin_core.__file__` resolves to the freshly built feature variant; log
both paths and the extension SHA-256. `maturin develop` can update
`prin_core.pth` without replacing an older `prin.pth` in a shared venv, so
an alternate worktree may import the wrong source unless `PYTHONPATH` is
set to that checkout's `python` directory. Abort on any path or
backend-probe disagreement rather than treating a successful build as
proof of the imported extension.

`crates/prin-py/Cargo.toml` has `default=[]`, and `wgpu` is selected under
`cfg(all(feature = "wgpu", not(feature = "cuda")))`; combining the flags
(`--features cuda,wgpu`) is **not** a wgpu build. Cargo fingerprints each
feature set, but the second `maturin develop` replaces the installed
`prin._prin_core`: no Python process may retain the old import after a
rebuild. Both variants come from the same unchanged
campaign execution checkout R; both run environments record R,
while E3 separately records main baseline M and the pre-registration
freeze edit SHA F. The Git-commit source-status check
applies to TRACKED CODE; append-only `RUN-` output directories
created after the first run must be accounted for as output,
not treated as permission for a code change or discarded to
force `git status` to look clean. The two builds
have individually recorded build command, feature set, imported
extension path and binary SHA-256 in `log.md` and the run `config`;
hashes may differ by design and E4 must verify each against its own log
entry, not demand binary identity. Verify current source status and SHA
before **each** build and run; output directories are append-only and
do not license a source edit. A missing/failed build or either probe
aborts that leg; do not substitute the already-installed other backend.
The driver records the binary hash and checks the default guard, but those
checks alone cannot prove that every compiled source line corresponds to
the checkout; the clean-build record is therefore mandatory.

### 5.2 Fixed H3 case list

The lexicographically first manifest case ID in each valid
`(model, coupling, integrator)` cell is fixed in E1, from metadata only:

```text
hopf_full_euler_n12_s20_dt0_005_K0_5_seed1800009
hopf_full_rk4_n12_s20_dt0_005_K0_5_seed1900009
hopf_mean_field_euler_n12_s20_dt0_005_K0_5_seed1600009
hopf_mean_field_rk4_n12_s20_dt0_005_K0_5_seed1700009
hopf_sparse_knn_euler_n12_s20_dt0_005_K0_5_seed2000009
hopf_sparse_knn_rk4_n12_s20_dt0_005_K0_5_seed2100009
kuramoto_full_euler_n12_s20_dt0_005_K0_5_seed1200009
kuramoto_full_rk4_n12_s20_dt0_005_K0_5_seed1300009
kuramoto_mean_field_euler_n12_s20_dt0_005_K0_5_seed1000009
kuramoto_mean_field_rk4_n12_s20_dt0_005_K0_5_seed1100009
kuramoto_sparse_knn_euler_n12_s20_dt0_005_K0_5_seed1400009
kuramoto_sparse_knn_rk4_n12_s20_dt0_005_K0_5_seed1500009
stuart_landau_full_euler_n12_s20_dt0_005_K0_5_seed2200009
stuart_landau_full_rk4_n12_s20_dt0_005_K0_5_seed2300009
```

The corpus's seed integers identify the already stored initial conditions;
they are not redrawn using the campaign key.

### 5.3 DV-007 positive explanation

1. Collect PRIN and the native reference; validate both outputs. For H1 the
   native reference is the stored corpus. For H2 it is a fresh unmodified
   PRINet trajectory from the identical explicit initial state.
2. Record every native per-array comparison. If all pass, classify
   `native-parity`.
3. A native breach off the DV-007 paths is `unexplained-breach`. The
   eligible paths are Stuart–Landau full coupling and Kuramoto/Hopf
   mean-field. A model name or a historical case ID alone cannot excuse a
   breach.
4. On an eligible breached path, integrate the same reference with
   `parity.prinet_f64.f64_corrected_reference`: only the three adjudicated
   derivative methods have their narrowing casts widened. No guard,
   integrator, coupling, metric or initial-state rule is otherwise changed.
5. Validate this reference and compare PRIN against it at the **same**
   array tolerances and horizon. All comparisons must pass to classify
   `explained-dv007`; otherwise classify `unexplained-breach`.

The reference source and instrument are hash-pinned and the cast-only
`assert_replacements_match_reference` AST check runs before measurement.
The instrument restores the original methods on exit, including errors;
these runs are serial, never concurrent in one Python process.

| Source | SHA-256 at E1 |
|---|---|
| Importable PRINet 3.0 `oscillator_models.py` | `89d19734c714e31f355d018d7b5889e48f4787841dc15c43df6abdad9d77d4b9` |
| `parity/prinet_f64.py` | `c6972d5f1ca1380f0d80249034479ed2974a34d20c27b295ddf90f441c1631c2` |
| Correction exactness evidence JSON | `ac218c34e0d8a70ddac21cdf6ec7a8fd66c2825828edabab40dbeaa9f79c67f4` |
| Correction postfix decomposition JSON | `2d741bbcf6ee9c4b33d92092f8b10c1cc7bac2eb5adce008f054926ccbf06dab` |

The last two files are supporting prior evidence in
`EVIDENCE/exp001-d1-s1/`. The r1 driver does not load their measured outputs.

### 5.4 Fixed ill-conditioned stratum

The registered zero-based fuzz indices are exactly:

```text
50, 76, 90, 270, 310, 330, 334, 362, 385, 398, 399,
415, 456, 522, 621, 623, 653, 691, 734, 841, 867, 878
```

For each, retain the native comparison and collect two fresh float64-
evaluated reference trajectories: original phases and
`numpy.nextafter(phase_init, +inf)`, leaving amplitudes, frequencies and all
parameters identical. A within-horizon comparison must breach the same
tolerance. The witness depends only on the reference, never the PRIN error.
All reference and PRIN arrays must be finite, correctly shaped, and inside
the registered envelope, with nonnegative PRIN amplitudes.

Retain the reference-sensitivity comparisons and PRIN-versus-float64
residuals even though the latter do not gate pointwise acceptance in this
stratum. Set `pointwise_eligible=false`, `accepted=null`, and
`classification="ill-conditioned-characterization"` only after the proof
succeeds. No residual ceiling is invented for this stratum. All valid
members with more than 20 steps remain in H2b; no separate statistical
confirmation of this small subgroup is claimed.

### 5.5 Driver and E3 commands

The new committed driver is
[`benchmarks/campaign/exp001_r1_driver.py`](../../../benchmarks/campaign/exp001_r1_driver.py).
It reuses the predecessor's numerical runners, sampler, GPU residency
checks and publication primitives. The predecessor's scientific rules and
default experiment identity remain unchanged. Its closure helper accepts
an explicitly supplied expected identity for the new record.

These are **prospective E3 commands**, executable only after §10's gates
close. Replace `<UTC>` with a fresh `yyyyMMddTHHmmssZ` timestamp and `<SHA>`
with the execution checkout's short SHA. The driver checks both SHA and
label against the directory name.
Here `<SHA>` is the short hash of the committed campaign
**execution** checkout `R`, not the separately recorded
green-main baseline `M`; the r1 driver must actually
exist and import from `R`. Every one of the six commands
must use the same `R` value. Log the full `R` alongside
the full `M` and freeze-edit `F` before the first run.

```powershell
# Build --features wgpu first, assert the live kernel probe, then run:
.venv\Scripts\python.exe -m benchmarks.campaign.exp001_r1_driver --mode kernel-path --out benchmarks/results/EXP-001/RUN-<UTC>-<SHA>-r1-kernel-path-wgpu --label r1-kernel-path-wgpu --session EXP-001-r1-E3 --operator MichaelMaillet
# Rebuild --features cuda; assert the live CUDA probe, then run the
# existing corpus, repeatability (twice), fuzz and CUDA kernel-path commands.

# Full corpus: H1
.venv\Scripts\python.exe -m benchmarks.campaign.exp001_r1_driver --mode corpus --corpus-dir parity/corpus --out benchmarks/results/EXP-001/RUN-<UTC>-<SHA>-r1-corpus-cpu --label r1-corpus-cpu --session EXP-001-r1-E3 --operator MichaelMaillet

# Repeatability, two separate invocations: H3 and campaign §6.5
.venv\Scripts\python.exe -m benchmarks.campaign.exp001_r1_driver --mode repeatability --out benchmarks/results/EXP-001/RUN-<UTC>-<SHA>-r1-repeatability-cpu --label r1-repeatability-cpu --session EXP-001-r1-E3 --operator MichaelMaillet
.venv\Scripts\python.exe -m benchmarks.campaign.exp001_r1_driver --mode repeatability --out benchmarks/results/EXP-001/RUN-<UTC>-<SHA>-r1-seedrep0-cpu --label r1-seedrep0-cpu --session EXP-001-r1-E3 --operator MichaelMaillet

# Exactly the registered 1,000 inputs: H2a/H2b
.venv\Scripts\python.exe -m benchmarks.campaign.exp001_r1_driver --mode fuzz --out benchmarks/results/EXP-001/RUN-<UTC>-<SHA>-r1-fuzz-cpu --label r1-fuzz-cpu --session EXP-001-r1-E3 --operator MichaelMaillet

# CUDA derivative kernel: H4
.venv\Scripts\python.exe -m benchmarks.campaign.exp001_r1_driver --mode kernel-path --out benchmarks/results/EXP-001/RUN-<UTC>-<SHA>-r1-kernel-path-cuda --label r1-kernel-path-cuda --session EXP-001-r1-E3 --operator MichaelMaillet
```

Six new run directories are registered: one wgpu, one CUDA, one corpus,
one fuzz and two repeatability; each GPU invocation contains 72 cases
independently, tags H4 and uses `timing_method="not-timed"`. The wgpu
record carries its post-dispatch `backend_name` per case and identifies
`environment.backend="wgpu"`; the CUDA record carries
`environment.backend="cuda"`. Both CUDA and wgpu per-case records retain
`dlpack_devices` for all three output capsules; the wgpu record
additionally retains `backend_name` read after its kernel call. The
run-closure validator rejects a
mismatched label/backend pair before manifest generation. The two
extension hashes intentionally need not match; the git source SHA must.

Every invocation reserves a fresh direct child of the raw root, writes one
`<mode>_<label>.json` result using `write_result`, and writes a metadata
sidecar. GPU metadata declares `timing_method="not-timed"` under campaign
amendment 2. The driver checks closure for `EXP-001-r1`, calls
`append_manifest`, then `verify_manifest`. A nonzero operational exit or
incomplete directory is logged as an abort; it is never repaired in place.

E3 logs the execution order above, UTC starts/ends, operator, build and
environment evidence, every directory, every failed attempt and anomalies.
Its first line identifies the approved pre-registration freeze SHA.
No hypothesis verdict or statistical adjudication is computed at E3.

## 6. Variables and controls

**Independent:** model, coupling, integrator, oscillator count, step count,
timestep, coupling/model parameters, explicit initial state and backend.
**Dependent:** native/corrected/sensitivity per-array pass flags, maximum
absolute/relative errors, failed/total elements, paired coherence summaries,
validity flags and repeatability bytes/digests.

Identical explicit inputs and parameters feed both arms. No separate
initial-state RNG, post-result model substitution, changed guard, changed
tolerance or tuned horizon is allowed. The corpus/spec/stream and reference
pins are controls, not outcome selectors. Sequential reference substitution
prevents a corrected reference from leaking into the native arm.

The only corrected reference is the registered measurement instrument; PRIN's
Rust implementation is the implementation under test. Metric reductions
remain those of each respective implementation. H2b always uses the native
reference, so the reference change used to explain H1/H2a cannot silently
change its estimand.

N=1 mean-field behavior, RK45, exponential/Jacobian and single-step
`_torch_compat` guard differences noted in the correction audit remain
outside this population. This experiment does not close those dispositions,
DV-001, DV-003, DV-036 or DV-040.

## 7. Sample plan and statistics

- **Seeds:** the only case-generation pair is **`(counter=0, key=1)`**,
  directly through `prin._prin_core.Seed`. All six implemented invocations
  record `(0,1)`; corpus/kernel-path/H3 consume stored inputs and perform
  no new
  random draw. There is no optional second fuzz batch.
- **Sample-size exception for E2 review:** deterministic H1/H3/H4 exhaust
  their registered populations. H2 uses one fixed stream with 1,000 case
  draws rather than ten independent experiment replications. This preserves
  the correction's precisely identified population. H2b uncertainty is over
  contributing cases in that ensemble; it does not estimate variation over
  independently rerun campaigns. E2 must explicitly approve this justification
  under campaign §6.3 / Experimentation Standards E1 item 8.

  **E2 decision (2026-09-28 UTC): APPROVED** by MichaelMaillet. This is a
  targeted verification of a correction against the exact previously-failing
  population, not a fresh discovery study; re-testing that identified
  population is the relevant confirmatory evidence for "did the fix work,"
  and no result is reused as new measurement (§1). See `e2-review.md` §2.
- **Deterministic rules:** H1/H2a/H3/H4 have no significance test. Counts,
  registered denominators, absolute/relative error maxima and distributions
  of per-case/array maxima are reported. A statistic cannot rescue a breach.
- **H4:** two separately manifested runs of the same 72 case IDs, 72 CUDA
  and 72 wgpu, with the same three f32-derivative tolerances and CPU
  reference. Each backend must supply its full valid denominator for a
  combined H4 confirmation; no pooling.
- **H2b unit:** one equal-weight paired summary per valid case with
  `n_steps > 20`, separately for each metric:
  `mean(produced[21:] - native_reference[21:])`. Serial time points are
  never treated as independent observations. Raw paired metric arrays,
  arm means and paired summaries remain in the result JSON.
- **Completeness:** all 1,000 cases must be valid for H2b inference; any
  case abort makes H2b inconclusive. At least **30** contributors are
  required per metric. No additional samples are drawn to reach this floor.
- **Interval:** the existing Rust-backed
  `prin.y4q1_tools.bootstrap_ci`, **10,000** resamples, **95%** CI,
  `alpha=0.05`. Seed argument **12455822396014146421** is exactly
  `Seed(0,1).next_u64()` from a fresh analysis stream. The Rust implementation
  uses its existing bootstrap-domain key `0x626f6f74`. Both metrics use this
  same deterministic resampling seed; no new RNG implementation is added.
- **Decision per metric:** `CONFIRMED` iff `-margin < CI_low` and
  `CI_high < margin`; `REFUTED` iff `CI_low > margin` or
  `CI_high < -margin`; otherwise **`INCONCLUSIVE`**, including a touching or
  overlapping boundary. Invalid/non-finite intervals abort analysis.
- **H2b overall:** refuted if either metric is refuted; confirmed only if
  both are confirmed; inconclusive otherwise.
- **Effect sizes and tests:** report paired mean difference with its CI,
  plus descriptive Cohen's d and two-sided Welch test from the existing
  Rust-backed APIs. The latter do not gate equivalence; undefined
  descriptive statistics are `null` with their names recorded, not zero.
- **Multiplicity:** two per-metric comparisons, with joint confirmation
  requiring both; the campaign's `>2` Holm-Bonferroni trigger does not
  apply. No extra confirmatory subgroup family is introduced.

The three-way H2b rule deliberately differs from the predecessor's rule
that refuted any interval not wholly inside the margin. Failure to establish
equivalence is not necessarily evidence of a non-equivalent mean. This
change is prospective in a new draft, subject to E2 review; it does not
reinterpret the old H2b verdict. The implementation is
`exp001_r1_driver.adjudicate_h2b`, tested with synthetic interval boundaries.

**E2 decision (2026-09-28 UTC): APPROVED** by MichaelMaillet. The three-way
rule is standard TOST-style equivalence-test logic: it correctly separates
"the data fail to demonstrate equivalence" (inconclusive) from "the data
demonstrate non-equivalence" (refuted), which the predecessor's binary rule
conflated. See `e2-review.md` §2.

## 8. Analysis plan

Before E4, commit the r1-specific analysis/renderer under this record's
`analysis/` directory, as required by campaign §7.4. It must use the
registered driver adjudicator and the following rules; the old EXP-001
analysis module is pinned to its own four original runs and must not be
retargeted or imported as a source of r1 verdicts.

1. Read only an explicit E3 run index, not a `RUN-*` glob. Verify each run
   manifest and sidecar, experiment/session identity, code SHA, protocol
   revision, seed, backend/dtype, input fingerprints, full case inventory
   and uniqueness. Reject missing/extra/duplicate cases and non-finite
   scientific fields. Abort an invalid analysis instead of inferring a
   result from a partial or mixed experiment. An admissible H4 analysis
   requires **six distinct r1 run IDs overall**, including exactly one
   `r1-kernel-path-wgpu` and one `r1-kernel-path-cuda` label, separate
   manifest-verified environments, per-case positive backend proofs, and
   two E3 build-log extension hashes associated with those backend labels
   on **one campaign execution source SHA R**, plus the
   distinct, already-merged green-main baseline M recorded
   in the E3 log; the hashes need not match
   across feature variants. For each GPU case, require exactly three
   stored `dlpack_devices` (`dphase`, `damplitude`, `dfrequency`), each
   `cuda` in the CUDA run and `cpu` in the wgpu run; require the wgpu
   `backend_name` to start with `wgpu`. Absent or conflicting proof
   invalidates that case/run, never confirms H4. Reject an extra,
   duplicated, mismatched or unverified run — including any
   `environment.git_commit` that differs from `R` or a run ID
   whose `<sha>` does not prefix `R`.
2. Re-evaluate each native/corrected/sensitivity decision from its retained
   per-array records. Recompute H2b's registered summaries from the stored
   paired metric arrays before applying the committed statistical helper.
   Do not re-run trajectories to render a report.
3. **H1:** any valid unexplained breach refutes; otherwise confirm only
   with 504 valid accepted cases; incomplete valid coverage is inconclusive.
4. **H2a:** any valid eligible unexplained breach refutes; otherwise confirm
   only with 978 valid accepted eligible cases plus all 22 valid registered
   characterizations. A missing/aborted sensitivity witness cannot reduce
   the registered denominator and yield confirmation.
5. **H2b:** apply §7 with all 1,000 cases accounted for; the 22 valid
   characterized cases remain eligible contributors by their step count.
6. **H3:** require both runs' metadata to validate independently and all
   14 cases in each to be byte-identical internally. Compare their result
   projections after removing only `environment`, `config.out_dir` and
   any per-run `run_id`; no scientific field or array digest is removed.
   Any valid mismatch refutes; missing/aborted coverage is inconclusive.
7. **H4:** validate both complete 72-case inventories and their per-case
   backend proofs separately; E4 verifies the retained per-case
   `dlpack_devices` keys/values and the wgpu `backend_name`; the live
   driver already rejected any wrong export/backend before publishing the
   result. E4 verifies each stored `comparisons` entry (`dphase`,
   `damplitude`, `dfrequency`, `within_tolerance`, `failed_count`, and
   error maxima) against the registered decision rule and the complete
   72-case inventory for each backend. The E3 driver computed the
   unchanged `rtol=1e-5, atol=1e-6` checks before publication; it retains
   these comparator records, not the raw derivative arrays. E4 must not
   claim an independent numerical `isclose` re-evaluation from absent raw
   arrays or run any new kernel to construct one. One valid breach on
   either backend refutes (D1);
   confirmation requires all 72 non-aborted comparisons on **both**
   backends; missing/aborted coverage without a valid breach is
   inconclusive. Never relabel CUDA as wgpu or pool the case counts.

Produce these fixed outputs under
`DOCS/test_and_benchmark_results/EXP-001-r1/`:

| Output | Required contents |
|---|---|
| `summary.json` | Verdicts, exact denominators, native/explained/characterized/failed/aborted counts, per-metric H2b statistics, repeatability result, required backend coverage, explicit input manifest digests |
| `summary.md` | Human-readable hypothesis table and expected-versus-observed table, using deterministic `prin.reporting` rendering with fixed generation time |
| `case-comparisons.json` | Every registered case and its native/corrected/sensitivity comparison evidence, including every breach and abort |
| `error-distributions.json` | Sorted per-case/array maximum absolute and relative errors, separated by native/corrected/reference-sensitivity and eligible/characterized populations |

No new figure is needed for this parity experiment. Regenerate the tables
through `prin.reporting`; commit the renderer and its tests before analysis.
Generate `report-manifest.json` in this record with the SHA-256/size of every
output. A clean regeneration from the fixed input index must reproduce all
digests. The E5 report lists each input run and manifest digest and the
output manifest digest.

E5 reports every hypothesis outcome, the expected-versus-observed table,
protocol deviations, explicit exploratory material, limitations, authorship
and maintainer verification. Any extra subgroup, distributional-distance or
phase-boundary analysis is exploratory and cannot change these verdicts.
DV-040 remains open: locally scan/type-check any future analysis module
under the record root and place its tests in the CI-covered `tests/` tree.

## 9. Resource budget

The inherited campaign limits are **8 CPU hours**, **2 GPU hours** and
**3 hosted-CI hours** for EXP-001, with an **8 MiB** tracked allocation and
the unchanged **64 MiB campaign-wide** cap. No hosted campaign run is
scheduled. The proposed r1 CPU work is expected to take 30–90 minutes,
CUDA minutes; these are planning estimates based on small bounded
populations, not measurements from a pilot.

**Storage needs explicit E2 disposition.** At E1 the original four run
directories occupy **6,208,871 bytes**, measured from file sizes only.
There are no other campaign run directories. The inherited 8 MiB shared
allocation therefore has **2,179,737 bytes** left. The old amendment-6
waiver covers the original fuzz artefact, not an automatically enlarged
new result.

| Proposed allocation for E2 review | Limit |
|---|---|
| New r1 tracked run artefacts — all six registered runs, including manifests | 8 MiB total |
| Shared `benchmarks/results/EXP-001/` allocation | 16 MiB total, explicitly including the original runs |
| New r1 fuzz run | 6 MiB exception to the generic 2 MiB per-run rule |
| Other r1 runs, including the wgpu kernel-path leg | 2 MiB each, still bounded by the r1 aggregate |
| Campaign-wide tracked artefacts | 64 MiB unchanged |
| Generated reports / optional untracked diagnostics | 64 MiB working-space estimate; authoritative decisions remain in tracked JSON |

This table is a **request, not an amendment**. Campaign plan §14.2 requires
a dated maintainer-approved budget/storage row before the expanded allocation
may be used. E2 must also account for original execution time against the
shared CPU/GPU allocation; anticipated r1 work does not waive cumulative
caps.

**E2 decision (2026-09-28 UTC): APPROVED as requested** by MichaelMaillet
(campaign plan §14.2 amendment #7). The driver now enforces: **16 MiB**
shared `EXP-001/` root (`RAW_ROOT_CAP_BYTES`, covering the original runs and
all new r1 runs together); a separate **8 MiB** cap on new r1 runs alone
(`R1_ROOT_CAP_BYTES`, checked only against `RUN-*-r1-*/` directories,
including the sixth wgpu kernel-path run); a
**6 MiB** per-run exception for the r1 fuzz leg (`FUZZ_RUN_CAP_BYTES`); and
the generic **2 MiB** per-run cap (`RUN_CAP_BYTES`) for every other r1 run,
the wgpu leg included.
The campaign-wide 64 MiB cap is unaffected. Each limit is independently
tested (`tests/test_exp001_r1_driver.py`); the run set this pre-registration
proposes is authorized against the storage caps alone. Storage was
approved at E2; the follow-up E2 wgpu-protocol decision and DV-043's
main/nightly closure remain open. It estimates the exact
writer serialization plus a conservative 64 KiB manifest reserve before
publication. Retain abandoned/aborted directories and do not reclaim the
original evidence to make room. See `e2-review.md` §3.

## 10. E2 handoff and execution gates

E1 delivers this complete **draft**, the implemented CPU/CUDA measurement
driver, synthetic tests and entry/validation record. It does not approve or
freeze the protocol and does not create E3/E4/E5 artefacts.

E2 must:

1. Independently review the hypotheses, unchanged tolerance machinery,
   DV-007 positive explanation, fixed 22-case handling, single-stream
   sample justification and prospective H2b three-way rule. Record
   MichaelMaillet's approval by name and date only after that review.
2. Obtain an independent follow-up review and MichaelMaillet's explicit
   dated approval for the now-implemented wgpu kernel-path leg in §2 —
   the tested driver support and the two-build order — before freeze.
   The original CUDA driver alone does not discharge it.
3. Approve or revise the **storage budget request** through campaign §14.2,
   record the dated amendment and align the driver's scoped limits.
   Reducing cases or dropping evidence to fit storage is not permitted.
4. Review the synthetic driver validation, Snyk evidence and any local gate
   limits in `e1-handoff.md`. Any remaining machinery work is a normal,
   reviewed pre-execution amendment; no r1 pilot or outcome inspection is
   permitted to choose thresholds, inputs or exclusions.
5. Before E3, ensure the exact freeze/driver commits, clean extension build,
   required main CI and latest nightly disposition are recorded — including
   DV-043's actual merged `main` SHA (a hotfix-branch SHA does not
   substitute) and one green `nightly.yml` `bench-regression` after that
   merge. Before the first `RUN-`, incorporate the green-main
   baseline M into the committed r1 execution checkout R
   and record both full SHAs; all six `environment.git_commit`
   values and RUN IDs must identify R, not M. Verify
   a clean tracked-source state at R. The last
   pre-registration edit F is independently recorded
   on line 1 of `log.md` at freeze.
   New numeric baseline changes follow campaign §10.2; do not
   assume E1's green merge remains current. The pre-existing PSR-039
   deviation-ledger CI gate (DV-044), found at the follow-up
   E2 amendment, must also be corrected and independently
   reviewed; its failure is not an E3 waiver. At E5, list the
   exact E2 baseline-to-E3-main code diff
   (`149cf2d..M`, the main baseline delta) as a protocol
   deviation — identifying `R` as the experiment's distinct
   source SHA, not a second mid-experiment main change — and report
   fresh results of both 72-case H4 GPU regression legs.
   A later numeric edit before E3 reopens the baseline entry
   check; it cannot be absorbed mid-experiment.

The campaign block on 0159 and downstream sessions remains in force until
the r1 E5 non-reversal condition or a Project Plan §8.3 amendment is
satisfied. Neither correction merge, E1 completion nor E2 approval alone
releases it.

### Original E2 outcome (2026-09-28 UTC; follow-up approval above and in e2-review.md §8)

Items 1, 3, 4 above are **satisfied**: independent review completed (item
4; see `e2-review.md`), the storage budget approved as requested (item 3;
campaign plan §14.2 amendment #7), and the sample-size/H2b-rule
justifications approved (item 1). Item 5 (freeze/build/CI/nightly currency)
is carried forward to E3 start, unchanged from E1's own instruction. At the
original E2 exit, item 2 was unsatisfied and DV-041's capability fix had not
yet merged. The follow-up proposed amendment now has live-tested, synthetic
wgpu support; independent review and explicit maintainer approval of the
revised H4/two-build protocol remain outstanding. This pre-registration
**does not freeze** and **E3 does not start**; the follow-up state is
recorded here.

The original three E2 approvals remain valid. The
follow-up H4/two-build **method** is now approved
by MichaelMaillet (2026-09-29 UTC) with the
non-author technical review disclosed in
`e2-review.md` §§6–8. Item 2 is closed as a
*protocol-design* gate only. Item 5 and
DV-043/DV-044 remain OPEN: no approved new
main baseline `M`, clean campaign execution
checkout `R`, green next nightly, first
`RUN-` directory, freeze, E3 execution or
scientific verdict exists yet. The separate
non-author E2 delta check of the corrected
M/R/F roles completed 2026-09-29 UTC with no
findings (`e2-review.md` §8). No prior
EXP-001 result is changed.
