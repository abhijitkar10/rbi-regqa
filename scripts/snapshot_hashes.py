"""Per-paragraph fingerprints of our 21 Nov 2026 snapshot, so a re-fetched corpus can be checked against it.
The RBI text itself is not in the repo; scripts_fetch_html.sh + src/parse.py rebuild it from rbi.org.in.

python scripts/snapshot_hashes.py          write data/catalog/paragraph_hashes.tsv from data/processed/paras.jsonl
python scripts/snapshot_hashes.py --check  compare a rebuilt corpus with it; list changed paragraphs and affected questions"""
import hashlib, json, re, sys
from pathlib import Path

OUT = Path("data/catalog/paragraph_hashes.tsv")


def fp(text):  # whitespace-insensitive, so harmless reformatting by the fetcher does not count as a change
    return hashlib.sha256(re.sub(r"\s+", " ", text).strip().encode()).hexdigest()[:16]


now = {(str(p["doc"]), str(p["para"])): fp(p["text"]) for p in map(json.loads, open("data/processed/paras.jsonl"))}
if "--check" not in sys.argv:
    OUT.write_text("doc\tpara\tsha256_16\n" + "".join(f"{d}\t{p}\t{h}\n" for (d, p), h in now.items()))
    print(f"wrote {OUT} ({len(now)} paragraphs)")
    sys.exit()

ref = {tuple(l.split("\t")[:2]): l.split("\t")[2] for l in OUT.read_text().splitlines()[1:]}
changed = {k for k in ref if k in now and now[k] != ref[k]}
missing = {k for k in ref if k not in now}
qs = [q for f in ("v1", "expert_v1") for q in map(json.loads, open(f"data/benchmark/{f}.jsonl"))]
hit = [q["qid"] for q in qs if (str(q["doc"]), str(q["para"])) in changed | missing]
print(f"{len(ref)} paragraphs in the snapshot: {len(ref) - len(changed) - len(missing)} identical, {len(changed)} changed, {len(missing)} missing")
print(f"questions whose gold paragraph changed or is missing: {len(hit)}", *hit[:50], sep="\n  ")
sys.exit(1 if hit else 0)
