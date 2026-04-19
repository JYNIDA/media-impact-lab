#!/usr/bin/env python3
"""pw-studio.py — Playwright-based YouTube Studio scraper with persistent login.

First run: `login` mode opens a headful browser so the user can sign into Google.
Cookies persist in a user_data_dir under this skill. Subsequent `fetch` runs use
the saved session (headless by default, or headful if the session needs a refresh).

Usage:
    python3 pw-studio.py login
    python3 pw-studio.py fetch VIDEO_ID [OUT_SUBDIR]
    python3 pw-studio.py fetch-ab VIDEO_ID [OUT_SUBDIR]
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

PROFILE = Path(__file__).parent / "pw-profile"
DEFAULT_OUTDIR = Path.home() / "Desktop/Cowork/media-impact-lab/screenshots"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def ctx(p, headless: bool):
    PROFILE.mkdir(parents=True, exist_ok=True)
    return p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE),
        headless=headless,
        viewport={"width": 1440, "height": 900},
        user_agent=UA,
        args=["--disable-blink-features=AutomationControlled"],
    )


def is_logged_in(page) -> bool:
    try:
        page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        url = page.url
        if "accounts.google.com" in url or "/signin" in url:
            return False
        # Studio dashboard URL contains /channel/
        return "/channel/" in url or page.locator("ytcp-navigation-drawer").count() > 0
    except Exception:
        return False


def cmd_login():
    print(f"Opening headful browser. Profile: {PROFILE}")
    with sync_playwright() as p:
        context = ctx(p, headless=False)
        page = context.new_page()
        page.goto("https://studio.youtube.com/")
        print("A browser window should have opened.")
        print("→ Sign into the Google account that manages EO Global.")
        print("→ Wait until you see YouTube Studio dashboard.")
        print("→ Script will auto-detect login and close the browser.")
        print("Polling for login (timeout 30 min)...")

        deadline = time.time() + 1800
        while time.time() < deadline:
            url = page.url
            if "studio.youtube.com/channel/" in url:
                print(f"✓ Logged in. URL: {url}")
                time.sleep(2)
                context.close()
                return
            time.sleep(3)
        print("✗ Timed out waiting for login.", file=sys.stderr)
        context.close()
        sys.exit(1)


def parse_number(txt: str):
    """Parse '12.4K' / '1,101' / '5.4%' / '57.4' → number."""
    if not txt:
        return None
    s = txt.strip().replace(",", "")
    m = re.match(r"^([0-9.]+)\s*([KMB%])?", s)
    if not m:
        return None
    val = float(m.group(1))
    mul = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get(m.group(2) or "", 1)
    return val * mul


def scrape_reach(page, outdir: Path, prefix: str) -> dict:
    """Reach tab: Impressions, CTR, Views, Unique viewers, traffic sources."""
    url = "https://studio.youtube.com/video/{vid}/analytics/tab-reach_viewers/period-default"
    data: dict = {"tab": "reach"}
    page.wait_for_load_state("networkidle", timeout=45000)
    time.sleep(5)
    page.screenshot(path=str(outdir / f"{prefix}_reach.png"), full_page=True)

    text = page.inner_text("body")
    # Metric cards — rely on label proximity
    for label, key in [
        ("Impressions", "impressions"),
        ("Impressions click-through rate", "ctr"),
        ("Views", "views"),
        ("Unique viewers", "unique_viewers"),
    ]:
        m = re.search(rf"{re.escape(label)}\s*\n?\s*([0-9.,]+\s*[KMB]?%?)", text)
        if m:
            data[key] = m.group(1).strip()
            data[f"{key}_num"] = parse_number(m.group(1))
    return data


def scrape_overview(page, outdir: Path, prefix: str) -> dict:
    page.wait_for_load_state("networkidle", timeout=45000)
    time.sleep(5)
    page.screenshot(path=str(outdir / f"{prefix}_overview.png"), full_page=True)
    text = page.inner_text("body")
    data: dict = {"tab": "overview"}
    for label, key in [
        ("Views", "views"),
        ("Watch time (hours)", "watch_time_hours"),
        ("Subscribers", "subscribers"),
    ]:
        m = re.search(rf"{re.escape(label)}\s*\n?\s*([0-9.,]+\s*[KMB]?)", text)
        if m:
            data[key] = m.group(1).strip()
            data[f"{key}_num"] = parse_number(m.group(1))
    # Realtime
    m = re.search(r"Realtime.*?\n?\s*([0-9.,]+)\s*\n?Views", text, re.DOTALL)
    if m:
        data["realtime_views"] = m.group(1).strip()
    # Traffic sources summary card
    traffic = {}
    for line in text.split("\n"):
        m = re.match(r"(Browse features|Suggested videos|YouTube search|External|Notifications|Direct or unknown|Other YouTube features)\s*([0-9.]+)%", line.strip())
        if m:
            traffic[m.group(1)] = float(m.group(2))
    if traffic:
        data["traffic_sources_pct"] = traffic
    return data


def scrape_engagement(page, outdir: Path, prefix: str) -> dict:
    page.wait_for_load_state("networkidle", timeout=45000)
    time.sleep(5)
    page.screenshot(path=str(outdir / f"{prefix}_engagement.png"), full_page=True)
    text = page.inner_text("body")
    data: dict = {"tab": "engagement"}
    for label, key in [
        ("Watch time (hours)", "watch_time_hours"),
        ("Average view duration", "avg_view_duration"),
    ]:
        m = re.search(rf"{re.escape(label)}\s*\n?\s*([0-9.:,]+\s*[KMB]?)", text)
        if m:
            data[key] = m.group(1).strip()
    return data


def scrape_audience(page, outdir: Path, prefix: str) -> dict:
    page.wait_for_load_state("networkidle", timeout=45000)
    time.sleep(5)
    page.screenshot(path=str(outdir / f"{prefix}_audience.png"), full_page=True)
    return {"tab": "audience", "screenshot": f"{prefix}_audience.png"}


def scrape_ab_test(page, vid: str, outdir: Path, prefix: str) -> dict:
    """Edit page → click A/B Testing → capture modal."""
    page.goto(f"https://studio.youtube.com/video/{vid}/edit", wait_until="domcontentloaded", timeout=45000)
    time.sleep(5)
    data: dict = {"tab": "ab_test"}
    try:
        btn = page.get_by_text(re.compile(r"A/B Test", re.I)).first
        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        time.sleep(3)
        page.screenshot(path=str(outdir / f"{prefix}_ab_test.png"), full_page=True)
        text = page.inner_text("body")
        # Extract watch time shares — e.g., "64.3%" and "35.7%"
        shares = re.findall(r"([0-9]{1,2}\.[0-9])%\s*Watch time share", text)
        if shares:
            data["watch_time_shares"] = [float(s) for s in shares]
        # Extract remaining time — "13 days 18 hours"
        m = re.search(r"Estimated time remaining[:\s]+(\d+\s*days?\s*\d+\s*hours?)", text, re.I)
        if m:
            data["time_remaining"] = m.group(1)
        status = re.search(r"Test\s+(running|completed)", text, re.I)
        if status:
            data["status"] = status.group(1).lower()
    except Exception as e:
        data["error"] = str(e)
    return data


def cmd_fetch(vid: str, subdir: str):
    outdir = DEFAULT_OUTDIR / subdir
    outdir.mkdir(parents=True, exist_ok=True)
    results = {"video_id": vid, "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S %Z")}

    # Google distinguishes headful vs headless sessions in its fingerprint
    # check, so cookies saved by headful `login` aren't valid in headless mode.
    # Use headful fetch too — brief window flash is acceptable trade for
    # not requiring a second login.
    with sync_playwright() as p:
        context = ctx(p, headless=False)
        page = context.new_page()

        # Quick auth check — wait for Studio URL to settle after any redirects
        page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=30000)
        for _ in range(10):
            time.sleep(1)
            if "studio.youtube.com/channel/" in page.url:
                break
        if "studio.youtube.com/channel/" not in page.url:
            print(f"ERROR: session not logged in (url={page.url}). Run: python3 pw-studio.py login", file=sys.stderr)
            page.screenshot(path="/tmp/pw-auth-fail.png")
            print("Debug screenshot: /tmp/pw-auth-fail.png", file=sys.stderr)
            context.close()
            sys.exit(2)

        prefix = subdir.replace("/", "_")

        # Reach
        try:
            page.goto(f"https://studio.youtube.com/video/{vid}/analytics/tab-reach_viewers/period-default",
                      wait_until="domcontentloaded", timeout=45000)
            results["reach"] = scrape_reach(page, outdir, prefix)
        except Exception as e:
            results["reach"] = {"error": str(e)}

        # Overview
        try:
            page.goto(f"https://studio.youtube.com/video/{vid}/analytics/tab-overview/period-default",
                      wait_until="domcontentloaded", timeout=45000)
            results["overview"] = scrape_overview(page, outdir, prefix)
        except Exception as e:
            results["overview"] = {"error": str(e)}

        # Engagement
        try:
            page.goto(f"https://studio.youtube.com/video/{vid}/analytics/tab-engagement/period-default",
                      wait_until="domcontentloaded", timeout=45000)
            results["engagement"] = scrape_engagement(page, outdir, prefix)
        except Exception as e:
            results["engagement"] = {"error": str(e)}

        # Audience (retention)
        try:
            page.goto(f"https://studio.youtube.com/video/{vid}/analytics/tab-audience/period-default",
                      wait_until="domcontentloaded", timeout=45000)
            results["audience"] = scrape_audience(page, outdir, prefix)
        except Exception as e:
            results["audience"] = {"error": str(e)}

        # A/B Test
        try:
            results["ab_test"] = scrape_ab_test(page, vid, outdir, prefix)
        except Exception as e:
            results["ab_test"] = {"error": str(e)}

        context.close()

    jsonpath = outdir / f"{prefix}_data.json"
    jsonpath.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\nScreenshots + data saved to: {outdir}")


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "login":
        cmd_login()
    elif mode == "fetch":
        if len(sys.argv) < 3:
            print("Usage: fetch VIDEO_ID [OUT_SUBDIR]", file=sys.stderr)
            sys.exit(1)
        vid = sys.argv[2]
        subdir = sys.argv[3] if len(sys.argv) > 3 else f"video_{vid}"
        cmd_fetch(vid, subdir)
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
