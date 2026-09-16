# Corrections ledger

Every claim withdrawn or revised, dated, at the same size as the claim it replaces.

The rule (`docs/OPERATING_RULES.md` §5): an over-claim against our own interest is still an
over-claim and gets filed here at full size. Entries are append-only. Nothing is deleted; a
correction that is itself wrong gets a further entry.

Format:

```
## YYYY-MM-DD - <one-line description>
**Claimed:**   what was said, quoted, with where it was said.
**Actual:**    what is true, with the artifact that establishes it.
**Size:**      how much the claim moved, in the units of the claim.
**Cause:**     why the wrong version was written.
**Fix:**       what changed in the instrument so this class of error is caught next time.
```

---

## 2026-09-16 — Said the mutation gates' controls are never built from the reader's expectations; four of them are, and it hid ten VOID clauses in an unfrozen preregistration

**Claimed.** `docs/OPERATING_RULES.md` §4 states the rule without exception: a reader's
mutation-gate control artifact "is never built from the reader's expectations, because a control
that shares an assumption with the reader cannot see the reader disagree with the world." The
`realfit4096` gate carried a case literally named
`the-control-artifact-is-built-from-the-runners-own-output-shape`, which passed, and
`tests/fixtures/realfit_runner_shape.json` said in its own `why` field that it existed "so the
realfit4096 mutation gate builds its control from the RUNNER's output shape rather than from the
reader's expectations (docs/OPERATING_RULES.md section 4)". All of that was in the repository and
none of it was true of the gate as written.

**Actual.** `_good_realfit` in `tests/mutation_test.py` loaded the captured fixture and then
replaced 51 of its 52 keys, taking `corpus`, `ext_corpus`, `fit_corpus`, `protocol` and
`partition` wholesale from the frozen reader's own module constants — `dict(r20.FIT)`,
`dict(r20.EXT)`, `dict(r20.CORPUS)`, `dict(r20.PARTITION)` — and injecting a `ledger` key the
runner did not write at all. The only artifact value still inherited from the runner by provenance
was `cluster_ci95_note`. The case that asserts §4 computed `set(shape) - set(art)`: one direction,
one nesting level, against a static committed file. An invented key was therefore invisible, every
nested divergence was invisible, and the fixture was itself already two `partition` keys stale
(`repro_idx_sha256`, `matched_idx_sha256`) with nothing able to notice.

The consequence was not hypothetical. Preregistration 0020's generated reader required a `ledger`
block that `tools/pivot/run_realfit.py` never banked, and carried four `fit_corpus` literals taken
from the corpus manifest's *built* counts where the runner measures the counts of chunks that
carry rows — `n_chunks` 1035 against 1029, `chunks_per_family` pe_bin 207 against 203 and py_src
674 against 672, `chunk_id_max` 20400000 (a hand-derived `chunk_id_base + 4 × family_stride`)
against the measured 20400039 — plus a `ceiling_distinct_fragments` key the runner never writes.
An honest, complete, valid run would have emitted **VOID on ten clauses** after about an hour of
fitting, and an artifact that *misdescribed* the fit corpus would have passed while the truthful
one voided. The gate was 33/33 green throughout. The pre-freeze check was green too: it compared
`r20.FIT["arrays"] == P["fit_corpus"]["arrays"]`, two copies of the same literal, for precisely
the fields that were wrong.

Three of five independent pre-freeze reviewers found the `ledger` defect separately; two of them
found the four literals. It was caught before the freeze and before any run, so no published
number was ever affected — but the claim about how the gates are built was published, and it was
false.

**Size.** Four gates of twenty-two build their controls this way (`oob4096`, and three siblings
whose docstrings say so, plus `realfit4096`). One preregistration's instrument, unfrozen, would
have voided its own run on ten clauses; the cost had it not been caught is one full run of the
six-arm design, banked as VOID, plus a re-read preregistration to recover it — which is exactly
what 0018 and 0019 cost. Against the rule as written, the gap is total rather than partial: §4
admits no exception and four gates take the exception.

**Cause.** The rule was written after the 0012 defect and mechanised for one gate; later gates
copied the *shape* of that mechanisation — load a fixture, then overwrite — without its substance,
and the case asserting the rule was written to check that nothing was *lost* rather than that
nothing was *invented*. A one-directional set difference reads as a completeness check and is not
one. Filing it as an open follow-up in `artifacts/pivot/engineering_log_0019.json` rather than as
a correction was the second mistake: it was already known, already written down as a gap, and
still shipped into 0020's instrument, because a follow-up has no gate behind it and a correction
demands a fix.

**Fix.** Four changes, all made for `realfit4096`, and the class is now filed as a correction
rather than a follow-up so the remaining three gates are owed the same.

1. `tools/pivot/run_realfit.py` grows a module-level `corpus_block()`, which the runner, the
   preregistration generator and the pre-freeze check all **call**. The sealed
   `scope.protocol.fit_corpus` and `ext_corpus` are its output rather than a retyping of the
   manifest; descriptive fields moved to `fit_corpus_described`, which nothing compares.
2. `_rf_sub()` in `tests/mutation_test.py` substitutes sealed values *into* the runner's own
   captured block key by key and raises on any key the two do not share, so a reader that expects
   a field the runner does not write fails at control-construction time.
3. The provenance case is symmetric (`set(shape) ^ set(art)`) and recurses into `corpus`,
   `ext_corpus`, `fit_corpus`, `partition`, `readings` and every record, and additionally asserts
   that every key the reader compares is a key the runner writes.
4. The pre-freeze check rebuilds both corpus blocks by calling the runner, asserts every reader
   expectation is a runner-written key, and asserts the captured fixture is current with the
   runner in the tree. The fixture was recaptured from a smoke of the current runner — which
   itself required fixing a runner whose sealed-hash refusals ran before its smoke guard, so the
   documented smoke invocation could not execute against the committed preregistration and the
   fixture's stated provenance was not reproducible.

`realfit4096` goes from 33 cases to 54; the new ones include a case that deletes the `ledger`, a
case for each wrong `fit_corpus` literal, and a case asserting that an artifact which misdescribes
the corpus is VOID rather than a pass.

---

## 2026-09-10 — Preregistration 0018 sealed the wrong null-block hash, and its frozen reader voided an honest run on it

**Claimed:** `prereg/0018-oob-4096.json` `scope.sealed_partition.null.null_sorted_sha256` =
`0653cc12…`, described in `scope.partition_sealed_before_any_fit` as "0003's sealed split, restated
hash for hash from 0017's sealed_partition (eval, pool, null)", beside `scope.design` and the NULL
arm, which say the null control is "M4 on the first 20000 pool rows with shuffled labels"; the
frozen reader `tools/readers/oob4096_verdict.py` carries the same literal, and by freezing it into
chain entry 18 with 72 mutation cases behind it we claimed it would emit a verdict on any complete,
valid run of the protocol. `VERDICT.md`'s in-flight paragraph said nothing below it changes until
the frozen reader has read the completed run.

