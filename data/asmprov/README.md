# data/asmprov/

Public NCBI assembly metadata for three bacterial taxa (*E. coli*, *K. pneumoniae*,
*S. aureus*) — 239,744 labelled records — plus four raw result files.

## How these got here, which is worth stating

These files were written into the repository by a round-2 adversarial reviewer and were then
swept into a commit by a blanket `git add -A` **without being examined first**. They were reviewed
afterwards, which is the wrong order. They are public NCBI metadata (accession, taxon, organism,
assembly method string, sequencing technology, contiguity statistics, submitter, BioProject,
release date) and contain nothing sensitive.

They are kept rather than deleted for a specific reason: unlike every other subagent measurement
in this project, **the inputs survived**. That made it possible to write the analysis afterwards
and re-derive the central result, which `tools/repro/assembly_provenance_splits.py` now does —
moving the assembly-provenance kill out of the weakest verification class.

## Files

| File | What it is |
|---|---|
| `ecoli.jsonl`, `kpneu.jsonl`, `saureus.jsonl` | 240,000 NCBI assembly metadata records, one JSON object per line. |
| `RESULTS_splits.txt` | The original reviewer's split-sensitivity output, over ten taxa. |
| `RESULTS_nullcontrol.txt` | The original reviewer's negative-control output. |
| `RESULTS_defline.txt`, `RESULTS_lengthmultiset.txt` | The original reviewer's other outputs. **Not reproducible from these inputs** — the defline result needs contig names, which the banked records do not contain. |

## Scope

The originating measurement used **ten** taxa; **three** are banked here. Sample sizes therefore
differ and the reproduction is not expected to match the original to the decimal. What is
reproduced is the *pattern*, and it does reproduce.
