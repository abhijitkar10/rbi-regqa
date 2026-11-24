#!/usr/bin/env bash
# Rebuild the paper's numbers, tables, figure and PDF from the results in this repo.
#   ./reproduce.sh        paper stage only: needs data/processed/ and results/rankings/ (both local, not in git)
#   ./reproduce.sh full   also rebuilds those: fetch the RBI text, parse, chunk, embed, rank (hours on a laptop CPU)
# LLM stages (question drafting, rewriting, answering, grading) are NOT rerun: their outputs are committed
# under data/ and results/, and rerunning them costs API quota and gives different samples.
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python

if [ "${1:-}" = full ]; then
  ./scripts_fetch_html.sh
  $PY src/parse.py
  $PY scripts/snapshot_hashes.py --check || echo "WARNING: some paragraphs differ from the 21 Nov 2026 snapshot (listed above)"
  $PY src/chunk.py
  for s in fixed para; do $PY src/embed.py $s BAAI/bge-small-en-v1.5 BAAI/bge-base-en-v1.5; done
  $PY src/embed.py para_title BAAI/bge-small-en-v1.5 BAAI/bge-base-en-v1.5 BAAI/bge-m3 Qwen/Qwen3-Embedding-0.6B
  for q in officer v1_customer expert_v1; do $PY src/eval_retrieval.py data/benchmark/$q.jsonl; done
fi

[ -d results/rankings ] && [ -f data/processed/paras.jsonl ] || { echo "missing data/processed or results/rankings: run ./reproduce.sh full"; exit 1; }
for s in near_copies retrieval_table customer_gap expert_any lender_aware bootstrap breakdown miss_analysis fig_wronglender paper_extras; do
  echo "== analysis/$s.py"; $PY analysis/$s.py > /dev/null
done
$PY scripts/recite.py > /dev/null
$PY analysis/summarize_answers.py v0,unans_v1 nvidia:stepfun-ai/step-5-preview groq:openai/gpt-oss-120b > /dev/null
$PY analysis/summarize_answers.py v0best nvidia:stepfun-ai/step-5-preview > /dev/null
$PY analysis/reader_table.py > /dev/null
$PY analysis/self_pref.py > /dev/null
$PY analysis/reader_breakdown.py > /dev/null
$PY analysis/failures.py > /dev/null
$PY analysis/judge_agreement.py > /dev/null
$PY analysis/audit.py > /dev/null
$PY analysis/make_numbers.py > /dev/null
(cd paper && tectonic -X compile main.tex 2>&1 | grep -iE "error|undefined|overfull" || true)
$PY scripts/arxiv_meta.py > /dev/null || echo "arxiv_meta.py: abstract problem, see paper/arxiv_meta.txt"
echo "paper/main.pdf rebuilt; TODOs left: $(grep -o 'todo{[^}]*' paper/main.tex paper/numbers.tex | wc -l | tr -d ' ')"
