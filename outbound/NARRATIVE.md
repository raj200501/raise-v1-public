# NARRATIVE — the spoken raise, in the founder's voice

Every number in this document exists in a banked artifact under `artifacts/` at the written
precision, enforced by `.venv/bin/python tools/claimcheck.py outbound/NARRATIVE.md`. Failures are
named at the same volume as passes. The words **"no buyer yet"** appear inside the first ninety
seconds by design, because burying that sentence is how trust dies in a meeting.

---

## The ninety-second version

> I'll tell you the ending first: we have one real, preregistered scaling curve, and **no buyer
> yet**. Here is how we got both halves of that sentence.
>
> Before we measured anything, we built the instrument. Bars frozen and hash-chained before the
> data existed, verdict readers frozen by hash, and every gate proven able to fail —
> 205 deliberate mutations, 205 detected, 0 survived.
>
> Then we ran the search the thesis demanded: 99 candidate domains over three rounds, 8 through
> adversarial review with default posture reject, 0 selected. We published that negative under a
> rule frozen before the final round ran.
>
> The pivot found one real curve: recover which of 26 DEFLATE encoder configurations produced a
> fragment carved from the middle of a compressed stream — no header, no plaintext. Accuracy
> 0.2395 at the top rung against 0.038462 chance, rising +0.0491 per decade over 2.9031 decades,
> clearing margins frozen in advance.
>
> Then we measured where our own result breaks, and published that with the same confidence: at a
> 1024-byte carve the same protocol fails its own bar, and at 2048 it fails on every reading —
> by 0.0025 against the frozen baselines and by 0.0206 against the strongest one. Every
> number I will ever quote you is a 4096-byte-window number.
>
> Then we ran 54 adversarial agents against the whole record. 13 findings survived refutation; all
> 13 were fixed by measurement and the full audit is published, rejected findings included.
>
> Nobody has been contacted, no customer is claimed. What we are asking you to underwrite is the
> instrument, the curve, and a team that publishes its own negatives.

*(At a measured speaking pace this is about ninety seconds.)*

---

## The five-minute version

> Up front, so it is not buried: there is **no buyer yet** — none contacted, none claimed. What
> follows is why the record is still worth your five minutes.

**The discipline came first.**

> Before any measurement, we built the thing that would keep us honest. 13 preregistrations,
> hash-chained so nothing can be silently inserted between two that already exist, each anchored
> to public randomness beacons — NIST and drand — with the verdict-emitting readers frozen by
> sha256 before their data existed. Then we proved the instrument itself can fail:
> 205 deliberate mutations across 15 gates, 205 detected, 0 survived. A gate that cannot fail is decoration, so
> we broke every one on purpose and checked that it noticed.

**The search, and the negative we published.**

> The thesis was that there are domains where labels manufacture themselves for free and accuracy
> rises with data. We searched for one: 99 candidate domains across three rounds, 8 put through
> adversarial review with default posture reject — and 0 selected. The stopping rule was frozen
> before the final round ran, and the verdict, no viable domain found, is published as a finding,
> not hidden as a failure. The search still paid: three measured laws about *why* these domains
> die, each retiring an entire candidate family. A fourth round was later authorised under its own
> preregistration with a higher bar. It also found nothing, and we published that too.

**The curve.**

> The pivot produced one result that is a claim about the world. The task: take a window carved
> from the middle of a DEFLATE stream — no header, no stream start, no plaintext — and recover
> which of 26 implementation-and-level configurations produced it. The label factory is free:
> compress any bytes under a configuration and the label is the configuration. Accuracy runs
> 0.0988, 0.1415, 0.1965, 0.2395 across rungs from 1000 to 800000 manufactured fragments, against
> chance of 0.038462. The slope is +0.0491 accuracy points per decade over 2.9031 decades, and the
> 95% interval — cluster-corrected after our own audit found the original too tight — is
> [0.0482, 0.0500]. The margin over the strongest trivial baseline is +0.1003 under the frozen
> reading and +0.0583 under a stricter reading we committed to before the numbers existed; both
> clear the preregistered 0.05. And we tell you where the signal lives rather than quoting the
> mixture: structured content — csv, log, json — rises at roughly +0.09 per decade, about ten
> times chance at the top rung, while incompressible content sits near a measured collision
> ceiling.

