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
# Everything this script records goes OUTSIDE the repository, to
# ~/prin-s3-scratch/<label>/, so it cannot change the tree it is measuring:
#   console.log   timestamped pytest console output
#   samples.jsonl sampler output (one JSON object per 30 s)
#   run.txt       commands, UTC start/end, git HEAD, pytest exit status
# The one in-repository write is pytest's own --basetemp=.pytest_basetemp, which
# AGENTS.md mandates by that exact name and which is gitignored. run.txt records
# the tracked-change and untracked-file counts before and after the run, so a
# change to the tree would show.
set -u
LABEL="${1:-}"
[ -n "$LABEL" ] || { echo "usage: diagnostic_suite_run.sh <label> [--lift-notebook-timeout] <pytest args...>"; exit 2; }
shift
# A label is a directory name under ~/prin-s3-scratch, so it must not be able to
# climb out of it: letters, digits, '_' and '-', not starting with '-' (no dots).
[[ "$LABEL" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]] || { echo "label must match [A-Za-z0-9][A-Za-z0-9_-]*"; exit 2; }
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

$PY -m pytest "$@" --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20 ${PLUGIN[@]+"${PLUGIN[@]}"} 2>&1 \
  | awk '{print strftime("%H:%M:%SZ", systime(), 1), $0; fflush()}' > "$OUT/console.log"
STATUS=${PIPESTATUS[0]}

# The sampler stops by itself once pytest has been gone for two samples (about
# 60 s). Allow it 150 s, then stop it, so this script can never hang on it.
for _ in $(seq 1 30); do kill -0 "$SAMPLER" 2>/dev/null || break; sleep 5; done
if kill -0 "$SAMPLER" 2>/dev/null; then
  kill "$SAMPLER" 2>/dev/null
  echo "sampler did not exit by itself within 150 s and was stopped" >> "$OUT/run.txt"
fi
wait "$SAMPLER" 2>/dev/null
{
  echo "pytest exit status: $STATUS"
  echo "ended: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "git HEAD at end: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)   untracked files: $(git status --porcelain | grep -c '^??')"
} >> "$OUT/run.txt"
exit "$STATUS"
