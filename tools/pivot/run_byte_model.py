#!/usr/bin/env python3
"""Train a byte-sequence model on raw 1024-byte fragments. Governed by preregistration 0009.

Builds its corpus from the SAME source chunks, carve, seed and grouping as 0007's corpus B, so the
held-out fragments are identical and the number sits directly beside 0007's 0.1165 rather than
approximately near it. Keeps the raw bytes, which the feature pipeline discards - that is the whole
point, since every one of the 1108 hand-engineered features throws away ORDER.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus import FAMILIES, N_CONFIGS, chunk_fragments, load_real  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FROZEN_SET = ["majority", "stratified", "depth3_tree", "logistic"]


def build_raw(n_chunks, offset, chunk_size, carve, src):
    real = load_real(src)
    X = np.empty((n_chunks * N_CONFIGS, carve), dtype=np.uint8)
    y = np.empty(n_chunks * N_CONFIGS, dtype=np.int16)
    g = np.empty(n_chunks * N_CONFIGS, dtype=np.int32)
    n = 0
    t = time.perf_counter()
    for i in range(n_chunks):
        idx = offset + i
        frags, labels, _ = chunk_fragments(idx, FAMILIES[idx % len(FAMILIES)], real,
                                           chunk_size, carve)
        for f, lab in zip(frags, labels):
            X[n] = np.frombuffer(f, dtype=np.uint8, count=carve)
            y[n] = lab; g[n] = idx; n += 1
        if (i + 1) % 2500 == 0:
            print(f"      {i+1}/{n_chunks} chunks, {n} fragments, "
                  f"{time.perf_counter()-t:.0f}s", flush=True)
    return X[:n], y[:n], g[:n], round(time.perf_counter() - t, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--carve", type=int, default=1024)
    ap.add_argument("--chunks", type=int, default=25000)
    ap.add_argument("--chunk-offset", type=int, default=50000)
    ap.add_argument("--chunk-size", type=int, default=32768)
    ap.add_argument("--rung", type=int, default=100000)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--seed", type=int, default=20260825)
    ap.add_argument("--eval-frac", type=float, default=0.2)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--cache", default=os.path.join(REPO, "data", "pivot", "raw_c1024.npz"))
    ap.add_argument("--src", default=os.path.join(REPO, "data", "pivot", "src"))
    ap.add_argument("--head", default="gap", choices=["gap", "flatten"],
                    help="gap reproduces 0009; flatten preserves position (0010)")
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "pivot", "byte_model.json"))
    args = ap.parse_args()

    if os.path.exists(args.cache):
        print(f"[1/5] reusing raw corpus {os.path.relpath(args.cache, REPO)}", flush=True)
        z = np.load(args.cache)
        X, y, g, build_s = z["X"], z["y"], z["g"], float(z["build_s"])
    else:
        print(f"[1/5] building raw corpus: carve {args.carve}, {args.chunks} chunks "
              f"at offset {args.chunk_offset}", flush=True)
        X, y, g, build_s = build_raw(args.chunks, args.chunk_offset, args.chunk_size,
                                     args.carve, args.src)
        np.savez(args.cache, X=X, y=y, g=g, build_s=build_s)
    print(f"      {len(y)} fragments x {X.shape[1]} bytes, {build_s}s", flush=True)

    # IDENTICAL split to 0007's corpus B: same seed, same shuffle order, same grouping.
    rng = np.random.default_rng(args.seed)
    groups = np.unique(g); rng.shuffle(groups)
    ev_groups = set(groups[:max(1, int(len(groups) * args.eval_frac))].tolist())
    is_ev = np.fromiter((int(v) in ev_groups for v in g), bool, len(g))
    tr = np.nonzero(~is_ev)[0]; rng.shuffle(tr); tr = tr[:args.rung]
    ev = np.nonzero(is_ev)[0]
    Xtr, ytr = X[tr], y[tr].astype(np.int64)
    Xe, ye = X[ev], y[ev].astype(np.int64)
    fp = hashlib.sha256(np.sort(np.array(sorted(ev_groups))).tobytes()).hexdigest()[:16]
    # The entire comparison against 0007 rests on the evaluation set being IDENTICAL, so it is
    # CHECKED against corpus B rather than argued from "same seed, same code". Corpus B's
    # fingerprint under this identical procedure is cb98419e098f48c0.
    EXPECTED_FP = "cb98419e098f48c0"
    if fp != EXPECTED_FP:
        print(f"REFUSING: eval-group fingerprint {fp} does not match 0007's corpus B "
              f"({EXPECTED_FP}). The comparison against 0.1165 would not be like for like.",
              file=sys.stderr)
        return 3
    print(f"[2/5] split: {len(ytr)} train / {len(ye)} eval  "
          f"(eval-group fingerprint {fp}, matches 0007's corpus B)", flush=True)

    print(f"[3/5] trivial baselines on the SAME {len(ytr)} rows", flush=True)
    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.tree import DecisionTreeClassifier
    # Baselines get a byte histogram - the natural cheap view of a raw byte string.
    def hist(A):
        out = np.zeros((len(A), 256), dtype=np.float32)
        for i in range(0, len(A), 20000):
            blk = A[i:i + 20000]
            out[i:i + len(blk)] = np.stack([np.bincount(r, minlength=256) for r in blk]) / blk.shape[1]
        return out
    Htr, He = hist(Xtr), hist(Xe)
    baselines = {}
    for nm, clf in [("majority", DummyClassifier(strategy="most_frequent")),
                    ("stratified", DummyClassifier(strategy="stratified", random_state=0)),
                    ("depth3_tree", DecisionTreeClassifier(max_depth=3, random_state=0)),
                    ("depth8_tree", DecisionTreeClassifier(max_depth=8, random_state=0)),
                    ("depth16_tree", DecisionTreeClassifier(max_depth=16, random_state=0)),
                    ("logistic", LogisticRegression(max_iter=400))]:
        t = time.perf_counter(); clf.fit(Htr, ytr)
        baselines[nm] = round(float((clf.predict(He) == ye).mean()), 4)
        print(f"      {nm:<14} {baselines[nm]:.4f}  ({time.perf_counter()-t:.0f}s)", flush=True)
    frozen = {k: v for k, v in baselines.items() if k in FROZEN_SET}
    fname = max(frozen, key=frozen.get); ename = max(baselines, key=baselines.get)
    del Htr, He

    import torch
    import torch.nn as nn
    torch.manual_seed(args.seed); torch.set_num_threads(args.threads)

    class ByteCNN(nn.Module):
        """Identical conv stack for both heads. ONLY the head differs, so any difference in the
        result is attributable to it - which is the entire question 0010 asks."""
        def __init__(self, n_classes=N_CONFIGS, emb=16, head="gap", seq=None):
            super().__init__()
            self.head = head
            self.emb = nn.Embedding(256, emb)
            self.net = nn.Sequential(
                nn.Conv1d(emb, 64, 9, padding=4), nn.ReLU(), nn.MaxPool1d(4),
                nn.Conv1d(64, 96, 9, padding=4), nn.ReLU(), nn.MaxPool1d(4),
                nn.Conv1d(96, 128, 9, padding=4), nn.ReLU())
            self.gap = nn.AdaptiveAvgPool1d(1)
            self.fc = nn.Linear(128 if head == "gap" else 128 * (seq // 16), n_classes)
        def forward(self, x):
            h = self.net(self.emb(x).transpose(1, 2))
            h = self.gap(h).squeeze(-1) if self.head == "gap" else h.flatten(1)
            return self.fc(h)

    def train_eval(labels, tag):
        m = ByteCNN(head=args.head, seq=Xtr.shape[1]); opt = torch.optim.Adam(m.parameters(), 1e-3); lf = nn.CrossEntropyLoss()
        yt = torch.from_numpy(labels)
        n = len(labels)
        for ep in range(args.epochs):
            m.train(); perm = torch.randperm(n); tot = 0.0
            t = time.perf_counter()
            for i in range(0, n, args.batch):
                b = perm[i:i + args.batch]
                xb = torch.from_numpy(Xtr[b.numpy()].astype(np.int64))
                opt.zero_grad(); loss = lf(m(xb), yt[b]); loss.backward(); opt.step()
                tot += float(loss.detach()) * len(b)
            print(f"      [{tag}] epoch {ep+1}/{args.epochs} loss {tot/n:.4f} "
                  f"({time.perf_counter()-t:.0f}s)", flush=True)
        m.eval(); correct = 0
        with torch.no_grad():
            for i in range(0, len(ye), 1024):
                xb = torch.from_numpy(Xe[i:i + 1024].astype(np.int64))
                correct += int((m(xb).argmax(1).numpy() == ye[i:i + 1024]).sum())
            tr_corr = 0
            for i in range(0, n, 1024):
                xb = torch.from_numpy(Xtr[i:i + 1024].astype(np.int64))
                tr_corr += int((m(xb).argmax(1).numpy() == labels[i:i + 1024]).sum())
        # TRAIN accuracy is returned because it is the failability half of the null control: a
        # control the model cannot fail carries no information (CORRECTIONS.md, 2026-08-26).
        return (round(correct / len(ye), 4), sum(p.numel() for p in m.parameters()),
                round(tr_corr / n, 4))

    print(f"[4/5] byte model, {args.epochs} epochs", flush=True)
    top1, nparams, top1_train = train_eval(ytr, "real")
    print(f"      byte model top-1 {top1:.4f}", flush=True)

    print("[5/5] null control: labels shuffled, identical training", flush=True)
    y_sh = ytr.copy(); rng.shuffle(y_sh)
    null1, _, null_train = train_eval(y_sh, "null")
    print(f"      shuffled-label eval {null1:.4f} | TRAIN {null_train:.4f} "
          f"(the control is informative only if this is high)", flush=True)

    ref = json.load(open(os.path.join(REPO, "artifacts", "pivot", "carve_generalisation.json")))
    feat = next((r["accuracy"] for r in ref["rungs"] if r["n_units"] == args.rung), None)
    if args.head == "flatten":
        pooled = json.load(open(os.path.join(REPO, "artifacts", "pivot", "byte_model.json")))
        flat = {"schema": "raise-v1/byte_model_flat/1",
                "preregistration": "0010-byte-model-position-preserving-head",
                "carve_bytes": args.carve, "matched_rung": args.rung,
                "n_train": int(len(ytr)), "n_eval": int(len(ye)), "n_classes": N_CONFIGS,
                "chance_accuracy": round(1.0 / N_CONFIGS, 6),
                "split_is_grouped_by_source": True, "eval_group_fingerprint": fp,
                "eval_group_fingerprint_matches_0007": True,
                "flat_model_top1": top1, "flat_model_train_top1": top1_train,
                "pooled_model_top1": pooled["byte_model_top1"],
                "feature_model_top1": feat,
                "null_train_top1": null_train, "null_eval_top1": null1,
                "trivial_baselines_same_rows": baselines,
                "best_trivial_baseline": frozen[fname], "best_trivial_baseline_name": fname,
                "model": "same conv stack as 0009; flatten head instead of global average pool",
                "model_params": int(nparams), "epochs": args.epochs, "seed": args.seed,
                "establishes_a_buyer": False}
        fo = os.path.join(REPO, "artifacts", "pivot", "byte_model_flat.json")
        with open(fo, "w", encoding="utf-8") as fh:
            json.dump(flat, fh, indent=2, sort_keys=True); fh.write("\n")
        print(f"\nflat {top1} | pooled {pooled['byte_model_top1']} | features {feat} | "
              f"best trivial {frozen[fname]}")
        print(f"null control: eval {null1} (must be at chance), TRAIN {null_train} "
              f"(must be high or the control means nothing)")
        print(f"wrote {os.path.relpath(fo, REPO)}")
        return 0

    out = {"schema": "raise-v1/byte_model/1", "preregistration": "0009-byte-sequence-representation",
           "carve_bytes": args.carve, "matched_rung": args.rung,
           "n_train": int(len(ytr)), "n_eval": int(len(ye)), "n_classes": N_CONFIGS,
           "chance_accuracy": round(1.0 / N_CONFIGS, 6),
           "split_is_grouped_by_source": True,
           "eval_group_fingerprint": fp,
           "eval_group_fingerprint_matches_0007": True,
           "byte_model_top1": top1, "feature_model_top1": feat,
           "byte_model_shuffled_top1": null1,
           "trivial_baselines_same_rows": baselines,
           "best_trivial_baseline": frozen[fname], "best_trivial_baseline_name": fname,
           "best_baseline_expanded": baselines[ename], "best_baseline_expanded_name": ename,
           "model": "1D CNN over raw bytes: 256-entry embedding, 3 conv+pool stages, GAP, linear",
           "model_params": int(nparams), "epochs": args.epochs, "batch": args.batch,
           "seed": args.seed, "establishes_a_buyer": False,
           "cost": {"build_seconds": build_s, "cpu_cores": args.threads, "gpu": "none"}}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True); fh.write("\n")
    print(f"\nbyte {top1} | features {feat} | best trivial {frozen[fname]} ({fname})")
    print(f"wrote {os.path.relpath(args.out, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
