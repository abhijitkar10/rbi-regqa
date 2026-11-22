# RBI-RegQA

An open benchmark for question answering over the Reserve Bank of India's banking rules: find the right paragraph among about 100 rulebooks, answer with a citation, and refuse when the rules don't say.

**Status:** under construction; preprint target 2026-12-20. See [STATUS.md](STATUS.md) for what is done and running, [PLAN.md](PLAN.md) for the paper plan, [CHANGELOG.md](CHANGELOG.md) for dated changes.

## Quick start

```bash
uv venv .venv --python 3.12 && uv pip install --python .venv/bin/python -r requirements.txt
./scripts_fetch_html.sh                        # Directions as markdown, via the Firecrawl CLI (free tier is enough)
.venv/bin/python src/parse.py                  # markdown -> numbered paragraphs
.venv/bin/python scripts/snapshot_hashes.py --check   # does your copy match our 21 Nov 2026 snapshot?
```

**The RBI text is not in this repo.** The RBI website reserves its rights, so we publish the questions, answers, paragraph numbers, short evidence quotes and code, and you fetch the Directions yourself. `data/catalog/paragraph_hashes.tsv` fingerprints every paragraph of our snapshot; the check lists any paragraph the RBI has amended since and the questions that depend on it. A fresh fetch on 22 Nov 2026 matched the snapshot exactly.

## Layout

| Path | What |
|---|---|
| `data/catalog/` | every RBI Master Direction listed on rbi.org.in, with links |
| `data/html/` | the Directions' text as fetched (not in git; `./scripts_fetch_html.sh`) |
| `data/benchmark/` | the questions: `v1.jsonl` (answerable + unanswerable), `v1_customer.jsonl` (plain-language), `expert_v1.jsonl` |
| `data/processed/` | paragraphs and chunks (not in git; regenerate with `src/parse.py`, `src/chunk.py`, `src/embed.py`) |
| `src/` | parsing, retrieval, question drafting, evaluation |

Builds on [kyc-rag](https://github.com/abhijitkar10/kyc-rag) (hand-written BM25, BGE dense search, RRF, BGE reranker).

## Licence

Code: MIT ([LICENSE](LICENSE)). Questions, answers and annotations: CC BY 4.0. The Directions are © Reserve Bank of India and are not redistributed here.
