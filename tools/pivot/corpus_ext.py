#!/usr/bin/env python3
"""Evaluation-only extension corpus: content families the corpus builder never produced (preregistration 0018).

The label factory is the builder's, unchanged: the same 26 (implementation, level) configurations, the same
32768-byte source chunks, the same mid-stream carve, the same feature extractor (tools/pivot/corpus.py and
tools/pivot/features.py are imported, not copied). What differs is the content: eight families that share
nothing with the builder's seven parametric generators and one Gutenberg family -

  real, pinned by sha256 (tools/pivot/ext_source_pins.json; fetched by tools/pivot/fetch_ext_sources.sh):
    py_src    CPython 3.11.9  Lib/**/*.py   (PSF-2.0)
    rst_doc   CPython 3.11.9  Doc/**/*.rst  (PSF-2.0)
    c_src     SQLite 3.45.3 amalgamation .c/.h (public domain)
    rfc_txt   RFC texts from rfc-editor.org (IETF Trust Legal Provisions)
    pe_bin    *.dll / *.exe / *.pyd from the CPython 3.11.9 Windows embeddable package (PSF-2.0 and bundled licences)
  synthetic, seeded per chunk, vocabulary disjoint from corpus.py's syllable words:
    xml       nested elements with attributes
    sql       an INSERT dump with typed columns
    hexdump   xxd-style hex lines over random bytes

Real families are cut into CONSECUTIVE, NON-OVERLAPPING 32768-byte chunks of the concatenated blob and a seeded
permutation picks which chunks are used: no two chunks share a byte (the audit's gutenberg finding, where random
offsets let evaluation windows overlap). Chunk ids live in their own space (CHUNK_ID_BASE + family stride + k), and
the family of a row is the `fam` array, never `g % 8`. Nothing here is ever fitted on: the corpus is scored only.

    python3 tools/pivot/corpus_ext.py --build            # data/pivot/ext_c4096.npz + artifacts/pivot/ext_corpus_manifest.json
    python3 tools/pivot/corpus_ext.py --check            # array hashes of the npz against the banked manifest
    python3 tools/pivot/corpus_ext.py --probe            # determinism: a small slice built twice, in two chunk orders
    python3 tools/pivot/corpus_ext.py --verify-pins      # every pinned source file present and byte-identical
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import random
import re
import sys
import tarfile
import time
import zipfile
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from corpus import CONFIGS, CONFIG_NAMES, N_CONFIGS, carve, compress  # noqa: E402
from features import N_FEATURES, features_many  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
SRC_DIR = os.path.join(REPO, "data", "pivot", "ext_src")
PINS_PATH = os.path.join(HERE, "ext_source_pins.json")
NPZ_PATH = os.path.join(REPO, "data", "pivot", "ext_c4096.npz")
MANIFEST_PATH = os.path.join(REPO, "artifacts", "pivot", "ext_corpus_manifest.json")

EXT_FAMILIES = ["c_src", "hexdump", "pe_bin", "py_src", "rfc_txt", "rst_doc", "sql", "xml"]   # frozen order
REAL_FAMILIES = ["c_src", "pe_bin", "py_src", "rfc_txt", "rst_doc"]
SYNTH_FAMILIES = ["hexdump", "sql", "xml"]
CHUNK_ID_BASE = 10_000_000
FAMILY_STRIDE = 100_000
DEFAULTS = {"n_per_family": 300, "chunk_size": 32768, "carve": 4096, "seed": 20260909}


def chunk_id(fam_index: int, k: int) -> int:
    return CHUNK_ID_BASE + fam_index * FAMILY_STRIDE + k


# ------------------------------------------------------------------ synthetic families (vocabulary disjoint from corpus.py)
WORDS = ("account address amount balance batch branch budget calendar campaign capacity category channel client "
         "cluster column comment contract country currency customer delivery department discount district document "
         "duration engine estimate expense factory feature forecast fragment gateway holiday inventory invoice journal "
         "language latitude longitude machine manager material message network operator package partner payment "
         "pipeline platform postcode priority product project province quantity receipt region release revenue "
         "schedule section segment service session shipment station status storage supplier ticket timezone "
         "transfer vehicle vendor version warehouse warranty").split()
ISO_COUNTRIES = "AR AU BR CA CH CL CN CO CZ DE DK EG ES FI FR GB GR HU ID IE IL IN IT JP KE KR MX NG NL NO NZ PE PH PL PT SE SG TH TR TW UA US VN ZA".split()


def _phrase(rng, lo, hi):
    return " ".join(rng.choice(WORDS) for _ in range(rng.randint(lo, hi)))


def _date(rng):
    return f"{rng.randint(1998, 2026)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"


def gen_xml(rng, size):
    out = ['<?xml version="1.0" encoding="UTF-8"?>\n<catalog xmlns="urn:ext:catalog" generated="', _date(rng), '">\n']
    while sum(map(len, out)) < size:
        ident = rng.randint(1, 10**7); entry = rng.choice(WORDS)
        out.append(f'  <{entry} id="{ident}" ref="{rng.choice(WORDS)}-{rng.randint(0, 9999):04d}" '
                   f'country="{rng.choice(ISO_COUNTRIES)}">\n')
        for _ in range(rng.randint(2, 7)):
            tag = rng.choice(WORDS)
            kind = rng.random()
            if kind < 0.35:
                out.append(f'    <{tag}>{_phrase(rng, 1, 6)}</{tag}>\n')
            elif kind < 0.6:
                out.append(f'    <{tag} unit="{rng.choice(["kg", "cm", "pcs", "hrs", "EUR", "USD"])}">'
                           f'{rng.random() * 10 ** rng.randint(0, 5):.{rng.randint(0, 4)}f}</{tag}>\n')
            elif kind < 0.8:
                out.append(f'    <{tag} on="{_date(rng)}" enabled="{str(rng.random() < 0.5).lower()}"/>\n')
            else:
                out.append(f'    <{tag}s>\n' + "".join(f'      <{tag}>{rng.choice(WORDS)}</{tag}>\n'
                                                       for _ in range(rng.randint(1, 4))) + f'    </{tag}s>\n')
        out.append(f'  </{entry}>\n')
    return "".join(out)[:size].encode()


def gen_sql(rng, size):
    table = rng.choice(WORDS)
    cols = rng.sample(WORDS, rng.randint(4, 9))
    kinds = [rng.choice(["int", "real", "text", "date", "bool"]) for _ in cols]
    out = [f"CREATE TABLE {table} (" + ", ".join(f"{c} {k.upper()}" for c, k in zip(cols, kinds)) + ");\n"]
    while sum(map(len, out)) < size:
        vals = []
        for k in kinds:
            r = rng.random()
            if r < 0.06:
                vals.append("NULL")
            elif k == "int":
                vals.append(str(rng.randint(-1000, 10**6)))
            elif k == "real":
                vals.append(f"{rng.uniform(-1e4, 1e5):.{rng.randint(1, 3)}f}")
            elif k == "text":
                vals.append("'" + _phrase(rng, 1, 5).replace("'", "''") + "'")
            elif k == "date":
                vals.append(f"'{_date(rng)}'")
            else:
                vals.append(rng.choice(["TRUE", "FALSE"]))
        out.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(vals)});\n")
    return "".join(out)[:size].encode()


def gen_hexdump(rng, size):
    out = []
    off = rng.randrange(0, 1 << 24) & ~0xF
    while sum(map(len, out)) < size:
        raw = bytes(rng.getrandbits(8) for _ in range(16))
        hexpart = " ".join(raw[i:i + 2].hex() for i in range(0, 16, 2))
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in raw)
        out.append(f"{off:08x}: {hexpart}  {ascii_part}\n")
        off += 16
    return "".join(out)[:size].encode()


GEN = {"xml": gen_xml, "sql": gen_sql, "hexdump": gen_hexdump}


# ------------------------------------------------------------------ real families (pinned upstream files)
def load_pins():
    return json.load(open(PINS_PATH, encoding="utf-8"))


def verify_pins(src_dir=SRC_DIR, pins=None):
    """Every pinned file present and byte-identical. Returns (ok, problems)."""
    pins = pins or load_pins()
    problems = []
    for rel, e in sorted(pins["files"].items()):
        p = os.path.join(src_dir, rel)
        if not os.path.isfile(p):
            problems.append(f"missing: {rel}")
            continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h != e["sha256"]:
            problems.append(f"sha256 mismatch: {rel} has {h[:12]}..., pinned {e['sha256'][:12]}...")
    return not problems, problems


def load_real_blobs(src_dir=SRC_DIR, pins=None):
    """Concatenate each real family's member files in sorted-name order. Refuses on any pin problem."""
    pins = pins or load_pins()
    ok, problems = verify_pins(src_dir, pins)
    if not ok:
        raise RuntimeError("extension sources do not match tools/pivot/ext_source_pins.json: " + "; ".join(problems[:5]))
    blobs = {}
    with tarfile.open(os.path.join(src_dir, "Python-3.11.9.tgz")) as t:
        members = {m.name: m for m in t.getmembers() if m.isfile()}
        py = sorted(n for n in members if re.match(r"^Python-3\.11\.9/Lib/.*\.py$", n))
        rst = sorted(n for n in members if re.match(r"^Python-3\.11\.9/Doc/.*\.rst$", n))
        blobs["py_src"] = b"".join(t.extractfile(members[n]).read() for n in py)
        blobs["rst_doc"] = b"".join(t.extractfile(members[n]).read() for n in rst)
    with zipfile.ZipFile(os.path.join(src_dir, "sqlite-amalgamation-3450300.zip")) as z:
        names = sorted(i.filename for i in z.infolist() if i.filename.endswith((".c", ".h")))
        blobs["c_src"] = b"".join(z.read(n) for n in names)
    with zipfile.ZipFile(os.path.join(src_dir, "python-3.11.9-embed-amd64.zip")) as z:
        names = sorted(i.filename for i in z.infolist() if i.filename.lower().endswith((".dll", ".exe", ".pyd")))
        blobs["pe_bin"] = b"".join(z.read(n) for n in names)
    rfcs = sorted(rel for rel in pins["files"] if rel.startswith("rfc/"))
    blobs["rfc_txt"] = b"".join(open(os.path.join(src_dir, rel), "rb").read() for rel in rfcs)
    return blobs


