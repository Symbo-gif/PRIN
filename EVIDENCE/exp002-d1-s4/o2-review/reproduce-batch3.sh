#!/usr/bin/env bash
# EXP-002 D1 S4 - observation O-2 cold review, third batch.
# C16 non-vacuity control for docstring_only_check.py (batch 2's control was
#     malformed: it passed a '^' suffix, which the tool rejects by design).
# C17 SUSPECTED DEFECT: final_legs.sh aggregates several legs with
#     `grep -a '^# exit code' FILE | grep -qv ': 0$' && overall=1`.
#     If FILE is missing or holds no marker line, the first grep fails, the second
#     sees no input and returns 1, so `&& overall=1` never runs: a leg that
#     produced no record is counted as PASSING. Reproduce it.
# C18 Did that fail-open bite any committed S3 record? Check every marker.
cd /c/dev/PRIN || exit 2
PY=.venv/Scripts/python.exe
OUT=/c/Users/there/prin-s4-scratch/o2
S3=EVIDENCE/exp002-d1-s3
mkdir -p "$OUT"
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
chk() { echo; echo "=================================================================="; echo "## $1"; echo "# started $(stamp)"; }

echo "# EXP-002 D1 S4 - O-2 cold review, batch 3"
echo "# date (UTC): $(stamp)"
echo "# git HEAD: $(git rev-parse HEAD)"
echo "# tracked changes at start: $(git status --porcelain --untracked-files=no | wc -l)"

# ------------------------------------------------------- C16 non-vacuity control
chk "C16 docstring_only_check.py is non-vacuous: a real code change must give exit 1"
F6=$(git log --format=%H --grep 'EXP002D1-S2-F6' -1)
F6P=$(git rev-parse "$F6^")
echo "  F6 commit = $F6   parent = $F6P"
echo "  F6 restored a real keyword argument (label=...) in fig13, so the AST must differ."
echo "  the changed hunk:"
git diff -U1 "$F6P" "$F6" -- python/prin/reporting/figure_generation.py | sed 's/^/    /'
echo "# command: $PY -I $S3/docstring_only_check.py --check $F6P $F6 python/prin/reporting/figure_generation.py"
$PY -I "$S3/docstring_only_check.py" --check "$F6P" "$F6" python/prin/reporting/figure_generation.py 2>&1
echo "# exit code: $? (1 expected = the tool detects a genuine code change, so C6b's 0 is meaningful)"

