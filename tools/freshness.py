#!/usr/bin/env python3
"""Gate: a number in a document must equal the CURRENT value in its artifact, not merely exist.

Why this is a separate gate. tools/claimcheck.py asks "does this number appear in some banked
artifact at the written precision?" That is the right question for a fabricated number and the
wrong question for a STALE one. A value that was true when it was written stays banked forever, so
it keeps passing after the world moves on. Both failures found so far are of that shape:

  - VERDICT.md said the preregistration chain had "1 entry, head cfcc915c" long after it had five
    entries and a different head. Both numbers were real; neither was current.
  - The mutation count in coverage.json said 49 while the suite ran 58, which broke CI for about an
    hour and was caught by the principal rather than by the instrument. That was patched with a
    one-off guard inside tests/mutation_test.py. This is the second instance of the same bug, so it
    gets a general mechanism instead of a second one-off.

Each registry entry names a file, a regex whose capture groups are the written values, an artifact,
and one path per group. The gate re-derives each path and compares. Registry:
docs/live_claims.json - which is data, so adding a claim needs no code change.

Path grammar, deliberately tiny so it can be audited by reading it:
    a.b.c                      nested keys; an integer component indexes a list (negatives allowed)
    <path>|len                 length
    <path>|head8               first 8 characters
    <path>|count:field=value   items of a list whose `field` equals `value`

Exit codes: 0 every live claim is current; 1 at least one is stale; 2 the registry is unusable.
"""
from __future__ import annotations

import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(REPO, "docs", "live_claims.json")


def resolve(doc, path):
    expr, _, op = path.partition("|")
    cur = doc
    for part in expr.split(".") if expr else []:
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    if not op:
        return cur
    if op == "len":
        return len(cur)
    if op == "head8":
        return str(cur)[:8]
    if op.startswith("count:"):
        field, _, want = op[len("count:"):].partition("=")
        return sum(1 for x in cur if str(x.get(field)) == want)
    raise KeyError(f"unknown operator {op!r} in path {path!r}")


def check(entry, repo=REPO):
    """Return (ok, [messages]). Anything that cannot be resolved is a FAILURE, never a skip."""
    msgs = []
    doc_path = os.path.join(repo, entry["file"])
    art_path = os.path.join(repo, entry["artifact"])
    if not os.path.exists(doc_path):
        return False, [f"{entry['id']}: document missing: {entry['file']}"]
    if not os.path.exists(art_path):
        return False, [f"{entry['id']}: artifact missing: {entry['artifact']}"]
    text = open(doc_path, encoding="utf-8").read()
    art = json.load(open(art_path, encoding="utf-8"))
    m = re.search(entry["pattern"], text)
    if not m:
        # A pattern that no longer matches means the sentence was reworded out from under the
        # registry. Silence there would be exactly the hole this gate exists to close.
        return False, [f"{entry['id']}: pattern does not match anything in {entry['file']} - "
                       f"the claim was reworded or removed, so it is no longer being checked"]
    if len(m.groups()) != len(entry["select"]):
        return False, [f"{entry['id']}: {len(m.groups())} capture group(s) but "
                       f"{len(entry['select'])} path(s)"]
    ok = True
    for written, path in zip(m.groups(), entry["select"]):
        try:
            current = resolve(art, path)
        except (KeyError, IndexError, TypeError, ValueError) as e:
            ok = False
            msgs.append(f"{entry['id']}: cannot resolve {path!r} in {entry['artifact']} "
                        f"({type(e).__name__}: {e})")
            continue
        if str(written) != str(current):
            ok = False
            msgs.append(f"{entry['id']}: {entry['file']} says {written!r}, "
                        f"{entry['artifact']}:{path} is currently {current!r}")
    return ok, msgs


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    reg_path = argv[0] if argv else REGISTRY
    repo = os.path.dirname(os.path.dirname(os.path.abspath(reg_path)))
    try:
        entries = json.load(open(reg_path, encoding="utf-8"))["claims"]
    except Exception as e:  # noqa: BLE001
        print(f"FRESHNESS: registry unusable ({type(e).__name__}: {e})", file=sys.stderr)
        return 2
    stale = []
    for entry in entries:
        ok, msgs = check(entry, repo)
        print(f"{'ok  ' if ok else 'STALE'} {entry['id']:<28} {entry['file']}")
        for msg in msgs:
            print(f"      · {msg}")
        if not ok:
            stale.append(entry["id"])
    print(f"\n{len(entries)} live claim(s) checked against their artifacts, {len(stale)} stale")
    if stale:
        print(f"FRESHNESS: FAIL ({', '.join(stale)})")
        return 1
    print("FRESHNESS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
