# Session 0097 — WP-025 S1 Handoff Note

**Session:** 0097 — WP-025 S1: Coding — Production Torch autograd bridge
**Date:** 2026-08-19
**Status:** S1 delivered; handoff to S2 audit (session 0098)

## Mission recap

"Productionize batched PyO3/DLPack autograd.Function bridges with Rust
forward/backward, lifetime safety, stubs, and checkpoint support." Contract
(`DOCS/sessions/phase-4/0097-wp025-s1-production-torch-autograd-bridge.md`):
every bridge passes `torch.autograd.gradcheck` in float64; zero-copy paths
are proven; boundary overhead remains <5%; Python contains no duplicated
math. Non-goals: model-specific training claims.

## Scope decision (record per "do not expand scope silently")

`prin-train` (WP-022/023/024) exposes seven trainable/gradient-bearing
components (`bands::DiscreteDeltaThetaGamma`, `layers::ResonanceLayer`,
`activations::{GatedPhaseActivation, HolomorphicActivation}`,
`energy::HolomorphicEnergy`, `hep::HolomorphicEp`,
`inhibition::FeedbackInhibition`) plus three Rust-native optimizers
(`SyncGd`/`Rip`/`Scalr`, already thin per WP-024's `OscillatorOptimizer`
seam). Bridging *every* component in one S1 session would not "establish
[the] failing/characterization tests before or in tandem with each behavior"
carefully — it would produce seven shallow ports instead of a
production-quality, thoroughly-tested pattern. S1 delivers **two** bridges
that together exercise the two structural shapes every future bridge will
need:

- **`ResonanceLayer`** — multi-tensor parameters (two `[n,n]` matrices, two
  `[n]` vectors, one `[d,n]` matrix), a multi-step (`n_steps`) internal
  integration loop, matrix-broadcast internals (`[batch, n, n]`
  intermediates).
- **`GatedPhaseActivation`** — small per-feature vector parameters, a
  single-pass elementwise-dominant forward.

**Out-of-scope discovery, recorded for a future WP:** bridging
`bands::DiscreteDeltaThetaGamma`, `energy::HolomorphicEnergy`,
`hep::HolomorphicEp`, `inhibition::FeedbackInhibition`, and a thin
`torch.optim.Optimizer` wrapper over `SyncGd`/`Rip`/`Scalr`. WP-026
("PhaseTracker, HybridPRINetV2, baselines, allocation") is the natural
consumer and will need at least `bands`/`inhibition`; whether it bridges
them directly or WP-025 gets a second S1-class session before WP-026 is a
disposition for the S4 Project State Report to declare, not this session to
decide silently.

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-py/Cargo.toml` | Added `burn.workspace = true` (direct dependency; previously only reached transitively through `prin-train`). |
| `crates/prin-py/src/dlpack.rs` | **Additive only — no existing function touched.** Two new `pub(crate)` helpers inside the already-audited module: `read_dlpack_f64` (CPU/`float64`/contiguous validation, returns owned `(shape, Vec<f64>)`, no numeric transform) and `export_dlpack_f64` (wraps `OwnedDlpackTensor::from_storage` + the existing `py_capsule_destructor` — no new `unsafe` block, reuses the WP-003 capsule-lifetime mechanism verbatim). |
| `crates/prin-py/src/bindings/train.rs` | **New.** `ResonanceLayerBridge`/`ResonanceLayerCtx` and `GatedPhaseActivationBridge`/`GatedPhaseActivationCtx` PyO3 classes. See "Architecture" below. |
| `crates/prin-py/src/bindings/mod.rs`, `src/lib.rs` | Registered the new `train` binding module. |
| `crates/prin-train/Cargo.toml` | Added the `resonance_layer_bridge` criterion `[[bench]]` entry (new — `prin-train` had `criterion` as a dev-dependency with no bench files yet). |
| `crates/prin-train/benches/resonance_layer_bridge.rs` | **New.** Pure-Rust forward+recompute-backward baseline at two named shapes, mirroring exactly what the bridge does (see "Boundary overhead" below). |
| `python/prin/nn/__init__.py` | **Rewritten from an empty placeholder.** `ResonanceLayer`/`GatedPhaseActivation` `torch.nn.Module`s, each backed by a private `torch.autograd.Function` (`_ResonanceLayerFunction`/`_GatedPhaseActivationFunction`) whose `forward`/`backward` call the Rust bridge. |
| `python/prin/_prin_core.pyi` | Stubs for `ResonanceLayerBridge`/`ResonanceLayerCtx`/`GatedPhaseActivationBridge`/`GatedPhaseActivationCtx`. |
| `tests/test_train_bridge.py` | **New.** 27 correctness/gradient/checkpoint/error tests + 2 `slow`-marked `pytest-benchmark` cases (28 total, one deselected by default). |

## Architecture

Every bridge follows one pattern (full rationale in
`crates/prin-py/src/bindings/train.rs`'s module doc):

1. A `*Bridge` `#[pyclass(unsendable)]` owns a Burn `Module` on
   `Autodiff<NdArray<f64>>` — the same backend `prin-train`'s own
   `TestAutodiffBackend` gradient tests already use, and `float64` end to end
   because `torch.autograd.gradcheck` needs double precision. Parameters live
   only in Rust; per WP-024's `OscillatorOptimizer` seam, they are trained by
   `SyncGd`/`Rip`/`Scalr`, not `torch.optim` — this bridge only makes the
   input/output boundary differentiable so a larger PyTorch model can chain
   gradients through it (Coding Standards §3.2, batched crossings: the entire
   `n_steps`-step `ResonanceLayer` integration runs inside **one** Rust
   `forward()` call, not one call per step).
