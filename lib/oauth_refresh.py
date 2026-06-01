#!/usr/bin/env python3
"""Re-authenticate YouTube Analytics OAuth for Media Impact Lab.

Opens a browser for Google consent, captures the authorization code via a
local callback server, exchanges it for tokens, and saves the new
refresh_token to config.json.

Usage:
    python3 oauth_refresh.py
"""

import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

CFG_PATH = Path.home() / ".claude/skills/media-impact-lab/config/config.json"
REDIRECT_URI = "http://localhost:8765/callback"

cfg = json.loads(CFG_PATH.read_text())
oauth = cfg["youtube_oauth"]
CLIENT_ID = oauth["client_id"]
CLIENT_SECRET = oauth["client_secret"]

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Auth complete. Return to terminal.</h2></body></html>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing code param")

    def log_message(self, *args):
        pass  # suppress server logs


def main():
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urllib.parse.urlencode({
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        })
    )

    print("\n=== YouTube Analytics OAuth Re-authentication ===")
    print(f"\nOpening browser for Google consent...")
    subprocess.run(["open", auth_url])
    print("If browser didn't open, visit:\n", auth_url)
    print("\nWaiting for callback on http://localhost:8765 ...")

    server = HTTPServer(("localhost", 8765), CallbackHandler)
    server.timeout = 120
    server.handle_request()

    if not auth_code:
        print("ERROR: No authorization code received.")
        sys.exit(1)

    print("Code received. Exchanging for tokens...")

    data = urllib.parse.urlencode({
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp = json.loads(urllib.request.urlopen(req).read())

    if "refresh_token" not in resp:
        print("ERROR: No refresh_token in response:", resp)
        sys.exit(1)

    new_refresh = resp["refresh_token"]
    cfg["youtube_oauth"]["channels"]["eo_global"]["refresh_token"] = new_refresh
    CFG_PATH.write_text(json.dumps(cfg, indent=2))

    print(f"\nSaved new refresh_token to config.json")
    print("Re-authentication complete.")


if __name__ == "__main__":
    main()