**Actual:** Two different row blocks have served as "the null block" in this record. 0014
(`artifacts/pivot/recipe_search_4096.json`, `null_control.fit_rows_sorted_sha256`) and 0016
(`prereg/0016-fdc-4096.json`, `sealed_partition.null.sorted_sha256`, "the first 20000 pool rows")
use the first 20000 rows of 0003's sealed pool in its sealed order, `822b6102…`. 0015 and 0017
(`tools/pivot/run_lofo.py`, `tools/pivot/run_lofo_l3.py`: `null_rows = folds[families[0]][:nn]`)
use the first 20000 training rows of the first leave-one-family-out fold (gutenberg withheld),
`0653cc12…`. 0018's design, its arms and its runner (`tools/pivot/run_oob.py`: `null_rows =
tr[:nn]`) use the pool block, and the run fitted the null control on it
(`artifacts/pivot/oob_4096.json`: `partition.null_sorted_sha256` and
`fits.null.fit_rows_sorted_sha256` both `822b6102…`; labels permuted, same multiset); the
preregistration sealed 0017's fold block. The reader compared the block's hash, and the fingerprint
derived from it, against the wrong literal and emitted `VOID` on five clauses, all of them that one
hash (`artifacts/pivot/oob_4096_verdict.json`, banked as emitted). Every other clause passed: the
three pool fits reproduce 0014's 0.2395, 0.2317 and 0.2884 exactly, the null control reads 0.0371
on the extension rows and 0.0383 on the sealed rows, the extension arrays, chunk layout and pool
hash to the sealed values, and both measured overlaps are 0. Recomputed on 2026-09-10 from the
cache's `y` and `g` arrays with the runner's own split function: the first 20000 pool rows hash to
`822b6102…` and the first fold's first 20000 training rows to `0653cc12…`. A scratch copy of the
reader with that one literal changed, its output redirected to the session scratchpad, reads
`OOB_TRANSFER_FAILS` (2450 of 38452 real-family rows correct, 0.0637, against 3402 needed) with no
validity clause failing; that scratch reading is not a verdict and is quoted here only to size the
defect.

**Size:** One preregistration's verdict, from a reading of the run to no reading of the run, after
21995.4 s of banked fit time (one launch, 02:25 to 08:38 UTC). In the bar's units, nothing: the
literal has no arithmetic content, and the numbers it hid point the way the preregistration's own
discount of its within-builder arithmetic allowed for (a fail, with the real-family reading below
the 0.097 to 0.118 bracket that arithmetic gave).

**Cause:** Two. (1) The preregistration generator restated the sealed partition "hash for hash from
0017" because 0017 and 0018 share the pool and the evaluation set, and the null block travelled in
the same three-field block; nobody checked that 0017's null block is 0015's fold block rather than
the pool block the design names, and the sealed field did not say which block it was. (2) The 0018
pre-freeze check compared the reader's literals to the preregistration's, so both were wrong
together, and the mutation gate built its control artifact from the reader's literals; neither
compared against the block the runner builds on the real pool. The smoke run could not catch it: a
smoke's null block is required to be smaller than the sealed one, so the smoke's reader exercise
had the null-block clause patched out. This is the 2026-09-03 failure in a new coat: a control that
shares an assumption with the reader cannot see the reader disagree with the world
(`docs/OPERATING_RULES.md` §4), and this time the shared assumption was a sealed literal rather
than a code path.

**Fix:** 0018 stands `VOID` on its own reader; nothing sealed changes. Preregistration 0019 re-reads
the same banked artifact under a reader that is 0018's frozen file with exactly the substitutions
declared in the preregistration (the output path, the stamp, the schema name, the print prefix, a
docstring prefix and the one literal), with every known number disclosed and the outcome the
numbers give committed to in advance (0013's precedent). The 0019 pre-freeze check recomputes the
null block from the cache's `y` and `g` with the runner's split and requires the literal to equal
it, the artifact's partition, 0014's null control and 0016's sealed null. The oob4096 mutation
gate now builds control artifacts from either reader's literals and keeps the defect visible:
0018's reader must `VOID` the block the runner fits, the re-read reader must `VOID` 0018's literal,
and the re-read reader must equal 0018's reader plus the declared substitutions, with a tampered
copy detected. Any later preregistration that restates a null block from a predecessor must say
which block it is beside the hash, and its pre-freeze check must recompute it from data.

**Addendum, 2026-09-10 (before the 0019 freeze), from the 0019 pre-freeze review; the entry above
stands as committed at b5ed4bf.** Four sentences above are wrong or short, and this ledger is
append-only, so they are corrected here rather than in place. (1) "Every other clause passed"
overstates what 0018's reader evaluated: the reader stops recomputing after a fit clause fails,
so its readings, reproduction, null-tolerance and transfer clauses were never reached; the scope,
corpus, extension-corpus, partition, environment, order and every other sealed-hash clause it did
evaluate passed, and the reproductions, null readings and overlaps quoted above are the
artifact's own banked values, which 0019's reader evaluates for the first time. (2) The 0018
pre-freeze check did more than compare two copies: it required the reader's partition block, null
hash included, to equal 0017's reader's, and labelled that block 0003's split; the correct
literal would have failed that check. (3) The quotation attributed to `scope.design` and the NULL
arm is `scope.design`'s; the arm says "0003's pool's first 20000 rows with shuffled labels". (4)
The Fix's gate sentence misdescribes the remedy: the gate's control artifacts are still built from
a reader's literals (every sealed hash but one is the reader's own copy, as `docs/OPERATING_RULES.md`
§4 warns); what closes the null-block hole is a case that requires 0019's literal to equal the
banked artifact's partition and null-fit hashes, 0014's null control and 0016's sealed null, and
0018's literal to equal 0015's and 0017's sealed nulls and lofo artifacts, plus the committed
recomputation `tools/pivot/null_block_check.py` (run by that case when the cache is present, and
exercised on a small cache in two further cases so it can be shown to fail). The closing rule is
now standing text in `docs/OPERATING_RULES.md` §4 (added 2026-09-10).

---

**Second addendum, 2026-09-16 (committed with the 0019 freeze), from the adversarial check of the
published record; the entry and the first addendum above stand as committed.** Three things in what
is above are wrong or stale. (1) The first addendum is dated 2026-09-10; it was drafted that day in
the session that filed the entry, and the session then paused, so it was first committed on
2026-09-16 in `36b1849`, six days after the date it carries. The same applies to the sealed-literal
paragraph added to `docs/OPERATING_RULES.md` §4, which carries 2026-09-10 and was committed on
2026-09-16. Both dates are the drafting date, not the publication date, and this addendum is the
correction; the dates above are not edited, because this ledger is append-only. (2) The list of the
re-read reader's declared substitutions in the Fix above names six; the preregistration declares
**seven** — the missing one is the headline print line, which makes the re-read reader announce
itself as a re-read. (3) The freeze order is not what git's commit order suggests: the chain entry
and the `frozen: true` flag were committed in the publication commit `932a73b` (2026-09-16T04:27:45Z),
after the commit that banked the verdict (`b7afe1a`, 04:15:17Z), while the freeze itself ran at
2026-09-16T04:14:59Z and the reader at 04:15:07Z. The chain entry's `frozen_utc` and its beacon
anchors order the freeze against the reading; the commit order does not.
`artifacts/pivot/engineering_log_0019.json` (`chronology`) banks the times, and the next
preregistration commits the chain entry in the same step as the freeze.

---

**Third addendum, 2026-09-16, from the adversarial check of the published record.** Five smaller
things, filed rather than edited in place. (1) The preregistration declares **eight** substitution
entries covering seven kinds of change; the second addendum above says "seven", which counts the
kinds, and `VERDICT.md` now says both. (2) `docs/OPERATING_RULES.md` §4 says without exception that a
reader's mutation-gate control artifact is built from the runner's output shape; the `oob4096` gate
builds its control from a reader's sealed literals, and three sibling gates do the same. That is the
construction this entry's defect defeats, and the rule and the gates disagree: filed as an open
follow-up in `artifacts/pivot/engineering_log_0019.json`, with the other three that check found (the
coverage gate never resolves a claim's `json_path`; six wall-clock `-fit-seconds` claims sit in the
strongest verification class; no repository tool guards an in-flight paragraph's clause). (3) The
0019 engineering log credited the committed pre-freeze check with two checks it does not perform —
that the reader's headline print line announces a re-read and that its docstring quotes the runner's
lines verbatim. Both were read by the operator and by the review, not asserted by the script; the log
now says so. (4) One line of that committed script could not fail (`x or True`); it is now a real
comparison against the commit that banked the artifact, and the banked `PASS` in
`artifacts/verification/prefreeze_0019.json` belongs to the version with that line inert. The script
also refuses to run after the freeze rather than overwrite the result it banked. (5) Two commit
messages state mutation-gate case counts the banked report does not (`36b1849` "gate 87 cases",
`b5ed4bf` "oob4096 gate 80 cases", against 85 at HEAD and 80 at that commit's suite run); commit
messages are not rewritten here because the preregistration chain seals commit hashes, and the banked
report is the count the record uses.

---

## 2026-09-10 — VERDICT.md's in-flight paragraph for 0018 described the clause the pre-freeze review had replaced

**Claimed:** `VERDICT.md`, the in-flight paragraph for 0018, from the freeze commit (7e4207e,
2026-09-10 02:24 UTC) until this entry's commit: "One clause, read by
`tools/readers/oob4096_verdict.py` on the recounted score vectors: M4's correct extension rows must
reach 5433 of 61409 (chance + 0.05)".

**Actual:** The sealed clause (`prereg/0018-oob-4096.json` `bar.transfer`, `scope.protocol.bar`,
the frozen reader's `MIN_CORRECT_REAL`) is M4's correct rows over the 38452 rows of the five
real-file families, 3402 needed; the eight-family mixture at 5433 of 61409 is a flag, banked and
never quoted as the verdict. The pre-freeze review re-scoped the clause from the mixture to the real
families before the freeze, because a mixture could be carried by the three families this record's
own generators produced; the paragraph kept the pre-review wording.

**Size:** One number pair in one paragraph, for about seven hours, describing a bar the sealed
instrument does not apply. The preregistration, the reader, the 72-case gate and the verdict file
were right throughout; no number in the paragraph was quoted as a result. The README's in-flight
sentence named no count.

**Cause:** The freeze-time documentation script carried the clause sentence from the design note
that the review superseded, and an in-flight paragraph is not a registered live claim, so no gate
compared it to the sealed clause.

**Fix:** The paragraph is replaced by the 0018/0019 section, which quotes the clause from the
verdict file. The 0019 pre-freeze check asserts that the 0019 preregistration quotes the clause as
3402 of 38452 and does not quote the mixture threshold as the clause; the 0019 publication script
refuses to apply the documents if the replaced sentence survives anywhere in `VERDICT.md` or
`README.md`.

**Addendum, 2026-09-10 (before the 0019 freeze), from the 0019 pre-freeze review; the entry above
stands as committed at b5ed4bf.** (1) The span is wrong: the sentence did not stop being published
at that entry's commit; it stands in `VERDICT.md` until the publication commit that replaces the
in-flight paragraph with the 0018/0019 section, after 0019 is frozen and read, so "about seven
hours" is the span to the entry, not to the fix. (2) `README.md`'s in-flight sentence is the same
defect without a count: "asks whether the headline recipe identifies the encoder on eight content
families the corpus builder never produced (61409 evaluation-only rows: ...), at chance + 0.05; it
is frozen and running" frames the bar over the eight families; it is replaced at the same
publication commit. (3) "The preregistration, the reader, the 72-case gate and the verdict file
were right throughout" should read "carried the clause as 3402 of 38452 throughout"; the
preregistration's null-block literal is the entry above. (4) The Cause is wrong about the
mechanism: the freeze-time script (the session's `freeze_docs_0018.py`) generated the sentence
from the sealed preregistration, but read `scope.protocol.min_correct` (the mixture flag's
threshold, 5433) and the corpus row count into a hard-coded "correct extension rows must reach"
template instead of `bar.transfer`'s threshold and denominator (3402 of 38452); so "generated
from the sealed preregistration" is the guard that failed, and the durable guard is that in-flight
text quotes the clause from the `bar` fields and is checked against them before the freeze commit.
(5) The Fix's "recorded in the same log" was written before the record existed; the publication
script's name, sha256 and its exact refusal strings are now banked in
`artifacts/pivot/engineering_log_0019.json` (`publication`), and the 0019 pre-freeze check is
committed as `tools/prereg_checks/prefreeze_0019.py` with its result banked in
`artifacts/verification/prefreeze_0019.json`.

---

**Second addendum, 2026-09-16 (committed with the 0019 freeze), from the adversarial check of the
published record; the entry and the first addendum above stand as committed.** Four corrections to
what is above. (1) The wrong sentence's span is now known exactly: it was published from the 0018
freeze commit `7e4207e` (2026-09-10T02:24:31Z) to the publication commit `932a73b`
(2026-09-16T04:27:45Z) — six days and two hours, not the "about seven hours" the Size paragraph
states, and the first addendum could not name the figure because the publication had not happened
yet. The README's in-flight sentence, which framed the same clause over the eight families without
a count, was published for the same span and replaced in the same commit. (2) Item (5) of the first
addendum corrects a phrase, "recorded in the same log", that the committed entry never contained;
it was written against a draft of the Fix. What the committed Fix actually says is that "the 0019
publication script refuses to apply the documents if the replaced sentence survives anywhere in
`VERDICT.md` or `README.md`" — that script is the session's `apply_0019_docs.py`, its sha256 and its
refusal strings are banked in `artifacts/pivot/engineering_log_0019.json` (`publication`), and it is
not a repository tool. (3) The same Fix's "durable guard" is therefore not yet in the repository:
nothing here asserts that an in-flight paragraph quotes the clause from the sealed preregistration's
`bar`. That gap is filed as an open follow-up in `artifacts/pivot/engineering_log_0019.json`
(`open_instrument_follow_ups`), with two others the same check found: the coverage gate never
resolves a claim's `json_path`, and six wall-clock `-fit-seconds` claims sit in the strongest
verification class with a command that reads the number back rather than re-deriving it. (4) The
addendum above is dated 2026-09-10 and was committed on 2026-09-16, as the companion entry's second
addendum records.

---

## 2026-09-10 — Three sealed preregistrations count their own place in the sealed-set ledger one short

**Claimed:** `prereg/0015-lofo-4096.json` `scope.sealed_set_disclosure`: "This is the third
preregistration scored on 0003's sealed evaluation set: 0003 scored it 12 times, 0006 for top-k,
0014 10 times plus 10 in a smoke confirm; 0015 adds 27 scorings"; `prereg/0016-fdc-4096.json`: "the
fourth preregistration"; `prereg/0017-lofo-l3-4096.json`: "the fifth preregistration".

**Actual:** Each sentence lists its predecessors correctly and then names an ordinal that counts
them without the entry itself: 0003, 0006 and 0014 are three, so 0015 is the fourth preregistration
scored on the sealed set, 0016 the fifth and 0017 the sixth. Preregistration 0018 says "the
seventh", which is right. The scoring counts in the same sentences (12, top-k, 10 plus 10, 27, 258,
10) are unchanged and traceable to the artifacts they name.

**Size:** One in an ordinal, in three sealed documents. No measurement, clause, hash or scoring
count moved, and no reader read the ordinal.

**Cause:** The sentence was copied forward from 0015 to 0016 to 0017 with the predecessor list
extended by one and the ordinal incremented by one, so the original off-by-one propagated; nobody
recounted the list against the ordinal. It was found by the 0018 pre-freeze review's wording
reviewer, who counted.

**Fix:** The three sentences are sealed by the chain and stay as written; this entry is the
correction (the chain's append-only rule, `docs/OPERATING_RULES.md`). The 0018 pre-freeze check
now asserts that the ordinal in its own disclosure equals one plus the number of predecessors it
lists, so the sentence cannot be copied forward with a stale ordinal again.

---

## 2026-09-04 — Three different counts of this ledger, and two of the preregistration chain, in the outbound documents

**Claimed:** `outbound/EVIDENCE_BRIEF.md`: "**11** preregistrations, hash-chained" and "**13**
corrections filed against this work"; `outbound/NARRATIVE.md`: "13 preregistrations", "The
corrections ledger now carries 13 entries" and, later in the same document, "12 corrections at
full size"; `docs/DILIGENCE.md`: "`CORRECTIONS.md`: thirteen entries at full size".

**Actual:** The chain held 13 entries (`artifacts/verification/prereg_status.json`, `chain|len`)
and this ledger held 14 dated entries before this one (`artifacts/verification/record_counts.json`,
`corrections_entries`, now 15 with this entry).

**Size:** The preregistration count was understated by 2 in one document. The corrections count
was understated by 1 in three places and by 2 in a fourth. No measured result moved; the numbers
describing the instrument were stale, which is the class of error the ledger's first entry of
2026-08-25 (a mutation count that did not match the repository) was supposed to have ended.

**Cause:** Each sentence was typed with the count current at the time and never registered as a
live claim. `tools/freshness.py` checked the chain length and head in `VERDICT.md` only; no
artifact banked the ledger's own length, so there was nothing to register a claim against.

**Fix:** `tools/record_counts.py` banks the ledger's entry count into an artifact and runs in
`tools/gates.sh`; six live claims in `docs/live_claims.json` now tie every one of the sentences
above to `prereg_status.json` or `record_counts.json`, so the next drift fails the gate instead of
waiting for someone to notice.

---

## 2026-09-03 — Preregistration 0012's frozen reader voided an honest run because of a defect in the reader, and the mutation gate had been built to the reader's assumption

**Claimed:** Implicitly, by freezing `tools/readers/recipe2048_verdict.py` into chain entry 12 with 25
mutation cases behind it: that the reader would emit a verdict on any complete, valid run of the
0012 protocol. `VERDICT.md` said, in the 0011 section, that 0012 "is frozen, and is running" and
that "no 0012 number appears in this document until its frozen reader emits one".

**Actual:** The run completed cleanly — 50 checkpoints, zero evaluation rows gathered during
selection, both reproduction controls landing on 0011's banked values to four decimals (0.1741 and
0.1266), the null control at 0.0408, the model's single scoring last — and the frozen reader
emitted `VOID` on two clauses: *"head model stage 2 records ['M4', 'M7'] are not ['M7', 'M4'] in
roster order"* and the same for the deep-tree head. The runner fits the two second-stage survivors
in roster order (M4 before M7, T2 before T3), which is the order every other clause of the reader
uses; the reader's implementation expected them in ranked order. Both orderings hold the same two
records, the same ranking and the same winner, and the reader's own re-derivation of the winner
agreed with the banked one for every head. The VOID is banked as emitted
(`artifacts/pivot/recipe_search_2048_verdict.json`). A scratch copy of the reader with that one
line changed reads `RECIPE_FAILS` on all three margins (0.212 − 0.1886, 0.212 − 0.1886,
0.2223 − 0.1975: 0.0234, 0.0234 and 0.0248 against the 0.05 bar); that scratch reading is not a
verdict and is quoted here only to size the defect.

**Size:** One preregistration's verdict, from a reading of the run to no reading of the run. In
the bar's units, nothing: the defect has no arithmetic content and the numbers it hid point the
way the preregistration predicted (`RECIPE_FAILS`, with the searched logistic raising the frozen
bar from 0.1266 to 0.1886, more than the searched model's gain from 0.1741 to 0.212).

**Cause:** Two, and the second is the one that matters. (1) The reader's stage-loop reused the
ranked list as the expected record order for later stages; the runner iterates the roster. (2)
The mutation gate's synthetic "good" artifact was built inside the test from the reader's
assumption — survivors listed in ranked order — instead of from the runner's behaviour, so the
control case passed and 24 mutations were detected against an artifact shape the runner never
produces. A gate that mirrors the thing it is checking cannot see that thing's disagreement with
the world; this is the same failure the 2026-08-25 allocation-flag entry names, one level up: a
check that shares an assumption with the code it checks.

**Fix.** Four changes, all made. (1) 0012 stands `VOID` on the record; the frozen reader is not
edited. (2) Preregistration 0013 re-reads the same banked artifact under a successor reader whose
only behavioural change is that one line (its diff against 0012's reader is five hunks, listed in
the preregistration), with every 0012 number quoted in the preregistration before its reader is
hashed into the chain and the outcome those numbers give — `RECIPE_FAILS` — committed to in
advance. (3) The mutation gate now builds its synthetic artifact with the runner's own rule for
second-stage record order, exercises the successor reader, and carries two standing cases: the
0012 reader voiding a runner-shaped artifact (kept failing, so the defect stays visible) and
ranked-order records voiding under the successor. (4) Standing rule, added to
`docs/OPERATING_RULES.md` §4: the control artifact of a reader's mutation gate is built from the
runner's output shape — a smoke run's structure or the runner's own ordering code — never from
the reader's expectations, and a reader is not frozen until its control case has been produced
that way.

---

## 2026-09-03 — The board review of the second quarter found nine distinct defects in the 2048 write-up and the quarter's documents

Five department reviewers and two board refuters per finding (`artifacts/verification/board_review_q2.json`:
36 raised, 29 confirmed by double refutation, 7 rejected; the 29 collapse to nine distinct defects
because several departments found the same one). Each is filed here at full size and fixed in the
same commit.

**1. A baseline misattributed.** `VERDICT.md` said the depth-16 tree reached 0.1103 at 1024. That
is the depth-8 tree; the depth-16 tree reached **0.1197** (`carve_generalisation.json`,
`within_trivial_baselines`), and the same document's 0007 section had both right. Fixed and
registered with `tools/freshness.py` (`verdict-2048-depth16-at-1024`).

**2. "A pass on csv and log masked by four incompressible families."** Two things wrong. Gutenberg is
prose, not an incompressible generator — three families are incompressible and gutenberg is the
fourth that fails. And "masked" was not supported: removing base64, binary and mixed leaves a
mixture that still misses the binding reading (**+0.0478** against the depth-16 tree; now banked as
`subsets.without_base64_binary_mixed` in `per_family_curves_2048.json`). Only the structured four as
a set clear both readings (**+0.0549**). README, VERDICT, the brief, the diligence map, the evidence
page and the coverage claim now say exactly that.

**3. "By 0.0025" as the headline.** The narrative, brief and one-pager quoted the slackest of three
failed within-size clauses as if it were the miss. The reading frozen as binding misses by
**0.0206** (`carve_margins_2048.json`, `distance_to_bar`), and transfer fails its margin at both
sizes rather than "collapsing to chance at both" (0.0455 at 2048 is above the null control). All
three documents now state every failed reading.

**4. Two sentences contradicted by their own numbers.** "Each halving of the window costs about the
same" sat beside 0.0504 and 0.0296; "the same ordering as at 4096" sat beside a list in which mixed
and base64 had swapped. Both rewritten to what the numbers show.

**5. An unbanked count.** "Two adversarial review rounds whose 60 findings…" traced to nothing but
commit messages. The two rounds are now banked in `artifacts/verification/prereg_0011_reviews.json`
(43 + 17 raw; 5 confirmed by double refutation; the rest adjudicated by hand when the subagent
quota expired) and the sentence cites it.

**6. The reader credited with a check the script performs.** VERDICT and the engineering log said
the frozen reader checks the corpus cache's build metadata; it checks the stamp the script writes
after the script has refused a mismatching cache. Reworded in both places.

**7. The training cost quoted without its environment.** The 2048 ladder ran under `nice` with
three BLAS threads after three container restarts, and the artifact banked `cpu_cores: 4` beside
it. `cost.train_environment` now records the conditions, and VERDICT and the milestone map say the
ladder is not comparable to 0007's; the milestone map's cost table gains the 2048 row, and its M3
extrapolation — which the measured run showed low by roughly half on both build and training — is
revised against three banked points.

**8. Licence statements.** The dataset card's content section and `tools/pivot/verify.sh` still
called the sources "public-domain", the sentence F1 found false for pg5200. The audit's Lingeling
finding answered a legal question in the repository's own favour ("which is evaluation and
research use") one paragraph after saying it makes no legal determination — the restriction in
`COPYING` is on *use* in a commercial context, and whether a company's banked reproduction run is
inside it is now COULD NOT VERIFY, in §5.3, in the consolidated list, and in README. A §5.1 grep
claim was false for the banked copy, and one §5.1 residual had been dropped from the consolidated
list; both fixed.

**9. Instrument and mirror.** The CI determinism probe had been passing with zero source bytes, so
the gutenberg family was silently synthetic in every CI run; it now refuses without sources and CI
fetches the pinned edition first. `fetch_sources.sh` could cache a 404 page as a source; it now
fails on HTTP errors. Coverage-map `reverify` commands for 0011 would have overwritten the banked
artifacts they verify — the class filed on 2026-09-02 for 0007 — and now point at the frozen reader
or at scratch paths with a diff. The public mirror's note said all four filtered GNSS files had
unverifiable terms when the audit resolved two of them, and said `chain.jsonl` carries a
`git_commit` it does not carry; the evidence page's provenance stamp named a commit at which the
artifacts it rendered did not exist. All reworded or fixed, and the mirror regenerated. One sealed
descriptor cannot be edited: `prereg/0011-carve-2048-boundary.json` `readings[corpus_b_chunk_offset].unit`
says "must be >= 75000" while the sealed bar and the frozen reader require exactly 75000..99999;
the bar governs, the reader enforces it, and this line is the record of the stale descriptor.

---

## 2026-09-02 — The same superseded interval, three more places: the 0003 headline bound in README and in VERDICT's summary and clause tables

**Claimed:** `README.md`: "a 95% interval of **[0.0485, 0.0497]**"; `VERDICT.md`, the results
summary table: "95% CI [0.0485, 0.0497]"; `VERDICT.md`, the `CURVE_ESTABLISHED` clause table:
"Slope 95% lower bound … 0.0485".

**Actual:** those are the fragment-level values the 2026-08-31 audit superseded. The banked
cluster-bootstrap interval in `artifacts/pivot/deflate_curve.json` is **[0.048216, 0.050014]**
(`slope_ci95_low`, `slope_ci95_high`), which the outbound brief, the one-pager and the evidence
page already quote. Found an hour after the previous entry, while wiring the mirror's README; the
previous entry's sweep covered the 1024 interval and missed the 4096 one it sat beside.

**Size:** three sentences; the lower bound moves from 0.0485 to 0.0482; the verdict clause is
unaffected.

**Cause:** the same as the entry above — superseded values stay banked, so the claim gate keeps
passing them — plus a sweep that searched for one number and not for the class.

**Fix:** all three now quote the six-decimal banked values with "cluster-corrected" beside them,
and all three are registered with `tools/freshness.py` (`readme-headline-interval`,
`verdict-summary-interval`, `verdict-clause-lower-bound`), so the next divergence fails a gate
instead of waiting to be noticed. A repository-wide search for every `*_superseded` value quoted
outside a sentence that labels it superseded was run and found no further instance.

---

## 2026-09-02 — A cold clone no longer rebuilds one of ten sources byte-identically; the claim was true on 2026-08-25 and silently false by 2026-09-02

**Claimed:** "the corpora themselves are not committed; a cold clone re-manufactures them and checks
the hashes" (`docs/strategy/MILESTONES.md`, the corpus-size table); "Corpora rebuild
deterministically from shipped sources and generators; the manifest banks content hashes of every
array so the rebuild is *proven* identical, not assumed" (`docs/DILIGENCE.md`, last section);
"the corpus manifest proves a rebuilt corpus byte-identical" (`outbound/NARRATIVE.md`).

**Actual:** On 2026-09-02 all ten Project Gutenberg sources were re-fetched from the exact URL
`tools/pivot/fetch_sources.sh` uses. Nine hash-matched the banked
`artifacts/pivot/corpus_manifest.json` (`sources_sha256`). **`pg1342.txt` did not**: gutenberg.org
now serves an edition differing in two lines — "young-man" has become "young man" and "Mr," has
become "Mr." — at the same byte length, sha256 `81300b79…` against the banked `a5666f87…`. A cold
clone run that day would have fetched the new edition, spent the corpus build (3415.5 banked seconds
at 4096) manufacturing gutenberg-family windows from slightly different bytes, and failed
`corpus_manifest.py --check` at the end, with no earlier signal. The banked measurements are
untouched — they were made on the banked bytes, which are on disk and hash-match — but the sentence
"a stranger can rebuild it byte-identically" was false for one file for some unknown part of the
eight days since the manifest was written, and nothing in the instrument would have said so until
an hour into a stranger's rebuild.

**Size:** one of ten source files; two lines of one novel; the whole of the reproducibility claim
for the gutenberg family, which is one eighth of every corpus.

**Cause:** the fetch script downloaded without checking against the manifest it exists to satisfy.
The manifest checks the *corpus*, at the end of an hour's build, not the *sources*, at the start.
And nobody re-fetched between 2026-08-25 and 2026-09-02, so the drift was found by a compliance
re-check, not by the reproducibility gate.

**Fix:** `tools/pivot/pin_sources.py`, run by `fetch_sources.sh` after every download: each source
must hash to the banked value; a later upstream edition recorded in `tools/pivot/source_pins.json`
is converted back to the banked bytes by its recorded line edits (both directions written
verbatim, and the script refuses to edit a line that is not the recorded upstream text); any other
edition is a hard exit 1 naming the file and this ledger. Exercised three ways before commit: banked
sources pass; today's upstream pg1342 is pinned back to `a5666f87…` byte-for-byte; a fabricated
unknown edition fails. **COULD NOT VERIFY** whether an archived copy of the banked pg1342 edition
exists (the Internet Archive is blocked by this container's egress policy); if gutenberg.org
changes pg1342 again in a way not recorded here, the rebuild will fail loudly, which is the
correct behaviour and will be filed here again.

---

## 2026-09-02 — Quoted the superseded 1024-carve slope bound after banking its replacement

**Claimed:** `VERDICT.md`, the `CARVE_FAILS` clause table and the "rising curve that is worthless"
paragraph: "Within-size slope 95% lower bound … 0.0198"; `outbound/ONE_PAGER.md`: "a lower bound
of **0.0198** excluding zero"; `artifacts/verification/coverage.json`, claim
`carve-rising-but-worthless`: "a 95% lower bound of 0.01975813023327274".

**Actual:** 0.0198 is the fragment-level bound the 2026-08-31 audit found anti-conservative. Its
replacement — the cluster-bootstrap bound over held-out source chunks, **0.019721**, which rounds
to **0.0197** — was banked the same day in `artifacts/pivot/carve_generalisation.json`
(`within_slope_ci95_low`) with the old value kept beside it as
`within_slope_ci95_low_fragment_level_superseded`. The three sentences kept quoting the
superseded one. The claim gate passed them because the superseded value is still banked — exactly
the "real but no longer current" class the freshness gate exists for, and none of the three
sentences was registered with it.

**Size:** one ten-thousandth of an accuracy point per decade, in three places; no clause changes.
The size is not the point. The point is that the audit's correction was banked and then not
propagated, by the same hands, on the same day.

**Cause:** the audit re-derivation wrote the corrected fields into the artifact and a paragraph
into VERDICT.md about the correction, but did not sweep the document for the old number. Found on
2026-09-02 by a pre-freeze review of preregistration 0011, which noticed that the coverage
claim's `reverify` command was also wrong: it named the default `run_carve.py` invocation, which
would *overwrite* the banked 0007 artifacts rather than re-derive the interval.

**Fix:** the three sentences now quote 0.0197 and say "cluster-corrected"; the coverage claim's
`reverify` names the frozen reader and the cluster re-derivation; `tools/scaling.py` now performs
the cluster bootstrap itself (`fit(groups=…)`) so future runs bank the corrected interval as the
primary one and the fragment-level one as superseded, in the script, not in a post-hoc patch.
Two more defects in the same correction, found by the second review pass and fixed the same day:
`audit_rederivations.json` banked the 0007 superseded interval's upper bound as `null` (now the
value from `carve_generalisation.json`), and the re-derivation had used 4000 bootstrap resamples
without recording it — verified today by reproducing both banked cluster intervals exactly at
4000 and not at the fitter's default 2000; the artifact now says so. The two seed-replication
artifacts, whose intervals are fragment-level, now carry a label saying so; no value changed.

---

## 2026-09-02 — Said "all fixed here" about six red-team findings; one of them was not

**Claimed:** commit `a42d0c7`, message: "RESEARCH QA (accepted): docs/qa/NEW_DOCS_REVIEW.md — six
verified findings against the post-audit documents, all fixed here."

**Actual:** Finding 2 of that review — `docs/DILIGENCE.md` saying "132 mutations across 13 gates"
against an artifact saying 134 — was not fixed. The commit did not touch `docs/DILIGENCE.md` at
all (`git show a42d0c7 -- docs/DILIGENCE.md` is empty). The wrong integer stood for two more days
in the section titled "Can my engineer verify any of this without trusting you?", until it was
found again on 2026-09-02 while a fourteenth gate was being added (the sentence now reads 153
across 14, and is registered). This is the stale-mutation-count error class filed three times on
2026-08-25 — and this time the review *found it*, the fix *was claimed*, and the fix was not made.

**Size:** one of six findings claimed fixed; one integer; in the verification section of the
diligence map.

**Cause:** the commit message's fix list was written from the review document, not from the diff.
A review is not a fix, and a message that says "fixed" without a hunk behind it is the same class
of claim this ledger exists for.

**Fix:** `docs/live_claims.json` now carries the DILIGENCE sentence (`diligence-mutations`) and the
EVIDENCE_BRIEF and NARRATIVE sentences that quote the same count, so `tools/freshness.py` fails on
the next divergence anywhere they appear. The instrument cannot check a commit message; that part
is a rule — name the hunk — and it is recorded here as a rule, not dressed as a gate.

---

## 2026-08-31 — An adversarial audit found 13 defects the instrument missed, three of them critical

Fifty-four independent review agents were run against this repository — six hostile lenses, every
finding then attacked by two refuters instructed to kill anything wrong, vague, or already
disclosed. Twenty-four findings were filed; **thirteen survived double refutation**. Every one was
real. They are listed at full size because the instrument this repository is built around checked
none of them: the gates verify that numbers trace, match, and stay current — not that the
*reasoning between the numbers* is sound.

**1. (critical) The bootstrap contradicted the split.** `tools/scaling.py` resampled 260000
evaluation fragments as independent. They are 10000 clusters of 26 fragments sharing a plaintext —
the *exact dependence unit the grouped split declares*. Measured within-chunk correctness
correlation: 0.140, against 0.016 across boundaries. Every published slope interval was
anti-conservative - the audit's on-the-spot estimate said roughly 45%, the corrected widths say
about half again as wide, and this ledger keeps both. Corrected by a cluster bootstrap over
chunks: 0003's interval
[0.0485, 0.0497] becomes **[0.0482, 0.0500]** (`artifacts/pivot/audit_rederivations.json`); the
verdict clause is unaffected; "pins the slope to about a thousandth" was false and is retracted.
The 0006 top-5 and 0007 intervals carry the same defect and are marked anti-conservative pending
re-derivation — their per-example scores were never banked, which is itself part of this defect.

**2. (critical) The grouped split promised something its mechanism does not provide.** For seven of
eight content families the chunk index determines the bytes. For gutenberg, every chunk is a
32768-byte window at a random offset into one shared 7.84 MB pool — ~26× coverage — so gutenberg
source bytes straddle train/eval, and "fragments carved from the same source bytes never straddle
the boundary", frozen into preregistration 0003 and repeated in three documents, is false for an
eighth of the corpus. The same pool-sharing voids the byte-level reading of 0007's
corpora-disjointness clause. Measured impact, from banked per-example scores: gutenberg is among
the *hardest* families (0.1596 vs 0.2511), excluding it raises every rung and steepens the slope to
+0.0524 [0.0514, 0.0535] — the defect ran against the headline, which is luck, not process. The
0007 reading strengthens: the transfer model had seen gutenberg-adjacent bytes and still collapsed
to chance.

**3. (critical) Subagent evidence relabelled "first-hand".** The three GitHub `total_count: 0`
queries supporting the G4 white-space claim lived in a round-1 subagent's artifact; the first-hand
re-run (`g4_firsthand.json`) never repeated the GitHub arm, and VERDICT.md attributed the zeros to
it anyway — the precise class of evidence this repository refuses to call verified, promoted by
sloppy citation. The queries have now been re-run genuinely first-hand through the authenticated
API: hard zero, all three, `incomplete_results: false` (`g4_github_firsthand.json`). The claim was
true; the provenance was not. The same sentence also said "four tools" where its artifact lists
five.

**4. (major) A not-before anchor cited as a not-after proof.** Both interpretation notes claimed
their drand anchor proved "no number existed at the time of recording". A beacon round proves only
that a file was written no *earlier* — nothing stops computing first and anchoring afterwards. The
notes' precedence rests on run logs and commit history, and both artifacts now say so in their own
text.

**5. (major) The closing section denied the headline.** "It contains no scaling curve that means
anything" survived three sweeps of the stale-claim bug class this repository built a gate for —
because the freshness gate guards registered numbers, and this was prose. The repository banks four
fitted curves; the closing bullet described one.

**6–8. (major/minor) Numbers misattributed or contradictory in prose.** 22.27 — the all-family mean
distinct-stream rate — was attributed to base64/binary content, which actually collapses to ~14.7,
inside the section titled "what is weak about it"; an error in the flattering direction. "Two"
load-bearing measurements re-derived in one paragraph, "three of the four" thirteen lines later.
L4's scope note still said no learned representation had been tested after 0009 and 0010 had run.

**9–12. (major/minor) L4's evidence was overstated three ways.** Its lead bullet called six
overlapping subsets "families" (four of the seven disjoint families were never measured alone, and
part of the ratio uniformity is mechanical column-sharing); it quoted a diagnostic whose own
artifact says "not quotable as a result" without carrying that label; and a law "derived by
measurement" leaned on that diagnostic for its lead evidence. L4 now leads with its two
preregistered halves (transfer collapse, ceiling stability) and quotes the diagnostic with its
label attached.

**What was fixed, what was not, and what this says about the instrument.** All thirteen are
corrected in place; the two derivations are banked; the G4 gap was closed by measurement rather
than by weakening the claim. Not fixed: the 0006/0007 intervals await re-derivation with banked
per-example scores. The meta-finding is the uncomfortable one: **every gate passed while all
thirteen defects were live.** The gates check mechanical honesty. Reasoning between numbers — a
bootstrap contradicting a split, an anchor cited backwards, a guarantee whose mechanism covers
seven families of eight — has no gate, and the only check that caught any of it was adversarial
review by agents instructed to kill the package. That check is now part of the record, and its
eleven *rejected* findings are retained alongside the thirteen confirmed, so the filter itself can
be audited.

## 2026-08-26 — Published a reading of our own null control that does not follow, and it understated our own result

**What was published.** The 0009 write-up, in `VERDICT.md` and as a coverage claim, read the null
control this way:

> The shuffled-label loss never moves from chance at all — **0.0006** across ten epochs. That is a
> clean null control, and it simultaneously says this architecture cannot memorise 100000 random
> labels. A model with no capacity to overfit may simply be too small, so part of "it failed" is
> "it was small".

**Why it does not follow.** A probe holding everything fixed except the final pooling layer:

| head | train accuracy on 5000 **shuffled** labels, 30 epochs |
|---|---:|
| global average pool — what 0009 used | 0.0486, against 0.0385 chance |
| flatten — position preserved | **0.364**, and still climbing steeply from 0.056 at epoch 20 |

Convolutional capacity is identical in both arms. The network could not memorise because a global
average pool **averages away per-example identity** — two fragments with the same local statistics
become the same vector, at any parameter count. It was not a shortage of capacity, and "it was
small" is not a supported reading of that number.

**Size.** One inferential step, in a caveat rather than a headline. But it is the caveat attached to
a *negative result*, and it is the sentence a reader would use to decide how much the negative is
worth — so it is load-bearing in the way caveats often are.

**Direction, and why it is worth naming.** This error ran **against us**: it manufactured a
weakness in our own finding that the evidence did not support, making the 0009 negative sound
flimsier than it was. Nearly every other entry in this ledger corrects an error that flattered us.
An unforced hedge is a smaller sin than an unforced boast, but it is the same failure — a statement
that the measurement did not license — and filing only the flattering ones would make this ledger a
performance rather than a record.

**What replaces it.** A narrower and better-supported caveat: 0009 tested one architecture whose
final pooling is a strong inductive bias, and whether that bias hurts the *task* is untested. Local
byte order may be exactly the right signal and position may be irrelevant, in which case the pool is
sensible and the negative stands cleanly.

**The generalisable lesson, which this repository should have reached on its own.** A null control
that the model **cannot fail** carries no information. `tests/mutation_test.py` exists because a gate
that cannot fail is decoration — and a control that cannot fail is decoration for exactly the same
reason. That argument was already written down here, applied to gates, and nobody applied it to
controls. Preregistration 0010 therefore adds a clause requiring a model to *demonstrate* it can
memorise shuffled labels before its null control is credited.

## 2026-08-25 — Broke CI with a stale mutation count for the THIRD time, after building the gate that catches it

**What happened.** I added 15 mutation tests for preregistration 0007's gate, took the suite from
81 to 96, and committed without updating the three places that carry that count: the
`mutations-detected` claim in `coverage.json`, the row in `VERDICT.md`, and the line in
`outbound/ONE_PAGER.md`. CI went red on `raj200501/raise-v1#1`.

