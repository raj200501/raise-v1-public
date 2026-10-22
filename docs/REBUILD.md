# Rebuilding the corpora and cache behind preregistrations 0018-0025

This document explains how to rebuild every corpus and cache that preregistrations 0018 to 0025 depend on, starting from a cold
clone, and how to check each one against the manifest banked in `artifacts/`. Each step gives the command, the output path, the
expected verification line, and what the cold-container rebuilds of 2026-10-21 and 2026-10-22 showed, as banked in
`artifacts/pivot/engineering_log_0025.json` (key `container_2026_10_21`, cited by its sub-keys) and `CORRECTIONS.md`. Where
neither they nor a session log confirms something, the text says **COULD NOT VERIFY**. The code described is at `c19e724`.

## Status at a glance

| artifact | used by | builder | banked manifest / pins | 2026-10-21/22 |
|---|---|---|---|---|
| `data/pivot/src/` (10 Gutenberg texts) | builder cache | `tools/pivot/fetch_sources.sh` | `artifacts/pivot/corpus_manifest.json` `sources_sha256` | verified after the fallback (`sources`); the first logged run predates it and FAILED (§1) |
| `data/pivot/ext_src/` (82 pins) | all four corpora | `tools/pivot/fetch_ext_sources.sh` | `tools/pivot/ext_source_pins.json` | verified (log; `sources`) |
| `data/pivot/ext_src2/` (623 pins) | realfit2, realfit3 | `tools/pivot/fetch_ext_sources2.sh` | `tools/pivot/ext_source_pins2.json` | verified (log; `sources`) |
| `data/pivot/ext_src3/` (612 pins) | realfit3 | `tools/pivot/fetch_ext_sources3.sh` | `tools/pivot/ext_source_pins3.json` | verified (log; `sources`) |
| `data/pivot/ext_c4096.npz` | 0018-0025 | `tools/pivot/corpus_ext.py` | `artifacts/pivot/ext_corpus_manifest.json` | **IDENTICAL** |
| `data/pivot/realfit_c4096.npz` | 0020-0025 | `tools/pivot/corpus_realfit.py` | `artifacts/pivot/realfit_corpus_manifest.json` | **IDENTICAL** |
| `data/pivot/realfit2_c4096.npz` | 0024, 0025 | `tools/pivot/corpus_realfit2.py` | `artifacts/pivot/realfit2_corpus_manifest.json` | **DOES NOT REPRODUCE**: y, g, fam identical; X differs from the banked X and between rebuilds (§2.1) |
| `data/pivot/realfit3_c4096.npz` | 0025 | `tools/pivot/corpus_realfit3.py` | `artifacts/pivot/realfit3_corpus_manifest.json` | **IDENTICAL** arrays, built alone; only its nesting line on realfit2's X differs (§2) |
| `data/pivot/full_c4096.npz` (builder cache) | 0018-0025 (`cache_identity`) | `tools/pivot/run_study.py` `build()` | `artifacts/pivot/corpus_manifest.json` | **not rebuilt**; its X, g and row-position hashes cannot be rebuilt; the reorder and content-proof path is committed, not run (§4) |

`tools/prereg_gen/0025/build_chain.sh` runs the four corpus steps in order, each build then `--check` against the banked
manifest, and writes the rebuilt manifests to `$RAISE_SCRATCH/rebuild/` (it refuses to start without `RAISE_SCRATCH`, a scratch
directory outside the repository). It and `tools/prereg_gen/0025/build_cache.py` find the repository root from their own path.

## 0. Prerequisites

**Build interpreter.** Python 3.11 linked against **zlib 1.3** (check with `python3 -c "import zlib; print(zlib.ZLIB_VERSION)"`).

- **Versions.** All four corpus manifests record python 3.11.15, numpy 2.4.6, zlib 1.3, isal 1.8.0, libdeflate 0.9.0 and
  zopfli 0.4.3. The rebuilds used python 3.11.17 with zlib 1.3 and the same libraries (`environment`).
