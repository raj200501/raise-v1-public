#!/usr/bin/env python3
"""Frozen reader for preregistration 0008 — the hunt for conjecture C1's falsifier.

Written and committed BEFORE any candidate was enumerated.

WHAT C1 SAYS. Withholding the transform's input is what creates the white space for a transform
label factory, and it is the same property that makes the market a forensics market and therefore
small. C1 is a conjecture, filed in the coverage map's weakest class, not a law.

WHAT WOULD FALSIFY IT. A transform label factory whose input is withheld for a reason OTHER than
after-the-fact loss — by privacy, by regulation, by physics, or by commercial boundary — with the
artifact still published in bulk, that clears G1..G5 and survives L1..L4.

THE BAR (frozen). A candidate SELECTS only if every one of these holds, and the default posture is
REJECT:

  withholding      mode in {privacy, regulation, physics, commercial} and the specific mechanism
                   that does the withholding is NAMED, not gestured at. "It is sensitive" is not a
                   mechanism; "42 U.S.C. 1320d-6" or "the plaintext no longer exists" is.
  not_loss         the withholding is not after-the-fact loss. A candidate whose input is merely
                   gone is the case C1 already covers and cannot falsify it.
  G1 abundance     >= 1e6 units, from a NAMED source with a VERIFIED count. An estimate, however
                   confident the prose around it, does not count. This clause is deliberately the
                   same measured standard round 4 raised the bar to.
  G2 manufacturer  labels at near-zero marginal cost, with the shape stated
  G3 monotonicity  a stated reason the task is not eaten by a larger general model
  G4 white space   checked FIRST-HAND, with raw HTTP status codes recorded per query. A failed
                   request that parses to zero results is NOT evidence of white space - the
                   archived trial nearly published exactly that error and caught it only by
                   checking the raw response.
  G5 buyer         a named buyer type AND a stated reason the market is not forensics-shaped. That
                   second half is the whole point: a candidate whose buyer is someone
                   reconstructing provenance after the fact confirms C1 rather than falsifying it.
  L1..L4           each survived, with a reason given per law

VERDICTS:
  C1_FALSIFIED         at least one candidate cleared everything
  NO_FALSIFIER_FOUND   none did

Anti-shield clauses (frozen):
  - NO_FALSIFIER_FOUND does NOT promote C1 to a law and this reader says so in its own artifact. A
    search that fails to find a counterexample is evidence about the search. Treating it as proof
    would be the exact error C1 itself is filed in the weakest class to avoid.
  - At least 12 candidates must be enumerated, and all four withholding modes must be represented,
    or the search was too narrow to conclude anything and the verdict is void.
  - A missing field reads as failure. Absence is never a pass.
  - This cannot revise 0001, 0002, 0003, 0006 or 0007.

Exit codes: 0 verdict emitted; 2 artifact missing or malformed.
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "phase0", "c1_falsifier_search.json")
OUT = os.path.join(REPO, "artifacts", "phase0", "c1_falsifier_verdict.json")

MIN_CANDIDATES = 12
MODES = {"privacy", "regulation", "physics", "commercial"}
GATES = ["G1_abundance_verified", "G2_manufacturer", "G3_monotonicity",
         "G4_white_space_firsthand", "G5_buyer_not_forensics"]
LAWS = ["L1", "L2", "L3", "L4"]


def candidate_fails(c):
    """Every reason this candidate does not SELECT. Empty list means it selects."""
    f = []
    mode = c.get("withholding_mode")
    if mode not in MODES:
        f.append(f"withholding_mode={mode!r} not in {sorted(MODES)}")
    if not str(c.get("withholding_mechanism", "")).strip():
        f.append("withholding_mechanism is empty - a mechanism must be named, not gestured at")
    if c.get("withholding_is_after_the_fact_loss") is not False:
        f.append("withholding is after-the-fact loss (or unstated); that is the case C1 covers and "
                 "cannot be falsified by")
    for g in GATES:
        if c.get(g) is not True:
            f.append(f"{g} is not True")
    n = c.get("G1_units")
    if not isinstance(n, (int, float)) or n < 1_000_000:
        f.append(f"G1_units={n!r} below 1e6 or not a number")
    if not str(c.get("G1_source", "")).strip():
        f.append("G1_source is empty - the count must come from a named source")
    if c.get("G1_count_is_verified") is not True:
        f.append("G1_count_is_verified is not True - an estimate does not clear this clause")
    queries = c.get("G4_queries")
    if not isinstance(queries, list) or not queries:
        f.append("G4_queries missing - white space must be checked first-hand")
    else:
        for q in queries:
            if not isinstance(q, dict) or "http_status" not in q:
                f.append("a G4 query records no http_status - a failed request that parses to zero "
                         "results is not evidence of white space")
                break
            if q.get("http_status") != 200:
                f.append(f"a G4 query returned http_status {q.get('http_status')!r}, not 200")
                break
    for law in LAWS:
        if c.get("laws_survived", {}).get(law) is not True:
            f.append(f"{law} not survived")
        elif not str(c.get("law_reasons", {}).get(law, "")).strip():
            f.append(f"{law} claimed survived with no reason given")
    if not str(c.get("G5_buyer_type", "")).strip():
        f.append("G5_buyer_type is empty")
    if not str(c.get("G5_why_not_forensics", "")).strip():
        f.append("G5_why_not_forensics is empty - a buyer reconstructing provenance after the fact "
                 "confirms C1 rather than falsifying it")
    return f


def main() -> int:
    if not os.path.exists(ARTIFACT):
        print(f"READER 0008: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0008: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 2

    cands = d.get("candidates")
    scope_fails = []
    if not isinstance(cands, list):
        print("READER 0008: candidates missing or not a list.", file=sys.stderr)
        return 2
    if len(cands) < MIN_CANDIDATES:
        scope_fails.append(f"only {len(cands)} candidates enumerated, need >= {MIN_CANDIDATES}")
    modes_seen = {c.get("withholding_mode") for c in cands} & MODES
    missing = sorted(MODES - modes_seen)
    if missing:
        scope_fails.append(f"withholding modes not represented: {missing}")

    per = []
    for c in cands:
        f = candidate_fails(c)
        per.append({"name": c.get("name"), "withholding_mode": c.get("withholding_mode"),
                    "selects": not f, "fails": f})
    selected = [p for p in per if p["selects"]]

    if scope_fails:
        verdict = "VOID_SEARCH_TOO_NARROW"
    elif selected:
        verdict = "C1_FALSIFIED"
    else:
        verdict = "NO_FALSIFIER_FOUND"

    result = {
        "schema": "raise-v1/c1_falsifier_verdict/1",
        "preregistration": "0008-c1-falsifier-search",
        "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "verdict": verdict,
        "n_candidates": len(cands),
        "n_selected": len(selected),
        "scope_failures": scope_fails,
        "per_candidate": per,
        "no_falsifier_found_does_not_promote_c1": (
            "A search that fails to find a counterexample is evidence about the search, not proof of "
            "the conjecture. C1 stays in the coverage map's weakest class regardless of this "
            "verdict, and stays labelled C1 rather than L5."),
        "establishes_a_buyer": False,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("READER 0008 — C1 falsifier search")
    print(f"  candidates enumerated           {len(cands)}")
    print(f"  withholding modes represented   {sorted(modes_seen)}")
    print(f"  selected                        {len(selected)}")
    for p in per:
        mark = "SELECT" if p["selects"] else "reject"
        print(f"    {mark}  {p['withholding_mode']:<11} {p['name']}")
        if not p["selects"]:
            print(f"            first blocker: {p['fails'][0]}")
    for f in scope_fails:
        print(f"  SCOPE FAILURE: {f}")
    print(f"\n  VERDICT: {verdict}")
    print(f"  {result['no_falsifier_found_does_not_promote_c1']}")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
