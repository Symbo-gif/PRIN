#!/usr/bin/env bash
# EXP-002 D1 S3 - static / quality / security / governance legs of the local gate
# (Coding Standards section 5, Plan amendment #48). Run from Git Bash at the
# repository root; legs run strictly one after another and never overlap pytest
# or cargo. Every leg prints its verbatim command, UTC start/end and exit code.
#
#   bash EVIDENCE/exp002-d1-s3/static_gate.sh
#
# Exit status is 0 only if every leg exited 0.
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

ROOTS=(python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/ EVIDENCE/exp002-d1-s1/ EVIDENCE/exp002-d1-s2/ EVIDENCE/exp002-d1-s3/)

echo "# EXP-002 D1 S3 - static gate"
echo "# git HEAD: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)   untracked: $(git status --porcelain | grep -c '^??')"
echo "# host: $(uname -srm)   $($PY -V 2>&1)   ruff $(.venv/Scripts/ruff.exe --version)   $(.venv/Scripts/mypy.exe --version)"

leg "ruff check over every first-party root and evidence dir" .venv/Scripts/ruff.exe check "${ROOTS[@]}"
leg "ruff format --check over the same roots" .venv/Scripts/ruff.exe format --check "${ROOTS[@]}"
leg "ruff format --check DOCS/experiments (source-only include)" .venv/Scripts/ruff.exe format --check DOCS/experiments/ --config "include = ['*.py', '*.pyi', '*.ipynb']"
leg "mypy python/prin --strict" .venv/Scripts/mypy.exe python/prin --strict
leg "mypy DOCS/experiments/ --strict" .venv/Scripts/mypy.exe DOCS/experiments/ --strict
leg "mypy --strict over every changed/new first-party file and the S1/S2/S3 instruments" .venv/Scripts/mypy.exe --strict   python/prin/reporting/figure_generation.py tests/test_publication_figure_arguments.py tests/test_notebooks.py   parity/test_parity_publication.py EVIDENCE/exp002-d1-s1/root_cause_decomposition.py   EVIDENCE/exp002-d1-s2/*.py EVIDENCE/exp002-d1-s3/*.py
leg "interrogate (floor 95%)" $PY -m interrogate -c pyproject.toml python/prin
leg "bandit python/prin DOCS/experiments" $PY -m bandit -r python/prin DOCS/experiments -c pyproject.toml
leg "bandit over the S1/S2/S3 evidence dirs" $PY -m bandit -r EVIDENCE/exp002-d1-s1 EVIDENCE/exp002-d1-s2 EVIDENCE/exp002-d1-s3 -c pyproject.toml
leg "check_global_session_registration.py" $PY tools/check_global_session_registration.py
leg "check_dv_register_gates.py" $PY tools/check_dv_register_gates.py
leg "check_skipif_probes.py" $PY tools/check_skipif_probes.py
leg "check_deviation_ledger.py 039 040 (report paths)" $PY tools/check_deviation_ledger.py DOCS/reports/039-project-state.md DOCS/reports/040-project-state.md

echo
echo "# overall: $overall (0 = every leg exited 0)"
exit "$overall"