- **CPU.** ISA-L's level 3 picks AVX2 or AVX-512 code at run time, the two write different bytes, and the banked build ran the
  native AVX-512 path. The log: "Any rebuild on an AVX2-only machine would differ for ext, realfit and realfit2 alike: the
  manifests record no CPU features" (`isal_level3_dispatch_hazard`). Rebuild on an AVX-512 machine.
- **zlib 1.3 against 1.3.2.** The 2026-10-21 audit found builder-chunk streams byte-identical under both, across all families
  and zlib levels; only the session's audit notes hold it (**COULD NOT VERIFY** from a committed file).

**Fit interpreter** (sealed fits and the content proof). 0025's `invocation.interpreter` requires Python 3.11.15 with numpy
2.4.6 and scikit-learn 1.9.0; its reader VOIDs any other. The container's 3.11.15 build links zlib 1.3.2 (`environment`); with it
0021's B-feat1, D1 and L3, refitted on 0021's rebuilt fit block, reproduce their banked per-example vectors on the 61409
extension rows exactly (`fitting_environment_reproduces`). Its scipy was 1.17.1, and 0024 banked none (**COULD NOT VERIFY**).

**Packages.** `requirements.txt` and `requirements-pivot.txt` set minimum versions only. To match the banked builds, run
`pip install numpy==2.4.6 scikit-learn==1.9.0 deflate==0.9.0 isal==1.8.0 zopfli==0.4.3`.

**Network.** The fetches need www.gutenberg.org, raw.githubusercontent.com (fallback), www.python.org, sqlite.org,
www.rfc-editor.org, and the archive hosts in `ext_source_pins2.json` / `ext_source_pins3.json`: files.pythonhosted.org,
curl.se, dl.google.com, www.lua.org, musl.libc.org, nginx.org, nodejs.org, ftp.postgresql.org, the.earth.li and zlib.net.

**Disk and memory.** The cache's X (1300000 x 1108 float32) is 5.76 GB (`artifacts/pivot/engineering_log.json`), and
`reorder_cache.py` writes a second file of that size (§4); no source or corpus file size is banked. Two attempts to build
realfit3 beside other work were killed by the memory cgroup at 11.4 GB; run alone, it completed (`corpora_rebuilt`). The banked
peak of `run_study.py` *with training* is 11.69 GB (same log). No other build's memory is banked; run each build alone.

**Rules that keep the check honest:**

- Never pass `--bank-manifest` to a builder or run `corpus_manifest.py --write`: both overwrite the banked manifests. Without
  it, `--build` refuses an existing file under `artifacts/` and writes `<npz stem>_rebuilt_manifest.json` beside the npz, and
  `--check` reads the banked manifest (since `27a61aa`; before it, `--build && --check` compared a rebuild with itself).
- Since `35b6493`, every new manifest (`tools/pivot/corpus_ext.py` `write_manifest`, called by all four builders) also records a
  `platform` block (CPU flags, numpy's SIMD targets, the C library, the zlib loaded, the isal, libdeflate and zopfli library
  files' hashes) and `X_blocks` (X's sha256 per 4096-row block). `--check` ignores both; the banked manifests predate them.
- `data/pivot/src/` must hold exactly the ten banked files: `corpus.load_real()` and `pin_sources.py` refuse an extra one
  (since `27a61aa`), because one stray file shifts every Gutenberg offset.

## 1. Sources

Each script skips a file that already exists and is non-empty, ends by checking every file against its pins, and exits non-zero
on a mismatch. The fetch logs carry no timestamps.

| step | command | output | expected final line | 2026-10-21 log |
|---|---|---|---|---|
| 1a | `bash tools/pivot/fetch_sources.sh` | the ten `data/pivot/src/pg*.txt` named in `sources_sha256` | `SOURCE PINS: PASS - every source is the banked edition` | `SOURCE PINS: FAIL (2: pg1952.txt, pg2701.txt)` (before the fallback existed) |
| 1b | `bash tools/pivot/fetch_ext_sources.sh` | `data/pivot/ext_src/` (3 archives + 79 RFCs) | `EXT SOURCES: every pinned file present and byte-identical` | that line, `EXIT 0` |
| 1c | `bash tools/pivot/fetch_ext_sources2.sh` | `data/pivot/ext_src2/` (23 archives + 600 RFCs) | `PINS: every pinned file present and byte-identical` | that line, `EXIT 0` |
| 1d | `bash tools/pivot/fetch_ext_sources3.sh` (verifies `ext_src2` too, so run 1c first) | `data/pivot/ext_src3/` (12 archives + 600 RFCs) | `PINS: every 0025 and 0024 pinned file present and byte-identical` | that line, `EXIT 0` |

