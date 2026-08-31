#!/usr/bin/env bash
# Every gate, in one command, in the order CI runs them.
#
# This exists because "I ran the tests" and "I ran the gates" were different things, and the gap
# between them turned CI red three times. Run it before every commit; CI runs the same script.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"

"$PY" tools/preflight.py            | tail -1
"$PY" tools/prereg.py verify        | tail -1
"$PY" tests/mutation_test.py        | tail -2
"$PY" tools/coverage.py             | tail -2
"$PY" tools/claimcheck.py outbound VERDICT.md | tail -1
"$PY" tools/freshness.py            | tail -1

# Frozen readers. Exit 0 means a verdict was emitted; exit 2 means the study's artifact is absent,
# which is PENDING rather than broken - a preregistration is frozen before its data exists, so a
# reader with nothing to read is the normal state between freezing and measuring. Any other exit
# code is a real failure.
#
# Deleting an artifact a result depends on is NOT quietly tolerated by this: every banked result is
# cited by a claim in the coverage map, and tools/coverage.py above fails on a claim whose artifact
# does not exist. That is the check with teeth; this loop only distinguishes pending from broken.
pending=()
for r in tools/readers/*.py; do
  set +e; out=$("$PY" "$r" 2>&1); rc=$?; set -e
  case $rc in
    0) echo "  verdict: $(echo "$out" | grep -E '^\s+VERDICT:' | head -1 | sed 's/^ *//')" ;;
    2) pending+=("$(basename "$r")") ;;
    *) echo "READER FAILED ($rc): $r"; echo "$out"; exit 1 ;;
  esac
done
if [ ${#pending[@]} -gt 0 ]; then
  echo "  pending (frozen, not yet measured): ${pending[*]}"
fi
echo
echo "ALL GATES PASS"
