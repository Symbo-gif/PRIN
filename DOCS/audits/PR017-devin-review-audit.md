# PRIN Audit Report — PR #17 External Code Review (devin-ai-integration)

**Date:** 2026-09-18
**Auditor:** Claude Sonnet 5 (AI pair), independently re-verifying findings from
the `devin-ai-integration[bot]` automated review — not a formal Work Package;
`tools/code-intelligence/` is deliberately outside the Session Cycle/WP process
(see its `CHANGELOG.md` entry and `DOCS/devtools/visualization-mcp-security.md`).
This report follows `DOCS/audits/TEMPLATE_Audit_Report.md` and the severity
scale of `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §5
because no dedicated governance document yet exists for external-bot PR
findings; it is the pattern to reuse for future occurrences of this event
class.
**Scope:** `tools/code-intelligence/ci_indexer/python_adapter.py` (call-graph
extraction), `tools/code-intelligence/ci_telemetry/summary.py` +
`tools/code-intelligence/ci_graph/store.py` (runtime-telemetry statistics) —
both introduced in commit `6006b41` (this PR, unmerged).
**Trigger:** GitHub PR #17 (`docs/era-001-readability-audit` → `main`),
`devin-ai-integration[bot]` automated review, 2 findings (`BUG_pr-review-job-
5059355a53254dd2b4b31bd0d08a82cb_0001`, `..._0002`), both `kind: bug`.
**Active brief:** ad hoc governance/remediation session, no session-brief file
(pre-Phase-7 PR gate, not a WP session).
**Git state:** `docs/era-001-readability-audit` @ `aecd61b6` (pre-remediation);
remediation commit follows.
**Verdict:** `PASS-WITH-FINDINGS` → remediated to **`PASS`** (see §7).

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| Independent reproduction of both devin findings | ✅ | Both confirmed genuine by direct code reading and a minimal failing-test reproduction (§2, §3). |
| False positives | ✅ (none) | Neither finding was a false positive; no dismissed items. |
| Severity classification | ✅ | Both classified `D2` — incorrect output from the subsystem's own core function, no D1 (no PRIN core math/architecture/security/reproducibility guarantee is touched; this is devtools-only). |
| Regression tests | ✅ | 2 new tests added, confirmed to fail against pre-fix source and pass against the fix (§3, evidence below). |
| Quality gates | ✅ | `ruff check` / `ruff format --check` / `mypy --strict` clean on all touched files; full subsystem suite 64/64 passing. |
| Security (Coding Standards §6) | ✅ | Snyk Code: 0 issues on `tools/code-intelligence`. No dependency manifest changed by this remediation, so Snyk Open Source / `pip-audit` deltas are N/A; `pip-audit --local` run anyway as a compensating check — only pre-existing, non-attributable `pip`/`setuptools` environment-tooling advisories (documented drift, see §2). GitHub secret scanning/push protection remain in force independently at push time. |
| Changed-code coverage | ✅ | Every touched line in `python_adapter.py`, `store.py`, `summary.py` is exercised by the new/existing tests (§2); whole-file percentages below 95% are pre-existing, out-of-scope lines, not the changed diff. |
| Documentation/artefact trail | ✅ | This report, `CHANGELOG.md` `[Unreleased]` entry, `DOCS/audits/README.md` index entry (this session). |

## 2. Methodology

Both findings were re-derived independently from the repository, not taken on
the bot's assertion:

1. Read `tools/code-intelligence/ci_indexer/python_adapter.py` in full and
   traced the `ast.walk` call graph by hand for a class with two methods
   calling a shared helper.
2. Read `tools/code-intelligence/ci_telemetry/summary.py` and
   `ci_graph/store.py::spans_by_operation`/`spans_for_operation` in full and
   traced the populations each draws from.
3. Reproduced each bug with a standalone script before touching any fix, then
   converted each into a permanent regression test.
4. Applied the minimal fix devin's "Recommended fix" pointed at, re-verified
   by temporarily restoring the pre-fix source (via `git show HEAD:<path>`)
   against the *new* tests to confirm they fail pre-fix and pass post-fix —
   proof the tests actually pin the bug rather than passing vacuously.
5. Ran the full local gate.

```bash
# Full subsystem suite, post-fix
$ python -m pytest tools/code-intelligence/tests/ -v
============================= test session starts =============================
collected 64 items
...
============================= 64 passed in 2.24s ==============================

# Lint / format / types on every touched file
$ python -m ruff check ci_indexer/python_adapter.py ci_graph/store.py \
    ci_telemetry/summary.py tests/test_indexer.py tests/test_telemetry.py
All checks passed!
$ python -m ruff format --check <same files>
5 files already formatted
$ python -m mypy --strict ci_indexer/python_adapter.py ci_graph/store.py \
    ci_telemetry/summary.py tests/test_indexer.py tests/test_telemetry.py
