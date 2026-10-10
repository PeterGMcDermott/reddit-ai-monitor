#!/usr/bin/env python3
"""Reddit Marriott x AI monitor (prototype).

Watches Reddit for posts mentioning Marriott (or a Marriott brand) AND an
AI topic: artificial intelligence, chatbots, Copilot, robots, automation, etc.

How: polls the /new/.rss Atom feed of a curated subreddit list, strips the
post text, keeps entries matching a brand regex AND an AI-topic regex,
dedups via seen_ids.json, writes matches to reports/report-<ts>.md.

Why RSS: Reddit's edge blocks unauthenticated JSON/API scraping from
datacenter IPs (HTTP 403 / bot-wall HTML / rapid 429s). The .rss feeds are
still served. For production volume, register a Reddit "script" app and use
OAuth (api.reddit.com) instead - see README.

Stdlib only. Be polite: ~15s between sub fetches.
"""
import html
import json
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
SUBS = [
    "marriott",
    "hotels",
    "travel",
    "awardtravel",
    "churning",
    "TalesFromTheFrontDesk",
    "hospitality",
]
DELAY = 15  # seconds between sub fetches; Reddit rate-limits aggressively

BRAND_RE = re.compile(
    r"\b(marriott|bonvoy|ritz-?carlton|sheraton|westin|courtyard|"
    r"residence inn|springhill|fairfield|towneplace|aloft|element|"
    r"moxy|tribute portfolio|autograph collection|luxury collection|"
    r"st\.?\s*regis|\bw\b hotels|edition|renaissance|gaylord|"
    r"delta hotels|four points|protea)\b",
    re.I,
)
AI_RE = re.compile(
    r"\b(ai|a\.i\.|artificial intelligence|generative ai|genai|chatbot|"
    r"copilot|machine learning|\bml\b|llm|large language model|robot|"
    r"automation|algorithm|deep learning|neural net)\b",
    re.I,
)

BASE = Path(__file__).resolve().parent
SEEN = BASE / "seen_ids.json"
REPORTS = BASE / "reports"
NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch_rss(sub):
    url = f"https://www.reddit.com/r/{sub}/new/.rss"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"  r/{sub}: 429, waiting 60s and retrying once")
            time.sleep(60)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode(errors="replace")
        raise


def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return html.unescape(s)


def parse(xml_text):
    root = ET.fromstring(xml_text)
    out = []
    for e in root.findall("a:entry", NS):
        link = e.find("a:link", NS)
        out.append(
            {
                "id": (e.findtext("a:id", default="", namespaces=NS) or "").split("/")[-1],
                "title": html.unescape(e.findtext("a:title", default="", namespaces=NS) or ""),
                "url": link.get("href") if link is not None else "",
                "updated": e.findtext("a:updated", default="", namespaces=NS) or "",
                "text": strip_html(e.findtext("a:content", default="", namespaces=NS)),
            }
        )
    return out


def main():
    seen = json.loads(SEEN.read_text()) if SEEN.exists() else []
    seen_set = set(seen)
    matches, scanned = [], 0

    for i, sub in enumerate(SUBS):
        if i:
            time.sleep(DELAY)
        try:
            entries = parse(fetch_rss(sub))
        except Exception as e:  # noqa: BLE001 - prototype; log and continue
            print(f"  r/{sub}: fetch failed: {str(e)[:100]}")
            continue
        print(f"  r/{sub}: {len(entries)} entries")
        scanned += len(entries)
        for p in entries:
            if not p["id"] or p["id"] in seen_set:
                continue
            seen_set.add(p["id"])
            text = f"{p['title']}\n{p['text']}"
            if BRAND_RE.search(text) and AI_RE.search(text):
                matches.append({"subreddit": sub, **p})

    SEEN.write_text(json.dumps(sorted(seen_set)))
    REPORTS.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    rep = REPORTS / f"report-{ts}.md"
    lines = [
        f"# Reddit Marriott x AI scan - {ts} UTC",
        "",
        f"Scanned {scanned} posts across {len(SUBS)} subs, "
        f"{len(matches)} matched (brand mention + AI topic).",
        "",
    ]
    for m in matches:
        lines += [
            f"## {m['title']}",
            f"r/{m['subreddit']} - {m['updated'][:10]}",
            m["url"],
            "",
        ]
    rep.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nWrote {rep} ({len(matches)} matches, {len(seen_set)} ids tracked)")


if __name__ == "__main__":
    main()
