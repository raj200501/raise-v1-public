#!/usr/bin/env bash
# Fetch the Project Gutenberg source bytes the label factory compresses, chosen for prose
# diversity. NOT uniformly public domain: pg5200 (Metamorphosis) self-identifies as a
# COPYRIGHTED Project Gutenberg eBook distributed under the Project Gutenberg License - see
# docs/compliance/LICENSE_AUDIT.md before redistributing anything derived from these bytes.
#
# The files/ path is fetched first because it is the path the banked corpora were built from;
# the cache/epub path serves a different, later edition of at least pg5200. gutenberg.org also
# re-edits files/ copies in place (pg1342 changed between 2026-08-25 and 2026-09-02; pg2701 by
# 2026-09-08), so every
# download is checked against the banked sha256 by tools/pivot/pin_sources.py, which fails
# loudly rather than letting a changed edition into a rebuilt corpus. The right source bytes are
# necessary for a rebuild to match artifacts/pivot/corpus_manifest.json, not sufficient: X and g
# of the caches tools/pivot/run_study.py build() writes come out in worker-completion row order
# and differ on every rebuild, by design (CORRECTIONS.md, 2026-10-21, builder cache row order).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/data/pivot/src"
# Every download lands in PART first - beside DIR, never in it, because tools/pivot/corpus.py reads every file in DIR - and
# is moved into DIR only after curl succeeds. A killed run therefore leaves no partial file in DIR for a re-run to skip as
# "already fetched" (the skip below tests for a non-empty file), and no stray file for the loader to read (cold-clone audit
# D5, D9). The move is a rename on one filesystem.
PART="$(dirname "$DIR")/src_partial"
mkdir -p "$DIR" "$PART"
UA="raise-v1-research/1.0"
for id in 1342 2701 84 1661 98 2600 1952 11 5200 74; do
  out="$DIR/pg${id}.txt"; tmp="$PART/pg${id}.txt"
  [ -s "$out" ] && continue
  # -f: an HTTP error is a failure, not a 404 page saved as the source (board review 2026-09-03);
  # the partial file is removed so the fallback runs and a later run re-fetches.
  curl -fsS --retry 3 --max-time 60 -A "$UA" -o "$tmp" "https://www.gutenberg.org/files/${id}/${id}-0.txt" 2>/dev/null \
    || { rm -f "$tmp"; curl -fsS --retry 3 --max-time 60 -A "$UA" -o "$tmp" "https://www.gutenberg.org/cache/epub/${id}/pg${id}.txt"; } \
    && mv "$tmp" "$out" \
    || { rm -f "$tmp"; echo "fetch failed for pg${id}" >&2; exit 1; }
done
# Gutenberg re-edits in place: by 2026-10-21 both pg1952 and pg2701 served editions other than the banked ones, and
# web.archive.org is not reachable from every network. The banked editions survive byte for byte in third-party copies;
# these URLs are pinned to a commit, and a copy is used ONLY when Gutenberg's file does not hash to the banked sha256 and the
# copy does (artifacts/pivot/corpus_manifest.json sources_sha256). pin_sources.py below stays the final arbiter.
# (CORRECTIONS.md, entry of 2026-10-21.)
FALLBACK_1952="https://raw.githubusercontent.com/EstDan09/huffman-compression-c-serial-fork-pthreads/17a9bac25cf06932109421453f0cf7e30aeb24e9/gutenberg_books/book_1952.txt"
FALLBACK_2701="https://raw.githubusercontent.com/EstDan09/huffman-compression-c-serial-fork-pthreads/17a9bac25cf06932109421453f0cf7e30aeb24e9/gutenberg_books/book_2701.txt"
MANIFEST="$(dirname "${BASH_SOURCE[0]}")/../../artifacts/pivot/corpus_manifest.json"
for id in 1952 2701; do
  out="$DIR/pg${id}.txt"
  want=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['sources_sha256']['pg${id}.txt'])" "$MANIFEST")
  have=$(sha256sum "$out" | cut -d' ' -f1)
  [ "$have" = "$want" ] && continue
  var="FALLBACK_${id}"; tmp="$PART/pg${id}.txt.fallback"
  curl -fsS --retry 3 --max-time 60 -A "$UA" -o "$tmp" "${!var}" || { rm -f "$tmp"; echo "fallback fetch failed for pg${id}" >&2; continue; }
  if [ "$(sha256sum "$tmp" | cut -d' ' -f1)" = "$want" ]; then
    mv "$tmp" "$out"; echo "pg${id}: Gutenberg serves another edition; the banked edition restored from the commit-pinned copy"
  else
    rm -f "$tmp"; echo "pg${id}: the pinned copy does not hash to the banked edition either" >&2
  fi
done
rmdir "$PART" 2>/dev/null || true
echo "source bytes: $(du -sh "$DIR" | cut -f1) in $DIR"
python3 "$(dirname "${BASH_SOURCE[0]}")/pin_sources.py"