**Step 1a: Gutenberg drift and the fallback.** gutenberg.org edits its `files/` copies in place.

- **pg1342** is converted back to the banked bytes by line edits recorded in `tools/pivot/source_pins.json`. The log reads
  `pinned   pg1342.txt: upstream edition 81300b79e8a8d65a… (seen 2026-09-02) -> banked edition via 2 recorded line edit(s)`.
- **pg1952 and pg2701.** On 2026-10-21 Gutenberg served new editions (sha256 `a40cdaa3…` and `f12eb530…`, against the banked
  `0604e2f8…` and `0670d7bb…`) that no recorded edit maps back.
- **The fallback.** `fetch_sources.sh` carries `FALLBACK_1952` and `FALLBACK_2701`: raw.githubusercontent.com,
  `EstDan09/huffman-compression-c-serial-fork-pthreads`, commit `17a9bac25cf06932109421453f0cf7e30aeb24e9`. It uses a copy
  **only** when Gutenberg's file does not hash to the banked value and the copy does, and says so (`pg1952: Gutenberg serves
  another edition; the banked edition restored from the commit-pinned copy`). `pin_sources.py` still makes the final call.
- **Evidence.** The engineering log banks the outcome: "every pinned source of 0003, 0018, 0024 and 0025 then verified
  byte-identical" (`sources`). CORRECTIONS.md (2026-10-21, the cold-clone entry) reports the fallback tested on a scratch copy
  with both books deleted, ending `SOURCE PINS: PASS`; that run is not among the logs (**COULD NOT VERIFY** from a log).
- **Untested revision.** `27a61aa` changed `fetch_sources.sh` again, to stage downloads in `data/pivot/src_partial/`. No log
  shows that revision run on an empty directory (**COULD NOT VERIFY**).
- **Limits.** Only pg1952 and pg2701, and only a *changed* edition: if gutenberg.org is unreachable the first loop exits 1
  before the fallback runs. web.archive.org is not used ("not reachable from every network"). If the third party deletes or
  rewrites its repository, the fetch fails loudly.

**Step 1b defect, now fixed.** Until 2026-10-21 the script requested `rfcrfc1034.txt`, so it had never fetched an RFC on a cold
machine. `27a61aa` also moved its downloads to `.part` files; that revision has not been run per the logs (**COULD NOT VERIFY**).

## 2. Corpora (in this order)

Each builder sorts its rows canonically (`np.lexsort` by chunk id, then label) after an `imap_unordered` pool, so its row order
does not depend on worker scheduling; its bytes still depend on the compressors (§2.1). `--check` hashes X, y, g and fam in
20000-row slices against the banked manifest. Run it without `--manifest`.

| step | inputs | commands | output |
|---|---|---|---|
| 2a ext (0018) | `ext_src` | `python3 tools/pivot/corpus_ext.py --build`, then `--check` | `data/pivot/ext_c4096.npz` + `data/pivot/ext_c4096_rebuilt_manifest.json` |
| 2b realfit (0020/0021) | `ext_src` (recomputes 0018's sealed selection, keeps the rest) | `python3 tools/pivot/corpus_realfit.py --build`, then `--check` | `data/pivot/realfit_c4096.npz` + `..._rebuilt_manifest.json` |
| 2c realfit2 (0024) | `ext_src2`; `ext_src` (exclusion hashes, 1024-byte run-overlap scan); the **banked** realfit manifest (pool sizes) | `python3 tools/pivot/corpus_realfit2.py --build`, then `--check` | `data/pivot/realfit2_c4096.npz` + `..._rebuilt_manifest.json` |
| 2d realfit3 (0025) | `ext_src3`, `ext_src2`, `ext_src`; the rebuilt `realfit2_c4096.npz`; the banked realfit and realfit2 manifests | `python3 tools/pivot/corpus_realfit3.py --build`, then `--check` (also re-hashes the realfit2 arrays it nests on) | `data/pivot/realfit3_c4096.npz` (NEW rows only) + `..._rebuilt_manifest.json` |

**Expected `--check` output.** Four lines `  ok   <array> <shape> <dtype> <first 16 hex>` in the order X, fam, g, y (`FAIL` in
place of `ok` on a mismatch), then the verdict line. Full hashes are in the banked manifests.

| corpus | rows / chunks | X | fam | g | y | verdict line when identical | 2026-10-21/22 (`corpora_rebuilt`) |
|---|---|---|---|---|---|---|---|
| ext | 61409 / 2400 | `c578eaf142dfd776` | `21b066e7020c5a4b` | `2f5b8a86cc0463c1` | `edbf9b3a9aa81033` | `EXT CORPUS: IDENTICAL to the banked manifest` | IDENTICAL |
| realfit | 26346 / 1035 | `d969c7d75f5bc774` | `8404e6764eb6a35e` | `3046de76635c2353` | `61f440bef345b3ec` | `REALFIT CORPUS: IDENTICAL to the banked manifest` | IDENTICAL |
| realfit2 | 193926 / 7606 | `d74bd30e71a5083f` | `73952be90fa7982e` | `84c9e74a1a7b4f90` | `5dcfd302b4dedd91` | `REALFIT2 CORPUS: IDENTICAL to the banked manifest` | **DIFFERS** on every rebuild: X `FAIL`; fam, g, y `ok` |
| realfit3 | 218955 / 8642 | `98547322dff713f0` | `8edd69ca2e0ce177` | `92770a90bee470f6` | `d0f540a413267cd5` | four `ok   nested on realfit2.<array>` lines, then `REALFIT3 CORPUS: IDENTICAL to the banked manifest` | its four arrays `ok`; `FAIL nested on realfit2.X`, so the verdict reads DIFFERS. It nests on 0024's banked realfit2 X, which no rebuild reproduces (§2.1): read its four array lines |

**Optional disjointness checks:** `corpus_realfit.py --disjoint` should end `DISJOINT: fit and sealed share nothing`, and
`corpus_realfit2.py`/`corpus_realfit3.py --disjoint` `DISJOINT: this corpus shares nothing with anything scored or fitted
before`. None has been run in a log (**COULD NOT VERIFY**).

**Build times** in seconds, banked `build_seconds` against the rebuild (`corpora_rebuilt`; `nice -n 10` on a shared container,
not benchmarks): ext 216.1 against not recorded; realfit 83.9 against 163.0; realfit2 452.2 against 2734.2 (first rebuild, under
load); realfit3 625.7 against 802.8 (alone). The banked realfit2 and realfit3 figures exclude the planning phase.

### 2.1 realfit2 does not reproduce

- **First rebuild** (2026-10-21): y, g, fam, `chunk_meta_sha256` and every other field agree with the banked manifest, but X
  hashes to `c395da3f4c1aa3cb`, not the banked `d74bd30e71a5083f` (`corpora_rebuilt`).
- **Second rebuild** (2026-10-22, the container restarted on a different CPU): X `4ff8ec5760ccb069`, y, g and fam identical.
  The two differ in exactly 6 of 193926 rows in 4 chunks, every one labelled 22 or 23 (ISA-L levels 1 and 2), the whole
  feature row moving (`second_rebuild_other_host`).
- **Run to run, not the CPU** (`isal_dispatch_test`). Both hosts select identical ISA-L code. With ISA-L forced onto each
  code-path tier, every tier but the native AVX-512 one changes y on 8 to 20 chunks; no tier or mixture gives the banked X. A third
  rebuild flipped a different chunk. A full build changes the level-1 and level-2 streams of roughly 0 to 4 chunks; 7 million
  CPU-pinned compressions in isolation produced none. Why a full build flips them: **COULD NOT VERIFY**.
- **The smoke subset reproduces.** The rows of each rebuild that form 0024's sealed smoke corpus (chunks k < 126 per family:
  16027 rows, 629 chunks) hash to its banked y, g, fam and X (`41d1d6f3ffdea27b`); `python3 -B
  tools/prereg_gen/0025/realfit2_smoke_subset_check.py` should end `... IDENTICAL to 0024's banked smoke corpus`.
