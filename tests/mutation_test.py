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
    for f in ("chainlib.py", "prereg.py", "claimcheck.py"):
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
