# Licensing and data-provenance audit

Date: 2026-08-31. Auditor: Compliance department lead. Method: every claim below was
verified first-hand against this repository — a file and line, a command run from the repo
root, or a hash comparison. Nothing is asserted from memory. Where the repository does not
contain the evidence, the row says **COULD NOT VERIFY** and names what an agency or upstream
check would have to establish.

Scope: (1) `data/pivot/src` source texts and the synthetic corpus, (2) Python dependencies
declared in `requirements*.txt`, (3) the GNSS products used by the EphemErr study,
(4) the repository's own licence versus the code and the outbound documents.

Claimcheck status: this file lives under `docs/`, not `outbound/`, so the claimcheck gate
does not apply to it. It was nevertheless run
(`.venv/bin/python tools/claimcheck.py docs/compliance/LICENSE_AUDIT.md`): it reports FAIL
on 13 numbers, every one of which is a file/line coordinate inside a source text or a
Project Gutenberg ebook ID — locations and identifiers read directly from files, not
measurements, and each is reproducible by the command cited beside it. No number in this
document is a measurement, an estimate, or a market/dollar figure. If any part of this
audit is ever lifted into `outbound/`, those coordinates must be allowlisted with reasons
or dropped.

This document also discharges, for the pivot and GNSS corpora, the promise at
`README.md:99-100` ("Data licences are recorded per-corpus in `docs/`") — a promise that,
before this audit, nothing in `docs/` actually fulfilled (`grep -rn -i licen docs/` matched
only a figurative use in `OPERATING_RULES.md:35`).

---

## 1. `data/pivot/src` — the ten Project Gutenberg source files

How each was verified: every file was opened; identity comes from the in-file title/author
block or PG header, not from the filename. `sha256sum` of every file was compared against the
banked manifest `artifacts/pivot/corpus_manifest.json` (`sources_sha256` key): **all 10 match**,
so the bytes on disk are the exact bytes the banked corpus was built from. These files are
**not committed to git** — `.gitignore:17` ignores `data/pivot/` and
`git ls-files data/pivot` returns nothing; they are re-fetched by
`tools/pivot/fetch_sources.sh`.

