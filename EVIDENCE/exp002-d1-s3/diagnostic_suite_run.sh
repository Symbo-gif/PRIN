#!/usr/bin/env bash
# EXP-002 D1 S3 - observed pytest run (finding EXP002D1-S2-F2).
#
#   bash EVIDENCE/exp002-d1-s3/diagnostic_suite_run.sh <label> [--lift-notebook-timeout] <pytest args...>
#
# Starts the out-of-process sampler (suite_sampler.py), then runs pytest with the
# required instrumentation (-o faulthandler_timeout=300 --durations=20,
# --basetemp=.pytest_basetemp, Git Bash first on PATH) and a UTC timestamp on
# every console line. With --lift-notebook-timeout the diagnostic plugin
# diag_nb_timeout.py is loaded so a slow notebook leg is measured instead of
# killed at 900 s; a run that does so is a DIAGNOSTIC run, never the gate.
#
# All output goes OUTSIDE the repository, to ~/prin-s3-scratch/<label>/, so the
# run cannot change the tree it is measuring:
#   console.log   timestamped pytest console output
#   samples.jsonl sampler output (one JSON object per 30 s)
#   run.txt       commands, UTC start/end, git HEAD, pytest exit status
set -u
LABEL="${1:?usage: diagnostic_suite_run.sh <label> [--lift-notebook-timeout] <pytest args...>}"
shift
case "$LABEL" in *[!A-Za-z0-9._-]*) echo "label must be [A-Za-z0-9._-]"; exit 2 ;; esac
LIFT=0
if [ "${1:-}" = "--lift-notebook-timeout" ]; then LIFT=1; shift; fi

cd "$(git rev-parse --show-toplevel)" || exit 2
OUT="$HOME/prin-s3-scratch/$LABEL"
mkdir -p "$OUT"
export PATH="/c/Program Files/Git/bin:$PATH"
PY=.venv/Scripts/python.exe
PLUGIN=()
if [ "$LIFT" -eq 1 ]; then
  export PYTHONPATH="$PWD/EVIDENCE/exp002-d1-s3${PYTHONPATH:+:$PYTHONPATH}"
  PLUGIN=(-p diag_nb_timeout)
fi

{
  echo "label: $LABEL"
  echo "git HEAD: $(git rev-parse HEAD)"
  echo "tracked changes vs HEAD: $(git status --porcelain --untracked-files=no | wc -l)"
  echo "untracked files: $(git status --porcelain | grep -c '^??')"
  echo "host: $(uname -srm)   $($PY -V 2>&1)   logical CPUs: $(nproc 2>/dev/null)"
  echo "diagnostic notebook-timeout plugin loaded: $LIFT"
  echo "pytest args: $*"
  echo "started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/run.txt"

$PY -I EVIDENCE/exp002-d1-s3/suite_sampler.py --period 30 > "$OUT/samples.jsonl" 2> "$OUT/sampler.err" &
SAMPLER=$!

$PY -m pytest "$@" --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20 "${PLUGIN[@]}" 2>&1 \
  | awk '{print strftime("%H:%M:%SZ", systime(), 1), $0; fflush()}' > "$OUT/console.log"
STATUS=${PIPESTATUS[0]}

# Let the sampler see pytest gone for two samples and exit by itself.
wait "$SAMPLER" 2>/dev/null
{
  echo "pytest exit status: $STATUS"
  echo "ended: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "git HEAD at end: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)"
} >> "$OUT/run.txt"
exit "$STATUS"
