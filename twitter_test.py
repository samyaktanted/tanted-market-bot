"""Verify X (Twitter) API v2 access and optionally post a test tweet.

Usage:
  python twitter_test.py           # auth check only (GET /2/users/me)
  python twitter_test.py --post    # also post a timestamped test tweet

Reads these keys from .env (same file as the IG bot):
  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
Get them at https://developer.x.com (app must have Read+Write, OAuth 1.0a).
"""
import os
import sys
from datetime import datetime

import tweepy
from dotenv import load_dotenv

load_dotenv()

REQUIRED = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"]


def main() -> int:
    missing = [k for k in REQUIRED if not os.getenv(k)]
    if missing:
        print("MISSING CREDENTIALS:", ", ".join(missing))
        print("Add them to .env, then re-run. See https://developer.x.com")
        return 2

    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )

    try:
        me = client.get_me()
    except tweepy.TweepyException as e:
        print("AUTH FAILED:", e)
        return 1
    print(f"AUTH OK -> @{me.data.username} (id {me.data.id})")

    if "--post" in sys.argv:
        text = f"automation test {datetime.utcnow():%Y-%m-%d %H:%M:%S}Z"
        try:
            resp = client.create_tweet(text=text)
        except tweepy.TweepyException as e:
            print("POST FAILED:", e)
            return 1
        print(f"POSTED tweet id {resp.data['id']}: {text}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
