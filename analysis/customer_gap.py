"""Officer vs customer wording on the same questions (paired), from results/rankings/.
Writes results/customer_gap.json: per config, R@5 / Book@1 / WL@1 for both wordings on the shared qids."""
import json, sys
from pathlib import Path
sys.path.insert(0, "src")
from retrieve import load_chunks

docs = {d["doc"]: d for d in map(json.loads, open("data/processed/docs.jsonl"))}
gold = {q["qid"]: q for q in map(json.loads, open("data/benchmark/v0.jsonl"))}


def score(rk, q, ch):
    hit = [ch[i]["doc"] == q["doc"] and q["para"] in ch[i]["paras"] for i in rk[:5]]
    top = ch[rk[0]]["doc"]
    return any(hit), hit[0], top == q["doc"], top != q["doc"] and docs[top]["topic"] == docs[q["doc"]]["topic"]


out, chunks = {}, {}
for f in sorted(Path("results/rankings").glob("v1_customer__*.json")):
    cs, name = f.stem.split("__")[1:3]
    o = Path(f"results/rankings/officer__{cs}__{name}.json")
    if not o.exists(): continue
    ch = chunks.setdefault(cs, load_chunks(cs))
    c, o = json.load(open(f)), json.load(open(o))
    oc = dict(zip(o["qids"], o["ranks"]))
    shared = [(qid, rk) for qid, rk in zip(c["qids"], c["ranks"]) if qid in oc]
    agg = {}
    for tag, pairs in (("officer", [(q, oc[q]) for q, _ in shared]), ("customer", shared)):
        s = [score(rk, gold[q], ch) for q, rk in pairs]
        agg[tag] = {k: round(sum(x[i] for x in s) / len(s), 3) for i, k in enumerate(("R@5", "R@1", "Book@1", "WL@1"))}
    out[f"{cs}|{name}"] = {"n": len(shared), **agg}
json.dump(out, open("results/customer_gap.json", "w"), indent=1)
for k, v in sorted(out.items(), key=lambda kv: -kv[1]["customer"]["R@5"]):
    print(f"{k:75} n={v['n']} R5 {v['officer']['R@5']:.3f}->{v['customer']['R@5']:.3f}  Book {v['officer']['Book@1']:.2f}->{v['customer']['Book@1']:.2f}  WL {v['officer']['WL@1']:.3f}->{v['customer']['WL@1']:.3f}")
