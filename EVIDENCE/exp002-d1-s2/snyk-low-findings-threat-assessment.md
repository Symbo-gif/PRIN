# EXP-002 D1 S2 — recorded threat assessment: two residual Snyk Code LOW `python/PT` findings

**Date:** 2026-10-15 UTC
**Recorded by:** S2 (EXP-002 D1 correction audit), under the maintainer's
in-session delegation to "make the call that follows established methodologies
and governance rigorously".
**Status:** ACCEPTED WITH ASSESSMENT — flagged for maintainer ratification.
**Tracked as:** audit finding `EXP002D1-S2-F8` (D4).
**Governing clauses:** Coding Standards §6.2 (Snyk Code gate = "0 medium+
findings"; recorded-threat-assessment pattern for items with no available fix),
§6.4 ("Findings are never suppressed, ignored, or excluded without evidence and
an approved deviation or amendment"; "remediates findings attributable to the
change, and rescans until the applicable gate is clean").

This assessment exists because §6.4 forbids dropping a finding silently. It is
**not** a suppression, an ignore entry, or a `.snyk` policy change: nothing was
excluded, and the findings remain visible in every scan recorded below.

---

## 1. The findings

Snyk Code (MCP integration, `mcp__snyk__snyk_code_scan`, `severity_threshold:
low`) over `C:\dev\PRIN\EVIDENCE\exp002-d1-s2` reports **2 findings**, both the
same rule:

| # | Rule | Severity | CWE | File | Line |
|---|---|---|---|---|---|
| 1 | `python/PT` "Path Traversal" | **Low** | CWE-23 | `EVIDENCE/exp002-d1-s2/changed_line_coverage.py` | 98 |
| 2 | `python/PT` "Path Traversal" | **Low** | CWE-23 | `EVIDENCE/exp002-d1-s2/decomposition_rerun_check.py` | 92 |

Message (both): *"Path Traversal: Unsanitized input from a command line
argument flows into `pathlib.Path`, where it is …"*

Both files are **S2's own audit instruments**, added by this session. They are
not shipped code: `EVIDENCE/` is not part of the `prin` package, is not
installed, is not imported by any library or test, and is not reachable from
any public API. They are read-only analysis tools invoked manually from a shell
by the auditor.

## 2. Affected API and data flow

Source: `sys.argv[1]` → `main(argv)` → `guarded_input_path(argv[0], role)` →
`candidate = Path(raw)`.

Sinks reached after the guard: `Path.is_file()`, `Path.read_bytes()`,
`Path.read_text()` — all **read-only**. Neither instrument writes, deletes,
renames, or executes anything derived from the argument. `changed_line_coverage.py`
additionally passes a *separate* argv element (`base_ref`) to a fixed-argv
`git diff` call, and `Path` is not used to construct that command.

## 3. Exploit prerequisites

For this to be exploitable, an attacker must already be able to **supply
command-line arguments to a process running as the auditor**. That is equivalent
to already having arbitrary code execution as that user on that workstation —
at which point the attacker can read any file the user can read directly, and
the instrument confers no additional capability.

There is therefore **no privilege boundary crossed**:

- no network input, no deserialized payload, no request parameter;
- no elevation — the tool runs with the invoking user's own permissions;
- no confidentiality gain — it can only read what the invoker could already read;
- no integrity gain — it writes nothing but its own stdout, which the calling
  shell redirects.

This is the standard false-positive shape for CLI developer tooling under
taint analysis.

## 4. Why it is nonetheless treated as worth a real control

The repository has an audited precedent for taking this class seriously, and for
a reason that is **not** confidentiality. Finding `PR23-F1` (D2, PR #23) was
`tools/reproduce.py::verify_manifest`/`append_manifest` following symbolic
links, so a symlinked `manifest.json` or artefact "verified clean" — *content*
integrity was checked while *path provenance* was not (CWE-59). It was fixed
with no-follow `_reject_symlink` / `_reject_non_regular` guards and five
regression tests.

S2's instruments are **evidence-producing verification tools**, so the same
failure mode applies with the same consequence: a symlinked input would be
compared while the evidence file named a different path, silently producing
false audit evidence. That is an integrity risk to the audit record itself, and
it is real even though the CWE-23 confidentiality framing is not.

## 5. Remediation performed (two iterations, both retained)

A guard `guarded_input_path()` was added to **both** instruments, mirroring the
`tools/reproduce.py` discipline:

1. reject any input containing a `..` path component (string-level, before
   `Path` construction);
2. **no-follow** symlink refusal (`Path.is_symlink()` before any
   link-following call);
3. refuse anything that exists but is not a regular file (directory/FIFO/special);
4. **resolve** the path and confine it to an explicit allowlist — the repository
   root, the platform temporary root, and `PRIN_S2_SCRATCH` when set — so a
   symlinked *parent* directory pointing outside is also refused;
5. re-check regular-file status on the resolved path;
6. record the **resolved absolute path and its SHA-256** in the evidence output,
   so each artefact is tied to the exact bytes measured (provenance, matching
   how S1's artefacts record `port_module_sha256`).

**Iteration 1** implemented (2)–(6). Rescan: still 2 findings, with the dataflow
now tracing *through* the guard (positions added at lines 72/97 and 66/91).
**Iteration 2** added the canonical `..` string check (1). Rescan: still 2
findings, dataflow unchanged in shape, now pointing at line 97→98 and 91→92 —
i.e. at `candidate = Path(raw)` *inside* the guard itself.

**Conclusion:** Snyk's `python/PT` model treats the `pathlib.Path` construction
as the sink and does not recognise `..`-rejection, `is_symlink()`,
`is_file()` or resolve-and-contain as sanitizers. No further code change
available to this session clears the finding without removing the tool's
ability to read the scratch artefact at all — which the S2 brief explicitly
requires ("`--out <scratch path outside the repo>`").

## 6. Proof the guard is not vacuous

[`path-guard-negative-tests.txt`](path-guard-negative-tests.txt) exercises both
instruments and records, for each:

| Case | Expected | Observed |
|---|---|---|
| path outside every allowed root | refuse | **REFUSED** (`is outside the allowed roots (…)`) |
| a directory, not a regular file | refuse | **REFUSED** (`is not a regular file`) |
| a `..` traversal component | refuse | **REFUSED** (`refusing a path containing a '..' component`) |
| a symbolic link to a real artefact | refuse | **REFUSED** (`refusing symbolic link …`) |
| positive control: a legitimate in-repo artefact | accept | **ACCEPTED** |
| the declared `PRIN_S2_SCRATCH` file | accept | **ACCEPTED** |

`guard negative-test failures: 0`, exit 0. The symlink case was exercisable on
this host (creation succeeded), so it is proven rather than assumed.

## 7. Compensating controls

- **Gate status:** the applicable §6.2 Snyk Code gate is **"0 medium+
  findings"**. Repo-wide scan at `severity_threshold: medium` returns
  `issueCount: 0`. The gate is **met**.
- Both findings are **Low**, in **non-shipped** audit tooling under `EVIDENCE/`.
- Read-only sinks; no write, delete, rename or execute path.
- The guard above, with negative-test proof.
- `bandit -r EVIDENCE/exp002-d1-s1 EVIDENCE/exp002-d1-s2 -c pyproject.toml` →
  **0 issues at every severity** (bandit does not report this dataflow).
- `ruff check` (including the `S` bandit rule set) and `ruff format --check` →
  clean; `mypy --strict` over all six instruments → clean.
- The instruments are invoked from recorded shell commands in this evidence
  directory, so every path actually used is on the record and auditable.
- Nothing was added to `.snyk`, no ignore or severity exclusion was created, and
  no scan was skipped.

## 8. Disposition

**ACCEPTED WITH ASSESSMENT**, as a **D4** finding (`EXP002D1-S2-F8`), on the
grounds that: the applicable medium+ gate is clean; the residual is Low severity
in non-shipped audit tooling; no privilege boundary is crossed; a genuine
integrity control was implemented and proven by negative tests; and the scanner
does not model that control.

**Flagged for maintainer ratification.** The maintainer delegated this call
in-session; per Coding Standards §6.2 the recorded-threat-assessment route
contemplates maintainer approval, so this is presented as a flagged default
rather than a settled exemption. If the maintainer prefers the findings cleared
over the tool's ability to read an out-of-tree scratch artefact, the alternative
is to have each instrument read only from inside the repository or the platform
temp root, and to move the scratch location accordingly — a usability change to
the documented regeneration workflow, not a security improvement.

**Re-check:** at S3's delta re-audit and again at S4's full gate, since §6.2
requires accepted items to stay visible and be re-checked every cycle.

## 9. Scan provenance

| Scan | Scope | Threshold | Result |
|---|---|---|---|
| MCP `snyk_code_scan` | `C:\dev\PRIN\EVIDENCE\exp002-d1-s2` | `low` | `issueCount: 2` (before remediation) |
| MCP `snyk_code_scan` | `C:\dev\PRIN` | `medium` | `issueCount: 0` |
| MCP `snyk_code_scan` | `C:\dev\PRIN\EVIDENCE\exp002-d1-s2` | `low` | `issueCount: 2` (after iteration 1) |
| MCP `snyk_code_scan` | `C:\dev\PRIN\EVIDENCE\exp002-d1-s2` | `low` | `issueCount: 2` (after iteration 2) |

Route: the Snyk **MCP** integration, which Coding Standards §6.4 expressly
permits ("through the configured IDE or MCP integration"). The **CLI** route was
**BLOCKED** this session — `snyk code test . --severity-threshold=low
--sarif-file-output=…` returned `401 Unauthorized` / `SNYK-0005` with no SARIF,
because the local token has expired and `snyk auth` requires an interactive
browser login by the maintainer. That is recorded as blocked and never as
passed (finding `EXP002D1-S2-F3`, Plan amendment #48 item 2).
