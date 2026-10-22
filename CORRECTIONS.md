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

## 2026-10-22 — Published 0022's, 0023's and 0024's real-file readings in words their readers did not emit: a recipe and a rule that are "the same rule", a scaling thesis that "holds on real files", and a model that "still leads" a "hand-writable" rule

**Claimed:**

- **0022.** "Searched on real content, the best boosted recipe and the best linear rule are the same rule." (`outbound/ONE_PAGER.md`). The same reading appears in four more places:
  - "**Searched on real content, the boosted recipe and the linear rule are the same rule.**" (`outbound/EVIDENCE_BRIEF.md`, a bold lead);
  - "On real content a searched boosted model and a searched linear rule are the same rule." (`README.md`);
  - "On real content, a searched boosted model and a searched linear rule are the same rule." (`VERDICT.md`);
  - "On real content the boosted model and the linear rule are the same rule, and we said in advance the run would probably say so." (`outbound/NARRATIVE.md`).

  The evidence page's 0022 panel says "Searched on real files, the boosted recipe and the linear rule are the same rule" (`tools/render/evidence_page.py`). `VERDICT.md`'s 0022 "What it means" says "a rule a person could write by hand — now a searched linear one — gets essentially all of it".
- **0023, the thesis.** "The budget excuse is answered on this content: the record's scaling thesis holds on real files, and what grows fastest with real data is the hand-writable rule." (`outbound/EVIDENCE_BRIEF.md`). The same claim appears in three more places:
  - "What it means: the record's scaling thesis holds on real files, and what grows fastest with real data is the hand-writable rule." (`docs/DILIGENCE.md`);
  - "so the record's scaling thesis holds on real files" (`VERDICT.md`);
  - "and what grows fastest is the hand-writable rule." (`README.md`).

  `VERDICT.md`'s 0023 section opens "— and the hand-writable linear rule rises faster."
- **0023, the reverse curve.** "On the builder's own evaluation set the model's curve is flat (0.000222): more real plaintexts do not move a reading on content the model was not fitted on." (`docs/DILIGENCE.md`). `VERDICT.md` has "more real plaintexts do not move the reading on content the model was not fitted on — 0018's transfer finding from the other side." The pass did not list this sentence. The same commits changed it, so it is filed here.
- **0024, the lead.** "The second decade of real plaintexts rises — and the boosted model still leads the hand-writable linear rule at the top rung." It appears:
  - in `outbound/ONE_PAGER.md`;
  - in bold in `outbound/EVIDENCE_BRIEF.md`;
  - as the lead sentence of `VERDICT.md`'s 0024 section.

  The same clause follows the verdict string `SECOND_DECADE_RISES_MODEL_LEADS` in three more places: `README.md`'s headline, the brief's summary bullet and `VERDICT.md`'s Passed table. `VERDICT.md` also has the heading "**The boosted model still leads the hand-writable linear rule at the top rung.**" `docs/DILIGENCE.md` answers "**Yes — and the boosted model still leads the linear rule**". The evidence page's `_lead_sentence` renders "the boosted model still leads the hand-writable linear rule", and so would its 0025 panel's `_lead_sentence3` (`tools/render/evidence_page.py`).
- **0024, the meaning.** "Other files of the same kinds keep buying the recipe the record's rate on the files it is scored on, through 8232 plaintexts (eight times 0021's), so the budget excuse is answered a second time on real content, this time with other files; at eight times 0021's plaintexts the boosted recipe still leads a rule a person can write out on the record's own real content, by 0.0039". It appears in five files: `outbound/NARRATIVE.md`, `README.md`, `VERDICT.md` (after "**What it means.**"), `docs/DILIGENCE.md` (after "What it means:", in lower case) and `outbound/EVIDENCE_BRIEF.md` (in its 0024 paragraph). Its second half stands alone in `outbound/ONE_PAGER.md`.

All of this was first published on 2026-09-17: c855ede for 0022, 216fd60 for 0023 and cad24ab for 0024, whose preregistration's question wording dates from its pre-freeze commit a50a2e9 the same day. The exception is the 0025 panel's `_lead_sentence3`, written on 2026-09-23 (1b46b41) in a guarded panel that has never rendered, because 0025 has not run.

**Actual:**

- **0022** (`artifacts/pivot/realsearch_4096_verdict.json`):
  - The selected model is a boosted tree (`flags.fit_info_by_family.model` "hgb") at 0.1189. The selected logistic reads 0.1182.
  - The searched margin is 0.0007, at 0021's budget of 26346 rows from 1029 plaintexts.
  - The selected logistic (L5) is a 26-class linear model over 1108 features (`realsearch_4096.json`, `n_features`).
  - 0022 banks no paired interval on the difference. Its informational per-model intervals overlap: [0.1159, 0.1218] for the model and [0.1152, 0.1211] for the logistic (`realsearch_4096.json`, `cluster_ci95_informational`).

  These are two model classes 0.0007 apart, not one rule.
- **0023** (`realcurve_4096_verdict.json`):
  - `REAL_CURVE_RISES` is a pass of the slope clause and of nothing else: the model's 0.007344 per doubling (scored-chunk interval [0.006199, 0.00846]) against 0.005.
  - The span is 2.984659 doublings. 0023's preregistration puts that at 0.8985 of a decade and says "It cannot reach 0003's two-decade scope rule and says so."
  - Its reader reads the pass as "a rise to 0021's failing reading, never 'more real data fixes the model'": 0.1193 against 0.1429 needed.
  - `informational_only` calls the run "an in-distribution reading on real content whose top rung fails the record's margin".
  - What grows fastest over those four rungs is the standardised logistic, at 0.009551 per doubling. Model minus logistic is -0.002207 (paired interval [-0.003707, -0.000752]).
  - In 0024's second decade the difference is not resolved: 0.00059, [-0.00102, 0.00231].
- **0023's reverse curve.** The same `informational_only` puts "the reverse curves on the builder's evaluation set" among the readings that are "not a verdict, not quotable as a pass". The readings on that set:
  - Over 0023's rungs the model's reading moved 0.000222 per doubling and the depth-3 tree's 0.009842 (`curves.*.builder_eval_slope_per_doubling`).
  - Over 0024's second decade the model's moved 0.00231 (`realcurve2_4096_verdict.json`, `flags.builder_eval_slope_per_doubling_second_decade`).
  - On the extension corpus's synthetic families the model went from 0.0693 at rung 4 to 0.0987 at rung 7 (`ext_subsets`).

  One informational slope over one decade was published as a general statement.
- **0024, the lead** (`realcurve2_4096_verdict.json`):
  - `MODEL_LEADS` at the top rung stands: 0.0039, paired interval [0.0001, 0.0077]. The reader's `meaning` says the intervals are "over the scored chunks only and do not resample the fit side".
  - "Still" does not stand. `flags.model_leads_logistic_at_every_rung` is false.
  - At rung 4 the lead is 0.0014, [-0.002303, 0.0047], `NO_SEPARATION`.
  - At rungs 5 and 6 the model reads below the logistic: 0.1236 against 0.1241, and 0.13 against 0.1321.
  - Over both decades the logistic rose faster (`both_decades_slope_per_doubling` 0.008166 against 0.006645).
- **0024, the rule.**
  - The model leads a standardised logistic regression over 1108 features (`realcurve2_4096.json`, `corpus.n_features`) and 26 classes.
  - The record's own rule "a person could write by hand" is 0021's depth-3 tree (`outbound/ONE_PAGER.md`: "a margin of 0.0264 over a rule a person could write by hand").
  - `prereg_interpretation.json` says even a depth-16 tree "is not a rule a person writes by hand".
- **0024's sealed text.**
  - "The record's rate" is defined only inside 0024's preregistration, as 0.005 per doubling, "never 0023's measured 0.007344".
  - The same preregistration seals that "the second-minus-first-decade slope is quoted in the same sentence as any pass". For the model that slope is -0.000374 (`flags.second_minus_first_decade_slope`), and no published document quoted it.
  - The top rung against 0021's bar re-applied: 0.1404 against 0.1419 needed with the tree as floor, and 0.1865 needed with the higher of tree and logistic as floor. The tree-floor flag is informational and "can only be optimistic". Only `docs/DILIGENCE.md`, `VERDICT.md`'s 0024 section and the evidence page stated either reading.

**Size:** No banked number moves, and every verdict string stands. What moved is what the sentences say about the numbers, in every document that publishes 0022 to 0024. Four of the errors flatter us:

- a lead read at one rung was published as continuous;
- a 26-class linear model over 1108 features was published as a rule a person writes;
- a slope-clause pass over 0.8985 of a decade was published as the record's scaling thesis holding;
- one informational slope was published as a general statement about content the model was not fitted on.

"The same rule" was wrong in kind: it called two model classes one rule. They differ by 0.0007, a difference 0022 does not resolve, so the direction of this error is not established. Every publication of 0024's pass also broke one of 0024's own sealed publication rules.

**Cause:** The published sentences took the preregistrations' question words as the answers' words.

- 0024's title asks "does the boosted model keep its lead over a hand-writable linear rule". Its sealed text says "a rule a person can write out" and "the record's rate". Those phrases were sealed to frame a question. `docs/OPERATING_RULES.md` §3 says frozen text is no licence for a flattering reading.
- The verdict suffix `MODEL_LEADS` reads one rung. The prose added "still".
- 0023's "What it means" was written in the voice of the pass, not in the voice of the reader's `meaning`, which bounds it. Its informational reverse curve was written up as a finding.
- No gate compares a published reading with its reader's `meaning`, and no draft was checked against 0024's sealed same-sentence rule.

**Fix:** The applied commits rewrote these sentences in place:

- **0022.**
  - `README.md` (aabcdb3) and `VERDICT.md` (8ebd2d4) say that at this budget the two "score 0.0007 apart".
  - The one-pager (b3ff1bf) says they "finish 0.0007 apart" at 0021's budget.
  - NARRATIVE (8ebd2d4) says "at 1029 plaintexts, the searched boosted model and the searched linear rule score 0.0007 apart, and we said in advance the run would probably fail".
  - The brief's bold lead and the evidence page's 0022 panel were in no item and were not changed. Both still say "the same rule" at HEAD f275303.
- **0023.**
  - The brief (6d1f5d9) says the excuse is answered "in distribution and over 0.8985 of a decade (short of 0003's two-decade scope rule)". It says more real plaintexts raise the model's reading "faster than the 0.005-per-doubling bar, to a reading that still fails the record's margin", and that the standardised logistic grows fastest.
  - `VERDICT.md` (8ebd2d4) and `docs/DILIGENCE.md` (938e0c7) keep "the record's scaling thesis holds". VERDICT.md scopes it to "these real files" and DILIGENCE.md to "these five files". Both add "in distribution, over just under a decade (0003's scope rule asks for two)" and a rise "to a reading that fails the record's margin".
  - "Hand-writable" became "linear" in `README.md` and "standardised linear" in `VERDICT.md` and `docs/DILIGENCE.md`.
- **The reverse curve.**
  - `docs/DILIGENCE.md` (938e0c7) now says readings on content the model was not fitted on "have moved readings little, not uniformly, and none of these readings is a verdict". It gives 0.000222, 0.009842, 0.00231 and the synthetic families' 0.0693 to 0.0987.
  - `VERDICT.md` (8ebd2d4) says the curve is "nearly flat over this decade", "an informational reading, not a verdict and not a general law".
  - **A new error in DILIGENCE.md's replacement.** "Moved readings little" holds only for the model on the builder's evaluation set (0.000222 and 0.00231 per doubling). Two of the other readings in the same sentence rose faster. The depth-3 tree's 0.009842 per doubling is above the 0.005 bar and above the model's own real-family 0.007344. On the synthetic families the model went from 0.0693 to 0.0987 over the second decade, a larger rise than its real-family reading made over the same rungs (0.1193 to 0.1404). It was fixed in d778549: the sentence now says readings on unseen content moved unevenly and names which moved little and which rose.
- **0024's lead.** No document now says "still leads the hand-writable linear rule".
  - `README.md`, `VERDICT.md` (lead, heading, Passed table) and the brief (bold lead, summary bullet) say that at the top rung the boosted model leads the standardised logistic by 0.0039.
  - README.md, VERDICT.md and the brief add that the model trailed at rungs 5 and 6. The one-pager says the model "edges ahead of the standardised linear rule, after reading below it at the two rungs before".
  - `docs/DILIGENCE.md` answers "**Yes — and at the top rung the boosted model leads the linear rule, by 0.0039**".
  - On the evidence page (388d0f1), `_lead_sentence` and `_lead_sentence3` read "leads the standardised logistic (a 26-class linear model over 1108 features, not a rule written by hand)". The 0024 panel now lists the rungs where the model read below the logistic, and says every interval is over the scored chunks only.
- **0024's meaning.**
  - "A rule a person can write out" became "the standardised logistic". README.md, VERDICT.md and DILIGENCE.md add "26 classes over 1108 features". NARRATIVE adds "a 26-class linear model over 1108 features, not a rule anyone writes out by hand".
  - "The record's rate" is now spelled out as the 0.005-per-doubling bar in six places: README.md, VERDICT.md, DILIGENCE.md, the brief, NARRATIVE and the evidence page. `README.md` keeps the words "keep buying the recipe the record's rate" and puts the definition after them.
  - The top rung against 0021's bar re-applied (0.1404 against 0.1419) now stands beside the lead in README.md, the one-pager, the brief and NARRATIVE. 8ebd2d4 also put it in VERDICT.md's 0024 meaning sentence and closing section. VERDICT.md's 0024 section, DILIGENCE.md and the evidence page already had it. The brief also gives 0.1865.
