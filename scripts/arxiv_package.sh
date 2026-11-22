#!/usr/bin/env bash
# Build the arXiv source package: build/arxiv/ + build/rbi-regqa-arxiv.tar.gz, then prove it compiles from that folder alone.
# arXiv does not reliably run BibTeX, so the generated main.bbl goes in the package.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf build/arxiv && mkdir -p build/arxiv
(cd paper && tectonic -X compile --keep-intermediates main.tex >/dev/null 2>&1)
inputs=$(grep -oE '\\input\{[^}]+\}' paper/main.tex | sed -E 's/\\input\{(.*)\}/\1/')
figs=$(grep -oE '\\includegraphics(\[[^]]*\])?\{[^}]+\}' paper/main.tex | sed -E 's/.*\{(.*)\}/\1/')
cp paper/main.tex paper/main.bbl paper/references.bib paper/acl.sty paper/acl_natbib.bst build/arxiv/
for f in $inputs; do cp "paper/${f%.tex}.tex" build/arxiv/; done
for f in $figs; do cp "paper/$f" build/arxiv/; done
rm -f paper/main.aux paper/main.log paper/main.blg paper/main.out paper/main.bbl
# compile a throwaway copy, so the packaged main.bbl stays exactly as generated
rm -rf build/arxiv_test && cp -r build/arxiv build/arxiv_test
(cd build/arxiv_test && tectonic -X compile main.tex 2>&1 | grep -iE "error|undefined|missing" || echo "package compiles: $(ls *.pdf)")
ls build/arxiv
grep -c 'todo{' build/arxiv/*.tex | grep -v ':0' || echo "no TODO macros left"
(cd build && rm -f arxiv/main.pdf && tar czf rbi-regqa-arxiv.tar.gz -C arxiv . && du -h rbi-regqa-arxiv.tar.gz)
.venv/bin/python scripts/check_refs.py || echo "NOT READY: fix the items above before submitting"
