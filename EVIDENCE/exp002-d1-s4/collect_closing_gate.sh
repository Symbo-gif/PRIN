#!/usr/bin/env bash
# EXP-002 D1 S4 - collect the 67100a69 closing-gate records WITHOUT clobbering
# the earlier runs already committed in this bundle.
#
# collect_final.sh cannot be reused as-is for two reasons:
#
#   1. It copies scratch fast/ and full/ over gate/fast/ and gate/full/, which
#      hold the committed 157ce5bc run that README.md and audit S4.7 cite by
#      path.  Overwriting them would silently relabel that record.
#   2. It writes a HARDCODED gate/isolated-rerun.txt asserting "S4's single
#      required full-suite run exited 0 (6331 passed ...)".  That was true of the
#      157ce5bc run and is now false: at 814b670c the full leg exited 1, and at
#      67100a69 the FAST leg exited 1 on a WinError 5 lock and does have an
#      isolation re-run.  Re-emitting it would commit a false statement.
#
# So this writes the new run into suffixed directories and leaves every earlier
# record byte-identical.  Three runs are now preserved side by side:
#   gate/fast/, gate/full/            157ce5bc  (green; superseded control)
#   gate/red-leg-814b670c/            814b670c  (RED; DV-032 defect)
#   gate/{fast,full}-67100a69/        67100a69  (the closing gate, authoritative)
#
# .jsonl is copied byte-for-byte with no header so the sampler record stays
# parseable.  A missing source is counted and reported, never silently skipped.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
S="$HOME/prin-s4-scratch"
D=EVIDENCE/exp002-d1-s4/gate
SHA=$(git rev-parse --short HEAD)
mkdir -p "$D/fast-$SHA" "$D/full-$SHA"
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
copied=0; missing=0

take() {  # take <src> <dst>  - text record, provenance header prepended
  if [ -f "$1" ]; then
    { echo "# copied from $1 at $(stamp)"; cat "$1"; } > "$2"
    copied=$((copied + 1)); echo "  copied  $1 -> $2"
  else
    missing=$((missing + 1)); echo "  MISSING $1 (not copied; $2 will not exist)"
  fi
}
take_raw() {  # byte-for-byte, no header (structured records)
  if [ -f "$1" ]; then
    cp -f "$1" "$2"
    copied=$((copied + 1)); echo "  copied  $1 -> $2  (raw, no header)"
  else
    missing=$((missing + 1)); echo "  MISSING $1 (not copied)"
  fi
}

echo "# collecting the $SHA closing-gate records into $D  ($(stamp))"

# --- the aggregated legs record --------------------------------------------
take "$S/gate/legs.txt"        "$D/long-legs-$SHA.txt"
take "$S/gate/change-set.txt"  "$D/change-set-$SHA.txt"

# --- fast leg (exit 1 on the WinError 5 lock class) -------------------------
take     "$S/fast/run.txt"       "$D/fast-$SHA/run.txt"
take     "$S/fast/console.log"   "$D/fast-$SHA/console.txt"
take_raw "$S/fast/samples.jsonl" "$D/fast-$SHA/samples.jsonl"
take     "$S/fast/sampler.err"   "$D/fast-$SHA/sampler-err.txt"

# --- full leg ---------------------------------------------------------------
take     "$S/full/run.txt"       "$D/full-$SHA/run.txt"
take     "$S/full/console.log"   "$D/full-$SHA/console.txt"
take_raw "$S/full/samples.jsonl" "$D/full-$SHA/samples.jsonl"
take     "$S/full/sampler.err"   "$D/full-$SHA/sampler-err.txt"

# --- isolated fast re-run, if it has been performed -------------------------
if [ -d "$S/fast-isolated" ]; then
  mkdir -p "$D/fast-isolated-$SHA"
  take     "$S/fast-isolated/run.txt"       "$D/fast-isolated-$SHA/run.txt"
  take     "$S/fast-isolated/console.log"   "$D/fast-isolated-$SHA/console.txt"
  take_raw "$S/fast-isolated/samples.jsonl" "$D/fast-isolated-$SHA/samples.jsonl"
  take     "$S/fast-isolated/sampler.err"   "$D/fast-isolated-$SHA/sampler-err.txt"
else
  echo "  absent  $S/fast-isolated (isolation re-run not yet performed)"
fi

# --- cheap legs from final_legs.sh, if present ------------------------------
if [ -d "$S/final" ]; then
  mkdir -p "$D/final-$SHA"
  for f in "$S"/final/*; do
    [ -f "$f" ] || continue
    take "$f" "$D/final-$SHA/$(basename "$f")"
  done
else
  echo "  absent  $S/final (cheap legs not yet run)"
fi

echo
echo "# copied: $copied   missing: $missing"
echo "# gate/fast/ and gate/full/ (157ce5bc) were NOT touched:"
ls -1 "$D/fast" "$D/full" | sed 's/^/    /'
[ "$missing" -eq 0 ]
