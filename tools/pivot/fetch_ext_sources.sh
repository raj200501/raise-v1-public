#!/usr/bin/env bash
# Fetch the upstream files the extension corpus (preregistration 0018) is built from, into
# data/pivot/ext_src (never committed). Every file is checked against tools/pivot/ext_source_pins.json
# by tools/pivot/corpus_ext.py before any chunk is cut; a changed upstream edition is a refusal, not a
# silent substitution. -f: an HTTP error is a failure, never a saved error page.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/data/pivot/ext_src"
mkdir -p "$DIR/rfc"
UA="raise-v1-research/1.0"
get() { local out="$1" url="$2"; [ -s "$out" ] && return 0
  curl -fsS --retry 3 --max-time 240 -A "$UA" -o "$out" "$url" || { rm -f "$out"; echo "fetch failed: $url" >&2; exit 1; }; }
get "$DIR/Python-3.11.9.tgz" "https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz"
get "$DIR/python-3.11.9-embed-amd64.zip" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
get "$DIR/sqlite-amalgamation-3450300.zip" "https://sqlite.org/2024/sqlite-amalgamation-3450300.zip"
for f in $(python3 -c "import json;print(' '.join(k[4:-4] for k in json.load(open('$(dirname "${BASH_SOURCE[0]}")/ext_source_pins.json'))['files'] if k.startswith('rfc/')))"); do
  get "$DIR/rfc/rfc${f}.txt" "https://www.rfc-editor.org/rfc/rfc${f}.txt"
done
echo "extension sources: $(du -sh "$DIR" | cut -f1) in $DIR"
python3 "$(dirname "${BASH_SOURCE[0]}")/corpus_ext.py" --verify-pins
