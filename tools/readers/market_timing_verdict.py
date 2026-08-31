#!/usr/bin/env python3
"""Frozen reader for preregistration 0004 - the market-timing search.

WHY THIS SEARCH IS DIFFERENT, AND WHY THAT NEEDS BOUNDING. Rounds 1-4 hunted UNSTUDIED problems
and found that large buyers are always crowded - the hole exists where the money is not. This
round inverts the hunt: look for markets that BECAME large recently, where existing literature
predates the money and therefore does not mean the opportunity is taken.

That is a genuine LOOSENING of G4, which is precisely the kind of move that lets a bar slip after
four negative results. So the loosening is bounded here, before any candidate is examined.

THE BAR (frozen). A candidate qualifies only if ALL hold:

  market_event_dated       a specific, citable, DATED event that created or mandated the buyer -
                           a regulation taking effect, a standard being finalised, a product
                           category appearing. Not a trend, not a forecast, not a market-size number.
  market_event_within_24mo the event is within 24 months of 2026-08-25.
  no_open_dataset          no open dataset of >= 10^6 labelled units for the task.
  post_event_efforts < 2   fewer than two serious efforts DATED AFTER the market event that target
                           the same task at comparable scale. Work predating the event does NOT count
                           against the candidate - that is the whole point - but it must be RECORDED.
  manufacturable           labels are free and exact at near-zero marginal cost, and the mechanism
                           is named.
  asymmetry_holds          the manufacturer knows something the student's input cannot contain.
  cpu_feasible             bytes_per_unit * 1e6 <= 20e9.

Anti-shield clauses (frozen):
  - "The market is growing" is NOT a dated event. A candidate without a specific citable date with a
    URL fails, however obviously large the market feels.
  - Pre-event literature is recorded in `prior_efforts` even though it does not disqualify. A search
    that does not look for it has not been run.
  - A MISSING field reads as failure. Absence is never a pass.
  - Failing any single clause fails the candidate. No aggregate score, no discretion.
  - This reader cannot overturn preregistrations 0001 or 0002. Those read the evidence of rounds
    1-4 and those readings stand.

Exit codes: 0 verdict emitted; 2 artifact missing or malformed.
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "market_timing", "candidates.json")
OUT = os.path.join(REPO, "artifacts", "market_timing", "verdict.json")
MAX_MONTHS = 24
MAX_BYTES = 20e9


def check(c: dict) -> list[str]:
    f = []
    if not c.get("market_event") or not c.get("market_event_date") or not c.get("market_event_url"):
        f.append("no dated, citable market event with a URL ('the market is growing' is not an event)")
    m = c.get("market_event_months_ago")
    if not isinstance(m, (int, float)):
        f.append("market_event_months_ago missing")
    elif m > MAX_MONTHS:
        f.append(f"market event is {m} months old, older than the frozen {MAX_MONTHS}")
    if c.get("open_dataset_at_1e6") is not False:
        f.append("an open dataset at >= 10^6 labelled units exists (or was not checked)")
    n = c.get("post_event_efforts_count")
    if not isinstance(n, int):
        f.append("post_event_efforts_count missing")
    elif n >= 2:
        f.append(f"{n} serious efforts postdate the market event, need < 2")
    if "prior_efforts" not in c:
        f.append("prior_efforts not recorded - pre-event work does not disqualify but must be looked for")
    if c.get("manufacturable") is not True or not c.get("manufacture_mechanism"):
        f.append("labels not established as manufacturable at near-zero cost, with the mechanism named")
    if c.get("asymmetry_holds") is not True or not c.get("asymmetry"):
        f.append("asymmetry not established (what does the manufacturer know that the student cannot?)")
    b = c.get("bytes_per_unit")
    if not isinstance(b, (int, float)):
        f.append("bytes_per_unit missing")
    elif b * 1e6 > MAX_BYTES:
        f.append(f"g6: {b} bytes/unit x 1e6 exceeds {MAX_BYTES:.3g}")
    return f


def main() -> int:
    if not os.path.exists(ARTIFACT):
        print(f"READER 0004: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              "  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0004: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 2

    rows = []
    for c in d.get("candidates", []):
        f = check(c)
        rows.append({"name": c.get("name", "<unnamed>"), "qualifies": not f, "failed_clauses": f})
    q = [r for r in rows if r["qualifies"]]
    verdict = "MARKET_TIMED_CANDIDATE_FOUND" if q else "NO_MARKET_TIMED_CANDIDATE_FOUND"

    res = {"schema": "raise-v1/market_timing_verdict/1",
           "preregistration": "0004-market-timing-search",
           "source_artifact": os.path.relpath(ARTIFACT, REPO),
           "n_candidates": len(rows), "n_qualifying": len(q),
           "verdict": verdict, "qualifying": [r["name"] for r in q], "rows": rows}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("READER 0004 - market-timing search")
    print(f"  candidates examined: {len(rows)}")
    for r in rows:
        print(f"  - {r['name'][:66]}: {'QUALIFIES' if r['qualifies'] else 'does not qualify'}")
        for x in r["failed_clauses"]:
            print(f"      · {x}")
    print(f"\n  VERDICT: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
