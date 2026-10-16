#!/usr/bin/env bash
# EXP-002 D1 S4 - observation O-2 cold review: reproductions by measurement on the
# committed S3 round-4 fixes (commits 3bc12c7a and b08dd574).
#
# Read-only with respect to S3's evidence: the pre-fix copy of delta_reaudit.sh is
# extracted from git into scratch, never written into the repository. The one
# deliberate working-tree edit (check C8) is to a tracked, committed source file and
# is restored and byte-verified at the end of that check.
cd /c/dev/PRIN || exit 2
PY=.venv/Scripts/python.exe
OUT=/c/Users/there/prin-s4-scratch/o2
mkdir -p "$OUT"
S3=EVIDENCE/exp002-d1-s3
MOD=python/prin/reporting/figure_generation.py

stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
chk() { echo; echo "=================================================================="; echo "## $1"; echo "# started $(stamp)"; }

echo "# EXP-002 D1 S4 - O-2 cold review reproductions"
echo "# date (UTC): $(stamp)"
echo "# git HEAD: $(git rev-parse HEAD)"
echo "# tracked changes at start: $(git status --porcelain --untracked-files=no | wc -l)"
echo "# host: $(uname -srm)   $($PY -V 2>&1)"
echo "# bash: $BASH_VERSION"

# ---------------------------------------------------------------- C1 syntax
chk "C1  bash -n on the five committed shell instruments under review"
for f in "$S3/closing_gate.sh" "$S3/final_legs.sh" "$S3/delta_reaudit.sh" \
         "$S3/diagnostic_suite_run.sh" "$S3/cold-review/launch_round.sh"; do
  bash -n "$f"; echo "  bash -n $f -> exit $?"
done

# --------------------------------------------- C2/C3 diagnostic_suite_run.sh
chk "C2  diagnostic_suite_run.sh with NO label (round-4 fix: must exit 2, not 1/127)"
echo "# command: bash $S3/diagnostic_suite_run.sh"
bash "$S3/diagnostic_suite_run.sh" 2>&1; echo "# exit code: $?"

chk "C3  diagnostic_suite_run.sh with a label that tries to climb out of scratch"
echo "# command: bash $S3/diagnostic_suite_run.sh ../evil tests/"
bash "$S3/diagnostic_suite_run.sh" ../evil tests/ 2>&1; echo "# exit code: $?"
echo "# command: bash $S3/diagnostic_suite_run.sh .hidden tests/"
bash "$S3/diagnostic_suite_run.sh" .hidden tests/ 2>&1; echo "# exit code: $?"
echo "  (a rejected label must not have created a directory:)"
ls -d /c/Users/there/prin-s4-scratch/evil /c/Users/there/prin-s3-scratch/evil 2>&1 | sed 's/^/    /'

# ------------------------------------------------------- C4 launch_round.sh
chk "C4  launch_round.sh argument validation (no reviewer is launched on these paths)"
echo "# command: bash $S3/cold-review/launch_round.sh   (no argument)"
bash "$S3/cold-review/launch_round.sh" 2>&1; echo "# exit code: $?"
echo "# command: bash $S3/cold-review/launch_round.sh ../evil"
bash "$S3/cold-review/launch_round.sh" ../evil 2>&1; echo "# exit code: $?"

