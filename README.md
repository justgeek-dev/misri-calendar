# Misri Calendar

- `public/` is what gets published (index.html, _headers, misri.ics).
- To update the calendar: replace `public/misri.ics` on GitHub. Cloudflare redeploys automatically.
- `build_misri.py` + `miqaat.csv` rebuild the calendar offline (`python3 build_misri.py --out public/misri.ics`).
