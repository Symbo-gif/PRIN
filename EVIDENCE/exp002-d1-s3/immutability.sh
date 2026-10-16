#!/usr/bin/env bash
# EXP-002 D1 S3 - immutability diffs. Run from Git Bash at the repository root.
#
#   bash EVIDENCE/exp002-d1-s3/immutability.sh <from-rev> <to-rev>
#
# Prints, for the half-open range from-rev..to-rev:
#   I1  the EXP-002 record, its raw run directories, CI workflows and the
#       dependency manifests (must be EMPTY);
#   I2  EVIDENCE/exp002-d1-s1/ - S1's evidence (only the README may differ, and
#       only by added lines);
#   I3  the S1 and S2 sections of the correction audit (the audit must be a pure
#       append: zero deleted lines).
# Exit status 0 when I1 is empty and I3 shows 0 deletions, 1 otherwise.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
FROM=$(git rev-parse --verify --quiet "${1:?usage: immutability.sh <from-rev> <to-rev>}^{commit}") || { echo "not a commit: $1"; exit 2; }
TO=$(git rev-parse --verify --quiet "${2:?usage: immutability.sh <from-rev> <to-rev>}^{commit}") || { echo "not a commit: $2"; exit 2; }
AUDIT=DOCS/audits/2026-10-15-exp002-d1-correction-audit.md
status=0

echo "range: $FROM..$TO   (HEAD now $(git rev-parse HEAD))"

echo
echo "## I1 EXP-002 record, benchmarks/results/EXP-002/, .github/, dependency manifests (must be empty)"
out=$(git diff --stat "$FROM..$TO" -- \
  DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/ \
  benchmarks/results/EXP-002/ .github/ Cargo.toml Cargo.lock pyproject.toml)
if [ -z "$out" ]; then echo "(empty)"; else echo "$out"; status=1; fi

echo
echo "## I2 EVIDENCE/exp002-d1-s1/ (S1 evidence; only the README may change)"
git diff --numstat "$FROM..$TO" -- EVIDENCE/exp002-d1-s1/ | sed 's/^/  /'
[ -z "$(git diff --numstat "$FROM..$TO" -- EVIDENCE/exp002-d1-s1/)" ] && echo "  (empty)"
echo "  files other than README.md changed: $(git diff --name-only "$FROM..$TO" -- EVIDENCE/exp002-d1-s1/ | grep -vc 'README.md$')"
echo "  deleted lines in S1 evidence: $(git diff --numstat "$FROM..$TO" -- EVIDENCE/exp002-d1-s1/ | awk '{d+=$2} END{print d+0}')"
echo "  EVIDENCE/exp002-d1-s1/ has a SHA256SUMS or manifest file: $(git ls-tree -r --name-only "$TO" -- EVIDENCE/exp002-d1-s1/ | grep -ci 'sha256\|manifest' )"

echo
echo "## I3 correction audit is append-only (deleted lines must be 0)"
git diff --numstat "$FROM..$TO" -- "$AUDIT" | awk '{printf "  added %s, deleted %s  %s\n",$1,$2,$3}'
del=$(git diff --numstat "$FROM..$TO" -- "$AUDIT" | awk '{d+=$2} END{print d+0}')
echo "  deletions: $del"
[ "$del" -eq 0 ] || status=1

echo
echo "# exit code: $status"
exit "$status"