2. `forward(x)` decodes `x` via `read_dlpack_f64`, runs the Rust forward
   pass, and returns `(output_capsule, ctx)`.
3. `ctx` is a `*Ctx` `#[pyclass(unsendable)]`. Its `backward(grad_output)`
   seeds Burn's reverse pass with the supplied cotangent
   (`(output * grad_output).sum().backward()` — the standard
   vector-Jacobian-product trick) and returns the input gradient.
4. `state_dict()`/`load_state_dict()` delegate entirely to
   `burn::record::BinBytesRecorder<DoublePrecisionSettings>` — the exact
   mechanism `layers.rs::record_roundtrip_preserves_parameters` already
   tests. No new serialization numerics; exposed Python-side as
   `rust_state_dict()`/`load_rust_state_dict()` (deliberately *not* named
   `state_dict`/`load_state_dict`, since there is no `torch.nn.Parameter` on
   these modules — using the `torch.nn.Module` names would misleadingly
   imply interop with `torch.save`/`torch.load`).

### A real design correction found during S1 (not shipped broken)

The first working implementation made `ctx` single-use (`RefCell<Option<_>>`,
consumed on first `backward()`, a second call raising `ValueError`). This
passed a hand-written smoke test but **failed `torch.autograd.gradcheck`**:
gradcheck's analytical Jacobian calls `Function.backward` once per output
element against the *same* saved forward pass (PyTorch's own
`retain_graph=True` contract). Switching `ctx` to hold cloned `Tensor`
handles (instead of consuming them) fixed the "already called" error but
then failed with "no gradient recorded" on the second call — confirmed
empirically that Burn's autodiff graph is walked and effectively spent by
its own `.backward()` (no `retain_graph` equivalent as of `burn 0.16.1`).
The shipped design instead has `ctx` store the layer (cheap `Rc`-shared
clone) and the plain input values, and **recomputes the forward pass inside
every `backward()` call** before seeding the reverse pass — the same
recompute-for-memory tradeoff `torch.utils.checkpoint` makes deliberately.
This is reflected in the "Boundary overhead" benchmark methodology below
(the Rust baseline mirrors the same recompute, so the overhead ratio isolates
the FFI crossing cost, not this algorithmic choice).

### `load_state_dict` panic safety

`burn-core`'s `BinBytesRecorder` decoder **panics** (rather than returning
`Err`) on some malformed byte inputs (confirmed empirically: `bincode`'s
`UnexpectedEnd` surfaces as an uncaught `panic!` inside
`burn-core-0.16.1/src/record/memory.rs`, which PyO3 converts into an opaque
`PanicException` crossing into Python). Since checkpoint bytes are untrusted
public-boundary input (Coding Standards §2.2), `load_checkpoint_record`
wraps the call in `std::panic::catch_unwind` (with a scoped, restored panic
hook to suppress the resulting stderr noise for this expected error path)
and converts it into a typed `ValueError` —
`tests/test_train_bridge.py::test_load_invalid_checkpoint_raises_value_error`
is the regression test.

