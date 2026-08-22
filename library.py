"""Vetted, hand-written content for the interactive/educational post types.
Nothing here is AI-generated at runtime. Add your own entries freely.

One item per type is picked per day, rotating deterministically by day-of-year
so posts are reproducible and cycle through the whole list."""
from datetime import date
from typing import Dict, List


def _pick(items: list):
    return items[date.today().timetuple().tm_yday % len(items)]


# ---- Quizzes: question, 4 options, index of correct answer, explanation ----
QUIZZES: List[Dict] = [
    {
        "q": "What does 'Nifty 50' represent?",
        "options": ["Top 50 NSE companies", "50 penny stocks",
                    "50 mutual funds", "A crypto index"],
        "answer": 0,
        "why": "Nifty 50 tracks the 50 largest, most liquid companies listed on "
               "the NSE — a benchmark for the broad Indian market.",
    },
    {
        "q": "A 'bull market' means prices are generally…",
        "options": ["Falling", "Flat", "Rising", "Frozen"],
        "answer": 2,
        "why": "A bull market is a sustained period of rising prices and optimism. "
               "A falling market is called a 'bear' market.",
    },
    {
        "q": "What is a 'dividend'?",
        "options": ["A type of loan", "A share of company profit paid to holders",
                    "A trading fee", "A stock split"],
        "answer": 1,
        "why": "A dividend is a portion of a company's profit distributed to "
               "shareholders, usually in cash.",
    },
    {
        "q": "What does 'IPO' stand for?",
        "options": ["Initial Public Offering", "Indian Profit Order",
                    "Internal Payout Option", "Investment Portfolio Owner"],
        "answer": 0,
        "why": "An IPO is when a private company first sells shares to the public "
               "and lists on a stock exchange.",
    },
    {
        "q": "Which is generally the LOWEST-risk?",
        "options": ["Small-cap stock", "Large-cap index fund",
                    "Crypto", "Single mid-cap stock"],
        "answer": 1,
        "why": "A large-cap index fund spreads money across many established "
               "companies, so it's usually less volatile than a single stock or crypto.",
    },
    {
        "q": "'SIP' in investing stands for…",
        "options": ["Stock Investment Plan", "Systematic Investment Plan",
                    "Single Instalment Payment", "Secure Interest Product"],
        "answer": 1,
        "why": "A Systematic Investment Plan invests a fixed amount at regular "
               "intervals, averaging your buy price over time.",
    },
    {
        "q": "What does a company's 'market cap' measure?",
        "options": ["Its yearly profit", "Its total debt",
                    "Total value of its shares", "Its dividend rate"],
        "answer": 2,
        "why": "Market cap = share price × number of shares. It's the total market "
               "value of the company's equity.",
    },
]

# ---- Jargon buster: term, plain definition, everyday example ----
TERMS: List[Dict] = [
    {"term": "Bull vs Bear",
     "def": "A 'bull' market rises; a 'bear' market falls.",
     "eg": "2021 was largely a bull run; sharp COVID-crash months were bearish."},
    {"term": "Blue-chip stock",
     "def": "Shares of large, well-established, financially sound companies.",
     "eg": "Names like Reliance, TCS or HDFC Bank are often called blue-chips."},
    {"term": "Market cap",
     "def": "The total value of a company's shares (price × number of shares).",
     "eg": "A ₹100 share × 10 crore shares = ₹1,000 crore market cap."},
    {"term": "P/E ratio",
     "def": "Price divided by earnings per share — how much you pay per ₹1 of profit.",
     "eg": "A P/E of 25 means you pay ₹25 for every ₹1 the company earns yearly."},
    {"term": "Dividend yield",
     "def": "Annual dividend as a % of the share price.",
     "eg": "A ₹10 dividend on a ₹200 share is a 5% dividend yield."},
    {"term": "Volatility",
     "def": "How much and how fast a price swings up and down.",
     "eg": "Small-caps are usually more volatile than large-cap index funds."},
    {"term": "Liquidity",
     "def": "How easily an asset can be bought/sold without moving its price.",
     "eg": "Nifty 50 stocks are highly liquid; obscure penny stocks are not."},
]

# ---- This or That: two options + a neutral discussion prompt ----
THIS_OR_THAT: List[Dict] = [
    {"a": "SIP", "b": "Lump sum",
     "context": "Investing a fixed amount monthly, or all at once?"},
    {"a": "Index funds", "b": "Individual stocks",
     "context": "Broad, low-effort diversification, or hand-picking companies?"},
    {"a": "Gold", "b": "Equity",
     "context": "A traditional store of value, or long-term growth?"},
    {"a": "Large-cap", "b": "Small-cap",
     "context": "Stability, or higher growth with higher risk?"},
    {"a": "Save first", "b": "Invest first",
     "context": "Build the emergency fund, or start investing early?"},
    {"a": "Active funds", "b": "Passive funds",
     "context": "Pay a manager to beat the market, or just track it cheaply?"},
]


def quiz_for_today() -> Dict:
    return _pick(QUIZZES)


def term_for_today() -> Dict:
    return _pick(TERMS)


def this_or_that_for_today() -> Dict:
    return _pick(THIS_OR_THAT)
