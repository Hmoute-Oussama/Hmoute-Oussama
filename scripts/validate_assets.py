"""Parse every SVG under assets/ so a malformed file can never be committed.

    python scripts/validate_assets.py

Checks well-formedness, that the root element is <svg>, that a viewBox exists,
and that no inline font size or stray character has broken the document. Runs
as a gate in the assets workflow, before anything is committed.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
NS = "{http://www.w3.org/2000/svg}"


def main() -> int:
    files = sorted(ASSETS.rglob("*.svg"))
    if not files:
        print("no SVG assets found", file=sys.stderr)
        return 1

    failures = 0
    for path in files:
        rel = path.relative_to(ROOT)
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as error:
            print(f"FAIL  {rel}  malformed XML: {error}")
            failures += 1
            continue

        tag = root.tag.replace(NS, "")
        if tag != "svg":
            print(f"FAIL  {rel}  root element is <{tag}>, expected <svg>")
            failures += 1
            continue
        if not root.get("viewBox"):
            print(f"FAIL  {rel}  missing viewBox")
            failures += 1
            continue

        print(f"ok    {rel}  {root.get('viewBox')}")

    print(f"\n{len(files) - failures}/{len(files)} assets valid")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