def real_selection(blobs, n_per_family, chunk_size, seed):
    """For each real family: the blob is cut into consecutive chunks; a permutation seeded by (seed, family index)
    picks n of them without replacement. Returns {family: [blob chunk index for k in range(n)]}."""
    sel = {}
    for f in REAL_FAMILIES:
        n_avail = len(blobs[f]) // chunk_size
        if n_avail < n_per_family:
            raise RuntimeError(f"{f}: only {n_avail} whole chunks of {chunk_size} bytes, {n_per_family} needed")
        rng = random.Random(seed * 1000 + EXT_FAMILIES.index(f))
        sel[f] = rng.sample(range(n_avail), n_per_family)
    return sel


_BLOBS = None
_SEL = None


def _init(src_dir, n_per_family, chunk_size, seed):
    global _BLOBS, _SEL
    _BLOBS = load_real_blobs(src_dir)
    _SEL = real_selection(_BLOBS, n_per_family, chunk_size, seed)


def source_chunk(family, k, chunk_size, blobs, sel):
    fi = EXT_FAMILIES.index(family)
    if family in REAL_FAMILIES:
        i = sel[family][k]
        return blobs[family][i * chunk_size:(i + 1) * chunk_size]
    return GEN[family](random.Random(chunk_id(fi, k)), chunk_size)