| File | Work (verified in-file) | In-file licence marker | How verified |
|---|---|---|---|
| `pg11.txt` | Alice's Adventures in Wonderland, Lewis Carroll — "THE MILLENNIUM FULCRUM EDITION 3.0" | START/END markers only; PG header **stripped**, no licence text in file | title/author at lines 8-10; markers at lines 1 and 3384 |
| `pg1342.txt` | Pride and Prejudice, Jane Austen | START/END markers only; header **stripped** | "Jane Austen" line 30, "Pride and Prejudice" line 109; markers at lines 1 and 14537 |
| `pg1661.txt` | The Adventures of Sherlock Holmes, Arthur Conan Doyle | **Full PG header** ("This eBook is for the use of anyone anywhere in the United States... under the terms of the Project Gutenberg License", lines 4-10) **and full licence text** ("START: FULL LICENSE", line 11982) | header lines 1-23; release-date block line 16 |
| `pg1952.txt` | The Yellow Wallpaper, Charlotte Perkins Gilman | START/END markers only; header **stripped** | title/author lines 6-8; markers at lines 1 and 849 |
| `pg2600.txt` | War and Peace, Leo Tolstoy, tr. Louise and Aylmer Maude | **Full PG header and full licence text** (grep "FULL LICENSE" matches) | header lines 1-26 (Title/Author/Translators block); markers at 26 and 65685 |
| `pg2701.txt` | Moby-Dick; or, The Whale, Herman Melville | START/END markers only; header **stripped** | title/author lines 6-10; markers at lines 1 and 21936 |
| `pg5200.txt` | Metamorphosis (Gregor Samsa text; PG eBook #5200) | **"\*\* This is a COPYRIGHTED Project Gutenberg eBook, Details Below \*\*"** (line 1) — but the "Details Below" are **absent**: the file ends at the END marker (line 1874) and contains no copyright details, no translator credit, no licence text | banner lines 1-2; `grep -c -i "copyright"` = 2 (the banner only); `grep -i wyllie` = no match |
| `pg74.txt` | The Adventures of Tom Sawyer, Mark Twain | START/END markers only; header **stripped** | title/author lines 5-8; markers at lines 1 and 8894 |
| `pg84.txt` | Frankenstein; or, the Modern Prometheus, Mary Wollstonecraft (Godwin) Shelley | START/END markers only; header **stripped** | title/author lines 3-7; markers at lines 1 and 7362 |
| `pg98.txt` | A Tale of Two Cities, Charles Dickens | START/END markers only; header **stripped** | title/author lines 4-8; markers at lines 1 and 15905 |

### Findings

**F1 — pg5200 contradicts the repo's own "public domain" statements.**
`tools/pivot/fetch_sources.sh:3` says the sources are "Public domain in the United States",
and `tools/pivot/DATASET_CARD.md:84` says "Source bytes are public domain (Project Gutenberg)
or synthetic". The file `pg5200.txt` says, in its own first line, that it is a
**COPYRIGHTED** Project Gutenberg eBook. A copyrighted PG eBook is distributable only under
the terms stated in that eBook — and those terms have been stripped from this copy. Both
repo statements are wrong as written for 1 of the 10 files.
**COULD NOT VERIFY** the actual terms of pg5200 (typically a copyrighted translation
distributed with a non-commercial or PG-License restriction): the details the banner points
to are not in the file, and no copy of them exists anywhere in the repository. Before any
release of the corpus or of fragments derived from it, the eBook #5200 licence block must be
re-fetched from gutenberg.org and either (a) the terms complied with, or (b) pg5200 dropped
and the corpus rebuilt (the banked manifest hash for pg5200,
`6b023bfb...`, would change, so this is detectable).

**F2 — eight of ten files carry no licence text at all.** Only `pg1661.txt` and
`pg2600.txt` retain the PG header and the full licence (which includes the Project
Gutenberg™ trademark conditions, `pg1661.txt:11982` ff.). The other eight were reduced to
bare START/END markers, so the repository copy itself does not evidence its own
redistribution basis. For the US-public-domain works the *text* is free regardless, but the
PG **trademark** terms (Section 1.B of the licence in `pg1661.txt`) attach to distributing
the files as "Project Gutenberg" eBooks. Mitigation already in place: the files are not
committed and not redistributed by this repo (`.gitignore:17`); each user fetches their own
copy from gutenberg.org via `fetch_sources.sh`.
**COULD NOT VERIFY** public-domain status of the specific *editions* from the files alone
(e.g. pg11's "Millennium Fulcrum Edition 3.0" is an edition statement, and pg2600 is the
Maude *translation* — translations carry their own copyright status). PG's catalog entries
for these ten IDs should be re-checked at gutenberg.org before any redistribution of the
bytes themselves.

**F3 — what `fetch_sources.sh` actually downloads.** Verified from
`tools/pivot/fetch_sources.sh:8-12`: exactly the ten IDs 1342, 2701, 84, 1661, 98, 2600,
1952, 11, 5200, 74, each from `https://www.gutenberg.org/files/<id>/<id>-0.txt` with a
fallback to `https://www.gutenberg.org/cache/epub/<id>/pg<id>.txt`, with user-agent
`raise-v1-research/1.0`. It downloads nothing else and skips files already present
(line 10), which is why the on-disk copies (with their stripped headers) persist unchanged —
and they hash-match the banked manifest, so they are the bytes actually measured.

**F4 — synthetic content is clean.** `tools/pivot/corpus.py` generates the other seven
content families (`json`, `csv`, `log`, `code`, `base64`, `binary`, `mixed`; the `SYNTH`
dict at lines 131-132 and `FAMILIES` at line 133) from `random.Random` draws over hardcoded
syllable/identifier lists (lines 58-128). No third-party corpus, no scraped data, no
embedded text beyond the Gutenberg pool loaded by `load_real()` (lines 136-144). The
derived `.npz` feature caches under `data/pivot/` are mechanical derivatives of these bytes
and are likewise gitignored.

---

## 2. Python dependencies declared in `requirements*.txt`

The three requirements files declare six packages (floors, not pins — `requirements.txt:1-4`).
Licences were read from the installed metadata under
`.venv/lib/python3.11/site-packages/<pkg>.dist-info/METADATA` (and the bundled
`licenses/` texts), not from memory. Command used:
`grep -m1 "^License" .venv/lib/*/site-packages/*.dist-info/METADATA` plus reading each
`dist-info/licenses/` file.

| Declared in | Package (installed version) | Licence (from installed metadata) | How verified |
|---|---|---|---|
| `requirements.txt` | numpy 2.4.6 | `License-Expression: BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` | METADATA; `licenses/LICENSE.txt` opens "Copyright (c) 2005-2025, NumPy Developers" BSD text |
| `requirements.txt` | scikit-learn 1.9.0 | `License-Expression: BSD-3-Clause` | METADATA; bundled licence opens "BSD 3-Clause License, Copyright (c) 2007-2026 The scikit-learn developers" |
| `requirements-pivot.txt` | zopfli 0.4.3 | `License: Apache-2.0` | METADATA; bundled licence is the Apache-2.0 text |
| `requirements-pivot.txt` | isal 1.8.0 | `License-Expression: PSF-2.0` | METADATA; `licenses/LICENSE` opens "PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2" |
| `requirements-pivot.txt` | deflate 0.9.0 | MIT (classifier `License :: OSI Approved :: MIT License`; no `License:` field) | METADATA classifier; `licenses/` file opens "MIT License, Copyright (c) 2020 Dan Watson" |
| `requirements-repro.txt` | python-sat 1.9.dev15 | `License: MIT` | METADATA; `licenses/LICENSE.txt` opens "MIT License, Copyright (c) 2018 Alexey Ignatiev, Joao Marques-Silva, Antonio Morgado" |

All six are permissive (BSD/MIT/Apache/PSF family). A sweep of **every** `dist-info` in the
venv (31 packages, same command) found no GPL-, LGPL- or AGPL-licensed package; the
strongest obligations present are attribution-style (BSD/MIT/Apache/PSF, plus
`packaging`'s "Apache-2.0 OR BSD-2-Clause" dual and torch's compound
"Apache-2.0 AND ... AND BSD-3-Clause AND BSL-1.0 AND MIT").

### Findings

**F5 — undeclared imports.** Two tools import packages that appear in **no**
`requirements*.txt`: `tools/pivot/run_byte_model.py` imports `torch` (installed:
torch 2.13.0+cpu, compound permissive expression above) and
`tools/repro/lichess_clock_curve.py` imports `zstandard` (installed: zstandard 0.25.0,
`License-Expression: BSD-3-Clause`). No licence problem, but the declared dependency
surface understates the real one; a diligence reviewer diffing imports against requirements
will find this in minutes.

**F6 — bundled native code.** `isal` wraps Intel's ISA-L C library and `python-sat` ships
compiled SAT solvers (`pysolvers.cpython-311-x86_64-linux-gnu.so` in site-packages). The
installed metadata states only the Python package's licence (PSF-2.0 and MIT
respectively). **COULD NOT VERIFY** from the repository the licences of the *bundled*
native components (ISA-L itself; the individual solver engines inside python-sat, which
upstream sources under varying MIT-like terms) — these must be confirmed from the upstream
projects before any redistribution of the venv or of wheels.

