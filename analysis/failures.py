"""Failure kinds per reader, from Step-5-judged v0 + unans_v1 answers, with examples.
  wrong_lender  answered WRONG; gold paragraph not in context but another lender's rulebook on the same topic is
  hedge         unanswerable question declined in the reader's own words instead of NOT FOUND (lenient-only refusal)
  bad_cite      graded CORRECT with the gold paragraph in context, but the citations miss it
RBI text appears only as paragraph ids; answers are cut to 25 words. Out: results/failures.json, paper/tab_failures.tex"""
import glob, json, random, sys
from collections import defaultdict
sys.path.insert(0, "src")
from retrieve import load_chunks

NAME = {"nvidia:minimaxai/minimax-m3.1-flash": "MiniMax-M3.1", "nvidia:nvidia/nemotron-3.5-bolt-e4b": "Nemotron Bolt",
        "nvidia:nvidia/nemotron-3.5-lightning-30b-a3b": "Nemotron Lightning", "groq:qwen/qwen3.8-27b": "Qwen3.8-27B",
        "groq:openai/gpt-oss-20b": "gpt-oss-20b", "mistral:ministral-8b-latest": "Ministral-8B",
        "mistral:ministral-14b-latest": "Ministral-14B"}  # same as reader_table.py

docs = {d["doc"]: d for d in map(json.loads, open("data/processed/docs.jsonl"))}
qs = {q["qid"]: q for f in ("v0", "unans_v1") for q in map(json.loads, open(f"data/benchmark/{f}.jsonl"))}
ch = load_chunks("para_title")
KINDS = ["wrong_lender", "hedge", "bad_cite"]


def kind(q, a, j):
    if not q["answerable"]:
        return "hedge" if j.get("refused_soft") and not j["refused"] and not j.get("empty") else None
    if j["refused"]: return None
    gold_in = any(ch[i]["doc"] == q["doc"] and q["para"] in ch[i]["paras"] for i in a["ctx"])
    if j["grade"] == "WRONG" and not gold_in and any(
            ch[i]["doc"] != q["doc"] and docs[ch[i]["doc"]]["topic"] == docs[q["doc"]]["topic"] for i in a["ctx"]):
        return "wrong_lender"
    if j["grade"] == "CORRECT" and gold_in and not j["cite_gold"]:
        return "bad_cite"


counts, ex = defaultdict(lambda: dict.fromkeys(KINDS, 0)), defaultdict(list)
for f in sorted(glob.glob("results/judged/*__nvidia_stepfun-ai_step-5-preview.jsonl")):
    stem = f.split("/")[-1].split("__")[0]
    if stem not in ("v0", "unans_v1"): continue
    A = {}
    for a in map(json.loads, open(f"results/answers/{stem}__{f.split('__')[1]}.jsonl")):
        A[a["qid"]] = a
    for j in map(json.loads, open(f)):
        q, a = qs[j["qid"]], A.get(j["qid"])
        if a is None or not (k := kind(q, a, j)): continue
        counts[j["model"]][k] += 1
        ex[k].append({"qid": j["qid"], "reader": j["model"], "question": q["question"],
                      "gold": f'{docs[q["doc"]]["entity"] or docs[q["doc"]]["title"][:60]} para {q.get("para", "-")}',
                      "answer": " ".join(a["answer"].split()[:25])})
random.seed(0)
out = {"counts": counts, "examples": {k: random.sample(v, min(5, len(v))) for k, v in ex.items()}}
json.dump(out, open("results/failures.json", "w"), indent=1)

rows = [f"{NAME.get(m, m)} & " + " & ".join(str(c[k]) for k in KINDS) + r" \\" for m, c in sorted(counts.items())]
tex = r"""\begin{table}[h]
\centering\small\setlength{\tabcolsep}{4pt}
\begin{tabular}{lrrr}
\toprule
Reader & Wrong & Hedge & Missed \\
 & lender & & cite \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Failure counts per reader (Step-5 judge). Wrong lender: wrong answer with no gold paragraph but another
lender's same-topic rulebook in context. Hedge: unanswerable question declined without NOT FOUND. Missed cite: correct
answer, gold paragraph in context, not cited. The repository lists five examples of each.}
\label{tab:failures}
\end{table}
"""
open("paper/tab_failures.tex", "w").write(tex)
print(json.dumps(counts, indent=1))
for k in KINDS:
    print(k, out["examples"].get(k, [])[:1])
