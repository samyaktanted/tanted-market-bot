"""Mutual-fund data for the informational 'Fund in Focus' posts.

Returns/NAV are computed LIVE from the free api.mfapi.in NAV history (real,
auto-updating). Holdings / AUM / expense ratio come from a dated snapshot below
(these change monthly — refresh periodically). Nothing here is a recommendation;
posts are framed as information only."""
from datetime import datetime, timedelta
from typing import Optional

import requests

# Featured funds. code = api.mfapi.in scheme code (Direct-Growth plan).
# holdings/aum/expense are a point-in-time snapshot ('as_of').
FUNDS = [
    {
        "code": 122639,
        "title_lines": ["Parag Parikh", "Flexi Cap"],
        "short": "Parag Parikh Flexi Cap",
        "aum": "~₹1.48 lakh Cr",
        "expense": "0.69% (direct)",
        "holdings": [("HDFC Bank", "7.6%"), ("Power Grid", "6.0%"),
                     ("ITC", "5.7%"), ("ICICI Bank", "5.6%"), ("Coal India", "4.9%")],
        "as_of": "Sep 2026",
    },
    {
        "code": 118778,
        "title_lines": ["Nippon India", "Small Cap"],
        "short": "Nippon India Small Cap",
        "aum": "~₹78,957 Cr",
        "expense": "0.69% (direct)",
        "holdings": [("HDFC Bank", "1.9%"), ("BHEL", "1.8%"),
                     ("Apar Industries", "1.5%"), ("Karur Vysya Bank", "1.4%"),
                     ("TD Power Systems", "1.4%")],
        "as_of": "Sep 2026",
    },
]


def _parse(d: str) -> datetime:
    return datetime.strptime(d, "%d-%m-%Y")


def get_fund_stats(code: int) -> Optional[dict]:
    """Live NAV + category + 1/3/5-yr CAGR from mfapi. None on failure."""
    try:
        j = requests.get(f"https://api.mfapi.in/mf/{code}", timeout=30).json()
        rows = [(_parse(x["date"]), float(x["nav"]))
                for x in j["data"] if x["nav"] not in ("", "0", "0.00000")]
        rows.sort(key=lambda t: t[0])            # oldest -> newest
        latest_dt, latest_nav = rows[-1]

        def cagr(n: int) -> Optional[float]:
            target = latest_dt - timedelta(days=int(365.25 * n))
            older = [nav for dt, nav in rows if dt <= target]
            if not older:
                return None
            return ((latest_nav / older[-1]) ** (1 / n) - 1) * 100

        cat = j["meta"]["scheme_category"].replace("Equity Scheme - ", "")
        return {
            "nav": latest_nav,
            "date": latest_dt.strftime("%d %b %Y"),
            "category": cat,
            "house": j["meta"]["fund_house"],
            "r1": cagr(1), "r3": cagr(3), "r5": cagr(5),
        }
    except Exception as exc:
        print(f"[warn] fund stats {code} failed: {exc}")
        return None
