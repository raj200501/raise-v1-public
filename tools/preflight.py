#!/usr/bin/env python3
"""Preflight: fail fast, at the top, with the cause and the fix.

A cold clone that dies forty frames deep inside a library has wasted the reader's time and
taught them nothing. This checks the interpreter floor and the dependency floors before any
real work starts, and every failure prints what is wrong AND the command that fixes it.

Exit codes: 0 ready; 1 something is missing or too old.
"""
from __future__ import annotations

import argparse
import importlib
import os
import platform
import re
import shutil
import sys

MIN_PYTHON = (3, 9)
REQ_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "requirements.txt")

# Import name may differ from the distribution name on PyPI.
IMPORT_NAME = {"scikit-learn": "sklearn"}


def parse_floors(path: str) -> list[tuple[str, tuple[int, ...] | None]]:
    floors = []
    if not os.path.exists(path):
        return floors
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            m = re.match(r"^([A-Za-z0-9_.\-]+)\s*(?:>=\s*([0-9][0-9.]*))?$", line)
            if not m:
                continue
            ver = tuple(int(p) for p in m.group(2).split(".")) if m.group(2) else None
            floors.append((m.group(1), ver))
    return floors


def version_tuple(v: str) -> tuple[int, ...]:
    parts = []
    for p in re.split(r"[.\-+]", v):
        if p.isdigit():
            parts.append(int(p))
        else:
            break
    return tuple(parts) or (0,)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--require", nargs="*", default=None,
                    help="only check these distributions (default: everything in requirements.txt)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    problems: list[tuple[str, str]] = []

    if sys.version_info < MIN_PYTHON:
        problems.append((
            f"Python {platform.python_version()} is below the floor "
            f"{'.'.join(map(str, MIN_PYTHON))}.",
            "Install a newer Python, e.g.  `uv python install 3.11`  or your platform's python3.11 package, "
            "then re-run with that interpreter.",
        ))

    floors = parse_floors(REQ_FILE)
    if args.require:
        wanted = set(args.require)
        floors = [f for f in floors if f[0] in wanted]

    installer = "uv pip install" if shutil.which("uv") else f"{sys.executable} -m pip install"
    for dist, floor in floors:
        mod = IMPORT_NAME.get(dist, dist.replace("-", "_"))
        try:
            m = importlib.import_module(mod)
        except Exception as e:  # noqa: BLE001
            problems.append((f"`{dist}` is not importable as `{mod}` ({type(e).__name__}: {e}).",
                             f"Run:  {installer} -r requirements.txt"))
            continue
        have = getattr(m, "__version__", None)
        if floor and have and version_tuple(have) < floor:
            problems.append((f"`{dist}` {have} is below the floor {'.'.join(map(str, floor))}.",
                             f"Run:  {installer} --upgrade '{dist}>={'.'.join(map(str, floor))}'"))
        elif not args.quiet:
            print(f"ok   {dist:<16} {have or '(no __version__)'}")

    if not args.quiet:
        print(f"ok   python           {platform.python_version()}  ({sys.executable})")

    if problems:
        print("\nPREFLIGHT: FAIL\n", file=sys.stderr)
        for cause, fix in problems:
            print(f"  cause: {cause}", file=sys.stderr)
            print(f"  fix:   {fix}\n", file=sys.stderr)
        return 1
    if not args.quiet:
        print("\nPREFLIGHT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
