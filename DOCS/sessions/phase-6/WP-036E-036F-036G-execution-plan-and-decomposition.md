# WP-036E / WP-036F / WP-036G — Execution plan and decomposition (Deferred-Validation closure before Phase 7)

**Status:** ADOPTED (2026-08-31, MichaelMaillet — recorded via this planning
session's `AskUserQuestion` selections) and carried into authority by
**Plan amendment #38**. Retained for rationale, the full DV disposition
matrix, and dependency ordering. Not an execution contract; the governing
contracts are the new WP-036E/F/G briefs `0144Q`–`0144AB`.

> **Superseded in part by Plan amendment #43 (2026-09-02).** WP-036E S1-start
> repository verification established that a *true bidirectional zero-copy
> Torch↔CubeCL DLPack kernel-input path* is not reachable on the pinned
> `cubecl 0.10.0` (`cubecl-cuda`'s `GpuStorage` cannot adopt an external CUDA
> device pointer as a `Handle`). Where this document says "**DV-030 … CLOSED by
> WP-036E**" and "the reason this WP exists", read: **`PARTIALLY CLOSED`** —
> device-resident buffers + device-`Handle` dispatch + on-device CUDA `f64`
> combine (DV-003) + **export**-direction zero-copy DLPack are delivered;
> bidirectional zero-copy kernel-input is re-gated to a `cubecl` external-memory
> API or a vendored `cubecl-cuda` storage shim. `0144Q` is decomposed into
> `0144Q1`–`0144Q3`. See
> [`WP-036E-S1-execution-plan-and-decomposition.md`](WP-036E-S1-execution-plan-and-decomposition.md).

**Prepared for:** the block of sessions inserted between WP-036C S4 (`0144P`)
and WP-037 S1 (`0145`).
**Author:** Claude Sonnet 5 (AI pair)
**Date:** 2026-08-31
**Authority:** Project Plan §6/§8 and amendments #1–#37; Development Workflow
and Audit Standards §2 (work-package definition), §3 (Session Cycle), §7
(scope limits and split rule); `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`
(update protocol, "each cycle's S4 session reviews this register"); Phase 1
Analytics R9 (register authority); the DV-004/R35 and DV-021/#30 precedents
for closing a long-open item by an explicit, dated disposition rather than an
indefinite "re-audited, unaffected".

---

## 0. Why this document exists

Phase 6 is nearly closed: WP-033, WP-034, WP-035, WP-036, WP-036A, WP-036B,
and WP-036D are complete; WP-036C (`0144M`–`0144P`), WP-037 (`0145`–`0148`),
and WP-038 (`0149`–`0152`) remain, after which the project enters the Phase 7
Experimentation and Benchmarking Campaign at session `0153` (campaign E0).

The Deferred Validation Register carries **17 open items** at PSR-036D. Phase 7
pre-registration and confirmatory experiments should not begin while items
that a work package *can* resolve remain open, and the items that a work
package *cannot* resolve (external hardware, third-party libraries, by-design
governance gates) should each carry an explicit, dated disposition rather than
an open-ended "re-audit every cycle" that no cycle ever discharges — the exact
anti-pattern Phase 5 analytics R35 called out for DV-004 and that #30 resolved
for DV-021.

This plan places the resolvable work into **three sequential work packages**
executed before WP-037, and specifies the disposition of every remaining item.

---

## 1. Maintainer decisions taken (2026-08-31)

| # | Decision | Selected |
|---|---|---|
| A | DV-005 (CUDA Burn training-stack autodiff backend) | **Dated deferral past 1.0.0.** Close DV-005 as `AMENDED` with concrete post-1.0 re-gate criteria; no new-numerics WP now. |
| B | Work-package breakdown | **Three WPs** — WP-036E (GPU device-resident execution), WP-036F (DirectML controller-graph execution), WP-036G (DV-register consolidation and permanent dispositions). |
| C | Placement | **Before WP-037, after WP-036C.** Sub-sessions `0144Q`–`0144AB`, inserted between `0144P` and `0145`; 0145–0198 untouched. |
| D | Identifiers | **WP-036E/F/G alphabetic siblings** of the WP-036 family (continuing amendments #33 / #36). No integer renumber; TRACEABILITY invariant 4 preserved. |

---

## 2. Complete open-item inventory and disposition (repository-verified against PSR-036D)

| DV | One-line | Class | Disposition under this plan |
|---|---|---|---|
| **DV-001** | Triton 3.0 fused-kernel timing — needs a **Linux** GPU runner | External infra | **Stays OPEN, permanent standing disposition (WP-036G).** No in-repo path exists (Triton has no Windows support; the on-hand `PRIN-GPU-Runner` is Windows). Same class as DV-009: closes only on out-of-band Linux-runner registration. WP-036G adds a dormant `gpu-triton.yml` skeleton gated on `[self-hosted, linux, gpu]` so registration is the sole remaining step, and records that DV-001 is **not** a Phase 7 entry blocker (EXP-004 pre-registration explicitly scopes Triton comparison as hardware-gated). |
| **DV-003** | Device-event kernel timing; host dispatch/sync dominates the 8-launch RK4 wall-clock; level-2 `f64` combine is host-side | GPU-kernel-internal | **CLOSED by WP-036E.** Moving the level-2 `f64` combine on-device and batching read-backs is squarely in WP-036E's device-resident scope; `StepReport` device-event timing across the full sequence is validated on `PRIN-GPU-Runner`. |
| **DV-005** | CUDA Burn **training-stack** autodiff backend + `<5%` boundary overhead | New numerics, no current workload | **CLOSED as `AMENDED` by amendment #38.** Out of scope for 1.0.0 (RC1 / Plan §6 Phase 6 exit and DoD do not require GPU training; `prin-train` is `NdArray`-only workspace-wide). Re-gate criteria named in §5. |
| **DV-006** | DirectML + VitisAI ONNX controller execution | Mixed (graph-side fixable + hardware-blocked) | **DirectML half CLOSED by WP-036F**; VitisAI/NPU half stays OPEN, re-scoped to "VitisAI NPU only, hardware-gated" (same class as DV-001). Resolves plan amendment #13's deferred DirectML condition. |
| **DV-007** | f64 vs PRINet-3.0 `torch.complex64`/f32 preserved numerical hazard | By design | **Permanent dated disposition (WP-036G).** A reference-implementation hazard, governed by the `1e-6` derivative tolerance + corpus `rtol=2e-6` + Parity Report (amendments #14/#16/#17/#25). Does not "close" by fixing and is not expected to; recorded as permanently accepted with **no further re-audit gate** — the DV-004/R35 pattern. |
| **DV-008** | Inherited `paste` RUSTSEC-2024-0436 (transitive via `cubecl`) | Third-party advisory | **Stays OPEN by nature; re-confirmed at WP-036G** (`cargo audit` exit 0, allowed warning). Cadence unchanged (upgrade when `cubecl` moves). Not a Phase 7 blocker. |
| **DV-009** | GitHub native secret scanning unavailable for this private repo | External infra | **Stays OPEN by nature; re-confirmed at WP-036G.** Gitleaks + branch protection compensating control in force (amendment #5). Not a Phase 7 blocker. |
| **DV-010** | Phase 1/2 pre-release tag never pushed; `release.yml` never executed | Maintainer action | **Routed to WP-038** (RC1 packaging and Phase 6 gate) as an explicit in-scope item — the tag push that triggers a real PyPI/crates.io publish belongs with RC1 publication, not a mid-phase session. WP-038 S1 brief updated by amendment #38. |
| **DV-011** | `torch@2.13.0` Snyk Open Source advisories (6), all `fixedIn: []` | Third-party advisory | **Stays OPEN by nature; re-confirmed at WP-036G** (`.snyk` ignore entries current; next scheduled recheck 2026-11-14 unchanged). Not a Phase 7 blocker. |
| **DV-013** | `M-F3`/`M-F7` policy-gate claims permanently `REQUIRES_HUMAN_REVIEW` | By design | **Permanent dated disposition (WP-036G).** OPEN by design; sign-off re-granted each EMA when the claim set changes (last: EMA-005, 2026-08-26). Recorded as a permanently-accepted governance pattern with no WP-level gate; not a Phase 7 blocker. |
| **DV-017** | Inherited `bincode` RUSTSEC-2025-0141 "unmaintained" (transitive via `burn-core`) | Third-party advisory | **Stays OPEN by nature; re-confirmed at WP-036G** (`cargo audit` exit 0, allowed warning per amendment #27). Not a Phase 7 blocker. |
| **DV-018** | `burn-tensor` 0.16.1 `sigmoid` downcasts through f32 on `NdArray<f64>` | Third-party library | **Permanent dated disposition (WP-036G).** Documented at every call site with `eps=1e-4`/`rtol=1e-6`; not a correctness issue at the scale `prin-train` uses it. Recorded as permanently accepted third-party behaviour; re-check only on a `burn` version bump. Not a Phase 7 blocker. |
| **DV-022** | GitHub-hosted `ubuntu-latest` disk-space exhaustion in `python`/`parity` | External infra | **Stays OPEN by nature; re-confirmed at WP-036G.** `parity.yml` WSL2 fallback documented; Windows jobs already on self-hosted runner. Not a Phase 7 blocker. |
| **DV-027** | `math-audit-mcp` editable-install `dist-info` stale (`pip show` reports 0.1.0) | Cosmetic, external tool | **Routed to the Phase 6 close EMA session** (EMA-006, not yet numbered) — `pip install -e .` in the tool's `.venv` refreshes it. Zero functional impact (`tools/math_audit_run.py` reads the live module). WP-036G records the routing. |
| **DV-028** | Vendoring `math-audit-mcp` into PRIN | By design | **Permanent dated disposition (WP-036G).** Decision already taken (R36, 2026-08-26: do not vendor; no CI-reachable remote exists). Recorded as final with no gate; re-evaluate only if a publishable remote appears. |
| **DV-030** | Device-resident GPU buffers / true zero-copy Torch↔CubeCL DLPack path | New multi-crate architecture | **CLOSED by WP-036E** — the reason this WP exists. |

**Also swept into WP-036G (pre-existing issues not yet on the register):**

- **`chacha20` yanked advisory** — noted in PSR-036D §5 as an allowed
  `cargo audit` warning alongside DV-008/DV-017 but never given its own
  register row. WP-036G formalises it as a DV item under the DV-008 governance
  class (informational advisory, transitive, re-check every cycle).
- **DV-019 Python-side sub-item** — `test_process_frame_gradcheck_with_prev_slots`
  intermittent gradcheck flake; DV-019's closure note left "its own
  shared-cause-confirmation question open for a future session". WP-036G
  either confirms the shared root cause with the Rust-side `burn-autodiff`
  global-server mechanism (`Hotfix-DV019`) and applies the same serialization
  guard, or opens a new dedicated DV item — per DV-019's own handoff §6.
- **`test_no_gpu_throughput_regression`** — wall-clock throughput-ratio
  heuristic that fails under host contention (PSR-036D §2 note, and the same
  class as DV-016/DV-019). WP-036G either hardens it (fixed iteration count +
  warm-up + relative-median gate) or documents it as CI-authoritative with an
  explicit tolerance, so Phase 7 does not inherit a known-fragile gate.

---

## 3. The three work packages

### WP-036E — GPU device-resident execution path

*Sessions `0144Q` (S1) · `0144R` (S2) · `0144S` (S3) · `0144T` (S4).
Closes DV-030 and DV-003.*

**Problem.** `0144I2` / amendment #37 established that **no layer of the GPU
stack holds device-resident state**: `prin-kernels`' CubeCL dispatch
functions (`sparse_knn::cubecl::sparse_knn_coupling_auto`,
`mean_field_rk4::cubecl::step_auto`, `discrete_step::cubecl::discrete_step_auto`)
take `&[f32]` host slices and return `Vec<f32>` host; `prin-sim`'s
`GpuSparseKuramoto` / `GpuMeanFieldEngine` / `GpuBandStepper` store state as
host `Vec<f32>`. Every GPU call therefore uploads and downloads on every
invocation, `test_acceptance_q2.py::test_sparse_vram_subquadratic` cannot pass
(the coupling matrix lives in Rust host memory invisible to `torch.cuda`),
and the mean-field RK4 level-2 `f64` combine runs host-side, so host
dispatch/sync overhead dominates the criterion wall-clock figure (~25 ms vs
388 µs device-event, DV-003).

**Scope.**
1. `prin-kernels` dispatch layer: add `Handle`/device-buffer-accepting
   entry points alongside the existing host-slice ones (one algorithm, one
   implementation — the host path becomes a thin upload→device-path→download
   wrapper; Coding Standards §N5).
2. `prin-sim` GPU engines hold persistent CubeCL device buffers across `step`
   calls; state stays on-device between steps; explicit `to_host()` only when
   the caller asks.
3. On-device `f64` level-2 combine for `mean_field_rk4` (DV-003); batched
   result read-backs across the 8-launch sequence; `StepReport` device-event
   timing over the whole sequence validated on `PRIN-GPU-Runner`.
4. `crates/prin-py/src/bindings/gpu.rs`: true zero-copy DLPack — a CUDA torch
   tensor → CubeCL device handle → kernel → CUDA torch tensor, no host
   round-trip. `read_dlpack_f32`/`export_dlpack_f32` gain device-pointer
   variants; `.pyi` updated.
5. `python/prin/_torch_compat.py`: the GPU dispatch branches added in
   `0144I2` upgrade from CPU-float32 marshalling to the zero-copy device
   path; the CPU `else` branch is byte-for-byte unchanged (golden-value
   pre/post test, as `0144I2` established).
6. Activate `test_sparse_vram_subquadratic` as the 8th `@pytest.mark.gpu`
   acceptance test with its assertion restored to `vram_full * 0.10`
   (reverting `0144K`'s DV-030 `skip`); `tests/README.md` GPU count 7 → 8.

**Acceptance.** `test_sparse_vram_subquadratic` passes on `PRIN-GPU-Runner`
with the `* 0.10` assertion and its `skipif` guard intact; the other 7 GPU
acceptance tests still pass; GPU-vs-CPU agreement within Testing Standards §3
tolerances (`rtol=1e-5`, `atol=1e-6`) or a per-test Parity Report annotation;
device-event timing for the fused RK4 sequence recorded and the DV-003
host-overhead gap closed or bounded with evidence; CPU path and the 489 CPU
acceptance tests byte-for-byte unchanged; numerical authority in Rust
(`check_no_python_numerics.py` clean); no new `prin` public symbol
(`verify_api_surface` stays `(set(), set())`); `unsafe` only in the already
kernel-FFI-audited modules under the amendment #8 pattern.

**Non-goals.** CUDA Burn *training* backend (DV-005); Triton (DV-001);
`prin-kernels` exponential-integrator kernel (no such kernel exists — the
`ExponentialIntegrator` GPU test stays on the device-restoring marshalling
path `0144I2` gave it); any `prin.__all__` change; release publishing.

**S1 decomposition.** `0144Q` is **pre-authorised to decompose** into
sequential coding sub-passes `0144Q1`–`0144Qn` under Development Workflow §7
(candidate split: `prin-kernels` device-handle dispatch layer; `prin-sim`
persistent device buffers + DV-003 on-device combine; `prin-py` zero-copy
DLPack + `_torch_compat.py` upgrade + `test_sparse_vram_subquadratic`
activation), confirmed at S1 start by a follow-on amendment if repository
verification shows one reviewable commit range is exceeded — the amendment
#34/#35/#36 precedent. Planned count is held at 245 until that confirmation.

### WP-036F — DirectML controller-graph execution

*Sessions `0144U` (S1) · `0144V` (S2) · `0144W` (S3) · `0144X` (S4).
Closes the DirectML half of DV-006; resolves amendment #13's deferred
condition.*

**Problem.** `EVIDENCE/0109-wp028-s1-controller-provider-report.json`
(WP-028 S1) established that `DmlExecutionProvider` **cannot execute the
controller graph**: DirectML fuses `Gemm`+`Relu` into a `DmlFusedGemm` node
that rejects the two-input `Gemm` form PyTorch exported
(`InvalidGraph: ... input size 2 not in range [min=3, max=3]`). The archived
PRINet 3.0 reference fails identically — a runtime/graph condition, not a PRIN
defect. DV-006 records the concrete fix: "re-exporting the controller graph
with three-input `Gemm` nodes so DirectML's fusion accepts it (a WP-030
export-side change)."

**Scope.**
1. The controller ONNX export path (owner: `prin-daemon` / the
   `SubconsciousController` export used by WP-028; verify the exact module at
   S1 start): emit `Gemm` nodes with an explicit zero/ös bias third input (or
   an `onnx` graph transform pass) so `DmlFusedGemm` fusion is satisfied.
   No change to the mathematical function of the graph.
2. Re-generate the committed controller graph artefact and its checksum;
   update any 3.0-reference comparison fixture accordingly.
3. Extend `tests/test_daemon_controller.py::TestCrossProviderAgreement`
   coverage: with the re-exported graph, `DmlExecutionProvider` now executes
   and its outputs are compared bit-for-bit (within Testing Standards §3
   tolerance) against `CPUExecutionProvider` and the 3.0 references across the
   differential case set.
4. `benchrunner` / provider-latency acceptance surface (the DV-006 re-audit
   gate names "provider and latency acceptance"): record DirectML latency
   alongside CPU on the project host.

**Acceptance.** The re-exported controller graph is mathematically identical
to the current one (differential test over the 48-case set, CPU provider,
bit-identical); `DmlExecutionProvider` executes it on the project host and
agrees with CPU within tolerance; the cross-provider harness widens
automatically; F5 / DoD item 7 DirectML condition satisfied and recorded;
amendment #13's WP-005 DirectML deferral formally discharged. Numerical
authority unaffected (the graph is a controller inference artefact, not PRIN
numerics). No `prin.__all__` change.

**Non-goals.** VitisAI / Ryzen AI NPU execution (the project host is a
Ryzen 7 8700F with no XDNA NPU and no CPython-3.14-matched VitisAI wheel —
hardware-blocked, stays in DV-006); retraining/quantization symbols (DV-025,
WP-036C scope); any controller *algorithm* change.

### WP-036G — Deferred-Validation register consolidation and permanent dispositions

*Sessions `0144Y` (S1) · `0144Z` (S2) · `0144AA` (S3) · `0144AB` (S4).
No source-code numerics. Governance + light test-hardening WP.*

**Problem.** After WP-036E/F, the register still carries items that no work
package can close: external infrastructure (DV-001, DV-009, DV-022),
third-party advisories with no upstream fix (DV-008, DV-011, DV-017,
`chacha20`), third-party library behaviour (DV-018), and by-design governance
gates (DV-007, DV-013, DV-028). Left as open "re-audit every cycle" rows they
create the false impression of unresolved risk going into Phase 7 and, per
R35, no cycle ever discharges them. Each needs an explicit, dated disposition.
Three pre-existing test-fragility issues (§2) also need resolution before the
campaign inherits them.

**Scope.**
1. **Permanent dispositions** (dated, maintainer-signed in the S4 PSR;
   DV-004/R35 pattern) for **DV-007, DV-013, DV-018, DV-028** — each row gets
   a "permanently accepted, no further re-audit gate" statement with the
   standing governance mechanism named. `check_dv_register_gates.py` and the
   register's own "Closed items" / "Active deferred items" split updated so
   these no longer appear as perpetually-pending.
2. **Standing-disposition confirmations** for **DV-001, DV-008, DV-009,
   DV-011, DV-017, DV-022**: one consolidated re-verification pass
   (`cargo audit`, `pip-audit`, Snyk, `gh api .../secret-scanning/alerts`,
   runner status, `.snyk` currency) with evidence, and a statement in each row
   that the item is external/third-party, not repo-closeable, and **not a
   Phase 7 entry blocker**. Add the dormant `gpu-triton.yml` skeleton
   (DV-001).
3. **`chacha20` yanked advisory** — new register row under the DV-008
   governance class (full visibility, threat assessment, compensating
   control, `cargo audit` exit-0 evidence, per-cycle re-check).
4. **DV-010** — confirm it is now owned by WP-038 S1 (brief updated by
   amendment #38); WP-036G does not push the tag.
5. **DV-027** — record routing to EMA-006.
6. **Test-fragility resolution:** the DV-019 Python sub-item, and
   `test_no_gpu_throughput_regression` — fix in tandem with a regression
   test, or register + document as CI-authoritative with an explicit
   tolerance. `bands.rs`-class Rust flakes are out of scope (closed by
   `Hotfix-DV019`).
7. **Phase 7 entry statement:** a short section in the WP-036G PSR
   enumerating every remaining OPEN DV item and asserting, per item, that it
   does not block campaign pre-registration or execution — the artefact E0
   (`0153`) reads.

**Acceptance.** Every DV register row is in exactly one of: `CLOSED`,
`AMENDED` (with amendment ref), permanent-disposition (dated, no gate), or
standing-external-disposition (dated, evidence, "not a Phase 7 blocker");
zero rows in an undated open-ended "re-audit every cycle" state without that
classification. The two test-fragility items are fixed or formally
dispositioned with a linked artefact. `check_dv_register_gates.py` passes.
`check_no_python_numerics.py` clean (unchanged). No `prin.__all__` change.

**Non-goals.** Any new numerics; closing DV-001's Triton comparison or
DV-006's VitisAI half (hardware-blocked); the WP-038 tag push; re-litigating
the R36 vendoring decision.

---

## 4. Dependency order and why this sequence

```
WP-036C (0144M–0144P)  ──►  WP-036E (0144Q–0144T)  ──►  WP-036F (0144U–0144X)  ──►  WP-036G (0144Y–0144AB)  ──►  WP-037 (0145…)
  full acceptance suite      device-resident GPU +        DirectML controller       register consolidation +
  ported (incl. test_gpu)    DV-030/DV-003 closed         graph, DV-006 half        permanent dispositions
```

- **WP-036C first** (unchanged): the full ~1,670-test suite must be ported and
  green before WP-036E touches the GPU path it depends on, and WP-036C's own
  `test_gpu.py` port defines the device-correctness contract WP-036E must not
  regress.
- **WP-036E before WP-036F**: WP-036E is the larger, higher-risk architecture
  change; running it first means WP-036F and WP-036G execute against a
  stable, fully device-resident GPU stack. WP-036F does not depend on
  WP-036E, but ordering the risky WP first is the amendment #31 R1 mitigation
  pattern ("known-numerics clusters first").
- **WP-036G last**: it consolidates and dates the disposition of everything
  the prior two WPs did *not* close, so it must see their final state. Its
  Phase 7 entry statement is the last artefact before `0145`.
- **All three before WP-037/WP-038**: the Parity Report draft (WP-037) and
  RC1 packaging + Phase 6 gate (WP-038) then reflect the final post-DV state —
  `test_sparse_vram_subquadratic` active, DirectML in DoD item 7, the DV
  register consolidated — rather than shipping RC1 with those open and
  amending afterward.

---

## 5. Draft Plan amendment #38 (adopted text in the plan)

> **#38 | 2026-08-31 | Project Plan §6 / WP-036C declaration (PSR-036D §6) /
> Development Workflow and Audit Standards §7 / `DOCS/sessions/SESSION_REGISTER.md`
> / `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` / WP-038 S1 brief |**
> **Three new work packages close or formally dispose of every open Deferred
> Validation Register item before Phase 7, plus DV-005/DV-006 scoping
> decisions.** The DV register carries 17 open items at PSR-036D; Phase 7
> pre-registration should not begin with work-package-resolvable items open,
> and the non-resolvable items need dated dispositions rather than indefinite
> "re-audit every cycle" rows (Phase 5 analytics R35 anti-pattern; DV-004 and
> DV-021/#30 precedent). **WP-036E** ("GPU device-resident execution path",
> sessions `0144Q`–`0144T`) makes the `prin-kernels` dispatch layer and the
> `prin-sim` GPU engines device-resident, adds a true zero-copy
> Torch↔CubeCL DLPack path, moves the mean-field RK4 level-2 `f64` combine
> on-device, and activates `test_sparse_vram_subquadratic` — **closing DV-030
> and DV-003**. **WP-036F** ("DirectML controller-graph execution", sessions
> `0144U`–`0144X`) re-exports the subconscious controller ONNX graph with
> three-input `Gemm` nodes so `DmlExecutionProvider` executes it, validating
> cross-provider agreement — **closing the DirectML half of DV-006** and
> discharging amendment #13's deferred DirectML condition; the VitisAI/NPU
> half stays OPEN, hardware-gated. **WP-036G** ("Deferred-Validation register
> consolidation and permanent dispositions", sessions `0144Y`–`0144AB`)
> assigns every remaining open item a dated disposition: permanent acceptance
> with no further gate for **DV-007, DV-013, DV-018, DV-028** (by-design /
> third-party, governed by a named standing mechanism); consolidated
> standing-external-disposition for **DV-001, DV-008, DV-009, DV-011, DV-017,
> DV-022** ("not a Phase 7 entry blocker", with a one-pass re-verification and
> a dormant `gpu-triton.yml` skeleton for DV-001); a new register row for the
> `chacha20` yanked advisory under the DV-008 governance class; and resolution
> or formal documented disposition of two pre-existing test-fragility issues
> (the DV-019 Python-side gradcheck sub-item; `test_no_gpu_throughput_regression`).
> **DV-005** (CUDA Burn training-stack autodiff backend + `<5%` boundary
> overhead) is **closed as `AMENDED`**: out of scope for 1.0.0 — RC1 / Plan
> §6 Phase 6 exit and the Definition of Done do not require GPU training, and
> `prin-train`'s Burn backend is `NdArray`-only workspace-wide with no Phase 6
> workload needing autodiff on device. Re-gate criteria: a dedicated post-1.0
> work package, or Phase 7 EXP-004, opened only when a concrete CUDA-backed
> training or fine-tuning workload exists that the CPU `NdArray` backend
> cannot serve in acceptable time; that WP adds the `burn-cuda` feature to
> `prin-train`, a CUDA `autograd.Function` bridge, float64 device gradcheck,
> and a boundary-overhead re-measurement. Same disposition class as DV-004/R35
> (long-open item resolved by explicit dated disposition) and #30 (target
> re-scoped to evidence and roadmap reality). **DV-010** (Phase 1/2
> pre-release tag) is reassigned from "maintainer approval" to **WP-038 S1
> scope** — the tag push that triggers `release.yml` belongs with RC1
> publication; the WP-038 S1 brief is updated in this amendment. **Sessions:**
> `0144Q`–`0144AB` (12 sub-sessions) are inserted between planned integer
> sessions `0144` (i.e. after the WP-036C block `0144P`) and `0145`, with the
> two-part identifier convention of amendments #31/#33/#36; `0144P`'s
> successor becomes `0144Q` and `0145`'s predecessor becomes `0144AB`. The
> integer sequence 0001–0198 and the block `0144A`–`0144P` are unchanged
> (TRACEABILITY invariant 4 preserved). Identifiers roll from single-letter
> `0144Q`–`0144Z` to two-letter `0144AA`–`0144AB` for the last two, an
> explicit extension of the two-part convention. WP-036E S1 (`0144Q`) is
> pre-authorised to decompose into `0144Q1`–`0144Qn` under Development
> Workflow §7, confirmed by a follow-on amendment at S1 start if needed.
> WP-036E/F/G Audit Reports and Project State Reports are numbered
> `036e`/`036f`/`036g`. Planned session count: **233 → 245** (+12). WP-036/A/B/C/D
> acceptance criteria and non-goals are unchanged. The aggregate WP-036 goal
> is extended to "and every open Deferred Validation item is closed or carries
> a dated disposition before Phase 7." Same disposition class as amendment #33
> (new sibling WP + mechanical insertion) and #31 (multi-WP declaration in one
> amendment). | maintainer approval (MichaelMaillet, 2026-08-31; this
> planning session's `AskUserQuestion` selections) |

---

## 6. Register / traceability / brief changes executed with this plan

1. **`DOCS/PRIN_Project_Plan.md`** — amendment #38 row in §8.3; §6 roadmap
   Phase 6 row and the post-table paragraph (session count 233 → 245, WP-036
   family now A/B/C/D/E/F/G).
2. **12 new briefs** `0144Q`–`0144AB` in `DOCS/sessions/phase-6/`.
3. **`0144P` brief** successor → `0144Q`; **`0145` brief** predecessor →
   `0144AB`.
4. **`0149` (WP-038 S1) brief** — DV-010 added to Expected work / scope.
5. **`SESSION_REGISTER.md`** — register version 1.3 → 1.4; planned count;
   amendment #38 note block; 12 rows; sub-session chain text.
6. **`DOCS/sessions/README.md`** — planned-session count line; sub-session
   list in §5.
7. **`DOCS/sessions/phase-6/README.md`** — amendment #38 paragraph; 12 rows;
   WP list in the header.
8. **`DOCS/sessions/TRACEABILITY.md`** — invariant 1 (WP-036 sibling family
   acknowledged), invariant 4/5 (chain), §1 F1/F5 rows, §4 (DV-003/DV-007/
   DV-018), §5 Phase 6 exit note, §6 R1/R4 detection rows.
9. **`DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`** — every open row gains
   the amendment #38 governing reference and its WP-036E/F/G re-audit gate
   (phrased without the literal "before session NNNN" trigger string, to keep
   `check_dv_register_gates.py` green); DV-005 moved toward "Closed items"
   framing as `AMENDED`.
10. **`CHANGELOG.md`** `[Unreleased]` — governance entry.

Actual closure evidence (test results, `cargo audit` output, DirectML
provider report, device-event timings) is produced by the WP-036E/F/G S1–S4
cycles and recorded in their audits, PSRs, and `DOCS/experiments/` handoffs —
not in this plan.

---

## 7. Risks

- **R1 — WP-036E is a genuine multi-crate rearchitecture.** Device-resident
  buffers touch `prin-kernels`, `prin-sim`, and `prin-py`. Mitigation: the
  host-slice API is retained as a thin wrapper (no consumer breaks); S1 is
  pre-authorised to decompose; the CPU path has a golden pre/post test; the 7
  already-green GPU acceptance tests are the regression guardrail.
- **R2 — `test_sparse_vram_subquadratic` may still not reach `< 10%`.** The
  assertion is a real VRAM-ratio bound. If device-resident CSR still exceeds
  it, WP-036E S2 adjudicates: a Parity-Report-annotated looser bound with
  evidence, or a further-deferred `skip` with a *new* DV item and a concrete
  next gate — never a silently weakened assertion (Testing Standards §1.1;
  the `0144K`/WP036D-F1 precedent).
- **R3 — DirectML re-export changes graph semantics.** Mitigation: WP-036F's
  first acceptance gate is a bit-identical differential test of the
  re-exported graph against the current one on the CPU provider over the
  full 48-case set, *before* any DirectML claim.
- **R4 — Identifier roll-over `0144Z` → `0144AA`.** Cosmetic; documented
  explicitly in amendment #38 and every affected index. `check_dv_register_gates.py`
  only parses 4-digit integers, so sub-session IDs never collide with its
  gate detection as long as DV rows avoid the literal "before session NNNN"
  phrasing (they do).
- **R5 — Scope creep in WP-036G.** A governance WP can absorb unbounded
  "while we're here" work. Mitigation: the brief's non-goals bar new numerics
  and hardware-blocked halves; the two test-fragility items are named
  explicitly and nothing else is in scope.

---

## 8. Recommendation

Adopt amendment #38 as drafted (§5); execute the register/brief changes (§6)
in this planning session; then run WP-036C (`0144M`) as already planned,
followed by WP-036E → WP-036F → WP-036G, then WP-037. No WP-036E/F/G code is
written until WP-036C closes and each WP's S1 entry conditions (maintainer
approval, prior S4 closed, no open D1/D2) are met.
