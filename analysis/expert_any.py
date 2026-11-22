"""Expert subset: strict hits (gold rulebook) vs any-copy hits (gold paragraph or a near-identical copy,
word-trigram Jaccard >= 0.9, in another lender's KYC rulebook). Most hand-written questions do not name a lender.
Out: results/expert_any.json"""
import json, re, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, "src")
from retrieve import load_chunks

KYC = [13141, 13109, 13090, 13064, 13040, 13014, 12988, 12969, 12943, 12927]
LENDER = re.compile(r"commercial bank|small finance|payments? bank|local area|regional rural|co-?operative|nbfc|non-banking|asset reconstruction|financial institution", re.I)
paras = defaultdict(dict)
for p in map(json.loads, open("data/processed/paras.jsonl")):
    if p["doc"] in KYC and p["para"] != "preamble": paras[p["doc"]][p["para"]] = p["text"]


def grams(t):
    w = re.findall(r"[a-z0-9]+", t.lower())
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


G = {(d, k): grams(t) for d, ps in paras.items() for k, t in ps.items()}
qs = {q["qid"]: q for q in map(json.loads, open("data/benchmark/expert_v1.jsonl")) if q["answerable"]}
copies = {}
for qid, q in qs.items():
    g = G[(q["doc"], q["para"])]
    copies[qid] = {(q["doc"], q["para"])} | {k for k, h in G.items() if k[0] != q["doc"] and g | h and len(g & h) / len(g | h) >= 0.9}

out, chunks = {}, {}
for f in sorted(Path("results/rankings").glob("expert_v1__*.json")):
    cs, name = f.stem.split("__")[1:3]
    ch = chunks.setdefault(cs, load_chunks(cs)); r = json.load(open(f))
    rows = []
    for qid, rk in zip(r["qids"], r["ranks"]):
        q = qs[qid]
        strict = [ch[i]["doc"] == q["doc"] and q["para"] in ch[i]["paras"] for i in rk[:5]]
        anyc = [any((ch[i]["doc"], p) in copies[qid] for p in ch[i]["paras"]) for i in rk[:5]]
        rows.append((strict[0], any(strict), anyc[0], any(anyc), bool(LENDER.search(q["question"]))))
    n = len(rows); named = [x for x in rows if x[4]]; unnamed = [x for x in rows if not x[4]]
    avg = lambda xs, i: round(sum(x[i] for x in xs) / len(xs), 3) if xs else None
    out[f"{cs}|{name}"] = {"n": n, "n_named": len(named), "R@1": avg(rows, 0), "R@5": avg(rows, 1), "AnyR@1": avg(rows, 2), "AnyR@5": avg(rows, 3),
                           "R@5_named": avg(named, 1), "R@5_unnamed": avg(unnamed, 1), "AnyR@5_unnamed": avg(unnamed, 3)}
json.dump(out, open("results/expert_any.json", "w"), indent=1)
print("copies per question:", sorted(len(c) for c in copies.values()))
for k, v in sorted(out.items(), key=lambda kv: -kv[1]["AnyR@5"]):
    print(f"{k:72} {v}")
