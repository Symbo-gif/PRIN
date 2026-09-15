# PRIN Master Session Register

**Register version:** 1.4  
**Planned sessions:** 198 integer sessions + 8 sub-sessions (`0144A`–`0144H`, plan amendment #31) + 6 sub-sessions (`0141A`–`0141C`, `0141D1`, `0141D2`, `0141E`, plan amendment #32 — `0141D` split into `0141D1`/`0141D2` under Development Workflow §7, 2026-08-27) + 4 sub-sessions (`0144A`–`0144D`, plan amendment #33, WP-036A, mechanical renumber executed 2026-08-29) + 4 sub-sessions (`0144A1`–`0144A4`, plan amendment #34, WP-036A S1 decomposition, 2026-08-30) + 6 sub-sessions (`0144E1`–`0144E6`, plan amendment #35, WP-036B strict-port decomposition, 2026-08-31) + 7 sub-sessions (WP-036D at `0144I`–`0144L` with S1 decomposed into `0144I1`–`0144I3`, plan amendment #36, "GPU execution path for the ported acceptance suite", 2026-08-31; the WP-036C block shifted `0144I`–`0144L` → `0144M`–`0144P`) + 12 sub-sessions (`0144Q`–`0144AB`, plan amendment #38, WP-036E/F/G Deferred-Validation closure block, 2026-08-31) + 8 sub-sessions (`0144M1`–`0144M8`, plan amendment #39, WP-036C S1 strict-port decomposition, 2026-08-31) + 3 sub-sessions (`0144Q1`–`0144Q3`, plan amendment #43, WP-036E S1 decomposition + zero-copy re-scope, 2026-09-02) = **256**
**Current entry point:** Session 0001  
**Status authority:** the latest approved Project State Report; this register
is updated during S4 only from committed evidence.

No listed session may be skipped, merged, or reordered without an approved
plan amendment. Mandatory S3 executes even after a zero-finding audit. A D1
found during Phase 7 inserts a correction cycle from `contingencies/` before
the next numbered session; planned numbers do not change.

**Amendment-inserted sub-sessions (plan amendment #31):** WP-036 was split
into WP-036 / WP-036B / WP-036C. WP-036B and WP-036C occupy eight planned
sub-sessions `0144A`–`0144H`, inserted between planned integer sessions 0144
and 0145. They do **not** renumber the 0001–0198 integer sequence
(TRACEABILITY invariant 4 — gap-free integer numbering — is preserved), the
same additive-by-amendment precedent as the EA/EMA global sessions
(amendments #15, #23) but inside the phase sequence. Their Audit Reports and
Project State Reports are numbered `036b`/`036c`.

**Amendment-inserted sub-sessions (plan amendment #33, adopted and executed
2026-08-29):** the D-D-appendix rows 31–44 owning-WP decision created a new
work package, WP-036A ("Trainable compatibility layers — `prin-train`
extension"), taking sessions `0144A`–`0144D` (four new briefs authored at
WP-036 S4). The existing WP-036B sessions shifted from `0144A`–`0144D` to
`0144E`–`0144H`; the existing WP-036C sessions shifted from `0144E`–`0144H`
to `0144I`–`0144L`. Planned session count: 216 (212 + 4). WP-036A's Audit
Report and Project State Report are numbered `036a`.

**Amendment-inserted sub-sessions (plan amendment #34, adopted 2026-08-30):**
WP-036A S1 (session 0144A) is executed as four sequential S1 coding
sub-passes `0144A1`–`0144A4`, inserted between `0144A` and the S2 audit
`0144B` (see
`DOCS/sessions/phase-6/WP-036A-S1-execution-plan-and-decomposition.md`),
because the 13 trainable-layer symbols are 13 new trainable Burn modules
(five composed primitives lack a trainable Rust owner) — one commit range
too large to review at S2 without deferring tests or weakening gradcheck
tolerances (Development Workflow §7). They do **not** renumber the integer
sequence or the `0144E`–`0144L` block (`0144B`'s predecessor becomes
`0144A4`). All four commit at their own green local gate and feed the
single S2 audit `0144B`; the contiguous `0144A`+`0144A1`–`0144A4` range is
pushed once with `0144B` (amendment #28). `0144A3` is pre-authorised to
split into `0144A3a` / `0144A3b` under Development Workflow §7 (the
continuous three-band-network Burn port is the single largest new-numerics
item); if it splits, planned count becomes 221.

**Amendment-inserted sub-sessions (plan amendment #35, adopted 2026-08-31):**
WP-036B S1 (session `0144E`) is executed as six sequential strict-port coding
sub-passes `0144E1`–`0144E6`, inserted between `0144E` and the S2 audit
`0144F` (see
`DOCS/sessions/phase-6/WP-036B-S1-execution-plan-and-decomposition.md`). The
13 reference files contain 498 test functions / 8,570 lines; collect-only
reached 481 before `test_clevr_n.py` failed on missing `benchmarks.clevr_n`.
Testing Standards §1.1 stays literal: imports only, assertions unchanged;
missing behavior is rebuilt through Rust-backed compatibility layers, never a
semantic-test rewrite. All six commit at their own green local gate and feed
the single S2 audit `0144F`; `0144F`'s predecessor becomes `0144E6`. They do
not renumber the integer sequence or surrounding `0144A`–`0144L` block.
Planned session count: 220 + 6 = 226.

**Amendment-inserted sub-sessions (plan amendment #36, adopted 2026-08-31):**
a new work package, WP-036D ("GPU execution path for the ported acceptance
suite"), declared as WP-036's sibling in the same alphabetic-suffix family as
WP-036A/B/C, takes sessions `0144I`–`0144L`; the existing WP-036C sessions
shift `0144I`–`0144L` → `0144M`–`0144P` to make room (the amendment-#33
mechanical-renumber precedent — four already-drafted PLANNED briefs plus
their cross-links renamed, executed with this amendment). WP-036D closes the
gap the WP-036B S2 audit surfaced in its §8 addendum: 8 of the 9
acceptance-suite skips are CUDA guards on tests with a real reference GPU
path, red on every CPU host because `python/prin/_torch_compat.py` has no GPU
execution path — while the Rust CubeCL kernels (`prin-kernels`), the
`prin-sim` GPU engines, and the self-hosted `PRIN-GPU-Runner` all already
exist. WP-036D S1 (session `0144I`) is executed as three sequential coding
sub-passes `0144I1`–`0144I3` (PyO3 GPU binding layer; `_torch_compat.py`
device dispatch; test activation + `gpu.yml`), all feeding the single S2
audit `0144J` (whose predecessor becomes `0144I3`); `0144M`'s predecessor
becomes `0144L`. No new `prin` public symbol; the CPU path is untouched;
DV-005 (CUDA Burn training backend) and DV-001 (Linux Triton runner) are
explicitly **not** closed by this WP. The seven new identifiers are additive
and do not renumber 0001–0198 or 0145–0198 (TRACEABILITY invariant 4
preserved). WP-036D's Audit Report and Project State Report are numbered
`036d`. Planned session count: **226 → 233** (+3 sub-passes `0144I1`–
`0144I3`, +4 renumber targets `0144M`–`0144P`). Same disposition class as
amendment #33 (new sibling WP + mechanical renumber) and #35 (S1
decomposition). See
[`phase-6/WP-036D-S1-execution-plan-and-decomposition.md`](phase-6/WP-036D-S1-execution-plan-and-decomposition.md).
**Plan amendment #37 (2026-08-31)** reopened `0144I1` once (added
`GpuSparseKuramoto.from_knn_phase`) and re-scoped `0144I2` after verification
showed the "zero-copy DLPack GPU" premise is unreachable at the current
architecture (`prin-kernels`' CubeCL dispatch and `prin-sim`'s GPU engines are
host-in/host-out); the marshalling boundary is CPU `float32`, GPU compute runs
on-device via CubeCL, and a true zero-copy Torch↔CubeCL path is deferred as
**DV-030**. No new session IDs; count unchanged at **233**; no renumber. It
also reconciled the pre-existing `0144E` / `0144I1` brief↔register status
drift to `COMPLETE`.

**Amendment-inserted sub-sessions (plan amendment #38, adopted 2026-08-31):**
three new sibling work packages close or formally dispose of every open
Deferred Validation Register item before Phase 7, taking sessions
`0144Q`–`0144AB` inserted between the WP-036C block (`0144P`) and `0145`
(`0144P`'s successor becomes `0144Q`; `0145`'s predecessor becomes `0144AB`).
**WP-036E** ("GPU device-resident execution path", `0144Q`–`0144T`) makes the
`prin-kernels` dispatch layer and `prin-sim` GPU engines device-resident,
adds a true zero-copy Torch↔CubeCL DLPack path, moves the mean-field RK4
level-2 `f64` combine on-device, and activates
`test_sparse_vram_subquadratic` — **closes DV-030 and DV-003**. **WP-036F**
("DirectML controller-graph execution", `0144U`–`0144X`) re-exports the
subconscious controller ONNX graph with three-input `Gemm` nodes so
`DmlExecutionProvider` executes it — **closes the DirectML half of DV-006**,
discharges amendment #13's DirectML deferral; the VitisAI/NPU half stays
OPEN, hardware-gated. **WP-036G** ("Deferred-Validation register
consolidation and permanent dispositions", `0144Y`–`0144AB`; no source
numerics) assigns every remaining open item a dated disposition — permanent
(DV-007, DV-013, DV-018, DV-028) or standing-external / "not a Phase 7 entry
blocker" (DV-001, DV-008, DV-009, DV-011, DV-017, DV-022) — adds a `chacha20`
register row and a dormant `gpu-triton.yml`, resolves two pre-existing
test-fragility issues, and writes a Phase 7 entry statement. **DV-005** (CUDA
Burn training backend) is closed as `AMENDED` (out of scope for 1.0.0; re-gate
to a post-1.0 WP with a concrete workload); **DV-010** is reassigned to
WP-038 S1 scope; **DV-027** routed to EMA-006. WP-036E S1 (`0144Q`) is
pre-authorised to decompose into `0144Q1`–`0144Qn` under Development Workflow
§7. Identifiers roll single-letter `0144Q`–`0144Z` to two-letter
`0144AA`–`0144AB` for the last two. The integer sequence 0001–0198 and the
block `0144A`–`0144P` are unchanged (TRACEABILITY invariant 4 preserved).
WP-036E/F/G Audit Reports and Project State Reports are numbered
`036e`/`036f`/`036g`. Planned session count: **233 → 245** (+12). See
[`phase-6/WP-036E-036F-036G-execution-plan-and-decomposition.md`](phase-6/WP-036E-036F-036G-execution-plan-and-decomposition.md).
The sub-session chain extends `… → 0144P → 0144Q → 0144R → 0144S → 0144T →
0144U → 0144V → 0144W → 0144X → 0144Y → 0144Z → 0144AA → 0144AB → 0145`.

**Amendment-inserted sub-sessions (plan amendment #39, adopted 2026-08-31):**
WP-036C S1 (session `0144M`) is executed as eight sequential strict-port coding
sub-passes `0144M1`–`0144M8`, inserted between `0144M` and the S2 audit `0144N`
(see
[`phase-6/WP-036C-S1-execution-plan-and-decomposition.md`](phase-6/WP-036C-S1-execution-plan-and-decomposition.md)).
Repository verification corrects the prospective brief's "~790 `def test_`
functions" to **1,097 functions / ~15,810 lines across 24 reference files**
(`pytest --collect-only`: 1,172 collected, 0 errors) — ~1.85× the WP-036B
range — plus DV-025's `retrain_controller` resolution and the y-series
compatibility gap-closure exposed by collection/execution. Testing Standards
§1.1 stays literal: imports only, assertions/expected-values/parametrization/
call-order/semantics unchanged; missing behavior is rebuilt through Rust-backed
compatibility layers, never a semantic-test rewrite; hazard-tolerance and
backend-availability governance is unchanged and never licenses a weakened
assertion or an unapproved skip. GPU/Triton reference tests stay `skipif`-guarded
and reuse WP-036D's `_torch_compat.py` device dispatch. DV-025 `retrain_controller`
is resolved in `0144M2`; `quantize_onnx` is resolved only if a ported assertion
exercises it, else it keeps its documented stub + Migration-Guide row under S2
veto (maintainer `AskUserQuestion` selection). Sub-pass file assignment:
`0144M1` integration_q3 + y2q1 + y2q4; `0144M2` y2q2 + y2q3; `0144M3` y3q1 +
y3q2; `0144M4` y3q3 + y3q4 + y3q45 + y3q49; `0144M5` y4q1 + y4q1_2 + y4q1_3;
`0144M6` y4q1_4 + y4q1_5 + y4q1_9; `0144M7` y4q1_7 + y4q1_8; `0144M8` y4q2 +
y4q3 + y4q4 + triton_kernels + gpu + consolidation. `0144M8` is pre-authorised
to split `0144M8a`/`0144M8b` under Development Workflow §7 (count held until
then). All eight commit at their own green local gate and feed the single S2
audit `0144N`; `0144N`'s predecessor becomes `0144M8`. They do not renumber the
integer sequence or the surrounding `0144A`–`0144AB` block. Planned session
count: **245 → 253** (254 if `0144M8` splits). The sub-session chain becomes
`… → 0144M → 0144M1 → 0144M2 → 0144M3 → 0144M4 → 0144M5 → 0144M6 → 0144M7 →
0144M8 → 0144N → …`.

**Amendment-inserted sub-sessions (plan amendment #43, adopted 2026-09-02):**
WP-036E S1 (session `0144Q`) is executed as three sequential coding sub-passes
`0144Q1`–`0144Q3`, inserted between `0144Q` and the S2 audit `0144R` (see
[`phase-6/WP-036E-S1-execution-plan-and-decomposition.md`](phase-6/WP-036E-S1-execution-plan-and-decomposition.md)).
S1-start repository verification established that the brief's headline
deliverable — a *true bidirectional zero-copy Torch↔CubeCL DLPack kernel-input
path* (DV-030's stated closure mechanism) — is **not reachable on the pinned
`cubecl 0.10.0`**: `cubecl-cuda`'s `GpuStorage` has no API to adopt an
externally-owned CUDA device pointer as a `Handle`, and `ComputeClient`'s entire
handle-creation surface consumes host bytes or allocates uninitialised device
memory (no `[patch]`/vendored fork). The only no-host-round-trip *input* route
needs a new direct `cudarc` dependency + `unsafe` FFI outside the
amendment-#8-audited modules + torch↔CubeCL cross-stream sync — all barred by
the `0144Q` Contract. Same wall that re-scoped predecessor `0144I2`
(amendment #37). **Decision (maintainer, 2026-09-02, `AskUserQuestion`):**
re-scope the S1 deliverable to the device-resident envelope
(`0144Q1` `prin-kernels` device-`Handle` dispatch layer; `0144Q2` `prin-sim`
persistent device buffers + on-device CUDA `f64` combine, DV-003; `0144Q3`
`prin-py` **export**-direction zero-copy DLPack + `_torch_compat.py` device
path + one host upload at engine construction + `test_sparse_vram_subquadratic`
disposition), and re-scope **DV-030** from `CLOSED by WP-036E` to
`PARTIALLY CLOSED` — bidirectional zero-copy kernel-input re-gated to a `cubecl`
external-memory API or a vendored `cubecl-cuda` storage shim (dedicated future
WP). `test_sparse_vram_subquadratic`'s disposition is adjudicated at S2
(`0144R`) per Plan risk R2. Each sub-pass commits at its own green local gate;
the contiguous `0144Q`+`0144Q1`–`0144Q3` range feeds the single S2 audit
`0144R` (predecessor becomes `0144Q3`). The three identifiers are additive and
do not renumber `0001`–`0198` or the surrounding `0144A`–`0144AB` block
(TRACEABILITY invariant 4 preserved). Planned session count: **253 → 256**
(+3). The sub-session chain becomes `… → 0144P → 0144Q → 0144Q1 → 0144Q2 →
0144Q3 → 0144R → 0144S → 0144T → 0144U → …`. Every other `0144Q` Contract
invariant is unchanged. Same disposition class as amendment #37 (same blocker,
predecessor session) and #30/#33/#39.

**Plan amendment #44 (adopted 2026-09-02, no new session IDs):** WP-036E S3
(`0144S`) audit finding WP036E-F1 (D1). Genuine CUDA device-event timing — the
amendment-#38 / `0144Q2` DV-003 closure criterion — is **not reachable on
`cubecl = "0.10.0"`**: `cubecl-cuda` 0.10.0 hard-registers `TimingMethod::System`
(`src/runtime.rs:173`) and its compute server `block_on(sync())`-brackets every
`client.profile(...)` (`src/compute/server.rs:197-213`). The alternatives (a new
direct `cudarc` dep + `unsafe` `cuEvent*` FFI outside the amendment-#8-audited
modules, or a vendored `cubecl-cuda` fork) are barred by the WP-036E contract —
the same dependency wall as amendments #37/#43. **Decision (maintainer,
2026-09-02, `AskUserQuestion`):** **DV-003 → `PARTIALLY CLOSED by WP-036E`** —
the on-device CUDA `f64` combine + batched read-backs + a measured bounded host
residual (≈0.03 ms at N=262,144) are delivered and kept; `StepReport::timing_method`
reports `System` on CUDA honestly; genuine device-event timing is re-gated to a
`cubecl` release exposing `TimingMethod::Device`/stream-event hooks for CUDA, or
a dedicated vendored-shim WP (not gated to WP-036E, not a Phase 7 entry blocker;
WP-036G consolidates the residual). No source numerics changed; no session IDs
added; planned count unchanged (256). Same disposition class as amendments
#37/#43 (same dependency wall, same WP family) and #30.

**Plan amendment #40 (adopted 2026-08-31, no new session IDs):** three `0144M1`
scope confirmations (maintainer `AskUserQuestion` selections). (1) The
deferred-symbol rebuild of the standalone `DiscreteDeltaThetaGamma` core and
`InterleavedHybridPRINet` is in-scope for `0144M1` as implementation repair
(amendment #35 precedent) — a new `DiscreteDeltaThetaGammaBridge` PyO3 binding
over the audited Burn owner `prin_train::bands` (WP-022), plus `order_parameters`
/ `pac_index` methods added to that module, is binding/method completion of an
already-public symbol (no `prin.__all__` addition). (2) `prin.__version__`
bumped `0.3.0-alpha.1` -> `0.3.0` (drop the pre-release tag) so
`test_acceptance_y2q4::TestVersioning` / `TestAPIFreeze` pass on unchanged
assertions; `pyproject.toml`, `Cargo.toml`, `CITATION.cff`, `CHANGELOG.md`
updated in step. (3) Minimal PRIN docs authored under `docs/`
(`Architecture_Guide.md`, `Getting_Started_Tutorial.md`,
`API_Reference_Coupling_Topologies.md`) as compatibility-support artefacts for
`test_acceptance_y2q4::TestDocumentation` (E5 `benchmarks/clevr_n.py`
precedent). `test_acceptance_y2q1::test_speed_vs_transformer`
(`@pytest.mark.slow`, excluded from the default gate) records a ported perf
assertion PRIN's bridge dispatch overhead does not meet; carried to the `0144N`
audit as an out-of-scope discovery, not weakened.

**Amendment-inserted sub-sessions (plan amendment #32):** WP-036 S1
(session 0141) is executed as five sequential S1 coding sub-passes
`0141A`–`0141E`, inserted between planned integer sessions 0141 and 0142
(see `DOCS/sessions/phase-6/WP-036-S1-execution-plan-and-decomposition.md`). They
do **not** renumber the integer sequence (0142's predecessor becomes
`0141E`). All five commit at their own green local gate and feed the single
S2 audit 0142; the contiguous `0141`+`0141A`–`0141E` range is pushed once
with 0142 (amendment #28). `0141D` **was split** into `0141D1` (Bucket G
solver family + `TelemetryLogger` — delivered) and `0141D2` (the ~40-symbol
Bucket G remainder) under Development Workflow §7, 2026-08-27, as the 0141D
brief "Expected work" item 3 pre-authorised; both feed 0142 and 0141E's
predecessor is unchanged (`0141D` bucket → last sub-pass `0141D2`).

## Global sessions — Executive Audits

Executive Audit Sessions are project-level audits governed by
`DOCS/standards/Executive_Audit_Governance_and_Methodology.md`. They are
global sessions **outside** the planned 0001–0198 sequence: the planned
numbering above remains unique and gap-free (TRACEABILITY invariant 4), and
no planned session is renumbered by an executive audit (plan amendment #15).

| EA | Date | Session brief | Git state | Status |
|---|---|---|---|---|
| EA-001 | 2026-08-07 | Executive Audit Session 001 — full-project audit across E1–E10; report `DOCS/audits/EXECUTIVE_AUDIT_REPORT_001.md` (`PASS-WITH-REMEDIATION`, findings E-F1–E-F5) | `feat/wp006-oscillator-state` @ `d1e6e0a` | COMPLETE `[RETROACTIVE UPDATE - Executive Audit 002]` registered here; EA-001's own report claimed this registration but the update was never committed (EA-002 finding E-F2) |
| EA-002 | 2026-08-08 | Executive Audit Session 002 — delta audit of Sessions 0025–0036 (WP-007..WP-009) plus full-project re-verification; report `DOCS/audits/EXECUTIVE_AUDIT_REPORT_002.md` (`PASS-WITH-REMEDIATION`, findings E-F1–E-F13) | `feat/wp006-oscillator-state` @ `f5ae5b7` + remediation commits | COMPLETE |
| EA-003 | 2026-08-14 | Executive Audit Session 003 — delta audit of Sessions 0037–0064 (WP-010..WP-016, Phase 1 and Phase 2 close) plus full-project re-verification; report `DOCS/audits/EXECUTIVE_AUDIT_REPORT_003.md` (`PASS-WITH-REMEDIATION`, findings E-F1–E-F14) | `main` @ `fbe1c92` + remediation commits | COMPLETE — E-F7 investigated and risk-accepted (maintainer approval); E-F6 tag/publish deliberately deferred (maintainer directive, not executed this session) |
| EA-004 | 2026-08-17 | Executive Audit Session 004 — delta audit of Sessions 0065–0084 (WP-017..WP-021, Phase 3 close) plus full-project re-verification; report `DOCS/audits/EXECUTIVE_AUDIT_REPORT_004.md` (`PASS-WITH-REMEDIATION`, findings E-F1–E-F2) | `main` @ `933f8a3` + remediation commits | COMPLETE — E-F1 (GitHub Actions billing block, DV-014) is an external account-level condition passed forward to the maintainer, not fixable in-session; E-F2 (cumulative deviation-ledger corruption recurrence) fully remediated with durable CI enforcement |
| EA-005 | 2026-08-20 | Executive Audit Session 005 — delta audit of Sessions 0085–0108 (WP-022..WP-027, Phase 4 close) plus EMA-003/EMA-004, plus full-project re-verification; report `DOCS/audits/EXECUTIVE_AUDIT_REPORT_005.md` (`PASS-WITH-REMEDIATION`, findings E-F1–E-F5) | `main` @ `29d5e06` + remediation commits | COMPLETE — E-F1 (mypy lint failure, torch missing in CI) FIXED; E-F2 (ubuntu runner disk exhaustion, DV-022) and E-F3 (windows-latest CubeCL timeout, DV-023) passed forward as external infrastructure conditions; E-F4 (phase-4 README status mismatch) and E-F5 (CHANGELOG missing WP-027) FIXED |
| EA-006 | 2026-08-26 | Executive Audit Session 006 — delta audit of Sessions 0109–0128 (WP-028..WP-032, Phase 5 close) plus two post-close CI hotfix commits (`cb5660b`, `5d90427`), plus full-project re-verification; report `DOCS/audits/EXECUTIVE_AUDIT_REPORT_006.md` (`PASS-WITH-REMEDIATION`, findings E-F1–E-F2) | `main` @ `5d90427` + remediation commits | COMPLETE — E-F1 (D3, hotfix commits never recorded in the deviation ledger, DV-024 stale) FIXED; E-F2 (D3, R28's precondition — dedicated hotfix/correction session for DV-019 before WP-028 S1 — never honored, Phase 5 closed anyway) remediated at the governance level: compliance gap recorded, hard entry-condition gate added to WP-033 S1 |

## Global sessions — Executive Mathematical Audits

Executive Mathematical Audit (EMA) Sessions are project-level audits governed
by `DOCS/standards/Executive_Mathematical_Audit_Governance_and_Methodology.md`,
introduced by plan amendment #23. Like EA sessions, they are global sessions
**outside** the planned 0001–0198 sequence (plan amendment #15's registration
precedent, extended to this second audit type): the planned numbering above
remains unique and gap-free (TRACEABILITY invariant 4), and no planned session
is renumbered by an executive mathematical audit.

| EMA | Date | Session brief | Git state | Status |
|---|---|---|---|---|
| EMA-001 | 2026-08-14 | Executive Mathematical Audit Session 001 — first integration of `math-audit-mcp` into PRIN; governance/methodology definition, independent claim-ledger audit (23 claims) of `prin-dynamics`/`prin-metrics`; report `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_001.md` (`FAIL`; one open D1 finding M-F1) | `main` @ `f1204ed` + session commits | COMPLETE (audit + report only) — M-F1 (D1, Z3-confirmed `chimera.rs` phase-wrap defect) is open and explicitly deferred to a follow-up EMA-001 remediation session, not fixed in this session by scope decision |
| EMA-001R | 2026-08-14 | Executive Mathematical Audit Session 001 — **remediation session**: fixed M-F1 (D1, `chimera.rs` `centred_wrap`) with regression coverage and a documented, permanent PRINet-3.0-fixture non-parity exception (amendment #25, upstream defect); re-encoded and Z3-reverified M-F2 (D3, `PW-01`/`PW-02`); resolved M-F3 (D2) for `GRA-01`/`TEN-01` via two new Lean 4 `decide`-based formal claims (`GRA-01-LEAN`, `TEN-01-LEAN`, amendment #24) reaching genuine ledger `PASS`, and for `INT-01`/`INT-02`/`HOPF-01`/`KUR-01` via informal Wolfram Engine secondary corroboration (`EVIDENCE/math-audit/manual/`) plus recorded maintainer/agent sign-off (all four remain `REQUIRES_HUMAN_REVIEW` at the governed ledger level by policy design, per M-F3's own diagnosis); report addendum in `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_001.md` §7-§9 | `main` @ `f1204ed` + remediation commit(s) | COMPLETE — verdict updated to `PASS-WITH-REMEDIATION` |
| EMA-002 | 2026-08-17 | Executive Mathematical Audit Session 002 — Phase 3 close mathematical audit. Re-verified 25 existing claims against `1604bd6` (zero regressions); added 3 new GPU kernel claims (`prin-kernels-gpu-properties.json`: GPU-RK4-01, GPU-RED-01, GPU-KNN-01) covering `prin-kernels` mean-field RK4 Butcher tableau, hierarchical reduction associativity, and sparse k-NN coupling normalization — all 3 reached genuine SymPy symbolic proof `PASS`. 28 total claims across 6 ledgers; 21 PASS, 7 REQUIRES_HUMAN_REVIEW (same M-F3 policy-gate as EMA-001R, re-confirmed under DV-013/R20 sign-off precedent). Report `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_002.md` | `main` @ `1604bd6` + session commits | COMPLETE — verdict `PASS-WITH-REMEDIATION` |
| EMA-003 | 2026-08-19 | Executive Mathematical Audit Session 003 — Phase 4 close mathematical audit, first EMA coverage of the trainable stack. Re-verified all 28 existing claims against `6e33ca5` (zero regressions); authored and executed 10 new `prin-train-trainable-stack-properties.json` claims (Hungarian loss entropy, dSiLU derivative, Scalr lr-scale boundaries, RIP Hebbian equilibrium, SyncGd penalty, GatedPhaseActivation/Scalr/sync-penalty/RIP-diagonal bounds) — 9/10 reached genuine SymPy/Z3 `PASS`; SCALR-LR-02 reached `INCONCLUSIVE` (recorded as new finding M-F8, a `math-audit-mcp` tool gap with `0**alpha` for symbolic `alpha`, later fixed at EMA-004). 38 total claims across 7 ledgers; 30 PASS, 1 INCONCLUSIVE, 7 REQUIRES_HUMAN_REVIEW (same M-F3/M-F7 policy-gate, re-confirmed under DV-013/R20 precedent). Direct redundant SymPy+Z3 cross-verification performed for all new claims. Report `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_003.md` (commit `cb2d83c`). **This session's own DEFERRED_VALIDATION_REGISTER.md/SESSION_REGISTER.md/CHANGELOG.md entries were not added at the time** (governance §8.6 closing-checklist gap); added retroactively by EMA-004 alongside its own entries. | `main` @ `6e33ca5` + session commit `cb2d83c` | COMPLETE — verdict `PASS-WITH-REMEDIATION` |
| EMA-004 | 2026-08-20 | Executive Mathematical Audit Session 004 — **tool remediation session**. Fixed EMA-003's M-F8 at root cause inside `math-audit-mcp`'s `verify_identity` (promote declared `"symbol > 0"`-style assumptions into SymPy `Symbol`-level kwargs so `Pow(0, x)` auto-evaluation can fire — `sympy.refine` has no handler for this case; not a SymPy limitation as previously characterized, a tool gap). Fixed EMA-001's M-F5 by adding `expected_output`/`output_tolerance` numeric-reconstruction comparison to `audit_tensor_contract` (pure NumPy, no PyTorch/JAX backend needed as previously scoped) and authored a new claim (TCK-01, `prin-tensor-hosvd-reconstruction.json`, first EMA coverage of `prin-tensor`) exercising it against the existing PRINet-3.0 reference fixture (`crates/prin-tensor/tests/data/prinet_reference_hosvd.json`), residual `7.1e-15` at `1e-10` tolerance. Added a new optional adapter/tool (PySAT: `pysat_adapter.py` + `audit_graph_regularity_sat`, CNF cardinality-encoding + CDCL SAT corroboration of graph k-regularity, independent solver family from NetworkX/Z3) and a new claim (GRA-01-SAT) corroborating GRA-01. Fixed EMA-001's M-F6 by `git init`-ing the tool's own (separate, non-PRIN) repository for the first time, 3 commits, HEAD `ef1c2001f38e6d6623e992c9785093e6c7c0b458`. Evaluated `z3_mcp` (non-additive, redundant with existing `z3_adapter.py`), `OpenLogic` (reference corpus, not a callable tool), MiniZinc MCP and SageMath (not installed; deferred, no concrete claim currently needs them). Re-ran the full audit: 40 claims across 8 ledgers (was 38/7), zero regressions confirmed claim-by-claim, 33 PASS / 0 FAIL / 0 INCONCLUSIVE / 7 REQUIRES_HUMAN_REVIEW (M-F7 unchanged, resolved-by-design). **Maintainer sign-off (MichaelMaillet, 2026-08-20) re-granted for the full current REQUIRES_HUMAN_REVIEW set** (INT-01, INT-02, HOPF-01, KUR-01, GRA-01, TEN-01, and first-time sign-off for the new TCK-01), per DV-013's recorded-sign-off resolution pattern — see report §8. Also retroactively added EMA-003's own missing register/changelog entries (governance §8.6 gap discovered this session). Report `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_004.md`. | `main` @ `cb2d83c` + session commit | COMPLETE — verdict `PASS-WITH-REMEDIATION` |
| EMA-005 | 2026-08-26 | Executive Mathematical Audit Session 005 — **Phase 5 close mathematical audit**. Re-verified all 40 existing claims against `79cf971` (zero regressions, confirmed claim-by-claim, including under an unplanned Lean 4.33.0→4.33.1 toolchain auto-upgrade, M-F10, confirmed non-regression). Independently investigated Phase 5 (WP-028..032, `crates/prin-daemon/src/{assignment,mot}.rs`, `crates/prin-train/src/{stats,adversarial}.rs`) for new mathematical content beyond EA-006's source-review disposition; found genuine unaudited content (Hungarian/Kuhn-Munkres assignment, IoU-distance geometry, Cohen's d, Welch-Satterthwaite degrees of freedom, Gamma-reflection/Beta-integral identities behind the Student's-t p-value) and authored a new ledger, `prin-daemon-phase5-properties.json` (6 claims: HUN-01, IOU-01, COHEN-01, WELCH-DF-01, GAMMA-REFLECT-01, BETA-SYM-01), deliberately scoped to `z3_invariant`/`symbolic_identity` tool types so none entered the M-F7 policy-gate class — 6/6 genuine `PASS`. Cross-validated every result with independent, out-of-band Wolfram Engine computation (confirmed usable on this workstation, `EVIDENCE/math-audit/manual/ema-005-wolfram-corroboration.{wls,txt}`), including a third independent confirmation channel (Rust brute-force test + Z3 UNSAT proof + Wolfram permutation search) for the Hungarian-assignment optimum. Discovered and worked around **M-F9** (D4: `math-audit-mcp`'s `verify_identity` allowlist has no Beta-function support — `betainc_regularized` rejected; re-derived BETA-SYM-01 from Euler's Beta-integral definition instead, a stronger independent check, not a weaker workaround) and recorded **M-F11** (D4: stale `pip show` metadata in the tool's `.venv`, cosmetic only). 46 total claims across 9 ledgers; 39 PASS / 0 FAIL / 0 INCONCLUSIVE / 0 TOOL_ERROR / 7 REQUIRES_HUMAN_REVIEW (unchanged composition from EMA-004). **Maintainer sign-off granted the same day (2026-08-26, MichaelMaillet)** for the unchanged 7-claim REQUIRES_HUMAN_REVIEW set, per DV-013's re-grant rule — see report §8. Report `DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_005.md`. | `main` @ `79cf971` + session commit | COMPLETE (audit + report) — verdict `PASS-WITH-REMEDIATION`; maintainer sign-off granted (§8) |

_EMA-006 (2026-09-01, Phase 6 mid-phase, `PASS-WITH-REMEDIATION`,
`DOCS/audits/EXECUTIVE_MATH_AUDIT_REPORT_006.md`) and EDA-001 (2026-09-01,
first Executive Documentation Audit, `PASS-WITH-REMEDIATION`,
`DOCS/audits/EXECUTIVE_DOCUMENTATION_AUDIT_REPORT_001.md`) were committed
without their own register rows/sections (each governance doc requires one).
ETCA-001 (§ below) flags this; a future EMA/EDA or EA session reconciles it._

## Global sessions — Executive Testing and CI Audits

Executive Testing and CI Audit (ETCA) Sessions are project-level audits
governed by `DOCS/standards/Executive_Testing_and_CI_Audit_Governance_and_Methodology.md`,
introduced by plan amendment #42. They verify the test suite and CI/CD gate
machinery in depth (EA dimensions E3/E9, exhausted rather than sampled) across
8 dimensions T1–T8, using the `T-FN` finding prefix. Like EA/EMA/EDA sessions
they are global sessions **outside** the planned 0001–0198 sequence (plan
amendment #15's registration precedent): the planned numbering remains unique
and gap-free (TRACEABILITY invariant 4), and no planned session is renumbered.

| ETCA | Date | Session brief | Git state | Status |
|---|---|---|---|---|
| ETCA-001 | 2026-09-01 | Executive Testing and CI Audit Session 001 — first ETCA session; establishes the audit type (governance + template + plan amendment #42). Phase 6 mid-phase (WP-033..WP-036C S4, sessions 0129–0144P; audit window delta since EA-006 `5d90427` through `e4fb372`). Systematic verification of the test suite and CI machinery across T1–T8. Report `DOCS/audits/EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_001.md` (`PASS-WITH-REMEDIATION`, findings T-F1–T-F10). Zero D1; three D2 (T-F1 `python.yml` bandit gate red → R17/R34 CI enforcement steps inert; T-F2 ~13 CI-failing `prinet`-dependent tests; T-F3 `wp001_baseline` gate red from a session-brief parser cap); five D3 (T-F4 the entire WP-036C cycle — 28 commits — unpushed and never through CI; T-F5 `repro.yml`/`python.yml` ubuntu disk exhaustion, DV-022 class; T-F6 self-hosted Windows `rust` leg 24 h runner hang, DV-024 class; T-F7 no enforcing benchmark-regression gate / no nightly full-suite workflow; T-F8 `test_no_gpu_throughput_regression` quarantined without a tracked DV item); two D4 (T-F9 figure/table tests fail under the AGENTS.md `--basetemp` override; T-F10 local/CI gate command drift + optimistic PSR verification blocks). Read-only w.r.t. first-party source/test code — all findings passed forward to a dedicated remediation session. | `main` @ `e4fb372` (local; `origin/main` @ `0313af5`) + session commit | COMPLETE (audit + report) — verdict `PASS-WITH-REMEDIATION`; blocking recommendation: no Phase 6 close push and no WP-036E S1 until T-F1/T-F2/T-F3/T-F5/T-F6 fixed and `origin/main` CI green |
| ETCA-001 remediation | 2026-09-01 | **Remediation session** for ETCA-001 (EDA-001 precedent). **T-F1** bandit `# nosec B404/B603/B110` + R17/R34 gates moved to a new `python.yml` `governance` job; **T-F2** `pytest.importorskip` guard on 17 WP-036A reference-parity test bodies; **T-F3** `wp001_baseline.py` metadata-block parser hardened + `0144P` brief `**Status:**` compressed; **T-F5** disk-reclaim + CPU-only torch before `maturin develop` in `python.yml`/`repro.yml`/`nightly.yml` (DV-022 extended); **T-F6** `rust.yml` Windows tests back on GitHub-hosted `windows-latest` — SPOF removed (DV-024 updated); **T-F7** new `.github/workflows/nightly.yml` (scheduled full suite + enforcing criterion/pytest-benchmark >10% regression gate via new `tools/check_bench_regression.py`); **T-F8** quarantine tracked as **DV-032**; **T-F9** `prin.reporting._artifacts.allowed_output_roots()` allows the in-repo `.pytest_basetemp` under pytest only; **T-F10** `AGENTS.md` bandit scope aligned to `python/prin`. Plus the two CI-only Windows failures the audit's T6 dimension flagged (`training_hooks.StateCollector` timer `monotonic`→`perf_counter`; `test_wp036d_gpu_dispatch` GPU-binding `skipif`) and, once CI actually ran the ubuntu suite, a batch of pre-existing failures the never-run CI had masked: a disk-reclaim step deleting the `setup-python` toolcache; `test_acceptance_y2q4::TestDocumentation` `docs/`→`DOCS/` case-sensitivity; an unseeded-input slot-attention gradcheck (autouse `torch.manual_seed`); `test_acceptance_y4q1_5::test_deterministic_seed` timing flake (→ DV-032). Coverage-measurement gap recorded as **DV-033**. Report §7 closure table filled; verdict updated to **PASS**. Three push cycles to green (`a37e846`, `ccfc442`, + the pre-existing-failure fixes). | `main` @ `e4fb372` → remediation commits, pushed; `origin/main` CI green | COMPLETE — verdict `PASS` |
| ETCA-002 | 2026-09-02 | Executive Testing and CI Audit Session 002 — **post-push CI-failure audit** of the batched WP-036E + WP-036F range (Deferred-Validation closure work), sessions `0144Q`–`0144X`; audit window `6343416..adbb1e3` (17 commits). Triggered by methodology §1.1 conditions 3 (CI-health: `origin/main` red on the latest push, ETCA-001's green state did not survive one WP cycle) and 4 (maintainer request). Report `DOCS/audits/EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_002.md` (`FAIL`, findings T-F1–T-F10). **One D1** (T-F1: WP-036E never pushed as its own S4 cycle; WP-036F S4 pushed the batched range **red** — `python` `lint`/`mypy` + all Windows `test` legs, `gpu` skipped, `nightly` red — yet both WPs declared closed, PSR-036F issued, DV-006 DirectML half marked CLOSED, amendment #13 marked discharged, S4 doc asserting "CI is green"; amendment #28 S4 exit criterion unmet for both WPs; **recurrence of ETCA-001 T-F4**). **Three D2** (T-F2 `mypy python/prin --strict` red in CI / green locally — unpinned `lint` toolchain, recurrence of ETCA-001 T-F10 / EA-005 E-F1; T-F3 5 DirectML/provider tests hard-fail every CI Windows leg — `skipif` guards test `ort.get_available_providers()` build capability not device executability + `TestProviderLatencyTool` unguarded, recurrence of ETCA-001 T-F2; T-F4 WP-036F audit A9 "✅ (local substitute)" + S4 doc "CI is green" — false verification claims). **Four D3** (T-F5 `nightly` `full-suite` permanently red on `test_speed_vs_transformer` 5.66× — untracked DV-032-class flake; T-F6 `gpu.yml` opt-in `[gpu]` tag → all GPU CI skipped on the push closing two GPU WPs; T-F7 **no branch protection on `main`** — CI unenforced, red pushes land unimpeded; T-F8 unbounded self-hosted `rust` Windows leg). **Two D4** (T-F9 doc/state drift "not pushed" vs `origin/main`; T-F10 unpinned `lint` toolchain hygiene). Read-only w.r.t. first-party source/test code — all findings passed forward to a dedicated ETCA-002 remediation session, with governance recommendations G1–G8 (per-WP blocking S4 push; machine-checked `tools/check_ci_green.py` S4 gate; branch protection = merge gate; `gpu.yml` on every `main` push; nightly-red dispositioned like push-red; pin every CI gate toolchain; ETCA auto-trigger on CI-health condition; recurrence ⇒ class-level regression guard). | `main` @ `adbb1e3` (local == `origin/main`) + session commit | COMPLETE (audit + report) — verdict `FAIL`; blocking recommendation: WP-036F is **not** closed and WP-036G S1 (`0144Y`) must not begin until T-F1–T-F4 fixed and `origin/main` CI (incl. a `[gpu]` run) confirmed green |
| ETCA-002 remediation | 2026-09-02 | **Remediation session** for ETCA-002 (ETCA-001-remediation / EDA-001 precedent). Maintainer `AskUserQuestion` decisions: enable GitHub branch protection (as a `main` **ruleset** — classic branch-protection unavailable on this private/Free repo, DV-009 precedent); run `gpu.yml` on every `main` push; adopt G1–G8 as **Plan amendment #45**; quarantine `test_speed_vs_transformer` into DV-032. **T-F1/T-F4** — `tools/check_ci_green.py` (machine-checked S4 CI-green gate, G2) + Development Workflow §3 "per-WP push is mandatory and blocking" + A9 update; WP-036F re-closed over a real green `origin/main` run. **T-F2** — `, unused-ignore` added to 6 torch-stub `# type: ignore` sites; `ci/lint-constraints.txt` pins the `python.yml` `lint` toolchain (T-F10/G6). **T-F3** — `tests/_env.py::directml_executes()` executability probe + `@pytest.mark.directml` replace the `ort.get_available_providers()` guards in `test_wp036f_reexport.py`/`test_daemon_controller.py`; `wp036f_provider_latency` records a portable `close` signal; `tools/check_skipif_probes.py` regression guard in `python.yml` `governance` (G8). **T-F5** — `test_speed_vs_transformer` → `tests/conftest.py` DV-032 quarantine; `nightly` green. **T-F6** — `gpu.yml` unconditional on `push:[main]` + `schedule` + `workflow_dispatch`, `-m "gpu or directml"` (G4). **T-F7** — `ci/main-branch-ruleset.json` (required checks incl. `gpu-cuda`/`gpu-wgpu` per maintainer decision + PR-required + no bypass); the chronic runner-offline condition root-caused (never a Windows service) and fixed via `ci/install-gpu-runner-service.ps1` (new **DV-034**). **T-F8** — dispositioned (already hosted + `timeout-minutes: 120`; residual = DV-016). **T-F9/T-F10** — doc/state drift corrected; lint toolchain pinned. Standards updated: Development Workflow §3/§4, Coding Standards §6.2, Testing Standards §1, ETCA methodology §4/§5.5. Report §7 closure table filled; verdict updated to **PASS**. | `main` @ `adbb1e3` → `bef851c` → `47d7ef3` → `9d4fd86`, pushed; `origin/main` CI green (`9d4fd86` HEAD, **all 6 workflows** `rust`/`python`/`parity`/`repro`/`snyk`/`gpu` `success`; `nightly` `workflow_dispatch` both jobs green; DirectML tests pass on `PRIN-GPU-Runner`, skip on hosted) | COMPLETE — verdict `PASS` |

## Global sessions — Ad hoc hotfix/correction sessions

Sessions opened outside the numbered 0001–0198 sequence to address a
governed defect under Development Workflow and Audit Standards §3/§7 (a
code defect in frozen scope, or a live `main` break) that cannot wait for
or be folded into an unrelated WP's own cycle. Named/numbered only when
actually opened, never pre-reserved (Phase 4 analytics R28's own
disposition). Prior instances of this class (`WP-025 S3-exec`,
`Exec-WP-026 S1` — see `CHANGELOG.md` `[Unreleased]` → `### Fixed` and
`DOCS/experiments/0101-exec-wp026-s1-handoff.md`) predate this table's
introduction and are not retroactively added here; this table starts with
`Hotfix-DV019`.

| Session | Date | Session brief | Git state | Status |
|---|---|---|---|---|
| `Hotfix-DV019` | 2026-08-26 | Dedicated hotfix/correction session for **DV-019** (`DEFERRED_VALIDATION_REGISTER.md`), executing Phase 5 analytics recommendation R33 (P0) and satisfying the hard entry-condition gate EA-006 added to WP-033 S1's session brief. Handoff note: `DOCS/experiments/hotfix-dv019-handoff.md`. Reproduced the flake on demand for the first time (9/12 `cargo test -p prin-train --lib` runs failed at default concurrency; 0/N failed at `--test-threads=1`), correcting the leading root-cause hypothesis: not a rayon summation-order artifact in three specific tests' fixtures, but a confirmed cross-thread graph-server interaction in `burn-autodiff` 0.16.1's default runtime (one process-global `AutodiffServer` shared by every `Autodiff<B>` graph, with no per-graph isolation). Fixed via a `prin-train`-private, test-only serialization mutex (`crate::support::autodiff_test_guard`) applied to all 42 autodiff-graph-touching tests across 14 files (not only the 3 originally-named modules); kept the fixture-hardening attempted first (batch/step-count/distinct-input changes to `bands.rs`/`hybrid.rs`/`phase_tracker.rs`) as independently-justified defense in depth, having directly confirmed it alone does not close the defect. | `main` @ `5fdfeb0` + session commit | COMPLETE — DV-019 `CLOSED`; 51 consecutive clean `cargo test -p prin-train --lib`-class runs plus the 10-concurrent-process contention scenario that reproduced the pre-fix defect; Python-side DV-019 sub-item re-confirmed clean (15/15) but its own root-cause-confirmation question remains open per DV-019's existing text |


| Seq | Phase | Unit | Type | Session brief | Current status |
|---:|---:|---|---|---|---|
| 0001 | 0 | WP-001 | S1 — Coding | [Foundation baseline and traceability](phase-0/0001-wp001-s1-foundation-baseline-and-traceability.md) | COMPLETE |
| 0002 | 0 | WP-001 | S2 — Audit | [Foundation baseline and traceability](phase-0/0002-wp001-s2-foundation-baseline-and-traceability.md) | COMPLETE |
| 0003 | 0 | WP-001 | S3 — Remediation | [Foundation baseline and traceability](phase-0/0003-wp001-s3-foundation-baseline-and-traceability.md) | COMPLETE |
| 0004 | 0 | WP-001 | S4 — Documentation | [Foundation baseline and traceability](phase-0/0004-wp001-s4-foundation-baseline-and-traceability.md) | COMPLETE |
| 0005 | 0 | WP-002 | S1 — Coding | [Golden corpus and differential harness](phase-0/0005-wp002-s1-golden-corpus-and-differential-harness.md) | COMPLETE |
| 0006 | 0 | WP-002 | S2 — Audit | [Golden corpus and differential harness](phase-0/0006-wp002-s2-golden-corpus-and-differential-harness.md) | COMPLETE |
| 0007 | 0 | WP-002 | S3 — Remediation | [Golden corpus and differential harness](phase-0/0007-wp002-s3-golden-corpus-and-differential-harness.md) | COMPLETE |
| 0008 | 0 | WP-002 | S4 — Documentation | [Golden corpus and differential harness](phase-0/0008-wp002-s4-golden-corpus-and-differential-harness.md) | COMPLETE |
| 0009 | 0 | WP-003 | S1 — Coding | [PyO3 and DLPack bridge spike](phase-0/0009-wp003-s1-pyo3-and-dlpack-bridge-spike.md) | COMPLETE |
| 0010 | 0 | WP-003 | S2 — Audit | [PyO3 and DLPack bridge spike](phase-0/0010-wp003-s2-pyo3-and-dlpack-bridge-spike.md) | COMPLETE |
| 0011 | 0 | WP-003 | S3 — Remediation | [PyO3 and DLPack bridge spike](phase-0/0011-wp003-s3-pyo3-and-dlpack-bridge-spike.md) | COMPLETE |
| 0012 | 0 | WP-003 | S4 — Documentation | [PyO3 and DLPack bridge spike](phase-0/0012-wp003-s4-pyo3-and-dlpack-bridge-spike.md) | COMPLETE |
| 0013 | 0 | WP-004 | S1 — Coding | [CubeCL fused RK4 spike](phase-0/0013-wp004-s1-cubecl-fused-rk4-spike.md) | COMPLETE |
| 0014 | 0 | WP-004 | S2 — Audit | [CubeCL fused RK4 spike](phase-0/0014-wp004-s2-cubecl-fused-rk4-spike.md) | COMPLETE |
| 0015 | 0 | WP-004 | S3 — Remediation | [CubeCL fused RK4 spike](phase-0/0015-wp004-s3-cubecl-fused-rk4-spike.md) | COMPLETE |
| 0016 | 0 | WP-004 | S4 — Documentation | [CubeCL fused RK4 spike](phase-0/0016-wp004-s4-cubecl-fused-rk4-spike.md) | COMPLETE |
| 0017 | 0 | WP-005 | S1 — Coding | [ORT backends, wheel matrix, and Phase 0 gate](phase-0/0017-wp005-s1-ort-backends-wheel-matrix-and-phase-0-gate.md) | COMPLETE |
| 0018 | 0 | WP-005 | S2 — Audit | [ORT backends, wheel matrix, and Phase 0 gate](phase-0/0018-wp005-s2-ort-backends-wheel-matrix-and-phase-0-gate.md) | COMPLETE |
| 0019 | 0 | WP-005 | S3 — Remediation | [ORT backends, wheel matrix, and Phase 0 gate](phase-0/0019-wp005-s3-ort-backends-wheel-matrix-and-phase-0-gate.md) | COMPLETE |
| 0020 | 0 | WP-005 | S4 — Documentation | [ORT backends, wheel matrix, and Phase 0 gate](phase-0/0020-wp005-s4-ort-backends-wheel-matrix-and-phase-0-gate.md) | COMPLETE |
| 0021 | 1 | WP-006 | S1 — Coding | [Oscillator state, errors, and deterministic seed](phase-1/0021-wp006-s1-oscillator-state-errors-and-deterministic-seed.md) | COMPLETE |
| 0022 | 1 | WP-006 | S2 — Audit | [Oscillator state, errors, and deterministic seed](phase-1/0022-wp006-s2-oscillator-state-errors-and-deterministic-seed.md) | COMPLETE |
| 0023 | 1 | WP-006 | S3 — Remediation | [Oscillator state, errors, and deterministic seed](phase-1/0023-wp006-s3-oscillator-state-errors-and-deterministic-seed.md) | COMPLETE |
| 0024 | 1 | WP-006 | S4 — Documentation | [Oscillator state, errors, and deterministic seed](phase-1/0024-wp006-s4-oscillator-state-errors-and-deterministic-seed.md) | COMPLETE |
| 0025 | 1 | WP-007 | S1 — Coding | [Oscillator dynamics models](phase-1/0025-wp007-s1-oscillator-dynamics-models.md) | COMPLETE |
| 0026 | 1 | WP-007 | S2 — Audit | [Oscillator dynamics models](phase-1/0026-wp007-s2-oscillator-dynamics-models.md) | COMPLETE |
| 0027 | 1 | WP-007 | S3 — Remediation | [Oscillator dynamics models](phase-1/0027-wp007-s3-oscillator-dynamics-models.md) | COMPLETE |
| 0028 | 1 | WP-007 | S4 — Documentation | [Oscillator dynamics models](phase-1/0028-wp007-s4-oscillator-dynamics-models.md) | COMPLETE |
| 0029 | 1 | WP-008 | S1 — Coding | [Basic integrators](phase-1/0029-wp008-s1-basic-integrators.md) | COMPLETE |
| 0030 | 1 | WP-008 | S2 — Audit | [Basic integrators](phase-1/0030-wp008-s2-basic-integrators.md) | COMPLETE |
| 0031 | 1 | WP-008 | S3 — Remediation | [Basic integrators](phase-1/0031-wp008-s3-basic-integrators.md) | COMPLETE |
| 0032 | 1 | WP-008 | S4 — Documentation | [Basic integrators](phase-1/0032-wp008-s4-basic-integrators.md) | COMPLETE |
| 0033 | 1 | WP-009 | S1 — Coding | [PAC, coupling topologies, and phase k-NN](phase-1/0033-wp009-s1-pac-coupling-topologies-and-phase-k-nn.md) | COMPLETE |
| 0034 | 1 | WP-009 | S2 — Audit | [PAC, coupling topologies, and phase k-NN](phase-1/0034-wp009-s2-pac-coupling-topologies-and-phase-k-nn.md) | COMPLETE |
| 0035 | 1 | WP-009 | S3 — Remediation | [PAC, coupling topologies, and phase k-NN](phase-1/0035-wp009-s3-pac-coupling-topologies-and-phase-k-nn.md) | COMPLETE |
| 0036 | 1 | WP-009 | S4 — Documentation | [PAC, coupling topologies, and phase k-NN](phase-1/0036-wp009-s4-pac-coupling-topologies-and-phase-k-nn.md) | COMPLETE |
| 0037 | 1 | WP-010 | S1 — Coding | [Phase metrics and chimera measures](phase-1/0037-wp010-s1-phase-metrics-and-chimera-measures.md) | COMPLETE |
| 0038 | 1 | WP-010 | S2 — Audit | [Phase metrics and chimera measures](phase-1/0038-wp010-s2-phase-metrics-and-chimera-measures.md) | COMPLETE |
| 0039 | 1 | WP-010 | S3 — Remediation | [Phase metrics and chimera measures](phase-1/0039-wp010-s3-phase-metrics-and-chimera-measures.md) | COMPLETE |
| 0040 | 1 | WP-010 | S4 — Documentation | [Phase metrics and chimera measures](phase-1/0040-wp010-s4-phase-metrics-and-chimera-measures.md) | COMPLETE |
| 0041 | 1 | WP-011 | S1 — Coding | [Phase 1 Python API and dynamics integration](phase-1/0041-wp011-s1-phase-1-python-api-and-dynamics-integration.md) | COMPLETE |
| 0042 | 1 | WP-011 | S2 — Audit | [Phase 1 Python API and dynamics integration](phase-1/0042-wp011-s2-phase-1-python-api-and-dynamics-integration.md) | COMPLETE |
| 0043 | 1 | WP-011 | S3 — Remediation | [Phase 1 Python API and dynamics integration](phase-1/0043-wp011-s3-phase-1-python-api-and-dynamics-integration.md) | COMPLETE |
| 0044 | 1 | WP-011 | S4 — Documentation | [Phase 1 Python API and dynamics integration](phase-1/0044-wp011-s4-phase-1-python-api-and-dynamics-integration.md) | COMPLETE |
| 0045 | 2 | WP-012 | S1 — Coding | [Exponential and multi-rate integrators](phase-2/0045-wp012-s1-exponential-and-multi-rate-integrators.md) | COMPLETE |
| 0046 | 2 | WP-012 | S2 — Audit | [Exponential and multi-rate integrators](phase-2/0046-wp012-s2-exponential-and-multi-rate-integrators.md) | COMPLETE |
| 0047 | 2 | WP-012 | S3 — Remediation | [Exponential and multi-rate integrators](phase-2/0047-wp012-s3-exponential-and-multi-rate-integrators.md) | COMPLETE |
| 0048 | 2 | WP-012 | S4 — Documentation | [Exponential and multi-rate integrators](phase-2/0048-wp012-s4-exponential-and-multi-rate-integrators.md) | COMPLETE |
| 0049 | 2 | WP-013 | S1 — Coding | [Continuous band networks and temporal propagation](phase-2/0049-wp013-s1-continuous-band-networks-and-temporal-propagation.md) | COMPLETE |
| 0050 | 2 | WP-013 | S2 — Audit | [Continuous band networks and temporal propagation](phase-2/0050-wp013-s2-continuous-band-networks-and-temporal-propagation.md) | COMPLETE |
| 0051 | 2 | WP-013 | S3 — Remediation | [Continuous band networks and temporal propagation](phase-2/0051-wp013-s3-continuous-band-networks-and-temporal-propagation.md) | COMPLETE |
| 0052 | 2 | WP-013 | S4 — Documentation | [Continuous band networks and temporal propagation](phase-2/0052-wp013-s4-continuous-band-networks-and-temporal-propagation.md) | COMPLETE |
| 0053 | 2 | WP-014 | S1 — Coding | [Tensor decompositions](phase-2/0053-wp014-s1-tensor-decompositions.md) | COMPLETE |
| 0054 | 2 | WP-014 | S2 — Audit | [Tensor decompositions](phase-2/0054-wp014-s2-tensor-decompositions.md) | COMPLETE |
| 0055 | 2 | WP-014 | S3 — Remediation | [Tensor decompositions](phase-2/0055-wp014-s3-tensor-decompositions.md) | COMPLETE |
| 0056 | 2 | WP-014 | S4 — Documentation | [Tensor decompositions](phase-2/0056-wp014-s4-tensor-decompositions.md) | COMPLETE |
| 0057 | 2 | WP-015 | S1 — Coding | [OscilloSim sparse simulation engine](phase-2/0057-wp015-s1-oscillosim-sparse-simulation-engine.md) | COMPLETE |
| 0058 | 2 | WP-015 | S2 — Audit | [OscilloSim sparse simulation engine](phase-2/0058-wp015-s2-oscillosim-sparse-simulation-engine.md) | COMPLETE |
| 0059 | 2 | WP-015 | S3 — Remediation | [OscilloSim sparse simulation engine](phase-2/0059-wp015-s3-oscillosim-sparse-simulation-engine.md) | COMPLETE |
| 0060 | 2 | WP-015 | S4 — Documentation | [OscilloSim sparse simulation engine](phase-2/0060-wp015-s4-oscillosim-sparse-simulation-engine.md) | COMPLETE |
| 0061 | 2 | WP-016 | S1 — Coding | [Parallel sweeps, CPU optimization, and Phase 2 gate](phase-2/0061-wp016-s1-parallel-sweeps-cpu-optimization-and-phase-2-gate.md) | COMPLETE |
| 0062 | 2 | WP-016 | S2 — Audit | [Parallel sweeps, CPU optimization, and Phase 2 gate](phase-2/0062-wp016-s2-parallel-sweeps-cpu-optimization-and-phase-2-gate.md) | COMPLETE |
| 0063 | 2 | WP-016 | S3 — Remediation | [Parallel sweeps, CPU optimization, and Phase 2 gate](phase-2/0063-wp016-s3-parallel-sweeps-cpu-optimization-and-phase-2-gate.md) | COMPLETE |
| 0064 | 2 | WP-016 | S4 — Documentation | [Parallel sweeps, CPU optimization, and Phase 2 gate](phase-2/0064-wp016-s4-parallel-sweeps-cpu-optimization-and-phase-2-gate.md) | COMPLETE |
| 0065 | 3 | WP-017 | S1 — Coding | [Kernel architecture and CPU references](phase-3/0065-wp017-s1-kernel-architecture-and-cpu-references.md) | COMPLETE |
| 0066 | 3 | WP-017 | S2 — Audit | [Kernel architecture and CPU references](phase-3/0066-wp017-s2-kernel-architecture-and-cpu-references.md) | COMPLETE |
| 0067 | 3 | WP-017 | S3 — Remediation | [Kernel architecture and CPU references](phase-3/0067-wp017-s3-kernel-architecture-and-cpu-references.md) | COMPLETE |
| 0068 | 3 | WP-017 | S4 — Documentation | [Kernel architecture and CPU references](phase-3/0068-wp017-s4-kernel-architecture-and-cpu-references.md) | COMPLETE |
| 0069 | 3 | WP-018 | S1 — Coding | [Fused mean-field RK4 kernel](phase-3/0069-wp018-s1-fused-mean-field-rk4-kernel.md) | COMPLETE |
| 0070 | 3 | WP-018 | S2 — Audit | [Fused mean-field RK4 kernel](phase-3/0070-wp018-s2-fused-mean-field-rk4-kernel.md) | COMPLETE |
| 0071 | 3 | WP-018 | S3 — Remediation | [Fused mean-field RK4 kernel](phase-3/0071-wp018-s3-fused-mean-field-rk4-kernel.md) | COMPLETE |
| 0072 | 3 | WP-018 | S4 — Documentation | [Fused mean-field RK4 kernel](phase-3/0072-wp018-s4-fused-mean-field-rk4-kernel.md) | COMPLETE |
| 0073 | 3 | WP-019 | S1 — Coding | [Sparse k-NN and PAC kernels](phase-3/0073-wp019-s1-sparse-k-nn-and-pac-kernels.md) | COMPLETE |
| 0074 | 3 | WP-019 | S2 — Audit | [Sparse k-NN and PAC kernels](phase-3/0074-wp019-s2-sparse-k-nn-and-pac-kernels.md) | COMPLETE |
| 0075 | 3 | WP-019 | S3 — Remediation | [Sparse k-NN and PAC kernels](phase-3/0075-wp019-s3-sparse-k-nn-and-pac-kernels.md) | COMPLETE |
| 0076 | 3 | WP-019 | S4 — Documentation | [Sparse k-NN and PAC kernels](phase-3/0076-wp019-s4-sparse-k-nn-and-pac-kernels.md) | COMPLETE |
| 0077 | 3 | WP-020 | S1 — Coding | [Fused discrete step and reductions](phase-3/0077-wp020-s1-fused-discrete-step-and-reductions.md) | COMPLETE |
| 0078 | 3 | WP-020 | S2 — Audit | [Fused discrete step and reductions](phase-3/0078-wp020-s2-fused-discrete-step-and-reductions.md) | COMPLETE |
| 0079 | 3 | WP-020 | S3 — Remediation | [Fused discrete step and reductions](phase-3/0079-wp020-s3-fused-discrete-step-and-reductions.md) | COMPLETE |
| 0080 | 3 | WP-020 | S4 — Documentation | [Fused discrete step and reductions](phase-3/0080-wp020-s4-fused-discrete-step-and-reductions.md) | COMPLETE |
| 0081 | 3 | WP-021 | S1 — Coding | [GPU integration and Phase 3 gate](phase-3/0081-wp021-s1-gpu-integration-and-phase-3-gate.md) | COMPLETE |
| 0082 | 3 | WP-021 | S2 — Audit | [GPU integration and Phase 3 gate](phase-3/0082-wp021-s2-gpu-integration-and-phase-3-gate.md) | COMPLETE |
| 0083 | 3 | WP-021 | S3 — Remediation | [GPU integration and Phase 3 gate](phase-3/0083-wp021-s3-gpu-integration-and-phase-3-gate.md) | COMPLETE |
| 0084 | 3 | WP-021 | S4 — Documentation | [GPU integration and Phase 3 gate](phase-3/0084-wp021-s4-gpu-integration-and-phase-3-gate.md) | COMPLETE |
| 0085 | 4 | WP-022 | S1 — Coding | [Trainable bands and resonance primitives](phase-4/0085-wp022-s1-trainable-bands-and-resonance-primitives.md) | COMPLETE |
| 0086 | 4 | WP-022 | S2 — Audit | [Trainable bands and resonance primitives](phase-4/0086-wp022-s2-trainable-bands-and-resonance-primitives.md) | COMPLETE |
| 0087 | 4 | WP-022 | S3 — Remediation | [Trainable bands and resonance primitives](phase-4/0087-wp022-s3-trainable-bands-and-resonance-primitives.md) | COMPLETE |
| 0088 | 4 | WP-022 | S4 — Documentation | [Trainable bands and resonance primitives](phase-4/0088-wp022-s4-trainable-bands-and-resonance-primitives.md) | COMPLETE |
| 0089 | 4 | WP-023 | S1 — Coding | [Inhibition, activations, and HEP](phase-4/0089-wp023-s1-inhibition-activations-and-hep.md) | COMPLETE |
| 0090 | 4 | WP-023 | S2 — Audit | [Inhibition, activations, and HEP](phase-4/0090-wp023-s2-inhibition-activations-and-hep.md) | COMPLETE |
| 0091 | 4 | WP-023 | S3 — Remediation | [Inhibition, activations, and HEP](phase-4/0091-wp023-s3-inhibition-activations-and-hep.md) | COMPLETE |
| 0092 | 4 | WP-023 | S4 — Documentation | [Inhibition, activations, and HEP](phase-4/0092-wp023-s4-inhibition-activations-and-hep.md) | COMPLETE |
| 0093 | 4 | WP-024 | S1 — Coding | [Oscillator-aware optimizers](phase-4/0093-wp024-s1-oscillator-aware-optimizers.md) | COMPLETE |
| 0094 | 4 | WP-024 | S2 — Audit | [Oscillator-aware optimizers](phase-4/0094-wp024-s2-oscillator-aware-optimizers.md) | COMPLETE |
| 0095 | 4 | WP-024 | S3 — Remediation | [Oscillator-aware optimizers](phase-4/0095-wp024-s3-oscillator-aware-optimizers.md) | COMPLETE |
| 0096 | 4 | WP-024 | S4 — Documentation | [Oscillator-aware optimizers](phase-4/0096-wp024-s4-oscillator-aware-optimizers.md) | COMPLETE |
| 0097 | 4 | WP-025 | S1 — Coding | [Production Torch autograd bridge](phase-4/0097-wp025-s1-production-torch-autograd-bridge.md) | COMPLETE |
| 0098 | 4 | WP-025 | S2 — Audit | [Production Torch autograd bridge](phase-4/0098-wp025-s2-production-torch-autograd-bridge.md) | COMPLETE |
| 0099 | 4 | WP-025 | S3 — Remediation | [Production Torch autograd bridge](phase-4/0099-wp025-s3-production-torch-autograd-bridge.md) | COMPLETE |
| 0100 | 4 | WP-025 | S4 — Documentation | [Production Torch autograd bridge](phase-4/0100-wp025-s4-production-torch-autograd-bridge.md) | COMPLETE |
| 0101 | 4 | WP-026 | S1 — Coding | [PhaseTracker, Hybrid, baselines, and allocation](phase-4/0101-wp026-s1-phasetracker-hybrid-baselines-and-allocation.md) | COMPLETE |
| 0102 | 4 | WP-026 | S2 — Audit | [PhaseTracker, Hybrid, baselines, and allocation](phase-4/0102-wp026-s2-phasetracker-hybrid-baselines-and-allocation.md) | COMPLETE |
| 0103 | 4 | WP-026 | S3 — Remediation | [PhaseTracker, Hybrid, baselines, and allocation](phase-4/0103-wp026-s3-phasetracker-hybrid-baselines-and-allocation.md) | COMPLETE |
| 0104 | 4 | WP-026 | S4 — Documentation | [PhaseTracker, Hybrid, baselines, and allocation](phase-4/0104-wp026-s4-phasetracker-hybrid-baselines-and-allocation.md) | COMPLETE |
| 0105 | 4 | WP-027 | S1 — Coding | [Trainable-stack integration and Phase 4 gate](phase-4/0105-wp027-s1-trainable-stack-integration-and-phase-4-gate.md) | COMPLETE |
| 0106 | 4 | WP-027 | S2 — Audit | [Trainable-stack integration and Phase 4 gate](phase-4/0106-wp027-s2-trainable-stack-integration-and-phase-4-gate.md) | COMPLETE |
| 0107 | 4 | WP-027 | S3 — Remediation | [Trainable-stack integration and Phase 4 gate](phase-4/0107-wp027-s3-trainable-stack-integration-and-phase-4-gate.md) | COMPLETE |
| 0108 | 4 | WP-027 | S4 — Documentation | [Trainable-stack integration and Phase 4 gate](phase-4/0108-wp027-s4-trainable-stack-integration-and-phase-4-gate.md) | COMPLETE |
| 0109 | 5 | WP-028 | S1 — Coding | [ONNX controller and backend selection](phase-5/0109-wp028-s1-onnx-controller-and-backend-selection.md) | COMPLETE |
| 0110 | 5 | WP-028 | S2 — Audit | [ONNX controller and backend selection](phase-5/0110-wp028-s2-onnx-controller-and-backend-selection.md) | COMPLETE |
| 0111 | 5 | WP-028 | S3 — Remediation | [ONNX controller and backend selection](phase-5/0111-wp028-s3-onnx-controller-and-backend-selection.md) | COMPLETE |
| 0112 | 5 | WP-028 | S4 — Documentation | [ONNX controller and backend selection](phase-5/0112-wp028-s4-onnx-controller-and-backend-selection.md) | COMPLETE |
| 0113 | 5 | WP-029 | S1 — Coding | [Daemon runtime and lock-free control buffer](phase-5/0113-wp029-s1-daemon-runtime-and-lock-free-control-buffer.md) | COMPLETE |
| 0114 | 5 | WP-029 | S2 — Audit | [Daemon runtime and lock-free control buffer](phase-5/0114-wp029-s2-daemon-runtime-and-lock-free-control-buffer.md) | COMPLETE |
| 0115 | 5 | WP-029 | S3 — Remediation | [Daemon runtime and lock-free control buffer](phase-5/0115-wp029-s3-daemon-runtime-and-lock-free-control-buffer.md) | COMPLETE |
| 0116 | 5 | WP-029 | S4 — Documentation | [Daemon runtime and lock-free control buffer](phase-5/0116-wp029-s4-daemon-runtime-and-lock-free-control-buffer.md) | COMPLETE |
| 0117 | 5 | WP-030 | S1 — Coding | [Training hooks and MOT evaluation](phase-5/0117-wp030-s1-training-hooks-and-mot-evaluation.md) | COMPLETE |
| 0118 | 5 | WP-030 | S2 — Audit | [Training hooks and MOT evaluation](phase-5/0118-wp030-s2-training-hooks-and-mot-evaluation.md) | COMPLETE |
| 0119 | 5 | WP-030 | S3 — Remediation | [Training hooks and MOT evaluation](phase-5/0119-wp030-s3-training-hooks-and-mot-evaluation.md) | COMPLETE |
| 0120 | 5 | WP-030 | S4 — Documentation | [Training hooks and MOT evaluation](phase-5/0120-wp030-s4-training-hooks-and-mot-evaluation.md) | COMPLETE |
| 0121 | 5 | WP-031 | S1 — Coding | [Temporal experiments, statistics, and adversarial tooling](phase-5/0121-wp031-s1-temporal-experiments-statistics-and-adversarial-tooling.md) | COMPLETE |
| 0122 | 5 | WP-031 | S2 — Audit | [Temporal experiments, statistics, and adversarial tooling](phase-5/0122-wp031-s2-temporal-experiments-statistics-and-adversarial-tooling.md) | COMPLETE |
| 0123 | 5 | WP-031 | S3 — Remediation | [Temporal experiments, statistics, and adversarial tooling](phase-5/0123-wp031-s3-temporal-experiments-statistics-and-adversarial-tooling.md) | COMPLETE |
| 0124 | 5 | WP-031 | S4 — Documentation | [Temporal experiments, statistics, and adversarial tooling](phase-5/0124-wp031-s4-temporal-experiments-statistics-and-adversarial-tooling.md) | COMPLETE |
| 0125 | 5 | WP-032 | S1 — Coding | [Daemon/evaluation integration and Phase 5 gate](phase-5/0125-wp032-s1-daemon-evaluation-integration-and-phase-5-gate.md) | COMPLETE |
| 0126 | 5 | WP-032 | S2 — Audit | [Daemon/evaluation integration and Phase 5 gate](phase-5/0126-wp032-s2-daemon-evaluation-integration-and-phase-5-gate.md) | COMPLETE |
| 0127 | 5 | WP-032 | S3 — Remediation | [Daemon/evaluation integration and Phase 5 gate](phase-5/0127-wp032-s3-daemon-evaluation-integration-and-phase-5-gate.md) | COMPLETE |
| 0128 | 5 | WP-032 | S4 — Documentation | [Daemon/evaluation integration and Phase 5 gate](phase-5/0128-wp032-s4-daemon-evaluation-integration-and-phase-5-gate.md) | COMPLETE |
| 0129 | 6 | WP-033 | S1 — Coding | [Unified benchmark runner and category migration](phase-6/0129-wp033-s1-unified-benchmark-runner-and-category-migration.md) | COMPLETE |
| 0130 | 6 | WP-033 | S2 — Audit | [Unified benchmark runner and category migration](phase-6/0130-wp033-s2-unified-benchmark-runner-and-category-migration.md) | COMPLETE |
| 0131 | 6 | WP-033 | S3 — Remediation | [Unified benchmark runner and category migration](phase-6/0131-wp033-s3-unified-benchmark-runner-and-category-migration.md) | COMPLETE |
| 0132 | 6 | WP-033 | S4 — Documentation | [Unified benchmark runner and category migration](phase-6/0132-wp033-s4-unified-benchmark-runner-and-category-migration.md) | COMPLETE |
| 0133 | 6 | WP-034 | S1 — Coding | [Reporting, figures, tables, and profiling](phase-6/0133-wp034-s1-reporting-figures-tables-and-profiling.md) | COMPLETE |
| 0134 | 6 | WP-034 | S2 — Audit | [Reporting, figures, tables, and profiling](phase-6/0134-wp034-s2-reporting-figures-tables-and-profiling.md) | COMPLETE |
| 0135 | 6 | WP-034 | S3 — Remediation | [Reporting, figures, tables, and profiling](phase-6/0135-wp034-s3-reporting-figures-tables-and-profiling.md) | COMPLETE |
| 0136 | 6 | WP-034 | S4 — Documentation | [Reporting, figures, tables, and profiling](phase-6/0136-wp034-s4-reporting-figures-tables-and-profiling.md) | COMPLETE |
| 0137 | 6 | WP-035 | S1 — Coding | [Reproduction pipeline and manifest](phase-6/0137-wp035-s1-reproduction-pipeline-and-manifest.md) | COMPLETE |
| 0138 | 6 | WP-035 | S2 — Audit | [Reproduction pipeline and manifest](phase-6/0138-wp035-s2-reproduction-pipeline-and-manifest.md) | COMPLETE |
| 0139 | 6 | WP-035 | S3 — Remediation | [Reproduction pipeline and manifest](phase-6/0139-wp035-s3-reproduction-pipeline-and-manifest.md) | COMPLETE |
| 0140 | 6 | WP-035 | S4 — Documentation | [Reproduction pipeline and manifest](phase-6/0140-wp035-s4-reproduction-pipeline-and-manifest.md) | COMPLETE |
| 0141 | 6 | WP-036 | S1 — Coding | [API completion, acceptance suite, and migration](phase-6/0141-wp036-s1-api-completion-acceptance-suite-and-migration.md) | PLANNED |
| 0141A | 6 | WP-036 | S1 — Coding | [Freeze machinery, re-export surface, aliases, D-D stubs](phase-6/0141A-wp036-s1a-freeze-machinery-and-reexport-surface.md) | COMPLETE |
| 0141B | 6 | WP-036 | S1 — Coding | [prin-tensor and prin-train Python bindings](phase-6/0141B-wp036-s1b-tensor-and-train-bindings.md) | COMPLETE |
| 0141C | 6 | WP-036 | S1 — Coding | [prin-kernels reference-fn bindings and DV-012 sweep bindings](phase-6/0141C-wp036-s1c-kernels-bindings-and-dv012.md) | COMPLETE |
| 0141D1 | 6 | WP-036 | S1 — Coding | [Net-new Python surface, part 1 — Bucket G solver family](phase-6/0141D1-wp036-s1d1-net-new-python-surface-solver-family.md) | COMPLETE |
| 0141D2 | 6 | WP-036 | S1 — Coding | [Net-new Python surface, part 2 — Bucket G remainder](phase-6/0141D2-wp036-s1d2-net-new-python-surface-remainder.md) | COMPLETE |
| 0141E | 6 | WP-036 | S1 — Coding | [Consolidation — Migration Guide table, smoke matrix, traceability, handoff](phase-6/0141E-wp036-s1e-consolidation-and-handoff.md) | COMPLETE |
| 0142 | 6 | WP-036 | S2 — Audit | [API completion, acceptance suite, and migration](phase-6/0142-wp036-s2-api-completion-acceptance-suite-and-migration.md) | COMPLETE |
| 0143 | 6 | WP-036 | S3 — Remediation | [API completion, acceptance suite, and migration](phase-6/0143-wp036-s3-api-completion-acceptance-suite-and-migration.md) | COMPLETE |
| 0144 | 6 | WP-036 | S4 — Documentation | [API completion, acceptance suite, and migration](phase-6/0144-wp036-s4-api-completion-acceptance-suite-and-migration.md) | COMPLETE |
| 0144A | 6 | WP-036A | S1 — Coding | [Trainable compatibility layers — `prin-train` extension](phase-6/0144A-wp036a-s1-trainable-compatibility-layers-prin-train-extension.md) | COMPLETE |
| 0144A1 | 6 | WP-036A | S1 — Coding | [Inhibition and sparsification family](phase-6/0144A1-wp036a-s1-inhibition-and-sparsification-family.md) | COMPLETE |
| 0144A2 | 6 | WP-036A | S1 — Coding | [Phase-to-rate and autoencoder family](phase-6/0144A2-wp036a-s1-phase-to-rate-and-autoencoder-family.md) | COMPLETE |
| 0144A3 | 6 | WP-036A | S1 — Coding | [Hierarchical, PAC, and discrete-layer family](phase-6/0144A3-wp036a-s1-hierarchical-pac-and-discrete-layer-family.md) | COMPLETE |
| 0144A4 | 6 | WP-036A | S1 — Coding | [Model container and consolidation](phase-6/0144A4-wp036a-s1-model-container-and-consolidation.md) | COMPLETE |
| 0144B | 6 | WP-036A | S2 — Audit | [Trainable compatibility layers — `prin-train` extension](phase-6/0144B-wp036a-s2-trainable-compatibility-layers-prin-train-extension.md) | COMPLETE |
| 0144C | 6 | WP-036A | S3 — Remediation | [Trainable compatibility layers — `prin-train` extension](phase-6/0144C-wp036a-s3-trainable-compatibility-layers-prin-train-extension.md) | COMPLETE |
| 0144D | 6 | WP-036A | S4 — Documentation | [Trainable compatibility layers — `prin-train` extension](phase-6/0144D-wp036a-s4-trainable-compatibility-layers-prin-train-extension.md) | COMPLETE |
| 0144E | 6 | WP-036B | S1 — Coding | [Acceptance suite port — core, dynamics, model stack, subconscious](phase-6/0144E-wp036b-s1-acceptance-suite-port-core-dynamics-model-stack.md) | COMPLETE |
| 0144E1 | 6 | WP-036B | S1 — Coding | [Core and utils strict port](phase-6/0144E1-wp036b-s1-core-and-utils-strict-port.md) | COMPLETE |
| 0144E2 | 6 | WP-036B | S1 — Coding | [Phases, hierarchical, and phase-to-rate strict port](phase-6/0144E2-wp036b-s1-phases-hierarchical-and-phase-to-rate-strict-port.md) | COMPLETE |
| 0144E3 | 6 | WP-036B | S1 — Coding | [Q2 and Q2-remaining strict port](phase-6/0144E3-wp036b-s1-q2-and-q2-remaining-strict-port.md) | COMPLETE |
| 0144E4 | 6 | WP-036B | S1 — Coding | [Q3-new, NN, and SCALR-enhanced strict port](phase-6/0144E4-wp036b-s1-q3-nn-and-scalr-enhanced-strict-port.md) | COMPLETE |
| 0144E5 | 6 | WP-036B | S1 — Coding | [Hybrid and CLEVR-N strict port](phase-6/0144E5-wp036b-s1-hybrid-and-clevr-n-strict-port.md) | COMPLETE |
| 0144E6 | 6 | WP-036B | S1 — Coding | [Subconscious strict port and consolidation](phase-6/0144E6-wp036b-s1-subconscious-and-consolidation.md) | COMPLETE |
| 0144F | 6 | WP-036B | S2 — Audit | [Acceptance suite port — core, dynamics, model stack, subconscious](phase-6/0144F-wp036b-s2-acceptance-suite-port-core-dynamics-model-stack.md) | COMPLETE |
| 0144G | 6 | WP-036B | S3 — Remediation | [Acceptance suite port — core, dynamics, model stack, subconscious](phase-6/0144G-wp036b-s3-acceptance-suite-port-core-dynamics-model-stack.md) | COMPLETE |
| 0144H | 6 | WP-036B | S4 — Documentation | [Acceptance suite port — core, dynamics, model stack, subconscious](phase-6/0144H-wp036b-s4-acceptance-suite-port-core-dynamics-model-stack.md) | COMPLETE |
| 0144I | 6 | WP-036D | S1 — Coding | [GPU execution path for the ported acceptance suite](phase-6/0144I-wp036d-s1-gpu-execution-path-ported-acceptance-suite.md) | COMPLETE |
| 0144I1 | 6 | WP-036D | S1 — Coding | [PyO3 GPU binding layer](phase-6/0144I1-wp036d-s1-pyo3-gpu-binding-layer.md) | COMPLETE |
| 0144I2 | 6 | WP-036D | S1 — Coding | [Python device dispatch and DLPack marshalling](phase-6/0144I2-wp036d-s1-device-dispatch-and-dlpack-marshalling.md) | COMPLETE |
| 0144I3 | 6 | WP-036D | S1 — Coding | [GPU test activation, CI, and consolidation](phase-6/0144I3-wp036d-s1-gpu-test-activation-and-ci.md) | COMPLETE |
| 0144J | 6 | WP-036D | S2 — Audit | [GPU execution path for the ported acceptance suite](phase-6/0144J-wp036d-s2-gpu-execution-path-ported-acceptance-suite.md) | COMPLETE |
| 0144K | 6 | WP-036D | S3 — Remediation | [GPU execution path for the ported acceptance suite](phase-6/0144K-wp036d-s3-gpu-execution-path-ported-acceptance-suite.md) | COMPLETE |
| 0144L | 6 | WP-036D | S4 — Documentation | [GPU execution path for the ported acceptance suite](phase-6/0144L-wp036d-s4-gpu-execution-path-ported-acceptance-suite.md) | COMPLETE |
| 0144M | 6 | WP-036C | S1 — Coding | [Acceptance suite port — integration, y-series, kernels; DV-025](phase-6/0144M-wp036c-s1-acceptance-suite-port-integration-y-series-kernels.md) | PLANNED |
| 0144M1 | 6 | WP-036C | S1 — Coding | [Integration-Q3 and Y2Q1/Y2Q4 strict port](phase-6/0144M1-wp036c-s1-integration-q3-and-y2q1-y2q4-strict-port.md) | COMPLETE |
| 0144M2 | 6 | WP-036C | S1 — Coding | [Y2Q2/Y2Q3 strict port and DV-025 retrain_controller](phase-6/0144M2-wp036c-s1-y2q2-y2q3-strict-port-and-dv025.md) | COMPLETE |
| 0144M3 | 6 | WP-036C | S1 — Coding | [Y3Q1/Y3Q2 strict port](phase-6/0144M3-wp036c-s1-y3q1-y3q2-strict-port.md) | COMPLETE |
| 0144M4 | 6 | WP-036C | S1 — Coding | [Y3Q3/Y3Q4/Y3Q45/Y3Q49 strict port](phase-6/0144M4-wp036c-s1-y3q3-y3q4-y3q45-y3q49-strict-port.md) | COMPLETE |
| 0144M5 | 6 | WP-036C | S1 — Coding | [Y4Q1/Y4Q1_2/Y4Q1_3 strict port](phase-6/0144M5-wp036c-s1-y4q1-y4q1-2-y4q1-3-strict-port.md) | COMPLETE |
| 0144M6 | 6 | WP-036C | S1 — Coding | [Y4Q1_4/Y4Q1_5/Y4Q1_9 strict port](phase-6/0144M6-wp036c-s1-y4q1-4-y4q1-5-y4q1-9-strict-port.md) | COMPLETE |
| 0144M7 | 6 | WP-036C | S1 — Coding | [Y4Q1_7/Y4Q1_8 strict port](phase-6/0144M7-wp036c-s1-y4q1-7-y4q1-8-strict-port.md) | COMPLETE |
| 0144M8 | 6 | WP-036C | S1 — Coding | [Y4Q2/Y4Q3/Y4Q4, GPU/Triton guards, and consolidation](phase-6/0144M8-wp036c-s1-y4q2-y4q3-y4q4-kernels-and-consolidation.md) | COMPLETE |
| 0144N | 6 | WP-036C | S2 — Audit | [Acceptance suite port — integration, y-series, kernels; DV-025](phase-6/0144N-wp036c-s2-acceptance-suite-port-integration-y-series-kernels.md) | COMPLETE |
| 0144O | 6 | WP-036C | S3 — Remediation | [Acceptance suite port — integration, y-series, kernels; DV-025](phase-6/0144O-wp036c-s3-acceptance-suite-port-integration-y-series-kernels.md) | COMPLETE |
| 0144P | 6 | WP-036C | S4 — Documentation | [Acceptance suite port — integration, y-series, kernels; DV-025](phase-6/0144P-wp036c-s4-acceptance-suite-port-integration-y-series-kernels.md) | COMPLETE |
| 0144Q | 6 | WP-036E | S1 — Coding | [GPU device-resident execution path](phase-6/0144Q-wp036e-s1-gpu-device-resident-execution-path.md) | PLANNED |
| 0144Q1 | 6 | WP-036E | S1 — Coding | [`prin-kernels` device-`Handle` dispatch layer](phase-6/0144Q1-wp036e-s1-prin-kernels-device-handle-dispatch-layer.md) | COMPLETE |
| 0144Q2 | 6 | WP-036E | S1 — Coding | [`prin-sim` persistent device buffers + DV-003 on-device combine](phase-6/0144Q2-wp036e-s1-prin-sim-persistent-device-buffers-dv003.md) | COMPLETE |
| 0144Q3 | 6 | WP-036E | S1 — Coding | [`prin-py` export zero-copy DLPack, `_torch_compat.py` device path, test activation](phase-6/0144Q3-wp036e-s1-prin-py-export-zero-copy-dlpack-torch-compat-test-activation.md) | COMPLETE |
| 0144R | 6 | WP-036E | S2 — Audit | [GPU device-resident execution path](phase-6/0144R-wp036e-s2-gpu-device-resident-execution-path.md) | COMPLETE |
| 0144S | 6 | WP-036E | S3 — Remediation | [GPU device-resident execution path](phase-6/0144S-wp036e-s3-gpu-device-resident-execution-path.md) | COMPLETE |
| 0144T | 6 | WP-036E | S4 — Documentation | [GPU device-resident execution path](phase-6/0144T-wp036e-s4-gpu-device-resident-execution-path.md) | COMPLETE |
| 0144U | 6 | WP-036F | S1 — Coding | [DirectML controller-graph execution](phase-6/0144U-wp036f-s1-directml-controller-graph-execution.md) | COMPLETE |
| 0144V | 6 | WP-036F | S2 — Audit | [DirectML controller-graph execution](phase-6/0144V-wp036f-s2-directml-controller-graph-execution.md) | COMPLETE |
| 0144W | 6 | WP-036F | S3 — Remediation | [DirectML controller-graph execution](phase-6/0144W-wp036f-s3-directml-controller-graph-execution.md) | COMPLETE |
| 0144X | 6 | WP-036F | S4 — Documentation | [DirectML controller-graph execution](phase-6/0144X-wp036f-s4-directml-controller-graph-execution.md) | COMPLETE |
| 0144Y | 6 | WP-036G | S1 — Coding | [Deferred-Validation register consolidation and permanent dispositions](phase-6/0144Y-wp036g-s1-dv-register-consolidation-and-permanent-dispositions.md) | COMPLETE |
| 0144Z | 6 | WP-036G | S2 — Audit | [Deferred-Validation register consolidation and permanent dispositions](phase-6/0144Z-wp036g-s2-dv-register-consolidation-and-permanent-dispositions.md) | COMPLETE |
| 0144AA | 6 | WP-036G | S3 — Remediation | [Deferred-Validation register consolidation and permanent dispositions](phase-6/0144AA-wp036g-s3-dv-register-consolidation-and-permanent-dispositions.md) | COMPLETE |
| 0144AB | 6 | WP-036G | S4 — Documentation | [Deferred-Validation register consolidation and permanent dispositions](phase-6/0144AB-wp036g-s4-dv-register-consolidation-and-permanent-dispositions.md) | COMPLETE |
| 0145 | 6 | WP-037 | S1 — Coding | [Documentation, notebooks, paper, and Parity Report draft](phase-6/0145-wp037-s1-documentation-notebooks-paper-and-parity-report-draft.md) | COMPLETE |
| 0146 | 6 | WP-037 | S2 — Audit | [Documentation, notebooks, paper, and Parity Report draft](phase-6/0146-wp037-s2-documentation-notebooks-paper-and-parity-report-draft.md) | COMPLETE |
| 0147 | 6 | WP-037 | S3 — Remediation | [Documentation, notebooks, paper, and Parity Report draft](phase-6/0147-wp037-s3-documentation-notebooks-paper-and-parity-report-draft.md) | PLANNED |
| 0148 | 6 | WP-037 | S4 — Documentation | [Documentation, notebooks, paper, and Parity Report draft](phase-6/0148-wp037-s4-documentation-notebooks-paper-and-parity-report-draft.md) | PLANNED |
| 0149 | 6 | WP-038 | S1 — Coding | [RC1 packaging and Phase 6 gate](phase-6/0149-wp038-s1-rc1-packaging-and-phase-6-gate.md) | PLANNED |
| 0150 | 6 | WP-038 | S2 — Audit | [RC1 packaging and Phase 6 gate](phase-6/0150-wp038-s2-rc1-packaging-and-phase-6-gate.md) | PLANNED |
| 0151 | 6 | WP-038 | S3 — Remediation | [RC1 packaging and Phase 6 gate](phase-6/0151-wp038-s3-rc1-packaging-and-phase-6-gate.md) | PLANNED |
| 0152 | 6 | WP-038 | S4 — Documentation | [RC1 packaging and Phase 6 gate](phase-6/0152-wp038-s4-rc1-packaging-and-phase-6-gate.md) | PLANNED |
| 0153 | 7 | Campaign | E0 — Campaign planning | [Approve and freeze Phase 7 campaign plan](phase-7/0153-campaign-e0-planning.md) | PLANNED |
| 0154 | 7 | EXP-001/C1 | E1 — Pre-registration | [Golden-trajectory numerical parity](phase-7/0154-exp001-e1-golden-trajectory-numerical-parity.md) | PLANNED |
| 0155 | 7 | EXP-001/C1 | E2 — Review and approval | [Golden-trajectory numerical parity](phase-7/0155-exp001-e2-golden-trajectory-numerical-parity.md) | PLANNED |
| 0156 | 7 | EXP-001/C1 | E3 — Execution | [Golden-trajectory numerical parity](phase-7/0156-exp001-e3-golden-trajectory-numerical-parity.md) | PLANNED |
| 0157 | 7 | EXP-001/C1 | E4 — Analysis | [Golden-trajectory numerical parity](phase-7/0157-exp001-e4-golden-trajectory-numerical-parity.md) | PLANNED |
| 0158 | 7 | EXP-001/C1 | E5 — Report | [Golden-trajectory numerical parity](phase-7/0158-exp001-e5-golden-trajectory-numerical-parity.md) | PLANNED |
| 0159 | 7 | EXP-002/C1 | E1 — Pre-registration | [API, benchmark-result, and reproduction parity](phase-7/0159-exp002-e1-api-benchmark-result-and-reproduction-parity.md) | PLANNED |
| 0160 | 7 | EXP-002/C1 | E2 — Review and approval | [API, benchmark-result, and reproduction parity](phase-7/0160-exp002-e2-api-benchmark-result-and-reproduction-parity.md) | PLANNED |
| 0161 | 7 | EXP-002/C1 | E3 — Execution | [API, benchmark-result, and reproduction parity](phase-7/0161-exp002-e3-api-benchmark-result-and-reproduction-parity.md) | PLANNED |
| 0162 | 7 | EXP-002/C1 | E4 — Analysis | [API, benchmark-result, and reproduction parity](phase-7/0162-exp002-e4-api-benchmark-result-and-reproduction-parity.md) | PLANNED |
| 0163 | 7 | EXP-002/C1 | E5 — Report | [API, benchmark-result, and reproduction parity](phase-7/0163-exp002-e5-api-benchmark-result-and-reproduction-parity.md) | PLANNED |
| 0164 | 7 | EXP-003/C2 | E1 — Pre-registration | [CPU scaling and sweep performance](phase-7/0164-exp003-e1-cpu-scaling-and-sweep-performance.md) | PLANNED |
| 0165 | 7 | EXP-003/C2 | E2 — Review and approval | [CPU scaling and sweep performance](phase-7/0165-exp003-e2-cpu-scaling-and-sweep-performance.md) | PLANNED |
| 0166 | 7 | EXP-003/C2 | E3 — Execution | [CPU scaling and sweep performance](phase-7/0166-exp003-e3-cpu-scaling-and-sweep-performance.md) | PLANNED |
| 0167 | 7 | EXP-003/C2 | E4 — Analysis | [CPU scaling and sweep performance](phase-7/0167-exp003-e4-cpu-scaling-and-sweep-performance.md) | PLANNED |
| 0168 | 7 | EXP-003/C2 | E5 — Report | [CPU scaling and sweep performance](phase-7/0168-exp003-e5-cpu-scaling-and-sweep-performance.md) | PLANNED |
| 0169 | 7 | EXP-004/C2 | E1 — Pre-registration | [GPU kernels and Torch bridge performance](phase-7/0169-exp004-e1-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0170 | 7 | EXP-004/C2 | E2 — Review and approval | [GPU kernels and Torch bridge performance](phase-7/0170-exp004-e2-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0171 | 7 | EXP-004/C2 | E3 — Execution | [GPU kernels and Torch bridge performance](phase-7/0171-exp004-e3-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0172 | 7 | EXP-004/C2 | E4 — Analysis | [GPU kernels and Torch bridge performance](phase-7/0172-exp004-e4-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0173 | 7 | EXP-004/C2 | E5 — Report | [GPU kernels and Torch bridge performance](phase-7/0173-exp004-e5-gpu-kernels-and-torch-bridge-performance.md) | PLANNED |
| 0174 | 7 | EXP-005/C3 | E1 — Pre-registration | [Dynamics, chimera, and capacity replication](phase-7/0174-exp005-e1-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0175 | 7 | EXP-005/C3 | E2 — Review and approval | [Dynamics, chimera, and capacity replication](phase-7/0175-exp005-e2-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0176 | 7 | EXP-005/C3 | E3 — Execution | [Dynamics, chimera, and capacity replication](phase-7/0176-exp005-e3-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0177 | 7 | EXP-005/C3 | E4 — Analysis | [Dynamics, chimera, and capacity replication](phase-7/0177-exp005-e4-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0178 | 7 | EXP-005/C3 | E5 — Report | [Dynamics, chimera, and capacity replication](phase-7/0178-exp005-e5-dynamics-chimera-and-capacity-replication.md) | PLANNED |
| 0179 | 7 | EXP-006/C3 | E1 — Pre-registration | [Temporal binding, PhaseTracker, and ablation replication](phase-7/0179-exp006-e1-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0180 | 7 | EXP-006/C3 | E2 — Review and approval | [Temporal binding, PhaseTracker, and ablation replication](phase-7/0180-exp006-e2-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0181 | 7 | EXP-006/C3 | E3 — Execution | [Temporal binding, PhaseTracker, and ablation replication](phase-7/0181-exp006-e3-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0182 | 7 | EXP-006/C3 | E4 — Analysis | [Temporal binding, PhaseTracker, and ablation replication](phase-7/0182-exp006-e4-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0183 | 7 | EXP-006/C3 | E5 — Report | [Temporal binding, PhaseTracker, and ablation replication](phase-7/0183-exp006-e5-temporal-binding-phasetracker-and-ablation-replication.md) | PLANNED |
| 0184 | 7 | EXP-007/C3 | E1 — Pre-registration | [Daemon, MOT, and adversarial replication](phase-7/0184-exp007-e1-daemon-mot-and-adversarial-replication.md) | PLANNED |
| 0185 | 7 | EXP-007/C3 | E2 — Review and approval | [Daemon, MOT, and adversarial replication](phase-7/0185-exp007-e2-daemon-mot-and-adversarial-replication.md) | PLANNED |
| 0186 | 7 | EXP-007/C3 | E3 — Execution | [Daemon, MOT, and adversarial replication](phase-7/0186-exp007-e3-daemon-mot-and-adversarial-replication.md) | PLANNED |
| 0187 | 7 | EXP-007/C3 | E4 — Analysis | [Daemon, MOT, and adversarial replication](phase-7/0187-exp007-e4-daemon-mot-and-adversarial-replication.md) | PLANNED |
| 0188 | 7 | EXP-007/C3 | E5 — Report | [Daemon, MOT, and adversarial replication](phase-7/0188-exp007-e5-daemon-mot-and-adversarial-replication.md) | PLANNED |
| 0189 | 7 | EXP-008/C4 | E1 — Pre-registration | [Cross-platform and new-capability characterization](phase-7/0189-exp008-e1-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0190 | 7 | EXP-008/C4 | E2 — Review and approval | [Cross-platform and new-capability characterization](phase-7/0190-exp008-e2-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0191 | 7 | EXP-008/C4 | E3 — Execution | [Cross-platform and new-capability characterization](phase-7/0191-exp008-e3-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0192 | 7 | EXP-008/C4 | E4 — Analysis | [Cross-platform and new-capability characterization](phase-7/0192-exp008-e4-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0193 | 7 | EXP-008/C4 | E5 — Report | [Cross-platform and new-capability characterization](phase-7/0193-exp008-e5-cross-platform-and-new-capability-characterization.md) | PLANNED |
| 0194 | 7 | Campaign | E6 — Campaign synthesis | [Campaign synthesis and evidence reconciliation](phase-7/0194-campaign-e6-synthesis.md) | PLANNED |
| 0195 | 7 | WP-039 | S1 — Coding | [Stable-release evidence closure](phase-7/0195-wp039-s1-stable-release-evidence-closure.md) | PLANNED |
| 0196 | 7 | WP-039 | S2 — Comprehensive audit | [Stable-release evidence closure](phase-7/0196-wp039-s2-stable-release-evidence-closure.md) | PLANNED |
| 0197 | 7 | WP-039 | S3 — Remediation | [Stable-release evidence closure](phase-7/0197-wp039-s3-stable-release-evidence-closure.md) | PLANNED |
| 0198 | 7 | WP-039 | S4 — Documentation and release | [Stable-release evidence closure](phase-7/0198-wp039-s4-stable-release-evidence-closure.md) | PLANNED |
