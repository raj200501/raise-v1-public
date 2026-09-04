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


_CFG2048 = {"reader": "recipe2048_verdict.py", "prereg": "0012-recipe-search-2048.json",
            "conf": {"majority": (0.0385, 0.0385), "stratified": (0.0385, 0.0385), "best_single_feat": (0.0726, 0.0762),
                     "depth3_tree": (0.09, 0.091), "deep_tree": (0.15, 0.155), "logistic": (0.13, 0.135),
                     "model": (0.21, 0.22)},
            "incumbent": (0.1741, 0.1819), "l1": (0.1266, 0.1315), "stamp": "0012-recipe-search-2048"}
_CFG4096 = {"reader": "recipe4096_verdict.py", "prereg": "0014-recipe-search-4096.json",
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
    part = dict(r12.PARTITION)
    _R = json.load(open(os.path.join(REPO, "prereg", cfg["prereg"])))["scope"]["roster"]
    proto = _R["protocol"]; heads = _R["heads"]
    by_id = {c["id"]: c for h in heads for c in h["candidates"]}
    fam8 = ["gutenberg", "base64", "binary", "code", "csv", "json", "log", "mixed"]

    def rec(head, cid, stage, n_rows, rows_sha, sorted_sha, top1, ng):
        c = by_id[cid]
        return {"id": cid, "head": head, "family": c["family"], "params": c.get("params", {}),
                "scaled": bool(c.get("scaled", False)), "val": c.get("val"), "seed": 20260825,
                "params_sha256": _sha12(c), "stage": stage, "n_fit_rows": n_rows, "fit_rows_sha256": rows_sha,
                "fit_rows_sorted_sha256": sorted_sha, "environment": dict(_ENV12), "status": "fit",
                "seconds": 1.0, "top1": top1, "top1_non_gutenberg": ng,
                "per_family": {f: round(top1, 4) for f in fam8}, "block_refills": [], "fit_info": {}}

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
    corpus = dict(r12.CORPUS)
    sel_doc = {"schema_version": 1, "preregistration": cfg["stamp"], "smoke": False,
               "roster_sha256": _sha12(_R), "roster": _R, "corpus": corpus, "partition": sel_part,
               "n_classes": 26, "class_names": [], "chance_accuracy": 0.038462, "stage": "select",
               "gathers": [{"name": "holdout", "n_rows": part["n_holdout_rows"], "n_eval_rows": 0}],
               "eval_rows_gathered_in_selection": 0, "environment": dict(_ENV12), "selection": selection,
               "selected_ids": selected, "ledger": [], "cost": {"selection_seconds_total": 1.0},
               "selection_started_utc": "2026-09-04T00:00:00Z", "selection_finished_utc": "2026-09-04T01:00:00Z"}
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
    art = {"schema_version": 1, "preregistration": cfg["stamp"], "smoke": False, "stage": "confirm",
           "roster_sha256": _sha12(_R), "roster": _R, "corpus": corpus, "partition": part, "n_classes": 26,
           "class_names": [], "chance_accuracy": 0.038462, "selection_sha256": sel_sha, "selection": sel_doc,
           "selected_ids": selected, "selected_model_id": selected["model"], "environment": dict(_ENV12),
           "complete": True, "missing_roles": [], "final": final,
           "final_top1": conf["model"][0], "final_top1_non_gutenberg": conf["model"][1],
           "final_per_family": final["model"]["per_family"], "final_status": "fit",
           "best_frozen_for_bar": bf, "best_frozen_searched": conf["logistic"][0], "best_frozen_head": "logistic",
           "best_expanded_for_bar": be, "best_expanded_searched": conf["deep_tree"][0], "best_expanded_head": "deep_tree",
           "best_expanded_non_gutenberg_for_bar": ben, "best_expanded_non_gutenberg_searched": conf["deep_tree"][1],
           "incumbent_refit": inc, "incumbent_refit_top1": cfg["incumbent"][0], "logistic_l1_refit": l1,
           "logistic_l1_refit_top1": cfg["l1"][0], "null_control": null, "shuffled_label_accuracy": 0.039,
           "null_rows": 20000, "cluster_ci95_informational": {}, "ledger": ledger, "cost": {},
           "confirmatory_started_utc": "2026-09-04T02:00:00Z"}
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