- **The banked bytes are not recoverable.** The banked X is most likely the canonical X plus an unknown set of such flips;
  with no per-row or per-block banked hash it cannot be searched for (`docs/strategy/0025_DECISION.md` §3.1).
- **What it moves.** Refitted on the first rebuild, 0024's depth-3 tree at r4..r7 and r5 logistic reproduce their banked
  vectors; the r7 logistic differs on 264 of 61409 extension rows (171 real; 5248 against 5249 real correct)
  (`refits_against_0024`). 0025 as sealed cannot run on a rebuild: `run_realcurve3.py` exits 3 on a realfit2 X other than
  `d74bd30e71a5083f`, `prefreeze_0025.py` requires `--check` IDENTICAL, and 0024's intervals must recompute exactly. The
  decision memo recommends amending 0025 before its freeze (reproduction within the sealed tolerances, on one sealed rebuild
  whose npz is kept); at `c19e724` that is not made and 0025 still seals `d74bd30e71a5083f`.
- **On a cold clone** expect `--check` to print `FAIL` for X and `ok` for fam, g and y, and the smoke subset IDENTICAL.
  Compare two rebuilds block by block through their manifests' `X_blocks`.

## 3. Field-by-field manifest comparison

`--check` never reads `chunk_meta_sha256` (the chunk fields `--disjoint` reads). Diff each rebuilt manifest with the banked one;
only the fields in `skip` may differ:

