#!/usr/bin/env python3
"""Frozen reader for preregistration 0015 — does the encoder-provenance signal survive content the
model has never seen? Leave-one-family-out transfer at 4096 with 0003's fixed recipes.

Written and committed BEFORE any fold was fitted under this preregistration.

WHY THIS EXISTS. Every verdict in this record trains and scores on the same eight content
families. The grouped split and the null control rule out memorising source chunks; nothing rules
out eight family-specific signatures. This reader takes the runner's artifact (tools/pivot/run_lofo.py)
and checks, clause by clause: the sealed corpus, split and folds (every hash a literal below); that
no fold's training rows contain a row of the held-out family or a chunk of the evaluation set; that
every fit is 0003's recipe (params hashes below), fitted on the sealed rows with the sealed seed and
scored exactly once; that the two reproduction controls land on 0003's banked values; that the null
control sits at chance; and that the LOFO mixture the verdict is read from equals what this reader
recomputes from the per-example vectors. Then one clause: the model's LOFO mixture accuracy against
chance + 0.05. TRANSFERS or TRANSFER_FAILS, published at the same size; VOID on any validity failure.

Every constant below was computed on 2026-09-08 from data/pivot/full_c4096.npz (corpus A) with
tools/pivot/run_carve.py grouped_split(seed 20260825, eval_frac 0.2, cap 800000) and the family
rule FAMILIES[chunk_id modulo 8], before any 0015 fit. Digest convention: sha256 of
np.ascontiguousarray(a).tobytes(); index arrays int64 in grouped_split / np.nonzero order; y as
stored (int16); sorted sets np.sort(...).astype(np.int64).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "lofo_4096.json")
SCORES = os.path.join(REPO, "artifacts", "pivot", "lofo_4096_scores.json")
NOT_RUN = os.path.join(REPO, "artifacts", "pivot", "lofo_4096_not_run.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "lofo_4096_verdict.json")
PREREG = "0015-lofo-4096"

FAMILIES = ["gutenberg", "base64", "binary", "code", "csv", "json", "log", "mixed"]
STRUCTURED = ["code", "csv", "json", "log"]
CORPUS = {'carve_bytes': 4096,
 'carve_bytes_source': 'sealed cache identity (sha256 of y and g); the cache carries no build metadata',
 'chunk_size': 32768,
 'chunk_offset': 0,
 'chunk_id_min': 0,
 'chunk_id_max': 49999,
 'n_source_chunks': 50000,
 'cache_y_sha256': '2b70426881e569f303c400b8dc2b3cb69f30dbe2e36a93dff56df54df9acf093',
 'cache_g_sha256': 'eda31b7cfa24640dff694c00e62849537490c9572966a5247d1f5127800e4df9',
 'n_rows': 1300000,
 'n_features': 1108}
# The sealed protocol block, key by key, and its hash; the banked protocol must equal both.
PROTOCOL = {'seed': 20260825,
 'eval_frac': 0.2,
 'top_rung': 800000,
 'threads': 3,
 'nice': 10,
 'carve': 4096,
 'chunk_offset': 0,
 'chunk_size': 32768,
 'cache_identity': {'y_sha256': '2b70426881e569f303c400b8dc2b3cb69f30dbe2e36a93dff56df54df9acf093',
                    'g_sha256': 'eda31b7cfa24640dff694c00e62849537490c9572966a5247d1f5127800e4df9'},
 'families': ['gutenberg', 'base64', 'binary', 'code', 'csv', 'json', 'log', 'mixed'],
 'fold_rows': 'all',
 'roles': ['majority', 'logistic', 'model'],
 'order': ['reproduction_model', 'reproduction_logistic', 'null', 'folds'],
 'null_rows': 20000,
 'structured_families': ['code', 'csv', 'json', 'log'],
 'caps': {'memory_kill_gb': 13.0},
 'launch': {'min_disk_free_gb': 0.25, 'min_mem_available_gb': 12.0},
 'bar': {'lofo_mixture_minus_chance': 0.05},
 'reproduction_tolerance': 0.005,
 'null_tolerance': 0.02}
PROTOCOL_SHA256 = "e245f35e1793042f9d3e441a88237de8b6db53c7810bd8a7b14c7580a0a14613"
# 0003's three fixed recipes, verbatim from 0014's sealed roster; their canonical-JSON hashes are what
# every record's params_sha256 must equal.
RECIPES = {'model': {'id': 'M1',
           'family': 'hgb',
           'val': 'frag',
           'params': {'learning_rate': 0.15, 'max_leaf_nodes': 63, 'max_iter': 200, 'n_iter_no_change': 10},
           'why': "0003's incumbent verbatim (run_study.py make_model 'hgb', run_carve.py's explicit "
                  'last-10% validation split); every other parameter at the sklearn 1.9.0 default'},
 'logistic': {'id': 'L1',
              'family': 'logistic',
              'params': {'max_iter': 400},
              'why': "0003's logistic verbatim (LogisticRegression(max_iter=400), lbfgs, C 1.0, raw "
                     'features): the frozen-set bar at 0.1392; its confirmatory reproduction within 0.005 is '
                     'a validity clause'},
 'majority': {'id': 'U1',
              'family': 'dummy',
              'params': {'strategy': 'most_frequent'},
              'why': 'no hyperparameter; confirmatory fit only, as in 0003 (0.0385 banked)'}}
RECIPES_SHA256 = "8d58ec2efa92330916444d07fd73b43d7b5edbb9ffb0dddd32304d3f448bc4d3"
RECIPE_SHA256 = {'model': '618e84840970bfe49e44fabdb0100895acd65ac4c042f0b402abe24c58386c9f',
 'logistic': '70dc5d929b8e4ea4616833d1997d40e038e1ed8e6a1cd071117f08f7b0e31b52',
 'majority': '0f9cdb98d303f47ace1c67a9814e51aa16642656480352724ea4f01a2aa8046a'}
PARTITION = {'n_eval_rows': 260000,
 'n_eval_chunks': 10000,
 'n_eval_non_gutenberg': 227006,
 'eval_idx_sha256': '7da1099e0cf9d4c3903dad62f52c91f67b751113fc4bfc0a62c53f05dccf1efa',
 'eval_y_sha256': '92b95cf02a21945cea2a7bd756a1e1096b07ec351b478c39e795a8a2267400d1',
 'n_pool_rows': 800000,
 'n_pool_chunks': 40000,
 'pool_idx_sha256': '17b0dc0bd9f7b9db6a5f0967cd96cbdccf524da56ed1aac7a80c4b57eb8ee7e5',
 'pool_y_sha256': 'd519612b4e46991f6ea1850fc92271e0de581e3cc378dd05fec59ff678dc72ea',
 'fold_rows': 'all',
 'families': ['gutenberg', 'base64', 'binary', 'code', 'csv', 'json', 'log', 'mixed'],
 'null_rows': 20000,
 'null_sorted_sha256': '0653cc12293ae078dd68b900c8778d93e701261ca93414be9eb7bb8e7ee686db'}
# Per fold: the held-out family's evaluation rows and the training rows (every pool row of the other
# seven families, in pool order); the runner also banks, and this reader requires to be 0, the counts
# of held-out-family rows in training, chunks shared with the evaluation set, and training rows that
# are evaluation rows.
FOLDS = {'gutenberg': {'n_eval_rows': 32994,
               'eval_idx_sha256': 'a6a1bef8036511315d2ac17e4a0f7078c6be848ca1c2c4b42d4ee6a084a56202',
               'n_train_rows': 700288,
               'train_idx_sha256': '036d65b93a92e3ebb950e4fe37c0a0354c18c8e258961ba21db37b6196f561e3',
               'train_sorted_sha256': 'e9c059873523e8543196c8bbb32fcaf0f628124a94c8b9766c75fdf5a2ab9648'},
 'base64': {'n_eval_rows': 32864,
            'eval_idx_sha256': 'bdebc4239afd64ccdfc6c27415326d95f29d1bcd8b46a4cf87b2c7fb63ad04eb',
            'n_train_rows': 700560,
            'train_idx_sha256': '989a2bb2df796f435a81dce996f0a9f5764044696c2eafaa85dcb58043854c32',
            'train_sorted_sha256': '32a0e6e6e99c0ff3140c0004c4b78faf3ea7958584191a835e47406d04b6d404'},
 'binary': {'n_eval_rows': 32474,
            'eval_idx_sha256': 'f91f609e7fb8739a17c0bb3a6fce9afdf1599b8282e14e366823461fb1dbd8c4',
            'n_train_rows': 699897,
            'train_idx_sha256': '986eb2ee3bf4193c97d3a0d730ab01d158292c864252633864122a218a51c653',
            'train_sorted_sha256': '9a5c958d8122ecda681a4292ed85d25fb8c6690c6f78a7f0d24a64e2a5ebf6a4'},
 'code': {'n_eval_rows': 31850,
          'eval_idx_sha256': '578248b2f2350e7aa5d3f7b2a832ecdb14fbd97d93e4690b7b4ea1e73a504bec',
          'n_train_rows': 699654,
          'train_idx_sha256': '14a38f73e27f9a4906b91e6803cae5cbe89fe0da1fa1e18b241038ff2653c222',
          'train_sorted_sha256': '39f72aa942c473a4ac8867c11d056a0527b5e6f0f4602c2e643157a2eff73775'},
 'csv': {'n_eval_rows': 31616,
         'eval_idx_sha256': 'b4ccfb51f5b8b54b2ef856b54af6e79cc7ca6ed62bc0d8cc8a7bfcac09dc5555',
         'n_train_rows': 699440,
         'train_idx_sha256': '8ae358528d974d213f64ee1d8d7800af18babba31b96dec37d6feb561afdf612',
         'train_sorted_sha256': '8f6fee17a72ee29f6bb8c2215e7b4bad24b367c2444e6eaa84e5ea7002017233'},
 'json': {'n_eval_rows': 32760,
          'eval_idx_sha256': '8eacb2d465c04006d1dbfd1452653d2cb4eab3a9ca633b1301b0b0064a17aaa4',
          'n_train_rows': 700071,
          'train_idx_sha256': '6f4c8110a832e4c3a1b184bbb212ae7d417e74784de11628369d7aa8e8726e25',
          'train_sorted_sha256': 'f9d7de73a4ffd623c962bdd8a82f8e8ab4959ab49b0989e3ca3907d22dfedb5d'},
 'log': {'n_eval_rows': 33254,
         'eval_idx_sha256': '1dab3cc04aa0ae442fc9cab1dd0f0cafd5b1b2e0cf3de25341ab39d8752e1d8b',
         'n_train_rows': 700473,
         'train_idx_sha256': '03ac48cec4a2761b22d023db503e17403e69251891387bd1836ae57e09635695',
         'train_sorted_sha256': '72a9d924f37f03ee6727e434ff839f04d101d697f413503d01c0106e39ae3fcb'},
 'mixed': {'n_eval_rows': 32188,
           'eval_idx_sha256': '3749067dd47d4a788ada22122dcf43c159d462ba5ade7904398735bdf94a80f1',
           'n_train_rows': 699617,
           'train_idx_sha256': '21870ebf6835b9e404baf3e729bf8cf5236da421479014ed7ae295df82ec1425',
           'train_sorted_sha256': '7705b06a505570c34bb5ade21e6be99c704fc8b012d854891bb8df5a81b7c5f7'}}
# 0003's in-distribution per-family accuracy at the 800000-row rung on these evaluation rows
# (artifacts/pivot/audit_rederivations.json): the retention reference, informational only.
REFERENCE_0003 = {'base64': 0.1221,
 'binary': 0.1049,
 'code': 0.2944,
 'csv': 0.3888,
 'gutenberg': 0.1596,
 'json': 0.3581,
 'log': 0.3756,
 'mixed': 0.1143}
INCUMBENT_TOP1, LOGISTIC_L1_TOP1, REPRODUCTION_TOLERANCE = 0.2395, 0.1392, 0.005
BAR, NULL_TOLERANCE, CHANCE = 0.05, 0.02, 0.038462
MIXTURE_MUST_REACH = 0.088462   # chance + BAR, the value a 4-decimal mixture must reach (0.0885 passes, 0.0884 fails)
ENV = {"threads": 3, "nice": 10, "sklearn": "1.9.0", "numpy": "2.4.6"}
SEED = 20260825
ROLES = ["majority", "logistic", "model"]


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_obj(obj) -> str:
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def main() -> int:
    if not os.path.exists(ARTIFACT):
        if os.path.exists(NOT_RUN):
            try:
                nr = json.load(open(NOT_RUN, encoding="utf-8"))
                print(f"READER 0015: NOT RUN — {nr.get('reason')!r} (stage {nr.get('stage')}, filed "
                      f"{nr.get('utc')}, {nr.get('n_checkpoints')} checkpoints). A NOT RUN is not a verdict.",
                      file=sys.stderr)
            except Exception:  # noqa: BLE001
                print("READER 0015: NOT RUN file present but unreadable.", file=sys.stderr)
            return 2
        print(f"READER 0015: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0015: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 2

    g = d.get
    void: list[str] = []

    def num(v):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None
        return v if math.isfinite(v) else None

    def expect_eq(where, got, want, label):
        if got != want:
            where.append(f"{label}={got!r}, preregistered {want!r}")

    # ---- scope
    if g("preregistration") != PREREG:
        void.append(f"scope: preregistration={g('preregistration')!r}, this reader is frozen for {PREREG}")
    if g("smoke") is not False:
        void.append(f"scope: smoke={g('smoke')!r}; a smoke run is not the preregistered run")
    if g("stage") != "run":
        void.append(f"scope: stage={g('stage')!r}")
    corpus = g("corpus") or {}
    for k, v in CORPUS.items():
        expect_eq(void, corpus.get(k), v, f"scope: corpus.{k}")
    if g("n_classes") != 26 or num(g("chance_accuracy")) != CHANCE:
        void.append(f"scope: n_classes={g('n_classes')!r}, chance_accuracy={g('chance_accuracy')!r}")
    proto = g("protocol") or {}
    for k in sorted(set(PROTOCOL) | set(proto)):
        if proto.get(k) != PROTOCOL.get(k):
            void.append(f"scope: protocol.{k}={proto.get(k)!r}, preregistered {PROTOCOL.get(k)!r}")
    if g("protocol_sha256") != PROTOCOL_SHA256 or sha_obj(proto) != PROTOCOL_SHA256:
        void.append("scope: the banked protocol does not hash to the sealed PROTOCOL_SHA256")
    recipes = g("recipes") or {}
    if g("recipes_sha256") != RECIPES_SHA256 or sha_obj(recipes) != RECIPES_SHA256 or recipes != RECIPES:
        void.append("scope: the banked recipes are not 0003's sealed recipes")

    # ---- sealed sets
    part = g("partition") or {}
    for k, v in PARTITION.items():
        expect_eq(void, part.get(k), v, f"sealed set: partition.{k}")
    pfolds = part.get("folds") or {}
    for f in FAMILIES:
        pf = pfolds.get(f) or {}
        for k, v in FOLDS[f].items():
            expect_eq(void, pf.get(k), v, f"sealed set: fold {f}.{k}")
        for k in ("train_rows_of_heldout_family", "train_chunks_shared_with_eval", "train_rows_in_eval"):
            if pf.get(k) != 0:
                void.append(f"leakage: fold {f}.{k}={pf.get(k)!r}, must be 0")
    if g("complete") is not True:
        void.append(f"complete: complete={g('complete')!r}; missing {g('missing_roles')!r}")
    if g("null_rows") != PROTOCOL["null_rows"]:
        void.append(f"null control: null_rows={g('null_rows')!r}")

    # ---- scores file, ledger
    scores, chunk_ids = {}, None
    if os.path.exists(SCORES):
        try:
            sd = json.load(open(SCORES, encoding="utf-8")) or {}
            scores = sd.get("per_example") or {}
            chunk_ids = sd.get("eval_chunk_ids")
            if sd.get("eval_idx_sha256") != PARTITION["eval_idx_sha256"] or sd.get("smoke") is not False \
                    or sd.get("preregistration") != PREREG:
                void.append("scores: the scores file is not this run's, or is a smoke run's")
        except Exception:  # noqa: BLE001
            void.append("scores: the scores file is not JSON")
    else:
        void.append("scores: the scores file is absent")
    if not isinstance(chunk_ids, list) or len(chunk_ids) != PARTITION["n_eval_rows"]:
        void.append("scores: eval_chunk_ids missing or not 260000 long"); chunk_ids = None
    ledger = g("ledger") or []

    def check_record(name, rec, role, rows_sha, sorted_sha, n_rows, key):
        if not isinstance(rec, dict) or rec.get("status") != "fit":
            void.append(f"fit: {name} status {(rec or {}).get('status')!r}; must be 'fit'"); return
        if num(rec.get("top1")) is None or num(rec.get("top1_non_gutenberg")) is None or \
                not isinstance(rec.get("per_family"), dict) or len(rec["per_family"]) != 8 or \
                any(num(v) is None for v in rec["per_family"].values()):
            void.append(f"fit: {name} scores are not all finite")
        if rec.get("id") != RECIPES[role]["id"] or rec.get("params_sha256") != RECIPE_SHA256[role]:
            void.append(f"fit: {name} is not 0003's {role} recipe (id {rec.get('id')!r}, params hash off-recipe)")
        if rec.get("seed") != SEED or rec.get("n_fit_rows") != n_rows or rec.get("fit_rows_sha256") != rows_sha \
                or (sorted_sha is not None and rec.get("fit_rows_sorted_sha256") != sorted_sha):
            void.append(f"fit: {name} was not fitted on the sealed rows with the preregistered seed")
        if any(not rf.get("probe_ok") for rf in (rec.get("block_refills") or [])):
            void.append(f"fit: {name} banked a failed block probe check")
        renv = rec.get("environment") or {}
        for k, v in ENV.items():
            if renv.get(k) != v:
                void.append(f"environment: {name} {k}={renv.get(k)!r}, banked {v!r}")
        done = [e for e in ledger if isinstance(e, dict) and e.get("name") == name and e.get("event") == "completed"]
        if len(done) != 1:
            void.append(f"fit: {name} has {len(done)} ledger completions, must be exactly 1")
        if key is not None:
            pe = scores.get(key)
            if not isinstance(pe, list) or len(pe) != PARTITION["n_eval_rows"]:
                void.append(f"fit: {name} per-example vector missing or not {PARTITION['n_eval_rows']} long")

    # ---- reproductions and the null control
    rep = g("reproduction") or {}
    inc, l1 = rep.get("model") or {}, rep.get("logistic") or {}
    check_record("repro_model", inc, "model", PARTITION["pool_idx_sha256"], None, PARTITION["n_pool_rows"], "repro_model")
    check_record("repro_logistic", l1, "logistic", PARTITION["pool_idx_sha256"], None, PARTITION["n_pool_rows"], "repro_logistic")
    if num(g("incumbent_refit_top1")) != num(inc.get("top1")) or num(g("logistic_l1_refit_top1")) != num(l1.get("top1")):
        void.append("reproduction: the banked refit accuracies are not the records'")
    if num(inc.get("top1")) is None or abs(num(inc.get("top1")) - INCUMBENT_TOP1) > REPRODUCTION_TOLERANCE:
        void.append(f"reproduction: the incumbent refit scores {inc.get('top1')!r} against 0003's banked "
                    f"{INCUMBENT_TOP1}; the pool or the evaluation set is not 0003's")
    if num(l1.get("top1")) is None or abs(num(l1.get("top1")) - LOGISTIC_L1_TOP1) > REPRODUCTION_TOLERANCE:
        void.append(f"reproduction: the 0003 logistic refit scores {l1.get('top1')!r} against the banked "
                    f"{LOGISTIC_L1_TOP1}")
    nc = g("null_control") or {}
    if nc.get("status") != "fit" or nc.get("id") != RECIPES["model"]["id"] or nc.get("params_sha256") != RECIPE_SHA256["model"] \
            or nc.get("n_fit_rows") != PROTOCOL["null_rows"] or nc.get("fit_rows_sorted_sha256") != PARTITION["null_sorted_sha256"]:
        void.append("null control: not 0003's model recipe on the sealed 20000-row null block")
    if num(g("shuffled_label_accuracy")) is None or num(g("shuffled_label_accuracy")) != num(nc.get("top1")):
        void.append("null control: shuffled_label_accuracy missing, not finite, or not the record's")
    elif num(g("shuffled_label_accuracy")) > CHANCE + NULL_TOLERANCE:
        void.append(f"null control: shuffled labels reached {g('shuffled_label_accuracy')}, above chance {CHANCE} + "
                    f"{NULL_TOLERANCE} — the pipeline leaks")
    done_null = [e for e in ledger if isinstance(e, dict) and e.get("name") == "null" and e.get("event") == "completed"]
    if len(done_null) != 1:
        void.append(f"null control: {len(done_null)} ledger completions, must be exactly 1")

    # ---- the folds
    folds = g("folds") or {}
    for f in FAMILIES:
        fd = folds.get(f) or {}
        for r in ROLES:
            check_record(f"fold_{f}_{r}", fd.get(r), r, FOLDS[f]["train_idx_sha256"], FOLDS[f]["train_sorted_sha256"],
                         FOLDS[f]["n_train_rows"], f"fold_{f}_{r}")
    env = g("environment") or {}
    for k, v in ENV.items():
        if env.get(k) != v:
            void.append(f"environment: {k}={env.get(k)!r}, banked {v!r}")

    # ---- the mixture, re-derived from the per-example vectors and the banked chunk ids
    lofo = g("lofo") or {}
    if chunk_ids is not None and not any(m.startswith("fit:") or m.startswith("scores:") for m in void):
        fam_e = [FAMILIES[int(c) % 8] for c in chunk_ids]
        n = PARTITION["n_eval_rows"]
        for r in ROLES:
            vecs = {f: scores.get(f"fold_{f}_{r}") for f in FAMILIES}
            mix = [int(vecs[fam_e[i]][i]) for i in range(n)]
            by_fam = {f: [] for f in FAMILIES}
            for i in range(n):
                by_fam[fam_e[i]].append(mix[i])
            mean = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
            rec_mix = {"mixture_top1": mean(mix),
                       "mixture_top1_non_gutenberg": mean([mix[i] for i in range(n) if fam_e[i] != "gutenberg"]),
                       "structured_four_top1": mean([mix[i] for i in range(n) if fam_e[i] in STRUCTURED]),
                       "per_family": {f: mean(by_fam[f]) for f in FAMILIES}}
            banked = lofo.get(r) or {}
            for k, v in rec_mix.items():
                if banked.get(k) != v:
                    void.append(f"mixture: lofo.{r}.{k}={banked.get(k)!r} is not the reader's recomputation {v!r}")
            for f in FAMILIES:
                # the fold's own banked per-family accuracy for its held-out family must be the mixture's
                fr = ((folds.get(f) or {}).get(r) or {}).get("per_family") or {}
                if num(fr.get(f)) != rec_mix["per_family"][f]:
                    void.append(f"mixture: fold {f} {r} banked {fr.get(f)!r} on its held-out family, recomputed "
                                f"{rec_mix['per_family'][f]!r}")
    model_mix = num(g("lofo_mixture_top1"))
    if model_mix is None or model_mix != ((lofo.get("model") or {}).get("mixture_top1")):
        void.append("mixture: lofo_mixture_top1 missing, not finite, or not the model role's mixture")
    logi_mix = num((lofo.get("logistic") or {}).get("mixture_top1"))
    if model_mix is not None and logi_mix is not None and num(g("lofo_margin_model_over_logistic")) != round(model_mix - logi_mix, 6):
        void.append("mixture: lofo_margin_model_over_logistic is not model minus logistic")

    # ---- the one clause
    fails: list[str] = []
    if not void:
        gap = round(model_mix - CHANCE, 6)
        if gap < BAR - 1e-9:
            fails.append(f"transfer: LOFO mixture {model_mix} - chance {CHANCE} = {gap} is below {BAR}")

    if void:
        verdict, meaning = "VOID", ("A validity or control clause fails, or the artifact is incomplete. This run says "
                                    "nothing about transfer in either direction.")
    elif fails:
        verdict, meaning = "TRANSFER_FAILS", (
            "The model's leave-one-family-out mixture does not clear chance by 0.05: on content its training set "
            "never contained, 0003's recipe does not identify the encoder at the preregistered level. The curve and "
            "the searched margin stand as measured and are statements about these eight content families.")
    else:
        verdict, meaning = "TRANSFERS", (
            "The model's leave-one-family-out mixture clears chance by 0.05: the encoder signature 0003's recipe "
            "learns on seven content families identifies the encoder on the eighth. A statement about transfer "
            "among the corpus builder's eight families at 4096 bytes; nothing here establishes a buyer.")

    retention = None
    if verdict != "VOID":
        pf = (lofo.get("model") or {}).get("per_family") or {}
        retention = {f: (round(pf[f] / REFERENCE_0003[f], 4) if num(pf.get(f)) is not None and REFERENCE_0003[f] else None)
                     for f in FAMILIES}
    result = {
        "schema": "raise-v1/lofo_4096_verdict/1",
        "preregistration": PREREG, "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "verdict": verdict, "meaning": meaning,
        "validity_failed_clauses": void, "transfer_failed_clauses": fails,
        "bar_applied": {"chance": CHANCE, "margin_over_chance": BAR, "mixture_must_reach": MIXTURE_MUST_REACH},
        "lofo_mixture_top1": model_mix,
        "lofo_mixture_minus_chance": round(model_mix - CHANCE, 6) if model_mix is not None else None,
        "lofo_mixture_top1_logistic": logi_mix,
        "lofo_mixture_top1_majority": num((lofo.get("majority") or {}).get("mixture_top1")),
        "lofo_margin_model_over_logistic": num(g("lofo_margin_model_over_logistic")),
        "retention_per_family": retention,
        "reference_0003_top_rung_per_family": REFERENCE_0003,
        "incumbent_reproduction_drift": round(num(inc.get("top1")) - INCUMBENT_TOP1, 6) if num(inc.get("top1")) is not None else None,
        "logistic_l1_reproduction_drift": round(num(l1.get("top1")) - LOGISTIC_L1_TOP1, 6) if num(l1.get("top1")) is not None else None,
        "informational_only": "the logistic and majority mixtures, the margin, the per-family readings, the structured-four "
                              "reading, retention, the reproduction drifts and the artifact's cluster intervals are "
                              "informational: not a verdict, not quotable as a pass. The verdict is the `verdict` field.",
        "establishes_a_buyer": False, "revises_0003_0014": False,
        "read": {k: g(k) for k in (
            "preregistration", "smoke", "stage", "complete", "missing_roles", "lofo_mixture_top1",
            "lofo_margin_model_over_logistic", "incumbent_refit_top1", "logistic_l1_refit_top1",
            "shuffled_label_accuracy", "chance_accuracy", "null_rows", "n_classes")},
        "lofo": lofo,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("READER 0015 — leave-one-family-out transfer at 4096")
    for k, v in result["read"].items():
        print(f"  {k:<36} {v}")
    for r in ROLES:
        print(f"  lofo.{r:<31} {json.dumps(lofo.get(r))[:200]}")
    if void:
        print(f"\n  VALIDITY FAILED CLAUSES ({len(void)}):")
        for f in void:
            print(f"    · {f}")
    if fails:
        print(f"\n  TRANSFER FAILED CLAUSES ({len(fails)}):")
        for f in fails:
            print(f"    · {f}")
    print(f"\n  VERDICT: {verdict}")
    print(f"  {meaning}")
    print("  This does not establish a buyer, and was never capable of doing so.")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
