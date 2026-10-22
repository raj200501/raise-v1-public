#!/usr/bin/env python3
"""Bank the design numbers of the 0026 design brief (docs/strategy/0026_DESIGN_BRIEF.md).

0026 is neither written nor frozen: it is a design brief for the preregistration that follows 0025's run. The brief
quotes numbers that were computed from banked vectors but were never banked. OPERATING_RULES 2 says a number goes in a
document only if a banked artifact holds it, so this script recomputes every one of them from banked artifacts with
the repository's own functions and writes artifacts/pivot/design_0026_numbers.json:

  numbers    the brief's computed readings: the reader positive control (0024's slope and lead, recomputed), the rung
             and fold sizes derived from the corpus manifests, the bootstrap precision proxies and the synthetic-family
             pilot (tools/pivot/run_realcurve.py slope_bootstrap and ols_slope, tools/pivot/run_realcurve2.py
             paired_lead_bootstrap, with 0024's own seed, n_boot and resample construction), the operating
             characteristics of the verdict rule under a normal approximation, and the label-prior bound read from
             data/pivot/ext_c4096.npz after its array hashes are checked against the banked manifest.
  estimates  the brief's cost, memory and fit-side figures. They are ESTIMATES, not measurements: each one is a stated
             formula applied to banked inputs, and its basis is written beside it.

Every entry carries its value at the precision the brief writes it, the full-precision value, the inputs (path, keys,
sha256 of the file), the function used, and the seed and n_boot where a bootstrap is involved. Where the recomputation
disagrees with the brief's draft the computed value is banked and the entry says so (equals_brief false,
brief_value). Nothing here is fitted; no runner is executed; full_c4096.npz is never opened.

    python3 -B tools/prereg_gen/0026/bank_design_numbers.py            # write the artifact
    python3 -B tools/prereg_gen/0026/bank_design_numbers.py --check    # recompute and compare with the banked file

Deterministic: the same inputs give a byte-identical file. Threads are capped at 2 and memory stays well under 2 GB.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import sys
from decimal import ROUND_HALF_UP, Decimal
from statistics import NormalDist

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import numpy as np  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(REPO, "tools", "pivot"))
from run_realcurve import ols_slope, slope_bootstrap  # noqa: E402  (0023's runner; 0024 imports the same)
from run_realcurve2 import paired_lead_bootstrap  # noqa: E402  (0024's runner)
from run_recipe_search import _sha  # noqa: E402  (the runners' array digest convention)
from run_realfit import _array_sha  # noqa: E402  (the runners' npz array digest)
from corpus_ext import REAL_FAMILIES, SYNTH_FAMILIES  # noqa: E402

OUT = "artifacts/pivot/design_0026_numbers.json"
BRIEF = "docs/strategy/0026_DESIGN_BRIEF.md"
COMPUTED_ON = "2026-10-21"   # the date these numbers were first banked; a re-run reproduces the file byte for byte
STATUS = f"design numbers for an unfrozen, unwritten preregistration; informational; computed {COMPUTED_ON} from banked vectors"

A_RC2 = "artifacts/pivot/realcurve2_4096.json"
A_RC2S = "artifacts/pivot/realcurve2_4096_scores.json"
A_OOBS = "artifacts/pivot/oob_4096_scores.json"
A_RF1 = "artifacts/pivot/realfit_corpus_manifest.json"
A_RF2 = "artifacts/pivot/realfit2_corpus_manifest.json"
A_RF3 = "artifacts/pivot/realfit3_corpus_manifest.json"
A_EXT = "artifacts/pivot/ext_corpus_manifest.json"
A_RFR = "artifacts/pivot/realfit_4096_rerun.json"
A_RC1V = "artifacts/pivot/realcurve_4096_verdict.json"
D_EXT = "data/pivot/ext_c4096.npz"

F_SLOPE = "tools/pivot/run_realcurve.py:slope_bootstrap (point: tools/pivot/run_realcurve.py:ols_slope on 4-decimal rung accuracies)"
F_LEAD = "tools/pivot/run_realcurve2.py:paired_lead_bootstrap (point: difference of 4-decimal accuracies)"
F_MANIFEST = "tools/prereg_gen/0026/bank_design_numbers.py:rung_sizes (counting over the manifests' chunk_ids_with_rows and rows_per_chunk)"
F_COST = "tools/prereg_gen/0026/bank_design_numbers.py:loglog_seconds (piecewise-linear interpolation of log seconds on log fit rows over 0024's rungs 1..7, per role)"

CHANCE = 1.0 / 26
BAR = 0.005
ROLES = ("depth3_tree", "logistic", "model")


def file_sha(rel):
    h = hashlib.sha256()
    with open(os.path.join(REPO, rel), "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return json.load(fh)


def q(x, places):
    """x at `places` decimals, half up, from its shortest decimal repr (so 0.00375 -> 0.0038, never a binary artefact)."""
    return float(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def qd(x, places):
    return {k: q(v, places) for k, v in x.items()}


SHA = {}


def inp(rel, *keys):
    if rel not in SHA:
        SHA[rel] = file_sha(rel)
    return {"path": rel, "keys": list(keys), "sha256": SHA[rel]}


def entry(what, value, value_full, brief_value, equals_brief, inputs, function, rule, sections, seed=None, n_boot=None, note=None):
    e = {"what": what, "value": value, "value_full": value_full, "brief_value": brief_value, "equals_brief": bool(equals_brief),
         "inputs": inputs, "function": function, "rule": rule, "brief_sections": sections, "seed": seed, "n_boot": n_boot}
    if note:
        e["note"] = note
    return e


# ----------------------------------------------------------------------------------------------- manifests -> sizes
def family_slices(man, n_key):
    """Per family (chunk ids, rows per chunk) in the manifest's row order: family-major, pool order within a family."""
    ids, rpc, out, i = man["chunk_ids_with_rows"], man["rows_per_chunk"], {}, 0
    for f in man["families"]:
        n = int(man["per_family"][f][n_key])
        out[f] = (list(ids[i:i + n]), list(rpc[i:i + n]))
        i += n
    assert i == len(ids) == len(rpc), "per-family chunk counts do not cover the manifest"
    for f in man["families"]:   # the family encoded in the id agrees with the slice
        fi = man["families"].index(f)
        assert all((c - man["chunk_id_base"]) // man["family_stride"] == fi for c in out[f][0]), f
    return out


def rung_sizes(m2, m3, base, k):
    """0026's rung k: per family g the first n_g * 2^k chunks with rows of g's realfit2 pool followed by its realfit3 pool."""
    p2, p3 = family_slices(m2, "n_chunks_with_rows"), family_slices(m3, "n_new_chunks_with_rows")
    fams = m2["families"]
    out = {"plaintexts_per_family": {}, "rows_per_family": {}, "realfit3_positions_per_family": {}, "chunk_ids": []}
    for f in fams:
        ids = p2[f][0] + p3[f][0]; rpc = p2[f][1] + p3[f][1]
        need = int(base[f]) * 2 ** k
        if need > len(ids):
            return None
        out["plaintexts_per_family"][f] = need
        out["rows_per_family"][f] = int(sum(rpc[:need]))
        out["realfit3_positions_per_family"][f] = max(0, need - len(p2[f][0]))
        out["chunk_ids"] += ids[:need]
    out["plaintexts"] = sum(out["plaintexts_per_family"].values())
    out["rows"] = sum(out["rows_per_family"].values())
    out["realfit3_positions"] = sum(out["realfit3_positions_per_family"].values())
    return out


# ----------------------------------------------------------------------------------------------- cost model (estimates)
def loglog_seconds(points, rows):
    """Seconds at `rows` by linear interpolation of log(seconds) on log(rows) between 0024's adjacent banked rungs."""
    pts = sorted(points)
    return float(math.exp(np.interp(math.log(rows), [math.log(a) for a, _ in pts], [math.log(b) for _, b in pts])))


def verdict(T, lo, hi):
    """The brief's ordered verdict rule (section 1)."""
    if hi < 0:
        return "TRANSFER_FALLS"
    if T >= BAR and lo > 0:
        return "TRANSFER_RISES"
    if lo > 0 and T < BAR:
        return "TRANSFER_BELOW_RATE"
    if lo <= 0 and hi < BAR:
        return "TRANSFER_FLAT"
    return "TRANSFER_NOT_RESOLVED"


def reading_probabilities(true_slope, sd, h):
    """P(each verdict) when T ~ N(true_slope, sd) and the interval is T -/+ h. The rule is constant between the
    thresholds it applies to T, so each segment's probability is a CDF difference read at the segment's midpoint."""
    cuts = sorted({-h, h, BAR, BAR - h, 0.0, BAR + h})
    edges = [-math.inf] + cuts + [math.inf]
    nd = NormalDist(true_slope, sd)
    out = {}
    for a, b in zip(edges[:-1], edges[1:]):
        mid = (a + b) / 2 if math.isfinite(a) and math.isfinite(b) else (b - 1.0 if math.isfinite(b) else a + 1.0)
        w = verdict(mid, mid - h, mid + h)
        out[w] = out.get(w, 0.0) + (nd.cdf(b) if math.isfinite(b) else 1.0) - (nd.cdf(a) if math.isfinite(a) else 0.0)
    return {w: out.get(w, 0.0) for w in ("TRANSFER_FALLS", "TRANSFER_RISES", "TRANSFER_BELOW_RATE", "TRANSFER_FLAT", "TRANSFER_NOT_RESOLVED")}


# ----------------------------------------------------------------------------------------------- main build
def build():
    rc2 = load(A_RC2)
    sb = rc2["slope_bootstrap"]["model"]
    NB, SEED = int(sb["n_boot"]), int(sb["seed"])
    L = [float(v) for v in rc2["log2_chunks"]]
    L2 = [float(v) for v in rc2["log2_chunks_second_decade"]]

    S = load(A_RC2S)
    ne = int(S["n_eval_rows"]); names = S["ext_families"]
    famx = np.array([names[i] for i in S["ext_fam"]]); gx = np.asarray(S["ext_chunk_ids"], np.int64)
    V = {k: np.asarray(v[ne:], np.int8) for k, v in S["per_example"].items()}
    ext_ids_sha = _sha(gx); ext_fam_sha = _sha(np.asarray(S["ext_fam"], np.int64))
    O = load(A_OOBS)
    oob_ids_equal = O["ext_chunk_ids"] == S["ext_chunk_ids"]
    oob_fam_equal = O["ext_fam"] == S["ext_fam"] and O["ext_families"] == S["ext_families"]
    oob_n_equal = O["n_ext_rows"] == S["n_ext_rows"]
    assert oob_ids_equal and oob_fam_equal and oob_n_equal, "0018's and 0024's extension rows are not aligned"
    V["oob_model"] = np.asarray(O["per_example"]["model"][int(O["n_eval_rows"]):], np.int8)
    del S, O

    real = np.isin(famx, REAL_FAMILIES); syn = np.isin(famx, SYNTH_FAMILIES)
    r4 = lambda v: round(float(v), 4)  # noqa: E731  (the runners' reading precision)

    def slope_rd(names_, xs, mask):
        ys = [r4(V[n][mask].mean()) for n in names_]
        sl = slope_bootstrap({"model": [V[n][mask] for n in names_]}, xs, gx[mask], NB, SEED)["model"]
        lo, hi = round(float(np.percentile(sl, 2.5)), 6), round(float(np.percentile(sl, 97.5)), 6)
        return {"rung_accuracies": ys, "x": list(xs), "point": round(ols_slope(xs, ys), 6), "ci95": [lo, hi],
                "half_width": round((hi - lo) / 2, 7), "n_chunks": int(len(np.unique(gx[mask]))), "n_rows": int(mask.sum())}

    def diff_rd(a, b, mask):
        d = paired_lead_bootstrap(V[a][mask], V[b][mask], gx[mask], NB, SEED)
        lo, hi = round(float(np.percentile(d, 2.5)), 6), round(float(np.percentile(d, 97.5)), 6)
        return {"point": round(r4(V[a][mask].mean()) - r4(V[b][mask].mean()), 4), "ci95": [lo, hi], "half_width": round((hi - lo) / 2, 7),
                "share_of_resamples_above_zero": round(float((d > 0).mean()), 4), "n_chunks": int(len(np.unique(gx[mask])))}

    def vin(*vecs):
        return [inp(A_RC2S, *([f"per_example.{v}" for v in vecs] + ["ext_chunk_ids", "ext_fam", "ext_families", "n_eval_rows"])),
                inp(A_RC2, "slope_bootstrap.model.n_boot", "slope_bootstrap.model.seed")]

    N, E, checks, disc = {}, {}, {}, []

    def put(store, key, e):
        store[key] = e
        if not e["equals_brief"]:
            disc.append({"key": key, "brief": e["brief_value"], "computed": e["value"], "note": e.get("note", "")})

    def pc(rd, places_point, places_ci):
        return {"point": q(rd["point"], places_point), "ci95": [q(rd["ci95"][0], places_ci), q(rd["ci95"][1], places_ci)]}

    # -- 1. reader positive control: 0024's banked slope and lead, recomputed from the banked vectors
    pos = slope_rd([f"r{k}_model" for k in range(4, 8)], L2, real)
    lead = diff_rd("r7_model", "r7_logistic", real)
    bl = rc2["lead_at_top"]["r7_model_minus_logistic"]
    slope_equal = pos["ci95"] == [float(v) for v in sb["ci95"]] and round(pos["point"], 5) == float(rc2["model_slope_per_doubling"])
    lead_equal = lead["ci95"] == [float(v) for v in bl["ci95"]] and lead["point"] == float(bl["point"])
    checks["positive_control_slope_equals_banked"] = bool(slope_equal)
    checks["positive_control_lead_equals_banked"] = bool(lead_equal)
    v = pc(pos, 5, 5)
    put(N, "positive_control_model_slope_second_decade", entry(
        "reader positive control: 0024's model slope over rungs 4..7 on the 38452 real rows, recomputed from the banked vectors",
        dict(v, equals_banked=bool(slope_equal)), pos, "0.00697 [0.00571, 0.00824]", v == {"point": 0.00697, "ci95": [0.00571, 0.00824]},
        vin("r4_model", "r5_model", "r6_model", "r7_model") + [inp(A_RC2, "log2_chunks_second_decade", "model_slope_per_doubling", "slope_bootstrap.model.ci95")],
        F_SLOPE, "x = 0024's log2_chunks_second_decade; real-family rows; compared with the banked point and ci95 for exact equality",
        ["status", "7"], SEED, NB))
    v = {"point": q(lead["point"], 4), "ci95": [q(lead["ci95"][0], 4), q(lead["ci95"][1], 4)]}
    put(N, "positive_control_lead_r7_model_minus_logistic", entry(
        "reader positive control: 0024's lead of M4 over L3 at rung 7 on the real rows, recomputed",
        dict(v, equals_banked=bool(lead_equal)), lead, "[0.0001, 0.0077]", v["ci95"] == [0.0001, 0.0077],
        vin("r7_model", "r7_logistic") + [inp(A_RC2, "lead_at_top.r7_model_minus_logistic")],
        F_LEAD, "paired over the real chunks with the slope bootstrap's resamples; compared with the banked point and ci95 for exact equality",
        ["status", "7"], SEED, NB))

    # -- 2. rung and fold sizes from the manifests
    m1, m2, m3, mx = load(A_RF1), load(A_RF2), load(A_RF3), load(A_EXT)
    fams = list(m2["families"]); base = {f: int(m2["base_chunks_with_rows_0021"][f]) for f in fams}
    assert m3["families"] == fams and m1["families"] == fams and {f: int(m3["base_chunks_with_rows_0021"][f]) for f in fams} == base
    p2, p3 = family_slices(m2, "n_chunks_with_rows"), family_slices(m3, "n_new_chunks_with_rows")
    concat_ascending = all(p2[f][0] + p3[f][0] == sorted(p2[f][0] + p3[f][0]) and len(set(p2[f][0] + p3[f][0])) == len(p2[f][0]) + len(p3[f][0])
                           for f in fams)
    pool_total = {f: len(p2[f][0]) + len(p3[f][0]) for f in fams}
    checks["realfit3_ids_continue_realfit2_ids_ascending_per_family"] = bool(concat_ascending)
    checks["pool_totals_equal_realfit3_n_pool_chunks_with_rows_total"] = pool_total == {f: int(m3["per_family"][f]["n_pool_chunks_with_rows_total"]) for f in fams}
    assert concat_ascending and checks["pool_totals_equal_realfit3_n_pool_chunks_with_rows_total"]
    R = {k: rung_sizes(m2, m3, base, k) for k in (0, 1, 2, 3)}
    man_in = [inp(A_RF2, "base_chunks_with_rows_0021", "chunk_ids_with_rows", "rows_per_chunk", "per_family.*.n_chunks_with_rows", "chunk_order_note"),
              inp(A_RF3, "chunk_ids_with_rows", "rows_per_chunk", "per_family.*.n_new_chunks_with_rows", "per_family.*.n_pool_chunks_with_rows_total", "chunk_order_note")]
    shift = rc2["partition"]["shift_arm"]
    k0_chunks_sha = _sha(np.sort(np.asarray(R[0]["chunk_ids"], np.int64)).astype(np.int64))
    k0_is_s4 = (R[0]["rows_per_family"] == {f: int(shift["rows_per_family"][f]) for f in fams} and R[0]["rows"] == int(shift["n_rows"])
                and k0_chunks_sha == shift["chunks_sha256"])
    checks["k0_equals_0024_s4_rows_and_chunks"] = bool(k0_is_s4)
    assert k0_is_s4, "rung k = 0 derived from the manifests is not 0024's shift arm s4"
    brief_rungs = {0: (1029, 26420, 0), 1: (2058, 52632, 0), 3: (8232, 210720, 658)}
    rv = {f"k{k}": {"plaintexts": R[k]["plaintexts"], "rows": R[k]["rows"], "realfit3_positions": R[k]["realfit3_positions"],
                    "plaintexts_per_family": R[k]["plaintexts_per_family"], "rows_per_family": R[k]["rows_per_family"],
                    "realfit3_positions_per_family": R[k]["realfit3_positions_per_family"]} for k in (0, 1, 3)}
    put(N, "rungs_all_five", entry(
        "0026's all-five rungs k = 0, 1, 3: plaintexts, rows and realfit3 positions used, in total and per family",
        rv, dict(rv, k0_chunks_sha256=k0_chunks_sha, k0_equals_0024_s4=bool(k0_is_s4)), "1029/26420/0; 2058/52632/0; 8232/210720/658 (7/132/449/52/18)",
        all((R[k]["plaintexts"], R[k]["rows"], R[k]["realfit3_positions"]) == brief_rungs[k] for k in brief_rungs)
        and R[3]["realfit3_positions_per_family"] == dict(zip(fams, (7, 132, 449, 52, 18))),
        man_in + [inp(A_RC2, "partition.shift_arm.rows_per_family", "partition.shift_arm.n_rows", "partition.shift_arm.chunks_sha256")],
        F_MANIFEST, "per family g the first n_g * 2^k chunks with rows of realfit2's pool then realfit3's (chunk id ascending); rows summed "
                    "from rows_per_chunk; k = 0 checked against 0024's s4 (rows per family and the sorted chunk-id digest)", ["3"]))
    share = R[3]["realfit3_positions"] / R[3]["plaintexts"]
    put(N, "realfit3_share_of_k3_plaintexts", entry(
        "share of rung k = 3's plaintexts that come from realfit3", q(share, 2), round(share, 6), "about 8% (658 of 8232)",
        q(share, 2) == 0.08, man_in, F_MANIFEST, "realfit3 positions used at k = 3 / plaintexts at k = 3", ["3"]))
    k4 = {f: {"needed": base[f] * 16, "in_pools": pool_total[f], "short_by": base[f] * 16 - pool_total[f]} for f in fams}
    put(N, "k4_impossible", entry(
        "rung k = 4 needs 16 n_g plaintexts per family; the two pools hold fewer for every family", k4, k4,
        "c_src needs 384 and the pools hold 185 + 198 = 383", k4["c_src"]["needed"] == 384 and k4["c_src"]["in_pools"] == 383
        and len(p2["c_src"][0]) == 185 and len(p3["c_src"][0]) == 198, man_in, F_MANIFEST,
        "needed = 16 x base_chunks_with_rows_0021; in_pools = realfit2 chunks with rows + realfit3 new chunks with rows", ["3"],
        note="every family is short at k = 4, not only c_src: " + ", ".join(f"{f} {k4[f]['needed']} against {k4[f]['in_pools']}" for f in fams)))
    folds = {}
    for F in fams:
        folds[F] = {"seen_plaintexts": {f"k{k}": R[k]["plaintexts"] - R[k]["plaintexts_per_family"][F] for k in (0, 1, 3)},
                    "fit_rows": {f"k{k}": R[k]["rows"] - R[k]["rows_per_family"][F] for k in (0, 1, 3)},
                    "scored_rows": int(mx["per_family"][F]["n_rows"]), "scored_chunks_with_rows": int(mx["per_family"][F]["n_chunks_with_rows"])}
    brief_folds = {"c_src": ((1005, 2010, 8040), (25821, 51491, 206010), 7800, 300), "pe_bin": ((826, 1652, 6608), (21219, 42197, 169011), 7407, 288),
                   "py_src": ((357, 714, 2856), (9179, 18278, 73205), 7709, 300), "rfc_txt": ((939, 1878, 7512), (24081, 48010, 192254), 7761, 300),
                   "rst_doc": ((989, 1978, 7912), (25380, 50552, 202400), 7775, 300)}
    fold_eq = all((tuple(folds[F]["seen_plaintexts"].values()), tuple(folds[F]["fit_rows"].values()), folds[F]["scored_rows"],
                   folds[F]["scored_chunks_with_rows"]) == brief_folds[F] for F in fams)
    put(N, "fold_sizes", entry(
        "per held-out family F: seen plaintexts and fit rows at k = 0, 1, 3 (the all-five rung with F's rows deleted), and F's scored rows and chunks",
        folds, folds, "section 3 fold table", fold_eq, man_in + [inp(A_EXT, "per_family.*.n_rows", "per_family.*.n_chunks_with_rows")],
        F_MANIFEST, "all-five rung minus F's plaintexts and rows; scored sizes are the extension manifest's", ["3"]))
    ratio = {f"k{k}": sum(folds[F]["fit_rows"][f"k{k}"] for F in fams) / R[k]["rows"] for k in (0, 1, 3)}
    put(N, "rotation_rows_ratio", entry(
        "sum over the five folds of fit rows, over the all-five rung's rows, per rung", qd(ratio, 2), ratio, "4.00x",
        all(q(r, 2) == 4.0 for r in ratio.values()), man_in, F_MANIFEST, "each family's rows are in four of the five folds", ["2"]))

    # -- 3. bootstrap precision proxies and the synthetic-family pilot (0024 vectors; s4, r5, r7 stand in for k = 0, 1, 3)
    X3 = [0, 1, 3]
    pr = slope_rd(["s4_model", "r5_model", "r7_model"], X3, real)
    ps = slope_rd(["s4_model", "r5_model", "r7_model"], X3, syn)
    v = dict(pc(pr, 5, 5), half_width=q(pr["half_width"], 5))
    put(N, "proxy_real_s4_anchored_slope", entry(
        "s4-anchored in-distribution proxy: M4 slope over {s4, r5, r7} at x = {0, 1, 3} on the real rows (1488 chunks)", v, pr,
        "0.00749 [0.00624, 0.00876], half-width 0.00126", v == {"point": 0.00749, "ci95": [0.00624, 0.00876], "half_width": 0.00126},
        vin("s4_model", "r5_model", "r7_model"), F_SLOPE, "x = k; half-width = (hi - lo) / 2", ["5", "6"], SEED, NB))
    v = dict(pc(ps, 5, 5), half_width=q(ps["half_width"], 5))
    put(N, "proxy_synthetic_s4_anchored_slope", entry(
        "s4-anchored pilot on the never-fitted synthetic families: M4 slope over {s4, r5, r7} at x = {0, 1, 3} (899 chunks)", v, ps,
        "0.00490 [0.00371, 0.00619], half-width 0.00124", v == {"point": 0.0049, "ci95": [0.00371, 0.00619], "half_width": 0.00124},
        vin("s4_model", "r5_model", "r7_model"), F_SLOPE, "x = k; hexdump, sql and xml rows; half-width = (hi - lo) / 2", ["6", "9"], SEED, NB))
    t_r = slope_rd(["s4_model", "r7_model"], [0, 3], real)
    t_s = slope_rd(["s4_model", "r7_model"], [0, 3], syn)
    v = {"real": q(t_r["half_width"], 5), "synthetic": q(t_s["half_width"], 5)}
    put(N, "proxy_two_rung_half_width", entry(
        "95% half-width of the slope over {s4, r7} at x = {0, 3} only (the k = 1 cut), real and synthetic rows", v, {"real": t_r, "synthetic": t_s},
        "0.00123-0.00128", sorted(v.values()) == [0.00123, 0.00128], vin("s4_model", "r7_model"), F_SLOPE, "x = {0, 3}", ["6", "12"], SEED, NB))
    per = {F: slope_rd(["s4_model", "r5_model", "r7_model"], X3, famx == F) for F in REAL_FAMILIES}
    v = {F: q(per[F]["half_width"], 5) for F in REAL_FAMILIES}
    rng_ = [q(min(r["half_width"] for r in per.values()), 4), q(max(r["half_width"] for r in per.values()), 4)]
    put(N, "proxy_one_fold_half_width", entry(
        "95% half-width of one family's slope over {s4, r5, r7} at x = {0, 1, 3}, bootstrapped over that family's own chunks",
        dict(v, range=rng_), per, "0.00296, 0.00266, 0.00308, 0.00287, 0.00257 (range 0.0026 to 0.0031)",
        [v[F] for F in REAL_FAMILIES] == [0.00296, 0.00266, 0.00308, 0.00287, 0.00257] and rng_ == [0.0026, 0.0031],
        vin("s4_model", "r5_model", "r7_model"), F_SLOPE, "one family's rows; chunk_ids = that family's chunks", ["2", "6"], SEED, NB))
    d = diff_rd("s4_model", "r4_model", real)
    v = {"point": q(d["point"], 4), "ci95": [q(d["ci95"][0], 4), q(d["ci95"][1], 4)], "half_width": q(d["half_width"], 4)}
    put(N, "real_s4_minus_r4", entry(
        "paired equal-count difference on the real rows: s4 (other projects) minus r4 (0021's block), M4", v, d,
        "-0.0009 [-0.0048, 0.0027], half-width about 0.0038", v == {"point": -0.0009, "ci95": [-0.0048, 0.0027], "half_width": 0.0038},
        vin("s4_model", "r4_model"), F_LEAD, "half-width = (hi - lo) / 2", ["6"], SEED, NB))
    fd = slope_rd([f"r{k}_model" for k in range(1, 5)], L[:4], syn)
    v = pc(fd, 5, 5)
    put(N, "synthetic_first_decade_slope", entry(
        "pilot: M4 slope over 0024's rungs 1..4 on the synthetic rows", v, fd, "-0.00014 [-0.00121, 0.00108]",
        v == {"point": -0.00014, "ci95": [-0.00121, 0.00108]}, vin("r1_model", "r2_model", "r3_model", "r4_model") + [inp(A_RC2, "log2_chunks")],
        F_SLOPE, "x = 0024's log2_chunks for rungs 1..4", ["9"], SEED, NB))
    sd2 = slope_rd([f"r{k}_model" for k in range(4, 8)], L2, syn)
    v = {"point": q(sd2["point"], 5), "ci95": [q(sd2["ci95"][0], 4), q(sd2["ci95"][1], 3)]}
    put(N, "synthetic_second_decade_r4_anchored_slope", entry(
        "pilot: M4 slope over 0024's rungs 4..7 (0024's construction, r4-anchored) on the synthetic rows", v, sd2, "0.00977 [0.0086, 0.011]",
        v == {"point": 0.00977, "ci95": [0.0086, 0.011]}, vin("r4_model", "r5_model", "r6_model", "r7_model") + [inp(A_RC2, "log2_chunks_second_decade")],
        F_SLOPE, "x = 0024's log2_chunks_second_decade", ["5", "9"], SEED, NB))
    d = diff_rd("s4_model", "r4_model", syn)
    v = {"point": q(d["point"], 4), "ci95": [q(d["ci95"][0], 4), q(d["ci95"][1], 4)]}
    put(N, "synthetic_s4_minus_r4", entry(
        "pilot: s4 minus r4 on the synthetic rows (other projects against the pinned files at equal count), M4", v, d, "+0.0153 [0.0115, 0.0192]",
        v == {"point": 0.0153, "ci95": [0.0115, 0.0192]}, vin("s4_model", "r4_model"), F_LEAD, "paired", ["9"], SEED, NB))
    d = diff_rd("r7_model", "oob_model", syn)
    v = {"point": q(d["point"], 4), "ci95": [q(d["ci95"][0], 4), q(d["ci95"][1], 4)]}
    put(N, "synthetic_r7_minus_0018_builder_model", entry(
        "pilot: 0024's r7 M4 minus 0018's builder-fitted M4 on the synthetic rows", v, d, "+0.0006 [-0.0034, 0.0044]",
        v == {"point": 0.0006, "ci95": [-0.0034, 0.0044]},
        vin("r7_model") + [inp(A_OOBS, "per_example.model", "ext_chunk_ids", "ext_fam", "ext_families", "n_eval_rows")],
        F_LEAD, "paired; 0018's vector is aligned row for row with 0024's (see checks)", ["9"], SEED, NB))
    checks["oob_4096_scores_ext_rows_aligned_with_realcurve2"] = {"ext_chunk_ids_equal": bool(oob_ids_equal), "ext_fam_and_families_equal": bool(oob_fam_equal),
                                                                   "n_ext_rows_equal": bool(oob_n_equal), "ext_chunk_ids_sha256": ext_ids_sha,
                                                                   "ext_fam_sha256": ext_fam_sha}
    put(N, "oob_vectors_aligned", entry(
        "0018's per-example vectors (oob_4096_scores.json) carry the same extension chunk ids and families, row for row, as 0024's",
        True, checks["oob_4096_scores_ext_rows_aligned_with_realcurve2"], "chunk ids and families equal 0024's", True,
        [inp(A_OOBS, "ext_chunk_ids", "ext_fam", "ext_families", "n_ext_rows"), inp(A_RC2S, "ext_chunk_ids", "ext_fam", "ext_families", "n_ext_rows")],
        "list equality", "element-for-element equality of the two files' ext_chunk_ids, ext_fam and ext_families", ["5"]))

    # -- 4. operating characteristics (normal approximation around the real in-distribution proxy's half-width)
    h = pr["half_width"]; se = h / 1.96
    put(N, "oc_standard_error", entry(
        "standard error of T under the normal approximation: the real proxy's 95% half-width / 1.96", q(se, 5), round(se, 8), "0.00064",
        q(se, 5) == 0.00064, vin("s4_model", "r5_model", "r7_model"), "half_width / 1.96", "from proxy_real_s4_anchored_slope", ["6"], SEED, NB))
    oc = {}
    for t in (0.0, 0.0015, 0.0025, 0.0035, 0.005, 0.0065):
        oc[repr(t)] = reading_probabilities(t, se, h)
    ocq = {t: {w: q(p, 2) for w, p in ps_.items()} for t, ps_ in oc.items()}
    brief_oc = {"0.0": {"TRANSFER_FLAT": 0.95, "TRANSFER_FALLS": 0.02, "TRANSFER_BELOW_RATE": 0.02}, "0.0015": {"TRANSFER_BELOW_RATE": 0.65, "TRANSFER_FLAT": 0.35},
                "0.0025": {"TRANSFER_BELOW_RATE": 0.97}, "0.0035": {"TRANSFER_BELOW_RATE": 0.99}, "0.005": {"TRANSFER_RISES": 0.5, "TRANSFER_BELOW_RATE": 0.5},
                "0.0065": {"TRANSFER_RISES": 0.99}}
    put(N, "operating_characteristics", entry(
        "probability of each verdict at six true slopes: T ~ N(true, se), interval T -/+ half-width, the ordered rule of section 1",
        ocq, {t: {w: round(p, 6) for w, p in ps_.items()} for t, ps_ in oc.items()}, "section 6 table; NOT_RESOLVED about 0.000",
        all(all(ocq[t][w] == p for w, p in brief_oc[t].items()) for t in brief_oc) and all(ocq[t]["TRANSFER_NOT_RESOLVED"] == 0.0 for t in ocq),
        vin("s4_model", "r5_model", "r7_model"), "tools/prereg_gen/0026/bank_design_numbers.py:reading_probabilities (statistics.NormalDist)",
        "segments between the rule's thresholds on T, each read by the rule at its midpoint", ["6"]))

    # -- 5. label-prior bound and chunk completeness on the sealed real rows (ext_c4096.npz, hashes checked against the manifest)
    arr_ok = {}
    for nm in ("y", "g", "fam"):
        sha, shape, dtype = _array_sha(os.path.join(REPO, D_EXT), nm)
        want = mx["arrays"][nm]
        arr_ok[nm] = {"sha256": sha, "equals_manifest": sha == want["sha256"] and shape == want["shape"] and dtype == want["dtype"]}
    checks["ext_c4096_arrays_equal_manifest"] = arr_ok
    assert all(a["equals_manifest"] for a in arr_ok.values()), "data/pivot/ext_c4096.npz does not match the banked manifest"
    z = np.load(os.path.join(REPO, D_EXT))
    y = np.asarray(z["y"]); g = np.asarray(z["g"]); fz = np.asarray(z["fam"]); del z
    freq = {}
    for F in REAL_FAMILIES:
        m = fz == mx["families"].index(F)
        freq[F] = float(np.bincount(y[m], minlength=26).max() / m.sum())
    top = max(freq, key=freq.get); lvl = freq[top] - CHANCE
    w = [(x - sum(X3) / 3) / sum((x - sum(X3) / 3) ** 2 for x in X3) for x in X3]
    slope_bound = lvl * sum(c for c in w if c > 0)
    realm = np.isin(fz, [mx["families"].index(F) for F in REAL_FAMILIES])
    ids, cnt = np.unique(g[realm], return_counts=True)
    full = int((cnt == 26).sum())
    v = {"max_family_label_frequency": q(freq[top], 6), "family": top, "chance": q(CHANCE, 6), "level_bound": q(lvl, 6),
         "slope_bound_per_doubling": q(slope_bound, 6), "chunks_with_all_26_rows": full, "real_chunks": int(len(ids)), "rows_in_complete_chunks": full * 26}
    put(N, "label_prior_bound", entry(
        "largest per-family label frequency on the real rows, the level a prior-only rule can move, its bound per doubling over k = {0, 1, 3}, "
        "and the chunks that carry all 26 rows", v, dict(v, per_family_max_label_frequency={F: round(x, 8) for F, x in freq.items()},
                                                          slope_bound_endpoint_over_3=round(lvl / 3, 8), slope_bound_ols=round(slope_bound, 8)),
        "0.038916 (py_src), 0.000454, under 0.00016 per doubling; 1473 of 1488 chunks carry all 26 rows (38298 rows)",
        False, [inp(D_EXT, "y", "g", "fam"), inp(A_EXT, "arrays.y", "arrays.g", "arrays.fam", "families")],
        "tools/pivot/run_realfit.py:_array_sha (hash check); numpy bincount",
        "per family max_c count(y = c) / n_rows; level bound = max - 1/26; slope bound = level bound x the sum of the positive OLS weights "
        "(x - mean) / Sxx over x = {0, 1, 3}, i.e. 5/14 of it", ["7"],
        note="the brief's 'under 0.00016 per doubling' divided the level by the 3 doublings spanned (0.000151); the largest OLS slope over "
             "k = {0, 1, 3} of a level confined to a band of that width is 5/14 of it, 0.000162, which is not under 0.00016"))

    # -- 6. ESTIMATES: cost, memory, fit side. Formula + banked inputs; never measurements.
    fits = rc2["fits"]; fi = rc2["fit_info_by_name"]
    PTS = {r: [(int(fits[f"r{k}_{r}"]["n_fit_rows"]), float(fits[f"r{k}_{r}"]["seconds"])) for k in range(1, 8)] for r in ROLES}
    cost_in = [inp(A_RC2, "fits.r{1..7}_{depth3_tree,logistic,model}.n_fit_rows", "fits.r{1..7}_{depth3_tree,logistic,model}.seconds")]

    def clause(k):
        return {F: {r: loglog_seconds(PTS[r], folds[F]["fit_rows"][f"k{k}"]) if k != 2 else loglog_seconds(PTS[r], R[2]["rows"] - R[2]["rows_per_family"][F])
                    for r in ROLES} for F in fams}
    C = {k: clause(k) for k in (0, 1, 2, 3)}
    layer = {f"k{k}": sum(sum(C[k][F].values()) for F in fams) for k in (0, 1, 2, 3)}
    m4k3 = sum(C[3][F]["model"] for F in fams)
    null_s = float(fits["null"]["seconds"]) * folds["c_src"]["fit_rows"]["k3"] / int(fits["null"]["n_fit_rows"])
    sbn = rc2["cost"]["seconds_by_name"]; repro = round(sbn["s4_model"] + sbn["s4_logistic"] + sbn["s4_depth3_tree"], 1)
    rr = load(A_RFR); fsec = rr["cost"]["seconds_by_name"]; frows = 26346
    assert int(m1["n_rows"]) == frows
    floors = sum((fsec["floor_feat1"] + fsec["floor_majority"] + fsec["floor_stratified"]) * folds[F]["fit_rows"][f"k{k}"] / frows
                 for F in fams for k in (0, 1, 3))
    core = null_s + repro + layer["k0"] + layer["k1"] + layer["k3"] + floors
    a1 = sum(loglog_seconds(PTS[r], int(m1["n_rows"]) - int(m1["per_family"][F]["n_rows"])) for F in fams for r in ROLES)
    pair = sum(loglog_seconds(PTS[r], R[k]["rows"] - R[k]["rows_per_family"]["py_src"] - R[k]["rows_per_family"]["rst_doc"]) for k in (0, 3) for r in ROLES)
    cum = {"null": null_s, "reproduction": null_s + repro, "k0": null_s + repro + layer["k0"], "k1": null_s + repro + layer["k0"] + layer["k1"]}
    cum["k3"] = cum["k1"] + layer["k3"]; cum["floors_core"] = core; cum["a1"] = core + a1; cum["pair"] = core + a1 + pair
    per_fold_core = {F: sum(sum(C[k][F].values()) for k in (0, 1, 3)) for F in fams}
    per_fold_k3 = {F: sum(C[3][F].values()) for F in fams}
    v = {"null": q(null_s, 0), "reproduction": repro, "clause_k0": q(layer["k0"], 0), "clause_k1": q(layer["k1"], 0), "clause_k3": q(layer["k3"], 0),
         "clause_k3_model": q(m4k3, 0), "floors": q(floors, 0), "core": q(core, 0), "core_hours": q(core / 3600, 2),
         "a1_arm": q(a1, 0), "pair_fold": q(pair, 0), "skipped_k2": q(layer["k2"], 0),
         "cumulative": {kk: q(vv, 0) for kk, vv in cum.items()}, "cumulative_hours": {"a1": q(cum["a1"] / 3600, 2), "pair": q(cum["pair"] / 3600, 2)},
         "per_fold_core": {F: q(x, 0) for F, x in per_fold_core.items()}, "per_fold_k3": {F: q(x, 0) for F, x in per_fold_k3.items()},
         "c_src_k3_model": q(C[3]["c_src"]["model"], 0)}
    vf = {"null": round(null_s, 3), "floors": round(floors, 3), "core": round(core, 3), "a1_arm": round(a1, 3), "pair_fold": round(pair, 3),
          "layers": {kk: round(x, 3) for kk, x in layer.items()}, "clause_k3_model": round(m4k3, 3),
          "per_fold_per_rung_per_role": {F: {f"k{k}": {r: round(C[k][F][r], 3) for r in ROLES} for k in (0, 1, 2, 3)} for F in fams}}
    brief_cost = {"null": 218, "reproduction": 353.2, "clause_k0": 1556, "clause_k1": 2504, "clause_k3": 10903, "clause_k3_model": 9283, "floors": 50,
                  "core": 15584, "core_hours": 4.33, "a1_arm": 1551, "pair_fold": 850, "skipped_k2": 5270, "c_src_k3_model": 2298}
    put(E, "cost_fit_seconds", dict(entry(
        "fit seconds per layer of the run, central estimate", v, vf,
        "null 218, reproduction 353.2, k0 1556, k1 2504, k3 10903 (M4 9283), floors about 50, core 15584 (4.33 h), A1 1551 (17135, 4.76 h), "
        "pair 850 (17985, 5.00 h), k2 5270; per fold 3662/3023/1254/3424/3600; k3 per fold 2694/2190/867/2506/2645; c_src k3 M4 2298",
        all(v[kk] == bv for kk, bv in brief_cost.items()), cost_in + [inp(A_RC2, "fits.null.seconds", "fits.null.n_fit_rows", "cost.seconds_by_name.s4_*"),
                                                                      inp(A_RFR, "cost.seconds_by_name.floor_feat1", "cost.seconds_by_name.floor_majority",
                                                                          "cost.seconds_by_name.floor_stratified"),
                                                                      inp(A_RF1, "n_rows", "per_family.*.n_rows")] + man_in,
        F_COST, "clause and arm fits: per role, log-log interpolation at each fold's fit rows; null: 0024's null seconds x rows / 210751; "
                "reproduction: 0024's three s4 seconds summed; floors: 0021's three floor seconds (B-feat1 1.1 s, the other two 0.0 s) at 26346 rows, "
                "linear in rows over the 15 fold-rung fits; A1: 0021's block minus F; pair fold: the all-five rung minus py_src and rst_doc at k = 0 and 3",
        ["0", "3", "7", "12"], note="floors were an allowance of about 50 s in the draft; the linear-in-rows estimate is 48 s, which moves the core "
                                    "and the cumulative totals by 2 s"), kind="estimate",
        basis="0024's banked fit seconds by role and rows; the run's real seconds depend on iteration counts, which are not known in advance"))
    xs = [int(fits[f"r{k}_model"]["n_fit_rows"]) for k in range(4, 8)]
    ys = [float(fits[f"r{k}_model"]["seconds"]) / int(fi[f"r{k}_model"]["n_iter"]) for k in range(4, 8)]
    b, a = (float(c) for c in np.polyfit(xs, ys, 1))
    per_iter_sum = sum(a + b * folds[F]["fit_rows"]["k3"] for F in fams)
    base_core = core - m4k3
    r153 = int(fi["r7_model"]["n_iter"]); r117 = int(fi["r6_model"]["n_iter"]); n184 = math.ceil(1.2 * r153); cap = 250
    cases = {str(n): base_core + n * per_iter_sum for n in (r117, n184, cap)}
    v = {"seconds_per_iteration_at_r4_to_r7": [q(t, 2) for t in ys], "intercept_seconds": q(a, 2), "seconds_per_row": q(b, 7),
         "n_iter_cases": [r117, n184, cap], "core_seconds": {n: q(s_, 0) for n, s_ in cases.items()}, "core_hours": {n: q(s_ / 3600, 2) for n, s_ in cases.items()},
         "c_src_k3_model_at_cap": q(cap * (a + b * folds["c_src"]["fit_rows"]["k3"]), 0), "central_equivalent_n_iter": q(m4k3 / per_iter_sum, 1)}
    put(E, "cost_range_by_iterations", dict(entry(
        "core fit seconds when every k = 3 M4 fit runs n iterations, by a per-iteration rule fitted to 0024's rungs 4..7", v,
        {"intercept": a, "slope": b, "cases": cases}, "about 4.1 + 5.3e-5 x rows; 13927 (3.87 h), 18294 (5.08 h), 22596 (6.28 h); c_src k3 M4 at the cap 3755",
        False, [inp(A_RC2, "fits.r{4..7}_model.seconds", "fits.r{4..7}_model.n_fit_rows", "fit_info_by_name.r{4..7}_model.n_iter")] + cost_in + man_in,
        "numpy.polyfit (degree 1) on seconds / n_iter against n_fit_rows", "core minus the central k = 3 M4 seconds, plus n x sum over folds of "
        "(intercept + slope x fold rows); n = r6's 117, ceil(1.2 x r7's 153) = 184, and the cap 250", ["12"],
        note="the least-squares line through 0024's four per-iteration points is about 3.90 + 0.0000546 x rows, not the draft's 4.1 + 5.3e-5; "
             "the cases move by 39 to 82 s"), kind="estimate", basis="assumes seconds per iteration are linear in rows, as at 0024's rungs 4..7"))
    ratio_w = float(rc2["cost"]["wall_seconds_this_invocation"]) / float(rc2["cost"]["banked_fit_seconds_total"])
    v = {"wall_over_fit": q(ratio_w, 3), "core_wall_seconds_at_most_about": q(core * ratio_w, -2), "core_wall_hours": q(core * ratio_w / 3600, 1)}
    put(E, "wall_time", dict(entry(
        "wall seconds at most 0024's wall-to-fit ratio times the fit seconds", v, {"ratio": ratio_w, "core_wall": core * ratio_w},
        "1.085; about 16900 s (4.7 h)", v == {"wall_over_fit": 1.085, "core_wall_seconds_at_most_about": 16900.0, "core_wall_hours": 4.7},
        [inp(A_RC2, "cost.wall_seconds_this_invocation", "cost.banked_fit_seconds_total")], "ratio", "core x ratio", ["12"]),
        kind="estimate", basis="0024 scored 321409 rows per fit; 0026 scores 61409, so the ratio is an upper allowance"))
    rss = [e["rss_gb"] for e in rc2["ledger"] if e.get("event") == "rung_bound" and e.get("rung") == 7 and e.get("name") == "run_r7_depth3_tree"]
    nfeat = int(mx["arrays"]["X"]["shape"][1]); n_eval = int(rc2["n_eval_rows"])
    comp = {"start_rss_gb": float(rss[0]), "minus_builder_scoring_set_gb": n_eval * nfeat * 4 / 1e9, "plus_realfit3_gb": int(m3["n_rows"]) * nfeat * 4 / 1e9,
            "plus_c_src_k3_block_float64_gb": folds["c_src"]["fit_rows"]["k3"] * nfeat * 8 / 1e9,
            "plus_trees_float32_copy_gb": folds["c_src"]["fit_rows"]["k3"] * nfeat * 4 / 1e9}
    peak = comp["start_rss_gb"] - comp["minus_builder_scoring_set_gb"] + comp["plus_realfit3_gb"] + comp["plus_c_src_k3_block_float64_gb"] + comp["plus_trees_float32_copy_gb"]
    v = dict({kk: q(x, 2) for kk, x in comp.items()}, peak_gb=q(peak, 1))
    put(E, "memory_peak", dict(entry(
        "anonymous memory peak at the c_src k = 3 tree fit", v, dict(comp, peak_gb=peak), "about 6.2 GB (3.59 - 1.15 + 0.97 + 1.83 + 0.91)", q(peak, 1) == 6.2,
        [inp(A_RC2, "ledger[event=rung_bound, name=run_r7_depth3_tree].rss_gb", "n_eval_rows"), inp(A_EXT, "arrays.X.shape"), inp(A_RF3, "n_rows")] + man_in,
        "sum", "start - 260000 x 1108 x 4 B + realfit3 rows x 1108 x 4 B + fold rows x 1108 x 8 B + fold rows x 1108 x 4 B (GB = 1e9 B)", ["12"],
        note="the unrounded components sum to 6.15 GB, which is 6.1 at one decimal; the draft's 6.2 summed the rounded components"),
        kind="estimate", basis="0024's anonymous RSS before its rung-7 block plus the arrays 0026 adds or drops; COULD NOT VERIFY until run"))
    sd_fit = float(load(A_RC1V)["flags"]["replicate_rung_1"]["difference_from_rung_1"]["model"])
    sxx = sum((x - sum(X3) / 3) ** 2 for x in X3)
    sd_tot = math.sqrt(se ** 2 + sd_fit ** 2 / sxx)
    p_flat = reading_probabilities(0.0, sd_tot, h)["TRANSFER_FLAT"]
    v = {"slope_dispersion": q(sd_tot, 5), "p_flat_at_true_zero": q(p_flat, 2)}
    put(E, "fit_side", dict(entry(
        "slope dispersion and P(FLAT | true slope 0) if 0023's one-replicate difference (0.001) were the per-rung fit-side SD, independent across rungs",
        v, {"slope_dispersion": sd_tot, "p_flat_at_true_zero": p_flat, "fit_sd_per_rung": sd_fit, "sxx": sxx}, "about 0.00079; about 0.89",
        v == {"slope_dispersion": 0.00079, "p_flat_at_true_zero": 0.89},
        [inp(A_RC1V, "flags.replicate_rung_1.difference_from_rung_1.model")] + vin("s4_model", "r5_model", "r7_model"),
        "tools/prereg_gen/0026/bank_design_numbers.py:reading_probabilities", "sqrt(se^2 + sd^2 / Sxx), Sxx over x = {0, 1, 3}; the interval keeps "
        "the scored-side half-width", ["6"]), kind="estimate", basis="one replicate reads the size of the fit-side variance; it does not bound it"))

    for store in (N, E):
        for e in store.values():
            e["inputs"] = sorted(e["inputs"], key=lambda i: i["path"])
    doc = {"schema": "raise-v1/design_0026_numbers/1", "status": STATUS, "brief": BRIEF,
           "generator": "tools/prereg_gen/0026/bank_design_numbers.py",
           "not_a_preregistration": "0026 is written and frozen only after 0025's run; nothing here is sealed, and the preregistration's pre-freeze "
                                    "check must recompute these with the runner's own code",
           "conventions": {"bootstrap": f"0024's construction: {NB} cluster resamples of the scored chunks, numpy default_rng({SEED}), rung accuracies "
                                        "rounded to 4 decimals inside each resample; ci95 = 2.5th and 97.5th percentiles rounded to 6 decimals",
                           "half_width": "(hi - lo) / 2 of the 6-decimal ci95", "value": "at the precision the brief writes it, rounded half up from the "
                           "shortest decimal repr; value_full holds the unrounded reading", "proxies": "0024's s4, r5 and r7 vectors stand in for 0026's "
                           "k = 0, 1 and 3 at x = k; r5 and r7 still contain 0021's block, so they are proxies only"},
           "environment": {"python": sys.version.split()[0], "numpy": np.__version__},
           "inputs": {p: {"sha256": SHA[p], "bytes": os.path.getsize(os.path.join(REPO, p))} for p in sorted(SHA)},
           "numbers": N, "estimates": E, "checks": checks,
           "discrepancies_with_the_draft": sorted(disc, key=lambda x: x["key"])}
    return doc


def dumps(doc):
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="recompute and compare with the banked file; exit 1 on any difference")
    args = ap.parse_args()
    text = dumps(build())
    path = os.path.join(REPO, OUT)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    if args.check:
        with open(path, encoding="utf-8") as fh:
            same = fh.read() == text
        print(f"{'ok' if same else 'DIFFERS'}: {OUT} {'reproduces' if same else 'does not reproduce'} byte for byte (peak RSS {peak:.0f} MB)")
        return 0 if same else 1
    with open(path + ".tmp", "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(path + ".tmp", path)
    doc = json.loads(text)
    print(f"wrote {OUT}: {len(doc['numbers'])} numbers, {len(doc['estimates'])} estimates, "
          f"{len(doc['discrepancies_with_the_draft'])} discrepancies with the draft (peak RSS {peak:.0f} MB)")
    for d in doc["discrepancies_with_the_draft"]:
        print(f"  {d['key']}: draft {d['brief']} | computed {json.dumps(d['computed'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
