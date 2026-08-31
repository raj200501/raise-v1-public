#!/usr/bin/env python3
"""Frozen reader for preregistration 0001 — the Phase 0 terminal verdict.

Written and committed BEFORE the round-3 search artifact exists. It reads the artifact and
emits exactly one of two verdicts, by a rule that cannot be adjusted once a number is known.

The bar (frozen):
    Phase 0 concludes DOMAIN_SELECTED if and only if at least one round-3 candidate satisfies
    ALL of the following simultaneously:
        adversarial overall_recommendation == "SELECT"
        g2a_verdict == "PASS"
        g3_verdict  == "PASS"
        g1_verdict  == "PASS"
        g6_verdict  == "PASS"
        its G4 verdict == "PASS"
    Otherwise Phase 0 concludes NO_VIABLE_DOMAIN_FOUND and terminates.

Anti-shield clauses (frozen, because a preregistration is a commitment and not a shield):
    - "BACKUP" does not satisfy the bar. Only "SELECT" does.
    - "MARGINAL" on any gate does not satisfy the bar. Only "PASS" does.
    - If a reviewer returns SELECT while any of its OWN gate verdicts is FAIL or MARGINAL, the
      reading taken is the gate verdict, not the recommendation. The non-flattering reading wins.
    - Zero adversarial reviews (e.g. every survivor failed G4) is NO_VIABLE_DOMAIN_FOUND. It is
      not "inconclusive" and it is not a reason to run a fourth round under this preregistration.
    - A missing or malformed artifact is a hard error, not a pass. Absence never reads as success.

Exit codes: 0 verdict emitted; 2 artifact missing or malformed.
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "phase0", "round3_domain_search.json")
OUT = os.path.join(REPO, "artifacts", "phase0", "phase0_verdict.json")

REQUIRED_PASS = ["g2a_verdict", "g3_verdict", "g1_verdict", "g6_verdict"]


def main() -> int:
    if not os.path.exists(ARTIFACT):
        print(f"READER 0001: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0001: artifact malformed ({type(e).__name__}: {e}). No verdict emitted.",
              file=sys.stderr)
        return 2

    reviews = d.get("adversarial", [])
    g4_by_domain = {g.get("domain", ""): g.get("g4_verdict") for g in d.get("g4_results", [])}

    rows = []
    for a in reviews:
        dom = a.get("domain", "")
        rec = a.get("overall_recommendation")
        gates = {k: a.get(k) for k in REQUIRED_PASS}
        g4 = a.get("g4_verdict") or g4_by_domain.get(dom)
        gate_fail = [k for k, v in gates.items() if v != "PASS"]
        qualifies = (rec == "SELECT" and not gate_fail and g4 == "PASS")
        reading = "QUALIFIES" if qualifies else "does not qualify"
        if rec == "SELECT" and gate_fail:
            reading = ("does not qualify — reviewer said SELECT but its own gate verdicts "
                       f"{', '.join(f'{k}={gates[k]}' for k in gate_fail)} do not read PASS; "
                       "the non-flattering reading is taken")
        elif rec == "SELECT" and g4 != "PASS":
            reading = (f"does not qualify — reviewer said SELECT but its G4 verdict is {g4!r}, "
                       "not PASS; the non-flattering reading is taken")
        rows.append({"domain": dom, "recommendation": rec, "g4_verdict": g4,
                     **gates, "qualifies": qualifies, "reading": reading})

    qualifying = [r for r in rows if r["qualifies"]]
    verdict = "DOMAIN_SELECTED" if qualifying else "NO_VIABLE_DOMAIN_FOUND"

    result = {
        "schema": "raise-v1/phase0_verdict/1",
        "preregistration": "0001-phase0-terminal-verdict",
        "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "n_adversarial_reviews": len(reviews),
        "n_qualifying": len(qualifying),
        "verdict": verdict,
        "qualifying_domains": [r["domain"] for r in qualifying],
        "rows": rows,
        "note": ("Zero adversarial reviews reads as NO_VIABLE_DOMAIN_FOUND, not as inconclusive."
                 if not reviews else ""),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print(f"READER 0001 — Phase 0 terminal verdict")
    print(f"  adversarial reviews read: {len(reviews)}")
    for r in rows:
        print(f"  - {r['domain'][:64]}")
        print(f"      rec={r['recommendation']} g4={r['g4_verdict']} "
              f"g2a={r['g2a_verdict']} g3={r['g3_verdict']} g1={r['g1_verdict']} g6={r['g6_verdict']}")
        print(f"      {r['reading']}")
    print(f"\n  VERDICT: {verdict}")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
