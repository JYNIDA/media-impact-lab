# Media Impact Lab: Hypothesis-Driven Video Performance Analysis

## Trigger
Use when: "impact lab", "media impact lab", "임팩트 랩", "발행 분석", "퍼포먼스 분석", "에피소드 분석", "가설 검증", "성과 분석"

## Overview

A per-episode experiment and analysis system. Measures full video impact: CTR, retention, subscriber conversion, watch time, traffic distribution.

**Core premise**: Title + Thumbnail + Intro = 1 Unit. Every publish tests a hypothesis about why that unit will (or won't) drive clicks, retention, and growth.

**Input surface**: Notion page (one page per episode: hypothesis + report)
**Guide**: Slack Canvas in `#gl-youtube-operations` (usage guide for team, stays as-is)

## Output

`~/Desktop/Cowork/media-impact-lab/`

- `{guest_name}_ep{N}.md` -- archive (e.g. `rem_koning_ep5.md`)
- `{guest_name}_ep{N}_chart.html` -- performance dashboard
- `cross_episode_trends.md` (after 3+ episodes)
- `pattern_library.md`

## Workflow

```
"impact lab start [Episode Title] [Guest Name]"
  → Claude creates Canvas in #gl-youtube-operations
  → Producer fills in Set A/B/C (title, thumbnail, intro, hypothesis)

"impact lab publish"
  → Claude reads Canvas, records publish time
  → Starts hourly CTR tracking

Hourly tracking until CTR stabilizes
  → Claude posts stabilization alert in Slack

D+7: Claude auto-generates Week 1 Report
  → Writes into Canvas + archives MD + chart HTML
  → Posts summary to Slack

D+14: Claude auto-generates Final Report
  → Updates Canvas with final numbers
  → Pattern library update
```

---

## Phases

### Phase 1: LEARN

**Input**: Full interview transcript + final video script (with intro)

**Extract:**
1. **Content DNA** (3-5 sentences): what makes this episode unique
2. **Hook Inventory**: top 5-8 moments with exact quotes
3. **Intro Analysis**: opening line, promise, tension, title/thumbnail connection
4. **One-Line Test**: single sentence for why someone should click

---

### Phase 2: HYPOTHESIZE (Notion)

Claude creates a row in the **2Q database** via `notion-create-pages` with `data_source_id`.

- **Data source ID**: `33874768-ec37-80e4-9c37-000bea9f211e` (2Q table)
- **Name format**: `[TTM] ep.N - Guest Name` / `[FF] Company - Founder Name`
- No "Media Impact Lab" prefix in the title -- episode name only

**Page content -- top section is the hypothesis (producer fills):**

```
## 1. 가설

### Set A
- **제목**: (정확한 제목)
- **썸네일**: (이미지 설명: 텍스트, 레이아웃, 색상, 표정)
- **인트로 흐름**: (인트로가 제목+썸네일과 어떻게 연결되는지)
- **가설**: (왜 이 세트가 클릭 + 리텐션을 끌 것인지. 심리적 트리거, 타겟 시청자)
- **예상 CTR**: __% - __%
- **킬 조건**: (이 수치 이하면 실패로 판정)

### Set B
(동일 구조)

### Set C (선택)
(동일 구조)

### 발행 전 메모
(타이밍, 경쟁 영상, 시청자 분위기)

## 2. 발행 로그
(Claude가 채움)

## 3. 보고서
(Claude가 D+7, D+14에 자동 작성 -- 가설 검증 결과가 여기에)
```

The hypothesis section is the core. The rest of the page is filled by Claude.

After creating the DB row:
1. Search `#request-썸네일` for guest name -- if thumbnail thread exists, include permalink in Slack message
2. Post link to `#gl-youtube-operations` via Slack (bot token, not MCP)

**Notion parent page**: `33874768ec3780ccb297e2e3f0bb208a` (Media Impact Lab)
**2Q Data source ID**: `33874768-ec37-80e4-9c37-000bea9f211e`
**Guide page**: `33874768ec3780259b7ff183bb3a7e10`

---

### Phase 3: PUBLISH

Record in Notion page (section 2. 발행 로그):
- Thumbnail request thread link: auto-search `#request-썸네일` channel for guest name, attach Slack permalink
- Publish timestamp
- Sets live, A/B mode
- Last-minute changes

---

### Phase 4: MEASURE

#### Data Collection Methods

Two collection methods work together:

**1. YouTube Analytics API** -- whatever the API can return (views trend, watch time, subs, engagement, retention curve when available)
**2. Playwright Studio scraper (REQUIRED)** -- everything the API can't return: Impressions, CTR, traffic source %, A/B watch-time share, retention when API is delayed, any Studio-only panel

**Hard rule**: anything not available via YouTube Analytics API MUST be collected via the Playwright scraper at `~/.claude/skills/media-impact-lab/lib/pw-studio.py`. Do not fall back to manual Canvas entry, do not skip Studio data, do not try `gstack browse` / `fetch-reach.sh` (those are deprecated). If Playwright session is not logged in, run the login flow below — never silently degrade to "API only".

#### Playwright Studio Flow

```bash
PY=/Users/jiyooneo/.vit/venv/bin/python3
SCRAPER=~/.claude/skills/media-impact-lab/lib/pw-studio.py

# First-time / session-expired login (opens headful Chromium, user signs in once)
$PY $SCRAPER login

# Fetch all Studio tabs for a video — Reach, Overview, Engagement, Audience, A/B modal
$PY $SCRAPER fetch "$VIDEO_ID" "{guest}_ep{N}"
# → screenshots + {guest}_ep{N}_data.json in ~/Desktop/Cowork/media-impact-lab/screenshots/{guest}_ep{N}/
```

Persistent Chromium profile lives at `~/.claude/skills/media-impact-lab/lib/pw-profile/` (gitignored — contains your Google session). Cookies persist across runs, typically months. When they eventually expire, the fetch command prints `ERROR: session not logged in` — re-run `login` mode and the scrape keeps working.

#### Hourly Tracking (First 24h)

Poll YouTube Analytics API hourly. Cumulative totals minus previous = delta.
Poll Playwright scraper (`pw-studio.py fetch`) for CTR + Impressions + A/B share alongside API calls.

**Adaptive stop**: CTR variance < 0.3% for 3 consecutive hours = stabilized. Post Slack alert.

#### D+7: Week 1 Checkpoint (auto-report trigger)

| Category | Metrics |
|----------|---------|
| **Click** | Impressions, CTR |
| **Watch** | Views, avg view duration, avg view %, minutes watched |
| **Growth** | Subs gained, subs lost, net subs, sub conversion per 1K views |
| **Engagement** | Likes, comments, shares |
| **Distribution** | Browse %, Suggested %, Search %, External % |
| **Retention** | Retention curve, first 30s retention, intro-to-body drop |
| **A/B Result** | Winner set, Watch Time Share per set |

**After D+7 data is collected, Claude auto-generates the Week 1 Report.**

#### D+14: Final Checkpoint

All D+7 metrics updated PLUS:
- Impression trend: still growing or dying?
- Suggested feed: top 5 "content suggesting this video"
- Final A/B winner confirmation
- Evergreen vs. spike-and-die verdict

**After D+14, Claude auto-generates the Final Report.**

#### YouTube Analytics API

**Endpoint**: `GET https://youtubeanalytics.googleapis.com/v2/reports`
**Scope**: `https://www.googleapis.com/auth/yt-analytics.readonly`

| Metric | API field |
|--------|-----------|
| Impressions | `impressions` |
| CTR | `impressionClickThroughRate` |
| Views | `views` |
| Avg view duration | `averageViewDuration` |
| Avg view % | `averageViewPercentage` |
| Subs gained | `subscribersGained` |
| Subs lost | `subscribersLost` |
| Watch time | `estimatedMinutesWatched` |
| Likes | `likes` |
| Comments | `comments` |
| Shares | `shares` |

**Retention curve:**
```
dimensions=elapsedVideoTimeRatio
metrics=audienceWatchRatio,relativeRetentionPerformance
filters=video==VIDEO_ID
```

**API limitations:**
- Hourly = cumulative polling trick (native = daily)
- A/B thumbnail results: Studio UI only → collected via Playwright scraper
- CTR by traffic source: unreliable via API → collected via Playwright scraper

#### Screenshots (attached to every report)

All screenshots saved to `~/Desktop/Cowork/media-impact-lab/screenshots/{guest}_ep{N}/`:

| Screenshot | When | Why |
|-----------|------|-----|
| `reach_H{hour}.png` | Every hourly poll | CTR graph trajectory over time |
| `reach_D7.png` | D+7 checkpoint | CTR + Impressions + traffic sources at D+7 |
| `reach_D14.png` | D+14 checkpoint | Final CTR + Impressions state |
| `ab_test.png` | D+7 and D+14 | **REQUIRED** -- shows which thumbnail + title won with Watch Time Share % |
| `retention_D7.png` | D+7 checkpoint | Retention curve shape |

The A/B test screenshot is the most critical -- it visually shows which thumbnail image and title combination drove more watch time, which numbers alone can't convey.

#### Manual Fallback
If the Playwright scraper fails (session expired, UI layout changed), **do not fall back to manual entry**. Options in order:
1. Re-run `pw-studio.py login` to refresh the session
2. If UI selector broke, update `pw-studio.py` (DOM changed) — look at the saved screenshot to confirm what rendered
3. Only if both fail, flag to user and hold the report until scraper works

#### Slack Alert (after Auto metrics are filled)

After `impact lab measure` fills both API + Browse data in the Canvas, post this alert to `#gl-youtube-operations`:

```
D+7 metrics collected for [Episode Name].
Canvas updated: [canvas link]

All metrics auto-collected (API + Playwright scraper):
✓ Views, watch time, subs, engagement, retention
✓ Impressions, CTR, traffic sources
✓ A/B thumbnail Watch Time Share
✓ Screenshots: CTR trajectory, A/B test report, retention curve

"impact lab report" 실행하면 리포트 자동 생성됩니다.
```

---

### Phase 5: REPORT (Auto-generated)

Two reports, auto-triggered:

#### Week 1 Report (D+7)

**5.1 The Experiment**: One paragraph summary.

**5.2 Hypothesis vs. Reality**:

| Set | Hypothesis | Predicted CTR | Actual CTR | Verdict |
|-----|-----------|:---:|:---:|:---:|
| A | | | | CONFIRMED / REJECTED / INCONCLUSIVE |

**5.3 Impact Scorecard**:

| Dimension | Score | EO Benchmark | Verdict |
|-----------|:-----:|:------------:|:-------:|
| CTR | X% | ~5% | |
| Avg view % | X% | ~30% | |
| Sub conversion / 1K views | X | TBD | |
| Engagement rate | X% | TBD | |

**5.4 CTR Trajectory**: Hourly curve shape, stabilization point, what it means.
- Attach: `reach_H*.png` screenshots showing CTR graph progression over time

**5.5 A/B Test Result**: Winner thumbnail + Watch Time Share per set.
- Attach: `ab_test.png` screenshot (REQUIRED -- shows thumbnail images + title + Watch Time Share)

**5.6 Retention Analysis**: First 30s, intro-to-body drop, key drop-offs, relative vs YouTube avg.
- Attach: `retention_D7.png` screenshot

**5.7 Growth Analysis**: Net subs, conversion rate, traffic source mix.

**5.8 Lessons Learned**: What worked, what didn't, surprises.

**5.9 Next Episode Application**: 2-3 concrete things to try next.

#### Final Report (D+14)

Updates Week 1 Report with:
- **5.9 Two-Week Trajectory**: Is the video still getting pushed or dying?
- **5.10 Pattern Update**: New/confirmed/retired patterns for pattern_library.md

#### Report Output
- Write into same Notion page (section 3. 보고서) via `notion-update-page` -- hypothesis validation at the top
- Save archive: `~/Desktop/Cowork/media-impact-lab/{file}.md`
- Post summary to `#gl-youtube-operations`
- **Chart HTML**: only generated on request (`{file}_chart.html`, dark theme, Chart.js, CTR/watch time/sub conversion/A/B test focus)

---

## Slack Canvas Template

Created by `impact lab start`:

**Title**: `Media Impact Lab: [Series] EP[N] -- [Guest Name]`

**Sections**:
1. HYPOTHESIS -- Set A/B/C (producer fills)
2. PUBLISH LOG -- timestamp, sets live
3. MEASUREMENT -- hourly table + D+7 + D+14
4. WEEK 1 REPORT -- Claude auto-generates at D+7
5. FINAL REPORT -- Claude auto-generates at D+14

---

## Commands

- `impact lab start [Episode Title] [Guest Name]` -- Create Canvas + LEARN
- `impact lab publish` -- Read Canvas, start tracking
- `impact lab measure` -- Collect data (hourly or checkpoint)
- `impact lab report` -- Generate report (auto at D+7, D+14)
- `impact lab trends` -- Cross-episode analysis (3+ episodes)

---

## Slack
- **Channel**: `#gl-youtube-operations` (channel ID: `C09UQSSK40M`)
- **Fallback**: `#team-gl-media`
- **Bot Token** (Block Kit, editable): stored in `~/.claude/skills/weekly-meeting/config/config.json` under `slack.impact_lab_bot_token`
- **Webhook** (legacy, non-editable): stored in config under `slack.impact_lab_webhook`
- **Thumbnail requests**: `#request-썸네일` (channel ID: `C033Z5AC3FA`)

### Slack Message Format — HARD REQUIREMENTS

**Two non-negotiable rules (apply to every Impact Lab Slack post, regardless of who is running this skill):**

1. **Identity: always post as the Media Impact Lab bot, never as a user.**
   - Required path: `curl` against `https://slack.com/api/chat.postMessage` with `Authorization: Bearer $BOT_TOKEN` (bot token from config).
   - Forbidden paths: MCP Slack tools (`mcp__claude_ai_Slack__slack_send_message` or equivalents), Slack desktop app typing, webhook URL when bot token is available.
   - Why: The bot identity is the team's visual signal that this is an automated D+N report. A post from a user account reads as a hand-typed summary and breaks that signal. Bot-posted messages can also be re-edited programmatically; user-posted messages cannot.

2. **Length and content: terse, numbers-led. No prose lessons in Slack.**
   - Target: ~10 to 15 short lines, readable in one glance.
   - Always include (in this order): (a) header `[Series] Guest Name — D+N timestamp`, (b) core numeric snapshot in a single pipe-delimited line, (c) CTR trajectory with arrows, (d) A/B test state (variants + winner or % lead), (e) Notion full-report link + thumbnail thread link.
   - Never include in Slack: multi-paragraph lessons, pre-publish iteration log, full hypothesis tables, "what to watch at D+7" prose. Those belong in the Notion page only.
   - Why: The Slack post is an alert and a link to the full report. Details belong in Notion. A 30-line Slack summary competes with the Notion page and buries the numbers.

### Recommended Terse Template (target format, confirmed on QFEX 2026-04-21)

Time-frame header must be accurate. Use `Publish Day, H+N` on upload day; switch to `D+1`, `D+7`, `D+14` only once we've actually crossed that boundary. Never label a same-day report as D+1.

```
:test_tube: [Series] Guest Name — Publish Day, H+N (YYYY-MM-DD HH:MM PDT)
  or
:test_tube: [Series] Guest Name — D+N (YYYY-MM-DD HH:MM PDT)

Views X.XK | Realtime X | Watch X.Xh (±X.Xh vs usual) | AVD M:SS (±M:SS) | Like XX.X% (ch avg XX.X%)

CTR trajectory (over N active hours, N manual thumbnail swaps):
X.X% → X.X% → X.X%

Native title A/B — XX% [A|B] wins, significance in ~Nd:
• A: "..." (origin)
• B: "..." (origin)

Lessons so far:
• 2-3 short bullets, one line each. No prose paragraphs.
• Grounded in what today's data actually shows, not generic advice.

Full report: <NOTION_URL|Notion> | Thumbnail iter: <SLACK_THREAD_URL|thread>
```

### Bot-Token Curl Pattern

```bash
TOKEN=$(python3 -c "import json; print(json.load(open('/Users/jiyooneo/.claude/skills/weekly-meeting/config/config.json'))['slack']['impact_lab_bot_token'])")
curl -s -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d @- <<'JSON'
{
  "channel": "C09UQSSK40M",
  "blocks": [
    {"type": "section", "text": {"type": "mrkdwn", "text": ":test_tube: *[Founder Focused] Guest Name — D+1 (2026-04-21 14:35 PDT)*"}},
    {"type": "section", "text": {"type": "mrkdwn", "text": "Views 2.8K | Realtime 153 | Watch 135.8h (−74.2h) | AVD 2:56 (−0:32)"}},
    {"type": "section", "text": {"type": "mrkdwn", "text": "CTR trajectory (5h, 4 manual swaps): 4.4% → 4.6% → 4.76%"}},
    {"type": "section", "text": {"type": "mrkdwn", "text": "*Native title A/B — 49% B wins, significance ~3d:*\n• A: \"Why This Ex-Quant Quit a $10B/Day Job...\" (Set D)\n• B: \"I Quit My 7-Figure Job on Wall Street // Here's Why\" (Jay iter)"}},
    {"type": "context", "elements": [{"type": "mrkdwn", "text": "<NOTION_URL|Full report> | <THREAD_URL|Thumbnail thread>"}]}
  ]
}
JSON
```

Header format for the first section: `[Series Name] Guest/Company - Founder Name`
Examples: `[Founder Focused] QFEX - Annanay Kapila`, `[The Thinking Mode] EP7 - Bharat Chandar`

---

## For Team Members

### What You Do

1. **One-time setup**: Run `/setup-browser-cookies` + `handoff` to authenticate (see Browser Auth Setup below)
2. **Before publish**: Fill Set A/B/C in the Slack Canvas (title, thumbnail description, intro flow, hypothesis)
3. **D+7**: Claude auto-collects everything (API + Playwright scraper). No manual data entry needed.
4. **Read the report**: Claude auto-generates analysis with screenshots attached. Review lessons and apply to next episode.

### What Claude Does

1. Creates Canvas and shares link in `#gl-youtube-operations`
2. Collects metrics via YouTube API (views, watch time, subs, engagement, retention)
3. Collects metrics via Playwright scraper (Impressions, CTR, traffic sources, A/B status, retention when API delays)
4. Tracks hourly CTR via Playwright scraper until stabilized
5. Auto-generates Week 1 Report (D+7) and Final Report (D+14)
6. Calculates derived metrics (sub conversion rate, impact scorecard)

### Auto vs. Manual Data

| Source | Metrics | How |
|--------|---------|-----|
| **Auto** (YouTube API) | Views, avg duration, avg view %, subs gained/lost, likes, comments, shares, retention curve | API call |
| **Auto** (Playwright scraper) | Impressions, CTR, traffic source %, A/B Watch Time Share, unique viewers, retention curve (fallback) | Headful Chromium with persistent Google session, reads Studio UI |

All metrics are now fully automated. No manual data entry required.

### Browser Auth Setup (One-Time per Team Member)

Each team member needs to authenticate once so Claude can access YouTube Studio on their behalf:

1. Run `/setup-browser-cookies` in Claude Code
2. In the picker UI, import `youtube.com` + `google.com` cookies from Chrome
3. If Google asks for password (cookie session mismatch), Claude runs `handoff`
4. A browser window opens -- log into your Google account with YouTube Studio access
5. Tell Claude "done" -- Claude runs `resume` and verifies Studio access
6. Cookies last ~2 weeks. Re-run this setup when session expires.

### How to Write a Good Hypothesis

Write 1-2 sentences about WHY this set will drive clicks AND retention. Examples:
- "Credential authority hook. Harvard + experimental data combo triggers curiosity in our core audience."
- "From X to Y transformation structure. Proven CTR pattern, testing with academic guest for first time."
- "Controversy angle. Title challenges a widely held belief, should trigger debate in comments."

There's no wrong answer. The point is to make your reasoning explicit so we can verify it after the data comes in.

---

## API Setup (Admin Only)

Config: `~/.claude/skills/weekly-meeting/config/config.json`

YouTube Analytics API:
- **Enabled**: Yes (2026-04-02)
- **OAuth consent screen**: External
- **Scopes**: `yt-analytics.readonly`, `yt-analytics-monetary.readonly`, `youtube.readonly`
- **Channels**: EO Global + EO Korea (both authenticated)
- **Limitation**: Impressions/CTR not available via API. YouTube intentionally blocks this. Collected via Playwright scraper (`pw-studio.py`) which drives a real Chromium against the Studio UI.
