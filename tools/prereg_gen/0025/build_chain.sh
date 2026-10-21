#!/usr/bin/env bash
# Cold-clone rebuild of the four non-Gutenberg corpora 0025 depends on; each build writes its manifest to the scratchpad and is then
# checked against the BANKED manifest (never overwritten).
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
SP=${RAISE_SCRATCH:?set RAISE_SCRATCH to a scratch directory outside the repository}
for b in corpus_ext corpus_realfit corpus_realfit2 corpus_realfit3; do
  echo "=== $b build $(date -u +%H:%M:%S)"
  nice -n 10 python3 tools/pivot/$b.py --build --manifest $SP/rebuild/${b}_manifest.json 2>&1 | tail -12 | cut -c1-240
  echo "=== $b check $(date -u +%H:%M:%S)"
  nice -n 10 python3 tools/pivot/$b.py --check 2>&1 | tail -14 | cut -c1-240
done
echo "=== DONE $(date -u +%H:%M:%S)"
