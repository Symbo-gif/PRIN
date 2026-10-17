#!/usr/bin/env bash
# Collect the red required-leg evidence for commit 814b670c into the S4 bundle.
#
# The earlier collected gate/full/ is the PASSING run at 157ce5bc and must not be
# overwritten: it is the control that proves the change set innocent.  This writes
# a sibling directory gate/red-leg-814b670c/ instead.
set -u
ROOT=/c/dev/PRIN
SCRATCH="$HOME/prin-s4-scratch"
DST="$ROOT/EVIDENCE/exp002-d1-s4/gate/red-leg-814b670c"
cd "$ROOT" || exit 2
mkdir -p "$DST/isolated"

# --- the red leg itself, verbatim -------------------------------------------
cp "$SCRATCH/full/run.txt"        "$DST/run.txt"
cp "$SCRATCH/full/console.log"    "$DST/console.txt"
cp "$SCRATCH/full/samples.jsonl"  "$DST/samples.jsonl"
cp "$SCRATCH/full/sampler.err"    "$DST/sampler-err.txt"
cp "$SCRATCH/gate/legs.txt"       "$DST/long-legs.txt"

# --- the two isolated reproductions -----------------------------------------
# Run 1 was executed without redirection; its console output is transcribed
# verbatim into run1-transcribed.txt and labelled as such.  Run 2 is an
# authentic capture.
cp "$SCRATCH/isolated-throughput-run2.txt" "$DST/isolated/run2-captured.txt"
for i in 1 2 3 4 5; do
  if [ -f "$SCRATCH/isolated-throughput/iter$i.txt" ]; then
    cp "$SCRATCH/isolated-throughput/iter$i.txt" "$DST/isolated/run2-iter$i.txt"
  fi
done

# --- the contention instrument and its two outputs --------------------------
cp "$SCRATCH/contention_window.py" "$DST/contention_window.py"
.venv/Scripts/python.exe -I "$DST/contention_window.py" \
    "$SCRATCH/full/samples.jsonl" 20:28:54 20:29:07 \
    > "$DST/contention-failing-leg.txt" 2>&1
.venv/Scripts/python.exe -I "$DST/contention_window.py" \
    "$ROOT/EVIDENCE/exp002-d1-s4/gate/full/samples.jsonl" 20:07:49 20:07:49 \
    > "$DST/contention-passing-leg.txt" 2>&1

# --- structural proof the change set cannot have caused it ------------------
{
  echo "# Structural attribution: the failing test and its subject code are"
  echo "# byte-identical between the run that PASSED and the run that FAILED."
  echo "# date (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo '== git rev-parse HEAD =='
  git rev-parse HEAD
  echo
  echo '== is 157ce5bc (the passing run) an ancestor of HEAD? =='
  if git merge-base --is-ancestor 157ce5bc HEAD; then echo YES; else echo NO; fi
  echo
  echo '== product + test code changed 157ce5bc..HEAD =='
  echo '(empty means the daemon under test and the test itself are byte-identical)'
  git diff --name-only 157ce5bc..HEAD -- python/ rust/ crates/ Cargo.toml Cargo.lock pyproject.toml tests/
  echo '== end (empty above) =='
  echo
  echo '== every file changed 157ce5bc..HEAD =='
  git diff --name-only 157ce5bc..HEAD
  echo
  echo '== the failing assertion, verbatim from the red leg =='
  grep -n -A4 'FAILURES' "$DST/console.txt" | head -12
  echo
  echo '== the same test in the PASSING control run =='
  grep -n 'test_no_gpu_throughput_regression' \
      "$ROOT/EVIDENCE/exp002-d1-s4/gate/full/console.txt"
} > "$DST/attribution.txt" 2>&1

echo "collected into EVIDENCE/exp002-d1-s4/gate/red-leg-814b670c:"
ls -1 "$DST"
echo
echo "isolated/:"
ls -1 "$DST/isolated"
