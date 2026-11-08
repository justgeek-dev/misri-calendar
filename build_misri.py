#!/usr/bin/env python3
"""Build misri.ics with no internet and no third party.

Dates : calculated here (Misri calendar, 30-year cycle).
Miqaat: read from miqaat.csv in the same folder (edit that file to add more).

Run:   python3 build_misri.py
       python3 build_misri.py --start 2026-01-01 --end 2032-12-31 --out misri.ics
Needs: Python 3.8+. Nothing else.
"""
import argparse, csv, os, zlib
from datetime import date, timedelta

MONTHS = ["Muharram", "Safar", "Rabi-ul-Awwal", "Rabi-ul-Aakhar", "Jamad-ul-Awwal",
          "Jamad-ul-Aakhar", "Rajab", "Shabaan", "Ramadan", "Shawwal", "Zilqada", "Zilhaj"]
LEAP = {2, 5, 8, 10, 13, 16, 19, 21, 24, 27, 29}
EPOCH = date(622, 7, 19).toordinal()
HERE = os.path.dirname(os.path.abspath(__file__))


def is_leap(y): return (y % 30) in LEAP
def year_len(y): return 355 if is_leap(y) else 354
def month_len(y, m):  # m is 0-based
    if m == 11: return 30 if is_leap(y) else 29
    return 30 if m % 2 == 0 else 29


def misri(d):
    """Gregorian date -> (year, month 1-12, day). Checked against published
    Bohra dates; the +1 day aligns the tabular epoch with them."""
    n = (d + timedelta(days=1)).toordinal() - EPOCH
    c = n // 10631
    y, n = 1 + 30 * c, n - c * 10631
    while n >= year_len(y):
        n -= year_len(y); y += 1
    m = 0
    while n >= month_len(y, m):
        n -= month_len(y, m); m += 1
    return y, m + 1, n + 1


def esc(s):
    return str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def vevent(uid, d, summary):
    return ["BEGIN:VEVENT", f"UID:{uid}", "DTSTAMP:20260101T000000Z",
            f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{esc(summary)}", "TRANSP:TRANSPARENT", "END:VEVENT"]


def load_miqaat(path):
    rows = []
    if not os.path.exists(path):
        print(f"No {path} found: building dates only."); return rows
    with open(path, newline="", encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
    for r in csv.DictReader(lines):
        try:
            m, d = int(r["month"]), int(r["day"])
            e = int(r["end_day"]) if (r.get("end_day") or "").strip() else d
            yr = int(r["year"]) if (r.get("year") or "").strip() else None
            assert 1 <= m <= 12 and 1 <= d <= e <= 30
            rows.append((m, d, e, r["name"].strip(), yr))
        except Exception:
            print("Skipped a bad line in miqaat.csv:", r)
    return rows


def build(start, end, out):
    miqaat = load_miqaat(os.path.join(HERE, "miqaat.csv"))
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Misri Calendar//EN", "CALSCALE:GREGORIAN",
         "METHOD:PUBLISH", "X-WR-CALNAME:Misri Calendar", "X-WR-CALDESC:Misri date every day plus miqaat",
         "REFRESH-INTERVAL;VALUE=DURATION:P1D", "X-PUBLISHED-TTL:P1D"]
    days = events = 0
    d = start
    while d <= end:
        y, m, dd = misri(d)
        L += vevent(f"misri-{d:%Y%m%d}@calendar.justgeek.dev", d, f"{dd} {MONTHS[m-1]} {y}")
        days += 1
        for (mm, a, b, name, yr) in miqaat:
            if mm == m and a <= dd <= b and (yr is None or yr == y):
                title = name if a == b else f"{name} - day {dd - a + 1} of {b - a + 1}"
                uid = f"miqaat-{d:%Y%m%d}-{zlib.crc32(name.encode()):08x}@calendar.justgeek.dev"
                L += vevent(uid, d, title); events += 1
        d += timedelta(days=1)
    L.append("END:VCALENDAR")
    with open(out, "w", newline="") as f:
        f.write("\r\n".join(L) + "\r\n")
    print(f"Wrote {out}: {days} days, {events} miqaat entries.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2026-01-01")
    p.add_argument("--end", default="2032-12-31")
    p.add_argument("--out", default="misri.ics")
    a = p.parse_args()
    build(date.fromisoformat(a.start), date.fromisoformat(a.end), a.out)
