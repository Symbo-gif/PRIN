#!/usr/bin/env bash
# EXP-002 D1 S4 - O-2: red-before / green-after demonstration of the one
# CONFIRMED defect (EXP002D1-S4-F1).
#
# The defect: EVIDENCE/exp002-d1-s3/final_legs.sh aggregates five of its legs with
#
#     grep -a '^# exit code' "$OUT/x.txt" | grep -qv ': 0$' && overall=1
#
# `grep -qv P` exits 0 only if SOME input line does not match P. With no input
# lines at all it exits 1, so the `&& overall=1` arm is skipped: a leg whose
# record is missing, empty, or holds no marker line is counted as PASSING.
# Round 4 fixed exactly this class for the Snyk leg (triage T4-2) by capturing
# `rc=$?` directly, but left the five grep-aggregated legs unchanged.
#
# RED  = the committed S3 pattern, evaluated over four record shapes.
# GREEN = the fail-closed `require_marker` helper used by this bundle's
#         final_legs.sh, evaluated over the same four shapes.
# Read-only: S3's file is never edited. Run from anywhere.
set -u
OUT="${S4_FAILOPEN_OUT:-$HOME/prin-s4-scratch/failopen}"
mkdir -p "$OUT"; rm -f "$OUT"/*.txt
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }

echo "# EXP-002 D1 S4 - EXP002D1-S4-F1 red-before / green-after"
echo "# date (UTC): $(stamp)"
echo "# defect location: EVIDENCE/exp002-d1-s3/final_legs.sh, the grep-aggregated legs"
echo "# the five committed lines that carry the pattern:"
grep -n "grep -qv" /c/dev/PRIN/EVIDENCE/exp002-d1-s3/final_legs.sh | sed 's/^/    /'

# ---------------------------------------------------------------- RED: S3 pattern
echo
echo "=================================================================="
echo "## RED - the committed S3 aggregation pattern"
red() {  # $1 = label, $2 = record file (may not exist)
  local overall=0
  grep -a '^# exit code' "$2" 2>/dev/null | grep -qv ': 0$' && overall=1
  printf '    %-34s overall=%s  %s\n' "$1" "$overall" \
    "$([ "$overall" -eq 0 ] && echo '<- reads as PASS' || echo '<- reads as FAIL')"
}
# Fixtures use the EXACT marker form the five grep-aggregated legs write. That
# form is bare: `# exit code: N` (sphinx, gitleaks, verify-manifest, the three
# index self-checks) and `(script exit: N)` (immutability). Verified against the
# committed S3 records rather than assumed - the legs whose markers DO carry
# trailing prose (Snyk's `# exit code: 1 (1 = findings reported, ...)`) are
# precisely the ones round 4 moved to direct `rc=$?` capture, and are not in the
# grep-aggregated set. An earlier draft of this script wrote "# exit code: 0 (a
# genuinely green leg)", whose trailing text is not the real form; that made the
# green fixture read as a failure under BOTH patterns and mislabelled the result.
printf '# exit code: 0\n' > "$OUT/ok.txt"
printf '# exit code: 1\n' > "$OUT/bad.txt"
printf '# sphinx -W --keep-going\n# date (UTC): x\n' > "$OUT/nomarker.txt"
:                                                    > "$OUT/empty.txt"
rm -f                                                "$OUT/missing.txt"
echo "    fixture bytes, to show the marker form is the bare real one:"
for f in ok bad nomarker empty; do
  printf '      %-10s ' "$f.txt"; od -c "$OUT/$f.txt" | head -2 | tr '\n' ' '; echo
done
red "marker '# exit code: 0'"   "$OUT/ok.txt"
red "marker '# exit code: 1'"   "$OUT/bad.txt"
red "record file MISSING"       "$OUT/missing.txt"
red "record has NO marker line" "$OUT/nomarker.txt"
red "record file EMPTY"         "$OUT/empty.txt"
echo "    => the two real marker shapes aggregate correctly; the 3 shapes where a"
echo "       leg produced no usable record all read as PASS. That is the defect."

# ------------------------------------------------------------- GREEN: fail-closed
echo
echo "=================================================================="
echo "## GREEN - the fail-closed require_marker helper (this bundle's final_legs.sh)"
# Verbatim from EVIDENCE/exp002-d1-s4/final_legs.sh
require_marker() {
  local file="$1" marker_re="$2" ok_re="$3" label="$4" n bad
  if [ ! -s "$file" ]; then
    printf '    %-34s NO RECORD (missing or empty)   -> FAIL (fail-closed)\n' "$label"
    return 1
  fi
  n=$(grep -ac "$marker_re" "$file")
  if [ "$n" -eq 0 ]; then
    printf '    %-34s record has no marker line     -> FAIL (fail-closed)\n' "$label"
    return 1
  fi
  bad=$(grep -a "$marker_re" "$file" | grep -avc "$ok_re")
  if [ "$bad" -ne 0 ]; then
    printf '    %-34s %s of %s marker(s) not ok -> FAIL\n' "$label" "$bad" "$n"
    return 1
  fi
  printf '    %-34s %s marker(s), all ok        -> PASS\n' "$label" "$n"
  return 0
}
green() { local overall=0; require_marker "$2" '^# exit code' ': 0$' "$1" || overall=1
          printf '       (overall=%s)\n' "$overall"; }
green "marker '# exit code: 0'"   "$OUT/ok.txt"
green "marker '# exit code: 1'"   "$OUT/bad.txt"
green "record file MISSING"       "$OUT/missing.txt"
green "record has NO marker line" "$OUT/nomarker.txt"
green "record file EMPTY"         "$OUT/empty.txt"

# ------------------------------------- the variant marker the immutability leg uses
echo
echo "=================================================================="
echo "## the immutability leg's variant marker ('script exit'), same demonstration"
printf 'range: a..b\n(script exit: 0)\n' > "$OUT/imm-ok.txt"
printf 'range: a..b\n(script exit: 1)\n' > "$OUT/imm-bad.txt"
printf 'range: a..b\n'                  > "$OUT/imm-nomarker.txt"
for pair in "script-exit 0:$OUT/imm-ok.txt" "script-exit 1:$OUT/imm-bad.txt" \
            "no marker:$OUT/imm-nomarker.txt"; do
  label="${pair%%:*}"; f="${pair#*:}"
  o=0; grep -a 'script exit' "$f" | grep -qv ': 0)' && o=1
  printf '    RED   %-18s overall=%s\n' "$label" "$o"
  n=0; require_marker "$f" 'script exit' ': 0)' "$label" >/dev/null || n=1
  printf '    GREEN %-18s overall=%s\n' "$label" "$n"
done

# --------------------------------------------- re-apply GREEN to the S3 records
echo
echo "=================================================================="
echo "## was the defect latent? require_marker re-applied to the committed S3 records"
S3F=/c/dev/PRIN/EVIDENCE/exp002-d1-s3/gate/final
lat=0
check_one() { require_marker "$S3F/$1" "$2" "$3" "$1" || lat=$((lat+1)); }
check_one sphinx.txt              '^# exit code' ': 0$'
check_one gitleaks.txt            '^# exit code' ': 0$'
check_one verify-manifest.txt     '^# exit code' ': 0$'
check_one index-selfcheck-s1.txt  '^# exit code' ': 0$'
check_one index-selfcheck-s2.txt  '^# exit code' ': 0$'
check_one index-selfcheck-s3.txt  '^# exit code' ': 0$'
check_one immutability-after.txt  'script exit'  ': 0)'
echo "    records failing the fail-closed check: $lat"
echo "    => 0 means every committed S3 record carries its marker, so no recorded"
echo "       S3 result was masked. The defect is LATENT, not realised."
echo
echo "# finished $(stamp)"
[ "$lat" -eq 0 ]
