#!/usr/bin/env python3
"""Frozen reader for preregistration 0016 — at a fixed plaintext budget, does spreading the training
data over more content families improve encoder identification on a family the model never saw?
The family-diversity transfer curve (FDC) at 4096 with 0003's fixed recipes.

Written and committed BEFORE any fold was fitted under this preregistration.

WHY THIS EXISTS. 0015 established that 0003's recipe, fitted on seven content families, does not
identify the encoder on the eighth at chance + 0.05, and left open whether that is a matter of how many
content types the model has seen. This reader takes the runner's artifact (tools/pivot/run_fdc.py) and
checks, clause by clause: the sealed corpus, split, reproduction rung, null block and every fold — the
32 fixed-budget (family, count) folds, the 24 single-family depth folds and the 8 predecessor folds
(every hash a literal below); that no fold's training rows contain a row of the held-out family, a row
outside its chosen families, or a chunk of the evaluation set, and that each fold's per-family chunk
counts are exactly what the sealed subset rule says, recomputed here from the family order; that every
fit is 0003's recipe (params hashes below), fitted on the sealed rows with the sealed seed and scored
exactly once; that the reproduction control lands on 0003's banked 100000-row rung; that the null
control sits at chance; and that every stitched mixture, curve and derived reading equals what this
reader recomputes from the per-example vectors and the banked chunk ids. Then one clause: this reader's
own ordinary-least-squares slope of the model's fixed-budget mixture against log2(family count), in
accuracy per doubling of families, against 0.005. DIVERSITY_HELPS or DIVERSITY_FLAT, published at the
same size; VOID on any validity failure.

Every constant below was computed on 2026-09-09 from data/pivot/full_c4096.npz (corpus A) with
tools/pivot/run_carve.py grouped_split(seed 20260825, eval_frac 0.2, cap 800000), the family rule
FAMILIES[chunk_id modulo 8] and the chunk-budget subset rule, before any 0016 fit. Digest convention:
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
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "fdc_4096.json")
SCORES = os.path.join(REPO, "artifacts", "pivot", "fdc_4096_scores.json")
NOT_RUN = os.path.join(REPO, "artifacts", "pivot", "fdc_4096_not_run.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "fdc_4096_verdict.json")
PREREG = "0016-fdc-4096"

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
 'family_counts': [1, 2, 4, 7],
 'subset_rule': 'following_cyclic_nested_by_chunk',
 'repro_rows': 100000,
 'roles': ['majority', 'logistic', 'model'],
 'order': ['reproduction_100k', 'null', 'folds'],
 'null_rows': 20000,
 'structured_families': ['code', 'csv', 'json', 'log'],
 'caps': {'memory_kill_gb': 13.0},
 'launch': {'min_disk_free_gb': 0.25, 'min_mem_available_gb': 6.0},
 'bar': {'slope_per_doubling_of_families': 0.005},
 'reproduction_tolerance': 0.005,
 'null_tolerance': 0.02,
 'budget_chunks': 4900,
 'environment': {'sklearn': '1.9.0', 'numpy': '2.4.6', 'python': '3.11.15'}}
PROTOCOL_SHA256 = "0106cde7242d88fe0c9822b19cb13544e6661ef313b06ef8d1675d41f56bc737"
# 0003's three fixed recipes, byte for byte 0015's sealed recipes; their canonical-JSON hashes are what
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
 'pool_sorted_sha256': '923cd266c3bf2a45683b2c479d36b046b311cc8f2e53426c962b6dd5ae836094',
 'pool_rows_per_family': {'gutenberg': 99712,
                          'base64': 99440,
                          'binary': 100103,
                          'code': 100346,
                          'csv': 100560,
                          'json': 99929,
                          'log': 99527,
                          'mixed': 100383},
 'pool_chunks_per_family': {'gutenberg': 4981,
                            'base64': 4986,
                            'binary': 5001,
                            'code': 5025,
                            'csv': 5034,
                            'json': 4990,
                            'log': 4971,
                            'mixed': 5012},
 'repro_rows': 100000,
 'repro_idx_sha256': '659169fcf818b742154948c86e7d60dda61f798a7b5f671c29a0b64827f34297',
 'repro_sorted_sha256': '38de80c9bf49f2ea8be8e52545632a0904de4b57dc00256c165123efeed7596a',
 'null_rows': 20000,
 'null_sorted_sha256': '822b61020d276a04620440eb2d2e7e60376e1efba83e89607c33c09c39fa1425',
 'budget_chunks': 4900,
 'family_counts': [1, 2, 4, 7],
 'depth_chunks': [4900, 2450, 1225, 700],
 'subset_rule': 'following_cyclic_nested_by_chunk',
 'families': ['gutenberg', 'base64', 'binary', 'code', 'csv', 'json', 'log', 'mixed']}
# The plaintext budget in source chunks, the family counts and their log2 (the abscissa), and the depth
# arm's sizes (the budget over each count; the budget itself is the k = 1 fold).
BUDGET_CHUNKS = 4900
KS = [1, 2, 4, 7]
LOG2K = [0.0, 1.0, 2.0, 2.807355]
DEPTH_CHUNKS = [4900, 2450, 1225, 700]
# Per held-out family: its evaluation rows; per family count k the chosen families (the k families that
# follow it cyclically in FAMILIES, nested in k), the chunks per family (budget / k), the sealed row
# count and hashes; the depth folds (the first successor alone at budget / k chunks, k > 1); and the
# predecessor fold (the family before it, at the budget). The runner also banks per fold, and this
# reader requires, four zero leakage counts and per-family row and chunk maps that agree with the rule.
FOLDS = {'gutenberg': {'n_eval_rows': 32994,
               'eval_idx_sha256': 'a6a1bef8036511315d2ac17e4a0f7078c6be848ca1c2c4b42d4ee6a084a56202',
               'by_k': {'1': {'families': ['base64'],
                              'chunks_per_family': 4900,
                              'n_train_rows': 97797,
                              'train_idx_sha256': '898e252261186184cd372e04c0521618a2476de333820ca18876bdca5a12a230',
                              'train_sorted_sha256': 'db6001d26d18cccaab51e4cf573614517225bb62566833fc137866f0fd639f6d',
                              'n_train_chunks': 4900},
                        '2': {'families': ['base64', 'binary'],
                              'chunks_per_family': 2450,
                              'n_train_rows': 98590,
                              'train_idx_sha256': '83469fa3e5fe2ad0f74d9b2e3f687fe70ed949843dd345718af2f3961fceee60',
                              'train_sorted_sha256': 'fc2adccbadbad600e79a60e1b0c010696eec2db9a2e9862455d4c76fb54f00ad',
                              'n_train_chunks': 4900},
                        '4': {'families': ['base64', 'binary', 'code', 'csv'],
                              'chunks_per_family': 1225,
                              'n_train_rows': 98973,
                              'train_idx_sha256': 'a1945e4e5a003786b7524c2f6d444933691c0eda4d052a9a5b85d80af5f80a5d',
                              'train_sorted_sha256': 'e7ff9ce368436e33e2a3c8d0c247e658fb24c918d4dbd5deeb3d5ed22ba12fb4',
                              'n_train_chunks': 4900},
                        '7': {'families': ['base64', 'binary', 'code', 'csv', 'json', 'log', 'mixed'],
                              'chunks_per_family': 700,
                              'n_train_rows': 99226,
                              'train_idx_sha256': '12ee75ea7d9d0239fe0bd8aec9195db85ee4e684d169ca5597b511bf1b943433',
                              'train_sorted_sha256': '29f2cab72ec354e574c2c270b06731e9c9c5f377b3318e26f2ca73a8881678ea',
                              'n_train_chunks': 4900}},
               'depth': {'2450': {'families': ['base64'],
                                  'chunks_per_family': 2450,
                                  'n_train_rows': 49106,
                                  'train_idx_sha256': '823b61c05221790ca54862af7b3bcb216f0f61e7fef23a85782545f12b501339',
                                  'train_sorted_sha256': '24639de0439a3c925dfb9fa1bc7ee79912672969b680e8b262d3117373bb02f0',
                                  'n_train_chunks': 2450},
                         '1225': {'families': ['base64'],
                                  'chunks_per_family': 1225,
                                  'n_train_rows': 24678,
                                  'train_idx_sha256': 'b0c28e21d3a2ce64456ce80b016c8b26b3096ff144a187116080fcdf0e0bf746',
                                  'train_sorted_sha256': '461acf59431a8c50481b1c6989ba013c0619a33b0c9fc5243209cd559f15a401',
                                  'n_train_chunks': 1225},
                         '700': {'families': ['base64'],
                                 'chunks_per_family': 700,
                                 'n_train_rows': 14168,
                                 'train_idx_sha256': '895278c2769e56ea188d11247f890a8c973f7a4c275801c7ee8ee69972dac6de',
                                 'train_sorted_sha256': '532c2f1d079cc2e658d42e4c121d7bdc20d41ac07a42653c0e0deed6e3e3acfd',
                                 'n_train_chunks': 700}},
               'pred_k1': {'families': ['mixed'],
                           'chunks_per_family': 4900,
                           'n_train_rows': 98225,
                           'train_idx_sha256': 'd2659b4480017fedd17a67ba1540fd5a3cc5bc02a75626dbcb9a2739bdffc344',
                           'train_sorted_sha256': '535fd1dff1587ff8904102743929b6eb81742ab94a9db58add52dadbe2f1b803',
                           'n_train_chunks': 4900}},
 'base64': {'n_eval_rows': 32864,
            'eval_idx_sha256': 'bdebc4239afd64ccdfc6c27415326d95f29d1bcd8b46a4cf87b2c7fb63ad04eb',
            'by_k': {'1': {'families': ['binary'],
                           'chunks_per_family': 4900,
                           'n_train_rows': 98161,
                           'train_idx_sha256': 'fdbe4640d1be305d6cb91c4484453fae488192bf2b38503153e47a0eeaf0567a',
                           'train_sorted_sha256': '5ea3f980141929b44118829217844d29fb4c86212b704bfb01c1b7cc1b04235e',
                           'n_train_chunks': 4900},
                     '2': {'families': ['binary', 'code'],
                           'chunks_per_family': 2450,
                           'n_train_rows': 98888,
                           'train_idx_sha256': '993a95e3743346f8da2bf42d4c7de8808e7520460bf7c3fa4793707bb765a276',
                           'train_sorted_sha256': 'ec9e645a44d6e3ff9047c5a6ba7ec750f557f8f43f83e9fbeb606f3f822d0ca1',
                           'n_train_chunks': 4900},
                     '4': {'families': ['binary', 'code', 'csv', 'json'],
                           'chunks_per_family': 1225,
                           'n_train_rows': 99125,
                           'train_idx_sha256': '03262eee7d218f940151755a19c391f64ad5894163626001634d7a925f3e814a',
                           'train_sorted_sha256': 'a3246dcab2e4dffc9c4687f7c5817c7f9fce3cfd671e7ecbb8351f2eb0c3163f',
                           'n_train_chunks': 4900},
                     '7': {'families': ['binary', 'code', 'csv', 'json', 'log', 'mixed', 'gutenberg'],
                           'chunks_per_family': 700,
                           'n_train_rows': 99163,
                           'train_idx_sha256': '56cbc8b3d4047aff2809485e5e0b22d788d25fd6835041bde894d789d6430079',
                           'train_sorted_sha256': '79d63cf2cca5579ec63036f490c8660e8e36f09ea4ceaaadd25cde9e818d9e2e',
                           'n_train_chunks': 4900}},
            'depth': {'2450': {'families': ['binary'],
                               'chunks_per_family': 2450,
                               'n_train_rows': 49484,
                               'train_idx_sha256': 'a5cc4b1f41cd2006c11beeaddcf188b3dbd650b8002795de9fa4648a91cb2c2d',
                               'train_sorted_sha256': '4806b86c03cde1c1889abf9b451c5e9338c787d51e1d0e67ee53f0360aebc965',
                               'n_train_chunks': 2450},
                      '1225': {'families': ['binary'],
                               'chunks_per_family': 1225,
                               'n_train_rows': 24792,
                               'train_idx_sha256': '3d3642651ab55ae36aa17ba10c86d4db25be63238f9aa2ae9764f9b97fa83f31',
                               'train_sorted_sha256': 'e78303c76bd090bda4a11a9c6ee55579229c6ceeed43e5961803653d1ba18923',
                               'n_train_chunks': 1225},
                      '700': {'families': ['binary'],
                              'chunks_per_family': 700,
                              'n_train_rows': 14152,
                              'train_idx_sha256': '7a0c0897ad8c5a8872569a328c101630da3fae2124f8d84bb7fbd3ea76a1a684',
                              'train_sorted_sha256': 'dcd304f6c4cb3df18dd46257d0fa49cc198fb865b76278db4cd426aa701d113c',
                              'n_train_chunks': 700}},
            'pred_k1': {'families': ['gutenberg'],
                        'chunks_per_family': 4900,
                        'n_train_rows': 98209,
                        'train_idx_sha256': '8bf3783cf12d4511b1fd5845d2f57900cef929861c26c0b7e9aee03db9b32055',
                        'train_sorted_sha256': '2dca00111af073547d6cc9ee84365ff095345a793fc74b9fefa178b10a5014d3',
                        'n_train_chunks': 4900}},
 'binary': {'n_eval_rows': 32474,
            'eval_idx_sha256': 'f91f609e7fb8739a17c0bb3a6fce9afdf1599b8282e14e366823461fb1dbd8c4',
            'by_k': {'1': {'families': ['code'],
                           'chunks_per_family': 4900,
                           'n_train_rows': 97972,
                           'train_idx_sha256': 'e77ce52541fe772f5ff448502e62323b38f50dc186376cd0da5bf47ebeda9317',
                           'train_sorted_sha256': '1020cab547322aab5c051814cc9871f9491672530eef68adef11ab2058ef130c',
                           'n_train_chunks': 4900},
                     '2': {'families': ['code', 'csv'],
                           'chunks_per_family': 2450,
                           'n_train_rows': 98746,
                           'train_idx_sha256': 'f37f388ea3f4781bc2ea98b12bc99174a297fe4b25dc8dc999a79d94da4da30b',
                           'train_sorted_sha256': 'b3cee52832c76ef74303bb80cdd4cd6ac62240ae6dd76a4335d4fe4f77b71f66',
                           'n_train_chunks': 4900},
                     '4': {'families': ['code', 'csv', 'json', 'log'],
                           'chunks_per_family': 1225,
                           'n_train_rows': 99153,
                           'train_idx_sha256': '1e2715d72d7a0cbcfed172f5c69bd39793a13d5e433778d57958951ea6c213b3',
                           'train_sorted_sha256': '0ff77c1187663ed20483d8c22a6cfaf8a04f11e49414e4337b1898da81e61cd7',
                           'n_train_chunks': 4900},
                     '7': {'families': ['code', 'csv', 'json', 'log', 'mixed', 'gutenberg', 'base64'],
                           'chunks_per_family': 700,
                           'n_train_rows': 99179,
                           'train_idx_sha256': '6221ced168fb6cbf7a5a52375a05d1e71b229d593c4ad9ae33b745ffba8432a7',
                           'train_sorted_sha256': '5005f1ed676441ec1d1a223cb172ebedc403a01c79e67d0e131726bcd1fa5068',
                           'n_train_chunks': 4900}},
            'depth': {'2450': {'families': ['code'],
                               'chunks_per_family': 2450,
                               'n_train_rows': 49404,
                               'train_idx_sha256': '99c54c680d77a9f3987a6a8b10c97075841a160638336ed3e439035dbd330419',
                               'train_sorted_sha256': '9701f4bb4f02a13c808439f301fc32f61e77492886e81394856a1f522e63abe8',
                               'n_train_chunks': 2450},
                      '1225': {'families': ['code'],
                               'chunks_per_family': 1225,
                               'n_train_rows': 24756,
                               'train_idx_sha256': '30a9feee69ad2c81fc67aefab649a0026753e1b303515925742a9e45de38769d',
                               'train_sorted_sha256': 'a94f81ec0dd3b02072012324c5534326dc0d2bf91f7b0f426501331c16596652',
                               'n_train_chunks': 1225},
                      '700': {'families': ['code'],
                              'chunks_per_family': 700,
                              'n_train_rows': 14193,
                              'train_idx_sha256': '7101752816c35496f8a46d1e6dbed1d975f843446783bd93040c962d9bb7a6de',
                              'train_sorted_sha256': '5a6c256fa9d52e454c93b52d52d1d6eb590828639318896cfc2716422b5fe5ac',
                              'n_train_chunks': 700}},
            'pred_k1': {'families': ['base64'],
                        'chunks_per_family': 4900,
                        'n_train_rows': 97797,
                        'train_idx_sha256': '898e252261186184cd372e04c0521618a2476de333820ca18876bdca5a12a230',
                        'train_sorted_sha256': 'db6001d26d18cccaab51e4cf573614517225bb62566833fc137866f0fd639f6d',
                        'n_train_chunks': 4900}},
 'code': {'n_eval_rows': 31850,
          'eval_idx_sha256': '578248b2f2350e7aa5d3f7b2a832ecdb14fbd97d93e4690b7b4ea1e73a504bec',
          'by_k': {'1': {'families': ['csv'],
                         'chunks_per_family': 4900,
                         'n_train_rows': 98014,
                         'train_idx_sha256': '0974848f4c6be567f08eca89abd59195e574bea7f5c6d30d5f354e02a92ad3d8',
                         'train_sorted_sha256': 'eeb08d0cb90bd61b19f936960f067840bd8a33dda278863a4f4d70d08a140066',
                         'n_train_chunks': 4900},
                   '2': {'families': ['csv', 'json'],
                         'chunks_per_family': 2450,
                         'n_train_rows': 98814,
                         'train_idx_sha256': '273d50cf42d75d662f7edc83d42e4e78f13e410655a73b2aa03074d722e41f9a',
                         'train_sorted_sha256': '076ad077ed62239fb66ca465a329a4bd0c0ab9791ea1d199dc209edf5244c7ad',
                         'n_train_chunks': 4900},
                   '4': {'families': ['csv', 'json', 'log', 'mixed'],
                         'chunks_per_family': 1225,
                         'n_train_rows': 99186,
                         'train_idx_sha256': '377721f410a09833cfebe6d3bf551c23438a54dfc9734e7bb810790f34189a34',
                         'train_sorted_sha256': '40ff603c682e531ce87c1130b02e5b7dbc931cccd9358431a686ee650ccb7741',
                         'n_train_chunks': 4900},
                   '7': {'families': ['csv', 'json', 'log', 'mixed', 'gutenberg', 'base64', 'binary'],
                         'chunks_per_family': 700,
                         'n_train_rows': 99138,
                         'train_idx_sha256': '82fb3a4bb0245d925e5ff834f35f2d32a72856e66a8247b1a37e01a0e4c0285e',
                         'train_sorted_sha256': '3eab8ddb9daab873edf69efd2bf9dd7f7e7908909b0016ed04af29e521b8cb10',
                         'n_train_chunks': 4900}},
          'depth': {'2450': {'families': ['csv'],
                             'chunks_per_family': 2450,
                             'n_train_rows': 49342,
                             'train_idx_sha256': 'b3afb883eba6abd247f3ddb2ae7c31f85d3c147681851ff48bf278e28827fb1d',
                             'train_sorted_sha256': 'ee3e778ce359b46cb033e4ae564a81d7fd20f2ffe94cb0e3764f7984d6a0b873',
                             'n_train_chunks': 2450},
                    '1225': {'families': ['csv'],
                             'chunks_per_family': 1225,
                             'n_train_rows': 24747,
                             'train_idx_sha256': '142892aefd3462fa21436e23a9e618637c2b648e633ae1c65ab7a711953c0043',
                             'train_sorted_sha256': '99a28d0da94daa04ff56cb0fe311dda059f71776bc67b25a7146ea2b18f76bc9',
                             'n_train_chunks': 1225},
                    '700': {'families': ['csv'],
                            'chunks_per_family': 700,
                            'n_train_rows': 14108,
                            'train_idx_sha256': '45ac1626dbd3f38a82d01f7b94b14f2ded6c162da766b9bf70ae951ce892a6db',
                            'train_sorted_sha256': 'f4359a1d0959902b3c0ce9cab2f24e58c32bcacf1785a8c809416b6320e1b01a',
                            'n_train_chunks': 700}},
          'pred_k1': {'families': ['binary'],
                      'chunks_per_family': 4900,
                      'n_train_rows': 98161,
                      'train_idx_sha256': 'fdbe4640d1be305d6cb91c4484453fae488192bf2b38503153e47a0eeaf0567a',
                      'train_sorted_sha256': '5ea3f980141929b44118829217844d29fb4c86212b704bfb01c1b7cc1b04235e',
                      'n_train_chunks': 4900}},
 'csv': {'n_eval_rows': 31616,
         'eval_idx_sha256': 'b4ccfb51f5b8b54b2ef856b54af6e79cc7ca6ed62bc0d8cc8a7bfcac09dc5555',
         'by_k': {'1': {'families': ['json'],
                        'chunks_per_family': 4900,
                        'n_train_rows': 98230,
                        'train_idx_sha256': 'f86222b9a341f631276af6dfdcaaba7f9c93d6226d79f6dfca0bfa257110b3ec',
                        'train_sorted_sha256': '198287b668a26f4d32fcd735450b8c87b9c0d16cd0d972cef9c5be84617a43dd',
                        'n_train_chunks': 4900},
                  '2': {'families': ['json', 'log'],
                        'chunks_per_family': 2450,
                        'n_train_rows': 98949,
                        'train_idx_sha256': 'b7fe0d843d91a0d570b99ed366b05fbed5d98037bfa37e3fab2db2f068adeb59',
                        'train_sorted_sha256': 'c429e88ec6bc3b2c3fcb573993ed45633dd7405b00be0bfc8449a5c31eea4ffc',
                        'n_train_chunks': 4900},
                  '4': {'families': ['json', 'log', 'mixed', 'gutenberg'],
                        'chunks_per_family': 1225,
                        'n_train_rows': 99200,
                        'train_idx_sha256': '93af21c1784eb641b73bedb633d7dda057225b818eccfae0242f327803cb626b',
                        'train_sorted_sha256': 'ed36c7f11dd85093c83069e622b68eab9226ac017d3e72772cf5f803041c8745',
                        'n_train_chunks': 4900},
                  '7': {'families': ['json', 'log', 'mixed', 'gutenberg', 'base64', 'binary', 'code'],
                        'chunks_per_family': 700,
                        'n_train_rows': 99223,
                        'train_idx_sha256': '046cb26f8b1dd64a77390cbc52cd90d8f260abd4e2e81b73db8fbc0622e1a98f',
                        'train_sorted_sha256': '85a1db7ce815f7a6b9f4ebf7a5a8e7ed7a8427a7b844dadc5855a89e08655b2b',
                        'n_train_chunks': 4900}},
         'depth': {'2450': {'families': ['json'],
                            'chunks_per_family': 2450,
                            'n_train_rows': 49472,
                            'train_idx_sha256': '4c83372481e380ea447ad56bc6ee491523d82e7dae9a9612f8fa9dc16f9cb6fb',
                            'train_sorted_sha256': '0ac0a6e3884684569c905a818772eb4019844b3f129dc36e29c292e2c17d2fe8',
                            'n_train_chunks': 2450},
                   '1225': {'families': ['json'],
                            'chunks_per_family': 1225,
                            'n_train_rows': 24830,
                            'train_idx_sha256': '2f1aa613a9e03023a058a8559be80cf6603ebd7937781631cfb4005a5206d016',
                            'train_sorted_sha256': 'bbddb776eff3bb61c21da2e2ea69603cafbbfd6d7268a299c1fc174ae5eb6cff',
                            'n_train_chunks': 1225},
                   '700': {'families': ['json'],
                           'chunks_per_family': 700,
                           'n_train_rows': 14212,
                           'train_idx_sha256': '89ae26ece37013533106da66ca1815104e9e5b5f3e3b5be757b7a5761e94d92c',
                           'train_sorted_sha256': 'bc21816dfd1ed9455366a837a06164fc69883504b89747fec2759524c4b55a57',
                           'n_train_chunks': 700}},
         'pred_k1': {'families': ['code'],
                     'chunks_per_family': 4900,
                     'n_train_rows': 97972,
                     'train_idx_sha256': 'e77ce52541fe772f5ff448502e62323b38f50dc186376cd0da5bf47ebeda9317',
                     'train_sorted_sha256': '1020cab547322aab5c051814cc9871f9491672530eef68adef11ab2058ef130c',
                     'n_train_chunks': 4900}},
 'json': {'n_eval_rows': 32760,
          'eval_idx_sha256': '8eacb2d465c04006d1dbfd1452653d2cb4eab3a9ca633b1301b0b0064a17aaa4',
          'by_k': {'1': {'families': ['log'],
                         'chunks_per_family': 4900,
                         'n_train_rows': 98196,
                         'train_idx_sha256': '92d5f3d9cdce4b16a9954e25c719a07eb2d3d11f3b69141b659a34364525b91d',
                         'train_sorted_sha256': '5ffae736f58b10a6ecbbb6dc8ea0b2cdaf49ecf1bf3912d59420f33de5b90e5e',
                         'n_train_chunks': 4900},
                   '2': {'families': ['log', 'mixed'],
                         'chunks_per_family': 2450,
                         'n_train_rows': 98861,
                         'train_idx_sha256': 'd188ab2fe88da8f303c2160b33a82269865b4e7cd7da40e6cf248286de7e9fa3',
                         'train_sorted_sha256': '4c2111ea4b1fb8ad473c7135eba3786e90b29e8d37387534f64c217a91e5fe86',
                         'n_train_chunks': 4900},
                   '4': {'families': ['log', 'mixed', 'gutenberg', 'base64'],
                         'chunks_per_family': 1225,
                         'n_train_rows': 99048,
                         'train_idx_sha256': '0c3e961fab35618ec371cc3f9bdfe41327db60ed9a241aed14c60bd7d8210451',
                         'train_sorted_sha256': '77507fc24d3adbe4944af7dea3e5363094c389e5765aa104930de44621e8db6e',
                         'n_train_chunks': 4900},
                   '7': {'families': ['log', 'mixed', 'gutenberg', 'base64', 'binary', 'code', 'csv'],
                         'chunks_per_family': 700,
                         'n_train_rows': 99119,
                         'train_idx_sha256': '487faedac353a291894417ba1c721feff93df26f2f7d2eb83e91ece068e0c89c',
                         'train_sorted_sha256': 'c3367143e029000db4c0ac6787fc5709b705d34af55316019f0c9e1e8611683b',
                         'n_train_chunks': 4900}},
          'depth': {'2450': {'families': ['log'],
                             'chunks_per_family': 2450,
                             'n_train_rows': 49477,
                             'train_idx_sha256': 'ba49a90c0956866e3a1fbd329700cdad26ab7cac410032c798043b5e03fab245',
                             'train_sorted_sha256': '3a21b0a9bc3ba6ade18c9cf7d1b5365e252422d86baa07f03ce43c5f2eea5835',
                             'n_train_chunks': 2450},
                    '1225': {'families': ['log'],
                             'chunks_per_family': 1225,
                             'n_train_rows': 24820,
                             'train_idx_sha256': '43927c734774d9f9d2da317c2dd92a5926fb3970936e288bc5bd626eb595d785',
                             'train_sorted_sha256': '073c7c6d8098dfd24ba665c5177c8daba565ad474bdf3edcd8e54086cd83ada2',
                             'n_train_chunks': 1225},
                    '700': {'families': ['log'],
                            'chunks_per_family': 700,
                            'n_train_rows': 14184,
                            'train_idx_sha256': 'ccb7ef7c17bcaadc47f99e49534570ff0faac03021b2a1db807efa1c02e564b6',
                            'train_sorted_sha256': '5f66f5048e02d1a69158317f3950a47d74a74a7f20b967fa82085e5540ba9721',
                            'n_train_chunks': 700}},
          'pred_k1': {'families': ['csv'],
                      'chunks_per_family': 4900,
                      'n_train_rows': 98014,
                      'train_idx_sha256': '0974848f4c6be567f08eca89abd59195e574bea7f5c6d30d5f354e02a92ad3d8',
                      'train_sorted_sha256': 'eeb08d0cb90bd61b19f936960f067840bd8a33dda278863a4f4d70d08a140066',
                      'n_train_chunks': 4900}},
 'log': {'n_eval_rows': 33254,
         'eval_idx_sha256': '1dab3cc04aa0ae442fc9cab1dd0f0cafd5b1b2e0cf3de25341ab39d8752e1d8b',
         'by_k': {'1': {'families': ['mixed'],
                        'chunks_per_family': 4900,
                        'n_train_rows': 98225,
                        'train_idx_sha256': 'd2659b4480017fedd17a67ba1540fd5a3cc5bc02a75626dbcb9a2739bdffc344',
                        'train_sorted_sha256': '535fd1dff1587ff8904102743929b6eb81742ab94a9db58add52dadbe2f1b803',
                        'n_train_chunks': 4900},
                  '2': {'families': ['mixed', 'gutenberg'],
                        'chunks_per_family': 2450,
                        'n_train_rows': 98794,
                        'train_idx_sha256': 'a599d8c06f109f0b52430161d3e53065a9ab705bc1c7890d115b8a5f300eee63',
                        'train_sorted_sha256': 'a12c20347cb917500ebd419fb3b30c31a714936612e5eb7130153bff5423bb93',
                        'n_train_chunks': 4900},
                  '4': {'families': ['mixed', 'gutenberg', 'base64', 'binary'],
                        'chunks_per_family': 1225,
                        'n_train_rows': 99020,
                        'train_idx_sha256': '9ec478edab285c410570ada805ee0ad7a2fa7e92e75cfb703d8ed62da24c9a76',
                        'train_sorted_sha256': '3394fb5f1f89dfc205c0878815df2377d5706065f966ec59507134b6d96aed0f',
                        'n_train_chunks': 4900},
                  '7': {'families': ['mixed', 'gutenberg', 'base64', 'binary', 'code', 'csv', 'json'],
                        'chunks_per_family': 700,
                        'n_train_rows': 99147,
                        'train_idx_sha256': '18a7948b4526092c76659cf594965ca95433b88e39631079671c79cb19c3a473',
                        'train_sorted_sha256': 'b270c048b7dd318a750b75ef916a4b504ac5d3d24bc6e35ce0c9c3310f7490dd',
                        'n_train_chunks': 4900}},
         'depth': {'2450': {'families': ['mixed'],
                            'chunks_per_family': 2450,
                            'n_train_rows': 49384,
                            'train_idx_sha256': '5e1b6495fe869f556ed8af68d5c110365a960dce39d2fc4c4a9608cfdc4c549f',
                            'train_sorted_sha256': 'ef726b41ed69cab7901edfd00502291e5fa2ceb9e3e831303423d97016a441d0',
                            'n_train_chunks': 2450},
                   '1225': {'families': ['mixed'],
                            'chunks_per_family': 1225,
                            'n_train_rows': 24789,
                            'train_idx_sha256': '321cf749bc2417ed826747dc11713eedba4df4331188a9393f22a400f7f7d81c',
                            'train_sorted_sha256': '7e85ebd2ba381d0baa7f40d4b2bd14f6a5f38508a6f0cb5f89716d549333d19f',
                            'n_train_chunks': 1225},
                   '700': {'families': ['mixed'],
                           'chunks_per_family': 700,
                           'n_train_rows': 14209,
                           'train_idx_sha256': 'b055508c1d6c0868f77a0b544fd026f936ae6a19fb4d4be6ec23414fb7f40c7f',
                           'train_sorted_sha256': '0a79db10144307c3a475fbbdf2d313ac7fc45b0dbc77eb24e4ed177b4f6fe3ba',
                           'n_train_chunks': 700}},
         'pred_k1': {'families': ['json'],
                     'chunks_per_family': 4900,
                     'n_train_rows': 98230,
                     'train_idx_sha256': 'f86222b9a341f631276af6dfdcaaba7f9c93d6226d79f6dfca0bfa257110b3ec',
                     'train_sorted_sha256': '198287b668a26f4d32fcd735450b8c87b9c0d16cd0d972cef9c5be84617a43dd',
                     'n_train_chunks': 4900}},
 'mixed': {'n_eval_rows': 32188,
           'eval_idx_sha256': '3749067dd47d4a788ada22122dcf43c159d462ba5ade7904398735bdf94a80f1',
           'by_k': {'1': {'families': ['gutenberg'],
                          'chunks_per_family': 4900,
                          'n_train_rows': 98209,
                          'train_idx_sha256': '8bf3783cf12d4511b1fd5845d2f57900cef929861c26c0b7e9aee03db9b32055',
                          'train_sorted_sha256': '2dca00111af073547d6cc9ee84365ff095345a793fc74b9fefa178b10a5014d3',
                          'n_train_chunks': 4900},
                    '2': {'families': ['gutenberg', 'base64'],
                          'chunks_per_family': 2450,
                          'n_train_rows': 98516,
                          'train_idx_sha256': 'd6014d267641f1611fcab38d939f721d441c4202778ffcc3f6861b577e245c54',
                          'train_sorted_sha256': '8eb74f99f4172f3345a2c6937227bf3cebe9ebfe39aa2ca7f434fa881092505c',
                          'n_train_chunks': 4900},
                    '4': {'families': ['gutenberg', 'base64', 'binary', 'code'],
                          'chunks_per_family': 1225,
                          'n_train_rows': 98987,
                          'train_idx_sha256': '1eef594e14acb635693506aa5e7ab3761c754fd27ffefb2bfb1077fa1fb87ee6',
                          'train_sorted_sha256': '28d56593117062a9936d30c04e53f4798a3ff92e8473735fd9d7e6da7e16ff47',
                          'n_train_chunks': 4900},
                    '7': {'families': ['gutenberg', 'base64', 'binary', 'code', 'csv', 'json', 'log'],
                          'chunks_per_family': 700,
                          'n_train_rows': 99122,
                          'train_idx_sha256': '94089fd7055c2e7f19c01680906cfcf98db0967b31c15fd1fb9467e0b60fd161',
                          'train_sorted_sha256': 'f55d87fbf4c32f213cdf5b0f147ebfa0c4652b566b3c07113965a6c770605d2b',
                          'n_train_chunks': 4900}},
           'depth': {'2450': {'families': ['gutenberg'],
                              'chunks_per_family': 2450,
                              'n_train_rows': 49410,
                              'train_idx_sha256': 'b01f3e33e64c833bbf47f5c7befcd6880a2fad58f6bca4738286e1fe10461783',
                              'train_sorted_sha256': '79b69e97da4611065c157984838781eafb5fa9f21f59a24f98840e9d890d00db',
                              'n_train_chunks': 2450},
                     '1225': {'families': ['gutenberg'],
                              'chunks_per_family': 1225,
                              'n_train_rows': 24761,
                              'train_idx_sha256': '192f5403fc896d5b7c84e2a2924003b6a761d89c1aeb8d6f6702e5900292cff5',
                              'train_sorted_sha256': 'b04af3f7756524a73cc17d190f0e23a41cf3343fd199de6d9ae1ec05c29ed6a4',
                              'n_train_chunks': 1225},
                     '700': {'families': ['gutenberg'],
                             'chunks_per_family': 700,
                             'n_train_rows': 14105,
                             'train_idx_sha256': '1033d20ae45ed779dc777f42f9d57da27243e9b671b2622216c79fc6de900686',
                             'train_sorted_sha256': 'c17b62c2907718198e7ce27cf51678464288b57e91504489bdd0b7182db73985',
                             'n_train_chunks': 700}},
           'pred_k1': {'families': ['log'],
                       'chunks_per_family': 4900,
                       'n_train_rows': 98196,
                       'train_idx_sha256': '92d5f3d9cdce4b16a9954e25c719a07eb2d3d11f3b69141b659a34364525b91d',
                       'train_sorted_sha256': '5ffae736f58b10a6ecbbb6dc8ea0b2cdaf49ecf1bf3912d59420f33de5b90e5e',
                       'n_train_chunks': 4900}}}
# The reproduction anchor: 0003's 100000-row rung (artifacts/pivot/deflate_curve.json rungs[2].accuracy),
# the incumbent M1 on the FIRST 100000 pool rows with its last 10% as the early-stopping validation
# split — the same rows and the same convention as 0003's ladder; 0011 banked the same 0.1965 on the
# identical rows (transfer_model_top1_on_reference_eval). 0014 reproduced the 800000-row rung exactly
# under this machinery, and the pre-freeze check reproduced this one exactly (engineering log 0016).
RUNG_100K_TOP1, REPRODUCTION_TOLERANCE = 0.1965, 0.005
BAR_SLOPE_PER_DOUBLING = 0.005
NULL_TOLERANCE, CHANCE = 0.02, 0.038462
# Informational drift references beside the null reading: 0014's null on the same block and shuffle,
# and 0003's banked null. The clause is chance + NULL_TOLERANCE.
NULL_0014_SAME_BLOCK, NULL_0003_BANKED = 0.0383, 0.0389
# 0015's leave-one-family-out mixtures at about 5000 chunks (about 700000 rows) per fold
# (artifacts/pivot/lofo_4096.json): the reference for the row axis under transfer, informational only.
REFERENCE_0015 = {"model_mixture_top1": 0.0859, "logistic_mixture_top1": 0.0928, "majority_mixture_top1": 0.0385,
                  "rows_per_fold_about": 700000, "chunks_per_family_about": 5000}
ENV = {"threads": 3, "nice": 10, "sklearn": "1.9.0", "numpy": "2.4.6"}
SEED = 20260825
ROLES = ["majority", "logistic", "model"]
SLOPE_AGREEMENT = 1e-6   # the runner's banked slope must agree with this reader's to this; the reader's is the verdict's


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_obj(obj) -> str:
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def ols_slope(xs, ys):
    xb = sum(xs) / len(xs); yb = sum(ys) / len(ys)
    sxx = sum((x - xb) ** 2 for x in xs)
    return sum((x - xb) * (y - yb) for x, y in zip(xs, ys)) / sxx


def following_families(f, k):
    i = FAMILIES.index(f)
    return [FAMILIES[(i + j) % len(FAMILIES)] for j in range(1, k + 1)]


def preceding_family(f):
    return FAMILIES[(FAMILIES.index(f) - 1) % len(FAMILIES)]


def main() -> int:
    if not os.path.exists(ARTIFACT):
        if os.path.exists(NOT_RUN):
            try:
                nr = json.load(open(NOT_RUN, encoding="utf-8"))
                print(f"READER 0016: NOT RUN — {nr.get('reason')!r} (stage {nr.get('stage')}, filed "
                      f"{nr.get('utc')}, {nr.get('n_checkpoints')} checkpoints). A NOT RUN is not a verdict.",
                      file=sys.stderr)
            except Exception:  # noqa: BLE001
                print("READER 0016: NOT RUN file present but unreadable.", file=sys.stderr)
            return 2
        print(f"READER 0016: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0016: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
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

    # ---- sealed sets, the subset rule recomputed, leakage
    part = g("partition") or {}
    for k, v in PARTITION.items():
        expect_eq(void, part.get(k), v, f"sealed set: partition.{k}")
    pfolds = part.get("folds") or {}

    def fold_specs(f):
        """(label, sealed block, chosen families, chunks per family) for every fold of held-out family f."""
        out = []
        for kk in KS:
            out.append((f"fold {f} k={kk}", FOLDS[f]["by_k"][str(kk)], following_families(f, kk), BUDGET_CHUNKS // kk, ("by_k", str(kk))))
        for n in DEPTH_CHUNKS[1:]:
            out.append((f"depth {f} c={n}", FOLDS[f]["depth"][str(n)], following_families(f, 1), n, ("depth", str(n))))
        out.append((f"pred {f} k=1", FOLDS[f]["pred_k1"], [preceding_family(f)], BUDGET_CHUNKS, ("pred_k1", None)))
        return out

    def banked_block(pf, where):
        sec, key = where
        b = pf.get(sec)
        if key is not None:
            b = (b or {}).get(key)
        return b or {}

    for f in FAMILIES:
        pf = pfolds.get(f) or {}
        for k in ("n_eval_rows", "eval_idx_sha256"):
            expect_eq(void, pf.get(k), FOLDS[f][k], f"sealed set: fold {f}.{k}")
        for label, sealed, chosen, per, where in fold_specs(f):
            pk = banked_block(pf, where)
            for k, v in sealed.items():
                expect_eq(void, pk.get(k), v, f"sealed set: {label}.{k}")
            for k in ("train_rows_of_heldout_family", "train_rows_outside_chosen_families",
                      "train_chunks_shared_with_eval", "train_rows_in_eval"):
                if pk.get(k) != 0:
                    void.append(f"leakage: {label}.{k}={pk.get(k)!r}, must be 0")
            # the subset rule, recomputed from the family order, against the banked per-family maps
            if pk.get("families") != chosen or pk.get("chunks_per_family") != per:
                void.append(f"subset rule: {label} banked families {pk.get('families')!r} at {pk.get('chunks_per_family')!r} "
                            f"chunks each; the rule says {chosen!r} at {per}")
            cm = pk.get("train_chunks_per_family") or {}; rm = pk.get("train_rows_per_family") or {}
            want = {c: (per if c in chosen else 0) for c in FAMILIES}
            if {c: cm.get(c) for c in FAMILIES} != want:
                void.append(f"subset rule: {label} per-family chunk counts {cm!r} are not {want!r}")
            if any((rm.get(c) or 0) != 0 for c in FAMILIES if c not in chosen) or any((rm.get(c) or 0) <= 0 for c in chosen) \
                    or sum(rm.get(c) or 0 for c in FAMILIES) != sealed["n_train_rows"]:
                void.append(f"subset rule: {label} per-family row counts {rm!r} do not sum to the sealed rows over the chosen families")
    if g("complete") is not True:
        void.append(f"complete: complete={g('complete')!r}; missing {g('missing_roles')!r}")
    if g("null_rows") != PROTOCOL["null_rows"]:
        void.append(f"null control: null_rows={g('null_rows')!r}")

    # ---- scores file, ledger
    scores, chunk_ids = {}, None
    n_eval = PARTITION["n_eval_rows"]
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
    if not isinstance(chunk_ids, list) or len(chunk_ids) != n_eval:
        void.append(f"scores: eval_chunk_ids missing or not {n_eval} long"); chunk_ids = None
    ledger = g("ledger") or []

    def good_vec(v):
        return isinstance(v, str) and len(v) == n_eval and set(v) <= {"0", "1"}

    def check_record(name, rec, role, rows_sha, sorted_sha, n_rows, key, stage):
        """rows_sha None: the unsorted index hash is not sealed for this record (the null block); the sorted one is."""
        if not isinstance(rec, dict) or rec.get("status") != "fit":
            void.append(f"fit: {name} status {(rec or {}).get('status')!r}; must be 'fit'"); return
        if num(rec.get("top1")) is None or num(rec.get("top1_non_gutenberg")) is None or \
                not isinstance(rec.get("per_family"), dict) or len(rec["per_family"]) != 8 or \
                any(num(v) is None for v in rec["per_family"].values()):
            void.append(f"fit: {name} scores are not all finite")
        if rec.get("id") != RECIPES[role]["id"] or rec.get("params_sha256") != RECIPE_SHA256[role]:
            void.append(f"fit: {name} is not 0003's {role} recipe (id {rec.get('id')!r}, params hash off-recipe)")
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
        if key is not None and not good_vec(scores.get(key)):
            void.append(f"fit: {name} per-example vector missing, not {n_eval} characters, or not all '0'/'1'")

    # ---- the reproduction and the null control
    rep = g("reproduction") or {}
    inc = rep.get("model_100k") or {}
    check_record("repro_100k", inc, "model", PARTITION["repro_idx_sha256"], PARTITION["repro_sorted_sha256"],
                 PARTITION["repro_rows"], "repro_100k", "reproduction")
    if num(g("incumbent_100k_refit_top1")) != num(inc.get("top1")):
        void.append("reproduction: the banked refit accuracy is not the record's")
    # tolerance compared at the 4-decimal precision the accuracies are banked at, so the written <= 0.005 holds
    # at the boundary in both directions (0.2015 passes, 0.2016 fails; float subtraction alone is asymmetric there)
    if num(inc.get("top1")) is None or round(abs(num(inc.get("top1")) - RUNG_100K_TOP1), 6) > REPRODUCTION_TOLERANCE:
        void.append(f"reproduction: the incumbent on 0003's 100000-row rung scores {inc.get('top1')!r} against 0003's "
                    f"banked {RUNG_100K_TOP1}; the pool order or the machinery is not 0003's")
    nc = g("null_control") or {}
    check_record("null", nc, "model", None, PARTITION["null_sorted_sha256"], PROTOCOL["null_rows"], None, "null")
    if nc.get("head") != "null":
        void.append("null control: the null record is not the null-stage fit")
    if num(g("shuffled_label_accuracy")) is None or num(g("shuffled_label_accuracy")) != num(nc.get("top1")):
        void.append("null control: shuffled_label_accuracy missing, not finite, or not the record's")
    elif num(g("shuffled_label_accuracy")) > CHANCE + NULL_TOLERANCE:
        void.append(f"null control: shuffled labels reached {g('shuffled_label_accuracy')}, above chance {CHANCE} + "
                    f"{NULL_TOLERANCE} — the pipeline leaks")

    # ---- the folds
    folds = g("folds") or {}
    fold_records = {}   # name -> record, for the mixture clause
    for f in FAMILIES:
        fd = folds.get(f) or {}
        for label, sealed, chosen, per, where in fold_specs(f):
            sec, key = where
            recs = fd.get(sec) or {}
            if key is not None:
                recs = recs.get(key) or {}
            if sec == "by_k":
                nm = lambda r, key=key: f"fold_{f}_k{key}_{r}"; stage = f"fdc:{f}:k{key}"  # noqa: E731
            elif sec == "depth":
                nm = lambda r, key=key: f"depth_{f}_c{key}_{r}"; stage = f"depth:{f}:c{key}"  # noqa: E731
            else:
                nm = lambda r: f"pred_{f}_k1_{r}"; stage = f"pred:{f}:k1"  # noqa: E731
            for r in ROLES:
                name = nm(r)
                check_record(name, recs.get(r), r, sealed["train_idx_sha256"], sealed["train_sorted_sha256"],
                             sealed["n_train_rows"], name, stage)
                fold_records[name] = recs.get(r) or {}
    env = g("environment") or {}
    for k, v in ENV.items():
        if env.get(k) != v:
            void.append(f"environment: {k}={env.get(k)!r}, banked {v!r}")

    # ---- the mixtures, the curve and the arms, re-derived from the per-example vectors and the banked chunk ids
    fdc = g("fdc") or {}

    def _ints(v, n):
        return isinstance(v, list) and len(v) == n and all(isinstance(x, int) and not isinstance(x, bool) for x in v)

    if chunk_ids is not None and not _ints(chunk_ids, n_eval):
        void.append("scores: eval_chunk_ids contains a non-integer entry"); chunk_ids = None
    mean = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
    r6 = lambda a, b: round(a - b, 6) if a is not None and b is not None else None  # noqa: E731
    reader_slope = None
    if chunk_ids is not None and not any(m.startswith("fit:") or m.startswith("scores:") for m in void):
        fam_e = [FAMILIES[int(c) % 8] for c in chunk_ids]
        rows_of = {f: [i for i in range(n_eval) if fam_e[i] == f] for f in FAMILIES}
        non_g = [i for i in range(n_eval) if fam_e[i] != "gutenberg"]
        struct = [i for i in range(n_eval) if fam_e[i] in STRUCTURED]

        def stitched(vec_of_family, label, banked, vec_key):
            """Recompute one stitched mixture, compare with the banked block and the banked stitched vector; return mixture_top1."""
            mix = [0] * n_eval
            for f in FAMILIES:
                v = scores.get(vec_of_family(f))
                for i in rows_of[f]:
                    mix[i] = 1 if v[i] == "1" else 0
            rec_mix = {"mixture_top1": mean(mix), "mixture_top1_non_gutenberg": mean([mix[i] for i in non_g]),
                       "structured_four_top1": mean([mix[i] for i in struct]),
                       "per_family": {f: mean([mix[i] for i in rows_of[f]]) for f in FAMILIES}}
            for k, v in rec_mix.items():
                if (banked or {}).get(k) != v:
                    void.append(f"mixture: {label}.{k}={(banked or {}).get(k)!r} is not the reader's recomputation {v!r}")
            if vec_key is not None:
                mv = scores.get(vec_key)
                if not good_vec(mv) or [1 if c == "1" else 0 for c in mv] != mix:
                    void.append(f"mixture: the banked stitched vector {vec_key} is not the stitched one")
            for f in FAMILIES:
                # the fold's own banked per-family accuracy for its held-out family must be the mixture's
                fr = (fold_records.get(vec_of_family(f)) or {}).get("per_family") or {}
                if num(fr.get(f)) != rec_mix["per_family"][f]:
                    void.append(f"mixture: {label}: fold {vec_of_family(f)} banked {fr.get(f)!r} on its held-out family, "
                                f"recomputed {rec_mix['per_family'][f]!r}")
            return rec_mix["mixture_top1"]

        for r in ROLES:
            bc = fdc.get(r) or {}
            by_k = bc.get("by_k") or {}
            ys = [stitched(lambda f, kk=kk, r=r: f"fold_{f}_k{kk}_{r}", f"fdc.{r}.by_k.{kk}", by_k.get(str(kk)),
                           f"fdc_mixture_k{kk}_{r}") for kk in KS]
            depth = bc.get("depth") or {}; dby = depth.get("by_chunks") or {}
            dys = [ys[0]]
            # the depth arm's budget point is the k = 1 fold's mixture, restated
            if (dby.get(str(BUDGET_CHUNKS)) or {}).get("mixture_top1") != ys[0]:
                void.append(f"depth: fdc.{r}.depth.by_chunks.{BUDGET_CHUNKS} is not the k=1 mixture {ys[0]!r}")
            for n in DEPTH_CHUNKS[1:]:
                dys.append(stitched(lambda f, n=n, r=r: f"depth_{f}_c{n}_{r}", f"fdc.{r}.depth.by_chunks.{n}", dby.get(str(n)),
                                    f"depth_mixture_c{n}_{r}"))
            pred_m = stitched(lambda f, r=r: f"pred_{f}_k1_{r}", f"fdc.{r}.pred_k1", bc.get("pred_k1"), f"pred_mixture_k1_{r}")
            # the curve: ordinates, slope, end difference, and the arms' derived readings, all from 4-decimal mixtures
            if bc.get("mixture_top1_by_k") != ys:
                void.append(f"curve: fdc.{r}.mixture_top1_by_k={bc.get('mixture_top1_by_k')!r} is not {ys!r}")
            if bc.get("family_counts") != KS or bc.get("log2_family_counts") != LOG2K:
                void.append(f"curve: fdc.{r} abscissae are not the sealed family counts")
            if depth.get("chunks") != DEPTH_CHUNKS or depth.get("mixture_top1_by_chunks") != dys:
                void.append(f"depth: fdc.{r}.depth sizes or ordinates are not the sealed sizes and the recomputed mixtures {dys!r}")
            if None not in ys:
                slope = round(ols_slope(LOG2K, ys), 6)
                if r == "model":
                    reader_slope = slope
                if num(bc.get("slope_per_doubling")) is None or abs(num(bc.get("slope_per_doubling")) - slope) > SLOPE_AGREEMENT:
                    void.append(f"curve: fdc.{r}.slope_per_doubling={bc.get('slope_per_doubling')!r}, recomputed {slope!r}")
                if num(bc.get("end_difference")) != r6(ys[-1], ys[0]):
                    void.append(f"curve: fdc.{r}.end_difference={bc.get('end_difference')!r}, recomputed {r6(ys[-1], ys[0])!r}")
            if None not in dys:
                if num(depth.get("row_effect_within_family")) != r6(dys[0], dys[-1]):
                    void.append(f"depth: fdc.{r}.depth.row_effect_within_family is not {r6(dys[0], dys[-1])!r}")
                want = round((dys[0] - dys[-1]) / math.log2(DEPTH_CHUNKS[0] / DEPTH_CHUNKS[-1]), 6)
                if num(depth.get("row_effect_per_doubling_of_chunks")) != want:
                    void.append(f"depth: fdc.{r}.depth.row_effect_per_doubling_of_chunks is not {want!r}")
                fe = bc.get("family_effect_at_matched_depth") or {}
                for i, kk in enumerate(KS[1:], start=1):
                    want = r6(ys[i], dys[i])
                    if num(fe.get(str(kk))) != want:
                        void.append(f"arms: fdc.{r}.family_effect_at_matched_depth.{kk}={fe.get(str(kk))!r} is not {want!r}")
            if num(bc.get("composition_spread_k1")) != r6(ys[0], pred_m):
                void.append(f"arms: fdc.{r}.composition_spread_k1 is not {r6(ys[0], pred_m)!r}")
    model_curve = fdc.get("model") or {}; logi_curve = fdc.get("logistic") or {}
    model_slope = num(g("fdc_slope_per_doubling"))
    if model_slope is None or model_slope != num(model_curve.get("slope_per_doubling")):
        void.append("curve: fdc_slope_per_doubling missing, not finite, or not the model role's slope")
    if g("fdc_mixture_top1_by_k") != model_curve.get("mixture_top1_by_k") or \
            num(g("fdc_end_difference")) != num(model_curve.get("end_difference")):
        void.append("curve: the headline ordinates or end difference are not the model role's")
    logi_slope = num(logi_curve.get("slope_per_doubling"))
    if model_slope is not None and logi_slope is not None and \
            num(g("fdc_slope_model_minus_logistic")) != round(model_slope - logi_slope, 6):
        void.append("curve: fdc_slope_model_minus_logistic is not model minus logistic")
    if not void and reader_slope is None:
        void.append("curve: the reader could not recompute the model's slope")

    # ---- the one clause, on the reader's own slope
    fails: list[str] = []
    if not void:
        if reader_slope < BAR_SLOPE_PER_DOUBLING - 1e-9:
            fails.append(f"diversity: the model's fixed-budget mixture slope {reader_slope} per doubling of families is below "
                         f"{BAR_SLOPE_PER_DOUBLING}")

    if void:
        verdict, meaning = "VOID", ("A validity or control clause fails, or the artifact is incomplete. This run says "
                                    "nothing about family diversity in either direction.")
    elif fails:
        verdict, meaning = "DIVERSITY_FLAT", (
            f"At a fixed plaintext budget of {BUDGET_CHUNKS} source chunks, spreading the training data over more content "
            f"families does not raise 0003's M1 recipe's accuracy on a family it never saw by {BAR_SLOPE_PER_DOUBLING} per "
            "doubling of families. More content types of the kind this corpus has are not, at this budget and rate, what "
            "would fix 0015's transfer failure for this recipe. A statement about the corpus builder's eight families at "
            "4096 bytes; nothing here establishes a buyer.")
    else:
        verdict, meaning = "DIVERSITY_HELPS", (
            f"At a fixed plaintext budget of {BUDGET_CHUNKS} source chunks, spreading the training data over more content "
            f"families raises 0003's M1 recipe's accuracy on a family it never saw by at least {BAR_SLOPE_PER_DOUBLING} per "
            "doubling of families: content diversity, not only volume, moves transfer for this recipe. A statement about "
            "the corpus builder's eight families at 4096 bytes; nothing here establishes a buyer, and nothing here revises "
            "0015's TRANSFER_FAILS.")

    mk7 = None
    if verdict != "VOID":
        ys = model_curve.get("mixture_top1_by_k") or []
        mk7 = ys[-1] if ys else None
    dm = model_curve.get("depth") or {}
    result = {
        "schema": "raise-v1/fdc_4096_verdict/1",
        "preregistration": PREREG, "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "verdict": verdict, "meaning": meaning,
        "validity_failed_clauses": void, "diversity_failed_clauses": fails,
        "bar_applied": {"slope_per_doubling_must_reach": BAR_SLOPE_PER_DOUBLING, "family_counts": KS,
                        "log2_family_counts": LOG2K, "budget_chunks": BUDGET_CHUNKS, "verdict_is_about": "0003's M1 recipe"},
        "fdc_slope_per_doubling": reader_slope if reader_slope is not None else model_slope,
        "fdc_slope_per_doubling_banked_by_runner": model_slope,
        "fdc_mixture_top1_by_k": g("fdc_mixture_top1_by_k"),
        "fdc_end_difference": num(g("fdc_end_difference")),
        "fdc_slope_per_doubling_logistic": logi_slope,
        "fdc_mixture_top1_by_k_logistic": logi_curve.get("mixture_top1_by_k"),
        "fdc_mixture_top1_by_k_majority": (fdc.get("majority") or {}).get("mixture_top1_by_k"),
        "fdc_slope_model_minus_logistic": num(g("fdc_slope_model_minus_logistic")),
        "structured_four_by_k_model": model_curve.get("structured_four_by_k"),
        "per_family_by_k_model": model_curve.get("per_family_by_k"),
        "depth_mixture_top1_by_chunks_model": dm.get("mixture_top1_by_chunks"),
        "depth_chunks": DEPTH_CHUNKS,
        "row_effect_within_family_model": num(dm.get("row_effect_within_family")),
        "row_effect_per_doubling_of_chunks_model": num(dm.get("row_effect_per_doubling_of_chunks")),
        "family_effect_at_matched_depth_model": model_curve.get("family_effect_at_matched_depth"),
        "composition_spread_k1_model": num(model_curve.get("composition_spread_k1")),
        "pred_k1_mixture_top1_model": num((model_curve.get("pred_k1") or {}).get("mixture_top1")),
        "depth_mixture_top1_by_chunks_logistic": (logi_curve.get("depth") or {}).get("mixture_top1_by_chunks"),
        "family_effect_at_matched_depth_logistic": logi_curve.get("family_effect_at_matched_depth"),
        "composition_spread_k1_logistic": num(logi_curve.get("composition_spread_k1")),
        "reference_0015": REFERENCE_0015,
        "k7_at_budget_minus_0015_k7_at_full_rows": (round(mk7 - REFERENCE_0015["model_mixture_top1"], 6)
                                                     if num(mk7) is not None else None),
        "incumbent_100k_reproduction_drift": (round(num(inc.get("top1")) - RUNG_100K_TOP1, 6)
                                              if num(inc.get("top1")) is not None else None),
        "null_drift_from_0014_same_block": (round(num(nc.get("top1")) - NULL_0014_SAME_BLOCK, 6)
                                            if num(nc.get("top1")) is not None else None),
        "null_drift_from_0003_banked": (round(num(nc.get("top1")) - NULL_0003_BANKED, 6)
                                        if num(nc.get("top1")) is not None else None),
        "informational_only": "the logistic and majority curves, the end differences, the depth and predecessor arms and every "
                              "reading derived from them, the per-family and structured-four readings, the comparison against "
                              "0015's full-row mixture, the reproduction and null drifts and the artifact's cluster intervals are "
                              "informational: not a verdict, not quotable as a pass. The verdict is the `verdict` field.",
        "establishes_a_buyer": False, "revises_0003_0014_0015": False,
        "read": {k: g(k) for k in (
            "preregistration", "smoke", "stage", "complete", "missing_roles", "fdc_slope_per_doubling",
            "fdc_mixture_top1_by_k", "fdc_end_difference", "fdc_slope_model_minus_logistic",
            "incumbent_100k_refit_top1", "shuffled_label_accuracy", "chance_accuracy", "null_rows", "n_classes")},
        "fdc": fdc,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("READER 0016 — family-diversity transfer curve at 4096")
    for k, v in result["read"].items():
        print(f"  {k:<36} {v}")
    for r in ROLES:
        c = fdc.get(r) or {}
        print(f"  fdc.{r:<31} by_k {c.get('mixture_top1_by_k')} slope/doubling {c.get('slope_per_doubling')} depth "
              f"{(c.get('depth') or {}).get('mixture_top1_by_chunks')} pred_k1 {(c.get('pred_k1') or {}).get('mixture_top1')}")
    if void:
        print(f"\n  VALIDITY FAILED CLAUSES ({len(void)}):")
        for f in void:
            print(f"    · {f}")
    if fails:
        print(f"\n  DIVERSITY FAILED CLAUSES ({len(fails)}):")
        for f in fails:
            print(f"    · {f}")
    print(f"\n  VERDICT: {verdict}")
    print(f"  {meaning}")
    print("  This does not establish a buyer, and was never capable of doing so.")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
