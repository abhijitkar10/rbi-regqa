"""How much of each lender's KYC rulebook is a copy of the Commercial Banks one?
For every paragraph, word-3-gram Jaccard to its closest Commercial Banks KYC paragraph.
Out: results/near_copies.json + a printed table."""
import json, re
from collections import defaultdict

CB, OTHERS = 13141, [13109, 13090, 13064, 13040, 13014, 12988, 12969, 12943, 12927]
docs = {d["doc"]: d for d in map(json.loads, open("data/processed/docs.jsonl"))}
paras = defaultdict(list)
for p in map(json.loads, open("data/processed/paras.jsonl")):
    if p["para"] != "preamble": paras[p["doc"]].append(p)


def grams(t):
    w = re.findall(r"[a-z0-9]+", t.lower())
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


cb = [grams(p["text"]) for p in paras[CB]]
rows = []
for d in OTHERS:
    sims = [max((len(g & c) / len(g | c) for c in cb if g | c), default=0) for g in (grams(p["text"]) for p in paras[d])]
    n = len(sims)
    rows.append({"doc": d, "entity": docs[d]["entity"], "paragraphs": n,
                 "identical_ge_0.9": round(sum(s >= 0.9 for s in sims) / n, 3),
                 "edited_0.5_0.9": round(sum(0.5 <= s < 0.9 for s in sims) / n, 3),
                 "different_lt_0.5": round(sum(s < 0.5 for s in sims) / n, 3)})
json.dump(rows, open("results/near_copies.json", "w"), indent=1)
print(f"{'lender':40s} paras  >=0.9  0.5-0.9  <0.5")
for r in rows:
    print(f"{r['entity']:40s} {r['paragraphs']:5d}  {r['identical_ge_0.9']:.2f}   {r['edited_0.5_0.9']:.2f}    {r['different_lt_0.5']:.2f}")
