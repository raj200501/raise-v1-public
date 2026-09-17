# Second-decade fit corpus sources (preregistration 0024) — provenance and licences

Date: 2026-09-17. Method: every file was fetched from this container through its egress proxy
(`tools/pivot/fetch_ext_sources2.sh`; the PyPI files directly, as the proxy's no-proxy list names that host),
hashed, and pinned by sha256 in `tools/pivot/ext_source_pins2.json`; `tools/pivot/corpus_realfit2.py` refuses to
cut a chunk from a file whose bytes differ from the pin. Nothing under `data/pivot/ext_src2` is committed; the corpus
built from it (`data/pivot/realfit2_c4096.npz`) is not committed either; its array hashes are banked in
`artifacts/pivot/realfit2_corpus_manifest.json` and sealed in the preregistration. The licence texts named below are
committed verbatim under `docs/compliance/sources/` and listed in `docs/compliance/sources/MANIFEST.json`.

What the corpus does with these bytes: it compresses 32768-byte chunks of them under 26 DEFLATE configurations and
keeps a 4096-byte window from the middle of each stream, plus features computed from that window. No source byte,
and no window, is redistributed; the corpus is fitted on and never scored. Every candidate chunk is dropped if it is
byte-identical to any whole chunk of any 0018 pinned file, or if it shares a run of 1024 bytes with any 0018 pinned
file at any offset (a 64-bit rolling hash over every 64-byte window of the 0018 files; the 0024 pre-freeze review found
that `node.exe` embeds the same OpenSSL build as 0018's `libcrypto-3.dll`, so identical code sat in both at shifted
offsets), so no whole chunk, no kilobyte run, no chunk id, no source hash and no feature row of the sealed evaluation
set or of 0021's fit block recurs here (`corpus_realfit2.py --disjoint` proves each of those on the built corpus).

Why these projects: the same five families as 0018 from DIFFERENT upstream projects — no file here is another
edition of CPython or SQLite, and no pinned RFC number is repeated — chosen for a permissive licence verified in
the archive itself, reachability through the proxy, and enough bytes for three more doublings of every family.

| Family | Upstream file (pinned) | Licence, as verified first-hand | Verified where |
|---|---|---|---|
| `py_src`, `rst_doc` | `Django-5.0.6.tar.gz` (PyPI) | BSD-3-Clause ("Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met") | `sources/Django-5.0.6_LICENSE.txt` |
| `py_src`, `rst_doc` | `numpy-1.26.4.tar.gz` (PyPI) | BSD-3-Clause; bundled components under the licences listed in `LICENSES_bundled.txt` | `sources/numpy-1.26.4_LICENSE.txt`, `sources/numpy-1.26.4_LICENSES_bundled.txt` |
| `py_src`, `rst_doc` | `pandas-2.2.2.tar.gz` (PyPI) | BSD-3-Clause | `sources/pandas-2.2.2_LICENSE.txt` |
| `py_src`, `rst_doc` | `scikit-learn-1.4.2.tar.gz` (PyPI) | BSD-3-Clause | `sources/scikit-learn-1.4.2_COPYING.txt` |
| `py_src`, `rst_doc` | `SQLAlchemy-2.0.29.tar.gz` (PyPI) | MIT ("Permission is hereby granted, free of charge, to any person obtaining a copy") | `sources/SQLAlchemy-2.0.29_LICENSE.txt` |
| `py_src`, `rst_doc` | `sympy-1.12.tar.gz` (PyPI) | BSD-3-Clause | `sources/sympy-1.12_LICENSE.txt` |
| `py_src`, `rst_doc` | `scipy-1.13.0.tar.gz` (PyPI) | BSD-3-Clause; bundled components under the licences listed in `LICENSES_bundled.txt` | `sources/scipy-1.13.0_LICENSE.txt`, `sources/scipy-1.13.0_LICENSES_bundled.txt` |
| `py_src`, `rst_doc` | `sphinx-7.2.6.tar.gz` (PyPI) | BSD-2-Clause | `sources/sphinx-7.2.6_LICENSE.txt` |
| `py_src`, `rst_doc` | `matplotlib-3.8.4.tar.gz` (PyPI) | Matplotlib licence, PSF-style ("MDT hereby grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce, analyze, test, perform and/or display publicly, prepare derivative works, distribute, and otherwise use matplotlib"); bundled fonts and data under the licences in the archive's `LICENSE/` directory, none of which are `.py` or `.rst` members | `sources/matplotlib-3.8.4_LICENSE.txt` |
| `py_src`, `rst_doc` | `twisted-24.3.0.tar.gz` (PyPI) | MIT | `sources/twisted-24.3.0_LICENSE.txt` |
| `py_src`, `rst_doc` | `astropy-6.0.1.tar.gz` (PyPI) | BSD-3-Clause | `sources/astropy-6.0.1_LICENSE.txt` |
| `py_src`, `rst_doc` | `networkx-3.3.tar.gz` (PyPI) | BSD-3-Clause | `sources/networkx-3.3_LICENSE.txt` |
| `py_src`, `rst_doc` | `statsmodels-0.14.1.tar.gz` (PyPI) | BSD-3-Clause | `sources/statsmodels-0.14.1_LICENSE.txt` |
| `py_src`, `rst_doc` | `pygments-2.17.2.tar.gz` (PyPI) | BSD-2-Clause | `sources/pygments-2.17.2_LICENSE.txt` |
| `c_src` | `postgresql-16.2.tar.gz` (ftp.postgresql.org) | PostgreSQL License ("Permission to use, copy, modify, and distribute this software and its documentation for any purpose, without fee, and without a written agreement is hereby granted") | `sources/postgresql-16.2_COPYRIGHT.txt` |
| `c_src` | `curl-8.7.1.tar.gz` (curl.se) | curl licence, MIT-style | `sources/curl-8.7.1_COPYING.txt` |
| `c_src` | `nginx-1.25.4.tar.gz` (nginx.org) | BSD-2-Clause | `sources/nginx-1.25.4_LICENSE.txt` |
| `c_src` | `musl-1.2.5.tar.gz` (musl.libc.org) | MIT ("musl as a whole is licensed under the following standard MIT license") | `sources/musl-1.2.5_COPYRIGHT.txt` |
| `c_src` | `lua-5.4.6.tar.gz` (lua.org) | MIT, as the licence block at the end of `src/lua.h`; the tarball carries no LICENSE file | `sources/lua-5.4.6_lua.h_licence_block.txt` |
| `c_src` | `zlib-1.3.1.tar.gz` (zlib.net) | zlib licence | `sources/zlib-1.3.1_LICENSE.txt` |
| `pe_bin` | `go1.22.2.windows-amd64.zip` (dl.google.com) | BSD-3-Clause | `sources/go1.22.2_LICENSE.txt` |
| (note) | the three `pe_bin` archives carry `.exe` members only (nineteen Go toolchain binaries, the single file `node.exe`, six PuTTY programs); the member rule admits `.dll` but none is present, so the new `pe_bin` plaintexts are executables where 0018's were mostly DLLs | | |
| `pe_bin` | `node-v20.12.2-win-x64.zip` (nodejs.org) | MIT; the same file lists the licences of the components bundled into `node.exe` (V8, ICU, OpenSSL, zlib and others, all permissive) | `sources/node-v20.12.2_LICENSE.txt` |
| `pe_bin` | `putty-0.81-w64.zip` (the.earth.li) | MIT, as the project's licence page served on 2026-09-17; the zip carries no licence file | `sources/putty-0.81_licence_page_as_served_2026-09-17.txt` |
| `rfc_txt` | 600 `rfcNNNN.txt` files (rfc-editor.org), a seeded sample (`random.Random(20260917).sample`) over the 7838 RFCs the RFC Editor's index lists as issued with a TXT format, not pinned by 0018, and not related to a 0018-pinned RFC by an Obsoletes, Obsoleted by, Updates or Updated by annotation in either direction (323 numbers so excluded; the index as served is hashed in `sources/MANIFEST.json` and the candidate list's sha256 in `tools/pivot/ext_source_pins2.json`) | Counted by `grep -l` over the pinned files on 2026-09-17: 310 carry the phrase `IETF Trust and the persons identified` (the BCP 78 / IETF Trust Legal Provisions notice, https://trustee.ietf.org/license-info, which grants the right to reproduce and distribute RFCs; the phrase wraps a line in the files, so it is matched without its tail); 165 carry `Copyright (C) The Internet Society` with its own reproduction-and-distribution grant; 39 more carry some other line matching `copyright` case-insensitively; 409 cite `BCP 78`. **COULD NOT VERIFY in the files themselves** for the 86 files that match no `copyright` case-insensitively (`grep -L -i copyright`; RFC 1007 to RFC 2215, the early series): their reproduction terms rest on the RFC Editor's published statement that RFCs may be freely reproduced, which this repository has not fetched and hashed | the counts are reproducible with the patterns quoted over `data/pivot/ext_src2/rfc2` |

Not verified first-hand, stated as such: **COULD NOT VERIFY** that every `.py` member of a PyPI source distribution
is under the distribution's top-level licence; a few projects vendor small third-party modules (numpy and scipy list
theirs in `LICENSES_bundled.txt`, all permissive), and this repository has not audited every file header. The corpus
neither redistributes nor executes any of them. Likewise for the Windows binaries: `node.exe` and the Go toolchain
embed third-party components whose licences are listed in the archives' LICENSE files, and this repository relies on
those lists.

Claimcheck status: this file lives under `docs/`, not `outbound/`; the counts in it (23 archives, 600 files, the
notice counts) are file-list facts reproducible from `tools/pivot/ext_source_pins2.json` and `grep`, not measurements.
