# Extension corpus sources (preregistration 0018) — provenance and licences

Date: 2026-09-09. Method: every file was fetched from this container through its egress proxy
(`tools/pivot/fetch_ext_sources.sh`), hashed, and pinned by sha256 in `tools/pivot/ext_source_pins.json`;
`tools/pivot/corpus_ext.py` refuses to cut a chunk from a file whose bytes differ from the pin. Nothing under
`data/pivot/ext_src` is committed; the corpus built from it (`data/pivot/ext_c4096.npz`) is not committed either;
its array hashes are banked in `artifacts/pivot/ext_corpus_manifest.json` and sealed in the preregistration.
The licence texts named below are committed verbatim under `docs/compliance/sources/` and listed in
`docs/compliance/sources/MANIFEST.json`.

What the corpus does with these bytes: it compresses 32768-byte chunks of them under 26 DEFLATE
configurations and keeps a 4096-byte window from the middle of each stream, plus features computed from that
window. No source byte, and no window, is redistributed; the corpus is scored by models and never fitted on.

| Family | Upstream file (pinned) | Licence, as verified first-hand | Verified where |
|---|---|---|---|
| `py_src`, `rst_doc` | `Python-3.11.9.tgz` (python.org) | PSF License Agreement for Python 3.11.9 (PSF-2.0 terms; "PSF hereby grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce, analyze, test, perform and/or display publicly, prepare derivative works, distribute, and otherwise use Python 3.11.9 alone or in any derivative version") | `sources/Python-3.11.9_LICENSE.txt`, section B |
| `pe_bin` | `python-3.11.9-embed-amd64.zip` (python.org) | The same PSF licence for the CPython binaries; the package also bundles `libcrypto-3.dll` and `libssl-3.dll` (OpenSSL, Apache-2.0), `sqlite3.dll` (public domain) and the Microsoft Visual C++ runtime redistributable (`vcruntime140.dll`, `vcruntime140_1.dll`), whose terms are reproduced in the package's LICENSE.txt "Additional Conditions" | `sources/python-3.11.9-embed_LICENSE.txt` |
| `c_src` | `sqlite-amalgamation-3450300.zip` (sqlite.org) | Public domain: the amalgamation's file header carries the SQLite blessing ("The author disclaims copyright to this source code") | `sources/sqlite-3.45.3_amalgamation_header_as_served_2026-09-09.txt` |
| `rfc_txt` | 79 `rfcNNNN.txt` files (rfc-editor.org) | Counted by `grep` over the pinned files on 2026-09-10: 46 carry "Copyright (c) 20xx IETF Trust and the persons identified as the document authors" subject to BCP 78 and the IETF Trust Legal Provisions (https://trustee.ietf.org/license-info), which grant the right to reproduce and distribute RFCs; 19 carry the earlier "Copyright (C) The Internet Society" notice with its own reproduction-and-distribution grant; 9 more carry some other copyright line; 64 cite BCP 78. **COULD NOT VERIFY in the files themselves** for RFC 791, 793, 1034, 1035 and 2119, which carry no copyright line at all: their reproduction terms rest on the RFC Editor's published statement that RFCs may be freely reproduced, which this repository has not fetched and hashed | `sources/rfc9110_copyright_notice_as_served_2026-09-09.txt` (one representative of the 46); the counts are reproducible with `grep -l` over `data/pivot/ext_src/rfc` |
| `xml`, `sql`, `hexdump` | none (synthetic; `tools/pivot/corpus_ext.py` generators) | this repository's licence | — |

Not verified first-hand, stated as such: **COULD NOT VERIFY** that the Microsoft Visual C++ runtime files inside
the embeddable package may be used as *source bytes for a compression experiment* under the redistributable's
terms; the package's LICENSE.txt permits their redistribution with Python applications, and the corpus neither
redistributes nor executes them. The two files are 1.0 percent of the `pe_bin` blob; if a later audit requires it
they can be excluded by editing the member filter in `corpus_ext.py`, which would change the sealed corpus and
therefore be a new preregistration, never an edit to 0018.

Claimcheck status: this file lives under `docs/`, not `outbound/`; the counts in it (79 files, 1.0 percent) are
file-list facts reproducible from `tools/pivot/ext_source_pins.json` and the archive listing, not measurements.
