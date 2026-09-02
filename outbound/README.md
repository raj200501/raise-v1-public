# outbound/

Anything intended to leave this repository — an email, a one-pager, a deck, a post.

**The rule:** every number in every file here must trace to a banked artifact under `artifacts/`,
at the precision it is written. Enforced by `python3 tools/claimcheck.py outbound VERDICT.md`,
which exits non-zero otherwise and has mutation tests proving it can fail
(`tests/mutation_test.py`, gate `claimcheck`).

Numbers that are genuinely not measurements go in `docs/claimcheck_allowlist.tsv` **with a written
reason**. An allowlist entry without a reason is a hard error, not a warning.

**Licence, decided deliberately:** everything in this directory is under the repository's
Apache-2.0 licence (`LICENSE`, `NOTICE`), the same as the code. The compliance audit
(`docs/compliance/LICENSE_AUDIT.md`, finding F10) asked whether investor-facing prose was meant to
be Apache-licensed by default. It is. A recipient's engineer may copy, modify and re-run anything
here; a document whose numbers can be re-derived by a stranger has nothing to protect.
