#!/usr/bin/env bash
LOGDIR=$1; SOURCE=$2
cd /c/dev/PRIN
log=$LOGDIR/G13a-pytest-full-failed-tests-isolated-rerun.log
{ echo "COMMAND: C:/dev/PRIN/.venv/Scripts/python.exe -m pytest tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression tests/test_notebooks.py::test_notebook_executes_end_to_end[02_clevr_n_binding.ipynb] -p no:cacheprovider --basetemp=.pytest_basetemp -o faulthandler_timeout=300 -v"; echo "CWD: C:/dev/PRIN"; echo "SOURCE: $SOURCE"; echo "HEAD: $(git rev-parse HEAD)"; echo "UTC-START: $(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "PURPOSE: diagnostic isolated rerun of the two G13 failures; G13 stays a failed capture"; echo "----"; } > $log
s=$(date +%s)
C:/dev/PRIN/.venv/Scripts/python.exe -m pytest "tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression" "tests/test_notebooks.py::test_notebook_executes_end_to_end[02_clevr_n_binding.ipynb]" -p no:cacheprovider --basetemp=.pytest_basetemp -o faulthandler_timeout=300 -v >> $log 2>&1
rc=$?
{ echo "----"; echo "UTC-END: $(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "ELAPSED_S: $(( $(date +%s) - s ))"; echo "EXIT_CODE: $rc"; } >> $log
echo "G13a exit=$rc"