**Why this one is worse than the first two.** The instrument caught it. `tests/mutation_test.py`
has carried a guard for exactly this since the first occurrence, and it printed exactly what it was
designed to print:

```
!! artifacts/verification/coverage.json claims 81 mutations, this run has 96.
!! Update the 'mutations-detected' claim or tools/coverage.py will fail and CI will go red.
```

**I did not see it, because I piped that command through
`grep -E "carve |MUTATION REPORT"` to keep the output short.** The filter I chose to read the
result with dropped the warning the result came with. Then I committed without running the gate
suite, because I had run *the tests* and treated that as the same thing.

So this is not a third instance of forgetting a number. It is the first instance of **defeating my
own instrument for convenience** — the warning existed, fired correctly, and was discarded by the
reader rather than missed by the writer.

**Size.** One CI cycle on an open pull request, and no published number was wrong for longer than
it took to notice — the gates that failed are the ones that stopped it reaching anyone. Against
that: the third occurrence of one bug class, with the second occurrence's fix in place and working.
A guard that a hurried reader can filter out of view is not a guard, and I am the hurried reader it
has to survive.

**Fix, in two parts.**

1. **The warning is now an exit code.** `tests/mutation_test.py` returns 1 when the banked claim
   disagrees with the run. An exit code cannot be grepped away. Verified by temporarily setting the
   claim to a wrong value and confirming the suite fails, rather than by assuming it would.

