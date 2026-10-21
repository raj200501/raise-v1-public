#!/usr/bin/env bash
# Operator script for preregistration 0025: the pre-freeze check, the freeze, and the post-freeze record, in order,
# stopping at the first failure. It never commits, pushes or launches: those commands are printed for the operator.
#
#   RAISE_SCRATCH=<dir outside the repo> bash tools/prereg_gen/0025/freeze_0025.sh [check] [--dry]
#   RAISE_SCRATCH=<dir outside the repo> bash tools/prereg_gen/0025/freeze_0025.sh freeze
#   RAISE_SCRATCH=<dir outside the repo> bash tools/prereg_gen/0025/freeze_0025.sh post-freeze
#
# check (default)  everything up to, not including, the freeze. Changes only what its steps bank (the mutation report,
#                  the counts update_counts_0025.py moves, prefreeze_0025.json, the gates' artifacts); when it leaves
#                  changes it prints the commit that must be pushed before `freeze`.
#   --dry          runs the cheap steps (tree, reader regeneration, interpreter, prereg verify) and echoes the heavy and
#                  the writing ones (mutation suite, update_counts, pre-freeze check, gates) instead of running them.
# freeze           a clean tree (untracked files included) at the pushed upstream tip; `check`; the check changed
#                  nothing; tools/prereg.py freeze; then the post-freeze steps; prints git add/commit/push and the launch.
# post-freeze      resumes the post-freeze steps on a frozen, not yet committed preregistration (each step idempotent).
#
# Where each step comes from: the 0023 and 0024 freeze commits (41b547e, 4f6b721: frozen at the clean pre-freeze commit,
# verify, in-flight paragraphs, the chain count and head in the three documents docs/live_claims.json ties to
# prereg_status.json, the engineering log's freeze block; eight files), 0021's ready-to-freeze commit (80d93c0: the suite
# re-banked, the counts moved, gates.sh ALL GATES PASS), this directory's README and scripts, prefreeze_0025.py's
# docstring, and the preregistration's own invocation and launch blocks.
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="$(cd "$SELF_DIR/../../.." && pwd -P)"
cd "$REPO"

PY="${PYTHON:-python3}"
export PYTHON="$PY"                 # tools/gates.sh runs every gate with $PYTHON
export PYTHONDONTWRITEBYTECODE=1    # the tracked .pyc below is rewritten by any import of chainlib otherwise
VENV_PY=/root/venv311/bin/python    # the sealed run's interpreter when the preregistration names python 3.11.15
GEN=tools/prereg_gen/0025
PREREG=prereg/0025-realcurve3-4096.json
READER=tools/readers/realcurve3_4096_verdict.py
PYC=tools/__pycache__/chainlib.cpython-311.pyc
HEAVY_RE='^ *[0-9]+ [^ ]*[p]ython[^ ]* .*(tools/pivot/run_|tools/pivot/corpus_|tests/mutation_test\.py)'

# what `check` may leave changed (its own outputs); anything else tracked and changed refuses the check
CHECK_WRITES=(VERDICT.md outbound/EVIDENCE_BRIEF.md outbound/NARRATIVE.md outbound/ONE_PAGER.md docs/DILIGENCE.md
  artifacts/verification/coverage.json artifacts/verification/mutation_report.json artifacts/verification/prefreeze_0025.json
  artifacts/verification/prereg_status.json artifacts/verification/record_counts.json "$PYC")
# what the freeze and the post-freeze steps change: 0024's freeze commit touched exactly these eight files
FREEZE_WRITES=(README.md VERDICT.md artifacts/pivot/engineering_log_0025.json artifacts/verification/prereg_status.json
  outbound/EVIDENCE_BRIEF.md outbound/NARRATIVE.md "$PREREG" prereg/chain.jsonl)

usage() { sed -n '2,17p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

MODE=check; DRY=0
for a in "$@"; do
  case "$a" in
    check|freeze|post-freeze) MODE="$a" ;;
    --dry) DRY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $a" >&2; usage >&2; exit 64 ;;
  esac
done
if [ "$DRY" = 1 ] && [ "$MODE" != check ]; then echo "--dry is for check only; freeze and post-freeze have no rehearsal" >&2; exit 64; fi

: "${RAISE_SCRATCH:?set RAISE_SCRATCH to a scratch directory outside the repository}"
SCR="$(realpath -m -- "$RAISE_SCRATCH")/freeze_0025"
case "$SCR/" in "$REPO/"*) echo "RAISE_SCRATCH must be outside the repository" >&2; exit 64 ;; esac
mkdir -p "$SCR"

