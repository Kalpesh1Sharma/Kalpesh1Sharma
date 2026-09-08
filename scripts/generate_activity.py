#!/usr/bin/env python3
from __future__ import annotations
import collections
import datetime as dt
import html
import json
import os
import urllib.request
from pathlib import Path

USERNAME = "Kalpesh1Sharma"
OUT = Path("assets/activity-pulse.svg")

def fetch_events():
    req = urllib.request.Request(
        f"https://api.github.com/users/{USERNAME}/events/public?per_page=100",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USERNAME}-profile-activity-pulse",
        },
    )
    token = os.getenv("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)

def safe(s):
    return html.escape(str(s), quote=True)

def main():
    events = fetch_events()
    today = dt.datetime.now(dt.timezone.utc).date()
    days = [today - dt.timedelta(days=i) for i in range(20)][::-1]
    day_counts = collections.Counter()
    repos = collections.Counter()
    types = collections.Counter()

    for event in events:
        try:
            created = dt.datetime.fromisoformat(event["created_at"].replace("Z", "+00:00")).date()
        except Exception:
            continue
        if created in days:
            day_counts[created] += 1
        repo = event.get("repo", {}).get("name", "").split("/")[-1]
        if repo:
            repos[repo] += 1
        types[event.get("type", "Event").replace("Event", "")] += 1

    counts = [day_counts[d] for d in days]
    max_count = max(max(counts, default=0), 1)
    left, right = 34, 686
    base_y, amp = 175, 86
    step = (right - left) / (len(days) - 1)
    pts = []
    for i, c in enumerate(counts):
        x = left + i * step
        y = base_y - (c / max_count) * amp
        pts.append((x, y, c))

    path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y, _ in pts)
    total = sum(counts)
    active = sum(1 for c in counts if c)
    top_repos = repos.most_common(3)

    circles = []
    for x, y, c in pts:
        r = 4 + min(c, 8) * 0.9
        opacity = 0.35 if c == 0 else 1
        circles.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="var(--panel)" '
            f'stroke="var(--accent)" stroke-width="2" opacity="{opacity}"/>'
        )

    labels = []
    for i in [0, 5, 10, 15, 19]:
        d = days[i]
        x, _, _ = pts[i]
        labels.append(
            f'<text x="{x:.1f}" y="219" class="date muted" text-anchor="middle">{d.strftime("%d %b")}</text>'
        )

    repo_text = " · ".join(f"{safe(name)} {count}" for name, count in top_repos) or "warming up"
    top_type = types.most_common(1)[0][0] if types else "activity"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="260" viewBox="0 0 720 260" role="img">
<style>
 .bg{{fill:#fffaf5;stroke:#ead9cf}}.text{{fill:#2f2927}}.muted{{fill:#7c6b66}}.pulse{{fill:none;stroke:#df6f8b;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}}.node{{fill:#fffdf9;stroke:#df6f8b;stroke-width:2}}
 .h{{font:800 25px Inter,Segoe UI,Arial,sans-serif}}.m{{font:600 11px ui-monospace,SFMono-Regular,Consolas,monospace;letter-spacing:.4px}}.date{{font:500 9px ui-monospace,SFMono-Regular,Consolas,monospace}}
 @media (prefers-color-scheme:dark){{.bg{{fill:#0d1016;stroke:#262c37}}.text{{fill:#f7f1ea}}.muted{{fill:#9ca1ad}}.pulse{{stroke:#ff7da2}}.node{{fill:#11151d;stroke:#ff7da2}}}}
</style>
<rect x="1" y="1" width="718" height="258" rx="24" class="bg" stroke-width="2"/>
<text x="32" y="45" class="h text">activity pulse</text>
<text x="32" y="67" class="m muted">{total} PUBLIC EVENTS · {active}/20 ACTIVE DAYS · SIGNAL: {safe(top_type).upper()}</text>
<path d="{path}" class="pulse"/>
{''.join(circles)}
{''.join(labels)}
<text x="32" y="241" class="m muted">TOP REPOS: {safe(repo_text)}</text>
</svg>'''
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT}")

if __name__ == "__main__":
    main()