- **Done later the same day (d778549).**
  - 0024's same-sentence rule: every sentence stating 0024's pass in README.md, VERDICT.md, DILIGENCE.md, NARRATIVE, the one-pager, the brief and the evidence page now carries "second decade minus first: -0.000374"; VERDICT.md's section heading is left as two scripts anchor on it, and the sentence after it carries the value.
  - "The record's scaling thesis holds" is withdrawn in VERDICT.md and DILIGENCE.md: the reading rises faster than the bar over 0.8985 of a decade, which does not establish the thesis 0003's scope rule ties to two decades.
  - VERDICT.md's 0022 "a rule a person could write by hand" now reads "the standardised linear rule (a 26-class linear model over 1108 features), now searched".
  - `tools/publish/publish_0025.py`: f275303 re-anchored its patterns on the rewritten wording, and the text it would publish itself is rewritten to the record's corrected wording (its lead sentences no longer say "still", "hand-writable" or "a rule a person can write out"; 6f05429); strings that quote the 0025 reader's sealed sentences verbatim are left as the reader words them.

Nothing mechanical checks that a published reading says what its reader's `meaning` says. That is recorded here as a rule, not dressed as a gate: quote the reader, not the preregistration's question.


## 2026-10-22 — Outbound copy called the headline "one real curve", "a claim about the world" and "structured content" without saying that seven of its eight content families are our own generators, and kept calling it the one real curve after a real-file curve existed

**Claimed:**

- `outbound/NARRATIVE.md`:
  - "I'll tell you the ending first: we have one real, preregistered scaling curve, and **no buyer yet**."
  - "The pivot found one real curve: recover which of 26 DEFLATE encoder configurations produced a fragment carved from the middle of a compressed stream"
  - "The pivot produced one result that is a claim about the world."
  - "structured content — csv, log, json — rises at roughly +0.09 per decade, about ten times chance at the top rung"
  - "One real curve with its boundaries measured by the same instrument."
  - In the crib: "In structured content — csv, log and json rise at roughly +0.09 per decade at about ten times chance —"
- `outbound/EVIDENCE_BRIEF.md`:
  - "on **structured content the curve rises at roughly +0.09 per decade** — nearly double the headline — with top-rung accuracy about **ten times chance**";
  - "The verdict is the mixture's; the rows are what a buyer with csv or log carves would need to see."
- The evidence page (`tools/render/evidence_page.py`): "Quality against the volume of manufactured labels — the FDM-1 question." and "structured content carries the curve at roughly twice the headline rate".
- `docs/DILIGENCE.md`: "~+0.09/decade on structured content (csv, log, json) at ten times chance".
- `VERDICT.md`:
  - "The first curve in this repository that is a claim about the world rather than a test of the instrument.";
  - "Structured content carries the curve";
  - "the per-family rows are what a buyer whose carves are csv or log would need to see."
- By omission, in two documents:
  - `outbound/ONE_PAGER.md`: "The label factory is free and unbounded: compress any bytes under every configuration and the label *is* the configuration you used." The page calls its numbers "a statement about the corpus builder's eight content families" and never says what the builder is.
  - `README.md`: "statements about the corpus builder's eight content families (gutenberg, base64, binary, code, csv, json, log, mixed), not about DEFLATE streams in general".

All of these stand in 4ca1ca5 (2026-09-16), where this clone's history begins.

**Actual:**

- **What the content is.**
  - `tools/pivot/corpus.py` builds `FAMILIES = ["gutenberg"] + sorted(SYNTH)`. `SYNTH` is seven generator functions: json, csv, log, code, base64, binary and mixed.
  - `artifacts/pivot/deflate_curve.json` `content_families` lists those eight.
  - 0016's reader banks the description "seven parametric generators and one real-prose family" (`fdc_4096_verdict.json`). `VERDICT.md` says the same twice. No outbound document said it of the builder's families.
- **The "+0.09 per decade" families.** csv, log and json (`per_family_curves.json`) are generator output:
  - slopes 0.090631, 0.090943 and 0.090131;
  - top rung 0.3888, 0.3756 and 0.3581, against chance 0.038462 (`deflate_curve.json`, `chance_accuracy`).

  The record holds no real csv, log or json file.
- **Real files.**
  - On real files the builder never produced, 0014's searched model reads 0.0637 against 0.088462 needed (`oob_4096_reread_verdict.json`, `OOB_TRANSFER_FAILS`).
  - Since 0023 and 0024 (2026-09-17) the record also has a preregistered curve fitted and scored on real files (`realcurve2_4096_verdict.json`). It rises: second-decade slope 0.00697 per doubling, [0.00571, 0.00824].
  - At the top rung it reaches 0.1404 over the five real kinds together. Per kind it reaches up to 0.1553, on py_src (`readings_banked.r7_model.ext_per_family`).
  - It does not clear 0021's bar re-applied there: 0.1419 is needed with the tree as floor (informational).

  "One real curve" therefore said too much about the headline's content. From 2026-09-17 it also said too little about the record.
- **The FDM-1 subtitle.** The evidence page put the name over a boosted-tree model's curve (`deflate_curve.json`, `model_class` "hgb") on that content. It named neither the model nor the content.

**Size:** The content of every 0003 and 0014 number: seven of eight families are generator output, in documents that never used the word. No banked number moves. Gutenberg is real prose, and `VERDICT.md` discloses the generators. The defect is that the investor-facing copy said "real", "the world" and "structured content" without saying what the content was. Two sentences also presented generator families as what a buyer's carves would need.

**Cause:** The outbound documents were written as compressions of `VERDICT.md`. They kept "structured content", and "real" in its archived-trial sense (a curve that clears its margins), and dropped what the content is. When 0023 and 0024 produced a real-file curve, no sentence saying "one real curve" was revisited. No gate can see an omission.

**Fix:**

- **The one-pager** (b3ff1bf) adds, after the label-factory sentence: "The 26 are zlib 1–9, libdeflate 1–12, ISA-L 0–3 and zopfli. The bytes are the corpus builder's eight content families: seven are its own synthetic generators (csv, log, json, code, base64, binary, mixed) and one is real Project Gutenberg prose."
- **README.md** (aabcdb3) adds "— seven of them the builder's own parametric generators, one real Project Gutenberg prose —".
- **The brief** (6d1f5d9):
  - says "on **the builder's synthetic structured generators (csv, log, json) the curve rises at roughly +0.09 per decade**";
  - calls the 2048 per-family rows "a decomposition on the builder's synthetic csv and log generators, not a reading on real carves".
- **The evidence page** (388d0f1):
  - The subtitle reads "the FDM-1 question, asked here of a boosted-tree model on the corpus builder's eight content families (seven parametric generators and Gutenberg prose)". The proposed clause naming what it is not asked of was not written.
  - The decomposition reads "the builder's generated structured families (csv, log, json; no real file of these kinds is among the record's real-content families)".
- **NARRATIVE** (8ebd2d4):
  - The ending reads "one preregistered scaling curve that clears its margins, on content mostly from our own generators; on real files the signal also rises with data but has not cleared the margin a cheap rule sets".
  - "The pivot found a curve", followed by "Seven of its eight content families come from our own generators, the eighth is Gutenberg prose" and the 0.0637-against-0.088462 real-file reading.
  - "The pivot produced a result that clears its preregistered margins; it is a statement about eight content families, seven of them from our own generators and one of Gutenberg prose."
  - "our generators' structured families", with "No real csv, log or json file has been measured", in the curve section and in the crib.
  - The close names one curve that clears its margins on content mostly from our generators, and a real-file signal that rises but has not cleared the margin a cheap rule sets.
- **VERDICT.md** (8ebd2d4):
  - keeps "The first curve in this repository that is a claim about the world rather than a test of the instrument" and appends "about four real DEFLATE libraries, on the corpus builder's eight content families, seven of which are its own parametric generators". NARRATIVE dropped its "claim about the world"; `VERDICT.md` still makes the claim, now qualified;
  - says "Structured content from the builder's own generators carries the curve";
  - gives the per-family rows as banked, "(csv and log here are the builder's own synthetic generators, and no buyer has been asked what it would need to see)".
- **docs/DILIGENCE.md** (938e0c7) says "on the builder's synthetic structured generators (csv, log, json)".
- **A new error in the replacements.**
  - NARRATIVE's "on the real files we have, the best the model reaches is 0.1404 (0024)" and its crib's "the best reading is 0.1404" give the five-kind reading as the best.
  - DILIGENCE.md's "the model reaches at most 0.1404" does the same.
  - Per kind, the same rung reads up to 0.1553 (py_src), so "at most" and "best" are wrong per kind, in the direction against us. They were fixed in d778549: each now says the reading over the five kinds together is 0.1404, up to 0.1553 on one kind (py_src).

No mechanical check exists for an omission. The rule is that a headline number in outbound copy says what its content is, in the same paragraph.


## 2026-10-22 — Published "the information is present at 1024" from 0007's rationale; 0007's own reader reads the result as "not recoverable at the shorter carve"

**Claimed:**

- `outbound/ONE_PAGER.md`: "The information is there at 1024. This is a modelling failure, not an information failure."
- `outbound/EVIDENCE_BRIEF.md`: "The information is present at 1024 (the collision ceiling barely moves: 20.9125 → 20.79 across 4096 → 512), so this is a modelling failure and is reported as one."
- `outbound/NARRATIVE.md`: "so the information is present at the shorter window and this is a modelling failure, and we say so in those words."
- `README.md`: "The information is present at 1024 — the byte-identity ceiling barely moves — so this is a modelling failure"
- `VERDICT.md`: "The information is present at 1024. **This is a modelling failure, not an information failure**, and the preregistration committed this document to saying so in those words before the number existed."
- `VERDICT.md`, L4's bullet: "The byte-identity ceiling barely moves across the range — 20.9125 distinct streams of 26 at 4096 against 20.79 at 512 — so this is a property of the representation, not of the fragment."
- `tools/render/evidence_page.py`: "The byte-identity ceiling barely moves across carve sizes, so this is a modelling failure and is reported as one."
- `docs/DILIGENCE.md`: "an information-ceiling measurement ruling out the easy excuse".
- `docs/strategy/MILESTONES.md`, the use-of-funds plan:
  - "The information is present (byte-identity ceiling 20.79 of 26 at 512 bytes against 20.9125 at 4096); the representation is what fails."
  - "so any per-size failure is a modelling result, not an information result, exactly as 0007 was forced to say."

**Actual:**

- **What A1 measures.** A1 (`artifacts/pivot/carve_channel_capacity.json`) counts how many of the 26 encodings of the same plaintext give distinct byte windows: 20.9125 at 4096, 20.805 at 1024 and 20.79 at 512.
  - Its own `why` calls this an information ceiling and says "This measures the input, never the outcome."
  - A ceiling that barely moves rules out byte collisions as the cause. It does not show that any model can recover the label.
- **The reader's reading.** 0007's reader banked: "The information is not recoverable at the shorter carve." (`carve_generalisation_verdict.json`, `meaning`).
- **The preregistration says both.**
  - `scope.why_1024`: "So the information is present at 1024, and anything that fails here is a MODELLING limit rather than an information limit."
  - `stop_rules[0]`: "The information is not recoverable at 1024 and the forensic setting is narrower than the 4096 numbers imply." It continues: "this outcome would be a modelling failure and must be reported as one."
- **What the model reads.** At 1024 the model reads 0.1355 against chance 0.038462, above chance. The logistic reads 0.1256, so the margin is +0.0099 against the bar of 0.05.
- **What has been tried since.**
  - 0009 is `BYTE_MODEL_FAILS`.
  - 0010 is `BYTE_FLAT_FAILS`, which its reader reads as "Inconclusive on the point 0010 exists to settle".
  - Whether any other model would clear the bar at 1024 is untested.

The sealed commitment to report a modelling failure stands. "The information is present", "not an information failure" and "the representation is what fails" do not.

**Size:** An untested inference was stated as a measured fact, in ten places across eight files. They include the one-pager, the README's headline section and the plan that sets milestone M1. The error flatters us, because it implies a better model would fix the failure. No number moves.

**Cause:** The sentences were published from the preregistration's rationale (`why_1024`), not from the reader's emitted `meaning`. The rationale was written before the run, to say why the run was worth doing. When frozen text disagrees with itself, `docs/OPERATING_RULES.md` §3 takes the reading that does not flatter, and the reader had already taken it. The commitment "in those words" was read as licensing the rationale along with the label.

**Fix:** Every sentence in that list but one was rewritten. Each now says byte collisions do not explain the failure and drops "the information is present". All but DILIGENCE.md's and MILESTONES.md's first sentence also keep the commitment to report a modelling failure:

- **The one-pager** (b3ff1bf): "So a collision ceiling does not explain the failure, and 0007's frozen reader reads it as sealed: the information is not recoverable at the shorter carve. This is a modelling failure, and is reported as one." It adds that no model in this record has shown the label recoverable at 1024, naming 0009 and 0010.
- **The brief** (6d1f5d9): "The frozen reader's banked reading is that the information is not recoverable at the shorter carve." It continues: "whether any model recovers the label at 1024 is untested beyond 0007's recipe, one byte-sequence CNN (0009) and an inconclusive variant (0010)".
- **README.md** (aabcdb3): the failure is reported, as preregistered, as a modelling failure, "which means only that". Whether any other model clears the bar at 1024 is untested beyond 0009 and 0010, and the frozen reader's reading is that the information is not recoverable at the shorter carve.
- **NARRATIVE** (8ebd2d4): "That is not proof the label can be recovered at 1024: our frozen reader reads this result as "not recoverable at the shorter carve"."
- **VERDICT.md's 0007 section** (8ebd2d4): the ceiling "bounds what any model could recover from above; it is not evidence that a better model would clear the bar". It then gives the reader's reading, with 0009 and 0010.
- **The evidence page** (388d0f1): "distinct bytes do not show that any model could recover the label, and the frozen reader reads it as not recoverable at the shorter carve".
- **DILIGENCE.md** (938e0c7): the measurement now shows "that byte collisions barely change across sizes and so do not explain it".
- **MILESTONES.md** (938e0c7): "whether a better representation would clear the bar is untested beyond 0009 and 0010". Also: "byte collisions do not explain any per-size failure, and 0007 was committed to report its failure as a modelling result; whether a better model would clear the bar at a shorter size is what this milestone tests".
- **Not changed.**
  - `VERDICT.md`'s L4 bullet ("so this is a property of the representation, not of the fragment") stands at HEAD f275303.
  - `VERDICT.md`'s rewritten 0007 sentence (8ebd2d4) keeps, in bold, "a modelling failure, not an information failure", now attributed to the preregistration's commitment, followed by the ceiling-bound and reader clauses. The sealed stop rule commits only to "a modelling failure"; "rather than an information limit" is in `why_1024`, the rationale. The phrase stands at HEAD f275303.

