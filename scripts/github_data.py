"""Real GitHub data, with failure modelled as a value instead of an exception.

Every fetcher returns ``None`` when GitHub is unreachable, rate limited, or has
changed the markup it exposes. Renderers treat ``None`` as "draw a graceful
unavailable state", so a broken API or a missing token can never produce a
fabricated number on the profile.

Only the standard library is used, so the generator runs on a bare runner.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import date, datetime

API = "https://api.github.com"
UA = "hmoute-profile-assets/1.0 (+https://github.com/Hmoute-Oussama)"
TIMEOUT = 20


def token() -> str:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def _open(url: str, accept: str, auth: bool) -> str:
    headers = {"User-Agent": UA, "Accept": accept}
    if auth and token():
        headers["Authorization"] = f"Bearer {token()}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read().decode("utf-8", "replace")


def _json(url: str):
    try:
        return json.loads(_open(url, "application/vnd.github+json", auth=True))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None


def fetch_user(username: str):
    """Profile record: public_repos, followers, created_at, ... or None."""
    return _json(f"{API}/users/{username}")


def fetch_repos(username: str, max_pages: int = 4):
    """Every repository owned by the user (forks included, tagged as such)."""
    repos = []
    for page in range(1, max_pages + 1):
        batch = _json(
            f"{API}/users/{username}/repos"
            f"?per_page=100&sort=pushed&direction=desc&type=owner&page={page}"
        )
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
    return repos or None


_TD = re.compile(r'<td\b[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*>', re.I)
_ID = re.compile(r'id="([^"]+)"')
_LEVEL = re.compile(r'data-level="(\d)"')
_TIP = re.compile(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>(.*?)</tool-tip>', re.I | re.S)
_TAG = re.compile(r"<[^>]+>")


def _tip_count(markup: str) -> int:
    plain = _TAG.sub("", markup).strip().lower()
    if plain.startswith("no contribution"):
        return 0
    match = re.match(r"([\d,]+)\s+contribution", plain)
    return int(match.group(1).replace(",", "")) if match else 0


def fetch_contributions(username: str):
    """One entry per day of the trailing year: date, level and true count.

    The public contribution graph is parsed from its HTML. If the markup ever
    changes, this returns None and the activity asset degrades instead of
    printing a guess.
    """
    try:
        html = _open(f"https://github.com/users/{username}/contributions", "text/html", auth=False)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None

    tips = {cid: _tip_count(body) for cid, body in _TIP.findall(html)}
    days = []
    for match in _TD.finditer(html):
        tag = match.group(0)
        ident = _ID.search(tag)
        level = _LEVEL.search(tag)
        if not ident or not level:
            continue
        days.append(
            {
                "date": match.group(1),
                "level": int(level.group(1)),
                "count": tips.get(ident.group(1), 0),
            }
        )
    return days or None


def summarise(days) -> dict | None:
    """Derive totals, streaks and the busiest day from real daily counts.

    The contribution graph arrives grouped by weekday rather than by date, so
    everything here sorts first. Streaks are only meaningful in date order.
    """
    if not days:
        return None

    ordered = sorted(days, key=lambda day: day["date"])
    total = sum(day["count"] for day in ordered)
    active = [day for day in ordered if day["count"] > 0]

    longest = run = 0
    for day in ordered:
        run = run + 1 if day["count"] > 0 else 0
        longest = max(longest, run)

    best = max(ordered, key=lambda day: day["count"])
    return {
        "total": total,
        "active_days": len(active),
        "longest_streak": longest,
        "best_count": best["count"],
        "best_date": best["date"],
        "first": ordered[0]["date"],
        "last": ordered[-1]["date"],
    }


def language_surface(repos) -> list:
    """Primary language per owned, non-fork repository, most common first.

    This counts repositories, not bytes, and the asset says so. Byte counts
    would need one extra API call per repository and a lot of luck.
    """
    if not repos:
        return []
    counts = {}
    for repo in repos:
        if repo.get("fork") or repo.get("archived"):
            continue
        lang = repo.get("language")
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def totals(repos) -> dict:
    """Aggregates over owned repositories. Zeros when data is unavailable."""
    owned = [repo for repo in repos or [] if not repo.get("fork")]
    stars = sum(repo.get("stargazers_count", 0) for repo in owned)
    pushed = [repo.get("pushed_at") for repo in owned if repo.get("pushed_at")]
    return {
        "owned": len(owned),
        "forks": len(repos or []) - len(owned),
        "stars": stars,
        "last_push": max(pushed)[:10] if pushed else "",
        "languages": len({repo.get("language") for repo in owned if repo.get("language")}),
    }


def recently_pushed(repos, window_days: int = 90) -> int:
    """Owned repositories with a push inside the window, ending at the latest push."""
    if not repos:
        return 0
    stamps = [repo.get("pushed_at") for repo in repos if repo.get("pushed_at")]
    if not stamps:
        return 0
    newest = datetime.strptime(max(stamps)[:10], "%Y-%m-%d").date()
    count = 0
    for repo in repos:
        stamp = repo.get("pushed_at")
        if not stamp:
            continue
        when = datetime.strptime(stamp[:10], "%Y-%m-%d").date()
        if (newest - when).days <= window_days:
            count += 1
    return count


def account_year(user) -> str:
    raw = (user or {}).get("created_at", "")
    try:
        return str(datetime.strptime(raw[:10], "%Y-%m-%d").year)
    except (ValueError, TypeError):
        return ""


def today() -> str:
    return date.today().isoformat()
