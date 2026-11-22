"""Pre-submission guard against what arXiv bans for (May 2026: one-year ban for unchecked AI output).
1) every arXiv reference exists and its title matches (arXiv API); other references by Crossref title search or URL;
2) no chatbot leftovers or TODO markers in the paper source. Exit 1 on any problem.
python scripts/check_refs.py"""
import json, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

bib = open("paper/references.bib").read()
entries = re.findall(r"@\w+\{([^,]+),\s*title=\{(.+?)\},\s*author=.*?\}\s*$", bib, re.M)
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower().replace("{", "").replace("}", ""))
UA = {"User-Agent": "rbi-regqa-refcheck/1.0"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()


bad = []
for key, title in entries:
    line = next(l for l in bib.splitlines() if l.startswith(f"@") and f"{{{key}," in l)
    if m := re.search(r"arXiv:(\d{4}\.\d{4,5})", line):
        x = ET.fromstring(get(f"https://export.arxiv.org/api/query?id_list={m.group(1)}"))
        got = x.find("{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}title")
        ok = got is not None and norm(got.text) == norm(title); time.sleep(3)  # arXiv API asks for 3 s between calls
    elif m := re.search(r"\\url\{([^}]+)\}", line):
        try: ok = urllib.request.urlopen(urllib.request.Request(m.group(1), headers=UA, method="HEAD"), timeout=30).status == 200
        except Exception: ok = False
    else:
        r = json.loads(get("https://api.crossref.org/works?rows=3&query.bibliographic=" + urllib.parse.quote(title)))
        ok = any(norm(t) == norm(title) for it in r["message"]["items"] for t in it.get("title", []))
    print(("ok  " if ok else "BAD ") + key)
    if not ok: bad.append(key)

src = "".join(open(f"paper/{f}").read() for f in ("main.tex", "numbers.tex", "app_prompts.tex"))
leftovers = [m.group(0) for m in re.finditer(r"(?i)as an ai\b|here is (a|the|your)\b|would you like me|i hope this helps|certainly!|\\todo\{[^}]*", src)]
print(f"chatbot/TODO leftovers: {len(leftovers)}", *leftovers, sep="\n  ")
sys.exit(1 if bad or leftovers else 0)
