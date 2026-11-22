# Status

_Updated 2026-11-22 (Mac clock). Running: `scripts/finisher.sh` restarts answering and grading every 30 min until every reader is graded._

**Done:** corpus (96 Directions, 8,065 paragraphs); benchmark v1 (318 answerable + 73 unanswerable), customer wording (273), expert subset (35 of 44 anchored); retrieval on officer, customer and expert questions (results/retrieval_*.json, customer_gap.json, expert_any.json); paper sections up to retrieval results, near-copy table, prompts appendix.

**Running:** 7 readers answering v0 + unans_v1, plus the v0best ablation for the two Nemotron readers; Step-5 grading. Grading is the bottleneck. Groq readers (gpt-oss-20b, Qwen3.8-27B) wait for their daily caps; Ministral-14B runs after 8B. 

**Next, in order:** when grading finishes -> `analysis/summarize_answers.py v0,unans_v1 nvidia:stepfun-ai/step-5-preview` -> second judge on a sample for agreement -> reader table, refusals, ablation, self-preference in the paper -> abstract -> `analysis/make_numbers.py`.

**Restart after a shutdown:** `./resume.sh` (drafting and embeddings are finished; for answering and grading just run `scripts/finisher.sh`).

**Needs Abhijit (about 3 hours):** fill the three CSVs in `audit/` (instructions in audit/README.md): 100 random questions, 30 unanswerable, 9 unanchored expert questions.

## Timeline to the preprint

| By | Milestone |
|---|---|
| 29 Nov | grading done; reader table, refusals, ablation, self-preference, judge agreement, abstract; full draft v1 |
| 6 Dec | human audit numbers in; licensing decision applied; claims-vs-numbers review pass; prose edit |
| 15 Dec | arXiv source package builds from a clean folder; metadata written (scheduled check on 16 Dec) |
| 20 Dec | submitted to arXiv (cs.CL, cross-list cs.IR) |

## Backlog (worked top-down by the scheduled check-ins; tick when done)

- [x] Lender-aware retrieval (2026-11-22, results/lender_aware.json, Table 3): detect the lender type in the question and filter / boost / prefix; measure on officer, customer and expert questions.
- [x] Paired bootstrap 95 % CIs for the headline retrieval comparisons (name prefix vs none, officer vs customer, re-ranker gain).
- [x] Audit sheets in `audit/` (see audit/README.md) for Abhijit: 100 random questions, 30 unanswerable, 9 unanchored expert questions (CSV, fill in a spreadsheet).
- [~] Second judge: gpt-oss-120b and Mistral Large 4 running on 30 random answers per reader (logs/judge2_*.log); kappa via `analysis/summarize_answers.py v0,unans_v1 nvidia:stepfun-ai/step-5-preview <second judge>` once the samples finish.
- [x] Retrieval breakdown by question type and by generator.
- [x] Figure 1: wrong-lender rate by chunking, for page 1.
- [ ] After grading: reader table, refusals (strict/lenient), v0 vs v0best ablation, self-preference, abstract headline.
- [x] Licensing (2026-11-22, Abhijit chose the fetch script): RBI text untracked (data/html/, audit CSVs); paragraph fingerprints in data/catalog/paragraph_hashes.tsv with `--check`; code MIT, annotations CC BY 4.0. Older commits still hold the text; removing it from history needs a force-push, which only Abhijit can approve.
- [x] `reproduce.sh` (paper stage from results; `full` also fetches, parses, embeds and ranks; LLM stages are not rerun).
- [x] arXiv readiness: `scripts/arxiv_package.sh` builds build/rbi-regqa-arxiv.tar.gz (44 KB, includes main.bbl) and proves it compiles from a clean folder (tectonic; TeX Live is not installed and needs Abhijit's password). `scripts/check_refs.py` verifies all 15 references (arXiv API, Crossref, URLs) and blocks on chatbot leftovers or TODO markers: arXiv's May 2026 rule bans authors for a year for unchecked AI output such as invented references. AI use is disclosed in the paper, as arXiv requires.
- [x] Outreach (2026-11-22, private vault, not in this repo): professor list refreshed from 2025-26 papers; 40 people in 4 batches, one hook line each. Bracketed numbers fill in after grading.
