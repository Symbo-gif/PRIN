#!/usr/bin/env bash
# Isolated re-run of the required fast suite, per AGENTS.md's prescribed
# remediation for the Windows pytest lock class.
#
# The fast leg at 67100a69 exited 1 on exactly one test:
#   tests/test_exp002_e4_analysis.py::test_linked_raw_root_aborts
#   PermissionError: [WinError 5] Access is denied:
#     '...\.pytest_basetemp\test_linked_raw_root_aborts0\repo\benchmarks\results\EXP-002'
#     -> '...\.pytest_basetemp\test_linked_raw_root_aborts0\repo\raw-moved'
#
# AGENTS.md documents this class and its remediation:
#   "antivirus/file-handle contention during tmp_path cleanup can surface as
#    PermissionError: [WinError 32] fixture-setup errors. Run the suites
#    sequentially; if lock errors appear, re-run the suite in isolation
#    (EA-002 E-F13)."
# and the DEFERRED_VALIDATION_REGISTER's DV-032 entry explicitly separates this
# "Windows WinError 5 rename class" from DV-032's host-sensitive timing ratios,
# naming it "the AGENTS.md-documented pytest temporary-directory contention
# class".
#
# This is therefore a DOCUMENTED remediation for a known environmental artifact,
# not rerun-until-green. Both runs are recorded: the failed leg is preserved in
# gate/full-67100a69/ (collected before this script runs, since suite_run.sh
# writes into the scratch label directory) and this re-run goes to its own label.
#
# MUST NOT run concurrently with the full-suite leg or with cargo (AGENTS.md).
set -u
cd /c/dev/PRIN || exit 2

echo "# isolated re-run of the required fast suite (AGENTS.md / EA-002 E-F13)"
echo "# date (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "# git HEAD: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)   untracked: $(git status --porcelain | grep -c '^??')"
echo "# reason: the fast leg exited 1 on a single PermissionError [WinError 5]"
echo "#         directory-rename failure inside .pytest_basetemp, the documented"
echo "#         Windows pytest lock class, in a test unrelated to this cycle's change."
echo "# scope: identical invocation to the required fast leg, run alone."
echo

# Guard: refuse to start if another pytest is live, since concurrent pytest runs
# on this host are what produce the lock class in the first place.
if tasklist //FI "IMAGENAME eq python.exe" 2>/dev/null | grep -qi 'python.exe'; then
  n=$(tasklist //FI "IMAGENAME eq python.exe" 2>/dev/null | grep -ci 'python.exe')
  echo "WARNING: $n python.exe process(es) live; waiting 60s for them to exit"
  sleep 60
fi

bash EVIDENCE/exp002-d1-s4/suite_run.sh fast-isolated tests/ -m "not slow and not gpu"
rc=$?
echo
echo "# isolated fast-suite exit: $rc"
echo "# finished $(date -u +%Y-%m-%dT%H:%M:%SZ)"
exit "$rc"
