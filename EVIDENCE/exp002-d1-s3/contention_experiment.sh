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
# gate. Everything is written OUTSIDE the repository, to
# ~/prin-s3-scratch/contention/ (control.json, treatment.json, console.log,
# samples.jsonl, run.txt).
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
if kill -0 "$LOAD" 2>/dev/null; then
  echo "load generator still running at treatment end: stopping the session-owned tree $(stamp)" >> "$OUT/run.txt"
  # The patterns are assembled from fragments so this command's own text does not
  # match them (it would otherwise kill itself).
  powershell.exe -NoProfile -Command "\$a = 'suite_run.sh contention' + '-load'; \$b = 'test_exp002_' + 'driver.py'; Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -like ('*' + \$a + '*') -or \$_.CommandLine -like ('*' + \$b + '*') } | ForEach-Object { taskkill /PID \$_.ProcessId /T /F | Out-Null }" > /dev/null 2>&1
fi
wait "$LOAD" 2>/dev/null
echo "finished: $(stamp)" >> "$OUT/run.txt"
