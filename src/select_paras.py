"""Choose the paragraphs questions are drafted from. Deterministic (seed 0).

Main set: up to 16 paragraphs from each source rulebook.
Entity set: paragraphs of other lenders' KYC Directions that differ from the Commercial Banks KYC
            text (word-3-gram Jaccard to the closest CB paragraph between 0.2 and 0.8): rules where
            the lender type changes the answer.
Out: data/questions/selection.jsonl {doc, para, set}
"""
import json, random, re
from collections import defaultdict

SOURCES = [13141, 13140, 13139, 13155, 13157, 13156, 13163, 13144, 13154, 13161, 13149,   # commercial banks
           12943, 12957, 12942, 13590, 12933, 12934, 12936, 12955]                         # NBFCs
CB_KYC, OTHER_KYC = 13141, [12927, 12943, 12969, 12988, 13014, 13040, 13064, 13090, 13109]
ADMIN = re.compile(r"shall be called|come into (force|effect)|hereby repeal|stand repealed", re.I)

paras = defaultdict(list)
for p in map(json.loads, open("data/processed/paras.jsonl")):
    if p["para"] != "preamble" and 200 <= len(p["text"]) <= 8000 and not ADMIN.search(p["text"][:300]):
        paras[p["doc"]].append(p)


def grams(t):
    w = re.findall(r"[a-z0-9]+", t.lower())
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


rng = random.Random(0)
sel = []
for d in SOURCES:
    for p in rng.sample(paras[d], min(16, len(paras[d]))):
        sel.append({"doc": d, "para": p["para"], "set": "main"})
cb = [grams(p["text"]) for p in paras[CB_KYC]]
for d in OTHER_KYC:
    cands = []
    for p in paras[d]:
        g = grams(p["text"])
        best = max((len(g & c) / len(g | c) for c in cb if g | c), default=0)
        if 0.2 <= best <= 0.8:
            cands.append(p)
    for p in rng.sample(cands, min(5, len(cands))):
        if not any(s["doc"] == d and s["para"] == p["para"] for s in sel):
            sel.append({"doc": d, "para": p["para"], "set": "entity"})
with open("data/questions/selection.jsonl", "w") as f:
    for s in sel:
        f.write(json.dumps(s) + "\n")
print(len(sel), "paragraphs:", sum(s["set"] == "main" for s in sel), "main,", sum(s["set"] == "entity" for s in sel), "entity")
print({d: len(paras[d]) for d in SOURCES + OTHER_KYC})
