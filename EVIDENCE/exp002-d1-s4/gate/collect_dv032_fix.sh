#!/usr/bin/env bash
# Collect the DV-032 fix evidence into the S4 bundle.
#
# Instruments already live in gate/ (dv032-*-probe.py, verify-dv032-fix.sh,
# measure-ratio-sensitivity.sh); this gathers their OUTPUTS from scratch, which is
# outside the repository, plus the two harness files that must stay outside the
# repo at run time (the pytest plugin and the engagement check).
#
# Both the superseded and the corrected runs are kept: the first verification
# shows the drain defect (a control failing on the WRONG assertion) and the first
# sensitivity run shows the module-patching defect. Discarding either would hide
# how the fix was validated.
set -u
ROOT=/c/dev/PRIN
S="$HOME/prin-s4-scratch"
D="$ROOT/EVIDENCE/exp002-d1-s4/gate/dv032-fix"
cd "$ROOT" || exit 2
mkdir -p "$D/verify-first-attempt" "$D/verify" "$D/sensitivity" "$D/sensitivity-runs"

missing=0
take() {  # take <src> <dst>
  if [ -f "$1" ]; then cp "$1" "$2"; else echo "MISSING: $1"; missing=$((missing + 1)); fi
}

# --- the metric probe and its output ----------------------------------------
take "$S/dv032-probe.txt"     "$D/metric-probe.txt"
# --- the bound probe: partial, it hung under load; kept as-is with its reason --
take "$S/dv032-bound.txt"     "$D/bound-probe-partial.txt"
# --- the tolerance distribution that sized the 1.60 bound ---------------------
take "$S/dv032-tolerance.txt" "$D/tolerance-probe.txt"

# --- verification: first attempt (drain defect) and corrected -----------------
for f in "$S"/dv032-verify/*.txt; do
  [ -f "$f" ] && cp "$f" "$D/verify-first-attempt/$(basename "$f")"
done
take "$S/dv032-verify2.txt"   "$D/verify/summary.txt"
for f in "$S"/dv032-verify/*.txt; do
  [ -f "$f" ] && cp "$f" "$D/verify/$(basename "$f")"
done

# --- sensitivity: first attempt (module-patching defect) and corrected --------
take "$S/dv032-sensitivity.txt"  "$D/sensitivity/run1-harness-defect.txt"
take "$S/dv032-sensitivity2.txt" "$D/sensitivity/run2-corrected.txt"
for f in "$S"/dv032-ratio-under-load/*.txt; do
  [ -f "$f" ] && cp "$f" "$D/sensitivity-runs/$(basename "$f")"
done

# --- harness files that must stay outside the repo at run time ---------------
take "$S/dv032negctl.py"   "$D/dv032negctl.py"
take "$S/verify_negctl.py" "$D/verify_negctl.py"

echo "collected into EVIDENCE/exp002-d1-s4/gate/dv032-fix  (missing sources: $missing)"
find "$D" -type f | sed "s|$D/||" | sort
