#!/usr/bin/env bash
# EXP-002 D1 S4 - immutability diffs. Run from Git Bash at the repository root.
#
#   bash EVIDENCE/exp002-d1-s4/immutability.sh <from-rev> <to-rev>
#
# Adapted copy of S3's immutability.sh. S4's rule set differs from S3's in one
# place, so the instrument differs: the EXP-002 record is NOT required to be
# empty, because closure item 4 mandates exactly one append to report.md section
# 15. Every other frozen surface must still be empty.
#
#   I1a the EXP-002 record: the ONLY changed file may be report.md, and its
#       change must be a pure append (0 deleted lines).
#   I1b benchmarks/results/EXP-002/, .github/, Cargo.toml, Cargo.lock and
#       pyproject.toml must be EMPTY.
#   I2  EVIDENCE/exp002-d1-s1/, -s2/ and -s3/ must be EMPTY (unedited).
#   I3  the correction audit must be a pure append (0 deleted lines).
#   I4  the S4 brief's "Closure checklist" and "Carried from S3" sections must be
#       byte-identical to the base revision (only the Status header lines and the
#       appended completion section may differ).
#
# Exit status 0 when every rule holds; 1 otherwise; 2 on a bad revision.
# Aggregation is by direct rc capture, never by grepping a record
# (the EXP002D1-S4-F1 fail-open class).
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
FROM=$(git rev-parse --verify --quiet "${1:?usage: immutability.sh <from-rev> <to-rev>}^{commit}") || { echo "not a commit: $1"; exit 2; }
TO=$(git rev-parse --verify --quiet "${2:?usage: immutability.sh <from-rev> <to-rev>}^{commit}") || { echo "not a commit: $2"; exit 2; }
AUDIT=DOCS/audits/2026-10-15-exp002-d1-correction-audit.md
REC=DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity
BRIEF=DOCS/sessions/contingencies/2026-10-14-exp002-d1-s4-correction-documentation.md
status=0

echo "# EXP-002 D1 S4 - immutability"
echo "range: $FROM..$TO   (HEAD now $(git rev-parse HEAD))"
echo "# date (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo
echo "## I1a the EXP-002 record: only report.md may change, and only by appended lines"
names=$(git diff --name-only "$FROM..$TO" -- "$REC/")
echo "  changed files: ${names:-<none>}"
other=$(printf '%s\n' "$names" | grep -v '^$' | grep -vc "/report.md$")
echo "  changed files other than report.md: $other"
[ "$other" -eq 0 ] || status=1
git diff --numstat "$FROM..$TO" -- "$REC/" | awk '{printf "  added %s, deleted %s  %s\n",$1,$2,$3}'
del=$(git diff --numstat "$FROM..$TO" -- "$REC/" | awk '{d+=$2} END{print d+0}')
echo "  deleted lines in the EXP-002 record: $del (must be 0)"
[ "$del" -eq 0 ] || status=1
echo "  the appended lines, verbatim, truncated to their first 90 characters:"
git diff -U0 "$FROM..$TO" -- "$REC/report.md" | grep -a '^+[^+]' | cut -c1-90 | sed 's/^/    /'

echo
echo "## I1b benchmarks/results/EXP-002/, .github/, Cargo.toml, Cargo.lock, pyproject.toml (must be empty)"
out=$(git diff --stat "$FROM..$TO" -- \
  benchmarks/results/EXP-002/ .github/ Cargo.toml Cargo.lock pyproject.toml)
if [ -z "$out" ]; then echo "  (empty)"; else echo "$out" | sed 's/^/  /'; status=1; fi

echo
echo "## I2 EVIDENCE/exp002-d1-s1/, -s2/ and -s3/ must be unedited"
for d in exp002-d1-s1 exp002-d1-s2 exp002-d1-s3; do
  o=$(git diff --numstat "$FROM..$TO" -- "EVIDENCE/$d/")
  if [ -z "$o" ]; then echo "  EVIDENCE/$d/: (empty)"; else echo "$o" | sed "s/^/  EVIDENCE\/$d: /"; status=1; fi
done

echo
echo "## I3 the correction audit is append-only (deleted lines must be 0)"
git diff --numstat "$FROM..$TO" -- "$AUDIT" | awk '{printf "  added %s, deleted %s  %s\n",$1,$2,$3}'
ad=$(git diff --numstat "$FROM..$TO" -- "$AUDIT" | awk '{d+=$2} END{print d+0}')
echo "  deletions: $ad"
[ "$ad" -eq 0 ] || status=1

echo
echo "## I4 the S4 brief's checklist and carried sections are byte-identical to the base"
TMP=$(mktemp -d)
git show "$FROM:$BRIEF" | sed -n '/^## Closure checklist/,$p' > "$TMP/base.txt"
sed -n '/^## Closure checklist/,$p' "$BRIEF" | sed '/^## S4 completion and handoff/,$d' > "$TMP/head.txt"
echo "  base section lines: $(wc -l < "$TMP/base.txt")   head section lines: $(wc -l < "$TMP/head.txt")"
if diff -u "$TMP/base.txt" "$TMP/head.txt" > "$TMP/d.txt"; then
  echo "  identical: yes"
else
  echo "  identical: NO"; sed 's/^/    /' "$TMP/d.txt"; status=1
fi
echo "  what the brief's diff does change (numstat, and every deleted line):"
git diff --numstat "$FROM..$TO" -- "$BRIEF" | awk '{printf "    added %s, deleted %s\n",$1,$2}'
git diff -U0 "$FROM..$TO" -- "$BRIEF" | grep -a '^-[^-]' | cut -c1-100 | sed 's/^/    DELETED: /'
rm -rf "$TMP"

echo
echo "# exit code: $status"
exit "$status"
