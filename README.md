# YT Impact Lab

Hypothesis-driven video performance analysis for EO Global.

Every publish is an experiment. Record your hypothesis before publishing, track performance data, and get auto-generated reports that verify what worked and what didn't.

## Install

```bash
# Clone into your Claude Code skills directory
git clone https://github.com/JYNIDA/yt-impact-lab.git ~/.claude/skills/yt-impact-lab
```

After cloning, the skill is immediately available in Claude Code.

## Quick Start

```
impact lab start EP7 Guest Name
```

This creates a Slack Canvas in `#gl-youtube-operations` with the episode template. Fill in your hypotheses, publish, and Claude handles the rest.

## Commands

| Command | What it does |
|---------|-------------|
| `impact lab start EP7 Name` | Create Canvas + extract content DNA from script |
| `impact lab publish` | Read Canvas, record publish time, start tracking |
| `impact lab measure` | Collect D+7 or D+14 data (auto + manual) |
| `impact lab report` | Generate analysis report |
| `impact lab trends` | Cross-episode analysis (3+ episodes) |

## Workflow

```
1. impact lab start    -->  Canvas created, link shared in Slack
2. Producer fills      -->  Set A/B/C hypotheses in Canvas
3. impact lab publish  -->  Publish logged, tracking starts
4. Hourly CTR          -->  Producer records from YouTube Studio
5. D+7                 -->  Claude auto-fills API data + alerts for manual items
6. impact lab report   -->  Week 1 Report auto-generated
7. D+14                -->  Final Report + pattern library update
```

## What's Auto vs. Manual

| Auto (YouTube API) | Manual (YouTube Studio) |
|---|---|
| Views | Impressions |
| Avg view duration | CTR |
| Avg view % | A/B test results |
| Subs gained/lost | Traffic source % |
| Likes, Comments, Shares | |
| Retention curve | |

YouTube does not provide Impressions/CTR data via API. This is an intentional restriction by YouTube.

## Requirements

- Claude Code with Slack MCP connected
- YouTube Analytics API OAuth configured (admin setup, one-time)
- Access to `#gl-youtube-operations` Slack channel
