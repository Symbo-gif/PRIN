#!/usr/bin/env bash
# EXP-002 D1 S3 - delta re-audit: the pre-fix failing reproduction and the post-fix
# passing parity tests (S3 session prompt section 7). Run from Git Bash at the repository root.
#
#   bash EVIDENCE/exp002-d1-s3/delta_reaudit.sh
#
# Steps, each with its verbatim command, UTC time and exit status:
#   1. record the module's SHA-256 at the S1/S2 head (5ba0129e), at S1's fix commit
#      (10d84f2b), at the pre-fix commit (d90eeabb) and on disk now;
#   2. restore the PRE-FIX module into the working tree and run the parity gate and
#      the fast-gate argument tests (both must FAIL: the regression is reproduced);
#   3. restore the module back to HEAD, show the tree is clean and the SHA-256 is
#      the on-disk value again;
#   4. run both test files together on the current tree (must all PASS).
# The working-tree module is restored by a trap even if a step fails.
cd "$(git rev-parse --show-toplevel)" || exit 2
export PATH="/c/Program Files/Git/bin:$PATH"
PY=.venv/Scripts/python.exe
MOD=python/prin/reporting/figure_generation.py
PARITY=parity/test_parity_publication.py
FAST=tests/test_publication_figure_arguments.py
FLAGS=(-q -rf --basetemp=.pytest_basetemp -o faulthandler_timeout=300 -p no:cacheprovider)
overall=0
trap 'git restore -- "$MOD" 2>/dev/null' EXIT

stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
blob_sha() { git show "$1:$MOD" | sha256sum | cut -d' ' -f1; }

echo "# EXP-002 D1 S3 - delta re-audit"
echo "# date (UTC): $(stamp)"
echo "# git HEAD: $(git rev-parse HEAD)   tracked changes at start: $(git status --porcelain --untracked-files=no | wc -l)"
echo "# host: $(uname -srm)   $($PY -V 2>&1)"
[ "$(git status --porcelain --untracked-files=no | wc -l)" -eq 0 ] || { echo "tree is not clean; refusing to run"; exit 2; }

echo
echo "## D1 figure_generation.py SHA-256 at the commits involved"
echo "  d90eeabb (pre-fix, the failing-test commit) : $(blob_sha d90eeabb)"
echo "  10d84f2b (S1's fix)                          : $(blob_sha 10d84f2b)"
echo "  5ba0129e (S1/S2 head = S3 base)              : $(blob_sha 5ba0129e)"
echo "  HEAD (with S3's F6 label and F7 docstring)   : $(blob_sha HEAD)"
echo "  on disk now                                  : $(sha "$MOD")"
PRE_EXPECT=e0f59253
echo "  pre-fix commit's digest starts with the S1/S2-recorded ${PRE_EXPECT}: $([ "$(blob_sha d90eeabb | cut -c1-8)" = "$PRE_EXPECT" ] && echo yes || echo NO)"
echo "  S1/S2 head's digest starts with the recorded b41dfc13                 : $([ "$(blob_sha 5ba0129e | cut -c1-8)" = "b41dfc13" ] && echo yes || echo NO)"
echo "  NOTE: S3's F6 and F7 commits change the module, so its digest at HEAD is no longer b41dfc13."
HEAD_SHA=$(sha "$MOD")

echo
echo "## D2 restore the PRE-FIX module and reproduce the regression (both runs must fail)"
echo "# command: git restore --source d90eeabb -- $MOD"
git restore --source d90eeabb -- "$MOD"; echo "# exit code: $?"
echo "  module on disk now: $(sha "$MOD")   (equals the pre-fix blob: $([ "$(sha "$MOD")" = "$(blob_sha d90eeabb)" ] && echo yes || echo NO))"
echo "  git diff d90eeabb -- module (must be empty): $(git diff d90eeabb -- "$MOD" | wc -l) lines"
echo
echo "# command: $PY -m pytest $PARITY ${FLAGS[*]}"
echo "# started $(stamp)"
$PY -m pytest "$PARITY" "${FLAGS[@]}" 2>&1 | tr -d '\r' | grep -E '^(FAILED|ERROR)|passed|failed|error' | sed 's/ - .*//' | sort | uniq -c | sort -rn | head -30
rc=${PIPESTATUS[0]}; echo "# exit code: $rc (must be 1)"; echo "# ended $(stamp)"
[ "$rc" -eq 1 ] || overall=1
echo
echo "# command: $PY -m pytest $FAST ${FLAGS[*]}"
echo "# started $(stamp)"
$PY -m pytest "$FAST" "${FLAGS[@]}" 2>&1 | tr -d '\r' | grep -E '^FAILED|passed|failed' | cut -c1-140
rc=${PIPESTATUS[0]}; echo "# exit code: $rc (must be 1)"; echo "# ended $(stamp)"
[ "$rc" -eq 1 ] || overall=1

echo
echo "## D3 restore the module to HEAD"
echo "# command: git restore -- $MOD"
git restore -- "$MOD"; echo "# exit code: $?"
echo "  module on disk now: $(sha "$MOD")   (equals the value before the restore: $([ "$(sha "$MOD")" = "$HEAD_SHA" ] && echo yes || echo NO))"
echo "  git status --porcelain (tracked): '$(git status --porcelain --untracked-files=no)'   $([ -z "$(git status --porcelain --untracked-files=no)" ] && echo CLEAN || echo NOT-CLEAN)"
[ "$(sha "$MOD")" = "$HEAD_SHA" ] || overall=1

echo
echo "## D4 post-fix: both test files together on the current tree (must all pass)"
echo "# command: $PY -m pytest $FAST $PARITY ${FLAGS[*]}"
echo "# started $(stamp)"
$PY -m pytest "$FAST" "$PARITY" "${FLAGS[@]}" 2>&1 | tr -d '\r' | tail -6
rc=${PIPESTATUS[0]}; echo "# exit code: $rc (must be 0)"; echo "# ended $(stamp)"
[ "$rc" -eq 0 ] || overall=1

echo
echo "# overall: $overall (0 = the regression reproduced pre-fix, the module restored, and all tests pass post-fix)"
exit "$overall"
