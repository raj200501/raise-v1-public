#!/usr/bin/env python3
"""Frozen reader for preregistration 0025 — TWO decades of real plaintexts at 4096: the fourth doubling of other files.

Written and committed BEFORE any fit was made under this preregistration. Every literal below was generated
from prereg/0025-realcurve3-4096.json or read from a banked artifact; none was typed here.

WHY THIS EXISTS. 0024 read SECOND_DECADE_RISES_MODEL_LEADS over seven nested rungs (130 -> 8232 real plaintexts,
rungs 5..7 other files of the same five families nested on 0021's block): the model's second-decade slope 0.00697
per doubling, the model 0.0039 ahead of the standardised logistic at the top rung with a paired interval
[0.0001, 0.0077]. The span was 1.8016 decades, short of 0003's two-decade scope rule. This run adds ONE more exact
per-family doubling from 0025's corpus (tools/pivot/corpus_realfit3.py: 0024's pool in 0024's order, then a seeded
permutation of the remaining and new candidates), so rung 8 holds sixteen times rung 4's plaintexts of every family
and the curve spans %(decades)s decades. Seven of the eight points were banked before this run, so no slope over them
can be the clause: the reader's verdict is read on the FOURTH DOUBLING alone - rung 8 minus rung 7 for the model,
with a paired cluster-bootstrap interval over the scored real chunks - into RISES (at or above 0.005 with the interval
above 0), BELOW_RATE (interval above 0, gain below 0.005), NOT_RESOLVED (interval includes 0) or FALLS (interval
below 0), suffixed by the lead of the model over the logistic at rung 8 under 0024's sealed rule. The same gain with rung 7
held at 0024's banked reading is read by the same rule; if the two straddle a reading boundary, the meaning states both and
the published reading is the less flattering one, named as such. 0024's seven rungs
and its shift arm are refitted row for row under 0024's own seeds and must reproduce 0024's readings (rung 7's three
roles within 0.0005, the rest within 0.005) and 0024's banked bootstrap intervals exactly (0024's bootstrap seed is
sealed for every verdict interval here). Three of 0021's four trivial-baseline floors are refitted on rungs 7 and 8 and
banked as flags; the fourth, B-tree3, is D1 itself, so the tree floor at a rung is the curve's tree reading there. A second shift arm - rung 8's plaintexts from 0025's corpus alone at 0021's count (the new files and 0024's archives' unused chunks; the composition per family is banked) - is fitted last,
informational, beside 0024's.

This reader takes the runner's artifact (tools/pivot/run_realcurve3.py) and checks, clause by clause: the sealed
corpora (array hashes for the builder cache, the evaluation corpus and the three fit corpora); the sealed split, the
sealed fit block, every sealed rung and both shift arms (hash for hash, nested, strictly increasing, exact doublings
above 0021's block); that nothing scored was fitted and the three fit corpora share nothing (the runner's measured
chunk, source-chunk and row-identity counts must all be 0); that every fit is the sealed recipe on the sealed rung
with the sealed seed, scored exactly once, in the sealed order, with its fingerprint recomputed here; that each
record's own scores equal what its per-example vector gives; that every reproduction lands within its tolerance and
0024's intervals reproduce exactly; that the null control on the top rung sits at chance on both row sets; that every
banked reading, curve, gain, interval, lead, floor and shift-arm difference equals what this reader recomputes from
the vectors and the sealed chunk layout. Then the sealed reading of the fourth doubling on the reader's own numbers,
and the sealed lead rule at rung 8. Twelve verdict strings, each published at the same size; VOID on any validity
failure.

NOT A TRANSFER READING, AND NOT 0023's IN-DISTRIBUTION READING EITHER. Every rung holds the scored files' own
unscored chunks (0021's block); the added plaintexts are other projects' files of the same five families. Nothing
fitted shares a byte, a kilobyte run, a chunk index, a chunk id or a source-chunk hash with anything scored, and the
runner measures that rather than assuming it. Every verdict string this reader emits says what the gain is measured
against.

WHAT THIS READER CANNOT SEE. The binding of a per-example vector to the fit that produced it is the runner's
self-report (its fingerprint, its ledger, the vector's hash) plus the committed checkpoints, which this reader
cross-checks whenever the checkpoint directory is present; it also requires the thirty-seven vectors to be pairwise
distinct. No extrapolation beyond the top rung is banked. A role at its iteration cap at the top rung is named
beside the lead reading, which is then not quoted as a recipe comparison.

Digest convention: sha256 of np.ascontiguousarray(a).tobytes(); index arrays int64 in their order; sorted sets
np.sort(...).astype(np.int64); corpus arrays as stored (float32 X, int16 y, int32 g little-endian, int8 fam);
per-example vectors as int8 bytes.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "realcurve3_4096.json")
SCORES = os.path.join(REPO, "artifacts", "pivot", "realcurve3_4096_scores.json")
NOT_RUN = os.path.join(REPO, "artifacts", "pivot", "realcurve3_4096_not_run.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "realcurve3_4096_verdict.json")
PREREG = "0025-realcurve3-4096"

FAMILIES = %(fam)s
EXT_FAMILIES = %(ext_fam)s
REAL_FAMILIES = %(real_fam)s
SYNTH_FAMILIES = %(synth_fam)s
FIT_FAMILIES = %(fit_fam)s
STRUCTURED_TEXT = %(structured)s
HIGH_ENTROPY = %(high_entropy)s

# the builder cache block the runner banks (0021's values; X's hash from the sealed cache identity)
CORPUS = %(corpus)s
# the sealed protocol, field by field, and its digest; the curve spec (protocol + recipes) and its digest
PROTOCOL = %(proto)s
PROTOCOL_SHA256 = "%(proto_sha)s"
CURVE_SHA256 = "%(curve_sha)s"
RECIPES = %(recipes)s
ROLES = %(roles)s
ORDER = %(order)s
DENOMINATORS = %(denominators)s
N_FIRST = %(n_first)s                   # 0023's rungs 1..4; rung 4 is 0021's whole fit block
DOUBLINGS_0024 = %(doublings_0024)s
DOUBLINGS_0025 = %(doublings_0025)s
N_RUNGS = %(n_rungs)s
TOP = "r%(n_rungs)s_"
R4 = "r%(n_first)s_"

PARTITION = %(partition)s
EXT = %(ext)s
FIT = %(fit)s
FIT2 = %(fit2)s
FIT3 = %(fit3)s
EXT_CHUNK_IDS = %(ext_chunk_ids)s
EXT_ROWS_PER_CHUNK = %(ext_rows_per_chunk)s
EVAL_CHUNK_IDS = %(eval_chunk_ids)s
EVAL_ROWS_PER_CHUNK = %(eval_rows_per_chunk)s
SEED = %(seed)s
SEED2 = %(seed2)s                     # 0024's: its pool, its rungs' row order, its shift arm, and every verdict interval's bootstrap here
SEED3 = %(seed3)s                     # 0025's: the new pool positions, rung 8's row order, the new shift arm, the null control
CHANCE = %(chance)s
N_EXT = %(n_ext)s
N_REAL = %(n_real)s
N_0024_RUNGS = %(n_0024_rungs)s       # 0024's rungs 1..7, reproduced row for row
FLOOR_ROLES = %(floor_roles)s         # three of 0021's four trivial baselines, refitted on rungs 7 and 8 (flags); B-tree3 is D1
ALL_ROLES = ROLES + FLOOR_ROLES
REFERENCE = %(reference)s              # 0021's banked readings rung 4's three roles must reproduce
REFERENCE_FIRST = %(reference_first)s  # 0023's banked readings per role over rungs 1..4
REFERENCE_0024 = %(reference_0024)s    # 0024's banked readings per role over rungs 1..7, which rungs 1..7 must reproduce
REFERENCE_SHIFT_0024 = %(reference_shift_0024)s   # 0024's banked shift-arm readings per role, which s4 must reproduce
REFERENCE_BOOT_0024 = %(reference_boot_0024)s     # 0024's banked slope_bootstrap and lead_at_top, which the reader's recomputation must equal exactly
REPRO_TOLERANCE = %(repro_tol)s
REPRO_TOLERANCE_R7 = %(repro_tol_r7)s  # rung 7's three roles, which the fourth-doubling gain and the lead read against
NULL_TOLERANCE = %(null_tol)s
NULL_SHA_EXPECTED = "%(null_sha)s"     # the top rung's labels permuted by the sealed generator, hash for hash
ENV = %(env)s
ENV_FULL = dict(ENV, threads=%(threads)s, nice=%(nice)s)
BAR_GAIN = %(bar_gain)s                # the record's rate: accuracy on the real-family rows per doubling of plaintexts
GAIN_RULE = %(gain_rule)s
LEAD_RULE = %(lead_rule)s
GAIN_CAP_NOTE = %(gain_cap_note)s     # the gain rule's own words for a capped model, N the rung
LEAD_CAP_NOTE = %(lead_cap_note)s     # the lead rule's own words for a capped role, <role> the role
# scope.design.how_the_sensitivity_gain_is_read: when the measured gain and the gain with rung 7 held at 0024's banked reading straddle
# a reading boundary, the published reading is the less flattering one; least flattering first
GAIN_READINGS_LEAST_FLATTERING_FIRST = ["FOURTH_DOUBLING_FALLS", "FOURTH_DOUBLING_NOT_RESOLVED", "FOURTH_DOUBLING_BELOW_RATE", "FOURTH_DOUBLING_RISES"]
N_BOOT = %(n_boot)s
BOOT_SEED = %(boot_seed)s              # 0024's seed2: the same resamples as 0024's verdict intervals
STABILITY_SEEDS = %(stability_seeds)s
LOG2X = %(log2x)s                      # log2(plaintexts) per rung, sealed
LOG2X_SECOND = LOG2X[N_FIRST - 1:]
LOG2X_FIRST = LOG2X[:N_FIRST]
LOG2X_0024 = LOG2X[:N_0024_RUNGS]
LOG2X_SECOND_0024 = LOG2X[N_FIRST - 1:N_0024_RUNGS]
MAX_ITER = %(max_iter)s                # by role: the iteration cap of the hgb and logistic recipes
SHIFT4 = "%(shift4)s"                  # 0024's shift arm, reproduced: rung 5's new plaintexts alone
SHIFT8 = "%(shift8)s"                  # the new shift arm: rung 8's plaintexts from 0025's corpus alone, rung 4's count; last
CKPT_DIR = os.path.join(REPO, "artifacts", "pivot", "realcurve3_4096_ckpt")
RESULT_KEYS = %(result_keys)s


def sha_obj(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def fingerprint(**parts) -> str:
    return sha_obj(parts)[:16]


def ols_slope(xs, ys):
    x = np.asarray(xs, np.float64); y = np.asarray(ys, np.float64); xm = x - x.mean()
    return float((xm * (y - y.mean())).sum() / (xm * xm).sum())


def slope_bootstrap(correct_by_role, log2x, chunk_ids, n_boot, seed):
    """tools/pivot/run_realcurve.py slope_bootstrap, verbatim: one resample of chunks per draw serves every rung and
    every role; rung accuracies inside a resample are rounded to 4 decimals, as the banked readings are."""
    _, inv = np.unique(chunk_ids, return_inverse=True); counts = np.bincount(inv).astype(np.float64)
    sums = {r: [np.bincount(inv, weights=np.asarray(c, np.float64), minlength=len(counts)) for c in vecs]
            for r, vecs in correct_by_role.items()}
    rng = np.random.default_rng(seed); n = len(counts)
    x = np.asarray(log2x, np.float64); xm = x - x.mean(); den = float((xm * xm).sum())
    out = {r: np.empty(n_boot) for r in correct_by_role}
    for b in range(n_boot):
        idx = rng.integers(0, n, n); tot = counts[idx].sum()
        for r, s in sums.items():
            accs = np.array([round(float(v[idx].sum() / tot), 4) for v in s])
            out[r][b] = float((xm * (accs - accs.mean())) .sum() / den)
    return out


def paired_lead_bootstrap(vec_a, vec_b, chunk_ids, n_boot, seed):
    """tools/pivot/run_realcurve2.py paired_lead_bootstrap, verbatim: the same generator construction and draw order as
    slope_bootstrap, so the resamples are the slope bootstrap's; accuracies rounded to 4 decimals inside a resample."""
    _, inv = np.unique(chunk_ids, return_inverse=True); counts = np.bincount(inv).astype(np.float64)
    sa = np.bincount(inv, weights=np.asarray(vec_a, np.float64), minlength=len(counts))
    sb = np.bincount(inv, weights=np.asarray(vec_b, np.float64), minlength=len(counts))
    rng = np.random.default_rng(seed); n = len(counts); out = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n); tot = counts[idx].sum()
        out[b] = round(float(sa[idx].sum() / tot), 4) - round(float(sb[idx].sum() / tot), 4)
    return out


