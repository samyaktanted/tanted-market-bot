"""One-time helper: turn a short-lived Instagram token into a long-lived one,
fetch your account id, and save both to a local .env file.

Run it in YOUR terminal (so the secrets stay on your machine):

    python setup_token.py

It will prompt for your short-lived token and your app secret. Nothing is
printed in full or sent anywhere except Meta's own API."""
import sys
from getpass import getpass

import requests

import config

HOST = config.IG_API_HOST          # graph.instagram.com
VER = config.GRAPH_API_VERSION     # v21.0


def main():
    print("Paste the values when prompted (input is hidden).\n")
    short_token = getpass("Short-lived token: ").strip()
    app_secret = getpass("App secret (App settings -> Basic): ").strip()
    if not short_token or not app_secret:
        sys.exit("Both values are required.")

    # 1) who am I -> user_id
    me = requests.get(
        f"https://{HOST}/{VER}/me",
        params={"fields": "user_id,username", "access_token": short_token},
        timeout=30,
    ).json()
    if "error" in me:
        sys.exit(f"Token check failed: {me['error']}")
    user_id = me.get("user_id") or me.get("id")
    username = me.get("username", "?")
    print(f"Account: @{username}  (id: {user_id})")

    # 2) exchange for a long-lived token (~60 days)
    ll = requests.get(
        f"https://{HOST}/access_token",
        params={
            "grant_type": "ig_exchange_token",
            "client_secret": app_secret,
            "access_token": short_token,
        },
        timeout=30,
    ).json()
    if "error" in ll or "access_token" not in ll:
        sys.exit(f"Long-lived exchange failed: {ll}")
    long_token = ll["access_token"]
    expires_days = round(ll.get("expires_in", 0) / 86400)
    print(f"Long-lived token obtained. Expires in ~{expires_days} days.")

    # 3) write .env (kept local; .gitignore already excludes it)
    lines = [
        f"IG_USER_ID={user_id}",
        f"IG_ACCESS_TOKEN={long_token}",
        f"GRAPH_API_VERSION={VER}",
        f"IG_API_HOST={HOST}",
    ]
    with open(".env", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\nSaved to .env  (do NOT commit this file — .gitignore already blocks it)")
    print("\nNext: add these two as GitHub repo secrets:")
    print(f"  IG_USER_ID       = {user_id}")
    print("  IG_ACCESS_TOKEN  = <the long-lived token in your .env>")


if __name__ == "__main__":
    main()