def chunk_rows(family, k, chunk_size, carve_len, blobs, sel):
    """All rows from one source chunk: features, labels, and the two ceilings (distinct streams, distinct carved
    fragments among the 26 configurations)."""
    src = source_chunk(family, k, chunk_size, blobs, sel)
    frags, labels, streams, carved = [], [], set(), set()
    for i, (_, impl, level) in enumerate(CONFIGS):
        try:
            stream = compress(impl, level, src)
        except Exception:  # noqa: BLE001
            continue
        streams.add(hashlib.sha1(stream).hexdigest())
        f = carve(stream, carve_len)
        if f is not None:
            frags.append(f); labels.append(i); carved.add(hashlib.sha1(f).hexdigest())
    return frags, labels, len(streams), len(carved), hashlib.sha256(src).hexdigest()


def _one(args):
    family, k, chunk_size, carve_len = args
    frags, labels, n_streams, n_carved, src_sha = chunk_rows(family, k, chunk_size, carve_len, _BLOBS, _SEL)
    fi = EXT_FAMILIES.index(family)
    meta = (chunk_id(fi, k), fi, k, n_streams, n_carved, src_sha)
    if not frags:
        return np.empty((0, N_FEATURES), np.float32), np.empty(0, np.int16), meta
    return features_many(frags), np.asarray(labels, np.int16), meta


