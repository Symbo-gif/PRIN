# PRIN Audit Report — Cycle 036F / WP-036F

**Date:** 2026-09-02
**Auditor:** AI pair (Claude Sonnet 5)
**Scope:** WP-036F "DirectML controller-graph execution" — the single S1 commit
`50fb088`: the re-exported three-input-`Gemm` controller graph
(`models/subconscious_controller.onnx` + `models/manifest.json`), the
`tools/wp036f_reexport_controller.py` transform/verifier, the
`tools/wp036f_provider_latency.py` evidence tool, the extended
`tests/test_daemon_controller.py::TestCrossProviderAgreement` and new
`tests/test_wp036f_reexport.py`, the `crates/prin-daemon` integration-test
digest constants, and the governing artefacts.
**Sessions:** `0144U` implementation; `0144V` this audit
**Active brief:** `DOCS/sessions/phase-6/0144V-wp036f-s2-directml-controller-graph-execution.md`
**Git state:** `main` @ `50fb088` (predecessor `b7d3ee7` = WP-036E S4)
**Verdict:** PASS-WITH-FINDINGS

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | Change is confined to a graph-transform pass over the committed artefact + verifier/evidence tools + tests + docs. No controller algorithm, daemon runtime, backend-selection, DV-025 symbol, or `prin` public-API change. NPU half correctly left OPEN. One D4 doc-catch-up (`DOCS/experiments/README.md` gained a `0144Q` handoff pointer) noted, not charged. |
| Plan/architecture conformance (A2) | ✅ | Amendment #38 authorises "an `onnx` graph transform pass" as an alternative to an export-path change; S1 correctly found no first-party PyTorch export path (`export_to_onnx` is DV-025 / WP-036C scope) and used a transform. `Y = αA'B' + βC` with `β=1, C=0` is exact IEEE-754; the graph function is provably unchanged. Numerical authority (Rust) untouched; Python adds no numerics. |
| Tests in tandem + coverage (A3) | ⚠️ | 21 new `test_wp036f_reexport.py` tests + 1 `TestCrossProviderAgreement` case, all committed with the change and independently green. **Changed-code coverage is 94% (< 95%)** — several `transform_graph` error paths and `_check` drift branches are untested and `coverage` runs cleanly at this scope (WP036F-F1). |
| Numerical parity + invariants (A4) | ✅ | Independently reproduced: the re-exported graph is **bit-identical** to the pristine PRINet 3.0 archive graph on `CPUExecutionProvider` over the 48-case set (`np.array_equal` on `uint32` views); `DmlExecutionProvider` executes it (active provider `DmlExecutionProvider`, not a CPU fallback) and agrees with CPU at `max_abs_diff 7.15e-7`, within Testing Standards §3's `rtol=1e-5, atol=1e-6`. No tolerance was loosened. |
| Quality gates (A5) | ✅ | `cargo fmt`/`clippy -D warnings`/`cargo test --workspace`/`cargo doc -D warnings` clean; `ruff check` + `ruff format --check` clean; `mypy python/prin --strict` 0 errors; `interrogate` 97.6%. `mypy --strict` on the two new *tools* has 3 stub/annotation nits (WP036F-F2) — outside the standard's `python/prin`-scoped gate, matching 5 pre-existing tools. |
| Security (A6) | ✅ | `bandit -r python/prin` and scoped `bandit` on both new tools: 0 issues. `cargo audit` exit 0 (3 governed advisories, no `Cargo.toml` change). `pip-audit` clean. Snyk Code: 5 pre-existing LOW path-traversal findings repo-wide, **none in the WP-036F files**; scoped scan of the two tools + test file = 0. Snyk Open Source not triggered — `git diff` confirms no `Cargo.toml`/`Cargo.lock`/`pyproject.toml`/requirements change. No secret, no runtime codegen. |
| Docstring/doc coverage (A7) | ✅ | `interrogate` 97.6% (≥95%); Rust workspace rustdoc clean under `-D warnings`. Both new tools carry a module docstring and Google-style docstrings on every public function. |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/stub marker; `prin.__all__` / `FROZEN_PUBLIC_API` / `_prin_core.pyi` unchanged (`verify_api_surface` → `(set(), set())`). Old digest `3396bfdd…` remains only in the two immutable EVIDENCE artefacts (`0017-wp005`, `0109-wp028`) and historical DOCS; every live consumer moved to `d7d7935b…`. `git diff --check` clean. |
| CI status (A9) | ✅ (local substitute) | Per amendment #28 nothing is pushed this cycle; the S4 push (`0144X`) runs CI over the whole range. Local gate fully reproduced this session (see §2). |
| Artefact trail (A10) | ✅ | S1 handoff, evidence JSON, CHANGELOG, SESSION_REGISTER, phase-6 index, brief status, and all touched READMEs are present and mutually consistent. DV-006 register row + DoD item 7 correctly left for S4 per the brief. |

