# Architecture

How the profile is put together, and why it is put together that way.

---

## 1. Design system

One visual language, applied everywhere: a **systems blueprint**.

| Token | Value | Role |
|:--|:--|:--|
| canvas | `#0A0E14` | every asset background |
| grid | `#131C26` | 40px technical grid |
| rule / frame | `#16202C` / `#1B2735` | separators and outer border |
| structure | `#2E4257` | edges, connections, spokes |
| type ramp | `#3C4C5E` → `#5E7386` → `#6E8095` → `#8FA3B8` → `#B9C9DA` → `#D7E3F0` | label → body → headline, dim to bright |
| signals | `#4CC2FF` `#2DD4BF` `#34D399` `#F5A524` `#F87171` `#A78BFA` `#60A5FA` | one meaning each, never decoration |
| heatmap | `#101821` `#14384A` `#1C5F7E` `#2E93BF` `#4CC2FF` | contribution levels 0–4 |

Rules that keep it coherent:

* **Two typefaces only.** Monospace for anything the machine would emit (identifiers,
  file names, counts, labels); system sans for the few human sentences.
* **No gradients except one.** A single azure fade rule in the hero. No neon, no glow
  beyond one radial wash, no drop shadows.
* **Every colour carries a meaning.** A colour is never chosen because it looks good in
  isolation; it is chosen because it means the same thing in the next asset.
* **Motion is functional.** Draw-on explains structure, flow implies direction, a pulse
  marks a gate or a live state. Nothing loops for decoration.
* **No emoji.** Ever, anywhere in the profile.

The palette is defined once, in [`scripts/theme.py`](../scripts/theme.py), and imported by
every generated asset. The hand-written SVGs repeat the same literals by design, so a
rendered asset has no external dependency at load time.

---

## 2. Repository layout

```
README.md                      the profile itself
config/profile.yml             curated content model: identity, domains,
                               projects, systems, experiments
assets/
  hero.svg                     opening identity + live topology
  universe.svg                 six domains and their relationships
  method.svg                   spec -> build -> verify -> ship -> observe
  ecosystem.svg                six layers of the working stack
  closing.svg                  terminal signature
  systems/
    verity.svg                 VERITY architecture
    agentsnap.svg              AgentSnap architecture
    pipeline.svg               CI/CD Visualizer architecture
    crisismesh.svg             CrisisMesh architecture
  generated/                   written by the generator, never by hand
    telemetry.svg
    activity.svg
    languages.svg
    experiments.svg
scripts/
  theme.py                     palette, typography, SVG primitives
  github_data.py               every network call, failure modelled as None
  render.py                    data -> SVG, one function per asset
  build_assets.py              orchestrator
  validate_assets.py           XML gate over every asset
.github/workflows/assets.yml   schedule, generate, commit on change
docs/                          this file and MAINTENANCE.md
profile-src/README.md          the previous profile, kept as an archive
```

The split matters: **curated** content lives in YAML and in hand-drawn SVG,
**derived** content lives in `assets/generated/` and is disposable. Deleting
`assets/generated/` costs nothing; deleting `config/profile.yml` costs the profile.

---

## 3. Static assets

These are drawn by hand and committed as-is. They contain no data that can go stale,
which is why they can be hand-written safely.

| Asset | Size | What moves |
|:--|:--|:--|
| `hero.svg` | 1200×380 | spokes draw on in sequence, a typewriter clip releases the statement, six labelled domain nodes fade in, three pulses travel the spokes, a scanline sweeps the canvas, the orbit ring rotates |
| `universe.svg` | 1200×560 | spokes draw outward from the hub, relationship edges animate, pulses travel each edge, satellites orbit two ellipses |
| `method.svg` | 1200×300 | the forward chain flows, the feedback arc back to SPEC flows, the VERIFY gate breathes |
| `ecosystem.svg` | 1200×600 | bands fade in top to bottom, the vertical spine flows |
| `closing.svg` | 1200×280 | terminal cursor blinks, session dot pulses, a status bar sweeps |
| `systems/*.svg` | 1100×330 | stage panels fade in left to right, arrows flow, the terminal stage breathes, the feedback loop flows |

Techniques, all native to SVG and all understood by GitHub's renderer:

* `<animate>` / `<animateMotion>` for element and path-following motion (SMIL).
* `@keyframes` inside a `<style>` block for fades, flowing dashes and pulses.
* `stroke-dasharray` + `stroke-dashoffset` animating to `0` for draw-on.
* `transform-box: fill-box` with `transform-origin: center` for rotation about an
  element's own centre rather than the canvas origin.
