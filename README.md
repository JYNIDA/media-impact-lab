# Media Impact Lab

Hypothesis-driven video performance analysis for EO Global.

Every publish is an experiment. Record your hypothesis before publishing, track performance data, and get auto-generated reports that verify what worked and what didn't.

## Install

```bash
# 1) Clone into your Claude Code skills directory
git clone https://github.com/JYNIDA/media-impact-lab.git ~/.claude/skills/media-impact-lab

# 2) Set up your local config (Slack bot token)
cp ~/.claude/skills/media-impact-lab/config/config.example.json \
   ~/.claude/skills/media-impact-lab/config/config.json
# Then edit config.json and replace the two REPLACE-ME placeholders.
# Bot token + webhook: ask Jiyoon (1Password preferred).

# 3) Verify
TOKEN=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.claude/skills/media-impact-lab/config/config.json')))['slack']['impact_lab_bot_token'])")
curl -s https://slack.com/api/auth.test -H "Authorization: Bearer $TOKEN"
# expected: {"ok": true, ...}
```

After step 2, the skill is available in Claude Code.

`config/config.json` is gitignored.

## Quick Start

```
impact lab start [Episode Title] [Guest Name]
```

This creates a Slack Canvas in `#gl-youtube-operations` with the episode template. Fill in your hypotheses, publish, and Claude handles the rest.

## Commands

| Command | What it does |
|---------|-------------|
| `impact lab start [Episode Title] [Guest Name]` | Create Canvas + extract content DNA from script |
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

## Altos Ventures Daily Digest

Get a daily Slack DM summarizing Altos Ventures news — press coverage,
funding/investment, official posts/SNS, and portfolio-company news. Claude
gathers the last 24–48h via web search and DMs you a Korean digest.

Runs automatically via GitHub Actions
([`.github/workflows/altos-daily-updates.yml`](.github/workflows/altos-daily-updates.yml))
on a daily cron (08:00 KST), and can be triggered manually from the **Actions**
tab.

**Setup — add three repository secrets** (Settings → Secrets and variables →
Actions):

| Secret | Value |
|--------|-------|
| `ANTHROPIC_API_KEY` | Claude API key (console.anthropic.com) |
| `SLACK_BOT_TOKEN` | Slack bot token with `chat:write` + `im:write` scopes |
| `SLACK_USER_ID` | Your Slack member ID, e.g. `U0XXXXXXX` (Slack profile → ⋯ → Copy member ID) |

**Run it locally / preview:**

```bash
# Preview without posting (reads config/config.json or env vars)
python3 lib/altos_digest.py --dry-run

# Gather + DM to yourself
ANTHROPIC_API_KEY=... SLACK_BOT_TOKEN=... SLACK_USER_ID=U0XXXXXXX \
  python3 lib/altos_digest.py
```

To change the delivery time, edit the `cron` line in the workflow (it's in UTC).
