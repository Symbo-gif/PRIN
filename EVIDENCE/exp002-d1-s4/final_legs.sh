#!/usr/bin/env bash
# EXP-002 D1 S4 - the cheap closing legs, run on the FINAL documentation commit.
#
#   bash EVIDENCE/exp002-d1-s4/final_legs.sh
#
# This is the corrected copy that SUPERSEDES EVIDENCE/exp002-d1-s3/final_legs.sh
# for finding EXP002D1-S4-F1 (D2, latent), confirmed by S4's O-2 review
# (o2-review/triage.md). S3's file is NOT edited; it is carried as superseded.
#
# THE DEFECT IN S3'S VERSION: five legs were aggregated with
#     grep -a '<marker>' FILE | grep -qv '<ok form>' && overall=1
# `grep -qv P` exits 0 only if SOME input line does not match P. With no input
# lines at all it exits 1, so the `&&` arm is skipped and a leg whose record is
# missing, empty, or holds no marker line leaves overall=0 - it reads as PASSING.
# Reproduced in o2-review/reproduce-batch3.txt (C17) and
# o2-review/failopen-red-green.txt.
#
# THE FIX: every leg is aggregated by the fail-closed `require_marker` helper
# below, or by direct `rc=$?` capture where the leg runs in this shell. A missing
# record, an empty record, a record with no marker line, and any marker that is
# not the ok form ALL set overall=1.
#
# Legs: the static / quality / security / governance gate, Sphinx from a deleted
# _build, gitleaks (full history and --staged), both immutability diffs, the
# EXP-002 manifest verification, the delta re-audit, the four bundle index
# self-checks, the Snyk Code CLI scan, and the state of PR #34. They run one
# after another and never overlap pytest or cargo.
#
# Output goes OUTSIDE the repository, to ~/prin-s4-scratch/final/ (override with
# FINAL_LEGS_OUT, used only to test this script's exit status), and is copied into
# the bundle afterwards by collect_final.sh.
#
# Exit status: 0 only if every leg exited 0 AND every leg produced a usable
# record. Anything else - including a leg that produced no record - is 1.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
export PATH="/c/Program Files/Git/bin:$PATH"
PY=.venv/Scripts/python.exe
OUT="${FINAL_LEGS_OUT:-$HOME/prin-s4-scratch/final}"
mkdir -p "$OUT"
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "tracked tree is not clean; refusing to start"; exit 2; }
GITLEAKS=DOCS/test_and_benchmark_results/ea007/full-gate/.tools/gitleaks/bin/gitleaks.exe
# Index self-checks of the three PRE-EXISTING bundles only. This bundle's own
# self-check cannot run here: it must index the gate/final records that this very
# script is still producing, and they are copied in by collect_final.sh afterwards.
# A bundle cannot index records that do not exist yet, so the s4 self-check is a
# separate post-collection step (the S4 session prompt requires it explicitly),
# recorded at gate/final/index-selfcheck-s4.txt. S3's final_legs.sh checked
# s1/s2/s3 for the same reason.
BUNDLES="exp002-d1-s1 exp002-d1-s2 exp002-d1-s3"
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
HEAD_SHA=$(git rev-parse HEAD)
overall=0

hdr() { echo "# $1"; echo "# date (UTC): $(stamp)"; echo "# git HEAD: $HEAD_SHA   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)"; echo; }

# Fail-closed aggregation. $1 record file, $2 marker regex, $3 ok regex, $4 label.
# Returns 1 (=> overall=1) when the record is missing, empty, holds no marker
# line, or holds any marker line that is not the ok form.
require_marker() {
  local file="$1" marker_re="$2" ok_re="$3" label="$4" n bad
  if [ ! -s "$file" ]; then
    echo "AGGREGATION $label: NO RECORD (missing or empty) -> FAIL (fail-closed)"; return 1
  fi
  n=$(grep -ac "$marker_re" "$file")
  if [ "$n" -eq 0 ]; then
    echo "AGGREGATION $label: record has no '$marker_re' marker line -> FAIL (fail-closed)"; return 1
  fi
  bad=$(grep -a "$marker_re" "$file" | grep -avc "$ok_re")
  if [ "$bad" -ne 0 ]; then
    echo "AGGREGATION $label: $bad of $n marker(s) not the ok form -> FAIL"; return 1
  fi
  echo "AGGREGATION $label: $n marker(s), all the ok form -> PASS"; return 0
}
# Fail-closed aggregation for a leg run in this shell, by direct status capture.
require_rc() {
  local rc="$1" label="$2"
  if [ "$rc" -eq 0 ]; then echo "AGGREGATION $label: exit 0 -> PASS"; return 0; fi
  echo "AGGREGATION $label: exit $rc -> FAIL"; return 1
}

# 1. static / quality / security / governance
bash EVIDENCE/exp002-d1-s4/static_gate.sh > "$OUT/static-gate.txt" 2>&1; rc=$?
require_rc "$rc" "static gate" || overall=1

