# raise-v1 — the evidence, its statistics, and its boundaries

Every number on this page traces to a machine-readable artifact in this repository at the written
precision, enforced by `tools/claimcheck.py` with zero allowlist entries. Rows marked `PENDING`
are genuinely unmeasured and are filled mechanically from artifacts or left as they are.

## What is claimed

One task — recover which of **26** DEFLATE `(implementation, level)` configurations produced a
window carved from the **middle** of a compressed stream, with no header, no stream start, no
plaintext — measured under bars frozen and hash-chained **before the data existed**, delivering:

- a scaling curve that clears every preregistered clause (`CURVE_ESTABLISHED`, prereg 0003);
- an operationally usable output — shortlist plus abstention — under its own preregistration
  (`OUTPUT_USABLE`, 0006);
- and its own boundaries, measured with equal force (`CARVE_FAILS` at 1024 bytes, 0007;
  `BYTE_MODEL_FAILS`, 0009).

## What is not claimed

**No customer, no user, no partner, no buyer.** G5 — a named buyer type — is uncleared, filed in
the verification map's weakest class, and no result here could have cleared it. Every number below
is a **4096-byte-window** number; at 1024 bytes the task fails its own bar.

## The headline curve, with corrected statistics

| Rung (manufactured fragments) | 1000 | 10000 | 100000 | 800000 |
|---|---:|---:|---:|---:|
| Accuracy (chance 0.038462) | 0.0988 | 0.1415 | 0.1965 | **0.2395** |

Slope **+0.0491** accuracy points per decade over **2.9031** decades, r² **0.9978**. The 95%
interval is a **cluster bootstrap over the 10000 held-out source chunks** — the dependence unit the
grouped split declares — giving **[0.0482, 0.0500]**. An adversarial audit found the originally
published fragment-level interval anti-conservative (about half again as wide once corrected); the
superseded values are retained in
the artifact beside the corrected ones. Null control: shuffled labels fall to **0.0389**.

Margins over trivial baselines trained on the same 800000 fragments as the top rung:

| Reading | Best baseline | Margin | Bar |
|---|---:|---:|---:|
| Frozen baseline set | logistic 0.1392 | **+0.1003** | 0.05 |
| All baselines, deep trees included | depth-16 tree 0.1812 | **+0.0583** | 0.05 |
| Frozen set, leaked family excluded | logistic 0.1438 | **+0.1073** | — |
| All baselines, leaked family excluded | depth-16 tree 0.1891 | **+0.0620** | — |

The last two rows exist because the audit found gutenberg-family source bytes straddle the
train/eval boundary (windows into one shared pool). Excluding that family **widens** both margins —
the defect was depressing the headline, not inflating it — and that is stated together with the
defect, not instead of it.

## Where the curve lives: per-family statistics

Per-family slopes with cluster-bootstrap 95% intervals, from the banked per-example scores:

| Family | Top-rung accuracy | Slope /decade | 95% CI |
|---|---:|---:|---|
| csv | 0.3888 | **+0.0906** | [0.0887, 0.0926] |
| log | 0.3756 | **+0.0909** | [0.0892, 0.0927] |
| json | 0.3581 | **+0.0901** | [0.0883, 0.0920] |
| code | 0.2944 | **+0.0690** | [0.0672, 0.0708] |
| gutenberg | 0.1596 | +0.0266 | [0.0253, 0.0279] |
| base64 | 0.1221 | +0.0136 | [0.0126, 0.0147] |
| binary | 0.1049 | +0.0097 | [0.0087, 0.0107] |
| mixed | 0.1143 | +0.0028 | [0.0020, 0.0037] |

The headline slope is a mixture: on **structured content the curve rises at roughly +0.09 per
decade** — nearly double the headline — with top-rung accuracy about **ten times chance**, while
incompressible families sit near the byte-identity collision ceiling (**14.667** and **14.75**
distinct streams of 26 for base64 and binary). Every interval excludes zero and is reported either
way.

## Operational reading (preregistration 0006)

| | Model | Best baseline | Margin |
|---|---:|---:|---:|
| Top-5 accuracy | 0.5694 | depth-16 tree 0.4610 | **+0.1084** |
| Most-confident-decile accuracy | 0.7922 | depth-16 tree 0.6937 | **+0.0985** |

Top-5 slope **+0.0985** per decade, cluster interval **[0.0971, 0.0999]** — the shortlist improves
about twice as fast as the single guess. The selective clause was scored under the strictest
reading available, fixed before the run; the looser reading would have given **+0.2510**.

## The boundaries, measured with the same instrument

- **1024-byte carve: `CARVE_FAILS`.** Within-size margin **+0.0099** against a 0.05 bar; a
  4096-trained model transfers at **0.0403** — chance. The information is present at 1024 (the
  collision ceiling barely moves: 20.9125 → 20.79 across 4096 → 512), so this is a modelling
  failure and is reported as one.
- **A byte-sequence CNN does not rescue it** (0009): 0.0849 against the hand-engineered 0.1165 and
  a byte-histogram logistic at 0.0943. A corrected-head variant (0010) was inconclusive under its
  frozen recipe, and its reader says so rather than counting it either way.

## Seed robustness

Two full-pipeline replications at independent seeds — fresh grouped split, fresh shuffles, fresh
model initialisation each run (`artifacts/pivot/seed_robustness.json`):

| Seed | Slope /decade | Top rung | Frozen margin | Null control |
|---|---:|---:|---:|---:|
| 20260825 (published) | +0.0491 | 0.2395 | +0.1003 | 0.0389 |
| 7 | +0.0486 | 0.2425 | +0.1116 | 0.0384 |
| 1234567 | +0.0478 | 0.2415 | +0.1100 | 0.0377 |

Slope spread across the three runs: **0.0014** — smaller than any single run's cluster interval.
Every run clears the frozen 0.05 margin; every null control sits at chance; and the **published run
is the lowest of the three** on both top rung and margin, so seed choice did not flatter it. These
replications cannot revise 0003's verdict — its frozen scope was one seed — they measure whether a
rerun would have said something different. It would not have.

## The instrument these numbers passed through

**10** preregistrations, hash-chained (entry *N* carries entry *N−1*'s hash) and anchored to NIST
Beacon 2.0 and drand; readers frozen by sha256 before their data existed.
**166** deliberate mutations across **14** gates, **166** detected, **0** survived — every gate provably capable of
failing. **11** corrections filed against this work at full size, including a **54-agent
adversarial audit** whose 13 confirmed findings (three critical) were each fixed — the load-bearing ones by new measurement,
with the audit record banked — rejected findings included — so the filter itself can be audited.

## Verify on a cold clone

```
bash tools/gates.sh
```

One command, every gate, exit non-zero on any failure. Two dependencies, CPU-only.
