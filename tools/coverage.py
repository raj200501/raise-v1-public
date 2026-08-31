#!/usr/bin/env python3
"""Verification-coverage map, enforced rather than asserted.

Every claim this project makes is placed in exactly one of three classes:

  primary-verifiable    a stranger can re-derive the number from raw inputs with shipped code
  arithmetic-verifiable the number follows by arithmetic from a banked artifact, but the artifact
                        itself rests on our run and cannot be re-derived by a stranger
  neither               asserted from a source we cannot re-derive or re-run

The point of the map is the third row, so this tool prints the weakest class FIRST and loudest,
and refuses to let a claim be filed as primary-verifiable unless the command that re-derives it
actually exists in this repository.

Checks, each of which exits non-zero:
  - every claim's cited artifact exists
  - every claim's cited value is actually present in that artifact
  - every class is one of the three
  - every primary-verifiable claim names a `reverify` command whose script exists on disk
  - every `neither` claim carries a written reason

Exit codes: 0 map is coherent; 1 a claim fails a check; 2 the map is missing or malformed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chainlib import REPO_ROOT  # noqa: E402

MAP = os.path.join(REPO_ROOT, "artifacts", "verification", "coverage.json")
CLASSES = ["neither", "arithmetic-verifiable", "primary-verifiable"]   # weakest first, deliberately
NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def values_in(obj):
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        yield float(obj)
    elif isinstance(obj, str):
        yield obj
        for m in NUM_RE.finditer(obj):
            try:
                yield float(m.group(0))
            except ValueError:
                pass
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from values_in(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from values_in(v)


def present(value, pool_nums: set[float], pool_strs: set[str]) -> bool:
    if isinstance(value, str):
        try:
            v = float(value)
        except ValueError:
            return value in pool_strs
        return any(abs(round(p, len(value.split(".")[1]) if "." in value else 0) - v) < 1e-9
                   for p in pool_nums) or value in pool_strs
    v = float(value)
    return any(abs(p - v) < 1e-9 for p in pool_nums)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", default=MAP)
    args = ap.parse_args()

    if not os.path.exists(args.map):
        print(f"coverage: map missing: {os.path.relpath(args.map, REPO_ROOT)}", file=sys.stderr)
        return 2
    try:
        claims = json.load(open(args.map, encoding="utf-8"))["claims"]
    except Exception as e:  # noqa: BLE001
        print(f"coverage: map malformed ({type(e).__name__}: {e})", file=sys.stderr)
        return 2

    problems: list[str] = []
    cache: dict[str, tuple[set, set]] = {}

    for c in claims:
        cid = c.get("id", "<no id>")
        cls = c.get("class")
        if cls not in CLASSES:
            problems.append(f"{cid}: class {cls!r} is not one of {CLASSES}")
            continue
        art = c.get("artifact")
        if not art:
            problems.append(f"{cid}: no artifact cited")
            continue
        apath = os.path.join(REPO_ROOT, art)
        if not os.path.exists(apath):
            problems.append(f"{cid}: cited artifact does not exist: {art}")
            continue
        if art not in cache:
            try:
                d = json.load(open(apath, encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                problems.append(f"{cid}: cited artifact is not readable JSON: {art} ({e})")
                cache[art] = (set(), set())
                continue
            nums, strs = set(), set()
            for v in values_in(d):
                (nums if isinstance(v, float) else strs).add(v)
            cache[art] = (nums, strs)
        nums, strs = cache[art]
        if "value" in c and not present(c["value"], nums, strs):
            problems.append(f"{cid}: value {c['value']!r} is not present in {art}")
        if cls == "primary-verifiable":
            cmd = c.get("reverify")
            if not cmd:
                problems.append(f"{cid}: filed primary-verifiable but names no reverify command")
            else:
                parts = shlex.split(cmd)
                script = next((p for p in parts if p.endswith(".py")), None)
                if script and not os.path.exists(os.path.join(REPO_ROOT, script)):
                    problems.append(f"{cid}: reverify command references a script that does not "
                                    f"exist: {script}")
        if cls == "neither" and not c.get("why_not_verifiable"):
            problems.append(f"{cid}: filed 'neither' but gives no reason")

    by_class = {k: [c for c in claims if c.get("class") == k] for k in CLASSES}
    print("VERIFICATION COVERAGE MAP — weakest class first, deliberately\n")
    for cls in CLASSES:
        rows = by_class[cls]
        banner = "!!! " if cls == "neither" else "    "
        print(f"{banner}{cls.upper()}  ({len(rows)} claim{'' if len(rows) == 1 else 's'})")
        for c in rows:
            print(f"      [{c.get('id')}] {c.get('claim','')[:96]}")
            print(f"          value={c.get('value')!r}  artifact={c.get('artifact')}")
            if cls == "neither":
                print(f"          why not verifiable: {c.get('why_not_verifiable','')[:150]}")
            elif cls == "primary-verifiable":
                print(f"          reverify: {c.get('reverify')}")
        print()

    total = len(claims)
    print(f"{total} claim(s): "
          + ", ".join(f"{len(by_class[k])} {k}" for k in CLASSES))
    if problems:
        print(f"\nCOVERAGE: FAIL ({len(problems)} problem(s))")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nCOVERAGE: PASS — every claim cites an artifact that exists and contains its value; "
          "every primary-verifiable claim names a command that exists.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
