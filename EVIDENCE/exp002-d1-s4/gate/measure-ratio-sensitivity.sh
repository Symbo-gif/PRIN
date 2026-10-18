#!/usr/bin/env bash
# Measure the process-CPU overhead ratio under a saturated host, with and without
# a CPU-hogging daemon, so the sensitivity of _DAEMON_CPU_RATIO_LIMIT is recorded
# as a number rather than asserted.
#
# pytest prints no ratio on a PASS, so the plugin mode "report"/"cpu-report" drops
# the limit to 0.0 to force the assertion to fail and reveal the measured value.
set -u
cd /c/dev/PRIN || exit 2

TEST='tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression'
OUT="$HOME/prin-s4-scratch/dv032-ratio-under-load"
mkdir -p "$OUT"
export PYTHONPATH="C:/Users/there/prin-s4-scratch"

host_cpu() {
  .venv/Scripts/python.exe -c "import psutil;print(f'{psutil.cpu_percent(interval=1.0):.1f}')" 2>/dev/null || echo n/a
}

run_mode() {  # run_mode <mode> <label>
  DV032_NEGCTL="$1" .venv/Scripts/python.exe -m pytest "$TEST" -p dv032negctl \
      -p no:cacheprovider --basetemp=.pytest_basetemp \
      > "$OUT/$2.txt" 2>&1
  local rc=$?
  local ratio
  ratio=$(grep -oE 'overhead ratio [0-9.]+' "$OUT/$2.txt" | tail -1)
  echo "  $2 : rc=$rc   host cpu $(host_cpu)%   ${ratio:-<no ratio reported>}"
}

echo "# ratio sensitivity under host saturation"
echo "# date (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "# git HEAD: $(git rev-parse HEAD)"
echo
echo "== quiet host =="
run_mode report quiet-report
run_mode cpu-report quiet-cpu-report
echo

echo "== starting load: one busy process per logical CPU =="
PIDS=""
N=$(.venv/Scripts/python.exe -c "import os;print(os.cpu_count() or 4)")
for ((i = 0; i < N; i++)); do
  .venv/Scripts/python.exe -c "while True: pass" &
  PIDS="$PIDS $!"
done
sleep 4
echo "  host cpu under load: $(host_cpu)%   (spawned $N)"
run_mode report loaded-report
run_mode cpu-report loaded-cpu-report
for p in $PIDS; do kill "$p" 2>/dev/null; done
wait 2>/dev/null
sleep 2
echo
echo "  host cpu after load removed: $(host_cpu)%"
echo
echo "Reading: 'report' is the ratio with a normal daemon; 'cpu-report' adds a"
echo "3.0 s-per-inference CPU hog.  The bound is 1.60.  If the hog does not lift"
echo "the loaded ratio above the bound, the bound has reduced sensitivity under"
echo "saturation and that must be recorded rather than claimed away."
echo "# finished $(date -u +%Y-%m-%dT%H:%M:%SZ)"
