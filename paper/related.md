# Related work: verified references (add only after checking the source)

| Key | Reference | Checked | Why we cite it |
|---|---|---|---|
| gokhan2024rirag | Gokhan et al. 2024, "RIRAG: Regulatory Information Retrieval and Answer Generation", arXiv:2409.05677. ObliQA: 27,869 synthetic questions from 40 ADGM (Abu Dhabi) financial regulation documents, NLI-validated; metric RePASs. | arxiv.org/abs/2409.05677, 2026-11-21 | Closest prior work: synthetic regulatory QA with passage retrieval. We differ: Indian rules, near-copy rulebooks per lender type, unanswerable questions, human audit, generator-bias test. |
| rirag2025 | Shared Task RIRAG-2025, RegNLP workshop (ACL Anthology 2025.regnlp-1.1). Best R@10 about 0.63 on 446 hidden questions. | aclanthology.org/2025.regnlp-1.1.pdf, 2026-11-21 | Venue precedent (RegNLP); retrieval is hard on regulatory text. |
| jain2026bfsi | Udit Jain, "Indian Regulatory BFSI Benchmark v1", GitHub uditjainstjis/indian-regulatory-bfsi-benchmark and HF udit6969/indian-regulatory-bfsi-benchmark-v1, July 2026, CC-BY-SA-4.0. 60 extractive questions (30 RBI, 30 SEBI), context given, no retrieval. | checked earlier session | Only Indian prior resource; no retrieval, no KYC/AML. |
