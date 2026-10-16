#!/usr/bin/env bash
# EXP-002 D1 S4 - copy the gate records from scratch (outside the repository) into
# the evidence bundle, as .txt (*.log is gitignored, so console logs are saved as
# .txt). Run after long_legs.sh and final_legs.sh.
#
#   bash EVIDENCE/exp002-d1-s4/collect_final.sh
#
# Text records get a one-line provenance header naming their scratch source and the
# copy time. **`.jsonl` records are copied byte-for-byte with no header**, because
# prepending a comment line would make the sampler record unparseable as JSONL.
#
# A missing source is reported and counted, never silently skipped: it means that
# leg did not run, and the script exits 1 so the omission cannot pass unnoticed.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
S="$HOME/prin-s4-scratch"
D=EVIDENCE/exp002-d1-s4/gate
mkdir -p "$D/fast" "$D/full" "$D/final"
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
copied=0; missing=0

# $1 = source path, $2 = destination path
take() {
  if [ -f "$1" ]; then
    { echo "# copied from $1 at $(stamp)"; cat "$1"; } > "$2"
    copied=$((copied + 1)); echo "  copied  $1 -> $2"
  else
    missing=$((missing + 1)); echo "  MISSING $1 (not copied; $2 will not exist)"
  fi
}
# byte-for-byte, no header (structured records)
take_raw() {
  if [ -f "$1" ]; then
    cp -f "$1" "$2"
    copied=$((copied + 1)); echo "  copied  $1 -> $2  (raw, no header)"
  else
    missing=$((missing + 1)); echo "  MISSING $1 (not copied; $2 will not exist)"
  fi
}
# already in the bundle, or produced outside scratch: copy only if the source exists
take_optional() {
  if [ -f "$1" ]; then take "$1" "$2"; else echo "  absent  $1 (optional; not an error)"; fi
}

echo "# collecting S4 gate records into $D  ($(stamp))"

# --- long legs ------------------------------------------------------------
take "$S/gate/change-set.txt"        "$D/change-set.txt"
take "$S/gate/legs.txt"              "$D/long-legs.txt"
take "$S/gate/immutability-before.txt" "$D/immutability-before.txt"
take "$S/fast/run.txt"               "$D/fast/run.txt"
take "$S/fast/console.log"           "$D/fast/console.txt"
take_raw "$S/fast/samples.jsonl"     "$D/fast/samples.jsonl"
take "$S/fast/sampler.err"           "$D/fast/sampler-err.txt"
take "$S/full/run.txt"               "$D/full/run.txt"
take "$S/full/console.log"           "$D/full/console.txt"
take_raw "$S/full/samples.jsonl"     "$D/full/samples.jsonl"
take "$S/full/sampler.err"           "$D/full/sampler-err.txt"

# --- the full suite exited 0, so decision 4A's supplementary isolation re-run of a
#     failed node was not needed. Recorded explicitly rather than left as a gap.
{ echo "# no isolation re-run was performed"
  echo "#"
  echo "# Decision 4A provides for a supplementary re-run of a failed node and its"
  echo "# file in isolation when the required full suite fails on a contention"
  echo "# flake, with the local record kept at its actual exit status."
  echo "#"
  echo "# S4's single required full-suite run exited 0 (6331 passed, 184 skipped,"
  echo "# 0 failed, 1:43:09), with 0 FAILED/ERROR lines in its console, so there was"
  echo "# no failed node to re-run. Nothing was rerun until green and no result was"
  echo "# selected for being favourable."
  echo "#"
  echo "# See full/run.txt and full/console.txt."
} > "$D/isolated-rerun.txt"
copied=$((copied + 1)); echo "  wrote   $D/isolated-rerun.txt (not-applicable record)"

# --- cheap legs -----------------------------------------------------------
for f in "$S"/final/*; do
  [ -f "$f" ] || continue
  take "$f" "$D/final/$(basename "$f")"
done

# --- hosted workflow enablement listings (captured directly into the bundle) ---
take_optional "$S/workflows-before.txt" "$D/workflows-before.txt"
take_optional "$S/workflows-after.txt"  "$D/workflows-after.txt"

echo
echo "# copied/wrote: $copied   missing: $missing"
echo "# a missing REQUIRED source means that leg did not run and is reported, never skipped"
[ "$missing" -eq 0 ]
