"""Pairwise agreement between the three LLM judges on the v0 agreement sample (Step-5 grades everything; gpt-oss-120b
and Mistral Large 4 grade 30 random answers per reader). Exact match and Cohen's kappa on the answers both judges graded.
Out: results/judge_agreement.json"""
import glob, json
from itertools import combinations

J = {"step5": "nvidia_stepfun-ai_step-5-preview", "gptoss120b": "groq_openai_gpt-oss-120b",
     "mistral_large": "nvidia_mistralai_mistral-large-4-1t-a52b"}
G = {k: {(f.split("/")[-1].split("__")[1], j["qid"]): j["grade"]
         for f in glob.glob(f"results/judged/v0__*__{v}.jsonl") for j in map(json.loads, open(f))} for k, v in J.items()}


def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in set(a) | set(b))
    return round(po, 3), round((po - pe) / (1 - pe), 3)


out = {}
for x, y in combinations(J, 2):
    keys = sorted(G[x].keys() & G[y].keys())
    po, k = kappa([G[x][q] for q in keys], [G[y][q] for q in keys])
    out[f"{x}~{y}"] = {"n": len(keys), "exact": po, "kappa": k}
out["n_all_three"] = len(G["step5"].keys() & G["gptoss120b"].keys() & G["mistral_large"].keys())
json.dump(out, open("results/judge_agreement.json", "w"), indent=1)
print(json.dumps(out, indent=1))