2. **`tools/gates.sh` runs every gate in one command**, in the order CI runs them, and CI now
   invokes that same script instead of listing the steps separately — so local and CI cannot drift
   apart, and "I ran the tests" stops being a different act from "I ran the gates".

   The script distinguishes a **pending** reader from a broken one: a frozen reader whose artifact
   does not exist yet exits 2, which is the normal state between freezing a preregistration and
   measuring it, and it is reported by name rather than treated as a failure. That leniency is safe
   only because a deleted result artifact is still caught elsewhere — every banked result is cited
   by a claim in the coverage map, and `coverage.py` fails on a claim whose artifact is missing.

**What it does not fix.** `gates.sh` has to actually be run. Nothing in this repository forces it
before a commit, and a pre-commit hook would live outside the committed tree where CI cannot see
it. The honest statement is that the guard now fails loudly in two places instead of one, and that
the remaining failure mode is a person skipping the command — which is what happened here.

## 2026-08-25 — Published three stale numbers in `VERDICT.md`, and the outbound gate passed all three

**What was published.** Three numbers in `VERDICT.md` describing the current state of the
instrument had stopped being true and kept being published:

| Row | Published | Actual at the time it was read |
|---|---|---|
| Preregistration chain | `1 entry, head cfcc915c…` | 5 entries, head `8ebe55a5…` |
| Weakest coverage row | `9 of 32 claims are in neither` | 9 of 36 |
| Coverage table | `primary-verifiable  17` | 21 |

