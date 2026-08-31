# Session 0144I3 — WP-036D S1 (sub-pass 3/3): GPU test activation, CI, and consolidation

**Status:** COMPLETE
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036D
**Session type:** S1 — Coding
**Predecessor:** [0144I2 — device dispatch and DLPack marshalling](0144I2-wp036d-s1-device-dispatch-and-dlpack-marshalling.md)
**Successor:** [0144J — Audit](0144J-wp036d-s2-gpu-execution-path-ported-acceptance-suite.md)
**Authority:** Project Plan §6/§8, amendments #31/#33/#36, and [`WP-036D-S1-execution-plan-and-decomposition.md`](WP-036D-S1-execution-plan-and-decomposition.md). The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Activate the 8 GPU acceptance tests (Phase C of audit `036b` §8.4), wire the
CI selection, capture GPU-vs-CPU kernel-equivalence evidence, and produce the
WP-036D S1 handoff.

## Contract

- Add `@pytest.mark.gpu` to each of the 8 tests **in addition to** its
  existing reference `@pytest.mark.skipif(not torch.cuda.is_available(), ...)`
  guard — the marker enables CI selection on the runner, the guard skips on a
  CPU host. No other change to any ported test body (Testing Standards §1.1).
- Register the `gpu` marker in `pyproject.toml` (`[tool.pytest.ini_options]`
  `markers`).
- Update `.github/workflows/gpu.yml` to run
  `pytest tests/ -v -m gpu --basetemp=.pytest_basetemp` on
  `PRIN-GPU-Runner`, replacing the documented "zero tests carry
  `@pytest.mark.gpu`, so `-m gpu` selects 0" exit-5 workaround.
- GPU f32 kernel vs CPU f64 reference equivalence evidence for each activated
  path, within Testing Standards §3 tolerances (`rtol=1e-5`, `atol=1e-6`);
  any wider tolerance carries a per-test annotation + Parity Report entry
  (amendment #14/#16/#17/#25), never an assertion edit.
- Full ported CPU acceptance suite re-run: **489 passed, 9 skipped** (the 8
  GPU tests are now marker-selected but still skip on the CPU host; the
  `psutil`-absent skip is unchanged).
- **Non-goals:** `test_gpu.py` / `test_triton_kernels.py` (WP-036C /
  DV-001); `prin-train`; new public symbols; final documentation prose
  (WP-036D S4).

## Required reading

- The 0144I parent brief; the `0144I1` and `0144I2` handoff sections
- `DOCS/audits/036b-wp036b-audit.md` §8.1 (the 8-test inventory) and §8.4
  Phase C
- `.github/workflows/gpu.yml`; `pyproject.toml` pytest config
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-001 / DV-002
- Testing Standards §1.1, §3

## Entry conditions

`0144I1` and `0144I2` committed at their green gates; device dispatch works
on a GPU-capable host.

## Expected work

1. Add the `gpu` marker to the 8 tests and register it.
2. Update `gpu.yml`; verify `-m gpu` now selects 8.
3. Run the 8 tests on `PRIN-GPU-Runner`; capture pass + kernel-equivalence
   evidence; record runner state live.
4. Re-run the full CPU acceptance suite and the CPU quality/security gates;
   confirm no regression.
5. Write `DOCS/experiments/0144I-wp036d-s1-handoff.md`: per-test evidence for
   all 8, acceptance-criterion → evidence map, tolerance-annotation list,
   runner state, and the CPU-path no-regression proof carried from `0144I2`.

## Prohibited

Test-body edits beyond the marker, weakened assertions, undocumented
tolerance drift, `test_gpu.py` activation, `prin-train` changes, scope creep,
or push.

## Exit gate

`-m gpu` selects the 8 tests, they pass on the runner and skip on a CPU host,
the CPU suite is 489 pass / 9 skip, `gpu.yml` runs the marker, and the S1
handoff is complete. The contiguous `0144I`+`0144I1`–`0144I3` range is ready
for the single S2 audit `0144J`. Commit locally only.
