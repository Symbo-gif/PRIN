#!/usr/bin/env bash
# Launch the three cold reviewers in parallel on the same brief. Usage: launch_round.sh <round-dir-name>
R=/c/Users/there/prin-s3-scratch/review
D="$R/$1"
BRIEF_WIN='C:\Users\there\prin-s3-scratch\review\reviewer-brief.md'
POINTER="Your complete instructions are in the file $BRIEF_WIN . Read that file in full and carry them out exactly. Print your complete report to standard output."
cd /c/dev/PRIN || exit 2
( devin --model swe-2-high -p --prompt-file "C:/Users/there/prin-s3-scratch/review/reviewer-brief.md" --permission-mode smart --export "C:/Users/there/prin-s3-scratch/review/$1/devin-export.md" > "$D/devin-stdout.txt" 2>&1; echo "exit=$?" > "$D/devin.exit" ) &
( agy --model gemini-3.8-flash-high --mode plan --output-format text -p "$POINTER" > "$D/agy-stdout.txt" 2>&1; echo "exit=$?" > "$D/agy.exit" ) &
( qwen.cmd -m qwen3.8-max-preview -o text -p "$POINTER" > "$D/qwen-stdout.txt" 2>&1; echo "exit=$?" > "$D/qwen.exit" ) &
wait