# ---------------------------------------------------------------- helpers
STEP="start"; N=0; FROZEN_HERE=0
step() { N=$((N + 1)); STEP="$N. $1"; printf '\n== %s  [%s]\n' "$STEP" "$(date -u +%H:%M:%SZ)"; }
fail() { echo "FAIL: $*" >&2; exit 1; }
dry() { printf '  DRY, not run: %s\n' "$*"; }
indent() { sed 's/^/  /'; }
restore_pyc() {
  if ! git diff --quiet -- "$PYC" 2>/dev/null; then git checkout -- "$PYC"; echo "  restored $PYC"; fi
}
runlog() {  # runlog <log> <cmd...>: output to <log>, the .pyc restored afterwards, the command's exit code returned
  local log="$1" rc=0; shift
  "$@" >"$log" 2>&1 || rc=$?
  restore_pyc
  return "$rc"
}
on_exit() {
  local rc=$?
  restore_pyc || true
  if [ "$rc" -ne 0 ]; then
    printf '\nSTOPPED at step %s (exit %s). Nothing was committed, pushed or launched.\n' "$STEP" "$rc" >&2
    if [ "$FROZEN_HERE" = 1 ]; then
      echo "  The preregistration IS frozen in the working tree, not committed. Fix the cause, then resume with:" >&2
      echo "    RAISE_SCRATCH=$RAISE_SCRATCH bash $GEN/freeze_0025.sh post-freeze" >&2
    fi
  fi
}
trap on_exit EXIT

