"""Figure 1: WrongLender@1 by chunking and retriever (rulebook wording). Out: paper/fig_wronglender.pdf"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

off = json.load(open("results/retrieval_officer.json"))
SETS = [("fixed", "800-char\nwindows"), ("para", "Paragraphs"), ("para_title", "Paragraphs +\nrulebook name")]
KINDS = [("bm25", "BM25", "#2a78d6"), ("dense", "Dense", "#eb6834"), ("hybrid", "Hybrid", "#1baf7a"), ("rerank:bge-reranker-v2-m3", "+ re-ranker", "#eda100")]


def pick(cs, kind):  # BM25, or the best variant of a kind by MRR (as in Table 2)
    rows = [r for r in off if r["chunks"] == cs and r["retriever"].startswith(kind)]
    return max(rows, key=lambda r: r["MRR@10"])["WrongLender@1"] * 100


plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(3.1, 1.9))
w = 0.2
for k, (kind, label, color) in enumerate(KINDS):
    xs = [i + (k - 1.5) * w for i in range(len(SETS))]
    ys = [pick(cs, kind) for cs, _ in SETS]
    ax.bar(xs, ys, w - 0.03, color=color, label=label, zorder=2)
    for x, y in zip(xs, ys):
        ax.text(x, y + 0.3, f"{y:.0f}", ha="center", va="bottom", fontsize=6, color="#52514e")
ax.set_xticks(range(len(SETS)), [n for _, n in SETS])
ax.set_ylabel("Wrong lender at rank 1 (%)")
ax.yaxis.grid(True, color="#e5e4df", lw=0.5, zorder=0); ax.tick_params(length=0)
ax.spines["left"].set_color("#b0afa8"); ax.spines["bottom"].set_color("#b0afa8")
ax.legend(ncol=4, frameon=False, fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, 1.16), handlelength=1, columnspacing=0.8)
fig.tight_layout(pad=0.2)
fig.savefig("paper/fig_wronglender.pdf"); fig.savefig("/private/tmp/claude-501/-Users-abhijitkar/c5117db4-8813-4561-af14-3c92571453ec/scratchpad/fig.png", dpi=200)
print("ok")
