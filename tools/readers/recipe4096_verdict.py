#!/usr/bin/env python3
"""Frozen reader for preregistration 0014 — does the headline 4096-byte result survive a SYMMETRIC
recipe search?

Written and committed BEFORE any candidate was fitted on corpus A under this preregistration.

WHY THIS EXISTS. At 2048 (0012, read under 0013) a symmetric recipe search moved the standardised
logistic baseline more than it moved the model, and the margin fell. The record's headline
(0003, CURVE_ESTABLISHED: 0.2395 against a raw logistic at 0.1392 and an unpruned depth-16 tree at
0.1812) was measured against baselines that same search could beat. This reader applies 0012's
protocol, clauses and verdict rule, byte for byte apart from the constants below, to corpus A:
0003's corpus, 0003's sealed evaluation set (260000 rows, 10000 chunks), 0003's 800000-row pool,
0003's baseline values as floors, and 0003's 0.2395 and 0.1392 as the reproduction controls. It is
0013's reader (the corrected order line included) with every 2048 constant replaced by its 4096
counterpart. Either outcome is published at the same size; a RECIPE_FAILS is a correction against
the headline's framing, filed in full.

Everything after this paragraph is 0013's reader with the constants replaced.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "recipe_search_4096.json")
SELECTION = os.path.join(REPO, "artifacts", "pivot", "recipe_search_4096_selection.json")
SCORES = os.path.join(REPO, "artifacts", "pivot", "recipe_search_4096_scores.json")
NOT_RUN = os.path.join(REPO, "artifacts", "pivot", "recipe_search_4096_not_run.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "recipe_search_4096_verdict.json")

PREREG = "0014-recipe-search-4096"
REREAD = PREREG
SEED, EVAL_FRAC, TOP_RUNG = 20260825, 0.2, 800000
CORPUS = {"carve_bytes": 4096,
          "carve_bytes_source": "sealed cache identity (sha256 of y and g); the cache carries no build metadata",
          "chunk_size": 32768, "chunk_offset": 0, "chunk_id_min": 0, "chunk_id_max": 49999,
          "n_source_chunks": 50000, "n_rows": 1300000, "n_features": 1108,
          # sha256 of corpus A's y (int16) and g (int32) arrays as loaded, banked in
          # artifacts/pivot/corpus_manifest.json for data/pivot/full_c4096.npz
          "cache_y_sha256": "2b70426881e569f303c400b8dc2b3cb69f30dbe2e36a93dff56df54df9acf093",
          "cache_g_sha256": "eda31b7cfa24640dff694c00e62849537490c9572966a5247d1f5127800e4df9"}
PROTOCOL = {
    "seed": 20260825,
    "eval_frac": 0.2,
    "top_rung": 800000,
    "threads": 3,
    "nice": 10,
    "carve": 4096,
    "chunk_offset": 0,
    "chunk_size": 32768,
    "holdout": {
        "rule": "chunk_id_mod",
        "modulus": 5,
        "residue": 0
    },
    "stages": [
        {
            "rows": 100000,
            "keep": 2
        },
        {
            "rows": "all",
            "keep": 1
        }
    ],
    "caps": {
        "selection_fit_seconds": 120000,
        "memory_kill_gb": 13.0
    },
    "launch": {
        "min_disk_free_gb": 0.25,
        "min_mem_available_gb": 12.0
    },
    "null_rows": 20000,
    "incumbent_id": "M1",
    "logistic_l1_id": "L1",
    "logistic_head_id": "logistic",
    "confirm_order": [
        "incumbent",
        "logistic_l1",
        "majority",
        "stratified",
        "best_single_feat",
        "depth3_tree",
        "deep_tree",
        "logistic",
        "null",
        "model"
    ],
    "floors": {
        "majority": 0.0385,
        "stratified": 0.0387,
        "depth3_tree": 0.0969,
        "logistic": 0.1392,
        "best_single_feat": 0.0751,
        "deep_tree": 0.1812
    },
    "floors_non_gutenberg": {
        "majority": 0.0385,
        "stratified": 0.0388,
        "depth3_tree": 0.0986,
        "logistic": 0.1438,
        "best_single_feat": 0.0769,
        "deep_tree": 0.1891
    },
    "cache_identity": {
        "y_sha256": "2b70426881e569f303c400b8dc2b3cb69f30dbe2e36a93dff56df54df9acf093",
        "g_sha256": "eda31b7cfa24640dff694c00e62849537490c9572966a5247d1f5127800e4df9"
    }
}
FROZEN_HEADS = ("majority", "stratified", "depth3_tree", "logistic")
EXPANDED_HEADS = FROZEN_HEADS + ("best_single_feat", "deep_tree")
# sha256 of the canonical JSON (sort_keys, separators (",", ":"), ensure_ascii False) of
# prereg["scope"]["roster"] - the protocol block above and every head's candidate list - taken at
# freeze time. The roster lives under the sealed `scope` field, so the chain's sealed_sha256
# protects it as well.
ROSTER_SHA256 = "fccad5345d152df80d8bc56128a081891eb23c91a77ac38439680a32940fc936"
# Every hash and count below was computed on 2026-09-04 from data/pivot/full_c4096.npz (corpus A, the
# cache 0003 was scored on) with tools/pivot/run_carve.py grouped_split(seed 20260825, eval_frac
# 0.2, cap 800000) and the holdout rule above, before any 0014 fit. Digest convention: sha256 of
# np.ascontiguousarray(a).tobytes(); index arrays int64 in grouped_split / np.nonzero order; y as
# stored (int16); chunk-id sets and sorted sets np.sort(...).astype(np.int64).
PARTITION = {
    "seed": 20260825,
    "eval_frac": 0.2,
    "top_rung": 800000,
    "split_is_grouped_by_source": True,
    "n_eval_rows": 260000,
    "n_eval_chunks": 10000,
    "n_eval_non_gutenberg": 227006,
    "eval_idx_sha256": "7da1099e0cf9d4c3903dad62f52c91f67b751113fc4bfc0a62c53f05dccf1efa",
    "eval_y_sha256": "92b95cf02a21945cea2a7bd756a1e1096b07ec351b478c39e795a8a2267400d1",
    "n_pool_rows": 800000,
    "n_pool_chunks": 40000,
    "pool_idx_sha256": "17b0dc0bd9f7b9db6a5f0967cd96cbdccf524da56ed1aac7a80c4b57eb8ee7e5",
    "pool_y_sha256": "d519612b4e46991f6ea1850fc92271e0de581e3cc378dd05fec59ff678dc72ea",
    "pool_sorted_sha256": "923cd266c3bf2a45683b2c479d36b046b311cc8f2e53426c962b6dd5ae836094",
    "holdout_rule": "chunk_id % 5 == 0",
    "n_holdout_rows": 160773,
    "n_holdout_chunks": 8040,
    "holdout_idx_sha256": "dd6cb8f7a7a7bdf6b5bcb0cebf0e533addc8e33f10e78c946c18723e449c7b02",
    "holdout_chunks_sha256": "9e0b446372c914311441d8af3e1c12b6644de115173e2a42c44d043b638c11c4",
    "n_fitpool_rows": 639227,
    "n_fitpool_chunks": 31960,
    "fitpool_idx_sha256": "2ebdb4606eeb8829b173e4dc9d47047c79914b685e5640fc2d43ace41affabaa",
    "fitpool_chunks_sha256": "fe7798e8a16c5cc4fea10be2f2171127c22cea223d3d5b01dbe655f790d8ac4e",
    "stage_rows": [
        100000,
        639227
    ],
    "stage_keep": [
        2,
        1
    ],
    "stage_chunks": [
        30778,
        31960
    ],
    "stage_idx_sha256": [
        "4b0465c58740b57d328025bd502068a5f63b78c25dc7399c054a43113e31eaae",
        "2ebdb4606eeb8829b173e4dc9d47047c79914b685e5640fc2d43ace41affabaa"
    ],
    "stage_sorted_sha256": [
        "75f42c8d2deaa6f52594d0275ef9a08b0e41cfe2aa7b8ed0f40688e67c824c90",
        "cd48b2cd2055f9431ceee5103048606d1cedae4387df59bb6d650d76be4bb2d1"
    ],
    "n_chunks_holdout_and_eval": 0,
    "n_chunks_holdout_and_fitpool": 0,
    "n_chunks_fitpool_and_eval": 0,
    "n_eval_rows_in_holdout": 0,
    "n_eval_rows_in_fitpool": 0
}
NULL_SORTED_SHA256 = "822b61020d276a04620440eb2d2e7e60376e1efba83e89607c33c09c39fa1425"   # first 20000 pool rows
# 0003's banked values on this evaluation set (artifacts/pivot/deflate_curve.json and
# artifacts/pivot/baseline_family_rescore.json).
INCUMBENT_TOP1, LOGISTIC_L1_TOP1, REPRODUCTION_TOLERANCE = 0.2395, 0.1392, 0.005
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
                print(f"READER 0014: NOT RUN — {nr.get('reason')!r} (stage {nr.get('stage')}, filed "
                      f"{nr.get('utc')}, {nr.get('n_checkpoints')} checkpoints). A NOT RUN is not a verdict.",
                      file=sys.stderr)
            except Exception:  # noqa: BLE001
                print("READER 0014: NOT RUN file present but unreadable.", file=sys.stderr)
            return 2
        print(f"READER 0014: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0014: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
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
            expected = [c["id"] for c in cands if c["id"] in rk[:keep]]   # survivors in ROSTER order, as the runner fits them
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
        void.append(f"reproduction: the incumbent refit scores {inc.get('top1')!r} against 0003's banked "
                    f"{INCUMBENT_TOP1}; the pool or the evaluation set is not 0003's")
    if num(l1.get("top1")) is None or abs(num(l1.get("top1")) - LOGISTIC_L1_TOP1) > REPRODUCTION_TOLERANCE:
        void.append(f"reproduction: the 0003 logistic refit scores {l1.get('top1')!r} against the banked "
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
            "the 4096-byte carve does not clear the 0.05 bar: the record's headline margin was measured "
            "against baselines a fair search beats. 0003's verdict stands on its own frozen reader; the "
            "headline framing is corrected at full size.")
        boundary = "the headline size fails under search; (2048, 4096] stands for the frozen recipe (0003, 0011)"
    else:
        verdict, meaning = "RECIPE_CLEARS", (
            "Every margin clause passes. The 4096-byte carve clears the 0.05 bar under a preregistered, "
            "symmetric recipe search: the headline result survives a fair baseline. A statement about "
            "4096 only; nothing below it is revised, and nothing here establishes a buyer.")
        boundary = "clears at 4096 under search; (2048, 4096] stands for the frozen recipe (0003, 0011)"

    result = {
        "schema": "raise-v1/recipe_search_4096_verdict/1",
        "preregistration": REREAD, "reads_artifact_of": PREREG, "source_artifact": os.path.relpath(ARTIFACT, REPO),
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

    print("READER 0014 — symmetric recipe search at 4096 (the headline size)")
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