tree_status() { git status --porcelain=v1 --untracked-files=all; }
path_of() { local p="${1:3}"; printf '%s' "${p##* -> }"; }
in_list() { local x="$1" y; shift; for y in "$@"; do [ "$x" = "$y" ] && return 0; done; return 1; }
changed_paths() { local line; while IFS= read -r line; do [ -n "$line" ] && path_of "$line" && echo; done < <(tree_status); }
tree_clean_strict() {
  local s; s="$(tree_status)"
  if [ -n "$s" ]; then echo "$s" | indent; fail "$1"; fi
  echo "  clean (git status --porcelain is empty)"
}
tree_check_allowed() {
  local line p bad=() unt=()
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    p="$(path_of "$line")"
    in_list "$p" "${CHECK_WRITES[@]}" && { echo "  allowed (a check output): ${line:0:2} $p"; continue; }
    if [ "${line:0:2}" = "??" ]; then unt+=("$p"); else bad+=("$p"); fi
  done < <(tree_status)
  if [ "${#unt[@]}" -gt 0 ]; then
    echo "  WARNING untracked (the check ignores them; freeze refuses until they are committed or removed):"
    printf '    %s\n' "${unt[@]}"
  fi
  if [ "${#bad[@]}" -gt 0 ]; then
    echo "  changed, tracked, not a check output:"; printf '    %s\n' "${bad[@]}"; fail "tracked files changed outside the check's own outputs"
  fi
  echo "  no tracked change outside the check's own outputs"
}
heavy_procs() { ps -eo pid=,args= | grep -E "$HEAVY_RE" | cut -c1-160 || true; }
prereg_state() {  # "<frozen> <0025 in chain> <chain length> <chain head id>"
  "$PY" - "$REPO" <<'PY'
import json, sys
R = sys.argv[1]
pr = json.load(open(f'{R}/prereg/0025-realcurve3-4096.json', encoding='utf-8'))
ch = [json.loads(l) for l in open(f'{R}/prereg/chain.jsonl', encoding='utf-8') if l.strip()]
print(str(pr.get('frozen') is True).lower(), str(any(e['id'] == '0025' for e in ch)).lower(), len(ch), ch[-1]['id'])
PY
}
counts_stated() {  # the mutation count and gate count the documents state now (coverage.json, the phrase update_counts moves)
  "$PY" - "$REPO" <<'PY'
import json, re, sys
s = open(f'{sys.argv[1]}/artifacts/verification/coverage.json', encoding='utf-8').read()
m = re.findall(r'failing: (\d+) deliberate mutations across (\d+) gates', s)
assert len(m) == 1, m
claim = [c for c in json.loads(s)['claims'] if c['id'] == 'mutations-detected'][0]['value']
assert int(m[0][0]) == int(claim), (m, claim)
print(m[0][0], m[0][1])
PY
}
mutation_args() {  # --jobs only when the suite's own --help offers it
  local help n
  help="$("$PY" tests/mutation_test.py --help 2>&1 || true)"
  if grep -q -- '--jobs' <<<"$help"; then
    n="$(nproc 2>/dev/null || echo 1)"; [ "$n" -gt 4 ] && n=4
    echo "--jobs ${MUTATION_JOBS:-$n}"
  fi
}
author_check() {
  [ -n "$(git log --author='^raj200501 <' -1 --format=%ae)" ] || fail "no commit by raj200501 in this history to take the author address from"
}
upstream_branch() {
  local u; u="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
  if [ -n "$u" ]; then echo "${u#origin/}"; else git rev-parse --abbrev-ref HEAD; fi
}
print_commit() {  # print_commit <message file> <paths...>
  local msg="$1"; shift
  echo "  git add -- $*"
  echo "  git -c user.name=raj200501 -c user.email=\"\$(git log --author='^raj200501 <' -1 --format=%ae)\" commit -F $msg"
  echo "  git push origin HEAD:$(upstream_branch)"
}
interpreter_check() {  # the sealed run's interpreter: the one the invocation names, with the sealed environment's versions
  "$PY" - "$REPO" "$VENV_PY" <<'PY'
import json, re, subprocess, sys
R, venv = sys.argv[1], sys.argv[2]
pr = json.load(open(f'{R}/prereg/0025-realcurve3-4096.json', encoding='utf-8'))
env = pr['scope']['curve']['protocol']['environment']
m = re.search(r'[Pp]ython (\d+\.\d+\.\d+)', pr['invocation']['interpreter'])
assert m, 'invocation.interpreter names no Python version'
if m.group(1) != '3.11.15' or env['python'] != '3.11.15':
    raise SystemExit(f"the invocation names Python {m.group(1)} and the sealed environment {env['python']}; this script knows "
                     f"only 3.11.15 ({venv})")
probe = 'import json, platform, numpy, sklearn; print(json.dumps({"python": platform.python_version(), "numpy": numpy.__version__, "sklearn": sklearn.__version__}))'
r = subprocess.run([venv, '-I', '-c', probe], capture_output=True, text=True)
if r.returncode != 0:
    raise SystemExit(f'{venv} does not run: {r.stderr.strip()[-300:]}')
got = json.loads(r.stdout)
bad = {k: [got.get(k), v] for k, v in env.items() if got.get(k) != v}
if bad:
    raise SystemExit(f'{venv} does not match scope.curve.protocol.environment ([found, sealed]): {bad}')
print(f'  {venv}: python {got["python"]}, numpy {got["numpy"]}, sklearn {got["sklearn"]} = scope.curve.protocol.environment')
PY
}
print_launch() {  # print_launch <title>: the sealed run, from invocation.run, with the interpreter swapped and a launch guard
  "$PY" - "$REPO" "$VENV_PY" "$SCR" "$HEAVY_RE" "$1" <<'PY'
import json, sys
R, venv, scr, heavy_re, title = sys.argv[1:6]
pr = json.load(open(f'{R}/prereg/0025-realcurve3-4096.json', encoding='utf-8'))
P = pr['scope']['curve']['protocol']; run = pr['invocation']['run']; mem = P['launch']['min_mem_available_gb']
assert P['threads'] == 3 and P['nice'] == 10, (P['threads'], P['nice'])
prefix = (f"OMP_NUM_THREADS={P['threads']} OPENBLAS_NUM_THREADS={P['threads']} MKL_NUM_THREADS={P['threads']} "
          f"nice -n {P['nice']} python3 tools/pivot/run_realcurve3.py ")
assert run.startswith(prefix) and run.count(' python3 ') == 1, run[:160]
cmd = run.replace(' python3 ', f' {venv} ', 1)
log = f'{scr}/realcurve3_4096_launch.log'
print(f'  {title} (not run by this script):\n')
print(f'cd {R}')
print("avail=$(awk '$1==\"MemAvailable:\"{print $2/1e6}' /proc/meminfo)")
print(f"busy=$(ps -eo pid=,args= | grep -E '{heavy_re}')")
print(f"if awk -v a=\"$avail\" -v m={mem} 'BEGIN{{exit !(a+0 >= m+0)}}' && [ -z \"$busy\" ]; then")
print(f'  nohup env {cmd} > {log} 2>&1 &')
print(f'  echo "launched: pid $!, log {log}"')
print('else')
print(f'  echo "NOT LAUNCHED: MemAvailable ${{avail}} GB (the preregistration needs >= {mem}); heavy processes: ${{busy:-none}}"')
print('fi')
print(f'\n  (invocation.run with python3 -> {venv}; launch.min_mem_available_gb {mem}; the runner itself re-checks memory, '
      f'disk, load, threads, nice and the environment and refuses with exit 3)')
PY
}

