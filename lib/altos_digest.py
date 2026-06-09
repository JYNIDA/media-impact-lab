#!/usr/bin/env python3
"""Daily Altos Ventures news digest -> Slack DM.

Gathers the last ~24-48h of Altos Ventures news via Claude's web search tool,
formats a Korean Slack message, and DMs it to the configured user. Covers:
press coverage, funding/investment news, official posts/SNS, and
portfolio-company news.

Credentials are read from the environment first (for GitHub Actions), then
fall back to config/config.json for local runs:

    ANTHROPIC_API_KEY   Claude API key
    SLACK_BOT_TOKEN     Slack bot token (needs chat:write, im:write)
    SLACK_USER_ID       Slack member ID to DM (e.g. U0XXXXXXX)

Usage:
    python3 altos_digest.py            # gather news + post to Slack DM
    python3 altos_digest.py --dry-run  # print the digest, do not post
"""

import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

MODEL = "claude-opus-4-8"

# Local config fallback (same file the rest of the skill uses).
CFG_CANDIDATES = [
    Path(__file__).resolve().parent.parent / "config" / "config.json",
    Path.home() / ".claude/skills/media-impact-lab/config/config.json",
]


def _load_cfg():
    for path in CFG_CANDIDATES:
        if path.exists():
            return json.loads(path.read_text())
    return {}


def _resolve_creds():
    cfg = _load_cfg()
    slack = cfg.get("slack") or {}
    anthropic_cfg = cfg.get("anthropic") or {}
    raw = {
        "api_key": os.environ.get("ANTHROPIC_API_KEY") or anthropic_cfg.get("api_key"),
        "bot_token": os.environ.get("SLACK_BOT_TOKEN") or slack.get("impact_lab_bot_token"),
        "user_id": os.environ.get("SLACK_USER_ID") or slack.get("my_user_id"),
    }
    # Pasted secrets often carry a trailing newline/space, which is an invalid
    # HTTP header value — strip whitespace so credentials are always clean.
    return {k: v.strip() if isinstance(v, str) else v for k, v in raw.items()}


def generate_digest(api_key):
    """Run Claude with the web search tool and return a Slack-ready message."""
    import anthropic

    today = dt.date.today().isoformat()
    client = anthropic.Anthropic(api_key=api_key)

    system = (
        "너는 Altos Ventures 다큐멘터리 제작팀을 위한 리서치 어시스턴트야. Altos는 "
        "미국(실리콘밸리)과 한국에 걸친 VC라, 미국 소식과 한국 소식을 모두 챙겨야 해. "
        "web_search 도구로 최신 정보를 직접 찾아 사실을 확인한 뒤 정리해. 영어권(미국) "
        "매체도 적극적으로 검색하고, 핵심은 한국어로 옮겨 써.\n"
        "기사 선정 기준이 중요해: 단순 '누가 얼마 투자받았다' 식 단신은 빼고, 산업의 흐름·"
        "배경·전략·인물·생태계를 깊이 다루는 *기획/심층/분석/인터뷰* 기사를 우선해. "
        "다큐 기획에 영감을 줄 만한(VC 산업 구조, 장기투자 철학, 한미 크로스보더 투자, "
        "이민자·창업가 스토리, 한국 스타트업의 글로벌 진출 등) 콘텐츠를 골라.\n"
        "출력은 오직 Slack 메시지 본문만 — 서두/맺음말/메타설명 없이. "
        "Slack mrkdwn 형식을 사용해: 굵게는 *별표*, 링크는 <URL|제목>, 불릿은 • 로. "
        "각 항목은 한두 문장으로 핵심과 '왜 다큐에 유용한지'를 짚고, 출처 링크를 꼭 붙여."
    )

    prompt = (
        f"오늘은 {today}야. 최근 24~48시간 내 발행된 소식을 web_search로 조사해서 아래 "
        "섹션으로 정리해줘. 각 섹션 제목은 굵게 표시하고, 해당 기간에 마땅한 소식이 없는 "
        "섹션은 '• 특이사항 없음'으로 적어.\n\n"
        "1. *🎯 Altos Ventures 직접 소식* — Altos가 언급된 기사(미국/한국), 공식 발행물·"
        "블로그·LinkedIn·X, 주요 포트폴리오사(토스, 두나무, 하이퍼커넥트 등) 소식. "
        "Altos 자체 뉴스가 적은 날이 많으니 작은 소식이라도 찾아봐.\n"
        "2. *🇺🇸 US 스타트업·VC 씬 (기획·심층)* — 미국 벤처/스타트업 생태계를 다룬 기획·"
        "분석·인물·트렌드 기사 (TechCrunch, The Information, Axios, Bloomberg 등 포함).\n"
        "3. *🇰🇷 한국 스타트업·VC 씬 (기획·심층)* — 한국 벤처 생태계를 다룬 기획·분석·"
        "인물·트렌드 기사.\n"
        "4. *🎬 다큐 참고 — 트렌드/인물/이슈* — 위에 안 들어가지만 Altos 다큐 기획에 "
        "영감을 줄 만한 폭넓은 기획 콘텐츠(장기투자, 크로스보더, 창업가 서사 등).\n\n"
        "맨 위에 한 줄 제목을 넣어: '*🗞️ Altos & 스타트업·VC 데일리 — {date}*'.\n"
        "단순 펀딩 단신은 빼고 기획·심층 기사를 우선해. 추측하지 말고 검색으로 확인된 "
        "내용만, 정보가 적으면 솔직하게 적어."
    ).replace("{date}", today)

    tools = [{"type": "web_search_20260209", "name": "web_search"}]
    messages = [{"role": "user", "content": prompt}]

    # Server-side web search runs an internal loop; resume on pause_turn.
    for _ in range(10):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            system=system,
            tools=tools,
            messages=messages,
        )
        if resp.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": resp.content})
            continue
        break

    text = "\n".join(b.text for b in resp.content if b.type == "text").strip()
    if not text:
        raise SystemExit("ERROR: model returned no text content.")
    return text


def _slack_api(method, token, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://slack.com/api/{method}",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def post_dm(token, user_id, text):
    opened = _slack_api("conversations.open", token, {"users": user_id})
    if not opened.get("ok"):
        raise SystemExit(f"ERROR: conversations.open failed: {opened.get('error')}")
    channel = opened["channel"]["id"]
    res = _slack_api("chat.postMessage", token, {
        "channel": channel,
        "text": text,
        "unfurl_links": False,
        "unfurl_media": False,
    })
    if not res.get("ok"):
        raise SystemExit(f"ERROR: chat.postMessage failed: {res.get('error')}")
    print(f"Posted Altos Ventures digest to DM with {user_id} (channel {channel}).")


def main():
    dry_run = "--dry-run" in sys.argv
    creds = _resolve_creds()

    if not creds["api_key"]:
        raise SystemExit("ERROR: ANTHROPIC_API_KEY not set (env or config.json).")

    digest = generate_digest(creds["api_key"])

    if dry_run:
        print(digest)
        return

    if not creds["bot_token"] or not creds["user_id"]:
        raise SystemExit(
            "ERROR: SLACK_BOT_TOKEN / SLACK_USER_ID not set. "
            "Use --dry-run to preview without posting."
        )

    post_dm(creds["bot_token"], creds["user_id"], digest)


if __name__ == "__main__":
    main()
