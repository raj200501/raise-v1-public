#!/usr/bin/env python3
"""Mutation tests: proof that every gate in this repo is capable of failing.

A verifier that cannot fail is decoration. Each mutation below deliberately breaks one
thing and asserts that the relevant gate notices. A mutation that SURVIVES (the gate still
passes) is a hole in the instrument and is reported as such.

Each case runs against a throwaway copy of tools/ in a temp directory, so the real repo is
never mutated. Writes artifacts/verification/mutation_report.json.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
    return p.returncode, p.stdout + p.stderr


def sandbox(tmp: str) -> str:
    root = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(root, "tools", "readers"), exist_ok=True)
    os.makedirs(os.path.join(root, "artifacts"), exist_ok=True)
    os.makedirs(os.path.join(root, "docs"), exist_ok=True)
    os.makedirs(os.path.join(root, "prereg"), exist_ok=True)
    for f in ("chainlib.py", "prereg.py", "claimcheck.py", "scaling.py", "trivial_baselines.py",
              "coverage.py", "freshness.py"):
        shutil.copy(os.path.join(REPO, "tools", f), os.path.join(root, "tools", f))
    with open(os.path.join(root, "docs", "claimcheck_allowlist.tsv"), "w") as fh:
        fh.write("# value\treason\n")
    return root


def seed_claimcheck(root: str):
    with open(os.path.join(root, "artifacts", "result.json"), "w") as fh:
        json.dump({"accuracy": 0.4123, "baseline": 0.25, "n": 1000}, fh)
    doc = os.path.join(root, "docs", "report.md")
    with open(doc, "w") as fh:
        fh.write("Accuracy was 0.412 against a baseline of 0.25 on 1000 units.\n")
    return doc


def seed_prereg(root: str) -> str:
    reader = os.path.join(root, "tools", "readers", "r.py")
    with open(reader, "w") as fh:
        fh.write("print('reading')\n")
    doc = {
        "id": "0001", "slug": "seed", "title": "seed",
        "scope": {"one_line": "x", "corpus": "x", "seed": "x", "rungs": "x",
                  "what_this_does_not_cover": "x"},
        "bar": {"acc": {"threshold": 0.3, "direction": "higher_is_better", "passes_if": "acc > 0.3"}},
        "readings": [{"name": "acc", "unit": "fraction", "source_artifact": "artifacts/result.json",
                      "json_path": "$.accuracy"}],
        "arms": ["a"], "stop_rules": ["s"], "reader": "tools/readers/r.py", "frozen": False,
    }
    path = os.path.join(root, "prereg", "0001-seed.json")
    with open(path, "w") as fh:
        json.dump(doc, fh, indent=2)
    rc, out = run([PY, "tools/prereg.py", "freeze", path], root)
    assert rc == 0, f"seed freeze failed: {out}"
    return path


CASES = []


def case(gate, name, expect):
    def deco(fn):
        CASES.append({"gate": gate, "name": name, "expect": expect, "fn": fn})
        return fn
    return deco


# ---------------------------------------------------------------- claimcheck gate

@case("claimcheck", "control-unmutated-passes", "pass")
def _(root):
    doc = seed_claimcheck(root)
    return run([PY, "tools/claimcheck.py", doc], root)


@case("claimcheck", "fabricated-number-in-doc", "fail")
def _(root):
    doc = seed_claimcheck(root)
    with open(doc, "a") as fh:
        fh.write("We also reached 0.981 on the held-out slice.\n")
    return run([PY, "tools/claimcheck.py", doc], root)


@case("claimcheck", "backing-artifact-deleted", "fail")
def _(root):
    doc = seed_claimcheck(root)
    os.remove(os.path.join(root, "artifacts", "result.json"))
    return run([PY, "tools/claimcheck.py", doc], root)


@case("claimcheck", "precision-overclaim", "fail")
def _(root):
    seed_claimcheck(root)
    with open(os.path.join(root, "artifacts", "result.json"), "w") as fh:
        json.dump({"accuracy": 0.41, "baseline": 0.25, "n": 1000}, fh)
    doc = os.path.join(root, "docs", "report.md")
    with open(doc, "w") as fh:
        fh.write("Accuracy was 0.4123 on 1000 units.\n")
    return run([PY, "tools/claimcheck.py", doc], root)


@case("claimcheck", "number-hidden-in-code-fence-is-still-checked", "fail")
def _(root):
    doc = seed_claimcheck(root)
    with open(doc, "a") as fh:
        fh.write("\n```\nfinal_score = 0.777\n```\n")
    return run([PY, "tools/claimcheck.py", doc], root)


@case("claimcheck", "claim-adjacent-to-url-not-swallowed", "fail")
def _(root):
    doc = seed_claimcheck(root)
    with open(doc, "a") as fh:
        fh.write("See https://example.com/run/12345 which reports 0.633 accuracy.\n")
    return run([PY, "tools/claimcheck.py", doc], root)


@case("claimcheck", "allowlist-entry-without-reason-is-rejected", "fail")
def _(root):
    doc = seed_claimcheck(root)
    with open(os.path.join(root, "docs", "claimcheck_allowlist.tsv"), "a") as fh:
        fh.write("0.981\n")
    with open(doc, "a") as fh:
        fh.write("We reached 0.981.\n")
    return run([PY, "tools/claimcheck.py", doc], root)


@case("claimcheck", "allowlist-with-reason-admits-exactly-that-number", "pass")
def _(root):
    doc = seed_claimcheck(root)
    with open(os.path.join(root, "docs", "claimcheck_allowlist.tsv"), "a") as fh:
        fh.write("2026\tcalendar year, not a measurement\n")
    with open(doc, "a") as fh:
        fh.write("Written in 2026.\n")
    return run([PY, "tools/claimcheck.py", doc], root)


# ---------------------------------------------------------------- prereg chain gate

@case("prereg", "control-clean-chain-verifies", "pass")
def _(root):
    seed_prereg(root)
    return run([PY, "tools/prereg.py", "verify"], root)


@case("prereg", "sealed-bar-edited-after-freeze", "fail")
def _(root):
    path = seed_prereg(root)
    doc = json.load(open(path))
    doc["bar"]["acc"]["threshold"] = 0.05
    json.dump(doc, open(path, "w"), indent=2)
    return run([PY, "tools/prereg.py", "verify"], root)


@case("prereg", "reader-edited-after-freeze", "fail")
def _(root):
    seed_prereg(root)
    with open(os.path.join(root, "tools", "readers", "r.py"), "a") as fh:
        fh.write("print('adjusted after seeing the number')\n")
    return run([PY, "tools/prereg.py", "verify"], root)


@case("prereg", "reading-definition-swapped-after-freeze", "fail")
def _(root):
    path = seed_prereg(root)
    doc = json.load(open(path))
    doc["readings"][0]["json_path"] = "$.baseline"
    json.dump(doc, open(path, "w"), indent=2)
    return run([PY, "tools/prereg.py", "verify"], root)


@case("prereg", "chain-entry-hash-tampered", "fail")
def _(root):
    seed_prereg(root)
    chain = os.path.join(root, "prereg", "chain.jsonl")
    lines = [json.loads(x) for x in open(chain) if x.strip()]
    lines[0]["sealed_sha256"] = "0" * 64
    with open(chain, "w") as fh:
        for e in lines:
            fh.write(json.dumps(e, sort_keys=True) + "\n")
    return run([PY, "tools/prereg.py", "verify"], root)


@case("prereg", "prereg-inserted-out-of-order", "fail")
def _(root):
    seed_prereg(root)
    reader2 = os.path.join(root, "tools", "readers", "r2.py")
    open(reader2, "w").write("print('r2')\n")
    doc = json.load(open(os.path.join(root, "prereg", "0001-seed.json")))
    doc.update({"id": "0002", "slug": "second", "reader": "tools/readers/r2.py", "frozen": False})
    for k in ("chain_hash", "chain_prev_hash", "reader_sha256", "anchors", "frozen_utc", "git_commit"):
        doc.pop(k, None)
    p2 = os.path.join(root, "prereg", "0002-second.json")
    json.dump(doc, open(p2, "w"), indent=2)
    run([PY, "tools/prereg.py", "freeze", p2], root)
    chain = os.path.join(root, "prereg", "chain.jsonl")
    lines = [json.loads(x) for x in open(chain) if x.strip()]
    lines.reverse()
    with open(chain, "w") as fh:
        for e in lines:
            fh.write(json.dumps(e, sort_keys=True) + "\n")
    return run([PY, "tools/prereg.py", "verify"], root)


@case("prereg", "frozen-file-absent-from-chain", "fail")
def _(root):
    seed_prereg(root)
    chain = os.path.join(root, "prereg", "chain.jsonl")
    open(chain, "w").write("")
    return run([PY, "tools/prereg.py", "verify"], root)


@case("prereg", "freeze-refuses-when-reader-does-not-exist", "fail")
def _(root):
    doc = {
        "id": "0001", "slug": "noreader", "title": "t",
        "scope": {"one_line": "x"}, "bar": {"acc": {"threshold": 0.3, "passes_if": "acc>0.3"}},
        "readings": [{"name": "acc", "unit": "f", "source_artifact": "a.json", "json_path": "$.a"}],
        "arms": ["a"], "stop_rules": ["s"], "reader": "tools/readers/does_not_exist.py", "frozen": False,
    }
    path = os.path.join(root, "prereg", "0001-noreader.json")
    json.dump(doc, open(path, "w"), indent=2)
    return run([PY, "tools/prereg.py", "freeze", path], root)


@case("prereg", "double-freeze-refused", "fail")
def _(root):
    path = seed_prereg(root)
    return run([PY, "tools/prereg.py", "freeze", path], root)


# ---------------------------------------------------------------- scaling-curve gate

def _rungs(root, probs, m=400, ns=(1000, 10000, 100000, 1000000), seed=7):
    import random as _r
    rng = _r.Random(seed)
    rungs = [{"n_units": n, "per_example": [1 if rng.random() < p else 0 for _ in range(m)]}
             for n, p in zip(ns, probs)]
    path = os.path.join(root, "artifacts", "scores.json")
    json.dump({"rungs": rungs}, open(path, "w"))
    return path


@case("scaling", "control-rising-curve-is-called-positive", "pass")
def _(root):
    p = _rungs(root, [0.20, 0.31, 0.42, 0.55])
    rc, out = run([PY, "tools/scaling.py", p, "--boot", "600",
                   "--out", os.path.join(root, "artifacts", "fit.json")], root)
    if rc != 0:
        return rc, out
    fit = json.load(open(os.path.join(root, "artifacts", "fit.json")))
    ok = fit["primary_fit"]["positive_slope_survives"] is True
    return (0 if ok else 1), f"positive_slope_survives={fit['primary_fit']['positive_slope_survives']}"


@case("scaling", "flat-curve-is-NOT-called-positive", "fail")
def _(root):
    p = _rungs(root, [0.30, 0.30, 0.30, 0.30])
    rc, out = run([PY, "tools/scaling.py", p, "--boot", "600",
                   "--out", os.path.join(root, "artifacts", "fit.json")], root)
    if rc != 0:
        return rc, out
    fit = json.load(open(os.path.join(root, "artifacts", "fit.json")))
    ok = fit["primary_fit"]["positive_slope_survives"] is True
    return (0 if ok else 1), f"positive_slope_survives={fit['primary_fit']['positive_slope_survives']}"


@case("scaling", "declining-curve-is-NOT-called-positive", "fail")
def _(root):
    p = _rungs(root, [0.55, 0.42, 0.31, 0.20])
    rc, out = run([PY, "tools/scaling.py", p, "--boot", "600",
                   "--out", os.path.join(root, "artifacts", "fit.json")], root)
    if rc != 0:
        return rc, out
    fit = json.load(open(os.path.join(root, "artifacts", "fit.json")))
    ok = fit["primary_fit"]["positive_slope_survives"] is True
    return (0 if ok else 1), f"positive_slope_survives={fit['primary_fit']['positive_slope_survives']}"


@case("scaling", "tiny-eval-set-must-not-survive-the-interval", "fail")
def _(root):
    p = _rungs(root, [0.30, 0.32, 0.34, 0.36], m=12)
    rc, out = run([PY, "tools/scaling.py", p, "--boot", "600",
                   "--out", os.path.join(root, "artifacts", "fit.json")], root)
    if rc != 0:
        return rc, out
    fit = json.load(open(os.path.join(root, "artifacts", "fit.json")))
    ok = fit["primary_fit"]["positive_slope_survives"] is True
    return (0 if ok else 1), f"positive_slope_survives={fit['primary_fit']['positive_slope_survives']}"


@case("scaling", "three-rungs-refused-by-scope", "fail")
def _(root):
    p = _rungs(root, [0.2, 0.3, 0.4], ns=(1000, 10000, 100000))
    return run([PY, "tools/scaling.py", p, "--boot", "50"], root)


@case("scaling", "under-two-decades-refused-by-scope", "fail")
def _(root):
    p = _rungs(root, [0.2, 0.3, 0.4, 0.5], ns=(1000, 2000, 4000, 8000))
    return run([PY, "tools/scaling.py", p, "--boot", "50"], root)


@case("scaling", "unpaired-eval-sets-refused", "fail")
def _(root):
    p = _rungs(root, [0.2, 0.3, 0.4, 0.5])
    d = json.load(open(p))
    d["rungs"][0]["per_example"] = d["rungs"][0]["per_example"][:50]
    json.dump(d, open(p, "w"))
    return run([PY, "tools/scaling.py", p, "--boot", "50"], root)


# ---------------------------------------------------------------- A2 trivial-baseline gate

def _tb(root, kind="signal", n=1200, seed=3):
    import random as _r
    rng = _r.Random(seed)
    X, y = [], []
    for _ in range(n):
        f = [rng.gauss(0, 1) for _ in range(5)]
        if kind == "signal":
            lab = 1 if f[0] + 0.5 * f[1] + rng.gauss(0, 0.6) > 0 else 0
        elif kind == "noise":
            lab = rng.randint(0, 1)
        elif kind == "leaked":
            lab = 1 if f[0] > 0 else 0
            f = f + [float(lab)]          # the label is literally a feature
        X.append(f); y.append(lab)
    cut = int(n * 0.7)
    tr = os.path.join(root, "artifacts", "tb_tr.json")
    te = os.path.join(root, "artifacts", "tb_te.json")
    json.dump({"X": X[:cut], "y": y[:cut]}, open(tr, "w"))
    json.dump({"X": X[cut:], "y": y[cut:]}, open(te, "w"))
    return tr, te


@case("a2-baseline", "control-strong-model-clears-the-floor", "pass")
def _(root):
    tr, te = _tb(root)
    return run([PY, "tools/trivial_baselines.py", tr, te,
                "--claimed-score", "0.99", "--margin", "0.02"], root)


@case("a2-baseline", "weak-model-below-floor-is-rejected", "fail")
def _(root):
    tr, te = _tb(root)
    return run([PY, "tools/trivial_baselines.py", tr, te,
                "--claimed-score", "0.55", "--margin", "0.02"], root)


@case("a2-baseline", "margin-does-real-work-just-above-baseline-still-fails", "fail")
def _(root):
    tr, te = _tb(root)
    rc, out = run([PY, "tools/trivial_baselines.py", tr, te, "--out",
                   os.path.join(root, "artifacts", "tb.json")], root)
    if rc != 0:
        return rc, out
    best = json.load(open(os.path.join(root, "artifacts", "tb.json")))["best_baseline_accuracy"]["value"]
    return run([PY, "tools/trivial_baselines.py", tr, te,
                "--claimed-score", f"{best + 0.005:.6f}", "--margin", "0.05"], root)


@case("a2-baseline", "degenerate-leaked-label-makes-the-baseline-unbeatable", "fail")
def _(root):
    tr, te = _tb(root, kind="leaked")
    return run([PY, "tools/trivial_baselines.py", tr, te,
                "--claimed-score", "0.97", "--margin", "0.02"], root)


@case("a2-baseline", "pure-noise-labels-cannot-be-cleared", "fail")
def _(root):
    tr, te = _tb(root, kind="noise")
    return run([PY, "tools/trivial_baselines.py", tr, te,
                "--claimed-score", "0.52", "--margin", "0.05"], root)


@case("a2-baseline", "claimed-score-without-a-preregistered-margin-is-refused", "fail")
def _(root):
    tr, te = _tb(root)
    return run([PY, "tools/trivial_baselines.py", tr, te, "--claimed-score", "0.99"], root)


# ---------------------------------------------------------------- coverage-map gate

def _cov(root, claims):
    os.makedirs(os.path.join(root, "artifacts", "verification"), exist_ok=True)
    json.dump({"schema": "raise-v1/coverage_map/1", "claims": claims},
              open(os.path.join(root, "artifacts", "verification", "coverage.json"), "w"))
    json.dump({"detected": 30, "survived": 0, "score": 0.8026},
              open(os.path.join(root, "artifacts", "result.json"), "w"))
    os.makedirs(os.path.join(root, "tools", "repro"), exist_ok=True)
    open(os.path.join(root, "tools", "repro", "r.py"), "w").write("print('ok')\n")
    return run([PY, "tools/coverage.py"], root)


GOOD = [
    {"id": "a", "class": "primary-verifiable", "claim": "x", "value": 30,
     "artifact": "artifacts/result.json", "reverify": "python3 tools/repro/r.py"},
    {"id": "b", "class": "arithmetic-verifiable", "claim": "y", "value": 0,
     "artifact": "artifacts/result.json"},
    {"id": "c", "class": "neither", "claim": "z", "value": 0.8026,
     "artifact": "artifacts/result.json", "why_not_verifiable": "ephemeral scratch dir"},
]


@case("coverage", "control-coherent-map-passes", "pass")
def _(root):
    return _cov(root, [dict(c) for c in GOOD])


@case("coverage", "claim-citing-a-missing-artifact-is-rejected", "fail")
def _(root):
    c = [dict(x) for x in GOOD]
    c[0]["artifact"] = "artifacts/does_not_exist.json"
    return _cov(root, c)


@case("coverage", "value-absent-from-the-cited-artifact-is-rejected", "fail")
def _(root):
    c = [dict(x) for x in GOOD]
    c[0]["value"] = 0.4242
    return _cov(root, c)


@case("coverage", "primary-verifiable-without-a-reverify-command-is-rejected", "fail")
def _(root):
    c = [dict(x) for x in GOOD]
    c[0].pop("reverify")
    return _cov(root, c)


@case("coverage", "primary-verifiable-naming-a-script-that-does-not-exist-is-rejected", "fail")
def _(root):
    c = [dict(x) for x in GOOD]
    c[0]["reverify"] = "python3 tools/repro/ghost.py"
    return _cov(root, c)


@case("coverage", "neither-without-a-written-reason-is-rejected", "fail")
def _(root):
    c = [dict(x) for x in GOOD]
    c[2].pop("why_not_verifiable")
    return _cov(root, c)


@case("coverage", "invented-class-is-rejected", "fail")
def _(root):
    c = [dict(x) for x in GOOD]
    c[1]["class"] = "mostly-verifiable"
    return _cov(root, c)


@case("coverage", "weakest-class-is-printed-first", "pass")
def _(root):
    rc, out = _cov(root, [dict(x) for x in GOOD])
    if rc != 0:
        return rc, out
    i_n, i_a, i_p = out.find("NEITHER"), out.find("ARITHMETIC-VERIFIABLE"), out.find("PRIMARY-VERIFIABLE")
    ok = -1 < i_n < i_a < i_p
    return (0 if ok else 1), f"order neither={i_n} arithmetic={i_a} primary={i_p}"


# ---------------------------------------------------------------- pivot curve reader (prereg 0003)

PASSING_CURVE = {
    "n_rungs": 4, "decades_spanned": 3.0,
    "slope": 0.06, "slope_ci95_low": 0.04, "slope_ci95_high": 0.08,
    "top_rung_accuracy": 0.25, "best_trivial_baseline": 0.15,
    "chance_accuracy": 0.0385, "shuffled_label_accuracy": 0.039,
    "split_is_grouped_by_source": True, "n_classes": 26,
}


def _curve(root, **overrides):
    os.makedirs(os.path.join(root, "artifacts", "pivot"), exist_ok=True)
    os.makedirs(os.path.join(root, "tools", "readers"), exist_ok=True)
    shutil.copy(os.path.join(REPO, "tools", "readers", "pivot_deflate_curve.py"),
                os.path.join(root, "tools", "readers", "pivot_deflate_curve.py"))
    d = dict(PASSING_CURVE)
    for k, v in overrides.items():
        if v is _DROP:
            d.pop(k, None)
        else:
            d[k] = v
    json.dump(d, open(os.path.join(root, "artifacts", "pivot", "deflate_curve.json"), "w"))
    rc, out = run([PY, "tools/readers/pivot_deflate_curve.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(root, "artifacts", "pivot", "deflate_verdict.json")))
    ok = v["verdict"] == "CURVE_ESTABLISHED"
    return (0 if ok else 1), f"verdict={v['verdict']} failed={v['failed_clauses']}"


class _Drop:
    pass


_DROP = _Drop()


@case("pivot-curve", "control-passing-curve-is-established", "pass")
def _(root):
    return _curve(root)


@case("pivot-curve", "flat-slope-interval-touching-zero-is-rejected", "fail")
def _(root):
    return _curve(root, slope_ci95_low=0.0)


@case("pivot-curve", "negative-slope-is-rejected", "fail")
def _(root):
    return _curve(root, slope=-0.02, slope_ci95_low=-0.04, slope_ci95_high=-0.01)


@case("pivot-curve", "margin-just-below-the-frozen-0.05-is-rejected", "fail")
def _(root):
    return _curve(root, top_rung_accuracy=0.1999, best_trivial_baseline=0.15)


@case("pivot-curve", "three-rungs-rejected-by-scope", "fail")
def _(root):
    return _curve(root, n_rungs=3)


@case("pivot-curve", "under-two-decades-rejected-by-scope", "fail")
def _(root):
    return _curve(root, decades_spanned=1.9)


@case("pivot-curve", "ungrouped-split-is-rejected", "fail")
def _(root):
    return _curve(root, split_is_grouped_by_source=False)


@case("pivot-curve", "null-control-above-chance-is-rejected", "fail")
def _(root):
    return _curve(root, shuffled_label_accuracy=0.20)


@case("pivot-curve", "missing-slope-field-is-rejected", "fail")
def _(root):
    return _curve(root, slope_ci95_low=_DROP)


@case("pivot-curve", "missing-null-control-is-rejected", "fail")
def _(root):
    return _curve(root, shuffled_label_accuracy=_DROP)


@case("pivot-curve", "absent-artifact-emits-no-verdict", "fail")
def _(root):
    os.makedirs(os.path.join(root, "tools", "readers"), exist_ok=True)
    shutil.copy(os.path.join(REPO, "tools", "readers", "pivot_deflate_curve.py"),
                os.path.join(root, "tools", "readers", "pivot_deflate_curve.py"))
    return run([PY, "tools/readers/pivot_deflate_curve.py"], root)


# ---------------------------------------------------------------- EphemErr A2 reader (prereg 0005)

PASSING_A2 = {
    "learned_auc": 0.99, "best_baseline_auc": 0.90, "best_baseline_name": "per_satellite_mean",
    "baseline_aucs": {"per_satellite_mean": 0.90}, "shuffled_label_auc": 0.50,
    "split_is_temporal": True, "n_test_epochs": 50000, "n_satellites": 30, "positive_rate": 0.1,
}


def _a2(root, **ov):
    os.makedirs(os.path.join(root, "artifacts", "ephemerr"), exist_ok=True)
    os.makedirs(os.path.join(root, "tools", "readers"), exist_ok=True)
    shutil.copy(os.path.join(REPO, "tools", "readers", "ephemerr_a2_verdict.py"),
                os.path.join(root, "tools", "readers", "ephemerr_a2_verdict.py"))
    d = dict(PASSING_A2)
    for k, v in ov.items():
        d.pop(k, None) if v is _DROP else d.__setitem__(k, v)
    json.dump(d, open(os.path.join(root, "artifacts", "ephemerr", "a2_result.json"), "w"))
    rc, out = run([PY, "tools/readers/ephemerr_a2_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(root, "artifacts", "ephemerr", "a2_verdict.json")))
    return (0 if v["verdict"] == "A2_PASSED" else 1), f"verdict={v['verdict']} {v['failed_clauses']}"


@case("ephemerr-a2", "control-passing-result-is-accepted", "pass")
def _(root):
    return _a2(root)


@case("ephemerr-a2", "margin-0.0458-the-real-result-is-rejected", "fail")
def _(root):
    return _a2(root, learned_auc=0.9821, best_baseline_auc=0.9363)


@case("ephemerr-a2", "margin-one-ten-thousandth-below-the-bar-is-rejected", "fail")
def _(root):
    return _a2(root, learned_auc=0.9499, best_baseline_auc=0.90)


@case("ephemerr-a2", "non-temporal-split-is-rejected", "fail")
def _(root):
    return _a2(root, split_is_temporal=False)


@case("ephemerr-a2", "null-control-above-0.55-is-rejected", "fail")
def _(root):
    return _a2(root, shuffled_label_auc=0.70)


@case("ephemerr-a2", "too-few-test-epochs-is-rejected", "fail")
def _(root):
    return _a2(root, n_test_epochs=1000)


@case("ephemerr-a2", "too-few-satellites-is-rejected", "fail")
def _(root):
    return _a2(root, n_satellites=5)


@case("ephemerr-a2", "missing-null-control-is-rejected", "fail")
def _(root):
    return _a2(root, shuffled_label_auc=_DROP)


@case("ephemerr-a2", "absent-artifact-emits-no-verdict", "fail")
def _(root):
    os.makedirs(os.path.join(root, "tools", "readers"), exist_ok=True)
    shutil.copy(os.path.join(REPO, "tools", "readers", "ephemerr_a2_verdict.py"),
                os.path.join(root, "tools", "readers", "ephemerr_a2_verdict.py"))
    return run([PY, "tools/readers/ephemerr_a2_verdict.py"], root)


# ---------------------------------------------------------------- freshness gate
#
# claimcheck asks whether a number EXISTS in a banked artifact. freshness asks whether it is the
# CURRENT one. A stale number passes the first and must fail the second, so the control case and
# the stale cases below are the whole point of the gate.

def _fresh(root, doc_text=None, art=None, claims=None):
    os.makedirs(os.path.join(root, "artifacts", "verification"), exist_ok=True)
    art = art if art is not None else {"chain": [{"hash": "aaaaaaaa11"}, {"hash": "bbbbbbbb22"}],
                                       "items": [{"class": "x"}, {"class": "y"}, {"class": "x"}]}
    json.dump(art, open(os.path.join(root, "artifacts", "verification", "s.json"), "w"))
    doc = os.path.join(root, "docs", "report.md")
    with open(doc, "w") as fh:
        fh.write(doc_text if doc_text is not None else "chain: 2 entries, head `bbbbbbbb`\nx-class: 2\n")
    default = [
        {"id": "chain", "file": "docs/report.md",
         "pattern": r"chain: (\d+) entries, head `([0-9a-z]{8})`",
         "artifact": "artifacts/verification/s.json",
         "select": ["chain|len", "chain.-1.hash|head8"]},
        {"id": "xclass", "file": "docs/report.md", "pattern": r"x-class: (\d+)",
         "artifact": "artifacts/verification/s.json",
         "select": ["items|count:class=x"]},
    ]
    reg = os.path.join(root, "docs", "live_claims.json")
    json.dump({"claims": claims if claims is not None else default}, open(reg, "w"))
    return run([PY, "tools/freshness.py", "docs/live_claims.json"], root)


@case("freshness", "control-current-claims-pass", "pass")
def _(root):
    return _fresh(root)


@case("freshness", "stale-count-that-claimcheck-would-still-pass", "fail")
def _(root):
    # 1 is a real number and appears in the artifact's own structure, so claimcheck has no grounds
    # to object. It is simply no longer the count. That gap is why this gate exists.
    return _fresh(root, doc_text="chain: 1 entries, head `bbbbbbbb`\nx-class: 2\n")


@case("freshness", "stale-hash-that-was-true-earlier", "fail")
def _(root):
    return _fresh(root, doc_text="chain: 2 entries, head `aaaaaaaa`\nx-class: 2\n")


@case("freshness", "stale-count-under-a-filtered-path", "fail")
def _(root):
    return _fresh(root, doc_text="chain: 2 entries, head `bbbbbbbb`\nx-class: 3\n")


@case("freshness", "reworded-claim-is-not-silently-skipped", "fail")
def _(root):
    # The sentence changed so the pattern no longer matches. Treating that as "nothing to check"
    # would let any claim escape the gate by being rephrased.
    return _fresh(root, doc_text="the chain holds two entries\nx-class: 2\n")


@case("freshness", "missing-artifact-is-a-failure-not-a-skip", "fail")
def _(root):
    r = _fresh(root)
    os.remove(os.path.join(root, "artifacts", "verification", "s.json"))
    return run([PY, "tools/freshness.py", "docs/live_claims.json"], root)


@case("freshness", "path-that-does-not-resolve-is-a-failure", "fail")
def _(root):
    return _fresh(root, claims=[{"id": "bad", "file": "docs/report.md", "pattern": r"x-class: (\d+)",
                                 "artifact": "artifacts/verification/s.json",
                                 "select": ["no_such_key|len"]}])


@case("freshness", "unknown-path-operator-is-a-failure", "fail")
def _(root):
    return _fresh(root, claims=[{"id": "bad", "file": "docs/report.md", "pattern": r"x-class: (\d+)",
                                 "artifact": "artifacts/verification/s.json",
                                 "select": ["items|sum"]}])


@case("freshness", "group-count-not-matching-path-count-is-a-failure", "fail")
def _(root):
    return _fresh(root, claims=[{"id": "bad", "file": "docs/report.md",
                                 "pattern": r"chain: (\d+) entries, head `([0-9a-z]{8})`",
                                 "artifact": "artifacts/verification/s.json",
                                 "select": ["chain|len"]}])


# ---------------------------------------------------------------- topk gate (preregistration 0006)
#
# The operational-output reader. Its two hardest clauses are the ones a passing top-1 result does
# NOT imply: that the model's shortlist still beats a deep tree once ranking 5 of 26 makes the task
# easier, and that its confidence tracks its correctness well enough to abstain on.

GOOD_TOPK = {
    "n_rungs": 4, "decades_spanned": 2.9031,
    "top1_accuracy": 0.24, "top3_accuracy": 0.41, "top5_accuracy": 0.52,
    "best_trivial_baseline_top5": 0.31, "best_trivial_baseline_top5_name": "logistic",
    "best_baseline_expanded_top5": 0.40, "best_baseline_expanded_top5_name": "depth8_tree",
    "selective_top_decile_accuracy": 0.71,
    "baseline_selective_top_decile_accuracy": 0.60,
    "top5_slope": 0.09, "top5_slope_ci95_low": 0.08, "top5_slope_ci95_high": 0.10,
    "shuffled_label_top5_accuracy": 0.1925,
    "split_is_grouped_by_source": True, "n_classes": 26,
}


def _topk(root, art=GOOD_TOPK):
    """Run the reader, then translate its VERDICT into an exit code.

    The reader exits 0 whenever it successfully emits a verdict, pass or fail alike - a reader that
    exited non-zero on a negative finding would be conflating "the study failed" with "the reader
    broke". So the mutation has to be judged on the verdict, not on the process exit code. The first
    version of this helper skipped that step and 12 mutations "survived" that the reader was in fact
    catching perfectly; the harness reported them as holes, which is what it is for.
    """
    os.makedirs(os.path.join(root, "artifacts", "pivot"), exist_ok=True)
    json.dump(art, open(os.path.join(root, "artifacts", "pivot", "deflate_topk.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", "deflate_topk_verdict.py"),
                os.path.join(root, "tools", "readers", "deflate_topk_verdict.py"))
    rc, out = run([PY, "tools/readers/deflate_topk_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(root, "artifacts", "pivot", "deflate_topk_verdict.json")))
    ok = v["verdict"] == "OUTPUT_USABLE"
    return (0 if ok else 1), f"verdict={v['verdict']} shape={v['shape']} failed={v['failed_clauses']}"


def _mut(**kw):
    a = dict(GOOD_TOPK); a.update(kw); return a


@case("topk", "control-usable-output-passes", "pass")
def _(root):
    return _topk(root)


@case("topk", "top5-margin-over-the-FROZEN-set-below-bar-is-rejected", "fail")
def _(root):
    return _topk(root, _mut(best_trivial_baseline_top5=0.48))


@case("topk", "top5-margin-over-the-EXPANDED-set-below-bar-is-rejected", "fail")
def _(root):
    # The likely honest failure: ranking 5 of 26 is much easier than picking 1, so a deep tree can
    # close the gap even where top-1 was clear. 0003 reported this set voluntarily; here it binds.
    return _topk(root, _mut(best_baseline_expanded_top5=0.49))


@case("topk", "selective-margin-over-the-best-baseline-decile-is-rejected", "fail")
def _(root):
    return _topk(root, _mut(baseline_selective_top_decile_accuracy=0.69))


@case("topk", "selective-accuracy-below-the-0.50-usability-floor-is-rejected", "fail")
def _(root):
    # Clears the comparative margin and still fails: being better than a dumb rule is not the same
    # as being right more often than not on the fragments you are surest about.
    return _topk(root, _mut(selective_top_decile_accuracy=0.44,
                            baseline_selective_top_decile_accuracy=0.30))


@case("topk", "top5-slope-lower-bound-touching-zero-is-rejected", "fail")
def _(root):
    return _topk(root, _mut(top5_slope_ci95_low=0.0))


@case("topk", "null-control-above-the-5-of-26-chance-level-is-rejected", "fail")
def _(root):
    return _topk(root, _mut(shuffled_label_top5_accuracy=0.2124))


@case("topk", "non-grouped-split-is-rejected-however-good-the-numbers", "fail")
def _(root):
    return _topk(root, _mut(split_is_grouped_by_source=False, top5_accuracy=0.95))


@case("topk", "too-few-rungs-is-rejected", "fail")
def _(root):
    return _topk(root, _mut(n_rungs=3))


@case("topk", "too-few-decades-is-rejected", "fail")
def _(root):
    return _topk(root, _mut(decades_spanned=1.9999))


@case("topk", "a-missing-field-reads-as-failure-not-as-a-pass", "fail")
def _(root):
    a = dict(GOOD_TOPK); del a["selective_top_decile_accuracy"]
    return _topk(root, a)


@case("topk", "a-true-looking-string-is-not-True", "fail")
def _(root):
    return _topk(root, _mut(split_is_grouped_by_source="yes"))


@case("topk", "absent-artifact-emits-no-verdict", "fail")
def _(root):
    shutil.copy(os.path.join(REPO, "tools", "readers", "deflate_topk_verdict.py"),
                os.path.join(root, "tools", "readers", "deflate_topk_verdict.py"))
    return run([PY, "tools/readers/deflate_topk_verdict.py"], root)


@case("topk", "the-partial-outcome-is-NAMED-rather-than-left-spinnable", "fail")
def _(root):
    # Shortlist clauses pass, selective clauses fail. The reader must not merely say FAILED - it
    # must name the shape, because "a usable shortlist" is exactly what such a result would be
    # sold as. If the name is missing, return 0 so this registers as a SURVIVING mutation.
    rc, out = _topk(root, _mut(selective_top_decile_accuracy=0.40,
                               baseline_selective_top_decile_accuracy=0.38))
    if rc == 1 and "USABLE SHORTLIST, UNUSABLE CONFIDENCE" not in out:
        return 0, out + " !! failed the study without naming the partial shape"
    return rc, out


def main() -> int:
    results = []
    for c in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            root = sandbox(tmp)
            try:
                rc, out = c["fn"](root)
            except Exception as e:  # noqa: BLE001
                rc, out = -1, f"HARNESS ERROR: {e}"
            observed = "pass" if rc == 0 else "fail"
            ok = observed == c["expect"]
            results.append({
                "gate": c["gate"], "mutation": c["name"], "expected": c["expect"],
                "observed": observed, "exit_code": rc, "detected": ok,
                "evidence": out.strip().splitlines()[-1][:200] if out.strip() else "",
            })

    survived = [r for r in results if not r["detected"]]
    by_gate: dict[str, dict] = {}
    for r in results:
        g = by_gate.setdefault(r["gate"], {"total": 0, "detected": 0})
        g["total"] += 1
        g["detected"] += 1 if r["detected"] else 0

    report = {
        "schema": "raise-v1/mutation_report/1",
        "total_mutations": len(results),
        "detected": len(results) - len(survived),
        "survived": len(survived),
        "by_gate": by_gate,
        "cases": results,
    }
    outdir = os.path.join(REPO, "artifacts", "verification")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "mutation_report.json"), "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")

    # Guard: the coverage map hard-codes this count in a claim. Adding a mutation without updating
    # that claim turns CI red, and the failure is easy to miss because it surfaces one gate later.
    # Warn here, loudly, at the moment the count changes. coverage.py remains the actual gate.
    cov = os.path.join(REPO, "artifacts", "verification", "coverage.json")
    if os.path.exists(cov):
        try:
            claims = json.load(open(cov))["claims"]
            claimed = next((c.get("value") for c in claims if c.get("id") == "mutations-detected"), None)
            if claimed is not None and int(claimed) != len(results):
                print(f"\n!! artifacts/verification/coverage.json claims {claimed} mutations, this run "
                      f"has {len(results)}.\n!! Update the 'mutations-detected' claim or "
                      f"tools/coverage.py will fail and CI will go red.\n")
        except Exception:  # noqa: BLE001
            pass

    width = max(len(r["mutation"]) for r in results)
    for r in results:
        mark = "OK  " if r["detected"] else "HOLE"
        print(f"{mark}  {r['gate']:<11} {r['mutation']:<{width}}  expected={r['expected']:<4} "
              f"observed={r['observed']:<4} rc={r['exit_code']}")
    print(f"\nMUTATION REPORT: {report['detected']}/{report['total_mutations']} mutations detected")
    print(f"wrote artifacts/verification/mutation_report.json")
    if survived:
        print(f"\nSURVIVING MUTATIONS ({len(survived)}) - these gates have holes:")
        for r in survived:
            print(f"  - {r['gate']}: {r['mutation']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
