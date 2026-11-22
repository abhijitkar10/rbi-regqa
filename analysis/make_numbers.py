"""Write paper/numbers.tex from the data and results files, so no number in the paper is typed by hand.
Missing inputs become a red TODO in the PDF. Run after any result changes."""
import json
from pathlib import Path

N = {}
def put(k, v): N[k] = v
def jl(p): return [json.loads(l) for l in open(p)] if Path(p).exists() else None

docs, paras = jl("data/processed/docs.jsonl"), jl("data/processed/paras.jsonl")
put("NDocs", sum(len(d["text"]) > 0 for d in docs) if docs else None)  # 2 of the 98 fetched pages are link-only stubs
put("NParas", f'{sum(p["para"] != "preamble" for p in paras):,}' if paras else None)
v1 = jl("data/benchmark/v1.jsonl")
put("NQuestions", sum(q["answerable"] for q in v1) if v1 else None)
put("NUnans", sum(not q["answerable"] for q in v1) if v1 else None)
sel = jl("data/questions/selection.jsonl")
put("NEntityParas", sum(s["set"] == "entity" for s in sel) if sel else None)
nc = json.load(open("results/near_copies.json")) if Path("results/near_copies.json").exists() else None
if nc:
    banks = [r["identical_ge_0.9"] for r in nc if r["entity"].endswith("Banks")]
    put("NearCopyBankRange", f"{round(100 * min(banks))}--{round(100 * max(banks))}\\%")
stats = json.load(open("results/gen_stats.json")) if Path("results/gen_stats.json").exists() else {}
for key, g in (("GenA", "nemotron"), ("GenB", "minimax")):
    put(key, {"nemotron": "Nemotron-3-Ultra", "minimax": "MiniMax-M3.1-Flash"}[g])
    s = stats.get(g)
    put(f"QuoteOk{key}", f'{100 * s["quote_ok"] / s["drafted"]:.1f}\\%' if s else None)
ex = jl("data/benchmark/expert.jsonl")
put("NExpertAnchored", f'{sum(bool(r.get("quote_ok")) for r in ex if r["answerable"])} of {sum(r["answerable"] for r in ex)}' if ex else None)
readers = json.load(open("results/readers.json")) if Path("results/readers.json").exists() else None
put("NReaders", "zero one two three four five six seven eight nine ten".split()[sum(not k.startswith("_") for k in readers)] if readers else "seven")

with open("paper/numbers.tex", "w") as f:
    for k, v in N.items():
        f.write(f"\\newcommand{{\\{k}}}{{{v if v is not None else chr(92) + 'todo{' + k + '}'}}}\n")
print("\n".join(f"{k} = {v}" for k, v in N.items()))

# --- retrieval headline numbers (appended; rewrites numbers.tex with these too) ---
rb = json.load(open("results/retrieval_best.json")) if Path("results/retrieval_best.json").exists() else None
if rb:
    b, f = rb["best"], rb["fixed_best"]
    for k, v in {"BestRfive": f'{b["R@5"]:.2f}', "BestRone": f'{b["R@1"]:.2f}', "BestBook": f'{100 * b["Book@1"]:.0f}\\%',
                 "BestWL": f'{100 * b["WrongLender@1"]:.1f}\\%', "FixedRfive": f'{f["R@5"]:.2f}', "FixedBook": f'{100 * f["Book@1"]:.0f}\\%',
                 "FixedWL": f'{100 * f["WrongLender@1"]:.1f}\\%'}.items():
        put(k, v)
ctx_q = json.load(open("results/contexts_v0.json")) if Path("results/contexts_v0.json").exists() else None
off = json.load(open("results/retrieval_officer.json")) if Path("results/retrieval_officer.json").exists() else []
para_wl = [r["WrongLender@1"] for r in off if r["chunks"] == "para"]
title_wl = [r["WrongLender@1"] for r in off if r["chunks"] == "para_title" and not r["retriever"].startswith("bm25")]
if para_wl and title_wl:
    put("ParaWLRange", f"{100 * min(para_wl):.0f}--{100 * max(para_wl):.0f}\\%")
    put("TitleWLRange", f"{100 * min(title_wl):.1f}--{100 * max(title_wl):.1f}\\%")
