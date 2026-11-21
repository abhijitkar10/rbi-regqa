"""Officer-style question -> how an ordinary customer would type it. Adds question_lay. Resumable.
python src/rewrite_lay.py IN.jsonl OUT.jsonl [MODEL]"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from llm import chat

SYSTEM = "You rewrite questions. Reply with the rewritten question only."
PROMPT = """Rewrite this question the way an ordinary bank customer or small-business owner in India would type it into a chatbot.
Use everyday words. Drop regulatory jargon, defined terms and acronyms (say what they mean instead), but keep every fact needed so the correct answer stays exactly the same, including which kind of lender it is about if the question says so.

Question: {q}"""

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "gemini:gemini-3.1-flash-lite"
    done = {json.loads(l)["qid"] for l in open(dst)} if Path(dst).exists() else set()
    with open(dst, "a") as out:
        for q in map(json.loads, open(src)):
            if q["qid"] in done: continue
            lay = chat(model, SYSTEM, PROMPT.format(q=q["question"]), max_tokens=2000, temperature=0).strip().strip('"')
            out.write(json.dumps({**q, "question_officer": q["question"], "question": lay, "rewriter": model}) + "\n"); out.flush()