The rule, not a gate: a published reading of a verdict quotes the reader's `meaning`, not the preregistration's `why`.


## 2026-10-22 — Kept leading with the fixed-recipe +0.1003 after VERDICT.md committed to label it as one wherever it appears, while the one-pager said it led with +0.0567

**Claimed:**

- `VERDICT.md`, in 0014's write-up: "The frozen recipes' +0.1003 is no longer the number to lead with; it is a fixed-recipe number and is labelled as one wherever it still appears."
- `outbound/ONE_PAGER.md`: "a smaller margin than the fixed-recipe **+0.1003**, and the one this page now leads with."
  - The page's opening reads "margin **+0.1003** frozen and **+0.0583** under the stricter reading with fixed recipes, **+0.0567** when every baseline is searched too (0014)".
  - Its result section reads "Best of the **preregistered** set: logistic at **0.1392**, margin **+0.1003**." The same paragraph continues "the commitment to report both was recorded mid-run and anchored to drand round **6408095**, before either number was known."
- `README.md`, the headline paragraph: "a margin over the best trivial baseline of **+0.1003** under the frozen baseline set and **+0.0583** under the stricter one that adds deep trees. Both clear the 0.05 frozen before the corpus existed."
- The evidence page's headline tile (`tools/render/evidence_page.py`, from `deflate_curve.json`): "+0.1003", "margin over the frozen baseline set (bar: 0.05) · stricter reading +0.0583".
- `outbound/NARRATIVE.md`: "The margin over the strongest trivial baseline is +0.1003 under the frozen reading and +0.0583 under a stricter reading we committed to before the numbers existed; both clear the preregistered 0.05." The same document later calls +0.0567 "the margin we quote now".
- `docs/strategy/MILESTONES.md`: "4096 (works, margin +0.1003 frozen and +0.0583 stricter)".

**Actual:**

- **0014** (`artifacts/pivot/recipe_search_4096_verdict.json`, `read`): the searched model reads 0.2884 against a searched logistic at 0.2317, on both the frozen and expanded readings. That is a margin of +0.0567. Without gutenberg it reads 0.3003 against 0.2427, a margin of +0.0576.
- **The fixed-recipe margins.** +0.1003 and +0.0583 are 0003's margins over the logistic at 0.1392 and over the depth-16 tree at 0.1812 (`deflate_curve.json`). So NARRATIVE's "over the strongest trivial baseline" belongs to +0.0583, not to +0.1003.
- **Where +0.1003 led.**
  - The one-pager put +0.1003 first in its opening and in its result section, and labelled it as fixed-recipe only in the opening.
  - README.md's headline paragraph, the evidence page's tile and NARRATIVE never labelled it.
  - MILESTONES.md quoted it as the working margin at 4096.
- **When the stricter reading was committed.** Not "before the numbers existed".
  - `prereg_interpretation.json` records it "before the final baseline and model numbers were known".
  - The same note says the deep trees were added during piloting, when "a depth-8 tree already reaches 0.1192 against 0.0385 chance".
  - By the note's own `anchor_direction_correction`, its drand anchor proves only that it was written no earlier than the anchored round. This ledger filed that defect on 2026-08-31 (item 4) and corrected the artifact. At fab3678 the one-pager and `VERDICT.md` still set the anchor beside the precedence claim.
  - The precedence rests on run logs and commit history from before 4ca1ca5, which this clone does not hold: COULD NOT VERIFY.

**Size:** The headline margin was quoted at the size the record had retired, in five documents. The sentence claiming the one-pager led with the smaller margin was false as published. It flattered us twice: it overstated the margin, and it claimed a candour the page did not deliver.

**Cause:**

- The 0014 write-up appended +0.0567 to the end of the one-pager's existing margin sentence instead of leading with it.
- The one-pager's later sentence was written to the intent and never re-read against the opening.
- The evidence page's tile is rendered from `deflate_curve.json`'s fields and was never pointed at 0014's artifact.
- README.md, NARRATIVE and MILESTONES.md were not swept for the commitment `VERDICT.md` made.

**Fix:**

- **The one-pager** (b3ff1bf):
  - Its opening now reads "**+0.0567** when every baseline is searched too (0014) — the margin we lead with — and, with 0003's fixed recipes, **+0.1003** frozen and **+0.0583** under the stricter reading".
  - Its result section labels +0.1003 "a fixed-recipe number" and gives +0.0567 beside it.
  - Its later sentence was left as written and is now true.
  - In the same paragraph, the precedence claim is said to rest "on the run logs and commit history, not on its drand anchor (round **6408095**), which proves only that it was written no earlier than that round".
- **The evidence page** (388d0f1): the tile's value is now computed from `recipe_search_4096.json` (`final_top1` less `best_frozen_for_bar`) and renders +0.0567. It is labelled "margin with every baseline searched too" and gives the fixed-recipe pair as "+0.1003 over the frozen set, +0.0583 over a depth-16 tree".
- **NARRATIVE** (8ebd2d4):
  - It says that under 0003's fixed recipes the margin was +0.1003 over "the best of the frozen baseline set, a logistic regression" and +0.0583 over "the strongest baseline of all, a depth-16 tree".
  - It calls the stricter reading one "we recorded mid-run, before the final numbers were known", and says +0.0567 "is the margin we quote".
- **VERDICT.md** (8ebd2d4) now says its drand anchor "proves only that it was written no earlier than that round (the precedence rests on the run logs and commit history)".
- **README.md** (aabcdb3) labels the pair "with fixed recipes" and adds "**+0.0567** once the model's and every baseline's recipes are searched too (0014, below), the margin quoted".
- **MILESTONES.md** (938e0c7) reads "margin +0.0567 under a symmetric recipe search, prereg 0014; +0.1003 frozen and +0.0583 stricter under fixed recipes".
- **Still asserted, COULD NOT VERIFY.** The replacements state the precedence as fact. NARRATIVE says "a stricter reading we recorded mid-run, before the final numbers were known". The one-pager says "recorded mid-run, before either number was known" and `VERDICT.md` "recorded mid-run, before the baseline and model numbers were known"; both say the claim rests on the run logs and commit history. Those records predate 4ca1ca5 and are not in this clone, so the precedence in all three COULD NOT BE VERIFIED here.

No gate checks which margin a page leads with. A `docs/live_claims.json` entry tying the one-pager's lead margin to 0014's fields would make the next regression fail `tools/freshness.py`. It is proposed here, not built.


## 2026-10-22 — Said every reader was frozen before its data existed; two of the twenty-four were re-reads frozen with every number they read already known

**Claimed:**

- `outbound/ONE_PAGER.md`, its first sentence: "**It is** a preregistered evaluation instrument, built and frozen before any of the numbers it reports existed, and designed so that each of its gates can be shown to fail on demand."
- `outbound/EVIDENCE_BRIEF.md`, of its **24** preregistrations: "readers frozen by sha256 before their data existed."
- `outbound/NARRATIVE.md`: "with the verdict-emitting readers frozen by sha256 before their data existed."
- `tools/render/evidence_page.py`, the verdicts panel: "Emitted by readers frozen by sha256 before their data existed."
- `README.md`: "**Readers are frozen by hash before the data exists.**" and "the machinery constraining how numbers may be reported was built and committed *before* the numbers existed".

All of these stand in 4ca1ca5 (2026-09-16T06:50:35Z), after both re-reads below were frozen.

**Actual:**

- **The two re-reads.**
  - `prereg/0013-recipe-search-2048-reread.json`, frozen 2026-09-03T19:30:49Z after 0012 ran: "No new measurement. Every 0012 number was known when this was written and is quoted here; under these clauses they read RECIPE_FAILS."
  - `prereg/0019-oob-4096-reread.json`, frozen 2026-09-16T04:14:59Z: "Every 0018 number was known when this was written and is quoted here; under these clauses they read OOB_TRANSFER_FAILS."
  - Both verdicts are quoted on the one-pager, and both re-reads are chain entries.
  - Both are disclosed as re-reads where they are quoted, and both read a failure, so no result was flattered. What was flattered is the instrument's first-sentence guarantee.
- **The gates were not all built first either.** `tools/freshness.py` was written after stale numbers had been published (this ledger, 2026-08-25). `tools/record_counts.py` came with the 2026-09-04 entry.
- **What git can show.**
  - For 0021 to 0024, each preregistration's `frozen_utc` precedes the first commit of its artifact in this clone. For example, 0024 was frozen at 2026-09-17T20:38:28Z, and `realcurve2_4096.json` was first committed in 7e536c3 at 21:06.
  - For 0001 to 0019 the order COULD NOT BE VERIFIED from git, because this clone is shallow at 4ca1ca5.

**Size:** Two of twenty-four chain entries. The property was stated without exception in the one-pager's first sentence, the brief's instrument paragraph, NARRATIVE, the evidence page and two README sentences. No result moves.

**Cause:** The sentence describes the rule in `docs/OPERATING_RULES.md` §1. The re-reads were disclosed one at a time, where their verdicts appear. Nobody re-read the blanket sentences when 0013 became the first exception. This is the class of the 2026-09-16 entry: an instrument property published without exception, when a minority of cases take one.

**Fix:** Each sentence now names the exception:

- **The one-pager** (b3ff1bf): "each verdict emitted by a reader frozen before the data it reads existed — except two disclosed re-reads (0013 and 0019), written after their runs and both reading a failure".
- **The brief** (6d1f5d9): "except the two disclosed re-reads (0013, 0019), whose readers were frozen with the numbers they read already known".
- **NARRATIVE** (8ebd2d4): "except two disclosed re-reads of banked runs (0013, 0019)".
- **The evidence page** (388d0f1): "except the two re-reads of banked runs (0013, 0019), which their chips name as such".
- **README.md** (aabcdb3) adds to both of its sentences that 0013 and 0019 "are disclosed re-reads of banked runs, frozen after them".

README.md still says the machinery "was built and committed *before* the numbers existed". The re-read exception is added there, but `tools/freshness.py` and `tools/record_counts.py` came later, and that part stands at HEAD f275303.

The brief's "measured under bars frozen and hash-chained **before the data existed**" was checked and left. The verdicts it lists do not include the re-reads, and the re-reads' bars are copies of bars frozen before their data.

No gate checks prose about the chain. A chain field marking a re-read, which the documents could then count, is proposed here and not built.


## 2026-10-22 — Described the outbound-number gate as tracing every number to its artifact; it checks that some banked value anywhere, or a hundred times or a hundredth of one, rounds to the number

**Claimed:**

- `outbound/ONE_PAGER.md` and `README.md`, the comment on the `claimcheck.py` command a cold-clone reader is told to run: "# every number traces to a banked artifact"
- `outbound/EVIDENCE_BRIEF.md`, its first sentence: "Every number on this page traces to a machine-readable artifact in this repository at the written precision, enforced by `tools/claimcheck.py` with zero allowlist entries."
- `outbound/README.md`: "**The rule:** every number in every file here must trace to a banked artifact under `artifacts/`, at the precision it is written. Enforced by `python3 tools/claimcheck.py outbound VERDICT.md`, which exits non-zero otherwise and has mutation tests proving it can fail"
- `outbound/ONE_PAGER.md`: "This document passes the outbound-copy gate with no allowlist entries, and every live number on it is checked against the current artifact by the gate below it."
- `outbound/NARRATIVE.md`: "because gates check that numbers trace, not that the reasoning between them is sound".
- The evidence page's eyebrow: "Preregistered evidence · every number read from a banked artifact". Its renderer's docstring begins "Render outbound/evidence_page.html from the banked artifacts. No number is typed by hand." (`tools/render/evidence_page.py`).
- This ledger, 2026-08-25, of the existence check: "For a fabricated number that is the right question."

**Actual:**

- **What `backed()` checks.** `backed()` in `tools/claimcheck.py` pools every value in every banked artifact, numbers inside prose strings included. It passes a written number if any value in the pool, or that value times 100 or divided by 100, rounds to it at its written places. Nothing ties a number to the artifact or field its sentence cites.
- **An example.** `VERDICT.md`'s "About 3900 optimisation steps" passes only through the times-or-divided-by-100 path: as a banked 39.0 times 100, or a banked 390000 divided by 100. No banked value is 3900.
- **Where the mechanism is described correctly.** `README.md`'s own bullet ("`claimcheck.py` asks whether a number exists in a banked artifact") is accurate. So is `docs/OPERATING_RULES.md` §2, apart from the times-100 path. The comments and opening sentences above are not.
- **"Exits non-zero otherwise" is false** for any wrong number that happens to match an unrelated value. A pool this large matches many numbers written at the record's usual precision. A reviewer measured how many, in memory; the result is not banked and is not quoted here.
- **What `tools/freshness.py` checks.** It checks a number against its own artifact field only if the number is registered in `docs/live_claims.json`.
  - The one-pager registers two (`onepager-mutations`, `onepager-weakest-row`).
  - Its other present-tense counts, such as "Eight are measurements made by subagents", are checked by nothing.
  - This ledger said as much on 2026-08-25: "Only numbers entered in the registry are checked; a live number nobody registers is still unguarded."
- **"Every number read".** The renderer types some measured values into its prose, as its own docstring now lists: 0.2395, 0.1392, 0.2317, 0.2884, 0.9031 and 1.8016. Each matches its banked value, but a typed number does not follow its artifact.