# ---------------------------------------------------------------- check: everything before the freeze
run_check() {
  local st frozen in_chain clen head rc out old_total old_gates jargs=()

  step "preconditions: RAISE_SCRATCH, unfrozen preregistration, 0025 not in the chain"
  echo "  repo $REPO; scratch $SCR; python $("$PY" -c 'import platform; print(platform.python_version())')"
  st="$(prereg_state)"; read -r frozen in_chain clen head <<<"$st"
  [ "$frozen" = false ] || fail "$PREREG is frozen: check runs before the freeze only (post-freeze resumes after it)"
  [ "$in_chain" = false ] || fail "prereg/chain.jsonl already holds 0025"
  echo "  $PREREG unfrozen; chain: $clen entries, head $head"

  step "working tree clean except the check's own outputs"
  restore_pyc
  tree_check_allowed

  step "no runner, corpus builder or mutation suite alive"
  out="$(heavy_procs)"
  if [ -z "$out" ]; then echo "  none"
  elif [ "$DRY" = 1 ]; then echo "$out" | indent; echo "  (DRY: noted; the heavy steps below are not run)"
  else echo "$out" | indent; fail "a heavy process is alive; the suite and the pre-freeze check would share its memory"; fi

  step "the committed reader is the generator's output ($GEN/gen_reader_0025.py)"
  rc=0; runlog "$SCR/gen_reader.log" "$PY" "$GEN/gen_reader_0025.py" "$REPO/$PREREG" "$SCR/reader_regenerated.py" || rc=$?
  indent <"$SCR/gen_reader.log"
  [ "$rc" -eq 0 ] || fail "the reader generator failed"
  cmp "$SCR/reader_regenerated.py" "$READER" || fail "$READER is not the generator's output"
  echo "  identical: $READER == $SCR/reader_regenerated.py"

  step "the sealed run's interpreter matches the sealed environment"
  interpreter_check

  step "full mutation suite (tests/mutation_test.py)"
  out="$(mutation_args)"; read -r -a jargs <<<"$out"
  out="$(counts_stated)"; read -r old_total old_gates <<<"$out"
  echo "  the documents state $old_total mutations across $old_gates gates; suite flags: ${jargs[*]:-(none; no --jobs in its --help)}"
  if [ "$DRY" = 1 ]; then
    dry "$PY tests/mutation_test.py${jargs[*]:+ ${jargs[*]}} > $SCR/mutation_full.log"
  else
    echo "  log: $SCR/mutation_full.log"
    rc=0; runlog "$SCR/mutation_full.log" "$PY" tests/mutation_test.py ${jargs[@]+"${jargs[@]}"} || rc=$?
    grep -E '^(MUTATION REPORT|MUTATION COUNT IS STALE|SURVIVING MUTATIONS|PARTIAL RUN)' "$SCR/mutation_full.log" | indent || true
    if [ "$rc" -ne 0 ]; then
      if [ "$rc" -eq 1 ] && grep -q '^MUTATION COUNT IS STALE' "$SCR/mutation_full.log" && ! grep -q '^SURVIVING MUTATIONS' "$SCR/mutation_full.log"; then
        echo "  the count moved and nothing survived: update_counts_0025.py moves it next"
      else
        fail "the mutation suite failed (exit $rc); see $SCR/mutation_full.log"
      fi
    fi
    "$PY" - "$REPO" <<'PY'
import json, sys
r = json.load(open(f'{sys.argv[1]}/artifacts/verification/mutation_report.json'))
g = r['by_gate'].get('realcurve3_4096', {})
assert r['survived'] == 0 and r['detected'] == r['total_mutations'], (r['detected'], r['total_mutations'], r['survived'])
assert g and g['detected'] == g['total'], g
print(f"  banked: {r['detected']}/{r['total_mutations']} across {len(r['by_gate'])} gates; realcurve3_4096 {g['detected']}/{g['total']}")
PY
  fi

  step "move the banked mutation and gate counts ($GEN/update_counts_0025.py)"
  if [ "$DRY" = 1 ]; then
    dry "$PY $GEN/update_counts_0025.py $old_total $old_gates   (the stated counts; it reads the new ones from the report)"
  else
    "$PY" "$GEN/update_counts_0025.py" "$old_total" "$old_gates" | indent
    restore_pyc
    "$PY" - "$REPO" <<'PY'
import json, sys
R = sys.argv[1]
r = json.load(open(f'{R}/artifacts/verification/mutation_report.json'))
claim = [c for c in json.load(open(f'{R}/artifacts/verification/coverage.json'))['claims'] if c['id'] == 'mutations-detected'][0]['value']
assert int(claim) == r['total_mutations'], (claim, r['total_mutations'])
print(f"  coverage claim mutations-detected = {claim} = the report's total")
PY
  fi

  step "pre-freeze check PASS (tools/prereg_checks/prefreeze_0025.py)"
  if [ "$DRY" = 1 ]; then
    dry "PREREG_0025_GENERATOR=$REPO/$GEN/gen_reader_0025.py PREREG_0025_SCRATCH=$SCR/prefreeze $PY tools/prereg_checks/prefreeze_0025.py"
  else
    echo "  log: $SCR/prefreeze_0025.log"
    rc=0
    runlog "$SCR/prefreeze_0025.log" env PREREG_0025_GENERATOR="$REPO/$GEN/gen_reader_0025.py" PREREG_0025_SCRATCH="$SCR/prefreeze" \
      "$PY" tools/prereg_checks/prefreeze_0025.py || rc=$?
    grep -E '^BAD ' "$SCR/prefreeze_0025.log" | indent || true
    tail -n 1 "$SCR/prefreeze_0025.log" | indent
    [ "$rc" -eq 0 ] && grep -q '^PRE-FREEZE 0025: PASS' "$SCR/prefreeze_0025.log" || fail "the pre-freeze check did not pass (exit $rc)"
  fi

  step "every gate (tools/gates.sh)"
  if [ "$DRY" = 1 ]; then
    dry "PYTHON=$PY bash tools/gates.sh > $SCR/gates.log"
  else
    echo "  log: $SCR/gates.log"
    rc=0; runlog "$SCR/gates.log" bash tools/gates.sh || rc=$?
    tail -n 6 "$SCR/gates.log" | indent
    [ "$rc" -eq 0 ] && [ "$(tail -n 1 "$SCR/gates.log")" = "ALL GATES PASS" ] || fail "tools/gates.sh did not pass (exit $rc)"
  fi

  step "the preregistration chain verifies (tools/prereg.py verify)"
  rc=0; runlog "$SCR/prereg_verify.log" "$PY" tools/prereg.py verify || rc=$?
  indent <"$SCR/prereg_verify.log"
  [ "$rc" -eq 0 ] && grep -q '^PREREG CHAIN VERIFY: PASS' "$SCR/prereg_verify.log" || fail "tools/prereg.py verify failed"
}

