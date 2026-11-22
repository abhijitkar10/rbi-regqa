# Status

_Updated 2026-11-22 (Mac clock). Running: `scripts/finisher.sh` restarts answering and grading every 30 min until every reader is graded._

**Done:** corpus (96 Directions, 8,065 paragraphs); benchmark v1 (318 answerable + 73 unanswerable), customer wording (273), expert subset (35 of 44 anchored); retrieval on officer and customer wording (results/retrieval_*.json, results/customer_gap.json); paper sections up to retrieval results, near-copy table, prompts appendix.

**Running:** 7 readers answering v0 + unans_v1, plus the v0best ablation for the two Nemotron readers; Step-5 grading. Grading is the bottleneck. Groq readers (gpt-oss-20b, Qwen3.8-27B) wait for their daily caps; Ministral-14B runs after 8B. Expert-subset retrieval eval queued.

**Next, in order:** when grading finishes -> `analysis/summarize_answers.py v0,unans_v1 nvidia:stepfun-ai/step-5-preview` -> second judge on a sample for agreement -> reader table, refusals, ablation, self-preference in the paper -> abstract -> `analysis/make_numbers.py`.

**Restart after a shutdown:** `./resume.sh` (drafting and embeddings are finished; for answering and grading just run `scripts/finisher.sh`).

**Needs Abhijit (about 3 hours):** audit 100 random questions; anchor the remaining 9 expert questions by hand; check 30 unanswerable questions.
