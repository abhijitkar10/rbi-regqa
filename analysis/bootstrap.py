"""Paired bootstrap 95% CIs (10,000 resamples over questions) for the paper's headline retrieval differences.
Out: results/bootstrap.json"""
import json, sys
import numpy as np
from pathlib import Path
sys.path.insert(0, "src")
from retrieve import load_chunks

docs = {d["doc"]: d for d in map(json.loads, open("data/processed/docs.jsonl"))}
Q = {}
for f in ("v0", "v1_customer", "expert_v1"):
    Q.update({q["qid"] + ("|c" if f == "v1_customer" else ""): q for q in map(json.loads, open(f"data/benchmark/{f}.jsonl")) if q["answerable"]})
CH = {}


def vec(stem, cs, name):
    """qid -> (R@1, R@5, WrongLender@1) for one ranking file."""
    ch = CH.setdefault(cs, load_chunks(cs)); r = json.load(open(f"results/rankings/{stem}__{cs}__{name}.json"))
    out = {}
    for qid, rk in zip(r["qids"], r["ranks"]):
        q = Q[qid + ("|c" if stem == "v1_customer" else "")]
        hit = [ch[i]["doc"] == q["doc"] and q["para"] in ch[i]["paras"] for i in rk[:5]]
        top = ch[rk[0]]["doc"]
        out[qid] = np.array([hit[0], any(hit), top != q["doc"] and docs[top]["topic"] == docs[q["doc"]]["topic"]], float)
    return out


def ci(a, b, rng=np.random.default_rng(0), n=10_000):
    """mean(b - a) per metric with a paired 95% CI; a, b: qid -> vector."""
    ids = sorted(set(a) & set(b)); d = np.stack([b[i] - a[i] for i in ids])
    boot = d[rng.integers(0, len(ids), (n, len(ids)))].mean(1)
    lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
    return {m: [round(x, 3) for x in (d.mean(0)[k], lo[k], hi[k])] for k, m in enumerate(("R@1", "R@5", "WL@1"))} | {"n": len(ids)}


BEST = ("para_title", "rerank_bge-reranker-v2-m3_on_hybrid_Qwen3-Embedding-0.6B")
FIXED = ("fixed", "rerank_bge-reranker-v2-m3_on_hybrid_bge-small-en-v1.5")
HYB = ("para_title", "hybrid_Qwen3-Embedding-0.6B")
o_best, o_fixed, o_hyb = vec("officer", *BEST), vec("officer", *FIXED), vec("officer", *HYB)
c_best, c_hyb = vec("v1_customer", *BEST), vec("v1_customer", *HYB)
res = {"prefix_vs_fixed": ci(o_fixed, o_best), "customer_vs_officer": ci(o_best, c_best),
       "rerank_gain_officer": ci(o_hyb, o_best), "rerank_gain_customer": ci(c_hyb, c_best)}
# difference in re-ranker gain (customer minus officer) on the shared questions
ids = sorted(set(c_best) & set(o_best))
dd = np.stack([(c_best[i] - c_hyb[i]) - (o_best[i] - o_hyb[i]) for i in ids])
boot = dd[np.random.default_rng(1).integers(0, len(ids), (10_000, len(ids)))].mean(1)
res["rerank_gain_diff"] = {"R@5": [round(dd.mean(0)[1], 3), *np.round(np.percentile(boot[:, 1], [2.5, 97.5]), 3).tolist()], "n": len(ids)}
json.dump(res, open("results/bootstrap.json", "w"), indent=1)
for k, v in res.items(): print(k, v)
