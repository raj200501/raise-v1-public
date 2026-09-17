#!/usr/bin/env python3
"""Mutation tests: proof that every gate in this repo is capable of failing.

A verifier that cannot fail is decoration. Each mutation below deliberately breaks one
thing and asserts that the relevant gate notices. A mutation that SURVIVES (the gate still
passes) is a hole in the instrument and is reported as such.

Each case runs against a throwaway copy of tools/ in a temp directory, so the real repo is
never mutated. Writes artifacts/verification/mutation_report.json.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import re
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
              "coverage.py", "freshness.py", "record_counts.py"):
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


@case("claimcheck", "svg-geometry-is-scrubbed-so-a-rendered-chart-can-pass", "pass")
def _(root):
    doc = seed_claimcheck(root)
    with open(os.path.join(root, "docs", "chart.html"), "w") as fh:
        fh.write('<svg viewBox="0 0 720 320"><circle cx="137.8" cy="229.9" r="4.5"/>'
                 '<text x="574.0" y="45.3">0.412</text></svg>\n')
    return run([PY, "tools/claimcheck.py", os.path.join(root, "docs", "chart.html")], root)


@case("claimcheck", "a-fabricated-number-in-svg-TEXT-is-still-caught", "fail")
def _(root):
    # The geometry scrub must not become a hole: what a chart DISPLAYS is a claim. 0.981 is drawn
    # at a scrubbed coordinate but its text content traces to nothing, and must still fail.
    doc = seed_claimcheck(root)
    with open(os.path.join(root, "docs", "chart.html"), "w") as fh:
        fh.write('<svg viewBox="0 0 720 320"><text x="574.0" y="45.3">0.981</text></svg>\n')
    return run([PY, "tools/claimcheck.py", os.path.join(root, "docs", "chart.html")], root)


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


# ---------------------------------------------------------------- record_counts gate
#
# The counts prose quotes about the record itself (how many corrections, how many chain entries)
# drifted in three outbound documents while every gate passed (CORRECTIONS.md, 2026-09-04).
# tools/record_counts.py banks the ledger's length; freshness ties each sentence to it. The gate is
# the pair, and the pair must fail when the ledger and the sentence disagree.

def _ledger(n_entries, template=False):
    head = "# Corrections ledger\n\nFormat:\n\n```\n## YYYY-MM-DD - <one-line description>\n```\n\n"
    if template:
        head += "## YYYY-MM-DD - a template heading left in the body\n\n"
    body = "".join(f"## 2026-08-{25 + i:02d} — correction {i}\n\n**Claimed:** x\n\n---\n\n" for i in range(n_entries))
    return head + body


def _counts(root, n_entries, prose_n, template=False):
    with open(os.path.join(root, "CORRECTIONS.md"), "w") as fh:
        fh.write(_ledger(n_entries, template))
    rc, out = run([PY, "tools/record_counts.py"], root)
    if rc != 0:
        return rc, out
    doc = os.path.join(root, "docs", "report.md")
    with open(doc, "w") as fh:
        fh.write(f"ledger: {prose_n} entries at full size\n")
    reg = os.path.join(root, "docs", "live_claims.json")
    json.dump({"claims": [{"id": "ledger", "file": "docs/report.md",
                           "pattern": r"ledger: (\d+) entries at full size",
                           "artifact": "artifacts/verification/record_counts.json",
                           "select": ["corrections_entries"]}]}, open(reg, "w"))
    return run([PY, "tools/freshness.py", "docs/live_claims.json"], root)


@case("record_counts", "control-ledger-and-prose-agree", "pass")
def _(root):
    return _counts(root, 2, 2)


@case("record_counts", "prose-count-stale-after-an-entry-was-filed", "fail")
def _(root):
    return _counts(root, 3, 2)


@case("record_counts", "prose-count-ahead-of-the-ledger", "fail")
def _(root):
    return _counts(root, 2, 3)


@case("record_counts", "template-heading-is-not-an-entry", "fail")
def _(root):
    # Two dated entries plus the format template's own heading: the tool must count 2, so prose
    # saying 3 has to fail.
    return _counts(root, 2, 3, template=True)


@case("record_counts", "empty-ledger-is-a-failure-not-zero", "fail")
def _(root):
    return _counts(root, 0, 0)


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


# ---------------------------------------------------------------- carve gate (preregistration 0007)
#
# This reader has THREE outcomes, not two, and the middle one (CARVE_SIZE_SPECIFIC) is a far softer
# statement than CARVE_FAILS. So the mutations check which verdict is emitted, not merely that the
# study failed - a reader that collapsed every negative into the softer label would pass a
# pass/fail-only test while misrepresenting the result.

GOOD_CARVE = {
    "carve_bytes": 1024, "reference_carve_bytes": 4096, "matched_rung": 100000,
    "n_rungs": 4, "decades_spanned": 2.6990,
    "within_top1": 0.17, "within_best_trivial_baseline": 0.09,
    "within_best_trivial_baseline_name": "logistic",
    "within_best_baseline_expanded": 0.11,
    "within_best_baseline_expanded_name": "depth16_tree",
    "within_slope": 0.04, "within_slope_ci95_low": 0.035,
    "transfer_top1": 0.15, "reference_matched_rung_top1": 0.1965,
    "chance_accuracy": 0.038462, "within_shuffled_label_accuracy": 0.0390,
    "within_split_is_grouped_by_source": True, "corpora_share_source_chunks": False,
    "n_classes": 26,
}


def _carve(root, art=GOOD_CARVE):
    os.makedirs(os.path.join(root, "artifacts", "pivot"), exist_ok=True)
    json.dump(art, open(os.path.join(root, "artifacts", "pivot",
                                     "carve_generalisation.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", "carve_generalisation_verdict.py"),
                os.path.join(root, "tools", "readers", "carve_generalisation_verdict.py"))
    rc, out = run([PY, "tools/readers/carve_generalisation_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(root, "artifacts", "pivot",
                                    "carve_generalisation_verdict.json")))
    ok = v["verdict"] == "CARVE_ROBUST"
    return (0 if ok else 1), (f"verdict={v['verdict']} within={v['within_size_failed_clauses']} "
                              f"transfer={v['transfer_failed_clauses']}")


def _cmut(**kw):
    a = dict(GOOD_CARVE); a.update(kw); return a


@case("carve", "control-robust-result-passes", "pass")
def _(root):
    return _carve(root)


@case("carve", "within-margin-over-the-frozen-set-below-bar-is-rejected", "fail")
def _(root):
    return _carve(root, _cmut(within_best_trivial_baseline=0.13))


@case("carve", "within-margin-over-the-expanded-set-below-bar-is-rejected", "fail")
def _(root):
    return _carve(root, _cmut(within_best_baseline_expanded=0.13))


@case("carve", "within-slope-lower-bound-touching-zero-is-rejected", "fail")
def _(root):
    return _carve(root, _cmut(within_slope_ci95_low=0.0))


@case("carve", "within-null-control-above-chance-plus-tolerance-is-rejected", "fail")
def _(root):
    return _carve(root, _cmut(within_shuffled_label_accuracy=0.0585))


@case("carve", "non-grouped-split-is-rejected-however-good-the-numbers", "fail")
def _(root):
    return _carve(root, _cmut(within_split_is_grouped_by_source=False, within_top1=0.95))


@case("carve", "too-few-rungs-is-rejected", "fail")
def _(root):
    return _carve(root, _cmut(n_rungs=3))


@case("carve", "too-few-decades-is-rejected", "fail")
def _(root):
    return _carve(root, _cmut(decades_spanned=1.9999))


@case("carve", "transfer-margin-below-bar-is-rejected", "fail")
def _(root):
    return _carve(root, _cmut(transfer_top1=0.13))


@case("carve", "corpora-sharing-source-chunks-invalidates-the-transfer-arm", "fail")
def _(root):
    # The chunk index IS the generator seed, so shared indices mean the transfer model is scored on
    # source bytes it trained on. A high transfer number under that condition is leakage, not
    # transfer, and must not be accepted.
    return _carve(root, _cmut(corpora_share_source_chunks=True, transfer_top1=0.60))


@case("carve", "an-unset-disjointness-flag-reads-as-failure-not-as-a-pass", "fail")
def _(root):
    a = dict(GOOD_CARVE); del a["corpora_share_source_chunks"]
    return _carve(root, a)


@case("carve", "a-missing-field-reads-as-failure-not-as-a-pass", "fail")
def _(root):
    a = dict(GOOD_CARVE); del a["within_slope_ci95_low"]
    return _carve(root, a)


@case("carve", "absent-artifact-emits-no-verdict", "fail")
def _(root):
    shutil.copy(os.path.join(REPO, "tools", "readers", "carve_generalisation_verdict.py"),
                os.path.join(root, "tools", "readers", "carve_generalisation_verdict.py"))
    return run([PY, "tools/readers/carve_generalisation_verdict.py"], root)


@case("carve", "a-transfer-only-failure-is-named-SIZE_SPECIFIC-not-collapsed-to-FAILS", "fail")
def _(root):
    rc, out = _carve(root, _cmut(transfer_top1=0.13))
    if rc != 0 and "verdict=CARVE_SIZE_SPECIFIC" not in out:
        return 0, out + " !! a transfer-only failure was not named CARVE_SIZE_SPECIFIC"
    return rc, out


@case("carve", "a-within-size-failure-is-NOT-softened-to-SIZE_SPECIFIC", "fail")
def _(root):
    # Both halves fail. The verdict must be the STRONGER negative. Reporting CARVE_SIZE_SPECIFIC
    # here would claim the information is present at the shorter carve when it is not.
    rc, out = _carve(root, _cmut(within_top1=0.10, transfer_top1=0.10))
    if rc != 0 and "verdict=CARVE_FAILS" not in out:
        return 0, out + " !! a within-size failure was softened to the milder verdict"
    return rc, out


# ---------------------------------------------------------------- carve2048 gate (preregistration 0011)
#
# The 0007 protocol at the midpoint carve, with two clauses 0007 did not have: the corpus must sit
# past BOTH earlier corpora by offset (not only by the flag the script sets), and the expanded margin
# must clear with the gutenberg family excluded - the family whose shared byte pool voids the
# disjointness guarantee. Both must be shown to fail on their own.

_MANIFEST = json.load(open(os.path.join(REPO, "artifacts", "pivot", "corpus_manifest.json")))
GOOD_CARVE2048 = {
    "preregistration": "0011-carve-2048-boundary",
    "carve_bytes": 2048, "carve_bytes_source": "cache metadata written at build time",
    "chunk_size": 32768, "eval_frac": 0.2,
    "sources_sha256": dict(_MANIFEST["sources_sha256"]),
    "reference_y_sha256": _MANIFEST["corpora"]["data/pivot/full_c4096.npz"]["y"]["sha256"],
    "reference_g_sha256": _MANIFEST["corpora"]["data/pivot/full_c4096.npz"]["g"]["sha256"],
    "reference_carve_bytes": 4096, "matched_rung": 100000,
    "transfer_model_top1_on_reference_eval": 0.1965,
    "within_slope_bootstrap_unit": "cluster", "within_slope_n_clusters": 5000,
    "within_slope_bootstrap_resamples": 2000,
    "seed": 20260825, "n_source_chunks": 25000,
    "rungs": [{"n_units": 1000, "accuracy": 0.06}, {"n_units": 10000, "accuracy": 0.10},
              {"n_units": 100000, "accuracy": 0.14}, {"n_units": 500000, "accuracy": 0.17}],
    "within_baselines_trained_on_n": 500000, "transfer_n_train": 100000,
    "n_rungs": 4, "decades_spanned": 2.6990,
    "within_top1": 0.17, "within_best_trivial_baseline": 0.09,
    "within_best_trivial_baseline_name": "logistic",
    "within_best_baseline_expanded": 0.11,
    "within_best_baseline_expanded_name": "depth16_tree",
    "within_top1_non_gutenberg": 0.18,
    "within_best_trivial_baseline_non_gutenberg": 0.092,
    "within_best_trivial_baseline_non_gutenberg_name": "logistic",
    "within_best_baseline_expanded_non_gutenberg": 0.115,
    "within_best_baseline_expanded_non_gutenberg_name": "depth16_tree",
    "within_slope": 0.04, "within_slope_ci95_low": 0.035,
    "transfer_top1": 0.15, "transfer_top1_non_gutenberg": 0.155,
    "reference_matched_rung_top1": 0.1965,
    "chance_accuracy": 0.038462, "within_shuffled_label_accuracy": 0.0390,
    "within_split_is_grouped_by_source": True, "corpora_share_source_chunks": False,
    "n_shared_source_chunks": 0, "corpus_b_chunk_offset": 75000, "corpus_b_chunk_id_max": 99999,
    "n_classes": 26,
}


def _carve2048(root, art=GOOD_CARVE2048):
    os.makedirs(os.path.join(root, "artifacts", "pivot"), exist_ok=True)
    json.dump(art, open(os.path.join(root, "artifacts", "pivot",
                                     "carve_generalisation_2048.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", "carve2048_verdict.py"),
                os.path.join(root, "tools", "readers", "carve2048_verdict.py"))
    rc, out = run([PY, "tools/readers/carve2048_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(root, "artifacts", "pivot",
                                    "carve_generalisation_2048_verdict.json")))
    ok = v["verdict"] == "CARVE_ROBUST"
    return (0 if ok else 1), (f"verdict={v['verdict']} boundary={v['boundary_bytes']} "
                              f"within={v['within_size_failed_clauses']} "
                              f"transfer={v['transfer_failed_clauses']}")


def _c2mut(**kw):
    a = dict(GOOD_CARVE2048); a.update(kw); return a


@case("carve2048", "control-robust-result-passes", "pass")
def _(root):
    return _carve2048(root)


@case("carve2048", "within-margin-over-the-frozen-set-below-bar-is-rejected", "fail")
def _(root):
    # transfer_top1 is raised so that ONLY the frozen-set within clause fails (isolating).
    rc, out = _carve2048(root, _c2mut(within_best_trivial_baseline=0.13, transfer_top1=0.30))
    if rc != 0 and "verdict=CARVE_FAILS" not in out:
        return 0, out + " !! the frozen-set within clause did not produce CARVE_FAILS on its own"
    return rc, out


@case("carve2048", "the-wrong-reference-carve-size-is-VOID", "fail")
def _(root):
    return _carve2048(root, _c2mut(reference_carve_bytes=2048))


@case("carve2048", "an-artifact-stamped-with-another-preregistration-is-VOID", "fail")
def _(root):
    rc, out = _carve2048(root, _c2mut(preregistration="0007-carve-size-generalisation"))
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! a foreign preregistration stamp was read as a result"
    return rc, out


@case("carve2048", "a-different-seed-is-VOID", "fail")
def _(root):
    return _carve2048(root, _c2mut(seed=7))


@case("carve2048", "a-different-rung-ladder-is-VOID-even-with-four-rungs", "fail")
def _(root):
    return _carve2048(root, _c2mut(rungs=[{"n_units": 1000}, {"n_units": 10000},
                                          {"n_units": 100000}, {"n_units": 400000}]))


@case("carve2048", "a-corpus-with-the-wrong-chunk-count-is-VOID", "fail")
def _(root):
    return _carve2048(root, _c2mut(n_source_chunks=24999))


@case("carve2048", "baselines-not-trained-on-the-top-rung-are-VOID", "fail")
def _(root):
    return _carve2048(root, _c2mut(within_baselines_trained_on_n=100000))


@case("carve2048", "an-unmatched-matched-rung-is-VOID", "fail")
def _(root):
    return _carve2048(root, _c2mut(matched_rung=800000, transfer_n_train=800000))


@case("carve2048", "a-transfer-model-fitted-on-more-rows-than-the-matched-rung-is-VOID", "fail")
def _(root):
    # matched_rung says 100000 but the script banks that it actually fitted on 800000 rows.
    rc, out = _carve2048(root, _c2mut(transfer_n_train=800000, transfer_top1=0.60,
                                      transfer_top1_non_gutenberg=0.60))
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! an over-trained transfer model was read as a result"
    return rc, out


@case("carve2048", "a-nonzero-shared-chunk-count-is-VOID-whatever-the-flag-says", "fail")
def _(root):
    rc, out = _carve2048(root, _c2mut(n_shared_source_chunks=3, corpora_share_source_chunks=False))
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! shared chunks were read as a transfer result instead of VOID"
    return rc, out


@case("carve2048", "within-margin-over-the-expanded-set-below-bar-is-rejected", "fail")
def _(root):
    return _carve2048(root, _c2mut(within_best_baseline_expanded=0.13))


@case("carve2048", "gutenberg-excluded-margin-below-bar-is-rejected-even-when-the-full-margin-clears", "fail")
def _(root):
    # Full-set margin 0.06 clears; the rows the disjointness guarantee actually covers do not.
    return _carve2048(root, _c2mut(within_best_baseline_expanded_non_gutenberg=0.14))


@case("carve2048", "a-missing-gutenberg-excluded-field-reads-as-failure-not-as-a-pass", "fail")
def _(root):
    a = _c2mut(); del a["within_top1_non_gutenberg"]
    return _carve2048(root, a)


@case("carve2048", "within-slope-lower-bound-touching-zero-is-rejected", "fail")
def _(root):
    return _carve2048(root, _c2mut(within_slope_ci95_low=0.0))


@case("carve2048", "within-null-control-above-chance-plus-tolerance-is-rejected", "fail")
def _(root):
    return _carve2048(root, _c2mut(within_shuffled_label_accuracy=0.0585))


@case("carve2048", "non-grouped-split-is-rejected-however-good-the-numbers", "fail")
def _(root):
    return _carve2048(root, _c2mut(within_split_is_grouped_by_source=False, within_top1=0.95,
                                   within_top1_non_gutenberg=0.95))


@case("carve2048", "too-few-rungs-is-rejected", "fail")
def _(root):
    return _carve2048(root, _c2mut(n_rungs=3))


@case("carve2048", "too-few-decades-is-rejected", "fail")
def _(root):
    return _carve2048(root, _c2mut(decades_spanned=1.9999))


@case("carve2048", "the-wrong-carve-size-is-rejected-the-reader-is-frozen-for-2048", "fail")
def _(root):
    return _carve2048(root, _c2mut(carve_bytes=1024))


@case("carve2048", "transfer-margin-below-bar-is-rejected", "fail")
def _(root):
    return _carve2048(root, _c2mut(transfer_top1=0.13))


@case("carve2048", "corpora-sharing-source-chunks-is-VOID-not-a-transfer-result", "fail")
def _(root):
    rc, out = _carve2048(root, _c2mut(corpora_share_source_chunks=True, n_shared_source_chunks=3,
                                      transfer_top1=0.60, transfer_top1_non_gutenberg=0.60))
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! overlapping corpora were read as a transfer result instead of VOID"
    return rc, out


@case("carve2048", "an-offset-inside-corpus-B-range-is-rejected-whatever-the-flag-says", "fail")
def _(root):
    # 50000 is past corpus A (so the script's flag would be False) but inside corpus B's range.
    return _carve2048(root, _c2mut(corpus_b_chunk_offset=50000, corpus_b_chunk_id_max=74999,
                                   corpora_share_source_chunks=False))


@case("carve2048", "a-corpus-redrawn-at-a-higher-offset-is-VOID-the-sealed-draw-is-exact", "fail")
def _(root):
    # Past both earlier corpora, disjoint, 25000 chunks - and not the preregistered draw.
    rc, out = _carve2048(root, _c2mut(corpus_b_chunk_offset=80000, corpus_b_chunk_id_max=104999))
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! a redrawn corpus was read as a result"
    return rc, out


@case("carve2048", "a-legacy-cache-whose-carve-comes-from-the-command-line-is-VOID", "fail")
def _(root):
    return _carve2048(root, _c2mut(carve_bytes_source="command line - legacy cache without build "
                                                      "metadata; the chunk-id range below is "
                                                      "measured from the data regardless"))


@case("carve2048", "a-different-eval-fraction-or-chunk-size-is-VOID", "fail")
def _(root):
    return _carve2048(root, _c2mut(eval_frac=0.1, chunk_size=16384))


@case("carve2048", "sources-that-do-not-hash-to-the-banked-edition-are-VOID", "fail")
def _(root):
    src = dict(GOOD_CARVE2048["sources_sha256"]); src["pg1342.txt"] = "81300b79" + "0" * 56
    rc, out = _carve2048(root, _c2mut(sources_sha256=src))
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! a corpus built from other source bytes was read as a result"
    return rc, out


@case("carve2048", "a-transfer-model-trained-on-an-unbanked-corpus-A-is-VOID", "fail")
def _(root):
    return _carve2048(root, _c2mut(reference_g_sha256="0" * 64))


@case("carve2048", "a-transfer-model-that-does-not-reproduce-corpus-A-is-VOID", "fail")
def _(root):
    # It should score 0.1965 on corpus A's own evaluation set; 0.17 means it is not that model.
    rc, out = _carve2048(root, _c2mut(transfer_model_top1_on_reference_eval=0.17))
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! a mis-trained transfer model was read as a transfer result"
    return rc, out


@case("carve2048", "a-fragment-level-slope-interval-in-the-gated-field-is-VOID", "fail")
def _(root):
    rc, out = _carve2048(root, _c2mut(within_slope_bootstrap_unit="example",
                                      within_slope_n_clusters=None))
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! an anti-conservative interval was gated on as if it were the cluster one"
    return rc, out


@case("carve2048", "a-margin-that-prints-as-exactly-0.0500-passes-not-a-float-artefact", "pass")
def _(root):
    # 0.1756 - 0.1256 is 0.05000000000000002 or 0.04999999999999999 depending on the platform;
    # the reader compares the difference rounded to 6 decimals, so it is exactly the bar and passes.
    return _carve2048(root, _c2mut(within_top1=0.1756, within_top1_non_gutenberg=0.1756,
                                   within_best_trivial_baseline=0.1256,
                                   within_best_baseline_expanded=0.1256,
                                   within_best_baseline_expanded_non_gutenberg=0.1256,
                                   within_best_trivial_baseline_non_gutenberg=0.1256,
                                   transfer_top1=0.1756, transfer_top1_non_gutenberg=0.1756))


@case("carve2048", "a-margin-that-prints-as-0.0499-fails-not-a-float-artefact", "fail")
def _(root):
    return _carve2048(root, _c2mut(within_top1=0.1755, within_top1_non_gutenberg=0.1756,
                                   within_best_trivial_baseline=0.1256,
                                   within_best_baseline_expanded=0.1256,
                                   within_best_baseline_expanded_non_gutenberg=0.1256,
                                   within_best_trivial_baseline_non_gutenberg=0.1256,
                                   transfer_top1=0.1756, transfer_top1_non_gutenberg=0.1756))


@case("carve2048", "an-unset-disjointness-flag-reads-as-failure-not-as-a-pass", "fail")
def _(root):
    a = _c2mut(); del a["corpora_share_source_chunks"]
    return _carve2048(root, a)


@case("carve2048", "a-missing-field-reads-as-failure-not-as-a-pass", "fail")
def _(root):
    a = _c2mut(); del a["within_top1"]
    return _carve2048(root, a)


@case("carve2048", "absent-artifact-emits-no-verdict", "fail")
def _(root):
    shutil.copy(os.path.join(REPO, "tools", "readers", "carve2048_verdict.py"),
                os.path.join(root, "tools", "readers", "carve2048_verdict.py"))
    return run([PY, "tools/readers/carve2048_verdict.py"], root)


@case("carve2048", "a-transfer-only-failure-is-named-SIZE_SPECIFIC-with-the-boundary-below-2048", "fail")
def _(root):
    rc, out = _carve2048(root, _c2mut(transfer_top1=0.13))
    if rc != 0 and ("verdict=CARVE_SIZE_SPECIFIC" not in out or "boundary=(1024, 2048]" not in out):
        return 0, out + " !! a transfer-only failure was not named SIZE_SPECIFIC with the right boundary"
    return rc, out


@case("carve2048", "a-within-size-failure-is-NOT-softened-and-places-the-boundary-above-2048", "fail")
def _(root):
    rc, out = _carve2048(root, _c2mut(within_top1=0.10, within_top1_non_gutenberg=0.10,
                                      transfer_top1=0.10, transfer_top1_non_gutenberg=0.10))
    if rc != 0 and ("verdict=CARVE_FAILS" not in out or "boundary=(2048, 4096]" not in out):
        return 0, out + " !! a within-size failure was softened or mis-bracketed"
    return rc, out


@case("carve2048", "gutenberg-excluded-transfer-margin-below-bar-is-rejected-even-when-the-full-margin-clears", "fail")
def _(root):
    # Full-row transfer margin 0.06 clears; on the rows the disjointness guarantee covers it does not.
    return _carve2048(root, _c2mut(transfer_top1_non_gutenberg=0.13))


@case("carve2048", "a-missing-gutenberg-excluded-transfer-field-is-VOID-not-a-pass", "fail")
def _(root):
    a = _c2mut(); del a["transfer_top1_non_gutenberg"]
    rc, out = _carve2048(root, a)
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! a missing field was read as a result rather than as VOID"
    return rc, out


@case("carve2048", "a-NaN-field-reads-as-VOID-not-as-a-pass", "fail")
def _(root):
    # json.dump writes NaN as a bare token and json.load reads it back; a reader that only checks
    # the field's TYPE would let NaN through every inequality, since every comparison with NaN
    # is False - including the ones that would have failed the clause.
    rc, out = _carve2048(root, _c2mut(within_top1=float("nan")))
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! a NaN was read as a result rather than as VOID"
    return rc, out


@case("carve2048", "a-scope-failure-is-named-VOID-and-brackets-no-boundary", "fail")
def _(root):
    # Too few rungs is not evidence that the task fails at 2048. A reader that turned it into
    # CARVE_FAILS would publish a boundary the data never measured.
    rc, out = _carve2048(root, _c2mut(n_rungs=3))
    if rc != 0 and ("verdict=VOID" not in out or "boundary=not bracketed by this run" not in out):
        return 0, out + " !! a scope failure was read as a result about the boundary"
    return rc, out


# ---------------------------------------------------------------- scaling gate (the slope fitter)
#
# Since 2026-09-02 the fitter performs the cluster bootstrap that 0011's slope clause gates on.
# The gate here is the fitter's own refusal and labelling: clustered evaluation rows must widen the
# interval, a groups array that does not match the evaluation set must be refused, and the unit
# must be labelled from what was done, not from what was asked.

def _scaling_scores(n_clusters=200, per=26, seed=0, drop_groups=False, bad_len=False):
    import random
    rng = random.Random(seed)
    m = n_clusters * per
    ids = [c for c in range(n_clusters) for _ in range(per)]
    rungs = []
    for k, n in enumerate((1000, 10000, 100000, 1000000)):
        # strongly clustered: every fragment of a chunk shares the chunk's outcome
        p = 0.05 + 0.05 * k
        chunk_ok = [1 if rng.random() < p else 0 for _ in range(n_clusters)]
        rungs.append({"n_units": n, "per_example": [chunk_ok[c] for c in ids]})
    d = {"rungs": rungs}
    if not drop_groups:
        d["eval_chunk_ids"] = ids[:-1] if bad_len else ids
    return d


def _scaling(root, scores):
    os.makedirs(os.path.join(root, "tools"), exist_ok=True)
    for f in ("scaling.py", "chainlib.py"):
        shutil.copy(os.path.join(REPO, "tools", f), os.path.join(root, "tools", f))
    p = os.path.join(root, "scores.json"); json.dump(scores, open(p, "w"))
    return run([PY, "tools/scaling.py", p, "--out", "fit.json"], root)


@case("scaling", "control-clustered-rows-widen-the-interval-and-it-is-labelled-cluster", "pass")
def _(root):
    rc, out = _scaling(root, _scaling_scores())
    if rc != 0:
        return rc, out
    rc2, out2 = _scaling(root, _scaling_scores(drop_groups=True))
    c = json.load(open(os.path.join(root, "fit.json")))
    if rc2 != 0:
        return rc2, out2
    # fit.json now holds the example-level fit; re-run the cluster one last so both are read
    rc, out = _scaling(root, _scaling_scores()); k = json.load(open(os.path.join(root, "fit.json")))
    wc = k["primary_fit"]["slope_ci95"][1] - k["primary_fit"]["slope_ci95"][0]
    we = c["primary_fit"]["slope_ci95"][1] - c["primary_fit"]["slope_ci95"][0]
    ok = k["bootstrap_unit"] == "cluster" and c["bootstrap_unit"] == "example" and wc > we * 1.5
    return (0 if ok else 1), (f"cluster width {wc:.5f} unit={k['bootstrap_unit']} n_clusters="
                              f"{k['n_clusters']} | example width {we:.5f} unit={c['bootstrap_unit']}")


@case("scaling", "a-groups-array-that-does-not-match-the-evaluation-set-is-refused", "fail")
def _(root):
    rc, out = _scaling(root, _scaling_scores(bad_len=True))
    if rc == 0:
        return 0, out + " !! a mismatched groups array was silently accepted"
    return rc, out


@case("scaling", "fewer-than-four-rungs-is-refused", "fail")
def _(root):
    sc = _scaling_scores(); sc["rungs"] = sc["rungs"][:3]
    return _scaling(root, sc)


# ---------------------------------------------------------------- c1 gate (preregistration 0008)
#
# A SEARCH reader. Its failure modes differ from a measurement reader's: the dangerous outcome is
# not a wrong number but a comforting negative produced by a search too narrow to conclude anything,
# so breadth is a clause and a narrow search voids rather than returns NO_FALSIFIER_FOUND.

def _c1_cand(**kw):
    c = {"name": "x", "withholding_mode": "privacy",
         "withholding_mechanism": "42 U.S.C. 1320d-6 bars disclosure of the underlying records",
         "withholding_is_after_the_fact_loss": False,
         "G1_abundance_verified": True, "G1_units": 5_000_000, "G1_source": "named registry",
         "G1_count_is_verified": True,
         "G2_manufacturer": True, "G3_monotonicity": True, "G4_white_space_firsthand": True,
         "G5_buyer_not_forensics": True, "G5_buyer_type": "regulator",
         "G5_why_not_forensics": "the buyer acts prospectively, gating a release",
         "G4_queries": [{"q": "a", "http_status": 200, "n_relevant": 0}],
         "laws_survived": {"L1": True, "L2": True, "L3": True, "L4": True},
         "law_reasons": {"L1": "r", "L2": "r", "L3": "r", "L4": "r"}}
    c.update(kw); return c


def _c1(root, cands=None):
    os.makedirs(os.path.join(root, "artifacts", "phase0"), exist_ok=True)
    if cands is None:
        cands = [_c1_cand(name=f"c{i}", withholding_mode=m)
                 for i, m in enumerate(["privacy", "regulation", "physics", "commercial"] * 3)]
    json.dump({"candidates": cands},
              open(os.path.join(root, "artifacts", "phase0", "c1_falsifier_search.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", "c1_falsifier_verdict.py"),
                os.path.join(root, "tools", "readers", "c1_falsifier_verdict.py"))
    rc, out = run([PY, "tools/readers/c1_falsifier_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(root, "artifacts", "phase0", "c1_falsifier_verdict.json")))
    return (0 if v["verdict"] == "C1_FALSIFIED" else 1), f"verdict={v['verdict']} sel={v['n_selected']}"


def _c1_all(**kw):
    """Twelve candidates covering all four modes, each mutated the same way."""
    modes = ["privacy", "regulation", "physics", "commercial"] * 3
    return [_c1_cand(name=f"c{i}", withholding_mode=m, **kw) for i, m in enumerate(modes)]


@case("c1", "control-a-real-falsifier-is-recognised", "pass")
def _(root):
    return _c1(root)


@case("c1", "after-the-fact-loss-cannot-falsify-the-conjecture-it-describes", "fail")
def _(root):
    return _c1(root, _c1_all(withholding_is_after_the_fact_loss=True))


@case("c1", "unstated-withholding-mechanism-is-rejected", "fail")
def _(root):
    return _c1(root, _c1_all(withholding_mechanism="   "))


@case("c1", "abundance-below-1e6-is-rejected", "fail")
def _(root):
    return _c1(root, _c1_all(G1_units=999_999))


@case("c1", "an-unverified-abundance-count-is-rejected", "fail")
def _(root):
    return _c1(root, _c1_all(G1_count_is_verified=False))


@case("c1", "a-G4-query-that-did-not-return-200-is-rejected", "fail")
def _(root):
    # The archived trial nearly published a white-space claim built on an HTTP 301 with 0 bytes.
    return _c1(root, _c1_all(G4_queries=[{"q": "a", "http_status": 301, "n_relevant": 0}]))


@case("c1", "a-G4-query-recording-no-status-at-all-is-rejected", "fail")
def _(root):
    return _c1(root, _c1_all(G4_queries=[{"q": "a", "n_relevant": 0}]))


@case("c1", "a-law-claimed-survived-with-no-reason-is-rejected", "fail")
def _(root):
    return _c1(root, _c1_all(law_reasons={"L1": "r", "L2": "", "L3": "r", "L4": "r"}))


@case("c1", "a-law-not-survived-is-rejected", "fail")
def _(root):
    return _c1(root, _c1_all(laws_survived={"L1": True, "L2": True, "L3": False, "L4": True}))


@case("c1", "a-forensics-buyer-confirms-the-conjecture-rather-than-falsifying-it", "fail")
def _(root):
    return _c1(root, _c1_all(G5_why_not_forensics=""))


@case("c1", "too-few-candidates-VOIDS-rather-than-returning-a-comforting-negative", "fail")
def _(root):
    rc, out = _c1(root, [_c1_cand(name=f"c{i}", withholding_mode=m, G1_units=1)
                         for i, m in enumerate(["privacy", "regulation", "physics", "commercial"])])
    if rc != 0 and "verdict=VOID_SEARCH_TOO_NARROW" not in out:
        return 0, out + " !! a too-narrow search returned a negative instead of voiding"
    return rc, out


@case("c1", "an-unexamined-withholding-mode-VOIDS-the-search", "fail")
def _(root):
    cands = [_c1_cand(name=f"c{i}", withholding_mode=m, G1_units=1)
             for i, m in enumerate(["privacy", "regulation", "privacy"] * 4)]
    rc, out = _c1(root, cands)
    if rc != 0 and "verdict=VOID_SEARCH_TOO_NARROW" not in out:
        return 0, out + " !! an unexamined mode did not void the search"
    return rc, out


@case("c1", "finding-nothing-must-NOT-promote-the-conjecture", "fail")
def _(root):
    # The whole discipline of filing C1 as a conjecture collapses if a failed search reads as
    # support. The reader must emit the disclaimer into its own artifact, not just print it.
    rc, out = _c1(root, _c1_all(G1_units=1))
    if rc == 0:
        return rc, out
    v = json.load(open(os.path.join(root, "artifacts", "phase0", "c1_falsifier_verdict.json")))
    if v.get("verdict") != "NO_FALSIFIER_FOUND":
        return 0, out + " !! a clean negative was not named NO_FALSIFIER_FOUND"
    if "not proof" not in str(v.get("no_falsifier_found_does_not_promote_c1", "")):
        return 0, out + " !! the verdict artifact does not carry the no-promotion disclaimer"
    return rc, out


@case("c1", "absent-artifact-emits-no-verdict", "fail")
def _(root):
    shutil.copy(os.path.join(REPO, "tools", "readers", "c1_falsifier_verdict.py"),
                os.path.join(root, "tools", "readers", "c1_falsifier_verdict.py"))
    return run([PY, "tools/readers/c1_falsifier_verdict.py"], root)


# ---------------------------------------------------------------- bytemodel gate (prereg 0009)
#
# Tests whether 0007's CARVE_FAILS is a property of the window or of the representation. Its
# distinctive clause is "beats hand": clearing the A2 margin while LOSING to the model it replaces
# would make the headline false, so that is a gate and not a footnote.

GOOD_BYTE = {
    "carve_bytes": 1024, "matched_rung": 100000, "n_train": 100000, "n_eval": 130000,
    "byte_model_top1": 0.19, "feature_model_top1": 0.1165,
    "best_trivial_baseline": 0.09, "best_trivial_baseline_name": "logistic",
    "best_baseline_expanded": 0.11, "best_baseline_expanded_name": "depth16_tree",
    "byte_model_shuffled_top1": 0.0390, "chance_accuracy": 0.038462,
    "split_is_grouped_by_source": True, "model_params": 182842, "epochs": 10, "n_classes": 26,
}


def _byte(root, art=GOOD_BYTE):
    os.makedirs(os.path.join(root, "artifacts", "pivot"), exist_ok=True)
    json.dump(art, open(os.path.join(root, "artifacts", "pivot", "byte_model.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", "byte_model_verdict.py"),
                os.path.join(root, "tools", "readers", "byte_model_verdict.py"))
    rc, out = run([PY, "tools/readers/byte_model_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(root, "artifacts", "pivot", "byte_model_verdict.json")))
    return (0 if v["verdict"] == "BYTE_MODEL_CLEARS" else 1), \
        f"verdict={v['verdict']} failed={v['failed_clauses']}"


def _bmut(**kw):
    a = dict(GOOD_BYTE); a.update(kw); return a


@case("bytemodel", "control-a-better-representation-is-recognised", "pass")
def _(root):
    return _byte(root)


@case("bytemodel", "A2-margin-below-bar-is-rejected", "fail")
def _(root):
    return _byte(root, _bmut(best_trivial_baseline=0.15))


@case("bytemodel", "clearing-A2-while-LOSING-to-the-model-it-replaces-is-rejected", "fail")
def _(root):
    # The clause that matters: 0.19 clears A2 over a 0.09 baseline, but a feature model at 0.20
    # means the byte representation is a different way of failing, not a better representation.
    return _byte(root, _bmut(feature_model_top1=0.20))


@case("bytemodel", "merely-tying-the-hand-engineered-model-is-rejected", "fail")
def _(root):
    return _byte(root, _bmut(feature_model_top1=0.19))


@case("bytemodel", "null-control-above-chance-catches-a-memorising-network", "fail")
def _(root):
    return _byte(root, _bmut(byte_model_shuffled_top1=0.0585))


@case("bytemodel", "non-grouped-split-is-rejected-however-good-the-numbers", "fail")
def _(root):
    return _byte(root, _bmut(split_is_grouped_by_source=False, byte_model_top1=0.95))


@case("bytemodel", "an-unmatched-rung-voids-the-comparison", "fail")
def _(root):
    # Training on more rows than the feature model saw would make "beats hand" meaningless.
    return _byte(root, _bmut(n_train=500000))


@case("bytemodel", "a-missing-field-reads-as-failure-not-as-a-pass", "fail")
def _(root):
    a = dict(GOOD_BYTE); del a["feature_model_top1"]
    return _byte(root, a)


@case("bytemodel", "absent-artifact-emits-no-verdict", "fail")
def _(root):
    shutil.copy(os.path.join(REPO, "tools", "readers", "byte_model_verdict.py"),
                os.path.join(root, "tools", "readers", "byte_model_verdict.py"))
    return run([PY, "tools/readers/byte_model_verdict.py"], root)


@case("bytemodel", "a-negative-is-reported-as-STRENGTHENING-L4-not-as-inconclusive", "fail")
def _(root):
    rc, out = _byte(root, _bmut(byte_model_top1=0.10))
    if rc != 0:
        v = json.load(open(os.path.join(root, "artifacts", "pivot", "byte_model_verdict.json")))
        if "strengthens" not in v.get("meaning", ""):
            return 0, out + " !! a negative did not state that it strengthens L4"
    return rc, out


# ---------------------------------------------------------------- byteflat gate (prereg 0010)
#
# The gate that exists because a null control the model CANNOT FAIL carries no information. That is
# the mutation-testing argument applied to controls instead of gates, and the clause enforcing it is
# the reason this reader exists rather than a re-run of 0009's.

GOOD_FLAT = {
    "carve_bytes": 1024, "matched_rung": 100000, "n_train": 100000, "n_eval": 130000,
    "flat_model_top1": 0.21, "pooled_model_top1": 0.0849, "feature_model_top1": 0.1165,
    "best_trivial_baseline": 0.0943, "best_trivial_baseline_name": "logistic",
    "null_train_top1": 0.62, "null_eval_top1": 0.0389, "chance_accuracy": 0.038462,
    "split_is_grouped_by_source": True, "eval_group_fingerprint_matches_0007": True,
    "model_params": 396000, "epochs": 10,
}


def _flat(root, art=GOOD_FLAT):
    os.makedirs(os.path.join(root, "artifacts", "pivot"), exist_ok=True)
    json.dump(art, open(os.path.join(root, "artifacts", "pivot", "byte_model_flat.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", "byte_model_flat_verdict.py"),
                os.path.join(root, "tools", "readers", "byte_model_flat_verdict.py"))
    rc, out = run([PY, "tools/readers/byte_model_flat_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(root, "artifacts", "pivot",
                                    "byte_model_flat_verdict.json")))
    return (0 if v["verdict"] == "BYTE_FLAT_CLEARS" else 1), \
        f"verdict={v['verdict']} failable={v['null_control_was_failable']} meaning={v['meaning'][:60]}"


def _fmut(**kw):
    a = dict(GOOD_FLAT); a.update(kw); return a


@case("byteflat", "control-a-head-change-that-works-is-recognised", "pass")
def _(root):
    return _flat(root)


@case("byteflat", "an-UNFAILABLE-null-control-is-rejected-however-clean-it-looks", "fail")
def _(root):
    # The whole point. Evaluation control at chance, everything else passing, but the model cannot
    # fit shuffled labels - so the clean control was guaranteed by architecture and means nothing.
    return _flat(root, _fmut(null_train_top1=0.05))


@case("byteflat", "an-unfailable-control-is-named-INCONCLUSIVE-not-a-negative", "fail")
def _(root):
    rc, out = _flat(root, _fmut(null_train_top1=0.05))
    if rc != 0 and "Inconclusive" not in out:
        return 0, out + " !! an unfailable control was reported as a negative rather than as inconclusive"
    return rc, out


@case("byteflat", "a-failable-control-negative-is-named-STRONGER-than-0009", "fail")
def _(root):
    rc, out = _flat(root, _fmut(flat_model_top1=0.09))
    if rc != 0 and "STRONGER" not in out:
        return 0, out + " !! a negative with a failable control was not named stronger than 0009"
    return rc, out


@case("byteflat", "a-leaking-null-control-is-rejected", "fail")
def _(root):
    return _flat(root, _fmut(null_eval_top1=0.0585))


@case("byteflat", "A2-margin-below-bar-is-rejected", "fail")
def _(root):
    return _flat(root, _fmut(best_trivial_baseline=0.17))


@case("byteflat", "tying-the-pooled-head-has-answered-nothing-and-is-rejected", "fail")
def _(root):
    return _flat(root, _fmut(pooled_model_top1=0.21))


@case("byteflat", "losing-to-the-hand-engineered-model-is-rejected", "fail")
def _(root):
    return _flat(root, _fmut(feature_model_top1=0.25))


@case("byteflat", "an-unfingerprinted-evaluation-set-is-rejected", "fail")
def _(root):
    return _flat(root, _fmut(eval_group_fingerprint_matches_0007=False))


@case("byteflat", "an-unmatched-rung-voids-the-comparison", "fail")
def _(root):
    return _flat(root, _fmut(n_train=500000))


@case("byteflat", "a-missing-field-reads-as-failure-not-as-a-pass", "fail")
def _(root):
    a = dict(GOOD_FLAT); del a["null_train_top1"]
    return _flat(root, a)


@case("byteflat", "absent-artifact-emits-no-verdict", "fail")
def _(root):
    shutil.copy(os.path.join(REPO, "tools", "readers", "byte_model_flat_verdict.py"),
                os.path.join(root, "tools", "readers", "byte_model_flat_verdict.py"))
    return run([PY, "tools/readers/byte_model_flat_verdict.py"], root)



# ---------------------------------------------------------------- recipe2048 gate (preregistrations 0012 and 0013)
#
# A symmetric recipe search: the reader re-derives every winner, re-hashes the roster, requires the
# sealed partition hashes, floors the searched baselines at 0011's values, requires one scoring per
# role with the model last, and reads VOID on any baseline that dropped out. Each of those must be
# shown to fail on its own.

_R12 = json.load(open(os.path.join(REPO, "prereg", "0012-recipe-search-2048.json")))["scope"]["roster"]
_ENV12 = {"threads": 3, "nice": 10, "sklearn": "1.9.0", "numpy": "2.4.6", "python": "3.11.15"}


def _canon12(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha12(o):
    return hashlib.sha256(_canon12(o).encode("utf-8")).hexdigest()


# ---- The five readers below (0012/0014, 0015, 0016, 0017, 0018/0019) take their gate controls' SHAPE from the banked
# runner artifact of the run each reader actually read (docs/OPERATING_RULES.md section 4: "the runner's output
# shape"). Until 2026-09-17 every one of them built `partition`, `corpus` (and `ext_corpus`) as dict(<reader>.PARTITION)
# and so on - the reader's own literals - and wrote fit records with a field set of the test's own: 6 to 8 runner-written
# fields absent from every record (heartbeat_max_rss_gb, utc, rss_gb, ...), 1 to 5 from every partition (eval_frac, seed,
# top_rung, holdout_chunks_per_family, ...), 1 to 6 from the top level, and nothing able to notice. CORRECTIONS.md
# 2026-09-16 filed the class for realfit4096 and undercounted the siblings; the entry of 2026-09-17 closes it. The VALUES
# are still the sealed ones; the KEY SET at every level is the runner's, via _rf_sub (defined with the realfit gate
# below) and _shape_fill, and one pass/fail pair per gate, registered before main(), holds the two together.

_BANKED_SHAPE = {"recipe2048": "recipe_search_2048.json", "recipe4096": "recipe_search_4096.json",
                 "lofo4096": "lofo_4096.json", "fdc4096": "fdc_4096.json", "lofol3": "lofo_l3_4096.json",
                 "oob4096": "oob_4096.json"}


def _banked_shape(gate):
    """The runner artifact the gate's reader read, as banked: the control's shape source."""
    return json.load(open(os.path.join(REPO, "artifacts", "pivot", _BANKED_SHAPE[gate]), encoding="utf-8"))


def _shape_fill(shape_block, control_block, label):
    """A block the control assembles field by field, completed to the runner's key set: every key the runner wrote and
    the control does not set is carried at its banked value, and a key the control sets that the runner never wrote is
    refused, because an invented key is a reader expectation in disguise (the `ledger` 0020's control injected)."""
    invented = sorted(set(control_block) - set(shape_block))
    if invented:
        raise AssertionError(f"{label}: the control carries keys the runner never writes: {invented}")
    return dict(shape_block, **control_block)


def _shape_problems(art, shape, blocks, records, reader_blocks):
    """Both directions, at every level a reader compares: the top level, each named block, each fit record; and every
    key a reader seals must be one the runner writes. Returns the disagreements (an empty list is the pass)."""
    problems = []
    if set(shape) != set(art):
        problems.append(f"top-level key sets differ: control-only {sorted(set(art) - set(shape))}, "
                        f"runner-only {sorted(set(shape) - set(art))}")
    for label, a, b in blocks:
        if set(a) != set(b):
            problems.append(f"{label}: control-only {sorted(set(a) - set(b))}, runner-only {sorted(set(b) - set(a))}")
    for label, a, b in records:
        if set(a) != set(b):
            problems.append(f"record {label}: control-only {sorted(set(a) - set(b))}, runner-only {sorted(set(b) - set(a))}")
    for name, sealed, blk in reader_blocks:
        unwritten = sorted(set(sealed) - set(blk))
        if unwritten:
            problems.append(f"the reader's {name} expects keys the runner never writes: {unwritten}")
    return problems


_CFG2048 = {"gate": "recipe2048", "reader": "recipe2048_verdict.py", "prereg": "0012-recipe-search-2048.json",
            "conf": {"majority": (0.0385, 0.0385), "stratified": (0.0385, 0.0385), "best_single_feat": (0.0726, 0.0762),
                     "depth3_tree": (0.09, 0.091), "deep_tree": (0.15, 0.155), "logistic": (0.13, 0.135),
                     "model": (0.21, 0.22)},
            "incumbent": (0.1741, 0.1819), "l1": (0.1266, 0.1315), "stamp": "0012-recipe-search-2048"}
_CFG4096 = {"gate": "recipe4096", "reader": "recipe4096_verdict.py", "prereg": "0014-recipe-search-4096.json",
            "conf": {"majority": (0.0385, 0.0385), "stratified": (0.0387, 0.0388), "best_single_feat": (0.0751, 0.0769),
                     "depth3_tree": (0.10, 0.101), "deep_tree": (0.19, 0.195), "logistic": (0.15, 0.155),
                     "model": (0.26, 0.27)},
            "incumbent": (0.2395, 0.2475), "l1": (0.1392, 0.1438), "stamp": "0014-recipe-search-4096"}


def _good_recipe2048(cfg=None):
    """A complete, valid artifact set whose numbers give RECIPE_CLEARS (2048: model 0.21 against a
    floored frozen bar 0.13 and an expanded bar 0.15; 4096: 0.26 against 0.15 and 0.19)."""
    cfg = cfg or _CFG2048
    import importlib.util
    spec = importlib.util.spec_from_file_location("r12", os.path.join(REPO, "tools", "readers", cfg["reader"]))
    r12 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r12)
    shape = _banked_shape(cfg["gate"])          # the run this reader read: the control's shape at every level
    part = _rf_sub(shape["partition"], dict(r12.PARTITION), f"{cfg['gate']} partition", sealed_may_be_subset=True)
    _R = json.load(open(os.path.join(REPO, "prereg", cfg["prereg"])))["scope"]["roster"]
    proto = _R["protocol"]; heads = _R["heads"]
    by_id = {c["id"]: c for h in heads for c in h["candidates"]}
    fam8 = ["gutenberg", "base64", "binary", "code", "csv", "json", "log", "mixed"]

    # the runner's own record of the same head (selection and confirmatory records share one field set)
    tmpl = dict({h: shape["final"][h] for h in shape["final"]}, incumbent=shape["incumbent_refit"],
                logistic_l1=shape["logistic_l1_refit"], null=shape["null_control"])

    def rec(head, cid, stage, n_rows, rows_sha, sorted_sha, top1, ng):
        c = by_id[cid]
        return _rf_sub(tmpl[head], {"id": cid, "head": head, "family": c["family"], "params": c.get("params", {}),
                "scaled": bool(c.get("scaled", False)), "val": c.get("val"), "seed": 20260825,
                "params_sha256": _sha12(c), "stage": stage, "n_fit_rows": n_rows, "fit_rows_sha256": rows_sha,
                "fit_rows_sorted_sha256": sorted_sha, "environment": dict(_ENV12), "status": "fit",
                "seconds": 1.0, "top1": top1, "top1_non_gutenberg": ng,
                "per_family": {f: round(top1, 4) for f in fam8}, "block_refills": [], "fit_info": {}},
                       f"record {head}/{cid}/{stage}", sealed_may_be_subset=True)

    # selection: stage-1 scores rise with roster index except M1/L1 (index 0) so the winner is a
    # searched recipe; keep 2 then 1
    sel_scores = {"model": {"M1": 0.14, "M2": 0.15, "M3": 0.16, "M4": 0.155, "M5": 0.12, "M6": 0.13, "M7": 0.11, "M8": 0.145},
                  "logistic": {"L1": 0.10, "L2": 0.11, "L3": 0.13, "L4": 0.125, "L5": 0.09, "L6": 0.12, "L7": 0.129, "L8": 0.124},
                  "depth3_tree": {"D1": 0.088, "D2": 0.088, "D3": 0.087, "D4": 0.086, "D5": 0.089, "D6": 0.0885, "D7": 0.088, "D8": 0.085},
                  "deep_tree": {"T1": 0.125, "T2": 0.144, "T3": 0.146, "T4": 0.143, "T5": 0.147, "T6": 0.14, "T7": 0.145, "T8": 0.149}}
    selection, selected = {}, {}
    for h in heads:
        hid = h["id"]
        if len(h["candidates"]) == 1:
            selection[hid] = {"side": h["side"], "stages": [], "selected_id": h["candidates"][0]["id"]}
            selected[hid] = h["candidates"][0]["id"]; continue
        stages, survivors = [], [c["id"] for c in h["candidates"]]
        for si in range(2):
            n, rs, ss = part["stage_rows"][si], part["stage_idx_sha256"][si], part["stage_sorted_sha256"][si]
            fit_order = [c["id"] for c in h["candidates"] if c["id"] in survivors]   # the runner fits survivors in ROSTER order
            recs = [rec(hid, cid, f"selection-{si + 1}", n, rs, ss, sel_scores[hid][cid],
                        round(sel_scores[hid][cid] + 0.005, 4)) for cid in fit_order]
            ranked = sorted(survivors, key=lambda cid: -sel_scores[hid][cid])
            keep = proto["stages"][si]["keep"]
            stages.append({"stage": si + 1, "n_fit_rows": n, "fit_rows_sha256": rs, "records": recs,
                           "eligible_ranked_ids": ranked, "advanced_ids": ranked[:keep]})
            survivors = ranked[:keep]
        selection[hid] = {"side": h["side"], "stages": stages, "selected_id": survivors[0]}
        selected[hid] = survivors[0]
    sel_part = {k: v for k, v in part.items() if k != "eval_y_sha256"}
    corpus = _rf_sub(shape["corpus"], dict(r12.CORPUS), f"{cfg['gate']} corpus", sealed_may_be_subset=True)
    sel_doc = _shape_fill(shape["selection"], {"schema_version": 1, "preregistration": cfg["stamp"], "smoke": False,
               "roster_sha256": _sha12(_R), "roster": _R, "corpus": corpus, "partition": sel_part,
               "n_classes": 26, "class_names": [], "chance_accuracy": 0.038462, "stage": "select",
               "gathers": [{"name": "holdout", "n_rows": part["n_holdout_rows"], "n_eval_rows": 0}],
               "eval_rows_gathered_in_selection": 0, "environment": dict(_ENV12), "selection": selection,
               "selected_ids": selected, "ledger": [], "cost": {"selection_seconds_total": 1.0},
               "selection_started_utc": "2026-09-04T00:00:00Z", "selection_finished_utc": "2026-09-04T01:00:00Z"}, "selection")
    sel_bytes = _canon12(sel_doc).encode("utf-8")
    pool_sha, pool_sorted = part["pool_idx_sha256"], part["pool_sorted_sha256"]
    conf = cfg["conf"]
    final = {hid: rec(hid, selected[hid], "confirmatory", part["n_pool_rows"], pool_sha, pool_sorted, *conf[hid]) for hid in conf}
    inc = rec("incumbent", "M1", "confirmatory", part["n_pool_rows"], pool_sha, pool_sorted, *cfg["incumbent"])
    l1 = rec("logistic_l1", "L1", "confirmatory", part["n_pool_rows"], pool_sha, pool_sorted, *cfg["l1"])
    null = rec("null", selected["model"], "null", 20000, "x", r12.NULL_SORTED_SHA256, 0.039, 0.039)
    order = ["confirm_incumbent", "confirm_logistic_l1", "confirm_majority", "confirm_stratified",
             "confirm_best_single_feat", "confirm_depth3_tree", "confirm_deep_tree", "confirm_logistic",
             "confirm_null", "confirm_model"]
    sel_sha = hashlib.sha256(sel_bytes).hexdigest()
    ledger = []
    for i, nm in enumerate(order):
        ledger += [{"name": nm, "fingerprint": nm, "event": "selection_bound", "selection_sha256": sel_sha},
                   {"name": nm, "fingerprint": nm, "event": "started", "utc": f"2026-09-04T02:{i:02d}:00Z"},
                   {"name": nm, "fingerprint": nm, "event": "completed", "utc": f"2026-09-04T02:{i:02d}:30Z"}]
    floors, floors_ng = proto["floors"], proto["floors_non_gutenberg"]
    frozen = ["majority", "stratified", "depth3_tree", "logistic"]; expanded = frozen + ["best_single_feat", "deep_tree"]
    bf = max(max(conf[h][0], floors[h]) for h in frozen); be = max(max(conf[h][0], floors[h]) for h in expanded)
    ben = max(max(conf[h][1], floors_ng[h]) for h in expanded)
    bfn = max(max(conf[h][1], floors_ng[h]) for h in frozen)
    art = _shape_fill(shape, {"schema_version": 1, "preregistration": cfg["stamp"], "smoke": False, "stage": "confirm",
           "roster_sha256": _sha12(_R), "roster": _R, "corpus": corpus, "partition": part, "n_classes": 26,
           "class_names": [], "chance_accuracy": 0.038462, "selection_sha256": sel_sha, "selection": sel_doc,
           "selected_ids": selected, "selected_model_id": selected["model"], "environment": dict(_ENV12),
           "complete": True, "missing_roles": [], "final": final,
           "final_top1": conf["model"][0], "final_top1_non_gutenberg": conf["model"][1],
           "final_per_family": final["model"]["per_family"], "final_status": "fit",
           "best_frozen_for_bar": bf, "best_frozen_searched": conf["logistic"][0], "best_frozen_head": "logistic",
           "best_frozen_non_gutenberg_for_bar": bfn, "best_frozen_non_gutenberg_searched": conf["logistic"][1],
           "best_expanded_for_bar": be, "best_expanded_searched": conf["deep_tree"][0], "best_expanded_head": "deep_tree",
           "best_expanded_non_gutenberg_for_bar": ben, "best_expanded_non_gutenberg_searched": conf["deep_tree"][1],
           "best_expanded_non_gutenberg_head": "deep_tree",
           "incumbent_refit": inc, "incumbent_refit_top1": cfg["incumbent"][0], "logistic_l1_refit": l1,
           "logistic_l1_refit_top1": cfg["l1"][0], "null_control": null, "shuffled_label_accuracy": 0.039,
           "null_rows": 20000, "cluster_ci95_informational": {}, "ledger": ledger, "cost": {},
           "confirmatory_started_utc": "2026-09-04T02:00:00Z"}, "artifact")
    scores = {"per_example": {k: [1] * part["n_eval_rows"] for k in list(conf) + ["incumbent", "logistic_l1"]}}
    return art, sel_bytes, scores


def _recipe2048(root, mutate=None, sel_bytes_override=None, drop_artifact=False, not_run=None,
                reader="recipe2048_reread_verdict.py", verdict_file="recipe_search_2048_reread_verdict.json",
                cfg=None, tag="2048"):
    art, sel_bytes, scores = _good_recipe2048(cfg)
    if mutate:
        r = mutate(art, scores)
        if r is not None:
            art = r
    piv = os.path.join(root, "artifacts", "pivot"); os.makedirs(piv, exist_ok=True)
    with open(os.path.join(piv, f"recipe_search_{tag}_selection.json"), "wb") as fh:
        fh.write(sel_bytes_override if sel_bytes_override is not None else sel_bytes)
    json.dump(scores, open(os.path.join(piv, f"recipe_search_{tag}_scores.json"), "w"))
    if not drop_artifact:
        json.dump(art, open(os.path.join(piv, f"recipe_search_{tag}.json"), "w"))
    if not_run is not None:
        json.dump(not_run, open(os.path.join(piv, f"recipe_search_{tag}_not_run.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", reader), os.path.join(root, "tools", "readers", reader))
    rc, out = run([PY, f"tools/readers/{reader}"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(piv, verdict_file)))
    ok = v["verdict"] == "RECIPE_CLEARS"
    return (0 if ok else 1), (f"verdict={v['verdict']} frozen_clears={v['frozen_reading_clears']} "
                              f"validity={v['validity_failed_clauses'][:2]} margin={v['margin_failed_clauses']}")


def _m12(**kw):
    def f(art, scores):
        art.update(kw)
    return f


@case("recipe2048", "control-clears-result-passes", "pass")
def _(root):
    return _recipe2048(root)


@case("recipe2048", "0012s-frozen-reader-VOIDs-a-runner-shaped-artifact-(the-filed-defect)", "fail")
def _(root):
    # CORRECTIONS.md 2026-09-03: 0012's reader expected second-stage records in ranked order; the runner
    # writes them in roster order. This case keeps that defect visible and is expected to fail.
    rc, out = _recipe2048(root, reader="recipe2048_verdict.py", verdict_file="recipe_search_2048_verdict.json")
    if rc != 0 and "in roster order" not in out and "verdict=VOID" not in out:
        return 0, out + " !! the 0012 reader no longer VOIDs on record order; the filed defect changed shape"
    return rc, out


@case("recipe2048", "second-stage-records-in-ranked-order-are-VOID-under-the-re-read-reader", "fail")
def _(root):
    def f(art, scores):
        for hid in ("model", "deep_tree"):
            st = art["selection"]["selection"][hid]["stages"][1]
            st["records"] = list(reversed(st["records"]))
    art, sel_bytes, scores = _good_recipe2048()
    sel = json.loads(sel_bytes)
    for hid in ("model", "deep_tree"):
        st = sel["selection"][hid]["stages"][1]; st["records"] = list(reversed(st["records"]))
    nb = _canon12(sel).encode("utf-8")
    def g(art, scores):
        art["selection"] = sel; art["selection_sha256"] = hashlib.sha256(nb).hexdigest()
        for e in art["ledger"]:
            if e["event"] == "selection_bound":
                e["selection_sha256"] = art["selection_sha256"]
    return _recipe2048(root, g, sel_bytes_override=nb)


@case("recipe2048", "a-frozen-only-pass-is-RECIPE_FAILS-with-the-field-informational", "fail")
def _(root):
    rc, out = _recipe2048(root, _m12(final_top1=0.19))          # F: +0.06 passes, S: +0.04 fails
    if rc != 0 and ("verdict=RECIPE_FAILS" not in out or "frozen_clears=True" not in out):
        return 0, out + " !! a frozen-only pass did not read RECIPE_FAILS with frozen_reading_clears True"
    return rc, out


@case("recipe2048", "the-gutenberg-excluded-expanded-margin-fails-on-its-own", "fail")
def _(root):
    return _recipe2048(root, _m12(final_top1_non_gutenberg=0.20))   # 0.20 - 0.155 = 0.045


@case("recipe2048", "a-margin-of-exactly-0.0500-passes-and-0.0499-fails", "fail")
def _(root):
    rc0, out0 = _recipe2048(root, _m12(final_top1=0.20))          # S: 0.20 - 0.15 = 0.0500
    if rc0 != 0:
        return 0, out0 + " !! a margin printed as 0.0500 did not pass"
    return _recipe2048(root, _m12(final_top1=0.1999))


@case("recipe2048", "one-parameter-changed-in-one-candidate-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["roster"] = json.loads(json.dumps(art["roster"]))
        art["roster"]["heads"][0]["candidates"][2]["params"]["max_iter"] = 301
    rc, out = _recipe2048(root, f)
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! an edited roster was read as a result"
    return rc, out


@case("recipe2048", "a-selected-id-that-is-not-the-rule's-winner-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["selected_ids"]["model"] = "M1"; art["selected_model_id"] = "M1"
    rc, out = _recipe2048(root, f)
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! a hand-picked winner was read as a result"
    return rc, out


@case("recipe2048", "a-different-evaluation-set-hash-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["eval_idx_sha256"] = "0" * 64
    return _recipe2048(root, f)


@case("recipe2048", "a-baseline-candidate-that-dropped-out-is-VOID-not-a-lower-bar", "fail")
def _(root):
    def f(art, scores):
        r = art["selection"]["selection"]["logistic"]["stages"][0]["records"][2]
        r["status"] = "infeasible_memory"; r["top1"] = None; r["evidence"] = "MemoryError"
        # the embedded selection must still hash-match the file: rewrite both
        return None
    art, sel_bytes, scores = _good_recipe2048()
    sel = json.loads(sel_bytes)
    r = sel["selection"]["logistic"]["stages"][0]["records"][2]
    r["status"] = "infeasible_memory"; r["top1"] = None; r["evidence"] = "MemoryError"
    sel["selection"]["logistic"]["stages"][0]["eligible_ranked_ids"] = [
        i for i in sel["selection"]["logistic"]["stages"][0]["eligible_ranked_ids"] if i != r["id"]]
    new_bytes = _canon12(sel).encode("utf-8")
    def g(art, scores):
        art["selection"] = sel; art["selection_sha256"] = hashlib.sha256(new_bytes).hexdigest()
        for e in art["ledger"]:
            if e["event"] == "selection_bound":
                e["selection_sha256"] = art["selection_sha256"]
        # the rule's winner is unchanged (L3 was the dropped one -> the new winner would be L7);
        # keep the banked winner so the only new defect is the drop-out
    rc, out = _recipe2048(root, g, sel_bytes_override=new_bytes)
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! a missing baseline arm was read as a result"
    return rc, out


@case("recipe2048", "an-incumbent-refit-outside-0.005-of-0011-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["incumbent_refit"]["top1"] = 0.18; art["incumbent_refit_top1"] = 0.18
    return _recipe2048(root, f)


@case("recipe2048", "a-0011-logistic-refit-outside-0.005-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["logistic_l1_refit"]["top1"] = 0.132; art["logistic_l1_refit_top1"] = 0.132
    return _recipe2048(root, f)


@case("recipe2048", "a-banked-bar-below-the-floor-recomputation-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["final"]["deep_tree"]["top1"] = 0.1214       # below the 0.1447 floor
        art["best_expanded_for_bar"] = 0.1214             # banked without the floor
        art["final_top1"] = 0.19                          # would pass S against 0.1214
    rc, out = _recipe2048(root, f)
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! an unfloored bar was read as a result"
    return rc, out


@case("recipe2048", "a-non-finite-final-score-is-VOID-not-a-pass", "fail")
def _(root):
    return _recipe2048(root, _m12(final_top1_non_gutenberg=float("nan")))


@case("recipe2048", "a-smoke-run-is-VOID", "fail")
def _(root):
    return _recipe2048(root, _m12(smoke=True))


@case("recipe2048", "a-model-fit-that-was-not-the-last-completion-is-VOID", "fail")
def _(root):
    def f(art, scores):
        L = art["ledger"]; i = next(k for k, e in enumerate(L) if e["name"] == "confirm_model" and e["event"] == "completed")
        L.append(L.pop(i - 6))                              # move an earlier completion after the model's
    return _recipe2048(root, f)


@case("recipe2048", "a-selection-file-that-differs-from-the-embedded-copy-is-VOID", "fail")
def _(root):
    art, sel_bytes, scores = _good_recipe2048()
    return _recipe2048(root, sel_bytes_override=sel_bytes + b"\n")


@case("recipe2048", "an-evaluation-row-gathered-during-selection-is-VOID", "fail")
def _(root):
    art, sel_bytes, scores = _good_recipe2048()
    sel = json.loads(sel_bytes); sel["eval_rows_gathered_in_selection"] = 1
    nb = _canon12(sel).encode("utf-8")
    def g(art, scores):
        art["selection"] = sel; art["selection_sha256"] = hashlib.sha256(nb).hexdigest()
        for e in art["ledger"]:
            if e["event"] == "selection_bound":
                e["selection_sha256"] = art["selection_sha256"]
    return _recipe2048(root, g, sel_bytes_override=nb)


@case("recipe2048", "absent-artifact-emits-no-verdict", "fail")
def _(root):
    return _recipe2048(root, drop_artifact=True)


@case("recipe2048", "a-NOT-RUN-marker-emits-no-verdict-and-names-the-rule", "fail")
def _(root):
    rc, out = _recipe2048(root, drop_artifact=True,
                          not_run={"reason": "three consecutive select launches produced no new checkpoint"})
    if rc == 2 and "NOT RUN" not in out:
        return 0, out + " !! the NOT RUN marker was not surfaced"
    return rc, out


@case("recipe2048", "an-incomplete-confirmatory-artifact-is-VOID", "fail")
def _(root):
    return _recipe2048(root, _m12(complete=False, missing_roles=["model"]))


@case("recipe2048", "a-per-example-vector-of-the-wrong-length-is-VOID", "fail")
def _(root):
    def f(art, scores):
        scores["per_example"]["model"] = [1] * 129999
    return _recipe2048(root, f)


@case("recipe2048", "a-role-scored-twice-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["ledger"].append({"name": "confirm_model", "fingerprint": "confirm_model", "event": "completed"})
    return _recipe2048(root, f)


@case("recipe2048", "a-record-fitted-at-another-thread-count-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["final"]["logistic"]["environment"]["threads"] = 4
    return _recipe2048(root, f)


@case("recipe2048", "an-artifact-stamped-with-another-preregistration-is-VOID", "fail")
def _(root):
    return _recipe2048(root, _m12(preregistration="0011-carve-2048-boundary"))


@case("recipe2048", "a-leaking-null-control-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["null_control"]["top1"] = 0.06; art["shuffled_label_accuracy"] = 0.06
    return _recipe2048(root, f)


@case("recipe2048", "a-baseline-head-substituted-with-a-non-selected-recipe-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["final"]["deep_tree"]["id"] = "T1"   # the head selected T8
    return _recipe2048(root, f)




# ---------------------------------------------------------------- recipe4096 gate (preregistration 0014)
#
# The same reader logic at the headline size, with 0003's floors and reproduction values; the control
# artifact is built the runner's way (second-stage survivors in roster order).

def _r4096(root, mutate=None, **kw):
    return _recipe2048(root, mutate, reader="recipe4096_verdict.py", verdict_file="recipe_search_4096_verdict.json",
                       cfg=_CFG4096, tag="4096", **kw)


@case("recipe4096", "control-clears-result-passes", "pass")
def _(root):
    return _r4096(root)


@case("recipe4096", "a-frozen-only-pass-is-RECIPE_FAILS", "fail")
def _(root):
    rc, out = _r4096(root, _m12(final_top1=0.23))            # F: 0.23-0.15 passes; S: 0.23-0.19 = 0.04 fails
    if rc != 0 and ("verdict=RECIPE_FAILS" not in out or "frozen_clears=True" not in out):
        return 0, out + " !! a frozen-only pass did not read RECIPE_FAILS with frozen_reading_clears True"
    return rc, out


@case("recipe4096", "a-margin-of-exactly-0.0500-passes-and-0.0499-fails", "fail")
def _(root):
    rc0, out0 = _r4096(root, _m12(final_top1=0.24))          # S: 0.24 - 0.19 = 0.0500
    if rc0 != 0:
        return 0, out0 + " !! a margin printed as 0.0500 did not pass"
    return _r4096(root, _m12(final_top1=0.2399))


@case("recipe4096", "a-different-evaluation-set-hash-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["eval_idx_sha256"] = "0" * 64
    return _r4096(root, f)


@case("recipe4096", "an-incumbent-refit-outside-0.005-of-0003-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["incumbent_refit"]["top1"] = 0.25; art["incumbent_refit_top1"] = 0.25
    return _r4096(root, f)


@case("recipe4096", "a-banked-bar-below-the-0003-floor-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["final"]["deep_tree"]["top1"] = 0.17; art["best_expanded_for_bar"] = 0.17; art["final_top1"] = 0.22
    rc, out = _r4096(root, f)
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! an unfloored bar was read as a result"
    return rc, out


@case("recipe4096", "one-parameter-changed-in-one-candidate-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["roster"] = json.loads(json.dumps(art["roster"]))
        art["roster"]["heads"][0]["candidates"][2]["params"]["max_iter"] = 301
    return _r4096(root, f)


@case("recipe4096", "a-per-example-vector-of-the-wrong-length-is-VOID", "fail")
def _(root):
    def f(art, scores):
        scores["per_example"]["model"] = [1] * 259999
    return _r4096(root, f)


@case("recipe4096", "a-model-fit-that-was-not-the-last-completion-is-VOID", "fail")
def _(root):
    def f(art, scores):
        L = art["ledger"]; i = next(k for k, e in enumerate(L) if e["name"] == "confirm_model" and e["event"] == "completed")
        L.append(L.pop(i - 6))
    return _r4096(root, f)


@case("recipe4096", "a-smoke-run-is-VOID", "fail")
def _(root):
    return _r4096(root, _m12(smoke=True))


@case("recipe4096", "absent-artifact-emits-no-verdict", "fail")
def _(root):
    return _r4096(root, drop_artifact=True)


def _stable_evidence(out: str) -> str:
    """Last line of a case's output, with the sandbox path and the hashes of throwaway chains
    built inside the sandbox replaced by placeholders. The report is a banked artifact whose
    digest the evidence page carries; without this the file changed on every run while every
    count stayed the same (board review 2026-09-03). Counts, not evidence strings, are the gate."""
    if not out.strip():
        return ""
    line = out.strip().splitlines()[-1]
    line = re.sub(r"/tmp/[^/\s]+", "<sandbox>", line)
    line = re.sub(r"\b[0-9a-f]{16,64}\b", "<hash>", line)
    return line[:200]



# ---------------------------------------------------------------- lofo4096 gate (0015)
#
# The 0015 reader reads a leave-one-family-out artifact: eight folds x three roles, two reproduction
# controls, a null control, and a mixture it re-derives from the per-example vectors. The control
# artifact below takes its shape - every key, nesting and record field - from the banked run the reader read
# (artifacts/pivot/lofo_4096.json) and its values from the reader's sealed constants, with the
# mixture, the per-family readings and the fold records all computed from the same vectors, exactly
# as the runner does; every case then breaks one thing and must be read as VOID or TRANSFER_FAILS.

def _lofo_reader():
    import importlib.util
    spec = importlib.util.spec_from_file_location("r15", os.path.join(REPO, "tools", "readers", "lofo4096_verdict.py"))
    r15 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r15)
    return r15


def _good_lofo(per_family=None, total_correct=None):
    """A complete, valid LOFO artifact set. per_family: the model's held-out accuracy per family (the
    logistic gets 0.6x, the majority 0.0385); total_correct overrides the model's correct count and is
    spread over the families so the mixture prints exactly total_correct / 260000."""
    r15 = _lofo_reader()
    shape = _banked_shape("lofo4096")
    fam = list(r15.FAMILIES); folds = r15.FOLDS; rec = r15.RECIPES
    part = _rf_sub(shape["partition"], dict(r15.PARTITION), "lofo4096 partition", sealed_may_be_subset=True)
    n_eval = part["n_eval_rows"]
    # evaluation chunk ids: family k's rows carry chunk id k (family = chunk % 8), in family blocks
    counts = {f: folds[f]["n_eval_rows"] for f in fam}
    chunk_ids = []
    for k, f in enumerate(fam):
        chunk_ids += [k] * counts[f]
    assert len(chunk_ids) == n_eval
    starts = {}; pos = 0
    for f in fam:
        starts[f] = pos; pos += counts[f]
    pf = per_family or {"gutenberg": 0.05, "base64": 0.04, "binary": 0.04, "code": 0.2, "csv": 0.25,
                        "json": 0.22, "log": 0.24, "mixed": 0.05}
    role_pf = {"model": pf, "logistic": {f: round(pf[f] * 0.6, 4) for f in fam}, "majority": {f: 0.0385 for f in fam}}
    correct_counts = {r: {f: int(round(role_pf[r][f] * counts[f])) for f in fam} for r in role_pf}
    if total_correct is not None:
        # spread the model's correct count: as even a share per family as integers allow
        base, extra = divmod(int(total_correct), len(fam))
        for i, f in enumerate(fam):
            correct_counts["model"][f] = base + (1 if i < extra else 0)

    def vec(role, f):
        v = [1] * n_eval                        # rows of other families: trained-on, arbitrary here
        c = correct_counts[role][f]
        for i in range(starts[f], starts[f] + counts[f]):
            v[i] = 1 if i - starts[f] < c else 0
        return v

    def _tmpl(name):                            # the runner's own record of the same name
        if name == "null":
            return shape["null_control"]
        if name.startswith("repro_"):
            return shape["reproduction"][name[len("repro_"):]]
        f, role = name[len("fold_"):].rsplit("_", 1)
        return shape["folds"][f][role]

    def record(name, role, n_rows, rows_sha, sorted_sha, top1, perfam, stage):
        c = rec[role]
        return _rf_sub(_tmpl(name), {"id": c["id"], "head": role, "family": c["family"], "params": c.get("params", {}),
                "scaled": False, "val": c.get("val"), "seed": 20260825, "params_sha256": _sha12(c),
                "stage": stage, "n_fit_rows": n_rows, "fit_rows_sha256": rows_sha, "fit_rows_sorted_sha256": sorted_sha,
                "environment": dict(_ENV12), "interruptions_before_this_fit": 0, "status": "fit", "seconds": 1.0,
                "top1": top1, "top1_non_gutenberg": top1, "per_family": perfam, "block_refills": [], "fit_info": {}},
                       f"record {name}", sealed_may_be_subset=True)

    per_example, fold_recs, lofo = {}, {f: {} for f in fam}, {}
    for role in ("majority", "logistic", "model"):
        mix = [0] * n_eval
        for f in fam:
            v = vec(role, f); per_example[f"fold_{f}_{role}"] = v
            for i in range(starts[f], starts[f] + counts[f]):
                mix[i] = v[i]
            perfam = {h: round(sum(v[starts[h]:starts[h] + counts[h]]) / counts[h], 4) for h in fam}
            fold_recs[f][role] = record(f"fold_{f}_{role}", role, folds[f]["n_train_rows"], folds[f]["train_idx_sha256"],
                                        folds[f]["train_sorted_sha256"], round(sum(v) / n_eval, 4), perfam, f"lofo:{f}")
        m = lambda idx: round(sum(mix[i] for i in idx) / len(idx), 4)  # noqa: E731
        allidx = range(n_eval)
        lofo[role] = {"mixture_top1": m(allidx),
                      "mixture_top1_non_gutenberg": m([i for i in allidx if chunk_ids[i] != 0]),
                      "structured_four_top1": m([i for i in allidx if fam[chunk_ids[i]] in r15.STRUCTURED]),
                      "per_family": {f: m(range(starts[f], starts[f] + counts[f])) for f in fam},
                      "mixture_vector_key": f"lofo_mixture_{role}"}
        per_example[f"lofo_mixture_{role}"] = mix
    pool_sha, n_pool = part["pool_idx_sha256"], part["n_pool_rows"]
    pool_sorted = part["pool_sorted_sha256"]
    inc = record("repro_model", "model", n_pool, pool_sha, pool_sorted, 0.2395, {f: 0.2395 for f in fam}, "reproduction")
    l1 = record("repro_logistic", "logistic", n_pool, pool_sha, pool_sorted, r15.LOGISTIC_L1_TOP1,
                {f: r15.LOGISTIC_L1_TOP1 for f in fam}, "reproduction")
    null = record("null", "model", part["null_rows"], "x", part["null_sorted_sha256"], 0.039, {f: 0.039 for f in fam}, "null")
    null["head"] = "null"
    per_example["repro_model"] = [1] * n_eval; per_example["repro_logistic"] = [0] * n_eval
    names = ["repro_model", "repro_logistic", "null"] + [f"fold_{f}_{r}" for f in fam for r in ("majority", "logistic", "model")]
    ledger = []
    for i, nm in enumerate(names):
        ledger += [{"name": nm, "fingerprint": nm, "event": "started", "utc": f"2026-09-08T20:{i:02d}:00Z"},
                   {"name": nm, "fingerprint": nm, "event": "completed", "utc": f"2026-09-08T20:{i:02d}:30Z"}]
    pfolds = {f: _rf_sub(shape["partition"]["folds"][f],
                         dict(folds[f], n_eval_chunks=1, n_train_chunks=1, train_rows_of_heldout_family=0,
                              train_chunks_shared_with_eval=0, train_rows_in_eval=0),
                         f"partition.folds.{f}", sealed_may_be_subset=True) for f in fam}
    partition = dict(part, folds=pfolds)
    mm, lm = lofo["model"]["mixture_top1"], lofo["logistic"]["mixture_top1"]
    corpus = _rf_sub(shape["corpus"], dict(r15.CORPUS), "lofo4096 corpus", sealed_may_be_subset=True)
    art = _shape_fill(shape, {"schema_version": 1, "schema": "raise-v1/lofo_4096/1", "preregistration": "0015-lofo-4096", "smoke": False,
           "stage": "run", "protocol": r15.PROTOCOL, "protocol_sha256": r15.PROTOCOL_SHA256, "recipes": rec,
           "recipes_sha256": r15.RECIPES_SHA256, "corpus": corpus, "partition": partition, "n_classes": 26,
           "class_names": [], "chance_accuracy": 0.038462, "environment": dict(_ENV12), "launch_environment": {},
           "launch_number": 1, "complete": True, "missing_roles": [],
           "reproduction": {"model": inc, "logistic": l1}, "incumbent_refit_top1": 0.2395,
           "logistic_l1_refit_top1": r15.LOGISTIC_L1_TOP1,
           "null_control": null, "shuffled_label_accuracy": 0.039, "null_rows": part["null_rows"],
           "folds": fold_recs, "lofo": lofo, "lofo_mixture_top1": mm,
           "lofo_margin_model_over_logistic": round(mm - lm, 6), "cluster_ci95_informational": {}, "ledger": ledger,
           "cost": {}, "run_started_utc": "2026-09-08T20:00:00Z", "run_finished_utc": "2026-09-08T21:00:00Z"}, "artifact")
    scores = {"schema": "raise-v1/lofo_4096_scores/1", "preregistration": "0015-lofo-4096", "smoke": False,
              "eval_idx_sha256": part["eval_idx_sha256"], "eval_chunk_ids": chunk_ids, "families": fam,
              "per_example": per_example}
    return art, scores


def _lofo(root, mutate=None, drop_artifact=False, drop_scores=False, **kw):
    art, scores = _good_lofo(**kw)
    if mutate:
        r = mutate(art, scores)
        if r is not None:
            art = r
    piv = os.path.join(root, "artifacts", "pivot"); os.makedirs(piv, exist_ok=True)
    if not drop_scores:
        json.dump(scores, open(os.path.join(piv, "lofo_4096_scores.json"), "w"))
    if not drop_artifact:
        json.dump(art, open(os.path.join(piv, "lofo_4096.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", "lofo4096_verdict.py"),
                os.path.join(root, "tools", "readers", "lofo4096_verdict.py"))
    rc, out = run([PY, "tools/readers/lofo4096_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(piv, "lofo_4096_verdict.json")))
    ok = v["verdict"] == "TRANSFERS"
    return (0 if ok else 1), (f"verdict={v['verdict']} mixture={v['lofo_mixture_top1']} "
                              f"validity={v['validity_failed_clauses'][:2]} transfer={v['transfer_failed_clauses']}")


@case("lofo4096", "control-transfers-passes", "pass")
def _(root):
    return _lofo(root)


@case("lofo4096", "a-mixture-below-chance-plus-0.05-is-TRANSFER_FAILS", "fail")
def _(root):
    rc, out = _lofo(root, per_family={"gutenberg": 0.05, "base64": 0.04, "binary": 0.04, "code": 0.12, "csv": 0.12,
                                      "json": 0.12, "log": 0.12, "mixed": 0.05})
    if rc != 0 and "verdict=TRANSFER_FAILS" not in out:
        return 0, out + " !! a mixture below the bar did not read TRANSFER_FAILS"
    return rc, out


@case("lofo4096", "a-mixture-of-exactly-0.0885-passes-and-0.0884-fails", "fail")
def _(root):
    rc0, out0 = _lofo(root, total_correct=23010)            # 23010 / 260000 = 0.0885 = chance + 0.050038
    if rc0 != 0:
        return 0, out0 + " !! a mixture printed as 0.0885 did not pass"
    return _lofo(root, total_correct=22984)                  # 0.0884: 0.049938 below the bar


@case("lofo4096", "a-different-evaluation-set-hash-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["eval_idx_sha256"] = "0" * 64
    return _lofo(root, f)


@case("lofo4096", "one-held-out-family-row-in-a-fold's-training-rows-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["folds"]["csv"]["train_rows_of_heldout_family"] = 1
    return _lofo(root, f)


@case("lofo4096", "a-fold-fitted-on-rows-other-than-the-sealed-ones-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["folds"]["log"]["model"]["fit_rows_sha256"] = "1" * 64
    return _lofo(root, f)


@case("lofo4096", "an-incumbent-refit-outside-0.005-of-0003-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["reproduction"]["model"]["top1"] = 0.25; art["incumbent_refit_top1"] = 0.25
    return _lofo(root, f)


@case("lofo4096", "a-null-control-above-chance-plus-0.02-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["null_control"]["top1"] = 0.06; art["shuffled_label_accuracy"] = 0.06
    return _lofo(root, f)


@case("lofo4096", "one-parameter-changed-in-one-recipe-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["recipes"] = json.loads(json.dumps(art["recipes"]))
        art["recipes"]["model"]["params"]["max_iter"] = 201
        art["recipes_sha256"] = _sha12(art["recipes"])
    return _lofo(root, f)


@case("lofo4096", "a-missing-fold-record-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["folds"]["json"]["logistic"] = None
    return _lofo(root, f)


@case("lofo4096", "a-per-example-vector-of-the-wrong-length-is-VOID", "fail")
def _(root):
    def f(art, scores):
        scores["per_example"]["fold_code_model"] = scores["per_example"]["fold_code_model"][:-1]
    return _lofo(root, f)


@case("lofo4096", "a-banked-mixture-that-is-not-the-recomputed-one-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["lofo"]["model"]["mixture_top1"] = round(art["lofo"]["model"]["mixture_top1"] + 0.01, 4)
        art["lofo_mixture_top1"] = art["lofo"]["model"]["mixture_top1"]
    return _lofo(root, f)


@case("lofo4096", "a-fold-scored-twice-is-VOID", "fail")
def _(root):
    def f(art, scores):
        L = art["ledger"]; e = next(x for x in L if x["name"] == "fold_csv_model" and x["event"] == "completed")
        L.append(dict(e))
    return _lofo(root, f)


@case("lofo4096", "a-smoke-run-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["smoke"] = True; scores["smoke"] = True
    return _lofo(root, f)


@case("lofo4096", "absent-artifact-emits-no-verdict", "fail")
def _(root):
    return _lofo(root, drop_artifact=True)


@case("lofo4096", "complete-false-with-a-missing-fit-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["complete"] = False; art["missing_roles"] = ["fold_mixed_model"]
    return _lofo(root, f)


@case("lofo4096", "one-record-whose-params-hash-is-off-recipe-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["folds"]["binary"]["model"]["params_sha256"] = "f" * 64      # recipes block intact
    return _lofo(root, f)


@case("lofo4096", "a-fold's-held-out-reading-that-disagrees-with-its-vector-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["folds"]["csv"]["model"]["per_family"]["csv"] = round(art["folds"]["csv"]["model"]["per_family"]["csv"] + 0.01, 4)
    return _lofo(root, f)


@case("lofo4096", "a-headline-mixture-that-is-not-the-model-role's-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["lofo_mixture_top1"] = art["lofo"]["logistic"]["mixture_top1"]
    return _lofo(root, f)


@case("lofo4096", "an-absent-scores-file-is-VOID", "fail")
def _(root):
    return _lofo(root, drop_scores=True)


@case("lofo4096", "a-different-sklearn-in-the-banked-environment-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["environment"] = dict(art["environment"], sklearn="1.8.0")
    return _lofo(root, f)


@case("lofo4096", "a-null-block-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["null_control"]["fit_rows_sorted_sha256"] = "9" * 64
    return _lofo(root, f)


@case("lofo4096", "an-L1-refit-at-exactly-the-tolerance-passes-and-just-outside-is-VOID", "fail")
def _(root):
    def hi(art, scores):
        art["reproduction"]["logistic"]["top1"] = 0.1402; art["logistic_l1_refit_top1"] = 0.1402   # anchor 0.1352 + 0.0050
    rc0, out0 = _lofo(root, hi)
    if rc0 != 0:
        return 0, out0 + " !! a refit exactly 0.005 from the anchor did not pass"
    def out(art, scores):
        art["reproduction"]["logistic"]["top1"] = 0.1403; art["logistic_l1_refit_top1"] = 0.1403
    return _lofo(root, out)


@case("lofo4096", "an-L1-refit-at-0003's-0.1392-passes-and-at-0.1292-is-VOID", "fail")
def _(root):
    def ok(art, scores):
        art["reproduction"]["logistic"]["top1"] = 0.1392; art["logistic_l1_refit_top1"] = 0.1392
    rc0, out0 = _lofo(root, ok)
    if rc0 != 0:
        return 0, out0 + " !! 0003's banked value, 0.004 from the anchor, did not pass"
    def bad(art, scores):
        art["reproduction"]["logistic"]["top1"] = 0.1292; art["logistic_l1_refit_top1"] = 0.1292
    return _lofo(root, bad)


@case("lofo4096", "a-non-integer-chunk-id-is-VOID-not-a-crash", "fail")
def _(root):
    def f(art, scores):
        scores["eval_chunk_ids"][5] = None
    rc, out = _lofo(root, f)
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! the reader crashed instead of emitting VOID"
    return rc, out


# ---------------------------------------------------------------- fdc4096 gate (0016)

def _fdc_reader():
    import importlib.util
    spec = importlib.util.spec_from_file_location("r16", os.path.join(REPO, "tools", "readers", "fdc4096_verdict.py"))
    r16 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r16)
    return r16


def _good_fdc(model_acc=None, total_correct_by_k=None):
    """A complete, valid family-diversity-curve artifact set. model_acc: function (family, k, chunks) -> the model's
    held-out accuracy for a fit with k source families at `chunks` chunks each (the logistic gets 0.8x, the majority
    0.0385); total_correct_by_k: four integers, the model's correct count at each fixed-budget k, spread over the
    families so the mixture prints exactly count / 260000."""
    r16 = _fdc_reader()
    shape = _banked_shape("fdc4096")
    fam = list(r16.FAMILIES); ks = list(r16.KS); folds = r16.FOLDS; rec = r16.RECIPES
    part = _rf_sub(shape["partition"], dict(r16.PARTITION), "fdc4096 partition", sealed_may_be_subset=True)
    C = r16.BUDGET_CHUNKS; depth_sizes = list(r16.DEPTH_CHUNKS[1:])
    n_eval = part["n_eval_rows"]
    counts = {f: folds[f]["n_eval_rows"] for f in fam}
    chunk_ids = []
    for i, f in enumerate(fam):
        chunk_ids += [i] * counts[f]            # family = chunk % 8, in family blocks
    assert len(chunk_ids) == n_eval
    starts = {}; pos = 0
    for f in fam:
        starts[f] = pos; pos += counts[f]
    if model_acc is None:
        def model_acc(f, k, chunks):  # noqa: E306
            base = 0.08 if f in r16.STRUCTURED else 0.045
            gain = 0.02 if f in r16.STRUCTURED else 0.005
            return round(base + gain * math.log2(k) + 0.004 * math.log2(chunks / 700), 4)
    role_acc = {"model": model_acc, "logistic": lambda f, k, c: round(model_acc(f, k, c) * 0.8, 4), "majority": lambda f, k, c: 0.0385,
                "logistic_l3": lambda f, k, c: round(model_acc(f, k, c) * 0.9, 4)}
    # fold specs: (name_fmt, section, key, k, chunks, stage_fmt)
    specs = []
    for k in ks:
        specs.append((f"fold_{{f}}_k{k}_{{r}}", "by_k", str(k), k, C // k, f"fdc:{{f}}:k{k}"))
    for n in depth_sizes:
        specs.append((f"depth_{{f}}_c{n}_{{r}}", "depth", str(n), 1, n, f"depth:{{f}}:c{n}"))
    specs.append(("pred_{f}_k1_{r}", "pred_k1", None, 1, C, "pred:{f}:k1"))
    correct = {}
    for name_fmt, sec, key, k, chunks, _ in specs:
        for r in role_acc:
            for f in fam:
                correct[(name_fmt.format(f=f, r=r))] = int(round(role_acc[r](f, k, chunks) * counts[f]))
    if total_correct_by_k is not None:
        for k, tc in zip(ks, total_correct_by_k):
            base, extra = divmod(int(tc), len(fam))
            for i, f in enumerate(fam):
                correct[f"fold_{f}_k{k}_model"] = base + (1 if i < extra else 0)

    def vec(name, f):
        v = ["1"] * n_eval                      # rows of other families: trained-on, arbitrary here
        c = correct[name]
        for i in range(starts[f], starts[f] + counts[f]):
            v[i] = "1" if i - starts[f] < c else "0"
        return "".join(v)

    def record(name, role, n_rows, rows_sha, sorted_sha, top1, perfam, stage, tmpl):
        c = rec[role]                            # tmpl: the runner's own record at the same place in the banked artifact
        return _rf_sub(tmpl, {"id": c["id"], "head": role, "family": c["family"], "params": c.get("params", {}),
                "scaled": bool(c.get("scaled", False)), "val": c.get("val"), "seed": 20260825, "params_sha256": _sha12(c),
                "stage": stage, "n_fit_rows": n_rows, "fit_rows_sha256": rows_sha, "fit_rows_sorted_sha256": sorted_sha,
                "environment": dict(_ENV12), "interruptions_before_this_fit": 0, "status": "fit", "seconds": 1.0,
                "top1": top1, "top1_non_gutenberg": top1, "per_family": perfam, "block_refills": [], "fit_info": {}},
                       f"record {name}", sealed_may_be_subset=True)

    mean = lambda xs: round(sum(xs) / len(xs), 4)  # noqa: E731
    r6 = lambda a, b: round(a - b, 6)  # noqa: E731
    per_example = {}
    fold_recs = {f: {"by_k": {str(k): {} for k in ks}, "depth": {str(n): {} for n in depth_sizes}, "pred_k1": {}} for f in fam}
    fdc = {}
    non_g = [i for i in range(n_eval) if chunk_ids[i] != 0]
    struct = [i for i in range(n_eval) if fam[chunk_ids[i]] in r16.STRUCTURED]

    def sealed_of(f, sec, key):
        return folds[f][sec] if key is None else folds[f][sec][key]

    def stitched(role, name_fmt, sec, key, stage_fmt, vec_key):
        mix = [0] * n_eval
        for f in fam:
            name = name_fmt.format(f=f, r=role); v = vec(name, f); per_example[name] = v
            for i in range(starts[f], starts[f] + counts[f]):
                mix[i] = 1 if v[i] == "1" else 0
            perfam = {h: mean([1 if ch == "1" else 0 for ch in v[starts[h]:starts[h] + counts[h]]]) for h in fam}
            sb = sealed_of(f, sec, key)
            rr = record(name, role, sb["n_train_rows"], sb["train_idx_sha256"], sb["train_sorted_sha256"],
                        mean([1 if ch == "1" else 0 for ch in v]), perfam, stage_fmt.format(f=f),
                        (shape["folds"][f][sec] if key is None else shape["folds"][f][sec][key])[role])
            if key is None:
                fold_recs[f][sec][role] = rr
            else:
                fold_recs[f][sec][key][role] = rr
        m = lambda idx: mean([mix[i] for i in idx])  # noqa: E731
        per_example[vec_key] = "".join("1" if x else "0" for x in mix)
        return {"mixture_top1": m(range(n_eval)), "mixture_top1_non_gutenberg": m(non_g),
                "structured_four_top1": m(struct), "per_family": {f: m(range(starts[f], starts[f] + counts[f])) for f in fam}}

    for role in ("majority", "logistic", "model", "logistic_l3"):
        by_k = {}; ys = []
        for k in ks:
            by_k[str(k)] = stitched(role, f"fold_{{f}}_k{k}_{{r}}", "by_k", str(k), f"fdc:{{f}}:k{k}", f"fdc_mixture_k{k}_{role}")
            ys.append(by_k[str(k)]["mixture_top1"])
        dby = {str(C): dict(by_k["1"])}; dys = [ys[0]]
        for n in depth_sizes:
            dby[str(n)] = stitched(role, f"depth_{{f}}_c{n}_{{r}}", "depth", str(n), f"depth:{{f}}:c{n}", f"depth_mixture_c{n}_{role}")
            dys.append(dby[str(n)]["mixture_top1"])
        pred = stitched(role, "pred_{f}_k1_{r}", "pred_k1", None, "pred:{f}:k1", f"pred_mixture_k1_{role}")
        dsizes = [C] + depth_sizes
        fdc[role] = {"by_k": by_k, "family_counts": ks, "log2_family_counts": r16.LOG2K, "mixture_top1_by_k": ys,
                     "slope_per_doubling": round(r16.ols_slope(r16.LOG2K, ys), 6), "end_difference": r6(ys[-1], ys[0]),
                     "structured_four_by_k": [by_k[str(k)]["structured_four_top1"] for k in ks],
                     "non_gutenberg_by_k": [by_k[str(k)]["mixture_top1_non_gutenberg"] for k in ks],
                     "per_family_by_k": {f: [by_k[str(k)]["per_family"][f] for k in ks] for f in fam},
                     "depth": {"by_chunks": dby, "chunks": dsizes, "mixture_top1_by_chunks": dys,
                               "per_family_by_chunks": {f: [dby[str(n)]["per_family"][f] for n in dsizes] for f in fam},
                               "row_effect_within_family": r6(dys[0], dys[-1]),
                               "row_effect_per_doubling_of_chunks": round((dys[0] - dys[-1]) / math.log2(dsizes[0] / dsizes[-1]), 6)},
                     "pred_k1": pred, "n_iter_by_k": {str(k): [None] * len(fam) for k in ks},
                     "family_effect_at_matched_depth": {str(k): r6(ys[i], dys[i]) for i, k in enumerate(ks) if i > 0},
                     "composition_spread_k1": r6(ys[0], pred["mixture_top1"])}
    inc = record("repro_100k", "model", part["repro_rows"], part["repro_idx_sha256"], part["repro_sorted_sha256"],
                 r16.RUNG_100K_TOP1, {f: r16.RUNG_100K_TOP1 for f in fam}, "reproduction", shape["reproduction"]["model_100k"])
    null = record("null", "model", part["null_rows"], "x", part["null_sorted_sha256"], 0.039, {f: 0.039 for f in fam}, "null",
                  shape["null_control"])
    null["head"] = "null"
    per_example["repro_100k"] = "1" * n_eval
    names = ["repro_100k", "null"]
    for f in fam:
        for name_fmt, _, _, _, _, _ in specs:
            names += [name_fmt.format(f=f, r=r) for r in ("majority", "logistic", "model", "logistic_l3")]
    ledger = []
    for i, nm in enumerate(names):
        ledger += [{"name": nm, "fingerprint": nm, "event": "started", "utc": f"2026-09-09T{3 + i // 60:02d}:{i % 60:02d}:00Z"},
                   {"name": nm, "fingerprint": nm, "event": "completed", "utc": f"2026-09-09T{3 + i // 60:02d}:{i % 60:02d}:30Z"}]

    def pblock(f, sb, chosen, per, tmpl):
        return _rf_sub(tmpl, dict(sb, train_rows_per_family={c: (sb["n_train_rows"] // len(chosen) if c in chosen else 0) for c in fam},
                    train_chunks_per_family={c: (per if c in chosen else 0) for c in fam},
                    train_rows_of_heldout_family=0, train_rows_outside_chosen_families=0,
                    train_chunks_shared_with_eval=0, train_rows_in_eval=0), f"partition.folds.{f} block", sealed_may_be_subset=True)

    pfolds = {}
    for f in fam:
        pf = {"n_eval_rows": folds[f]["n_eval_rows"], "eval_idx_sha256": folds[f]["eval_idx_sha256"], "n_eval_chunks": folds[f]["n_eval_chunks"],
              "by_k": {}, "depth": {}, "pred_k1": None}
        for k in ks:
            sb = folds[f]["by_k"][str(k)]; pf["by_k"][str(k)] = pblock(f, sb, sb["families"], C // k, shape["partition"]["folds"][f]["by_k"][str(k)])
        for n in depth_sizes:
            sb = folds[f]["depth"][str(n)]; pf["depth"][str(n)] = pblock(f, sb, sb["families"], n, shape["partition"]["folds"][f]["depth"][str(n)])
        sb = folds[f]["pred_k1"]; pf["pred_k1"] = pblock(f, sb, sb["families"], C, shape["partition"]["folds"][f]["pred_k1"])
        # make the row maps sum exactly to the sealed rows (integer division above may lose a remainder)
        for blk in list(pf["by_k"].values()) + list(pf["depth"].values()) + [pf["pred_k1"]]:
            rm = blk["train_rows_per_family"]; chosen = blk["families"]
            rm[chosen[0]] += blk["n_train_rows"] - sum(rm.values())
        pfolds[f] = _rf_sub(shape["partition"]["folds"][f], pf, f"partition.folds.{f}", sealed_may_be_subset=True)
    partition = dict(part, folds=pfolds)
    ms, ls = fdc["model"]["slope_per_doubling"], fdc["logistic"]["slope_per_doubling"]
    corpus = _rf_sub(shape["corpus"], dict(r16.CORPUS), "fdc4096 corpus", sealed_may_be_subset=True)
    art = _shape_fill(shape, {"schema_version": 1, "schema": "raise-v1/fdc_4096/1", "preregistration": "0016-fdc-4096", "smoke": False,
           "stage": "run", "protocol": r16.PROTOCOL, "protocol_sha256": r16.PROTOCOL_SHA256, "recipes": rec,
           "recipes_sha256": r16.RECIPES_SHA256, "corpus": corpus, "partition": partition, "n_classes": 26,
           "class_names": [], "chance_accuracy": 0.038462, "environment": dict(_ENV12), "launch_environment": {},
           "launch_number": 1, "complete": True, "missing_roles": [],
           "reproduction": {"model_100k": inc}, "incumbent_100k_refit_top1": r16.RUNG_100K_TOP1,
           "null_control": null, "shuffled_label_accuracy": 0.039, "null_rows": part["null_rows"],
           "folds": fold_recs, "fdc": fdc, "fdc_slope_per_doubling": ms,
           "fdc_mixture_top1_by_k": fdc["model"]["mixture_top1_by_k"], "fdc_end_difference": fdc["model"]["end_difference"],
           "fdc_slope_model_minus_logistic": round(ms - ls, 6), "cluster_ci95_informational": {}, "ledger": ledger,
           "cost": {}, "run_started_utc": "2026-09-09T03:00:00Z", "run_finished_utc": "2026-09-09T09:00:00Z"}, "artifact")
    scores = {"schema": "raise-v1/fdc_4096_scores/1", "preregistration": "0016-fdc-4096", "smoke": False,
              "eval_idx_sha256": part["eval_idx_sha256"], "eval_chunk_ids": chunk_ids, "families": fam,
              "per_example": per_example}
    return art, scores


def _fdc(root, mutate=None, drop_artifact=False, drop_scores=False, **kw):
    art, scores = _good_fdc(**kw)
    if mutate:
        r = mutate(art, scores)
        if r is not None:
            art = r
    piv = os.path.join(root, "artifacts", "pivot"); os.makedirs(piv, exist_ok=True)
    if not drop_scores:
        json.dump(scores, open(os.path.join(piv, "fdc_4096_scores.json"), "w"))
    if not drop_artifact:
        json.dump(art, open(os.path.join(piv, "fdc_4096.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", "fdc4096_verdict.py"),
                os.path.join(root, "tools", "readers", "fdc4096_verdict.py"))
    rc, out = run([PY, "tools/readers/fdc4096_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(piv, "fdc_4096_verdict.json")))
    ok = v["verdict"] == "DIVERSITY_HELPS"
    return (0 if ok else 1), (f"verdict={v['verdict']} slope={v['fdc_slope_per_doubling']} by_k={v['fdc_mixture_top1_by_k']} "
                              f"validity={v['validity_failed_clauses'][:2]} diversity={v['diversity_failed_clauses']}")


@case("fdc4096", "control-diversity-helps-passes", "pass")
def _(root):
    return _fdc(root)


@case("fdc4096", "a-flat-curve-is-DIVERSITY_FLAT", "fail")
def _(root):
    rc, out = _fdc(root, model_acc=lambda f, k, c: 0.12 if f in ("code", "csv", "json", "log") else 0.05)
    if rc != 0 and "verdict=DIVERSITY_FLAT" not in out:
        return 0, out + " !! a flat curve did not read DIVERSITY_FLAT"
    return rc, out


@case("fdc4096", "a-slope-of-exactly-0.005-passes-and-0.004999-fails", "fail")
def _(root):
    # counts found by search over 4-decimal mixtures at x = [0, 1, 2, log2 7]: [13000, 14359, 15718, 16601] / 260000
    # gives an OLS slope of exactly 0.005000; [13000, 14476, 15952, 16550] gives 0.004999
    rc0, out0 = _fdc(root, total_correct_by_k=[13000, 14359, 15718, 16601])
    if rc0 != 0:
        return 0, out0 + " !! a slope of exactly 0.005 should pass"
    rc1, out1 = _fdc(root, total_correct_by_k=[13000, 14476, 15952, 16550])
    if rc1 != 0 and "verdict=DIVERSITY_FLAT" not in out1:
        return 0, out1 + " !! 0.004999 did not read DIVERSITY_FLAT"
    return rc1, out0 + " | " + out1


@case("fdc4096", "a-reader-that-computed-the-slope-in-natural-log-would-be-caught-by-the-boundary-fixture", "fail")
def _(root):
    # the same exact-0.005 fixture with the runner's banked slope replaced by the ln-based value: the reader's own
    # log2 computation disagrees with the banked value beyond 1e-6 and voids
    def f(art, scores):
        ys = art["fdc"]["model"]["mixture_top1_by_k"]; r16 = _fdc_reader()
        xs = [math.log(k) for k in r16.KS]
        art["fdc"]["model"]["slope_per_doubling"] = round(r16.ols_slope(xs, ys), 6); art["fdc_slope_per_doubling"] = art["fdc"]["model"]["slope_per_doubling"]
        art["fdc_slope_model_minus_logistic"] = round(art["fdc_slope_per_doubling"] - art["fdc"]["logistic"]["slope_per_doubling"], 6)
    return _fdc(root, f, total_correct_by_k=[13000, 14359, 15718, 16601])


@case("fdc4096", "a-different-evaluation-set-hash-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["eval_idx_sha256"] = "0" * 64; scores["eval_idx_sha256"] = "0" * 64
    return _fdc(root, f)


@case("fdc4096", "one-held-out-family-row-in-a-fold's-training-rows-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["folds"]["csv"]["by_k"]["4"]["train_rows_of_heldout_family"] = 1
    return _fdc(root, f)


@case("fdc4096", "one-training-row-outside-the-chosen-families-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["folds"]["log"]["by_k"]["2"]["train_rows_outside_chosen_families"] = 1
    return _fdc(root, f)


@case("fdc4096", "a-fold-with-a-different-family-subset-is-VOID", "fail")
def _(root):
    def f(art, scores):
        fk = art["partition"]["folds"]["code"]["by_k"]["1"]; fk["families"] = ["json"]
    return _fdc(root, f)


@case("fdc4096", "a-per-family-chunk-map-that-disagrees-with-the-subset-rule-is-VOID", "fail")
def _(root):
    # the hashes and the families list are the sealed ones; only the banked per-family chunk map disagrees with the rule
    def f(art, scores):
        cm = art["partition"]["folds"]["json"]["by_k"]["4"]["train_chunks_per_family"]; cm["log"] -= 1; cm["gutenberg"] += 1
    return _fdc(root, f)


@case("fdc4096", "a-depth-fold-drawn-from-the-wrong-family-is-VOID", "fail")
def _(root):
    def f(art, scores):
        blk = art["partition"]["folds"]["binary"]["depth"]["700"]; blk["families"] = ["csv"]
        blk["train_chunks_per_family"] = {c: (700 if c == "csv" else 0) for c in blk["train_chunks_per_family"]}
    return _fdc(root, f)


@case("fdc4096", "a-predecessor-fold-drawn-from-the-successor-is-VOID", "fail")
def _(root):
    def f(art, scores):
        blk = art["partition"]["folds"]["mixed"]["pred_k1"]; blk["families"] = ["gutenberg"]
        blk["train_chunks_per_family"] = {c: (4900 if c == "gutenberg" else 0) for c in blk["train_chunks_per_family"]}
    return _fdc(root, f)


@case("fdc4096", "a-fold-fitted-on-rows-other-than-the-sealed-ones-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["folds"]["json"]["by_k"]["7"]["model"]["fit_rows_sha256"] = "f" * 64
    return _fdc(root, f)


@case("fdc4096", "a-budget-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["budget_chunks"] = 4200
    return _fdc(root, f)


@case("fdc4096", "a-family-count-list-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["family_counts"] = [1, 2, 4, 8]
        for r in art["fdc"].values():
            r["family_counts"] = [1, 2, 4, 8]
    return _fdc(root, f)


@case("fdc4096", "a-100k-reproduction-at-exactly-the-tolerance-passes-and-just-outside-is-VOID", "fail")
def _(root):
    def edge(art, scores):
        art["reproduction"]["model_100k"]["top1"] = 0.2015; art["incumbent_100k_refit_top1"] = 0.2015
    rc0, out0 = _fdc(root, edge)
    if rc0 != 0:
        return 0, out0 + " !! 0.2015 is within 0.005 of 0.1965 and should pass"

    def over(art, scores):
        art["reproduction"]["model_100k"]["top1"] = 0.2016; art["incumbent_100k_refit_top1"] = 0.2016
    rc1, out1 = _fdc(root, over)
    return rc1, out0 + " | " + out1


@case("fdc4096", "a-null-control-at-0.0584-passes-and-0.0585-is-VOID", "fail")
def _(root):
    def edge(art, scores):
        art["null_control"]["top1"] = 0.0584; art["shuffled_label_accuracy"] = 0.0584
    rc0, out0 = _fdc(root, edge)
    if rc0 != 0:
        return 0, out0 + " !! 0.0584 is within chance + 0.02 and should pass"

    def over(art, scores):
        art["null_control"]["top1"] = 0.0585; art["shuffled_label_accuracy"] = 0.0585
    rc1, out1 = _fdc(root, over)
    return rc1, out0 + " | " + out1


@case("fdc4096", "one-parameter-changed-in-one-recipe-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["recipes"]["model"]["params"]["max_leaf_nodes"] = 64
        art["recipes_sha256"] = _sha12(art["recipes"])
        for fd in art["folds"].values():
            for kd in fd["by_k"].values():
                kd["model"]["params"] = art["recipes"]["model"]["params"]; kd["model"]["params_sha256"] = _sha12(art["recipes"]["model"])
    return _fdc(root, f)


@case("fdc4096", "a-missing-fold-record-is-VOID", "fail")
def _(root):
    def f(art, scores):
        del art["folds"]["mixed"]["by_k"]["7"]["logistic"]
    return _fdc(root, f)


@case("fdc4096", "a-missing-depth-record-is-VOID", "fail")
def _(root):
    def f(art, scores):
        del art["folds"]["csv"]["depth"]["1225"]["model"]
    return _fdc(root, f)


@case("fdc4096", "a-per-example-vector-of-the-wrong-length-is-VOID", "fail")
def _(root):
    def f(art, scores):
        scores["per_example"]["fold_binary_k2_model"] = scores["per_example"]["fold_binary_k2_model"][:-1]
    return _fdc(root, f)


@case("fdc4096", "a-per-example-vector-with-a-character-that-is-not-0-or-1-is-VOID", "fail")
def _(root):
    def f(art, scores):
        v = scores["per_example"]["fold_base64_k1_model"]; scores["per_example"]["fold_base64_k1_model"] = "2" + v[1:]
    return _fdc(root, f)


@case("fdc4096", "a-banked-mixture-that-is-not-the-recomputed-one-is-VOID", "fail")
def _(root):
    def f(art, scores):
        c = art["fdc"]["model"]; k = "4"
        c["by_k"][k]["mixture_top1"] = round(c["by_k"][k]["mixture_top1"] + 0.01, 4)
        c["mixture_top1_by_k"][2] = c["by_k"][k]["mixture_top1"]
        art["fdc_mixture_top1_by_k"] = c["mixture_top1_by_k"]
    return _fdc(root, f)


@case("fdc4096", "a-banked-slope-that-is-not-the-recomputed-one-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["fdc"]["model"]["slope_per_doubling"] = 0.05; art["fdc_slope_per_doubling"] = 0.05
        art["fdc_slope_model_minus_logistic"] = round(0.05 - art["fdc"]["logistic"]["slope_per_doubling"], 6)
    return _fdc(root, f)


@case("fdc4096", "a-headline-slope-that-is-not-the-model-role's-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["fdc_slope_per_doubling"] = art["fdc"]["logistic"]["slope_per_doubling"] + 0.03
    return _fdc(root, f)


@case("fdc4096", "a-stitched-mixture-vector-that-is-not-the-stitch-is-VOID", "fail")
def _(root):
    def f(art, scores):
        v = scores["per_example"]["fdc_mixture_k7_model"]
        i = v.index("0"); scores["per_example"]["fdc_mixture_k7_model"] = v[:i] + "1" + v[i + 1:]
    return _fdc(root, f)


@case("fdc4096", "a-family-effect-reading-that-is-not-the-arithmetic-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["fdc"]["model"]["family_effect_at_matched_depth"]["7"] = 0.5
    return _fdc(root, f)


@case("fdc4096", "a-composition-spread-that-is-not-the-arithmetic-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["fdc"]["logistic"]["composition_spread_k1"] = -0.5
    return _fdc(root, f)


@case("fdc4096", "a-depth-curve-whose-budget-point-is-not-the-k1-mixture-is-VOID", "fail")
def _(root):
    def f(art, scores):
        d = art["fdc"]["model"]["depth"]; d["by_chunks"]["4900"]["mixture_top1"] = round(d["by_chunks"]["4900"]["mixture_top1"] + 0.01, 4)
        d["mixture_top1_by_chunks"][0] = d["by_chunks"]["4900"]["mixture_top1"]
    return _fdc(root, f)


@case("fdc4096", "a-fold-scored-twice-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["ledger"].append({"name": "fold_code_k4_model", "fingerprint": "fold_code_k4_model", "event": "completed",
                              "utc": "2026-09-09T10:00:00Z"})
    return _fdc(root, f)


@case("fdc4096", "a-smoke-run-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["smoke"] = True; scores["smoke"] = True
    return _fdc(root, f)


@case("fdc4096", "absent-artifact-emits-no-verdict", "fail")
def _(root):
    return _fdc(root, drop_artifact=True)


@case("fdc4096", "complete-false-with-a-missing-fit-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["complete"] = False; art["missing_roles"] = ["fold_mixed_k7_model"]; del art["folds"]["mixed"]["by_k"]["7"]["model"]
    return _fdc(root, f)


@case("fdc4096", "one-record-whose-params-hash-is-off-recipe-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["folds"]["gutenberg"]["by_k"]["1"]["model"]["params_sha256"] = "e" * 64
    return _fdc(root, f)


@case("fdc4096", "a-fold's-held-out-reading-that-disagrees-with-its-vector-is-VOID", "fail")
def _(root):
    def f(art, scores):
        r = art["folds"]["csv"]["by_k"]["2"]["model"]; r["per_family"]["csv"] = round(r["per_family"]["csv"] + 0.01, 4)
    return _fdc(root, f)


@case("fdc4096", "a-fold-record-carrying-another-fold's-stage-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["folds"]["log"]["by_k"]["4"]["logistic"]["stage"] = "fdc:log:k2"
    return _fdc(root, f)


@case("fdc4096", "an-absent-scores-file-is-VOID", "fail")
def _(root):
    return _fdc(root, drop_scores=True)


@case("fdc4096", "a-different-sklearn-in-the-banked-environment-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["environment"]["sklearn"] = "1.8.0"
    return _fdc(root, f)


@case("fdc4096", "a-null-block-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["null_control"]["fit_rows_sorted_sha256"] = "a" * 64
    return _fdc(root, f)


@case("fdc4096", "a-reproduction-fitted-on-rows-other-than-0003's-rung-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["reproduction"]["model_100k"]["fit_rows_sha256"] = "b" * 64
    return _fdc(root, f)


@case("fdc4096", "a-non-integer-chunk-id-is-VOID-not-a-crash", "fail")
def _(root):
    def f(art, scores):
        scores["eval_chunk_ids"][5] = None
    rc, out = _fdc(root, f)
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! the reader crashed instead of emitting VOID"
    return rc, out



# ---------------------------------------------------------------- lofol3 gate (0017)

def _lofol3_reader():
    import importlib.util
    spec = importlib.util.spec_from_file_location("r17", os.path.join(REPO, "tools", "readers", "lofol3_4096_verdict.py"))
    r17 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r17)
    return r17


def _good_lofol3(per_family=None, total_correct=None):
    """A complete, valid 0017 artifact set: L3 on 0015's folds. per_family: L3's held-out accuracy per family;
    total_correct overrides the correct count and is spread over the families so the mixture prints exactly
    total_correct / 260000."""
    r17 = _lofol3_reader()
    shape = _banked_shape("lofol3")
    fam = list(r17.FAMILIES); folds = r17.FOLDS; rec = r17.RECIPES
    part = _rf_sub(shape["partition"], dict(r17.PARTITION), "lofol3 partition", sealed_may_be_subset=True)
    n_eval = part["n_eval_rows"]
    counts = {f: folds[f]["n_eval_rows"] for f in fam}
    chunk_ids = []
    for k, f in enumerate(fam):
        chunk_ids += [k] * counts[f]
    assert len(chunk_ids) == n_eval
    starts = {}; pos = 0
    for f in fam:
        starts[f] = pos; pos += counts[f]
    pf = per_family or {"gutenberg": 0.09, "base64": 0.07, "binary": 0.08, "code": 0.2, "csv": 0.2,
                        "json": 0.22, "log": 0.2, "mixed": 0.1}                     # mixture well above 0.1359
    correct = {f: int(round(pf[f] * counts[f])) for f in fam}
    if total_correct is not None:
        base, extra = divmod(int(total_correct), len(fam))
        for i, f in enumerate(fam):
            correct[f] = base + (1 if i < extra else 0)

    def vec(f):
        v = [1] * n_eval
        c = correct[f]
        for i in range(starts[f], starts[f] + counts[f]):
            v[i] = 1 if i - starts[f] < c else 0
        return v

    def _tmpl(name):                            # the runner's own record of the same name
        if name == "null":
            return shape["null_control"]
        if name == "repro_l3":
            return shape["reproduction"]["logistic_l3"]
        return shape["folds"][name[len("fold_"):-len("_logistic_l3")]]["logistic_l3"]

    def record(name, n_rows, rows_sha, sorted_sha, top1, perfam, stage):
        c = rec["logistic_l3"]
        return _rf_sub(_tmpl(name), {"id": c["id"], "head": "logistic_l3", "family": c["family"], "params": c.get("params", {}),
                "scaled": True, "val": c.get("val"), "seed": 20260825, "params_sha256": _sha12(c),
                "stage": stage, "n_fit_rows": n_rows, "fit_rows_sha256": rows_sha, "fit_rows_sorted_sha256": sorted_sha,
                "environment": dict(_ENV12), "interruptions_before_this_fit": 0, "status": "fit", "seconds": 1.0,
                "top1": top1, "top1_non_gutenberg": top1, "per_family": perfam, "block_refills": [{"probe_ok": True}], "fit_info": {}},
                       f"record {name}", sealed_may_be_subset=True)

    per_example, fold_recs = {}, {}
    mix = [0] * n_eval
    for f in fam:
        v = vec(f); per_example[f"fold_{f}_logistic_l3"] = v
        for i in range(starts[f], starts[f] + counts[f]):
            mix[i] = v[i]
        perfam = {h: round(sum(v[starts[h]:starts[h] + counts[h]]) / counts[h], 4) for h in fam}
        fold_recs[f] = {"logistic_l3": record(f"fold_{f}_logistic_l3", folds[f]["n_train_rows"], folds[f]["train_idx_sha256"],
                                              folds[f]["train_sorted_sha256"], round(sum(v) / n_eval, 4), perfam, f"lofo:{f}")}
    m = lambda idx: round(sum(mix[i] for i in idx) / len(idx), 4)  # noqa: E731
    allidx = range(n_eval)
    lofo = {"logistic_l3": {"mixture_top1": m(allidx),
                            "mixture_top1_non_gutenberg": m([i for i in allidx if chunk_ids[i] != 0]),
                            "structured_four_top1": m([i for i in allidx if fam[chunk_ids[i]] in r17.STRUCTURED]),
                            "per_family": {f: m(range(starts[f], starts[f] + counts[f])) for f in fam},
                            "mixture_vector_key": "lofo_mixture_logistic_l3"}}
    per_example["lofo_mixture_logistic_l3"] = mix
    pool_sha, n_pool, pool_sorted = part["pool_idx_sha256"], part["n_pool_rows"], part["pool_sorted_sha256"]
    l3 = record("repro_l3", n_pool, pool_sha, pool_sorted, r17.L3_TOP1_0014, {f: r17.L3_TOP1_0014 for f in fam}, "reproduction")
    null = record("null", part["null_rows"], "x", part["null_sorted_sha256"], 0.039, {f: 0.039 for f in fam}, "null")
    null["head"] = "null"
    per_example["repro_l3"] = [1] * n_eval
    names = ["repro_l3", "null"] + [f"fold_{f}_logistic_l3" for f in fam]
    ledger = []
    for i, nm in enumerate(names):
        ledger += [{"name": nm, "fingerprint": nm, "event": "started", "utc": f"2026-09-09T20:{i:02d}:00Z"},
                   {"name": nm, "fingerprint": nm, "event": "completed", "utc": f"2026-09-09T20:{i:02d}:30Z"}]
    pfolds = {f: _rf_sub(shape["partition"]["folds"][f],
                         dict(folds[f], train_rows_of_heldout_family=0, train_chunks_shared_with_eval=0, train_rows_in_eval=0),
                         f"partition.folds.{f}", sealed_may_be_subset=True) for f in fam}
    partition = dict(part, folds=pfolds)
    mm = lofo["logistic_l3"]["mixture_top1"]; ref = r17.REFERENCE_0015; l3c = sum(mix)
    corpus = _rf_sub(shape["corpus"], dict(r17.CORPUS), "lofol3 corpus", sealed_may_be_subset=True)
    art = _shape_fill(shape, {"schema_version": 1, "schema": "raise-v1/lofo_l3_4096/1", "preregistration": "0017-lofo-l3-4096", "smoke": False,
           "lofo_correct_l3": l3c, "lofo_margin_l3_over_0015_model_exact": round((l3c - ref["model_correct"]) / n_eval, 6),
           "n_iter_by_fold": {f: 500 for f in fam}, "any_fold_at_iteration_cap": False,
           "stage": "run", "protocol": r17.PROTOCOL, "protocol_sha256": r17.PROTOCOL_SHA256, "recipes": rec,
           "recipes_sha256": r17.RECIPES_SHA256, "corpus": corpus, "partition": partition, "n_classes": 26,
           "class_names": [], "chance_accuracy": 0.038462, "environment": dict(_ENV12), "launch_environment": {},
           "launch_number": 1, "complete": True, "missing_roles": [],
           "reproduction": {"logistic_l3": l3}, "logistic_l3_refit_top1": r17.L3_TOP1_0014,
           "null_control": null, "shuffled_label_accuracy": 0.039, "null_rows": part["null_rows"],
           "folds": fold_recs, "lofo": lofo, "lofo_mixture_top1": mm, "reference_0015": ref,
           "lofo_margin_l3_over_0015_model": round(mm - ref["model_mixture_top1"], 6),
           "lofo_margin_l3_over_0015_logistic": round(mm - ref["logistic_mixture_top1"], 6),
           "lofo_per_family_margin_over_0015_model": {f: round(lofo["logistic_l3"]["per_family"][f] - ref["model_per_family"][f], 6) for f in fam},
           "cluster_ci95_informational": {}, "ledger": ledger, "cost": {},
           "run_started_utc": "2026-09-09T20:00:00Z", "run_finished_utc": "2026-09-09T23:00:00Z"}, "artifact")
    scores = {"schema": "raise-v1/lofo_l3_4096_scores/1", "preregistration": "0017-lofo-l3-4096", "smoke": False,
              "eval_idx_sha256": part["eval_idx_sha256"], "eval_chunk_ids": chunk_ids, "families": fam,
              "per_example": per_example}
    return art, scores


def _lofol3(root, mutate=None, drop_artifact=False, drop_scores=False, **kw):
    art, scores = _good_lofol3(**kw)
    if mutate:
        r = mutate(art, scores)
        if r is not None:
            art = r
    piv = os.path.join(root, "artifacts", "pivot"); os.makedirs(piv, exist_ok=True)
    if not drop_scores:
        json.dump(scores, open(os.path.join(piv, "lofo_l3_4096_scores.json"), "w"))
    if not drop_artifact:
        json.dump(art, open(os.path.join(piv, "lofo_l3_4096.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", "lofol3_4096_verdict.py"),
                os.path.join(root, "tools", "readers", "lofol3_4096_verdict.py"))
    rc, out = run([PY, "tools/readers/lofol3_4096_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(piv, "lofo_l3_4096_verdict.json")))
    ok = v["verdict"] == "L3_LEADS_INCUMBENT_UNDER_TRANSFER"
    return (0 if ok else 1), (f"verdict={v['verdict']} mixture={v['lofo_mixture_top1_l3']} margin={v['lofo_margin_l3_over_0015_model_exact']} "
                              f"validity={v['validity_failed_clauses'][:2]} lead={v['lead_failed_clauses']}")


@case("lofol3", "control-l3-lead-passes", "pass")
def _(root):
    return _lofol3(root)


@case("lofol3", "a-lead-below-the-margin-is-L3_LEAD_BELOW_BAR", "fail")
def _(root):
    rc, out = _lofol3(root, per_family={"gutenberg": 0.06, "base64": 0.06, "binary": 0.07, "code": 0.1, "csv": 0.1,
                                        "json": 0.1, "log": 0.1, "mixed": 0.08})
    if rc != 0 and "verdict=L3_LEAD_BELOW_BAR" not in out:
        return 0, out + " !! a lead below the margin did not read L3_LEAD_BELOW_BAR"
    return rc, out


@case("lofol3", "a-lead-of-exactly-the-margin-in-rows-passes-and-one-row-fewer-fails", "fail")
def _(root):
    r17 = _lofol3_reader(); edge = r17.REFERENCE_0015["model_correct"] + r17.MARGIN_CORRECT
    rc0, out0 = _lofol3(root, total_correct=edge)
    if rc0 != 0:
        return 0, out0 + f" !! {edge} correct rows is exactly the incumbent's count plus the margin and should pass"
    rc1, out1 = _lofol3(root, total_correct=edge - 1)
    if rc1 != 0 and "verdict=L3_LEAD_BELOW_BAR" not in out1:
        return 0, out1 + " !! one row fewer did not read L3_LEAD_BELOW_BAR"
    return rc1, out0 + " | " + out1


@case("lofol3", "a-banked-correct-count-off-by-one-row-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["lofo_correct_l3"] += 1
    return _lofol3(root, f)


@case("lofol3", "a-missing-iteration-count-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["n_iter_by_fold"]["csv"] = None
    return _lofol3(root, f)


@case("lofol3", "a-different-evaluation-set-hash-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["eval_idx_sha256"] = "0" * 64; scores["eval_idx_sha256"] = "0" * 64
    return _lofol3(root, f)


@case("lofol3", "one-held-out-family-row-in-a-fold's-training-rows-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["folds"]["csv"]["train_rows_of_heldout_family"] = 1
    return _lofol3(root, f)


@case("lofol3", "a-fold-fitted-on-rows-other-than-0015's-sealed-ones-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["folds"]["json"]["logistic_l3"]["fit_rows_sha256"] = "f" * 64
    return _lofol3(root, f)


@case("lofol3", "an-L3-reproduction-at-exactly-the-tolerance-passes-and-just-outside-is-VOID", "fail")
def _(root):
    def edge(art, scores):
        art["reproduction"]["logistic_l3"]["top1"] = 0.2367; art["logistic_l3_refit_top1"] = 0.2367
    rc0, out0 = _lofol3(root, edge)
    if rc0 != 0:
        return 0, out0 + " !! 0.2367 is within 0.005 of 0.2317 and should pass"

    def over(art, scores):
        art["reproduction"]["logistic_l3"]["top1"] = 0.2368; art["logistic_l3_refit_top1"] = 0.2368
    rc1, out1 = _lofol3(root, over)
    return rc1, out0 + " | " + out1


@case("lofol3", "a-null-control-above-chance-plus-0.02-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["null_control"]["top1"] = 0.06; art["shuffled_label_accuracy"] = 0.06
    return _lofol3(root, f)


@case("lofol3", "one-parameter-changed-in-the-recipe-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["recipes"]["logistic_l3"]["params"]["C"] = 0.5
        art["recipes_sha256"] = _sha12(art["recipes"])
        for fd in art["folds"].values():
            fd["logistic_l3"]["params"] = art["recipes"]["logistic_l3"]["params"]; fd["logistic_l3"]["params_sha256"] = _sha12(art["recipes"]["logistic_l3"])
    return _lofol3(root, f)


@case("lofol3", "an-unstandardised-fit-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["folds"]["log"]["logistic_l3"]["scaled"] = False
    return _lofol3(root, f)


@case("lofol3", "a-missing-fold-record-is-VOID", "fail")
def _(root):
    def f(art, scores):
        del art["folds"]["mixed"]["logistic_l3"]
    return _lofol3(root, f)


@case("lofol3", "a-per-example-vector-of-the-wrong-length-is-VOID", "fail")
def _(root):
    def f(art, scores):
        scores["per_example"]["fold_binary_logistic_l3"] = scores["per_example"]["fold_binary_logistic_l3"][:-1]
    return _lofol3(root, f)


@case("lofol3", "a-banked-mixture-that-is-not-the-recomputed-one-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["lofo"]["logistic_l3"]["mixture_top1"] = round(art["lofo"]["logistic_l3"]["mixture_top1"] + 0.01, 4)
        art["lofo_mixture_top1"] = art["lofo"]["logistic_l3"]["mixture_top1"]
        art["lofo_margin_l3_over_0015_model"] = round(art["lofo_mixture_top1"] - art["reference_0015"]["model_mixture_top1"], 6)
        art["lofo_margin_l3_over_0015_logistic"] = round(art["lofo_mixture_top1"] - art["reference_0015"]["logistic_mixture_top1"], 6)
    return _lofol3(root, f)


@case("lofol3", "a-banked-margin-that-is-not-the-arithmetic-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["lofo_margin_l3_over_0015_model"] = 0.5
    return _lofol3(root, f)


@case("lofol3", "a-0015-reference-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["reference_0015"]["model_mixture_top1"] = 0.05
        art["lofo_margin_l3_over_0015_model"] = round(art["lofo_mixture_top1"] - 0.05, 6)
    return _lofol3(root, f)


@case("lofol3", "a-fold-scored-twice-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["ledger"].append({"name": "fold_code_logistic_l3", "fingerprint": "fold_code_logistic_l3", "event": "completed",
                              "utc": "2026-09-09T23:30:00Z"})
    return _lofol3(root, f)


@case("lofol3", "a-smoke-run-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["smoke"] = True; scores["smoke"] = True
    return _lofol3(root, f)


@case("lofol3", "absent-artifact-emits-no-verdict", "fail")
def _(root):
    return _lofol3(root, drop_artifact=True)


@case("lofol3", "complete-false-with-a-missing-fit-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["complete"] = False; art["missing_roles"] = ["fold_mixed_logistic_l3"]; del art["folds"]["mixed"]["logistic_l3"]
    return _lofol3(root, f)


@case("lofol3", "one-record-whose-params-hash-is-off-recipe-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["folds"]["gutenberg"]["logistic_l3"]["params_sha256"] = "e" * 64
    return _lofol3(root, f)


@case("lofol3", "a-fold's-held-out-reading-that-disagrees-with-its-vector-is-VOID", "fail")
def _(root):
    def f(art, scores):
        r = art["folds"]["csv"]["logistic_l3"]; r["per_family"]["csv"] = round(r["per_family"]["csv"] + 0.01, 4)
    return _lofol3(root, f)


@case("lofol3", "a-stitched-mixture-vector-that-is-not-the-stitch-is-VOID", "fail")
def _(root):
    def f(art, scores):
        v = scores["per_example"]["lofo_mixture_logistic_l3"]; i = v.index(0); v[i] = 1
    return _lofol3(root, f)


@case("lofol3", "an-absent-scores-file-is-VOID", "fail")
def _(root):
    return _lofol3(root, drop_scores=True)


@case("lofol3", "a-different-sklearn-in-the-banked-environment-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["environment"]["sklearn"] = "1.8.0"
    return _lofol3(root, f)


@case("lofol3", "a-null-block-that-is-not-0015's-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["null_control"]["fit_rows_sorted_sha256"] = "a" * 64
    return _lofol3(root, f)


@case("lofol3", "a-failed-block-probe-after-standardising-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["folds"]["base64"]["logistic_l3"]["block_refills"] = [{"probe_ok": False}]
    return _lofol3(root, f)


@case("lofol3", "a-non-integer-chunk-id-is-VOID-not-a-crash", "fail")
def _(root):
    def f(art, scores):
        scores["eval_chunk_ids"][5] = None
    rc, out = _lofol3(root, f)
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! the reader crashed instead of emitting VOID"
    return rc, out



# ---------------------------------------------------------------- oob4096 gate (0018)

def _oob_reader(reader="oob4096_verdict.py"):
    """0018's frozen reader, or (reader="oob4096_reread_verdict.py") 0019's re-read reader: the same module shape, one literal apart."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(reader.replace(".py", ""), os.path.join(REPO, "tools", "readers", reader))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


_OOB_READERS = {"0018": ("oob4096_verdict.py", "oob_4096_verdict.json"),
                "0019": ("oob4096_reread_verdict.py", "oob_4096_reread_verdict.json")}
_OOB_RUNNER_NULL = "822b61020d276a04620440eb2d2e7e60376e1efba83e89607c33c09c39fa1425"   # sorted first 20000 pool rows (0014, 0016, run_oob.py)
_OOB_0018_NULL = "0653cc12293ae078dd68b900c8778d93e701261ca93414be9eb7bb8e7ee686db"     # 0015/0017's fold block, sealed by 0018 in error


def _reread_0019_expected_text(text=None, subs=None):
    """0018's frozen reader with exactly the substitutions declared (and sealed) in prereg/0019: what the re-read reader must be.
    text and subs are injectable so the builder's own refusals can be exercised; the defaults read the repository files."""
    if subs is None:
        pr = json.load(open(os.path.join(REPO, "prereg", "0019-oob-4096-reread.json")))
        subs = pr["scope"]["what_changes_from_0018"]["declared_substitutions"]
    if text is None:
        text = open(os.path.join(REPO, "tools", "readers", "oob4096_verdict.py"), encoding="utf-8").read()
    for sub in subs:
        if text.count(sub["old"]) != sub["occurrences"]:
            return None, f"substitution {sub['old'][:40]!r}: {text.count(sub['old'])} occurrences, declared {sub['occurrences']}"
        text = text.replace(sub["old"], sub["new"])
    return text, None


def _oob_readings(r18, v, fam_x, fam_e):
    n_eval, n_ext = r18.PARTITION["n_eval_rows"], r18.N_EXT
    rep, ex = v[:n_eval], v[n_eval:]
    by = {f: [] for f in r18.EXT_FAMILIES}
    for i in range(n_ext):
        by[fam_x[i]].append(ex[i])
    m4 = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
    real = [x for f in r18.REAL_FAMILIES for x in by[f]]; synth = [x for f in r18.SYNTH_FAMILIES for x in by[f]]
    return {"reproduction_top1": m4(rep), "reproduction_correct": sum(rep), "ext_top1": m4(ex), "ext_correct": sum(ex),
            "n_ext_rows": n_ext, "ext_per_family": {f: m4(by[f]) for f in r18.EXT_FAMILIES},
            "ext_per_family_correct": {f: sum(by[f]) for f in r18.EXT_FAMILIES},
            "ext_structured_text_top1": m4([x for f in r18.STRUCTURED_TEXT for x in by[f]]),
            "ext_high_entropy_top1": m4([x for f in r18.HIGH_ENTROPY for x in by[f]]),
            "ext_real_top1": m4(real), "ext_real_correct": sum(real), "n_ext_real_rows": len(real),
            "ext_synthetic_correct": sum(synth), "ext_synthetic_top1": m4(synth),
            "reproduction_per_family": {f: m4([rep[i] for i in range(n_eval) if fam_e[i] == f]) for f in r18.FAMILIES}}


def _good_oob(ext_acc=None, model_real_correct=None, model_synth_acc=None, repro=None, reader="oob4096_verdict.py"):
    """A complete, valid 0018 artifact set whose extension arrays reproduce the sealed fam and g arrays exactly (the fam
    array is family-major, g is the expansion of the sealed chunk ids by their row counts). ext_acc: extension accuracy per
    role (spread evenly over families); model_real_correct overrides M4's correct count over the real-family rows exactly;
    model_synth_acc overrides M4's accuracy on the synthetic families; repro overrides a role's reproduction accuracy.
    reader names the module whose sealed VALUES (partition hashes, fingerprints) the control carries: 0018's the fold-block null
    hash it sealed in error, 0019's the pool block the runner fits (CORRECTIONS.md 2026-09-10). The SHAPE - every key, nesting
    and record field - is the banked run's (artifacts/pivot/oob_4096.json; OPERATING_RULES section 4, CORRECTIONS.md 2026-09-17),
    so under 0018's reader the control is the runner's artifact with one value put back to the literal that reader disagrees
    with the world on; the case `0018s-frozen-reader-VOIDs-the-runners-null-block` is where that disagreement is shown."""
    r18 = _oob_reader(reader)
    shape = _banked_shape("oob4096")
    part = _rf_sub(shape["partition"], dict(r18.PARTITION), "oob4096 partition", sealed_may_be_subset=True)
    n_eval = part["n_eval_rows"]; n_ext = r18.N_EXT; rec = r18.RECIPES; roles = list(r18.ROLES)
    fams = list(r18.EXT_FAMILIES); rpf = r18.EXT["rows_per_family"]
    fam_idx = []
    for k, f in enumerate(fams):
        fam_idx += [k] * rpf[f]
    assert len(fam_idx) == n_ext
    fam_x = [fams[i] for i in fam_idx]
    ext_ids = [c for c, n in zip(r18.EXT_CHUNK_IDS, r18.EXT_ROWS_PER_CHUNK) for _ in range(n)]
    assert len(ext_ids) == n_ext
    # a sealed-looking evaluation set: 10000 distinct builder chunk ids, 26 rows each, 1269 of them gutenberg (id % 8 == 0)
    n_gut = (n_eval - part["n_eval_non_gutenberg"]) // 26; n_chunks = part["n_eval_chunks"]
    gut_ids = [8 * i for i in range(n_gut)]; other = [c for c in range(1, 49999) if c % 8 != 0][: n_chunks - n_gut]
    eval_ids = [c for c in gut_ids + other for _ in range(26)]
    fam_e = [r18.FAMILIES[c % 8] for c in eval_ids]
    acc = dict({"incumbent": 0.09, "logistic_l3": 0.10, "model": 0.12, "null": 0.038}, **(ext_acc or {}))
    reps = dict(r18.REFERENCE_TOP1, null=0.038); reps.update(repro or {})
    real = set(r18.REAL_FAMILIES)

    def vec(name):
        v = [0] * (n_eval + n_ext)
        k = int(round(reps[name] * n_eval))
        for i in range(k):
            v[i] = 1
        per = {f: int(round(acc[name] * rpf[f])) for f in fams}
        if name == "model" and model_real_correct is not None:
            rf = [f for f in fams if f in real]; base, extra = divmod(int(model_real_correct), len(rf))
            for j, f in enumerate(rf):
                per[f] = base + (1 if j < extra else 0)
        if name == "model" and model_synth_acc is not None:
            for f in fams:
                if f not in real:
                    per[f] = int(round(model_synth_acc * rpf[f]))
        pos = n_eval
        for f in fams:
            for i in range(pos, pos + per[f]):
                v[i] = 1
            pos += rpf[f]
        return v

    def fp(name):
        role = "null" if name == "null" else name
        return r18.fingerprint(prereg=r18.PREREG, seed=20260825, role=role, cand=rec["model"] if name == "null" else rec[name],
                               stage="null" if name == "null" else "pool",
                               rows=part["null_sorted_sha256"] if name == "null" else part["pool_idx_sha256"],
                               eval=part["eval_idx_sha256"], ext=r18.EXT["arrays"]["X"]["sha256"])

    def record(name, role, head, n_rows, rows_sha, sorted_sha, stage, v):
        c = rec[role]; m4 = lambda xs: round(sum(xs) / len(xs), 4)  # noqa: E731
        ng = [v[i] for i in range(n_eval) if fam_e[i] != "gutenberg"] + v[n_eval:]
        return _rf_sub(shape["fits"][name], {"id": c["id"], "head": head, "family": c["family"], "params": c.get("params", {}), "scaled": bool(c.get("scaled", False)),
                "val": c.get("val"), "seed": 20260825, "params_sha256": _sha12(c), "stage": stage, "n_fit_rows": n_rows,
                "fit_rows_sha256": rows_sha, "fit_rows_sorted_sha256": sorted_sha, "environment": dict(_ENV12),
                "interruptions_before_this_fit": 0, "status": "fit", "seconds": 1.0, "top1": m4(v), "top1_non_gutenberg": m4(ng),
                "per_family": {f: m4([v[i] for i in range(n_eval) if fam_e[i] == f]) for f in r18.FAMILIES},
                "block_refills": [{"probe_ok": True}], "fit_info": {"n_iter": 100}, "fingerprint": fp(name),
                "per_example_sha256": hashlib.sha256(bytes(v)).hexdigest()}, f"fits.{name}", sealed_may_be_subset=True)

    per_example, reads, fits = {}, {}, {}
    for name in ["null"] + roles:
        v = vec(name); per_example[name] = v; reads[name] = _oob_readings(r18, v, fam_x, fam_e)
    for r in roles:
        fits[r] = record(r, r, r, part["n_pool_rows"], part["pool_idx_sha256"], part["pool_sorted_sha256"], "pool", per_example[r])
    fits["null"] = record("null", "model", "null", part["null_rows"], "x", part["null_sorted_sha256"], "null", per_example["null"])
    ledger = []
    for i, nm in enumerate(["null"] + roles):
        ledger += [{"name": nm, "fingerprint": fp(nm), "event": "started", "utc": f"2026-09-10T00:{i:02d}:00Z"},
                   {"name": nm, "fingerprint": fp(nm), "event": "completed", "utc": f"2026-09-10T00:{i:02d}:30Z"}]
    mc, lc, ic = (reads[r]["ext_correct"] for r in ("model", "logistic_l3", "incumbent"))
    part.update({"pool_chunks_shared_with_ext": 0, "eval_chunks_shared_with_ext": 0, "pool_rows_identical_to_an_ext_row": 0,
                 "eval_rows_identical_to_an_ext_row": 0, "null_y_shuffled_sha256": "0" * 64, "null_labels_permuted": True,
                 "null_labels_same_multiset": True})
    n_real = reads["model"]["n_ext_real_rows"]
    art = _shape_fill(shape, {"schema_version": 1, "schema": "raise-v1/oob_4096/1", "preregistration": "0018-oob-4096", "smoke": False, "stage": "run",
           "protocol": r18.PROTOCOL, "protocol_sha256": r18.PROTOCOL_SHA256, "recipes": rec, "recipes_sha256": r18.RECIPES_SHA256,
           "corpus": _rf_sub(shape["corpus"], dict(r18.CORPUS), "oob4096 corpus", sealed_may_be_subset=True),
           "ext_corpus": _rf_sub(shape["ext_corpus"], dict(r18.EXT), "oob4096 ext_corpus"), "partition": part, "n_classes": 26, "class_names": [],
           "chance_accuracy": 0.038462, "environment": dict(_ENV12),
           "launch_environment": {"ok": True, "problems": [], "env": dict(_ENV12), "loadavg_1_5_15": [0.1, 0.1, 0.1]},
           "launch_number": 1, "complete": True, "missing_roles": [], "fits": fits, "readings": reads,
           "reproduction_top1": {r: reads[r]["reproduction_top1"] for r in roles},
           "reproduction_drift": {r: round(reads[r]["reproduction_top1"] - r18.REFERENCE_TOP1[r], 6) for r in roles},
           "reference_top1": dict(r18.REFERENCE_TOP1),
           "ext_top1": {r: reads[r]["ext_top1"] for r in roles}, "ext_correct": {r: reads[r]["ext_correct"] for r in roles},
           "ext_real_top1": {r: reads[r]["ext_real_top1"] for r in roles},
           "ext_real_correct": {r: reads[r]["ext_real_correct"] for r in roles},
           "ext_top1_model": reads["model"]["ext_top1"], "ext_correct_model": mc, "ext_real_correct_model": reads["model"]["ext_real_correct"],
           "n_ext_real_rows": n_real, "ext_real_families": list(r18.REAL_FAMILIES), "ext_synthetic_families": list(r18.SYNTH_FAMILIES),
           "ext_label_histogram": list(r18.EXT_LABEL_HISTOGRAM), "ext_majority_class_rate": round(max(r18.EXT_LABEL_HISTOGRAM) / n_ext, 6),
           "ext_margin_model_over_logistic_l3_exact": round((mc - lc) / n_ext, 6),
           "ext_margin_model_over_incumbent_exact": round((mc - ic) / n_ext, 6),
           "ext_per_family": {r: reads[r]["ext_per_family"] for r in roles},
           "null_control": fits["null"], "shuffled_label_accuracy_ext": reads["null"]["ext_top1"],
           "shuffled_label_accuracy_eval": reads["null"]["reproduction_top1"], "null_rows": part["null_rows"],
           "n_ext_rows": n_ext, "n_eval_rows": n_eval, "fit_info_by_role": {r: fits[r]["fit_info"] for r in roles},
           "cluster_ci95_informational": {}, "ledger": ledger, "cost": {},
           "run_started_utc": "2026-09-10T00:00:00Z", "first_launch_utc": "2026-09-10T00:00:00Z", "run_finished_utc": "2026-09-10T06:00:00Z"}, "artifact")
    scores = {"schema": "raise-v1/oob_4096_scores/1", "preregistration": "0018-oob-4096", "smoke": False,
              "n_eval_rows": n_eval, "n_ext_rows": n_ext, "eval_idx_sha256": part["eval_idx_sha256"],
              "eval_chunk_ids": eval_ids, "ext_chunk_ids": ext_ids, "ext_fam": fam_idx, "ext_families": fams,
              "ext_arrays_sha256": {k: v["sha256"] for k, v in r18.EXT["arrays"].items()}, "per_example": per_example}
    return art, scores


def _oob(root, mutate=None, drop_artifact=False, drop_scores=False, prereg="0018", build_from=None, **kw):
    """Run preregistration `prereg`'s reader (0018's frozen reader by default; "0019" for the re-read reader) on an artifact
    built from `build_from`'s literals (the same preregistration unless given)."""
    reader, verdict_file = _OOB_READERS[prereg]
    art, scores = _good_oob(reader=_OOB_READERS[build_from or prereg][0], **kw)
    if mutate:
        r = mutate(art, scores)
        if r is not None:
            art = r
    piv = os.path.join(root, "artifacts", "pivot"); os.makedirs(piv, exist_ok=True)
    if not drop_scores:
        json.dump(scores, open(os.path.join(piv, "oob_4096_scores.json"), "w"))
    if not drop_artifact:
        json.dump(art, open(os.path.join(piv, "oob_4096.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", reader), os.path.join(root, "tools", "readers", reader))
    rc, out = run([PY, f"tools/readers/{reader}"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(piv, verdict_file)))
    ok = v["verdict"] == "OOB_TRANSFERS"
    return (0 if ok else 1), (f"verdict={v['verdict']} real={v.get('ext_real_top1_model')} correct={v.get('ext_real_correct_model')} "
                              f"validity={v['validity_failed_clauses'][:2]} transfer={v['transfer_failed_clauses']}")


def _oob_void(root, mutate, expect_clause=None, **kw):
    """A mutation that must read VOID (or, for a missing artifact, emit no verdict); the harness counts rc != 0 as detected."""
    rc, out = _oob(root, mutate, **kw)
    if rc != 0 and "verdict=VOID" not in out and "No verdict emitted" not in out and "VOID:" not in out:
        return 0, out + " !! detected but not as VOID"
    if expect_clause and expect_clause not in out:
        return 0, out + f" !! VOID for another reason than {expect_clause!r}"
    return rc, out


@case("oob4096", "control-model-clears-the-bar-on-the-real-families", "pass")
def _(root):
    return _oob(root)


@case("oob4096", "model-below-the-bar-on-the-real-families-is-OOB_TRANSFER_FAILS", "fail")
def _(root):
    rc, out = _oob(root, ext_acc={"model": 0.07})
    if rc != 0 and "verdict=OOB_TRANSFER_FAILS" not in out:
        return 0, out + " !! a reading below the bar did not read OOB_TRANSFER_FAILS"
    return rc, out


@case("oob4096", "a-pass-carried-by-the-synthetic-families-alone-is-OOB_TRANSFER_FAILS", "fail")
def _(root):
    r18 = _oob_reader()
    rc, out = _oob(root, model_real_correct=int(0.039 * r18.N_REAL), model_synth_acc=0.30)
    if rc != 0 and "verdict=OOB_TRANSFER_FAILS" not in out:
        return 0, out + " !! synthetic families alone carried the verdict"
    return rc, out


@case("oob4096", "exactly-min-correct-real-rows-passes-and-one-row-fewer-fails", "fail")
def _(root):
    r18 = _oob_reader()
    rc0, out0 = _oob(root, model_real_correct=r18.MIN_CORRECT_REAL)
    if rc0 != 0:
        return 0, out0 + f" !! {r18.MIN_CORRECT_REAL} correct real rows is exactly the bar and should pass"
    rc1, out1 = _oob(root, model_real_correct=r18.MIN_CORRECT_REAL - 1)
    if rc1 != 0 and "verdict=OOB_TRANSFER_FAILS" not in out1:
        return 0, out1 + " !! one row fewer did not read OOB_TRANSFER_FAILS"
    return rc1, out0 + " | " + out1


@case("oob4096", "a-banked-real-correct-count-off-by-one-row-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["ext_real_correct_model"] += 1
    return _oob_void(root, f, "ext_real_correct_model")


@case("oob4096", "a-banked-mixture-count-off-by-one-row-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["ext_correct_model"] += 1
    return _oob_void(root, f)


@case("oob4096", "a-banked-per-family-reading-off-by-0.0001-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["ext_per_family"]["model"]["c_src"] = round(a["ext_per_family"]["model"]["c_src"] + 0.0001, 4)
    return _oob_void(root, f)


@case("oob4096", "a-reproduction-drift-of-plus-or-minus-0.005-passes-and-0.0051-is-VOID", "fail")
def _(root):
    r18 = _oob_reader(); ref = r18.REFERENCE_TOP1["model"]
    for sign in (1, -1):
        rc0, out0 = _oob(root, repro={"model": round(ref + sign * 0.005, 4)})
        if rc0 != 0:
            return 0, out0 + " !! a drift of exactly 0.005 should pass"
    rc1, out1 = _oob(root, repro={"model": round(ref + 0.0051, 4)})
    if rc1 != 0 and "verdict=VOID" not in out1:
        return 0, out1 + " !! a drift of 0.0051 did not VOID"
    rc2, out2 = _oob(root, repro={"model": round(ref - 0.0051, 4)})
    if rc2 != 0 and "verdict=VOID" not in out2:
        return 0, out2 + " !! a drift of -0.0051 did not VOID"
    return (rc1 or rc2), out1 + " | " + out2


@case("oob4096", "the-incumbent-reproduction-off-by-0.006-is-VOID", "fail")
def _(root):
    r18 = _oob_reader()
    return _oob_void(root, None, "reproduction", repro={"incumbent": round(r18.REFERENCE_TOP1["incumbent"] + 0.006, 4)})


@case("oob4096", "null-control-above-chance-plus-0.01-on-the-extension-rows-is-VOID", "fail")
def _(root):
    return _oob_void(root, None, "null control", ext_acc={"null": 0.06})


@case("oob4096", "null-control-above-chance-plus-0.01-on-the-sealed-rows-is-VOID", "fail")
def _(root):
    return _oob_void(root, None, "null control", repro={"null": 0.06})


@case("oob4096", "null-control-at-0.0484-passes-and-0.0485-is-VOID", "fail")
def _(root):
    rc0, out0 = _oob(root, ext_acc={"null": 0.0484})
    if rc0 != 0:
        return 0, out0 + " !! a null of 0.0484 (chance + 0.0099) should pass"
    return _oob_void(root, None, "null control", ext_acc={"null": 0.0485})


@case("oob4096", "a-smoke-artifact-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["smoke"] = True; s["smoke"] = True
    return _oob_void(root, f, "smoke")


@case("oob4096", "a-stage-other-than-run-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["stage"] = "selection"
    return _oob_void(root, f, "stage")


@case("oob4096", "a-corpus-literal-changed-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["corpus"]["cache_y_sha256"] = "0" * 64
    return _oob_void(root, f, "corpus")


@case("oob4096", "extension-array-hash-changed-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["ext_corpus"]["arrays"] = dict(a["ext_corpus"]["arrays"], X={"sha256": "<hash>", "shape": [61409, 1108], "dtype": "float32"})
    return _oob_void(root, f, "extension corpus")


@case("oob4096", "extension-rows-per-family-changed-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["ext_corpus"]["rows_per_family"] = dict(a["ext_corpus"]["rows_per_family"], c_src=7799)
    return _oob_void(root, f, "extension corpus")


@case("oob4096", "extension-label-histogram-changed-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["ext_label_histogram"][0] += 1
    return _oob_void(root, f, "label histogram")


@case("oob4096", "scores-file-naming-a-different-extension-corpus-is-VOID", "fail")
def _(root):
    def f(a, s):
        s["ext_arrays_sha256"]["X"] = "0" * 64
    return _oob_void(root, f, "scores")


@case("oob4096", "one-extension-row-moved-to-another-family-is-VOID", "fail")
def _(root):
    def f(a, s):
        s["ext_fam"][0] = 1
    return _oob_void(root, f, "scores")


@case("oob4096", "two-extension-rows-swapped-across-families-is-VOID", "fail")
def _(root):
    def f(a, s):
        i, j = 0, len(s["ext_fam"]) - 1
        s["ext_fam"][i], s["ext_fam"][j] = s["ext_fam"][j], s["ext_fam"][i]
    return _oob_void(root, f, "ext_fam")


@case("oob4096", "an-extension-family-index-out-of-range-is-VOID", "fail")
def _(root):
    def f(a, s):
        s["ext_fam"][5] = 8
    return _oob_void(root, f, "ext_fam")


@case("oob4096", "extension-chunk-ids-shifted-by-one-is-VOID", "fail")
def _(root):
    def f(a, s):
        s["ext_chunk_ids"] = [c + 1 for c in s["ext_chunk_ids"]]
    return _oob_void(root, f, "ext_chunk_ids")


@case("oob4096", "extension-chunk-ids-inside-the-builder-id-space-is-VOID", "fail")
def _(root):
    def f(a, s):
        s["ext_chunk_ids"] = [c - 10000000 for c in s["ext_chunk_ids"]]
    return _oob_void(root, f, "ext_chunk_ids")


@case("oob4096", "extension-chunk-ids-reordered-is-VOID", "fail")
def _(root):
    def f(a, s):
        s["ext_chunk_ids"] = s["ext_chunk_ids"][::-1]
    return _oob_void(root, f, "ext_chunk_ids")


@case("oob4096", "evaluation-chunk-ids-with-the-wrong-gutenberg-share-is-VOID", "fail")
def _(root):
    def f(a, s):
        s["eval_chunk_ids"] = [c + 1 for c in s["eval_chunk_ids"]]
    return _oob_void(root, f, "eval_chunk_ids")


@case("oob4096", "a-per-example-vector-one-entry-short-is-VOID", "fail")
def _(root):
    def f(a, s):
        s["per_example"]["model"] = s["per_example"]["model"][:-1]
    return _oob_void(root, f, "per-example")


@case("oob4096", "a-per-example-entry-of-2-is-VOID", "fail")
def _(root):
    def f(a, s):
        s["per_example"]["model"][0] = 2
    return _oob_void(root, f, "per-example")


@case("oob4096", "a-per-example-sha-not-the-vectors-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["model"]["per_example_sha256"] = "0" * 64
    return _oob_void(root, f, "per_example_sha256")


@case("oob4096", "a-record-top1-not-its-vectors-mean-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["model"]["top1"] = round(a["fits"]["model"]["top1"] + 0.001, 4)
    return _oob_void(root, f, "record top1")


@case("oob4096", "a-record-per-family-not-its-vectors-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["incumbent"]["per_family"]["csv"] = round(a["fits"]["incumbent"]["per_family"]["csv"] + 0.001, 4)
    return _oob_void(root, f, "per_family")


@case("oob4096", "the-model-fit-under-another-recipe-hash-is-VOID", "fail")
def _(root):
    r18 = _oob_reader()
    def f(a, s):
        a["fits"]["model"]["params_sha256"] = r18.RECIPE_SHA256["incumbent"]
    return _oob_void(root, f, "sealed M4")


@case("oob4096", "the-model-params-changed-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["model"]["params"] = dict(a["fits"]["model"]["params"], max_iter=300)
    return _oob_void(root, f, "sealed M4")


@case("oob4096", "the-model-fitted-on-rows-that-are-not-the-sealed-pool-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["model"]["fit_rows_sha256"] = "0" * 64
    return _oob_void(root, f, "sealed rows")


@case("oob4096", "the-logistic-fitted-on-one-row-fewer-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["logistic_l3"]["n_fit_rows"] -= 1
    return _oob_void(root, f, "sealed rows")


@case("oob4096", "the-logistic-not-standardised-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["logistic_l3"]["scaled"] = False
    return _oob_void(root, f, "sealed L3")


@case("oob4096", "the-model-fitted-with-group-validation-instead-of-frag-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["model"]["val"] = "group"
    return _oob_void(root, f, "sealed M4")


@case("oob4096", "a-record-without-an-iteration-count-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["model"]["fit_info"] = {}; a["fit_info_by_role"]["model"] = {}
    return _oob_void(root, f, "iteration count")


@case("oob4096", "fit-info-by-role-not-the-records-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fit_info_by_role"]["model"] = {"n_iter": 250}
    return _oob_void(root, f, "fit_info_by_role")


@case("oob4096", "two-ledger-completions-for-the-model-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["ledger"].append(dict(a["ledger"][-1]))
    return _oob_void(root, f, "ledger completions")


@case("oob4096", "a-missing-ledger-completion-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["ledger"] = [e for e in a["ledger"] if not (e["name"] == "incumbent" and e["event"] == "completed")]
    return _oob_void(root, f, "ledger completions")


@case("oob4096", "a-completion-under-another-fingerprint-is-VOID", "fail")
def _(root):
    def f(a, s):
        for e in a["ledger"]:
            if e["name"] == "model" and e["event"] == "completed":
                e["fingerprint"] = "0" * 16
    return _oob_void(root, f, "fingerprint")


@case("oob4096", "a-record-fingerprint-not-recomputable-from-the-sealed-literals-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["model"]["fingerprint"] = "0" * 16
    return _oob_void(root, f, "fingerprint")


@case("oob4096", "a-completion-without-a-preceding-start-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["ledger"] = [e for e in a["ledger"] if not (e["name"] == "model" and e["event"] == "started")]
    return _oob_void(root, f, "started")


@case("oob4096", "completions-out-of-the-sealed-order-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["ledger"] = a["ledger"][2:] + a["ledger"][:2]   # the null's two events moved to the end
    return _oob_void(root, f, "sealed order")


@case("oob4096", "an-incomplete-artifact-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["complete"] = False; a["missing_roles"] = ["model"]
    return _oob_void(root, f, "complete")


@case("oob4096", "a-complete-artifact-without-a-finish-time-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["run_finished_utc"] = None
    return _oob_void(root, f, "complete")


@case("oob4096", "a-protocol-with-a-lower-bar-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["protocol"] = dict(a["protocol"], bar={"model_real_correct_over_n_real_minus_chance": 0.04})
    return _oob_void(root, f, "protocol")


@case("oob4096", "a-recipe-with-more-iterations-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["recipes"] = dict(a["recipes"], model=dict(a["recipes"]["model"], params=dict(a["recipes"]["model"]["params"], max_iter=300)))
    return _oob_void(root, f, "recipes")


@case("oob4096", "a-changed-in-distribution-reference-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["reference_top1"] = dict(a["reference_top1"], model=0.28)
    return _oob_void(root, f, "references")


@case("oob4096", "a-different-sklearn-version-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["environment"] = dict(a["environment"], sklearn="1.8.0")
    return _oob_void(root, f, "environment")


@case("oob4096", "a-different-python-version-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["model"]["environment"] = dict(a["fits"]["model"]["environment"], python="3.12.1")
    return _oob_void(root, f, "environment")


@case("oob4096", "a-launch-environment-with-a-problem-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["launch_environment"]["ok"] = False; a["launch_environment"]["problems"] = ["MemAvailable 12.0 GB < 14.5"]
    return _oob_void(root, f, "launch_environment")


@case("oob4096", "a-not-run-file-beside-an-artifact-is-no-verdict", "fail")
def _(root):
    piv = os.path.join(root, "artifacts", "pivot"); os.makedirs(piv, exist_ok=True)
    json.dump({"schema": "raise-v1/oob_4096_not_run/1", "preregistration": "0018-oob-4096", "stage": "run",
               "reason": "null control read 0.06 on the extension rows", "utc": "2026-09-10T00:02:00Z", "n_checkpoints": 1},
              open(os.path.join(piv, "oob_4096_not_run.json"), "w"))
    rc, out = _oob(root)   # a complete, passing artifact sits beside the marker
    if os.path.exists(os.path.join(piv, "oob_4096_verdict.json")):
        return 0, out + " !! a verdict was emitted beside a NOT RUN marker"
    if rc != 2 or "NOT RUN" not in out:
        return 0, out + " !! the reader did not report NOT RUN with exit 2"
    return rc, out


@case("oob4096", "artifact-absent-is-no-verdict", "fail")
def _(root):
    return _oob(root, drop_artifact=True)


@case("oob4096", "scores-file-absent-is-VOID", "fail")
def _(root):
    return _oob_void(root, None, "scores", drop_scores=True)


@case("oob4096", "another-preregistration-id-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["preregistration"] = "0017-lofo-l3-4096"
    return _oob_void(root, f, "preregistration")


@case("oob4096", "the-null-record-not-a-null-stage-fit-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["null"]["head"] = "model"; a["null_control"] = a["fits"]["null"]
    return _oob_void(root, f)


@case("oob4096", "the-null-fitted-with-the-incumbent-recipe-is-VOID", "fail")
def _(root):
    r18 = _oob_reader()
    def f(a, s):
        a["fits"]["null"]["id"] = "M1"; a["fits"]["null"]["params_sha256"] = r18.RECIPE_SHA256["incumbent"]; a["null_control"] = a["fits"]["null"]
    return _oob_void(root, f, "sealed M4")


@case("oob4096", "the-null-labels-not-a-permutation-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["partition"]["null_labels_permuted"] = False
    return _oob_void(root, f, "permutation")


@case("oob4096", "a-fit-with-another-seed-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["incumbent"]["seed"] = 1
    return _oob_void(root, f, "seed")


@case("oob4096", "a-banked-exact-margin-off-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["ext_margin_model_over_logistic_l3_exact"] = round(a["ext_margin_model_over_logistic_l3_exact"] + 0.000001, 6)
    return _oob_void(root, f, "margin")


@case("oob4096", "extension-chunk-ids-not-disjoint-from-the-builder-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["ext_corpus"]["chunk_ids_disjoint_from_builder"] = False
    return _oob_void(root, f, "disjoint")


@case("oob4096", "a-measured-overlap-of-one-row-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["partition"]["pool_rows_identical_to_an_ext_row"] = 1
    return _oob_void(root, f, "leakage")


@case("oob4096", "a-shared-evaluation-chunk-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["partition"]["eval_chunks_shared_with_ext"] = 1
    return _oob_void(root, f, "leakage")


@case("oob4096", "a-banked-subset-reading-off-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["readings"]["model"]["ext_real_top1"] = round(a["readings"]["model"]["ext_real_top1"] + 0.0001, 4)
    return _oob_void(root, f, "readings")


@case("oob4096", "the-banked-null-extension-reading-not-the-recomputed-one-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["shuffled_label_accuracy_ext"] = round(a["shuffled_label_accuracy_ext"] + 0.0001, 4)
    return _oob_void(root, f, "null control")


@case("oob4096", "a-pool-fit-with-a-failed-block-probe-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["model"]["block_refills"] = [{"probe_ok": False}]
    return _oob_void(root, f, "probe")


@case("oob4096", "a-record-with-memory-infeasible-status-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["fits"]["model"]["status"] = "infeasible_memory"
    return _oob_void(root, f, "status")


@case("oob4096", "a-partition-with-another-evaluation-hash-is-VOID", "fail")
def _(root):
    def f(a, s):
        a["partition"]["eval_idx_sha256"] = "0" * 64
    return _oob_void(root, f, "sealed set")


@case("oob4096", "an-artifact-whose-fits-block-is-a-list-is-VOID-not-a-traceback", "fail")
def _(root):
    def f(a, s):
        a["fits"] = [a["fits"]["model"]]
    rc, out = _oob(root, f)
    piv = os.path.join(root, "artifacts", "pivot")
    if not os.path.exists(os.path.join(piv, "oob_4096_verdict.json")):
        return 0, out + " !! no verdict file was written"
    v = json.load(open(os.path.join(piv, "oob_4096_verdict.json")))
    return (1 if v["verdict"] == "VOID" else 0), f"verdict={v['verdict']} validity={v['validity_failed_clauses'][:1]}"


@case("oob4096", "the-mixture-flag-is-banked-but-does-not-decide-the-verdict", "fail")
def _(root):
    # M4 clears the real-family bar while the eight-family mixture stays under its flag threshold: the verdict passes and
    # the flag reads False, so a reader that decided on the mixture would disagree with this reader
    r18 = _oob_reader()
    rc0, out0 = _oob(root, model_real_correct=r18.MIN_CORRECT_REAL + 50, model_synth_acc=0.01)
    if rc0 != 0:
        return 0, out0 + " !! the real-family clause should pass regardless of the synthetic families"
    piv = os.path.join(root, "artifacts", "pivot"); v = json.load(open(os.path.join(piv, "oob_4096_verdict.json")))
    if v["bar_applied"]["flags"]["mixture_reaches_bar"] is not False:
        return 0, out0 + " !! the mixture flag should read False here"
    rc1, out1 = _oob(root, model_real_correct=r18.MIN_CORRECT_REAL - 1, model_synth_acc=0.5)
    return rc1, out0 + " | " + out1


# ---- the re-read (preregistration 0019): the same clauses, one literal apart; the filed defect stays visible

@case("oob4096", "0018s-frozen-reader-VOIDs-the-runners-null-block-(the-filed-defect)", "fail")
def _(root):
    # CORRECTIONS.md 2026-09-10: 0018 sealed 0017's fold-based null block hash; the runner fits the first 20000 pool rows.
    # An artifact built the way the runner builds it (0019's literals) must stay VOID under 0018's frozen reader, on that hash.
    rc, out = _oob(root, prereg="0018", build_from="0019")
    if rc != 0 and ("null_sorted_sha256" not in out or "verdict=VOID" not in out):
        return 0, out + " !! 0018's reader no longer VOIDs on the null block hash; the filed defect changed shape"
    return rc, out


@case("oob4096", "control-passes-under-the-re-read-reader", "pass")
def _(root):
    return _oob(root, prereg="0019")


@case("oob4096", "0018s-sealed-null-literal-is-VOID-under-the-re-read-reader", "fail")
def _(root):
    # the fold block 0018 sealed is not the block the runner fits; under the corrected literal it is a hash mismatch like any other
    return _oob_void(root, None, expect_clause="null_sorted_sha256", prereg="0019", build_from="0018")


@case("oob4096", "a-null-block-that-is-neither-sealed-literal-is-VOID-under-the-re-read-reader", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["null_sorted_sha256"] = "0" * 64; art["fits"]["null"]["fit_rows_sorted_sha256"] = "0" * 64
    return _oob_void(root, f, expect_clause="null_sorted_sha256", prereg="0019")


@case("oob4096", "one-real-family-row-under-the-bar-is-OOB_TRANSFER_FAILS-under-the-re-read-reader", "fail")
def _(root):
    r19 = _oob_reader("oob4096_reread_verdict.py")
    rc, out = _oob(root, prereg="0019", model_real_correct=r19.MIN_CORRECT_REAL - 1)
    if rc != 0 and "verdict=OOB_TRANSFER_FAILS" not in out:
        return 0, out + " !! detected but not as OOB_TRANSFER_FAILS"
    return rc, out


@case("oob4096", "an-artifact-stamped-0019-is-VOID-under-both-readers-(the-re-read-reads-0018s-artifact)", "fail")
def _(root):
    def f(art, scores):
        art["preregistration"] = "0019-oob-4096-reread"; scores["preregistration"] = "0019-oob-4096-reread"
    rc19, out19 = _oob_void(root, f, expect_clause="preregistration", prereg="0019")
    rc18, out18 = _oob_void(root, f, expect_clause="preregistration", prereg="0018")   # each reader on its own literals: the stamp is the sole cause
    if rc19 == 0 or rc18 == 0:
        return 0, f"0019: {out19[:120]} | 0018: {out18[:120]}"
    return 1, f"0019: {out19[:120]} | 0018: {out18[:120]}"


@case("oob4096", "the-re-read-reader-is-0018s-frozen-reader-plus-exactly-the-declared-substitutions", "pass")
def _(root):
    expected, problem = _reread_0019_expected_text()
    if expected is None:
        return 1, problem
    actual = open(os.path.join(REPO, "tools", "readers", "oob4096_reread_verdict.py"), encoding="utf-8").read()
    if actual != expected:
        import difflib
        d = [l for l in difflib.unified_diff(expected.splitlines(), actual.splitlines(), lineterm="", n=0) if l[:1] in "+-"][:6]
        return 1, "the re-read reader differs from 0018's reader plus the declared substitutions: " + " | ".join(d)
    return 0, "identical to 0018's frozen reader plus the declared substitutions"


@case("oob4096", "the-re-read-literal-is-the-block-the-runner-fitted-and-0018s-is-0017s-fold-block", "pass")
def _(root):
    # ties both readers' literals to the world as banked: the runner's artifact, 0014's null control, 0016's sealed null (pool
    # block) and 0015's, 0017's sealed nulls and lofo artifacts (fold block); with the cache present, recomputed from y and g
    r18 = _oob_reader("oob4096_verdict.py"); r19 = _oob_reader("oob4096_reread_verdict.py")
    A = lambda *p: json.load(open(os.path.join(REPO, *p)))  # noqa: E731
    art = A("artifacts", "pivot", "oob_4096.json"); r14 = A("artifacts", "pivot", "recipe_search_4096.json")
    p15 = A("prereg", "0015-lofo-4096.json"); p16 = A("prereg", "0016-fdc-4096.json"); p17 = A("prereg", "0017-lofo-l3-4096.json")
    l15 = A("artifacts", "pivot", "lofo_4096.json"); l17 = A("artifacts", "pivot", "lofo_l3_4096.json")
    pool = {r19.PARTITION["null_sorted_sha256"], _OOB_RUNNER_NULL, art["partition"]["null_sorted_sha256"],
            art["fits"]["null"]["fit_rows_sorted_sha256"], r14["null_control"]["fit_rows_sorted_sha256"],
            p16["scope"]["sealed_partition"]["null"]["sorted_sha256"]}
    fold = {r18.PARTITION["null_sorted_sha256"], _OOB_0018_NULL, p15["scope"]["sealed_partition"]["null"]["null_sorted_sha256"],
            p17["scope"]["sealed_partition"]["null"]["null_sorted_sha256"], l15["partition"]["null_sorted_sha256"],
            l17["partition"]["null_sorted_sha256"]}
    if len(pool) != 1 or len(fold) != 1 or pool == fold:
        return 1, f"pool-block hashes {sorted(h[:8] for h in pool)} fold-block hashes {sorted(h[:8] for h in fold)}"
    cache = os.path.join(REPO, "data", "pivot", "full_c4096.npz")
    if os.path.exists(cache):
        rc, out = run([PY, "tools/pivot/null_block_check.py", "--cache", cache, "--sealed", r19.PARTITION["null_sorted_sha256"],
                       "--artifact", "artifacts/pivot/oob_4096.json"], REPO)
        if rc != 0:
            return 1, "null_block_check.py on the cache: " + out[-300:]
        return 0, "one pool block, one fold block, and the cache recomputation agrees"
    return 0, "one pool block, one fold block (cache absent: the recomputation from y and g was not run here)"


def _tiny_cache(root):
    """A small builder-shaped cache (y, g only) in the sandbox for exercising tools/pivot/null_block_check.py without the data."""
    import numpy as np
    n_chunks, rows = 400, 26
    g = np.repeat(np.arange(n_chunks, dtype=np.int32), rows); y = np.tile(np.arange(rows, dtype=np.int16), n_chunks)
    path = os.path.join(root, "tiny_c4096.npz"); np.savez(path, y=y, g=g)
    sys.path.insert(0, os.path.join(REPO, "tools", "pivot"))
    from run_carve import grouped_split  # noqa: E402
    ev, tr, _ = grouped_split(y, g, 20260825, 0.2, 8000)
    return path, hashlib.sha256(np.ascontiguousarray(np.sort(tr[:20000]).astype(np.int64)).tobytes()).hexdigest()


@case("oob4096", "null-block-tool-passes-on-the-block-recomputed-from-y-and-g", "pass")
def _(root):
    path, pool = _tiny_cache(root)
    return run([PY, "tools/pivot/null_block_check.py", "--cache", path, "--sealed", pool, "--cap", "8000"], REPO)


@case("oob4096", "null-block-tool-fails-on-a-literal-that-is-not-the-recomputed-block", "fail")
def _(root):
    path, pool = _tiny_cache(root)
    rc, out = run([PY, "tools/pivot/null_block_check.py", "--cache", path, "--sealed", "0" * 64, "--cap", "8000"], REPO)
    if rc != 0 and "NULL BLOCK CHECK: FAIL" not in out:
        return 0, out + " !! non-zero exit without the FAIL line"
    return rc, out


@case("oob4096", "an-artifact-whose-fits-block-is-a-list-is-VOID-under-the-re-read-reader-with-the-0019-stamp", "fail")
def _(root):
    def f(art, scores):
        art["fits"] = [art["fits"][k] for k in art["fits"]]
    rc, out = _oob(root, f, prereg="0019")
    vf = os.path.join(root, "artifacts", "pivot", "oob_4096_reread_verdict.json")
    if not os.path.exists(vf):
        return 0, out + " !! no re-read verdict file written on the unexpected-shape path"
    v = json.load(open(vf))
    if v.get("verdict") != "VOID" or v.get("preregistration") != "0019-oob-4096-reread" or v.get("reads_artifact_of") != "0018-oob-4096" \
            or v.get("schema") != "raise-v1/oob_4096_reread_verdict/1":
        return 0, f"!! unexpected-shape verdict carries {v.get('verdict')}, {v.get('preregistration')}, {v.get('reads_artifact_of')}, {v.get('schema')}"
    return rc, out


@case("oob4096", "a-declared-occurrence-count-off-by-one-is-refused-by-the-rebuild", "fail")
def _(root):
    pr = json.load(open(os.path.join(REPO, "prereg", "0019-oob-4096-reread.json")))
    subs = json.loads(json.dumps(pr["scope"]["what_changes_from_0018"]["declared_substitutions"]))
    subs[0]["occurrences"] += 1
    expected, problem = _reread_0019_expected_text(subs=subs)
    return (1 if expected is None else 0), (problem or "!! an off-by-one occurrence count was accepted")


@case("oob4096", "a-re-read-reader-with-any-other-line-changed-is-detected", "fail")
def _(root):
    # a mutation of the structural check above: one undeclared change (the bar) must be caught by the same comparison
    expected, problem = _reread_0019_expected_text()
    if expected is None:
        return 1, problem
    actual = open(os.path.join(REPO, "tools", "readers", "oob4096_reread_verdict.py"), encoding="utf-8").read()
    tampered = actual.replace("BAR = 0.05", "BAR = 0.04")
    if tampered == actual:
        return 0, "!! the tamper target was not found; the structural check was not exercised"
    return (1 if tampered != expected else 0), ("tampered copy differs from 0018 plus the declared substitutions" if tampered != expected
                                                 else "!! a tampered reader passed the structural check")


# ---------------------------------------------------------------- realfit4096 gate (preregistration 0020)
#
# The control artifact is built from the RUNNER's output shape, not the reader's expectations
# (docs/OPERATING_RULES.md section 4, and the finding the 0019 review filed against the oob4096 gate):
# tests/fixtures/realfit_runner_shape.json is a smoke run of tools/pivot/run_realfit.py with its values
# left in place, and the gate replaces the values with the sealed ones while keeping every key, nesting
# and record field the runner wrote. Each mutation below must be shown to fail on its own.

_RF_SHAPE = os.path.join(REPO, "tests", "fixtures", "realfit_runner_shape.json")


def _rf_reader():
    import importlib.util
    spec = importlib.util.spec_from_file_location("r20", os.path.join(REPO, "tools", "readers", "realfit4096_rerun_verdict.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _rf_readings(r20, v, fam_x, fam_e):
    """The runner's readings() over one per-example vector, recomputed here from the same rule."""
    n_eval, n_ext = r20.PARTITION["n_eval_rows"], r20.N_EXT
    rep, ex = v[:n_eval], v[n_eval:]
    by = {f: [] for f in r20.EXT_FAMILIES}
    for i in range(n_ext):
        by[fam_x[i]].append(ex[i])
    m4 = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
    real = [x for f in r20.REAL_FAMILIES for x in by[f]]; synth = [x for f in r20.SYNTH_FAMILIES for x in by[f]]
    return {"builder_eval_top1": m4(rep), "builder_eval_correct": sum(rep), "ext_top1": m4(ex), "ext_correct": sum(ex),
            "n_ext_rows": n_ext, "ext_per_family": {f: m4(by[f]) for f in r20.EXT_FAMILIES},
            "ext_per_family_correct": {f: sum(by[f]) for f in r20.EXT_FAMILIES},
            "ext_structured_text_top1": m4([x for f in r20.STRUCTURED_TEXT for x in by[f]]),
            "ext_high_entropy_top1": m4([x for f in r20.HIGH_ENTROPY for x in by[f]]),
            "ext_real_top1": m4(real), "ext_real_correct": sum(real), "n_ext_real_rows": len(real),
            "ext_synthetic_correct": sum(synth), "ext_synthetic_top1": m4(synth),
            "builder_eval_per_family": {f: m4([rep[i] for i in range(n_eval) if fam_e[i] == f]) for f in r20.FAMILIES}}


def _rf_sub(fixture_block, sealed_block, label, sealed_may_be_subset=False):
    """Substitute sealed values INTO the runner's own block, key by key, and refuse on any key the two do not share.

    0020's pre-freeze review found the previous version doing `dict(r20.FIT)` - taking the whole block from the
    READER's literals - which is exactly what OPERATING_RULES section 4 forbids: a control that shares an assumption
    with the reader cannot see the reader disagree with the world. Four wrong values and one invented key sat behind
    that and the 33-case gate was green throughout. Here the KEY SET is the runner's, from the captured fixture, and
    only the values are the run's; a reader that expects a key the runner does not write, or stops expecting one it
    does, fails the gate at construction time instead of an hour into the run.
    """
    fk, sk = set(fixture_block), set(sealed_block)
    if sealed_may_be_subset:
        if not sk <= fk:
            raise AssertionError(f"{label}: the reader expects keys the runner does not write: {sorted(sk - fk)}")
    elif fk != sk:
        raise AssertionError(f"{label}: reader-only {sorted(sk - fk)}, runner-only {sorted(fk - sk)}")
    return dict(fixture_block, **sealed_block)


def _good_realfit(real_correct=None, acc=None, repro=None, null_acc=None, matched_real_correct=None):
    """A complete, valid 0020 artifact set. Shape AND key sets from the runner's own smoke output (tests/fixtures/
    realfit_runner_shape.json); only the values are the sealed run's. real_correct sets real_model's correct
    real-family row count exactly; matched_real_correct does the same for the builder-matched arm; acc/repro/null_acc
    set accuracies."""
    r20 = _rf_reader()
    shape = json.load(open(_RF_SHAPE, encoding="utf-8"))["artifact"]
    part = _rf_sub(shape["partition"], dict(r20.PARTITION), "partition", sealed_may_be_subset=True)
    n_eval = part["n_eval_rows"]; n_ext = r20.N_EXT
    fams = list(r20.EXT_FAMILIES); rpf = r20.EXT["rows_per_family"]
    fam_idx = []
    for k, f in enumerate(fams):
        fam_idx += [k] * rpf[f]
    assert len(fam_idx) == n_ext
    fam_x = [fams[i] for i in fam_idx]
    ext_ids = [c for c, n in zip(r20.EXT_CHUNK_IDS, r20.EXT_ROWS_PER_CHUNK) for _ in range(n)]
    assert len(ext_ids) == n_ext
    # The real evaluation chunk ids, from the reader's sealed run-length encoding of the run's own g[ev] array.
    # They were invented here before (a synthetic gutenberg/other mix that satisfied the range, distinct-count and
    # family-mix checks but nothing else), which is why there was nothing for a digest to bind against.
    eval_ids = [c for c, n in zip(r20.EVAL_CHUNK_IDS, r20.EVAL_ROWS_PER_CHUNK) for _ in range(n)]
    assert len(eval_ids) == n_eval
    fam_e = [r20.FAMILIES[c % 8] for c in eval_ids]
    real = set(r20.REAL_FAMILIES)
    base_acc = {"repro": r20.REPRO_REFERENCE, "null": 0.038, "real_model": 0.12, "real_incumbent": 0.10,
                "real_logistic": 0.09, "builder_matched": 0.11, "builder_chunk_matched": 0.10,
                # out-of-sample readings on the extension real rows, where a trivial rule fitted on real content
                # sits near chance (the pre-freeze smoke read 0.0385/0.0445/0.0445/0.0457 there) - not 0003's
                # in-distribution builder-content figures, which are a different corpus
                "floor_majority": 0.0385, "floor_stratified": 0.0387, "floor_feat1": 0.045, "floor_tree3": 0.055}
    assert set(base_acc) == set(r20.ORDER), sorted(set(r20.ORDER) ^ set(base_acc))
    base_acc.update(acc or {})
    if repro is not None:
        base_acc["repro"] = repro
    if null_acc is not None:
        base_acc["null"] = null_acc

    def vec(name):
        v = [0] * (n_eval + n_ext)
        k = int(round(base_acc[name] * n_eval))
        for i in range(k):
            v[i] = 1
        per = {f: int(round(base_acc[name] * rpf[f])) for f in fams}
        target = {"real_model": real_correct, "builder_matched": matched_real_correct}.get(name)
        if target is not None:
            rf = [f for f in fams if f in real]; b, extra = divmod(int(target), len(rf))
            for j, f in enumerate(rf):
                per[f] = b + (1 if j < extra else 0)
        pos = n_eval
        for f in fams:
            for i in range(pos, pos + per[f]):
                v[i] = 1
            pos += rpf[f]
        return v

    def fp(name):
        return r20.fingerprint(prereg=r20.PREREG, seed=r20.SEED, role=name, cand=r20.RECIPES[r20.RECIPE_OF[name]],
                               stage=r20.STAGE_OF[name], rows=part[r20.ROWS_OF[name][2]],
                               eval=part["eval_idx_sha256"], ext=r20.EXT["arrays"]["X"]["sha256"],
                               fit=r20.FIT["arrays"]["X"]["sha256"])

    def record(name, v):
        c = r20.RECIPES[r20.RECIPE_OF[name]]
        n_key, idx_key, sorted_key = r20.ROWS_OF[name]
        m4 = lambda xs: round(sum(xs) / len(xs), 4)  # noqa: E731
        ng = [v[i] for i in range(n_eval) if fam_e[i] != "gutenberg"] + v[n_eval:]
        # fit_info, block_refills and environment are the RUNNER's, taken from the captured record and never
        # overwritten. Overwriting fit_info with {"n_iter": 100} for all eleven arms handed the reader a value the
        # runner never writes for the four trivial baselines - which is how a reader that voids an honest run on
        # four clauses sat behind a green 58/58 gate (0021 pre-freeze review, instrument lens, finding H3). The key
        # sets are checked both ways by _rf_sub; these three are checked by not being touched.
        sealed = {"id": c["id"], "head": name, "family": c["family"], "params": c.get("params", {}),
                  "scaled": bool(c.get("scaled", False)), "val": c.get("val"), "seed": r20.SEED,
                  "params_sha256": r20.RECIPE_SHA256[r20.RECIPE_OF[name]], "stage": r20.STAGE_OF[name],
                  "n_fit_rows": part[n_key], "fit_rows_sha256": part[idx_key], "fit_rows_sorted_sha256": part[sorted_key],
                  "environment": dict(shape["fits"][name]["environment"], threads=3, nice=10),
                  "interruptions_before_this_fit": 0, "status": "fit",
                  "top1": m4(v), "top1_non_gutenberg": m4(ng),
                  "per_family": {f: m4([v[i] for i in range(n_eval) if fam_e[i] == f]) for f in r20.FAMILIES},
                  "fingerprint": fp(name), "per_example_sha256": hashlib.sha256(bytes(v)).hexdigest()}
        return _rf_sub(shape["fits"][name], sealed, f"fits.{name}", sealed_may_be_subset=True)

    per_example, reads, fits = {}, {}, {}
    for name in r20.ORDER:
        v = vec(name); per_example[name] = v
        reads[name] = _rf_readings(r20, v, fam_x, fam_e)
        fits[name] = record(name, v)
    ledger = []
    for i, nm in enumerate(r20.ORDER):
        ledger += [{"name": nm, "fingerprint": fp(nm), "event": "started", "utc": f"2026-09-16T05:{i:02d}:00Z"},
                   {"name": nm, "fingerprint": fp(nm), "event": "completed", "utc": f"2026-09-16T05:{i:02d}:30Z"}]
    part.update({"pool_chunks_shared_with_ext": 0, "eval_chunks_shared_with_ext": 0, "fit_chunks_shared_with_ext": 0,
                 "fit_chunks_shared_with_builder": 0, "fit_source_chunks_shared_with_ext": 0,
                 "fit_rows_identical_to_a_scored_row": 0,
                 "matched_rows_identical_to_a_scored_row": r20.EXPECTED_COLLISIONS["matched_block"],
                 "repro_rows_identical_to_a_scored_row": r20.EXPECTED_COLLISIONS["repro_block"],
                 "chunk_matched_rows_identical_to_a_scored_row": r20.EXPECTED_COLLISIONS["chunk_matched_block"],
                 "expected_rows_identical_to_a_scored_row": dict(r20.EXPECTED_COLLISIONS),
                 "pool_rows_identical_to_a_scored_row": r20.POOL_ROWS_IDENTICAL,
                 "pool_collision_row_sha256": r20.EXPECTED_COLLISION_ROW_SHA["pool_block"],
                 "repro_collision_row_sha256": r20.EXPECTED_COLLISION_ROW_SHA["repro_block"],
                 "matched_collision_row_sha256": r20.EXPECTED_COLLISION_ROW_SHA["matched_block"],
                 "n_fit_source_chunks": r20.FIT["n_chunks"],
                 "n_ext_source_chunks": r20.EXT["n_chunks"], "null_y_shuffled_sha256": "0" * 64,
                 "null_labels_permuted": True, "null_labels_same_multiset": True,
                 "row_identity_digest": "blake2b-128 of the contiguous float32 feature row, over every scored row"})
    rm = reads["real_model"]
    art = dict(shape)                        # the runner's own key set, values replaced
    art.update({"schema_version": 1, "schema": "raise-v1/realfit_4096_rerun/1", "preregistration": r20.PREREG, "smoke": False,
                "stage": "run", "protocol": r20.PROTOCOL, "protocol_sha256": r20.PROTOCOL_SHA256, "recipes": r20.RECIPES,
                "recipes_sha256": r20.RECIPES_SHA256,
                "corpus": _rf_sub(shape["corpus"], dict(r20.CORPUS), "corpus", sealed_may_be_subset=True),
                "ext_corpus": _rf_sub(shape["ext_corpus"], dict(r20.EXT), "ext_corpus"),
                "fit_corpus": _rf_sub(shape["fit_corpus"], dict(r20.FIT), "fit_corpus"),
                "partition": part, "n_classes": 26, "class_names": [],
                "chance_accuracy": r20.CHANCE, "environment": dict(r20.ENV, threads=3, nice=10),
                "launch_environment": {"ok": True, "problems": [], "env": dict(r20.ENV, threads=3, nice=10),
                                       "loadavg_1_5_15": [0.1, 0.1, 0.1]},
                "launch_number": 1, "complete": True, "missing_roles": [], "fits": fits, "readings": reads,
                "ext_real_top1": {n: reads[n]["ext_real_top1"] for n in r20.ORDER},
                "ext_real_correct": {n: reads[n]["ext_real_correct"] for n in r20.ORDER},
                "ext_top1": {n: reads[n]["ext_top1"] for n in r20.ORDER},
                "ext_correct": {n: reads[n]["ext_correct"] for n in r20.ORDER},
                "builder_eval_top1": {n: reads[n]["builder_eval_top1"] for n in r20.ORDER},
                "ext_per_family": {n: reads[n]["ext_per_family"] for n in r20.ORDER},
                "ext_real_top1_model": rm["ext_real_top1"], "ext_real_correct_model": rm["ext_real_correct"],
                "ext_top1_model": rm["ext_top1"], "ext_correct_model": rm["ext_correct"],
                "n_ext_real_rows": rm["n_ext_real_rows"], "n_ext_rows": n_ext, "n_eval_rows": n_eval,
                "ext_real_families": list(r20.REAL_FAMILIES), "ext_synthetic_families": list(r20.SYNTH_FAMILIES),
                "fit_families": list(r20.FIT_FAMILIES), "fit_rows_per_family": r20.FIT["rows_per_family"],
                "reproduction_top1": reads["repro"]["builder_eval_top1"],
                "reference_top1": {"repro": r20.REPRO_REFERENCE},
                "shuffled_label_accuracy_ext": reads["null"]["ext_top1"],
                "shuffled_label_accuracy_eval": reads["null"]["builder_eval_top1"],
                "null_control": fits["null"],
                "fit_info_by_name": {n: fits[n]["fit_info"] for n in r20.ORDER},
                "cluster_ci95_informational": {}, "ledger": ledger, "cost": {},
                "fit_record_top1_is": shape["fit_record_top1_is"],
                "run_started_utc": "2026-09-16T05:00:00Z", "first_launch_utc": "2026-09-16T05:00:00Z",
                "run_finished_utc": "2026-09-16T06:00:00Z"})
    scores = {"schema": "raise-v1/realfit_4096_rerun_scores/1", "preregistration": r20.PREREG, "smoke": False,
              "n_eval_rows": n_eval, "n_ext_rows": n_ext, "eval_idx_sha256": part["eval_idx_sha256"],
              "eval_chunk_ids": eval_ids, "ext_chunk_ids": ext_ids, "ext_fam": fam_idx, "ext_families": fams,
              "ext_arrays_sha256": {k: v["sha256"] for k, v in r20.EXT["arrays"].items()},
              "fit_arrays_sha256": {k: v["sha256"] for k, v in r20.FIT["arrays"].items()},
              "per_example": per_example}
    return art, scores


def _realfit(root, mutate=None, drop_artifact=False, drop_scores=False, not_run=None, **kw):
    art, scores = _good_realfit(**kw)
    if mutate:
        r = mutate(art, scores)
        if r is not None:
            art = r
    piv = os.path.join(root, "artifacts", "pivot"); os.makedirs(piv, exist_ok=True)
    if not drop_scores:
        json.dump(scores, open(os.path.join(piv, "realfit_4096_rerun_scores.json"), "w"))
    if not drop_artifact:
        json.dump(art, open(os.path.join(piv, "realfit_4096_rerun.json"), "w"))
    if not_run is not None:
        json.dump(not_run, open(os.path.join(piv, "realfit_4096_rerun_not_run.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", "realfit4096_rerun_verdict.py"),
                os.path.join(root, "tools", "readers", "realfit4096_rerun_verdict.py"))
    rc, out = run([PY, "tools/readers/realfit4096_rerun_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(piv, "realfit_4096_rerun_verdict.json")))
    ok = v["verdict"] == "REAL_FIT_CLEARS"
    return (0 if ok else 1), (f"verdict={v['verdict']} real={v.get('ext_real_top1_model')} "
                              f"correct={v.get('ext_real_correct_model')} validity={v['validity_failed_clauses'][:2]} "
                              f"clause={v['clause_failed']}")


def _realfit_void(root, mutate, expect_clause=None, **kw):
    rc, out = _realfit(root, mutate, **kw)
    if rc != 0 and "verdict=VOID" not in out and "No verdict emitted" not in out:
        return 0, out + " !! detected but not as VOID"
    if expect_clause and expect_clause not in out:
        return 0, out + f" !! VOID for another reason than {expect_clause!r}"
    return rc, out


def _rf_need(**kw):
    """The clause's row count for a given control: ceil(N_REAL * (measured floor + BAR)). The floor is what the four
    trivial-baseline arms reach on the real-family rows OF THAT CONTROL, so a boundary case cannot be written against
    a constant - which is the point of OPERATING_RULES section 4a."""
    r20 = _rf_reader()
    art, _ = _good_realfit(**kw)
    floor = max(art["ext_real_top1"][n] for n in r20.FLOOR_ROLES)
    return int(math.ceil(r20.N_REAL * (floor + r20.BAR) - 1e-9))


@case("realfit4096", "control-real-fit-clears-the-bar-on-the-real-families", "pass")
def _(root):
    return _realfit(root)


@case("realfit4096", "one-real-family-row-under-the-bar-is-REAL_FIT_FAILS", "fail")
def _(root):
    r20 = _rf_reader()
    rc, out = _realfit(root, real_correct=_rf_need() - 1)
    if rc != 0 and "verdict=REAL_FIT_FAILS" not in out:
        return 0, out + " !! detected but not as REAL_FIT_FAILS"
    return rc, out


@case("realfit4096", "exactly-min-correct-real-rows-clears-and-one-fewer-fails", "fail")
def _(root):
    need = _rf_need()
    rc_at, out_at = _realfit(root, real_correct=need)
    rc_un, out_un = _realfit(root, real_correct=need - 1)
    if rc_at != 0:
        return 0, f"!! exactly {need} (measured floor + the margin) did not clear: {out_at[:150]}"
    return (1 if rc_un != 0 else 0), f"at {need}={out_at[:60]} | under={out_un[:100]}"


@case("realfit4096", "a-pass-carried-by-the-builder-matched-arm-alone-is-still-REAL_FIT_FAILS", "fail")
def _(root):
    r20 = _rf_reader()
    need = _rf_need()
    rc, out = _realfit(root, real_correct=need - 200, matched_real_correct=need + 500)
    if rc != 0 and "verdict=REAL_FIT_FAILS" not in out:
        return 0, out + " !! a flag decided the verdict"
    return rc, out


@case("realfit4096", "the-reproduction-rung-off-by-0.006-is-VOID", "fail")
def _(root):
    r20 = _rf_reader()
    return _realfit_void(root, None, expect_clause="reproduction", repro=round(r20.REPRO_REFERENCE + 0.006, 4))


@case("realfit4096", "a-reproduction-drift-inside-the-tolerance-still-clears", "pass")
def _(root):
    r20 = _rf_reader()
    return _realfit(root, repro=round(r20.REPRO_REFERENCE + r20.REPRO_TOLERANCE, 4))


@case("realfit4096", "a-leaking-null-control-is-VOID", "fail")
def _(root):
    r20 = _rf_reader()
    return _realfit_void(root, None, expect_clause="null control", null_acc=round(r20.CHANCE + r20.NULL_TOLERANCE + 0.002, 4))


@case("realfit4096", "a-smoke-artifact-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["smoke"] = True; scores["smoke"] = True
    return _realfit_void(root, f, expect_clause="smoke")


@case("realfit4096", "an-artifact-stamped-with-another-preregistration-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["preregistration"] = "0018-oob-4096"; scores["preregistration"] = "0018-oob-4096"
    return _realfit_void(root, f, expect_clause="preregistration")


@case("realfit4096", "a-fit-row-byte-identical-to-a-scored-row-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["fit_rows_identical_to_a_scored_row"] = 1
    return _realfit_void(root, f, expect_clause="fit_rows_identical_to_a_scored_row")


@case("realfit4096", "a-fit-chunk-shared-with-the-evaluation-corpus-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["fit_chunks_shared_with_ext"] = 1
    return _realfit_void(root, f, expect_clause="fit_chunks_shared_with_ext")


@case("realfit4096", "a-shared-source-chunk-hash-between-fit-and-evaluation-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["partition"]["fit_source_chunks_shared_with_ext"] = 1
    return _realfit_void(root, f, expect_clause="fit_source_chunks_shared_with_ext")


@case("realfit4096", "a-fit-corpus-array-hash-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["fit_corpus"] = dict(art["fit_corpus"])
        art["fit_corpus"]["arrays"] = dict(art["fit_corpus"]["arrays"])
        art["fit_corpus"]["arrays"]["X"] = dict(art["fit_corpus"]["arrays"]["X"], sha256="0" * 64)
    return _realfit_void(root, f, expect_clause="fit corpus")


@case("realfit4096", "an-evaluation-corpus-array-hash-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["ext_corpus"] = dict(art["ext_corpus"])
        art["ext_corpus"]["arrays"] = dict(art["ext_corpus"]["arrays"])
        art["ext_corpus"]["arrays"]["y"] = dict(art["ext_corpus"]["arrays"]["y"], sha256="0" * 64)
    return _realfit_void(root, f, expect_clause="evaluation corpus")


@case("realfit4096", "a-banked-real-correct-count-off-by-one-row-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["readings"]["real_model"]["ext_real_correct"] += 1
    return _realfit_void(root, f, expect_clause="readings")


@case("realfit4096", "a-banked-per-family-reading-off-by-0.0001-is-VOID", "fail")
def _(root):
    def f(art, scores):
        fam = _rf_reader().EXT_FAMILIES[0]
        art["readings"]["real_model"]["ext_per_family"][fam] = round(
            art["readings"]["real_model"]["ext_per_family"][fam] + 0.0001, 4)
    return _realfit_void(root, f, expect_clause="readings")


@case("realfit4096", "a-per-example-vector-whose-hash-is-not-the-records-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["fits"]["real_model"]["per_example_sha256"] = "0" * 64
    return _realfit_void(root, f, expect_clause="per_example_sha256")


@case("realfit4096", "a-fingerprint-that-is-not-the-recomputed-one-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["fits"]["real_model"]["fingerprint"] = "0" * 16
    return _realfit_void(root, f, expect_clause="fingerprint")


@case("realfit4096", "completions-out-of-the-sealed-order-are-VOID", "fail")
def _(root):
    def f(art, scores):
        led = art["ledger"]
        i = next(k for k, e in enumerate(led) if e["name"] == "real_model" and e["event"] == "completed")
        j = next(k for k, e in enumerate(led) if e["name"] == "builder_matched" and e["event"] == "completed")
        led[i], led[j] = led[j], led[i]
    return _realfit_void(root, f, expect_clause="sealed order")


@case("realfit4096", "an-arm-scored-twice-is-VOID", "fail")
def _(root):
    def f(art, scores):
        e = next(x for x in art["ledger"] if x["name"] == "real_model" and x["event"] == "completed")
        art["ledger"].append(dict(e))
    return _realfit_void(root, f, expect_clause="ledger completions")


@case("realfit4096", "a-missing-arm-is-VOID", "fail")
def _(root):
    def f(art, scores):
        del art["fits"]["builder_matched"]; del scores["per_example"]["builder_matched"]
        del art["readings"]["builder_matched"]
    return _realfit_void(root, f, expect_clause="builder_matched")


@case("realfit4096", "an-arm-fitted-with-another-recipes-parameters-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["fits"]["real_model"]["params"] = dict(art["fits"]["real_model"]["params"], max_iter=999)
    return _realfit_void(root, f, expect_clause="sealed")


@case("realfit4096", "an-arm-fitted-on-rows-that-are-not-the-sealed-block-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["fits"]["real_model"]["fit_rows_sorted_sha256"] = "0" * 64
    return _realfit_void(root, f, expect_clause="sealed rows")


@case("realfit4096", "a-record-fitted-at-another-thread-count-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["fits"]["real_incumbent"]["environment"] = dict(art["fits"]["real_incumbent"]["environment"], threads=1)
    return _realfit_void(root, f, expect_clause="environment")


@case("realfit4096", "ext_fam-that-does-not-hash-to-the-sealed-fam-array-is-VOID", "fail")
def _(root):
    def f(art, scores):
        scores["ext_fam"] = list(reversed(scores["ext_fam"]))
    return _realfit_void(root, f, expect_clause="ext_fam")


@case("realfit4096", "chunk-ids-that-are-not-the-sealed-expansion-are-VOID", "fail")
def _(root):
    def f(art, scores):
        scores["ext_chunk_ids"] = list(reversed(scores["ext_chunk_ids"]))
    return _realfit_void(root, f, expect_clause="ext_chunk_ids")


@case("realfit4096", "an-absent-scores-file-is-VOID", "fail")
def _(root):
    return _realfit_void(root, None, expect_clause="scores", drop_scores=True)


@case("realfit4096", "an-absent-artifact-emits-no-verdict", "fail")
def _(root):
    rc, out = _realfit(root, drop_artifact=True)
    if rc != 0 and "No verdict emitted" not in out:
        return 0, out + " !! detected but not as an absent artifact"
    return rc, out


@case("realfit4096", "a-NOT-RUN-marker-beside-an-artifact-emits-no-verdict", "fail")
def _(root):
    rc, out = _realfit(root, not_run={"schema": "raise-v1/realfit_4096_rerun_not_run/1", "preregistration": "0021-realfit-4096-rerun",
                                      "stage": "run", "reason": "the null control leaked", "utc": "2026-09-16T05:00:00Z",
                                      "n_checkpoints": 2})
    if rc != 0 and "NOT RUN" not in out:
        return 0, out + " !! detected but not as NOT RUN"
    return rc, out


@case("realfit4096", "an-artifact-whose-fits-block-is-a-list-is-VOID-not-a-traceback", "fail")
def _(root):
    def f(art, scores):
        art["fits"] = [art["fits"][k] for k in art["fits"]]
    return _realfit_void(root, f)


@case("realfit4096", "an-incomplete-run-is-VOID", "fail")
def _(root):
    def f(art, scores):
        art["complete"] = False; art["run_finished_utc"] = None
    return _realfit_void(root, f, expect_clause="complete")


@case("realfit4096", "the-fit-corpus-row-counts-per-family-must-be-the-sealed-ones", "fail")
def _(root):
    def f(art, scores):
        fam = _rf_reader().FIT_FAMILIES[0]
        art["fit_rows_per_family"] = dict(art["fit_rows_per_family"])
        art["fit_rows_per_family"][fam] += 1
    return _realfit_void(root, f, expect_clause="fit row counts")


@case("realfit4096", "a-fit-corpus-chunk-count-that-is-not-the-measured-one-is-VOID", "fail")
def _(root):
    # The 0020 pre-freeze review's headline defect: the reader sealed the corpus manifest's SELECTED chunk count
    # (1035) where the runner measures the chunks that carry rows (1029). No case covered any fit_corpus field
    # except arrays, so 33/33 was green while the reader could not read the run.
    def m(a, s):
        a["fit_corpus"]["n_chunks"] = a["fit_corpus"]["n_chunks"] + 6
    return _realfit_void(root, m, expect_clause="fit_corpus.n_chunks")


@case("realfit4096", "a-fit-corpus-chunk-id-max-that-is-not-the-measured-one-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fit_corpus"]["chunk_id_max"] = 20400000     # base + 4*stride, the value the reader wrongly carried
    return _realfit_void(root, m, expect_clause="fit_corpus.chunk_id_max")


@case("realfit4096", "a-fit-corpus-per-family-chunk-count-that-is-not-the-measured-one-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fit_corpus"]["chunks_per_family"]["pe_bin"] += 4
    return _realfit_void(root, m, expect_clause="fit_corpus.chunks_per_family")


@case("realfit4096", "a-fit-corpus-label-histogram-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fit_corpus"]["label_histogram"] = list(a["fit_corpus"]["label_histogram"])
        a["fit_corpus"]["label_histogram"][0] += 1
    return _realfit_void(root, m, expect_clause="fit_corpus.label_histogram")


@case("realfit4096", "an-artifact-with-no-ledger-is-VOID", "fail")
def _(root):
    # The runner did not bank one at all until the pre-freeze review; the reader requires exactly one completion
    # per arm, so an honest run read VOID on eleven clauses. Nothing tested that the key was present.
    def m(a, s):
        del a["ledger"]
    return _realfit_void(root, m, expect_clause="ledger completions")


@case("realfit4096", "a-null-control-whose-labels-are-not-a-permutation-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["null_labels_same_multiset"] = False
    return _realfit_void(root, m, expect_clause="null")


@case("realfit4096", "a-repro-block-collision-count-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    # 0020 required zero here and refused at launch on the builder's own duplicate chunks. 0021 seals the measured
    # count instead, so BOTH directions must void: more rows means new content crossed, fewer means these are not
    # the sealed blocks.
    r20 = _rf_reader()

    def m(a, s):
        a["partition"]["repro_rows_identical_to_a_scored_row"] = r20.EXPECTED_COLLISIONS["repro_block"] + 1
    return _realfit_void(root, m, expect_clause="repro_block")


@case("realfit4096", "a-repro-block-collision-count-of-zero-is-VOID-not-a-pass", "fail")
def _(root):
    def m(a, s):
        a["partition"]["repro_rows_identical_to_a_scored_row"] = 0
    return _realfit_void(root, m, expect_clause="repro_block")


@case("realfit4096", "a-matched-block-collision-count-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    r20 = _rf_reader()

    def m(a, s):
        a["partition"]["matched_rows_identical_to_a_scored_row"] = r20.EXPECTED_COLLISIONS["matched_block"] + 3
    return _realfit_void(root, m, expect_clause="matched_block")


@case("realfit4096", "the-right-number-of-colliding-rows-but-the-wrong-rows-is-VOID", "fail")
def _(root):
    # The bar says "the collisions are the measured ones". A tally of 8 passes on any 8 rows; the sealed row-identity
    # hash does not (0021 pre-freeze review, condition lens, finding M2).
    def m(a, s):
        a["partition"]["repro_collision_row_sha256"] = "0" * 64
    return _realfit_void(root, m, expect_clause="colliding rows of the repro_block")


@case("realfit4096", "a-new-colliding-row-beyond-the-repro-block-is-VOID", "fail")
def _(root):
    # 18 of the 26 colliding pool rows sit past the reproduction block's first 100000 rows, where no block count
    # would see a new one. The pool-wide count and hash close that (finding M3).
    r20 = _rf_reader()

    def m(a, s):
        a["partition"]["pool_rows_identical_to_a_scored_row"] = r20.POOL_ROWS_IDENTICAL + 1
    return _realfit_void(root, m, expect_clause="pool rows are byte-identical")


@case("realfit4096", "a-builder-cache-feature-hash-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    # The 5.76 GB array nothing hashed before 0021, and the array the collision rule is a statement about (finding H2).
    def m(a, s):
        a["corpus"]["cache_X_sha256"] = "f" * 64
    return _realfit_void(root, m, expect_clause="cache_X_sha256")


@case("realfit4096", "a-chunk-matched-block-collision-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["chunk_matched_rows_identical_to_a_scored_row"] = 1
    return _realfit_void(root, m, expect_clause="chunk_matched_block")


@case("realfit4096", "an-artifact-without-the-sealed-expected-collision-counts-is-VOID", "fail")
def _(root):
    def m(a, s):
        del a["partition"]["expected_rows_identical_to_a_scored_row"]
    return _realfit_void(root, m, expect_clause="sealed expected collision counts")


@case("realfit4096", "one-fit-row-identical-to-a-scored-row-is-still-VOID", "fail")
def _(root):
    # The clause's own corpus: this one stays a blanket zero, because it IS the verdict's integrity.
    def m(a, s):
        a["partition"]["fit_rows_identical_to_a_scored_row"] = 1
    return _realfit_void(root, m, expect_clause="fit_rows_identical_to_a_scored_row")


@case("realfit4096", "a-pool-chunk-shared-with-the-extension-corpus-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["pool_chunks_shared_with_ext"] = 2
    return _realfit_void(root, m, expect_clause="pool_chunks_shared_with_ext")


@case("realfit4096", "an-evaluation-chunk-shared-with-the-extension-corpus-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["eval_chunks_shared_with_ext"] = 1
    return _realfit_void(root, m, expect_clause="eval_chunks_shared_with_ext")


@case("realfit4096", "a-fit-chunk-shared-with-the-builder-cache-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["fit_chunks_shared_with_builder"] = 1
    return _realfit_void(root, m, expect_clause="fit_chunks_shared_with_builder")


@case("realfit4096", "permuted-evaluation-chunk-ids-are-VOID", "fail")
def _(root):
    # Range, distinct count and family mix are permutation-invariant, and fam_e drives every builder-side
    # per-family reading. Before the review this array was bound by none of them.
    def m(a, s):
        s["eval_chunk_ids"] = s["eval_chunk_ids"][26:] + s["eval_chunk_ids"][:26]
    return _realfit_void(root, m, expect_clause="eval_chunk_ids")


@case("realfit4096", "a-banked-top1_non_gutenberg-that-is-not-the-vectors-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["real_model"]["top1_non_gutenberg"] = 0.9999
    return _realfit_void(root, m, expect_clause="top1_non_gutenberg")


@case("realfit4096", "an-arm-outside-the-sealed-order-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["secret_arm"] = dict(a["fits"]["real_model"])
    return _realfit_void(root, m, expect_clause="outside the sealed order")


@case("realfit4096", "a-banked-builder-eval-reading-that-is-not-the-vectors-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["readings"]["real_model"]["builder_eval_top1"] = 0.4242
    return _realfit_void(root, m, expect_clause="builder_eval_top1")


@case("realfit4096", "a-smoke-artifact-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["smoke"] = True; s["smoke"] = True
    return _realfit_void(root, m)


@case("realfit4096", "a-stage-that-is-not-run-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["stage"] = "smoke"
    return _realfit_void(root, m, expect_clause="stage")


@case("realfit4096", "a-floor-arm-missing-from-the-artifact-is-VOID", "fail")
def _(root):
    # Without the floor arms there is no measured floor, so there is no clause: section 4a is not optional.
    def m(a, s):
        del a["fits"]["floor_tree3"]
    return _realfit_void(root, m)


@case("realfit4096", "a-floor-arm-fitted-on-rows-that-are-not-the-fit-block-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["floor_tree3"]["fit_rows_sha256"] = "0" * 64
    return _realfit_void(root, m, expect_clause="floor_tree3")


@case("realfit4096", "a-floor-that-rises-above-the-model-turns-a-pass-into-REAL_FIT_FAILS", "fail")
def _(root):
    # The whole point of 4a: a model that clears chance + the margin but NOT the trivial floor + the margin is a
    # fail. Under the drafted chance-based clause this artifact would have been published as a pass.
    r20 = _rf_reader()
    rc, out = _realfit(root, real_correct=r20.MIN_CORRECT_REAL + 400,
                       acc={"floor_tree3": 0.11, "floor_feat1": 0.09})
    if rc != 0 and "verdict=REAL_FIT_FAILS" not in out:
        return 0, out + " !! a model beaten by a depth-3 tree was not read as REAL_FIT_FAILS"
    return rc, out


@case("realfit4096", "the-floor-is-the-maximum-of-the-four-trivial-arms-not-the-first", "fail")
def _(root):
    # If the reader took any arm but the maximum, this control (where floor_feat1 leads) would clear.
    r20 = _rf_reader()
    rc, out = _realfit(root, real_correct=r20.MIN_CORRECT_REAL + 900, acc={"floor_feat1": 0.10})
    if rc != 0 and "verdict=REAL_FIT_FAILS" not in out:
        return 0, out + " !! the floor was not the maximum over the four trivial arms"
    return rc, out


@case("realfit4096", "the-readers-record-requirements-hold-against-the-runners-own-banked-values", "pass")
def _(root):
    # Key sets are not enough. The reader demanded an integer fit_info.n_iter from all eleven arms; the runner banks
    # {} for the two dummy baselines and {depth, n_leaves} for the two tree baselines, so an honest run voided on
    # four clauses while the gate stayed green - because the control overwrote fit_info with {"n_iter": 100}. This
    # case checks the reader's per-record requirements against the FIXTURE's own values (0021 pre-freeze review,
    # instrument lens, finding H3).
    r20 = _rf_reader()
    shape = json.load(open(_RF_SHAPE, encoding="utf-8"))["artifact"]
    problems = []
    is_int = lambda v: isinstance(v, int) and not isinstance(v, bool)  # noqa: E731
    for nm in r20.ORDER:
        rec = shape["fits"].get(nm)
        if not isinstance(rec, dict):
            problems.append(f"{nm}: the runner banked no record"); continue
        fam = r20.RECIPES[r20.RECIPE_OF[nm]]["family"]
        info = rec.get("fit_info")
        if not isinstance(info, dict):
            problems.append(f"{nm}: fit_info is {info!r}")
        elif fam in ("hgb", "logistic"):
            if not is_int(info.get("n_iter")):
                problems.append(f"{nm} ({fam}): the reader wants an integer n_iter, the runner banked {info!r}")
        elif fam == "tree":
            if not (is_int(info.get("depth")) and is_int(info.get("n_leaves"))):
                problems.append(f"{nm} ({fam}): the reader wants integer depth and n_leaves, the runner banked {info!r}")
        elif fam == "dummy" and info:
            problems.append(f"{nm} (dummy): the runner banked {info!r}; sklearn's DummyClassifier exposes nothing")
        if not isinstance(rec.get("block_refills"), list):
            problems.append(f"{nm}: block_refills is {rec.get('block_refills')!r}")
        missing = sorted({"threads", "nice", "sklearn", "numpy", "python"} - set(rec.get("environment") or {}))
        if missing:
            problems.append(f"{nm}: the runner's record environment lacks {missing}")
    if problems:
        return 1, "; ".join(problems[:4])
    fams = sorted({r20.RECIPES[r20.RECIPE_OF[n]]["family"] for n in r20.ORDER})
    return 0, (f"the reader's per-record requirements hold against the runner's own banked values for all "
               f"{len(r20.ORDER)} arms across {len(fams)} estimator families ({', '.join(fams)})")


@case("realfit4096", "a-floor-arm-banking-an-iteration-count-it-cannot-have-is-VOID", "fail")
def _(root):
    # The converse: a dummy baseline that reports an n_iter is not this run's estimator.
    def m(a, s):
        a["fits"]["floor_tree3"]["fit_info"] = {"n_iter": 100}
    return _realfit_void(root, m, expect_clause="floor_tree3")


@case("realfit4096", "the-control-artifact-is-built-from-the-runners-own-output-shape", "pass")
def _(root):
    # docs/OPERATING_RULES.md section 4: the control must not be built from the reader's expectations. This case fails
    # if the fixture stops being a runner output - if the runner grows or drops a key the control would not carry it.
    # SYMMETRIC and RECURSIVE. The previous version computed only `set(shape) - set(art)` at the top level, so an
    # invented key (the control injected a `ledger` the runner never wrote) and a nested divergence (four fit_corpus
    # values, plus a ceiling key) were both invisible, and the fixture was itself two partition keys stale. Both
    # directions, at every level the reader compares, is the whole point of the rule.
    shape = json.load(open(_RF_SHAPE, encoding="utf-8"))["artifact"]
    art, _ = _good_realfit()
    r20 = _rf_reader()
    problems = []
    sym = sorted(set(shape) ^ set(art))
    if sym:
        problems.append(f"top-level key sets differ: reader-side-only {sorted(set(art) - set(shape))}, "
                        f"runner-only {sorted(set(shape) - set(art))}")
    for blk in ("corpus", "ext_corpus", "fit_corpus", "partition", "readings"):
        d = sorted(set(shape[blk]) ^ set(art[blk]))
        if d:
            problems.append(f"{blk}: key sets differ {d}")
    # the reader's own expectations must be writable by the runner: every key it compares must be a key in the fixture
    for name, sealed, blk in (("EXT", r20.EXT, "ext_corpus"), ("FIT", r20.FIT, "fit_corpus"),
                              ("PARTITION", r20.PARTITION, "partition"), ("CORPUS", r20.CORPUS, "corpus")):
        unwritten = sorted(set(sealed) - set(shape[blk]))
        if unwritten:
            problems.append(f"the reader's {name} expects keys the runner never writes: {unwritten}")
    if sorted(set(shape["fits"]) ^ set(art["fits"])):
        problems.append(f"arms differ: {sorted(set(shape['fits']) ^ set(art['fits']))}")
    else:
        for nm in sorted(art["fits"]):
            d = sorted(set(shape["fits"][nm]) ^ set(art["fits"][nm]))
            if d:
                problems.append(f"record {nm}: field sets differ {d}")
    if problems:
        return 1, "; ".join(problems[:4])
    return 0, (f"control and fixture agree both ways on {len(shape)} artifact keys, {len(art['fits'])} arms, "
               f"{len(art['fits']['real_model'])} record fields and the corpus/partition/readings nesting; "
               f"every reader expectation is a key the runner writes")


# ---------------------------------------------------------------- section 4 provenance for the five earlier readers
#
# One pass/fail pair per gate. The pass case fails if the control and the banked runner artifact disagree in EITHER
# direction at ANY level a reader compares (top level, every block, every fit record), or if a reader seals a key the
# runner never writes. The fail case rebuilds the control the way every one of these gates built it until 2026-09-17 -
# partition = dict(<reader>.PARTITION) - and requires that the same check refuses it. (CORRECTIONS.md 2026-09-17.)


def _recipe_reader(cfg):
    import importlib.util
    spec = importlib.util.spec_from_file_location("rr", os.path.join(REPO, "tools", "readers", cfg["reader"]))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _prov_recipe(cfg, art):
    shape = _banked_shape(cfg["gate"]); r = _recipe_reader(cfg)
    blocks = [("partition", art["partition"], shape["partition"]), ("corpus", art["corpus"], shape["corpus"]),
              ("selection", art["selection"], shape["selection"]),
              ("selection.partition", art["selection"]["partition"], shape["selection"]["partition"]),
              ("final (arms)", art["final"], shape["final"])]
    records = [(f"final.{h}", art["final"][h], shape["final"][h]) for h in art["final"] if h in shape["final"]]
    records += [(k, art[k], shape[k]) for k in ("incumbent_refit", "logistic_l1_refit", "null_control")]
    for hid, h in art["selection"]["selection"].items():
        for st in h["stages"]:
            records += [(f"selection.{hid}.{st['stage']}.{rc['id']}", rc, shape["final"][hid]) for rc in st["records"]]
    return _shape_problems(art, shape, blocks, records,
                           [("PARTITION", r.PARTITION, shape["partition"]), ("CORPUS", r.CORPUS, shape["corpus"])])


def _prov_lofo_like(gate, r, art):
    """0015's and 0017's artifacts: eight folds of records, reproduction arms, a null control, a lofo block per role."""
    shape = _banked_shape(gate)
    blocks = [("partition", art["partition"], shape["partition"]), ("corpus", art["corpus"], shape["corpus"]),
              ("folds (families)", art["folds"], shape["folds"]),
              ("reproduction (arms)", art["reproduction"], shape["reproduction"]), ("lofo (roles)", art["lofo"], shape["lofo"])]
    blocks += [(f"lofo.{role}", art["lofo"][role], shape["lofo"][role]) for role in art["lofo"] if role in shape["lofo"]]
    if "folds" in art["partition"]:
        blocks.append(("partition.folds (families)", art["partition"]["folds"], shape["partition"]["folds"]))
        blocks += [(f"partition.folds.{f}", art["partition"]["folds"][f], shape["partition"]["folds"][f])
                   for f in art["partition"]["folds"] if f in shape["partition"]["folds"]]
    records = [(f"folds.{f}.{role}", art["folds"][f][role], shape["folds"][f][role])
               for f in art["folds"] if f in shape["folds"] for role in art["folds"][f] if role in shape["folds"][f]]
    records += [(f"reproduction.{k}", art["reproduction"][k], shape["reproduction"][k]) for k in art["reproduction"] if k in shape["reproduction"]]
    records.append(("null_control", art["null_control"], shape["null_control"]))
    return _shape_problems(art, shape, blocks, records,
                           [("PARTITION", r.PARTITION, shape["partition"]), ("CORPUS", r.CORPUS, shape["corpus"])])


def _prov_fdc(art):
    shape = _banked_shape("fdc4096"); r = _fdc_reader()
    blocks = [("partition", art["partition"], shape["partition"]), ("corpus", art["corpus"], shape["corpus"]),
              ("folds (families)", art["folds"], shape["folds"]),
              ("reproduction (arms)", art["reproduction"], shape["reproduction"]), ("fdc (roles)", art["fdc"], shape["fdc"])]
    blocks += [(f"fdc.{role}", art["fdc"][role], shape["fdc"][role]) for role in art["fdc"] if role in shape["fdc"]]
    P, S = art["partition"], shape["partition"]
    if "folds" in P:
        blocks.append(("partition.folds (families)", P["folds"], S["folds"]))
        for f in P["folds"]:
            if f not in S["folds"]:
                continue
            a, b = P["folds"][f], S["folds"][f]
            blocks.append((f"partition.folds.{f}", a, b))
            for sec in ("by_k", "depth"):
                if sec in a and sec in b:
                    blocks.append((f"partition.folds.{f}.{sec} (sizes)", a[sec], b[sec]))
                    blocks += [(f"partition.folds.{f}.{sec}.{k}", a[sec][k], b[sec][k]) for k in a[sec] if k in b[sec]]
            if "pred_k1" in a and "pred_k1" in b:
                blocks.append((f"partition.folds.{f}.pred_k1", a["pred_k1"], b["pred_k1"]))
    records = []
    for f in art["folds"]:
        if f not in shape["folds"]:
            continue
        a, b = art["folds"][f], shape["folds"][f]
        blocks.append((f"folds.{f} (sections)", a, b))
        for sec in ("by_k", "depth"):
            blocks.append((f"folds.{f}.{sec} (sizes)", a[sec], b[sec]))
            for k in a[sec]:
                if k not in b[sec]:
                    continue
                blocks.append((f"folds.{f}.{sec}.{k} (roles)", a[sec][k], b[sec][k]))
                records += [(f"folds.{f}.{sec}.{k}.{role}", a[sec][k][role], b[sec][k][role]) for role in a[sec][k] if role in b[sec][k]]
        blocks.append((f"folds.{f}.pred_k1 (roles)", a["pred_k1"], b["pred_k1"]))
        records += [(f"folds.{f}.pred_k1.{role}", a["pred_k1"][role], b["pred_k1"][role]) for role in a["pred_k1"] if role in b["pred_k1"]]
    records += [(f"reproduction.{k}", art["reproduction"][k], shape["reproduction"][k]) for k in art["reproduction"] if k in shape["reproduction"]]
    records.append(("null_control", art["null_control"], shape["null_control"]))
    return _shape_problems(art, shape, blocks, records,
                           [("PARTITION", r.PARTITION, shape["partition"]), ("CORPUS", r.CORPUS, shape["corpus"])])


def _prov_oob(art, reader="oob4096_verdict.py"):
    shape = _banked_shape("oob4096"); r = _oob_reader(reader)
    blocks = [("partition", art["partition"], shape["partition"]), ("corpus", art["corpus"], shape["corpus"]),
              ("ext_corpus", art["ext_corpus"], shape["ext_corpus"]), ("fits (arms)", art["fits"], shape["fits"]),
              ("readings (arms)", art["readings"], shape["readings"])]
    blocks += [(f"readings.{a}", art["readings"][a], shape["readings"][a]) for a in art["readings"] if a in shape["readings"]]
    records = [(f"fits.{a}", art["fits"][a], shape["fits"][a]) for a in art["fits"] if a in shape["fits"]]
    return _shape_problems(art, shape, blocks, records,
                           [("PARTITION", r.PARTITION, shape["partition"]), ("CORPUS", r.CORPUS, shape["corpus"]),
                            ("EXT", r.EXT, shape["ext_corpus"])])


def _register_provenance(gate, build, prov, reader_partition):
    @case(gate, "the-control-artifact-is-built-from-the-banked-runner-output-shape", "pass")
    def _(root):
        problems = prov(build())
        if problems:
            return 1, "; ".join(problems[:4])
        return 0, (f"control and {_BANKED_SHAPE[gate]} agree both ways at the top level, in every block and in every "
                   f"fit record; every key the reader seals is one the runner writes")

    @case(gate, "a-control-whose-partition-is-the-readers-own-literals-is-detected", "fail")
    def _(root):
        art = build(); art["partition"] = dict(reader_partition())   # the construction until 2026-09-17
        problems = prov(art)
        if not problems:
            return 0, "!! a partition taken from the reader's literals was not detected"
        return 1, problems[0]


_register_provenance("recipe2048", lambda: _good_recipe2048(_CFG2048)[0], lambda a: _prov_recipe(_CFG2048, a),
                     lambda: _recipe_reader(_CFG2048).PARTITION)
_register_provenance("recipe4096", lambda: _good_recipe2048(_CFG4096)[0], lambda a: _prov_recipe(_CFG4096, a),
                     lambda: _recipe_reader(_CFG4096).PARTITION)
_register_provenance("lofo4096", lambda: _good_lofo()[0], lambda a: _prov_lofo_like("lofo4096", _lofo_reader(), a),
                     lambda: _lofo_reader().PARTITION)
_register_provenance("fdc4096", lambda: _good_fdc()[0], _prov_fdc, lambda: _fdc_reader().PARTITION)
_register_provenance("lofol3", lambda: _good_lofol3()[0], lambda a: _prov_lofo_like("lofol3", _lofol3_reader(), a),
                     lambda: _lofol3_reader().PARTITION)
_register_provenance("oob4096", lambda: _good_oob()[0], _prov_oob, lambda: _oob_reader().PARTITION)


# ---------------------------------------------------------------- realsearch4096 gate (0022)
#
# The 0022 reader reads a symmetric recipe search run INSIDE 0021's real fit block: a selection file (one stage per
# searched head on a chunk-rule holdout), a confirmatory artifact (reproduction arms, a null control, six baseline
# heads and the model, each fitted once on the whole fit block and scored once on 0018's scoring set), and the scores
# file. The control below takes its SHAPE - every key, nesting and record field - from tests/fixtures/
# realsearch_runner_shape.json, a smoke run of tools/pivot/run_realsearch.py itself, and its VALUES from the reader's
# sealed literals (docs/OPERATING_RULES.md section 4; CORRECTIONS.md 2026-09-16 and 2026-09-17). Every case then
# breaks one thing and must be read as VOID or REAL_RECIPE_FAILS.

_RS_SHAPE = os.path.join(REPO, "tests", "fixtures", "realsearch_runner_shape.json")


def _rs_reader():
    import importlib.util
    spec = importlib.util.spec_from_file_location("r22", os.path.join(REPO, "tools", "readers", "realsearch4096_verdict.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _rs_readings(r22, v, fam_x, fam_e):
    """The runner's readings() over one per-example vector, recomputed here from the same rule (0021's shape)."""
    n_eval, n_ext = r22.PARTITION["n_eval_rows"], r22.N_EXT
    rep, ex = v[:n_eval], v[n_eval:]
    by = {f: [] for f in r22.EXT_FAMILIES}
    for i in range(n_ext):
        by[fam_x[i]].append(ex[i])
    m4 = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
    real = [x for f in r22.REAL_FAMILIES for x in by[f]]; synth = [x for f in r22.SYNTH_FAMILIES for x in by[f]]
    return {"builder_eval_top1": m4(rep), "builder_eval_correct": sum(rep), "ext_top1": m4(ex), "ext_correct": sum(ex),
            "n_ext_rows": n_ext, "ext_per_family": {f: m4(by[f]) for f in r22.EXT_FAMILIES},
            "ext_per_family_correct": {f: sum(by[f]) for f in r22.EXT_FAMILIES},
            "ext_structured_text_top1": m4([x for f in r22.STRUCTURED_TEXT for x in by[f]]),
            "ext_high_entropy_top1": m4([x for f in r22.HIGH_ENTROPY for x in by[f]]),
            "ext_real_top1": m4(real), "ext_real_correct": sum(real), "n_ext_real_rows": len(real),
            "ext_synthetic_correct": sum(synth), "ext_synthetic_top1": m4(synth),
            "builder_eval_per_family": {f: m4([rep[i] for i in range(n_eval) if fam_e[i] == f]) for f in r22.FAMILIES}}


# The selection scores that decide each head's winner in the control: M3, L4, D2 and T3, none of them a reference
# recipe, so all four reproduction arms are fitted. A head that selects its REFERENCE recipe (M1 or M4, L3, D1) makes
# that arm an alias of its own confirmatory fit, and a deterministic refit of the same recipe on the same rows reads
# what 0021 read - so a model head that selects M4 is pinned to 0021's 0.1193 and cannot clear, which the reader
# enforces through the reproduction clause (the first version of this control selected M4 and read 0.20: VOID, drift
# 0.0807). Ties are avoided so the rule's winner is unambiguous.
_RS_SEL_SCORES = {"model": {"M1": 0.12, "M2": 0.125, "M3": 0.14, "M4": 0.13, "M5": 0.11, "M6": 0.12, "M7": 0.115, "M8": 0.13},
                  "logistic": {"L1": 0.10, "L2": 0.105, "L3": 0.125, "L4": 0.13, "L5": 0.09, "L6": 0.12, "L7": 0.126, "L8": 0.128},
                  "depth3_tree": {"D1": 0.088, "D2": 0.09, "D3": 0.087, "D4": 0.086, "D5": 0.089, "D6": 0.0885, "D7": 0.088, "D8": 0.085},
                  "deep_tree": {"T1": 0.10, "T2": 0.11, "T3": 0.118, "T4": 0.112, "T5": 0.115, "T6": 0.105, "T7": 0.108, "T8": 0.117}}


def _good_realsearch(model_real_correct=None, head_real=None, repro=None, null_acc=None, sel_scores=None,
                     sel_status=None, sel_mutate=None):
    """A complete, valid 0022 artifact set (artifact, selection bytes, scores). Shape AND key sets from the runner's own
    smoke output (tests/fixtures/realsearch_runner_shape.json); only the values are the sealed run's.

    Defaults give REAL_RECIPE_CLEARS: the model head selects M3 and reads 0.20 on the real-family rows against a searched logistic at 0.13
    (the binding bar on both readings; deep_tree 0.12, depth3 0.10, best_single_feat 0.06, majority and stratified at
    their 0021 floors), and every reproduction arm reads exactly its 0021 reference. head_real overrides a head's
    real-family accuracy; model_real_correct sets the model's correct real-family rows exactly; repro overrides a
    reproduction arm's reading (an aliased arm's is its head's); null_acc the null's; sel_scores the selection stage's
    holdout scores by head and candidate; sel_status a (head, candidate) -> status override; sel_mutate a function of the
    selection document applied BEFORE the file is hashed, so the ledger and the fingerprints bind to the mutated file
    exactly as a runner that read it would have."""
    r22 = _rs_reader(); shape = json.load(open(_RS_SHAPE, encoding="utf-8"))
    S_art, S_sel = shape["artifact"], shape["selection"]
    zeros = {k: 0 for k in ("pool_chunks_shared_with_ext", "eval_chunks_shared_with_ext", "fit_chunks_shared_with_ext",
                            "fit_chunks_shared_with_builder", "fit_source_chunks_shared_with_ext", "fit_rows_identical_to_a_scored_row",
                            "n_chunks_holdout_and_fitpool", "n_holdout_rows_in_fitpool")}
    nulls = {"null_y_shuffled_sha256": r22.NULL_SHA_EXPECTED, "null_labels_permuted": True, "null_labels_same_multiset": True}
    part = _rf_sub(S_art["partition"], dict(r22.PARTITION, **zeros, **nulls), "partition", sealed_may_be_subset=True)
    sel_part = {k: v for k, v in part.items() if k not in ("eval_y_sha256", *nulls)}
    # the roster's key set is the runner's (strict, both ways, in both files); its values are the sealed ones, deep-copied
    roster = _rf_sub(S_art["roster"], json.loads(json.dumps({"protocol": r22.PROTOCOL, "heads": r22.HEADS})), "roster")
    _rf_sub(S_sel["roster"], roster, "selection.roster")
    assert _sha12(roster) == r22.ROSTER_SHA256, "the reader's roster literals do not hash to its ROSTER_SHA256"
    by_id = {c["id"]: c for h in r22.HEADS for c in h["candidates"]}
    n_eval, n_ext, n_real = r22.PARTITION["n_eval_rows"], r22.N_EXT, r22.N_REAL
    fams = list(r22.EXT_FAMILIES); rpf = r22.EXT["rows_per_family"]
    fam_idx = []
    for k, f in enumerate(fams):
        fam_idx += [k] * rpf[f]
    fam_x = [fams[i] for i in fam_idx]
    ext_ids = [c for c, n in zip(r22.EXT_CHUNK_IDS, r22.EXT_ROWS_PER_CHUNK) for _ in range(n)]
    eval_ids = [c for c, n in zip(r22.EVAL_CHUNK_IDS, r22.EVAL_ROWS_PER_CHUNK) for _ in range(n)]
    fam_e = [r22.FAMILIES[c % 8] for c in eval_ids]
    env = dict(shape["artifact"]["environment"], threads=3, nice=10)
    real = set(r22.REAL_FAMILIES)
    # ---- selection
    scores_sel = {h: dict(v) for h, v in _RS_SEL_SCORES.items()}
    for h, v in (sel_scores or {}).items():
        scores_sel[h].update(v)
    st_rows, st_idx, st_sorted = part["stage_rows"][0], part["stage_idx_sha256"][0], part["stage_sorted_sha256"][0]
    tmpl_sel = S_sel["selection"]["model"]["stages"][0]["records"][0]      # the runner's selection record shape

    def sel_record(hid, c):
        sc = scores_sel[hid][c["id"]]
        status = (sel_status or {}).get((hid, c["id"]), "fit")
        sealed = {"id": c["id"], "head": hid, "family": c["family"], "params": dict(c.get("params", {})),
                  "scaled": bool(c.get("scaled", False)), "val": c.get("val"), "seed": r22.SEED, "params_sha256": _sha12(c),
                  "stage": "selection-1", "n_fit_rows": st_rows, "fit_rows_sha256": st_idx, "fit_rows_sorted_sha256": st_sorted,
                  "environment": dict(env), "interruptions_before_this_fit": 0, "status": status, "seconds": 1.0,
                  "top1": sc, "top1_non_gutenberg": sc, "per_family": {f: sc for f in r22.FIT_FAMILIES}}
        rec = _rf_sub(tmpl_sel, sealed, f"selection record {hid}/{c['id']}", sealed_may_be_subset=True)
        if status != "fit":
            rec.update({"top1": None, "top1_non_gutenberg": None, "per_family": None, "seconds": None,
                        "evidence": "killed with anonymous RSS 13.2 GB at the last heartbeat, at or above the preregistered 13.0 GB"})
        return rec

    selection, selected = {}, {}
    for h in r22.HEADS:
        hid = h["id"]
        if len(h["candidates"]) == 1:
            selection[hid] = {"side": h["side"], "stages": [], "selected_id": h["candidates"][0]["id"]}
        else:
            recs = [sel_record(hid, c) for c in h["candidates"]]
            pool = [r for r in recs if r["status"] == "fit"]
            ranked = []
            while pool:
                best = max(pool, key=lambda r: (r["top1"], -[x["id"] for x in recs].index(r["id"])))
                ranked.append(best["id"]); pool = [r for r in pool if r is not best]
            selection[hid] = {"side": h["side"], "selected_id": ranked[0] if ranked else None,
                              "stages": [{"stage": 1, "n_fit_rows": st_rows, "fit_rows_sha256": st_idx, "records": recs,
                                          "eligible_ranked_ids": ranked, "advanced_ids": ranked[:1]}]}
        selected[hid] = selection[hid]["selected_id"]
    sel_ledger = []
    for h in r22.HEADS:
        for c in h["candidates"] if len(h["candidates"]) > 1 else []:
            nm = f"sel1_{h['id']}_{c['id']}"
            sel_ledger += [{"name": nm, "fingerprint": nm, "event": "started", "utc": "2026-09-18T00:00:00Z", "rss_gb": 1.0, "pid": 1, "attempt": 1},
                           {"name": nm, "fingerprint": nm, "event": "completed", "utc": "2026-09-18T00:00:30Z", "rss_gb": 1.0, "pid": 1, "seconds": 1.0}]
    sel_secs = {hid: round(sum((r.get("seconds") or 0) for s in e["stages"] for r in s["records"]), 1) for hid, e in selection.items()}
    sel_doc = _shape_fill(S_sel, {
        "schema_version": 1, "schema": "raise-v1/realsearch_4096/1", "preregistration": r22.PREREG, "smoke": False,
        "roster_sha256": r22.ROSTER_SHA256, "roster": roster, "corpus": dict(r22.CORPUS), "ext_corpus": dict(r22.EXT),
        "fit_corpus": dict(r22.FIT), "partition": sel_part, "n_classes": 26, "class_names": [], "chance_accuracy": r22.CHANCE,
        "stage": "select",
        "gathers": [{"name": "holdout", "source": "fit_corpus", "n_rows": part["n_holdout_rows"], "idx_sha256": part["holdout_idx_sha256"],
                     "n_rows_identical_to_a_scored_row": 0},
                    {"name": "stage1", "source": "fit_corpus", "n_rows": st_rows, "idx_sha256": st_idx, "n_rows_identical_to_a_scored_row": 0}],
        "scored_rows_gathered_in_selection": 0, "environment": dict(env),
        "launch_environment": {"env": dict(env), "loadavg_1_5_15": [0.1, 0.1, 0.1], "problems": [], "ok": True}, "launch_number": 1,
        "selection": selection, "selected_ids": selected, "ledger": sel_ledger,
        "cost": {"selection_seconds_by_head": sel_secs, "selection_seconds_total": round(sum(sel_secs.values()), 1),
                 "wall_seconds_this_invocation": 100.0, "interruptions_by_head": {hid: 0 for hid in selection}},
        "selection_started_utc": "2026-09-18T00:00:00Z", "selection_finished_utc": "2026-09-18T01:00:00Z"}, "selection")
    if sel_mutate:
        sel_mutate(sel_doc)
    sel_bytes = _canon12(sel_doc).encode("utf-8"); sel_sha = hashlib.sha256(sel_bytes).hexdigest()
    # ---- confirmatory
    aliased = {arm: hid for arm, (hid, ref) in r22.REPRO_ARMS.items() if selected.get(hid) == ref}
    roles = [n for n in r22.CONFIRM_ORDER if n not in aliased]
    acc_real = dict({"majority": r22.FLOORS["majority"], "stratified": r22.FLOORS["stratified"], "best_single_feat": 0.06,
                     "depth3_tree": 0.10, "deep_tree": 0.12, "logistic": 0.13, "model": 0.20, "null": 0.037}, **(head_real or {}))
    for arm in r22.REPRO_ARMS:
        acc_real[arm] = r22.REFERENCE[arm]
    acc_real.update(repro or {})
    if null_acc is not None:
        acc_real["null"] = null_acc
    rep_acc = {n: (0.19 if n not in ("null", "majority", "stratified") else 0.038) for n in roles}

    def vec(name):
        v = [0] * (n_eval + n_ext)
        for i in range(int(round(rep_acc[name] * n_eval))):
            v[i] = 1
        per = {f: int(round(acc_real[name] * rpf[f])) for f in fams}
        if name == "model" and model_real_correct is not None:
            rf = [f for f in fams if f in real]; base, extra = divmod(int(model_real_correct), len(rf))
            for j, f in enumerate(rf):
                per[f] = base + (1 if j < extra else 0)
        pos = n_eval
        for f in fams:
            for i in range(pos, pos + per[f]):
                v[i] = 1
            pos += rpf[f]
        return v

    def cand_of(name):
        if name in r22.REPRO_ARMS:
            return by_id[r22.REPRO_ARMS[name][1]]
        return by_id[selected["model"]] if name == "null" else by_id[selected[name]]

    def stage_of(name):
        return "reproduction" if name in r22.REPRO_ARMS else ("null" if name == "null" else "confirmatory")

    def fp(name):
        return r22.fingerprint(prereg=r22.PREREG, seed=r22.SEED, head=name, cand=cand_of(name), stage=stage_of(name),
                               rows=part["fit_sorted_sha256"], eval=part["eval_idx_sha256"], ext=r22.EXT["arrays"]["X"]["sha256"],
                               fit=r22.FIT["arrays"]["X"]["sha256"], selection=sel_sha)

    tmpl_by_family = {"hgb": "repro_m4", "logistic": "logistic", "tree": "depth3_tree", "dummy": "majority"}

    def record(name, v):
        c = cand_of(name); m4 = lambda xs: round(sum(xs) / len(xs), 4)  # noqa: E731
        fam_s = fam_e + ["ext:" + f for f in fam_x]
        ng = [v[i] for i in range(n_eval) if fam_e[i] != "gutenberg"] + v[n_eval:]
        # fit_info, block_refills and the memory fields are the RUNNER's, from the captured record of the same estimator
        # family (a tree banks depth and leaves, an HGB an iteration count, a dummy nothing) and never overwritten.
        tmpl = S_art["fits"][name] if name in S_art["fits"] else S_art["fits"][tmpl_by_family[c["family"]]]
        sealed = {"id": c["id"], "head": name, "family": c["family"], "params": dict(c.get("params", {})),
                  "scaled": bool(c.get("scaled", False)), "val": c.get("val"), "seed": r22.SEED, "params_sha256": _sha12(c),
                  "stage": stage_of(name), "n_fit_rows": part["fit_rows"], "fit_rows_sha256": part["fit_idx_sha256"],
                  "fit_rows_sorted_sha256": part["fit_sorted_sha256"], "environment": dict(env), "interruptions_before_this_fit": 0,
                  "status": "fit", "top1": m4(v), "top1_non_gutenberg": m4(ng),
                  "per_family": {f: m4([v[i] for i in range(len(v)) if fam_s[i] == f]) for f in sorted(set(fam_s))},
                  "fingerprint": fp(name), "per_example_sha256": hashlib.sha256(bytes(v)).hexdigest()}
        return _rf_sub(tmpl, sealed, f"fits.{name}", sealed_may_be_subset=True)

    per_example, reads, fits = {}, {}, {}
    for name in roles:
        v = vec(name); per_example[name] = v
        reads[name] = _rs_readings(r22, v, fam_x, fam_e)
        fits[name] = record(name, v)
    ledger = list(sel_ledger)
    for i, nm in enumerate(roles):
        ledger += [{"name": f"confirm_{nm}", "fingerprint": fp(nm), "event": "selection_bound", "utc": f"2026-09-18T02:{i:02d}:00Z",
                    "rss_gb": 1.0, "pid": 1, "selection_sha256": sel_sha},
                   {"name": f"confirm_{nm}", "fingerprint": fp(nm), "event": "started", "utc": f"2026-09-18T02:{i:02d}:01Z", "rss_gb": 1.0, "pid": 1, "attempt": 1},
                   {"name": f"confirm_{nm}", "fingerprint": fp(nm), "event": "completed", "utc": f"2026-09-18T02:{i:02d}:30Z", "rss_gb": 1.0, "pid": 1, "seconds": 1.0}]
    per_head_searched = {h: reads[h]["ext_real_top1"] for h in r22.EXPANDED_HEADS}
    per_head = {h: max(per_head_searched[h], r22.FLOORS[h]) for h in r22.EXPANDED_HEADS}

    def best(hs):
        b = max(per_head[h] for h in hs); return b, sorted(h for h in hs if per_head[h] == b)[0]
    bf, bfh = best(r22.FROZEN_HEADS); be, beh = best(r22.EXPANDED_HEADS)
    need = lambda b: int(math.ceil(n_real * (b + r22.MARGIN) - 1e-9))  # noqa: E731
    rm = reads["model"]
    repro_top1 = {arm: reads[aliased.get(arm, arm)]["ext_real_top1"] for arm in r22.REPRO_ARMS}
    art = _shape_fill(S_art, {
        "schema_version": 1, "schema": "raise-v1/realsearch_4096/1", "preregistration": r22.PREREG, "smoke": False,
        "roster_sha256": r22.ROSTER_SHA256, "roster": roster, "corpus": dict(r22.CORPUS), "ext_corpus": dict(r22.EXT),
        "fit_corpus": dict(r22.FIT), "partition": part, "n_classes": 26, "class_names": [], "chance_accuracy": r22.CHANCE,
        "stage": "confirm", "selection_sha256": sel_sha, "selection": sel_doc, "selected_ids": selected,
        "selected_model_id": selected["model"], "aliased_reproductions": aliased, "environment": dict(env),
        "launch_environment": {"env": dict(env), "loadavg_1_5_15": [0.1, 0.1, 0.1], "problems": [], "ok": True}, "launch_number": 1,
        "complete": True, "missing_roles": [], "fits": fits, "readings": reads,
        "ext_real_top1": {n: reads[n]["ext_real_top1"] for n in roles}, "ext_real_correct": {n: reads[n]["ext_real_correct"] for n in roles},
        "ext_top1": {n: reads[n]["ext_top1"] for n in roles}, "ext_correct": {n: reads[n]["ext_correct"] for n in roles},
        "builder_eval_top1": {n: reads[n]["builder_eval_top1"] for n in roles}, "ext_per_family": {n: reads[n]["ext_per_family"] for n in roles},
        "bars": {"per_head": per_head, "per_head_searched": per_head_searched, "floors": dict(r22.FLOORS),
                 "frozen_heads": list(r22.FROZEN_HEADS), "expanded_heads": list(r22.EXPANDED_HEADS),
                 "best_frozen_for_bar": bf, "best_frozen_head": bfh, "best_frozen_searched": per_head_searched[bfh],
                 "best_expanded_for_bar": be, "best_expanded_head": beh, "best_expanded_searched": per_head_searched[beh],
                 "margin": r22.MARGIN, "n_real_rows": n_real, "min_correct_real_frozen": need(bf), "min_correct_real_expanded": need(be)},
        "model_real_top1": rm["ext_real_top1"], "model_real_correct": rm["ext_real_correct"],
        "model_ext_top1": rm["ext_top1"], "model_ext_correct": rm["ext_correct"],
        "n_ext_real_rows": n_real, "n_ext_rows": n_ext, "n_eval_rows": n_eval,
        "ext_real_families": list(r22.REAL_FAMILIES), "ext_synthetic_families": list(r22.SYNTH_FAMILIES),
        "fit_families": list(r22.FIT_FAMILIES), "fit_rows_per_family": r22.FIT["rows_per_family"],
        "reference_top1": dict(r22.REFERENCE), "reproduction_top1": repro_top1,
        "reproduction_drift": {arm: round(repro_top1[arm] - r22.REFERENCE[arm], 6) for arm in r22.REPRO_ARMS},
        "shuffled_label_accuracy_ext": reads["null"]["ext_top1"], "shuffled_label_accuracy_eval": reads["null"]["builder_eval_top1"],
        "null_control": fits["null"], "null_rows": part["fit_rows"],
        "fit_info_by_name": {n: fits[n]["fit_info"] for n in roles}, "ledger": ledger,
        "cluster_ci95_informational": {}, "cost": {},
        "confirmatory_started_utc": "2026-09-18T02:00:00Z", "first_launch_utc": "2026-09-18T00:00:00Z",
        "run_finished_utc": "2026-09-18T03:00:00Z"}, "artifact")
    scores = {"schema": "raise-v1/realsearch_4096_scores/1", "preregistration": r22.PREREG, "smoke": False,
              "n_eval_rows": n_eval, "n_ext_rows": n_ext, "eval_idx_sha256": part["eval_idx_sha256"],
              "eval_chunk_ids": eval_ids, "ext_chunk_ids": ext_ids, "ext_fam": fam_idx, "ext_families": fams,
              "ext_arrays_sha256": {k: v["sha256"] for k, v in r22.EXT["arrays"].items()},
              "fit_arrays_sha256": {k: v["sha256"] for k, v in r22.FIT["arrays"].items()},
              "layout": "each per_example vector is [sealed evaluation rows (n_eval_rows)] + [extension rows (n_ext_rows)]",
              "per_example": per_example}
    return art, sel_bytes, scores


def _realsearch(root, mutate=None, sel_bytes_override=None, drop_artifact=False, drop_scores=False, drop_selection=False,
                not_run=None, **kw):
    art, sel_bytes, scores = _good_realsearch(**kw)
    if mutate:
        r = mutate(art, scores)
        if r is not None:
            art = r
    piv = os.path.join(root, "artifacts", "pivot"); os.makedirs(piv, exist_ok=True)
    if not drop_selection:
        with open(os.path.join(piv, "realsearch_4096_selection.json"), "wb") as fh:
            fh.write(sel_bytes_override if sel_bytes_override is not None else sel_bytes)
    if not drop_scores:
        json.dump(scores, open(os.path.join(piv, "realsearch_4096_scores.json"), "w"))
    if not drop_artifact:
        json.dump(art, open(os.path.join(piv, "realsearch_4096.json"), "w"))
    if not_run is not None:
        json.dump(not_run, open(os.path.join(piv, "realsearch_4096_not_run.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", "realsearch4096_verdict.py"),
                os.path.join(root, "tools", "readers", "realsearch4096_verdict.py"))
    rc, out = run([PY, "tools/readers/realsearch4096_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(piv, "realsearch_4096_verdict.json")))
    ok = v["verdict"] == "REAL_RECIPE_CLEARS"
    return (0 if ok else 1), (f"verdict={v['verdict']} real={v.get('model_real_top1')} correct={v.get('model_real_correct')} "
                              f"validity={v['validity_failed_clauses'][:2]} margin={v['margin_failed_clauses']}")


def _realsearch_void(root, mutate=None, expect_clause=None, **kw):
    rc, out = _realsearch(root, mutate, **kw)
    if rc != 0 and "verdict=VOID" not in out and "No verdict emitted" not in out:
        return 0, out + " !! detected but not as VOID"
    if expect_clause and expect_clause not in out:
        return 0, out + f" !! VOID for another reason than {expect_clause!r}"
    return rc, out


def _rs_need(**kw):
    """The frozen clause's row count for a given control: ceil(N_REAL x (best frozen bar + MARGIN))."""
    art, _, _ = _good_realsearch(**kw)
    return art["bars"]["min_correct_real_frozen"], art["bars"]["min_correct_real_expanded"]


@case("realsearch4096", "control-searched-model-clears-both-bars-on-the-real-families", "pass")
def _(root):
    return _realsearch(root)


@case("realsearch4096", "one-real-family-row-under-the-frozen-bar-is-REAL_RECIPE_FAILS", "fail")
def _(root):
    nf, ne = _rs_need()
    rc, out = _realsearch(root, model_real_correct=nf - 1)
    if rc != 0 and "verdict=REAL_RECIPE_FAILS" not in out:
        return 0, out + " !! detected but not as REAL_RECIPE_FAILS"
    return rc, out


@case("realsearch4096", "exactly-min-correct-real-rows-clears", "pass")
def _(root):
    nf, ne = _rs_need()
    return _realsearch(root, model_real_correct=max(nf, ne))


@case("realsearch4096", "a-model-clearing-the-frozen-bar-but-not-the-expanded-bar-is-REAL_RECIPE_FAILS", "fail")
def _(root):
    # the searched deep tree rises to 0.16: the expanded bar is 0.16, the frozen bar stays the logistic's 0.13
    rc, out = _realsearch(root, head_real={"deep_tree": 0.16})
    if rc != 0 and ("verdict=REAL_RECIPE_FAILS" not in out or "margin S" not in out or "margin F" in out):
        return 0, out + " !! expected only the expanded clause to fail"
    return rc, out


@case("realsearch4096", "a-searched-baseline-below-its-0021-floor-cannot-lower-the-bar", "pass")
def _(root):
    # the searched logistic reads 0.10, below 0021's 0.1179: the bar is the floor, and the model at 0.20 still clears
    rc, out = _realsearch(root, head_real={"logistic": 0.10})
    if rc == 0 and "correct=7690" not in out:
        return 1, out
    return rc, out


@case("realsearch4096", "a-banked-bar-that-ignores-the-0021-floor-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["bars"]["per_head"]["logistic"] = 0.10; a["bars"]["best_frozen_for_bar"] = 0.10; a["bars"]["best_expanded_for_bar"] = 0.10
        a["bars"]["min_correct_real_frozen"] = a["bars"]["min_correct_real_expanded"] = 5768
    return _realsearch_void(root, m, expect_clause="bars:", head_real={"logistic": 0.10})


@case("realsearch4096", "a-banked-bar-off-by-0.0001-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["bars"]["best_frozen_for_bar"] = round(a["bars"]["best_frozen_for_bar"] - 0.0001, 4)
    return _realsearch_void(root, m, expect_clause="bars:")


@case("realsearch4096", "a-banked-min-correct-off-by-one-row-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["bars"]["min_correct_real_frozen"] -= 1
    return _realsearch_void(root, m, expect_clause="bars:")


@case("realsearch4096", "the-model-head-selecting-0021s-recipe-reproduces-it-and-cannot-clear", "fail")
def _(root):
    # M4 wins the model head: repro_m4 is aliased to the model's own fit, the model reads 0021's 0.1193, the run is a clean
    # REAL_RECIPE_FAILS (validity empty), not a VOID
    rc, out = _realsearch(root, sel_scores={"model": {"M4": 0.15}}, head_real={"model": 0.1193})
    if rc != 0 and ("verdict=REAL_RECIPE_FAILS" not in out or "validity=[]" not in out):
        return 0, out + " !! expected a clean REAL_RECIPE_FAILS through the aliased reproduction"
    return rc, out


@case("realsearch4096", "the-model-head-selecting-0021s-recipe-and-reading-0.20-is-VOID", "fail")
def _(root):
    # a deterministic refit of M4 on the same rows cannot read 0.20 when 0021 read 0.1193: the aliased reproduction voids it
    return _realsearch_void(root, expect_clause="reproduction: repro_m4", sel_scores={"model": {"M4": 0.15}})


@case("realsearch4096", "an-aliasing-map-that-disagrees-with-the-selected-ids-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["aliased_reproductions"] = {"repro_m4": "model"}
    return _realsearch_void(root, m, expect_clause="reproduction: aliased")


@case("realsearch4096", "a-reproduction-arm-off-by-0.006-is-VOID", "fail")
def _(root):
    r22 = _rs_reader()
    return _realsearch_void(root, expect_clause="reproduction: repro_l3", repro={"repro_l3": round(r22.REFERENCE["repro_l3"] + 0.006, 4)})


@case("realsearch4096", "a-reproduction-drift-inside-the-tolerance-still-clears", "pass")
def _(root):
    r22 = _rs_reader()
    return _realsearch(root, repro={"repro_d1": round(r22.REFERENCE["repro_d1"] - 0.004, 4)})


@case("realsearch4096", "a-leaking-null-control-is-VOID", "fail")
def _(root):
    return _realsearch_void(root, expect_clause="null control", null_acc=0.06)


@case("realsearch4096", "a-null-control-at-0.0484-passes-and-0.0485-is-VOID", "fail")
def _(root):
    rc1, out1 = _realsearch(root, null_acc=0.0484)
    if rc1 != 0:
        return 0, out1 + " !! 0.0484 (chance + 0.01, to 4 decimals) should pass"
    return _realsearch_void(root, expect_clause="null control", null_acc=0.0486)


@case("realsearch4096", "null-labels-that-are-not-0021s-permutation-are-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["null_y_shuffled_sha256"] = "0" * 64
    return _realsearch_void(root, m, expect_clause="null control: the permuted")


@case("realsearch4096", "null-labels-not-a-permutation-are-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["null_labels_same_multiset"] = False
    return _realsearch_void(root, m, expect_clause="null control")


@case("realsearch4096", "a-null-control-not-the-selected-model-recipe-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["null"]["id"] = "M1"
    return _realsearch_void(root, m, expect_clause="fit: null")


@case("realsearch4096", "a-smoke-artifact-is-VOID", "fail")
def _(root):
    return _realsearch_void(root, lambda a, s: a.update(smoke=True), expect_clause="scope: smoke")


@case("realsearch4096", "an-artifact-stamped-with-another-preregistration-is-VOID", "fail")
def _(root):
    return _realsearch_void(root, lambda a, s: a.update(preregistration="0021-realfit-4096-rerun"), expect_clause="scope: prereg")


@case("realsearch4096", "a-select-stage-artifact-is-VOID", "fail")
def _(root):
    return _realsearch_void(root, lambda a, s: a.update(stage="select"), expect_clause="scope: stage")


@case("realsearch4096", "a-fit-row-byte-identical-to-a-scored-row-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["fit_rows_identical_to_a_scored_row"] = 1; a["selection"]["partition"]["fit_rows_identical_to_a_scored_row"] = 1
    return _realsearch_void(root, m, expect_clause="leakage: partition.fit_rows_identical")


@case("realsearch4096", "a-fit-chunk-shared-with-the-evaluation-corpus-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["fit_chunks_shared_with_ext"] = 1; a["selection"]["partition"]["fit_chunks_shared_with_ext"] = 1
    return _realsearch_void(root, m, expect_clause="leakage: partition.fit_chunks_shared_with_ext")


@case("realsearch4096", "a-holdout-row-in-the-fit-pool-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["n_holdout_rows_in_fitpool"] = 1; a["selection"]["partition"]["n_holdout_rows_in_fitpool"] = 1
    return _realsearch_void(root, m, expect_clause="leakage: partition.n_holdout_rows_in_fitpool")


@case("realsearch4096", "a-holdout-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["holdout_idx_sha256"] = "0" * 64
    return _realsearch_void(root, m, expect_clause="sealed set: partition.holdout_idx_sha256")


@case("realsearch4096", "a-stage-block-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["stage_idx_sha256"] = ["0" * 64]
    return _realsearch_void(root, m, expect_clause="sealed set: partition.stage_idx_sha256")


@case("realsearch4096", "a-fit-block-that-is-not-0021s-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["fit_idx_sha256"] = "0" * 64
    return _realsearch_void(root, m, expect_clause="sealed set: partition.fit_idx_sha256")


@case("realsearch4096", "a-fit-corpus-array-hash-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fit_corpus"]["arrays"]["X"]["sha256"] = "0" * 64
    return _realsearch_void(root, m, expect_clause="fit corpus: fit_corpus.arrays")


@case("realsearch4096", "an-evaluation-corpus-array-hash-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["ext_corpus"]["arrays"]["X"]["sha256"] = "0" * 64
    return _realsearch_void(root, m, expect_clause="evaluation corpus: ext_corpus.arrays")


@case("realsearch4096", "a-builder-cache-feature-hash-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["corpus"]["cache_X_sha256"] = "0" * 64
    return _realsearch_void(root, m, expect_clause="scope: corpus.cache_X_sha256")


@case("realsearch4096", "a-fit-corpus-label-histogram-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fit_corpus"]["label_histogram"][0] += 1
    return _realsearch_void(root, m, expect_clause="fit corpus: fit_corpus.label_histogram")


@case("realsearch4096", "a-banked-real-correct-count-off-by-one-row-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["model_real_correct"] += 1
    return _realsearch_void(root, m, expect_clause="readings:")


@case("realsearch4096", "a-banked-per-family-reading-off-by-0.0001-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["readings"]["model"]["ext_per_family"]["py_src"] = round(a["readings"]["model"]["ext_per_family"]["py_src"] + 0.0001, 4)
    return _realsearch_void(root, m, expect_clause="readings: model.ext_per_family")


@case("realsearch4096", "a-record-top1-not-its-vectors-mean-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["model"]["top1"] = round(a["fits"]["model"]["top1"] + 0.0001, 4)
    return _realsearch_void(root, m, expect_clause="fit: model record top1")


@case("realsearch4096", "a-record-per-family-not-its-vectors-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["logistic"]["per_family"]["ext:c_src"] = round(a["fits"]["logistic"]["per_family"]["ext:c_src"] + 0.0001, 4)
    return _realsearch_void(root, m, expect_clause="fit: logistic record per_family")


@case("realsearch4096", "a-per-example-vector-whose-hash-is-not-the-records-is-VOID", "fail")
def _(root):
    def m(a, s):
        v = s["per_example"]["model"]; v[0] = 1 - v[0]
    return _realsearch_void(root, m, expect_clause="fit: model per_example_sha256")


@case("realsearch4096", "a-fingerprint-that-is-not-the-recomputed-one-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["model"]["fingerprint"] = "0" * 16
    return _realsearch_void(root, m, expect_clause="fit: model fingerprint")


@case("realsearch4096", "a-model-fit-that-was-not-the-last-completion-is-VOID", "fail")
def _(root):
    def m(a, s):
        L = a["ledger"]; i = next(k for k, e in enumerate(L) if e["name"] == "confirm_model" and e["event"] == "completed")
        L.append(L.pop(i - 2)); L.append(L.pop(i - 2)); L.append(L.pop(i - 2))   # move the model's three events before the logistic's
        j = next(k for k, e in enumerate(L) if e["name"] == "confirm_logistic" and e["event"] == "selection_bound")
        model = [e for e in L if e["name"] == "confirm_model"]; rest = [e for e in L if e["name"] != "confirm_model"]
        a["ledger"] = rest[:j] + model + rest[j:]
    return _realsearch_void(root, m, expect_clause="order: the model")


@case("realsearch4096", "an-arm-scored-twice-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["ledger"].append(dict(next(e for e in a["ledger"] if e["name"] == "confirm_logistic" and e["event"] == "completed")))
    return _realsearch_void(root, m, expect_clause="fit: logistic has 2 ledger completions")


@case("realsearch4096", "a-missing-role-is-VOID", "fail")
def _(root):
    def m(a, s):
        del a["fits"]["deep_tree"]
    return _realsearch_void(root, m, expect_clause="fit: the artifact banks roles outside")


@case("realsearch4096", "a-role-outside-the-sealed-order-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["extra"] = dict(a["fits"]["model"])
    return _realsearch_void(root, m, expect_clause="fit: the artifact banks roles outside")


@case("realsearch4096", "a-record-of-an-aliased-reproduction-arm-is-VOID", "fail")
def _(root):
    # M4 wins: repro_m4 must be aliased; an artifact that ALSO banks a repro_m4 record is scoring a recipe twice
    def m(a, s):
        a["fits"]["repro_m4"] = dict(a["fits"]["model"], head="repro_m4")
    return _realsearch_void(root, m, expect_clause="fit: the artifact banks roles outside", sel_scores={"model": {"M4": 0.15}},
                            head_real={"model": 0.1193})


@case("realsearch4096", "an-arm-fitted-with-another-recipes-parameters-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["model"]["params"] = dict(a["fits"]["model"]["params"], max_iter=999)
    return _realsearch_void(root, m, expect_clause="fit: model is not the roster's")


@case("realsearch4096", "an-arm-fitted-on-rows-that-are-not-the-sealed-block-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["logistic"]["fit_rows_sha256"] = "0" * 64
    return _realsearch_void(root, m, expect_clause="fit: logistic was not fitted on the sealed fit block")


@case("realsearch4096", "a-record-fitted-at-another-thread-count-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["model"]["environment"]["threads"] = 4
    return _realsearch_void(root, m, expect_clause="environment: model threads")


@case("realsearch4096", "a-tree-record-banking-an-iteration-count-instead-of-a-depth-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["depth3_tree"]["fit_info"] = {"n_iter": 100}; a["fit_info_by_name"]["depth3_tree"] = {"n_iter": 100}
    return _realsearch_void(root, m, expect_clause="fit: depth3_tree has no integer depth")


@case("realsearch4096", "ext_fam-that-does-not-hash-to-the-sealed-fam-array-is-VOID", "fail")
def _(root):
    def m(a, s):
        s["ext_fam"][0], s["ext_fam"][-1] = s["ext_fam"][-1], s["ext_fam"][0]
    return _realsearch_void(root, m, expect_clause="scores: ext_fam")


@case("realsearch4096", "permuted-evaluation-chunk-ids-are-VOID", "fail")
def _(root):
    def m(a, s):
        s["eval_chunk_ids"] = s["eval_chunk_ids"][26:] + s["eval_chunk_ids"][:26]
    return _realsearch_void(root, m, expect_clause="scores: eval_chunk_ids")


@case("realsearch4096", "an-absent-scores-file-is-VOID", "fail")
def _(root):
    return _realsearch_void(root, drop_scores=True, expect_clause="scores: the scores file is absent")


@case("realsearch4096", "an-absent-artifact-emits-no-verdict", "fail")
def _(root):
    rc, out = _realsearch(root, drop_artifact=True)
    if rc != 2 or "No verdict emitted" not in out:
        return 0, out + f" !! rc={rc}"
    return rc, out


@case("realsearch4096", "a-NOT-RUN-marker-emits-no-verdict", "fail")
def _(root):
    rc, out = _realsearch(root, not_run={"reason": "test", "stage": "confirm", "utc": "x", "n_checkpoints": 0})
    if rc != 2 or "NOT RUN" not in out:
        return 0, out + f" !! rc={rc}"
    return rc, out


@case("realsearch4096", "an-artifact-whose-fits-block-is-a-list-is-VOID-not-a-traceback", "fail")
def _(root):
    def m(a, s):
        a["fits"] = [a["fits"]["model"]]
    rc, out = _realsearch(root, m)
    if rc != 0 and "verdict=VOID" not in out:
        return 0, out + " !! the reader crashed instead of emitting VOID"
    return rc, out


@case("realsearch4096", "an-incomplete-run-is-VOID", "fail")
def _(root):
    return _realsearch_void(root, lambda a, s: a.update(complete=False, missing_roles=["model"]), expect_clause="complete:")


@case("realsearch4096", "an-artifact-with-no-ledger-is-VOID", "fail")
def _(root):
    return _realsearch_void(root, lambda a, s: a.update(ledger=[]), expect_clause="fit:")


@case("realsearch4096", "an-absent-selection-file-is-VOID", "fail")
def _(root):
    return _realsearch_void(root, drop_selection=True, expect_clause="leakage: the selection file is absent")


@case("realsearch4096", "a-selection-file-whose-hash-is-not-the-banked-one-is-VOID", "fail")
def _(root):
    art, sel_bytes, _ = _good_realsearch()
    return _realsearch_void(root, sel_bytes_override=sel_bytes + b"\n", expect_clause="leakage: selection_sha256")


@case("realsearch4096", "an-embedded-selection-that-differs-from-the-file-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["selection"]["cost"]["wall_seconds_this_invocation"] = 101.0
    return _realsearch_void(root, m, expect_clause="leakage: the embedded selection")


@case("realsearch4096", "a-selection-that-gathered-a-scored-row-is-VOID", "fail")
def _(root):
    def sm(sel):
        sel["gathers"][0]["n_rows_identical_to_a_scored_row"] = 1
    return _realsearch_void(root, expect_clause="leakage: stage select", sel_mutate=sm)


@case("realsearch4096", "a-selection-that-finished-after-confirmation-started-is-VOID", "fail")
def _(root):
    def sm(sel):
        sel["selection_finished_utc"] = "2026-09-18T02:30:00Z"
    return _realsearch_void(root, expect_clause="leakage: selection did not finish", sel_mutate=sm)


@case("realsearch4096", "a-confirmatory-entry-bound-to-another-selection-file-is-VOID", "fail")
def _(root):
    def m(a, s):
        e = next(e for e in a["ledger"] if e["event"] == "selection_bound" and e["name"] == "confirm_model"); e["selection_sha256"] = "0" * 64
    return _realsearch_void(root, m, expect_clause="leakage: confirmatory ledger entry")


@case("realsearch4096", "a-selection-record-with-a-changed-parameter-is-VOID", "fail")
def _(root):
    def sm(sel):
        sel["selection"]["model"]["stages"][0]["records"][2]["params"]["max_iter"] = 301
    return _realsearch_void(root, expect_clause="search: head model M3", sel_mutate=sm)


@case("realsearch4096", "a-banked-winner-that-is-not-the-rules-is-VOID", "fail")
def _(root):
    def sm(sel):
        sel["selection"]["logistic"]["selected_id"] = "L3"; sel["selected_ids"]["logistic"] = "L3"
        sel["selection"]["logistic"]["stages"][0]["advanced_ids"] = ["L3"]
    return _realsearch_void(root, expect_clause="search: head logistic", sel_mutate=sm)


@case("realsearch4096", "a-baseline-candidate-that-dropped-out-is-VOID", "fail")
def _(root):
    return _realsearch_void(root, expect_clause="search: baseline head logistic candidate L2", sel_status={("logistic", "L2"): "infeasible_memory"})


@case("realsearch4096", "two-model-candidates-infeasible-with-evidence-still-clears", "pass")
def _(root):
    return _realsearch(root, sel_status={("model", "M5"): "infeasible_memory", ("model", "M6"): "infeasible_memory"})


@case("realsearch4096", "three-model-candidates-infeasible-is-VOID", "fail")
def _(root):
    return _realsearch_void(root, expect_clause="search: 3 model-side infeasible",
                            sel_status={("model", "M5"): "infeasible_memory", ("model", "M6"): "infeasible_memory", ("model", "M7"): "infeasible_memory"})


@case("realsearch4096", "an-infeasible-incumbent-is-VOID", "fail")
def _(root):
    return _realsearch_void(root, expect_clause="search: the incumbent is infeasible", sel_status={("model", "M1"): "infeasible_memory"})


@case("realsearch4096", "a-knob-free-head-with-a-selection-stage-is-VOID", "fail")
def _(root):
    def sm(sel):
        sel["selection"]["majority"]["stages"] = [{"stage": 1, "records": []}]
    return _realsearch_void(root, expect_clause="search: knob-free head majority", sel_mutate=sm)


@case("realsearch4096", "a-roster-with-one-candidate-changed-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["roster"]["heads"][0]["candidates"][3]["params"]["max_iter"] = 251
    return _realsearch_void(root, m, expect_clause="scope: the banked roster")


@case("realsearch4096", "a-protocol-with-a-lower-margin-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["roster"]["protocol"]["bar"]["margin"] = 0.02
    return _realsearch_void(root, m, expect_clause="scope: roster.protocol.bar")


@case("realsearch4096", "a-protocol-with-a-lower-floor-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["roster"]["protocol"]["floors"]["logistic"] = 0.05
    return _realsearch_void(root, m, expect_clause="scope: roster.protocol.floors")


@case("realsearch4096", "a-changed-reproduction-reference-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["reference_top1"]["repro_m4"] = 0.20
    return _realsearch_void(root, m, expect_clause="reproduction: the banked reference")


@case("realsearch4096", "a-selected-model-id-that-disagrees-with-selected-ids-is-VOID", "fail")
def _(root):
    return _realsearch_void(root, lambda a, s: a.update(selected_model_id="M1"), expect_clause="search: selected_model_id")


@case("realsearch4096", "a-launch-environment-with-a-problem-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["launch_environment"]["ok"] = False; a["launch_environment"]["problems"] = ["threads 4 != preregistered 3"]
    return _realsearch_void(root, m, expect_clause="environment: launch_environment")


@case("realsearch4096", "the-logistic-head-selecting-0021s-recipe-reproduces-it-and-the-run-still-clears", "pass")
def _(root):
    # L3 wins the logistic head: repro_l3 is aliased to the logistic's own fit at 0021's 0.1179, the bar stays at the floor
    r22 = _rs_reader()
    return _realsearch(root, sel_scores={"logistic": {"L3": 0.15}}, head_real={"logistic": r22.REFERENCE["repro_l3"]})


@case("realsearch4096", "the-depth3-head-selecting-0021s-recipe-reproduces-it-and-the-run-still-clears", "pass")
def _(root):
    r22 = _rs_reader()
    return _realsearch(root, sel_scores={"depth3_tree": {"D1": 0.15}}, head_real={"depth3_tree": r22.REFERENCE["repro_d1"]})


@case("realsearch4096", "every-head-selecting-its-reference-recipe-is-a-clean-REAL_RECIPE_FAILS", "fail")
def _(root):
    r22 = _rs_reader()
    rc, out = _realsearch(root, sel_scores={"model": {"M1": 0.15}, "logistic": {"L3": 0.15}, "depth3_tree": {"D1": 0.15}},
                          head_real={"model": r22.REFERENCE["repro_m1"], "logistic": r22.REFERENCE["repro_l3"],
                                     "depth3_tree": r22.REFERENCE["repro_d1"]})
    if rc != 0 and ("verdict=REAL_RECIPE_FAILS" not in out or "validity=[]" not in out):
        return 0, out + " !! expected a clean REAL_RECIPE_FAILS with three aliased arms"
    return rc, out


@case("realsearch4096", "an-aliased-logistic-reproduction-off-by-0.006-is-VOID", "fail")
def _(root):
    r22 = _rs_reader()
    return _realsearch_void(root, expect_clause="reproduction: repro_l3", sel_scores={"logistic": {"L3": 0.15}},
                            head_real={"logistic": round(r22.REFERENCE["repro_l3"] + 0.006, 4)})


@case("realsearch4096", "a-control-whose-partition-is-the-readers-own-literals-is-detected", "fail")
def _(root):
    # the construction the six older gates used until 2026-09-17; the provenance case below must refuse it
    shape = json.load(open(_RS_SHAPE, encoding="utf-8")); S_art = shape["artifact"]
    art, sel_bytes, scores = _good_realsearch(); r22 = _rs_reader()
    art["partition"] = dict(r22.PARTITION)
    problems = _shape_problems(art, S_art, [("partition", art["partition"], S_art["partition"])], [], [])
    if not problems:
        return 0, "!! a partition taken from the reader's literals was not detected"
    return 1, problems[0]


@case("realsearch4096", "the-readers-record-requirements-hold-against-the-runners-own-banked-values", "pass")
def _(root):
    # the fixture's smoke records must satisfy every per-record requirement the reader makes that is NOT a sealed value:
    # fit_info by estimator family, per_family over the families present, probe_ok, finite scores
    shape = json.load(open(_RS_SHAPE, encoding="utf-8")); r22 = _rs_reader()
    by_id = {c["id"]: c for h in r22.HEADS for c in h["candidates"]}
    problems = []
    for name, rec in shape["artifact"]["fits"].items():
        fam = by_id[rec["id"]]["family"]; info = rec.get("fit_info")
        if fam in ("hgb", "logistic") and not isinstance(info.get("n_iter"), int):
            problems.append(f"{name}: {fam} without n_iter")
        if fam == "tree" and not (isinstance(info.get("depth"), int) and isinstance(info.get("n_leaves"), int)):
            problems.append(f"{name}: tree without depth/n_leaves")
        if fam == "dummy" and info != {}:
            problems.append(f"{name}: dummy with fit_info {info}")
        if sorted(rec["per_family"]) != sorted(r22.FAMILIES + ["ext:" + f for f in r22.EXT_FAMILIES]):
            problems.append(f"{name}: per_family keys {sorted(rec['per_family'])}")
        if any(not rf.get("probe_ok") for rf in rec.get("block_refills") or []):
            problems.append(f"{name}: a failed probe")
    for hid, e in shape["selection"]["selection"].items():
        for st in e["stages"]:
            for rec in st["records"]:
                if rec["status"] == "fit" and sorted(rec["per_family"]) != sorted(r22.FIT_FAMILIES):
                    problems.append(f"selection {hid}/{rec['id']}: per_family keys {sorted(rec['per_family'])}")
    if problems:
        return 1, "; ".join(problems[:4])
    return 0, f"{len(shape['artifact']['fits'])} confirmatory and {sum(len(st['records']) for e in shape['selection']['selection'].values() for st in e['stages'])} selection records satisfy the reader's record requirements"


@case("realsearch4096", "the-control-artifact-is-built-from-the-runners-own-output-shape", "pass")
def _(root):
    # docs/OPERATING_RULES.md section 4: symmetric and recursive - top level, every block, every record, both files
    shape = json.load(open(_RS_SHAPE, encoding="utf-8")); S_art, S_sel = shape["artifact"], shape["selection"]
    art, sel_bytes, scores = _good_realsearch(); sel = json.loads(sel_bytes); r22 = _rs_reader()
    blocks = [("partition", art["partition"], S_art["partition"]), ("corpus", art["corpus"], S_art["corpus"]),
              ("ext_corpus", art["ext_corpus"], S_art["ext_corpus"]), ("fit_corpus", art["fit_corpus"], S_art["fit_corpus"]),
              ("roster", art["roster"], S_art["roster"]), ("selection.roster", sel["roster"], S_sel["roster"]),
              ("bars", art["bars"], S_art["bars"]), ("selection (file)", sel, S_sel), ("selection.partition", sel["partition"], S_sel["partition"]),
              ("scores (file)", {k: v for k, v in scores.items()}, dict(shape["scores"], per_example=None, eval_chunk_ids=None, ext_chunk_ids=None, ext_fam=None))]
    blocks += [(f"readings.{n}", art["readings"][n], S_art["readings"]["model"]) for n in art["readings"]]
    records = [(f"fits.{n}", art["fits"][n], S_art["fits"][n] if n in S_art["fits"] else S_art["fits"]["repro_m4"]) for n in art["fits"]]
    for hid, e in sel["selection"].items():
        for st in e["stages"]:
            records += [(f"selection.{hid}.{r['id']}", r, S_sel["selection"]["model"]["stages"][0]["records"][0]) for r in st["records"]]
    problems = _shape_problems(art, S_art, blocks, records,
                               [("PARTITION", r22.PARTITION, S_art["partition"]), ("CORPUS", r22.CORPUS, S_art["corpus"]),
                                ("EXT", r22.EXT, S_art["ext_corpus"]), ("FIT", r22.FIT, S_art["fit_corpus"])])
    if problems:
        return 1, "; ".join(problems[:4])
    return 0, (f"control and fixture agree both ways on {len(S_art)} artifact keys, {len(S_sel)} selection keys, {len(art['fits'])} "
               f"confirmatory records, {sum(len(st['records']) for e in sel['selection'].values() for st in e['stages'])} selection "
               f"records and every block; every reader expectation is a key the runner writes")


# ---------------------------------------------------------------- realcurve4096 gate (0023)
# The 0023 reader reads a scaling curve on real plaintexts: 0021's three fixed recipes on four nested, family-stratified
# rungs of the real fit block, a slope per doubling of plaintexts and a paired cluster bootstrap. The control takes its
# SHAPE from tests/fixtures/realcurve_runner_shape.json, a smoke run of tools/pivot/run_realcurve.py itself, and its
# VALUES from the reader's sealed literals; the curve, the slopes and the bootstrap are computed with the runner's own
# functions on the control's vectors (docs/OPERATING_RULES.md section 4).
_RC_SHAPE = os.path.join(REPO, "tests", "fixtures", "realcurve_runner_shape.json")


def _rc_reader():
    import importlib.util
    spec = importlib.util.spec_from_file_location("r23", os.path.join(REPO, "tools", "readers", "realcurve4096_verdict.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _rc_runner():
    import importlib.util
    sys.path.insert(0, os.path.join(REPO, "tools", "pivot"))
    spec = importlib.util.spec_from_file_location("run_realcurve", os.path.join(REPO, "tools", "pivot", "run_realcurve.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _rc_readings(r23, v, fam_x, fam_e):
    """The runner's readings() over one per-example vector, recomputed here from the same rule (0021's shape)."""
    n_eval, n_ext = r23.PARTITION["n_eval_rows"], r23.N_EXT
    rep, ex = v[:n_eval], v[n_eval:]
    by = {f: [] for f in r23.EXT_FAMILIES}
    for i in range(n_ext):
        by[fam_x[i]].append(ex[i])
    m4 = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
    real = [x for f in r23.REAL_FAMILIES for x in by[f]]; synth = [x for f in r23.SYNTH_FAMILIES for x in by[f]]
    return {"builder_eval_top1": m4(rep), "builder_eval_correct": sum(rep), "ext_top1": m4(ex), "ext_correct": sum(ex),
            "n_ext_rows": n_ext, "ext_per_family": {f: m4(by[f]) for f in r23.EXT_FAMILIES},
            "ext_per_family_correct": {f: sum(by[f]) for f in r23.EXT_FAMILIES},
            "ext_structured_text_top1": m4([x for f in r23.STRUCTURED_TEXT for x in by[f]]),
            "ext_high_entropy_top1": m4([x for f in r23.HIGH_ENTROPY for x in by[f]]),
            "ext_real_top1": m4(real), "ext_real_correct": sum(real), "n_ext_real_rows": len(real),
            "ext_synthetic_correct": sum(synth), "ext_synthetic_top1": m4(synth),
            "builder_eval_per_family": {f: m4([rep[i] for i in range(n_eval) if fam_e[i] == f]) for f in r23.FAMILIES}}


# Default rung accuracies on the real-family rows (top rung = 0021's reference exactly): a rising model curve that clears
# the bar, a flatter logistic and tree beside it, the null at chance.
_RC_ACC = {"model": [0.09, 0.10, 0.11, 0.1193], "logistic": [0.10, 0.105, 0.11, 0.1179], "depth3_tree": [0.08, 0.085, 0.09, 0.0929]}
_RC_REP_ACC = {"model": 0.093, "logistic": 0.099, "depth3_tree": 0.082}     # the replicate of rung 1: near rung 1, never identical


def _good_realcurve(acc=None, null_acc=None, mode="nested", rep_acc=None):
    """A complete, valid 0023 artifact set (artifact, scores). Shape AND key sets from the runner's own smoke output
    (tests/fixtures/realcurve_runner_shape.json); only the values are the sealed run's, and the curve, slopes and
    bootstrap are computed with tools/pivot/run_realcurve.py's own functions on the control's vectors.

    acc overrides a role's four rung accuracies on the real-family rows; null_acc the null's. Vectors are marked at
    CHUNK granularity with row precision inside the last chunk: 'nested' marks each family's leading chunks, so a
    higher rung's correct rows contain a lower rung's (one corpus growing) and every chunk resample agrees on the
    direction; 'disjoint' rotates each rung's marked chunks to a different part of every family, so the rungs are
    correct on different plaintexts and a chunk bootstrap sees the rise the chunks do NOT agree on."""
    r23 = _rc_reader(); rr = _rc_runner(); shape = json.load(open(_RC_SHAPE, encoding="utf-8")); S_art = shape["artifact"]
    zeros = {k: 0 for k in ("pool_chunks_shared_with_ext", "eval_chunks_shared_with_ext", "fit_chunks_shared_with_ext",
                            "fit_chunks_shared_with_builder", "fit_source_chunks_shared_with_ext", "fit_rows_identical_to_a_scored_row")}
    nulls = {"null_y_shuffled_sha256": r23.NULL_SHA_EXPECTED, "null_labels_permuted": True, "null_labels_same_multiset": True}
    part = _rf_sub(S_art["partition"], dict(r23.PARTITION, **zeros, **nulls), "partition", sealed_may_be_subset=True)
    spec = _rf_sub(S_art["curve_spec"], json.loads(json.dumps({"protocol": r23.PROTOCOL, "recipes": r23.RECIPES})), "curve_spec")
    assert _sha12(spec) == r23.CURVE_SHA256, "the reader's curve literals do not hash to its CURVE_SHA256"
    n_eval, n_ext, n_real = r23.PARTITION["n_eval_rows"], r23.N_EXT, r23.N_REAL
    fams = list(r23.EXT_FAMILIES); rpf = r23.EXT["rows_per_family"]
    fam_idx = []
    for k, f in enumerate(fams):
        fam_idx += [k] * rpf[f]
    fam_x = [fams[i] for i in fam_idx]
    ext_ids = [c for c, n in zip(r23.EXT_CHUNK_IDS, r23.EXT_ROWS_PER_CHUNK) for _ in range(n)]
    eval_ids = [c for c, n in zip(r23.EVAL_CHUNK_IDS, r23.EVAL_ROWS_PER_CHUNK) for _ in range(n)]
    fam_e = [r23.FAMILIES[c % 8] for c in eval_ids]
    env = dict(S_art["environment"], threads=3, nice=10)
    # each family's chunks as row ranges of the extension block, in row order
    chunks_by_fam = {f: [] for f in fams}
    pos = 0
    for c, n in zip(r23.EXT_CHUNK_IDS, r23.EXT_ROWS_PER_CHUNK):
        chunks_by_fam[fam_x[pos]].append((pos, pos + n)); pos += n
    assert pos == n_ext
    accs = {r: list(v) for r, v in _RC_ACC.items()}
    for r, v in (acc or {}).items():
        accs[r] = list(v)
    raccs = dict(_RC_REP_ACC, **(rep_acc or {}))
    n_rungs = r23.N_RUNGS; order = list(r23.ORDER); REP = r23.REPLICATE

    def vec(role, k, a, idx=0):
        """Real-family accuracy a at rung k: leading (nested) or rotated (disjoint) chunks per family, row-precise. The
        builder-evaluation part carries idx extra correct rows so that no two fits bank an identical vector (the reader
        requires the sixteen vectors to be pairwise distinct; two honest fits do not score identically)."""
        v = [0] * (n_eval + n_ext)
        rep = 0.19 if role != "null" else 0.038
        for i in range(int(round(rep * n_eval)) + idx):
            v[i] = 1
        for f in fams:
            want = int(round(a * rpf[f])); ch = chunks_by_fam[f]
            start = 0 if (mode == "nested" or role == "null" or k == REP) else (k * len(ch) // (n_rungs + 1))
            j = 0
            while want > 0:
                s, e = ch[(start + j) % len(ch)]; take = min(want, e - s)
                for i in range(s, s + take):
                    v[n_eval + i] = 1
                want -= take; j += 1
        return v

    def name_parts(name):
        if name == "null":
            return n_rungs, "null"
        head, role = name.split("_", 1)
        return (REP if head == REP else int(head[1:])), role

    def rk_of(k):
        return part["replicate_rung_1"] if k == REP else part["rungs"][k - 1]

    def stage_of(name):
        return "null" if name == "null" else ("replicate" if name_parts(name)[0] == REP else "curve")

    def cand_of(name):
        return r23.RECIPES["model"] if name == "null" else r23.RECIPES[name_parts(name)[1]]

    def fp(name):
        k, role = name_parts(name); rk = rk_of(k)
        return r23.fingerprint(prereg=r23.PREREG, seed=r23.SEED, head=role, cand=cand_of(name), stage=stage_of(name),
                               rung=k, rows=rk["sorted_sha256"], eval=part["eval_idx_sha256"], ext=r23.EXT["arrays"]["X"]["sha256"],
                               fit=r23.FIT["arrays"]["X"]["sha256"])

    def record(name, v):
        k, role = name_parts(name); c = cand_of(name); rk = rk_of(k); m4 = lambda xs: round(sum(xs) / len(xs), 4)  # noqa: E731
        fam_s = fam_e + ["ext:" + f for f in fam_x]
        ng = [v[i] for i in range(n_eval) if fam_e[i] != "gutenberg"] + v[n_eval:]
        sealed = {"id": c["id"], "head": role, "role": role, "rung": k, "family": c["family"], "params": dict(c.get("params", {})),
                  "scaled": bool(c.get("scaled", False)), "val": c.get("val"), "seed": r23.SEED, "params_sha256": _sha12(c),
                  "stage": stage_of(name), "n_fit_rows": rk["n_rows"], "fit_rows_sha256": rk["idx_sha256"],
                  "fit_rows_sorted_sha256": rk["sorted_sha256"], "n_rung_rows": rk["n_rows"], "n_rung_chunks": rk["n_chunks"],
                  "environment": dict(env), "interruptions_before_this_fit": 0, "status": "fit", "top1": m4(v), "top1_non_gutenberg": m4(ng),
                  "per_family": {f: m4([v[i] for i in range(len(v)) if fam_s[i] == f]) for f in sorted(set(fam_s))},
                  "fingerprint": fp(name), "per_example_sha256": hashlib.sha256(bytes(v)).hexdigest()}
        return _rf_sub(S_art["fits"][name], sealed, f"fits.{name}", sealed_may_be_subset=True)

    per_example, reads, fits = {}, {}, {}
    for idx, name in enumerate(order):
        k, role = name_parts(name)
        a = (null_acc if null_acc is not None else 0.037) if name == "null" else (raccs[role] if k == REP else accs[role][k - 1])
        v = vec(role, k, a, idx); per_example[name] = v
        reads[name] = _rc_readings(r23, v, fam_x, fam_e); fits[name] = record(name, v)
    ledger = []
    for i, nm in enumerate(order):
        k, _ = name_parts(nm); rk = rk_of(k)
        ledger += [{"name": f"run_{nm}", "fingerprint": fp(nm), "event": "rung_bound", "utc": f"2026-09-19T02:{i:02d}:00Z", "rss_gb": 1.0,
                    "pid": 1, "rung": k, "rung_sorted_sha256": rk["sorted_sha256"]},
                   {"name": f"run_{nm}", "fingerprint": fp(nm), "event": "started", "utc": f"2026-09-19T02:{i:02d}:01Z", "rss_gb": 1.0, "pid": 1, "attempt": 1},
                   {"name": f"run_{nm}", "fingerprint": fp(nm), "event": "completed", "utc": f"2026-09-19T02:{i:02d}:30Z", "rss_gb": 1.0, "pid": 1, "seconds": 1.0}]
    log2x = list(r23.LOG2X)

    def role_curve(role):
        pts = []
        for rk in part["rungs"]:
            rd = reads[f"r{rk['rung']}_{role}"]
            pts.append({"rung": rk["rung"], "denominator": rk["denominator"], "n_chunks": rk["n_chunks"], "n_rows": rk["n_rows"],
                        "log2_chunks": rk["log2_chunks"], "ext_real_top1": rd["ext_real_top1"], "ext_real_correct": rd["ext_real_correct"],
                        "builder_eval_top1": rd["builder_eval_top1"], "ext_per_family": {f: rd["ext_per_family"][f] for f in r23.REAL_FAMILIES}})
        ys = [p["ext_real_top1"] for p in pts]
        return {"rungs": pts, "complete": True, "slope_per_doubling": round(rr.ols_slope(log2x, ys), 6),
                "end_to_end_gain": round(ys[-1] - ys[0], 4),
                "rung_to_rung_gains": [round(ys[i + 1] - ys[i], 4) for i in range(len(ys) - 1)],
                "slope_with_top_rung_at_reference": round(rr.ols_slope(log2x, ys[:-1] + [float(r23.REFERENCE[role])]), 6),
                "per_family_slope_per_doubling": {f: round(rr.ols_slope(log2x, [p["ext_per_family"][f] for p in pts]), 6) for f in r23.REAL_FAMILIES},
                "builder_eval_slope_per_doubling": round(rr.ols_slope(log2x, [p["builder_eval_top1"] for p in pts]), 6)}
    curves = {role: role_curve(role) for role in r23.ROLES}
    rep_block = {"rung": part["replicate_rung_1"], "readings": {}, "difference_from_rung_1": {}, "slope_with_replicate_at_rung_1": {},
                 "note": S_art["replicate_rung_1"]["note"]}
    for role in r23.ROLES:
        rr_ = reads[f"{REP}_{role}"]; r1 = reads[f"r1_{role}"]
        rep_block["readings"][role] = {"ext_real_top1": rr_["ext_real_top1"], "ext_real_correct": rr_["ext_real_correct"],
                                       "builder_eval_top1": rr_["builder_eval_top1"],
                                       "ext_per_family": {f: rr_["ext_per_family"][f] for f in r23.REAL_FAMILIES}}
        rep_block["difference_from_rung_1"][role] = round(rr_["ext_real_top1"] - r1["ext_real_top1"], 4)
        ys = [p["ext_real_top1"] for p in curves[role]["rungs"]]
        rep_block["slope_with_replicate_at_rung_1"][role] = round(rr.ols_slope(log2x, [rr_["ext_real_top1"]] + ys[1:]), 6)
    ms, ls, ts = (curves[r]["slope_per_doubling"] for r in ("model", "logistic", "depth3_tree"))
    import numpy as _np
    real_idx = [i for i in range(n_ext) if fam_x[i] in r23.REAL_FAMILIES]
    cid = _np.asarray([ext_ids[i] for i in real_idx], _np.int64)
    by_role = {role: [_np.asarray([per_example[f"r{k}_{role}"][n_eval + i] for i in real_idx], _np.int8) for k in range(1, n_rungs + 1)]
               for role in r23.ROLES}
    sl = rr.slope_bootstrap(by_role, log2x, cid, r23.N_BOOT, r23.BOOT_SEED)
    boot = {role: {"ci95": [round(float(_np.percentile(sl[role], 2.5)), 6), round(float(_np.percentile(sl[role], 97.5)), 6)],
                   "n_boot": r23.N_BOOT, "seed": r23.BOOT_SEED, "mean": round(float(sl[role].mean()), 6)} for role in r23.ROLES}
    for a_, b_ in (("model", "logistic"), ("model", "depth3_tree")):
        d = sl[a_] - sl[b_]
        boot[f"{a_}_minus_{b_}"] = {"ci95": [round(float(_np.percentile(d, 2.5)), 6), round(float(_np.percentile(d, 97.5)), 6)],
                                    "paired": True, "share_of_resamples_with_model_ahead": round(float((d > 0).mean()), 4)}
    boot["unit"] = S_art["slope_bootstrap"]["unit"]
    top = f"r{n_rungs}_"
    art = _shape_fill(S_art, {
        "schema_version": 1, "schema": "raise-v1/realcurve_4096/1", "preregistration": r23.PREREG, "smoke": False,
        "curve_sha256": r23.CURVE_SHA256, "curve_spec": spec, "corpus": dict(r23.CORPUS), "ext_corpus": dict(r23.EXT),
        "fit_corpus": dict(r23.FIT), "partition": part, "n_classes": 26, "class_names": [], "chance_accuracy": r23.CHANCE,
        "stage": "run", "environment": dict(env),
        "launch_environment": {"env": dict(env), "loadavg_1_5_15": [0.1, 0.1, 0.1], "problems": [], "ok": True, "loadavg_waited_seconds": 0},
        "launch_number": 1, "complete": True, "missing_roles": [], "fits": fits, "readings": reads,
        "ext_real_top1": {n: reads[n]["ext_real_top1"] for n in order}, "ext_real_correct": {n: reads[n]["ext_real_correct"] for n in order},
        "ext_top1": {n: reads[n]["ext_top1"] for n in order}, "builder_eval_top1": {n: reads[n]["builder_eval_top1"] for n in order},
        "ext_per_family": {n: reads[n]["ext_per_family"] for n in order},
        "curves": curves, "roles": list(r23.ROLES), "n_rungs": n_rungs, "denominators": list(r23.DENOMINATORS), "log2_chunks": log2x,
        "model_slope_per_doubling": ms, "logistic_slope_per_doubling": ls, "depth3_tree_slope_per_doubling": ts,
        "slope_model_minus_logistic": round(ms - ls, 6), "slope_model_minus_depth3_tree": round(ms - ts, 6),
        "bar": {"slope_per_doubling": r23.BAR_SLOPE, "bootstrap_lower_bound_gt": r23.BOOT_LB, "n_boot": r23.N_BOOT, "bootstrap_seed": r23.BOOT_SEED},
        "slope_bootstrap": boot, "replicate_rung_1": rep_block,
        "n_ext_real_rows": n_real, "n_ext_rows": n_ext, "n_eval_rows": n_eval,
        "ext_real_families": list(r23.REAL_FAMILIES), "ext_synthetic_families": list(r23.SYNTH_FAMILIES),
        "fit_families": list(r23.FIT_FAMILIES), "fit_rows_per_family": r23.FIT["rows_per_family"],
        "reference_top1": dict(r23.REFERENCE), "reproduction_top1": {role: reads[top + role]["ext_real_top1"] for role in r23.ROLES},
        "reproduction_drift": {role: round(reads[top + role]["ext_real_top1"] - r23.REFERENCE[role], 6) for role in r23.ROLES},
        "shuffled_label_accuracy_ext": reads["null"]["ext_top1"], "shuffled_label_accuracy_eval": reads["null"]["builder_eval_top1"],
        "shuffled_label_accuracy_real": reads["null"]["ext_real_top1"],
        "null_control": fits["null"], "null_rows": part["fit_rows"],
        "fit_info_by_name": {n: fits[n]["fit_info"] for n in order}, "ledger": ledger,
        "cluster_ci95_informational": {}, "cost": {},
        "run_started_utc": "2026-09-19T02:00:00Z", "first_launch_utc": "2026-09-19T02:00:00Z", "run_finished_utc": "2026-09-19T03:00:00Z"}, "artifact")
    scores = {"schema": "raise-v1/realcurve_4096_scores/1", "preregistration": r23.PREREG, "smoke": False,
              "n_eval_rows": n_eval, "n_ext_rows": n_ext, "eval_idx_sha256": part["eval_idx_sha256"],
              "eval_chunk_ids": eval_ids, "ext_chunk_ids": ext_ids, "ext_fam": fam_idx, "ext_families": fams,
              "ext_arrays_sha256": {k: v["sha256"] for k, v in r23.EXT["arrays"].items()},
              "fit_arrays_sha256": {k: v["sha256"] for k, v in r23.FIT["arrays"].items()},
              "layout": "each per_example vector is [sealed evaluation rows (n_eval_rows)] + [extension rows (n_ext_rows)]",
              "per_example": per_example}
    return art, scores


def _realcurve(root, mutate=None, drop_artifact=False, drop_scores=False, not_run=None, **kw):
    art, scores = _good_realcurve(**kw)
    if mutate:
        r = mutate(art, scores)
        if r is not None:
            art = r
    piv = os.path.join(root, "artifacts", "pivot"); os.makedirs(piv, exist_ok=True)
    if not drop_scores:
        json.dump(scores, open(os.path.join(piv, "realcurve_4096_scores.json"), "w"))
    if not drop_artifact:
        json.dump(art, open(os.path.join(piv, "realcurve_4096.json"), "w"))
    if not_run is not None:
        json.dump(not_run, open(os.path.join(piv, "realcurve_4096_not_run.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", "realcurve4096_verdict.py"),
                os.path.join(root, "tools", "readers", "realcurve4096_verdict.py"))
    rc, out = run([PY, "tools/readers/realcurve4096_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(piv, "realcurve_4096_verdict.json")))
    ok = v["verdict"] == "REAL_CURVE_RISES"
    return (0 if ok else 1), (f"verdict={v['verdict']} slope={v.get('model_slope_per_doubling')} ci={v.get('model_slope_ci95')} "
                              f"rungs={v.get('model_real_top1_by_rung')} validity={v['validity_failed_clauses'][:2]} "
                              f"slope_failed={v['slope_failed_clauses']}")


def _realcurve_void(root, mutate=None, expect_clause=None, **kw):
    rc, out = _realcurve(root, mutate, **kw)
    if rc != 0 and "verdict=VOID" not in out and "No verdict emitted" not in out:
        return 0, out + " !! detected but not as VOID"
    if expect_clause and expect_clause not in out:
        return 0, out + f" !! VOID for another reason than {expect_clause!r}"
    return rc, out


def _realcurve_flat(root, expect_clause, **kw):
    rc, out = _realcurve(root, **kw)
    if rc != 0 and ("verdict=REAL_CURVE_FLAT" not in out or "validity=[]" not in out or expect_clause not in out):
        return 0, out + f" !! expected a clean REAL_CURVE_FLAT on {expect_clause!r}"
    return rc, out


def _rc_mut(fn):
    def m(art, scores):
        fn(art, scores)
    return m


@case("realcurve4096", "control-rising-model-curve-is-REAL_CURVE_RISES", "pass")
def _(root):
    rc, out = _realcurve(root)
    if rc == 0 and "validity=[]" not in out:
        return 1, out
    return rc, out


@case("realcurve4096", "control-logistic-rising-faster-than-the-model-is-still-a-pass-and-a-flag", "pass")
def _(root):
    return _realcurve(root, acc={"logistic": [0.07, 0.09, 0.11, 0.1179]})


@case("realcurve4096", "control-slope-just-above-the-bar-passes", "pass")
def _(root):
    art, _ = _good_realcurve(acc={"model": [0.1033, 0.1086, 0.114, 0.1193]})
    if not (0.005 <= art["model_slope_per_doubling"] < 0.0062):
        return 1, f"!! control slope {art['model_slope_per_doubling']} is not just above the bar"
    return _realcurve(root, acc={"model": [0.1033, 0.1086, 0.114, 0.1193]})


@case("realcurve4096", "a-model-slope-just-below-the-bar-is-REAL_CURVE_FLAT", "fail")
def _(root):
    art, _ = _good_realcurve(acc={"model": [0.1065, 0.1108, 0.115, 0.1193]})
    if not (0.0035 < art["model_slope_per_doubling"] < 0.005):
        return 0, f"!! control slope {art['model_slope_per_doubling']} is not just below the bar"
    return _realcurve_flat(root, "slope:", acc={"model": [0.1065, 0.1108, 0.115, 0.1193]})


@case("realcurve4096", "a-flat-model-curve-is-REAL_CURVE_FLAT", "fail")
def _(root):
    return _realcurve_flat(root, "slope:", acc={"model": [0.1193, 0.1193, 0.1193, 0.1193]})


@case("realcurve4096", "a-falling-model-curve-is-REAL_CURVE_FLAT", "fail")
def _(root):
    return _realcurve_flat(root, "slope:", acc={"model": [0.14, 0.13, 0.125, 0.1193]})


@case("realcurve4096", "a-rise-the-scored-chunks-do-not-agree-on-fails-the-bootstrap-clause-alone", "fail")
def _(root):
    # the same rung readings as a passing control, but each rung is correct on DIFFERENT plaintexts: the slope clears the bar
    # and the chunk bootstrap's 2.5th percentile does not sit above 0
    art, _ = _good_realcurve(mode="disjoint", acc={"model": [0.1033, 0.1086, 0.114, 0.1193]})
    if art["model_slope_per_doubling"] < 0.005 or art["slope_bootstrap"]["model"]["ci95"][0] > 0:
        return 0, f"!! control slope {art['model_slope_per_doubling']} ci {art['slope_bootstrap']['model']['ci95']} does not isolate the bootstrap clause"
    rc, out = _realcurve_flat(root, "slope_bootstrap:", mode="disjoint", acc={"model": [0.1033, 0.1086, 0.114, 0.1193]})
    if rc != 0 and "slope: the model" in out:
        return 0, out + " !! the slope clause failed too"
    return rc, out


@case("realcurve4096", "a-top-rung-model-reading-0.006-off-0021-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, expect_clause="reproduction: r4_model", acc={"model": [0.09, 0.10, 0.11, 0.1253]})


@case("realcurve4096", "a-top-rung-logistic-reading-0.006-off-0021-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, expect_clause="reproduction: r4_logistic", acc={"logistic": [0.10, 0.105, 0.11, 0.1239]})


@case("realcurve4096", "a-top-rung-tree-reading-0.006-off-0021-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, expect_clause="reproduction: r4_depth3_tree", acc={"depth3_tree": [0.08, 0.085, 0.09, 0.0869]})


@case("realcurve4096", "a-top-rung-reading-within-tolerance-passes", "pass")
def _(root):
    return _realcurve(root, acc={"model": [0.09, 0.10, 0.11, 0.1233]})


@case("realcurve4096", "a-null-control-above-chance-plus-tolerance-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, expect_clause="null control: shuffled labels", null_acc=0.05)


@case("realcurve4096", "a-null-label-array-that-is-not-0021s-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["partition"].__setitem__("null_y_shuffled_sha256", "0" * 64)),
                           expect_clause="null control: the permuted label array")


@case("realcurve4096", "null-labels-not-banked-as-a-permutation-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["partition"].__setitem__("null_labels_same_multiset", False)),
                           expect_clause="null control: the null labels")


@case("realcurve4096", "a-smoke-artifact-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a.__setitem__("smoke", True)), expect_clause="scope: smoke")


@case("realcurve4096", "a-wrong-preregistration-id-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a.__setitem__("preregistration", "0022-realsearch-4096")), expect_clause="scope: preregistration")


@case("realcurve4096", "a-protocol-with-one-changed-denominator-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curve_spec"]["protocol"]["denominators"] = [16, 4, 2, 1]
    return _realcurve_void(root, _rc_mut(m), expect_clause="scope:")


@case("realcurve4096", "a-recipe-off-the-sealed-three-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curve_spec"]["recipes"]["model"]["params"]["learning_rate"] = 0.31
    return _realcurve_void(root, _rc_mut(m), expect_clause="scope:")


@case("realcurve4096", "a-fit-record-on-an-off-recipe-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["r2_model"]["params"] = dict(a["fits"]["r2_model"]["params"], max_leaf_nodes=7)
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: r2_model is not the sealed")


@case("realcurve4096", "a-builder-cache-x-hash-off-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["corpus"].__setitem__("cache_X_sha256", "f" * 64)), expect_clause="scope: corpus.cache_X_sha256")


@case("realcurve4096", "an-extension-corpus-block-off-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["ext_corpus"].__setitem__("n_rows", a["ext_corpus"]["n_rows"] + 1)),
                           expect_clause="evaluation corpus: ext_corpus.n_rows")


@case("realcurve4096", "a-fit-corpus-array-hash-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fit_corpus"]["arrays"]["X"]["sha256"] = "e" * 64
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit corpus: fit_corpus.arrays")


@case("realcurve4096", "a-fit-block-index-hash-off-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["partition"].__setitem__("fit_idx_sha256", "d" * 64)), expect_clause="sealed set: partition.fit_idx_sha256")


@case("realcurve4096", "a-rungs-row-count-off-by-one-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["rungs"][1]["n_rows"] += 1
    return _realcurve_void(root, _rc_mut(m), expect_clause="sealed set: partition.rungs")


@case("realcurve4096", "a-rungs-chunk-set-hash-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["rungs"][0]["chunks_sha256"] = "c" * 64
    return _realcurve_void(root, _rc_mut(m), expect_clause="sealed set: partition.rungs")


@case("realcurve4096", "rungs-banked-as-not-nested-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["partition"].__setitem__("rungs_nested", False)), expect_clause="partition.rungs_nested")


@case("realcurve4096", "a-top-rung-that-is-not-the-fit-block-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["partition"].__setitem__("top_rung_is_fit_block", False)), expect_clause="partition.top_rung_is_fit_block")


@case("realcurve4096", "one-fit-row-identical-to-a-scored-row-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["partition"].__setitem__("fit_rows_identical_to_a_scored_row", 1)),
                           expect_clause="leakage: partition.fit_rows_identical_to_a_scored_row")


@case("realcurve4096", "a-fit-chunk-shared-with-the-builder-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["partition"].__setitem__("fit_chunks_shared_with_builder", 1)),
                           expect_clause="leakage: partition.fit_chunks_shared_with_builder")


@case("realcurve4096", "a-record-fitted-on-the-wrong-rung-is-VOID", "fail")
def _(root):
    def m(a, s):
        r1, r2 = a["fits"]["r1_model"], a["fits"]["r2_model"]
        r1["fit_rows_sha256"], r1["fit_rows_sorted_sha256"], r1["n_fit_rows"] = r2["fit_rows_sha256"], r2["fit_rows_sorted_sha256"], r2["n_fit_rows"]
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: r1_model was not fitted on sealed rung 1")


@case("realcurve4096", "a-missing-rung-role-is-VOID", "fail")
def _(root):
    def m(a, s):
        del a["fits"]["r3_logistic"]
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: the artifact banks roles outside the sealed order")


@case("realcurve4096", "an-extra-role-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["r5_model"] = dict(a["fits"]["r4_model"])
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: the artifact banks roles outside the sealed order")


@case("realcurve4096", "a-fingerprint-off-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["fits"]["r4_model"].__setitem__("fingerprint", "0123456789abcdef")),
                           expect_clause="fit: r4_model fingerprint")


@case("realcurve4096", "a-role-completed-twice-is-VOID", "fail")
def _(root):
    def m(a, s):
        done = [e for e in a["ledger"] if e["name"] == "run_r1_model" and e["event"] == "completed"][0]
        a["ledger"].append(dict(done))
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: r1_model has 2 ledger completions")


@case("realcurve4096", "completions-out-of-the-sealed-order-are-VOID", "fail")
def _(root):
    def m(a, s):
        # the whole of r4_model's three events (rung_bound, started, completed) move after r1_depth3_tree's: every role's own
        # start still precedes its completion, and only the sealed order is broken
        L = a["ledger"]; mine = [e for e in L if e["name"] == "run_r4_model"]; rest = [e for e in L if e["name"] != "run_r4_model"]
        j = max(i for i, e in enumerate(rest) if e["name"] == "run_r1_depth3_tree") + 1
        a["ledger"] = rest[:j] + mine + rest[j:]
    return _realcurve_void(root, _rc_mut(m), expect_clause="order")


@case("realcurve4096", "a-rung-bound-event-naming-the-wrong-rung-is-VOID", "fail")
def _(root):
    def m(a, s):
        e = [e for e in a["ledger"] if e["name"] == "run_r2_logistic" and e["event"] == "rung_bound"][0]; e["rung"] = 3
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: r2_logistic has no 'rung_bound' event")


@case("realcurve4096", "a-per-example-vector-one-row-short-is-VOID", "fail")
def _(root):
    def m(a, s):
        s["per_example"]["r3_model"] = s["per_example"]["r3_model"][:-1]
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: r3_model per-example vector")


@case("realcurve4096", "a-per-example-hash-off-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["fits"]["r3_model"].__setitem__("per_example_sha256", "a" * 64)),
                           expect_clause="fit: r3_model per_example_sha256")


@case("realcurve4096", "a-record-top1-off-by-0.0001-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["fits"]["r2_depth3_tree"].__setitem__("top1", round(a["fits"]["r2_depth3_tree"]["top1"] + 0.0001, 4))),
                           expect_clause="fit: r2_depth3_tree record top1")


@case("realcurve4096", "a-banked-rung-reading-off-by-0.0001-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["readings"]["r1_model"]["ext_real_top1"] = round(a["readings"]["r1_model"]["ext_real_top1"] + 0.0001, 4)
    return _realcurve_void(root, _rc_mut(m), expect_clause="readings: r1_model.ext_real_top1")


@case("realcurve4096", "a-banked-curve-point-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curves"]["model"]["rungs"][0]["ext_real_top1"] = round(a["curves"]["model"]["rungs"][0]["ext_real_top1"] + 0.0001, 4)
    return _realcurve_void(root, _rc_mut(m), expect_clause="curve: curves.model.rungs")


@case("realcurve4096", "a-banked-slope-off-by-0.00001-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curves"]["model"]["slope_per_doubling"] = round(a["curves"]["model"]["slope_per_doubling"] + 0.00001, 6)
        a["model_slope_per_doubling"] = a["curves"]["model"]["slope_per_doubling"]
        a["slope_model_minus_logistic"] = round(a["model_slope_per_doubling"] - a["logistic_slope_per_doubling"], 6)
        a["slope_model_minus_depth3_tree"] = round(a["model_slope_per_doubling"] - a["depth3_tree_slope_per_doubling"], 6)
    return _realcurve_void(root, _rc_mut(m), expect_clause="curve: curves.model.slope_per_doubling")


@case("realcurve4096", "a-top-level-slope-that-is-not-the-curves-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a.__setitem__("model_slope_per_doubling", 0.02)), expect_clause="curve: a banked top-level slope")


@case("realcurve4096", "a-slope-difference-that-is-not-model-minus-logistic-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a.__setitem__("slope_model_minus_logistic", 0.0)), expect_clause="curve: a banked slope difference")


@case("realcurve4096", "a-banked-bootstrap-interval-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["slope_bootstrap"]["model"]["ci95"][0] = round(a["slope_bootstrap"]["model"]["ci95"][0] - 0.000001, 6)
    return _realcurve_void(root, _rc_mut(m), expect_clause="curve: slope_bootstrap.model")


@case("realcurve4096", "a-banked-paired-difference-interval-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["slope_bootstrap"]["model_minus_logistic"]["share_of_resamples_with_model_ahead"] = 0.5
    return _realcurve_void(root, _rc_mut(m), expect_clause="curve: slope_bootstrap.model_minus_logistic")


@case("realcurve4096", "a-bar-banked-lower-than-sealed-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["bar"].__setitem__("slope_per_doubling", 0.001)), expect_clause="scope: bar=")


@case("realcurve4096", "log2-plaintexts-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["log2_chunks"] = [x + 0.5 for x in a["log2_chunks"]]
    return _realcurve_void(root, _rc_mut(m), expect_clause="scope: roles=")


@case("realcurve4096", "an-incomplete-artifact-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["complete"] = False; a["run_finished_utc"] = None
    return _realcurve_void(root, _rc_mut(m), expect_clause="complete: complete=False")


@case("realcurve4096", "a-wrong-thread-count-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["environment"]["threads"] = 4
    return _realcurve_void(root, _rc_mut(m), expect_clause="environment: threads")


@case("realcurve4096", "a-launch-that-was-not-ok-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["launch_environment"]["ok"] = False; a["launch_environment"]["problems"] = ["load 3.1"]
    return _realcurve_void(root, _rc_mut(m), expect_clause="environment: launch_environment")


@case("realcurve4096", "a-scores-file-from-a-smoke-is-VOID", "fail")
def _(root):
    def m(a, s):
        s["smoke"] = True
    return _realcurve_void(root, _rc_mut(m), expect_clause="scores: the scores file")


@case("realcurve4096", "an-absent-scores-file-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, drop_scores=True, expect_clause="scores: the scores file is absent")


@case("realcurve4096", "an-absent-artifact-is-pending-not-a-pass", "fail")
def _(root):
    rc, out = _realcurve(root, drop_artifact=True)
    if rc != 2:
        return 0, out + " !! expected exit 2 (pending)"
    return rc, out


@case("realcurve4096", "a-NOT-RUN-file-is-pending-not-a-pass", "fail")
def _(root):
    rc, out = _realcurve(root, not_run={"schema": "raise-v1/realcurve_4096_not_run/1", "preregistration": "0023-realcurve-4096",
                                        "stage": "run", "reason": "r4_model read 0.13 against 0021's banked 0.1193", "utc": "2026-09-19T02:00:00Z",
                                        "smoke": False, "n_checkpoints": 4})
    if rc != 2 or "NOT RUN" not in out:
        return 0, out + " !! expected exit 2 with NOT RUN"
    return rc, out


@case("realcurve4096", "an-artifact-of-unexpected-shape-is-VOID-with-every-result-key", "fail")
def _(root):
    def m(a, s):
        a["fits"] = ["not", "a", "mapping"]
    rc, out = _realcurve_void(root, _rc_mut(m))
    v = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve_4096_verdict.json")))
    r23 = _rc_reader()
    missing = sorted(set(r23.RESULT_KEYS) - set(v))
    if missing:
        return 0, f"!! the exception path omitted result keys {missing}"
    return rc, out


@case("realcurve4096", "a-control-whose-partition-is-the-readers-own-literals-is-detected", "fail")
def _(root):
    shape = json.load(open(_RC_SHAPE, encoding="utf-8")); S_art = shape["artifact"]
    art, _ = _good_realcurve(); r23 = _rc_reader()
    art["partition"] = dict(r23.PARTITION)
    problems = _shape_problems(art, S_art, [("partition", art["partition"], S_art["partition"])], [], [])
    if not problems:
        return 0, "!! a partition taken from the reader's literals was not detected"
    return 1, problems[0]


@case("realcurve4096", "the-readers-record-requirements-hold-against-the-runners-own-banked-values", "pass")
def _(root):
    shape = json.load(open(_RC_SHAPE, encoding="utf-8")); r23 = _rc_reader()
    problems = []
    for name, rec in shape["artifact"]["fits"].items():
        role = "model" if name == "null" else name.split("_", 1)[1]
        fam = r23.RECIPES[role]["family"]; info = rec.get("fit_info")
        if rec["id"] != r23.RECIPES[role]["id"]:
            problems.append(f"{name}: id {rec['id']} is not the sealed {r23.RECIPES[role]['id']}")
        if fam in ("hgb", "logistic") and not isinstance(info.get("n_iter"), int):
            problems.append(f"{name}: {fam} without n_iter")
        if fam == "tree" and not (isinstance(info.get("depth"), int) and isinstance(info.get("n_leaves"), int)):
            problems.append(f"{name}: tree without depth/n_leaves")
        if sorted(rec["per_family"]) != sorted(r23.FAMILIES + ["ext:" + f for f in r23.EXT_FAMILIES]):
            problems.append(f"{name}: per_family keys {sorted(rec['per_family'])}")
        if any(not rf.get("probe_ok") for rf in rec.get("block_refills") or []):
            problems.append(f"{name}: a failed probe")
        want_rung = r23.N_RUNGS if name == "null" else (r23.REPLICATE if name.startswith(r23.REPLICATE + "_") else int(name[1:name.index("_")]))
        if rec.get("rung") != want_rung or rec.get("role") != ("null" if name == "null" else role):
            problems.append(f"{name}: rung/role fields {rec.get('rung')}/{rec.get('role')}")
    if problems:
        return 1, "; ".join(problems[:4])
    return 0, f"{len(shape['artifact']['fits'])} records satisfy the reader's per-record requirements on the runner's own values"


@case("realcurve4096", "the-control-artifact-is-built-from-the-runners-own-output-shape", "pass")
def _(root):
    shape = json.load(open(_RC_SHAPE, encoding="utf-8")); S_art = shape["artifact"]
    art, scores = _good_realcurve(); r23 = _rc_reader()
    blocks = [("partition", art["partition"], S_art["partition"]), ("corpus", art["corpus"], S_art["corpus"]),
              ("ext_corpus", art["ext_corpus"], S_art["ext_corpus"]), ("fit_corpus", art["fit_corpus"], S_art["fit_corpus"]),
              ("curve_spec", art["curve_spec"], S_art["curve_spec"]), ("bar", art["bar"], S_art["bar"]),
              ("slope_bootstrap", art["slope_bootstrap"], S_art["slope_bootstrap"]),
              ("replicate_rung_1", art["replicate_rung_1"], S_art["replicate_rung_1"]),
              ("replicate_rung_1.rung", art["replicate_rung_1"]["rung"], S_art["replicate_rung_1"]["rung"]),
              ("partition.replicate_rung_1", art["partition"]["replicate_rung_1"], S_art["partition"]["replicate_rung_1"]),
              ("scores (file)", {k: v for k, v in scores.items()}, dict(shape["scores"], per_example=None, eval_chunk_ids=None, ext_chunk_ids=None, ext_fam=None))]
    blocks += [(f"readings.{n}", art["readings"][n], S_art["readings"]["r1_model"]) for n in art["readings"]]
    blocks += [(f"curves.{r}", art["curves"][r], S_art["curves"][r]) for r in art["curves"]]
    blocks += [(f"partition.rungs[{i}]", a, b) for i, (a, b) in enumerate(zip(art["partition"]["rungs"], S_art["partition"]["rungs"]))]
    records = [(f"fits.{n}", art["fits"][n], S_art["fits"][n]) for n in art["fits"]]
    problems = _shape_problems(art, S_art, blocks, records,
                               [("PARTITION", r23.PARTITION, S_art["partition"]), ("CORPUS", r23.CORPUS, S_art["corpus"]),
                                ("EXT", r23.EXT, S_art["ext_corpus"]), ("FIT", r23.FIT, S_art["fit_corpus"])])
    if problems:
        return 1, "; ".join(problems[:4])
    return 0, (f"control and fixture agree both ways on {len(S_art)} artifact keys, {len(art['fits'])} records, every curve and every block; "
               f"every reader expectation is a key the runner writes")




def _rc_ckpt(root, art, scores, mutate=None):
    """Write the control's checkpoints into the scratch root so the reader's cross-check runs; mutate(ck_by_name) first if given."""
    d = os.path.join(root, "artifacts", "pivot", "realcurve_4096_ckpt"); os.makedirs(d, exist_ok=True)
    cks = {n: {"fingerprint": art["fits"][n]["fingerprint"], "record": dict(art["fits"][n]), "per_example": list(scores["per_example"][n])}
           for n in art["fits"]}
    if mutate:
        mutate(cks)
    for n, ck in cks.items():
        json.dump(ck, open(os.path.join(d, f"run_{n}.json"), "w"))


@case("realcurve4096", "two-roles-banking-the-same-per-example-vector-is-VOID", "fail")
def _(root):
    def m(a, s):
        # r2_model's vector becomes r3_model's, and every field that describes it is rebanked consistently
        s["per_example"]["r2_model"] = list(s["per_example"]["r3_model"])
        a["fits"]["r2_model"]["per_example_sha256"] = a["fits"]["r3_model"]["per_example_sha256"]
        for k in ("top1", "top1_non_gutenberg", "per_family"):
            a["fits"]["r2_model"][k] = a["fits"]["r3_model"][k]
        a["readings"]["r2_model"] = dict(a["readings"]["r3_model"])
        for k in ("ext_real_top1", "ext_real_correct", "ext_top1", "builder_eval_top1", "ext_per_family"):
            a[k]["r2_model"] = a[k]["r3_model"]
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: roles")


@case("realcurve4096", "a-completion-under-a-foreign-name-is-VOID", "fail")
def _(root):
    def m(a, s):
        done = [e for e in a["ledger"] if e["name"] == "run_r1_model" and e["event"] == "completed"][0]
        a["ledger"].append(dict(done, name="confirm_model"))
    return _realcurve_void(root, _rc_mut(m), expect_clause="order: the ledger carries completions under names outside")


@case("realcurve4096", "a-VOID-banks-no-slope-and-no-interval", "fail")
def _(root):
    def m(a, s):
        a["curves"]["logistic"]["end_to_end_gain"] = round(a["curves"]["logistic"]["end_to_end_gain"] + 0.0001, 4)
    rc, out = _realcurve_void(root, _rc_mut(m), expect_clause="curve: curves.logistic.end_to_end_gain")
    v = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve_4096_verdict.json")))
    if v.get("model_slope_per_doubling") is not None or v.get("model_slope_ci95") is not None or v.get("curves") is not None:
        return 0, out + " !! a VOID verdict banked a slope, an interval or a curve"
    return rc, out


@case("realcurve4096", "a-bootstrap-only-FLAT-names-the-interval-clause-in-its-meaning", "fail")
def _(root):
    rc, out = _realcurve_flat(root, "slope_bootstrap:", mode="disjoint", acc={"model": [0.1033, 0.1086, 0.114, 0.1193]})
    v = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve_4096_verdict.json")))
    m = v.get("meaning") or ""
    if rc != 0 and ("the interval clause" not in m or "do not agree on the rise" not in m or "would not have moved" in m):
        return 0, out + " !! the FLAT meaning does not name the interval clause"
    return rc, out


@case("realcurve4096", "a-replicate-rung-hash-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["replicate_rung_1"]["chunks_sha256"] = "b" * 64
    return _realcurve_void(root, _rc_mut(m), expect_clause="sealed set: partition.replicate_rung_1")


@case("realcurve4096", "a-missing-replicate-role-is-VOID", "fail")
def _(root):
    def m(a, s):
        del a["fits"]["rep1_model"]
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: the artifact banks roles outside the sealed order")


@case("realcurve4096", "a-banked-replicate-difference-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["replicate_rung_1"]["difference_from_rung_1"]["model"] = round(a["replicate_rung_1"]["difference_from_rung_1"]["model"] + 0.0001, 4)
    return _realcurve_void(root, _rc_mut(m), expect_clause="replicate: replicate_rung_1.difference_from_rung_1")


@case("realcurve4096", "a-replicate-banking-rung-1s-vector-is-VOID-as-a-shared-vector", "fail")
def _(root):
    def m(a, s):
        s["per_example"]["rep1_model"] = list(s["per_example"]["r1_model"])
        for k in ("per_example_sha256", "top1", "top1_non_gutenberg", "per_family"):
            a["fits"]["rep1_model"][k] = a["fits"]["r1_model"][k]
        a["readings"]["rep1_model"] = dict(a["readings"]["r1_model"])
        for k in ("ext_real_top1", "ext_real_correct", "ext_top1", "builder_eval_top1", "ext_per_family"):
            a[k]["rep1_model"] = a[k]["r1_model"]
        a["replicate_rung_1"]["readings"]["model"] = dict(a["replicate_rung_1"]["readings"]["model"],
                                                          ext_real_top1=a["readings"]["r1_model"]["ext_real_top1"],
                                                          ext_real_correct=a["readings"]["r1_model"]["ext_real_correct"],
                                                          builder_eval_top1=a["readings"]["r1_model"]["builder_eval_top1"],
                                                          ext_per_family={f: a["readings"]["r1_model"]["ext_per_family"][f] for f in a["ext_real_families"]})
        a["replicate_rung_1"]["difference_from_rung_1"]["model"] = 0.0
        a["replicate_rung_1"]["slope_with_replicate_at_rung_1"]["model"] = a["curves"]["model"]["slope_per_doubling"]
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: roles")


@case("realcurve4096", "a-banked-sensitivity-slope-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curves"]["model"]["slope_with_top_rung_at_reference"] = round(a["curves"]["model"]["slope_with_top_rung_at_reference"] + 0.00001, 6)
    return _realcurve_void(root, _rc_mut(m), expect_clause="curve: curves.model.slope_with_top_rung_at_reference")


@case("realcurve4096", "a-banked-rung-to-rung-gain-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curves"]["depth3_tree"]["rung_to_rung_gains"][1] = round(a["curves"]["depth3_tree"]["rung_to_rung_gains"][1] + 0.0001, 4)
    return _realcurve_void(root, _rc_mut(m), expect_clause="curve: curves.depth3_tree.rung_to_rung_gains")


@case("realcurve4096", "a-banked-per-family-slope-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curves"]["model"]["per_family_slope_per_doubling"]["py_src"] = round(a["curves"]["model"]["per_family_slope_per_doubling"]["py_src"] + 0.00001, 6)
    return _realcurve_void(root, _rc_mut(m), expect_clause="curve: curves.model.per_family_slope_per_doubling")


@case("realcurve4096", "a-bootstrap-block-without-its-unit-is-VOID", "fail")
def _(root):
    def m(a, s):
        del a["slope_bootstrap"]["unit"]
    return _realcurve_void(root, _rc_mut(m), expect_clause="curve: slope_bootstrap carries no unit")


@case("realcurve4096", "a-banked-paired-interval-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["slope_bootstrap"]["model_minus_logistic"]["ci95"][1] = round(a["slope_bootstrap"]["model_minus_logistic"]["ci95"][1] + 0.000001, 6)
    return _realcurve_void(root, _rc_mut(m), expect_clause="curve: slope_bootstrap.model_minus_logistic")


@case("realcurve4096", "eval-chunk-ids-with-two-entries-swapped-is-VOID", "fail")
def _(root):
    def m(a, s):
        ids = s["eval_chunk_ids"]; i = next(i for i in range(1, len(ids)) if ids[i] != ids[0]); ids[0], ids[i] = ids[i], ids[0]
    return _realcurve_void(root, _rc_mut(m), expect_clause="scores: eval_chunk_ids")


@case("realcurve4096", "ext-chunk-ids-with-two-entries-swapped-is-VOID", "fail")
def _(root):
    def m(a, s):
        ids = s["ext_chunk_ids"]; i = next(i for i in range(1, len(ids)) if ids[i] != ids[0]); ids[0], ids[i] = ids[i], ids[0]
    return _realcurve_void(root, _rc_mut(m), expect_clause="scores: ext_chunk_ids")


@case("realcurve4096", "ext-fam-with-two-entries-swapped-is-VOID", "fail")
def _(root):
    def m(a, s):
        f = s["ext_fam"]; i = next(i for i in range(1, len(f)) if f[i] != f[0]); f[0], f[i] = f[i], f[0]
    return _realcurve_void(root, _rc_mut(m), expect_clause="scores: ext_fam")


@case("realcurve4096", "a-scores-file-naming-different-arrays-is-VOID", "fail")
def _(root):
    def m(a, s):
        s["ext_arrays_sha256"]["X"] = "9" * 64
    return _realcurve_void(root, _rc_mut(m), expect_clause="scores: the scores file is not this run's")


@case("realcurve4096", "fit-info-by-name-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fit_info_by_name"] = {k: dict(v) for k, v in a["fit_info_by_name"].items()}     # a copy: the control aliases the records' dicts
        a["fit_info_by_name"]["r1_model"]["n_iter"] = 999
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: fit_info_by_name is not the records' fit_info")


@case("realcurve4096", "an-extra-banked-reading-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["readings"]["r5_model"] = dict(a["readings"]["r4_model"])
    return _realcurve_void(root, _rc_mut(m), expect_clause="readings: banked readings for")


@case("realcurve4096", "a-record-per-family-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["r2_logistic"]["per_family"] = dict(a["fits"]["r2_logistic"]["per_family"], code=0.5)
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: r2_logistic record per_family")


@case("realcurve4096", "a-record-with-the-wrong-stage-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["fits"]["r3_model"].__setitem__("stage", "confirmatory")), expect_clause="fit: r3_model stage")


@case("realcurve4096", "a-record-banked-infeasible-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a["fits"]["r3_model"].__setitem__("status", "infeasible_memory")), expect_clause="fit: r3_model status")


@case("realcurve4096", "a-record-with-a-wrong-environment-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["r4_logistic"]["environment"] = dict(a["fits"]["r4_logistic"]["environment"], sklearn="0.0.0")
    return _realcurve_void(root, _rc_mut(m), expect_clause="environment: r4_logistic sklearn")


@case("realcurve4096", "a-record-with-a-failed-block-probe-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["r2_model"]["block_refills"] = [{"probe_ok": False}]
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: r2_model banked a failed block probe")


@case("realcurve4096", "a-null-control-field-that-is-not-the-null-record-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["null_control"] = dict(a["fits"]["r4_model"])
    return _realcurve_void(root, _rc_mut(m), expect_clause="null control: null_control is not the banked null record")


@case("realcurve4096", "null-rows-off-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a.__setitem__("null_rows", a["null_rows"] - 1)), expect_clause="null control: null_rows")


@case("realcurve4096", "a-banked-reference-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["reference_top1"] = dict(a["reference_top1"], model=0.12)
    return _realcurve_void(root, _rc_mut(m), expect_clause="reproduction: the banked reference readings")


@case("realcurve4096", "a-banked-drift-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["reproduction_drift"] = dict(a["reproduction_drift"], logistic=0.001)
    return _realcurve_void(root, _rc_mut(m), expect_clause="reproduction: reproduction_drift")


@case("realcurve4096", "a-banked-shuffled-label-reading-off-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a.__setitem__("shuffled_label_accuracy_real", 0.0381)), expect_clause="null control: a banked shuffled-label")


@case("realcurve4096", "a-banked-summary-reading-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["ext_real_top1"] = dict(a["ext_real_top1"]); a["ext_real_top1"]["r2_model"] = round(a["ext_real_top1"]["r2_model"] + 0.0001, 4)
    return _realcurve_void(root, _rc_mut(m), expect_clause="readings: a banked summary reading for r2_model")


@case("realcurve4096", "a-select-stage-artifact-is-VOID", "fail")
def _(root):
    return _realcurve_void(root, _rc_mut(lambda a, s: a.__setitem__("stage", "select")), expect_clause="scope: stage")


@case("realcurve4096", "a-completion-event-with-a-wrong-fingerprint-is-VOID", "fail")
def _(root):
    def m(a, s):
        e = [e for e in a["ledger"] if e["name"] == "run_r2_model" and e["event"] == "completed"][0]; e["fingerprint"] = "ffffffffffffffff"
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: r2_model's completion event does not carry")


@case("realcurve4096", "a-completion-without-its-start-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["ledger"] = [e for e in a["ledger"] if not (e["name"] == "run_r3_logistic" and e["event"] == "started")]
    return _realcurve_void(root, _rc_mut(m), expect_clause="fit: r3_logistic has no 'started' event")


@case("realcurve4096", "a-malformed-artifact-file-is-pending-not-a-pass", "fail")
def _(root):
    art, scores = _good_realcurve()
    piv = os.path.join(root, "artifacts", "pivot"); os.makedirs(piv, exist_ok=True)
    json.dump(scores, open(os.path.join(piv, "realcurve_4096_scores.json"), "w"))
    open(os.path.join(piv, "realcurve_4096.json"), "w").write("{not json")
    shutil.copy(os.path.join(REPO, "tools", "readers", "realcurve4096_verdict.py"), os.path.join(root, "tools", "readers", "realcurve4096_verdict.py"))
    rc, out = run([PY, "tools/readers/realcurve4096_verdict.py"], root)
    if rc != 2:
        return 0, out + " !! expected exit 2 on a malformed artifact"
    return rc, out


@case("realcurve4096", "a-resumed-run-that-relogged-its-rung-bound-events-passes", "pass")
def _(root):
    def m(a, s):
        # a relaunch after a crash: every step re-logs rung_bound; the crashed fit restarts with attempt 2 and one completion
        L = a["ledger"]; extra = []
        for e in L:
            if e["event"] == "rung_bound":
                extra.append(dict(e, utc="2026-09-19T04:00:00Z"))
        i = next(i for i, e in enumerate(L) if e["name"] == "run_r2_model" and e["event"] == "started")
        L.insert(i + 1, dict(L[i], attempt=2, utc="2026-09-19T04:00:01Z"))
        a["ledger"] = L + extra; a["launch_number"] = 2
        a["launch_environment"] = dict(a["launch_environment"], loadavg_waited_seconds=45)
    return _realcurve(root, _rc_mut(m))


@case("realcurve4096", "committed-checkpoints-that-agree-pass", "pass")
def _(root):
    art, scores = _good_realcurve()
    _rc_ckpt(root, art, scores)
    rc, out = _realcurve(root)
    v = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve_4096_verdict.json")))
    if rc == 0 and v.get("checkpoints_cross_checked") != len(art["fits"]):
        return 1, out + f" !! checkpoints_cross_checked={v.get('checkpoints_cross_checked')}"
    return rc, out


@case("realcurve4096", "a-committed-checkpoint-with-a-different-vector-is-VOID", "fail")
def _(root):
    art, scores = _good_realcurve()

    def m(cks):
        v = cks["r2_model"]["per_example"]; v[0] = 1 - v[0]
    _rc_ckpt(root, art, scores, m)
    return _realcurve_void(root, expect_clause="checkpoint: r2_model's committed checkpoint")


@case("realcurve4096", "a-missing-committed-checkpoint-is-VOID", "fail")
def _(root):
    art, scores = _good_realcurve()
    _rc_ckpt(root, art, scores)
    os.remove(os.path.join(root, "artifacts", "pivot", "realcurve_4096_ckpt", "run_r1_logistic.json"))
    return _realcurve_void(root, expect_clause="checkpoint: r1_logistic has no checkpoint")


@case("realcurve4096", "the-exception-path-writes-the-normal-paths-key-set", "pass")
def _(root):
    rc, out = _realcurve(root)
    ok = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve_4096_verdict.json")))
    rc2, out2 = _realcurve_void(root, _rc_mut(lambda a, s: a.__setitem__("fits", ["not", "a", "mapping"])))
    bad = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve_4096_verdict.json")))
    if set(ok) != set(bad):
        return 1, f"!! key sets differ: normal-only {sorted(set(ok) - set(bad))}, exception-only {sorted(set(bad) - set(ok))}"
    return 0, f"{len(ok)} keys on both paths"


# ---------------------------------------------------------------- realcurve2_4096 gate (0024)
# The 0024 reader reads the SECOND decade of real plaintexts: 0021's three fixed recipes on 0023's four rungs plus three
# exact doublings of new pinned files nested on 0021's block, the second-decade slope per doubling of plaintexts with a
# paired cluster bootstrap, and the lead of the model over the logistic at the top rung read by a sealed rule into the
# verdict string. The control takes its SHAPE from tests/fixtures/realcurve2_runner_shape.json, a smoke run of
# tools/pivot/run_realcurve2.py itself, and its VALUES from the reader's sealed literals; the curves, the slopes, the
# bootstrap and the leads are computed with the runner's own functions on the control's vectors (OPERATING_RULES 4).
_RC2_SHAPE = os.path.join(REPO, "tests", "fixtures", "realcurve2_runner_shape.json")


def _rc2_reader():
    import importlib.util
    spec = importlib.util.spec_from_file_location("r24", os.path.join(REPO, "tools", "readers", "realcurve2_4096_verdict.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _rc2_runner():
    import importlib.util
    sys.path.insert(0, os.path.join(REPO, "tools", "pivot"))
    spec = importlib.util.spec_from_file_location("run_realcurve2", os.path.join(REPO, "tools", "pivot", "run_realcurve2.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


# Default rung accuracies on the real-family rows: rungs 1..4 are 0023's banked readings exactly (the reader requires
# them within 0.005), the second decade rises for every role, the model ahead at the top; the null at chance.
_RC2_ACC = {"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.128, 0.136, 0.143],
            "logistic": [0.0911, 0.0939, 0.1085, 0.1179, 0.124, 0.130, 0.136],
            "depth3_tree": [0.0834, 0.0901, 0.0915, 0.0929, 0.096, 0.099, 0.102]}


_RC2_SHIFT_ACC = {"model": 0.105, "logistic": 0.101, "depth3_tree": 0.085}   # the shift arm: below rung 4, never identical


def _good_realcurve2(acc=None, null_acc=None, mode="nested", shift_acc=None, lead_shift=False):
    """A complete, valid 0024 artifact set (artifact, scores). Shape AND key sets from the runner's own smoke output
    (tests/fixtures/realcurve2_runner_shape.json); only the values are the sealed run's, and the curves, slopes, bootstrap
    and leads are computed with tools/pivot/run_realcurve2.py's own functions on the control's vectors.

    acc overrides a role's seven rung accuracies on the real-family rows; null_acc the null's. Vectors are marked at
    CHUNK granularity with row precision inside the last chunk: 'nested' marks each family's leading chunks, so a higher
    rung's correct rows contain a lower rung's and every chunk resample agrees on the direction (and on the lead);
    'disjoint' rotates each rung's marked chunks to a different part of every family, so the rungs are correct on
    different plaintexts and a chunk bootstrap sees the rise the chunks do NOT agree on. lead_shift rotates ONLY the
    logistic's top-rung marking by half of every family's chunk list, so the top-rung lead interval genuinely straddles 0
    while the curve part is untouched (0024 pre-freeze review, reader lens, finding 1)."""
    r24 = _rc2_reader(); rr = _rc2_runner(); shape = json.load(open(_RC2_SHAPE, encoding="utf-8")); S_art = shape["artifact"]
    zeros = {k: 0 for k in ("pool_chunks_shared_with_ext", "eval_chunks_shared_with_ext", "fit_chunks_shared_with_ext",
                            "fit_chunks_shared_with_builder", "fit_source_chunks_shared_with_ext", "fit_rows_identical_to_a_scored_row",
                            "fit2_chunks_shared_with_ext", "fit2_chunks_shared_with_builder", "fit2_chunks_shared_with_fit",
                            "fit2_source_chunks_shared_with_ext", "fit2_source_chunks_shared_with_fit", "fit2_rows_identical_to_a_scored_row")}
    nulls = {"null_y_shuffled_sha256": r24.NULL_SHA_EXPECTED, "null_labels_permuted": True, "null_labels_same_multiset": True}
    part = _rf_sub(S_art["partition"], dict(r24.PARTITION, **zeros, **nulls), "partition", sealed_may_be_subset=True)
    spec = _rf_sub(S_art["curve_spec"], json.loads(json.dumps({"protocol": r24.PROTOCOL, "recipes": r24.RECIPES})), "curve_spec")
    assert _sha12(spec) == r24.CURVE_SHA256, "the reader's curve literals do not hash to its CURVE_SHA256"
    n_eval, n_ext, n_real = r24.PARTITION["n_eval_rows"], r24.N_EXT, r24.N_REAL
    fams = list(r24.EXT_FAMILIES); rpf = r24.EXT["rows_per_family"]
    fam_idx = []
    for k, f in enumerate(fams):
        fam_idx += [k] * rpf[f]
    fam_x = [fams[i] for i in fam_idx]
    ext_ids = [c for c, n in zip(r24.EXT_CHUNK_IDS, r24.EXT_ROWS_PER_CHUNK) for _ in range(n)]
    eval_ids = [c for c, n in zip(r24.EVAL_CHUNK_IDS, r24.EVAL_ROWS_PER_CHUNK) for _ in range(n)]
    fam_e = [r24.FAMILIES[c % 8] for c in eval_ids]
    env = dict(S_art["environment"], threads=3, nice=10)
    chunks_by_fam = {f: [] for f in fams}
    pos = 0
    for c, n in zip(r24.EXT_CHUNK_IDS, r24.EXT_ROWS_PER_CHUNK):
        chunks_by_fam[fam_x[pos]].append((pos, pos + n)); pos += n
    assert pos == n_ext
    accs = {r: list(v) for r, v in _RC2_ACC.items()}
    for r, v in (acc or {}).items():
        accs[r] = list(v)
    saccs = dict(_RC2_SHIFT_ACC, **(shift_acc or {}))
    n_rungs = r24.N_RUNGS; n_first = r24.N_FIRST; order = list(r24.ORDER); SH = r24.SHIFT

    def vec(role, k, a, idx=0):
        v = [0] * (n_eval + n_ext)
        rep = 0.19 if role != "null" else 0.038
        for i in range(int(round(rep * n_eval)) + idx):
            v[i] = 1
        for f in fams:
            want = int(round(a * rpf[f])); ch = chunks_by_fam[f]
            if lead_shift and role == "logistic" and k == n_rungs:
                start = len(ch) // 2
            elif mode == "nested" or role == "null" or k == SH:
                start = 0
            else:
                start = (k * len(ch) // (n_rungs + 1))
            j = 0
            while want > 0:
                s, e = ch[(start + j) % len(ch)]; take = min(want, e - s)
                for i in range(s, s + take):
                    v[n_eval + i] = 1
                want -= take; j += 1
        return v

    def name_parts(name):
        if name == "null":
            return n_rungs, "null"
        head, role = name.split("_", 1)
        return (SH if head == SH else int(head[1:])), role

    def rk_of(k):
        return part["shift_arm"] if k == SH else part["rungs"][k - 1]

    def stage_of(name):
        if name == "null":
            return "null"
        k = name_parts(name)[0]
        return "shift" if k == SH else ("curve" if k > n_first else "reproduction")

    def cand_of(name):
        return r24.RECIPES["model"] if name == "null" else r24.RECIPES[name_parts(name)[1]]

    def fp(name):
        k, role = name_parts(name); rk = rk_of(k)
        return r24.fingerprint(prereg=r24.PREREG, seed=r24.SEED, seed2=r24.SEED2, head=role, cand=cand_of(name), stage=stage_of(name),
                               rung=k, rows=rk["sorted_sha256"], eval=part["eval_idx_sha256"], ext=r24.EXT["arrays"]["X"]["sha256"],
                               fit=r24.FIT["arrays"]["X"]["sha256"], fit2=r24.FIT2["arrays"]["X"]["sha256"])

    def record(name, v):
        k, role = name_parts(name); c = cand_of(name); rk = rk_of(k); m4 = lambda xs: round(sum(xs) / len(xs), 4)  # noqa: E731
        fam_s = fam_e + ["ext:" + f for f in fam_x]
        ng = [v[i] for i in range(n_eval) if fam_e[i] != "gutenberg"] + v[n_eval:]
        sealed = {"id": c["id"], "head": role, "role": role, "rung": k, "family": c["family"], "params": dict(c.get("params", {})),
                  "scaled": bool(c.get("scaled", False)), "val": c.get("val"), "seed": r24.SEED, "params_sha256": _sha12(c),
                  "stage": stage_of(name), "n_fit_rows": rk["n_rows"], "fit_rows_sha256": rk["idx_sha256"],
                  "fit_rows_sorted_sha256": rk["sorted_sha256"], "n_rung_rows": rk["n_rows"], "n_rung_chunks": rk["n_chunks"],
                  "environment": dict(env), "interruptions_before_this_fit": 0, "status": "fit", "top1": m4(v), "top1_non_gutenberg": m4(ng),
                  "per_family": {f: m4([v[i] for i in range(len(v)) if fam_s[i] == f]) for f in sorted(set(fam_s))},
                  "fingerprint": fp(name), "per_example_sha256": hashlib.sha256(bytes(v)).hexdigest()}
        return _rf_sub(S_art["fits"][name], sealed, f"fits.{name}", sealed_may_be_subset=True)

    per_example, reads, fits = {}, {}, {}
    for idx, name in enumerate(order):
        k, role = name_parts(name)
        a = (null_acc if null_acc is not None else 0.037) if name == "null" else (saccs[role] if k == SH else accs[role][k - 1])
        v = vec(role, k, a, idx); per_example[name] = v
        reads[name] = _rc_readings(r24, v, fam_x, fam_e); fits[name] = record(name, v)
    ledger = []
    for i, nm in enumerate(order):
        k, _ = name_parts(nm); rk = rk_of(k)
        ledger += [{"name": f"run_{nm}", "fingerprint": fp(nm), "event": "rung_bound", "utc": f"2026-09-19T02:{i:02d}:00Z", "rss_gb": 1.0,
                    "pid": 1, "rung": k, "rung_sorted_sha256": rk["sorted_sha256"]},
                   {"name": f"run_{nm}", "fingerprint": fp(nm), "event": "started", "utc": f"2026-09-19T02:{i:02d}:01Z", "rss_gb": 1.0, "pid": 1, "attempt": 1},
                   {"name": f"run_{nm}", "fingerprint": fp(nm), "event": "completed", "utc": f"2026-09-19T02:{i:02d}:30Z", "rss_gb": 1.0, "pid": 1, "seconds": 1.0}]
    log2x = list(r24.LOG2X); log2s = log2x[n_first - 1:]; log2f = log2x[:n_first]

    def role_curve(role):
        pts = []
        for rk in part["rungs"]:
            rd = reads[f"r{rk['rung']}_{role}"]
            pts.append({"rung": rk["rung"], "decade": rk["decade"], "n_chunks": rk["n_chunks"], "n_rows": rk["n_rows"],
                        "log2_chunks": rk["log2_chunks"], "ext_real_top1": rd["ext_real_top1"], "ext_real_correct": rd["ext_real_correct"],
                        "builder_eval_top1": rd["builder_eval_top1"], "ext_per_family": {f: rd["ext_per_family"][f] for f in r24.REAL_FAMILIES}})
        ys = [p["ext_real_top1"] for p in pts]; ys2 = ys[n_first - 1:]; ys1 = ys[:n_first]
        return {"rungs": pts, "complete": True,
                "slope_per_doubling_second_decade": round(rr.ols_slope(log2s, ys2), 6),
                "slope_per_doubling_first_decade": round(rr.ols_slope(log2f, ys1), 6),
                "slope_per_doubling_both_decades": round(rr.ols_slope(log2x, ys), 6),
                "end_to_end_gain_second_decade": round(ys[-1] - ys[n_first - 1], 4),
                "end_to_end_gain_both_decades": round(ys[-1] - ys[0], 4),
                "rung_to_rung_gains": [round(ys[i + 1] - ys[i], 4) for i in range(len(ys) - 1)],
                "slope_second_decade_with_rung4_at_reference": round(rr.ols_slope(log2s, [float(r24.REFERENCE[role])] + ys2[1:]), 6),
                "per_family_slope_per_doubling_second_decade": {f: round(rr.ols_slope(log2s, [p["ext_per_family"][f] for p in pts[n_first - 1:]]), 6)
                                                                for f in r24.REAL_FAMILIES},
                "builder_eval_slope_per_doubling_second_decade": round(rr.ols_slope(log2s, [p["builder_eval_top1"] for p in pts[n_first - 1:]]), 6)}
    curves = {role: role_curve(role) for role in r24.ROLES}
    shift_block = {"arm": part["shift_arm"], "readings": {}, "difference_from_rung_4": {}, "difference_from_rung_5": {}, "note": S_art["shift_arm"]["note"]}
    for role in r24.ROLES:
        rs_ = reads[f"{SH}_{role}"]
        shift_block["readings"][role] = {"ext_real_top1": rs_["ext_real_top1"], "ext_real_correct": rs_["ext_real_correct"],
                                         "builder_eval_top1": rs_["builder_eval_top1"], "ext_per_family": {f: rs_["ext_per_family"][f] for f in r24.REAL_FAMILIES}}
        shift_block["difference_from_rung_4"][role] = round(rs_["ext_real_top1"] - reads[f"r{n_first}_{role}"]["ext_real_top1"], 4)
        shift_block["difference_from_rung_5"][role] = round(rs_["ext_real_top1"] - reads[f"r{n_first + 1}_{role}"]["ext_real_top1"], 4)
    ms, ls, ts = (curves[r]["slope_per_doubling_second_decade"] for r in ("model", "logistic", "depth3_tree"))
    import numpy as _np
    real_idx = [i for i in range(n_ext) if fam_x[i] in r24.REAL_FAMILIES]
    cid = _np.asarray([ext_ids[i] for i in real_idx], _np.int64)
    vecs = {n: _np.asarray([per_example[n][n_eval + i] for i in real_idx], _np.int8) for n in order if n != "null"}
    by_role = {role: [vecs[f"r{k}_{role}"] for k in range(n_first, n_rungs + 1)] for role in r24.ROLES}
    sl = rr.slope_bootstrap(by_role, log2s, cid, r24.N_BOOT, r24.BOOT_SEED)
    boot = {role: {"ci95": [round(float(_np.percentile(sl[role], 2.5)), 6), round(float(_np.percentile(sl[role], 97.5)), 6)],
                   "n_boot": r24.N_BOOT, "seed": r24.BOOT_SEED, "mean": round(float(sl[role].mean()), 6)} for role in r24.ROLES}
    for a_, b_ in (("model", "logistic"), ("model", "depth3_tree")):
        d = sl[a_] - sl[b_]
        boot[f"{a_}_minus_{b_}"] = {"ci95": [round(float(_np.percentile(d, 2.5)), 6), round(float(_np.percentile(d, 97.5)), 6)],
                                    "paired": True, "share_of_resamples_with_model_ahead": round(float((d > 0).mean()), 4)}
    boot["unit"] = S_art["slope_bootstrap"]["unit"]
    lead = {}
    for k in (n_rungs, n_first):
        for a_, b_ in (("model", "logistic"), ("model", "depth3_tree")):
            dv = rr.paired_lead_bootstrap(vecs[f"r{k}_{a_}"], vecs[f"r{k}_{b_}"], cid, r24.N_BOOT, r24.BOOT_SEED)
            lo, hi = round(float(_np.percentile(dv, 2.5)), 6), round(float(_np.percentile(dv, 97.5)), 6)
            lead[f"r{k}_{a_}_minus_{b_}"] = {
                "point": round(reads[f"r{k}_{a_}"]["ext_real_top1"] - reads[f"r{k}_{b_}"]["ext_real_top1"], 4), "ci95": [lo, hi],
                "n_boot": r24.N_BOOT, "seed": r24.BOOT_SEED, "share_of_resamples_with_model_ahead": round(float((dv > 0).mean()), 4),
                "reading": ("MODEL_LEADS" if lo > 0 else "LINEAR_LEADS" if hi < 0 else "NO_SEPARATION") if b_ == "logistic"
                           else ("MODEL_LEADS" if lo > 0 else "TREE_LEADS" if hi < 0 else "NO_SEPARATION")}
    lead["unit"] = S_art["lead_at_top"]["unit"]; lead["verdict_pair"] = f"r{n_rungs}_model_minus_logistic"
    top = f"r{n_rungs}_"; r4_ = f"r{n_first}_"
    top_top1 = {role: reads[top + role]["ext_real_top1"] for role in r24.ROLES}
    repro_first = {role: [reads[f"r{k}_{role}"]["ext_real_top1"] for k in range(1, n_first + 1)] for role in r24.ROLES}
    art = _shape_fill(S_art, {
        "schema_version": 1, "schema": "raise-v1/realcurve2_4096/1", "preregistration": r24.PREREG, "smoke": False,
        "curve_sha256": r24.CURVE_SHA256, "curve_spec": spec, "corpus": dict(r24.CORPUS), "ext_corpus": dict(r24.EXT),
        "fit_corpus": dict(r24.FIT), "fit2_corpus": dict(r24.FIT2), "partition": part, "n_classes": 26, "class_names": [],
        "chance_accuracy": r24.CHANCE, "stage": "run", "environment": dict(env),
        "launch_environment": {"env": dict(env), "loadavg_1_5_15": [0.1, 0.1, 0.1], "problems": [], "ok": True, "loadavg_waited_seconds": 0},
        "launch_number": 1, "complete": True, "missing_roles": [], "fits": fits, "readings": reads,
        "ext_real_top1": {n: reads[n]["ext_real_top1"] for n in order}, "ext_real_correct": {n: reads[n]["ext_real_correct"] for n in order},
        "ext_top1": {n: reads[n]["ext_top1"] for n in order}, "builder_eval_top1": {n: reads[n]["builder_eval_top1"] for n in order},
        "ext_per_family": {n: reads[n]["ext_per_family"] for n in order},
        "curves": curves, "roles": list(r24.ROLES), "n_rungs": n_rungs, "n_first_decade_rungs": n_first, "denominators": list(r24.DENOMINATORS),
        "doublings": r24.DOUBLINGS, "log2_chunks": log2x, "log2_chunks_second_decade": log2s,
        "model_slope_per_doubling": ms, "logistic_slope_per_doubling": ls, "depth3_tree_slope_per_doubling": ts,
        "slope_model_minus_logistic": round(ms - ls, 6), "slope_model_minus_depth3_tree": round(ms - ts, 6),
        "top_rung_top1": top_top1, "top_rung_model_minus_logistic": round(top_top1["model"] - top_top1["logistic"], 4),
        "top_rung_model_minus_depth3_tree": round(top_top1["model"] - top_top1["depth3_tree"], 4),
        "bar": {"slope_per_doubling": r24.BAR_SLOPE, "bootstrap_lower_bound_gt": r24.BOOT_LB, "n_boot": r24.N_BOOT, "bootstrap_seed": r24.BOOT_SEED,
                "lead_rule": r24.LEAD_RULE},
        "slope_bootstrap": boot, "lead_at_top": lead, "shift_arm": shift_block,
        "n_ext_real_rows": n_real, "n_ext_rows": n_ext, "n_eval_rows": n_eval,
        "ext_real_families": list(r24.REAL_FAMILIES), "ext_synthetic_families": list(r24.SYNTH_FAMILIES),
        "fit_families": list(r24.FIT_FAMILIES), "fit_rows_per_family": r24.FIT["rows_per_family"], "fit2_rows_per_family": r24.FIT2["rows_per_family"],
        "reference_top1": dict(r24.REFERENCE), "reproduction_top1": {role: reads[r4_ + role]["ext_real_top1"] for role in r24.ROLES},
        "reproduction_drift": {role: round(reads[r4_ + role]["ext_real_top1"] - r24.REFERENCE[role], 6) for role in r24.ROLES},
        "reference_first_decade": {r: list(r24.REFERENCE_FIRST[r]) for r in r24.ROLES}, "reproduction_first_decade": repro_first,
        "reproduction_first_decade_drift": {r: [round(a - b, 6) for a, b in zip(repro_first[r], r24.REFERENCE_FIRST[r])] for r in r24.ROLES},
        "shuffled_label_accuracy_ext": reads["null"]["ext_top1"], "shuffled_label_accuracy_eval": reads["null"]["builder_eval_top1"],
        "shuffled_label_accuracy_real": reads["null"]["ext_real_top1"],
        "null_control": fits["null"], "null_rows": part["rungs"][-1]["n_rows"],
        "fit_info_by_name": {n: fits[n]["fit_info"] for n in order}, "ledger": ledger,
        "cluster_ci95_informational": {}, "cost": {},
        "run_started_utc": "2026-09-19T02:00:00Z", "first_launch_utc": "2026-09-19T02:00:00Z", "run_finished_utc": "2026-09-19T03:00:00Z"}, "artifact")
    scores = {"schema": "raise-v1/realcurve2_4096_scores/1", "preregistration": r24.PREREG, "smoke": False,
              "n_eval_rows": n_eval, "n_ext_rows": n_ext, "eval_idx_sha256": part["eval_idx_sha256"],
              "eval_chunk_ids": eval_ids, "ext_chunk_ids": ext_ids, "ext_fam": fam_idx, "ext_families": fams,
              "ext_arrays_sha256": {k: v["sha256"] for k, v in r24.EXT["arrays"].items()},
              "fit_arrays_sha256": {k: v["sha256"] for k, v in r24.FIT["arrays"].items()},
              "fit2_arrays_sha256": {k: v["sha256"] for k, v in r24.FIT2["arrays"].items()},
              "layout": "each per_example vector is [sealed evaluation rows (n_eval_rows)] + [extension rows (n_ext_rows)]",
              "per_example": per_example}
    return art, scores


def _realcurve2(root, mutate=None, drop_artifact=False, drop_scores=False, not_run=None, expect="SECOND_DECADE_RISES_MODEL_LEADS", **kw):
    art, scores = _good_realcurve2(**kw)
    if mutate:
        r = mutate(art, scores)
        if r is not None:
            art = r
    piv = os.path.join(root, "artifacts", "pivot"); os.makedirs(piv, exist_ok=True)
    if not drop_scores:
        json.dump(scores, open(os.path.join(piv, "realcurve2_4096_scores.json"), "w"))
    if not drop_artifact:
        json.dump(art, open(os.path.join(piv, "realcurve2_4096.json"), "w"))
    if not_run is not None:
        json.dump(not_run, open(os.path.join(piv, "realcurve2_4096_not_run.json"), "w"))
    shutil.copy(os.path.join(REPO, "tools", "readers", "realcurve2_4096_verdict.py"),
                os.path.join(root, "tools", "readers", "realcurve2_4096_verdict.py"))
    rc, out = run([PY, "tools/readers/realcurve2_4096_verdict.py"], root)
    if rc != 0:
        return rc, out
    v = json.load(open(os.path.join(piv, "realcurve2_4096_verdict.json")))
    ok = v["verdict"] == expect
    return (0 if ok else 1), (f"verdict={v['verdict']} lead={v.get('lead_reading')} slope={v.get('model_slope_per_doubling')} "
                              f"ci={v.get('model_slope_ci95')} rungs={v.get('model_real_top1_by_rung')} validity={v['validity_failed_clauses'][:6]} "
                              f"slope_failed={v['slope_failed_clauses']}")


def _realcurve2_void(root, mutate=None, expect_clause=None, **kw):
    rc, out = _realcurve2(root, mutate, **kw)
    if rc != 0 and "verdict=VOID" not in out and "No verdict emitted" not in out:
        return 0, out + " !! detected but not as VOID"
    if expect_clause and expect_clause not in out:
        return 0, out + f" !! VOID for another reason than {expect_clause!r}"
    return rc, out


def _realcurve2_flat(root, expect_clause, **kw):
    rc, out = _realcurve2(root, **kw)
    if rc != 0 and ("verdict=SECOND_DECADE_FLAT" not in out or "validity=[]" not in out or expect_clause not in out):
        return 0, out + f" !! expected a clean SECOND_DECADE_FLAT on {expect_clause!r}"
    return rc, out


def _rc2_mut(fn):
    def m(art, scores):
        fn(art, scores)
    return m


def _rc2_ckpt(root, art, scores, mutate=None):
    """The control's checkpoints as the runner writes them: run_fit's record (WITHOUT the six fields fit_role adds to the banked
    record afterwards), the fingerprint and the vector; mutate(ck_by_name) first if given."""
    d = os.path.join(root, "artifacts", "pivot", "realcurve2_4096_ckpt"); os.makedirs(d, exist_ok=True)
    added = ("fingerprint", "rung", "role", "n_rung_rows", "n_rung_chunks", "per_example_sha256")
    cks = {n: {"fingerprint": art["fits"][n]["fingerprint"], "record": {k: v for k, v in art["fits"][n].items() if k not in added},
               "per_example": list(scores["per_example"][n])} for n in art["fits"]}
    if mutate:
        mutate(cks)
    for n, ck in cks.items():
        json.dump(ck, open(os.path.join(d, f"run_{n}.json"), "w"))


_RC2_G = "realcurve2_4096"


@case(_RC2_G, "control-rising-second-decade-with-the-model-ahead-is-SECOND_DECADE_RISES_MODEL_LEADS", "pass")
def _(root):
    rc, out = _realcurve2(root)
    if rc == 0 and "validity=[]" not in out:
        return 1, out
    return rc, out


@case(_RC2_G, "control-linear-rule-ahead-at-the-top-is-SECOND_DECADE_RISES_LINEAR_LEADS", "pass")
def _(root):
    return _realcurve2(root, acc={"logistic": [0.0911, 0.0939, 0.1085, 0.1179, 0.130, 0.142, 0.152]}, expect="SECOND_DECADE_RISES_LINEAR_LEADS")


@case(_RC2_G, "control-model-and-logistic-equal-at-the-top-is-NO_SEPARATION-never-equal", "pass")
def _(root):
    rc, out = _realcurve2(root, acc={"logistic": [0.0911, 0.0939, 0.1085, 0.1179, 0.130, 0.137, 0.143]}, expect="SECOND_DECADE_RISES_NO_SEPARATION")
    if rc == 0:
        v = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve2_4096_verdict.json")))
        if "equal" in (v.get("meaning") or "").split("never read as 'equal'")[0].split("not separated")[-1]:
            return 1, out + " !! the meaning reads the pair as equal"
    return rc, out


@case(_RC2_G, "control-a-flat-second-decade-with-the-linear-rule-ahead-is-SECOND_DECADE_FLAT_LINEAR_LEADS", "pass")
def _(root):
    return _realcurve2(root, acc={"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.1193, 0.1193, 0.1193],
                                  "logistic": [0.0911, 0.0939, 0.1085, 0.1179, 0.124, 0.130, 0.136]}, expect="SECOND_DECADE_FLAT_LINEAR_LEADS")


@case(_RC2_G, "control-slope-just-above-the-bar-passes", "pass")
def _(root):
    a = {"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.1245, 0.1298, 0.1350], "logistic": [0.0911, 0.0939, 0.1085, 0.1179, 0.121, 0.124, 0.127]}
    art, _ = _good_realcurve2(acc=a)
    if not (0.005 <= art["model_slope_per_doubling"] < 0.0062):
        return 1, f"!! control slope {art['model_slope_per_doubling']} is not just above the bar"
    return _realcurve2(root, acc=a)


@case(_RC2_G, "a-model-second-decade-slope-just-below-the-bar-is-SECOND_DECADE_FLAT", "fail")
def _(root):
    a = {"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.1235, 0.1278, 0.1320]}
    art, _ = _good_realcurve2(acc=a)
    if not (0.0035 < art["model_slope_per_doubling"] < 0.005):
        return 0, f"!! control slope {art['model_slope_per_doubling']} is not just below the bar"
    return _realcurve2_flat(root, "slope:", acc=a)


@case(_RC2_G, "a-flat-second-decade-is-SECOND_DECADE_FLAT", "fail")
def _(root):
    return _realcurve2_flat(root, "slope:", acc={"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.1193, 0.1193, 0.1193]})


@case(_RC2_G, "a-falling-second-decade-is-SECOND_DECADE_FLAT", "fail")
def _(root):
    return _realcurve2_flat(root, "slope:", acc={"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.115, 0.112, 0.110]})


@case(_RC2_G, "a-first-decade-rise-alone-does-not-carry-the-verdict", "fail")
def _(root):
    # the first decade reproduces 0023's rise; the second decade is flat: FLAT, whatever the both-decade slope says
    rc, out = _realcurve2_flat(root, "slope:", acc={"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.1193, 0.1193, 0.1193]})
    if rc != 0:
        v = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve2_4096_verdict.json")))
        if (v.get("flags") or {}).get("both_decades_slope_per_doubling", {}).get("model", 0) <= 0:
            return 0, out + " !! the control's both-decade slope is not positive"
    return rc, out


@case(_RC2_G, "a-rise-the-scored-chunks-do-not-agree-on-fails-the-bootstrap-clause-alone", "fail")
def _(root):
    a = {"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.1245, 0.1298, 0.1350]}
    art, _ = _good_realcurve2(mode="disjoint", acc=a)
    if art["model_slope_per_doubling"] < 0.005 or art["slope_bootstrap"]["model"]["ci95"][0] > 0:
        return 0, f"!! control slope {art['model_slope_per_doubling']} ci {art['slope_bootstrap']['model']['ci95']} does not isolate the bootstrap clause"
    rc, out = _realcurve2_flat(root, "slope_bootstrap:", mode="disjoint", acc=a)
    if rc != 0 and "slope: the model" in out:
        return 0, out + " !! the slope clause failed too"
    return rc, out


@case(_RC2_G, "a-rung-4-model-reading-0.006-off-0021-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, expect_clause="reproduction: r4_model", acc={"model": [0.0974, 0.1065, 0.1139, 0.1253, 0.128, 0.136, 0.143]})


@case(_RC2_G, "a-rung-4-logistic-reading-0.006-off-0021-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, expect_clause="reproduction: r4_logistic", acc={"logistic": [0.0911, 0.0939, 0.1085, 0.1239, 0.128, 0.132, 0.136]})


@case(_RC2_G, "a-rung-4-tree-reading-0.006-off-0021-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, expect_clause="reproduction: r4_depth3_tree", acc={"depth3_tree": [0.0834, 0.0901, 0.0915, 0.0869, 0.096, 0.099, 0.102]})


@case(_RC2_G, "a-rung-1-model-reading-0.006-off-0023-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, expect_clause="reproduction: r1_model", acc={"model": [0.1034, 0.1065, 0.1139, 0.1193, 0.128, 0.136, 0.143]})


@case(_RC2_G, "a-rung-3-logistic-reading-0.006-off-0023-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, expect_clause="reproduction: r3_logistic", acc={"logistic": [0.0911, 0.0939, 0.1025, 0.1179, 0.124, 0.130, 0.136]})


@case(_RC2_G, "first-decade-readings-within-tolerance-pass", "pass")
def _(root):
    return _realcurve2(root, acc={"model": [0.1014, 0.1025, 0.1179, 0.1233, 0.128, 0.136, 0.143]})


@case(_RC2_G, "a-null-control-above-chance-plus-tolerance-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, expect_clause="null control: shuffled labels", null_acc=0.05)


@case(_RC2_G, "a-null-label-array-that-is-not-the-sealed-one-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["partition"].__setitem__("null_y_shuffled_sha256", "0" * 64)),
                            expect_clause="null control: the permuted label array")


@case(_RC2_G, "null-labels-not-banked-as-a-permutation-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["partition"].__setitem__("null_labels_same_multiset", False)),
                            expect_clause="null control: the null labels")


@case(_RC2_G, "a-partition-without-its-null-rule-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["partition"].__delitem__("null_rule")), expect_clause="null control: the partition carries no null_rule")


@case(_RC2_G, "a-smoke-artifact-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a.__setitem__("smoke", True)), expect_clause="scope: smoke")


@case(_RC2_G, "a-wrong-preregistration-id-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a.__setitem__("preregistration", "0023-realcurve-4096")), expect_clause="scope: preregistration")


@case(_RC2_G, "a-protocol-with-one-changed-denominator-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curve_spec"]["protocol"]["denominators"] = [16, 4, 2, 1]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="scope:")


@case(_RC2_G, "a-protocol-with-a-changed-doubling-count-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curve_spec"]["protocol"]["doublings"] = 4
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="scope:")


@case(_RC2_G, "a-recipe-off-the-sealed-three-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curve_spec"]["recipes"]["model"]["params"]["learning_rate"] = 0.31
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="scope:")


@case(_RC2_G, "a-fit-record-on-an-off-recipe-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["r6_model"]["params"] = dict(a["fits"]["r6_model"]["params"], max_leaf_nodes=7)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: r6_model is not the sealed")


@case(_RC2_G, "a-builder-cache-x-hash-off-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["corpus"].__setitem__("cache_X_sha256", "f" * 64)), expect_clause="scope: corpus.cache_X_sha256")


@case(_RC2_G, "an-extension-corpus-block-off-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["ext_corpus"].__setitem__("n_rows", a["ext_corpus"]["n_rows"] + 1)),
                            expect_clause="evaluation corpus: ext_corpus.n_rows")


@case(_RC2_G, "a-fit-corpus-array-hash-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fit_corpus"]["arrays"]["X"]["sha256"] = "e" * 64
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit corpus: fit_corpus.arrays")


@case(_RC2_G, "a-second-decade-corpus-array-hash-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fit2_corpus"]["arrays"]["X"]["sha256"] = "e" * 64
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="second-decade corpus: fit2_corpus.arrays")


@case(_RC2_G, "a-second-decade-corpus-chunk-count-off-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["fit2_corpus"].__setitem__("n_chunks", a["fit2_corpus"]["n_chunks"] - 1)),
                            expect_clause="second-decade corpus: fit2_corpus.n_chunks")


@case(_RC2_G, "a-fit-block-index-hash-off-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["partition"].__setitem__("fit_idx_sha256", "d" * 64)), expect_clause="sealed set: partition.fit_idx_sha256")


@case(_RC2_G, "a-rungs-row-count-off-by-one-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["rungs"][5]["n_rows"] += 1
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="sealed set: partition.rungs")


@case(_RC2_G, "a-rungs-chunk-set-hash-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["rungs"][0]["chunks_sha256"] = "c" * 64
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="sealed set: partition.rungs")


@case(_RC2_G, "a-new-chunk-set-hash-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["rungs"][6]["new_chunks_sha256"] = "c" * 64
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="sealed set: partition.rungs")


@case(_RC2_G, "a-rung-with-one-new-chunk-too-many-is-VOID", "fail")
def _(root):
    def m(a, s):
        r = a["partition"]["rungs"][4]; r["new_chunks_per_family"] = dict(r["new_chunks_per_family"], c_src=r["new_chunks_per_family"]["c_src"] + 1)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="sealed set: partition.rungs")


@case(_RC2_G, "rungs-banked-as-not-nested-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["partition"].__setitem__("rungs_nested", False)), expect_clause="partition.rungs_nested")


@case(_RC2_G, "a-rung-4-that-is-not-the-fit-block-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["partition"].__setitem__("rung4_is_fit_block", False)), expect_clause="partition.rung4_is_fit_block")


@case(_RC2_G, "inexact-doublings-are-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["partition"].__setitem__("second_decade_exact_doublings", False)),
                            expect_clause="partition.second_decade_exact_doublings")


@case(_RC2_G, "a-short-pool-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["partition"].__setitem__("pool_short", {"py_src": {"needed": 4704, "in_pool": 4700}})),
                            expect_clause="partition.pool_short")


@case(_RC2_G, "pool-counts-off-are-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["pool_chunks_with_rows_per_family"] = dict(a["partition"]["pool_chunks_with_rows_per_family"], c_src=1)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="sealed set: partition.pool_chunks_with_rows_per_family")


@case(_RC2_G, "one-fit-row-identical-to-a-scored-row-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["partition"].__setitem__("fit_rows_identical_to_a_scored_row", 1)),
                            expect_clause="leakage: partition.fit_rows_identical_to_a_scored_row")


@case(_RC2_G, "one-second-decade-row-identical-to-a-scored-row-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["partition"].__setitem__("fit2_rows_identical_to_a_scored_row", 1)),
                            expect_clause="leakage: partition.fit2_rows_identical_to_a_scored_row")


@case(_RC2_G, "a-second-decade-chunk-shared-with-0021s-block-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["partition"].__setitem__("fit2_chunks_shared_with_fit", 1)),
                            expect_clause="leakage: partition.fit2_chunks_shared_with_fit")


@case(_RC2_G, "a-second-decade-source-hash-shared-with-the-scored-corpus-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["partition"].__setitem__("fit2_source_chunks_shared_with_ext", 1)),
                            expect_clause="leakage: partition.fit2_source_chunks_shared_with_ext")


@case(_RC2_G, "a-record-fitted-on-the-wrong-rung-is-VOID", "fail")
def _(root):
    def m(a, s):
        r5, r6 = a["fits"]["r5_model"], a["fits"]["r6_model"]
        r5["fit_rows_sha256"], r5["fit_rows_sorted_sha256"], r5["n_fit_rows"] = r6["fit_rows_sha256"], r6["fit_rows_sorted_sha256"], r6["n_fit_rows"]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: r5_model was not fitted on sealed rung 5")


@case(_RC2_G, "a-missing-rung-role-is-VOID", "fail")
def _(root):
    def m(a, s):
        del a["fits"]["r7_logistic"]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: the artifact banks roles outside the sealed order")


@case(_RC2_G, "an-extra-role-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["r8_model"] = dict(a["fits"]["r7_model"])
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: the artifact banks roles outside the sealed order")


@case(_RC2_G, "a-fingerprint-off-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["fits"]["r7_model"].__setitem__("fingerprint", "0123456789abcdef")),
                            expect_clause="fit: r7_model fingerprint")


@case(_RC2_G, "a-role-completed-twice-is-VOID", "fail")
def _(root):
    def m(a, s):
        done = [e for e in a["ledger"] if e["name"] == "run_r1_model" and e["event"] == "completed"][0]
        a["ledger"].append(dict(done))
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: r1_model has 2 ledger completions")


@case(_RC2_G, "completions-out-of-the-sealed-order-are-VOID", "fail")
def _(root):
    def m(a, s):
        L = a["ledger"]; mine = [e for e in L if e["name"] == "run_r7_model"]; rest = [e for e in L if e["name"] != "run_r7_model"]
        j = max(i for i, e in enumerate(rest) if e["name"] == "run_r1_depth3_tree") + 1
        a["ledger"] = rest[:j] + mine + rest[j:]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="order")


@case(_RC2_G, "a-rung-bound-event-naming-the-wrong-rung-is-VOID", "fail")
def _(root):
    def m(a, s):
        e = [e for e in a["ledger"] if e["name"] == "run_r5_logistic" and e["event"] == "rung_bound"][0]; e["rung"] = 6
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: r5_logistic has no 'rung_bound' event")


@case(_RC2_G, "a-per-example-vector-one-row-short-is-VOID", "fail")
def _(root):
    def m(a, s):
        s["per_example"]["r6_model"] = s["per_example"]["r6_model"][:-1]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: r6_model per-example vector")


@case(_RC2_G, "a-per-example-hash-off-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["fits"]["r6_model"].__setitem__("per_example_sha256", "a" * 64)),
                            expect_clause="fit: r6_model per_example_sha256")


@case(_RC2_G, "a-record-top1-off-by-0.0001-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["fits"]["r5_depth3_tree"].__setitem__("top1", round(a["fits"]["r5_depth3_tree"]["top1"] + 0.0001, 4))),
                            expect_clause="fit: r5_depth3_tree record top1")


@case(_RC2_G, "a-banked-rung-reading-off-by-0.0001-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["readings"]["r7_model"]["ext_real_top1"] = round(a["readings"]["r7_model"]["ext_real_top1"] + 0.0001, 4)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="readings: r7_model.ext_real_top1")


@case(_RC2_G, "a-banked-curve-point-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curves"]["model"]["rungs"][6]["ext_real_top1"] = round(a["curves"]["model"]["rungs"][6]["ext_real_top1"] + 0.0001, 4)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: curves.model.rungs")


@case(_RC2_G, "a-banked-second-decade-slope-off-by-0.00001-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curves"]["model"]["slope_per_doubling_second_decade"] = round(a["curves"]["model"]["slope_per_doubling_second_decade"] + 0.00001, 6)
        a["model_slope_per_doubling"] = a["curves"]["model"]["slope_per_doubling_second_decade"]
        a["slope_model_minus_logistic"] = round(a["model_slope_per_doubling"] - a["logistic_slope_per_doubling"], 6)
        a["slope_model_minus_depth3_tree"] = round(a["model_slope_per_doubling"] - a["depth3_tree_slope_per_doubling"], 6)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: curves.model.slope_per_doubling_second_decade")


@case(_RC2_G, "a-banked-first-decade-slope-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curves"]["logistic"]["slope_per_doubling_first_decade"] = round(a["curves"]["logistic"]["slope_per_doubling_first_decade"] + 0.00001, 6)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: curves.logistic.slope_per_doubling_first_decade")


@case(_RC2_G, "a-banked-both-decade-slope-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curves"]["depth3_tree"]["slope_per_doubling_both_decades"] = round(a["curves"]["depth3_tree"]["slope_per_doubling_both_decades"] + 0.00001, 6)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: curves.depth3_tree.slope_per_doubling_both_decades")


@case(_RC2_G, "a-top-level-slope-that-is-not-the-curves-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a.__setitem__("model_slope_per_doubling", 0.02)), expect_clause="curve: a banked top-level slope")


@case(_RC2_G, "a-top-level-slope-that-is-the-first-decades-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["model_slope_per_doubling"] = a["curves"]["model"]["slope_per_doubling_first_decade"]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: a banked top-level slope")


@case(_RC2_G, "a-slope-difference-that-is-not-model-minus-logistic-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a.__setitem__("slope_model_minus_logistic", 0.0)), expect_clause="curve: a banked slope difference")


@case(_RC2_G, "a-banked-top-rung-reading-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["top_rung_top1"] = dict(a["top_rung_top1"], model=round(a["top_rung_top1"]["model"] + 0.0001, 4))
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: the banked top-rung readings")


@case(_RC2_G, "a-banked-top-rung-difference-off-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a.__setitem__("top_rung_model_minus_logistic", 0.0)), expect_clause="curve: the banked top-rung readings")


@case(_RC2_G, "a-banked-bootstrap-interval-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["slope_bootstrap"]["model"]["ci95"][0] = round(a["slope_bootstrap"]["model"]["ci95"][0] - 0.000001, 6)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: slope_bootstrap.model")


@case(_RC2_G, "a-banked-paired-difference-interval-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["slope_bootstrap"]["model_minus_logistic"]["share_of_resamples_with_model_ahead"] = 0.5
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: slope_bootstrap.model_minus_logistic")


@case(_RC2_G, "a-bootstrap-block-without-its-unit-is-VOID", "fail")
def _(root):
    def m(a, s):
        del a["slope_bootstrap"]["unit"]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: slope_bootstrap carries no unit")


@case(_RC2_G, "a-banked-lead-interval-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["lead_at_top"]["r7_model_minus_logistic"]["ci95"][0] = round(a["lead_at_top"]["r7_model_minus_logistic"]["ci95"][0] - 0.000001, 6)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="lead: lead_at_top.r7_model_minus_logistic")


@case(_RC2_G, "a-banked-lead-reading-that-contradicts-its-interval-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["lead_at_top"]["r7_model_minus_logistic"]["reading"] = "NO_SEPARATION"
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="lead: lead_at_top.r7_model_minus_logistic")


@case(_RC2_G, "a-banked-rung-4-lead-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["lead_at_top"]["r4_model_minus_depth3_tree"]["point"] = 0.0
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="lead: lead_at_top.r4_model_minus_depth3_tree")


@case(_RC2_G, "a-lead-block-naming-another-verdict-pair-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["lead_at_top"].__setitem__("verdict_pair", "r4_model_minus_logistic")),
                            expect_clause="lead: lead_at_top carries no unit or names a verdict pair")


@case(_RC2_G, "a-bar-banked-lower-than-sealed-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["bar"].__setitem__("slope_per_doubling", 0.001)), expect_clause="scope: bar=")


@case(_RC2_G, "a-bar-with-a-different-lead-rule-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["bar"].__setitem__("lead_rule", "the point estimate's sign")), expect_clause="scope: bar=")


@case(_RC2_G, "log2-plaintexts-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["log2_chunks"] = [x + 0.5 for x in a["log2_chunks"]]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="scope: roles=")


@case(_RC2_G, "an-incomplete-artifact-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["complete"] = False; a["run_finished_utc"] = None
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="complete: complete=False")


@case(_RC2_G, "a-wrong-thread-count-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["environment"]["threads"] = 4
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="environment: threads")


@case(_RC2_G, "a-launch-that-was-not-ok-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["launch_environment"]["ok"] = False; a["launch_environment"]["problems"] = ["load 3.1"]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="environment: launch_environment")


@case(_RC2_G, "a-scores-file-from-a-smoke-is-VOID", "fail")
def _(root):
    def m(a, s):
        s["smoke"] = True
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="scores: the scores file")


@case(_RC2_G, "a-scores-file-naming-a-different-second-decade-corpus-is-VOID", "fail")
def _(root):
    def m(a, s):
        s["fit2_arrays_sha256"]["X"] = "9" * 64
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="scores: the scores file is not this run's")


@case(_RC2_G, "an-absent-scores-file-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, drop_scores=True, expect_clause="scores: the scores file is absent")


@case(_RC2_G, "an-absent-artifact-is-pending-not-a-pass", "fail")
def _(root):
    rc, out = _realcurve2(root, drop_artifact=True)
    if rc != 2:
        return 0, out + " !! expected exit 2 (pending)"
    return rc, out


@case(_RC2_G, "a-NOT-RUN-file-is-pending-not-a-pass", "fail")
def _(root):
    rc, out = _realcurve2(root, not_run={"schema": "raise-v1/realcurve2_4096_not_run/1", "preregistration": "0024-realcurve2-4096",
                                         "stage": "run", "reason": "r4_model read 0.13 against 0023's banked 0.1193", "utc": "2026-09-19T02:00:00Z",
                                         "smoke": False, "n_checkpoints": 4})
    if rc != 2 or "NOT RUN" not in out:
        return 0, out + " !! expected exit 2 with NOT RUN"
    return rc, out


@case(_RC2_G, "an-artifact-of-unexpected-shape-is-VOID-with-every-result-key", "fail")
def _(root):
    def m(a, s):
        a["partition"] = "not a mapping"          # part.get raises inside read(): the exception path, not the normal one
    rc, out = _realcurve2_void(root, _rc2_mut(m))
    v = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve2_4096_verdict.json")))
    r24 = _rc2_reader()
    missing = sorted(set(r24.RESULT_KEYS) - set(v))
    if missing:
        return 0, f"!! the exception path omitted result keys {missing}"
    if not (v["validity_failed_clauses"] and v["validity_failed_clauses"][0].startswith("reader: artifact of unexpected shape")):
        return 0, out + " !! the exception path was not taken"
    return rc, out


@case(_RC2_G, "fits-that-are-not-a-mapping-are-VOID-on-the-normal-path", "fail")
def _(root):
    def m(a, s):
        a["fits"] = ["not", "a", "mapping"]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: fits is not a mapping")


@case(_RC2_G, "a-control-whose-partition-is-the-readers-own-literals-is-detected", "fail")
def _(root):
    shape = json.load(open(_RC2_SHAPE, encoding="utf-8")); S_art = shape["artifact"]
    art, _ = _good_realcurve2(); r24 = _rc2_reader()
    art["partition"] = dict(r24.PARTITION)
    problems = _shape_problems(art, S_art, [("partition", art["partition"], S_art["partition"])], [], [])
    if not problems:
        return 0, "!! a partition taken from the reader's literals was not detected"
    return 1, problems[0]


@case(_RC2_G, "the-readers-record-requirements-hold-against-the-runners-own-banked-values", "pass")
def _(root):
    shape = json.load(open(_RC2_SHAPE, encoding="utf-8")); r24 = _rc2_reader()
    problems = []
    for name, rec in shape["artifact"]["fits"].items():
        role = "model" if name == "null" else name.split("_", 1)[1]
        fam = r24.RECIPES[role]["family"]; info = rec.get("fit_info")
        if rec["id"] != r24.RECIPES[role]["id"]:
            problems.append(f"{name}: id {rec['id']} is not the sealed {r24.RECIPES[role]['id']}")
        if fam in ("hgb", "logistic") and not isinstance(info.get("n_iter"), int):
            problems.append(f"{name}: {fam} without n_iter")
        if fam == "tree" and not (isinstance(info.get("depth"), int) and isinstance(info.get("n_leaves"), int)):
            problems.append(f"{name}: tree without depth/n_leaves")
        if sorted(rec["per_family"]) != sorted(r24.FAMILIES + ["ext:" + f for f in r24.EXT_FAMILIES]):
            problems.append(f"{name}: per_family keys {sorted(rec['per_family'])}")
        if any(not rf.get("probe_ok") for rf in rec.get("block_refills") or []):
            problems.append(f"{name}: a failed probe")
        head = None if name == "null" else name[:name.index("_")]
        want_rung = r24.N_RUNGS if name == "null" else (r24.SHIFT if head == r24.SHIFT else int(head[1:]))
        want_stage = "null" if name == "null" else ("shift" if want_rung == r24.SHIFT else ("curve" if want_rung > r24.N_FIRST else "reproduction"))
        if rec.get("rung") != want_rung or rec.get("role") != ("null" if name == "null" else role) or rec.get("stage") != want_stage:
            problems.append(f"{name}: rung/role/stage fields {rec.get('rung')}/{rec.get('role')}/{rec.get('stage')}")
    if problems:
        return 1, "; ".join(problems[:4])
    return 0, f"{len(shape['artifact']['fits'])} records satisfy the reader's per-record requirements on the runner's own values"


@case(_RC2_G, "the-control-artifact-is-built-from-the-runners-own-output-shape", "pass")
def _(root):
    shape = json.load(open(_RC2_SHAPE, encoding="utf-8")); S_art = shape["artifact"]
    art, scores = _good_realcurve2(); r24 = _rc2_reader()
    blocks = [("partition", art["partition"], S_art["partition"]), ("corpus", art["corpus"], S_art["corpus"]),
              ("ext_corpus", art["ext_corpus"], S_art["ext_corpus"]), ("fit_corpus", art["fit_corpus"], S_art["fit_corpus"]),
              ("fit2_corpus", art["fit2_corpus"], S_art["fit2_corpus"]),
              ("curve_spec", art["curve_spec"], S_art["curve_spec"]), ("bar", art["bar"], S_art["bar"]),
              ("slope_bootstrap", art["slope_bootstrap"], S_art["slope_bootstrap"]), ("lead_at_top", art["lead_at_top"], S_art["lead_at_top"]),
              ("scores (file)", {k: v for k, v in scores.items()}, dict(shape["scores"], per_example=None, eval_chunk_ids=None, ext_chunk_ids=None, ext_fam=None))]
    blocks += [(f"readings.{n}", art["readings"][n], S_art["readings"]["r1_model"]) for n in art["readings"]]
    blocks += [(f"curves.{r}", art["curves"][r], S_art["curves"][r]) for r in art["curves"]]
    blocks += [(f"partition.rungs[{i}]", a, b) for i, (a, b) in enumerate(zip(art["partition"]["rungs"], S_art["partition"]["rungs"]))]
    blocks += [(f"lead_at_top.{k}", art["lead_at_top"][k], S_art["lead_at_top"][k]) for k in art["lead_at_top"] if isinstance(art["lead_at_top"][k], dict)]
    records = [(f"fits.{n}", art["fits"][n], S_art["fits"][n]) for n in art["fits"]]
    problems = _shape_problems(art, S_art, blocks, records,
                               [("PARTITION", r24.PARTITION, S_art["partition"]), ("CORPUS", r24.CORPUS, S_art["corpus"]),
                                ("EXT", r24.EXT, S_art["ext_corpus"]), ("FIT", r24.FIT, S_art["fit_corpus"]), ("FIT2", r24.FIT2, S_art["fit2_corpus"])])
    if problems:
        return 1, "; ".join(problems[:4])
    return 0, (f"control and fixture agree both ways on {len(S_art)} artifact keys, {len(art['fits'])} records, every curve, every lead and every block; "
               f"every reader expectation is a key the runner writes")


@case(_RC2_G, "two-roles-banking-the-same-per-example-vector-is-VOID", "fail")
def _(root):
    def m(a, s):
        s["per_example"]["r5_model"] = list(s["per_example"]["r6_model"])
        a["fits"]["r5_model"]["per_example_sha256"] = a["fits"]["r6_model"]["per_example_sha256"]
        for k in ("top1", "top1_non_gutenberg", "per_family"):
            a["fits"]["r5_model"][k] = a["fits"]["r6_model"][k]
        a["readings"]["r5_model"] = dict(a["readings"]["r6_model"])
        for k in ("ext_real_top1", "ext_real_correct", "ext_top1", "builder_eval_top1", "ext_per_family"):
            a[k]["r5_model"] = a[k]["r6_model"]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: roles")


@case(_RC2_G, "a-completion-under-a-foreign-name-is-VOID", "fail")
def _(root):
    def m(a, s):
        done = [e for e in a["ledger"] if e["name"] == "run_r1_model" and e["event"] == "completed"][0]
        a["ledger"].append(dict(done, name="confirm_model"))
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="order: the ledger carries completions under names outside")


@case(_RC2_G, "a-VOID-banks-no-slope-no-interval-and-no-lead", "fail")
def _(root):
    def m(a, s):
        a["curves"]["logistic"]["end_to_end_gain_second_decade"] = round(a["curves"]["logistic"]["end_to_end_gain_second_decade"] + 0.0001, 4)
    rc, out = _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: curves.logistic.end_to_end_gain_second_decade")
    v = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve2_4096_verdict.json")))
    if any(v.get(k) is not None for k in ("model_slope_per_doubling", "model_slope_ci95", "curves", "lead_at_top", "lead_reading", "verdict_components")):
        return 0, out + " !! a VOID verdict banked a slope, an interval, a curve or a lead"
    return rc, out


@case(_RC2_G, "a-bootstrap-only-FLAT-names-the-interval-clause-in-its-meaning", "fail")
def _(root):
    a = {"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.1245, 0.1298, 0.1350]}
    rc, out = _realcurve2_flat(root, "slope_bootstrap:", mode="disjoint", acc=a)
    v = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve2_4096_verdict.json")))
    m = v.get("meaning") or ""
    if rc != 0 and ("the interval clause" not in m or "do not agree on the rise" not in m):
        return 0, out + " !! the FLAT meaning does not name the interval clause"
    return rc, out


@case(_RC2_G, "a-FLAT-verdict-still-carries-the-lead-suffix", "fail")
def _(root):
    rc, out = _realcurve2_flat(root, "slope:", acc={"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.1193, 0.1193, 0.1193]})
    if rc != 0 and "verdict=SECOND_DECADE_FLAT_" not in out:
        return 0, out + " !! the FLAT verdict carries no lead suffix"
    return rc, out


@case(_RC2_G, "a-banked-rung-to-rung-gain-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curves"]["depth3_tree"]["rung_to_rung_gains"][5] = round(a["curves"]["depth3_tree"]["rung_to_rung_gains"][5] + 0.0001, 4)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: curves.depth3_tree.rung_to_rung_gains")


@case(_RC2_G, "a-banked-per-family-slope-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curves"]["model"]["per_family_slope_per_doubling_second_decade"]["py_src"] = round(a["curves"]["model"]["per_family_slope_per_doubling_second_decade"]["py_src"] + 0.00001, 6)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: curves.model.per_family_slope_per_doubling_second_decade")


@case(_RC2_G, "a-banked-paired-interval-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["slope_bootstrap"]["model_minus_logistic"]["ci95"][1] = round(a["slope_bootstrap"]["model_minus_logistic"]["ci95"][1] + 0.000001, 6)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: slope_bootstrap.model_minus_logistic")


@case(_RC2_G, "eval-chunk-ids-with-two-entries-swapped-is-VOID", "fail")
def _(root):
    def m(a, s):
        ids = s["eval_chunk_ids"]; i = next(i for i in range(1, len(ids)) if ids[i] != ids[0]); ids[0], ids[i] = ids[i], ids[0]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="scores: eval_chunk_ids")


@case(_RC2_G, "ext-chunk-ids-with-two-entries-swapped-is-VOID", "fail")
def _(root):
    def m(a, s):
        ids = s["ext_chunk_ids"]; i = next(i for i in range(1, len(ids)) if ids[i] != ids[0]); ids[0], ids[i] = ids[i], ids[0]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="scores: ext_chunk_ids")


@case(_RC2_G, "ext-fam-with-two-entries-swapped-is-VOID", "fail")
def _(root):
    def m(a, s):
        f = s["ext_fam"]; i = next(i for i in range(1, len(f)) if f[i] != f[0]); f[0], f[i] = f[i], f[0]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="scores: ext_fam")


@case(_RC2_G, "fit-info-by-name-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fit_info_by_name"] = {k: dict(v) for k, v in a["fit_info_by_name"].items()}
        a["fit_info_by_name"]["r1_model"]["n_iter"] = 999
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: fit_info_by_name is not the records' fit_info")


@case(_RC2_G, "an-extra-banked-reading-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["readings"]["r8_model"] = dict(a["readings"]["r7_model"])
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="readings: banked readings for")


@case(_RC2_G, "a-record-per-family-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["r2_logistic"]["per_family"] = dict(a["fits"]["r2_logistic"]["per_family"], code=0.5)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: r2_logistic record per_family")


@case(_RC2_G, "a-second-decade-record-with-the-reproduction-stage-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["fits"]["r5_model"].__setitem__("stage", "reproduction")), expect_clause="fit: r5_model stage")


@case(_RC2_G, "a-record-banked-infeasible-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["fits"]["r7_model"].__setitem__("status", "infeasible_memory")), expect_clause="fit: r7_model status")


@case(_RC2_G, "a-record-with-a-wrong-environment-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["r4_logistic"]["environment"] = dict(a["fits"]["r4_logistic"]["environment"], sklearn="0.0.0")
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="environment: r4_logistic sklearn")


@case(_RC2_G, "a-record-with-a-failed-block-probe-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["fits"]["r6_model"]["block_refills"] = [{"probe_ok": False}]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: r6_model banked a failed block probe")


@case(_RC2_G, "a-null-control-field-that-is-not-the-null-record-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["null_control"] = dict(a["fits"]["r7_model"])
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="null control: null_control is not the banked null record")


@case(_RC2_G, "null-rows-that-are-not-the-top-rungs-are-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a.__setitem__("null_rows", a["partition"]["rungs"][3]["n_rows"])), expect_clause="null control: null_rows")


@case(_RC2_G, "a-banked-reference-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["reference_top1"] = dict(a["reference_top1"], model=0.12)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="reproduction: the banked reference readings")


@case(_RC2_G, "a-banked-first-decade-reference-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["reference_first_decade"] = dict(a["reference_first_decade"], model=[0.0974, 0.1065, 0.1139, 0.12])
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="reproduction: reproduction_first_decade or reference_first_decade")


@case(_RC2_G, "a-banked-drift-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["reproduction_drift"] = dict(a["reproduction_drift"], logistic=0.001)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="reproduction: reproduction_drift")


@case(_RC2_G, "a-banked-first-decade-drift-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["reproduction_first_decade_drift"] = dict(a["reproduction_first_decade_drift"], model=[0.001, 0.0, 0.0, 0.0])
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="reproduction: reproduction_first_decade_drift")


@case(_RC2_G, "a-banked-shuffled-label-reading-off-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a.__setitem__("shuffled_label_accuracy_real", 0.0381)), expect_clause="null control: a banked shuffled-label")


@case(_RC2_G, "a-banked-summary-reading-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["ext_real_top1"] = dict(a["ext_real_top1"]); a["ext_real_top1"]["r6_model"] = round(a["ext_real_top1"]["r6_model"] + 0.0001, 4)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="readings: a banked summary reading for r6_model")


@case(_RC2_G, "a-select-stage-artifact-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a.__setitem__("stage", "select")), expect_clause="scope: stage")


@case(_RC2_G, "a-completion-event-with-a-wrong-fingerprint-is-VOID", "fail")
def _(root):
    def m(a, s):
        e = [e for e in a["ledger"] if e["name"] == "run_r6_model" and e["event"] == "completed"][0]; e["fingerprint"] = "ffffffffffffffff"
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: r6_model's completion event does not carry")


@case(_RC2_G, "a-completion-without-its-start-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["ledger"] = [e for e in a["ledger"] if not (e["name"] == "run_r3_logistic" and e["event"] == "started")]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: r3_logistic has no 'started' event")


@case(_RC2_G, "a-malformed-artifact-file-is-pending-not-a-pass", "fail")
def _(root):
    art, scores = _good_realcurve2()
    piv = os.path.join(root, "artifacts", "pivot"); os.makedirs(piv, exist_ok=True)
    json.dump(scores, open(os.path.join(piv, "realcurve2_4096_scores.json"), "w"))
    open(os.path.join(piv, "realcurve2_4096.json"), "w").write("{not json")
    shutil.copy(os.path.join(REPO, "tools", "readers", "realcurve2_4096_verdict.py"), os.path.join(root, "tools", "readers", "realcurve2_4096_verdict.py"))
    rc, out = run([PY, "tools/readers/realcurve2_4096_verdict.py"], root)
    if rc != 2:
        return 0, out + " !! expected exit 2 on a malformed artifact"
    return rc, out


@case(_RC2_G, "a-resumed-run-that-relogged-its-rung-bound-events-passes", "pass")
def _(root):
    def m(a, s):
        L = a["ledger"]; extra = []
        for e in L:
            if e["event"] == "rung_bound":
                extra.append(dict(e, utc="2026-09-19T04:00:00Z"))
        i = next(i for i, e in enumerate(L) if e["name"] == "run_r6_model" and e["event"] == "started")
        L.insert(i + 1, dict(L[i], attempt=2, utc="2026-09-19T04:00:01Z"))
        a["ledger"] = L + extra; a["launch_number"] = 2
        a["launch_environment"] = dict(a["launch_environment"], loadavg_waited_seconds=45)
    return _realcurve2(root, _rc2_mut(m))


@case(_RC2_G, "committed-checkpoints-that-agree-pass", "pass")
def _(root):
    art, scores = _good_realcurve2()
    _rc2_ckpt(root, art, scores)
    rc, out = _realcurve2(root)
    v = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve2_4096_verdict.json")))
    if rc == 0 and v.get("checkpoints_cross_checked") != len(art["fits"]):
        return 1, out + f" !! checkpoints_cross_checked={v.get('checkpoints_cross_checked')}"
    return rc, out


@case(_RC2_G, "a-committed-checkpoint-with-a-different-vector-is-VOID", "fail")
def _(root):
    art, scores = _good_realcurve2()

    def m(cks):
        v = cks["r6_model"]["per_example"]; v[0] = 1 - v[0]
    _rc2_ckpt(root, art, scores, m)
    return _realcurve2_void(root, expect_clause="checkpoint: r6_model's committed checkpoint")


@case(_RC2_G, "a-missing-committed-checkpoint-is-VOID", "fail")
def _(root):
    art, scores = _good_realcurve2()
    _rc2_ckpt(root, art, scores)
    os.remove(os.path.join(root, "artifacts", "pivot", "realcurve2_4096_ckpt", "run_r5_logistic.json"))
    return _realcurve2_void(root, expect_clause="checkpoint: r5_logistic has no checkpoint")


@case(_RC2_G, "the-exception-path-writes-the-normal-paths-key-set", "pass")
def _(root):
    rc, out = _realcurve2(root)
    ok = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve2_4096_verdict.json")))
    rc2, out2 = _realcurve2_void(root, _rc2_mut(lambda a, s: a.__setitem__("partition", "not a mapping")))
    bad = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve2_4096_verdict.json")))
    if not (bad["validity_failed_clauses"] and bad["validity_failed_clauses"][0].startswith("reader:")):
        return 1, "!! the exception path was not taken"
    if set(ok) != set(bad):
        return 1, f"!! key sets differ: normal-only {sorted(set(ok) - set(bad))}, exception-only {sorted(set(bad) - set(ok))}"
    return 0, f"{len(ok)} keys on both paths"


# ---- cases added after the 0024 pre-freeze review (reader and gate lens)
@case(_RC2_G, "control-a-lead-interval-that-straddles-0-is-NO_SEPARATION-whatever-the-point-sign-says", "pass")
def _(root):
    a = {"logistic": [0.0911, 0.0939, 0.1085, 0.1179, 0.124, 0.130, 0.141]}
    art, _ = _good_realcurve2(acc=a, lead_shift=True)
    lt = art["lead_at_top"]["r7_model_minus_logistic"]
    if not (lt["point"] > 0 and lt["ci95"][0] < 0 < lt["ci95"][1] and 0.3 < lt["share_of_resamples_with_model_ahead"] < 0.7):
        return 1, f"!! the control's lead interval does not straddle 0: {lt}"
    return _realcurve2(root, acc=a, lead_shift=True, expect="SECOND_DECADE_RISES_NO_SEPARATION")


@case(_RC2_G, "control-a-lead-interval-that-straddles-0-with-the-logistic-ahead-on-the-point-is-NO_SEPARATION", "pass")
def _(root):
    a = {"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.128, 0.136, 0.141], "logistic": [0.0911, 0.0939, 0.1085, 0.1179, 0.124, 0.130, 0.143]}
    art, _ = _good_realcurve2(acc=a, lead_shift=True)
    lt = art["lead_at_top"]["r7_model_minus_logistic"]
    if not (lt["point"] < 0 and lt["ci95"][0] < 0 < lt["ci95"][1]):
        return 1, f"!! the control's lead interval does not straddle 0 with the logistic ahead on the point: {lt}"
    return _realcurve2(root, acc=a, lead_shift=True, expect="SECOND_DECADE_RISES_NO_SEPARATION")


@case(_RC2_G, "control-the-lead-at-the-top-is-read-from-the-top-rung-not-from-the-slope-difference", "pass")
def _(root):
    a = {"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.120, 0.135, 0.143], "logistic": [0.0911, 0.0939, 0.1085, 0.1179, 0.140, 0.141, 0.1445]}
    art, _ = _good_realcurve2(acc=a)
    if art["slope_bootstrap"]["model_minus_logistic"]["ci95"][0] > 0 or art["lead_at_top"]["r7_model_minus_logistic"]["ci95"][1] >= 0:
        return 1, f"!! the control does not separate the slope difference from the lead: {art['slope_bootstrap']['model_minus_logistic']} / {art['lead_at_top']['r7_model_minus_logistic']}"
    return _realcurve2(root, acc=a, expect="SECOND_DECADE_RISES_LINEAR_LEADS")


@case(_RC2_G, "control-a-flat-second-decade-with-the-model-ahead-is-SECOND_DECADE_FLAT_MODEL_LEADS", "pass")
def _(root):
    return _realcurve2(root, acc={"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.1193, 0.1193, 0.1193],
                                  "logistic": [0.0911, 0.0939, 0.1085, 0.1179, 0.1179, 0.1179, 0.1179]}, expect="SECOND_DECADE_FLAT_MODEL_LEADS")


@case(_RC2_G, "control-a-flat-second-decade-with-no-separation-is-SECOND_DECADE_FLAT_NO_SEPARATION", "pass")
def _(root):
    a = {"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.1193, 0.1193, 0.1193], "logistic": [0.0911, 0.0939, 0.1085, 0.1179, 0.1179, 0.1179, 0.1193]}
    return _realcurve2(root, acc=a, lead_shift=True, expect="SECOND_DECADE_FLAT_NO_SEPARATION")


@case(_RC2_G, "control-a-role-at-its-iteration-cap-at-the-top-rung-is-flagged-and-the-lead-is-not-a-recipe-comparison", "pass")
def _(root):
    def m(a, s):
        a["fits"]["r7_logistic"]["fit_info"] = dict(a["fits"]["r7_logistic"]["fit_info"], n_iter=1000)
        a["fit_info_by_name"] = {k: dict(v) for k, v in a["fit_info_by_name"].items()}; a["fit_info_by_name"]["r7_logistic"]["n_iter"] = 1000
    rc, out = _realcurve2(root, _rc2_mut(m))
    v = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve2_4096_verdict.json")))
    f = v.get("flags") or {}
    if rc == 0 and not (f.get("roles_at_iteration_cap_at_the_top_rung") == ["r7_logistic"] and f.get("lead_at_top_is_a_recipe_comparison") is False
                        and "iteration cap at the top rung" in (v.get("meaning") or "")):
        return 1, out + f" !! cap flags {f.get('roles_at_iteration_cap_at_the_top_rung')} / {f.get('lead_at_top_is_a_recipe_comparison')}"
    return rc, out


@case(_RC2_G, "a-falling-second-decade-names-the-fall-in-its-meaning", "fail")
def _(root):
    rc, out = _realcurve2_flat(root, "slope:", acc={"model": [0.0974, 0.1065, 0.1139, 0.1193, 0.115, 0.112, 0.110]})
    v = json.load(open(os.path.join(root, "artifacts", "pivot", "realcurve2_4096_verdict.json")))
    if rc != 0 and "lowered the model's reading on the original files" not in (v.get("meaning") or ""):
        return 0, out + " !! the falling second decade is not named"
    return rc, out


@case(_RC2_G, "a-null-record-fitted-on-rung-4s-rows-is-VOID", "fail")
def _(root):
    def m(a, s):
        for k in ("n_fit_rows", "fit_rows_sha256", "fit_rows_sorted_sha256", "n_rung_rows", "n_rung_chunks"):
            a["fits"]["null"][k] = a["fits"]["r4_model"][k]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: null was not fitted on sealed rung 7")


@case(_RC2_G, "a-record-with-the-right-rung-but-the-wrong-chunk-count-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["fits"]["r6_logistic"].__setitem__("n_rung_chunks", a["fits"]["r6_logistic"]["n_rung_chunks"] + 1)),
                            expect_clause="fit: r6_logistic was not fitted on sealed rung 6")


@case(_RC2_G, "log2-second-decade-abscissae-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["log2_chunks_second_decade"] = [x + 0.5 for x in a["log2_chunks_second_decade"]]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="scope: roles=")


@case(_RC2_G, "a-top-level-doubling-count-off-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a.__setitem__("doublings", 4)), expect_clause="scope: roles=")


@case(_RC2_G, "second-decade-corpus-row-counts-off-are-VOID", "fail")
def _(root):
    def m(a, s):
        a["fit2_rows_per_family"] = dict(a["fit2_rows_per_family"], c_src=a["fit2_rows_per_family"]["c_src"] + 1)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="corpora: the banked family lists or fit row counts")


@case(_RC2_G, "a-lead-block-without-its-unit-is-VOID", "fail")
def _(root):
    def m(a, s):
        del a["lead_at_top"]["unit"]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="lead: lead_at_top carries no unit")


@case(_RC2_G, "a-banked-first-decade-reproduction-reading-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["reproduction_first_decade"] = {k: list(v) for k, v in a["reproduction_first_decade"].items()}
        a["reproduction_first_decade"]["model"][0] = round(a["reproduction_first_decade"]["model"][0] + 0.0001, 4)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="reproduction: reproduction_first_decade or reference_first_decade")


@case(_RC2_G, "a-banked-lead-point-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["lead_at_top"]["r7_model_minus_logistic"]["point"] = round(a["lead_at_top"]["r7_model_minus_logistic"]["point"] + 0.0001, 4)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="lead: lead_at_top.r7_model_minus_logistic")


@case(_RC2_G, "a-rung-bound-event-with-the-right-rung-but-the-wrong-row-hash-is-VOID", "fail")
def _(root):
    def m(a, s):
        e = [e for e in a["ledger"] if e["name"] == "run_r5_model" and e["event"] == "rung_bound"][0]; e["rung_sorted_sha256"] = "0" * 64
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: r5_model has no 'rung_bound' event")


@case(_RC2_G, "real-row-count-off-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a.__setitem__("n_ext_real_rows", a["n_ext_real_rows"] - 1)), expect_clause="corpora: n_ext_rows=")


@case(_RC2_G, "a-shift-arm-hash-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["partition"]["shift_arm"]["chunks_sha256"] = "b" * 64
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="sealed set: partition.shift_arm")


@case(_RC2_G, "a-shift-arm-that-is-not-rung-5s-new-chunks-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["partition"]["shift_arm"].__setitem__("same_chunks_as_rung_5s_new_chunks", False)),
                            expect_clause="partition.shift_arm")


@case(_RC2_G, "a-missing-shift-arm-role-is-VOID", "fail")
def _(root):
    def m(a, s):
        del a["fits"]["s4_model"]
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: the artifact banks roles outside the sealed order")


@case(_RC2_G, "a-banked-shift-arm-difference-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["shift_arm"]["difference_from_rung_4"]["model"] = round(a["shift_arm"]["difference_from_rung_4"]["model"] + 0.0001, 4)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="shift arm: shift_arm.difference_from_rung_4")


@case(_RC2_G, "a-shift-arm-record-with-the-curve-stage-is-VOID", "fail")
def _(root):
    return _realcurve2_void(root, _rc2_mut(lambda a, s: a["fits"]["s4_model"].__setitem__("stage", "curve")), expect_clause="fit: s4_model stage")


@case(_RC2_G, "a-shift-arm-banking-rung-4s-vector-is-VOID-as-a-shared-vector", "fail")
def _(root):
    def m(a, s):
        s["per_example"]["s4_model"] = list(s["per_example"]["r4_model"])
        for k in ("per_example_sha256", "top1", "top1_non_gutenberg", "per_family"):
            a["fits"]["s4_model"][k] = a["fits"]["r4_model"][k]
        a["readings"]["s4_model"] = dict(a["readings"]["r4_model"])
        for k in ("ext_real_top1", "ext_real_correct", "ext_top1", "builder_eval_top1", "ext_per_family"):
            a[k]["s4_model"] = a[k]["r4_model"]
        rd = a["readings"]["r4_model"]
        a["shift_arm"]["readings"]["model"] = {"ext_real_top1": rd["ext_real_top1"], "ext_real_correct": rd["ext_real_correct"],
                                               "builder_eval_top1": rd["builder_eval_top1"], "ext_per_family": {f: rd["ext_per_family"][f] for f in a["ext_real_families"]}}
        a["shift_arm"]["difference_from_rung_4"]["model"] = 0.0
        a["shift_arm"]["difference_from_rung_5"]["model"] = round(rd["ext_real_top1"] - a["readings"]["r5_model"]["ext_real_top1"], 4)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="fit: roles")


@case(_RC2_G, "a-banked-sensitivity-slope-off-is-VOID", "fail")
def _(root):
    def m(a, s):
        a["curves"]["model"]["slope_second_decade_with_rung4_at_reference"] = round(a["curves"]["model"]["slope_second_decade_with_rung4_at_reference"] + 0.00001, 6)
    return _realcurve2_void(root, _rc2_mut(m), expect_clause="curve: curves.model.slope_second_decade_with_rung4_at_reference")


@case(_RC2_G, "a-committed-checkpoint-whose-record-differs-from-the-banked-one-is-VOID", "fail")
def _(root):
    art, scores = _good_realcurve2()

    def m(cks):
        cks["r6_model"]["record"] = dict(cks["r6_model"]["record"], seconds=999.0)
    _rc2_ckpt(root, art, scores, m)
    return _realcurve2_void(root, expect_clause="checkpoint: r6_model's committed checkpoint")



def main() -> int:
    # `python3 tests/mutation_test.py <gate> [<gate> ...]` runs only those gates' cases and writes NO report (a partial
    # report would make the banked count stale); the full suite, as CI runs it, takes no arguments.
    only = set(sys.argv[1:])
    cases = [c for c in CASES if not only or c["gate"] in only]
    if only and not cases:
        print(f"no cases for gates {sorted(only)}", file=sys.stderr); return 2
    results = []
    for c in cases:
        with tempfile.TemporaryDirectory() as tmp:
            root = sandbox(tmp)
            try:
                rc, out = c["fn"](root)
            except Exception as e:  # noqa: BLE001
                rc, out = -1, f"HARNESS ERROR: {e}"
            observed = "pass" if rc == 0 else "fail"
            ok = observed == c["expect"] and rc != -1        # a HARNESS ERROR is never a detection (0024 pre-freeze review)
            results.append({
                "gate": c["gate"], "mutation": c["name"], "expected": c["expect"],
                "observed": observed, "exit_code": rc, "detected": ok,
                "evidence": _stable_evidence(out),
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
    if only:
        width = max(len(r["mutation"]) for r in results)
        for r in results:
            print(f"{'OK  ' if r['detected'] else 'HOLE'}  {r['gate']:<11} {r['mutation']:<{width}}  expected={r['expected']:<4} "
                  f"observed={r['observed']:<4} rc={r['exit_code']}  {r['evidence'][:160]}")
        print(f"\nPARTIAL RUN ({sorted(only)}): {report['detected']}/{report['total_mutations']} detected; no report written")
        return 0 if not survived else 1
    with open(os.path.join(outdir, "mutation_report.json"), "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")

    # Guard: the coverage map hard-codes this count in a claim. Adding a mutation without updating
    # that claim turns CI red one gate later, where it is easy to miss.
    #
    # This was a WARNING and it failed three times. The third time is why it is now an EXIT CODE:
    # the warning printed exactly as designed, and it was filtered out of view by a grep over this
    # command's own output before the commit went out. A signal that a hurried reader can drop is
    # not a guard. An exit code cannot be grepped away.
    stale_claim = None
    cov = os.path.join(REPO, "artifacts", "verification", "coverage.json")
    if os.path.exists(cov):
        try:
            claims = json.load(open(cov))["claims"]
            claimed = next((c.get("value") for c in claims if c.get("id") == "mutations-detected"), None)
            if claimed is not None and int(claimed) != len(results):
                stale_claim = (int(claimed), len(results))
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
    if stale_claim:
        claimed, actual = stale_claim
        print(f"\nMUTATION COUNT IS STALE: artifacts/verification/coverage.json claims {claimed}, "
              f"this run has {actual}.")
        print("Update the 'mutations-detected' claim, and the rows in VERDICT.md and "
              "outbound/ONE_PAGER.md that carry the same count, before committing.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
