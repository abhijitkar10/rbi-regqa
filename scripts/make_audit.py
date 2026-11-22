"""Audit sheets for the hand checks (CSV, open in Numbers/Excel/Sheets). Fixed seed, so reruns give the same sample.
python scripts/make_audit.py -> audit/questions_100.csv, audit/unanswerable_30.csv, audit/expert_unanchored.csv"""
import csv, json, random, sys
sys.path.insert(0, "src")
from retrieve import BM25, load_chunks

paras = {(str(p["doc"]), str(p["para"])): p["text"] for p in map(json.loads, open("data/processed/paras.jsonl"))}
docs = {str(d["doc"]): d["title"] for d in map(json.loads, open("data/processed/docs.jsonl"))}
v1 = [json.loads(l) for l in open("data/benchmark/v1.jsonl")]
rnd = random.Random(42)


def write(name, rows):
    with open(f"audit/{name}", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(name, len(rows))


ans = rnd.sample([q for q in v1 if q["answerable"]], 100)
write("questions_100.csv", [{"qid": q["qid"], "rulebook": docs[str(q["doc"])], "para": q["para"], "paragraph_text": paras[(str(q["doc"]), str(q["para"]))],
                             "question": q["question"], "reference_answer": q["answer"], "evidence_quote": q["evidence"], "type": q["type"],
                             "FAIR_Y_N": "", "ANSWER_CORRECT_Y_N": "", "notes": ""} for q in ans])

chunks = load_chunks("para_title"); ctx = json.load(open("results/contexts_unans_v1.json"))
un = rnd.sample([q for q in v1 if not q["answerable"]], 30)
write("unanswerable_30.csv", [{"qid": q["qid"], "rulebook": docs[str(q["doc"])], "source_para": q["para"], "source_paragraph_text": paras[(str(q["doc"]), str(q["para"]))],
                               "question": q["question"], "why_unanswerable": q.get("why", ""),
                               **{f"passage_{i + 1}": chunks[c]["text"][:1500] for i, c in enumerate(ctx[q["qid"]][:5])},
                               "TRULY_UNANSWERABLE_Y_N": "", "FAIR_Y_N": "", "notes": ""} for q in un])

kyc = [(k[1], t) for k, t in paras.items() if k[0] == "13141" and k[1] != "preamble"]
bm = BM25([t for _, t in kyc])
ex = [r for r in map(json.loads, open("data/benchmark/expert.jsonl")) if r["answerable"] and not r.get("quote_ok")]
write("expert_unanchored.csv", [{"qid": r["qid"], "question": r["question"], "your_answer": r["answer"], "old_ref (2025 Master Direction)": r.get("old_ref", ""),
                                 **{f"candidate_{i + 1}": f"para {kyc[j][0]}: {kyc[j][1][:400]}" for i, j in enumerate(bm.search(r["question"] + " " + r["answer"])[:5])},
                                 "CORRECT_PARA (number or none)": "", "EVIDENCE_QUOTE (copy from the para)": "", "notes": ""} for r in ex])
