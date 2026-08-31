#!/usr/bin/env python3
"""Outbound-copy gate: every number in a document must trace to a banked artifact.

Rule enforced: if a figure is not in a banked file under artifacts/, it does not go in a
document. A number appears in an email, a deck, a README or a report ONLY if some banked
artifact contains a value that rounds to it at the precision it was written.

Numbers that are legitimately not measurements (calendar years, an ISO date, a count of
sections, a version number) must be declared in docs/claimcheck_allowlist.tsv WITH A REASON.
The allowlist is auditable: it is a diffable file and every line carries its justification.

Principled exclusions, each of which is itself covered by a mutation test:
  - digits inside a URL          (a URL is an address, not a claim)
  - markdown ordered-list markers at line start
  - long hex strings (>=16 hex chars): commit ids and digests
  - SVG/HTML geometry attributes (x= y= points= viewBox= style=): where a mark is drawn is not a
    claim; the TEXT a chart displays still is, and is still checked
  - text on a line ending with the marker  <!-- claimcheck:ignore-line REASON -->

Exit codes: 0 all numbers backed; 1 unbacked numbers found; 2 usage/config error.
"""
from __future__ import annotations

import argparse
import csv
import glob
import io
import json
import os
import re
import sys
from typing import Iterable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chainlib import REPO_ROOT  # noqa: E402

ARTIFACT_DIR = os.path.join(REPO_ROOT, "artifacts")
ALLOWLIST = os.path.join(REPO_ROOT, "docs", "claimcheck_allowlist.tsv")

NUM_RE = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)(?:[eE]([+-]?\d+))?(?![\w])")
URL_RE = re.compile(r"(?:https?://|www\.)\S+")
# SVG/HTML geometry attributes: coordinates are where a mark is DRAWN, not a claim about the world.
# Only the quoted attribute VALUE is blanked; numbers in element text content - chart labels, which
# ARE claims - still reach the extractor. A style="" span is layout for the same reason.
GEOM_RE = re.compile(
    r'\b(?:x|y|x1|x2|y1|y2|cx|cy|r|rx|ry|dx|dy|width|height|points|viewBox|offset|style)='
    r'"[^"]*"')
HEX_RE = re.compile(r"\b[0-9a-fA-F]{16,}\b")
OL_RE = re.compile(r"^(\s*)(\d+)([.)]\s)")
IGNORE_LINE_RE = re.compile(r"<!--\s*claimcheck:ignore-line\b")
EPS = 1e-9


def iter_numbers(obj) -> Iterable[float]:
    """Every numeric leaf in a nested JSON structure, plus numbers embedded in strings."""
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        yield float(obj)
    elif isinstance(obj, str):
        for m in NUM_RE.finditer(obj):
            try:
                yield float(m.group(0))
            except ValueError:
                pass
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from iter_numbers(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_numbers(v)


def load_banked() -> tuple[set[float], list[str]]:
    """Collect every numeric value present in artifacts/. Returns (values, files_read)."""
    values: set[float] = set()
    files: list[str] = []
    for path in sorted(glob.glob(os.path.join(ARTIFACT_DIR, "**", "*"), recursive=True)):
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".json", ".jsonl", ".csv", ".tsv"):
            continue
        files.append(os.path.relpath(path, REPO_ROOT))
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except Exception:  # noqa: BLE001
            continue
        if ext == ".json":
            try:
                values.update(iter_numbers(json.loads(text)))
                continue
            except Exception:  # noqa: BLE001
                pass
        if ext == ".jsonl":
            ok = True
            for line in text.splitlines():
                if not line.strip():
                    continue
                try:
                    values.update(iter_numbers(json.loads(line)))
                except Exception:  # noqa: BLE001
                    ok = False
            if ok:
                continue
        if ext in (".csv", ".tsv"):
            delim = "\t" if ext == ".tsv" else ","
            for row in csv.reader(io.StringIO(text), delimiter=delim):
                for cell in row:
                    for m in NUM_RE.finditer(cell):
                        try:
                            values.add(float(m.group(0)))
                        except ValueError:
                            pass
            continue
        for m in NUM_RE.finditer(text):
            try:
                values.add(float(m.group(0)))
            except ValueError:
                pass
    return values, files