```
python3 - data/pivot/ext_c4096_rebuilt_manifest.json artifacts/pivot/ext_corpus_manifest.json <<'PY'
import json, sys
a, b = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])
skip = {"build_seconds", "generated_utc", "library_versions", "platform", "X_blocks"}
print(sorted(k for k in set(a) | set(b) if k not in skip and a.get(k) != b.get(k)) or "no other field differs")
PY
```

On the session's rebuilt manifests this finds no other field for ext, realfit and realfit3, and only `arrays` (X's hash) for
both realfit2 rebuilds. Those manifests are session scratch; the engineering log banks the realfit2 statement only.

## 4. Builder cache `data/pivot/full_c4096.npz` — not rebuilt

**What it is.** 50000 source chunks of 32768 bytes (the ten Gutenberg texts and the builder's synthetic families), carved at
4096 bytes: 1300000 rows x 1108 features. Preregistrations 0018 and 0020 seal its y and g hashes in `cache_identity`; 0021 to
0025 also seal X (`a28a2d40…`, [1300000, 1108], float32). The banked build took 3415.5 s on 4 cores (`deflate_curve.json`).

**Status.** Held "until the realfit2 difference is understood, because the same question (does this machine reproduce the banked
features?) applies to it" (`corpora_rebuilt`). The decision memo schedules build, reorder, content proof and re-seal (its step 7).

- **Build only:** `python3 tools/prereg_gen/0025/build_cache.py` calls `run_study.build(50000, 32768, 4096, data/pivot/src, 4, 0,
  0)`, saves X, y, g and build_s as `run_study.py --cache` does, and refuses to overwrite an existing cache.
- **Build and train** (`docs/DILIGENCE.md`, `tools/pivot/verify.sh`):
  `python3 tools/pivot/run_study.py --cache data/pivot/full_c4096.npz --chunks 50000 --carve 4096 --model hgb --rungs 1000 10000 100000 800000 --tag full --out /tmp/deflate_curve.json --scores-out /tmp/deflate_rung_scores.json`.
  Without `--out` and `--scores-out` it overwrites the banked curve files; its curve is a re-measurement on a different draw.
