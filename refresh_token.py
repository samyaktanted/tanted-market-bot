"""Refreshes the long-lived Instagram token for another ~60 days and writes the
new value to new_token.txt (the workflow then stores it back as a GitHub secret).

The new token is NEVER printed to stdout, so it can't leak into CI logs.
Reads the current token from IG_ACCESS_TOKEN (env)."""
import sys

import requests

import config


def main():
    if not config.IG_ACCESS_TOKEN:
        sys.exit("IG_ACCESS_TOKEN is not set.")

    resp = requests.get(
        f"https://{config.IG_API_HOST}/refresh_access_token",
        params={
            "grant_type": "ig_refresh_token",
            "access_token": config.IG_ACCESS_TOKEN,
        },
        timeout=30,
    ).json()

    if "access_token" not in resp:
        sys.exit(f"Refresh failed: {resp}")

    new_token = resp["access_token"]
    days = round(resp.get("expires_in", 0) / 86400)

    with open("new_token.txt", "w", encoding="utf-8") as f:
        f.write(new_token)

    # Only non-secret info is printed.
    print(f"Token refreshed. New token valid for ~{days} days. Wrote new_token.txt")


if __name__ == "__main__":
    main()