**Size:** An instrument property, overstated in six documents:

- the evidence brief's first sentence;
- the rule `outbound/README.md` states for every outbound file;
- the command comments in the one-pager and README.md;
- the one-pager's claim about live numbers;
- NARRATIVE's account of the audit;
- the evidence page's eyebrow.

This entry shows no number in any document to be wrong. The guarantee behind all of them is weaker than published.

**Cause:** "Traces" is the intent of `docs/OPERATING_RULES.md` §2; what was built is a pooled existence check. The accurate description was written where the mechanism is explained, and the short descriptions kept the intent's word. This is the class of the 2026-09-16 entry and of the 2026-10-21 probe entry: a check credited with the property it was built to approximate.

**Fix:**

- **README.md** (aabcdb3):
  - The claimcheck comment reads "# every number matches some banked value at its written precision, not necessarily the one cited".
  - The freshness comment reads "# every number registered in docs/live_claims.json equals its artifact's current value".
  - The bullet adds "It does not check that the supporting value is the one the sentence cites."
  - The freshness bullet adds that "a number nobody registers is checked only by `claimcheck.py`".
- **The one-pager** (b3ff1bf):
  - Its comments read "# every number equals some banked value at its written precision, not necessarily the one cited" and "# every registered live number equals its CURRENT artifact value".
  - Its closing sentence names the two registered numbers, and says "a live number nobody registers is unguarded".
- **The brief** (6d1f5d9): its first sentence now says each number "matches a value banked", "a necessary check, not a trace". It names the times-or-divided-by-100 path, and says the gate "does not check that the artifact a sentence cites is the one that holds it". It names the three counts `tools/freshness.py` ties to their fields; the brief's preregistration, mutation and correction counts are all registered.
- **outbound/README.md** (6d1f5d9): it keeps the rule, and says the command "checks a necessary condition only". It adds that "which artifact field a number comes from is checked only for the numbers registered in `docs/live_claims.json`".
- **NARRATIVE** (8ebd2d4) reads "gates check that numbers are banked".
- **The evidence page** (388d0f1): the eyebrow reads "rendered from banked artifacts", and the docstring lists the typed values.
- **Not changed.**
  - `tools/claimcheck.py` itself is unchanged; its docstring still opens "every number in a document must trace to a banked artifact".
  - `docs/OPERATING_RULES.md` §2 still omits the times-100 path.

No check ties each outbound number to the artifact its sentence cites, and none is claimed. The registry remains the only field-level check.


## 2026-10-22 — Kept saying the manifest proves a rebuilt corpus byte-identical after two filed fetch failures; the builder caches cannot be rebuilt to their banked hashes, and 0024's corpus rebuilt twice with two different feature arrays, neither the banked one

**Claimed:**

- `docs/DILIGENCE.md`: "Corpora rebuild deterministically from shipped sources and generators; the manifest banks content hashes of every array so the rebuild is *proven* identical, not assumed." Also its command comment "# prove a rebuilt corpus is byte-identical to ours". The pass refuted that comment taken alone, as a description of a check on a rebuild that matches. It is filed here with the evidence page's identical, confirmed comment, because for the builder caches that check cannot pass.
- `outbound/NARRATIVE.md`: "the corpus manifest proves a rebuilt corpus byte-identical rather than assuming it." and "A validated instrument that reproduces on a cold clone."
- `tools/render/evidence_page.py`, in the evidence page's cold-clone block: "# prove a rebuilt corpus is byte-identical"
- `README.md`, its opening paragraph: "plus one shipped open artifact a stranger can reproduce from a cold clone."

This ledger quoted the DILIGENCE and NARRATIVE sentences on 2026-09-02, and the DILIGENCE one again on 2026-10-21. Both entries fixed the fetch and left the sentences standing.

**Actual:**

