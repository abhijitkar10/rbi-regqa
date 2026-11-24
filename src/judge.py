"""Grade answers. python src/judge.py QUESTIONS.jsonl JUDGE_MODEL ANSWERS.jsonl [...] [--limit N]

Answerable:   LLM judge -> CORRECT / PARTIAL / WRONG against the reference answer + evidence;
              cite_gold: a cited passage is the gold paragraph (deterministic).
Unanswerable: correct iff the model said NOT FOUND (deterministic, no judge call).
Out: results/judged/<answers-stem>__<judge>.jsonl
"""
import json, random, re, sys

SOFT_REFUSAL = re.compile(r"\bnot found\b|(do|does) not (contain|specify|mention|provide|state|include|address)|no (information|mention|details?)|not (specified|mentioned|stated|provided|available) in the (provided )?passages|cannot be determined|unable to (find|determine)", re.I)
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
        rows = [r for r in map(json.loads, open(f)) if not r["answer"].startswith("ERROR")]
        if limit:  # agreement sample: first `limit` of the seed-0 shuffle of answers needing the LLM judge; shuffled
            # before dropping done rows so resumed runs keep the same picks (before 2026-11-24 they drifted on resume)
            rows = sorted((r for r in rows if qs[r["qid"]]["answerable"] and not r["refused"]), key=lambda r: r["qid"])
            random.Random(0).shuffle(rows)
            rows = [r for r in rows[:limit] if r["qid"] not in done][:max(0, limit - len(done))]
        else:
            rows = [r for r in rows if r["qid"] not in done]
        with open(out_path, "a") as out:
            for r in rows:
                q = qs[r["qid"]]
                cited = [chunks[r["ctx"][s - 1]] for s in r["cited"]]
                soft = r["refused"] or bool(SOFT_REFUSAL.search(r["answer"][:400])) or not r["answer"].strip()
                rec = {"qid": r["qid"], "model": r["model"], "judge": judge, "answerable": q["answerable"], "refused": r["refused"],
                       "refused_soft": soft, "empty": not r["answer"].strip()}
                if q["answerable"]:
                    if r["refused"]:
                        rec["grade"] = "WRONG"
                    else:
                        try:
                            g = chat(judge, SYSTEM, PROMPT.format(q=q["question"], ref=q["answer"], ev=q["evidence"], a=r["answer"]),
                                     max_tokens=2000).strip().upper()
                        except Exception as e:  # not written, so a rerun retries it
                            print(judge, r["qid"], "ERROR", type(e).__name__, flush=True); continue
                        rec["grade"] = next((w for w in ("PARTIAL", "CORRECT", "WRONG") if w in g), "WRONG")
                    rec["cite_gold"] = any(c["doc"] == q["doc"] and q["para"] in c["paras"] for c in cited)
                    rec["cited_any"] = bool(cited)
                else:  # strict: exact NOT FOUND; lenient: any clear "not in the passages"
                    rec["grade"] = "CORRECT" if r["refused"] else "WRONG"
                    rec["grade_soft"] = "CORRECT" if soft else "WRONG"
                out.write(json.dumps(rec) + "\n"); out.flush()


if __name__ == "__main__":
    args = sys.argv[1:]
    lim = int(args[args.index("--limit") + 1]) if "--limit" in args else None
    if "--limit" in args:
        i = args.index("--limit"); args = args[:i] + args[i + 2:]
    main(args[0], args[1], args[2:], lim)
