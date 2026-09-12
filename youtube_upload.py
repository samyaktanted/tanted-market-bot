"""Upload a video to YouTube via the Data API v3 (faceless-channel automation).

One-time setup (you do this once in Google Cloud):
  1. Create a project, enable "YouTube Data API v3".
  2. OAuth consent screen (External, add yourself as a test user).
  3. Create an OAuth Client ID (type: Desktop). Note client_id + client_secret.
  4. Run the local consent flow once to get a refresh token (see get_refresh
     token helper below: `python youtube_upload.py --auth`).
Store as env / GitHub secrets: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.

Usage:
  python youtube_upload.py --file output/video/short.mp4 \
      --title "How Rs 5,000/month becomes Rs 50 lakh" \
      --description-file output/video/anim_caption.txt --shorts --privacy public
"""
import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials(
        None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri=TOKEN_URI,
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds)


def upload(file: str, title: str, description: str, tags, privacy="public",
           shorts=False) -> str:
    from googleapiclient.http import MediaFileUpload
    if shorts and "#Shorts" not in description:
        description = description.rstrip() + "\n\n#Shorts"
    body = {
        "snippet": {"title": title[:100], "description": description[:4900],
                    "tags": tags, "categoryId": "22"},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(file, chunksize=-1, resumable=True,
                            mimetype="video/mp4")
    req = _service().videos().insert(part="snippet,status", body=body,
                                     media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"upload {int(status.progress()*100)}%")
    vid = resp["id"]
    print(f"UPLOADED https://youtu.be/{vid}  (privacy={privacy})")
    return vid


def _auth_flow():
    """Run once locally to mint a refresh token."""
    from google_auth_oauthlib.flow import InstalledAppFlow
    cfg = {"installed": {
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": TOKEN_URI,
        "redirect_uris": ["http://localhost"]}}
    flow = InstalledAppFlow.from_client_config(cfg, SCOPES)
    creds = flow.run_local_server(port=0)
    print("\nYT_REFRESH_TOKEN=", creds.refresh_token, sep="")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--auth", action="store_true", help="one-time: get refresh token")
    ap.add_argument("--file")
    ap.add_argument("--title", default="")
    ap.add_argument("--description-file")
    ap.add_argument("--tags", default="investing,finance,sip,compounding,india")
    ap.add_argument("--privacy", default="public",
                    choices=["public", "unlisted", "private"])
    ap.add_argument("--shorts", action="store_true")
    a = ap.parse_args()
    if a.auth:
        _auth_flow(); return
    if not a.file:
        sys.exit("--file required")
    desc = open(a.description_file, encoding="utf-8").read() if a.description_file else ""
    upload(a.file, a.title, desc, a.tags.split(","), a.privacy, a.shorts)


if __name__ == "__main__":
    main()
