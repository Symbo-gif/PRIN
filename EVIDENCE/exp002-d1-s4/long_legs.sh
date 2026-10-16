#!/usr/bin/env bash
# EXP-002 D1 S4 - the long legs of the closing local gate (Plan amendment #48;
# supervised per Testing Standards section 7 / amendment #49).
#
#   bash EVIDENCE/exp002-d1-s4/long_legs.sh <base-rev>
#
# <base-rev> is the S3 head this cycle's S4 work sits on (6b55c6ba). The script
# FIRST records the change set by file kind, because section 5 of the S4 session
# prompt makes three legs conditional and the condition must be measured, not
# assumed:
#   - cargo fmt/clippy/test         only if Rust changed
#   - cargo audit / pip-audit / Snyk Open Source   only if a dependency manifest changed
#   - per-change Python coverage    only if first-party Python changed
# It then runs the two required suites, strictly one after another (pytest is
# never concurrent with cargo or with another pytest on this host), and refuses
# to start unless the tracked tree is clean.
#
# Output goes OUTSIDE the repository, to ~/prin-s4-scratch/gate/, and is copied
# into the bundle afterwards by collect_final.sh:
#   change-set.txt  the measured change set and which conditional legs it triggers
#   legs.txt        the suite legs, each with verbatim command, UTC times, exit code
#   fast/ full/     per-suite console.log, samples.jsonl and run.txt (suite_run.sh)
#
# Exit status: 0 only if both suites exited 0; 1 otherwise. Every leg's own exit
# code is in legs.txt either way. Aggregation is by direct rc capture, never by
# grepping a record (the EXP002D1-S4-F1 fail-open class).
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
BASE=$(git rev-parse --verify --quiet "${1:?usage: long_legs.sh <base-rev>}^{commit}") || { echo "not a commit: $1"; exit 2; }
export PATH="/c/Program Files/Git/bin:$PATH"
PY=.venv/Scripts/python.exe
OUT="$HOME/prin-s4-scratch/gate"
mkdir -p "$OUT"
LEGS="$OUT/legs.txt"
overall=0
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked tree is not clean; refusing to start"; exit 2; }

stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }

# ---------------------------------------------------------------- change set
{
  echo "# EXP-002 D1 S4 - measured change set, $BASE..HEAD"
  echo "# date (UTC): $(stamp)"
  echo "# git HEAD: $(git rev-parse HEAD)"
  echo "# host: $(uname -srm)   $($PY -V 2>&1)   pytest $($PY -m pytest --version 2>&1 | tr -d '\r')"
  echo
  echo "## every path changed in this range"
  git diff --numstat "$BASE..HEAD" | awk '{printf "  +%-6s -%-6s %s\n",$1,$2,$3}'
  echo "  total files changed: $(git diff --name-only "$BASE..HEAD" | wc -l)"
  echo
  echo "## by kind (this decides which conditional legs apply)"
  rust=$(git diff --name-only "$BASE..HEAD" | grep -cE '\.rs$|^Cargo\.toml$|(^|/)Cargo\.lock$|\.toml$' || true)
  rustsrc=$(git diff --name-only "$BASE..HEAD" | grep -cE '\.rs$' || true)
  manifest=$(git diff --name-only "$BASE..HEAD" | grep -cE '^Cargo\.toml$|^Cargo\.lock$|^pyproject\.toml$|(^|/)Cargo\.toml$|requirements.*\.txt$' || true)
  pysrc=$(git diff --name-only "$BASE..HEAD" | grep -E '\.py$' | grep -cvE '^EVIDENCE/|^DOCS/experiments/' || true)
  pyany=$(git diff --name-only "$BASE..HEAD" | grep -cE '\.py$' || true)
  wf=$(git diff --name-only "$BASE..HEAD" | grep -cE '^\.github/' || true)
  echo "  Rust sources (.rs)                                  : $rustsrc"
  echo "  dependency manifests (Cargo.toml/lock, pyproject,   : $manifest"
  echo "    *requirements.txt)"
  echo "  first-party Python (outside EVIDENCE/ and           : $pysrc"
  echo "    DOCS/experiments/)"
  echo "  any Python (.py)                                    : $pyany"
  echo "  .github/ workflow files                             : $wf"
  echo
  echo "## conditional-leg decisions, from the counts above"
  echo "  cargo fmt / clippy / test        : $([ "$rustsrc" -eq 0 ] && echo 'NOT RUN - no Rust source changed' || echo 'REQUIRED')"
  echo "  cargo audit / pip-audit / Snyk OS: $([ "$manifest" -eq 0 ] && echo 'NOT RUN - no dependency manifest changed' || echo 'REQUIRED')"
  echo "  per-change Python coverage       : $([ "$pysrc" -eq 0 ] && echo 'NOT RUN - no first-party Python changed, so there are no changed executable lines to cover' || echo 'REQUIRED')"
  echo "  Snyk Code CLI                    : REQUIRED - run unconditionally in final_legs.sh (Coding Standards 6.2; cheap, and it also re-checks the three ratified python/PT locations)"
  echo "  Sphinx / gitleaks / governance   : REQUIRED - documentation and evidence changed"
  echo
  echo "## the Python files changed, listed explicitly so the coverage decision is checkable"
  git diff --name-only "$BASE..HEAD" | grep -E '\.py$' | sed 's/^/  /' || echo "  (none)"
} > "$OUT/change-set.txt" 2>&1
cat "$OUT/change-set.txt"

{
  echo "# EXP-002 D1 S4 - closing gate, long legs"
  echo "# date (UTC): $(stamp)"
  echo "# git HEAD: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)   untracked: $(git status --porcelain | grep -c '^??')"
  echo "# base: $BASE"
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

# 1. required fast suite (must be a clean single pass)
rm -rf "$HOME/prin-s4-scratch/fast" "$HOME/prin-s4-scratch/full"
bash EVIDENCE/exp002-d1-s4/suite_run.sh fast tests/ -m "not slow and not gpu"
rc=$?; echo "fast suite exit: $rc" >> "$LEGS"; [ "$rc" -eq 0 ] || overall=1

# 2. required full suite, ONCE, recorded at its actual exit status.
#    No rerun-until-green: O-1's disposition forbids it (Testing Standards 7 item 6).
bash EVIDENCE/exp002-d1-s4/suite_run.sh full tests/ parity/
rc=$?; echo "full suite exit: $rc" >> "$LEGS"; [ "$rc" -eq 0 ] || overall=1

echo >> "$LEGS"
echo "# all long legs finished $(stamp)" >> "$LEGS"
echo "# git HEAD at end: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)   untracked: $(git status --porcelain | grep -c '^??')" >> "$LEGS"
echo "# overall: $overall (0 = both suites exited 0)" >> "$LEGS"
echo "long legs overall: $overall"
exit "$overall"
