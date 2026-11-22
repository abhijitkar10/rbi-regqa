"""Why the best retriever misses: every question whose gold paragraph is not in the top 5, on rulebook and customer
wording. Each miss gets the first matching tag:
  near_copy   a top-5 chunk holds a near-identical copy of the gold paragraph (word-trigram Jaccard >= 0.9) in another rulebook
  right_book  the gold rulebook is in the top 5, but not the gold paragraph
  wrong_book  top 1 is another lender's rulebook on the same topic (different text)
  off_topic   anything else
Out: results/miss_analysis.json, paper/tab_misses.tex"""
import json, re, sys
from collections import Counter
sys.path.insert(0, "src"); sys.path.insert(0, "analysis")
from retrieve import load_chunks

docs = {d["doc"]: d for d in map(json.loads, open("data/processed/docs.jsonl"))}
text = {(p["doc"], p["para"]): p["text"] for p in map(json.loads, open("data/processed/paras.jsonl"))}
ch = load_chunks("para_title")
BEST = "para_title__rerank_bge-reranker-v2-m3_on_hybrid_Qwen3-Embedding-0.6B"
SETS = {"officer": "data/benchmark/v0.jsonl", "v1_customer": "data/benchmark/v1_customer.jsonl"}
TAGS = ["near_copy", "right_book", "wrong_book", "off_topic"]


def grams(t):
    w = re.findall(r"[a-z0-9]+", t.lower())
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


def jac(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


ALL = {k: grams(t) for k, t in text.items() if k[1] != "preamble"}


def n_copies(q):  # other rulebooks holding a near-identical copy of the gold paragraph (boilerplate if many)
    g = ALL[(q["doc"], q["para"])]
    return len({d for (d, p), h in ALL.items() if d != q["doc"] and jac(g, h) >= 0.9})


def neighbour(q, rk):  # a gold-rulebook paragraph within 3 numbers of the gold one is in the top 5
    num = lambda p: int(m.group()) if (m := re.match(r"\d+", p)) else None
    g = num(q["para"])
    return g is not None and any(c["doc"] == q["doc"] and (n := num(p)) is not None and 0 < abs(n - g) <= 3
                                 for c in (ch[i] for i in rk[:5]) for p in c["paras"])


def tag(q, rk):
    g = grams(text[(q["doc"], q["para"])])
    top5 = [ch[i] for i in rk[:5]]
    if any(c["doc"] != q["doc"] and jac(g, grams(text[(c["doc"], p)])) >= 0.9 for c in top5 for p in c["paras"]):
        return "near_copy"
    if any(c["doc"] == q["doc"] for c in top5):
        return "right_book"
    return "wrong_book" if docs[top5[0]["doc"]]["topic"] == docs[q["doc"]]["topic"] else "off_topic"


out, examples = {}, {}
for stem, qfile in SETS.items():
    qs = {q["qid"]: q for q in map(json.loads, open(qfile)) if q["answerable"]}
    r = json.load(open(f"results/rankings/{stem}__{BEST}.json"))
    misses = []
    for qid, rk in zip(r["qids"], r["ranks"]):
        q = qs[qid]
        hit = [ch[i]["doc"] == q["doc"] and q["para"] in ch[i]["paras"] for i in rk]
        if any(hit[:5]): continue
        t = tag(q, rk)
        misses.append({"qid": qid, "tag": t, "gold_rank": hit.index(True) + 1 if any(hit) else None,
                       "type": q["type"], "gold_chars": len(text[(q["doc"], q["para"])]), "copies": n_copies(q), "neighbour": neighbour(q, rk)})
        examples.setdefault(f"{stem}|{t}", []).append({"qid": qid, "question": q["question"], "gold": f'{docs[q["doc"]]["title"][:90]} para {q["para"]}',
                                                     "top1": f'{docs[ch[rk[0]]["doc"]]["title"][:90]} para {ch[rk[0]]["paras"]}'})
    c = Counter(m["tag"] for m in misses)
    out[stem] = {"n": len(qs), "misses": len(misses), "tags": {t: c[t] for t in TAGS},
                 "gold_in_top30": sum(m["gold_rank"] is not None for m in misses),
                 "right_book_neighbour": sum(m["neighbour"] for m in misses if m["tag"] == "right_book"),
                 "boilerplate_gold": sum(m["copies"] >= 10 for m in misses),
                 "by_type": dict(Counter(m["type"] for m in misses)), "rows": misses}
json.dump({"results": out, "examples": examples}, open("results/miss_analysis.json", "w"), indent=1)

NAME = {"near_copy": "Same text, other lender", "right_book": "Right rulebook, other para.",
        "wrong_book": "Other lender, other text", "off_topic": "Other topic"}
o, c = out["officer"], out["v1_customer"]
rows = [f"{NAME[t]} & {o['tags'][t]} & {c['tags'][t]} \\\\" for t in TAGS]
rows.insert(2, rf"\quad neighbour ($\pm$3) in top 5 & {o['right_book_neighbour']} & {c['right_book_neighbour']} \\")
tex = r"""\begin{table}[t]
\centering\small
\begin{tabular}{lrr}
\toprule
Miss type & Rulebook & Customer \\
\midrule
""" + "\n".join(rows) + rf"""
\midrule
Misses (gold not in top 5) & {o['misses']}/{o['n']} & {c['misses']}/{c['n']} \\
Boilerplate gold & {o['boilerplate_gold']} & {c['boilerplate_gold']} \\
Gold still in top 30 & {o['gold_in_top30']} & {c['gold_in_top30']} \\
\bottomrule
\end{{tabular}}
\caption{{Why the best retriever (name-prefixed paragraphs, hybrid, BGE-reranker-v2-m3) misses. Each miss takes the first
matching type. ``Same text'': word-trigram Jaccard $\geq0.9$ with the gold paragraph. ``Neighbour'': a gold-rulebook
paragraph numbered within 3 of the gold one. ``Boilerplate'': the gold paragraph has near-copies in 10 or more rulebooks.}}
\label{{tab:misses}}
\end{{table}}
"""
open("paper/tab_misses.tex", "w").write(tex)
for stem, v in out.items():
    print(stem, {k: v[k] for k in v if k != "rows"})