def build(n_per_family, chunk_size, carve_len, seed, procs, src_dir=SRC_DIR, families=None, order_seed=None):
    families = families or EXT_FAMILIES
    tasks = [(f, k, chunk_size, carve_len) for f in families for k in range(n_per_family)]
    if order_seed is not None:   # the probe shuffles the task order: the corpus must not depend on it
        random.Random(order_seed).shuffle(tasks)
    cap = len(tasks) * N_CONFIGS
    X = np.empty((cap, N_FEATURES), np.float32); Y = np.empty(cap, np.int16); G = np.empty(cap, np.int32)
    F = np.empty(cap, np.int8)
    metas = []
    n = 0; t0 = time.perf_counter()
    with Pool(procs, initializer=_init, initargs=(src_dir, n_per_family, chunk_size, seed)) as pool:
        for j, (x, y, meta) in enumerate(pool.imap_unordered(_one, tasks, chunksize=4), 1):
            m = len(y)
            if m:
                X[n:n + m] = x; Y[n:n + m] = y; G[n:n + m] = meta[0]; F[n:n + m] = meta[1]; n += m
            metas.append(meta)
            if j % 400 == 0:
                print(f"    {j}/{len(tasks)} chunks, {n} rows, {time.perf_counter() - t0:.0f}s", flush=True)
    # canonical row order: by chunk id then label, so the arrays do not depend on worker scheduling
    order = np.lexsort((Y[:n], G[:n]))
    X, Y, G, F = X[:n][order], Y[:n][order], G[:n][order], F[:n][order]
    metas.sort()
    meta_arr = {"chunk_ids": np.array([m[0] for m in metas], np.int32),
                "chunk_fam": np.array([m[1] for m in metas], np.int8),
                "chunk_k": np.array([m[2] for m in metas], np.int32),
                "distinct_streams": np.array([m[3] for m in metas], np.int8),
                "distinct_fragments": np.array([m[4] for m in metas], np.int8),
                "src_sha256": np.array([m[5] for m in metas])}
    return X, Y, G, F, meta_arr, round(time.perf_counter() - t0, 1)


