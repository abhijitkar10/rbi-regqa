"""Best retriever on rulebook wording, split by question type and by generator. Out: results/breakdown.json"""
import json, sys
from collections import defaultdict
sys.path.insert(0, "src")
from retrieve import load_chunks

docs = {d["doc"]: d for d in map(json.loads, open("data/processed/docs.jsonl"))}
qs = {q["qid"]: q for q in map(json.loads, open("data/benchmark/v0.jsonl"))}
ch = load_chunks("para_title")
r = json.load(open("results/rankings/officer__para_title__rerank_bge-reranker-v2-m3_on_hybrid_Qwen3-Embedding-0.6B.json"))
groups = defaultdict(list)
for qid, rk in zip(r["qids"], r["ranks"]):
    q = qs[qid]; hit = [ch[i]["doc"] == q["doc"] and q["para"] in ch[i]["paras"] for i in rk[:5]]
    v = (hit[0], any(hit))
    for g in (f"type:{q['type']}", f"gen:{q['generator']}", f"set:{q['set']}"): groups[g].append(v)
out = {g: {"n": len(v), "R@1": round(sum(x[0] for x in v) / len(v), 3), "R@5": round(sum(x[1] for x in v) / len(v), 3)} for g, v in sorted(groups.items())}
json.dump(out, open("results/breakdown.json", "w"), indent=1)
for g, v in out.items(): print(f"{g:28} {v}")
