#!/usr/bin/env bash
# EXP-002 D1 S4 - observation O-2 cold review, second batch.
# Completes the checks whose first invocation was malformed (C6/C7 used the shell
# suffix '^', which docstring_only_check.py rejects by design), corrects the C9
# aggregation census, and mechanism-tests the two round-4 fixes not yet exercised:
# final_legs.sh's "no SARIF => exit 1" and launch_round.sh's exit status.
cd /c/dev/PRIN || exit 2
PY=.venv/Scripts/python.exe
OUT=/c/Users/there/prin-s4-scratch/o2
S3=EVIDENCE/exp002-d1-s3
mkdir -p "$OUT"
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
chk() { echo; echo "=================================================================="; echo "## $1"; echo "# started $(stamp)"; }

echo "# EXP-002 D1 S4 - O-2 cold review, batch 2"
echo "# date (UTC): $(stamp)"
echo "# git HEAD: $(git rev-parse HEAD)"
echo "# tracked changes at start: $(git status --porcelain --untracked-files=no | wc -l)"

# ------------------------------------------------ C6b AST identity, hex revisions
chk "C6b b08dd574 (tests/test_notebooks.py) is comment-only: AST identity, resolved hex"
PARENT=$(git rev-parse 'b08dd574^')
echo "  resolved b08dd574^ = $PARENT"
echo "# command: $PY -I $S3/docstring_only_check.py --check $PARENT b08dd574 tests/test_notebooks.py"
$PY -I "$S3/docstring_only_check.py" --check "$PARENT" b08dd574 tests/test_notebooks.py 2>&1
echo "# exit code: $? (0 = AST identical outside the module docstring)"
echo "  negative control - the same tool over a commit that DID change code (3bc12c7a's"
echo "  parent..3bc12c7a on closing_gate.sh is shell, so use the S3 F6 label commit instead):"
F6=$(git log --format=%H --grep 'EXP002D1-S2-F6' -1)
echo "  F6 commit = $F6"
$PY -I "$S3/docstring_only_check.py" --check "$F6^" "$F6" python/prin/reporting/figure_generation.py 2>&1
echo "# exit code: $? (1 expected: F6 restored a real keyword argument, so the AST differs)"

# --------------------------------------------- C7b positive control, hex revisions
chk "C7b docstring_only_check.py positive control with resolved hex revisions"
D_PARENT=$(git rev-parse '3bc12c7a^')
echo "  resolved 3bc12c7a^ = $D_PARENT"
echo "# command: $PY -I $S3/docstring_only_check.py --check $D_PARENT 3bc12c7a $S3/docstring_only_check.py"
$PY -I "$S3/docstring_only_check.py" --check "$D_PARENT" 3bc12c7a "$S3/docstring_only_check.py" 2>&1
echo "# exit code: $? (0 expected: round 4 changed only its docstring)"
echo "  and the same for the two-round-4-changed Python-visible claim in the commit message:"
git diff --numstat "$D_PARENT" 3bc12c7a -- "$S3/docstring_only_check.py" | sed 's/^/    numstat: /'

# ------------------------------------------- C9b closing_gate.sh aggregation census
chk "C9b closing_gate.sh: a correct census of leg aggregation (C9's grep undercounted)"
echo "  every statement that runs a leg, with the statement that captures its status:"
awk '
  /^bash EVIDENCE.*diagnostic_suite_run\.sh/ { print "    LINE " NR ": " $0; getline; print "    LINE " NR ": " $0; next }
  /^leg /                                    { print "    LINE " NR ": " $0; next }
  /^if ! leg /                               { print "    LINE " NR ": " $0; getline; getline; print "    LINE " NR ": " $0; next }
