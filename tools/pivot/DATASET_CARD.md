# Carved-DEFLATE Encoder Provenance — dataset card

> **Status: not yet published.** This card is written before the corpus is finalised so that its
> structure is not shaped by the result. Any row reading `PENDING` is genuinely unmeasured; none of
> them will be filled in by hand — they come from the banked artifacts or they stay `PENDING`.

## What it is

Fragments carved from the **middle** of DEFLATE streams, labelled with the
`(implementation, level)` that produced them.

The point of the dataset is what it *withholds*. Each fragment is a fixed-size window from the
interior of a compressed stream, and it comes with:

- **no header** — so the zlib `FLEVEL` hint, two advisory bits that are routinely wrong anyway, is absent
- **no stream start** — so the dynamic Huffman tables needed to decode the token sequence are absent
- **no plaintext** — so the stream cannot be recompressed and compared
- **not even the stream length** — so compression ratio is not a feature

That is what a forensic carve out of a disk image or a truncated capture actually looks like.

## Why it does not already exist

Every existing tool needs something this dataset deliberately removes:

| Tool | What it needs | Available in a carve? |
|---|---|---|
| `preflate` / `preflate-rs` | the decoded token stream, hence the stream start | no |
| `grittibanzli` | same | no |
| `precomp` | the plaintext, to recompress and compare | no |
| `list-compresslevel.py` | the plaintext | no |

So the incumbents are inapplicable by construction rather than by being outperformed. A white-space
check during the archived trial found **four non-learned tools, zero machine-learning efforts and
zero open datasets at any scale**.

## Label factory

| | |
|---|---|
| Implementations | zlib, zopfli, Intel ISA-L (igzip), libdeflate |
| Classes | 26 `(implementation, level)` configurations |
| Marginal cost per labelled example | one compression call |
| Ground truth | exact — the label *is* the configuration invoked |

## Content

Source bytes are mixed deliberately across content families so a model cannot succeed by memorising
content: Project Gutenberg prose (nine editions PG lists as "Public domain in the USA"; pg5200 is a
copyrighted eBook under the Project Gutenberg License — see Licence below) plus synthetic JSON, CSV, logs, source-code-like
text, base64, packed binary, and mixed-entropy runs.

Every fragment records the source chunk it came from, so evaluation **must** be split by source
chunk. A random split over fragments carved from the same bytes measures content memorisation
rather than encoder identification.

## Known limitations, stated up front

- **Encoders absent from this build**: 7-Zip's deflate, Java's `Deflater`, Go's `flate`, and the
  Cloudflare and Windows zlib forks. A model trained here has not been shown to generalise to them.
- **Incompressible content caps what is achievable.** Measured: base64 and packed-binary sources
  collapse to roughly 14 distinct streams out of 26, because with nothing to match, encoders
  converge on stored or near-minimal blocks. See `artifacts/pivot/channel_capacity.json`.
- **One carve size, and generalisation across carve sizes is now measured and REFUTED.** At a 1024-byte carve the model ties a dumb rule and a 4096-trained model falls to chance (`CARVE_FAILS`, preregistration 0007). Every number on this card is a 4096-byte-window number.
- **No customer, user or partner.** None is claimed.

## Numbers

| | |
|---|---|
| Fragments | 1,300,000 (800,000 train / 260,000 eval, grouped by source chunk) |
| Classes | 26 |
| Chance accuracy | 0.0385 |
| Distinct-stream rate (A1) | 22.27 of 26, collision rate 0.143 |
| Null control (shuffled labels) | 0.0389 vs chance 0.038462 — passes (tolerance 0.02) |
| Best trivial baseline | frozen set: logistic 0.1392; expanded set: depth16_tree 0.1812 |
| Scaling slope, 95% interval | +0.0491 accuracy/decade, 95% CI [+0.0482, +0.0500] over 2.9031 decades |
| Verdict from the frozen reader | **CURVE_ESTABLISHED** |
| Top-1 / top-3 / top-5 at the top rung | 0.2395 / 0.4497 / 0.5694 |
| Accuracy on the most-confident decile | 0.7922 (26000 fragments) |
| Operational verdict (preregistration 0006) | **OUTPUT_USABLE** |

## Licence

Source bytes are Project Gutenberg texts or synthetic. The compliance audit (docs/compliance/LICENSE_AUDIT.md) found they are NOT uniformly public domain: one file, pg5200 (Metamorphosis), self-identifies as a copyrighted Project Gutenberg eBook with its licence terms stripped from the repo copy, and eight of ten files carry no licence text. An earlier version of this line said "public domain" without having checked. The 2026-09-02 follow-up in the same audit re-fetched the terms: pg5200 is distributed under the Project Gutenberg License with no additional copyright-holder terms in the file (§1.E.3), so use is bound by §1.E.1–1.E.7 — no fee, licence kept attached — and whether terms exist outside the file COULD NOT be verified. The sources are re-fetched, never committed, and pinned to the banked edition by `tools/pivot/pin_sources.py` because gutenberg.org re-edits files in place (pg1342 changed between 2026-08-25 and 2026-09-02; CORRECTIONS.md). The fragments are mechanical
derivatives of those bytes. Code is Apache-2.0.
