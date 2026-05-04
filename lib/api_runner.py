#!/usr/bin/env python3
"""
YouTube Analytics + Data API runner for Media Impact Lab.

Usage:
    python3 api_runner.py video_summary VIDEO_ID [SLUG] [--channel eo_global|eo_korea]

Writes JSON to ~/Desktop/Cowork/media-impact-lab/screenshots/{slug}/{slug}_api.json
Never prints credentials. Stdout is metrics-only.
"""
import json, sys, os, urllib.request, urllib.parse, urllib.error, datetime as dt
from pathlib import Path

CFG_PATH = Path.home() / ".claude/skills/weekly-meeting/config/config.json"
OUT_ROOT = Path.home() / "Desktop/Cowork/media-impact-lab/screenshots"


def _load_cfg():
    return json.loads(CFG_PATH.read_text())


def _refresh_access_token(client_id, client_secret, refresh_token):
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read())
    return body["access_token"]


def _get(url, access_token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode("utf-8", "ignore")[:500]}


def _resolve_channel(cfg, channel_key):
    yt = cfg.get("youtube_oauth") or cfg.get("youtube_analytics") or {}
    channels = yt.get("channels") or {}
    ch = channels.get(channel_key)
    if not ch:
        raise SystemExit(f"ERROR: channel '{channel_key}' not found under youtube_oauth.channels (have: {list(channels.keys())})")
    client_id = yt.get("client_id") or ch.get("client_id")
    client_secret = yt.get("client_secret") or ch.get("client_secret")
    refresh_token = ch.get("refresh_token") or yt.get("refresh_token")
    channel_id = ch.get("channel_id") or yt.get("channel_id")
    if not (client_id and client_secret and refresh_token):
        raise SystemExit("ERROR: missing client_id / client_secret / refresh_token in config")
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "channel_id": channel_id,
    }


def video_summary(video_id, slug, channel_key="eo_global"):
    cfg = _load_cfg()
    creds = _resolve_channel(cfg, channel_key)
    channel_id = creds.get("channel_id") or "UClWTCPVi-AU9TeCN6FkGARg"
    access = _refresh_access_token(creds["client_id"], creds["client_secret"], creds["refresh_token"])
    data_api_key = (cfg.get("youtube") or {}).get("api_key")

    today = dt.date.today()
    end = today.isoformat()
    start = (today - dt.timedelta(days=14)).isoformat()

    base = "https://youtubeanalytics.googleapis.com/v2/reports"
    common = {
        "ids": f"channel=={channel_id}",
        "filters": f"video=={video_id}",
        "startDate": start,
        "endDate": end,
    }

    out = {"video_id": video_id, "slug": slug, "fetched_at": dt.datetime.utcnow().isoformat() + "Z",
           "window": {"start": start, "end": end}}

    summary_metrics = ",".join([
        "views", "estimatedMinutesWatched", "averageViewDuration", "averageViewPercentage",
        "subscribersGained", "subscribersLost", "likes", "comments", "shares",
    ])
    summary_url = base + "?" + urllib.parse.urlencode({**common, "metrics": summary_metrics})
    out["summary"] = _get(summary_url, access)

    daily_url = base + "?" + urllib.parse.urlencode({**common, "metrics": "views,estimatedMinutesWatched,subscribersGained,subscribersLost", "dimensions": "day", "sort": "day"})
    out["daily"] = _get(daily_url, access)

    src_url = base + "?" + urllib.parse.urlencode({**common, "metrics": "views,estimatedMinutesWatched", "dimensions": "insightTrafficSourceType", "sort": "-views"})
    out["traffic_source"] = _get(src_url, access)

    ret_url = base + "?" + urllib.parse.urlencode({**common, "metrics": "audienceWatchRatio,relativeRetentionPerformance", "dimensions": "elapsedVideoTimeRatio", "sort": "elapsedVideoTimeRatio"})
    out["retention"] = _get(ret_url, access)

    geo_url = base + "?" + urllib.parse.urlencode({**common, "metrics": "views,estimatedMinutesWatched,averageViewDuration", "dimensions": "country", "sort": "-views", "maxResults": 10})
    out["country"] = _get(geo_url, access)

    if data_api_key:
        v_url = (
            "https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails,liveStreamingDetails"
            f"&id={video_id}&key={data_api_key}"
        )
        out["video_data"] = _get(v_url, access)

    out_dir = OUT_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}_api.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps({"ok": True, "out": str(out_path),
                      "summary_rows": len((out["summary"] or {}).get("rows", []) or []),
                      "daily_rows": len((out["daily"] or {}).get("rows", []) or []),
                      "retention_rows": len((out["retention"] or {}).get("rows", []) or [])}))


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "video_summary":
        print(__doc__)
        sys.exit(2)
    video_id = sys.argv[2]
    slug = sys.argv[3] if len(sys.argv) > 3 else video_id
    channel = "eo_global"
    if "--channel" in sys.argv:
        channel = sys.argv[sys.argv.index("--channel") + 1]
    video_summary(video_id, slug, channel)
