# Public mirror — what this repository is, and what was filtered

This repository is the public mirror of the private working repository `raj200501/raise-v1`,
regenerated from its `main` branch. Every measurement, artifact, preregistration, reader, gate,
correction and document is identical to the private repository at the mirrored commit. Two
things were removed from the mirror's **history** with `git filter-branch`, so every commit hash
differs from the private repository's:

1. **`data/gnss/`** — four GNSS product files (5.5 MB) committed in the private repository's
   history and untracked on 2026-09-02: two ESA final orbit/clock products whose redistribution
   terms COULD NOT be verified (`docs/compliance/LICENSE_AUDIT.md` §5.4), and the two copies of a
   BKG-served IGS broadcast file committed alongside them, whose IGS terms the audit records as
   open. All four were removed together so the mirror carries no agency products at all.
   `tools/gnss/fetch.sh` re-fetches them from the agencies for anyone reproducing the EphemErr
   study; the banked artifacts under `artifacts/ephemerr/` are unchanged.
2. **One e-mail address** in two files (a user-agent string and a review byline), replaced by
   a placeholder.

Nothing else differs: same trees otherwise, same authors, same dates, same messages, same order.
The private repository's history is the precedence record the preregistration chain refers to:
each `prereg/*.json` carries the `git_commit` at which it was frozen (`prereg/chain.jsonl` carries
the hash chain - frozen_utc, sealed_sha256, prev_hash - that orders them independently of git),
and those commit hashes are the **private** repository's. The table below maps them to this
mirror's commits so the ordering can be checked here too.

Mirror built 2026-09-05 23:15 UTC from private `main` = `2e1d4ed6aa97a7d506a09ae803fd5a208793e455` → mirror `199d5446fdd7b850452827f131407a1b3c479d2c`; 210 commits.

| Preregistration | frozen at (private) | same commit here (mirror) |
|---|---|---|
| 0001 phase0-terminal-verdict | `f0cdd1c16bf7` | `a93ac77ae11d` |
| 0002 phase0-round4-verdict | `078f4231ae16` | `5c57193a2428` |
| 0003 pivot-deflate-curve | `163592178669` | `1286b69b7c33` |
| 0004 market-timing-search | `1336f7fbbf21` | `cfb6b4f4415c` |
| 0005 ephemerr-a2 | `a6db99984053` | `154f39786634` |
| 0006 deflate-operational-output | `faa120eb7dd6` | `bbcf50816ba3` |
| 0007 carve-size-generalisation | `44d212caa047` | `82910624a27b` |
| 0008 c1-falsifier-search | `80aac3ab7cf5` | `ccaba0add598` |
| 0009 byte-sequence-representation | `fae87d06cd68` | `50a247664dc5` |
| 0010 byte-model-position-preserving-head | `4857d7739a15` | `9462cfe408b5` |
| 0011 carve-2048-boundary | `d0a2eb2f185c` | `538a720146a2` |
| 0012 recipe-search-2048 | `4c18a332d48f` | `31e9e9857f4e` |
| 0013 recipe-search-2048-reread | `8699160b0da9` | `90ee3da86937` |
| 0014 recipe-search-4096 | `58b044e2a19c` | `b1df91073e0e` |
| PR #1 merge commit (precedence record) | `e856baa62b49` | `3c2c45a5ff3e` |

The full map (every commit) is in `docs/public_mirror_commit_map.json`.

The mirror is regenerated from the private `main` after each meaningful step and force-updated (the filtered
history is rebuilt deterministically, but this note's commit is new each time), so a clone of this mirror should
`git fetch` and reset to `origin/main` rather than pull.

`bash tools/gates.sh` runs every gate here exactly as in the private repository; `python3 tools/prereg.py verify`
verifies the chain and the frozen readers' hashes, which do not depend on git history.
