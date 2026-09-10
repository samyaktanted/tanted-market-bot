"""Refreshes the @ai_facts_knowledge long-lived Instagram token (~60 days) and
writes the new value to new_ai_token.txt. The CI workflow stores it back as the
IG_AI_ACCESS_TOKEN repo secret. The token is never printed to stdout.

Reads the current token from IG_AI_ACCESS_TOKEN (env)."""
import os
import sys

import requests

HOST = os.getenv("IG_API_HOST", "graph.instagram.com")


def main():
    token = os.getenv("IG_AI_ACCESS_TOKEN")
    if not token:
        sys.exit("IG_AI_ACCESS_TOKEN is not set.")

    resp = requests.get(
        f"https://{HOST}/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": token},
        timeout=30,
    ).json()

    if "access_token" not in resp:
        sys.exit(f"Refresh failed: {resp}")

    with open("new_ai_token.txt", "w", encoding="utf-8") as f:
        f.write(resp["access_token"])
    days = round(resp.get("expires_in", 0) / 86400)
    print(f"AI token refreshed. Valid ~{days} days. Wrote new_ai_token.txt")


if __name__ == "__main__":
    main()
