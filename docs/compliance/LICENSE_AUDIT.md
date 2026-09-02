# Licensing and data-provenance audit

**Status, 2026-09-02:** the five COULD NOT VERIFY items of the 2026-08-31 audit below were
re-checked first-hand against the upstream documents (fetched from this container, hashed into
`docs/compliance/sources/MANIFEST.json`, licence texts committed verbatim under
`docs/compliance/sources/`). Three are resolved, two are narrowed, three new findings were made
(F11–F13, one of them a non-commercial licence inside the venv), and the 2026-08-31 text is kept
unchanged as the record of what was known then. See **§5, the 2026-09-02 follow-up**, and the
**updated consolidated list** at the end.

---

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
git ls-files data/gnss                               # the 4 committed product files (untracked on 2026-09-02; see §5.4)
grep -n licence artifacts/ephemerr/pipeline_validation.json
```

---

## 5. Follow-up, 2026-09-02 — the COULD NOT VERIFY list, re-checked at the source

Method: each upstream document was fetched from this container with
`curl -A raise-v1-research/1.0` on 2026-09-02 and its sha256 recorded in
`docs/compliance/sources/MANIFEST.json` (which also lists the three hosts that could not be
reached and why). Licence texts are committed verbatim under `docs/compliance/sources/`. Every
quotation below is copied from the fetched bytes, not from memory. This section makes no legal
determination; it records what the documents say and what this repository does.

### 5.1 pg5200 (Metamorphosis) — item 1: **RESOLVED as to the terms in the file; one residual**

- The Project Gutenberg catalog page for eBook #5200 states: *"Copyrighted. Read the copyright
  notice inside this book for details."* The catalog pages for the other nine IDs each state
  *"Public domain in the USA."* (all ten pages hashed in the manifest).
- The current PG copy (`cache/epub/5200/pg5200.txt`, header committed as
  `sources/pg5200_header_as_served_2026-09-02.txt`) carries the standard §1.E.1 sentence, then
  *"\*\*\* This is a COPYRIGHTED Project Gutenberg eBook. Details Below. \*\*\*"*, and
  *"Translator: David Wyllie"*. The "details below" are the full Project Gutenberg License. Its
  §1.E.3 (committed verbatim in `sources/pg5200_licence_1E_clauses_as_served_2026-09-02.txt`)
  reads: *"If an individual Project Gutenberg electronic work is posted with the permission of the
  copyright holder, your use and distribution must comply with both paragraphs 1.E.1 through
  1.E.7 and any additional terms imposed by the copyright holder. Additional terms will be linked
  to the Project Gutenberg License for all works posted with the permission of the copyright holder
  found at the beginning of this work."*
- **No additional terms appear at the beginning of the work**, in the current copy or in the banked
  copy (`grep -n "©\|(C)\|non-commercial\|Wyllie"` matches only the translator line in both).
- So the terms that bind are §1.E.1–1.E.7: no fee for access or copies (§1.E.7), the licence
  kept attached (§1.E.4), the §1.E.1 sentence displayed on any copy (§1.E.1, §1.E.5). This
  repository distributes neither the file nor the corpus (both gitignored); the file it measured is
  the `files/5200/5200-0.txt` edition, re-fetched today byte-identical to the banked hash
  (`6b023bfb…`), whose two-line banner and missing licence are how gutenberg.org serves that path.
- **Residual COULD NOT VERIFY:** whether the copyright holder imposes terms anywhere other than
  the file (nothing is linked from the file or the catalog page), and whether training on
  compressed windows of the text is within §1.E.7 for a company — a legal judgement this audit
  does not make. **Recommendation:** any *future* corpus should replace pg5200 with a text whose
  catalog status is "Public domain in the USA."; the banked corpora stay as measured, because the
  chain binds them and because the gutenberg family's contribution is banked separately
  (gutenberg-excluded margins in `artifacts/pivot/audit_rederivations.json`).
- Incidentally: the `cache/epub` copy's body text differs from the `files/` edition (the header
  says "Most recently updated: June 9, 2026"). Irrelevant to the terms; relevant to reproducibility
  — see §5.6.

### 5.2 Public-domain status of the other nine editions — item 2: **RESOLVED to the extent PG asserts it**

Each of the nine catalog pages (IDs 11, 74, 84, 98, 1342, 1661, 1952, 2600, 2701) states *"Public
domain in the USA."* That is Project Gutenberg's own status line for the specific edition it
serves, which is what the 2026-08-31 audit asked for. It is a statement about the United States;
the §1.E.1 sentence itself says users elsewhere must check local law. Not re-verified beyond PG's
assertion.

### 5.3 Native components in `isal` and `python-sat` — item 3: **RESOLVED for ISA-L and five of six solvers; one finding; one unreachable**

- **ISA-L:** the wheel bundles `isal/isa-l/LICENSE`, which is **byte-identical** (sha256
  `bc8fd4a3…`) to upstream `intel/isa-l` `LICENSE`: BSD-3-Clause, "Copyright(c) 2011-2024 Intel
  Corporation". Committed as `sources/isa-l_LICENSE_BSD-3-Clause.txt`.
- **python-sat:** the wheel compiles the solvers listed in pysat's `solvers/prepare.py` (fetched,
  hashed). `tools/repro/sat_solver_identity.py` uses six: Cadical153, Glucose42, Lingeling,
  Minisat22, MapleChrono, Mergesat3. Upstream licences, fetched from the sources pysat declares:

  | Solver (pysat name) | Upstream licence | Committed as |
  |---|---|---|
  | CaDiCaL 1.5.3 | MIT | `sources/cadical-1.5.3_LICENSE.txt` |
  | Glucose 4.2.1 | MIT (Gilles Audemard, 2023) | `sources/glucose-4.2.1_LICENSE.txt` |
  | MiniSat 2.2.0 | MIT-form (Eén, Sörensson) | `sources/minisat-2.2.0_LICENSE.txt` |
  | MergeSat 3.0 | MIT-form, several copyright holders | `sources/mergesat-3.0_LICENSE.txt` |
  | **Lingeling** bbc-9230380-160707 | **evaluation and research use only; not commercial** | `sources/lingeling-bbc-9230380-160707_COPYING.txt` |
  | MapleLCMDistChronoBT | **COULD NOT VERIFY** — pysat's declared source returned HTTP 503, then a connection reset | — |

  **F11 — Lingeling is not permissively licensed.** Its `COPYING` states, verbatim: *"Permission
  is hereby granted, free of charge, to use this software for evaluation and research purposes.
  This license does not allow this software to be used in a commercial context."* and *"All other
  usage is reserved."* Where it is used here: only `tools/repro/sat_solver_identity.py`, the
  reproduction of a Phase-0 **kill** (the SAT-solver-identity candidate), which is evaluation and
  research use. It is **not in the product path** — nothing in the DEFLATE pivot imports pysat.
  It must not ship in anything commercial; if the company ever productises code touching pysat,
  Lingeling is dropped first. `README.md` now says so.
  **F13 — the venv contains it regardless of use:** python-sat's wheel bundles the compiled
  solvers, so `pysolvers.cpython-311-x86_64-linux-gnu.so` in the venv contains Lingeling whether
  or not it is called. Redistributing the venv or the wheel would redistribute it.
  On MapleChrono: MergeSat's own `LICENSE` lists "Maple_LCM_Dist_Chrono -- Copyright (c) 2018,
  Vadim Ryvchin, Alexander Nadel" among the code it incorporates under MIT terms; that
  corroborates but is not MapleChrono's own licence file, so the row stays COULD NOT VERIFY.

### 5.4 IGS / BKG / ESA GNSS products — item 4: **RESOLVED for IGS and BKG; NARROWED for ESA; files untracked**

- **IGS.** The *IGS Data and Product Disclaimer and Terms of Use* (5 August 2020; PDF sha256
  `7b4e253c…`, linked from `igs.org/data-access/`; text extracted with pypdf and committed as
  `sources/IGS_Data_and_Product_Disclaimer_and_Terms_of_Use_200805.txt`) states, verbatim: *"The
  IGS products and station data are provided openly for the benefit of all scientific,
  educational, and commercial users. For 25 years, IGS data and products have been made openly
  available for use without restriction, and continue to be offered free of cost or obligation."*
  Attribution: *"By accessing data, products, and any other information from the IGS, users agree
  to appropriately cite and attribute these resources to providers and their sponsors,
  acknowledgment of IGS and its contributing organizations, and to adherence to professional and
  ethical standards."* Terms of use: *"Access to, and use of IGS data, products, and other
  information constitutes acceptance of the aforementioned information."* Commercial use is
  therefore expressly within scope; attribution is the obligation.
- **BKG.** The broadcast file `BRDC00IGS_R_…` is an IGS product served by BKG, an IGS Global Data
  Center. BKG's GDC site carries no data-licence text of its own: the Impressum is a liability
  disclaimer and the archive-access page is download mechanics (both fetched and hashed). The file
  re-fetched today is **byte-identical** to `data/gnss/brdc_001.rnx.gz` (sha256 `92f95dd3…`).
- **ESA.** The Navigation Support Office page says *"Our latest published products are freely
  available on our web page"*, and its "Terms and Conditions" link resolves to ESA's general
  website terms, whose Copyrights section says, verbatim: *"The contents of the ESA website are
  intended for the personal and non-commercial use of its users. ESA grants permission to users to
  visit the site, and to download and copy information, images, documents and materials from the
  website for users' personal non-commercial use. ESA does not grant the right to resell or
  redistribute any information, documents, images or material from its website or to compile or
  create derivative works from material on its website."* The `ESA0OPSFIN` products are ESA's
  **IGS Analysis Center** products, which the IGS distributes through its data centres under the
  IGS terms above — but BKG's IGS products directory for GPS week 2347 does not carry the
  ESA-named files (HTTP 404) and the IGN data centre was unreachable, so they could not be
  re-sourced under IGS terms today. **COULD NOT VERIFY whether ESA's website terms govern the
  product directory.** Recommendation: before any commercial use of ESA products, obtain them from
  an IGS data centre or put the question to the Navigation Support Office in writing.
- **Actions taken in this commit.** The four product files are **untracked** (`git rm --cached`;
  they remain on disk and gitignored, and the history that contains them — commit `b185129`,
  5.5 MB — is deliberately not rewritten, because commit order is this repository's precedence
  record). `tools/gnss/fetch.sh` now states the terms and the attribution. The EphemErr result is
  banked and unchanged.
- **Attribution adopted:** GNSS products — International GNSS Service (IGS) and its contributing
  organizations; broadcast navigation via the BKG GNSS Data Center; precise orbit and clock
  products by the ESA/ESOC Navigation Support Office.

### 5.5 `data/asmprov/` NCBI metadata — item 5: **RESOLVED as to NCBI's own terms**

NCBI's *Website and Data Usage Policies and Disclaimers* page (fetched, sha256 `8ad8f6f1…`)
states, verbatim: *"Information that is created by or for the US government on this site is within
the public domain."* and, under Molecular Data Usage — which names the Assembly database among
those covered — *"NCBI itself places no restrictions on the use or distribution of the data
contained therein. Nor do we accept data when the submitter has requested restrictions on reuse or
redistribution. However, some submitters of the original data (or the country of origin of such
data) may claim patent, copyright, or other intellectual property rights in all or a portion of the
data (that has been submitted). NCBI is not in a position to assess the validity of such claims"*.
The committed files are assembly *metadata* records (accession, organism, submitter, statistics),
not sequence. **Residual COULD NOT VERIFY:** submitter-level IP claims, per record — NCBI itself
says it cannot assess them, and this audit did not attempt to for 239,744 records.

### 5.6 New finding — F12: upstream edition drift breaks the byte-identical rebuild

Re-fetching all ten sources from the URL `fetch_sources.sh` uses: nine hash-match the banked
manifest; **`pg1342.txt` does not** (two typographic lines changed upstream). Filed at full size in
`CORRECTIONS.md` 2026-09-02; fixed by `tools/pivot/pin_sources.py` and `source_pins.json`. Whether
an archived copy of the banked edition exists **COULD NOT be verified** — the Internet Archive is
blocked by this container's egress policy.

### 5.7 Earlier findings closed

- **F5** (undeclared imports): `requirements-repro.txt` now declares `torch>=2.13` and
  `zstandard>=0.25`.
- **F9** (LICENSE form): `LICENSE` is now the canonical Apache-2.0 text (sha256 `cfc7749b…`,
  fetched from apache.org); the copyright line moved to `NOTICE`.
- **F10** (outbound prose licence): decided — Apache-2.0, deliberately; stated in
  `outbound/README.md`.

## Updated consolidated COULD NOT VERIFY list (2026-09-02)

1. Any pg5200 copyright-holder terms that exist *outside* the file — none are linked from the
   file or the catalog page (§5.1).
2. Whether ESA's general website terms govern the product directory at
   `navigation-office.esa.int/products/` (§5.4).
3. The licence of MapleLCMDistChronoBT from its declared source, which was unreachable (§5.3).
4. Submitter-level IP claims on individual NCBI assembly records (§5.5).
5. Whether an archived copy of the banked pg1342 edition exists (§5.6).

Resolved since 2026-08-31: the pg5200 terms as stated in the file; the public-domain status PG
asserts for the other nine editions; ISA-L and five of six SAT solver licences; the IGS and BKG
terms basis, with attribution recorded; NCBI's own terms for `data/asmprov/`; F5, F9, F10.

## Reproducing the follow-up

```
cat docs/compliance/sources/MANIFEST.json                          # every URL, sha256, byte count, and the unreachable hosts
python3 tools/pivot/pin_sources.py                                 # sources hash to the banked edition (or are pinned back to it)
grep -n "commercial" docs/compliance/sources/lingeling-*_COPYING.txt
grep -n "commercial" docs/compliance/sources/IGS_Data_and_Product_Disclaimer_and_Terms_of_Use_200805.txt
git ls-files data/gnss                                             # now empty
```
