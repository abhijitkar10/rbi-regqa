"""Own-family check as a difference-in-differences. A reader's gap = acc on Nemotron-drafted minus acc on MiniMax-drafted
questions. MiniMax-drafted questions are harder for every reader, so raw accuracy cannot show self-preference; instead
  nemotron_pref = mean gap of Nemotron readers - mean gap of other-family readers   (>0: Nemotron favours its own)
  minimax_pref  = mean gap of other-family readers - gap of the MiniMax reader       (>0: MiniMax favours its own)
95% CI: 10,000 bootstrap resamples of questions within each generator. Ungraded answers are skipped (nanmean).
Out: results/self_pref.json"""
import glob, json
import numpy as np

SCORE = {"CORRECT": 1, "PARTIAL": 0.5, "WRONG": 0}
qs = [q for q in map(json.loads, open("data/benchmark/v0.jsonl")) if q["answerable"]]
idx = {q["qid"]: i for i, q in enumerate(qs)}
files = sorted(glob.glob("results/judged/v0__*__nvidia_stepfun-ai_step-5-preview.jsonl"))
readers = [f.split("__")[1] for f in files]
M = np.full((len(qs), len(readers)), np.nan)
for j, f in enumerate(files):
    for r in map(json.loads, open(f)):
        M[idx[r["qid"]], j] = SCORE[r["grade"]]
fam = np.array(["nemotron" if "nemotron" in r else "minimax" if "minimax" in r else "other" for r in readers])
gen = np.array([q["generator"] for q in qs])
A, B = np.where(gen == "nemotron")[0], np.where(gen == "minimax")[0]


def stats(a, b):
    gap = np.nanmean(M[a], 0) - np.nanmean(M[b], 0)
    o = gap[fam == "other"].mean()
    return gap, gap[fam == "nemotron"].mean() - o, o - gap[fam == "minimax"].mean()


gap, nem, mm = stats(A, B)
rng = np.random.default_rng(0)
boot = np.array([stats(rng.choice(A, len(A)), rng.choice(B, len(B)))[1:] for _ in range(10_000)])
lo, hi = np.percentile(boot, [2.5, 97.5], 0)
out = {"gap": {r: round(float(g), 3) for r, g in zip(readers, gap)},
       "graded": {r: int((~np.isnan(M[:, j])).sum()) for j, r in enumerate(readers)},
       "nemotron_pref": [round(float(x), 3) for x in (nem, lo[0], hi[0])],
       "minimax_pref": [round(float(x), 3) for x in (mm, lo[1], hi[1])]}
json.dump(out, open("results/self_pref.json", "w"), indent=1)
print(json.dumps(out, indent=1))