check_report() {  # after a standalone check: what it changed, and the commit that must be pushed before `freeze`
  local p add=() old_total="$1"
  step "what the check changed"
  restore_pyc
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    if in_list "$p" "${CHECK_WRITES[@]}"; then add+=("$p"); fi
  done < <(changed_paths)
  if [ "$DRY" = 1 ]; then
    git status --short | indent
    echo "  DRY: the suite, the counts, the pre-freeze check and the gates were not run; this is not a freeze-ready result"
  elif [ "${#add[@]}" -eq 0 ]; then
    echo "  nothing: HEAD passes the check as committed; when it is pushed, run: RAISE_SCRATCH=$RAISE_SCRATCH bash $GEN/freeze_0025.sh freeze"
  else
    author_check
    "$PY" - "$REPO" "$SCR/prefreeze_commit_message.txt" "$old_total" <<'PY'
import json, sys
R, out, old = sys.argv[1], sys.argv[2], int(sys.argv[3])
r = json.load(open(f'{R}/artifacts/verification/mutation_report.json')); g = r['by_gate']['realcurve3_4096']
moved = (f"The suite goes {old} to {r['total_mutations']} across {len(r['by_gate'])} gates, and the count moved in every document that "
         f"states it (tools/prereg_gen/0025/update_counts_0025.py, by phrase). ") if old != r['total_mutations'] else ""
msg = (f"0025 ready to freeze: {r['detected']}/{r['total_mutations']} mutations re-banked, pre-freeze check PASS, all gates pass\n\n"
       f"{moved}The realcurve3_4096 gate stands at {g['detected']}/{g['total']}. tools/prereg_checks/prefreeze_0025.py passed and is\n"
       f"banked in artifacts/verification/prefreeze_0025.json. bash tools/gates.sh: ALL GATES PASS. tools/prereg.py verify passes.\n")
open(out, 'w', encoding='utf-8').write(msg)
PY
    echo "  changed: ${add[*]}"
    echo "  commit and push these before the freeze (printed, not run; message in $SCR/prefreeze_commit_message.txt):"
    print_commit "$SCR/prefreeze_commit_message.txt" "${add[@]}"
    echo "  then: RAISE_SCRATCH=$RAISE_SCRATCH bash $GEN/freeze_0025.sh freeze"
  fi
}

