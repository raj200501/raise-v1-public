# Diligence map

The questions a hostile technical reviewer should ask, with where each answer lives. None of these
are hypothetical — most were literally asked by the 54-agent adversarial audit whose full record,
rejected findings included, is banked at `artifacts/verification/adversarial_audit.json`.

## "Is the slope real, or a seed artifact?"

The interval is a cluster bootstrap over the 10,000 held-out source chunks — the dependence unit
the split declares — after an audit found the original fragment-level interval anti-conservative
(`artifacts/pivot/audit_rederivations.json`, CORRECTIONS.md 2026-08-31). Seed variance is measured
by full-pipeline replications at independent seeds: `artifacts/pivot/deflate_curve_seed*.json`, or
the row stays PENDING in `outbound/EVIDENCE_BRIEF.md`.

## "Is it memorising content rather than identifying encoders?"

Three answers, one of them against us. The split is grouped by source chunk, and the archived trial
measured the random-split failure this prevents (0.4873 → 0.1531). The null control retrains on
shuffled labels and falls to chance. And the audit found the grouping guarantee **false for the
gutenberg family** (shared byte pool) — with the measured impact running *against* the headline:
excluding the leaked family widens both margins (`$.gutenberg_excluded_margins` in
`audit_rederivations.json`).

## "Won't a frontier model just do this?"

The input is mid-stream entropy-coded bitstream — no header, no text, nothing `javap`-like renders
legible (the attack that killed the JVM candidate in `trial/pivot/DOMAIN_SELECTION.md` was checked
here and does not transfer). The measured stand-ins for "clever prior, no task-specific data" are
the trivial-baseline ladder up to depth-16 trees and logistic regression, all trained on the same
data as the top rung; the margins over them are the headline clauses.

## "Where does the signal actually live?"

`artifacts/pivot/per_family_curves.json`: ~+0.09/decade on structured content (csv, log, json) at
ten times chance, near-flat on incompressible families sitting at the measured collision ceiling
(`carve_channel_capacity.json`). The headline is a mixture and the decomposition is published —
at 2048 too (`per_family_curves_2048.json`): csv and log clear the 0.05 bar on both readings
(+0.0554 and +0.0501 against the depth-16 tree), the structured four clear it as a set (+0.0549),
and the mixture misses on every reading — even without the three incompressible families (+0.0478).

## "Does it survive realistic carve sizes?"

**No, and that is preregistered and published**: `CARVE_FAILS` at 1024 bytes (prereg 0007), with
transfer collapsing to chance, an information-ceiling measurement ruling out the easy excuse, and
two learned-representation attempts (0009, 0010) that did not rescue it. At 2048 bytes (prereg
0011, expected outcome stated before the corpus existed) it fails again — +0.0475 against the 0.05
bar on the frozen set, +0.0294 against all baselines, transfer from 4096 at 0.0455 — so the
boundary of the working window is bracketed to (2048, 4096]. A symmetric recipe search at 2048
(prereg 0012, read under 0013 after 0012's own frozen reader voided the run on a defect of its own,
filed in `CORRECTIONS.md`) moved the model to 0.212 and the standardised logistic baseline to
0.1886, so the margin fell to +0.0234: `RECIPE_FAILS`. Every number in this repository is a
4096-byte-window number and the documents say so.

## "Who buys it?"

Uncleared, and filed in the coverage map's **weakest class** rather than dressed as a finding. The
structural argument for why this family of tasks resists buyers is stated as three labelled
conjectures (C1, C2 and a refinement) with falsifiers, plus a preregistered search for C1's
falsifier that returned `NO_FALSIFIER_FOUND` across 14 candidates (prereg 0008).

## "How do I know the bars weren't set after the results?"

`python3 tools/prereg.py verify` — a hash chain where entry *N* carries entry *N−1*'s hash, NIST
Beacon and drand anchors per entry, and readers frozen by sha256. Two honest limits, stated in the
record itself: the beacon proves **not-before only** (both interpretation artifacts carry that
correction), and precedence over measurements otherwise rests on commit history — which is why the
PR was merged with a merge commit, preserving it.

## "What did you get wrong?"

`CORRECTIONS.md`: thirteen entries at full size, including a published figure our own reproduction
contradicted, an instrument warning grepped out of view before a commit, a wrong reading of our own
null control (an error *against* us, filed anyway), and the audit's thirteen findings. The pattern
of what the gates missed is stated there: they check mechanical honesty, not reasoning between
numbers.

## "Can my engineer verify any of this without trusting you?"

```
bash tools/gates.sh                                  # every gate, one command, exit non-zero on failure
bash tools/pivot/fetch_sources.sh                    # fetch sources; pin_sources.py fails unless they hash to the banked edition
python3 tools/pivot/corpus_manifest.py --check       # prove a rebuilt corpus is byte-identical to ours
```

Corpora rebuild deterministically from shipped sources and generators; the manifest banks
content hashes of every array so the rebuild is *proven* identical, not assumed. 205 mutations across 15 gates certify every gate can fail
(that count is checked against the mutation report by `tools/freshness.py`, because an earlier
version of this sentence said 132 while the artifact said 134); the reproduction that matters most — the audit — is
banked with its kill-list included.
