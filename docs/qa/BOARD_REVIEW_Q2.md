# Board review — second quarter (2026-09-03)

**What was reviewed.** Every deliverable of the quarter, at `main` = the PR #2 merge commit: the
compliance follow-up (`docs/compliance/LICENSE_AUDIT.md` §5 and `sources/`), the four 2026-09-02
correction entries, source pinning (`tools/pivot/pin_sources.py`), preregistration 0011 end to end
(prereg, frozen reader, measurement script, cluster-bootstrap fitter, artifacts, mutation gates),
every document that quotes the 2048 result, and the public mirror.

**How.** Five department reviewers (compliance, statistics, reproducibility, research QA, public
mirror), each hunting defects in its own deliverables with file:line evidence; two board refuters
per finding, instructed to kill anything wrong, vague, already disclosed, or not a defect on reading
the code; a finding survives only if both decline. 77 agents. Record:
`artifacts/verification/board_review_q2.json` (titles of every confirmed and rejected finding).

**Result.** 36 raised, 29 confirmed, 7 rejected. The 29 collapse to nine distinct defects, each
filed in `CORRECTIONS.md` (2026-09-03) and fixed in the same commit. The ones that matter most:

- a baseline misattributed in VERDICT (depth-8 quoted as depth-16 at 1024);
- "a pass on csv and log masked by the incompressible families" overstated what the artifact
  supports — the mixture misses even without those families (+0.0478 against the binding bar);
- the outbound documents quoted the slackest failed clause (0.0025) as the miss, when the binding
  reading misses by 0.0206;
- the CI determinism probe had been passing with zero source bytes, so one of eight families was
  silently synthetic in every CI run;
- the Lingeling finding answered a legal question in the repository's favour; it is now
  COULD NOT VERIFY.

**What the seven rejected findings were.** Listed in the artifact. Two are worth reading anyway:
one argued the logistic baseline's non-convergence warning should be disclosed (the refuters found
sklearn's warning is about the optimiser's iteration cap, the banked accuracy is what that solver
returned, and 0007 had the same warning); one argued the scaling gate never exercises the cluster
branch (it does: `control-clustered-rows-widen-the-interval-and-it-is-labelled-cluster`).

**What this review could not do.** Judge whether the boundary bracket, the near-miss framing or the
decomposition would persuade a buyer. No reviewer here is a buyer, and none was asked to pretend.