# ---------------------------------------------------------------- after the freeze
post_freeze() {
  local rc p extra=() missing=() changed=()

  step "the chain verifies with 0025 (tools/prereg.py verify)"
  rc=0; runlog "$SCR/prereg_verify_frozen.log" "$PY" tools/prereg.py verify || rc=$?
  indent <"$SCR/prereg_verify_frozen.log"
  [ "$rc" -eq 0 ] && grep -q '^PREREG CHAIN VERIFY: PASS' "$SCR/prereg_verify_frozen.log" || fail "tools/prereg.py verify failed after the freeze"

  step "in-flight paragraphs in VERDICT.md and README.md ($GEN/freeze_docs_0025.py)"
  "$PY" "$GEN/freeze_docs_0025.py" | indent
  restore_pyc

  step "the chain count and head in VERDICT.md, outbound/EVIDENCE_BRIEF.md, outbound/NARRATIVE.md"
  "$PY" - "$REPO" <<'PY'
import json, sys
R = sys.argv[1]
st = json.load(open(f'{R}/artifacts/verification/prereg_status.json', encoding='utf-8'))
ch = st['chain']; n = len(ch); assert ch[-1]['id'] == '0025' and st['verified'] is True, ch[-1]['id']
h, ph = ch[-1]['hash'][:8], ch[-2]['hash'][:8]
row = '| Preregistration chain verifies, reader unchanged since freeze | '
edits = [('VERDICT.md', f'{row}{n - 1} entries, head `{ph}…` |', f'{row}{n} entries, head `{h}…` |'),
         ('outbound/EVIDENCE_BRIEF.md', f'**{n - 1}** preregistrations, hash-chained', f'**{n}** preregistrations, hash-chained'),
         ('outbound/NARRATIVE.md', f'keep us honest. {n - 1} preregistrations,\n> hash-chained', f'keep us honest. {n} preregistrations,\n> hash-chained')]
for p, a, b in edits:
    s = open(f'{R}/{p}', encoding='utf-8').read()
    if s.count(b) == 1 and a not in s:
        print(f'  already moved: {p}'); continue
    assert s.count(a) == 1, (p, s.count(a), a)
    open(f'{R}/{p}', 'w', encoding='utf-8').write(s.replace(a, b, 1)); print(f'  {p}: {n - 1} -> {n}' + (f', head {h}' if p == 'VERDICT.md' else ''))
PY

  step "the engineering log's freeze record (artifacts/pivot/engineering_log_0025.json)"
  "$PY" - "$REPO" <<'PY'
import hashlib, json, subprocess, sys
R = sys.argv[1]
pr = json.load(open(f'{R}/prereg/0025-realcurve3-4096.json', encoding='utf-8')); sp = pr['scope']['sealed_partition']
e = [json.loads(l) for l in open(f'{R}/prereg/chain.jsonl', encoding='utf-8') if l.strip()][-1]
assert pr['frozen'] is True and e['id'] == '0025' and e['hash'] == pr['chain_hash'], (e['id'], pr.get('frozen'))
rep = json.load(open(f'{R}/artifacts/verification/mutation_report.json')); g = rep['by_gate']['realcurve3_4096']
pf = json.load(open(f'{R}/artifacts/verification/prefreeze_0025.json'))
at_commit = subprocess.run(['git', '-C', R, 'show', f"{pr['git_commit']}:prereg/0025-realcurve3-4096.json"], capture_output=True, check=True).stdout
assert pf['passed'] is True and pf['prereg_sha256_at_check'] == hashlib.sha256(at_commit).hexdigest(), 'prefreeze_0025.json is not a PASS on the frozen commit\'s file'
path = f'{R}/artifacts/pivot/engineering_log_0025.json'
E = json.load(open(path, encoding='utf-8'))
E['freeze'] = {
    "anchors": pr['anchors'], "chain_hash": pr['chain_hash'], "chain_prev_hash": pr['chain_prev_hash'], "chain_seq": e['seq'],
    "frozen_utc": pr['frozen_utc'], "git_commit": pr['git_commit'], "git_dirty_at_freeze": pr['git_dirty_at_freeze'],
    "in_flight_documents": "VERDICT.md and README.md carry the in-flight paragraphs generated from the sealed file (tools/prereg_gen/0025/freeze_docs_0025.py)",
    "mutation_report_at_freeze": {"cases": g['total'], "detected": rep['detected'], "gate": "realcurve3_4096", "total": rep['total_mutations']},
    "prefreeze_check": f"artifacts/verification/prefreeze_0025.json (PASS at the pre-freeze commit {pr['git_commit'][:7]})",
    "reader_sha256": pr['reader_sha256'],
    "sealed_span": {"decades_spanned": sp['decades_spanned'], "decades_spanned_second_decade": sp['decades_spanned_second_decade'],
                    "doublings_spanned": sp['doublings_spanned'], "doublings_spanned_second_decade": sp['doublings_spanned_second_decade'],
                    "rungs_plaintexts": [r['n_chunks'] for r in sp['rungs']], "rungs_rows": [r['n_rows'] for r in sp['rungs']],
                    "shift_arm": {k: sp['shift_arm'][k] for k in ('n_chunks', 'n_rows')},
                    "shift_arm_0025": {k: sp['shift_arm_0025'][k] for k in ('n_chunks', 'n_rows')}},
}
E['status'] = f"frozen {pr['frozen_utc'][:10]}; run pending"
with open(path, 'w', encoding='utf-8') as fh:
    json.dump(E, fh, indent=2, sort_keys=True, ensure_ascii=True); fh.write('\n')
print(f"  freeze block written: seq {e['seq']}, frozen {pr['frozen_utc']}, commit {pr['git_commit'][:7]}, status {E['status']!r}")
PY

  step "the cheap gates on the frozen record (freshness, claimcheck, coverage, the 0025 reader pending)"
  rc=0; runlog "$SCR/freshness.log" "$PY" tools/freshness.py || rc=$?; tail -n 1 "$SCR/freshness.log" | indent
  [ "$rc" -eq 0 ] || fail "tools/freshness.py: a live claim is stale (see $SCR/freshness.log)"
  rc=0; runlog "$SCR/claimcheck.log" "$PY" tools/claimcheck.py outbound VERDICT.md || rc=$?; tail -n 1 "$SCR/claimcheck.log" | indent
  [ "$rc" -eq 0 ] || fail "tools/claimcheck.py failed (see $SCR/claimcheck.log)"
  rc=0; runlog "$SCR/coverage.log" "$PY" tools/coverage.py || rc=$?; tail -n 1 "$SCR/coverage.log" | indent
  [ "$rc" -eq 0 ] || fail "tools/coverage.py failed (see $SCR/coverage.log)"
  rc=0; runlog "$SCR/reader_0025.log" "$PY" "$READER" || rc=$?; head -n 1 "$SCR/reader_0025.log" | indent
  [ "$rc" -eq 2 ] || fail "the 0025 reader exited $rc with no run artifact (2, pending, expected)"

  step "the freeze changed exactly 0024's eight files"
  restore_pyc
  while IFS= read -r p; do [ -n "$p" ] && changed+=("$p"); done < <(changed_paths)
  for p in "${changed[@]}"; do in_list "$p" "${FREEZE_WRITES[@]}" || extra+=("$p"); done
  for p in "${FREEZE_WRITES[@]}"; do in_list "$p" "${changed[@]}" || missing+=("$p"); done
  git status --short | indent
  [ "${#extra[@]}" -eq 0 ] || fail "changed beyond the freeze's files: ${extra[*]}"
  [ "${#missing[@]}" -eq 0 ] || fail "not changed: ${missing[*]}"

  step "commit, push and launch (printed, not run)"
  author_check
  "$PY" - "$REPO" "$SCR/freeze_commit_message.txt" <<'PY'
import json, sys
R, out = sys.argv[1], sys.argv[2]
pr = json.load(open(f'{R}/prereg/0025-realcurve3-4096.json', encoding='utf-8'))
ch = [json.loads(l) for l in open(f'{R}/prereg/chain.jsonl', encoding='utf-8') if l.strip()]; e = ch[-1]; a = pr['anchors']
rep = json.load(open(f'{R}/artifacts/verification/mutation_report.json')); g = rep['by_gate']['realcurve3_4096']
msg = (f"0025 frozen: chain entry {e['seq']}, beacon-anchored; in-flight paragraphs from the sealed file\n\n"
       f"prereg/0025-realcurve3-4096.json is frozen (seq {e['seq']}, hash {e['hash'][:16]}, prev {e['prev_hash'][:16]}, NIST beacon pulse\n"
       f"{a['nist_beacon_v2']['pulse']} and drand round {a['drand']['round']} embedded) at the clean pre-freeze commit {pr['git_commit'][:7]}; "
       f"tools/prereg.py verify\npasses on {len(ch)} entries and the reader's sha256 is recorded. The pre-freeze check passed at that commit "
       f"and is banked in\nartifacts/verification/prefreeze_0025.json; the mutation suite stood at {rep['detected']}/{rep['total_mutations']}, "
       f"the realcurve3_4096 gate at {g['detected']}/{g['total']}.\n\n"
       f"VERDICT.md and README.md carry the in-flight paragraphs, generated from the sealed file by\n"
       f"tools/prereg_gen/0025/freeze_docs_0025.py. The chain count and head moved in the three documents that state them. The\n"
       f"engineering log records the freeze and the sealed span. Nothing below the in-flight line changes until the frozen\n"
       f"reader has read the completed run.\n")
open(out, 'w', encoding='utf-8').write(msg)
PY
  echo "  message: $SCR/freeze_commit_message.txt"
  print_commit "$SCR/freeze_commit_message.txt" "${FREEZE_WRITES[@]}"
  echo
  interpreter_check
  print_launch "after the freeze commit is pushed, the sealed run"
}

