#!/usr/bin/env bash
# Cold-clone rebuild of the four non-Gutenberg corpora 0025 depends on; each build writes its manifest to the scratchpad and is then
# checked against the BANKED manifest (never overwritten).
set -u
cd /home/user/raise-v1
SP=/tmp/claude-0/-home-user-raise-v1/5d675fa9-5fc4-501c-b3b3-a76510397d00/scratchpad
for b in corpus_ext corpus_realfit corpus_realfit2 corpus_realfit3; do
  echo "=== $b build $(date -u +%H:%M:%S)"
  nice -n 10 python3 tools/pivot/$b.py --build --manifest $SP/rebuild/${b}_manifest.json 2>&1 | tail -12 | cut -c1-240
  echo "=== $b check $(date -u +%H:%M:%S)"
  nice -n 10 python3 tools/pivot/$b.py --check 2>&1 | tail -14 | cut -c1-240
done
echo "=== DONE $(date -u +%H:%M:%S)"
