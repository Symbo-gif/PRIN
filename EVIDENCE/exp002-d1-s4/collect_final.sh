#!/usr/bin/env bash
# EXP-002 D1 S4 - copy the gate records from scratch (outside the repository) into
# the evidence bundle, as .txt (*.log is gitignored, so console logs are saved as
# .txt). Run after long_legs.sh and final_legs.sh.
#
#   bash EVIDENCE/exp002-d1-s4/collect_final.sh
#
# Idempotent: it copies, it never edits a record's content. Each copied file gets
# a one-line provenance header naming its scratch source and the copy time, so a
# reader can tell the bundle copy from the original.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
S="$HOME/prin-s4-scratch"
D=EVIDENCE/exp002-d1-s4/gate
mkdir -p "$D/fast" "$D/full"
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
copied=0; missing=0

# $1 = source path, $2 = destination path relative to the bundle
take() {
  if [ -f "$1" ]; then
    { echo "# copied from $1 at $(stamp)"; cat "$1"; } > "$2"
    copied=$((copied + 1))
    echo "  copied $1 -> $2"
  else
    missing=$((missing + 1))
    echo "  MISSING $1 (not copied; $2 will not exist)"
  fi
}

echo "# collecting S4 gate records into $D"
take "$S/gate/change-set.txt"  "$D/change-set.txt"
take "$S/gate/legs.txt"        "$D/long-legs.txt"
take "$S/fast/run.txt"         "$D/fast/run.txt"
take "$S/fast/console.log"     "$D/fast/console.txt"
take "$S/fast/samples.jsonl"   "$D/fast/samples.jsonl"
take "$S/fast/sampler.err"     "$D/fast/sampler-err.txt"
take "$S/full/run.txt"         "$D/full/run.txt"
take "$S/full/console.log"     "$D/full/console.txt"
take "$S/full/samples.jsonl"   "$D/full/samples.jsonl"
take "$S/full/sampler.err"     "$D/full/sampler-err.txt"
for f in "$S"/final/*; do
  [ -f "$f" ] || continue
  take "$f" "$D/final/$(basename "$f")"
done

echo
echo "# copied: $copied   missing: $missing"
echo "# a missing source is reported, never silently skipped: it means that leg did not run"
[ "$missing" -eq 0 ]
