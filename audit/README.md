# Hand audit (Abhijit)

Open each CSV in Numbers, Excel or Google Sheets, fill the CAPITALISED columns, save as CSV with the same name. About 3 hours in all.

| File | Rows | Fill in | What to judge |
|---|---|---|---|
| `questions_100.csv` | 100 random answerable questions | `FAIR_Y_N`, `ANSWER_CORRECT_Y_N` | Fair: a compliance officer could ask it and the paragraph answers it on its own. Correct: the reference answer matches the paragraph. |
| `unanswerable_30.csv` | 30 random unanswerable questions | `TRULY_UNANSWERABLE_Y_N`, `FAIR_Y_N` | Truly unanswerable: none of the five passages (or the rules as you know them) states the answer. Fair: a reasonable question on the topic, not a trick. |
| `expert_unanchored.csv` | your 9 questions that could not be matched automatically | `CORRECT_PARA`, `EVIDENCE_QUOTE` | The paragraph of the 2025 Commercial Banks KYC Directions that answers it (candidates are listed; type `none` if the rule no longer exists), and a short exact quote from it. |

The sample is fixed (seed 42): `python scripts/make_audit.py` regenerates the same rows.
