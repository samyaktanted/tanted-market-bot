"""Registry of post types. Each builder returns (images, caption).

Add a new post type by writing a build_* function and registering it in
POST_TYPES. The daily/extra workflows pick a type by name or by weekday."""
from datetime import date
from typing import Callable, Dict, List, Tuple

from PIL import Image

import config
import content
import library
import market_data
import news
import premium
import render

HASHTAGS = " ".join(content.HASHTAGS)


def _footer_caption(extra_tags: str = "") -> str:
    tags = HASHTAGS + (" " + extra_tags if extra_tags else "")
    return (f"\nFollow {config.BRAND_HANDLE} for daily market content. "
            f"More at {config.BRAND_WEBSITE}\n\n{config.DISCLAIMER}\n\n{tags}")


# --- Daily recap (the anchor post) ---------------------------------------
def build_recap() -> Tuple[List[Image.Image], str]:
    import tips
    snap = market_data.get_snapshot()
    tip = tips.tip_for_today()
    return render.build_recap_slides(snap, tip), content.build_caption(snap, tip)


# --- Global cues (pre-market / morning) ----------------------------------
def build_global() -> Tuple[List[Image.Image], str]:
    date_str = market_data.today_ist()
    cues = market_data.get_quotes(market_data.GLOBAL_CUES)
    extras = market_data.get_quotes(market_data.COMMODITIES_FX)

    slides = [
        render.title_slide("Good morning", ["GLOBAL", "CUES"], date_str),
    ]
    if cues:
        slides.append(render.quotes_slide("Overnight global markets", cues))
    if extras:
        slides.append(render.quotes_slide("Commodities, FX & crypto", extras))
    slides.append(render.outro_slide())

    lines = [f"Global cues \U0001F30F  |  {date_str}", ""]
    for q in cues:
        arrow = "\U0001F7E2" if q.is_up else "\U0001F534"
        lines.append(f"{arrow} {q.name}: {q.change_pct:+.2f}%")
    caption = "\n".join(lines) + _footer_caption("#premarket #globalmarkets")
    return slides, caption


# --- News roundup ---------------------------------------------------------
def build_news() -> Tuple[List[Image.Image], str]:
    date_str = market_data.today_ist()
    heads = news.get_headlines(limit=5)
    slides = [render.title_slide("Today in markets", ["MARKET", "NEWS"], date_str)]
    if heads:
        bullets = [h.title for h in heads]
        tags = [f"— {h.source}" for h in heads]
        slides.append(render.bullets_slide("Top headlines", bullets, tags=tags))
    slides.append(render.outro_slide())

    cap_lines = [f"Today's market headlines \U0001F4F0  |  {date_str}", ""]
    for h in heads:
        cap_lines.append(f"• {h.title} — {h.source}")
    cap_lines.append("\n(Headlines aggregated from public sources; tap through to "
                     "each outlet for the full story.)")
    caption = "\n".join(cap_lines) + _footer_caption("#marketnews #businessnews")
    return slides, caption


# --- Quiz (with reveal) ---------------------------------------------------
def build_quiz() -> Tuple[List[Image.Image], str]:
    q = library.quiz_for_today()
    opts = q["options"]
    letters = ["A", "B", "C", "D"]
    opt_lines = [f"{letters[i]}.  {opt}" for i, opt in enumerate(opts)]
    ans_letter = letters[q["answer"]]

    slides = [
        render.title_slide("Market quiz", ["QUIZ", "TIME"], "Swipe & test yourself"),
        render.text_slide("Question", q["q"], "Comment your answer before you swipe!",
                          body_size=44),
        render.bullets_slide("Pick one", opt_lines),
        render.text_slide("Answer",
                          f"{ans_letter}. {opts[q['answer']]}", q["why"],
                          body_size=42),
        render.outro_slide(),
    ]
    caption = (f"\U0001F9E0 Market quiz!\n\n{q['q']}\n\n"
               + "\n".join(opt_lines)
               + "\n\nComment your guess \U0001F447 (answer on the last slide)"
               + _footer_caption("#financequiz #investingbasics"))
    return slides, caption


# --- Jargon buster / term of the day -------------------------------------
def build_term() -> Tuple[List[Image.Image], str]:
    t = library.term_for_today()
    slides = [
        render.title_slide("Jargon buster", ["TERM OF", "THE DAY"], t["term"]),
        render.text_slide(t["term"], "What it means", t["def"], body_size=48),
        render.text_slide("Example", t["term"], t["eg"], body_size=44),
        render.outro_slide(),
    ]
    caption = (f"\U0001F4D8 Jargon buster — {t['term']}\n\n{t['def']}\n\n"
               f"Example: {t['eg']}\n\nSave this for later \U0001F516"
               + _footer_caption("#investing101 #financeeducation"))
    return slides, caption


