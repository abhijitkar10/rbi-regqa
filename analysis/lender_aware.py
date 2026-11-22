"""Lender-aware retrieval: detect the lender type named in the question and move that lender's rulebooks
to the front of the retrieved top 30 (stable). Variants: none / promote / promote + default to Commercial Banks
when no lender is named. Reads results/rankings/, writes results/lender_aware.json."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, "src")
from retrieve import load_chunks

docs = {d["doc"]: d for d in map(json.loads, open("data/processed/docs.jsonl"))}
def entity(d):  # 7 Directions have no entity field; take it from the title
    return docs[d]["entity"] or re.match(r"Reserve Bank of India \(([^–)]+)", docs[d]["title"]).group(1).strip()
ENT = {d: entity(d) for d in docs}

LENDERS = [(r"commercial bank|\bscbs?\b", "Commercial Banks"), (r"small finance bank|\bsfbs?\b", "Small Finance Banks"),
           (r"payments? bank", "Payments Banks"), (r"local area bank|\blabs?\b", "Local Area Banks"),
           (r"regional rural bank|\brrbs?\b", "Regional Rural Banks"), (r"urban co-?operative bank|\bucbs?\b", "Urban Co-operative Banks"),
           (r"rural co-?operative bank|state co-?operative bank|district central co-?operative|\bstcbs?\b|\bdccbs?\b", "Rural Co-operative Banks"),
           (r"\bnbfcs?\b|non-?banking financial compan", "Non-Banking Financial Companies"),
           (r"\baifis?\b|all[- ]india financial institution|\bexim bank\b|\bnabard\b|\bsidbi\b|\bnhb\b|\bnabfid\b", "All India Financial Institutions"),
           (r"\barcs?\b|asset reconstruction", "Asset Reconstruction Companies"), (r"housing finance compan|\bhfcs?\b", "Housing Finance Companies"),
           (r"core investment compan|\bcics?\b", "Core Investment Companies"), (r"primary dealer", "Standalone Primary Dealers"),
           (r"mortgage guarantee", "Mortgage Guarantee Companies"), (r"universal bank", "Universal Banks")]


def detect(q):
    t = q.lower().replace("‐", "-").replace("–", "-")
    return {e for p, e in LENDERS if re.search(p, t)}


def promote(rk, ch, want):
    return [i for i in rk if ENT[ch[i]["doc"]] in want] + [i for i in rk if ENT[ch[i]["doc"]] not in want] if want else rk


def score(qs, ranks, ch):
    m = dict.fromkeys(("R@1", "R@5", "R@30", "Book@1", "WrongLender@1"), 0)
    for q, rk in zip(qs, ranks):
        hit = [ch[i]["doc"] == q["doc"] and q["para"] in ch[i]["paras"] for i in rk]
        m["R@1"] += hit[0]; m["R@5"] += any(hit[:5]); m["R@30"] += any(hit)
        top = ch[rk[0]]["doc"]; m["Book@1"] += top == q["doc"]
        m["WrongLender@1"] += top != q["doc"] and docs[top]["topic"] == docs[q["doc"]]["topic"]
    return {k: round(v / len(qs), 3) for k, v in m.items()}


SETS = {"officer": "data/benchmark/v0.jsonl", "v1_customer": "data/benchmark/v1_customer.jsonl", "expert_v1": "data/benchmark/expert_v1.jsonl"}
out, chunks = {}, {}
for stem, qfile in SETS.items():
    qs = {q["qid"]: q for q in map(json.loads, open(qfile)) if q["answerable"]}
    det = {qid: detect(q["question"]) for qid, q in qs.items()}
    named = [qid for qid in qs if det[qid]]
    out[f"{stem}|detection"] = {"n": len(qs), "named": len(named),
                                "precision": round(sum(ENT[qs[q]["doc"]] in det[q] for q in named) / max(len(named), 1), 3)}
    for f in sorted(Path("results/rankings").glob(f"{stem}__*.json")):
        cs, name = f.stem.split("__")[1:3]
        if not (name.startswith("rerank_bge-reranker-v2-m3") or name.startswith("hybrid") or name == "bm25"): continue
        ch = chunks.setdefault(cs, load_chunks(cs)); r = json.load(open(f))
        q = [qs[x] for x in r["qids"]]
        for var, want in [("none", lambda x: set()), ("promote", lambda x: det[x]),
                          ("promote+CB", lambda x: det[x] or {"Commercial Banks"})]:
            out[f"{stem}|{cs}|{name}|{var}"] = score(q, [promote(rk, ch, want(x)) for x, rk in zip(r["qids"], r["ranks"])], ch)
json.dump(out, open("results/lender_aware.json", "w"), indent=1)
for k, v in out.items():
    if "detection" in k or "rerank" in k or "bm25" in k: print(f"{k:95} {v}")

# --- paper table: R@1 and WL@1 per question set, best re-ranked config per chunking, three variants ---
NAMES = {"fixed": "800-char windows", "para": "Paragraphs", "para_title": "Paragraphs + rulebook name"}
VAR = {"none": "as retrieved", "promote": "named lender first", "promote+CB": "+ default lender"}
lines = []
for cs in ("fixed", "para", "para_title"):
    lines.append(f"\\multicolumn{{7}}{{l}}{{\\textit{{{NAMES[cs]}}}}}\\\\")
    for v, label in VAR.items():
        cells = []
        for stem in SETS:
            k = next((k for k in out if k.startswith(f"{stem}|{cs}|rerank_bge-reranker-v2-m3") and k.endswith(f"|{v}")), None)
            cells += [f"{out[k]['R@1']:.2f}", f"{100 * out[k]['WrongLender@1']:.0f}"] if k else ["--", "--"]
        lines.append(f"\\quad {label} & " + " & ".join(cells) + "\\\\")
    lines.append("\\midrule")
open("paper/tab_lender.tex", "w").write(
    "\\begin{table}[t]\\centering\\small\\setlength{\\tabcolsep}{2.5pt}\n\\begin{tabular}{lcccccc}\\toprule\n"
    "& \\multicolumn{2}{c}{Rulebook} & \\multicolumn{2}{c}{Customer} & \\multicolumn{2}{c}{Expert}\\\\\n"
    "& R@1 & WL & R@1 & WL & R@1 & WL\\\\\\midrule\n" + "\n".join(lines[:-1]) +
    "\n\\bottomrule\\end{tabular}\n\\caption{Lender-aware re-ordering of the top 30 from hybrid retrieval + BGE-reranker-v2-m3. "
    "\\emph{Named lender first}: chunks from rulebooks of the lender type named in the question move to the front. "
    "\\emph{+ default lender}: questions that name no lender use the deployment's lender (here commercial banks). WL: WrongLender@1 in \\%.}"
    "\\label{tab:lender}\n\\end{table}\n")
