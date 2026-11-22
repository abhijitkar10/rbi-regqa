# Status

_Updated 2026-11-22 (Mac clock). Running: `scripts/finisher.sh` restarts answering and grading every 30 min until every reader is graded._

**Done:** corpus (96 Directions, 8,065 paragraphs); benchmark v1 (318 answerable + 73 unanswerable), customer wording (273), expert subset (35 of 44 anchored); retrieval on officer, customer and expert questions (results/retrieval_*.json, customer_gap.json, expert_any.json); paper sections up to retrieval results, near-copy table, prompts appendix.

**Running:** 7 readers answering v0 + unans_v1, plus the v0best ablation for the two Nemotron readers; Step-5 grading. Grading is the bottleneck. Groq readers (gpt-oss-20b, Qwen3.8-27B) wait for their daily caps; Ministral-14B runs after 8B. 

**Next, in order:** when grading finishes -> `analysis/summarize_answers.py v0,unans_v1 nvidia:stepfun-ai/step-5-preview` -> second judge on a sample for agreement -> reader table, refusals, ablation, self-preference in the paper -> abstract -> `analysis/make_numbers.py`.

**Restart after a shutdown:** `./resume.sh` (drafting and embeddings are finished; for answering and grading just run `scripts/finisher.sh`).

**Needs Abhijit (about 3 hours):** fill the three CSVs in `audit/` (instructions in audit/README.md): 100 random questions, 30 unanswerable, 9 unanchored expert questions.

## Backlog (worked top-down by the scheduled check-ins; tick when done)

- [x] Lender-aware retrieval (2026-11-22, results/lender_aware.json, Table 3): detect the lender type in the question and filter / boost / prefix; measure on officer, customer and expert questions.
- [x] Paired bootstrap 95 % CIs for the headline retrieval comparisons (name prefix vs none, officer vs customer, re-ranker gain).
- [x] Audit sheets in `audit/` (see audit/README.md) for Abhijit: 100 random questions, 30 unanswerable, 9 unanchored expert questions (CSV, fill in a spreadsheet).
- [~] Second judge: gpt-oss-120b and Mistral Large 4 running on 30 random answers per reader (logs/judge2_*.log); kappa via `analysis/summarize_answers.py v0,unans_v1 nvidia:stepfun-ai/step-5-preview <second judge>` once the samples finish.
- [x] Retrieval breakdown by question type and by generator.
- [x] Figure 1: wrong-lender rate by chunking, for page 1.
- [ ] After grading: reader table, refusals (strict/lenient), v0 vs v0best ablation, self-preference, abstract headline.
- [~] CITATION.cff done. RBI's site says "All Rights Reserved" and prohibits caching/framing without permission; the repo commits the Directions' full text. **Decision for Abhijit:** keep the text, or ship paragraph IDs + a fetch script instead (and/or ask RBI). Dataset card waits on this.
- [ ] `reproduce.sh`: results -> numbers -> tables -> PDF in one command.
- [ ] arXiv readiness: compile with pdflatex (TeX Live), check arXiv's policy on AI-written text, size limits.
- [ ] Outreach (private vault): refresh professor list, one tailored hook line per professor.
