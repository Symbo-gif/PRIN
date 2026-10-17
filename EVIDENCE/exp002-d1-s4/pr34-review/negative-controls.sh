# Runner for the four negative controls
# copied from /c/Users/there/prin-s4-scratch/negcontrols.sh at 2026-10-17T19:03:58Z

#!/usr/bin/env bash
# The four negative controls for the platform-scoped digest tie, with the plugin
# patching `item.module` (the module pytest actually collected) rather than a
# same-named but distinct `parity.*` module object.
#
# Expected outcomes, and what each proves:
#   corrupt-figure        FAIL  - the byte-exact branch is live on the authoring platform
#   corrupt-tex           FAIL  - tables are byte-exact on the authoring platform
#   bogus+corrupt-figure  PASS  - off-platform, figures take the structural branch
#   bogus+corrupt-tex     FAIL  - off-platform, tables are STILL byte-exact
# The first and third are the same corruption with only the platform differing, so
# together they prove the branch is selected by the record's declared platform.
set -u
cd /c/dev/PRIN || exit 2
export PATH="/c/Program Files/Git/bin:$PATH"
export PYTHONPATH="C:/Users/there/prin-s4-scratch${PYTHONPATH:+;$PYTHONPATH}"
PY=.venv/Scripts/python.exe
MOD=parity/test_parity_publication.py
FLAGS=(-q -rf --basetemp=.pytest_basetemp -o faulthandler_timeout=300 -p no:cacheprovider -p negctl)
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
overall=0

echo "# negative controls for the platform-scoped digest tie"
echo "# date (UTC): $(stamp)"
echo "# git HEAD: $(git rev-parse HEAD)"
echo "# module sha256: $(sha256sum "$MOD" | cut -d' ' -f1)"
echo "# host platform: $($PY -c 'import platform;print(platform.platform())')"

run_mode() {  # $1 = NEGCTL mode, $2 = expected exit code, $3 = what it proves
  echo
  echo "=================================================================="
  echo "## NEGCTL=$1   (expected exit $2)"
  echo "## proves: $3"
  echo "# command: NEGCTL=$1 $PY -m pytest $MOD -k reference_arm_reproduces ${FLAGS[*]}"
  echo "# started $(stamp)"
  NEGCTL="$1" $PY -m pytest "$MOD" -k "reference_arm_reproduces" "${FLAGS[@]}" > "/tmp/nc-$1.txt" 2>&1
  rc=$?
  grep -a 'NEGCTL' "/tmp/nc-$1.txt" | sed 's/^/  /'
  grep -aE '^(FAILED|ERROR)' "/tmp/nc-$1.txt" | head -4 | sed 's/^/  /'
  tail -2 "/tmp/nc-$1.txt" | sed 's/^/  /'
  echo "# exit code: $rc (expected $2)"
  echo "# ended $(stamp)"
  if [ "$rc" -eq "$2" ]; then
    echo "  RESULT: as expected"
  else
    echo "  RESULT: UNEXPECTED - this control did not measure what it claims"
    overall=1
  fi
}

run_mode corrupt-figure       1 "the byte-exact comparison is live on the authoring platform (not a no-op)"
run_mode corrupt-tex          1 "tables are byte-exact on the authoring platform"
run_mode bogus+corrupt-figure 0 "off-platform the figure tie is correctly relaxed to the structural branch"
run_mode bogus+corrupt-tex    1 "off-platform the TABLE tie is still byte-exact - tables were not relaxed"

echo
echo "=================================================================="
echo "## V1 the unmodified run on this host (all 94 tests, no control)"
echo "# started $(stamp)"
$PY -m pytest "$MOD" "${FLAGS[@]/-p negctl/}" > /tmp/nc-plain.txt 2>&1; rc=$?
tail -3 /tmp/nc-plain.txt | sed 's/^/  /'
echo "# exit code: $rc (must be 0)"
[ "$rc" -eq 0 ] || overall=1

echo
echo "# overall: $overall (0 = every control produced its expected outcome)"
echo "# finished $(stamp)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)"
exit "$overall"
