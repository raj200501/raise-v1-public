#!/usr/bin/env python3
"""Verify the fetched Project Gutenberg sources are the exact bytes the corpora were built from.

Called by tools/pivot/fetch_sources.sh after every download. For each file under data/pivot/src:

  sha256 == banked (artifacts/pivot/corpus_manifest.json)   -> ok
  sha256 is a known later upstream edition (source_pins.json) -> apply its recorded line edits,
                                                                 re-hash, must now equal banked
  anything else                                              -> FAIL, exit 1, name the file

Exit 1 is the whole point. Before this existed, a changed upstream edition would have gone into a
rebuilt corpus unnoticed until its arrays were hashed (CORRECTIONS.md 2026-09-02). The right source
bytes are necessary for a rebuild to match the banked manifest, not sufficient: X and g of the
caches tools/pivot/run_study.py build() writes (full_c4096, carve_c1024, carve_c2048) come out in
worker-completion row order and differ on every rebuild, by design; y and raw_c1024 rebuild
identical (CORRECTIONS.md, 2026-10-21, builder cache row order).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO, "data", "pivot", "src")
MANIFEST = os.path.join(REPO, "artifacts", "pivot", "corpus_manifest.json")
PINS = os.path.join(REPO, "tools", "pivot", "source_pins.json")


def sha256(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def apply_edits(path: str, edits: list[dict]) -> None:
    lines = open(path, "rb").read().split(b"\n")
    for e in edits:
        i = e["line"] - 1
        have = lines[i].decode("utf-8")
        if have != e["from"]:
            raise SystemExit(f"pin_sources: {os.path.basename(path)} line {e['line']} is not the "
                             f"recorded upstream text; refusing to edit blind.\n  have: {have!r}\n"
                             f"  want: {e['from']!r}")
        lines[i] = e["to"].encode("utf-8")
    with open(path, "wb") as fh:
        fh.write(b"\n".join(lines))


def main() -> int:
    banked = json.load(open(MANIFEST, encoding="utf-8"))["sources_sha256"]
    pins = json.load(open(PINS, encoding="utf-8"))["pins"]
    bad: list[str] = []
    for name, want in sorted(banked.items()):
        path = os.path.join(SRC, name)
        if not os.path.exists(path):
            print(f"MISSING  {name}"); bad.append(name); continue
        got = sha256(path)
        if got == want:
            print(f"ok       {name}"); continue
        edition = pins.get(name, {}).get("known_upstream_editions", {}).get(got)
        if edition is None:
            print(f"UNKNOWN  {name}: sha256 {got[:16]}… is neither the banked edition "
                  f"({want[:16]}…) nor a recorded upstream edition. Upstream has changed; the "
                  f"rebuild would NOT be byte-identical. Record the edition in "
                  f"tools/pivot/source_pins.json or say so in CORRECTIONS.md.")
            bad.append(name); continue
        apply_edits(path, edition["line_edits"])
        now = sha256(path)
        if now != want:
            print(f"FAIL     {name}: recorded edits applied but sha256 {now[:16]}… != banked")
            bad.append(name); continue
        print(f"pinned   {name}: upstream edition {got[:16]}… (seen {edition['observed_utc_date']}) "
              f"-> banked edition via {len(edition['line_edits'])} recorded line edit(s)")
    # tools/pivot/corpus.py load_real reads EVERY file here and refuses one that is not banked (cold-clone audit D5)
    for name in sorted(os.listdir(SRC)) if os.path.isdir(SRC) else []:
        if os.path.isfile(os.path.join(SRC, name)) and name not in banked:
            print(f"EXTRA    {name}: not a banked source; the corpus loader refuses a source directory "
                  f"holding it. Remove it."); bad.append(name)
    print("SOURCE PINS:", "PASS - every source is the banked edition" if not bad
          else f"FAIL ({len(bad)}: {', '.join(bad)})")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
