#!/usr/bin/env bash
# Session-0162 local gate runner (scratch tooling; not committed).
# Usage: gate.sh <log-dir> <source-description> <leg> [<leg> ...]
# Each leg writes <log-dir>/<leg>.log headed by COMMAND/CWD/SOURCE/UTC-START/HOST
# and ending with ELAPSED_S and the real EXIT_CODE. Run from Git Bash.
set -u
LOGDIR=$1
SOURCE=$2
shift 2
mkdir -p "$LOGDIR"
cd /c/dev/PRIN || exit 2
PY=C:/dev/PRIN/.venv/Scripts/python.exe
RUFF=C:/dev/PRIN/.venv/Scripts/ruff.exe
MYPY=C:/dev/PRIN/.venv/Scripts/mypy.exe
CARGO=C:/Users/there/.cargo/bin/cargo.exe
GITLEAKS=C:/dev/PRIN/DOCS/test_and_benchmark_results/ea007/full-gate/.tools/gitleaks/bin/gitleaks.exe
SCR=C:/Users/there/AppData/Local/Temp/claude/c--dev-PRIN/5e1d6deb-495c-48f1-bf1a-4c8ad51472b3/scratchpad
MODDIR=DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/analysis

run() {
  local name=$1
  shift
  local log="$LOGDIR/$name.log"
  {
    printf 'COMMAND:'
    printf ' %s' "$@"
    printf '\n'
    echo "CWD: C:/dev/PRIN"
    echo "SOURCE: $SOURCE"
    echo "HEAD: $(git rev-parse HEAD)"
    echo "UTC-START: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "HOST: $(hostname) (Windows-11-10.0.26300-SP0), Git Bash"
    echo "----"
  } > "$log"
  local start
  start=$(date +%s)
  "$@" >> "$log" 2>&1
  local rc=$?
  {
    echo "----"
    echo "UTC-END: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "ELAPSED_S: $(( $(date +%s) - start ))"
    echo "EXIT_CODE: $rc"
  } >> "$log"
  echo "$name exit=$rc"
}

for leg in "$@"; do
  case $leg in
    G01) run G01-ruff-check "$RUFF" check python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/ ;;
    G02) run G02-ruff-format-check "$RUFF" format --check python/ tests/ benchmarks/ tools/ parity/ ;;
    G03) run G03-ruff-format-check-experiments "$RUFF" format --check DOCS/experiments/ --config "include = ['*.py', '*.pyi', '*.ipynb']" ;;
    G04) run G04-mypy-prin "$MYPY" python/prin --strict ;;
    G05) run G05-mypy-experiments "$MYPY" DOCS/experiments/ --strict ;;
    G06) run G06-mypy-exp002-driver "$MYPY" benchmarks/campaign/exp002_driver.py --strict ;;
    G07) run G07-interrogate "$PY" -m interrogate -c pyproject.toml python/prin ;;
    G08) run G08-bandit "$PY" -m bandit -r python/prin DOCS/experiments -c pyproject.toml ;;
    G09) run G09-focused-pytest "$PY" -m pytest tests/test_exp002_e4_analysis.py tests/test_campaign_quality_gates.py tests/test_basetemp.py -p no:cacheprovider "--basetemp=$SCR/bt-focused" "--cov=$MODDIR" --cov-branch --cov-report=term-missing "--cov-report=json:$LOGDIR/G09-focused-coverage.json" ;;
    G10) run G10-governance-deviation-ledger "$PY" tools/check_deviation_ledger.py DOCS/reports/039-project-state.md DOCS/reports/040-project-state.md ;;
    G10b) run G10b-governance-dv-gates "$PY" tools/check_dv_register_gates.py ;;
    G10c) run G10c-governance-session-registration "$PY" tools/check_global_session_registration.py ;;
    G10d) run G10d-governance-skipif-probes "$PY" tools/check_skipif_probes.py ;;
    G10e) run G10e-governance-wp001 "$PY" tools/wp001_baseline.py check ;;
    G10f) run G10f-git-diff-check git diff --cached --check ;;
    G11) rm -rf "$SCR/sphinx-html"; run G11-sphinx "$PY" -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx "$SCR/sphinx-html" ;;
    G12) run G12-pytest-fast "$PY" -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20 ;;
    G13) run G13-pytest-full "$PY" -m pytest tests/ parity/ --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20 ;;
    G17) run G17-gitleaks-full-history "$GITLEAKS" git C:/dev/PRIN --redact --no-banner --report-format json --report-path "$LOGDIR/gitleaks-history.json" ;;
    G18) run G18-gitleaks-staged "$GITLEAKS" git C:/dev/PRIN --pre-commit --staged --redact --no-banner --report-format json --report-path "$LOGDIR/gitleaks-staged.json" ;;
    R01) run R01-cargo-version "$CARGO" --version --verbose ;;
    R02) run R02-cargo-fmt "$CARGO" fmt --all -- --check ;;
    R03) run R03-cargo-clippy "$CARGO" clippy --workspace --all-targets -- -D warnings ;;
    R04) run R04-cargo-clippy-strict "$CARGO" clippy --workspace --all-targets --features strict-checks -- -D warnings ;;
    R05) run R05-cargo-test "$CARGO" test --workspace ;;
    R06) run R06-cargo-test-strict "$CARGO" test --workspace --features strict-checks ;;
    R07) run R07-cargo-llvm-cov-kernels "$CARGO" llvm-cov -p prin-kernels --features wgpu,cpu ;;
    R08) run R08-cargo-audit "$CARGO" audit ;;
    *) echo "unknown leg $leg"; exit 2 ;;
  esac
done
