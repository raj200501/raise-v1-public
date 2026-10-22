#!/usr/bin/env bash
# build_mirror.sh - rebuild the public, history-filtered mirror of raise-v1.
#
#   bash build_mirror.sh <out-dir>
#   cd <out-dir> && git push -f public main        # publish (run by the operator, never by this script)
#
# What the mirror is (README.md "Public mirror"; the mirror's docs/PUBLIC_MIRROR.md; LICENSE_AUDIT.md 5.4):
#   * the private repository's main, with its history rewritten by `git filter-branch` so that
#       1. the four GNSS product files untracked on 2026-09-02 (data/gnss/brdc001.rnx.gz, brdc_001.rnx.gz,
#          clk_001.CLK.gz, sp3_001.SP3.gz; added in 6ed8a6d and b185129) are absent from every commit, and
#       2. the e-mail address in file contents (the fetch.sh user-agent and the NEW_DOCS_REVIEW.md byline)
#          is replaced by a placeholder in every commit;
#     authors, committers, dates, messages and commit order are untouched (commit signatures are dropped by
#     the rewrite), so the filtered history is deterministic: commits already published keep their hashes;
#   * plus one commit on top, authored by the repository owner: docs/PUBLIC_MIRROR.md (the note, with the
#     preregistration commit table), docs/public_mirror_commit_map.json (every private commit -> mirror
#     commit), a README banner, and a one-line comment at the top of .github/workflows/verify.yml.
#
# The script never writes to the source repository (it clones it, and if the clone is shallow deepens it from
# the source's own origin URL). It refuses to write into a directory it did not create. It verifies the result
# before it finishes, and exits non-zero if anything is off. It never pushes.
#
# Environment overrides: SRC_REPO (default: the checkout this script is in), SRC_REF (main), OWNER_EMAIL, MIRROR_TRAILER,
# PUBLIC_URL (https://github.com/raj200501/raise-v1-public.git), ALLOW_PUBLISHED_REWRITE=1 to accept a result
# that would change commits the published mirror already carries.
set -euo pipefail

