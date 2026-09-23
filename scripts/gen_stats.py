"""Draw the stats panels straight from the GitHub GraphQL API.

Run with --demo to render from synthetic data, so the layout can be checked
locally without a token.

Language totals cover public repositories only, and exclude forks — a fork's
bytes are someone else's work.
"""

import argparse
import datetime as dt
import json
import os
import pathlib
import random
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from theme import (  # noqa: E402
    AMBER, CELL_W, MELT, MONO, RAMP, SVG_CLOSE, esc, glyph_row, shade_style,
    svg_open,
)

OUT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.github.com/graphql"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false,
                 privacy: PUBLIC, orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


def fetch(login: str, token: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        API, data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{login}-profile-stats",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise SystemExit(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]


def demo_data() -> dict:
    rng = random.Random(11)
    today = dt.date.today()
    days = []
    for i in range(365):
        d = today - dt.timedelta(days=364 - i)
        weekday_penalty = 0.35 if d.weekday() >= 5 else 1.0
        n = max(0, int(rng.gauss(5, 5) * weekday_penalty))
        days.append({"date": d.isoformat(), "contributionCount": n})
    return {
        "contributionsCollection": {
            "contributionCalendar": {
                "totalContributions": sum(x["contributionCount"] for x in days),
                "weeks": [{"contributionDays": days[i:i + 7]}
                          for i in range(0, len(days), 7)],
            }
        },
        "repositories": {"nodes": [
            {"name": "UAV-EngineTwin", "languages": {"edges": [
                {"size": 412000, "node": {"name": "Python"}},
                {"size": 96000, "node": {"name": "TypeScript"}},
                {"size": 31000, "node": {"name": "SQL"}}]}},
            {"name": "antarctic-routing", "languages": {"edges": [
                {"size": 288000, "node": {"name": "Python"}},
                {"size": 24000, "node": {"name": "C++"}}]}},
        ]},
    }


def flatten_days(user: dict):
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    return cal["totalContributions"], days


def streaks(days):
    cur = longest = run = 0
    for d in days:
        if d["contributionCount"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    # Current streak walks backwards; an empty today doesn't break it yet.
    for i, d in enumerate(reversed(days)):
        if d["contributionCount"] > 0:
            cur += 1
        elif i == 0:
            continue
        else:
            break
    return cur, longest


def languages(user, top=6):
    totals = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            totals[edge["node"]["name"]] = totals.get(edge["node"]["name"], 0) + edge["size"]
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])[:top]
    grand = sum(totals.values()) or 1
    return [(name, size, size / grand) for name, size in ranked]


def panel_label(x, y, text, size=11.5, cls="mut"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" font-family="{MONO}" '
            f'font-size="{size}">{esc(text)}</text>')


def big_number(x, y, value, size=27):
    return (f'<text x="{x:.1f}" y="{y:.1f}" class="fg" font-family="{MONO}" '
            f'font-size="{size}" font-weight="700">{esc(str(value))}</text>')


def write_streak(cur, longest, total):
    w, h = 460, 96
    p = [svg_open(w, h, "Contribution streaks")]
    cols = [("current streak", f"{cur} d"), ("longest streak", f"{longest} d"),
            ("contributions, 1 y", f"{total}")]
    for i, (label, value) in enumerate(cols):
        x = 6 + i * 152
        p.append(big_number(x, 44, value))
        p.append(panel_label(x, 66, label))
        if i:
            p.append(f'<rect x="{x - 18}" y="18" width="1" height="54" '
                     f'fill="{MELT}" opacity="0.35"/>')
    p.append(SVG_CLOSE)
    (OUT / "streak.svg").write_text("".join(p), encoding="utf-8")


def write_langs(langs):
    row_h, w = 22, 460
    h = 18 + row_h * len(langs)
    p = [svg_open(w, h, "Top languages by bytes")]
    bar_x, bar_w = 118, 250
    for i, (name, size, frac) in enumerate(langs):
        y = 16 + i * row_h
        p.append(panel_label(6, y + 4, name, size=12, cls="fg"))
        p.append(f'<rect x="{bar_x}" y="{y - 7}" width="{bar_w}" height="10" rx="2" '
                 f'fill="{MELT}" opacity="0.16"/>')
        p.append(f'<rect x="{bar_x}" y="{y - 7}" width="{max(2, bar_w * frac):.1f}" '
                 f'height="10" rx="2" fill="{MELT}"/>')
        p.append(panel_label(bar_x + bar_w + 10, y + 4, f"{frac * 100:4.1f}%", size=11))
    p.append(SVG_CLOSE)
    (OUT / "langs.svg").write_text("".join(p), encoding="utf-8")


def write_year(days):
    """One character per day, quiet to loud, using the hero's ramp so the two
    graphics read as the same language."""
    per_row = 73
    rows = [days[i:i + per_row] for i in range(0, len(days), per_row)]
    counts = [d["contributionCount"] for d in days if d["contributionCount"]]
    peak = max(counts) if counts else 1
    w = int(12 + per_row * CELL_W)
    h = 26 + len(rows) * 17 + 16
    p = [svg_open(w, h, "The last year, one character per day",
                  extra_style=shade_style())]
    p.append(panel_label(6, 14, f"{days[0]['date']} → {days[-1]['date']}"))
    for r, row in enumerate(rows):
        y = 34 + r * 17
        shades = []
        for d in row:
            n = d["contributionCount"]
            shades.append(0 if not n else
                          min(len(RAMP) - 1, 1 + int((n / peak) ** 0.55 * (len(RAMP) - 2))))
        start = 0
        for i in range(1, len(row) + 1):
            if i == len(row) or shades[i] != shades[start]:
                idx = shades[start]
                if idx:
                    p.append(glyph_row([RAMP[idx]] * (i - start), 6 + start * CELL_W,
                                       y, size=12.5, cls=f"s{idx}"))
                start = i
    p.append(panel_label(6, h - 6, f"quiet {RAMP.strip()} loud   peak {peak}/day"))
    p.append(SVG_CLOSE)
    (OUT / "year.svg").write_text("".join(p), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--login", default=os.environ.get("PROFILE_LOGIN", "Gauri-Mahajan01"))
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    if args.demo:
        user = demo_data()
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("GITHUB_TOKEN not set (use --demo to preview)")
        user = fetch(args.login, token)

    total, days = flatten_days(user)
    cur, longest = streaks(days)
    write_streak(cur, longest, total)
    write_langs(languages(user))
    write_year(days)
    print(f"streak={cur} longest={longest} total={total} days={len(days)}")


if __name__ == "__main__":
    main()
