#!/usr/bin/env bash
# EXP-002 D1 S4 - static / quality / security / governance legs of the local gate
# (Coding Standards section 5, Plan amendment #48; supervised per Testing
# Standards section 7 / amendment #49).
#
#   bash EVIDENCE/exp002-d1-s4/static_gate.sh
#
# Adapted copy of S3's static_gate.sh: the evidence roots now include
# EVIDENCE/exp002-d1-s4/, and the deviation-ledger leg compares 040 -> 041.
# Run from Git Bash at the repository root; legs run strictly one after another
# and never overlap pytest or cargo. Every leg prints its verbatim command, UTC
# start/end and exit code.
#
# Exit status is 0 only if every leg exited 0. Aggregation is by direct rc
# capture, never by grepping a record (the EXP002D1-S4-F1 fail-open class).
cd "$(git rev-parse --show-toplevel)" || exit 2
export PATH="/c/Program Files/Git/bin:$PATH"
PY=.venv/Scripts/python.exe
overall=0
n=0

leg() {
  n=$((n + 1))
  local id
  id=$(printf 'L%02d' "$n")
  echo
  echo "## $id $1"
  shift
  echo "# command: $*"
  echo "# started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  "$@" 2>&1
  local rc=$?
  echo "# exit code: $rc"
  echo "# ended $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  [ "$rc" -eq 0 ] || overall=1
}

ROOTS=(python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/
       EVIDENCE/exp002-d1-s1/ EVIDENCE/exp002-d1-s2/ EVIDENCE/exp002-d1-s3/ EVIDENCE/exp002-d1-s4/)
FMTROOTS=(python/ tests/ benchmarks/ tools/ parity/
          EVIDENCE/exp002-d1-s1/ EVIDENCE/exp002-d1-s2/ EVIDENCE/exp002-d1-s3/ EVIDENCE/exp002-d1-s4/)

# mypy targets: the first-party files this correction cycle changed (S1-S3; S4
# changes no first-party source) plus every committed instrument in the four
# bundles. Built by expansion so a bundle with no .py file cannot pass a literal
# unmatched glob to mypy.
MYPY_TARGETS=(python/prin/reporting/figure_generation.py
              tests/test_publication_figure_arguments.py
              tests/test_notebooks.py
              parity/test_parity_publication.py)
for d in exp002-d1-s1 exp002-d1-s2 exp002-d1-s3 exp002-d1-s4; do
  for f in "EVIDENCE/$d"/*.py; do [ -f "$f" ] && MYPY_TARGETS+=("$f"); done
done

echo "# EXP-002 D1 S4 - static gate"
echo "# date (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "# git HEAD: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)   untracked: $(git status --porcelain | grep -c '^??')"
echo "# host: $(uname -srm)   $($PY -V 2>&1)   ruff $(.venv/Scripts/ruff.exe --version)   $(.venv/Scripts/mypy.exe --version)"
echo "# mypy target count: ${#MYPY_TARGETS[@]}"

leg "ruff check over every first-party root and the four evidence dirs" .venv/Scripts/ruff.exe check "${ROOTS[@]}"
# DOCS/experiments is format-checked separately (next leg) with the source-only include,
# as AGENTS.md documents: a plain `ruff format --check DOCS/experiments/` also formats the
# Markdown code blocks of the frozen experiment reports, which are not source.
leg "ruff format --check over the source roots" .venv/Scripts/ruff.exe format --check "${FMTROOTS[@]}"
leg "ruff format --check DOCS/experiments (source-only include)" .venv/Scripts/ruff.exe format --check DOCS/experiments/ --config "include = ['*.py', '*.pyi', '*.ipynb']"
leg "mypy python/prin --strict" .venv/Scripts/mypy.exe python/prin --strict
leg "mypy DOCS/experiments/ --strict" .venv/Scripts/mypy.exe DOCS/experiments/ --strict
leg "mypy --strict over the cycle's changed first-party files and every bundle instrument" .venv/Scripts/mypy.exe --strict "${MYPY_TARGETS[@]}"
leg "interrogate (floor 95%)" $PY -m interrogate -c pyproject.toml python/prin
leg "bandit python/prin DOCS/experiments" $PY -m bandit -r python/prin DOCS/experiments -c pyproject.toml
leg "bandit over the four evidence dirs" $PY -m bandit -r EVIDENCE/exp002-d1-s1 EVIDENCE/exp002-d1-s2 EVIDENCE/exp002-d1-s3 EVIDENCE/exp002-d1-s4 -c pyproject.toml
leg "check_global_session_registration.py" $PY tools/check_global_session_registration.py
leg "check_dv_register_gates.py" $PY tools/check_dv_register_gates.py
leg "check_skipif_probes.py" $PY tools/check_skipif_probes.py
leg "check_deviation_ledger.py 040 041 (report paths)" $PY tools/check_deviation_ledger.py DOCS/reports/040-project-state.md DOCS/reports/041-project-state.md

echo
echo "# overall: $overall (0 = every leg exited 0)"
exit "$overall"
