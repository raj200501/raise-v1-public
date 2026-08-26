#!/usr/bin/env python3
"""Frozen reader for preregistration 0009 — is the 1024-byte failure a property of the WINDOW, or
of the hand-engineered representation?

Written and committed BEFORE the raw-byte corpus was built and before any sequence model was trained.

WHY THIS EXISTS. Law L4 says a representation made of summary statistics over a fragment binds the
result to the fragment's length. When that law was written, this repository stated its own scope
limit in the same paragraph: it does NOT establish that a LEARNED representation over the raw bit
sequence would be window-bound, and none had been tested. 0007 returned CARVE_FAILS at 1024 using
1108 hand-engineered statistics, every one of which discards ORDER. This tests the alternative.

The comparison is exact, not approximate: the byte corpus is built from the SAME source chunks, at
the SAME carve, with the SAME seed and grouping as 0007's corpus B, so the model is evaluated on the
identical held-out fragments and its number sits directly beside 0007's.

THE BAR (frozen). BYTE_MODEL_CLEARS if and only if ALL hold:

  scope        n_train == matched_rung and split_is_grouped_by_source is True
  A2 margin    byte_model_top1 - best_trivial_baseline >= 0.05   (baselines on the SAME rows)
  beats hand   byte_model_top1 > feature_model_top1              (strictly - a representation that
               does not beat the one it replaces is not a better representation)
  null control byte_model_shuffled_top1 <= chance + 0.02

WHAT EACH OUTCOME MEANS, fixed now so neither can be spun later:

  BYTE_MODEL_CLEARS   L4's scope limit was the important part. 0007's CARVE_FAILS is specific to a
                      summary-statistic representation, NOT to the 1024-byte window, and this
                      document must say so wherever CARVE_FAILS is quoted.
  BYTE_MODEL_FAILS    L4 strengthens. The window binding is not an artifact of hand engineering, and
                      a model that sees byte ORDER - the thing every existing feature discards -
                      does not rescue it either.

Anti-shield clauses (frozen):
  - Trivial baselines are trained on the SAME rows as the byte model. Beating a starved baseline
    would flatter it, as it would have in 0003 and 0006.
  - The 'beats hand' clause exists because clearing A2 while losing to the feature model would mean
    the byte model is merely a different way of failing, and the headline would be false.
  - A missing field reads as failure. Absence is never a pass.
  - This cannot revise 0003, 0006 or 0007. CARVE_FAILS stands as the verdict on the representation
    it was measured with.

Exit codes: 0 verdict emitted; 2 artifact missing or malformed.
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "byte_model.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "byte_model_verdict.json")

MARGIN = 0.05
NULL_TOLERANCE = 0.02


def main() -> int:
    if not os.path.exists(ARTIFACT):
        print(f"READER 0009: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0009: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 2

    fails: list[str] = []
    g = d.get

    def num(k):
        v = g(k)
        return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    if g("split_is_grouped_by_source") is not True:
        fails.append("split: split_is_grouped_by_source is not True")
    n_train, rung = g("n_train"), g("matched_rung")
    if not isinstance(n_train, int) or not isinstance(rung, int) or n_train != rung:
        fails.append(f"scope: n_train={n_train!r} does not equal matched_rung={rung!r}; the "
                     f"comparison against the feature model would not be at a matched rung")

    top, base = num("byte_model_top1"), num("best_trivial_baseline")
    if top is None or base is None:
        fails.append("A2 margin: byte_model_top1 or best_trivial_baseline missing")
    elif top - base < MARGIN:
        fails.append(f"A2 margin: {top} - {base} = {round(top - base, 4)} is below the "
                     f"preregistered {MARGIN}")

    feat = num("feature_model_top1")
    if top is None or feat is None:
        fails.append("beats hand: byte_model_top1 or feature_model_top1 missing")
    elif top <= feat:
        fails.append(f"beats hand: {top} does not exceed the hand-engineered model's {feat} — a "
                     f"representation that does not beat the one it replaces is not a better "
                     f"representation")

    nul, chance = num("byte_model_shuffled_top1"), num("chance_accuracy")
    if nul is None or chance is None:
        fails.append("null control: byte_model_shuffled_top1 or chance_accuracy missing")
    elif nul > chance + NULL_TOLERANCE:
        fails.append(f"null control: shuffled labels reached {nul}, above chance {chance} + "
                     f"{NULL_TOLERANCE}")

    verdict = "BYTE_MODEL_CLEARS" if not fails else "BYTE_MODEL_FAILS"
    meaning = ("L4's scope limit was the important part: 0007's CARVE_FAILS is specific to a "
               "summary-statistic representation, NOT to the 1024-byte window, and that must be "
               "said wherever CARVE_FAILS is quoted."
               if verdict == "BYTE_MODEL_CLEARS" else
               "L4 strengthens. The window binding is not an artifact of hand engineering: a model "
               "that sees byte ORDER - the thing every existing feature discards - does not rescue "
               "it either.")

    result = {
        "schema": "raise-v1/byte_model_verdict/1",
        "preregistration": "0009-byte-sequence-representation",
        "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "verdict": verdict, "meaning": meaning, "failed_clauses": fails,
        "establishes_a_buyer": False,
        "read": {k: g(k) for k in
                 ("carve_bytes", "matched_rung", "n_train", "n_eval", "byte_model_top1",
                  "feature_model_top1", "best_trivial_baseline", "best_trivial_baseline_name",
                  "best_baseline_expanded", "best_baseline_expanded_name",
                  "byte_model_shuffled_top1", "chance_accuracy", "split_is_grouped_by_source",
                  "model_params", "epochs", "n_classes")},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("READER 0009 — byte-sequence representation at a 1024-byte carve")
    for k, v in result["read"].items():
        print(f"  {k:<30} {v}")
    if fails:
        print(f"\n  FAILED CLAUSES ({len(fails)}):")
        for f in fails:
            print(f"    · {f}")
    print(f"\n  VERDICT: {verdict}")
    print(f"  {meaning}")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
