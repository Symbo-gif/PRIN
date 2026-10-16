#!/usr/bin/env bash
# EXP-002 D1 S3 - the long legs of the closing local gate (Plan amendment #48).
#
#   bash EVIDENCE/exp002-d1-s3/closing_gate.sh
#
# Runs strictly one leg after another (pytest is never concurrent with cargo or
# with another pytest on this host) on the tree it is started on, and refuses to
# start unless the tracked tree is clean. Output goes OUTSIDE the repository, to
# ~/prin-s3-scratch/gate/, and is copied into the evidence bundle afterwards:
#
#   fast-suite/   the required fast invocation, via diagnostic_suite_run.sh
#   full-suite/   the required full invocation, via diagnostic_suite_run.sh
#                 (no diagnostic plugin: the shipped per-notebook bounds apply)
#   legs.txt      every other leg, each with its verbatim command, UTC times and
#                 exit status: targeted coverage and the changed-line analysis,
#                 cargo fmt / clippy / test, the from-scratch Sphinx build, and
#                 gitleaks over the full history and --staged.
#
# The cheap legs that must be repeated on the final documentation commit (static
# gate, Snyk, immutability, manifests, delta re-audit, index checks) are in
# final_legs.sh.
#
# Exit status: 0 only if both suites and every other leg exited 0; 1 otherwise.
# Every leg's own exit code is in legs.txt either way. (The aggregated status was
# added after the run recorded in gate/closing-gate-legs.txt, on cold-review round
# 4's finding that the script always exited 0; no recorded line changed.)
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
export PATH="/c/Program Files/Git/bin:$PATH"
PY=.venv/Scripts/python.exe
OUT="$HOME/prin-s3-scratch/gate"
mkdir -p "$OUT"
LEGS="$OUT/legs.txt"
overall=0
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked tree is not clean; refusing to start"; exit 2; }
GITLEAKS=DOCS/test_and_benchmark_results/ea007/full-gate/.tools/gitleaks/bin/gitleaks.exe

stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
{
  echo "# EXP-002 D1 S3 - closing gate, long legs"
  echo "# date (UTC): $(stamp)"
  echo "# git HEAD: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)   untracked: $(git status --porcelain | grep -c '^??')"
  echo "# host: $(uname -srm)   $($PY -V 2>&1)   pytest $($PY -m pytest --version 2>&1 | tr -d '\r')"
  echo "# rustc: $(rustc --version 2>&1)   cargo: $(cargo --version 2>&1)   gitleaks: $($GITLEAKS version 2>&1 | head -1)"
} > "$LEGS"

leg() {
  local title="$1"; shift
  {
    echo
    echo "## $title"
    echo "# command: $*"
    echo "# started $(stamp)"
  } >> "$LEGS"
  "$@" >> "$LEGS" 2>&1
  local rc=$?
  { echo "# exit code: $rc"; echo "# ended $(stamp)"; } >> "$LEGS"
  return "$rc"
}

# 1. required fast suite (observed by the sampler; no diagnostic plugin)
rm -rf "$HOME/prin-s3-scratch/gate-fast" "$HOME/prin-s3-scratch/gate-full"
bash EVIDENCE/exp002-d1-s3/diagnostic_suite_run.sh gate-fast tests/ -m "not slow and not gpu"
rc=$?; echo "fast suite exit: $rc" >> "$LEGS"; [ "$rc" -eq 0 ] || overall=1

# 2. required full suite
bash EVIDENCE/exp002-d1-s3/diagnostic_suite_run.sh gate-full tests/ parity/
rc=$?; echo "full suite exit: $rc" >> "$LEGS"; [ "$rc" -eq 0 ] || overall=1

# 3. targeted coverage (path form: the module form fails on this host, DV-033) and
#    the changed-line analysis against both the cycle base and the S3 base
COV="$(cygpath -m "${TEMP:-/tmp}")/prin-s3-coverage.json"
leg "targeted coverage run (path form)" $PY -m pytest tests/test_publication_figure_arguments.py tests/test_publication_generation.py parity/test_parity_publication.py --cov=python/prin/reporting "--cov-report=json:$COV" --cov-report=term-missing --basetemp=.pytest_basetemp -p no:cacheprovider || overall=1
leg "changed-line coverage against the S3 base 5ba0129e" env PYTHONIOENCODING=utf-8 $PY EVIDENCE/exp002-d1-s2/changed_line_coverage.py "$COV" 5ba0129e python/prin/reporting/figure_generation.py || overall=1
leg "changed-line coverage against the cycle base fd8854ed" env PYTHONIOENCODING=utf-8 $PY EVIDENCE/exp002-d1-s2/changed_line_coverage.py "$COV" fd8854ed python/prin/reporting/figure_generation.py || overall=1

# 4. Rust legs, sequential, after pytest has finished
leg "cargo fmt --all -- --check" cargo fmt --all -- --check || overall=1
leg "cargo clippy --workspace --all-targets -- -D warnings" cargo clippy --workspace --all-targets -- -D warnings || overall=1
if ! leg "cargo test --workspace (attempt 1)" cargo test --workspace; then
  echo "# attempt 1 failed; the documented Windows contention class is os error 32 / LNK1104. Retrying once, both attempts recorded." >> "$LEGS"
  leg "cargo test --workspace (attempt 2)" cargo test --workspace || overall=1
fi

# 5. Sphinx from a deleted _build (incremental builds mask autodoc warnings)
rm -rf DOCS/sphinx/_build
leg "sphinx -W --keep-going -b html (from a deleted _build)" $PY -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html || overall=1

# 6. secret scans with the pinned binary
leg "gitleaks, full history" $GITLEAKS git . --no-banner || overall=1
leg "gitleaks, --staged" $GITLEAKS git . --staged --no-banner || overall=1

echo >> "$LEGS"
echo "# all long legs finished $(stamp)" >> "$LEGS"
echo "# git HEAD at end: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)   untracked: $(git status --porcelain | grep -c '^??')" >> "$LEGS"
echo "# overall: $overall (0 = every leg exited 0)" >> "$LEGS"
exit "$overall"
