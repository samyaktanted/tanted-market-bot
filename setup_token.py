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
    token = getpass("Access token (from the dashboard): ").strip()
    # App secret is only needed IF the token is short-lived and must be exchanged.
    app_secret = getpass("App secret (optional - press Enter to skip): ").strip()
    if not token:
        sys.exit("An access token is required.")

    # 1) who am I -> user_id (also validates the token)
    me = requests.get(
        f"https://{HOST}/{VER}/me",
        params={"fields": "user_id,username", "access_token": token},
        timeout=30,
    ).json()
    if "error" in me:
        sys.exit(f"Token check failed: {me['error']}")
    user_id = me.get("user_id") or me.get("id")
    username = me.get("username", "?")
    print(f"Account: @{username}  (id: {user_id})")

    # 2) Try to exchange for a long-lived token. In the Instagram-Login flow the
    #    dashboard-generated token is ALREADY long-lived, so the exchange will
    #    fail with 'invalid token' - that's fine, we just keep the token as-is.
    long_token = token
    if app_secret:
        ll = requests.get(
            f"https://{HOST}/access_token",
            params={
                "grant_type": "ig_exchange_token",
                "client_secret": app_secret,
                "access_token": token,
            },
            timeout=30,
        ).json()
        if "access_token" in ll:
            long_token = ll["access_token"]
            days = round(ll.get("expires_in", 0) / 86400)
            print(f"Exchanged for a long-lived token (~{days} days).")
        else:
            print("Exchange not applicable - the dashboard token is already "
                  "long-lived. Keeping it as-is.")
    else:
        print("Skipping exchange - keeping the dashboard token (already long-lived).")

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
