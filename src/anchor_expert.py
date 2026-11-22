"""Re-anchor kyc-rag's 50 hand-written questions (old KYC Master Direction) to the Commercial Banks KYC
Directions 2025 (doc 13141). BM25 shortlist over that doc, an LLM picks the paragraph and an exact quote,
the quote is verified by script. Out: data/benchmark/expert.jsonl  (audit by hand before use)."""
import csv, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from llm import chat
from retrieve import BM25
from gen_questions import quote_ok, parse_json

DOC = 13141
MODEL = sys.argv[1] if len(sys.argv) > 1 else "nvidia:stepfun-ai/step-5-preview"
SRC = Path.home() / "Documents/life/kyc-rag/eval/questions.csv"
RE_SUB = [(r"\bRegulated Entit(y|ies)\b", "commercial bank"), (r"\bREs\b", "commercial banks"), (r"\b(an|An) RE\b", r"\1 commercial bank"), (r"\bRE\b", "commercial bank")]
PROMPT = """Question: {q}
Expected answer (written for an older version of the rules): {a}

Candidate paragraphs from the Commercial Banks KYC Directions 2025:
{cands}

Which single paragraph best supports the expected answer? Reply with JSON:
{{"para": "<paragraph number or NONE>", "evidence": "<exact quote from that paragraph, 10-60 words, copied character for character>", "changed": "<one sentence on whether the 2025 rule differs from the expected answer, or 'no'>"}}"""

paras = [p for p in map(json.loads, open("data/processed/paras.jsonl")) if p["doc"] == DOC]
# candidates are <=1500-char paragraph pieces, so long paragraphs (definitions) aren't cut off
pieces = [c for c in map(json.loads, open("data/processed/chunks_para.jsonl")) if c["doc"] == DOC]
bm = BM25([c["text"] for c in pieces])
prev = {r["qid"]: r for r in map(json.loads, open("data/benchmark/expert.jsonl"))} if Path("data/benchmark/expert.jsonl").exists() else {}
out = []
for r in csv.DictReader(open(SRC)):
    if prev.get(f"expert-{r['id']}", {}).get("quote_ok") or prev.get(f"expert-{r['id']}", {}).get("answerable") is False:
        out.append(prev[f"expert-{r['id']}"]); continue
    q = r["question"]
    for pat, rep in RE_SUB:
        q = re.sub(pat, rep, q)
    rec = {"qid": f"expert-{r['id']}", "doc": DOC, "set": "expert", "generator": "human", "category": r["category"],
           "question": q, "question_original": r["question"], "answer": r["answer_in_own_words"],
           "old_ref": r["clause_ref"], "answerable": r["answerable"] == "yes"}
    if rec["answerable"]:
        top = [pieces[i] for i in bm.search(q + " " + r["answer_in_own_words"], k=8)]
        cands = "\n\n".join(f"[para {c['paras'][0]}] {c['text']}" for c in top)
        try:
            j = parse_json(chat(MODEL, "Reply with one JSON object only.", PROMPT.format(q=q, a=r["answer_in_own_words"], cands=cands), max_tokens=4000)) or {}
        except Exception as e:  # keep the earlier attempt; a rerun tries again
            print(rec["qid"], "ERROR", type(e).__name__, flush=True)
            out.append(prev.get(rec["qid"], rec)); continue
        p = next((p for p in paras if p["para"] == str(j.get("para"))), None)
        rec.update(para=j.get("para"), evidence=j.get("evidence"), changed=j.get("changed"), anchored_by=MODEL,
                   quote_ok=bool(p) and quote_ok(j.get("evidence", ""), p["text"]))
    out.append(rec)
    print(rec["qid"], rec.get("para"), rec.get("quote_ok"), (rec.get("changed") or "")[:80], flush=True)
    done_ids = {o["qid"] for o in out}  # save after every question: finished ones + untouched earlier ones
    with open("data/benchmark/expert.jsonl", "w") as f:
        for o in out + [v for k, v in prev.items() if k not in done_ids]:
            f.write(json.dumps(o) + "\n")
ok = [r for r in out if r["answerable"]]
print(f"anchored {sum(r['quote_ok'] for r in ok)}/{len(ok)} answerable; {len(out) - len(ok)} unanswerable kept for re-check")