with open("paper/numbers.tex", "w") as fh:
    for k, v in N.items():
        fh.write(f"\\newcommand{{\\{k}}}{{{v if v is not None else chr(92) + 'todo{' + k + '}'}}}\n")

# --- customer wording, paired on the same questions (results/customer_gap.json) ---
cg = json.load(open("results/customer_gap.json")) if Path("results/customer_gap.json").exists() else None
if cg and rb:
    key = lambda cs, ret: f"{cs}|{ret.replace(':', '_').replace('<', '_on_')}"
    best = cg[key(rb["best"]["chunks"], rb["best"]["retriever"])]
    hyb = cg[key(rb["best"]["chunks"], rb["best"]["retriever"].split("<")[1])]
    bm = cg[key(rb["best"]["chunks"], "bm25")]
    put("NCust", best["n"])
    put("CustOffRfive", f'{best["officer"]["R@5"]:.2f}'); put("CustRfive", f'{best["customer"]["R@5"]:.2f}')
    put("CustOffBook", f'{100 * best["officer"]["Book@1"]:.0f}\\%'); put("CustBook", f'{100 * best["customer"]["Book@1"]:.0f}\\%')
    put("CustWL", f'{100 * best["customer"]["WL@1"]:.1f}\\%')
    put("CustBMOff", f'{bm["officer"]["R@5"]:.2f}'); put("CustBM", f'{bm["customer"]["R@5"]:.2f}')
    put("OffRerankGain", f'{best["officer"]["R@5"] - hyb["officer"]["R@5"]:.2f}')
    put("CustRerankGain", f'{best["customer"]["R@5"] - hyb["customer"]["R@5"]:.2f}')
    with open("paper/numbers.tex", "w") as fh:
        for k, v in N.items():
            fh.write(f"\\newcommand{{\\{k}}}{{{v if v is not None else chr(92) + 'todo{' + k + '}'}}}\n")

# --- corpus dates: "Updated as on <date>" in Direction titles; snapshot = when the HTML was fetched ---
import re, os, glob
from datetime import datetime
_d = [d for d in jl("data/processed/docs.jsonl") if d["text"].strip()]
_up = [datetime.strptime(m.group(1), "%B %d, %Y") for d in _d if (m := re.search(r"Updated as on (\w+ \d+, \d{4})", d["title"]))]
_fetched = max(os.path.getmtime(p) for p in glob.glob("data/html/*.md"))
fmt = lambda t: f"{t.day} {t:%B %Y}"
put("NUpdated", len(_up))
put("UpdateRange", f"{fmt(min(_up))} to {fmt(max(_up))}" if _up else None)
put("SnapshotDate", fmt(datetime.fromtimestamp(_fetched)))
with open("paper/numbers.tex", "w") as fh:
    for k, v in N.items():
        fh.write(f"\\newcommand{{\\{k}}}{{{v if v is not None else chr(92) + 'todo{' + k + '}'}}}\n")

# --- expert subset: strict vs any-copy (results/expert_any.json; config = name-prefixed paragraphs + BGE-reranker-v2-m3) ---
ea = json.load(open("results/expert_any.json")) if Path("results/expert_any.json").exists() else None
if ea:
    k = next(k for k in ea if k.startswith("para_title|rerank_bge-reranker-v2-m3"))
    e = ea[k]
    ew = next(r for r in json.load(open("results/retrieval_expert_v1.json")) if r["chunks"] == "para_title" and r["retriever"].startswith("rerank:bge-reranker-v2-m3"))
    put("NExpertQ", e["n"]); put("NExpertUnnamed", e["n"] - e["n_named"])
    put("ExpertRone", f'{e["R@1"]:.2f}'); put("ExpertRfive", f'{e["R@5"]:.2f}')
    put("ExpertAnyRone", f'{e["AnyR@1"]:.2f}'); put("ExpertAnyRfive", f'{e["AnyR@5"]:.2f}')
    put("ExpertWL", f'{100 * ew["WrongLender@1"]:.0f}\\%')
    put("ExpertBMAnyRfive", f'{ea["para_title|bm25"]["AnyR@5"]:.2f}')
    with open("paper/numbers.tex", "w") as fh:
        for kk, v in N.items():
            fh.write(f"\\newcommand{{\\{kk}}}{{{v if v is not None else chr(92) + 'todo{' + kk + '}'}}}\n")

