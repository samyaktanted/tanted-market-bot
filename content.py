"""Turns a market Snapshot + tip into the Instagram caption. Commentary is
templated from real numbers — it never invents a 'reason' the market moved."""
from typing import Tuple

import config
from market_data import Snapshot

HASHTAGS = [
    "#stockmarket", "#nifty50", "#sensex", "#investing", "#indianstockmarket",
    "#sharemarket", "#nse", "#bse", "#stocks", "#financialfreedom",
    "#personalfinance", "#tantedinvestments", "#marketrecap", "#trading",
    "#wealth",
]


def _arrow(up: bool) -> str:
    return "\U0001F7E2" if up else "\U0001F534"  # green / red circle


def _index_line(snap: Snapshot) -> str:
    parts = []
    for q in snap.indices:
        parts.append(f"{_arrow(q.is_up)} {q.name}: {q.last:,.0f} ({q.change_pct:+.2f}%)")
    return "\n".join(parts)


def build_caption(snap: Snapshot, tip: Tuple[str, str]) -> str:
    tip_title, tip_body = tip
    nifty = snap.nifty
    if nifty is not None:
        mood = "closed higher" if nifty.is_up else "closed lower"
        headline = f"Markets {mood} today \U0001F4CA"
    else:
        headline = "Today's market recap \U0001F4CA"

    top_gain = snap.gainers[0] if snap.gainers else None
    top_lose = snap.losers[0] if snap.losers else None

    lines = [
        f"{headline}  |  {snap.date_ist}",
        "",
        _index_line(snap),
        "",
        f"Market breadth: {snap.advances} advancing / {snap.declines} declining (Nifty 50)",
    ]
    if top_gain:
        lines.append(f"Top gainer: {top_gain.name} ({top_gain.change_pct:+.2f}%)")
    if top_lose:
        lines.append(f"Top loser: {top_lose.name} ({top_lose.change_pct:+.2f}%)")

    lines += [
        "",
        f"\U0001F4A1 Tip of the day — {tip_title}: {tip_body}",
        "",
        f"Follow {config.BRAND_HANDLE} for a daily recap. More at {config.BRAND_WEBSITE}",
        "",
        config.DISCLAIMER,
        "",
        " ".join(HASHTAGS),
    ]
    return "\n".join(lines)
