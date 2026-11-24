"""Hand-audit results. Reads the filled audit CSVs (audit/questions_100.csv, audit/unanswerable_30.csv: untracked, they
hold RBI text) and keeps only the verdicts (qid + the author's columns) in audit/verdicts_*.csv, which are committed, so
the numbers rebuild from a clean clone. A sheet counts only when every row is filled with Y or N.
Out: audit/verdicts_questions.csv, audit/verdicts_unanswerable.csv, results/audit.json"""
import csv, json
from pathlib import Path

SHEETS = {"questions": ("audit/questions_100.csv", ["FAIR_Y_N", "ANSWER_CORRECT_Y_N"]),
          "unanswerable": ("audit/unanswerable_30.csv", ["TRULY_UNANSWERABLE_Y_N", "FAIR_Y_N"])}
out = {}
for name, (src, cols) in SHEETS.items():
    keep = Path(f"audit/verdicts_{name}.csv")
    if Path(src).exists():
        rows = [{"qid": r["qid"], **{c: r[c].strip().upper()[:1] for c in cols}, "notes": r.get("notes", "").strip()}
                for r in csv.DictReader(open(src, encoding="utf-8-sig"))]
        if any(r[c] for r in rows for c in cols):  # write verdicts once the author has started
            with open(keep, "w", newline="") as f:
                w = csv.DictWriter(f, ["qid", *cols, "notes"]); w.writeheader(); w.writerows(rows)
    if not keep.exists():
        out[name] = None; continue
    rows = list(csv.DictReader(open(keep)))
    filled = all(r[c] in ("Y", "N") for r in rows for c in cols)
    out[name] = {"n": len(rows), "complete": filled, **{c: sum(r[c] == "Y" for r in rows) for c in cols},
                 "filled_rows": sum(all(r[c] in ("Y", "N") for c in cols) for r in rows)}
json.dump(out, open("results/audit.json", "w"), indent=1)
print(json.dumps(out, indent=1))

if __name__ == "__main__":  # self-check of the Y/N rule on a toy sheet
    assert "yes".strip().upper()[:1] == "Y" and " n ".strip().upper()[:1] == "N"
