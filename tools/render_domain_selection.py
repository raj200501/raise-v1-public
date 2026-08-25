#!/usr/bin/env python3
"""Render docs/DOMAIN_SELECTION.md from the banked domain-search artifacts.

The document is GENERATED, not typed. Every candidate, gate score, recorded search and
adversarial verdict in it comes from artifacts/phase0/round*_domain_search.json, so the
prose cannot drift away from the evidence it claims to summarise.
"""
from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chainlib import REPO_ROOT, sha256_file  # noqa: E402

OUT = os.path.join(REPO_ROOT, "docs", "DOMAIN_SELECTION.md")


def esc(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()


def main() -> int:
    rounds = sorted(glob.glob(os.path.join(REPO_ROOT, "artifacts", "phase0", "round*_domain_search.json")))
    if not rounds:
        print("no round artifacts found", file=sys.stderr)
        return 2

    L: list[str] = []
    w = L.append

    w("# Phase 0 — Domain selection")
    w("")
    w("> **This document is generated** by `tools/render_domain_selection.py` from the banked")
    w("> artifacts listed below. Do not edit it by hand; edit the evidence and re-render.")
    w("")
    w("| Source artifact | sha256 |")
    w("|---|---|")
    for p in rounds:
        w(f"| `{os.path.relpath(p, REPO_ROOT)}` | `{sha256_file(p)[:32]}…` |")
    w("")

    w("## What is being decided, and the standard it must meet")
    w("")
    w("We are looking for a domain in which to reproduce the *structure* of the FDM-1 result:")
    w("an abundant unlabelled corpus, a mechanism that manufactures labels for it at near-zero")
    w("marginal cost, a known-good recipe, and a quality curve that rises with data. Five hard")
    w("gates, all of which must pass:")
    w("")
    w("| Gate | Requirement |")
    w("|---|---|")
    w("| **G1** | ≥ ~10⁶ units exist and are legally obtainable, with a named source and a count. |")
    w("| **G2** | A label manufacturer at near-zero marginal cost: (a) inverse model on a small seed, (b) environment supplies truth free, or (c) the artifact was generated from a structured source that still exists. |")
    w("| **G3** | More data/compute plausibly makes it better, **and** a bigger general model with plain prompting does not simply do it. |")
    w("| **G4** | White space verified, not assumed: < ~3 serious efforts and no open dataset at target scale, after ≥6 query formulations and ≥2 domain-specific venues. |")
    w("| **G5** | If it works at scale, a named buyer type pays. |")
    w("")
    w("Two further preconditions were added before any candidate was scored, so that they could")
    w("not be invented afterwards to justify a choice:")
    w("")
    w("| Gate | Requirement | Why it was added |")
    w("|---|---|---|")
    w("| **G6** | The four-rung curve must be trainable on the actual execution box: 4 CPU cores, 15 GB RAM, **no GPU**, ~30 GB disk. | This is the machine the work runs on. A domain that needs a GPU cluster is not a domain this project can execute. |")
    w("| **G2a** | The label manufacturer must know something the student's input cannot contain. | Added *after* round 1 on the evidence below. See “The finding that changed the gates”. |")
    w("")

    analysis = os.path.join(REPO_ROOT, "docs", "_domain_selection_analysis.md")
    if os.path.exists(analysis):
        w(open(analysis, encoding="utf-8").read().rstrip())
        w("")

    for p in rounds:
        d = json.load(open(p, encoding="utf-8"))
        rn = d.get("round", "?")
        w("")
        w("---")
        w("")
        w(f"# Round {rn}")
        w("")
        for i, sr in enumerate(d.get("scout_reads", []) or [], 1):
            w(f"### Round {rn}: scout {i} — honest read")
            w("")
            w("> Scouts were told that “nothing in this structure threads it, and here is why” is a")
            w("> valid and valuable answer, and is better than padding.")
            w("")
            w("```")
            w(sr)
            w("```")
            w("")
        for a in d.get("round1_leftovers_attacked", []) or []:
            w(f"### Round {rn}: adversarial review of a round-1 survivor that was never attacked — {a['domain']}")
            w("")
            w(f"**Recommendation: {a['overall_recommendation']}.** "
              f"G2a {a.get('g2a_verdict','?')} · G3 {a['g3_verdict']} · G1 {a['g1_verdict']} · G6 {a['g6_verdict']}")
            w("")
            for head, key in [("What the manufacturer knows that the student cannot (G2a)", "g2a_what_manufacturer_knows"),
                              ("Channel capacity (A1)", "a1_channel_capacity"),
                              ("The dumbest baseline (A2)", "a2_dumb_baseline"),
                              ("G3 — kill attempt", "g3_kill_attempt"),
                              ("G3 — does it survive?", "g3_survives"),
                              ("G1 — licence reality", "g1_licence_reality"),
                              ("G4 — re-check", "g4_recheck"),
                              ("G6 — feasibility", "g6_reasoning"),
                              ("Strongest case against", "strongest_case_against")]:
                if a.get(key):
                    w(f"**{head}**")
                    w("")
                    w(a[key])
                    w("")

        m = d.get("method", {})
        w("**Method.** " + " → ".join(f"*{k}*: {v}" for k, v in m.items()) if m else "")
        w("")

        cands = d.get("all_candidates", [])
        w(f"## Round {rn}: all {len(cands)} candidates generated, before any scoring")
        w("")
        w("Candidates were generated by three scouts working in deliberately unfashionable sectors,")
        w("*before* any gate was applied, so that the pool was not pre-filtered toward a preferred answer.")
        w("")
        w("| # | Candidate | Input modality | Label manufacturer | G1 estimate | CPU-feasible |")
        w("|---:|---|---|---|---|:--:|")
        for i, c in enumerate(cands, 1):
            w(f"| {i} | **{esc(c['name'])[:78]}** | {esc(c['input_modality'])[:95]} | "
              f"`{c.get('g2_shape','?')}` | {esc(c.get('g1_est_units',''))[:70]} | "
              f"{'yes' if c.get('g6_cpu_feasible') else 'NO'} |")
        w("")

        sc = d.get("screened", {})
        rej = sc.get("rejected", [])
        w(f"## Round {rn}: {len(rej)} rejected at screen, with the gate that killed each")
        w("")
        w("| Candidate | Killed by | Reason |")
        w("|---|---|---|")
        for x in rej:
            w(f"| {esc(x['name'])[:70]} | `{esc(x['killed_by'])[:40]}` | {esc(x['reason'])[:300]} |")
        w("")

        surv = sc.get("survivors", [])
        w(f"## Round {rn}: {len(surv)} survivors carried to white-space verification")
        w("")
        for i, s in enumerate(surv, 1):
            w(f"### {i}. {s['name']}")
            w("")
            w(f"{s['one_line']}")
            w("")
            w(f"- **Input modality** — {s['input_modality']}")
            w(f"- **Label** — {s['output_label']}")
            w(f"- **Corpus (G1)** — {s['g1_corpus']}")
            w(f"- **Manufacturer (G2, shape `{s['g2_shape']}`)** — {s['g2_mechanism']}")
            w(f"- **Scale argument (G3)** — {s['g3_argument']}")
            w(f"- **Buyer (G5)** — {s['g5_buyer']}")
            w(f"- **Why it survived the screen** — {s['why_survives']}")
            w("")

        g4 = d.get("g4_results", [])
        nsearch = sum(len(g.get("searches", [])) for g in g4)
        w(f"## Round {rn}: white-space verification (G4) — {nsearch} recorded searches")
        w("")
        w("“I did not find anything” is not evidence of white space. Every search below was actually")
        w("run, and what came back is recorded whether or not it was convenient.")
        w("")
        w("| Domain | Verdict | Crowding | Searches | Serious efforts | Open datasets |")
        w("|---|:--:|:--:|:--:|:--:|:--:|")
        for g in g4:
            w(f"| {esc(g['domain'])[:64]} | **{g['g4_verdict']}** | {g['crowding_score']}/10 | "
              f"{len(g['searches'])} | {len(g['serious_efforts'])} | {len(g['open_datasets'])} |")
        w("")
        for g in g4:
            w(f"### G4 detail — {g['domain']}")
            w("")
            w(f"**Verdict: {g['g4_verdict']}** (crowding {g['crowding_score']}/10)")
            w("")
            w(g["g4_reasoning"])
            w("")
            if g.get("serious_efforts"):
                w("**Serious efforts found:**")
                w("")
                w("| Effort | Year | What it did | Scale | URL |")
                w("|---|---|---|---|---|")
                for e in g["serious_efforts"]:
                    w(f"| {esc(e['name'])[:60]} | {esc(e['year'])} | {esc(e['what_it_did'])[:150]} | "
                      f"{esc(e['scale'])[:80]} | {esc(e['url'])[:90]} |")
                w("")
            if g.get("open_datasets"):
                w("**Open datasets found:**")
                w("")
                w("| Dataset | Size | URL |")
                w("|---|---|---|")
                for e in g["open_datasets"]:
                    w(f"| {esc(e['name'])[:60]} | {esc(e['size'])[:60]} | {esc(e['url'])[:90]} |")
                w("")
            w("<details><summary>All searches run for this domain</summary>")
            w("")
            w("| Venue | Query | Relevant hits | What came back |")
            w("|---|---|:--:|---|")
            for s in g["searches"]:
                w(f"| {esc(s['venue'])[:40]} | `{esc(s['query'])[:110]}` | {s['n_relevant_hits']} | "
                  f"{esc(s['result_summary'])[:400]} |")
            w("")
            w("</details>")
            w("")

        adv = d.get("adversarial", [])
        w(f"## Round {rn}: adversarial review — {len(adv)} finalists, default posture REJECT")
        w("")
        w("Each finalist was handed to an agent instructed to kill it, with the founder's previous")
        w("failure stated explicitly as the thing to look for. Several of these reviews are backed by")
        w("measurements the reviewer took on this box rather than by argument.")
        w("")
        w("| Finalist | G3 | G1 | G6 | Verdict |")
        w("|---|:--:|:--:|:--:|:--:|")
        for a in adv:
            w(f"| {esc(a['domain'])[:70]} | {a['g3_verdict']} | {a['g1_verdict']} | {a['g6_verdict']} | "
              f"**{a['overall_recommendation']}** |")
        w("")
        for a in adv:
            w(f"### Adversarial review — {a['domain']}")
            w("")
            w(f"**Recommendation: {a['overall_recommendation']}.** "
              f"G3 {a['g3_verdict']} · G1 {a['g1_verdict']} · G6 {a['g6_verdict']}. "
              f"Reviewer confidence: {a['confidence']}")
            w("")
            for head, key in [("G3 — kill attempt", "g3_kill_attempt"),
                              ("G3 — does it survive?", "g3_survives"),
                              ("G1 — licence reality", "g1_licence_reality"),
                              ("G2 — label noise and degeneracy", "g2_noise_risk"),
                              ("G6 — CPU feasibility, concretely", "g6_reasoning"),
                              ("Strongest case against", "strongest_case_against")]:
                w(f"**{head}**")
                w("")
                w(a.get(key, "COULD NOT VERIFY"))
                w("")

        lims = d.get("known_limitations", [])
        if lims:
            w(f"## Round {rn}: known limitations of this round")
            w("")
            for x in lims:
                w(f"- {x}")
            w("")

    body = "\n".join(L) + "\n"
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(body)
    print(f"wrote {os.path.relpath(OUT, REPO_ROOT)} ({len(body)} chars, {body.count(chr(10))} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