OUT_ARG=${1:?usage: bash build_mirror.sh <out-dir>}
SRC_REPO=${SRC_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}
SRC_REF=${SRC_REF:-main}
PUBLIC_URL=${PUBLIC_URL:-https://github.com/raj200501/raise-v1-public.git}
ALLOW_PUBLISHED_REWRITE=${ALLOW_PUBLISHED_REWRITE:-0}

OWNER_NAME="raj200501"
# The owner's address is read from the source history (the owner's own commits), never written in this file: the mirror
# replaces it in EMAIL_FILES, and its scan requires it to appear in those files only.
OWNER_EMAIL=${OWNER_EMAIL:-$(git -C "$SRC_REPO" log -1 --author="^$OWNER_NAME <" --format=%ae "$SRC_REF" 2>/dev/null || true)}
[ -n "$OWNER_EMAIL" ] || { echo "build_mirror: ERROR: set OWNER_EMAIL (no commit by $OWNER_NAME on $SRC_REF)" >&2; exit 1; }
FILTER_EMAIL=${FILTER_EMAIL:-$OWNER_EMAIL}
EMAIL_PLACEHOLDER="<contact: see the repository owner>"
GNSS_PATHS="data/gnss/brdc001.rnx.gz data/gnss/brdc_001.rnx.gz data/gnss/clk_001.CLK.gz data/gnss/sp3_001.SP3.gz"
EMAIL_FILES="docs/qa/NEW_DOCS_REVIEW.md tools/gnss/fetch.sh tools/publish/build_mirror.sh"
STAMP=build_mirror.stamp

die() { echo "build_mirror: ERROR: $*" >&2; exit 1; }
say() { echo "build_mirror: $*" >&2; }

command -v git >/dev/null || die "git not found"
command -v python3 >/dev/null || die "python3 not found"
git -C "$SRC_REPO" rev-parse --git-dir >/dev/null 2>&1 || die "$SRC_REPO is not a git repository"
SRC_SHA=$(git -C "$SRC_REPO" rev-parse --verify --quiet "refs/heads/$SRC_REF^{commit}") \
  || die "$SRC_REPO has no branch $SRC_REF"
SRC_TOP=$(cd "$SRC_REPO" && git rev-parse --show-toplevel)

# ---- output directory: only ever a fresh one, or one this script built before ---------------------------
OUT=$(python3 -I -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$OUT_ARG")
OUT_REAL=$(python3 -I -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$OUT")
SRC_REAL=$(python3 -I -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$SRC_TOP")
case "$OUT_REAL/" in "$SRC_REAL/"*) die "output $OUT is inside the source repository $SRC_REAL";; esac
case "$SRC_REAL/" in "$OUT_REAL/"*) die "output $OUT contains the source repository $SRC_REAL";; esac
if [ -L "$OUT" ]; then die "$OUT is a symlink; give a real directory path"; fi
if [ -e "$OUT" ]; then
  if [ -d "$OUT" ] && [ -z "$(ls -A "$OUT")" ]; then
    rmdir "$OUT"
  elif [ -f "$OUT/.git/$STAMP" ]; then
    say "removing the previous mirror build at $OUT"
    rm -rf -- "$OUT"
  else
    die "$OUT exists and is not a previous build_mirror output (no .git/$STAMP); refusing to touch it - pick another path"
  fi
fi

WORK=$(mktemp -d "${TMPDIR:-/tmp}/build_mirror.XXXXXX")
trap 'rm -rf -- "$WORK"' EXIT
mkdir -p "$(dirname "$OUT")"

# ---- 1. fresh, full-history clone of the source branch ------------------------------------------------
say "cloning $SRC_REPO ($SRC_REF = $SRC_SHA) into $OUT"
git clone -q --no-local --no-tags --single-branch --branch "$SRC_REF" -- "$SRC_REPO" "$OUT"
echo "built by build_mirror.sh from $SRC_REPO $SRC_REF $SRC_SHA" > "$OUT/.git/$STAMP"
g() { git -C "$OUT" -c commit.gpgsign=false "$@"; }
[ "$(g rev-parse HEAD)" = "$SRC_SHA" ] || die "clone HEAD differs from $SRC_REPO $SRC_REF"
if [ "$(g rev-parse --is-shallow-repository)" = true ]; then
  ORIGIN_URL=$(git -C "$SRC_REPO" remote get-url origin 2>/dev/null) || die "source is shallow and has no origin to deepen from"
  say "source clone is shallow; fetching the full history of $SRC_REF from $ORIGIN_URL (read only)"
  g fetch -q --unshallow --no-tags "$ORIGIN_URL" "$SRC_REF"
  [ "$(g rev-parse --is-shallow-repository)" = false ] || die "history is still shallow after --unshallow"
fi
g remote remove origin            # the mirror must never point back at the private repository
g fsck --connectivity-only --no-progress "$SRC_SHA" >/dev/null || die "history of $SRC_SHA is incomplete"
PRIVATE_COUNT=$(g rev-list --count "$SRC_SHA")
say "private $SRC_REF: $PRIVATE_COUNT commits"

# ---- 2. scan: the exact items to remove, and fail closed if history holds anything the note does not say --
cat > "$WORK/mirror_helper.py" <<'PYEOF'
import json, os, subprocess, sys

REPO = os.environ["OUT"]
EMAIL = os.environ["FILTER_EMAIL"].encode()
PLACEHOLDER = os.environ["EMAIL_PLACEHOLDER"].encode()
GNSS = set(os.environ["GNSS_PATHS"].split())
EMAIL_FILES = set(os.environ["EMAIL_FILES"].split())
WORK = os.environ["WORK"]


def git(*args, inp=None):
    r = subprocess.run(["git", "-C", REPO, "-c", "commit.gpgsign=false", *args], input=inp,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode:
        sys.exit("git %s failed: %s" % (" ".join(args), r.stderr.decode(errors="replace")))
    return r.stdout


def fail(msg):
    sys.exit("build_mirror: VERIFY FAILED: " + msg)


class Cat:
    def __init__(self):
        self.p = subprocess.Popen(["git", "-C", REPO, "cat-file", "--batch"], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE)

    def get(self, sha):
        self.p.stdin.write(sha.encode() + b"\n"); self.p.stdin.flush()
        hdr = self.p.stdout.readline().split()
        if len(hdr) < 3:
            fail("object %s missing" % sha)
        data = self.p.stdout.read(int(hdr[2])); self.p.stdout.read(1)
        return hdr[1].decode(), data


def tree_entries(commit):
    out = git("ls-tree", "-r", "-z", "--full-tree", commit).split(b"\0")
    ents = {}
    for e in out:
        if not e:
            continue
        meta, path = e.split(b"\t", 1)
        mode, typ, sha = meta.decode().split()
        ents[path.decode("utf-8", "surrogateescape")] = (mode, typ, sha)
    return ents


def parse_commit(raw):
    head, _, msg = raw.partition(b"\n\n")
    fields = {"parent": []}
    cont = None
    for line in head.split(b"\n"):
        if line.startswith(b" ") and cont:
            continue                      # continuation of a multi-line header (gpgsig, mergetag)
        k, _, v = line.partition(b" ")
        k = k.decode(); cont = k
        if k == "parent":
            fields["parent"].append(v.decode())
        else:
            fields[k] = v
    return fields, msg


def scan(rev):
    """Find every blob holding the address and every path under data/gnss/ anywhere in rev's history."""
    commits = git("rev-list", rev).decode().split()
    blob_paths, gnss_seen = {}, set()
    for c in commits:
        for path, (mode, typ, sha) in tree_entries(c).items():
            if typ == "blob":
                blob_paths.setdefault(sha, set()).add(path)
            if path.startswith("data/gnss/"):
                gnss_seen.add(path)
    cat = Cat()
    hits = {}
    for sha in blob_paths:
        _, data = cat.get(sha)
        if EMAIL in data:
            hits[sha] = data
    email_paths = set().union(*(blob_paths[s] for s in hits)) if hits else set()
    if gnss_seen != GNSS:
        fail("paths under data/gnss/ in history are %s, the note says exactly %s; update the script and the note"
             % (sorted(gnss_seen), sorted(GNSS)))
    if email_paths != EMAIL_FILES:
        fail("the address appears in %s, the note says exactly %s; update the script and the note"
             % (sorted(email_paths), sorted(EMAIL_FILES)))
    for c in commits:
        if EMAIL in parse_commit(cat.get(c)[1])[1]:
            fail("the address appears in the message of commit %s (the mirror keeps messages unchanged)" % c)
    with open(os.path.join(WORK, "blobmap"), "w") as f:
        for old, data in sorted(hits.items()):
            new = git("hash-object", "-w", "--stdin", inp=data.replace(EMAIL, PLACEHOLDER)).decode().strip()
            f.write("%s %s\n" % (old, new))
    print("scan: %d commits; %d blob(s) with the address in %s; GNSS paths %s"
          % (len(commits), len(hits), sorted(email_paths), sorted(gnss_seen)), file=sys.stderr)


def load_map():
    m = {}
    for line in git("cat-file", "blob", "refs/build-mirror/state:filter.map").decode().split():
        old, new = line.split(":")
        m[old] = new
    return m


def verify_history(src, filtered):
    """Commit by commit: same metadata and message, parents mapped, tree = original minus GNSS, address replaced."""
    m = load_map()
    blobmap = dict(l.split() for l in open(os.path.join(WORK, "blobmap")))
    order = git("rev-list", "--reverse", "--topo-order", src).decode().split()
    if m.get(src) != filtered:
        fail("filter map does not take %s to %s" % (src, filtered))
    if set(order) - set(m):
        fail("%d private commits have no mirror commit" % len(set(order) - set(m)))
    mirror_order = git("rev-list", "--reverse", "--topo-order", filtered).decode().split()
    if mirror_order != [m[c] for c in order]:
        fail("mirror history is not the private history commit for commit, in order")
    cat = Cat()
    for c in order:
        n = m[c]
        (of, omsg), (nf, nmsg) = parse_commit(cat.get(c)[1]), parse_commit(cat.get(n)[1])
        for k in ("author", "committer"):
            if of[k] != nf[k]:
                fail("%s %s: %r != %r" % (c, k, of[k], nf[k]))
        if omsg != nmsg:
            fail("%s: message changed" % c)
        if of.get("encoding") != nf.get("encoding"):
            fail("%s: encoding header changed" % c)
        if [m[p] for p in of["parent"]] != nf["parent"]:
            fail("%s: parents not mapped" % c)
        expect = {}
        for path, (mode, typ, sha) in tree_entries(c).items():
            if path in GNSS:
                continue
            expect[path] = (mode, typ, blobmap.get(sha, sha))
        if tree_entries(n) != expect:
            fail("%s -> %s: tree is not the original minus the GNSS files with the address replaced" % (c, n))
    out = {c: m[c] for c in order}
    with open(os.path.join(WORK, "commitmap.json"), "w") as f:
        json.dump({"private_main": src, "mirror_main": filtered, "map_private_to_mirror": out}, f, indent=1)
    print("history: %d commits verified one to one (authors, committers, dates, messages, parents, trees)"
          % len(order), file=sys.stderr)


NOTE_HEAD = """# Public mirror — what this repository is, and what was filtered

This repository is the public mirror of the private working repository `raj200501/raise-v1`,
regenerated from its `main` branch. Every measurement, artifact, preregistration, reader, gate,
correction and document is identical to the private repository at the mirrored commit. Two
things were removed from the mirror's **history** with `git filter-branch`, so every commit hash
differs from the private repository's:

1. **`data/gnss/`** — four GNSS product files (5.5 MB) committed in the private repository's
   history and untracked on 2026-09-02: two ESA final orbit/clock products whose redistribution
   terms COULD NOT be verified (`docs/compliance/LICENSE_AUDIT.md` §5.4), and the two copies of a
   BKG-served IGS broadcast file committed alongside them, whose IGS terms the audit records as
   open. All four were removed together so the mirror carries no agency products at all.
   `tools/gnss/fetch.sh` re-fetches them from the agencies for anyone reproducing the EphemErr
   study; the banked artifacts under `artifacts/ephemerr/` are unchanged.
2. **One e-mail address** in three files (a user-agent string, a review byline, and the earlier
   versions of this mirror's own build script, which wrote it out), replaced by a placeholder.

Nothing else differs: same trees otherwise, same authors, same dates, same messages, same order.
The private repository's history is the precedence record the preregistration chain refers to:
each `prereg/*.json` carries the `git_commit` at which it was frozen (`prereg/chain.jsonl` carries
the hash chain - frozen_utc, sealed_sha256, prev_hash - that orders them independently of git),
and those commit hashes are the **private** repository's. The table below maps them to this
mirror's commits so the ordering can be checked here too.

"""

NOTE_TAIL = """
The full map (every commit) is in `docs/public_mirror_commit_map.json`.

The mirror is regenerated from the private `main` after each meaningful step and force-updated (the filtered
history is rebuilt deterministically, but this note's commit is new each time), so a clone of this mirror should
`git fetch` and reset to `origin/main` rather than pull.

`bash tools/gates.sh` runs every gate here exactly as in the private repository; `python3 tools/prereg.py verify`
verifies the chain and the frozen readers' hashes, which do not depend on git history.
"""

BANNER = """> **Public mirror.** This is the public mirror of the private working repository; its history omits four
> GNSS product files (two ESA products whose redistribution terms could not be verified, and the two BKG
> broadcast copies committed with them) and one e-mail address. Everything
> else is identical. Commit-hash map and details: `docs/PUBLIC_MIRROR.md`.

"""

WORKFLOW_LINE = ("# Public mirror: manual runs only (workflow_dispatch); the private repository runs this on "
                 "pushes to main.\n")
ADDED = ["docs/PUBLIC_MIRROR.md", "docs/public_mirror_commit_map.json", "README.md", ".github/workflows/verify.yml"]


def write_additions(built_utc):
    cm = json.load(open(os.path.join(WORK, "commitmap.json")))
    src, filtered, m = cm["private_main"], cm["mirror_main"], cm["map_private_to_mirror"]
    rows = []
    for name in sorted(os.listdir(os.path.join(REPO, "prereg"))):
        if not (name.endswith(".json") and name[:4].isdigit()):
            continue
        d = json.load(open(os.path.join(REPO, "prereg", name)))
        gc = d.get("git_commit")
        if not gc:
            continue                      # not frozen yet: no precedence commit to map
        if gc not in m:
            fail("prereg/%s git_commit %s is not in the private main history" % (name, gc))
        num, slug = name[:-5].split("-", 1)
        rows.append("| %s %s | `%s` | `%s` |" % (num, slug, gc[:12], m[gc][:12]))
    pr1 = [l.split(" ", 1)[0] for l in git("log", "--format=%H %s", src).decode().splitlines()
           if l.split(" ", 1)[1].startswith("Merge pull request #1 from ")]
    if len(pr1) != 1:
        fail("expected exactly one 'Merge pull request #1' commit, found %d" % len(pr1))
    rows.append("| PR #1 merge commit (precedence record) | `%s` | `%s` |" % (pr1[0][:12], m[pr1[0]][:12]))
    note = (NOTE_HEAD
            + "Mirror built %s UTC from private `main` = `%s` → mirror `%s`; %d commits.\n\n"
              % (built_utc, src, filtered, len(m))
            + "| Preregistration | frozen at (private) | same commit here (mirror) |\n|---|---|---|\n"
            + "\n".join(rows) + "\n" + NOTE_TAIL)
    with open(os.path.join(REPO, "docs/PUBLIC_MIRROR.md"), "w", encoding="utf-8") as f:
        f.write(note)
    with open(os.path.join(REPO, "docs/public_mirror_commit_map.json"), "w") as f:
        json.dump(cm, f, indent=1)
    readme = open(os.path.join(REPO, "README.md"), encoding="utf-8").read()
    if readme.startswith("> **Public mirror.**"):
        fail("README.md already carries the mirror banner")
    open(os.path.join(REPO, "README.md"), "w", encoding="utf-8").write(BANNER + readme)
    wf = os.path.join(REPO, ".github/workflows/verify.yml")
    text = open(wf, encoding="utf-8").read()
    if not text.startswith("name: verify\n"):
        fail(".github/workflows/verify.yml no longer starts with 'name: verify'; check the mirror comment")
    open(wf, "w", encoding="utf-8").write(WORKFLOW_LINE + text)
    print("note: %d preregistration rows + PR #1" % (len(rows) - 1), file=sys.stderr)


def verify_tip(src, filtered, tip):
    """The tip = private main's tree, minus GNSS, address replaced, plus exactly the four mirror additions."""
    blobmap = dict(l.split() for l in open(os.path.join(WORK, "blobmap")))
    priv, filt, top = tree_entries(src), tree_entries(filtered), tree_entries(tip)
    expect = {p: (mo, t, blobmap.get(s, s)) for p, (mo, t, s) in priv.items() if p not in GNSS}
    if filt != expect:
        fail("filtered tip tree != private main tree minus GNSS with the address replaced")
    changed = sorted(p for p in set(top) | set(filt) if top.get(p) != filt.get(p))
    if changed != sorted(ADDED):
        fail("the mirror commit changes %s, expected exactly %s" % (changed, sorted(ADDED)))
    rest = sorted(p for p in set(priv) | set(top) if priv.get(p) != top.get(p))
    print("tip: differs from private %s only in %s" % (src[:12], rest), file=sys.stderr)
    parents = parse_commit(Cat().get(tip)[1])[0]["parent"]
    if parents != [filtered]:
        fail("mirror commit's parent is %s, expected %s" % (parents, filtered))


def verify_store(tip, gnss_blobs_file):
    """After gc: one ref, and no removed item anywhere in the object store (reachable or not)."""
    refs = git("for-each-ref", "--format=%(refname)").decode().split()
    if refs != ["refs/heads/main"]:
        fail("refs other than main remain: %s" % refs)
    bad_blobs = set(open(gnss_blobs_file).read().split())
    blobmap_old = {l.split()[0] for l in open(os.path.join(WORK, "blobmap"))}
    objs = git("cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype)").decode().split("\n")
    cat = Cat()
    nblob = 0
    for line in objs:
        if not line:
            continue
        sha, typ = line.split()
        if typ != "blob":
            continue
        nblob += 1
        if sha in bad_blobs or sha in blobmap_old:
            fail("removed blob %s is still in the object store" % sha)
        if EMAIL in cat.get(sha)[1]:
            fail("blob %s in the object store contains the address" % sha)
    paths = set()
    for c in git("rev-list", "--all").decode().split():
        paths.update(tree_entries(c))
    leaked = sorted(p for p in paths if p.startswith("data/gnss/"))
    if leaked:
        fail("paths under data/gnss/ reachable in the mirror: %s" % leaked)
    print("store: only refs/heads/main; %d blobs, none removed-GNSS, none with the address; no data/gnss/ path in"
          " any commit" % nblob, file=sys.stderr)


def check_published(published_map_file):
    """Commits the published mirror already carries must come out with the same hashes (deterministic rebuild)."""
    pub = json.load(open(published_map_file))
    ours = json.load(open(os.path.join(WORK, "commitmap.json")))["map_private_to_mirror"]
    common = [c for c in pub["map_private_to_mirror"] if c in ours]
    diff = [c for c in common if pub["map_private_to_mirror"][c] != ours[c]]
    gone = [c for c in pub["map_private_to_mirror"] if c not in ours]
    print("published mirror: built from private %s; %d of its %d mapped commits are in this build, %d with a"
          " different hash, %d no longer in private main"
          % (pub["private_main"][:12], len(common), len(pub["map_private_to_mirror"]), len(diff), len(gone)),
          file=sys.stderr)
    if diff or gone:
        print("DIVERGES", file=sys.stdout)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "scan":
        scan(sys.argv[2])
    elif cmd == "verify-history":
        verify_history(sys.argv[2], sys.argv[3])
    elif cmd == "write-additions":
        write_additions(sys.argv[2])
    elif cmd == "verify-tip":
        verify_tip(*sys.argv[2:5])
    elif cmd == "verify-store":
        verify_store(*sys.argv[2:4])
    elif cmd == "check-published":
        check_published(sys.argv[2])
    else:
        sys.exit("unknown helper command " + cmd)
PYEOF
export OUT WORK FILTER_EMAIL EMAIL_PLACEHOLDER GNSS_PATHS EMAIL_FILES
helper() { python3 -I "$WORK/mirror_helper.py" "$@"; }

helper scan "$SRC_SHA"
# blob ids of the GNSS files, for the post-gc object-store check
for c in $(g rev-list "$SRC_SHA" -- data/gnss); do
  g ls-tree -r "$c" -- $GNSS_PATHS | awk '{print $3}'
done | sort -u > "$WORK/gnss_blobs"

# ---- 3. rewrite: drop the four GNSS paths, swap the address-bearing blobs, keep everything else ----------
export BLOBMAP="$WORK/blobmap"
say "rewriting $PRIVATE_COUNT commits with git filter-branch --index-filter"
FILTER_BRANCH_SQUELCH_WARNING=1 g filter-branch -f \
  --state-branch refs/build-mirror/state \
  --index-filter '
    git rm -q --cached --ignore-unmatch -- $GNSS_PATHS &&
    git ls-files -s | awk -v map="$BLOBMAP" '"'"'
      BEGIN { while ((getline l < map) > 0) { split(l, a, " "); m[a[1]] = a[2] } }
      { tab = index($0, "\t"); split(substr($0, 1, tab - 1), h, " ")
        if (h[2] in m) printf "%s %s %s\t%s\n", h[1], m[h[2]], h[3], substr($0, tab + 1) }
    '"'"' | git update-index --index-info
  ' -- "$SRC_REF" > "$WORK/filter-branch.log" 2>&1 || { tail -20 "$WORK/filter-branch.log" >&2; die "filter-branch failed"; }
FILTERED=$(g rev-parse "refs/heads/$SRC_REF")
[ "$FILTERED" != "$SRC_SHA" ] || die "filter-branch changed nothing"
helper verify-history "$SRC_SHA" "$FILTERED"

# ---- 4. the mirror's own commit: note, commit map, README banner, workflow comment ----------------------
NOW=$(date -u +%s)
BUILT=$(date -u -d "@$NOW" '+%Y-%m-%d %H:%M')
helper write-additions "$BUILT"
g add -- docs/PUBLIC_MIRROR.md docs/public_mirror_commit_map.json README.md .github/workflows/verify.yml
# MIRROR_TRAILER (optional): trailer lines for the mirror commit's message, supplied by the operator at build time.
{ printf 'Public mirror: filtered-history note, commit map, README banner\n'
  [ -z "${MIRROR_TRAILER:-}" ] || printf '\n%s\n' "$MIRROR_TRAILER"; } > "$WORK/msg"
# Authored and committed as the repository owner (contributions count); signed if the user's git config signs.
GIT_AUTHOR_NAME="$OWNER_NAME" GIT_AUTHOR_EMAIL="$OWNER_EMAIL" GIT_AUTHOR_DATE="@$NOW +0000" \
GIT_COMMITTER_NAME="$OWNER_NAME" GIT_COMMITTER_EMAIL="$OWNER_EMAIL" GIT_COMMITTER_DATE="@$NOW +0000" \
  git -C "$OUT" commit -q --no-verify -F "$WORK/msg"
TIP=$(g rev-parse HEAD)
[ -z "$(g status --porcelain)" ] || die "working tree not clean after the mirror commit"
helper verify-tip "$SRC_SHA" "$FILTERED" "$TIP"

# ---- 5. drop everything but main, so the object store holds nothing that was filtered ------------------
g for-each-ref --format='%(refname)' | { grep -v '^refs/heads/main$' || true; } | while read -r ref; do g update-ref -d "$ref"; done
g reflog expire --expire=now --all
g gc -q --prune=now
helper verify-store "$TIP" "$WORK/gnss_blobs"

# ---- 6. compare with what is published (read only) ------------------------------------------------------
PUB=$WORK/published.git
git init -q --bare "$PUB"
if git -C "$PUB" fetch -q --depth=1 --no-tags "$PUBLIC_URL" main 2>"$WORK/pubfetch.log" \
   && git -C "$PUB" show FETCH_HEAD:docs/public_mirror_commit_map.json > "$WORK/published_map.json" 2>/dev/null; then
  PUB_TIP=$(git -C "$PUB" rev-parse FETCH_HEAD)
  say "published mirror main = $PUB_TIP"
  PUB_CHECK=$(helper check-published "$WORK/published_map.json")
  if [ "$PUB_CHECK" = DIVERGES ]; then
    [ "$ALLOW_PUBLISHED_REWRITE" = 1 ] \
      || die "this build would change commits the published mirror already carries; set ALLOW_PUBLISHED_REWRITE=1 if intended"
    say "WARNING: published commits will be rewritten (ALLOW_PUBLISHED_REWRITE=1)"
  fi
else
  say "WARNING: could not read the published mirror at $PUBLIC_URL; determinism check skipped"
  PUB_TIP=unknown
fi

g remote add public "$PUBLIC_URL"
say "done: $OUT main = $TIP ($((PRIVATE_COUNT + 1)) commits; filtered private tip $FILTERED)"
say "to publish (replaces published main $PUB_TIP):  cd $OUT && git push -f public main"
