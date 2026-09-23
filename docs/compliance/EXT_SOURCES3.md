# Fourth-doubling fit corpus sources (preregistration 0025) — provenance and licences

Date: 2026-09-23. Method: every new file was fetched from this container through its egress proxy
(`tools/pivot/fetch_ext_sources3.sh`; the PyPI files directly, as the proxy's no-proxy list names that host),
hashed, and pinned by sha256 in `tools/pivot/ext_source_pins3.json`; `tools/pivot/corpus_realfit3.py` refuses to
cut a chunk from a file whose bytes differ from the pin, and refuses unless 0024's pinned sources
(`docs/compliance/EXT_SOURCES2.md`) are present and byte-identical too, because the 0025 corpus nests on 0024's
pool. Nothing under `data/pivot/ext_src3` is committed; the corpus built from it (`data/pivot/realfit3_c4096.npz`,
the NEW pool positions only) is not committed either; its array hashes are banked in
`artifacts/pivot/realfit3_corpus_manifest.json` and sealed in the preregistration. The licence texts named below are
committed verbatim under `docs/compliance/sources/` and listed in `docs/compliance/sources/MANIFEST.json`.

What the corpus does with these bytes: it compresses 32768-byte chunks of them under 26 DEFLATE configurations and
keeps a 4096-byte window from the middle of each stream, plus features computed from that window. No source byte,
and no window, is redistributed; the corpus is fitted on and never scored. Every new candidate chunk is dropped if it
is byte-identical to any whole chunk of any 0018 pinned file or of 0024's corpus, if it shares a run of 1024 bytes
with any 0018 pinned file at any offset, or if it shares a run of 1024 bytes with 0024's blob of the same family at
any offset (the 0018 run-overlap rule of 0024, re-applied to the previous fit corpus, so that "other files" is proven
rather than asserted); vendored copies of other projects under `_vendor`, `vendored` and `ext` directories are excluded
by the member rule before any chunk is cut. `corpus_realfit3.py --disjoint` proves each of those on the built corpus.

Why these projects: the same five families as 0018 and 0024, from projects pinned by neither. Only `py_src` and
`rfc_txt` needed new sources for a fourth doubling (0024's candidate frame runs out for them); `c_src` and `pe_bin`
take their fourth doubling from 0024's unused candidates of 0024's archives, and `rst_doc` from 0024's unused
candidates and the new archives' `.rst` members. Chosen for a permissive licence verified in the archive itself,
reachability through the proxy, and enough bytes for one more doubling of `py_src`.

| Family | Upstream file (pinned) | Licence, as verified first-hand | Verified where |
|---|---|---|---|
| `py_src`, `rst_doc` | `botocore-1.43.100.tar.gz` (PyPI) | Apache-2.0 ("Licensed under the Apache License, Version 2.0"); LICENSE.txt | `sources/botocore-1.43.100_LICENSE.txt` |
| `py_src`, `rst_doc` | `dask-2026.8.0.tar.gz` (PyPI) | BSD-3-Clause ("Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met"); LICENSE.txt | `sources/dask-2026.8.0_LICENSE.txt` |
| `py_src`, `rst_doc` | `homeassistant-2026.9.3.tar.gz` (PyPI) | Apache-2.0 ("Licensed under the Apache License, Version 2.0"); LICENSE.md | `sources/homeassistant-2026.9.3_LICENSE.md.txt` |
| `py_src`, `rst_doc` | `ipython-9.17.1.tar.gz` (PyPI) | BSD-3-Clause ("Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met"); LICENSE; COPYING.rst restates the terms | `sources/ipython-9.17.1_LICENSE.txt, sources/ipython-9.17.1_COPYING.rst.txt` |
| `py_src`, `rst_doc` | `nova-33.0.2.tar.gz` (PyPI) | Apache-2.0 ("Licensed under the Apache License, Version 2.0"); LICENSE | `sources/nova-33.0.2_LICENSE.txt` |
| `py_src`, `rst_doc` | `numba-0.67.0.tar.gz` (PyPI) | BSD-2-Clause ("Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met"); LICENSE); vendored components under the licences listed in LICENSES.third-party | `sources/numba-0.67.0_LICENSE.txt, sources/numba-0.67.0_LICENSES.third-party.txt` |
| `py_src`, `rst_doc` | `pip-26.2.1.tar.gz` (PyPI) | MIT ("Permission is hereby granted, free of charge, to any person obtaining a copy"); LICENSE.txt); the vendored packages under src/pip/_vendor are excluded from the corpus by the member rule | `sources/pip-26.2.1_LICENSE.txt` |
| `py_src`, `rst_doc` | `salt-3008.2.tar.gz` (PyPI) | Apache-2.0 ("Licensed under the Apache License, Version 2.0"); LICENSE); the vendored packages under salt/ext are excluded from the corpus by the member rule | `sources/salt-3008.2_LICENSE.txt` |
| `py_src`, `rst_doc` | `setuptools-84.0.0.tar.gz` (PyPI) | MIT ("Permission is hereby granted, free of charge, to any person obtaining a copy"); LICENSE); the vendored packages under setuptools/_vendor are excluded from the corpus by the member rule | `sources/setuptools-84.0.0_LICENSE.txt` |
| `py_src`, `rst_doc` | `tornado-6.5.10.tar.gz` (PyPI) | Apache-2.0 ("Licensed under the Apache License, Version 2.0"); LICENSE | `sources/tornado-6.5.10_LICENSE.txt` |
| `py_src`, `rst_doc` | `transformers-5.17.0.tar.gz` (PyPI) | Apache-2.0 ("Licensed under the Apache License, Version 2.0"); LICENSE | `sources/transformers-5.17.0_LICENSE.txt` |
| `py_src`, `rst_doc` | `xarray-2026.7.0.tar.gz` (PyPI) | Apache-2.0 ("Licensed under the Apache License, Version 2.0"); LICENSE | `sources/xarray-2026.7.0_LICENSE.txt` |
| `rfc_txt` | 600 `rfcNNNN.txt` files (rfc-editor.org), a seeded sample (`random.Random(20260923).sample`) over the 8827 RFCs the RFC Editor's index (as served 2026-09-23, hashed in `sources/MANIFEST.json`) lists as issued with a TXT format, RFC 1 upward, not pinned by 0018 or 0024, and not related to a 0018-pinned RFC by an Obsoletes, Obsoleted by, Updates or Updated by annotation in either direction (329 numbers so excluded; the candidate list's sha256 in `tools/pivot/ext_source_pins3.json`). The parser corrects 0024's, which had skipped the entries numbered below 1000 and five annotations that wrapped a line (`CORRECTIONS.md`, 2026-09-23) | Counted by `grep -l` over the pinned files on 2026-09-23: 277 carry the phrase `IETF Trust and the persons identified` (the BCP 78 / IETF Trust Legal Provisions notice, https://trustee.ietf.org/license-info, which grants the right to reproduce and distribute RFCs); 147 carry `Copyright (C) The Internet Society` with its own reproduction-and-distribution grant; 39 more carry some other line matching `copyright` case-insensitively; 375 cite `BCP 78`. **COULD NOT VERIFY in the files themselves** for the 137 files that match no `copyright` case-insensitively (`grep -L -i copyright`; RFC 33 to RFC 2207, the early series, more numerous than 0024's 86 because the corrected frame includes RFCs 1 to 999): their reproduction terms rest on the RFC Editor's published statement that RFCs may be freely reproduced, which this repository has not fetched and hashed | the counts are reproducible with the patterns quoted over `data/pivot/ext_src3/rfc3` |

Vendored directories excluded by the member rule (their bytes never enter a blob): `pip/_vendor` (3.3 MB of `.py`),
`setuptools/_vendor` (0.9 MB), `botocore/vendored` (42 KB), `salt/ext` (0.4 MB) and nova's `doc/ext` (34 KB).
numba's `LICENSES.third-party` lists the licences of components vendored inside numba's own tree; those components'
`.py` files are numba's release files and are used as source bytes only.

What is NOT excluded, stated: runs shorter than 1024 bytes (boilerplate lines, short code sequences) shared with a
scored or previously fitted file; near-duplicate code that revises a 0024 file without copying a kilobyte of it
verbatim; and repeats WITHIN the new files themselves (the whole-chunk dedup drops only byte-identical 32768-byte
chunks, as 0024's did).