# --- This or That (engagement) -------------------------------------------
def build_thisorthat() -> Tuple[List[Image.Image], str]:
    t = library.this_or_that_for_today()
    slides = [
        render.title_slide("This or that", ["THIS", "OR THAT?"], t["context"]),
        render.two_option_slide(t["a"], t["b"]),
        render.text_slide("Your call", f"{t['a']}  or  {t['b']}?",
                          "There's no single right answer — it depends on your goals, "
                          "horizon and risk comfort. Tell us your pick and why \U0001F447",
                          body_size=42),
        render.outro_slide(),
    ]
    caption = (f"\U0001F914 This or that: {t['a']} or {t['b']}?\n\n{t['context']}\n\n"
               f"Drop your pick in the comments \U0001F447"
               + _footer_caption("#thisorthat #personalfinance"))
    return slides, caption


# --- Mutual funds 101 (premium template, educational) --------------------
def build_mutualfunds() -> Tuple[List[Image.Image], str]:
    total = 6
    slides = [
        premium.cover("MUTUAL FUNDS 101", ["Mutual funds,", "explained"],
                      "The 2-minute beginner's guide", total),
        premium.section("What is a mutual fund?", [
            ("The idea",
             "It pools money from many investors, and a professional manager "
             "invests it in a basket of stocks, bonds or both."),
            ("Why people use them",
             "Instant diversification and professional management — even with a "
             "small amount like a ₹500 monthly SIP."),
        ], page=2, total=total),
        premium.section("The main types", [
            ("Equity funds", "Mostly stocks — higher growth, bigger swings."),
            ("Debt funds", "Bonds / fixed income — steadier, lower risk."),
            ("Hybrid funds", "A blend of equity + debt for balance."),
            ("Index funds & ETFs", "Track an index like Nifty 50 at very low cost."),
        ], page=3, total=total),
        premium.section("Key terms to know", [
            ("NAV", "Net Asset Value — the per-unit price of the fund."),
            ("Expense ratio", "The fund's annual fee. Lower is better."),
            ("AUM", "Assets Under Management — total money in the fund."),
            ("Exit load", "A small fee if you redeem too early."),
        ], page=4, total=total),
        premium.section("How to start", [
            ("1. Set your goal", "Know your time horizon and risk comfort first."),
            ("2. Pick a fund type", "Match it to the goal — equity for long-term "
             "growth, debt for stability."),
            ("3. Start an SIP", "Automate a fixed monthly amount and stay consistent."),
        ], page=5, total=total),
        premium.outro(page=6, total=total),
    ]
    caption = (
        "\U0001F4B0 Mutual Funds 101 — the 2-minute beginner's guide\n\n"
        "A mutual fund pools money from many investors and a professional manager "
        "invests it in a basket of stocks and/or bonds — giving you instant "
        "diversification, even with a small SIP.\n\n"
        "Types: \U0001F4C8 Equity (growth) • \U0001F3E6 Debt (stability) • "
        "⚖️ Hybrid (both) • \U0001F4CA Index/ETF (low-cost)\n\n"
        "Key terms: NAV, expense ratio, AUM, exit load.\n\n"
        "Save this for later \U0001F516 and follow for a beginner-friendly money "
        "tip every day."
        + _footer_caption("#mutualfunds #sip #mutualfundssahihai #investing101")
    )
    return slides, caption


POST_TYPES: Dict[str, Callable[[], Tuple[List[Image.Image], str]]] = {
    "recap": build_recap,
    "global": build_global,
    "news": build_news,
    "quiz": build_quiz,
    "term": build_term,
    "thisorthat": build_thisorthat,
    "mutualfunds": build_mutualfunds,
}

# Weekday rotation for the "extra" (non-recap) daily post. Mon=0 .. Sun=6.
EXTRA_ROTATION = {
    0: "global",       # Monday
    1: "quiz",         # Tuesday
    2: "term",         # Wednesday
    3: "thisorthat",   # Thursday
    4: "news",         # Friday
    5: "term",         # Saturday
    6: "quiz",         # Sunday
}


def resolve_type(post_type: str) -> str:
    """Turn 'auto-extra' into a concrete type based on today's weekday (IST)."""
    if post_type == "auto-extra":
        return EXTRA_ROTATION[date.today().weekday()]
    if post_type not in POST_TYPES:
        raise ValueError(f"Unknown post type: {post_type}. "
                         f"Choices: {', '.join(POST_TYPES)} or auto-extra")
    return post_type


def build(post_type: str) -> Tuple[List[Image.Image], str]:
    return POST_TYPES[resolve_type(post_type)]()
