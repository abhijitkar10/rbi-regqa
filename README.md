# RBI-RegQA

An open benchmark for question answering over the Reserve Bank of India's banking rules: find the right paragraph among about 100 rulebooks, answer with a citation, and refuse when the rules don't say.

**Status:** experiments and grading finished; draft paper in [paper/main.pdf](paper/main.pdf). Waiting on the author's hand audit, then the arXiv preprint (target 2026-12-20). See [STATUS.md](STATUS.md) for what is done and running, [PLAN.md](PLAN.md) for the paper plan, [CHANGELOG.md](CHANGELOG.md) for dated changes.

## Quick start

```bash
uv venv .venv --python 3.12 && uv pip install --python .venv/bin/python -r requirements.txt
./scripts_fetch_html.sh                        # Directions as markdown, via the Firecrawl CLI (free tier is enough)
.venv/bin/python src/parse.py                  # markdown -> numbered paragraphs
.venv/bin/python scripts/snapshot_hashes.py --check   # does your copy match our 21 Nov 2026 snapshot?
```

**The RBI text is not in this repo.** The RBI website reserves its rights, so we publish the questions, answers, paragraph numbers, short evidence quotes and code, and you fetch the Directions yourself. `data/catalog/paragraph_hashes.tsv` fingerprints every paragraph of our snapshot; the check lists any paragraph the RBI has amended since and the questions that depend on it. A fresh fetch on 22 Nov 2026 matched the snapshot exactly.

## Results

On 318 answerable questions over 96 Directions (8,065 paragraphs):

- With plain 800-character chunks, the best retriever's top result is the right rule from the wrong lender's rulebook for 14.2% of questions. Writing the rulebook's name into each paragraph chunk cuts this to 1.3–6.3% (dense, hybrid and re-ranked) and raises R@5 from 0.84 to 0.95.
- On the author's own questions, which rarely name a lender, R@1 is 0.37; defaulting to the deployment's lender raises it to 0.77.
- Seven open readers answering from the top 5 passages score 0.80–0.89 (MiniMax-M3.1 best); accuracy is 0.93 when the gold paragraph is in the context and 0.34 when it is not. Qwen3.8-27B refuses only 37% of unanswerable questions with the requested NOT FOUND, but 92% if its own-words declines count.

## Reproduce the paper

```bash
./reproduce.sh          # numbers, tables, figure and PDF from the committed results (needs data/processed/ and results/rankings/)
./reproduce.sh full     # also fetch, parse, chunk, embed and rank (hours on a laptop CPU)
scripts/arxiv_pack.sh   # arXiv source tarball (paper/arxiv.tar.gz)
```

LLM stages (drafting, answering, grading) are not rerun; their outputs are committed under `data/benchmark/` and `results/`.

## Layout

| Path | What |
|---|---|
| `data/catalog/` | every RBI Master Direction listed on rbi.org.in, with links |
| `data/html/` | the Directions' text as fetched (not in git; `./scripts_fetch_html.sh`) |
| `data/benchmark/` | the questions: `v1.jsonl` (answerable + unanswerable; `v0.jsonl` and `unans_v1.jsonl` are the answerable and unanswerable sets the paper evaluates), `v1_customer.jsonl` (plain-language), `expert_v1.jsonl` |
| `data/processed/` | paragraphs and chunks (not in git; regenerate with `src/parse.py`, `src/chunk.py`, `src/embed.py`) |
| `src/` | parsing, retrieval, question drafting, evaluation |
| `analysis/` | scripts that turn results into the paper's tables, figure and `paper/numbers.tex` |
| `results/` | rankings, reader answers and judge grades |
| `paper/` | LaTeX source; every number comes from `numbers.tex` or a generated table |

Builds on [kyc-rag](https://github.com/abhijitkar10/kyc-rag) (hand-written BM25, BGE dense search, RRF, BGE reranker).

## Cite

GitHub's "Cite this repository" button reads [CITATION.cff](CITATION.cff). Until the arXiv version is out, cite the repository.

## Licence

Code: MIT ([LICENSE](LICENSE)). Questions, answers and annotations: CC BY 4.0. The Directions are © Reserve Bank of India and are not redistributed here.
