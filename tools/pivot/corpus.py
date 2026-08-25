#!/usr/bin/env python3
"""The label factory: manufacture carved-DEFLATE fragments with exact free labels.

Take any bytes, compress them under every available (implementation, level) configuration, and
carve a fixed-size window from the MIDDLE of each resulting stream. The label is the configuration
that produced it, and it costs one compression call.

What the student receives is deliberately impoverished: the carved bytes and nothing else. No
header, no stream start, no plaintext, and NOT the stream length. That is what a forensic carve
actually looks like, and it is what makes every incumbent tool inapplicable - preflate and
grittibanzli need the stream start to decode the token sequence, precomp and list-compresslevel.py
need the plaintext to recompress and compare.

Content families are mixed deliberately so that a model cannot succeed by memorising content, and
each fragment records the source chunk it came from so the evaluation split can be grouped by it.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import random
import struct
import zlib

import deflate as libdeflate
import zopfli.zlib as zopfli
from isal import isal_zlib

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# (name, implementation, level). Frozen ordering: the label id is the index into this list.
CONFIGS: list[tuple[str, str, int]] = (
    [(f"zlib-{l}", "zlib", l) for l in range(1, 10)]
    + [(f"libdeflate-{l}", "libdeflate", l) for l in range(1, 13)]
    + [(f"isal-{l}", "isal", l) for l in range(0, 4)]
    + [("zopfli", "zopfli", 0)]
)
CONFIG_NAMES = [c[0] for c in CONFIGS]
N_CONFIGS = len(CONFIGS)


def compress(impl: str, level: int, data: bytes) -> bytes:
    if impl == "zlib":
        return zlib.compress(data, level)
    if impl == "libdeflate":
        return libdeflate.zlib_compress(data, level)
    if impl == "isal":
        return isal_zlib.compress(data, level)
    if impl == "zopfli":
        return zopfli.compress(data)
    raise ValueError(impl)


# ------------------------------------------------------------------ content families

def _words(rng, n):
    syl = ["ka", "ro", "mi", "ta", "len", "sor", "ba", "quix", "fen", "dro", "al", "ish"]
    return [("".join(rng.choice(syl) for _ in range(rng.randint(1, 3)))) for _ in range(n)]


def gen_json(rng, size):
    out = []
    keys = _words(rng, 24)
    while sum(map(len, out)) < size:
        rec = {rng.choice(keys): rng.choice([rng.randint(0, 10**6), round(rng.random(), 5),
                                             "".join(_words(rng, rng.randint(1, 4))), None, True])
               for _ in range(rng.randint(3, 12))}
        out.append(json.dumps(rec) + "\n")
    return "".join(out)[:size].encode()


def gen_csv(rng, size):
    cols = _words(rng, rng.randint(4, 12))
    out = [",".join(cols) + "\n"]
    while sum(map(len, out)) < size:
        out.append(",".join(str(rng.randint(0, 99999)) if rng.random() < 0.6
                            else rng.choice(cols) for _ in cols) + "\n")
    return "".join(out)[:size].encode()


def gen_log(rng, size):
    lvl = ["INFO", "WARN", "ERROR", "DEBUG"]
    comp = _words(rng, 10)
    out = []
    while sum(map(len, out)) < size:
        out.append(f"2026-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}T"
                   f"{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:{rng.randint(0,59):02d}Z "
                   f"{rng.choice(lvl)} [{rng.choice(comp)}] "
                   f"{' '.join(_words(rng, rng.randint(3,10)))} id={rng.randint(0,10**7)}\n")
    return "".join(out)[:size].encode()


def gen_code(rng, size):
    ident = _words(rng, 30)
    out = []
    while sum(map(len, out)) < size:
        f = rng.choice(ident)
        out.append(f"def {f}({', '.join(rng.sample(ident, rng.randint(1,3)))}):\n")
        for _ in range(rng.randint(1, 6)):
            out.append(f"    {rng.choice(ident)} = {rng.choice(ident)} "
                       f"{rng.choice(['+','-','*','/','%'])} {rng.randint(0,999)}\n")
        out.append(f"    return {rng.choice(ident)}\n\n")
    return "".join(out)[:size].encode()


def gen_base64(rng, size):
    raw = bytes(rng.getrandbits(8) for _ in range(int(size * 0.78) + 64))
    return base64.b64encode(raw)[:size]


def gen_binary(rng, size):
    out = bytearray()
    while len(out) < size:
        out += struct.pack("<IHHf", rng.randint(0, 2**32 - 1), rng.randint(0, 65535),
                           rng.randint(0, 255), rng.random() * 1000)
    return bytes(out[:size])


def gen_mixed(rng, size):
    out = bytearray()
    while len(out) < size:
        if rng.random() < 0.5:
            out += bytes([rng.randint(0, 255)]) * rng.randint(4, 200)
        else:
            out += bytes(rng.getrandbits(8) for _ in range(rng.randint(16, 200)))
    return bytes(out[:size])


SYNTH = {"json": gen_json, "csv": gen_csv, "log": gen_log, "code": gen_code,
         "base64": gen_base64, "binary": gen_binary, "mixed": gen_mixed}
FAMILIES = ["gutenberg"] + sorted(SYNTH)


def load_real(src_dir: str) -> bytes:
    blobs = []
    if os.path.isdir(src_dir):
        for f in sorted(os.listdir(src_dir)):
            p = os.path.join(src_dir, f)
            if os.path.isfile(p):
                with open(p, "rb") as fh:
                    blobs.append(fh.read())
    return b"".join(blobs)


def make_chunk(rng, family: str, real: bytes, size: int) -> bytes:
    if family == "gutenberg" and len(real) > size + 16:
        off = rng.randrange(0, len(real) - size)
        return real[off:off + size]
    return SYNTH[family if family in SYNTH else "json"](rng, size)


def carve(stream: bytes, carve_len: int) -> bytes | None:
    """A window from the middle. Never the first bytes, so the header is never included."""
    if len(stream) < carve_len + 64:
        return None
    start = (len(stream) - carve_len) // 2
    if start < 8:
        return None
    return stream[start:start + carve_len]


def chunk_fragments(seed: int, family: str, real: bytes, chunk_size: int, carve_len: int):
    """All fragments derivable from ONE source chunk. Returns (frags, labels, distinct_streams)."""
    rng = random.Random(seed)
    src = make_chunk(rng, family, real, chunk_size)
    frags, labels, digests = [], [], set()
    for i, (_, impl, level) in enumerate(CONFIGS):
        try:
            stream = compress(impl, level, src)
        except Exception:  # noqa: BLE001
            continue
        digests.add(hashlib.sha1(stream).hexdigest())
        f = carve(stream, carve_len)
        if f is not None:
            frags.append(f)
            labels.append(i)
    return frags, labels, len(digests)
