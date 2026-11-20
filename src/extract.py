"""PDF -> pages. One JSON line per page: {doc, section, page, text}. Run: python src/extract.py"""
import json
from pathlib import Path
from pypdf import PdfReader

cat = {r["id"]: r for r in json.load(open("data/catalog/rbi_master_directions.json"))}
out = Path("data/processed/pages.jsonl"); out.parent.mkdir(parents=True, exist_ok=True)
docs = []
with out.open("w") as f:
    for pdf in sorted(Path("data/raw").glob("*/*.pdf")):
        doc = int(pdf.stem)
        try:
            pages = PdfReader(pdf).pages
        except Exception as e:
            print("SKIP", pdf, e); continue
        chars = 0
        for i, p in enumerate(pages, 1):
            text = " ".join((p.extract_text() or "").split())
            chars += len(text)
            f.write(json.dumps({"doc": doc, "section": pdf.parent.name, "page": i, "text": text}) + "\n")
        docs.append({"doc": doc, "section": pdf.parent.name, "title": cat[doc]["title"], "date": cat[doc]["date"],
                     "pdf": cat[doc]["pdf"], "pages": len(pages), "chars": chars})
json.dump(docs, open("data/catalog/docs.json", "w"), indent=1)
print(f"{len(docs)} docs, {sum(d['pages'] for d in docs)} pages, {sum(d['chars'] for d in docs):,} chars")
