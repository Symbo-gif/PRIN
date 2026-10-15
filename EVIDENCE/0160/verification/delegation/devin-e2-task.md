# Cold self-audit (read-only) — EXP-002 E2 approval round, code and science

Repository `C:\dev\PRIN`; working tree = commit `ed993e9` plus staged changes.
Do NOT run shell commands or edit files. Print the report to stdout.

Diffs since the previously reviewed commit `0d4278d`:
- `C:\Users\there\AppData\Local\Temp\claude\c--dev-PRIN\caa74057-f2dc-43bd-8cf8-b18f5c141339\scratchpad\e2\delta-code.diff`
- `...\scratchpad\e2\delta-records.diff` (same directory)

Key files: `benchmarks/campaign/exp002_driver.py` (new `sensitivity_bytes`,
`sensitivity_sha256` field, `_FILE_DIGEST_KEYS`), `tests/test_exp002_driver.py`,
`tests/_basetemp.py`, `tests/conftest.py` (new `pytest_sessionstart`),
`tests/test_basetemp.py`, `tests/test_0160_manifest.py`,
`crates/prin-kernels/src/compat.rs`, `.github/workflows/python.yml`,
`ci/lint-constraints.txt`,
`DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/{preregistration.md,e2-review.md}`,
`EVIDENCE/0160/verification/e2-review/{CrlfCanonical.lean,z3_png_colour_rules.py,crlf_model_crosscheck.py,e2_static_verification.py}`.

Context: EXP-002 is a pre-registered experiment. This round accepted E1, made
the E2 decisions under a maintainer delegation, APPROVED the protocol, and
fixed two hosted CI failures and a flaky pytest fixture. The next step is E3
execution, so anything that would make E3 fail, mis-record, or produce a
misleading verdict matters most.

Hunt for real defects, each with a concrete scenario:
1. `sensitivity_bytes`: does it faithfully implement "the section 5.4 policy
   as committed at 6314532" (compare `git show 6314532:benchmarks/campaign/exp002_driver.py`
   `_normalized_pdf`/`normalized_bytes` — you may read that version if you can
   locate it; otherwise compare against the protocol text)? Any input on which
   it raises where the approved policy does not (would abort a genuine E3 run)?
2. Closure now requires `sensitivity_sha256` on every file record: can a
   genuine `collect_reproduction` record ever lack it?
3. `tests/_basetemp.py` + `conftest.py` hook: could it delete anything other
   than the user-given `--basetemp`? Behaviour under pytest-xdist, `--basetemp`
   relative paths, `rootpath` vs cwd, symlinked basetemp, Python 3.11
   (`onerror` branch), Linux hosted runners. Could it make CI or the local
   gate slower or fail where it passed before?
4. `compat.rs` rewrite: identical behaviour to the removed loop?
5. Lint job numpy pin: could adding numpy change `mypy python/prin --strict`
   results on CI (torch 2.13 + numpy 2.5.1)? Is numpy 2.5.1 installable on
   ubuntu Python 3.12?
6. The Lean proof (`CrlfCanonical.lean`): are `canon`/`translate` faithful
   models of `bytes.replace(b"\r\n", b"\n")` and CPython Windows text-mode
   writing? Is the stated conclusion ("same content up to a CR immediately
   before an LF") actually what the two theorems imply? Any gap?
7. The Z3 script: is the transcription of the driver's PNG expression
   faithful to `_validate_png`? Is the encoded "specification" correct?
8. Scientific rigor of the E2 decisions in `e2-review.md` §4 (especially
   9: H2 kept confirmatory; H3 primary under the amended policy plus a
   sensitivity analysis). Is any decision inconsistent with
   `DOCS/standards/Experimentation_Standards.md` or the protocol? Is there a
   path by which E4 could still report only the favourable H3 verdict?
9. E3 readiness: will the driver's admission pass on a clean checkout of the
   approval commit? (Protocol header parse: `**Status:** APPROVED`, and the
   approval line must start `MichaelMaillet, YYYY-MM-DD UTC`.) Anything in
   the approved protocol or e2-review.md §8 checklist that conflicts with the
   driver's actual behaviour (e.g. the PowerShell listing-digest one-liner)?

Do NOT report as defects: the driver refusing DRAFT protocols; synthetic-only
tests; global storage coupling; not counting publication files at closure;
frozen 0159 evidence unchanged.

Report each finding: severity, file:line, scenario, reason. List areas found
sound.