All three were true when written. None was true when found. The chain row is the worst of them:
it is the row a reader would check *first* to decide whether anything else in the document can be
trusted, and it understated the instrument's own record by four preregistrations.

**Why the gate passed them.** `tools/claimcheck.py` asks: does this number appear in a banked
artifact at the precision written? For a fabricated number that is the right question. For a stale
one it is the wrong question, and the gate cannot be tuned into asking the right one — the old
value stays banked forever, so it keeps passing on its own merits. `cfcc915c` really is the hash
of chain entry 1. `17` really was the count. The gate was working exactly as specified and the
specification had a hole in it.

**Size.** Three numbers, in the document that exists to be the honest summary, one of them the
integrity claim about the preregistration chain itself. Against that: the direction is
*self-deprecating* in all three cases — fewer preregistrations, fewer primary-verifiable claims,
a smaller denominator on the weakest row. Nothing here flattered the work. That is luck rather
than process, and it is not a mitigation: a mechanism that lets stale numbers through lets
flattering ones through equally.

**This is the second instance of the same bug.** The first is the entry above, dated the same day:
the mutation count in `coverage.json` said 49 while the suite ran 58, CI went red for about an
hour, and the principal caught it before this repository did. That was patched with a one-off
guard inside `tests/mutation_test.py` comparing the two numbers. A one-off guard for one number
is not a fix for a class of bug, and writing a second one-off would have been the wrong response
to being shown the same failure twice.

