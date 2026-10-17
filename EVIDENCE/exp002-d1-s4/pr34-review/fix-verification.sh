# Runner for the fix verification
# copied from /c/Users/there/prin-s4-scratch/verify_fix2.sh at 2026-10-17T19:03:58Z

#!/usr/bin/env bash
# Verify the platform-scoped digest tie in parity/test_parity_publication.py.
#
# Two harness bugs from the first attempt are fixed here, and both are recorded
# because each would have produced a misleading result:
#   (1) PYTHONPATH was exported as an MSYS path (/c/Users/...). Native Windows
#       Python never sees it, so `-p negctl` died with "No module named
#       'negctl'" and V2/V3 measured nothing. Windows paths with `;` separators
#       are required.
#   (2) `cmd | tail -4; rc=$?` captured tail's status, not the command's, so a
#       real ruff E501 was reported as "exit code: 0". Every status below is now
#       taken from ${PIPESTATUS[0]} or from an unpiped run.
#
#   V1  normal run on this Windows host: the record's platform matches, so the
#       byte-exact branch is taken for all 39 files. Must PASS.
#   V2  NEGCTL=bogus-platform: the record's platform is patched to one this host
#       is not. The 11 .tex tables must STILL be byte-exact, the 28 figures take
#       the structural branch. Must PASS - and it proves the branch is selected
#       by the record's declared platform, not by the host OS.
#   V3  NEGCTL=corrupt-digest: one figure's expected digest is corrupted while the
#       platform still matches. Must FAIL - proving the byte-exact comparison is
#       still load-bearing and was not turned into a no-op.
#   V4  static gate over the changed file.
set -u
cd /c/dev/PRIN || exit 2
export PATH="/c/Program Files/Git/bin:$PATH"
export PYTHONPATH="C:/Users/there/prin-s4-scratch${PYTHONPATH:+;$PYTHONPATH}"
PY=.venv/Scripts/python.exe
MOD=parity/test_parity_publication.py
FLAGS=(-q -rf --basetemp=.pytest_basetemp -o faulthandler_timeout=300 -p no:cacheprovider)
overall=0
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }

echo "# platform-scoped digest tie - verification (harness bugs 1 and 2 fixed)"
echo "# date (UTC): $(stamp)"
echo "# git HEAD: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)"
echo "# host platform: $($PY -c 'import platform;print(platform.platform())')"
echo "# record platform: $($PY -c "import json;print(json.load(open('benchmarks/results/EXP-002/RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu/reproduction.json',encoding='utf-8'))['environment']['platform'])")"
echo "# module sha256: $(sha256sum "$MOD" | cut -d' ' -f1)"
echo "# PYTHONPATH: $PYTHONPATH"
echo "# plugin resolvable: $($PY -c 'import negctl; print("yes", negctl.__file__)' 2>&1 | head -1)"

echo
echo "===== V1 normal run on the authoring platform (must PASS, byte-exact) ====="
echo "# started $(stamp)"
$PY -m pytest "$MOD" "${FLAGS[@]}" > /tmp/v1.txt 2>&1; rc=$?
tail -4 /tmp/v1.txt
echo "# exit code: $rc (must be 0)"
echo "# ended $(stamp)"
[ "$rc" -eq 0 ] || overall=1

echo
echo "===== V2 NEGCTL=bogus-platform (record's platform != this host) ====="
echo "# started $(stamp)"
NEGCTL=bogus-platform $PY -m pytest "$MOD" "${FLAGS[@]}" -p negctl > /tmp/v2.txt 2>&1; rc=$?
grep -a 'NEGCTL active' /tmp/v2.txt | sed 's/^/  /'
tail -4 /tmp/v2.txt
echo "# exit code: $rc (must be 0)"
echo "# ended $(stamp)"
[ "$rc" -eq 0 ] || overall=1
echo "  collected count (must equal V1's, so nothing was deselected):"
grep -aoE 'collected [0-9]+ item' /tmp/v2.txt | sed 's/^/    /'

echo
echo "===== V3 NEGCTL=corrupt-digest (must FAIL: the tie is still load-bearing) ====="
echo "# started $(stamp)"
NEGCTL=corrupt-digest $PY -m pytest "$MOD" -k "reference_arm_reproduces" "${FLAGS[@]}" -p negctl > /tmp/v3.txt 2>&1; rc=$?
grep -a 'NEGCTL active' /tmp/v3.txt | sed 's/^/  /'
grep -aE '^(FAILED|E  )' /tmp/v3.txt | head -6 | sed 's/^/  /'
tail -3 /tmp/v3.txt
echo "# exit code: $rc (must be 1 - a corrupted expectation must be caught)"
echo "# ended $(stamp)"
if [ "$rc" -eq 1 ]; then
  echo "  V3 correctly FAILED: the byte-exact comparison is load-bearing on this platform"
else
  echo "  V3 DID NOT FAIL: the byte-exact comparison would be vacuous"; overall=1
fi

echo
echo "===== V4 static gate over the changed file (statuses taken unpiped) ====="
echo "# command: .venv/Scripts/ruff.exe check $MOD"
.venv/Scripts/ruff.exe check "$MOD" > /tmp/v4a.txt 2>&1; rc=$?; tail -2 /tmp/v4a.txt; echo "# exit code: $rc"; [ "$rc" -eq 0 ] || overall=1
echo "# command: .venv/Scripts/ruff.exe format --check $MOD"
.venv/Scripts/ruff.exe format --check "$MOD" > /tmp/v4b.txt 2>&1; rc=$?; tail -2 /tmp/v4b.txt; echo "# exit code: $rc"; [ "$rc" -eq 0 ] || overall=1
echo "# command: .venv/Scripts/mypy.exe --strict $MOD"
.venv/Scripts/mypy.exe --strict "$MOD" > /tmp/v4c.txt 2>&1; rc=$?; tail -2 /tmp/v4c.txt; echo "# exit code: $rc"; [ "$rc" -eq 0 ] || overall=1
echo "# command: $PY -m bandit -r parity -c pyproject.toml"
$PY -m bandit -r parity -c pyproject.toml > /tmp/v4d.txt 2>&1; rc=$?
grep -aE 'Total issues|Low:|Medium:|High:|Total lines' /tmp/v4d.txt | head -6 | sed 's/^/  /'
echo "# exit code: $rc"; [ "$rc" -eq 0 ] || overall=1

echo
echo "===== V5 the new mechanism test, run explicitly ====="
$PY -m pytest "$MOD" -k "digest_tie_is_scoped" -v --basetemp=.pytest_basetemp -p no:cacheprovider > /tmp/v5.txt 2>&1; rc=$?
tail -3 /tmp/v5.txt
echo "# exit code: $rc"; [ "$rc" -eq 0 ] || overall=1

echo
echo "# overall: $overall (0 = V1 pass, V2 pass, V3 fail-as-required, V4 clean, V5 pass)"
echo "# finished $(stamp)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)"
exit "$overall"