Success: no issues found in 5 source files

# Changed-code coverage (whole-file numbers include pre-existing untouched
# lines; the "Missing" ranges below do not include any line this session
# changed)
$ python -m pytest tools/code-intelligence/tests/ \
    --cov=ci_indexer.python_adapter --cov=ci_graph.store --cov=ci_telemetry.summary \
    --cov-report=term-missing -q
ci_graph\store.py                145     17    88%   103-104, 251-252, 307-308, 310-311, 390-392, 434-436, 485, 569, 583
ci_indexer\python_adapter.py      72     14    81%   43-48, 75-76, 94, 206, 212-219
ci_telemetry\summary.py           43      5    88%   44, 51, 116-118

# Security: Snyk Code on the touched subsystem
$ snyk code test tools/code-intelligence
Total issues:   0

# Security: pip-audit compensating check (no dependency manifest changed)
$ pip-audit --local   # run from tools/code-intelligence/
Found 16 known vulnerabilities in 2 packages: pip 25.2, setuptools 78.1.0
  (pre-existing environment tooling, not a dependency this remediation
  touched; consistent with the drift already documented in
  DOCS/devtools/visualization-mcp-security.md and session memory for this
  subsystem — not attributable to this change, not remediable from this
  scope without touching the governed torch pin)
```

Pre-fix vs. post-fix regression proof (findings substituted back to
pre-remediation source, new tests run in isolation):

```
tests\test_indexer.py::test_class_method_calls_are_not_double_attributed_to_the_class FAILED
  AssertionError: assert not [PendingCall(src_id='python:foo.py::Foo', callee_name='helper', line=3),
                               PendingCall(src_id='python:foo.py::Foo', callee_name='helper', line=5)]
tests\test_telemetry.py::test_error_rate_never_exceeds_one_under_a_tight_global_limit FAILED
  AssertionError: assert 5 == 0
   +  where 5 = OperationStats(operation_name='cli.rare', count=1, ..., error_count=5, error_rate=5.0).error_count
```

Both tests pass cleanly against the fixed source (§ full-suite run above).

## 3. Detailed findings

### 3.1 PR017-F1 — Class nodes absorb all calls made inside their methods

`tools/code-intelligence/ci_indexer/python_adapter.py:132-141` (pre-fix). For
a `ClassDef`, `_walk_statement` recurses into every member (line 132-140),
which for each `FunctionDef`/`AsyncFunctionDef` member independently calls
`_collect_calls(stmt, func_id, out)` (line 175) — this already records every
call made in that method's body against the method node, correctly. The
class-level call `_collect_calls(stmt, class_id, out)` on line 141 then
`ast.walk`s the *entire class subtree again*, including every method body
already covered above, re-attributing each of those calls to the class node
as well.

Consequence, confirmed by direct trace and reproduced in a test: a class
`Foo` with methods `a` and `b` each calling `helper()` produces the correct
`method Foo.a -> helper` and `method Foo.b -> helper` edges, plus two spurious
`class Foo -> helper` edges, and `helper`'s `call_site_frequency` in the
orchestrator (`tools/code-intelligence/ci_indexer/orchestrator.py:345-351`)
is inflated from 2 to 4. Since `_MAX_CALL_SITE_OCCURRENCES_FOR_RESOLUTION`
caps resolution at 30 occurrences, a name near that threshold can be pushed
over it purely by this double-count and have its (otherwise valid) `CALLS`
edges silently dropped — a correctness bug in the tool's core deliverable
(an accurate code knowledge graph), not merely a cosmetic one.

**Fix:** narrow class-level call collection to direct, non-definition
class-body statements only (matching devin's recommended fix), so methods
and nested classes — which already collect their own calls via the existing
recursion — are excluded from the class-level walk:

```python
for member in stmt.body:
    _walk_statement(member, file_node_id, repo_path, content_hash, out,
                     scope_prefix=f"{qualified}.")
    if not isinstance(
        member, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    ):
        _collect_calls(member, class_id, out)