def _sha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def manifest_of(X, Y, G, F, meta, n_per_family, chunk_size, carve_len, seed, build_s, pins, sel):
    fam_names = np.array(EXT_FAMILIES)
    per_family = {}
    for fi, f in enumerate(EXT_FAMILIES):
        m = F == fi; cm = meta["chunk_fam"] == fi
        per_family[f] = {"n_rows": int(m.sum()), "n_chunks": int(cm.sum()),
                         "rows_per_chunk_mean": round(float(m.sum() / max(cm.sum(), 1)), 4),
                         "ceiling_distinct_streams": round(float(meta["distinct_streams"][cm].mean() / N_CONFIGS), 4),
                         "ceiling_distinct_fragments": round(float(meta["distinct_fragments"][cm].mean() / N_CONFIGS), 4),
                         "kind": "real" if f in REAL_FAMILIES else "synthetic",
                         "selection_sha256": (hashlib.sha256(json.dumps(sel[f]).encode()).hexdigest() if f in sel else None)}
    return {"schema": "raise-v1/ext_corpus_manifest/1",
            "why": "content hashes of the extension corpus arrays and per-family ceilings; a rebuilt corpus is proven identical by "
                   "`python3 tools/pivot/corpus_ext.py --check`, and preregistration 0018 seals these hashes",
            "npz": os.path.relpath(NPZ_PATH, REPO), "families": EXT_FAMILIES, "real_families": REAL_FAMILIES,
            "synthetic_families": SYNTH_FAMILIES, "n_per_family": n_per_family, "chunk_size": chunk_size, "carve": carve_len,
            "seed": seed, "chunk_id_base": CHUNK_ID_BASE, "family_stride": FAMILY_STRIDE, "n_rows": int(len(Y)),
            "n_chunks": int(len(meta["chunk_ids"])), "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES,
            "arrays": {"X": {"sha256": _sha(X), "shape": list(X.shape), "dtype": str(X.dtype)},
                       "y": {"sha256": _sha(Y), "shape": list(Y.shape), "dtype": str(Y.dtype)},
                       "g": {"sha256": _sha(G), "shape": list(G.shape), "dtype": str(G.dtype)},
                       "fam": {"sha256": _sha(F), "shape": list(F.shape), "dtype": str(F.dtype)}},
            "chunk_meta_sha256": {k: _sha(v) if v.dtype.kind != "U" else hashlib.sha256("\n".join(v).encode()).hexdigest()
                                  for k, v in meta.items()},
            "per_family": per_family, "source_pins": pins["files"], "build_seconds": build_s,
            "rows_dropped_short_stream": int(len(meta["chunk_ids"]) * N_CONFIGS - len(Y)),
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def save_npz(path, X, Y, G, F, meta, n_per_family, chunk_size, carve_len, seed):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez(path, X=X, y=Y, g=G, fam=F, carve=np.int64(carve_len), chunk_size=np.int64(chunk_size),
             n_per_family=np.int64(n_per_family), seed=np.int64(seed), chunk_id_base=np.int64(CHUNK_ID_BASE),
             families=np.array(EXT_FAMILIES), **{f"meta_{k}": v for k, v in meta.items()})


def check(npz_path=NPZ_PATH, manifest_path=MANIFEST_PATH):
    from npzmap import npz_memmap
    man = json.load(open(manifest_path, encoding="utf-8"))
    ok = True
    for name, rec in man["arrays"].items():
        arr = npz_memmap(npz_path, name)
        h = hashlib.sha256()
        for i in range(0, len(arr), 20000):
            h.update(np.ascontiguousarray(arr[i:i + 20000]).tobytes())
        same = h.hexdigest() == rec["sha256"] and list(arr.shape) == rec["shape"] and str(arr.dtype) == rec["dtype"]
        print(f"  {'ok  ' if same else 'FAIL'} {name} {list(arr.shape)} {arr.dtype} {h.hexdigest()[:16]}")
        ok &= same
    print("EXT CORPUS: " + ("IDENTICAL to the banked manifest" if ok else "DIFFERS from the banked manifest"))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true"); ap.add_argument("--check", action="store_true")
    ap.add_argument("--probe", action="store_true"); ap.add_argument("--verify-pins", action="store_true")
    ap.add_argument("--n-per-family", type=int, default=DEFAULTS["n_per_family"])
    ap.add_argument("--chunk-size", type=int, default=DEFAULTS["chunk_size"])
    ap.add_argument("--carve", type=int, default=DEFAULTS["carve"])
    ap.add_argument("--seed", type=int, default=DEFAULTS["seed"])
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--src", default=SRC_DIR)
    ap.add_argument("--out", default=NPZ_PATH); ap.add_argument("--manifest", default=MANIFEST_PATH)
    a = ap.parse_args()
    if a.verify_pins:
        ok, problems = verify_pins(a.src)
        print("EXT SOURCES: " + ("every pinned file present and byte-identical" if ok else "; ".join(problems)))
        return 0 if ok else 1
    if a.probe:
        n = 3
        h = []
        for order_seed in (None, 7):
            X, Y, G, F, meta, s = build(n, a.chunk_size, a.carve, a.seed, a.procs, a.src, order_seed=order_seed)
            h.append((_sha(X), _sha(Y), _sha(G), _sha(F), _sha(meta["distinct_fragments"])))
            print(f"  probe build ({'canonical' if order_seed is None else 'shuffled'} order): {len(Y)} rows in {s}s; "
                  f"X {h[-1][0][:16]}")
        same = h[0] == h[1]
        print("EXT CORPUS PROBE: " + ("deterministic (two builds, two task orders, identical arrays)" if same else "NOT deterministic"))
        return 0 if same else 1
    if a.build:
        pins = load_pins()
        blobs = load_real_blobs(a.src, pins); sel = real_selection(blobs, a.n_per_family, a.chunk_size, a.seed)
        del blobs
        print(f"building {len(EXT_FAMILIES)} families x {a.n_per_family} chunks ({a.chunk_size} B, carve {a.carve} B), seed {a.seed}",
              flush=True)
        X, Y, G, F, meta, s = build(a.n_per_family, a.chunk_size, a.carve, a.seed, a.procs, a.src)
        save_npz(a.out, X, Y, G, F, meta, a.n_per_family, a.chunk_size, a.carve, a.seed)
        man = manifest_of(X, Y, G, F, meta, a.n_per_family, a.chunk_size, a.carve, a.seed, s, pins, sel)
        os.makedirs(os.path.dirname(a.manifest), exist_ok=True)
        with open(a.manifest, "w", encoding="utf-8") as fh:
            json.dump(man, fh, indent=2, sort_keys=True); fh.write("\n")
        print(f"wrote {os.path.relpath(a.out, REPO)} ({len(Y)} rows, {man['n_chunks']} chunks, {s}s) and "
              f"{os.path.relpath(a.manifest, REPO)}")
        for f, r in man["per_family"].items():
            print(f"  {f:<8} rows {r['n_rows']:>6} chunks {r['n_chunks']:>4} ceilings streams {r['ceiling_distinct_streams']} "
                  f"fragments {r['ceiling_distinct_fragments']}")
        return 0
    if a.check:
        return 0 if check(a.out, a.manifest) else 1
    ap.print_help(); return 2


if __name__ == "__main__":
    raise SystemExit(main())
