#!/usr/bin/env bash
# Verify the DV-032 replacement for test_no_gpu_throughput_regression.
#
# A robustness fix that can never fail is worse than the flaky original, so this
# proves BOTH directions:
#   * positive: the test passes repeatedly on a quiet host AND on a host
#     saturated with one busy process per logical CPU (the condition that
#     produced the original 22.07 / 2.13 / 3.42 failures);
#   * negative: each new assertion still fails when the daemon is genuinely
#     broken -- a CPU-hogging daemon must trip the ratio, an erroring daemon must
#     trip the deterministic error/dlq counts.
#
# Aggregation is fail-closed by direct rc capture (never by grepping a record),
# which is the EXP002D1-S4-F1 lesson.
set -u
cd /c/dev/PRIN || exit 2

TEST='tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression'
SCRATCH="$HOME/prin-s4-scratch"
OUT="$SCRATCH/dv032-verify"
mkdir -p "$OUT"
# Native Windows Python needs a Windows-style PYTHONPATH; an MSYS /c/... path is
# invisible to it, which silently made an earlier negative control measure nothing.
export PYTHONPATH="C:/Users/there/prin-s4-scratch"
export DV032_NEGCTL=""

overall=0
note() { printf '%s\n' "$*"; }

run_pytest() {  # run_pytest <label> <expect: pass|fail>
  local label="$1" expect="$2"
  .venv/Scripts/python.exe -m pytest "$TEST" -p dv032negctl -p no:cacheprovider \
      --basetemp=.pytest_basetemp -o faulthandler_timeout=300 \
      > "$OUT/$label.txt" 2>&1
  local rc=$?
  local summary
  summary=$(grep -E '=====.*(passed|failed)' "$OUT/$label.txt" | tail -1)
  local verdict
  if [ "$expect" = pass ] && [ "$rc" -eq 0 ]; then verdict=OK
  elif [ "$expect" = fail ] && [ "$rc" -ne 0 ]; then verdict=OK
  else verdict="MISMATCH"; overall=1; fi
  note "  [$verdict] $label  expected=$expect  rc=$rc"
  note "         $summary"
  local detail
  detail=$(grep -oE 'Daemon process-CPU overhead ratio [0-9.]+ > [0-9.]+|daemon reported [0-9]+ inference errors|daemon dead-lettered [0-9]+ states|Throughput ratio [0-9.]+' "$OUT/$label.txt" | tail -1)
  [ -n "$detail" ] && note "         measured: $detail"
  return 0
}

load_start() {
  LOAD_PIDS=""
  local n
  n=$(.venv/Scripts/python.exe -c "import os;print(os.cpu_count() or 4)")
  local i
  for ((i = 0; i < n; i++)); do
    .venv/Scripts/python.exe -c "while True: pass" &
    LOAD_PIDS="$LOAD_PIDS $!"
  done
  sleep 4
}
load_stop() {
  for p in $LOAD_PIDS; do kill "$p" 2>/dev/null; done
  wait 2>/dev/null
  sleep 3
}
host_cpu() {
  .venv/Scripts/python.exe -c "import psutil;print(f'{psutil.cpu_percent(interval=1.0):.1f}')" 2>/dev/null || echo n/a
}

note "# DV-032 fix verification"
note "# date (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
note "# git HEAD: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)"
note "# test: $TEST"
note

note "== 0. static checks on the changed file =="
.venv/Scripts/ruff check tests/test_acceptance_subconscious.py > "$OUT/ruff-check.txt" 2>&1
rc=$?; note "  ruff check rc=$rc : $(tail -1 "$OUT/ruff-check.txt")"; [ "$rc" -eq 0 ] || overall=1
.venv/Scripts/ruff format --check tests/test_acceptance_subconscious.py > "$OUT/ruff-format.txt" 2>&1
rc=$?; note "  ruff format --check rc=$rc : $(tail -1 "$OUT/ruff-format.txt")"; [ "$rc" -eq 0 ] || overall=1
note

note "== 1. positive control: quiet host =="
note "  host cpu: $(host_cpu)%"
for i in 1 2 3; do run_pytest "quiet-$i" pass; done
note

note "== 2. negative control: CPU-hogging daemon (must FAIL the ratio) =="
note "  host cpu: $(host_cpu)%"
DV032_NEGCTL=cpu run_pytest "negctl-cpu" fail
note

note "== 3. negative control: erroring daemon (must FAIL the error/dlq counts) =="
DV032_NEGCTL=errors run_pytest "negctl-errors" fail
note

note "== 4. positive control: SATURATED host (the condition that broke the original) =="
load_start
note "  host cpu under generated load: $(host_cpu)%"
for i in 1 2 3; do run_pytest "loaded-$i" pass; done
note "  == 4b. negative control under the same load (must still FAIL) =="
DV032_NEGCTL=cpu run_pytest "loaded-negctl-cpu" fail
load_stop
note "  host cpu after load removed: $(host_cpu)%"
note

note "# overall: $overall  (0 = every expectation matched)"
note "# finished $(date -u +%Y-%m-%dT%H:%M:%SZ)"
exit "$overall"
