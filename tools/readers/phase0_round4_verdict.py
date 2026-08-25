#!/usr/bin/env python3
"""Frozen reader for preregistration 0002 — the round-4 verdict.

Written and committed BEFORE any round-4 candidate was chosen and before any round-4
measurement was taken.

CONTEXT THIS READER EXISTS IN. Preregistration 0001 terminated Phase 0 with
NO_VIABLE_DOMAIN_FOUND over 99 candidates. Round 4 was authorised afterwards, by the
principal, to search the one class of problem the round-3 finding named and the earlier
pool never contained. Opening a round after a negative result is exactly the move that
needs scrutiny, so this preregistration raises the bar rather than lowering it: rounds 1-3
admitted ARGUED evidence, and this round admits only MEASURED evidence taken first-hand.

The bar (frozen). Round 4 concludes DOMAIN_SELECTED if and only if at least one candidate
satisfies ALL of the following simultaneously:

    g1_verdict            == "PASS"      and a licence_url is recorded
    g4_verdict            == "PASS"
    g2a_verified          is True        (absence from the student's input checked against
                                          the format spec or codebook, not assumed)
    a1_label_entropy_bits >  1.0         MEASURED on a real sample
    a2_margin_over_best_baseline >= 0.05 MEASURED; the preregistered margin is 0.05
    f5_slope_ci95_low     >  0.0         MEASURED over >= 3 rungs spanning >= 1.5 decades
    g6_bytes_per_unit * 1e6 <= 20e9
    measured_first_hand   is True

Otherwise the verdict is NO_VIABLE_DOMAIN_FOUND_ROUND4.

Anti-shield clauses (frozen):
  - A MISSING field reads as failure for that candidate. Absence is never a pass.
  - An ESTIMATED value never satisfies a MEASURED requirement. Every reading listed above as
    MEASURED must carry `"measured": true` on the candidate record; `false` or absent reads
    as failure, however confident the accompanying prose.
  - Zero candidates reaching the measurement stage reads as NO_VIABLE_DOMAIN_FOUND_ROUND4.
    It is not "inconclusive" and it does not license a fifth round.
  - This preregistration CANNOT overturn preregistration 0001's verdict. 0001 read the
    evidence of rounds 1-3 and that reading stands regardless of what happens here. A
    DOMAIN_SELECTED here is a NEW finding on NEW evidence, recorded alongside 0001's, never
    as a retraction of it.
  - A candidate that fails any single clause fails, no matter how strong the others are.
    There is no aggregate score and no discretion.
  - A missing or malformed artifact is a hard error, not a pass.

Exit codes: 0 verdict emitted; 2 artifact missing or malformed.
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "phase0", "round4_measurements.json")
OUT = os.path.join(REPO, "artifacts", "phase0", "round4_verdict.json")

MARGIN = 0.05
MIN_ENTROPY_BITS = 1.0
MAX_CORPUS_BYTES = 20e9


def check(c: dict) -> tuple[bool, list[str]]:
    """Returns (qualifies, list of reasons it does not)."""
    fails: list[str] = []

    def measured(key: str) -> bool:
        m = c.get("measured", {})
        return bool(m.get(key)) if isinstance(m, dict) else False

    if c.get("g1_verdict") != "PASS":
        fails.append(f"g1_verdict={c.get('g1_verdict')!r}, not PASS")
    if not c.get("licence_url"):
        fails.append("no licence_url recorded")
    if c.get("g4_verdict") != "PASS":
        fails.append(f"g4_verdict={c.get('g4_verdict')!r}, not PASS")
    if c.get("g2a_verified") is not True:
        fails.append("g2a_verified is not True (asymmetry not checked against the spec)")

    ent = c.get("a1_label_entropy_bits")
    if not isinstance(ent, (int, float)):
        fails.append("a1_label_entropy_bits missing")
    elif not measured("a1_label_entropy_bits"):
        fails.append("a1_label_entropy_bits is not marked measured")
    elif ent <= MIN_ENTROPY_BITS:
        fails.append(f"a1_label_entropy_bits={ent} does not exceed {MIN_ENTROPY_BITS}")

    marg = c.get("a2_margin_over_best_baseline")
    if not isinstance(marg, (int, float)):
        fails.append("a2_margin_over_best_baseline missing")
    elif not measured("a2_margin_over_best_baseline"):
        fails.append("a2_margin_over_best_baseline is not marked measured")
    elif marg < MARGIN:
        fails.append(f"a2_margin_over_best_baseline={marg} is below the preregistered {MARGIN}")

    lo = c.get("f5_slope_ci95_low")
    if not isinstance(lo, (int, float)):
        fails.append("f5_slope_ci95_low missing")
    elif not measured("f5_slope_ci95_low"):
        fails.append("f5_slope_ci95_low is not marked measured")
    elif lo <= 0.0:
        fails.append(f"f5_slope_ci95_low={lo} does not exceed 0")

    bpu = c.get("g6_bytes_per_unit")
    if not isinstance(bpu, (int, float)):
        fails.append("g6_bytes_per_unit missing")
    elif bpu * 1e6 > MAX_CORPUS_BYTES:
        fails.append(f"g6: {bpu} bytes/unit x 1e6 = {bpu * 1e6:.3g} exceeds {MAX_CORPUS_BYTES:.3g}")

    if c.get("measured_first_hand") is not True:
        fails.append("measured_first_hand is not True")

    return (not fails), fails


def main() -> int:
    if not os.path.exists(ARTIFACT):
        print(f"READER 0002: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0002: artifact malformed ({type(e).__name__}: {e}). No verdict emitted.",
              file=sys.stderr)
        return 2

    cands = d.get("candidates_measured", [])
    rows = []
    for c in cands:
        ok, fails = check(c)
        rows.append({"name": c.get("name", "<unnamed>"), "qualifies": ok, "failed_clauses": fails})

    qualifying = [r for r in rows if r["qualifies"]]
    verdict = "DOMAIN_SELECTED" if qualifying else "NO_VIABLE_DOMAIN_FOUND_ROUND4"

    result = {
        "schema": "raise-v1/round4_verdict/1",
        "preregistration": "0002-phase0-round4-verdict",
        "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "n_candidates_measured": len(cands),
        "n_qualifying": len(qualifying),
        "verdict": verdict,
        "qualifying_domains": [r["name"] for r in qualifying],
        "rows": rows,
        "relationship_to_prereg_0001": (
            "This verdict is recorded ALONGSIDE preregistration 0001's NO_VIABLE_DOMAIN_FOUND, "
            "never as a retraction of it. 0001 read the evidence of rounds 1-3 and that reading "
            "stands."),
        "note": ("Zero candidates reaching measurement reads as NO_VIABLE_DOMAIN_FOUND_ROUND4, "
                 "not as inconclusive." if not cands else ""),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("READER 0002 — round-4 verdict")
    print(f"  candidates measured: {len(cands)}")
    for r in rows:
        print(f"  - {r['name'][:70]}: {'QUALIFIES' if r['qualifies'] else 'does not qualify'}")
        for f in r["failed_clauses"]:
            print(f"      · {f}")
    print(f"\n  VERDICT: {verdict}")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
