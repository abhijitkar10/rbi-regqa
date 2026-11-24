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

# --- what the best retriever's misses are (results/miss_analysis.json) ---
ma = json.load(open("results/miss_analysis.json"))["results"] if Path("results/miss_analysis.json").exists() else None
if ma:
    o, c = ma["officer"], ma["v1_customer"]
    put("MissOff", o["misses"]); put("MissCust", c["misses"]); put("MissAll", o["misses"] + c["misses"])
    put("MissNearCopy", o["tags"]["near_copy"] + c["tags"]["near_copy"])
    put("MissOffRight", o["tags"]["right_book"]); put("MissCustRight", c["tags"]["right_book"])
    put("MissOffNeighbour", o["right_book_neighbour"]); put("MissCustOffTopic", c["tags"]["off_topic"])
    put("MissBoiler", o["boilerplate_gold"] + c["boilerplate_gold"])
    with open("paper/numbers.tex", "w") as fh:
        for kk, v in N.items():
            fh.write(f"\\newcommand{{\\{kk}}}{{{v if v is not None else chr(92) + 'todo{' + kk + '}'}}}\n")

# --- readers (results/readers.json, results/reader_ctx.json) ---
if Path("results/readers.json").exists() and Path("results/reader_ctx.json").exists():
    rc, ja = json.load(open("results/reader_ctx.json")), json.load(open("results/readers.json")).get("_judge_agreement")
    put("CtxRfive", f"{rc['v0']:.0%}".replace("%", r"\%")); put("CtxBestRfive", f"{rc['v0best']:.0%}".replace("%", r"\%"))
    if ja: put("JudgeN", ja["n"]); put("JudgeExact", f"{ja['exact']:.2f}"); put("JudgeKappa", f"{ja['kappa']:.2f}")
    if Path("results/judge_agreement.json").exists():  # third judge (analysis/judge_agreement.py)
        jg = json.load(open("results/judge_agreement.json"))
        put("JudgeThreeN", jg["step5~mistral_large"]["n"]); put("JudgeThreeKappa", f'{jg["step5~mistral_large"]["kappa"]:.2f}')
        put("JudgeOthersN", jg["gptoss120b~mistral_large"]["n"]); put("JudgeOthersKappa", f'{jg["gptoss120b~mistral_large"]["kappa"]:.2f}')
    with open("paper/numbers.tex", "w") as fh:
        for kk, v in N.items():
            fh.write(f"\\newcommand{{\\{kk}}}{{{v if v is not None else chr(92) + 'todo{' + kk + '}'}}}\n")

# --- own-family check (results/self_pref.json) ---
if Path("results/self_pref.json").exists():
    sp = json.load(open("results/self_pref.json"))
    for k, name in (("nemotron_pref", "PrefNem"), ("minimax_pref", "PrefMM")):
        v, lo, hi = sp[k]
        put(name, f"${v:+.3f}$"); put(name + "CI", f"$[{lo:+.3f}, {hi:+.3f}]$")
    with open("paper/numbers.tex", "w") as fh:
        for kk, v in N.items():
            fh.write(f"\\newcommand{{\\{kk}}}{{{v if v is not None else chr(92) + 'todo{' + kk + '}'}}}\n")

# --- reader accuracy by type / set / gold in context (results/reader_breakdown.json) ---
if Path("results/reader_breakdown.json").exists():
    rb = json.load(open("results/reader_breakdown.json"))
    put("RdApp", f"{rb['type']['applicability']['acc']:.2f}"); put("RdObl", f"{rb['type']['obligation']['acc']:.2f}")
    put("RdEntity", f"{rb['set']['entity']['acc']:.2f}"); put("RdMain", f"{rb['set']['main']['acc']:.2f}")
    put("RdGoldIn", f"{rb['gold_in_context']['yes']['acc']:.2f}"); put("RdGoldOut", f"{rb['gold_in_context']['no']['acc']:.2f}")
    put("NGoldOut", rb["gold_in_context"]["no"]["n"])
    with open("paper/numbers.tex", "w") as fh:
        for kk, v in N.items():
            fh.write(f"\\newcommand{{\\{kk}}}{{{v if v is not None else chr(92) + 'todo{' + kk + '}'}}}\n")

# --- reader results prose (readers.json, readers_v0best.json, failures.json) ---
if Path("results/readers.json").exists() and Path("results/readers_v0best.json").exists():
    rd = {m: v for m, v in json.load(open("results/readers.json")).items() if not m.startswith("_")}
    bst = {m: v for m, v in json.load(open("results/readers_v0best.json")).items() if not m.startswith("_")}
    rng = lambda k, ms=rd: f"{min(ms[m][k] for m in ms):.2f}--{max(ms[m][k] for m in ms):.2f}"
    put("RdAccRange", rng("acc")); put("RdCiteRange", rng("cite_gold")); put("RdFalseRefRange", rng("false_ref"))
    top = max(rd, key=lambda m: rd[m]["acc"]); put("RdTopAcc", f"{rd[top]['acc']:.2f}")
    Q, L, B = "groq:qwen/qwen3.8-27b", "nvidia:nvidia/nemotron-3.5-lightning-30b-a3b", "nvidia:nvidia/nemotron-3.5-bolt-e4b"
    put("QwenUnStrict", f"{rd[Q]['unans_ref']:.2f}"); put("QwenUnSoft", f"{rd[Q]['unans_ref_soft']:.2f}")
    put("OtherUnStrictRange", rng("unans_ref", {m: v for m, v in rd.items() if m != Q}))
    put("LightEmpty", rd[L]["empty"]); put("LightEmptyBest", bst[L]["empty"])
    for tag, m in (("Bolt", B), ("Light", L)):
        put(f"{tag}Acc", f"{rd[m]['acc']:.2f}"); put(f"{tag}AccBest", f"{bst[m]['acc']:.2f}")
        put(f"{tag}CiteBest", f"{bst[m]['cite_gold']:.2f}")
    if Path("results/failures.json").exists():
        fc = json.load(open("results/failures.json"))["counts"]
        put("FailWLMax", max(c["wrong_lender"] for c in fc.values())); put("FailHedgeQwen", fc[Q]["hedge"])
        put("FailHedgeOtherMax", max(c["hedge"] for m, c in fc.items() if m != Q))
    with open("paper/numbers.tex", "w") as fh:
        for kk, v in N.items():
            fh.write(f"\\newcommand{{\\{kk}}}{{{v if v is not None else chr(92) + 'todo{' + kk + '}'}}}\n")

# --- hand audit (results/audit.json from analysis/audit.py); stays \todo until a sheet is fully filled ---
if Path("results/audit.json").exists():
    au = json.load(open("results/audit.json"))
    q, u = au.get("questions"), au.get("unanswerable")
    ok = lambda s: s and s["complete"]
    put("AuditN", q["n"] if ok(q) else None); put("AuditFair", q["FAIR_Y_N"] if ok(q) else None)
    put("AuditCorrect", q["ANSWER_CORRECT_Y_N"] if ok(q) else None)
    put("AuditUnN", u["n"] if ok(u) else None); put("AuditUnTrue", u["TRULY_UNANSWERABLE_Y_N"] if ok(u) else None)
    put("AuditUnFair", u["FAIR_Y_N"] if ok(u) else None)
    with open("paper/numbers.tex", "w") as fh:
        for kk, v in N.items():
            fh.write(f"\\newcommand{{\\{kk}}}{{{v if v is not None else chr(92) + 'todo{' + kk + '}'}}}\n")
