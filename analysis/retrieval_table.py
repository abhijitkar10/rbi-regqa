"""results/retrieval_<stem>.json -> paper/tab_retrieval.tex (main table) and the best-config numbers.
Rows: each chunking x {BM25, best dense, best hybrid, best re-ranker}; officer wording, with the customer
wording's R@5 alongside when results/retrieval_v1_customer.json exists."""
import json
from pathlib import Path

off = json.load(open("results/retrieval_officer.json"))
cust = {(r["chunks"], r["retriever"]): r for r in json.load(open("results/retrieval_v1_customer.json"))} if Path("results/retrieval_v1_customer.json").exists() else {}
NAMES = {"fixed": "800-char windows", "para": "Paragraphs", "para_title": "Paragraphs + rulebook name"}


def pretty(ret):
    if ret == "bm25": return "BM25"
    kind, rest = ret.split(":", 1)
    if kind == "dense": return f"Dense ({rest.replace('-en-v1.5', '').replace('bge', 'BGE').replace('-Embedding-0.6B', '-Emb')})"
    if kind == "hybrid": return f"Hybrid (BM25 + {rest.replace('-en-v1.5', '').replace('bge', 'BGE').replace('-Embedding-0.6B', '-Emb')})"
    return "+ " + rest.split("<")[0].replace("bge-reranker-", "BGE-rr-")


lines = []
for cs in ("fixed", "para", "para_title"):
    rows = [r for r in off if r["chunks"] == cs]
    pick = [next(r for r in rows if r["retriever"] == "bm25")]
    for kind in ("dense", "hybrid"):
        pick.append(max((r for r in rows if r["retriever"].startswith(kind)), key=lambda r: r["MRR@10"]))
    pick += sorted((r for r in rows if r["retriever"].startswith("rerank")), key=lambda r: r["MRR@10"])
    lines.append(f"\\multicolumn{{7}}{{l}}{{\\textit{{{NAMES[cs]}}}}}\\\\")
    for r in pick:
        c = cust.get((cs, r["retriever"]))
        lines.append(f"{pretty(r['retriever'])} & {r['R@1']:.2f} & {r['R@5']:.2f} & {r['MRR@10']:.2f} & {r['Book@1']:.2f} & {100 * r['WrongLender@1']:.1f} & {c['R@5']:.2f} \\\\" if c else
                     f"{pretty(r['retriever'])} & {r['R@1']:.2f} & {r['R@5']:.2f} & {r['MRR@10']:.2f} & {r['Book@1']:.2f} & {100 * r['WrongLender@1']:.1f} & -- \\\\")
    lines.append("\\midrule")
tex = ("\\begin{table*}[t]\\centering\\small\\setlength{\\tabcolsep}{3pt}\n\\begin{tabular}{lcccccc}\\toprule\n"
       "Retriever & R@1 & R@5 & MRR & Book@1 & WL@1\\,\\% & R@5$_{\\text{cust}}$\\\\\\midrule\n" + "\n".join(lines[:-1]) +
       "\n\\bottomrule\\end{tabular}\n\\caption{Retrieval on " + str(off[0]["n"]) + " answerable questions. A hit is a chunk from the gold Direction covering the gold paragraph. "
       "Book@1: top chunk from the gold Direction. WL@1: top chunk is the same topic in another lender's Direction. "
       "R@5$_{\\text{cust}}$: same retriever on the plain-language paraphrases. Dense and hybrid rows show the best embedding model by MRR.}\\label{tab:retrieval}\n\\end{table*}\n")
open("paper/tab_retrieval.tex", "w").write(tex)
best = max(off, key=lambda r: r["MRR@10"]); fixed_best = max((r for r in off if r["chunks"] == "fixed"), key=lambda r: r["MRR@10"])
json.dump({"best": best, "fixed_best": fixed_best}, open("results/retrieval_best.json", "w"), indent=1)
print("best:", best["chunks"], best["retriever"], best["R@5"], best["WrongLender@1"], "| fixed best:", fixed_best["R@5"], fixed_best["WrongLender@1"])
