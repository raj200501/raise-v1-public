#!/usr/bin/env python3
"""Bank the counts that prose keeps quoting about the record itself.

Why this exists: on 2026-09-04 the outbound documents carried three different counts of the
corrections ledger (12, 13 and "thirteen") and two of the preregistration chain (11 and 13),
none of them registered with tools/freshness.py, so every gate passed while the numbers drifted.
This tool writes the counts to an artifact; docs/live_claims.json ties each sentence to it.

The output is deterministic (no timestamps), so the artifacts digest is stable across gate runs.
"""
from __future__ import annotations

import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, "CORRECTIONS.md")
OUT = os.path.join(REPO, "artifacts", "verification", "record_counts.json")
ENTRY = re.compile(r"^## (\d{4}-\d{2}-\d{2}) ", re.M)


def main() -> int:
    text = open(LEDGER, encoding="utf-8").read()
    dates = ENTRY.findall(text)
    if not dates:
        print("record_counts: no dated entries found in CORRECTIONS.md")
        return 1
    doc = {
        "schema": "raise-v1/record_counts/1",
        "source": "CORRECTIONS.md",
        "rule": "one entry per heading of the form '## YYYY-MM-DD '; the template heading does not match",
        "corrections_entries": len(dates),
        "corrections_first_date": min(dates),
        "corrections_latest_date": max(dates),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"record_counts: {len(dates)} corrections entries ({min(dates)} .. {max(dates)}) -> "
          f"{os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