---

## 3. EphemErr study — IGS/BKG/ESA GNSS products

**What the repo states.** `artifacts/ephemerr/pipeline_validation.json` line 18:
`"licence": "public IGS/ESA products, no authentication"` — that one phrase is the entire
recorded terms basis. The same artifact's `corpus` block (lines 15-23) names the products:
broadcast navigation `BRDC00IGS_R_20250010000_01D_MN.rnx.gz` from BKG, precise orbit
`ESA0OPSFIN_20250010000_01D_05M_ORB.SP3.gz` and precise clock
`ESA0OPSFIN_20250010000_01D_30S_CLK.CLK.gz` from ESA, for day 2025-001.

**What the fetch script actually pulls.** `tools/gnss/fetch.sh:25-30`: BRDC files from
`https://igs.bkg.bund.de/root_ftp/IGS/BRDC/...` and ESA final orbit/clock from
`http://navigation-office.esa.int/products/gnss-products/...` (note: the ESA URLs are plain
`http`), default day range 1-21 of 2025, user-agent `raise-v1-research/1.0 (email)`.
`data/gnss/` currently holds 63 files.

**What is committed to git.** Although `.gitignore:21` now ignores `data/gnss/`,
`git ls-files data/gnss` shows **4 product files are tracked**: `brdc001.rnx.gz`,
`brdc_001.rnx.gz`, `clk_001.CLK.gz`, `sp3_001.SP3.gz`. Committing them is
**redistribution** of BKG/ESA products, which is a stronger act than fetching for own use
and is exactly what an agency terms-of-use document governs.

### Findings

**F7 — the terms basis is an assertion, not a record. COULD NOT VERIFY:** no BKG, IGS, or
ESA terms-of-use text, data-policy citation, or licence URL exists anywhere in the
repository (`grep -rn -i "licen|terms" tools/gnss/` matches nothing). "No authentication
required" is a fact about access, not a licence. Before diligence, the following must be
re-checked with the agencies and the answers filed here:

1. **IGS data policy** — the IGS terms of use governing IGS-branded products (the BRDC file
   is an IGS combined product, `BRDC00IGS_R_...`), including required attribution/citation.
