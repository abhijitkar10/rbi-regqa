#!/bin/bash
# Fetch each Direction's HTML page (rbi.org.in serves the full text there) as markdown via Firecrawl.
# The PDF host (rbidocs) answers scripts with a JavaScript bot check, so we use the HTML page instead.
cd "$(dirname "$0")"; mkdir -p data/html
cut -f2 data/catalog/download_list.tsv | while read -r id; do
  out="data/html/$id.md"; [ -s "$out" ] && continue
  for try in 1 2 3; do firecrawl scrape "https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=$id" --only-main-content -o "$out.part" >/dev/null 2>&1 && break; sleep 15; done \
    && mv "$out.part" "$out" || echo "FAIL $id"
done
echo "done: $(ls data/html/*.md | wc -l) files"