def composition_phrase(comp):
    """What the fourth doubling's added files are per family, in the stop rules' words, from the sealed counts alone: 'new projects'
    where most of a family's added plaintexts come from new files, 'other chunks of 0024's projects' where none does, 'a mixture'
    otherwise (stop_rules[5]; the generator refuses a reader whose phrase is not the stop rule's)."""
    groups = {"new projects": [], "other chunks of 0024's projects": [], "a mixture": []}
    for f, c in comp.items():
        new = c["from_new_files"]
        groups["new projects" if 2 * new > c["n"] else "other chunks of 0024's projects" if new == 0 else "a mixture"].append(f)
    return ", ".join(f"{k} for {' and '.join(fs) if len(fs) < 3 else ', '.join(fs[:-1]) + ' and ' + fs[-1]}" for k, fs in groups.items() if fs)


def _write(result):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")


def main() -> int:
    if os.path.exists(OUT):
        os.remove(OUT)   # a stale verdict never survives a reader run that emits none
    if os.path.exists(NOT_RUN):
        try:
            nr = json.load(open(NOT_RUN, encoding="utf-8"))
            print(f"READER 0025: NOT RUN — {nr.get('reason')!r} (stage {nr.get('stage')}, filed {nr.get('utc')}, "
                  f"{nr.get('n_checkpoints')} checkpoints). A NOT RUN is not a verdict.", file=sys.stderr)
        except Exception:  # noqa: BLE001
            print("READER 0025: NOT RUN file present but unreadable.", file=sys.stderr)
        return 2
    if not os.path.exists(ARTIFACT):
        print(f"READER 0025: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n  Absence is not a pass. No verdict emitted.",
              file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0025: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 2
    try:
        return read(d)
    except Exception as e:  # noqa: BLE001
        result = dict({k: None for k in RESULT_KEYS},
                      schema="raise-v1/realcurve3_4096_verdict/1", preregistration=PREREG,
                      source_artifact=os.path.relpath(ARTIFACT, REPO), verdict="VOID",
                      meaning="The artifact has an unexpected shape; nothing is counted in either direction.",
                      validity_failed_clauses=[f"reader: artifact of unexpected shape ({type(e).__name__}: {e})"],
                      establishes_a_buyer=False)
        _write(result)
        print(f"READER 0025 — VOID: artifact of unexpected shape ({type(e).__name__}: {e})\n  wrote {os.path.relpath(OUT, REPO)}")
        return 0


def read(d) -> int:
    g = d.get
    void: list[str] = []

    def num(v):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None
        return v if math.isfinite(v) else None

    def expect_eq(where, got, want, label):
        if got != want:
            where.append(f"{label}={got!r}, preregistered {want!r}")

    def _ints(v, n, values=None):
        return isinstance(v, list) and len(v) == n and all(
            isinstance(x, int) and not isinstance(x, bool) and (values is None or x in values) for x in v)

    _int = lambda v: isinstance(v, int) and not isinstance(v, bool)  # noqa: E731
    mean4 = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
    rungs_sealed = PARTITION["rungs"]

    def rung_of(name):
        if name == "null":
            return N_RUNGS
        head = name[:name.index("_")]
        return head if head in (SHIFT4, SHIFT8) else int(head[1:])

    def role_of(name):
        return "null" if name == "null" else name[name.index("_") + 1:]

    def cand_of(name):
        return RECIPES["model"] if name == "null" else RECIPES[role_of(name)]

    def rk_of(k):
        return PARTITION["shift_arm"] if k == SHIFT4 else PARTITION["shift_arm_0025"] if k == SHIFT8 else rungs_sealed[k - 1]

    def stage_of(name):
        if name == "null":
            return "null"
        k = rung_of(name); role = role_of(name)
        return "shift" if k in (SHIFT4, SHIFT8) else "floor" if role in FLOOR_ROLES else ("curve" if k > N_0024_RUNGS else "reproduction")

    # ---- scope
    if g("preregistration") != PREREG:
        void.append(f"scope: preregistration={g('preregistration')!r}, this reader is frozen for {PREREG}")
    if g("smoke") is not False:
        void.append(f"scope: smoke={g('smoke')!r}; a smoke run is not the preregistered run")
    if g("stage") != "run":
        void.append(f"scope: stage={g('stage')!r}, the verdict is read from the run artifact")
    corpus = g("corpus") or {}
    for k, v in CORPUS.items():
        expect_eq(void, corpus.get(k), v, f"scope: corpus.{k}")
    if g("n_classes") != 26 or num(g("chance_accuracy")) != CHANCE:
        void.append(f"scope: n_classes={g('n_classes')!r}, chance_accuracy={g('chance_accuracy')!r}")
    spec = g("curve_spec") or {}
    if g("curve_sha256") != CURVE_SHA256 or sha_obj(spec) != CURVE_SHA256:
        void.append("scope: the banked curve spec does not hash to the sealed CURVE_SHA256")
    proto = spec.get("protocol") or {}
    for k in sorted(set(PROTOCOL) | set(proto)):
        if proto.get(k) != PROTOCOL.get(k):
            void.append(f"scope: curve_spec.protocol.{k}={proto.get(k)!r}, preregistered {PROTOCOL.get(k)!r}")
    if sha_obj(proto) != PROTOCOL_SHA256:
        void.append("scope: the banked protocol does not hash to the sealed PROTOCOL_SHA256")
    if spec.get("recipes") != RECIPES:
        void.append("scope: the banked recipes are not the sealed six")
    if g("roles") != ROLES or g("floor_roles") != FLOOR_ROLES or g("n_rungs") != N_RUNGS or g("n_first_decade_rungs") != N_FIRST \
            or g("n_0024_rungs") != N_0024_RUNGS or g("denominators") != DENOMINATORS or g("doublings_0024") != DOUBLINGS_0024 \
            or g("doublings_0025") != DOUBLINGS_0025 or g("log2_chunks") != LOG2X or g("log2_chunks_second_decade") != LOG2X_SECOND:
        void.append(f"scope: roles={g('roles')!r}, floor_roles={g('floor_roles')!r}, n_rungs={g('n_rungs')!r}, n_0024_rungs={g('n_0024_rungs')!r}, "
                    f"denominators={g('denominators')!r}, doublings={g('doublings_0024')!r}+{g('doublings_0025')!r}, log2_chunks={g('log2_chunks')!r} "
                    f"are not the sealed ones")
    if g("bar") != {"gain_per_doubling": BAR_GAIN, "gain_rule": GAIN_RULE, "lead_rule": LEAD_RULE, "n_boot": N_BOOT, "bootstrap_seed": BOOT_SEED}:
        void.append(f"scope: bar={g('bar')!r} is not the sealed bar")

    # ---- the scored corpus and the two fit corpora
    ext = g("ext_corpus") or {}
    for k, v in EXT.items():
        expect_eq(void, ext.get(k), v, f"evaluation corpus: ext_corpus.{k}")
    fit = g("fit_corpus") or {}
    for k, v in FIT.items():
        expect_eq(void, fit.get(k), v, f"fit corpus: fit_corpus.{k}")
    fit2 = g("fit2_corpus") or {}
    for k, v in FIT2.items():
        expect_eq(void, fit2.get(k), v, f"second-decade corpus: fit2_corpus.{k}")
    fit3 = g("fit3_corpus") or {}
    for k, v in FIT3.items():
        expect_eq(void, fit3.get(k), v, f"fourth-doubling corpus: fit3_corpus.{k}")
    n_eval = PARTITION["n_eval_rows"]; n_all = n_eval + N_EXT
    if g("n_ext_rows") != N_EXT or g("n_eval_rows") != n_eval or g("n_ext_real_rows") != N_REAL:
        void.append(f"corpora: n_ext_rows={g('n_ext_rows')!r}, n_eval_rows={g('n_eval_rows')!r}, "
                    f"n_ext_real_rows={g('n_ext_real_rows')!r}")
    if g("ext_real_families") != REAL_FAMILIES or g("ext_synthetic_families") != SYNTH_FAMILIES \
            or g("fit_families") != FIT_FAMILIES or g("fit_rows_per_family") != FIT["rows_per_family"] \
            or g("fit2_rows_per_family") != FIT2["rows_per_family"] or g("fit3_rows_per_family") != FIT3["rows_per_family"]:
        void.append("corpora: the banked family lists or fit row counts are not the sealed ones")

    # ---- sealed sets, the rungs, and the measured proof that nothing scored was fitted
    part = g("partition") or {}
    for k, v in PARTITION.items():
        expect_eq(void, part.get(k), v, f"sealed set: partition.{k}")
    for k in ("pool_chunks_shared_with_ext", "eval_chunks_shared_with_ext", "fit_chunks_shared_with_ext",
              "fit_chunks_shared_with_builder", "fit_source_chunks_shared_with_ext", "fit_rows_identical_to_a_scored_row",
              "fit2_chunks_shared_with_ext", "fit2_chunks_shared_with_builder", "fit2_chunks_shared_with_fit",
              "fit2_source_chunks_shared_with_ext", "fit2_source_chunks_shared_with_fit", "fit2_rows_identical_to_a_scored_row",
              "fit3_chunks_shared_with_ext", "fit3_chunks_shared_with_builder", "fit3_chunks_shared_with_fit", "fit3_chunks_shared_with_fit2",
              "fit3_source_chunks_shared_with_ext", "fit3_source_chunks_shared_with_fit", "fit3_source_chunks_shared_with_fit2",
              "fit3_rows_identical_to_a_scored_row"):
        if part.get(k) != 0:
            void.append(f"leakage: partition.{k}={part.get(k)!r}, must be the measured 0")
    if not isinstance(part.get("chunk_ids_0025_continue_0024s_per_family"), dict) or not all(part["chunk_ids_0025_continue_0024s_per_family"].get(f) is True for f in FIT_FAMILIES):
        void.append("rungs: 0025's chunk ids are not banked as continuing 0024's per family")
    for k in ("rungs_nested", "rung_chunks_strictly_increasing", "rung4_is_fit_block", "second_decade_exact_doublings",
              "split_is_grouped_by_source"):
        if part.get(k) is not True:
            void.append(f"rungs: partition.{k}={part.get(k)!r}, must be True")
    if part.get("pool_short") != {}:
        void.append(f"rungs: partition.pool_short={part.get('pool_short')!r}, the pool must cover every doubling")
    sa = part.get("shift_arm") or {}
    if sa.get("same_chunks_as_rung_5s_new_chunks") is not True or sa.get("same_plaintext_count_as_rung_4") is not True:
        void.append("shift arm: partition.shift_arm must be rung 5's new chunks and rung 4's plaintext count")
    s8 = part.get("shift_arm_0025") or {}
    if s8.get("all_chunks_in_the_top_rung") is not True or s8.get("all_chunks_above_0024s_ids") is not True or s8.get("same_plaintext_count_as_rung_4") is not True:
        void.append("shift arm: partition.shift_arm_0025 must be the top rung's new-file plaintexts alone at rung 4's count")
    if part.get("null_labels_permuted") is not True or part.get("null_labels_same_multiset") is not True:
        void.append("null control: the null labels are not banked as a permutation of the top rung's labels")
    if part.get("null_y_shuffled_sha256") != NULL_SHA_EXPECTED:
        void.append(f"null control: the permuted label array hashes to {part.get('null_y_shuffled_sha256')!r}, not the sealed "
                    f"{NULL_SHA_EXPECTED!r}")
    if not isinstance(part.get("null_rule"), str):
        void.append("null control: the partition carries no null_rule")
    if g("complete") is not True or not isinstance(g("run_finished_utc"), str):
        void.append(f"complete: complete={g('complete')!r}, run_finished_utc={g('run_finished_utc')!r}; missing {g('missing_roles')!r}")
    le = g("launch_environment") or {}
    if le.get("ok") is not True or le.get("problems") != [] or any((le.get("env") or {}).get(k) != v for k, v in ENV_FULL.items()):
        void.append("environment: launch_environment is not ok with the sealed environment")
    env = g("environment") or {}
    for k, v in ENV_FULL.items():
        if env.get(k) != v:
            void.append(f"environment: {k}={env.get(k)!r}, banked {v!r}")
    ledger = g("ledger") or []

    # ---- scores file: the vectors and the arrays that bind every reading to the sealed corpora
    scores, ext_fam_idx, eci, eval_ids = {}, None, None, None
    if os.path.exists(SCORES):
        try:
            sd = json.load(open(SCORES, encoding="utf-8")) or {}
            scores = sd.get("per_example") or {}
            ext_fam_idx = sd.get("ext_fam"); eci = sd.get("ext_chunk_ids"); eval_ids = sd.get("eval_chunk_ids")
            if sd.get("eval_idx_sha256") != PARTITION["eval_idx_sha256"] or sd.get("smoke") is not False \
                    or sd.get("preregistration") != PREREG or sd.get("n_eval_rows") != n_eval or sd.get("n_ext_rows") != N_EXT \
                    or sd.get("ext_families") != EXT_FAMILIES \
                    or sd.get("ext_arrays_sha256") != {k: v["sha256"] for k, v in EXT["arrays"].items()} \
                    or sd.get("fit_arrays_sha256") != {k: v["sha256"] for k, v in FIT["arrays"].items()} \
                    or sd.get("fit2_arrays_sha256") != {k: v["sha256"] for k, v in FIT2["arrays"].items()} \
                    or sd.get("fit3_arrays_sha256") != {k: v["sha256"] for k, v in FIT3["arrays"].items()}:
                void.append("scores: the scores file is not this run's, or is a smoke run's, or names a different corpus")
        except Exception:  # noqa: BLE001
            void.append("scores: the scores file is not JSON")
    else:
        void.append("scores: the scores file is absent")
    if not _ints(ext_fam_idx, N_EXT, set(range(len(EXT_FAMILIES)))):
        void.append("scores: ext_fam missing, not N_EXT long, or not family indices"); ext_fam_idx = None
    elif hashlib.sha256(bytes(ext_fam_idx)).hexdigest() != EXT["arrays"]["fam"]["sha256"]:
        void.append("scores: ext_fam does not hash to the sealed fam array"); ext_fam_idx = None
    if not _ints(eci, N_EXT):
        void.append("scores: ext_chunk_ids missing or not N_EXT long"); eci = None
    else:
        try:
            gb = b"".join(int(x).to_bytes(4, "little", signed=True) for x in eci)
        except OverflowError:
            gb = b""
        if hashlib.sha256(gb).hexdigest() != EXT["arrays"]["g"]["sha256"]:
            void.append("scores: ext_chunk_ids do not hash to the sealed g array")
        if eci != [c for c, n in zip(EXT_CHUNK_IDS, EXT_ROWS_PER_CHUNK) for _ in range(n)]:
            void.append("scores: ext_chunk_ids are not the sealed chunk ids expanded by their sealed row counts")
        if ext_fam_idx is not None:
            per = {f: set() for f in EXT_FAMILIES}
            for c, f in zip(eci, ext_fam_idx):
                per[EXT_FAMILIES[f]].add(c)
            if {f: len(s) for f, s in per.items()} != EXT["chunks_per_family"]:
                void.append("scores: distinct chunk ids per family are not the sealed chunks_per_family")
    if ext_fam_idx is not None:
        counts = {f: 0 for f in EXT_FAMILIES}
        for i in ext_fam_idx:
            counts[EXT_FAMILIES[i]] += 1
        if counts != EXT["rows_per_family"]:
            void.append(f"scores: ext_fam row counts {counts} are not the sealed rows_per_family")
    fam_e = None
    if not _ints(eval_ids, n_eval, None) or min(eval_ids) < CORPUS["chunk_id_min"] or max(eval_ids) > CORPUS["chunk_id_max"] \
            or len(set(eval_ids)) != PARTITION["n_eval_chunks"] \
            or sum(1 for c in eval_ids if c %% len(FAMILIES) != 0) != PARTITION["n_eval_non_gutenberg"]:
        void.append("scores: eval_chunk_ids missing, not the sealed evaluation chunks, or not the sealed family mix")
    else:
        try:
            _eb = b"".join(int(x).to_bytes(4, "little", signed=True) for x in eval_ids)
        except OverflowError:
            _eb = b""
        _expected = [c for c, n in zip(EVAL_CHUNK_IDS, EVAL_ROWS_PER_CHUNK) for _ in range(n)]
        if hashlib.sha256(_eb).hexdigest() != PARTITION["eval_g_sha256"] or list(eval_ids) != _expected:
            void.append("scores: eval_chunk_ids are not the sealed evaluation chunk ids expanded by their sealed row counts, "
                        "or do not hash to the sealed evaluation g array")
        else:
            fam_e = [FAMILIES[int(c) %% len(FAMILIES)] for c in eval_ids]

    # ---- the fits: one scoring per role, the sealed recipe on the sealed rung, the sealed order
    fits = g("fits") or {}
    if not isinstance(fits, dict):
        void.append("fit: fits is not a mapping"); fits = {}

    def expected_fp(name, cand):
        k = rung_of(name); rk = rk_of(k)
        return fingerprint(prereg=PREREG, seed=SEED, seed2=SEED2, seed3=SEED3, head=("null" if name == "null" else role_of(name)), cand=cand,
                           stage=stage_of(name), rung=k, rows=rk["sorted_sha256"],
                           eval=PARTITION["eval_idx_sha256"], ext=EXT["arrays"]["X"]["sha256"], fit=FIT["arrays"]["X"]["sha256"],
                           fit2=FIT2["arrays"]["X"]["sha256"], fit3=FIT3["arrays"]["X"]["sha256"])

    completed_pos = {}

    def check_record(name):
        rec = fits.get(name); cand = cand_of(name); k = rung_of(name); rk = rk_of(k)
        head = "null" if name == "null" else role_of(name); stage = stage_of(name)
        if not isinstance(rec, dict) or rec.get("status") != "fit":
            void.append(f"fit: {name} status {(rec.get('status') if isinstance(rec, dict) else type(rec).__name__)!r}; must be 'fit'"); return
        if num(rec.get("top1")) is None or num(rec.get("top1_non_gutenberg")) is None or \
                not isinstance(rec.get("per_family"), dict) or any(num(v) is None for v in rec["per_family"].values()):
            void.append(f"fit: {name} scores are not all finite")
        if rec.get("id") != cand["id"] or rec.get("params_sha256") != sha_obj(cand) or rec.get("params") != cand.get("params", {}) \
                or rec.get("family") != cand["family"] or bool(rec.get("scaled")) != bool(cand.get("scaled", False)) \
                or rec.get("val") != cand.get("val") or rec.get("head") != head:
            void.append(f"fit: {name} is not the sealed {cand['id']} (id, params, params hash, family, scaled, val or head off-recipe)")
        if rec.get("seed") != SEED or rec.get("n_fit_rows") != rk["n_rows"] or rec.get("fit_rows_sha256") != rk["idx_sha256"] \
                or rec.get("fit_rows_sorted_sha256") != rk["sorted_sha256"] or rec.get("rung") != k or rec.get("role") != head \
                or rec.get("n_rung_rows") != rk["n_rows"] or rec.get("n_rung_chunks") != rk["n_chunks"]:
            void.append(f"fit: {name} was not fitted on sealed rung {k} with the preregistered seed")
        if rec.get("stage") != stage:
            void.append(f"fit: {name} stage {rec.get('stage')!r} is not {stage!r}")
        if any(not (rf.get("probe_ok") if isinstance(rf, dict) else False) for rf in (rec.get("block_refills") or [])):
            void.append(f"fit: {name} banked a failed block probe check")
        info = rec.get("fit_info")
        if not isinstance(info, dict):
            void.append(f"fit: {name} banked no fit_info")
        elif cand["family"] in ("hgb", "logistic"):
            if not _int(info.get("n_iter")):
                void.append(f"fit: {name} has no integer iteration count")
        elif cand["family"] == "tree":
            if not (_int(info.get("depth")) and _int(info.get("n_leaves"))):
                void.append(f"fit: {name} has no integer depth and leaf count")
        elif cand["family"] == "dummy":
            if not isinstance(info, dict):
                void.append(f"fit: {name} has no fit_info mapping")
        renv = rec.get("environment") or {}
        for kk, v in ENV_FULL.items():
            if renv.get(kk) != v:
                void.append(f"environment: {name} {kk}={renv.get(kk)!r}, banked {v!r}")
        fp = expected_fp(name, cand)
        if rec.get("fingerprint") != fp:
            void.append(f"fit: {name} fingerprint {rec.get('fingerprint')!r} is not the one recomputed from the sealed literals")
        done = [i for i, e in enumerate(ledger) if isinstance(e, dict) and e.get("name") == f"run_{name}" and e.get("event") == "completed"]
        if len(done) != 1:
            void.append(f"fit: {name} has {len(done)} ledger completions, must be exactly 1")
        else:
            ce = ledger[done[0]]
            if ce.get("fingerprint") != fp:
                void.append(f"fit: {name}'s completion event does not carry the sealed fingerprint")
            if not any(isinstance(e, dict) and e.get("name") == f"run_{name}" and e.get("event") == "started" and e.get("fingerprint") == fp
                       for e in ledger[:done[0]]):
                void.append(f"fit: {name} has no 'started' event with its fingerprint before its completion")
            if not any(isinstance(e, dict) and e.get("name") == f"run_{name}" and e.get("event") == "rung_bound"
                       and e.get("rung") == k and e.get("rung_sorted_sha256") == rk["sorted_sha256"] for e in ledger[:done[0]]):
                void.append(f"fit: {name} has no 'rung_bound' event naming sealed rung {k} before its completion")
            completed_pos[name] = done[0]
        pe = scores.get(name)
        if not _ints(pe, n_all, (0, 1)):
            void.append(f"fit: {name} per-example vector missing, not {n_all} long, or not in {{0, 1}}"); return
        if rec.get("per_example_sha256") != hashlib.sha256(bytes(pe)).hexdigest():
            void.append(f"fit: {name} per_example_sha256 is not the hash of its banked vector")
        if num(rec.get("top1")) != mean4(pe):
            void.append(f"fit: {name} record top1 {rec.get('top1')!r} is not its vector's mean {mean4(pe)!r}")
        if fam_e is not None and ext_fam_idx is not None:
            fam_s = fam_e + ["ext:" + EXT_FAMILIES[i] for i in ext_fam_idx]
            pf = {f: mean4([pe[i] for i in range(n_all) if fam_s[i] == f]) for f in sorted(set(fam_s))}
            if rec.get("per_family") != pf:
                void.append(f"fit: {name} record per_family is not its vector's per-family means over the sealed scoring set")
            tng = mean4([pe[i] for i in range(n_eval) if fam_e[i] != "gutenberg"] + list(pe[n_eval:]))
            if num(rec.get("top1_non_gutenberg")) != tng:
                void.append(f"fit: {name} record top1_non_gutenberg {rec.get('top1_non_gutenberg')!r} is not its vector's "
                            f"non-gutenberg mean {tng!r}")

    if set(fits) != set(ORDER):
        extra = sorted(set(fits) - set(ORDER)); absent = sorted(set(ORDER) - set(fits))
        void.append(f"fit: the artifact banks roles outside the sealed order (extra {extra}, missing {absent}) - "
                    f"'scored exactly once, in the sealed order' is a property of the run, not of {len(ORDER)} names")
    for name in ORDER:
        check_record(name)
    # B-majority predicts one constant class, the majority label of its rung; when rungs 7 and 8 share that label the two majority
    # floors bank the same vector honestly (found by the pre-freeze review on the runner's own smoke). That pair, and only that pair,
    # may coincide; any other shared vector - including a majority floor equal to any other role - is VOID.
    maj_pair = {f"r{N_0024_RUNGS}_floor_majority", f"r{N_RUNGS}_floor_majority"}
    by_sha = {}
    for n in ORDER:
        if isinstance(fits.get(n), dict) and fits[n].get("per_example_sha256") is not None:
            by_sha.setdefault(fits[n]["per_example_sha256"], []).append(n)
    same = sorted(n for grp in by_sha.values() if len(grp) > 1 and set(grp) != maj_pair for n in grp)
    if same:
        void.append(f"fit: roles {same} bank the same per-example vector; distinct fits on distinct row sets do not score identically "
                    f"(only the majority-class floor at rungs {N_0024_RUNGS} and {N_RUNGS} may)")
    foreign = [e.get("name") for e in ledger if isinstance(e, dict) and e.get("event") == "completed"
               and e.get("name") not in {f"run_{n}" for n in ORDER}]
    if foreign:
        void.append(f"order: the ledger carries completions under names outside the sealed order ({foreign[:3]!r})")
    ckpt_checked = None
    if os.path.isdir(CKPT_DIR):
        ckpt_checked = 0
        for name in ORDER:
            rec = fits.get(name); cp = os.path.join(CKPT_DIR, f"run_{name}.json")
            if not isinstance(rec, dict):
                continue
            if not os.path.exists(cp):
                void.append(f"checkpoint: {name} has no checkpoint although the checkpoint directory is present"); continue
            try:
                ck = json.load(open(cp, encoding="utf-8"))
            except Exception:  # noqa: BLE001
                void.append(f"checkpoint: {name}'s checkpoint is not JSON"); continue
            pe = ck.get("per_example") if isinstance(ck, dict) else None
            added = ("fingerprint", "rung", "role", "n_rung_rows", "n_rung_chunks", "per_example_sha256")   # fit_role adds these after run_fit
            ok_ = (isinstance(ck, dict) and ck.get("fingerprint") == expected_fp(name, cand_of(name)) and _ints(pe, n_all, (0, 1))
                   and hashlib.sha256(bytes(pe)).hexdigest() == rec.get("per_example_sha256")
                   and ck.get("record") == {k: v for k, v in rec.items() if k not in added})
            if not ok_:
                void.append(f"checkpoint: {name}'s committed checkpoint does not carry the sealed fingerprint, the banked vector and the banked record")
            else:
                ckpt_checked += 1
    if g("null_control") != (fits.get("null") or {}):
        void.append("null control: null_control is not the banked null record")
    if g("null_rows") != rungs_sealed[-1]["n_rows"]:
        void.append(f"null control: null_rows={g('null_rows')!r}, the null control is fitted on the whole top rung")
    if len(completed_pos) == len(ORDER) and [completed_pos[n] for n in ORDER] != sorted(completed_pos[n] for n in ORDER):
        void.append("fit: the ledger's completions are not in the sealed order " + ", ".join(ORDER))
    completions = [e.get("name") for e in ledger if isinstance(e, dict) and e.get("event") == "completed"
                   and str(e.get("name", "")).startswith("run_")]
    if completions != [f"run_{n}" for n in ORDER]:
        void.append(f"order: the ledger's run completions are not exactly the sealed order ({completions!r})")
    if g("fit_info_by_name") != {n: (fits.get(n) or {}).get("fit_info") for n in ORDER}:
        void.append("fit: fit_info_by_name is not the records' fit_info")

    # ---- every reading re-derived from the per-example vectors and the sealed family arrays
    reads = g("readings") or {}
    rec_reads = {}
    real_idx = None
    if ext_fam_idx is not None and fam_e is not None and not any(m.startswith("fit:") or m.startswith("scores:") for m in void):
        fam_x = [EXT_FAMILIES[i] for i in ext_fam_idx]
        real_idx = [i for i in range(N_EXT) if fam_x[i] in REAL_FAMILIES]
        for name in ORDER:
            v = scores[name]; rep, ex = v[:n_eval], v[n_eval:]
            by = {f: [] for f in EXT_FAMILIES}
            for i in range(N_EXT):
                by[fam_x[i]].append(ex[i])
            real = [x for f in REAL_FAMILIES for x in by[f]]; synth = [x for f in SYNTH_FAMILIES for x in by[f]]
            rr = {"builder_eval_top1": mean4(rep), "builder_eval_correct": sum(rep),
                  "ext_top1": mean4(ex), "ext_correct": sum(ex), "n_ext_rows": N_EXT,
                  "ext_per_family": {f: mean4(by[f]) for f in EXT_FAMILIES},
                  "ext_per_family_correct": {f: sum(by[f]) for f in EXT_FAMILIES},
                  "ext_structured_text_top1": mean4([x for f in STRUCTURED_TEXT for x in by[f]]),
                  "ext_high_entropy_top1": mean4([x for f in HIGH_ENTROPY for x in by[f]]),
                  "ext_real_top1": mean4(real), "ext_real_correct": sum(real), "n_ext_real_rows": len(real),
                  "ext_synthetic_correct": sum(synth), "ext_synthetic_top1": mean4(synth),
                  "builder_eval_per_family": {f: mean4([rep[i] for i in range(n_eval) if fam_e[i] == f]) for f in FAMILIES}}
            if len(real) != N_REAL:
                void.append(f"readings: the sealed family array gives {len(real)} real-family rows, not {N_REAL}")
            rec_reads[name] = rr
            banked = reads.get(name) or {}
            for k, val in rr.items():
                if banked.get(k) != val:
                    void.append(f"readings: {name}.{k}={banked.get(k)!r} is not the reader's recomputation {val!r}")
        if set(reads) != set(ORDER):
            void.append(f"readings: banked readings for {sorted(reads)!r}, expected exactly {ORDER!r}")
        for name in ORDER:
            if num((g("ext_real_top1") or {}).get(name)) != rec_reads[name]["ext_real_top1"] \
                    or (g("ext_real_correct") or {}).get(name) != rec_reads[name]["ext_real_correct"] \
                    or num((g("ext_top1") or {}).get(name)) != rec_reads[name]["ext_top1"] \
                    or num((g("builder_eval_top1") or {}).get(name)) != rec_reads[name]["builder_eval_top1"] \
                    or (g("ext_per_family") or {}).get(name) != rec_reads[name]["ext_per_family"]:
                void.append(f"readings: a banked summary reading for {name} is not the recomputed value")
        repro_expect = {role: rec_reads[R4 + role]["ext_real_top1"] for role in ROLES}
        if {k: num(v) for k, v in (g("reproduction_top1") or {}).items()} != repro_expect:
            void.append("reproduction: reproduction_top1 is not rung 4's recomputed real-family reading per role")
        if g("reference_top1") != REFERENCE:
            void.append("reproduction: the banked reference readings are not 0021's sealed ones")
        drift_expect = {role: round(repro_expect[role] - REFERENCE[role], 6) for role in ROLES}
        if {k: num(v) for k, v in (g("reproduction_drift") or {}).items()} != drift_expect:
            void.append("reproduction: reproduction_drift is not the recomputed drift per role")
        first_expect = {role: [rec_reads[f"r{k}_{role}"]["ext_real_top1"] for k in range(1, N_FIRST + 1)] for role in ROLES}
        if g("reproduction_first_decade") != first_expect or g("reference_first_decade") != REFERENCE_FIRST:
            void.append("reproduction: reproduction_first_decade or reference_first_decade is not the recomputed or sealed value")
        first_drift = {role: [round(a - b, 6) for a, b in zip(first_expect[role], REFERENCE_FIRST[role])] for role in ROLES}
        if g("reproduction_first_decade_drift") != first_drift:
            void.append("reproduction: reproduction_first_decade_drift is not the recomputed drift per rung and role")
        r24_expect = {role: [rec_reads[f"r{k}_{role}"]["ext_real_top1"] for k in range(1, N_0024_RUNGS + 1)] for role in ROLES}
        if g("reproduction_0024") != r24_expect or g("reference_0024") != REFERENCE_0024:
            void.append("reproduction: reproduction_0024 or reference_0024 is not the recomputed or sealed value")
        r24_drift = {role: [round(a_ - b_, 6) for a_, b_ in zip(r24_expect[role], REFERENCE_0024[role])] for role in ROLES}
        if g("reproduction_0024_drift") != r24_drift:
            void.append("reproduction: reproduction_0024_drift is not the recomputed drift per rung and role")
        s4_expect = {role: rec_reads[f"{SHIFT4}_{role}"]["ext_real_top1"] for role in ROLES}
        if {k: num(v) for k, v in (g("reproduction_shift_arm_0024") or {}).items()} != s4_expect or g("reference_shift_arm_0024") != REFERENCE_SHIFT_0024:
            void.append("reproduction: reproduction_shift_arm_0024 or reference_shift_arm_0024 is not the recomputed or sealed value")
        if {k: num(v) for k, v in (g("reproduction_shift_arm_0024_drift") or {}).items()} != {role: round(s4_expect[role] - REFERENCE_SHIFT_0024[role], 6) for role in ROLES}:
            void.append("reproduction: reproduction_shift_arm_0024_drift is not the recomputed drift per role")
        if num(g("shuffled_label_accuracy_ext")) != rec_reads["null"]["ext_top1"] \
                or num(g("shuffled_label_accuracy_eval")) != rec_reads["null"]["builder_eval_top1"] \
                or num(g("shuffled_label_accuracy_real")) != rec_reads["null"]["ext_real_top1"]:
            void.append("null control: a banked shuffled-label reading is not the recomputed value")
    elif not void:
        void.append("readings: the reader could not recompute the readings")

    # ---- controls: rung 4 reproduces 0021, rungs 1..4 reproduce 0023, rungs 1..7 and the shift arm reproduce 0024; the null sits at chance
    if not void:
        for role in ROLES:
            got = rec_reads[R4 + role]["ext_real_top1"]; drift = round(got - REFERENCE[role], 6)
            if abs(drift) > REPRO_TOLERANCE:
                void.append(f"reproduction: {R4}{role} read {got} against 0021's banked {REFERENCE[role]} (drift {drift} > "
                            f"{REPRO_TOLERANCE}): the fit block, the scoring set or the machinery is not 0021's")
            for k in range(1, N_FIRST + 1):
                got = rec_reads[f"r{k}_{role}"]["ext_real_top1"]; drift = round(got - REFERENCE_FIRST[role][k - 1], 6)
                if abs(drift) > REPRO_TOLERANCE:
                    void.append(f"reproduction: r{k}_{role} read {got} against 0023's banked {REFERENCE_FIRST[role][k - 1]} (drift {drift} > "
                                f"{REPRO_TOLERANCE}): the rung, the scoring set or the machinery is not 0023's")
            for k in range(1, N_0024_RUNGS + 1):
                got = rec_reads[f"r{k}_{role}"]["ext_real_top1"]; drift = round(got - REFERENCE_0024[role][k - 1], 6)
                tol = REPRO_TOLERANCE_R7 if k == N_0024_RUNGS else REPRO_TOLERANCE
                if abs(drift) > tol:
                    void.append(f"reproduction: r{k}_{role} read {got} against 0024's banked {REFERENCE_0024[role][k - 1]} (drift {drift} > "
                                f"{tol}): the rung, the scoring set or the machinery is not 0024's")
            got = rec_reads[f"{SHIFT4}_{role}"]["ext_real_top1"]; drift = round(got - REFERENCE_SHIFT_0024[role], 6)
            if abs(drift) > REPRO_TOLERANCE:
                void.append(f"reproduction: {SHIFT4}_{role} read {got} against 0024's banked shift-arm {REFERENCE_SHIFT_0024[role]} (drift {drift} > "
                            f"{REPRO_TOLERANCE}): 0024's shift arm is not reproduced")
        nx, ne = rec_reads["null"]["ext_top1"], rec_reads["null"]["builder_eval_top1"]
        if nx > CHANCE + NULL_TOLERANCE or ne > CHANCE + NULL_TOLERANCE:
            void.append(f"null control: shuffled labels read {nx} on the extension rows and {ne} on the sealed evaluation rows "
                        f"against chance {CHANCE} + {NULL_TOLERANCE} — the pipeline leaks")

    # ---- the curves, re-derived: rung readings, slopes, the fourth-doubling gain, gains, per-family readings, the floors, the shift arms
    curves_banked = g("curves") or {}
    my_curves = {}; boot = None; lead = None; gain = None; repro_boot = None; my_floors = None; my_s4 = None; my_s8 = None; stab = None
    TOPK = N_RUNGS; R7 = N_0024_RUNGS; TOP = f"r{TOPK}_"; RTOP = f"r{TOPK}"

    def pct(a):
        return [round(float(np.percentile(a, 2.5)), 6), round(float(np.percentile(a, 97.5)), 6)]

    def gain_reading(gn, lo, hi):
        if hi < 0:
            return "FOURTH_DOUBLING_FALLS"
        if gn >= BAR_GAIN - 1e-9 and lo > 0:
            return "FOURTH_DOUBLING_RISES"
        if lo > 0:
            return "FOURTH_DOUBLING_BELOW_RATE"
        return "FOURTH_DOUBLING_NOT_RESOLVED"

    def lead_reading(lo, hi, other):
        if other == "logistic":
            return "MODEL_LEADS" if lo > 0 else "LINEAR_LEADS" if hi < 0 else "NO_SEPARATION"
        return "MODEL_LEADS" if lo > 0 else "TREE_LEADS" if hi < 0 else "NO_SEPARATION"

    if not void:
        for role in ROLES:
            pts = []
            for k, rk in enumerate(rungs_sealed, start=1):
                rr = rec_reads[f"r{k}_{role}"]
                pts.append({"rung": k, "decade": rk["decade"], "n_chunks": rk["n_chunks"], "n_rows": rk["n_rows"],
                            "log2_chunks": rk["log2_chunks"], "ext_real_top1": rr["ext_real_top1"], "ext_real_correct": rr["ext_real_correct"],
                            "builder_eval_top1": rr["builder_eval_top1"],
                            "ext_per_family": {f: rr["ext_per_family"][f] for f in REAL_FAMILIES}})
            ys = [p["ext_real_top1"] for p in pts]; ys2 = ys[N_FIRST - 1:]; ys1 = ys[:N_FIRST]
            c = {"rungs": pts, "complete": True,
                 "slope_per_doubling_second_decade": round(ols_slope(LOG2X_SECOND, ys2), 6),
                 "slope_per_doubling_first_decade": round(ols_slope(LOG2X_FIRST, ys1), 6),
                 "slope_per_doubling_both_decades": round(ols_slope(LOG2X, ys), 6),
                 "slope_per_doubling_second_decade_0024": round(ols_slope(LOG2X_SECOND_0024, ys[N_FIRST - 1:N_0024_RUNGS]), 6),
                 "slope_per_doubling_both_decades_0024": round(ols_slope(LOG2X_0024, ys[:N_0024_RUNGS]), 6),
                 "fourth_doubling_gain": round(ys[TOPK - 1] - ys[R7 - 1], 4),
                 "fourth_doubling_gain_with_rung7_at_reference": round(ys[TOPK - 1] - float(REFERENCE_0024[role][R7 - 1]), 4),
                 "end_to_end_gain_second_decade": round(ys[-1] - ys[N_FIRST - 1], 4),
                 "end_to_end_gain_both_decades": round(ys[-1] - ys[0], 4),
                 "rung_to_rung_gains": [round(ys[i + 1] - ys[i], 4) for i in range(len(ys) - 1)],
                 "per_family_fourth_doubling_gain": {f: round(pts[TOPK - 1]["ext_per_family"][f] - pts[R7 - 1]["ext_per_family"][f], 4) for f in REAL_FAMILIES},
                 "per_family_slope_per_doubling_second_decade": {
                     f: round(ols_slope(LOG2X_SECOND, [p["ext_per_family"][f] for p in pts[N_FIRST - 1:]]), 6) for f in REAL_FAMILIES},
                 "builder_eval_slope_per_doubling_second_decade": round(ols_slope(LOG2X_SECOND, [p["builder_eval_top1"] for p in pts[N_FIRST - 1:]]), 6),
                 "builder_eval_fourth_doubling_gain": round(pts[TOPK - 1]["builder_eval_top1"] - pts[R7 - 1]["builder_eval_top1"], 4)}
            my_curves[role] = c
            bc = curves_banked.get(role) or {}
            for kk in sorted(set(c) | set(bc)):
                if bc.get(kk) != c.get(kk):
                    void.append(f"curve: curves.{role}.{kk} is not the reader's recomputation")
        for role, key in (("model", "model_fourth_doubling_gain"), ("logistic", "logistic_fourth_doubling_gain"), ("depth3_tree", "depth3_tree_fourth_doubling_gain")):
            if num(g(key)) != my_curves[role]["fourth_doubling_gain"]:
                void.append(f"curve: {key} is not the recomputed fourth-doubling gain")
        for role, key in (("model", "model_slope_per_doubling"), ("logistic", "logistic_slope_per_doubling"), ("depth3_tree", "depth3_tree_slope_per_doubling")):
            if num(g(key)) != my_curves[role]["slope_per_doubling_second_decade"]:
                void.append(f"curve: {key} is not the recomputed second-decade slope over rungs {N_FIRST}..{N_RUNGS}")
        top = {role: rec_reads[TOP + role]["ext_real_top1"] for role in ROLES}
        if g("top_rung_top1") != top or num(g("top_rung_model_minus_logistic")) != round(top["model"] - top["logistic"], 4) \
                or num(g("top_rung_model_minus_depth3_tree")) != round(top["model"] - top["depth3_tree"], 4):
            void.append("curve: the banked top-rung readings or differences are not the recomputed values")
        # the floors, refitted on rungs 7 and 8: 0021's clause re-applied (flags)
        my_floors = {}
        for k in (R7, TOPK):
            model_, log_, tree_ = (rec_reads[f"r{k}_{r_}"]["ext_real_top1"] for r_ in ("model", "logistic", "depth3_tree"))
            fl = {fr: rec_reads[f"r{k}_{fr}"]["ext_real_top1"] for fr in FLOOR_ROLES}
            fl["floor_tree3"] = tree_   # B-tree3 is D1: the rung's depth3_tree reading is the tree floor
            best = max(fl.values())
            my_floors[f"r{k}"] = {"floors": fl, "best_floor": best, "best_floor_role": max(fl, key=fl.get), "model": model_, "logistic": log_, "depth3_tree": tree_,
                                  "needed_0021_clause": round(best + 0.05, 4), "clears_0021_clause": bool(model_ >= round(best + 0.05, 4)),
                                  "needed_with_logistic_as_floor": round(max(best, log_) + 0.05, 4),
                                  "clears_with_logistic_as_floor": bool(model_ >= round(max(best, log_) + 0.05, 4))}
        fb = g("floors") or {}
        for k in (f"r{R7}", f"r{TOPK}"):
            if fb.get(k) != my_floors[k]:
                void.append(f"floors: floors.{k} is not the reader's recomputation")
        if not isinstance(fb.get("note"), str):
            void.append("floors: the floors block carries no note")
        # the shift arms, re-derived
        my_s4 = {"arm": PARTITION["shift_arm"], "readings": {}, "difference_from_rung_4": {}, "difference_from_rung_5": {}}
        my_s8 = {"arm": PARTITION["shift_arm_0025"], "readings": {}, "difference_from_rung_4": {}, "difference_from_rung_7": {}, "difference_from_rung_8": {},
                 "difference_from_shift_arm_0024": {}}
        for role in ROLES:
            a4 = rec_reads[f"{SHIFT4}_{role}"]; a8 = rec_reads[f"{SHIFT8}_{role}"]
            my_s4["readings"][role] = {"ext_real_top1": a4["ext_real_top1"], "ext_real_correct": a4["ext_real_correct"], "builder_eval_top1": a4["builder_eval_top1"],
                                       "ext_per_family": {f: a4["ext_per_family"][f] for f in REAL_FAMILIES}}
            my_s4["difference_from_rung_4"][role] = round(a4["ext_real_top1"] - rec_reads[f"{R4}{role}"]["ext_real_top1"], 4)
            my_s4["difference_from_rung_5"][role] = round(a4["ext_real_top1"] - rec_reads[f"r{N_FIRST + 1}_{role}"]["ext_real_top1"], 4)
            my_s8["readings"][role] = {"ext_real_top1": a8["ext_real_top1"], "ext_real_correct": a8["ext_real_correct"], "builder_eval_top1": a8["builder_eval_top1"],
                                       "ext_per_family": {f: a8["ext_per_family"][f] for f in REAL_FAMILIES}}
            for kk, key in ((N_FIRST, "difference_from_rung_4"), (R7, "difference_from_rung_7"), (TOPK, "difference_from_rung_8")):
                my_s8[key][role] = round(a8["ext_real_top1"] - rec_reads[f"r{kk}_{role}"]["ext_real_top1"], 4)
            my_s8["difference_from_shift_arm_0024"][role] = round(a8["ext_real_top1"] - a4["ext_real_top1"], 4)
        for blk, mine, label in (("shift_arm", my_s4, "0024's shift arm"), ("shift_arm_0025", my_s8, "the new shift arm")):
            sb = g(blk) or {}
            for kk in list(mine):
                if sb.get(kk) != mine[kk]:
                    void.append(f"shift arm: {blk}.{kk} is not the reader's recomputation ({label})")
            if not isinstance(sb.get("note"), str):
                void.append(f"shift arm: {blk} carries no note")
        # the bootstraps, from the vectors and the sealed extension chunk layout under 0024's seed
        cid = np.asarray([eci[i] for i in real_idx], np.int64)
        vec = {n: np.asarray([scores[n][n_eval + i] for i in real_idx], np.int8) for n in ORDER if n != "null"}
        # (a) 0024's intervals, reproduced exactly
        sl24 = slope_bootstrap({role: [vec[f"r{k}_{role}"] for k in range(N_FIRST, N_0024_RUNGS + 1)] for role in ROLES}, LOG2X_SECOND_0024, cid, N_BOOT, BOOT_SEED)
        repro_boot = {"slope_bootstrap_0024": {role: {"ci95": pct(sl24[role]), "n_boot": N_BOOT, "seed": BOOT_SEED, "mean": round(float(sl24[role].mean()), 6)} for role in ROLES},
                      "lead_0024": {}}
        for a_, b_ in (("model", "logistic"), ("model", "depth3_tree")):
            dd = sl24[a_] - sl24[b_]
            repro_boot["slope_bootstrap_0024"][f"{a_}_minus_{b_}"] = {"ci95": pct(dd), "paired": True, "share_of_resamples_with_model_ahead": round(float((dd > 0).mean()), 4)}
        for k in (N_0024_RUNGS, N_FIRST):
            for a_, b_ in (("model", "logistic"), ("model", "depth3_tree")):
                dv = paired_lead_bootstrap(vec[f"r{k}_{a_}"], vec[f"r{k}_{b_}"], cid, N_BOOT, BOOT_SEED); lo, hi = pct(dv)
                repro_boot["lead_0024"][f"r{k}_{a_}_minus_{b_}"] = {
                    "point": round(rec_reads[f"r{k}_{a_}"]["ext_real_top1"] - rec_reads[f"r{k}_{b_}"]["ext_real_top1"], 4), "ci95": [lo, hi],
                    "n_boot": N_BOOT, "seed": BOOT_SEED, "share_of_resamples_with_model_ahead": round(float((dv > 0).mean()), 4), "reading": lead_reading(lo, hi, b_)}
        eq_slope = all(repro_boot["slope_bootstrap_0024"].get(k) == v for k, v in REFERENCE_BOOT_0024["slope_bootstrap"].items())
        eq_lead = all(repro_boot["lead_0024"].get(k) == v for k, v in REFERENCE_BOOT_0024["lead_at_top"].items())
        repro_boot["equals_0024s_banked"] = {"slope_bootstrap": bool(eq_slope), "lead_at_top": bool(eq_lead)}
        rb = g("reproduction_bootstrap_0024") or {}
        for kk in ("slope_bootstrap_0024", "lead_0024", "equals_0024s_banked"):
            if rb.get(kk) != repro_boot[kk]:
                void.append(f"reproduction: reproduction_bootstrap_0024.{kk} is not the reader's recomputation")
        if not isinstance(rb.get("unit"), str):
            void.append("reproduction: reproduction_bootstrap_0024 carries no unit")
        if not (eq_slope and eq_lead):
            void.append("reproduction: 0024's banked slope and lead intervals do not reproduce exactly from this run's vectors under 0024's seed: the "
                        "instrument is not 0024's")
        # (b) this run's intervals
        sl = slope_bootstrap({role: [vec[f"r{k}_{role}"] for k in range(N_FIRST, N_RUNGS + 1)] for role in ROLES}, LOG2X_SECOND, cid, N_BOOT, BOOT_SEED)
        sl_all = slope_bootstrap({role: [vec[f"r{k}_{role}"] for k in range(1, N_RUNGS + 1)] for role in ROLES}, LOG2X, cid, N_BOOT, BOOT_SEED)
        boot = {role: {"ci95": pct(sl[role]), "n_boot": N_BOOT, "seed": BOOT_SEED, "mean": round(float(sl[role].mean()), 6)} for role in ROLES}
        for a_, b_ in (("model", "logistic"), ("model", "depth3_tree")):
            dd = sl[a_] - sl[b_]
            boot[f"{a_}_minus_{b_}"] = {"ci95": pct(dd), "paired": True, "share_of_resamples_with_model_ahead": round(float((dd > 0).mean()), 4)}
        boot["both_decades"] = {role: {"ci95": pct(sl_all[role]), "n_boot": N_BOOT, "seed": BOOT_SEED, "mean": round(float(sl_all[role].mean()), 6)} for role in ROLES}
        banked_boot = g("slope_bootstrap") or {}
        for kk in list(boot):
            if banked_boot.get(kk) != boot[kk]:
                void.append(f"curve: slope_bootstrap.{kk} is not the reader's recomputation")
        if not isinstance(banked_boot.get("unit"), str):
            void.append("curve: slope_bootstrap carries no unit")
        gain = {}
        for role in ROLES:
            dv = paired_lead_bootstrap(vec[f"r{N_RUNGS}_{role}"], vec[f"r{N_0024_RUNGS}_{role}"], cid, N_BOOT, BOOT_SEED); lo, hi = pct(dv)
            point = round(rec_reads[f"r{N_RUNGS}_{role}"]["ext_real_top1"] - rec_reads[f"r{N_0024_RUNGS}_{role}"]["ext_real_top1"], 4)
            gain[role] = {"point": point, "ci95": [lo, hi], "n_boot": N_BOOT, "seed": BOOT_SEED,
                          "share_of_resamples_with_a_gain": round(float((dv > 0).mean()), 4), "reading": gain_reading(point, lo, hi)}
        gain["verdict_role"] = "model"; gain["bar"] = BAR_GAIN
        bg = g("fourth_doubling") or {}
        for kk in list(gain):
            if bg.get(kk) != gain[kk]:
                void.append(f"gain: fourth_doubling.{kk}={bg.get(kk)!r} is not the reader's recomputation {gain[kk]!r}")
        if not isinstance(bg.get("unit"), str):
            void.append("gain: fourth_doubling carries no unit")
        lead = {}
        for k in (N_RUNGS, N_0024_RUNGS, N_FIRST):
            for a_, b_ in (("model", "logistic"), ("model", "depth3_tree")):
                dv = paired_lead_bootstrap(vec[f"r{k}_{a_}"], vec[f"r{k}_{b_}"], cid, N_BOOT, BOOT_SEED); lo, hi = pct(dv)
                lead[f"r{k}_{a_}_minus_{b_}"] = {
                    "point": round(rec_reads[f"r{k}_{a_}"]["ext_real_top1"] - rec_reads[f"r{k}_{b_}"]["ext_real_top1"], 4), "ci95": [lo, hi],
                    "n_boot": N_BOOT, "seed": BOOT_SEED, "share_of_resamples_with_model_ahead": round(float((dv > 0).mean()), 4), "reading": lead_reading(lo, hi, b_)}
        dv = paired_lead_bootstrap(vec[f"{SHIFT8}_model"], vec[f"{SHIFT4}_model"], cid, N_BOOT, BOOT_SEED)
        lead["s8_minus_s4_model"] = {"point": round(rec_reads[f"{SHIFT8}_model"]["ext_real_top1"] - rec_reads[f"{SHIFT4}_model"]["ext_real_top1"], 4),
                                     "ci95": pct(dv), "n_boot": N_BOOT, "seed": BOOT_SEED, "informational": True}
        banked_lead = g("lead_at_top") or {}
        for kk in list(lead):
            if banked_lead.get(kk) != lead[kk]:
                void.append(f"lead: lead_at_top.{kk}={banked_lead.get(kk)!r} is not the reader's recomputation {lead[kk]!r}")
        if not isinstance(banked_lead.get("unit"), str) or banked_lead.get("verdict_pair") != f"{TOP}model_minus_logistic":
            void.append("lead: lead_at_top carries no unit or names a verdict pair other than the top rung's model minus logistic")
        # (c) seed stability of the two verdict intervals
        stab = {"seeds": [BOOT_SEED + 1 + i for i in range(STABILITY_SEEDS)], "gain_readings": {}, "lead_readings": {}}
        for s_ in stab["seeds"]:
            dg = paired_lead_bootstrap(vec[f"r{N_RUNGS}_model"], vec[f"r{N_0024_RUNGS}_model"], cid, N_BOOT, s_); lo, hi = pct(dg)
            stab["gain_readings"][str(s_)] = gain_reading(gain["model"]["point"], lo, hi)
            dl = paired_lead_bootstrap(vec[f"r{N_RUNGS}_model"], vec[f"r{N_RUNGS}_logistic"], cid, N_BOOT, s_); lo, hi = pct(dl)
            stab["lead_readings"][str(s_)] = lead_reading(lo, hi, "logistic")
        stab["n_seeds_with_another_gain_reading"] = sum(1 for v in stab["gain_readings"].values() if v != gain["model"]["reading"])
        stab["n_seeds_with_another_lead_reading"] = sum(1 for v in stab["lead_readings"].values() if v != lead[f"{TOP}model_minus_logistic"]["reading"])
        bs = g("seed_stability") or {}
        for kk in list(stab):
            if bs.get(kk) != stab[kk]:
                void.append(f"stability: seed_stability.{kk} is not the reader's recomputation")
        if not isinstance(bs.get("note"), str):
            void.append("stability: seed_stability carries no note")

    # the measured reading (rung 8 minus this run's rung 7) and the sensitivity reading (rung 8 minus 0024's banked rung-7 reading, on the
    # same paired interval). scope.design.how_the_sensitivity_gain_is_read: if the two straddle a reading boundary, every document states
    # both and the published reading - the verdict's gain part - is the less flattering one, named as such; its point is the one that reads so
    gain_measured = gain["model"]["reading"] if gain is not None and not void else None
    gain_read = gain_measured; gain_sens = None; sens_point = None; gain_pub_point = None
    if gain_measured is not None:
        sens_point = my_curves["model"]["fourth_doubling_gain_with_rung7_at_reference"]
        gain_sens = gain_reading(sens_point, gain["model"]["ci95"][0], gain["model"]["ci95"][1])
        gain_read = min((gain_measured, gain_sens), key=GAIN_READINGS_LEAST_FLATTERING_FIRST.index)
        gain_pub_point = gain["model"]["point"] if gain_read == gain_measured else sens_point
    gain_straddle = gain_measured is not None and gain_sens != gain_measured
    lead_read = lead[f"{TOP}model_minus_logistic"]["reading"] if lead is not None and not void else None

    flags = None
    if not void:
        n_iter = {n: (fits[n].get("fit_info") or {}).get("n_iter") for n in ORDER}
        cap = {n: MAX_ITER.get(role_of(n) if n != "null" else "model", 0) for n in ORDER}
        capped = sorted(n for n in ORDER if _int(n_iter[n]) and cap[n] > 0 and n_iter[n] >= cap[n])
        capped_top = sorted(n for n in capped if n.startswith(TOP))
        capped_r7 = sorted(n for n in capped if n.startswith(f"r{R7}_"))
        rung_table = [{"rung": k, "decade": rk["decade"], "n_chunks": rk["n_chunks"], "n_rows": rk["n_rows"],
                       **{role: rec_reads[f"r{k}_{role}"]["ext_real_top1"] for role in ROLES}} for k, rk in enumerate(rungs_sealed, start=1)]
        gm = gain["model"]; lt = lead[f"{TOP}model_minus_logistic"]
        by_rung = {role: [p["ext_real_top1"] for p in my_curves[role]["rungs"]] for role in ROLES}
        two_decade = {role: {"slope_per_doubling": my_curves[role]["slope_per_doubling_both_decades"], "ci95": boot["both_decades"][role]["ci95"]} for role in ROLES}
        flags = {"gain_reading": gain_read, "lead_at_top": lead_read,
                 "roles_at_iteration_cap_at_the_top_rung": capped_top, "roles_at_iteration_cap_at_rung_7": capped_r7,
                 "lead_at_top_is_a_recipe_comparison": not capped_top,
                 "gain_is_a_recipe_reading": not any(f"r{k}_model" in capped for k in (R7, TOPK)),
                 "fourth_doubling_gain": gm["point"], "fourth_doubling_gain_ci95_paired": gm["ci95"],
                 "fourth_doubling_gain_by_role": {role: gain[role]["point"] for role in ROLES},
                 "fourth_doubling_gain_ci95_by_role": {role: gain[role]["ci95"] for role in ROLES},
                 "fourth_doubling_reading_by_role": {role: gain[role]["reading"] for role in ROLES},
                 "fourth_doubling_gain_with_rung7_at_0024s_reading": {role: my_curves[role]["fourth_doubling_gain_with_rung7_at_reference"] for role in ROLES},
                 "fourth_doubling_reading_with_rung7_at_0024s_reading": gain_sens,
                 "fourth_doubling_measured_and_sensitivity_readings": {
                     "measured": {"point": gm["point"], "rung7_reading": by_rung["model"][R7 - 1], "reading": gain_measured},
                     "with_rung7_at_0024s_reading": {"point": sens_point, "rung7_reading": REFERENCE_0024["model"][R7 - 1], "reading": gain_sens},
                     "interval": gm["ci95"], "straddle_a_reading_boundary": gain_straddle, "published_reading": gain_read, "published_point": gain_pub_point,
                     "published_is": ("the less flattering one" if gain_straddle else "the reading both give")},
                 "per_family_fourth_doubling_gain": {role: my_curves[role]["per_family_fourth_doubling_gain"] for role in ROLES},
                 "two_decade_slope_per_doubling": two_decade,
                 "two_decade_slope_is": f"the OLS slope over all eight rungs ({round(PARTITION['doublings_spanned'] * math.log10(2), 4)} decades) with its scored-chunk interval; seven of its eight points "
                                        "were banked by 0023 and 0024 before this run, so it is a flag quoted only beside the fourth-doubling reading, "
                                        "never a rise of its own; the span meets 0003's two-decade scope rule only in the sense that the rule asked for two decades of data; its one-corpus, one-seed terms are not met by this curve, whose first decade is the scored files' own chunks",
                 "second_decade_slope_per_doubling": {role: my_curves[role]["slope_per_doubling_second_decade"] for role in ROLES},
                 "second_decade_slope_ci95": {role: boot[role]["ci95"] for role in ROLES},
                 "second_decade_slope_0024_reproduced": {role: my_curves[role]["slope_per_doubling_second_decade_0024"] for role in ROLES},
                 "first_decade_slope_per_doubling": {role: my_curves[role]["slope_per_doubling_first_decade"] for role in ROLES},
                 "slope_model_minus_logistic_second_decade": round(my_curves["model"]["slope_per_doubling_second_decade"] - my_curves["logistic"]["slope_per_doubling_second_decade"], 6),
                 "slope_model_minus_logistic_ci95_paired": boot["model_minus_logistic"]["ci95"],
                 "share_of_resamples_with_model_ahead_of_logistic": boot["model_minus_logistic"]["share_of_resamples_with_model_ahead"],
                 "share_is": "a description of the resamples, not a probability that the model is better",
                 "lead_model_minus_logistic_at_top": lt, "lead_model_minus_logistic_at_rung7": lead[f"r{R7}_model_minus_logistic"],
                 "lead_model_minus_logistic_at_rung4": lead[f"{R4}model_minus_logistic"],
                 "lead_model_minus_depth3_tree_at_top": lead[f"{TOP}model_minus_depth3_tree"],
                 "model_minus_logistic_by_rung": [round(by_rung["model"][i] - by_rung["logistic"][i], 4) for i in range(N_RUNGS)],
                 "end_to_end_gain_second_decade": {role: my_curves[role]["end_to_end_gain_second_decade"] for role in ROLES},
                 "end_to_end_gain_both_decades": {role: my_curves[role]["end_to_end_gain_both_decades"] for role in ROLES},
                 "rung_to_rung_gains": {role: my_curves[role]["rung_to_rung_gains"] for role in ROLES},
                 "per_family_slope_per_doubling_second_decade": {role: my_curves[role]["per_family_slope_per_doubling_second_decade"] for role in ROLES},
                 "builder_eval_fourth_doubling_gain": {role: my_curves[role]["builder_eval_fourth_doubling_gain"] for role in ROLES},
                 "rung_table": rung_table, "doublings_spanned": PARTITION["doublings_spanned"],
                 "doublings_spanned_second_decade": PARTITION["doublings_spanned_second_decade"],
                 "decades_spanned": round(PARTITION["doublings_spanned"] * math.log10(2), 4),
                 "floors": my_floors,
                 "shift_arm_0024": {"readings_ext_real_top1": {role: my_s4["readings"][role]["ext_real_top1"] for role in ROLES},
                                    "difference_from_rung_4": my_s4["difference_from_rung_4"], "difference_from_rung_5": my_s4["difference_from_rung_5"]},
                 "shift_arm_0025": {"readings_ext_real_top1": {role: my_s8["readings"][role]["ext_real_top1"] for role in ROLES},
                                    "difference_from_rung_4": my_s8["difference_from_rung_4"], "difference_from_rung_7": my_s8["difference_from_rung_7"],
                                    "difference_from_rung_8": my_s8["difference_from_rung_8"], "difference_from_shift_arm_0024": my_s8["difference_from_shift_arm_0024"],
                                    "s8_minus_s4_model_ci95_paired": lead["s8_minus_s4_model"]["ci95"],
                                    "composition_per_family": PARTITION["shift_arm_0025"]["composition_per_family"],
                                    "n_chunks": PARTITION["shift_arm_0025"]["n_chunks"], "n_rows": PARTITION["shift_arm_0025"]["n_rows"]},
                 "rung_8_added_composition_per_family": rungs_sealed[TOPK - 1]["added_composition_per_family"],
                 "seed_stability": {"n_seeds": STABILITY_SEEDS, "n_seeds_with_another_gain_reading": stab["n_seeds_with_another_gain_reading"],
                                    "n_seeds_with_another_lead_reading": stab["n_seeds_with_another_lead_reading"]},
                 "reproduction_drift_rung_4": {role: round(rec_reads[R4 + role]["ext_real_top1"] - REFERENCE[role], 6) for role in ROLES},
                 "reproduction_0024_drift": {role: [round(rec_reads[f"r{k}_{role}"]["ext_real_top1"] - REFERENCE_0024[role][k - 1], 6) for k in range(1, N_0024_RUNGS + 1)] for role in ROLES},
                 "reproduction_shift_arm_0024_drift": {role: round(rec_reads[f"{SHIFT4}_{role}"]["ext_real_top1"] - REFERENCE_SHIFT_0024[role], 6) for role in ROLES},
                 "reproduction_bootstrap_0024_exact": repro_boot["equals_0024s_banked"],
                 "checkpoints_cross_checked": ckpt_checked,
                 "null_real_top1": rec_reads["null"]["ext_real_top1"],
                 "n_iter_by_name": n_iter,
                 "at_iteration_cap": {n: (n_iter[n] >= cap[n]) for n in ORDER if _int(n_iter[n]) and cap[n] > 0},
                 "roles_at_iteration_cap": capped}

    top_read = rec_reads[TOP + "model"]["ext_real_top1"] if not void else None
    by_rung = {role: [p["ext_real_top1"] for p in my_curves[role]["rungs"]] for role in ROLES} if not void else None
    plaintexts = [r["n_chunks"] for r in rungs_sealed]
    if void:
        verdict, meaning = "VOID", ("A validity or control clause fails, or the artifact is incomplete. This run says nothing "
                                    "about the fourth doubling of real plaintexts in either direction.")
    else:
        verdict = f"{gain_read}_{lead_read}"
        gm = gain["model"]; lt = lead[f"{TOP}model_minus_logistic"]
        # the sealed rules' own words in the same sentence as the reading they touch: the gain rule's '(the model at its iteration cap at
        # rung N)' - the gain is the model's, so only the model's cap at rung 7 or 8 touches it - and the lead rule's '(the <role> at its
        # iteration cap at rung 8 (the top rung))' - the lead is model minus logistic at rung 8, so either one's cap there does
        cap_note = ("".join(" " + LEAD_CAP_NOTE.replace("<role>", n[len(TOP):]) for n in flags["roles_at_iteration_cap_at_the_top_rung"])
                    + ("; not a recipe comparison" if flags["roles_at_iteration_cap_at_the_top_rung"] else ""))
        gain_cap_rungs = [k for k in (R7, TOPK) if f"r{k}_model" in flags["roles_at_iteration_cap"]]
        gain_cap = ("".join(" " + GAIN_CAP_NOTE.replace(" N)", f" {k})") for k in gain_cap_rungs)
                    + ("; the cap is part of the sealed recipe and is never raised, and the gain is read as is, not as a recipe reading"
                       if gain_cap_rungs else ""))
        gp = gain_pub_point   # the point that gives the published reading: the measured one unless the less flattering reading is the sensitivity one
        gain_text = {"FOURTH_DOUBLING_RISES": f"the fourth doubling buys the model {gp} on the real-family rows (paired interval {gm['ci95']}, entirely above 0), at or above the record's rate of {BAR_GAIN} per doubling",
                     "FOURTH_DOUBLING_BELOW_RATE": f"the fourth doubling buys the model {gp} on the real-family rows (paired interval {gm['ci95']}, entirely above 0), below the record's rate of {BAR_GAIN} per doubling: a rise below the record's rate",
                     "FOURTH_DOUBLING_NOT_RESOLVED": f"the fourth doubling moves the model by {gp} on the real-family rows with a paired interval {gm['ci95']} that includes 0: whether the fourth doubling bought anything is not resolved by the scored chunks at this size, never read as 'flat' or 'equal'",
                     "FOURTH_DOUBLING_FALLS": f"the fourth doubling moves the model by {gp} on the real-family rows with a paired interval {gm['ci95']} entirely below 0: adding the fourth doubling's files of the same kinds lowered the model's reading on the original files"}[gain_read] + gain_cap
        # scope.design.how_the_sensitivity_gain_is_read: on a straddle both readings are stated and the published one is named as the less flattering
        straddle_text = (f"; the gain measured against this run's rung {R7} ({by_rung['model'][R7 - 1]}) is {gm['point']} and reads {gain_measured}, the gain with rung "
                         f"{R7} held at 0024's banked {REFERENCE_0024['model'][R7 - 1]} is {sens_point} and reads {gain_sens}: the two straddle a reading boundary, and "
                         f"the published reading, {gain_read}, is the less flattering one" if gain_straddle else "")
        pf_text = ", ".join(f"{f} {v}" for f, v in my_curves["model"]["per_family_fourth_doubling_gain"].items())
        roles_text = (f"the standardised logistic's fourth-doubling gain is {gain['logistic']['point']} (paired interval {gain['logistic']['ci95']}) and the depth-3 "
                      f"tree's {gain['depth3_tree']['point']} (paired interval {gain['depth3_tree']['ci95']})")
        lead_text = {"MODEL_LEADS": f"at rung {N_RUNGS} the model leads the standardised logistic by {lt['point']} (paired interval {lt['ci95']}, entirely above 0)",
                     "LINEAR_LEADS": f"at rung {N_RUNGS} the standardised logistic leads the model by {round(-lt['point'], 4)} (paired interval of model minus logistic {lt['ci95']}, entirely below 0): a rule a person can write out has overtaken the boosted recipe",
                     "NO_SEPARATION": f"at rung {N_RUNGS} model minus logistic is {lt['point']} with a paired interval {lt['ci95']} that includes 0: the two are not separated at this size, never read as 'equal'"}[lead_read] + cap_note
        stab_text = (f" Under {STABILITY_SEEDS} other bootstrap seeds the gain reading would have differed {flags['seed_stability']['n_seeds_with_another_gain_reading']} "
                     f"times and the lead reading {flags['seed_stability']['n_seeds_with_another_lead_reading']} times (a flag).")
        # stop_rules[5]: what the fourth doubling is and what its files are per family, from the sealed composition of rung 8's added plaintexts
        comp8 = rungs_sealed[TOPK - 1]["added_composition_per_family"]
        fl7 = my_floors[f"r{R7}"]
        comp_text = (f" The fourth doubling is one doubling ({plaintexts[TOPK - 1]} against {plaintexts[R7 - 1]} plaintexts) of other files of the same five "
                     f"families above 0024's top rung: {composition_phrase(comp8)} (of each family's added plaintexts, from new files: "
                     + ", ".join(f"{f} {c['from_new_files']} of {c['n']}" for f, c in comp8.items())
                     + "; the rest are other chunks of 0024's projects, from its pool and its archives' unused chunks).")
        meaning = (f"{verdict}: {gain_text}{straddle_text}; per family the model's fourth-doubling gain is {pf_text}, and {roles_text}; {lead_text}. "
                   f"At 4096 bytes, on nested rungs of {plaintexts[0]} to {plaintexts[-1]} real plaintexts "
                   f"({PARTITION['doublings_spanned']} doublings, {flags['decades_spanned']} decades: rungs 1..{N_FIRST} are 0023's chunks of the five 0018 pinned files, rungs "
                   f"{N_FIRST + 1}..{N_0024_RUNGS} 0024's other files of the same five families, rung {N_RUNGS} one more exact doubling of other files), 0021's three "
                   f"fixed recipes read, per rung: the model {by_rung['model']}, the standardised logistic {by_rung['logistic']}, the depth-3 tree "
                   f"{by_rung['depth3_tree']} on the {N_REAL} real-family rows.{comp_text} Seven of the eight points were banked before this run, so the two-decade slope "
                   f"(model {flags['two_decade_slope_per_doubling']['model']['slope_per_doubling']} per doubling, interval {flags['two_decade_slope_per_doubling']['model']['ci95']}) "
                   f"is a flag quoted only beside the fourth-doubling reading, never a rise of its own; the span meets 0003's two-decade scope rule only in "
                   f"the sense that the rule asked for two decades of data; its one-corpus, one-seed terms are not met by this curve, whose first decade "
                   f"is the scored files' own chunks. Rungs 1..{N_0024_RUNGS} and 0024's shift arm reproduced 0024's readings (rung {N_0024_RUNGS} within {REPRO_TOLERANCE_R7}) and "
                   f"0024's bootstrap intervals exactly. The floors refitted at rung {N_RUNGS} put 0021's clause at {my_floors[RTOP]['needed_0021_clause']} and "
                   f"the model's {top_read} "
                   + ("clears it: 0021's margin re-applied at sixteen times 0021's plaintexts, informational, revising nothing of 0021's verdict"
                      if my_floors[RTOP]['clears_0021_clause'] else
                      "does not clear it: at sixteen times 0021's plaintexts the boosted recipe is still within 0.05 of the best rule a person could write out")
                   + f" (with the standardised logistic among the floors the clause is {my_floors[RTOP]['needed_with_logistic_as_floor']}, "
                   + ("cleared" if my_floors[RTOP]['clears_with_logistic_as_floor'] else "not cleared")
                   + f"; at rung {R7} the two clauses are {fl7['needed_0021_clause']} and {fl7['needed_with_logistic_as_floor']} against the model's "
                   f"{fl7['model']}, " + ("cleared" if fl7['clears_0021_clause'] else "not cleared") + " and "
                   + ("cleared" if fl7['clears_with_logistic_as_floor'] else "not cleared")
                   + f"). 0024's shift arm (rung {N_FIRST + 1}'s new plaintexts alone at rung 4's count, reproduced) reads {flags['shift_arm_0024']['readings_ext_real_top1']}, "
                   f"against rung 4 by {flags['shift_arm_0024']['difference_from_rung_4']}; the new shift arm (rung {N_RUNGS}'s plaintexts from 0025's corpus alone at rung 4's "
                   f"count: the new files and 0024's archives' unused chunks) reads {flags['shift_arm_0025']['readings_ext_real_top1']}, against rung 4 by "
                   f"{flags['shift_arm_0025']['difference_from_rung_4']} and against 0024's shift arm by {flags['shift_arm_0025']['difference_from_shift_arm_0024']} "
                   f"(the model's paired interval {flags['shift_arm_0025']['s8_minus_s4_model_ci95_paired']}).{stab_text} "
                   f"Not a transfer reading: every rung holds the scored files' own unscored chunks; the added plaintexts are other files of the same families; "
                   f"nothing fitted shares a byte, a kilobyte run, a chunk id or a source-chunk hash with anything scored; the intervals are over the scored chunks "
                   f"only and do not resample the fit side or the draw of the rung's plaintexts. Nothing here revises 0003, 0014, 0015, 0016, 0017, 0018, 0019, "
                   f"0021, 0022, 0023 or 0024, and nothing here establishes a buyer. Nothing beyond the top rung is banked.")
    result = {
        "schema": "raise-v1/realcurve3_4096_verdict/1",
        "preregistration": PREREG,
        "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "verdict": verdict,
        "verdict_components": ({"gain": gain_read, "lead": lead_read} if not void else None),
        "meaning": meaning,
        "validity_failed_clauses": void,
        "gain_reading": gain_read,
        "lead_reading": lead_read,
        "bar_applied": {"gain_per_doubling": BAR_GAIN, "gain_rule": GAIN_RULE, "lead_rule": LEAD_RULE, "n_boot": N_BOOT, "bootstrap_seed": BOOT_SEED,
                        "doublings_spanned": PARTITION["doublings_spanned"], "doublings_spanned_second_decade": PARTITION["doublings_spanned_second_decade"],
                        "decades_spanned": round(PARTITION["doublings_spanned"] * math.log10(2), 4), "log2_chunks": LOG2X,
                        "rungs": [{k: r[k] for k in ("rung", "decade", "n_chunks", "n_rows")} for r in rungs_sealed],
                        "n_real_rows": N_REAL, "fit_rows": FIT["n_rows"], "fit_source_chunks": FIT["n_chunks"],
                        "fit2_rows": FIT2["n_rows"], "fit2_source_chunks": FIT2["n_chunks"], "fit3_rows": FIT3["n_rows"], "fit3_source_chunks": FIT3["n_chunks"]},
        "model_fourth_doubling_gain": gain["model"]["point"] if (gain and not void) else None,
        "model_fourth_doubling_gain_ci95": gain["model"]["ci95"] if (gain and not void) else None,
        "logistic_fourth_doubling_gain": gain["logistic"]["point"] if (gain and not void) else None,
        "depth3_tree_fourth_doubling_gain": gain["depth3_tree"]["point"] if (gain and not void) else None,
        "model_slope_per_doubling": my_curves["model"]["slope_per_doubling_second_decade"] if not void else None,
        "model_slope_ci95": boot["model"]["ci95"] if (boot and not void) else None,
        "model_two_decade_slope_per_doubling": my_curves["model"]["slope_per_doubling_both_decades"] if not void else None,
        "model_two_decade_slope_ci95": boot["both_decades"]["model"]["ci95"] if (boot and not void) else None,
        "logistic_slope_per_doubling": my_curves["logistic"]["slope_per_doubling_second_decade"] if not void else None,
        "depth3_tree_slope_per_doubling": my_curves["depth3_tree"]["slope_per_doubling_second_decade"] if not void else None,
        "curves": my_curves if not void else None,
        "fourth_doubling": gain if not void else None,
        "slope_bootstrap": boot if not void else None,
        "lead_at_top": lead if not void else None,
        "reproduction_bootstrap_0024": repro_boot if not void else None,
        "seed_stability": stab if not void else None,
        "floors": my_floors if not void else None,
        "shift_arm": my_s4 if not void else None,
        "shift_arm_0025": my_s8 if not void else None,
        "flags": flags,
        "model_real_top1_by_rung": by_rung["model"] if not void else None,
        "model_real_top1_top_rung": top_read,
        "ext_real_top1": {n: rec_reads[n]["ext_real_top1"] for n in ORDER} if not void else None,
        "ext_real_correct": {n: rec_reads[n]["ext_real_correct"] for n in ORDER} if not void else None,
        "ext_top1": {n: rec_reads[n]["ext_top1"] for n in ORDER} if not void else None,
        "ext_per_family": {n: rec_reads[n]["ext_per_family"] for n in ORDER} if not void else None,
        "builder_eval_top1": {n: rec_reads[n]["builder_eval_top1"] for n in ORDER} if not void else None,
        "reproduction_top1": {role: rec_reads[R4 + role]["ext_real_top1"] for role in ROLES} if not void else None,
        "reproduction_reference": REFERENCE,
        "reproduction_drift": (flags or {}).get("reproduction_drift_rung_4"),
        "reproduction_first_decade": ({role: [rec_reads[f"r{k}_{role}"]["ext_real_top1"] for k in range(1, N_FIRST + 1)] for role in ROLES} if not void else None),
        "reproduction_first_decade_reference": REFERENCE_FIRST,
        "reproduction_0024": ({role: [rec_reads[f"r{k}_{role}"]["ext_real_top1"] for k in range(1, N_0024_RUNGS + 1)] for role in ROLES} if not void else None),
        "reproduction_0024_reference": REFERENCE_0024,
        "reproduction_shift_arm_0024": ({role: rec_reads[f"{SHIFT4}_{role}"]["ext_real_top1"] for role in ROLES} if not void else None),
        "reproduction_shift_arm_0024_reference": REFERENCE_SHIFT_0024,
        "shuffled_label_accuracy_ext": rec_reads["null"]["ext_top1"] if not void else None,
        "shuffled_label_accuracy_eval": rec_reads["null"]["builder_eval_top1"] if not void else None,
        "shuffled_label_accuracy_real": rec_reads["null"]["ext_real_top1"] if not void else None,
        "checkpoints_cross_checked": ckpt_checked,
        "ext_rows_per_family": EXT["rows_per_family"],
        "fit_rows_per_family": FIT["rows_per_family"],
        "fit2_rows_per_family": FIT2["rows_per_family"],
        "fit3_rows_per_family": FIT3["rows_per_family"],
        "informational_only": "the flags, the two-decade and second-decade slopes and their intervals, the other roles' gains, the per-family "
                              "gains and slopes, the sensitivity gain, the floors, both shift arms, the leads at rungs 7 and 4 and over the tree, "
                              "the seed-stability counts and the artifact's cluster intervals are informational: not a verdict, not quotable as a "
                              "rise of their own. The verdict is the `verdict` field: its gain part is read on the model's fourth-doubling gain and "
                              "its paired scored-chunk interval by the sealed four-way rule - and where the same gain with rung 7 held at 0024's "
                              "banked reading reads otherwise, the less flattering of the two readings is published, named as such - its lead part "
                              "on the sealed lead rule at rung 8.",
        "is_a_transfer_reading": False,
        "establishes_a_buyer": False,
        "revises_0003_0014_0015_0016_0017_0018_0019_0021_0022_0023_0024": False,
        "read": {k: g(k) for k in (
            "preregistration", "smoke", "stage", "complete", "missing_roles", "model_fourth_doubling_gain", "model_slope_per_doubling",
            "logistic_slope_per_doubling", "depth3_tree_slope_per_doubling", "shuffled_label_accuracy_ext",
            "shuffled_label_accuracy_eval", "chance_accuracy", "n_ext_rows", "n_ext_real_rows", "n_eval_rows", "n_classes",
            "n_rungs", "doublings_0024", "doublings_0025", "curve_sha256")},
        "readings_banked": reads,
    }
    _write(result)

    print("READER 0025 — two decades of real plaintexts at 4096: the fourth doubling of other files, nested on 0024's rungs")
    for k, v in result["read"].items():
        print(f"  {k:<40} {v}")
    if not void:
        print(f"  {'model top-1 by rung':<40} {result['model_real_top1_by_rung']} over plaintexts {[r['n_chunks'] for r in rungs_sealed]}")
        print(f"  {'fourth-doubling gain (model)':<40} {gain['model']['point']} paired {gain['model']['ci95']} -> {gain_measured}; logistic {gain['logistic']['point']}, tree {gain['depth3_tree']['point']}")
        print(f"  {'... with rung 7 at 0024s reading':<40} {sens_point} -> {gain_sens}; published {gain_read}"
              + (" (the two straddle a reading boundary: the less flattering one)" if gain_straddle else ""))
        print(f"  {'lead at the top rung':<40} {lead[f'{TOP}model_minus_logistic']}")
        print(f"  {'two-decade slope (model)':<40} {flags['two_decade_slope_per_doubling']['model']}; 0024 intervals reproduced {repro_boot['equals_0024s_banked']}")
        print(f"  {'new shift arm minus rung 4 / minus s4':<40} {flags['shift_arm_0025']['difference_from_rung_4']} / {flags['shift_arm_0025']['difference_from_shift_arm_0024']}")
        print(f"  {'floors at rung 8':<40} best {my_floors[RTOP]['best_floor_role']} {my_floors[RTOP]['best_floor']}, needed {my_floors[RTOP]['needed_0021_clause']}, model {top_read}")
    if void:
        print(f"\n  VALIDITY FAILED CLAUSES ({len(void)}):")
        for m in void:
            print(f"    · {m}")
    print(f"\n  VERDICT: {verdict}\n  {meaning}")
    print("  This does not establish a buyer, and was never capable of doing so.")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