# ------------------------------------------- C17 the suspected fail-open pattern
chk "C17 final_legs.sh grep-based aggregation: does a MISSING marker fail open?"
echo "  the aggregation lines in the committed script:"
grep -n "grep -qv" "$S3/final_legs.sh" | sed 's/^/    /'
echo
cat > "$OUT/c17.sh" <<'EOF'
overall=0
OUT=/c/Users/there/prin-s4-scratch/o2/c17
mkdir -p "$OUT"; rm -f "$OUT"/*

# case A: marker present, exit 0  -> must stay 0
echo "# exit code: 0" > "$OUT/a.txt"
grep -a '^# exit code' "$OUT/a.txt" | grep -qv ': 0$' && overall=1
echo "    A marker 'exit code: 0'          -> overall=$overall (expect 0)"

# case B: marker present, exit 1  -> must become 1
overall=0
echo "# exit code: 1" > "$OUT/b.txt"
grep -a '^# exit code' "$OUT/b.txt" | grep -qv ': 0$' && overall=1
echo "    B marker 'exit code: 1'          -> overall=$overall (expect 1)"

# case C: FILE MISSING entirely   -> what happens?
overall=0
rm -f "$OUT/c.txt"
grep -a '^# exit code' "$OUT/c.txt" 2>/dev/null | grep -qv ': 0$' && overall=1
echo "    C record file MISSING            -> overall=$overall (expect 1 if fail-closed)"

# case D: file exists but the leg died before writing a marker
overall=0
echo "# sphinx -W --keep-going, from a deleted DOCS/sphinx/_build" > "$OUT/d.txt"
echo "# date (UTC): 2026-10-16T00:00:00Z" >> "$OUT/d.txt"
grep -a '^# exit code' "$OUT/d.txt" | grep -qv ': 0$' && overall=1
echo "    D file present, NO marker line   -> overall=$overall (expect 1 if fail-closed)"

# case E: empty file
overall=0
: > "$OUT/e.txt"
grep -a '^# exit code' "$OUT/e.txt" | grep -qv ': 0$' && overall=1
echo "    E record file EMPTY              -> overall=$overall (expect 1 if fail-closed)"

# case F: the immutability variant, marker missing
overall=0
echo "range: aaa..bbb" > "$OUT/f.txt"
grep -a 'script exit' "$OUT/f.txt" | grep -qv ': 0)' && overall=1
echo "    F immutability variant, no marker-> overall=$overall (expect 1 if fail-closed)"

# case G: two markers, first 0 second 1 (the gitleaks shape) -> must become 1
overall=0
printf '# exit code: 0\n# exit code: 1\n' > "$OUT/g.txt"
grep -a '^# exit code' "$OUT/g.txt" | grep -qv ': 0$' && overall=1
echo "    G two markers 0 then 1           -> overall=$overall (expect 1)"
exit 0
EOF
bash "$OUT/c17.sh"
echo
echo "  why: 'grep -qv P' returns 0 only if some line does NOT match P. With no input"
echo "  lines at all it returns 1, so the '&& overall=1' arm is skipped."
printf '    proof: echo -n "" | grep -qv ": 0$"; echo "empty-input grep -qv exit = $?"\n' > /dev/null
echo -n "" | grep -qv ': 0$'; echo "    empty-input 'grep -qv' exit = $?  (1 = no line selected = arm skipped)"
echo -n "" | grep -q  ': 0$'; echo "    empty-input 'grep -q'  exit = $?  (1 = nothing matched)"

# --------------------------------- C18 did it bite a committed S3 record?
chk "C18 every marker the committed S3 final records rely on, actually present?"
$PY - <<'PYEOF'
import pathlib, re, sys
base = pathlib.Path("EVIDENCE/exp002-d1-s3/gate/final")
# (record file, the grep pattern final_legs.sh uses, the "ok" form it accepts)
checks = [
    ("sphinx.txt",                 r"^# exit code",  ": 0"),
    ("gitleaks.txt",               r"^# exit code",  ": 0"),
    ("immutability-after.txt",     r"script exit",   ": 0)"),
    ("verify-manifest.txt",        r"^# exit code",  ": 0"),
    ("index-selfcheck-s1.txt",     r"^# exit code",  ": 0"),
    ("index-selfcheck-s2.txt",     r"^# exit code",  ": 0"),
    ("index-selfcheck-s3.txt",     r"^# exit code",  ": 0"),
    ("snyk-code-s3-final.txt",     r"^# (exit code|filter exit code)", None),
]
bad = 0
print("    record                        marker lines  values                          verdict")
for name, pat, _ok in checks:
    p = base / name
    if not p.is_file():
        print(f"    {name:28s} FILE MISSING                                              FAIL-OPEN RISK")
        bad += 1
        continue
    lines = [ln for ln in p.read_text(encoding="utf-8", errors="replace").splitlines()
             if re.match(pat, ln)]
    if not lines:
        print(f"    {name:28s} {0:>12d}  {'(none)':32s} FAIL-OPEN RISK")
        bad += 1
        continue
    vals = "; ".join(ln.replace("# exit code", "ec").replace("# filter exit code", "fec")[:34] for ln in lines)
    print(f"    {name:28s} {len(lines):>12d}  {vals[:60]:60s} marker present")
print()
print(f"    records with a missing marker (i.e. where the fail-open could bite): {bad}")
sys.exit(1 if bad else 0)
PYEOF
echo "# python exit code: $? (0 = every committed record carries its marker, so no"
echo "#   recorded S3 result was masked by the C17 fail-open; the defect is latent)"
echo
echo "  cross-check: the values those markers hold, read directly:"
for f in sphinx gitleaks immutability-after verify-manifest index-selfcheck-s1 index-selfcheck-s2 index-selfcheck-s3; do
  printf '    %-24s ' "$f.txt"
  grep -a -E '^# exit code|script exit' "$S3/gate/final/$f.txt" 2>/dev/null | tr '\n' '|'
  echo
done
echo "  and the two legs final_legs.sh aggregates by direct rc, not by grep:"
printf '    static-gate.txt          -> '; grep -a '^# overall' "$S3/gate/final/static-gate.txt" 2>/dev/null || echo "(no '# overall' line)"
printf '    delta-reaudit.txt        -> '; grep -a '^# overall' "$S3/gate/final/delta-reaudit.txt" 2>/dev/null || echo "(no '# overall' line)"
printf '    snyk filter exit code    -> '; grep -a 'filter exit code' "$S3/gate/final/snyk-code-s3-final.txt" 2>/dev/null || echo "(none)"

echo
echo "=================================================================="
echo "# batch 3 finished $(stamp)"
echo "# git HEAD at end: $(git rev-parse HEAD)"
echo "# tracked changes at end: '$(git status --porcelain --untracked-files=no)'"
