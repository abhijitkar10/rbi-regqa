"""Embed a chunk set with one model. python src/embed.py SET MODEL [MODEL...]
Out: data/processed/emb/<set>__<model-short>.npy (normalised float16)."""
import json, sys
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

def short(m): return m.split("/")[-1]

if __name__ == "__main__":
    cset, models = sys.argv[1], sys.argv[2:]
    texts = [json.loads(l)["text"] for l in open(f"data/processed/chunks_{cset}.jsonl")]
    Path("data/processed/emb").mkdir(exist_ok=True)
    for m in models:
        out = Path(f"data/processed/emb/{cset}__{short(m)}.npy")
        if out.exists(): continue
        v = SentenceTransformer(m).encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
        np.save(out, v.astype(np.float16)); print(cset, m, v.shape, flush=True)
