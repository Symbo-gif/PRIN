#!/usr/bin/env bash
# EXP-002 D1 S3 - paired contention experiment (finding EXP002D1-S2-F2).
#
#   bash EVIDENCE/exp002-d1-s3/contention_experiment.sh
#
# The observed full-suite run showed the notebook legs starved of CPU while the
# host sat at ~100% from the moment the file-heavy tests/test_exp002_* tests
# began. This script tests whether that group is enough to cause it, by
# measuring one notebook twice, with nothing else changed:
#
#   control    notebook 02 alone, no pytest running (the quiet-host baseline);
#   treatment  the same notebook, started once the host has been saturated for
#              three consecutive checks while ONLY tests/test_exp002_driver.py
#              and tests/test_exp002_e4_analysis.py run next to it.
#
# The pytest subset is only a load generator: it is stopped (session-owned
# process tree) when the treatment notebook finishes, and is never reported as a
# gate. Everything is written OUTSIDE the repository: to ~/prin-s3-scratch/contention/
# (run.txt, control.json, control.err, treatment.json, treatment.err,
# load-runner.txt) and, by diagnostic_suite_run.sh for the load generator, to
# ~/prin-s3-scratch/contention-load/ (run.txt, console.log, samples.jsonl).
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
export PATH="/c/Program Files/Git/bin:$PATH"
PY=.venv/Scripts/python.exe
OUT="$HOME/prin-s3-scratch/contention"
mkdir -p "$OUT"
NB=02_clevr_n_binding.ipynb
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
host_cpu() { $PY -I -c "import psutil; print(psutil.cpu_percent(interval=5))"; }

{
  echo "started: $(stamp)"
  echo "git HEAD: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)"
  echo "notebook: $NB   treatment load: tests/test_exp002_driver.py tests/test_exp002_e4_analysis.py"
} > "$OUT/run.txt"

# --- control -----------------------------------------------------------------
echo "control host cpu% (5 s mean): $(host_cpu)" >> "$OUT/run.txt"
echo "control start: $(stamp)" >> "$OUT/run.txt"
$PY -I EVIDENCE/exp002-d1-s3/notebook_timing.py --notebook "$NB" --timeout 7200 --label control-quiet > "$OUT/control.json" 2> "$OUT/control.err"
echo "control exit: $?   end: $(stamp)" >> "$OUT/run.txt"

# --- treatment: start the load generator, wait for saturation -----------------
bash EVIDENCE/exp002-d1-s3/diagnostic_suite_run.sh contention-load \
  tests/test_exp002_driver.py tests/test_exp002_e4_analysis.py -q -p no:cacheprovider \
  > "$OUT/load-runner.txt" 2>&1 &
LOAD=$!
echo "load generator started: $(stamp)" >> "$OUT/run.txt"

saturated=0
for _ in $(seq 1 240); do                       # at most 240 x ~5 s = 20 min
  cpu=$(host_cpu)
  if awk -v c="$cpu" 'BEGIN{exit !(c >= 90)}'; then saturated=$((saturated + 1)); else saturated=0; fi
  [ "$saturated" -ge 3 ] && break
done
echo "saturation reached: $([ "$saturated" -ge 3 ] && echo yes || echo NO)   at $(stamp)   (last host cpu% $cpu)" >> "$OUT/run.txt"

echo "treatment start: $(stamp)" >> "$OUT/run.txt"
$PY -I EVIDENCE/exp002-d1-s3/notebook_timing.py --notebook "$NB" --timeout 7200 --label treatment-under-exp002-tests > "$OUT/treatment.json" 2> "$OUT/treatment.err"
echo "treatment exit: $?   end: $(stamp)" >> "$OUT/run.txt"

# --- stop the load generator (it is not a gate) --------------------------------
# Only the process tree this script started is stopped: the runner's Windows PID is
# read from /proc and taskkill /T takes that runner and its children (pytest, the
# sampler). Nothing is matched by command-line text, so no unrelated process of the
# maintainer's can be hit.
if kill -0 "$LOAD" 2>/dev/null; then
  echo "load generator still running at treatment end: stopping its process tree $(stamp)" >> "$OUT/run.txt"
  WINPID=$(cat "/proc/$LOAD/winpid" 2>/dev/null)
  if [ -n "$WINPID" ]; then /c/Windows/System32/taskkill.exe //PID "$WINPID" //T //F > /dev/null 2>&1; fi
fi
wait "$LOAD" 2>/dev/null
echo "finished: $(stamp)" >> "$OUT/run.txt"
