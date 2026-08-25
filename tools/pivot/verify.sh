#!/usr/bin/env bash
# One command, cold clone, nothing installed. Preflight first so a missing dependency fails at the
# top with its cause and its fix, rather than forty frames deep inside a library.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

PY="${PYTHON:-python3}"
echo "== preflight =="
"$PY" tools/preflight.py

echo
echo "== the instrument =="
"$PY" tools/prereg.py verify
"$PY" tests/mutation_test.py | tail -2
"$PY" tools/coverage.py | tail -2
"$PY" tools/claimcheck.py outbound VERDICT.md | tail -2
"$PY" tools/freshness.py | tail -2

echo
echo "== the pivot result, read by its frozen reader =="
"$PY" tools/readers/pivot_deflate_curve.py
echo
"$PY" tools/readers/deflate_topk_verdict.py

cat <<'MSG'

To re-derive the result from scratch rather than read the banked one:

    pip install -r requirements-pivot.txt     # zopfli, isal, libdeflate
    tools/pivot/fetch_sources.sh              # public-domain source bytes
    python3 tools/pivot/run_study.py --help   # the manufacture-and-measure pipeline

Everything above exits non-zero on failure.
MSG