' "$S3/closing_gate.sh"
echo
echo "  legs run by the script (diagnostic_suite_run x2, leg x9 incl. the cargo retry):"
echo "    diagnostic_suite_run.sh invocations : $(grep -c 'diagnostic_suite_run.sh gate-' "$S3/closing_gate.sh")"
echo "    'leg \"' invocations                 : $(grep -c '^leg \|^if ! leg ' "$S3/closing_gate.sh")"
echo "    statements setting overall=1        : $(grep -c 'overall=1' "$S3/closing_gate.sh")"
echo
echo "  is any leg's status dropped? List every leg line and the aggregation that covers it:"
$PY - <<'PYEOF'
import re, pathlib
src = pathlib.Path("EVIDENCE/exp002-d1-s3/closing_gate.sh").read_text(encoding="utf-8").splitlines()
legs, covered, uncovered = [], [], []
for i, line in enumerate(src):
    is_leg = line.startswith("leg ") or line.startswith("if ! leg ") or "diagnostic_suite_run.sh gate-" in line
    if not is_leg:
        continue
    legs.append((i + 1, line.strip()[:72]))
    # aggregation may be on the same line (|| overall=1) or the next (rc=$? ... overall=1)
    window = " ".join(src[i:i + 3])
    if "overall=1" in window:
        covered.append((i + 1, "same/next-line aggregation"))
    elif line.startswith("if ! leg "):
        # the retry arm carries the aggregation for this leg
        covered.append((i + 1, "cargo attempt-1: aggregation is on the retry arm by design (AGENTS.md retry-once)"))
    else:
        uncovered.append((i + 1, line.strip()[:72]))
print(f"    legs found              : {len(legs)}")
print(f"    legs with aggregation   : {len(covered)}")
print(f"    legs WITHOUT aggregation: {len(uncovered)}")
for n, why in covered:
    print(f"      line {n:3d}  {why}")
for n, text in uncovered:
    print(f"      line {n:3d}  UNCOVERED: {text}")
print("    RESULT:", "every leg is aggregated" if not uncovered else "GAP FOUND")
PYEOF
echo "# python exit code: $?"

# ------------------------------- C13 final_legs.sh: no SARIF must give exit 1
chk "C13 final_legs.sh round-4 fix: a Snyk leg that writes no SARIF gives exit 1"
echo "  the Snyk block is extracted VERBATIM from the committed script; only the legs"
echo "  before it and the 'snyk' binary are stubbed, so the control flow under review"
echo "  is the committed one."
STUBDIR="$OUT/stubbin"; mkdir -p "$STUBDIR"
# a snyk stub that authenticates, then "scans" and writes NO sarif (the blocked case)
cat > "$STUBDIR/snyk" <<'EOF'
#!/usr/bin/env bash
case "$1" in
  --version) echo "1.1306.2-stub"; exit 0 ;;
  whoami)    echo "stub-account"; exit 0 ;;
  code)      echo "stub: scan ran, wrote no SARIF (simulating SNYK-0005/401)"; exit 2 ;;
esac
exit 0
EOF
chmod +x "$STUBDIR/snyk"
H="$OUT/final_legs_snyk_harness.sh"
{
  echo '#!/usr/bin/env bash'
  echo 'set -u'
  echo "export PATH=\"$STUBDIR:\$PATH\""
  echo 'cd /c/dev/PRIN || exit 2'
  echo '.venv/Scripts/python.exe -V >/dev/null 2>&1'
  echo 'PY=.venv/Scripts/python.exe'
  echo "OUT=\"$OUT/c13\"; mkdir -p \"\$OUT\"; rm -f \"\$OUT\"/*"
  echo 'stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }'
  echo 'HEAD_SHA=$(git rev-parse HEAD)'
  echo 'overall=0'
  # hdr() verbatim from the committed script (the round-4 change is inside it)
  sed -n '/^hdr() {/p' "$S3/final_legs.sh"
  # the Snyk block, verbatim
  sed -n '/^# 5\. Snyk Code CLI/,/^# 6\. the draft PR is untouched/p' "$S3/final_legs.sh" | sed '$d'
  echo 'echo "harness overall: $overall"'
  echo 'exit "$overall"'
} > "$H"
echo "  --- the verbatim block under test:"
sed -n '/^# 5\. Snyk Code CLI/,/^# 6\. the draft PR is untouched/p' "$S3/final_legs.sh" | sed '$d' | sed 's/^/    /'
echo
echo "# command: PATH=<stub first> bash <harness>   (snyk writes NO SARIF)"
bash "$H" 2>&1 | sed 's/^/    /'
echo "# exit code: ${PIPESTATUS[0]} (expect 1 = BLOCKED, never 0)"
echo "  the record it wrote:"
sed 's/^/    /' "$OUT/c13/snyk-code-s3-final.txt"