# 2. Sphinx, from a deleted _build (an incremental build masks autodoc warnings)
{ hdr "sphinx -W --keep-going, from a deleted DOCS/sphinx/_build"
  rm -rf DOCS/sphinx/_build
  echo "# command: $PY -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html"
  echo "# started $(stamp)"
  $PY -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html 2>&1 | tail -15
  echo "# exit code: ${PIPESTATUS[0]}"
  echo "# ended $(stamp)"; } > "$OUT/sphinx.txt" 2>&1
require_marker "$OUT/sphinx.txt" '^# exit code' ': 0$' sphinx || overall=1

# 3. gitleaks (two legs, so two markers must both be the ok form)
{ hdr "gitleaks (pinned binary): full history, then --staged"
  for args in "git . --no-banner" "git . --staged --no-banner"; do
    echo "# command: $GITLEAKS $args"; echo "# started $(stamp)"
    $GITLEAKS $args 2>&1 | sed 's/\x1b\[[0-9;]*m//g'
    echo "# exit code: ${PIPESTATUS[0]}"; echo "# ended $(stamp)"; echo
  done; } > "$OUT/gitleaks.txt" 2>&1
require_marker "$OUT/gitleaks.txt" '^# exit code' ': 0$' gitleaks || overall=1

# 4. immutability, manifests, delta re-audit, index self-checks
{ hdr "immutability diffs for the S4 delta, 6b55c6ba..HEAD"
  bash EVIDENCE/exp002-d1-s4/immutability.sh 6b55c6ba HEAD; echo "(script exit: $?)"; } > "$OUT/immutability-after.txt" 2>&1
require_marker "$OUT/immutability-after.txt" 'script exit' ': 0)' immutability || overall=1
{ hdr "verify_manifest over the five EXP-002 RUN-* directories and the frozen input manifest"
  $PY -I EVIDENCE/exp002-d1-s3/verify_manifest_runs.py; echo "# exit code: $?"; } > "$OUT/verify-manifest.txt" 2>&1
require_marker "$OUT/verify-manifest.txt" '^# exit code' ': 0$' verify-manifest || overall=1
bash EVIDENCE/exp002-d1-s3/delta_reaudit.sh > "$OUT/delta-reaudit.txt" 2>&1; rc=$?
require_rc "$rc" "delta re-audit" || overall=1
for b in $BUNDLES; do
  { hdr "index self-check of EVIDENCE/$b/"
    echo "# command: $PY -I EVIDENCE/exp002-d1-s3/index_selfcheck.py $b"
    $PY -I EVIDENCE/exp002-d1-s3/index_selfcheck.py "$b"; echo "# exit code: $?"; } > "$OUT/index-selfcheck-${b#exp002-d1-}.txt" 2>&1
  require_marker "$OUT/index-selfcheck-${b#exp002-d1-}.txt" '^# exit code' ': 0$' "index-selfcheck-${b#exp002-d1-}" || overall=1
done

# 5. Snyk Code CLI (authentication verified first: an expired token gives 401 and no SARIF)
{ hdr "Snyk Code CLI"
  echo "# snyk $(snyk --version)"; echo "# command: snyk whoami"; snyk whoami; rc=$?; echo "# exit code: $rc"
  [ "$rc" -eq 0 ] || overall=1
  SARIF="$(cygpath -m "${TEMP:-/tmp}")/prin-s4-final.sarif"
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
    echo; echo "## The ratified python/PT locations (F8, all three) and any finding above LOW"
    grep -aE 'python/PT|HIGH|MEDIUM' "$OUT/snyk-console.txt" | head -40
  else
    echo "# NO SARIF WRITTEN: this leg is BLOCKED, not clean."
    overall=1
  fi; } > "$OUT/snyk-code-s4-final.txt" 2>&1
# Fail-closed on the Snyk record too: it must exist and must not say BLOCKED.
if [ ! -s "$OUT/snyk-code-s4-final.txt" ]; then
  echo "AGGREGATION snyk record: NO RECORD -> FAIL (fail-closed)"; overall=1
elif grep -aq 'NO SARIF WRITTEN' "$OUT/snyk-code-s4-final.txt"; then
  echo "AGGREGATION snyk record: says BLOCKED -> FAIL"; overall=1
else
  echo "AGGREGATION snyk record: present and not BLOCKED -> PASS"
fi

# 6. the state of PR #34 and of the branch
{ hdr "PR #34 and the branch"
  echo "# command: gh pr view 34 --json state,isDraft,headRefOid"; gh pr view 34 --json state,isDraft,headRefOid 2>&1
  echo "# command: git fetch --all --prune"; git fetch -q --all --prune 2>&1
  echo "# command: git rev-parse origin/hotfix/exp002-d1-figure-parity"; git rev-parse origin/hotfix/exp002-d1-figure-parity
  echo "# commits ahead of origin: $(git rev-list --count origin/hotfix/exp002-d1-figure-parity..HEAD)   behind: $(git rev-list --count HEAD..origin/hotfix/exp002-d1-figure-parity)"; } > "$OUT/pr-34.txt" 2>&1

echo "final legs overall: $overall (0 = every leg exited 0 and produced a usable record)"
exit "$overall"