**Fix.** `tools/freshness.py`, a gate that re-derives each live number from its artifact and fails
on divergence, driven by a data registry (`docs/live_claims.json`) so adding a claim needs no code
change. It is wired into CI and `tools/pivot/verify.sh`. On its first run against the unmodified
repository it failed, naming all three stale numbers — the failure above is the gate's own control
case, not a hypothetical.

Two design choices worth stating, because both could have been made the comfortable way:

- A registry pattern that **no longer matches** its document is a FAILURE, not a skip. Otherwise
  any claim escapes the gate by being reworded. This is the case that caught the chain row: the
  document said "1 entry" where the pattern wanted "entries".
- A **missing artifact** is a failure, not a skip. Absence is never a pass, the same rule the
  frozen readers already apply.

Nine mutation tests cover it, including the one that states the point: a stale count that
`claimcheck` still passes must make `freshness` fail. The suite is now 67 mutations across 8
gates, 67 detected, 0 survived.

**What it does not fix.** Only numbers entered in the registry are checked; a live number nobody
registers is still unguarded. The registry is a judgement call about which numbers describe the
present rather than a past measurement, and that judgement is not itself mechanised. A 2026-08-25
accuracy is *supposed* to stay what it was, so it must stay out of the registry — and the boundary
between those two kinds of number is drawn by hand.