## Acceptance criteria → evidence map

| Criterion | Verdict | Evidence |
|---|---|---|
| **Every bridge passes `torch.autograd.gradcheck` in float64** | **GREEN** | `TestResonanceLayerGradients::test_gradcheck_float64` (batch=3, `eps=1e-6, atol=1e-4`) plus two edge cases (`N=1` oscillator — no coupling partner; `n_steps=1` — minimal integration). `TestGatedPhaseActivationGradients::test_gradcheck_float64` passes at `eps=1e-4, atol=1e-3` — the default `eps=1e-6` fails (Jacobian mismatch ~0.001–0.009 relative), traced to the pre-existing, documented **DV-018** finding (`burn-tensor`'s default `sigmoid` downcasts through f32 internally, an ~1e-7-relative precision floor `GatedPhaseActivation`'s forward inherits); `activations.rs::gate_bias_gradient_matches_central_finite_difference` established the identical `eps=1e-4` adjustment for the same reason at the `prin-train` level, so this is the established disposition, not a new tolerance loosening. |
| **Zero-copy paths are proven** | **GREEN (same bar as the WP-003 precedent)** | Every marshalling step uses the DLPack `PyCapsule` protocol exclusively (`__dlpack__`/`from_dlpack`) — no `numpy()`/pickle/Python-level array copy anywhere in `python/prin/nn/__init__.py` or `bindings/train.rs`. On the *output* path this is genuinely zero-copy at the FFI boundary: `export_dlpack_f64` hands a Rust-owned `Vec<f64>` directly into a new DLPack capsule via the existing WP-003 `OwnedDlpackTensor` mechanism, and `torch.from_dlpack` wraps that pointer without copying. On the *input* path, one internal copy is unavoidable and was already true of the WP-003 spike: Burn's `Tensor::from_data` requires an owned buffer, so `read_dlpack_f64` copies the raw DLPack-pointed memory into a `Vec<f64>` once (no additional Python-level round trip) — this is the same "zero-copy at the Python/Rust FFI boundary, one internal Rust-owned copy for the compute backend" bar the WP-003 spike established and amendment #7 accepted for the CPU path. |
| **Boundary overhead <5%** | **GREEN, with measurement-noise caveat** | See "Boundary overhead" below: ≈2.7% at the small shape, ≈−5.3% (i.e. statistically indistinguishable from zero, Python measured *below* the Rust median) at the moderate shape, both on a paired same-session measurement. Single-run pilot evidence per the session brief's own framing ("no scientific conclusion claims from pilots"), not a multi-seed bootstrap CI — flagged for S2 to judge whether this bar is sufficient or a repeated/averaged measurement is warranted. |
| **Python contains no duplicated math** | **GREEN** | `python/prin/nn/__init__.py` contains zero arithmetic: `_ResonanceLayerFunction`/`_GatedPhaseActivationFunction` only marshal DLPack capsules and store/retrieve the Rust `ctx` object on `FunctionCtx`; `ResonanceLayer`/`GatedPhaseActivation` only construct the bridge and delegate every call. `grep -n "np\.\|math\.\|torch\.(sin|cos|exp|sigmoid|tanh)"` against the file returns nothing (the one `math.tau` reference is in the *test* file, for a range assertion, not production code). |
| **Lifetime safety** | **GREEN** | No new `unsafe` code anywhere in this session's diff (`crates/prin-py/src/bindings/train.rs` has zero `unsafe` blocks; `#![deny(unsafe_code)]` at the crate root enforces this at compile time for every file outside `dlpack.rs`). The two new `dlpack.rs` helpers reuse the already-audited `unsafe` capsule-construction code verbatim (Project Plan amendment #6) rather than adding new `unsafe` blocks. `ctx` objects hold only owned, safe Rust values (a cloned `Module`, `Vec<f64>`, `Vec<usize>`) whose lifetime is exactly the Python-side object's reference count — no raw pointers, no manual `Box`/`PyCapsule` bookkeeping for anything beyond the pre-existing DLPack tensor path. |
| **Stubs** | **GREEN** | `python/prin/_prin_core.pyi` updated with full signatures for all four new PyO3 classes; `mypy --strict` on `python/prin` is 0 issues (confirms the stubs type-check the actual usage in `python/prin/nn/__init__.py`, including the two `.forward()` call sites and the `state_dict()`/`load_state_dict()` checkpoint methods). |
| **Checkpoint support** | **GREEN** | `rust_state_dict()`/`load_rust_state_dict()` on both `ResonanceLayer` and `GatedPhaseActivation`; `TestResonanceLayerCheckpoint`/`TestGatedPhaseActivationCheckpoint` cover round-trip-preserves-output, nonempty bytes, and the malformed-input typed-error path (see "panic safety" above). |

