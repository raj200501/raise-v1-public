#!/usr/bin/env python3
"""Frozen reader for preregistration 0017 — under leave-one-family-out transfer at 4096, does 0014's
searched, standardised logistic L3 lead the incumbent by the preregistered margin (0.02, i.e. 5200 of
260000 rows)?

Written and committed BEFORE any fold was fitted under this preregistration.

WHY THIS EXISTS. 0015 found that under transfer the raw logistic L1 (0.0928) beat the incumbent HGB
M1 (0.0859) while hitting its 400-iteration cap in every fold, which left open whether a linear rule
generalises at least as well as the boosted model or an unconverged fit merely regularised. Every
in-distribution margin clause in this record is the boosted model over a baseline set by at least 0.05
(0003 over the frozen set whose best member is the raw logistic and over the expanded set whose best
member is a depth-16 tree; 0014's searched model over the searched logistic L3). This reader takes the runner's artifact (tools/pivot/run_lofo_l3.py) and checks, clause by
clause: the sealed corpus, split and 0015's eight folds (every hash a literal below, identical to
0015's); that no fold's training rows contain a row of the held-out family or a chunk of the
evaluation set; that every fit is 0014's L3 (params hash below), fitted on the sealed rows with the
sealed seed and scored exactly once; that the reproduction control lands on 0014's same-convention
0.2317; that the null control sits at chance; and that the LOFO mixture equals what this reader
recomputes from the per-example vectors. Then one clause: L3's stitched correct count against 0015's
banked incumbent count plus the margin. L3_LEADS_INCUMBENT_UNDER_TRANSFER or L3_LEAD_BELOW_BAR, published at the same
size; VOID on any validity failure. The in-distribution gap between this pair is small (0014 banked the incumbent at
0.2395 and L3 at 0.2317); the clause is the record's margin discipline applied to the linear rule under transfer,
not the reversal of any one in-distribution clause.

Every constant below is 0015's sealed partition (computed 2026-09-08 from data/pivot/full_c4096.npz
with tools/pivot/run_carve.py grouped_split(seed 20260825, eval_frac 0.2, cap 800000) and the family
rule FAMILIES[chunk_id modulo 8]), restated on 2026-09-09 before any 0017 fit. Digest convention:
sha256 of np.ascontiguousarray(a).tobytes(); index arrays int64 in grouped_split / np.nonzero order;
y as stored (int16); sorted sets np.sort(...).astype(np.int64).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "lofo_l3_4096.json")
SCORES = os.path.join(REPO, "artifacts", "pivot", "lofo_l3_4096_scores.json")
NOT_RUN = os.path.join(REPO, "artifacts", "pivot", "lofo_l3_4096_not_run.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "lofo_l3_4096_verdict.json")
PREREG = "0017-lofo-l3-4096"

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
 'roles': ['logistic_l3'],
 'order': ['reproduction_l3', 'null', 'folds'],
 'null_rows': 20000,
 'structured_families': ['code', 'csv', 'json', 'log'],
 'caps': {'memory_kill_gb': 13.0},
 'launch': {'min_disk_free_gb': 0.25, 'min_mem_available_gb': 14.5},
 'environment': {'sklearn': '1.9.0', 'numpy': '2.4.6', 'python': '3.11.15'},
 'reference_0015': {'source': 'artifacts/pivot/lofo_4096.json',
                    'model_mixture_top1': 0.0859,
                    'logistic_mixture_top1': 0.0928,
                    'majority_mixture_top1': 0.0385,
                    'model_per_family': {'base64': 0.0653,
                                         'binary': 0.0618,
                                         'code': 0.1135,
                                         'csv': 0.0968,
                                         'gutenberg': 0.0552,
                                         'json': 0.1134,
                                         'log': 0.1083,
                                         'mixed': 0.0738},
                    'logistic_per_family': {'base64': 0.0596,
                                            'binary': 0.0773,
                                            'code': 0.1023,
                                            'csv': 0.103,
                                            'gutenberg': 0.0635,
                                            'json': 0.1504,
                                            'log': 0.1104,
                                            'mixed': 0.0762},
                    'model_structured_four_top1': 0.1081,
                    'logistic_structured_four_top1': 0.1167,
                    'model_correct': 22343,
                    'logistic_correct': 24131,
                    'n_eval_rows': 260000,
                    'counts_source': 'sum of the stitched vectors lofo_mixture_model and '
                                     'lofo_mixture_logistic in artifacts/pivot/lofo_4096_scores.json (22343 '
                                     '/ 260000 = 0.085935, banked 0.0859; 24131 / 260000 = 0.092812, banked '
                                     '0.0928)'},
 'bar': {'l3_correct_minus_0015_incumbent_correct_over_n_eval': 0.02},
 'reproduction_tolerance': 0.005,
 'null_tolerance': 0.02}
PROTOCOL_SHA256 = "6a0f5fc20f706bf922f0cd826aca614353e8ed253f99d6d28e13092ed79a1d8b"
# 0014's searched logistic L3, byte for byte 0014's sealed roster entry; its canonical-JSON hash is what
# every record's params_sha256 must equal.
RECIPES = {'logistic_l3': {'family': 'logistic',
                 'id': 'L3',
                 'params': {'C': 1.0, 'max_iter': 1000},
                 'scaled': True,
                 'why': 'standardised inputs with C 1.0: the single most standard fix for an lbfgs logistic '
                        'on 1108 unscaled hand-engineered columns'}}
RECIPES_SHA256 = "67d78d3fece51a0877f53a4a9611a82fd5b9f8907a83da060907652ddc9a1b8b"
RECIPE_SHA256 = {'logistic_l3': '6c963004952ef934d6609c0a9d1d384a87728591b1694515f43328ab05344dfe'}
PARTITION = {'n_eval_rows': 260000,
 'n_eval_chunks': 10000,
 'n_eval_non_gutenberg': 227006,
 'eval_idx_sha256': '7da1099e0cf9d4c3903dad62f52c91f67b751113fc4bfc0a62c53f05dccf1efa',
 'eval_y_sha256': '92b95cf02a21945cea2a7bd756a1e1096b07ec351b478c39e795a8a2267400d1',
 'n_pool_rows': 800000,
 'n_pool_chunks': 40000,
 'pool_idx_sha256': '17b0dc0bd9f7b9db6a5f0967cd96cbdccf524da56ed1aac7a80c4b57eb8ee7e5',
 'pool_y_sha256': 'd519612b4e46991f6ea1850fc92271e0de581e3cc378dd05fec59ff678dc72ea',
 'pool_sorted_sha256': '923cd266c3bf2a45683b2c479d36b046b311cc8f2e53426c962b6dd5ae836094',
 'fold_rows': 'all',
 'families': ['gutenberg', 'base64', 'binary', 'code', 'csv', 'json', 'log', 'mixed'],
 'null_rows': 20000,
 'null_sorted_sha256': '0653cc12293ae078dd68b900c8778d93e701261ca93414be9eb7bb8e7ee686db'}
# Per fold, 0015's literals: the held-out family's evaluation rows and the training rows (every pool row
# of the other seven families, in pool order); the runner also banks, and this reader requires to be 0,
# the counts of held-out-family rows in training, chunks shared with the evaluation set, and training
# rows that are evaluation rows.
FOLDS = {'gutenberg': {'n_eval_rows': 32994,
               'eval_idx_sha256': 'a6a1bef8036511315d2ac17e4a0f7078c6be848ca1c2c4b42d4ee6a084a56202',
               'n_eval_chunks': 1269,
               'n_train_rows': 700288,
               'train_idx_sha256': '036d65b93a92e3ebb950e4fe37c0a0354c18c8e258961ba21db37b6196f561e3',
               'train_sorted_sha256': 'e9c059873523e8543196c8bbb32fcaf0f628124a94c8b9766c75fdf5a2ab9648',
               'n_train_chunks': 35019},
 'base64': {'n_eval_rows': 32864,
            'eval_idx_sha256': 'bdebc4239afd64ccdfc6c27415326d95f29d1bcd8b46a4cf87b2c7fb63ad04eb',
            'n_eval_chunks': 1264,
            'n_train_rows': 700560,
            'train_idx_sha256': '989a2bb2df796f435a81dce996f0a9f5764044696c2eafaa85dcb58043854c32',
            'train_sorted_sha256': '32a0e6e6e99c0ff3140c0004c4b78faf3ea7958584191a835e47406d04b6d404',
            'n_train_chunks': 35014},
 'binary': {'n_eval_rows': 32474,
            'eval_idx_sha256': 'f91f609e7fb8739a17c0bb3a6fce9afdf1599b8282e14e366823461fb1dbd8c4',
            'n_eval_chunks': 1249,
            'n_train_rows': 699897,
            'train_idx_sha256': '986eb2ee3bf4193c97d3a0d730ab01d158292c864252633864122a218a51c653',
            'train_sorted_sha256': '9a5c958d8122ecda681a4292ed85d25fb8c6690c6f78a7f0d24a64e2a5ebf6a4',
            'n_train_chunks': 34999},
 'code': {'n_eval_rows': 31850,
          'eval_idx_sha256': '578248b2f2350e7aa5d3f7b2a832ecdb14fbd97d93e4690b7b4ea1e73a504bec',
          'n_eval_chunks': 1225,
          'n_train_rows': 699654,
          'train_idx_sha256': '14a38f73e27f9a4906b91e6803cae5cbe89fe0da1fa1e18b241038ff2653c222',
          'train_sorted_sha256': '39f72aa942c473a4ac8867c11d056a0527b5e6f0f4602c2e643157a2eff73775',
          'n_train_chunks': 34975},
 'csv': {'n_eval_rows': 31616,
         'eval_idx_sha256': 'b4ccfb51f5b8b54b2ef856b54af6e79cc7ca6ed62bc0d8cc8a7bfcac09dc5555',
         'n_eval_chunks': 1216,
         'n_train_rows': 699440,
         'train_idx_sha256': '8ae358528d974d213f64ee1d8d7800af18babba31b96dec37d6feb561afdf612',
         'train_sorted_sha256': '8f6fee17a72ee29f6bb8c2215e7b4bad24b367c2444e6eaa84e5ea7002017233',
         'n_train_chunks': 34966},
 'json': {'n_eval_rows': 32760,
          'eval_idx_sha256': '8eacb2d465c04006d1dbfd1452653d2cb4eab3a9ca633b1301b0b0064a17aaa4',
          'n_eval_chunks': 1260,
          'n_train_rows': 700071,
          'train_idx_sha256': '6f4c8110a832e4c3a1b184bbb212ae7d417e74784de11628369d7aa8e8726e25',
          'train_sorted_sha256': 'f9d7de73a4ffd623c962bdd8a82f8e8ab4959ab49b0989e3ca3907d22dfedb5d',
          'n_train_chunks': 35010},
 'log': {'n_eval_rows': 33254,
         'eval_idx_sha256': '1dab3cc04aa0ae442fc9cab1dd0f0cafd5b1b2e0cf3de25341ab39d8752e1d8b',
         'n_eval_chunks': 1279,
         'n_train_rows': 700473,
         'train_idx_sha256': '03ac48cec4a2761b22d023db503e17403e69251891387bd1836ae57e09635695',
         'train_sorted_sha256': '72a9d924f37f03ee6727e434ff839f04d101d697f413503d01c0106e39ae3fcb',
         'n_train_chunks': 35029},
 'mixed': {'n_eval_rows': 32188,
           'eval_idx_sha256': '3749067dd47d4a788ada22122dcf43c159d462ba5ade7904398735bdf94a80f1',
           'n_eval_chunks': 1238,
           'n_train_rows': 699617,
           'train_idx_sha256': '21870ebf6835b9e404baf3e729bf8cf5236da421479014ed7ae295df82ec1425',
           'train_sorted_sha256': '7705b06a505570c34bb5ade21e6be99c704fc8b012d854891bb8df5a81b7c5f7',
           'n_train_chunks': 34988}}
# 0015's banked leave-one-family-out readings (artifacts/pivot/lofo_4096.json): the incumbent's mixture
# is the other side of the margin clause; the rest are informational references.
REFERENCE_0015 = {'source': 'artifacts/pivot/lofo_4096.json',
 'model_mixture_top1': 0.0859,
 'logistic_mixture_top1': 0.0928,
 'majority_mixture_top1': 0.0385,
 'model_per_family': {'base64': 0.0653,
                      'binary': 0.0618,
                      'code': 0.1135,
                      'csv': 0.0968,
                      'gutenberg': 0.0552,
                      'json': 0.1134,
                      'log': 0.1083,
                      'mixed': 0.0738},
 'logistic_per_family': {'base64': 0.0596,
                         'binary': 0.0773,
                         'code': 0.1023,
                         'csv': 0.103,
                         'gutenberg': 0.0635,
                         'json': 0.1504,
                         'log': 0.1104,
                         'mixed': 0.0762},
 'model_structured_four_top1': 0.1081,
 'logistic_structured_four_top1': 0.1167,
 'model_correct': 22343,
 'logistic_correct': 24131,
 'n_eval_rows': 260000,
 'counts_source': 'sum of the stitched vectors lofo_mixture_model and lofo_mixture_logistic in '
                  'artifacts/pivot/lofo_4096_scores.json (22343 / 260000 = 0.085935, banked 0.0859; 24131 / '
                  '260000 = 0.092812, banked 0.0928)'}
# The reproduction anchor: 0014's confirmatory refit of this exact recipe on this exact 800000-row pool
# block with this machinery (artifacts/pivot/recipe_search_4096.json final.logistic.top1, 728
# iterations), the same-convention value; compared at the 4-decimal precision the accuracies are banked
# at (0.2367 passes, 0.2368 fails).
L3_TOP1_0014, REPRODUCTION_TOLERANCE = 0.2317, 0.005
MARGIN_BAR, NULL_TOLERANCE, CHANCE = 0.02, 0.02, 0.038462
# The clause is read on EXACT correct counts, not on 4-decimal mixtures: L3's stitched correct count (recomputed here
# from the per-example vectors) minus 0015's banked incumbent correct count (REFERENCE_0015["model_correct"], the sum
# of 0015's stitched vector) must be at least MARGIN_BAR x 260000 = MARGIN_CORRECT rows.
MARGIN_CORRECT = 5200
MIXTURE_MUST_REACH = 0.105935   # the same bar restated as a mixture, for reading: model_correct + MARGIN_CORRECT over 260000, 6 decimals
ENV = {"threads": 3, "nice": 10, "sklearn": "1.9.0", "numpy": "2.4.6"}
SEED = 20260825
ROLES = ["logistic_l3"]


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_obj(obj) -> str:
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def main() -> int:
    if not os.path.exists(ARTIFACT):
        if os.path.exists(NOT_RUN):
            try:
                nr = json.load(open(NOT_RUN, encoding="utf-8"))
                print(f"READER 0017: NOT RUN — {nr.get('reason')!r} (stage {nr.get('stage')}, filed "
                      f"{nr.get('utc')}, {nr.get('n_checkpoints')} checkpoints). A NOT RUN is not a verdict.",
                      file=sys.stderr)
            except Exception:  # noqa: BLE001
                print("READER 0017: NOT RUN file present but unreadable.", file=sys.stderr)
            return 2
        print(f"READER 0017: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0017: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
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
        void.append("scope: the banked recipe is not 0014's sealed L3")
    if g("reference_0015") != REFERENCE_0015:
        void.append("scope: the banked 0015 references are not the sealed ones")

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

    def check_record(name, rec, role, rows_sha, sorted_sha, n_rows, key, stage):
        """rows_sha None: the unsorted index hash is not sealed for this record (the null block); the sorted one is."""
        if not isinstance(rec, dict) or rec.get("status") != "fit":
            void.append(f"fit: {name} status {(rec or {}).get('status')!r}; must be 'fit'"); return
        if num(rec.get("top1")) is None or num(rec.get("top1_non_gutenberg")) is None or \
                not isinstance(rec.get("per_family"), dict) or len(rec["per_family"]) != 8 or \
                any(num(v) is None for v in rec["per_family"].values()):
            void.append(f"fit: {name} scores are not all finite")
        if rec.get("id") != RECIPES[role]["id"] or rec.get("params_sha256") != RECIPE_SHA256[role] or rec.get("scaled") is not True:
            void.append(f"fit: {name} is not 0014's L3 (id {rec.get('id')!r}, params hash off-recipe, or not standardised)")
        if rec.get("seed") != SEED or rec.get("n_fit_rows") != n_rows \
                or (rows_sha is not None and rec.get("fit_rows_sha256") != rows_sha) \
                or (sorted_sha is not None and rec.get("fit_rows_sorted_sha256") != sorted_sha):
            void.append(f"fit: {name} was not fitted on the sealed rows with the preregistered seed")
        if rec.get("stage") != stage:
            void.append(f"fit: {name} stage {rec.get('stage')!r} is not {stage!r}")
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

    # ---- the reproduction and the null control
    rep = g("reproduction") or {}
    l3 = rep.get("logistic_l3") or {}
    check_record("repro_l3", l3, "logistic_l3", PARTITION["pool_idx_sha256"], PARTITION["pool_sorted_sha256"],
                 PARTITION["n_pool_rows"], "repro_l3", "reproduction")
    if num(g("logistic_l3_refit_top1")) != num(l3.get("top1")):
        void.append("reproduction: the banked refit accuracy is not the record's")
    if num(l3.get("top1")) is None or round(abs(num(l3.get("top1")) - L3_TOP1_0014), 6) > REPRODUCTION_TOLERANCE:
        void.append(f"reproduction: L3 on the full pool scores {l3.get('top1')!r} against 0014's same-convention "
                    f"{L3_TOP1_0014}; the pool, the evaluation set or the machinery is not 0014's")
    nc = g("null_control") or {}
    check_record("null", nc, "logistic_l3", None, PARTITION["null_sorted_sha256"], PROTOCOL["null_rows"], None, "null")
    if nc.get("head") != "null":
        void.append("null control: the null record is not the null-stage fit")
    if num(g("shuffled_label_accuracy")) is None or num(g("shuffled_label_accuracy")) != num(nc.get("top1")):
        void.append("null control: shuffled_label_accuracy missing, not finite, or not the record's")
    elif num(g("shuffled_label_accuracy")) > CHANCE + NULL_TOLERANCE:
        void.append(f"null control: shuffled labels reached {g('shuffled_label_accuracy')}, above chance {CHANCE} + "
                    f"{NULL_TOLERANCE} — the pipeline leaks")

    # ---- the folds
    folds = g("folds") or {}
    for f in FAMILIES:
        fd = folds.get(f) or {}
        for r in ROLES:
            check_record(f"fold_{f}_{r}", fd.get(r), r, FOLDS[f]["train_idx_sha256"], FOLDS[f]["train_sorted_sha256"],
                         FOLDS[f]["n_train_rows"], f"fold_{f}_{r}", f"lofo:{f}")
    env = g("environment") or {}
    for k, v in ENV.items():
        if env.get(k) != v:
            void.append(f"environment: {k}={env.get(k)!r}, banked {v!r}")

    # ---- the mixture, re-derived from the per-example vectors and the banked chunk ids
    lofo = g("lofo") or {}

    def _ints(v, n, values=None):
        return isinstance(v, list) and len(v) == n and all(
            isinstance(x, int) and not isinstance(x, bool) and (values is None or x in values) for x in v)

    if chunk_ids is not None and not _ints(chunk_ids, PARTITION["n_eval_rows"]):
        void.append("scores: eval_chunk_ids contains a non-integer entry"); chunk_ids = None
    for f in FAMILIES:
        for r in ROLES:
            v = scores.get(f"fold_{f}_{r}")
            if isinstance(v, list) and len(v) == PARTITION["n_eval_rows"] and not _ints(v, PARTITION["n_eval_rows"], (0, 1)):
                void.append(f"scores: fold_{f}_{r} per-example vector contains an entry that is not 0 or 1")
    l3_mix = None; l3_correct = None
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
            mv = scores.get(f"lofo_mixture_{r}")
            if not _ints(mv, n, (0, 1)) or mv != mix:
                void.append(f"mixture: the banked stitched vector lofo_mixture_{r} is not the stitched one")
            for f in FAMILIES:
                fr = ((folds.get(f) or {}).get(r) or {}).get("per_family") or {}
                if num(fr.get(f)) != rec_mix["per_family"][f]:
                    void.append(f"mixture: fold {f} {r} banked {fr.get(f)!r} on its held-out family, recomputed "
                                f"{rec_mix['per_family'][f]!r}")
            if r == "logistic_l3":
                l3_mix = rec_mix["mixture_top1"]; l3_correct = sum(mix)
    banked_mix = num(g("lofo_mixture_top1"))
    if banked_mix is None or banked_mix != ((lofo.get("logistic_l3") or {}).get("mixture_top1")):
        void.append("mixture: lofo_mixture_top1 missing, not finite, or not L3's mixture")
    ref_m = REFERENCE_0015["model_mixture_top1"]; ref_l = REFERENCE_0015["logistic_mixture_top1"]
    ref_mc = REFERENCE_0015["model_correct"]; n_rows = REFERENCE_0015["n_eval_rows"]
    if banked_mix is not None:
        if num(g("lofo_margin_l3_over_0015_model")) != round(banked_mix - ref_m, 6):
            void.append("margin: lofo_margin_l3_over_0015_model is not the mixture minus 0015's incumbent mixture")
        if num(g("lofo_margin_l3_over_0015_logistic")) != round(banked_mix - ref_l, 6):
            void.append("margin: lofo_margin_l3_over_0015_logistic is not the mixture minus 0015's logistic mixture")
    if l3_correct is not None:
        if g("lofo_correct_l3") != l3_correct:
            void.append(f"margin: lofo_correct_l3={g('lofo_correct_l3')!r} is not the reader's stitched correct count {l3_correct}")
        if num(g("lofo_margin_l3_over_0015_model_exact")) != round((l3_correct - ref_mc) / n_rows, 6):
            void.append("margin: lofo_margin_l3_over_0015_model_exact is not (correct counts difference) / 260000")
    nib = g("n_iter_by_fold") or {}
    if any(not isinstance(nib.get(f), int) or isinstance(nib.get(f), bool) for f in FAMILIES):
        void.append("fit: n_iter_by_fold is missing an integer iteration count for some fold")
    if not void and (l3_mix is None or l3_correct is None):
        void.append("mixture: the reader could not recompute L3's mixture")

    # ---- the one clause, on the reader's own stitched correct count against 0015's banked count
    fails: list[str] = []
    margin_exact = None; below_cap = None
    if not void:
        margin_exact = round((l3_correct - ref_mc) / n_rows, 6)
        below_cap = sum(1 for f in FAMILIES if nib[f] < RECIPES["logistic_l3"]["params"]["max_iter"])
        if l3_correct - ref_mc < MARGIN_CORRECT:
            fails.append(f"lead: L3's stitched correct count {l3_correct} minus 0015's incumbent count {ref_mc} = "
                         f"{l3_correct - ref_mc} rows ({margin_exact}) is below {MARGIN_CORRECT} rows ({MARGIN_BAR})")

    if void:
        verdict, meaning = "VOID", ("A validity or control clause fails, or the artifact is incomplete. This run says "
                                    "nothing about the searched logistic under transfer in either direction.")
        # noqa: the banked mixture is not restated under VOID
    elif fails:
        verdict, meaning = "L3_LEAD_BELOW_BAR", (
            f"Under leave-one-family-out transfer at 4096 on 0015's folds, 0014's searched, standardised logistic does not "
            f"lead 0003's fixed incumbent by {MARGIN_BAR}: the standardised linear rule's lead over the incumbent on unseen "
            f"families, if any (the exact margin {margin_exact} may be negative), is below the preregistered bar; iteration "
            f"counts are banked ({below_cap} of 8 folds below the 1000 cap). L3 is a searched recipe and the incumbent is not; "
            "0014's searched model is not measured here. A statement about the corpus builder's eight families (seven "
            "parametric generators and one real-prose family) at 4096 bytes and this pair of recipes; nothing here "
            "establishes a buyer.")
    else:
        verdict, meaning = "L3_LEADS_INCUMBENT_UNDER_TRANSFER", (
            f"Under leave-one-family-out transfer at 4096 on 0015's folds, 0014's searched, standardised logistic leads "
            f"0003's fixed incumbent by at least {MARGIN_BAR}: on content the models never saw, the standardised linear rule "
            f"(iteration counts banked; {below_cap} of 8 folds below the 1000 cap) identifies the encoder materially better "
            "than the boosted incumbent, while in-distribution the incumbent leads it by 0.0078 (0.2395 against 0.2317). L3 "
            "is a searched recipe and the incumbent is not; 0014's searched model is not measured here and its in-distribution "
            "clause is untouched. A statement about the corpus builder's eight families at 4096 bytes and this pair of "
            "recipes; nothing here establishes a buyer, and nothing here revises 0003, 0014 or 0015.")

    pf = (lofo.get("logistic_l3") or {}).get("per_family") or {}
    result = {
        "schema": "raise-v1/lofo_l3_4096_verdict/1",
        "preregistration": PREREG, "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "verdict": verdict, "meaning": meaning,
        "validity_failed_clauses": void, "lead_failed_clauses": fails,
        "bar_applied": {"reference_0015_incumbent_mixture": ref_m, "reference_0015_incumbent_correct": ref_mc, "margin": MARGIN_BAR,
                        "margin_correct_rows": MARGIN_CORRECT, "mixture_must_reach": MIXTURE_MUST_REACH,
                        "reaches_record_margin_bar_0.05": (l3_correct - ref_mc >= round(0.05 * n_rows)) if l3_correct is not None and not void else None,
                        # 0015's own transfer bar, its TRANSFERS comparison verbatim on the 4-decimal mixture (0.0885 passes)
                        "reaches_0015_transfer_bar": (round(l3_mix - CHANCE, 6) >= 0.05 - 1e-9) if l3_mix is not None and not void else None},
        "n_iter_by_fold": g("n_iter_by_fold"), "any_fold_at_iteration_cap": g("any_fold_at_iteration_cap"),
        "lofo_mixture_top1_l3": l3_mix if verdict != "VOID" else None,
        "lofo_correct_l3": l3_correct if verdict != "VOID" else None,
        "lofo_margin_l3_over_0015_model_exact": margin_exact,
        "lofo_mixture_top1_l3_banked_by_runner": banked_mix,
        "lofo_margin_l3_over_0015_model": num(g("lofo_margin_l3_over_0015_model")) if verdict != "VOID" else None,
        "lofo_margin_l3_over_0015_logistic": num(g("lofo_margin_l3_over_0015_logistic")) if verdict != "VOID" else None,
        "lofo_mixture_minus_chance_l3": round(banked_mix - CHANCE, 6) if banked_mix is not None and verdict != "VOID" else None,
        "per_family_l3": pf if verdict != "VOID" else None,
        "per_family_margin_over_0015_model": g("lofo_per_family_margin_over_0015_model"),
        "reference_0015": REFERENCE_0015,
        "structured_four_top1_l3": num((lofo.get("logistic_l3") or {}).get("structured_four_top1")) if verdict != "VOID" else None,
        "folds_below_iteration_cap": below_cap,
        "l3_reproduction_drift": round(num(l3.get("top1")) - L3_TOP1_0014, 6) if num(l3.get("top1")) is not None else None,
        "informational_only": "the margin over 0015's logistic, the per-family readings, the structured-four reading, the "
                              "reproduction drift and the artifact's cluster intervals are informational: not a verdict, "
                              "not quotable as a pass. The verdict is the `verdict` field.",
        "establishes_a_buyer": False, "revises_0003_0014_0015": False,
        "read": {k: g(k) for k in (
            "preregistration", "smoke", "stage", "complete", "missing_roles", "lofo_mixture_top1",
            "lofo_margin_l3_over_0015_model", "lofo_margin_l3_over_0015_model_exact", "lofo_correct_l3",
            "lofo_margin_l3_over_0015_logistic", "logistic_l3_refit_top1", "n_iter_by_fold", "any_fold_at_iteration_cap",
            "shuffled_label_accuracy", "chance_accuracy", "null_rows", "n_classes")},
        "lofo": lofo,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("READER 0017 — the searched logistic under leave-one-family-out transfer at 4096")
    for k, v in result["read"].items():
        print(f"  {k:<36} {v}")
    print(f"  lofo.logistic_l3                    {json.dumps(lofo.get('logistic_l3'))[:220]}")
    if void:
        print(f"\n  VALIDITY FAILED CLAUSES ({len(void)}):")
        for f in void:
            print(f"    · {f}")
    if fails:
        print(f"\n  LEAD FAILED CLAUSES ({len(fails)}):")
        for f in fails:
            print(f"    · {f}")
    print(f"\n  VERDICT: {verdict}")
    print(f"  {meaning}")
    print("  This does not establish a buyer, and was never capable of doing so.")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