2. **BKG** — terms for `igs.bkg.bund.de` root_ftp downloads (BKG is a German federal
   agency; its open-data terms typically require source attribution).
3. **ESA navigation office** — terms for `navigation-office.esa.int` final products
   (`ESA0OPSFIN`), specifically whether **redistribution** (the 4 committed files) and
   **commercial use** (a Series A company's product development) are permitted, and what
   attribution ESA requires.
4. Whether keeping the 4 product files in git history is acceptable, or whether they should
   be removed and re-fetched like the other 59.

The scientific-community norm for these products is open access with attribution, and the
repo's behaviour (public endpoints, no credentials, polite user-agent) is consistent with
that — but a norm is not a recorded licence, and this audit does not convert one into the
other.

---

## 4. The repository's own licence

| Item | Status | How verified |
|---|---|---|
| `LICENSE` (repo root) | Apache License 2.0, "Copyright 2026 Raj Kashikar" (line 17); the file is the short-form notice with a pointer to the full text, not the full 10-section Apache text | read `LICENSE` in full (19 lines) |
| README licence statement | `README.md:99-100`: "Apache-2.0 (see `LICENSE`). Data licences are recorded per-corpus in `docs/` and are not assumed to be the same as the code licence." | read README |
| Code files (`tools/**`, `tests/**`) | No per-file copyright or SPDX headers anywhere (`grep -rn -i "apache|spdx|licen" tools/*.py tools/pivot/*.py tools/gnss/*.py` matches only a variable name in `render_domain_selection.py`). Legally covered by the root LICENSE; per-file headers are an Apache-2.0 convention, not a requirement | grep across tools/ and tests/ |
| Outbound documents (`outbound/*.md`, `.html`) | Carry **no** licence or copyright notice of their own; as committed repo content they fall under the root Apache-2.0 grant, which permits recipients to reuse and modify them. If the company does not intend investor-facing prose to be Apache-licensed, it should say so | grep of `outbound/` for licence/copyright terms |
| Dataset card | `tools/pivot/DATASET_CARD.md:82-85` states "Source bytes are public domain (Project Gutenberg) or synthetic... Code is Apache-2.0" — the public-domain half is contradicted by pg5200 (Finding F1) | read the card's Licence section |

### Findings

**F8 — the README's data-licence promise was unfulfilled.** `README.md:99-100` says data
licences "are recorded per-corpus in `docs/`". Before this document, no file under `docs/`
recorded any data licence. This audit now records the pivot corpus (§1) and the GNSS corpus
(§3); the committed `data/asmprov/` NCBI metadata corpus (public NCBI assembly metadata per
`data/asmprov/README.md`) was outside this audit's assigned scope and still needs its own
recorded basis — noted here so the gap is visible rather than silently narrowed.

**F9 — LICENSE text form.** The root `LICENSE` is the abbreviated boilerplate block (the
"Licensed under the Apache License..." notice plus a link), not the canonical full Apache-2.0
text. Diligence checklists commonly flag this; dropping in the full text is a one-file fix
and changes nothing substantive.

**F10 — Apache-2.0 covers outbound prose by default.** See table row above: nothing exempts
`outbound/` from the code licence. Decide deliberately whether that is intended.

---

## Consolidated COULD NOT VERIFY list

1. The distribution terms of `pg5200.txt` (copyrighted PG eBook; terms stripped from the
   repo copy) — re-fetch the licence block from gutenberg.org (F1).
2. Public-domain status of the specific editions/translations for the eight
   header-stripped Gutenberg files, from the files alone (F2).
3. Licences of native components bundled inside `isal` and `python-sat` wheels (F6).
4. IGS, BKG, and ESA terms of use for the GNSS products — including redistribution of the
   4 committed files and commercial use; nothing in the repo records them (F7).
5. Licence basis of the committed `data/asmprov/` NCBI corpus — out of assigned scope,
   flagged for a follow-up audit (F8).

## Reproducing this audit

```
sha256sum data/pivot/src/*.txt                       # compare to artifacts/pivot/corpus_manifest.json sources_sha256
head -2 data/pivot/src/pg5200.txt                    # the COPYRIGHTED banner
grep -n "FULL LICENSE" data/pivot/src/*.txt          # only pg1661, pg2600
grep -m1 "^License" .venv/lib/*/site-packages/*.dist-info/METADATA
git ls-files data/gnss                               # the 4 committed product files
grep -n licence artifacts/ephemerr/pipeline_validation.json
```
