# Tanted Investments — Daily Market Post Bot

Automated system that researches the **Indian markets** each day and posts a
**multi-slide carousel** (daily recap + educational tip) to Instagram
[@tanted_investments](https://www.instagram.com/tanted_investments) via the
Meta Graph API. Runs on a schedule with GitHub Actions.

Every number in a post comes from a **real market data feed** (Yahoo Finance) —
nothing is invented. Educational tips come from a hand-written, vetted library.
A **"not investment advice"** disclaimer is included in every post.

## What it produces

A 6-slide carousel (4:5, 1080×1350):

1. Cover — date + Nifty 50 headline number
2. Where markets closed — Nifty 50, Sensex, Bank Nifty
3. Top gainers (Nifty 50)
4. Top losers (Nifty 50)
5. Tip of the day
6. Follow CTA + disclaimer

…plus a caption with the numbers, the tip, links, disclaimer, and hashtags.

## Repo layout

| File | Purpose |
|---|---|
| `market_data.py` | Pulls indices + Nifty 50 movers via yfinance |
| `tips.py` | Vetted educational tip library (edit this to add your own) |
| `content.py` | Builds the Instagram caption |
| `render.py` | Renders the carousel PNGs (Pillow) |
| `instagram.py` | Publishes the carousel via Meta Graph API |
| `main.py` | `generate` and `publish` commands |
| `config.py` | All settings, read from env vars |
| `.github/workflows/daily-post.yml` | Daily schedule |

## Quick start (local test — no posting)

```bash
cd tanted-market-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py generate
```

This writes slides + `caption.txt` + `manifest.json` to `output/<date>/`.
Open the PNGs to review. No Instagram credentials needed for this step.

## Going live: Instagram auto-posting setup

Instagram only allows automated posting through the **Meta Graph API**, which
requires a bit of one-time setup:

1. **Convert the account to Business or Creator** (Instagram app → Settings →
   Account type). Personal accounts cannot use the publishing API.
2. **Create a Facebook Page** and link the Instagram account to it.
3. Go to **developers.facebook.com** → create an App (type: *Business*).
4. Add the **Instagram Graph API** product and request the permissions
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`.
5. Use the **Graph API Explorer** to get a User token, then exchange it for a
   **long-lived token** (~60 days). Automate refresh, or refresh it before it
   expires. (Meta docs: "Long-Lived Access Tokens".)
6. Get your **Instagram Business Account ID** (`GET /me/accounts` → then
   `GET /{page-id}?fields=instagram_business_account`).

Then set two secrets: `IG_USER_ID` and `IG_ACCESS_TOKEN`.

> ⚠️ Meta fetches the slide images from a **public HTTPS URL**. The CI serves
> them from `raw.githubusercontent.com` — which means **the repo must be public**
> for the default setup to work. If you want the repo private, host the images
> on your own site (`tantedinvestments.com`) and set `PUBLIC_IMAGE_BASE_URL`
> to that folder instead.

### Test a real post locally

Host `output/<date>/` somewhere public, then:

```bash
cp .env.example .env   # fill in IG_USER_ID, IG_ACCESS_TOKEN, PUBLIC_IMAGE_BASE_URL
python main.py generate --publish
```

## Scheduling with GitHub Actions

1. Push this folder to a GitHub repo (public — see the note above).
2. Repo → **Settings → Secrets and variables → Actions** → add:
   - `IG_USER_ID`
   - `IG_ACCESS_TOKEN`
   - `GRAPH_API_VERSION` (optional, defaults to `v21.0`)
3. The workflow runs **Mon–Fri at 4:30 PM IST** (11:00 UTC). Trigger a manual
   test run any time from the **Actions** tab → *Daily market post* → *Run workflow*.

The workflow: generates slides → commits them to the repo (so they're public) →
publishes the carousel using the images at that commit.

## Safety & correctness notes

- **Not financial advice.** Every post carries the disclaimer in `config.DISCLAIMER`.
- **No fabricated data.** Prices/changes come from yfinance; tips are pre-written.
- **Holidays:** the schedule does not detect Indian market holidays — on those
  days it posts the last available close. Add a holiday check if you want it to skip.
- **Data source:** Yahoo Finance is a free, unofficial feed and can occasionally
  be delayed or miss a symbol. For production-grade accuracy consider a paid
  data provider and swap out `market_data.py`.
- **Token expiry:** long-lived tokens last ~60 days. Set a reminder to refresh,
  or add an auto-refresh step.

## Customizing

- **Colors/branding:** edit the `COLOR_*` and `BRAND_*` values in `config.py`
  (or set them as env vars).
- **Tips:** add entries to `TIPS` in `tips.py`.
- **Universe / indices:** edit `NIFTY50` and `INDICES` in `market_data.py`.
- **Hashtags:** edit `HASHTAGS` in `content.py`.
