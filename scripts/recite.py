"""Recompute citations in stored answers with answer.parse_cites, and cite_gold / cited_any in judged files (deterministic,
no LLM). Fixes rows written before 2026-11-23, when only the exact form [S1] was parsed. Files changed in the last
15 minutes are skipped (a running job may be appending); rerun later. Usage: .venv/bin/python scripts/recite.py"""
import glob, json, os, sys, time
sys.path.insert(0, "src")
from answer import parse_cites
from retrieve import load_chunks

ch = load_chunks("para_title")
qs = {q["qid"]: q for f in glob.glob("data/benchmark/*.jsonl") for q in map(json.loads, open(f))}
busy = lambda f: time.time() - os.path.getmtime(f) < 900


def rewrite(f, rows):
    tmp = f + ".tmp"
    with open(tmp, "w") as fh:
        fh.writelines(json.dumps(r) + "\n" for r in rows)
    os.replace(tmp, f)


answers = {}
for f in sorted(glob.glob("results/answers/*.jsonl")):
    rows, n = [json.loads(l) for l in open(f)], 0
    for r in rows:
        c = parse_cites(r["answer"])
        n += c != r["cited"]; r["cited"] = c
    answers[os.path.basename(f)[:-6]] = {r["qid"]: r for r in rows}
    if n and busy(f): print("skip (busy)", f); continue
    if n: rewrite(f, rows); print(f"{n:4d} cited fixed  {f}")
for f in sorted(glob.glob("results/judged/*.jsonl")):
    stem, reader = os.path.basename(f).split("__")[:2]
    A, rows, n = answers.get(f"{stem}__{reader}", {}), [json.loads(l) for l in open(f)], 0
    for r in rows:
        a, q = A.get(r["qid"]), qs[r["qid"]]
        if a is None or "cite_gold" not in r: continue
        cited = [ch[a["ctx"][s - 1]] for s in a["cited"]]
        new = (any(c["doc"] == q["doc"] and q["para"] in c["paras"] for c in cited), bool(cited))
        n += new != (r["cite_gold"], r["cited_any"]); r["cite_gold"], r["cited_any"] = new
    if n and busy(f): print("skip (busy)", f); continue
    if n: rewrite(f, rows); print(f"{n:4d} cite_gold fixed  {f}")
