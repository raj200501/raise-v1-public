#!/usr/bin/env python3
"""Frozen reader for preregistration 0010 — the byte model with a position-preserving head.

Written and committed BEFORE the model was trained.

WHY THIS EXISTS. 0009 returned BYTE_MODEL_FAILS using a network that ends in a global average pool.
A probe then showed that pool averages away per-example identity: at identical convolutional
capacity, a flatten head memorises 5000 shuffled labels to 0.364 train accuracy where the pooled
head reaches 0.0486 against 0.0385 chance. That retired a caveat 0009 had published (see
CORRECTIONS.md) and left one real question open — whether the pooling hurt the TASK, not just
memorisation. 0010 answers it by changing ONLY the head.

THE NEW CLAUSE, and the reason this reader exists rather than a re-run of 0009's:

  A NULL CONTROL THE MODEL CANNOT FAIL CARRIES NO INFORMATION.

That is the argument tests/mutation_test.py already makes about gates - a gate that cannot fail is
decoration - and nobody in this repository had applied it to controls until a probe forced it. So
the null control here is TWO numbers, not one:

  null_train_top1   must be HIGH. The model must demonstrably fit shuffled labels, proving the
                    control had teeth. 0009's control was guaranteed clean by architecture, which
                    is worth nothing.
  null_eval_top1    must be at chance. Fitting shuffled labels must not generalise.

THE BAR (frozen). BYTE_FLAT_CLEARS if and only if ALL hold:

  scope           n_train == matched_rung and split_is_grouped_by_source is True
  A2 margin       flat_model_top1 - best_trivial_baseline          >= 0.05
  beats hand      flat_model_top1 > feature_model_top1             (strictly)
  beats pooled    flat_model_top1 > pooled_model_top1              (strictly - else the head change
                  did nothing and 0009's verdict simply stands)
  control failable null_train_top1                                 >= 0.30
  control clean   null_eval_top1 <= chance + 0.02

Anti-shield clauses (frozen):
  - Only the head changes. Same corpus, same rung, same seed, same grouped split, same conv stack,
    same epochs. A win from any other difference would not answer the question asked.
  - The evaluation set must be identical to 0007's corpus B, checked by fingerprint, not argued.
  - BYTE_FLAT_CLEARS would mean 0009's negative was an artifact of its head, and every place this
    repository quotes 0009 must then say so.
  - BYTE_FLAT_FAILS with a FAILABLE control is a much stronger negative than 0009's, and must be
    reported as strengthening L4 further rather than as a repeat.
  - A missing field reads as failure. Absence is never a pass.
  - This cannot revise 0003, 0006, 0007 or 0009.

Exit codes: 0 verdict emitted; 2 artifact missing or malformed.
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "byte_model_flat.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "byte_model_flat_verdict.json")

MARGIN = 0.05
NULL_TOLERANCE = 0.02
CONTROL_FAILABLE_MIN = 0.30


def main() -> int:
    if not os.path.exists(ARTIFACT):
        print(f"READER 0010: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0010: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 2

    fails: list[str] = []
    g = d.get

    def num(k):
        v = g(k)
        return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    if g("split_is_grouped_by_source") is not True:
        fails.append("split: split_is_grouped_by_source is not True")
    if g("eval_group_fingerprint_matches_0007") is not True:
        fails.append("split: the evaluation set is not verified identical to 0007's corpus B, so no "
                     "comparison against 0.1165 is like for like")
    n_train, rung = g("n_train"), g("matched_rung")
    if not isinstance(n_train, int) or not isinstance(rung, int) or n_train != rung:
        fails.append(f"scope: n_train={n_train!r} does not equal matched_rung={rung!r}")

    top = num("flat_model_top1")
    base = num("best_trivial_baseline")
    if top is None or base is None:
        fails.append("A2 margin: flat_model_top1 or best_trivial_baseline missing")
    elif top - base < MARGIN:
        fails.append(f"A2 margin: {top} - {base} = {round(top - base, 4)} is below {MARGIN}")

    for key, label in (("feature_model_top1", "beats hand"), ("pooled_model_top1", "beats pooled")):
        other = num(key)
        if top is None or other is None:
            fails.append(f"{label}: flat_model_top1 or {key} missing")
        elif top <= other:
            extra = ("" if label == "beats hand" else
                     " — the head change did nothing and 0009's verdict simply stands")
            fails.append(f"{label}: {top} does not exceed {other}{extra}")

    ntr = num("null_train_top1")
    if ntr is None:
        fails.append("control failable: null_train_top1 missing")
    elif ntr < CONTROL_FAILABLE_MIN:
        fails.append(f"control failable: null_train_top1={ntr} is below {CONTROL_FAILABLE_MIN} — the "
                     f"model cannot fit shuffled labels, so a clean null control would be guaranteed "
                     f"by architecture and would carry no information")

    nev, chance = num("null_eval_top1"), num("chance_accuracy")
    if nev is None or chance is None:
        fails.append("control clean: null_eval_top1 or chance_accuracy missing")
    elif nev > chance + NULL_TOLERANCE:
        fails.append(f"control clean: shuffled labels reached {nev} on evaluation, above chance "
                     f"{chance} + {NULL_TOLERANCE}")

    verdict = "BYTE_FLAT_CLEARS" if not fails else "BYTE_FLAT_FAILS"
    control_ok = not any(f.startswith("control failable") for f in fails)
    if verdict == "BYTE_FLAT_CLEARS":
        meaning = ("0009's negative was an artifact of its head. Every place this repository quotes "
                   "0009 must say so.")
    elif control_ok:
        meaning = ("A STRONGER negative than 0009's: this model demonstrably CAN fit shuffled "
                   "labels, so its clean evaluation control was earned rather than guaranteed by "
                   "architecture. L4 strengthens further.")
    else:
        meaning = ("Inconclusive on the point 0010 exists to settle: the control was not shown "
                   "failable, so this run repeats 0009's weakness rather than removing it.")

    result = {"schema": "raise-v1/byte_model_flat_verdict/1",
              "preregistration": "0010-byte-model-position-preserving-head",
              "source_artifact": os.path.relpath(ARTIFACT, REPO),
              "verdict": verdict, "meaning": meaning, "failed_clauses": fails,
              "null_control_was_failable": control_ok, "establishes_a_buyer": False,
              "read": {k: g(k) for k in
                       ("carve_bytes", "matched_rung", "n_train", "n_eval", "flat_model_top1",
                        "pooled_model_top1", "feature_model_top1", "best_trivial_baseline",
                        "best_trivial_baseline_name", "null_train_top1", "null_eval_top1",
                        "chance_accuracy", "split_is_grouped_by_source",
                        "eval_group_fingerprint_matches_0007", "model_params", "epochs")}}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True); fh.write("\n")

    print("READER 0010 — byte model with a position-preserving head")
    for k, v in result["read"].items():
        print(f"  {k:<34} {v}")
    if fails:
        print(f"\n  FAILED CLAUSES ({len(fails)}):")
        for f in fails:
            print(f"    · {f}")
    print(f"\n  VERDICT: {verdict}")
    print(f"  null control was failable: {control_ok}")
    print(f"  {meaning}")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
