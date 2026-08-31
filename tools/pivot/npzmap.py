#!/usr/bin/env python3
"""Open an array inside an UNCOMPRESSED .npz as a true np.memmap.

Why this file exists. `np.load(path, mmap_mode="r")` SILENTLY IGNORES mmap_mode when the path is a
.npz - it returns an NpzFile, and every `z["X"]` is a full in-memory read. Verified on numpy 2.4.6:

    z = np.load("data/pivot/full_c4096.npz", mmap_mode="r")
    isinstance(z["X"], np.memmap)  ->  False
    z["X"].nbytes                  ->  5.76e9

That is the actual cause of all five OOM kills on the full DEFLATE run, not sklearn's float64
conversion. The conversion is real and is still handled, but it was the second-largest term; the
5.76 GB phantom was the largest, and it was resident for the whole materialisation.

An uncompressed .npz is a zip with STORED entries, so each .npy sits contiguously in the file and
can be mapped in place. That costs no extra disk, which matters here: the cache is 5.77 GB and the
volume has less than 9 GB free, so writing a second copy as loose .npy files is not available.
"""
from __future__ import annotations

import struct
import zipfile

import numpy as np


def npz_memmap(path, name):
    """Return (memmap, ) for `name` inside uncompressed npz `path`. Raises if the entry is deflated."""
    with zipfile.ZipFile(path) as zf:
        info = zf.getinfo(name if name.endswith(".npy") else name + ".npy")
        if info.compress_type != zipfile.ZIP_STORED:
            raise ValueError(f"{path}:{info.filename} is compressed; cannot be mapped in place")
        hdr_off = info.header_offset
    with open(path, "rb") as fh:
        fh.seek(hdr_off)
        local = fh.read(30)
        if local[:4] != b"PK\x03\x04":
            raise ValueError(f"{path}: bad local header at {hdr_off}")
        name_len, extra_len = struct.unpack("<HH", local[26:30])
        data_off = hdr_off + 30 + name_len + extra_len
        fh.seek(data_off)
        # .npy header: magic(6) ver(2) then header length (2 bytes v1, 4 bytes v2+)
        magic = fh.read(8)
        if magic[:6] != b"\x93NUMPY":
            raise ValueError(f"{path}:{name} is not a .npy payload")
        if magic[6] == 1:
            (hlen,) = struct.unpack("<H", fh.read(2))
            arr_off = data_off + 10 + hlen
        else:
            (hlen,) = struct.unpack("<I", fh.read(4))
            arr_off = data_off + 12 + hlen
        meta = eval(fh.read(hlen).decode("latin1"), {"__builtins__": {}}, {})  # noqa: S307
    if meta.get("fortran_order"):
        raise ValueError(f"{path}:{name} is Fortran-ordered; not supported")
    return np.memmap(path, dtype=np.dtype(meta["descr"]), mode="r",
                     offset=arr_off, shape=tuple(meta["shape"]))


def fill_f32(dest, src, rows, cols, chunk=20000):
    """Same chunked gather as fill_f64, keeping the source's float32 width."""
    return fill_f64(dest, src, rows, cols, chunk)


def fill_f64(dest, src, rows, cols, chunk=20000):
    """dest[i] = src[rows[i], :cols] as float64, without ever materialising the float32 whole.

    `np.ascontiguousarray(src[rows][:, :cols], dtype=np.float64)` holds a float32 intermediate AND
    the float64 result at the same time: 3.55 + 7.09 = 10.6 GB at the top rung. Chunked, the
    transient is one chunk (~88 MB).
    """
    order = np.argsort(rows, kind="stable")
    for i in range(0, len(order), chunk):
        sel = order[i:i + chunk]
        dest[sel] = src[rows[sel], :cols]   # ascending source rows -> near-sequential file reads
    return dest
