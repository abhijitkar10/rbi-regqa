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
- [x] Second judge: gpt-oss-120b done (κ 0.61 vs Step-5, n=210, in the paper). Mistral Large 4 moved to the Third judge item below.
- [x] Retrieval breakdown by question type and by generator.
- [x] Figure 1: wrong-lender rate by chunking, for page 1.
- [x] Error analysis (2026-11-23, results/miss_analysis.json, Table 4): all 72 best-config misses (17 rulebook wording, 55 customer) tagged automatically and spot-read. With name prefixes only 6 are near-copy confusions; most are the right rulebook, wrong paragraph, usually a neighbour; single-paragraph gold labels undercount some correct hits (now in Limitations).
- [x] Claims-vs-numbers pass on the finished sections (2026-11-23): `make_numbers.py` regenerates numbers.tex and tables with no diff; the remaining literals (800/200/1,500 chunking, top-30 re-rank, 10,000 bootstrap resamples, 50 expert questions, Jaccard 0.9, ten-rulebook boilerplate, ±3 neighbour) match the code. Fixed one unsourced claim: "about 240 Directions" → 244 Directions replacing 9,445 circulars across 11 entity types, cited to the RBI press release.
- [x] Prose pass (no-ai-slop) on Introduction, Corpus and Retrieval sections; results sections wait for grading. Done 2026-11-23: six edits (active voice, defined WrongLender@1 as a share, reason for customer wording tied to the BM25 drop); the rest was already plain.
- [x] Dry-run the post-grading pipeline on the readers already fully graded (bolt, lightning, minimax, v0best ×2): run `analysis/summarize_answers.py`, draft the reader-table and refusal LaTeX generators and macros, so the final run is one command when gpt-oss/qwen/ministral finish. Done 2026-11-23: `analysis/reader_table.py` → paper/tab_readers.tex (Table 5, unfinished readers daggered), Ctx/Judge macros in make_numbers, wired into reproduce.sh. Found and fixed: v0 readers did NOT use the best retriever (gold in top 5: 85% vs 95% for v0best); Answering paragraph now says so. Early reads: MiniMax-drafted questions are harder for every reader (self-preference must be tested as a gap, not raw acc); Qwen refuses unanswerables 0.38 strict vs 0.90 lenient (hedges instead of NOT FOUND); best context lifts the two Nemotron readers by +0.03/+0.07; Step-5 vs gpt-oss-120b κ=0.61 (n=210).
- [x] Own-family check script (2026-11-23, `analysis/self_pref.py` → results/self_pref.json, macros \PrefNem/\PrefMM, in reproduce.sh): difference-in-differences of each reader's Nemotron-minus-MiniMax gap against the other-family readers, 10,000-resample bootstrap CI. On partial grades: Nemotron +0.046 [−0.004, +0.099], MiniMax −0.023 [−0.075, +0.027]; neither CI excludes zero yet.
- [x] Reader accuracy breakdown (2026-11-23, `analysis/reader_breakdown.py` → results/reader_breakdown.json, macros \Rd*, in reproduce.sh). Partial grades, mean over readers: gold in top-5 context 0.92 vs not 0.34 (48 questions); applicability 0.75 vs obligation 0.86 (same hardest type as retrieval); edited-copy paragraphs 0.93 vs main 0.83 (only 23 questions).
- [x] Failure appendix (2026-11-23, `analysis/failures.py` → results/failures.json + Appendix B table): wrong-lender answers, hedges, missed citations per reader, five examples each. Found and fixed a citation-parser bug: only the exact form [S1] was read, so [S1, S3], [S1(2)], [S1–S3] and 【S1】 counted as no citation. `src/answer.py` now uses `parse_cites`; `scripts/recite.py` recomputes stored citations without LLM calls (330 rows fixed; runs in reproduce.sh). Cite scores: Ministral-8B 0.69→0.86, Ministral-14B 0.68→0.87, gpt-oss-20b 0.76→0.87; all readers now 0.85–0.89. Qwen's 40 hedges dominate the unanswerable failures; wrong-lender answers are rare (1–5 per reader).
- [x] Reader Results drafted (2026-11-23): five paragraphs after Table 5 (accuracy/citations/gold-in-context, best-context ablation, strict vs lenient refusal, own-family check, judge agreement), every number a macro from make_numbers. After the final run, re-read: the prose names MiniMax-M3.1 as top reader and Qwen as the hedger, which macros do not check. Remaining TODOs: abstract headline (after grading), two audit TODOs (need Abhijit's audit CSVs).
- [x] Limitations, reader side: one LLM judge with κ 0.61 to a second; lenient refusal counts empty replies; v0 readers saw the weaker retriever's context; readers ran once at default sampling.
- [x] Conclusion paragraph (if none): three findings, one recommendation for RAG over versioned or per-entity rulebooks; keep within 8 pages.
- [x] Abstract headline draft now, macros only (\TitleWLRange, \BestRfive, \RdGoldIn/\RdGoldOut, expert R@1), replacing the abstract \todo; recheck wording after grading.
- [x] Related-work freshness: search 2025–26 papers on regulatory/legal RAG with near-duplicate or versioned documents; add at most two citations if they are close.
- [x] arXiv source package: `scripts/arxiv_pack.sh` → paper/arxiv.tar.gz (sources + generated .bbl, rebuilt from the tarball alone; warns on \todo). Rerun after the final reproduce.sh.
- [x] README: results so far (retrieval, final), reproduce section, analysis/results/paper in layout. Add reader headline after grading.
- [x] After grading (2026-11-24 04:40): all 7 readers × (v0 318 + unans 73) and v0best ×2 graded by Step-5; recite + reproduce.sh rerun. Final: acc 0.80–0.89 (MiniMax 0.89, Qwen 0.86, gpt-oss-20b 0.84), cite 0.84–0.89, false refusals 0.04–0.07, gold-in-context 0.93 vs 0.34, own-family Nemotron +0.039 [−0.005, +0.087], MiniMax −0.016 [−0.062, +0.028]. Prose names re-read: MiniMax top and Qwen the hedger still hold. Abstract and README updated; arXiv package rebuilt.
- [~] Third judge: Mistral Large 4 resumed 2026-11-24 on the same 30-per-reader v0 sample (slow, timeouts; logs/judge2_nvidia_mistralai_*). When 210 done: κ vs Step-5 and vs gpt-oss-120b; add one sentence to the judge paragraph if it changes the picture. Interim 2026-11-24 (n=108): κ 0.58 vs Step-5, exact agreement 0.86, in line with gpt-oss-120b's 0.61, so no change to the paper expected. Found a resume bug in src/judge.py --limit: done rows were dropped before the shuffle, so each restart drew a new sample and Mistral's picks overlapped gpt-oss-120b's on only 39 answers. Fixed (shuffle the full pool, take the first 30, skip done) and restarted; the remaining readers (MiniMax, Bolt, Lightning, Ministral-8B) now land on gpt-oss-120b's exact sample, giving ~95 answers graded by all three judges.
- [x] (2026-11-24) Claims-vs-numbers pass on the sections written after grading (reader results, Conclusion, Limitations, appendix): no hard-coded results; spelled-out counts (four embedders, two re-rankers, seven bank types) match Table 2. Fixed one overclaim: abstract and Conclusion gave the name-prefix WrongLender range 1.3–6.3% without its scope; prefixed BM25 is 8.2%. Both now say dense, hybrid and re-ranked (README too).
- [x] (2026-11-24) Fill the [bracketed] numbers in the private vault outreach files (professors.md hooks, interview pack, email template) from the final numbers.
- [x] Licensing (2026-11-22, Abhijit chose the fetch script): RBI text untracked (data/html/, audit CSVs); paragraph fingerprints in data/catalog/paragraph_hashes.tsv with `--check`; code MIT, annotations CC BY 4.0. Older commits still hold the text; removing it from history needs a force-push, which only Abhijit can approve.
- [x] `reproduce.sh` (paper stage from results; `full` also fetches, parses, embeds and ranks; LLM stages are not rerun).
- [x] arXiv readiness: `scripts/arxiv_package.sh` builds build/rbi-regqa-arxiv.tar.gz (44 KB, includes main.bbl) and proves it compiles from a clean folder (tectonic; TeX Live is not installed and needs Abhijit's password). `scripts/check_refs.py` verifies all 15 references (arXiv API, Crossref, URLs) and blocks on chatbot leftovers or TODO markers: arXiv's May 2026 rule bans authors for a year for unchecked AI output such as invented references. AI use is disclosed in the paper, as arXiv requires.
- [x] Outreach (2026-11-22, private vault, not in this repo): professor list refreshed from 2025-26 papers; 40 people in 4 batches, one hook line each. Bracketed numbers fill in after grading.
