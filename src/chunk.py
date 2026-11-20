"""Docs -> three chunk sets, each chunk mapped to the paragraph(s) it covers (for paragraph-level recall).

fixed      800-char windows, 200 overlap (the kyc-rag baseline)
para       one chunk per numbered paragraph; paragraphs over 1500 chars split at line breaks
para_title same as para, prefixed with the rulebook name ("Small Finance Banks - Know Your Customer, para 18")
Out: data/processed/chunks_<set>.jsonl {id, doc, paras, text}
"""
import json
from collections import defaultdict

docs = {d["doc"]: d for d in map(json.loads, open("data/processed/docs.jsonl"))}
paras = defaultdict(list)
for p in map(json.loads, open("data/processed/paras.jsonl")):
    paras[p["doc"]].append(p)


def fixed(size=800, overlap=200):
    for doc, d in docs.items():
        t = d["text"]
        for s in range(0, max(len(t) - overlap, 1), size - overlap):
            e = min(s + size, len(t))
            cover = [p["para"] for p in paras[doc] if p["start"] < e and p["end"] > s]
            yield {"doc": doc, "paras": cover, "text": t[s:e]}


def split(text, cap=1500):
    out, cur = [], ""
    for line in text.splitlines(keepends=True):
        if cur and len(cur) + len(line) > cap:
            out.append(cur); cur = ""
        while len(line) > cap:  # one huge line (tables): hard cut
            out.append(line[:cap]); line = line[cap:]
        cur += line
    return out + [cur] if cur.strip() else out


def para(title=False):
    for doc, ps in paras.items():
        d = docs[doc]
        name = f'{d["entity"]} - {d["topic"]}' if d["entity"] else d["title"]
        for p in ps:
            for piece in split(p["text"]):
                head = f'{name}, para {p["para"]}\n' if title else ""
                yield {"doc": doc, "paras": [p["para"]], "text": head + piece}


if __name__ == "__main__":
    assert [len(x) for x in split("a" * 1000 + "\n" + "b" * 1000 + "\n")] == [1001, 1001]
    for name, gen in [("fixed", fixed()), ("para", para()), ("para_title", para(True))]:
        n = 0
        with open(f"data/processed/chunks_{name}.jsonl", "w") as f:
            for i, c in enumerate(gen):
                f.write(json.dumps({"id": i, **c}) + "\n"); n += 1
        print(name, n, "chunks")