**The operational reading.**

> For the one setting where a carved fragment is the real input — forensic carving — a single best
> guess is the wrong question. Under a separate preregistration, frozen before any top-k number
> existed: the top-5 shortlist reaches 0.5694, a +0.1084 margin over the strongest baseline; the
> most-confident decile scores 0.7922. The shortlist improves at +0.0985 per decade — roughly
> twice the top-1 slope. The output has the shape a forensic use would need. Shape is not demand,
> and I'll come back to that.

**The boundary, stated with the same confidence as the passes.**

> Then we attacked our own result under preregistration, and it failed. At a 1024-byte carve the
> model ties a dumb rule — margin +0.0099 against the same 0.05 bar — and a 4096-trained model
> transferred to 1024-byte fragments scores 0.0403, which is chance. We measured away the easy
> excuse before freezing the bar: the byte-identity ceiling barely moves, 20.9125 distinct streams
> of 26 at 4096 against 20.79 at 512, so the information is present at the shorter window and this
> is a modelling failure, and we say so in those words. A byte-sequence CNN did not rescue it —
> 0.0849 against the hand-engineered 0.1165 — and a corrected-head variant came back inconclusive,
> which its frozen reader states rather than counting it either way. So: every number I have
> quoted is a 4096-byte-window number, and the forensic setting does not guarantee that window.
> That caveat is in every document we ship, because it is the most important sentence in the
> record. We then measured the midpoint under a third preregistration, with the expected
> outcome written down first: at 2048 bytes the model reaches 0.1741 against a logistic baseline
> of 0.1266 — +0.0475 against the 0.05 bar, 0.0025 short — and +0.0294 against a depth-16
> tree at 0.1447, 0.0206 short on the reading we froze as binding; transfer from 4096 lands
> at 0.0455 against a 0.1266 baseline and fails its margin. The boundary of our result is
> bracketed to (2048, 4096], and the near-miss on the slack reading is published beside the
> clear miss on the strict one.

**The audit we invited, and what it found.**

> Then we ran 54 independent adversarial agents against the repository — six hostile lenses, every
> finding attacked by two refuters instructed to kill anything wrong or vague. 13 findings
> survived, three of them critical: a bootstrap that contradicted our own split, a split guarantee
> that was false for one of eight content families, and subagent evidence mislabelled first-hand.
> All 13 were fixed by measurement, and the audit record is banked with its rejected findings
> included, so the filter itself can be audited. The corrections ledger now carries 13 entries at
> full size — including one where the error ran *against* our interest and was filed anyway. And
> the uncomfortable meta-finding is published with it: every gate passed while all of those
> defects were live, because gates check that numbers trace, not that the reasoning between them
> is sound. Adversarial review is the only thing that caught them, which is why it is now part of
> the process.

**The close.**

> So here is the honest inventory. A validated instrument that reproduces on a cold clone. One
> real curve with its boundaries measured by the same instrument. A corrections ledger that costs
> us something to keep. A verification map that prints its weakest class first — 14 of 96 claims
> we ourselves cannot currently re-derive, and it says so. And no buyer yet: G5, a named buyer
> type, is the gate this work has not cleared, and no result in the repository could have cleared
> it, because that work happens outside the repository. We are raising to do exactly that work,
> on top of an evidence base built so that you never have to take our word for anything —
> `bash tools/gates.sh` on a cold clone, exit non-zero on any failure. If you want the flattering
> version, we cannot give it to you. We built a machine that stops us.

*(At a measured speaking pace this is about five minutes.)*

---

## The hard-questions crib — the spoken one-sentence answer to each diligence question

The diligence map at `docs/DILIGENCE.md` carries **nine** question headings (the brief for this
document said eight; the file itself has nine, so all nine are answered here — see COULD NOT
VERIFY below). Each answer is one sentence, meant to be said out loud, unhedged where the record
allows and explicitly hedged where it does not.

