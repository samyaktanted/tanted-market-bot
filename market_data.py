"""Fetches real Indian market data via yfinance. Nothing here is invented:
every number in the post comes from these feeds."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

IST = ZoneInfo("Asia/Kolkata")

# Headline indices (Yahoo Finance symbols).
INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK",
}

# Universe used to compute top gainers/losers and market breadth.
# Nifty 50 constituents (Yahoo tickers use the .NS suffix for NSE).
NIFTY50 = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BEL.NS", "BHARTIARTL.NS",
    "CIPLA.NS", "COALINDIA.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS",
    "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS",
    "HINDUNILVR.NS", "ICICIBANK.NS", "INDUSINDBK.NS", "INFY.NS", "ITC.NS",
    "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS", "M&M.NS", "MARUTI.NS",
    "NESTLEIND.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS",
    "SBILIFE.NS", "SBIN.NS", "SHRIRAMFIN.NS", "SUNPHARMA.NS", "TCS.NS",
    "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS",
    "TRENT.NS", "ULTRACEMCO.NS", "WIPRO.NS",
]


@dataclass
class Quote:
    name: str
    last: float
    change_pct: float

    @property
    def is_up(self) -> bool:
        return self.change_pct >= 0


@dataclass
class Snapshot:
    date_ist: str
    indices: List[Quote] = field(default_factory=list)
    gainers: List[Quote] = field(default_factory=list)
    losers: List[Quote] = field(default_factory=list)
    advances: int = 0
    declines: int = 0

    @property
    def nifty(self) -> Optional[Quote]:
        for q in self.indices:
            if q.name == "NIFTY 50":
                return q
        return None


def _pct_change_from_history(df: pd.DataFrame) -> Optional[Quote]:
    """Return last close and % change vs the prior close from a small history df."""
    closes = df["Close"].dropna()
    if len(closes) < 2:
        return None
    last = float(closes.iloc[-1])
    prev = float(closes.iloc[-2])
    if prev == 0:
        return None
    return Quote(name="", last=last, change_pct=(last - prev) / prev * 100.0)


def _clean_name(ticker: str) -> str:
    return ticker.replace(".NS", "").replace("&", "&")


def get_snapshot() -> Snapshot:
    now = datetime.now(IST)
    snap = Snapshot(date_ist=now.strftime("%d %b %Y"))

    # Indices: pull 5 days so we always have a prior close even after holidays.
    for name, sym in INDICES.items():
        try:
            hist = yf.Ticker(sym).history(period="5d")
            q = _pct_change_from_history(hist)
            if q:
                q.name = name
                snap.indices.append(q)
        except Exception as exc:  # keep going even if one index fails
            print(f"[warn] index {name} ({sym}) failed: {exc}")

    # Universe movers: one batched download is far faster than per-ticker calls.
    quotes: List[Quote] = []
    try:
        data = yf.download(
            NIFTY50, period="5d", group_by="ticker",
            auto_adjust=False, progress=False, threads=True,
        )
        for tkr in NIFTY50:
            try:
                df = data[tkr] if tkr in data.columns.get_level_values(0) else None
                if df is None:
                    continue
                q = _pct_change_from_history(df)
                if q:
                    q.name = _clean_name(tkr)
                    quotes.append(q)
            except Exception:
                continue
    except Exception as exc:
        print(f"[warn] batch download failed: {exc}")

    quotes.sort(key=lambda q: q.change_pct, reverse=True)
    snap.gainers = quotes[:5]
    snap.losers = list(reversed(quotes[-5:])) if len(quotes) >= 5 else []
    snap.advances = sum(1 for q in quotes if q.change_pct > 0)
    snap.declines = sum(1 for q in quotes if q.change_pct < 0)
    return snap


if __name__ == "__main__":
    s = get_snapshot()
    print(s.date_ist)
    for q in s.indices:
        print(f"  {q.name}: {q.last:,.2f} ({q.change_pct:+.2f}%)")
    print("Gainers:", [(q.name, round(q.change_pct, 2)) for q in s.gainers])
    print("Losers:", [(q.name, round(q.change_pct, 2)) for q in s.losers])
    print("Breadth:", s.advances, "up /", s.declines, "down")