1. **The builder caches.** `run_study.build()` writes whole batches in worker-completion order and never sorts. So the X and g of the three builder caches it wrote cannot be rebuilt to their banked hashes on any machine. The caches are `full_c4096` (0003), `carve_c1024` (0007) and `carve_c2048` (0011). Sources: this ledger, 2026-10-21, the CI-probe entry; and ea495ac, "the banked X/g/position hashes cannot be recovered".
2. **The rebuilds of 2026-10-21 and 2026-10-22.** A fresh container rebuilt three real-file corpora on 2026-10-21 (`artifacts/pivot/engineering_log_0025.json`, `container_2026_10_21.corpora_rebuilt`).
   - 0018's and 0021's corpora matched their manifests byte for byte.
   - 0024's did not. Its y, g and fam hash to the banked values, but X hashes to c395da3f4c1aa3cb, not the banked d74bd30e71a5083f. The log's `realfit2_localisation_2026_10_22.cause` reads COULD NOT VERIFY.
   - A second rebuild of 0024's corpus on 2026-10-22, on a host with a different CPU, gave a third X hash, 4ff8ec5760ccb069, with y, g and fam identical. It differs from the first rebuild in 6 of 193926 rows, all labelled 22 or 23 (ISA-L levels 1 and 2). Forcing ISA-L's code paths showed this is not the CPU: the flips are run to run, roughly 0 to 4 chunks per full build (`realfit2_localisation_2026_10_22.isal_dispatch_test`; the entry of this date on 0024's corpus).
   - Refitted on the first rebuild, 0024's trees and its rung-5 logistic reproduce their banked vectors. Its rung-7 logistic does not: "r7_logistic DIFFERS on 264 rows (171 real; 5248 against 5249 real correct" (`realfit2_localisation_2026_10_22.refits_against_0024`).
3. **The CPU.** ISA-L's level 3 picks AVX2 or AVX-512 code at run time, and the two give different bytes. The log says: "Any rebuild on an AVX2-only machine would differ for ext, realfit and realfit2 alike: the manifests record no CPU features" (`isal_level3_dispatch_hazard`).
4. **The gates.** `tools/gates.sh` re-reads banked artifacts and re-runs no fit, so "reproduces on a cold clone" said more than the gates do.

The banked measurements are untouched: they were made on the banked bytes. Any rebuild of a builder cache itself COULD NOT BE VERIFIED: the log lists `full_c4096` as "not built yet".

**Size:** The reproducibility claim fails in three ways:

- for the three builder caches, on which the headline (0003, 0014) and the 1024 and 2048 carve studies rest;
- for 0024's corpus, whose two rebuilds also differ from each other, at ISA-L levels 1 and 2 on a few chunks per build, run to run;
- for every real-file corpus, on an AVX2-only machine.

This is the third ledger entry against the same sentences, and the first to find them false beyond the fetch.

**Cause:** The sentences describe what the manifest was designed to do. They rely on one property: that the builder writes the same bytes in the same order on any machine. No cold rebuild tested that against banked hashes until 2026-10-21. Both earlier entries fixed the step that failed first, the fetch, and did not ask whether the sentence held beyond it.

**Fix:**

- **docs/DILIGENCE.md** (938e0c7):
  - The sentence became a paragraph. It says the corpora are rebuilt from upstream sources pinned by sha256, that the fetch has broken before, and that "a rebuild is checked rather than assumed, and the check does not pass for every array". It then lists what a rebuild does and does not reproduce.
  - The command comment reads "# compare the rebuild's array hashes with the banked ones; X and g", continued on the next line as "of the build() caches print DIFF by design (see below)".
  - MILESTONES.md's corpus-size paragraph says the same.
- **NARRATIVE** (8ebd2d4):
  - The close reads "A mutation-tested instrument whose gates run on a cold clone — though no rebuild reproduces our headline corpus byte for byte (its results can be re-measured on a fresh draw, not re-derived on the same rows), one real-content corpus did not rebuild identical on a second machine, and the rebuild path has broken twice besides".
  - The crib answer opens "For consistency, yes" and says the gates re-read our banked artifacts. It says the manifest "checks the rebuild against ours rather than assuming it", and names what cannot pass and what fails today.
- **The evidence page** (388d0f1): the comment reads "# compare a rebuilt corpus with the banked hashes (what can match: below)", and a paragraph below it says what can match.
- **README.md** (aabcdb3): "a stranger can rebuild from a cold clone, though not all of it to the byte", followed by what a rebuild does and does not reproduce.
- **The other documents.**
  - The one-pager (b3ff1bf) renames its section "Check the record's integrity yourself, on a cold clone", and says "None of these commands re-runs a measurement".
  - The brief (6d1f5d9) says `gates.sh` "reads the banked artifacts; it does not rebuild the corpora", and lists what a rebuild does and does not reproduce. `outbound/README.md` (6d1f5d9) says "A stranger cannot re-derive every number by rebuilding".
  - `VERDICT.md` (8ebd2d4) says what "primary-verifiable" means for a builder-pool result: "re-measure it with the shipped code on a different draw of the same design, not re-derive the banked number on the same rows". That paragraph points to the Phase 3 row, which lists what a rebuild reproduces. The headline curve's Passed-table class and the coverage table's definition of `primary-verifiable` now say the same: a re-measurement on a different draw.
- **The tooling** (f44b63b):
  - `corpus_manifest.py`'s docstring now promises a comparison "array by array", not a proof.
  - `verify.sh`, `pin_sources.py` and `fetch_sources.sh` say the right sources are necessary for a matching rebuild, not sufficient.
  - In `coverage.json`, `corpus-manifest-2048` now files only y as primary-verifiable. The reverify commands of `deflate-curve-slope`, `deflate-margin-expanded`, `seed-robustness` and `carve2048-within` say they return a re-measurement on a different draw.
  - Separately, 35b6493 makes new manifests record the CPU feature flags and library files a build ran on, and hash X per block of rows. The banked manifests predate it.
- **COULD NOT VERIFY in the replacements.** The new texts say a rebuild reproduces three things: the labels of every corpus, `raw_c1024` whole, and the 4096 cache's evaluation set as a set of chunks. No rebuild of a builder cache or of `raw_c1024` is banked. Those clauses rest on the builder's code and the banked hashes, not on a rebuild.
- **The defects themselves** are filed in the two entries of this date on the builder caches' row order and on the rebuild of
  0024's corpus; this entry covers the published sentences and their rewrites.
- **The reorder tool.** ea495ac gives a rebuilt cache a documented canonical order. It cannot recover the banked hashes, and nothing here claims it does.


## 2026-10-22 — NARRATIVE.md still said all 13 audit findings were fixed by measurement; ten were fixed by editing text, and the QA review that caught the same wording elsewhere did not cover this file

**Claimed:** `outbound/NARRATIVE.md`: "13 findings survived refutation; all 13 were fixed by measurement and the full audit is published, rejected findings included." and "All 13 were fixed by measurement, and the audit record is banked with its rejected findings".

**Actual:**

- `artifacts/verification/adversarial_audit.json` holds 13 confirmed findings: 3 critical, 6 major and 4 minor.
- The three critical findings were answered by new measurement or derivation (`audit_rederivations.json`, `baseline_family_rescore.json`, `g4_github_firsthand.json`).
- The six major and four minor findings were corrected in the text ("All thirteen are corrected in place", this ledger, 2026-08-31).
- The QA review of 2026-08-31 (`docs/qa/NEW_DOCS_REVIEW.md`, Finding 3) flagged the same universal claim in `outbound/EVIDENCE_BRIEF.md` and on the evidence page. Both say "the load-bearing ones by new measurement".
- `outbound/NARRATIVE.md` was outside that review's scope and kept the sentence.

**Size:** Ten of thirteen findings, in two sentences of the spoken narrative. It flatters us: it overstates the rigour of our response to the one review whose subject was overstatement.

**Cause:** The QA fix was applied to the files the review named, not to every file carrying the sentence. This is the shape of the 2026-09-02 entry: a fix scoped to the review's list rather than to the defect.

**Fix:** Both sentences now say all 13 were fixed, "the three critical ones by new measurement, the other ten by correcting the text" (8ebd2d4). The brief and the evidence page were already right and were not changed. The rule, not a gate: a wording correction is applied by searching every published document for the phrase, not by working through the review's file list.


## 2026-10-22 — Answered "Won't a frontier model just do this?" by calling baselines trained on all of the task data "stand-ins for a clever prior with no task data"; no pretrained model has been run

**Claimed:**

- `docs/DILIGENCE.md`: "The measured stand-ins for "clever prior, no task-specific data" are the trivial-baseline ladder up to depth-16 trees and logistic regression, all trained on the same data as the top rung; the margins over them are the headline clauses."
- `outbound/NARRATIVE.md`, the crib: "the measured stand-ins for a clever prior with no task data — logistic regression and depth-16 trees trained on the same 800000 fragments — are exactly what every headline margin is scored against."

**Actual:**

- The baselines were trained on the same 800000 task fragments as the top rung (`deflate_curve.json`, `baselines_trained_on_n`). With all of the task data, they cannot stand in for a prior with none.
- No pretrained, LLM, transformer or frontier model appears in any verdict, curve or score artifact under `artifacts/pivot/`. The only matches for those words are a search note in `g4_firsthand.json` and a file name in `realfit3_corpus_manifest.json`.
- The answer to the question is that it has not been measured. Whether a frontier model would do this is COULD NOT VERIFY.

**Size:** The record's answer to the central competition question, in the diligence map and the investor crib, describes a measurement that was not made. It flatters us.

**Cause:** The question was answered with the measurement we had, relabelled to fit the question.

**Fix:**

- `docs/DILIGENCE.md` (938e0c7): "No stand-in for "clever prior, no task-specific data" was measured: no large pretrained model was tested." The margins are over the baseline ladder trained on the same data, "which bounds cheap learned rules, not a frontier model".
- The crib (8ebd2d4) opens "Not measured: no pretrained or frontier model has been run on this task". It says the margins measure "what a cheap learned rule does with all of our data, not what a frontier model could do".

No gate can check that an answer answers its question.


## 2026-10-22 — Headed the one-pager's competitor paragraph "Why no existing tool does this" on a search with two disclosed gaps the page left out

**Claimed:**

- `outbound/ONE_PAGER.md`: "**Why no existing tool does this.**"
- `VERDICT.md`'s conjecture C1, on the same search: "That withholding is precisely why no incumbent tool applies:"

**Actual:**

- The search behind both is `artifacts/pivot/g4_firsthand.json`, with its GitHub arm in `g4_github_firsthand.json`. Its own `honest_limits` list two gaps:
  - encode.su, "the venue where compression practitioners actually argue", returned 403 and "was NOT searched". It is "the single most likely place for undocumented prior work on this exact question".
  - "No patent search was run.", although round 4 found two USPTO patents on another candidate's exact task.
- `VERDICT.md` prints both limits beside the same tool list: "The honest limits stand: encode.su was unreachable and was not searched, and no patent search was run." The one-pager did not.
- The paragraph names four of the artifact's five known tools; the fifth identifies compression type only.
- Commercial forensic suites appear in no search artifact: COULD NOT VERIFY.

**Size:** One heading and one sentence of a conjecture, on the competition question, stating absence in our search as absence in the world. It flatters us, and `docs/OPERATING_RULES.md` §6 forbids exactly this.

**Cause:** The one-pager compressed `VERDICT.md`'s paragraph and kept its conclusion without its limits; C1 restated the conclusion away from the paragraph that carries them.

**Fix:**

- The one-pager (b3ff1bf):
  - The heading reads "**Why none of the tools we found does this.**".
  - The paragraph ends: "The search has known gaps: encode.su was unreachable and was not searched, and no patent search was run (`artifacts/pivot/g4_firsthand.json`)."
- C1 (8ebd2d4) reads "none of the five public tools we found applies (encode.su and patents were not searched, and commercial forensic suites were not checked)".

§6 is a rule and stays one.


## 2026-10-22 — Listed archive recompression and repackaged-APK detection as uses of the result; the record's frozen analysis says the task's advantage disappears in both

**Claimed:**

- `outbound/ONE_PAGER.md`, "What it does not establish": "The uses this points at — forensic carving of unallocated disk, archive recompression, repackaged-APK detection — are narrow, nobody has been contacted, and nothing measured here says anyone would pay."
- `VERDICT.md`: "But the buyers this points at — forensic carving of unallocated disk, archive recompression, repackaged-APK detection — are narrow".

**Actual:**

- 0006's scope, frozen 2026-08-25T21:49:05Z (`prereg/0006-deflate-operational-output.json`, `scope.what_this_is_for`): "archive recompression and repackaged-artifact checks both have the whole stream and the plaintext, so incumbent tools apply there and this task's advantage disappears".
- `VERDICT.md` says the same in its 0006 section: "Archive recompression and repackaged-artifact checks both hold the whole stream and the plaintext, so incumbent tools apply there and this task's advantage disappears."
- Just above the listed sentence, the one-pager itself names forensic carving as "the buyer type the entire G5 argument leaned on".

**Size:** Two of the three listed uses, in the paragraph whose job is to say what the result does not establish. It flatters us: it widens the apparent market against our own frozen analysis.

**Cause:** The list names adjacent applications. The analysis that rules two of them out lives in 0006 and in `VERDICT.md`. It was not carried into the one-pager, or into `VERDICT.md`'s own earlier paragraph.

**Fix:**

- The one-pager (b3ff1bf) names one use where a carved fragment is the real input, forensic carving of unallocated disk. It says archive recompression and repackaged-APK detection "hold the whole stream and the plaintext, so incumbent tools apply there and this task's advantage disappears".
- `VERDICT.md` (8ebd2d4) now says the same, pointing to its 0006 section.


## 2026-10-22 — The one-pager said every candidate died to a failure mode "established by measurement rather than argument", L3 said there are "exactly three ways", and L1's range was stated past its own numbers; some kills were argued, the record names a fourth way, and the range holds for seven of nine

**Claimed:**

- `outbound/ONE_PAGER.md`:
  - "Every candidate died to one of five failure modes, each established by measurement rather than argument."
  - L3: "the labelling must already be someone's job, and there are exactly three ways that happens — each destroying a different gate."
  - L1: "explains up to 0.994 of the residual variance in satellite orbit-correction arcs".
- `VERDICT.md`:
  - L3's heading: "— and there are exactly three ways that happens, each destroying a different gate";
  - "It is four laws, each derived by measurement";
  - "Everything above this line is measured.";
  - L1: "explains between 0.946 and 0.994 of the residual variance in eight of nine Sentinel-1 orbit-correction component-arcs". `artifacts/verification/coverage.json`'s claim `sentinel1-fit` gives the same range.
- `outbound/NARRATIVE.md`: "The search still paid: three measured laws about *why* these domains die, each retiring an entire candidate family."
- The evidence page's footer (`tools/render/evidence_page.py`): "four measured laws".

**Actual:**

- **Measurement.**
  - `VERDICT.md` calls L3(i) "the only law whose evidence is primary-verifiable".
  - L1's Sentinel-1 fit and L3(iii)'s MOT numbers are in the coverage map's weakest class (`artifacts/verification/coverage.json`, ids `sentinel1-fit`, `mot-untrained-rule`, `mot-prior-outcome`).
  - `VERDICT.md` says a reader who declines a subagent's word "is left with the laws unproven, and would be right to."
- **Argument.**
  - Some candidates were killed by argument. A round-3 scout recorded that "every F5 reading in its submission is an argument rather than a result" (`artifacts/phase0/round3_domain_search.json`).
  - No banked artifact defines "five failure modes": COULD NOT VERIFY.
- **"Exactly three".**
  - `VERDICT.md` says "There is a fourth case, and the pool contained zero instances of it." In that case the label is a by-product of a human acting on a rich sensor stream.
  - The one-pager's own "What that leaves" paragraph, a few lines later, describes the class the pool lacked.
  - The three ways were observed among 99 candidates (`artifacts/phase0/phase0_totals.json`, `total_candidates`).
- **L1's range.**
  - The subagent's per-component values (`artifacts/phase0/round2_domain_search.json`) are 0.993, 0.975 and 0.946; 0.974, 0.954 and 0.480; and 0.983, 0.994 and 0.944.
  - Eight of nine are 0.944 or better. Only seven are 0.946 or better.
  - The subagent's own summary, "0.946 or better in 8 of 9", does not match its values, and `VERDICT.md` and `coverage.json` copied it.

**Size:** Seven sentences on the laws' evidence, two of them statements of a law, and one range overstated in two published places (`VERDICT.md` and `coverage.json`; the archived trial notes `trial/pivot/_analysis.md` and `trial/pivot/DOMAIN_SELECTION.md` carry it too) and given only by its top in the one-pager:

- Argument was presented as measurement.
- An observation over 99 candidates was presented as an exhaustive taxonomy, which the record itself contradicts.
- L1's lower bound was overstated for one component-arc in nine, by 0.002.

It flatters us.

**Cause:** The laws were first written as derived results. The record later qualified them in three places: the coverage map, its weakest-row paragraph, and its fourth-case section. The summary sentences were not brought into line. This is the class of this ledger's 2026-08-31 items 9 to 12, a law "derived by measurement". L1's range was copied from a subagent's summary sentence, not from its values.

**Fix:**

- **The one-pager** (b3ff1bf):
  - The section heading "Why it is worth more than a domain would have been" became "What the search produced".
  - The sentence reads "Every candidate died to one of five failure modes. Only L3(i)'s evidence below is primary-verifiable (reproduced here). L1's and L3(iii)'s rest on subagent measurements no one can now re-run (see *The part that should be read first*), and L3's three-way split is argued, not measured."
  - L1 reads "0.944 to 0.994 of the residual variance in eight of nine component-arcs of three Sentinel-1 orbit-correction arcs (0.480 in the ninth) — a subagent measurement this repository cannot re-run".
  - L3 reads "across 99 candidates we found it happen in three ways".
- **VERDICT.md** (8ebd2d4):
  - "four laws, each resting on measurement — three from the search, several of whose load-bearing measurements are subagent numbers this repository cannot reproduce";
  - L1 adds "a subagent measurement this repository cannot reproduce (coverage class `neither`, below)";
  - L3's heading reads "among our candidates we found three ways that happens";
  - "Everything above this line rests on measurement, several of the load-bearing ones subagent measurements in the coverage map's `neither` class."
- **NARRATIVE** (8ebd2d4): "three laws about *why* these domains die, each derived from measurements — some of them a subagent's that we have not re-derived here".
- **The evidence page** (388d0f1): "four laws derived by measurement (three of them from the search, part of whose evidence was measured in scratch directories that no longer exist and cannot be reproduced here)".
- **Not changed.**
  - "five failure modes" stands in the one-pager, with no banked definition.
  - `VERDICT.md`'s L1 range and `coverage.json`'s `sentinel1-fit` claim still say 0.946 in eight of nine at HEAD f275303, so the one-pager (0.944) and `VERDICT.md` now disagree. The two archived trial notes are unchanged.

`docs/OPERATING_RULES.md` §6 is the rule.


## 2026-10-22 — VERDICT.md's closing section still counted four curves with exactly one a claim about the world, and said most findings rest on subagent measurements; the record outgrew both

**Claimed:** `VERDICT.md`, "What this repository does not establish":

- "**It contains four fitted, interval-bounded curves, and exactly one of them is a claim about the world** — the carved-DEFLATE curve of preregistration 0003, valid at a 4096-byte window and only there (0007)."
- "**Most of its findings rest on subagent measurements** that have not been independently reproduced, as the coverage map states in detail."

**Actual:**

- **The curves.**
  - The record now banks more than four fitted, interval-bounded curves. They include 0011's at 2048 (`carve_generalisation_2048_verdict.json`), and 0023's and 0024's on real files (`realcurve_4096_verdict.json`, `realcurve2_4096_verdict.json`).
  - The real-file curves are claims about real files. They rise, and their top readings do not clear 0021's bar: 0.1193 against 0.1429. Re-applied with the tree as floor (informational), 0.1404 does not clear 0.1419.
  - 0003's curve is a claim about the builder's eight content families, seven of them generators (see the generator-content entry above).
- **The findings.**
  - The coverage map holds 283 claims (`artifacts/verification/coverage.json`). 14 are in the weakest class, and nine of those rest on subagent measurements: eight that no one can re-run, and one (`sat-subagent-slope-not-reproduced`) that this repository tried to reproduce and could not. 233 are primary-verifiable.
  - So "most of its findings" was false, in the direction against us.

**Size:** Two bullets in the section that exists to say what the repository does not establish.

- The first erred both ways at once: it understated the curves and overstated what the one it names is about. It was corrected once already for the same class (this ledger, 2026-08-31, item 5).
- The second ran against us.

**Cause:** The closing section is prose with no registered numbers, so nothing fails when the record grows. It was true when written and was not revisited when 0011, 0023, 0024 and the coverage work landed.

**Fix:** Both bullets were rewritten (8ebd2d4).

- **The first** gives no count of curves ("more than the four this bullet once counted"). It names:
  - 0003's curve, "on the corpus builder's eight content families, seven of them its own generators";
  - the real-plaintext curves and the bar they do not clear (0.1404 against 0.1419, re-applied);
  - the curves that miss.

  An error in the proposed replacement, which gave 0024's reading for 0023's, was not carried over.
- **The second** says "Some of its findings" rest on subagent measurements, and names the Sentinel-1 fit behind L1 and the MOT numbers behind L3(iii). It says the shipped code's re-derivability "is a property of the code, not a reproduction by anyone outside this team".
- **The proposal not followed.** The draft of this entry proposed bullets without counts. The second bullet as written carries four counts ("eight of the 14 claims", "233 of the 283 claims"). None is registered in `docs/live_claims.json`, so the same cause can recur when the coverage map moves. Its "eight" follows `VERDICT.md`'s own split, which counts the actively unreproduced figure separately as "the ninth"; under the bullet's own words (subagent measurements "that have not been independently reproduced") that figure counts too, and the number is nine. It stands at HEAD f275303.


## 2026-10-22 — NARRATIVE.md said the diligence map has nine question headings and that its crib answers all of them; the map has more, and the questions on 0015 onward are answered elsewhere in the document

**Claimed:** `outbound/NARRATIVE.md`:

- "The diligence map at `docs/DILIGENCE.md` carries **nine** question headings (the brief for this document said eight; the file itself has nine, so all nine are answered here — see COULD NOT VERIFY below)."
- In that COULD NOT VERIFY section: "`docs/DILIGENCE.md` contains nine question headings. All nine are answered above rather than silently dropping one."

**Actual:**

- `docs/DILIGENCE.md` carries seventeen question headings at fab3678. Among them are the questions on 0015 to 0024, from "Does it work on content it has never seen?" to "Does a second decade of real files help?". The newest were added on 2026-09-17 (216fd60, cad24ab).
- The crib answers none of these. They are answered in NARRATIVE's five-minute version.
- `tools/publish/publish_0025.py` adds another heading when 0025 is published, and nothing updates or checks this count.

**Size:** One count and one completeness claim, false since at least 4ca1ca5 (2026-09-16), where this clone's history begins. They sit in the section of the document meant to list what could not be verified. Flattering: the sentences claimed the crib covered all of the map's question headings; it covered nine of seventeen.

**Cause:** The count of a growing file was written as prose and never registered. This is the class of this ledger's 2026-09-04 entry.

**Fix:** Both sentences were rewritten (8ebd2d4).

- They say the map carries **seventeen** question headings. They say nine are answered in the crib and the eight on 0015 to 0024 in the five-minute version.
- The draft of this entry proposed giving no count. The text as written gives one, unregistered.
- 0025's publication script adds the heading "Does a fourth doubling of real files help?" to the map. So "seventeen" goes stale the day 0025 is published, unless that script or a registry entry moves it. The cause stands.


## 2026-10-22 — DILIGENCE.md said 0014's margin is +0.0567 "on every reading"; with gutenberg excluded it is +0.0576, and two more documents say the same

**Claimed:**

- `docs/DILIGENCE.md`, "Does it survive realistic carve sizes?": "0.2317, +0.0567 on every reading, `RECIPE_CLEARS`,".
- `outbound/EVIDENCE_BRIEF.md`, its summary: "0014: +0.0567 on every reading against a searched logistic at 0.2317".
- `outbound/NARRATIVE.md`: "and the margin held at +0.0567 on every reading".

**Actual:** From `artifacts/pivot/recipe_search_4096_verdict.json`:

- On the frozen and expanded readings, `read.final_top1` is 0.2884 against 0.2317, so +0.0567.
- With the leaked family excluded, `read.final_top1_non_gutenberg` is 0.3003 against `bars_applied.expanded_non_gutenberg` 0.2427, so +0.0576.

`VERDICT.md` and the one-pager give all three readings.

**Size:** One reading of three, off by less than a thousandth, in the direction against us, in three documents. It is filed because this ledger files errors against our interest at the same size as the rest.

**Cause:** "Every reading" was generalised from two readings that happen to be equal.

**Fix:** `docs/DILIGENCE.md` (938e0c7) gives "+0.0567 on the frozen and the expanded reading and +0.0576 with the leaked gutenberg family excluded". The brief's bullet was rewritten in 6d1f5d9, to add the gutenberg clause, and kept "+0.0567 on every reading". NARRATIVE's sentence was in no item and is unchanged. Both stand at HEAD f275303.


## 2026-10-22 — VERDICT.md, the dataset card and this ledger gave the all-family mean distinct-stream count as 22.27 (the card with a collision rate of 0.143), and the evidence page set a 4096-window mean of 20.9125 beside whole-stream values; the banked whole-stream mean is 22.261 and the banked collision rate 0.1438

**Claimed:**

- `VERDICT.md`, "Incompressible content caps what is achievable": "22.27 is the mean across all eight content families".
- `tools/pivot/DATASET_CARD.md`: "22.27 of 26, collision rate 0.143".
- This ledger, 2026-08-31, items 6 to 8: "22.27 — the all-family mean distinct-stream rate".
- The evidence page, "Where the curve lives" (`outbound/evidence_page.html`, rendered by `tools/render/evidence_page.py`): "(14.667 and 14.75 distinct streams of 26 for base64 and binary; the mean across all eight families is 20.9125)".

**Actual:**

- **The whole-stream mean.** `artifacts/pivot/channel_capacity.json` banks `overall_mean_distinct_streams` as 22.261, which is 22.26 at two decimals.
  - The mean of its eight `per_family` values (14.667 to 25.917) agrees.
  - 22.27 appears only in the same artifact's prose `reading` field, beside its "collision rate of 0.143".
  - The same artifact banks `collision_rate` as 0.1438, which is 0.144 at three places. The prose's 0.143 misstates it at three places, and in the same direction as 22.27: fewer collisions, more distinct streams.
  - `tools/claimcheck.py` reads numbers out of strings, so it passed both figures.
- **The page's 20.9125.** That figure is `carve_channel_capacity.json` `by_carve.4096.mean_distinct_streams_of_26`, a mean over 4096-byte windows. The page set it beside 14.667 and 14.75, which are whole-stream values from `channel_capacity.json`. That is two measurements from two artifacts, read as one comparison.
- **The earlier review.** The QA review of 2026-08-31 (`docs/qa/NEW_DOCS_REVIEW.md`, Finding 1) flagged the page for giving 20.9125 as the incompressible families' ceiling. The repair added the right per-family values and kept 20.9125 beside them.

**Size:** For 22.27: under a hundredth, in the second decimal, flattering by that much and no more. For the dataset card's 0.143: collisions understated by under a thousandth, flattering by that much. For the page: one comparison mixing window sizes. No number in it is wrong for its own measurement. It is filed because entries here are append-only, the 2026-08-31 entry repeats 22.27, and the page's figure survived one review already.

**Cause:** 22.27 and 0.143 were copied from the artifact's prose, which rounds both wrongly, not from its numeric fields; the gate cannot tell the two apart. The page's sentence drew its per-family values from `channel_capacity.json` and its mean from `carve_channel_capacity.json`. Nothing checks that two numbers set side by side measure the same thing.

**Fix:**

- `VERDICT.md` (8ebd2d4) says 22.261.
- The renderer (388d0f1) now reads `channel_capacity.json` `overall_mean_distinct_streams`, and the page says "against 22.261 across all eight families, all three on whole streams of 32768-byte source chunks".
- `tools/pivot/DATASET_CARD.md` was in no applied commit: it still says "22.27 of 26, collision rate 0.143" at HEAD f275303, both figures wrong. This entry's draft said the 22.27 would be corrected, and it was not.
- The artifact's `reading` field is banked and stays as written; this entry is its correction.


## 2026-10-22 — The 2026-09-02 entry said one of six QA findings went unfixed; two did, and Finding 6's wrong artifact pointer in DILIGENCE.md stood until today

**Claimed:**

- This ledger, 2026-09-02: "**Size:** one of six findings claimed fixed; one integer; in the verification section of the diligence map."
- The pointer at issue, `docs/DILIGENCE.md`, "Where does the signal actually live?": "near-flat on incompressible families sitting at the measured collision ceiling (`carve_channel_capacity.json`)."

**Actual:**

- `docs/qa/NEW_DOCS_REVIEW.md` Finding 6: `carve_channel_capacity.json` holds only all-family means per carve size. The per-family ceilings (14.667 for base64, 14.75 for binary) are in `channel_capacity.json`, `per_family`.
- The 2026-09-02 entry itself records that "The commit did not touch `docs/DILIGENCE.md` at all". Finding 6 is in that file, so it was unfixed too, and the pointer stood unchanged at fab3678.
- a42d0c7 predates this clone's history, so its diff COULD NOT BE VERIFIED directly. This finding rests on the ledger's own words and on the pointer still standing.

**Size:** One wrong file pointer, with no number misquoted. One count in a ledger entry: one of six becomes two of six.

**Cause:** The 2026-09-02 entry checked the finding that had been found again, the mutation count. It did not check the review's other findings against the same diff.

**Fix:** The pointer (938e0c7) now reads "(`channel_capacity.json`: 14.667 and 14.75 distinct streams of 26 for base64 and binary)". The rule, not a gate: when a claim of "fixed" turns out false, every finding it covered is re-checked against the diff.

## 2026-10-22 — Said a corpus rebuild is proven byte-identical; 0024's realfit2 corpus does not rebuild byte for byte, because ISA-L's level-1 and level-2 output on rare chunks is not reproducible from run to run, and 0024's rung-7 logistic does not reproduce on a rebuild

**Claimed:** "Corpora rebuild deterministically from shipped sources and generators; the manifest banks content hashes of every
array so the rebuild is *proven* identical, not assumed" (`docs/DILIGENCE.md`), said of every corpus the record rests on. For
0024's second-decade corpus the claim carried weight: preregistration 0025 seals the rule that 0024's slope and lead intervals
must recompute exactly from rungs 1..7 before any rung-8 fit, which presumes rungs 5..7 can be rebuilt byte for byte. The 0025
engineering log, in its first entry on the refits (d8485ff, 2026-10-22), said the rebuilt corpus's difference "does not move
these fits"; that was written before the rung-7 logistic finished and was corrected in the log itself (fab3678).

**Actual:** On 2026-10-21 `tools/pivot/corpus_realfit2.py --build` on a fresh container, from pinned sources that verify byte for
byte and with the library versions the banked manifest records (isal 1.8.0, libdeflate 0.9.0, zopfli 0.4.3, zlib 1.3, numpy
2.4.6; python 3.11.17 here against 3.11.15 then), produced arrays whose y, g and fam, chunk metadata and every other manifest
field equal the banked ones, but whose X (193926 x 1108 float32) hashes to `c395da3f…`, not the banked `d74bd30e…`
(`artifacts/pivot/realfit2_corpus_manifest.json`; `artifacts/pivot/engineering_log_0025.json`, `container_2026_10_21`). The
corpora 0018 and 0021 rest on (`ext_c4096`, `realfit_c4096`) rebuilt identical on the same container.

What is known about where and how much:
- The rows that form 0024's sealed smoke corpus (the first 126 pool chunks per family: 16027 rows, 629 chunks, all 26
  configurations) hash to 0024's banked smoke y, g, fam and X (`41d1d6f3…`;
  `tools/prereg_gen/0025/realfit2_smoke_subset_check.py`), so the difference lies in the chunks with k >= 126.
