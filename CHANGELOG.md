# Changelog

## 2026-11-22

- **Customer wording, paired on the same 273 questions** (analysis/customer_gap.py): the best retriever falls from R@5 0.96 to 0.80, BM25 on the same chunks from 0.78 to 0.42. The cross-encoder adds 0.07 R@5 over its hybrid input on rulebook wording but 0.18 on customer wording. The misses are not near-copy confusions (wrong-lender 1.5 %); the top result comes from a rulebook on another topic (right rulebook at rank 1: 80 % vs 91 %).
- Paper: near-copy table, corpus dates (59 of 96 Directions amended, 5 Dec 2025 to 19 Oct 2026; snapshot 21 Nov 2026) and the prompts appendix, all generated from files (analysis/paper_extras.py, make_numbers.py).
- Expert subset: 35 of 44 answerable questions now tied to a verified paragraph.
- Drafting finished: both generators covered all 322 paragraphs (errors retried once). Quote check pass: Nemotron 619/627, MiniMax 599/605; 20 Nemotron questions dropped for "this paragraph"-style references.
- **Benchmark v1:** 318 answerable questions (167 Nemotron, 151 MiniMax; 26 Directions) + 73 unanswerable. Unanswerable candidates were checked by two verifiers (Step-5 and gpt-oss-120b) over the top-5 retrieved passages; they agreed on 81/90 and 73 were kept (both said not answered).
- Plain-language paraphrases (Nemotron-3.5-Super): 273/318 kept the lender type and form v1_customer; they are plainer but still close to the rulebook's wording.
- **Retrieval, officer wording (318 questions):** best = paragraph chunks prefixed with the rulebook name + hybrid (BM25 + Qwen3-Embedding-0.6B) + BGE-reranker-v2-m3: R@1 0.77, R@5 0.95, right rulebook at rank 1 91 %, wrong lender's near-copy at rank 1 2.2 %. Without the name prefix the best is R@5 0.84 (fixed windows) with 14.2 % wrong-lender; plain paragraphs do slightly worse than overlapping windows (R@5 0.79). The name prefix is the single biggest win.
- Readers answer from a fixed earlier retriever (paragraph + name, hybrid BGE-base + BGE-reranker-base: R@5 0.85, wrong-lender 3.5 %). Ablation: the two Nemotron readers also answer from the best retriever's passages.
- Robustness: answer/judge/verify scripts skip failed calls so reruns retry them; scripts/finisher.sh restarts answering and judging every 30 min until done (free-tier daily caps). Groq gpt-oss-20b hit its daily cap after 141 answers.
- Refusals scored strictly (exact NOT FOUND) and leniently (any clear "not in the passages"); empty answers counted.

## 2026-11-21

- Repo created. Paper plan in PLAN.md (decided in two planning rounds with Abhijit).
- Catalogued all 379 RBI Master Directions from rbi.org.in. RBI consolidated its rules in November 2025 into entity-wise Directions; the kyc-rag rulebook (KYC Master Direction, Aug 2025) is superseded for commercial banks by the Commercial Banks KYC Directions 2025 (updated 2026-10-01).
- The PDF host (rbidocs.rbi.org.in) returns a JavaScript bot check to scripts, so the text comes from each Direction's HTML page instead (fetched with Firecrawl). This keeps paragraph numbers, so citations are paragraph-level rather than page-level.
- Parsed 98 Directions into 8,161 numbered paragraphs (handles "1.These", a number alone on a line, and deleted-paragraph gaps). Three technical Directions still parse coarsely (capital charge, NBFC ALM, NBFC financial statements); they stay as distractors and are not question sources.
- Chunk sets: fixed 800/200 windows (10,885), one per paragraph (10,254), and per paragraph with the rulebook name prefixed. Embedded with BGE-small and BGE-base; Qwen3-Embedding-0.6B and BGE-M3 added for the best chunk set.
- Question drafting, paired on the same 322 paragraphs (299 from 19 source rulebooks, 23 where another lender's KYC rule differs from the commercial-bank text). Only 23 paragraphs qualify because the nine lender-specific KYC rulebooks are near word-for-word copies.
- Generator changes, all measured not guessed: Gemini 3.5 Flash then Gemini 2.5 Flash ran out of free daily quota after about 25 paragraphs each (their drafts kept in data/questions/extra/); SambaNova out of credit; Mistral Medium rate-limited; Kimi K3.1 Pro 100-200 s per paragraph. Final pair: **Nemotron-3-Ultra** and **MiniMax-M3.1-Flash**, both 100 % exact-quote rate in the pilot.
- Early retrieval check on 52 questions: hybrid R@5 0.94; the BGE re-ranker raised R@1 but also picked the wrong lender's near-copy more often (10 % vs 4 %).
- Expert subset: kyc-rag's 50 hand-written questions re-anchored to the 2025 Commercial Banks KYC Directions ("Regulated Entity" -> "commercial bank"); quote verified by script, to be audited by hand.
- Quote check made tolerant of what models do when copying (ellipses, dropped list markers like "(iv)", different hyphen characters); every part of the quote must still appear in order. Recomputed for all drafts: Nemotron 99.6 %, MiniMax 99.1 %.
- Near-copy measurement (analysis/near_copies.py): 76-87 % of KYC paragraphs for the six other bank types are near-identical (word-trigram Jaccard >= 0.9) to the commercial-bank KYC Directions; NBFC, AIFI and ARC versions are mostly edited (68-77 % in 0.5-0.9).
- Closest prior work confirmed: RIRAG / ObliQA (Gokhan, Wang, Gurevych, Briscoe 2024; Abu Dhabi regulations). Bibliography entries checked against the arXiv API (paper/related.md).
- Paper draft started (paper/main.tex, ACL preprint style); every number comes from paper/numbers.tex, generated by analysis/make_numbers.py.
- Gemini free tier now allows only about 20 requests per model per day (3.5 Flash, 2.5 Flash, 3.1 Flash-Lite all hit it); Groq gpt-oss-120b hit its 200K tokens/day. Customer-wording rewrite moves to a non-Gemini model.
- Outreach material (professor list, email drafts, interview pack) kept out of this public repo.
- Free LLM endpoints tested with a one-line prompt: Gemini 2.5/3.5 Flash, Groq gpt-oss-20b and Qwen3.8-27B, Ministral-8B, Nemotron Bolt work; Mistral Medium and GLM-5.3 were rate-limited; Cerebras needs payment. The FreeLLMAPI gateway is down because the Dell is offline.