* A `clipPath` whose `width` is animated to reveal text left to right.

---

## 4. Generated assets

One Python process, four outputs, three layers.

```
build_assets.py          orchestration, file writing, validation
      |
      +-- github_data.py     network + parsing; returns None on any failure
      +-- render.py          one function per asset; pure string building
      +-- theme.py           palette + primitives shared by all renderers
```

### The data layer

| Function | Source | Returns |
|:--|:--|:--|
| `fetch_user` | `GET /users/{handle}` | profile record |
| `fetch_repos` | `GET /users/{handle}/repos` (≤4 pages) | every owned repository, forks included and tagged |
| `fetch_contributions` | `GET github.com/users/{handle}/contributions` (HTML) | one entry per day: date, level, true count |
| `summarise` | local | totals, active days, longest streak, busiest day |
| `language_surface` | local | primary language per non-fork repository |
| `totals`, `recently_pushed` | local | stars, language count, latest push, 90-day activity |

Only the standard library is used (`urllib`, `json`, `re`, `datetime`), so the workflow
needs no HTTP client. `GITHUB_TOKEN` is attached when present, which raises the rate
limit; the contribution graph is a public HTML page and is fetched unauthenticated.

Two details are easy to get wrong and are handled explicitly:

* **The contribution graph is serialised by weekday, not by date.** The HTML table is
  7 rows by ~53 columns, emitted row by row. Any code that assumes the days arrive in
  chronological order produces a scrambled calendar and meaningless streaks. Both
  `summarise` and `_layout_days` sort by date, and the grid position of a day is derived
  from the date itself rather than from its index.
* **Punctuation travels as character references.** `esc()` in `theme.py` escapes a bare
  `&` but leaves an existing `&#183;` or `&amp;` intact, so entity-based punctuation is
  not double-escaped into visible `&amp;#183;`.

### The failure model

Every fetcher returns `None` instead of raising. Every renderer accepts `None` and draws
an explicit panel:

> CONTRIBUTION DATA UNAVAILABLE AT GENERATION TIME
> the profile keeps the last good asset until the next successful run

`build_assets.py` exits `0` unless a file cannot be written. `--offline` skips the network
entirely and exercises those degraded paths, which is how the fallbacks are tested.

The consequence is the property the brief asked for: **an API outage can never publish a
fabricated statistic.** It can only publish an honest gap.

### Determinism

No wall-clock timestamp is embedded anywhere. Every "as of" marker is derived from the
data: the telemetry panel uses the newest repository push, the activity panel uses the
newest contribution. Identical data therefore produces a byte-identical file, which is
what makes the workflow's "commit only when the data changed" step meaningful rather
than noisy.

---

## 5. GitHub compatibility

The profile is rendered by GitHub's Markdown pipeline, which strips scripts, strips
event handlers, and proxies external images. Everything here is designed inside those
limits:

| Constraint | How it is respected |
|:--|:--|
| No JavaScript | All motion is SMIL and CSS keyframes inside the SVG. Both run in an `<img>`-embedded SVG. |
| No event handlers | No `onclick`, no `onload`, no inline `javascript:`. |
| No external fetches from the asset | Every SVG is self-contained: no remote fonts, no remote images, no `<script>`, no `<foreignObject>`. |
| Layout control | `width="100%"` on every `<img>`, so panels scale with the browser. |
| Accessibility | Each SVG has `role="img"`, an `aria-label` and a `<title>`; every `<img>` has `alt` text. |
| SVG must be valid XML | `scripts/validate_assets.py` parses every file and fails the workflow on a malformed document. (`--` is illegal inside an XML comment, which is a genuinely easy way to break an SVG.) |

Deliberately avoided: third-party stat-card services and streak-card services. They add
an outage dependency, they render in a visual language this profile does not control, and
several of the hosted ones are unreliable. The three activity panels are generated here
instead, from data this repository can reproduce.

---

## 6. What is deliberately absent

* **Fabricated metrics.** No "years of experience" counter, no proficiency percentages,
  no invented contribution counts. Every number traces to the API or to a repository.
* **Forked work presented as original.** The repository list is filtered so that forks are
  excluded from the language surface and never appear in *Selected systems*.
* **Badge walls.** A single LinkedIn badge row would say less than the hero does.
* **Emoji.** See above. It is a hard rule, not a preference.
* **A "tech stack" logo grid.** The ecosystem panel replaces it with six layers that each
  have one responsibility, which is a claim about architecture rather than a list.
