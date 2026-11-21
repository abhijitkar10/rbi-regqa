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
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[-‐‑‒–—―]", " ", s)                                    # every dash/hyphen -> space
    s = re.sub(r"\((?:[ivxlc]+|[a-z]|\d+[a-z]?)\)", " ", s, flags=re.I)  # list markers (iv) (a) (5)
    return re.sub(r"\s+", " ", re.sub(r"[^\w%'\".,;:()/ ]", " ", s)).strip().lower()


def quote_ok(quote, text):
    """Every piece of the quote (split at ellipses, pieces of 3+ words) appears in the text, in order."""
    t, pos = norm(text), 0
    segs = [x for x in (norm(q).strip(" .,;") for q in re.split(r"\.\.\.|…", quote or "")) if len(x.split()) >= 3]
    for seg in segs:
        i = t.find(seg, pos)
        if i < 0:
            return False
        pos = i + len(seg)
    return bool(segs)


def parse_json(raw):
    m = re.search(r"\{.*\}", raw, re.S)
    return json.loads(m.group(0)) if m else None


def main(model, sel_path, out_path):
    docs = {d["doc"]: d for d in map(json.loads, open("data/processed/docs.jsonl"))}
    paras = {(p["doc"], p["para"]): p for p in map(json.loads, open("data/processed/paras.jsonl"))}
    base = Path(out_path).name.split(".")[0]  # gen_x.jsonl, gen_x.rev.jsonl, gen_x.w2.jsonl share work

    def done():  # re-read every pass so parallel workers on the same generator skip each other's paragraphs
        return {(r["doc"], r["para"]) for f in Path(out_path).parent.glob(base + ".*jsonl") for r in map(json.loads, open(f))}
    with open(out_path, "a") as out:
        for s in map(json.loads, open(sel_path)):
            key = (s["doc"], s["para"])
            if key in done():
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
    assert quote_ok("a non account based customer, i.e., a walk in", "(5) a non-account-based customer, i.e., a walk‑in customer")
    assert quote_ok("from the senior management; the bank subjects all such accounts", "from the senior management; (iv) the bank subjects all such accounts")
    assert quote_ok("obtain the following from an individual ... the proof of possession", "obtain the following from an individual while opening: (1) the proof of possession")
    assert not quote_ok("the proof of possession ... obtain the following from", "obtain the following from an individual: the proof of possession")
    main(*sys.argv[1:4])
