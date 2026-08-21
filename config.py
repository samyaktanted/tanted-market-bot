"""Central configuration. Values are read from environment variables so the
same code runs locally (via a .env file) and in GitHub Actions (via secrets)."""
import os

try:
    # Load a local .env if present. In CI the vars come from secrets instead.
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# ---- Brand ----
BRAND_NAME = os.getenv("BRAND_NAME", "Tanted Investments")
BRAND_HANDLE = os.getenv("BRAND_HANDLE", "@tanted_investments")
BRAND_WEBSITE = os.getenv("BRAND_WEBSITE", "tantedinvestments.com")

# Colors (hex). Tweak to match your brand palette.
COLOR_BG = os.getenv("COLOR_BG", "#0B1F3A")        # deep navy
COLOR_ACCENT = os.getenv("COLOR_ACCENT", "#E8B04B")  # gold
COLOR_UP = os.getenv("COLOR_UP", "#2ECC71")        # green
COLOR_DOWN = os.getenv("COLOR_DOWN", "#E74C3C")    # red
COLOR_TEXT = os.getenv("COLOR_TEXT", "#FFFFFF")
COLOR_MUTED = os.getenv("COLOR_MUTED", "#9FB3C8")

# Optional path to a .ttf font. If unset, we auto-detect a system font.
FONT_PATH = os.getenv("FONT_PATH", "")

# ---- Instagram API (Instagram Login use case) ----
# Uses "Instagram API with Instagram Login" -> host graph.instagram.com.
# IG_USER_ID here is the Instagram professional account id from
#   GET https://graph.instagram.com/v21.0/me?fields=user_id,username
IG_USER_ID = os.getenv("IG_USER_ID", "")           # Instagram professional account id
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")  # Long-lived Instagram user token
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v21.0")
# API host. graph.instagram.com for Instagram Login; change to graph.facebook.com
# only if you use the older Facebook-Login (linked Page) flow instead.
IG_API_HOST = os.getenv("IG_API_HOST", "graph.instagram.com")

# Public base URL where generated slide images are reachable (must be public
# HTTPS for the Graph API to fetch them). In CI this is set to a raw GitHub URL.
PUBLIC_IMAGE_BASE_URL = os.getenv("PUBLIC_IMAGE_BASE_URL", "").rstrip("/")

# ---- Output ----
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")

# Required, non-negotiable disclaimer appended to every post.
DISCLAIMER = (
    "Disclaimer: Educational content only, not investment advice. "
    "Markets carry risk. Do your own research or consult a SEBI-registered "
    "advisor before investing."
)