## 2026-08-25 — Published a mutation count that did not match the repository, and broke CI for an hour

**Claimed.** `VERDICT.md`, `README.md` and `outbound/ONE_PAGER.md` all stated "38 mutations, 38
detected, 0 survived".

**Actual.** 49. Eleven mutation cases for the pivot reader were added and committed without
updating the claim, so for roughly an hour the published figure understated the instrument by
eleven cases and **GitHub Actions was red on every push in that window**.

**Size.** Small in the number, and it errs *against* our own interest — understating how many ways
the gates were shown to fail makes the instrument look weaker, not stronger. What is not small is
the process failure behind it.

**Cause.** The mutation tests were added, run, and committed — but `tools/coverage.py` was not run
before committing. Locally the gates are only green if you actually run all of them, and I ran the
one I had just changed. The stale claim then surfaced one gate later, in CI, where I was not
looking. **The user noticed the red CI before I did**, which is the part worth recording: an
unwatched gate is not a gate.

**Fix.** Two changes. (1) `tests/mutation_test.py` now compares its own case count against the
`mutations-detected` claim in the coverage map and prints a loud warning at the moment they
diverge, so the mismatch surfaces where it is created rather than one gate downstream.
`tools/coverage.py` remains the enforcing gate. (2) All four documents now read 49, from the
banked artifact.

