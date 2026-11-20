# Paper plan: RBI-RegQA

**Purpose.** A preprint that wins a remote research internship by cold email. Everything is optimised for a professor skimming it in two minutes: one clear contribution, a public dataset, honest numbers, a clean repo.

**Deadline.** Preprint by 2026-12-20; emails from the first week of January 2027 (about 40 professors, 60 % India / 40 % abroad, 10 a week).

## The contribution

An open benchmark for **retrieval-augmented question answering over Indian banking regulation**, built on the RBI's November 2025 consolidated Directions.

What is new, against the closest prior work (Udit Jain's 60-question RBI/SEBI reading set, GitHub/HF, July 2026, no paper):

1. **Retrieval over the full rulebooks.** The system has to find the paragraph among about 100 Directions; nothing hands it the passage.
2. **Paragraph-level citations,** checked automatically against the source text.
3. **Unanswerable questions** that look answerable; the system should refuse.
4. **Near-duplicate rulebooks.** RBI issues almost the same KYC Directions separately for each type of lender (commercial banks, small finance banks, NBFCs, co-operative banks and others). A question about one lender type must be answered from that lender's rulebook. We measure how often retrieval picks the wrong near-copy.
5. **KYC, AML, lending and conduct coverage,** which the prior set lacks.

## Data

- Corpus: every Commercial Bank and NBFC Direction plus the KYC Directions for every lender type (98 documents), fetched from rbi.org.in as text with paragraph numbers.
- Questions: about 300, drafted by two different LLM families from paragraph text. Each carries a verbatim quote that a script checks against the source. Abhijit audits a random 100; the paper reports the audit error rate.
- Expert subset: the 50 hand-written questions from kyc-rag, re-anchored to the 2025 KYC Directions, reported separately.

## Experiments (build each option, measure, keep the winner)

| Choice | Options compared |
|---|---|
| Question drafting | Generator A (Gemini) vs Generator B (another family); also: does a model score higher on its own family's questions? |
| Chunking | fixed 800/200-character windows vs one chunk per numbered paragraph |
| Retrieval | BM25 (hand-written) · dense BGE-small · dense BGE-base · hybrid RRF · hybrid + BGE reranker |
| Answering | 4-5 small open models (gpt-oss-20b, Qwen3.8-27B, Ministral-8B, Nemotron Bolt and others) with the same top-5 context |
| Metrics | recall@k (paragraph level), wrong-rulebook rate, answer correctness (LLM judge + human sample), citation validity, refusal accuracy |

## Posting

arXiv (cs.CL or cs.IR) with an endorser: Abhijit's 8th-semester professor, offered co-authorship if they review it. Zenodo DOI and GitHub on day one regardless. A workshop (NLLP or FinNLP) later.

AI use is disclosed in the paper.
