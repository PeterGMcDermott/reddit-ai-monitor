# Reddit Marriott x AI monitor (prototype)

Watches Reddit for posts that mention Marriott (or a Marriott brand) **and**
an AI topic: artificial intelligence, chatbots, Copilot, robots, automation, etc.

## How it works

`monitor.py` (stdlib only, no dependencies):
1. Pulls the `/new/.rss` feed of 7 curated subs (marriott, hotels, travel,
   awardtravel, churning, TalesFromTheFrontDesk, hospitality).
2. Keeps posts matching a brand regex AND an AI-topic regex (title + post text).
3. Dedups via `seen_ids.json`, writes a timestamped report to
   `reports/report-<ts>.md`.

## Run it

```
python3 monitor.py
```

## Notes

- No Reddit account needed for the prototype. Browser-style User-Agent + 15s
  delay between sub fetches, with one retry on 429s. Reddit still throttles
  unauthenticated fetches hard (3 of 7 subs 429'd on the first run), so
  coverage is partial without API access.
- To scale up (more subs, comments, higher limits): register a Reddit "script"
  app at reddit.com/prefs/apps and add OAuth token flow.
- Natural next steps: comment scanning, sentiment flagging, email/Slack alerts,
  a scheduled run (cron) instead of manual.
- Before using for official Marriott reputation work, clear it with corporate
  comms/legal; enterprise social listening may already cover this.
