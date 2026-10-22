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

To re-measure the result from scratch rather than read the banked one, in this order:

    pip install -r requirements-pivot.txt     # zopfli, isal, libdeflate
    tools/pivot/fetch_sources.sh              # Project Gutenberg source bytes, checked against their banked hashes;
                                              # terms in docs/compliance/LICENSE_AUDIT.md
    python3 tools/pivot/run_study.py --cache data/pivot/full_c4096.npz --chunks 50000 --carve 4096 \
        --model hgb --rungs 1000 10000 100000 800000 --tag full \
        --out /tmp/deflate_curve.json --scores-out /tmp/deflate_rung_scores.json
                                              # builds the corpus first (no cache yet), then measures; the banked
                                              # artifacts/pivot/ files are not written
    python3 tools/pivot/corpus_manifest.py --check   # the rebuilt corpus against the banked array hashes

What this reproduces and what it does not (CORRECTIONS.md, 2026-10-21, builder cache row order):
the source bytes are checked byte for byte, and the rebuilt cache's labels y hash to the banked y.
Its X and g do not: run_study.py build() writes rows in the order its workers finish, so --check
reads DIFF for full_c4096's X and g on every rebuild, by design, and MISSING for the three corpora
this block does not build, and exits non-zero. The evaluation set is the same set of chunks, but
the training pool is a different draw of rows, so the curve printed is a re-measurement on a
different draw of the pool, not a re-derivation of the banked numbers on the same rows.

The other steps exit non-zero on failure; the manifest check exits non-zero on a faithful rebuild too.
MSG