The mathematical-identity and DirectML-execution acceptance criteria are met and
independently verified; scope, security, and public-API invariants hold. The
cycle passes with findings because the new first-party tool code lands below the
Testing Standards §4/§5 ≥95% changed-code coverage gate (WP036F-F1, D2) and the
two tool modules carry minor `mypy --strict` nits (WP036F-F2, D4). No source was
changed during this S2 audit.

## 2. Methodology

Environment: Windows 11 (10.0.26200) maintainer host; AMD Ryzen 7 8700F (no XDNA
NPU); Python 3.14.0; `onnxruntime` 1.24.4 with
`get_available_providers() == ['DmlExecutionProvider', 'CPUExecutionProvider']`;
`onnx` 1.22.0 (repo) / 1.22.x; `numpy` 2.5.1.

```powershell
# Range and hygiene
git show --stat 50fb088            # 18 files, 1138 insertions(+), 17 deletions(-)
git diff --check b7d3ee7..50fb088  # -> clean (exit 0)

# A2/A4 — independent ONNX structural diff (re-exported vs pristine 3.0 archive)
python - <<'PY'   # summarised
#  ir_version, opset_import, producer, graph.name, graph.input, graph.output,
#  and every non-Gemm node + attribute: IDENTICAL.
#  Gemm nodes: inputs [state_vector,net.0.weight] -> [...,net.0.bias] (x3).
#  initializers: + net.0.bias (f32,[128]), net.3.bias (f32,[128]),
#                net.6.bias (f32,[8]); all raw_data all-zero.
PY

# A4 — independent 48-case CPU differential + DirectML agreement
python - <<'PY'
# rng = np.random.default_rng(20260902); batch (48,32) f32
# CPU re-exported vs CPU pristine archive: np.array_equal(uint32 views) -> True
# DML session get_providers()[0] == 'DmlExecutionProvider'
# DML vs CPU max abs diff -> 7.152557e-07  (< atol 1e-6 + rtol 1e-5 * |cpu|)
# ort.InferenceSession(pristine, providers=['DmlExecutionProvider'])
#   -> INVALID_GRAPH: fused op ('node_Gemm_144')+('node_relu') input size 2 not in [3,3]
PY

python tools/wp036f_reexport_controller.py --check
# -> OK: 3 Gemm nodes, all three-input; manifest current

# A8 — digest propagation
git ls-files | xargs grep -l 3396bfdd…4102   # -> EVIDENCE/0017, EVIDENCE/0109 only (both immutable)
git ls-files | xargs grep -l d7d7935b…341a   # -> manifest.json, integration_controller_model.rs,
#                                                 0144U handoff, 0144U evidence json

# A5 — Rust
cargo fmt --all -- --check                                  # clean
cargo clippy --workspace --all-targets -- -D warnings       # clean
cargo test --workspace                                      # 48 "test result: ok", 0 FAILED
#   prin-daemon: integration_controller_model 7 pass, parity_subconscious 8 pass
RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps     # clean

# A3/A5/A7 — Python
ruff check python/ tests/ benchmarks/ tools/ parity/        # All checks passed
ruff format --check python/ tests/ benchmarks/ tools/ parity/  # 245 files already formatted
mypy python/prin --strict                                   # Success, 62 files
interrogate -c pyproject.toml python/prin                   # 97.6% PASS
bandit -r python/prin -c pyproject.toml                     # 0
bandit -c pyproject.toml tools/wp036f_reexport_controller.py tools/wp036f_provider_latency.py  # 0

pytest tests/ -m "not slow and not gpu" -q -p no:cov --basetemp=.pytest_basetemp
# -> 2765 passed, 202 skipped, 30 deselected
pytest tests/test_wp036f_reexport.py tests/test_daemon_controller.py parity/test_parity_subconscious.py -q
# -> 126 passed, 1 skipped   (21 wp036f + 24 daemon-controller incl. the new DirectML case)

# A3 — changed-code coverage (coverage tooling ran clean at this narrow scope, twice)
pytest tests/test_wp036f_reexport.py --cov=tools.wp036f_reexport_controller \
       --cov=tools.wp036f_provider_latency --cov-report=term-missing
#   wp036f_provider_latency.py     97%   (miss 99, 191)
#   wp036f_reexport_controller.py  92%   (miss 71-72, 121-122, 174, 184-185, 188, 201-202, 206)
#   TOTAL                          94%

# A6 — security
cargo audit                           # exit 0; paste RUSTSEC-2024-0436, bincode RUSTSEC-2025-0141,
#                                        chacha20 yanked  (3 allowed, no Cargo.toml change)
pip_audit .                           # No known vulnerabilities found
snyk code test --severity-threshold=low   # 5 LOW repo-wide (wp001_baseline x3, wp030_mot_fixture,
#                                            wp031_stats_fixture) — 0 in WP-036F files
snyk code test tools/wp036f_reexport_controller.py tools/wp036f_provider_latency.py \
               tests/test_wp036f_reexport.py --severity-threshold=low   # 0 issues

# A2/A8 — architectural / public-surface gates
python tools/check_no_python_numerics.py    # No Python numerics in 19 WP-036 S1 compat modules
python -c "import prin;from prin._deprecation import verify_api_surface;print(verify_api_surface(prin.__all__))"
#   -> (set(), set())
python tools/wp001_baseline.py check         # WP-001 baseline validation passed
python tools/check_dv_register_gates.py      # passed (33 DV rows, 198 session entries)
```

