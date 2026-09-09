#!/usr/bin/env python3
"""Frozen reader for preregistration 0018 — out-of-builder transfer at 4096: does the headline recipe
(0014's searched HGB M4) identify the encoder on content families the corpus builder never produced?

Written and committed BEFORE any fit was made under this preregistration.

WHY THIS EXISTS. Every transfer reading in this record (0015, 0016, 0017) was taken inside the corpus
builder: seven parametric generators sharing one syllable vocabulary and one Gutenberg family. This
reader takes the runner's artifact (tools/pivot/run_oob.py) and checks, clause by clause: the sealed fit
corpus and split (every hash a literal below, 0003's); the sealed extension corpus (array hashes, row
and chunk counts, family order, chunk ids disjoint from the builder's); that every fit is the sealed
recipe (M1, L3, M4: params hashes below), fitted once on the sealed pool with the sealed seed and scored
exactly once; that each reproduction lands within 0.005 of its banked in-distribution value; that the
null control sits at chance on the extension rows; and that every banked reading equals what this
reader recomputes from the per-example vectors. Then one clause: M4's count of correct extension rows
against chance + 0.05. OOB_TRANSFERS or OOB_TRANSFER_FAILS, published at the same size; VOID on any
validity failure. The incumbent's and the standardised logistic's readings at the same bar are flags.

Digest convention: sha256 of np.ascontiguousarray(a).tobytes(); index arrays int64 in grouped_split /
np.nonzero order; y as stored (int16); sorted sets np.sort(...).astype(np.int64); extension arrays as
stored (float32 X, int16 y, int32 g, int8 fam), hashed in 20000-row pieces of the contiguous bytes.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "oob_4096.json")
SCORES = os.path.join(REPO, "artifacts", "pivot", "oob_4096_scores.json")
NOT_RUN = os.path.join(REPO, "artifacts", "pivot", "oob_4096_not_run.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "oob_4096_verdict.json")
PREREG = "0018-oob-4096"

FAMILIES = ["gutenberg", "base64", "binary", "code", "csv", "json", "log", "mixed"]
EXT_FAMILIES = ["c_src", "hexdump", "pe_bin", "py_src", "rfc_txt", "rst_doc", "sql", "xml"]
REAL_FAMILIES = ["c_src", "pe_bin", "py_src", "rfc_txt", "rst_doc"]
SYNTH_FAMILIES = ["hexdump", "sql", "xml"]
STRUCTURED_TEXT = ["c_src", "py_src", "rfc_txt", "rst_doc", "sql", "xml"]
HIGH_ENTROPY = ["hexdump", "pe_bin"]
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
 'ext_families': ['c_src', 'hexdump', 'pe_bin', 'py_src', 'rfc_txt', 'rst_doc', 'sql', 'xml'],
 'fit_rows': 'all',
 'roles': ['incumbent', 'logistic_l3', 'model'],
 'order': ['null', 'incumbent', 'logistic_l3', 'model'],
 'null_rows': 20000,
 'pool_idx_sha256': '17b0dc0bd9f7b9db6a5f0967cd96cbdccf524da56ed1aac7a80c4b57eb8ee7e5',
 'caps': {'memory_kill_gb': 14.0},
 'launch': {'min_disk_free_gb': 0.5, 'min_mem_available_gb': 14.5},
 'environment': {'sklearn': '1.9.0', 'numpy': '2.4.6', 'python': '3.11.15'},
 'reference_top1': {'incumbent': 0.2395, 'logistic_l3': 0.2317, 'model': 0.2884},
 'reference_source': 'artifacts/pivot/recipe_search_4096.json: incumbent_refit.top1, final.logistic.top1, '
                     'final.model.top1',
 'ext_corpus': {'npz': 'data/pivot/ext_c4096.npz',
                'manifest': 'artifacts/pivot/ext_corpus_manifest.json',
                'arrays': {'X': {'dtype': 'float32',
                                 'sha256': 'c578eaf142dfd776fe2c9433420133ae6b2d304cdd546f2bdbbc50b397c4f5db',
                                 'shape': [61409, 1108]},
                           'fam': {'dtype': 'int8',
                                   'sha256': '21b066e7020c5a4ba247101e679ba31f23cbeae5500ab67e64f453b83e61f917',
                                   'shape': [61409]},
                           'g': {'dtype': 'int32',
                                 'sha256': '2f5b8a86cc0463c1376d1ceb379ffe710e709899f2db4e1a527d355d6fcfc8b9',
                                 'shape': [61409]},
                           'y': {'dtype': 'int16',
                                 'sha256': 'edbf9b3a9aa810338807a4a397884b58b27a28bbf0d99826050403bdeeabdd46',
                                 'shape': [61409]}},
                'n_rows': 61409,
                'n_chunks': 2400,
                'families': ['c_src', 'hexdump', 'pe_bin', 'py_src', 'rfc_txt', 'rst_doc', 'sql', 'xml'],
                'real_families': ['c_src', 'pe_bin', 'py_src', 'rfc_txt', 'rst_doc'],
                'synthetic_families': ['hexdump', 'sql', 'xml'],
                'rows_per_family': {'c_src': 7800,
                                    'hexdump': 7800,
                                    'pe_bin': 7407,
                                    'py_src': 7709,
                                    'rfc_txt': 7761,
                                    'rst_doc': 7775,
                                    'sql': 7357,
                                    'xml': 7800},
                'chunks_per_family': {'c_src': 300,
                                      'hexdump': 300,
                                      'pe_bin': 300,
                                      'py_src': 300,
                                      'rfc_txt': 300,
                                      'rst_doc': 300,
                                      'sql': 300,
                                      'xml': 300},
                'ceiling_distinct_fragments': {'c_src': 0.9751,
                                               'hexdump': 0.9987,
                                               'pe_bin': 0.8949,
                                               'py_src': 0.9828,
                                               'rfc_txt': 0.9768,
                                               'rst_doc': 0.9538,
                                               'sql': 0.8987,
                                               'xml': 0.9512},
                'ceiling_distinct_streams': {'c_src': 0.9818,
                                             'hexdump': 1.0,
                                             'pe_bin': 0.9499,
                                             'py_src': 0.9959,
                                             'rfc_txt': 0.9856,
                                             'rst_doc': 0.966,
                                             'sql': 0.9533,
                                             'xml': 0.9524},
                'chunk_id_min': 10000000,
                'chunk_id_max': 10700299,
                'rows_dropped_short_stream': 991,
                'seed': 20260909,
                'n_per_family': 300,
                'source_pins_sha256_of_file': '2403ba48846503b6f92744558e1d34453124aa3e56d6058614a49da864e5f694'},
 'bar': {'model_ext_correct_over_n_ext_minus_chance': 0.05},
 'min_correct': 5433,
 'reproduction_tolerance': 0.005,
 'null_tolerance': 0.02,
 'subsets': {'structured_text': ['c_src', 'py_src', 'rfc_txt', 'rst_doc', 'sql', 'xml'],
             'high_entropy': ['hexdump', 'pe_bin']}}
PROTOCOL_SHA256 = "209671c428800039d6f7419c19fd3d8e3cc325021df1ff0f7dfd56ce572b2610"
# 0003's incumbent M1, 0014's L3 and 0014's M4, byte for byte the sealed entries; each record's params_sha256
# must equal its recipe's canonical-JSON hash.
RECIPES = {'incumbent': {'family': 'hgb',
               'id': 'M1',
               'params': {'learning_rate': 0.15,
                          'max_iter': 200,
                          'max_leaf_nodes': 63,
                          'n_iter_no_change': 10},
               'val': 'frag',
               'scaled': False,
               'why': "0003's incumbent recipe verbatim (0014 incumbent_refit: 0.2395 on the sealed set); "
                      'the fixed boosted model every transfer reading so far was taken on'},
 'logistic_l3': {'family': 'logistic',
                 'id': 'L3',
                 'params': {'C': 1.0, 'max_iter': 1000},
                 'scaled': True,
                 'why': 'standardised inputs with C 1.0: the single most standard fix for an lbfgs logistic '
                        'on 1108 unscaled hand-engineered columns'},
 'model': {'family': 'hgb',
           'id': 'M4',
           'params': {'l2_regularization': 1.0,
                      'learning_rate': 0.05,
                      'max_iter': 250,
                      'max_leaf_nodes': 127,
                      'n_iter_no_change': 20},
           'val': 'frag',
           'scaled': False,
           'why': "0014's searched model verbatim (final.model: 0.2884 on the sealed set, 250 iterations); "
                  'the headline recipe, never fitted under transfer before this preregistration'}}
RECIPES_SHA256 = "0f3c895efcabd59c7fbeee0815a5e3f8e16ae8bd8460fd25760273398033aaeb"
RECIPE_SHA256 = {'incumbent': 'a59f10c62a5cb852540916f3d39e4a5b7843a3eaa8c778a64cea139cc8d0a51a',
 'logistic_l3': '6c963004952ef934d6609c0a9d1d384a87728591b1694515f43328ab05344dfe',
 'model': '2fb41d66ad962cc8938b990f3867fb4caf26470d7a0b9a66bac83bfd1f772260'}
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
 'fit_rows': 'all',
 'families': ['gutenberg', 'base64', 'binary', 'code', 'csv', 'json', 'log', 'mixed'],
 'null_rows': 20000,
 'null_sorted_sha256': '0653cc12293ae078dd68b900c8778d93e701261ca93414be9eb7bb8e7ee686db',
 'pool_rows_in_ext': 0,
 'eval_rows_in_ext': 0,
 'split_is_grouped_by_source': True}
# The extension corpus, sealed at build time by tools/pivot/corpus_ext.py; evaluation only.
EXT = {'npz': 'data/pivot/ext_c4096.npz',
 'arrays': {'X': {'dtype': 'float32',
                  'sha256': 'c578eaf142dfd776fe2c9433420133ae6b2d304cdd546f2bdbbc50b397c4f5db',
                  'shape': [61409, 1108]},
            'fam': {'dtype': 'int8',
                    'sha256': '21b066e7020c5a4ba247101e679ba31f23cbeae5500ab67e64f453b83e61f917',
                    'shape': [61409]},
            'g': {'dtype': 'int32',
                  'sha256': '2f5b8a86cc0463c1376d1ceb379ffe710e709899f2db4e1a527d355d6fcfc8b9',
                  'shape': [61409]},
            'y': {'dtype': 'int16',
                  'sha256': 'edbf9b3a9aa810338807a4a397884b58b27a28bbf0d99826050403bdeeabdd46',
                  'shape': [61409]}},
 'n_rows': 61409,
 'n_chunks': 2400,
 'families': ['c_src', 'hexdump', 'pe_bin', 'py_src', 'rfc_txt', 'rst_doc', 'sql', 'xml'],
 'rows_per_family': {'c_src': 7800,
                     'hexdump': 7800,
                     'pe_bin': 7407,
                     'py_src': 7709,
                     'rfc_txt': 7761,
                     'rst_doc': 7775,
                     'sql': 7357,
                     'xml': 7800},
 'chunks_per_family': {'c_src': 300,
                       'hexdump': 300,
                       'pe_bin': 300,
                       'py_src': 300,
                       'rfc_txt': 300,
                       'rst_doc': 300,
                       'sql': 300,
                       'xml': 300},
 'chunk_id_min': 10000000,
 'chunk_id_max': 10700299,
 'chunk_ids_disjoint_from_builder': True}
EXT_CEILING_FRAGMENTS = {'c_src': 0.9751,
 'hexdump': 0.9987,
 'pe_bin': 0.8949,
 'py_src': 0.9828,
 'rfc_txt': 0.9768,
 'rst_doc': 0.9538,
 'sql': 0.8987,
 'xml': 0.9512}
# The banked in-distribution readings each reproduction must land on (artifacts/pivot/recipe_search_4096.json:
# incumbent_refit.top1, final.logistic.top1, final.model.top1), compared at the 4-decimal precision the accuracies
# are banked at.
REFERENCE_TOP1 = {'incumbent': 0.2395, 'logistic_l3': 0.2317, 'model': 0.2884}
REPRODUCTION_TOLERANCE, NULL_TOLERANCE, CHANCE = 0.005, 0.02, 0.038462
BAR = 0.05
N_EXT = 61409
# The clause is read on EXACT counts: M4's correct extension rows, recomputed here from its per-example vector, must
# reach ceil(N_EXT x (1/26 + BAR)) = MIN_CORRECT.
MIN_CORRECT = 5433
MIXTURE_MUST_REACH = 0.088462   # the same bar restated as a mixture over N_EXT rows, 6 decimals
ENV = {"threads": 3, "nice": 10, "sklearn": "1.9.0", "numpy": "2.4.6"}
SEED = 20260825
ROLES = ["incumbent", "logistic_l3", "model"]


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_obj(obj) -> str:
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def main() -> int:
    if not os.path.exists(ARTIFACT):
        if os.path.exists(NOT_RUN):
            try:
                nr = json.load(open(NOT_RUN, encoding="utf-8"))
                print(f"READER 0018: NOT RUN — {nr.get('reason')!r} (stage {nr.get('stage')}, filed {nr.get('utc')}, "
                      f"{nr.get('n_checkpoints')} checkpoints). A NOT RUN is not a verdict.", file=sys.stderr)
            except Exception:  # noqa: BLE001
                print("READER 0018: NOT RUN file present but unreadable.", file=sys.stderr)
            return 2
        print(f"READER 0018: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n  Absence is not a pass. No verdict emitted.",
              file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0018: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
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
        void.append("scope: the banked recipes are not the sealed M1, L3 and M4")
    if g("reference_top1") != REFERENCE_TOP1:
        void.append("scope: the banked in-distribution references are not the sealed ones")

    # ---- the extension corpus
    ext = g("ext_corpus") or {}
    for k, v in EXT.items():
        expect_eq(void, ext.get(k), v, f"extension corpus: ext_corpus.{k}")
    if g("n_ext_rows") != N_EXT or g("n_eval_rows") != PARTITION["n_eval_rows"]:
        void.append(f"extension corpus: n_ext_rows={g('n_ext_rows')!r}, n_eval_rows={g('n_eval_rows')!r}")

    # ---- sealed sets
    part = g("partition") or {}
    for k, v in PARTITION.items():
        expect_eq(void, part.get(k), v, f"sealed set: partition.{k}")
    if g("complete") is not True:
        void.append(f"complete: complete={g('complete')!r}; missing {g('missing_roles')!r}")
    if g("null_rows") != PROTOCOL["null_rows"]:
        void.append(f"null control: null_rows={g('null_rows')!r}")

    # ---- scores file, ledger
    n_eval = PARTITION["n_eval_rows"]; n_all = n_eval + N_EXT
    scores, ext_fam_idx = {}, None
    if os.path.exists(SCORES):
        try:
            sd = json.load(open(SCORES, encoding="utf-8")) or {}
            scores = sd.get("per_example") or {}
            ext_fam_idx = sd.get("ext_fam")
            if sd.get("eval_idx_sha256") != PARTITION["eval_idx_sha256"] or sd.get("smoke") is not False \
                    or sd.get("preregistration") != PREREG or sd.get("n_eval_rows") != n_eval or sd.get("n_ext_rows") != N_EXT \
                    or sd.get("ext_families") != EXT_FAMILIES \
                    or sd.get("ext_arrays_sha256") != {k: v["sha256"] for k, v in EXT["arrays"].items()}:
                void.append("scores: the scores file is not this run's, or is a smoke run's, or names a different extension corpus")
            eci = sd.get("ext_chunk_ids")
            if not isinstance(eci, list) or len(eci) != N_EXT:
                void.append("scores: ext_chunk_ids missing or not N_EXT long")
        except Exception:  # noqa: BLE001
            void.append("scores: the scores file is not JSON")
    else:
        void.append("scores: the scores file is absent")

    def _ints(v, n, values=None):
        return isinstance(v, list) and len(v) == n and all(
            isinstance(x, int) and not isinstance(x, bool) and (values is None or x in values) for x in v)

    if not _ints(ext_fam_idx, N_EXT, set(range(len(EXT_FAMILIES)))):
        void.append("scores: ext_fam missing, not N_EXT long, or not family indices"); ext_fam_idx = None
    elif ext_fam_idx is not None:
        counts = {f: 0 for f in EXT_FAMILIES}
        for i in ext_fam_idx:
            counts[EXT_FAMILIES[i]] += 1
        if counts != EXT["rows_per_family"]:
            void.append(f"scores: ext_fam row counts {counts} are not the sealed rows_per_family")
    ledger = g("ledger") or []
    fits = g("fits") or {}

    def check_record(name, rec, role, rows_sha, sorted_sha, n_rows, stage):
        if not isinstance(rec, dict) or rec.get("status") != "fit":
            void.append(f"fit: {name} status {(rec or {}).get('status')!r}; must be 'fit'"); return
        if num(rec.get("top1")) is None or num(rec.get("top1_non_gutenberg")) is None or \
                not isinstance(rec.get("per_family"), dict) or len(rec["per_family"]) != 8 or \
                any(num(v) is None for v in rec["per_family"].values()):
            void.append(f"fit: {name} scores are not all finite")
        cand = RECIPES[role]
        if rec.get("id") != cand["id"] or rec.get("params_sha256") != RECIPE_SHA256[role] \
                or bool(rec.get("scaled")) != bool(cand.get("scaled", False)) or rec.get("val") != cand.get("val"):
            void.append(f"fit: {name} is not the sealed {cand['id']} (id {rec.get('id')!r}, params hash, scaled or val off-recipe)")
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
        pe = scores.get(name)
        if not _ints(pe, n_all, (0, 1)):
            void.append(f"fit: {name} per-example vector missing, not {n_all} long, or not in {{0, 1}}")

    for r in ROLES:
        check_record(r, fits.get(r), r, PARTITION["pool_idx_sha256"], PARTITION["pool_sorted_sha256"], PARTITION["n_pool_rows"], "pool")
    nc = fits.get("null") or {}
    check_record("null", nc, "model", None, PARTITION["null_sorted_sha256"], PROTOCOL["null_rows"], "null")
    if nc.get("head") != "null":
        void.append("null control: the null record is not the null-stage fit")
    if g("null_control") != nc:
        void.append("null control: null_control is not the banked null record")
    env = g("environment") or {}
    for k, v in ENV.items():
        if env.get(k) != v:
            void.append(f"environment: {k}={env.get(k)!r}, banked {v!r}")

    # ---- every reading re-derived from the per-example vectors and the extension family indices
    reads = g("readings") or {}
    mean4 = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
    rec_reads = {}
    if ext_fam_idx is not None and not any(m.startswith("fit:") or m.startswith("scores:") for m in void):
        fam_x = [EXT_FAMILIES[i] for i in ext_fam_idx]
        for name in ROLES + ["null"]:
            v = scores[name]; rep, ex = v[:n_eval], v[n_eval:]
            by = {f: [] for f in EXT_FAMILIES}
            for i in range(N_EXT):
                by[fam_x[i]].append(ex[i])
            rr = {"reproduction_top1": mean4(rep), "reproduction_correct": sum(rep),
                  "ext_top1": mean4(ex), "ext_correct": sum(ex), "n_ext_rows": N_EXT,
                  "ext_per_family": {f: mean4(by[f]) for f in EXT_FAMILIES},
                  "ext_per_family_correct": {f: sum(by[f]) for f in EXT_FAMILIES},
                  "ext_structured_text_top1": mean4([x for f in STRUCTURED_TEXT for x in by[f]]),
                  "ext_high_entropy_top1": mean4([x for f in HIGH_ENTROPY for x in by[f]]),
                  "ext_real_top1": mean4([x for f in REAL_FAMILIES for x in by[f]]),
                  "ext_synthetic_top1": mean4([x for f in SYNTH_FAMILIES for x in by[f]])}
            rec_reads[name] = rr
            banked = reads.get(name) or {}
            for k, val in rr.items():
                if banked.get(k) != val:
                    void.append(f"readings: {name}.{k}={banked.get(k)!r} is not the reader's recomputation {val!r}")
        for r in ROLES:
            if num((g("reproduction_top1") or {}).get(r)) != rec_reads[r]["reproduction_top1"]:
                void.append(f"reproduction: reproduction_top1.{r} is not the recomputed value")
            if num((g("ext_top1") or {}).get(r)) != rec_reads[r]["ext_top1"] or (g("ext_correct") or {}).get(r) != rec_reads[r]["ext_correct"]:
                void.append(f"readings: ext_top1.{r} or ext_correct.{r} is not the recomputed value")
            if (g("ext_per_family") or {}).get(r) != rec_reads[r]["ext_per_family"]:
                void.append(f"readings: ext_per_family.{r} is not the recomputed value")
            drift = round(abs(rec_reads[r]["reproduction_top1"] - REFERENCE_TOP1[r]), 6)
            if drift > REPRODUCTION_TOLERANCE:
                void.append(f"reproduction: {r} on the full pool scores {rec_reads[r]['reproduction_top1']} against the banked "
                            f"{REFERENCE_TOP1[r]}; the pool, the evaluation set or the machinery is not 0014's")
        if num(g("ext_top1_model")) != rec_reads["model"]["ext_top1"] or g("ext_correct_model") != rec_reads["model"]["ext_correct"]:
            void.append("readings: ext_top1_model or ext_correct_model is not the recomputed value")
        mc, lc, ic = (rec_reads[r]["ext_correct"] for r in ROLES[2:] + ROLES[1:2] + ROLES[:1])
        if num(g("ext_margin_model_over_logistic_l3_exact")) != round((mc - lc) / N_EXT, 6):
            void.append("margin: ext_margin_model_over_logistic_l3_exact is not (correct counts difference) / N_EXT")
        if num(g("ext_margin_model_over_incumbent_exact")) != round((mc - ic) / N_EXT, 6):
            void.append("margin: ext_margin_model_over_incumbent_exact is not (correct counts difference) / N_EXT")
        null_ext = rec_reads["null"]["ext_top1"]
        if num(g("shuffled_label_accuracy_ext")) != null_ext:
            void.append("null control: shuffled_label_accuracy_ext is not the recomputed value")
        elif null_ext > CHANCE + NULL_TOLERANCE:
            void.append(f"null control: shuffled labels reached {null_ext} on the extension rows, above chance {CHANCE} + "
                        f"{NULL_TOLERANCE} — the pipeline leaks")
    elif not void:
        void.append("readings: the reader could not recompute the readings")

    # ---- the one clause, on the reader's own count of M4's correct extension rows
    fails: list[str] = []
    mc = rec_reads.get("model", {}).get("ext_correct") if not void else None
    if not void and mc < MIN_CORRECT:
        fails.append(f"transfer: M4's correct extension rows {mc} of {N_EXT} ({rec_reads['model']['ext_top1']}) is below "
                     f"{MIN_CORRECT} (chance {CHANCE} + {BAR} = {MIXTURE_MUST_REACH})")

    flags = None
    if not void:
        lc = rec_reads["logistic_l3"]["ext_correct"]; ic = rec_reads["incumbent"]["ext_correct"]
        flags = {"logistic_l3_reaches_bar": lc >= MIN_CORRECT, "incumbent_reaches_bar": ic >= MIN_CORRECT,
                 "model_leads_logistic_l3_rows": mc - lc, "model_leads_incumbent_rows": mc - ic,
                 "model_leads_logistic_l3_by_0.05": mc - lc >= math.ceil(0.05 * N_EXT - 1e-9),
                 "model_leads_incumbent_by_0.05": mc - ic >= math.ceil(0.05 * N_EXT - 1e-9),
                 "families_where_model_reaches_bar": [f for f in EXT_FAMILIES
                                                      if rec_reads["model"]["ext_per_family"][f] >= round(CHANCE + BAR, 4)]}

    if void:
        verdict, meaning = "VOID", ("A validity or control clause fails, or the artifact is incomplete. This run says nothing "
                                    "about transfer outside the builder in either direction.")
    elif fails:
        verdict, meaning = "OOB_TRANSFER_FAILS", (
            f"At 4096 bytes, 0014's searched model, fitted on the builder's eight families, does not identify the encoder on "
            f"the eight extension families at chance + {BAR}: {mc} of {N_EXT} extension rows correct "
            f"({rec_reads['model']['ext_top1']}) against {MIN_CORRECT} needed. A bound on the headline recipe's reach outside "
            "the builder, for these eight families (five real, pinned; three synthetic); per-family readings and ceilings are "
            "banked beside it. Nothing here revises 0003, 0014, 0015, 0016 or 0017, and nothing here establishes a buyer.")
    else:
        verdict, meaning = "OOB_TRANSFERS", (
            f"At 4096 bytes, 0014's searched model, fitted on the builder's eight families, identifies the encoder on the eight "
            f"extension families at chance + {BAR} or better: {mc} of {N_EXT} extension rows correct "
            f"({rec_reads['model']['ext_top1']}) against {MIN_CORRECT} needed. The first transfer reading in this record taken "
            "outside the builder, for these eight families (five real, pinned; three synthetic); per-family readings and "
            "ceilings are banked beside it. Nothing here revises 0003, 0014, 0015, 0016 or 0017, and nothing here establishes a buyer.")

    result = {
        "schema": "raise-v1/oob_4096_verdict/1",
        "preregistration": PREREG, "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "verdict": verdict, "meaning": meaning,
        "validity_failed_clauses": void, "transfer_failed_clauses": fails,
        "bar_applied": {"chance": CHANCE, "bar": BAR, "mixture_must_reach": MIXTURE_MUST_REACH, "min_correct": MIN_CORRECT,
                        "n_ext_rows": N_EXT, "flags": flags},
        "ext_top1_model": rec_reads["model"]["ext_top1"] if not void else None,
        "ext_correct_model": mc if not void else None,
        "ext_top1": {r: rec_reads[r]["ext_top1"] for r in ROLES} if not void else None,
        "ext_correct": {r: rec_reads[r]["ext_correct"] for r in ROLES} if not void else None,
        "ext_per_family": {r: rec_reads[r]["ext_per_family"] for r in ROLES} if not void else None,
        "ext_subsets": {r: {k: rec_reads[r][k] for k in ("ext_structured_text_top1", "ext_high_entropy_top1", "ext_real_top1",
                                                         "ext_synthetic_top1")} for r in ROLES} if not void else None,
        "ext_margin_model_over_logistic_l3_exact": num(g("ext_margin_model_over_logistic_l3_exact")) if not void else None,
        "ext_margin_model_over_incumbent_exact": num(g("ext_margin_model_over_incumbent_exact")) if not void else None,
        "ext_mixture_minus_chance_model": round(rec_reads["model"]["ext_top1"] - CHANCE, 6) if not void else None,
        "reproduction_top1": {r: rec_reads[r]["reproduction_top1"] for r in ROLES} if not void else None,
        "reproduction_drift": {r: round(rec_reads[r]["reproduction_top1"] - REFERENCE_TOP1[r], 6) for r in ROLES} if not void else None,
        "reference_top1": REFERENCE_TOP1,
        "shuffled_label_accuracy_ext": rec_reads["null"]["ext_top1"] if not void else None,
        "ext_ceiling_distinct_fragments": EXT_CEILING_FRAGMENTS,
        "ext_rows_per_family": EXT["rows_per_family"],
        "fit_info_by_role": g("fit_info_by_role"),
        "informational_only": "the flags, the per-family and subset readings, the margins, the reproduction drifts, the ceilings and "
                              "the artifact's cluster intervals are informational: not a verdict, not quotable as a pass. The "
                              "verdict is the `verdict` field.",
        "establishes_a_buyer": False, "revises_0003_0014_0015_0016_0017": False,
        "read": {k: g(k) for k in (
            "preregistration", "smoke", "stage", "complete", "missing_roles", "ext_top1_model", "ext_correct_model", "ext_top1",
            "reproduction_top1", "ext_margin_model_over_logistic_l3_exact", "ext_margin_model_over_incumbent_exact",
            "shuffled_label_accuracy_ext", "chance_accuracy", "null_rows", "n_ext_rows", "n_classes")},
        "readings_banked": reads,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("READER 0018 — out-of-builder transfer at 4096")
    for k, v in result["read"].items():
        print(f"  {k:<40} {v}")
    print(f"  ext_per_family (model)                   {json.dumps((reads.get('model') or {}).get('ext_per_family'))}")
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
