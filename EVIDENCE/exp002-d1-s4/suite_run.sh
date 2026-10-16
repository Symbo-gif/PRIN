#!/usr/bin/env bash
# EXP-002 D1 S4 - observed pytest run. Adapted copy of S3's diagnostic_suite_run.sh
# (which S4's O-2 review verified correct: C2/C3 in o2-review/triage.md), with the
# scratch root moved to ~/prin-s4-scratch so S4's records cannot collide with S3's.
#
#   bash EVIDENCE/exp002-d1-s4/suite_run.sh <label> <pytest args...>
#
# Runs pytest with the required instrumentation (-o faulthandler_timeout=300
# --durations=20, --basetemp=.pytest_basetemp, Git Bash first on PATH) and a UTC
# timestamp on every console line, observed by S3's out-of-process sampler.
# Everything recorded goes OUTSIDE the repository, to ~/prin-s4-scratch/<label>/:
#   console.log   timestamped pytest console output
#   samples.jsonl sampler output (one JSON object per 30 s)
#   run.txt       commands, UTC start/end, git HEAD, pytest exit status
# The one in-repository write is pytest's own --basetemp=.pytest_basetemp, which
# AGENTS.md mandates by that exact name and which is gitignored.
#
# Exit status is pytest's. A missing or malformed label exits 2 BEFORE anything
# runs (S3's round-4 fix, re-verified here).
set -u
LABEL="${1:-}"
[ -n "$LABEL" ] || { echo "usage: suite_run.sh <label> <pytest args...>"; exit 2; }
shift
# A label is a directory name under ~/prin-s4-scratch, so it must not be able to
# climb out of it: letters, digits, '_' and '-', not starting with '-'.
[[ "$LABEL" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]] || { echo "label must match [A-Za-z0-9][A-Za-z0-9_-]*"; exit 2; }
[ "$#" -ge 1 ] || { echo "no pytest arguments given"; exit 2; }

cd "$(git rev-parse --show-toplevel)" || exit 2
OUT="$HOME/prin-s4-scratch/$LABEL"
mkdir -p "$OUT"
export PATH="/c/Program Files/Git/bin:$PATH"
PY=.venv/Scripts/python.exe
SAMPLER=EVIDENCE/exp002-d1-s3/suite_sampler.py

{
  echo "label: $LABEL"
  echo "git HEAD: $(git rev-parse HEAD)"
  echo "tracked changes vs HEAD: $(git status --porcelain --untracked-files=no | wc -l)"
  echo "untracked files: $(git status --porcelain | grep -c '^??')"
  echo "host: $(uname -srm)   $($PY -V 2>&1)   logical CPUs: $(nproc 2>/dev/null)"
  echo "pytest args: $*"
  echo "command: $PY -m pytest $* --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20"
  echo "started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/run.txt"

$PY -I "$SAMPLER" --period 30 > "$OUT/samples.jsonl" 2> "$OUT/sampler.err" &
SAMPLER_PID=$!

$PY -m pytest "$@" --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20 2>&1 \
  | awk '{print strftime("%H:%M:%SZ", systime(), 1), $0; fflush()}' > "$OUT/console.log"
STATUS=${PIPESTATUS[0]}

# The sampler stops by itself once pytest has been gone for two samples (~60 s).
# Allow it 150 s, then stop it, so this script can never hang on it. Only this
# script's own sampler is ever signalled.
for _ in $(seq 1 30); do kill -0 "$SAMPLER_PID" 2>/dev/null || break; sleep 5; done
if kill -0 "$SAMPLER_PID" 2>/dev/null; then
  kill "$SAMPLER_PID" 2>/dev/null
  echo "sampler did not exit by itself within 150 s and was stopped" >> "$OUT/run.txt"
fi
wait "$SAMPLER_PID" 2>/dev/null
{
  echo "pytest exit status: $STATUS"
  echo "ended: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "git HEAD at end: $(git rev-parse HEAD)   tracked changes: $(git status --porcelain --untracked-files=no | wc -l)   untracked files: $(git status --porcelain | grep -c '^??')"
} >> "$OUT/run.txt"
echo "run recorded in $OUT ; pytest exit status: $STATUS"
exit "$STATUS"
