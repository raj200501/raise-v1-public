"""Features for a carved DEFLATE fragment.

The fragment is bit-packed, entropy-coded and byte-misaligned to everything. A byte histogram of
such data is close to uniform by construction, so surface statistics carry little - which is the
point, and is why a trivial baseline should struggle here. These features are deliberately generic:
nothing here encodes knowledge of any particular encoder.

Crucially the STREAM LENGTH is not a feature and is never passed in. A forensic carve does not come
with the length of the stream it was cut from, and admitting it would hand a dumb baseline the
compression ratio.
"""
from __future__ import annotations

import numpy as np

NBUCKET_PAIR = 256
BIT_RUN_BUCKETS = 12


def _bit_runs(bits: np.ndarray) -> np.ndarray:
    """Length distribution of runs of equal bits, log-bucketed."""
    if bits.size < 2:
        return np.zeros(BIT_RUN_BUCKETS * 2, dtype=np.float64)
    change = np.nonzero(np.diff(bits))[0]
    starts = np.concatenate(([0], change + 1))
    ends = np.concatenate((change + 1, [bits.size]))
    lens = ends - starts
    vals = bits[starts]
    out = np.zeros(BIT_RUN_BUCKETS * 2)
    b = np.minimum((np.log2(np.maximum(lens, 1))).astype(int), BIT_RUN_BUCKETS - 1)
    for v in (0, 1):
        m = vals == v
        if m.any():
            out[v * BIT_RUN_BUCKETS: (v + 1) * BIT_RUN_BUCKETS] = np.bincount(
                b[m], minlength=BIT_RUN_BUCKETS)[:BIT_RUN_BUCKETS]
    return out / max(lens.size, 1)


def features_one(frag: bytes) -> np.ndarray:
    a = np.frombuffer(frag, dtype=np.uint8)
    n = a.size
    hist = np.bincount(a, minlength=256).astype(np.float64) / max(n, 1)

    bits = np.unpackbits(a)
    ones = float(bits.mean())
    runs = _bit_runs(bits)

    pair = ((a[:-1].astype(np.int32) * 31 + a[1:].astype(np.int32)) % NBUCKET_PAIR)
    pairh = np.bincount(pair, minlength=NBUCKET_PAIR).astype(np.float64) / max(n - 1, 1)

    w = 64
    nw = n // w
    if nw >= 2:
        win = a[: nw * w].reshape(nw, w)
        ent = np.empty(nw)
        for i in range(nw):
            c = np.bincount(win[i], minlength=256)
            p = c[c > 0] / w
            ent[i] = -(p * np.log2(p)).sum()
        ent_stats = [ent.mean(), ent.std(), ent.min(), ent.max(),
                     float(np.percentile(ent, 25)), float(np.percentile(ent, 75))]
    else:
        ent_stats = [0.0] * 6

    lags = []
    for lag in (1, 2, 3, 4, 8, 16, 32, 64):
        if bits.size > lag:
            x, y = bits[:-lag].astype(np.float64), bits[lag:].astype(np.float64)
            sx, sy = x.std(), y.std()
            lags.append(float(((x - x.mean()) * (y - y.mean())).mean() / (sx * sy))
                        if sx > 0 and sy > 0 else 0.0)
        else:
            lags.append(0.0)

    nz = hist[hist > 0]
    byte_ent = float(-(nz * np.log2(nz)).sum())
    distinct = float((hist > 0).sum()) / 256.0

    return np.concatenate([
        hist, pairh, runs,
        np.array([ones, byte_ent, distinct] + ent_stats + lags, dtype=np.float64),
        _align_stats(bits), _stored_block_signal(a),
    ])


def _align_stats(bits: np.ndarray) -> np.ndarray:
    """Read the fragment as bytes at each of the 8 bit alignments.

    DEFLATE is bit-packed: Huffman codes do not respect byte boundaries, so a carved fragment's
    natural byte grid is arbitrary. Statistics computed at every alignment expose structure the
    byte-aligned view cannot see, and the alignment at which the data looks LEAST uniform is itself
    informative about the code lengths the encoder chose.
    """
    out = []
    n = bits.size // 8 * 8
    for off in range(8):
        b = bits[off: off + n - 8]
        if b.size < 64:
            out.extend([0.0] * 5)
            continue
        v = np.packbits(b[: b.size // 8 * 8])
        c = np.bincount(v, minlength=256).astype(np.float64)
        tot = c.sum()
        if tot <= 0:
            out.extend([0.0] * 5)
            continue
        p = c / tot
        nz = p[p > 0]
        ent = float(-(nz * np.log2(nz)).sum())
        chi = float(((c - tot / 256.0) ** 2 / (tot / 256.0)).sum() / tot)
        srt = np.sort(p)[::-1]
        out.extend([ent, chi, float(srt[0]), float(srt[:5].sum()), float((p > 0).mean())])
    return np.asarray(out, dtype=np.float64)


def _stored_block_signal(a: np.ndarray) -> np.ndarray:
    """DEFLATE stored blocks (BTYPE=00) byte-align and emit LEN followed by its complement ~LEN.

    That complement pair is a hard, checkable signature, and encoders differ sharply in how often
    they emit stored blocks - ISA-L at its lowest level leans on them heavily. Scanning for
    positions where two consecutive 16-bit little-endian words are bitwise complements gives a
    direct count of that behaviour without needing to decode anything.
    """
    if a.size < 8:
        return np.zeros(3)
    lo = a[:-3].astype(np.uint16) | (a[1:-2].astype(np.uint16) << 8)
    hi = a[2:-1].astype(np.uint16) | (a[3:].astype(np.uint16) << 8)
    comp = (lo ^ hi) == 0xFFFF
    n_comp = float(comp.sum())
    runs = float((a == 0).sum()) / a.size
    return np.array([n_comp, n_comp / max(a.size, 1), runs])


N_FEATURES = 256 + NBUCKET_PAIR + BIT_RUN_BUCKETS * 2 + 3 + 6 + 8 + 40 + 3


def features_many(frags) -> np.ndarray:
    out = np.empty((len(frags), N_FEATURES), dtype=np.float32)
    for i, f in enumerate(frags):
        out[i] = features_one(f)
    return out
