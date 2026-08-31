# Session 0144U — WP-036F S1: Coding — DirectML controller-graph execution

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036F
**Session type:** S1 — Coding
**Predecessor:** [0144T — Documentation (WP-036E S4)](0144T-wp036e-s4-gpu-device-resident-execution-path.md)
**Successor:** [0144V — Audit](0144V-wp036f-s2-directml-controller-graph-execution.md)
**Authority:** Project Plan §6/§8 and amendments #13/#38, and [`WP-036E-036F-036G-execution-plan-and-decomposition.md`](WP-036E-036F-036G-execution-plan-and-decomposition.md). If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

> **New work package (Plan amendment #38).**
> `EVIDENCE/0109-wp028-s1-controller-provider-report.json` (WP-028 S1)
> established that `DmlExecutionProvider` cannot execute the subconscious
> controller graph: DirectML fuses `Gemm`+`Relu` into a `DmlFusedGemm` node
> that rejects the two-input `Gemm` form PyTorch exported
> (`InvalidGraph: ... input size 2 not in range [min=3, max=3]`). The archived
> PRINet 3.0 reference fails identically — a runtime/graph condition, not a
> PRIN defect (matches amendment #13's WP-005 finding). DV-006 records the fix:
> "re-exporting the controller graph with three-input `Gemm` nodes so
> DirectML's fusion accepts it (a WP-030 export-side change)." WP-036F
> executes that fix and closes the DirectML half of DV-006.

## Mission

Re-export the subconscious controller ONNX graph so every `Gemm` node carries
an explicit third (bias) input, making it acceptable to DirectML's
`DmlFusedGemm` fusion, **without changing the mathematical function of the
graph**; validate that `DmlExecutionProvider` executes the re-exported graph
on the project host and that its outputs agree bit-for-bit (within Testing
Standards §3 tolerance) with `CPUExecutionProvider` and the PRINet 3.0
references across the differential case set; record DirectML provider latency
alongside CPU.

## Contract

- **Acceptance:**
  - The re-exported controller graph is **mathematically identical** to the
    current one: a differential test over the existing 48-case set on
    `CPUExecutionProvider` is bit-identical (within registered tolerance)
    before any DirectML claim.
  - `DmlExecutionProvider` executes the re-exported graph on the project host
    (registered providers: `DmlExecutionProvider`, `CPUExecutionProvider`)
    and its outputs agree with CPU within Testing Standards §3 tolerance
    across the differential case set;
    `tests/test_daemon_controller.py::TestCrossProviderAgreement` widens
    automatically to include DirectML.
  - DirectML vs CPU provider latency for the controller graph is measured and
    recorded on the project host (the DV-006 re-audit gate names "provider
    and latency acceptance").
  - The committed controller graph artefact and its checksum are regenerated;
    any 3.0-reference comparison fixture is updated consistently.
  - `≥95%` coverage on new/changed first-party code; numerical authority
    unaffected (the graph is a controller inference artefact, not PRIN
    numerics); no `prin.__all__` / `FROZEN_PUBLIC_API` change.
- **Non-goals:** VitisAI / Ryzen AI NPU execution (hardware-blocked — the
  project host is a Ryzen 7 8700F with no XDNA NPU and no CPython-3.14-matched
  VitisAI wheel; stays OPEN in DV-006); `retrain_controller` /
  `export_to_onnx` / `quantize_onnx` (DV-025 — WP-036C scope); any change to
  the controller *algorithm*, the daemon runtime, or backend-selection logic;
  release publishing.

## Required reading

- `DOCS/PRIN_Project_Plan.md` §3.1 F5, §7 R4, and amendments #13/#38
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §3/§7
- `DOCS/standards/Testing_Standards.md` §1, §3
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-006 (and DV-025 for the
  boundary)
- `DOCS/audits/028-wp028-audit.md` A1; `DOCS/experiments/0109-wp028-s1-handoff.md`;
  `EVIDENCE/0109-wp028-s1-controller-provider-report.json`
- `DOCS/reports/036e-project-state.md` and the cumulative deviation ledger
- The controller ONNX export path (verify the exact owning module at S1
  start: `crates/prin-daemon/` and/or the `SubconsciousController` export used
  by WP-028); `tests/test_daemon_controller.py`
- [`WP-036E-036F-036G-execution-plan-and-decomposition.md`](WP-036E-036F-036G-execution-plan-and-decomposition.md) §3 (WP-036F), §7 (risk R3)

## Entry conditions

- WP-036E S4 (`0144T`) is closed and committed.
- No unresolved D1/D2 finding exists.
- WP-036F scope, acceptance criteria, and non-goals have maintainer approval
  (Plan amendment #38; PSR-036E §6 hand-off).
- The project host's ONNX Runtime `DmlExecutionProvider` is available; its
  state is confirmed at S1 start and recorded.

## Expected work

1. Establish the failing/characterization test first: reproduce the
   `InvalidGraph` DirectML load failure on the current graph, and a passing
   CPU-provider differential baseline.
2. In the controller export path, emit three-input `Gemm` nodes (explicit
   zero/constant bias where the current export omits it) — or an equivalent
   `onnx` graph-transform pass over the exported model — so `DmlFusedGemm`
   fusion is satisfied. No change to the graph's function.
3. Regenerate the committed graph artefact + checksum; update reference
   fixtures.
4. Extend `TestCrossProviderAgreement` so DirectML is exercised and compared
   bit-for-bit (within tolerance) against CPU and the 3.0 references.
5. Add a provider-latency measurement (DirectML vs CPU) for the controller
   graph; record environment.
6. Tests in tandem; deterministic `Seed` preserved; record out-of-scope
   discoveries.

## Required evidence and outputs

- Code, regenerated artefact, and tests in one S1 commit range;
  `≥95%` coverage on changed first-party code.
- CPU-provider differential bit-identity evidence for the re-exported graph
  (pre-DirectML); DirectML execution + agreement evidence; latency table.
- `ruff` / `ruff format --check` / `mypy --strict` / `interrogate` /
  `bandit` / `pytest` / `cargo fmt` / clippy / `cargo test` / `cargo audit` /
  `pip-audit`; Snyk Code on modified supported source.
- `DOCS/experiments/0144U-wp036f-s1-handoff.md` mapping each acceptance
  criterion to evidence and recording provider state.

## Prohibited

- Any change to the controller's mathematical function; NPU/VitisAI work;
  DV-025 symbols; weakened assertions/tolerances; undocumented public API;
  hidden RNG; unapproved `unsafe`; scope creep into the daemon runtime or
  backend selection; unregistered experimentation.

## Exit gate

All S1 gates green; the re-exported graph is bit-identical to the current one
on CPU; `DmlExecutionProvider` executes it and agrees within tolerance;
latency recorded; every acceptance criterion is evidence-mapped. Hand off to
the mandatory S2 audit `0144V`.
