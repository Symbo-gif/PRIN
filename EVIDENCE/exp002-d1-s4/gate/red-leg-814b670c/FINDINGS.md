# Red required leg at `814b670c` — findings

**Recorded 2026-10-17, session `EXP-002-D1` S4. Status: the required local gate
is RED at the commit this session would close. No merge was performed.**

## 1. What failed

The required full-suite leg (`pytest tests/ parity/`, no coverage, amendment #49
invocation) at `814b670c` finished with:

```
==== 1 failed, 6331 passed, 184 skipped, 61 warnings in 5613.67s (1:33:33) ====
FAILED tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression
```

`gate/red-leg-814b670c/long-legs.txt` records `fast suite exit: 0`,
`full suite exit: 1`, `overall: 1`. The fast leg was green
(4044 passed / 178 skipped / 55 deselected, 0:40:22).

The assertion, verbatim from `console.txt`:

```
tests\test_acceptance_subconscious.py:608: in test_no_gpu_throughput_regression
    assert ratio < 1.30, f"Throughput ratio {ratio:.2f} > 1.30"
E   AssertionError: Throughput ratio 22.07 > 1.30
E   assert 22.074290046215165 < 1.3
```

The test ran 20:28:54Z → 20:29:07Z, at 8% collection. It failed at 20:29:07Z.

## 2. The change set is not the cause (measured)

`attribution.txt` records:

* `157ce5bc` — the commit whose full-suite run **passed** this same test
  (`gate/full/console.txt:618`, `PASSED [ 8%]` at 20:07:49Z) — is an ancestor of
  `814b670c`.
* `git diff --name-only 157ce5bc..HEAD` over `python/`, `rust/`, `crates/`,
  `Cargo.toml`, `Cargo.lock`, `pyproject.toml` **and `tests/`** is **empty**.

So `tests/test_acceptance_subconscious.py` and the `SubconsciousDaemon` code it
exercises are byte-identical between the run that passed and the run that
failed. The only files changed in between are documentation, evidence, and
`parity/test_parity_publication.py`. Parity tests collect at ~100% and cannot
affect a test that ran at 8%.

## 3. Attribution: load sensitivity, measured not guessed

Testing Standards §7 item 3 forbids recording a guessed attribution as cause, so
the mechanism was measured rather than assumed.

**Whole-leg contention does not discriminate the two runs.** From
`contention-failing-leg.txt` and `contention-passing-leg.txt`:

| | passed (`157ce5bc`) | failed (`814b670c`) |
|---|---|---|
| host `cpu_percent` median | **96.5 %** | **96.2 %** |
| samples ≥ 90 % | 84 / 111 | 79 / 108 |
| samples ≥ 95 % | 72 / 111 | 65 / 108 |
| pytest CPU-s / wall-s median | 0.422 | **0.483** (better) |
| host CPU nearest the test | 94.9 % | 97.4 % |

The run that **passed** had marginally *higher* whole-leg contention and *worse*
pytest CPU efficiency. A 93-minute median cannot resolve the 13-second window
this assertion measures in, so it is not the discriminating variable — and this
is why "the host was busy" is **not** recorded as the cause.

**Isolated reproduction does discriminate, and does identify the mechanism.**
`isolated-throughput.sh` runs the single test five times, sampling host CPU
before each iteration and recording every outcome:

| run | host CPU across iterations | test wall time | outcome |
|---|---|---|---|
| #1 `run1-transcribed.txt` | 12.2, 57.7, 97.1, **99.7**, **97.2** % | 6.7–9.9 s | **3 passed / 2 failed** — ratios **2.13**, **3.42** |
| #2 `run2-captured.txt` | 11.9, 22.7, 20.8, 24.1, 14.9 % | **4.1–4.3 s** | **5 passed / 0 failed** |

Run #1 is a verbatim **transcription** (it was executed without redirection);
run #2 is an authentic capture and the primary record. Both are retained.

The mechanism is therefore measured: the assertion is a wall-clock ratio whose
outcome tracks instantaneous host load. On a quiet host it completes in ~4.2 s
and passes 5/5; at 97–99.7 % host CPU it takes 7–10 s and fails intermittently.
The in-suite ratio of 22.07 is far above the isolated 2.13/3.42, consistent with
a full pytest session carrying far more concurrent load (2 pytest processes plus
live Jupyter kernels) than one isolated test.

## 4. Re-running the required leg is not available

Run #1 measured **3 passes / 2 failures on the same commit**. The full suite
generates most of its own ~96 % host load, so ambient quiet cannot be arranged
for it. A further required-leg run is therefore a **coin flip**, and repeating it
to obtain a green result is the rerun-until-green that §7 item 6 prohibits
("Incomplete is not pass"; no session may skip tests, weaken assertions, shorten
scientific samples, or suppress warnings to obtain a green result). The red leg
is recorded as red.

## 5. DV-032's hardening disposition is empirically refuted

`DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-032 states the test is
**PARTIALLY HARDENED (2026-09-15, WP-036G S4)** — "now runs fixed work after
warm-up and compares seven-sample medians at the unchanged `<1.30` limit; its
quarantine is removed" — and documents it as measuring "**~1.28–1.32 under
load**".

Measured at `814b670c` instead: **2.13**, **3.42** (isolated, host 97–99.7 %)
and **22.07** (in-suite). The seven-sample-median hardening does **not** make the
assertion robust, and the documented 1.28–1.32 band is wrong by more than an
order of magnitude in the in-suite case. Its quarantine was removed on a claim
this session has directly falsified.

DV-032's own recorded fix path remains owed: "convert each to a seeded
frame-count / `pytest-benchmark` case with an explicit tolerance".

## 6. Disposition

* The red leg is preserved verbatim; the passing control run at `157ce5bc` in
  `gate/full/` was **not** overwritten.
* No test was skipped, xfailed, re-quarantined, or edited. The `<1.30` tolerance
  is untouched (§7 items 6 and 8).
* Converting the test to DV-032's registered deterministic form is **S1-class
  code work** requiring its own S2 audit. It was deliberately **not** performed
  inside this S4 documentation session, because doing so in order to turn this
  gate green would compromise the session discipline and read as weakening an
  assertion to obtain a pass.
* **PR #34 was not merged.** Merging to `main` is irreversible and shared-state,
  and authorization A1 was premised on a green required gate, which does not
  hold. Escalated to the maintainer with this evidence.