- The container compresses deterministically (1745 chunks x 25 configurations, twice, 0 differences), and numpy's AVX-512
  dispatch does not move the sampled rows (5135 rows recomputed with it disabled are byte-identical).
- Refitted with the sealed interpreter through the repository's own partition and fitting code (every rung's row set hashes to
  0024's sealed rung hashes), 0024's fits reproduce their banked per-example vectors on the 61409 extension rows exactly at
  r4..r7 for the depth-3 tree and at r5 for the logistic (n_iter 479, as banked). The rung-7 logistic does not: 264 of 61409
  rows differ (171 real; 5248 against 5249 real rows correct, a reading difference of about 0.00003), and it ran 678
  iterations against the banked 664. The difference is in the fit inputs, in realfit2 rows that rungs 6 and 7 add.
- A second rebuild on 2026-10-22, after the container restarted on a newer CPU (numpy's AVX512_ICL and AVX512_SPR targets
  present), gives a third X, `4ff8ec57…`, with y, g, fam and the smoke subset identical again. The two rebuilds differ in
  exactly 6 of 193926 rows in 4 chunks, every one labelled 22 or 23 - ISA-L levels 1 and 2 - with the whole feature row
  moving: the compressed bytes differ. It is not the CPU. ISA-L dispatches 17 functions on the deflate path, both hosts
  select identical code, and forcing each code-path tier shows every tier but the native AVX-512 one changes y on 8 to 20
  chunks (so the banked build ran the native path too) while no tier or mixture reproduces the banked X. The flips are run
  to run: a full build changes the level-1 and level-2 streams of roughly 0 to 4 chunks, a third rebuild on one host flipped
  a chunk the other two did not, and seven million CPU-pinned compressions in isolation produced none. Why a full pipeline
  run flips them is not identified (COULD NOT VERIFY). The banked X is most likely the canonical X plus an unknown set of
  such flips; with no per-row or per-block banked hash it cannot be searched for, so the banked bytes are not recoverable.
  Separately, ISA-L's level 3 writes different bytes on its AVX2 and AVX-512 paths, so a rebuild on an AVX2-only machine
  would differ for every corpus.
- The other three real-content corpora rebuild identical: 0018's and 0021's on the first host, 0025's `realfit3_c4096` (X
  `98547322…`, y, g, fam) on the second, so the dependence has shown itself only on realfit2's rare inputs so far.

**Size:** One of the four real-content corpora 0025 depends on (realfit2, 193926 rows) is not reproducible byte for byte on a
second machine; its rare differing rows move 0024's rung-7 logistic on 264 of 61409 scored extension rows and one real row
of 38452. Every 0024 verdict and number stands: each was measured on the banked corpus and each reader reads banked artifacts.
What moves: a stranger rebuilding realfit2 cannot re-derive 0024's rung 6..7 fits bit for bit, only to within a reading
difference of the order shown; and 0025, as sealed, cannot pass its own exact-interval rule on a rebuilt realfit2 and would
file NOT RUN. 0025 is unfrozen; whether it is amended before its freeze (a reproduction within the reading tolerances, filed
as weaker than the exact rule) or runs on the banked bytes reproduced is set out in `docs/strategy/0025_DECISION.md` and
not yet taken.

**Cause:** One of the four DEFLATE libraries the labels are made from, ISA-L, occasionally writes different level-1 and
level-2 bytes for the same input inside a full build, and the builders feature the compressed stream; the builders assumed a
compressor is a pure function of its input and level, and nothing checked it. The manifests banked the library versions but
not the platform under them - CPU features, the C library, which `libz` was loaded, the library files' hashes - and banked X as
one hash, so the difference could not be localised below "somewhere in 193926 rows" until two rebuilds on two hosts were
compared row by row. The "proven identical" rebuild had never been run on a second machine before 2026-10-21; the two corpora that
were rebuilt first came out identical, and the sentence was extended to all of them.

**Fix:** `tools/prereg_gen/0025/realfit2_smoke_subset_check.py` localises a realfit2 rebuild against 0024's sealed smoke
corpus. From now on every corpus builder's manifest records the platform it was built on (CPU feature flags, numpy's SIMD
targets, the C library, the zlib runtime and the loaded `libz`'s path and hash, and the hashes of the isal, libdeflate and
zopfli library files) and X hashed per block of rows, so a future mismatch names its block and its platform difference
(`tools/pivot/corpus_ext.py` `platform_block`, `write_manifest`). `docs/DILIGENCE.md` says which corpora rebuilt identical on
a second machine and which did not. The banked manifests are not rewritten. Proposed, not made: a builder that compresses
each ISA-L configuration twice and refuses (or retries) on disagreement; whether that would catch this fault, which isolated
compressions never showed, is untested.

## 2026-10-21 — Said a rebuilt builder cache is proven byte-identical; its builder writes rows in worker-completion order, so no rebuild reproduces its X and g, or any row-position hash sealed from 0011 to 0025

