# Changelog

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
- Free LLM endpoints tested with a one-line prompt: Gemini 2.5/3.5 Flash, Groq gpt-oss-20b and Qwen3.8-27B, Ministral-8B, Nemotron Bolt work; Mistral Medium and GLM-5.3 were rate-limited; Cerebras needs payment. The FreeLLMAPI gateway is down because the Dell is offline.
