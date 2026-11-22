#!/usr/bin/env bash
# Every 30 min: restart answering for any reader with missing answers, and judging for any reader with
# ungraded answers, unless already running. Exits when every reader has all answers and all grades.
# Handles free-tier daily caps: a capped run stops after 5 failures; the next pass resumes it.
cd "$(dirname "$0")/.."
J=nvidia:stepfun-ai/step-5-preview
READERS="groq:openai/gpt-oss-20b groq:qwen/qwen3.8-27b mistral:ministral-8b-latest mistral:ministral-14b-latest nvidia:nvidia/nemotron-3.5-bolt-e4b nvidia:nvidia/nemotron-3.5-lightning-30b-a3b nvidia:minimaxai/minimax-m3.1-flash"
lines() { [ -f "$1" ] && wc -l < "$1" | tr -d ' ' || echo 0; }
while true; do
  todo=0
  for m in $READERS; do
    tag=$(echo "$m" | tr ':/' '__')
    for stem in v0 unans_v1; do
      want=$(lines data/benchmark/$stem.jsonl); have=$(lines results/answers/${stem}__$tag.jsonl)
      if [ "$have" -lt "$want" ]; then
        todo=1
        pgrep -f "src/[a]nswer.py data/benchmark/$stem.jsonl.*$m" >/dev/null || \
          { nohup .venv/bin/python src/answer.py data/benchmark/$stem.jsonl $m >> logs/finisher_answer_$tag.log 2>&1 & echo "$(date +%H:%M) answer $stem $m ($have/$want)"; }
      fi
      ans=results/answers/${stem}__$tag.jsonl; jd=results/judged/${stem}__${tag}__$(echo $J | tr ':/' '__').jsonl
      if [ -f "$ans" ] && [ "$(lines $jd)" -lt "$(jq -s 'map(select(.answer|startswith("ERROR")|not))|length' $ans)" ]; then
        todo=1
        pgrep -f "src/[j]udge.py data/benchmark/$stem.jsonl.*$tag" >/dev/null || \
          { nohup .venv/bin/python src/judge.py data/benchmark/$stem.jsonl $J $ans >> logs/finisher_judge_$tag.log 2>&1 & echo "$(date +%H:%M) judge $stem $m"; }
      fi
    done
  done
  [ $todo -eq 0 ] && { echo "$(date +%H:%M) all answers graded"; break; }
  sleep 1800
done
