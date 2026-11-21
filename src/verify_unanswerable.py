"""Keep only unanswerable candidates that the corpus really doesn't answer.

python src/verify_unanswerable.py CANDIDATES.jsonl MODEL N_PER_GENERATOR
Samples N per generator (seed 0), retrieves the same top-5 context answer.py uses, asks MODEL whether any
passage answers the question. Out: data/benchmark/unans_verified.jsonl (verdict field; keep NOT_ANSWERED).
"""
import json, random, re, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from llm import chat
from answer import contexts

PROMPT = """Passages:
{ctx}

Question: {q}

Does any passage state the answer to this exact question (the specific number, deadline, condition or fact asked)?
Reply with one line: ANSWERED [S#] or NOT ANSWERED."""

if __name__ == "__main__":
    src, model, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    cands = [json.loads(l) for l in open(src)]
    by = defaultdict(list)
    for c in cands: by[c["generator"]].append(c)
    rng = random.Random(0)
    pick = [c for g in sorted(by) for c in rng.sample(by[g], min(n, len(by[g])))]
    ctx = contexts(src, pick)
    chunks = [json.loads(l) for l in open("data/processed/chunks_para_title.jsonl")]
    out_path = Path("data/benchmark/unans_verified.jsonl")
    done = {json.loads(l)["qid"] for l in open(out_path)} if out_path.exists() else set()
    with open(out_path, "a") as out:
        for c in pick:
            if c["qid"] in done: continue
            block = "\n\n".join(f"[S{j + 1}] {chunks[i]['text']}" for j, i in enumerate(ctx[c["qid"]]))
            v = chat(model, "You check whether passages answer a question. Reply with one line.", PROMPT.format(ctx=block, q=c["question"]), max_tokens=2000).strip().upper()
            c["verdict"] = "NOT_ANSWERED" if "NOT ANSWERED" in v else "ANSWERED"
            c["verifier"] = model
            out.write(json.dumps(c) + "\n"); out.flush()
    rows = [json.loads(l) for l in open(out_path)]
    print({g: f"{sum(r['verdict'] == 'NOT_ANSWERED' for r in rows if r['generator'] == g)}/{sum(r['generator'] == g for r in rows)} kept" for g in by})
