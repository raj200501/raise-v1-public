#!/usr/bin/env bash
# Fetch the Project Gutenberg source bytes the label factory compresses, chosen for prose
# diversity. NOT uniformly public domain: pg5200 (Metamorphosis) self-identifies as a
# COPYRIGHTED Project Gutenberg eBook distributed under the Project Gutenberg License - see
# docs/compliance/LICENSE_AUDIT.md before redistributing anything derived from these bytes.
#
# The files/ path is fetched first because it is the path the banked corpora were built from;
# the cache/epub path serves a different, later edition of at least pg5200. gutenberg.org also
# re-edits files/ copies in place (pg1342 changed between 2026-08-25 and 2026-09-02), so every
# download is checked against the banked sha256 by tools/pivot/pin_sources.py, which fails
# loudly rather than letting a changed edition rebuild a corpus that no longer matches
# artifacts/pivot/corpus_manifest.json.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/data/pivot/src"
mkdir -p "$DIR"
UA="raise-v1-research/1.0"
for id in 1342 2701 84 1661 98 2600 1952 11 5200 74; do
  out="$DIR/pg${id}.txt"
  [ -s "$out" ] && continue
  # -f: an HTTP error is a failure, not a 404 page saved as the source (board review 2026-09-03);
  # the partial file is removed so the fallback runs and a later run re-fetches.
  curl -fsS --retry 3 --max-time 60 -A "$UA" -o "$out" "https://www.gutenberg.org/files/${id}/${id}-0.txt" 2>/dev/null \
    || { rm -f "$out"; curl -fsS --retry 3 --max-time 60 -A "$UA" -o "$out" "https://www.gutenberg.org/cache/epub/${id}/pg${id}.txt"; } \
    || { rm -f "$out"; echo "fetch failed for pg${id}" >&2; exit 1; }
done
echo "source bytes: $(du -sh "$DIR" | cut -f1) in $DIR"
python3 "$(dirname "${BASH_SOURCE[0]}")/pin_sources.py"
