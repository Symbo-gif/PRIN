# EXP-001 D1 correction — S1 evidence

Status: **current** (S1 complete; regenerated for the 67-case exactness audit
and the independent-review remediation of 2026-09-27, audit record §S1.9).

Root-cause evidence for the EXP-001 D1 correction cycle, session S1
([brief](../../DOCS/sessions/contingencies/2026-09-23-exp001-d1-s1-correction-implementation.md);
record in [`DOCS/audits/2026-09-24-exp001-d1-correction-audit.md`](../../DOCS/audits/2026-09-24-exp001-d1-correction-audit.md)).
Every file here was generated on the E3 host (Windows 11, project venv,
`torch 2.11.0+cu128`, `numpy 2.5.1`) by the committed scripts below, run from
the repository root.

| File | What it is |
|---|---|
| [`root_cause_decomposition.py`](root_cause_decomposition.py) | Generator. Re-derives every H1 and H2a breach and attributes each one by controlled substitution: PRINet 3.0 re-run with its DV-007 casts widened to float64, with PRIN's pre-correction guard swapped in, or from initial phases moved by one ulp. |
| [`root-cause-decomposition-prefix.json`](root-cause-decomposition-prefix.json) | That run against the **pre-fix** build (`bd737e1`, the reproduction commit; extension built from a worktree and imported via `PYTHONPATH`, as the file's `prin_extension` field records). The build reproduces E3 exactly (19/504 and 103/1,000, same sets) and equals PRINet 3.0 evaluated in float64 with the pre-correction guard to `3.3e-12` on every well-conditioned case. |
| [`root-cause-decomposition-postfix.json`](root-cause-decomposition-postfix.json) | The same run against the **post-fix** build (`34e8811`). PRIN matches PRINet 3.0 evaluated in float64 with its native guard on all 978 well-conditioned fuzz cases, 973 of them to `≤ 4e-14`, and on all 504 corpus cases to `2.0e-15`. |
| [`dv007_exactness_audit.py`](dv007_exactness_audit.py) | Generator for the campaign plan §10.4 item 3 evidence. It evaluates PRINet 3.0's own discrete map (equations, Euler/RK4 update, guards, phase wrap modulo the float64 `2π`, metrics) in 50-digit mpmath from each case's exact float64 initial state, and runs SymPy lemmas L1–L4. |
| [`dv007-exactness-audit.json`](dv007-exactness-audit.json) | For all **67** adjudicated DV-007 breaches (19 H1, 48 H2a — including the 10 well-conditioned cases that are also guard-sensitive; S1.9 widened the scope from 57): PRIN is inside the registered tolerance with no breach — within `3.6e-15` of the exact map on H1 and `4.7e-14` on the DV-007-only cases, with the 10 combined amplitude-regime cases at worst `7.6e-8` (rtol-dominated, still zero breaches) — while the reference is outside the registered tolerance (up to `5.05`). The reference is the erroneous side in 67/67. All five SymPy lemmas hold. |

In both decomposition files `git_head` is the checkout the script ran from
(`34e8811`, which supplied the script, the gates, and the PRINet 3.0 reference).
The PRIN build under test is identified by `prin_package` / `prin_extension`:
`C:\dev\PRIN-prefix\…` is the `bd737e1` worktree build, and `C:\dev\PRIN\…` is
the post-fix build. Since S1.9 the generator also *derives* the label from the
imported build (it probes for the `guard` keyword the correction added) and
refuses to write a mislabelled artefact.

Mechanism attribution over H2a's 103 breaches, identical at both builds:
DV-007 alone 38; guard alone 33; DV-007 + guard 10; DV-007 + guard +
ill-conditioned 19; guard + ill-conditioned 3; unexplained **0**. Every H1
breach is DV-007 alone. All 33 H2a breaches at or above `1e-3` (by the E3
artefact's own magnitudes) are guard-sensitive.

## Regenerating

Both generators run from the repository root with the project venv. The
decomposition re-derives its label from the imported build, so the build
under test must be the one `import prin` resolves.

**Post-fix (postfix):**

```bash
# 1. the checkout is the post-fix build; rebuild the extension if the Rust
#    code changed since the last build:
maturin develop
# 2. decomposition:
python EVIDENCE/exp001-d1-s1/root_cause_decomposition.py --label postfix \
    --out EVIDENCE/exp001-d1-s1/root-cause-decomposition-postfix.json
# 3. exactness audit (runs against the committed decomposition JSON):
python EVIDENCE/exp001-d1-s1/dv007_exactness_audit.py \
    --decomposition EVIDENCE/exp001-d1-s1/root-cause-decomposition-postfix.json \
    --out EVIDENCE/exp001-d1-s1/dv007-exactness-audit.json
```

**Pre-fix (prefix):** the generator script did not exist at the reproduction
commit, so run the post-fix copy of the script from the post-fix checkout
while putting the pre-fix package first on `PYTHONPATH` (the script inserts
the checkout root at `sys.path[0]`, which serves `benchmarks`/`parity`;
`prin` itself resolves through `PYTHONPATH`):

```bash
git worktree add ../PRIN-prefix bd737e1
# build the pre-fix extension in the worktree (maturin develop against its
# own venv, or cargo build and place the .pyd under its python/prin/)
# then, from the post-fix checkout, with the prefix package FIRST:
PYTHONPATH="C:/dev/PRIN-prefix/python;C:/dev/PRIN" \
  python EVIDENCE/exp001-d1-s1/root_cause_decomposition.py --label prefix \
  --out EVIDENCE/exp001-d1-s1/root-cause-decomposition-prefix.json
```

The label probe (the pre-fix build has no `guard` keyword on its fixed-step
integrators) verifies that the import actually resolved to the pre-fix
build; a mismatch exits instead of writing a plausible artefact —
`git_head` alone cannot discriminate the two builds when the script is
newer than the build under test. The exactness audit runs against whichever
committed decomposition JSON it is pointed at, and records
`prin_extension`/`git_head` provenance in its payload.

A decomposition run whose `--label` does not match the imported build (the
pre-fix build has no `guard` keyword on its fixed-step integrators) exits
with an error instead of writing a plausible artefact — `git_head` alone
cannot discriminate the two builds when the script is newer than the build
under test.
