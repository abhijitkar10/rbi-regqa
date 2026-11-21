# Status

_Updated 2026-11-21 06:07 IST (Mac clock). **Paused**: laptop shut down for travel. Run `./resume.sh` to restart._

**Done:** 96 Directions parsed (8,065 paragraphs); three chunk sets; BGE-small/base and Qwen3-Embedding vectors; retrieval, answering, judging and verification scripts; near-copy analysis; paper draft (compiles); verified bibliography.

**Paused mid-way (all resumable):**
- Question drafting: Nemotron-3-Ultra 290/322 paragraphs, MiniMax-M3.1-Flash 253/322 (`./resume.sh`).
- BGE-M3 embeddings (restarted by `./resume.sh`).
- Customer-wording rewrites: 32 done with Nemotron-3.5-Super (lender type checked); rerun `src/rewrite_lay.py data/benchmark/v0.jsonl data/benchmark/unans_cand.jsonl data/benchmark/lay_cache.jsonl` after v0 is final.
- Early retrieval eval was stopped before writing results; rerun on the final set instead.

**Next, in order:** `src/build_benchmark.py` -> rewrites -> `src/verify_unanswerable.py data/benchmark/unans_cand.jsonl <verifier> 60` -> `src/finalize.py` -> `src/eval_retrieval.py` on v1, v1_customer, expert_v1 -> `src/answer.py` with 7 readers -> `src/judge.py` with two judges -> `analysis/summarize_answers.py` -> `analysis/make_numbers.py` -> paper results.

**Quotas to know:** Gemini free tier about 20 requests/model/day; Groq gpt-oss-120b 200K tokens/day; Mistral Medium rate-limited; SambaNova out of credit. NVIDIA (Nemotron, MiniMax) is the workhorse.

**Needs Abhijit (about 3 hours):** audit 100 random questions; anchor 17 expert questions by hand; check 30 unanswerable questions.
