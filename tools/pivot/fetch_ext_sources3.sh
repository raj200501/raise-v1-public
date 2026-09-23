#!/usr/bin/env bash
# Fetch the NEW upstream files the fourth-doubling fit corpus (preregistration 0025) is built from, into
# data/pivot/ext_src3 (never committed). 0024's sources (tools/pivot/fetch_ext_sources2.sh) are needed too: the 0025 corpus
# nests on 0024's pool. Every file is checked against tools/pivot/ext_source_pins3.json by tools/pivot/corpus_realfit3.py
# before any chunk is cut; a changed upstream edition is a refusal, not a silent substitution. -f: an HTTP error is a
# failure, never a saved error page. --speed-limit: a stalled transfer is retried rather than waited on.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR="$(cd "$HERE/../.." && pwd)/data/pivot/ext_src3"
mkdir -p "$DIR/rfc3"
UA="raise-v1-research/1.0"
get() { local out="$1" url="$2"; [ -s "$out" ] && return 0
  curl -fsS --retry 5 --retry-all-errors --speed-time 30 --speed-limit 2000 --max-time 900 -A "$UA" -o "$out.part" "$url" \
    && mv "$out.part" "$out" || { rm -f "$out.part"; echo "fetch failed: $url" >&2; exit 1; }; }
export -f get; export UA
python3 - "$HERE/ext_source_pins3.json" <<'PY' | while read -r name url; do get "$DIR/$name" "$url"; done
import json, sys
p = json.load(open(sys.argv[1]))
for k, v in sorted(p["files"].items()):
    if "url" in v:
        print(k, v["url"])
PY
python3 - "$HERE/ext_source_pins3.json" <<'PY' | xargs -P 6 -I{} bash -c 'get "'"$DIR"'/rfc3/rfc{}.txt" "https://www.rfc-editor.org/rfc/rfc{}.txt"'
import json, sys
p = json.load(open(sys.argv[1]))
for k in sorted(p["files"]):
    if k.startswith("rfc3/"):
        print(k[len("rfc3/rfc"):-4])
PY
echo "fourth-doubling sources: $(du -sh "$DIR" | cut -f1) in $DIR"
python3 "$HERE/corpus_realfit3.py" --verify-pins