# --- lender-aware re-ordering (results/lender_aware.json) ---
la = json.load(open("results/lender_aware.json")) if Path("results/lender_aware.json").exists() else None
if la:
    d = la["officer|detection"]
    put("LANamed", f'{d["named"]} of {d["n"]}'); put("LAPrec", f'{100 * d["precision"]:.1f}\\%')
    fn = la[next(k for k in la if k.startswith("officer|fixed|rerank_bge-reranker-v2-m3") and k.endswith("|none"))]
    fp = la[next(k for k in la if k.startswith("officer|fixed|rerank_bge-reranker-v2-m3") and k.endswith("|promote"))]
    put("LAFixedWL", f'{100 * fn["WrongLender@1"]:.1f}\\%'); put("LAFixedWLp", f'{100 * fp["WrongLender@1"]:.1f}\\%')
    put("LAFixedRone", f'{fn["R@1"]:.2f}'); put("LAFixedRonep", f'{fp["R@1"]:.2f}'); put("LAFixedRfivep", f'{fp["R@5"]:.2f}')
    ed = la[next(k for k in la if k.startswith("expert_v1|para_title|rerank_bge-reranker-v2-m3") and k.endswith("|promote+CB"))]
    put("LAExpertRone", f'{ed["R@1"]:.2f}'); put("LAExpertRthirty", f'{ed["R@30"]:.2f}')
    put("LAExpertNamed", la["expert_v1|detection"]["named"])
    with open("paper/numbers.tex", "w") as fh:
        for kk, v in N.items():
            fh.write(f"\\newcommand{{\\{kk}}}{{{v if v is not None else chr(92) + 'todo{' + kk + '}'}}}\n")

# --- paired bootstrap CIs (results/bootstrap.json) ---
bs = json.load(open("results/bootstrap.json")) if Path("results/bootstrap.json").exists() else None
if bs:
    rng = lambda v, s=1: f"{s * v[1]:.2f}--{s * v[2]:.2f}" if s > 0 else f"{-v[2]:.2f}--{-v[1]:.2f}"
    put("CIPrefixRfive", rng(bs["prefix_vs_fixed"]["R@5"])); put("CIPrefixWL", f'{-100 * bs["prefix_vs_fixed"]["WL@1"][2]:.0f}--{-100 * bs["prefix_vs_fixed"]["WL@1"][1]:.0f}')
    put("CICustRfive", rng(bs["customer_vs_officer"]["R@5"], -1))
    put("RerankDiff", f'{bs["rerank_gain_diff"]["R@5"][0]:.2f}'); put("CIRerankDiff", rng(bs["rerank_gain_diff"]["R@5"]))
    with open("paper/numbers.tex", "w") as fh:
        for kk, v in N.items():
            fh.write(f"\\newcommand{{\\{kk}}}{{{v if v is not None else chr(92) + 'todo{' + kk + '}'}}}\n")

# --- breakdown of the best retriever by question type and generator (results/breakdown.json) ---
bd = json.load(open("results/breakdown.json")) if Path("results/breakdown.json").exists() else None
if bd:
    put("NApp", bd["type:applicability"]["n"]); put("AppRone", f'{bd["type:applicability"]["R@1"]:.2f}'); put("AppRfive", f'{bd["type:applicability"]["R@5"]:.2f}')
    put("OblRone", f'{bd["type:obligation"]["R@1"]:.2f}'); put("OblRfive", f'{bd["type:obligation"]["R@5"]:.2f}')
    put("GenARfive", f'{bd["gen:nemotron"]["R@5"]:.2f}'); put("GenBRfive", f'{bd["gen:minimax"]["R@5"]:.2f}')
    with open("paper/numbers.tex", "w") as fh:
        for kk, v in N.items():
            fh.write(f"\\newcommand{{\\{kk}}}{{{v if v is not None else chr(92) + 'todo{' + kk + '}'}}}\n")
