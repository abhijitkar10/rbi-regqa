# RBI-RegQA

An open benchmark for question answering over the Reserve Bank of India's banking rules: find the right paragraph among about 100 rulebooks, answer with a citation, and refuse when the rules don't say.

**Status:** under construction; preprint target 2026-12-20. See [STATUS.md](STATUS.md) for what is done and running, [PLAN.md](PLAN.md) for the paper plan, [CHANGELOG.md](CHANGELOG.md) for dated changes.

## Quick start

```bash
uv venv .venv --python 3.12 && uv pip install --python .venv/bin/python -r requirements.txt
./scripts_fetch_html.sh          # Directions as markdown, via Firecrawl (needs FIRECRAWL_API_KEY)
.venv/bin/python src/parse.py    # markdown -> numbered paragraphs
```

## Layout

| Path | What |
|---|---|
| `data/catalog/` | every RBI Master Direction listed on rbi.org.in, with links |
| `data/html/` | the Directions' text as fetched (public RBI documents) |
| `data/processed/` | paragraphs and chunks (not in git; regenerate with `src/parse.py`, `src/chunk.py`, `src/embed.py`) |
| `src/` | parsing, retrieval, question drafting, evaluation |

Builds on [kyc-rag](https://github.com/abhijitkar10/kyc-rag) (hand-written BM25, BGE dense search, RRF, BGE reranker).
