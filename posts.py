"""Registry of post types. Each builder returns (images, caption).

Every post type uses the premium branded template (premium.py): gradient
background, gold glow, logo badges, cards, icons and page numbers.

Add a new post type by writing a build_* function and registering it in
POST_TYPES. Daily/extra workflows pick a type by name or by weekday."""
from datetime import date
from typing import Callable, Dict, List, Tuple

from PIL import Image

import config
import content
import library
import market_data
import news
import premium

HASHTAGS = " ".join(content.HASHTAGS)


def _footer_caption(extra_tags: str = "") -> str:
    tags = HASHTAGS + (" " + extra_tags if extra_tags else "")
    return (f"\nFollow {config.BRAND_HANDLE} for daily market content. "
            f"More at {config.BRAND_WEBSITE}\n\n{config.DISCLAIMER}\n\n{tags}")


def _assemble(specs: List[Callable[[int, int], Image.Image]]) -> List[Image.Image]:
    total = len(specs)
    return [fn(i + 1, total) for i, fn in enumerate(specs)]


# --- Daily recap (the anchor post) ---------------------------------------
def build_recap() -> Tuple[List[Image.Image], str]:
    import tips
    snap = market_data.get_snapshot()
    tip = tips.tip_for_today()
    specs = [
        lambda p, t: premium.cover("MARKET RECAP", ["Daily market", "recap"],
                                   snap.date_ist, t, hero="chart_up"),
        lambda p, t: premium.rows("Where markets closed", snap.indices, p, t),
    ]
    if snap.gainers:
        specs.append(lambda p, t: premium.rows("Top gainers", snap.gainers, p, t))
    if snap.losers:
        specs.append(lambda p, t: premium.rows("Top losers", snap.losers, p, t))
    specs.append(lambda p, t: premium.section("Tip of the day",
                                              [(tip[0], tip[1], "bulb")], p, t))
    specs.append(lambda p, t: premium.outro(p, t))
    return _assemble(specs), content.build_caption(snap, tip)


# --- Global cues (pre-market / morning) ----------------------------------
def build_global() -> Tuple[List[Image.Image], str]:
    date_str = market_data.today_ist()
    cues = market_data.get_quotes(market_data.GLOBAL_CUES)
    extras = market_data.get_quotes(market_data.COMMODITIES_FX)
    specs = [lambda p, t: premium.cover("GLOBAL CUES", ["Global", "cues"],
                                        f"Good morning  |  {date_str}", t, hero="globe")]
    if cues:
        specs.append(lambda p, t: premium.rows("Overnight global markets", cues, p, t))
    if extras:
        specs.append(lambda p, t: premium.rows("Commodities, FX & crypto", extras, p, t))
    specs.append(lambda p, t: premium.outro(p, t))

    lines = [f"Global cues \U0001F30F  |  {date_str}", ""]
    for q in cues:
        arrow = "\U0001F7E2" if q.is_up else "\U0001F534"
        lines.append(f"{arrow} {q.name}: {q.change_pct:+.2f}%")
    return _assemble(specs), "\n".join(lines) + _footer_caption("#premarket #globalmarkets")


# --- News roundup ---------------------------------------------------------
def build_news() -> Tuple[List[Image.Image], str]:
    date_str = market_data.today_ist()
    heads = news.get_headlines(limit=4)
    specs = [lambda p, t: premium.cover("MARKET NEWS", ["Today in", "markets"],
                                        date_str, t, hero="newspaper")]
    if heads:
        items = [(h.title, h.source) for h in heads]
        specs.append(lambda p, t: premium.list_slide("Top headlines", items, p, t))
    specs.append(lambda p, t: premium.outro(p, t))

    cap_lines = [f"Today's market headlines \U0001F4F0  |  {date_str}", ""]
    for h in heads:
        cap_lines.append(f"• {h.title} — {h.source}")
    cap_lines.append("\n(Headlines aggregated from public sources; tap through to "
                     "each outlet for the full story.)")
    return _assemble(specs), "\n".join(cap_lines) + _footer_caption("#marketnews #businessnews")