# ------------------------------------------- C5 launch_round.sh mkdir -p fix
chk "C5  launch_round.sh creates the round directory (round-4 fix) - stubbed copy"
# The committed script launches three reviewer CLIs; this copy keeps its argument
# validation and mkdir line verbatim and replaces only the three launch lines, so
# the fix under review (mkdir -p before the redirections) is exercised for real.
STUB=/c/Users/there/prin-s4-scratch/o2/launch_round_stub.sh
R=/c/Users/there/prin-s4-scratch/o2/rounds
mkdir -p "$R"; rm -rf "$R"/*
{
  sed -n '1,/^mkdir -p "\$D"/p' "$S3/cold-review/launch_round.sh" \
    | sed "s#^R=/c/Users/there/prin-s3-scratch/review#R=$R#"
  cat <<'STUBTAIL'
echo "stub: round directory exists -> $([ -d "$D" ] && echo yes || echo NO)"
echo "stub: writable -> $([ -w "$D" ] && echo yes || echo NO)"
( true > "$D/devin-stdout.txt" 2>&1; echo "exit=$?" > "$D/devin.exit" ) &
( true > "$D/agy-stdout.txt"   2>&1; echo "exit=$?" > "$D/agy.exit" ) &
( true > "$D/qwen-stdout.txt"  2>&1; echo "exit=$?" > "$D/qwen.exit" ) &
wait
STUBTAIL
} > "$STUB"
echo "# the verbatim lines taken from the committed script:"
sed -n '1,/^mkdir -p "\$D"/p' "$S3/cold-review/launch_round.sh" | sed 's/^/    /'
echo "# command: bash <stub> round5"
bash "$STUB" round5 2>&1; echo "# exit code: $?"
echo "  contents of $R/round5 :"
ls -1 "$R/round5" 2>&1 | sed 's/^/    /'
echo "  --- negative control: the SAME stub with 'mkdir -p' removed (the pre-fix shape)"
NOFIX=/c/Users/there/prin-s4-scratch/o2/launch_round_nofix.sh
grep -v '^mkdir -p "\$D"' "$STUB" > "$NOFIX"
rm -rf "$R"/*
echo "# command: bash <stub-without-mkdir> round5"
bash "$NOFIX" round5 2>&1; echo "# exit code: $?"
echo "  contents of $R afterwards:"
ls -1 "$R" 2>&1 | sed 's/^/    /'

# ------------------------------------------- C6 b08dd574 is comment-only
chk "C6  b08dd574 (tests/test_notebooks.py) is comment-only: AST identity"
echo "# command: $PY -I $S3/docstring_only_check.py --check b08dd574^ b08dd574 tests/test_notebooks.py"
$PY -I "$S3/docstring_only_check.py" --check 'b08dd574^' b08dd574 tests/test_notebooks.py 2>&1
echo "# exit code: $?"
echo "  diff --numstat (added/deleted lines):"
git diff --numstat 'b08dd574^' b08dd574 -- tests/test_notebooks.py | sed 's/^/    /'
echo "  every changed line is a comment (no non-'#' line in the diff body):"
git diff -U0 'b08dd574^' b08dd574 -- tests/test_notebooks.py \
  | grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' | grep -vcE '^[+-]#' | sed 's/^/    non-comment changed lines: /'

# ------------------------- C7 docstring_only_check.py docstring claim (both revs)
chk "C7  docstring_only_check.py: the membership test really runs per revision"
echo "# a path tracked at HEAD but NOT at fd8854ed must be refused (exit 2), proving"
echo "# the test is applied to revision A as well as revision B:"
echo "# command: $PY -I $S3/docstring_only_check.py --check fd8854ed HEAD $S3/index_selfcheck.py"
$PY -I "$S3/docstring_only_check.py" --check fd8854ed HEAD "$S3/index_selfcheck.py" 2>&1
echo "# exit code: $?"
echo "  positive control - a path tracked at both revisions, docstring-only change:"
echo "# command: $PY -I $S3/docstring_only_check.py --check 3bc12c7a^ 3bc12c7a $S3/docstring_only_check.py"
$PY -I "$S3/docstring_only_check.py" --check '3bc12c7a^' 3bc12c7a "$S3/docstring_only_check.py" 2>&1
echo "# exit code: $?"

# ------------------------------------------- C8 delta_reaudit.sh trap order
chk "C8  delta_reaudit.sh trap order: red-before (pre-fix) / green-after (committed)"
PREFIX=/c/Users/there/prin-s4-scratch/o2/delta_reaudit_prefix.sh
git show "3bc12c7a^:$S3/delta_reaudit.sh" > "$PREFIX"
echo "  the only difference between the pre-fix copy and the committed script:"
diff "$PREFIX" "$S3/delta_reaudit.sh" | sed 's/^/    /'
GOOD_SHA=$(git show "HEAD:$MOD" | sha256sum | cut -d' ' -f1)
echo "  HEAD blob sha256 of $MOD: $GOOD_SHA"

MARKER="# S4-O2-C8-UNCOMMITTED-EDIT"
run_case() {  # $1 = label, $2 = script
  git restore -- "$MOD"
  printf '\n%s\n' "$MARKER" >> "$MOD"
  local before after
  before=$(sha256sum "$MOD" | cut -d' ' -f1)
  echo "  [$1] uncommitted edit applied; module sha256 $before"
  echo "  [$1] command: bash $2"
  bash "$2" > "/c/Users/there/prin-s4-scratch/o2/c8-$1.txt" 2>&1
  local rc=$?
  after=$(sha256sum "$MOD" | cut -d' ' -f1)
  echo "  [$1] exit code: $rc"
  echo "  [$1] refusal message: $(grep -a 'refusing to run' "/c/Users/there/prin-s4-scratch/o2/c8-$1.txt" || echo '(none)')"
  echo "  [$1] module sha256 after the run: $after"
  if [ "$after" = "$before" ]; then
    echo "  [$1] VERDICT: the uncommitted edit SURVIVED"
  elif [ "$after" = "$GOOD_SHA" ]; then
    echo "  [$1] VERDICT: the uncommitted edit was DESTROYED (restored to HEAD)"
  else
    echo "  [$1] VERDICT: module is in an unexpected state"
  fi
}
echo
echo "  --- red before: the PRE-FIX copy (trap armed before the clean-tree guard)"
run_case prefix "$PREFIX"
echo
echo "  --- green after: the COMMITTED script (trap armed after the guard)"
run_case committed "$S3/delta_reaudit.sh"
git restore -- "$MOD"
echo
echo "  tree restored. module sha256 now: $(sha256sum "$MOD" | cut -d' ' -f1)"
echo "  equals the HEAD blob: $([ "$(sha256sum "$MOD" | cut -d' ' -f1)" = "$GOOD_SHA" ] && echo yes || echo NO)"
echo "  git status --porcelain (tracked): '$(git status --porcelain --untracked-files=no)'"

# ------------------------- C9 closing_gate.sh aggregation, mechanism test
chk "C9  closing_gate.sh: every leg is aggregated, and 'overall' really propagates"
echo "  leg invocations in the committed script, and whether each is aggregated:"
grep -nE '^(leg |bash EVIDENCE|if ! leg )' "$S3/closing_gate.sh" | sed 's/^/    /'
echo "  count of leg/bash invocations            : $(grep -cE '^(leg |bash EVIDENCE|if ! leg )' "$S3/closing_gate.sh")"
echo "  count carrying '|| overall=1' or rc=\$? : $(grep -E '^(leg |bash EVIDENCE|if ! leg )' "$S3/closing_gate.sh" | grep -cE '\|\| overall=1|rc=\$\?')"
echo "  last two statements of the script:"
tail -2 "$S3/closing_gate.sh" | sed 's/^/    /'
echo
echo "  --- mechanism test: the committed leg() function verbatim, driven by stubs"
HARNESS=/c/Users/there/prin-s4-scratch/o2/leg_harness.sh
{
  echo '#!/usr/bin/env bash'
  echo 'set -u'
  echo 'LEGS=/c/Users/there/prin-s4-scratch/o2/legs-harness.txt'
  echo ': > "$LEGS"'
  echo 'overall=0'
  echo 'stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }'
  # the leg() function body, extracted verbatim from the committed script
  sed -n '/^leg() {$/,/^}$/p' "$S3/closing_gate.sh"
  echo 'leg "passing leg" true || overall=1'
  echo 'leg "failing leg" false || overall=1'
  echo 'leg "exit-2 leg" bash -c "exit 2" || overall=1'
  echo 'echo "# overall: $overall" >> "$LEGS"'
  echo 'exit "$overall"'
} > "$HARNESS"
echo "  extracted leg() definition:"
sed -n '/^leg() {$/,/^}$/p' "$S3/closing_gate.sh" | sed 's/^/    /'
echo "# command: bash <harness with one failing leg>"
bash "$HARNESS"; echo "# exit code: $? (expect 1)"
echo "  harness legs.txt:"
sed 's/^/    /' /c/Users/there/prin-s4-scratch/o2/legs-harness.txt
{
  echo '#!/usr/bin/env bash'
  echo 'set -u'
  echo 'LEGS=/c/Users/there/prin-s4-scratch/o2/legs-harness2.txt'
  echo ': > "$LEGS"'
  echo 'overall=0'
  echo 'stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }'
  sed -n '/^leg() {$/,/^}$/p' "$S3/closing_gate.sh"
  echo 'leg "passing leg A" true || overall=1'
  echo 'leg "passing leg B" true || overall=1'
  echo 'echo "# overall: $overall" >> "$LEGS"'
  echo 'exit "$overall"'
} > /c/Users/there/prin-s4-scratch/o2/leg_harness2.sh
echo "# command: bash <harness with all legs passing>"
bash /c/Users/there/prin-s4-scratch/o2/leg_harness2.sh; echo "# exit code: $? (expect 0)"

# --------------------- C10 wc -l padding under Git Bash (the guard's compare)
chk "C10 the clean-tree guards compare \$(... | wc -l) with -eq: does wc pad on this host?"
echo "  raw bytes of 'git status --porcelain --untracked-files=no | wc -l' on a clean tree:"
git status --porcelain --untracked-files=no | wc -l | od -c | head -2 | sed 's/^/    /'
echo "  the guard as written, evaluated: $([ "$(git status --porcelain --untracked-files=no | wc -l)" -eq 0 ] && echo PASSES || echo FAILS)"
printf 'x\ny\n' | { echo "  padded-input control: [ \"$(printf '   0')\" -eq 0 ] -> $([ "   0" -eq 0 ] && echo PASSES || echo FAILS)"; }

# ------------------------------- C11 the F2 bound tests still pass (5 tests)
chk "C11 tests/test_notebooks.py bound tests still pass after the comment change"
export PATH="/c/Program Files/Git/bin:$PATH"
echo "# command: $PY -m pytest tests/test_notebooks.py -k 'timeout or contract or cells or directory' -q --basetemp=.pytest_basetemp -p no:cacheprovider"
$PY -m pytest tests/test_notebooks.py -k "timeout or contract or cells or directory" -q \
  --basetemp=.pytest_basetemp -p no:cacheprovider 2>&1 | tail -8
echo "# exit code: ${PIPESTATUS[0]}"

# ------------------- C12 the comment's arithmetic, recomputed independently
chk "C12 the numbers the b08dd574 comment cites, recomputed from the committed constants"
$PY - <<'PYEOF'
import math, json, subprocess, pathlib
src = pathlib.Path("tests/test_notebooks.py").read_text(encoding="utf-8")
def grab(name):
    start = src.index(name + " = {")
    end = src.index("}", start)
    body = src[start:end+1]
    return {k: float(v) for k, v in (
        (p.split(":")[0].strip().strip('"'), p.split(":")[1].strip().rstrip(","))
        for p in body[body.index("{")+1:body.rindex("}")].strip().splitlines() if ":" in p)}
bounds = grab("NOTEBOOK_CELL_TIMEOUT_SECONDS")
recorded = grab("RECORDED_CONTENDED_MAX_SECONDS")
margin = float(src.split("BOUND_MARGIN = ")[1].split("\n")[0])
rounding = float(src.split("BOUND_ROUNDING_SECONDS = ")[1].split("\n")[0])
quiet = {"01_oscillosim_quickstart.ipynb": 73.3, "02_clevr_n_binding.ipynb": 71.1,
         "03_custom_coupling.ipynb": 44.5, "04_torch_bridge.ipynb": 37.0}
insuite = {"01_oscillosim_quickstart.ipynb": 678.9, "02_clevr_n_binding.ipynb": 2975.0,
           "03_custom_coupling.ipynb": 367.3, "04_torch_bridge.ipynb": 382.1}
print(f"  BOUND_MARGIN={margin}  BOUND_ROUNDING_SECONDS={rounding}")
print("  notebook                              bound  recorded  rule  quiet  bound/quiet  in-suite/quiet")
ratios = []
slow = []
for n in sorted(bounds):
    rule = math.ceil(margin * recorded[n] / rounding) * rounding
    ok = "OK" if rule == bounds[n] else f"MISMATCH({rule})"
    r = bounds[n] / quiet[n]
    ratios.append(r)
    s = insuite[n] / quiet[n]
    slow.append(s)
    print(f"  {n:36s} {bounds[n]:6.0f} {recorded[n]:9.2f} {ok:>13s} {quiet[n]:6.1f} {r:10.1f} {s:14.1f}")
print(f"  bound/quiet ratio range      : {min(ratios):.1f} - {max(ratios):.1f}   comment claims '37-152'")
print(f"  in-suite/quiet slowdown range: {min(slow):.1f} - {max(slow):.1f}   comment claims '8-42x'")
print(f"  paired-experiment slowdown   : {3484.0/80.7:.1f}x               comment claims '43x'")
print(f"  quiet-host duration range    : {min(quiet.values()):.1f} - {max(quiet.values()):.1f} s   comment claims '37-73 s'")
PYEOF
echo "# exit code: $?"

echo
echo "=================================================================="
echo "# O-2 reproduction script finished $(stamp)"
echo "# git HEAD at end: $(git rev-parse HEAD)"
echo "# tracked changes at end: '$(git status --porcelain --untracked-files=no)'"
