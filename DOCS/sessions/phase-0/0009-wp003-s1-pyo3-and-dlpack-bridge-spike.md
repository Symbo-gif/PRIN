# Session 0009 — WP-003 S1: Coding — PyO3 and DLPack bridge spike

**Status:** COMPLETE  
**Roadmap phase:** 0 — Foundation  
**Execution unit:** WP-003  
**Session type:** S1 — Coding  
**Predecessor:** [0008 — Documentation](0008-wp002-s4-golden-corpus-and-differential-harness.md)  
**Successor:** [0010 — Audit](0010-wp003-s2-pyo3-and-dlpack-bridge-spike.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Prototype zero-copy Torch↔Rust DLPack exchange, batched boundary calls, ownership/lifetime handling, dtype/device validation, and microbenchmark instrumentation.

## Contract

- **Acceptance:** CPU and available CUDA round trips are correct; ownership and error paths are tested; measured boundary overhead supports <5% training-step target or a documented go/no-go amendment.
- **Non-goals:** Production trainable layers or per-step Python crossings.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- Coding, Testing, Documentation, Benchmarking/Reproducibility, and Security provisions relevant to this scope

## Entry conditions

- The preceding S4 (or campaign synthesis for WP-039) is closed and committed.
- WP-003 scope, acceptance criteria, and non-goals have maintainer approval.
- No unresolved D1/D2 finding exists; any carried D4 is explicitly in this scope.

## Expected work

1. Establish failing/characterization tests before or in tandem with each behavior.
2. Implement only the declared scope; keep numerical authority in Rust and backend dispatch in `prin-kernels` where applicable.
3. Add unit, property, parity, gradient, kernel-equivalence, integration, security, and performance tests as the touched behavior requires.
4. Validate public inputs, use typed errors, document all public API, preserve deterministic Seed flow, and capture benchmark environments.
5. Record out-of-scope discoveries for a later WP; do not expand scope silently.

## Required evidence and outputs

- Code and tests in the same S1 commit range; ≥95% coverage on new/changed code.
- Relevant golden cases and invariants green at registered tolerances.
- `cargo fmt`, clippy `-D warnings`, Rust tests/rustdoc; ruff, mypy strict,
  interrogate, bandit, pytest, dependency audits as applicable.
- Benchmark before/after evidence for performance work; no scientific conclusion claims from pilots.
- An S1 handoff note mapping each acceptance criterion to evidence.

## Prohibited

- Deferred tests, weakened assertions/tolerances, undocumented public API, duplicated Python numerics, hidden RNG, unapproved `unsafe`, scope creep, or unregistered experimentation.

## Exit gate

All S1 gates are green and every acceptance criterion is evidence-mapped. Hand
off to the mandatory S2 audit; S1 may not self-certify completion.

## S1 handoff

### Acceptance-criterion → evidence mapping

| # | Criterion | Evidence | Command / result |
|---|-----------|----------|------------------|
| 1 | CPU round trips are correct | `dlpack_negate` and `dlpack_round_trip` produce `torch.Tensor` values equal to the expected negation / copy for `float32` and `float64`, 1-D and 2-D. | `pytest tests/test_dlpack_bridge.py -v` — 17 passed. |
| 2 | Batched boundary calls work | `dlpack_negate_batched` accepts a list of tensors and returns a list of new capsules; `prin.dlpack.negate_batched` wraps this as a list of `torch.Tensor`. | `TestDlpackNegate::test_negate_batched` (both dtypes). |
| 3 | Ownership and error paths are tested | Owned `DLManagedTensor` carries a DLPack `deleter` and a PyCapsule destructor; the capsule is freed exactly once whether consumed by `torch.from_dlpack` or GC'd. Error paths cover non-contiguous tensors, unsupported dtypes, and non-DLPack objects. | Rust unit `dlpack::tests::owned_dlpack_tensor_can_be_built_and_dropped`; Python `test_non_contiguous_rejected`, `test_integer_dtype_rejected`, `test_rejects_versioned_or_bad_capsule`. |
| 4 | dtype/device validation | The bridge validates CPU device (`device_type == kDLCPU`), `float32`/`float64` dtype, `lanes == 1`, C-contiguous strides, and `byte_offset == 0`. | `tests/test_dlpack_bridge.py`. |
| 5 | Measured boundary overhead | `pytest-benchmark` fixtures in `TestDlpackBenchmarks` report round-trip and batched latency. | See benchmark results below. |
| 6 | Rust owns the numerics | The actual element-wise negate is `prin_kernels::ops::negate_f32` / `negate_f64`. `python/prin/dlpack.py` contains only capsule conversion and no math. | `crates/prin-kernels/src/ops.rs` and `crates/prin-py/src/dlpack.rs`. |
| 7 | Quality gates green | `cargo fmt`, `cargo clippy -D warnings`, `cargo test --workspace`, `mypy`, `ruff`, `interrogate`, `bandit`, `pip-audit`, `cargo audit`, `cargo doc -D warnings`, and `sphinx -W` all pass. | See verification table. |

### Verification table

| Gate | Result |
|------|--------|
| `cargo fmt --all -- --check` | OK |
| `cargo clippy --workspace --all-targets -- -D warnings` | OK |
| `cargo test --workspace` | 6 Rust tests passed (3 `prin-kernels` + 3 `prin-py` dlpack unit) |
| `$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps` | OK |
| `cargo audit` | 0 findings |
| `.venv\Scripts\mypy python/prin --strict` | OK (14 files) |
| `.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/` | OK |
| `.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/` | OK |
| `.venv\Scripts\python -m interrogate -c pyproject.toml python/prin` | 100% |
| `.venv\Scripts\python -m bandit -r . -c pyproject.toml` | 0 findings |
| `.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin.parity --cov-report=term-missing` | 111 passed |
| `.venv\Scripts\python -m pytest tests/ parity/ --cov=prin.parity --cov-report=term-missing` | 123 passed |
| `.venv\Scripts\python -m pytest tests/test_dlpack_bridge.py -m "not slow and not gpu" --cov=prin.dlpack` | `prin.dlpack` 100% covered |
| `.venv\Scripts\python -m pip_audit .` | 0 findings |
| `.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt` | 0 findings |
| `.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html` | OK |
| Snyk Code (`severity_threshold=medium`) | 0 findings |
| Snyk Open Source (`severity_threshold=low`, `all_projects=true`) | 0 findings |

### Microbenchmark results (pytest-benchmark)

- `test_negate_round_trip_latency[float64]`: mean ~108.7 µs for 16 384 elements (≈ 6.6 GB/s).
- `test_negate_round_trip_latency[float32]`: mean ~115.4 µs for 16 384 elements.
- `test_negate_batched_latency[float64]`: mean ~247.7 µs for 8 × 4096 elements.
- `test_negate_batched_latency[float32]`: mean ~255.7 µs for 8 × 4096 elements.

These numbers measure the full `torch.Tensor → PyCapsule → Rust → PyCapsule → torch.Tensor` path for a trivial kernel. The overhead is dominated by the two Python crossings and the DLPack capsule construction; the actual data copy inside the Rust `negate` kernel is a single contiguous pass. No training-step fraction claim is made from this pilot.

### CUDA status

The environment under test uses a CPU-only `torch` build (`2.13.0+cpu`). CUDA device tensors are detected and rejected at the bridge (non-CPU device error). A CUDA round trip is a Phase 0 spike go/no-go item; a documented go/no-go amendment is in order if CUDA hardware is unavailable before WP-003 closes.

### Files introduced or modified

- `crates/prin-kernels/src/ops.rs` (new): `negate_f32` / `negate_f64` representative kernel.
- `crates/prin-kernels/src/lib.rs`: expose `ops` module.
- `crates/prin-py/src/dlpack.rs` (new): audited PyO3/DLPack bridge (`dlpack_negate`, `dlpack_negate_batched`, `dlpack_round_trip`).
- `crates/prin-py/src/lib.rs`: register DLPack functions.
- `crates/prin-py/Cargo.toml`: add `dlpack` workspace dependency.
- `Cargo.toml`: add `dlpack = "0.2.0"` to workspace dependencies.
- `python/prin/dlpack.py` (new): thin wrapper returning `torch.Tensor`.
- `python/prin/_prin_core.pyi`: stubs for the new PyO3 functions.
- `tests/test_dlpack_bridge.py` (new): integration, error-path, and benchmark tests.

### D4 item for S2 audit

`crates/prin-py/src/dlpack.rs` contains audited `unsafe` for the Python C API and DLPack C ABI. The Coding Standards state that `prin-kernels` is the crate permitted to contain audited `unsafe`. Two defensible positions exist:

1. **Accept `prin-py` as the Python-FFI boundary.** The `unsafe` is isolated to a single module with `#![allow(unsafe_code)]`, `#![deny(unsafe_op_in_unsafe_fn)]`, and `// SAFETY:` comments on every `unsafe` block. The rest of `prin-py` remains `unsafe`-free (`#![deny(unsafe_code)]`).
2. **Relocate the `unsafe` to `prin-kernels`.** This would require adding a `pyo3` dependency to `prin-kernels` (also a layer deviation) so that the capsule construction can live in the kernel crate.

The current implementation chooses option 1 because the DLPack exchange is inherently a Python-FFI concern and the `prin-py` crate is already the workspace's Python-linking extension crate. S2 should either approve this deviation, move the `unsafe`, or amend the standard to explicitly permit a scoped `prin-py` DLPack FFI module.
