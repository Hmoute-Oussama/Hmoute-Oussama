"""Palette, typography and SVG primitives shared by every asset.

The profile uses one visual language, "xenotech": a violet-black void, a
hexagonal lattice under everything, chamfered plates instead of rounded ones and
a bioluminescent signal set. Hand-written assets and generated assets both draw
from this file, so the profile never drifts into a collection of unrelated
widgets.

Non-negotiable rules
--------------------
* No rounded rectangles anywhere. Every plate is chamfered on the diagonal.
* No gradients beyond the three shared ones: ``core``, ``beam`` and ``arc``.
* Motion must leave the element correct at rest. Every animation class
  describes only the *from* state and uses ``animation-fill-mode: both``, so
  ``prefers-reduced-motion`` or a stripped animation still shows the finished
  frame rather than an invisible one.
* Nothing here fetches or invents data. It only formats.
"""

from __future__ import annotations

import re

# --- void -------------------------------------------------------------------
VOID = "#05030C"
DEEP = "#0A0616"
MEMBRANE = "#0F0A1E"
MEMBRANE_ALT = "#140E27"
WELL = "#0B0716"

# --- lattice and structure --------------------------------------------------
LATTICE = "#150F2C"
LATTICE_L = "#1B1338"
SEAM = "#1E1544"
STROKE = "#261B4E"
FRAME = "#322466"
EDGE = "#3E2C78"
EDGE_SOFT = "#54409C"

# --- type ramp (dim -> bright) ---------------------------------------------
LABEL = "#66569E"
MUTED = "#7A6AB4"
SOFT = "#9486CC"
BODY = "#AFA3E0"
MID = "#CFC5F7"
BRIGHT = "#F2ECFF"

# --- bioluminescent signals -------------------------------------------------
XENO = "#9D6BFF"
BIOLUME = "#E879F9"
VITAL = "#6EF2B0"
HAZARD = "#FFB454"
HEMO = "#FF6B8A"
ION = "#5FD9FF"
SPORE = "#C4B5FD"

# Contribution heat ramp, levels 0..4. Level 0 is the empty cell: an outline
# drawn in SEAM, which is why it is the same value as the well.
HEAT = ["#0B0716", "#2B1A5E", "#4B2AA8", "#7C4AE0", "#C58CFF"]

MONO = "ui-monospace,'SFMono-Regular','SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"

_CSS = f"""      .m{{font-family:{MONO}}}
      .s{{font-family:{SANS}}}
      .fade{{animation:fade .85s cubic-bezier(.2,.7,.2,1) both}}
      @keyframes fade{{from{{opacity:0}}}}
      .rise{{animation:rise .9s cubic-bezier(.2,.7,.2,1) both}}
      @keyframes rise{{from{{opacity:0;transform:translateY(9px)}}}}
      .grow{{transform-box:fill-box;transform-origin:left center;animation:grow 1.25s cubic-bezier(.2,.8,.2,1) both}}
      @keyframes grow{{from{{transform:scaleX(0)}}}}
      .draw{{stroke-dasharray:1;animation:draw 1.7s cubic-bezier(.3,.7,.3,1) both}}
      @keyframes draw{{from{{stroke-dashoffset:1}}}}
      .flow{{stroke-dasharray:5 9;animation:flow 2.3s linear infinite}}
      @keyframes flow{{to{{stroke-dashoffset:-56}}}}
      .flow-r{{stroke-dasharray:4 11;animation:flow-r 3.4s linear infinite}}
      @keyframes flow-r{{to{{stroke-dashoffset:60}}}}
      .breathe{{animation:breathe 3.8s ease-in-out infinite}}
      @keyframes breathe{{0%,100%{{opacity:.2}}50%{{opacity:.9}}}}
      .pulse{{animation:pulse 2.8s ease-in-out infinite}}
      @keyframes pulse{{0%,100%{{opacity:.32}}50%{{opacity:1}}}}
      .blink{{animation:blink 1.1s steps(1) infinite}}
      @keyframes blink{{50%{{opacity:0}}}}
      .glitch{{animation:glitch 7s steps(1) infinite}}
      @keyframes glitch{{0%,93%,100%{{opacity:1}}94%{{opacity:.25}}95%{{opacity:1}}96%{{opacity:.45}}97%{{opacity:1}}}}
      .drift{{animation:drift 19s ease-in-out infinite}}
      @keyframes drift{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-5px)}}}}
      @media (prefers-reduced-motion: reduce){{
        .fade,.rise,.grow,.draw,.flow,.flow-r,.breathe,.pulse,.blink,.glitch,.drift{{animation:none}}
      }}"""

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


