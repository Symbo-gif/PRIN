#!/usr/bin/env bash
# Re-run only Devin on the same brief. Usage: launch_devin_attempt.sh <round-dir-name> <attempt-number>
R=/c/Users/there/prin-s3-scratch/review
[[ "$1" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]] || { echo "round name must match [A-Za-z0-9][A-Za-z0-9_-]*"; exit 2; }
[[ "$2" =~ ^[0-9]+$ ]] || { echo "attempt must be a number"; exit 2; }
D="$R/$1"
cd /c/dev/PRIN || exit 2
devin --model swe-2-high -p --prompt-file "C:/Users/there/prin-s3-scratch/review/reviewer-brief.md" --permission-mode smart --export "C:/Users/there/prin-s3-scratch/review/$1/devin-attempt$2-export.md" > "$D/devin-attempt$2-stdout.txt" 2>&1
echo "exit=$?" > "$D/devin-attempt$2.exit"
