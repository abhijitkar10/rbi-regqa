"""Per-reader results from results/judged/*.jsonl -> results/readers.json and a printed table.

acc        mean grade on answerable (CORRECT 1, PARTIAL 0.5, WRONG 0)
cite_gold  share of answered (not refused) answerable questions whose citations include the gold paragraph
false_ref  share of answerable questions refused
unans_ref  share of unanswerable questions correctly refused
by_gen     acc split by which model drafted the question (own-family check)
agreement  between two judges on the questions both graded (exact match and Cohen's kappa)
Usage: python analysis/summarize_answers.py STEM[,STEM2] PRIMARY_JUDGE [SECOND_JUDGE]
"""
import glob, json, sys
from collections import defaultdict

stems, j1 = sys.argv[1].split(","), sys.argv[2].replace(":", "_").replace("/", "_")  # e.g. v0,unans_v1
j2 = sys.argv[3].replace(":", "_").replace("/", "_") if len(sys.argv) > 3 else None
qs = {q["qid"]: q for st in stems for q in map(json.loads, open(f"data/benchmark/{st}.jsonl"))}
SCORE = {"CORRECT": 1, "PARTIAL": 0.5, "WRONG": 0}


def load(judge):
    rows = defaultdict(dict)
    for f in (f for st in stems for f in glob.glob(f"results/judged/{st}__*__{judge}.jsonl")):
        for r in map(json.loads, open(f)):
            rows[r["model"]][r["qid"]] = r
    return rows


R, out = load(j1), {}
for model, rows in sorted(R.items()):
    ans = [r for r in rows.values() if r["answerable"]]
    un = [r for r in rows.values() if not r["answerable"]]
    answered = [r for r in ans if not r["refused"]]
    by_gen = defaultdict(list)
    for r in ans:
        by_gen[qs[r["qid"]]["generator"]].append(SCORE[r["grade"]])
    out[model] = {"n_ans": len(ans), "n_unans": len(un),
                  "acc": round(sum(SCORE[r["grade"]] for r in ans) / max(len(ans), 1), 3),
                  "cite_gold": round(sum(r["cite_gold"] for r in answered) / max(len(answered), 1), 3),
                  "false_ref": round(sum(r["refused"] for r in ans) / max(len(ans), 1), 3),
                  "unans_ref": round(sum(r["refused"] for r in un) / max(len(un), 1), 3),
                  "unans_ref_soft": round(sum(r.get("refused_soft", r["refused"]) for r in un) / max(len(un), 1), 3),
                  "false_ref_soft": round(sum(r.get("refused_soft", r["refused"]) for r in ans) / max(len(ans), 1), 3),
                  "empty": sum(r.get("empty", False) for r in rows.values()),
                  "by_gen": {g: round(sum(v) / len(v), 3) for g, v in by_gen.items()}}
if j2:
    R2 = load(j2); same = tot = 0; pairs = []
    for model in R:
        for qid, r in R[model].items():
            r2 = R2.get(model, {}).get(qid)
            if r2 and r["answerable"] and not r["refused"]:
                pairs.append((r["grade"], r2["grade"]))
    if pairs:
        labels = list(SCORE); n = len(pairs)
        po = sum(a == b for a, b in pairs) / n
        pe = sum((sum(a == l for a, _ in pairs) / n) * (sum(b == l for _, b in pairs) / n) for l in labels)
        out["_judge_agreement"] = {"n": n, "exact": round(po, 3), "kappa": round((po - pe) / (1 - pe), 3) if pe < 1 else None}
json.dump(out, open("results/readers.json" if "v0" in stems else f"results/readers_{stems[0]}.json", "w"), indent=1)
print(f"{'model':48s} acc   cite  falseRef(soft) unansRef(soft) empty  by-generator")
for m, v in out.items():
    if m.startswith("_"): print(m, v); continue
    print(f"{m:48s} {v['acc']:.2f}  {v['cite_gold']:.2f}  {v['false_ref']:.2f}({v['false_ref_soft']:.2f})     {v['unans_ref']:.2f}({v['unans_ref_soft']:.2f})     {v['empty']:3d}  {v['by_gen']}")
