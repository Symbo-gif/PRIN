#!/usr/bin/env bash
# Characterize the one failing assertion in isolation, without modifying it.
#
# The required full-suite leg at 814b670c exited 1 on
#   tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression
# with "Throughput ratio 22.07 > 1.30".  DV-032 registers this test as a
# host-sensitive wall-clock ratio and documents it measuring ~1.28-1.32 under
# load, i.e. sitting on its own 1.30 boundary.
#
# This is a DIAGNOSTIC, not a replacement for the required leg and not a
# rerun-until-green: every iteration's outcome is recorded whether it passes or
# fails.  The assertion and the test text are not touched (Testing Standards
# section 7 item 6).
set -u
cd /c/dev/PRIN || exit 2

TEST='tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression'
OUT="$HOME/prin-s4-scratch/isolated-throughput"
mkdir -p "$OUT"

echo "# isolated characterization of the failing throughput assertion"
echo "# date (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "# git HEAD: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)   untracked: $(git status --porcelain | grep -c '^??')"
echo "# test: $TEST"
echo "# note: the test asserts a wall-clock ratio, so ambient host load is part of"
echo "#       the measurement.  Host CPU is sampled before each iteration."
echo

passes=0
fails=0
for i in 1 2 3 4 5; do
  host=$(.venv/Scripts/python.exe -I -c \
    'import psutil; print(f"{psutil.cpu_percent(interval=1.0):.1f}")' 2>/dev/null || echo "n/a")
  echo "== iteration $i   host cpu before: ${host}%"
  t0=$(date -u +%s)
  .venv/Scripts/python.exe -m pytest "$TEST" -p no:cacheprovider --basetemp=.pytest_basetemp \
      -o faulthandler_timeout=300 > "$OUT/iter$i.txt" 2>&1
  rc=$?
  t1=$(date -u +%s)
  line=$(grep -E '=====' "$OUT/iter$i.txt" | tail -1)
  ratio=$(grep -oE 'Throughput ratio [0-9.]+' "$OUT/iter$i.txt" | tail -1)
  echo "   exit: $rc   wall: $((t1 - t0))s"
  echo "   summary: $line"
  if [ -n "$ratio" ]; then echo "   measured: $ratio"; fi
  if [ "$rc" -eq 0 ]; then passes=$((passes + 1)); else fails=$((fails + 1)); fi
  echo
done

echo "# iterations: 5   passed: $passes   failed: $fails"
echo "# finished $(date -u +%Y-%m-%dT%H:%M:%SZ)"
