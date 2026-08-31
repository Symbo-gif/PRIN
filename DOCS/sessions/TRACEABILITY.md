# Session-plan traceability matrix

This matrix proves that the numbered Session Execution Plan covers the
requirements, architecture invariants, parity obligations, roadmap exits,
risks, and Definition of Done. It maps **planned responsibility**, not
completion; completion evidence is cited by Audit and Project State Reports.

## 1. Functional requirements

| Requirement | Primary implementation sessions | Independent confirmation |
|---|---|---|
| **F1 — 175+ symbol feature parity** | WP-001 inventory (0001–0004); incremental WPs 006–036; WP-036 compatibility surface + freeze machinery + Migration Guide table (0141 + coding sub-passes `0141A`–`0141E`, amdt #32; audit/remediation/docs 0142–0144); WP-036A trainable compatibility layers (`0144A` + coding sub-passes `0144A1`–`0144A4`, amdt #34; audit/remediation/docs `0144B`–`0144D`); WP-036B strict acceptance-suite port (`0144E` + `0144E1`–`0144E6` feeding `0144F`–`0144H`, amdt #31/#33/#35); WP-036D GPU execution path for the ported suite (`0144I` + `0144I1`–`0144I3` feeding `0144J`–`0144L`, amdt #36); WP-036C acceptance-suite port (`0144M`–`0144P`, shifted by amdt #36) | EXP-002 E1–E5 (0159–0163); WP-039 audit (0196) |
| **F2 — numerical/result parity** | WP-002 corpus (0005–0008); all numerical WPs 006–032; WP-037 Parity draft | EXP-001 (0154–0158), EXP-002 (0159–0163), EXP-005–007 (0174–0188); synthesis 0194 |
| **F3 — differentiability/PyTorch interop** | WP-003 spike (0009–0012); WP-022–027 (0085–0108) | EXP-004 (0169–0173), EXP-006 (0179–0183); WP-039 audit |
| **F4 — byte-comparable reproduction** | WP-034–035 (0133–0140), WP-037 (0145–0148) | EXP-002 (0159–0163); synthesis 0194 |
| **F5 — CPU/DirectML/Ryzen AI controller** | WP-005 probe (0017–0020); WP-028–029 (0109–0116) | EXP-007–008 (0184–0193); WP-039 audit |

## 2. Non-functional requirements

| Requirement | Primary implementation sessions | Independent confirmation |
|---|---|---|
| **N1 — GPU/CPU/sweep performance** | WP-003–004 spikes; WP-016; WP-018–021; WP-027; WP-029 | EXP-003–004 (0164–0173), EXP-007 (0184–0188) |
| **N2 — Linux/Windows/macOS + graceful fallback** | WP-005; WP-017–021; WP-028; WP-038 | EXP-008 (0189–0193); stable-release audit |
| **N3 — safety, no unaudited unsafe/data races** | Every S1/S2/S3; especially WP-017, WP-025, WP-029 | Every S2 A6; comprehensive audit 0196 |
| **N4 — compiler-free wheels** | WP-005; WP-038 | EXP-008; final WP-039 |
| **N5 — strict typing/one algorithm one implementation** | WP-001 baseline; WP-006 onward; WP-017 backend architecture | Every S2 A2/A5/A7; comprehensive audit |
| **N6 — MIT** | Foundation metadata and packaging WPs | WP-038 and WP-039 audits |

## 3. Architecture invariants

| Invariant | Sessions owning design/enforcement | Audit evidence point |
|---|---|---|
| One algorithm, one implementation | WP-017 architecture; all kernel WPs; thin wrappers WP-011/WP-025 | A2 in every relevant S2; WP-021 S2 (0082); WP-039 S2 (0196) |
| No numerics in Python | WP-011, WP-025, WP-031, reporting WPs | A2 diff inspection in every affected S2; EXP-002 API audit |
| Explicit state and one Seed authority | WP-006; propagated through all stochastic WPs | WP-006 S2 (0022), parity EXP-001, comprehensive audit |
| Feature-flag/backend discipline | WP-005, WP-017–021, WP-028, WP-038 | Phase 3/5/6 exit audits and EXP-008 |
| Crate layering | WP-001 baseline; all Rust WPs | A2 dependency inspection every S2; WP-039 S2 |

## 4. Numerical-hazard traceability

| Hazard | Owning WP/session range | Campaign confirmation |
|---|---|---|
| Phase wrap `% 2π`, safe difference | WP-006 (0021–0024) | EXP-001 |
| Amplitude `[1e-6,10]`, derivative `±1e4` | WP-006–008 | EXP-001 |
| Coupling normalization `1/N` vs `1/k` | WP-009 (0033–0036), WP-019 | EXP-001/EXP-005 |
| `φ₁(λ) → 1` | WP-012 (0045–0048) | EXP-001 |
| STE hard-forward/soft-backward | WP-023 (0089–0092), bridge WP-025 | EXP-004/EXP-006 |
| Statistical—not pointwise—chaotic parity | WP-002 harness; WP-010/WP-015 | EXP-001/EXP-005 |

## 5. Phase exits

| Phase | Exit-owning session | Required evidence |
|---:|---|---|
| 0 | WP-005 S4 — **0020** | Three spikes decided; corpus committed; wheel/provider gates |
| 1 | WP-011 S4 — **0044** | All non-trainable dynamics parity/property suites green |
| 2 | WP-016 S4 — **0064** | N≤1M CPU parity; sweep/CPU speed targets |
| 3 | WP-021 S4 — **0084** | Kernel equivalence and approved GPU targets |
| 4 | WP-027 S4 — **0108** | PhaseTracker validation threshold, gradcheck, bridge <5% |
| 5 | WP-032 S4 — **0128** | Daemon latency and MOT reference equivalence |
| 6 | WP-038 S4 — **0152** | Repro/CI/docs/wheels green; RC1 published |
| 7 | WP-039 S4 — **0198** | Campaign complete; DoD clean; stable `1.0.0` released |

## 6. Risk register coverage

| Risk | Prevention/de-risk session | Detection/response |
|---:|---|---|
| R1 CubeCL misses Triton | WP-004 (0013–0016) | WP-021 gate; EXP-004; amendment/fallback correction cycle |
| R2 bridge overhead | WP-003 (0009–0012) | WP-025/027 gates; EXP-004 |
| R3 numerical drift | WP-002 before numerics | Every numerical S2; EXP-001/002/005–007 |
| R4 VitisAI gaps | WP-005 | WP-028; EXP-008; documented CPU/DirectML fallback |
| R5 autodiff gaps | WP-023/025 | Gradcheck audit; EXP-004/006 |
| R6 benchmark scope creep | WP-033 unified runner | WP-033 S2; EXP-002 coverage |
| R7 Rust ramp-up | dependency-first WP ordering | S2 every cycle; no phase advances with open findings |

## 7. Definition-of-Done traceability

| DoD item | Final evidence session(s) |
|---:|---|
| 1. Public API complete | WP-036 (compatibility surface + freeze machinery); EXP-002; 0196 |
| 2. Acceptance suite cross-platform | WP-036B (`0144E` + `0144E1`–`0144E6` strict port, then `0144F`–`0144H`), WP-036D (GPU execution path, `0144I`–`0144L`), and WP-036C (`0144M`–`0144P`); WP-038; 0196 |
| 3. Parity suite + Report | EXP-001/002; 0194; 0196 |
| 4. Performance targets/regression gates | EXP-003/004/007; 0194; 0196 |
| 5. Reproduction manifest | WP-035; EXP-002; 0196 |
| 6. Compiler-free wheels | WP-038; EXP-008; WP-039 |
| 7. Controller providers | EXP-007/008; 0196 |
| 8. Docs/docs.rs/notebooks | WP-037/038; WP-039 S4 |
| 9. Quality/security gates | every cycle; comprehensive S2 0196 |
| 10. Docstring thresholds | every S1/S2/S4; 0196 |
| 11. Complete audit/state trail | all S2/S4; 0196 |
| 12. Phase 7 campaign complete | 0153–0194; 0196–0198 |

## 8. Completeness invariants for this directory

The Session Plan is structurally complete only if all remain true:

1. Exactly 39 WPs exist, each with exactly one ordered S1/S2/S3/S4 brief.
2. Exactly eight campaign experiments exist, each with E1/E2/E3/E4/E5.
3. Campaign E0 precedes every experiment; E6 follows every experiment.
4. Global sequence is unique and gap-free from 0001 through 0198. Amendment
   #31 (`0144A`–`0144H`), amendment #32 (`0141A`–`0141E`), amendment #33
   (`0144A`–`0144D` for WP-036A, shifting the amendment-#31 block to
   `0144E`–`0144L`), amendment #34 (`0144A1`–`0144A4`, WP-036A S1
   decomposition), amendment #35 (`0144E1`–`0144E6`, WP-036B strict-port
   S1 decomposition), and amendment #36 (WP-036D at `0144I`–`0144L` incl.
   `0144I1`–`0144I3`, shifting the WP-036C block to `0144M`–`0144P`) add
   planned sub-sessions between existing integers; the integer sequence
   0001–0198 remains unique and gap-free.
5. Every predecessor/successor link resolves; only 0001 lacks a file
   predecessor and only 0198 lacks a file successor. Sub-session chains link
   internally: `0141` → `0141A` → … → `0141E` → `0142`, and
   `0144A` → `0144A1` → … → `0144A4` → `0144B` → … → `0144E` →
   `0144E1` → … → `0144E6` → `0144F` → `0144G` → `0144H` → `0144I` →
   `0144I1` → `0144I2` → `0144I3` → `0144J` → `0144K` → `0144L` →
   `0144M` → … → `0144P` → `0145`.
6. Every Project Plan F/N requirement, roadmap phase, risk, parity hazard, and
   Definition-of-Done item has at least one implementation owner and one
   independent confirmation point.
7. Conditional correction templates exist and cannot authorize resumption
   before their S4 closes.

Violating any invariant is at least a D2 governance finding.
