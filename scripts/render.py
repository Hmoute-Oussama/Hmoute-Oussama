"""Renderers: real data in, blueprint SVG out.

Each function returns a complete SVG document as a string and never raises on
missing input. When a data source is unavailable the renderer draws an honest
"unavailable" panel, because the profile must degrade rather than invent.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import theme as T

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

# ---------------------------------------------------------------- activity ---

W_ACT, H_ACT = 1200, 300


def _unavailable(width, height, kicker, note, title, message, detail):
    out = T.svg(width, height, title, title)
    out.append(T.kicker(40, 42, kicker))
    out.append(T.kicker(width - 40, 42, note, anchor="end"))
    out.append(T.rule(40, 58, width - 40))
    box_h = 90
    y = (height - box_h) / 2 + 10
    out.append(T.panel(40, y, width - 80, box_h, fill=T.PANEL))
    out.append(T.text(width / 2, y + 40, message, fill=T.MID, size=12, spacing=2, anchor="middle"))
    out.append(T.text(width / 2, y + 64, detail, fill=T.SOFT, size=10, anchor="middle"))
    out.append(T.close(width, height))
    return "\n".join(out)


def _layout_days(days):
    """Place each day on the calendar grid, Sunday at the top.

    Column and row come from the date itself, never from the order the days
    arrive in: the contribution graph is serialised by weekday, not by date.
    """
    ordered = sorted(days, key=lambda day: day["date"])
    first = datetime.strptime(ordered[0]["date"], "%Y-%m-%d").date()
    origin = first - timedelta(days=first.isoweekday() % 7)  # the Sunday on or before

    cells = []
    for day in ordered:
        when = datetime.strptime(day["date"], "%Y-%m-%d").date()
        offset = (when - origin).days
        cells.append((offset // 7, when.isoweekday() % 7, day))
    columns = max(cell[0] for cell in cells) + 1
    return cells, columns


def render_activity(days, summary) -> str:
    if not days or not summary:
        return _unavailable(
            W_ACT,
            H_ACT,
            "05 / ENGINEERING ACTIVITY",
            "GITHUB CONTRIBUTIONS",
            "Contribution activity",
            "CONTRIBUTION DATA UNAVAILABLE AT GENERATION TIME",
            "the profile keeps the last good asset until the next successful run",
        )

    cells, columns = _layout_days(days)
    pitch, size = 17, 13
    grid_w = columns * pitch
    x0 = round((W_ACT - grid_w) / 2)
    y0 = 96

    out = T.svg(W_ACT, H_ACT, "Contribution activity for the last twelve months",
                "Contribution activity")
    out.append(T.kicker(40, 42, "05 / ENGINEERING ACTIVITY"))
    out.append(T.kicker(W_ACT - 40, 42, "EACH CELL IS ONE DAY &#183; GITHUB CONTRIBUTIONS, LAST 12 MONTHS",
                        anchor="end"))
    out.append(T.rule(40, 58, W_ACT - 40))

    # month labels, dropped whenever one would collide with the previous one
    last_col, seen_month = -9, None
    for column, _row, day in cells:
        key = day["date"][:7]
        if key == seen_month:
            continue
        seen_month = key
        if column - last_col >= 3:
            out.append(T.text(x0 + column * pitch, y0 - 10, MONTHS[int(day["date"][5:7]) - 1],
                              fill=T.LABEL, size=9, spacing=1.4))
            last_col = column

    for label, row in (("MON", 1), ("WED", 3), ("FRI", 5)):
        out.append(T.text(x0 - 10, y0 + row * pitch + 10, label, fill=T.LABEL, size=8.5,
                          anchor="end", spacing=1))

    for column, row, day in cells:
        x = x0 + column * pitch
        y = y0 + row * pitch
        out.append(
            f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="2.5" '
            f'fill="{T.HEAT[day["level"]]}"/>'
        )

    # stat cells
    stats = [
        ("CONTRIBUTIONS (12M)", T.num(summary["total"]), T.ACCENT),
        ("ACTIVE DAYS", T.num(summary["active_days"]), T.GREEN),
        ("LONGEST STREAK", f'{T.num(summary["longest_streak"])} d', T.VIOLET),
        ("BUSIEST DAY / " + summary["best_date"], T.num(summary["best_count"]), T.AMBER),
    ]
    for index, (label, value, colour) in enumerate(stats):
        x = 40 + index * 260
        if index:
            out.append(f'<line x1="{x - 20}" y1="236" x2="{x - 20}" y2="284" stroke="{T.RULE}"/>')
        out.append(T.text(x, 246, label, fill=T.LABEL, size=9.5, spacing=1.6))
        out.append(T.text(x, 274, value, fill=T.BRIGHT, size=24, weight="600"))
        out.append(f'<rect x="{x}" y="284" width="26" height="2" rx="1" fill="{colour}"/>')

    out.append(T.close(W_ACT, H_ACT))
    return "\n".join(out)


# --------------------------------------------------------------- telemetry ---

W_TEL, H_TEL = 1200, 190


def render_telemetry(user, repos, stats, recent) -> str:
    as_of = stats.get("last_push") or "-"
    cells = [
        ("PUBLIC REPOSITORIES", T.num((user or {}).get("public_repos", 0)), T.ACCENT),
        ("STARS RECEIVED", T.num(stats.get("stars", 0)), T.GREEN),
        ("FOLLOWERS", T.num((user or {}).get("followers", 0)), T.VIOLET),
        ("LANGUAGES USED", T.num(stats.get("languages", 0)), T.AMBER),
        ("PUSHED / 90 DAYS", T.num(recent), T.TEAL),
        ("MEMBER SINCE", _member_year(user), T.BLUE),
    ]

    out = T.svg(W_TEL, H_TEL, "Live GitHub telemetry", "Telemetry")
    out.append(T.kicker(40, 42, "05 / TELEMETRY"))
    out.append(T.kicker(W_TEL - 40, 42,
                        f"SOURCE: GITHUB REST API &#183; AS OF {as_of}", anchor="end"))
    out.append(T.rule(40, 58, W_TEL - 40))

    step = (W_TEL - 80) / len(cells)
    for index, (label, value, colour) in enumerate(cells):
        x = round(40 + index * step)
        if index:
            out.append(f'<line x1="{x}" y1="74" x2="{x}" y2="166" stroke="{T.RULE}"/>')
        out.append(T.text(x + 22, 112, value, fill=T.BRIGHT, size=32, weight="600"))
        out.append(f'<rect x="{x + 22}" y="126" width="26" height="2.5" rx="1.25" fill="{colour}"/>')
        out.append(T.text(x + 22, 150, label, fill=T.LABEL, size=9.5, spacing=1.5))

    out.append(T.close(W_TEL, H_TEL))
    return "\n".join(out)


def _member_year(user) -> str:
    raw = (user or {}).get("created_at", "")
    try:
        return str(datetime.strptime(raw[:10], "%Y-%m-%d").year)
    except (ValueError, TypeError):
        return "-"


# --------------------------------------------------------------- languages ---

W_LANG, H_LANG = 1200, 340


def render_languages(surface, owned: int) -> str:
    if not surface:
        return _unavailable(
            W_LANG,
            H_LANG,
            "05 / LANGUAGE SURFACE",
            "GITHUB REST API",
            "Language surface",
            "REPOSITORY DATA UNAVAILABLE AT GENERATION TIME",
            "the profile keeps the last good asset until the next successful run",
        )

    top = surface[:8]
    peak = max(count for _lang, count in top)
    out = T.svg(W_LANG, H_LANG, "Primary language across public repositories", "Language surface")
    out.append(T.kicker(40, 42, "05 / LANGUAGE SURFACE"))
    out.append(T.kicker(W_LANG - 40, 42,
                        f"PRIMARY LANGUAGE OF {T.num(owned)} NON-FORK REPOSITORIES", anchor="end"))
    out.append(T.rule(40, 58, W_LANG - 40))

    x_track, track_w = 180, 860

    for index, (lang, count) in enumerate(top):
        base = 92 + index * 31
        width = max(6, round(track_w * count / peak))
        opacity = round(max(0.28, 0.95 - index * 0.085), 2)
        out.append(T.text(168, base + 1, lang, fill=T.BODY, size=11, anchor="end"))
        out.append(f'<rect x="{x_track}" y="{base - 11}" width="{track_w}" height="13" rx="3" fill="#0E1720"/>')
        out.append(f'<rect x="{x_track}" y="{base - 11}" width="{width}" height="13" rx="3" '
                   f'fill="{T.ACCENT}" opacity="{opacity}"/>')
        out.append(T.text(x_track + track_w + 14, base, f"{count} repo" + ("s" if count != 1 else ""),
                          fill=T.SOFT, size=10))

    out.append(T.kicker(40, 330, "COUNTS REPOSITORIES BY PRIMARY LANGUAGE, NOT BYTES", size=9, spacing=1.4))
    out.append(T.close(W_LANG, H_LANG))
    return "\n".join(out)


# ------------------------------------------------------------- experiments ---

PITCH = 52


def render_experiments(items) -> str:
    if not items:
        return _unavailable(
            1200, 180, "06 / CURRENT EXPERIMENTS", "config/profile.yml", "Current experiments",
            "NO EXPERIMENTS CONFIGURED", "edit config/profile.yml to populate this panel",
        )

    height = 70 + len(items) * PITCH + 34
    accents = [T.ACCENT, T.VIOLET, T.GREEN, T.AMBER, T.TEAL]
    out = T.svg(1200, height, "Current experiments", "Current experiments")
    out.append(T.kicker(40, 42, "06 / CURRENT EXPERIMENTS"))
    out.append(T.kicker(1160, 42, "EDIT config/profile.yml &#183; THIS PANEL IS REGENERATED", anchor="end"))
    out.append(T.rule(40, 58, 1160))

    for index, item in enumerate(items):
        y = 64 + index * PITCH
        out.append(T.panel(40, y, 1120, 44, fill=T.PANEL))
        out.append(T.accent_bar(40, y, 44, accents[index % len(accents)]))
        out.append(T.text(62, y + 28, f"0{index + 1}", fill=T.LABEL, size=10, spacing=1))
        out.append(T.text(92, y + 19, item.get("title", ""), fill=T.BRIGHT, size=13, mono=False, weight="500"))
        out.append(T.text(92, y + 36, item.get("detail", ""), fill=T.SOFT, size=9.5))

    out.append(T.kicker(40, height - 14,
                        f"{T.num(len(items))} ACTIVE THREADS &#183; TRACKED IN config/profile.yml, RENDERED AT BUILD TIME",
                        size=9, spacing=1.4))
    out.append(T.close(1200, height))
    return "\n".join(out)
