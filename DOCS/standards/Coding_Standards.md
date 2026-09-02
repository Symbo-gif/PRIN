# PRIN Coding Standards

**Status:** Normative. All code merged to `main` must comply. Enforced by CI
(`rust.yml`, `python.yml`); reviewers must reject non-compliant PRs.

---

## 1. General principles

1. **One algorithm, one implementation.** Backend dispatch (CPU/CUDA/wgpu)
   happens inside `prin-kernels`; math is never duplicated at call sites.
2. **The Python layer contains no numerics.** All computation lives in Rust.
3. **Explicit state, no hidden globals.** Deterministic seeding is threaded
   through every stochastic entry point via the single `Seed` type.
4. **Fail loudly, early, and typed.** Validate inputs at public API boundaries;
   raise/return precise, actionable errors.
5. **Correctness before performance; performance with evidence.** Optimizations
   require a benchmark demonstrating the win (see Benchmarking Standards).
6. **All work flows through the Session Cycle** (Development Workflow and
   Audit Standards): code and its tests are written in tandem in S1, audited
   in S2, and standards violations found by audit are D2 findings that must be
   remediated in the same cycle. Write to standard at write time — never
   "clean up later".

## 2. Rust standards

### 2.1 Toolchain and lints

- Stable toolchain pinned by `rust-toolchain.toml`; MSRV declared in the
  workspace (`rust-version`) and only raised in minor releases.
- `cargo fmt` (default style) and `cargo clippy --workspace --all-targets
  -- -D warnings` must be clean.