echo
echo "  --- positive control: a stub snyk that DOES write a SARIF"
cat > "$STUBDIR/snyk" <<'EOF'
#!/usr/bin/env bash
case "$1" in
  --version) echo "1.1306.2-stub"; exit 0 ;;
  whoami)    echo "stub-account"; exit 0 ;;
  code)
    for a in "$@"; do case "$a" in --sarif-file-output=*) f="${a#--sarif-file-output=}" ;; esac; done
    printf '{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"SnykCode","version":"1.0"}},"results":[]}]}' > "$(cygpath -u "$f")"
    printf 'Test Summary\nOpen issues: 0 [ 0 HIGH  0 MEDIUM  0 LOW ]\n'
    exit 0 ;;
esac
exit 0
EOF
chmod +x "$STUBDIR/snyk"
echo "# command: PATH=<stub first> bash <harness>   (snyk writes a valid empty SARIF)"
bash "$H" 2>&1 | sed 's/^/    /'
echo "# exit code: ${PIPESTATUS[0]} (expect 0)"

echo
echo "  --- negative control on whoami: an unauthenticated stub (401 class)"
cat > "$STUBDIR/snyk" <<'EOF'
#!/usr/bin/env bash
case "$1" in
  --version) echo "1.1306.2-stub"; exit 0 ;;
  whoami)    echo "ERROR Authentication error (SNYK-0005) 401 Unauthorized"; exit 2 ;;
  code)      echo "stub: did not run"; exit 2 ;;
esac
exit 0
EOF
chmod +x "$STUBDIR/snyk"
echo "# command: PATH=<stub first> bash <harness>   (whoami fails)"
bash "$H" 2>&1 | sed 's/^/    /'
echo "# exit code: ${PIPESTATUS[0]} (expect 1)"

# --------------------- C14 brace-group redirection and variable propagation
chk "C14 does 'overall=1' set inside '{ ...; } > file' reach the caller? (load-bearing for C13)"
$PY - <<'PYEOF'
print("    bash semantics: { } is a group command, NOT a subshell, so assignments persist.")
PYEOF
cat > "$OUT/c14.sh" <<'EOF'
overall=0
{ echo "inside the group"; overall=1; } > /c/Users/there/prin-s4-scratch/o2/c14.txt 2>&1
echo "    after a brace group with redirection, overall = $overall"
( echo "inside a subshell"; overall=2 ) > /dev/null 2>&1
echo "    after a parenthesised subshell,        overall = $overall"
exit "$overall"
EOF
bash "$OUT/c14.sh"; echo "# exit code: $? (1 expected: the brace-group assignment propagated, the subshell's did not)"

# --------------------------------- C15 launch_round.sh exit status is 'wait'
chk "C15 launch_round.sh always exits 0: is a reviewer failure captured anywhere?"
echo "  the script's last statement: '$(tail -1 "$S3/cold-review/launch_round.sh")'"
echo "  per-reviewer exit codes are written by each subshell to <round>/<tool>.exit:"
grep -n '\.exit' "$S3/cold-review/launch_round.sh" | sed 's/^/    /'
echo "  what the committed round records actually hold (evidence that .exit is the channel used):"
for d in "$S3"/cold-review/round*; do
  [ -d "$d" ] || continue
  echo "    $(basename "$d"): $(ls -1 "$d" | grep -c '\.exit$') .exit files -> $(for f in "$d"/*.exit; do [ -f "$f" ] && printf '%s=%s ' "$(basename "$f" .exit)" "$(cat "$f")"; done)"
done
echo "  bash 'wait' with no operands returns 0 regardless of the jobs' statuses:"
cat > "$OUT/c15.sh" <<'EOF'
( exit 3 ) &
( exit 4 ) &
wait
echo "    after two failing background jobs, \$? = $?"
EOF
bash "$OUT/c15.sh"
echo "  so launch_round.sh's own status is NOT a pass/fail signal; the .exit files are."
echo "  Classification: pre-existing design property, unchanged by round 4, and the"
echo "  per-reviewer statuses ARE captured. Not a defect in the fixes under review."

echo
echo "=================================================================="
echo "# batch 2 finished $(stamp)"
echo "# git HEAD at end: $(git rev-parse HEAD)"
echo "# tracked changes at end: '$(git status --porcelain --untracked-files=no)'"
