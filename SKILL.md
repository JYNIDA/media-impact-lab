# Media Impact Lab: Hypothesis-Driven Video Performance Analysis

## Trigger
Use when: "impact lab", "media impact lab", "임팩트 랩", "발행 분석", "퍼포먼스 분석", "에피소드 분석", "가설 검증", "성과 분석"

## Overview

A per-episode experiment and analysis system. Measures full video impact: CTR, retention, subscriber conversion, watch time, traffic distribution.

**Core premise**: Title + Thumbnail + Intro = 1 Unit. Every publish tests a hypothesis about why that unit will (or won't) drive clicks, retention, and growth.

**Input surface**: Slack Canvas in `#gl-youtube-operations`

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

### Phase 2: HYPOTHESIZE (Slack Canvas)

Claude creates Canvas in `#gl-youtube-operations` via `slack_create_canvas`.

Producer fills in per A/B/C set:
- Title (exact)
- Thumbnail (describe visual: text, layout, colors)
- Intro flow (how intro connects)
- Hypothesis (free-form: WHY will this drive clicks AND retention?)
- Predicted CTR range
- Kill condition

---

### Phase 3: PUBLISH

Record in Canvas:
- Publish timestamp
- Sets live, A/B mode
- Last-minute changes

---

### Phase 4: MEASURE

#### Data Collection Methods

Two collection methods work together:

**1. YouTube Analytics API** -- views, watch time, subs, engagement, retention
**2. Studio Browse** -- Impressions, CTR, traffic source %, A/B thumbnail data

Studio Browse uses a headless browser (gstack browse) with imported Google cookies to read data directly from YouTube Studio UI. This bypasses YouTube's API restrictions on Impressions/CTR.

**Prerequisites**: Each team member must complete a one-time browser auth setup (see "Browser Auth Setup" section below).

#### Studio Browse Flow

**Reach tab (Impressions, CTR, traffic sources):**
```
1. goto "https://studio.youtube.com/video/{VIDEO_ID}/analytics/tab-reach_viewers/period-default"
2. Wait 3s for data load
3. Screenshot → save as {guest}_ep{N}_reach_H{hour}.png
4. Read: Impressions, CTR, unique viewers
5. Read traffic source breakdown (Browse %, Suggested %, Search %, External %)
```

**A/B Test report (Watch Time Share):**
```
1. goto "https://studio.youtube.com/video/{VIDEO_ID}/edit"
2. Click "A/B Testing" button
3. Wait 2s for modal load
4. Screenshot → save as {guest}_ep{N}_ab_test.png (REQUIRED for every report)
5. Read: Watch time share % per thumbnail, test status (running/completed)
6. If "Test running..." → record status + estimated time remaining
7. If completed → record winner + Watch time share per set
```

If browse session is expired (Google login page appears), post Slack alert:
```
Browse session expired. Run /setup-browser-cookies + handoff to re-authenticate.
```

#### Hourly Tracking (First 24h)

Poll YouTube Analytics API hourly. Cumulative totals minus previous = delta.
Poll Studio Browse for CTR + Impressions alongside API calls.

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
- A/B thumbnail results: Studio UI only → now collected via Studio Browse
- CTR by traffic source: unreliable via API → now collected via Studio Browse

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
If Studio Browse fails (cookie expired, UI layout changed), producer fills Canvas measurement table manually.

#### Slack Alert (after Auto metrics are filled)

After `impact lab measure` fills both API + Browse data in the Canvas, post this alert to `#gl-youtube-operations`:

```
D+7 metrics collected for [Episode Name].
Canvas updated: [canvas link]

All metrics auto-collected (API + Studio Browse):
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
- Write into Slack Canvas via `slack_update_canvas`
- Save archive: `~/Desktop/Cowork/media-impact-lab/{file}.md`
- Generate chart: `{file}_chart.html` (dark theme, Chart.js, standalone)
- Post summary to `#gl-youtube-operations`

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
- **Canvas + discussion**: `#gl-youtube-operations`
- **Fallback**: `#team-gl-media`

---

## For Team Members

### What You Do

1. **One-time setup**: Run `/setup-browser-cookies` + `handoff` to authenticate (see Browser Auth Setup below)
2. **Before publish**: Fill Set A/B/C in the Slack Canvas (title, thumbnail description, intro flow, hypothesis)
3. **D+7**: Claude auto-collects everything (API + Studio Browse). No manual data entry needed.
4. **Read the report**: Claude auto-generates analysis with screenshots attached. Review lessons and apply to next episode.

### What Claude Does

1. Creates Canvas and shares link in `#gl-youtube-operations`
2. Collects metrics via YouTube API (views, watch time, subs, engagement, retention)
3. Collects metrics via Studio Browse (Impressions, CTR, traffic sources, A/B status)
4. Tracks hourly CTR via Studio Browse until stabilized
5. Auto-generates Week 1 Report (D+7) and Final Report (D+14)
6. Calculates derived metrics (sub conversion rate, impact scorecard)

### Auto vs. Manual Data

| Source | Metrics | How |
|--------|---------|-----|
| **Auto** (YouTube API) | Views, avg duration, avg view %, subs gained/lost, likes, comments, shares, retention curve | API call |
| **Auto** (Studio Browse) | Impressions, CTR, traffic source %, A/B Watch Time Share, unique viewers | Headless browser reads YouTube Studio UI |

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
- **Limitation**: Impressions/CTR not available via API. YouTube intentionally blocks this. Collected via Studio Browse (headless browser accessing Studio UI).
