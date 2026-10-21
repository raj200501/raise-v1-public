# Preregistration 0025's generators and operator scripts

Until 2026-10-21 the scripts that wrote each preregistration's sealed file and generated its frozen reader lived only in the
session's scratchpad. That container was replaced and they were lost; `prereg/0025-realcurve3-4096.json` and
`tools/readers/realcurve3_4096_verdict.py` survived because they are committed. From 0025 on they are committed here.

| file | what it does |
|---|---|
| `gen_reader_0025.py` | generates `tools/readers/realcurve3_4096_verdict.py` from the preregistration and `reader_0025_template.py` (Python %-substitution; every literal from the sealed file or a banked artifact). Rebuilt on 2026-10-21 from the session transcript and the committed reader, and proven by regenerating the committed reader byte for byte from the committed preregistration. `tools/prereg_checks/prefreeze_0025.py` runs it (env `PREREG_0025_GENERATOR`) and refuses a reader that is not its output. |
| `reader_0025_template.py` | the reader with its sealed literals as `%(name)s` placeholders. |
| `amend_prereg_0025.py` | applies the pre-freeze instrument review's changes to the unfrozen preregistration as exact, asserted replacements, recomputes the sealed hashes, records each change under `amendments_before_freeze`. The original generator, `make_prereg_0025.py`, was lost; its output is the committed file before the amendment. |
| `freeze_docs_0025.py` | writes the in-flight paragraphs in `VERDICT.md` and `README.md` from the sealed file after the freeze. |
| `make_englog_0025.py` | writes the pre-freeze fields of `artifacts/pivot/engineering_log_0025.json` (reads the runner smoke from `$RAISE_SCRATCH/smoke_realcurve3/out.json`). |
| `capture_fixture_0025.py` | captures `tests/fixtures/realcurve3_runner_shape.json` from the runner's smoke (`$RAISE_SCRATCH/smoke_realcurve3/`). |
| `update_counts_0025.py` | moves the banked mutation count and gate count in every document that states them, from the report itself. |
| `build_chain.sh`, `build_cache.py` | the cold-clone rebuild of 0018's, 0021's, 0024's and 0025's corpora (each manifest written outside `artifacts/` and then checked against the banked one) and of the builder cache without training. |

`tools/publish/build_mirror.sh` builds the public, history-filtered mirror (rebuilt the same day and verified to reproduce
every published mirror commit hash).
