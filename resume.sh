#!/bin/bash
# Restart every paused job; each one skips work already saved. Run from the repo root: ./resume.sh
cd "$(dirname "$0")"; mkdir -p logs
P=.venv/bin/python
for M in nvidia:nvidia/nemotron-3-ultra-550b-a55b nvidia:minimaxai/minimax-m3.1-flash; do
  n=$(echo $M | sed 's|.*/||; s/-.*//')
  for w in "" .rev .w1 .w2; do
    sel=data/questions/selection.jsonl; [ "$w" = .rev ] && sel=data/questions/selection_rev.jsonl
    [ "$w" = .w1 ] && sel=data/questions/selection_s1.jsonl; [ "$w" = .w2 ] && sel=data/questions/selection_s2.jsonl
    nohup $P src/gen_questions.py $M $sel data/questions/gen_$n$w.jsonl > logs/gen_$n$w.log 2>&1 &
  done
done
nohup $P src/embed.py para_title BAAI/bge-m3 > logs/embed2.log 2>&1 &
echo "drafting + BGE-M3 restarted; next: build_benchmark -> rewrite_lay -> verify_unanswerable -> finalize -> eval_retrieval -> answer -> judge"
