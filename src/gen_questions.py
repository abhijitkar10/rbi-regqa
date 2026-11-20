"""Draft benchmark questions from single paragraphs with one generator model. Resumable.

python src/gen_questions.py MODEL SELECTION.jsonl OUT.jsonl
SELECTION lines: {doc, para}. OUT lines: {doc, para, generator, raw, questions, unanswerable, quote_ok:[...]}
"""
import json, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from llm import chat

SYSTEM = "You write questions for a research benchmark on Indian banking regulation. Reply with one JSON object and nothing else."
PROMPT = """Rulebook: {title}
Paragraph {para} (section: {heading})
<<<
{text}
>>>

Write up to 2 questions that a compliance officer at one of the lenders this rulebook covers ({entity}) might ask, each answerable from this paragraph alone.
- The question must make sense to someone who has not seen the paragraph: name the subject explicitly. Never say "this paragraph", "these Directions", "the above".
- Say which kind of lender you mean (e.g. "a small finance bank", "an NBFC") when the rule depends on it.
- Paraphrase as a real person would ask; do not copy the paragraph's wording.
- answer: one or two sentences.
- evidence: an exact, character-for-character quote from the paragraph (10 to 60 words) that proves the answer.
- type: one of definition, threshold (numbers, limits, time periods), obligation, permission, procedure, applicability.

Also write 1 unanswerable question: on this paragraph's topic, sounding like the rulebook should answer it, but asking for something this paragraph does not state (a number, deadline, case or condition that is absent).

Return: {{"questions": [{{"question": "...", "answer": "...", "evidence": "...", "type": "..."}}], "unanswerable": {{"question": "...", "why": "..."}}}}
If the paragraph is purely administrative (title, commencement, repeals, numbering), return {{"questions": [], "unanswerable": null}}."""


def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", re.sub(r"[^\w%'\"\-.,;:()/ ]", " ", s)).strip().lower()


def quote_ok(quote, text):
    return bool(quote) and norm(quote) in norm(text)


def parse_json(raw):
    m = re.search(r"\{.*\}", raw, re.S)
    return json.loads(m.group(0)) if m else None


def main(model, sel_path, out_path):
    docs = {d["doc"]: d for d in map(json.loads, open("data/processed/docs.jsonl"))}
    paras = {(p["doc"], p["para"]): p for p in map(json.loads, open("data/processed/paras.jsonl"))}
    done = {(r["doc"], r["para"]) for r in map(json.loads, open(out_path))} if Path(out_path).exists() else set()
    with open(out_path, "a") as out:
        for s in map(json.loads, open(sel_path)):
            key = (s["doc"], s["para"])
            if key in done:
                continue
            p, d = paras[key], docs[s["doc"]]
            prompt = PROMPT.format(title=d["title"], para=p["para"], heading=p["heading"] or "-",
                                   text=p["text"][:6000], entity=d["entity"] or "regulated entities")
            t = time.time()
            try:
                raw = chat(model, SYSTEM, prompt, max_tokens=3000, temperature=0.3)
                j = parse_json(raw) or {}
            except Exception as e:
                raw, j = f"ERROR {type(e).__name__}: {str(e)[:200]}", {}
            qs = j.get("questions") or []
            rec = {"doc": s["doc"], "para": s["para"], "generator": model, "secs": round(time.time() - t, 1),
                   "questions": qs, "unanswerable": j.get("unanswerable"),
                   "quote_ok": [quote_ok(q.get("evidence", ""), p["text"]) for q in qs], "raw": raw if not j else ""}
            out.write(json.dumps(rec) + "\n"); out.flush()
            print(f'{key} {rec["secs"]}s q={len(qs)} quotes_ok={sum(rec["quote_ok"])}/{len(qs)}', flush=True)


if __name__ == "__main__":
    assert quote_ok("the bank shall NOT reject", "The bank shall not  reject an application")
    assert not quote_ok("the bank may reject", "The bank shall not reject an application")
    main(*sys.argv[1:4])
