"""Retrievers over one chunk set. Each returns, per question, a ranked list of chunk indices.

bm25        hand-written Okapi BM25 (ported from kyc-rag)
dense       cosine over precomputed embeddings (any model in data/processed/emb/)
hybrid      reciprocal rank fusion of bm25 + dense
rerank      cross-encoder re-scores the hybrid top-30
"""
import json, math, re
from collections import Counter, defaultdict
import numpy as np

_TOKEN = re.compile(r"[a-z0-9]+")
RRF_K, POOL = 60, 30
QUERY_PREFIX = {"bge-small-en-v1.5": "Represent this sentence for searching relevant passages: ",
                "bge-base-en-v1.5": "Represent this sentence for searching relevant passages: "}


def tokenize(t): return _TOKEN.findall(t.lower())


def load_chunks(cset): return [json.loads(l) for l in open(f"data/processed/chunks_{cset}.jsonl")]


class BM25:
    def __init__(self, texts, k1=1.5, b=0.75):
        toks = [tokenize(t) for t in texts]
        self.k1, self.b = k1, b
        self.dl = [len(t) for t in toks]; self.avgdl = sum(self.dl) / len(self.dl)
        self.post, df = defaultdict(list), Counter()
        for i, ts in enumerate(toks):
            for term, f in Counter(ts).items():
                self.post[term].append((i, f)); df[term] += 1
        n = len(toks)
        self.idf = {t: math.log((n - c + 0.5) / (c + 0.5) + 1) for t, c in df.items()}

    def search(self, q, k=100):
        s = defaultdict(float)
        for term in tokenize(q):
            for i, f in self.post.get(term, ()):
                s[i] += self.idf[term] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avgdl))
        return [i for i, _ in sorted(s.items(), key=lambda kv: -kv[1])[:k]]


class Dense:
    def __init__(self, cset, model):
        from sentence_transformers import SentenceTransformer
        self.short = model.split("/")[-1]
        self.vecs = np.load(f"data/processed/emb/{cset}__{self.short}.npy").astype(np.float32)
        self.model = SentenceTransformer(model)

    def search_many(self, qs, k=100):
        qv = self.model.encode([QUERY_PREFIX.get(self.short, "") + q for q in qs], normalize_embeddings=True, batch_size=64)
        sims = qv @ self.vecs.T
        return [list(np.argsort(-row)[:k]) for row in sims]


def rrf(*lists, k=100):
    s = defaultdict(float)
    for lst in lists:
        for r, i in enumerate(lst[:POOL]):
            s[i] += 1 / (RRF_K + r + 1)
    return [i for i, _ in sorted(s.items(), key=lambda kv: -kv[1])[:k]]


def rerank(ce, texts, q, cand, k=30):
    cand = cand[:k]
    scores = ce.predict([(q, texts[i]) for i in cand], batch_size=32)
    return [cand[j] for j in np.argsort(-scores)]


if __name__ == "__main__":
    b = BM25(["the cat sat", "dogs bark loudly", "the cat and the dog"])
    assert b.search("cat")[:2] == [0, 2] or b.search("cat")[:2] == [2, 0]
    assert rrf([1, 2], [2, 3])[0] == 2
    print("retrieve.py self-checks passed")
