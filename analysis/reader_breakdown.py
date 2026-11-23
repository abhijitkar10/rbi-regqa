"""Reader accuracy (Step-5 grades, v0) split by question type, by set (main vs edited-copy 'entity' paragraphs), and by
whether the gold paragraph was in the reader's top-5 context. Mean over readers of each reader's mean (ungraded skipped).
Out: results/reader_breakdown.json"""
import glob, json, sys, warnings
warnings.simplefilter("ignore", RuntimeWarning)
import numpy as np
sys.path.insert(0, "src")
from retrieve import load_chunks

SCORE = {"CORRECT": 1, "PARTIAL": 0.5, "WRONG": 0}
qs = [q for q in map(json.loads, open("data/benchmark/v0.jsonl")) if q["answerable"]]
idx = {q["qid"]: i for i, q in enumerate(qs)}
files = sorted(glob.glob("results/judged/v0__*__nvidia_stepfun-ai_step-5-preview.jsonl"))
M = np.full((len(qs), len(files)), np.nan)
for j, f in enumerate(files):
    for r in map(json.loads, open(f)):
        M[idx[r["qid"]], j] = SCORE[r["grade"]]
ch, ctx = load_chunks("para_title"), json.load(open("results/contexts_v0.json"))
gold_in = np.array([any(ch[i]["doc"] == q["doc"] and q["para"] in ch[i]["paras"] for i in ctx[q["qid"]][:5]) for q in qs])


def acc(mask):
    return {"n": int(mask.sum()), "acc": round(float(np.nanmean(np.nanmean(M[mask], 0))), 3)}


out = {"type": {t: acc(np.array([q["type"] == t for q in qs])) for t in sorted({q["type"] for q in qs})},
       "set": {s: acc(np.array([q["set"] == s for q in qs])) for s in ("main", "entity")},
       "gold_in_context": {"yes": acc(gold_in), "no": acc(~gold_in)}}
json.dump(out, open("results/reader_breakdown.json", "w"), indent=1)
print(json.dumps(out, indent=1))
