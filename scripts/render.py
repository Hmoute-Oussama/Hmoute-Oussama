"""Renderers: real data in, xenotech SVG out.

Each function returns a complete SVG document as a string and never raises on
missing input. When a data source is unavailable the renderer draws an honest
"unavailable" panel, because the profile must degrade rather than invent.

The contribution calendar is drawn as a hex lattice: one hexagon per day, laid
out on the true hexagonal packing (column pitch 1.5r, row pitch r*sqrt(3), odd
columns offset by half a row). The same flat-topped hexagon is the background
lattice, so the data sits inside the structure instead of on top of it.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import theme as T

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

# One signal per metric, so a colour always means the same thing across panels.
SIGNALS = [T.ION, T.XENO, T.BIOLUME, T.SPORE, T.VITAL, T.HAZARD, T.HEMO]


def _open(width, height, title, label=None) -> list:
    out = T.svg(width, height, label or title, title)
    out.append(T.halo(width * 0.14, 40, width * 0.34))
    return out


def _header(out, width, left, right):
    out.append(T.kicker(40, 42, left))
    if right:
        out.append(T.kicker(width - 40, 42, right, anchor="end"))
    out.append(T.rule(40, 58, width - 40, cls="draw"))


def _unavailable(width, height, kicker, note, title, message, detail):
    out = _open(width, height, title)
    _header(out, width, kicker, note)

    plate_h, cut = 92, 16
    y = round((height - plate_h) / 2 + 8, 1)
    out.append(T.panel(40, y, width - 80, plate_h, cut=cut, cls="fade"))
    out.append(T.hex_outline(96, y + plate_h / 2, 22, stroke=T.HEMO, opacity=0.55, cls="pulse"))
    out.append(T.text(148, y + 40, message, fill=T.MID, size=12, spacing=2))
    out.append(T.text(148, y + 64, detail, fill=T.SOFT, size=10))
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


# ---------------------------------------------------------------- activity ---

W_ACT, H_ACT = 1200, 330
HEX_R = 11  # circumradius of one day cell
HEX_X = HEX_R * 1.5                       # column pitch of a hexagonal packing
HEX_Y = round(HEX_R * 3 ** 0.5, 4)        # row pitch


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
    x0 = round((W_ACT - columns * HEX_X) / 2)
    y0 = 108

    out = _open(W_ACT, H_ACT, "Contribution activity",
                "Contribution activity for the last twelve months")
    _header(out, W_ACT, "05 / ENGINEERING ACTIVITY",
            "EACH CELL IS ONE DAY &#183; GITHUB CONTRIBUTIONS, LAST 12 MONTHS")

    # month markers, dropped whenever one would collide with the previous one
    last_col, seen_month = -9, None
    for column, _row, day in cells:
        key = day["date"][:7]
        if key == seen_month:
            continue
        seen_month = key
        if column - last_col >= 3:
            out.append(T.text(x0 + column * HEX_X - HEX_R, y0 - 30,
                              MONTHS[int(day["date"][5:7]) - 1], fill=T.LABEL, size=9, spacing=1.4))
            last_col = column

    for label, row in (("MON", 1), ("WED", 3), ("FRI", 5)):
        out.append(T.text(x0 - HEX_R - 8, y0 + row * HEX_Y + 3, label, fill=T.LABEL,
                          size=8.5, anchor="end", spacing=1))

    # one hexagon per day; an empty day is an outline, an active day is filled
    for column, row, day in cells:
        cx = round(x0 + column * HEX_X, 2)
        cy = round(y0 + row * HEX_Y + (column % 2) * HEX_Y / 2, 2)
        level = day["level"]
        delay = round(0.1 + column * 0.012, 2)
        if level:
            out.append(
                f'<g class="fade" style="animation-delay:{delay}s">'
                + T.hex_cell(cx, cy, HEX_R, T.HEAT[level])
                + "</g>"
            )
        else:
            out.append(
                f'<g class="fade" style="animation-delay:{delay}s">'
                + T.hex_cell(cx, cy, HEX_R, T.WELL, stroke=T.SEAM)
                + "</g>"
            )

    # stat row
    stats = [
        ("CONTRIBUTIONS (12M)", T.num(summary["total"]), T.ION),
        ("ACTIVE DAYS", T.num(summary["active_days"]), T.VITAL),
        ("LONGEST STREAK", f'{T.num(summary["longest_streak"])} d', T.BIOLUME),
        ("BUSIEST DAY / " + summary["best_date"], T.num(summary["best_count"]), T.HAZARD),
    ]
    for index, (label, value, colour) in enumerate(stats):
        x = 40 + index * 205
        if index:
            out.append(f'<path d="M{x - 26} 252V318" fill="none" stroke="{T.SEAM}"/>')
        out.append(T.text(x, 268, label, fill=T.LABEL, size=9, spacing=1.5))
        out.append(T.text(x, 302, value, fill=T.BRIGHT, size=25, weight="600"))
        out.append(T.strip(x, 312, 26, colour))

    out.append(f'<path d="M862 252V318" fill="none" stroke="{T.SEAM}"/>')
    out.append(T.text(884, 268, "INTENSITY", fill=T.LABEL, size=9, spacing=1.5))
    for level in range(5):
        out.append(T.hex_cell(892 + level * 20, 300, 6, T.HEAT[level],
                              stroke=None if level else T.SEAM))

    out.append(T.close(W_ACT, H_ACT))
    return "\n".join(out)


# --------------------------------------------------------------- telemetry ---

W_TEL, H_TEL = 1200, 200


def render_telemetry(user, repos, stats, recent) -> str:
    as_of = stats.get("last_push") or "-"
    cells = [
        ("PUBLIC REPOSITORIES", T.num((user or {}).get("public_repos", 0)), T.ION),
        ("STARS RECEIVED", T.num(stats.get("stars", 0)), T.XENO),
        ("FOLLOWERS", T.num((user or {}).get("followers", 0)), T.BIOLUME),
        ("LANGUAGES USED", T.num(stats.get("languages", 0)), T.SPORE),
        ("PUSHED / 90 DAYS", T.num(recent), T.VITAL),
        ("MEMBER SINCE", _member_year(user), T.HAZARD),
    ]

    out = _open(W_TEL, H_TEL, "Live GitHub telemetry")
    _header(out, W_TEL, "05 / TELEMETRY", f"SOURCE: GITHUB REST API &#183; AS OF {as_of}")

    step = (W_TEL - 80) / len(cells)
    for index, (label, value, colour) in enumerate(cells):
        cx = round(40 + step * (index + 0.5), 1)
        cy = 118
        if index:
            out.append(f'<path d="M{round(40 + step * index, 1)} 76V158" fill="none" stroke="{T.SEAM}"/>')
        out.append(T.hex_cell(cx, cy, 34, T.MEMBRANE, stroke=T.STROKE))
        out.append(T.hex_outline(cx, cy, 30, stroke=colour, opacity=0.45))
        out.append(f'<path class="breathe" style="animation-delay:{round(index * 0.32, 2)}s" '
                   f'transform="translate({cx},{cy - 33})" d="{T.hexagon(5)}" fill="{colour}"/>')
        out.append(T.text(cx, cy + 8, value, fill=T.BRIGHT, size=22, weight="600", anchor="middle"))
        out.append(T.text(cx, 176, label, fill=T.LABEL, size=9, spacing=1.5, anchor="middle"))

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
TRACK_X, TRACK_W = 180, 848


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
    out = _open(W_LANG, H_LANG, "Language surface",
                "Primary language across public repositories")
    _header(out, W_LANG, "05 / LANGUAGE SURFACE",
            f"PRIMARY LANGUAGE OF {T.num(owned)} NON-FORK REPOSITORIES")

    for index, (lang, count) in enumerate(top):
        base = 94 + index * 29
        width = max(14, round(TRACK_W * count / peak))
        colour = T.BIOLUME if index == 0 else T.XENO
        opacity = round(max(0.3, 0.95 - index * 0.08), 2)
        cut = min(7, round(width / 3))
        out.append(T.text(168, base + 4, lang, fill=T.BODY, size=11, anchor="end"))
        out.append(T.panel(TRACK_X, base - 11, TRACK_W, 14, fill=T.WELL,
                           stroke=T.STROKE, cut=7, corners="tr-bl"))
        out.append(T.panel(TRACK_X, base - 11, width, 14, fill=colour, stroke="none",
                           cut=cut, corners="tr-bl", opacity=opacity, cls="grow",
                           delay=round(0.12 + index * 0.09, 2)))
        out.append(T.text(TRACK_X + TRACK_W + 14, base + 4,
                          f"{count} repo" + ("s" if count != 1 else ""), fill=T.SOFT, size=10))

    out.append(T.kicker(40, 328, "COUNTS REPOSITORIES BY PRIMARY LANGUAGE, NOT BY BYTES",
                        size=9, spacing=1.4))
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

    height = 74 + len(items) * PITCH + 30
    out = _open(1200, height, "Current experiments")
    _header(out, 1200, "06 / CURRENT EXPERIMENTS",
            "EDIT config/profile.yml &#183; THIS PANEL IS REGENERATED")

    for index, item in enumerate(items):
        y = 66 + index * PITCH
        colour = SIGNALS[index % len(SIGNALS)]
        out.append(T.panel(40, y, 1120, 44, cut=10, corners="tr-bl", cls="fade",
                           delay=round(index * 0.08, 2)))
        out.append(T.hex_cell(74, y + 22, 13, T.WELL, stroke=colour))
        out.append(T.text(74, y + 26, f"0{index + 1}", fill=colour, size=10.5, anchor="middle"))
        out.append(T.text(104, y + 20, item.get("title", ""), fill=T.BRIGHT,
                          size=13, mono=False, weight="500"))
        out.append(T.text(104, y + 37, item.get("detail", ""), fill=T.SOFT, size=9.5))
        out.append(f'<circle class="pulse" style="animation-delay:{round(index * 0.45, 2)}s" '
                   f'cx="1136" cy="{y + 22}" r="3" fill="{colour}"/>')

    out.append(T.kicker(40, height - 16,
                        f"{T.num(len(items))} ACTIVE THREADS &#183; TRACKED IN config/profile.yml, "
                        "RENDERED AT BUILD TIME",
                        size=9, spacing=1.4))
    out.append(T.close(1200, height))
    return "\n".join(out)
