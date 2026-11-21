"""Answer questions from the top-5 retrieved passages, with [S#] citations or NOT FOUND. Resumable.

python src/answer.py QUESTIONS.jsonl MODEL [MODEL...]
Context: chunks_para_title + hybrid(BM25, bge-base) re-ranked by bge-reranker-base (cached per question file).
Out: results/answers/<qfile>__<model>.jsonl {qid, answer, cited, refused, ctx}
"""
import json, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from llm import chat

CSET, K = "para_title", 5
SYSTEM = "You answer questions about Reserve Bank of India banking regulations using only the passages given."
PROMPT = """Passages:
{ctx}

Question: {q}

Answer in one to three sentences using only the passages. Cite the passages you use like [S2]. If the passages do not contain the answer, reply exactly: NOT FOUND"""


def contexts(qfile, qs):
    cache = Path(f"results/contexts_{Path(qfile).stem}.json")
    have = json.load(open(cache)) if cache.exists() else {}
    todo = [q for q in qs if q["qid"] not in have]
    if todo:
        from retrieve import BM25, Dense, rrf, rerank, load_chunks
        from sentence_transformers import CrossEncoder
        chunks = load_chunks(CSET); texts = [c["text"] for c in chunks]
        bm, de, ce = BM25(texts), Dense(CSET, "BAAI/bge-base-en-v1.5"), CrossEncoder("BAAI/bge-reranker-base")
        dense = de.search_many([q["question"] for q in todo])
        for q, d in zip(todo, dense):
            have[q["qid"]] = [int(i) for i in rerank(ce, texts, q["question"], rrf(bm.search(q["question"]), d))[:K]]
        json.dump(have, open(cache, "w"))
    return have


def main(qfile, models):
    qs = [json.loads(l) for l in open(qfile)]
    ctx = contexts(qfile, qs)
    chunks = [json.loads(l) for l in open(f"data/processed/chunks_{CSET}.jsonl")]
    Path("results/answers").mkdir(parents=True, exist_ok=True)
    for model in models:
        out_path = Path(f"results/answers/{Path(qfile).stem}__{model.replace(':', '_').replace('/', '_')}.jsonl")
        done = {json.loads(l)["qid"] for l in open(out_path)} if out_path.exists() else set()
        with open(out_path, "a") as out:
            for q in qs:
                if q["qid"] in done: continue
                ids = ctx[q["qid"]]
                block = "\n\n".join(f"[S{j + 1}] {chunks[i]['text']}" for j, i in enumerate(ids))
                t = time.time()
                try:
                    a = chat(model, SYSTEM, PROMPT.format(ctx=block, q=q["question"]), max_tokens=3000).strip()
                except Exception as e:
                    a = f"ERROR {type(e).__name__}: {str(e)[:150]}"
                cited = sorted({int(n) for n in re.findall(r"\[S(\d)\]", a) if 1 <= int(n) <= K})
                out.write(json.dumps({"qid": q["qid"], "model": model, "answer": a, "cited": cited,
                                      "refused": a.upper().startswith("NOT FOUND"), "ctx": ids,
                                      "secs": round(time.time() - t, 1)}) + "\n"); out.flush()
        print(model, "done", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