- **Verification:** `python3 tools/pivot/corpus_manifest.py --check` ends `MANIFEST CHECK: FAIL (…)` even for a perfect cache,
  because `carve_c1024`, `raw_c1024` and `carve_c2048` print `MISSING …`. Read the three `data/pivot/full_c4096.npz:` lines.

**Known defect: the row order cannot be reproduced** (CORRECTIONS.md, 2026-10-21, the builder-cache entry).

- `run_study.build()` collects results with `Pool.imap_unordered(_one, tasks, chunksize=8)` and writes each batch at the next
  free row. Nothing sorts the rows before `np.savez`, so the row order is one run's worker-completion order.
- **y is order-free:** the banked `2b70426881e569f3…` equals sha256 of `np.tile(np.arange(26, dtype=np.int16), 50000)`. **g is
  not:** the banked `eda31b7cfa24640d…` differs from sha256 of `np.repeat(np.arange(50000, dtype=np.int32), 26)`
  (`677641ad70ee229c…`). In the banked manifest `carve_c1024` (written by `build()`) and `raw_c1024` (a sequential loop) hold
  the same chunks with the same y, and only `raw_c1024`'s g ascends. The CI probe's fourth build, which calls `build()`, found
  its own row order not canonical on its first run (CORRECTIONS.md, the CI-probe entry).
- **What is lost:** X, g and the row-position hashes (`eval_idx_sha256`, `pool_idx_sha256`, `pool_sorted_sha256`); the pool's
  membership moves with the order, because `grouped_split` keeps a seeded choice of row positions. The evaluation rows are a
  set of chunks whose banked order (`eval_chunk_layout`) can be restored. A rebuild should show `ok` for y and `DIFF` for X and
  g; no rebuild of this cache has been checked (**COULD NOT VERIFY**).
- **The runners refuse it.** `run_oob`, `run_realfit`, `run_realsearch`, `run_realcurve`, `run_realcurve2` and `run_realcurve3`
  refuse a cache whose y/g hashes are not the sealed ones (`REFUSING: cache carries no build metadata …`).
- **Frozen preregistrations (0018-0024).** No rebuild can meet their sealed identity: nothing banked fixes the order of the
  batches that hold no evaluation chunk, and `reorder_cache.py` gives g `82b87d8b…`, not `eda31b7c…` (CORRECTIONS.md). Their
  readers re-read banked artifacts; a builder-pool result can be re-measured on a different draw, not re-derived.

**Repair path for 0025 (committed, not run).** 0025 is unfrozen, scores only the sealed evaluation rows and fits nothing on the pool.

1. `python3 tools/prereg_gen/0025/build_cache.py`, with the machine alone; move the result to `data/pivot/full_c4096_rebuilt_raw.npz`.
2. `python3 tools/prereg_gen/0025/reorder_cache.py data/pivot/full_c4096_rebuilt_raw.npz prereg/0025-realcurve3-4096.json -o
   data/pivot/full_c4096.npz --report $RAISE_SCRATCH/reorder_report.json`: batches whole, evaluation batches in
   `eval_chunk_layout` order, each other batch after its id-predecessor. It asserts the sealed `eval_y_sha256`, `eval_g_sha256`
   and layout and an unchanged row set, else exits 3 and leaves nothing behind; it prints the new X, g and position hashes.
3. With the fit interpreter, `OMP_NUM_THREADS=3 python3 -B tools/prereg_gen/0025/cache_content_proof.py data/pivot/full_c4096.npz
   --out artifacts/verification/cache_rebuild_0025.json --allow-repo-out` refits 0021's B-feat1, D1, M1 and L3 on 0021's fit
   block and compares each row's 0/1 correctness with the banked vectors: extension rows (control), evaluation rows (test). It
   catches gross content errors; it is not a byte-equality proof. Its control part (`--ext-only`) already reproduces exactly
   (`fitting_environment_reproduces`).
