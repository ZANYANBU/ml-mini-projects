#!/bin/bash
# Builds report/ML_Project_Report_Team_Cash_Guard.docx and .pdf with a contents page that has page numbers.
# Needs: node with the "docx" package (NODE_PATH), LibreOffice (soffice), poppler (pdftotext).
set -e
cd "$(dirname "$0")"
export PATH="/Applications/LibreOffice.app/Contents/MacOS:$PATH"
OUT=../ML_Project_Report_Team_Cash_Guard
node build_report.js                                    # pass 1: no page numbers yet
soffice --headless --convert-to pdf --outdir /tmp "$OUT.docx" >/dev/null 2>&1
python3 - <<'PY'
import json, subprocess
heads = json.load(open(".headings.json"))
pdf = "/tmp/ML_Project_Report_Team_Cash_Guard.pdf"
n = int([l for l in subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout.splitlines() if l.startswith("Pages")][0].split()[-1])
pages = [subprocess.run(["pdftotext", "-layout", "-f", str(i), "-l", str(i), pdf, "-"], capture_output=True, text=True).stdout for i in range(1, n + 1)]
FRONT = 2                                               # cover and bonafide carry no page number
found, start = {}, FRONT + 1                            # skip the contents pages themselves when searching
toc_pages = {i for i, t in enumerate(pages, 1) if "TABLE OF CONTENTS" in t}
for lvl, h in heads:
    for i in range(start, n + 1):
        if i in toc_pages:
            continue
        lines = [" ".join(l.split()) for l in pages[i - 1].splitlines()]
        joined = [lines[k] + ("" if lines[k].endswith("-") else " ") + lines[k + 1] for k in range(len(lines) - 1)]   # long titles wrap
        if h in lines or any(j.strip() == h for j in joined):
            found[h] = i - FRONT; start = i; break
missing = [h for _, h in heads if h not in found]
json.dump(found, open("/tmp/toc_pages.json", "w"))
print(f"{len(found)} of {len(heads)} headings placed" + (f"; not found: {missing}" if missing else ""))
PY
TOC_PAGES=/tmp/toc_pages.json node build_report.js       # pass 2: the same layout, with the numbers
zip -d "$OUT.docx" '*/' >/dev/null 2>&1 || true
soffice --headless --convert-to pdf --outdir .. "$OUT.docx" >/dev/null 2>&1
rm -f .headings.json
echo "done: $OUT.docx and $OUT.pdf"
