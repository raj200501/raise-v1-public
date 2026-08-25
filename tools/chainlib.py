"""Canonical serialisation + hashing primitives shared by every gate in this repo.

Everything that must be tamper-evident goes through here, so there is exactly one
definition of "the bytes we hashed" and it is auditable in one place.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from typing import Any

CANON_KWARGS = dict(sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def canon(obj: Any) -> bytes:
    """Deterministic JSON bytes. Sorted keys, no whitespace, no NaN, UTF-8."""
    return json.dumps(obj, **CANON_KWARGS).encode("utf-8")


def sha256_obj(obj: Any) -> str:
    return hashlib.sha256(canon(obj)).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_head(repo_root: str = ".") -> str:
    """Current commit, or the literal string UNCOMMITTED if git is unavailable."""
    try:
        out = subprocess.run(
            ["git", "-C", repo_root, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=15,
        )
        return out.stdout.strip() if out.returncode == 0 else "UNCOMMITTED"
    except Exception:
        return "UNCOMMITTED"


def git_dirty(repo_root: str = ".") -> bool:
    try:
        out = subprocess.run(
            ["git", "-C", repo_root, "status", "--porcelain"],
            capture_output=True, text=True, timeout=15,
        )
        return bool(out.stdout.strip())
    except Exception:
        return True


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