## 3. Detailed findings

### 3.1 A1/A2 — Scope and architecture

The S1 diff is 18 files. The only functional artefact touched is
`models/subconscious_controller.onnx`; the only first-party code added is the two
`tools/wp036f_*.py` scripts and the two test additions. `crates/prin-daemon/`
sees changes **only** in `tests/integration_controller_model.rs` (three digest
literals + one byte-size constant, no assertion logic). `python/prin/` is
untouched. This matches amendment #38's WP-036F scope exactly:

- **Transform pass, not export path.** Amendment #38 scope item 1 permits "an
  `onnx` graph transform pass". S1 verified there is no first-party PyTorch
  export path (`export_to_onnx` / `retrain_controller` / `quantize_onnx` are
  DV-025, re-targeted to WP-036C, and explicitly a WP-036F non-goal) and
  implemented `transform_graph(model)` in
  `tools/wp036f_reexport_controller.py:76`, which copies the model and appends
  one zero-valued `float32` initializer per two-input `Gemm`. It is idempotent
  (`len(node.input) == 3` short-circuits at line 102) and doubles as the
  `--check` verifier.
- **Function is provably unchanged.** `Gemm` computes
  `Y = alpha·A'·B' + beta·C`; `beta` is already `1.0` on all three nodes and the
  new `C` is all zeros, so `Y_ij = (A'·B')_ij + 0.0` — exact for every finite
  IEEE-754 value. Confirmed structurally (independent proto diff: `ir_version`,
  `opset_import`, `producer_*`, `graph.name`, `graph.input`, `graph.output`, and
  every non-`Gemm` node and attribute are byte-identical between the re-exported
  graph and the pristine 3.0 archive; the only delta is the three added bias
  inputs and their three all-zero inline initializers) and empirically (§3.3).
