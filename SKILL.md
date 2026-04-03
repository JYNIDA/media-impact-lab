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

#### Hourly Tracking (First 24h)

Poll YouTube Analytics API hourly. Cumulative totals minus previous = delta.

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
- A/B thumbnail results: Studio UI only
- CTR by traffic source: unreliable via API

#### Manual Fallback
Producer fills Canvas measurement table. Captures API-exclusive data: A/B Watch Time Share, traffic source CTR.

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

**5.5 Retention Analysis**: First 30s, intro-to-body drop, key drop-offs, relative vs YouTube avg.

**5.6 Growth Analysis**: Net subs, conversion rate, traffic source mix.

**5.7 Lessons Learned**: What worked, what didn't, surprises.

**5.8 Next Episode Application**: 2-3 concrete things to try next.

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

1. **Before publish**: Fill Set A/B/C in the Slack Canvas (title, thumbnail description, intro flow, hypothesis)
2. **After publish**: Record hourly CTR from YouTube Studio until it stabilizes
3. **D+7**: Claude sends a Slack alert. Fill in Manual items from Studio (Impressions, CTR, traffic sources, A/B results)
4. **Read the report**: Claude auto-generates analysis. Review lessons and apply to next episode.

### What Claude Does

1. Creates Canvas and shares link in `#gl-youtube-operations`
2. Collects D+7 Auto metrics via YouTube API (views, watch time, subs, engagement, retention)
3. Sends Slack alert when Manual items are needed
4. Auto-generates Week 1 Report (D+7) and Final Report (D+14)
5. Calculates derived metrics (sub conversion rate, impact scorecard)

### Auto vs. Manual Data

| Source | Metrics | Why |
|--------|---------|-----|
| **Auto** (YouTube API) | Views, avg duration, avg view %, subs gained/lost, likes, comments, shares, retention curve | API provides these |
| **Manual** (YouTube Studio) | Impressions, CTR, A/B Watch Time Share, A/B winner, traffic source % | YouTube blocks these from API |

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
- **Limitation**: Impressions/CTR not available via API. YouTube intentionally blocks this. Use Studio UI.