```

The prior standalone `_collect_calls(stmt, class_id, out)` call is removed.
Class-body-level calls (e.g. `x = default_factory()` directly in the class
body, not inside a method) remain correctly attributed to the class node —
covered by a dedicated regression test so the narrowing does not silently
regress that case.

### 3.2 PR017-F2 — Runtime error rate can exceed 100%

`tools/code-intelligence/ci_telemetry/summary.py:90-98` (pre-fix) computed
`count` (in `operation_stats`) from `store.spans_by_operation(limit=limit)` —
a *globally* bounded, most-recent-first sample (the `LIMIT` in
`ci_graph/store.py:530-534` applies before grouping by operation, not per
operation, despite the pre-fix docstring's claim of "per operation") — while
`_error_counts` computed `error_count` from `store.spans_for_operation(op)`,
which is unbounded and returns *every* span ever ingested for that operation.
Once total spans exceed the global limit, an operation can have a small
`count` (its share of the bounded recent window) but a large `error_count`
(its all-time error history), so `error_rate = error_count / count` can
exceed `1.0` and `error_count` can exceed `count` — violating
`OperationStats`'s own documented contract (`error_rate` = `error_count /
count`). Reproduced exactly: with 5 historical errors for an operation pushed
out of an 11-span global window by a flood of a different operation, the
pre-fix code reported `count=1, error_count=5, error_rate=5.0`.

**Fix:** compute duration and status from the *same* bounded query rather
than two differently-bounded populations (devin's recommended fix).
`GraphStore.spans_by_operation` now selects `(operation_name, duration_ms,
status)` together and returns `dict[str, list[tuple[float, str]]]`;
`operation_stats` derives both `count`/percentiles and `error_count` from the
same per-operation list, so `error_count <= count` and `error_rate <= 1.0`
are now structural invariants, not merely likely outcomes. The now-unused
`_error_counts` helper (and its `sqlite3` import) is removed. The
`spans_by_operation` docstring is corrected to describe the limit as global
(across all operations, before grouping), not per-operation, so a future
reader cannot rebuild the same bug from a doc that already misdescribed the
old behavior. `spans_by_operation` has exactly one other call site
(`operation_stats` itself); `spans_for_operation` (unbounded, used
separately by `ci_mcp_server/tools.py:751` for full single-operation trace
lookups) is untouched — its unbounded semantics are correct for that
distinct use case and not implicated in this finding.

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| PR017-F1 | D2 | `ci_indexer/python_adapter.py:141` (pre-fix) | Class-level call collection re-walks every method body already covered by the method's own collection, double-recording calls against the class and inflating `call_site_frequency` enough to drop real `CALLS` edges past the 30-occurrence resolution cap. | Coding Standards §1 "one algorithm, one implementation" (a call site must be attributed exactly once); the tool's own documented purpose (`ci_graph/README.md`/module docstring: an accurate code knowledge graph). | Narrow the class-level walk to direct, non-definition class-body statements only. |
| PR017-F2 | D2 | `ci_telemetry/summary.py:90-98` (pre-fix) | `error_count` (unbounded, all-time) and `count` (globally bounded, recent) are drawn from different populations, letting `error_rate` exceed `1.0` and violate the `OperationStats` docstring contract. | `OperationStats` dataclass's own documented contract (`error_rate: error_count / count`); Coding Standards §6 correctness expectations for shipped telemetry surfaced via CLI/MCP tools. | Derive `count` and `error_count` from one bounded query so they describe the same sample. |

## 5. Deviation-ledger delta

New findings added: `PR017-F1`, `PR017-F2` (both `D2`, both closed in this
same session — see §7). No prior deviation-ledger entries touch these files
(`tools/code-intelligence/` was introduced whole-cloth in commit `6006b41`,
its own S1-equivalent session, and has had no prior audit). No carried
findings existed to re-inspect.

## 6. Verdict and required actions

`PASS-WITH-FINDINGS`: two `D2` findings, zero `D1`, both independently
reproduced and confirmed genuine (not false positives), neither touching
PRIN's mathematical/architectural/security/reproducibility core — the
governed WP/Session-Cycle subsystem is unaffected; both are confined to the
opt-in `tools/code-intelligence/` devtools add-on. Per Development Workflow
and Audit Standards §5 (D2 severity), required response is "Fix in
remediation step before audit session closure" — done in this same session
(§7), consistent with this event class not having a separate multi-day
S2→S3 gap (a pre-merge PR review gate, not an in-flight WP).

## 7. Closure table (remediation, same session)

| ID | Resolution | Commit / evidence | Delta re-audit evidence |
|---|---|---|---|
| PR017-F1 | FIXED | `python_adapter.py` narrowed class-level call collection; regression tests `test_class_method_calls_are_not_double_attributed_to_the_class` + `test_class_body_level_calls_are_still_attributed_to_the_class` in `tests/test_indexer.py` | Test fails on pre-fix source (`assert not class_calls` → 2 spurious `class Foo -> helper` calls), passes on fixed source; full suite 64/64; ruff/mypy clean. |
| PR017-F2 | FIXED | `store.py::spans_by_operation` now returns bounded `(duration, status)` pairs; `summary.py::operation_stats` derives `count`/`error_count` from the same sample, `_error_counts` removed | Test fails on pre-fix source (`error_count=5, error_rate=5.0` against `count=1`), passes on fixed source (`error_count=0`); full suite 64/64; ruff/mypy clean. |

**Delta re-audit date:** 2026-09-18 — **Result:** CLEAN (both findings
FIXED, zero carried forward, full local gate green, Snyk Code 0 issues).
