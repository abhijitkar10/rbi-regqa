"""Assemble the release files from v0 + verified unanswerables + rewrites.

data/benchmark/v1.jsonl           answerable (officer wording) + verified unanswerable
data/benchmark/v1_customer.jsonl  same questions in customer wording (rows without a rewrite are dropped)
data/benchmark/expert_v1.jsonl    hand-written subset: anchored answerables + the 'trick' unanswerables
"""
import json
from pathlib import Path


def jl(p): return [json.loads(l) for l in open(p)] if Path(p).exists() else []


v0 = jl("data/benchmark/v0.jsonl")
import glob
votes = {}
for f in sorted(glob.glob("data/benchmark/unans_verified__*.jsonl")):
    for u in jl(f):
        if all(v["verifier"] != u["verifier"] for v in votes.get(u["qid"], [])):  # one vote per verifier
            votes.setdefault(u["qid"], []).append(u)
n_ver = len(glob.glob("data/benchmark/unans_verified__*.jsonl"))
# keep an unanswerable question only if every verifier saw it and every one said NOT_ANSWERED
unans = [{k: v for k, v in vs[0].items() if k not in ("verdict", "verifier")} for vs in votes.values()
         if len(vs) == n_ver and all(v["verdict"] == "NOT_ANSWERED" for v in vs)]
v1 = v0 + unans
lay = {r["qid"]: r["question"] for r in jl("data/benchmark/lay_cache.jsonl") if r.get("lender_kept", True) and r.get("rewriter", "").startswith("nvidia:")}
cust = [{**q, "question_officer": q["question"], "question": lay[q["qid"]]} for q in v1 if q["qid"] in lay]
expert = [r for r in jl("data/benchmark/expert.jsonl") if not r["answerable"] or r.get("quote_ok")]
for r in expert:
    r["para"] = str(r.get("para")) if r["answerable"] else None
for name, rows in [("v1", v1), ("v1_customer", cust), ("expert_v1", expert)]:
    with open(f"data/benchmark/{name}.jsonl", "w") as f:
        for r in rows: f.write(json.dumps(r) + "\n")
    print(f"{name}: {sum(r['answerable'] for r in rows)} answerable, {sum(not r['answerable'] for r in rows)} unanswerable")