# --- geometry ---------------------------------------------------------------

def hexagon(r: float) -> str:
    """Path data for a flat-topped hexagon of circumradius ``r``, centred on 0,0.

    Flat-topped is the orientation that tiles as SVG ``<pattern>`` tiles, so the
    same shape serves the background lattice and every hex node on top of it.
    """
    h = round(r * 3 ** 0.5 / 2, 4)
    x = round(r, 4)
    return f"M{x} 0L{x / 2} {h}L{-x / 2} {h}L{-x} 0L{-x / 2} {-h}L{x / 2} {-h}Z"


def hex_outline(cx, cy, r, *, stroke=EDGE, width=1, dash=None, rotate=0,
                opacity=None, cls=None) -> str:
    """A single decorative hexagon, drawn as an outline.

    Only opacity classes (``breathe``, ``pulse``) are safe here: a class that
    transforms the element would move the hexagon relative to the lattice behind
    it, so rotation is offered as a static attribute instead.
    """
    attrs = [f'transform="translate({cx},{cy}) rotate({rotate})"', f'd="{hexagon(r)}"',
             'fill="none"', f'stroke="{stroke}"', f'stroke-width="{width}"']
    if dash:
        attrs.append(f'stroke-dasharray="{dash}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity}"')
    if cls:
        attrs.insert(0, f'class="{cls}"')
    return f"<path {' '.join(attrs)}/>"


def hex_cell(cx, cy, r, fill, *, stroke=None, width=1, opacity=None) -> str:
    """A filled hexagon cell, the atom of every lattice diagram here."""
    attrs = [f'transform="translate({cx},{cy})"', f'd="{hexagon(r)}"', f'fill="{fill}"']
    if stroke:
        attrs.append(f'stroke="{stroke}" stroke-width="{width}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity}"')
    return f"<path {' '.join(attrs)}/>"


def chamfer(x, y, w, h, *, cut=14, corners="all") -> str:
    """Path data for a plate whose corners are cut on the diagonal.

    ``corners`` selects which corners are cut: ``all`` is the default chrome
    plate, while ``tl-br`` and ``tr-bl`` cut two opposite corners and give a
    process step its direction.
    """
    if corners == "tl-br":
        return (f"M{x} {y + cut}L{x + cut} {y}H{x + w}V{y + h - cut}"
                f"L{x + w - cut} {y + h}H{x}Z")
    if corners == "tr-bl":
        return (f"M{x} {y}H{x + w - cut}L{x + w} {y + cut}V{y + h}H{x + cut}"
                f"L{x} {y + h - cut}Z")
    return (f"M{x} {y + cut}L{x + cut} {y}H{x + w - cut}L{x + w} {y + cut}"
            f"V{y + h - cut}L{x + w - cut} {y + h}H{x + cut}L{x} {y + h - cut}Z")


# --- document ---------------------------------------------------------------

