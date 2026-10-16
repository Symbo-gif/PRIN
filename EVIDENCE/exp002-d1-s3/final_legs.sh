#!/usr/bin/env bash
# EXP-002 D1 S3 - the cheap closing legs, run on the FINAL documentation commit.
#
#   bash EVIDENCE/exp002-d1-s3/final_legs.sh
#
# These legs are repeated on the last commit because they are sensitive to the
# documentation and evidence that is still being written when the long legs
# (closing_gate.sh) run: the static / quality / security / governance gate, the
# Snyk Code CLI scan, the immutability diffs, the manifest verification, the delta
# re-audit, the index self-checks of the three bundles, the from-scratch Sphinx
# build, gitleaks, and the state of draft PR #34. They run one after another and
# never overlap pytest or cargo. Output goes OUTSIDE the repository, to
# ~/prin-s3-scratch/final/ (override with FINAL_LEGS_OUT, used only to test the
# script's exit status), and is copied into the bundle afterwards by
# collect_final.sh. Exit status: 0 only if every leg exited 0 and the Snyk leg
# actually ran; a Snyk leg with no SARIF is BLOCKED and gives exit 1.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
export PATH="/c/Program Files/Git/bin:$PATH"
PY=.venv/Scripts/python.exe
OUT="${FINAL_LEGS_OUT:-$HOME/prin-s3-scratch/final}"
mkdir -p "$OUT"
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked tree is not clean; refusing to start"; exit 2; }
GITLEAKS=DOCS/test_and_benchmark_results/ea007/full-gate/.tools/gitleaks/bin/gitleaks.exe
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
HEAD_SHA=$(git rev-parse HEAD)
overall=0

hdr() { echo "# $1"; echo "# date (UTC): $(stamp)"; echo "# git HEAD: $HEAD_SHA   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)"; echo; }

# 1. static / quality / security / governance
bash EVIDENCE/exp002-d1-s3/static_gate.sh > "$OUT/static-gate.txt" 2>&1; rc=$?; [ "$rc" -eq 0 ] || overall=1
echo "static gate exit: $rc"

# 2. Sphinx, from a deleted _build
{ hdr "sphinx -W --keep-going, from a deleted DOCS/sphinx/_build"
  rm -rf DOCS/sphinx/_build
  echo "# command: $PY -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html"
  echo "# started $(stamp)"
  $PY -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html 2>&1 | tail -15
  echo "# exit code: ${PIPESTATUS[0]}"
  echo "# ended $(stamp)"; } > "$OUT/sphinx.txt" 2>&1
grep -a '^# exit code' "$OUT/sphinx.txt" | grep -qv ': 0$' && overall=1

# 3. gitleaks
{ hdr "gitleaks (pinned binary): full history, then --staged"
  for args in "git . --no-banner" "git . --staged --no-banner"; do
    echo "# command: $GITLEAKS $args"; echo "# started $(stamp)"
    $GITLEAKS $args 2>&1 | sed 's/\x1b\[[0-9;]*m//g'
    echo "# exit code: ${PIPESTATUS[0]}"; echo "# ended $(stamp)"; echo
  done; } > "$OUT/gitleaks.txt" 2>&1
grep -a '^# exit code' "$OUT/gitleaks.txt" | grep -qv ': 0$' && overall=1

# 4. immutability, manifests, delta re-audit, index self-checks
{ hdr "immutability diffs for the S3 delta, 5ba0129e..HEAD"
  bash EVIDENCE/exp002-d1-s3/immutability.sh 5ba0129e HEAD; echo "(script exit: $?)"; } > "$OUT/immutability-after.txt" 2>&1
grep -a 'script exit' "$OUT/immutability-after.txt" | grep -qv ': 0)' && overall=1
{ hdr "verify_manifest over the five EXP-002 RUN-* directories and the frozen input manifest"
  $PY -I EVIDENCE/exp002-d1-s3/verify_manifest_runs.py; echo "# exit code: $?"; } > "$OUT/verify-manifest.txt" 2>&1
grep -a '^# exit code' "$OUT/verify-manifest.txt" | grep -qv ': 0$' && overall=1
bash EVIDENCE/exp002-d1-s3/delta_reaudit.sh > "$OUT/delta-reaudit.txt" 2>&1; rc=$?; [ "$rc" -eq 0 ] || overall=1
echo "delta re-audit exit: $rc"
for b in exp002-d1-s1 exp002-d1-s2 exp002-d1-s3; do
  { hdr "index self-check of EVIDENCE/$b/"
    echo "# command: $PY -I EVIDENCE/exp002-d1-s3/index_selfcheck.py $b"
    $PY -I EVIDENCE/exp002-d1-s3/index_selfcheck.py "$b"; echo "# exit code: $?"; } > "$OUT/index-selfcheck-${b#exp002-d1-}.txt" 2>&1
  grep -a '^# exit code' "$OUT/index-selfcheck-${b#exp002-d1-}.txt" | grep -qv ': 0$' && overall=1
done

# 5. Snyk Code CLI (authentication verified first: an expired token gives 401 and no SARIF)
{ hdr "Snyk Code CLI"
  echo "# snyk $(snyk --version)"; echo "# command: snyk whoami"; snyk whoami; rc=$?; echo "# exit code: $rc"
  [ "$rc" -eq 0 ] || overall=1
  SARIF="$(cygpath -m "${TEMP:-/tmp}")/prin-s3-final.sarif"
  rm -f "$SARIF"
  echo; echo "# command: snyk code test . --severity-threshold=low --sarif-file-output=$SARIF"
  echo "# started $(stamp)"
  snyk code test . --severity-threshold=low "--sarif-file-output=$SARIF" > "$OUT/snyk-console.txt" 2>&1
  rc=$?; echo "# exit code: $rc (1 = findings reported, not a scan failure; 2 or more = the scan did not run)"
  [ "$rc" -le 1 ] || overall=1
  echo "# ended $(stamp)"
  if [ -s "$SARIF" ]; then
    echo "# SARIF sha256: $(sha256sum "$SARIF" | cut -d' ' -f1)  size: $(stat -c %s "$SARIF") bytes (kept outside the repository)"
    echo; echo "## CLI Test Summary, verbatim"; sed -n '/Test Summary/,/Open issues/p' "$OUT/snyk-console.txt"
    echo; echo "## Bucketed by snyk_s3_filter.py (SARIF on stdin)"
    $PY -I EVIDENCE/exp002-d1-s3/snyk_s3_filter.py < "$SARIF"; rc=$?; echo "# filter exit code: $rc (0 = nothing above LOW in any git-known path)"
    [ "$rc" -eq 0 ] || overall=1
  else
    echo "# NO SARIF WRITTEN: this leg is BLOCKED, not clean."
    overall=1
  fi; } > "$OUT/snyk-code-s3-final.txt" 2>&1

# 6. the draft PR is untouched
{ hdr "draft PR #34"
  echo "# command: gh pr view 34 --json state,isDraft,headRefOid"; gh pr view 34 --json state,isDraft,headRefOid 2>&1
  echo "# command: git rev-parse origin/hotfix/exp002-d1-figure-parity (after git fetch)"; git fetch -q --all --prune 2>&1; git rev-parse origin/hotfix/exp002-d1-figure-parity
  echo "# commits ahead of origin: $(git rev-list --count origin/hotfix/exp002-d1-figure-parity..HEAD)   behind: $(git rev-list --count HEAD..origin/hotfix/exp002-d1-figure-parity)"; } > "$OUT/pr-34.txt" 2>&1

echo "final legs overall: $overall (0 = every leg exited 0)"
exit "$overall"