# --- Quiz (with reveal) ---------------------------------------------------
def build_quiz() -> Tuple[List[Image.Image], str]:
    q = library.quiz_for_today()
    opts = q["options"]
    letters = ["A", "B", "C", "D"]
    opt_cards = [(f"{letters[i]}.  {o}", "") for i, o in enumerate(opts)]
    opt_lines = [f"{letters[i]}.  {o}" for i, o in enumerate(opts)]
    ans = letters[q["answer"]]
    specs = [
        lambda p, t: premium.cover("QUIZ TIME", ["Test", "yourself"],
                                   "Swipe to reveal the answer", t, hero="question"),
        lambda p, t: premium.text_block("Question", q["q"],
                                        "Comment your answer before you swipe!", p, t),
        lambda p, t: premium.section("Pick one", opt_cards, p, t),
        lambda p, t: premium.text_block("Answer", f"{ans}. {opts[q['answer']]}",
                                        q["why"], p, t),
        lambda p, t: premium.outro(p, t),
    ]
    caption = (f"\U0001F9E0 Market quiz!\n\n{q['q']}\n\n" + "\n".join(opt_lines)
               + "\n\nComment your guess \U0001F447 (answer on the last slide)"
               + _footer_caption("#financequiz #investingbasics"))
    return _assemble(specs), caption


# --- Jargon buster / term of the day -------------------------------------
def build_term() -> Tuple[List[Image.Image], str]:
    tm = library.term_for_today()
    specs = [
        lambda p, t: premium.cover("TERM OF THE DAY", ["Jargon", "buster"],
                                   tm["term"], t, hero="book"),
        lambda p, t: premium.text_block("What it means", tm["term"], tm["def"],
                                        p, t, body_size=48),
        lambda p, t: premium.text_block("Example", tm["term"], tm["eg"],
                                        p, t, body_size=46),
        lambda p, t: premium.outro(p, t),
    ]
    caption = (f"\U0001F4D8 Jargon buster — {tm['term']}\n\n{tm['def']}\n\n"
               f"Example: {tm['eg']}\n\nSave this for later \U0001F516"
               + _footer_caption("#investing101 #financeeducation"))
    return _assemble(specs), caption


# --- This or That (engagement) -------------------------------------------
def build_thisorthat() -> Tuple[List[Image.Image], str]:
    to = library.this_or_that_for_today()
    specs = [
        lambda p, t: premium.cover("THIS OR THAT", ["This", "or that?"],
                                   to["context"], t, hero="scale"),
        lambda p, t: premium.versus(to["a"], to["b"], p, t),
        lambda p, t: premium.text_block("Your call", f"{to['a']} or {to['b']}?",
                                        "There's no single right answer — it depends "
                                        "on your goals, horizon and risk comfort. Tell "
                                        "us your pick and why below.", p, t, body_size=44),
        lambda p, t: premium.outro(p, t),
    ]
    caption = (f"\U0001F914 This or that: {to['a']} or {to['b']}?\n\n{to['context']}\n\n"
               f"Drop your pick in the comments \U0001F447"
               + _footer_caption("#thisorthat #personalfinance"))
    return _assemble(specs), caption