**Claimed:** "Corpora rebuild deterministically from shipped sources and generators; the manifest banks content hashes of every
array so the rebuild is *proven* identical, not assumed" (`docs/DILIGENCE.md`). It sits under a command block that ends
`corpus_manifest.py --check  # prove a rebuilt corpus is byte-identical to ours`. At 27a61aa (2026-10-21 21:07 UTC) that block
gained the `run_study.py` command that builds `data/pivot/full_c4096.npz`, in the same commit whose message says the builder
cache's X/g hashes cannot be rebuilt. Other places:
- "the corpus manifest proves a rebuilt corpus byte-identical rather than assuming it" (`outbound/NARRATIVE.md`);
- "`corpus_manifest.py --check` # prove a rebuilt corpus is byte-identical" (`outbound/evidence_page.html`);
- "a cold clone re-manufactures them and checks the hashes" (`docs/strategy/MILESTONES.md`), said of the four corpora in the
  manifest;
- "a rebuilt corpus C is proven byte-identical rather than assumed" (`artifacts/verification/coverage.json`, claim
  `corpus-manifest-2048`, filed primary-verifiable);
- "so a stranger's rebuild can be PROVEN identical" (`tools/pivot/corpus_manifest.py`; the manifest banks the docstring's
  second paragraph as its `why`);
- "so a cold clone still rebuilds byte-identically" (`tools/pivot/source_pins.json`);
- `tools/pivot/verify.sh`'s "To re-derive the result from scratch" block, which builds the cache and checks it against "the
  banked array hashes";
- three primary-verifiable coverage claims (`deflate-curve-slope`, `deflate-margin-expanded`, `seed-robustness`) whose
  re-verification command is that rebuild followed by a re-measurement.

This ledger said it too, this morning. The cold-clone entry of this date counted the builder cache among the claims the source
fix restored, and its Fix says "Every corpus rebuilt on this container is checked against its banked manifest before any
preregistration uses it."

**Actual:** `tools/pivot/run_study.py` `build()` hands its chunk tasks to `Pool(procs).imap_unordered(_one, tasks, chunksize=8)`
and writes each result at the next free row as it arrives (`X[n:n + m] = ...`). A batch of eight consecutive chunks comes back
whole, but the batches come back in whatever order the workers finish them, and nothing sorts the rows before `np.savez`. The
row order of every cache `build()` writes is therefore a record of one run's scheduling, and no rebuild can be asked to repeat
it. Three of the four corpora `artifacts/pivot/corpus_manifest.json` banks were written by `build()`: `full_c4096` (by
`run_study.py`, under 0003), and `carve_c1024` and `carve_c2048` (by `run_carve.py`, which imports it).

The banked record shows the order is not reproducible, without any rebuild being needed to show it:
1. `carve_c1024` and `raw_c1024` hold the same 25000 chunks (50000 to 74999) with the same y. `raw_c1024` was written by a
   sequential loop in `run_byte_model.py`. Its banked g is the ascending sequence (sha256 `8e81f592…`, recomputed 2026-10-21).
   `carve_c1024`'s banked g is not (`0076adaf…`).
2. `full_c4096`'s banked g (`eda31b7c…`) is not the ascending sequence either (`677641ad…`). The sealed evaluation chunk
   sequence (`scope.eval_chunk_layout` of 0024 and 0025: 10000 chunks in 5211 batches) runs backwards 711 times and is never
   more than 3 batches from ascending. That is the signature of four workers finishing eight-chunk batches out of turn.

So on any rebuild, X and g of the three caches hash differently, however faithful the sources, code and libraries are, and
`corpus_manifest.py --check` prints DIFF for six of their nine arrays. y is unaffected. Every one of the 50000 chunks yields all
26 configurations in configuration order, so y is the same periodic sequence in any batch order; the banked y hashes,
`2b704268…` and `7f008413…`, equal that sequence's hashes. `raw_c1024` rebuilds whole. By the CI probe's own docstring, the
manifest check had "only ever been executed on the machine that built them", against the files its hashes were taken from. The
banked `full_c4096` went with the old container on 2026-10-21 (the cold-clone entry of this date), and its row order went with
it.

The order carried more than positions. `grouped_split` (`tools/pivot/run_carve.py`, the split every 4096 runner imports) holds
out the first 20% of a seeded shuffle of the chunk ids. It then shuffles the training rows' *positions* with the same generator
and keeps the first 800000. The permutation is fixed by the seed and the counts, so the cache's row order fixes which 800000 of
the 1040000 training rows form the pool, not only the order they come in. The evaluation set is a set of chunks and survives a
rebuild as a set; the pool does not. `tools/prereg_checks/prefreeze_0025.py` says the opposite: "a rebuilt cache moves row
positions only".

What is sealed on the lost orders:

| Hash | Value | Sealed in |
|---|---|---|
| `eval_idx_sha256` (`full_c4096`) | `7da1099e…` | 0014–0018, 0020–0025 |
| `pool_idx_sha256` | `17b0dc0b…` | 0014–0018, 0020–0025; restated in 0019 |
| `pool_sorted_sha256` | `923cd266…` | 0014–0018, 0020–0025 |
| `pool_y_sha256` | `d519612b…` | 0014–0018, 0020–0025 |
| g, in `cache_identity` | `eda31b7c…` | 0014–0018, 0020–0025; 0011's corpus-A clause by reference to the manifest |
| `eval_g_sha256` | `882292fc…` | 0020–0025 |
| X, in `cache_identity` | `a28a2d40…` | 0021–0025 |
| pool-block null | `822b6102…` | 0014, 0016, 0019 |
| fold-block null | `0653cc12…` | 0015, 0017, 0018, 0019 |
| g of `carve_c2048` | `070a4b08…` | 0012, and 0012's and 0013's readers |

The two null blocks are derived from the pool. Every runner from 0014 on refuses a builder cache whose y and g (and, from 0021
on, X) are not its sealed `cache_identity`. The runners from 0018 on also refuse a pool whose hash is not the sealed one. All of
these preregistrations are frozen except 0025.

What a reader can and cannot re-verify now, for the frozen ones:
- **Re-read:** everything, unchanged. Every frozen reader reads banked artifacts, not the cache.
- **Re-run under the frozen protocol:** nothing that touches the builder cache. Each frozen runner refuses a rebuilt cache at
  its identity check, and no reorder recovers the banked order: nothing banked fixes the order of the 1039 batches that hold
  no evaluation chunk (about 2^1257 admissible orders remain), and `tools/prereg_gen/0025/reorder_cache.py`'s documented order
  gives g `82b87d8b…` on any complete rebuild, not the banked `eda31b7c…` (computed from the real y and g structure; no rebuilt
  cache has been reordered yet). A run with that check removed is not the frozen protocol.
- **The evaluation rows,** scored by every preregistration from 0014 to 0024: their chunks are a set, and their order is
  banked (`eval_chunk_layout`, `eval_y_sha256`, `eval_g_sha256`). So a rebuilt cache can be put back into an order that yields
  them in the banked sequence. No banked hash covers their features except the lost X, so their content can be shown only by
  behaviour. 0021's recipes are refitted on 0021's fit block (a real-content corpus, rebuilt identical on 2026-10-21) and
  scored on the rebuilt evaluation rows. Their per-example correctness vectors are compared with the banked vectors, which
  agree hash for hash across 0021, 0022, 0023 and 0024. That proof (`tools/prereg_gen/0025/cache_content_proof.py`) compares
  each row's 0/1 correctness, not its features, so it catches gross content errors and is not a byte-equality proof. It has
  not been run on a rebuilt cache: the cache was not rebuilt on 2026-10-21/22, because the rebuild of realfit2 (the next
  entry) showed this container does not reproduce every banked feature byte. Its control part - 0021's B-feat1, D1 and L3
  refitted on 0021's fit block and scored on the sealed extension rows - reproduces the banked vectors exactly here. For 0022,
  0023 and 0024, which fit only on real-content corpora, the evaluation rows are the whole of their dependence on the builder
  cache.
- **Pool rows:** nothing. Every fit on a builder pool was made on rows nobody can now identify, ourselves included:
  - 0003's four rungs and 0006, on `full_c4096`;
  - 0007 on `carve_c1024` and 0011 on `carve_c2048`, each with a matched model fitted on `full_c4096`'s pool;
  - 0012 on `carve_c2048`;
  - 0014's roster, 0015's and 0017's folds, 0016's family budgets, and 0018's pool fits and null block, on `full_c4096`;
  - 0020's and 0021's reproduction and builder-matched blocks, with 0021's sealed collision-row hashes, on `full_c4096`.

  The only exceptions are 26 pool rows in five batches whose absolute positions `artifacts/pivot/builder_duplicate_chunks.json`
  banks. Those results stand as banked. A rebuild can re-measure them on a different draw of the same design but cannot
  re-derive them on the same rows. The three coverage claims named above would return a re-measurement, not the banked number;
  that includes 0003's headline slope.

**Size:** Six of the twelve arrays the manifest banks were claimed "proven identical" and cannot be reproduced by any rebuild:
X and g of three of its four corpora (X is 1300000 × 1108 float32 for one and 650000 × 1108 for the other two). The claim held
for y in all four corpora and for `raw_c1024` whole. Fifteen preregistrations seal or carry hashes of the lost orders (0011 to
0025): fourteen are frozen, and 0025 is unfrozen; its re-seal waits on a rebuilt cache. Every verdict and every banked number stands: each was measured
on the banked caches, and each reader reads banked artifacts. What moves is what a stranger can re-derive. "Rebuild and check
the hashes" becomes: rebuild the rows as a set, recover the evaluation rows' banked order from banked layouts, show their
content by behaviour, and re-measure every builder-pool result on a different draw of the pool, never on the same rows.

**Cause:** `build()` was written for memory (one preallocated copy) and speed (a Pool). `corpus_manifest.py` was written
afterwards to hash whatever was on disk, and its proof was never run against a second build. So a row order no second build
could produce was banked as content, then sealed, hash by hash, into every preregistration that read the cache. The evidence
sat in the manifest from the day `raw_c1024` and `carve_c1024` were banked beside each other (the same chunks, the same y, two
different g), and nobody compared them. The later builders were written knowing the hazard: `corpus_ext.build()` sorts its rows
by chunk id and label "so the arrays do not depend on worker scheduling", and its `--probe` shuffles the task order to prove it.
That lesson was never applied back to `run_study.build()`. The CI determinism probe sorted the same hazard out of its own
assembly (the CI-probe entry of this date). The cold-clone entry of this date, filed hours earlier, treated a cold clone's
failure to rebuild the builder cache as a fetch problem, because the fetch failed first.

**Fix:**
1. `run_study.build()` is not changed. This follows cold-clone audit D1, recorded in `tools/ci/determinism_probe.py` at
   27a61aa: "a different behaviour would make the banked corpora impossible to reason about".
2. For 0025 (unfrozen):
   - `tools/prereg_gen/0025/reorder_cache.py` (committed ea495ac) writes the rebuilt cache in a documented order
     that depends only on the cache's chunk-id set and the preregistration. Batches are kept whole, evaluation batches come in
     the order of the sealed `eval_chunk_layout`, and each evaluation-free batch follows its id-predecessor. By its own
     docstring, this puts the five batches with banked positions at those positions. It asserts that `grouped_split` then
     returns the evaluation rows with the sealed `eval_y_sha256`, `eval_g_sha256` and chunk layout, and that the output holds
     exactly the input's rows.
   - `tools/prereg_gen/0025/cache_content_proof.py` (committed 9f33d6b, hardened 4dda925) is the behavioural content proof
     described above, with M1 added to sharpen it. Its control is the extension rows, whose bytes are sealed. Not yet run on a
     rebuilt cache (see above).
   - `tools/prereg_gen/0025/amend_cache_0025.py` refuses unless that proof passed on the same cache (its whole-cache hashes
     and its digest of the evaluation rows' features are recomputed) and the order proof holds. It then replaces
     0025's `cache_identity` X and g, the evaluation-row position hash and the three pool hashes wherever they stand. It keeps
     each banked value beside its replacement as `*_banked_2026_08` and records the change under `amendments_before_freeze`.
   - `tools/prereg_checks/prefreeze_0025.py` accepts a rebuilt cache only with those records in place and the cache on disk
     hashing to them.
   - 0025 scores the evaluation rows and fits nothing on the pool. Its re-sealed pool is a different set of rows, and nothing
     in 0025 reads it.
3. 0011 to 0024 are frozen and are not edited; this entry is their record. The CI-probe entry of this date said this entry would be filed with the cache's content
   proof; it is filed without it, because the cache was not rebuilt (above).
4. The published sentences that said a rebuilt corpus is proven identical were rewritten with the entry of this date on
   the manifest sentences, which lists each change; the `oob4096` mutation-gate case that recomputed 0019's null block
   whenever a cache was present now recognises a rebuilt cache by its g and says the recomputation cannot run on it (5e86c5f).
   Left as banked, superseded by this entry: the `why` field of `artifacts/pivot/corpus_manifest.json` and the comment in
   `tools/pivot/source_pins.json` (both are hashed inputs; rewriting their prose would change banked bytes).

## 2026-10-21 — Said the CI determinism probe proves the property the real corpus build's parallelism depends on; it never ran the real build, and the sort in its own assembly hid the row order that makes the builder caches unrebuildable

**Claimed:** CI runs `tools/ci/determinism_probe.py` as "Corpus determinism probe (small slice built twice + order-shuffled,
hashes must match; refuses without source bytes)" (`.github/workflows/verify.yml`). The probe's module docstring set it beside
the manifest's proof: "The full corpora (gigabytes) are banked by content hash in tools/pivot/corpus_manifest.py, but that proof
has only ever been executed on the machine that built them. This probe manufactures a SMALL corpus slice twice in the CI
container". It went on: "It also proves the property the real build's parallelism depends on: run_study.py's build() feeds a
multiprocessing Pool with imap_unordered, so per-chunk generation MUST be order-independent [...] Build 3 therefore manufactures
the same chunks in REVERSED order, reassembles them in canonical order, and must reproduce the same hashes." `build_slice()`'s
docstring called its sorted assembly "exactly the invariant that makes the real build's imap_unordered pool safe." The text
stood from at least 2026-09-03 (the board review repaired the probe's zero-source-bytes defect that day, item 9 of that day's
board-review entry; this clone's history begins at 4ca1ca5, 2026-09-16, where the text is as quoted) until 27a61aa (2026-10-21).

**Actual:** The probe never called `run_study.build()`, never started a Pool and never called `imap_unordered`. It called the two
per-chunk primitives (`corpus.chunk_fragments`, `features.features_many`) in a plain loop over 40 chunks at offset 900400, three
times, assembled each build's blocks in sorted chunk-id order - a step the real build does not have - and compared the three
builds' X, y and g hashes with each other. That shows a chunk's rows depend only on its index, within one process in one
container: necessary for a parallel build to be reproducible, not sufficient. `build()` writes rows in batch-completion order
and never sorts, so the X and g of the three caches it wrote (`full_c4096`, `carve_c1024`, `carve_c2048`) cannot be rebuilt, and
the probe's sort removed exactly that difference before anything was hashed. It passed while the property it was cited for was
false for every cache `build()` has written. It never covered the builder cache in any form: no line of it ran the code that
orders the cache's rows; its chunks lie outside every banked corpus by design; and it compared a build only with another build
in the same container, never with a banked hash, so it did not execute the manifest proof it was set beside, on any machine. The
probe that does exercise its builder was already in the repository: `tools/pivot/corpus_ext.py --probe` runs 0018's real
`build()`, Pool and all, with the task order shuffled and that builder's own sort in place
(`artifacts/pivot/engineering_log_0018.json`, `determinism_probe`).

**Size:** One CI gate's stated coverage, from "the property the real build's parallelism depends on" to a property of two
per-chunk functions in one process: it covered none of the three caches `build()` wrote. No number moves; the probe's three
comparisons were right about what they compared. The claim stood for at least seven weeks.

**Cause:** The probe sorts its blocks so that builds in different manufacture orders can be compared - the right construction
for a probe of per-chunk determinism - and its docstring then credited the sort's guarantee to a build that does not sort. A
check that supplies the property it is meant to test cannot see that property missing: the class in `docs/OPERATING_RULES.md`
§4 and in the 2026-09-03 entry on 0012's gate, here between a probe and the code it names. The 2026-09-03 board review read the
probe closely enough to find that it ran with no source bytes, and did not ask whether it ran the build at all. Found by the
cold-clone audit (D1) on 2026-10-21, when the builder cache had to be rebuilt.

**Fix:** At 27a61aa both docstrings were rewritten to say what the probe does not prove (comments only). Now: the module's first
line and the paragraph that set it beside the manifest say what it checks and that it compares no banked hash; the CI step is
renamed "Per-chunk determinism probe (small slice built three ways + the real build()'s rows as a set; not the manifest proof;
refuses without source bytes)"; and a fourth build calls `run_study.build()` itself, with a Pool of 2 processes, on the probe's
slice and requires its rows, sorted by chunk id and label, to be byte-identical to the canonical assembly - the property the
real build does have - and prints whether its own row order was canonical. On its first run here (2026-10-21) the four builds'
sorted rows were identical and the real build's own order was not canonical: the builder-cache row-order defect the cold-clone
audit (D1) found, shown by the gate that had stood in for it (that defect's own entry is filed with the cache's content proof).

