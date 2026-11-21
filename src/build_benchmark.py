"""Collect drafted questions -> benchmark files.

pool.jsonl      every question whose evidence quote matched the source paragraph (both generators)
unans_cand.jsonl unanswerable candidates (verified later by verify_unanswerable.py)
v0.jsonl        one answerable question per paragraph, generators alternating by paragraph
"""
import glob, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from gen_questions import quote_ok
from collections import defaultdict

META = re.compile(r"\b(this|the above|the said|these) (paragraph|clause|direction|directions|rulebook|section|provision)s?\b", re.I)
GEN = {"nvidia:nvidia/nemotron-3-ultra-550b-a55b": "nemotron", "nvidia:minimaxai/minimax-m3.1-flash": "minimax"}

recs = {}
for f in glob.glob("data/questions/gen_*.jsonl"):
    for r in map(json.loads, open(f)):
        if r["questions"] or (r["generator"], r["doc"], r["para"]) not in recs:
            recs[(r["generator"], r["doc"], r["para"])] = r
sel = [json.loads(l) for l in open("data/questions/selection.jsonl")]
setof = {(s["doc"], s["para"]): s["set"] for s in sel}
order = {(s["doc"], s["para"]): i for i, s in enumerate(sel)}

ptext = {(p["doc"], p["para"]): p["text"] for p in map(json.loads, open("data/processed/paras.jsonl"))}
pool, unans, stats = [], [], defaultdict(lambda: defaultdict(int))
for (g, doc, para), r in recs.items():
    gen = GEN[g]
    stats[gen]["paragraphs"] += 1
    for i, q in enumerate(r["questions"]):
        stats[gen]["drafted"] += 1
        ok = quote_ok(q.get("evidence", ""), ptext[(doc, para)])  # recomputed, so every draft uses the same check
        meta = bool(META.search(q.get("question", "")))
        stats[gen]["quote_ok"] += ok; stats[gen]["meta_ref"] += meta
        if ok and not meta:
            pool.append({"qid": f"{doc}-{para}-{gen}-{i}", "doc": doc, "para": para, "set": setof[(doc, para)],
                         "generator": gen, "answerable": True, **{k: q.get(k) for k in ("question", "answer", "evidence", "type")}})
    u = r.get("unanswerable")
    if isinstance(u, dict) and u.get("question"):
        unans.append({"qid": f"{doc}-{para}-{gen}-u", "doc": doc, "para": para, "set": setof[(doc, para)],
                      "generator": gen, "answerable": False, "question": u["question"], "why": u.get("why")})

by_para = defaultdict(dict)
for q in pool:
    by_para[(q["doc"], q["para"])].setdefault(q["generator"], q)
v0 = []
for key, gens in sorted(by_para.items(), key=lambda kv: order[kv[0]]):
    rot = list(GEN.values()); i = order[key] % len(rot)
    want = rot[i:] + rot[:i]  # rotate first choice across generators
    v0.append(next(gens[g] for g in want if g in gens))

for name, rows in [("pool", pool), ("unans_cand", unans), ("v0", v0)]:
    with open(f"data/benchmark/{name}.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
Path("results").mkdir(exist_ok=True)
json.dump({g: dict(s) for g, s in stats.items()}, open("results/gen_stats.json", "w"), indent=1)
print({g: dict(s) for g, s in stats.items()})
print(f"pool {len(pool)}  unanswerable candidates {len(unans)}  v0 {len(v0)}",
      {g: sum(q['generator'] == g for q in v0) for g in GEN.values()})
