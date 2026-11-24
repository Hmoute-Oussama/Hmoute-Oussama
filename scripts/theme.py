"""Palette, typography and SVG primitives shared by every asset.

The profile uses one visual language, a "systems blueprint": a dark slate
canvas, a thin technical grid, azure/teal signal accents and monospaced labels.
Hand-written assets and generated assets both draw from this file so the
profile never drifts into a collection of unrelated widgets.

Nothing here fetches or invents data. It only formats.
"""

from __future__ import annotations

import re

# --- canvas -----------------------------------------------------------------
BG = "#0A0E14"
GRID = "#131C26"
RULE = "#16202C"
FRAME = "#1B2735"
PANEL = "#0B131C"
PANEL_ALT = "#0D1620"
STROKE = "#1E2C3A"

# --- structure --------------------------------------------------------------
EDGE = "#2E4257"
EDGE_SOFT = "#3A5068"

# --- type ramp (dim -> bright) ---------------------------------------------
LABEL = "#3C4C5E"
MUTED = "#5E7386"
SOFT = "#6E8095"
BODY = "#8FA3B8"
MID = "#B9C9DA"
BRIGHT = "#D7E3F0"

# --- signals ----------------------------------------------------------------
ACCENT = "#4CC2FF"
TEAL = "#2DD4BF"
GREEN = "#34D399"
AMBER = "#F5A524"
RED = "#F87171"
VIOLET = "#A78BFA"
BLUE = "#60A5FA"

# Contribution heatmap ramp, levels 0..4.
HEAT = ["#101821", "#14384A", "#1C5F7E", "#2E93BF", "#4CC2FF"]

MONO = "ui-monospace,'SFMono-Regular','SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"


_BARE_AMP = re.compile(r"&(?!#[0-9]+;|#x[0-9A-Fa-f]+;|[A-Za-z][A-Za-z0-9]*;)")


def esc(value) -> str:
    """Escape text for an SVG text node or attribute.

    An ampersand that already begins a character reference (``&#183;``, ``&amp;``)
    is left alone, so callers can keep using entities for punctuation without
    the escaping layer doubling them into ``&amp;#183;``.
    """
    safe = _BARE_AMP.sub("&amp;", str(value))
    return (
        safe.replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def num(value) -> str:
    """Thousands-separated integer."""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def svg(width: int, height: int, label: str, title: str, grid: bool = True) -> list:
    """Return the opening lines of a blueprint SVG (background + shared CSS)."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{esc(label)}">',
        f"  <title>{esc(title)}</title>",
        "  <defs>",
        '    <pattern id="g" width="40" height="40" patternUnits="userSpaceOnUse">'
        f'<path d="M40 0H0V40" fill="none" stroke="{GRID}" stroke-width="1"/></pattern>',
        "    <style>",
        f"      .m{{font-family:{MONO}}}",
        f"      .s{{font-family:{SANS}}}",
        "      .fade{opacity:0;animation:fade .7s ease forwards}",
        "      @keyframes fade{to{opacity:1}}",
        "      .flow{stroke-dasharray:6 7;animation:flow 1.8s linear infinite}",
        "      @keyframes flow{to{stroke-dashoffset:-26}}",
        "      .breathe{animation:breathe 3.4s ease-in-out infinite}",
        "      @keyframes breathe{0%,100%{opacity:.25}50%{opacity:.85}}",
        "    </style>",
        "  </defs>",
        f'  <rect width="{width}" height="{height}" fill="{BG}"/>',
    ]
    if grid:
        lines.append(f'  <rect width="{width}" height="{height}" fill="url(#g)"/>')
    return lines


def text(
    x,
    y,
    content,
    *,
    fill=BODY,
    size=10,
    mono=True,
    anchor="start",
    spacing=None,
    weight=None,
    opacity=None,
) -> str:
    """One <text> node using the shared type classes."""
    attrs = [f'x="{x}"', f'y="{y}"', f'fill="{fill}"', f'font-size="{size}"']
    if spacing is not None:
        attrs.append(f'letter-spacing="{spacing}"')
    if weight is not None:
        attrs.append(f'font-weight="{weight}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity}"')
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    cls = "m" if mono else "s"
    return f'<text class="{cls}" {" ".join(attrs)}>{esc(content)}</text>'


def kicker(x, y, content, *, fill=LABEL, size=10.5, spacing=2.4, anchor="start") -> str:
    """The uppercase section marker used at the top of every asset."""
    return text(x, y, content, fill=fill, size=size, spacing=spacing, anchor=anchor)


def rule(x1, y, x2) -> str:
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{RULE}"/>'


def panel(x, y, w, h, *, fill=PANEL, stroke=STROKE, radius=7, cls=None, delay=None) -> str:
    extra = f' class="{cls}"' if cls else ""
    if delay is not None:
        extra += f' style="animation-delay:{delay}s"'
    return f'<rect{extra} x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def accent_bar(x, y, h, color, w=3) -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="1.5" fill="{color}"/>'


def close(width: int, height: int) -> str:
    return (
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" '
        f'fill="none" stroke="{FRAME}"/>\n</svg>'
    )
