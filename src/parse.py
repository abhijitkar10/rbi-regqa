"""Directions markdown -> numbered paragraphs with character offsets.

Out: data/processed/docs.jsonl  {doc, entity, topic, title, text}
     data/processed/paras.jsonl {doc, para, heading, start, end, text}   (text == doc text[start:end])
Run: python src/parse.py
"""
import json, re
from pathlib import Path

CAT = {r["id"]: r for r in json.load(open("data/catalog/rbi_master_directions.json"))}
PARA = re.compile(r"^(\d+)\.(?:\s+|$|(?=[A-Z“\"'‘(\[]))(.*)")  # "1. x", "1.These", "4." alone
FOOTNOTE = re.compile(r"^\d+\s+(Substituted|Inserted|Deleted|Amended|Added|Omitted|Renumbered)\b", re.I)
END = re.compile(r"^- \[20\d\d\]\(")
HEAD = re.compile(r"^(Chapter [IVXLC]+\b.*|[A-Z]\.\s?[A-Z].{2,120}|Annex.*|Appendix.*|Schedule.*)$")
TITLE = re.compile(r"\((.+?)\s+[–-]\s+(.+)\)\s*(Directions|Guidelines)")


def clean(line):
    line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)          # images
    line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)      # links -> text
    line = line.replace("\\", "").strip().strip("|").strip()
    line = re.sub(r"\s*\|\s*", " | ", line)                   # table cells
    return "" if set(line) <= set("-| ") else line


def parse(md, doc):
    lines = md.splitlines()
    start = next((i + 1 for i, l in enumerate(lines) if "Previous Versions" in l), 0)
    body = []
    for l in lines[start:]:
        if END.match(l) or FOOTNOTE.match(l.strip()):
            break
        c = clean(l)
        if c:
            body.append(c)
    text, paras, cur, heading = "", [], None, ""
    for c in body:
        m = PARA.match(c)
        last = int(cur["para"]) if cur and cur["para"].isdigit() else 0
        if m and last < int(m.group(1)) <= last + 4:  # gaps: RBI deletes paragraphs ("[*****]")
            cur = {"doc": doc, "para": m.group(1), "heading": heading, "start": len(text)}
            paras.append(cur)
        elif HEAD.match(c) and len(c) < 140:
            heading = c
        if not paras:  # preamble before paragraph 1
            cur = {"doc": doc, "para": "preamble", "heading": "", "start": 0}
            paras.append(cur)
        text += c + "\n"
        cur["end"] = len(text)
    for p in paras:
        p["text"] = text[p["start"]:p["end"]]
    return text, paras


def main():
    out = Path("data/processed"); out.mkdir(parents=True, exist_ok=True)
    nd = np_ = 0
    with open(out / "docs.jsonl", "w") as fd, open(out / "paras.jsonl", "w") as fp:
        for f in sorted(Path("data/html").glob("*.md")):
            doc = int(f.stem)
            text, paras = parse(f.read_text(), doc)
            t = CAT[doc]["title"]
            m = TITLE.search(t)
            entity, topic = (m.group(1), m.group(2)) if m else ("", t)
            fd.write(json.dumps({"doc": doc, "entity": entity, "topic": topic, "title": t, "text": text}) + "\n")
            for p in paras:
                fp.write(json.dumps(p) + "\n")
            nd += 1; np_ += len(paras)
            if len(paras) < 3:
                print(f"WARN {doc}: only {len(paras)} paragraphs, {len(text)} chars  {t[:80]}")
    print(f"{nd} docs, {np_} paragraphs")


if __name__ == "__main__":
    # self-check: numbering must be sequential, offsets must slice back to the text
    t, ps = parse("Previous Versions\nIntro\nChapter I – X\n1\\. one\n(a) sub\n9\\. not a para\n2.Two\n4.\\\nfour\n", 1)
    assert [p["para"] for p in ps] == ["preamble", "1", "2", "4"], ps
    assert all(t[p["start"]:p["end"]] == p["text"] for p in ps)
    assert "9. not a para" in ps[1]["text"] and ps[1]["heading"] == "Chapter I – X"
    main()