def svg(width: int, height: int, label: str, title: str, lattice: bool = True) -> list:
    """Return the opening lines of a xenotech SVG: defs, CSS, void and lattice."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{esc(label)}">',
        f"  <title>{esc(title)}</title>",
        "  <defs>",
        "    " + _lattice(16, LATTICE, 0.85, "lat"),
        "    " + _lattice(52, LATTICE_L, 0.5, "lat2"),
        '    <radialGradient id="core" cx="0.5" cy="0.5" r="0.5">',
        f'      <stop offset="0" stop-color="{XENO}" stop-opacity="0.17"/>',
        f'      <stop offset="0.55" stop-color="{BIOLUME}" stop-opacity="0.05"/>',
        f'      <stop offset="1" stop-color="{XENO}" stop-opacity="0"/>',
        "    </radialGradient>",
        '    <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">',
        f'      <stop offset="0" stop-color="{XENO}" stop-opacity="0"/>',
        f'      <stop offset="0.5" stop-color="{BIOLUME}" stop-opacity="0.85"/>',
        f'      <stop offset="1" stop-color="{XENO}" stop-opacity="0"/>',
        "    </linearGradient>",
        "    <style>",
        _CSS,
        "    </style>",
        "  </defs>",
        f'  <rect width="{width}" height="{height}" fill="{VOID}"/>',
    ]
    if lattice:
        lines.append(f'  <rect width="{width}" height="{height}" fill="url(#lat)"/>')
        lines.append(f'  <rect width="{width}" height="{height}" fill="url(#lat2)"/>')
    return lines


def _lattice(r: float, stroke: str, opacity: float, ident: str) -> str:
    """A seamless flat-top hex lattice as one ``<pattern>``.

    The tile is 3r x r*sqrt(3) and carries four hexes: the origin hex, its
    horizontal repeat, and the two half-step vertical repeats. That is exactly
    what is needed to cover every edge of the tile without a visible seam.
    ``ident`` is required because two patterns are stacked in the defs and
    duplicate ids would make the second one unreachable.
    """
    width = 3 * r
    height = r * 3 ** 0.5
    body = "".join(
        f'<path d="{hexagon(r)}" transform="translate({round(x, 4)},{round(y, 4)})"/>'
        for x, y in [(0, 0), (width, 0), (width / 2, height / 2), (width / 2, -height / 2)]
    )
    return (
        f'<pattern id="{ident}" width="{round(width, 4)}" height="{round(height, 4)}" '
        f'patternUnits="userSpaceOnUse" fill="none" stroke="{stroke}" stroke-width="1" '
        f'opacity="{opacity}">{body}</pattern>'
    )


def halo(cx, cy, r) -> str:
    """The shared violet core glow. One per asset, deliberately."""
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#core)"/>'


def close(width: int, height: int, *, cut=42) -> str:
    """The chamfered page frame plus the closing tag."""
    x0, y0, x1, y1 = 0.5, 0.5, width - 0.5, height - 0.5
    return f'<path d="{chamfer(x0, y0, x1 - x0, y1 - y0, cut=cut)}" fill="none" stroke="{FRAME}"/>\n</svg>'


# --- atoms ------------------------------------------------------------------

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
    cls=None,
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
    if cls:
        attrs.append(f'class="{cls}"')
    else:
        attrs.insert(0, f'class="{"m" if mono else "s"}"')
    return f'<text {" ".join(attrs)}>{esc(content)}</text>'


def kicker(x, y, content, *, fill=LABEL, size=10.5, spacing=2.4, anchor="start") -> str:
    """The uppercase section marker used at the top of every asset."""
    return text(x, y, content, fill=fill, size=size, spacing=spacing, anchor=anchor)


def rule(x1, y, x2, *, stroke=SEAM, cls=None) -> str:
    """A horizontal seam drawn as a path.

    A path rather than a line, so the ``draw`` class can carry ``pathLength``
    and animate proportionally to the seam's own length.
    """
    extra = ""
    if cls:
        extra = f' class="{cls}" pathLength="1"' if cls == "draw" else f' class="{cls}"'
    return f'<path d="M{x1} {y}H{x2}" fill="none" stroke="{stroke}"{extra}/>'


def panel(x, y, w, h, *, fill=MEMBRANE, stroke=STROKE, cut=14, corners="all",
          width=1, opacity=None, cls=None, delay=None) -> str:
    """A chamfered plate. The replacement for every rounded rectangle."""
    extra = f' class="{cls}"' if cls else ""
    if delay is not None:
        extra += f' style="animation-delay:{delay}s"'
    if opacity is not None:
        extra += f' opacity="{opacity}"'
    return (f'<path{extra} d="{chamfer(x, y, w, h, cut=cut, corners=corners)}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')


def strip(x, y, length, color, *, width=2.4) -> str:
    """The accent strip that sits on a plate's top edge."""
    return (f'<path d="M{x} {y}H{x + length}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round"/>')


def accent_tab(x, y, h, color, *, w=3, skew=5) -> str:
    """A slanted left-edge tab, the vertical counterpart of the top strip."""
    return (f'<path d="M{x} {y + 2}H{x + w}L{x + w + skew} {y + h - 2}H{x + skew}Z" '
            f'fill="{color}"/>')


def dot(cx, cy, r, color, *, opacity=None) -> str:
    """A signal marker."""
    extra = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"{extra}/>'
