# artifacts/

Banked, machine-readable results. **This directory is the only legal source of a number in
any document produced by this project** (`docs/OPERATING_RULES.md` §2), and
`tools/claimcheck.py` enforces that mechanically.

Every file here should carry a `schema` field naming its shape and version, so a reader can
tell what a value means without reading the code that produced it.

| Path | What it holds |
|---|---|
| `verification/mutation_report.json` | Which gate mutations were detected, and which survived. |
| `phase0/` | Domain-selection evidence: reachability probes, white-space search records. |