# --- Mutual funds 101 -----------------------------------------------------
def build_mutualfunds() -> Tuple[List[Image.Image], str]:
    specs = [
        lambda p, t: premium.cover("MUTUAL FUNDS 101", ["Mutual funds,", "explained"],
                                   "The 2-minute beginner's guide", t, hero="bar_chart"),
        lambda p, t: premium.section("What is a mutual fund?", [
            ("The idea", "It pools money from many investors, and a professional "
             "manager invests it in a basket of stocks, bonds or both.", "bulb"),
            ("Why people use them", "Instant diversification and professional "
             "management — even with a small ₹500 monthly SIP.", "grid"),
        ], p, t),
        lambda p, t: premium.section("The main types", [
            ("Equity funds", "Mostly stocks — higher growth, bigger swings.", "chart_up"),
            ("Debt funds", "Bonds / fixed income — steadier, lower risk.", "shield"),
            ("Hybrid funds", "A blend of equity + debt for balance.", "scale"),
            ("Index funds & ETFs", "Track an index like Nifty 50 at very low cost.",
             "bar_chart"),
        ], p, t),
        lambda p, t: premium.section("Key terms to know", [
            ("NAV", "Net Asset Value — the per-unit price of the fund.", "rupee"),
            ("Expense ratio", "The fund's annual fee. Lower is better.", "percent"),
            ("AUM", "Assets Under Management — total money in the fund.", "coins"),
            ("Exit load", "A small fee if you redeem too early.", "warning"),
        ], p, t),
        lambda p, t: premium.section("How to start", [
            ("1. Set your goal", "Know your time horizon and risk comfort first.",
             "target"),
            ("2. Pick a fund type", "Match it to the goal — equity for long-term "
             "growth, debt for stability.", "grid"),
            ("3. Start an SIP", "Automate a fixed monthly amount and stay consistent.",
             "calendar"),
        ], p, t),
        lambda p, t: premium.outro(p, t),
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
    return _assemble(specs), caption


# --- REITs & InvITs 101 ---------------------------------------------------
def build_reitinvit() -> Tuple[List[Image.Image], str]:
    specs = [
        lambda p, t: premium.cover("REITs & INVITS", ["REITs & InvITs,", "explained"],
                                   "Invest in real estate & infrastructure", t,
                                   hero="building"),
        lambda p, t: premium.section("What are they?", [
            ("REIT", "Real Estate Investment Trust — pools money to own rent-earning "
             "property like malls, offices and warehouses.", "building"),
            ("InvIT", "Infrastructure Investment Trust — owns income assets like "
             "highways, power transmission lines and pipelines.", "road"),
        ], p, t),
        lambda p, t: premium.section("How they work", [
            ("Listed & tradable", "Both list on the exchange and trade like shares.",
             "chart_up"),
            ("You own units", "You buy 'units' — each is a small slice of the trust.",
             "pie"),
            ("Income pass-through", "They pay out most of their income to unitholders.",
             "coins"),
        ], p, t),
        lambda p, t: premium.section("Why people consider them", [
            ("Regular income", "Distributions can offer a steady payout stream.",
             "coins"),
            ("Diversification", "Exposure beyond just stocks and bonds.", "grid"),
            ("Access + liquidity", "Own a share of big assets with a small amount.",
             "check"),
        ], p, t),
        lambda p, t: premium.section("Know the risks", [
            ("Rate sensitive", "Prices often dip when interest rates rise.", "percent"),
            ("Market swings", "Unit prices move with the market, not just the assets.",
             "chart_down"),
            ("Concentration", "Returns depend on a limited set of assets.", "target"),
        ], p, t),
        lambda p, t: premium.section("Key terms", [
            ("Unit", "One tradable slice of the trust.", "pie"),
            ("DPU", "Distribution Per Unit — income paid per unit.", "coins"),
            ("Yield", "Annual distribution as a % of the unit price.", "percent"),
        ], p, t),
        lambda p, t: premium.outro(p, t),
    ]
    caption = (
        "\U0001F3E2 REITs & InvITs, explained\n\n"
        "Want a slice of real estate or infrastructure without buying a whole "
        "building or highway? That's what these trusts let you do:\n\n"
        "\U0001F3EC REIT — owns rent-earning property (malls, offices, warehouses)\n"
        "\U0001F6E3️ InvIT — owns income infrastructure (roads, power lines, pipelines)\n\n"
        "Both list on the exchange, you buy 'units', and they pass most of their "
        "income back to you as regular distributions.\n\n"
        "Remember: unit prices swing with the market and are sensitive to interest "
        "rates. Save this \U0001F516 and follow for more."
        + _footer_caption("#reit #invit #realestate #passiveincome #investing101")
    )
    return _assemble(specs), caption


# --- SIP + how to choose a fund (no specific recommendations) -------------
def build_sip() -> Tuple[List[Image.Image], str]:
    specs = [
        lambda p, t: premium.cover("SIP EXPLAINED", ["The power", "of SIP"],
                                   "Small amounts, big habits", t, hero="piggy"),
        lambda p, t: premium.section("What is an SIP?", [
            ("The idea", "A Systematic Investment Plan invests a fixed amount "
             "automatically at regular intervals — say ₹1,000 every month.", "calendar"),
            ("Why it works", "You invest through ups and downs, so you never have "
             "to time the market.", "chart_up"),
        ], p, t),
        lambda p, t: premium.section("Two superpowers", [
            ("Rupee-cost averaging", "You buy more units when prices are low and "
             "fewer when high, smoothing your average cost.", "swap"),
            ("Compounding", "Returns start earning their own returns — the longer "
             "you stay, the bigger the snowball.", "snowball"),
        ], p, t),
        lambda p, t: premium.section("How to choose a fund", [
            ("Match the goal", "Long-term wealth: equity funds. Short-term needs: "
             "debt funds.", "target"),
            ("Prefer low cost", "A lower expense ratio keeps more returns with you; "
             "index funds are cheap.", "percent"),
            ("Check consistency", "Look at long-term track record and risk — not just "
             "last year's return.", "check"),
        ], p, t),
        lambda p, t: premium.section("Common mistakes", [
            ("Stopping in a dip", "Dips are when SIPs buy cheap — pausing defeats "
             "the purpose.", "warning"),
            ("Chasing last year's winner", "Past returns don't guarantee future ones.",
             "chart_down"),
            ("No goal or horizon", "Invest with a clear purpose and time frame.",
             "target"),
        ], p, t),
        lambda p, t: premium.text_block("Bottom line", "Start small, stay consistent",
                                        "Even ₹500 a month — started early and left to "
                                        "compound — can grow into a meaningful corpus "
                                        "over the years. Consistency beats timing.", p, t),
        lambda p, t: premium.outro(p, t),
    ]
    caption = (
        "\U0001F4C8 The power of SIP\n\n"
        "A Systematic Investment Plan invests a fixed amount automatically every "
        "month — so you build wealth on autopilot without trying to time the "
        "market.\n\n"
        "Why it works: rupee-cost averaging (buy more when cheap) + compounding "
        "(returns earning returns).\n\n"
        "How to choose a fund (we don't recommend specific schemes): match it to "
        "your goal, prefer a low expense ratio, and check long-term consistency — "
        "not last year's chart.\n\n"
        "Save this \U0001F516 and start small. Even ₹500/month adds up."
        + _footer_caption("#sip #mutualfunds #compounding #investing101 #wealthbuilding")
    )
    return _assemble(specs), caption


POST_TYPES: Dict[str, Callable[[], Tuple[List[Image.Image], str]]] = {
    "recap": build_recap,
    "global": build_global,
    "news": build_news,
    "quiz": build_quiz,
    "term": build_term,
    "thisorthat": build_thisorthat,
    "mutualfunds": build_mutualfunds,
    "reitinvit": build_reitinvit,
    "sip": build_sip,
}

EXTRA_ROTATION = {
    0: "global", 1: "quiz", 2: "term", 3: "thisorthat", 4: "news", 5: "term", 6: "quiz",
}


def resolve_type(post_type: str) -> str:
    if post_type == "auto-extra":
        return EXTRA_ROTATION[date.today().weekday()]
    if post_type not in POST_TYPES:
        raise ValueError(f"Unknown post type: {post_type}. "
                         f"Choices: {', '.join(POST_TYPES)} or auto-extra")
    return post_type


def build(post_type: str) -> Tuple[List[Image.Image], str]:
    return POST_TYPES[resolve_type(post_type)]()
