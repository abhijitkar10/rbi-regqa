"""Paper pieces that come straight from files: near-copy table and the prompts appendix.
python analysis/paper_extras.py -> paper/tab_nearcopy.tex, paper/app_prompts.tex"""
import ast, json, re, unicodedata

rows = json.load(open("results/near_copies.json"))
SHORT = {"All India Financial Institutions": "All-India Fin.\\ Inst.\\ (AIFI)", "Non-Banking Financial Companies": "NBFCs",
         "Asset Reconstruction Companies": "Asset Reconstr.\\ Cos (ARC)", "Urban Co-operative Banks": "Urban Co-op Banks", "Rural Co-operative Banks": "Rural Co-op Banks"}
body = "\n".join(f"{SHORT.get(r['entity'], r['entity'])} & {r['paragraphs']} & {100 * r['identical_ge_0.9']:.0f} & {100 * r['edited_0.5_0.9']:.0f} & {100 * r['different_lt_0.5']:.0f}\\\\"
                 for r in rows)
open("paper/tab_nearcopy.tex", "w").write(
    "\\begin{table}[t]\\centering\\small\\setlength{\\tabcolsep}{3pt}\n\\begin{tabular}{lrrrr}\\toprule\n"
    "KYC Directions for & Paras & $\\geq$0.9 & 0.5--0.9 & $<$0.5\\\\\\midrule\n" + body +
    "\n\\bottomrule\\end{tabular}\n\\caption{Share (\\%) of each lender's KYC paragraphs by word-trigram Jaccard similarity to the closest "
    "paragraph of the Commercial Banks KYC Directions: near-identical, edited, different.}\\label{tab:nearcopy}\n\\end{table}\n")


def consts(path):
    out = {}
    for n in ast.parse(open(path).read()).body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            out[n.targets[0].id] = n.value.value
    return out


def shown(s):  # format string -> text the model sees, placeholders as <name>
    return re.sub(r"(?<!\{)\{(\w+)\}(?!\})", r"<\1>", s).replace("{{", "{").replace("}}", "}")


def ascii_(s):  # listings cannot break multi-byte characters
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", "-")
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


parts = []
for title, path, sys_ in [("Question drafting", "src/gen_questions.py", None), ("Customer rewrite", "src/rewrite_lay.py", None),
                          ("Answering", "src/answer.py", None), ("Grading", "src/judge.py", None),
                          ("Unanswerable check", "src/verify_unanswerable.py", "You check whether passages answer a question. Reply with one line.")]:
    c = consts(path)
    parts.append(f"\\noindent\\textbf{{{title}.}}\n\\begin{{lstlisting}}\nSYSTEM: {ascii_(sys_ or c['SYSTEM'])}\n\n{ascii_(shown(c['PROMPT']))}\n\\end{{lstlisting}}")
open("paper/app_prompts.tex", "w").write(
    "Text in angle brackets is filled per item. The rewriter's retry appends: "
    "``Keep the kind of lender named in the question (e.g.\\ `small finance bank', `NBFC') in your rewrite.''\n\n" + "\n\n".join(parts) + "\n")
print("ok", len(rows), "near-copy rows,", len(parts), "prompts")