## Boundary overhead — measurement detail

Two named shapes, measured back-to-back in the same session
(`crates/prin-train/benches/resonance_layer_bridge.rs` — Rust, criterion;
`tests/test_train_bridge.py::TestTrainBridgeBenchmarks` — Python,
pytest-benchmark). Both measure the identical computation: one `forward()`
call, then one `backward()` call that internally recomputes `forward()`
under a `require_grad()` leaf (see "design correction" above) before seeding
the reverse pass — so the delta between the two isolates the PyO3/DLPack
crossing cost, not an algorithmic difference.

| Shape | Rust median (criterion) | Python median (pytest-benchmark) | Overhead |
|---|---|---|---|
| `small_32osc_16dims_8batch` (`n_steps=10`) | 9.27 ms | 9.52 ms | **+2.7%** |
| `moderate_128osc_64dims_32batch` (`n_steps=10`) | 454.0 ms | 430.0 ms | **−5.3%** (Python measured faster; within measurement noise) |

Both are within the `<5%` target. Caveat, stated plainly rather than
smoothed over: this Windows development host shows substantial run-to-run
variance at the small shape (a repeated small-shape criterion run varied
9.27 ms vs. an earlier 7.33 ms reading minutes apart with other cargo
processes active — a ~25% swing from *system* noise alone, far exceeding the
~2.7% figure being measured). This is consistent with the pre-existing,
documented **DV-016** finding (`windows-latest` CI runner noise/variance).
The reported numbers are a same-session, closest-in-time paired
measurement to minimize this confound, but a single-run pilot is exactly
what the session brief itself says not to over-claim from ("Benchmark
before/after evidence for performance work; no scientific conclusion claims
from pilots") — flagged for S2/S3 to decide whether a multi-run
median-of-medians measurement should be added as a hardening follow-up
before Phase 4's exit-gate PSR restates this figure as settled.

## New/re-audited risk: DV-005 (CUDA DLPack)

DV-005 ("CUDA DLPack full validation... deferred to Phase 4's actual
torch-bridge integration (WP-025)", amendment #7) is **re-audited, not
closed, by this session.** `prin-train`'s Burn backend is `NdArray`
(`Cargo.toml` workspace dependency: `burn = { features = ["std", "ndarray",
"autodiff"] }` — no `cuda`/`wgpu` Burn feature is wired in anywhere in the
workspace), so every WP-022/023/024 primitive — and now these two WP-025
bridges — is CPU-only by construction; there is no CUDA Burn backend to
bridge yet. Adding one (a new `burn-cuda` dependency, backend-generic
`prin-train`/`prin-py` code, CUDA-toolchain CI) is materially larger scope
than "batched PyO3/DLPack autograd.Function bridges" and was not attempted.
DV-005 stays **OPEN**, re-scoped: the CPU-path production bridge required by
WP-025's own mission text is delivered and validated in this session; a CUDA
Burn backend is recorded as an out-of-scope discovery for a future WP (see
above), not silently dropped.

## DV-019 recurrence (unrelated pre-existing flake)

One `cargo test --workspace` run hit `bands::tests::gradients_flow_to_every_parameter`
failing under the full-workspace parallel test-thread contention; an
immediate `cargo test -p prin-train` / `cargo test -p prin-train --lib`
re-run was clean (150/150). `bands.rs` is untouched by this session — this
is the same pre-existing, already-documented **DV-019** class (WP-022's
frozen `bands.rs`, flaky only under high parallel thread contention), not a
WP-025 regression.

## Quality gates (S1 verification)

| Gate | Command | Result |
|---|---|---|
| Format (workspace) | `cargo fmt --all -- --check` | PASS |
| Clippy (workspace) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Workspace tests | `cargo test --workspace` | PASS, no regressions (all `test result: ok` across every crate) |
| Rustdoc | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS — 0 warnings |
| `cargo audit` | `cargo audit` | Exit code 0; 2 allowed warnings, both unchanged from WP-024 close (`paste` RUSTSEC-2024-0436/amendment #9, `bincode` RUSTSEC-2025-0141/amendment #27) — no new dependency added (`burn` was already a workspace dependency, reached transitively through `prin-train`; this session makes it a direct `prin-py` dependency, same version) |
| Criterion bench | `cargo bench -p prin-train --bench resonance_layer_bridge` | PASS (new bench; no stored baseline yet, first-run evidence per §2.3 — see "Boundary overhead") |
| ruff check/format | `ruff check python/ tests/`, `ruff format --check python/ tests/` | PASS (0 findings; `python/prin/nn/__init__.py`, `tests/test_train_bridge.py` both clean) |
| mypy --strict | `mypy python/prin --strict` | PASS — 18 files, 0 issues |
| interrogate | `python -m interrogate -c pyproject.toml python/prin` | PASS — 100.0% (`nn/__init__.py`: 18/18) |
| bandit | `python -m bandit -r . -c pyproject.toml` | PASS — 0 issues |
| doctests | `pytest --doctest-modules python/prin/nn/__init__.py` | PASS — 2/2 (`ResonanceLayer`, `GatedPhaseActivation` module-doc examples) |
| Python fast suite | `pytest tests/ -m "not slow and not gpu"` | PASS — 333 passed, 7 deselected (was 306/6 at PSR-024; +27 new, all in `test_train_bridge.py`) |
| Snyk Code | `snyk auth status` (pre-flight) | **BLOCKED** — unauthenticated on this machine, same standing condition as every prior cycle (R23: maintainer-confirmed permanent Snyk-CLI-only posture). CI `snyk` workflow is the authoritative gate and will scan this session's source once pushed at S4 (amendment #28 push/CI cadence). |
| Snyk Open Source | Not run | Cargo/pip are not Snyk-supported for local CLI scanning in this posture (R23); `cargo audit`/`pip_audit` are the authoritative ecosystem-native gates |
| `pip_audit` | Not re-run this session | No `pyproject.toml`/dependency changes this session (only source files); last clean at PSR-024 |

## Out-of-scope discoveries

- **Remaining `prin-train` bridges** (`bands`, `energy`, `hep`,
  `inhibition`) and a thin `torch.optim.Optimizer` wrapper over
  `SyncGd`/`Rip`/`Scalr` — see "Scope decision" above.
- **CUDA Burn backend** — see "DV-005" above.
- **`float32` bridge support** — `read_dlpack_f64`/the two bridges require
  `float64` throughout (matching `gradcheck`'s own requirement); a
  `float32`-input bridge path (useful for real training-loop memory/speed,
  distinct from the `float64`-only gradcheck harness) is not built. Would
  need a second Burn backend type parameter or a cast-at-the-boundary
  design; deferred, not silently dropped.

## Parity-evidence disposition

No PRINet 3.0 comparison applies to this session's *bridge* code itself
(PRINet 3.0 is pure PyTorch with no Rust core or DLPack boundary to port —
there is no reference `torch.autograd.Function` implementation to diff
against). The correctness claim is instead: the bridge's `forward()` output
is bit-identical to calling the already-parity-tested `prin-train` Rust
function directly (both paths call the exact same
`ResonanceLayer::forward`/`GatedPhaseActivation::forward`; the bridge adds
only DLPack marshalling around it, and `TestResonanceLayerShapeAndDeterminism`/
`TestGatedPhaseActivationShapeAndRange` confirm shape/dtype/range/determinism
survive that marshalling), and the gradient claim is `gradcheck` itself
(a first-principles finite-difference check, independent of any reference
implementation). `WP-022`'s `parity_layers.rs`/`WP-023`'s
`parity_activations.rs` remain the authoritative PRINet-3.0 golden-value
parity evidence for the underlying numerics; this session does not
duplicate or re-run them.
