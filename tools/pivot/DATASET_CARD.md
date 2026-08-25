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
content: public-domain prose (Project Gutenberg) plus synthetic JSON, CSV, logs, source-code-like
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
- **One carve size.** Generalisation across carve sizes is not established.
- **No customer, user or partner.** None is claimed.

## Numbers

| | |
|---|---|
| Fragments | PENDING |
| Classes | 26 |
| Chance accuracy | 0.0385 |
| Distinct-stream rate (A1) | 22.27 of 26, collision rate 0.143 |
| Null control (shuffled labels) | PENDING |
| Best trivial baseline | PENDING |
| Scaling slope, 95% interval | PENDING |
| Verdict from the frozen reader | PENDING |

## Licence

Source bytes are public domain (Project Gutenberg) or synthetic. The fragments are mechanical
derivatives of those bytes. Code is Apache-2.0.
