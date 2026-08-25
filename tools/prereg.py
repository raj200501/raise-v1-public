#!/usr/bin/env python3
"""Preregistration with hash-chained ordering and external not-before anchors.

The discipline this enforces:

  1. A preregistration names the SCOPE, freezes the BAR (the thresholds), freezes the
     READINGS (what will be read, in what units), and points at a READER SCRIPT that
     already exists on disk. The reader's sha256 is recorded at freeze time.
  2. Freezing appends to an append-only chain (prereg/chain.jsonl). Entry N carries
     prev_hash = hash of entry N-1, so the ORDER of preregistrations is tamper-evident:
     you cannot silently insert a preregistration between two existing ones.
  3. Freezing also embeds public randomness beacon pulses (NIST Interoperable
     Randomness Beacon 2.0 and drand). Those values are unpredictable before their
     round exists, so the entry proves NOT-BEFORE that round independently of git and
     independently of this repo's own history.
  4. `verify` recomputes the whole chain AND re-hashes every reader script. If a reader
     was edited after the bar was frozen, verification fails. That is the point: a
     reader written or adjusted after seeing the number is shaped by it.

Commands:
  new <slug>          scaffold prereg/NNNN-<slug>.json
  freeze <path>       anchor + hash + append to the chain (refuses if already frozen)
  verify              recompute chain, reader hashes, and file/entry agreement
  show                print the chain
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chainlib import REPO_ROOT, canon, git_dirty, git_head, sha256_file, sha256_obj  # noqa: E402

PREREG_DIR = os.path.join(REPO_ROOT, "prereg")
CHAIN = os.path.join(PREREG_DIR, "chain.jsonl")
GENESIS = "0" * 64

# Fields that are hashed into the chain entry. Anything not listed here is metadata and
# is NOT protected -- keep this list tight and explicit.
SEALED_FIELDS = [
    "id", "slug", "title", "scope", "bar", "readings", "reader",
    "reader_sha256", "arms", "stop_rules", "frozen_utc", "git_commit", "anchors",
]


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fetch(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers={"User-Agent": "raise-v1-prereg/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_anchors() -> dict:
    """Public not-before anchors. Records failures explicitly instead of silently omitting."""
    anchors = {}
    try:
        p = _fetch("https://beacon.nist.gov/beacon/2.0/pulse/last")["pulse"]
        anchors["nist_beacon_v2"] = {
            "chain": p["chainIndex"], "pulse": p["pulseIndex"],
            "time_stamp": p["timeStamp"], "output_value": p["outputValue"],
        }
    except Exception as e:  # noqa: BLE001
        anchors["nist_beacon_v2"] = {"COULD_NOT_VERIFY": str(e)[:200]}
    try:
        d = _fetch("https://api.drand.sh/public/latest")
        anchors["drand"] = {"round": d["round"], "randomness": d["randomness"]}
    except Exception as e:  # noqa: BLE001
        anchors["drand"] = {"COULD_NOT_VERIFY": str(e)[:200]}
    return anchors


def chain_entries() -> list[dict]:
    if not os.path.exists(CHAIN):
        return []
    with open(CHAIN, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def next_id() -> str:
    return f"{len(chain_entries()) + 1:04d}"


def cmd_new(args) -> int:
    os.makedirs(PREREG_DIR, exist_ok=True)
    pid = next_id()
    path = os.path.join(PREREG_DIR, f"{pid}-{args.slug}.json")
    if os.path.exists(path):
        print(f"refusing to overwrite {path}", file=sys.stderr)
        return 2
    doc = {
        "id": pid,
        "slug": args.slug,
        "title": "FILL IN",
        "scope": {
            "one_line": "FILL IN. State scope BEFORE the data: one corpus, one seed, one rung.",
            "corpus": "FILL IN", "seed": "FILL IN", "rungs": "FILL IN",
            "what_this_does_not_cover": "FILL IN",
        },
        "bar": {"FILL_IN_metric_name": {"threshold": 0.0, "direction": "higher_is_better",
                                        "passes_if": "FILL IN as an explicit inequality"}},
        "readings": [{"name": "FILL IN", "unit": "FILL IN", "source_artifact": "artifacts/FILL_IN.json",
                      "json_path": "FILL IN"}],
        "arms": ["FILL IN: including the rival explanation run as an arm, not as a paragraph"],
        "stop_rules": ["FILL IN: what result makes us stop and publish the negative"],
        "reader": "tools/readers/FILL_IN.py",
        "frozen": False,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")
    print(path)
    return 0


def cmd_freeze(args) -> int:
    path = args.path
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if doc.get("frozen"):
        print(f"{path} is already frozen; preregistrations are append-only", file=sys.stderr)
        return 2
    reader = doc.get("reader", "")
    reader_abs = os.path.join(REPO_ROOT, reader)
    if not os.path.exists(reader_abs):
        print(f"reader does not exist: {reader}\n"
              f"  The reader must be written BEFORE the data exists. That is the whole point.",
              file=sys.stderr)
        return 3
    for reading in doc.get("readings", []):
        if "FILL IN" in json.dumps(reading):
            print(f"unfilled reading in {path}: {reading}", file=sys.stderr)
            return 4
    if "FILL IN" in json.dumps(doc.get("bar", {})) or "FILL_IN" in json.dumps(doc.get("bar", {})):
        print(f"unfilled bar in {path}", file=sys.stderr)
        return 4

    doc["reader_sha256"] = sha256_file(reader_abs)
    doc["frozen_utc"] = _now()
    doc["git_commit"] = git_head(REPO_ROOT)
    doc["git_dirty_at_freeze"] = git_dirty(REPO_ROOT)
    doc["anchors"] = fetch_anchors()

    sealed = {k: doc.get(k) for k in SEALED_FIELDS}
    prev = chain_entries()
    prev_hash = prev[-1]["hash"] if prev else GENESIS
    entry = {"seq": len(prev) + 1, "id": doc["id"], "slug": doc["slug"],
             "frozen_utc": doc["frozen_utc"], "file": os.path.relpath(path, REPO_ROOT),
             "prev_hash": prev_hash, "sealed_sha256": sha256_obj(sealed)}
    entry["hash"] = sha256_obj({k: entry[k] for k in
                                ["seq", "id", "slug", "frozen_utc", "file", "prev_hash", "sealed_sha256"]})

    doc["frozen"] = True
    doc["chain_hash"] = entry["hash"]
    doc["chain_prev_hash"] = prev_hash
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")
    with open(CHAIN, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    print(f"FROZEN {doc['id']}-{doc['slug']}  seq={entry['seq']}  hash={entry['hash'][:16]}  "
          f"prev={prev_hash[:16]}")
    return 0


def cmd_verify(args) -> int:
    entries = chain_entries()
    problems: list[str] = []
    prev_hash = GENESIS
    seen_files = set()

    for i, e in enumerate(entries):
        if e.get("seq") != i + 1:
            problems.append(f"entry {i}: seq is {e.get('seq')}, expected {i + 1}")
        if e.get("prev_hash") != prev_hash:
            problems.append(f"entry {e.get('seq')}: prev_hash {str(e.get('prev_hash'))[:16]} "
                            f"!= actual predecessor {prev_hash[:16]} (chain order broken)")
        recomputed = sha256_obj({k: e[k] for k in
                                 ["seq", "id", "slug", "frozen_utc", "file", "prev_hash", "sealed_sha256"]})
        if recomputed != e.get("hash"):
            problems.append(f"entry {e.get('seq')}: hash mismatch (entry was edited)")
        prev_hash = e.get("hash", "")

        fpath = os.path.join(REPO_ROOT, e["file"])
        seen_files.add(os.path.abspath(fpath))
        if not os.path.exists(fpath):
            problems.append(f"entry {e['seq']}: file missing: {e['file']}")
            continue
        with open(fpath, encoding="utf-8") as fh:
            doc = json.load(fh)
        sealed = {k: doc.get(k) for k in SEALED_FIELDS}
        if sha256_obj(sealed) != e["sealed_sha256"]:
            problems.append(f"entry {e['seq']} ({e['file']}): sealed content changed after freezing")
        reader_abs = os.path.join(REPO_ROOT, doc.get("reader", ""))
        if not os.path.exists(reader_abs):
            problems.append(f"entry {e['seq']}: reader missing: {doc.get('reader')}")
        elif sha256_file(reader_abs) != doc.get("reader_sha256"):
            problems.append(f"entry {e['seq']}: READER EDITED AFTER FREEZE: {doc.get('reader')}\n"
                            f"      frozen={doc.get('reader_sha256')[:16]} "
                            f"now={sha256_file(reader_abs)[:16]}")

    for path in sorted(glob.glob(os.path.join(PREREG_DIR, "[0-9][0-9][0-9][0-9]-*.json"))):
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        if doc.get("frozen") and os.path.abspath(path) not in seen_files:
            problems.append(f"{os.path.relpath(path, REPO_ROOT)}: marked frozen but absent from the chain")

    if problems:
        print(f"PREREG CHAIN VERIFY: FAIL ({len(problems)} problem(s))")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"PREREG CHAIN VERIFY: PASS ({len(entries)} entr{'y' if len(entries) == 1 else 'ies'}, "
          f"head={prev_hash[:16] if entries else 'GENESIS'})")
    return 0


def cmd_show(args) -> int:
    for e in chain_entries():
        print(f"{e['seq']:>3}  {e['id']}-{e['slug']:<34}  {e['frozen_utc']}  {e['hash'][:16]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("new"); p.add_argument("slug"); p.set_defaults(fn=cmd_new)
    p = sub.add_parser("freeze"); p.add_argument("path"); p.set_defaults(fn=cmd_freeze)
    p = sub.add_parser("verify"); p.set_defaults(fn=cmd_verify)
    p = sub.add_parser("show"); p.set_defaults(fn=cmd_show)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