- **No controller-algorithm / daemon-runtime / backend-selection change.**
  `crates/prin-daemon/src/**` and `python/prin/daemon.py` carry no diff. The
  `SubconsciousController` and `_executable_backends()` used by the new test are
  pre-existing; the cross-provider harness widens to DirectML automatically
  because it already probes providers at run time.
- **NPU boundary respected.** DV-006's VitisAI / Ryzen AI NPU half is untouched
  and stays OPEN: `VitisAIExecutionProvider` is not registered (Ryzen AI 1.7.0
  ships it as `cp312`; the venv is CPython 3.14) and the host CPU carries no XDNA
  NPU. The S1 handoff §7 logs this correctly as hardware/wheel-gated, same class
  as DV-001.
- **DV-006 register row and DoD item 7** are correctly **not** edited this
  session — the brief and amendment #38 assign those updates to WP-036F S4
  (`0144X`). The register still shows DV-006 `OPEN`.

One cosmetic observation, not charged as a finding: this commit also added a
`0144Q-wp036e-s1-handoff.md` bullet to `DOCS/experiments/README.md` — a
WP-036E artefact index catch-up that WP-036E S4 missed. It is accurate and
harmless; note it in the S4 doc pass.

### 3.2 A3 — Tests in tandem and coverage

Behaviour and tests are in the same commit. `tests/test_wp036f_reexport.py`
(21 tests) covers: committed-artefact structure (`[3,3,3]` arities, inline
`float32` zero bias, unchanged I/O contract, manifest digest matches file),
the transform function (idempotency on the committed graph, three-bias rebuild
of a stripped graph, `_bias_name` derivation, bad-arity and non-initializer
rejection), `main` round-trip and two `--check` drift cases (stale manifest,
two-input `Gemm`), the **R3 CPU bit-identity** gate (vs an in-memory
bias-stripped copy *and* vs the pristine archive), DirectML rejection of the
pre-transform graph + execution + agreement of the re-exported one (`skipif`
`DmlExecutionProvider` absent), and the latency tool's `build_report` / `main`.
`tests/test_daemon_controller.py::TestCrossProviderAgreement` gains
`test_directml_executes_the_reexported_graph`. All are independently green.

**WP036F-F1 (D2).** Changed-code coverage is **94%**, below Testing Standards
§4/§5's ≥95% gate for new/changed code. Unlike the general DV-033 condition
(`coverage` "segfault or hang" on this host), `pytest --cov` scoped to the two
new modules ran cleanly and repeatably this session and reports:

| Module | Cover | Uncovered lines |
|---|---|---|
| `tools/wp036f_reexport_controller.py` | 92% | 71–72 (`_gemm_out_features` non-rank-2 weight `ValueError`), 121–122 (bias-name collision `ValueError`), 174 (`_check` "no Gemm nodes"), 184–185 (`_check` bias not inline), 188 (`_check` bias not `float32` zero), 201–202 (`_check` manifest lists a missing file), 206 (`_check` manifest `sha256` stale) |
| `tools/wp036f_provider_latency.py` | 97% | 99 (`_pre_transform_check` archive absent), 191 (`main` DirectML not registered) |

Every uncovered line is an instrumentable branch (an error path or a drift
detector), not a non-instrumentable kernel body, so DV-004's exclusion class
does not apply. The S1 handoff's "manual review, CI codecov authoritative"
disposition is not warranted here because the measurement is locally available
and shows a real gap — the same position the WP-036E S2 audit took at
WP036E-F3, which S3 resolved with added tests rather than a CI deferral.

**Remedy (S3):** add ~7 targeted tests — a crafted non-rank-2 `Gemm` weight, a
pre-existing colliding `net.N.bias` initializer, a `_check` run over an empty
graph, over a graph whose `Gemm` third input is a graph input rather than an
initializer, over a graph with a non-zero bias, over a manifest naming a
missing file, and over a manifest with a correct size but wrong digest; plus a
`monkeypatch` of `latency_tool._PRISTINE` to a missing path and of
`available_providers()` to exclude DirectML — then re-run the scoped `--cov`
and confirm ≥95%.

