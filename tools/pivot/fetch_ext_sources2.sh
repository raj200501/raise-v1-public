#!/usr/bin/env bash
# Fetch the upstream files the second-decade fit corpus (preregistration 0024) is built from, into
# data/pivot/ext_src2 (never committed). Every file is checked against tools/pivot/ext_source_pins2.json
# by tools/pivot/corpus_realfit2.py before any chunk is cut; a changed upstream edition is a refusal, not a
# silent substitution. -f: an HTTP error is a failure, never a saved error page. --speed-limit: a stalled
# transfer is retried rather than waited on.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR="$(cd "$HERE/../.." && pwd)/data/pivot/ext_src2"
mkdir -p "$DIR/rfc2"
UA="raise-v1-research/1.0"
get() { local out="$1" url="$2"; [ -s "$out" ] && return 0
  curl -fsS --retry 5 --retry-all-errors --speed-time 30 --speed-limit 2000 --max-time 900 -A "$UA" -o "$out.part" "$url" \
    && mv "$out.part" "$out" || { rm -f "$out.part"; echo "fetch failed: $url" >&2; exit 1; }; }
export -f get; export UA
# archives: name and url from the pins file
python3 - "$HERE/ext_source_pins2.json" <<'PY' | while read -r name url; do get "$DIR/$name" "$url"; done
import json, sys
p = json.load(open(sys.argv[1]))
for k, v in sorted(p["files"].items()):
    if "url" in v:
        print(k, v["url"])
PY
# RFCs: the pinned numbers, six at a time
python3 - "$HERE/ext_source_pins2.json" <<'PY' | xargs -P 6 -I{} bash -c 'get "'"$DIR"'/rfc2/rfc{}.txt" "https://www.rfc-editor.org/rfc/rfc{}.txt"'
import json, sys
p = json.load(open(sys.argv[1]))
for k in sorted(p["files"]):
    if k.startswith("rfc2/"):
        print(k[len("rfc2/rfc"):-4])
PY
echo "second-decade sources: $(du -sh "$DIR" | cut -f1) in $DIR"
python3 "$HERE/corpus_realfit2.py" --verify-pins