**"Is the slope real, or a seed artifact?"**
> Measured, both ways: the interval is a cluster bootstrap over the 10000 held-out source chunks —
> corrected to [0.0482, 0.0500] after our own audit found the original anti-conservative — and two
> full-pipeline replications at independent seeds give slopes of 0.0486 and 0.0478 against the
> published 0.0491, a spread of 0.0014, with the published run the lowest of the three on margin.

**"Is it memorising content rather than identifying encoders?"**
> The split groups by source chunk, retraining on shuffled labels falls to 0.0389 — chance — and
> when the audit found the grouping guarantee false for one of eight families, excluding that
> family made every rung and the slope better, not worse, so the leak was hurting us, not helping.

**"Won't a frontier model just do this?"**
> The input is mid-stream entropy-coded bitstream with nothing renderable in it, and the measured
> stand-ins for a clever prior with no task data — logistic regression and depth-16 trees trained
> on the same 800000 fragments — are exactly what every headline margin is scored against.

**"Where does the signal actually live?"**
> In structured content — csv, log and json rise at roughly +0.09 per decade at about ten times
> chance — while incompressible families sit at a measured collision ceiling, and we publish that
> decomposition rather than letting the headline mixture speak for the whole task.

**"Does it survive realistic carve sizes?"**
> No — at 1024 bytes the model ties a dumb rule, at 2048 it misses the bar on every reading (by
> 0.0025 against the frozen baselines, by 0.0206 against the strongest), and transfer fails its
> margin at both sizes — 0.0403 at 1024, which is chance, and 0.0455 at 2048 against a 0.1266
> baseline; we preregistered those tests ourselves, they failed, and every number we quote is a
> 4096-byte-window number labelled as such.

**"Who buys it?"**
> No one yet — no buyer has been contacted, none is claimed, and that gap is filed in our
> verification map's weakest class rather than dressed up as a finding, because clearing it is
> precisely what this raise is for.

**"How do I know the bars weren't set after the results?"**
> Run `tools/prereg.py verify` — a hash chain with public beacon anchors proves ordering and
> not-before time — and the honest limit, that a beacon cannot prove not-after, is written into
> the record itself rather than discovered by you.

**"What did you get wrong?"**
> 12 corrections at full size, including a published figure our own reproduction contradicted, an
> instrument warning I personally grepped out of view, and 13 audit findings — the pattern being
> that our gates check mechanical honesty, not reasoning, which the ledger states out loud.

**"Can my engineer verify any of this without trusting you?"**
> Yes — `bash tools/gates.sh` on a cold clone runs every gate with two CPU-only dependencies and
> exits non-zero on any failure, and the corpus manifest proves a rebuilt corpus byte-identical
> rather than assuming it.

---

## What the speaker must NOT say

- **No market size, no dollar figure, no customer count.** None exists in any artifact, so none
  may be spoken. If asked for TAM: "we have not measured one and will not invent one in a
  meeting."
- **Never quote a 4096-byte number without the window.** "It works" is a misquote; "it works at
  4096" is the claim.
- **Never read the permutation p of 0.0417 as "just under 0.05".** It is the arithmetic floor of
  an exact test over four rungs and cannot be smaller.
- **Quote seed robustness exactly.** Three runs, slope spread 0.0014, published run lowest on
  margin — and never rounder than that (`artifacts/pivot/seed_robustness.json`).
- **No superlatives without an artifact.** "Preregistered", "cluster-corrected", "audited" are
  backed; "best-in-class", "unprecedented", "massive" are not, for anything, anywhere.

## COULD NOT VERIFY

- ~~Seed variance of the headline slope~~ — resolved after this document's first draft: two
  replications are banked in `artifacts/pivot/seed_robustness.json` and quoted in the crib above.
- **The count of diligence questions.** The brief for this document specified eight questions;
  `docs/DILIGENCE.md` contains nine question headings. All nine are answered above rather than
  silently dropping one.
- **That any buyer would pay.** No buyer has been contacted; `establishes_a_buyer: false` is
  emitted by the reader itself, and nothing in this narrative asserts otherwise.
