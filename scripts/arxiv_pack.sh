#!/bin/bash
# Build the arXiv source tarball: paper sources + the generated .bbl (arXiv does not run BibTeX).
# Out: paper/arxiv.tar.gz. Warns if \todo markers remain.
set -euo pipefail
cd "$(dirname "$0")/../paper"
t=$(mktemp -d)
cp main.tex numbers.tex app_prompts.tex tab_*.tex fig_*.pdf acl.sty "$t"/
tectonic --keep-intermediates -o "$t" main.tex >/dev/null 2>&1
rm -f "$t"/main.{pdf,aux,log,blg,out}
(cd "$t" && tectonic main.tex >/dev/null 2>&1 && rm -f main.{pdf,aux,log,out})  # check it builds from the tarball's files alone
tar -czf arxiv.tar.gz -C "$t" .
echo "paper/arxiv.tar.gz: $(tar -tzf arxiv.tar.gz | tr '\n' ' ')"
[ "$(grep -v newcommand main.tex | grep -c '\\todo{')" = 0 ] || echo "WARNING: $(grep -v newcommand main.tex | grep -c '\\todo{') \\todo markers remain"
rm -rf "$t"