### 3.3 A4 — Numerical parity and invariants

Independently reproduced this session (not merely re-read from the S1 evidence
JSON), `rng = np.random.default_rng(20260902)`, batch `(48, 32)` `float32`:

- **CPU bit-identity vs the 3.0 reference.** `np.array_equal` on the `uint32`
  views of the re-exported-graph output and the pristine PRINet 3.0 archive
  graph output on `CPUExecutionProvider` → `True`. `max_abs_diff = 0.0`. This is
  the R3 gate and it holds against the actual archived reference, not only an
  in-memory copy.
- **DirectML executes it.** `ort.InferenceSession(model, providers=['DmlExecutionProvider','CPUExecutionProvider']).get_providers()[0] == 'DmlExecutionProvider'`
  — a real DirectML placement, not a silent CPU fallback.
- **DirectML agrees with CPU.** `max_abs_diff = 7.152557e-07`, inside
  `atol=1e-6 + rtol=1e-5·|cpu|` everywhere. This is the standing Testing
  Standards §3 GPU-vs-CPU default already used by `TestCrossProviderAgreement`;
  it was not loosened.
- **The pre-transform graph is still rejected by DirectML** with the documented
  `INVALID_GRAPH … DmlFusedGemm … input size 2 not in range [min=3, max=3]`,
  confirming the fix addresses the actual failure mode and that the archived
  3.0 graph fails identically (a runtime/graph condition, matching amendment
  #13's WP-005 finding).

DirectML-vs-CPU latency is recorded in
`EVIDENCE/0144U-wp036f-s1-controller-provider-report.json`
(`latency_ms_median_batch48`: CPU ≈ 0.033 ms, DirectML ≈ 0.27 ms, batch 48,
median of 500 warm calls). DirectML being ~8× slower on this ~50 K-parameter MLP
is dispatch/copy overhead on a graph this small — recorded honestly, correctly
not treated as a regression (backend-selection logic is out of scope, and the
daemon does not select DirectML for the controller by default).

### 3.4 A5 — Quality gates

`cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D
warnings`, `cargo test --workspace` (48 `test result: ok`, 0 `FAILED`;
`prin-daemon` `integration_controller_model` 7/7 and `parity_subconscious` 8/8
green with the new digest), and `RUSTDOCFLAGS=-D warnings cargo doc --workspace
--no-deps` are all clean. `ruff check` and `ruff format --check` pass over
`python/ tests/ benchmarks/ tools/ parity/`. `mypy python/prin --strict` reports
0 errors across 62 files. `interrogate` is 97.6%.

**WP036F-F2 (D4).** `mypy --strict` on the two new tool modules (outside the
Coding Standards §5 gate, which is scoped to `python/prin`) reports 3 issues:

- `tools/wp036f_reexport_controller.py:148` — `list(manifest["files"])` where
  `manifest` is `dict[str, object]`; the trailing `# type: ignore[arg-type]`
  now names the wrong error code (`mypy` emits `call-overload` here).
- `tools/wp036f_provider_latency.py:131` —
  `np.allclose(dml_out, cpu_out, **_TOL)` splats a `dict[str, float]` into what
  the numpy stub treats as a positional `bool`.

Both are cosmetic: the code is correct at run time (`rtol`/`atol` are float
kwargs; the manifest list is genuinely a list). Five pre-existing tools already
fail `mypy tools/ --strict`, so this is consistent with current project posture,
not a regression of a green gate. **Remedy (S3 or explicit one-cycle carry):**
annotate `manifest["files"]` via `cast(list[dict[str, object]], …)` and pass
`rtol=…, atol=…` explicitly to `np.allclose`; or record a documented
`tools/`-scope exclusion. Lowest priority.

### 3.5 A6 — Security

`bandit -r python/prin` and a scoped `bandit` over both new tools: 0 issues.
`cargo audit` exits 0 with the three governed advisories (`paste`
RUSTSEC-2024-0436, `bincode` RUSTSEC-2025-0141, `chacha20` yanked); `git diff`
confirms no `Cargo.toml`/`Cargo.lock` change, so the DV-008/DV-017 governance is
untouched. `pip-audit .` is clean. Snyk Code at `--severity-threshold=low`
reports 5 LOW path-traversal findings repo-wide, all in unrelated command-line
fixture/baseline tools (`wp001_baseline.py` ×3, `wp030_mot_fixture.py`,
`wp031_stats_fixture.py`) — the identical set the WP-036E S2 audit recorded —
and **zero** in the WP-036F files; a scoped scan of the two new tools plus the
new test file returns 0. Snyk Open Source was correctly not triggered: no
dependency or manifest file changed. No secret, no runtime code generation.

### 3.6 A7/A8/A10 — Documentation, hygiene, artefact trail

`interrogate` 97.6% and rustdoc `-D warnings` clean. Both new tools have a
module docstring and Google-style docstrings on every public function
(`Args:` / `Returns:` / `Raises:` present where applicable). No TODO/FIXME/stub
marker in the range. `prin.__all__`, `FROZEN_PUBLIC_API`, and
`_prin_core.pyi` are unchanged; `verify_api_surface(prin.__all__)` →
`(set(), set())`. `check_no_python_numerics.py`, `wp001_baseline.py check`, and
`check_dv_register_gates.py` all pass.

Digest propagation is complete and correct: the old digest
`3396bfdd…4102` survives only in `EVIDENCE/0017-wp005-s1-ort-probe.json`
(immutable phase-0 artefact; `test_phase0_gate.py` asserts it is never mutated,
and the gate reads only `can_run`) and `EVIDENCE/0109-wp028-s1-controller-provider-report.json`
(the prior-failure evidence this very brief cites), plus historical audit/PSR
prose. `models/manifest.json`, the Rust integration test, the S1 handoff, and
the new evidence JSON all carry `d7d7935b…341a`; `prin.daemon` derives its
expected digest from the manifest at run time, so it follows automatically
(`the_committed_manifest_verifies_every_model_artefact` green).

CHANGELOG `[Unreleased]`, `SESSION_REGISTER.md` (`0144U` → COMPLETE),
`DOCS/sessions/phase-6/README.md`, the `0144U` brief status, and the touched
READMEs (`models/`, `tools/`, `tests/`, `EVIDENCE/`, `DOCS/experiments/`) are
present and mutually consistent. `git diff --check` is clean.

### 3.7 A9 — CI / local reproduction

Per amendment #28 nothing is pushed this cycle; CI runs once at the S4 push
(`0144X`) over the full `0144U`–`0144X` range. The full local gate was
reproduced this session (§2) and is green apart from the changed-code coverage
gap in §3.2.

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP036F-F1 | D2 | `tools/wp036f_reexport_controller.py` (lines 71–72, 121–122, 174, 184–185, 188, 201–202, 206); `tools/wp036f_provider_latency.py` (99, 191) | Changed-code coverage is 94% (< 95%). Instrumentable error paths in `transform_graph` / `_gemm_out_features` and every drift branch of `_check` are untested; `pytest --cov` runs cleanly at this scope this session, so the DV-033 "manual review / CI-authoritative" fallback is not warranted. | Testing Standards §4/§5; Development Workflow §3 S1 exit ("New/changed code at ≥95% coverage"); WP-036F acceptance "≥95% coverage on new/changed first-party code" | Add ~7 targeted tests for the error/drift branches (non-rank-2 weight, bias-name collision, empty graph, non-initializer bias input, non-zero bias, manifest missing-file, manifest digest-stale) plus `monkeypatch` cases for `_PRISTINE` absent and DirectML unregistered; re-run scoped `--cov` and confirm ≥95%. If any residual line is genuinely defensive/unreachable, document it explicitly (DV-033-style) rather than leaving it silent. |
| WP036F-F2 | D4 | `tools/wp036f_reexport_controller.py:148`; `tools/wp036f_provider_latency.py:131` | `mypy --strict` nits in the new tools: a stale `# type: ignore[arg-type]` (actual code is `call-overload`) on `list(manifest["files"])`, and a `**dict` splat into `np.allclose`. Outside the `python/prin` mypy gate and consistent with 5 pre-existing tools, but avoidable in code written this cycle. | Coding Standards §5 (gate is `python/prin`-scoped — advisory here); repository hygiene A8 | `cast(list[dict[str, object]], manifest["files"])`; pass `rtol=`/`atol=` explicitly to `np.allclose`. Fix in S3 or take the one permitted D4 carry with a documented `tools/` mypy-scope note. |

## 5. Deviation-ledger delta

New findings to add to the cumulative ledger at WP-036F S4:
`WP036F-F1` (D2) and `WP036F-F2` (D4). No prior finding changes status during
this read-only audit.

Deferred-validation adjudication:

- **DV-006 — DirectML half:** the evidence required to close it is **in place
  and independently verified** — the re-exported graph is bit-identical to the
  3.0 reference on CPU, `DmlExecutionProvider` executes it, and cross-provider
  agreement holds within Testing Standards §3 tolerance, with provider/latency
  acceptance recorded. The register row and DoD item 7 update remain a **WP-036F
  S4 (`0144X`)** action per amendment #38 and the brief; this audit confirms
  they are not blocked. Amendment #13's deferred DirectML condition is
  dischargeable at S4.
- **DV-006 — VitisAI / Ryzen AI NPU half:** stays **OPEN**, hardware/wheel-gated
  (no XDNA NPU; no CPython-3.14 VitisAI wheel). Unchanged by this WP; WP-036G
  consolidates its permanent disposition class.
- **DV-025** (`retrain_controller` / `export_to_onnx` / `quantize_onnx`):
  untouched — no symbol added, the transform is a standalone tool. Boundary
  respected.
- **DV-033** (per-change coverage on the maintainer host): this session found
  `coverage` *does* run at a narrow module scope; WP036F-F1's remedy should be
  measured that way rather than deferred to CI.

## 6. Verdict and required actions

**PASS-WITH-FINDINGS.** No D1. The two acceptance criteria that define WP-036F —
mathematical identity of the re-exported graph (48-case CPU bit-identity vs the
3.0 reference) and `DmlExecutionProvider` execution with in-tolerance
cross-provider agreement — are met and independently reproduced. Scope,
architecture, security, numerical authority, and public-API invariants all hold.
The findings are a changed-code coverage shortfall (D2) and cosmetic type-hint
nits in the new tools (D4).

Ordered S3 (`0144W`) action list:

1. **WP036F-F1** — add the error-path / drift-branch tests listed in §4; re-run
   `pytest tests/test_wp036f_reexport.py --cov=tools.wp036f_reexport_controller
   --cov=tools.wp036f_provider_latency --cov-report=term-missing` and confirm
   ≥95%. Document any residual defensive line explicitly.
2. **WP036F-F2** — apply the two one-line type fixes, or record a documented
   `tools/` mypy-scope carry.
3. Re-run the touched-area gates (`cargo test -p prin-daemon`,
   `pytest tests/test_wp036f_reexport.py tests/test_daemon_controller.py`,
   `tools/wp036f_reexport_controller.py --check`, `ruff`, `mypy python/prin
   --strict`, `bandit`, `cargo audit`, `pip-audit`, scoped Snyk Code) and append
   the closure table.
4. S3 is mandatory even though the verdict is not FAIL (Development Workflow §3):
   record the closure and an independent delta re-audit.

**Maintainer acknowledgment of the verdict:** pending — to be recorded by the
maintainer (Development Workflow §6). S1 is committed locally at `50fb088`; the
push is at S4 (`0144X`) per the amendment #28 cadence.

---

## 7. Closure table (appended by S3 remediation — session `0144W`)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP036F-F1 | FIXED / … | `<sha>` | |
| WP036F-F2 | FIXED / CARRIED(1) / … | `<sha>` | |

**Delta re-audit date:** YYYY-MM-DD — **Result:** CLEAN / findings remain