## 2026-10-21 — A cold clone could not rebuild the corpora 0018 to 0025 rest on: one fetch script never worked, and two more Gutenberg books were re-edited

**Claimed:** "Corpora rebuild deterministically from shipped sources and generators; the manifest banks content hashes of every
array so the rebuild is *proven* identical, not assumed" (`docs/DILIGENCE.md`); the fetch scripts' own headers, which say every
file is fetched and checked against its pins before any chunk is cut (`tools/pivot/fetch_ext_sources.sh`, `fetch_sources.sh`).

**Actual:** On 2026-10-21 this work moved to a fresh container with nothing under `data/` and ran the documented fetches.
Two of them failed. (1) `tools/pivot/fetch_ext_sources.sh` asked rfc-editor.org for `rfcrfc1034.txt`: the pins in
`tools/pivot/ext_source_pins.json` are keyed `rfc/rfc1034.txt` and the script stripped only `rfc/`. Both files entered the
repository in the same commit (4ca1ca5, 2026-09-16), so the script never fetched an RFC on a cold machine; the extension corpus
of 0018 had been built from files fetched before the script existed. Every corpus downstream of it (0020 to 0025) inherited a
rebuild path that stopped at the first RFC. (2) `tools/pivot/fetch_sources.sh` failed its pin check on `pg1952.txt` and
`pg2701.txt`: gutenberg.org now serves editions other than the banked ones (sha256 `a40cdaa3…` and `f12eb530…` against the banked
`0604e2f8…` and `0670d7bb…`), and neither re-edit is one of the line edits `tools/pivot/source_pins.json` records. The pin check
failed loudly, as the 2026-09-02 entry designed it to, but there was no way through it. The banked measurements are untouched:
they were made on the banked bytes.

**Size:** one fetch script of four, broken for every cold clone since it was written; two of ten Gutenberg sources; the whole
reproducibility claim for 0018's extension corpus and every real-content corpus built beside it, and for the builder cache.

**Cause:** the fetch script was written after the corpus it fetches for had been built, and was never run on an empty machine;
the corpus manifest checks are run at the end of a build, so a fetch that fails first is never reached by them. The Gutenberg
drift is the one this ledger already predicted on 2026-09-02.

**Fix:** `fetch_ext_sources.sh` takes the RFC number from the file name (`k.split('/')[-1][3:-4]`); run on the fresh container it
fetched all 79 RFCs and `corpus_ext.py --verify-pins` reported every pinned file byte-identical. The banked editions of pg1952 and
pg2701 were found byte for byte (full sha256 equal to the banked values) in a third-party repository, and `fetch_sources.sh` now
falls back to those commit-pinned URLs only when Gutenberg's file does not hash to the banked value and the copy does;
`pin_sources.py` remains the final arbiter. Tested on a scratch copy with both books deleted: Gutenberg served the new editions,
the fallback restored the banked ones, `SOURCE PINS: PASS`. Every corpus rebuilt on this container is checked against its banked
manifest before any preregistration uses it. A third party can delete or rewrite its repository; if that happens the rebuild
fails loudly again and will be filed here again.

---

## 2026-09-23 — Described 0024's RFC sampling frame as "every RFC the index lists"; the parser had skipped RFCs 1 to 999 and five wrapped annotations

**Claimed.** `docs/compliance/EXT_SOURCES2.md` (rfc_txt row), `tools/pivot/ext_source_pins2.json`
(`rfc_source.sample`) and `docs/compliance/sources/MANIFEST.json` (the rfc-index entry): the 0024 RFC sample was
"a seeded sample over the 7838 RFCs the RFC Editor's index lists as issued with a TXT format, not pinned by 0018,
and not related to a 0018-pinned RFC by an Obsoletes, Obsoleted by, Updates or Updated by annotation in either
direction (323 numbers so excluded)"; the MANIFEST note put the issued-TXT count not pinned by 0018 at 8117.

**Actual.** The sampling script (a scratchpad file, since deleted) parsed the index with a four-digit entry pattern
and a four-digit `RFCnnnn` pattern. The index writes RFCs 1 to 999 without zero padding and writes the numbers
inside annotations without padding too, and it wraps long annotations onto a second line. Rebuilding the parser
from the documented rule for preregistration 0025 (`tools/pivot/ext_source_pins3.json`, `rfc_source.sample`) and
checking it against 0024's banked lists on the index as served 2026-09-23 shows: (1) every entry numbered below
1000 was outside 0024's frame, so "every RFC the index lists" was "every RFC numbered 1000 and above"; (2) five
RFCs whose `(Updates RFC...)` annotation wraps a line - 5761 (updates 3550), 7111 (updates 4180), 7160 (updates
3550), 8573 (updates 5905) and 9673 (updates 8200), each naming a 0018-pinned RFC - were not excluded as related,
and two RFCs below 1000 (760, obsoleted by 791; 761, obsoleted by 793) were neither in the frame nor in the
exclusion list; (3) RFC 9999 was banked as related although the index carries no such annotation today (a change
in the index, or a parser artefact; COULD NOT VERIFY, the 2026-09-17 index text was hashed but not kept).
None of the 600 RFCs 0024 drew is related to a 0018 pin under the corrected parser, so 0024's sample satisfies
its stated rule; the frame it was drawn from was smaller than stated, and its exclusion count was five short.

**Size.** The frame: 7838 stated against about 8800 under the corrected rule on the same index (the exact count
for the 2026-09-17 index cannot be recomputed; on the 2026-09-23 index the corrected rule gives 9427 candidates
before removing 0024's 600, of which about 950 are RFCs below 1000 and about 40 were issued since). The exclusion
list: 323 stated, 329 under the corrected parser (five wrapped annotations and RFC 760/761 added, 9999 removed).
No 0024 number moves: the drawn files, the corpus, the readings and the verdict are unchanged; what was wrong is
a sentence about how the files were chosen.

**Cause.** A regex written for the modern four-digit entries, tested on the numbers it was written for, and
reported as "every RFC". The same failure class as the 2026-08-25 allocation-flag entry: a heuristic mistaken for
the rule it approximates, caught only because 0025 re-implemented the rule and diffed the result against the
banked lists rather than reusing the code.

**Fix.** 0025's sampler (`rfc_source.sample` in `ext_source_pins3.json`) parses one-to-five-digit entry numbers
and unpadded annotation numbers, joins wrapped annotation lines, and banks the frame size, the exclusion list and
the candidate list's sha256 from the index as served, which is hashed in `docs/compliance/sources/MANIFEST.json`;
its validation against 0024's banked lists is recorded in `artifacts/pivot/engineering_log_0025.json`. The 0024
documents keep their sentence with a pointer to this entry (`docs/compliance/EXT_SOURCES2.md`, rfc_txt row).

---

## 2026-09-17 — Said three gates were still owed the section-4 treatment; six gate names behind five builders were, and every one of them was missing runner-written fields at three levels

**Claimed.** `CORRECTIONS.md` 2026-09-16, "Size": "Four gates of twenty-two build their controls
this way (`oob4096`, and three siblings whose docstrings say so, plus `realfit4096`)", and "Fix":
"the remaining three gates are owed the same." `artifacts/pivot/engineering_log_0019.json` filed
the same count as an open follow-up: "the oob4096 gate ... and three sibling gates do the same".

**Actual.** Six gate names take their controls from reader literals: `recipe2048` and `recipe4096`
(one builder, `_good_recipe2048`, in two configurations), `lofo4096`, `fdc4096`, `lofol3` and
`oob4096`. Measured on 2026-09-17 before any of them changed, each control as built at commit
`2c29021` against the banked runner artifact its reader read
(`artifacts/verification/gate_controls_before_fix.json`): every fit record the six controls wrote
lacked 6 to 8 fields the runner writes (`heartbeat_max_rss_gb`,
`last_heartbeat_rss_gb_before_this_fit`, `rss_gb`, `ru_maxrss_gb`, `utc`; `rss_gb_is` and
`rss_total_gb` from the later runners; `interruptions_before_this_fit` in the recipe gates) — 50 of
50 records in each recipe gate, 27 of 27 in `lofo4096`, 258 of 258 in `fdc4096`, 10 of 10 in
`lofol3`, 4 of 4 in `oob4096`. Every partition lacked 1 to 5 (`holdout_chunks_per_family`;
`eval_frac`, `seed`, `split_is_grouped_by_source`, `top_rung`;
`every_block_carries_all_classes_in_fit_and_validation_rows`; `row_identity_digest`). The top level
lacked 1 to 6 (`cluster_ci95_note` in all six; `launch_environment`, `launch_number`,
`best_frozen_non_gutenberg_for_bar`, `best_frozen_non_gutenberg_searched` and
`best_expanded_non_gutenberg_head` in the recipe gates; `fit_record_top1_is` in `oob4096`). No
control carried a key the runner does not write, and every value a reader seals matched the banked
artifact except the one already filed (0018's null-block hash, entry of 2026-09-10) — which is the
defect this construction could not see, and the six gates were green through all of it. The eight
earlier reader gates (`pivot-curve` through `byteflat`) never import their readers' constants and
are not in the class.

**Size.** Two gate names and one builder: "the remaining three" was five builders behind six names,
so "four gates of twenty-two" was six of twenty-two before `realfit4096` is counted. The 2026-09-16
entry was written the day before this one, from which docstrings mentioned the construction rather
than from a measurement. No published number moved: the controls' values were the sealed ones
either way, and the readers read the same banked artifacts either way.

**Cause.** The count was taken from a docstring grep. `recipe2048` and `recipe4096` share one
builder whose docstring says nothing about where its blocks come from, so the grep could not see
them, and the one entry that undercounted was the entry filing the class.

**Fix.** Every one of the six controls now takes its shape from the banked runner artifact its
reader read (`_BANKED_SHAPE` in `tests/mutation_test.py`): `partition`, `corpus` and `ext_corpus`
through `_rf_sub` (sealed values into the runner's key set, refusing any key the runner never
wrote), every fit record through `_rf_sub` against the runner's own record at the same place in the
artifact, and the top level and the selection document through `_shape_fill`, which carries every
runner-written key the control does not set at its banked value and refuses any invented key. One
pass/fail pair per gate — `the-control-artifact-is-built-from-the-banked-runner-output-shape` and
`a-control-whose-partition-is-the-readers-own-literals-is-detected` — checks both directions at the
top level, in every block and in every fit record, and that every key a reader seals is one the
runner writes; the fail case rebuilds the partition the old way and must be refused. The suite goes
from 463 cases to 475. The 0019 follow-up is closed, and `docs/OPERATING_RULES.md` §4 records that
the rule now holds for every reader's gate. Under 0018's reader the control still carries 0018's
wrong null-block literal, on purpose: that is the value the reader disagrees with the world on, and
the case `0018s-frozen-reader-VOIDs-the-runners-null-block` is where the disagreement is shown.

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