# ---------------------------------------------------------------- modes
case "$MODE" in
  check)
    OUT="$(counts_stated)"; read -r OLD_TOTAL _ <<<"$OUT"
    run_check
    check_report "$OLD_TOTAL"
    step "the sealed run's launch command (preview; freeze prints it again after the freeze)"
    print_launch "preview, valid only once the frozen preregistration is committed and pushed"
    printf '\nCHECK %s\n' "$([ "$DRY" = 1 ] && echo "DRY RUN COMPLETE (heavy steps echoed, not run)" || echo PASS)"
    ;;

  freeze)
    step "freeze preconditions: a clean tree at the pushed upstream tip"
    restore_pyc
    tree_clean_strict "freeze needs a clean tree, untracked files included (tools/prereg.py records git status --porcelain as git_dirty_at_freeze)"
    UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)" || fail "the branch has no upstream on origin"
    git fetch --quiet origin || fail "git fetch origin failed"
    [ "$(git rev-parse HEAD)" = "$(git rev-parse '@{u}')" ] || fail "HEAD $(git rev-parse --short HEAD) is not the tip of $UPSTREAM ($(git rev-parse --short '@{u}')): push or pull first"
    START_HEAD="$(git rev-parse HEAD)"
    author_check
    echo "  HEAD $START_HEAD = $UPSTREAM"

    run_check

    step "the check changed nothing and HEAD did not move"
    restore_pyc
    tree_clean_strict "the check changed files: run check, commit and push what it prints, then run freeze again"
    [ "$(git rev-parse HEAD)" = "$START_HEAD" ] || fail "HEAD moved during the check"

    step "the beacons answer (tools/prereg.py fetch_anchors, as the freeze will call it)"
    "$PY" - "$REPO" <<'PY'
