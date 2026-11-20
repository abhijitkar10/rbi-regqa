# Changelog

## 2026-11-21

- Repo created. Paper plan in PLAN.md (decided in two planning rounds with Abhijit).
- Catalogued all 379 RBI Master Directions from rbi.org.in. RBI consolidated its rules in November 2025 into entity-wise Directions; the kyc-rag rulebook (KYC Master Direction, Aug 2025) is superseded for commercial banks by the Commercial Banks KYC Directions 2025 (updated 2026-10-01).
- The PDF host (rbidocs.rbi.org.in) returns a JavaScript bot check to scripts, so the text comes from each Direction's HTML page instead (fetched with Firecrawl). This keeps paragraph numbers, so citations are paragraph-level rather than page-level.
- Free LLM endpoints tested with a one-line prompt: Gemini 2.5/3.5 Flash, Groq gpt-oss-20b and Qwen3.8-27B, Ministral-8B, Nemotron Bolt work; Mistral Medium and GLM-5.3 were rate-limited; Cerebras needs payment. The FreeLLMAPI gateway is down because the Dell is offline.
