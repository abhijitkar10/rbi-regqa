"""arXiv submission metadata from the paper source, so it stays in sync with main.tex and numbers.tex.
Out: paper/arxiv_meta.txt (paste into the arXiv form). Fails if the abstract is over arXiv's 1,920-character limit
or still holds LaTeX. Usage: python scripts/arxiv_meta.py"""
import re, subprocess, sys

tex, num = open("paper/main.tex").read(), open("paper/numbers.tex").read()
macros = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{(.*)\}", num))


def plain(s):
    s = re.sub(r"\\(\w+)\{\}", lambda m: macros.get(m.group(1), m.group(0)), s)  # \Macro{} -> value
    s = re.sub(r"\\(?:emph|textbf|textit|url)\{([^}]*)\}", r"\1", s)
    s = s.replace("\\%", "%").replace("--", "–").replace("\\\\", " ").replace("~", " ").replace("\\ ", " ")
    return re.sub(r"\s+", " ", s).strip()


title = plain(re.search(r"\\title\{(.+?)\}\n", tex, re.S).group(1))
abstract = plain(re.search(r"\\begin\{abstract\}(.+?)\\end\{abstract\}", tex, re.S).group(1))
pages = re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", "paper/main.pdf"], capture_output=True, text=True).stdout).group(1)
tables, figs = len(re.findall(r"\\input\{tab_", tex)), tex.count("\\includegraphics")

problems = [p for p, bad in [(f"abstract is {len(abstract)} chars (> 1920)", len(abstract) > 1920),
                             ("LaTeX left in abstract", bool(re.search(r"[\\{}$]", abstract))),
                             ("LaTeX left in title", bool(re.search(r"[\\{}$]", title)))] if bad]
out = f"""Title: {title}
Authors: Abhijit Kar
Primary category: cs.CL    Cross-list: cs.IR
Comments: {pages} pages, {figs} figure, {tables} tables. Data and code: https://github.com/abhijitkar10/rbi-regqa
License: CC BY 4.0
MSC / ACM class: (leave blank)

Abstract ({len(abstract)} chars):
{abstract}
"""
open("paper/arxiv_meta.txt", "w").write(out)
print(out)
if problems:
    sys.exit("PROBLEMS: " + "; ".join(problems))
