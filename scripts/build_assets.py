"""Orchestrator: fetch real data, render every generated asset, write to disk.

    python scripts/build_assets.py            # full run (needs network)
    python scripts/build_assets.py --offline  # render from nothing, check layout

Design rules
------------
* Never fabricate. A failed fetch produces a degraded asset, never a fake number.
* Never break the build. The process exits 0 unless a file cannot be written,
  so a bad API day leaves the previous, still-correct asset in place.
* Deterministic output. No wall-clock timestamps are embedded: the "as of"
  marker comes from the data itself, so scheduled runs only produce a commit
  when the underlying numbers actually changed.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import github_data as gh  # noqa: E402
import render  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "profile.yml"
OUT = ROOT / "assets" / "generated"


def load_config():
    try:
        import yaml
    except ImportError:
        print("error: PyYAML is required -> pip install pyyaml", file=sys.stderr)
        raise SystemExit(2)
    with CONFIG.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write(name: str, svg: str):
    """Write only when the bytes differ, so unchanged assets stay untouched."""
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    previous = path.read_text(encoding="utf-8") if path.exists() else None
    if previous == svg:
        return path, False, len(svg)
    path.write_text(svg, encoding="utf-8")
    return path, True, len(svg)


def verify(svg: str, name: str) -> bool:
    try:
        ET.fromstring(svg)
    except ET.ParseError as error:
        print(f"  ! {name} is not well-formed XML: {error}", file=sys.stderr)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true",
                        help="skip the network and exercise the degraded paths")
    args = parser.parse_args()

    config = load_config()
    username = config["identity"]["handle"]

    if args.offline:
        user = repos = days = None
        print(f"offline run for {username}: every asset renders its fallback state")
    else:
        user = gh.fetch_user(username)
        repos = gh.fetch_repos(username)
        days = gh.fetch_contributions(username)
        print(f"fetched: user={'ok' if user else 'FAIL'} "
              f"repos={len(repos) if repos else 'FAIL'} "
              f"days={len(days) if days else 'FAIL'}")

    summary = gh.summarise(days)
    stats = gh.totals(repos)
    recent = gh.recently_pushed(repos)
    surface = gh.language_surface(repos)
    owned = stats["owned"] or (user or {}).get("public_repos", 0)

    outputs = {
        "activity.svg": render.render_activity(days, summary),
        "telemetry.svg": render.render_telemetry(user, repos, stats, recent),
        "languages.svg": render.render_languages(surface, owned),
        "experiments.svg": render.render_experiments(config.get("experiments") or []),
    }

    print(f"\nwriting {OUT.relative_to(ROOT)}")
    written = 0
    for name, svg in outputs.items():
        if not verify(svg, name):
            continue
        _path, changed, size = write(name, svg)
        written += 1 if changed else 0
        print(f"  {'updated' if changed else 'unchanged'}  {name:<18} {size:>6} bytes")

    print(f"\n{written} of {len(outputs)} assets changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
