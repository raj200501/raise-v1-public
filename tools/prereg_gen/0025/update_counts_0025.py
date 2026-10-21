"""Update the banked mutation count and the gate count in every document that states them, by phrase, from the report itself."""
import json, sys
R = '/home/user/raise-v1'
r = json.load(open(f"{R}/artifacts/verification/mutation_report.json"))
new, det, sur, gates = r["total_mutations"], r["detected"], r["survived"], len(r["by_gate"])
assert det == new and sur == 0 and "realcurve3_4096" in r["by_gate"], (new, det, sur, sorted(r["by_gate"]))
old, old_g = int(sys.argv[1]), int(sys.argv[2])
edits = [
 (f"{R}/VERDICT.md", f"| {old} mutations, {old} detected, 0 survived |", f"| {new} mutations, {new} detected, 0 survived |"),
 (f"{R}/outbound/EVIDENCE_BRIEF.md", f"**{old}** deliberate mutations across **{old_g}** gates, **{old}** detected", f"**{new}** deliberate mutations across **{gates}** gates, **{new}** detected"),
 (f"{R}/outbound/NARRATIVE.md", f"> {old} deliberate mutations, {old} detected, 0 survived.", f"> {new} deliberate mutations, {new} detected, 0 survived."),
 (f"{R}/outbound/NARRATIVE.md", f"> {old} deliberate mutations across {old_g} gates, {old} detected, 0 survived.", f"> {new} deliberate mutations across {gates} gates, {new} detected, 0 survived."),
 (f"{R}/outbound/ONE_PAGER.md", f"# {old} deliberate mutations, {old} detected, 0 survived", f"# {new} deliberate mutations, {new} detected, 0 survived"),
 (f"{R}/docs/DILIGENCE.md", f"{old} mutations across {old_g} gates certify", f"{new} mutations across {gates} gates certify"),
 (f"{R}/artifacts/verification/coverage.json", f"failing: {old} deliberate mutations across {old_g} gates, {old} detected, 0 survived.", f"failing: {new} deliberate mutations across {gates} gates, {new} detected, 0 survived."),
 (f"{R}/artifacts/verification/coverage.json", f'"json_path": "$.detected",\n      "reverify": "python3 tests/mutation_test.py",\n      "value": {old}', f'"json_path": "$.detected",\n      "reverify": "python3 tests/mutation_test.py",\n      "value": {new}'),
]
for p, a, b in edits:
    s = open(p, encoding="utf-8").read(); n = s.count(a)
    assert n == 1, (p, n, a[:60])
    open(p, "w", encoding="utf-8").write(s.replace(a, b, 1)); print("updated", p)
print("count", old, "->", new, "| gates", old_g, "->", gates)
