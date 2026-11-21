"""Retrieval eval: every chunk set x retriever on a question file.

python src/eval_retrieval.py data/benchmark/v0.jsonl [sets] [rerankers]
Metrics (answerable questions only):
  R@k        a top-k chunk is from the gold rulebook and covers the gold paragraph
  MRR@10     reciprocal rank of the first such chunk
  Book@1     top-1 chunk is from the gold rulebook
  WrongLender@1  top-1 chunk is the same topic but another lender's rulebook (near-copy confusion)
Writes results/retrieval_<file>.json and the ranked lists to results/rankings/.
"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from retrieve import BM25, Dense, rrf, rerank, load_chunks

DENSE = ["BAAI/bge-small-en-v1.5", "BAAI/bge-base-en-v1.5", "BAAI/bge-m3", "Qwen/Qwen3-Embedding-0.6B"]
docs = {d["doc"]: d for d in map(json.loads, open("data/processed/docs.jsonl"))}


def metrics(qs, chunks, ranks):
    n = len(qs); m = {"R@1": 0, "R@5": 0, "R@10": 0, "MRR@10": 0, "Book@1": 0, "WrongLender@1": 0}
    for q, rk in zip(qs, ranks):
        hit = [chunks[i]["doc"] == q["doc"] and q["para"] in chunks[i]["paras"] for i in rk[:10]]
        first = hit.index(True) + 1 if True in hit else None
        for k in (1, 5, 10):
            m[f"R@{k}"] += bool(first and first <= k)
        m["MRR@10"] += 1 / first if first else 0
        top = chunks[rk[0]]["doc"]
        m["Book@1"] += top == q["doc"]
        m["WrongLender@1"] += top != q["doc"] and docs[top]["topic"] == docs[q["doc"]]["topic"]
    return {k: round(v / n, 3) for k, v in m.items()}


def main(qfile, sets=("fixed", "para", "para_title"), rerankers=("BAAI/bge-reranker-base", "BAAI/bge-reranker-v2-m3")):
    qs = [q for q in map(json.loads, open(qfile)) if q["answerable"]]
    texts_q = [q["question"] for q in qs]
    out, rows = Path("results"), []
    (out / "rankings").mkdir(parents=True, exist_ok=True)
    from sentence_transformers import CrossEncoder
    ces = {r: CrossEncoder(r) for r in rerankers}
    for cs in sets:
        chunks = load_chunks(cs); texts = [c["text"] for c in chunks]
        runs = {"bm25": [BM25(texts).search(q) for q in texts_q]}
        for m in DENSE:
            if Path(f"data/processed/emb/{cs}__{m.split('/')[-1]}.npy").exists():
                runs[f"dense:{m.split('/')[-1]}"] = Dense(cs, m).search_many(texts_q)
        dense_names = [k for k in runs if k.startswith("dense")]
        for d in dense_names:
            runs[f"hybrid:{d.split(':')[1]}"] = [rrf(a, b) for a, b in zip(runs["bm25"], runs[d])]
        hyb = [k for k in runs if k.startswith("hybrid")]
        best_h = max(hyb, key=lambda k: metrics(qs, chunks, runs[k])["MRR@10"]) if hyb else None
        for r, ce in ces.items():
            if best_h:
                t = time.time()
                runs[f"rerank:{r.split('/')[-1]}<{best_h}"] = [rerank(ce, texts, q, c) for q, c in zip(texts_q, runs[best_h])]
                print(f"  {cs} rerank {r} {time.time() - t:.0f}s", flush=True)
        for name, ranks in runs.items():
            row = {"chunks": cs, "retriever": name, "n": len(qs), **metrics(qs, chunks, ranks)}
            rows.append(row); print(json.dumps(row), flush=True)
            json.dump({"qids": [q["qid"] for q in qs], "ranks": [[int(i) for i in r[:30]] for r in ranks]},
                      open(out / "rankings" / f"{Path(qfile).stem}__{cs}__{name.replace(':', '_').replace('<', '_on_')}.json", "w"))
    json.dump(rows, open(out / f"retrieval_{Path(qfile).stem}.json", "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], *[a.split(",") for a in sys.argv[2:]])