## 2026-08-25 — Called the round-3 finding "a usable specification"; it is not white space

**Claimed.** In `VERDICT.md`: *"The class that would work: a high-bandwidth physical recording that
is the causal consequence of the hidden variable, published in bulk for a reason unrelated to the
label. … That is a usable specification for a fourth round, and it is the most valuable thing the
search produced."* Amplified in `outbound/ONE_PAGER.md` as *"That is a usable specification, not a
consolation."*

**Actual.** Round 4 checked that class first-hand and found it **occupied wherever it was probed**.
Five instances, five crowded:

| Instance in the class | What is already there |
|---|---|
| chess clock traces → rating | *Chess Rating Estimation from Moves and Clock Times Using a CNN-LSTM* (arXiv 2409.11506, Springer 2025) — the proposal itself, and it reports that clock usage carries skill information board-only models cannot recover. Plus RatingNet, *Predicting Chess Player Rating Based on a Single Game* (2023), ChessMimic (2026). |
| GNSS SNR → antenna / signal condition | An established multipath and NLOS classification literature, 2021–2025. |
| hydrophone recordings + AIS → ship | *Automated data curation for self-supervised learning in underwater acoustic analysis* (arXiv 2505.20066) pairs AIS with bulk passive-acoustic recordings to pseudo-label a large unlabelled corpus for SSL — **the FDM-1 structure itself, already built**. Plus Oceanship (arXiv 2401.02099). |
| LIGO strain → detector data quality | `iDQ`, a supervised learner on thousands of auxiliary channels, **in production across four observing runs**, with a 2024 performance paper. Plus Gravity Spy. |
| open radio archives → signal state | Adjacent to RF modulation classification, already on the pre-existing kill list. |

A general search confirms the shape: pseudo-labelling a large unlabelled sensor archive from weak or
independent supervision is a **named, surveyed methodology** across sensing disciplines —
pseudo-labeling, self-training, weak supervision — with its own review literature.

**Size.** This retracts the single most positive-sounding output of the entire project. It was the
one forward-looking sentence in a document that is otherwise a negative result, it was the line the
outbound one-pager led its closing section with, and it is now withdrawn as written.

**Precisely what survives and what does not.** What survives: the round-3 observation that the
99-candidate pool contained **zero instances of the class**. That is still true and still
interesting. What does not survive: the inference that the class is therefore **open**. Membership
in the class is not evidence of white space — the class is where every sensing discipline already
works. Five probes is not proof that every instance is occupied, and the corrected claim is the
narrower one: *the class is not white space by default, and every instance must be crowding-checked
individually.*

**Cause.** A finding about the *absence of something in our pool* was written up as a finding about
*the presence of an opportunity in the world*. Those are different claims and the evidence only
supported the first. It read well, it was the only encouraging thing in the document, and it was
not checked before being published — including into outbound copy. That combination is exactly how
an over-claim survives review.

**Fix.** Both documents now state the narrower claim and carry the five probes. Added to
`docs/OPERATING_RULES.md` §6: **a finding that something is absent from our sample is never written
as a finding that it is available in the world without a separate check** — and where the two get
conflated, the conflation is the error, not the wording.

## 2026-08-25 — Published a scaling-rate figure that our own reproduction does not reproduce

**Claimed.** In `docs/_domain_selection_analysis.md`, under law L3(i): *"a learned model on 27 joint
features scores **0.2384** at 13,500 rows, rising **+2.8 accuracy points per decade**. Closing that
gap needs roughly 27 more decades of data."* Repeated in `VERDICT.md` as *"climbs only a couple of
accuracy points per decade"*. Both were taken from a subagent's measurement and stated as fact.

**Actual.** Re-derived here from scratch with six real CDCL solvers via PySAT
(`tools/repro/sat_solver_identity.py`, banked in `artifacts/verification/repro_sat_comparison.json`),
at the same top rung of 13,500 training rows: the learned model reaches **0.1800**, not 0.2384; the
slope is **+1.21** accuracy points per decade, not +2.8; and the gap closes in **66.6** decades, not
27. Three other figures from the same subagent *did* reproduce — determinism exactly (1530 of 1530
re-solves returning the byte-identical model), the free decoder closely (0.9857 against 0.9863), and
the divergence result more strongly (all six solvers agreed on 0 of 3,000 instances against 0 of 339).

**Size.** One of three headline numbers in one of the three laws that close Phase 0, wrong by more
than a factor of two on the slope and by a factor of 2.5 on the decades. The qualitative claim — a
free zero-training decoder near 0.986 against a learned model near the 0.1667 chance level, with a
gap no realistic quantity of data closes — survives intact and is if anything strengthened.

**Cause, and the part that matters.** The error runs in the direction that *flatters our own
conclusion*: a weaker learned arm makes law L3(i) look stronger. That is precisely why it cannot be
quietly corrected by adopting the better-looking number. The most likely explanation is **not** that
the subagent was wrong but that **the feature set implemented here is worse than the one it used** —
both of our runs sit barely above chance, which is what an underpowered feature set looks like. The
subagent's code lived in an ephemeral scratch directory and is gone, so the two implementations
cannot be diffed and the cause cannot be established. Underlying all of it: a number measured by a
subagent, in a directory that no longer exists, was written into a published document as though it
were established.

**Fix.** Three changes, all made. (1) Neither figure is quoted as established anywhere. The documents
now state the qualitative claim, cite the reproduced numbers as reproduced, and record the subagent's
as not reproduced. (2) The reproduction ships as runnable code and both runs are banked, including
the first run that could **not** reach the top rung — kept so the run that did cannot be mistaken for
the only one. (3) `artifacts/verification/coverage.json` now carries an explicit `neither` row for
the subagent's SAT figures whose stated reason is that this repository tried to reproduce them and
could not.

## 2026-08-25 — Miscounted the ACS PUMS allocation-flag columns, and blamed a subagent for it

**Claimed.** In `artifacts/phase0/reproduction_alloctrace.json`, first version, under
`discrepancies`: the round-2 reviewing agent reported "77 contiguous allocation flags" in the
2023 ACS PUMS person file; this repository recorded "76 columns match the filter
`startswith('F') and endswith('P')`" and assessed the gap as "a naming-filter difference, not a
substantive disagreement", listing it as a discrepancy in an artifact whose stated purpose was
checking the agent's work.

**Actual.** There are exactly **77** allocation flags, and the agent's count was right. The
person file has 80 columns beginning with `F`; three of them — `FER` (gave birth in the past 12
months), `FOD1P` and `FOD2P` (recoded field of degree) — are substantive data variables that
merely start with `F`. Three genuine flags end in `C` rather than `P` (`FHINS3C`, `FHINS4C`,
`FHINS5C`), which is why the filter used here does not return 77. The full column list is in the
banked artifact and can be recounted by anyone.

**Size.** One column in an absolute count (76 vs 77, 1.3% of the count). Substantively larger
than that: the entry appeared in a verification artifact, under a heading that reads as "what
the agent got wrong", and it recorded a defect in this repository's own check as though it were
a defect in the thing being checked. The direction of the error is the part that matters. An
independent-verification artifact that manufactures a discrepancy is worse than one that finds
none, because its whole value is that its findings can be trusted in both directions.

**Cause.** A regex-shaped assumption — that PUMS allocation flags are exactly the columns
matching `F*P` — was written into a one-off check and never tested against the data dictionary,
then reported as a measurement. It is the same failure this repository has spent two rounds
killing in other people's candidates: a heuristic mistaken for ground truth. It was caught only
because the raw column list was printed alongside the count, which is luck, not process.

**Fix.** Two changes, both made. (1) The artifact now records 77 with its derivation stated
explicitly, so the count can be checked without rerunning anything. (2) The standing rule, now
in `docs/OPERATING_RULES.md` §8: a count derived from a *pattern over names* is not a
measurement until the pattern has been checked against the authoritative definition, and any
artifact reporting such a count must print the derivation beside it. Where a check disagrees
with the thing it is checking, the check is assumed wrong until it is shown otherwise.
