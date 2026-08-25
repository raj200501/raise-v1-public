# outbound/

Anything intended to leave this repository — an email, a one-pager, a deck, a post.

**The rule:** every number in every file here must trace to a banked artifact under `artifacts/`,
at the precision it is written. Enforced by `python3 tools/claimcheck.py outbound VERDICT.md`,
which exits non-zero otherwise and has mutation tests proving it can fail
(`tests/mutation_test.py`, gate `claimcheck`).

Numbers that are genuinely not measurements go in `docs/claimcheck_allowlist.tsv` **with a written
reason**. An allowlist entry without a reason is a hard error, not a warning.