4. `python3 tools/prereg_gen/0025/amend_cache_0025.py` refuses unless that proof passed in full mode on the same cache and the
   order proof holds; it re-seals `cache_identity` X and g, the evaluation-row position hash and the three pool hashes, keeping
   each banked value as `*_banked_2026_08` and recording the change under `amendments_before_freeze`.

None of these has run; `artifacts/verification/cache_rebuild_0025.json` does not exist.

## 5. Smoke corpora sealed in the preregistrations

Built into scratch, with array hashes sealed under `smoke`; they exercise the runners and carry no verdict. Only
`corpus_realfit2.py` and `corpus_realfit3.py` refuse a capped build aimed at the sealed corpus path: always pass `--out`.

| sealed in | npz (scratch) | command or recorded parameters | 2026-10-21/22 |
|---|---|---|---|
| 0018 | `smoke_oob/ext_small.npz` | `corpus_ext.py`, n_per_family 5, seed 20260909; command not recorded | not rebuilt: **COULD NOT VERIFY** |
| 0020-0022 | `smoke_realfit/fit_small.npz` | 15 chunks, 390 rows; command not recorded | not rebuilt: **COULD NOT VERIFY** |
| 0020-0025 | `smoke_realfit/ext_small.npz` | `corpus_ext.py --build --n-per-family 4 --out <s>/ext_small.npz --manifest <s>/ext_small_manifest.json` | rebuilt; array hashes equal 0025's `smoke.ext_corpus` (session log) |
| 0023-0025 | `smoke_realfit/fit_small16.npz` | `corpus_realfit.py --build --cap-per-family 16 --out … --manifest …` | rebuilt; equal to `smoke.fit_corpus` (session log) |
| 0024, 0025 | `fit2_small.npz` (0024: `smoke_realfit2/`, 0025: `smoke3/`) | `corpus_realfit2.py --build --cap-per-family 126 --base-per-family 16 --out … --manifest …` | capped build not run: **COULD NOT VERIFY**; the same rows, taken from each full rebuild, hash to the sealed smoke hashes (§2.1) |
| 0025 | `smoke3/fit3_small.npz` | `corpus_realfit3.py --build --cap-per-family 128 --base-per-family 16 --realfit2 <fit2_small.npz> --realfit2-manifest <its manifest> --out … --manifest …` | not built: **COULD NOT VERIFY** |

## 6. Which code the rebuilds ran

ext, realfit and the first realfit2 rebuild started on 2026-10-21 before `27a61aa`, with `--manifest` passed to a scratch path;
realfit3 ran on 2026-10-22 before `35b6493` (its manifest has no `platform` block); the second realfit2 rebuild's manifest has one.
Two commits since the first rebuilds touch the four builders: `27a61aa` (where `--build` writes its manifest; the source check
in `corpus.load_real()`, which none of them calls) and `35b6493` (`platform`, `X_blocks`). Neither changes a builder's `build()`.
At `c19e724`, `fetch_ext_sources2.sh`, `fetch_ext_sources3.sh` and `corpus_realfit2.py` are unchanged since their logged runs;
the other fetch scripts and builders have changed and have not been run end to end since (**COULD NOT VERIFY**).

## 7. Evidence

- **Committed:** `CORRECTIONS.md` (2026-10-21: the cold clone, the CI probe, the builder cache's row order; 2026-10-22:
  realfit2); `artifacts/pivot/engineering_log_0025.json`, `container_2026_10_21` (`sources`, `environment`, `corpora_rebuilt`,
  `realfit2_localisation_2026_10_22` with `second_rebuild_other_host` and `isal_dispatch_test`, `fitting_environment_reproduces`);
  `docs/strategy/0025_DECISION.md`; the banked manifests in `artifacts/pivot/`; `prereg/0018-…` to `prereg/0025-…`
  (`cache_identity`, `smoke`); `tools/prereg_gen/0025/` and its README.
- **Session logs** (scratch, not committed): `rebuild/build_chain.log`, `rebuild/fetch_*.log`, `rebuild/realfit3_alone2.log`,
  `rebuild/smoke_light.log`, the rebuilt manifests, and the dispatch test's scripts and data (`isal_recover/`).