- Every crate carries `#![forbid(unsafe_code)]`. Exceptions:
  1. Audited kernel-FFI modules inside `prin-kernels` (Phase 3+) may use
     `unsafe` in dedicated modules with `#![deny(unsafe_op_in_unsafe_fn)]`,
     a `// SAFETY:` comment on every unsafe block, and mandatory
     second-reviewer sign-off.
  2. Audited Python-FFI modules inside `prin-py` may use `unsafe` to call the
     Python C API and DLPack C ABI under the same controls: dedicated module
     (`crates/prin-py/src/dlpack.rs`), `#![deny(unsafe_op_in_unsafe_fn)]`, a
     `// SAFETY:` comment on every unsafe block, and mandatory second-reviewer
     sign-off. Because `#![forbid(unsafe_code)]` cannot be scoped to a single
     module, `prin-py` uses crate-level `#![deny(unsafe_code)]` with a
     module-level `#![allow(unsafe_code)]` in `dlpack.rs` (Project Plan
     amendment #6).
- `#![warn(missing_docs)]` on every crate — combined with CI's
  `RUSTFLAGS="-D warnings"` this makes **100% public-item documentation a
  build requirement**. `cargo doc --no-deps` must also be clean under
  `RUSTDOCFLAGS="-D warnings"` (CI `docs` job). See Documentation Standards §2.

### 2.2 Design

- **Traits for algorithm families** (`Dynamics`, `Integrator`); **enums for
  closed sets** (coupling modes, backends) — never stringly-typed dispatch.
- Errors: `thiserror` error enums per crate; no `panic!`/`unwrap`/`expect` in
  library code paths (allowed in tests and at binary entry points). Numerical
  guard failures under `strict-checks` return typed errors.
- Numerics: f64 for reference paths and accumulations of reductions; f32
  compute allowed on performance paths with f64 accumulate where the parity
  program requires it. Document every clamp/guard with its PRINet 3.0 origin.
- Parallelism: `rayon` for data parallelism; no hand-rolled threading outside
  `prin-daemon`'s audited ring buffer. Send/Sync bounds explicit on public
  types.
- Logging/telemetry: `tracing` spans; no `println!` in library code.
- Dependencies: added to `[workspace.dependencies]` only, with justification in
  the PR description; `cargo audit` must stay clean.

### 2.3 Naming

- Crates: `prin-<domain>`. Modules: single-word nouns (`state`, `models`,
  `integrate`). Types: `UpperCamelCase`; functions/fields: `snake_case`;
  feature flags: `kebab-case` (`strict-checks`).

## 3. Python standards

### 3.1 Tooling

- Python ≥ 3.11. Formatter/linter: **ruff** (line length 88, rule set in
  `pyproject.toml` including the pydocstyle `D` rules, Google convention),
  `ruff format` for formatting.
- Docstring coverage is enforced twice: ruff `D` rules fail on undocumented
  public modules/classes/functions, and **`interrogate` must report ≥95%**
  overall coverage (`fail-under = 95` in `pyproject.toml`). Public API
  docstring coverage is 100% — no exceptions (Documentation Standards §2).
- **`mypy --strict`** on `python/prin` — zero errors. The compiled extension is
  typed via generated `_prin_core.pyi` stubs, regenerated whenever the PyO3 API
  changes and committed in the same PR.
- `from __future__ import annotations` in every module.

### 3.2 Design

- Public functions/classes: full type hints and Google-style docstrings with
  `Args`/`Returns`/`Raises`/`Examples` sections (doctest-checked where
  practical).
- No bare `except:`; no mutable default arguments; no `eval`/`exec`/runtime
  code generation (security requirement).
- Torch bridges: every Rust-backed trainable op is a `torch.autograd.Function`
  with forward **and** backward calling Rust; boundary crossings are batched
  (one call per integration, not per step).
- API compatibility: public symbols mirror PRINet 3.0. Deviations require a
  Migration Guide entry in the same PR. Deprecations use the ported
  `_deprecation` machinery — never silent removal.

### 3.3 Example (canonical docstring/validation style)

```python
def compute_binding_strength(
    phases: torch.Tensor,
    coupling_matrix: torch.Tensor,
    temperature: float = 1.0,
) -> torch.Tensor:
    """Compute the pairwise oscillator binding strength.

    Args:
        phases: Oscillator phase angles in radians. Shape: (N,).
        coupling_matrix: Symmetric adjacency matrix. Shape: (N, N).
        temperature: Softmax temperature for binding sharpness. Must be > 0.

    Returns:
        Pairwise binding strength matrix. Shape: (N, N), values in [0, 1].

    Raises:
        ValueError: If shapes are inconsistent or temperature <= 0.
    """
    if temperature <= 0:
        raise ValueError(f"temperature must be positive, got {temperature}")
    ...
```

## 4. Version control

- **Conventional Commits** (`feat:`, `fix:`, `docs:`, `test:`, `perf:`,
  `refactor:`, `chore:`); imperative mood; body explains *why*.
- Branch names: `<type>/<short-description>` (e.g. `feat/knn-phase-index`).
- `[gpu]` in a commit message triggers the self-hosted GPU CI job.
- PRs: small and focused; all CI green; ≥1 maintainer review (2 for `unsafe`,
  numerics-affecting, or release changes); no force-pushes to `main`.
- **Push/CI cadence (Plan amendment #28):** S1, S2, and S3 sessions commit
  locally only — they never push. Only the S4 commit that closes a cycle is
  pushed, carrying the full S1–S4 range for that WP in one push; that push is
  the sole point at which CI runs for the cycle. See Development Workflow and
  Audit Standards §3 ("Push and CI cadence") for the full rule and its
  hotfix exception.

## 5. Local gate (must pass before pushing)

```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps  # pwsh: $env:RUSTDOCFLAGS="-D warnings"; cargo doc --workspace --no-deps
ruff check python/ tests/ benchmarks/ tools/
ruff format --check python/ tests/ benchmarks/ tools/
mypy python/prin --strict
interrogate -c pyproject.toml python/prin
bandit -r python/prin -c pyproject.toml
pytest tests/ -v -m "not slow and not gpu"
```

## 6. Security standards

Security is a first-class gate (audit checklist A6), not a release-time
activity. The following are hard requirements at the **highest industry
threshold**:

### 6.1 Code-level

- **No runtime code generation or evaluation** anywhere in shipped code: no
  `eval`/`exec`/`compile` of dynamic strings, no runtime nvcc/MSVC JIT, no
  `pickle.load` of untrusted data (use JSON/NPZ with validation).
- **`unsafe` Rust** is forbidden (`#![forbid(unsafe_code)]`) except in
  audited kernel-FFI modules inside `prin-kernels` and audited Python-FFI
  modules inside `prin-py`: dedicated module, `#![deny(unsafe_op_in_unsafe_fn)]`,
  a `// SAFETY:` justification per block, and mandatory second-reviewer sign-off
  recorded in the PR.
- **Input validation at every public boundary** (shapes, dtypes, ranges,
  finiteness) with typed errors; validation failures must be unreachable from
  memory-unsafe paths.
- No secrets in the repository, test fixtures, notebooks, or CI logs — GitHub
  secret scanning + push protection enabled; credentials only via CI
  secrets/OIDC.
- Subprocess use: no `shell=True`; absolute executables; arguments as lists.
- File-system writes confined to declared output directories
  (`benchmarks/results/`, `DOCS/test_and_benchmark_results/`, temp dirs).

### 6.2 Toolchain gates (all must be clean; run in CI on every PR)

**No merge-gating CI job may `pip install` (or `cargo install`) an unpinned
tool** (ETCA-002 T-F10 / Plan amendment #45 G6). A gate whose toolchain floats
run-to-run is non-deterministic — green locally, red in CI on the same commit —
and cannot be trusted as a merge control. Every gating job installs from a
committed constraints/lock file (`ci/lint-constraints.txt`, `Cargo.lock`,
`DOCS/sphinx/requirements.txt`, …), kept in step with the maintainer host, and
tool versions are bumped deliberately in their own commit.

| Tool | Scope | Gate |
|---|---|---|
| `cargo audit` | Rust dependency advisories | 0 unaddressed advisories |
| `cargo clippy -D warnings` | Rust lints incl. correctness/security classes | 0 warnings |
| `ruff` `S` rules (bandit set) | Python source | 0 findings outside tests |
| `bandit -r python/prin` | Python SAST (defense in depth) | 0 medium+ findings |
| `pip-audit` | Python dependency advisories | 0 unaddressed advisories |
| Snyk Code | active first-party source in supported languages | 0 medium+ findings |
| Snyk Open Source | supported manifests and resolved Python dependency sets | 0 unaddressed advisories |
| Secret scanning / push protection | whole repo | enabled, 0 alerts |

When GitHub reports that native secret scanning is unavailable for a private
repository, an approved temporary amendment may substitute all of the following:
a blocking full-history secret scan on every push and pull request, that scan as
a required `main` protection check, PR-only changes to `main`, and a native-control
availability recheck in every cycle. Native secret scanning and push protection
must be enabled as soon as GitHub makes them available; this exception cannot be
used when the controls are merely disabled or misconfigured.

Snyk is additive defense in depth: it does not replace `cargo audit`,
`pip-audit`, or GitHub secret scanning and push protection. Where Snyk cannot
resolve a native manifest, the ecosystem-native gate remains authoritative;
a resolved dependency manifest or SBOM may provide additional Snyk coverage.
Immutable, non-shipped historical material under `DOCS/archive/` may be excluded
from active-code analysis when the exclusion is explicit and reviewed.

Advisories with no available fix require a recorded threat assessment naming the
advisory, affected API and exploit prerequisites, compensating controls, and
maintainer approval. They remain visible and are re-checked every cycle. A Snyk
Open Source gate may use `--fail-on=all` only for such an approved set: this
continues to report every advisory while failing CI when any upgrade or patch
path exists. An ignore or severity exclusion is not an equivalent control.

### 6.3 Supply chain

- Dependencies are added only via `[workspace.dependencies]` /
  `pyproject.toml` with a PR justification; prefer well-maintained,
  widely-audited crates/packages.
- CI actions are pinned to major versions from trusted publishers; release
  publishing uses **OIDC trusted publishing** (no long-lived tokens).
- Model artefacts (`models/*.onnx`) are SHA-256–manifest verified before use.

### 6.4 Agentic secure-development controls

AI-assisted changes follow the same normative sources and gates as human-authored
changes. Before editing, the agent reads the active session brief, applicable
standards, latest Project State Report and deviation ledger, and any governing
audit; repository code and configuration are the source of implementation facts.

For new or modified first-party code in a Snyk-supported language, the agent runs
Snyk Code through the configured IDE or MCP integration, remediates findings
attributable to the change, and rescans until the applicable gate is clean. A
dependency or manifest change additionally runs the applicable Snyk Open Source
scan and every ecosystem-native audit in §6.2. Findings are never suppressed,
ignored, or excluded without evidence and an approved deviation or amendment.
If Snyk is unavailable, the agent records the blocked validation and must not
represent the change as Snyk-validated; CI remains the authoritative merge gate.
