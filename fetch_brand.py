"""One-off: pull the account's profile picture (logo) and list recent posts via
the Instagram Graph API, using the token in .env. Saves logo to assets/logo.png."""
import os

import requests

import config

HOST, VER = config.IG_API_HOST, config.GRAPH_API_VERSION
TOK = config.IG_ACCESS_TOKEN


def main():
    os.makedirs("assets", exist_ok=True)
    me = requests.get(
        f"https://{HOST}/{VER}/me",
        params={"fields": "username,account_type,media_count,profile_picture_url",
                "access_token": TOK},
        timeout=30,
    ).json()
    print("Account:", {k: v for k, v in me.items() if k != "profile_picture_url"})

    pic = me.get("profile_picture_url")
    if pic:
        img = requests.get(pic, timeout=30).content
        with open("assets/logo.png", "wb") as f:
            f.write(img)
        print(f"Saved logo -> assets/logo.png ({len(img)} bytes)")
    else:
        print("No profile_picture_url returned (permission or empty).")

    media = requests.get(
        f"https://{HOST}/{VER}/me/media",
        params={"fields": "id,caption,media_type,timestamp,permalink",
                "limit": 8, "access_token": TOK},
        timeout=30,
    ).json()
    print("\nRecent posts:")
    for m in media.get("data", []):
        cap = (m.get("caption") or "").split("\n")[0][:70]
        print(f"  [{m.get('media_type')}] {m.get('timestamp','')[:10]}  {cap}")


if __name__ == "__main__":
    main()
