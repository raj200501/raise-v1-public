#!/usr/bin/env python3
"""Frozen reader for preregistration 0012 — does a budgeted, SYMMETRIC recipe search clear the
0.05 margin bar at the 2048-byte carve?

Written and committed BEFORE any candidate was fitted on the 2048-byte corpus under this
preregistration.

WHY THIS EXISTS. 0011 measured the incumbent recipe at 2048 and returned CARVE_FAILS with the
frozen-set margin 0.0025 short of the bar (0.1741 against logistic 0.1266) and the expanded margin
+0.0294 (against the depth-16 tree 0.1447). VERDICT.md names the next question: a gap that small
"is exactly the gap a per-head recipe search might close", and "a training recipe tuned under one
architecture is not architecture-neutral, and freezing it privileges the incumbent". This
preregistration answers it the only fair way: every HEAD with a hyperparameter - the model, the
logistic, the depth-3 tree, the deep tree - is an enumerated roster of the same size, selected by
the same rule on the same chunk-rule holdout, and each head's selected recipe is fitted once on
the same 500000 training rows 0011 used and scored once on 0011's sealed evaluation set, the
model last.

THE BAR (frozen). Validity and control first, then 0011's three margin clauses:

  scope            preregistration stamp, not a smoke run, the corpus cache's build metadata and
                   array hashes, seed 20260825, eval_frac 0.2, top rung 500000, the protocol
                   block equal to the constants sealed here, and the roster (protocol and every
                   head's candidate list) hashing to ROSTER_SHA256
  sealed sets      the evaluation set (index and label hashes, 130000 rows, 5000 chunks, 113412
                   non-gutenberg rows), the pool (500000 rows, 20000 chunks), the holdout
                   (chunk_id % 5 == 0: 100169 rows, 4002 chunks), the fit pool, the stage
                   blocks - every hash and count equal to the values computed from the banked
                   cache and written here before any 0012 fit
  no leakage       the split is grouped by source; measured chunk overlaps holdout/eval,
                   holdout/fit-pool, fit-pool/eval are 0; 0 eval rows in either; stage select
                   gathered 0 eval rows; the confirmatory artifact embeds the selection file and
                   its sha256 equals the file on disk and the hash bound into every confirmatory
                   ledger entry; selection finished before confirmation started
  search as        every searched candidate has exactly one stage-1 record in roster order with
  enumerated       the preregistered seed, row count, row hash and params hash; the reader
                   RE-DERIVES each head's ranking, advanced set and winner (highest holdout top-1
                   among status 'fit', ties at 4 decimals to the lower roster index); any baseline
                   record that is not 'fit' is VOID (a baseline that drops out can only flatter
                   the model); on the model side at most 2 infeasible_memory records with banked
                   evidence, never the incumbent
  one scoring      every confirmatory role has status 'fit', finite scores, a 130000-length
  per role         per-example vector, one ledger completion, the selected id (no substitution);
                   the model's record is the LAST completion in the ledger
  environment      every record ran at 3 threads, nice 10, the banked sklearn and numpy
  reproduction     the incumbent refit is within 0.005 of 0.1741 and the 0011 logistic refit is
                   within 0.005 of 0.1266 - the pool is the pool
  null control     shuffled labels with the SELECTED model recipe <= chance + 0.02
  bar arithmetic   bar_h = max(head h's confirmatory top-1, floor_h) with 0011's floors; the
                   banked bars equal the reader's recomputation
  margin F         final_top1 - max over the frozen heads of bar_h                  >= 0.05
  margin S         final_top1 - max over all six baseline heads of bar_h           >= 0.05
  margin S-ng      the expanded reading on the non-gutenberg rows with its floors  >= 0.05

The floors are 0011's banked values per head, so the searched baselines can raise the bar and
never lower it. The frozen-non-gutenberg clause is not added: its bar can never exceed the
expanded-non-gutenberg bar. A run in which only margin F clears is RECIPE_FAILS; the reader
banks `frozen_reading_clears` beside the verdict stamped informational, never as a verdict value.

VERDICTS, stated here before the data:

  VOID            a validity or control clause fails, or any field the reader needs is missing or
                  not finite (NaN and inf read as absent), or the artifact is not complete. No
                  result in either direction; the failed clauses and missing roles are named.
  RECIPE_FAILS    valid run; any margin clause fails. Under a budgeted, symmetric search of the
                  preregistered recipe space, the 2048-byte carve does not clear the 0.05 bar; the
                  window boundary statement (2048, 4096] stands for the frozen recipe and for this
                  searched space.
  RECIPE_CLEARS   valid run; every margin clause passes. The 2048-byte carve clears the bar under
                  a preregistered, symmetric search. A statement about the searched recipe only:
                  0011's CARVE_FAILS for the frozen recipe stands unrevised, no lower end is
                  claimed for the searched recipe (1024 was not measured under a search), and it
                  does NOT establish a buyer.

NOT RUN is not a verdict: if artifacts/pivot/recipe_search_2048_not_run.json exists and no
artifact does, the reader prints the rule that stopped the run and exits 2 (pending).

Anti-shield clauses (frozen):
  - Every set the run touches is tied to this preregistration by hash, not by the script's word.
  - The roster is tied by hash, so nothing can be added, removed or re-parameterised after
    seeing a number; every record carries a params hash the reader recomputes.
  - The winner is re-derived from the banked records, so a hand-picked winner is VOID.
  - Absence, NaN and inf read as VOID. Absence is never a pass and never a fail.
  - Margins are compared after rounding the difference to 6 decimals.
  - This reader cannot revise 0003, 0006, 0007 or 0011. establishes_a_buyer and
    revises_0003_0006_0007_0011 are emitted False unconditionally.

Exit codes: 0 verdict emitted; 2 artifact missing (pending or NOT RUN) or malformed.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "recipe_search_2048.json")
SELECTION = os.path.join(REPO, "artifacts", "pivot", "recipe_search_2048_selection.json")
SCORES = os.path.join(REPO, "artifacts", "pivot", "recipe_search_2048_scores.json")
NOT_RUN = os.path.join(REPO, "artifacts", "pivot", "recipe_search_2048_not_run.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "recipe_search_2048_verdict.json")

PREREG = "0012-recipe-search-2048"
SEED, EVAL_FRAC, TOP_RUNG = 20260825, 0.2, 500000
CORPUS = {"carve_bytes": 2048, "carve_bytes_source": "cache metadata written at build time",
          "chunk_size": 32768, "chunk_offset": 75000, "chunk_id_min": 75000, "chunk_id_max": 99999,
          "n_source_chunks": 25000, "n_rows": 650000, "n_features": 1108,
          # sha256 of the cache's y (int16) and g (int32) arrays as loaded, banked in
          # artifacts/pivot/corpus_manifest.json for data/pivot/carve_c2048.npz
          "cache_y_sha256": "7f008413fd5bff9a308ade8fa5769533c5ac557f66ce0f5789a664ac88316c73",
          "cache_g_sha256": "070a4b086f8f7bb84d8c730bb7963525a3fa8ddb4c862dba209a765e8c406c0c"}
PROTOCOL = {
    "seed": SEED, "eval_frac": EVAL_FRAC, "top_rung": TOP_RUNG, "threads": 3, "nice": 10,
    "carve": 2048, "chunk_offset": 75000, "chunk_size": 32768,
    "holdout": {"rule": "chunk_id_mod", "modulus": 5, "residue": 0},
    "stages": [{"rows": 100000, "keep": 2}, {"rows": "all", "keep": 1}],
    "caps": {"selection_fit_seconds": 72000, "memory_kill_gb": 12.5},
    "launch": {"min_disk_free_gb": 0.25, "min_mem_available_gb": 9.0},
    "null_rows": 20000, "incumbent_id": "M1", "logistic_l1_id": "L1", "logistic_head_id": "logistic",
    "confirm_order": ["incumbent", "logistic_l1", "majority", "stratified", "best_single_feat",
                      "depth3_tree", "deep_tree", "logistic", "null", "model"],
    "floors": {"majority": 0.0385, "stratified": 0.0385, "depth3_tree": 0.0887, "logistic": 0.1266,
               "best_single_feat": 0.0726, "deep_tree": 0.1447},
    "floors_non_gutenberg": {"majority": 0.0385, "stratified": 0.0385, "depth3_tree": 0.0898,
                             "logistic": 0.1315, "best_single_feat": 0.0762, "deep_tree": 0.1511},
}
FROZEN_HEADS = ("majority", "stratified", "depth3_tree", "logistic")
EXPANDED_HEADS = FROZEN_HEADS + ("best_single_feat", "deep_tree")
# sha256 of the canonical JSON (sort_keys, separators (",", ":"), ensure_ascii False) of
# prereg["scope"]["roster"] - the protocol block above and every head's candidate list - taken at
# freeze time. The roster lives under the sealed `scope` field, so the chain's sealed_sha256
# protects it as well.
ROSTER_SHA256 = "0956bb74d9cb60b74865bf4f8d9762170a81cd31c29d6c3fae07c2d8d3112c8b"
# Every hash and count below was computed on 2026-09-03 from data/pivot/carve_c2048.npz (the
# cache 0011 was scored on) with tools/pivot/run_carve.py grouped_split(seed 20260825, eval_frac
# 0.2, cap 500000) and the holdout rule above, before any 0012 fit. Digest convention: sha256 of
# np.ascontiguousarray(a).tobytes(); index arrays int64 in grouped_split / np.nonzero order; y as
# stored (int16); chunk-id sets and sorted sets np.sort(...).astype(np.int64).
PARTITION = {
    "seed": SEED, "eval_frac": EVAL_FRAC, "top_rung": TOP_RUNG, "split_is_grouped_by_source": True,
    "n_eval_rows": 130000, "n_eval_chunks": 5000, "n_eval_non_gutenberg": 113412,
    "eval_idx_sha256": "4036c7a58bd46113725adda2b3bf3602ca1597888ad1b934b46d327ef07536a3",
    "eval_y_sha256": "7bc394869e339686b8fe28e8b34a42dc9d6d53e0ad4b2ac3f4eeb58c20c14f45",
    "n_pool_rows": 500000, "n_pool_chunks": 20000,
    "pool_idx_sha256": "c716babc84a83fbc0a05b3b65a04614b171e20fa2653a02024e80ff7526d6c9d",
    "pool_y_sha256": "c5d6902effe3d2acb924b92ec6d65fcf03b60d248d3c60813f9bee95d11893a1",
    "pool_sorted_sha256": "45729322ca18dcd5041ff475ebf1bd30f48460be0ae0d143557fe26f0bc2ef2b",
    "holdout_rule": "chunk_id % 5 == 0",
    "n_holdout_rows": 100169, "n_holdout_chunks": 4002,
    "holdout_idx_sha256": "820792faeaac582f7a4be9473cbafca58377666bda9330cbcce3c68e800b2e80",
    "holdout_chunks_sha256": "38f7d35db793e72dc876d67db4a647e52063a2c09c1f6e36e9669479cdec40ad",
    "n_fitpool_rows": 399831, "n_fitpool_chunks": 15998,
    "fitpool_idx_sha256": "e6c3004ecfd94f115ae2ec6d7e8b583c17022b45f9c7cc0d8db0554779469ab0",
    "fitpool_chunks_sha256": "82146ba01ba8955b2c7f9cbc7782b78ee29f11299e956795a6c8a3d3d1d7a6ac",
    "stage_rows": [100000, 399831], "stage_keep": [2, 1], "stage_chunks": [15988, 15998],
    "stage_idx_sha256": ["e236dfff9a3abbf964145ab76de1cef66a8159550839b54c826301cb942790c6",
                         "e6c3004ecfd94f115ae2ec6d7e8b583c17022b45f9c7cc0d8db0554779469ab0"],
    "stage_sorted_sha256": ["5e01a28ec982b9ce361ddc63bb76a1452cc9d2fc28802de2a329c7094958ac88",
                            "b044d1f8e1d39cb35e976abff309e366690f3d2b327ddd3a0c282951cc1b1f09"],
    "n_chunks_holdout_and_eval": 0, "n_chunks_holdout_and_fitpool": 0, "n_chunks_fitpool_and_eval": 0,
    "n_eval_rows_in_holdout": 0, "n_eval_rows_in_fitpool": 0,
}
NULL_SORTED_SHA256 = "b49e356bbf2ff6969cc5cae3db769caac61cd15ad2f50c4d0a71c94fe7535722"   # first 20000 pool rows
# 0011's banked values on this evaluation set (artifacts/pivot/carve_generalisation_2048.json).
INCUMBENT_TOP1, LOGISTIC_L1_TOP1, REPRODUCTION_TOLERANCE = 0.1741, 0.1266, 0.005
MARGIN, NULL_TOLERANCE, CHANCE = 0.05, 0.02, 0.038462
ENV = {"threads": 3, "nice": 10, "sklearn": "1.9.0", "numpy": "2.4.6"}
MAX_MODEL_INFEASIBLE = 2


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_obj(obj) -> str:
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def main() -> int:
    if not os.path.exists(ARTIFACT):
        if os.path.exists(NOT_RUN):
            try:
                nr = json.load(open(NOT_RUN, encoding="utf-8"))
                print(f"READER 0012: NOT RUN — {nr.get('reason')!r} (stage {nr.get('stage')}, filed "
                      f"{nr.get('utc')}, {nr.get('n_checkpoints')} checkpoints). A NOT RUN is not a verdict.",
                      file=sys.stderr)
            except Exception:  # noqa: BLE001
                print("READER 0012: NOT RUN file present but unreadable.", file=sys.stderr)
            return 2
        print(f"READER 0012: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0012: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 2

    g = d.get
    void: list[str] = []
    fails: list[str] = []

    def num(v):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None
        return v if math.isfinite(v) else None

    def margin(a, b):
        return round(a - b, 6)

    def below(a, b):
        return margin(a, b) < MARGIN - 1e-9

    def expect_eq(where, got, want, label):
        if got != want:
            where.append(f"{label}={got!r}, preregistered {want!r}")

    # ---- scope
    if g("preregistration") != PREREG:
        void.append(f"scope: preregistration={g('preregistration')!r}, this reader is frozen for {PREREG}")
    if g("smoke") is not False:
        void.append(f"scope: smoke={g('smoke')!r}; a smoke run is not the preregistered run")
    if g("stage") != "confirm":
        void.append(f"scope: stage={g('stage')!r}, the verdict is read from the confirmatory artifact")
    corpus = g("corpus") or {}
    for k, v in CORPUS.items():
        expect_eq(void, corpus.get(k), v, f"scope: corpus.{k}")
    if g("n_classes") != 26 or num(g("chance_accuracy")) != CHANCE:
        void.append(f"scope: n_classes={g('n_classes')!r}, chance_accuracy={g('chance_accuracy')!r}")
    roster = g("roster") or {}
    if g("roster_sha256") != ROSTER_SHA256 or sha_obj(roster) != ROSTER_SHA256:
        void.append("scope: the banked roster does not hash to the sealed ROSTER_SHA256")
    proto = roster.get("protocol") or {}
    for k in sorted(set(PROTOCOL) | set(proto)):
        if proto.get(k) != PROTOCOL.get(k):
            void.append(f"scope: roster.protocol.{k}={proto.get(k)!r}, preregistered {PROTOCOL.get(k)!r}")
    heads = roster.get("heads") or []
    by_head = {h.get("id"): h for h in heads if isinstance(h, dict)}
    by_id = {c["id"]: c for h in heads for c in h.get("candidates", [])}
    model_head = next((h for h in heads if h.get("side") == "model"), None)
    if model_head is None:
        void.append("scope: no model head in the roster")
    for hid in EXPANDED_HEADS:
        if hid not in by_head:
            void.append(f"scope: baseline head {hid} absent from the roster")

    # ---- sealed sets and no leakage
    part = g("partition") or {}
    for k, v in PARTITION.items():
        expect_eq(void, part.get(k), v, f"sealed set: partition.{k}")
    if g("complete") is not True:
        void.append(f"complete: complete={g('complete')!r}; missing roles {g('missing_roles')!r}")
    sel = g("selection") or {}
    sel_sha = g("selection_sha256")
    if not os.path.exists(SELECTION):
        void.append("leakage: the selection file is absent from disk")
    else:
        on_disk = open(SELECTION, "rb").read()
        if hashlib.sha256(on_disk).hexdigest() != sel_sha:
            void.append("leakage: selection_sha256 does not equal the sha256 of the selection file on disk")
        try:
            if json.loads(on_disk) != sel:
                void.append("leakage: the embedded selection file differs from the file on disk")
        except Exception:  # noqa: BLE001
            void.append("leakage: the selection file on disk is not JSON")
    if sel.get("stage") != "select" or sel.get("preregistration") != PREREG or sel.get("smoke") is not False:
        void.append("leakage: the selection file is not this preregistration's stage-select output")
    if sel.get("roster_sha256") != ROSTER_SHA256 or sha_obj(sel.get("roster")) != ROSTER_SHA256:
        void.append("leakage: the selection file's roster does not hash to the sealed ROSTER_SHA256")
    if sel.get("eval_rows_gathered_in_selection") != 0 or \
            any(gt.get("n_eval_rows") != 0 for gt in (sel.get("gathers") or [])):
        void.append("leakage: stage select gathered evaluation rows")
    spart = sel.get("partition") or {}
    for k, v in PARTITION.items():
        if k != "eval_y_sha256":           # the label hash is banked only where labels were scored
            expect_eq(void, spart.get(k), v, f"leakage: selection.partition.{k}")
    if not (isinstance(sel.get("selection_finished_utc"), str) and isinstance(g("confirmatory_started_utc"), str)
            and sel["selection_finished_utc"] <= g("confirmatory_started_utc")):
        void.append("leakage: selection did not finish before confirmation started")
    ledger = g("ledger") or []
    for e in ledger:
        if isinstance(e, dict) and e.get("event") == "selection_bound" and e.get("selection_sha256") != sel_sha:
            void.append(f"leakage: confirmatory ledger entry {e.get('name')} bound to a different selection file")

    # ---- the search as enumerated, re-derived
    def ranked(records):
        pool = [r for r in records if r.get("status") == "fit" and num(r.get("top1")) is not None]
        out = []
        while pool:
            best = None
            for r in pool:
                if best is None or r["top1"] > best["top1"] + 1e-12:
                    best = r
            out.append(best["id"]); pool = [r for r in pool if r is not best]
        return out

    selected = g("selected_ids") or {}
    model_infeasible = 0
    for hid, h in by_head.items():
        cands = h.get("candidates") or []
        entry = (sel.get("selection") or {}).get(hid)
        if not isinstance(entry, dict):
            void.append(f"search: head {hid} has no selection entry"); continue
        if entry.get("side") != h.get("side"):
            void.append(f"search: head {hid} banked side {entry.get('side')!r} != roster side {h.get('side')!r}")
        if len(cands) == 1:
            if entry.get("stages") or entry.get("selected_id") != cands[0]["id"]:
                void.append(f"search: knob-free head {hid} must select its single candidate with no stages")
            if selected.get(hid) != cands[0]["id"]:
                void.append(f"search: selected_ids[{hid}]={selected.get(hid)!r} != {cands[0]['id']!r}")
            continue
        stages = entry.get("stages") or []
        if len(stages) != len(PROTOCOL["stages"]):
            void.append(f"search: head {hid} ran {len(stages)} stages, preregistered {len(PROTOCOL['stages'])}")
            continue
        expected = [c["id"] for c in cands]
        for si, st in enumerate(stages):
            recs = st.get("records") or []
            if [r.get("id") for r in recs] != expected:
                void.append(f"search: head {hid} stage {si + 1} records {[r.get('id') for r in recs]!r} are not "
                            f"{expected!r} in roster order"); break
            for r in recs:
                cid = r.get("id")
                if r.get("status") not in ("fit", "infeasible_memory"):
                    void.append(f"search: head {hid} {cid} stage {si + 1} status {r.get('status')!r}")
                elif r.get("status") != "fit":
                    if h.get("side") != "model":
                        void.append(f"search: baseline head {hid} candidate {cid} stage {si + 1} is "
                                    f"{r.get('status')!r}; a symmetric search with a missing baseline arm is "
                                    f"not symmetric")
                    else:
                        model_infeasible += 1
                        if not r.get("evidence"):
                            void.append(f"search: model candidate {cid} stage {si + 1} infeasible without evidence")
                        if cid == PROTOCOL["incumbent_id"]:
                            void.append("search: the incumbent is infeasible; the search cannot contain the recipe "
                                        "it was meant to improve on")
                if r.get("seed") != SEED or r.get("n_fit_rows") != PARTITION["stage_rows"][si] or \
                        r.get("fit_rows_sha256") != PARTITION["stage_idx_sha256"][si] or \
                        r.get("fit_rows_sorted_sha256") != PARTITION["stage_sorted_sha256"][si]:
                    void.append(f"search: head {hid} {cid} stage {si + 1} was not fitted on the sealed stage block "
                                f"with the preregistered seed")
                if r.get("params_sha256") != sha_obj(by_id.get(cid)):
                    void.append(f"search: head {hid} {cid} stage {si + 1} params hash is off-roster")
                if r.get("status") == "fit" and (num(r.get("top1")) is None or num(r.get("top1_non_gutenberg")) is None):
                    void.append(f"search: head {hid} {cid} stage {si + 1} is 'fit' without finite scores")
                renv = r.get("environment") or {}
                for k, v in ENV.items():
                    if renv.get(k) != v:
                        void.append(f"environment: head {hid} {cid} stage {si + 1} {k}={renv.get(k)!r}, banked {v!r}")
            rk = ranked(recs); keep = PROTOCOL["stages"][si]["keep"]
            if st.get("eligible_ranked_ids") != rk or st.get("advanced_ids") != rk[:keep]:
                void.append(f"search: head {hid} stage {si + 1} banked ranking/advance differs from the rule's")
            expected = rk[:keep]
        winner = expected[0] if expected else None
        if winner is None:
            void.append(f"search: head {hid} has no eligible candidate after the last stage")
        if entry.get("selected_id") != winner or selected.get(hid) != winner:
            void.append(f"search: head {hid} selected {entry.get('selected_id')!r} in the selection file and "
                        f"{selected.get(hid)!r} in the artifact; the rule yields {winner!r}")
    if model_infeasible > MAX_MODEL_INFEASIBLE:
        void.append(f"search: {model_infeasible} model-side infeasible records, at most {MAX_MODEL_INFEASIBLE}")
    if model_head is not None and g("selected_model_id") != selected.get(model_head["id"]):
        void.append("search: selected_model_id disagrees with selected_ids for the model head")

    # ---- confirmatory: one scoring per role, the selected recipe, the sealed pool
    final = g("final") or {}
    scores = {}
    if os.path.exists(SCORES):
        try:
            scores = (json.load(open(SCORES, encoding="utf-8")) or {}).get("per_example") or {}
        except Exception:  # noqa: BLE001
            void.append("confirmatory: the scores file is not JSON")
    else:
        void.append("confirmatory: the scores file is absent")

    def check_role(name, rec, cand_id, rows_sha, sorted_sha, n_rows, key):
        if not isinstance(rec, dict) or rec.get("status") != "fit":
            void.append(f"confirmatory: {name} status {(rec or {}).get('status')!r}; must be 'fit'"); return
        if num(rec.get("top1")) is None or num(rec.get("top1_non_gutenberg")) is None or \
                not isinstance(rec.get("per_family"), dict) or len(rec["per_family"]) != 8 or \
                any(num(v) is None for v in rec["per_family"].values()):
            void.append(f"confirmatory: {name} scores are not all finite")
        if rec.get("id") != cand_id:
            void.append(f"confirmatory: {name} record id {rec.get('id')!r} is not the selected {cand_id!r}")
        if rec.get("params_sha256") != sha_obj(by_id.get(cand_id)):
            void.append(f"confirmatory: {name} params hash is off-roster")
        if rec.get("seed") != SEED or rec.get("n_fit_rows") != n_rows or rec.get("fit_rows_sha256") != rows_sha \
                or rec.get("fit_rows_sorted_sha256") != sorted_sha:
            void.append(f"confirmatory: {name} was not fitted on the sealed rows with the preregistered seed")
        if any(not rf.get("probe_ok") for rf in (rec.get("block_refills") or [])):
            void.append(f"confirmatory: {name} banked a failed pool probe check")
        renv = rec.get("environment") or {}
        for k, v in ENV.items():
            if renv.get(k) != v:
                void.append(f"environment: {name} {k}={renv.get(k)!r}, banked {v!r}")
        done = [e for e in ledger if isinstance(e, dict) and e.get("name") == name and e.get("event") == "completed"]
        if len(done) != 1:
            void.append(f"confirmatory: {name} has {len(done)} ledger completions, must be exactly 1")
        if key is not None:
            pe = scores.get(key)
            if not isinstance(pe, list) or len(pe) != PARTITION["n_eval_rows"]:
                void.append(f"confirmatory: {name} per-example vector missing or not {PARTITION['n_eval_rows']} long")

    pool_sha, pool_sorted = PARTITION["pool_idx_sha256"], PARTITION["pool_sorted_sha256"]
    inc_id, l1_id, lh = PROTOCOL["incumbent_id"], PROTOCOL["logistic_l1_id"], PROTOCOL["logistic_head_id"]
    mh = model_head["id"] if model_head else None
    for hid in by_head:
        check_role(f"confirm_{hid}", final.get(hid), selected.get(hid), pool_sha, pool_sorted, TOP_RUNG, hid)
    inc = g("incumbent_refit") or {}
    if selected.get(mh) == inc_id:
        if inc != final.get(mh):
            void.append("reproduction: the incumbent won, so its refit must be the model's own record")
    else:
        check_role("confirm_incumbent", inc, inc_id, pool_sha, pool_sorted, TOP_RUNG, "incumbent")
    l1 = g("logistic_l1_refit") or {}
    if selected.get(lh) == l1_id:
        if l1 != final.get(lh):
            void.append("reproduction: L1 won the logistic head, so its refit must be that head's own record")
    else:
        check_role("confirm_logistic_l1", l1, l1_id, pool_sha, pool_sorted, TOP_RUNG, "logistic_l1")
    if num(inc.get("top1")) is None or abs(num(inc.get("top1")) - INCUMBENT_TOP1) > REPRODUCTION_TOLERANCE:
        void.append(f"reproduction: the incumbent refit scores {inc.get('top1')!r} against 0011's banked "
                    f"{INCUMBENT_TOP1}; the pool or the evaluation set is not 0011's")
    if num(l1.get("top1")) is None or abs(num(l1.get("top1")) - LOGISTIC_L1_TOP1) > REPRODUCTION_TOLERANCE:
        void.append(f"reproduction: the 0011 logistic refit scores {l1.get('top1')!r} against the banked "
                    f"{LOGISTIC_L1_TOP1}")
    nc = g("null_control") or {}
    if nc.get("status") != "fit" or nc.get("id") != g("selected_model_id") or nc.get("n_fit_rows") != PROTOCOL["null_rows"] \
            or nc.get("fit_rows_sorted_sha256") != NULL_SORTED_SHA256 or g("null_rows") != PROTOCOL["null_rows"]:
        void.append("null control: not the selected model recipe on the sealed 20000-row null block")
    if num(g("shuffled_label_accuracy")) is None:
        void.append("null control: shuffled_label_accuracy missing or not finite")
    elif num(g("shuffled_label_accuracy")) > CHANCE + NULL_TOLERANCE:
        void.append(f"null control: shuffled labels reached {g('shuffled_label_accuracy')}, above chance {CHANCE} + "
                    f"{NULL_TOLERANCE} with the selected recipe — the pipeline leaks")
    # the model's confirmatory completion must be the last completion in the ledger
    completions = [e.get("name") for e in ledger if isinstance(e, dict) and e.get("event") == "completed"
                   and str(e.get("name", "")).startswith("confirm_")]
    if not completions or completions[-1] != f"confirm_{mh}":
        void.append(f"order: the model's confirmatory fit was not the last completion ({completions[-1:]!r})")
    env = g("environment") or {}
    for k, v in ENV.items():
        if env.get(k) != v:
            void.append(f"environment: {k}={env.get(k)!r}, banked {v!r}")

    # ---- bar arithmetic re-derived
    def bars(key, floors):
        out = {}
        for hid in EXPANDED_HEADS:
            v = num((final.get(hid) or {}).get(key))
            out[hid] = None if v is None else max(v, floors[hid])
        return out

    b = bars("top1", PROTOCOL["floors"]); bn = bars("top1_non_gutenberg", PROTOCOL["floors_non_gutenberg"])
    if any(v is None for v in list(b.values()) + list(bn.values())):
        void.append("bars: a baseline head has no finite confirmatory score")
        bar_f = bar_e = bar_en = None
    else:
        bar_f = max(b[h] for h in FROZEN_HEADS); bar_e = max(b[h] for h in EXPANDED_HEADS)
        bar_en = max(bn[h] for h in EXPANDED_HEADS)
        for k, v in (("best_frozen_for_bar", bar_f), ("best_expanded_for_bar", bar_e),
                     ("best_expanded_non_gutenberg_for_bar", bar_en)):
            if num(g(k)) != v:
                void.append(f"bars: {k}={g(k)!r} is not the reader's recomputation {v!r}")

    frozen_clears = None
    top1, top1_ng = num(g("final_top1")), num(g("final_top1_non_gutenberg"))
    if top1 is None or top1_ng is None:
        void.append("field: final_top1 / final_top1_non_gutenberg missing or not finite")
    elif not void:
        if below(top1, bar_f):
            fails.append(f"margin F (frozen set): {top1} - {bar_f} = {margin(top1, bar_f)} is below {MARGIN}")
        frozen_clears = not below(top1, bar_f)
        if below(top1, bar_e):
            fails.append(f"margin S (expanded set): {top1} - {bar_e} = {margin(top1, bar_e)} is below {MARGIN}")
        if below(top1_ng, bar_en):
            fails.append(f"margin S-ng (expanded set, gutenberg excluded): {top1_ng} - {bar_en} = "
                         f"{margin(top1_ng, bar_en)} is below {MARGIN}")

    if void:
        verdict, meaning = "VOID", (
            "A validity or control clause fails, or the artifact is incomplete. This run says nothing about "
            "the bar in either direction.")
        boundary = "not bracketed by this run"
    elif fails:
        verdict, meaning = "RECIPE_FAILS", (
            "A margin clause fails. Under a budgeted, symmetric search of the preregistered recipe space, "
            "the 2048-byte carve does not clear the 0.05 bar; the window boundary statement (2048, 4096] "
            "stands for the frozen recipe and for this searched space.")
        boundary = "(2048, 4096], frozen and searched"
    else:
        verdict, meaning = "RECIPE_CLEARS", (
            "Every margin clause passes. The 2048-byte carve clears the 0.05 bar under a preregistered, "
            "symmetric recipe search. A statement about the searched recipe only: 0011's CARVE_FAILS for the "
            "frozen recipe stands unrevised, no lower end is claimed for the searched recipe, and nothing "
            "here establishes a buyer.")
        boundary = "clears at 2048 under search; below 2048 unmeasured under search; (2048, 4096] stands for the frozen recipe (0011)"

    result = {
        "schema": "raise-v1/recipe_search_2048_verdict/1",
        "preregistration": PREREG, "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "verdict": verdict, "meaning": meaning, "boundary_bytes": boundary,
        "validity_failed_clauses": void, "margin_failed_clauses": fails,
        "frozen_reading_clears": frozen_clears,
        "gain_over_incumbent": round(top1 - INCUMBENT_TOP1, 6) if top1 is not None else None,
        "incumbent_reproduction_drift": round(num(inc.get("top1")) - INCUMBENT_TOP1, 6) if num(inc.get("top1")) is not None else None,
        "logistic_l1_reproduction_drift": round(num(l1.get("top1")) - LOGISTIC_L1_TOP1, 6) if num(l1.get("top1")) is not None else None,
        "informational_only": "frozen_reading_clears, gain_over_incumbent, the reproduction drifts and the "
                              "artifact's cluster intervals are informational: not a verdict, not quotable as a "
                              "pass. The verdict is the `verdict` field and nothing else.",
        "bars_applied": {"frozen": bar_f, "expanded": bar_e, "expanded_non_gutenberg": bar_en,
                         "per_head": b, "per_head_non_gutenberg": bn, "margin": MARGIN},
        "establishes_a_buyer": False, "revises_0003_0006_0007_0011": False,
        "read": {k: g(k) for k in (
            "preregistration", "smoke", "stage", "complete", "missing_roles", "selected_model_id", "selected_ids",
            "final_top1", "final_top1_non_gutenberg", "final_per_family", "best_frozen_for_bar",
            "best_frozen_searched", "best_frozen_head", "best_expanded_for_bar", "best_expanded_searched",
            "best_expanded_head", "best_expanded_non_gutenberg_for_bar", "best_expanded_non_gutenberg_searched",
            "incumbent_refit_top1", "logistic_l1_refit_top1", "shuffled_label_accuracy", "chance_accuracy",
            "null_rows", "n_classes", "selection_sha256", "cluster_ci95_informational")},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("READER 0012 — symmetric recipe search at 2048")
    for k, v in result["read"].items():
        print(f"  {k:<44} {v}")
    for label, fl in (("VALIDITY", void), ("MARGIN", fails)):
        if fl:
            print(f"\n  {label} FAILED CLAUSES ({len(fl)}):")
            for f in fl:
                print(f"    · {f}")
    print(f"\n  VERDICT: {verdict}")
    print(f"  {meaning}")
    print("  This does not establish a buyer, and was never capable of doing so.")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
