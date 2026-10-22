# outbound/

Anything intended to leave this repository — an email, a one-pager, a deck, a post.

**The rule:** every number in every file here must trace to a banked artifact under `artifacts/`,
at the precision it is written. `python3 tools/claimcheck.py outbound VERDICT.md` checks a necessary
condition only: it exits non-zero when no banked value (or that value times or divided by 100) rounds to a
number at its written precision, and has mutation tests proving it can fail (`tests/mutation_test.py`,
gate `claimcheck`). It does not check that a number came from the artifact its sentence cites; which
artifact field a number comes from is checked only for the numbers registered in `docs/live_claims.json`
(`tools/freshness.py`).

Numbers that are genuinely not measurements go in `docs/claimcheck_allowlist.tsv` **with a written
reason**. An allowlist entry without a reason is a hard error, not a warning.

**Licence, decided deliberately:** everything in this directory is under the repository's
Apache-2.0 licence (`LICENSE`, `NOTICE`), the same as the code. The compliance audit
(`docs/compliance/LICENSE_AUDIT.md`, finding F10) asked whether investor-facing prose was meant to
be Apache-licensed by default. It is. A recipient's engineer may copy, modify and re-run anything
here; a document whose numbers a stranger can check against the banked artifacts has nothing to protect.
A stranger cannot re-derive every number by rebuilding: results fitted on a builder pool can be re-measured on a
different draw, not on the same rows, and one real-content corpus (0024's) does not rebuild byte for byte
(`outbound/EVIDENCE_BRIEF.md`, "Verify on a cold clone"; `CORRECTIONS.md`, 2026-10-21 and 2026-10-22).
