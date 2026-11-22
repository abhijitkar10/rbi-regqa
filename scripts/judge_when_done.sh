#!/usr/bin/env bash
# Start a Step-5 judge for each reader's answer file once that reader has stopped answering.
cd "$(dirname "$0")/.."
J=nvidia:stepfun-ai/step-5-preview
declare -A started
while true; do
  left=0
  for f in results/answers/v0__*.jsonl; do
    tag=$(basename "$f" .jsonl | sed 's/^v0__//')
    [ -n "${started[$tag]}" ] && continue
    model=$(head -1 "$f" | jq -r .model)
    if pgrep -f "src/[a]nswer.py data/benchmark/v0.jsonl.*$model" >/dev/null; then left=1; continue; fi
    pgrep -f "src/[j]udge.py.*$tag" >/dev/null || nohup .venv/bin/python src/judge.py data/benchmark/v0.jsonl $J "$f" > "logs/judge_$tag.log" 2>&1 &
    started[$tag]=1; echo "judge started: $tag ($(wc -l < "$f") answers)"
  done
  [ $left -eq 0 ] && break
  sleep 60
done
