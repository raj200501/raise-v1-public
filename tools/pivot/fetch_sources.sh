#!/usr/bin/env bash
# Fetch the Project Gutenberg source bytes the label factory compresses, chosen for prose
# diversity. NOT uniformly public domain: pg5200 (Metamorphosis) self-identifies as a
# COPYRIGHTED Project Gutenberg eBook - see docs/compliance/LICENSE_AUDIT.md before
# redistributing anything derived from these bytes.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/data/pivot/src"
mkdir -p "$DIR"
UA="raise-v1-research/1.0"
for id in 1342 2701 84 1661 98 2600 1952 11 5200 74; do
  out="$DIR/pg${id}.txt"
  [ -s "$out" ] && continue
  curl -sS --max-time 60 -A "$UA" -o "$out" "https://www.gutenberg.org/files/${id}/${id}-0.txt" 2>/dev/null \
    || curl -sS --max-time 60 -A "$UA" -o "$out" "https://www.gutenberg.org/cache/epub/${id}/pg${id}.txt"
done
echo "source bytes: $(du -sh "$DIR" | cut -f1) in $DIR"
