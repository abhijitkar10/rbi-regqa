"""Reader table (Table 5) from results/readers.json (v0 + unans_v1) and results/readers_v0best.json (best-retriever
context ablation, two readers). Also writes results/reader_ctx.json: how often the gold paragraph is in each context set.
Readers not fully graded are marked with a dagger.  Out: paper/tab_readers.tex"""
import json, sys
sys.path.insert(0, "src")
from retrieve import load_chunks

NAME = {"nvidia:minimaxai/minimax-m3.1-flash": "MiniMax-M3.1", "nvidia:nvidia/nemotron-3.5-bolt-e4b": "Nemotron Bolt",
        "nvidia:nvidia/nemotron-3.5-lightning-30b-a3b": "Nemotron Lightning", "groq:qwen/qwen3.8-27b": "Qwen3.8-27B",
        "groq:openai/gpt-oss-20b": "gpt-oss-20b", "mistral:ministral-8b-latest": "Ministral-8B",
        "mistral:ministral-14b-latest": "Ministral-14B"}
ch = load_chunks("para_title")
qs = [q for q in map(json.loads, open("data/benchmark/v0.jsonl")) if q["answerable"]]
ctx = {}
for stem in ["v0", "v0best"]:
    c = json.load(open(f"results/contexts_{stem}.json"))
    ctx[stem] = round(sum(any(ch[i]["doc"] == q["doc"] and q["para"] in ch[i]["paras"] for i in c[q["qid"]][:5]) for q in qs) / len(qs), 3)
json.dump(ctx, open("results/reader_ctx.json", "w"))

main, best = json.load(open("results/readers.json")), json.load(open("results/readers_v0best.json"))
N_ANS, N_UN = len(qs), sum(1 for _ in open("data/benchmark/unans_v1.jsonl"))


def row(m, v, label=None):
    done = v["n_ans"] == N_ANS and v["n_unans"] in (0, N_UN)
    un = f"{v['unans_ref']:.2f}/{v['unans_ref_soft']:.2f}" if v["n_unans"] else "--"
    return (f"{label or NAME.get(m, m)}{'' if done else '$^\\dagger$'} & {v['acc']:.2f} & {v['cite_gold']:.2f} & "
            f"{v['false_ref']:.2f} & {un} \\\\")


rows = [row(m, v) for m, v in sorted(((m, v) for m, v in main.items() if not m.startswith("_")), key=lambda kv: -kv[1]["acc"])]
abl = [row(m, v, NAME[m].split()[-1] + ", best ctx.") for m, v in sorted(best.items()) if not m.startswith("_")]
tex = r"""\begin{table}[t]
\centering\small\setlength{\tabcolsep}{4pt}
\begin{tabular}{lrrrr}
\toprule
Reader & Acc. & Cite & Ref. & Ref.\ unans. \\
 & & & ans. & strict/lenient \\
\midrule
""" + "\n".join(rows) + "\n\\midrule\n" + "\n".join(abl) + rf"""
\bottomrule
\end{{tabular}}
\caption{{Readers answering from the top 5 passages (gold paragraph in context for {ctx['v0']:.0%} of questions; {ctx['v0best']:.0%}
with the best retriever, bottom rows). Acc.: judge grade, correct 1, partial 0.5. Cite: answered questions whose citations
include the gold paragraph. Ref.: share answered NOT FOUND. $^\dagger$not yet fully graded.}}
\label{{tab:readers}}
\end{{table}}
""".replace("%", r"\%")
open("paper/tab_readers.tex", "w").write(tex)
print(ctx); print(tex)