import json, sys
sys.path.insert(0, f'{sys.argv[1]}/tools')
import prereg
a = prereg.fetch_anchors()
bad = {k: v for k, v in a.items() if 'COULD_NOT_VERIFY' in v}
if bad:
    raise SystemExit(f'a beacon does not answer: {json.dumps(bad)[:400]}')
print(f"  NIST pulse {a['nist_beacon_v2']['pulse']} ({a['nist_beacon_v2']['time_stamp']}), drand round {a['drand']['round']}")
PY
    restore_pyc
    tree_clean_strict "the beacon probe changed the tree"

    step "FREEZE (tools/prereg.py freeze $PREREG)"
    rc=0; runlog "$SCR/freeze.log" "$PY" tools/prereg.py freeze "$PREREG" || rc=$?
    indent <"$SCR/freeze.log"
    [ "$rc" -eq 0 ] || fail "tools/prereg.py freeze failed (exit $rc)"
    FROZEN_HERE=1

    step "the frozen file: chain entry, commit, clean flag, anchors"
    "$PY" - "$REPO" "$START_HEAD" <<'PY'
import json, sys
R, head = sys.argv[1], sys.argv[2]
pr = json.load(open(f'{R}/prereg/0025-realcurve3-4096.json', encoding='utf-8'))
ch = [json.loads(l) for l in open(f'{R}/prereg/chain.jsonl', encoding='utf-8') if l.strip()]; e = ch[-1]
problems = []
if not (pr.get('frozen') is True and e['id'] == '0025' and e['hash'] == pr['chain_hash'] and e['seq'] == len(ch)):
    problems.append('the file and the chain entry disagree')
if pr.get('git_commit') != head:
    problems.append(f"git_commit {pr.get('git_commit')} is not the checked commit {head}")
if pr.get('git_dirty_at_freeze') is not False:
    problems.append('git_dirty_at_freeze is not false')
bad = {k: v for k, v in pr.get('anchors', {}).items() if 'COULD_NOT_VERIFY' in v}
if bad or set(pr.get('anchors', {})) != {'nist_beacon_v2', 'drand'}:
    problems.append(f'anchors: {json.dumps(pr.get("anchors"))[:300]}')
if problems:
    print('\n'.join('  ' + p for p in problems))
    raise SystemExit('the freeze is recorded but not as the record requires; it is uncommitted - to discard it and freeze again: '
                     'git checkout -- prereg/0025-realcurve3-4096.json prereg/chain.jsonl')
print(f"  seq {e['seq']}, hash {e['hash'][:16]}, prev {e['prev_hash'][:16]}, frozen {pr['frozen_utc']}, commit {head[:7]}, clean; "
      f"NIST pulse {pr['anchors']['nist_beacon_v2']['pulse']}, drand round {pr['anchors']['drand']['round']}")
PY

    post_freeze
    printf '\nFROZEN. Nothing is committed, pushed or launched: run the printed commands.\n'
    ;;

  post-freeze)
    step "post-freeze preconditions: frozen in the working tree, not yet committed"
    st="$(prereg_state)"; read -r FROZEN IN_CHAIN _ HEAD_ID <<<"$st"
    [ "$FROZEN" = true ] && [ "$IN_CHAIN" = true ] && [ "$HEAD_ID" = 0025 ] || fail "$PREREG is not frozen with 0025 at the chain head"
    git show "HEAD:$PREREG" | "$PY" -c 'import json, sys; sys.exit(0 if json.load(sys.stdin).get("frozen") is False else 1)' \
      || fail "the freeze is already committed at HEAD; nothing to resume"
    FROZEN_HERE=1
    echo "  frozen, uncommitted; resuming"
    post_freeze
    printf '\nPOST-FREEZE COMPLETE. Nothing is committed, pushed or launched: run the printed commands.\n'
    ;;
esac
