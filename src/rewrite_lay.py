"""Officer-style question -> how an ordinary customer would type it. Adds question_lay. Resumable.
python src/rewrite_lay.py IN.jsonl [IN2.jsonl ...] OUT.jsonl [provider:MODEL]"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from llm import chat

SYSTEM = "You rewrite questions. Reply with the rewritten question only."
PROMPT = """Rewrite this question the way an ordinary bank customer or small-business owner in India would type it into a chatbot.
Use everyday words. Drop regulatory jargon, defined terms and acronyms (say what they mean instead), but keep every fact needed so the correct answer stays exactly the same, including which kind of lender it is about if the question says so.

Question: {q}"""

LENDERS = [r"commercial bank", r"small finance bank", r"payments? bank", r"local area bank", r"regional rural bank",
           r"urban co ?operative bank", r"rural co ?operative bank", r"(nbfc|non banking financial)", r"(aifi|all india financial institution)",
           r"(arc|asset reconstruction)", r"(microfinance|nbfc mfi)", r"(peer to peer|p2p)", r"account aggregator"]


def lenders(text):
    t = re.sub(r"[-‐‑–]", " ", text.lower())
    return {p for p in LENDERS if re.search(p, t)}


def rewrite(model, q):
    lay = chat(model, SYSTEM, PROMPT.format(q=q), max_tokens=2000, temperature=0).strip().strip('"')
    missing = lenders(q) - lenders(lay)
    if missing:  # one retry with an explicit reminder
        lay = chat(model, SYSTEM, PROMPT.format(q=q) + "\nKeep the kind of lender named in the question (e.g. 'small finance bank', 'NBFC') in your rewrite.",
                   max_tokens=2000, temperature=0).strip().strip('"')
        missing = lenders(q) - lenders(lay)
    return lay, not missing


if __name__ == "__main__":
    assert lenders("Can a Small Finance Bank open...") == {r"small finance bank"}
    assert lenders("an NBFC-MFI must") >= {r"(nbfc|non banking financial)"}
    *srcs, dst = [a for a in sys.argv[1:] if ":" not in a]
    model = next((a for a in sys.argv[1:] if ":" in a), "nvidia:nvidia/nemotron-3.5-super-vl-120b-a12b")
    done = {json.loads(l)["qid"] for l in open(dst)} if Path(dst).exists() else set()
    with open(dst, "a") as out:
        for q in (json.loads(l) for src in srcs for l in open(src)):
            if q["qid"] in done: continue
            lay, kept = rewrite(model, q["question"])
            out.write(json.dumps({**q, "question_officer": q["question"], "question": lay, "rewriter": model, "lender_kept": kept}) + "\n"); out.flush()