def load_allowlist() -> dict[str, str]:
    allowed: dict[str, str] = {}
    if not os.path.exists(ALLOWLIST):
        return allowed
    with open(ALLOWLIST, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 2 or not parts[1].strip():
                raise SystemExit(f"claimcheck: allowlist line lacks a reason: {line!r}")
            allowed[parts[0].strip()] = parts[1].strip()
    return allowed


def backed(token: str, banked: set[float]) -> bool:
    """A written number is backed if some banked value rounds to it at its own precision."""
    try:
        d = float(token)
    except ValueError:
        return False
    frac = token.split(".")[1] if "." in token else ""
    places = len(re.sub(r"[eE].*$", "", frac))
    for v in banked:
        for cand in (v, v * 100.0, v / 100.0):
            try:
                if abs(round(cand, places) - d) < EPS:
                    return True
            except (OverflowError, ValueError):
                continue
    return False


def scrub(line: str) -> str:
    """Blank out spans that are addresses/identifiers rather than claims."""
    line = URL_RE.sub(lambda m: " " * len(m.group(0)), line)
    line = GEOM_RE.sub(lambda m: " " * len(m.group(0)), line)
    line = HEX_RE.sub(lambda m: " " * len(m.group(0)), line)
    m = OL_RE.match(line)
    if m:
        line = m.group(1) + " " * len(m.group(2)) + m.group(3) + line[m.end():]
    return line


def check_file(path: str, banked: set[float], allowed: dict[str, str]) -> list[tuple[int, str, str]]:
    bad: list[tuple[int, str, str]] = []
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            if IGNORE_LINE_RE.search(raw):
                continue
            line = scrub(raw.rstrip("\n"))
            for m in NUM_RE.finditer(line):
                token = m.group(1)
                if token in allowed or m.group(0) in allowed:
                    continue
                if not backed(token, banked):
                    bad.append((lineno, token, raw.strip()[:150]))
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="documents to check (default: outbound/**)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    targets: list[str] = []
    for p in (args.paths or [os.path.join(REPO_ROOT, "outbound")]):
        if os.path.isdir(p):
            targets += [q for q in sorted(glob.glob(os.path.join(p, "**", "*"), recursive=True))
                        if os.path.isfile(q) and os.path.splitext(q)[1].lower() in (".md", ".txt", ".html")]
        elif os.path.isfile(p):
            targets.append(p)
        else:
            print(f"claimcheck: no such path: {p}", file=sys.stderr)
            return 2

    banked, files = load_banked()
    allowed = load_allowlist()
    if not targets:
        if not args.quiet:
            print("claimcheck: no documents to check")
        return 0

    total_bad = 0
    for t in targets:
        bad = check_file(t, banked, allowed)
        rel = os.path.relpath(t, REPO_ROOT)
        if bad:
            total_bad += len(bad)
            print(f"FAIL {rel}: {len(bad)} unbacked number(s)")
            for lineno, tok, ctx in bad:
                print(f"    {rel}:{lineno}: {tok!r} traces to no banked artifact | {ctx}")
        elif not args.quiet:
            print(f"ok   {rel}")

    if not args.quiet:
        print(f"\nbanked from {len(files)} artifact file(s), {len(banked)} distinct value(s); "
              f"allowlist has {len(allowed)} entr{'y' if len(allowed) == 1 else 'ies'}")
    if total_bad:
        print(f"\nCLAIMCHECK: FAIL - {total_bad} number(s) in outbound copy do not trace to an artifact.")
        return 1
    print("CLAIMCHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
