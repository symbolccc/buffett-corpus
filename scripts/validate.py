# validate.py - provenance / schema hard gates
# usage: python validate.py [repo_root]
# exit 0 = PASS, exit 1 = FAIL
import json, sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROV = {"buffett_verbatim","buffett_implied","skill_author","industry_convention","practice_derived"}
WEIGHT = {"gate","veto","core","signal_only","context"}
STATUS = {"verified_web","verified_local","to_verify","missing"}
fails, warns, oks = [], [], []
def load(p):
    with open(os.path.join(root, p), encoding='utf-8') as f: return json.load(f)
def check_item(it, kind):
    iid = it.get("id", "?")
    prov, w = it.get("provenance"), it.get("decision_weight")
    refs = it.get("source_refs") or []
    st = it.get("source_refs_status")
    if prov not in PROV: fails.append(f"{kind}/{iid}: provenance '{prov}' not in enum")
    if w not in WEIGHT: fails.append(f"{kind}/{iid}: decision_weight '{w}' not in enum")
    if st not in STATUS: fails.append(f"{kind}/{iid}: source_refs_status '{st}' not in enum")
    if w == "veto" and prov != "buffett_verbatim":
        fails.append(f"{kind}/{iid}: HARD RULE veto requires provenance=buffett_verbatim (got {prov})")
    if prov == "buffett_verbatim" and len(refs) == 0:
        fails.append(f"{kind}/{iid}: HARD RULE buffett_verbatim requires non-empty source_refs")
    if w == "gate":
        if prov not in ("buffett_verbatim","buffett_implied"):
            fails.append(f"{kind}/{iid}: HARD RULE gate requires verbatim/implied provenance")
        if not it.get("gate_rule") or not it.get("fallback"):
            fails.append(f"{kind}/{iid}: gate requires gate_rule and fallback")
    if prov == "buffett_verbatim" and st == "to_verify":
        warns.append(f"{kind}/{iid}: verbatim but year/source not yet verified - do not cite as verified")
    if st == "missing" and w in ("veto","gate"):
        fails.append(f"{kind}/{iid}: {w} with missing source_refs")
    oks.append(iid)
try:
    c = load("criteria/criteria.json"); t = load("criteria/thresholds.json"); s = load("ingest/schema/financials.schema.json")
except Exception as e:
    print("FAIL: cannot load inputs:", e); sys.exit(1)
for it in c["criteria"]: check_item(it, "criteria")
for it in t["thresholds"]: check_item(it, "threshold")
for f in s["fields"]:
    if "key" not in f or "zh" not in f: fails.append(f"schema/field missing key or zh: {f}")
used = set()
for it in c["criteria"] + t["thresholds"]:
    for u in (it.get("used_by") or []): used.add(u)
print(f"checked: {len(c['criteria'])} criteria + {len(t['thresholds'])} thresholds + {len(s['fields'])} fields")
for w in warns: print("  WARN ", w)
if fails:
    print(f"FAIL ({len(fails)}):")
    for f in fails: print("  -", f)
    sys.exit(1)
print(f"PASS - {len(oks)} items ok, {len(warns)} warnings (warnings do not block)")