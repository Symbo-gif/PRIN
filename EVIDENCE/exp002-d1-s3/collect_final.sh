#!/usr/bin/env bash
# EXP-002 D1 S3 - copy the records final_legs.sh wrote OUTSIDE the repository into
# EVIDENCE/exp002-d1-s3/gate/final/.
#
#   bash EVIDENCE/exp002-d1-s3/collect_final.sh
#
# The only change made to a record is cosmetic: ANSI colour and erase-line escape
# sequences are removed, and carriage returns (Windows line endings, and the
# in-place progress lines Sphinx and gitleaks print) become newlines, so the file
# is plain LF text that the repository's `.gitattributes` will not rewrite. Every
# command, exit code, UTC time and result line is copied unchanged. The SARIF
# report is not copied (712 KB; its SHA-256 is in snyk-code-s3-final.txt).
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
SRC="$HOME/prin-s3-scratch/final"
DST="EVIDENCE/exp002-d1-s3/gate/final"
FILES="static-gate sphinx gitleaks immutability-after verify-manifest delta-reaudit index-selfcheck-s1 index-selfcheck-s2 index-selfcheck-s3 snyk-code-s3-final snyk-console pr-34"
mkdir -p "$DST"
for f in $FILES; do
  [ -f "$SRC/$f.txt" ] || { echo "missing record: $SRC/$f.txt"; exit 1; }
  sed -e 's/\x1b\[[0-9;]*[mK]//g' -e 's/\r$//' -e 's/\r/\n/g' "$SRC/$f.txt" > "$DST/$f.txt"
done
echo "copied $(echo "$FILES" | wc -w) records to $DST"
