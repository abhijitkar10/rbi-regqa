"""Grade answers. python src/judge.py QUESTIONS.jsonl JUDGE_MODEL ANSWERS.jsonl [...] [--limit N]

Answerable:   LLM judge -> CORRECT / PARTIAL / WRONG against the reference answer + evidence;
              cite_gold: a cited passage is the gold paragraph (deterministic).
Unanswerable: correct iff the model said NOT FOUND (deterministic, no judge call).
Out: results/judged/<answers-stem>__<judge>.jsonl
"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from llm import chat

SYSTEM = "You grade answers to questions about banking regulations. Reply with one word: CORRECT, PARTIAL or WRONG."
PROMPT = """Question: {q}
Reference answer: {ref}
Supporting rule text: "{ev}"

Answer to grade: {a}

CORRECT = states the reference answer's key facts with nothing that contradicts the rule.
PARTIAL = some key facts right, some missing, or vague.
WRONG = contradicts the reference, says the information is not available, or answers something else."""


def main(qfile, judge, files, limit=None):
    qs = {q["qid"]: q for q in map(json.loads, open(qfile))}
    chunks = [json.loads(l) for l in open("data/processed/chunks_para_title.jsonl")]
    Path("results/judged").mkdir(parents=True, exist_ok=True)
    for f in files:
        out_path = Path(f"results/judged/{Path(f).stem}__{judge.replace(':', '_').replace('/', '_')}.jsonl")
        done = {json.loads(l)["qid"] for l in open(out_path)} if out_path.exists() else set()
        rows = [r for r in map(json.loads, open(f)) if r["qid"] not in done and not r["answer"].startswith("ERROR")]
        with open(out_path, "a") as out:
            for r in rows[:limit]:
                q = qs[r["qid"]]
                cited = [chunks[r["ctx"][s - 1]] for s in r["cited"]]
                rec = {"qid": r["qid"], "model": r["model"], "judge": judge, "answerable": q["answerable"], "refused": r["refused"]}
                if q["answerable"]:
                    if r["refused"]:
                        rec["grade"] = "WRONG"
                    else:
                        g = chat(judge, SYSTEM, PROMPT.format(q=q["question"], ref=q["answer"], ev=q["evidence"], a=r["answer"]),
                                 max_tokens=2000).strip().upper()
                        rec["grade"] = next((w for w in ("PARTIAL", "CORRECT", "WRONG") if w in g), "WRONG")
                    rec["cite_gold"] = any(c["doc"] == q["doc"] and q["para"] in c["paras"] for c in cited)
                    rec["cited_any"] = bool(cited)
                else:
                    rec["grade"] = "CORRECT" if r["refused"] else "WRONG"
                out.write(json.dumps(rec) + "\n"); out.flush()


if __name__ == "__main__":
    args = sys.argv[1:]
    lim = int(args[args.index("--limit") + 1]) if "--limit" in args else None
    if "--limit" in args:
        i = args.index("--limit"); args = args[:i] + args[i + 2:]
    main(args[0], args[1], args[2:], lim)
